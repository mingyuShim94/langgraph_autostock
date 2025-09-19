#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 트레이딩 시스템 운영 그래프 워크플로우

LangGraph를 활용한 6개 노드의 자율 트레이딩 워크플로우 구성:
포트폴리오 진단 → 시장 분석 → AI 의사결정 → 리스크 검증 → 주문 실행 → 기록 보고
"""

import uuid
from datetime import datetime
from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, START, END

# 프로젝트 모듈 임포트
from src.trading_graph.state import TradingState, get_state_summary
from src.trading_graph.nodes import (
    fetch_portfolio_status,
    analyze_market_conditions, 
    generate_trading_plan,
    validate_trading_plan,
    execute_trading_plan,
    record_and_report
)


def risk_validation_router(state: TradingState) -> Literal["execute_trading_plan", "record_and_report"]:
    """
    리스크 검증 결과에 따른 조건부 라우팅
    
    - 검증 통과: 주문 실행으로 진행
    - 검증 실패: 주문 실행 건너뛰고 바로 보고로 진행
    """
    risk_validation = state.get("risk_validation")
    
    if risk_validation and risk_validation.get("is_valid", False):
        print("🟢 리스크 검증 통과 → 주문 실행 진행")
        return "execute_trading_plan"
    else:
        print("🔴 리스크 검증 실패 → 주문 실행 건너뛰고 보고 진행")
        return "record_and_report"


def create_trading_workflow() -> StateGraph:
    """
    운영 그래프 워크플로우 생성
    
    Returns:
        StateGraph: 컴파일 준비된 LangGraph 워크플로우
    """
    print("🏗️ 운영 그래프 워크플로우 생성 중...")
    
    # StateGraph 초기화
    workflow = StateGraph(TradingState)
    
    # 노드 추가
    print("  📊 노드 등록 중...")
    workflow.add_node("fetch_portfolio_status", fetch_portfolio_status)
    workflow.add_node("analyze_market_conditions", analyze_market_conditions)
    workflow.add_node("generate_trading_plan", generate_trading_plan)
    workflow.add_node("validate_trading_plan", validate_trading_plan)
    workflow.add_node("execute_trading_plan", execute_trading_plan)
    workflow.add_node("record_and_report", record_and_report)
    
    # 엣지 연결
    print("  🔗 노드 연결 중...")
    
    # 순차적 실행 엣지
    workflow.add_edge(START, "fetch_portfolio_status")
    workflow.add_edge("fetch_portfolio_status", "analyze_market_conditions")
    workflow.add_edge("analyze_market_conditions", "generate_trading_plan")
    workflow.add_edge("generate_trading_plan", "validate_trading_plan")
    
    # 조건부 엣지: 리스크 검증 결과에 따른 분기
    workflow.add_conditional_edges(
        "validate_trading_plan",
        risk_validation_router,
        {
            "execute_trading_plan": "execute_trading_plan",
            "record_and_report": "record_and_report"
        }
    )
    
    # 주문 실행 → 보고
    workflow.add_edge("execute_trading_plan", "record_and_report")
    
    # 보고 → 종료
    workflow.add_edge("record_and_report", END)
    
    print("  ✅ 워크플로우 생성 완료")
    print("     📋 노드 6개, 엣지 7개 (조건부 엣지 1개 포함)")
    
    return workflow


def initialize_trading_state(
    environment: str = "paper", 
    mock_mode: bool = True,
    workflow_id: str = None
) -> TradingState:
    """
    트레이딩 워크플로우 초기 상태 생성
    
    Args:
        environment: 거래 환경 ("paper" 또는 "prod")
        mock_mode: 모의 모드 여부
        workflow_id: 워크플로우 고유 ID (None이면 자동 생성)
    
    Returns:
        TradingState: 초기화된 상태 객체
    """
    if workflow_id is None:
        workflow_id = f"trade_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
    
    initial_state: TradingState = {
        # 노드별 실행 결과 (초기값 None)
        "portfolio_status": None,
        "market_analysis": None,
        "trading_plan": None,
        "risk_validation": None,
        "execution_result": None,
        "final_report": None,
        
        # 메타데이터
        "workflow_id": workflow_id,
        "start_time": datetime.now().isoformat(),
        "current_node": "initialized",
        "errors": [],
        
        # 설정 정보
        "environment": environment,
        "mock_mode": mock_mode
    }
    
    return initial_state


def run_trading_workflow(
    environment: str = "paper",
    mock_mode: bool = True,
    verbose: bool = True
) -> Dict[str, Any]:
    """
    완전한 트레이딩 워크플로우 실행
    
    Args:
        environment: 거래 환경 ("paper" 또는 "prod")
        mock_mode: 모의 모드 여부
        verbose: 상세 로그 출력 여부
    
    Returns:
        Dict: 실행 결과 및 상태 정보
    """
    print("🚀 AI 트레이딩 시스템 운영 그래프 실행 시작")
    print("=" * 80)
    
    try:
        # 1. 워크플로우 생성 및 컴파일
        if verbose:
            print("1️⃣ 워크플로우 초기화...")
        
        workflow = create_trading_workflow()
        compiled_workflow = workflow.compile()
        
        # 2. 초기 상태 설정
        if verbose:
            print("2️⃣ 초기 상태 설정...")
        
        initial_state = initialize_trading_state(
            environment=environment,
            mock_mode=mock_mode
        )
        
        workflow_id = initial_state["workflow_id"]
        start_time = initial_state["start_time"]
        
        if verbose:
            print(f"   🆔 워크플로우 ID: {workflow_id}")
            print(f"   ⏰ 시작 시간: {start_time}")
            print(f"   🏢 환경: {environment} {'(Mock)' if mock_mode else '(Live)'}")
            print()
        
        # 3. 워크플로우 실행
        if verbose:
            print("3️⃣ 워크플로우 실행...")
            print("-" * 40)
        
        final_state = compiled_workflow.invoke(initial_state)
        
        # 4. 실행 결과 분석
        if verbose:
            print("-" * 40)
            print("4️⃣ 실행 결과 분석...")
        
        execution_time = (
            datetime.now() - datetime.fromisoformat(start_time)
        ).total_seconds()
        
        # 성공 여부 판단
        errors = final_state.get("errors", [])
        has_errors = len(errors) > 0
        
        execution_result = final_state.get("execution_result")
        orders_executed = execution_result.get("total_executed", 0) if execution_result else 0
        
        # 결과 요약
        result_summary = {
            "success": not has_errors,
            "workflow_id": workflow_id,
            "execution_time_seconds": execution_time,
            "environment": environment,
            "mock_mode": mock_mode,
            "orders_executed": orders_executed,
            "errors_count": len(errors),
            "final_state": final_state
        }
        
        if verbose:
            print()
            print("📊 실행 결과 요약")
            print("-" * 40)
            print(f"   ✅ 성공 여부: {'성공' if result_summary['success'] else '실패'}")
            print(f"   ⏱️ 실행 시간: {execution_time:.1f}초")
            print(f"   ⚡ 실행된 주문: {orders_executed}건")
            print(f"   ❌ 오류 개수: {len(errors)}건")
            
            if errors:
                print("   🚨 발생한 오류:")
                for i, error in enumerate(errors, 1):
                    print(f"      {i}. {error}")
            
            print()
            print("🎯 상태 요약")
            print("-" * 40)
            print(f"   {get_state_summary(final_state)}")
            
            # 최종 보고서가 있다면 출력
            final_report = final_state.get("final_report")
            if final_report:
                print()
                print("📝 최종 보고서")
                print("=" * 80)
                print(final_report)
        
        return result_summary
        
    except Exception as e:
        error_msg = f"워크플로우 실행 중 치명적 오류: {str(e)}"
        print(f"💥 {error_msg}")
        
        return {
            "success": False,
            "workflow_id": None,
            "execution_time_seconds": 0,
            "environment": environment,
            "mock_mode": mock_mode,
            "orders_executed": 0,
            "errors_count": 1,
            "fatal_error": error_msg,
            "final_state": None
        }


def get_workflow_visualization() -> str:
    """
    워크플로우 구조를 텍스트로 시각화
    
    Returns:
        str: ASCII 아트 형태의 워크플로우 다이어그램
    """
    diagram = """
