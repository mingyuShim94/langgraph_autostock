# KIS API 구현 가이드
> `docs/all_architecture.md` 자율 트레이딩 시스템 구현을 위한 KIS 증권 API 사용법 종합 가이드

## 🎯 개요

이 문서는 `docs/all_architecture.md`에 정의된 **자율적 AI 트레이딩 시스템**을 KIS(한국투자증권) API로 실제 구현하기 위한 완전한 가이드입니다. 

### 아키텍처 핵심 구성요소
- **운영 그래프 (Trading Graph)**: 실시간 포트폴리오 관리 및 매매 실행
- **성찰 그래프 (Reflection Graph)**: 과거 데이터 분석을 통한 시스템 학습 및 개선
- **거래 데이터베이스**: 모든 학습의 근간이 되는 중앙 기억 장치

---

## 📋 목차

1. [환경 설정 및 사전 준비](#1-환경-설정-및-사전-준비)
2. [인증 시스템 구현](#2-인증-시스템-구현)
3. [운영 그래프 API 매핑](#3-운영-그래프-api-매핑)
4. [성찰 그래프 API 매핑](#4-성찰-그래프-api-매핑)
5. [거래 데이터베이스 스키마 매핑](#5-거래-데이터베이스-스키마-매핑)
6. [웹소켓 실시간 데이터](#6-웹소켓-실시간-데이터)
7. [실제 구현 예제](#7-실제-구현-예제)
8. [에러 처리 및 베스트 프랙티스](#8-에러-처리-및-베스트-프랙티스)

---

## 1. 환경 설정 및 사전 준비

### 1.1 시스템 요구사항

```bash
# Python 환경 요구사항
Python 3.9 이상 필요
uv 패키지 매니저 사용 권장 (빠르고 간편한 의존성 관리)
```

### 1.2 uv 패키지 매니저 설치

한국투자증권 GitHub에서 권장하는 uv를 사용하여 의존성을 관리합니다.

```bash
# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# 설치 확인
uv --version
# uv 0.x.x ... -> 설치 완료
```

### 1.3 프로젝트 설정

```bash
# KIS Open API 샘플 코드 저장소 클론
git clone https://github.com/koreainvestment/open-trading-api
cd open-trading-api/kis_github

# uv를 사용한 의존성 설치 - 한줄로 끝
uv sync
```

### 1.4 KIS Open API 서비스 신청

🍀 **[서비스 신청 안내 바로가기](https://kis-developers.com)**

1. **한국투자증권 계좌 개설** 및 ID 연결
2. **한국투자증권 홈페이지** or 앱에서 Open API 서비스 신청
3. **앱키(App Key), 앱시크릿(App Secret)** 발급
4. **모의투자 및 실전투자** 앱키 각각 준비

### 1.5 kis_devlp.yaml 설정

프로젝트 루트에 위치한 `kis_devlp.yaml` 파일을 본인의 계정 정보로 수정합니다.

```yaml
# 실전투자
my_app: "여기에 실전투자 앱키 입력"
my_sec: "여기에 실전투자 앱시크릿 입력"

# 모의투자
paper_app: "여기에 모의투자 앱키 입력"
paper_sec: "여기에 모의투자 앱시크릿 입력"

# HTS ID(KIS Developers 고객 ID) - 체결통보, 나의 조건 목록 확인 등에 사용
my_htsid: "사용자 HTS ID"

# 계좌번호 앞 8자리
my_acct_stock: "증권계좌 8자리"
my_acct_future: "선물옵션계좌 8자리"
my_paper_stock: "모의투자 증권계좌 8자리"
my_paper_future: "모의투자 선물옵션계좌 8자리"

# 계좌번호 뒤 2자리
my_prod: "01" # 종합계좌
# my_prod: "03" # 국내선물옵션 계좌
# my_prod: "08" # 해외선물옵션 계좌
# my_prod: "22" # 연금저축 계좌
# my_prod: "29" # 퇴직연금 계좌

# User-Agent(기본값 사용 권장, 변경 불필요)
my_agent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
```

### 1.6 kis_auth.py 설정 경로 수정

`kis_auth.py`의 `config_root` 경로를 본인 환경에 맞게 수정합니다. 발급된 토큰 파일이 저장될 경로로, 제3자가 찾기 어렵도록 설정하는 것을 권장합니다.

```python
# kis_auth.py 39번째 줄
# Windows - C:\Users\사용자이름\KIS\config
# Linux/macOS - /home/사용자이름/KIS/config
# config_root = os.path.join(os.path.expanduser("~"), "KIS", "config")
config_root = os.path.join(os.path.expanduser("~"), "폴더 경로", "config")
```

### 1.7 폴더 구조 이해

KIS Open API 샘플 코드는 두 가지 목적으로 구성되어 있습니다:

```
.
├── examples_llm/                  # LLM용 샘플 코드
│   ├── kis_auth.py              # 인증 공통 함수
│   └── domestic_stock           # 국내주식
│       └── inquire_price        # API 단일 기능별 폴더
│           ├── inquire_price.py         # 한줄 호출 파일
│           └── chk_inquire_price.py     # 테스트 파일
├── examples_user/                 # 사용자용 실제 사용 예제
│   ├── kis_auth.py              # 인증 공통 함수
│   └── domestic_stock           # 국내주식
│       ├── domestic_stock_functions.py        # 통합 함수 파일
│       ├── domestic_stock_examples.py         # 실행 예제 파일
│       ├── domestic_stock_functions_ws.py     # WebSocket 함수 파일
│       └── domestic_stock_examples_ws.py      # WebSocket 예제 파일
```

**📌 우리 프로젝트에서는 `examples_user/` 폴더의 코드를 기반으로 구현합니다.**

---

## 2. 인증 시스템 구현

### 2.1 기본 인증 설정

```python
import sys
import logging

# KIS API 샘플 코드 경로 추가
sys.path.extend(['..', '.', 'open-trading-api-main/examples_user'])

# KIS 인증 모듈 import
import kis_auth as ka

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 인증 초기화 (모의투자)
ka.auth(svr="vps", product="01")  # vps: 모의투자, prod: 실전투자
trenv = ka.getTREnv()

# 실전투자로 전환하려면
# ka.auth(svr="prod", product="01")
```

### 2.2 환경별 인증 설정

```python
def setup_kis_environment(env_type="demo", account_type="01"):
    """
    KIS API 환경 설정
    
    Args:
        env_type (str): "demo" (모의투자) 또는 "real" (실전투자)
        account_type (str): "01" (종합계좌), "03" (선물옵션), "08" (해외선물옵션)
    
    Returns:
        dict: 환경 정보
    """
    try:
        # 환경 매핑
        svr_mapping = {
            "demo": "vps",   # 모의투자 서버
            "real": "prod"   # 실전투자 서버
        }
        
        svr = svr_mapping.get(env_type, "vps")
        
        # KIS 인증
        ka.auth(svr=svr, product=account_type)
        trenv = ka.getTREnv()
        
        logger.info(f"KIS 환경 설정 완료: {env_type} 환경, 계좌유형: {account_type}")
        
        return {
            "environment": env_type,
            "server": svr,
            "account_type": account_type,
            "account_number": trenv.my_acct,
            "product_code": trenv.my_prod
        }
        
    except Exception as e:
        logger.error(f"KIS 환경 설정 실패: {str(e)}")
        raise
```

### 2.3 토큰 관리 및 재발급

```python
def setup_authentication(env_type="demo"):
    """
    KIS API 인증 설정 (토큰 자동 관리)
    
    Args:
        env_type (str): "demo" (모의투자) 또는 "real" (실전투자)
    
    Returns:
        dict: 인증 정보
    """
    try:
        # 환경 설정
        svr = "vps" if env_type == "demo" else "prod"
        
        # KIS 인증 (토큰 자동 발급/갱신)
        ka.auth(svr=svr, product="01")
        trenv = ka.getTREnv()
        
        logger.info(f"인증 완료: {env_type} 환경")
        
        return {
            "environment": env_type,
            "server": svr,
            "account_number": trenv.my_acct,
            "product_code": trenv.my_prod,
            "app_key": trenv.my_app,
            "app_secret": trenv.my_sec
        }
        
    except Exception as e:
        logger.error(f"인증 실패: {str(e)}")
        # 토큰 재발급 시도 (1분당 1회 제한)
        try:
            logger.info("토큰 재발급 시도 중...")
            ka.auth(svr=svr, product="01")
            return setup_authentication(env_type)
        except Exception as retry_error:
            logger.error(f"토큰 재발급 실패: {str(retry_error)}")
            raise

def refresh_token_if_needed():
    """
    토큰 만료 시 자동 재발급
    주의: 1분당 1회만 발급 가능
    """
    try:
        # 현재 환경 정보 가져오기
        trenv = ka.getTREnv()
        current_svr = "prod" if hasattr(trenv, 'prod') else "vps"
        
        # 토큰 재발급
        ka.auth(svr=current_svr, product="01")
        logger.info("토큰 재발급 성공")
        return True
        
    except Exception as e:
        logger.error(f"토큰 재발급 실패: {str(e)}")
        return False
```

### 2.4 WebSocket 인증 설정

```python
def setup_websocket_auth():
    """
    WebSocket 실시간 데이터용 인증 설정
    """
    try:
        # WebSocket 인증
        ka.auth_ws()
        logger.info("WebSocket 인증 완료")
        
        # WebSocket 클라이언트 생성
        kws = ka.KISWebSocket(api_url="/tryitout")
        
        return kws
        
    except Exception as e:
        logger.error(f"WebSocket 인증 실패: {str(e)}")
        raise
```

---

## 3. 운영 그래프 API 매핑

운영 그래프는 **실시간으로 시장에 대응하여 포트폴리오를 관리하고 매매를 실행**하는 핵심 엔진입니다.

### 3.1 노드 1: 포트폴리오 진단

**목적**: 현재 보유 종목, 수량, 평균 단가, 현금 예수금 등 계좌의 모든 정보를 조회

```python
from domestic_stock_functions import inquire_account_balance, inquire_balance

def fetch_portfolio_status():
    """
    아키텍처 노드 1: 포트폴리오 진단
    현재 계좌 상태를 완전히 파악
    """
    try:
        # 1. 계좌 자산 현황 조회 (현금, 총 자산 등)
        account_df, account_summary = inquire_account_balance(
            cano=trenv.my_acct,
            acnt_prdt_cd=trenv.my_prod
        )
        
        # 2. 주식 잔고 상세 조회 (보유 종목별 정보)
        holdings_df, holdings_summary = inquire_balance(
            env_dv="demo",  # 또는 "real"
            cano=trenv.my_acct,
            acnt_prdt_cd=trenv.my_prod,
            afhr_flpr_yn="N",    # 시간외단일가반영여부
            inqr_dvsn="01",      # 조회구분
            unpr_dvsn="01",      # 단가구분
            fund_sttl_icld_yn="N", # 펀드결제분포함여부
            fncg_amt_auto_rdpt_yn="N", # 융자금액자동상환여부
            prcs_dvsn="00"       # 처리구분
        )
        
        # 3. 포트폴리오 상태 구조화
        portfolio_status = {
            "cash_balance": float(account_summary.iloc[0]['dnca_tot_amt']),  # 예수금 총액
            "total_asset": float(account_summary.iloc[0]['tot_evlu_amt']),   # 총 평가금액
            "holdings": [],
            "timestamp": datetime.now().isoformat()
        }
        
        # 보유 종목 정보 추가
        for _, row in holdings_df.iterrows():
            if int(row['hldg_qty']) > 0:  # 보유수량이 있는 종목만
                portfolio_status["holdings"].append({
                    "ticker": row['pdno'],                    # 종목코드
                    "quantity": int(row['hldg_qty']),        # 보유수량
                    "avg_price": float(row['pchs_avg_pric']), # 평균취득단가
                    "current_price": float(row['prpr']),      # 현재가
                    "evaluation_amt": float(row['evlu_amt']), # 평가금액
                    "profit_loss": float(row['evlu_pfls_amt']) # 평가손익금액
                })
        
        return portfolio_status
        
    except Exception as e:
        logger.error(f"Portfolio fetch failed: {str(e)}")
        return None
```

### 3.2 노드 2: 시장 분석 및 기회/위험 탐색

**목적**: 현재 보유 자산 및 시장 전체 상황을 분석

```python
from domestic_stock_functions import inquire_price, inquire_ccnl, volume_rank, fluctuation

def analyze_market_conditions(portfolio_status):
    """
    아키텍처 노드 2: 시장 분석 및 기회/위험 탐색
    보유 종목 및 전체 시장 상황 분석
    """
    try:
        market_analysis = {
            "holdings_analysis": [],
            "market_opportunities": [],
            "market_risks": [],
            "timestamp": datetime.now().isoformat()
        }
        
        # 1. 보유 종목별 현재 시세 및 분석
        for holding in portfolio_status["holdings"]:
            ticker = holding["ticker"]
            
            # 현재가 시세 조회
            price_data = inquire_price(
                env_dv="demo",
                fid_cond_mrkt_div_code="J",
                fid_input_iscd=ticker
            )
            
            # 체결 정보 조회
            ccnl_data = inquire_ccnl(
                env_dv="demo",
                fid_cond_mrkt_div_code="J", 
                fid_input_iscd=ticker
            )
            
            holding_analysis = {
                "ticker": ticker,
                "current_price": float(price_data.iloc[0]['stck_prpr']),
                "change_rate": float(price_data.iloc[0]['prdy_ctrt']),
                "volume": int(price_data.iloc[0]['acml_vol']),
                "market_cap": float(price_data.iloc[0]['hts_avls']) if 'hts_avls' in price_data.columns else 0,
                "trading_strength": self._calculate_trading_strength(ccnl_data)
            }
            
            market_analysis["holdings_analysis"].append(holding_analysis)
        
        # 2. 시장 기회 탐색 - 거래량 급증 종목
        volume_leaders = volume_rank(
            fid_cond_mrkt_div_code="J",
            fid_cond_scr_div_code="20171",
            fid_input_iscd="0000",
            fid_div_cls_code="0",
            fid_blng_cls_code="0",
            fid_trgt_cls_code="111111111",
            fid_trgt_exls_cls_code="0000000000",
            fid_input_price_1="0",
            fid_input_price_2="1000000",
            fid_vol_cnt="100000",
            fid_input_date_1=""
        )
        
        # 상위 10개 종목을 기회로 분석
        for i, (_, row) in enumerate(volume_leaders.head(10).iterrows()):
            market_analysis["market_opportunities"].append({
                "rank": i + 1,
                "ticker": row['mksc_shrn_iscd'],
                "name": row['hts_kor_isnm'],
                "reason": f"거래량 급증 {row['acml_vol']}주",
                "change_rate": float(row['prdy_ctrt']),
                "volume_ratio": float(row['vol_tnrt']) if 'vol_tnrt' in row else 0
            })
        
        # 3. 시장 리스크 분석 - 급락 종목
        decline_stocks = fluctuation(
            fid_cond_mrkt_div_code="J",
            fid_cond_scr_div_code="20170",
            fid_input_iscd="0000",
            fid_rank_sort_cls_code="1",  # 하락률 순
            fid_input_cnt_1="0",
            fid_prc_cls_code="0",
            fid_input_price_1="",
            fid_input_price_2="",
            fid_vol_cnt="",
            fid_trgt_cls_code="0",
            fid_trgt_exls_cls_code="0",
            fid_div_cls_code="0",
            fid_rsfl_rate1="",
            fid_rsfl_rate2=""
        )
        
        # 하락률 상위 10개 종목을 리스크로 분석
        for i, (_, row) in enumerate(decline_stocks.head(10).iterrows()):
            market_analysis["market_risks"].append({
                "rank": i + 1,
                "ticker": row['mksc_shrn_iscd'],
                "name": row['hts_kor_isnm'],
                "reason": f"급락 {row['prdy_ctrt']}%",
                "change_rate": float(row['prdy_ctrt'])
            })
        
        return market_analysis
        
    except Exception as e:
        logger.error(f"Market analysis failed: {str(e)}")
        return None

def _calculate_trading_strength(ccnl_data):
    """체결 데이터를 바탕으로 거래 강도 계산"""
    if ccnl_data.empty:
        return 0.0
    
    # 간단한 체결강도 계산 로직
    total_volume = ccnl_data['cntg_vol'].astype(int).sum()
    buy_volume = ccnl_data[ccnl_data['cntg_vol'].astype(int) > 0]['cntg_vol'].astype(int).sum()
    
    if total_volume == 0:
        return 0.0
    
    return (buy_volume / total_volume) * 100
```

### 3.3 노드 3: 거래 계획 수립 (The Brain)

**목적**: 핵심 의사결정 프롬프트를 기반으로 구체적인 매매 계획 수립

```python
def generate_trading_plan(portfolio_status, market_analysis, decision_prompt):
    """
    아키텍처 노드 3: 거래 계획 수립 (The Brain)
    AI 의사결정을 통한 구체적 매매 계획 생성
    """
    try:
        # LLM에 전달할 컨텍스트 구성
        context = {
            "portfolio": portfolio_status,
            "market": market_analysis,
            "decision_rules": decision_prompt,
            "timestamp": datetime.now().isoformat()
        }
        
        # AI 의사결정 호출 (OpenAI API 사용)
        from openai import OpenAI
        client = OpenAI()
        
        prompt = f"""
        당신은 전문 펀드매니저입니다. 다음 정보를 바탕으로 구체적인 거래 계획을 수립하세요.
        
        현재 포트폴리오: {json.dumps(context['portfolio'], ensure_ascii=False, indent=2)}
        시장 분석: {json.dumps(context['market'], ensure_ascii=False, indent=2)}
        
        의사결정 규칙:
        {decision_prompt}
        
        다음 JSON 형식으로 거래 계획을 제시하세요:
        {{
            "actions": [
                {{
                    "type": "buy" or "sell",
                    "ticker": "종목코드",
                    "quantity": 수량,
                    "target_price": 목표가격,
                    "reason": "거래 이유"
                }}
            ],
            "justification": "전체적인 거래 결정 근거",
            "risk_assessment": "리스크 평가",
            "expected_outcome": "예상 결과"
        }}
        """
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        
        # AI 응답 파싱
        ai_decision = json.loads(response.choices[0].message.content)
        
        # 거래 계획 구조화
        trade_plan = {
            "actions": ai_decision.get("actions", []),
            "justification_text": ai_decision.get("justification", ""),
            "risk_assessment": ai_decision.get("risk_assessment", ""),
            "expected_outcome": ai_decision.get("expected_outcome", ""),
            "timestamp": datetime.now().isoformat(),
            "decision_context": context
        }
        
        return trade_plan
        
    except Exception as e:
        logger.error(f"Trading plan generation failed: {str(e)}")
        return None
```

### 3.4 노드 4: 최종 리스크 점검

**목적**: 수립된 계획의 실행 가능성 및 리스크 검증

```python
from domestic_stock_functions import inquire_psbl_order, inquire_psbl_sell

def validate_trading_plan(trade_plan, portfolio_status):
    """
    아키텍처 노드 4: 최종 리스크 점검
    거래 계획의 실행 가능성 검증
    """
    try:
        validation_results = {
            "is_valid": True,
            "validated_actions": [],
            "validation_errors": [],
            "timestamp": datetime.now().isoformat()
        }
        
        for action in trade_plan["actions"]:
            action_validation = {
                "action": action,
                "is_valid": True,
                "error_message": None,
                "adjusted_quantity": action["quantity"]
            }
            
            if action["type"] == "buy":
                # 매수 가능 금액 조회
                psbl_order = inquire_psbl_order(
                    env_dv="demo",
                    cano=trenv.my_acct,
                    acnt_prdt_cd=trenv.my_prod,
                    pdno=action["ticker"],
                    ord_unpr=str(action["target_price"]),
                    ord_dvsn="01",  # 지정가
                    cma_evlu_amt_icld_yn="N",
                    ovrs_icld_yn="N"
                )
                
                max_qty = int(psbl_order.iloc[0]['ord_psbl_qty'])
                if action["quantity"] > max_qty:
                    if max_qty > 0:
                        action_validation["adjusted_quantity"] = max_qty
                        action_validation["error_message"] = f"수량 조정: {action['quantity']} -> {max_qty}"
                    else:
                        action_validation["is_valid"] = False
                        action_validation["error_message"] = "매수 가능 금액 부족"
                        
            elif action["type"] == "sell":
                # 매도 가능 수량 조회
                psbl_sell = inquire_psbl_sell(
                    cano=trenv.my_acct,
                    acnt_prdt_cd=trenv.my_prod,
                    pdno=action["ticker"]
                )
                
                max_sell_qty = int(psbl_sell.iloc[0]['ord_psbl_qty'])
                if action["quantity"] > max_sell_qty:
                    if max_sell_qty > 0:
                        action_validation["adjusted_quantity"] = max_sell_qty
                        action_validation["error_message"] = f"수량 조정: {action['quantity']} -> {max_sell_qty}"
                    else:
                        action_validation["is_valid"] = False
                        action_validation["error_message"] = "매도 가능 수량 없음"
            
            # 가격 범위 검증 (상한가/하한가 체크)
            current_price = action["target_price"]
            if current_price <= 0:
                action_validation["is_valid"] = False
                action_validation["error_message"] = "유효하지 않은 주문 가격"
            
            validation_results["validated_actions"].append(action_validation)
            
            if not action_validation["is_valid"]:
                validation_results["is_valid"] = False
                validation_results["validation_errors"].append(action_validation["error_message"])
        
        return validation_results
        
    except Exception as e:
        logger.error(f"Trading plan validation failed: {str(e)}")
        return {"is_valid": False, "validation_errors": [str(e)]}
```

### 3.5 노드 5: 주문 실행

**목적**: 검증된 거래 계획을 실제 API로 실행

```python
from domestic_stock_functions import order_cash, order_credit

def execute_trading_plan(validated_plan):
    """
    아키텍처 노드 5: 주문 실행
    검증된 거래 계획을 실제 주문으로 실행
    """
    try:
        execution_results = {
            "executed_orders": [],
            "execution_errors": [],
            "total_executed": 0,
            "timestamp": datetime.now().isoformat()
        }
        
        if not validated_plan["is_valid"]:
            execution_results["execution_errors"].append("거래 계획 검증 실패")
            return execution_results
        
        for action_validation in validated_plan["validated_actions"]:
            if not action_validation["is_valid"]:
                continue
                
            action = action_validation["action"]
            quantity = action_validation["adjusted_quantity"]
            
            try:
                # 현금 주문 실행
                order_result = order_cash(
                    env_dv="demo",  # 또는 "real"
                    ord_dv=action["type"],  # "buy" or "sell"
                    cano=trenv.my_acct,
                    acnt_prdt_cd=trenv.my_prod,
                    pdno=action["ticker"],
                    ord_dvsn="00",  # 지정가
                    ord_qty=str(quantity),
                    ord_unpr=str(int(action["target_price"])),
                    excg_id_dvsn_cd="KRX"
                )
                
                # 주문 결과 저장
                order_info = {
                    "ticker": action["ticker"],
                    "type": action["type"],
                    "quantity": quantity,
                    "price": action["target_price"],
                    "order_number": order_result.iloc[0]['odno'] if not order_result.empty else None,
                    "status": "submitted",
                    "timestamp": datetime.now().isoformat(),
                    "reason": action["reason"]
                }
                
                execution_results["executed_orders"].append(order_info)
                execution_results["total_executed"] += 1
                
                logger.info(f"Order executed: {action['type']} {quantity} shares of {action['ticker']} at {action['target_price']}")
                
            except Exception as order_error:
                error_msg = f"주문 실행 실패 {action['ticker']}: {str(order_error)}"
                execution_results["execution_errors"].append(error_msg)
                logger.error(error_msg)
        
        return execution_results
        
    except Exception as e:
        logger.error(f"Order execution failed: {str(e)}")
        return {"executed_orders": [], "execution_errors": [str(e)]}
```

### 3.6 노드 6: 기록 및 보고

**목적**: 모든 거래 정보를 데이터베이스에 저장하고 관리자에게 보고

```python
import sqlite3
from datetime import datetime

def record_and_report(state):
    """
    아키텍처 노드 6: 기록 및 보고
    거래 데이터베이스에 저장 및 관리자 보고
    """
    try:
        # 거래 데이터베이스에 저장
        trade_records = []
        
        for executed_order in state["execution_results"]["executed_orders"]:
            # 아키텍처의 거래 데이터베이스 스키마에 맞춘 레코드 생성
            record = {
                "timestamp": executed_order["timestamp"],
                "ticker": executed_order["ticker"],
                "action": executed_order["type"].upper(),
                "quantity": executed_order["quantity"],
                "price": executed_order["price"],
                "justification_text": state["trade_plan"]["justification_text"],
                "market_snapshot": json.dumps(state["market_analysis"]),
                "portfolio_before": json.dumps(state["portfolio_status"]),
                "pnl_7_days": None,  # 추후 업데이트
                "pnl_30_days": None  # 추후 업데이트
            }
            
            trade_records.append(record)
        
        # 데이터베이스 저장
        save_to_database(trade_records)
        
        # 관리자 보고서 생성
        report = generate_trading_report(state)
        
        # 슬랙/이메일 전송 (구현 필요)
        send_notification(report)
        
        return {
            "records_saved": len(trade_records),
            "report_sent": True,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Record and report failed: {str(e)}")
        return {"records_saved": 0, "report_sent": False, "error": str(e)}

def save_to_database(trade_records):
    """거래 데이터베이스에 레코드 저장"""
    conn = sqlite3.connect('trading_database.db')
    cursor = conn.cursor()
    
    # 테이블 생성 (존재하지 않는 경우)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trades (
            trade_id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            ticker TEXT NOT NULL,
            action TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL,
            justification_text TEXT,
            market_snapshot TEXT,
            portfolio_before TEXT,
            pnl_7_days REAL,
            pnl_30_days REAL
        )
    ''')
    
    # 레코드 삽입
    for record in trade_records:
        cursor.execute('''
            INSERT INTO trades (timestamp, ticker, action, quantity, price, 
                              justification_text, market_snapshot, portfolio_before)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            record["timestamp"], record["ticker"], record["action"],
            record["quantity"], record["price"], record["justification_text"],
            record["market_snapshot"], record["portfolio_before"]
        ))
    
    conn.commit()
    conn.close()

def generate_trading_report(state):
    """거래 보고서 생성"""
    executed_orders = state["execution_results"]["executed_orders"]
    
    report = f"""
    📊 일일 거래 보고서
    ==================
    
    📅 거래 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    💼 실행된 주문: {len(executed_orders)}개
    
    📈 거래 내역:
    """
    
    for order in executed_orders:
        report += f"""
    - {order['type'].upper()} {order['ticker']} {order['quantity']}주 @ {order['price']:,}원
      사유: {order['reason']}
    """
    
    report += f"""
    
    🧠 AI 판단 근거:
    {state['trade_plan']['justification_text']}
    
    ⚠️ 리스크 평가:
    {state['trade_plan']['risk_assessment']}
    """
    
    return report
```

---

## 4. 성찰 그래프 API 매핑

성찰 그래프는 **주기적으로 과거 데이터를 분석하여 시스템을 학습시키고 개선**하는 엔진입니다.

### 4.1 노드 M1: 성과 데이터 집계

**목적**: 지난주 거래 기록을 분석하여 성과 보고서 생성

```python
from domestic_stock_functions import inquire_daily_ccld, inquire_period_profit

def aggregate_performance_data(start_date, end_date):
    """
    아키텍처 노드 M1: 성과 데이터 집계
    지정 기간의 거래 성과 분석
    """
    try:
        # 1. 일별 주문 체결 내역 조회
        daily_trades_df, daily_summary = inquire_daily_ccld(
            env_dv="demo",
            pd_dv="inner",
            cano=trenv.my_acct,
            acnt_prdt_cd=trenv.my_prod,
            inqr_strt_dt=start_date.replace('-', ''),
            inqr_end_dt=end_date.replace('-', ''),
            sll_buy_dvsn_cd="00",  # 전체 (매수+매도)
            inqr_dvsn="00",
            pdno="",  # 전체 종목
            ccld_dvsn="00",
            inqr_dvsn_3="00"
        )
        
        # 2. 기간별 손익 조회
        profit_df, profit_summary = inquire_period_profit(
            cano=trenv.my_acct,
            acnt_prdt_cd=trenv.my_prod,
            inqr_strt_dt=start_date.replace('-', ''),
            inqr_end_dt=end_date.replace('-', ''),
            sort_dvsn="00",
            inqr_dvsn="00",
            cblc_dvsn="00"
        )
        
        # 3. 성과 데이터 분석
        performance_analysis = {
            "period": {"start": start_date, "end": end_date},
            "total_trades": len(daily_trades_df),
            "total_profit": 0,
            "win_rate": 0,
            "best_trades": [],
            "worst_trades": [],
            "average_holding_period": 0,
            "timestamp": datetime.now().isoformat()
        }
        
        if not daily_trades_df.empty:
            # 수익률 계산
            buy_trades = daily_trades_df[daily_trades_df['sll_buy_dvsn_cd'] == '02']
            sell_trades = daily_trades_df[daily_trades_df['sll_buy_dvsn_cd'] == '01']
            
            # 종목별 매수-매도 매칭하여 손익 계산
            ticker_pnl = {}
            
            for _, sell in sell_trades.iterrows():
                ticker = sell['pdno']
                sell_amount = float(sell['tot_ccld_amt'])
                
                # 해당 종목의 매수 거래 찾기
                matching_buys = buy_trades[buy_trades['pdno'] == ticker]
                if not matching_buys.empty:
                    avg_buy_price = matching_buys['tot_ccld_amt'].astype(float).mean()
                    pnl = sell_amount - avg_buy_price
                    
                    ticker_pnl[ticker] = {
                        'pnl': pnl,
                        'return_rate': (pnl / avg_buy_price) * 100,
                        'sell_date': sell['ccld_dvsn'],
                        'ticker': ticker
                    }
            
            # 베스트/워스트 거래 선정
            sorted_trades = sorted(ticker_pnl.values(), key=lambda x: x['pnl'], reverse=True)
            
            performance_analysis["best_trades"] = sorted_trades[:5]  # 상위 5개
            performance_analysis["worst_trades"] = sorted_trades[-5:]  # 하위 5개
            
            # 전체 수익률 및 승률
            total_pnl = sum(trade['pnl'] for trade in ticker_pnl.values())
            winning_trades = len([t for t in ticker_pnl.values() if t['pnl'] > 0])
            
            performance_analysis["total_profit"] = total_pnl
            performance_analysis["win_rate"] = (winning_trades / len(ticker_pnl)) * 100 if ticker_pnl else 0
        
        # 4. 데이터베이스에서 상세 거래 기록 조회 (justification_text 포함)
        worst_trades_data = get_worst_trades_details(performance_analysis["worst_trades"])
        
        return {
            "weekly_report": performance_analysis,
            "worst_trades_data": worst_trades_data
        }
        
    except Exception as e:
        logger.error(f"Performance data aggregation failed: {str(e)}")
        return None

def get_worst_trades_details(worst_trades):
    """데이터베이스에서 실패 거래의 상세 정보 조회"""
    conn = sqlite3.connect('trading_database.db')
    
    worst_details = []
    for trade in worst_trades:
        cursor = conn.execute('''
            SELECT * FROM trades 
            WHERE ticker = ? 
            ORDER BY timestamp DESC 
            LIMIT 1
        ''', (trade['ticker'],))
        
        result = cursor.fetchone()
        if result:
            worst_details.append({
                'ticker': result[2],
                'action': result[3],
                'justification_text': result[6],
                'market_snapshot': json.loads(result[7]) if result[7] else {},
                'pnl': trade['pnl'],
                'return_rate': trade['return_rate']
            })
    
    conn.close()
    return worst_details
```

### 4.2 노드 M2: 성공/실패 요인 분석 엔진

**목적**: 손실 거래들의 공통 패턴을 LLM으로 분석

```python
def analyze_success_failure_factors(performance_data):
    """
    아키텍처 노드 M2: 성공/실패 요인 분석 엔진
    LLM을 통한 거래 패턴 분석
    """
    try:
        from openai import OpenAI
        client = OpenAI()
        
        # 실패 거래 데이터 준비
        worst_trades = performance_data["worst_trades_data"]
        weekly_report = performance_data["weekly_report"]
        
        # LLM 분석 프롬프트
        analysis_prompt = f"""
        당신은 전문 투자 분석가입니다. 다음 실패한 거래들을 분석하여 공통적인 실패 패턴을 찾아주세요.
        
        주간 성과 요약:
        - 총 거래 수: {weekly_report['total_trades']}
        - 총 손익: {weekly_report['total_profit']:,.0f}원
        - 승률: {weekly_report['win_rate']:.1f}%
        
        실패 거래 상세:
        {json.dumps(worst_trades, ensure_ascii=False, indent=2)}
        
        다음 관점에서 분석해주세요:
        1. 의사결정 과정의 문제점
        2. 시장 상황 판단 오류
        3. 리스크 관리 실패
        4. 타이밍 문제
        5. 종목 선정 오류
        
        분석 결과를 JSON 형식으로 제시하세요:
        {{
            "common_failures": [
                {{
                    "pattern": "실패 패턴 설명",
                    "frequency": "발생 빈도",
                    "impact": "손실 규모",
                    "examples": ["관련 사례들"]
                }}
            ],
            "key_insights": [
                "핵심 인사이트 1",
                "핵심 인사이트 2"
            ],
            "improvement_areas": [
                "개선이 필요한 영역 1",
                "개선이 필요한 영역 2"
            ]
        }}
        """
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": analysis_prompt}],
            temperature=0.3
        )
        
        # 분석 결과 파싱
        analysis_result = json.loads(response.choices[0].message.content)
        
        # 개선 인사이트 구조화
        improvement_insights = {
            "analysis_date": datetime.now().isoformat(),
            "period_analyzed": performance_data["weekly_report"]["period"],
            "common_failures": analysis_result["common_failures"],
            "key_insights": analysis_result["key_insights"],
            "improvement_areas": analysis_result["improvement_areas"],
            "priority_score": calculate_priority_score(analysis_result)
        }
        
        return improvement_insights
        
    except Exception as e:
        logger.error(f"Success/failure analysis failed: {str(e)}")
        return None

def calculate_priority_score(analysis_result):
    """개선 우선순위 점수 계산"""
    # 실패 패턴의 빈도와 영향도를 바탕으로 우선순위 점수 계산
    priority_scores = {}
    
    for failure in analysis_result["common_failures"]:
        # 빈도와 영향도를 숫자로 변환 (간단한 휴리스틱)
        frequency_score = len(failure.get("examples", [])) * 10
        impact_keywords = ["큰", "심각한", "치명적인", "대규모"]
        impact_score = sum(10 for keyword in impact_keywords if keyword in failure["impact"])
        
        pattern = failure["pattern"]
        priority_scores[pattern] = frequency_score + impact_score
    
    return dict(sorted(priority_scores.items(), key=lambda x: x[1], reverse=True))
```

### 4.3 노드 M3: 전략 규칙 생성

**목적**: 추상적인 인사이트를 구체적인 행동 규칙으로 변환

```python
def generate_strategy_rules(improvement_insights):
    """
    아키텍처 노드 M3: 전략 규칙 생성
    개선 인사이트를 실행 가능한 규칙으로 변환
    """
    try:
        from openai import OpenAI
        client = OpenAI()
        
        # 규칙 생성 프롬프트
        rule_generation_prompt = f"""
        당신은 트레이딩 시스템 설계자입니다. 다음 분석 결과를 바탕으로 구체적이고 실행 가능한 투자 규칙을 만들어주세요.
        
        개선 인사이트:
        {json.dumps(improvement_insights, ensure_ascii=False, indent=2)}
        
        규칙은 다음 조건을 만족해야 합니다:
        1. 명확하고 구체적 (애매한 표현 금지)
        2. 수치화 가능 (예: "VIX 25 이상일 때", "거래량이 평균의 3배 이상일 때")
        3. 자동화 가능 (프로그래밍으로 구현 가능)
        4. 검증 가능 (백테스팅 가능)
        
        다음 JSON 형식으로 규칙을 제시하세요:
        {{
            "new_rules": [
                {{
                    "rule_id": "규칙 고유 ID",
                    "category": "risk_management" | "entry_criteria" | "exit_criteria" | "position_sizing",
                    "rule_text": "구체적인 규칙 설명",
                    "condition": "실행 조건 (프로그래밍 가능한 형태)",
                    "action": "취해야 할 행동",
                    "priority": 1-10,
                    "rationale": "규칙의 근거"
                }}
            ],
            "deprecated_rules": [
                "제거해야 할 기존 규칙들"
            ]
        }}
        """
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": rule_generation_prompt}],
            temperature=0.2
        )
        
        # 규칙 파싱
        rules_result = json.loads(response.choices[0].message.content)
        
        # 규칙 구조화 및 검증
        validated_rules = []
        for rule in rules_result["new_rules"]:
            if validate_rule_format(rule):
                validated_rules.append({
                    "rule_id": rule["rule_id"],
                    "category": rule["category"],
                    "rule_text": rule["rule_text"],
                    "condition": rule["condition"],
                    "action": rule["action"],
                    "priority": rule["priority"],
                    "rationale": rule["rationale"],
                    "created_date": datetime.now().isoformat(),
                    "source_analysis": improvement_insights["analysis_date"]
                })
        
        new_strategy_rule = {
            "generation_date": datetime.now().isoformat(),
            "source_period": improvement_insights["period_analyzed"],
            "new_rules": validated_rules,
            "deprecated_rules": rules_result.get("deprecated_rules", []),
            "rule_count": len(validated_rules)
        }
        
        return new_strategy_rule
        
    except Exception as e:
        logger.error(f"Strategy rule generation failed: {str(e)}")
        return None

def validate_rule_format(rule):
    """규칙 형식 검증"""
    required_fields = ["rule_id", "category", "rule_text", "condition", "action", "priority"]
    
    for field in required_fields:
        if field not in rule or not rule[field]:
            return False
    
    # 카테고리 검증
    valid_categories = ["risk_management", "entry_criteria", "exit_criteria", "position_sizing"]
    if rule["category"] not in valid_categories:
        return False
    
    # 우선순위 검증
    try:
        priority = int(rule["priority"])
        if priority < 1 or priority > 10:
            return False
    except ValueError:
        return False
    
    return True
```

### 4.4 노드 M4: 시스템 로직 자동 업데이트

**목적**: 핵심 의사결정 프롬프트 파일을 자동으로 업데이트

```python
def update_system_logic(new_strategy_rule):
    """
    아키텍처 노드 M4: 시스템 로직 자동 업데이트
    의사결정 프롬프트 파일 자동 수정
    """
    try:
        # 1. 현재 의사결정 프롬프트 파일 읽기
        prompt_file_path = "prompts/core_decision_prompt.md"
        
        with open(prompt_file_path, 'r', encoding='utf-8') as f:
            current_prompt = f.read()
        
        # 2. 새로운 규칙들을 프롬프트에 통합
        updated_prompt = integrate_new_rules(current_prompt, new_strategy_rule)
        
        # 3. 백업 생성
        backup_path = f"prompts/backups/core_decision_prompt_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        os.makedirs(os.path.dirname(backup_path), exist_ok=True)
        
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(current_prompt)
        
        # 4. 업데이트된 프롬프트 저장
        with open(prompt_file_path, 'w', encoding='utf-8') as f:
            f.write(updated_prompt)
        
        # 5. 변경 이력 기록
        change_log = {
            "update_date": datetime.now().isoformat(),
            "backup_file": backup_path,
            "rules_added": len(new_strategy_rule["new_rules"]),
            "rules_deprecated": len(new_strategy_rule["deprecated_rules"]),
            "new_rules": new_strategy_rule["new_rules"],
            "version": generate_version_number()
        }
        
        save_change_log(change_log)
        
        # 6. Git 커밋 (선택사항)
        if should_commit_changes():
            commit_changes(change_log)
        
        # 7. 관리자 보고
        update_report = generate_update_report(change_log)
        send_notification(update_report)
        
        return {
            "success": True,
            "backup_created": backup_path,
            "rules_updated": len(new_strategy_rule["new_rules"]),
            "version": change_log["version"],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"System logic update failed: {str(e)}")
        return {"success": False, "error": str(e)}

def integrate_new_rules(current_prompt, new_strategy_rule):
    """프롬프트에 새로운 규칙 통합"""
    
    # 프롬프트 내 규칙 섹션 찾기
    rules_section_start = current_prompt.find("## 투자 원칙 및 규칙")
    
    if rules_section_start == -1:
        # 규칙 섹션이 없으면 새로 생성
        rules_section = "\n\n## 투자 원칙 및 규칙\n\n"
    else:
        # 기존 섹션 찾기
        next_section_start = current_prompt.find("\n## ", rules_section_start + 1)
        if next_section_start == -1:
            next_section_start = len(current_prompt)
        
        rules_section = current_prompt[rules_section_start:next_section_start]
    
    # 새로운 규칙 추가
    for rule in new_strategy_rule["new_rules"]:
        rule_text = f"""
### {rule['category'].replace('_', ' ').title()}: {rule['rule_id']}
**규칙**: {rule['rule_text']}
**조건**: {rule['condition']}
**행동**: {rule['action']}
**우선순위**: {rule['priority']}/10
**근거**: {rule['rationale']}
**추가일**: {rule['created_date'][:10]}

"""
        rules_section += rule_text
    
    # 기존 규칙 제거 (deprecated_rules)
    for deprecated_rule in new_strategy_rule["deprecated_rules"]:
        # 간단한 텍스트 매칭으로 제거 (실제로는 더 정교한 로직 필요)
        rules_section = rules_section.replace(deprecated_rule, "")
    
    # 전체 프롬프트 재구성
    if rules_section_start == -1:
        updated_prompt = current_prompt + rules_section
    else:
        next_section_start = current_prompt.find("\n## ", rules_section_start + 1)
        if next_section_start == -1:
            updated_prompt = current_prompt[:rules_section_start] + rules_section
        else:
            updated_prompt = (current_prompt[:rules_section_start] + 
                            rules_section + 
                            current_prompt[next_section_start:])
    
    return updated_prompt

def generate_update_report(change_log):
    """시스템 업데이트 보고서 생성"""
    report = f"""
    🤖 AI 트레이딩 시스템 자동 업데이트 완료
    ========================================
    
    📅 업데이트 시간: {change_log['update_date']}
    📝 버전: {change_log['version']}
    
    📊 변경 사항:
    - 새로운 규칙 추가: {change_log['rules_added']}개
    - 기존 규칙 제거: {change_log['rules_deprecated']}개
    
    🆕 추가된 규칙들:
    """
    
    for rule in change_log['new_rules']:
        report += f"""
    - [{rule['category']}] {rule['rule_text']}
      조건: {rule['condition']}
      우선순위: {rule['priority']}/10
    """
    
    report += f"""
    
    💾 백업 파일: {change_log['backup_file']}
    
    ⚡ 시스템이 스스로 학습하고 개선되었습니다!
    """
    
    return report
```

---

## 5. 거래 데이터베이스 스키마 매핑

아키텍처에서 정의한 거래 데이터베이스 스키마와 KIS API 응답을 매핑합니다.

### 5.1 데이터베이스 스키마 구현

```sql
-- 아키텍처 문서에 정의된 거래 데이터베이스 스키마
CREATE TABLE trades (
    trade_id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,                    -- 거래 실행 시간
    ticker TEXT NOT NULL,                       -- 종목 코드
    action TEXT NOT NULL,                       -- 'BUY' 또는 'SELL'
    quantity INTEGER NOT NULL,                  -- 거래 수량
    price REAL NOT NULL,                        -- 평균 체결 단가
    justification_text TEXT,                    -- AI의 상세한 논리적 근거
    market_snapshot TEXT,                       -- 거래 당시 시장 상황 (JSON)
    portfolio_before TEXT,                      -- 거래 직전 포트폴리오 상태 (JSON)
    pnl_7_days REAL,                           -- 7일 후 수익률 (추후 업데이트)
    pnl_30_days REAL,                          -- 30일 후 수익률 (추후 업데이트)
    order_number TEXT,                          -- KIS API 주문번호
    execution_status TEXT,                      -- 체결 상태
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 성과 추적을 위한 인덱스
CREATE INDEX idx_trades_timestamp ON trades(timestamp);
CREATE INDEX idx_trades_ticker ON trades(ticker);
CREATE INDEX idx_trades_action ON trades(action);
```

### 5.2 KIS API 응답 매핑

```python
def map_kis_response_to_schema(execution_result, trade_plan, market_analysis, portfolio_status):
    """
    KIS API 응답을 데이터베이스 스키마에 매핑
    """
    mapped_record = {
        "timestamp": datetime.now().isoformat(),
        "ticker": execution_result["ticker"],
        "action": execution_result["type"].upper(),
        "quantity": execution_result["quantity"],
        "price": execution_result["price"],
        
        # 아키텍처 핵심 필드들
        "justification_text": trade_plan["justification_text"],
        "market_snapshot": json.dumps({
            "kospi_index": get_kospi_index(),
            "market_volatility": calculate_market_volatility(market_analysis),
            "top_volume_stocks": market_analysis["market_opportunities"][:5],
            "market_sentiment": analyze_market_sentiment(market_analysis),
            "timestamp": datetime.now().isoformat()
        }),
        "portfolio_before": json.dumps(portfolio_status),
        
        # KIS API 특정 필드들
        "order_number": execution_result.get("order_number"),
        "execution_status": "submitted",  # 초기값, 나중에 업데이트
        
        # 성과 추적 필드들 (나중에 업데이트)
        "pnl_7_days": None,
        "pnl_30_days": None
    }
    
    return mapped_record

def get_kospi_index():
    """코스피 지수 조회"""
    try:
        from domestic_stock_functions import inquire_index_price
        index_data = inquire_index_price(
            fid_cond_mrkt_div_code="U",
            fid_input_iscd="0001"  # 코스피
        )
        return float(index_data.iloc[0]['bstp_nmix_prpr'])
    except:
        return 0.0

def calculate_market_volatility(market_analysis):
    """시장 변동성 계산"""
    try:
        # 상위 변동성 종목들의 평균 등락률로 간단 계산
        change_rates = []
        for holding in market_analysis["holdings_analysis"]:
            change_rates.append(abs(holding["change_rate"]))
        
        return sum(change_rates) / len(change_rates) if change_rates else 0.0
    except:
        return 0.0

def analyze_market_sentiment(market_analysis):
    """시장 심리 분석"""
    try:
        # 상승 종목 vs 하락 종목 비율로 간단 계산
        rising_count = len([h for h in market_analysis["holdings_analysis"] if h["change_rate"] > 0])
        total_count = len(market_analysis["holdings_analysis"])
        
        if total_count == 0:
            return "neutral"
        
        rising_ratio = rising_count / total_count
        
        if rising_ratio >= 0.7:
            return "bullish"
        elif rising_ratio <= 0.3:
            return "bearish"
        else:
            return "neutral"
    except:
        return "neutral"
```

---

## 6. 웹소켓 실시간 데이터

실시간 시세 데이터 수신을 위한 WebSocket 연결 및 관리

### 6.1 WebSocket 연결 설정

```python
import sys
sys.path.extend(['..', '.', 'open-trading-api-main/examples_user'])

import kis_auth as ka
from domestic_stock_functions_ws import *

def setup_websocket_connection():
    """
    실시간 데이터용 WebSocket 연결 설정
    """
    try:
        # 기본 인증
        ka.auth(svr="vps", product="01")  # 모의투자
        
        # WebSocket 인증
        ka.auth_ws()
        
        # WebSocket 클라이언트 생성
        kws = ka.KISWebSocket(api_url="/tryitout")
        
        logger.info("WebSocket 연결 준비 완료")
        return kws
        
    except Exception as e:
        logger.error(f"WebSocket 연결 실패: {str(e)}")
        raise

def subscribe_realtime_prices(kws, tickers):
    """
    다중 종목 실시간 시세 구독
    
    Args:
        kws: KISWebSocket 인스턴스
        tickers: 구독할 종목코드 리스트
    """
    try:
        # 실시간 호가 구독
        kws.subscribe(request=asking_price_krx, data=tickers)
        
        # 실시간 체결 구독 (선택사항)
        # kws.subscribe(request=realtime_conclusion_krx, data=tickers)
        
        logger.info(f"실시간 데이터 구독 시작: {tickers}")
        
    except Exception as e:
        logger.error(f"실시간 데이터 구독 실패: {str(e)}")
        raise
```

### 6.2 실시간 데이터 처리

```python
import threading
import queue
import time
from datetime import datetime

class RealtimeDataHandler:
    """실시간 데이터 처리 클래스"""
    
    def __init__(self):
        self.data_queue = queue.Queue()
        self.is_running = False
        self.websocket = None
        
    def start_realtime_monitoring(self, tickers):
        """실시간 모니터링 시작"""
        try:
            # WebSocket 연결
            self.websocket = setup_websocket_connection()
            
            # 실시간 데이터 구독
            subscribe_realtime_prices(self.websocket, tickers)
            
            # 데이터 처리 스레드 시작
            self.is_running = True
            processing_thread = threading.Thread(target=self._process_realtime_data)
            processing_thread.daemon = True
            processing_thread.start()
            
            logger.info("실시간 모니터링 시작")
            
        except Exception as e:
            logger.error(f"실시간 모니터링 시작 실패: {str(e)}")
            self.stop_realtime_monitoring()
            
    def _process_realtime_data(self):
        """실시간 데이터 처리 루프"""
        while self.is_running:
            try:
                # WebSocket에서 데이터 수신 대기
                if self.websocket and hasattr(self.websocket, 'get_data'):
                    data = self.websocket.get_data(timeout=1.0)
                    if data:
                        self._handle_realtime_update(data)
                else:
                    time.sleep(0.1)
                    
            except Exception as e:
                logger.error(f"실시간 데이터 처리 오류: {str(e)}")
                time.sleep(1)
                
    def _handle_realtime_update(self, data):
        """실시간 데이터 업데이트 처리"""
        try:
            # 데이터 파싱
            if 'output' in data:
                ticker = data['output'].get('mksc_shrn_iscd', '')
                current_price = float(data['output'].get('stck_prpr', 0))
                change_rate = float(data['output'].get('prdy_ctrt', 0))
                volume = int(data['output'].get('acml_vol', 0))
                
                # 실시간 데이터 구조화
                realtime_data = {
                    'ticker': ticker,
                    'price': current_price,
                    'change_rate': change_rate,
                    'volume': volume,
                    'timestamp': datetime.now().isoformat()
                }
                
                # 데이터 큐에 추가
                self.data_queue.put(realtime_data)
                
                # 알람 조건 체크 (예: 급등락/급락)
                self._check_alert_conditions(realtime_data)
                
        except Exception as e:
            logger.error(f"실시간 데이터 처리 오류: {str(e)}")
            
    def _check_alert_conditions(self, data):
        """알람 조건 체크"""
        try:
            # 급등락/급락 감지
            if abs(data['change_rate']) >= 5.0:  # 5% 이상 변동
                alert_msg = f"주가 대폭 변동 감지: {data['ticker']} {data['change_rate']:.2f}%"
                logger.warning(alert_msg)
                # 슬랙/이메일 알람 전송 기능 추가 가능
                
            # 거래량 급증 감지
            if data['volume'] > 1000000:  # 100만주 이상
                alert_msg = f"거래량 급증 감지: {data['ticker']} {data['volume']:,}주"
                logger.info(alert_msg)
                
        except Exception as e:
            logger.error(f"알람 조건 체크 오류: {str(e)}")
            
    def get_latest_data(self, ticker=None):
        """최신 데이터 조회"""
        latest_data = []
        
        # 큐에서 데이터 추출
        while not self.data_queue.empty():
            try:
                data = self.data_queue.get_nowait()
                if ticker is None or data['ticker'] == ticker:
                    latest_data.append(data)
            except queue.Empty:
                break
                
        return latest_data
        
    def stop_realtime_monitoring(self):
        """실시간 모니터링 중지"""
        self.is_running = False
        if self.websocket:
            try:
                self.websocket.close()
            except:
                pass
        logger.info("실시간 모니터링 중지")
```

### 6.3 실시간 데이터 활용 예제

```python
# 실시간 데이터 모니터링 사용 예제
if __name__ == "__main__":
    # 실시간 데이터 핸들러 생성
    realtime_handler = RealtimeDataHandler()
    
    try:
        # 모니터링할 종목 설정
        watch_tickers = ["005930", "000660", "035420"]  # 삼성전자, SK하이닉스, 네이버
        
        # 실시간 모니터링 시작
        realtime_handler.start_realtime_monitoring(watch_tickers)
        
        # 10초마다 데이터 확인
        for i in range(60):  # 10분간 실행
            time.sleep(10)
            
            # 최신 데이터 확인
            latest_data = realtime_handler.get_latest_data()
            if latest_data:
                for data in latest_data[-3:]:  # 최근 3개 데이터
                    print(f"{data['ticker']}: {data['price']:,}원 ({data['change_rate']:+.2f}%)")
                    
    except KeyboardInterrupt:
        print("사용자에 의해 중지되었습니다.")
    finally:
        # 정리
        realtime_handler.stop_realtime_monitoring()
```

---

## 7. 실제 구현 예제

### 5.1 전체 운영 그래프 실행

```python
import logging
from datetime import datetime
import json

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TradingGraphExecutor:
    """운영 그래프 실행 엔진"""
    
    def __init__(self, env_type="demo"):
        self.env_type = env_type
        self.auth_info = setup_authentication(env_type)
        
    def execute_trading_cycle(self):
        """완전한 거래 사이클 실행"""
        try:
            logger.info("🚀 운영 그래프 실행 시작")
            
            # 노드 1: 포트폴리오 진단
            logger.info("📊 노드 1: 포트폴리오 진단 중...")
            portfolio_status = fetch_portfolio_status()
            if not portfolio_status:
                raise Exception("포트폴리오 진단 실패")
            
            # 노드 2: 시장 분석
            logger.info("📈 노드 2: 시장 분석 중...")
            market_analysis = analyze_market_conditions(portfolio_status)
            if not market_analysis:
                raise Exception("시장 분석 실패")
            
            # 노드 3: 거래 계획 수립
            logger.info("🧠 노드 3: AI 거래 계획 수립 중...")
            decision_prompt = load_decision_prompt()
            trade_plan = generate_trading_plan(portfolio_status, market_analysis, decision_prompt)
            if not trade_plan:
                raise Exception("거래 계획 수립 실패")
            
            # 노드 4: 리스크 점검
            logger.info("⚠️  노드 4: 리스크 점검 중...")
            validation_result = validate_trading_plan(trade_plan, portfolio_status)
            
            if not validation_result["is_valid"]:
                logger.warning("⚠️ 리스크 점검 실패, 기록 후 종료")
                # 실패 사유 기록
                record_failed_plan(trade_plan, validation_result)
                return {"success": False, "reason": "risk_validation_failed"}
            
            # 노드 5: 주문 실행
            logger.info("💰 노드 5: 주문 실행 중...")
            execution_results = execute_trading_plan(validation_result)
            
            # 노드 6: 기록 및 보고
            logger.info("📝 노드 6: 기록 및 보고 중...")
            state = {
                "portfolio_status": portfolio_status,
                "market_analysis": market_analysis,
                "trade_plan": trade_plan,
                "validation_result": validation_result,
                "execution_results": execution_results
            }
            
            record_result = record_and_report(state)
            
            logger.info("✅ 운영 그래프 실행 완료")
            return {"success": True, "executed_orders": len(execution_results["executed_orders"])}
            
        except Exception as e:
            logger.error(f"❌ 운영 그래프 실행 실패: {str(e)}")
            return {"success": False, "error": str(e)}

def load_decision_prompt():
    """의사결정 프롬프트 로드"""
    try:
        with open("prompts/core_decision_prompt.md", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        # 기본 프롬프트 반환
        return """
        # 기본 투자 원칙
        
        ## 리스크 관리
        - 단일 종목 투자 비중은 전체 자산의 10%를 초과하지 않는다
        - 일일 손실 한도는 전체 자산의 2%로 제한한다
        
        ## 진입 조건
        - 거래량이 최근 20일 평균의 1.5배 이상인 종목만 고려한다
        - 기술적 지표가 상승 신호를 보이는 종목을 우선한다
        
        ## 청산 조건
        - 7% 손실 시 무조건 손절한다
        - 15% 수익 시 50% 부분 익절한다
        """

def record_failed_plan(trade_plan, validation_result):
    """실패한 거래 계획 기록"""
    failed_record = {
        "timestamp": datetime.now().isoformat(),
        "plan": trade_plan,
        "failure_reason": validation_result["validation_errors"],
        "type": "failed_plan"
    }
    
    # 실패 로그 저장
    with open("logs/failed_plans.json", "a", encoding="utf-8") as f:
        f.write(json.dumps(failed_record, ensure_ascii=False) + "\n")

# 실행 예제
if __name__ == "__main__":
    executor = TradingGraphExecutor(env_type="demo")
    result = executor.execute_trading_cycle()
    print(f"거래 사이클 결과: {result}")
```

### 5.2 성찰 그래프 실행 (주간)

```python
class ReflectionGraphExecutor:
    """성찰 그래프 실행 엔진"""
    
    def execute_weekly_reflection(self):
        """주간 성찰 및 학습 실행"""
        try:
            logger.info("🔍 성찰 그래프 실행 시작")
            
            # 지난주 날짜 계산
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            
            # 노드 M1: 성과 데이터 집계
            logger.info("📊 노드 M1: 성과 데이터 집계 중...")
            performance_data = aggregate_performance_data(start_date, end_date)
            if not performance_data:
                raise Exception("성과 데이터 집계 실패")
            
            # 노드 M2: 성공/실패 요인 분석
            logger.info("🔬 노드 M2: 성공/실패 요인 분석 중...")
            improvement_insights = analyze_success_failure_factors(performance_data)
            if not improvement_insights:
                raise Exception("성공/실패 요인 분석 실패")
            
            # 노드 M3: 전략 규칙 생성
            logger.info("⚙️  노드 M3: 새로운 전략 규칙 생성 중...")
            new_strategy_rule = generate_strategy_rules(improvement_insights)
            if not new_strategy_rule:
                raise Exception("전략 규칙 생성 실패")
            
            # 노드 M4: 시스템 로직 업데이트
            logger.info("🔄 노드 M4: 시스템 로직 자동 업데이트 중...")
            update_result = update_system_logic(new_strategy_rule)
            
            if update_result["success"]:
                logger.info("✅ 성찰 그래프 실행 완료 - 시스템이 스스로 개선되었습니다!")
                return {
                    "success": True,
                    "rules_added": update_result["rules_updated"],
                    "version": update_result["version"]
                }
            else:
                logger.error("❌ 시스템 업데이트 실패")
                return {"success": False, "error": update_result["error"]}
                
        except Exception as e:
            logger.error(f"❌ 성찰 그래프 실행 실패: {str(e)}")
            return {"success": False, "error": str(e)}

# 주간 실행 스케줄러
import schedule
import time

def schedule_reflection():
    """성찰 그래프 주간 스케줄링"""
    reflection_executor = ReflectionGraphExecutor()
    
    # 매주 일요일 오후 6시에 실행
    schedule.every().sunday.at("18:00").do(reflection_executor.execute_weekly_reflection)
    
    while True:
        schedule.run_pending()
        time.sleep(3600)  # 1시간마다 체크
```

---

## 6. 에러 처리 및 베스트 프랙티스

### 6.1 에러 처리 전략

```python
class KISAPIError(Exception):
    """KIS API 관련 에러"""
    pass

class TradingSystemError(Exception):
    """트레이딩 시스템 에러"""
    pass

def robust_api_call(api_function, *args, **kwargs):
    """안정적인 API 호출 래퍼"""
    max_retries = 3
    retry_delay = 1
    
    for attempt in range(max_retries):
        try:
            result = api_function(*args, **kwargs)
            if result is not None and not result.empty:
                return result
            else:
                raise KISAPIError("Empty response from API")
                
        except Exception as e:
            logger.warning(f"API call attempt {attempt + 1} failed: {str(e)}")
            
            if attempt == max_retries - 1:
                logger.error(f"API call failed after {max_retries} attempts")
                raise KISAPIError(f"API call failed: {str(e)}")
            
            time.sleep(retry_delay * (2 ** attempt))  # 지수 백오프
    
    return None

# 사용 예제
def safe_fetch_portfolio():
    """안전한 포트폴리오 조회"""
    try:
        account_df, account_summary = robust_api_call(
            inquire_account_balance,
            cano=trenv.my_acct,
            acnt_prdt_cd=trenv.my_prod
        )
        return account_df, account_summary
    except KISAPIError as e:
        logger.error(f"포트폴리오 조회 실패: {str(e)}")
        return None, None
```

### 6.2 성능 최적화

```python
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor

class AsyncKISClient:
    """비동기 KIS API 클라이언트"""
    
    def __init__(self):
        self.session = None
        self.executor = ThreadPoolExecutor(max_workers=5)
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()
        self.executor.shutdown()
    
    async def fetch_multiple_prices(self, tickers):
        """여러 종목 시세 동시 조회"""
        tasks = []
        for ticker in tickers:
            task = asyncio.create_task(self._fetch_single_price(ticker))
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results
    
    async def _fetch_single_price(self, ticker):
        """단일 종목 시세 조회"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            inquire_price,
            "demo", "J", ticker
        )

# 사용 예제
async def fast_market_analysis():
    """고성능 시장 분석"""
    async with AsyncKISClient() as client:
        tickers = ["005930", "000660", "035420"]  # 삼성전자, SK하이닉스, 네이버
        prices = await client.fetch_multiple_prices(tickers)
        return prices
```

### 6.3 데이터 검증

```python
from pydantic import BaseModel, validator
from typing import List, Optional

class TradeRecord(BaseModel):
    """거래 기록 검증 모델"""
    ticker: str
    action: str
    quantity: int
    price: float
    timestamp: str
    justification_text: str
    
    @validator('ticker')
    def validate_ticker(cls, v):
        if not v or len(v) != 6:
            raise ValueError('종목코드는 6자리여야 합니다')
        return v
    
    @validator('action')
    def validate_action(cls, v):
        if v not in ['BUY', 'SELL']:
            raise ValueError('거래구분은 BUY 또는 SELL이어야 합니다')
        return v
    
    @validator('quantity')
    def validate_quantity(cls, v):
        if v <= 0:
            raise ValueError('거래수량은 양수여야 합니다')
        return v
    
    @validator('price')
    def validate_price(cls, v):
        if v <= 0:
            raise ValueError('거래가격은 양수여야 합니다')
        return v

def validate_and_save_trade(trade_data):
    """거래 데이터 검증 후 저장"""
    try:
        validated_trade = TradeRecord(**trade_data)
        save_to_database([validated_trade.dict()])
        return True
    except Exception as e:
        logger.error(f"거래 데이터 검증 실패: {str(e)}")
        return False
```

### 6.4 모니터링 및 알림

```python
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class SystemMonitor:
    """시스템 모니터링"""
    
    def __init__(self):
        self.alert_thresholds = {
            "max_daily_loss": 0.02,  # 일일 최대 손실 2%
            "max_consecutive_losses": 3,  # 연속 손실 거래 3회
            "api_error_rate": 0.1  # API 에러율 10%
        }
    
    def check_system_health(self):
        """시스템 건강도 체크"""
        health_report = {
            "status": "healthy",
            "issues": [],
            "timestamp": datetime.now().isoformat()
        }
        
        # 일일 손실률 체크
        daily_loss = self.calculate_daily_loss()
        if daily_loss > self.alert_thresholds["max_daily_loss"]:
            health_report["status"] = "warning"
            health_report["issues"].append(f"일일 손실률 {daily_loss:.2%} 초과")
        
        # 연속 손실 체크
        consecutive_losses = self.count_consecutive_losses()
        if consecutive_losses >= self.alert_thresholds["max_consecutive_losses"]:
            health_report["status"] = "critical"
            health_report["issues"].append(f"연속 손실 거래 {consecutive_losses}회")
        
        # API 에러율 체크
        api_error_rate = self.calculate_api_error_rate()
        if api_error_rate > self.alert_thresholds["api_error_rate"]:
            health_report["status"] = "warning"
            health_report["issues"].append(f"API 에러율 {api_error_rate:.2%}")
        
        return health_report
    
    def send_alert(self, message, urgency="normal"):
        """알림 전송"""
        # 슬랙 또는 이메일로 알림 전송
        if urgency == "critical":
            self.send_email_alert(message)
        self.send_slack_alert(message)
    
    def send_slack_alert(self, message):
        """슬랙 알림 전송"""
        # 슬랙 웹훅 구현 필요
        pass
    
    def send_email_alert(self, message):
        """이메일 알림 전송"""
        # 이메일 전송 구현 필요
        pass
```

---

## 9. 문제 해결 및 마무리

### 9.1 주요 문제 해결 가이드

#### 토큰 오류 시
```python
import kis_auth as ka

# 토큰 재발급 - 1분당 1회 발급됩니다.
ka.auth(svr="prod")  # 또는 "vps"
```

#### 설정 파일 오류 시
- `kis_devlp.yaml` 파일의 앱키, 앱시크릿이 올바른지 확인
- 계좌번호 형식이 맞는지 확인 (앞 8자리 + 뒤 2자리)
- **'No close frame received' 오류**: `kis_devlp.yaml`에 입력하신 HTS ID가 정확한지 확인

#### 의존성 오류 시
```bash
# 의존성 재설치
uv sync --reinstall
```

#### import 오류 시
```python
# 올바른 경로 설정
import sys
sys.path.extend(['..', '.', 'open-trading-api-main/examples_user'])

# KIS 모듈 import
import kis_auth as ka
from domestic_stock_functions import *
```

### 9.2 베스트 프랙티스 체크리스트

#### 환경 설정
- [ ] Python 3.9+ 설치 확인
- [ ] uv 패키지 매니저 설치
- [ ] KIS Open API 서비스 신청 완료
- [ ] `kis_devlp.yaml` 설정 완료
- [ ] `config_root` 경로 설정

#### 보안
- [ ] 실전투자 전에 모의투자로 충분한 테스트
- [ ] API Key를 코드에 하드코딩하지 말고 환경변수 사용
- [ ] 토큰 파일 저장 경로를 안전한 위치로 설정
- [ ] 리스크 관리 규칙 철저히 준수

#### 성능
- [ ] API 호출 제한 및 에러 처리 주의
- [ ] 여러 종목 동시 조회 시 비동기 처리 고려
- [ ] 데이터 백업 및 시스템 모니터링 필수
- [ ] WebSocket 연결 안정성 모니터링

### 9.3 추가 리소스

- **[KIS Developers 공식 사이트](https://kis-developers.com)** - API 문서 및 업데이트
- **[GitHub 저장소](https://github.com/koreainvestment/open-trading-api)** - 최신 샘플 코드
- **커뮤니티**: KIS Developers 사이트의 Q&A 섹션 활용

---

## 10. 마무리

이 가이드는 `docs/all_architecture.md`에 정의된 자율적 AI 트레이딩 시스템을 KIS API로 실제 구현하기 위한 완전한 로드맵을 제공합니다.

### 🎯 핵심 구현 포인트

1. **환경 설정**: uv 패키지 매니저와 체계적인 설정 가이드
2. **운영 그래프**: 6개 노드로 구성된 실시간 거래 실행 엔진
3. **성찰 그래프**: 4개 노드로 구성된 자동 학습 및 개선 시스템
4. **거래 데이터베이스**: 모든 학습의 근간이 되는 중앙화된 기록 시스템
5. **WebSocket 실시간 데이터**: 실시간 시세 모니터링 및 알람 시스템
6. **KIS API 통합**: 인증부터 실제 거래까지 완전한 API 활용

### 🔄 다음 단계

1. **환경 설정**: KIS API 샘플 코드 다운로드 및 기본 설정 완료
2. **모의투자 테스트**: 안전한 환경에서 기능 테스트 및 디버깅
3. **LV1 Observer 구현**: 기본적인 모니터링 및 보고 시스템 구축
4. **실시간 데이터 연동**: WebSocket을 통한 실시간 시세 모니터링
5. **성찰 그래프 구현**: 자동 학습 및 시스템 개선 엔진
6. **LV2-LV5 단계**: 점진적 고도화 및 실전 환경 전환

### ⚠️ 중요 주의사항

- **모의투자 환경**에서 충분한 테스트 후 실전 전환
- **API 호출 제한** (1분당 1회 토큰 발급) 및 **에러 처리** 철저
- **HTS ID 정확성** 확인 (WebSocket 오류 방지)
- **리스크 관리 규칙** 철저히 준수
- **인증 정보 보안** 및 **데이터 백업** 필수
- **시스템 모니터링** 및 **예외 상황 대비** 철저

이제 이 가이드를 바탕으로 안전하고 효율적인 자율 트레이딩 시스템을 구축할 수 있습니다! 🚀