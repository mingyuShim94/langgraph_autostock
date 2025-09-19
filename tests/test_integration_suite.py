#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
1.3 통합 테스트 및 검증 마스터 스위트

Phase 1.3의 모든 통합 테스트를 실행하고 종합 결과를 제공합니다.
"""

import time
import sys
from datetime import datetime
from typing import Dict, Any

# 개별 테스트 모듈 import
from test_multi_llm_workflow import MultiLLMWorkflowTester
from test_usage_tracking import UsageTrackingTester
from test_database_integration import DatabaseIntegrationTester
from test_error_recovery import ErrorRecoveryTester


class IntegrationTestSuite:
    """1.3 통합 테스트 마스터 스위트"""
    
    def __init__(self):
        self.test_session_id = f"integration_suite_{int(time.time())}"
        self.start_time = None
        self.end_time = None
        self.test_results = {}
    
    def run_all_tests(self) -> Dict[str, Any]:
        """모든 통합 테스트 실행"""
        self.start_time = time.time()
        
        print("🚀 Phase 1.3 통합 테스트 및 검증 시작")
        print("=" * 80)
        print(f"테스트 세션 ID: {self.test_session_id}")
        print(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # 1. 다중 LLM 동시 호출 테스트
        print("📋 1/4: 다중 LLM 동시 호출 워크플로우 테스트")
        print("-" * 50)
        try:
            workflow_tester = MultiLLMWorkflowTester()
            self.test_results['workflow'] = workflow_tester.run_comprehensive_test()
            print("✅ 다중 LLM 워크플로우 테스트 완료\n")
        except Exception as e:
            print(f"❌ 다중 LLM 워크플로우 테스트 실패: {e}\n")
            self.test_results['workflow'] = {'error': str(e), 'success': False}
        
        # 2. API 사용량 추적 시스템 테스트
        print("📋 2/4: API 사용량 추적 시스템 테스트")
        print("-" * 50)
        try:
            usage_tester = UsageTrackingTester()
            self.test_results['usage_tracking'] = usage_tester.run_comprehensive_test()
            print("✅ API 사용량 추적 테스트 완료\n")
        except Exception as e:
            print(f"❌ API 사용량 추적 테스트 실패: {e}\n")
            self.test_results['usage_tracking'] = {'error': str(e), 'success': False}
        
        # 3. 데이터베이스 확장 기능 통합 테스트
        print("📋 3/4: 데이터베이스 확장 기능 통합 테스트")
        print("-" * 50)
        try:
            db_tester = DatabaseIntegrationTester()
            self.test_results['database_integration'] = db_tester.run_comprehensive_test()
            print("✅ 데이터베이스 통합 테스트 완료\n")
        except Exception as e:
            print(f"❌ 데이터베이스 통합 테스트 실패: {e}\n")
            self.test_results['database_integration'] = {'error': str(e), 'success': False}
        
        # 4. 에러 복구 및 폴백 메커니즘 테스트
        print("📋 4/4: 에러 복구 및 폴백 메커니즘 테스트")
        print("-" * 50)
        try:
            error_tester = ErrorRecoveryTester()
            self.test_results['error_recovery'] = error_tester.run_comprehensive_test()
            print("✅ 에러 복구 메커니즘 테스트 완료\n")
        except Exception as e:
            print(f"❌ 에러 복구 메커니즘 테스트 실패: {e}\n")
            self.test_results['error_recovery'] = {'error': str(e), 'success': False}
        
        self.end_time = time.time()
        
        # 종합 결과 분석
        self.analyze_results()
        
        return self.test_results
    
    def analyze_results(self) -> None:
        """테스트 결과 분석 및 요약"""
        total_duration = self.end_time - self.start_time
        
        print("=" * 80)
        print("📊 Phase 1.3 통합 테스트 종합 결과")
        print("=" * 80)
        print(f"총 소요 시간: {total_duration:.1f}초 ({total_duration/60:.1f}분)")
        print(f"완료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # 각 테스트 영역별 결과
        test_areas = [
            ('workflow', '다중 LLM 동시 호출 워크플로우'),
            ('usage_tracking', 'API 사용량 추적 시스템'),
            ('database_integration', '데이터베이스 확장 기능 통합'),
            ('error_recovery', '에러 복구 및 폴백 메커니즘')
        ]
        
        overall_success = True
        detailed_results = {}
        
        for test_key, test_name in test_areas:
            result = self.test_results.get(test_key, {})
            
            if 'error' in result:
                print(f"❌ {test_name}: 테스트 실행 실패")
                print(f"   오류: {result['error']}")
                overall_success = False
                detailed_results[test_key] = {'status': 'ERROR', 'details': result['error']}
            
            elif test_key == 'workflow':
                summary = result.get('summary', {})
                if summary.get('test_passed', False):
                    print(f"✅ {test_name}: 통과")
                    print(f"   성공률: {summary['overall_success_rate']:.1%}")
                    print(f"   총 비용: ${summary['total_cost']:.4f}")
                    detailed_results[test_key] = {'status': 'PASS', 'success_rate': summary['overall_success_rate']}
                else:
                    print(f"❌ {test_name}: 실패")
                    overall_success = False
                    detailed_results[test_key] = {'status': 'FAIL', 'success_rate': summary.get('overall_success_rate', 0)}
            
            elif test_key == 'usage_tracking':
                summary = result.get('summary', {})
                if summary.get('all_tests_passed', False):
                    print(f"✅ {test_name}: 통과")
                    print(f"   토큰 카운팅: {'PASS' if summary['token_counting_passed'] else 'FAIL'}")
                    print(f"   비용 계산: {'PASS' if summary['cost_calculation_passed'] else 'FAIL'}")
                    detailed_results[test_key] = {'status': 'PASS'}
                else:
                    print(f"❌ {test_name}: 실패")
                    overall_success = False
                    detailed_results[test_key] = {'status': 'FAIL'}
            
            elif test_key == 'database_integration':
                summary = result.get('summary', {})
                if summary.get('all_tests_passed', False):
                    print(f"✅ {test_name}: 통과")
                    print(f"   CRUD 작업: {'PASS' if summary['crud_operations_passed'] else 'FAIL'}")
                    print(f"   데이터 무결성: {'PASS' if summary['data_integrity_passed'] else 'FAIL'}")
                    detailed_results[test_key] = {'status': 'PASS'}
                else:
                    print(f"❌ {test_name}: 실패")
                    overall_success = False
                    detailed_results[test_key] = {'status': 'FAIL'}
            
            elif test_key == 'error_recovery':
                summary = result.get('summary', {})
                if summary.get('all_tests_passed', False):
                    print(f"✅ {test_name}: 통과")
                    print(f"   장애 복구: {'PASS' if summary['failure_recovery_passed'] else 'FAIL'}")
                    print(f"   연쇄 장애 방지: {'PASS' if summary['cascade_prevention_passed'] else 'FAIL'}")
                    detailed_results[test_key] = {'status': 'PASS'}
                else:
                    print(f"❌ {test_name}: 실패")
                    overall_success = False
                    detailed_results[test_key] = {'status': 'FAIL'}
            
            print()
        
        # 최종 판정
        print("=" * 80)
        if overall_success:
            print("🎉 Phase 1.3 통합 테스트 및 검증 완료!")
            print("✅ 모든 테스트가 성공적으로 통과되었습니다.")
            print("\n🚀 Phase 2 진행 준비 완료!")
        else:
            print("⚠️  Phase 1.3 통합 테스트에서 일부 실패가 발생했습니다.")
            print("❌ 실패한 테스트를 먼저 수정해야 합니다.")
        
        print("=" * 80)
        
        # 결과 요약을 test_results에 추가
        self.test_results['integration_summary'] = {
            'overall_success': overall_success,
            'total_duration': total_duration,
            'test_count': len(test_areas),
            'passed_tests': sum(1 for details in detailed_results.values() if details['status'] == 'PASS'),
            'failed_tests': sum(1 for details in detailed_results.values() if details['status'] == 'FAIL'),
            'error_tests': sum(1 for details in detailed_results.values() if details['status'] == 'ERROR'),
            'detailed_results': detailed_results,
            'timestamp': datetime.now().isoformat()
        }
    
    def generate_report(self) -> str:
        """테스트 결과 리포트 생성"""
        if not self.test_results:
            return "테스트가 아직 실행되지 않았습니다."
        
        summary = self.test_results.get('integration_summary', {})
        
        report = f"""
