# 자율 AI 트레이딩 시스템

스스로 학습하고 개선하는 LangGraph 기반 자율적 AI 트레이딩 시스템

## 🎯 프로젝트 개요

이 시스템은 한국투자증권 KIS API를 활용하여 실시간 포트폴리오 관리와 매매를 실행하며, 자신의 투자 결정 결과를 분석하여 지속적으로 학습하고 개선하는 AI 트레이딩 시스템입니다.

### 핵심 구성요소
- **운영 그래프 (Trading Graph)**: 실시간 포트폴리오 관리 및 매매 실행
- **성찰 그래프 (Reflection Graph)**: 과거 데이터 분석을 통한 시스템 학습 및 개선  
- **거래 데이터베이스**: 모든 학습의 근간이 되는 중앙 기억 장치

## 🚀 빠른 시작

### 1. 환경 설정

```bash
# 의존성 설치
cd open-trading-api-main
uv sync

# KIS API 설정
mkdir -p ~/KIS/config
# ~/KIS/config/kis_devlp.yaml 파일에 API 키 설정
```

### 2. LLM API 키 설정

```bash
# .env 파일 생성
cp .env.example .env

# .env 파일에 실제 API 키들을 입력
nano .env
```

필수 LLM API 키들:
- `ANTHROPIC_API_KEY` (Claude)
- `OPENAI_API_KEY` (GPT)  
- `GOOGLE_AI_API_KEY` (Gemini)
- `PERPLEXITY_API_KEY` (Perplexity)

### 3. 시스템 테스트

```bash
# LLM 클라이언트 통합 테스트
uv run python test_llm_clients.py

# KIS API 연결 테스트
python test_kis_auth.py
```

### 4. 개발 진행 상황 확인

현재 진행 상황은 [개발 로드맵](docs/development_roadmap.md)에서 확인할 수 있습니다.

## 📁 프로젝트 구조

```
langgraph_study/
├── open-trading-api-main/         # KIS API 라이브러리
├── src/                           # 메인 소스코드
│   ├── trading_graph/            # 운영 그래프 (6개 노드)
│   ├── reflection_graph/         # 성찰 그래프 (4개 노드)
│   ├── database/                 # SQLite 데이터베이스
│   ├── kis_client/              # KIS API 클라이언트
│   └── utils/                   # 공통 유틸리티
├── prompts/                      # AI 프롬프트 관리
├── data/                        # 데이터 저장소
├── logs/                        # 로그 파일
├── tests/                       # 테스트 코드
└── docs/                        # 문서
    ├── plan/                    # 개발 계획서들
    ├── development_roadmap.md   # 개발 로드맵
    ├── kis_api_implementation_guide.md  # KIS API 구현 가이드
    └── all_architecture.md      # 전체 시스템 아키텍처
```

## 📋 개발 단계

### 🎯 하이브리드 LLM 전략

| 에이전트 | LLM 모델 | 용도 |
|---------|---------|------|
| **CIO Agent** | Claude Opus 4.1 | 최종 의사결정 및 종합 분석 |
| **Technical Analyst** | GPT-5 | 차트 분석 및 기술적 지표 |
| **Sector Researcher** | Perplexity sonar-pro | 실시간 시장 리서치 |
| **Valuation Analyst** | Gemini 2.5 Flash | 펀더멘털 분석 |

### 📊 진행 상황

- **Phase 1.1**: 하이브리드 LLM 인프라 구축 ✅ **완료 (15.5%)**
  - 다중 LLM 클라이언트 통합
  - GPT-5 및 Claude 4 최신 모델 지원
  - 에이전트별 최적화된 모델 매핑
  - 비용 추적 및 성능 모니터링

- **Phase 1.2**: 중앙 데이터베이스 확장 🔄 **다음 단계**
- **Phase 2**: 전문가 팀 기반 운영 그래프 (9개 노드)
- **Phase 3**: 성찰 및 자기 개조 그래프 (5개 노드)
- **Phase 4**: 통합 테스트 및 검증
- **Phase 5**: 프로덕션 배포

자세한 내용은 [상세 개발 계획서](docs/plan/claude_detailed_development_plan(0919).md) 참조

## ⚠️ 주의사항

- **모의투자 우선**: 충분한 테스트 없이 실전 투자 금지
- **API 키 보안**: API 키 및 계좌 정보 절대 노출 금지
- **백업**: 모든 거래 데이터 안전하게 보관

## 📄 라이선스

이 프로젝트는 개인 학습 및 연구 목적으로 작성되었습니다.