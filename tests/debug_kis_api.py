"""
KIS API 상세 디버깅 스크립트
403 오류 원인 분석 및 해결
"""
import os
import sys
import json
import requests
from datetime import datetime

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.kis_auth import KISAuth
from config.settings import settings


def debug_token_request():
    """토큰 발급 요청 상세 디버깅"""
    print("🔍 토큰 발급 상세 디버깅")
    print("=" * 50)

    auth = KISAuth(environment='paper')

    # 요청 정보 출력
    payload = {
        "grant_type": "client_credentials",
        "appkey": auth.tr_env.my_app,
        "appsecret": auth.tr_env.my_sec
    }

    url = f"{auth.tr_env.my_url}/oauth2/tokenP"
    headers = auth._get_base_headers()

    print(f"📍 URL: {url}")
    print(f"🔑 App Key: {payload['appkey'][:10]}...")
    print(f"🔐 App Secret: {payload['appsecret'][:20]}...")
    print(f"📋 Headers: {json.dumps(headers, indent=2)}")
    print(f"📦 Payload: {json.dumps(payload, indent=2)}")
    print()

    try:
        print("🚀 토큰 발급 요청 중...")
        response = requests.post(url, data=json.dumps(payload), headers=headers, timeout=10)

        print(f"📊 응답 코드: {response.status_code}")
        print(f"📋 응답 헤더: {dict(response.headers)}")

        if response.status_code == 200:
            result = response.json()
            print(f"✅ 토큰 발급 성공!")
            print(f"📄 응답 내용: {json.dumps(result, indent=2, ensure_ascii=False)}")
            return result.get('access_token')
        else:
            print(f"❌ 토큰 발급 실패: {response.status_code}")
            print(f"📄 오류 내용: {response.text}")
            return None

    except Exception as e:
        print(f"❌ 토큰 요청 실패: {e}")
        return None


def debug_simple_api_call(token):
    """간단한 API 호출 디버깅"""
    print("\n🔍 간단한 API 호출 디버깅")
    print("=" * 50)

    if not token:
        print("❌ 토큰이 없어서 API 호출을 건너뜁니다.")
        return

    auth = KISAuth(environment='paper')

    # 가장 간단한 API부터 시도 - 시장 운영시간 조회
    url = f"{auth.tr_env.my_url}/uapi/domestic-stock/v1/quotations/chk-holiday"

    headers = {
        "Content-Type": "application/json",
        "Accept": "text/plain",
        "charset": "UTF-8",
        "User-Agent": auth.config['my_agent'],
        "authorization": f"Bearer {token}",
        "appkey": auth.tr_env.my_app,
        "appsecret": auth.tr_env.my_sec,
        "tr_id": "CTCA0903R",
        "custtype": "P"
    }

    params = {
        "BASS_DT": datetime.now().strftime("%Y%m%d"),
        "CTX_AREA_NK": "",
        "CTX_AREA_FK": ""
    }

    print(f"📍 URL: {url}")
    print(f"🔖 TR_ID: CTCA0903R")
    print(f"📅 기준일: {params['BASS_DT']}")
    print(f"🔑 토큰: {token[:20]}...")
    print(f"📋 헤더 개수: {len(headers)}")
    print()

    try:
        print("🚀 API 호출 중...")
        response = requests.get(url, headers=headers, params=params, timeout=10)

        print(f"📊 응답 코드: {response.status_code}")
        print(f"📋 응답 헤더: {dict(response.headers)}")

        if response.status_code == 200:
            result = response.json()
            print(f"✅ API 호출 성공!")
            print(f"📄 응답 내용: {json.dumps(result, indent=2, ensure_ascii=False)}")
            return True
        else:
            print(f"❌ API 호출 실패: {response.status_code}")
            print(f"📄 오류 내용: {response.text}")

            # 응답 내용 파싱 시도
            try:
                error_data = response.json()
                print(f"📋 파싱된 오류: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
            except:
                print("📋 JSON 파싱 실패")

            return False

    except Exception as e:
        print(f"❌ API 호출 실패: {e}")
        return False


def debug_tr_id_variations(token):
    """다양한 TR_ID로 테스트"""
    print("\n🔍 다양한 TR_ID 테스트")
    print("=" * 50)

    if not token:
        print("❌ 토큰이 없어서 테스트를 건너뜁니다.")
        return

    auth = KISAuth(environment='paper')

    # 모의투자용 TR_ID 목록
    test_cases = [
        ("VTTC8434R", "주식잔고조회"),  # 모의투자용
        ("FHKST01010100", "주식현재가시세"),  # 공통
        ("CTCA0903R", "휴장일조회")  # 공통
    ]

    for tr_id, description in test_cases:
        print(f"\n🧪 테스트: {tr_id} ({description})")

        headers = {
            "Content-Type": "application/json",
            "Accept": "text/plain",
            "charset": "UTF-8",
            "User-Agent": auth.config['my_agent'],
            "authorization": f"Bearer {token}",
            "appkey": auth.tr_env.my_app,
            "appsecret": auth.tr_env.my_sec,
            "tr_id": tr_id,
            "custtype": "P"
        }

        if tr_id == "VTTC8434R":
            # 잔고조회용 파라미터
            url = f"{auth.tr_env.my_url}/uapi/domestic-stock/v1/trading/inquire-balance"
            params = {
                "CANO": auth.tr_env.my_acct,
                "ACNT_PRDT_CD": auth.tr_env.my_prod,
                "AFHR_FLPR_YN": "N",
                "OFL_YN": "",
                "INQR_DVSN": "02",
                "UNPR_DVSN": "01",
                "FUND_STTL_ICLD_YN": "N",
                "FNCG_AMT_AUTO_RDPT_YN": "N",
                "PRCS_DVSN": "01",
                "CTX_AREA_FK100": "",
                "CTX_AREA_NK100": ""
            }
            response = requests.get(url, headers=headers, params=params, timeout=10)

        elif tr_id == "FHKST01010100":
            # 주식현재가용 파라미터
            url = f"{auth.tr_env.my_url}/uapi/domestic-stock/v1/quotations/inquire-price"
            params = {
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": "005930"  # 삼성전자
            }
            response = requests.get(url, headers=headers, params=params, timeout=10)

        else:
            # 휴장일조회용 파라미터
            url = f"{auth.tr_env.my_url}/uapi/domestic-stock/v1/quotations/chk-holiday"
            params = {
                "BASS_DT": datetime.now().strftime("%Y%m%d"),
                "CTX_AREA_NK": "",
                "CTX_AREA_FK": ""
            }
            response = requests.get(url, headers=headers, params=params, timeout=10)

        print(f"   📊 응답: {response.status_code}")
        if response.status_code == 200:
            print(f"   ✅ 성공")
        else:
            print(f"   ❌ 실패: {response.text[:100]}...")


def main():
    """메인 디버깅 실행"""
    print("🐛 KIS API 상세 디버깅 시작")
    print(f"⏰ 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # 1. 토큰 발급 디버깅
    token = debug_token_request()

    # 2. 간단한 API 호출 디버깅
    debug_simple_api_call(token)

    # 3. 다양한 TR_ID 테스트
    debug_tr_id_variations(token)

    print(f"\n⏰ 디버깅 완료: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()