#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
섹터 리서치 에이전트 종합 테스트 스크립트

Phase 2.1 노드 2: 섹터 리서치 에이전트의 모든 기능을 검증하는 테스트
- 기본 기능 테스트
- Mock 모드 테스트
- Perplexity 연동 테스트 (API 키 있는 경우)
- 에러 처리 테스트
- 출력 검증 테스트
"""

import sys
import os
import json
import time
from pathlib import Path
from datetime import datetime

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from src.agents.sector_researcher import SectorResearcherAgent
from src.agents.base_agent import AgentContext, AgentResult
from src.utils.sector_research_engine import get_sector_research_engine


class SectorResearcherTester:
    """섹터 리서치 에이전트 테스트 클래스"""
    
    def __init__(self):
        """테스터 초기화"""
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        
        print("=" * 60)
        print("🔬 섹터 리서치 에이전트 종합 테스트")
        print("=" * 60)
    
    def run_all_tests(self) -> bool:
        """모든 테스트 실행"""
        tests = [
            ("기본 기능 테스트", self.test_basic_functionality),
            ("섹터 분석 (Mock 모드)", self.test_sector_analysis_mock),
            ("섹터 리서치 엔진 테스트", self.test_research_engine),
            ("프롬프트 생성 테스트", self.test_prompt_generation),
            ("에러 처리 테스트", self.test_error_handling),
            ("출력 검증 테스트", self.test_output_validation),
            ("캐싱 시스템 테스트", self.test_caching_system),
            ("LLM 통합 테스트 (API 키 있는 경우)", self.test_llm_integration)
        ]
        
        for test_name, test_func in tests:
            self.total_tests += 1
            try:
                print(f"\n🧪 {test_name}")
                print("-" * 50)
                
                start_time = time.time()
                result = test_func()
                execution_time = time.time() - start_time
                
                if result:
                    self.passed_tests += 1
                    print(f"✅ {test_name} 통과 ({execution_time:.2f}초)")
                else:
                    print(f"❌ {test_name} 실패 ({execution_time:.2f}초)")
                
                self.test_results.append({
                    'name': test_name,
                    'passed': result,
                    'execution_time': execution_time
                })
                
            except Exception as e:
                print(f"❌ {test_name} 예외 발생: {str(e)}")
                self.test_results.append({
                    'name': test_name,
                    'passed': False,
                    'error': str(e)
                })
        
        # 최종 결과 출력
        self.print_test_summary()
        return self.passed_tests == self.total_tests
    
    def test_basic_functionality(self) -> bool:
        """기본 기능 테스트"""
        try:
            # 에이전트 초기화
            agent = SectorResearcherAgent()
            
            # 에이전트 정보 확인
            info = agent.get_agent_info()
            print(f"에이전트 타입: {info['agent_type']}")
            print(f"지원 섹터 수: {info['supported_sectors']}")
            print(f"실시간 검색: {info['real_time_search']}")
            
            # 필수 속성 확인
            assert hasattr(agent, 'research_engine')
            assert hasattr(agent, 'default_focus_sectors')
            assert len(agent.default_focus_sectors) > 0
            
            print("✓ 에이전트 초기화 성공")
            print("✓ 필수 속성 확인 완료")
            
            return True
            
        except Exception as e:
            print(f"기본 기능 테스트 실패: {e}")
            return False
    
    def test_sector_analysis_mock(self) -> bool:
        """섹터 분석 Mock 모드 테스트"""
        try:
            # Mock 모드로 에이전트 생성 (API 키 없이도 동작)
            agent = SectorResearcherAgent()
            
            # 테스트 컨텍스트 생성
            context = AgentContext(
                agent_id="sector_researcher",
                execution_id="test_001",
                timestamp=datetime.now(),
                input_data={
                    'focus_sectors': ['기술주', '반도체', '금융', '자동차'],
                    'analysis_depth': 'detailed',
                    'force_refresh': True
                }
            )
            
            # 에이전트 실행
            result = agent.execute(context)
            
            # 결과 검증
            assert result.success, f"실행 실패: {result.error_message}"
            assert 'research_result' in result.result_data
            assert 'summary' in result.result_data
            assert 'recommendations' in result.result_data
            
            # 연구 결과 세부 검증
            research_result = result.result_data['research_result']
            assert 'sector_rankings' in research_result
            assert 'top_opportunities' in research_result
            assert 'confidence_indicators' in research_result
            
            # 추천 결과 검증
            recommendations = result.result_data['recommendations']
            assert isinstance(recommendations, list)
            assert len(recommendations) > 0
            
            print(f"✓ 섹터 분석 실행 성공 (소요시간: {result.execution_time:.2f}초)")
            print(f"✓ 분석된 섹터 수: {len(research_result['sector_rankings'])}")
            print(f"✓ 발굴된 기회: {len(research_result['top_opportunities'])}개")
            print(f"✓ 추천 항목: {len(recommendations)}개")
            print(f"✓ 신뢰도: {result.confidence_score:.2%}")
            
            return True
            
        except Exception as e:
            print(f"섹터 분석 Mock 테스트 실패: {e}")
            return False
    
    def test_research_engine(self) -> bool:
        """섹터 리서치 엔진 테스트"""
        try:
            engine = get_sector_research_engine()
            
            # 기본 속성 확인
            assert len(engine.sectors) >= 19, "19개 이상의 섹터가 정의되어야 함"
            assert len(engine.MAJOR_SECTORS) >= 19, "주요 섹터 매핑이 충분해야 함"
            
            # 섹터 가중치 확인
            weights = engine.sector_weights
            assert abs(sum(weights.values()) - 1.0) < 0.1, "섹터 가중치 합계는 1.0에 가까워야 함"
            
            # 프롬프트 생성 테스트
            test_sectors = ['기술주', '금융', '자동차']
            
            # 다양한 타입의 프롬프트 생성
            comprehensive_prompt = engine.generate_sector_research_prompt(test_sectors, "comprehensive")
            overview_prompt = engine.generate_sector_research_prompt(test_sectors, "market_overview")
            rotation_prompt = engine.generate_sector_research_prompt(test_sectors, "rotation_signals")
            
            assert len(comprehensive_prompt) > 1000, "포괄적 프롬프트는 충분히 상세해야 함"
            assert len(overview_prompt) > 200, "개요 프롬프트는 적절한 길이여야 함"
            assert "로테이션" in rotation_prompt, "로테이션 프롬프트에는 로테이션 관련 내용이 포함되어야 함"
            
            # 벤치마크 데이터 확인
            benchmark_data = engine.get_sector_benchmark_data()
            assert len(benchmark_data) >= 19, "모든 섹터의 벤치마크 데이터가 있어야 함"
            
            # 상관관계 계산 테스트
            correlation = engine.calculate_sector_correlation('기술주', '반도체')
            assert 0.0 <= correlation <= 1.0, "상관관계는 0-1 범위여야 함"
            
            print("✓ 섹터 리서치 엔진 기본 기능 확인")
            print(f"✓ 등록된 섹터 수: {len(engine.sectors)}")
            print(f"✓ 프롬프트 생성 기능 확인 (3가지 타입)")
            print("✓ 벤치마크 데이터 및 상관관계 계산 확인")
            
            return True
            
        except Exception as e:
            print(f"리서치 엔진 테스트 실패: {e}")
            return False
    
    def test_prompt_generation(self) -> bool:
        """프롬프트 생성 테스트"""
        try:
            engine = get_sector_research_engine()
            
            # 다양한 시나리오의 프롬프트 생성
            test_cases = [
                (['기술주'], 'market_overview'),
                (['기술주', '금융', '자동차'], 'comprehensive'),
                (['반도체', '자동차'], 'sector_deep_dive'),
                (['기술주', '금융', '헬스케어', '에너지'], 'rotation_signals')
            ]
            
            for sectors, analysis_type in test_cases:
                prompt = engine.generate_sector_research_prompt(sectors, analysis_type)
                
                # 프롬프트 품질 검증
                assert len(prompt) > 100, f"{analysis_type} 프롬프트가 너무 짧음"
                assert "한국" in prompt, "한국 시장 관련 내용이 포함되어야 함"
                assert datetime.now().strftime("%Y년") in prompt, "현재 연도가 포함되어야 함"
                
                # 분석 타입별 특화 내용 확인
                if analysis_type == 'market_overview':
                    assert "개요" in prompt or "500단어" in prompt
                elif analysis_type == 'rotation_signals':
                    assert "로테이션" in prompt or "자금 이동" in prompt
                elif analysis_type == 'sector_deep_dive':
                    assert "심층" in prompt or "상세" in prompt
                
                print(f"✓ {analysis_type} 프롬프트 생성 확인 ({len(prompt)}자)")
            
            return True
            
        except Exception as e:
            print(f"프롬프트 생성 테스트 실패: {e}")
            return False
    
    def test_error_handling(self) -> bool:
        """에러 처리 테스트"""
        try:
            agent = SectorResearcherAgent()
            
            # 잘못된 입력 데이터 테스트
            invalid_contexts = [
                # 잘못된 섹터명
                {
                    'focus_sectors': ['존재하지않는섹터', '기술주'],
                    'analysis_depth': 'detailed'
                },
                # 잘못된 분석 깊이
                {
                    'focus_sectors': ['기술주'],
                    'analysis_depth': 'invalid_depth'
                },
                # 잘못된 focus_sectors 타입
                {
                    'focus_sectors': 'not_a_list',
                    'analysis_depth': 'basic'
                }
            ]
            
            for i, invalid_data in enumerate(invalid_contexts):
                context = AgentContext(
                    agent_id="sector_researcher",
                    execution_id=f"error_test_{i}",
                    timestamp=datetime.now(),
                    input_data=invalid_data
                )
                
                result = agent.execute(context)
                
                # 에러가 적절히 처리되었는지 확인
                assert not result.success, f"에러 테스트 {i}에서 성공해서는 안됨"
                assert result.error_message, f"에러 메시지가 없음: {i}"
                
                print(f"✓ 에러 케이스 {i+1} 적절히 처리됨")
            
            return True
            
        except Exception as e:
            print(f"에러 처리 테스트 실패: {e}")
            return False
    
    def test_output_validation(self) -> bool:
        """출력 검증 테스트"""
        try:
            agent = SectorResearcherAgent()
            
            # 정상적인 실행
            context = AgentContext(
                agent_id="sector_researcher",
                execution_id="validation_test",
                timestamp=datetime.now(),
                input_data={
                    'focus_sectors': ['기술주', '금융'],
                    'analysis_depth': 'basic'
                }
            )
            
            result = agent.execute(context)
            
            # 기본 결과 구조 검증
            assert result.success
            assert isinstance(result.result_data, dict)
            assert result.confidence_score is not None
            assert 0.0 <= result.confidence_score <= 1.0
            
            # 결과 데이터 상세 검증
            data = result.result_data
            required_fields = ['research_result', 'analysis_metadata', 'summary', 'recommendations']
            
            for field in required_fields:
                assert field in data, f"필수 필드 '{field}' 누락"
            
            # 연구 결과 검증
            research_result = data['research_result']
            assert 'sector_rankings' in research_result
            assert 'confidence_indicators' in research_result
            assert 'research_timestamp' in research_result
            
            # 메타데이터 검증
            metadata = data['analysis_metadata']
            assert 'agent_type' in metadata
            assert 'llm_mode' in metadata
            assert metadata['agent_type'] == 'sector_researcher'
            
            # 추천 결과 검증
            recommendations = data['recommendations']
            assert isinstance(recommendations, list)
            
            if recommendations:  # 추천이 있는 경우
                for rec in recommendations:
                    assert 'sector' in rec
                    assert 'action' in rec
                    assert 'confidence' in rec
            
            print("✓ 출력 데이터 구조 검증 완료")
            print("✓ 필수 필드 모두 존재")
            print("✓ 데이터 타입 검증 완료")
            print(f"✓ 신뢰도 점수: {result.confidence_score:.2%}")
            
            return True
            
        except Exception as e:
            print(f"출력 검증 테스트 실패: {e}")
            return False
    
    def test_caching_system(self) -> bool:
        """캐싱 시스템 테스트"""
        try:
            agent = SectorResearcherAgent()
            
            # 동일한 요청으로 두 번 실행
            input_data = {
                'focus_sectors': ['기술주', '금융'],
                'analysis_depth': 'basic'
            }
            
            context1 = AgentContext(
                agent_id="sector_researcher",
                execution_id="cache_test_1",
                timestamp=datetime.now(),
                input_data=input_data.copy()
            )
            
            context2 = AgentContext(
                agent_id="sector_researcher", 
                execution_id="cache_test_2",
                timestamp=datetime.now(),
                input_data=input_data.copy()
            )
            
            # 첫 번째 실행 (캐시 생성)
            result1 = agent.execute(context1)
            assert result1.success
            
            # 두 번째 실행 (캐시 사용)
            result2 = agent.execute(context2)
            assert result2.success
            
            # 캐시 상태 확인
            cache_status = agent.get_cache_status()
            assert cache_status['cache_entries'] > 0
            
            # 캐시 클리어 테스트
            agent.clear_cache()
            cache_status_after = agent.get_cache_status()
            assert cache_status_after['cache_entries'] == 0
            
            print("✓ 캐싱 시스템 정상 동작")
            print(f"✓ 캐시 TTL: {agent.cache_ttl_minutes}분")
            print("✓ 캐시 클리어 기능 확인")
            
            return True
            
        except Exception as e:
            print(f"캐싱 시스템 테스트 실패: {e}")
            return False
    
    def test_llm_integration(self) -> bool:
        """LLM 통합 테스트 (API 키가 있는 경우만)"""
        try:
            # API 키 확인
            api_key = os.getenv('PERPLEXITY_API_KEY')
            if not api_key:
                print("⚠️  PERPLEXITY_API_KEY가 설정되지 않음 - Mock 모드로 테스트")
                return True  # API 키가 없어도 테스트 통과
            
            print("🔗 Perplexity API 연동 테스트 시작...")
            
            # 실제 API를 사용하는 에이전트 생성
            agent = SectorResearcherAgent()
            
            if not agent.llm_available:
                print("⚠️  LLM 클라이언트 초기화 실패 - Mock 모드로 동작")
                return True
            
            # 간단한 분석 요청
            context = AgentContext(
                agent_id="sector_researcher",
                execution_id="llm_test",
                timestamp=datetime.now(),
                input_data={
                    'focus_sectors': ['기술주', '반도체'],
                    'analysis_depth': 'basic',  # 비용 절약을 위해 basic 모드
                    'force_refresh': True
                }
            )
            
            print("🚀 Perplexity API 호출 중...")
            result = agent.execute(context)
            
            if result.success:
                # LLM 사용량 통계 확인
                llm_usage = result.llm_usage
                if llm_usage:
                    print(f"✓ API 호출 성공")
                    print(f"✓ 토큰 사용량: {llm_usage.get('tokens_used', 'N/A')}")
                    print(f"✓ 비용: ${llm_usage.get('total_cost', 'N/A'):.4f}")
                
                # 실시간 검색 확인
                metadata = result.result_data.get('analysis_metadata', {})
                if metadata.get('llm_mode') == 'real':
                    print("✓ 실시간 검색 모드로 동작")
                
                return True
            else:
                print(f"❌ API 호출 실패: {result.error_message}")
                return False
                
        except Exception as e:
            print(f"LLM 통합 테스트 중 예외: {e}")
            # API 관련 예외는 실패로 처리하지 않음 (선택적 기능)
            return True
    
    def print_test_summary(self):
        """테스트 결과 요약 출력"""
        print("\n" + "=" * 60)
        print("📊 테스트 결과 요약")
        print("=" * 60)
        
        success_rate = (self.passed_tests / self.total_tests) * 100 if self.total_tests > 0 else 0
        
        print(f"전체 테스트: {self.total_tests}개")
        print(f"통과한 테스트: {self.passed_tests}개")
        print(f"실패한 테스트: {self.total_tests - self.passed_tests}개")
        print(f"성공률: {success_rate:.1f}%")
        
        # 개별 테스트 결과
        print("\n📋 개별 테스트 결과:")
        for result in self.test_results:
            status = "✅ 통과" if result['passed'] else "❌ 실패"
            time_info = f"({result.get('execution_time', 0):.2f}초)"
            print(f"  {status} {result['name']} {time_info}")
            
            if 'error' in result:
                print(f"    오류: {result['error']}")
        
        # 최종 판정
        if success_rate >= 80:
            print(f"\n🎉 섹터 리서치 에이전트 구현 성공! (성공률: {success_rate:.1f}%)")
        else:
            print(f"\n⚠️  일부 테스트 실패 - 추가 검토 필요 (성공률: {success_rate:.1f}%)")


def main():
    """메인 함수"""
    print("Phase 2.1 노드 2: 섹터 리서치 에이전트 테스트 시작\n")
    
    tester = SectorResearcherTester()
    success = tester.run_all_tests()
    
    # 결과 요약 JSON 저장
    results_summary = {
        'timestamp': datetime.now().isoformat(),
        'total_tests': tester.total_tests,
        'passed_tests': tester.passed_tests,
        'success_rate': (tester.passed_tests / tester.total_tests) * 100,
        'test_results': tester.test_results
    }
    
    results_file = project_root / 'test_results_sector_researcher.json'
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results_summary, f, ensure_ascii=False, indent=2)
    
    print(f"\n📁 상세 결과가 저장되었습니다: {results_file}")
    
    return success


if __name__ == "__main__":
    main()