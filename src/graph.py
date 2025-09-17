"""
LV1 Observer - 기본 그래프 구조
LangGraph를 사용한 기본 워크플로우를 정의합니다.
"""
import uuid
from datetime import datetime
from typing import Dict, Any
from langgraph.graph import StateGraph, END
from .state import ObserverState, create_initial_state

# 노드 함수들 (현재는 스텁으로 구현)
def fetch_portfolio_status(state: ObserverState) -> ObserverState:
    """
    노드 1: 계좌 상태 조회
    증권사 API를 통해 포트폴리오 정보를 조회합니다.
    """
    print(f"📊 [{state['execution_id']}] 계좌 상태 조회 시작...")

    try:
        # 현재 단계 업데이트
        state["current_step"] = "fetching_portfolio"

        # KIS API를 통한 실제 포트폴리오 조회
        from .kis_client import fetch_portfolio_status as kis_fetch_portfolio, KISAPIError

        print("   💼 KIS API 연결...")
        print("   📈 포트폴리오 정보 조회...")

        # 설정에서 환경 정보 가져오기 (기본값: paper)
        environment = state.get("config", {}).get("environment", "paper")

        # KIS API 호출
        portfolio_data = kis_fetch_portfolio(environment)

        print(f"   ✅ 포트폴리오 데이터 수집 완료")
        print(f"      - 총자산: {portfolio_data.total_asset:,.0f}원")
        print(f"      - 현금잔고: {portfolio_data.cash_balance:,.0f}원")
        print(f"      - 보유종목: {len(portfolio_data.stocks)}개")

        # 상태 업데이트
        from .state import update_portfolio_status
        state = update_portfolio_status(state, portfolio_data)

        return state

    except KISAPIError as e:
        print(f"   ❌ KIS API 오류: {e.message}")
        state["error_message"] = f"KIS API 오류: {e.message}"
        state["current_step"] = "portfolio_fetch_error"
        state["status"] = "error"
        return state
    except Exception as e:
        print(f"   ❌ 계좌 상태 조회 실패: {e}")
        state["error_message"] = f"계좌 상태 조회 실패: {e}"
        state["current_step"] = "portfolio_fetch_error"
        state["status"] = "error"
        return state

def collect_news_data(state: ObserverState) -> ObserverState:
    """
    노드 2: 뉴스 수집
    보유 종목에 대한 최신 뉴스를 수집합니다.
    """
    print(f"📰 [{state['execution_id']}] 뉴스 데이터 수집 시작...")

    try:
        # 현재 단계 업데이트
        state["current_step"] = "collecting_news"

        # TODO: 실제 뉴스 API 호출 로직 구현
        # 현재는 목업 데이터로 대체
        print("   🔍 뉴스 API 연결...")
        print("   📝 보유 종목별 뉴스 검색...")
        print("   📊 뉴스 데이터 정제 및 분류...")
        print("   ✅ 뉴스 데이터 수집 완료")

        # 임시: 빈 뉴스 데이터로 설정
        # 실제 구현시에는 API 응답을 파싱하여 NewsData 객체 생성
        state["news_data"] = None  # Phase 4에서 구현 예정
        state["current_step"] = "news_collected"

        return state

    except Exception as e:
        print(f"   ❌ 뉴스 수집 실패: {e}")
        state["error_message"] = f"뉴스 수집 실패: {e}"
        state["current_step"] = "news_collection_error"
        state["status"] = "error"
        return state

def generate_daily_report(state: ObserverState) -> ObserverState:
    """
    노드 3: 결과 요약 및 보고
    수집된 데이터를 분석하여 일일 브리핑 리포트를 생성합니다.
    """
    print(f"📋 [{state['execution_id']}] 일일 리포트 생성 시작...")

    try:
        # 현재 단계 업데이트
        state["current_step"] = "generating_report"

        # TODO: 실제 LLM 기반 분석 및 리포트 생성 로직 구현
        # 현재는 목업 데이터로 대체
        print("   🤖 LLM 분석 시작...")
        print("   📈 포트폴리오 분석...")
        print("   📰 뉴스 영향도 분석...")
        print("   📄 브리핑 리포트 생성...")
        print("   ✅ 일일 리포트 생성 완료")

        # 임시: 빈 리포트로 설정
        # 실제 구현시에는 LLM 응답을 파싱하여 DailyReport 객체 생성
        state["daily_report"] = None  # Phase 5에서 구현 예정
        state["current_step"] = "report_generated"
        state["status"] = "completed"

        return state

    except Exception as e:
        print(f"   ❌ 리포트 생성 실패: {e}")
        state["error_message"] = f"리포트 생성 실패: {e}"
        state["current_step"] = "report_generation_error"
        state["status"] = "error"
        return state

