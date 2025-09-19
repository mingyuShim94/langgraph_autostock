#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Streamlit 대시보드 실행 스크립트

LangGraph 자율 트레이딩 시스템의 Streamlit 대시보드를 실행합니다.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

def setup_environment():
    """환경 설정"""
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    print("✅ 환경 설정 완료")
    return True

def check_dependencies():
    """의존성 확인"""
    required_packages = ['streamlit', 'plotly', 'pandas', 'numpy']
    missing_packages = []
    
    # uv 환경에서 패키지 확인
    try:
        import subprocess
        result = subprocess.run(['uv', 'pip', 'list'], capture_output=True, text=True)
        installed_packages = result.stdout.lower()
        
        for package in required_packages:
            if package.lower() in installed_packages:
                print(f"✅ {package} 설치됨 (uv 환경)")
            else:
                missing_packages.append(package)
                print(f"❌ {package} 누락")
    except Exception:
        # fallback: 직접 import 시도
        for package in required_packages:
            try:
                __import__(package)
                print(f"✅ {package} 설치됨")
            except ImportError:
                missing_packages.append(package)
                print(f"❌ {package} 누락")
    
    if missing_packages:
        print(f"\n다음 명령어로 설치하세요:")
        print(f"uv sync  # 또는")
        print(f"uv add {' '.join(missing_packages)}")
        return False
    
    return True

def run_dashboard(port=8501):
    """대시보드 실행"""
    app_path = "src/streamlit_dashboard/main.py"
    
    if not os.path.exists(app_path):
        print(f"❌ Streamlit 앱이 없습니다: {app_path}")
        return False
    
    # uv 환경에서 streamlit 실행
    cmd = [
        "uv", "run", "streamlit", "run", app_path,
        "--server.port", str(port),
        "--server.address", "localhost"
    ]
    
    print(f"🚀 uv 환경에서 대시보드 시작: http://localhost:{port}")
    print(f"실행 명령: {' '.join(cmd)}")
    
    try:
        subprocess.run(cmd)
    except FileNotFoundError:
        print("❌ uv 또는 Streamlit이 설치되지 않았습니다.")
        print("설치 명령: uv sync")
        return False
    except Exception as e:
        print(f"❌ 실행 오류: {e}")
        return False
    
    return True

def main():
    parser = argparse.ArgumentParser(description="LangGraph 트레이딩 대시보드")
    parser.add_argument("--port", "-p", type=int, default=8501, help="포트 번호")
    parser.add_argument("--check-deps", action="store_true", help="의존성 확인")
    
    args = parser.parse_args()
    
    if args.check_deps:
        if check_dependencies():
            print("✅ 모든 의존성이 설치되어 있습니다.")
        return
    
    print("🚀 LangGraph 트레이딩 대시보드")
    print("=" * 40)
    
    if not setup_environment():
        sys.exit(1)
    
    if not check_dependencies():
        sys.exit(1)
    
    if not run_dashboard(args.port):
        sys.exit(1)

if __name__ == "__main__":
    main()