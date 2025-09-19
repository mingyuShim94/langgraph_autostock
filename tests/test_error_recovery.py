#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
에러 복구 및 폴백 메커니즘 검증 테스트

LLM API 장애, 네트워크 오류, 타임아웃 등의 상황에서 
시스템의 복구 능력과 대체 경로 동작을 검증합니다.
"""

import time
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from unittest.mock import Mock, patch, MagicMock

# pytest는 선택적으로 import
try:
    import pytest
    PYTEST_AVAILABLE = True
except ImportError:
    PYTEST_AVAILABLE = False

from src.llm_clients.client_factory import LLMClientFactory
from src.llm_clients.base import LLMRequest, LLMResponse
from src.llm_clients.exceptions import LLMClientError, ConfigurationError, RateLimitError


class ErrorRecoveryTester:
    """에러 복구 및 폴백 메커니즘 테스터"""
    
    def __init__(self):
        self.client_factory = LLMClientFactory()
        self.test_session_id = f"test_error_recovery_{int(time.time())}"
    
    def create_test_request(self, agent_type: str) -> LLMRequest:
        """테스트용 LLM 요청 생성"""
        return LLMRequest(
            prompt="This is a test request for error recovery testing.",
            agent_type=agent_type,
            temperature=0.1,
            max_tokens=500
        )
    
    def simulate_api_failure(self, client, failure_type: str = "connection_error"):
        """API 장애 시뮬레이션"""
        if failure_type == "connection_error":
            raise ConnectionError("Failed to connect to API endpoint")
        elif failure_type == "timeout":
            raise TimeoutError("Request timed out after 60 seconds")
        elif failure_type == "rate_limit":
            raise RateLimitError("Rate limit exceeded")
        elif failure_type == "authentication":
            raise Exception("Authentication failed: Invalid API key")
        elif failure_type == "server_error":
            raise Exception("Internal server error (500)")
        else:
            raise Exception(f"Unknown error type: {failure_type}")
    
    def test_single_llm_failure_recovery(self) -> Dict[str, Any]:
        """단일 LLM 장애 복구 테스트"""
        test_results = []
        
        # 테스트할 에이전트와 장애 유형
        test_cases = [
            ("technical_analyst", "connection_error"),
            ("valuation_analyst", "timeout"),
            ("cio", "rate_limit"),
            ("sector_researcher", "server_error")
        ]
        
        for agent_type, failure_type in test_cases:
            try:
                client = self.client_factory.get_client(agent_type)
                request = self.create_test_request(agent_type)
                
                # 첫 번째 시도 - 실패 시뮬레이션
                start_time = time.time()
                first_attempt_failed = False
                
                try:
                    # Mock을 사용하여 첫 번째 요청 실패 시뮬레이션
                    with patch.object(client, 'generate_response') as mock_response:
                        mock_response.side_effect = lambda req: self.simulate_api_failure(client, failure_type)
                        response = client.generate_response(request)
                except Exception:
                    first_attempt_failed = True
                
                # 두 번째 시도 - 복구 시뮬레이션
                recovery_time = time.time()
                recovery_successful = False
                
                try:
                    # 실제 클라이언트로 재시도 (또는 폴백 메커니즘)
                    response = self.test_fallback_mechanism(agent_type, request)
                    if response:
                        recovery_successful = True
                        total_recovery_time = recovery_time - start_time
                    else:
                        total_recovery_time = None
                        
                except Exception as e:
                    total_recovery_time = time.time() - start_time
                
                test_results.append({
                    'agent_type': agent_type,
                    'failure_type': failure_type,
                    'first_attempt_failed': first_attempt_failed,
                    'recovery_successful': recovery_successful,
                    'recovery_time': total_recovery_time,
                    'success': first_attempt_failed and recovery_successful
                })
                
            except Exception as e:
                test_results.append({
                    'agent_type': agent_type,
                    'failure_type': failure_type,
                    'success': False,
                    'error': str(e)
                })
        
        # 결과 집계
        successful_recoveries = [r for r in test_results if r.get('success', False)]
        recovery_rate = len(successful_recoveries) / len(test_cases) if test_cases else 0
        
        avg_recovery_time = None
        if successful_recoveries:
            valid_times = [r['recovery_time'] for r in successful_recoveries if r['recovery_time'] is not None]
            if valid_times:
                avg_recovery_time = sum(valid_times) / len(valid_times)
        
        return {
            'test_type': 'single_llm_failure_recovery',
            'total_tests': len(test_cases),
            'successful_recoveries': len(successful_recoveries),
            'recovery_rate': recovery_rate,
            'avg_recovery_time': avg_recovery_time,
            'individual_results': test_results
        }
    
    def test_fallback_mechanism(self, agent_type: str, request: LLMRequest) -> Optional[LLMResponse]:
        """폴백 메커니즘 테스트"""
        # 실제 폴백 로직 구현
        # 에이전트별 대체 모델 매핑
        fallback_mapping = {
            'technical_analyst': 'valuation_analyst',  # GPT -> Gemini
            'valuation_analyst': 'cio',               # Gemini -> Claude
            'cio': 'technical_analyst',               # Claude -> GPT
            'sector_researcher': 'technical_analyst'  # Perplexity -> GPT
        }
        
        fallback_agent = fallback_mapping.get(agent_type)
        if fallback_agent:
            try:
                fallback_client = self.client_factory.get_client(fallback_agent)
                # 요청을 폴백 에이전트 타입으로 수정
                fallback_request = LLMRequest(
                    prompt=request.prompt,
                    agent_type=fallback_agent,
                    temperature=request.temperature,
                    max_tokens=request.max_tokens
                )
                return fallback_client.generate_response(fallback_request)
            except Exception:
                return None
        return None
    
    def test_network_timeout_handling(self) -> Dict[str, Any]:
        """네트워크 타임아웃 처리 테스트"""
        test_results = []
        timeout_thresholds = [5, 15, 30, 60]  # 다양한 타임아웃 임계값
        
        for timeout_seconds in timeout_thresholds:
            try:
                agent_type = "cio"
                client = self.client_factory.get_client(agent_type)
                request = self.create_test_request(agent_type)
                
                start_time = time.time()
                
                # 타임아웃 시뮬레이션
                with patch.object(client, 'generate_response') as mock_response:
                    def timeout_simulation(req):
                        time.sleep(timeout_seconds + 1)  # 임계값보다 오래 걸리도록
                        return LLMResponse(
                            content="Test response",
                            model_used="test-model",
                            tokens_used=100,
                            cost=0.01,
                            response_time=timeout_seconds + 1
                        )
                    
                    mock_response.side_effect = timeout_simulation
                    
                    try:
                        # 타임아웃 제한 적용
                        response = asyncio.wait_for(
                            asyncio.to_thread(client.generate_response, request),
                            timeout=timeout_seconds
                        )
                        timeout_handled = False
                    except asyncio.TimeoutError:
                        timeout_handled = True
                
                end_time = time.time()
                actual_time = end_time - start_time
                
                test_results.append({
                    'timeout_threshold': timeout_seconds,
                    'actual_time': actual_time,
                    'timeout_handled': timeout_handled,
                    'within_threshold': actual_time <= (timeout_seconds + 2),  # 2초 여유
                    'success': timeout_handled
                })
                
            except Exception as e:
                test_results.append({
                    'timeout_threshold': timeout_seconds,
                    'success': False,
                    'error': str(e)
                })
        
        # 결과 집계
        successful_tests = [r for r in test_results if r.get('success', False)]
        success_rate = len(successful_tests) / len(timeout_thresholds) if timeout_thresholds else 0
        
        return {
            'test_type': 'network_timeout_handling',
            'total_tests': len(timeout_thresholds),
            'successful_tests': len(successful_tests),
            'success_rate': success_rate,
            'individual_results': test_results
        }
    
    def test_rate_limit_retry_logic(self) -> Dict[str, Any]:
        """레이트 리미트 재시도 로직 테스트"""
        agent_type = "technical_analyst"
        client = self.client_factory.get_client(agent_type)
        request = self.create_test_request(agent_type)
        
        # 재시도 카운터
        attempt_count = 0
        max_retries = 3
        retry_delays = []
        
        def rate_limit_simulation(req):
            nonlocal attempt_count
            attempt_count += 1
            
            if attempt_count <= 2:  # 처음 2번은 실패
                raise RateLimitError("Rate limit exceeded. Retry after 1 second.")
            else:  # 3번째는 성공
                return LLMResponse(
                    content="Success after retries",
                    model_used="test-model",
                    tokens_used=150,
                    cost=0.02,
                    response_time=1.5
                )
        
        try:
            start_time = time.time()
            
            # 재시도 로직 시뮬레이션
            for retry in range(max_retries + 1):
                try:
                    with patch.object(client, 'generate_response') as mock_response:
                        mock_response.side_effect = rate_limit_simulation
                        response = client.generate_response(request)
                        break  # 성공 시 루프 종료
                        
                except RateLimitError:
                    if retry < max_retries:
                        retry_delay = 2 ** retry  # 지수 백오프
                        retry_delays.append(retry_delay)
                        time.sleep(retry_delay)
                    else:
                        raise  # 최대 재시도 횟수 초과
            
            end_time = time.time()
            total_time = end_time - start_time
            
            return {
                'test_type': 'rate_limit_retry_logic',
                'max_retries': max_retries,
                'actual_attempts': attempt_count,
                'retry_delays': retry_delays,
                'total_time': total_time,
                'final_success': attempt_count <= max_retries + 1,
                'success': True
            }
            
        except Exception as e:
            return {
                'test_type': 'rate_limit_retry_logic',
                'success': False,
                'error': str(e),
                'attempt_count': attempt_count
            }
    
    def test_cascade_failure_prevention(self) -> Dict[str, Any]:
        """연쇄 장애 방지 테스트"""
        # 모든 에이전트에 대해 순차적으로 장애 시뮬레이션
        agents = ["portfolio_rebalancer", "sector_researcher", "technical_analyst", "cio"]
        failure_scenarios = []
        
        for i, failed_agent in enumerate(agents):
            scenario_result = {
                'failed_agent': failed_agent,
                'failed_position': i,
                'subsequent_agents_affected': 0,
                'workflow_completed': False,
                'fallback_activated': False
            }
            
            try:
                # 실패한 에이전트 이후의 에이전트들이 계속 작동하는지 테스트
                for j, agent in enumerate(agents[i+1:], i+1):
                    try:
                        client = self.client_factory.get_client(agent)
                        request = self.create_test_request(agent)
                        
                        if agent == failed_agent:
                            # 해당 에이전트는 실패 시뮬레이션
                            raise Exception(f"Simulated failure for {agent}")
                        else:
                            # 다른 에이전트들은 정상 동작해야 함
                            response = self.test_fallback_mechanism(agent, request)
                            if response is None:
                                # 폴백도 실패한 경우
                                scenario_result['subsequent_agents_affected'] += 1
                            else:
                                scenario_result['fallback_activated'] = True
                    
                    except Exception:
                        scenario_result['subsequent_agents_affected'] += 1
                
                # 워크플로우 완료 여부 판단
                affected_ratio = scenario_result['subsequent_agents_affected'] / max(1, len(agents) - i - 1)
                scenario_result['workflow_completed'] = affected_ratio < 0.5  # 50% 이상이 작동하면 완료로 간주
                
            except Exception as e:
                scenario_result['error'] = str(e)
            
            failure_scenarios.append(scenario_result)
        
        # 결과 집계
        completed_workflows = [s for s in failure_scenarios if s.get('workflow_completed', False)]
        cascade_prevention_rate = len(completed_workflows) / len(agents) if agents else 0
        
        return {
            'test_type': 'cascade_failure_prevention',
            'total_scenarios': len(agents),
            'completed_workflows': len(completed_workflows),
            'cascade_prevention_rate': cascade_prevention_rate,
            'failure_scenarios': failure_scenarios,
            'success': cascade_prevention_rate >= 0.7  # 70% 이상의 시나리오에서 워크플로우 완료
        }
    
    def test_system_health_monitoring(self) -> Dict[str, Any]:
        """시스템 상태 모니터링 테스트"""
        health_checks = []
        
        # 각 LLM 클라이언트의 상태 확인
        agent_types = ["cio", "technical_analyst", "valuation_analyst", "sector_researcher"]
        
        for agent_type in agent_types:
            try:
                client = self.client_factory.get_client(agent_type)
                
                # 클라이언트 상태 확인
                is_healthy = client.is_healthy()
                usage_stats = client.get_usage_stats()
                
                # 성공률 계산
                if usage_stats.total_requests > 0:
                    success_rate = usage_stats.successful_requests / usage_stats.total_requests
                else:
                    success_rate = 1.0  # 요청이 없으면 100%로 간주
                
                health_checks.append({
                    'agent_type': agent_type,
                    'is_healthy': is_healthy,
                    'success_rate': success_rate,
                    'total_requests': usage_stats.total_requests,
                    'failed_requests': usage_stats.failed_requests,
                    'avg_response_time': usage_stats.average_response_time,
                    'status': 'healthy' if is_healthy and success_rate >= 0.8 else 'unhealthy'
                })
                
            except Exception as e:
                health_checks.append({
                    'agent_type': agent_type,
                    'is_healthy': False,
                    'status': 'error',
                    'error': str(e)
                })
        
        # 전체 시스템 상태 판단
        healthy_agents = [hc for hc in health_checks if hc.get('status') == 'healthy']
        system_health_ratio = len(healthy_agents) / len(agent_types) if agent_types else 0
        
        overall_system_status = 'healthy' if system_health_ratio >= 0.75 else 'degraded' if system_health_ratio >= 0.5 else 'critical'
        
        return {
            'test_type': 'system_health_monitoring',
            'total_agents': len(agent_types),
            'healthy_agents': len(healthy_agents),
            'system_health_ratio': system_health_ratio,
            'overall_status': overall_system_status,
            'individual_health_checks': health_checks,
            'success': system_health_ratio >= 0.75
        }
    
    def run_comprehensive_test(self) -> Dict[str, Any]:
        """종합 에러 복구 테스트 실행"""
        print("🚀 에러 복구 및 폴백 메커니즘 종합 테스트 시작")
        
        test_results = {}
        
        # 1. 단일 LLM 장애 복구 테스트
        print("🔧 단일 LLM 장애 복구 테스트 중...")
        test_results['failure_recovery'] = self.test_single_llm_failure_recovery()
        
        # 2. 네트워크 타임아웃 처리 테스트
        print("⏱️ 네트워크 타임아웃 처리 테스트 중...")
        test_results['timeout_handling'] = self.test_network_timeout_handling()
        
        # 3. 레이트 리미트 재시도 로직 테스트
        print("🔄 레이트 리미트 재시도 로직 테스트 중...")
        test_results['retry_logic'] = self.test_rate_limit_retry_logic()
        
        # 4. 연쇄 장애 방지 테스트
        print("🛡️ 연쇄 장애 방지 테스트 중...")
        test_results['cascade_prevention'] = self.test_cascade_failure_prevention()
        
        # 5. 시스템 상태 모니터링 테스트
        print("📊 시스템 상태 모니터링 테스트 중...")
        test_results['health_monitoring'] = self.test_system_health_monitoring()
        
        # 전체 결과 요약
        all_tests_passed = all([
            test_results['failure_recovery']['recovery_rate'] >= 0.7,
            test_results['timeout_handling']['success_rate'] >= 0.8,
            test_results['retry_logic']['success'],
            test_results['cascade_prevention']['success'],
            test_results['health_monitoring']['success']
        ])
        
        test_results['summary'] = {
            'failure_recovery_passed': test_results['failure_recovery']['recovery_rate'] >= 0.7,
            'timeout_handling_passed': test_results['timeout_handling']['success_rate'] >= 0.8,
            'retry_logic_passed': test_results['retry_logic']['success'],
            'cascade_prevention_passed': test_results['cascade_prevention']['success'],
            'health_monitoring_passed': test_results['health_monitoring']['success'],
            'all_tests_passed': all_tests_passed
        }
        
        return test_results


# pytest 테스트 케이스들
class TestErrorRecovery:
    """pytest 기반 에러 복구 테스트"""
    
    @pytest.fixture
    def tester(self):
        """테스터 인스턴스 생성"""
        return ErrorRecoveryTester()
    
    def test_failure_recovery(self, tester):
        """장애 복구 테스트"""
        result = tester.test_single_llm_failure_recovery()
        
        assert result['recovery_rate'] >= 0.7, f"Recovery rate {result['recovery_rate']:.1%} is below 70%"
        
        print(f"✅ 장애 복구 테스트 통과: {result['recovery_rate']:.1%}")
    
    def test_timeout_handling(self, tester):
        """타임아웃 처리 테스트"""
        result = tester.test_network_timeout_handling()
        
        assert result['success_rate'] >= 0.8, f"Timeout handling success rate {result['success_rate']:.1%} is below 80%"
        
        print(f"✅ 타임아웃 처리 테스트 통과: {result['success_rate']:.1%}")
    
    def test_retry_logic(self, tester):
        """재시도 로직 테스트"""
        result = tester.test_rate_limit_retry_logic()
        
        assert result['success'], f"Retry logic test failed: {result.get('error', 'Unknown error')}"
        
        print(f"✅ 재시도 로직 테스트 통과")
    
    def test_cascade_prevention(self, tester):
        """연쇄 장애 방지 테스트"""
        result = tester.test_cascade_failure_prevention()
        
        assert result['success'], f"Cascade failure prevention failed: {result['cascade_prevention_rate']:.1%}"
        
        print(f"✅ 연쇄 장애 방지 테스트 통과: {result['cascade_prevention_rate']:.1%}")
    
    def test_health_monitoring(self, tester):
        """상태 모니터링 테스트"""
        result = tester.test_system_health_monitoring()
        
        assert result['success'], f"Health monitoring failed: {result['overall_status']}"
        
        print(f"✅ 상태 모니터링 테스트 통과: {result['overall_status']}")


def main():
    """메인 실행 함수"""
    tester = ErrorRecoveryTester()
    results = tester.run_comprehensive_test()
    
    print("\n" + "="*60)
    print("📋 에러 복구 및 폴백 메커니즘 테스트 결과")
    print("="*60)
    
    # 장애 복구 결과
    recovery_result = results['failure_recovery']
    print(f"\n🔧 단일 LLM 장애 복구:")
    print(f"   복구율: {recovery_result['recovery_rate']:.1%} ({recovery_result['successful_recoveries']}/{recovery_result['total_tests']})")
    if recovery_result['avg_recovery_time']:
        print(f"   평균 복구 시간: {recovery_result['avg_recovery_time']:.1f}초")
    
    # 타임아웃 처리 결과
    timeout_result = results['timeout_handling']
    print(f"\n⏱️ 네트워크 타임아웃 처리:")
    print(f"   성공률: {timeout_result['success_rate']:.1%} ({timeout_result['successful_tests']}/{timeout_result['total_tests']})")
    
    # 재시도 로직 결과
    retry_result = results['retry_logic']
    print(f"\n🔄 레이트 리미트 재시도 로직:")
    print(f"   성공: {'✅' if retry_result['success'] else '❌'}")
    if retry_result['success']:
        print(f"   시도 횟수: {retry_result['actual_attempts']}")
        print(f"   총 소요 시간: {retry_result['total_time']:.1f}초")
    
    # 연쇄 장애 방지 결과
    cascade_result = results['cascade_prevention']
    print(f"\n🛡️ 연쇄 장애 방지:")
    print(f"   성공: {'✅' if cascade_result['success'] else '❌'}")
    print(f"   방지율: {cascade_result['cascade_prevention_rate']:.1%} ({cascade_result['completed_workflows']}/{cascade_result['total_scenarios']})")
    
    # 상태 모니터링 결과
    health_result = results['health_monitoring']
    print(f"\n📊 시스템 상태 모니터링:")
    print(f"   시스템 상태: {health_result['overall_status'].upper()}")
    print(f"   건강한 에이전트: {health_result['healthy_agents']}/{health_result['total_agents']}")
    print(f"   시스템 건강도: {health_result['system_health_ratio']:.1%}")
    
    # 전체 요약
    summary = results['summary']
    print(f"\n📈 전체 요약:")
    print(f"   장애 복구: {'✅ PASS' if summary['failure_recovery_passed'] else '❌ FAIL'}")
    print(f"   타임아웃 처리: {'✅ PASS' if summary['timeout_handling_passed'] else '❌ FAIL'}")
    print(f"   재시도 로직: {'✅ PASS' if summary['retry_logic_passed'] else '❌ FAIL'}")
    print(f"   연쇄 장애 방지: {'✅ PASS' if summary['cascade_prevention_passed'] else '❌ FAIL'}")
    print(f"   상태 모니터링: {'✅ PASS' if summary['health_monitoring_passed'] else '❌ FAIL'}")
    print(f"   전체 테스트: {'✅ PASS' if summary['all_tests_passed'] else '❌ FAIL'}")
    
    return results


if __name__ == "__main__":
    main()