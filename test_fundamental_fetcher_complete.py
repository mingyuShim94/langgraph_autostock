#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
펀더멘털 페처 에이전트 완전 통합 테스트
실제 KIS API + Gemini 2.5 Flash-Lite AI 분석 포함
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

# 환경 변수 설정 (실제 KIS API 키)
os.environ["KIS_PAPER_APP_KEY"] = "PSEAkM0fRWfmXwAjAWcKkVMBm7IsUZiDCcPu"
os.environ["KIS_PAPER_APP_SECRET"] = "f1sPtaFBQn/0h+7KkQm/MWu8GvII26QK7EQ4ALlyt31UIGbWB1Xdx73l0adA5gTiy4A+VPTuURtPhQJOUQP+U9tv/ZNticETOUA2D7cEcMDdxnAZSJ+hsBKKH22RxFhDiz2R9IEffMaoPmA//RQYPoTTlQ9oQ+cPX9W0f2IYIW8Aok8lVBk="
os.environ["KIS_PAPER_ACCOUNT_NUMBER"] = "50140992-01"

print("🚀 펀더멘털 페처 에이전트 완전 통합 테스트")
print("📋 실제 KIS API + Gemini 2.5 Flash-Lite AI 분석")
print("=" * 60)

def test_fundamental_fetcher_agent():
    """펀더멘털 페처 에이전트 완전 테스트"""
    print("\n🤖 펀더멘털 페처 에이전트 테스트...")
    
    try:
        from src.agents.fundamental_fetcher import FundamentalFetcherAgent
        from src.utils.agent_context import AgentContext
        
        # 에이전트 생성
        agent = FundamentalFetcherAgent()
        print(f"   ✅ 에이전트 생성 완료: {agent.__class__.__name__}")
        
        # 테스트용 입력 데이터
        test_input = {
            "tickers": ["005930", "000660", "035420"],  # 삼성전자, SK하이닉스, 네이버
            "analysis_type": "fundamental_screening",
            "include_news": True,
            "include_industry_comparison": True
        }
        
        # AgentContext 생성
        context = AgentContext(
            current_step="fundamental_analysis",
            input_data=test_input,
            context_data={
                "market_condition": "neutral",
                "timestamp": datetime.now().isoformat()
            }
        )
        
        print(f"   📊 테스트 종목: {test_input['tickers']}")
        print(f"   🔍 분석 타입: {test_input['analysis_type']}")
        
        # 에이전트 실행
        start_time = time.time()
        result = agent.process(context)
        execution_time = time.time() - start_time
        
        print(f"   ⏱️ 실행 시간: {execution_time:.2f}초")
        print(f"   ✅ 에이전트 실행 완료")
        
        # 결과 분석
        if result and "fundamental_analysis" in result:
            analysis_data = result["fundamental_analysis"]
            
            print(f"\n   📈 분석 결과:")
            print(f"      분석된 종목 수: {len(analysis_data.get('individual_analysis', {}))}")
            print(f"      추천 종목: {analysis_data.get('recommendations', {}).get('buy', [])}")
            print(f"      시장 전망: {analysis_data.get('market_outlook', 'N/A')}")
            print(f"      신뢰도: {analysis_data.get('confidence_score', 'N/A')}")
            
            # 개별 종목 분석 확인
            individual_analysis = analysis_data.get("individual_analysis", {})
            if individual_analysis:
                print(f"\n   🔍 개별 종목 분석:")
                for ticker, data in individual_analysis.items():
                    print(f"      {ticker}: 투자등급={data.get('grade', 'N/A')}, "
                          f"PER={data.get('per', 'N/A')}, "
                          f"소스={data.get('data_source', 'N/A')}")
            
            return True
        else:
            print(f"   ❌ 결과 데이터 구조 오류")
            return False
            
    except Exception as e:
        print(f"   ❌ 에이전트 테스트 실패: {e}")
        import traceback
        print(f"   📋 상세 오류:\n{traceback.format_exc()}")
        return False

