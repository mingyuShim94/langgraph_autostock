#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KIS 환경 설정 및 실제 API 테스트

환경변수와 기존 KIS 클라이언트를 사용하여 실제 API 연동 테스트
"""

import os
import sys
import time
import logging
from datetime import datetime

# 프로젝트 루트 경로 추가
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# .env 파일 로드
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ .env 파일 로드 완료")
except ImportError:
    print("⚠️ python-dotenv 모듈 없음, 환경변수는 직접 설정해야 합니다")

print("🔍 KIS 환경 설정 및 API 연동 테스트")
print("=" * 60)


def check_environment_variables():
    """환경변수 확인"""
    print("📋 환경변수 확인 중...")
    
    kis_env_vars = [
        'KIS_PAPER_APP_KEY',
        'KIS_PAPER_APP_SECRET', 
        'KIS_PAPER_ACCOUNT_NUMBER',
        'KIS_APP_KEY',
        'KIS_APP_SECRET',
        'KIS_ACCOUNT_NUMBER'
    ]
    
    found_vars = {}
    for var in kis_env_vars:
        value = os.getenv(var)
        if value:
            found_vars[var] = value[:10] + "..." if len(value) > 10 else value
            print(f"   ✅ {var}: {found_vars[var]}")
        else:
            print(f"   ❌ {var}: 설정되지 않음")
    
    return found_vars


def check_kis_client():
    """기존 KIS 클라이언트 확인"""
    print("\n🏗️ 기존 KIS 클라이언트 확인...")
    
    try:
        from src.kis_client.client import KISAuthManager, KISClientError
        print("   ✅ KIS 클라이언트 모듈 import 성공")
        
        # KIS Auth Manager 테스트
        auth_manager = KISAuthManager(environment="paper")
        print(f"   ✅ KISAuthManager 생성 성공 (환경: paper)")
        
        return True
        
    except Exception as e:
        print(f"   ❌ KIS 클라이언트 import 실패: {e}")
        return False


def test_fundamental_data_engine_with_kis():
    """펀더멘털 데이터 엔진을 KIS 환경에서 테스트"""
    print("\n📊 펀더멘털 데이터 엔진 KIS 연동 테스트...")
    
    try:
        from src.utils.fundamental_data_engine import FundamentalDataEngine
        
        # 환경변수가 있으면 실제 API 모드, 없으면 Mock 모드
        has_kis_env = bool(os.getenv('KIS_PAPER_APP_KEY'))
        mock_mode = not has_kis_env
        
        print(f"   🔧 테스트 모드: {'Mock' if mock_mode else 'Real API'}")
        
        # 데이터 엔진 생성
        engine = FundamentalDataEngine(
            mock_mode=mock_mode,
            cache_ttl_minutes=1
        )
        
        # 삼성전자 테스트
        print("   📈 삼성전자(005930) 데이터 수집 중...")
        data = engine.collect_fundamental_data("005930")
        
        print(f"   ✅ 수집 성공:")
        print(f"      - 회사명: {data.company_name}")
        print(f"      - 데이터 소스: {data.financial_ratios.source}")
        print(f"      - 데이터 품질: {data.financial_ratios.data_quality.value}")
        print(f"      - PER: {data.financial_ratios.per}")
        print(f"      - PBR: {data.financial_ratios.pbr}")
        print(f"      - ROE: {data.financial_ratios.roe}%")
        print(f"      - 신뢰도: {data.confidence_score}")
        print(f"      - 수집 시간: {data.collection_time:.3f}초")
        
        # 실제 API 데이터인지 확인
        if data.financial_ratios.source == "KIS_API":
            print("   🎉 실제 KIS API 데이터 수집 성공!")
            return "REAL_API"
        elif data.financial_ratios.source == "MOCK_DATA":
            print("   🎭 Mock 데이터 사용 (정상 작동)")
            return "MOCK"
        else:
            print(f"   ⚠️ 알 수 없는 데이터 소스: {data.financial_ratios.source}")
            return "UNKNOWN"
            
    except Exception as e:
        print(f"   ❌ 펀더멘털 데이터 엔진 테스트 실패: {e}")
        return "ERROR"


def test_multiple_tickers():
    """여러 종목 동시 테스트"""
    print("\n📊 다중 종목 테스트...")
    
    try:
        from src.utils.fundamental_data_engine import FundamentalDataEngine
        
        # 환경변수 확인하여 모드 결정
        has_kis_env = bool(os.getenv('KIS_PAPER_APP_KEY'))
        mock_mode = not has_kis_env
        
        engine = FundamentalDataEngine(mock_mode=mock_mode)
        
        # 대표 종목들
        tickers = ["005930", "000660", "035420"]  # 삼성전자, SK하이닉스, 네이버
        names = ["삼성전자", "SK하이닉스", "네이버"]
        
        results = []
        for i, ticker in enumerate(tickers):
            print(f"   📈 {names[i]}({ticker}) 수집 중...")
            try:
                data = engine.collect_fundamental_data(ticker)
                results.append({
                    'ticker': ticker,
                    'name': names[i],
                    'success': True,
                    'source': data.financial_ratios.source,
                    'confidence': data.confidence_score
                })
                print(f"      ✅ 성공 (소스: {data.financial_ratios.source})")
                
                # API 부하 방지
                time.sleep(0.5)
                
            except Exception as e:
                print(f"      ❌ 실패: {e}")
                results.append({
                    'ticker': ticker,
                    'name': names[i], 
                    'success': False,
                    'error': str(e)
                })
        
        # 결과 요약
        success_count = sum(1 for r in results if r['success'])
        real_api_count = sum(1 for r in results if r.get('source') == 'KIS_API')
        
        print(f"\n   📊 다중 종목 테스트 결과:")
        print(f"      성공한 종목: {success_count}/{len(tickers)}")
        print(f"      실제 API 데이터: {real_api_count}/{len(tickers)}")
        
        return success_count >= 2  # 최소 2개 성공
        
    except Exception as e:
        print(f"   ❌ 다중 종목 테스트 실패: {e}")
        return False


def main():
    """메인 테스트 함수"""
    start_time = time.time()
    
    print(f"📅 테스트 시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 1. 환경변수 확인
    env_vars = check_environment_variables()
    has_env = bool(env_vars)
    
    # 2. KIS 클라이언트 확인
    client_ok = check_kis_client()
    
    # 3. 펀더멘털 데이터 엔진 테스트
    engine_result = test_fundamental_data_engine_with_kis()
    
    # 4. 다중 종목 테스트
    multi_result = test_multiple_tickers()
    
    # 결과 요약
    total_time = time.time() - start_time
    
    print("\n" + "=" * 60)
    print("📊 KIS 환경 테스트 결과 요약")
    print("=" * 60)
    print(f"⏱️ 총 실행 시간: {total_time:.2f}초")
    print(f"🔑 환경변수 설정: {'✅ 있음' if has_env else '❌ 없음'}")
    print(f"🏗️ KIS 클라이언트: {'✅ 정상' if client_ok else '❌ 오류'}")
    print(f"📊 데이터 엔진: {engine_result}")
    print(f"🔄 다중 종목: {'✅ 성공' if multi_result else '❌ 실패'}")
    
    if engine_result == "REAL_API":
        print("\n🎉 실제 KIS API 연동 성공!")
        print("   - 환경변수가 올바르게 설정되어 있습니다")
        print("   - 실제 재무 데이터를 성공적으로 수집했습니다")
        print("   - 펀더멘털 페처 에이전트가 실제 환경에서 작동합니다")
    elif engine_result == "MOCK":
        print("\n🎭 Mock 모드로 정상 작동")
        print("   - KIS API 환경변수가 설정되지 않았습니다")
        print("   - Mock 데이터로 시스템이 완벽하게 작동합니다")
        print("   - 실제 사용을 위해서는 KIS API 키 설정이 필요합니다")
    else:
        print("\n⚠️ 테스트 완료하지만 일부 이슈 있음")
    
    print("\n💡 환경변수 설정 방법:")
    print("   export KIS_PAPER_APP_KEY='your_paper_app_key'")
    print("   export KIS_PAPER_APP_SECRET='your_paper_secret'")
    print("   export KIS_PAPER_ACCOUNT_NUMBER='your_paper_account'")
    
    return engine_result in ["REAL_API", "MOCK"]


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)