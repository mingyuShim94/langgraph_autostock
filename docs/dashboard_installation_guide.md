# 🚀 Streamlit 대시보드 설치 및 실행 가이드

## 🎯 문제 해결: uv 환경에서 패키지 인식 오류

**문제**: `uv add`로 패키지를 설치했지만 Python이 패키지를 찾지 못하는 경우

**원인**: Python 버전 불일치 및 가상환경 경로 문제

## 📋 해결 방법 (권장 순서)

### 방법 1: uv 환경 수정 (권장)

#### 1단계: Python 버전 수정
```bash
# pyproject.toml 파일에서 requires-python 확인
cat pyproject.toml | grep requires-python

# 현재 Python 버전 확인  
python --version

# 버전이 맞지 않으면 pyproject.toml 수정
# requires-python = ">=3.12" (현재 시스템에 맞게)
```

#### 2단계: uv 환경 재설정
```bash
# 의존성 재동기화
uv sync --reinstall

# 설치된 패키지 확인
uv pip list
```

#### 3단계: uv run으로 실행
```bash
# uv 환경에서 대시보드 실행
python run_dashboard.py

# 또는 직접 uv run 사용
uv run streamlit run src/streamlit_dashboard/main.py
```

### 방법 2: 가상환경 + pip 사용

#### 1단계: 가상환경 생성
```bash
# 새 가상환경 생성
python -m venv dashboard_env

# 가상환경 활성화 (macOS/Linux)
source dashboard_env/bin/activate

# 가상환경 활성화 (Windows)
dashboard_env\Scripts\activate
```

#### 2단계: 의존성 설치
```bash
# pip로 패키지 설치
pip install streamlit plotly pandas numpy altair streamlit-autorefresh

# 또는 requirements.txt 사용
pip install -r requirements.txt
```

#### 3단계: 대시보드 실행
```bash
# 가상환경에서 직접 실행
streamlit run src/streamlit_dashboard/main.py --server.port 8501
```

### 방법 3: conda 환경 사용

#### 1단계: conda 환경 생성
```bash
# 새 conda 환경 생성
conda create -n langgraph-dashboard python=3.12

# 환경 활성화
conda activate langgraph-dashboard
```

#### 2단계: 패키지 설치
```bash
# conda-forge에서 설치
conda install -c conda-forge streamlit plotly pandas numpy

# pip로 추가 패키지 설치
pip install altair streamlit-autorefresh
```

#### 3단계: 대시보드 실행
```bash
# conda 환경에서 실행
streamlit run src/streamlit_dashboard/main.py
```

## 🔧 문제 진단 명령어

### uv 환경 상태 확인
```bash
# uv 버전 확인
uv --version

# 프로젝트 상태 확인
uv sync --dry-run

# 설치된 패키지 목록
uv pip list

# 가상환경 경로 확인
uv venv --preview
```

### Python 환경 확인
```bash
# 현재 Python 경로
which python

# Python 버전
python --version

# 패키지 경로 확인
python -c "import sys; print('\n'.join(sys.path))"

# 개별 패키지 확인
python -c "import streamlit; print(streamlit.__file__)"
```

## 🚨 일반적인 오류 및 해결책

### 오류 1: ModuleNotFoundError
```bash
ModuleNotFoundError: No module named 'streamlit'
```

**해결책**:
```bash
# uv 환경에서 실행하도록 수정
uv run python run_dashboard.py

# 또는 가상환경 활성화 후 실행
source .venv/bin/activate
python run_dashboard.py
```

### 오류 2: Python 버전 불일치
```bash
ERROR: Python 3.13 is required
```

**해결책**:
```bash
# pyproject.toml 수정
requires-python = ">=3.12"

# 환경 재설정
uv sync --reinstall
```

### 오류 3: 권한 오류
```bash
Permission denied: '/usr/local/lib/python3.x/site-packages'
```

**해결책**:
```bash
# 가상환경 사용 (uv 또는 venv)
uv venv
source .venv/bin/activate

# 또는 사용자 설치
pip install --user streamlit plotly pandas numpy
```

## 📋 실행 방법 요약

### 🥇 추천: uv 방법
```bash
# 1. 환경 준비
uv sync

# 2. 대시보드 실행
python run_dashboard.py
# 또는
uv run streamlit run src/streamlit_dashboard/main.py
```

### 🥈 대안 1: 직접 실행
```bash
# 1. 패키지 확인
python -c "import streamlit, plotly, pandas, numpy; print('All packages available')"

# 2. 직접 실행
streamlit run src/streamlit_dashboard/main.py --server.port 8501
```

### 🥉 대안 2: 가상환경
```bash
# 1. 가상환경 생성 및 활성화
python -m venv dashboard_env
source dashboard_env/bin/activate  # macOS/Linux
# dashboard_env\Scripts\activate  # Windows

# 2. 패키지 설치
pip install streamlit plotly pandas numpy altair

# 3. 실행
streamlit run src/streamlit_dashboard/main.py
```

## 🔗 브라우저 접속

대시보드가 성공적으로 시작되면:

```
🚀 http://localhost:8501
```

## 📞 추가 지원

문제가 지속될 경우:

1. **환경 정보 수집**:
   ```bash
   python --version
   uv --version
   pip list | grep -E "(streamlit|plotly|pandas|numpy)"
   ```

2. **로그 확인**:
   ```bash
   python run_dashboard.py --check-deps
   ```

3. **최종 수단 - 완전 재설치**:
   ```bash
   # uv 캐시 정리
   uv cache clean
   
   # 가상환경 삭제 후 재생성
   rm -rf .venv
   uv sync
   ```