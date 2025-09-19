#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
비용 분석 페이지

LangGraph 자율 트레이딩 시스템의 운영 비용 분석 및 수익성 평가
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
    calculate_percentage_change
)
from src.streamlit_dashboard.utils.chart_helpers import (
    create_cost_analysis_chart, create_line_chart, create_pie_chart,
    create_bar_chart, COLOR_PALETTE, TRADING_COLORS
)
from src.streamlit_dashboard.components.metrics_cards import (
    FinancialMetricCard, PercentageMetricCard, CountMetricCard,
    create_cost_cards
)

try:
    from src.database.schema import db_manager
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False

# 페이지 설정
st.set_page_config(
    page_title="비용 분석",
    page_icon="💰",
    layout="wide"
)

add_custom_css()

# 페이지 제목
st.title("💰 비용 분석 및 수익성 평가")
st.markdown("**트레이딩 시스템의 모든 운영 비용을 추적하고 ROI를 분석합니다**")

# 필터 및 제어
col1, col2, col3, col4 = st.columns(4)

with col1:
    time_range = st.selectbox(
        "📅 분석 기간",
        ["1일", "1주", "1개월", "3개월", "6개월", "1년"],
        index=2,
        key="cost_time_range"
    )

with col2:
    cost_category = st.multiselect(
        "📊 비용 카테고리",
        ["LLM API", "거래 수수료", "데이터 피드", "서버 인프라", "기타"],
        default=["LLM API", "거래 수수료", "데이터 피드"],
        key="cost_category"
    )

with col3:
    view_mode = st.selectbox(
        "👁️ 표시 방식",
        ["절대값", "비율", "누적", "일평균"],
        index=0,
        key="cost_view_mode"
    )

with col4:
    if st.button("🔄 데이터 새로고침", key="cost_refresh"):
        st.cache_data.clear()
        st.rerun()

st.markdown("---")

# 비용 데이터 생성
@cached_function(ttl=60)
def get_cost_analysis_data():
    """비용 분석 데이터 생성"""
    
    # 카테고리별 비용 구조
    cost_categories = {
        'LLM API': {
            'daily_cost': 45.30,
            'monthly_cost': 1359.0,
            'breakdown': {
                'GPT-4': 125.75,
                'Claude-3': 89.30,
                'GPT-3.5': 45.80,
                'Gemini': 32.40,
                'Perplexity': 28.90
            },
            'cost_per_trade': 1.25,
            'trend': 'increasing'
        },
        '거래 수수료': {
            'daily_cost': 28.50,
            'monthly_cost': 855.0,
            'breakdown': {
                '주식 거래': 520.0,
                'ETF 거래': 180.0,
                '옵션 거래': 155.0
            },
            'cost_per_trade': 0.95,
            'trend': 'stable'
        },
        '데이터 피드': {
            'daily_cost': 12.80,
            'monthly_cost': 384.0,
            'breakdown': {
                '실시간 시세': 200.0,
                '뉴스 피드': 120.0,
                '경제 지표': 64.0
            },
            'cost_per_trade': 0.45,
            'trend': 'stable'
        },
        '서버 인프라': {
            'daily_cost': 8.70,
            'monthly_cost': 261.0,
            'breakdown': {
                'AWS EC2': 180.0,
                'Database': 50.0,
                'Storage': 31.0
            },
            'cost_per_trade': 0.30,
            'trend': 'decreasing'
        },
        '기타': {
            'daily_cost': 5.20,
            'monthly_cost': 156.0,
            'breakdown': {
                '모니터링': 80.0,
                '백업': 46.0,
                '도구/라이센스': 30.0
            },
            'cost_per_trade': 0.18,
            'trend': 'stable'
        }
    }
    
    # 30일 시계열 데이터 생성
    dates = pd.date_range(start=datetime.now() - timedelta(days=30), end=datetime.now(), freq='D')
    daily_costs = []
    
    for date in dates:
        day_data = {'date': date}
        total_daily = 0
        
        for category, data in cost_categories.items():
            # 트렌드에 따른 변동
            base_cost = data['daily_cost']
            if data['trend'] == 'increasing':
                daily_cost = base_cost * (1 + np.random.uniform(0.02, 0.08))
            elif data['trend'] == 'decreasing':
                daily_cost = base_cost * (1 - np.random.uniform(0.01, 0.05))
            else:  # stable
                daily_cost = base_cost * (1 + np.random.uniform(-0.02, 0.02))
            
            day_data[category] = daily_cost
            total_daily += daily_cost
        
        day_data['total'] = total_daily
        daily_costs.append(day_data)
    
    # ROI 및 수익성 데이터
    total_revenue = 8500.0  # 월 수익
    total_costs = sum(cat['monthly_cost'] for cat in cost_categories.values())
    net_profit = total_revenue - total_costs
    roi = (net_profit / total_costs) * 100 if total_costs > 0 else 0
    
    return {
        'categories': cost_categories,
        'daily_data': pd.DataFrame(daily_costs),
        'summary': {
            'total_monthly_cost': total_costs,
            'total_monthly_revenue': total_revenue,
            'net_profit': net_profit,
            'roi': roi,
            'break_even_trades': int(total_costs / 4.0),  # 평균 거래당 수익 가정
            'cost_efficiency': total_costs / total_revenue if total_revenue > 0 else 0
        }
    }

