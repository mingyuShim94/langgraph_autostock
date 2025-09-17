"""
LV1 Observer - 커스텀 예외 클래스
"""

class ObserverBaseException(Exception):
    """Observer 시스템의 기본 예외 클래스"""
    def __init__(self, message: str, node: str = None, execution_id: str = None):
        self.message = message
        self.node = node
        self.execution_id = execution_id
        super().__init__(self.message)

    def __str__(self):
        parts = [self.message]
        if self.node:
            parts.append(f"Node: {self.node}")
        if self.execution_id:
            parts.append(f"Execution ID: {self.execution_id}")
        return " | ".join(parts)

class PortfolioFetchError(ObserverBaseException):
    """포트폴리오 조회 관련 예외"""
    pass

class NewsCollectionError(ObserverBaseException):
    """뉴스 수집 관련 예외"""
    pass

class ReportGenerationError(ObserverBaseException):
    """리포트 생성 관련 예외"""
    pass

class APIConnectionError(ObserverBaseException):
    """API 연결 관련 예외"""
    def __init__(self, message: str, api_name: str, status_code: int = None, **kwargs):
        self.api_name = api_name
        self.status_code = status_code
        super().__init__(message, **kwargs)

    def __str__(self):
        base_msg = super().__str__()
        if self.status_code:
            return f"{base_msg} | API: {self.api_name} | Status: {self.status_code}"
        else:
            return f"{base_msg} | API: {self.api_name}"

class ConfigurationError(ObserverBaseException):
    """설정 관련 예외"""
    pass

class ValidationError(ObserverBaseException):
    """데이터 검증 관련 예외"""
    pass