#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
거래 히스토리 페이지

LangGraph 자율 트레이딩 시스템의 모든 거래 기록을 상세히 분석하고 추적
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
    get_time_range_filter, create_summary_cards, add_custom_css,
    filter_dataframe_by_date
)
from src.streamlit_dashboard.utils.chart_helpers import (
    create_candlestick_chart, create_line_chart, create_bar_chart,
    create_heatmap, COLOR_PALETTE, TRADING_COLORS
)
from src.streamlit_dashboard.components.metrics_cards import (
    CountMetricCard, FinancialMetricCard, PercentageMetricCard
)

try:
    from src.database.schema import db_manager
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False

# 페이지 설정
st.set_page_config(
    page_title="거래 히스토리",
    page_icon="📊",
    layout="wide"
)

add_custom_css()

# 페이지 제목
st.title("📊 거래 히스토리 및 포트폴리오 분석")
st.markdown("**모든 거래 기록을 상세히 추적하고 성과를 분석합니다**")

# 필터 및 제어
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    time_range = st.selectbox(
        "📅 조회 기간",
        ["1일", "1주", "1개월", "3개월", "6개월", "1년", "전체"],
        index=2,
        key="history_time_range"
    )

with col2:
    symbol_filter = st.multiselect(
        "🏢 종목 필터",
        ["AAPL", "GOOGL", "MSFT", "TSLA", "NVDA", "AMZN", "META"],
        key="history_symbol_filter"
    )

with col3:
    action_filter = st.multiselect(
        "📈 거래 유형",
        ["BUY", "SELL"],
        default=["BUY", "SELL"],
        key="history_action_filter"
    )

with col4:
    status_filter = st.multiselect(
        "✅ 거래 상태",
        ["COMPLETED", "PENDING", "FAILED", "CANCELLED"],
        default=["COMPLETED"],
        key="history_status_filter"
    )

with col5:
    if st.button("🔄 데이터 새로고침", key="history_refresh"):
        st.cache_data.clear()
        st.rerun()

st.markdown("---")

# 거래 데이터 생성
@cached_function(ttl=30)
def get_trading_history_data():
    """거래 히스토리 데이터 생성"""
    
    # 더미 거래 데이터 생성
    symbols = ["AAPL", "GOOGL", "MSFT", "TSLA", "NVDA", "AMZN", "META", "NFLX", "CRM", "ORCL"]
    agents = ["Portfolio Manager", "Market Analyst", "Risk Controller", "Technical Analyst"]
    
    trades = []
    trade_id = 1000
    
    # 90일간의 거래 생성
    for days_ago in range(90, 0, -1):
        trade_date = datetime.now() - timedelta(days=days_ago)
        
        # 하루에 3-8개 거래 생성
        daily_trades = np.random.randint(3, 9)
        
        for _ in range(daily_trades):
            symbol = np.random.choice(symbols)
            action = np.random.choice(["BUY", "SELL"])
            agent = np.random.choice(agents)
            
            # 가격 범위 설정 (종목별)
            price_ranges = {
                "AAPL": (150, 200), "GOOGL": (2500, 3200), "MSFT": (300, 400),
                "TSLA": (180, 280), "NVDA": (400, 600), "AMZN": (3000, 3800),
                "META": (250, 350), "NFLX": (400, 500), "CRM": (200, 280), "ORCL": (80, 120)
            }
            
            min_price, max_price = price_ranges.get(symbol, (100, 200))
            price = np.random.uniform(min_price, max_price)
            quantity = np.random.randint(10, 500)
            
            # 거래 상태 (대부분 완료)
            status_weights = [0.85, 0.05, 0.05, 0.05]  # COMPLETED, PENDING, FAILED, CANCELLED
            status = np.random.choice(["COMPLETED", "PENDING", "FAILED", "CANCELLED"], p=status_weights)
            
            # P&L 계산 (완료된 거래만)
            if status == "COMPLETED":
                # 승률 70% 가정
                is_profit = np.random.random() < 0.70
                if is_profit:
                    pnl = np.random.uniform(0.5, 5.0) * quantity
                else:
                    pnl = -np.random.uniform(0.2, 3.0) * quantity
            else:
                pnl = 0.0
            
            # 거래 수수료
            commission = quantity * price * 0.001  # 0.1% 수수료
            
            # 거래 시간 (시장 시간 내)
            trade_time = trade_date.replace(
                hour=np.random.randint(9, 16),
                minute=np.random.randint(0, 60),
                second=np.random.randint(0, 60)
            )
            
            trades.append({
                'trade_id': f"T{trade_id:06d}",
                'timestamp': trade_time,
                'symbol': symbol,
                'action': action,
                'quantity': quantity,
                'price': price,
                'total_value': quantity * price,
                'status': status,
                'agent': agent,
                'pnl': pnl,
                'commission': commission,
                'net_pnl': pnl - commission,
                'decision_confidence': np.random.uniform(0.6, 0.95),
                'market_condition': np.random.choice(["Bull", "Bear", "Sideways"]),
                'execution_time_ms': np.random.randint(100, 2000)
            })
            
            trade_id += 1
    
    return pd.DataFrame(trades)

