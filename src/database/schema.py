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
            'pnl_30_days': self.pnl_30_days
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
            
            # 거래 기록 테이블
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
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 성능 최적화를 위한 인덱스 생성
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_trades_timestamp ON trades(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_trades_ticker ON trades(ticker)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_trades_action ON trades(action)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_trades_pnl_7_days ON trades(pnl_7_days)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_trades_pnl_30_days ON trades(pnl_30_days)')
            
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
                        pnl_7_days, pnl_30_days
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    trade_dict['pnl_30_days']
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


# 데이터베이스 매니저 싱글톤 인스턴스
db_manager = DatabaseManager()