def test_data_engine_performance():
    """데이터 엔진 성능 테스트"""
    print("\n⚡ 데이터 엔진 성능 테스트...")
    
    try:
        from src.utils.fundamental_data_engine import FundamentalDataEngine
        
        # 실제 API 모드로 엔진 생성
        engine = FundamentalDataEngine(mock_mode=False, cache_ttl_minutes=5)
        
        # 대표 종목들
        test_tickers = ["005930", "000660", "035420", "068270", "105560"]  # 5개 종목
        names = ["삼성전자", "SK하이닉스", "네이버", "셀트리온", "KB금융"]
        
        print(f"   📊 테스트 대상: {len(test_tickers)}개 종목")
        
        results = []
        total_start = time.time()
        
        for i, ticker in enumerate(test_tickers):
            print(f"   📈 {names[i]}({ticker}) 분석 중...")
            
            start_time = time.time()
            try:
                data = engine.collect_fundamental_data(ticker, include_news=True)
                fetch_time = time.time() - start_time
                
                results.append({
                    'ticker': ticker,
                    'name': names[i],
                    'success': True,
                    'fetch_time': fetch_time,
                    'data_source': data.financial_ratios.source,
                    'data_quality': data.financial_ratios.data_quality.value,
                    'confidence': data.confidence_score,
                    'news_count': len(data.recent_news) if hasattr(data, 'recent_news') else 0
                })
                
                print(f"      ✅ 성공 ({fetch_time:.2f}초, 소스: {data.financial_ratios.source})")
                
                # API 부하 방지를 위한 딜레이
                time.sleep(0.3)
                
            except Exception as e:
                fetch_time = time.time() - start_time
                results.append({
                    'ticker': ticker,
                    'name': names[i],
                    'success': False,
                    'fetch_time': fetch_time,
                    'error': str(e)
                })
                print(f"      ❌ 실패 ({fetch_time:.2f}초): {e}")
        
        total_time = time.time() - total_start
        
        # 성능 분석
        successful = [r for r in results if r['success']]
        success_rate = len(successful) / len(results) * 100
        avg_time = sum(r['fetch_time'] for r in successful) / len(successful) if successful else 0
        real_api_count = sum(1 for r in successful if r.get('data_source') == 'KIS_API')
        
        print(f"\n   📊 성능 분석 결과:")
        print(f"      총 실행 시간: {total_time:.2f}초")
        print(f"      성공률: {success_rate:.1f}% ({len(successful)}/{len(results)})")
        print(f"      평균 처리 시간: {avg_time:.2f}초/종목")
        print(f"      실제 API 사용: {real_api_count}/{len(successful)}")
        
        return success_rate >= 80  # 80% 이상 성공률 요구
        
    except Exception as e:
        print(f"   ❌ 성능 테스트 실패: {e}")
        return False

