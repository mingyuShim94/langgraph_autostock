"""
KIS API 실제 연결 테스트
제공받은 API 키로 실제 토큰 발급 및 API 호출 테스트
"""
import os
import sys
import json
from datetime import datetime

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.kis_auth import KISAuth, authenticate
from config.settings import settings


def test_real_authentication():
    """실제 API 키로 인증 테스트"""
    print("🔐 KIS API 실제 인증 테스트 시작")
    print("=" * 50)

    try:
        # 모의투자 환경으로 인증 인스턴스 생성
        auth = KISAuth(environment='paper')

        print(f"📊 환경: {auth.environment}")
        print(f"📍 서버: {auth.tr_env.my_url}")
        print(f"🔑 앱키: {auth.tr_env.my_app[:10]}...")
        print(f"🏦 계좌: {auth.tr_env.my_acct}")
        print()

        # 실제 토큰 발급 시도
        print("🚀 토큰 발급 시도...")
        success = auth.authenticate(force_refresh=True)

        if success:
            print("✅ 토큰 발급 성공!")
            print(f"🎫 토큰: {auth.token_cache[:20]}...")
            print(f"⏰ 만료시간: {auth.token_expires_at}")

            # 인증 헤더 생성 테스트
            headers = auth.get_auth_headers("TEST_TR_ID")
            print(f"📋 헤더 생성 성공: {len(headers)}개")

            return True
        else:
            print("❌ 토큰 발급 실패")
            return False

    except Exception as e:
        print(f"❌ 인증 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_basic_api_call():
    """기본 API 호출 테스트"""
    print("\n📡 기본 API 호출 테스트")
    print("=" * 50)

    try:
        # 인증 수행
        auth = authenticate('paper')

        # 테스트용 API 호출 (시장 운영 시간 조회)
        url = f"{auth.tr_env.my_url}/uapi/domestic-stock/v1/quotations/chk-holiday"
        headers = auth.get_auth_headers("CTCA0903R")

        params = {
            "BASS_DT": datetime.now().strftime("%Y%m%d"),
            "CTX_AREA_NK": "",
            "CTX_AREA_FK": ""
        }

        print(f"🌐 URL: {url}")
        print(f"🔖 TR_ID: CTCA0903R")
        print(f"📅 조회일: {params['BASS_DT']}")

        import requests
        response = requests.get(url, headers=headers, params=params, timeout=10)

        print(f"📊 응답 코드: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print("✅ API 호출 성공!")
            print(f"📋 응답 데이터: {json.dumps(result, indent=2, ensure_ascii=False)}")
            return True
        else:
            print(f"❌ API 호출 실패: {response.status_code}")
            print(f"📄 응답 내용: {response.text}")
            return False

    except Exception as e:
        print(f"❌ API 호출 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_account_info():
    """계좌 정보 조회 테스트"""
    print("\n🏦 계좌 정보 조회 테스트")
    print("=" * 50)

    try:
        # 인증 수행
        auth = authenticate('paper')

        # 계좌 정보 출력
        account_info = auth.get_account_info()
        print("📊 계좌 정보:")
        for key, value in account_info.items():
            print(f"   {key}: {value}")

        print(f"\n🔧 기술 정보:")
        print(f"   토큰 캐시 상태: {'있음' if auth.token_cache else '없음'}")
        print(f"   토큰 만료시간: {auth.token_expires_at}")
        print(f"   Rate limiting: {0.5 if auth.is_paper_trading() else 0.05}초")

        return True

    except Exception as e:
        print(f"❌ 계좌 정보 조회 실패: {e}")
        return False


def test_configuration_validation():
    """설정 검증 재실행"""
    print("\n⚙️ 설정 검증 (API 키 설정 후)")
    print("=" * 50)

    try:
        from tests.test_kis_config import KISConfigValidator

        validator = KISConfigValidator()
        result = validator.validate_all()

        return result['is_valid']

    except Exception as e:
        print(f"❌ 설정 검증 실패: {e}")
        return False


def main():
    """메인 테스트 실행"""
    print("🚀 KIS API 실제 연결 테스트 시작")
    print(f"⏰ 테스트 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    test_results = []

    # 1. 설정 검증
    print("1️⃣ 설정 검증 테스트")
    config_valid = test_configuration_validation()
    test_results.append(("설정 검증", config_valid))

    if not config_valid:
        print("❌ 설정 검증 실패. 테스트를 중단합니다.")
        return False

    # 2. 실제 인증 테스트
    print("\n2️⃣ 실제 인증 테스트")
    auth_success = test_real_authentication()
    test_results.append(("실제 인증", auth_success))

    if not auth_success:
        print("❌ 인증 실패. API 호출 테스트를 건너뜁니다.")
    else:
        # 3. 기본 API 호출 테스트
        print("\n3️⃣ 기본 API 호출 테스트")
        api_success = test_basic_api_call()
        test_results.append(("기본 API 호출", api_success))

        # 4. 계좌 정보 테스트
        print("\n4️⃣ 계좌 정보 테스트")
        account_success = test_account_info()
        test_results.append(("계좌 정보", account_success))

    # 결과 요약
    print("\n" + "=" * 60)
    print("📊 테스트 결과 요약")
    print("=" * 60)

    for test_name, result in test_results:
        status = "✅ 성공" if result else "❌ 실패"
        print(f"{test_name}: {status}")

    success_count = sum(1 for _, result in test_results if result)
    total_count = len(test_results)

    print(f"\n📈 성공률: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")

    if success_count == total_count:
        print("🎉 모든 테스트 성공! KIS API 연결이 완벽하게 동작합니다.")
    elif success_count > 0:
        print("⚠️ 일부 테스트 성공. 부분적으로 동작합니다.")
    else:
        print("❌ 모든 테스트 실패. 설정을 확인해주세요.")

    print(f"⏰ 테스트 완료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    return success_count == total_count


if __name__ == "__main__":
    main()