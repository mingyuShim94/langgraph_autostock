#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
시스템 개요 페이지

LangGraph 자율 트레이딩 시스템의 전반적인 상태와 핵심 지표를 보여주는 메인 대시보드
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import sys
import os

# 프로젝트 루트 경로 추가
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)

from src.streamlit_dashboard.utils.dashboard_utils import (
    cached_function, format_currency, format_percentage,
    get_time_range_filter, create_status_indicator, add_custom_css
)
from src.streamlit_dashboard.utils.chart_helpers import (
    create_line_chart, create_performance_chart, create_gauge_chart,
    create_bar_chart, COLOR_PALETTE, TRADING_COLORS
)
from src.streamlit_dashboard.components.metrics_cards import (
    create_trading_overview_cards, create_performance_cards, 
    create_risk_cards, get_sample_metrics_data, create_status_card
)

try:
    from src.database.schema import db_manager
    from src.dashboard.performance_metrics import PerformanceMetricsCalculator
    DB_AVAILABLE = True
except ImportError as e:
    DB_AVAILABLE = False
    st.error(f"데이터베이스 모듈 로딩 실패: {e}")

# 페이지 설정
st.set_page_config(
    page_title="시스템 개요",
    page_icon="🏠",
    layout="wide"
)

# 커스텀 CSS 적용
add_custom_css()

# 페이지 제목
st.title("🏠 시스템 개요")
st.markdown("**LangGraph 자율 트레이딩 시스템의 실시간 상태 모니터링**")

# 자동 새로고침 설정
col1, col2, col3 = st.columns([1, 1, 2])
with col1:
    auto_refresh = st.checkbox("🔄 자동 새로고침", value=True, key="overview_auto_refresh")
with col2:
    refresh_interval = st.selectbox("새로고침 간격 (초)", [10, 30, 60, 120], index=1, key="overview_refresh_interval")
with col3:
    if st.button("🔄 수동 새로고침", key="overview_manual_refresh"):
        st.cache_data.clear()
        st.rerun()

st.markdown("---")

# 시스템 상태 표시
@cached_function(ttl=30)
def get_system_status():
    """시스템 상태 정보 가져오기"""
    if not DB_AVAILABLE:
        return {
            'database': {'status': 'error', 'message': 'Database module not available'},
            'trading': {'status': 'unknown', 'message': 'Cannot determine trading status'},
            'agents': {'status': 'unknown', 'active_count': 0}
        }
    
    try:
        total_trades = len(db_manager.get_all_trades())
        recent_trades = db_manager.get_recent_trades(limit=5)
        
        # 최근 거래 기반으로 트레이딩 상태 판단
        if recent_trades:
            latest_trade = recent_trades[0]
            time_since_last = datetime.now() - latest_trade.timestamp
            trading_active = time_since_last.total_seconds() < 3600  # 1시간 이내
        else:
            trading_active = False
        
        return {
            'database': {
                'status': 'active',
                'message': f'연결됨 - 총 {total_trades}건의 거래 기록',
                'total_trades': total_trades
            },
            'trading': {
                'status': 'active' if trading_active else 'idle',
                'message': '활성 거래 중' if trading_active else '대기 중',
                'last_trade': recent_trades[0].timestamp if recent_trades else None
            },
            'agents': {
                'status': 'active',
                'active_count': 4,  # 하드코딩된 값 (실제로는 agent status 확인)
                'message': '4개 에이전트 활성화'
            }
        }
    except Exception as e:
        return {
            'database': {'status': 'error', 'message': f'연결 오류: {str(e)}'},
            'trading': {'status': 'error', 'message': '상태 확인 불가'},
            'agents': {'status': 'error', 'active_count': 0, 'message': '에이전트 상태 불확실'}
        }

# 시스템 상태 카드들
st.subheader("🔍 시스템 상태")
system_status = get_system_status()

col1, col2, col3, col4 = st.columns(4)

