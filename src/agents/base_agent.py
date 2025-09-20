"""
모든 전문가 에이전트의 기본 클래스

모든 에이전트가 공통으로 상속받는 베이스 클래스로,
LLM 클라이언트 연동, 로깅, 에러 처리 등 공통 기능을 제공합니다.
"""

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Optional
from datetime import datetime

from src.llm_clients.client_factory import create_agent_client
from src.llm_clients.base import LLMRequest, LLMResponse
from src.llm_clients.exceptions import LLMClientError


@dataclass
class AgentContext:
    """에이전트 실행 컨텍스트"""
    agent_id: str
    execution_id: str
    timestamp: datetime
    input_data: Dict[str, Any]
    metadata: Dict[str, Any] = None


@dataclass  
class AgentResult:
    """에이전트 실행 결과"""
    agent_id: str
    execution_id: str
    success: bool
    result_data: Dict[str, Any]
    execution_time: float
    llm_usage: Dict[str, Any] = None
    error_message: Optional[str] = None
    confidence_score: Optional[float] = None


class BaseAgent(ABC):
    """모든 전문가 에이전트의 기본 클래스"""
    
    def __init__(self, agent_type: str, config: Optional[Dict[str, Any]] = None):
        """
        에이전트 초기화
        
        Args:
            agent_type: 에이전트 타입 (config/agent_llm_mapping.yaml의 키)
            config: 추가 설정 (LLM 설정 덮어쓰기 등)
        """
        self.agent_type = agent_type
        self.config = config or {}
        self.logger = logging.getLogger(f"agent.{agent_type}")
        
        # LLM 클라이언트 초기화
        try:
            self.llm_client = create_agent_client(agent_type, **self.config)
            self.logger.info(f"{agent_type} 에이전트 초기화 완료")
        except Exception as e:
            self.logger.error(f"{agent_type} 에이전트 LLM 클라이언트 초기화 실패: {e}")
            raise
    
    def execute(self, context: AgentContext) -> AgentResult:
        """
        에이전트 실행 (템플릿 메서드 패턴)
        
        Args:
            context: 실행 컨텍스트
            
        Returns:
            AgentResult: 실행 결과
        """
        start_time = time.time()
        execution_id = context.execution_id
        
        self.logger.info(f"에이전트 실행 시작: {self.agent_type} (ID: {execution_id})")
        
        try:
            # 입력 데이터 검증
            self._validate_input(context.input_data)
            
            # 실제 작업 수행 (하위 클래스에서 구현)
            result_data = self._process(context)
            
            # 결과 검증
            self._validate_output(result_data)
            
            execution_time = time.time() - start_time
            
            result = AgentResult(
                agent_id=self.agent_type,
                execution_id=execution_id,
                success=True,
                result_data=result_data,
                execution_time=execution_time,
                llm_usage=self._get_llm_usage_stats(),
                confidence_score=self._calculate_confidence(result_data)
            )
            
            self.logger.info(f"에이전트 실행 완료: {self.agent_type} ({execution_time:.2f}초)")
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = str(e)
            
            self.logger.error(f"에이전트 실행 실패: {self.agent_type} - {error_msg}")
            
            return AgentResult(
                agent_id=self.agent_type,
                execution_id=execution_id,
                success=False,
                result_data={},
                execution_time=execution_time,
                error_message=error_msg
            )
    
    @abstractmethod
    def _process(self, context: AgentContext) -> Dict[str, Any]:
        """
        실제 작업 처리 로직 (하위 클래스에서 구현)
        
        Args:
            context: 실행 컨텍스트
            
        Returns:
            Dict[str, Any]: 처리 결과 데이터
        """
        pass
    
    def _validate_input(self, input_data: Dict[str, Any]) -> None:
        """
        입력 데이터 검증 (하위 클래스에서 오버라이드 가능)
        
        Args:
            input_data: 입력 데이터
            
        Raises:
            ValueError: 입력 데이터가 유효하지 않은 경우
        """
        if not isinstance(input_data, dict):
            raise ValueError("입력 데이터는 딕셔너리 형태여야 합니다")
    
    def _validate_output(self, output_data: Dict[str, Any]) -> None:
        """
        출력 데이터 검증 (하위 클래스에서 오버라이드 가능)
        
        Args:
            output_data: 출력 데이터
            
        Raises:
            ValueError: 출력 데이터가 유효하지 않은 경우
        """
        if not isinstance(output_data, dict):
            raise ValueError("출력 데이터는 딕셔너리 형태여야 합니다")
    
    def _calculate_confidence(self, result_data: Dict[str, Any]) -> float:
        """
        결과에 대한 신뢰도 점수 계산 (하위 클래스에서 오버라이드 가능)
        
        Args:
            result_data: 결과 데이터
            
        Returns:
            float: 신뢰도 점수 (0.0 ~ 1.0)
        """
        # 기본 신뢰도 (하위 클래스에서 더 정교한 로직 구현 가능)
        return 0.8
    
    def _get_llm_usage_stats(self) -> Dict[str, Any]:
        """LLM 사용량 통계 반환"""
        if hasattr(self.llm_client, 'usage_stats'):
            return {
                'total_requests': self.llm_client.usage_stats.total_requests,
                'total_cost': self.llm_client.usage_stats.total_cost,
                'tokens_used': self.llm_client.usage_stats.total_tokens_used,
                'avg_response_time': self.llm_client.usage_stats.average_response_time
            }
        return {}
    
    def query_llm(self, prompt: str, **kwargs) -> LLMResponse:
        """
        LLM에 쿼리 전송 (편의 메서드)
        
        Args:
            prompt: 프롬프트 텍스트
            **kwargs: 추가 LLM 요청 옵션
            
        Returns:
            LLMResponse: LLM 응답
        """
        request = LLMRequest(
            prompt=prompt,
            agent_type=self.agent_type,
            **kwargs
        )
        
        return self.llm_client.generate_response(request)
    
    def get_agent_info(self) -> Dict[str, Any]:
        """에이전트 정보 반환"""
        return {
            'agent_type': self.agent_type,
            'agent_class': self.__class__.__name__,
            'llm_provider': self.llm_client.provider_name if self.llm_client else None,
            'llm_model': self.llm_client.model_name if self.llm_client else None,
            'config': self.config
        }