# 포트폴리오 데이터 생성
@cached_function(ttl=60)
def get_portfolio_data():
    """현재 포트폴리오 상태 데이터"""
    
    symbols = ["AAPL", "GOOGL", "MSFT", "TSLA", "NVDA", "AMZN", "META"]
    portfolio = []
    
    for symbol in symbols:
        # 랜덤 포지션 생성
        if np.random.random() > 0.3:  # 70% 확률로 포지션 보유
            quantity = np.random.randint(50, 300)
            avg_cost = np.random.uniform(100, 400)
            current_price = avg_cost * np.random.uniform(0.85, 1.25)  # ±25% 변동
            
            market_value = quantity * current_price
            cost_basis = quantity * avg_cost
            unrealized_pnl = market_value - cost_basis
            unrealized_pnl_pct = (unrealized_pnl / cost_basis) * 100
            
            portfolio.append({
                'symbol': symbol,
                'quantity': quantity,
                'avg_cost': avg_cost,
                'current_price': current_price,
                'market_value': market_value,
                'cost_basis': cost_basis,
                'unrealized_pnl': unrealized_pnl,
                'unrealized_pnl_pct': unrealized_pnl_pct,
                'weight': 0  # 나중에 계산
            })
    
    portfolio_df = pd.DataFrame(portfolio)
    
    # 포트폴리오 비중 계산
    total_value = portfolio_df['market_value'].sum()
    portfolio_df['weight'] = (portfolio_df['market_value'] / total_value) * 100
    
    return portfolio_df

# 거래 요약 통계
st.subheader("📈 거래 요약 통계")

trades_df = get_trading_history_data()

# 필터 적용
start_date, end_date = get_time_range_filter(time_range)
filtered_trades = filter_dataframe_by_date(trades_df, 'timestamp', start_date, end_date)

if symbol_filter:
    filtered_trades = filtered_trades[filtered_trades['symbol'].isin(symbol_filter)]
if action_filter:
    filtered_trades = filtered_trades[filtered_trades['action'].isin(action_filter)]
if status_filter:
    filtered_trades = filtered_trades[filtered_trades['status'].isin(status_filter)]

# 통계 계산
total_trades = len(filtered_trades)
completed_trades = len(filtered_trades[filtered_trades['status'] == 'COMPLETED'])
total_volume = filtered_trades['total_value'].sum()
total_pnl = filtered_trades[filtered_trades['status'] == 'COMPLETED']['net_pnl'].sum()
win_trades = len(filtered_trades[(filtered_trades['status'] == 'COMPLETED') & (filtered_trades['net_pnl'] > 0)])
win_rate = (win_trades / completed_trades) * 100 if completed_trades > 0 else 0

# 요약 카드
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    CountMetricCard(
        title="📊 총 거래 수",
        value=total_trades,
        help_text="선택된 기간의 총 거래 수"
    ).render()

with col2:
    CountMetricCard(
        title="✅ 완료된 거래",
        value=completed_trades,
        help_text="성공적으로 실행된 거래"
    ).render()

with col3:
    FinancialMetricCard(
        title="💰 총 거래량",
        value=total_volume,
        help_text="총 거래 금액"
    ).render()

with col4:
    FinancialMetricCard(
        title="💎 순손익",
        value=total_pnl,
        help_text="수수료 차감 후 순손익"
    ).render()

