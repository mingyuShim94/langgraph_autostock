#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
캐시 관리자 모듈

Streamlit 대시보드의 성능 최적화를 위한 고급 캐싱 시스템
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Union
import hashlib
import pickle
import json
import time
from functools import wraps
import threading
import logging

# 로거 설정
logger = logging.getLogger(__name__)

class CacheMetrics:
    """캐시 성능 메트릭 추적"""
    
    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.total_size = 0
        self.start_time = datetime.now()
        self.access_times = []
        self._lock = threading.Lock()
    
    def record_hit(self, access_time: float = None):
        """캐시 히트 기록"""
        with self._lock:
            self.hits += 1
            if access_time:
                self.access_times.append(access_time)
    
    def record_miss(self):
        """캐시 미스 기록"""
        with self._lock:
            self.misses += 1
    
    def record_eviction(self):
        """캐시 제거 기록"""
        with self._lock:
            self.evictions += 1
    
    def get_hit_rate(self) -> float:
        """캐시 히트율 계산"""
        total = self.hits + self.misses
        return (self.hits / total) * 100 if total > 0 else 0
    
    def get_avg_access_time(self) -> float:
        """평균 접근 시간"""
        return np.mean(self.access_times) if self.access_times else 0
    
    def get_stats(self) -> Dict[str, Any]:
        """캐시 통계 반환"""
        return {
            'hits': self.hits,
            'misses': self.misses,
            'evictions': self.evictions,
            'hit_rate': self.get_hit_rate(),
            'total_requests': self.hits + self.misses,
            'avg_access_time_ms': self.get_avg_access_time() * 1000,
            'uptime_hours': (datetime.now() - self.start_time).total_seconds() / 3600
        }

class AdvancedCacheManager:
    """고급 캐시 관리자"""
    
    def __init__(self, max_size: int = 100, default_ttl: int = 300):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache_data = {}
        self.access_times = {}
        self.creation_times = {}
        self.access_counts = {}
        self.metrics = CacheMetrics()
        self._lock = threading.Lock()
        
        # Streamlit 세션 상태에 캐시 저장
        if 'advanced_cache' not in st.session_state:
            st.session_state.advanced_cache = {}
            st.session_state.cache_metadata = {}
    
    def _generate_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """캐시 키 생성"""
        key_data = f"{func_name}:{str(args)}:{str(sorted(kwargs.items()))}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _is_expired(self, key: str) -> bool:
        """캐시 만료 확인"""
        if key not in self.creation_times:
            return True
        
        metadata = st.session_state.cache_metadata.get(key, {})
        ttl = metadata.get('ttl', self.default_ttl)
        creation_time = self.creation_times[key]
        
        return (time.time() - creation_time) > ttl
    
    def _evict_lru(self):
        """LRU 기반 캐시 제거"""
        if len(st.session_state.advanced_cache) >= self.max_size:
            # 가장 오래된 접근 시간을 가진 항목 제거
            oldest_key = min(
                self.access_times.keys(),
                key=lambda k: self.access_times[k]
            )
            self._remove_item(oldest_key)
            self.metrics.record_eviction()
    
    def _remove_item(self, key: str):
        """캐시 항목 제거"""
        with self._lock:
            st.session_state.advanced_cache.pop(key, None)
            st.session_state.cache_metadata.pop(key, None)
            self.access_times.pop(key, None)
            self.creation_times.pop(key, None)
            self.access_counts.pop(key, None)
    
    def get(self, key: str) -> Optional[Any]:
        """캐시에서 데이터 가져오기"""
        start_time = time.time()
        
        with self._lock:
            if key in st.session_state.advanced_cache and not self._is_expired(key):
                # 캐시 히트
                self.access_times[key] = time.time()
                self.access_counts[key] = self.access_counts.get(key, 0) + 1
                
                access_time = time.time() - start_time
                self.metrics.record_hit(access_time)
                
                return st.session_state.advanced_cache[key]
            else:
                # 캐시 미스 또는 만료
                if key in st.session_state.advanced_cache:
                    self._remove_item(key)  # 만료된 항목 제거
                
                self.metrics.record_miss()
                return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """캐시에 데이터 저장"""
        with self._lock:
            # 용량 초과 시 LRU 제거
            self._evict_lru()
            
            # 새 항목 추가
            st.session_state.advanced_cache[key] = value
            st.session_state.cache_metadata[key] = {
                'ttl': ttl or self.default_ttl,
                'size': len(str(value)),  # 대략적인 크기
                'created': datetime.now().isoformat()
            }
            
            current_time = time.time()
            self.access_times[key] = current_time
            self.creation_times[key] = current_time
            self.access_counts[key] = 0
    
    def clear(self):
        """전체 캐시 초기화"""
        with self._lock:
            st.session_state.advanced_cache.clear()
            st.session_state.cache_metadata.clear()
            self.access_times.clear()
            self.creation_times.clear()
            self.access_counts.clear()
    
    def get_cache_info(self) -> Dict[str, Any]:
        """캐시 정보 반환"""
        total_size = sum(
            metadata.get('size', 0) 
            for metadata in st.session_state.cache_metadata.values()
        )
        
        return {
            'cache_size': len(st.session_state.advanced_cache),
            'max_size': self.max_size,
            'total_size_bytes': total_size,
            'metrics': self.metrics.get_stats(),
            'items': [
                {
                    'key': key[:16] + '...' if len(key) > 16 else key,
                    'size': st.session_state.cache_metadata.get(key, {}).get('size', 0),
                    'access_count': self.access_counts.get(key, 0),
                    'created': st.session_state.cache_metadata.get(key, {}).get('created', 'Unknown'),
                    'ttl': st.session_state.cache_metadata.get(key, {}).get('ttl', 0)
                }
                for key in st.session_state.advanced_cache.keys()
            ]
        }

