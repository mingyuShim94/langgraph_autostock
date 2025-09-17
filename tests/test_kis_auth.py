"""
KIS 인증 시스템 테스트
실제 API 키 없이도 구조 검증 가능
"""
import os
import sys
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.kis_auth import KISAuth, authenticate, get_auth_instance
from config.settings import settings
from src.exceptions import APIConnectionError


class TestKISAuth:
    """KIS 인증 시스템 테스트 클래스"""

    @pytest.fixture
    def mock_auth(self):
        """테스트용 KIS 인증 인스턴스"""
        return KISAuth(environment='paper')

    def test_auth_initialization(self, mock_auth):
        """인증 인스턴스 초기화 테스트"""
        assert mock_auth.environment == 'paper'
        assert mock_auth.token_cache is None
        assert mock_auth.token_expires_at is None
        assert mock_auth.tr_env is not None

    def test_paper_trading_detection(self, mock_auth):
        """모의투자 환경 감지 테스트"""
        assert mock_auth.is_paper_trading() == True

        prod_auth = KISAuth(environment='prod')
        assert prod_auth.is_paper_trading() == False

    def test_account_info_retrieval(self, mock_auth):
        """계좌 정보 조회 테스트"""
        account_info = mock_auth.get_account_info()

        required_keys = ['account_number', 'product_code', 'environment', 'base_url']
        for key in required_keys:
            assert key in account_info

        assert account_info['environment'] == 'paper'

    def test_base_headers_generation(self, mock_auth):
        """기본 헤더 생성 테스트"""
        headers = mock_auth._get_base_headers()

        required_headers = ['Content-Type', 'Accept', 'charset', 'User-Agent']
        for header in required_headers:
            assert header in headers

        assert headers['Content-Type'] == 'application/json'

    def test_mock_token_creation(self, mock_auth):
        """Mock 토큰 생성 테스트"""
        result = mock_auth._create_mock_token()

        assert result == True
        assert mock_auth.token_cache is not None
        assert mock_auth.token_expires_at is not None
        assert 'mock_token' in mock_auth.token_cache

    def test_token_validation(self, mock_auth):
        """토큰 유효성 검증 테스트"""
        # 토큰 없는 상태
        assert mock_auth._read_token() is None

        # Mock 토큰 생성
        mock_auth._create_mock_token()
        token = mock_auth._read_token()

        assert token is not None
        assert token == mock_auth.token_cache

    def test_authentication_without_api_keys(self, mock_auth):
        """API 키 없이 인증 테스트 (Mock 토큰 사용)"""
        result = mock_auth.authenticate()

        assert result == True
        assert mock_auth.token_cache is not None
        assert 'mock_token' in mock_auth.token_cache

    def test_auth_headers_generation(self, mock_auth):
        """인증 헤더 생성 테스트"""
        # 토큰 없는 상태에서 에러 확인
        with pytest.raises(APIConnectionError):
            mock_auth.get_auth_headers("TEST_TR_ID")

        # 인증 후 헤더 생성
        mock_auth.authenticate()
        headers = mock_auth.get_auth_headers("TEST_TR_ID")

        required_auth_headers = ['authorization', 'appkey', 'appsecret', 'tr_id', 'custtype']
        for header in required_auth_headers:
            assert header in headers

        assert headers['tr_id'] == 'TEST_TR_ID'
        assert 'Bearer' in headers['authorization']

    def test_smart_sleep_timing(self, mock_auth):
        """Rate limiting 지연 시간 테스트"""
        start_time = datetime.now()
        mock_auth.smart_sleep()
        end_time = datetime.now()

        # 모의투자는 0.5초 지연
        elapsed = (end_time - start_time).total_seconds()
        assert elapsed >= 0.4  # 약간의 여유를 둠

    def test_environment_switching(self):
        """환경 전환 테스트"""
        paper_auth = KISAuth('paper')
        prod_auth = KISAuth('prod')

        assert paper_auth.environment == 'paper'
        assert prod_auth.environment == 'prod'

        # URL이 환경에 맞게 설정되는지 확인
        assert 'vts' in paper_auth.tr_env.my_url  # 모의투자 URL
        assert 'vts' not in prod_auth.tr_env.my_url  # 실전투자 URL

    @patch('requests.post')
    def test_real_api_call_simulation(self, mock_post, mock_auth):
        """실제 API 호출 시뮬레이션 (Mock 응답)"""
        # Mock 응답 설정
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'access_token': 'real_token_12345',
            'access_token_token_expired': '2024-12-31 23:59:59'
        }
        mock_post.return_value = mock_response

        # 실제 API 키가 있다고 가정하고 테스트
        with patch.object(mock_auth.tr_env, 'my_app', 'test_app_key'):
            with patch.object(mock_auth.tr_env, 'my_sec', 'test_app_secret'):
                result = mock_auth._request_new_token()

                assert result == True
                assert mock_auth.token_cache == 'real_token_12345'

    def test_global_auth_instance(self):
        """글로벌 인증 인스턴스 테스트"""
        auth1 = get_auth_instance('paper')
        auth2 = get_auth_instance('paper')

        # 같은 환경이면 같은 인스턴스
        assert auth1 is auth2

        # 다른 환경이면 새 인스턴스
        auth3 = get_auth_instance('prod')
        assert auth1 is not auth3

    def test_convenience_authenticate_function(self):
        """편의 함수 테스트"""
        auth = authenticate('paper')

        assert isinstance(auth, KISAuth)
        assert auth.environment == 'paper'
        assert auth.token_cache is not None


class TestKISSettings:
    """KIS 설정 시스템 테스트"""

    def test_kis_config_generation(self):
        """KIS 설정 생성 테스트"""
        config = settings.get_kis_config()

        required_keys = [
            'my_app', 'my_sec', 'paper_app', 'paper_sec',
            'my_acct_stock', 'my_paper_stock', 'my_prod',
            'prod', 'vps', 'my_agent'
        ]

        for key in required_keys:
            assert key in config

    def test_environment_based_config(self):
        """환경별 설정 테스트"""
        # 모의투자 환경
        with patch.object(settings, 'KIS_ENVIRONMENT', 'paper'):
            config = settings.get_kis_config()
            # 모의투자 설정이 기본값으로 사용되는지 확인
            assert config['my_app'] == settings.KIS_PAPER_APP_KEY

        # 실전투자 환경
        with patch.object(settings, 'KIS_ENVIRONMENT', 'prod'):
            config = settings.get_kis_config()
            # 실전투자 설정이 기본값으로 사용되는지 확인
            assert config['my_app'] == settings.KIS_APP_KEY

    def test_kis_headers_generation(self):
        """KIS 헤더 생성 테스트"""
        headers = settings.get_kis_headers()

        assert 'Content-Type' in headers
        assert 'User-Agent' in headers
        assert headers['Content-Type'] == 'application/json'


if __name__ == "__main__":
    # 간단한 실행 테스트
    print("=== KIS Auth 기본 테스트 ===")

    try:
        # 인증 인스턴스 생성
        auth = KISAuth('paper')
        print(f"✅ 인증 인스턴스 생성 성공: {auth.environment}")

        # 계좌 정보 확인
        account_info = auth.get_account_info()
        print(f"✅ 계좌 정보: {account_info}")

        # Mock 인증 테스트
        auth.authenticate()
        print(f"✅ Mock 인증 성공: {auth.token_cache[:20]}...")

        # 헤더 생성 테스트
        headers = auth.get_auth_headers("TEST")
        print(f"✅ 인증 헤더 생성 성공: {len(headers)} 개 헤더")

        print("\n🎉 모든 기본 테스트 통과!")

    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()