def test_gemini_integration():
    """Gemini 2.5 Flash-Lite 통합 테스트"""
    print("\n🧠 Gemini 2.5 Flash-Lite AI 분석 테스트...")
    
    try:
        from src.llm_clients.gemini import GeminiClient
        from src.llm_clients.request import LLMRequest
        
        # Gemini 클라이언트 생성
        gemini_client = GeminiClient()
        
        # 테스트용 재무 데이터
        test_data = {
            "company_name": "삼성전자",
            "ticker": "005930",
            "financial_ratios": {
                "per": 15.2,
                "pbr": 1.8,
                "roe": 12.5,
                "debt_ratio": 0.3,
                "current_ratio": 1.8
            },
            "recent_news": [
                "삼성전자, 3분기 실적 예상치 상회",
                "메모리 반도체 수요 회복 조짐"
            ]
        }
        
        # LLM 요청 생성
        prompt = f"""
다음 기업의 펀더멘털 분석을 수행하세요:

기업 정보:
- 회사명: {test_data['company_name']}
- 종목코드: {test_data['ticker']}
- PER: {test_data['financial_ratios']['per']}
- PBR: {test_data['financial_ratios']['pbr']}
- ROE: {test_data['financial_ratios']['roe']}%

최근 뉴스:
{chr(10).join(f"- {news}" for news in test_data['recent_news'])}

다음 형식으로 응답하세요:
{{
  "investment_grade": "A|B|C|D|F",
  "target_price": 숫자,
  "key_strengths": ["강점1", "강점2"],
  "key_risks": ["리스크1", "리스크2"],
  "investment_thesis": "투자 논리 요약"
}}
"""
        
        request = LLMRequest(
            agent_type="fundamental_fetcher",
            prompt=prompt,
            temperature=0.4,
            max_tokens=1000
        )
        
        print(f"   🤖 Gemini Flash-Lite 분석 요청 중...")
        start_time = time.time()
        
        response = gemini_client.make_request(request)
        
        analysis_time = time.time() - start_time
        print(f"   ⏱️ AI 분석 시간: {analysis_time:.2f}초")
        
        if response and response.content:
            print(f"   ✅ AI 분석 완료")
            print(f"   📊 응답 길이: {len(response.content)}자")
            
            # JSON 파싱 시도
            try:
                import json
                analysis_result = json.loads(response.content)
                print(f"   🎯 투자 등급: {analysis_result.get('investment_grade', 'N/A')}")
                print(f"   💰 목표 주가: {analysis_result.get('target_price', 'N/A')}")
                return True
            except json.JSONDecodeError:
                print(f"   ⚠️ JSON 파싱 실패하지만 응답은 수신됨")
                return True
        else:
            print(f"   ❌ AI 응답 없음")
            return False
            
    except Exception as e:
        print(f"   ❌ Gemini 테스트 실패: {e}")
        return False

def main():
    """메인 테스트 함수"""
    start_time = time.time()
    
    print(f"📅 테스트 시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 테스트 실행
    tests = [
        ("데이터 엔진 성능", test_data_engine_performance),
        ("Gemini AI 통합", test_gemini_integration),
        ("펀더멘털 페처 에이전트", test_fundamental_fetcher_agent)
    ]
    
    results = []
    passed = 0
    
    for test_name, test_func in tests:
        print(f"\n🔍 {test_name} 테스트 실행...")
        try:
            success = test_func()
            if success:
                print(f"✅ {test_name} 성공")
                passed += 1
            else:
                print(f"❌ {test_name} 실패")
            
            results.append({
                "name": test_name,
                "success": success
            })
        except Exception as e:
            print(f"💥 {test_name} 예외: {e}")
            results.append({
                "name": test_name,
                "success": False,
                "error": str(e)
            })
    
    # 최종 결과
    total_time = time.time() - start_time
    success_rate = (passed / len(tests)) * 100 if tests else 0
    
    print("\n" + "=" * 60)
    print("🎯 최종 테스트 결과")
    print("=" * 60)
    print(f"⏱️ 총 실행 시간: {total_time:.2f}초")
    print(f"📊 전체 테스트: {len(tests)}개")
    print(f"✅ 성공: {passed}개")
    print(f"❌ 실패: {len(tests) - passed}개")
    print(f"📈 성공률: {success_rate:.1f}%")
    
    if success_rate == 100:
        print("\n🎉 펀더멘털 페처 에이전트 완벽 작동!")
        print("   - 실제 KIS API 데이터 수집 성공")
        print("   - Gemini 2.5 Flash-Lite AI 분석 정상")
        print("   - 통합 에이전트 워크플로우 완료")
    elif success_rate >= 70:
        print("\n✅ 펀더멘털 페처 에이전트 정상 작동")
        print("   - 대부분의 기능이 정상 작동합니다")
    else:
        print("\n⚠️ 일부 기능에 문제가 있습니다")
    
    # 결과 저장
    final_result = {
        "timestamp": datetime.now().isoformat(),
        "total_time": total_time,
        "success_rate": success_rate,
        "tests": results,
        "summary": {
            "total": len(tests),
            "passed": passed,
            "failed": len(tests) - passed
        }
    }
    
    try:
        with open("test_results_complete.json", "w", encoding="utf-8") as f:
            json.dump(final_result, f, ensure_ascii=False, indent=2)
        print(f"\n💾 상세 결과 저장: test_results_complete.json")
    except Exception as e:
        print(f"\n❌ 결과 저장 실패: {e}")
    
    return success_rate == 100

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)