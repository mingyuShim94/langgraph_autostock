"""
Gemini 클라이언트 구현 (최신 API)

Google의 Gemini 모델들 (2.5-Pro, 2.5-Flash 등)을 지원하는 클라이언트
"""

import time
import os
from typing import List, Dict, Any, Optional
from google import genai
from google.genai import types

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
    
    # 지원하는 Gemini 모델들 (정확한 모델명)
    SUPPORTED_MODELS = {
        'pro-2.5': 'models/gemini-2.5-pro',
        'flash-2.5': 'models/gemini-2.5-flash',
        'flash-lite': 'models/gemini-2.5-flash-lite',
        'pro': 'models/gemini-2.5-pro',  # 기본값
        'flash': 'models/gemini-2.5-flash',  # 기본값
        # 호환성을 위한 이전 버전들 (필요시)
        'pro-1.5': 'models/gemini-1.5-pro',
        'flash-1.5': 'models/gemini-1.5-flash'
    }
    
    # 모델별 토큰 가격 (USD per 1M tokens) - 2025년 기준
    MODEL_PRICING = {
        'models/gemini-2.5-pro': {'input': 1.25, 'output': 5.0},
        'models/gemini-2.5-flash': {'input': 0.075, 'output': 0.3},
        'models/gemini-2.5-flash-lite': {'input': 0.05, 'output': 0.2},  # Lite 버전은 더 저렴
        'models/gemini-1.5-pro': {'input': 1.25, 'output': 5.0},
        'models/gemini-1.5-flash': {'input': 0.075, 'output': 0.3}
    }
    
    def __init__(self, model_name: str, api_key: str, **config):
        """
        Gemini 클라이언트 초기화 (최신 API)
        
        Args:
            model_name: 사용할 Gemini 모델명 (pro-2.5, flash-2.5 등)
            api_key: Google AI API 키
            **config: 추가 설정 (max_tokens, temperature 등)
        """
        # 실제 모델명 매핑 먼저 확인
        if model_name not in self.SUPPORTED_MODELS:
            raise ModelNotSupportedError("gemini", model_name)
        
        self.actual_model_name = self.SUPPORTED_MODELS[model_name]
        
        # 부모 클래스 초기화
        super().__init__("gemini", model_name, api_key, **config)
        
        # 최신 Google AI 클라이언트 초기화
        self.client = genai.Client(api_key=api_key)
        
        # 기본 설정
        self.default_max_tokens = config.get('max_tokens', 4000)
        self.default_temperature = config.get('temperature', 0.7)
        
        # Flash 모델은 더 빠른 응답을 위해 낮은 temperature 사용
        if 'flash' in model_name:
            self.default_temperature = 0.4
        
        # 섹터 리서치용 Google Search 도구 활성화 여부
        self.enable_search = config.get('enable_search', False)
    
    def validate_config(self) -> bool:
        """Gemini 클라이언트 설정 검증"""
        if not self.api_key:
            raise ConfigurationError("gemini", "API 키가 설정되지 않았습니다")
        
        if self.model_name not in self.SUPPORTED_MODELS:
            raise ConfigurationError("gemini", f"지원하지 않는 모델: {self.model_name}")
        
        # API 키 유효성 간단 체크는 실제 사용할 때 검증
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
        """최신 Gemini API로 응답 생성"""
        start_time = time.time()
        
        try:
            # 구조화된 메시지 구성
            user_content = request.prompt
            if request.system_prompt:
                user_content = f"{request.system_prompt}\n\n{request.prompt}"
            
            contents = [
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=user_content)]
                )
            ]
            
            # 도구 설정 (섹터 리서치용 Google Search)
            tools = []
            if (request.agent_type == "sector_researcher" or 
                request.agent_type == "fundamental_fetcher" or 
                self.enable_search):
                tools.append(types.Tool(googleSearch=types.GoogleSearch()))
            
            # 생성 설정
            config_kwargs = {
                "tools": tools if tools else None
            }
            
            # 시스템 지시사항 추가 (에이전트별 특화)
            system_instructions = []
            if request.agent_type == "fundamental_analyst":
                system_instructions.append(
                    types.Part.from_text("당신은 전문적인 펀더멘털 분석가입니다. 재무 데이터를 정확히 분석하고 투자 가치를 평가하세요.")
                )
            elif request.agent_type == "risk_analyst":
                system_instructions.append(
                    types.Part.from_text("당신은 위험 관리 전문가입니다. 포트폴리오 리스크를 정확히 평가하고 위험 요소를 식별하세요.")
                )
            elif request.agent_type == "sector_researcher":
                system_instructions.append(
                    types.Part.from_text("당신은 섹터 리서치 전문가입니다. 실시간 시장 정보를 활용하여 섹터 트렌드를 분석하세요.")
                )
            
            if system_instructions:
                config_kwargs["system_instruction"] = system_instructions
            
            # 선택적 파라미터 추가
            if request.max_tokens:
                config_kwargs["max_output_tokens"] = min(request.max_tokens, 8000)
            if request.temperature is not None:
                config_kwargs["temperature"] = max(0.0, min(request.temperature, 1.0))
            
            # 에이전트별 특별 설정
            if request.agent_type == "risk_analyst":
                config_kwargs["temperature"] = 0.2  # 정확성 중시
            elif request.agent_type == "fundamental_analyst":
                # Thinking Config 활성화 (복잡한 분석용)
                config_kwargs["thinking_config"] = types.ThinkingConfig(thinking_budget=-1)
            
            generate_content_config = types.GenerateContentConfig(**config_kwargs)
            
            # 최신 Gemini API 호출
            response_chunks = list(self.client.models.generate_content_stream(
                model=self.actual_model_name,
                contents=contents,
                config=generate_content_config
            ))
            
            end_time = time.time()
            response_time = end_time - start_time
            
            # 스트리밍 응답 결합
            content = "".join(chunk.text for chunk in response_chunks if chunk.text)
            
            # 토큰 사용량 추정
            input_tokens = self._estimate_tokens(user_content)
            output_tokens = self._estimate_tokens(content)
            total_tokens = input_tokens + output_tokens
            
            # 비용 계산
            pricing = self.MODEL_PRICING.get(self.actual_model_name, {'input': 0.075, 'output': 0.3})
            cost = ((input_tokens / 1000000) * pricing['input'] + 
                   (output_tokens / 1000000) * pricing['output'])
            
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
                    'tools_used': len(tools),
                    'has_search': bool(tools),
                    'stream_chunks': len(response_chunks)
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
    
    def _calculate_confidence_score(self, content: str, request: LLMRequest) -> float:
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
            'models/gemini-2.5-pro': 2000000,        # 2M tokens
            'models/gemini-2.5-flash': 1000000,      # 1M tokens
            'models/gemini-2.5-flash-lite': 1000000, # 1M tokens
            'models/gemini-1.5-pro': 2000000,        # 2M tokens  
            'models/gemini-1.5-flash': 1000000       # 1M tokens
        }
        
        return {
            'provider': self.provider_name,
            'model_alias': self.model_name,
            'actual_model': self.actual_model_name,
            'pricing': self.MODEL_PRICING.get(self.actual_model_name),
            'max_context_length': context_lengths.get(self.actual_model_name, 1000000),
            'supports_system_prompt': True,  # 최신 API는 시스템 지시사항 지원
            'supports_multimodal': True,
            'supports_search': True,  # Google Search 도구 지원
            'supports_streaming': True,  # 스트리밍 응답 지원
            'supports_thinking': True,  # Thinking Config 지원
            'is_flash_version': 'flash' in self.model_name,
            'api_version': 'v2.5'  # 최신 API 버전
        }