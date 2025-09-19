"""
LLM 클라이언트 공통 예외 클래스들
"""

from typing import Optional, Any


class LLMClientError(Exception):
    """LLM 클라이언트 기본 예외 클래스"""
    
    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[Any] = None):
        super().__init__(message)
        self.error_code = error_code
        self.details = details


class APIConnectionError(LLMClientError):
    """API 연결 실패 예외"""
    
    def __init__(self, provider: str, message: str = "API 연결에 실패했습니다"):
        super().__init__(f"[{provider}] {message}", error_code="CONNECTION_FAILED")
        self.provider = provider


class TokenLimitExceededError(LLMClientError):
    """토큰 한도 초과 예외"""
    
    def __init__(self, provider: str, used_tokens: int, limit: int):
        message = f"토큰 한도 초과: {used_tokens}/{limit}"
        super().__init__(f"[{provider}] {message}", error_code="TOKEN_LIMIT_EXCEEDED")
        self.provider = provider
        self.used_tokens = used_tokens
        self.limit = limit


class ResponseQualityError(LLMClientError):
    """응답 품질 문제 예외"""
    
    def __init__(self, provider: str, issue: str):
        super().__init__(f"[{provider}] 응답 품질 문제: {issue}", error_code="QUALITY_ISSUE")
        self.provider = provider
        self.issue = issue


class ModelNotSupportedError(LLMClientError):
    """지원하지 않는 모델 예외"""
    
    def __init__(self, provider: str, model_name: str):
        message = f"지원하지 않는 모델: {model_name}"
        super().__init__(f"[{provider}] {message}", error_code="MODEL_NOT_SUPPORTED")
        self.provider = provider
        self.model_name = model_name


class RateLimitError(LLMClientError):
    """API 호출 한도 초과 예외"""
    
    def __init__(self, provider: str, retry_after: Optional[int] = None):
        message = "API 호출 한도 초과"
        if retry_after:
            message += f" (재시도까지 {retry_after}초 대기 필요)"
        super().__init__(f"[{provider}] {message}", error_code="RATE_LIMIT_EXCEEDED")
        self.provider = provider
        self.retry_after = retry_after


class ConfigurationError(LLMClientError):
    """설정 오류 예외"""
    
    def __init__(self, provider: str, config_issue: str):
        super().__init__(f"[{provider}] 설정 오류: {config_issue}", error_code="CONFIG_ERROR")
        self.provider = provider
        self.config_issue = config_issue