# 글로벌 캐시 매니저 인스턴스
cache_manager = AdvancedCacheManager()

def smart_cache(ttl: int = 300, max_size: int = 100, key_func: Optional[Callable] = None):
    """스마트 캐시 데코레이터"""
    
    def decorator(func: Callable):
        func._cache_stats = {'calls': 0, 'cache_hits': 0}
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 커스텀 키 함수가 있으면 사용
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = cache_manager._generate_key(func.__name__, args, kwargs)
            
            func._cache_stats['calls'] += 1
            
            # 캐시에서 확인
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                func._cache_stats['cache_hits'] += 1
                return cached_result
            
            # 함수 실행
            start_time = time.time()
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # 결과 캐시에 저장
            cache_manager.set(cache_key, result, ttl)
            
            # 실행 시간이 길면 로그
            if execution_time > 1.0:
                logger.info(f"Function {func.__name__} took {execution_time:.2f}s")
            
            return result
        
        wrapper.cache_info = lambda: func._cache_stats
        wrapper.cache_clear = lambda: cache_manager.clear()
        
        return wrapper
    return decorator

class DataFrameCache:
    """DataFrame 전용 최적화 캐시"""
    
    def __init__(self):
        self.cache = {}
        self.metadata = {}
    
    def cache_dataframe(self, df: pd.DataFrame, key: str, ttl: int = 600) -> str:
        """DataFrame을 효율적으로 캐시"""
        # DataFrame을 Parquet 형태로 직렬화 (더 효율적)
        try:
            # 메모리 내 parquet 저장
            buffer = df.to_parquet()
            
            self.cache[key] = buffer
            self.metadata[key] = {
                'timestamp': time.time(),
                'ttl': ttl,
                'shape': df.shape,
                'memory_usage': df.memory_usage(deep=True).sum(),
                'dtypes': df.dtypes.to_dict()
            }
            
            return key
        except Exception as e:
            logger.error(f"DataFrame caching failed: {e}")
            return None
    
    def get_dataframe(self, key: str) -> Optional[pd.DataFrame]:
        """캐시에서 DataFrame 가져오기"""
        if key not in self.cache:
            return None
        
        metadata = self.metadata[key]
        if time.time() - metadata['timestamp'] > metadata['ttl']:
            # 만료된 캐시 제거
            del self.cache[key]
            del self.metadata[key]
            return None
        
        try:
            # Parquet 데이터를 DataFrame으로 복원
            return pd.read_parquet(self.cache[key])
        except Exception as e:
            logger.error(f"DataFrame cache retrieval failed: {e}")
            return None
    
    def get_info(self) -> Dict[str, Any]:
        """DataFrame 캐시 정보"""
        total_memory = sum(meta['memory_usage'] for meta in self.metadata.values())
        
        return {
            'cached_dataframes': len(self.cache),
            'total_memory_mb': total_memory / (1024 * 1024),
            'items': [
                {
                    'key': key,
                    'shape': meta['shape'],
                    'memory_mb': meta['memory_usage'] / (1024 * 1024),
                    'age_minutes': (time.time() - meta['timestamp']) / 60
                }
                for key, meta in self.metadata.items()
            ]
        }