with col5:
    PercentageMetricCard(
        title="🎯 승률",
        value=win_rate / 100,
        precision=1,
        help_text="수익 거래 비율"
    ).render()

st.markdown("---")

# 거래 차트 및 분석
col1, col2 = st.columns(2)

with col1:
    st.subheader("📈 일별 거래량 추이")
    
    # 일별 거래 집계
    daily_trades = filtered_trades.groupby(filtered_trades['timestamp'].dt.date).agg({
        'trade_id': 'count',
        'total_value': 'sum',
        'net_pnl': 'sum'
    }).reset_index()
    daily_trades.columns = ['date', 'trade_count', 'volume', 'pnl']
    
    if not daily_trades.empty:
        fig = create_line_chart(
            daily_trades, 'date', 'trade_count',
            title="", x_title="날짜", y_title="거래 수",
            color=COLOR_PALETTE['primary']
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("선택된 조건에 해당하는 거래가 없습니다.")

with col2:
    st.subheader("💰 일별 손익 추이")
    
    if not daily_trades.empty:
        fig = go.Figure()
        
        # 손익 바 차트 (양수는 초록, 음수는 빨강)
        colors = [TRADING_COLORS['profit'] if pnl >= 0 else TRADING_COLORS['loss'] for pnl in daily_trades['pnl']]
        
        fig.add_trace(go.Bar(
            x=daily_trades['date'],
            y=daily_trades['pnl'],
            marker_color=colors,
            name='일별 손익',
            hovertemplate='날짜: %{x}<br>손익: $%{y:.2f}<extra></extra>'
        ))
        
        fig.update_layout(
            title="",
            xaxis_title="날짜",
            yaxis_title="손익 ($)",
            height=400,
            showlegend=False
        )
        fig.add_hline(y=0, line_dash="dash", line_color="gray")
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("손익 데이터가 없습니다.")

# 종목별 분석
st.markdown("---")
st.subheader("🏢 종목별 거래 분석")

if not filtered_trades.empty:
    # 종목별 집계
    symbol_analysis = filtered_trades.groupby('symbol').agg({
        'trade_id': 'count',
        'quantity': 'sum',
        'total_value': 'sum',
        'net_pnl': 'sum',
        'commission': 'sum'
    }).reset_index()
    
    symbol_analysis.columns = ['symbol', 'trade_count', 'total_quantity', 'total_value', 'net_pnl', 'total_commission']
    symbol_analysis['avg_trade_size'] = symbol_analysis['total_value'] / symbol_analysis['trade_count']
    symbol_analysis['pnl_per_trade'] = symbol_analysis['net_pnl'] / symbol_analysis['trade_count']
    
    # 종목별 수익률 계산
    symbol_analysis['return_rate'] = (symbol_analysis['net_pnl'] / symbol_analysis['total_value']) * 100
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📊 종목별 거래 현황")
        
        # 종목별 거래 수 차트
        fig = create_bar_chart(
            symbol_analysis.head(10), 'symbol', 'trade_count',
            title="", x_title="종목", y_title="거래 수",
            height=350
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### 💰 종목별 손익")
        
        # 종목별 손익 차트
        colors = [TRADING_COLORS['profit'] if pnl >= 0 else TRADING_COLORS['loss'] 
                 for pnl in symbol_analysis['net_pnl']]
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=symbol_analysis['symbol'],
            y=symbol_analysis['net_pnl'],
            marker_color=colors,
            name='종목별 손익'
        ))
        
        fig.update_layout(
            title="",
            xaxis_title="종목",
            yaxis_title="순손익 ($)",
            height=350,
            showlegend=False
        )
        fig.add_hline(y=0, line_dash="dash", line_color="gray")
        
        st.plotly_chart(fig, use_container_width=True)
    
    # 종목별 상세 테이블
    st.markdown("### 📋 종목별 상세 통계")
    
    display_df = symbol_analysis.copy()
    display_df['거래수'] = display_df['trade_count']
    display_df['총거래량'] = display_df['total_quantity'].apply(lambda x: f"{x:,}")
    display_df['총거래금액'] = display_df['total_value'].apply(lambda x: format_currency(x))
    display_df['순손익'] = display_df['net_pnl'].apply(lambda x: format_currency(x))
    display_df['수익률'] = display_df['return_rate'].apply(lambda x: f"{x:.2f}%")
    display_df['평균거래규모'] = display_df['avg_trade_size'].apply(lambda x: format_currency(x))
    
    st.dataframe(
        display_df[['symbol', '거래수', '총거래량', '총거래금액', '순손익', '수익률', '평균거래규모']].rename(
            columns={'symbol': '종목'}
        ),
        use_container_width=True,
        hide_index=True
    )

