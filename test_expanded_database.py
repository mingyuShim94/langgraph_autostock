#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
확장된 데이터베이스 스키마 테스트 스크립트
Phase 3 에이전트 성과 추적 시스템 검증
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import json

# 프로젝트 루트 경로 추가
sys.path.append(str(Path(__file__).parent))

from src.database.schema import (
    db_manager, TradeRecord, AgentPerformance, LLMUsageLog, 
    ModelEvolutionHistory, SystemMetrics
)


def test_enhanced_trade_record():
    """확장된 TradeRecord 테스트"""
    print("🧪 1. 확장된 TradeRecord 테스트")
    
    # 에이전트 기여도가 포함된 거래 기록 생성
    agent_contributions = {
        "cio": 0.4,  # CIO 에이전트가 40% 기여
        "technical_analyst": 0.3,  # 기술적 분석가가 30%
        "valuation_analyst": 0.2,  # 밸류에이션 분석가가 20%
        "risk_analyst": 0.1  # 리스크 분석가가 10%
    }
    
    analysis_metadata = {
        "decision_time_seconds": 45.2,
        "models_used": ["claude-opus-4.1", "gpt-5", "gemini-flash-2.5"],
        "total_cost_usd": 0.15,
        "confidence_factors": {
            "technical_signals": 0.8,
            "fundamental_strength": 0.7,
            "market_sentiment": 0.6,
            "risk_assessment": 0.9
        }
    }
    
    trade_record = TradeRecord(
        trade_id=f"TEST_TRADE_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        timestamp=datetime.now().isoformat(),
        ticker="005930",  # 삼성전자
        action="buy",
        quantity=10,
        price=75000,
        justification_text="AI 분석 결과 기술적 신호와 펀더멘털이 모두 양호하여 매수 결정",
        market_snapshot={"kospi": 2650, "volume": 15000000, "foreign_net": 500000},
        portfolio_before={"cash": 1000000, "stocks": {"005930": 0}},
        agent_contributions=agent_contributions,
        decision_confidence=0.85,
        analysis_metadata=analysis_metadata
    )
    
    # 데이터베이스에 삽입
    success = db_manager.insert_trade(trade_record)
    print(f"  ✅ 확장된 거래 기록 삽입: {success}")
    
    return success