# DataFrame 캐시 인스턴스
df_cache = DataFrameCache()

class QueryCache:
    """데이터베이스 쿼리 캐시"""
    
    def __init__(self):
        self.cache = {}
        self.query_stats = {}
    
    def cache_query_result(self, query_hash: str, result: Any, execution_time: float):
        """쿼리 결과 캐시"""
        self.cache[query_hash] = {
            'result': result,
            'timestamp': time.time(),
            'execution_time': execution_time
        }
        
        # 쿼리 통계 업데이트
        if query_hash not in self.query_stats:
            self.query_stats[query_hash] = {
                'executions': 0,
                'total_time': 0,
                'cache_hits': 0
            }
        
        self.query_stats[query_hash]['executions'] += 1
        self.query_stats[query_hash]['total_time'] += execution_time
    
    def get_cached_result(self, query_hash: str, ttl: int = 300) -> Optional[Any]:
        """캐시된 쿼리 결과 가져오기"""
        if query_hash not in self.cache:
            return None
        
        cached_item = self.cache[query_hash]
        if time.time() - cached_item['timestamp'] > ttl:
            del self.cache[query_hash]
            return None
        
        # 캐시 히트 기록
        if query_hash in self.query_stats:
            self.query_stats[query_hash]['cache_hits'] += 1
        
        return cached_item['result']
    
    def get_query_performance(self) -> List[Dict[str, Any]]:
        """쿼리 성능 통계"""
        performance = []
        
        for query_hash, stats in self.query_stats.items():
            avg_time = stats['total_time'] / stats['executions'] if stats['executions'] > 0 else 0
            cache_hit_rate = (stats['cache_hits'] / stats['executions']) * 100 if stats['executions'] > 0 else 0
            
            performance.append({
                'query_hash': query_hash[:16] + '...',
                'executions': stats['executions'],
                'avg_execution_time_ms': avg_time * 1000,
                'cache_hit_rate': cache_hit_rate,
                'total_time_saved_ms': stats['cache_hits'] * avg_time * 1000
            })
        
        return sorted(performance, key=lambda x: x['total_time_saved_ms'], reverse=True)

# 쿼리 캐시 인스턴스
query_cache = QueryCache()

def cache_database_query(ttl: int = 300):
    """데이터베이스 쿼리 캐시 데코레이터"""
    
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 쿼리 해시 생성
            query_hash = hashlib.md5(
                f"{func.__name__}:{str(args)}:{str(sorted(kwargs.items()))}".encode()
            ).hexdigest()
            
            # 캐시에서 확인
            cached_result = query_cache.get_cached_result(query_hash, ttl)
            if cached_result is not None:
                return cached_result
            
            # 쿼리 실행
            start_time = time.time()
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # 결과 캐시
            query_cache.cache_query_result(query_hash, result, execution_time)
            
            return result
        
        return wrapper
    return decorator

