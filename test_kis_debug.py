#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KIS API 디버깅 및 구조 확인
"""

import sys
import os

# KIS API 모듈 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__), 'open-trading-api-main/examples_user'))

import kis_auth as ka

def debug_kis_structure():
    """KIS API 구조 디버깅"""
    print("🔍 KIS API 구조 분석...")
    
    try:
        # 모의투자 환경에서 인증
        print("📍 모의투자 환경 인증 시도...")
        result = ka.auth(svr="vps", product="01")
        print(f"✅ auth() 결과: {result}")
        
        # 환경 정보 가져오기
        print("📍 환경 정보 가져오기...")
        trenv = ka.getTREnv()
        print(f"✅ getTREnv() 결과 타입: {type(trenv)}")
        
        # 객체 속성 확인
        print("\n📋 trenv 객체 속성들:")
        for attr in dir(trenv):
            if not attr.startswith('_'):
                try:
                    value = getattr(trenv, attr)
                    if callable(value):
                        print(f"   {attr}: <function>")
                    else:
                        # 민감한 정보는 일부만 표시
                        if attr in ['my_app', 'my_sec', 'my_token'] and value:
                            print(f"   {attr}: {str(value)[:10]}...")
                        else:
                            print(f"   {attr}: {value}")
                except Exception as e:
                    print(f"   {attr}: <Error: {e}>")
        
        return True, trenv
        
    except Exception as e:
        print(f"❌ 디버깅 실패: {e}")
        import traceback
        traceback.print_exc()
        return False, None

if __name__ == "__main__":
    debug_kis_structure()