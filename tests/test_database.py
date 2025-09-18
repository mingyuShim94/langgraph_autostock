#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
데이터베이스 스키마 테스트
"""

import sys
import os
from datetime import datetime
from uuid import uuid4

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.database.schema import DatabaseManager, TradeRecord

def test_database_creation():
    """데이터베이스 생성 테스트"""
    print("🗄️ 데이터베이스 생성 테스트...")
    
    try:
        # 테스트용 데이터베이스 생성
        db = DatabaseManager("data/test_trading_records.db")
        print("✅ 데이터베이스 생성 성공")
        return True
    except Exception as e:
        print(f"❌ 데이터베이스 생성 실패: {e}")
        return False

def test_trade_record_insertion():
    """거래 기록 삽입 테스트"""
    print("\n📝 거래 기록 삽입 테스트...")
    
    try:
        db = DatabaseManager("data/test_trading_records.db")
        
        # 샘플 거래 기록 생성
        trade_record = TradeRecord(
            trade_id=str(uuid4()),
            timestamp=datetime.now().isoformat(),
            ticker="005930",  # 삼성전자
            action="buy",
            quantity=10,
            price=75000,
            justification_text="기술적 지표 상승 신호 및 거래량 증가로 매수 결정",
            market_snapshot={
                "market_status": "open",
                "kospi_index": 2500.5,
                "vix": 18.2,
                "usd_krw": 1320.5
            },
            portfolio_before={
                "total_value": 10000000,
                "cash": 2000000,
                "holdings": {"005930": {"quantity": 5, "avg_price": 73000}}
            },
            pnl_7_days=None,  # 아직 미정
            pnl_30_days=None
        )
        
        # 데이터 삽입
        success = db.insert_trade(trade_record)
        
        if success:
            print("✅ 거래 기록 삽입 성공")
            print(f"   거래 ID: {trade_record.trade_id}")
            print(f"   종목: {trade_record.ticker}")
            print(f"   액션: {trade_record.action}")
            print(f"   수량: {trade_record.quantity}")
            return True
        else:
            print("❌ 거래 기록 삽입 실패")
            return False
            
    except Exception as e:
        print(f"❌ 거래 기록 삽입 테스트 실패: {e}")
        return False

def test_trade_record_query():
    """거래 기록 조회 테스트"""
    print("\n🔍 거래 기록 조회 테스트...")
    
    try:
        db = DatabaseManager("data/test_trading_records.db")
        
        # 최근 30일 거래 조회
        trades = db.get_trades_by_period(30)
        print(f"✅ 최근 30일 거래: {len(trades)}건")
        
        if trades:
            latest_trade = trades[0]
            print(f"   최근 거래 - 종목: {latest_trade['ticker']}, "
                  f"액션: {latest_trade['action']}, "
                  f"가격: {latest_trade['price']:,}원")
        
        # 거래 통계 조회
        stats = db.get_trade_statistics()
        print(f"✅ 거래 통계:")
        print(f"   총 거래: {stats.get('total_trades', 0)}건")
        print(f"   매수: {stats.get('buy_trades', 0)}건")
        print(f"   매도: {stats.get('sell_trades', 0)}건")
        
        return True
        
    except Exception as e:
        print(f"❌ 거래 기록 조회 테스트 실패: {e}")
        return False

def test_pnl_update():
    """손익 업데이트 테스트"""
    print("\n💰 손익 업데이트 테스트...")
    
    try:
        db = DatabaseManager("data/test_trading_records.db")
        
        # 최근 거래 가져오기
        trades = db.get_trades_by_period(30)
        if not trades:
            print("❌ 업데이트할 거래 기록이 없습니다")
            return False
        
        trade_id = trades[0]['trade_id']
        
        # 가상의 7일 후 손익 업데이트
        test_pnl_7d = 50000  # 5만원 수익
        success = db.update_pnl(trade_id, pnl_7_days=test_pnl_7d)
        
        if success:
            print(f"✅ 손익 업데이트 성공")
            print(f"   거래 ID: {trade_id}")
            print(f"   7일 손익: {test_pnl_7d:,}원")
            return True
        else:
            print("❌ 손익 업데이트 실패")
            return False
            
    except Exception as e:
        print(f"❌ 손익 업데이트 테스트 실패: {e}")
        return False

def main():
    """메인 테스트 함수"""
    print("🚀 데이터베이스 스키마 종합 테스트")
    print("=" * 50)
    
    tests = [
        ("데이터베이스 생성", test_database_creation),
        ("거래 기록 삽입", test_trade_record_insertion),
        ("거래 기록 조회", test_trade_record_query),
        ("손익 업데이트", test_pnl_update),
    ]
    
    results = []
    for test_name, test_func in tests:
        result = test_func()
        results.append((test_name, result))
    
    # 결과 요약
    print("\n" + "=" * 50)
    print("🎯 데이터베이스 테스트 결과")
    
    for test_name, result in results:
        status = "✅ 성공" if result else "❌ 실패"
        print(f"   {test_name}: {status}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("\n🎉 모든 데이터베이스 테스트 통과!")
        print("   Phase 1 데이터베이스 스키마 구현 완료")
    else:
        print("\n⚠️  일부 테스트 실패. 코드를 점검해주세요.")

if __name__ == "__main__":
    main()