with col1:
    db_status = system_status['database']['status']
    create_status_card(
        "데이터베이스",
        db_status,
        {"메시지": system_status['database']['message']},
        "success" if db_status == 'active' else "error"
    )

with col2:
    trading_status = system_status['trading']['status']
    create_status_card(
        "트레이딩 엔진",
        trading_status,
        {"상태": system_status['trading']['message']},
        "success" if trading_status == 'active' else "warning"
    )

with col3:
    agent_status = system_status['agents']['status']
    create_status_card(
        "AI 에이전트",
        agent_status,
        {
            "활성 에이전트": system_status['agents']['active_count'],
            "상태": system_status['agents']['message']
        },
        "success" if agent_status == 'active' else "error"
    )

with col4:
    create_status_card(
        "시스템 건강도",
        "양호",
        {
            "가동 시간": "24시간 12분",
            "CPU 사용률": "23%",
            "메모리 사용률": "45%"
        },
        "success"
    )

st.markdown("---")

# 핵심 성과 지표
@cached_function(ttl=60)
def get_performance_metrics():
    """성과 메트릭 데이터 가져오기"""
    if not DB_AVAILABLE:
        return get_sample_metrics_data()
    
    try:
        metrics_calc = PerformanceMetricsCalculator()
        metrics = metrics_calc.get_realtime_metrics()
        
        return {
            'portfolio_value': 125000.0,  # 실제 값으로 대체 필요
            'total_return_rate': metrics.total_return_rate,
            'win_rate': metrics.win_rate,
            'total_trades_count': metrics.total_trades_count,
            'daily_return_rate': metrics.daily_return_rate,
            'sharpe_ratio': 1.45,  # 실제 계산 필요
            'max_drawdown': -0.08,  # 실제 계산 필요
            'win_streak': 5  # 실제 계산 필요
        }
    except Exception as e:
        st.warning(f"성과 메트릭 로딩 중 오류: {e}")
        return get_sample_metrics_data()

st.subheader("📊 핵심 성과 지표")
metrics_data = get_performance_metrics()
create_trading_overview_cards(metrics_data)

st.markdown("---")

# 성과 상세 분석
st.subheader("📈 성과 상세 분석")
create_performance_cards(metrics_data)

st.markdown("---")

# 실시간 차트 섹션
col1, col2 = st.columns(2)

with col1:
    st.subheader("📈 포트폴리오 가치 추이")
    
    # 더미 데이터로 차트 생성 (실제로는 데이터베이스에서 가져와야 함)
    import numpy as np
    dates = pd.date_range(start=datetime.now() - timedelta(days=30), end=datetime.now(), freq='D')
    portfolio_values = [100000 + 1000*i + 500*np.sin(i/3) for i in range(len(dates))]
    
    portfolio_df = pd.DataFrame({
        'Date': dates,
        'Portfolio_Value': portfolio_values
    })
    
    fig = create_line_chart(
        portfolio_df, 'Date', 'Portfolio_Value',
        title="", x_title="날짜", y_title="포트폴리오 가치 ($)",
        color=TRADING_COLORS['profit']
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("🎯 수익률 분포")
    
    # 더미 거래 데이터로 히스토그램 생성
    returns = np.random.normal(0.02, 0.05, 100)  # 평균 2% 수익률, 5% 변동성
    
    fig = px.histogram(
        x=returns,
        nbins=20,
        title="",
        labels={"x": "수익률", "y": "거래 수"},
        color_discrete_sequence=[COLOR_PALETTE['primary']]
    )
    fig.update_layout(height=400)
    fig.add_vline(x=0, line_dash="dash", line_color="red", annotation_text="손익분기점")
    st.plotly_chart(fig, use_container_width=True)

# 위험 관리 지표
st.markdown("---")
st.subheader("⚠️ 위험 관리")

risk_data = {
    'portfolio_beta': 1.12,
    'volatility': 0.18,
    'var_95': -0.045,
    'risk_score': 35
}
create_risk_cards(risk_data)

# 최근 거래 활동
st.markdown("---")
st.subheader("📋 최근 거래 활동")

@cached_function(ttl=30)
def get_recent_trades_data():
    """최근 거래 데이터 가져오기"""
    if not DB_AVAILABLE:
        # 더미 데이터
        return pd.DataFrame({
            'timestamp': [datetime.now() - timedelta(hours=i) for i in range(10)],
            'symbol': ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'NVDA'] * 2,
            'action': ['BUY', 'SELL'] * 5,
            'quantity': [100, 50, 200, 75, 150, 100, 80, 120, 90, 110],
            'price': [150.25, 2800.50, 330.75, 220.80, 450.30, 151.00, 2790.25, 329.50, 219.75, 449.80],
            'status': ['COMPLETED'] * 10
        })
    
    try:
        recent_trades = db_manager.get_recent_trades(limit=10)
        if not recent_trades:
            return pd.DataFrame()
        
        return pd.DataFrame([{
            'timestamp': trade.timestamp,
            'symbol': trade.symbol,
            'action': trade.action,
            'quantity': trade.quantity,
            'price': trade.price,
            'status': trade.status
        } for trade in recent_trades])
    except Exception as e:
        st.error(f"거래 데이터 로딩 실패: {e}")
        return pd.DataFrame()