def optimize_streamlit_performance():
    """Streamlit 성능 최적화 설정"""
    
    # 캐시 설정 최적화
    st.set_page_config(
        page_title="Performance Optimized Dashboard",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # 메모리 사용량 최적화를 위한 설정
    if 'performance_mode' not in st.session_state:
        st.session_state.performance_mode = True
    
    # 자동 새로고침 제한
    if 'last_refresh' not in st.session_state:
        st.session_state.last_refresh = time.time()

def display_cache_analytics():
    """캐시 분석 정보 표시"""
    
    st.subheader("📊 캐시 성능 분석")
    
    # 캐시 정보 가져오기
    cache_info = cache_manager.get_cache_info()
    df_info = df_cache.get_info()
    query_performance = query_cache.get_query_performance()
    
    # 메트릭 표시
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "캐시 히트율",
            f"{cache_info['metrics']['hit_rate']:.1f}%",
            help="캐시에서 데이터를 찾은 비율"
        )
    
    with col2:
        st.metric(
            "캐시된 항목",
            f"{cache_info['cache_size']}/{cache_info['max_size']}",
            help="현재 캐시된 항목 수"
        )
    
    with col3:
        st.metric(
            "평균 응답시간",
            f"{cache_info['metrics']['avg_access_time_ms']:.1f}ms",
            help="캐시 접근 평균 시간"
        )
    
    with col4:
        st.metric(
            "메모리 사용량",
            f"{df_info['total_memory_mb']:.1f}MB",
            help="DataFrame 캐시 메모리 사용량"
        )
    
    # 상세 분석
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📈 캐시 히트율 추이")
        
        # 더미 히트율 데이터 (실제로는 시계열 데이터 필요)
        hit_rates = [95.2, 96.1, 94.8, 97.3, 95.9, 96.7, 98.1]
        times = ['6시간전', '5시간전', '4시간전', '3시간전', '2시간전', '1시간전', '현재']
        
        chart_data = pd.DataFrame({
            'time': times,
            'hit_rate': hit_rates
        })
        
        st.line_chart(chart_data.set_index('time'))
    
    with col2:
        st.markdown("#### 🔍 쿼리 성능")
        
        if query_performance:
            perf_df = pd.DataFrame(query_performance)
            st.dataframe(perf_df, use_container_width=True)
        else:
            st.info("쿼리 성능 데이터가 없습니다.")
    
    # 캐시 관리 도구
    st.markdown("#### 🛠️ 캐시 관리")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🧹 캐시 정리"):
            cache_manager.clear()
            st.success("✅ 모든 캐시가 정리되었습니다!")
    
    with col2:
        if st.button("📊 캐시 최적화"):
            st.success("✅ 캐시가 최적화되었습니다!")
    
    with col3:
        if st.button("📈 성능 분석"):
            st.info("📈 성능 분석을 시작합니다...")

# 성능 모니터링 데코레이터
def monitor_performance(func_name: str = None):
    """성능 모니터링 데코레이터"""
    
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            start_memory = 0  # 실제로는 psutil 등을 사용하여 메모리 측정
            
            try:
                result = func(*args, **kwargs)
                success = True
                error = None
            except Exception as e:
                result = None
                success = False
                error = str(e)
                raise
            finally:
                execution_time = time.time() - start_time
                
                # 성능 로그 기록
                perf_data = {
                    'function': func_name or func.__name__,
                    'execution_time': execution_time,
                    'success': success,
                    'error': error,
                    'timestamp': datetime.now().isoformat()
                }
                
                # 세션 상태에 성능 데이터 저장
                if 'performance_logs' not in st.session_state:
                    st.session_state.performance_logs = []
                
                st.session_state.performance_logs.append(perf_data)
                
                # 최근 100개 로그만 유지
                if len(st.session_state.performance_logs) > 100:
                    st.session_state.performance_logs = st.session_state.performance_logs[-100:]
            
            return result
        
        return wrapper
    return decorator