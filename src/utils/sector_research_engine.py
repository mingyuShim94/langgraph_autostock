"""
섹터 리서치 엔진

실시간 웹 검색을 통한 섹터 트렌드 분석 및 유망 섹터 발굴을 지원하는 엔진
Perplexity sonar-pro 모델의 검색 기능을 최대 활용하여 정확하고 최신의 섹터 분석 제공
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class SectorCategory(Enum):
    """주요 섹터 카테고리"""
    TECHNOLOGY = "기술주"
    FINANCE = "금융"
    HEALTHCARE = "헬스케어"
    ENERGY = "에너지"
    MATERIALS = "소재"
    CONSUMER_DISCRETIONARY = "경기소비재"
    CONSUMER_STAPLES = "필수소비재"
    INDUSTRIALS = "산업재"
    UTILITIES = "유틸리티"
    REAL_ESTATE = "부동산"
    TELECOMMUNICATIONS = "통신"
    AUTOMOBILES = "자동차"
    CHEMICALS = "화학"
    CONSTRUCTION = "건설"
    ENTERTAINMENT = "엔터테인먼트"
    FOOD_BEVERAGE = "식음료"
    RETAIL = "유통"
    SHIPPING = "해운항공"
    SEMICONDUCTORS = "반도체"


@dataclass
class SectorMetrics:
    """섹터 분석 지표"""
    sector_name: str
    trend_score: float  # 0-100점 트렌드 점수
    sentiment_score: float  # -1 ~ 1 뉴스 감정 점수
    momentum_score: float  # 0-100점 모멘텀 점수
    policy_impact: float  # -1 ~ 1 정책 영향도
    relative_strength: float  # 0-100점 상대 강도
    opportunity_level: str  # "낮음", "보통", "높음", "매우높음"
    risk_level: str  # "낮음", "보통", "높음"
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return asdict(self)


@dataclass
class SectorOpportunity:
    """섹터 투자 기회"""
    sector_name: str
    opportunity_type: str  # "정책수혜", "기술혁신", "시장확대", "구조변화"
    description: str
    confidence_level: float  # 0-1 신뢰도
    time_horizon: str  # "단기", "중기", "장기"
    expected_impact: str  # "낮음", "보통", "높음"
    key_catalysts: List[str]  # 주요 촉매 요인
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return asdict(self)


@dataclass
class RotationSignal:
    """섹터 로테이션 신호"""
    from_sector: str
    to_sector: str
    signal_strength: float  # 0-1 신호 강도
    reasoning: str
    timing: str  # "즉시", "단기", "중기"
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return asdict(self)


@dataclass
class SectorResearchResult:
    """섹터 리서치 결과"""
    research_timestamp: datetime
    analysis_period: str
    sector_rankings: List[SectorMetrics]
    top_opportunities: List[SectorOpportunity]
    rotation_signals: List[RotationSignal]
    market_overview: str
    confidence_indicators: Dict[str, float]
    data_sources: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        result = asdict(self)
        result['research_timestamp'] = self.research_timestamp.isoformat()
        return result


class SectorResearchEngine:
    """섹터 리서치 엔진"""
    
    # 19개 주요 섹터 정의
    MAJOR_SECTORS = {
        "기술주": ["삼성전자", "SK하이닉스", "NAVER", "카카오", "LG전자"],
        "금융": ["삼성생명", "KB금융", "신한지주", "하나금융그룹", "우리금융그룹"],
        "헬스케어": ["삼성바이오로직스", "셀트리온", "유한양행", "대웅제약", "한미약품"],
        "에너지": ["SK이노베이션", "GS", "한국전력", "SK가스", "S-Oil"],
        "소재": ["POSCO홀딩스", "LG화학", "롯데케미칼", "효성", "코오롱인더"],
        "경기소비재": ["현대차", "기아", "LG생활건강", "아모레퍼시픽", "현대글로비스"],
        "필수소비재": ["CJ제일제당", "오리온", "농심", "롯데제과", "해태제과"],
        "산업재": ["두산에너빌리티", "HD현대", "삼성중공업", "현대건설", "GS건설"],
        "유틸리티": ["한국전력", "한국가스공사", "K-water", "한전KPS", "KEPCO"],
        "부동산": ["롯데리츠", "신한알파리츠", "맥쿼리인프라", "케이리츠", "이리츠"],
        "통신": ["SK텔레콤", "KT", "LG유플러스", "KT&G", "SK브로드밴드"],
        "자동차": ["현대차", "기아", "현대모비스", "만도", "현대위아"],
        "화학": ["LG화학", "롯데케미칼", "한화솔루션", "SK케미칼", "코오롱인더"],
        "건설": ["삼성물산", "현대건설", "대우건설", "GS건설", "롯데건설"],
        "엔터테인먼트": ["HYBE", "SM엔터", "JYP엔터", "YG엔터", "넷마블"],
        "식음료": ["CJ제일제당", "오리온", "농심", "롯데제과", "동원F&B"],
        "유통": ["롯데쇼핑", "신세계", "현대백화점", "GS리테일", "이마트"],
        "해운항공": ["HMM", "팬오션", "SM상선", "대한항공", "아시아나항공"],
        "반도체": ["삼성전자", "SK하이닉스", "메모리", "DB하이텍", "실리콘웍스"]
    }
    
    def __init__(self):
        """섹터 리서치 엔진 초기화"""
        self.sectors = list(self.MAJOR_SECTORS.keys())
        self.sector_weights = self._calculate_sector_weights()
        self.cache = {}  # 간단한 캐싱 시스템
        self.cache_duration = timedelta(minutes=5)
        
        logger.info(f"섹터 리서치 엔진 초기화 완료 - {len(self.sectors)}개 섹터 등록")
    
    def _calculate_sector_weights(self) -> Dict[str, float]:
        """섹터별 가중치 계산 (시가총액 기준 추정)"""
        # 실제로는 실시간 시총 데이터를 사용해야 하지만, 여기서는 추정값 사용
        weights = {
            "기술주": 0.25,
            "반도체": 0.20,
            "금융": 0.12,
            "자동차": 0.08,
            "화학": 0.06,
            "헬스케어": 0.05,
            "소재": 0.04,
            "에너지": 0.04,
            "산업재": 0.03,
            "경기소비재": 0.03,
            "건설": 0.02,
            "유통": 0.02,
            "통신": 0.02,
            "필수소비재": 0.015,
            "해운항공": 0.01,
            "엔터테인먼트": 0.01,
            "식음료": 0.01,
            "부동산": 0.005,
            "유틸리티": 0.005
        }
        return weights
    
    def generate_sector_research_prompt(self, focus_sectors: Optional[List[str]] = None, analysis_type: str = "comprehensive") -> str:
        """
        Perplexity에 최적화된 섹터 리서치 프롬프트 생성
        
        Args:
            focus_sectors: 특별히 주목할 섹터 리스트 (None이면 전체 섹터)
            analysis_type: 분석 유형 ("market_overview", "sector_deep_dive", "rotation_signals", "comprehensive")
            
        Returns:
            str: 최적화된 프롬프트
        """
        sectors_to_analyze = focus_sectors if focus_sectors else self.sectors[:10]  # 상위 10개 섹터
        
        current_date = datetime.now().strftime("%Y년 %m월 %d일")
        current_time = datetime.now().strftime("%H시 %M분")
        
        # 분석 유형별 특화 프롬프트 생성
        if analysis_type == "market_overview":
            return self._generate_market_overview_prompt(sectors_to_analyze, current_date)
        elif analysis_type == "sector_deep_dive":
            return self._generate_deep_dive_prompt(sectors_to_analyze, current_date)
        elif analysis_type == "rotation_signals":
            return self._generate_rotation_prompt(sectors_to_analyze, current_date)
        else:  # comprehensive
            return self._generate_comprehensive_prompt(sectors_to_analyze, current_date, current_time)
    
    def _generate_comprehensive_prompt(self, sectors: List[str], current_date: str, current_time: str) -> str:
        """종합적인 섹터 분석 프롬프트"""
        # 주요 섹터와 대표 종목 매핑
        sector_examples = []
        for sector in sectors[:8]:  # 상위 8개 섹터만
            examples = self.MAJOR_SECTORS.get(sector, [])[:3]  # 각 섹터당 3개 종목
            if examples:
                sector_examples.append(f"• {sector}: {', '.join(examples)}")
        
        prompt = f"""# 한국 주식 시장 실시간 섹터 분석 요청