# 비용 요약 카드
st.subheader("💰 비용 요약")
cost_data = get_cost_analysis_data()

# 필터링된 카테고리 비용 계산
filtered_monthly_cost = 0
filtered_daily_cost = 0

if cost_category:
    for cat in cost_category:
        if cat in cost_data['categories']:
            filtered_monthly_cost += cost_data['categories'][cat]['monthly_cost']
            filtered_daily_cost += cost_data['categories'][cat]['daily_cost']
else:
    filtered_monthly_cost = cost_data['summary']['total_monthly_cost']
    filtered_daily_cost = sum(cat['daily_cost'] for cat in cost_data['categories'].values())

# 요약 메트릭
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    FinancialMetricCard(
        title="📅 월간 총 비용",
        value=filtered_monthly_cost,
        help_text="선택된 카테고리의 월간 총 비용"
    ).render()

with col2:
    FinancialMetricCard(
        title="📊 일평균 비용",
        value=filtered_daily_cost,
        help_text="일평균 운영 비용"
    ).render()

with col3:
    FinancialMetricCard(
        title="💵 월간 수익",
        value=cost_data['summary']['total_monthly_revenue'],
        help_text="트레이딩 시스템 월간 수익"
    ).render()

with col4:
    FinancialMetricCard(
        title="💎 순이익",
        value=cost_data['summary']['net_profit'],
        help_text="수익에서 비용을 뺀 순이익"
    ).render()

with col5:
    PercentageMetricCard(
        title="📈 ROI",
        value=cost_data['summary']['roi'] / 100,
        help_text="투자 대비 수익률"
    ).render()

st.markdown("---")

# 상세 비용 카드
st.subheader("📊 카테고리별 비용 분석")

if cost_category:
    filtered_categories = {k: v for k, v in cost_data['categories'].items() if k in cost_category}
else:
    filtered_categories = cost_data['categories']

# 비용 카드 데이터 준비
cost_cards_data = {}
for cat_name, cat_data in filtered_categories.items():
    cost_cards_data[f"{cat_name}_cost"] = cat_data['monthly_cost']

create_cost_cards(cost_cards_data)

st.markdown("---")

# 비용 분포 및 트렌드 차트
col1, col2 = st.columns(2)

