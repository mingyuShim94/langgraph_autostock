# 🚀 Streamlit 대시보드 빠른 시작 가이드

## 🎯 문제가 해결되었습니다!

**이전 문제**: `uv add`로 설치했지만 패키지를 찾지 못함  
**해결 완료**: ✅ Python 버전 수정 및 uv 환경 최적화

---

## 📋 즉시 실행 방법

### 🥇 방법 1: 수정된 스크립트 사용 (추천)

```bash
# 1. 의존성 확인 (이미 설치됨)
python run_dashboard.py --check-deps

# 2. 대시보드 실행
python run_dashboard.py

# 3. 브라우저 접속
# http://localhost:8501
```

### 🥈 방법 2: 직접 uv run 사용

```bash
# uv 환경에서 직접 실행
uv run streamlit run src/streamlit_dashboard/main.py --server.port 8501
```

### 🥉 방법 3: 문제 발생시 대안

```bash
# 가상환경 활성화 후 실행
source .venv/bin/activate
streamlit run src/streamlit_dashboard/main.py --server.port 8501
```

---

## 🔧 해결된 문제들

### ✅ 1. Python 버전 불일치 해결
- **이전**: `requires-python = ">=3.13"` 
- **수정**: `requires-python = ">=3.12"` (현재 시스템 3.12.3에 맞춤)

### ✅ 2. uv 환경 재설정 완료
```bash
uv sync --reinstall  # 96개 패키지 재설치 완료
```

### ✅ 3. 실행 스크립트 개선
- `run_dashboard.py`가 uv 환경 자동 감지
- `uv run` 명령어로 올바른 환경에서 실행

### ✅ 4. 전체 검증 완료
- **단위 테스트**: 7/7 통과 ✅
- **의존성 확인**: streamlit, plotly, pandas, numpy 모두 설치됨 ✅
- **파일 구조**: 6개 페이지 모두 존재 ✅

---

## 📊 대시보드 구성

접속 후 다음 페이지들을 이용할 수 있습니다:

- 🏠 **시스템 개요**: 전체 상태 및 핵심 지표
- 🤖 **에이전트 성과**: AI 에이전트별 성과 분석  
- 🧠 **LLM 사용량**: API 사용량 및 비용 추적
- 💰 **비용 분석**: ROI 분석 및 예산 관리
- 📊 **거래 히스토리**: 거래 기록 및 포트폴리오
- ⚙️ **시스템 관리**: 설정 및 제어 패널

---

## 🚨 혹시 문제가 발생한다면

### 1. 의존성 재확인
```bash
python run_dashboard.py --check-deps
```

### 2. uv 환경 상태 확인
```bash
uv pip list | grep -E "(streamlit|plotly|pandas|numpy)"
```

### 3. 직접 import 테스트
```bash
uv run python -c "import streamlit, plotly, pandas, numpy; print('All OK!')"
```

### 4. 최종 수단 - 완전 재설치
```bash
uv cache clean
rm -rf .venv
uv sync
```

---

## 📞 추가 지원

상세한 설치 가이드: `docs/dashboard_installation_guide.md`  
문제 해결이 안되면 해당 문서를 참조하세요.

---

**🎉 이제 완전히 작동하는 Streamlit 대시보드를 사용할 수 있습니다!**