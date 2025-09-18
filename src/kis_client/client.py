#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KIS API 클라이언트 모듈

한국투자증권 Open Trading API를 래핑하여 트레이딩 시스템에서 사용하기 쉽도록 구성
"""

import sys
import os
import time
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import pandas as pd

# KIS API 모듈 경로 추가
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
kis_path = os.path.join(project_root, 'open-trading-api-main/examples_user')
kis_domestic_path = os.path.join(project_root, 'open-trading-api-main/examples_user/domestic_stock')
kis_auth_path = os.path.join(project_root, 'open-trading-api-main/examples_user/auth')

sys.path.extend([kis_path, kis_domestic_path, kis_auth_path])

try:
    import kis_auth as ka
    from domestic_stock_functions import (
        inquire_account_balance, inquire_balance, inquire_price,
        inquire_ccnl, volume_rank, fluctuation,
        inquire_psbl_order, inquire_psbl_sell, order_cash
    )
except ImportError as e:
    print(f"⚠️ KIS API 모듈 import 실패: {e}")
    print("KIS API 의존성이 없는 경우 mock 모드로 실행됩니다.")


class KISClientError(Exception):
    """KIS API 클라이언트 에러"""
    pass


class KISAuthManager:
    """KIS API 인증 관리 클래스"""
    
    def __init__(self, environment: str = "paper"):
        """
        인증 매니저 초기화
        
        Args:
            environment: 환경 설정 ("paper": 모의투자, "prod": 실전투자)
        """
        self.environment = environment
        self.is_authenticated = False
        self.last_auth_time = None
        self.auth_expiry_minutes = 60  # 토큰 유효 시간
        
    def authenticate(self) -> bool:
        """
        KIS API 인증 수행
        
        Returns:
            bool: 인증 성공 여부
        """
        try:
            # 환경에 따른 서버 설정
            server = "vps" if self.environment == "paper" else "prod"
            
            print(f"🔐 KIS API 인증 시작 (환경: {self.environment})")
            ka.auth(svr=server, product="01")
            
            self.is_authenticated = True
            self.last_auth_time = datetime.now()
            
            trenv = ka.getTREnv()
            print(f"✅ 인증 성공 - 계좌: {trenv.my_acct}")
            
            return True
            
        except Exception as e:
            print(f"❌ KIS API 인증 실패: {e}")
            self.is_authenticated = False
            return False
    
    def check_auth_status(self) -> bool:
        """
        인증 상태 확인 및 필요시 재인증
        
        Returns:
            bool: 유효한 인증 상태인지 여부
        """
        if not self.is_authenticated:
            return self.authenticate()
        
        # 토큰 만료 체크
        if self.last_auth_time:
            elapsed = (datetime.now() - self.last_auth_time).total_seconds() / 60
            if elapsed > self.auth_expiry_minutes:
                print("🔄 토큰 만료, 재인증 수행")
                return self.authenticate()
        
        return True


class KISClient:
    """KIS API 통합 클라이언트"""
    
    def __init__(self, environment: str = "paper", mock_mode: bool = False):
        """
        KIS 클라이언트 초기화
        
        Args:
            environment: 환경 설정 ("paper": 모의투자, "prod": 실전투자)
            mock_mode: 모의 모드 (KIS API 없이 테스트)
        """
        self.environment = environment
        self.mock_mode = mock_mode
        self.auth_manager = KISAuthManager(environment)
        
        if not mock_mode:
            # 초기 인증 수행
            if not self.auth_manager.authenticate():
                raise KISClientError("KIS API 초기 인증 실패")
    
    def _ensure_authenticated(self):
        """인증 상태 확인"""
        if self.mock_mode:
            return
        
        if not self.auth_manager.check_auth_status():
            raise KISClientError("KIS API 인증 실패")
    
    def get_account_balance(self) -> Dict[str, Any]:
        """
        계좌 잔고 조회
        
        Returns:
            Dict: 계좌 잔고 정보
        """
        self._ensure_authenticated()
        
        if self.mock_mode:
            return {
                "total_cash": 1000000,
                "available_cash": 800000,
                "total_value": 2000000,
                "stock_value": 1000000
            }
        
        try:
            trenv = ka.getTREnv()
            
            # 모의투자 환경에서는 주식잔고조회로 대체
            if self.environment == "paper":
                print(f"ℹ️ 모의투자 환경 - 주식잔고조회 API 사용")
                holdings_df, summary_df = inquire_balance(
                    env_dv="demo",
                    cano=trenv.my_acct,
                    acnt_prdt_cd=trenv.my_prod,
                    afhr_flpr_yn="N",
                    inqr_dvsn="01",
                    unpr_dvsn="01",
                    fund_sttl_icld_yn="N",
                    fncg_amt_auto_rdpt_yn="N",
                    prcs_dvsn="00"
                )
                
                if not summary_df.empty:
                    summary = summary_df.iloc[0]
                    return {
                        "total_cash": float(summary.get('dnca_tot_amt', 0)),
                        "available_cash": float(summary.get('nxdy_excc_amt', 0)),
                        "total_value": float(summary.get('tot_evlu_amt', 0)),
                        "stock_value": float(summary.get('scts_evlu_amt', 0))
                    }
                else:
                    # 기본값 반환 (모의투자에서 계좌 정보 없을 경우)
                    return {
                        "total_cash": 10000000,  # 기본 모의 자금 1천만원
                        "available_cash": 10000000,
                        "total_value": 10000000,
                        "stock_value": 0
                    }
            else:
                # 실전투자에서는 원래 API 사용
                account_df, summary_df = inquire_account_balance(
                    cano=trenv.my_acct,
                    acnt_prdt_cd=trenv.my_prod,
                    inqr_dvsn_1="",
                    bspr_bf_dt_aply_yn=""
                )
                
                if not summary_df.empty:
                    summary = summary_df.iloc[0]
                    return {
                        "total_cash": float(summary.get('dnca_tot_amt', 0)),
                        "available_cash": float(summary.get('nxdy_excc_amt', 0)),
                        "total_value": float(summary.get('tot_evlu_amt', 0)),
                        "stock_value": float(summary.get('scts_evlu_amt', 0))
                    }
                else:
                    error_msg = f"계좌 잔고 조회 실패 - 환경: {self.environment}, 빈 응답 반환"
                    print(f"⚠️ {error_msg}")
                    return {"error": error_msg}
                
        except Exception as e:
            error_msg = f"계좌 잔고 조회 실패 - 환경: {self.environment}, 오류: {str(e)}"
            print(f"⚠️ {error_msg}")
            
            # 환경 설정 오류 감지
            if "없는 서비스 코드" in str(e) or "OPSQ0002" in str(e):
                if self.environment == "paper":
                    print(f"ℹ️ 모의투자 환경에서 해당 API가 지원되지 않음 - 기본값 반환")
                    return {
                        "total_cash": 10000000,  # 기본 모의 자금 1천만원
                        "available_cash": 10000000,
                        "total_value": 10000000,
                        "stock_value": 0
                    }
                error_msg += " (환경별 TR 코드 불일치 가능성)"
            
            raise KISClientError(error_msg)
    
    def get_stock_holdings(self) -> List[Dict[str, Any]]:
        """
        주식 보유 현황 조회
        
        Returns:
            List[Dict]: 보유 주식 정보 리스트
        """
        self._ensure_authenticated()
        
        if self.mock_mode:
            return [
                {
                    "ticker": "005930",
                    "name": "삼성전자",
                    "quantity": 10,
                    "avg_price": 75000,
                    "current_price": 77000,
                    "total_value": 770000,
                    "pnl": 20000
                }
            ]
        
        try:
            trenv = ka.getTREnv()
            holdings_df, _ = inquire_balance(
                env_dv="demo" if self.environment == "paper" else "real",
                cano=trenv.my_acct,
                acnt_prdt_cd=trenv.my_prod,
                afhr_flpr_yn="N",
                inqr_dvsn="01",
                unpr_dvsn="01",
                fund_sttl_icld_yn="N",
                fncg_amt_auto_rdpt_yn="N",
                prcs_dvsn="00"
            )
            
            holdings = []
            if not holdings_df.empty:
                for _, row in holdings_df.iterrows():
                    if int(row['hldg_qty']) > 0:  # 보유 수량이 있는 것만
                        holdings.append({
                            "ticker": row['pdno'],
                            "name": row['prdt_name'],
                            "quantity": int(row['hldg_qty']),
                            "avg_price": float(row['pchs_avg_pric']),
                            "current_price": float(row['prpr']),
                            "total_value": float(row['evlu_amt']),
                            "pnl": float(row['evlu_pfls_amt'])
                        })
            
            return holdings
            
        except Exception as e:
            error_msg = f"주식 보유 현황 조회 실패 - 환경: {self.environment}, 오류: {str(e)}"
            print(f"⚠️ {error_msg}")
            raise KISClientError(error_msg)
    
    def get_stock_price(self, ticker: str) -> Dict[str, Any]:
        """
        주식 현재가 조회
        
        Args:
            ticker: 종목 코드
            
        Returns:
            Dict: 주식 가격 정보
        """
        self._ensure_authenticated()
        
        if self.mock_mode:
            return {
                "ticker": ticker,
                "current_price": 77000,
                "change": 2000,
                "change_rate": 2.67,
                "volume": 1500000,
                "high": 78000,
                "low": 75000
            }
        
        try:
            price_df = inquire_price(
                env_dv="demo" if self.environment == "paper" else "real",
                fid_cond_mrkt_div_code="J",  # KRX 시장
                fid_input_iscd=ticker
            )
            
            if not price_df.empty:
                price_data = price_df.iloc[0]
                return {
                    "ticker": ticker,
                    "current_price": float(price_data.get('stck_prpr', 0)),
                    "change": float(price_data.get('prdy_vrss', 0)),
                    "change_rate": float(price_data.get('prdy_vrss_rate', 0)),
                    "volume": int(price_data.get('acml_vol', 0)),
                    "high": float(price_data.get('stck_hgpr', 0)),
                    "low": float(price_data.get('stck_lwpr', 0))
                }
            else:
                return {"error": f"주식 가격 조회 실패: {ticker}"}
                
        except Exception as e:
            raise KISClientError(f"주식 가격 조회 실패: {e}")
    
    def get_trading_volume_rank(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        거래량 순위 조회
        
        Args:
            limit: 조회할 종목 수
            
        Returns:
            List[Dict]: 거래량 순위 정보
        """
        self._ensure_authenticated()
        
        if self.mock_mode:
            return [
                {"ticker": "005930", "name": "삼성전자", "volume": 15000000, "change_rate": 2.5},
                {"ticker": "000660", "name": "SK하이닉스", "volume": 8000000, "change_rate": -1.2}
            ]
        
        try:
            volume_df = volume_rank()
            
            volume_list = []
            if not volume_df.empty:
                for i, row in volume_df.head(limit).iterrows():
                    volume_list.append({
                        "ticker": row.get('mksc_shrn_iscd', ''),
                        "name": row.get('hts_kor_isnm', ''),
                        "volume": int(row.get('acml_vol', 0)),
                        "change_rate": float(row.get('prdy_vrss_rate', 0))
                    })
            
            return volume_list
            
        except Exception as e:
            raise KISClientError(f"거래량 순위 조회 실패: {e}")
    
    def place_buy_order(self, ticker: str, quantity: int, price: Optional[float] = None) -> Dict[str, Any]:
        """
        매수 주문 실행
        
        Args:
            ticker: 종목 코드
            quantity: 수량
            price: 가격 (None이면 시장가)
            
        Returns:
            Dict: 주문 결과
        """
        self._ensure_authenticated()
        
        if self.mock_mode:
            return {
                "order_id": f"MOCK_{int(time.time())}",
                "ticker": ticker,
                "quantity": quantity,
                "price": price or 77000,
                "status": "success",
                "message": "모의 매수 주문 완료"
            }
        
        try:
            trenv = ka.getTREnv()
            
            # 주문 유형 설정
            ord_dvsn = "00" if price is None else "01"  # 00: 시장가, 01: 지정가
            order_price = str(int(price)) if price else "0"
            
            result_df = order_cash(
                env_dv="demo" if self.environment == "paper" else "real",
                ord_dv="buy",
                cano=trenv.my_acct,
                acnt_prdt_cd=trenv.my_prod,
                pdno=ticker,
                ord_dvsn=ord_dvsn,
                ord_qty=str(quantity),
                ord_unpr=order_price,
                excg_id_dvsn_cd="KRX"
            )
            
            if not result_df.empty:
                result = result_df.iloc[0]
                return {
                    "order_id": result.get('odno', ''),
                    "ticker": ticker,
                    "quantity": quantity,
                    "price": price,
                    "status": "success" if result.get('rt_cd') == '0' else "failed",
                    "message": result.get('msg1', '')
                }
            else:
                return {"error": "매수 주문 실패"}
                
        except Exception as e:
            raise KISClientError(f"매수 주문 실패: {e}")
    
    def place_sell_order(self, ticker: str, quantity: int, price: Optional[float] = None) -> Dict[str, Any]:
        """
        매도 주문 실행
        
        Args:
            ticker: 종목 코드
            quantity: 수량
            price: 가격 (None이면 시장가)
            
        Returns:
            Dict: 주문 결과
        """
        self._ensure_authenticated()
        
        if self.mock_mode:
            return {
                "order_id": f"MOCK_{int(time.time())}",
                "ticker": ticker,
                "quantity": quantity,
                "price": price or 77000,
                "status": "success",
                "message": "모의 매도 주문 완료"
            }
        
        try:
            trenv = ka.getTREnv()
            
            # 주문 유형 설정
            ord_dvsn = "00" if price is None else "01"  # 00: 시장가, 01: 지정가
            order_price = str(int(price)) if price else "0"
            
            result_df = order_cash(
                env_dv="demo" if self.environment == "paper" else "real",
                ord_dv="sell",
                cano=trenv.my_acct,
                acnt_prdt_cd=trenv.my_prod,
                pdno=ticker,
                ord_dvsn=ord_dvsn,
                ord_qty=str(quantity),
                ord_unpr=order_price,
                excg_id_dvsn_cd="KRX"
            )
            
            if not result_df.empty:
                result = result_df.iloc[0]
                return {
                    "order_id": result.get('odno', ''),
                    "ticker": ticker,
                    "quantity": quantity,
                    "price": price,
                    "status": "success" if result.get('rt_cd') == '0' else "failed",
                    "message": result.get('msg1', '')
                }
            else:
                return {"error": "매도 주문 실패"}
                
        except Exception as e:
            raise KISClientError(f"매도 주문 실패: {e}")


# 전역 KIS 클라이언트 인스턴스 (싱글톤 패턴)
_kis_client = None

def get_kis_client(environment: str = "paper", mock_mode: bool = False) -> KISClient:
    """
    KIS 클라이언트 싱글톤 인스턴스 가져오기
    
    Args:
        environment: 환경 설정
        mock_mode: 모의 모드
        
    Returns:
        KISClient: KIS 클라이언트 인스턴스
    """
    global _kis_client
    
    if _kis_client is None:
        _kis_client = KISClient(environment, mock_mode)
    
    return _kis_client