def test_agent_performance_tracking():
    """에이전트 성과 추적 테스트"""
    print("\n🧪 2. 에이전트 성과 추적 테스트")
    
    # 여러 에이전트의 성과 기록 생성
    agents_performance = [
        AgentPerformance(
            agent_name="cio",
            period_start=(datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d"),
            period_end=datetime.now().strftime("%Y-%m-%d"),
            total_decisions=25,
            successful_decisions=18,
            avg_contribution_score=0.42,
            performance_rating=85.5,
            wins=15,
            losses=10,
            total_pnl_attributed=125000,
            confidence_accuracy=0.78
        ),
        AgentPerformance(
            agent_name="technical_analyst",
            period_start=(datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d"), 
            period_end=datetime.now().strftime("%Y-%m-%d"),
            total_decisions=25,
            successful_decisions=20,
            avg_contribution_score=0.28,
            performance_rating=92.3,
            wins=18,
            losses=7,
            total_pnl_attributed=85000,
            confidence_accuracy=0.85
        ),
        AgentPerformance(
            agent_name="risk_analyst",
            period_start=(datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d"),
            period_end=datetime.now().strftime("%Y-%m-%d"), 
            total_decisions=25,
            successful_decisions=22,
            avg_contribution_score=0.15,
            performance_rating=96.1,
            wins=20,
            losses=5,
            total_pnl_attributed=35000,
            confidence_accuracy=0.91
        )
    ]
    
    # 성과 기록 삽입
    for performance in agents_performance:
        success = db_manager.insert_agent_performance(performance)
        print(f"  ✅ {performance.agent_name} 성과 기록 삽입: {success}")
    
    # 성과 조회 테스트
    all_performance = db_manager.get_agent_performance()
    print(f"  📊 전체 에이전트 성과 기록: {len(all_performance)}개")
    
    # 특정 에이전트 성과 조회
    cio_performance = db_manager.get_agent_performance(agent_name="cio")
    print(f"  📊 CIO 에이전트 성과: {len(cio_performance)}개")
    
    return len(all_performance) > 0


def test_llm_usage_logging():
    """LLM 사용량 로깅 테스트"""
    print("\n🧪 3. LLM 사용량 로깅 테스트")
    
    # 다양한 LLM 사용량 로그 생성
    usage_logs = [
        LLMUsageLog(
            timestamp=datetime.now().isoformat(),
            agent_name="cio",
            provider="claude",
            model="opus-4.1",
            tokens_used=1500,
            cost_usd=0.045,
            response_time_ms=2500,
            request_type="final_decision",
            success=True
        ),
        LLMUsageLog(
            timestamp=(datetime.now() - timedelta(minutes=5)).isoformat(),
            agent_name="technical_analyst", 
            provider="gpt",
            model="gpt-5",
            tokens_used=800,
            cost_usd=0.016,
            response_time_ms=1800,
            request_type="technical_analysis",
            success=True
        ),
        LLMUsageLog(
            timestamp=(datetime.now() - timedelta(minutes=10)).isoformat(),
            agent_name="sector_researcher",
            provider="perplexity", 
            model="sonar-pro",
            tokens_used=2000,
            cost_usd=0.020,
            response_time_ms=3200,
            request_type="market_research",
            success=True
        ),
        LLMUsageLog(
            timestamp=(datetime.now() - timedelta(minutes=15)).isoformat(),
            agent_name="valuation_analyst",
            provider="gemini",
            model="flash-2.5",
            tokens_used=1200,
            cost_usd=0.012,
            response_time_ms=2100,
            request_type="valuation_analysis", 
            success=False,
            error_message="API rate limit exceeded"
        )
    ]
    
    # 사용량 로그 삽입
    for log in usage_logs:
        success = db_manager.log_llm_usage(log)
        print(f"  ✅ {log.agent_name}({log.provider}) 사용량 로그: {success}")
    
    # 사용량 통계 조회
    stats = db_manager.get_llm_usage_stats(days=1)
    print(f"  📊 LLM 사용량 통계: {len(stats.get('provider_stats', {}))}개 제공사")
    
    for provider, stat in stats.get('provider_stats', {}).items():
        print(f"    - {provider}: {stat['total_requests']}회, ${stat['total_cost']:.3f}")
    
    return len(stats.get('provider_stats', {})) > 0


def test_model_evolution_tracking():
    """모델 진화 추적 테스트"""
    print("\n🧪 4. 모델 진화 추적 테스트")
    
    # 모델 교체 이력 기록
    evolution_records = [
        ModelEvolutionHistory(
            timestamp=datetime.now().isoformat(),
            agent_name="technical_analyst",
            old_provider="gpt",
            old_model="gpt-4o",
            new_provider="gpt", 
            new_model="gpt-5",
            reason="기술적 분석 정확도 15% 향상 확인",
            performance_improvement=0.15,
            triggered_by="automatic"
        ),
        ModelEvolutionHistory(
            timestamp=(datetime.now() - timedelta(days=7)).isoformat(),
            agent_name="cio",
            old_provider="claude",
            old_model="opus-3.5",
            new_provider="claude",
            new_model="opus-4.1", 
            reason="의사결정 품질 향상 및 응답 속도 개선",
            performance_improvement=0.12,
            triggered_by="manual"
        )
    ]
    
    # 진화 이력 기록
    for evolution in evolution_records:
        success = db_manager.log_model_evolution(evolution)
        print(f"  ✅ {evolution.agent_name} 모델 진화 이력: {success}")
    
    # 진화 이력 조회
    history = db_manager.get_model_evolution_history()
    print(f"  📊 모델 진화 이력: {len(history)}개 기록")
    
    return len(history) > 0


def test_system_metrics():
    """시스템 메트릭 테스트"""
    print("\n🧪 5. 시스템 메트릭 테스트")
    
    # 시스템 성과 지표 생성
    metrics = SystemMetrics(
        date=datetime.now().strftime("%Y-%m-%d"),
        total_trades=25,
        win_rate=72.0,
        total_pnl=245000,
        total_cost_usd=2.15,
        avg_decision_time_seconds=38.5,
        agent_efficiency_score=0.84,
        model_diversity_index=0.75,  # 4개 제공사 사용
        auto_improvements=2,
        human_interventions=0
    )
    
    # 메트릭 삽입
    success = db_manager.insert_system_metrics(metrics)
    print(f"  ✅ 시스템 메트릭 기록: {success}")
    
    # 메트릭 조회
    daily_metrics = db_manager.get_system_metrics(days=1)
    print(f"  📊 일일 시스템 메트릭: {len(daily_metrics)}개")
    
    if daily_metrics:
        today_metric = daily_metrics[0]
        print(f"    - 승률: {today_metric['win_rate']}%")
        print(f"    - 총 손익: {today_metric['total_pnl']:,}원")
        print(f"    - 에이전트 효율성: {today_metric['agent_efficiency_score']:.2f}")
    
    return len(daily_metrics) > 0


def test_advanced_analytics():
    """고급 분석 기능 테스트"""
    print("\n🧪 6. 고급 분석 기능 테스트")
    
    # 에이전트 기여도 분석
    contribution_analysis = db_manager.get_agent_contribution_analysis(days=30)
    print(f"  📊 에이전트 기여도 분석: {len(contribution_analysis.get('agent_impact', {}))}개 에이전트")
    
    for agent, impact in contribution_analysis.get('agent_impact', {}).items():
        print(f"    - {agent}: 효율성 점수 {impact['efficiency_score']:.3f}")
    
    # 저성과 에이전트 식별
    underperforming = db_manager.get_underperforming_agents(min_trades=1)
    print(f"  ⚠️  저성과 에이전트: {len(underperforming)}개")
    
    return True


def main():
    """모든 테스트 실행"""
    print("🚀 Phase 3 확장 데이터베이스 스키마 테스트 시작\n")
    
    tests = [
        ("확장된 TradeRecord", test_enhanced_trade_record),
        ("에이전트 성과 추적", test_agent_performance_tracking), 
        ("LLM 사용량 로깅", test_llm_usage_logging),
        ("모델 진화 추적", test_model_evolution_tracking),
        ("시스템 메트릭", test_system_metrics),
        ("고급 분석 기능", test_advanced_analytics)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result, None))
        except Exception as e:
            results.append((test_name, False, str(e)))
    
    # 결과 요약
    print("\n" + "="*60)
    print("📊 테스트 결과 요약")
    print("="*60)
    
    passed = 0
    for test_name, result, error in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if error:
            print(f"    오류: {error}")
        if result:
            passed += 1
    
    print(f"\n🎯 전체 결과: {passed}/{len(tests)} 테스트 통과")
    
    if passed == len(tests):
        print("🎉 모든 테스트가 성공적으로 완료되었습니다!")
        print("✅ Phase 3 데이터베이스 스키마 확장이 정상 작동합니다.")
    else:
        print("⚠️  일부 테스트가 실패했습니다. 로그를 확인하세요.")
    
    return passed == len(tests)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)