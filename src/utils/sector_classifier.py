"""
종목 섹터 분류 유틸리티

종목 코드를 기반으로 해당 종목이 속한 섹터를 분류하고,
섹터별 특성 정보를 제공하는 유틸리티 클래스
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class SectorType(Enum):
    """주요 섹터 분류"""
    TECHNOLOGY = "기술주"
    FINANCE = "금융"
    HEALTHCARE = "헬스케어"
    CONSUMER_STAPLES = "필수소비재"
    CONSUMER_DISCRETIONARY = "임의소비재"
    INDUSTRIALS = "산업재"
    ENERGY = "에너지"
    MATERIALS = "소재"
    UTILITIES = "유틸리티"
    REAL_ESTATE = "부동산"
    TELECOMMUNICATIONS = "통신"
    ENTERTAINMENT = "엔터테인먼트"
    AUTOMOBILE = "자동차"
    AEROSPACE = "항공우주"
    SHIPPING = "해운"
    CONSTRUCTION = "건설"
    FOOD_BEVERAGE = "식품음료"
    RETAIL = "유통"
    CHEMICALS = "화학"
    UNKNOWN = "미분류"


@dataclass
class SectorInfo:
    """섹터 정보"""
    sector_type: SectorType
    sector_name_kr: str
    sector_name_en: str
    characteristics: List[str]
    volatility_level: str  # "낮음", "보통", "높음"
    cycle_sensitivity: str  # "방어", "순환", "성장"


class SectorClassifier:
    """종목 섹터 분류기"""
    
    def __init__(self):
        """섹터 분류기 초기화"""
        self.logger = logging.getLogger(__name__)
        
        # 종목 코드별 섹터 매핑 (주요 종목들)
        self.ticker_sector_map = self._initialize_ticker_mapping()
        
        # 섹터별 상세 정보
        self.sector_info_map = self._initialize_sector_info()
    
    def _initialize_ticker_mapping(self) -> Dict[str, SectorType]:
        """종목 코드별 섹터 매핑 초기화"""
        return {
            # 기술주
            "005930": SectorType.TECHNOLOGY,  # 삼성전자
            "000660": SectorType.TECHNOLOGY,  # SK하이닉스
            "035420": SectorType.TECHNOLOGY,  # 네이버
            "035720": SectorType.TECHNOLOGY,  # 카카오
            "207940": SectorType.TECHNOLOGY,  # 삼성바이오로직스
            "068270": SectorType.TECHNOLOGY,  # 셀트리온
            "028300": SectorType.TECHNOLOGY,  # HLB
            "036570": SectorType.TECHNOLOGY,  # 엔씨소프트
            "251270": SectorType.TECHNOLOGY,  # 넷마블
            "012330": SectorType.TECHNOLOGY,  # 현대모비스
            
            # 금융
            "055550": SectorType.FINANCE,     # 신한지주
            "105560": SectorType.FINANCE,     # KB금융
            "086790": SectorType.FINANCE,     # 하나금융지주
            "316140": SectorType.FINANCE,     # 우리금융지주
            "032830": SectorType.FINANCE,     # 삼성생명
            "085620": SectorType.FINANCE,     # 미래에셋증권
            "003540": SectorType.FINANCE,     # 대신증권
            
            # 자동차
            "005380": SectorType.AUTOMOBILE,  # 현대차
            "000270": SectorType.AUTOMOBILE,  # 기아
            "161390": SectorType.AUTOMOBILE,  # 한국타이어
            "034730": SectorType.AUTOMOBILE,  # SK
            
            # 화학/소재
            "051910": SectorType.CHEMICALS,   # LG화학
            "006400": SectorType.MATERIALS,   # 삼성SDI
            "096770": SectorType.MATERIALS,   # SK이노베이션
            "011170": SectorType.CHEMICALS,   # 롯데케미칼
            "005490": SectorType.MATERIALS,   # POSCO홀딩스
            "010950": SectorType.MATERIALS,   # S-Oil
            
            # 식품음료
            "097950": SectorType.FOOD_BEVERAGE, # CJ제일제당
            "004990": SectorType.FOOD_BEVERAGE, # 롯데지주
            "271560": SectorType.FOOD_BEVERAGE, # 오리온
            "007070": SectorType.FOOD_BEVERAGE, # GS리테일
            
            # 유통/소비재
            "282330": SectorType.CONSUMER_DISCRETIONARY, # BGF리테일
            "139480": SectorType.CONSUMER_DISCRETIONARY, # 이마트
            "057050": SectorType.CONSUMER_DISCRETIONARY, # 현대홈쇼핑
            
            # 건설
            "000720": SectorType.CONSTRUCTION,  # 현대건설
            "028050": SectorType.CONSTRUCTION,  # 삼성물산
            "047040": SectorType.CONSTRUCTION,  # 대우건설
            
            # 해운
            "009540": SectorType.SHIPPING,      # HD한국조선해양
            "011200": SectorType.SHIPPING,      # HMM
            
            # 항공
            "003490": SectorType.AEROSPACE,     # 대한항공
            "020560": SectorType.AEROSPACE,     # 아시아나항공
            
            # 엔터테인먼트
            "041510": SectorType.ENTERTAINMENT, # SM엔터테인먼트
            "122870": SectorType.ENTERTAINMENT, # YG엔터테인먼트
            "035900": SectorType.ENTERTAINMENT, # JYP Ent.
            
            # 통신
            "030200": SectorType.TELECOMMUNICATIONS, # KT
            "017670": SectorType.TELECOMMUNICATIONS, # SK텔레콤
            "032640": SectorType.TELECOMMUNICATIONS, # LG유플러스
            
            # 헬스케어/바이오
            "326030": SectorType.HEALTHCARE,    # SK바이오팜
            "196170": SectorType.HEALTHCARE,    # 알테오젠
            "145020": SectorType.HEALTHCARE,    # 휴젤
            "302440": SectorType.HEALTHCARE,    # SK바이오사이언스
            
            # 에너지/유틸리티
            "015760": SectorType.ENERGY,        # 한국전력
            "034020": SectorType.UTILITIES,     # 두산에너빌리티
            "267250": SectorType.ENERGY,        # HD현대중공업
        }
    
    def _initialize_sector_info(self) -> Dict[SectorType, SectorInfo]:
        """섹터별 상세 정보 초기화"""
        return {
            SectorType.TECHNOLOGY: SectorInfo(
                sector_type=SectorType.TECHNOLOGY,
                sector_name_kr="기술주",
                sector_name_en="Technology",
                characteristics=["고성장", "높은 변동성", "혁신 중심", "글로벌 경쟁"],
                volatility_level="높음",
                cycle_sensitivity="성장"
            ),
            SectorType.FINANCE: SectorInfo(
                sector_type=SectorType.FINANCE,
                sector_name_kr="금융",
                sector_name_en="Finance",
                characteristics=["금리 민감", "경기 순환", "규제 영향", "배당 매력"],
                volatility_level="보통",
                cycle_sensitivity="순환"
            ),
            SectorType.HEALTHCARE: SectorInfo(
                sector_type=SectorType.HEALTHCARE,
                sector_name_kr="헬스케어",
                sector_name_en="Healthcare",
                characteristics=["방어적 성격", "인구 고령화", "신약 개발", "규제 리스크"],
                volatility_level="보통",
                cycle_sensitivity="방어"
            ),
            SectorType.CONSUMER_STAPLES: SectorInfo(
                sector_type=SectorType.CONSUMER_STAPLES,
                sector_name_kr="필수소비재",
                sector_name_en="Consumer Staples",
                characteristics=["안정적 수요", "방어적", "배당 안정", "인플레이션 영향"],
                volatility_level="낮음",
                cycle_sensitivity="방어"
            ),
            SectorType.CONSUMER_DISCRETIONARY: SectorInfo(
                sector_type=SectorType.CONSUMER_DISCRETIONARY,
                sector_name_kr="임의소비재",
                sector_name_en="Consumer Discretionary",
                characteristics=["경기 민감", "소비 심리", "계절성", "브랜드 파워"],
                volatility_level="높음",
                cycle_sensitivity="순환"
            ),
            SectorType.AUTOMOBILE: SectorInfo(
                sector_type=SectorType.AUTOMOBILE,
                sector_name_kr="자동차",
                sector_name_en="Automobile",
                characteristics=["경기 민감", "전기차 전환", "글로벌 공급망", "원자재 가격"],
                volatility_level="높음",
                cycle_sensitivity="순환"
            ),
            SectorType.CHEMICALS: SectorInfo(
                sector_type=SectorType.CHEMICALS,
                sector_name_kr="화학",
                sector_name_en="Chemicals",
                characteristics=["원자재 가격", "경기 순환", "환경 규제", "에너지 의존"],
                volatility_level="높음",
                cycle_sensitivity="순환"
            ),
            SectorType.MATERIALS: SectorInfo(
                sector_type=SectorType.MATERIALS,
                sector_name_kr="소재",
                sector_name_en="Materials",
                characteristics=["경기 선행", "원자재 가격", "중국 수요", "인프라 투자"],
                volatility_level="높음",
                cycle_sensitivity="순환"
            ),
            SectorType.ENERGY: SectorInfo(
                sector_type=SectorType.ENERGY,
                sector_name_kr="에너지",
                sector_name_en="Energy",
                characteristics=["유가 의존", "신재생 전환", "지정학적 리스크", "ESG 이슈"],
                volatility_level="높음",
                cycle_sensitivity="순환"
            ),
            SectorType.UTILITIES: SectorInfo(
                sector_type=SectorType.UTILITIES,
                sector_name_kr="유틸리티",
                sector_name_en="Utilities",
                characteristics=["안정적 현금흐름", "규제 산업", "금리 민감", "배당 수익"],
                volatility_level="낮음",
                cycle_sensitivity="방어"
            ),
            SectorType.TELECOMMUNICATIONS: SectorInfo(
                sector_type=SectorType.TELECOMMUNICATIONS,
                sector_name_kr="통신",
                sector_name_en="Telecommunications",
                characteristics=["안정적 수익", "5G 투자", "경쟁 심화", "배당 매력"],
                volatility_level="낮음",
                cycle_sensitivity="방어"
            ),
            SectorType.ENTERTAINMENT: SectorInfo(
                sector_type=SectorType.ENTERTAINMENT,
                sector_name_kr="엔터테인먼트",
                sector_name_en="Entertainment",
                characteristics=["한류 열풍", "콘텐츠 IP", "높은 변동성", "글로벌 확장"],
                volatility_level="높음",
                cycle_sensitivity="성장"
            ),
            SectorType.SHIPPING: SectorInfo(
                sector_type=SectorType.SHIPPING,
                sector_name_kr="해운",
                sector_name_en="Shipping",
                characteristics=["경기 초민감", "해운료 변동", "글로벌 물동량", "유가 영향"],
                volatility_level="높음",
                cycle_sensitivity="순환"
            ),
            SectorType.CONSTRUCTION: SectorInfo(
                sector_type=SectorType.CONSTRUCTION,
                sector_name_kr="건설",
                sector_name_en="Construction",
                characteristics=["부동산 시장", "정부 정책", "수주 의존", "계절성"],
                volatility_level="보통",
                cycle_sensitivity="순환"
            ),
            SectorType.AEROSPACE: SectorInfo(
                sector_type=SectorType.AEROSPACE,
                sector_name_kr="항공우주",
                sector_name_en="Aerospace",
                characteristics=["여행 수요", "연료비 변동", "코로나 영향", "국제선 회복"],
                volatility_level="높음",
                cycle_sensitivity="순환"
            ),
            SectorType.FOOD_BEVERAGE: SectorInfo(
                sector_type=SectorType.FOOD_BEVERAGE,
                sector_name_kr="식품음료",
                sector_name_en="Food & Beverage",
                characteristics=["안정적 수요", "브랜드 가치", "원자재 가격", "건강 트렌드"],
                volatility_level="낮음",
                cycle_sensitivity="방어"
            ),
            SectorType.RETAIL: SectorInfo(
                sector_type=SectorType.RETAIL,
                sector_name_kr="유통",
                sector_name_en="Retail",
                characteristics=["소비 심리", "온라인 전환", "임대료 부담", "경기 민감"],
                volatility_level="보통",
                cycle_sensitivity="순환"
            ),
            SectorType.UNKNOWN: SectorInfo(
                sector_type=SectorType.UNKNOWN,
                sector_name_kr="미분류",
                sector_name_en="Unknown",
                characteristics=["분류 필요"],
                volatility_level="보통",
                cycle_sensitivity="순환"
            )
        }
    
    def classify_ticker(self, ticker: str) -> SectorType:
        """
        종목 코드로 섹터 분류
        
        Args:
            ticker: 종목 코드 (6자리)
            
        Returns:
            SectorType: 분류된 섹터
        """
        if ticker in self.ticker_sector_map:
            return self.ticker_sector_map[ticker]
        
        # 매핑되지 않은 종목은 종목 코드 기반 추론 시도
        inferred_sector = self._infer_sector_from_code(ticker)
        if inferred_sector != SectorType.UNKNOWN:
            self.logger.info(f"종목 {ticker}를 {inferred_sector.value}로 추론 분류")
            return inferred_sector
        
        self.logger.warning(f"종목 {ticker}의 섹터를 분류할 수 없음 - UNKNOWN으로 분류")
        return SectorType.UNKNOWN
    
    def _infer_sector_from_code(self, ticker: str) -> SectorType:
        """
        종목 코드 패턴으로 섹터 추론 (간단한 휴리스틱)
        
        Args:
            ticker: 종목 코드
            
        Returns:
            SectorType: 추론된 섹터
        """
        # 일부 종목 코드 패턴 기반 추론
        # 실제로는 더 정교한 로직이나 외부 API 연동 필요
        
        if ticker.startswith("00"):
            # 00으로 시작하는 종목들 중 일부 패턴
            return SectorType.UNKNOWN
        elif ticker.startswith("03"):
            # 03으로 시작하는 종목들 중 일부 패턴 (IT 관련 많음)
            return SectorType.TECHNOLOGY
        
        return SectorType.UNKNOWN
    
    def get_sector_info(self, sector_type: SectorType) -> SectorInfo:
        """
        섹터 상세 정보 반환
        
        Args:
            sector_type: 섹터 타입
            
        Returns:
            SectorInfo: 섹터 상세 정보
        """
        return self.sector_info_map.get(sector_type, self.sector_info_map[SectorType.UNKNOWN])
    
    def get_all_sectors(self) -> List[SectorType]:
        """모든 섹터 타입 반환"""
        return list(SectorType)
    
    def add_ticker_mapping(self, ticker: str, sector_type: SectorType) -> None:
        """
        새로운 종목-섹터 매핑 추가
        
        Args:
            ticker: 종목 코드
            sector_type: 섹터 타입
        """
        self.ticker_sector_map[ticker] = sector_type
        self.logger.info(f"종목 {ticker}를 {sector_type.value} 섹터로 매핑 추가")
    
    def get_sector_tickers(self, sector_type: SectorType) -> List[str]:
        """
        특정 섹터에 속한 종목 코드들 반환
        
        Args:
            sector_type: 섹터 타입
            
        Returns:
            List[str]: 해당 섹터의 종목 코드 리스트
        """
        return [ticker for ticker, sector in self.ticker_sector_map.items() 
                if sector == sector_type]
    
    def get_sector_distribution(self, tickers: List[str]) -> Dict[SectorType, int]:
        """
        종목 리스트의 섹터별 분포 계산
        
        Args:
            tickers: 종목 코드 리스트
            
        Returns:
            Dict[SectorType, int]: 섹터별 종목 수
        """
        distribution = {}
        for ticker in tickers:
            sector = self.classify_ticker(ticker)
            distribution[sector] = distribution.get(sector, 0) + 1
        
        return distribution


# 전역 섹터 분류기 인스턴스 (싱글톤 패턴)
_sector_classifier = None

def get_sector_classifier() -> SectorClassifier:
    """섹터 분류기 싱글톤 인스턴스 반환"""
    global _sector_classifier
    
    if _sector_classifier is None:
        _sector_classifier = SectorClassifier()
    
    return _sector_classifier