#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Streamlit 대시보드 공통 유틸리티 모듈

대시보드 전반에서 사용되는 공통 기능들을 제공
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import json
import hashlib
from functools import wraps
import time

class DashboardCache:
    """대시보드 캐싱 시스템"""
    
    def __init__(self):
        if 'dashboard_cache' not in st.session_state:
            st.session_state.dashboard_cache = {}
    
    def get(self, key: str) -> Optional[Any]:
        """캐시에서 데이터 가져오기"""
        cache_data = st.session_state.dashboard_cache.get(key)
        if cache_data:
            data, timestamp, ttl = cache_data
            if time.time() - timestamp < ttl:
                return data
            else:
                # 만료된 캐시 삭제
                del st.session_state.dashboard_cache[key]
        return None
    
    def set(self, key: str, value: Any, ttl: int = 300) -> None:
        """캐시에 데이터 저장 (기본 TTL: 5분)"""
        st.session_state.dashboard_cache[key] = (value, time.time(), ttl)
    
    def clear(self) -> None:
        """전체 캐시 초기화"""
        st.session_state.dashboard_cache.clear()

# 전역 캐시 인스턴스
cache = DashboardCache()

def cached_function(ttl: int = 300):
    """함수 결과를 캐싱하는 데코레이터"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 캐시 키 생성
            key_data = f"{func.__name__}:{str(args)}:{str(sorted(kwargs.items()))}"
            cache_key = hashlib.md5(key_data.encode()).hexdigest()
            
            # 캐시에서 확인
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # 함수 실행 및 캐시 저장
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            return result
        return wrapper
    return decorator

def format_currency(value: float, currency: str = "USD") -> str:
    """통화 형식으로 포맷"""
    if currency == "USD":
        return f"${value:,.2f}"
    elif currency == "KRW":
        return f"₩{value:,.0f}"
    else:
        return f"{value:,.2f} {currency}"

def format_percentage(value: float, precision: int = 2) -> str:
    """백분율 형식으로 포맷"""
    return f"{value:.{precision}%}"

def format_large_number(value: float, precision: int = 1) -> str:
    """큰 숫자를 K, M, B 단위로 포맷"""
    if abs(value) >= 1_000_000_000:
        return f"{value/1_000_000_000:.{precision}f}B"
    elif abs(value) >= 1_000_000:
        return f"{value/1_000_000:.{precision}f}M"
    elif abs(value) >= 1_000:
        return f"{value/1_000:.{precision}f}K"
    else:
        return f"{value:.{precision}f}"

def get_time_range_filter(range_type: str) -> Tuple[datetime, datetime]:
    """시간 범위 필터 생성"""
    now = datetime.now()
    
    if range_type == "1일":
        start_time = now - timedelta(days=1)
    elif range_type == "1주":
        start_time = now - timedelta(weeks=1)
    elif range_type == "1개월":
        start_time = now - timedelta(days=30)
    elif range_type == "3개월":
        start_time = now - timedelta(days=90)
    elif range_type == "6개월":
        start_time = now - timedelta(days=180)
    elif range_type == "1년":
        start_time = now - timedelta(days=365)
    else:  # "전체"
        start_time = datetime(2020, 1, 1)
    
    return start_time, now

def create_status_indicator(status: str, size: str = "normal") -> str:
    """상태 인디케이터 생성"""
    status_map = {
        "success": "🟢",
        "warning": "🟡", 
        "error": "🔴",
        "info": "🔵",
        "active": "✅",
        "inactive": "❌",
        "pending": "⏳",
        "completed": "✅"
    }
    
    if size == "large":
        return f"### {status_map.get(status.lower(), '❓')}"
    elif size == "small":
        return status_map.get(status.lower(), "❓")
    else:
        return f"## {status_map.get(status.lower(), '❓')}"

def create_metric_delta_color(delta: float) -> str:
    """메트릭 델타 색상 결정"""
    if delta > 0:
        return "normal"  # 초록색
    elif delta < 0:
        return "inverse"  # 빨간색
    else:
        return "off"  # 회색

def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """안전한 나눗셈 (0으로 나누기 방지)"""
    if denominator == 0 or denominator is None:
        return default
    return numerator / denominator

def calculate_percentage_change(current: float, previous: float) -> float:
    """변화율 계산"""
    if previous == 0 or previous is None:
        return 0.0
    return ((current - previous) / previous) * 100

def filter_dataframe_by_date(df: pd.DataFrame, date_column: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
    """날짜 범위로 데이터프레임 필터링"""
    if df.empty or date_column not in df.columns:
        return df
    
    # 날짜 컬럼을 datetime 타입으로 변환
    if not pd.api.types.is_datetime64_any_dtype(df[date_column]):
        df[date_column] = pd.to_datetime(df[date_column])
    
    return df[(df[date_column] >= start_date) & (df[date_column] <= end_date)]

def create_summary_cards(data: Dict[str, Any], columns: int = 4) -> None:
    """요약 카드 생성"""
    cols = st.columns(columns)
    
    for i, (key, value) in enumerate(data.items()):
        with cols[i % columns]:
            if isinstance(value, dict):
                st.metric(
                    label=value.get("label", key),
                    value=value.get("value", "N/A"),
                    delta=value.get("delta"),
                    delta_color=value.get("delta_color", "normal")
                )
            else:
                st.metric(label=key, value=value)

@cached_function(ttl=60)  # 1분 캐시
def get_system_status() -> Dict[str, Any]:
    """시스템 상태 정보 가져오기"""
    try:
        from src.database.schema import db_manager
        
        # 데이터베이스 연결 테스트
        total_trades = len(db_manager.get_all_trades())
        
        return {
            "database": {
                "status": "connected",
                "total_trades": total_trades,
                "last_updated": datetime.now()
            },
            "trading_system": {
                "status": "active",
                "last_heartbeat": datetime.now()
            }
        }
    except Exception as e:
        return {
            "database": {
                "status": "error",
                "error": str(e),
                "last_updated": datetime.now()
            },
            "trading_system": {
                "status": "unknown",
                "last_heartbeat": None
            }
        }

def show_loading_spinner(text: str = "로딩 중...") -> None:
    """로딩 스피너 표시"""
    with st.spinner(text):
        time.sleep(0.1)  # 짧은 지연으로 스피너 표시

def display_error_message(error: Exception, context: str = "") -> None:
    """에러 메시지 표시"""
    st.error(f"❌ 오류 발생{f' ({context})' if context else ''}")
    with st.expander("오류 세부사항"):
        st.code(str(error))

def create_download_button(data: Any, filename: str, mime_type: str = "application/json") -> None:
    """다운로드 버튼 생성"""
    if isinstance(data, pd.DataFrame):
        csv_data = data.to_csv(index=False)
        st.download_button(
            label="📥 CSV로 다운로드",
            data=csv_data,
            file_name=f"{filename}.csv",
            mime="text/csv"
        )
    elif isinstance(data, dict) or isinstance(data, list):
        json_data = json.dumps(data, ensure_ascii=False, indent=2)
        st.download_button(
            label="📥 JSON으로 다운로드",
            data=json_data,
            file_name=f"{filename}.json",
            mime=mime_type
        )

def validate_data_freshness(timestamp: datetime, max_age_minutes: int = 30) -> bool:
    """데이터 신선도 검증"""
    age = datetime.now() - timestamp
    return age.total_seconds() < (max_age_minutes * 60)

class SessionStateManager:
    """세션 상태 관리 헬퍼"""
    
    @staticmethod
    def get(key: str, default: Any = None) -> Any:
        """세션 상태에서 값 가져오기"""
        return st.session_state.get(key, default)
    
    @staticmethod
    def set(key: str, value: Any) -> None:
        """세션 상태에 값 설정"""
        st.session_state[key] = value
    
    @staticmethod
    def increment(key: str, amount: int = 1) -> int:
        """세션 상태 값 증가"""
        current = st.session_state.get(key, 0)
        new_value = current + amount
        st.session_state[key] = new_value
        return new_value
    
    @staticmethod
    def toggle(key: str) -> bool:
        """세션 상태 불린 값 토글"""
        current = st.session_state.get(key, False)
        new_value = not current
        st.session_state[key] = new_value
        return new_value

# 세션 관리자 인스턴스
session = SessionStateManager()

def setup_page_config(
    title: str,
    icon: str = "📊",
    layout: str = "wide",
    sidebar_state: str = "expanded"
) -> None:
    """페이지 기본 설정"""
    st.set_page_config(
        page_title=title,
        page_icon=icon,
        layout=layout,
        initial_sidebar_state=sidebar_state
    )

def add_custom_css() -> None:
    """커스텀 CSS 스타일 추가"""
    st.markdown("""
    <style>
    /* 메트릭 카드 스타일 개선 */
    .metric-container {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    
    /* 성공/경고/오류 상태 색상 */
    .status-success { color: #28a745; }
    .status-warning { color: #ffc107; }
    .status-error { color: #dc3545; }
    .status-info { color: #17a2b8; }
    
    /* 사이드바 스타일 */
    .sidebar .sidebar-content {
        background-color: #f8f9fa;
    }
    
    /* 차트 컨테이너 */
    .chart-container {
        background-color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)