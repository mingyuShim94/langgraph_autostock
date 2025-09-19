#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
에이전트 성과 페이지

LangGraph 자율 트레이딩 시스템의 AI 에이전트별 성과 분석 및 기여도 추적
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import numpy as np
import sys
import os

# 프로젝트 루트 경로 추가
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)

from src.streamlit_dashboard.utils.dashboard_utils import (
    cached_function, format_currency, format_percentage,
    get_time_range_filter, create_summary_cards, add_custom_css
)
from src.streamlit_dashboard.utils.chart_helpers import (
    create_agent_performance_chart, create_bar_chart, create_pie_chart,
    COLOR_PALETTE, TRADING_COLORS
)
from src.streamlit_dashboard.components.metrics_cards import (
    create_agent_cards, CountMetricCard, PercentageMetricCard, FinancialMetricCard
)

try:
    from src.database.schema import db_manager
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False

# 페이지 설정
st.set_page_config(
    page_title="에이전트 성과",
    page_icon="🤖",
    layout="wide"
)

add_custom_css()

# 페이지 제목
st.title("🤖 AI 에이전트 성과 분석")
st.markdown("**각 AI 에이전트의 트레이딩 성과와 기여도를 분석합니다**")

# 필터 옵션
col1, col2, col3, col4 = st.columns(4)

with col1:
    time_range = st.selectbox(
        "📅 분석 기간",
        ["1일", "1주", "1개월", "3개월", "6개월", "전체"],
        index=2,
        key="agent_time_range"
    )

with col2:
    metric_type = st.selectbox(
        "📊 성과 지표",
        ["수익률", "거래 수", "승률", "위험조정수익률", "비용효율성"],
        index=0,
        key="agent_metric_type"
    )

with col3:
    agent_filter = st.multiselect(
        "🤖 에이전트 선택",
        ["Portfolio Manager", "Market Analyst", "Risk Controller", "Technical Analyst"],
        default=["Portfolio Manager", "Market Analyst", "Risk Controller", "Technical Analyst"],
        key="agent_filter"
    )

with col4:
    if st.button("🔄 데이터 새로고침", key="agent_refresh"):
        st.cache_data.clear()
        st.rerun()

st.markdown("---")

# 더미 에이전트 데이터 생성
@cached_function(ttl=60)
def get_agent_performance_data():
    """에이전트 성과 데이터 가져오기"""
    agents = [
        {
            'agent_name': 'Portfolio Manager',
            'agent_type': 'portfolio',
            'total_return': 0.15,
            'daily_return': 0.008,
            'total_trades': 45,
            'win_rate': 0.72,
            'avg_trade_size': 10000,
            'total_pnl': 15000,
            'cost_efficiency': 0.02,
            'risk_score': 3.2,
            'active_since': datetime.now() - timedelta(days=90)
        },
        {
            'agent_name': 'Market Analyst',
            'agent_type': 'analysis',
            'total_return': 0.12,
            'daily_return': 0.006,
            'total_trades': 38,
            'win_rate': 0.68,
            'avg_trade_size': 8500,
            'total_pnl': 12000,
            'cost_efficiency': 0.018,
            'risk_score': 2.8,
            'active_since': datetime.now() - timedelta(days=85)
        },
        {
            'agent_name': 'Risk Controller',
            'agent_type': 'risk',
            'total_return': 0.08,
            'daily_return': 0.004,
            'total_trades': 22,
            'win_rate': 0.82,
            'avg_trade_size': 12000,
            'total_pnl': 8000,
            'cost_efficiency': 0.015,
            'risk_score': 1.5,
            'active_since': datetime.now() - timedelta(days=80)
        },
        {
            'agent_name': 'Technical Analyst',
            'agent_type': 'technical',
            'total_return': 0.18,
            'daily_return': 0.01,
            'total_trades': 52,
            'win_rate': 0.65,
            'avg_trade_size': 9000,
            'total_pnl': 18000,
            'cost_efficiency': 0.025,
            'risk_score': 4.1,
            'active_since': datetime.now() - timedelta(days=95)
        }
    ]
    
    # 시간 기반 성과 데이터 생성
    for agent in agents:
        # 30일간의 일별 성과 데이터
        dates = pd.date_range(start=datetime.now() - timedelta(days=30), end=datetime.now(), freq='D')
        daily_returns = np.random.normal(agent['daily_return'], 0.02, len(dates))
        cumulative_returns = (1 + pd.Series(daily_returns)).cumprod() - 1
        
        agent['performance_history'] = pd.DataFrame({
            'date': dates,
            'daily_return': daily_returns,
            'cumulative_return': cumulative_returns,
            'trades_count': np.random.poisson(agent['total_trades'] / 30, len(dates))
        })
    
    return agents

# 에이전트 요약 카드
st.subheader("🏆 에이전트 성과 요약")
agent_data = get_agent_performance_data()