🚀 AI 트레이딩 시스템 운영 그래프 워크플로우

    START
      ↓
┌─────────────────────┐
│ 1️⃣ Portfolio Status │  ← 포트폴리오 진단
│  (계좌 + 주식잔고)    │
└─────────────────────┘
      ↓
┌─────────────────────┐
│ 2️⃣ Market Analysis  │  ← 시장 분석
│  (시세 + 거래량)      │
└─────────────────────┘
      ↓
┌─────────────────────┐
│ 3️⃣ Trading Plan     │  ← AI 의사결정
│  (GPT-4 의사결정)    │
└─────────────────────┘
      ↓
┌─────────────────────┐
│ 4️⃣ Risk Validation  │  ← 리스크 검증
│  (안전성 검증)       │
└─────────────────────┘
      ↓
    검증 통과?
   ✅ YES │ ❌ NO
      ↓   │
┌─────────────────────┐ │
│ 5️⃣ Order Execution  │ │  ← 주문 실행
│  (실제 매매)         │ │
└─────────────────────┘ │
      ↓                │
      └────────────────┘
      ↓
┌─────────────────────┐
│ 6️⃣ Record & Report  │  ← 기록 및 보고
│  (DB 저장 + 보고서)   │
└─────────────────────┘
      ↓
     END

🔄 총 6개 노드, 조건부 분기 1개
⚡ 예상 실행 시간: 30-60초
🛡️ 리스크 검증으로 안전성 보장
"""
    return diagram


if __name__ == "__main__":
    # 워크플로우 시각화 출력
    print(get_workflow_visualization())
    
    # 기본 실행 (모의 모드)
    print("\n" + "=" * 80)
    result = run_trading_workflow(
        environment="paper",
        mock_mode=True,
        verbose=True
    )
    
    print("\n" + "=" * 80)
    print(f"🎯 최종 결과: {'✅ 성공' if result['success'] else '❌ 실패'}")
    print(f"📊 워크플로우 ID: {result['workflow_id']}")
    print(f"⏱️ 실행 시간: {result['execution_time_seconds']:.1f}초")