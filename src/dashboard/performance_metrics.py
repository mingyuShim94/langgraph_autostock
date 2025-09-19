#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
실시간 성과 메트릭 계산 시스템
에이전트별, LLM별, 전체 시스템 성과를 실시간으로 계산
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import numpy as np

from ..database.schema import db_manager


@dataclass
class RealTimeMetrics:
    """실시간 성과 메트릭 데이터 클래스"""
    timestamp: str
    
    # 전체 시스템 메트릭
    total_trades_today: int
    win_rate_today: float
    total_pnl_today: float
    total_cost_today: float
    
    # 에이전트별 메트릭
    agent_performance: Dict[str, Any]
    
    # LLM별 메트릭  
    llm_usage_stats: Dict[str, Any]
    
    # 트렌드 데이터
    hourly_trends: List[Dict[str, Any]]
    daily_trends: List[Dict[str, Any]]
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'timestamp': self.timestamp,
            'system_metrics': {
                'total_trades_today': self.total_trades_today,
                'win_rate_today': self.win_rate_today,
                'total_pnl_today': self.total_pnl_today,
                'total_cost_today': self.total_cost_today
            },
            'agent_performance': self.agent_performance,
            'llm_usage_stats': self.llm_usage_stats,
            'trends': {
                'hourly': self.hourly_trends,
                'daily': self.daily_trends
            }
        }


