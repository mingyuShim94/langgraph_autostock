#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
실시간 성과 대시보드 API 서버 실행 스크립트
"""

import sys
from pathlib import Path

# 프로젝트 루트 경로 추가
sys.path.append(str(Path(__file__).parent))

from src.dashboard.api_endpoints import create_dashboard_api
from src.dashboard.dashboard_data_pipeline import PipelineConfig


def main():
    print("🚀 실시간 성과 대시보드 API 서버 시작")
    print("🔗 주요 엔드포인트:")
    print("   http://localhost:8080/api/health - 헬스 체크")
    print("   http://localhost:8080/api/metrics/realtime - 실시간 메트릭")
    print("   http://localhost:8080/api/system/overview - 시스템 개요")
    print("   http://localhost:8080/api/agents/ranking - 에이전트 순위")
    print("   http://localhost:8080/api/llm/usage - LLM 사용량")
    print("   http://localhost:8080/api/cost/efficiency - 비용 효율성")
    print("\n🛑 중지: Ctrl+C\n")
    
    try:
        # API 서버 생성 및 실행
        api = create_dashboard_api(
            host="localhost",
            port=8080,
            debug=True
        )
        
        # 서버 실행
        api.run(use_reloader=False)  # reloader 비활성화로 안정성 향상
        
    except KeyboardInterrupt:
        print("\n🛑 서버가 중지되었습니다.")
    except Exception as e:
        print(f"❌ 서버 오류: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()