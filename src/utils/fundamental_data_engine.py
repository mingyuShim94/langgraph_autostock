"""
펀더멘털 데이터 수집 및 구조화 엔진

재무제표, 공시 정보, 뉴스 데이터를 효율적으로 수집하고 구조화하는 시스템
KIS API와 Google Search를 활용한 다차원 데이터 수집
"""

import os
import sys
import time
import json
import logging
import hashlib
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

# KIS API 모듈 경로 추가
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
kis_path = os.path.join(project_root, 'open-trading-api-main/examples_user')
kis_domestic_path = os.path.join(project_root, 'open-trading-api-main/examples_user/domestic_stock')
kis_llm_path = os.path.join(project_root, 'open-trading-api-main/examples_llm/domestic_stock/finance_financial_ratio')

sys.path.extend([kis_path, kis_domestic_path, kis_llm_path])

try:
    import kis_auth as ka
    from finance_financial_ratio import finance_financial_ratio
    KIS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ KIS API 모듈 import 실패: {e}")
    print("KIS API 의존성이 없는 경우 mock 모드로 실행됩니다.")
    KIS_AVAILABLE = False


class DataQuality(Enum):
    """데이터 품질 등급"""
    HIGH = "high"      # 실시간 정확한 데이터
    MEDIUM = "medium"  # 캐시된 데이터 또는 일부 지연
    LOW = "low"        # Mock 데이터 또는 오래된 데이터
    UNKNOWN = "unknown"


@dataclass
class FinancialRatio:
    """재무비율 데이터 구조"""
    ticker: str
    company_name: str
    
    # 수익성 지표
    per: Optional[float] = None           # 주가수익비율
    pbr: Optional[float] = None           # 주가순자산비율
    roe: Optional[float] = None           # 자기자본이익률
    roa: Optional[float] = None           # 총자산이익률
    operating_margin: Optional[float] = None  # 영업이익률
    net_margin: Optional[float] = None    # 순이익률
    
    # 안정성 지표
    debt_ratio: Optional[float] = None    # 부채비율
    current_ratio: Optional[float] = None # 유동비율
    quick_ratio: Optional[float] = None   # 당좌비율
    
    # 성장성 지표
    revenue_growth: Optional[float] = None     # 매출 성장률
    profit_growth: Optional[float] = None      # 순이익 성장률
    
    # 배당 지표
    dividend_yield: Optional[float] = None     # 배당수익률
    dividend_payout: Optional[float] = None    # 배당성향
    
    # 메타데이터
    data_date: str = None                 # 데이터 기준일
    data_quality: DataQuality = DataQuality.UNKNOWN
    source: str = "unknown"              # 데이터 출처


@dataclass
class NewsData:
    """뉴스 데이터 구조"""
    ticker: str
    title: str
    summary: str
    published_date: str
    source: str
    sentiment_score: float = 0.0  # -1.0 (부정) ~ 1.0 (긍정)
    relevance_score: float = 0.0  # 0.0 ~ 1.0 (관련성)
    url: Optional[str] = None


@dataclass
class IndustryComparison:
    """동종업계 비교 데이터"""
    ticker: str
    industry_name: str
    industry_avg_per: Optional[float] = None
    industry_avg_pbr: Optional[float] = None
    industry_avg_roe: Optional[float] = None
    industry_avg_debt_ratio: Optional[float] = None
    rank_in_industry: Optional[int] = None
    total_companies: Optional[int] = None
    percentile: Optional[float] = None  # 업계 내 백분위수


@dataclass
class FundamentalData:
    """통합 펀더멘털 데이터"""
    ticker: str
    company_name: str
    financial_ratios: FinancialRatio
    news_data: List[NewsData]
    industry_comparison: IndustryComparison
    data_timestamp: str
    collection_time: float
    confidence_score: float = 0.0  # 0.0 ~ 1.0
    cache_key: str = None


