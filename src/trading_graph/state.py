#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 트레이딩 시스템 운영 그래프 상태 정의

LangGraph 워크플로우에서 사용되는 상태 관리를 위한 TypedDict 정의
"""

from typing import Dict, Any, Optional, List
from typing_extensions import TypedDict
from dataclasses import dataclass, asdict


@dataclass
class PortfolioStatus:
    """포트폴리오 현황 데이터 클래스"""
    total_cash: float  # 총 현금
    total_value: float  # 총 자산가치
    stock_holdings: List[Dict[str, Any]]  # 주식 보유 현황
    cash_ratio: float  # 현금 비중
    stock_positions: Dict[str, Dict[str, Any]]  # 종목별 포지션 정보
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MarketAnalysis:
    """시장 분석 결과 데이터 클래스"""
    market_sentiment: str  # 시장 심리 (bullish/bearish/neutral)
    volume_leaders: List[Dict[str, Any]]  # 거래량 상위 종목
    price_movers: List[Dict[str, Any]]  # 급등락 종목
    risk_factors: List[str]  # 리스크 요소들
    opportunities: List[str]  # 기회 요소들
    market_score: float  # 시장 점수 (0-100)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass 
class TradingPlan:
    """AI 거래 계획 데이터 클래스"""
    actions: List[Dict[str, Any]]  # 거래 액션 리스트
    justification: str  # 전체 거래 근거
    risk_assessment: str  # 리스크 평가
    expected_outcome: str  # 예상 결과
    confidence_score: float  # 신뢰도 점수 (0-100)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RiskValidation:
    """리스크 검증 결과 데이터 클래스"""
    is_valid: bool  # 검증 통과 여부
    cash_sufficient: bool  # 현금 충분성
    position_size_ok: bool  # 포지션 사이징 적절성
    daily_loss_limit_ok: bool  # 일일 손실한도 준수
    price_range_valid: bool  # 가격 범위 유효성
    validation_errors: List[str]  # 검증 오류 목록
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ExecutionResult:
    """주문 실행 결과 데이터 클래스"""
    executed_orders: List[Dict[str, Any]]  # 실행된 주문들
    failed_orders: List[Dict[str, Any]]  # 실패한 주문들
    total_executed: int  # 총 실행 건수
    total_failed: int  # 총 실패 건수
    execution_summary: str  # 실행 요약
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class TradingState(TypedDict):
    """
    운영 그래프 워크플로우 상태
    
    LangGraph의 각 노드에서 접근하고 업데이트하는 중앙 상태 관리
    """
    # 노드별 실행 결과
    portfolio_status: Optional[Dict[str, Any]]  # Node 1: 포트폴리오 진단 결과
    market_analysis: Optional[Dict[str, Any]]   # Node 2: 시장 분석 결과  
    trading_plan: Optional[Dict[str, Any]]      # Node 3: AI 거래 계획
    risk_validation: Optional[Dict[str, Any]]   # Node 4: 리스크 검증 결과
    execution_result: Optional[Dict[str, Any]]  # Node 5: 주문 실행 결과
    final_report: Optional[str]                 # Node 6: 최종 보고서
    
    # 메타데이터
    workflow_id: Optional[str]                  # 워크플로우 실행 ID
    start_time: Optional[str]                   # 시작 시간
    current_node: Optional[str]                 # 현재 실행 중인 노드
    errors: Optional[List[str]]                 # 에러 로그
    
    # 설정 정보
    environment: Optional[str]                  # 실행 환경 (paper/prod)
    mock_mode: Optional[bool]                   # 모의 모드 여부


def update_portfolio_status(state: TradingState, portfolio_data: PortfolioStatus) -> TradingState:
    """포트폴리오 상태 업데이트 헬퍼 함수"""
    return {
        **state,
        "portfolio_status": portfolio_data.to_dict(),
        "current_node": "portfolio_diagnosis"
    }


def update_market_analysis(state: TradingState, market_data: MarketAnalysis) -> TradingState:
    """시장 분석 상태 업데이트 헬퍼 함수"""
    return {
        **state,
        "market_analysis": market_data.to_dict(),
        "current_node": "market_analysis"
    }


def update_trading_plan(state: TradingState, plan_data: TradingPlan) -> TradingState:
    """거래 계획 상태 업데이트 헬퍼 함수"""
    return {
        **state,
        "trading_plan": plan_data.to_dict(),
        "current_node": "ai_decision"
    }


def update_risk_validation(state: TradingState, validation_data: RiskValidation) -> TradingState:
    """리스크 검증 상태 업데이트 헬퍼 함수"""
    return {
        **state,
        "risk_validation": validation_data.to_dict(),
        "current_node": "risk_validation"
    }


def update_execution_result(state: TradingState, execution_data: ExecutionResult) -> TradingState:
    """실행 결과 상태 업데이트 헬퍼 함수"""
    return {
        **state,
        "execution_result": execution_data.to_dict(),
        "current_node": "order_execution"
    }


def update_final_report(state: TradingState, report: str) -> TradingState:
    """최종 보고서 상태 업데이트 헬퍼 함수"""
    return {
        **state,
        "final_report": report,
        "current_node": "reporting"
    }


def add_error(state: TradingState, error_msg: str) -> TradingState:
    """에러 메시지 추가 헬퍼 함수"""
    errors = state.get("errors", [])
    errors.append(error_msg)
    return {
        **state,
        "errors": errors
    }


def get_state_summary(state: TradingState) -> str:
    """상태 요약 정보 반환"""
    summary_parts = []
    
    if state.get("portfolio_status"):
        portfolio = state["portfolio_status"]
        summary_parts.append(f"💰 총자산: {portfolio.get('total_value', 0):,.0f}원")
        summary_parts.append(f"💵 현금: {portfolio.get('total_cash', 0):,.0f}원")
    
    if state.get("market_analysis"):
        market = state["market_analysis"]
        summary_parts.append(f"📈 시장점수: {market.get('market_score', 0):.1f}/100")
        summary_parts.append(f"🎭 시장심리: {market.get('market_sentiment', 'unknown')}")
    
    if state.get("trading_plan"):
        plan = state["trading_plan"]
        actions = plan.get("actions", [])
        summary_parts.append(f"🎯 계획된 거래: {len(actions)}건")
        summary_parts.append(f"🔮 신뢰도: {plan.get('confidence_score', 0):.1f}%")
    
    if state.get("risk_validation"):
        validation = state["risk_validation"]
        is_valid = validation.get("is_valid", False)
        summary_parts.append(f"✅ 리스크검증: {'통과' if is_valid else '실패'}")
    
    if state.get("execution_result"):
        execution = state["execution_result"]
        executed = execution.get("total_executed", 0)
        failed = execution.get("total_failed", 0)
        summary_parts.append(f"⚡ 실행결과: 성공 {executed}건, 실패 {failed}건")
    
    current_node = state.get("current_node", "unknown")
    summary_parts.append(f"🔄 현재단계: {current_node}")
    
    return " | ".join(summary_parts)