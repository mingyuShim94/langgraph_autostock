"""
LV1 Observer - KIS API 인증 모듈
GitHub kis_auth.py 로직을 현재 프로젝트에 맞게 통합
"""
import os
import json
import time
import logging
from datetime import datetime, timedelta
from collections import namedtuple
from typing import Dict, Any, Optional
import requests

from config.settings import settings
from src.exceptions import APIConnectionError

# 로깅 설정
logger = logging.getLogger(__name__)

class KISAuth:
    """KIS API 인증 관리 클래스"""

    def __init__(self, environment: str = None):
        """
        KIS 인증 클래스 초기화

        Args:
            environment: 'paper' (모의투자) 또는 'prod' (실전투자)
        """
        self.environment = environment or settings.KIS_ENVIRONMENT
        self.config = settings.get_kis_config()
        self.token_cache: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None
        self.last_auth_time = datetime.now()

        # GitHub 호환 환경 설정
        self.tr_env = self._create_tr_env()

        logger.info(f"KIS Auth initialized - Environment: {self.environment}")

    def _create_tr_env(self) -> namedtuple:
        """GitHub kis_auth.py 호환 TR 환경 생성"""
        KISEnv = namedtuple('KISEnv', [
            'my_app', 'my_sec', 'my_acct', 'my_prod',
            'my_htsid', 'my_token', 'my_url', 'my_url_ws'
        ])

        is_paper = self.environment == 'paper'

        return KISEnv(
            my_app=self.config['paper_app'] if is_paper else self.config['my_app'],
            my_sec=self.config['paper_sec'] if is_paper else self.config['my_sec'],
            my_acct=self.config['my_paper_stock'] if is_paper else self.config['my_acct_stock'],
            my_prod=self.config['my_prod'],
            my_htsid=self.config['my_htsid'],
            my_token=self.token_cache or '',
            my_url=self.config['vps'] if is_paper else self.config['prod'],
            my_url_ws=self.config['vops'] if is_paper else self.config['ops']
        )

    def _get_base_headers(self) -> Dict[str, str]:
        """기본 API 헤더 반환"""
        return {
            "Content-Type": "application/json",
            "Accept": "text/plain",
            "charset": "UTF-8",
            "User-Agent": self.config['my_agent']
        }

    def _save_token(self, token: str, expires_at: str) -> None:
        """토큰과 만료시간 저장"""
        try:
            self.token_cache = token
            self.token_expires_at = datetime.strptime(expires_at, "%Y-%m-%d %H:%M:%S")

            # TR 환경 업데이트
            self.tr_env = self.tr_env._replace(my_token=token)

            logger.info(f"Token saved successfully, expires at: {self.token_expires_at}")

        except Exception as e:
            logger.error(f"Failed to save token: {e}")
            raise APIConnectionError(f"토큰 저장 실패: {e}", "KIS_AUTH")

    def _read_token(self) -> Optional[str]:
        """저장된 토큰 읽기 및 유효성 검증"""
        try:
            if not self.token_cache or not self.token_expires_at:
                return None

            # 토큰 만료 확인
            now = datetime.now()
            if self.token_expires_at > now:
                logger.info("Valid token found in cache")
                return self.token_cache
            else:
                logger.info("Token expired, need new token")
                return None

        except Exception as e:
            logger.error(f"Failed to read token: {e}")
            return None

    def authenticate(self, force_refresh: bool = False) -> bool:
        """
        KIS API 인증 수행

        Args:
            force_refresh: 강제로 새 토큰 발급

        Returns:
            bool: 인증 성공 여부
        """
        try:
            # 기존 토큰 확인 (강제 갱신이 아닌 경우)
            if not force_refresh:
                existing_token = self._read_token()
                if existing_token:
                    logger.info("Using existing valid token")
                    return True

            # 새 토큰 발급
            return self._request_new_token()

        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            raise APIConnectionError(f"인증 실패: {e}", "KIS_AUTH")

    def _request_new_token(self) -> bool:
        """새 토큰 발급 요청"""
        logger.info(f"Requesting new token for {self.environment} environment")

        # API 키 확인
        app_key = self.tr_env.my_app
        app_secret = self.tr_env.my_sec

        if not app_key or app_key.startswith('your_'):
            logger.warning("API keys not configured - using mock token")
            return self._create_mock_token()

        # 실제 토큰 발급 요청
        payload = {
            "grant_type": "client_credentials",
            "appkey": app_key,
            "appsecret": app_secret
        }

        url = f"{self.tr_env.my_url}/oauth2/tokenP"
        headers = self._get_base_headers()

        try:
            response = requests.post(url, data=json.dumps(payload), headers=headers, timeout=10)

            if response.status_code == 200:
                result = response.json()
                access_token = result.get('access_token')
                expires_at = result.get('access_token_token_expired')

                if access_token and expires_at:
                    self._save_token(access_token, expires_at)
                    logger.info("New token acquired successfully")
                    return True
                else:
                    raise APIConnectionError("토큰 응답 형식 오류", "KIS_AUTH")
            else:
                raise APIConnectionError(f"토큰 발급 실패: {response.status_code}", "KIS_AUTH", response.status_code)

        except requests.RequestException as e:
            logger.error(f"Network error during token request: {e}")
            # 네트워크 오류 시 mock 토큰으로 대체 (개발 단계)
            return self._create_mock_token()

    def _create_mock_token(self) -> bool:
        """개발/테스트용 가짜 토큰 생성"""
        logger.info("Creating mock token for development")

        mock_token = f"mock_token_{self.environment}_{int(time.time())}"
        mock_expires = (datetime.now() + timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")

        self._save_token(mock_token, mock_expires)
        return True

    def get_auth_headers(self, tr_id: str = "") -> Dict[str, str]:
        """API 호출용 인증 헤더 반환"""
        if not self.token_cache:
            raise APIConnectionError("토큰이 없습니다. authenticate()를 먼저 호출하세요.", "KIS_AUTH")

        headers = self._get_base_headers()
        headers.update({
            "authorization": f"Bearer {self.token_cache}",
            "appkey": self.tr_env.my_app,
            "appsecret": self.tr_env.my_sec,
            "tr_id": tr_id,
            "custtype": "P"  # 개인고객
        })

        return headers

    def is_paper_trading(self) -> bool:
        """모의투자 환경인지 확인"""
        return self.environment == "paper"

    def get_account_info(self) -> Dict[str, str]:
        """계좌 정보 반환"""
        return {
            "account_number": self.tr_env.my_acct,
            "product_code": self.tr_env.my_prod,
            "environment": self.environment,
            "base_url": self.tr_env.my_url
        }

    def smart_sleep(self) -> None:
        """API Rate Limiting을 위한 지연"""
        sleep_time = 0.5 if self.is_paper_trading() else 0.05
        logger.debug(f"Rate limiting sleep: {sleep_time}s")
        time.sleep(sleep_time)


# 전역 인스턴스 (옵션)
_global_auth: Optional[KISAuth] = None

def get_auth_instance(environment: str = None) -> KISAuth:
    """글로벌 인증 인스턴스 반환"""
    global _global_auth

    target_env = environment or settings.KIS_ENVIRONMENT

    if _global_auth is None or _global_auth.environment != target_env:
        _global_auth = KISAuth(target_env)

    return _global_auth

def authenticate(environment: str = None, force_refresh: bool = False) -> KISAuth:
    """편의 함수: 인증 수행 후 인스턴스 반환"""
    auth = get_auth_instance(environment)
    auth.authenticate(force_refresh)
    return auth