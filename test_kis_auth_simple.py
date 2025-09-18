#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
간단한 KIS API 인증 테스트 스크립트
"""

import sys
import os

# KIS API 모듈 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__), 'open-trading-api-main/examples_user'))

try:
    import kis_auth as ka
    print("✅ KIS API 기본 모듈 import 성공")
except ImportError as e:
    print(f"❌ KIS API 모듈 import 실패: {e}")
    sys.exit(1)

def test_basic_authentication():
    """기본 KIS API 인증 테스트"""
    print("\n🔐 KIS API 기본 인증 테스트 시작...")
    
    try:
        # 모의투자 환경에서 인증
        print("📍 모의투자 환경 인증 중...")
        ka.auth(svr="vps", product="01")  # vps: 모의투자, product: 종합계좌
        
        # 환경 정보 가져오기
        trenv = ka.getTREnv()
        
        print("✅ 기본 인증 성공!")
        print(f"   API 서버: {trenv.my_url}")
        print(f"   WebSocket: {trenv.my_url_ws}")
        print(f"   계좌번호: {trenv.my_acct}")
        print(f"   상품코드: {trenv.my_prod}")
        print(f"   앱키: {trenv.my_app[:10]}...")  # 보안을 위해 일부만 표시
        
        return True, trenv
        
    except Exception as e:
        print(f"❌ 인증 실패: {e}")
        return False, None

def test_basic_api_call(trenv):
    """기본 API 호출 테스트"""
    print("\n📡 기본 API 호출 테스트...")
    
    try:
        # API 설정 상태 확인
        print(f"✅ API 서버 URL: {trenv.my_url}")
        print(f"✅ 토큰 존재: {'Yes' if trenv.my_token else 'No'}")
        print(f"✅ 앱키 설정: {'Yes' if trenv.my_app else 'No'}")
        print(f"✅ HTS ID: {trenv.my_htsid}")
        
        return True
        
    except Exception as e:
        print(f"❌ API 설정 확인 실패: {e}")
        return False

def main():
    """메인 테스트 함수"""
    print("🚀 KIS API 기본 연결 테스트")
    print("=" * 40)
    
    # 1. 기본 인증 테스트
    auth_success, trenv = test_basic_authentication()
    if not auth_success:
        print("\n❌ 기본 인증 실패")
        return
    
    # 2. API 설정 확인
    api_success = test_basic_api_call(trenv)
    
    # 결과 요약
    print("\n" + "=" * 40)
    print("🎯 기본 테스트 결과")
    print(f"   인증: {'✅ 성공' if auth_success else '❌ 실패'}")
    print(f"   API 설정: {'✅ 성공' if api_success else '❌ 실패'}")
    
    if auth_success and api_success:
        print("\n🎉 기본 연결 테스트 통과!")
        print("   KIS API 기본 설정이 완료되었습니다.")
        print("   이제 고급 기능 테스트를 진행할 수 있습니다.")
    else:
        print("\n⚠️  기본 테스트 실패. 설정을 확인해주세요.")

if __name__ == "__main__":
    main()