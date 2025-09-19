#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
실시간 성과 대시보드 데이터 파이프라인
데이터 수집, 집계, 캐싱, 배포를 담당하는 중앙 파이프라인
"""

import json
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
import schedule
from pathlib import Path

from .performance_metrics import PerformanceMetricsCalculator, RealTimeMetrics
from ..database.schema import db_manager


@dataclass
class PipelineConfig:
    """파이프라인 설정"""
    update_interval_seconds: int = 300  # 5분마다 업데이트
    cache_duration_minutes: int = 5     # 5분 캐시
    enable_real_time_updates: bool = True
    export_to_file: bool = True
    export_directory: str = "data/dashboard_cache"
    max_cache_files: int = 100


class DashboardDataPipeline:
    """실시간 대시보드 데이터 파이프라인"""
    
    def __init__(self, config: Optional[PipelineConfig] = None):
        self.config = config or PipelineConfig()
        self.metrics_calculator = PerformanceMetricsCalculator()
        
        # 내부 상태
        self._is_running = False
        self._update_thread = None
        self._subscribers: List[Callable[[RealTimeMetrics], None]] = []
        self._latest_metrics: Optional[RealTimeMetrics] = None
        
        # 캐시 디렉토리 생성
        self.cache_dir = Path(self.config.export_directory)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"📊 대시보드 파이프라인 초기화 완료")
        print(f"   - 업데이트 주기: {self.config.update_interval_seconds}초")
        print(f"   - 캐시 디렉토리: {self.cache_dir}")
    
    def start(self):
        """파이프라인 시작"""
        if self._is_running:
            print("⚠️  파이프라인이 이미 실행 중입니다")
            return
        
        print("🚀 대시보드 데이터 파이프라인 시작")
        
        self._is_running = True
        
        # 초기 메트릭 계산
        self._update_metrics()
        
        if self.config.enable_real_time_updates:
            # 백그라운드 업데이트 스레드 시작
            self._update_thread = threading.Thread(target=self._run_update_loop, daemon=True)
            self._update_thread.start()
            
            # 스케줄러 설정
            schedule.every(self.config.update_interval_seconds).seconds.do(self._update_metrics)
            
        print("✅ 파이프라인 시작됨")
    
    def stop(self):
        """파이프라인 중지"""
        if not self._is_running:
            return
        
        print("🛑 대시보드 데이터 파이프라인 중지")
        self._is_running = False
        
        if self._update_thread:
            self._update_thread.join(timeout=5)
        
        schedule.clear()
        print("✅ 파이프라인 중지됨")
    
    def _run_update_loop(self):
        """백그라운드 업데이트 루프"""
        while self._is_running:
            try:
                schedule.run_pending()
                time.sleep(1)
            except Exception as e:
                print(f"❌ 업데이트 루프 오류: {e}")
                time.sleep(5)  # 오류 발생 시 5초 대기
    
    def _update_metrics(self):
        """메트릭 업데이트"""
        try:
            start_time = time.time()
            
            # 새로운 메트릭 계산
            metrics = self.metrics_calculator.get_real_time_metrics(refresh_cache=True)
            self._latest_metrics = metrics
            
            # 파일로 export (설정된 경우)
            if self.config.export_to_file:
                self._export_to_file(metrics)
            
            # 구독자들에게 알림
            self._notify_subscribers(metrics)
            
            duration = time.time() - start_time
            print(f"📊 메트릭 업데이트 완료 ({duration:.2f}초)")
            
        except Exception as e:
            print(f"❌ 메트릭 업데이트 실패: {e}")
    
    def _export_to_file(self, metrics: RealTimeMetrics):
        """메트릭을 파일로 export"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"dashboard_metrics_{timestamp}.json"
            filepath = self.cache_dir / filename
            
            # JSON 파일 저장
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(metrics.to_dict(), f, ensure_ascii=False, indent=2)
            
            # 최신 파일에 대한 심볼릭 링크 생성
            latest_filepath = self.cache_dir / "latest_metrics.json"
            if latest_filepath.exists():
                latest_filepath.unlink()
            
            with open(latest_filepath, 'w', encoding='utf-8') as f:
                json.dump(metrics.to_dict(), f, ensure_ascii=False, indent=2)
            
            # 오래된 캐시 파일 정리
            self._cleanup_old_cache_files()
            
        except Exception as e:
            print(f"❌ 파일 export 실패: {e}")
    
    def _cleanup_old_cache_files(self):
        """오래된 캐시 파일 정리"""
        try:
            cache_files = list(self.cache_dir.glob("dashboard_metrics_*.json"))
            cache_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # 최대 개수 초과 시 오래된 파일 삭제
            if len(cache_files) > self.config.max_cache_files:
                for old_file in cache_files[self.config.max_cache_files:]:
                    old_file.unlink()
                    
        except Exception as e:
            print(f"❌ 캐시 파일 정리 실패: {e}")
    
    def subscribe(self, callback: Callable[[RealTimeMetrics], None]):
        """메트릭 업데이트 구독"""
        self._subscribers.append(callback)
        print(f"📡 구독자 추가됨 (총 {len(self._subscribers)}명)")
        
        # 최신 메트릭이 있으면 즉시 전송
        if self._latest_metrics:
            try:
                callback(self._latest_metrics)
            except Exception as e:
                print(f"❌ 구독자 알림 실패: {e}")
    
    def unsubscribe(self, callback: Callable[[RealTimeMetrics], None]):
        """구독 해제"""
        if callback in self._subscribers:
            self._subscribers.remove(callback)
            print(f"📡 구독자 제거됨 (총 {len(self._subscribers)}명)")
    
    def _notify_subscribers(self, metrics: RealTimeMetrics):
        """구독자들에게 알림"""
        for callback in self._subscribers[:]:  # 복사본으로 순회
            try:
                callback(metrics)
            except Exception as e:
                print(f"❌ 구독자 알림 실패: {e}")
                # 실패한 구독자 제거
                self._subscribers.remove(callback)
    
    def get_latest_metrics(self) -> Optional[RealTimeMetrics]:
        """최신 메트릭 조회"""
        return self._latest_metrics
    
    def force_update(self):
        """강제 업데이트"""
        print("🔄 강제 메트릭 업데이트 실행")
        self._update_metrics()
    
    def get_cached_metrics(self, hours_back: int = 24) -> List[Dict[str, Any]]:
        """캐시된 메트릭 히스토리 조회"""
        try:
            cached_metrics = []
            cutoff_time = datetime.now() - timedelta(hours=hours_back)
            
            cache_files = list(self.cache_dir.glob("dashboard_metrics_*.json"))
            cache_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            for cache_file in cache_files:
                file_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
                if file_time >= cutoff_time:
                    try:
                        with open(cache_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            cached_metrics.append(data)
                    except Exception as e:
                        print(f"⚠️  캐시 파일 읽기 실패 {cache_file}: {e}")
            
            return sorted(cached_metrics, key=lambda x: x.get('timestamp', ''))
            
        except Exception as e:
            print(f"❌ 캐시된 메트릭 조회 실패: {e}")
            return []
    
    def get_health_status(self) -> Dict[str, Any]:
        """파이프라인 상태 정보"""
        return {
            'is_running': self._is_running,
            'subscribers_count': len(self._subscribers),
            'last_update': self._latest_metrics.timestamp if self._latest_metrics else None,
            'config': {
                'update_interval': self.config.update_interval_seconds,
                'cache_duration': self.config.cache_duration_minutes,
                'real_time_updates': self.config.enable_real_time_updates
            },
            'cache_directory': str(self.cache_dir),
            'cache_files_count': len(list(self.cache_dir.glob("dashboard_metrics_*.json")))
        }
    
    def export_current_snapshot(self, filename: Optional[str] = None) -> str:
        """현재 상태의 스냅샷 export"""
        if not self._latest_metrics:
            self.force_update()
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"dashboard_snapshot_{timestamp}.json"
        
        filepath = self.cache_dir / filename
        
        snapshot_data = {
            'export_timestamp': datetime.now().isoformat(),
            'pipeline_status': self.get_health_status(),
            'metrics': self._latest_metrics.to_dict() if self._latest_metrics else None,
            'additional_analytics': {
                'agent_ranking': self.metrics_calculator.get_agent_ranking(period_days=7),
                'cost_efficiency': self.metrics_calculator.get_cost_efficiency_analysis()
            }
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(snapshot_data, f, ensure_ascii=False, indent=2)
        
        print(f"📸 스냅샷 저장: {filepath}")
        return str(filepath)


# 전역 파이프라인 인스턴스 (싱글톤)
_global_pipeline: Optional[DashboardDataPipeline] = None

def get_dashboard_pipeline() -> DashboardDataPipeline:
    """전역 파이프라인 인스턴스 반환"""
    global _global_pipeline
    if _global_pipeline is None:
        _global_pipeline = DashboardDataPipeline()
    return _global_pipeline

def start_dashboard_pipeline(config: Optional[PipelineConfig] = None):
    """전역 파이프라인 시작"""
    global _global_pipeline
    if config:
        _global_pipeline = DashboardDataPipeline(config)
    else:
        _global_pipeline = get_dashboard_pipeline()
    
    _global_pipeline.start()
    return _global_pipeline

def stop_dashboard_pipeline():
    """전역 파이프라인 중지"""
    global _global_pipeline
    if _global_pipeline:
        _global_pipeline.stop()