**분석 시점**: {current_date} {current_time} (한국시간)
**분석 목적**: 투자 의사결정을 위한 섹터별 실시간 트렌드 및 기회 분석

## 🎯 분석 대상 섹터 및 주요 종목
{chr(10).join(sector_examples)}

## 📋 요청 분석 항목

### 1. 실시간 시장 동향 (최우선)
각 섹터별로 다음 정보를 **구체적인 수치와 함께** 제공:
- **오늘 장중 섹터 지수 변화율** (가능한 경우)
- **최근 1주일 주요 뉴스** (날짜, 출처 포함)
- **주요 종목 주가 움직임** (상승/하락률 포함)

### 2. 정책 및 이벤트 영향 분석
- **최근 정부 정책 발표**가 각 섹터에 미치는 영향
- **글로벌 이벤트** (미국 금리, 중국 정책 등) 연관성
- **계절적 요인** 및 **연말 특수** 고려사항

### 3. 기관/외국인 수급 동향
- **최근 1개월 기관/외국인 매매 동향**
- **섹터별 자금 유입/유출** 패턴
- **대형주 vs 중소형주** 선호도 변화

### 4. 투자 매력도 점수 (0-100점)
각 섹터별 점수를 다음 기준으로 산정:
- 펀더멘털 강도 (30%)
- 기술적 모멘텀 (25%)
- 정책 지원 (20%)
- 수급 개선 (15%)
- 글로벌 트렌드 부합 (10%)

