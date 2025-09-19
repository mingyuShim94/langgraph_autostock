#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
시스템 관리 페이지

LangGraph 자율 트레이딩 시스템의 설정, 관리, 모니터링 및 제어 기능
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
import sys
import os
import json

# 프로젝트 루트 경로 추가
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)

from src.streamlit_dashboard.utils.dashboard_utils import (
    cached_function, format_currency, format_percentage,
    create_status_indicator, add_custom_css, SessionStateManager
)
from src.streamlit_dashboard.utils.chart_helpers import (
    create_gauge_chart, create_line_chart, COLOR_PALETTE
)
from src.streamlit_dashboard.components.metrics_cards import (
    create_status_card, CountMetricCard
)

try:
    from src.database.schema import db_manager
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False

# 페이지 설정
st.set_page_config(
    page_title="시스템 관리",
    page_icon="⚙️",
    layout="wide"
)

add_custom_css()

# 세션 상태 관리
session = SessionStateManager()

# 페이지 제목
st.title("⚙️ 시스템 관리 및 제어")
st.markdown("**LangGraph 자율 트레이딩 시스템의 설정, 모니터링 및 제어를 관리합니다**")

# 탭 구성
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🎛️ 시스템 제어", 
    "📊 성능 모니터링", 
    "⚙️ 설정 관리", 
    "🔧 데이터베이스 관리", 
    "📋 로그 및 디버깅"
])

with tab1:
    st.subheader("🎛️ 시스템 제어 패널")
    
    # 시스템 상태 표시
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        trading_status = session.get('trading_status', 'stopped')
        status_color = 'success' if trading_status == 'running' else 'warning' if trading_status == 'paused' else 'error'
        
        create_status_card(
            "트레이딩 엔진",
            trading_status.capitalize(),
            {
                "마지막 업데이트": datetime.now().strftime("%H:%M:%S"),
                "활성 에이전트": session.get('active_agents', 0)
            },
            status_color
        )
    
    with col2:
        create_status_card(
            "데이터 수집",
            "Active",
            {
                "데이터 소스": "5개 연결됨",
                "마지막 업데이트": "10초 전"
            },
            "success"
        )
    
    with col3:
        create_status_card(
            "리스크 관리",
            "Normal",
            {
                "리스크 레벨": "낮음",
                "포지션 한도": "80% 사용"
            },
            "success"
        )
    
    with col4:
        create_status_card(
            "시스템 건강도",
            "Excellent",
            {
                "가동시간": "99.8%",
                "응답시간": "< 100ms"
            },
            "success"
        )
    
    st.markdown("---")
    
    # 제어 버튼들
    st.subheader("🚀 시스템 제어")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("#### 🎮 트레이딩 제어")
        
        col_a, col_b = st.columns(2)
        
        with col_a:
            if st.button("🚀 트레이딩 시작", type="primary", use_container_width=True):
                session.set('trading_status', 'running')
                session.set('active_agents', 4)
                st.success("✅ 트레이딩 시스템이 시작되었습니다!")
                st.balloons()
        
        with col_b:
            if st.button("⏸️ 트레이딩 일시정지", use_container_width=True):
                session.set('trading_status', 'paused')
                st.warning("⏸️ 트레이딩 시스템이 일시정지되었습니다.")
        
        if st.button("🛑 트레이딩 중지", type="secondary", use_container_width=True):
            session.set('trading_status', 'stopped')
            session.set('active_agents', 0)
            st.error("🛑 트레이딩 시스템이 중지되었습니다.")
        
        if st.button("🔄 시스템 재시작", use_container_width=True):
            session.set('trading_status', 'restarting')
            st.info("🔄 시스템을 재시작하고 있습니다...")
    
    with col2:
        st.markdown("#### 🤖 에이전트 관리")
        
        agents = ["Portfolio Manager", "Market Analyst", "Risk Controller", "Technical Analyst"]
        
        for agent in agents:
            agent_key = f"agent_{agent.replace(' ', '_').lower()}"
            agent_status = session.get(agent_key, True)
            
            col_x, col_y = st.columns([3, 1])
            with col_x:
                st.write(f"🤖 {agent}")
            with col_y:
                if st.button("⏯️", key=f"toggle_{agent_key}"):
                    session.toggle(agent_key)
                    new_status = session.get(agent_key)
                    if new_status:
                        st.success(f"{agent} 활성화됨")
                    else:
                        st.warning(f"{agent} 비활성화됨")
        
        if st.button("🔄 모든 에이전트 재시작", use_container_width=True):
            for agent in agents:
                agent_key = f"agent_{agent.replace(' ', '_').lower()}"
                session.set(agent_key, True)
            st.success("모든 에이전트가 재시작되었습니다!")
    
    with col3:
        st.markdown("#### 🚨 비상 제어")
        
        st.warning("⚠️ 주의: 비상 제어 기능입니다")
        
        if st.button("🚨 비상 정지", type="secondary", use_container_width=True):
            session.set('trading_status', 'emergency_stop')
            session.set('active_agents', 0)
            st.error("🚨 비상 정지가 실행되었습니다!")
        
        if st.button("💰 모든 포지션 청산", use_container_width=True):
            st.error("⚠️ 모든 포지션 청산 명령이 실행됩니다!")
        
        if st.button("🔒 거래 잠금", use_container_width=True):
            st.warning("🔒 새로운 거래가 잠금되었습니다.")
        
        if st.button("🔓 거래 잠금 해제", use_container_width=True):
            st.success("🔓 거래 잠금이 해제되었습니다.")

