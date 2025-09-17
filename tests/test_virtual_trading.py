"""
KIS API 모의투자 가상 매수 테스트
포트폴리오 데이터 생성을 위한 테스트 매수
"""
import os
import sys
import json
import requests
from datetime import datetime

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.kis_auth import authenticate


def check_current_price(stock_code: str = "005930"):
    """주식 현재가 조회"""
    print(f"📈 {stock_code} 현재가 조회")
    print("-" * 30)

    try:
        auth = authenticate('paper')

        url = f"{auth.tr_env.my_url}/uapi/domestic-stock/v1/quotations/inquire-price"

        headers = {
            "Content-Type": "application/json",
            "Accept": "text/plain",
            "charset": "UTF-8",
            "User-Agent": auth.config['my_agent'],
            "authorization": f"Bearer {auth.token_cache}",
            "appkey": auth.tr_env.my_app,
            "appsecret": auth.tr_env.my_sec,
            "tr_id": "FHKST01010100",
            "custtype": "P"
        }

        params = {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": stock_code
        }

        response = requests.get(url, headers=headers, params=params, timeout=10)

        if response.status_code == 200:
            result = response.json()
            if 'output' in result:
                output = result['output']
                current_price = output.get('stck_prpr', '0')
                stock_name = output.get('prdt_abrv_name', 'N/A')

                print(f"   종목명: {stock_name}")
                print(f"   현재가: {current_price}원")
                print(f"   등락률: {output.get('prdy_ctrt', 'N/A')}%")

                return int(current_price)
            else:
                print("   ❌ 현재가 조회 실패")
                return 0
        else:
            print(f"   ❌ API 호출 실패: {response.status_code}")
            return 0

    except Exception as e:
        print(f"   ❌ 현재가 조회 실패: {e}")
        return 0


def simulate_buy_order(stock_code: str = "005930", quantity: int = 1):
    """모의 매수 주문 (실제로는 실행되지 않음 - 시뮬레이션)"""
    print(f"\n💰 모의 매수 주문 시뮬레이션")
    print("=" * 40)

    try:
        auth = authenticate('paper')

        # 현재가 조회
        current_price = check_current_price(stock_code)
        if current_price == 0:
            print("❌ 현재가를 가져올 수 없어서 주문을 중단합니다.")
            return False

        print(f"\n📊 주문 정보:")
        print(f"   종목코드: {stock_code}")
        print(f"   주문수량: {quantity}주")
        print(f"   주문가격: {current_price}원 (현재가)")
        print(f"   총 금액: {current_price * quantity:,}원")

        # 실제 주문 API (참고용 - 실제 실행하지 않음)
        """
        모의투자 매수 주문 API 구조:
        TR_ID: VTTC0802U (모의투자 현금매수주문)
        URL: /uapi/domestic-stock/v1/trading/order-cash

        필수 파라미터:
        - CANO: 계좌번호
        - ACNT_PRDT_CD: 계좌상품코드
        - PDNO: 종목코드
        - ORD_DVSN: 주문구분 (00:지정가)
        - ORD_QTY: 주문수량
        - ORD_UNPR: 주문단가
        """

        print(f"\n⚠️ 실제 주문은 실행하지 않습니다.")
        print(f"📝 모의투자 주문 API 정보:")
        print(f"   TR_ID: VTTC0802U")
        print(f"   URL: /uapi/domestic-stock/v1/trading/order-cash")
        print(f"   주문구분: 00 (지정가)")

        return True

    except Exception as e:
        print(f"❌ 주문 시뮬레이션 실패: {e}")
        return False


