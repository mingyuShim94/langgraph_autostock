#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 트레이딩 시스템 데이터베이스 스키마 정의

거래 기록을 저장하고 성찰 그래프의 학습 소스로 활용되는 중앙 데이터베이스
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path
from enum import Enum


@dataclass
class TradeRecord:
    """거래 기록 데이터 클래스"""
    trade_id: str
    timestamp: str
    ticker: str
    action: str  # 'buy' or 'sell'
    quantity: int
    price: float
    justification_text: str  # AI 의사결정 근거
    market_snapshot: Dict[str, Any]  # 거래 당시 시장 상황
    portfolio_before: Dict[str, Any]  # 거래 전 포트폴리오
    pnl_7_days: Optional[float] = None  # 7일 후 손익
    pnl_30_days: Optional[float] = None  # 30일 후 손익
    # Phase 3 확장 필드들
    agent_contributions: Optional[Dict[str, float]] = None  # 에이전트별 기여도 (0-1)
    decision_confidence: Optional[float] = None  # CIO 최종 결정 신뢰도
    analysis_metadata: Optional[Dict[str, Any]] = None  # 분석 과정 메타데이터
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'trade_id': self.trade_id,
            'timestamp': self.timestamp,
            'ticker': self.ticker,
            'action': self.action,
            'quantity': self.quantity,
            'price': self.price,
            'justification_text': self.justification_text,
            'market_snapshot': json.dumps(self.market_snapshot, ensure_ascii=False),
            'portfolio_before': json.dumps(self.portfolio_before, ensure_ascii=False),
            'pnl_7_days': self.pnl_7_days,
            'pnl_30_days': self.pnl_30_days,
            'agent_contributions': json.dumps(self.agent_contributions, ensure_ascii=False) if self.agent_contributions else None,
            'decision_confidence': self.decision_confidence,
            'analysis_metadata': json.dumps(self.analysis_metadata, ensure_ascii=False) if self.analysis_metadata else None
        }


@dataclass
class AgentPerformance:
    """에이전트별 성과 기록 데이터 클래스"""
    agent_name: str
    period_start: str
    period_end: str
    total_decisions: int
    successful_decisions: int
    avg_contribution_score: float
    performance_rating: float  # 0-100 점수
    wins: int
    losses: int
    total_pnl_attributed: float
    confidence_accuracy: float  # 신뢰도와 실제 결과 간 상관관계
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'agent_name': self.agent_name,
            'period_start': self.period_start,
            'period_end': self.period_end,
            'total_decisions': self.total_decisions,
            'successful_decisions': self.successful_decisions,
            'avg_contribution_score': self.avg_contribution_score,
            'performance_rating': self.performance_rating,
            'wins': self.wins,
            'losses': self.losses,
            'total_pnl_attributed': self.total_pnl_attributed,
            'confidence_accuracy': self.confidence_accuracy
        }


@dataclass
class LLMUsageLog:
    """LLM 사용량 로그 데이터 클래스"""
    timestamp: str
    agent_name: str
    provider: str  # claude, gpt, gemini, perplexity
    model: str
    tokens_used: int
    cost_usd: float
    response_time_ms: float
    request_type: str  # analysis, decision, reflection 등
    success: bool
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'timestamp': self.timestamp,
            'agent_name': self.agent_name,
            'provider': self.provider,
            'model': self.model,
            'tokens_used': self.tokens_used,
            'cost_usd': self.cost_usd,
            'response_time_ms': self.response_time_ms,
            'request_type': self.request_type,
            'success': self.success,
            'error_message': self.error_message
        }


