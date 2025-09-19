"""
GPT 클라이언트 구현

OpenAI의 GPT 모델들 (GPT-4, GPT-5, GPT-4 Turbo 등)을 지원하는 클라이언트
"""

import time
from typing import List, Dict, Any, Optional
import openai
from openai import OpenAI

from .base import BaseAgentLLM, LLMRequest, LLMResponse, UsageStats
from .exceptions import (
    APIConnectionError,
    TokenLimitExceededError,
    ModelNotSupportedError,
    ConfigurationError,
    RateLimitError,
    ResponseQualityError
)


class GPTClient(BaseAgentLLM):
    """OpenAI GPT LLM 클라이언트"""
    
    # 지원하는 GPT 모델들
    SUPPORTED_MODELS = {
        'gpt-5': 'gpt-4o',  # GPT-5가 출시되면 실제 모델명으로 업데이트 필요
        'gpt-4o': 'gpt-4o',
        'gpt-4': 'gpt-4-turbo-preview',
        'gpt-4-turbo': 'gpt-4-turbo-preview',
        'gpt-5-nano': 'gpt-4o-mini',  # 빠른 처리용 경량 모델
        'gpt-4o-mini': 'gpt-4o-mini'
    }
    
    # 모델별 토큰 가격 (USD per 1K tokens) - 2024년 기준
    MODEL_PRICING = {
        'gpt-4o': {'input': 0.005, 'output': 0.015},
        'gpt-4-turbo-preview': {'input': 0.01, 'output': 0.03},
        'gpt-4o-mini': {'input': 0.00015, 'output': 0.0006}
    }
    
    def __init__(self, model_name: str, api_key: str, **config):
        """
        GPT 클라이언트 초기화
        
        Args:
            model_name: 사용할 GPT 모델명 (gpt-5, gpt-4o, gpt-5-nano 등)
            api_key: OpenAI API 키
            **config: 추가 설정 (max_tokens, temperature 등)
        """
        super().__init__("gpt", model_name, api_key, **config)
        
        # OpenAI 클라이언트 초기화
        self.client = OpenAI(api_key=api_key)
        
        # 실제 모델명 매핑
        if model_name not in self.SUPPORTED_MODELS:
            raise ModelNotSupportedError("gpt", model_name)
        
        self.actual_model_name = self.SUPPORTED_MODELS[model_name]
        
        # 기본 설정
        self.default_max_tokens = config.get('max_tokens', 4000)
        self.default_temperature = config.get('temperature', 0.7)
        
        # GPT-5 nano는 더 빠른 응답을 위해 낮은 temperature 사용
        if 'nano' in model_name:
            self.default_temperature = 0.3
    
    def validate_config(self) -> bool:
        """GPT 클라이언트 설정 검증"""
        if not self.api_key:
            raise ConfigurationError("gpt", "API 키가 설정되지 않았습니다")
        
        if self.model_name not in self.SUPPORTED_MODELS:
            raise ConfigurationError("gpt", f"지원하지 않는 모델: {self.model_name}")
        
        # API 키 유효성 간단 체크
        try:
            # 테스트 요청으로 API 키 검증
            response = self.client.chat.completions.create(
                model=self.actual_model_name,
                max_tokens=10,
                messages=[{"role": "user", "content": "Hello"}]
            )
            return True
        except openai.AuthenticationError:
            raise ConfigurationError("gpt", "유효하지 않은 API 키")
        except Exception as e:
            # 네트워크 오류 등은 일시적일 수 있으므로 경고만 출력
            print(f"OpenAI API 연결 확인 실패 (일시적일 수 있음): {e}")
            return True
    
    def get_supported_models(self) -> List[str]:
        """지원하는 GPT 모델 목록 반환"""
        return list(self.SUPPORTED_MODELS.keys())
    
    def estimate_cost(self, request: LLMRequest) -> float:
        """요청에 대한 예상 비용 계산"""
        # 입력 토큰 추정 (대략 1 token = 0.75 words)
        input_tokens = len(request.prompt.split()) / 0.75
        if request.system_prompt:
            input_tokens += len(request.system_prompt.split()) / 0.75
        
        # 출력 토큰 추정
        max_tokens = request.max_tokens or self.default_max_tokens
        output_tokens = max_tokens * 0.8  # 평균적으로 max의 80% 사용 가정
        
        pricing = self.MODEL_PRICING.get(self.actual_model_name, {'input': 0.005, 'output': 0.015})
        
        input_cost = (input_tokens / 1000) * pricing['input']
        output_cost = (output_tokens / 1000) * pricing['output']
        
        return input_cost + output_cost
    
    def generate_response(self, request: LLMRequest) -> LLMResponse:
        """GPT로부터 응답 생성"""
        start_time = time.time()
        
        try:
            # 메시지 구성
            messages = []
            
            if request.system_prompt:
                messages.append({"role": "system", "content": request.system_prompt})
            
            messages.append({"role": "user", "content": request.prompt})
            
            # API 호출 파라미터
            kwargs = {
                "model": self.actual_model_name,
                "max_tokens": request.max_tokens or self.default_max_tokens,
                "temperature": request.temperature or self.default_temperature,
                "messages": messages
            }
            
            # 에이전트 타입별 특별 설정
            if request.agent_type == "technical_analyst":
                # 기술적 분석은 더 정확한 수치 계산이 필요
                kwargs["temperature"] = 0.2
            elif request.agent_type in ["portfolio_rebalancer", "trade_planner"]:
                # 포트폴리오 관련 작업은 일관성이 중요
                kwargs["temperature"] = 0.1
            
            # OpenAI API 호출
            response = self.client.chat.completions.create(**kwargs)
            
            end_time = time.time()
            response_time = end_time - start_time
            
            # 응답 내용 추출
            content = response.choices[0].message.content or ""
            
            # 토큰 사용량 및 비용 계산
            usage = response.usage
            input_tokens = usage.prompt_tokens
            output_tokens = usage.completion_tokens
            total_tokens = usage.total_tokens
            
            pricing = self.MODEL_PRICING.get(self.actual_model_name, {'input': 0.005, 'output': 0.015})
            cost = ((input_tokens / 1000) * pricing['input'] + 
                   (output_tokens / 1000) * pricing['output'])
            
            # 응답 품질 검증
            confidence_score = self._calculate_confidence_score(content, request)
            
            llm_response = LLMResponse(
                content=content,
                model_used=self.actual_model_name,
                tokens_used=total_tokens,
                cost=cost,
                response_time=response_time,
                confidence_score=confidence_score,
                metadata={
                    'input_tokens': input_tokens,
                    'output_tokens': output_tokens,
                    'finish_reason': response.choices[0].finish_reason,
                    'model_alias': self.model_name
                }
            )
            
            # 사용량 통계 업데이트
            self.update_usage_stats(llm_response, success=True)
            
            return llm_response
            
        except openai.RateLimitError as e:
            self.update_usage_stats(None, success=False)
            # OpenAI rate limit 헤더에서 재시도 시간 추출
            retry_after = getattr(e.response, 'headers', {}).get('retry-after', 60)
            raise RateLimitError("gpt", retry_after=int(retry_after))
            
        except openai.BadRequestError as e:
            self.update_usage_stats(None, success=False)
            if "maximum context length" in str(e).lower():
                raise TokenLimitExceededError("gpt", len(request.prompt), self.default_max_tokens)
            raise ResponseQualityError("gpt", f"잘못된 요청: {e}")
            
        except (openai.APIConnectionError, openai.APITimeoutError) as e:
            self.update_usage_stats(None, success=False)
            raise APIConnectionError("gpt", f"API 연결 실패: {e}")
            
        except Exception as e:
            self.update_usage_stats(None, success=False)
            raise APIConnectionError("gpt", f"예상치 못한 오류: {e}")
    
    def _calculate_confidence_score(self, content: str, request: LLMRequest) -> float:
        """응답의 신뢰도 점수 계산 (0.0 ~ 1.0)"""
        if not content or len(content.strip()) < 10:
            return 0.0
        
        # 기본 점수
        score = 0.7
        
        # 에이전트 타입별 품질 기준
        if request.agent_type == "technical_analyst":
            # 기술적 분석은 구체적인 지표와 수치가 필요
            technical_indicators = ["rsi", "macd", "bollinger", "이동평균", "지지선", "저항선", "%"]
            if any(indicator in content.lower() for indicator in technical_indicators):
                score += 0.2
            
            # 수치 데이터 포함 여부 확인
            import re
            if re.search(r'\b\d+(\.\d+)?%?\b', content):
                score += 0.1
                
        elif request.agent_type == "cio":
            # CIO는 종합적 분석과 명확한 결론이 필요
            if "결론" in content or "권고" in content or "추천" in content:
                score += 0.2
                
        elif request.agent_type in ["portfolio_rebalancer", "allocator"]:
            # 포트폴리오 관련은 구체적인 비율이나 금액이 필요
            import re
            if re.search(r'\b\d+%|\$\d+|원\b', content):
                score += 0.2
        
        # 응답 길이 적절성 (에이전트별 차등 적용)
        if request.agent_type in ["trade_planner", "screener"]:
            # 간단한 작업은 짧은 응답이 적절
            if 20 <= len(content) <= 500:
                score += 0.1
        else:
            # 분석 작업은 상세한 응답이 필요
            if 100 <= len(content) <= 2000:
                score += 0.1
        
        return min(score, 1.0)
    
    def get_model_info(self) -> Dict[str, Any]:
        """현재 사용 중인 모델 정보 반환"""
        context_lengths = {
            'gpt-4o': 128000,
            'gpt-4-turbo-preview': 128000,
            'gpt-4o-mini': 128000
        }
        
        return {
            'provider': self.provider_name,
            'model_alias': self.model_name,
            'actual_model': self.actual_model_name,
            'pricing': self.MODEL_PRICING.get(self.actual_model_name),
            'max_context_length': context_lengths.get(self.actual_model_name, 128000),
            'supports_system_prompt': True,
            'supports_function_calling': True,
            'is_nano_version': 'nano' in self.model_name or 'mini' in self.model_name
        }