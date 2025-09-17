"""
KIS API Rate Limit 고려 테스트
1분 대기 후 토큰 발급 재시도
"""
import os
import sys
import time
import json
from datetime import datetime

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.kis_auth import KISAuth


def test_with_rate_limit():
    """Rate Limit을 고려한 테스트"""
    print("⏰ KIS API Rate Limit 고려 테스트")
    print("=" * 50)

    auth = KISAuth(environment='paper')

    print(f"📊 환경: {auth.environment}")
    print(f"📍 서버: {auth.tr_env.my_url}")
    print(f"🔑 앱키: {auth.tr_env.my_app[:10]}...")
    print(f"🏦 계좌: {auth.tr_env.my_acct}")
    print()

    # 토큰 발급 시도
    print("🚀 토큰 발급 시도 중...")
    print("⚠️ Rate Limit: 1분당 1회 제한")

    try:
        import requests

        payload = {
            "grant_type": "client_credentials",
            "appkey": auth.tr_env.my_app,
            "appsecret": auth.tr_env.my_sec
        }

        url = f"{auth.tr_env.my_url}/oauth2/tokenP"
        headers = auth._get_base_headers()

        response = requests.post(url, data=json.dumps(payload), headers=headers, timeout=10)

        print(f"📊 응답 코드: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            token = result.get('access_token')
            expires_at = result.get('access_token_token_expired')

            print("✅ 토큰 발급 성공!")
            print(f"🎫 토큰: {token[:20]}...")
            print(f"⏰ 만료시간: {expires_at}")

            # 토큰으로 간단한 API 호출 테스트
            return test_simple_api_with_token(auth, token)

        elif response.status_code == 403:
            error_data = response.json()
            error_code = error_data.get('error_code', '')
            error_desc = error_data.get('error_description', '')

            if 'EGW00133' in error_code:
                print("⚠️ Rate Limit 제한 감지")
                print(f"📄 오류 메시지: {error_desc}")
                print("⏳ 1분 대기 후 재시도...")

                # 60초 대기 (카운트다운 표시)
                for i in range(60, 0, -1):
                    print(f"\r⏰ 대기 중... {i:2d}초 남음", end="", flush=True)
                    time.sleep(1)
                print("\n⏰ 대기 완료!")

                # 재시도
                print("🔄 토큰 발급 재시도...")
                response = requests.post(url, data=json.dumps(payload), headers=headers, timeout=10)

                if response.status_code == 200:
                    result = response.json()
                    token = result.get('access_token')
                    expires_at = result.get('access_token_token_expired')

                    print("✅ 토큰 발급 성공!")
                    print(f"🎫 토큰: {token[:20]}...")
                    print(f"⏰ 만료시간: {expires_at}")

                    # 토큰으로 API 호출 테스트
                    return test_simple_api_with_token(auth, token)
                else:
                    print(f"❌ 재시도 실패: {response.status_code}")
                    print(f"📄 오류: {response.text}")
                    return False
            else:
                print(f"❌ 다른 오류: {error_code} - {error_desc}")
                return False
        else:
            print(f"❌ 예상치 못한 오류: {response.status_code}")
            print(f"📄 응답: {response.text}")
            return False

    except Exception as e:
        print(f"❌ 토큰 발급 실패: {e}")
        return False


def test_simple_api_with_token(auth, token):
    """토큰을 사용한 간단한 API 호출"""
    print("\n📡 토큰으로 API 호출 테스트")
    print("=" * 40)

    try:
        import requests

        # 삼성전자 현재가 조회 (가장 기본적인 API)
        url = f"{auth.tr_env.my_url}/uapi/domestic-stock/v1/quotations/inquire-price"

        headers = {
            "Content-Type": "application/json",
            "Accept": "text/plain",
            "charset": "UTF-8",
            "User-Agent": auth.config['my_agent'],
            "authorization": f"Bearer {token}",
            "appkey": auth.tr_env.my_app,
            "appsecret": auth.tr_env.my_sec,
            "tr_id": "FHKST01010100",
            "custtype": "P"
        }

        params = {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": "005930"  # 삼성전자
        }

        print(f"📍 API: 삼성전자 현재가 조회")
        print(f"🔖 TR_ID: FHKST01010100")
        print(f"📈 종목코드: 005930 (삼성전자)")

        response = requests.get(url, headers=headers, params=params, timeout=10)

        print(f"📊 응답 코드: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print("✅ API 호출 성공!")

            # 중요한 데이터만 출력
            if 'output' in result:
                output = result['output']
                print(f"📈 현재가: {output.get('stck_prpr', 'N/A')}원")
                print(f"📊 등락률: {output.get('prdy_ctrt', 'N/A')}%")
                print(f"📅 시간: {output.get('stck_cntg_hour', 'N/A')}")
            else:
                print(f"📄 전체 응답: {json.dumps(result, indent=2, ensure_ascii=False)}")

            return True
        else:
            print(f"❌ API 호출 실패: {response.status_code}")
            print(f"📄 오류: {response.text}")
            return False

    except Exception as e:
        print(f"❌ API 호출 실패: {e}")
        return False


def main():
    """메인 테스트"""
    print("🚀 KIS API Rate Limit 고려 테스트 시작")
    print(f"⏰ 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    success = test_with_rate_limit()

    print(f"\n⏰ 테스트 완료: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if success:
        print("🎉 KIS API 연결 및 호출 성공!")
        print("✅ 이제 실제 포트폴리오 조회 테스트 진행 가능")
    else:
        print("❌ KIS API 연결 실패")
        print("📝 API 키나 설정을 다시 확인해주세요")

    return success


if __name__ == "__main__":
    main()