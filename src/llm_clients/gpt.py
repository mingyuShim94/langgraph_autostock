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
        'gpt-5': 'gpt-5',           # 최신 GPT-5 모델
        'gpt-5-nano': 'gpt-5-nano', # 빠른 처리용 경량 모델
        'gpt-5-mini': 'gpt-5-mini', # 중간 성능 모델
        'gpt-4o': 'gpt-4o',         # 기존 GPT-4o 호환성 유지
        'gpt-4': 'gpt-4-turbo-preview',
        'gpt-4-turbo': 'gpt-4-turbo-preview',
        'gpt-4o-mini': 'gpt-4o-mini'
    }
    
    # 모델별 토큰 가격 (USD per 1K tokens) - 2025년 기준
    MODEL_PRICING = {
        'gpt-5': {'input': 0.01, 'output': 0.03},        # GPT-5 프리미엄 모델
        'gpt-5-nano': {'input': 0.0002, 'output': 0.0008}, # 경량 모델
        'gpt-5-mini': {'input': 0.001, 'output': 0.003},   # 중간 모델
        'gpt-4o': {'input': 0.005, 'output': 0.015},      # 기존 GPT-4o
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
        
        # GPT-5 경량 모델들은 더 빠른 응답을 위해 낮은 temperature 사용
        if 'nano' in model_name or 'mini' in model_name:
            self.default_temperature = 0.3
    
    def validate_config(self) -> bool:
        """GPT 클라이언트 설정 검증"""
        if not self.api_key:
            raise ConfigurationError("gpt", "API 키가 설정되지 않았습니다")
        
        if self.model_name not in self.SUPPORTED_MODELS:
            raise ConfigurationError("gpt", f"지원하지 않는 모델: {self.model_name}")
        
        # API 키 유효성 간단 체크는 실제 사용할 때 검증
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
            # GPT-5 모델 체크
            is_gpt5_model = self.actual_model_name.startswith('gpt-5')
            
            if is_gpt5_model:
                # 새로운 GPT-5 API 구조
                # 메시지 구성 (새로운 input 형식)
                input_messages = []
                
                # 시스템 프롬프트가 있는 경우 user 메시지에 통합
                user_content = request.prompt
                if request.system_prompt:
                    user_content = f"{request.system_prompt}\n\n{request.prompt}"
                
                input_messages.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": user_content
                        }
                    ]
                })
                
                # 에이전트 타입별 reasoning effort 설정
                reasoning_effort = "medium"  # 기본값
                text_verbosity = "medium"    # 기본값
                
                if request.agent_type == "technical_analyst":
                    reasoning_effort = "high"    # 정확한 수치 계산 필요
                    text_verbosity = "high"
                elif request.agent_type in ["portfolio_rebalancer", "trade_planner"]:
                    reasoning_effort = "high"    # 일관성과 정확성 중요
                    text_verbosity = "medium"
                elif request.agent_type in ["screener", "fundamental_fetcher"]:
                    reasoning_effort = "low"     # 빠른 처리 우선
                    text_verbosity = "low"
                
                # API 호출 파라미터 (새로운 GPT-5 형식)
                kwargs = {
                    "model": self.actual_model_name,
                    "input": input_messages,
                    "text": {
                        "format": {
                            "type": "text"
                        },
                        "verbosity": text_verbosity
                    },
                    "reasoning": {
                        "effort": reasoning_effort
                    },
                    "tools": [],
                    "store": True,
                    "include": [
                        "reasoning.encrypted_content"
                    ]
                }
                
                # OpenAI GPT-5 API 호출
                response = self.client.responses.create(**kwargs)
                
            else:
                # 기존 GPT-4 API 구조 유지
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
                    kwargs["temperature"] = 0.2
                elif request.agent_type in ["portfolio_rebalancer", "trade_planner"]:
                    kwargs["temperature"] = 0.1
                
                # OpenAI API 호출
                response = self.client.chat.completions.create(**kwargs)
            
            end_time = time.time()
            response_time = end_time - start_time
            
            # 응답 내용 추출 (GPT-5 vs GPT-4 구분)
            if is_gpt5_model:
                # GPT-5 새로운 응답 구조 - 다양한 구조 시도
                content = ""
                if hasattr(response, 'choices') and response.choices:
                    choice = response.choices[0]
                    # 여러 가능한 구조 확인
                    if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                        content = choice.message.content or ""
                    elif hasattr(choice, 'text'):
                        content = choice.text or ""
                    elif hasattr(choice, 'content'):
                        content = choice.content or ""
                elif hasattr(response, 'output'):
                    # 새로운 GPT-5 output 구조
                    output = response.output
                    if hasattr(output, 'content'):
                        content = output.content or ""
                    elif hasattr(output, 'text'):
                        content = output.text or ""
                elif hasattr(response, 'output_text'):
                    content = response.output_text or ""
                elif hasattr(response, 'text'):
                    content = response.text or ""
                elif hasattr(response, 'content'):
                    content = response.content or ""
                
                # 디버깅용 로그
                if not content:
                    print(f"GPT-5 response.output_text: {getattr(response, 'output_text', 'NONE')}")
                    print(f"GPT-5 response.text: {getattr(response, 'text', 'NONE')}")
                    if hasattr(response, 'output'):
                        print(f"GPT-5 response.output: {response.output}")
                    
                    # 강제로 output_text나 text 사용
                    if hasattr(response, 'output_text') and response.output_text:
                        content = str(response.output_text)
                    elif hasattr(response, 'text') and response.text:
                        content = str(response.text)
                
                # GPT-5 토큰 사용량 (응답 구조에 따라 조정 필요)
                if hasattr(response, 'usage'):
                    usage = response.usage
                    input_tokens = getattr(usage, 'prompt_tokens', 0) or getattr(usage, 'input_tokens', 0)
                    output_tokens = getattr(usage, 'completion_tokens', 0) or getattr(usage, 'output_tokens', 0)
                    total_tokens = input_tokens + output_tokens
                else:
                    # 토큰 사용량 추정
                    input_tokens = self._estimate_tokens(user_content)
                    output_tokens = self._estimate_tokens(content)
                    total_tokens = input_tokens + output_tokens
            else:
                # 기존 GPT-4 응답 구조
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
            
            # 메타데이터 구성 (GPT-5 vs GPT-4 구분)
            metadata = {
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'model_alias': self.model_name,
                'api_version': 'gpt-5' if is_gpt5_model else 'gpt-4'
            }
            
            if is_gpt5_model:
                metadata.update({
                    'reasoning_effort': reasoning_effort,
                    'text_verbosity': text_verbosity,
                    'has_reasoning': True
                })
            else:
                metadata.update({
                    'finish_reason': response.choices[0].finish_reason,
                    'temperature': kwargs.get('temperature', self.default_temperature)
                })
            
            llm_response = LLMResponse(
                content=content,
                model_used=self.actual_model_name,
                tokens_used=total_tokens,
                cost=cost,
                response_time=response_time,
                confidence_score=confidence_score,
                metadata=metadata
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
    
    def _estimate_tokens(self, text: str) -> int:
        """텍스트의 토큰 수 추정 (GPT-5용)"""
        # 대략적인 토큰 수 계산 (1 token ≈ 0.75 words)
        word_count = len(text.split())
        return int(word_count / 0.75)
    
    def get_model_info(self) -> Dict[str, Any]:
        """현재 사용 중인 모델 정보 반환"""
        context_lengths = {
            'gpt-5': 200000,              # GPT-5 확장된 컨텍스트
            'gpt-5-nano': 128000,         # 경량 모델
            'gpt-5-mini': 128000,         # 중간 모델
            'gpt-4o': 128000,
            'gpt-4-turbo-preview': 128000,
            'gpt-4o-mini': 128000
        }
        
        is_gpt5_model = self.actual_model_name.startswith('gpt-5')
        
        info = {
            'provider': self.provider_name,
            'model_alias': self.model_name,
            'actual_model': self.actual_model_name,
            'pricing': self.MODEL_PRICING.get(self.actual_model_name),
            'max_context_length': context_lengths.get(self.actual_model_name, 128000),
            'supports_system_prompt': True,
            'supports_function_calling': True,
            'is_nano_version': 'nano' in self.model_name or 'mini' in self.model_name,
            'api_version': 'gpt-5' if is_gpt5_model else 'gpt-4'
        }
        
        # GPT-5 특별 기능들
        if is_gpt5_model:
            info.update({
                'supports_reasoning': True,
                'supports_verbosity_control': True,
                'supports_effort_control': True,
                'supports_encrypted_reasoning': True
            })
        
        return info