#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Streamlit 대시보드 시스템 테스트

LangGraph 자율 트레이딩 시스템의 Streamlit 대시보드 전체 기능을 테스트합니다.
"""

import os
import sys
import unittest
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

class TestDashboardComponents(unittest.TestCase):
    """대시보드 컴포넌트 테스트"""
    
    def test_dashboard_utils_import(self):
        """대시보드 유틸리티 모듈 임포트 테스트"""
        try:
            from src.streamlit_dashboard.utils.dashboard_utils import (
                format_currency, format_percentage
            )
            self.assertTrue(True, "Dashboard utils imported successfully")
        except ImportError as e:
            self.fail(f"Failed to import dashboard utils: {e}")
    
    def test_chart_helpers_import(self):
        """차트 헬퍼 모듈 임포트 테스트"""
        try:
            from src.streamlit_dashboard.utils.chart_helpers import (
                create_line_chart, create_bar_chart, COLOR_PALETTE
            )
            self.assertTrue(True, "Chart helpers imported successfully")
        except ImportError as e:
            self.fail(f"Failed to import chart helpers: {e}")
    
    def test_metrics_cards_import(self):
        """메트릭 카드 컴포넌트 임포트 테스트"""
        try:
            from src.streamlit_dashboard.components.metrics_cards import (
                FinancialMetricCard, PercentageMetricCard, CountMetricCard
            )
            self.assertTrue(True, "Metrics cards imported successfully")
        except ImportError as e:
            self.fail(f"Failed to import metrics cards: {e}")

class TestUtilityFunctions(unittest.TestCase):
    """유틸리티 함수 테스트"""
    
    def test_format_currency(self):
        """통화 포맷 함수 테스트"""
        try:
            from src.streamlit_dashboard.utils.dashboard_utils import format_currency
            
            result = format_currency(1234.56, "USD")
            self.assertEqual(result, "$1,234.56")
            
        except Exception as e:
            self.fail(f"Currency formatting failed: {e}")
    
    def test_format_percentage(self):
        """백분율 포맷 함수 테스트"""
        try:
            from src.streamlit_dashboard.utils.dashboard_utils import format_percentage
            
            result = format_percentage(0.1234)
            self.assertEqual(result, "12.34%")
            
        except Exception as e:
            self.fail(f"Percentage formatting failed: {e}")

class TestPageStructure(unittest.TestCase):
    """페이지 구조 테스트"""
    
    def test_all_pages_exist(self):
        """모든 페이지 파일 존재 확인"""
        pages_dir = project_root / "src" / "streamlit_dashboard" / "pages"
        
        expected_pages = [
            "01_🏠_시스템_개요.py",
            "02_🤖_에이전트_성과.py", 
            "03_🧠_LLM_사용량.py",
            "04_💰_비용_분석.py",
            "05_📊_거래_히스토리.py",
            "06_⚙️_시스템_관리.py"
        ]
        
        for page in expected_pages:
            page_path = pages_dir / page
            self.assertTrue(
                page_path.exists(), 
                f"Page file missing: {page}"
            )
    
    def test_main_app_exists(self):
        """메인 앱 파일 존재 확인"""
        main_app_path = project_root / "src" / "streamlit_dashboard" / "main.py"
        self.assertTrue(main_app_path.exists(), "Main app file missing")

def run_integration_test():
    """통합 테스트 실행"""
    print("🧪 Streamlit 대시보드 통합 테스트 시작")
    print("=" * 50)
    
    try:
        # 1. 환경 변수 설정 테스트
        print("1️⃣ 환경 설정 테스트...")
        os.environ['TESTING'] = 'true'
        
        # 2. 모든 페이지 파일 확인
        print("2️⃣ 페이지 파일 확인...")
        pages_dir = project_root / "src" / "streamlit_dashboard" / "pages"
        
        page_count = 0
        for page_file in pages_dir.glob("*.py"):
            if page_file.stem.startswith("0"):
                try:
                    with open(page_file, 'r', encoding='utf-8') as f:
                        compile(f.read(), page_file, 'exec')
                    print(f"   ✅ {page_file.name}")
                    page_count += 1
                except SyntaxError as e:
                    print(f"   ❌ {page_file.name}: {e}")
                    return False
        
        print(f"   총 {page_count}개 페이지 확인 완료")
        
        # 3. 유틸리티 모듈 테스트
        print("3️⃣ 유틸리티 모듈 테스트...")
        from src.streamlit_dashboard.utils import dashboard_utils, chart_helpers
        from src.streamlit_dashboard.components import metrics_cards
        print("   ✅ 모든 유틸리티 모듈 로드 성공")
        
        # 4. 데이터 생성 테스트
        print("4️⃣ 데이터 생성 테스트...")
        
        test_data = pd.DataFrame({
            'date': pd.date_range(start='2024-01-01', periods=30),
            'value': np.random.cumsum(np.random.randn(30))
        })
        print(f"   ✅ 테스트 데이터 생성: {len(test_data)} 행")
        
        print("\n✅ 모든 통합 테스트 통과!")
        return True
        
    except Exception as e:
        print(f"\n❌ 통합 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """메인 테스트 실행 함수"""
    
    print("🧪 LangGraph Streamlit 대시보드 테스트")
    print("=" * 50)
    
    # 단위 테스트 실행
    print("\n📋 단위 테스트 실행:")
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    test_classes = [
        TestDashboardComponents,
        TestUtilityFunctions, 
        TestPageStructure
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print(f"\n📊 단위 테스트 결과:")
    print(f"   실행: {result.testsRun}")
    print(f"   성공: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"   실패: {len(result.failures)}")
    print(f"   오류: {len(result.errors)}")
    
    # 통합 테스트 실행
    print(f"\n🔧 통합 테스트:")
    integration_success = run_integration_test()
    
    overall_success = (result.wasSuccessful() and integration_success)
    
    print(f"\n🎯 전체 결과: {'✅ 성공' if overall_success else '❌ 실패'}")
    
    return overall_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)