## 🔍 특별 주목 포인트

1. **AI/반도체**: 미국 대중 제재, 삼성/SK하이닉스 실적
2. **2차전지/자동차**: 전기차 보조금, 중국 시장 상황
3. **바이오/헬스케어**: 신약 승인, 고령화 트렌드
4. **금융**: 금리 정책, 부동산 PF 리스크
5. **K-컨텐츠/게임**: 해외 진출, 규제 변화

## 📊 최종 요청사항

1. **섹터별 투자 매력도 순위** (1-8위, 점수 포함)
2. **TOP 3 투자 추천 섹터** + 구체적 이유
3. **주의 섹터** + 리스크 요인
4. **섹터 로테이션 신호** (A섹터 → B섹터 이동 감지)

⚠️ **중요**: 모든 정보에 대해 **출처와 날짜를 반드시 명시**하고, 추측이 아닌 **실제 데이터 기반**으로 분석해주세요."""
        
        return prompt.strip()
    
    def _generate_market_overview_prompt(self, sectors: List[str], current_date: str) -> str:
        """시장 개요 프롬프트"""
        prompt = f"""# 한국 주식 시장 섹터 개요 ({current_date})

다음 주요 섹터들의 **최신 시장 개요**를 간결하게 분석해주세요:
{', '.join(sectors[:5])}

각 섹터별로 다음 정보만 간단히:
1. **오늘/이번주 주요 이슈** (1-2개)
2. **현재 트렌드** (상승/하락/보합)
3. **투자 매력도** (1-5점)

전체 응답은 **500단어 이내**로 제한하고, **핵심 정보와 출처**만 포함해주세요."""
        
        return prompt.strip()
    
    def _generate_deep_dive_prompt(self, sectors: List[str], current_date: str) -> str:
        """특정 섹터 심층 분석 프롬프트"""
        target_sector = sectors[0] if sectors else "기술주"
        
        prompt = f"""# 한국 {target_sector} 섹터 심층 분석 ({current_date})

**한국 주식 시장의 {target_sector} 섹터**에 대한 상세 분석을 요청합니다:

## 📈 최근 성과 분석
- 최근 1개월 한국 {target_sector} 섹터 지수 변화
- 주요 종목별 주가 성과 (삼성전자, SK하이닉스 등)
- 거래량 및 시가총액 변화

## 🔍 펀더멘털 분석
- 주요 한국 기업 실적 및 전망
- 산업 성장률 및 시장 규모
- 경쟁 구조 및 시장 점유율

