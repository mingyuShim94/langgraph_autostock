#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Streamlit 메트릭 카드 컴포넌트

트레이딩 시스템의 핵심 성과 지표를 시각화하는 재사용 가능한 컴포넌트들
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
import pandas as pd
import numpy as np

from ..utils.dashboard_utils import (
    format_currency, format_percentage, format_large_number,
    create_metric_delta_color, calculate_percentage_change,
    cached_function
)

class MetricCard:
    """기본 메트릭 카드 클래스"""
    
    def __init__(
        self,
        title: str,
        value: Union[float, int, str],
        delta: Optional[Union[float, str]] = None,
        delta_color: str = "normal",
        help_text: Optional[str] = None,
        prefix: str = "",
        suffix: str = ""
    ):
        self.title = title
        self.value = value
        self.delta = delta
        self.delta_color = delta_color
        self.help_text = help_text
        self.prefix = prefix
        self.suffix = suffix
    
    def render(self) -> None:
        """메트릭 카드 렌더링"""
        formatted_value = f"{self.prefix}{self.value}{self.suffix}"
        
        st.metric(
            label=self.title,
            value=formatted_value,
            delta=self.delta,
            delta_color=self.delta_color,
            help=self.help_text
        )

class FinancialMetricCard(MetricCard):
    """금융 메트릭 전용 카드"""
    
    def __init__(
        self,
        title: str,
        value: float,
        previous_value: Optional[float] = None,
        currency: str = "USD",
        show_percentage_delta: bool = False,
        help_text: Optional[str] = None
    ):
        formatted_value = format_currency(value, currency)
        
        delta = None
        delta_color = "normal"
        
        if previous_value is not None:
            if show_percentage_delta:
                pct_change = calculate_percentage_change(value, previous_value)
                delta = format_percentage(pct_change / 100)
            else:
                delta = format_currency(value - previous_value, currency)
            
            delta_color = create_metric_delta_color(value - previous_value)
        
        super().__init__(
            title=title,
            value=formatted_value,
            delta=delta,
            delta_color=delta_color,
            help_text=help_text
        )

class PercentageMetricCard(MetricCard):
    """백분율 메트릭 카드"""
    
    def __init__(
        self,
        title: str,
        value: float,
        previous_value: Optional[float] = None,
        precision: int = 2,
        help_text: Optional[str] = None
    ):
        formatted_value = format_percentage(value, precision)
        
        delta = None
        delta_color = "normal"
        
        if previous_value is not None:
            delta_change = value - previous_value
            delta = f"{delta_change:+.{precision}%}"
            delta_color = create_metric_delta_color(delta_change)
        
        super().__init__(
            title=title,
            value=formatted_value,
            delta=delta,
            delta_color=delta_color,
            help_text=help_text
        )

class CountMetricCard(MetricCard):
    """카운트 메트릭 카드"""
    
    def __init__(
        self,
        title: str,
        value: int,
        previous_value: Optional[int] = None,
        use_large_format: bool = False,
        help_text: Optional[str] = None
    ):
        formatted_value = format_large_number(value) if use_large_format else str(value)
        
        delta = None
        delta_color = "normal"
        
        if previous_value is not None:
            delta_change = value - previous_value
            delta = f"{delta_change:+,}"
            delta_color = create_metric_delta_color(delta_change)
        
        super().__init__(
            title=title,
            value=formatted_value,
            delta=delta,
            delta_color=delta_color,
            help_text=help_text
        )

def create_trading_overview_cards(metrics_data: Dict[str, Any]) -> None:
    """트레이딩 개요 메트릭 카드들 생성"""
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        FinancialMetricCard(
            title="💰 포트폴리오 가치",
            value=metrics_data.get('portfolio_value', 0.0),
            previous_value=metrics_data.get('previous_portfolio_value'),
            help_text="현재 포트폴리오의 총 가치"
        ).render()
    
    with col2:
        PercentageMetricCard(
            title="📈 총 수익률",
            value=metrics_data.get('total_return_rate', 0.0),
            previous_value=metrics_data.get('previous_return_rate'),
            help_text="시작 이후 누적 수익률"
        ).render()
    
    with col3:
        PercentageMetricCard(
            title="🎯 승률",
            value=metrics_data.get('win_rate', 0.0),
            previous_value=metrics_data.get('previous_win_rate'),
            precision=1,
            help_text="전체 거래 중 수익 거래의 비율"
        ).render()
    
    with col4:
        CountMetricCard(
            title="📊 총 거래",
            value=metrics_data.get('total_trades_count', 0),
            previous_value=metrics_data.get('previous_trades_count'),
            help_text="실행된 총 거래 수"
        ).render()

