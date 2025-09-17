# API 설정 가이드

LV1 Observer 시스템을 위한 필수 API 설정 방법을 안내합니다.

## 1. OpenAI API 설정

### 1.1 API 키 발급
1. [OpenAI 웹사이트](https://platform.openai.com/) 접속
2. 회원가입 또는 로그인
3. API Keys 메뉴에서 새 API 키 생성
4. 생성된 키를 안전하게 보관

### 1.2 환경변수 설정
`.env` 파일에서 다음 값을 수정:
```bash
OPENAI_API_KEY=sk-your_actual_openai_api_key_here
```

## 2. 한국투자증권 KIS API 설정

### 2.1 API 신청
1. [한국투자증권 API 포털](https://apiportal.koreainvestment.com/) 접속
2. 회원가입 및 본인인증
3. 앱 등록 (모의투자용 또는 실투자용)
4. APP KEY, APP SECRET 발급

### 2.2 환경변수 설정
`.env` 파일에서 다음 값들을 수정:
```bash
KIS_APP_KEY=your_actual_kis_app_key_here
KIS_APP_SECRET=your_actual_kis_app_secret_here
KIS_ACCOUNT_NUMBER=your_account_number_here
```

### 2.3 주의사항
- **모의투자 계좌** 사용을 강력히 권장
- 실계좌 사용시 소액으로 테스트
- API 호출 한도 확인 (일일 제한)

## 3. 네이버 뉴스 API 설정

### 3.1 API 신청
1. [네이버 개발자 센터](https://developers.naver.com/apps/) 접속
2. 네이버 아이디로 로그인
3. 애플리케이션 등록
4. 검색 API 사용 설정
5. Client ID, Client Secret 발급

### 3.2 환경변수 설정
`.env` 파일에서 다음 값들을 수정:
```bash
NAVER_CLIENT_ID=your_actual_naver_client_id_here
NAVER_CLIENT_SECRET=your_actual_naver_client_secret_here
```

## 4. 설정 완료 후 테스트

API 키 설정 완료 후 다음 명령으로 연결 테스트:

```bash
# 가상환경 활성화
source venv/bin/activate

# API 연결 테스트 실행
python tests/test_api_connection.py
```

모든 API가 정상 연결되면 다음 단계로 진행할 수 있습니다.

## 5. 보안 주의사항

- **절대** API 키를 git에 커밋하지 마세요
- `.env` 파일은 `.gitignore`에 포함되어 있습니다
- API 키는 안전한 곳에 별도 보관
- 주기적으로 API 키 로테이션 권장

## 6. 문제 해결

### 6.1 OpenAI API 오류
- API 키 형식 확인 (sk-로 시작)
- 계정 잔액 확인
- API 제한 사항 확인

### 6.2 KIS API 오류
- 앱 승인 상태 확인
- 계좌번호 형식 확인
- 시장 시간 및 휴일 확인

### 6.3 네이버 뉴스 API 오류
- 애플리케이션 승인 상태 확인
- 일일 호출 제한 확인
- 요청 파라미터 형식 확인

---

**중요**: 모든 API 키 설정이 완료된 후에만 다음 Phase로 진행하세요.