# Phase 1.3 통합 테스트 및 검증 리포트

## 테스트 개요
- **실행 시간**: {summary.get('timestamp', 'N/A')}
- **세션 ID**: {self.test_session_id}
- **총 소요 시간**: {summary.get('total_duration', 0):.1f}초
- **전체 결과**: {'✅ PASS' if summary.get('overall_success', False) else '❌ FAIL'}

## 테스트 결과 요약
- **총 테스트 영역**: {summary.get('test_count', 0)}개
- **통과**: {summary.get('passed_tests', 0)}개
- **실패**: {summary.get('failed_tests', 0)}개
- **오류**: {summary.get('error_tests', 0)}개

## 세부 테스트 결과

### 1. 다중 LLM 동시 호출 워크플로우
- **상태**: {summary.get('detailed_results', {}).get('workflow', {}).get('status', 'N/A')}
- **설명**: 4개 전문가 에이전트 병렬 처리 및 순차 워크플로우 검증

### 2. API 사용량 추적 시스템
- **상태**: {summary.get('detailed_results', {}).get('usage_tracking', {}).get('status', 'N/A')}
- **설명**: 토큰 카운팅, 비용 계산, 사용량 로깅 정확성 검증

### 3. 데이터베이스 확장 기능 통합
- **상태**: {summary.get('detailed_results', {}).get('database_integration', {}).get('status', 'N/A')}
- **설명**: 새 테이블 CRUD, 에이전트 성과 추적, 데이터 무결성 검증