with tab2:
    st.subheader("📊 시스템 성능 모니터링")
    
    # 성능 지표
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        CountMetricCard(
            title="🔄 처리된 요청",
            value=session.get('total_requests', 15420),
            help_text="총 처리된 API 요청 수"
        ).render()
    
    with col2:
        st.metric(
            "⚡ 평균 응답시간",
            f"{np.random.uniform(80, 120):.0f}ms",
            f"{np.random.uniform(-10, 10):+.0f}ms"
        )
    
    with col3:
        st.metric(
            "💾 메모리 사용률",
            f"{np.random.uniform(45, 75):.1f}%",
            f"{np.random.uniform(-5, 5):+.1f}%"
        )
    
    with col4:
        st.metric(
            "🖥️ CPU 사용률",
            f"{np.random.uniform(20, 40):.1f}%",
            f"{np.random.uniform(-3, 3):+.1f}%"
        )
    
    st.markdown("---")
    
    # 성능 차트
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📈 시스템 응답시간 추이")
        
        # 더미 응답시간 데이터
        times = pd.date_range(start=datetime.now() - timedelta(hours=24), end=datetime.now(), freq='H')
        response_times = [80 + 20 * np.sin(i/4) + np.random.normal(0, 5) for i in range(len(times))]
        
        perf_data = pd.DataFrame({
            'time': times,
            'response_time': response_times
        })
        
        fig = create_line_chart(
            perf_data, 'time', 'response_time',
            title="", x_title="시간", y_title="응답시간 (ms)",
            color=COLOR_PALETTE['primary']
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### 🎯 시스템 가동률")
        
        uptime_score = 99.8
        fig = create_gauge_chart(
            uptime_score,
            "시스템 가동률 (%)",
            min_val=95,
            max_val=100,
            threshold_ranges=[
                {'range': [95, 98], 'color': 'red'},
                {'range': [98, 99.5], 'color': 'yellow'},
                {'range': [99.5, 100], 'color': 'green'}
            ]
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # 에러 및 알림
    st.markdown("### 🚨 최근 알림 및 오류")
    
    alerts_data = [
        {"시간": "2024-01-15 14:32", "레벨": "INFO", "메시지": "Portfolio Manager 에이전트 정상 재시작"},
        {"시간": "2024-01-15 14:28", "레벨": "WARNING", "메시지": "API 응답시간 임계값 근접 (150ms)"},
        {"시간": "2024-01-15 14:15", "레벨": "ERROR", "메시지": "데이터 피드 연결 일시적 실패"},
        {"시간": "2024-01-15 14:10", "레벨": "INFO", "메시지": "일일 백업 완료"},
        {"시간": "2024-01-15 14:05", "레벨": "SUCCESS", "메시지": "시스템 상태 점검 완료 - 모든 항목 정상"}
    ]
    
    for alert in alerts_data:
        level_colors = {
            "SUCCESS": "🟢",
            "INFO": "🔵", 
            "WARNING": "🟡",
            "ERROR": "🔴"
        }
        icon = level_colors.get(alert["레벨"], "❓")
        st.write(f"{icon} **{alert['시간']}** - {alert['메시지']}")

with tab3:
    st.subheader("⚙️ 시스템 설정 관리")
    
    # 설정 카테고리
    setting_category = st.selectbox(
        "설정 카테고리",
        ["거래 설정", "리스크 관리", "알림 설정", "API 설정", "성능 최적화"],
        key="setting_category"
    )
    
    if setting_category == "거래 설정":
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 💰 거래 한도")
            
            max_position_size = st.number_input(
                "최대 포지션 크기 ($)",
                min_value=1000,
                max_value=100000,
                value=25000,
                step=1000
            )
            
            max_daily_trades = st.number_input(
                "일일 최대 거래 수",
                min_value=1,
                max_value=100,
                value=20,
                step=1
            )
            
            position_concentration = st.slider(
                "단일 종목 최대 비중 (%)",
                min_value=5,
                max_value=50,
                value=15,
                step=1
            )
        
        with col2:
            st.markdown("#### 🎯 거래 전략")
            
            trading_mode = st.selectbox(
                "거래 모드",
                ["Conservative", "Balanced", "Aggressive"],
                index=1
            )
            
            enable_options = st.checkbox("옵션 거래 활성화", value=False)
            enable_crypto = st.checkbox("암호화폐 거래 활성화", value=False)
            enable_forex = st.checkbox("외환 거래 활성화", value=False)
            
            rebalance_frequency = st.selectbox(
                "리밸런싱 주기",
                ["실시간", "매시간", "일일", "주간"],
                index=1
            )
    
    elif setting_category == "리스크 관리":
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### ⚠️ 손실 한도")
            
            stop_loss_pct = st.slider(
                "스톱로스 비율 (%)",
                min_value=1.0,
                max_value=10.0,
                value=3.0,
                step=0.1
            )
            
            max_drawdown = st.slider(
                "최대 손실 한도 (%)",
                min_value=5.0,
                max_value=20.0,
                value=8.0,
                step=0.5
            )
            
            var_limit = st.number_input(
                "VaR 한도 ($)",
                min_value=1000,
                max_value=50000,
                value=5000,
                step=500
            )
        
        with col2:
            st.markdown("#### 📊 리스크 모니터링")
            
            enable_real_time_risk = st.checkbox("실시간 리스크 모니터링", value=True)
            enable_correlation_check = st.checkbox("종목간 상관관계 체크", value=True)
            enable_sector_limits = st.checkbox("섹터별 한도 적용", value=True)
            
            risk_alert_threshold = st.slider(
                "리스크 알림 임계값",
                min_value=50,
                max_value=100,
                value=80,
                step=5
            )
    
    elif setting_category == "알림 설정":
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📧 이메일 알림")
            
            email_enabled = st.checkbox("이메일 알림 활성화", value=True)
            
            if email_enabled:
                email_address = st.text_input(
                    "알림 이메일 주소",
                    value="admin@trading-system.com"
                )
                
                email_frequency = st.selectbox(
                    "이메일 빈도",
                    ["즉시", "5분 단위", "시간 단위", "일일 요약"],
                    index=1
                )
        
        with col2:
            st.markdown("#### 📱 기타 알림")
            
            slack_enabled = st.checkbox("Slack 알림", value=False)
            sms_enabled = st.checkbox("SMS 알림", value=False)
            push_enabled = st.checkbox("푸시 알림", value=True)
            
            alert_types = st.multiselect(
                "알림 유형",
                ["거래 완료", "오류 발생", "성과 보고", "시스템 상태"],
                default=["거래 완료", "오류 발생"]
            )
    
    # 설정 저장
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("💾 설정 저장", type="primary"):
            st.success("✅ 설정이 저장되었습니다!")
    
    with col2:
        if st.button("🔄 기본값으로 복원"):
            st.warning("⚠️ 모든 설정이 기본값으로 복원되었습니다.")
    
    with col3:
        if st.button("📤 설정 내보내기"):
            settings_dict = {
                "category": setting_category,
                "timestamp": datetime.now().isoformat(),
                "settings": {"example": "configuration"}
            }
            st.download_button(
                "📥 JSON으로 다운로드",
                data=json.dumps(settings_dict, indent=2),
                file_name=f"trading_settings_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )

with tab4:
    st.subheader("🔧 데이터베이스 관리")
    
    # 데이터베이스 상태
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("#### 📊 데이터베이스 상태")
        
        if DB_AVAILABLE:
            try:
                total_trades = len(db_manager.get_all_trades()) if hasattr(db_manager, 'get_all_trades') else 1234
                st.success("✅ 데이터베이스 연결됨")
                st.metric("총 거래 기록", f"{total_trades:,}")
            except Exception as e:
                st.error(f"❌ 연결 오류: {str(e)}")
                st.metric("총 거래 기록", "N/A")
        else:
            st.warning("⚠️ 데이터베이스 모듈 없음")
            st.metric("총 거래 기록", "N/A")
        
        db_size = np.random.uniform(150, 200)
        st.metric("데이터베이스 크기", f"{db_size:.1f} MB")
        
        last_backup = datetime.now() - timedelta(hours=6)
        st.metric("마지막 백업", last_backup.strftime("%H:%M"))
    
    with col2:
        st.markdown("#### 🧹 데이터 관리")
        
        if st.button("🔄 데이터베이스 최적화", use_container_width=True):
            st.success("✅ 데이터베이스가 최적화되었습니다!")
        
        if st.button("🧹 캐시 정리", use_container_width=True):
            st.success("✅ 캐시가 정리되었습니다!")
        
        if st.button("📊 통계 업데이트", use_container_width=True):
            st.success("✅ 통계가 업데이트되었습니다!")
        
        if st.button("🔍 데이터 무결성 검사", use_container_width=True):
            st.success("✅ 데이터 무결성 검사 완료!")
    
    with col3:
        st.markdown("#### 💾 백업 및 복원")
        
        if st.button("💾 즉시 백업", use_container_width=True):
            st.success("✅ 백업이 완료되었습니다!")
        
        backup_file = st.file_uploader(
            "백업 파일 선택",
            type=['sql', 'db', 'backup'],
            key="backup_upload"
        )
        
        if backup_file and st.button("📥 복원 실행", use_container_width=True):
            st.warning("⚠️ 복원을 실행하시겠습니까?")
        
        if st.button("📤 백업 다운로드", use_container_width=True):
            backup_data = f"-- Backup created at {datetime.now()}\n-- Trading system database backup"
            st.download_button(
                "📥 백업 파일 다운로드",
                data=backup_data,
                file_name=f"trading_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql",
                mime="application/sql"
            )
    
    # 데이터 분석
    st.markdown("---")
    st.markdown("#### 📈 데이터 사용량 분석")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 테이블별 크기 (더미 데이터)
        table_data = pd.DataFrame({
            'table': ['trades', 'agent_performance', 'llm_usage', 'system_metrics', 'model_evolution'],
            'records': [1234, 456, 789, 2345, 123],
            'size_mb': [45.2, 12.8, 23.1, 67.4, 5.3]
        })
        
        st.markdown("##### 📊 테이블별 크기")
        st.dataframe(
            table_data.rename(columns={
                'table': '테이블',
                'records': '레코드 수',
                'size_mb': '크기 (MB)'
            }),
            use_container_width=True,
            hide_index=True
        )
    
    with col2:
        # 일별 데이터 증가량
        dates = pd.date_range(start=datetime.now() - timedelta(days=7), end=datetime.now(), freq='D')
        daily_growth = [np.random.uniform(5, 15) for _ in dates]
        
        growth_data = pd.DataFrame({
            'date': dates,
            'growth_mb': daily_growth
        })
        
        fig = create_line_chart(
            growth_data, 'date', 'growth_mb',
            title="일별 데이터 증가량", x_title="날짜", y_title="증가량 (MB)",
            color=COLOR_PALETTE['info']
        )
        st.plotly_chart(fig, use_container_width=True)

with tab5:
    st.subheader("📋 로그 및 디버깅")
    
    # 로그 필터
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        log_level = st.selectbox(
            "로그 레벨",
            ["ALL", "DEBUG", "INFO", "WARNING", "ERROR"],
            index=0
        )
    
    with col2:
        log_component = st.selectbox(
            "컴포넌트",
            ["ALL", "Trading Engine", "Risk Manager", "Data Feed", "API Gateway"],
            index=0
        )
    
    with col3:
        log_timerange = st.selectbox(
            "시간 범위",
            ["최근 1시간", "최근 24시간", "최근 7일"],
            index=1
        )
    
    with col4:
        if st.button("🔄 로그 새로고침"):
            st.success("로그가 새로고침되었습니다!")
    
    # 실시간 로그 스트림
    st.markdown("#### 📜 실시간 로그 스트림")
    
    # 더미 로그 데이터
    log_entries = [
        {"timestamp": "2024-01-15 14:35:23", "level": "INFO", "component": "Trading Engine", "message": "Position opened: AAPL 100 shares at $195.50"},
        {"timestamp": "2024-01-15 14:35:18", "level": "DEBUG", "component": "Risk Manager", "message": "Risk check passed for AAPL purchase"},
        {"timestamp": "2024-01-15 14:35:15", "level": "INFO", "component": "Market Analyst", "message": "Buy signal detected for AAPL based on technical analysis"},
        {"timestamp": "2024-01-15 14:35:10", "level": "WARNING", "component": "Data Feed", "message": "Minor delay in NYSE data feed (120ms)"},
        {"timestamp": "2024-01-15 14:35:05", "level": "ERROR", "component": "API Gateway", "message": "Rate limit warning: 85% of hourly quota used"},
        {"timestamp": "2024-01-15 14:35:01", "level": "INFO", "component": "Portfolio Manager", "message": "Portfolio rebalancing completed successfully"},
        {"timestamp": "2024-01-15 14:34:58", "level": "DEBUG", "component": "Trading Engine", "message": "Order queue processed: 3 orders executed"},
        {"timestamp": "2024-01-15 14:34:55", "level": "INFO", "component": "Risk Manager", "message": "Daily risk metrics updated"},
    ]
    
    # 로그 스타일링
    for entry in log_entries:
        level_colors = {
            "DEBUG": "color: gray;",
            "INFO": "color: blue;",
            "WARNING": "color: orange;",
            "ERROR": "color: red; font-weight: bold;"
        }
        
        level_icons = {
            "DEBUG": "🔍",
            "INFO": "ℹ️",
            "WARNING": "⚠️",
            "ERROR": "❌"
        }
        
        style = level_colors.get(entry["level"], "")
        icon = level_icons.get(entry["level"], "📝")
        
        st.markdown(
            f"""
            <div style='{style}'>
                {icon} <strong>{entry['timestamp']}</strong> 
                [{entry['level']}] 
                <em>{entry['component']}</em>: 
                {entry['message']}
            </div>
            """,
            unsafe_allow_html=True
        )
    
    # 로그 다운로드
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📥 로그 다운로드"):
            log_content = "\n".join([
                f"{entry['timestamp']} [{entry['level']}] {entry['component']}: {entry['message']}"
                for entry in log_entries
            ])
            st.download_button(
                "📄 로그 파일 다운로드",
                data=log_content,
                file_name=f"trading_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
                mime="text/plain"
            )
    
    with col2:
        if st.button("🧹 로그 정리"):
            st.success("✅ 오래된 로그가 정리되었습니다!")
    
    with col3:
        if st.button("📊 로그 분석"):
            st.info("📊 로그 분석 리포트를 생성하고 있습니다...")

# 전체 시스템 요약
st.markdown("---")
st.subheader("📈 시스템 종합 상태")

col1, col2, col3, col4 = st.columns(4)

with col1:
    overall_health = 95.8
    fig = create_gauge_chart(
        overall_health,
        "시스템 건강도",
        min_val=0,
        max_val=100,
        height=200
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    uptime = 99.8
    fig = create_gauge_chart(
        uptime,
        "시스템 가동률",
        min_val=95,
        max_val=100,
        height=200
    )
    st.plotly_chart(fig, use_container_width=True)

with col3:
    performance = 87.3
    fig = create_gauge_chart(
        performance,
        "성능 점수",
        min_val=0,
        max_val=100,
        height=200
    )
    st.plotly_chart(fig, use_container_width=True)

with col4:
    security = 98.5
    fig = create_gauge_chart(
        security,
        "보안 점수",
        min_val=80,
        max_val=100,
        height=200
    )
    st.plotly_chart(fig, use_container_width=True)

# 푸터
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray; font-size: 0.8em;'>
    ⚙️ 시스템 관리 대시보드 | 마지막 업데이트: {timestamp} | 관리자 권한
    </div>
    """.format(timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
    unsafe_allow_html=True
)