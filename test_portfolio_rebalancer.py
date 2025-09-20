#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
포트폴리오 리밸런싱 에이전트 테스트 스크립트

Phase 2.1 노드 1 구현 검증용 테스트
리밸런싱 에이전트의 모든 기능을 종합적으로 테스트합니다.
"""

import sys
import logging
from datetime import datetime
from typing import Dict, Any

# 프로젝트 루트 경로 추가
sys.path.append('.')

from src.agents.portfolio_rebalancer import PortfolioRebalancerAgent
from src.agents.base_agent import AgentContext

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_basic_agent_functionality():
    """기본 에이전트 기능 테스트"""
    print("🔧 기본 에이전트 기능 테스트")
    print("-" * 50)
    
    try:
        # 에이전트 인스턴스 생성
        agent = PortfolioRebalancerAgent()
        
        # 에이전트 정보 확인
        agent_info = agent.get_agent_info()
        print(f"✅ 에이전트 정보:")
        print(f"   - 타입: {agent_info['agent_type']}")
        print(f"   - 클래스: {agent_info['agent_class']}")
        print(f"   - LLM 제공사: {agent_info['llm_provider']}")
        print(f"   - LLM 모델: {agent_info['llm_model']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 기본 기능 테스트 실패: {str(e)}")
        return False


def test_portfolio_analysis_mock_mode():
    """모의 모드 포트폴리오 분석 테스트"""
    print("\n📊 모의 모드 포트폴리오 분석 테스트")
    print("-" * 50)
    
    try:
        # 에이전트 인스턴스 생성
        agent = PortfolioRebalancerAgent()
        
        # 테스트 컨텍스트 생성
        context = AgentContext(
            agent_id="portfolio_rebalancer",
            execution_id=f"test_{int(datetime.now().timestamp())}",
            timestamp=datetime.now(),
            input_data={
                "environment": "paper",
                "mock_mode": True
            }
        )
        
        # 에이전트 실행
        result = agent.execute(context)
        
        if result.success:
            print("✅ 포트폴리오 분석 성공")
            print(f"   - 실행 시간: {result.execution_time:.2f}초")
            print(f"   - 신뢰도: {result.confidence_score:.2f}")
            
            # 결과 상세 분석
            analysis_result = result.result_data
            
            # 포트폴리오 진단 결과
            diagnosis = analysis_result.get("diagnosis", {})
            print(f"\n📋 포트폴리오 진단:")
            print(f"   - 총 자산: {diagnosis.get('total_value'):,}원")
            print(f"   - 현금: {diagnosis.get('cash_value'):,}원")
            print(f"   - 주식: {diagnosis.get('stock_value'):,}원")
            print(f"   - 보유 종목 수: {len(diagnosis.get('holdings', []))}")
            
            # 리밸런싱 평가 결과
            rebalancing = analysis_result.get("rebalancing_assessment", {})
            print(f"\n⚖️ 리밸런싱 평가:")
            print(f"   - 점수: {rebalancing.get('score', 0):.2f}")
            print(f"   - 우선순위: {rebalancing.get('priority', 'N/A')}")
            print(f"   - 주요 이슈: {len(rebalancing.get('reasons', []))}개")
            
            # LLM 권고사항
            llm_rec = analysis_result.get("llm_recommendation", {})
            if "llm_response" in llm_rec:
                llm_data = llm_rec["llm_response"]
                print(f"\n🤖 LLM 권고사항:")
                print(f"   - 전반적 평가: {llm_data.get('overall_assessment', 'N/A')[:100]}...")
                print(f"   - 액션 플랜: {len(llm_data.get('action_plan', []))}개")
                print(f"   - 사용 모델: {llm_rec.get('model_used', 'N/A')}")
            
            return True
            
        else:
            print(f"❌ 포트폴리오 분석 실패: {result.error_message}")
            return False
            
    except Exception as e:
        print(f"❌ 모의 모드 테스트 실패: {str(e)}")
        return False


def test_sector_classification():
    """섹터 분류 기능 테스트"""
    print("\n🏭 섹터 분류 기능 테스트")
    print("-" * 50)
    
    try:
        from src.utils.sector_classifier import get_sector_classifier
        
        classifier = get_sector_classifier()
        
        # 테스트 종목들
        test_tickers = ["005930", "000660", "035420", "055550", "005380"]
        
        print("종목별 섹터 분류 결과:")
        for ticker in test_tickers:
            sector = classifier.classify_ticker(ticker)
            sector_info = classifier.get_sector_info(sector)
            print(f"   - {ticker}: {sector_info.sector_name_kr} ({sector_info.volatility_level})")
        
        # 섹터 분포 테스트
        distribution = classifier.get_sector_distribution(test_tickers)
        print(f"\n섹터 분포:")
        for sector, count in distribution.items():
            print(f"   - {sector.value}: {count}개")
        
        return True
        
    except Exception as e:
        print(f"❌ 섹터 분류 테스트 실패: {str(e)}")
        return False


def test_portfolio_analyzer():
    """포트폴리오 분석기 테스트"""
    print("\n📈 포트폴리오 분석기 테스트")
    print("-" * 50)
    
    try:
        from src.utils.portfolio_analyzer import get_portfolio_analyzer
        
        analyzer = get_portfolio_analyzer()
        
        # 테스트 데이터
        test_holdings = [
            {
                "ticker": "005930",
                "name": "삼성전자",
                "quantity": 10,
                "avg_price": 75000,
                "current_price": 77000,
                "total_value": 770000,
                "pnl": 20000
            },
            {
                "ticker": "000660",
                "name": "SK하이닉스", 
                "quantity": 3,
                "avg_price": 80000,
                "current_price": 76666,
                "total_value": 230000,
                "pnl": -10000
            }
        ]
        
        cash_balance = 1000000
        total_value = 2000000
        
        # 포트폴리오 분석 실행
        metrics = analyzer.analyze_portfolio(test_holdings, cash_balance, total_value)
        
        print(f"포트폴리오 분석 결과:")
        print(f"   - 분산투자 점수: {metrics.diversification_score:.2f}")
        print(f"   - 집중도 위험: {metrics.concentration_risk:.2f}")
        print(f"   - 리밸런싱 점수: {metrics.rebalancing_score:.2f}")
        print(f"   - 우선순위: {metrics.rebalancing_priority}")
        print(f"   - 섹터 수: {metrics.sector_count}")
        print(f"   - 허핀달 지수: {metrics.herfindahl_index:.4f}")
        
        # 리밸런싱 권고사항 생성
        recommendation = analyzer.generate_rebalancing_recommendation(metrics)
        print(f"\n권고사항:")
        print(f"   - 우선순위: {recommendation.priority}")
        print(f"   - 점수: {recommendation.score:.2f}")
        print(f"   - 이유: {len(recommendation.reasons)}개")
        print(f"   - 액션: {len(recommendation.actions)}개")
        
        return True
        
    except Exception as e:
        print(f"❌ 포트폴리오 분석기 테스트 실패: {str(e)}")
        return False


def test_kis_client_integration():
    """KIS 클라이언트 통합 테스트"""
    print("\n🔌 KIS 클라이언트 통합 테스트")
    print("-" * 50)
    
    try:
        from src.kis_client.client import get_kis_client
        
        # 모의 모드로 클라이언트 생성
        client = get_kis_client(environment="paper", mock_mode=True)
        
        # 상세 포트폴리오 조회 테스트
        detailed_portfolio = client.get_detailed_portfolio()
        
        total_value = detailed_portfolio.get('total_value') or 0
        holdings = detailed_portfolio.get('holdings', [])
        
        print(f"✅ 상세 포트폴리오 조회 성공:")
        print(f"   - 총 자산: {total_value:,}원")
        print(f"   - 보유 종목: {len(holdings)}개")
        
        # 섹터 배분 조회 테스트
        holdings = detailed_portfolio.get('holdings', [])
        if holdings:
            sector_allocation = client.get_sector_allocation(holdings)
            print(f"   - 섹터 수: {len(sector_allocation)}")
            
            for sector_name, allocation in sector_allocation.items():
                print(f"     * {sector_name}: {allocation['weight']:.1%}")
        
        # 포트폴리오 메트릭 계산 테스트
        metrics = client.calculate_portfolio_metrics(detailed_portfolio)
        print(f"   - 리밸런싱 점수: {metrics.get('rebalancing_score', 0):.2f}")
        print(f"   - 분산투자 점수: {metrics.get('diversification_score', 0):.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ KIS 클라이언트 통합 테스트 실패: {str(e)}")
        return False


def test_error_handling():
    """에러 처리 테스트"""
    print("\n🚨 에러 처리 테스트")
    print("-" * 50)
    
    try:
        agent = PortfolioRebalancerAgent()
        
        # 잘못된 입력 데이터로 테스트
        invalid_context = AgentContext(
            agent_id="portfolio_rebalancer",
            execution_id="test_error",
            timestamp=datetime.now(),
            input_data={
                "environment": "invalid_env",  # 잘못된 환경
                "mock_mode": "not_boolean"     # 잘못된 타입
            }
        )
        
        result = agent.execute(invalid_context)
        
        if not result.success:
            print(f"✅ 에러 처리 성공: {result.error_message}")
            return True
        else:
            print("❌ 에러가 발생해야 하는데 성공함")
            return False
            
    except Exception as e:
        print(f"✅ 예외 처리 성공: {str(e)}")
        return True


def run_comprehensive_test():
    """종합 테스트 실행"""
    print("🚀 포트폴리오 리밸런싱 에이전트 종합 테스트")
    print("=" * 80)
    
    test_results = {}
    
    # 개별 테스트 실행
    tests = [
        ("기본 기능", test_basic_agent_functionality),
        ("포트폴리오 분석 (모의모드)", test_portfolio_analysis_mock_mode),
        ("섹터 분류", test_sector_classification),
        ("포트폴리오 분석기", test_portfolio_analyzer),
        ("KIS 클라이언트 통합", test_kis_client_integration),
        ("에러 처리", test_error_handling)
    ]
    
    for test_name, test_func in tests:
        try:
            test_results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} 테스트 중 예외 발생: {str(e)}")
            test_results[test_name] = False
    
    # 결과 요약
    print("\n" + "=" * 80)
    print("📊 테스트 결과 요약")
    print("=" * 80)
    
    total_tests = len(test_results)
    passed_tests = sum(test_results.values())
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n총 테스트: {total_tests}")
    print(f"통과: {passed_tests}")
    print(f"실패: {total_tests - passed_tests}")
    print(f"성공률: {passed_tests/total_tests*100:.1f}%")
    
    if passed_tests == total_tests:
        print("\n🎉 모든 테스트 통과! Phase 2.1 노드 1 구현 완료")
        return True
    else:
        print(f"\n⚠️ {total_tests - passed_tests}개 테스트 실패. 수정 필요")
        return False


if __name__ == "__main__":
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)