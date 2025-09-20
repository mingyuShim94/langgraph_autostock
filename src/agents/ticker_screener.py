#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
거래가능 티커 스크리너

KIS API의 inquire_psbl_order 함수를 활용하여 
종목별 매매가능 여부를 확인하는 스크리너입니다.
LLM을 사용하지 않는 순수 API 기반 검증 기능입니다.
"""

import logging
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

from src.kis_client.client import KISClient, KISClientError


@dataclass
class TickerScreenResult:
    """티커 스크리닝 결과"""
    tradable_tickers: List[str]          # 거래가능 종목 리스트
    non_tradable_tickers: List[str]      # 거래불가 종목 리스트
    error_tickers: List[str]             # API 에러 발생 종목 리스트
    total_checked: int                   # 총 체크한 종목 수
    execution_time: float                # 실행 시간 (초)
    errors: List[Dict[str, str]]         # 에러 상세 정보


class TickerScreener:
    """거래가능 티커 스크리너 클래스"""
    
    def __init__(self, kis_client: KISClient, config: Optional[Dict[str, Any]] = None):
        """
        스크리너 초기화
        
        Args:
            kis_client: KIS API 클라이언트
            config: 추가 설정 옵션
        """
        self.kis_client = kis_client
        self.config = config or {}
        self.logger = logging.getLogger("ticker_screener")
        
        # 기본 설정
        self.default_test_price = self.config.get('test_price', '1000')  # 테스트용 주문가격
        self.default_ord_dvsn = self.config.get('ord_dvsn', '01')       # 시장가
        self.api_delay = self.config.get('api_delay', 0.1)              # API 호출 간격 (초)
        self.max_retries = self.config.get('max_retries', 2)            # 재시도 횟수
    
    def check_tradable_tickers(
        self, 
        ticker_list: List[str],
        test_price: Optional[str] = None
    ) -> TickerScreenResult:
        """
        여러 종목의 거래가능 여부를 일괄 확인
        
        Args:
            ticker_list: 확인할 종목 코드 리스트 (6자리)
            test_price: 테스트용 주문 가격 (기본값: 1000원)
            
        Returns:
            TickerScreenResult: 스크리닝 결과
        """
        start_time = time.time()
        test_price = test_price or self.default_test_price
        
        tradable_tickers = []
        non_tradable_tickers = []
        error_tickers = []
        errors = []
        
        self.logger.info(f"티커 스크리닝 시작: {len(ticker_list)}개 종목")
        
        for i, ticker in enumerate(ticker_list):
            try:
                self.logger.debug(f"[{i+1}/{len(ticker_list)}] {ticker} 검사 중...")
                
                # 거래가능 여부 체크
                is_tradable, error_msg = self._check_single_ticker(ticker, test_price)
                
                if is_tradable:
                    tradable_tickers.append(ticker)
                    self.logger.debug(f"✅ {ticker}: 거래가능")
                elif error_msg:
                    error_tickers.append(ticker)
                    errors.append({
                        'ticker': ticker,
                        'error': error_msg
                    })
                    self.logger.warning(f"⚠️ {ticker}: API 에러 - {error_msg}")
                else:
                    non_tradable_tickers.append(ticker)
                    self.logger.debug(f"❌ {ticker}: 거래불가")
                
                # API 호출 간격 조절
                if i < len(ticker_list) - 1:  # 마지막이 아닌 경우
                    time.sleep(self.api_delay)
                    
            except Exception as e:
                error_tickers.append(ticker)
                error_msg = f"예외 발생: {str(e)}"
                errors.append({
                    'ticker': ticker,
                    'error': error_msg
                })
                self.logger.error(f"💥 {ticker}: {error_msg}")
        
        execution_time = time.time() - start_time
        
        result = TickerScreenResult(
            tradable_tickers=tradable_tickers,
            non_tradable_tickers=non_tradable_tickers,
            error_tickers=error_tickers,
            total_checked=len(ticker_list),
            execution_time=execution_time,
            errors=errors
        )
        
        self.logger.info(
            f"스크리닝 완료 ({execution_time:.2f}초): "
            f"거래가능 {len(tradable_tickers)}개, "
            f"거래불가 {len(non_tradable_tickers)}개, "
            f"에러 {len(error_tickers)}개"
        )
        
        return result
    
    def _check_single_ticker(
        self, 
        ticker: str, 
        test_price: str
    ) -> Tuple[bool, Optional[str]]:
        """
        단일 종목의 거래가능 여부 확인
        
        Args:
            ticker: 종목코드 (6자리)
            test_price: 테스트용 주문 가격
            
        Returns:
            Tuple[bool, Optional[str]]: (거래가능여부, 에러메시지)
        """
        # 종목코드 검증
        if not ticker or len(ticker) != 6 or not ticker.isdigit():
            return False, f"잘못된 종목코드 형식: {ticker}"
        
        retry_count = 0
        last_error = None
        
        while retry_count <= self.max_retries:
            try:
                # KIS API로 매수가능 조회 시도
                result = self.kis_client.inquire_psbl_order(
                    pdno=ticker,
                    ord_unpr=test_price,
                    ord_dvsn=self.default_ord_dvsn,
                    cma_evlu_amt_icld_yn="N",
                    ovrs_icld_yn="N"
                )
                
                # API 호출 성공하면 거래가능으로 판단
                if result is not None and not result.empty:
                    return True, None
                else:
                    return False, None
                    
            except KISClientError as e:
                last_error = str(e)
                self.logger.debug(f"{ticker} KIS API 에러 (시도 {retry_count + 1}): {last_error}")
                
                # 특정 에러의 경우 재시도하지 않음
                if any(keyword in last_error.lower() for keyword in [
                    '거래정지', '상장폐지', '관리종목', 'suspended', 'delisted'
                ]):
                    return False, None
                
                retry_count += 1
                if retry_count <= self.max_retries:
                    time.sleep(self.api_delay * 2)  # 재시도 시 더 긴 대기
                    
            except Exception as e:
                last_error = str(e)
                self.logger.debug(f"{ticker} 일반 에러 (시도 {retry_count + 1}): {last_error}")
                retry_count += 1
                if retry_count <= self.max_retries:
                    time.sleep(self.api_delay * 2)
        
        # 모든 재시도 실패
        return False, last_error
    
    def get_summary_stats(self, result: TickerScreenResult) -> Dict[str, Any]:
        """
        스크리닝 결과 요약 통계
        
        Args:
            result: 스크리닝 결과
            
        Returns:
            Dict: 요약 통계
        """
        total = result.total_checked
        if total == 0:
            return {}
        
        return {
            'total_tickers': total,
            'tradable_count': len(result.tradable_tickers),
            'non_tradable_count': len(result.non_tradable_tickers),
            'error_count': len(result.error_tickers),
            'tradable_ratio': len(result.tradable_tickers) / total,
            'success_ratio': (len(result.tradable_tickers) + len(result.non_tradable_tickers)) / total,
            'execution_time': result.execution_time,
            'avg_time_per_ticker': result.execution_time / total
        }


def create_ticker_screener(kis_client: KISClient, **config) -> TickerScreener:
    """
    티커 스크리너 팩토리 함수
    
    Args:
        kis_client: KIS API 클라이언트
        **config: 추가 설정
        
    Returns:
        TickerScreener: 스크리너 인스턴스
    """
    return TickerScreener(kis_client, config)