## 🌍 외부 환경 영향
- 글로벌 트렌드와 한국 시장 연관성
- 한국 정부 정책 영향
- 환율/원자재 가격이 한국 기업에 미치는 영향

구체적인 **수치, 날짜, 출처**를 포함하여 분석해주세요."""
        
        return prompt.strip()
    
    def _generate_rotation_prompt(self, sectors: List[str], current_date: str) -> str:
        """섹터 로테이션 신호 프롬프트"""
        prompt = f"""# 한국 주식 시장 섹터 로테이션 신호 분석 ({current_date})

**섹터 간 자금 이동 패턴** 및 **로테이션 신호**를 분석해주세요:

## 🔄 현재 감지되는 로테이션 신호
다음 섹터들 간의 자금 이동 패턴:
{', '.join(sectors)}

각 섹터별로:
1. **자금 유입/유출 현황** (최근 2주)
2. **상대적 강도** (다른 섹터 대비)
3. **로테이션 방향성** (A→B 이동 신호)

## 📊 요청 결과
- **현재 강세 섹터** TOP 3
- **약세→강세 전환 신호** 섹터
- **강세→약세 전환 신호** 섹터
- **향후 2-4주 로테이션 방향 예측**

**기관/외국인 매매 데이터** 및 **최근 자금 흐름 패턴**을 근거로 분석해주세요."""
        
        return prompt.strip()
    
    def parse_llm_response(self, llm_response: str) -> SectorResearchResult:
        """
        LLM 응답을 구조화된 섹터 리서치 결과로 파싱
        
        Args:
            llm_response: LLM으로부터의 응답 텍스트
            
        Returns:
            SectorResearchResult: 구조화된 분석 결과
        """
        # 실제 LLM 응답을 파싱하는 로직 (여기서는 mock 데이터)
        # 실제 구현에서는 정규식이나 자연어 처리를 통해 구조화
        
        current_time = datetime.now()
        
        # Mock 섹터 메트릭 생성
        sector_rankings = []
        for i, sector in enumerate(self.sectors[:10]):
            trend_score = max(0, min(100, 70 + (i * 2) + (hash(sector) % 20)))
            sentiment_score = (hash(sector) % 200 - 100) / 100  # -1 ~ 1
            
            metrics = SectorMetrics(
                sector_name=sector,
                trend_score=trend_score,
                sentiment_score=sentiment_score,
                momentum_score=max(0, min(100, trend_score + 10)),
                policy_impact=sentiment_score * 0.5,
                relative_strength=trend_score * 0.8,
                opportunity_level=self._categorize_opportunity(trend_score),
                risk_level=self._categorize_risk(sentiment_score)
            )
            sector_rankings.append(metrics)
        
        # 점수 기준으로 정렬
        sector_rankings.sort(key=lambda x: x.trend_score, reverse=True)
        
        # Mock 투자 기회 생성
        top_opportunities = [
            SectorOpportunity(
                sector_name=sector_rankings[0].sector_name,
                opportunity_type="정책수혜",
                description=f"{sector_rankings[0].sector_name} 섹터의 정부 지원 정책 확대",
                confidence_level=0.8,
                time_horizon="중기",
                expected_impact="높음",
                key_catalysts=["정부 지원", "시장 확대", "기술 혁신"]
            ),
            SectorOpportunity(
                sector_name=sector_rankings[1].sector_name,
                opportunity_type="기술혁신",
                description=f"{sector_rankings[1].sector_name} 섹터의 혁신 기술 도입",
                confidence_level=0.7,
                time_horizon="장기",
                expected_impact="높음",
                key_catalysts=["기술 발전", "시장 수요 증가"]
            )
        ]
        
        # Mock 로테이션 신호
        rotation_signals = [
            RotationSignal(
                from_sector=sector_rankings[-1].sector_name,
                to_sector=sector_rankings[0].sector_name,
                signal_strength=0.7,
                reasoning="시장 트렌드 변화로 인한 자금 이동",
                timing="단기"
            )
        ]
        
        return SectorResearchResult(
            research_timestamp=current_time,
            analysis_period="최근 1주일",
            sector_rankings=sector_rankings,
            top_opportunities=top_opportunities,
            rotation_signals=rotation_signals,
            market_overview="전반적으로 기술주와 반도체 섹터가 강세를 보이고 있음",
            confidence_indicators={
                "data_freshness": 0.9,
                "source_reliability": 0.8,
                "analysis_confidence": 0.85
            },
            data_sources=["Perplexity 실시간 검색", "한국 증권시장", "정부 정책 발표"]
        )
    
    def _categorize_opportunity(self, trend_score: float) -> str:
        """트렌드 점수를 기반으로 기회 수준 분류"""
        if trend_score >= 85:
            return "매우높음"
        elif trend_score >= 70:
            return "높음"
        elif trend_score >= 50:
            return "보통"
        else:
            return "낮음"
    
    def _categorize_risk(self, sentiment_score: float) -> str:
        """감정 점수를 기반으로 리스크 수준 분류"""
        if sentiment_score <= -0.5:
            return "높음"
        elif sentiment_score <= 0.2:
            return "보통"
        else:
            return "낮음"
    
    def calculate_sector_correlation(self, sector1: str, sector2: str) -> float:
        """두 섹터 간의 상관관계 계산 (Mock)"""
        # 실제로는 과거 수익률 데이터를 사용해야 함
        correlation_matrix = {
            ("기술주", "반도체"): 0.8,
            ("자동차", "소재"): 0.6,
            ("금융", "부동산"): 0.5,
            ("에너지", "화학"): 0.7
        }
        
        key = (sector1, sector2) if (sector1, sector2) in correlation_matrix else (sector2, sector1)
        return correlation_matrix.get(key, 0.3)  # 기본값
    
    def get_sector_benchmark_data(self) -> Dict[str, Dict[str, float]]:
        """섹터별 벤치마크 데이터 반환"""
        # 실제로는 외부 데이터 소스에서 가져와야 함
        benchmark_data = {}
        
        for sector in self.sectors:
            benchmark_data[sector] = {
                "pe_ratio": 15.0 + (hash(sector) % 20),
                "pb_ratio": 1.2 + (hash(sector) % 10) * 0.1,
                "dividend_yield": 2.0 + (hash(sector) % 30) * 0.1,
                "market_cap_weight": self.sector_weights.get(sector, 0.01)
            }
        
        return benchmark_data
    
    def validate_research_result(self, result: SectorResearchResult) -> Tuple[bool, List[str]]:
        """
        리서치 결과 검증
        
        Args:
            result: 검증할 리서치 결과
            
        Returns:
            Tuple[bool, List[str]]: (검증 성공 여부, 오류 메시지 리스트)
        """
        errors = []
        
        # 기본 필드 검증
        if not result.sector_rankings:
            errors.append("섹터 순위 데이터가 없습니다")
        
        if not result.market_overview:
            errors.append("시장 개요가 없습니다")
        
        # 점수 범위 검증
        for ranking in result.sector_rankings:
            if not (0 <= ranking.trend_score <= 100):
                errors.append(f"{ranking.sector_name}의 트렌드 점수가 유효 범위를 벗어났습니다")
            
            if not (-1 <= ranking.sentiment_score <= 1):
                errors.append(f"{ranking.sector_name}의 감정 점수가 유효 범위를 벗어났습니다")
        
        # 신뢰도 검증
        for key, confidence in result.confidence_indicators.items():
            if not (0 <= confidence <= 1):
                errors.append(f"신뢰도 지표 {key}가 유효 범위를 벗어났습니다")
        
        # 최신성 검증 (5분 이내)
        time_diff = datetime.now() - result.research_timestamp
        if time_diff > timedelta(minutes=5):
            errors.append("분석 결과가 너무 오래되었습니다")
        
        return len(errors) == 0, errors


def get_sector_research_engine() -> SectorResearchEngine:
    """섹터 리서치 엔진 싱글톤 인스턴스 반환"""
    if not hasattr(get_sector_research_engine, '_instance'):
        get_sector_research_engine._instance = SectorResearchEngine()
    
    return get_sector_research_engine._instance