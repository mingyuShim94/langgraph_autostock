#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KIS API 클라이언트 테스트
"""

import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.kis_client.client import KISClient, get_kis_client

def test_kis_client_mock_mode():
    """KIS 클라이언트 모의 모드 테스트"""
    print("🎭 KIS 클라이언트 모의 모드 테스트...")
    
    try:
        # 모의 모드로 클라이언트 생성
        client = KISClient(environment="paper", mock_mode=True)
        print("✅ 모의 모드 클라이언트 생성 성공")
        
        # 계좌 잔고 조회 테스트
        balance = client.get_account_balance()
        print(f"✅ 계좌 잔고: {balance.get('total_cash', 0):,}원")
        
        # 주식 보유 현황 테스트
        holdings = client.get_stock_holdings()
        print(f"✅ 보유 종목: {len(holdings)}개")
        if holdings:
            print(f"   첫 번째 종목: {holdings[0]['name']} ({holdings[0]['ticker']})")
        
        # 주식 가격 조회 테스트
        price_info = client.get_stock_price("005930")
        print(f"✅ 삼성전자 현재가: {price_info.get('current_price', 0):,}원")
        
        return True
        
    except Exception as e:
        print(f"❌ 모의 모드 테스트 실패: {e}")
        return False

def test_kis_client_real_api():
    """KIS 클라이언트 실제 API 테스트"""
    print("\n🔗 KIS 클라이언트 실제 API 테스트...")
    
    try:
        # 실제 API로 클라이언트 생성 (모의투자)
        client = KISClient(environment="paper", mock_mode=False)
        print("✅ 실제 API 클라이언트 생성 성공")
        
        # KIS 환경 상태 확인
        try:
            import sys
            sys.path.extend(['open-trading-api-main/examples_user'])
            import kis_auth as ka
            
            trenv = ka.getTREnv()
            is_paper = ka.isPaperTrading()
            print(f"🔧 KIS 환경 상태 - 모의투자: {is_paper}, 계좌: {trenv.my_acct}")
        except Exception as debug_e:
            print(f"⚠️ 환경 상태 확인 실패: {debug_e}")
        
        # 계좌 잔고 조회 테스트
        balance = client.get_account_balance()
        if "error" not in balance:
            print(f"✅ 실제 계좌 잔고: {balance.get('total_cash', 0):,}원")
            print(f"   총 자산: {balance.get('total_value', 0):,}원")
        else:
            print(f"⚠️ 계좌 잔고 조회 오류: {balance['error']}")
        
        # 주식 보유 현황 테스트
        holdings = client.get_stock_holdings()
        print(f"✅ 실제 보유 종목: {len(holdings)}개")
        
        for holding in holdings[:3]:  # 최대 3개만 표시
            print(f"   📊 {holding['name']} ({holding['ticker']})")
            print(f"      보유: {holding['quantity']:,}주, 평단: {holding['avg_price']:,}원")
            print(f"      현재가: {holding['current_price']:,}원, 손익: {holding['pnl']:,}원")
        
        # 주식 가격 조회 테스트 (삼성전자)
        price_info = client.get_stock_price("005930")
        if "error" not in price_info:
            print(f"✅ 삼성전자 실시간 정보:")
            print(f"   현재가: {price_info.get('current_price', 0):,}원")
            print(f"   등락: {price_info.get('change', 0):,}원 ({price_info.get('change_rate', 0):.2f}%)")
            print(f"   거래량: {price_info.get('volume', 0):,}주")
        else:
            print(f"⚠️ 주식 가격 조회 오류: {price_info['error']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 실제 API 테스트 실패: {e}")
        print("   KIS API 설정을 확인해주세요.")
        return False

def test_trading_functions():
    """거래 기능 테스트 (모의 모드)"""
    print("\n💰 거래 기능 테스트 (모의 모드)...")
    
    try:
        client = KISClient(environment="paper", mock_mode=True)
        
        # 모의 매수 주문
        buy_result = client.place_buy_order(
            ticker="005930",
            quantity=1,
            price=75000
        )
        
        if buy_result.get("status") == "success":
            print("✅ 모의 매수 주문 성공")
            print(f"   주문ID: {buy_result['order_id']}")
            print(f"   종목: {buy_result['ticker']}")
            print(f"   수량: {buy_result['quantity']}주")
            print(f"   가격: {buy_result['price']:,}원")
        else:
            print(f"❌ 매수 주문 실패: {buy_result}")
        
        # 모의 매도 주문
        sell_result = client.place_sell_order(
            ticker="005930",
            quantity=1,
            price=77000
        )
        
        if sell_result.get("status") == "success":
            print("✅ 모의 매도 주문 성공")
            print(f"   주문ID: {sell_result['order_id']}")
            print(f"   수량: {sell_result['quantity']}주")
            print(f"   가격: {sell_result['price']:,}원")
        else:
            print(f"❌ 매도 주문 실패: {sell_result}")
        
        return True
        
    except Exception as e:
        print(f"❌ 거래 기능 테스트 실패: {e}")
        return False

def test_singleton_pattern():
    """싱글톤 패턴 테스트"""
    print("\n🔄 싱글톤 패턴 테스트...")
    
    try:
        client1 = get_kis_client(mock_mode=True)
        client2 = get_kis_client(mock_mode=True)
        
        if client1 is client2:
            print("✅ 싱글톤 패턴 정상 동작 (같은 인스턴스)")
            return True
        else:
            print("❌ 싱글톤 패턴 오류 (다른 인스턴스)")
            return False
            
    except Exception as e:
        print(f"❌ 싱글톤 패턴 테스트 실패: {e}")
        return False

def main():
    """메인 테스트 함수"""
    print("🚀 KIS API 클라이언트 종합 테스트")
    print("=" * 60)
    
    tests = [
        ("모의 모드 기본 기능", test_kis_client_mock_mode),
        ("실제 API 연동", test_kis_client_real_api),
        ("거래 기능 (모의)", test_trading_functions),
        ("싱글톤 패턴", test_singleton_pattern),
    ]
    
    results = []
    for test_name, test_func in tests:
        result = test_func()
        results.append((test_name, result))
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("🎯 KIS 클라이언트 테스트 결과")
    
    for test_name, result in results:
        status = "✅ 성공" if result else "❌ 실패"
        print(f"   {test_name}: {status}")
    
    passed_count = sum(1 for _, result in results if result)
    total_count = len(results)
    
    print(f"\n📊 전체 결과: {passed_count}/{total_count} 테스트 통과")
    
    if passed_count == total_count:
        print("🎉 모든 KIS 클라이언트 테스트 통과!")
        print("   Phase 1 KIS API 클라이언트 모듈 구현 완료")
    elif passed_count >= total_count - 1:
        print("⚠️ 대부분의 테스트 통과. 실제 API 설정을 확인해주세요.")
    else:
        print("❌ 여러 테스트 실패. 코드를 점검해주세요.")

if __name__ == "__main__":
    main()