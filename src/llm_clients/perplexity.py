"""
Perplexity 클라이언트 구현

Perplexity의 검색 강화 모델들 (sonar-pro 등)을 지원하는 클라이언트
실시간 웹 검색이 필요한 섹터 리서치 등에 특화
"""

import time
from typing import List, Dict, Any, Optional
import requests
import json

from .base import BaseAgentLLM, LLMRequest, LLMResponse, UsageStats
from .exceptions import (
    APIConnectionError,
    TokenLimitExceededError,
    ModelNotSupportedError,
    ConfigurationError,
    RateLimitError,
    ResponseQualityError
)


class PerplexityClient(BaseAgentLLM):
    """Perplexity LLM 클라이언트"""
    
    # 지원하는 Perplexity 모델들 (실제 사용 가능한 모델만)
    SUPPORTED_MODELS = {
        'sonar-pro': 'sonar-pro',
        'sonar': 'sonar'
    }
    
    # 모델별 토큰 가격 (USD per 1K tokens) - 추정값
    MODEL_PRICING = {
        'sonar-pro': {'input': 0.001, 'output': 0.001},
        'sonar': {'input': 0.0005, 'output': 0.0005}
    }
    
    def __init__(self, model_name: str, api_key: str, **config):
        """
        Perplexity 클라이언트 초기화
        
        Args:
            model_name: 사용할 Perplexity 모델명 (sonar-pro, sonar-large 등)
            api_key: Perplexity API 키
            **config: 추가 설정 (max_tokens, temperature 등)
        """
        # 실제 모델명 매핑 먼저 설정
        if model_name not in self.SUPPORTED_MODELS:
            raise ModelNotSupportedError("perplexity", model_name)
        
        self.actual_model_name = self.SUPPORTED_MODELS[model_name]
        
        # API 엔드포인트
        self.api_url = "https://api.perplexity.ai/chat/completions"
        
        # 부모 클래스 초기화 (validate_config 호출됨)
        super().__init__("perplexity", model_name, api_key, **config)
        
        # 기본 설정
        self.default_max_tokens = config.get('max_tokens', 4000)
        self.default_temperature = config.get('temperature', 0.3)  # 팩트 체크가 중요하므로 낮은 temperature
        
        # HTTP 헤더 설정
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def validate_config(self) -> bool:
        """Perplexity 클라이언트 설정 검증"""
        if not self.api_key:
            raise ConfigurationError("perplexity", "API 키가 설정되지 않았습니다")
        
        if self.model_name not in self.SUPPORTED_MODELS:
            raise ConfigurationError("perplexity", f"지원하지 않는 모델: {self.model_name}")
        
        # API 키 유효성 간단 체크는 실제 사용할 때 검증
        return True
    
    def get_supported_models(self) -> List[str]:
        """지원하는 Perplexity 모델 목록 반환"""
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
        
        pricing = self.MODEL_PRICING.get(self.actual_model_name, {'input': 0.001, 'output': 0.001})
        
        input_cost = (input_tokens / 1000) * pricing['input']
        output_cost = (output_tokens / 1000) * pricing['output']
        
        return input_cost + output_cost
    
    def generate_response(self, request: LLMRequest) -> LLMResponse:
        """Perplexity로부터 응답 생성"""
        start_time = time.time()
        
        try:
            # 메시지 구성 (시스템 프롬프트와 사용자 프롬프트 결합)
            user_content = request.prompt
            if request.system_prompt:
                user_content = f"{request.system_prompt}\n\n{request.prompt}"
            
            # 섹터 리서치의 경우 실시간 검색을 위한 프롬프트 최적화
            optimized_prompt = self._optimize_prompt_for_search(user_content, request.agent_type)
            
            # 기본 페이로드 (필수 파라미터만)
            payload = {
                "model": self.actual_model_name,
                "messages": [
                    {"role": "user", "content": optimized_prompt}
                ]
            }
            
            # 옵셔널 파라미터 조건부 추가
            if request.max_tokens:
                payload["max_tokens"] = min(request.max_tokens, 4000)  # Perplexity 한도
            
            if request.temperature is not None:
                payload["temperature"] = max(0.0, min(request.temperature, 1.0))  # 범위 제한
            
            # Perplexity API 호출
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=60  # 실시간 검색 때문에 더 긴 타임아웃
            )
            
            end_time = time.time()
            response_time = end_time - start_time
            
            # 응답 처리
            if response.status_code == 200:
                response_data = response.json()
                
                # 응답 내용 추출
                content = ""
                if response_data.get("choices"):
                    content = response_data["choices"][0]["message"]["content"]
                
                # 토큰 사용량 추출 (또는 추정)
                usage = response_data.get("usage", {})
                input_tokens = usage.get("prompt_tokens", self._estimate_tokens(optimized_prompt))
                output_tokens = usage.get("completion_tokens", self._estimate_tokens(content))
                total_tokens = input_tokens + output_tokens
                
                # 비용 계산
                pricing = self.MODEL_PRICING.get(self.actual_model_name, {'input': 0.001, 'output': 0.001})
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
                        'model_alias': self.model_name,
                        'has_citations': self._has_citations(content),
                        'search_enhanced': True
                    }
                )
                
                # 사용량 통계 업데이트
                self.update_usage_stats(llm_response, success=True)
                
                return llm_response
                
            elif response.status_code == 429:
                self.update_usage_stats(None, success=False)
                raise RateLimitError("perplexity", retry_after=60)
                
            elif response.status_code == 401:
                self.update_usage_stats(None, success=False)
                raise APIConnectionError("perplexity", "인증 실패 - API 키를 확인하세요")
                
            else:
                self.update_usage_stats(None, success=False)
                # 디버깅을 위한 상세 에러 정보
                error_detail = ""
                try:
                    error_response = response.json()
                    error_detail = f" - {error_response}"
                except:
                    error_detail = f" - {response.text[:200]}"
                
                raise APIConnectionError("perplexity", f"API 요청 실패: {response.status_code}{error_detail}")
                
        except requests.exceptions.Timeout:
            self.update_usage_stats(None, success=False)
            raise APIConnectionError("perplexity", "요청 시간 초과")
            
        except requests.exceptions.RequestException as e:
            self.update_usage_stats(None, success=False)
            raise APIConnectionError("perplexity", f"네트워크 오류: {e}")
            
        except Exception as e:
            self.update_usage_stats(None, success=False)
            raise APIConnectionError("perplexity", f"예상치 못한 오류: {e}")
    
    def _optimize_prompt_for_search(self, prompt: str, agent_type: str) -> str:
        """검색 최적화를 위한 프롬프트 개선"""
        if agent_type == "sector_researcher":
            # 섹터 리서치는 실시간 정보가 중요
            return f"""최신 시장 정보를 바탕으로 다음 질문에 답해주세요. 
가능한 한 최신 데이터, 뉴스, 시장 동향을 포함하여 답변해주세요.

{prompt}

응답에는 다음을 포함해주세요:
1. 최신 시장 동향 (최근 1주일 내)
2. 관련 뉴스나 발표 사항
3. 구체적인 수치나 데이터
4. 정보 출처"""
        
        return prompt  # 다른 에이전트는 원본 프롬프트 사용
    
    def _estimate_tokens(self, text: str) -> int:
        """텍스트의 토큰 수 추정"""
        # 대략적인 토큰 수 계산 (1 token ≈ 0.75 words)
        word_count = len(text.split())
        return int(word_count / 0.75)
    
    def _has_citations(self, content: str) -> bool:
        """응답에 인용문이나 출처가 포함되어 있는지 확인"""
        citation_indicators = ["[", "]", "출처:", "source:", "according to", "reports", "www.", "http"]
        return any(indicator in content.lower() for indicator in citation_indicators)
    
    def _calculate_confidence_score(self, content: str, request: LLMRequest) -> float:
        """응답의 신뢰도 점수 계산 (0.0 ~ 1.0)"""
        if not content or len(content.strip()) < 10:
            return 0.0
        
        # 기본 점수
        score = 0.7
        
        # 인용문이나 출처가 포함된 경우 높은 점수
        if self._has_citations(content):
            score += 0.2
        
        # 구체적인 수치나 데이터가 포함된 경우
        import re
        if re.search(r'\b\d+(\.\d+)?%?\b', content):
            score += 0.1
        
        # 에이전트 타입별 품질 기준
        if request.agent_type == "sector_researcher":
            # 섹터 리서치는 최신성이 중요
            recent_indicators = ["최근", "오늘", "이번 주", "금주", "현재", "2024", "2025"]
            if any(indicator in content for indicator in recent_indicators):
                score += 0.1
            
            # 시장 관련 용어 포함 여부
            market_terms = ["주가", "시장", "투자", "상승", "하락", "거래량", "시가총액"]
            if any(term in content for term in market_terms):
                score += 0.1
        
        # 응답 길이 적절성
        if 100 <= len(content) <= 2000:
            score += 0.1
        
        return min(score, 1.0)
    
    def get_model_info(self) -> Dict[str, Any]:
        """현재 사용 중인 모델 정보 반환"""
        return {
            'provider': self.provider_name,
            'model_alias': self.model_name,
            'actual_model': self.actual_model_name,
            'pricing': self.MODEL_PRICING.get(self.actual_model_name),
            'max_context_length': 128000,  # 128K context
            'supports_system_prompt': True,
            'supports_real_time_search': True,
            'supports_citations': True,
            'is_search_enhanced': True,
            'best_for': ["sector_research", "market_analysis", "real_time_data"]
        }