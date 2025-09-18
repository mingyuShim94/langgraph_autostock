#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KIS API 인증 테스트 스크립트
모의투자 환경에서 KIS API 연결 및 기본 기능 테스트
"""

import sys
import os

# KIS API 모듈 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__), 'open-trading-api-main/examples_user'))

try:
    import kis_auth as ka
    from auth_functions import auth_token
    from domestic_stock_functions import inquire_account_balance, inquire_balance
    print("✅ KIS API 모듈 import 성공")
except ImportError as e:
    print(f"❌ KIS API 모듈 import 실패: {e}")
    print("open-trading-api-main/examples_user 경로를 확인해주세요.")
    sys.exit(1)

def test_kis_authentication():
    """KIS API 인증 테스트"""
    print("\n🔐 KIS API 인증 테스트 시작...")
    
    try:
        # 모의투자 환경에서 인증
        print("📍 모의투자 환경 인증 중...")
        ka.auth(svr="vps", product="01")  # vps: 모의투자, product: 종합계좌
        
        # 환경 정보 가져오기
        trenv = ka.getTREnv()
        
        print("✅ 인증 성공!")
        print(f"   계좌번호: {trenv.my_acct}")
        print(f"   상품코드: {trenv.my_prod}")
        print(f"   앱키: {trenv.my_app[:10]}...")  # 보안을 위해 일부만 표시
        
        return True, trenv
        
    except Exception as e:
        print(f"❌ 인증 실패: {e}")
        return False, None

def test_account_balance(trenv):
    """계좌잔고 조회 테스트"""
    print("\n💰 계좌잔고 조회 테스트 시작...")
    
    try:
        # 계좌 자산 현황 조회
        account_df, account_summary = inquire_account_balance(
            cano=trenv.my_acct,
            acnt_prdt_cd=trenv.my_prod
        )
        
        if not account_summary.empty:
            print("✅ 계좌잔고 조회 성공!")
            
            # 주요 정보 출력
            summary = account_summary.iloc[0]
            print(f"   예수금 총액: {summary.get('dnca_tot_amt', 'N/A'):,}원")
            print(f"   총 평가금액: {summary.get('tot_evlu_amt', 'N/A'):,}원")
            print(f"   순자산액: {summary.get('nass_amt', 'N/A'):,}원")
            
            return True
        else:
            print("❌ 계좌잔고 데이터 없음")
            return False
            
    except Exception as e:
        print(f"❌ 계좌잔고 조회 실패: {e}")
        return False

def test_stock_balance(trenv):
    """주식잔고 조회 테스트"""
    print("\n📈 주식잔고 조회 테스트 시작...")
    
    try:
        # 주식잔고 조회
        holdings_df, holdings_summary = inquire_balance(
            env_dv="demo",  # 모의투자
            cano=trenv.my_acct,
            acnt_prdt_cd=trenv.my_prod,
            afhr_flpr_yn="N",
            inqr_dvsn="01",
            unpr_dvsn="01",
            fund_sttl_icld_yn="N",
            fncg_amt_auto_rdpt_yn="N",
            prcs_dvsn="00"
        )
        
        print("✅ 주식잔고 조회 성공!")
        
        if not holdings_df.empty:
            # 보유 종목 정보
            stock_count = len(holdings_df[holdings_df['hldg_qty'].astype(int) > 0])
            print(f"   보유 종목 수: {stock_count}개")
            
            # 보유 종목 상세 (수량이 있는 것만)
            for idx, row in holdings_df.iterrows():
                if int(row['hldg_qty']) > 0:
                    print(f"   📊 {row.get('prdt_name', 'N/A')} ({row.get('pdno', 'N/A')})")
                    print(f"      보유수량: {int(row['hldg_qty']):,}주")
                    print(f"      평균단가: {float(row['pchs_avg_pric']):,}원")
                    print(f"      현재가: {float(row['prpr']):,}원")
                    print(f"      평가손익: {float(row['evlu_pfls_amt']):,}원")
        else:
            print("   보유 종목 없음 (모의투자 계좌)")
            
        return True
        
    except Exception as e:
        print(f"❌ 주식잔고 조회 실패: {e}")
        return False

def main():
    """메인 테스트 함수"""
    print("🚀 KIS API 종합 테스트 시작")
    print("=" * 50)
    
    # 1. 인증 테스트
    auth_success, trenv = test_kis_authentication()
    if not auth_success:
        print("\n❌ 인증 실패로 테스트 중단")
        return
    
    # 2. 계좌잔고 조회 테스트
    balance_success = test_account_balance(trenv)
    
    # 3. 주식잔고 조회 테스트
    stock_success = test_stock_balance(trenv)
    
    # 결과 요약
    print("\n" + "=" * 50)
    print("🎯 테스트 결과 요약")
    print(f"   인증: {'✅ 성공' if auth_success else '❌ 실패'}")
    print(f"   계좌잔고 조회: {'✅ 성공' if balance_success else '❌ 실패'}")
    print(f"   주식잔고 조회: {'✅ 성공' if stock_success else '❌ 실패'}")
    
    if auth_success and balance_success and stock_success:
        print("\n🎉 모든 테스트 통과! KIS API 연동 준비 완료")
        print("   이제 Phase 1 단계로 진행할 수 있습니다.")
    else:
        print("\n⚠️  일부 테스트 실패. 설정을 다시 확인해주세요.")

if __name__ == "__main__":
    main()