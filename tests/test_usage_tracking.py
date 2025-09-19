#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API 사용량 추적 시스템 검증 테스트

LLM 사용량 로깅, 비용 계산, 대시보드 데이터 파이프라인을 검증합니다.
"""

import time
from datetime import datetime, timedelta
from typing import Dict, List, Any

# pytest는 선택적으로 import
try:
    import pytest
    PYTEST_AVAILABLE = True
except ImportError:
    PYTEST_AVAILABLE = False

from src.llm_clients.client_factory import LLMClientFactory
from src.llm_clients.base import LLMRequest, UsageStats
from src.database.schema import DatabaseManager, LLMUsageLog, AgentPerformance


class UsageTrackingTester:
    """사용량 추적 시스템 테스터"""
    
    def __init__(self):
        self.client_factory = LLMClientFactory()
        self.db_manager = DatabaseManager()
        self.test_session_id = f"test_session_{int(time.time())}"
    
    def create_test_request(self, agent_type: str, size: str = "small") -> LLMRequest:
        """다양한 크기의 테스트 요청 생성"""
        prompts = {
            "small": "Analyze AAPL stock briefly.",
            "medium": "Provide a detailed analysis of AAPL stock including fundamentals, technicals, and market sentiment. " * 10,
            "large": "Conduct a comprehensive investment analysis covering all aspects of Apple Inc. " * 50
        }
        
        max_tokens = {
            "small": 200,
            "medium": 1000, 
            "large": 2000
        }
        
        return LLMRequest(
            prompt=prompts.get(size, prompts["small"]),
            agent_type=agent_type,
            max_tokens=max_tokens.get(size, 200),
            temperature=0.1
        )
    
    def test_token_counting_accuracy(self) -> Dict[str, Any]:
        """토큰 카운팅 정확성 테스트"""
        test_results = []
        
        test_cases = [
            ("valuation_analyst", "small"),
            ("technical_analyst", "medium"),
            ("cio", "large")
        ]
        
        for agent_type, size in test_cases:
            try:
                client = self.client_factory.get_client(agent_type)
                request = self.create_test_request(agent_type, size)
                
                # 사용량 통계 초기화
                initial_stats = client.get_usage_stats()
                initial_tokens = initial_stats.total_tokens_used
                
                # 요청 실행
                response = client.generate_response(request)
                
                # 사용량 통계 확인
                final_stats = client.get_usage_stats()
                token_increase = final_stats.total_tokens_used - initial_tokens
                
                # 토큰 수 검증 (응답에서 보고된 토큰과 통계의 증가량이 일치해야 함)
                token_accuracy = abs(token_increase - response.tokens_used) <= 5  # 5 토큰 오차 허용
                
                test_results.append({
                    'agent_type': agent_type,
                    'request_size': size,
                    'reported_tokens': response.tokens_used,
                    'stats_increase': token_increase,
                    'token_accuracy': token_accuracy,
                    'cost': response.cost,
                    'model_used': response.model_used,
                    'success': True
                })
                
            except Exception as e:
                test_results.append({
                    'agent_type': agent_type,
                    'request_size': size,
                    'success': False,
                    'error': str(e)
                })
        
        # 정확성 계산
        successful_tests = [r for r in test_results if r.get('success', False)]
        accurate_tests = [r for r in successful_tests if r.get('token_accuracy', False)]
        
        accuracy_rate = len(accurate_tests) / len(successful_tests) if successful_tests else 0
        
        return {
            'test_type': 'token_counting_accuracy',
            'total_tests': len(test_cases),
            'successful_tests': len(successful_tests),
            'accurate_tests': len(accurate_tests),
            'accuracy_rate': accuracy_rate,
            'individual_results': test_results
        }
    
    def test_cost_calculation_accuracy(self) -> Dict[str, Any]:
        """비용 계산 정확성 테스트"""
        test_results = []
        
        # 각 LLM 제공사별 비용 계산 테스트
        provider_agents = {
            'claude': 'cio',
            'gpt': 'technical_analyst',
            'gemini': 'valuation_analyst',
            'perplexity': 'sector_researcher'
        }
        
        for provider, agent_type in provider_agents.items():
            try:
                client = self.client_factory.get_client(agent_type)
                request = self.create_test_request(agent_type, "medium")
                
                # 예상 비용 계산
                estimated_cost = client.estimate_cost(request)
                
                # 실제 요청 실행
                response = client.generate_response(request)
                actual_cost = response.cost
                
                # 비용 정확성 검증 (20% 오차 허용)
                cost_difference = abs(estimated_cost - actual_cost)
                cost_accuracy = cost_difference <= (estimated_cost * 0.2)
                
                test_results.append({
                    'provider': provider,
                    'agent_type': agent_type,
                    'estimated_cost': estimated_cost,
                    'actual_cost': actual_cost,
                    'cost_difference': cost_difference,
                    'cost_accuracy': cost_accuracy,
                    'tokens_used': response.tokens_used,
                    'success': True
                })
                
            except Exception as e:
                test_results.append({
                    'provider': provider,
                    'agent_type': agent_type,
                    'success': False,
                    'error': str(e)
                })
        
        successful_tests = [r for r in test_results if r.get('success', False)]
        accurate_tests = [r for r in successful_tests if r.get('cost_accuracy', False)]
        
        accuracy_rate = len(accurate_tests) / len(successful_tests) if successful_tests else 0
        
        return {
            'test_type': 'cost_calculation_accuracy',
            'total_providers': len(provider_agents),
            'successful_tests': len(successful_tests),
            'accurate_tests': len(accurate_tests),
            'accuracy_rate': accuracy_rate,
            'individual_results': test_results
        }
    
    def test_usage_logging_to_database(self) -> Dict[str, Any]:
        """데이터베이스 사용량 로깅 테스트"""
        test_agents = ['cio', 'technical_analyst', 'valuation_analyst']
        logged_records = []
        
        for agent_type in test_agents:
            try:
                client = self.client_factory.get_client(agent_type)
                request = self.create_test_request(agent_type, "small")
                
                # 요청 실행
                response = client.generate_response(request)
                
                # 데이터베이스에 수동으로 로그 기록 (실제 시스템에서는 자동)
                usage_log = LLMUsageLog(
                    session_id=self.test_session_id,
                    agent_type=agent_type,
                    provider=response.model_used.split('-')[0] if response.model_used else 'unknown',
                    model_name=response.model_used,
                    tokens_used=response.tokens_used,
                    cost=response.cost,
                    response_time=response.response_time,
                    timestamp=datetime.now()
                )
                
                # 데이터베이스에 저장
                log_id = self.db_manager.add_llm_usage_log(usage_log)
                
                logged_records.append({
                    'log_id': log_id,
                    'agent_type': agent_type,
                    'tokens_used': response.tokens_used,
                    'cost': response.cost,
                    'model_used': response.model_used,
                    'success': True
                })
                
            except Exception as e:
                logged_records.append({
                    'agent_type': agent_type,
                    'success': False,
                    'error': str(e)
                })
        
        # 데이터베이스에서 로그 조회하여 검증
        try:
            retrieved_logs = self.db_manager.get_llm_usage_logs(session_id=self.test_session_id)
            retrieved_count = len(retrieved_logs)
            expected_count = len([r for r in logged_records if r['success']])
            
            logging_accuracy = retrieved_count == expected_count
            
        except Exception as e:
            retrieved_count = 0
            logging_accuracy = False
        
        successful_logs = [r for r in logged_records if r['success']]
        
        return {
            'test_type': 'usage_logging',
            'total_attempts': len(test_agents),
            'successful_logs': len(successful_logs),
            'retrieved_logs': retrieved_count,
            'logging_accuracy': logging_accuracy,
            'individual_results': logged_records
        }
    
    def test_real_time_stats_tracking(self) -> Dict[str, Any]:
        """실시간 통계 추적 테스트"""
        agent_type = 'cio'
        client = self.client_factory.get_client(agent_type)
        
        # 초기 상태 기록
        initial_stats = client.get_usage_stats()
        
        # 여러 요청 실행
        num_requests = 3
        requests_made = 0
        successful_requests = 0
        total_tokens = 0
        total_cost = 0.0
        
        for i in range(num_requests):
            try:
                request = self.create_test_request(agent_type, "small")
                response = client.generate_response(request)
                
                requests_made += 1
                successful_requests += 1
                total_tokens += response.tokens_used
                total_cost += response.cost
                
            except Exception:
                requests_made += 1
        
        # 최종 상태 확인
        final_stats = client.get_usage_stats()
        
        # 통계 정확성 검증
        expected_total_requests = initial_stats.total_requests + requests_made
        expected_successful_requests = initial_stats.successful_requests + successful_requests
        expected_total_tokens = initial_stats.total_tokens_used + total_tokens
        expected_total_cost = initial_stats.total_cost + total_cost
        
        stats_accuracy = (
            final_stats.total_requests == expected_total_requests and
            final_stats.successful_requests == expected_successful_requests and
            abs(final_stats.total_tokens_used - expected_total_tokens) <= 10 and  # 10 토큰 오차 허용
            abs(final_stats.total_cost - expected_total_cost) <= 0.01  # $0.01 오차 허용
        )
        
        return {
            'test_type': 'real_time_stats',
            'requests_made': requests_made,
            'successful_requests': successful_requests,
            'initial_stats': {
                'total_requests': initial_stats.total_requests,
                'successful_requests': initial_stats.successful_requests,
                'total_tokens': initial_stats.total_tokens_used,
                'total_cost': initial_stats.total_cost
            },
            'final_stats': {
                'total_requests': final_stats.total_requests,
                'successful_requests': final_stats.successful_requests,
                'total_tokens': final_stats.total_tokens_used,
                'total_cost': final_stats.total_cost
            },
            'expected_stats': {
                'total_requests': expected_total_requests,
                'successful_requests': expected_successful_requests,
                'total_tokens': expected_total_tokens,
                'total_cost': expected_total_cost
            },
            'stats_accuracy': stats_accuracy
        }
    
    def run_comprehensive_test(self) -> Dict[str, Any]:
        """종합 사용량 추적 테스트 실행"""
        print("🚀 API 사용량 추적 시스템 종합 테스트 시작")
        
        test_results = {}
        
        # 1. 토큰 카운팅 정확성 테스트
        print("🔢 토큰 카운팅 정확성 테스트 중...")
        test_results['token_counting'] = self.test_token_counting_accuracy()
        
        # 2. 비용 계산 정확성 테스트
        print("💰 비용 계산 정확성 테스트 중...")
        test_results['cost_calculation'] = self.test_cost_calculation_accuracy()
        
        # 3. 데이터베이스 로깅 테스트
        print("📝 데이터베이스 사용량 로깅 테스트 중...")
        test_results['usage_logging'] = self.test_usage_logging_to_database()
        
        # 4. 실시간 통계 추적 테스트
        print("📊 실시간 통계 추적 테스트 중...")
        test_results['real_time_stats'] = self.test_real_time_stats_tracking()
        
        # 전체 결과 요약
        all_tests_passed = all([
            test_results['token_counting']['accuracy_rate'] >= 0.9,
            test_results['cost_calculation']['accuracy_rate'] >= 0.8,
            test_results['usage_logging']['logging_accuracy'],
            test_results['real_time_stats']['stats_accuracy']
        ])
        
        test_results['summary'] = {
            'token_counting_passed': test_results['token_counting']['accuracy_rate'] >= 0.9,
            'cost_calculation_passed': test_results['cost_calculation']['accuracy_rate'] >= 0.8,
            'usage_logging_passed': test_results['usage_logging']['logging_accuracy'],
            'real_time_stats_passed': test_results['real_time_stats']['stats_accuracy'],
            'all_tests_passed': all_tests_passed
        }
        
        return test_results


# pytest 테스트 케이스들
class TestUsageTracking:
    """pytest 기반 사용량 추적 테스트"""
    
    @pytest.fixture
    def tester(self):
        """테스터 인스턴스 생성"""
        return UsageTrackingTester()
    
    def test_token_counting_accuracy(self, tester):
        """토큰 카운팅 정확성 테스트"""
        result = tester.test_token_counting_accuracy()
        
        assert result['accuracy_rate'] >= 0.9, f"Token counting accuracy {result['accuracy_rate']:.1%} is below 90%"
        
        print(f"✅ 토큰 카운팅 정확성 테스트 통과: {result['accuracy_rate']:.1%}")
    
    def test_cost_calculation_accuracy(self, tester):
        """비용 계산 정확성 테스트"""
        result = tester.test_cost_calculation_accuracy()
        
        assert result['accuracy_rate'] >= 0.8, f"Cost calculation accuracy {result['accuracy_rate']:.1%} is below 80%"
        
        print(f"✅ 비용 계산 정확성 테스트 통과: {result['accuracy_rate']:.1%}")
    
    def test_database_logging(self, tester):
        """데이터베이스 로깅 테스트"""
        result = tester.test_usage_logging_to_database()
        
        assert result['logging_accuracy'], "Database logging failed"
        
        print(f"✅ 데이터베이스 로깅 테스트 통과: {result['successful_logs']}/{result['total_attempts']}")
    
    def test_real_time_stats(self, tester):
        """실시간 통계 추적 테스트"""
        result = tester.test_real_time_stats_tracking()
        
        assert result['stats_accuracy'], "Real-time stats tracking failed"
        
        print(f"✅ 실시간 통계 추적 테스트 통과")


def main():
    """메인 실행 함수"""
    tester = UsageTrackingTester()
    results = tester.run_comprehensive_test()
    
    print("\n" + "="*60)
    print("📋 API 사용량 추적 시스템 테스트 결과")
    print("="*60)
    
    # 토큰 카운팅 결과
    token_result = results['token_counting']
    print(f"\n🔢 토큰 카운팅 정확성:")
    print(f"   정확도: {token_result['accuracy_rate']:.1%} ({token_result['accurate_tests']}/{token_result['successful_tests']})")
    
    # 비용 계산 결과
    cost_result = results['cost_calculation']
    print(f"\n💰 비용 계산 정확성:")
    print(f"   정확도: {cost_result['accuracy_rate']:.1%} ({cost_result['accurate_tests']}/{cost_result['successful_tests']})")
    
    # 데이터베이스 로깅 결과
    logging_result = results['usage_logging']
    print(f"\n📝 데이터베이스 로깅:")
    print(f"   성공: {'✅' if logging_result['logging_accuracy'] else '❌'}")
    print(f"   로그 기록: {logging_result['successful_logs']}/{logging_result['total_attempts']}")
    print(f"   조회 검증: {logging_result['retrieved_logs']}개 로그 조회됨")
    
    # 실시간 통계 결과
    stats_result = results['real_time_stats']
    print(f"\n📊 실시간 통계 추적:")
    print(f"   정확성: {'✅' if stats_result['stats_accuracy'] else '❌'}")
    print(f"   요청 수행: {stats_result['successful_requests']}/{stats_result['requests_made']}")
    
    # 전체 요약
    summary = results['summary']
    print(f"\n📈 전체 요약:")
    print(f"   토큰 카운팅: {'✅ PASS' if summary['token_counting_passed'] else '❌ FAIL'}")
    print(f"   비용 계산: {'✅ PASS' if summary['cost_calculation_passed'] else '❌ FAIL'}")
    print(f"   데이터베이스 로깅: {'✅ PASS' if summary['usage_logging_passed'] else '❌ FAIL'}")
    print(f"   실시간 통계: {'✅ PASS' if summary['real_time_stats_passed'] else '❌ FAIL'}")
    print(f"   전체 테스트: {'✅ PASS' if summary['all_tests_passed'] else '❌ FAIL'}")
    
    return results


if __name__ == "__main__":
    main()