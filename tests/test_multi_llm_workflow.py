#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
다중 LLM 동시 호출 워크플로우 테스트

실제 에이전트 워크플로우에서 발생하는 동시 LLM 호출 시나리오를 테스트합니다.
"""

import asyncio
import time
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

# pytest는 선택적으로 import (없어도 클래스는 작동)
try:
    import pytest
    PYTEST_AVAILABLE = True
except ImportError:
    PYTEST_AVAILABLE = False

from src.llm_clients.client_factory import LLMClientFactory
from src.llm_clients.base import LLMRequest, LLMResponse


class MultiLLMWorkflowTester:
    """다중 LLM 워크플로우 테스트 클래스"""
    
    def __init__(self):
        self.client_factory = LLMClientFactory()
        self.test_results = {}
    
    def create_test_request(self, agent_type: str, test_prompt: str = None) -> LLMRequest:
        """테스트용 LLM 요청 생성"""
        if test_prompt is None:
            test_prompt = f"This is a test request for {agent_type} agent. Please respond with a brief analysis."
        
        return LLMRequest(
            prompt=test_prompt,
            agent_type=agent_type,
            temperature=0.1,
            max_tokens=500
        )
    
    def test_single_llm_call(self, agent_type: str) -> Dict[str, Any]:
        """단일 LLM 호출 테스트"""
        start_time = time.time()
        
        try:
            client = self.client_factory.get_client(agent_type)
            request = self.create_test_request(agent_type)
            response = client.generate_response(request)
            
            end_time = time.time()
            response_time = end_time - start_time
            
            return {
                'agent_type': agent_type,
                'success': True,
                'response_time': response_time,
                'tokens_used': response.tokens_used,
                'cost': response.cost,
                'model_used': response.model_used,
                'error': None
            }
            
        except Exception as e:
            end_time = time.time()
            response_time = end_time - start_time
            
            return {
                'agent_type': agent_type,
                'success': False,
                'response_time': response_time,
                'tokens_used': 0,
                'cost': 0.0,
                'model_used': None,
                'error': str(e)
            }
    
    def test_parallel_analysis_agents(self) -> Dict[str, Any]:
        """병렬 분석 에이전트 동시 호출 테스트 (Phase 2 5a-5d)"""
        parallel_agents = [
            'valuation_analyst',
            'flow_analyst', 
            'risk_analyst',
            'technical_analyst'
        ]
        
        start_time = time.time()
        results = []
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            # 4개 에이전트 동시 실행
            future_to_agent = {
                executor.submit(self.test_single_llm_call, agent): agent 
                for agent in parallel_agents
            }
            
            for future in as_completed(future_to_agent):
                agent = future_to_agent[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    results.append({
                        'agent_type': agent,
                        'success': False,
                        'response_time': 0,
                        'tokens_used': 0,
                        'cost': 0.0,
                        'model_used': None,
                        'error': f"Execution error: {str(e)}"
                    })
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # 결과 집계
        successful_calls = [r for r in results if r['success']]
        failed_calls = [r for r in results if not r['success']]
        
        return {
            'test_type': 'parallel_analysis',
            'total_time': total_time,
            'total_agents': len(parallel_agents),
            'successful_calls': len(successful_calls),
            'failed_calls': len(failed_calls),
            'success_rate': len(successful_calls) / len(parallel_agents),
            'average_response_time': sum(r['response_time'] for r in successful_calls) / len(successful_calls) if successful_calls else 0,
            'total_tokens': sum(r['tokens_used'] for r in results),
            'total_cost': sum(r['cost'] for r in results),
            'individual_results': results
        }
    
    def test_sequential_workflow(self) -> Dict[str, Any]:
        """순차 워크플로우 테스트"""
        sequential_agents = [
            'portfolio_rebalancer',
            'sector_researcher', 
            'ticker_screener',
            'fundamental_fetcher'
        ]
        
        start_time = time.time()
        results = []
        
        # 순차적으로 실행
        for agent in sequential_agents:
            result = self.test_single_llm_call(agent)
            results.append(result)
            
            # 실패한 경우 중단
            if not result['success']:
                break
        
        end_time = time.time()
        total_time = end_time - start_time
        
        successful_calls = [r for r in results if r['success']]
        failed_calls = [r for r in results if not r['success']]
        
        return {
            'test_type': 'sequential_workflow',
            'total_time': total_time,
            'total_agents': len(sequential_agents),
            'completed_agents': len(results),
            'successful_calls': len(successful_calls),
            'failed_calls': len(failed_calls),
            'success_rate': len(successful_calls) / len(results) if results else 0,
            'individual_results': results
        }
    
    def test_cio_decision_making(self) -> Dict[str, Any]:
        """CIO 에이전트 단독 의사결정 테스트"""
        cio_prompt = """
        Based on the following analysis reports, make a final investment decision:
        
        Valuation Analysis: AAPL appears undervalued with P/E of 25 vs industry average of 30
        Flow Analysis: Strong institutional buying detected in tech sector
        Risk Analysis: Portfolio concentration risk is acceptable at current levels
        Technical Analysis: AAPL showing bullish breakout pattern above $150 resistance
        
        Please provide your final investment recommendation.
        """
        
        request = self.create_test_request('cio', cio_prompt)
        result = self.test_single_llm_call('cio')
        
        return {
            'test_type': 'cio_decision',
            'agent_type': 'cio',
            'result': result
        }
    
    def run_comprehensive_test(self) -> Dict[str, Any]:
        """종합 테스트 실행"""
        print("🚀 다중 LLM 워크플로우 종합 테스트 시작")
        
        test_results = {}
        
        # 1. 병렬 분석 에이전트 테스트
        print("📊 병렬 분석 에이전트 테스트 중...")
        test_results['parallel_analysis'] = self.test_parallel_analysis_agents()
        
        # 2. 순차 워크플로우 테스트
        print("🔄 순차 워크플로우 테스트 중...")
        test_results['sequential_workflow'] = self.test_sequential_workflow()
        
        # 3. CIO 의사결정 테스트
        print("👑 CIO 의사결정 테스트 중...")
        test_results['cio_decision'] = self.test_cio_decision_making()
        
        # 전체 결과 요약
        total_calls = 0
        total_successful = 0
        total_time = 0
        total_cost = 0
        
        for test_name, result in test_results.items():
            if test_name in ['parallel_analysis', 'sequential_workflow']:
                total_calls += result.get('total_agents', 0)
                total_successful += result.get('successful_calls', 0)
                total_time += result.get('total_time', 0)
                total_cost += result.get('total_cost', 0)
            elif test_name == 'cio_decision':
                total_calls += 1
                total_successful += 1 if result['result']['success'] else 0
                total_time += result['result']['response_time']
                total_cost += result['result']['cost']
        
        test_results['summary'] = {
            'total_calls': total_calls,
            'total_successful': total_successful,
            'overall_success_rate': total_successful / total_calls if total_calls > 0 else 0,
            'total_time': total_time,
            'total_cost': total_cost,
            'test_passed': total_successful / total_calls >= 0.8 if total_calls > 0 else False  # 80% 성공률 기준
        }
        
        return test_results


# pytest 테스트 케이스들
class TestMultiLLMWorkflow:
    """pytest 기반 테스트 케이스"""
    
    @pytest.fixture
    def tester(self):
        """테스터 인스턴스 생성"""
        return MultiLLMWorkflowTester()
    
    def test_parallel_analysis_agents_success_rate(self, tester):
        """병렬 분석 에이전트 성공률 테스트"""
        result = tester.test_parallel_analysis_agents()
        
        # 80% 이상 성공률 요구
        assert result['success_rate'] >= 0.8, f"Success rate {result['success_rate']} is below 80%"
        
        # 평균 응답 시간 60초 이하 요구
        assert result['average_response_time'] <= 60, f"Average response time {result['average_response_time']} exceeds 60 seconds"
        
        print(f"✅ 병렬 분석 테스트 통과: 성공률 {result['success_rate']:.1%}, 평균 응답시간 {result['average_response_time']:.1f}초")
    
    def test_sequential_workflow_completion(self, tester):
        """순차 워크플로우 완료 테스트"""
        result = tester.test_sequential_workflow()
        
        # 모든 에이전트 성공적 완료 요구
        assert result['success_rate'] >= 0.8, f"Sequential workflow success rate {result['success_rate']} is below 80%"
        
        print(f"✅ 순차 워크플로우 테스트 통과: 성공률 {result['success_rate']:.1%}")
    
    def test_cio_decision_making(self, tester):
        """CIO 의사결정 테스트"""
        result = tester.test_cio_decision_making()
        
        assert result['result']['success'], f"CIO decision making failed: {result['result']['error']}"
        
        print(f"✅ CIO 의사결정 테스트 통과: 응답시간 {result['result']['response_time']:.1f}초")


def main():
    """메인 실행 함수"""
    tester = MultiLLMWorkflowTester()
    results = tester.run_comprehensive_test()
    
    print("\n" + "="*60)
    print("📋 다중 LLM 워크플로우 테스트 결과")
    print("="*60)
    
    # 병렬 분석 결과
    parallel_result = results['parallel_analysis']
    print(f"\n📊 병렬 분석 에이전트 (4개 동시 호출):")
    print(f"   성공률: {parallel_result['success_rate']:.1%} ({parallel_result['successful_calls']}/{parallel_result['total_agents']})")
    print(f"   총 소요시간: {parallel_result['total_time']:.1f}초")
    print(f"   평균 응답시간: {parallel_result['average_response_time']:.1f}초")
    print(f"   총 비용: ${parallel_result['total_cost']:.4f}")
    
    # 순차 워크플로우 결과
    sequential_result = results['sequential_workflow']
    print(f"\n🔄 순차 워크플로우:")
    print(f"   성공률: {sequential_result['success_rate']:.1%} ({sequential_result['successful_calls']}/{sequential_result['completed_agents']})")
    print(f"   총 소요시간: {sequential_result['total_time']:.1f}초")
    
    # CIO 결과
    cio_result = results['cio_decision']['result']
    print(f"\n👑 CIO 의사결정:")
    print(f"   성공: {'✅' if cio_result['success'] else '❌'}")
    print(f"   응답시간: {cio_result['response_time']:.1f}초")
    print(f"   사용 모델: {cio_result['model_used']}")
    
    # 전체 요약
    summary = results['summary']
    print(f"\n📈 전체 요약:")
    print(f"   총 호출 수: {summary['total_calls']}")
    print(f"   전체 성공률: {summary['overall_success_rate']:.1%}")
    print(f"   총 소요시간: {summary['total_time']:.1f}초")
    print(f"   총 비용: ${summary['total_cost']:.4f}")
    print(f"   테스트 통과: {'✅ PASS' if summary['test_passed'] else '❌ FAIL'}")
    
    return results


if __name__ == "__main__":
    main()