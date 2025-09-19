"""
LLM 클라이언트 기본 추상 클래스

모든 LLM 클라이언트가 구현해야 할 표준 인터페이스를 정의합니다.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime


@dataclass
class UsageStats:
    """LLM 사용량 통계"""
    total_requests: int
    successful_requests: int
    failed_requests: int
    total_tokens_used: int
    total_cost: float
    average_response_time: float
    last_request_time: Optional[datetime] = None


@dataclass
class LLMResponse:
    """LLM 응답 표준 포맷"""
    content: str
    model_used: str
    tokens_used: int
    cost: float
    response_time: float
    confidence_score: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class LLMRequest:
    """LLM 요청 표준 포맷"""
    prompt: str
    agent_type: str
    model_name: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    system_prompt: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class BaseAgentLLM(ABC):
    """모든 LLM 클라이언트의 기본 추상 클래스"""
    
    def __init__(self, provider_name: str, model_name: str, api_key: str, **config):
        """
        LLM 클라이언트 초기화
        
        Args:
            provider_name: LLM 제공사명 (claude, gpt, gemini, perplexity)
            model_name: 사용할 구체적 모델명 (opus-4.1, gpt-5, flash-2.5 등)
            api_key: API 키
            **config: 추가 설정 옵션들
        """
        self.provider_name = provider_name
        self.model_name = model_name
        self.api_key = api_key
        self.config = config
        self.usage_stats = UsageStats(
            total_requests=0,
            successful_requests=0,
            failed_requests=0,
            total_tokens_used=0,
            total_cost=0.0,
            average_response_time=0.0
        )
        
        # 설정 검증
        self.validate_config()
    
    @abstractmethod
    def generate_response(self, request: LLMRequest) -> LLMResponse:
        """
        LLM으로부터 응답 생성
        
        Args:
            request: 표준화된 LLM 요청 객체
            
        Returns:
            LLMResponse: 표준화된 응답 객체
            
        Raises:
            LLMClientError: 요청 처리 중 오류 발생 시
        """
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        """
        클라이언트 설정 유효성 검증
        
        Returns:
            bool: 설정이 유효한 경우 True
            
        Raises:
            ConfigurationError: 설정이 유효하지 않은 경우
        """
        pass
    
    @abstractmethod
    def get_supported_models(self) -> List[str]:
        """
        지원하는 모델 목록 반환
        
        Returns:
            List[str]: 지원하는 모델명 리스트
        """
        pass
    
    @abstractmethod
    def estimate_cost(self, request: LLMRequest) -> float:
        """
        요청에 대한 예상 비용 계산
        
        Args:
            request: LLM 요청 객체
            
        Returns:
            float: 예상 비용 (USD)
        """
        pass
    
    def update_usage_stats(self, response: LLMResponse, success: bool = True) -> None:
        """사용량 통계 업데이트"""
        self.usage_stats.total_requests += 1
        self.usage_stats.last_request_time = datetime.now()
        
        if success:
            self.usage_stats.successful_requests += 1
            self.usage_stats.total_tokens_used += response.tokens_used
            self.usage_stats.total_cost += response.cost
            
            # 평균 응답 시간 계산
            total_time = (self.usage_stats.average_response_time * 
                         (self.usage_stats.successful_requests - 1) + 
                         response.response_time)
            self.usage_stats.average_response_time = total_time / self.usage_stats.successful_requests
        else:
            self.usage_stats.failed_requests += 1
    
    def get_usage_stats(self) -> UsageStats:
        """현재 사용량 통계 반환"""
        return self.usage_stats
    
    def reset_usage_stats(self) -> None:
        """사용량 통계 초기화"""
        self.usage_stats = UsageStats(
            total_requests=0,
            successful_requests=0,
            failed_requests=0,
            total_tokens_used=0,
            total_cost=0.0,
            average_response_time=0.0
        )
    
    def is_healthy(self) -> bool:
        """클라이언트 상태 확인"""
        if self.usage_stats.total_requests == 0:
            return True
        
        success_rate = self.usage_stats.successful_requests / self.usage_stats.total_requests
        return success_rate >= 0.8  # 80% 이상 성공률
    
    def __str__(self) -> str:
        return f"{self.provider_name}({self.model_name})"
    
    def __repr__(self) -> str:
        return (f"<{self.__class__.__name__} "
                f"provider={self.provider_name} "
                f"model={self.model_name} "
                f"requests={self.usage_stats.total_requests}>")