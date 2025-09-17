# KIS API 설정 가이드

LV1 Observer에서 한국투자증권(KIS) API를 사용하기 위한 설정 가이드입니다.

## 1. KIS API 계정 신청

### 1.1 한국투자증권 계정 필요사항
- 한국투자증권 계좌 (실계좌 또는 모의투자 계좌)
- 한국투자증권 HTS ID
- 휴대폰 본인인증

### 1.2 KIS Developers 포털 접속
1. [KIS API 포털](https://apiportal.koreainvestment.com/) 접속
2. 회원가입 및 로그인
3. 서비스 신청 → Open API 서비스 신청

### 1.3 앱 등록 및 키 발급
1. **실전투자용 앱**: 실제 계좌 연동용
   - 앱 이름: `LV1_Observer_Prod`
   - 서비스 구분: 실전투자
   - 계좌권한: 잔고조회, 주문 등

2. **모의투자용 앱**: 개발 및 테스트용
   - 앱 이름: `LV1_Observer_Paper`
   - 서비스 구분: 모의투자
   - 계좌권한: 잔고조회, 주문 등

### 1.4 발급받을 정보
- **실전투자**: App Key, App Secret
- **모의투자**: App Key, App Secret
- **HTS ID**: 웹소켓 연결시 필요
- **계좌번호**: 8자리 + 2자리 (예: 12345678-01)

## 2. 환경변수 설정

### 2.1 .env 파일 수정
프로젝트 루트의 `.env` 파일을 열고 다음 값들을 설정:

```bash
# 개발 단계에서는 모의투자로 시작 (안전)
KIS_ENVIRONMENT=paper

# 실전투자 정보 (나중에 실제 사용시)
KIS_APP_KEY=실전투자_앱키
KIS_APP_SECRET=실전투자_앱시크릿
KIS_ACCOUNT_NUMBER=실전계좌번호_8자리
KIS_ACCOUNT_PRODUCT=01

# 모의투자 정보 (개발 및 테스트용)
KIS_PAPER_APP_KEY=모의투자_앱키
KIS_PAPER_APP_SECRET=모의투자_앱시크릿
KIS_PAPER_ACCOUNT_NUMBER=모의투자계좌번호_8자리

# 기타 정보
KIS_HTS_ID=HTS_사용자ID
```

### 2.2 계좌번호 형식
- **전체 계좌번호**: 12345678-01
- **8자리 부분**: 12345678 (KIS_ACCOUNT_NUMBER에 입력)
- **2자리 부분**: 01 (KIS_ACCOUNT_PRODUCT에 입력)

#### 계좌 상품 코드
- `01`: 종합계좌 (주식투자)
- `03`: 국내선물옵션
- `08`: 해외선물옵션
- `22`: 개인연금저축
- `29`: 퇴직연금

## 3. 설정 검증 테스트

### 3.1 기본 설정 확인
```python
from config.settings import settings

# 설정 로드 테스트
config = settings.get_kis_config()
print("KIS 설정:", config['my_app'][:10] + "...")  # 앱키 일부만 표시
```

### 3.2 환경 전환 테스트
```python
# 모의투자 환경 (기본값)
os.environ['KIS_ENVIRONMENT'] = 'paper'

# 실전투자 환경 (주의!)
os.environ['KIS_ENVIRONMENT'] = 'prod'
```

## 4. 보안 고려사항

### 4.1 중요 정보 보호
- `.env` 파일은 `.gitignore`에 포함되어 Git에 커밋되지 않음
- 앱키와 앱시크릿은 절대 공개하지 말 것
- 실전투자는 충분한 테스트 후에만 사용

### 4.2 단계별 접근
1. **1단계**: 모의투자로 모든 기능 테스트
2. **2단계**: 실전투자 소액으로 검증
3. **3단계**: 실제 운영 시작

### 4.3 토큰 관리
- API 토큰은 자동으로 발급 및 갱신됨
- 토큰 유효기간: 24시간
- 토큰은 별도 파일에 안전하게 저장됨

## 5. 자주 발생하는 문제

### 5.1 인증 실패
```
Error: Get Authentification token fail!
```
**해결방법**: 앱키, 앱시크릿이 올바른지 확인

### 5.2 계좌번호 오류
```
Error: 계좌번호 형식 오류
```
**해결방법**: 8자리-2자리 형식 확인

### 5.3 권한 부족
```
Error: 접근 권한이 없습니다
```
**해결방법**: API 서비스 신청 시 필요한 권한 선택했는지 확인

## 6. 다음 단계

설정이 완료되면:
1. Phase 1.3: 기본 인증 테스트 진행
2. Phase 2.1: 포트폴리오 조회 API 테스트
3. Phase 2.2: 종목 시세 조회 API 테스트

## 참고 자료

- [KIS API 공식 문서](https://apiportal.koreainvestment.com/)
- [GitHub 샘플 코드](https://github.com/koreainvestment/open-trading-api)
- [LV1 Observer 계획서](../prompts/lv1_plan.md)