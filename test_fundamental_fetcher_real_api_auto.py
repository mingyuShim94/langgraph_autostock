#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
펀더멘털 페처 에이전트 실제 KIS API 연동 자동 테스트

자동으로 'y' 응답하여 테스트 진행
"""

import os
import sys
import time
import json
import logging
from datetime import datetime

# 프로젝트 루트 경로 추가
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

print("🚀 실제 KIS API 연동 테스트를 자동으로 시작합니다...")

# KIS API 모듈 경로 추가
kis_path = os.path.join(project_root, 'open-trading-api-main/examples_user')
kis_domestic_path = os.path.join(project_root, 'open-trading-api-main/examples_user/domestic_stock')
kis_llm_path = os.path.join(project_root, 'open-trading-api-main/examples_llm/domestic_stock/finance_financial_ratio')

sys.path.extend([kis_path, kis_domestic_path, kis_llm_path])

# 필수 라이브러리 체크
try:
    import requests
    print("✅ requests 모듈 사용 가능")
except ImportError:
    print("❌ requests 모듈 없음")

try:
    import pandas
    print(f"✅ pandas 모듈 사용 가능: {pandas.__version__}")
except ImportError:
    print("❌ pandas 모듈 없음")

# KIS API 모듈 체크
try:
    import kis_auth as ka
    from finance_financial_ratio import finance_financial_ratio
    KIS_AVAILABLE = True
    print("✅ KIS API 모듈 import 성공")
except ImportError as e:
    print(f"❌ KIS API 모듈 import 실패: {e}")
    KIS_AVAILABLE = False

def simple_kis_test():
    """간단한 KIS API 테스트"""
    print("\n" + "=" * 60)
    print("📊 간단한 KIS API 연동 테스트")
    print("=" * 60)
    
    if not KIS_AVAILABLE:
        print("❌ KIS API 모듈을 사용할 수 없습니다.")
        print("📁 필요한 파일들:")
        print("   - open-trading-api-main/ 폴더")
        print("   - ~/KIS/config/kis_devlp.yaml 설정 파일")
        return False
    
    try:
        # 1. 인증 테스트
        print("🔐 Step 1: KIS API 인증 테스트")
        ka.auth(svr="vps", product="01")  # Paper trading
        trenv = ka.getTREnv()
        print(f"   ✅ 인증 성공 - 계좌: {trenv.my_acct}")
        
        # 2. 재무비율 API 테스트
        print("📊 Step 2: 삼성전자 재무비율 조회")
        financial_data = finance_financial_ratio(
            fid_div_cls_code="0",
            fid_cond_mrkt_div_code="J", 
            fid_input_iscd="005930"
        )
        
        if financial_data is not None and not financial_data.empty:
            print(f"   ✅ 데이터 수신 성공 - {len(financial_data)}행 {len(financial_data.columns)}컬럼")
            
            # 첫 번째 행 데이터 출력
            if len(financial_data) > 0:
                first_row = financial_data.iloc[0]
                print("   📈 샘플 재무 데이터:")
                for i, (col, val) in enumerate(first_row.items()):
                    if i < 3:  # 처음 3개만
                        print(f"      {col}: {val}")
            
            return True
        else:
            print("   ❌ 빈 데이터 또는 None 수신")
            return False
            
    except Exception as e:
        print(f"   ❌ 테스트 실패: {e}")
        
        # 오류 진단
        print("\n🔧 문제 해결 가이드:")
        if "No such file" in str(e) or "FileNotFoundError" in str(e):
            print("   📁 설정 파일 문제:")
            print("      - ~/KIS/config/kis_devlp.yaml 파일이 있는지 확인")
            print("      - 파일 경로 및 권한 확인")
        elif "403" in str(e) or "401" in str(e):
            print("   🔑 인증 문제:")
            print("      - KIS Open API 서비스 신청 확인")
            print("      - Paper trading 앱키/시크릿 정확성 확인")
        elif "timeout" in str(e).lower():
            print("   🌐 네트워크 문제:")
            print("      - 인터넷 연결 상태 확인")
            print("      - 방화벽 설정 확인")
        
        return False

def test_fundamental_engine():
    """펀더멘털 데이터 엔진 테스트"""
    print("\n📊 펀더멘털 데이터 엔진 테스트")
    
    try:
        from src.utils.fundamental_data_engine import FundamentalDataEngine
        
        # Mock 모드로 먼저 테스트
        print("🎭 Mock 모드 테스트...")
        mock_engine = FundamentalDataEngine(mock_mode=True)
        mock_data = mock_engine.collect_fundamental_data("005930")
        print(f"   ✅ Mock 데이터: {mock_data.company_name}, 신뢰도={mock_data.confidence_score}")
        
        if KIS_AVAILABLE:
            # 실제 API 모드 테스트
            print("📡 실제 API 모드 테스트...")
            real_engine = FundamentalDataEngine(mock_mode=False)
            real_data = real_engine.collect_fundamental_data("005930")
            print(f"   ✅ 실제 데이터: {real_data.company_name}, 소스={real_data.financial_ratios.source}")
            
            if real_data.financial_ratios.source == "KIS_API":
                print("   🎉 실제 KIS API 데이터 수집 성공!")
                return True
            else:
                print("   ⚠️ Mock 데이터로 폴백됨")
                return False
        else:
            print("   ⚠️ KIS API 모듈 없어 Mock 모드만 테스트")
            return True
            
    except Exception as e:
        print(f"   ❌ 펀더멘털 엔진 테스트 실패: {e}")
        return False

def main():
    """메인 테스트 함수"""
    print("🧪 펀더멘털 페처 KIS API 연동 자동 테스트")
    print(f"📅 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "tests": []
    }
    
    # 테스트 실행
    tests = [
        ("KIS API 기본 연동", simple_kis_test),
        ("펀더멘털 데이터 엔진", test_fundamental_engine)
    ]
    
    passed = 0
    for test_name, test_func in tests:
        print(f"\n🔍 {test_name} 테스트 중...")
        try:
            success = test_func()
            if success:
                print(f"✅ {test_name} 성공")
                passed += 1
            else:
                print(f"❌ {test_name} 실패")
            
            results["tests"].append({
                "name": test_name,
                "success": success
            })
        except Exception as e:
            print(f"💥 {test_name} 예외: {e}")
            results["tests"].append({
                "name": test_name,
                "success": False,
                "error": str(e)
            })
    
    # 결과 요약
    total = len(tests)
    success_rate = (passed / total) * 100 if total > 0 else 0
    
    print("\n" + "=" * 60)
    print("📊 테스트 결과 요약")
    print("=" * 60)
    print(f"🎯 전체 테스트: {total}개")
    print(f"✅ 성공: {passed}개")
    print(f"❌ 실패: {total - passed}개")
    print(f"📈 성공률: {success_rate:.1f}%")
    
    if success_rate == 100:
        print("🎉 모든 테스트 성공!")
    elif success_rate >= 50:
        print("⚠️ 일부 테스트 성공")
    else:
        print("🚨 대부분 테스트 실패")
    
    # 결과 저장
    results["success_rate"] = success_rate
    results["summary"] = {
        "total": total,
        "passed": passed,
        "failed": total - passed
    }
    
    try:
        with open("test_results_kis_auto.json", "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print("\n💾 결과 저장: test_results_kis_auto.json")
    except Exception as e:
        print(f"\n❌ 결과 저장 실패: {e}")
    
    return success_rate == 100

if __name__ == "__main__":
    main()