class FundamentalDataEngine:
    """펀더멘털 데이터 수집 및 구조화 엔진"""
    
    # 한국 주요 업종 분류
    INDUSTRY_MAPPING = {
        "005930": "반도체",      # 삼성전자
        "000660": "반도체",      # SK하이닉스
        "035420": "화학",        # NAVER
        "035720": "화학",        # 카카오
        "207940": "자동차",      # 삼성바이오로직스
        "086960": "호텔/레저",   # 엔터프라이즈
        "096770": "IT서비스",    # SK이노베이션
        "055550": "은행",        # 신한지주
        "105560": "증권",        # KB금융
        "028260": "음식료",      # 삼성물산
        "000270": "항공운송",    # 기아
        "068270": "셀트리온",    # 셀트리온
        "323410": "카카오뱅크",  # 카카오뱅크
        "003670": "포스코홀딩스", # 포스코홀딩스
        "034730": "SK"           # SK
    }
    
    def __init__(self, cache_ttl_minutes: int = 5, mock_mode: bool = False):
        """
        펀더멘털 데이터 엔진 초기화
        
        Args:
            cache_ttl_minutes: 캐시 유효 시간 (분)
            mock_mode: Mock 모드 사용 여부
        """
        self.cache_ttl_minutes = cache_ttl_minutes
        self.mock_mode = mock_mode or not KIS_AVAILABLE
        self.cache = {}
        self.logger = logging.getLogger(__name__)
        
        # KIS API 인증 상태 확인
        self.kis_authenticated = False
        if not self.mock_mode:
            self._check_kis_authentication()
        
        # 연결 안정화를 위한 세션 설정
        self._setup_session()
    
    def _check_kis_authentication(self) -> bool:
        """KIS API 인증 상태 확인"""
        try:
            ka.auth(svr="vps", product="01")  # Paper trading 서버
            self.kis_authenticated = True
            self.logger.info("✅ KIS API 인증 성공")
            return True
        except Exception as e:
            self.logger.warning(f"⚠️ KIS API 인증 실패: {e}, Mock 모드로 전환")
            self.mock_mode = True
            self.kis_authenticated = False
            return False
    
    def _setup_session(self):
        """SSL 연결 안정화를 위한 세션 설정"""
        self.session = requests.Session()
        
        # SSL 설정 강화
        self.session.verify = True
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive'
        })
        
        # Retry 설정 (SSL 에러 포함)
        retry_strategy = Retry(
            total=3,  # 최대 3회 재시도
            backoff_factor=1,  # 재시도 간격 (1초, 2초, 4초)
            status_forcelist=[429, 500, 502, 503, 504],  # 재시도할 HTTP 상태 코드
            allowed_methods=["HEAD", "GET", "OPTIONS"]  # 재시도할 HTTP 메서드
        )
        
        # HTTP 어댑터 설정
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,  # Connection pool 크기
            pool_maxsize=20,     # 최대 연결 수
            pool_block=False     # Pool이 가득 찰 때 차단하지 않음
        )
        
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # 타임아웃 설정
        self.default_timeout = (10, 30)  # (connect_timeout, read_timeout)
    
    def _safe_api_call(self, api_func, *args, max_retries=3, **kwargs):
        """SSL 에러에 안전한 API 호출 래퍼"""
        for attempt in range(max_retries):
            try:
                # API 호출 전 Rate Limiting 방지를 위한 대기
                if attempt > 0:
                    wait_time = min(2 ** attempt, 10)  # Exponential backoff (최대 10초)
                    self.logger.info(f"재시도 {attempt + 1}/{max_retries}, {wait_time}초 대기 중...")
                    time.sleep(wait_time)
                else:
                    # 첫 호출도 안전한 간격 유지
                    time.sleep(1.0)
                
                # KIS API의 smart_sleep 활용
                if hasattr(ka, 'smart_sleep') and attempt > 0:
                    ka.smart_sleep()
                
                result = api_func(*args, **kwargs)
                return result
                
            except Exception as e:
                error_msg = str(e).lower()
                
                # SSL 관련 에러 감지
                if any(ssl_error in error_msg for ssl_error in [
                    'ssl', 'eof', 'connection', 'timeout', 'read timed out',
                    'unexpected_eof_while_reading', 'httpsconnectionpool'
                ]):
                    self.logger.warning(f"SSL/연결 에러 (시도 {attempt + 1}/{max_retries}): {e}")
                    
                    if attempt == max_retries - 1:
                        self.logger.error(f"최대 재시도 횟수 초과. API 호출 실패: {e}")
                        raise
                    continue
                    
                # Rate limiting 에러
                elif '초당 거래건수' in error_msg or 'rate limit' in error_msg:
                    self.logger.warning(f"Rate limit 에러 (시도 {attempt + 1}/{max_retries}): {e}")
                    wait_time = min(5 * (attempt + 1), 30)  # 5초씩 증가, 최대 30초
                    time.sleep(wait_time)
                    continue
                    
                # 기타 에러는 즉시 raise
                else:
                    self.logger.error(f"API 호출 실패: {e}")
                    raise
        
        # 모든 재시도 실패 시
        raise Exception(f"API 호출이 {max_retries}회 모두 실패했습니다.")
    
    def collect_fundamental_data(
        self, 
        ticker: str, 
        include_news: bool = True,
        include_industry_comparison: bool = True
    ) -> FundamentalData:
        """
        종목의 펀더멘털 데이터 종합 수집
        
        Args:
            ticker: 종목 코드
            include_news: 뉴스 데이터 포함 여부
            include_industry_comparison: 동종업계 비교 포함 여부
            
        Returns:
            FundamentalData: 통합 펀더멘털 데이터
        """
        start_time = time.time()
        cache_key = self._generate_cache_key(ticker, include_news, include_industry_comparison)
        
        # 캐시 확인
        cached_data = self._get_cached_data(cache_key)
        if cached_data:
            self.logger.info(f"📋 캐시에서 데이터 반환: {ticker}")
            return cached_data
        
        self.logger.info(f"🔍 펀더멘털 데이터 수집 시작: {ticker}")
        
        try:
            # 1. 재무비율 데이터 수집
            financial_ratios = self._collect_financial_ratios(ticker)
            
            # 2. 뉴스 데이터 수집 (선택적)
            news_data = []
            if include_news:
                news_data = self._collect_news_data(ticker)
            
            # 3. 동종업계 비교 데이터 (선택적)
            industry_comparison = None
            if include_industry_comparison:
                industry_comparison = self._collect_industry_comparison(ticker)
            
            # 4. 통합 데이터 구성
            collection_time = time.time() - start_time
            confidence_score = self._calculate_confidence_score(
                financial_ratios, news_data, industry_comparison
            )
            
            fundamental_data = FundamentalData(
                ticker=ticker,
                company_name=financial_ratios.company_name,
                financial_ratios=financial_ratios,
                news_data=news_data,
                industry_comparison=industry_comparison,
                data_timestamp=datetime.now().isoformat(),
                collection_time=collection_time,
                confidence_score=confidence_score,
                cache_key=cache_key
            )
            
            # 캐시 저장
            self._save_to_cache(cache_key, fundamental_data)
            
            self.logger.info(f"✅ 데이터 수집 완료: {ticker} ({collection_time:.2f}초)")
            return fundamental_data
            
        except Exception as e:
            self.logger.error(f"❌ 데이터 수집 실패: {ticker} - {e}")
            # 실패 시 Mock 데이터 반환
            return self._generate_mock_fundamental_data(ticker)
    
    def _collect_financial_ratios(self, ticker: str) -> FinancialRatio:
        """재무비율 데이터 수집"""
        if self.mock_mode or not self.kis_authenticated:
            return self._generate_mock_financial_ratios(ticker)
        
        try:
            # SSL 안전한 KIS API 호출
            financial_data = self._safe_api_call(
                finance_financial_ratio,
                fid_div_cls_code="0",  # 0: 년도별 데이터
                fid_cond_mrkt_div_code="J",  # J: 코스피/코스닥
                fid_input_iscd=ticker
            )
            
            if financial_data is not None and not financial_data.empty:
                # DataFrame에서 최신 데이터 추출
                latest_data = financial_data.iloc[0] if len(financial_data) > 0 else None
                
                if latest_data is not None:
                    return self._parse_kis_financial_data(ticker, latest_data)
            
            # 데이터가 없으면 Mock 데이터 반환
            self.logger.warning(f"⚠️ KIS API에서 데이터 없음, Mock 데이터 사용: {ticker}")
            return self._generate_mock_financial_ratios(ticker)
            
        except Exception as e:
            self.logger.error(f"❌ KIS API 재무 데이터 수집 실패: {ticker} - {e}")
            return self._generate_mock_financial_ratios(ticker)
    
    def _parse_kis_financial_data(self, ticker: str, data: Any) -> FinancialRatio:
        """KIS API 데이터를 FinancialRatio 객체로 변환"""
        company_name = f"Company_{ticker}"  # KIS API에서 회사명 추출
        
        # 안전한 숫자 변환 함수
        def safe_float(value, default=None):
            try:
                if value is None or value == '' or value == '0':
                    return default
                return float(str(value).replace(',', ''))
            except:
                return default
        
        return FinancialRatio(
            ticker=ticker,
            company_name=company_name,
            per=safe_float(getattr(data, 'per', None)),
            pbr=safe_float(getattr(data, 'pbr', None)),
            roe=safe_float(getattr(data, 'roe', None)),
            roa=safe_float(getattr(data, 'roa', None)),
            operating_margin=safe_float(getattr(data, 'operating_margin', None)),
            net_margin=safe_float(getattr(data, 'net_margin', None)),
            debt_ratio=safe_float(getattr(data, 'debt_ratio', None)),
            current_ratio=safe_float(getattr(data, 'current_ratio', None)),
            quick_ratio=safe_float(getattr(data, 'quick_ratio', None)),
            revenue_growth=safe_float(getattr(data, 'revenue_growth', None)),
            profit_growth=safe_float(getattr(data, 'profit_growth', None)),
            dividend_yield=safe_float(getattr(data, 'dividend_yield', None)),
            dividend_payout=safe_float(getattr(data, 'dividend_payout', None)),
            data_date=datetime.now().strftime("%Y-%m-%d"),
            data_quality=DataQuality.HIGH,
            source="KIS_API"
        )
    
    def _collect_news_data(self, ticker: str) -> List[NewsData]:
        """뉴스 데이터 수집 (Mock 구현)"""
        # 실제 구현에서는 Gemini Google Search로 뉴스 수집
        # 여기서는 Mock 데이터 생성
        company_name = f"Company_{ticker}"
        
        mock_news = [
            NewsData(
                ticker=ticker,
                title=f"{company_name} 3분기 실적 발표, 예상치 상회",
                summary=f"{company_name}가 3분기 매출과 영업이익이 시장 예상을 상회했다고 발표했다.",
                published_date=(datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),
                source="한국경제",
                sentiment_score=0.7,
                relevance_score=0.9,
                url=f"https://example.com/news/{ticker}/1"
            ),
            NewsData(
                ticker=ticker,
                title=f"{company_name} 신규 투자 계획 발표",
                summary=f"{company_name}가 차세대 기술 개발을 위한 대규모 투자 계획을 발표했다.",
                published_date=(datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d"),
                source="매일경제",
                sentiment_score=0.5,
                relevance_score=0.8,
                url=f"https://example.com/news/{ticker}/2"
            ),
            NewsData(
                ticker=ticker,
                title=f"증권사, {company_name} 목표주가 상향 조정",
                summary=f"주요 증권사들이 {company_name}의 목표주가를 일제히 상향 조정했다.",
                published_date=(datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d"),
                source="이데일리",
                sentiment_score=0.8,
                relevance_score=0.7,
                url=f"https://example.com/news/{ticker}/3"
            )
        ]
        
        return mock_news
    
    def _collect_industry_comparison(self, ticker: str) -> IndustryComparison:
        """동종업계 비교 데이터 수집"""
        industry_name = self.INDUSTRY_MAPPING.get(ticker, "기타")
        
        # Mock 동종업계 데이터 생성
        return IndustryComparison(
            ticker=ticker,
            industry_name=industry_name,
            industry_avg_per=15.2,
            industry_avg_pbr=1.3,
            industry_avg_roe=8.5,
            industry_avg_debt_ratio=35.0,
            rank_in_industry=12,
            total_companies=45,
            percentile=73.3
        )
    
    def _generate_mock_financial_ratios(self, ticker: str) -> FinancialRatio:
        """Mock 재무비율 데이터 생성"""
        import random
        random.seed(hash(ticker) % 1000)  # 종목별 일관된 데이터
        
        company_name = f"Company_{ticker}"
        
        return FinancialRatio(
            ticker=ticker,
            company_name=company_name,
            per=round(random.uniform(8.0, 25.0), 1),
            pbr=round(random.uniform(0.8, 3.0), 2),
            roe=round(random.uniform(5.0, 20.0), 1),
            roa=round(random.uniform(3.0, 15.0), 1),
            operating_margin=round(random.uniform(5.0, 25.0), 1),
            net_margin=round(random.uniform(3.0, 20.0), 1),
            debt_ratio=round(random.uniform(20.0, 60.0), 1),
            current_ratio=round(random.uniform(1.0, 3.0), 2),
            quick_ratio=round(random.uniform(0.8, 2.5), 2),
            revenue_growth=round(random.uniform(-10.0, 30.0), 1),
            profit_growth=round(random.uniform(-15.0, 40.0), 1),
            dividend_yield=round(random.uniform(0.0, 5.0), 2),
            dividend_payout=round(random.uniform(10.0, 60.0), 1),
            data_date=datetime.now().strftime("%Y-%m-%d"),
            data_quality=DataQuality.LOW,
            source="MOCK_DATA"
        )
    
    def _generate_mock_fundamental_data(self, ticker: str) -> FundamentalData:
        """실패 시 Mock 펀더멘털 데이터 생성"""
        financial_ratios = self._generate_mock_financial_ratios(ticker)
        news_data = self._collect_news_data(ticker)
        industry_comparison = self._collect_industry_comparison(ticker)
        
        return FundamentalData(
            ticker=ticker,
            company_name=financial_ratios.company_name,
            financial_ratios=financial_ratios,
            news_data=news_data,
            industry_comparison=industry_comparison,
            data_timestamp=datetime.now().isoformat(),
            collection_time=0.1,
            confidence_score=0.3,  # Mock 데이터는 낮은 신뢰도
            cache_key=f"mock_{ticker}"
        )
    
    def _calculate_confidence_score(
        self, 
        financial_ratios: FinancialRatio,
        news_data: List[NewsData],
        industry_comparison: Optional[IndustryComparison]
    ) -> float:
        """데이터 신뢰도 점수 계산"""
        score = 0.0
        
        # 재무 데이터 품질 (50%)
        if financial_ratios.data_quality == DataQuality.HIGH:
            score += 0.5
        elif financial_ratios.data_quality == DataQuality.MEDIUM:
            score += 0.3
        elif financial_ratios.data_quality == DataQuality.LOW:
            score += 0.1
        
        # 뉴스 데이터 신선도 (30%)
        if news_data:
            recent_news = sum(1 for news in news_data 
                            if (datetime.now() - datetime.fromisoformat(news.published_date + "T00:00:00")).days <= 7)
            news_score = min(recent_news / 3, 1.0) * 0.3
            score += news_score
        
        # 업계 비교 데이터 (20%)
        if industry_comparison:
            score += 0.2
        
        return round(score, 3)
    
    def _generate_cache_key(self, ticker: str, include_news: bool, include_industry: bool) -> str:
        """캐시 키 생성"""
        key_data = f"{ticker}_{include_news}_{include_industry}_{datetime.now().strftime('%Y%m%d%H%M')}"
        return hashlib.md5(key_data.encode()).hexdigest()[:16]
    
    def _get_cached_data(self, cache_key: str) -> Optional[FundamentalData]:
        """캐시에서 데이터 조회"""
        if cache_key in self.cache:
            data, timestamp = self.cache[cache_key]
            
            # TTL 확인
            if (datetime.now() - timestamp).total_seconds() / 60 < self.cache_ttl_minutes:
                return data
            else:
                # 만료된 캐시 삭제
                del self.cache[cache_key]
        
        return None
    
    def _save_to_cache(self, cache_key: str, data: FundamentalData) -> None:
        """데이터를 캐시에 저장"""
        self.cache[cache_key] = (data, datetime.now())
        
        # 캐시 크기 제한 (최대 100개)
        if len(self.cache) > 100:
            # 가장 오래된 캐시 삭제
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k][1])
            del self.cache[oldest_key]
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """캐시 통계 정보 반환"""
        total_cached = len(self.cache)
        
        if total_cached == 0:
            return {
                "total_cached_items": 0,
                "cache_hit_rate": 0.0,
                "average_age_minutes": 0.0
            }
        
        # 평균 캐시 연령 계산
        now = datetime.now()
        ages = [(now - timestamp).total_seconds() / 60 for _, timestamp in self.cache.values()]
        avg_age = sum(ages) / len(ages) if ages else 0.0
        
        return {
            "total_cached_items": total_cached,
            "cache_ttl_minutes": self.cache_ttl_minutes,
            "average_age_minutes": round(avg_age, 2),
            "mock_mode": self.mock_mode,
            "kis_authenticated": self.kis_authenticated
        }
    
    def clear_cache(self) -> None:
        """캐시 초기화"""
        self.cache.clear()
        self.logger.info("🗑️ 캐시 초기화 완료")
    
    def batch_collect_data(self, tickers: List[str], max_concurrent: int = 5) -> Dict[str, FundamentalData]:
        """여러 종목의 데이터를 배치로 수집"""
        results = {}
        
        self.logger.info(f"🔄 배치 데이터 수집 시작: {len(tickers)}개 종목")
        
        for i in range(0, len(tickers), max_concurrent):
            batch = tickers[i:i + max_concurrent]
            
            for ticker in batch:
                try:
                    results[ticker] = self.collect_fundamental_data(ticker)
                    time.sleep(0.1)  # API 부하 방지
                except Exception as e:
                    self.logger.error(f"❌ 배치 수집 실패: {ticker} - {e}")
                    results[ticker] = self._generate_mock_fundamental_data(ticker)
        
        self.logger.info(f"✅ 배치 수집 완료: {len(results)}개 종목")
        return results