class PerformanceMetricsCalculator:
    """실시간 성과 메트릭 계산기"""
    
    def __init__(self, db_manager=db_manager):
        self.db_manager = db_manager
        self._cache = {}
        self._cache_expire_time = timedelta(minutes=5)  # 5분 캐시
        
    def get_real_time_metrics(self, refresh_cache: bool = False) -> RealTimeMetrics:
        """실시간 성과 메트릭 계산"""
        cache_key = "real_time_metrics"
        current_time = datetime.now()
        
        # 캐시 확인
        if not refresh_cache and cache_key in self._cache:
            cached_data, cache_time = self._cache[cache_key]
            if current_time - cache_time < self._cache_expire_time:
                return cached_data
        
        # 새로운 메트릭 계산
        metrics = self._calculate_metrics()
        
        # 캐시 저장
        self._cache[cache_key] = (metrics, current_time)
        
        return metrics
    
    def _calculate_metrics(self) -> RealTimeMetrics:
        """실제 메트릭 계산 로직"""
        current_time = datetime.now()
        today_start = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # 1. 오늘의 전체 시스템 메트릭
        system_metrics = self._calculate_system_metrics_today(today_start, current_time)
        
        # 2. 에이전트별 성과
        agent_performance = self._calculate_agent_performance_today(today_start, current_time)
        
        # 3. LLM 사용량 통계
        llm_stats = self._calculate_llm_usage_today(today_start, current_time)
        
        # 4. 시간별 트렌드 (최근 24시간)
        hourly_trends = self._calculate_hourly_trends(current_time - timedelta(hours=24), current_time)
        
        # 5. 일별 트렌드 (최근 30일)
        daily_trends = self._calculate_daily_trends(current_time - timedelta(days=30), current_time)
        
        return RealTimeMetrics(
            timestamp=current_time.isoformat(),
            total_trades_today=system_metrics['total_trades'],
            win_rate_today=system_metrics['win_rate'],
            total_pnl_today=system_metrics['total_pnl'],
            total_cost_today=system_metrics['total_cost'],
            agent_performance=agent_performance,
            llm_usage_stats=llm_stats,
            hourly_trends=hourly_trends,
            daily_trends=daily_trends
        )
    
    def _calculate_system_metrics_today(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """오늘의 전체 시스템 메트릭 계산"""
        try:
            # 오늘의 거래들 조회
            trades = self.db_manager.get_trades_by_period(days=1)
            
            if not trades:
                return {
                    'total_trades': 0,
                    'win_rate': 0.0,
                    'total_pnl': 0.0,
                    'total_cost': 0.0
                }
            
            # 기본 통계 계산
            total_trades = len(trades)
            
            # P&L 계산 (7일 기준)
            completed_trades = [t for t in trades if t.get('pnl_7_days') is not None]
            
            if completed_trades:
                total_pnl = sum(t['pnl_7_days'] for t in completed_trades)
                winning_trades = sum(1 for t in completed_trades if t['pnl_7_days'] > 0)
                win_rate = (winning_trades / len(completed_trades)) * 100
            else:
                total_pnl = 0.0
                win_rate = 0.0
            
            # 오늘의 LLM 비용 계산
            llm_usage = self.db_manager.get_llm_usage_stats(days=1)
            total_cost = sum(
                provider_stats.get('total_cost', 0) 
                for provider_stats in llm_usage.get('provider_stats', {}).values()
            )
            
            return {
                'total_trades': total_trades,
                'win_rate': round(win_rate, 2),
                'total_pnl': round(total_pnl, 2),
                'total_cost': round(total_cost, 4)
            }
            
        except Exception as e:
            print(f"❌ 시스템 메트릭 계산 실패: {e}")
            return {'total_trades': 0, 'win_rate': 0.0, 'total_pnl': 0.0, 'total_cost': 0.0}
    
    def _calculate_agent_performance_today(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """에이전트별 오늘 성과 계산"""
        try:
            # 에이전트 기여도 분석 (오늘)
            contribution_analysis = self.db_manager.get_agent_contribution_analysis(days=1)
            
            if not contribution_analysis.get('agent_impact'):
                return {}
            
            agent_performance = {}
            
            for agent, impact_data in contribution_analysis['agent_impact'].items():
                # 각 에이전트의 핵심 지표 추출
                agent_performance[agent] = {
                    'efficiency_score': round(impact_data.get('efficiency_score', 0), 2),
                    'trades_involved': impact_data.get('trades_involved', 0),
                    'total_contribution': round(impact_data.get('total_contribution', 0), 2),
                    'positive_pnl': round(impact_data.get('positive_pnl_contribution', 0), 2),
                    'negative_pnl': round(impact_data.get('negative_pnl_contribution', 0), 2),
                    'avg_confidence': round(impact_data.get('avg_confidence', 0), 2)
                }
                
                # 성과 등급 계산
                efficiency = impact_data.get('efficiency_score', 0)
                if efficiency > 50:
                    grade = "A"
                elif efficiency > 20:
                    grade = "B"  
                elif efficiency > 0:
                    grade = "C"
                elif efficiency > -20:
                    grade = "D"
                else:
                    grade = "F"
                
                agent_performance[agent]['performance_grade'] = grade
            
            return agent_performance
            
        except Exception as e:
            print(f"❌ 에이전트 성과 계산 실패: {e}")
            return {}
    
    def _calculate_llm_usage_today(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """오늘의 LLM 사용량 통계"""
        try:
            usage_stats = self.db_manager.get_llm_usage_stats(days=1)
            
            # 제공사별 통계 정리
            provider_summary = {}
            for provider, stats in usage_stats.get('provider_stats', {}).items():
                provider_summary[provider] = {
                    'requests': stats.get('total_requests', 0),
                    'cost': round(stats.get('total_cost', 0), 4),
                    'tokens': stats.get('total_tokens', 0),
                    'success_rate': round(stats.get('success_rate', 0), 1),
                    'avg_response_time': round(stats.get('avg_response_time', 0), 0)
                }
            
            # 에이전트별 사용량 TOP 5
            agent_stats = usage_stats.get('agent_stats', {})
            top_agents = sorted(
                agent_stats.items(), 
                key=lambda x: x[1].get('total_cost', 0), 
                reverse=True
            )[:5]
            
            agent_summary = {}
            for agent, stats in top_agents:
                agent_summary[agent] = {
                    'requests': stats.get('total_requests', 0),
                    'cost': round(stats.get('total_cost', 0), 4),
                    'avg_response_time': round(stats.get('avg_response_time', 0), 0)
                }
            
            return {
                'providers': provider_summary,
                'top_agents': agent_summary,
                'total_requests': sum(p.get('requests', 0) for p in provider_summary.values()),
                'total_cost': sum(p.get('cost', 0) for p in provider_summary.values())
            }
            
        except Exception as e:
            print(f"❌ LLM 사용량 계산 실패: {e}")
            return {}
    
    def _calculate_hourly_trends(self, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        """시간별 트렌드 계산 (최근 24시간)"""
        try:
            trends = []
            current_hour = start_time.replace(minute=0, second=0, microsecond=0)
            
            while current_hour <= end_time:
                next_hour = current_hour + timedelta(hours=1)
                
                # 해당 시간대의 메트릭 계산
                hour_metrics = self._get_metrics_for_period(current_hour, next_hour)
                
                trends.append({
                    'timestamp': current_hour.isoformat(),
                    'hour': current_hour.hour,
                    'trades': hour_metrics.get('trades', 0),
                    'pnl': hour_metrics.get('pnl', 0),
                    'cost': hour_metrics.get('cost', 0)
                })
                
                current_hour = next_hour
            
            return trends[-24:]  # 최근 24시간만
            
        except Exception as e:
            print(f"❌ 시간별 트렌드 계산 실패: {e}")
            return []
    
    def _calculate_daily_trends(self, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        """일별 트렌드 계산 (최근 30일)"""
        try:
            # 시스템 메트릭에서 일별 데이터 조회
            daily_metrics = self.db_manager.get_system_metrics(days=30)
            
            trends = []
            for metric in daily_metrics:
                trends.append({
                    'date': metric['date'],
                    'trades': metric['total_trades'],
                    'win_rate': metric['win_rate'],
                    'pnl': metric['total_pnl'],
                    'cost': metric['total_cost_usd'],
                    'agent_efficiency': metric['agent_efficiency_score']
                })
            
            return sorted(trends, key=lambda x: x['date'])
            
        except Exception as e:
            print(f"❌ 일별 트렌드 계산 실패: {e}")
            return []
    
    def _get_metrics_for_period(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """특정 기간의 메트릭 계산"""
        # 실제 구현에서는 더 정교한 시간 기반 쿼리가 필요
        # 현재는 단순화된 버전
        return {
            'trades': 0,
            'pnl': 0.0,
            'cost': 0.0
        }
    
    def get_agent_ranking(self, period_days: int = 7) -> List[Dict[str, Any]]:
        """에이전트 성과 순위 (기간별)"""
        try:
            analysis = self.db_manager.get_agent_contribution_analysis(days=period_days)
            
            if not analysis.get('agent_impact'):
                return []
            
            # 효율성 점수 기준으로 정렬
            ranking = []
            for agent, impact in analysis['agent_impact'].items():
                ranking.append({
                    'agent': agent,
                    'efficiency_score': round(impact.get('efficiency_score', 0), 2),
                    'trades_count': impact.get('trades_involved', 0),
                    'total_pnl_contribution': round(
                        impact.get('positive_pnl_contribution', 0) - 
                        impact.get('negative_pnl_contribution', 0), 2
                    )
                })
            
            # 효율성 점수 내림차순 정렬
            ranking.sort(key=lambda x: x['efficiency_score'], reverse=True)
            
            # 순위 추가
            for i, agent_data in enumerate(ranking, 1):
                agent_data['rank'] = i
            
            return ranking
            
        except Exception as e:
            print(f"❌ 에이전트 순위 계산 실패: {e}")
            return []
    
    def get_cost_efficiency_analysis(self) -> Dict[str, Any]:
        """비용 효율성 분석"""
        try:
            # 최근 7일 데이터
            llm_stats = self.db_manager.get_llm_usage_stats(days=7)
            trades_stats = self.db_manager.get_trade_statistics()
            
            total_cost = sum(
                provider['total_cost'] 
                for provider in llm_stats.get('provider_stats', {}).values()
            )
            
            total_pnl = trades_stats.get('total_pnl_7d', 0)
            
            if total_cost > 0:
                roi = (total_pnl / total_cost) * 100
                cost_per_trade = total_cost / max(trades_stats.get('total_trades', 1), 1)
            else:
                roi = 0
                cost_per_trade = 0
            
            return {
                'total_cost_7d': round(total_cost, 4),
                'total_pnl_7d': round(total_pnl, 2),
                'roi_percentage': round(roi, 1),
                'cost_per_trade': round(cost_per_trade, 4),
                'break_even_trades_needed': max(0, int(-total_pnl / cost_per_trade)) if cost_per_trade > 0 and total_pnl < 0 else 0
            }
            
        except Exception as e:
            print(f"❌ 비용 효율성 분석 실패: {e}")
            return {}
    
    def clear_cache(self):
        """캐시 초기화"""
        self._cache.clear()
        print("📊 성과 메트릭 캐시 초기화됨")