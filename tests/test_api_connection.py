"""
API 연결 테스트 스크립트
실제 API 키 설정 후 연결 상태를 확인합니다.
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import requests
from config.settings import settings

def test_openai_api():
    """OpenAI API 연결 테스트"""
    print("🔍 OpenAI API 연결 테스트...")

    if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY.startswith("your_"):
        print("❌ OpenAI API 키가 설정되지 않았습니다.")
        print("   .env 파일에서 OPENAI_API_KEY를 설정해주세요.")
        return False

    try:
        from openai import OpenAI
        client = OpenAI(api_key=settings.OPENAI_API_KEY)

        # 간단한 테스트 요청
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "안녕하세요"}],
            max_tokens=10
        )

        print("✅ OpenAI API 연결 성공!")
        return True

    except Exception as e:
        print(f"❌ OpenAI API 연결 실패: {e}")
        return False

def test_kis_api():
    """한국투자증권 API 연결 테스트"""
    print("\n🔍 KIS API 연결 테스트...")

    if not all([settings.KIS_APP_KEY, settings.KIS_APP_SECRET]) or \
       settings.KIS_APP_KEY.startswith("your_"):
        print("❌ KIS API 키가 설정되지 않았습니다.")
        print("   .env 파일에서 KIS_APP_KEY, KIS_APP_SECRET을 설정해주세요.")
        print("   한국투자증권 API 신청: https://apiportal.koreainvestment.com/")
        return False

    try:
        # 모의투자 환경에서 테스트
        url = f"{settings.KIS_PAPER_BASE_URL}/oauth2/tokenP"
        headers = {
            "Content-Type": "application/json"
        }
        data = {
            "grant_type": "client_credentials",
            "appkey": settings.KIS_APP_KEY,
            "appsecret": settings.KIS_APP_SECRET
        }

        response = requests.post(url, json=data, headers=headers)

        if response.status_code == 200:
            print("✅ KIS API 연결 성공!")
            token_data = response.json()
            print(f"   Access Token: {token_data.get('access_token', '')[:20]}...")
            return True
        else:
            print(f"❌ KIS API 연결 실패: {response.status_code}")
            print(f"   응답: {response.text}")
            return False

    except Exception as e:
        print(f"❌ KIS API 연결 실패: {e}")
        return False

def test_naver_news_api():
    """네이버 뉴스 API 연결 테스트"""
    print("\n🔍 네이버 뉴스 API 연결 테스트...")

    if not all([settings.NAVER_CLIENT_ID, settings.NAVER_CLIENT_SECRET]) or \
       settings.NAVER_CLIENT_ID.startswith("your_"):
        print("❌ 네이버 API 키가 설정되지 않았습니다.")
        print("   .env 파일에서 NAVER_CLIENT_ID, NAVER_CLIENT_SECRET을 설정해주세요.")
        print("   네이버 API 신청: https://developers.naver.com/apps/")
        return False

    try:
        url = settings.NAVER_NEWS_API_URL
        headers = settings.get_naver_headers()
        params = {
            "query": "삼성전자",
            "display": 1,
            "start": 1,
            "sort": "date"
        }

        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 200:
            print("✅ 네이버 뉴스 API 연결 성공!")
            data = response.json()
            print(f"   검색 결과: {data.get('total', 0)}건")
            return True
        else:
            print(f"❌ 네이버 뉴스 API 연결 실패: {response.status_code}")
            print(f"   응답: {response.text}")
            return False

    except Exception as e:
        print(f"❌ 네이버 뉴스 API 연결 실패: {e}")
        return False

def main():
    """모든 API 연결 테스트 실행"""
    print("=" * 50)
    print("🚀 LV1 Observer - API 연결 테스트")
    print("=" * 50)

    # 설정 검증
    validation_result = settings.validate_required_settings()
    if not validation_result["is_valid"]:
        print(f"\n⚠️  누락된 설정: {', '.join(validation_result['missing_settings'])}")
        print("   .env 파일을 확인하고 필요한 API 키를 설정해주세요.\n")

    # API 테스트 실행
    results = {
        "OpenAI": test_openai_api(),
        "KIS": test_kis_api(),
        "Naver News": test_naver_news_api()
    }

    # 결과 요약
    print("\n" + "=" * 50)
    print("📊 테스트 결과 요약")
    print("=" * 50)

    for api_name, success in results.items():
        status = "✅ 성공" if success else "❌ 실패"
        print(f"{api_name:15}: {status}")

    success_count = sum(results.values())
    total_count = len(results)

    print(f"\n총 {total_count}개 중 {success_count}개 성공")

    if success_count == total_count:
        print("🎉 모든 API 연결이 성공했습니다!")
    else:
        print("⚠️  일부 API 연결에 실패했습니다. 위의 메시지를 확인해주세요.")

if __name__ == "__main__":
    main()