# 조건부 라우팅 함수 (현재는 단순한 순차 진행)
def should_continue_to_news(state: ObserverState) -> str:
    """포트폴리오 조회 후 뉴스 수집으로 진행할지 결정"""
    if state["status"] == "error":
        return END
    return "collect_news"

def should_continue_to_report(state: ObserverState) -> str:
    """뉴스 수집 후 리포트 생성으로 진행할지 결정"""
    if state["status"] == "error":
        return END
    return "generate_report"

def should_end(state: ObserverState) -> str:
    """리포트 생성 후 종료 결정"""
    return END

# 그래프 생성 함수
def create_observer_graph() -> StateGraph:
    """LV1 Observer 그래프를 생성합니다."""

    # StateGraph 객체 생성
    workflow = StateGraph(ObserverState)

    # 노드 추가
    workflow.add_node("fetch_portfolio", fetch_portfolio_status)
    workflow.add_node("collect_news", collect_news_data)
    workflow.add_node("generate_report", generate_daily_report)

    # 엣지 연결 (순차적 흐름)
    workflow.set_entry_point("fetch_portfolio")

    # 조건부 엣지 추가
    workflow.add_conditional_edges(
        "fetch_portfolio",
        should_continue_to_news,
        {
            "collect_news": "collect_news",
            END: END
        }
    )

    workflow.add_conditional_edges(
        "collect_news",
        should_continue_to_report,
        {
            "generate_report": "generate_report",
            END: END
        }
    )

    workflow.add_conditional_edges(
        "generate_report",
        should_end,
        {
            END: END
        }
    )

    return workflow

# 그래프 실행 함수
def run_observer(config: Dict[str, Any] = None) -> ObserverState:
    """
    LV1 Observer를 실행합니다.

    Args:
        config: 실행 설정 (선택사항)

    Returns:
        ObserverState: 실행 결과 상태
    """
    # 실행 ID 생성
    execution_id = str(uuid.uuid4())[:8]

    print("=" * 60)
    print(f"🚀 LV1 Observer 실행 시작 (ID: {execution_id})")
    print(f"⏰ 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    try:
        # 그래프 생성 및 컴파일
        workflow = create_observer_graph()
        app = workflow.compile()

        # 초기 상태 생성
        initial_state = create_initial_state(execution_id, config)

        # 그래프 실행
        result = app.invoke(initial_state)

        # 실행 결과 출력
        print("\n" + "=" * 60)
        print("📊 실행 결과 요약")
        print("=" * 60)
        print(f"실행 ID: {result['execution_id']}")
        print(f"상태: {result['status']}")
        print(f"현재 단계: {result['current_step']}")

        if result['status'] == 'error':
            print(f"오류 메시지: {result['error_message']}")
        else:
            print("✅ 모든 단계가 성공적으로 완료되었습니다!")

        # 실행 시간 계산
        execution_time = datetime.now() - result['start_time']
        print(f"실행 시간: {execution_time.total_seconds():.2f}초")

        return result

    except Exception as e:
        print(f"\n❌ 그래프 실행 중 예외 발생: {e}")
        # 오류 상태 반환
        error_state = create_initial_state(execution_id, config)
        error_state["status"] = "error"
        error_state["error_message"] = str(e)
        error_state["current_step"] = "graph_execution_error"
        return error_state

# 메인 실행 함수 (테스트용)
if __name__ == "__main__":
    # 기본 설정으로 Observer 실행
    result = run_observer()

    # 결과에 따른 종료 코드 설정
    if result["status"] == "completed":
        exit(0)
    else:
        exit(1)