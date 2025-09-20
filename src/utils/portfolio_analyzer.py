"""
포트폴리오 분석 도구

포트폴리오의 다양한 지표를 계산하고 분석하는 유틸리티 클래스
리밸런싱 필요도, 집중도 위험, 다각화 수준 등을 평가합니다.
"""

import math
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import logging

from .sector_classifier import get_sector_classifier, SectorType

logger = logging.getLogger(__name__)


@dataclass
class StockHolding:
    """개별 주식 보유 정보"""
    ticker: str
    name: str
    quantity: int
    avg_price: float
    current_price: float
    total_value: float
    pnl: float
    weight: float = 0.0  # 포트폴리오 내 비중
    sector: SectorType = SectorType.UNKNOWN


@dataclass
class SectorAllocation:
    """섹터별 자산 배분 정보"""
    sector_type: SectorType
    sector_name: str
    total_value: float
    weight: float
    stock_count: int
    holdings: List[StockHolding]


@dataclass
class PortfolioMetrics:
    """포트폴리오 주요 지표"""
    total_value: float
    cash_value: float
    stock_value: float
    cash_ratio: float
    stock_ratio: float
    total_pnl: float
    total_pnl_rate: float
    
    # 분산투자 지표
    diversification_score: float  # 0~1, 높을수록 잘 분산됨
    concentration_risk: float     # 0~1, 높을수록 집중도 위험 높음
    herfindahl_index: float      # 집중도 지수 (0~1)
    
    # 섹터 분석
    sector_count: int
    largest_sector_weight: float
    sector_allocation: List[SectorAllocation]
    
    # 리밸런싱 지표
    rebalancing_score: float     # 0~1, 높을수록 리밸런싱 필요
    rebalancing_priority: str    # "낮음", "보통", "높음", "긴급"


@dataclass
class RebalancingRecommendation:
    """리밸런싱 권고 사항"""
    priority: str
    score: float
    reasons: List[str]
    actions: List[Dict[str, Any]]
    target_allocations: Dict[str, float]
    expected_improvement: str