# 필터링된 에이전트 데이터
filtered_agents = [agent for agent in agent_data if agent['agent_name'] in agent_filter]

if filtered_agents:
    create_agent_cards(filtered_agents)
else:
    st.warning("선택된 에이전트가 없습니다.")

st.markdown("---")

# 에이전트 순위 및 비교
st.subheader("📊 에이전트 순위 및 비교")

if filtered_agents:
    # 성과 지표별 순위
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🥇 성과 순위")
        
        # 선택된 지표에 따른 정렬
        metric_map = {
            "수익률": "total_return",
            "거래 수": "total_trades", 
            "승률": "win_rate",
            "위험조정수익률": "total_return",  # 실제로는 샤프 비율 등 계산 필요
            "비용효율성": "cost_efficiency"
        }
        
        sort_key = metric_map.get(metric_type, "total_return")
        sorted_agents = sorted(filtered_agents, key=lambda x: x[sort_key], reverse=True)
        
        ranking_data = []
        for i, agent in enumerate(sorted_agents, 1):
            value = agent[sort_key]
            if sort_key in ["total_return", "win_rate"]:
                formatted_value = format_percentage(value)
            elif sort_key == "cost_efficiency":
                formatted_value = format_percentage(value)
            else:
                formatted_value = f"{value:,}"
            
            ranking_data.append({
                "순위": f"{i}위",
                "에이전트": agent['agent_name'],
                metric_type: formatted_value,
                "타입": agent['agent_type']
            })
        
        st.dataframe(pd.DataFrame(ranking_data), use_container_width=True, hide_index=True)
    
    with col2:
        st.markdown("### 📈 성과 비교 차트")
        
        # 에이전트 성과 비교 차트
        fig = create_agent_performance_chart(filtered_agents, "에이전트 성과 비교")
        st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# 시계열 성과 분석
st.subheader("📈 시계열 성과 분석")