# 현재 포트폴리오 상태
st.markdown("---")
st.subheader("💼 현재 포트폴리오")

portfolio_df = get_portfolio_data()

if not portfolio_df.empty:
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.markdown("### 📊 포트폴리오 구성")
        
        # 포트폴리오 비중 파이 차트
        fig = px.pie(
            portfolio_df, 
            values='market_value', 
            names='symbol',
            title="",
            hover_data=['quantity', 'current_price']
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### 💰 포트폴리오 요약")
        
        total_market_value = portfolio_df['market_value'].sum()
        total_cost_basis = portfolio_df['cost_basis'].sum()
        total_unrealized_pnl = portfolio_df['unrealized_pnl'].sum()
        total_unrealized_pct = (total_unrealized_pnl / total_cost_basis) * 100 if total_cost_basis > 0 else 0
        
        st.metric("총 시가", format_currency(total_market_value))
        st.metric("투자 원금", format_currency(total_cost_basis))
        st.metric("평가 손익", format_currency(total_unrealized_pnl))
        st.metric("수익률", f"{total_unrealized_pct:.2f}%")
    
    with col3:
        st.markdown("### 🏆 최고/최저 종목")
        
        best_performer = portfolio_df.loc[portfolio_df['unrealized_pnl_pct'].idxmax()]
        worst_performer = portfolio_df.loc[portfolio_df['unrealized_pnl_pct'].idxmin()]
        
        st.success(f"🥇 최고: {best_performer['symbol']}")
        st.write(f"   {best_performer['unrealized_pnl_pct']:.1f}%")
        st.write(f"   {format_currency(best_performer['unrealized_pnl'])}")
        
        st.error(f"🥉 최저: {worst_performer['symbol']}")
        st.write(f"   {worst_performer['unrealized_pnl_pct']:.1f}%")
        st.write(f"   {format_currency(worst_performer['unrealized_pnl'])}")
    
    # 포트폴리오 상세 테이블
    st.markdown("### 📋 포트폴리오 상세")
    
    portfolio_display = portfolio_df.copy()
    portfolio_display['종목'] = portfolio_display['symbol']
    portfolio_display['수량'] = portfolio_display['quantity'].apply(lambda x: f"{x:,}")
    portfolio_display['평균단가'] = portfolio_display['avg_cost'].apply(lambda x: f"${x:.2f}")
    portfolio_display['현재가'] = portfolio_display['current_price'].apply(lambda x: f"${x:.2f}")
    portfolio_display['시가총액'] = portfolio_display['market_value'].apply(lambda x: format_currency(x))
    portfolio_display['평가손익'] = portfolio_display['unrealized_pnl'].apply(lambda x: format_currency(x))
    portfolio_display['수익률'] = portfolio_display['unrealized_pnl_pct'].apply(lambda x: f"{x:.2f}%")
    portfolio_display['비중'] = portfolio_display['weight'].apply(lambda x: f"{x:.1f}%")
    
    st.dataframe(
        portfolio_display[['종목', '수량', '평균단가', '현재가', '시가총액', '평가손익', '수익률', '비중']],
        use_container_width=True,
        hide_index=True
    )

# 에이전트별 거래 분석
st.markdown("---")
st.subheader("🤖 에이전트별 거래 분석")

if not filtered_trades.empty:
    agent_analysis = filtered_trades.groupby('agent').agg({
        'trade_id': 'count',
        'total_value': 'sum',
        'net_pnl': 'sum',
        'decision_confidence': 'mean'
    }).reset_index()
    
    agent_analysis.columns = ['agent', 'trade_count', 'total_value', 'net_pnl', 'avg_confidence']
    agent_analysis['success_rate'] = 0  # 나중에 계산
    
    # 각 에이전트의 성공률 계산
    for i, agent in enumerate(agent_analysis['agent']):
        agent_trades = filtered_trades[
            (filtered_trades['agent'] == agent) & 
            (filtered_trades['status'] == 'COMPLETED')
        ]
        if len(agent_trades) > 0:
            success_count = len(agent_trades[agent_trades['net_pnl'] > 0])
            agent_analysis.loc[i, 'success_rate'] = (success_count / len(agent_trades)) * 100
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📊 에이전트별 거래 수")
        
        fig = create_bar_chart(
            agent_analysis, 'agent', 'trade_count',
            title="", x_title="에이전트", y_title="거래 수",
            height=350
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### 🎯 에이전트별 성과")
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=agent_analysis['avg_confidence'],
            y=agent_analysis['success_rate'],
            mode='markers+text',
            text=agent_analysis['agent'],
            textposition='top center',
            marker=dict(
                size=agent_analysis['trade_count'],
                sizemode='diameter',
                sizeref=2. * max(agent_analysis['trade_count']) / (20. ** 2),
                color=agent_analysis['net_pnl'],
                colorscale='RdYlGn',
                showscale=True,
                colorbar=dict(title="순손익 ($)")
            ),
            hovertemplate='에이전트: %{text}<br>' +
                         '신뢰도: %{x:.2f}<br>' +
                         '성공률: %{y:.1f}%<br>' +
                         '<extra></extra>'
        ))
        
        fig.update_layout(
            title="에이전트 성과 매트릭스",
            xaxis_title="평균 의사결정 신뢰도",
            yaxis_title="성공률 (%)",
            height=350
        )
        
        st.plotly_chart(fig, use_container_width=True)

