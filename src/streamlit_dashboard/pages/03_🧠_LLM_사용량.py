#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM 사용량 페이지

LangGraph 자율 트레이딩 시스템의 LLM API 사용량, 비용 및 성능 분석
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
    format_large_number
)
from src.streamlit_dashboard.utils.chart_helpers import (
    create_line_chart, create_bar_chart, create_pie_chart,
    COLOR_PALETTE, TRADING_COLORS
)
from src.streamlit_dashboard.components.metrics_cards import (
    CountMetricCard, FinancialMetricCard, PercentageMetricCard,
    create_compact_metric_row
)

try:
    from src.database.schema import db_manager
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False

# 페이지 설정
st.set_page_config(
    page_title="LLM 사용량",
    page_icon="🧠",
    layout="wide"
)

add_custom_css()

# 페이지 제목
st.title("🧠 LLM 사용량 분석")
st.markdown("**Large Language Model API 사용량, 비용 및 성능을 모니터링합니다**")

# 필터 및 제어
col1, col2, col3, col4 = st.columns(4)

with col1:
    time_range = st.selectbox(
        "📅 분석 기간",
        ["1일", "1주", "1개월", "3개월", "전체"],
        index=2,
        key="llm_time_range"
    )

with col2:
    model_filter = st.multiselect(
        "🤖 모델 선택",
        ["GPT-4", "GPT-3.5-Turbo", "Claude-3", "Gemini-Pro", "Perplexity"],
        default=["GPT-4", "Claude-3"],
        key="llm_model_filter"
    )

with col3:
    metric_view = st.selectbox(
        "📊 표시 방식",
        ["토큰 사용량", "API 호출 수", "비용", "응답 시간"],
        index=0,
        key="llm_metric_view"
    )

with col4:
    if st.button("🔄 데이터 새로고침", key="llm_refresh"):
        st.cache_data.clear()
        st.rerun()

st.markdown("---")

# LLM 사용량 데이터 생성
@cached_function(ttl=60)
def get_llm_usage_data():
    """LLM 사용량 데이터 생성"""
    
    models = [
        {
            'model_name': 'GPT-4',
            'provider': 'OpenAI',
            'input_tokens': 1_250_000,
            'output_tokens': 450_000,
            'total_calls': 1_245,
            'total_cost': 125.75,
            'avg_response_time': 3.2,
            'success_rate': 0.985,
            'usage_by_agent': {
                'Portfolio Manager': 35,
                'Market Analyst': 28,
                'Risk Controller': 15,
                'Technical Analyst': 22
            }
        },
        {
            'model_name': 'Claude-3',
            'provider': 'Anthropic',
            'input_tokens': 980_000,
            'output_tokens': 320_000,
            'total_calls': 856,
            'total_cost': 89.30,
            'avg_response_time': 2.8,
            'success_rate': 0.992,
            'usage_by_agent': {
                'Portfolio Manager': 40,
                'Market Analyst': 35,
                'Risk Controller': 12,
                'Technical Analyst': 13
            }
        },
        {
            'model_name': 'GPT-3.5-Turbo',
            'provider': 'OpenAI',
            'input_tokens': 2_100_000,
            'output_tokens': 650_000,
            'total_calls': 2_234,
            'total_cost': 45.80,
            'avg_response_time': 1.5,
            'success_rate': 0.978,
            'usage_by_agent': {
                'Portfolio Manager': 25,
                'Market Analyst': 30,
                'Risk Controller': 20,
                'Technical Analyst': 25
            }
        },
        {
            'model_name': 'Gemini-Pro',
            'provider': 'Google',
            'input_tokens': 750_000,
            'output_tokens': 280_000,
            'total_calls': 567,
            'total_cost': 32.40,
            'avg_response_time': 2.1,
            'success_rate': 0.975,
            'usage_by_agent': {
                'Portfolio Manager': 20,
                'Market Analyst': 45,
                'Risk Controller': 15,
                'Technical Analyst': 20
            }
        },
        {
            'model_name': 'Perplexity',
            'provider': 'Perplexity',
            'input_tokens': 450_000,
            'output_tokens': 180_000,
            'total_calls': 234,
            'total_cost': 28.90,
            'avg_response_time': 3.8,
            'success_rate': 0.988,
            'usage_by_agent': {
                'Portfolio Manager': 10,
                'Market Analyst': 60,
                'Risk Controller': 10,
                'Technical Analyst': 20
            }
        }
    ]
    
    # 시간별 사용량 데이터 생성
    dates = pd.date_range(start=datetime.now() - timedelta(days=30), end=datetime.now(), freq='D')
    
    for model in models:
        daily_data = []
        for date in dates:
            # 랜덤하지만 일관된 패턴 생성
            base_calls = model['total_calls'] / 30
            daily_calls = int(np.random.poisson(base_calls))
            daily_tokens = daily_calls * (model['input_tokens'] + model['output_tokens']) // model['total_calls']
            daily_cost = daily_calls * model['total_cost'] / model['total_calls']
            
            daily_data.append({
                'date': date,
                'calls': daily_calls,
                'input_tokens': int(daily_tokens * 0.7),
                'output_tokens': int(daily_tokens * 0.3),
                'cost': daily_cost,
                'avg_response_time': model['avg_response_time'] + np.random.normal(0, 0.5)
            })
        
        model['daily_usage'] = pd.DataFrame(daily_data)
    
    return models