# 편의 함수들
def collect_single_ticker_data(ticker: str, mock_mode: bool = False) -> FundamentalData:
    """단일 종목 데이터 수집 편의 함수"""
    engine = FundamentalDataEngine(mock_mode=mock_mode)
    return engine.collect_fundamental_data(ticker)


def collect_multiple_tickers_data(tickers: List[str], mock_mode: bool = False) -> Dict[str, FundamentalData]:
    """복수 종목 데이터 수집 편의 함수"""
    engine = FundamentalDataEngine(mock_mode=mock_mode)
    return engine.batch_collect_data(tickers)


if __name__ == "__main__":
    # 테스트 실행
    logging.basicConfig(level=logging.INFO)
    
    # 단일 종목 테스트
    print("🧪 단일 종목 테스트: 삼성전자 (005930)")
    data = collect_single_ticker_data("005930", mock_mode=True)
    print(f"✅ 수집 완료: {data.company_name}")
    print(f"📊 재무 지표: PER={data.financial_ratios.per}, PBR={data.financial_ratios.pbr}")
    print(f"📰 뉴스 개수: {len(data.news_data)}개")
    print(f"🎯 신뢰도: {data.confidence_score}")
    
    # 배치 테스트
    print("\n🧪 배치 테스트: 3개 종목")
    tickers = ["005930", "000660", "035420"]
    batch_data = collect_multiple_tickers_data(tickers, mock_mode=True)
    print(f"✅ 배치 수집 완료: {len(batch_data)}개 종목")