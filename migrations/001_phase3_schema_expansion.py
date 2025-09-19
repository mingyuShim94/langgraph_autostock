#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 3 데이터베이스 스키마 확장 마이그레이션
v1.0 -> v1.1: 에이전트 성과 추적 및 LLM 사용량 로깅 시스템 추가

실행 방법:
python migrations/001_phase3_schema_expansion.py [--db-path custom_path]
"""

import sqlite3
import sys
import argparse
from pathlib import Path
from datetime import datetime

# 프로젝트 루트 경로 추가
sys.path.append(str(Path(__file__).parent.parent))


def check_current_schema_version(db_path: str) -> int:
    """현재 스키마 버전 확인"""
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # schema_version 테이블 존재 확인
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='schema_version'
            """)
            
            if not cursor.fetchone():
                return 0  # 초기 버전
            
            # 최신 버전 확인
            cursor.execute("SELECT MAX(version) FROM schema_version")
            result = cursor.fetchone()
            return result[0] if result[0] else 0
            
    except Exception as e:
        print(f"❌ 스키마 버전 확인 실패: {e}")
        return -1


def backup_database(db_path: str) -> str:
    """데이터베이스 백업"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{db_path}.backup_{timestamp}"
        
        # 원본 파일 복사
        import shutil
        shutil.copy2(db_path, backup_path)
        
        print(f"✅ 데이터베이스 백업 완료: {backup_path}")
        return backup_path
        
    except Exception as e:
        print(f"❌ 데이터베이스 백업 실패: {e}")
        return None


def add_agent_contribution_fields(cursor) -> bool:
    """기존 trades 테이블에 에이전트 기여도 필드 추가"""
    try:
        # 새로운 컬럼들 추가
        new_columns = [
            ("agent_contributions", "TEXT"),  # JSON 형태
            ("decision_confidence", "REAL"),
            ("analysis_metadata", "TEXT")  # JSON 형태
        ]
        
        for column_name, column_type in new_columns:
            try:
                cursor.execute(f"ALTER TABLE trades ADD COLUMN {column_name} {column_type}")
                print(f"✅ trades 테이블에 {column_name} 컬럼 추가")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e):
                    print(f"⚠️  {column_name} 컬럼이 이미 존재함")
                else:
                    raise e
        
        return True
        
    except Exception as e:
        print(f"❌ trades 테이블 확장 실패: {e}")
        return False


def create_new_tables(cursor) -> bool:
    """새로운 테이블들 생성"""
    try:
        # 1. 에이전트 성과 테이블
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
        print("✅ agent_performance 테이블 생성")
        
        # 2. LLM 사용량 로그 테이블
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
        print("✅ llm_usage_log 테이블 생성")
        
        # 3. 모델 진화 이력 테이블
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
        print("✅ model_evolution_history 테이블 생성")
        
        # 4. 시스템 성과 지표 테이블
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
        print("✅ system_metrics 테이블 생성")
        
        return True
        
    except Exception as e:
        print(f"❌ 새로운 테이블 생성 실패: {e}")
        return False


def create_indexes(cursor) -> bool:
    """새로운 인덱스들 생성"""
    try:
        indexes = [
            # 에이전트 성과 테이블 인덱스
            ("idx_agent_performance_agent", "agent_performance", "agent_name"),
            ("idx_agent_performance_period", "agent_performance", "period_start, period_end"),
            
            # LLM 사용량 로그 인덱스
            ("idx_llm_usage_agent", "llm_usage_log", "agent_name"),
            ("idx_llm_usage_provider", "llm_usage_log", "provider"),
            ("idx_llm_usage_timestamp", "llm_usage_log", "timestamp"),
            
            # 모델 진화 이력 인덱스
            ("idx_model_evolution_agent", "model_evolution_history", "agent_name"),
            ("idx_model_evolution_timestamp", "model_evolution_history", "timestamp"),
            
            # 시스템 메트릭 인덱스
            ("idx_system_metrics_date", "system_metrics", "date")
        ]
        
        for index_name, table_name, columns in indexes:
            cursor.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name}({columns})")
            print(f"✅ 인덱스 생성: {index_name}")
        
        return True
        
    except Exception as e:
        print(f"❌ 인덱스 생성 실패: {e}")
        return False


def update_schema_version(cursor) -> bool:
    """스키마 버전 업데이트"""
    try:
        # schema_version 테이블이 없으면 생성
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY,
                applied_at TEXT DEFAULT CURRENT_TIMESTAMP,
                description TEXT
            )
        ''')
        
        # 새 버전 기록
        cursor.execute('''
            INSERT OR REPLACE INTO schema_version (version, description) 
            VALUES (1, "Phase 3 schema expansion: agent performance tracking, LLM usage logging, model evolution")
        ''')
        print("✅ 스키마 버전 1로 업데이트")
        
        return True
        
    except Exception as e:
        print(f"❌ 스키마 버전 업데이트 실패: {e}")
        return False


def run_migration(db_path: str, force: bool = False) -> bool:
    """마이그레이션 실행"""
    print(f"🚀 Phase 3 스키마 확장 마이그레이션 시작")
    print(f"📁 데이터베이스 경로: {db_path}")
    
    # 현재 버전 확인
    current_version = check_current_schema_version(db_path)
    if current_version == -1:
        return False
    
    print(f"📊 현재 스키마 버전: {current_version}")
    
    if current_version >= 1 and not force:
        print("✅ 이미 최신 버전입니다. --force 옵션을 사용하여 강제 실행 가능")
        return True
    
    # 데이터베이스 백업
    if Path(db_path).exists():
        backup_path = backup_database(db_path)
        if not backup_path:
            return False
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # 트랜잭션 시작
            cursor.execute("BEGIN")
            
            print("\n📝 1. 기존 trades 테이블에 에이전트 기여도 필드 추가...")
            if not add_agent_contribution_fields(cursor):
                raise Exception("trades 테이블 확장 실패")
            
            print("\n📝 2. 새로운 테이블들 생성...")
            if not create_new_tables(cursor):
                raise Exception("새로운 테이블 생성 실패")
            
            print("\n📝 3. 성능 최적화 인덱스 생성...")
            if not create_indexes(cursor):
                raise Exception("인덱스 생성 실패")
            
            print("\n📝 4. 스키마 버전 업데이트...")
            if not update_schema_version(cursor):
                raise Exception("스키마 버전 업데이트 실패")
            
            # 커밋
            cursor.execute("COMMIT")
            
            print("\n🎉 마이그레이션 성공적으로 완료!")
            print(f"📈 스키마 버전: {current_version} -> 1")
            
            return True
            
    except Exception as e:
        print(f"\n❌ 마이그레이션 실패: {e}")
        try:
            cursor.execute("ROLLBACK")
            print("🔄 변경사항 롤백 완료")
        except:
            pass
        return False


def verify_migration(db_path: str) -> bool:
    """마이그레이션 검증"""
    print("\n🔍 마이그레이션 결과 검증 중...")
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # 1. 스키마 버전 확인
            cursor.execute("SELECT version FROM schema_version ORDER BY version DESC LIMIT 1")
            version = cursor.fetchone()
            if not version or version[0] != 1:
                print("❌ 스키마 버전이 올바르지 않음")
                return False
            print("✅ 스키마 버전 확인")
            
            # 2. 새로운 테이블들 존재 확인
            required_tables = [
                'trades', 'agent_performance', 'llm_usage_log', 
                'model_evolution_history', 'system_metrics', 'schema_version'
            ]
            
            for table in required_tables:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
                if not cursor.fetchone():
                    print(f"❌ 테이블 {table}이 존재하지 않음")
                    return False
            print("✅ 모든 테이블 존재 확인")
            
            # 3. trades 테이블 새 컬럼 확인
            cursor.execute("PRAGMA table_info(trades)")
            columns = [col[1] for col in cursor.fetchall()]
            required_columns = ['agent_contributions', 'decision_confidence', 'analysis_metadata']
            
            for col in required_columns:
                if col not in columns:
                    print(f"❌ trades 테이블에 {col} 컬럼이 없음")
                    return False
            print("✅ trades 테이블 확장 컬럼 확인")
            
            print("🎉 마이그레이션 검증 완료!")
            return True
            
    except Exception as e:
        print(f"❌ 검증 실패: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Phase 3 데이터베이스 스키마 확장 마이그레이션")
    parser.add_argument(
        "--db-path", 
        default="data/trading_records.db",
        help="데이터베이스 파일 경로 (기본값: data/trading_records.db)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="이미 최신 버전이어도 강제로 마이그레이션 실행"
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="마이그레이션 없이 검증만 실행"
    )
    
    args = parser.parse_args()
    
    # 데이터베이스 디렉토리 생성
    db_path = Path(args.db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    if args.verify_only:
        return verify_migration(str(db_path))
    
    # 마이그레이션 실행
    success = run_migration(str(db_path), args.force)
    
    if success:
        # 검증 실행
        verify_migration(str(db_path))
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)