### 4. 에러 복구 및 폴백 메커니즘
- **상태**: {summary.get('detailed_results', {}).get('error_recovery', {}).get('status', 'N/A')}
- **설명**: API 장애 복구, 타임아웃 처리, 연쇄 장애 방지 검증

## 결론
"""
        
        if summary.get('overall_success', False):
            report += """
✅ **Phase 1.3 통합 테스트가 성공적으로 완료되었습니다.**

하이브리드 LLM 인프라 및 중앙 메모리 고도화가 완료되어 Phase 2 진행이 가능합니다.

### 다음 단계
- Phase 2: 전문가 팀 기반 운영 그래프 구현 (9개 노드)
- 4개 전문가 에이전트의 병렬 분석 시스템 구축
- CIO 에이전트 기반 최종 의사결정 시스템 구현
"""
        else:
            report += """
⚠️ **일부 테스트에서 실패가 발생했습니다.**

Phase 2 진행 전에 실패한 테스트를 수정해야 합니다.

### 권장 조치
1. 실패한 테스트 영역의 상세 로그 확인
2. 해당 컴포넌트 수정 및 재테스트
3. 모든 테스트 통과 후 Phase 2 진행
"""
        
        return report


def main():
    """메인 실행 함수"""
    suite = IntegrationTestSuite()
    
    try:
        # 모든 테스트 실행
        results = suite.run_all_tests()
        
        # 리포트 생성 및 출력
        report = suite.generate_report()
        print("\n" + report)
        
        # 결과에 따른 종료 코드 반환
        if results.get('integration_summary', {}).get('overall_success', False):
            print("\n🎯 모든 테스트가 성공적으로 완료되었습니다!")
            return 0
        else:
            print("\n⚠️ 일부 테스트가 실패했습니다. 수정이 필요합니다.")
            return 1
            
    except KeyboardInterrupt:
        print("\n⏹️ 사용자에 의해 테스트가 중단되었습니다.")
        return 130
    except Exception as e:
        print(f"\n❌ 테스트 실행 중 예상치 못한 오류가 발생했습니다: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)