"""
LV1 Observer 시스템 기본 설정
"""
import os
from dotenv import load_dotenv
from typing import Dict, Any

# .env 파일 로드
load_dotenv()

class Settings:
    """애플리케이션 설정 클래스"""

    # 환경 설정
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    # API 설정
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    # KIS API 설정
    KIS_APP_KEY = os.getenv("KIS_APP_KEY")
    KIS_APP_SECRET = os.getenv("KIS_APP_SECRET")
    KIS_ACCESS_TOKEN = os.getenv("KIS_ACCESS_TOKEN")
    KIS_ACCOUNT_NUMBER = os.getenv("KIS_ACCOUNT_NUMBER")

    # 뉴스 API 설정
    NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
    NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")

    # 애플리케이션 설정
    DEFAULT_CURRENCY = os.getenv("DEFAULT_CURRENCY", "KRW")
    REPORT_TIMEZONE = os.getenv("REPORT_TIMEZONE", "Asia/Seoul")

    # 이메일 설정 (선택사항)
    SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    EMAIL_USER = os.getenv("EMAIL_USER")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
    NOTIFICATION_EMAIL = os.getenv("NOTIFICATION_EMAIL")

    # KIS API 엔드포인트
    KIS_BASE_URL = "https://openapi.koreainvestment.com:9443"
    KIS_PAPER_BASE_URL = "https://openapivts.koreainvestment.com:29443"  # 모의투자용

    # 뉴스 API 엔드포인트
    NAVER_NEWS_API_URL = "https://openapi.naver.com/v1/search/news.json"

    # 로깅 설정
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE_PATH = "logs/observer.log"

    # 포트폴리오 설정
    MAX_NEWS_PER_STOCK = 5  # 종목당 최대 뉴스 개수
    NEWS_SEARCH_DAYS = 1    # 뉴스 검색 일수

    @classmethod
    def validate_required_settings(cls) -> Dict[str, Any]:
        """필수 설정 값들을 검증합니다."""
        missing_settings = []

        required_settings = [
            ("OPENAI_API_KEY", cls.OPENAI_API_KEY),
            # KIS API는 나중에 실제 계정 생성 후 검증
            # ("KIS_APP_KEY", cls.KIS_APP_KEY),
            # ("KIS_APP_SECRET", cls.KIS_APP_SECRET),
        ]

        for setting_name, setting_value in required_settings:
            if not setting_value or setting_value == f"your_{setting_name.lower()}_here":
                missing_settings.append(setting_name)

        return {
            "is_valid": len(missing_settings) == 0,
            "missing_settings": missing_settings
        }

    @classmethod
    def get_kis_headers(cls) -> Dict[str, str]:
        """KIS API 호출용 헤더를 반환합니다."""
        return {
            "Content-Type": "application/json",
            "authorization": f"Bearer {cls.KIS_ACCESS_TOKEN}",
            "appkey": cls.KIS_APP_KEY,
            "appsecret": cls.KIS_APP_SECRET,
            "tr_id": "",  # 거래 ID는 각 API 호출시 설정
        }

    @classmethod
    def get_naver_headers(cls) -> Dict[str, str]:
        """네이버 뉴스 API 호출용 헤더를 반환합니다."""
        return {
            "X-Naver-Client-Id": cls.NAVER_CLIENT_ID,
            "X-Naver-Client-Secret": cls.NAVER_CLIENT_SECRET,
        }

# 전역 설정 인스턴스
settings = Settings()