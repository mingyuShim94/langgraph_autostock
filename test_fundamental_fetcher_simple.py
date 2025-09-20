#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
펀더멘털 페처 에이전트 간단 테스트

의존성 문제를 피해 핵심 기능만 테스트
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

def test_data_engine():
    """데이터 엔진 독립 테스트"""
    print("🔍 FundamentalDataEngine 테스트 시작")
    
    try:
        from src.utils.fundamental_data_engine import FundamentalDataEngine, collect_single_ticker_data
        
        # 단일 종목 테스트
        print("📊 단일 종목 데이터 수집 테스트")
        data = collect_single_ticker_data("005930", mock_mode=True)
        
        print(f"✅ 종목: {data.ticker}")
        print(f"✅ 회사명: {data.company_name}")
        print(f"✅ PER: {data.financial_ratios.per}")
        print(f"✅ PBR: {data.financial_ratios.pbr}")
        print(f"✅ ROE: {data.financial_ratios.roe}%")
        print(f"✅ 뉴스 개수: {len(data.news_data)}개")
        print(f"✅ 신뢰도: {data.confidence_score}")
        print(f"✅ 수집 시간: {data.collection_time:.3f}초")
        
        # 배치 테스트
        print("\n📊 배치 데이터 수집 테스트")
        from src.utils.fundamental_data_engine import collect_multiple_tickers_data
        
        tickers = ["005930", "000660", "035420"]
        batch_data = collect_multiple_tickers_data(tickers, mock_mode=True)
        
        print(f"✅ 처리된 종목 수: {len(batch_data)}")
        for ticker, data in batch_data.items():
            print(f"   - {ticker}: {data.company_name}, 신뢰도={data.confidence_score}")
        
        # 캐싱 테스트
        print("\n📊 캐싱 시스템 테스트")
        engine = FundamentalDataEngine(cache_ttl_minutes=5, mock_mode=True)
        
        # 첫 번째 요청
        start_time = time.time()
        data1 = engine.collect_fundamental_data("005930")
        first_time = time.time() - start_time
        
        # 두 번째 요청 (캐시 사용)
        start_time = time.time()
        data2 = engine.collect_fundamental_data("005930")
        second_time = time.time() - start_time
        
        speed_improvement = first_time / max(second_time, 0.001)
        print(f"✅ 첫 번째 요청: {first_time:.3f}초")
        print(f"✅ 두 번째 요청: {second_time:.3f}초")
        print(f"✅ 성능 향상: {speed_improvement:.1f}x")
        
        # 캐시 통계
        cache_stats = engine.get_cache_stats()
        print(f"✅ 캐시 항목: {cache_stats['total_cached_items']}개")
        print(f"✅ Mock 모드: {cache_stats['mock_mode']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 데이터 엔진 테스트 실패: {e}")
        return False

def test_data_structures():
    """데이터 구조 테스트"""
    print("\n🔍 데이터 구조 테스트 시작")
    
    try:
        from src.utils.fundamental_data_engine import (
            FinancialRatio, NewsData, IndustryComparison, 
            FundamentalData, DataQuality
        )
        
        # FinancialRatio 테스트
        fr = FinancialRatio(
            ticker="005930",
            company_name="삼성전자",
            per=12.5,
            pbr=1.2,
            roe=15.5,
            debt_ratio=30.2,
            data_quality=DataQuality.HIGH,
            source="TEST"
        )
        
        print(f"✅ FinancialRatio: {fr.company_name}, PER={fr.per}")
        
        # NewsData 테스트
        news = NewsData(
            ticker="005930",
            title="삼성전자 실적 발표",
            summary="좋은 실적을 기록했습니다",
            published_date="2025-09-20",
            source="테스트뉴스",
            sentiment_score=0.7,
            relevance_score=0.9
        )
        
        print(f"✅ NewsData: {news.title}, 감정점수={news.sentiment_score}")
        
        # IndustryComparison 테스트
        industry = IndustryComparison(
            ticker="005930",
            industry_name="반도체",
            industry_avg_per=15.0,
            rank_in_industry=3,
            total_companies=50,
            percentile=94.0
        )
        
        print(f"✅ IndustryComparison: {industry.industry_name}, 순위={industry.rank_in_industry}/{industry.total_companies}")
        
        return True
        
    except Exception as e:
        print(f"❌ 데이터 구조 테스트 실패: {e}")
        return False