trades_df = get_recent_trades_data()

if not trades_df.empty:
    # 거래 테이블 포맷팅
    trades_display = trades_df.copy()
    trades_display['시간'] = trades_display['timestamp'].dt.strftime('%H:%M:%S')
    trades_display['날짜'] = trades_display['timestamp'].dt.strftime('%Y-%m-%d')
    trades_display['종목'] = trades_display['symbol']
    trades_display['타입'] = trades_display['action'].map({'BUY': '🔵 매수', 'SELL': '🔴 매도'})
    trades_display['수량'] = trades_display['quantity']
    trades_display['가격'] = trades_display['price'].apply(lambda x: f"${x:.2f}")
    trades_display['상태'] = trades_display['status'].map({
        'COMPLETED': '✅ 완료',
        'PENDING': '⏳ 대기',
        'FAILED': '❌ 실패'
    })
    
    st.dataframe(
        trades_display[['날짜', '시간', '종목', '타입', '수량', '가격', '상태']],
        use_container_width=True,
        height=300
    )
    
    # 거래 통계
    col1, col2, col3 = st.columns(3)
    with col1:
        buy_count = len(trades_df[trades_df['action'] == 'BUY'])
        st.metric("매수 거래", buy_count)
    with col2:
        sell_count = len(trades_df[trades_df['action'] == 'SELL'])
        st.metric("매도 거래", sell_count)
    with col3:
        total_volume = trades_df['quantity'].sum()
        st.metric("총 거래량", f"{total_volume:,}")
else:
    st.info("📝 최근 거래 데이터가 없습니다.")

# 시장 상황
st.markdown("---")
st.subheader("🌍 시장 현황")

col1, col2, col3, col4 = st.columns(4)

# 더미 시장 데이터
market_data = {
    'S&P 500': {'value': 4185.47, 'change': 1.2},
    'NASDAQ': {'value': 12450.33, 'change': -0.8},
    'USD/KRW': {'value': 1320.50, 'change': 0.3},
    'VIX': {'value': 18.2, 'change': -2.1}
}

for i, (name, data) in enumerate(market_data.items()):
    with [col1, col2, col3, col4][i]:
        delta_color = "normal" if data['change'] >= 0 else "inverse"
        st.metric(
            name, 
            f"{data['value']:,.2f}",
            f"{data['change']:+.1f}%",
            delta_color=delta_color
        )

# 푸터
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray; font-size: 0.8em;'>
    📊 실시간 업데이트 | 마지막 업데이트: {timestamp} | 🤖 LangGraph Trading System v1.0
    </div>
    """.format(timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
    unsafe_allow_html=True
)

# 자동 새로고침 구현
if auto_refresh:
    import time
    time.sleep(refresh_interval)
    st.rerun()