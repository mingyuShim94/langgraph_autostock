"""
KIS API 설정 검증 스크립트
API 키 발급 전/후 설정 상태 확인
"""
import os
import sys
from typing import Dict, List, Tuple

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config.settings import settings


class KISConfigValidator:
    """KIS API 설정 검증 클래스"""

    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.success_items: List[str] = []

    def validate_all(self) -> Dict[str, any]:
        """전체 설정 검증"""
        print("🔍 KIS API 설정 검증 시작...\n")

        # 기본 설정 검증
        self._validate_basic_settings()

        # 환경변수 검증
        self._validate_environment_variables()

        # GitHub 호환성 검증
        self._validate_github_compatibility()

        # API 키 상태 확인
        self._check_api_key_status()

        # 결과 출력
        self._print_results()

        return {
            'is_valid': len(self.errors) == 0,
            'errors': self.errors,
            'warnings': self.warnings,
            'success_count': len(self.success_items)
        }

    def _validate_basic_settings(self):
        """기본 설정 검증"""
        print("📋 1. 기본 설정 검증")

        # Settings 클래스 로드 확인
        try:
            assert hasattr(settings, 'KIS_ENVIRONMENT')
            self.success_items.append("Settings 클래스 로드 성공")
        except Exception as e:
            self.errors.append(f"Settings 클래스 로드 실패: {e}")

        # 기본 환경 설정 확인
        try:
            env = settings.KIS_ENVIRONMENT
            if env in ['paper', 'prod']:
                self.success_items.append(f"환경 설정 유효: {env}")
            else:
                self.warnings.append(f"환경 설정 값 확인 필요: {env}")
        except Exception as e:
            self.errors.append(f"환경 설정 확인 실패: {e}")

        # URL 설정 확인
        urls_to_check = [
            ('KIS_PROD_URL', settings.KIS_PROD_URL),
            ('KIS_PAPER_URL', settings.KIS_PAPER_URL)
        ]

        for name, url in urls_to_check:
            if url and 'openapi' in url:
                self.success_items.append(f"{name} 설정 유효")
            else:
                self.errors.append(f"{name} 설정 오류: {url}")

        print("   ✅ 기본 설정 검증 완료\n")

    def _validate_environment_variables(self):
        """환경변수 검증"""
        print("🔧 2. 환경변수 검증")

        # 필수 환경변수 목록
        required_vars = [
            'KIS_ENVIRONMENT',
            'KIS_ACCOUNT_PRODUCT'
        ]

        # 조건부 필수 환경변수 (API 키가 설정되어 있을 때만)
        conditional_vars = [
            'KIS_APP_KEY',
            'KIS_APP_SECRET',
            'KIS_PAPER_APP_KEY',
            'KIS_PAPER_APP_SECRET',
            'KIS_ACCOUNT_NUMBER',
            'KIS_PAPER_ACCOUNT_NUMBER',
            'KIS_HTS_ID'
        ]

        # 필수 환경변수 확인
        for var in required_vars:
            value = getattr(settings, var, None)
            if value and value != f"your_{var.lower()}_here":
                self.success_items.append(f"{var} 설정됨")
            else:
                self.errors.append(f"{var} 미설정 또는 기본값")

        # 조건부 환경변수 확인
        api_keys_set = []
        for var in conditional_vars:
            value = getattr(settings, var, None)
            if value and not value.startswith('your_'):
                api_keys_set.append(var)
                self.success_items.append(f"{var} 설정됨")
            else:
                self.warnings.append(f"{var} 미설정 (API 키 발급 후 설정 필요)")

        # API 키 설정 상태 요약
        if len(api_keys_set) == 0:
            self.warnings.append("모든 API 키 미설정 - 개발 모드로 동작")
        elif len(api_keys_set) < len(conditional_vars):
            self.warnings.append("일부 API 키만 설정됨 - 설정 완료 필요")
        else:
            self.success_items.append("모든 API 키 설정 완료")

        print("   ✅ 환경변수 검증 완료\n")

    def _validate_github_compatibility(self):
        """GitHub 호환성 검증"""
        print("🔗 3. GitHub 호환성 검증")

        try:
            # get_kis_config() 메서드 테스트
            config = settings.get_kis_config()

            # GitHub 필수 키 확인
            github_required_keys = [
                'my_app', 'my_sec', 'paper_app', 'paper_sec',
                'my_acct_stock', 'my_paper_stock', 'my_prod',
                'prod', 'vps', 'my_agent'
            ]

            missing_keys = []
            for key in github_required_keys:
                if key not in config:
                    missing_keys.append(key)

            if len(missing_keys) == 0:
                self.success_items.append("GitHub 호환 설정 완전함")
            else:
                self.errors.append(f"GitHub 호환 설정 누락: {missing_keys}")

            # 환경별 설정 전환 테스트
            paper_config = settings.get_kis_config()
            if paper_config['my_app'] == paper_config['paper_app']:
                self.success_items.append("모의투자 환경 설정 정상")
            else:
                self.warnings.append("모의투자 환경 설정 확인 필요")

        except Exception as e:
            self.errors.append(f"GitHub 호환성 검증 실패: {e}")

        print("   ✅ GitHub 호환성 검증 완료\n")

    def _check_api_key_status(self):
        """API 키 상태 확인"""
        print("🔑 4. API 키 상태 확인")

        api_key_status = {
            '실전투자 앱키': settings.KIS_APP_KEY,
            '실전투자 앱시크릿': settings.KIS_APP_SECRET,
            '모의투자 앱키': settings.KIS_PAPER_APP_KEY,
            '모의투자 앱시크릿': settings.KIS_PAPER_APP_SECRET,
            '실전 계좌번호': settings.KIS_ACCOUNT_NUMBER,
            '모의 계좌번호': settings.KIS_PAPER_ACCOUNT_NUMBER,
            'HTS ID': settings.KIS_HTS_ID
        }

        configured_keys = []
        unconfigured_keys = []

        for name, value in api_key_status.items():
            if value and not value.startswith('your_') and value.strip():
                configured_keys.append(name)
                # 보안을 위해 일부만 표시
                masked_value = f"{value[:8]}..." if len(value) > 8 else "***"
                self.success_items.append(f"{name}: {masked_value}")
            else:
                unconfigured_keys.append(name)

        if len(unconfigured_keys) > 0:
            self.warnings.append(f"미설정 API 정보: {', '.join(unconfigured_keys)}")

        # API 키 발급 상태에 따른 안내
        if len(configured_keys) == 0:
            print("   ⚠️  모든 API 키가 미설정 상태입니다.")
            print("   📝 KIS API 포털에서 앱키 발급 후 .env 파일 업데이트 필요")
        elif len(configured_keys) < len(api_key_status):
            print("   ⚠️  일부 API 키만 설정되어 있습니다.")
            print("   📝 누락된 키들을 .env 파일에 추가해주세요.")
        else:
            print("   ✅ 모든 API 키가 설정되어 있습니다.")

        print("   ✅ API 키 상태 확인 완료\n")

    def _print_results(self):
        """검증 결과 출력"""
        print("=" * 60)
        print("📊 KIS API 설정 검증 결과")
        print("=" * 60)

        # 성공 항목
        if self.success_items:
            print(f"✅ 성공 ({len(self.success_items)}개):")
            for item in self.success_items:
                print(f"   • {item}")
            print()

        # 경고 항목
        if self.warnings:
            print(f"⚠️  경고 ({len(self.warnings)}개):")
            for warning in self.warnings:
                print(f"   • {warning}")
            print()

        # 오류 항목
        if self.errors:
            print(f"❌ 오류 ({len(self.errors)}개):")
            for error in self.errors:
                print(f"   • {error}")
            print()

        # 전체 상태
        if len(self.errors) == 0:
            print("🎉 설정 검증 완료! API 키 발급 후 즉시 사용 가능합니다.")
        else:
            print("⚠️  설정 오류가 있습니다. 수정 후 재검증해주세요.")

        print()

    def get_next_steps(self) -> List[str]:
        """다음 단계 안내"""
        steps = []

        if len(self.errors) > 0:
            steps.append("1. 설정 오류 수정")
            steps.append("2. 설정 재검증")

        # API 키 상태에 따른 안내
        unconfigured_count = len([w for w in self.warnings if 'API' in w or '키' in w])

        if unconfigured_count > 0:
            steps.extend([
                "3. KIS API 포털에서 앱키 발급",
                "4. .env 파일에 발급받은 키 설정",
                "5. Phase 1.4 - 실제 API 연결 테스트"
            ])
        else:
            steps.extend([
                "3. Phase 1.4 - 실제 API 연결 테스트",
                "4. Phase 2.1 - 포트폴리오 조회 테스트"
            ])

        return steps


def main():
    """메인 실행 함수"""
    validator = KISConfigValidator()
    result = validator.validate_all()

    # 다음 단계 안내
    next_steps = validator.get_next_steps()
    if next_steps:
        print("📋 다음 단계:")
        for step in next_steps:
            print(f"   {step}")
        print()

    return result


if __name__ == "__main__":
    main()