def create_performance_cards(performance_data: Dict[str, Any]) -> None:
    """성과 분석 메트릭 카드들 생성"""
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        PercentageMetricCard(
            title="📊 일간 수익률",
            value=performance_data.get('daily_return_rate', 0.0),
            help_text="오늘의 수익률"
        ).render()
    
    with col2:
        MetricCard(
            title="⚡ 샤프 비율",
            value=f"{performance_data.get('sharpe_ratio', 0.0):.2f}",
            help_text="위험 대비 수익률 (높을수록 좋음)"
        ).render()
    
    with col3:
        PercentageMetricCard(
            title="📉 최대 손실",
            value=performance_data.get('max_drawdown', 0.0),
            help_text="최고점 대비 최대 하락폭"
        ).render()
    
    with col4:
        MetricCard(
            title="🔥 연속 승리",
            value=performance_data.get('win_streak', 0),
            help_text="현재 연속 수익 거래 수"
        ).render()

def create_cost_cards(cost_data: Dict[str, Any]) -> None:
    """비용 분석 메트릭 카드들 생성"""
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        FinancialMetricCard(
            title="💸 총 비용",
            value=cost_data.get('total_cost', 0.0),
            previous_value=cost_data.get('previous_total_cost'),
            help_text="누적 총 비용 (API 호출, 수수료 등)"
        ).render()
    
    with col2:
        FinancialMetricCard(
            title="🤖 LLM 비용",
            value=cost_data.get('llm_cost', 0.0),
            previous_value=cost_data.get('previous_llm_cost'),
            help_text="LLM API 호출 비용"
        ).render()
    
    with col3:
        FinancialMetricCard(
            title="💰 거래 수수료",
            value=cost_data.get('trading_fees', 0.0),
            previous_value=cost_data.get('previous_trading_fees'),
            help_text="브로커 거래 수수료"
        ).render()
    
    with col4:
        PercentageMetricCard(
            title="📊 비용 효율성",
            value=cost_data.get('cost_efficiency', 0.0),
            help_text="수익 대비 비용 비율 (낮을수록 좋음)"
        ).render()

def create_agent_cards(agent_data: List[Dict[str, Any]]) -> None:
    """에이전트 성과 메트릭 카드들 생성"""
    
    if not agent_data:
        st.info("에이전트 데이터가 없습니다.")
        return
    
    # 상위 4개 에이전트만 표시
    top_agents = sorted(agent_data, key=lambda x: x.get('total_return', 0), reverse=True)[:4]
    
    cols = st.columns(len(top_agents))
    
    for i, agent in enumerate(top_agents):
        with cols[i]:
            st.markdown(f"### 🤖 {agent.get('agent_name', 'Unknown')}")
            
            # 에이전트별 메트릭
            PercentageMetricCard(
                title="수익률",
                value=agent.get('total_return', 0.0),
                help_text=f"{agent.get('agent_name')}의 총 수익률"
            ).render()
            
            CountMetricCard(
                title="거래 수",
                value=agent.get('total_trades', 0),
                help_text="에이전트가 실행한 거래 수"
            ).render()
            
            PercentageMetricCard(
                title="승률",
                value=agent.get('win_rate', 0.0),
                precision=1,
                help_text="에이전트의 거래 승률"
            ).render()

def create_risk_cards(risk_data: Dict[str, Any]) -> None:
    """리스크 관리 메트릭 카드들 생성"""
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        PercentageMetricCard(
            title="📊 포트폴리오 베타",
            value=risk_data.get('portfolio_beta', 0.0),
            help_text="시장 대비 민감도 (1.0 = 시장과 동일)"
        ).render()
    
    with col2:
        PercentageMetricCard(
            title="📉 변동성",
            value=risk_data.get('volatility', 0.0),
            help_text="포트폴리오 수익률의 표준편차"
        ).render()
    
    with col3:
        PercentageMetricCard(
            title="⚠️ VaR (95%)",
            value=risk_data.get('var_95', 0.0),
            help_text="95% 신뢰도에서 예상 최대 손실"
        ).render()
    
    with col4:
        MetricCard(
            title="🛡️ 리스크 점수",
            value=f"{risk_data.get('risk_score', 0)}/100",
            help_text="종합 리스크 평가 점수 (낮을수록 안전)"
        ).render()

def create_market_cards(market_data: Dict[str, Any]) -> None:
    """시장 분석 메트릭 카드들 생성"""
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        PercentageMetricCard(
            title="📈 시장 수익률",
            value=market_data.get('market_return', 0.0),
            help_text="시장 지수 수익률 (S&P 500 등)"
        ).render()
    
    with col2:
        MetricCard(
            title="🌡️ 시장 온도",
            value=market_data.get('market_sentiment', 'Neutral'),
            help_text="시장 심리 상태"
        ).render()
    
    with col3:
        MetricCard(
            title="📊 변동성 지수",
            value=f"{market_data.get('vix', 0.0):.1f}",
            help_text="VIX - 시장 불안정성 지표"
        ).render()
    
    with col4:
        CountMetricCard(
            title="🏢 활성 종목",
            value=market_data.get('active_symbols', 0),
            help_text="현재 거래 중인 종목 수"
        ).render()

