#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
실시간 성과 대시보드 시스템 테스트
전체 파이프라인, API, 메트릭 계산 검증
"""

import sys
import time
import threading
from pathlib import Path
from datetime import datetime

# 프로젝트 루트 경로 추가
sys.path.append(str(Path(__file__).parent))

from src.dashboard import DashboardDataPipeline, PerformanceMetricsCalculator, DashboardAPI
from src.dashboard.dashboard_data_pipeline import PipelineConfig


def test_performance_metrics():
    """성과 메트릭 계산 테스트"""
    print("🧪 1. 성과 메트릭 계산 테스트")
    
    calculator = PerformanceMetricsCalculator()
    
    # 실시간 메트릭 계산
    print("   📊 실시간 메트릭 계산 중...")
    metrics = calculator.get_real_time_metrics()
    
    print(f"   ✅ 오늘 거래 수: {metrics.total_trades_today}")
    print(f"   ✅ 오늘 승률: {metrics.win_rate_today}%")
    print(f"   ✅ 오늘 손익: {metrics.total_pnl_today:,}원")
    print(f"   ✅ 오늘 비용: ${metrics.total_cost_today}")
    print(f"   ✅ 에이전트 수: {len(metrics.agent_performance)}")
    
    # 에이전트 순위
    print("\n   📊 에이전트 순위 계산 중...")
    ranking = calculator.get_agent_ranking(period_days=7)
    
    if ranking:
        print("   🏆 상위 에이전트:")
        for i, agent in enumerate(ranking[:3], 1):
            print(f"      {i}위: {agent['agent']} (효율성: {agent['efficiency_score']})")
    else:
        print("   ⚠️  순위 데이터 없음")
    
    # 비용 효율성 분석
    print("\n   💰 비용 효율성 분석 중...")
    cost_analysis = calculator.get_cost_efficiency_analysis()
    
    if cost_analysis:
        print(f"   💸 7일 총 비용: ${cost_analysis.get('total_cost_7d', 0)}")
        print(f"   💹 7일 총 손익: {cost_analysis.get('total_pnl_7d', 0):,}원")
        print(f"   📈 ROI: {cost_analysis.get('roi_percentage', 0)}%")
    else:
        print("   ⚠️  비용 분석 데이터 없음")
    
    return True


def test_data_pipeline():
    """데이터 파이프라인 테스트"""
    print("\n🧪 2. 데이터 파이프라인 테스트")
    
    # 짧은 업데이트 주기로 테스트 설정
    config = PipelineConfig(
        update_interval_seconds=10,  # 10초마다 업데이트
        cache_duration_minutes=1,    # 1분 캐시
        enable_real_time_updates=True,
        export_to_file=True
    )
    
    pipeline = DashboardDataPipeline(config)
    
    # 파이프라인 시작
    print("   🚀 파이프라인 시작...")
    pipeline.start()
    
    # 상태 확인
    status = pipeline.get_health_status()
    print(f"   ✅ 파이프라인 상태: {'실행중' if status['is_running'] else '중지됨'}")
    print(f"   ✅ 캐시 디렉토리: {status['cache_directory']}")
    
    # 구독자 테스트
    update_count = [0]  # 리스트로 감싸서 클로저에서 수정 가능하게
    
    def metrics_subscriber(metrics):
        update_count[0] += 1
        print(f"   📡 메트릭 업데이트 수신 #{update_count[0]} - 시간: {metrics.timestamp}")
        print(f"      오늘 거래: {metrics.total_trades_today}, 승률: {metrics.win_rate_today}%")
    
    pipeline.subscribe(metrics_subscriber)
    
    # 강제 업데이트 테스트
    print("   🔄 강제 업데이트 테스트...")
    pipeline.force_update()
    
    # 잠시 대기 (실시간 업데이트 확인)
    print("   ⏳ 15초간 실시간 업데이트 테스트...")
    time.sleep(15)
    
    # 스냅샷 export 테스트
    print("   📸 스냅샷 export 테스트...")
    snapshot_path = pipeline.export_current_snapshot()
    print(f"   ✅ 스냅샷 저장: {snapshot_path}")
    
    # 캐시된 메트릭 조회
    cached_metrics = pipeline.get_cached_metrics(hours_back=1)
    print(f"   📂 캐시된 메트릭: {len(cached_metrics)}개")
    
    # 파이프라인 중지
    print("   🛑 파이프라인 중지...")
    pipeline.stop()
    
    return True


def test_api_endpoints():
    """API 엔드포인트 테스트"""
    print("\n🧪 3. API 엔드포인트 테스트")
    
    try:
        # API 서버 생성 (실행하지는 않음)
        api = DashboardAPI(host="localhost", port=8080, debug=True)
        app = api.get_app()
        
        print("   ✅ API 서버 인스턴스 생성 완료")
        print("   ✅ Flask 앱 설정 완료")
        
        # 테스트 클라이언트로 API 엔드포인트 테스트
        with app.test_client() as client:
            
            # 헬스 체크
            print("   🏥 헬스 체크 테스트...")
            response = client.get('/api/health')
            assert response.status_code == 200
            health_data = response.get_json()
            print(f"      상태: {health_data['status']}")
            
            # 실시간 메트릭
            print("   📊 실시간 메트릭 API 테스트...")
            response = client.get('/api/metrics/realtime')
            assert response.status_code == 200
            metrics_data = response.get_json()
            print(f"      성공: {metrics_data['success']}")
            
            # 시스템 개요
            print("   🖥️  시스템 개요 API 테스트...")
            response = client.get('/api/system/overview')
            assert response.status_code == 200
            overview_data = response.get_json()
            print(f"      성공: {overview_data['success']}")
            
            # 에이전트 순위
            print("   🏆 에이전트 순위 API 테스트...")
            response = client.get('/api/agents/ranking?days=7')
            assert response.status_code == 200
            ranking_data = response.get_json()
            print(f"      성공: {ranking_data['success']}")
            
            # LLM 사용량
            print("   🤖 LLM 사용량 API 테스트...")
            response = client.get('/api/llm/usage?days=7')
            assert response.status_code == 200
            usage_data = response.get_json()
            print(f"      성공: {usage_data['success']}")
            
            # 비용 효율성
            print("   💰 비용 효율성 API 테스트...")
            response = client.get('/api/cost/efficiency')
            assert response.status_code == 200
            cost_data = response.get_json()
            print(f"      성공: {cost_data['success']}")
        
        print("   ✅ 모든 API 엔드포인트 테스트 통과")
        return True
        
    except Exception as e:
        print(f"   ❌ API 테스트 실패: {e}")
        return False


def test_integration():
    """통합 테스트"""
    print("\n🧪 4. 통합 테스트")
    
    try:
        from src.dashboard.dashboard_data_pipeline import start_dashboard_pipeline
        
        # 전역 파이프라인 시작
        print("   🌐 전역 파이프라인 시작...")
        pipeline = start_dashboard_pipeline(
            config=PipelineConfig(
                update_interval_seconds=5,
                enable_real_time_updates=True,
                export_to_file=True
            )
        )
        
        # 잠시 실행
        print("   ⏳ 10초간 통합 시스템 실행...")
        time.sleep(10)
        
        # 상태 확인
        status = pipeline.get_health_status()
        print(f"   📊 파이프라인 실행 상태: {status['is_running']}")
        print(f"   📂 캐시 파일 수: {status['cache_files_count']}")
        
        # 파이프라인 중지
        from src.dashboard.dashboard_data_pipeline import stop_dashboard_pipeline
        stop_dashboard_pipeline()
        
        print("   ✅ 통합 테스트 완료")
        return True
        
    except Exception as e:
        print(f"   ❌ 통합 테스트 실패: {e}")
        return False


def main():
    """모든 테스트 실행"""
    print("🚀 실시간 성과 대시보드 시스템 테스트 시작\n")
    
    tests = [
        ("성과 메트릭 계산", test_performance_metrics),
        ("데이터 파이프라인", test_data_pipeline),
        ("API 엔드포인트", test_api_endpoints),
        ("시스템 통합", test_integration)
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
    print("📊 대시보드 시스템 테스트 결과")
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
        print("🎉 모든 대시보드 시스템 테스트가 성공적으로 완료되었습니다!")
        print("✅ 실시간 성과 대시보드 데이터 파이프라인이 정상 작동합니다.")
        
        print("\n📡 API 서버 실행 방법:")
        print("   python -c \"from src.dashboard.api_endpoints import create_dashboard_api; api = create_dashboard_api(); api.run()\"")
        
        print("\n🔗 주요 API 엔드포인트:")
        print("   http://localhost:8080/api/health")
        print("   http://localhost:8080/api/metrics/realtime")
        print("   http://localhost:8080/api/system/overview")
        print("   http://localhost:8080/api/agents/ranking")
    else:
        print("⚠️  일부 테스트가 실패했습니다. 로그를 확인하세요.")
    
    return passed == len(tests)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)