class PortfolioAnalyzer:
    """포트폴리오 분석기"""
    
    def __init__(self):
        """포트폴리오 분석기 초기화"""
        self.logger = logging.getLogger(__name__)
        self.sector_classifier = get_sector_classifier()
        
        # 기본 설정값들
        self.max_single_stock_weight = 0.20      # 단일 종목 최대 비중 20%
        self.max_sector_weight = 0.40            # 단일 섹터 최대 비중 40%
        self.min_cash_ratio = 0.05              # 최소 현금 비중 5%
        self.target_diversification_score = 0.7  # 목표 분산투자 점수
        
    def analyze_portfolio(self, holdings: List[Dict[str, Any]], 
                         cash_balance: float, 
                         total_value: float) -> PortfolioMetrics:
        """
        포트폴리오 종합 분석
        
        Args:
            holdings: 보유 주식 정보 리스트
            cash_balance: 현금 잔고
            total_value: 총 자산 가치
            
        Returns:
            PortfolioMetrics: 포트폴리오 분석 결과
        """
        # 보유 주식 정보 구조화
        stock_holdings = self._create_stock_holdings(holdings, total_value)
        
        # 기본 지표 계산
        stock_value = sum(holding.total_value for holding in stock_holdings)
        cash_ratio = cash_balance / total_value if total_value > 0 else 0
        stock_ratio = stock_value / total_value if total_value > 0 else 0
        
        # 수익률 계산
        total_pnl = sum(holding.pnl for holding in stock_holdings)
        total_cost = sum(holding.avg_price * holding.quantity for holding in stock_holdings)
        total_pnl_rate = (total_pnl / total_cost * 100) if total_cost > 0 else 0
        
        # 섹터별 분석
        sector_allocation = self._analyze_sector_allocation(stock_holdings)
        
        # 집중도 및 분산투자 지표 계산
        diversification_score = self._calculate_diversification_score(stock_holdings, sector_allocation)
        concentration_risk = self._calculate_concentration_risk(stock_holdings, sector_allocation)
        herfindahl_index = self._calculate_herfindahl_index(stock_holdings)
        
        # 리밸런싱 필요도 계산
        rebalancing_score = self._calculate_rebalancing_score(
            stock_holdings, sector_allocation, cash_ratio
        )
        
        return PortfolioMetrics(
            total_value=total_value,
            cash_value=cash_balance,
            stock_value=stock_value,
            cash_ratio=cash_ratio,
            stock_ratio=stock_ratio,
            total_pnl=total_pnl,
            total_pnl_rate=total_pnl_rate,
            diversification_score=diversification_score,
            concentration_risk=concentration_risk,
            herfindahl_index=herfindahl_index,
            sector_count=len(sector_allocation),
            largest_sector_weight=max([s.weight for s in sector_allocation], default=0),
            sector_allocation=sector_allocation,
            rebalancing_score=rebalancing_score,
            rebalancing_priority=self._get_priority_level(rebalancing_score)
        )
    
    def _create_stock_holdings(self, holdings_data: List[Dict[str, Any]], 
                              total_value: float) -> List[StockHolding]:
        """보유 주식 정보를 StockHolding 객체로 변환"""
        stock_holdings = []
        
        for holding_data in holdings_data:
            ticker = holding_data.get('ticker', '')
            sector = self.sector_classifier.classify_ticker(ticker)
            weight = holding_data.get('total_value', 0) / total_value if total_value > 0 else 0
            
            stock_holding = StockHolding(
                ticker=ticker,
                name=holding_data.get('name', ''),
                quantity=holding_data.get('quantity', 0),
                avg_price=holding_data.get('avg_price', 0),
                current_price=holding_data.get('current_price', 0),
                total_value=holding_data.get('total_value', 0),
                pnl=holding_data.get('pnl', 0),
                weight=weight,
                sector=sector
            )
            
            stock_holdings.append(stock_holding)
        
        return stock_holdings
    
    def _analyze_sector_allocation(self, holdings: List[StockHolding]) -> List[SectorAllocation]:
        """섹터별 자산 배분 분석"""
        sector_map = {}
        total_stock_value = sum(holding.total_value for holding in holdings)
        
        # 섹터별 그룹핑
        for holding in holdings:
            sector = holding.sector
            if sector not in sector_map:
                sector_map[sector] = {
                    'holdings': [],
                    'total_value': 0
                }
            
            sector_map[sector]['holdings'].append(holding)
            sector_map[sector]['total_value'] += holding.total_value
        
        # SectorAllocation 객체 생성
        sector_allocations = []
        for sector_type, sector_data in sector_map.items():
            sector_info = self.sector_classifier.get_sector_info(sector_type)
            weight = sector_data['total_value'] / total_stock_value if total_stock_value > 0 else 0
            
            allocation = SectorAllocation(
                sector_type=sector_type,
                sector_name=sector_info.sector_name_kr,
                total_value=sector_data['total_value'],
                weight=weight,
                stock_count=len(sector_data['holdings']),
                holdings=sector_data['holdings']
            )
            
            sector_allocations.append(allocation)
        
        # 비중 순으로 정렬
        sector_allocations.sort(key=lambda x: x.weight, reverse=True)
        
        return sector_allocations
    
    def _calculate_diversification_score(self, holdings: List[StockHolding], 
                                       sector_allocations: List[SectorAllocation]) -> float:
        """분산투자 점수 계산 (0~1, 높을수록 잘 분산됨)"""
        if not holdings:
            return 0.0
        
        # 1. 종목 수 다각화 점수 (많을수록 좋음, 최대 20개까지 고려)
        stock_count_score = min(len(holdings) / 20, 1.0)
        
        # 2. 섹터 다각화 점수 (섹터가 많고 고르게 분산될수록 좋음)
        sector_count_score = min(len(sector_allocations) / 10, 1.0)  # 최대 10개 섹터까지 고려
        
        # 3. 섹터 비중 균등성 점수 (섹터별 비중이 고를수록 좋음)
        if sector_allocations:
            sector_weights = [allocation.weight for allocation in sector_allocations]
            sector_balance_score = 1 - self._calculate_gini_coefficient(sector_weights)
        else:
            sector_balance_score = 0
        
        # 4. 개별 종목 집중도 점수 (단일 종목 비중이 낮을수록 좋음)
        max_stock_weight = max([holding.weight for holding in holdings], default=0)
        stock_concentration_score = 1 - min(max_stock_weight / self.max_single_stock_weight, 1.0)
        
        # 가중 평균으로 최종 점수 계산
        diversification_score = (
            stock_count_score * 0.25 +
            sector_count_score * 0.25 +
            sector_balance_score * 0.25 +
            stock_concentration_score * 0.25
        )
        
        return round(diversification_score, 3)
    
    def _calculate_concentration_risk(self, holdings: List[StockHolding], 
                                    sector_allocations: List[SectorAllocation]) -> float:
        """집중도 위험 계산 (0~1, 높을수록 위험)"""
        if not holdings:
            return 0.0
        
        risk_score = 0.0
        
        # 1. 단일 종목 집중도 위험
        max_stock_weight = max([holding.weight for holding in holdings], default=0)
        if max_stock_weight > self.max_single_stock_weight:
            risk_score += (max_stock_weight - self.max_single_stock_weight) * 2
        
        # 2. 상위 3종목 집중도 위험
        top3_weights = sorted([holding.weight for holding in holdings], reverse=True)[:3]
        top3_concentration = sum(top3_weights)
        if top3_concentration > 0.6:  # 상위 3종목이 60% 초과 시 위험
            risk_score += (top3_concentration - 0.6) * 1.5
        
        # 3. 섹터 집중도 위험
        if sector_allocations:
            max_sector_weight = max([allocation.weight for allocation in sector_allocations])
            if max_sector_weight > self.max_sector_weight:
                risk_score += (max_sector_weight - self.max_sector_weight) * 1.5
        
        # 4. 섹터 수 부족 위험
        if len(sector_allocations) < 3:
            risk_score += 0.2 * (3 - len(sector_allocations))
        
        return min(risk_score, 1.0)  # 최대 1.0으로 제한
    
    def _calculate_herfindahl_index(self, holdings: List[StockHolding]) -> float:
        """허핀달 집중도 지수 계산 (0~1, 높을수록 집중도 높음)"""
        if not holdings:
            return 0.0
        
        weights = [holding.weight for holding in holdings]
        hhi = sum(weight ** 2 for weight in weights)
        
        return round(hhi, 4)
    
    def _calculate_gini_coefficient(self, values: List[float]) -> float:
        """지니 계수 계산 (불평등 측정, 0~1)"""
        if not values or len(values) < 2:
            return 0.0
        
        sorted_values = sorted(values)
        n = len(sorted_values)
        cumulative_sum = 0
        
        for i, value in enumerate(sorted_values):
            cumulative_sum += value * (n - i)
        
        if sum(sorted_values) == 0:
            return 0.0
        
        gini = (2 * cumulative_sum) / (n * sum(sorted_values)) - (n + 1) / n
        return max(0.0, min(1.0, gini))
    
    def _calculate_rebalancing_score(self, holdings: List[StockHolding], 
                                   sector_allocations: List[SectorAllocation], 
                                   cash_ratio: float) -> float:
        """리밸런싱 필요도 점수 계산 (0~1, 높을수록 리밸런싱 필요)"""
        if not holdings:
            return 0.0
        
        score = 0.0
        
        # 1. 개별 종목 비중 이탈 (20% 초과 시)
        for holding in holdings:
            if holding.weight > self.max_single_stock_weight:
                excess = holding.weight - self.max_single_stock_weight
                score += excess * 2  # 초과분의 2배 가중치
        
        # 2. 섹터 비중 이탈 (40% 초과 시)
        for allocation in sector_allocations:
            if allocation.weight > self.max_sector_weight:
                excess = allocation.weight - self.max_sector_weight
                score += excess * 1.5  # 초과분의 1.5배 가중치
        
        # 3. 현금 비중 부족 또는 과다
        if cash_ratio < self.min_cash_ratio:
            score += (self.min_cash_ratio - cash_ratio) * 0.5
        elif cash_ratio > 0.3:  # 현금 30% 초과 시 비효율
            score += (cash_ratio - 0.3) * 0.3
        
        # 4. 분산투자 부족
        diversification_gap = self.target_diversification_score - self._calculate_diversification_score(holdings, sector_allocations)
        if diversification_gap > 0:
            score += diversification_gap * 0.5
        
        # 5. 손실 종목 비중 (손절 고려)
        for holding in holdings:
            if holding.pnl < 0:
                loss_rate = abs(holding.pnl) / (holding.avg_price * holding.quantity)
                if loss_rate > 0.15:  # 15% 이상 손실 시
                    score += loss_rate * holding.weight * 0.3
        
        return min(score, 1.0)  # 최대 1.0으로 제한
    
    def _get_priority_level(self, score: float) -> str:
        """리밸런싱 점수를 우선순위 레벨로 변환"""
        if score >= 0.8:
            return "긴급"
        elif score >= 0.6:
            return "높음"
        elif score >= 0.3:
            return "보통"
        else:
            return "낮음"
    
    def generate_rebalancing_recommendation(self, metrics: PortfolioMetrics) -> RebalancingRecommendation:
        """리밸런싱 권고사항 생성"""
        reasons = []
        actions = []
        target_allocations = {}
        
        # 문제점 분석 및 권고사항 생성
        if metrics.concentration_risk > 0.3:
            reasons.append(f"집중도 위험이 높습니다 (위험도: {metrics.concentration_risk:.1%})")
        
        if metrics.diversification_score < 0.6:
            reasons.append(f"분산투자가 부족합니다 (분산점수: {metrics.diversification_score:.1%})")
        
        if metrics.largest_sector_weight > self.max_sector_weight:
            reasons.append(f"특정 섹터 비중이 과도합니다 (최대 섹터: {metrics.largest_sector_weight:.1%})")
        
        if metrics.cash_ratio < self.min_cash_ratio:
            reasons.append(f"현금 비중이 부족합니다 (현재: {metrics.cash_ratio:.1%})")
        elif metrics.cash_ratio > 0.3:
            reasons.append(f"현금 비중이 과도합니다 (현재: {metrics.cash_ratio:.1%})")
        
        # 구체적 액션 플랜 생성
        # (실제로는 더 정교한 로직 필요)
        if metrics.rebalancing_score > 0.5:
            actions.append({
                "type": "reduce_concentration",
                "description": "집중도가 높은 종목/섹터 비중 축소",
                "urgency": "높음"
            })
            
            actions.append({
                "type": "increase_diversification", 
                "description": "다양한 섹터로 분산투자 확대",
                "urgency": "보통"
            })
        
        # 목표 배분 제안 (간단한 예시)
        for allocation in metrics.sector_allocation:
            if allocation.weight > self.max_sector_weight:
                target_allocations[allocation.sector_name] = self.max_sector_weight
            else:
                target_allocations[allocation.sector_name] = allocation.weight
        
        # 기대 효과
        if metrics.rebalancing_score > 0.6:
            expected_improvement = "포트폴리오 안정성 크게 향상 예상"
        elif metrics.rebalancing_score > 0.3:
            expected_improvement = "포트폴리오 균형성 개선 예상"
        else:
            expected_improvement = "현재 포트폴리오 구성 양호"
        
        return RebalancingRecommendation(
            priority=metrics.rebalancing_priority,
            score=metrics.rebalancing_score,
            reasons=reasons,
            actions=actions,
            target_allocations=target_allocations,
            expected_improvement=expected_improvement
        )


# 전역 포트폴리오 분석기 인스턴스 (싱글톤 패턴)
_portfolio_analyzer = None

def get_portfolio_analyzer() -> PortfolioAnalyzer:
    """포트폴리오 분석기 싱글톤 인스턴스 반환"""
    global _portfolio_analyzer
    
    if _portfolio_analyzer is None:
        _portfolio_analyzer = PortfolioAnalyzer()
    
    return _portfolio_analyzer