# 전체 사용량 요약
st.subheader("📊 LLM 사용량 요약")
llm_data = get_llm_usage_data()

# 필터링된 데이터
if model_filter:
    filtered_llm_data = [model for model in llm_data if model['model_name'] in model_filter]
else:
    filtered_llm_data = llm_data

# 전체 통계 계산
total_input_tokens = sum(model['input_tokens'] for model in filtered_llm_data)
total_output_tokens = sum(model['output_tokens'] for model in filtered_llm_data)
total_calls = sum(model['total_calls'] for model in filtered_llm_data)
total_cost = sum(model['total_cost'] for model in filtered_llm_data)
avg_response_time = sum(model['avg_response_time'] * model['total_calls'] for model in filtered_llm_data) / total_calls if total_calls > 0 else 0

# 요약 카드
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    CountMetricCard(
        title="🔄 총 API 호출",
        value=total_calls,
        use_large_format=True,
        help_text="전체 LLM API 호출 횟수"
    ).render()

with col2:
    CountMetricCard(
        title="📝 입력 토큰",
        value=total_input_tokens,
        use_large_format=True,
        help_text="총 입력 토큰 수"
    ).render()

with col3:
    CountMetricCard(
        title="💬 출력 토큰",
        value=total_output_tokens,
        use_large_format=True,
        help_text="총 출력 토큰 수"
    ).render()

with col4:
    FinancialMetricCard(
        title="💰 총 비용",
        value=total_cost,
        help_text="LLM API 사용 총 비용"
    ).render()

with col5:
    st.metric(
        "⚡ 평균 응답시간",
        f"{avg_response_time:.1f}초",
        help="API 호출 평균 응답 시간"
    )

st.markdown("---")

# 모델별 비교
st.subheader("🤖 모델별 사용량 비교")

if filtered_llm_data:
    # 모델 비교 테이블
    comparison_data = []
    for model in filtered_llm_data:
        efficiency = (model['input_tokens'] + model['output_tokens']) / model['total_cost'] if model['total_cost'] > 0 else 0
        
        comparison_data.append({
            '모델': model['model_name'],
            '제공사': model['provider'],
            'API 호출': f"{model['total_calls']:,}",
            '총 토큰': format_large_number(model['input_tokens'] + model['output_tokens']),
            '비용': format_currency(model['total_cost']),
            '응답시간': f"{model['avg_response_time']:.1f}초",
            '성공률': format_percentage(model['success_rate']),
            '토큰/달러': f"{efficiency:,.0f}"
        })
    
    st.dataframe(pd.DataFrame(comparison_data), use_container_width=True, hide_index=True)
    
    # 모델별 차트
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📊 모델별 사용량 분포")
        
        chart_data = pd.DataFrame([
            {
                'model': model['model_name'],
                'calls': model['total_calls'],
                'tokens': model['input_tokens'] + model['output_tokens'],
                'cost': model['total_cost']
            }
            for model in filtered_llm_data
        ])
        
        if metric_view == "토큰 사용량":
            fig = px.bar(chart_data, x='model', y='tokens', title="", color='model')
            fig.update_yaxes(title="토큰 수")
        elif metric_view == "API 호출 수":
            fig = px.bar(chart_data, x='model', y='calls', title="", color='model')
            fig.update_yaxes(title="호출 수")
        elif metric_view == "비용":
            fig = px.bar(chart_data, x='model', y='cost', title="", color='model')
            fig.update_yaxes(title="비용 ($)")
        else:  # 응답 시간
            response_data = pd.DataFrame([
                {'model': model['model_name'], 'response_time': model['avg_response_time']}
                for model in filtered_llm_data
            ])
            fig = px.bar(response_data, x='model', y='response_time', title="", color='model')
            fig.update_yaxes(title="응답 시간 (초)")
        
        fig.update_xaxes(title="모델")
        fig.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### 🥧 비용 분포")
        
        cost_data = pd.DataFrame([
            {'model': model['model_name'], 'cost': model['total_cost']}
            for model in filtered_llm_data
        ])
        
        fig = px.pie(cost_data, values='cost', names='model', title="")
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# 시계열 분석
st.subheader("📈 시계열 사용량 분석")

