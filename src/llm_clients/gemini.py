"""
Gemini 클라이언트 구현

Google의 Gemini 모델들 (Flash, Pro 등)을 지원하는 클라이언트
"""

import time
from typing import List, Dict, Any, Optional
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from .base import BaseAgentLLM, LLMRequest, LLMResponse, UsageStats
from .exceptions import (
    APIConnectionError,
    TokenLimitExceededError,
    ModelNotSupportedError,
    ConfigurationError,
    RateLimitError,
    ResponseQualityError
)


class GeminiClient(BaseAgentLLM):
    """Google Gemini LLM 클라이언트"""
    
    # 지원하는 Gemini 모델들
    SUPPORTED_MODELS = {
        'flash-2.5': 'gemini-2.0-flash-exp',
        'flash-2.0': 'gemini-2.0-flash-exp',
        'flash': 'gemini-1.5-flash',
        'flash-1.5': 'gemini-1.5-flash',
        'pro-2.0': 'gemini-2.0-flash-exp',  # Pro 2.0이 출시되면 업데이트 필요
        'pro': 'gemini-1.5-pro',
        'pro-1.5': 'gemini-1.5-pro',
        'flash-lite': 'gemini-1.5-flash'  # 빠른 처리용
    }
    
    # 모델별 토큰 가격 (USD per 1M tokens) - 2024년 기준
    MODEL_PRICING = {
        'gemini-2.0-flash-exp': {'input': 0.075, 'output': 0.3},
        'gemini-1.5-flash': {'input': 0.075, 'output': 0.3}, 
        'gemini-1.5-pro': {'input': 1.25, 'output': 5.0}
    }
    
    def __init__(self, model_name: str, api_key: str, **config):
        """
        Gemini 클라이언트 초기화
        
        Args:
            model_name: 사용할 Gemini 모델명 (flash-2.5, pro-2.0 등)
            api_key: Google AI API 키
            **config: 추가 설정 (max_tokens, temperature 등)
        """
        super().__init__("gemini", model_name, api_key, **config)
        
        # Google AI 클라이언트 초기화
        genai.configure(api_key=api_key)
        
        # 실제 모델명 매핑
        if model_name not in self.SUPPORTED_MODELS:
            raise ModelNotSupportedError("gemini", model_name)
        
        self.actual_model_name = self.SUPPORTED_MODELS[model_name]
        
        # Gemini 모델 인스턴스 생성
        self.model = genai.GenerativeModel(self.actual_model_name)
        
        # 기본 설정
        self.default_max_tokens = config.get('max_tokens', 4000)
        self.default_temperature = config.get('temperature', 0.7)
        
        # Flash 모델은 더 빠른 응답을 위해 낮은 temperature 사용
        if 'flash' in model_name:
            self.default_temperature = 0.4
        
        # 안전 설정 (금융 분석에 필요한 자유도 확보)
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE
        }
    
    def validate_config(self) -> bool:
        """Gemini 클라이언트 설정 검증"""
        if not self.api_key:
            raise ConfigurationError("gemini", "API 키가 설정되지 않았습니다")
        
        if self.model_name not in self.SUPPORTED_MODELS:
            raise ConfigurationError("gemini", f"지원하지 않는 모델: {self.model_name}")
        
        # API 키 유효성 간단 체크
        try:
            # 테스트 요청으로 API 키 검증
            response = self.model.generate_content(
                "Hello",
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=10,
                    temperature=0.1
                ),
                safety_settings=self.safety_settings
            )
            return True
        except Exception as e:
            if "api_key" in str(e).lower() or "authentication" in str(e).lower():
                raise ConfigurationError("gemini", "유효하지 않은 API 키")
            else:
                # 네트워크 오류 등은 일시적일 수 있으므로 경고만 출력
                print(f"Gemini API 연결 확인 실패 (일시적일 수 있음): {e}")
                return True
    
    def get_supported_models(self) -> List[str]:
        """지원하는 Gemini 모델 목록 반환"""
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
        
        pricing = self.MODEL_PRICING.get(self.actual_model_name, {'input': 0.075, 'output': 0.3})
        
        # Gemini는 1M 토큰 기준 가격이므로 1,000,000으로 나눔
        input_cost = (input_tokens / 1000000) * pricing['input']
        output_cost = (output_tokens / 1000000) * pricing['output']
        
        return input_cost + output_cost
    
    def generate_response(self, request: LLMRequest) -> LLMResponse:
        """Gemini로부터 응답 생성"""
        start_time = time.time()
        
        try:
            # 프롬프트 구성 (시스템 프롬프트가 있으면 결합)
            full_prompt = request.prompt
            if request.system_prompt:
                full_prompt = f"{request.system_prompt}\n\n{request.prompt}"
            
            # 생성 설정
            generation_config = genai.types.GenerationConfig(
                max_output_tokens=request.max_tokens or self.default_max_tokens,
                temperature=request.temperature or self.default_temperature
            )
            
            # 에이전트 타입별 특별 설정
            if request.agent_type == "fundamental_analyst":
                # 펀더멘털 분석은 더 긴 컨텍스트 처리 능력 활용
                generation_config.max_output_tokens = min(8000, generation_config.max_output_tokens)
            elif request.agent_type == "risk_analyst":
                # 리스크 분석은 정확성이 중요
                generation_config.temperature = 0.2
            
            # Gemini API 호출
            response = self.model.generate_content(
                full_prompt,
                generation_config=generation_config,
                safety_settings=self.safety_settings
            )
            
            end_time = time.time()
            response_time = end_time - start_time
            
            # 응답 내용 추출
            content = ""
            if response.text:
                content = response.text
            elif response.candidates:
                # 안전 필터에 의해 차단되었을 가능성
                content = "응답이 안전 필터에 의해 차단되었습니다."
            
            # 토큰 사용량 계산 (Gemini는 정확한 토큰 카운트를 제공하지 않으므로 추정)
            input_tokens = self._estimate_tokens(full_prompt)
            output_tokens = self._estimate_tokens(content)
            total_tokens = input_tokens + output_tokens
            
            # 비용 계산
            pricing = self.MODEL_PRICING.get(self.actual_model_name, {'input': 0.075, 'output': 0.3})
            cost = ((input_tokens / 1000000) * pricing['input'] + 
                   (output_tokens / 1000000) * pricing['output'])
            
            # 응답 품질 검증
            confidence_score = self._calculate_confidence_score(content, request, response)
            
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
                    'safety_ratings': response.candidates[0].safety_ratings if response.candidates else None,
                    'finish_reason': response.candidates[0].finish_reason if response.candidates else None
                }
            )
            
            # 사용량 통계 업데이트
            self.update_usage_stats(llm_response, success=True)
            
            return llm_response
            
        except Exception as e:
            self.update_usage_stats(None, success=False)
            
            error_msg = str(e).lower()
            
            if "quota" in error_msg or "rate limit" in error_msg:
                raise RateLimitError("gemini", retry_after=60)
            elif "token" in error_msg and "limit" in error_msg:
                raise TokenLimitExceededError("gemini", len(request.prompt), self.default_max_tokens)
            elif "api_key" in error_msg or "authentication" in error_msg:
                raise APIConnectionError("gemini", "인증 실패")
            else:
                raise APIConnectionError("gemini", f"예상치 못한 오류: {e}")
    
    def _estimate_tokens(self, text: str) -> int:
        """텍스트의 토큰 수 추정"""
        # Gemini는 정확한 토큰 카운터를 제공하지 않으므로 근사치 사용
        # 평균적으로 1 token ≈ 0.75 words (영어 기준)
        # 한국어는 약간 더 많은 토큰 사용
        word_count = len(text.split())
        korean_chars = len([c for c in text if ord(c) >= 0xAC00 and ord(c) <= 0xD7A3])
        
        # 한국어 비율에 따라 토큰 수 조정
        if korean_chars > word_count * 2:  # 한국어가 많은 경우
            return int(word_count * 1.2)
        else:
            return int(word_count / 0.75)
    
    def _calculate_confidence_score(self, content: str, request: LLMRequest, response) -> float:
        """응답의 신뢰도 점수 계산 (0.0 ~ 1.0)"""
        if not content or len(content.strip()) < 10:
            return 0.0
        
        # 기본 점수
        score = 0.7
        
        # 안전 필터 체크
        if "안전 필터" in content or "차단되었습니다" in content:
            return 0.1
        
        # 에이전트 타입별 품질 기준
        if request.agent_type == "fundamental_analyst":
            # 펀더멘털 분석은 재무 지표나 수치가 포함되어야 함
            financial_terms = ["매출", "영업이익", "per", "pbr", "roe", "부채비율", "현금흐름"]
            if any(term in content.lower() for term in financial_terms):
                score += 0.2
                
        elif request.agent_type == "valuation_analyst":
            # 밸류에이션 분석은 구체적인 평가 방법론이 포함되어야 함
            valuation_methods = ["dcf", "per", "pbr", "ev/ebitda", "내재가치", "할인율"]
            if any(method in content.lower() for method in valuation_methods):
                score += 0.2
                
        elif request.agent_type == "flow_analyst":
            # 자금 흐름 분석은 거래량이나 수급 관련 내용이 포함되어야 함
            flow_terms = ["거래량", "외국인", "기관", "개인", "순매수", "순매도", "수급"]
            if any(term in content.lower() for term in flow_terms):
                score += 0.2
        
        # 응답 길이 적절성 (펀더멘털 분석은 긴 응답 선호)
        if request.agent_type in ["fundamental_analyst", "valuation_analyst"]:
            if 200 <= len(content) <= 3000:
                score += 0.1
        else:
            if 50 <= len(content) <= 1500:
                score += 0.1
        
        # Gemini 특성상 구조화된 응답을 잘 생성하므로 보너스
        if any(marker in content for marker in ["###", "**", "1.", "2.", "- "]):
            score += 0.1
        
        return min(score, 1.0)
    
    def get_model_info(self) -> Dict[str, Any]:
        """현재 사용 중인 모델 정보 반환"""
        context_lengths = {
            'gemini-2.0-flash-exp': 1000000,  # 1M tokens
            'gemini-1.5-flash': 1000000,
            'gemini-1.5-pro': 2000000  # 2M tokens
        }
        
        return {
            'provider': self.provider_name,
            'model_alias': self.model_name,
            'actual_model': self.actual_model_name,
            'pricing': self.MODEL_PRICING.get(self.actual_model_name),
            'max_context_length': context_lengths.get(self.actual_model_name, 1000000),
            'supports_system_prompt': False,  # Gemini는 별도 시스템 프롬프트 없음
            'supports_multimodal': True,
            'is_flash_version': 'flash' in self.model_name,
            'safety_settings_enabled': True
        }