def create_mock_portfolio_data():
    """테스트용 Mock 포트폴리오 데이터 생성"""
    print("\n📊 테스트용 Mock 포트폴리오 데이터 생성")
    print("=" * 50)

    try:
        # 인기 종목들의 현재가 조회
        test_stocks = [
            ("005930", "삼성전자"),
            ("000660", "SK하이닉스"),
            ("035420", "NAVER")
        ]

        mock_portfolio = {
            "ctx_area_fk100": "",
            "ctx_area_nk100": "",
            "output1": [],
            "output2": [{
                "tot_evlu_amt": "0",
                "nass_amt": "10000000",  # 1천만원 현금
                "scts_evlu_amt": "0",
                "evlu_pfls_smtl_amt": "0",
                "pchs_amt_smtl_amt": "0"
            }],
            "rt_cd": "0",
            "msg_cd": "20310000",
            "msg1": "Mock 데이터 생성 완료"
        }

        print("📈 가상 보유종목 생성:")

        for stock_code, stock_name in test_stocks:
            current_price = check_current_price(stock_code)
            if current_price > 0:
                quantity = 10  # 각각 10주씩 보유한다고 가정
                eval_amt = current_price * quantity

                stock_data = {
                    "pdno": stock_code,
                    "prdt_name": stock_name,
                    "hldg_qty": str(quantity),
                    "pchs_avg_pric": str(current_price),
                    "prpr": str(current_price),
                    "evlu_amt": str(eval_amt),
                    "evlu_pfls_amt": "0",
                    "evlu_pfls_rt": "0.00"
                }

                mock_portfolio["output1"].append(stock_data)

                # 계좌 요약 업데이트
                current_total = int(mock_portfolio["output2"][0]["scts_evlu_amt"])
                mock_portfolio["output2"][0]["scts_evlu_amt"] = str(current_total + eval_amt)

                print(f"   ✅ {stock_name}: {quantity}주, {eval_amt:,}원")

        # 총 평가금액 계산
        stock_total = int(mock_portfolio["output2"][0]["scts_evlu_amt"])
        cash_total = int(mock_portfolio["output2"][0]["nass_amt"])
        total_amt = stock_total + cash_total

        mock_portfolio["output2"][0]["tot_evlu_amt"] = str(total_amt)
        mock_portfolio["output2"][0]["pchs_amt_smtl_amt"] = str(stock_total)

        print(f"\n💰 Mock 포트폴리오 요약:")
        print(f"   📈 주식평가: {stock_total:,}원")
        print(f"   💵 현금잔고: {cash_total:,}원")
        print(f"   💎 총 자산: {total_amt:,}원")

        # Mock 데이터 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"logs/mock_portfolio_{timestamp}.json"

        os.makedirs("logs", exist_ok=True)
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(mock_portfolio, f, indent=2, ensure_ascii=False)

        print(f"\n💾 Mock 데이터 저장: {filename}")

        return mock_portfolio

    except Exception as e:
        print(f"❌ Mock 데이터 생성 실패: {e}")
        return None


def test_mock_data_mapping():
    """Mock 데이터로 매핑 테스트"""
    print("\n🔄 Mock 데이터 매핑 테스트")
    print("=" * 40)

    try:
        # Mock 데이터 생성
        mock_data = create_mock_portfolio_data()
        if not mock_data:
            return False

        # state.py 모델로 변환
        sys.path.append('..')
        from src.state import StockInfo, PortfolioStatus

        stocks = []
        for stock_data in mock_data['output1']:
            stock_info = StockInfo(
                ticker=stock_data['pdno'],
                name=stock_data['prdt_name'],
                quantity=int(stock_data['hldg_qty']),
                avg_price=float(stock_data['pchs_avg_pric']),
                current_price=float(stock_data['prpr']),
                market_value=float(stock_data['evlu_amt']),
                profit_loss=float(stock_data['evlu_pfls_amt']),
                profit_loss_rate=float(stock_data['evlu_pfls_rt'])
            )
            stocks.append(stock_info)

        summary = mock_data['output2'][0]
        portfolio = PortfolioStatus(
            total_asset=float(summary['tot_evlu_amt']),
            total_investment=float(summary['pchs_amt_smtl_amt']),
            cash_balance=float(summary['nass_amt']),
            total_profit_loss=float(summary['evlu_pfls_amt']),
            total_profit_loss_rate=0.0,
            stocks=stocks,
            last_updated=datetime.now()
        )

        print(f"✅ Mock PortfolioStatus 생성 성공")
        print(f"   총자산: {portfolio.total_asset:,.0f}원")
        print(f"   보유종목: {len(portfolio.stocks)}개")

        for stock in portfolio.stocks:
            print(f"      - {stock.name}: {stock.quantity}주, {stock.market_value:,.0f}원")

        return portfolio

    except Exception as e:
        print(f"❌ Mock 데이터 매핑 실패: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """메인 실행"""
    print("🧪 KIS API 가상 트레이딩 테스트")
    print(f"⏰ 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # 1. 현재가 조회 테스트
    print("1️⃣ 현재가 조회 테스트")
    check_current_price("005930")

    # 2. 매수 주문 시뮬레이션
    print("\n2️⃣ 매수 주문 시뮬레이션")
    simulate_buy_order("005930", 10)

    # 3. Mock 포트폴리오 데이터 생성 및 매핑
    print("\n3️⃣ Mock 포트폴리오 테스트")
    mock_portfolio = test_mock_data_mapping()

    if mock_portfolio:
        print("\n🎉 가상 트레이딩 테스트 완료!")
        print("✅ 포트폴리오 데이터 구조 검증 성공")
    else:
        print("\n❌ 가상 트레이딩 테스트 실패")

    print(f"\n⏰ 완료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()