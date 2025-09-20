"""
포트폴리오 리밸런싱 에이전트

Phase 2.1 노드 1: 포트폴리오 진단 및 리밸런싱 필요도 분석을 담당하는 전문가 에이전트
GPT-5 nano 모델을 사용하여 빠르고 정확한 포트폴리오 분석을 수행합니다.
"""

import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import asdict

from .base_agent import BaseAgent, AgentContext, AgentResult
from ..kis_client.client import get_kis_client
from ..utils.portfolio_analyzer import get_portfolio_analyzer, PortfolioMetrics, RebalancingRecommendation
from ..utils.sector_classifier import get_sector_classifier

logger = logging.getLogger(__name__)


class PortfolioRebalancerAgent(BaseAgent):
    """포트폴리오 리밸런싱 에이전트"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        리밸런싱 에이전트 초기화
        
        Args:
            config: 추가 설정 (LLM 설정 덮어쓰기 등)
        """
        # LLM 클라이언트 초기화 시도 (API 키가 없는 경우 mock 모드로 폴백)
        try:
            super().__init__("portfolio_rebalancer", config)
            self.llm_available = True
        except Exception as e:
            self.logger.warning(f"LLM 클라이언트 초기화 실패, mock 모드로 진행: {str(e)}")
            self.agent_type = "portfolio_rebalancer"
            self.config = config or {}
            self.logger = logging.getLogger(f"agent.{self.agent_type}")
            self.llm_client = None
            self.llm_available = False
        
        # 의존성 초기화
        self.kis_client = get_kis_client(environment="paper", mock_mode=True)  # 기본 설정
        self.portfolio_analyzer = get_portfolio_analyzer()
        self.sector_classifier = get_sector_classifier()
        
        self.logger.info("포트폴리오 리밸런싱 에이전트 초기화 완료")
    
    def execute(self, context: AgentContext) -> AgentResult:
        """
        에이전트 실행 (LLM 없이도 실행 가능하도록 오버라이드)
        
        Args:
            context: 실행 컨텍스트
            
        Returns:
            AgentResult: 실행 결과
        """
        start_time = time.time()
        execution_id = context.execution_id
        
        self.logger.info(f"에이전트 실행 시작: {self.agent_type} (ID: {execution_id})")
        
        try:
            # 입력 데이터 검증
            self._validate_input(context.input_data)
            
            # 실제 작업 수행
            result_data = self._process(context)
            
            # 결과 검증
            self._validate_output(result_data)
            
            execution_time = time.time() - start_time
            
            result = AgentResult(
                agent_id=self.agent_type,
                execution_id=execution_id,
                success=True,
                result_data=result_data,
                execution_time=execution_time,
                llm_usage=self._get_llm_usage_stats() if self.llm_available else {},
                confidence_score=self._calculate_confidence(result_data)
            )
            
            self.logger.info(f"에이전트 실행 완료: {self.agent_type} ({execution_time:.2f}초)")
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = str(e)
            
            self.logger.error(f"에이전트 실행 실패: {self.agent_type} - {error_msg}")
            
            return AgentResult(
                agent_id=self.agent_type,
                execution_id=execution_id,
                success=False,
                result_data={},
                execution_time=execution_time,
                error_message=error_msg
            )
    
    def get_agent_info(self) -> Dict[str, Any]:
        """에이전트 정보 반환 (LLM 없이도 동작하도록 수정)"""
        return {
            'agent_type': self.agent_type,
            'agent_class': self.__class__.__name__,
            'llm_provider': self.llm_client.provider_name if (self.llm_available and self.llm_client) else "none",
            'llm_model': self.llm_client.model_name if (self.llm_available and self.llm_client) else "none",
            'llm_available': self.llm_available,
            'config': self.config
        }
    
    def _validate_input(self, input_data: Dict[str, Any]) -> None:
        """입력 데이터 검증"""
        if not isinstance(input_data, dict):
            raise ValueError("입력 데이터는 딕셔너리 형태여야 합니다")
        
        # 리밸런싱 에이전트 특화 검증
        if "environment" in input_data:
            env = input_data["environment"]
            if env not in ["paper", "prod"]:
                raise ValueError(f"지원하지 않는 거래 환경: {env}")
        
        if "mock_mode" in input_data:
            if not isinstance(input_data["mock_mode"], bool):
                raise ValueError("mock_mode는 불린 값이어야 합니다")
    
    def _process(self, context: AgentContext) -> Dict[str, Any]:
        """
        포트폴리오 리밸런싱 분석 처리
        
        Args:
            context: 실행 컨텍스트
            
        Returns:
            Dict[str, Any]: 리밸런싱 분석 결과
        """
        input_data = context.input_data
        
        # KIS 클라이언트 환경 설정
        environment = input_data.get("environment", "paper")
        mock_mode = input_data.get("mock_mode", True)
        
        self.logger.info(f"포트폴리오 분석 시작 - 환경: {environment}, 모의모드: {mock_mode}")
        
        try:
            # 1. 포트폴리오 진단
            portfolio_diagnosis = self._diagnose_portfolio(environment, mock_mode)
            
            # 2. 섹터별/종목별 비중 분석  
            allocation_analysis = self._analyze_allocation(portfolio_diagnosis)
            
            # 3. 리밸런싱 필요도 스코어링
            rebalancing_assessment = self._assess_rebalancing_need(
                portfolio_diagnosis, allocation_analysis
            )
            
            # 4. LLM 기반 종합 판단 및 권고사항 생성
            llm_recommendation = self._generate_llm_recommendation(
                portfolio_diagnosis, allocation_analysis, rebalancing_assessment
            )
            
            # 5. 결과 종합
            result = {
                "diagnosis": portfolio_diagnosis,
                "allocation_analysis": allocation_analysis,
                "rebalancing_assessment": rebalancing_assessment,
                "llm_recommendation": llm_recommendation,
                "execution_summary": {
                    "agent_type": self.agent_type,
                    "analysis_timestamp": datetime.now().isoformat(),
                    "environment": environment,
                    "mock_mode": mock_mode,
                    "analysis_quality": "high" if portfolio_diagnosis["total_value"] > 0 else "limited"
                }
            }
            
            self.logger.info(f"포트폴리오 분석 완료 - 리밸런싱 점수: {rebalancing_assessment['score']:.2f}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"포트폴리오 분석 실패: {str(e)}")
            raise
    
    def _diagnose_portfolio(self, environment: str, mock_mode: bool) -> Dict[str, Any]:
        """
        포트폴리오 진단 수행
        
        Args:
            environment: 거래 환경
            mock_mode: 모의 모드 여부
            
        Returns:
            Dict[str, Any]: 포트폴리오 진단 결과
        """
        try:
            # KIS API를 통한 포트폴리오 데이터 수집
            if hasattr(self.kis_client, 'environment') and self.kis_client.environment != environment:
                # 환경이 바뀐 경우 새 클라이언트 생성
                self.kis_client = get_kis_client(environment=environment, mock_mode=mock_mode)
            
            # 상세 포트폴리오 정보 조회
            detailed_portfolio = self.kis_client.get_detailed_portfolio()
            
            # 포트폴리오 메트릭 계산
            portfolio_metrics = self.kis_client.calculate_portfolio_metrics(detailed_portfolio)
            
            return {
                "account_info": detailed_portfolio.get("account_info", {}),
                "holdings": detailed_portfolio.get("holdings", []),
                "total_value": detailed_portfolio.get("total_value", 0),
                "stock_value": detailed_portfolio.get("stock_value", 0),
                "cash_value": detailed_portfolio.get("cash_value", 0),
                "metrics": portfolio_metrics,
                "timestamp": detailed_portfolio.get("timestamp", datetime.now().isoformat())
            }
            
        except Exception as e:
            self.logger.error(f"포트폴리오 진단 실패: {str(e)}")
            # 빈 포트폴리오 기본값 반환
            return {
                "account_info": {},
                "holdings": [],
                "total_value": 0,
                "stock_value": 0,
                "cash_value": 0,
                "metrics": {},
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _analyze_allocation(self, portfolio_diagnosis: Dict[str, Any]) -> Dict[str, Any]:
        """
        섹터별/종목별 비중 분석
        
        Args:
            portfolio_diagnosis: 포트폴리오 진단 결과
            
        Returns:
            Dict[str, Any]: 배분 분석 결과
        """
        holdings = portfolio_diagnosis.get("holdings", [])
        total_value = portfolio_diagnosis.get("total_value", 0)
        
        if not holdings or total_value == 0:
            return {
                "sector_allocation": [],
                "stock_concentration": [],
                "allocation_summary": {
                    "sector_count": 0,
                    "stock_count": 0,
                    "max_single_stock_weight": 0,
                    "max_sector_weight": 0,
                    "diversification_level": "insufficient_data"
                }
            }
        
        # 섹터별 배분 분석
        sector_allocation = self.kis_client.get_sector_allocation(holdings)
        
        # 종목별 집중도 분석
        stock_concentration = []
        for holding in holdings:
            stock_concentration.append({
                "ticker": holding["ticker"],
                "name": holding["name"],
                "weight": holding["weight"],
                "sector": self.sector_classifier.classify_ticker(holding["ticker"]).value,
                "concentration_level": self._get_concentration_level(holding["weight"])
            })
        
        # 집중도별 정렬
        stock_concentration.sort(key=lambda x: x["weight"], reverse=True)
        
        # 배분 요약 통계
        sector_weights = [alloc["weight"] for alloc in sector_allocation.values()]
        stock_weights = [holding["weight"] for holding in holdings]
        
        allocation_summary = {
            "sector_count": len(sector_allocation),
            "stock_count": len(holdings),
            "max_single_stock_weight": max(stock_weights) if stock_weights else 0,
            "max_sector_weight": max(sector_weights) if sector_weights else 0,
            "top3_stock_concentration": sum(sorted(stock_weights, reverse=True)[:3]),
            "diversification_level": self._evaluate_diversification_level(
                len(sector_allocation), len(holdings), max(stock_weights) if stock_weights else 0
            )
        }
        
        return {
            "sector_allocation": sector_allocation,
            "stock_concentration": stock_concentration,
            "allocation_summary": allocation_summary
        }
    
    def _assess_rebalancing_need(self, portfolio_diagnosis: Dict[str, Any], 
                               allocation_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        리밸런싱 필요도 평가
        
        Args:
            portfolio_diagnosis: 포트폴리오 진단 결과
            allocation_analysis: 배분 분석 결과
            
        Returns:
            Dict[str, Any]: 리밸런싱 평가 결과
        """
        metrics = portfolio_diagnosis.get("metrics", {})
        
        rebalancing_score = metrics.get("rebalancing_score", 0)
        priority = metrics.get("rebalancing_priority", "낮음")
        
        # 리밸런싱 필요 이유 분석
        reasons = []
        recommendations = []
        
        # 집중도 위험 체크
        concentration_risk = metrics.get("concentration_risk", 0)
        if concentration_risk > 0.3:
            reasons.append(f"집중도 위험 높음 (위험도: {concentration_risk:.1%})")
            recommendations.append("집중된 종목/섹터 비중 분산")
        
        # 분산투자 부족 체크
        diversification_score = metrics.get("diversification_score", 0)
        if diversification_score < 0.6:
            reasons.append(f"분산투자 부족 (분산점수: {diversification_score:.1%})")
            recommendations.append("섹터 및 종목 다각화 확대")
        
        # 현금 비중 체크
        cash_ratio = metrics.get("cash_ratio", 0)
        if cash_ratio < 0.05:
            reasons.append("현금 비중 부족 (기회비용 관리 필요)")
            recommendations.append("일부 보유종목 매도하여 현금 확보")
        elif cash_ratio > 0.3:
            reasons.append("현금 비중 과다 (투자기회 손실)")
            recommendations.append("현금을 활용한 추가 투자 검토")
        
        # 단일 종목 과다 보유 체크
        allocation_summary = allocation_analysis.get("allocation_summary", {})
        max_stock_weight = allocation_summary.get("max_single_stock_weight", 0)
        if max_stock_weight > 0.2:
            reasons.append(f"단일 종목 과다 보유 (최대 비중: {max_stock_weight:.1%})")
            recommendations.append("집중 보유 종목 일부 매도")
        
        return {
            "score": rebalancing_score,
            "priority": priority,
            "reasons": reasons,
            "recommendations": recommendations,
            "assessment_details": {
                "concentration_risk": concentration_risk,
                "diversification_score": diversification_score,
                "cash_ratio": cash_ratio,
                "max_stock_weight": max_stock_weight,
                "overall_health": self._get_portfolio_health_level(rebalancing_score)
            }
        }
    
    def _generate_llm_recommendation(self, portfolio_diagnosis: Dict[str, Any],
                                   allocation_analysis: Dict[str, Any],
                                   rebalancing_assessment: Dict[str, Any]) -> Dict[str, Any]:
        """
        LLM 기반 종합 판단 및 권고사항 생성
        
        Args:
            portfolio_diagnosis: 포트폴리오 진단 결과
            allocation_analysis: 배분 분석 결과
            rebalancing_assessment: 리밸런싱 평가 결과
            
        Returns:
            Dict[str, Any]: LLM 권고사항
        """
        # LLM에 전달할 분석 데이터 구성
        analysis_data = {
            "포트폴리오_현황": {
                "총자산": portfolio_diagnosis.get("total_value", 0),
                "현금비중": portfolio_diagnosis.get("metrics", {}).get("cash_ratio", 0),
                "보유종목수": len(portfolio_diagnosis.get("holdings", [])),
                "섹터수": allocation_analysis.get("allocation_summary", {}).get("sector_count", 0)
            },
            "리스크_지표": {
                "집중도위험": rebalancing_assessment.get("assessment_details", {}).get("concentration_risk", 0),
                "분산투자점수": rebalancing_assessment.get("assessment_details", {}).get("diversification_score", 0),
                "리밸런싱점수": rebalancing_assessment.get("score", 0),
                "우선순위": rebalancing_assessment.get("priority", "낮음")
            },
            "주요_이슈": rebalancing_assessment.get("reasons", []),
            "기본_권고사항": rebalancing_assessment.get("recommendations", [])
        }
        
        # LLM 프롬프트 구성
        prompt = f"""
당신은 포트폴리오 리밸런싱 전문가입니다. 다음 포트폴리오 분석 결과를 바탕으로 종합적인 리밸런싱 권고안을 작성해주세요.

## 포트폴리오 분석 결과
{analysis_data}

## 요청사항
1. 현재 포트폴리오 상태에 대한 전문가 평가
2. 주요 리스크 요인과 개선 방향
3. 구체적인 리밸런싱 액션 플랜 (우선순위 포함)
4. 예상 효과 및 주의사항

## 응답 형식
JSON 형태로 다음 구조로 응답해주세요:
{{
    "overall_assessment": "포트폴리오 전반적 평가",
    "key_risks": ["주요 리스크 1", "주요 리스크 2"],
    "action_plan": [
        {{
            "action": "구체적 액션",
            "priority": "높음/보통/낮음",
            "rationale": "실행 근거",
            "expected_impact": "예상 효과"
        }}
    ],
    "timeline": "권장 실행 일정",
    "cautions": ["주의사항 1", "주의사항 2"]
}}
"""
        
        try:
            # LLM 사용 가능한 경우에만 쿼리 전송
            if self.llm_available and self.llm_client:
                response = self.query_llm(prompt, temperature=0.3, max_tokens=1500)
                
                # 응답 파싱 시도
                try:
                    import json
                    llm_output = json.loads(response.content)
                except json.JSONDecodeError:
                    # JSON 파싱 실패 시 기본 구조 반환
                    llm_output = {
                        "overall_assessment": response.content[:200],
                        "key_risks": rebalancing_assessment.get("reasons", []),
                        "action_plan": [
                            {
                                "action": rec,
                                "priority": rebalancing_assessment.get("priority", "보통"),
                                "rationale": "분석 데이터 기반",
                                "expected_impact": "포트폴리오 안정성 개선"
                            }
                            for rec in rebalancing_assessment.get("recommendations", [])
                        ],
                        "timeline": "1-2주 내 실행 권장",
                        "cautions": ["시장 상황 고려", "거래 비용 최소화"]
                    }
                
                return {
                    "llm_response": llm_output,
                    "confidence_score": self._calculate_confidence({"llm_response": llm_output}),
                    "model_used": self.llm_client.model_name,
                    "tokens_used": response.tokens_used,
                    "response_time": response.response_time
                }
            else:
                # LLM이 없는 경우 분석 데이터 기반 권고사항 생성
                self.logger.info("LLM 없이 분석 데이터 기반 권고사항 생성")
                
                # 기본 권고사항 구조 생성
                fallback_response = {
                    "overall_assessment": f"포트폴리오 분석 완료. 리밸런싱 점수: {rebalancing_assessment.get('score', 0):.2f}",
                    "key_risks": rebalancing_assessment.get("reasons", []),
                    "action_plan": [
                        {
                            "action": rec,
                            "priority": rebalancing_assessment.get("priority", "보통"),
                            "rationale": "정량 분석 결과",
                            "expected_impact": "포트폴리오 균형 개선"
                        }
                        for rec in rebalancing_assessment.get("recommendations", [])
                    ],
                    "timeline": "적절한 시기에 실행",
                    "cautions": ["시장 변동성 고려", "거래 비용 고려"]
                }
                
                return {
                    "llm_response": fallback_response,
                    "confidence_score": 0.7,
                    "model_used": "analysis_only",
                    "tokens_used": 0,
                    "response_time": 0
                }
            
        except Exception as e:
            self.logger.error(f"LLM 권고사항 생성 실패: {str(e)}")
            
            # 폴백 권고사항
            return {
                "llm_response": {
                    "overall_assessment": f"포트폴리오 분석 완료. 리밸런싱 점수: {rebalancing_assessment.get('score', 0):.2f}",
                    "key_risks": rebalancing_assessment.get("reasons", []),
                    "action_plan": [
                        {
                            "action": rec,
                            "priority": rebalancing_assessment.get("priority", "보통"),
                            "rationale": "정량 분석 결과",
                            "expected_impact": "포트폴리오 균형 개선"
                        }
                        for rec in rebalancing_assessment.get("recommendations", [])
                    ],
                    "timeline": "적절한 시기에 실행",
                    "cautions": ["시장 변동성 고려"]
                },
                "confidence_score": 0.7,
                "model_used": "fallback",
                "error": str(e)
            }
    
    def _get_concentration_level(self, weight: float) -> str:
        """종목 비중에 따른 집중도 레벨 반환"""
        if weight >= 0.3:
            return "매우높음"
        elif weight >= 0.2:
            return "높음"
        elif weight >= 0.1:
            return "보통"
        elif weight >= 0.05:
            return "낮음"
        else:
            return "매우낮음"
    
    def _evaluate_diversification_level(self, sector_count: int, stock_count: int, max_stock_weight: float) -> str:
        """분산투자 수준 평가"""
        if sector_count >= 5 and stock_count >= 10 and max_stock_weight <= 0.15:
            return "excellent"
        elif sector_count >= 4 and stock_count >= 7 and max_stock_weight <= 0.2:
            return "good"
        elif sector_count >= 3 and stock_count >= 5 and max_stock_weight <= 0.3:
            return "fair"
        elif sector_count >= 2 and stock_count >= 3:
            return "poor"
        else:
            return "very_poor"
    
    def _get_portfolio_health_level(self, rebalancing_score: float) -> str:
        """포트폴리오 건강도 레벨 반환"""
        if rebalancing_score <= 0.2:
            return "excellent"
        elif rebalancing_score <= 0.4:
            return "good"
        elif rebalancing_score <= 0.6:
            return "fair"
        elif rebalancing_score <= 0.8:
            return "poor"
        else:
            return "critical"
    
    def _calculate_confidence(self, result_data: Dict[str, Any]) -> float:
        """결과에 대한 신뢰도 계산"""
        base_confidence = 0.8
        
        # LLM 응답이 있는 경우 신뢰도 증가
        if "llm_response" in result_data:
            llm_response = result_data["llm_response"]
            if isinstance(llm_response, dict) and "overall_assessment" in llm_response:
                base_confidence += 0.1
        
        # 포트폴리오 데이터가 충분한 경우 신뢰도 증가
        if "diagnosis" in result_data:
            holdings_count = len(result_data["diagnosis"].get("holdings", []))
            if holdings_count >= 3:
                base_confidence += 0.05
            if holdings_count >= 5:
                base_confidence += 0.05
        
        return min(base_confidence, 1.0)