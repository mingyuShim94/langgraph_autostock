"""
Claude 클라이언트 구현

Anthropic의 Claude 모델들 (Opus, Sonnet, Haiku 등)을 지원하는 클라이언트
"""

import time
from typing import List, Dict, Any, Optional
import anthropic
from anthropic import Anthropic

from .base import BaseAgentLLM, LLMRequest, LLMResponse, UsageStats
from .exceptions import (
    APIConnectionError,
    TokenLimitExceededError,
    ModelNotSupportedError,
    ConfigurationError,
    RateLimitError,
    ResponseQualityError
)


class ClaudeClient(BaseAgentLLM):
    """Claude LLM 클라이언트"""
    
    # 지원하는 Claude 모델들
    SUPPORTED_MODELS = {
        'opus-4.1': 'claude-3-opus-20240229',
        'opus-3': 'claude-3-opus-20240229', 
        'sonnet-4': 'claude-3-5-sonnet-20241022',
        'sonnet-3.5': 'claude-3-5-sonnet-20241022',
        'sonnet-3': 'claude-3-sonnet-20240229',
        'haiku-3': 'claude-3-haiku-20240307'
    }
    
    # 모델별 토큰 가격 (USD per 1K tokens)
    MODEL_PRICING = {
        'claude-3-opus-20240229': {'input': 0.015, 'output': 0.075},
        'claude-3-5-sonnet-20241022': {'input': 0.003, 'output': 0.015},
        'claude-3-sonnet-20240229': {'input': 0.003, 'output': 0.015},
        'claude-3-haiku-20240307': {'input': 0.00025, 'output': 0.00125}
    }
    
    def __init__(self, model_name: str, api_key: str, **config):
        """
        Claude 클라이언트 초기화
        
        Args:
            model_name: 사용할 Claude 모델명 (opus-4.1, sonnet-3.5 등)
            api_key: Anthropic API 키
            **config: 추가 설정 (max_tokens, temperature 등)
        """
        super().__init__("claude", model_name, api_key, **config)
        
        # Anthropic 클라이언트 초기화
        self.client = Anthropic(api_key=api_key)
        
        # 실제 모델명 매핑
        if model_name not in self.SUPPORTED_MODELS:
            raise ModelNotSupportedError("claude", model_name)
        
        self.actual_model_name = self.SUPPORTED_MODELS[model_name]
        
        # 기본 설정
        self.default_max_tokens = config.get('max_tokens', 4000)
        self.default_temperature = config.get('temperature', 0.7)
    
    def validate_config(self) -> bool:
        """Claude 클라이언트 설정 검증"""
        if not self.api_key:
            raise ConfigurationError("claude", "API 키가 설정되지 않았습니다")
        
        if self.model_name not in self.SUPPORTED_MODELS:
            raise ConfigurationError("claude", f"지원하지 않는 모델: {self.model_name}")
        
        # API 키 유효성 간단 체크
        try:
            # 테스트 요청으로 API 키 검증
            response = self.client.messages.create(
                model=self.actual_model_name,
                max_tokens=10,
                messages=[{"role": "user", "content": "Hello"}]
            )
            return True
        except anthropic.AuthenticationError:
            raise ConfigurationError("claude", "유효하지 않은 API 키")
        except Exception as e:
            # 네트워크 오류 등은 일시적일 수 있으므로 경고만 출력
            print(f"Claude API 연결 확인 실패 (일시적일 수 있음): {e}")
            return True
    
    def get_supported_models(self) -> List[str]:
        """지원하는 Claude 모델 목록 반환"""
        return list(self.SUPPORTED_MODELS.keys())
    
    def estimate_cost(self, request: LLMRequest) -> float:
        """요청에 대한 예상 비용 계산"""
        # 입력 토큰 추정 (대략 1 token = 0.75 words)
        input_tokens = len(request.prompt.split()) / 0.75
        
        # 출력 토큰 추정 (max_tokens 또는 기본값 사용)
        max_tokens = request.max_tokens or self.default_max_tokens
        output_tokens = max_tokens * 0.8  # 평균적으로 max의 80% 사용 가정
        
        pricing = self.MODEL_PRICING.get(self.actual_model_name, {'input': 0.003, 'output': 0.015})
        
        input_cost = (input_tokens / 1000) * pricing['input']
        output_cost = (output_tokens / 1000) * pricing['output']
        
        return input_cost + output_cost
    
    def generate_response(self, request: LLMRequest) -> LLMResponse:
        """Claude로부터 응답 생성"""
        start_time = time.time()
        
        try:
            # 요청 파라미터 구성
            messages = [{"role": "user", "content": request.prompt}]
            
            # 시스템 프롬프트가 있는 경우 추가
            kwargs = {
                "model": self.actual_model_name,
                "max_tokens": request.max_tokens or self.default_max_tokens,
                "temperature": request.temperature or self.default_temperature,
                "messages": messages
            }
            
            if request.system_prompt:
                kwargs["system"] = request.system_prompt
            
            # Claude API 호출
            response = self.client.messages.create(**kwargs)
            
            end_time = time.time()
            response_time = end_time - start_time
            
            # 응답 내용 추출
            content = ""
            if response.content:
                content = " ".join([block.text for block in response.content if hasattr(block, 'text')])
            
            # 토큰 사용량 및 비용 계산
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            total_tokens = input_tokens + output_tokens
            
            pricing = self.MODEL_PRICING.get(self.actual_model_name, {'input': 0.003, 'output': 0.015})
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
                    'stop_reason': response.stop_reason
                }
            )
            
            # 사용량 통계 업데이트
            self.update_usage_stats(llm_response, success=True)
            
            return llm_response
            
        except anthropic.RateLimitError as e:
            self.update_usage_stats(None, success=False)
            raise RateLimitError("claude", retry_after=60)
            
        except anthropic.InvalidRequestError as e:
            self.update_usage_stats(None, success=False)
            if "maximum context length" in str(e).lower():
                raise TokenLimitExceededError("claude", len(request.prompt), self.default_max_tokens)
            raise ResponseQualityError("claude", f"잘못된 요청: {e}")
            
        except anthropic.APIConnectionError as e:
            self.update_usage_stats(None, success=False)
            raise APIConnectionError("claude", f"API 연결 실패: {e}")
            
        except Exception as e:
            self.update_usage_stats(None, success=False)
            raise APIConnectionError("claude", f"예상치 못한 오류: {e}")
    
    def _calculate_confidence_score(self, content: str, request: LLMRequest) -> float:
        """응답의 신뢰도 점수 계산 (0.0 ~ 1.0)"""
        if not content or len(content.strip()) < 10:
            return 0.0
        
        # 기본 점수
        score = 0.7
        
        # 에이전트 타입별 품질 기준 적용
        if request.agent_type == "cio":
            # CIO 에이전트는 구조화된 분석을 요구
            if "분석" in content and "결론" in content:
                score += 0.2
        elif request.agent_type == "technical_analyst":
            # 기술적 분석은 수치나 지표가 포함되어야 함
            if any(indicator in content.lower() for indicator in ["rsi", "macd", "이평선", "%"]):
                score += 0.2
        
        # 응답 길이 적절성 검사
        if 50 <= len(content) <= 2000:
            score += 0.1
        
        return min(score, 1.0)
    
    def get_model_info(self) -> Dict[str, Any]:
        """현재 사용 중인 모델 정보 반환"""
        return {
            'provider': self.provider_name,
            'model_alias': self.model_name,
            'actual_model': self.actual_model_name,
            'pricing': self.MODEL_PRICING.get(self.actual_model_name),
            'max_context_length': 200000 if 'opus' in self.model_name else 200000,
            'supports_system_prompt': True,
            'supports_function_calling': True
        }