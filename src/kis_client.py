"""
KIS API Client
한국투자증권 API 통합 클라이언트 모듈
LangGraph 노드에서 사용할 수 있는 고수준 인터페이스 제공
"""
import json
import requests
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from .kis_auth import authenticate
from .state import StockInfo, PortfolioStatus


@dataclass
class MarketData:
    """시장 데이터 모델"""
    ticker: str
    name: str
    current_price: float
    change_rate: float
    volume: int
    market_cap: Optional[float] = None
    last_updated: datetime = None


class KISAPIError(Exception):
    """KIS API 관련 예외"""
    def __init__(self, message: str, error_code: str = None, status_code: int = None):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        super().__init__(self.message)


class KISClient:
    """
    KIS API 통합 클라이언트

    LangGraph 노드에서 사용할 수 있는 고수준 API 제공:
    - 포트폴리오 조회
    - 종목 시세 조회
    - 주문 실행 (모의투자)
    - 계좌 정보 조회
    """

    def __init__(self, environment: str = 'paper'):
        """
        KIS 클라이언트 초기화

        Args:
            environment: 'paper' (모의투자) 또는 'real' (실투자)
        """
        self.environment = environment
        self.auth = None
        self._initialize_auth()

    def _initialize_auth(self):
        """인증 초기화"""
        try:
            self.auth = authenticate(self.environment)
        except Exception as e:
            raise KISAPIError(f"Authentication failed: {e}")

    def get_portfolio_status(self) -> PortfolioStatus:
        """
        포트폴리오 상태 조회

        Returns:
            PortfolioStatus: 포트폴리오 상태 객체

        Raises:
            KISAPIError: API 호출 실패 시
        """
        try:
            # 모의투자용 TR_ID
            tr_id = "VTTC8434R"
            url = f"{self.auth.tr_env.my_url}/uapi/domestic-stock/v1/trading/inquire-balance"

            headers = {
                "Content-Type": "application/json",
                "Accept": "text/plain",
                "charset": "UTF-8",
                "User-Agent": self.auth.config['my_agent'],
                "authorization": f"Bearer {self.auth.token_cache}",
                "appkey": self.auth.tr_env.my_app,
                "appsecret": self.auth.tr_env.my_sec,
                "tr_id": tr_id,
                "custtype": "P"
            }

            params = {
                "CANO": self.auth.tr_env.my_acct,
                "ACNT_PRDT_CD": self.auth.tr_env.my_prod,
                "AFHR_FLPR_YN": "N",
                "OFL_YN": "",
                "INQR_DVSN": "02",  # 종목별
                "UNPR_DVSN": "01",
                "FUND_STTL_ICLD_YN": "N",
                "FNCG_AMT_AUTO_RDPT_YN": "N",
                "PRCS_DVSN": "01",
                "CTX_AREA_FK100": "",
                "CTX_AREA_NK100": ""
            }

            response = requests.get(url, headers=headers, params=params, timeout=15)

            if response.status_code != 200:
                raise KISAPIError(
                    f"Portfolio inquiry failed: {response.status_code}",
                    status_code=response.status_code
                )

            result = response.json()

            if result.get('rt_cd') != '0':
                raise KISAPIError(
                    f"API error: {result.get('msg1', 'Unknown error')}",
                    error_code=result.get('msg_cd')
                )

            return self._parse_portfolio_response(result)

        except requests.RequestException as e:
            raise KISAPIError(f"Network error during portfolio inquiry: {e}")
        except Exception as e:
            raise KISAPIError(f"Unexpected error during portfolio inquiry: {e}")

    def _parse_portfolio_response(self, response: Dict[str, Any]) -> PortfolioStatus:
        """포트폴리오 응답 데이터 파싱"""
        stocks = []

        # 보유종목 파싱
        if 'output1' in response:
            for stock_data in response['output1']:
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
                except (ValueError, TypeError) as e:
                    # 개별 종목 파싱 실패는 로그만 남기고 계속 진행
                    print(f"Warning: Failed to parse stock data: {e}")

        # 계좌 요약 파싱
        summary = response.get('output2', [{}])[0] if response.get('output2') else {}

        portfolio = PortfolioStatus(
            total_asset=float(summary.get('tot_evlu_amt', '0')),
            total_investment=float(summary.get('pchs_amt_smtl_amt', '0')),
            cash_balance=float(summary.get('nass_amt', '0')),
            total_profit_loss=float(summary.get('evlu_pfls_smtl_amt', '0')),
            total_profit_loss_rate=self._calculate_profit_loss_rate(
                float(summary.get('evlu_pfls_smtl_amt', '0')),
                float(summary.get('pchs_amt_smtl_amt', '0'))
            ),
            stocks=stocks,
            last_updated=datetime.now()
        )

        return portfolio

    def _calculate_profit_loss_rate(self, profit_loss: float, investment: float) -> float:
        """수익률 계산"""
        if investment == 0:
            return 0.0
        return round((profit_loss / investment) * 100, 2)

    def get_stock_price(self, ticker: str) -> MarketData:
        """
        종목 현재가 조회

        Args:
            ticker: 종목코드 (예: '005930')

        Returns:
            MarketData: 주식 시세 데이터

        Raises:
            KISAPIError: API 호출 실패 시
        """
        try:
            url = f"{self.auth.tr_env.my_url}/uapi/domestic-stock/v1/quotations/inquire-price"

            headers = {
                "Content-Type": "application/json",
                "Accept": "text/plain",
                "charset": "UTF-8",
                "User-Agent": self.auth.config['my_agent'],
                "authorization": f"Bearer {self.auth.token_cache}",
                "appkey": self.auth.tr_env.my_app,
                "appsecret": self.auth.tr_env.my_sec,
                "tr_id": "FHKST01010100",
                "custtype": "P"
            }

            params = {
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": ticker
            }

            response = requests.get(url, headers=headers, params=params, timeout=10)

            if response.status_code != 200:
                raise KISAPIError(
                    f"Stock price inquiry failed for {ticker}: {response.status_code}",
                    status_code=response.status_code
                )

            result = response.json()

            if 'output' not in result:
                raise KISAPIError(f"Invalid response format for stock {ticker}")

            output = result['output']

            return MarketData(
                ticker=ticker,
                name=output.get('prdt_abrv_name', 'N/A'),
                current_price=float(output.get('stck_prpr', '0')),
                change_rate=float(output.get('prdy_ctrt', '0')),
                volume=int(output.get('acml_vol', '0')),
                last_updated=datetime.now()
            )

        except requests.RequestException as e:
            raise KISAPIError(f"Network error during stock price inquiry for {ticker}: {e}")
        except (ValueError, TypeError) as e:
            raise KISAPIError(f"Data parsing error for stock {ticker}: {e}")
        except Exception as e:
            raise KISAPIError(f"Unexpected error during stock price inquiry for {ticker}: {e}")

    def get_multiple_stock_prices(self, tickers: List[str]) -> Dict[str, MarketData]:
        """
        여러 종목 현재가 일괄 조회

        Args:
            tickers: 종목코드 리스트

        Returns:
            Dict[str, MarketData]: 종목코드별 시세 데이터
        """
        results = {}

        for ticker in tickers:
            try:
                market_data = self.get_stock_price(ticker)
                results[ticker] = market_data
            except KISAPIError as e:
                print(f"Warning: Failed to get price for {ticker}: {e.message}")
                # 실패한 종목은 결과에서 제외
                continue

        return results

    def get_account_summary(self) -> Dict[str, Any]:
        """
        계좌 요약 정보 조회

        Returns:
            Dict: 계좌 요약 정보
        """
        portfolio = self.get_portfolio_status()

        return {
            "account_number": self.auth.tr_env.my_acct,
            "total_asset": portfolio.total_asset,
            "cash_balance": portfolio.cash_balance,
            "stock_value": portfolio.total_asset - portfolio.cash_balance,
            "total_profit_loss": portfolio.total_profit_loss,
            "profit_loss_rate": portfolio.total_profit_loss_rate,
            "stock_count": len(portfolio.stocks),
            "last_updated": portfolio.last_updated.isoformat()
        }

    def is_market_open(self) -> bool:
        """
        시장 개장 여부 확인

        Returns:
            bool: 시장 개장 여부
        """
        # 간단한 구현: 평일 9시-15시30분을 개장시간으로 가정
        now = datetime.now()

        # 주말 체크
        if now.weekday() >= 5:  # 토요일(5), 일요일(6)
            return False

        # 시간 체크
        market_open = now.replace(hour=9, minute=0, second=0, microsecond=0)
        market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)

        return market_open <= now <= market_close

    def validate_connection(self) -> bool:
        """
        API 연결 상태 검증

        Returns:
            bool: 연결 성공 여부
        """
        try:
            # 인증 토큰이 있는지만 확인 (API 호출은 실제 사용 시에만)
            return self.auth is not None and self.auth.token_cache is not None
        except Exception:
            return False


