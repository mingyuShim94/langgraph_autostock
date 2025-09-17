"""
KIS Client 통합 테스트
LangGraph 노드에서 사용할 KIS 클라이언트 모듈 검증
"""
import os
import sys
from datetime import datetime

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.kis_client import (
    KISClient,
    create_kis_client,
    fetch_portfolio_status,
    fetch_stock_prices,
    validate_kis_connection,
    KISAPIError
)


def test_kis_client_creation():
    """KIS 클라이언트 생성 테스트"""
    print("🔧 KIS 클라이언트 생성 테스트")
    print("-" * 40)

    try:
        # 직접 생성
        client = KISClient(environment='paper')
        print(f"✅ 직접 생성 성공: {client.environment}")

        # 팩토리 함수 사용
        client2 = create_kis_client('paper')
        print(f"✅ 팩토리 생성 성공: {client2.environment}")

        return True
    except Exception as e:
        print(f"❌ 클라이언트 생성 실패: {e}")
        return False


def test_connection_validation():
    """연결 검증 테스트"""
    print("\n🔍 연결 검증 테스트")
    print("-" * 40)

    try:
        # 편의 함수 사용
        is_connected = validate_kis_connection('paper')
        print(f"✅ 연결 상태: {'성공' if is_connected else '실패'}")

        # 클라이언트 직접 사용
        client = create_kis_client('paper')
        is_connected2 = client.validate_connection()
        print(f"✅ 직접 검증: {'성공' if is_connected2 else '실패'}")

        return is_connected or is_connected2
    except Exception as e:
        print(f"❌ 연결 검증 실패: {e}")
        return False


def test_stock_price_inquiry():
    """종목 시세 조회 테스트"""
    print("\n📈 종목 시세 조회 테스트")
    print("-" * 40)

    try:
        client = create_kis_client('paper')

        # 단일 종목 조회
        print("📊 삼성전자 (005930) 조회:")
        market_data = client.get_stock_price('005930')
        print(f"   종목명: {market_data.name}")
        print(f"   현재가: {market_data.current_price:,}원")
        print(f"   등락률: {market_data.change_rate}%")
        print(f"   거래량: {market_data.volume:,}")

        # 다중 종목 조회 (편의 함수)
        print("\n📊 다중 종목 조회:")
        tickers = ['005930', '000660', '035420']
        prices = fetch_stock_prices(tickers, 'paper')

        for ticker, data in prices.items():
            print(f"   {ticker} ({data.name}): {data.current_price:,}원 ({data.change_rate:+.2f}%)")

        return True
    except KISAPIError as e:
        print(f"❌ API 오류: {e.message}")
        return False
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")
        return False


def test_portfolio_inquiry():
    """포트폴리오 조회 테스트"""
    print("\n💼 포트폴리오 조회 테스트")
    print("-" * 40)

    try:
        # 편의 함수 사용
        portfolio = fetch_portfolio_status('paper')

        print(f"💰 총 자산: {portfolio.total_asset:,.0f}원")
        print(f"💵 현금잔고: {portfolio.cash_balance:,.0f}원")
        print(f"📈 투자금액: {portfolio.total_investment:,.0f}원")
        print(f"📊 평가손익: {portfolio.total_profit_loss:,.0f}원 ({portfolio.total_profit_loss_rate:+.2f}%)")
        print(f"📦 보유종목: {len(portfolio.stocks)}개")

        if portfolio.stocks:
            print("\n📈 보유종목 상세:")
            for stock in portfolio.stocks[:5]:  # 최대 5개만 표시
                print(f"   {stock.name} ({stock.ticker}): {stock.quantity}주")
                print(f"      현재가: {stock.current_price:,}원")
                print(f"      평가금액: {stock.market_value:,}원")
                print(f"      손익: {stock.profit_loss:+,.0f}원 ({stock.profit_loss_rate:+.2f}%)")
        else:
            print("   📝 보유종목이 없습니다.")

        # 클라이언트 직접 사용으로도 테스트
        client = create_kis_client('paper')
        account_summary = client.get_account_summary()
        print(f"\n🏦 계좌 요약:")
        print(f"   계좌번호: {account_summary['account_number']}")
        print(f"   총자산: {account_summary['total_asset']:,.0f}원")
        print(f"   주식가치: {account_summary['stock_value']:,.0f}원")
        print(f"   보유종목수: {account_summary['stock_count']}개")

        return True
    except KISAPIError as e:
        print(f"❌ API 오류: {e.message}")
        return False
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_market_status():
    """시장 상태 조회 테스트"""
    print("\n🕒 시장 상태 조회 테스트")
    print("-" * 40)

    try:
        client = create_kis_client('paper')
        is_open = client.is_market_open()

        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"📅 현재 시각: {current_time}")
        print(f"🏪 시장 상태: {'개장' if is_open else '휴장'}")

        return True
    except Exception as e:
        print(f"❌ 시장 상태 조회 실패: {e}")
        return False


def main():
    """통합 테스트 실행"""
    print("🧪 KIS Client 통합 테스트 시작")
    print(f"⏰ 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    test_results = []

    # 1. 클라이언트 생성 테스트
    result1 = test_kis_client_creation()
    test_results.append(("클라이언트 생성", result1))

    # 2. 연결 검증 테스트
    result2 = test_connection_validation()
    test_results.append(("연결 검증", result2))

    # 3. 종목 시세 조회 테스트
    result3 = test_stock_price_inquiry()
    test_results.append(("종목 시세 조회", result3))

    # 4. 포트폴리오 조회 테스트
    result4 = test_portfolio_inquiry()
    test_results.append(("포트폴리오 조회", result4))

    # 5. 시장 상태 조회 테스트
    result5 = test_market_status()
    test_results.append(("시장 상태 조회", result5))

    # 결과 요약
    print("\n" + "=" * 60)
    print("📊 테스트 결과 요약")
    print("-" * 60)

    passed = 0
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<20} {status}")
        if result:
            passed += 1

    success_rate = (passed / len(test_results)) * 100
    print(f"\n🎯 성공률: {passed}/{len(test_results)} ({success_rate:.1f}%)")

    if success_rate >= 80:
        print("🎉 KIS Client 통합 테스트 성공!")
        print("✅ LangGraph 노드 통합 준비 완료")
        return True
    else:
        print("❌ KIS Client 통합 테스트 실패")
        print("🔧 문제를 해결한 후 다시 시도하세요")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)