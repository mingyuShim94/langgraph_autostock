#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 트레이딩 시스템 메인 실행 스크립트

Phase 2 운영 그래프의 메인 진입점으로, 다양한 실행 모드를 제공합니다:
- 단발성 실행: 즉시 1회 트레이딩 워크플로우 실행
- 스케줄 실행: 정해진 시간에 자동 실행 (향후 확장)
- 테스트 모드: 안전한 검증 실행
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.trading_graph.workflow import run_trading_workflow, get_workflow_visualization


def main():
    """메인 함수 - 명령행 인자 처리 및 워크플로우 실행"""
    
    # 명령행 인자 파서 설정
    parser = argparse.ArgumentParser(
        description="AI 트레이딩 시스템 운영 그래프 실행",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
실행 예시:
  python src/trading_graph/main.py                    # 기본 실행 (모의투자 + Mock)
  python src/trading_graph/main.py --env paper        # 모의투자 환경
  python src/trading_graph/main.py --env prod --live  # 실전투자 환경
  python src/trading_graph/main.py --test             # 테스트 모드
  python src/trading_graph/main.py --viz              # 워크플로우 시각화만 출력
        """
    )
    
    parser.add_argument(
        "--env", 
        choices=["paper", "prod"],
        default="paper",
        help="거래 환경 (paper: 모의투자, prod: 실전투자, 기본값: paper)"
    )
    
    parser.add_argument(
        "--live",
        action="store_true", 
        help="실제 API 모드 (기본값: Mock 모드)"
    )
    
    parser.add_argument(
        "--test",
        action="store_true",
        help="테스트 모드 - 실행 전 안전성 검증"
    )
    
    parser.add_argument(
        "--viz",
        action="store_true",
        help="워크플로우 시각화만 출력하고 종료"
    )
    
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="최소한의 출력만 표시"
    )
    
    args = parser.parse_args()
    
    # 워크플로우 시각화만 요청된 경우
    if args.viz:
        print(get_workflow_visualization())
        return
    
    # 실행 환경 및 모드 설정
    environment = args.env
    mock_mode = not args.live
    verbose = not args.quiet
    
    # 환경 안전성 검증
    if args.test:
        print("🧪 테스트 모드 실행")
        print("=" * 60)
        result = run_test_mode(environment, mock_mode, verbose)
        sys.exit(0 if result else 1)
    
    # 실전 환경 경고
    if environment == "prod" and not mock_mode:
        if not confirm_production_execution():
            print("❌ 실전 실행이 취소되었습니다.")
            sys.exit(1)
    
    # 워크플로우 실행
    print("🚀 AI 트레이딩 시스템 실행")
    print("=" * 60)
    print(f"🏢 환경: {environment.upper()}")
    print(f"🔧 모드: {'Mock' if mock_mode else 'Live'}")
    print(f"⏰ 시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    try:
        result = run_trading_workflow(
            environment=environment,
            mock_mode=mock_mode,
            verbose=verbose
        )
        
        # 실행 결과에 따른 종료 코드
        if result["success"]:
            print("\n🎉 트레이딩 워크플로우 실행 완료!")
            if result["orders_executed"] > 0:
                print(f"⚡ {result['orders_executed']}건의 주문이 실행되었습니다.")
            sys.exit(0)
        else:
            print("\n💥 트레이딩 워크플로우 실행 실패!")
            if result.get("fatal_error"):
                print(f"🚨 치명적 오류: {result['fatal_error']}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⏹️ 사용자에 의해 실행이 중단되었습니다.")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 예상치 못한 오류 발생: {str(e)}")
        sys.exit(1)


def confirm_production_execution() -> bool:
    """실전 환경 실행 확인"""
    print("\n" + "⚠️" * 20)
    print("🚨 **실전 투자 환경 실행 경고** 🚨")
    print("⚠️" * 20)
    print()
    print("실제 자금이 투입되는 거래가 실행됩니다!")
    print("다음 사항을 확인했는지 점검해주세요:")
    print()
    print("✅ 충분한 테스트를 완료했습니까?")
    print("✅ 투자 금액과 리스크를 이해했습니까?")
    print("✅ 시스템 로직을 검토했습니까?") 
    print("✅ 비상 상황 대응 계획이 있습니까?")
    print()
    
    while True:
        response = input("정말로 실전 환경에서 실행하시겠습니까? (yes/no): ").strip().lower()
        
        if response in ["yes", "y"]:
            print("\n✅ 실전 환경 실행을 확인했습니다.")
            return True
        elif response in ["no", "n"]:
            return False
        else:
            print("❌ 'yes' 또는 'no'로 답해주세요.")


def run_test_mode(environment: str, mock_mode: bool, verbose: bool) -> bool:
    """
    테스트 모드 실행 - 안전성 검증
    
    Returns:
        bool: 테스트 성공 여부
    """
    print("🔍 시스템 구성 요소 점검...")
    
    test_results = []
    
    # 1. 필수 모듈 임포트 테스트
    print("\n1️⃣ 모듈 임포트 테스트")
    try:
        from src.kis_client.client import get_kis_client
        from src.database.schema import db_manager
        from src.trading_graph.nodes import fetch_portfolio_status
        print("   ✅ 모든 핵심 모듈 임포트 성공")
        test_results.append(True)
    except Exception as e:
        print(f"   ❌ 모듈 임포트 실패: {e}")
        test_results.append(False)
    
    # 2. KIS 클라이언트 연결 테스트
    print("\n2️⃣ KIS 클라이언트 연결 테스트")
    try:
        client = get_kis_client(environment=environment, mock_mode=True)  # 테스트는 항상 Mock
        balance = client.get_account_balance()
        print(f"   ✅ KIS 클라이언트 연결 성공 (잔고: {balance.get('total_cash', 0):,}원)")
        test_results.append(True)
    except Exception as e:
        print(f"   ❌ KIS 클라이언트 연결 실패: {e}")
        test_results.append(False)
    
    # 3. 데이터베이스 연결 테스트
    print("\n3️⃣ 데이터베이스 연결 테스트")
    try:
        stats = db_manager.get_trade_statistics()
        print(f"   ✅ 데이터베이스 연결 성공 (총 거래: {stats.get('total_trades', 0)}건)")
        test_results.append(True)
    except Exception as e:
        print(f"   ❌ 데이터베이스 연결 실패: {e}")
        test_results.append(False)
    
    # 4. 워크플로우 구성 테스트
    print("\n4️⃣ 워크플로우 구성 테스트")
    try:
        from src.trading_graph.workflow import create_trading_workflow
        workflow = create_trading_workflow()
        compiled = workflow.compile()
        print("   ✅ 워크플로우 구성 성공")
        test_results.append(True)
    except Exception as e:
        print(f"   ❌ 워크플로우 구성 실패: {e}")
        test_results.append(False)
    
    # 5. 프롬프트 파일 존재 확인
    print("\n5️⃣ 프롬프트 파일 확인")
    try:
        prompt_path = Path("prompts/core_decision_prompt.md")
        if prompt_path.exists():
            with open(prompt_path, 'r', encoding='utf-8') as f:
                content = f.read()
            print(f"   ✅ 프롬프트 파일 존재 ({len(content)}자)")
            test_results.append(True)
        else:
            print("   ❌ 프롬프트 파일이 존재하지 않습니다")
            test_results.append(False)
    except Exception as e:
        print(f"   ❌ 프롬프트 파일 확인 실패: {e}")
        test_results.append(False)
    
    # 테스트 결과 요약
    passed_tests = sum(test_results)
    total_tests = len(test_results)
    success_rate = (passed_tests / total_tests) * 100
    
    print("\n" + "=" * 60)
    print("🧪 테스트 결과 요약")
    print("=" * 60)
    print(f"📊 통과: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
    
    if passed_tests == total_tests:
        print("🎉 모든 테스트 통과! 시스템이 정상 작동합니다.")
        print("✅ 실제 워크플로우 실행 준비 완료")
        return True
    else:
        print("⚠️ 일부 테스트 실패. 문제를 해결한 후 다시 시도해주세요.")
        print("❌ 실제 워크플로우 실행을 권장하지 않습니다.")
        return False


if __name__ == "__main__":
    main()