# 거래 상세 로그
st.markdown("---")
st.subheader("📋 최근 거래 상세 로그")

# 페이지네이션을 위한 설정
page_size = 20
total_pages = (len(filtered_trades) + page_size - 1) // page_size

col1, col2, col3 = st.columns([1, 2, 1])

with col1:
    page_number = st.number_input(
        "페이지",
        min_value=1,
        max_value=max(1, total_pages),
        value=1,
        key="trade_page"
    )

with col2:
    st.write(f"총 {len(filtered_trades)}개 거래 중 {(page_number-1)*page_size + 1}-{min(page_number*page_size, len(filtered_trades))} 표시")

with col3:
    sort_column = st.selectbox(
        "정렬 기준",
        ["timestamp", "net_pnl", "total_value", "decision_confidence"],
        key="trade_sort"
    )

# 데이터 정렬 및 페이지네이션
sorted_trades = filtered_trades.sort_values(sort_column, ascending=False)
start_idx = (page_number - 1) * page_size
end_idx = start_idx + page_size
page_trades = sorted_trades.iloc[start_idx:end_idx]

# 거래 상세 테이블
if not page_trades.empty:
    detail_df = page_trades.copy()
    detail_df['거래ID'] = detail_df['trade_id']
    detail_df['시간'] = detail_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
    detail_df['종목'] = detail_df['symbol']
    detail_df['타입'] = detail_df['action'].map({'BUY': '🔵 매수', 'SELL': '🔴 매도'})
    detail_df['수량'] = detail_df['quantity'].apply(lambda x: f"{x:,}")
    detail_df['가격'] = detail_df['price'].apply(lambda x: f"${x:.2f}")
    detail_df['총액'] = detail_df['total_value'].apply(lambda x: format_currency(x))
    detail_df['손익'] = detail_df['net_pnl'].apply(lambda x: format_currency(x))
    detail_df['상태'] = detail_df['status'].map({
        'COMPLETED': '✅ 완료',
        'PENDING': '⏳ 대기',
        'FAILED': '❌ 실패',
        'CANCELLED': '🚫 취소'
    })
    detail_df['에이전트'] = detail_df['agent']
    detail_df['신뢰도'] = detail_df['decision_confidence'].apply(lambda x: f"{x:.2f}")
    
    st.dataframe(
        detail_df[['거래ID', '시간', '종목', '타입', '수량', '가격', '총액', '손익', '상태', '에이전트', '신뢰도']],
        use_container_width=True,
        hide_index=True
    )
else:
    st.info("표시할 거래가 없습니다.")

# 푸터
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray; font-size: 0.8em;'>
    📊 거래 히스토리 추적 | 마지막 업데이트: {timestamp} | 실시간 포트폴리오
    </div>
    """.format(timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
    unsafe_allow_html=True
)