def create_compact_metric_row(
    metrics: List[Tuple[str, Union[str, float, int]]], 
    columns: int = 6
) -> None:
    """컴팩트한 메트릭 행 생성"""
    
    cols = st.columns(columns)
    
    for i, (label, value) in enumerate(metrics):
        with cols[i % columns]:
            if isinstance(value, float):
                if 0 < abs(value) < 1:
                    formatted_value = format_percentage(value)
                else:
                    formatted_value = f"{value:.2f}"
            else:
                formatted_value = str(value)
            
            st.metric(label=label, value=formatted_value)

def create_status_card(
    title: str,
    status: str,
    details: Optional[Dict[str, Any]] = None,
    color: str = "normal"
) -> None:
    """상태 표시 카드 생성"""
    
    status_icons = {
        'active': '🟢',
        'inactive': '🔴',
        'warning': '🟡',
        'error': '🔴',
        'success': '✅',
        'pending': '⏳'
    }
    
    icon = status_icons.get(status.lower(), '❓')
    
    st.markdown(f"### {icon} {title}")
    st.write(f"상태: **{status}**")
    
    if details:
        for key, value in details.items():
            st.write(f"- {key}: {value}")

@cached_function(ttl=30)  # 30초 캐시
def get_sample_metrics_data() -> Dict[str, Any]:
    """샘플 메트릭 데이터 생성 (개발용)"""
    
    return {
        # 포트폴리오 데이터
        'portfolio_value': 125_000.0,
        'previous_portfolio_value': 123_500.0,
        'total_return_rate': 0.15,
        'previous_return_rate': 0.12,
        'win_rate': 0.68,
        'previous_win_rate': 0.65,
        'total_trades_count': 127,
        'previous_trades_count': 119,
        
        # 성과 데이터
        'daily_return_rate': 0.023,
        'sharpe_ratio': 1.45,
        'max_drawdown': -0.08,
        'win_streak': 5,
        
        # 비용 데이터
        'total_cost': 2_450.75,
        'previous_total_cost': 2_380.50,
        'llm_cost': 1_200.30,
        'previous_llm_cost': 1_150.20,
        'trading_fees': 1_250.45,
        'previous_trading_fees': 1_230.30,
        'cost_efficiency': 0.019,
        
        # 리스크 데이터
        'portfolio_beta': 1.12,
        'volatility': 0.18,
        'var_95': -0.045,
        'risk_score': 35,
        
        # 시장 데이터
        'market_return': 0.08,
        'market_sentiment': 'Bullish',
        'vix': 18.5,
        'active_symbols': 12
    }

def create_mini_chart_metric(
    title: str,
    current_value: float,
    historical_data: List[float],
    chart_type: str = "line",
    height: int = 60
) -> None:
    """미니 차트가 포함된 메트릭 카드"""
    
    st.subheader(title)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # 현재 값 표시
        if 0 < abs(current_value) < 1:
            formatted_value = format_percentage(current_value)
        elif abs(current_value) > 1000:
            formatted_value = format_currency(current_value)
        else:
            formatted_value = f"{current_value:.2f}"
        
        st.markdown(f"### {formatted_value}")
        
        # 변화율 계산
        if len(historical_data) > 1:
            change = calculate_percentage_change(current_value, historical_data[-2])
            delta_color = "normal" if change >= 0 else "inverse"
            st.markdown(
                f"<span style='color: {'green' if change >= 0 else 'red'}'>"
                f"{change:+.1f}%</span>",
                unsafe_allow_html=True
            )
    
    with col2:
        # 미니 차트
        if chart_type == "line":
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                y=historical_data,
                mode='lines',
                line=dict(width=2, color='#1f77b4'),
                showlegend=False
            ))
            fig.update_layout(
                height=height,
                margin=dict(l=0, r=0, t=0, b=0),
                xaxis=dict(showgrid=False, showticklabels=False),
                yaxis=dict(showgrid=False, showticklabels=False),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
        elif chart_type == "bar":
            fig = go.Figure()
            fig.add_trace(go.Bar(
                y=historical_data,
                marker_color='#1f77b4',
                showlegend=False
            ))
            fig.update_layout(
                height=height,
                margin=dict(l=0, r=0, t=0, b=0),
                xaxis=dict(showgrid=False, showticklabels=False),
                yaxis=dict(showgrid=False, showticklabels=False),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
        
        st.plotly_chart(fig, use_container_width=True)