@dataclass
class ModelEvolutionHistory:
    """모델 교체 이력 데이터 클래스"""
    timestamp: str
    agent_name: str
    old_provider: str
    old_model: str
    new_provider: str
    new_model: str
    reason: str
    performance_improvement: float  # 예상 개선도 (-1 to 1)
    triggered_by: str  # 'automatic', 'manual', 'scheduled'
    validation_period_days: int = 7
    rollback_threshold: float = -0.1  # 성과 악화 시 롤백 기준
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'timestamp': self.timestamp,
            'agent_name': self.agent_name,
            'old_provider': self.old_provider,
            'old_model': self.old_model,
            'new_provider': self.new_provider,
            'new_model': self.new_model,
            'reason': self.reason,
            'performance_improvement': self.performance_improvement,
            'triggered_by': self.triggered_by,
            'validation_period_days': self.validation_period_days,
            'rollback_threshold': self.rollback_threshold
        }


@dataclass
class SystemMetrics:
    """시스템 전체 성과 지표 데이터 클래스"""
    date: str
    total_trades: int
    win_rate: float
    total_pnl: float
    total_cost_usd: float  # LLM 사용 비용
    avg_decision_time_seconds: float
    agent_efficiency_score: float  # 전체 에이전트 팀 효율성
    model_diversity_index: float  # 사용 중인 모델의 다양성 지수
    auto_improvements: int  # 자동 개선 횟수
    human_interventions: int  # 인간 개입 필요 횟수
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'date': self.date,
            'total_trades': self.total_trades,
            'win_rate': self.win_rate,
            'total_pnl': self.total_pnl,
            'total_cost_usd': self.total_cost_usd,
            'avg_decision_time_seconds': self.avg_decision_time_seconds,
            'agent_efficiency_score': self.agent_efficiency_score,
            'model_diversity_index': self.model_diversity_index,
            'auto_improvements': self.auto_improvements,
            'human_interventions': self.human_interventions
        }


