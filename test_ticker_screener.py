#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
티커 스크리너 테스트

ticker_screener.py의 기능을 테스트하는 스크립트입니다.
"""

import logging
import sys
import os
from typing import List

# 프로젝트 루트 경로 추가
project_root = os.path.dirname(__file__)
sys.path.append(project_root)

from src.agents.ticker_screener import TickerScreener, create_ticker_screener
from src.kis_client.client import get_kis_client

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_ticker_screener_mock():
    """모의 모드로 티커 스크리너 테스트"""
    print("=" * 60)
    print("🧪 티커 스크리너 모의 모드 테스트")
    print("=" * 60)
    
    # 모의 모드로 KIS 클라이언트 생성
    kis_client = get_kis_client(environment="paper", mock_mode=True)
    
    # 티커 스크리너 생성
    screener_config = {
        'test_price': '1000',
        'api_delay': 0.05,  # 테스트용 짧은 지연
        'max_retries': 1
    }
    screener = create_ticker_screener(kis_client, **screener_config)
    
    # 테스트할 종목 리스트 (실제 종목 코드)
    test_tickers = [
        "005930",  # 삼성전자
        "000660",  # SK하이닉스
        "035420",  # NAVER
        "005380",  # 현대차
        "051910",  # LG화학
        "006400",  # 삼성SDI
        "035720",  # 카카오
        "207940",  # 삼성바이오로직스
        "068270",  # 셀트리온
        "323410"   # 카카오뱅크
    ]
    
    print(f"📋 테스트 종목 수: {len(test_tickers)}개")
    print(f"🔧 설정: test_price={screener_config['test_price']}, api_delay={screener_config['api_delay']}")
    print()
    
    # 스크리닝 실행
    result = screener.check_tradable_tickers(test_tickers)
    
    # 결과 출력
    print("🎯 스크리닝 결과:")
    print(f"   ✅ 거래가능: {len(result.tradable_tickers)}개")
    print(f"   ❌ 거래불가: {len(result.non_tradable_tickers)}개") 
    print(f"   ⚠️ 에러: {len(result.error_tickers)}개")
    print(f"   ⏱️ 실행시간: {result.execution_time:.2f}초")
    print()
    
    # 상세 결과
    if result.tradable_tickers:
        print("✅ 거래가능 종목:")
        for ticker in result.tradable_tickers:
            print(f"   - {ticker}")
    
    if result.non_tradable_tickers:
        print("\n❌ 거래불가 종목:")
        for ticker in result.non_tradable_tickers:
            print(f"   - {ticker}")
    
    if result.error_tickers:
        print("\n⚠️ 에러 종목:")
        for error in result.errors:
            print(f"   - {error['ticker']}: {error['error']}")
    
    # 통계 정보
    print("\n📊 상세 통계:")
    stats = screener.get_summary_stats(result)
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"   {key}: {value:.3f}")
        else:
            print(f"   {key}: {value}")
    
    return result

def test_single_ticker():
    """단일 종목 테스트"""
    print("\n" + "=" * 60)
    print("🔍 단일 종목 테스트")
    print("=" * 60)
    
    # 모의 모드로 KIS 클라이언트 생성
    kis_client = get_kis_client(environment="paper", mock_mode=True)
    screener = create_ticker_screener(kis_client)
    
    # 삼성전자 단일 테스트
    single_ticker = ["005930"]
    result = screener.check_tradable_tickers(single_ticker)
    
    print(f"🎯 단일 종목 ({single_ticker[0]}) 테스트 결과:")
    print(f"   거래가능: {len(result.tradable_tickers) > 0}")
    print(f"   실행시간: {result.execution_time:.3f}초")
    
    return result

def test_invalid_tickers():
    """잘못된 종목코드 테스트"""
    print("\n" + "=" * 60)
    print("❌ 잘못된 종목코드 테스트")
    print("=" * 60)
    
    # 모의 모드로 KIS 클라이언트 생성
    kis_client = get_kis_client(environment="paper", mock_mode=True)
    screener = create_ticker_screener(kis_client)
    
    # 잘못된 종목코드들
    invalid_tickers = [
        "12345",    # 5자리
        "1234567",  # 7자리
        "abcdef",   # 문자
        "123abc",   # 혼합
        "",         # 빈 문자열
        "999999"    # 존재하지 않는 코드
    ]
    
    result = screener.check_tradable_tickers(invalid_tickers)
    
    print(f"🎯 잘못된 종목코드 테스트 결과:")
    print(f"   에러 종목: {len(result.error_tickers)}개")
    print(f"   에러 내용:")
    for error in result.errors:
        print(f"     - {error['ticker']}: {error['error']}")
    
    return result

def test_real_api_mode():
    """실제 API 모드 테스트 (선택적)"""
    print("\n" + "=" * 60)
    print("🌐 실제 API 모드 테스트 (KIS API 설정 필요)")
    print("=" * 60)
    
    try:
        # 실제 모드로 KIS 클라이언트 생성 시도
        kis_client = get_kis_client(environment="paper", mock_mode=False)
        screener = create_ticker_screener(kis_client, test_price="1000", api_delay=0.5)
        
        # 소수 종목으로 테스트
        test_tickers = ["005930", "000660"]  # 삼성전자, SK하이닉스
        
        print(f"📋 실제 API로 {len(test_tickers)}개 종목 테스트 중...")
        result = screener.check_tradable_tickers(test_tickers)
        
        print("🎯 실제 API 테스트 결과:")
        print(f"   ✅ 거래가능: {len(result.tradable_tickers)}개")
        print(f"   ❌ 거래불가: {len(result.non_tradable_tickers)}개")
        print(f"   ⚠️ 에러: {len(result.error_tickers)}개")
        print(f"   ⏱️ 실행시간: {result.execution_time:.2f}초")
        
        if result.tradable_tickers:
            print("   거래가능 종목:", result.tradable_tickers)
        
        if result.errors:
            print("   에러 내용:")
            for error in result.errors:
                print(f"     - {error['ticker']}: {error['error']}")
        
        return result
        
    except Exception as e:
        print(f"⚠️ 실제 API 테스트 건너뜀: {e}")
        print("   (KIS API 설정이 필요하거나 인증 실패)")
        return None

def main():
    """메인 테스트 함수"""
    print("🚀 티커 스크리너 종합 테스트 시작")
    print()
    
    results = {}
    
    # 1. 모의 모드 기본 테스트
    results['mock_test'] = test_ticker_screener_mock()
    
    # 2. 단일 종목 테스트
    results['single_test'] = test_single_ticker()
    
    # 3. 잘못된 종목코드 테스트
    results['invalid_test'] = test_invalid_tickers()
    
    # 4. 실제 API 테스트 (선택적)
    results['real_api_test'] = test_real_api_mode()
    
    # 전체 결과 요약
    print("\n" + "=" * 60)
    print("📋 전체 테스트 결과 요약")
    print("=" * 60)
    
    for test_name, result in results.items():
        if result:
            print(f"{test_name}:")
            print(f"  총 종목: {result.total_checked}개")
            print(f"  거래가능: {len(result.tradable_tickers)}개")
            print(f"  실행시간: {result.execution_time:.2f}초")
        else:
            print(f"{test_name}: 건너뜀")
    
    print("\n✅ 모든 테스트 완료!")

if __name__ == "__main__":
    main()