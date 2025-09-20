#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
펀더멘털 페처 에이전트 실제 KIS API 연동 테스트

실제 KIS API를 사용하여 재무제표 데이터를 수집하고 테스트
docs/kis_api_implementation_guide.md 기반 구현
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

# KIS API 모듈 경로 추가 (docs/kis_api_implementation_guide.md 참고)
kis_path = os.path.join(project_root, 'open-trading-api-main/examples_user')
kis_domestic_path = os.path.join(project_root, 'open-trading-api-main/examples_user/domestic_stock')
kis_llm_path = os.path.join(project_root, 'open-trading-api-main/examples_llm/domestic_stock/finance_financial_ratio')

sys.path.extend([kis_path, kis_domestic_path, kis_llm_path])

try:
    import kis_auth as ka
    from finance_financial_ratio import finance_financial_ratio
    KIS_AVAILABLE = True
    print("✅ KIS API 모듈 import 성공")
except ImportError as e:
    print(f"❌ KIS API 모듈 import 실패: {e}")
    KIS_AVAILABLE = False

from src.utils.fundamental_data_engine import FundamentalDataEngine


class KISAPITester:
    """KIS API 실제 연동 테스터"""
    
    def __init__(self):
        """테스터 초기화"""
        self.logger = logging.getLogger(__name__)
        self.start_time = time.time()
        self.test_results = []
        
        # 로깅 설정
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        print("=" * 80)
        print("🔥 펀더멘털 페처 에이전트 실제 KIS API 연동 테스트")
        print("=" * 80)
        print(f"📅 테스트 시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🔧 KIS API 사용 가능: {'YES' if KIS_AVAILABLE else 'NO'}")
        print()
    
    def run_all_tests(self) -> bool:
        """모든 실제 API 테스트 실행"""
        if not KIS_AVAILABLE:
            print("❌ KIS API 모듈을 사용할 수 없어 테스트를 중단합니다.")
            return False
        
        tests = [
            ("KIS API 인증 테스트", self.test_kis_authentication),
            ("재무비율 API 직접 호출 테스트", self.test_direct_financial_ratio_api),
            ("펀더멘털 데이터 엔진 실제 API 테스트", self.test_real_api_data_engine),
            ("다중 종목 실제 데이터 수집 테스트", self.test_multiple_tickers_real_data),
            ("실제 vs Mock 데이터 비교 테스트", self.test_real_vs_mock_comparison)
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
                
                # API 부하 방지를 위한 대기
                time.sleep(1)
                
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
    
    def test_kis_authentication(self) -> bool:
        """KIS API 인증 테스트"""
        try:
            print("   🔐 KIS API 인증 시도 중...")
            
            # Paper trading 서버로 인증 (docs/kis_api_implementation_guide.md 참고)
            ka.auth(svr="vps", product="01")
            trenv = ka.getTREnv()
            
            print(f"   ✓ 인증 성공")
            print(f"   ✓ 계좌번호: {trenv.my_acct}")
            print(f"   ✓ 앱키: {trenv.my_app[:10]}...")
            print(f"   ✓ 서버: vps (Paper Trading)")
            
            return True
            
        except Exception as e:
            print(f"   ❌ KIS API 인증 실패: {e}")
            print("   💡 해결방법:")
            print("      1. ~/KIS/config/kis_devlp.yaml 파일 확인")
            print("      2. Paper trading 앱키/시크릿 정확성 확인")
            print("      3. 한국투자증권 Open API 서비스 신청 확인")
            return False
    
    def test_direct_financial_ratio_api(self) -> bool:
        """재무비율 API 직접 호출 테스트"""
        try:
            print("   📊 삼성전자(005930) 재무비율 데이터 조회 중...")
            
            # 실제 finance_financial_ratio API 호출
            financial_data = finance_financial_ratio(
                fid_div_cls_code="0",  # 0: 년도별 데이터
                fid_cond_mrkt_div_code="J",  # J: 코스피/코스닥
                fid_input_iscd="005930"  # 삼성전자
            )
            
            if financial_data is not None and not financial_data.empty:
                print(f"   ✓ 데이터 수신 성공")
                print(f"   ✓ 데이터 행 수: {len(financial_data)}")
                print(f"   ✓ 데이터 컬럼 수: {len(financial_data.columns)}")
                
                # 샘플 데이터 출력
                if len(financial_data) > 0:
                    first_row = financial_data.iloc[0]
                    print(f"   ✓ 샘플 데이터:")
                    for i, (col, val) in enumerate(first_row.items()):
                        if i < 5:  # 처음 5개 컬럼만 출력
                            print(f"      - {col}: {val}")
                
                return True
            else:
                print("   ❌ 빈 데이터 수신")
                return False
            
        except Exception as e:
            print(f"   ❌ 재무비율 API 호출 실패: {e}")
            return False
    
    def test_real_api_data_engine(self) -> bool:
        """펀더멘털 데이터 엔진 실제 API 테스트"""
        try:
            print("   🔧 실제 API 모드로 데이터 엔진 초기화...")
            
            # Mock 모드 비활성화
            engine = FundamentalDataEngine(mock_mode=False, cache_ttl_minutes=1)
            
            print("   📈 네이버(035420) 펀더멘털 데이터 수집 중...")
            data = engine.collect_fundamental_data("035420")
            
            # 데이터 검증
            assert data.ticker == "035420"
            assert data.company_name is not None
            assert data.financial_ratios is not None
            
            fr = data.financial_ratios
            print(f"   ✓ 회사명: {data.company_name}")
            print(f"   ✓ 데이터 품질: {data.financial_ratios.data_quality.value}")
            print(f"   ✓ 데이터 소스: {data.financial_ratios.source}")
            
            if fr.per is not None:
                print(f"   ✓ PER: {fr.per}")
            if fr.pbr is not None:
                print(f"   ✓ PBR: {fr.pbr}")
            if fr.roe is not None:
                print(f"   ✓ ROE: {fr.roe}%")
            if fr.debt_ratio is not None:
                print(f"   ✓ 부채비율: {fr.debt_ratio}%")
            
            print(f"   ✓ 수집 시간: {data.collection_time:.3f}초")
            print(f"   ✓ 신뢰도: {data.confidence_score}")
            
            # 실제 API 데이터인지 확인
            if data.financial_ratios.source == "KIS_API":
                print("   🎉 실제 KIS API 데이터 수집 성공!")
                return True
            else:
                print(f"   ⚠️ Mock 데이터 사용됨: {data.financial_ratios.source}")
                return False
            
        except Exception as e:
            print(f"   ❌ 실제 API 데이터 엔진 테스트 실패: {e}")
            return False
    
    def test_multiple_tickers_real_data(self) -> bool:
        """다중 종목 실제 데이터 수집 테스트"""
        try:
            print("   📊 3개 종목 동시 수집 테스트...")
            
            engine = FundamentalDataEngine(mock_mode=False, cache_ttl_minutes=1)
            
            # 대표 종목들
            tickers = ["005930", "000660", "035720"]  # 삼성전자, SK하이닉스, 카카오
            ticker_names = ["삼성전자", "SK하이닉스", "카카오"]
            
            results = {}
            real_data_count = 0
            
            for i, ticker in enumerate(tickers):
                print(f"   📈 {ticker_names[i]}({ticker}) 데이터 수집 중...")
                
                try:
                    data = engine.collect_fundamental_data(ticker)
                    results[ticker] = data
                    
                    if data.financial_ratios.source == "KIS_API":
                        real_data_count += 1
                        print(f"      ✓ 실제 API 데이터 수집 성공")
                    else:
                        print(f"      ⚠️ Mock 데이터 사용")
                    
                    print(f"      ✓ 신뢰도: {data.confidence_score}")
                    
                    # API 부하 방지
                    time.sleep(0.5)
                    
                except Exception as e:
                    print(f"      ❌ {ticker} 수집 실패: {e}")
                    results[ticker] = None
            
            # 결과 요약
            success_count = len([r for r in results.values() if r is not None])
            print(f"   ✓ 성공한 종목 수: {success_count}/{len(tickers)}")
            print(f"   ✓ 실제 API 데이터: {real_data_count}/{len(tickers)}")
            
            # 캐시 통계
            cache_stats = engine.get_cache_stats()
            print(f"   ✓ 캐시 항목: {cache_stats['total_cached_items']}개")
            
            return success_count >= 2  # 최소 2개 종목은 성공해야 함
            
        except Exception as e:
            print(f"   ❌ 다중 종목 테스트 실패: {e}")
            return False
    
    def test_real_vs_mock_comparison(self) -> bool:
        """실제 vs Mock 데이터 비교 테스트"""
        try:
            print("   🔄 실제 데이터 vs Mock 데이터 비교...")
            
            ticker = "005930"  # 삼성전자
            
            # 실제 API 데이터 수집
            print("   📡 실제 API 데이터 수집 중...")
            real_engine = FundamentalDataEngine(mock_mode=False)
            real_data = real_engine.collect_fundamental_data(ticker)
            
            # Mock 데이터 수집
            print("   🎭 Mock 데이터 수집 중...")
            mock_engine = FundamentalDataEngine(mock_mode=True)
            mock_data = mock_engine.collect_fundamental_data(ticker)
            
            # 비교 분석
            print(f"\n   📊 데이터 비교 결과:")
            print(f"   {'항목':<15} {'실제 API':<15} {'Mock 데이터':<15}")
            print(f"   {'-'*45}")
            
            comparisons = [
                ("데이터 소스", real_data.financial_ratios.source, mock_data.financial_ratios.source),
                ("데이터 품질", real_data.financial_ratios.data_quality.value, mock_data.financial_ratios.data_quality.value),
                ("PER", real_data.financial_ratios.per, mock_data.financial_ratios.per),
                ("PBR", real_data.financial_ratios.pbr, mock_data.financial_ratios.pbr),
                ("ROE", real_data.financial_ratios.roe, mock_data.financial_ratios.roe),
                ("신뢰도", real_data.confidence_score, mock_data.confidence_score),
                ("수집시간", f"{real_data.collection_time:.3f}s", f"{mock_data.collection_time:.3f}s")
            ]
            
            for item, real_val, mock_val in comparisons:
                print(f"   {item:<15} {str(real_val):<15} {str(mock_val):<15}")
            
            # 실제 데이터 품질 검증
            is_real_data = real_data.financial_ratios.source == "KIS_API"
            is_mock_data = mock_data.financial_ratios.source == "MOCK_DATA"
            
            print(f"\n   📈 품질 분석:")
            print(f"   ✓ 실제 API 데이터 여부: {is_real_data}")
            print(f"   ✓ Mock 데이터 여부: {is_mock_data}")
            print(f"   ✓ 데이터 구조 일치성: {type(real_data) == type(mock_data)}")
            
            return is_real_data and is_mock_data  # 둘 다 올바르게 작동해야 함
            
        except Exception as e:
            print(f"   ❌ 실제 vs Mock 데이터 비교 실패: {e}")
            return False
    
    def _print_test_summary(self, passed: int, total: int) -> None:
        """테스트 결과 요약 출력"""
        print("\n" + "=" * 80)
        print("📊 실제 KIS API 연동 테스트 결과 요약")
        print("=" * 80)
        
        success_rate = (passed / total) * 100 if total > 0 else 0
        total_time = time.time() - self.start_time
        
        print(f"🎯 전체 테스트: {total}개")
        print(f"✅ 통과한 테스트: {passed}개")
        print(f"❌ 실패한 테스트: {total - passed}개")
        print(f"📈 성공률: {success_rate:.1f}%")
        print(f"⏱️ 총 실행 시간: {total_time:.2f}초")
        
        if success_rate == 100:
            print("🎉 모든 실제 API 테스트 통과! KIS API 연동이 완벽하게 작동합니다.")
        elif success_rate >= 80:
            print("⚠️ 대부분의 테스트 통과. 일부 API 기능에 주의가 필요합니다.")
        else:
            print("🚨 다수의 테스트 실패. KIS API 설정 및 연동을 점검하세요.")
        
        print("\n📋 개별 테스트 결과:")
        for i, result in enumerate(self.test_results, 1):
            status = "✅ PASS" if result["passed"] else "❌ FAIL"
            print(f"  {i:2d}. {result['name']:40s} {status} ({result['execution_time']:.3f}초)")
            
            if not result["passed"] and "error" in result:
                print(f"      오류: {result['error']}")
        
        if success_rate < 100:
            print("\n💡 문제 해결 가이드:")
            print("1. ~/KIS/config/kis_devlp.yaml 파일의 API 키 확인")
            print("2. 한국투자증권 Open API 서비스 신청 상태 확인")
            print("3. Paper trading 앱키와 실전투자 앱키 구분 확인")
            print("4. 네트워크 연결 및 방화벽 설정 확인")
    
    def _save_test_results(self, passed: int, total: int) -> None:
        """테스트 결과를 JSON 파일로 저장"""
        results = {
            "timestamp": datetime.now().isoformat(),
            "test_type": "real_kis_api_integration",
            "total_tests": total,
            "passed_tests": passed,
            "success_rate": (passed / total) * 100 if total > 0 else 0,
            "test_results": self.test_results,
            "kis_api_available": KIS_AVAILABLE,
            "pandas_version": "2.3.2"
        }
        
        filename = f"test_results_kis_api_real.json"
        filepath = os.path.join(project_root, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f"\n💾 테스트 결과 저장: {filename}")
        except Exception as e:
            print(f"\n❌ 테스트 결과 저장 실패: {e}")


def main():
    """메인 테스트 실행 함수"""
    print("🚀 실제 KIS API 연동 테스트를 시작합니다...")
    print()
    print("⚠️  주의사항:")
    print("- 이 테스트는 실제 KIS Open API를 사용합니다")
    print("- Paper trading 환경에서 실행됩니다")
    print("- API 키가 올바르게 설정되어야 합니다")
    print("- ~/KIS/config/kis_devlp.yaml 파일을 확인하세요")
    print()
    
    # 사용자 확인
    response = input("계속 진행하시겠습니까? (y/N): ")
    if response.lower() != 'y':
        print("테스트를 취소합니다.")
        return
    
    # 테스터 실행
    tester = KISAPITester()
    success = tester.run_all_tests()
    
    # 종료 코드 설정
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()