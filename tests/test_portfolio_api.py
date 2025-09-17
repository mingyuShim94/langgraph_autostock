"""
KIS API 포트폴리오 조회 테스트
실제 모의투자 계좌 잔고 조회 및 데이터 분석
"""
import os
import sys
import json
import requests
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.kis_auth import authenticate
from config.settings import settings


def test_portfolio_balance():
    """포트폴리오 잔고 조회 테스트"""
    print("💼 포트폴리오 잔고 조회 테스트")
    print("=" * 50)

    try:
        # 인증 수행
        auth = authenticate('paper')
        print(f"✅ 인증 성공")
        print(f"🏦 계좌: {auth.tr_env.my_acct}")
        print(f"📋 상품코드: {auth.tr_env.my_prod}")
        print()

        # 모의투자용 TR_ID
        tr_id = "VTTC8434R"  # 모의투자 잔고조회
        url = f"{auth.tr_env.my_url}/uapi/domestic-stock/v1/trading/inquire-balance"

        headers = {
            "Content-Type": "application/json",
            "Accept": "text/plain",
            "charset": "UTF-8",
            "User-Agent": auth.config['my_agent'],
            "authorization": f"Bearer {auth.token_cache}",
            "appkey": auth.tr_env.my_app,
            "appsecret": auth.tr_env.my_sec,
            "tr_id": tr_id,
            "custtype": "P"
        }

        params = {
            "CANO": auth.tr_env.my_acct,
            "ACNT_PRDT_CD": auth.tr_env.my_prod,
            "AFHR_FLPR_YN": "N",
            "OFL_YN": "",
            "INQR_DVSN": "02",  # 종목별
            "UNPR_DVSN": "01",
            "FUND_STTL_ICLD_YN": "N",
            "FNCG_AMT_AUTO_RDPT_YN": "N",
            "PRCS_DVSN": "01",  # 전일매매미포함
            "CTX_AREA_FK100": "",
            "CTX_AREA_NK100": ""
        }

        print(f"📡 API 호출 중...")
        print(f"🔗 URL: {url}")
        print(f"🔖 TR_ID: {tr_id}")
        print(f"📊 조회구분: 종목별")

        response = requests.get(url, headers=headers, params=params, timeout=15)

        print(f"📊 응답 코드: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print("✅ 잔고 조회 성공!")

            # 응답 구조 분석
            analyze_balance_response(result)
            return result

        else:
            print(f"❌ 잔고 조회 실패: {response.status_code}")
            print(f"📄 오류 내용: {response.text}")

            # 오류 분석
            try:
                error_data = response.json()
                print(f"📋 오류 코드: {error_data.get('msg_cd', 'N/A')}")
                print(f"📋 오류 메시지: {error_data.get('msg1', 'N/A')}")
            except:
                pass

            return None

    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return None


def analyze_balance_response(result: Dict[str, Any]):
    """잔고 조회 응답 분석"""
    print("\n📊 응답 데이터 분석")
    print("-" * 40)

    # 응답 구조 확인
    print(f"📋 응답 키: {list(result.keys())}")

    # rt_cd 확인 (성공 여부)
    rt_cd = result.get('rt_cd', '')
    msg1 = result.get('msg1', '')
    print(f"📈 응답 코드: {rt_cd}")
    print(f"📝 메시지: {msg1}")

    if rt_cd != '0':
        print(f"⚠️ 응답 코드가 성공(0)이 아닙니다: {rt_cd}")
        return

    # output1 (보유종목) 분석
    if 'output1' in result:
        stocks = result['output1']
        print(f"\n📈 보유종목 분석 (총 {len(stocks)}개)")

        if len(stocks) > 0:
            # DataFrame으로 변환하여 분석
            df_stocks = pd.DataFrame(stocks)
            print(f"📊 데이터 컬럼: {list(df_stocks.columns)}")

            # 주요 정보 출력
            for i, stock in enumerate(stocks[:5]):  # 최대 5개만 표시
                stock_name = stock.get('prdt_name', 'N/A')
                stock_code = stock.get('pdno', 'N/A')
                quantity = stock.get('hldg_qty', '0')
                current_price = stock.get('prpr', '0')
                eval_amt = stock.get('evlu_amt', '0')
                profit_loss = stock.get('evlu_pfls_amt', '0')

                print(f"   {i+1}. {stock_name} ({stock_code})")
                print(f"      보유수량: {quantity}주")
                print(f"      현재가: {current_price}원")
                print(f"      평가금액: {eval_amt}원")
                print(f"      평가손익: {profit_loss}원")

            if len(stocks) > 5:
                print(f"   ... 외 {len(stocks) - 5}개 종목")

        else:
            print("   📝 보유종목이 없습니다.")

    # output2 (계좌 요약) 분석
    if 'output2' in result:
        summary = result['output2']
        if len(summary) > 0:
            account_info = summary[0]  # 첫 번째 항목이 계좌 요약

            print(f"\n💰 계좌 요약 정보")

            total_asset = account_info.get('tot_evlu_amt', '0')
            cash_balance = account_info.get('nass_amt', '0')
            stock_eval = account_info.get('scts_evlu_amt', '0')
            total_profit = account_info.get('evlu_pfls_smtl_amt', '0')
            profit_rate = account_info.get('tot_evlu_pfls_amt', '0')

            print(f"   💎 총 평가금액: {format_currency(total_asset)}")
            print(f"   💵 현금잔고: {format_currency(cash_balance)}")
            print(f"   📈 주식평가금액: {format_currency(stock_eval)}")
            print(f"   📊 총 평가손익: {format_currency(total_profit)}")
            print(f"   📈 수익률: {profit_rate}%")

    # 전체 응답 저장 (디버깅용)
    save_response_data(result)


def format_currency(amount_str: str) -> str:
    """통화 포맷팅"""
    try:
        amount = int(amount_str)
        return f"{amount:,}원"
    except:
        return f"{amount_str}원"


def save_response_data(result: Dict[str, Any]):
    """응답 데이터 파일로 저장"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"logs/portfolio_response_{timestamp}.json"

        os.makedirs("logs", exist_ok=True)

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        print(f"\n💾 응답 데이터 저장: {filename}")

    except Exception as e:
        print(f"⚠️ 데이터 저장 실패: {e}")


def test_data_mapping():
    """데이터 매핑 테스트 (state.py 모델과 연동)"""
    print("\n🔄 데이터 매핑 테스트")
    print("=" * 50)

    # 포트폴리오 조회
    balance_data = test_portfolio_balance()

    if not balance_data:
        print("❌ 잔고 데이터가 없어서 매핑 테스트를 건너뜁니다.")
        return False

    try:
        # state.py 모델 import
        sys.path.append('..')
        from src.state import StockInfo, PortfolioStatus

        print("📊 state.py 모델로 데이터 변환 중...")

        # 보유종목 데이터 변환
        stocks = []
        if 'output1' in balance_data:
            for stock_data in balance_data['output1'][:3]:  # 최대 3개만 테스트
                try:
                    stock_info = StockInfo(
                        ticker=stock_data.get('pdno', ''),
                        name=stock_data.get('prdt_name', ''),
                        quantity=int(stock_data.get('hldg_qty', '0')),
                        avg_price=float(stock_data.get('pchs_avg_pric', '0')),
                        current_price=float(stock_data.get('prpr', '0')),
                        market_value=float(stock_data.get('evlu_amt', '0')),
                        profit_loss=float(stock_data.get('evlu_pfls_amt', '0')),
                        profit_loss_rate=float(stock_data.get('evlu_pfls_rt', '0'))
                    )
                    stocks.append(stock_info)
                    print(f"   ✅ {stock_info.name} 변환 성공")
                except Exception as e:
                    print(f"   ⚠️ 종목 변환 실패: {e}")

        # 포트폴리오 요약 데이터 변환
        if 'output2' in balance_data and len(balance_data['output2']) > 0:
            summary = balance_data['output2'][0]

            portfolio = PortfolioStatus(
                total_asset=float(summary.get('tot_evlu_amt', '0')),
                total_investment=float(summary.get('pchs_amt_smtl_amt', '0')),
                cash_balance=float(summary.get('nass_amt', '0')),
                total_profit_loss=float(summary.get('evlu_pfls_smtl_amt', '0')),
                total_profit_loss_rate=float(summary.get('tot_evlu_pfls_amt', '0')),
                stocks=stocks,
                last_updated=datetime.now()
            )

            print(f"✅ PortfolioStatus 객체 생성 성공")
            print(f"   총자산: {portfolio.total_asset:,.0f}원")
            print(f"   보유종목: {len(portfolio.stocks)}개")
            print(f"   수익률: {portfolio.total_profit_loss_rate}%")

            return portfolio
        else:
            print("⚠️ 계좌 요약 데이터가 없습니다.")
            return None

    except Exception as e:
        print(f"❌ 데이터 매핑 실패: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """메인 테스트 실행"""
    print("💼 KIS API 포트폴리오 조회 테스트 시작")
    print(f"⏰ 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # 1. 기본 잔고 조회 테스트
    balance_result = test_portfolio_balance()

    # 2. 데이터 매핑 테스트
    if balance_result:
        portfolio_obj = test_data_mapping()

        if portfolio_obj:
            print("\n🎉 포트폴리오 조회 및 매핑 테스트 완료!")
            print("✅ Phase 2.1 성공 - 다음 단계 진행 가능")
            return True

    print("\n❌ 포트폴리오 조회 테스트 실패")
    return False


if __name__ == "__main__":
    main()