with col1:
    st.subheader("🥧 비용 분포")
    
    # 카테고리별 비용 파이 차트
    pie_data = pd.DataFrame([
        {'category': cat, 'cost': data['monthly_cost']}
        for cat, data in filtered_categories.items()
    ])
    
    fig = create_pie_chart(
        pie_data, 'cost', 'category',
        title="", height=400
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("📈 비용 트렌드")
    
    # 시간 범위 필터 적용
    start_date, end_date = get_time_range_filter(time_range)
    filtered_daily_data = cost_data['daily_data'][
        (cost_data['daily_data']['date'] >= start_date) & 
        (cost_data['daily_data']['date'] <= end_date)
    ]
    
    # 누적 또는 일별 차트
    if view_mode == "누적":
        # 누적 비용 계산
        cumulative_data = filtered_daily_data.copy()
        for cat in cost_category if cost_category else filtered_categories.keys():
            if cat in cumulative_data.columns:
                cumulative_data[f'{cat}_cumsum'] = cumulative_data[cat].cumsum()
        
        fig = go.Figure()
        for cat in cost_category if cost_category else filtered_categories.keys():
            if f'{cat}_cumsum' in cumulative_data.columns:
                fig.add_trace(go.Scatter(
                    x=cumulative_data['date'],
                    y=cumulative_data[f'{cat}_cumsum'],
                    mode='lines',
                    name=cat,
                    stackgroup='one'
                ))
        
        fig.update_layout(
            title="누적 비용 추이",
            xaxis_title="날짜",
            yaxis_title="누적 비용 ($)",
            height=400
        )
    else:
        # 일별 비용 스택 차트
        fig = go.Figure()
        for cat in cost_category if cost_category else filtered_categories.keys():
            if cat in filtered_daily_data.columns:
                fig.add_trace(go.Scatter(
                    x=filtered_daily_data['date'],
                    y=filtered_daily_data[cat],
                    mode='lines+markers',
                    name=cat,
                    stackgroup='one' if view_mode == "절대값" else None
                ))
        
        fig.update_layout(
            title="일별 비용 추이",
            xaxis_title="날짜",
            yaxis_title="일별 비용 ($)",
            height=400
        )
    
    st.plotly_chart(fig, use_container_width=True)

# 카테고리별 세부 분석
st.markdown("---")
st.subheader("🔍 카테고리별 세부 분석")

if filtered_categories:
    selected_category = st.selectbox(
        "분석할 카테고리 선택:",
        list(filtered_categories.keys()),
        key="detailed_category_select"
    )
    
    category_detail = filtered_categories[selected_category]
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"#### 💰 {selected_category} 상세 비용")
        
        # 세부 비용 분해
        breakdown_data = pd.DataFrame([
            {'item': item, 'cost': cost}
            for item, cost in category_detail['breakdown'].items()
        ])
        
        fig = create_bar_chart(
            breakdown_data, 'item', 'cost',
            title="", x_title="항목", y_title="비용 ($)",
            height=350
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # 세부 항목 테이블
        breakdown_display = breakdown_data.copy()
        breakdown_display['비용'] = breakdown_display['cost'].apply(lambda x: format_currency(x))
        breakdown_display['비율'] = (breakdown_display['cost'] / breakdown_display['cost'].sum() * 100).apply(lambda x: f"{x:.1f}%")
        
        st.dataframe(
            breakdown_display[['item', '비용', '비율']].rename(columns={'item': '항목'}),
            use_container_width=True,
            hide_index=True
        )
    
    with col2:
        st.markdown(f"#### 📊 {selected_category} 성과 지표")
        
        # 카테고리별 KPI
        col_a, col_b = st.columns(2)
        
        with col_a:
            FinancialMetricCard(
                title="월간 비용",
                value=category_detail['monthly_cost']
            ).render()
            
            FinancialMetricCard(
                title="일평균 비용",
                value=category_detail['daily_cost']
            ).render()
        
        with col_b:
            FinancialMetricCard(
                title="거래당 비용",
                value=category_detail['cost_per_trade']
            ).render()
            
            # 트렌드 표시
            trend_emoji = {
                'increasing': '📈 증가',
                'decreasing': '📉 감소',
                'stable': '📊 안정'
            }
            st.metric(
                "비용 트렌드",
                trend_emoji.get(category_detail['trend'], '❓ 불명')
            )
        
        # 효율성 분석
        st.markdown("##### 📈 효율성 지표")
        
        # 해당 카테고리의 30일 데이터
        category_history = cost_data['daily_data'][selected_category].tolist()
        efficiency_score = (1 / np.std(category_history)) * 100  # 변동성 역수
        
        st.metric(
            "비용 안정성 점수",
            f"{efficiency_score:.1f}/100",
            help="높을수록 비용이 안정적 (변동성이 낮음)"
        )

# 수익성 분석
st.markdown("---")
st.subheader("💎 수익성 및 ROI 분석")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("#### 📊 손익분기점 분석")
    
    break_even_trades = cost_data['summary']['break_even_trades']
    current_monthly_trades = 850  # 더미 데이터
    
    # 손익분기점 차트
    trades_data = pd.DataFrame({
        'trades': list(range(0, 1200, 50)),
        'revenue': [t * 4.0 for t in range(0, 1200, 50)],  # 거래당 $4 수익 가정
        'cost': [cost_data['summary']['total_monthly_cost']] * 24
    })
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=trades_data['trades'],
        y=trades_data['revenue'],
        mode='lines',
        name='수익',
        line=dict(color=TRADING_COLORS['profit'])
    ))
    fig.add_trace(go.Scatter(
        x=trades_data['trades'],
        y=trades_data['cost'],
        mode='lines',
        name='비용',
        line=dict(color=TRADING_COLORS['loss'], dash='dash')
    ))
    
    # 손익분기점 표시
    fig.add_vline(
        x=break_even_trades,
        line_dash="dot",
        line_color="orange",
        annotation_text=f"손익분기점: {break_even_trades}거래"
    )
    
    fig.update_layout(
        title="손익분기점 분석",
        xaxis_title="월간 거래 수",
        yaxis_title="금액 ($)",
        height=350
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("#### 💰 수익성 지표")
    
    # 주요 수익성 지표
    profit_margin = (cost_data['summary']['net_profit'] / cost_data['summary']['total_monthly_revenue']) * 100
    cost_ratio = cost_data['summary']['cost_efficiency'] * 100
    
    st.metric(
        "이익률",
        f"{profit_margin:.1f}%",
        help="수익 대비 순이익 비율"
    )
    
    st.metric(
        "비용 비율",
        f"{cost_ratio:.1f}%",
        help="수익 대비 비용 비율"
    )
    
    st.metric(
        "투자회수기간",
        "2.3개월",
        help="초기 투자금 회수 예상 기간"
    )
    
    # ROI 게이지 차트
    roi_value = cost_data['summary']['roi']
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=roi_value,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "ROI (%)"},
        gauge={
            'axis': {'range': [None, 200]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 50], 'color': "lightgray"},
                {'range': [50, 100], 'color': "yellow"},
                {'range': [100, 200], 'color': "green"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 150
            }
        }
    ))
    fig.update_layout(height=300)
    st.plotly_chart(fig, use_container_width=True)

