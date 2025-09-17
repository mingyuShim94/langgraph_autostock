"""
LV1 Observer - State 스키마 정의
LangGraph에서 사용할 상태(State) 객체를 정의합니다.
"""
from typing import Dict, List, Optional, Any
from typing_extensions import TypedDict
from datetime import datetime
from pydantic import BaseModel

class StockInfo(BaseModel):
    """개별 종목 정보"""
    ticker: str  # 종목코드
    name: str    # 종목명
    quantity: int  # 보유수량
    avg_price: float  # 평균단가
    current_price: float  # 현재가
    market_value: float  # 평가금액
    profit_loss: float   # 평가손익
    profit_loss_rate: float  # 수익률(%)

class PortfolioStatus(BaseModel):
    """포트폴리오 전체 상태"""
    total_asset: float  # 총자산
    total_investment: float  # 총투자원금
    cash_balance: float  # 현금잔고
    total_profit_loss: float  # 총평가손익
    total_profit_loss_rate: float  # 총수익률(%)
    stocks: List[StockInfo]  # 보유종목 리스트
    last_updated: datetime  # 마지막 업데이트 시간

class NewsItem(BaseModel):
    """개별 뉴스 아이템"""
    title: str  # 뉴스 제목
    link: str   # 뉴스 링크
    description: str  # 뉴스 요약
    pub_date: str  # 발행일
    ticker: str  # 관련 종목코드
    relevance_score: float  # 관련도 점수 (0.0-1.0)
    sentiment: Optional[str]  # 감정 분석 결과 ('positive', 'negative', 'neutral')

class NewsData(BaseModel):
    """뉴스 데이터 전체"""
    total_count: int  # 총 뉴스 개수
    news_by_ticker: Dict[str, List[NewsItem]]  # 종목별 뉴스
    market_news: List[NewsItem]  # 시장 전체 뉴스
    collected_at: datetime  # 수집 시간

class DailyReport(BaseModel):
    """일일 브리핑 리포트"""
    report_date: datetime  # 리포트 생성일
    portfolio_summary: str  # 포트폴리오 요약
    key_news_summary: str  # 주요 뉴스 요약
    market_impact_analysis: str  # 시장 영향 분석
    attention_points: List[str]  # 주의사항
    recommendations: List[str]  # 권장사항
    generated_by: str  # 생성 모델명
    confidence_score: float  # 신뢰도 점수

class ObserverState(TypedDict):
    """
    LV1 Observer의 중앙 상태 객체
    모든 노드에서 공유하는 데이터를 정의합니다.
    """

    # 포트폴리오 관련
    portfolio_status: Optional[PortfolioStatus]

    # 뉴스 관련
    news_data: Optional[NewsData]

    # 리포트 관련
    daily_report: Optional[DailyReport]

    # 메타데이터
    execution_id: str  # 실행 고유 ID
    start_time: datetime  # 실행 시작 시간
    current_step: str  # 현재 실행 중인 단계
    status: str  # 실행 상태 ('running', 'completed', 'error')
    error_message: Optional[str]  # 오류 메시지

    # 설정
    config: Dict[str, Any]  # 실행 설정

# 초기 상태 생성 함수
def create_initial_state(execution_id: str, config: Dict[str, Any] = None) -> ObserverState:
    """초기 상태 객체를 생성합니다."""
    return ObserverState(
        portfolio_status=None,
        news_data=None,
        daily_report=None,
        execution_id=execution_id,
        start_time=datetime.now(),
        current_step="initialized",
        status="running",
        error_message=None,
        config=config or {}
    )

# 상태 업데이트 헬퍼 함수들
def update_portfolio_status(state: ObserverState, portfolio: PortfolioStatus) -> ObserverState:
    """포트폴리오 상태를 업데이트합니다."""
    state["portfolio_status"] = portfolio
    state["current_step"] = "portfolio_updated"
    return state

def update_news_data(state: ObserverState, news: NewsData) -> ObserverState:
    """뉴스 데이터를 업데이트합니다."""
    state["news_data"] = news
    state["current_step"] = "news_updated"
    return state

def update_daily_report(state: ObserverState, report: DailyReport) -> ObserverState:
    """일일 리포트를 업데이트합니다."""
    state["daily_report"] = report
    state["current_step"] = "report_generated"
    state["status"] = "completed"
    return state

def update_error(state: ObserverState, error_message: str, step: str) -> ObserverState:
    """오류 상태를 업데이트합니다."""
    state["error_message"] = error_message
    state["current_step"] = step
    state["status"] = "error"
    return state

# 상태 검증 함수들
def validate_portfolio_status(portfolio: PortfolioStatus) -> bool:
    """포트폴리오 상태의 유효성을 검증합니다."""
    try:
        # 기본 검증
        assert portfolio.total_asset >= 0, "총자산은 0 이상이어야 합니다"
        assert portfolio.cash_balance >= 0, "현금잔고는 0 이상이어야 합니다"
        assert len(portfolio.stocks) >= 0, "보유종목은 0개 이상이어야 합니다"

        # 계산 검증
        calculated_market_value = sum(stock.market_value for stock in portfolio.stocks)
        total_with_cash = calculated_market_value + portfolio.cash_balance

        # 허용 오차 범위 (0.01% 이내)
        tolerance = max(total_with_cash * 0.0001, 1.0)
        assert abs(portfolio.total_asset - total_with_cash) <= tolerance, \
            f"총자산 계산 오류: {portfolio.total_asset} != {total_with_cash}"

        return True
    except AssertionError as e:
        print(f"포트폴리오 검증 실패: {e}")
        return False

def validate_news_data(news: NewsData) -> bool:
    """뉴스 데이터의 유효성을 검증합니다."""
    try:
        assert news.total_count >= 0, "뉴스 개수는 0 이상이어야 합니다"

        # 각 뉴스 아이템 검증
        total_news_count = 0
        for ticker, news_list in news.news_by_ticker.items():
            for news_item in news_list:
                assert 0.0 <= news_item.relevance_score <= 1.0, \
                    f"관련도 점수는 0.0-1.0 사이여야 합니다: {news_item.relevance_score}"
                total_news_count += 1

        total_news_count += len(news.market_news)

        # 총 개수 일치 확인 (약간의 오차 허용)
        assert abs(news.total_count - total_news_count) <= 5, \
            f"뉴스 개수 불일치: {news.total_count} != {total_news_count}"

        return True
    except AssertionError as e:
        print(f"뉴스 데이터 검증 실패: {e}")
        return False