def create_kis_client(environment: str = 'paper') -> KISClient:
    """
    KIS 클라이언트 팩토리 함수

    Args:
        environment: 'paper' (모의투자) 또는 'real' (실투자)

    Returns:
        KISClient: 초기화된 KIS 클라이언트
    """
    return KISClient(environment=environment)


# LangGraph 노드에서 사용할 편의 함수들
def fetch_portfolio_status(environment: str = 'paper') -> PortfolioStatus:
    """
    포트폴리오 상태 조회 (LangGraph 노드용)

    Args:
        environment: API 환경

    Returns:
        PortfolioStatus: 포트폴리오 상태
    """
    client = create_kis_client(environment)
    return client.get_portfolio_status()


def fetch_stock_prices(tickers: List[str], environment: str = 'paper') -> Dict[str, MarketData]:
    """
    종목 시세 조회 (LangGraph 노드용)

    Args:
        tickers: 종목코드 리스트
        environment: API 환경

    Returns:
        Dict[str, MarketData]: 종목별 시세 데이터
    """
    client = create_kis_client(environment)
    return client.get_multiple_stock_prices(tickers)


def validate_kis_connection(environment: str = 'paper') -> bool:
    """
    KIS API 연결 검증 (LangGraph 노드용)

    Args:
        environment: API 환경

    Returns:
        bool: 연결 성공 여부
    """
    try:
        client = create_kis_client(environment)
        return client.validate_connection()
    except Exception:
        return False