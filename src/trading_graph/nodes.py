#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 트레이딩 시스템 운영 그래프 노드 구현

LangGraph 워크플로우를 구성하는 6개 핵심 노드 정의:
1. fetch_portfolio_status: 포트폴리오 진단
2. analyze_market_conditions: 시장 분석 및 기회/위험 탐색  
3. generate_trading_plan: AI 의사결정 엔진
4. validate_trading_plan: 최종 리스크 점검
5. execute_trading_plan: 주문 실행
6. record_and_report: 기록 및 보고
"""

import json
import time
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path

# 프로젝트 모듈 임포트
from src.kis_client.client import get_kis_client
from src.database.schema import db_manager, TradeRecord
from src.trading_graph.state import (
    TradingState, PortfolioStatus, MarketAnalysis, TradingPlan, 
    RiskValidation, ExecutionResult, add_error
)


def fetch_portfolio_status(state: TradingState) -> TradingState:
    """
    노드 1: 포트폴리오 진단
    
    KIS API를 통해 계좌잔고와 주식잔고를 조회하여 
    현재 포트폴리오 상태를 진단합니다.
    """
    print("🔍 [Node 1] 포트폴리오 진단 시작...")
    
    try:
        # KIS 클라이언트 획득
        environment = state.get("environment", "paper")
        mock_mode = state.get("mock_mode", True)
        client = get_kis_client(environment=environment, mock_mode=mock_mode)
        
        # 계좌 잔고 조회
        print("  📊 계좌 잔고 조회 중...")
        balance_info = client.get_account_balance()
        total_cash = balance_info.get("total_cash", 0)
        total_value = balance_info.get("total_value", total_cash)
        
        # 주식 보유 현황 조회
        print("  📈 주식 보유 현황 조회 중...")
        stock_holdings = client.get_stock_holdings()
        
        # 포지션별 분석
        stock_positions = {}
        total_stock_value = 0
        
        for holding in stock_holdings:
            ticker = holding.get("ticker", "")
            if ticker:
                position_value = holding.get("quantity", 0) * holding.get("current_price", 0)
                total_stock_value += position_value
                
                stock_positions[ticker] = {
                    "name": holding.get("name", ""),
                    "quantity": holding.get("quantity", 0),
                    "avg_price": holding.get("avg_price", 0),
                    "current_price": holding.get("current_price", 0),
                    "position_value": position_value,
                    "pnl": holding.get("pnl", 0),
                    "pnl_rate": holding.get("pnl_rate", 0.0)
                }
        
        # 현금 비중 계산
        cash_ratio = (total_cash / total_value * 100) if total_value > 0 else 100.0
        
        # PortfolioStatus 객체 생성
        portfolio_status = PortfolioStatus(
            total_cash=total_cash,
            total_value=total_value,
            stock_holdings=stock_holdings,
            cash_ratio=cash_ratio,
            stock_positions=stock_positions
        )
        
        print(f"  ✅ 포트폴리오 진단 완료")
        print(f"     💰 총자산: {total_value:,.0f}원")
        print(f"     💵 현금: {total_cash:,.0f}원 ({cash_ratio:.1f}%)")
        print(f"     📊 보유종목: {len(stock_holdings)}개")
        
        return {
            **state,
            "portfolio_status": portfolio_status.to_dict(),
            "current_node": "portfolio_diagnosis"
        }
        
    except Exception as e:
        error_msg = f"포트폴리오 진단 실패: {str(e)}"
        print(f"  ❌ {error_msg}")
        return add_error(state, error_msg)


def analyze_market_conditions(state: TradingState) -> TradingState:
    """
    노드 2: 시장 분석 및 기회/위험 탐색
    
    보유종목의 실시간 시세를 조회하고, 거래량 및 가격 변동을 분석하여
    시장 기회와 위험 요소를 탐지합니다.
    """
    print("🔍 [Node 2] 시장 분석 시작...")
    
    try:
        # KIS 클라이언트 획득
        environment = state.get("environment", "paper")
        mock_mode = state.get("mock_mode", True)
        client = get_kis_client(environment=environment, mock_mode=mock_mode)
        
        # 포트폴리오 정보 확인
        portfolio_status = state.get("portfolio_status")
        if not portfolio_status:
            raise ValueError("포트폴리오 정보가 없습니다. Node 1을 먼저 실행해주세요.")
        
        stock_positions = portfolio_status.get("stock_positions", {})
        
        # 보유종목 실시간 시세 분석
        print("  📈 보유종목 실시간 시세 분석 중...")
        price_movers = []
        
        for ticker, position in stock_positions.items():
            try:
                price_info = client.get_stock_price(ticker)
                current_price = price_info.get("current_price", 0)
                change_rate = price_info.get("change_rate", 0.0)
                volume = price_info.get("volume", 0)
                
                # 급등락 종목 탐지 (변동률 ±3% 이상)
                if abs(change_rate) >= 3.0:
                    price_movers.append({
                        "ticker": ticker,
                        "name": position.get("name", ""),
                        "current_price": current_price,
                        "change_rate": change_rate,
                        "volume": volume,
                        "direction": "상승" if change_rate > 0 else "하락"
                    })
                    
            except Exception as e:
                print(f"    ⚠️ {ticker} 시세 조회 실패: {e}")
        
        # 거래량 상위 종목 조회 (KIS API 활용)
        print("  📊 거래량 상위 종목 조회 중...")
        try:
            volume_leaders = client.get_trading_volume_rank()[:10]  # 상위 10개
        except Exception as e:
            print(f"    ⚠️ 거래량 상위 종목 조회 실패: {e}")
            volume_leaders = []
        
        # 시장 심리 및 점수 계산
        market_sentiment = "neutral"
        market_score = 50.0
        risk_factors = []
        opportunities = []
        
        # 급등락 종목 분석
        rising_count = len([m for m in price_movers if m["direction"] == "상승"])
        falling_count = len([m for m in price_movers if m["direction"] == "하락"])
        
        if rising_count > falling_count:
            market_sentiment = "bullish"
            market_score += 20
            opportunities.append(f"보유종목 중 {rising_count}개 급상승 중")
        elif falling_count > rising_count:
            market_sentiment = "bearish"
            market_score -= 20
            risk_factors.append(f"보유종목 중 {falling_count}개 급하락 중")
        
        # 현금 비중 분석
        cash_ratio = portfolio_status.get("cash_ratio", 0)
        if cash_ratio > 50:
            opportunities.append("높은 현금 비중으로 매수 기회 포착 가능")
            market_score += 10
        elif cash_ratio < 10:
            risk_factors.append("낮은 현금 비중으로 추가 투자 여력 부족")
            market_score -= 10
        
        # 기본 리스크 요소
        if len(stock_positions) > 10:
            risk_factors.append("과도한 종목 분산으로 관리 복잡성 증가")
        
        if not opportunities:
            opportunities.append("현재 특별한 기회 요소 없음")
            
        if not risk_factors:
            risk_factors.append("현재 특별한 리스크 요소 없음")
        
        # MarketAnalysis 객체 생성
        market_analysis = MarketAnalysis(
            market_sentiment=market_sentiment,
            volume_leaders=volume_leaders,
            price_movers=price_movers,
            risk_factors=risk_factors,
            opportunities=opportunities,
            market_score=max(0, min(100, market_score))  # 0-100 범위로 제한
        )
        
        print(f"  ✅ 시장 분석 완료")
        print(f"     🎭 시장심리: {market_sentiment}")
        print(f"     📊 시장점수: {market_analysis.market_score:.1f}/100")
        print(f"     📈 급등락종목: {len(price_movers)}개")
        print(f"     🎯 기회요소: {len(opportunities)}개")
        print(f"     ⚠️ 리스크요소: {len(risk_factors)}개")
        
        return {
            **state,
            "market_analysis": market_analysis.to_dict(),
            "current_node": "market_analysis"
        }
        
    except Exception as e:
        error_msg = f"시장 분석 실패: {str(e)}"
        print(f"  ❌ {error_msg}")
        return add_error(state, error_msg)


def generate_trading_plan(state: TradingState) -> TradingState:
    """
    노드 3: AI 의사결정 엔진
    
    포트폴리오 현황과 시장 분석 결과를 바탕으로
    OpenAI GPT-4를 활용하여 거래 계획을 생성합니다.
    """
    print("🧠 [Node 3] AI 의사결정 엔진 시작...")
    
    try:
        # 필수 상태 확인
        portfolio_status = state.get("portfolio_status")
        market_analysis = state.get("market_analysis")
        
        if not portfolio_status or not market_analysis:
            raise ValueError("포트폴리오 정보 또는 시장 분석 결과가 없습니다.")
        
        # 의사결정 프롬프트 로드
        prompt_path = Path("prompts/core_decision_prompt.md")
        if not prompt_path.exists():
            raise FileNotFoundError("의사결정 프롬프트 파일이 없습니다.")
        
        print("  📖 의사결정 프롬프트 로드 중...")
        with open(prompt_path, 'r', encoding='utf-8') as f:
            decision_prompt = f.read()
        
        # 컨텍스트 구성
        context = {
            "portfolio": portfolio_status,
            "market": market_analysis,
            "timestamp": datetime.now().isoformat()
        }
        
        # 현재는 Mock AI 의사결정 (실제 OpenAI 연동은 추후 구현)
        print("  🤖 AI 의사결정 처리 중...")
        print("     ℹ️ [Mock Mode] 실제 OpenAI GPT-4 연동은 추후 구현")
        
        # Mock 거래 계획 생성
        actions = []
        justification = "Mock AI 의사결정: 현재 시장 상황을 분석한 결과, "
        
        # 시장 점수 기반 의사결정
        market_score = market_analysis.get("market_score", 50)
        cash_ratio = portfolio_status.get("cash_ratio", 0)
        
        if market_score > 70 and cash_ratio > 30:
            # 강세장이고 현금이 충분한 경우
            actions.append({
                "type": "buy",
                "ticker": "005930",  # 삼성전자
                "quantity": 1,
                "target_price": 75000,
                "reason": "시장 점수가 높고 현금 여력이 충분하여 우량주 매수"
            })
            justification += "강세 시장 상황에서 현금 여력을 활용한 추가 투자가 적절합니다."
            
        elif market_score < 30:
            # 약세장인 경우
            stock_positions = portfolio_status.get("stock_positions", {})
            if stock_positions:
                # 손실이 큰 종목이 있다면 매도 고려
                for ticker, position in stock_positions.items():
                    pnl_rate = position.get("pnl_rate", 0)
                    if pnl_rate < -5:  # 5% 이상 손실
                        actions.append({
                            "type": "sell",
                            "ticker": ticker,
                            "quantity": max(1, position.get("quantity", 0) // 2),
                            "target_price": position.get("current_price", 0),
                            "reason": f"손실 확정 및 리스크 관리 ({pnl_rate:.1f}% 손실)"
                        })
                        break
            justification += "약세 시장 상황에서 손실 관리 및 현금 확보가 우선입니다."
            
        else:
            # 중립 시장
            justification += "중립적 시장 상황에서 현재 포지션 유지가 적절합니다."
        
        # 액션이 없는 경우 기본 메시지
        if not actions:
            justification += " 현재 상황에서는 관망이 최선의 선택입니다."
        
        # TradingPlan 객체 생성
        trading_plan = TradingPlan(
            actions=actions,
            justification=justification,
            risk_assessment="Mock 리스크 평가: 포지션 사이즈 및 손실 한도 내에서 거래 계획",
            expected_outcome=f"예상 수익률: ±3%, 성공 확률: {min(90, market_score + 20):.0f}%",
            confidence_score=min(95, market_score + 30)  # Mock 신뢰도
        )
        
        print(f"  ✅ AI 의사결정 완료")
        print(f"     🎯 계획된 거래: {len(actions)}건")
        print(f"     🔮 신뢰도: {trading_plan.confidence_score:.1f}%")
        
        if actions:
            print("     📋 거래 계획:")
            for i, action in enumerate(actions, 1):
                action_type = "매수" if action["type"] == "buy" else "매도"
                print(f"       {i}. {action_type} {action['ticker']} {action['quantity']}주 @ {action['target_price']:,}원")
        
        return {
            **state,
            "trading_plan": trading_plan.to_dict(),
            "current_node": "ai_decision"
        }
        
    except Exception as e:
        error_msg = f"AI 의사결정 실패: {str(e)}"
        print(f"  ❌ {error_msg}")
        return add_error(state, error_msg)


def validate_trading_plan(state: TradingState) -> TradingState:
    """
    노드 4: 최종 리스크 점검
    
    생성된 거래 계획이 리스크 관리 규칙을 준수하는지 
    최종 검증을 수행합니다.
    """
    print("🛡️ [Node 4] 최종 리스크 점검 시작...")
    
    try:
        # 필수 상태 확인
        portfolio_status = state.get("portfolio_status")
        trading_plan = state.get("trading_plan")
        
        if not portfolio_status or not trading_plan:
            raise ValueError("포트폴리오 정보 또는 거래 계획이 없습니다.")
        
        actions = trading_plan.get("actions", [])
        total_cash = portfolio_status.get("total_cash", 0)
        total_value = portfolio_status.get("total_value", 0)
        stock_positions = portfolio_status.get("stock_positions", {})
        
        # 검증 결과 초기화
        cash_sufficient = True
        position_size_ok = True  
        daily_loss_limit_ok = True
        price_range_valid = True
        validation_errors = []
        
        print("  🔍 거래 계획 검증 중...")
        
        # 현금 충분성 검증
        print("    💰 현금 충분성 검증...")
        required_cash = 0
        for action in actions:
            if action.get("type") == "buy":
                cost = action.get("quantity", 0) * action.get("target_price", 0)
                required_cash += cost
        
        if required_cash > total_cash:
            cash_sufficient = False
            validation_errors.append(f"현금 부족: 필요 {required_cash:,}원 > 보유 {total_cash:,}원")
        
        # 포지션 사이징 검증 (단일 종목 10% 제한)
        print("    📊 포지션 사이징 검증...")
        for action in actions:
            if action.get("type") == "buy":
                ticker = action.get("ticker", "")
                quantity = action.get("quantity", 0)
                target_price = action.get("target_price", 0)
                investment_amount = quantity * target_price
                
                # 현재 보유 가치 + 신규 투자 금액
                current_position_value = 0
                if ticker in stock_positions:
                    current_position_value = stock_positions[ticker].get("position_value", 0)
                
                total_position_value = current_position_value + investment_amount
                position_ratio = (total_position_value / total_value) * 100
                
                if position_ratio > 10:
                    position_size_ok = False
                    validation_errors.append(f"{ticker} 포지션 과대: {position_ratio:.1f}% > 10%")
        
        # 일일 손실 한도 검증 (총 자산의 2% 제한)
        print("    ⚠️ 일일 손실 한도 검증...")
        max_daily_loss = total_value * 0.02  # 2%
        
        # 현재 일일 손실 계산 (간소화된 버전)
        current_daily_loss = 0
        for position in stock_positions.values():
            pnl = position.get("pnl", 0)
            if pnl < 0:
                current_daily_loss += abs(pnl)
        
        if current_daily_loss > max_daily_loss:
            daily_loss_limit_ok = False
            validation_errors.append(f"일일 손실 한도 초과: {current_daily_loss:,}원 > {max_daily_loss:,}원")
        
        # 가격 범위 유효성 검증 (상한가/하한가 체크는 간소화)
        print("    💹 가격 범위 유효성 검증...")
        for action in actions:
            target_price = action.get("target_price", 0)
            if target_price <= 0:
                price_range_valid = False
                validation_errors.append(f"잘못된 목표가격: {target_price}")
        
        # 전체 검증 결과
        is_valid = cash_sufficient and position_size_ok and daily_loss_limit_ok and price_range_valid
        
        # RiskValidation 객체 생성
        risk_validation = RiskValidation(
            is_valid=is_valid,
            cash_sufficient=cash_sufficient,
            position_size_ok=position_size_ok,
            daily_loss_limit_ok=daily_loss_limit_ok,
            price_range_valid=price_range_valid,
            validation_errors=validation_errors
        )
        
        print(f"  ✅ 리스크 점검 완료")
        print(f"     🛡️ 검증 결과: {'✅ 통과' if is_valid else '❌ 실패'}")
        
        if validation_errors:
            print(f"     ⚠️ 검증 오류 {len(validation_errors)}건:")
            for i, error in enumerate(validation_errors, 1):
                print(f"       {i}. {error}")
        
        return {
            **state,
            "risk_validation": risk_validation.to_dict(),
            "current_node": "risk_validation"
        }
        
    except Exception as e:
        error_msg = f"리스크 점검 실패: {str(e)}"
        print(f"  ❌ {error_msg}")
        return add_error(state, error_msg)


def execute_trading_plan(state: TradingState) -> TradingState:
    """
    노드 5: 주문 실행
    
    리스크 검증을 통과한 거래 계획을 바탕으로
    실제 주문을 실행합니다.
    """
    print("⚡ [Node 5] 주문 실행 시작...")
    
    try:
        # 필수 상태 확인
        trading_plan = state.get("trading_plan")
        risk_validation = state.get("risk_validation")
        
        if not trading_plan or not risk_validation:
            raise ValueError("거래 계획 또는 리스크 검증 결과가 없습니다.")
        
        # 리스크 검증 통과 확인
        if not risk_validation.get("is_valid", False):
            print("  ⚠️ 리스크 검증 실패로 주문 실행 취소")
            execution_result = ExecutionResult(
                executed_orders=[],
                failed_orders=[],
                total_executed=0,
                total_failed=0,
                execution_summary="리스크 검증 실패로 모든 주문 취소됨"
            )
            
            return {
                **state,
                "execution_result": execution_result.to_dict(),
                "current_node": "order_execution"
            }
        
        # KIS 클라이언트 획득
        environment = state.get("environment", "paper")
        mock_mode = state.get("mock_mode", True)
        client = get_kis_client(environment=environment, mock_mode=mock_mode)
        
        actions = trading_plan.get("actions", [])
        executed_orders = []
        failed_orders = []
        
        print(f"  📋 {len(actions)}건 주문 실행 중...")
        
        for i, action in enumerate(actions, 1):
            try:
                action_type = action.get("type")
                ticker = action.get("ticker", "")
                quantity = action.get("quantity", 0)
                target_price = action.get("target_price", 0)
                reason = action.get("reason", "")
                
                print(f"    {i}. {action_type.upper()} {ticker} {quantity}주 @ {target_price:,}원")
                
                # 주문 실행
                if action_type == "buy":
                    result = client.place_buy_order(
                        ticker=ticker,
                        quantity=quantity,
                        price=target_price
                    )
                elif action_type == "sell":
                    result = client.place_sell_order(
                        ticker=ticker,
                        quantity=quantity, 
                        price=target_price
                    )
                else:
                    raise ValueError(f"지원하지 않는 주문 유형: {action_type}")
                
                # 결과 처리
                if result.get("status") == "success":
                    order_info = {
                        "order_id": result.get("order_id"),
                        "ticker": ticker,
                        "type": action_type,
                        "quantity": quantity,
                        "price": target_price,
                        "reason": reason,
                        "timestamp": datetime.now().isoformat()
                    }
                    executed_orders.append(order_info)
                    print(f"       ✅ 성공 (주문ID: {result.get('order_id')})")
                else:
                    error_info = {
                        "ticker": ticker,
                        "type": action_type,
                        "quantity": quantity,
                        "price": target_price,
                        "error": result.get("error", "Unknown error"),
                        "timestamp": datetime.now().isoformat()
                    }
                    failed_orders.append(error_info)
                    print(f"       ❌ 실패: {result.get('error')}")
                
                # 주문 간 딜레이 (API 제한 고려)
                time.sleep(0.5)
                
            except Exception as e:
                error_info = {
                    "ticker": action.get("ticker", ""),
                    "type": action.get("type", ""),
                    "quantity": action.get("quantity", 0),
                    "price": action.get("target_price", 0),
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
                failed_orders.append(error_info)
                print(f"       ❌ 예외 발생: {e}")
        
        # 실행 결과 요약
        total_executed = len(executed_orders)
        total_failed = len(failed_orders)
        success_rate = (total_executed / len(actions) * 100) if actions else 0
        
        execution_summary = f"주문 실행 완료: 성공 {total_executed}건, 실패 {total_failed}건 (성공률 {success_rate:.1f}%)"
        
        # ExecutionResult 객체 생성
        execution_result = ExecutionResult(
            executed_orders=executed_orders,
            failed_orders=failed_orders,
            total_executed=total_executed,
            total_failed=total_failed,
            execution_summary=execution_summary
        )
        
        print(f"  ✅ 주문 실행 완료")
        print(f"     ⚡ 성공: {total_executed}건")
        print(f"     ❌ 실패: {total_failed}건")
        print(f"     📊 성공률: {success_rate:.1f}%")
        
        return {
            **state,
            "execution_result": execution_result.to_dict(),
            "current_node": "order_execution"
        }
        
    except Exception as e:
        error_msg = f"주문 실행 실패: {str(e)}"
        print(f"  ❌ {error_msg}")
        return add_error(state, error_msg)


def record_and_report(state: TradingState) -> TradingState:
    """
    노드 6: 기록 및 보고
    
    실행된 거래를 데이터베이스에 기록하고
    최종 보고서를 생성합니다.
    """
    print("📝 [Node 6] 기록 및 보고 시작...")
    
    try:
        # 필수 상태 확인
        execution_result = state.get("execution_result")
        if not execution_result:
            raise ValueError("주문 실행 결과가 없습니다.")
        
        executed_orders = execution_result.get("executed_orders", [])
        portfolio_status = state.get("portfolio_status", {})
        market_analysis = state.get("market_analysis", {})
        trading_plan = state.get("trading_plan", {})
        
        # 실행된 주문들을 데이터베이스에 기록
        print("  💾 거래 기록 데이터베이스 저장 중...")
        saved_count = 0
        
        for order in executed_orders:
            try:
                # TradeRecord 객체 생성
                trade_record = TradeRecord(
                    trade_id=order.get("order_id", f"UNKNOWN_{int(time.time())}"),
                    timestamp=order.get("timestamp", datetime.now().isoformat()),
                    ticker=order.get("ticker", ""),
                    action=order.get("type", ""),
                    quantity=order.get("quantity", 0),
                    price=order.get("price", 0),
                    justification_text=order.get("reason", ""),
                    market_snapshot=market_analysis,
                    portfolio_before=portfolio_status
                )
                
                # 데이터베이스에 저장
                if db_manager.insert_trade(trade_record):
                    saved_count += 1
                    print(f"    ✅ {order.get('ticker')} 기록 저장 완료")
                else:
                    print(f"    ❌ {order.get('ticker')} 기록 저장 실패")
                    
            except Exception as e:
                print(f"    ❌ 거래 기록 저장 오류: {e}")
        
        # 최종 보고서 생성
        print("  📊 최종 보고서 생성 중...")
        
        # 보고서 내용 구성
        report_sections = []
        
        # 1. 실행 요약
        report_sections.append("# 🤖 AI 트레이딩 시스템 실행 보고서")
        report_sections.append(f"**실행 시간**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_sections.append(f"**환경**: {state.get('environment', 'paper')} {'(Mock Mode)' if state.get('mock_mode') else ''}")
        report_sections.append("")
        
        # 2. 포트폴리오 현황
        report_sections.append("## 💰 포트폴리오 현황")
        total_value = portfolio_status.get("total_value", 0)
        total_cash = portfolio_status.get("total_cash", 0)
        cash_ratio = portfolio_status.get("cash_ratio", 0)
        stock_count = len(portfolio_status.get("stock_positions", {}))
        
        report_sections.append(f"- **총 자산**: {total_value:,.0f}원")
        report_sections.append(f"- **현금**: {total_cash:,.0f}원 ({cash_ratio:.1f}%)")
        report_sections.append(f"- **보유 종목**: {stock_count}개")
        report_sections.append("")
        
        # 3. 시장 분석 결과
        report_sections.append("## 📈 시장 분석")
        market_sentiment = market_analysis.get("market_sentiment", "unknown")
        market_score = market_analysis.get("market_score", 0)
        opportunities = market_analysis.get("opportunities", [])
        risk_factors = market_analysis.get("risk_factors", [])
        
        report_sections.append(f"- **시장 심리**: {market_sentiment}")
        report_sections.append(f"- **시장 점수**: {market_score:.1f}/100")
        report_sections.append(f"- **기회 요소**: {len(opportunities)}개")
        report_sections.append(f"- **리스크 요소**: {len(risk_factors)}개")
        report_sections.append("")
        
        # 4. AI 의사결정 결과
        report_sections.append("## 🧠 AI 의사결정")
        confidence_score = trading_plan.get("confidence_score", 0)
        justification = trading_plan.get("justification", "정보 없음")
        planned_actions = len(trading_plan.get("actions", []))
        
        report_sections.append(f"- **신뢰도**: {confidence_score:.1f}%")
        report_sections.append(f"- **계획된 거래**: {planned_actions}건")
        report_sections.append(f"- **의사결정 근거**: {justification}")
        report_sections.append("")
        
        # 5. 실행 결과
        report_sections.append("## ⚡ 실행 결과")
        total_executed = execution_result.get("total_executed", 0)
        total_failed = execution_result.get("total_failed", 0)
        success_rate = (total_executed / (total_executed + total_failed) * 100) if (total_executed + total_failed) > 0 else 0
        
        report_sections.append(f"- **성공한 주문**: {total_executed}건")
        report_sections.append(f"- **실패한 주문**: {total_failed}건")  
        report_sections.append(f"- **성공률**: {success_rate:.1f}%")
        report_sections.append(f"- **데이터베이스 저장**: {saved_count}건")
        report_sections.append("")
        
        # 6. 실행된 주문 상세
        if executed_orders:
            report_sections.append("## 📋 실행된 주문 상세")
            for i, order in enumerate(executed_orders, 1):
                action_type = "매수" if order.get("type") == "buy" else "매도"
                report_sections.append(f"{i}. **{action_type}** {order.get('ticker')} {order.get('quantity')}주 @ {order.get('price'):,}원")
                report_sections.append(f"   - 주문ID: {order.get('order_id')}")
                report_sections.append(f"   - 사유: {order.get('reason')}")
            report_sections.append("")
        
        # 7. 오류 및 주의사항
        errors = state.get("errors", [])
        if errors or execution_result.get("failed_orders"):
            report_sections.append("## ⚠️ 오류 및 주의사항")
            
            for error in errors:
                report_sections.append(f"- {error}")
            
            for failed_order in execution_result.get("failed_orders", []):
                action_type = "매수" if failed_order.get("type") == "buy" else "매도"
                report_sections.append(f"- 주문 실패: {action_type} {failed_order.get('ticker')} - {failed_order.get('error')}")
            
            report_sections.append("")
        
        # 8. 시스템 상태
        report_sections.append("## 🔧 시스템 상태")
        workflow_id = state.get("workflow_id", "N/A")
        start_time = state.get("start_time", "N/A")
        report_sections.append(f"- **워크플로우 ID**: {workflow_id}")
        report_sections.append(f"- **시작 시간**: {start_time}")
        report_sections.append(f"- **Phase**: 2 (운영 그래프)")
        report_sections.append("")
        
        report_sections.append("---")
        report_sections.append("*AI 트레이딩 시스템 by LangGraph*")
        
        # 최종 보고서 조합
        final_report = "\n".join(report_sections)
        
        print(f"  ✅ 기록 및 보고 완료")
        print(f"     💾 저장된 거래: {saved_count}건")
        print(f"     📊 보고서 길이: {len(final_report)}자")
        
        return {
            **state,
            "final_report": final_report,
            "current_node": "reporting"
        }
        
    except Exception as e:
        error_msg = f"기록 및 보고 실패: {str(e)}"
        print(f"  ❌ {error_msg}")
        return add_error(state, error_msg)