with col3:
    st.markdown("#### 📈 비용 최적화 제안")
    
    # 비용 최적화 분석
    optimization_suggestions = [
        {
            'category': 'LLM API',
            'potential_saving': 250.0,
            'suggestion': 'GPT-3.5 사용 비율 증가',
            'impact': 'medium'
        },
        {
            'category': '거래 수수료',
            'potential_saving': 120.0,
            'suggestion': '대량 거래 할인 활용',
            'impact': 'low'
        },
        {
            'category': '서버 인프라',
            'potential_saving': 80.0,
            'suggestion': 'Reserved Instance 활용',
            'impact': 'low'
        }
    ]
    
    for suggestion in optimization_suggestions:
        with st.expander(f"💡 {suggestion['category']} 최적화"):
            col_a, col_b = st.columns([2, 1])
            
            with col_a:
                st.write(f"**제안**: {suggestion['suggestion']}")
                st.write(f"**예상 절감**: {format_currency(suggestion['potential_saving'])}/월")
            
            with col_b:
                impact_color = {
                    'high': '🔴',
                    'medium': '🟡',
                    'low': '🟢'
                }
                st.write(f"**영향도**: {impact_color.get(suggestion['impact'], '❓')}")
    
    total_potential_saving = sum(s['potential_saving'] for s in optimization_suggestions)
    st.success(f"💰 총 절감 가능: {format_currency(total_potential_saving)}/월")

# 비용 알림 및 예산 관리
st.markdown("---")
st.subheader("🚨 예산 관리 및 알림")

col1, col2 = st.columns(2)

with col1:
    st.markdown("#### 💸 예산 설정")
    
    monthly_budget = st.number_input(
        "월간 예산 한도 ($)",
        min_value=0.0,
        value=4000.0,
        step=100.0,
        key="monthly_budget"
    )
    
    daily_budget = monthly_budget / 30
    current_monthly_cost = cost_data['summary']['total_monthly_cost']
    budget_usage = (current_monthly_cost / monthly_budget) * 100 if monthly_budget > 0 else 0
    
    # 예산 사용률 표시
    if budget_usage > 100:
        st.error(f"⚠️ 예산 초과: {budget_usage:.1f}% ({format_currency(current_monthly_cost - monthly_budget)} 초과)")
    elif budget_usage > 80:
        st.warning(f"⚠️ 예산 근접: {budget_usage:.1f}% 사용")
    else:
        st.success(f"✅ 예산 내: {budget_usage:.1f}% 사용")
    
    # 예산 진행률 차트
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=budget_usage,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "예산 사용률 (%)"},
        gauge={
            'axis': {'range': [None, 120]},
            'bar': {'color': "blue"},
            'steps': [
                {'range': [0, 60], 'color': "lightgreen"},
                {'range': [60, 80], 'color': "yellow"},
                {'range': [80, 100], 'color': "orange"},
                {'range': [100, 120], 'color': "red"}
            ]
        }
    ))
    fig.update_layout(height=250)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("#### 🔔 알림 설정")
    
    cost_alert_threshold = st.slider(
        "일일 비용 알림 임계값 (%)",
        min_value=50,
        max_value=150,
        value=90,
        step=5
    )
    
    email_alerts = st.checkbox("📧 이메일 알림 활성화", value=True)
    slack_alerts = st.checkbox("📱 Slack 알림 활성화", value=False)
    
    if st.button("💾 알림 설정 저장"):
        st.success("알림 설정이 저장되었습니다!")
    
    # 현재 알림 상태
    st.markdown("##### 🚨 현재 알림")
    
    current_daily_cost = filtered_daily_cost
    daily_threshold = (daily_budget * cost_alert_threshold / 100)
    
    if current_daily_cost > daily_threshold:
        st.error(f"⚠️ 일일 비용 임계값 초과: {format_currency(current_daily_cost)} > {format_currency(daily_threshold)}")
    else:
        st.success(f"✅ 일일 비용 정상: {format_currency(current_daily_cost)}")

# 푸터
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray; font-size: 0.8em;'>
    💰 비용 분석 및 수익성 모니터링 | 마지막 업데이트: {timestamp} | ROI 추적
    </div>
    """.format(timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
    unsafe_allow_html=True
)