class DatabaseManager:
    """트레이딩 데이터베이스 관리 클래스"""
    
    def __init__(self, db_path: str = "data/trading_records.db"):
        """
        데이터베이스 매니저 초기화
        
        Args:
            db_path: 데이터베이스 파일 경로
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._create_tables()
    
    def _create_tables(self):
        """데이터베이스 테이블 생성"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 스키마 버전 테이블 (마이그레이션 관리용)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER PRIMARY KEY,
                    applied_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    description TEXT
                )
            ''')
            
            # 거래 기록 테이블 (확장됨)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trades (
                    trade_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    ticker TEXT NOT NULL,
                    action TEXT NOT NULL CHECK (action IN ('buy', 'sell')),
                    quantity INTEGER NOT NULL,
                    price REAL NOT NULL,
                    justification_text TEXT NOT NULL,
                    market_snapshot TEXT NOT NULL,  -- JSON 형태
                    portfolio_before TEXT NOT NULL,  -- JSON 형태
                    pnl_7_days REAL,
                    pnl_30_days REAL,
                    agent_contributions TEXT,  -- JSON 형태, 에이전트별 기여도
                    decision_confidence REAL,  -- CIO 최종 결정 신뢰도
                    analysis_metadata TEXT,  -- JSON 형태, 분석 과정 메타데이터
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 에이전트 성과 테이블
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS agent_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_name TEXT NOT NULL,
                    period_start TEXT NOT NULL,
                    period_end TEXT NOT NULL,
                    total_decisions INTEGER NOT NULL,
                    successful_decisions INTEGER NOT NULL,
                    avg_contribution_score REAL NOT NULL,
                    performance_rating REAL NOT NULL,
                    wins INTEGER NOT NULL,
                    losses INTEGER NOT NULL,
                    total_pnl_attributed REAL NOT NULL,
                    confidence_accuracy REAL NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(agent_name, period_start, period_end)
                )
            ''')
            
            # LLM 사용량 로그 테이블
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS llm_usage_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    agent_name TEXT NOT NULL,
                    provider TEXT NOT NULL CHECK (provider IN ('claude', 'gpt', 'gemini', 'perplexity')),
                    model TEXT NOT NULL,
                    tokens_used INTEGER NOT NULL,
                    cost_usd REAL NOT NULL,
                    response_time_ms REAL NOT NULL,
                    request_type TEXT NOT NULL,
                    success BOOLEAN NOT NULL,
                    error_message TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 모델 진화 이력 테이블
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS model_evolution_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    agent_name TEXT NOT NULL,
                    old_provider TEXT NOT NULL,
                    old_model TEXT NOT NULL,
                    new_provider TEXT NOT NULL,
                    new_model TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    performance_improvement REAL NOT NULL,
                    triggered_by TEXT NOT NULL CHECK (triggered_by IN ('automatic', 'manual', 'scheduled')),
                    validation_period_days INTEGER DEFAULT 7,
                    rollback_threshold REAL DEFAULT -0.1,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 시스템 성과 지표 테이블
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL UNIQUE,
                    total_trades INTEGER NOT NULL,
                    win_rate REAL NOT NULL,
                    total_pnl REAL NOT NULL,
                    total_cost_usd REAL NOT NULL,
                    avg_decision_time_seconds REAL NOT NULL,
                    agent_efficiency_score REAL NOT NULL,
                    model_diversity_index REAL NOT NULL,
                    auto_improvements INTEGER NOT NULL,
                    human_interventions INTEGER NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 기존 인덱스들
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_trades_timestamp ON trades(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_trades_ticker ON trades(ticker)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_trades_action ON trades(action)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_trades_pnl_7_days ON trades(pnl_7_days)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_trades_pnl_30_days ON trades(pnl_30_days)')
            
            # 새로운 인덱스들
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_agent_performance_agent ON agent_performance(agent_name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_agent_performance_period ON agent_performance(period_start, period_end)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_llm_usage_agent ON llm_usage_log(agent_name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_llm_usage_provider ON llm_usage_log(provider)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_llm_usage_timestamp ON llm_usage_log(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_model_evolution_agent ON model_evolution_history(agent_name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_model_evolution_timestamp ON model_evolution_history(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_system_metrics_date ON system_metrics(date)')
            
            # 현재 스키마 버전 기록
            cursor.execute('INSERT OR IGNORE INTO schema_version (version, description) VALUES (1, "Initial Phase 3 schema with agent performance tracking")')
            
            conn.commit()
    
    def insert_trade(self, trade_record: TradeRecord) -> bool:
        """
        거래 기록 삽입
        
        Args:
            trade_record: 거래 기록 객체
            
        Returns:
            bool: 삽입 성공 여부
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                trade_dict = trade_record.to_dict()
                
                cursor.execute('''
                    INSERT INTO trades (
                        trade_id, timestamp, ticker, action, quantity, price,
                        justification_text, market_snapshot, portfolio_before,
                        pnl_7_days, pnl_30_days, agent_contributions, 
                        decision_confidence, analysis_metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    trade_dict['trade_id'],
                    trade_dict['timestamp'],
                    trade_dict['ticker'],
                    trade_dict['action'],
                    trade_dict['quantity'],
                    trade_dict['price'],
                    trade_dict['justification_text'],
                    trade_dict['market_snapshot'],
                    trade_dict['portfolio_before'],
                    trade_dict['pnl_7_days'],
                    trade_dict['pnl_30_days'],
                    trade_dict['agent_contributions'],
                    trade_dict['decision_confidence'],
                    trade_dict['analysis_metadata']
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            print(f"❌ 거래 기록 삽입 실패: {e}")
            return False
    
    def get_trades_by_period(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        기간별 거래 기록 조회
        
        Args:
            days: 조회할 일수 (기본 30일)
            
        Returns:
            List[Dict]: 거래 기록 리스트
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM trades 
                    WHERE datetime(timestamp) >= datetime('now', '-{} days')
                    ORDER BY timestamp DESC
                '''.format(days))
                
                columns = [desc[0] for desc in cursor.description]
                trades = []
                
                for row in cursor.fetchall():
                    trade = dict(zip(columns, row))
                    # JSON 필드 파싱
                    trade['market_snapshot'] = json.loads(trade['market_snapshot'])
                    trade['portfolio_before'] = json.loads(trade['portfolio_before'])
                    if trade['agent_contributions']:
                        trade['agent_contributions'] = json.loads(trade['agent_contributions'])
                    if trade['analysis_metadata']:
                        trade['analysis_metadata'] = json.loads(trade['analysis_metadata'])
                    trades.append(trade)
                
                return trades
                
        except Exception as e:
            print(f"❌ 거래 기록 조회 실패: {e}")
            return []
    
    def get_worst_trades(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        손실이 큰 거래 조회 (성찰 그래프용)
        
        Args:
            limit: 조회할 최대 개수
            
        Returns:
            List[Dict]: 손실 거래 리스트
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM trades 
                    WHERE pnl_7_days IS NOT NULL AND pnl_7_days < 0
                    ORDER BY pnl_7_days ASC
                    LIMIT ?
                ''', (limit,))
                
                columns = [desc[0] for desc in cursor.description]
                trades = []
                
                for row in cursor.fetchall():
                    trade = dict(zip(columns, row))
                    # JSON 필드 파싱
                    trade['market_snapshot'] = json.loads(trade['market_snapshot'])
                    trade['portfolio_before'] = json.loads(trade['portfolio_before'])
                    trades.append(trade)
                
                return trades
                
        except Exception as e:
            print(f"❌ 손실 거래 조회 실패: {e}")
            return []
    
    def update_pnl(self, trade_id: str, pnl_7_days: float = None, pnl_30_days: float = None) -> bool:
        """
        거래의 손익 정보 업데이트
        
        Args:
            trade_id: 거래 ID
            pnl_7_days: 7일 후 손익
            pnl_30_days: 30일 후 손익
            
        Returns:
            bool: 업데이트 성공 여부
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if pnl_7_days is not None:
                    cursor.execute('''
                        UPDATE trades 
                        SET pnl_7_days = ?
                        WHERE trade_id = ?
                    ''', (pnl_7_days, trade_id))
                
                if pnl_30_days is not None:
                    cursor.execute('''
                        UPDATE trades 
                        SET pnl_30_days = ?
                        WHERE trade_id = ?
                    ''', (pnl_30_days, trade_id))
                
                conn.commit()
                return True
                
        except Exception as e:
            print(f"❌ 손익 업데이트 실패: {e}")
            return False
    
    def get_trade_statistics(self) -> Dict[str, Any]:
        """
        거래 통계 조회
        
        Returns:
            Dict: 거래 통계 정보
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 기본 통계
                cursor.execute('SELECT COUNT(*) FROM trades')
                total_trades = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM trades WHERE action = "buy"')
                buy_trades = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM trades WHERE action = "sell"')
                sell_trades = cursor.fetchone()[0]
                
                # 손익 통계 (7일 기준)
                cursor.execute('''
                    SELECT 
                        AVG(pnl_7_days) as avg_pnl,
                        SUM(pnl_7_days) as total_pnl,
                        COUNT(CASE WHEN pnl_7_days > 0 THEN 1 END) as winning_trades,
                        COUNT(CASE WHEN pnl_7_days < 0 THEN 1 END) as losing_trades
                    FROM trades 
                    WHERE pnl_7_days IS NOT NULL
                ''')
                
                pnl_stats = cursor.fetchone()
                
                return {
                    'total_trades': total_trades,
                    'buy_trades': buy_trades,
                    'sell_trades': sell_trades,
                    'avg_pnl_7d': pnl_stats[0] if pnl_stats[0] else 0,
                    'total_pnl_7d': pnl_stats[1] if pnl_stats[1] else 0,
                    'winning_trades': pnl_stats[2] if pnl_stats[2] else 0,
                    'losing_trades': pnl_stats[3] if pnl_stats[3] else 0,
                    'win_rate': (pnl_stats[2] / (pnl_stats[2] + pnl_stats[3])) * 100 
                               if (pnl_stats[2] and pnl_stats[3]) else 0
                }
                
        except Exception as e:
            print(f"❌ 거래 통계 조회 실패: {e}")
            return {}
    
    # =============================================================================
    # 에이전트 성과 관련 메서드들
    # =============================================================================
    
    def insert_agent_performance(self, performance: AgentPerformance) -> bool:
        """에이전트 성과 기록 삽입"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                perf_dict = performance.to_dict()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO agent_performance (
                        agent_name, period_start, period_end, total_decisions,
                        successful_decisions, avg_contribution_score, performance_rating,
                        wins, losses, total_pnl_attributed, confidence_accuracy
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    perf_dict['agent_name'],
                    perf_dict['period_start'],
                    perf_dict['period_end'],
                    perf_dict['total_decisions'],
                    perf_dict['successful_decisions'],
                    perf_dict['avg_contribution_score'],
                    perf_dict['performance_rating'],
                    perf_dict['wins'],
                    perf_dict['losses'],
                    perf_dict['total_pnl_attributed'],
                    perf_dict['confidence_accuracy']
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            print(f"❌ 에이전트 성과 기록 삽입 실패: {e}")
            return False
    
    def get_agent_performance(self, agent_name: str = None, days: int = 30) -> List[Dict[str, Any]]:
        """에이전트 성과 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if agent_name:
                    cursor.execute('''
                        SELECT * FROM agent_performance 
                        WHERE agent_name = ? 
                        AND datetime(period_end) >= datetime('now', '-{} days')
                        ORDER BY period_end DESC
                    '''.format(days), (agent_name,))
                else:
                    cursor.execute('''
                        SELECT * FROM agent_performance 
                        WHERE datetime(period_end) >= datetime('now', '-{} days')
                        ORDER BY performance_rating DESC
                    '''.format(days))
                
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
                
        except Exception as e:
            print(f"❌ 에이전트 성과 조회 실패: {e}")
            return []
    
    # =============================================================================
    # LLM 사용량 관련 메서드들
    # =============================================================================
    
    def log_llm_usage(self, usage_log: LLMUsageLog) -> bool:
        """LLM 사용량 로그 기록"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                log_dict = usage_log.to_dict()
                
                cursor.execute('''
                    INSERT INTO llm_usage_log (
                        timestamp, agent_name, provider, model, tokens_used,
                        cost_usd, response_time_ms, request_type, success, error_message
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    log_dict['timestamp'],
                    log_dict['agent_name'],
                    log_dict['provider'],
                    log_dict['model'],
                    log_dict['tokens_used'],
                    log_dict['cost_usd'],
                    log_dict['response_time_ms'],
                    log_dict['request_type'],
                    log_dict['success'],
                    log_dict['error_message']
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            print(f"❌ LLM 사용량 로그 기록 실패: {e}")
            return False
    
    def get_llm_usage_stats(self, days: int = 7) -> Dict[str, Any]:
        """LLM 사용량 통계 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 전체 통계
                cursor.execute('''
                    SELECT 
                        provider,
                        COUNT(*) as total_requests,
                        SUM(tokens_used) as total_tokens,
                        SUM(cost_usd) as total_cost,
                        AVG(response_time_ms) as avg_response_time,
                        SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_requests
                    FROM llm_usage_log 
                    WHERE datetime(timestamp) >= datetime('now', '-{} days')
                    GROUP BY provider
                '''.format(days))
                
                provider_stats = {}
                for row in cursor.fetchall():
                    provider_stats[row[0]] = {
                        'total_requests': row[1],
                        'total_tokens': row[2],
                        'total_cost': row[3],
                        'avg_response_time': row[4],
                        'successful_requests': row[5],
                        'success_rate': (row[5] / row[1]) * 100 if row[1] > 0 else 0
                    }
                
                # 에이전트별 통계
                cursor.execute('''
                    SELECT 
                        agent_name,
                        COUNT(*) as total_requests,
                        SUM(cost_usd) as total_cost,
                        AVG(response_time_ms) as avg_response_time
                    FROM llm_usage_log 
                    WHERE datetime(timestamp) >= datetime('now', '-{} days')
                    GROUP BY agent_name
                    ORDER BY total_cost DESC
                '''.format(days))
                
                agent_stats = {}
                for row in cursor.fetchall():
                    agent_stats[row[0]] = {
                        'total_requests': row[1],
                        'total_cost': row[2],
                        'avg_response_time': row[3]
                    }
                
                return {
                    'provider_stats': provider_stats,
                    'agent_stats': agent_stats
                }
                
        except Exception as e:
            print(f"❌ LLM 사용량 통계 조회 실패: {e}")
            return {}
    
    # =============================================================================
    # 모델 진화 관련 메서드들
    # =============================================================================
    
    def log_model_evolution(self, evolution: ModelEvolutionHistory) -> bool:
        """모델 교체 이력 기록"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                evo_dict = evolution.to_dict()
                
                cursor.execute('''
                    INSERT INTO model_evolution_history (
                        timestamp, agent_name, old_provider, old_model,
                        new_provider, new_model, reason, performance_improvement,
                        triggered_by, validation_period_days, rollback_threshold
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    evo_dict['timestamp'],
                    evo_dict['agent_name'],
                    evo_dict['old_provider'],
                    evo_dict['old_model'],
                    evo_dict['new_provider'],
                    evo_dict['new_model'],
                    evo_dict['reason'],
                    evo_dict['performance_improvement'],
                    evo_dict['triggered_by'],
                    evo_dict['validation_period_days'],
                    evo_dict['rollback_threshold']
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            print(f"❌ 모델 진화 이력 기록 실패: {e}")
            return False
    
    def get_model_evolution_history(self, agent_name: str = None) -> List[Dict[str, Any]]:
        """모델 교체 이력 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if agent_name:
                    cursor.execute('''
                        SELECT * FROM model_evolution_history 
                        WHERE agent_name = ?
                        ORDER BY timestamp DESC
                    ''', (agent_name,))
                else:
                    cursor.execute('''
                        SELECT * FROM model_evolution_history 
                        ORDER BY timestamp DESC
                    ''')
                
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
                
        except Exception as e:
            print(f"❌ 모델 진화 이력 조회 실패: {e}")
            return []
    
    # =============================================================================
    # 시스템 메트릭 관련 메서드들
    # =============================================================================
    
    def insert_system_metrics(self, metrics: SystemMetrics) -> bool:
        """시스템 성과 지표 기록"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                metrics_dict = metrics.to_dict()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO system_metrics (
                        date, total_trades, win_rate, total_pnl, total_cost_usd,
                        avg_decision_time_seconds, agent_efficiency_score,
                        model_diversity_index, auto_improvements, human_interventions
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    metrics_dict['date'],
                    metrics_dict['total_trades'],
                    metrics_dict['win_rate'],
                    metrics_dict['total_pnl'],
                    metrics_dict['total_cost_usd'],
                    metrics_dict['avg_decision_time_seconds'],
                    metrics_dict['agent_efficiency_score'],
                    metrics_dict['model_diversity_index'],
                    metrics_dict['auto_improvements'],
                    metrics_dict['human_interventions']
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            print(f"❌ 시스템 메트릭 기록 실패: {e}")
            return False
    
    def get_system_metrics(self, days: int = 30) -> List[Dict[str, Any]]:
        """시스템 성과 지표 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM system_metrics 
                    WHERE datetime(date) >= datetime('now', '-{} days')
                    ORDER BY date DESC
                '''.format(days))
                
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
                
        except Exception as e:
            print(f"❌ 시스템 메트릭 조회 실패: {e}")
            return []
    
    # =============================================================================
    # 분석 및 성찰 그래프용 메서드들
    # =============================================================================
    
    def get_agent_contribution_analysis(self, days: int = 30) -> Dict[str, Any]:
        """에이전트 기여도 분석 (성찰 그래프용)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT 
                        agent_contributions,
                        pnl_7_days,
                        decision_confidence
                    FROM trades 
                    WHERE agent_contributions IS NOT NULL 
                    AND pnl_7_days IS NOT NULL
                    AND datetime(timestamp) >= datetime('now', '-{} days')
                '''.format(days))
                
                agent_impact = {}
                total_trades = 0
                
                for row in cursor.fetchall():
                    if row[0]:  # agent_contributions가 존재하는 경우
                        contributions = json.loads(row[0])
                        pnl = row[1]
                        confidence = row[2]
                        
                        for agent, contribution in contributions.items():
                            if agent not in agent_impact:
                                agent_impact[agent] = {
                                    'total_contribution': 0,
                                    'positive_pnl_contribution': 0,
                                    'negative_pnl_contribution': 0,
                                    'trades_involved': 0,
                                    'avg_confidence_when_involved': []
                                }
                            
                            agent_impact[agent]['total_contribution'] += contribution
                            agent_impact[agent]['trades_involved'] += 1
                            
                            if confidence:
                                agent_impact[agent]['avg_confidence_when_involved'].append(confidence)
                            
                            if pnl > 0:
                                agent_impact[agent]['positive_pnl_contribution'] += contribution * pnl
                            else:
                                agent_impact[agent]['negative_pnl_contribution'] += contribution * abs(pnl)
                        
                        total_trades += 1
                
                # 평균 계산
                for agent in agent_impact:
                    if agent_impact[agent]['avg_confidence_when_involved']:
                        agent_impact[agent]['avg_confidence'] = sum(agent_impact[agent]['avg_confidence_when_involved']) / len(agent_impact[agent]['avg_confidence_when_involved'])
                    else:
                        agent_impact[agent]['avg_confidence'] = 0
                    
                    del agent_impact[agent]['avg_confidence_when_involved']
                    
                    # 에이전트 효율성 스코어 계산
                    if agent_impact[agent]['trades_involved'] > 0:
                        agent_impact[agent]['efficiency_score'] = (
                            agent_impact[agent]['positive_pnl_contribution'] - 
                            agent_impact[agent]['negative_pnl_contribution']
                        ) / agent_impact[agent]['trades_involved']
                    else:
                        agent_impact[agent]['efficiency_score'] = 0
                
                return {
                    'agent_impact': agent_impact,
                    'total_trades_analyzed': total_trades,
                    'analysis_period_days': days
                }
                
        except Exception as e:
            print(f"❌ 에이전트 기여도 분석 실패: {e}")
            return {}
    
    def get_underperforming_agents(self, min_trades: int = 10) -> List[Dict[str, Any]]:
        """성과가 낮은 에이전트 식별 (자기 개조용)"""
        try:
            analysis = self.get_agent_contribution_analysis()
            
            underperforming = []
            
            for agent, stats in analysis.get('agent_impact', {}).items():
                if stats['trades_involved'] >= min_trades:
                    if stats['efficiency_score'] < -0.1:  # 손실 기여도가 높음
                        underperforming.append({
                            'agent_name': agent,
                            'efficiency_score': stats['efficiency_score'],
                            'trades_involved': stats['trades_involved'],
                            'negative_contribution': stats['negative_pnl_contribution'],
                            'avg_confidence': stats['avg_confidence']
                        })
            
            # 효율성 점수 기준으로 정렬 (낮은 순)
            underperforming.sort(key=lambda x: x['efficiency_score'])
            
            return underperforming
            
        except Exception as e:
            print(f"❌ 저성과 에이전트 식별 실패: {e}")
            return []


# 데이터베이스 매니저 싱글톤 인스턴스
db_manager = DatabaseManager()