if filtered_agents:
    # 시간 범위 필터 적용
    start_date, end_date = get_time_range_filter(time_range)
    
    # 누적 수익률 차트
    fig = go.Figure()
    
    for agent in filtered_agents:
        history = agent['performance_history']
        filtered_history = history[
            (history['date'] >= start_date) & (history['date'] <= end_date)
        ]
        
        if not filtered_history.empty:
            fig.add_trace(go.Scatter(
                x=filtered_history['date'],
                y=filtered_history['cumulative_return'] * 100,
                mode='lines+markers',
                name=agent['agent_name'],
                line=dict(width=3),
                marker=dict(size=4)
            ))
    
    fig.update_layout(
        title="에이전트별 누적 수익률 추이",
        xaxis_title="날짜",
        yaxis_title="누적 수익률 (%)",
        height=450,
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 일별 거래량 차트
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📊 일별 거래량")
        
        trade_data = []
        for agent in filtered_agents:
            history = agent['performance_history']
            filtered_history = history[
                (history['date'] >= start_date) & (history['date'] <= end_date)
            ]
            
            for _, row in filtered_history.iterrows():
                trade_data.append({
                    'date': row['date'],
                    'agent': agent['agent_name'],
                    'trades': row['trades_count']
                })
        
        if trade_data:
            trade_df = pd.DataFrame(trade_data)
            fig = px.bar(
                trade_df, x='date', y='trades', color='agent',
                title="",
                labels={'trades': '거래 수', 'date': '날짜'}
            )
            fig.update_layout(height=350)
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### 🎯 에이전트별 기여도")
        
        # 에이전트별 총 수익 기여도
        contribution_data = []
        total_pnl = sum(agent['total_pnl'] for agent in filtered_agents)
        
        for agent in filtered_agents:
            contribution = (agent['total_pnl'] / total_pnl) * 100 if total_pnl > 0 else 0
            contribution_data.append({
                'agent': agent['agent_name'],
                'contribution': contribution,
                'pnl': agent['total_pnl']
            })
        
        contrib_df = pd.DataFrame(contribution_data)
        fig = px.pie(
            contrib_df, values='contribution', names='agent',
            title="",
            hover_data=['pnl']
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(height=350)
        st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# 에이전트 상세 분석
st.subheader("🔍 에이전트 상세 분석")

if filtered_agents:
    selected_agent = st.selectbox(
        "분석할 에이전트 선택:",
        [agent['agent_name'] for agent in filtered_agents],
        key="detailed_agent_select"
    )
    
    agent_detail = next(agent for agent in filtered_agents if agent['agent_name'] == selected_agent)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("#### 📊 핵심 지표")
        FinancialMetricCard(
            title="총 수익",
            value=agent_detail['total_pnl']
        ).render()
        
        PercentageMetricCard(
            title="평균 일간 수익률",
            value=agent_detail['daily_return']
        ).render()
        
        CountMetricCard(
            title="평균 거래 규모",
            value=int(agent_detail['avg_trade_size']),
            use_large_format=True
        ).render()
    
    with col2:
        st.markdown("#### 🎯 성과 지표")
        PercentageMetricCard(
            title="총 수익률",
            value=agent_detail['total_return']
        ).render()
        
        PercentageMetricCard(
            title="거래 승률",
            value=agent_detail['win_rate'],
            precision=1
        ).render()
        
        PercentageMetricCard(
            title="비용 효율성",
            value=agent_detail['cost_efficiency']
        ).render()
    
    with col3:
        st.markdown("#### ⚠️ 리스크 지표")
        
        st.metric(
            "리스크 점수",
            f"{agent_detail['risk_score']:.1f}/5.0",
            help="낮을수록 안전 (1=매우안전, 5=고위험)"
        )
        
        # 활동 기간
        days_active = (datetime.now() - agent_detail['active_since']).days
        st.metric(
            "활동 기간",
            f"{days_active}일",
            help="에이전트 활성화 이후 경과 일수"
        )
        
        # 평균 보유 기간 (더미 데이터)
        avg_holding = np.random.uniform(2, 10)
        st.metric(
            "평균 보유 기간",
            f"{avg_holding:.1f}시간",
            help="평균 포지션 보유 시간"
        )
    
    # 에이전트별 상세 차트
    st.markdown("---")
    st.markdown("#### 📈 상세 성과 차트")
    
    history = agent_detail['performance_history']
    
    # 서브플롯 생성
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('일간 수익률', '누적 수익률', '일별 거래 수', '변동성'),
        specs=[[{"secondary_y": False}, {"secondary_y": False}],
               [{"secondary_y": False}, {"secondary_y": False}]]
    )
    
    # 일간 수익률
    fig.add_trace(
        go.Bar(x=history['date'], y=history['daily_return']*100, name='일간수익률'),
        row=1, col=1
    )
    
    # 누적 수익률
    fig.add_trace(
        go.Scatter(x=history['date'], y=history['cumulative_return']*100, mode='lines', name='누적수익률'),
        row=1, col=2
    )
    
    # 일별 거래 수
    fig.add_trace(
        go.Bar(x=history['date'], y=history['trades_count'], name='거래수'),
        row=2, col=1
    )
    
    # 변동성 (rolling standard deviation)
    rolling_vol = history['daily_return'].rolling(window=7).std() * 100
    fig.add_trace(
        go.Scatter(x=history['date'], y=rolling_vol, mode='lines', name='7일변동성'),
        row=2, col=2
    )
    
    fig.update_layout(height=600, showlegend=False)
    fig.update_xaxes(title_text="날짜", row=2, col=1)
    fig.update_xaxes(title_text="날짜", row=2, col=2)
    fig.update_yaxes(title_text="수익률 (%)", row=1, col=1)
    fig.update_yaxes(title_text="누적 수익률 (%)", row=1, col=2)
    fig.update_yaxes(title_text="거래 수", row=2, col=1)
    fig.update_yaxes(title_text="변동성 (%)", row=2, col=2)
    
    st.plotly_chart(fig, use_container_width=True)

# 에이전트 설정 및 관리
st.markdown("---")
st.subheader("⚙️ 에이전트 관리")

col1, col2 = st.columns(2)

with col1:
    st.markdown("#### 🔧 에이전트 제어")
    
    for agent in filtered_agents:
        with st.expander(f"🤖 {agent['agent_name']}"):
            col_a, col_b, col_c = st.columns(3)
            
            with col_a:
                if st.button(f"⏸️ 일시정지", key=f"pause_{agent['agent_name']}"):
                    st.success(f"{agent['agent_name']} 일시정지됨")
            
            with col_b:
                if st.button(f"🚀 재시작", key=f"restart_{agent['agent_name']}"):
                    st.success(f"{agent['agent_name']} 재시작됨")
            
            with col_c:
                if st.button(f"⚙️ 설정", key=f"config_{agent['agent_name']}"):
                    st.info(f"{agent['agent_name']} 설정 페이지로 이동")

with col2:
    st.markdown("#### 📊 전체 에이전트 통계")
    
    total_agents = len(agent_data)
    active_agents = len([a for a in agent_data if a['total_trades'] > 0])
    total_trades = sum(a['total_trades'] for a in agent_data)
    total_pnl = sum(a['total_pnl'] for a in agent_data)
    
    stats_data = {
        "총 에이전트 수": total_agents,
        "활성 에이전트": active_agents,
        "총 거래 수": f"{total_trades:,}",
        "총 수익": format_currency(total_pnl)
    }
    
    for stat, value in stats_data.items():
        st.metric(stat, value)

# 푸터
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray; font-size: 0.8em;'>
    🤖 AI 에이전트 성과 모니터링 | 마지막 업데이트: {timestamp} | 실시간 분석
    </div>
    """.format(timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
    unsafe_allow_html=True
)