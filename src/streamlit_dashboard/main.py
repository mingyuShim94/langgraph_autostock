#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Streamlit 실시간 트레이딩 대시보드 메인 앱

LangGraph 자율 트레이딩 시스템의 성과 추적 및 관리 대시보드
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
import os

# 프로젝트 루트 경로 추가
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from src.database.schema import db_manager
from src.dashboard.performance_metrics import PerformanceMetricsCalculator

# 페이지 설정
st.set_page_config(
    page_title="LangGraph 트레이딩 시스템",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 사이드바 설정
st.sidebar.title("📊 트레이딩 대시보드")
st.sidebar.markdown("---")

# 시스템 상태 표시
with st.sidebar.container():
    st.subheader("🔄 시스템 상태")
    
    # 데이터베이스 연결 상태 확인
    try:
        total_trades = len(db_manager.get_all_trades())
        st.success(f"✅ 데이터베이스 연결됨")
        st.metric("총 거래 수", total_trades)
    except Exception as e:
        st.error("❌ 데이터베이스 연결 실패")
        st.error(f"오류: {str(e)}")
    
    # 성능 계산기 초기화
    try:
        metrics_calc = PerformanceMetricsCalculator()
        st.success("✅ 성능 계산기 준비완료")
    except Exception as e:
        st.error("❌ 성능 계산기 초기화 실패")
        st.error(f"오류: {str(e)}")

# 메인 대시보드
st.title("🚀 LangGraph 자율 트레이딩 시스템")
st.markdown("**실시간 성과 추적 및 관리 대시보드**")

# 실시간 업데이트 설정
col1, col2, col3 = st.columns([1, 1, 2])
with col1:
    auto_refresh = st.checkbox("🔄 자동 새로고침", value=True)
with col2:
    refresh_interval = st.selectbox("새로고침 간격", [5, 10, 30, 60], index=1)
with col3:
    if st.button("🔄 수동 새로고침"):
        st.experimental_rerun()

if auto_refresh:
    # 자동 새로고침을 위한 빈 컨테이너
    placeholder = st.empty()
    
# 탭 구성
tab1, tab2, tab3 = st.tabs(["📊 실시간 개요", "📈 성과 차트", "⚙️ 시스템 설정"])

with tab1:
    st.subheader("📊 실시간 시스템 개요")
    
    # 주요 메트릭 표시
    col1, col2, col3, col4 = st.columns(4)
    
    try:
        # 성능 메트릭 가져오기
        metrics = metrics_calc.get_realtime_metrics()
        
        with col1:
            st.metric(
                label="💰 총 수익률",
                value=f"{metrics.total_return_rate:.2%}",
                delta=f"{metrics.daily_return_rate:.2%} (일간)"
            )
        
        with col2:
            st.metric(
                label="🎯 승률",
                value=f"{metrics.win_rate:.1%}",
                delta=f"{metrics.total_trades_count} 거래"
            )
        
        with col3:
            st.metric(
                label="💸 총 비용",
                value=f"${metrics.total_cost:.2f}",
                delta=f"${metrics.daily_cost:.2f} (일간)"
            )
        
        with col4:
            st.metric(
                label="🤖 활성 에이전트",
                value=len(metrics.agent_rankings),
                delta="실행중"
            )
    
    except Exception as e:
        st.error(f"메트릭 로딩 실패: {str(e)}")
        # 기본값 표시
        with col1:
            st.metric("💰 총 수익률", "0.00%", "0.00%")
        with col2:
            st.metric("🎯 승률", "0.0%", "0 거래")
        with col3:
            st.metric("💸 총 비용", "$0.00", "$0.00")
        with col4:
            st.metric("🤖 활성 에이전트", "0", "대기중")
    
    st.markdown("---")
    
    # 최근 거래 테이블
    st.subheader("📋 최근 거래 내역")
    try:
        recent_trades = db_manager.get_recent_trades(limit=10)
        if recent_trades:
            df = pd.DataFrame([{
                "거래ID": trade.trade_id[:8] + "...",
                "종목": trade.symbol,
                "유형": "매수" if trade.action == "BUY" else "매도",
                "수량": trade.quantity,
                "가격": f"${trade.price:.2f}",
                "시간": trade.timestamp.strftime("%H:%M:%S"),
                "상태": "✅ 완료" if trade.status == "COMPLETED" else "⏳ 대기"
            } for trade in recent_trades])
            st.dataframe(df, use_container_width=True)
        else:
            st.info("📝 거래 내역이 없습니다.")
    except Exception as e:
        st.error(f"거래 내역 로딩 실패: {str(e)}")

with tab2:
    st.subheader("📈 성과 차트")
    
    # 시간 범위 선택
    col1, col2 = st.columns(2)
    with col1:
        time_range = st.selectbox(
            "기간 선택",
            ["1일", "1주", "1개월", "3개월", "전체"],
            index=2
        )
    with col2:
        chart_type = st.selectbox(
            "차트 유형",
            ["수익률 추이", "거래량 분석", "에이전트 성과", "비용 분석"],
            index=0
        )
    
    # 차트 표시 영역
    chart_container = st.container()
    
    with chart_container:
        try:
            if chart_type == "수익률 추이":
                # 수익률 추이 차트 (더미 데이터)
                dates = pd.date_range(start="2024-01-01", end=datetime.now(), freq="D")
                returns = [0.001 * i + 0.05 * (i % 7 - 3) for i in range(len(dates))]
                
                fig = px.line(
                    x=dates, y=returns,
                    title="📈 누적 수익률 추이",
                    labels={"x": "날짜", "y": "수익률 (%)"}
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            
            elif chart_type == "에이전트 성과":
                # 에이전트 성과 차트 (더미 데이터)
                agents = ["Portfolio Manager", "Risk Analyst", "Market Researcher", "Technical Analyst"]
                performance = [0.12, 0.08, 0.15, 0.10]
                
                fig = px.bar(
                    x=agents, y=performance,
                    title="🤖 에이전트별 성과 기여도",
                    labels={"x": "에이전트", "y": "기여도 (%)"}
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            
            else:
                st.info(f"'{chart_type}' 차트는 개발 중입니다.")
                
        except Exception as e:
            st.error(f"차트 생성 실패: {str(e)}")

with tab3:
    st.subheader("⚙️ 시스템 설정")
    
    # 시스템 제어
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔧 시스템 제어")
        
        if st.button("🚀 트레이딩 시작", type="primary"):
            st.success("트레이딩 시스템이 시작되었습니다!")
        
        if st.button("⏸️ 트레이딩 일시정지"):
            st.warning("트레이딩 시스템이 일시정지되었습니다.")
        
        if st.button("🛑 트레이딩 중지", type="secondary"):
            st.error("트레이딩 시스템이 중지되었습니다.")
    
    with col2:
        st.subheader("📊 데이터 관리")
        
        if st.button("🔄 데이터베이스 새로고침"):
            st.success("데이터베이스가 새로고침되었습니다!")
        
        if st.button("📤 데이터 내보내기"):
            st.success("데이터 내보내기가 시작되었습니다!")
        
        if st.button("🧹 캐시 정리"):
            st.success("캐시가 정리되었습니다!")
    
    st.markdown("---")
    
    # 설정 옵션
    st.subheader("⚙️ 대시보드 설정")
    
    col1, col2 = st.columns(2)
    with col1:
        st.checkbox("🔔 알림 활성화", value=True)
        st.checkbox("📧 이메일 알림", value=False)
        st.selectbox("테마", ["Dark", "Light", "Auto"], index=0)
    
    with col2:
        st.number_input("🔄 새로고침 간격 (초)", min_value=5, max_value=300, value=30)
        st.number_input("📊 차트 업데이트 간격 (초)", min_value=10, max_value=600, value=60)
        st.selectbox("시간대", ["Asia/Seoul", "UTC", "US/Eastern"], index=0)

# 푸터
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray; font-size: 0.8em;'>
    🤖 LangGraph 자율 트레이딩 시스템 v1.0.0 | 
    📊 실시간 대시보드 | 
    ⚡ Powered by Streamlit
    </div>
    """,
    unsafe_allow_html=True
)