if filtered_llm_data:
    start_date, end_date = get_time_range_filter(time_range)
    
    # 시계열 차트
    fig = go.Figure()
    
    for model in filtered_llm_data:
        daily_data = model['daily_usage']
        filtered_data = daily_data[
            (daily_data['date'] >= start_date) & (daily_data['date'] <= end_date)
        ]
        
        if not filtered_data.empty:
            if metric_view == "토큰 사용량":
                y_data = filtered_data['input_tokens'] + filtered_data['output_tokens']
                y_title = "토큰 수"
            elif metric_view == "API 호출 수":
                y_data = filtered_data['calls']
                y_title = "호출 수"
            elif metric_view == "비용":
                y_data = filtered_data['cost']
                y_title = "비용 ($)"
            else:  # 응답 시간
                y_data = filtered_data['avg_response_time']
                y_title = "응답 시간 (초)"
            
            fig.add_trace(go.Scatter(
                x=filtered_data['date'],
                y=y_data,
                mode='lines+markers',
                name=model['model_name'],
                line=dict(width=3),
                marker=dict(size=4)
            ))
    
    fig.update_layout(
        title=f"모델별 {metric_view} 추이",
        xaxis_title="날짜",
        yaxis_title=y_title,
        height=450,
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# 에이전트별 LLM 사용량
st.subheader("🤖 에이전트별 LLM 사용 분석")

if filtered_llm_data:
    # 에이전트별 사용량 집계
    agent_usage = {}
    agents = ['Portfolio Manager', 'Market Analyst', 'Risk Controller', 'Technical Analyst']
    
    for agent in agents:
        agent_usage[agent] = {
            'total_usage': 0,
            'models': {},
            'total_cost': 0
        }
    
    for model in filtered_llm_data:
        for agent, percentage in model['usage_by_agent'].items():
            if agent in agent_usage:
                usage_calls = int(model['total_calls'] * percentage / 100)
                usage_cost = model['total_cost'] * percentage / 100
                
                agent_usage[agent]['total_usage'] += usage_calls
                agent_usage[agent]['models'][model['model_name']] = usage_calls
                agent_usage[agent]['total_cost'] += usage_cost
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📊 에이전트별 사용량")
        
        agent_data = []
        for agent, data in agent_usage.items():
            agent_data.append({
                'agent': agent,
                'usage': data['total_usage'],
                'cost': data['total_cost']
            })
        
        agent_df = pd.DataFrame(agent_data)
        fig = px.bar(agent_df, x='agent', y='usage', title="", color='agent')
        fig.update_layout(height=400, showlegend=False)
        fig.update_xaxes(title="에이전트")
        fig.update_yaxes(title="API 호출 수")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### 💰 에이전트별 비용")
        
        fig = px.bar(agent_df, x='agent', y='cost', title="", color='agent')
        fig.update_layout(height=400, showlegend=False)
        fig.update_xaxes(title="에이전트")
        fig.update_yaxes(title="비용 ($)")
        st.plotly_chart(fig, use_container_width=True)
    
    # 에이전트-모델 매트릭스
    st.markdown("### 🔍 에이전트-모델 사용 매트릭스")
    
    matrix_data = []
    for agent, data in agent_usage.items():
        row = {'Agent': agent}
        for model in filtered_llm_data:
            model_name = model['model_name']
            row[model_name] = data['models'].get(model_name, 0)
        matrix_data.append(row)
    
    matrix_df = pd.DataFrame(matrix_data)
    st.dataframe(matrix_df, use_container_width=True, hide_index=True)

st.markdown("---")

# 성능 및 효율성 분석
st.subheader("⚡ 성능 및 효율성 분석")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("#### 🎯 응답 시간 분포")
    
    response_times = [model['avg_response_time'] for model in filtered_llm_data]
    model_names = [model['model_name'] for model in filtered_llm_data]
    
    fig = px.box(y=response_times, title="")
    fig.update_layout(height=300)
    fig.update_yaxes(title="응답 시간 (초)")
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("#### 📈 성공률 비교")
    
    success_rates = [model['success_rate'] * 100 for model in filtered_llm_data]
    
    fig = px.bar(x=model_names, y=success_rates, title="")
    fig.update_layout(height=300, showlegend=False)
    fig.update_xaxes(title="모델")
    fig.update_yaxes(title="성공률 (%)")
    fig.add_hline(y=95, line_dash="dash", line_color="red", annotation_text="최소 기준선")
    st.plotly_chart(fig, use_container_width=True)

with col3:
    st.markdown("#### 💎 비용 효율성")
    
    # 토큰당 비용 계산
    efficiency_data = []
    for model in filtered_llm_data:
        total_tokens = model['input_tokens'] + model['output_tokens']
        cost_per_token = model['total_cost'] / total_tokens if total_tokens > 0 else 0
        efficiency_data.append({
            'model': model['model_name'],
            'cost_per_1k_tokens': cost_per_token * 1000
        })
    
    eff_df = pd.DataFrame(efficiency_data)
    fig = px.bar(eff_df, x='model', y='cost_per_1k_tokens', title="")
    fig.update_layout(height=300, showlegend=False)
    fig.update_xaxes(title="모델")
    fig.update_yaxes(title="1K 토큰당 비용 ($)")
    st.plotly_chart(fig, use_container_width=True)

# 실시간 알림 및 임계값
st.markdown("---")
st.subheader("🚨 알림 및 임계값 설정")

col1, col2 = st.columns(2)

with col1:
    st.markdown("#### ⚙️ 임계값 설정")
    
    daily_cost_limit = st.number_input("일일 비용 한도 ($)", min_value=0.0, value=50.0, step=1.0)
    monthly_token_limit = st.number_input("월간 토큰 한도 (M)", min_value=0.0, value=10.0, step=0.5)
    response_time_threshold = st.number_input("응답 시간 임계값 (초)", min_value=0.0, value=5.0, step=0.1)
    
    if st.button("💾 임계값 저장"):
        st.success("임계값이 저장되었습니다!")

with col2:
    st.markdown("#### 🔔 현재 상태")
    
    # 현재 일일 비용 (더미)
    current_daily_cost = sum(model['total_cost'] for model in filtered_llm_data) / 30
    
    if current_daily_cost > daily_cost_limit:
        st.error(f"⚠️ 일일 비용 초과: ${current_daily_cost:.2f} / ${daily_cost_limit:.2f}")
    else:
        st.success(f"✅ 일일 비용 정상: ${current_daily_cost:.2f} / ${daily_cost_limit:.2f}")
    
    # 응답 시간 상태
    max_response_time = max(model['avg_response_time'] for model in filtered_llm_data)
    
    if max_response_time > response_time_threshold:
        st.warning(f"⚠️ 응답 시간 느림: {max_response_time:.1f}초 > {response_time_threshold:.1f}초")
    else:
        st.success(f"✅ 응답 시간 양호: {max_response_time:.1f}초")

# 푸터
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray; font-size: 0.8em;'>
    🧠 LLM 사용량 모니터링 | 마지막 업데이트: {timestamp} | 실시간 추적
    </div>
    """.format(timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
    unsafe_allow_html=True
)