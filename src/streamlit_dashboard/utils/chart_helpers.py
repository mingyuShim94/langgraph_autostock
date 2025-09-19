#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Streamlit 차트 생성 헬퍼 모듈

다양한 차트와 시각화 요소를 생성하는 유틸리티 함수들
"""

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
import streamlit as st

# 차트 색상 팔레트
COLOR_PALETTE = {
    'primary': '#1f77b4',
    'success': '#2ca02c',
    'warning': '#ff7f0e',
    'danger': '#d62728',
    'info': '#17becf',
    'secondary': '#7f7f7f',
    'light': '#bcbd22',
    'dark': '#8c564b'
}

TRADING_COLORS = {
    'profit': '#00C851',
    'loss': '#FF4444',
    'buy': '#007E33',
    'sell': '#CC0000',
    'neutral': '#6c757d'
}

def create_line_chart(
    data: pd.DataFrame,
    x_col: str,
    y_col: str,
    title: str = "",
    x_title: str = "",
    y_title: str = "",
    color: str = COLOR_PALETTE['primary'],
    show_markers: bool = True,
    height: int = 400
) -> go.Figure:
    """기본 라인 차트 생성"""
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=data[x_col],
        y=data[y_col],
        mode='lines+markers' if show_markers else 'lines',
        name=y_col,
        line=dict(color=color, width=2),
        marker=dict(size=6 if show_markers else 0)
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title=x_title,
        yaxis_title=y_title,
        height=height,
        showlegend=False,
        hovermode='x unified'
    )
    
    return fig

def create_multi_line_chart(
    data: pd.DataFrame,
    x_col: str,
    y_cols: List[str],
    title: str = "",
    x_title: str = "",
    y_title: str = "",
    colors: Optional[List[str]] = None,
    height: int = 400
) -> go.Figure:
    """다중 라인 차트 생성"""
    
    fig = go.Figure()
    
    if colors is None:
        colors = list(COLOR_PALETTE.values())[:len(y_cols)]
    
    for i, y_col in enumerate(y_cols):
        color = colors[i % len(colors)]
        fig.add_trace(go.Scatter(
            x=data[x_col],
            y=data[y_col],
            mode='lines+markers',
            name=y_col,
            line=dict(color=color, width=2),
            marker=dict(size=4)
        ))
    
    fig.update_layout(
        title=title,
        xaxis_title=x_title,
        yaxis_title=y_title,
        height=height,
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig

def create_bar_chart(
    data: pd.DataFrame,
    x_col: str,
    y_col: str,
    title: str = "",
    x_title: str = "",
    y_title: str = "",
    color_col: Optional[str] = None,
    height: int = 400,
    horizontal: bool = False
) -> go.Figure:
    """막대 차트 생성"""
    
    if horizontal:
        fig = px.bar(
            data, x=y_col, y=x_col,
            title=title,
            color=color_col,
            orientation='h',
            height=height
        )
        fig.update_xaxes(title=y_title)
        fig.update_yaxes(title=x_title)
    else:
        fig = px.bar(
            data, x=x_col, y=y_col,
            title=title,
            color=color_col,
            height=height
        )
        fig.update_xaxes(title=x_title)
        fig.update_yaxes(title=y_title)
    
    fig.update_layout(showlegend=bool(color_col))
    
    return fig

def create_pie_chart(
    data: pd.DataFrame,
    values_col: str,
    names_col: str,
    title: str = "",
    height: int = 400,
    hole_size: float = 0.0
) -> go.Figure:
    """원형 차트 (도넛 차트 포함) 생성"""
    
    fig = px.pie(
        data,
        values=values_col,
        names=names_col,
        title=title,
        height=height,
        hole=hole_size
    )
    
    fig.update_traces(
        textposition='inside',
        textinfo='percent+label'
    )
    
    return fig

def create_candlestick_chart(
    data: pd.DataFrame,
    date_col: str,
    open_col: str,
    high_col: str,
    low_col: str,
    close_col: str,
    title: str = "주가 차트",
    volume_col: Optional[str] = None,
    height: int = 500
) -> go.Figure:
    """캔들스틱 차트 생성"""
    
    if volume_col:
        # 부차트와 함께 생성
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.1,
            row_width=[0.7, 0.3],
            subplot_titles=(title, "거래량")
        )
        
        # 캔들스틱 차트
        fig.add_trace(
            go.Candlestick(
                x=data[date_col],
                open=data[open_col],
                high=data[high_col],
                low=data[low_col],
                close=data[close_col],
                name="가격"
            ),
            row=1, col=1
        )
        
        # 거래량 차트
        fig.add_trace(
            go.Bar(
                x=data[date_col],
                y=data[volume_col],
                name="거래량",
                marker_color='rgba(158,202,225,0.6)'
            ),
            row=2, col=1
        )
    else:
        fig = go.Figure(data=[go.Candlestick(
            x=data[date_col],
            open=data[open_col],
            high=data[high_col],
            low=data[low_col],
            close=data[close_col],
            name="가격"
        )])
        
        fig.update_layout(title=title)
    
    fig.update_layout(
        height=height,
        xaxis_rangeslider_visible=False,
        showlegend=False
    )
    
    return fig

def create_heatmap(
    data: pd.DataFrame,
    x_col: str,
    y_col: str,
    z_col: str,
    title: str = "",
    colorscale: str = "RdYlBu_r",
    height: int = 400
) -> go.Figure:
    """히트맵 생성"""
    
    pivot_data = data.pivot(index=y_col, columns=x_col, values=z_col)
    
    fig = go.Figure(data=go.Heatmap(
        z=pivot_data.values,
        x=pivot_data.columns,
        y=pivot_data.index,
        colorscale=colorscale,
        hoverongaps=False
    ))
    
    fig.update_layout(
        title=title,
        height=height
    )
    
    return fig

def create_gauge_chart(
    value: float,
    title: str,
    min_val: float = 0,
    max_val: float = 100,
    threshold_ranges: Optional[List[Dict]] = None,
    height: int = 300
) -> go.Figure:
    """게이지 차트 생성"""
    
    if threshold_ranges is None:
        threshold_ranges = [
            {'range': [0, 30], 'color': TRADING_COLORS['loss']},
            {'range': [30, 70], 'color': COLOR_PALETTE['warning']},
            {'range': [70, 100], 'color': TRADING_COLORS['profit']}
        ]
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=value,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title},
        gauge={
            'axis': {'range': [min_val, max_val]},
            'bar': {'color': COLOR_PALETTE['primary']},
            'steps': [
                {'range': [r['range'][0], r['range'][1]], 'color': r['color']}
                for r in threshold_ranges
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': max_val * 0.9
            }
        }
    ))
    
    fig.update_layout(height=height)
    
    return fig

def create_performance_chart(
    data: pd.DataFrame,
    date_col: str,
    return_col: str,
    benchmark_col: Optional[str] = None,
    title: str = "성과 추이",
    height: int = 400
) -> go.Figure:
    """성과 추이 차트 생성"""
    
    fig = go.Figure()
    
    # 누적 수익률 계산
    cumulative_returns = (1 + data[return_col]).cumprod()
    
    fig.add_trace(go.Scatter(
        x=data[date_col],
        y=cumulative_returns,
        mode='lines',
        name='포트폴리오',
        line=dict(color=TRADING_COLORS['profit'], width=3)
    ))
    
    if benchmark_col and benchmark_col in data.columns:
        cumulative_benchmark = (1 + data[benchmark_col]).cumprod()
        fig.add_trace(go.Scatter(
            x=data[date_col],
            y=cumulative_benchmark,
            mode='lines',
            name='벤치마크',
            line=dict(color=COLOR_PALETTE['secondary'], width=2, dash='dash')
        ))
    
    fig.update_layout(
        title=title,
        xaxis_title="날짜",
        yaxis_title="누적 수익률",
        height=height,
        hovermode='x unified'
    )
    
    return fig

def create_agent_performance_chart(
    agent_data: List[Dict[str, Any]],
    title: str = "에이전트 성과",
    height: int = 400
) -> go.Figure:
    """에이전트 성과 비교 차트"""
    
    agents = [d['agent_name'] for d in agent_data]
    returns = [d.get('total_return', 0) for d in agent_data]
    trades = [d.get('total_trades', 0) for d in agent_data]
    win_rates = [d.get('win_rate', 0) for d in agent_data]
    
    # 부차트 생성
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('총 수익률', '거래 횟수', '승률', '위험 조정 수익률'),
        specs=[[{"secondary_y": False}, {"secondary_y": False}],
               [{"secondary_y": False}, {"secondary_y": False}]]
    )
    
    # 총 수익률
    fig.add_trace(
        go.Bar(x=agents, y=returns, name='수익률',
               marker_color=[TRADING_COLORS['profit'] if r > 0 else TRADING_COLORS['loss'] for r in returns]),
        row=1, col=1
    )
    
    # 거래 횟수
    fig.add_trace(
        go.Bar(x=agents, y=trades, name='거래수', marker_color=COLOR_PALETTE['info']),
        row=1, col=2
    )
    
    # 승률
    fig.add_trace(
        go.Bar(x=agents, y=win_rates, name='승률', marker_color=COLOR_PALETTE['warning']),
        row=2, col=1
    )
    
    # 샤프 비율 (더미 데이터)
    sharpe_ratios = [np.random.uniform(0.5, 2.0) for _ in agents]
    fig.add_trace(
        go.Bar(x=agents, y=sharpe_ratios, name='샤프비율', marker_color=COLOR_PALETTE['secondary']),
        row=2, col=2
    )
    
    fig.update_layout(
        title_text=title,
        height=height,
        showlegend=False
    )
    
    return fig

def create_cost_analysis_chart(
    cost_data: pd.DataFrame,
    date_col: str,
    cost_col: str,
    category_col: Optional[str] = None,
    title: str = "비용 분석",
    height: int = 400
) -> go.Figure:
    """비용 분석 차트 생성"""
    
    if category_col and category_col in cost_data.columns:
        # 카테고리별 스택 차트
        fig = px.bar(
            cost_data,
            x=date_col,
            y=cost_col,
            color=category_col,
            title=title,
            height=height
        )
    else:
        # 기본 막대 차트
        fig = px.bar(
            cost_data,
            x=date_col,
            y=cost_col,
            title=title,
            height=height,
            color_discrete_sequence=[COLOR_PALETTE['danger']]
        )
    
    fig.update_layout(
        xaxis_title="날짜",
        yaxis_title="비용 ($)"
    )
    
    return fig

def create_correlation_matrix(
    data: pd.DataFrame,
    title: str = "상관관계 매트릭스",
    height: int = 500
) -> go.Figure:
    """상관관계 매트릭스 히트맵"""
    
    corr_matrix = data.corr()
    
    fig = go.Figure(data=go.Heatmap(
        z=corr_matrix.values,
        x=corr_matrix.columns,
        y=corr_matrix.index,
        colorscale='RdBu',
        zmid=0,
        text=corr_matrix.round(2).values,
        texttemplate="%{text}",
        textfont={"size": 10},
        hoverongaps=False
    ))
    
    fig.update_layout(
        title=title,
        height=height,
        xaxis={'side': 'bottom'}
    )
    
    return fig

def create_risk_return_scatter(
    data: pd.DataFrame,
    risk_col: str,
    return_col: str,
    name_col: Optional[str] = None,
    title: str = "위험-수익률 분포",
    height: int = 400
) -> go.Figure:
    """위험-수익률 산점도"""
    
    fig = go.Figure()
    
    if name_col and name_col in data.columns:
        for name in data[name_col].unique():
            subset = data[data[name_col] == name]
            fig.add_trace(go.Scatter(
                x=subset[risk_col],
                y=subset[return_col],
                mode='markers',
                name=name,
                marker=dict(size=12),
                text=subset[name_col] if name_col else None,
                hovertemplate=f"<b>%{{text}}</b><br>위험: %{{x:.2%}}<br>수익률: %{{y:.2%}}<extra></extra>"
            ))
    else:
        fig.add_trace(go.Scatter(
            x=data[risk_col],
            y=data[return_col],
            mode='markers',
            marker=dict(size=12, color=COLOR_PALETTE['primary']),
            hovertemplate="위험: %{x:.2%}<br>수익률: %{y:.2%}<extra></extra>"
        ))
    
    fig.update_layout(
        title=title,
        xaxis_title="위험 (변동성)",
        yaxis_title="수익률",
        height=height
    )
    
    return fig

def add_chart_annotations(
    fig: go.Figure,
    annotations: List[Dict[str, Any]]
) -> go.Figure:
    """차트에 주석 추가"""
    
    for ann in annotations:
        fig.add_annotation(
            x=ann.get('x'),
            y=ann.get('y'),
            text=ann.get('text', ''),
            showarrow=ann.get('showarrow', True),
            arrowhead=ann.get('arrowhead', 2),
            arrowsize=ann.get('arrowsize', 1),
            arrowwidth=ann.get('arrowwidth', 2),
            arrowcolor=ann.get('arrowcolor', COLOR_PALETTE['secondary'])
        )
    
    return fig

def apply_dark_theme(fig: go.Figure) -> go.Figure:
    """차트에 다크 테마 적용"""
    
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='white'
    )
    
    fig.update_xaxes(
        gridcolor='rgba(255,255,255,0.1)',
        zerolinecolor='rgba(255,255,255,0.1)'
    )
    
    fig.update_yaxes(
        gridcolor='rgba(255,255,255,0.1)',
        zerolinecolor='rgba(255,255,255,0.1)'
    )
    
    return fig

def export_chart_as_html(fig: go.Figure, filename: str) -> str:
    """차트를 HTML로 내보내기"""
    
    html_str = fig.to_html(include_plotlyjs=True)
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html_str)
    
    return filename