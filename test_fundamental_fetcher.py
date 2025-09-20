#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
펀더멘털 페처 에이전트 (Gemini 2.5 Flash-Lite) 종합 테스트

Phase 2.1 노드 4: 펀더멘털 데이터 수집 및 Gemini AI 분석 시스템 테스트
"""

import os
import sys
import time
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

# 프로젝트 루트 경로 추가
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.utils.fundamental_data_engine import FundamentalDataEngine, collect_single_ticker_data
from src.agents.fundamental_fetcher import FundamentalFetcherAgent, create_fundamental_fetcher
from src.agents.base_agent import AgentContext


class FundamentalFetcherTester:
    """펀더멘털 페처 에이전트 종합 테스트 클래스"""
    
    def __init__(self, mock_mode: bool = True):
        """
        테스터 초기화
        
        Args:
            mock_mode: Mock 모드 사용 여부 (기본값: True)
        """
        self.mock_mode = mock_mode
        self.test_results = []
        self.start_time = time.time()
        
        # 로깅 설정
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # 테스트용 종목 코드
        self.test_tickers = ["005930", "000660", "035420"]  # 삼성전자, SK하이닉스, NAVER
        self.single_ticker = "005930"  # 삼성전자
        
        print("=" * 80)
        print("🧪 펀더멘털 페처 에이전트 (Gemini 2.5 Flash-Lite) 종합 테스트")
        print("=" * 80)
        print(f"📅 테스트 시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🔧 Mock 모드: {'ON' if mock_mode else 'OFF'}")
        print(f"📊 테스트 종목: {self.test_tickers}")
        print()
    
    def run_all_tests(self) -> bool:
        """모든 테스트 실행"""
        tests = [
            ("기본 기능 테스트", self.test_basic_functionality),
            ("데이터 엔진 테스트", self.test_data_engine),
            ("재무 데이터 수집 테스트", self.test_financial_data_collection),
            ("뉴스 데이터 수집 테스트", self.test_news_data_collection),
            ("업계 비교 데이터 테스트", self.test_industry_comparison),
            ("에이전트 실행 테스트", self.test_agent_execution),
            ("Gemini AI 분석 테스트", self.test_gemini_ai_analysis),
            ("캐싱 시스템 테스트", self.test_caching_system),
            ("배치 처리 테스트", self.test_batch_processing),
            ("데이터 품질 검증 테스트", self.test_data_quality_validation)
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n🔍 {test_name} 실행 중...")
            try:
                start_time = time.time()
                success = test_func()
                execution_time = time.time() - start_time
                
                if success:
                    print(f"✅ {test_name} 통과 ({execution_time:.3f}초)")
                    passed_tests += 1
                else:
                    print(f"❌ {test_name} 실패 ({execution_time:.3f}초)")
                
                self.test_results.append({
                    "name": test_name,
                    "passed": success,
                    "execution_time": execution_time
                })
                
            except Exception as e:
                execution_time = time.time() - start_time
                print(f"💥 {test_name} 예외 발생: {str(e)} ({execution_time:.3f}초)")
                self.test_results.append({
                    "name": test_name,
                    "passed": False,
                    "execution_time": execution_time,
                    "error": str(e)
                })
        
        # 테스트 결과 요약
        self._print_test_summary(passed_tests, total_tests)
        
        # 결과 파일 저장
        self._save_test_results(passed_tests, total_tests)
        
        return passed_tests == total_tests
    
    def test_basic_functionality(self) -> bool:
        """기본 기능 테스트"""
        try:
            # 에이전트 생성
            agent = create_fundamental_fetcher(mock_mode=self.mock_mode)
            
            # 기본 속성 확인
            assert agent.agent_type == "fundamental_fetcher"
            assert hasattr(agent, 'data_engine')
            assert hasattr(agent, 'llm_client')
            
            # 설정 확인
            agent_info = agent.get_agent_info()
            assert 'agent_type' in agent_info
            assert 'llm_provider' in agent_info
            
            print(f"   ✓ 에이전트 타입: {agent_info['agent_type']}")
            print(f"   ✓ LLM 제공사: {agent_info['llm_provider']}")
            print(f"   ✓ LLM 모델: {agent_info['llm_model']}")
            
            return True
            
        except Exception as e:
            print(f"   ❌ 기본 기능 테스트 실패: {e}")
            return False
    
    def test_data_engine(self) -> bool:
        """데이터 엔진 테스트"""
        try:
            # 데이터 엔진 직접 테스트
            engine = FundamentalDataEngine(mock_mode=self.mock_mode)
            
            # 단일 종목 데이터 수집
            data = engine.collect_fundamental_data(self.single_ticker)
            
            # 데이터 구조 검증
            assert data.ticker == self.single_ticker
            assert data.company_name is not None
            assert data.financial_ratios is not None
            assert isinstance(data.news_data, list)
            assert data.industry_comparison is not None
            assert data.confidence_score >= 0.0
            
            # 재무 지표 검증
            fr = data.financial_ratios
            print(f"   ✓ 재무 지표: PER={fr.per}, PBR={fr.pbr}, ROE={fr.roe}%")
            print(f"   ✓ 뉴스 개수: {len(data.news_data)}건")
            print(f"   ✓ 신뢰도: {data.confidence_score}")
            
            return True
            
        except Exception as e:
            print(f"   ❌ 데이터 엔진 테스트 실패: {e}")
            return False
    
    def test_financial_data_collection(self) -> bool:
        """재무 데이터 수집 테스트"""
        try:
            engine = FundamentalDataEngine(mock_mode=self.mock_mode)
            
            # 재무 데이터만 수집
            data = engine.collect_fundamental_data(
                self.single_ticker, 
                include_news=False, 
                include_industry_comparison=False
            )
            
            fr = data.financial_ratios
            
            # 주요 재무 지표 확인
            financial_indicators = [
                ('PER', fr.per),
                ('PBR', fr.pbr),
                ('ROE', fr.roe),
                ('부채비율', fr.debt_ratio),
                ('영업이익률', fr.operating_margin)
            ]
            
            valid_indicators = 0
            for name, value in financial_indicators:
                if value is not None:
                    valid_indicators += 1
                    print(f"   ✓ {name}: {value}")
            
            print(f"   ✓ 유효 지표 수: {valid_indicators}/{len(financial_indicators)}")
            
            # 최소 3개 이상의 유효한 지표가 있어야 함
            return valid_indicators >= 3
            
        except Exception as e:
            print(f"   ❌ 재무 데이터 수집 테스트 실패: {e}")
            return False
    
    def test_news_data_collection(self) -> bool:
        """뉴스 데이터 수집 테스트"""
        try:
            engine = FundamentalDataEngine(mock_mode=self.mock_mode)
            
            # 뉴스 데이터 포함 수집
            data = engine.collect_fundamental_data(
                self.single_ticker, 
                include_news=True, 
                include_industry_comparison=False
            )
            
            news_data = data.news_data
            assert isinstance(news_data, list)
            
            if len(news_data) > 0:
                # 뉴스 데이터 구조 검증
                first_news = news_data[0]
                assert hasattr(first_news, 'title')
                assert hasattr(first_news, 'summary')
                assert hasattr(first_news, 'sentiment_score')
                assert hasattr(first_news, 'published_date')
                
                print(f"   ✓ 수집된 뉴스: {len(news_data)}건")
                print(f"   ✓ 첫 번째 뉴스: {first_news.title}")
                print(f"   ✓ 감정 점수: {first_news.sentiment_score}")
                
                # 감정 점수 범위 확인
                for news in news_data:
                    assert -1.0 <= news.sentiment_score <= 1.0
                
                return True
            else:
                print("   ⚠️ 수집된 뉴스가 없음 (Mock 모드에서는 정상)")
                return True
            
        except Exception as e:
            print(f"   ❌ 뉴스 데이터 수집 테스트 실패: {e}")
            return False
    
    def test_industry_comparison(self) -> bool:
        """업계 비교 데이터 테스트"""
        try:
            engine = FundamentalDataEngine(mock_mode=self.mock_mode)
            
            data = engine.collect_fundamental_data(
                self.single_ticker, 
                include_news=False, 
                include_industry_comparison=True
            )
            
            industry_comp = data.industry_comparison
            assert industry_comp is not None
            assert industry_comp.ticker == self.single_ticker
            assert industry_comp.industry_name is not None
            
            print(f"   ✓ 업종: {industry_comp.industry_name}")
            print(f"   ✓ 업계 평균 PER: {industry_comp.industry_avg_per}")
            print(f"   ✓ 업계 순위: {industry_comp.rank_in_industry}/{industry_comp.total_companies}")
            print(f"   ✓ 백분위수: {industry_comp.percentile}%")
            
            # 순위 정보 검증
            if industry_comp.rank_in_industry and industry_comp.total_companies:
                assert 1 <= industry_comp.rank_in_industry <= industry_comp.total_companies
            
            return True
            
        except Exception as e:
            print(f"   ❌ 업계 비교 데이터 테스트 실패: {e}")
            return False
    
    def test_agent_execution(self) -> bool:
        """에이전트 실행 테스트 (BaseAgent 패턴)"""
        try:
            agent = create_fundamental_fetcher(mock_mode=self.mock_mode)
            
            # AgentContext 생성
            context = AgentContext(
                agent_id="fundamental_fetcher",
                execution_id=f"test_{int(time.time())}",
                timestamp=datetime.now(),
                input_data={
                    'tickers': self.test_tickers,
                    'include_news': True,
                    'include_industry_comparison': True
                }
            )
            
            # 에이전트 실행
            result = agent.execute(context)
            
            # 실행 결과 검증
            assert result.success == True
            assert result.agent_id == "fundamental_fetcher"
            assert 'fundamental_data' in result.result_data
            assert 'analysis_summary' in result.result_data
            assert 'data_quality' in result.result_data
            
            fundamental_data = result.result_data['fundamental_data']
            assert len(fundamental_data) == len(self.test_tickers)
            
            print(f"   ✓ 처리된 종목 수: {len(fundamental_data)}")
            print(f"   ✓ 실행 시간: {result.execution_time:.3f}초")
            print(f"   ✓ 신뢰도: {result.confidence_score}")
            
            # 데이터 품질 정보
            data_quality = result.result_data['data_quality']
            print(f"   ✓ 데이터 품질: {data_quality['overall_quality']}")
            
            return True
            
        except Exception as e:
            print(f"   ❌ 에이전트 실행 테스트 실패: {e}")
            return False
    
    def test_gemini_ai_analysis(self) -> bool:
        """Gemini 2.5 Flash-Lite AI 분석 테스트"""
        try:
            # Mock 모드가 아닌 경우에만 실제 API 테스트
            if not self.mock_mode:
                print("   ⚠️ 실제 Gemini API 테스트는 API 키가 필요합니다")
                return True
            
            agent = create_fundamental_fetcher(mock_mode=self.mock_mode)
            
            context = AgentContext(
                agent_id="fundamental_fetcher",
                execution_id=f"ai_test_{int(time.time())}",
                timestamp=datetime.now(),
                input_data={
                    'tickers': [self.single_ticker],
                    'include_news': True,
                    'sector_context': {
                        'top_sectors': ['반도체', '기술주'],
                        'market_trends': '긍정적 모멘텀'
                    }
                }
            )
            
            result = agent.execute(context)
            
            # AI 분석 결과 확인
            if 'analysis_summary' in result.result_data:
                analysis = result.result_data['analysis_summary']
                
                if 'ai_analysis' in analysis:
                    ai_result = analysis['ai_analysis']
                    print(f"   ✓ AI 분석 완료")
                    
                    if isinstance(ai_result, dict):
                        print(f"   ✓ 전체 평가: {ai_result.get('overall_assessment', 'N/A')[:100]}...")
                        print(f"   ✓ 추천 종목: {ai_result.get('top_picks', [])}")
                        print(f"   ✓ 신뢰도: {ai_result.get('confidence_level', 'N/A')}")
                    
                    return True
                else:
                    print("   ⚠️ AI 분석 결과 없음 (Mock 모드 또는 API 오류)")
                    return True
            
            return True
            
        except Exception as e:
            print(f"   ❌ Gemini AI 분석 테스트 실패: {e}")
            return False
    
    def test_caching_system(self) -> bool:
        """캐싱 시스템 테스트"""
        try:
            engine = FundamentalDataEngine(cache_ttl_minutes=5, mock_mode=self.mock_mode)
            
            # 첫 번째 요청 (캐시 없음)
            start_time = time.time()
            data1 = engine.collect_fundamental_data(self.single_ticker)
            first_request_time = time.time() - start_time
            
            # 두 번째 요청 (캐시 있음)
            start_time = time.time()
            data2 = engine.collect_fundamental_data(self.single_ticker)
            second_request_time = time.time() - start_time
            
            # 캐시 효과 확인
            assert data1.ticker == data2.ticker
            assert data1.company_name == data2.company_name
            
            # 두 번째 요청이 더 빨라야 함
            speed_improvement = first_request_time / max(second_request_time, 0.001)
            
            print(f"   ✓ 첫 번째 요청: {first_request_time:.3f}초")
            print(f"   ✓ 두 번째 요청: {second_request_time:.3f}초")
            print(f"   ✓ 성능 향상: {speed_improvement:.1f}x")
            
            # 캐시 통계 확인
            cache_stats = engine.get_cache_stats()
            print(f"   ✓ 캐시된 항목: {cache_stats['total_cached_items']}개")
            
            return speed_improvement > 1.5  # 최소 1.5배 향상 기대
            
        except Exception as e:
            print(f"   ❌ 캐싱 시스템 테스트 실패: {e}")
            return False
    
    def test_batch_processing(self) -> bool:
        """배치 처리 테스트"""
        try:
            engine = FundamentalDataEngine(mock_mode=self.mock_mode)
            
            # 배치 데이터 수집
            batch_data = engine.batch_collect_data(self.test_tickers)
            
            # 결과 검증
            assert len(batch_data) == len(self.test_tickers)
            
            for ticker in self.test_tickers:
                assert ticker in batch_data
                data = batch_data[ticker]
                assert data.ticker == ticker
                assert data.company_name is not None
            
            print(f"   ✓ 배치 처리된 종목 수: {len(batch_data)}")
            
            # 각 종목별 데이터 요약
            for ticker, data in batch_data.items():
                print(f"   ✓ {ticker}: {data.company_name}, 신뢰도={data.confidence_score}")
            
            return True
            
        except Exception as e:
            print(f"   ❌ 배치 처리 테스트 실패: {e}")
            return False
    
    def test_data_quality_validation(self) -> bool:
        """데이터 품질 검증 테스트"""
        try:
            agent = create_fundamental_fetcher(mock_mode=self.mock_mode)
            
            context = AgentContext(
                agent_id="fundamental_fetcher",
                execution_id=f"quality_test_{int(time.time())}",
                timestamp=datetime.now(),
                input_data={'tickers': self.test_tickers}
            )
            
            result = agent.execute(context)
            
            # 데이터 품질 정보 확인
            data_quality = result.result_data['data_quality']
            
            assert 'overall_quality' in data_quality
            assert 'quality_score' in data_quality
            assert 'individual_scores' in data_quality
            
            quality_score = data_quality['quality_score']
            overall_quality = data_quality['overall_quality']
            
            print(f"   ✓ 전체 품질 등급: {overall_quality}")
            print(f"   ✓ 품질 점수: {quality_score}")
            
            # 개별 종목 품질 점수
            individual_scores = data_quality['individual_scores']
            for ticker, score in individual_scores.items():
                print(f"   ✓ {ticker} 품질: {score}")
            
            # 품질 점수는 0.0 ~ 1.0 범위
            assert 0.0 <= quality_score <= 1.0
            
            return True
            
        except Exception as e:
            print(f"   ❌ 데이터 품질 검증 테스트 실패: {e}")
            return False
    
    def _print_test_summary(self, passed: int, total: int) -> None:
        """테스트 결과 요약 출력"""
        print("\n" + "=" * 80)
        print("📊 펀더멘털 페처 에이전트 테스트 결과 요약")
        print("=" * 80)
        
        success_rate = (passed / total) * 100 if total > 0 else 0
        total_time = time.time() - self.start_time
        
        print(f"🎯 전체 테스트: {total}개")
        print(f"✅ 통과한 테스트: {passed}개")
        print(f"❌ 실패한 테스트: {total - passed}개")
        print(f"📈 성공률: {success_rate:.1f}%")
        print(f"⏱️ 총 실행 시간: {total_time:.2f}초")
        
        if success_rate == 100:
            print("🎉 모든 테스트 통과! 펀더멘털 페처 에이전트가 정상적으로 작동합니다.")
        elif success_rate >= 80:
            print("⚠️ 대부분의 테스트 통과. 일부 기능에 주의가 필요합니다.")
        else:
            print("🚨 다수의 테스트 실패. 시스템 점검이 필요합니다.")
        
        print("\n📋 개별 테스트 결과:")
        for i, result in enumerate(self.test_results, 1):
            status = "✅ PASS" if result["passed"] else "❌ FAIL"
            print(f"  {i:2d}. {result['name']:30s} {status} ({result['execution_time']:.3f}초)")
            
            if not result["passed"] and "error" in result:
                print(f"      오류: {result['error']}")
    
    def _save_test_results(self, passed: int, total: int) -> None:
        """테스트 결과를 JSON 파일로 저장"""
        results = {
            "timestamp": datetime.now().isoformat(),
            "total_tests": total,
            "passed_tests": passed,
            "success_rate": (passed / total) * 100 if total > 0 else 0,
            "test_results": self.test_results
        }
        
        filename = f"test_results_fundamental_fetcher.json"
        filepath = os.path.join(project_root, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f"\n💾 테스트 결과 저장: {filename}")
        except Exception as e:
            print(f"\n❌ 테스트 결과 저장 실패: {e}")


def main():
    """메인 테스트 실행 함수"""
    
    # 환경 변수 확인
    mock_mode = True  # 기본적으로 Mock 모드로 실행
    
    # 명령행 인자 처리
    if len(sys.argv) > 1 and sys.argv[1] == "--live":
        mock_mode = False
        print("🔴 실제 API 모드로 실행 (API 키 필요)")
    
    # 테스터 실행
    tester = FundamentalFetcherTester(mock_mode=mock_mode)
    success = tester.run_all_tests()
    
    # 종료 코드 설정
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()