def test_mock_data_quality():
    """Mock 데이터 품질 테스트"""
    print("\n🔍 Mock 데이터 품질 테스트 시작")
    
    try:
        from src.utils.fundamental_data_engine import FundamentalDataEngine
        
        engine = FundamentalDataEngine(mock_mode=True)
        
        # 여러 종목 테스트하여 데이터 품질 확인
        test_tickers = ["005930", "000660", "035420", "035720", "207940"]
        results = []
        
        for ticker in test_tickers:
            data = engine.collect_fundamental_data(ticker)
            
            # 재무 지표 완성도 확인
            fr = data.financial_ratios
            completed_fields = sum(1 for field in [fr.per, fr.pbr, fr.roe, fr.debt_ratio, fr.operating_margin] if field is not None)
            completeness = completed_fields / 5
            
            results.append({
                'ticker': ticker,
                'company': data.company_name,
                'completeness': completeness,
                'confidence': data.confidence_score,
                'news_count': len(data.news_data),
                'per': fr.per,
                'pbr': fr.pbr,
                'roe': fr.roe
            })
            
            print(f"✅ {ticker}: 완성도={completeness:.1%}, 신뢰도={data.confidence_score}, 뉴스={len(data.news_data)}건")
        
        # 전체 품질 통계
        avg_completeness = sum(r['completeness'] for r in results) / len(results)
        avg_confidence = sum(r['confidence'] for r in results) / len(results)
        
        print(f"\n📊 전체 품질 통계:")
        print(f"✅ 평균 완성도: {avg_completeness:.1%}")
        print(f"✅ 평균 신뢰도: {avg_confidence:.3f}")
        print(f"✅ 테스트 종목 수: {len(results)}")
        
        return avg_completeness > 0.8 and avg_confidence > 0.5
        
    except Exception as e:
        print(f"❌ Mock 데이터 품질 테스트 실패: {e}")
        return False

def save_test_results(results):
    """테스트 결과 저장"""
    test_summary = {
        "timestamp": datetime.now().isoformat(),
        "test_type": "fundamental_fetcher_simple",
        "total_tests": len(results),
        "passed_tests": sum(1 for r in results if r['passed']),
        "success_rate": (sum(1 for r in results if r['passed']) / len(results)) * 100,
        "test_results": results
    }
    
    try:
        with open("test_results_fundamental_fetcher_simple.json", 'w', encoding='utf-8') as f:
            json.dump(test_summary, f, ensure_ascii=False, indent=2)
        print(f"\n💾 테스트 결과 저장: test_results_fundamental_fetcher_simple.json")
    except Exception as e:
        print(f"❌ 결과 저장 실패: {e}")

def main():
    """메인 테스트 함수"""
    print("=" * 80)
    print("🧪 펀더멘털 페처 에이전트 (Gemini 2.5 Flash-Lite) 간단 테스트")
    print("=" * 80)
    print(f"📅 테스트 시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🔧 Mock 모드로 실행")
    print()
    
    # 테스트 실행
    tests = [
        ("데이터 엔진 테스트", test_data_engine),
        ("데이터 구조 테스트", test_data_structures),
        ("Mock 데이터 품질 테스트", test_mock_data_quality)
    ]
    
    results = []
    passed = 0
    
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"🔍 {test_name}")
        print(f"{'='*60}")
        
        try:
            start_time = time.time()
            success = test_func()
            execution_time = time.time() - start_time
            
            if success:
                print(f"\n✅ {test_name} 통과 ({execution_time:.3f}초)")
                passed += 1
            else:
                print(f"\n❌ {test_name} 실패 ({execution_time:.3f}초)")
            
            results.append({
                "name": test_name,
                "passed": success,
                "execution_time": execution_time
            })
            
        except Exception as e:
            execution_time = time.time() - start_time
            print(f"\n💥 {test_name} 예외 발생: {str(e)} ({execution_time:.3f}초)")
            results.append({
                "name": test_name,
                "passed": False,
                "execution_time": execution_time,
                "error": str(e)
            })
    
    # 최종 결과
    total = len(tests)
    success_rate = (passed / total) * 100
    
    print("\n" + "=" * 80)
    print("📊 펀더멘털 페처 에이전트 테스트 결과 요약")
    print("=" * 80)
    print(f"🎯 전체 테스트: {total}개")
    print(f"✅ 통과한 테스트: {passed}개")
    print(f"❌ 실패한 테스트: {total - passed}개")
    print(f"📈 성공률: {success_rate:.1f}%")
    
    if success_rate == 100:
        print("🎉 모든 테스트 통과! 펀더멘털 데이터 엔진이 정상 작동합니다.")
    elif success_rate >= 80:
        print("⚠️ 대부분의 테스트 통과. 일부 기능 확인 필요.")
    else:
        print("🚨 다수의 테스트 실패. 시스템 점검 필요.")
    
    # 결과 저장
    save_test_results(results)
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)