"""
섹터 리서치 에이전트

Phase 2.1 노드 2: 실시간 웹 검색을 통한 섹터 트렌드 분석 및 유망 섹터 발굴
Perplexity sonar-pro 모델을 사용하여 최신 시장 정보를 기반으로 한 정확한 섹터 분석 제공
"""

import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

from .base_agent import BaseAgent, AgentContext, AgentResult
from ..utils.sector_research_engine import get_sector_research_engine, SectorResearchResult
from ..llm_clients.base import LLMRequest

logger = logging.getLogger(__name__)


class SectorResearcherAgent(BaseAgent):
    """섹터 리서치 에이전트"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        섹터 리서치 에이전트 초기화
        
        Args:
            config: 추가 설정 (LLM 설정 덮어쓰기 등)
        """
        # LLM 클라이언트 초기화 시도 (API 키가 없는 경우 mock 모드로 폴백)
        try:
            super().__init__("sector_researcher", config)
            self.llm_available = True
            logger.info(f"Perplexity 클라이언트 연결 성공: {self.llm_client.model_name}")
        except Exception as e:
            logger.warning(f"LLM 클라이언트 초기화 실패, mock 모드로 진행: {str(e)}")
            self.agent_type = "sector_researcher"
            self.config = config or {}
            self.logger = logging.getLogger(f"agent.{self.agent_type}")
            self.llm_client = None
            self.llm_available = False
        
        # 의존성 초기화
        self.research_engine = get_sector_research_engine()
        
        # 에이전트별 설정
        self.default_focus_sectors = [
            "기술주", "반도체", "금융", "자동차", "화학", 
            "헬스케어", "에너지", "소재", "엔터테인먼트", "통신"
        ]
        
        self.analysis_cache = {}  # 캐싱 시스템
        self.cache_ttl_minutes = 5  # 캐시 유효 시간
        
        logger.info("섹터 리서치 에이전트 초기화 완료")
    
    def _validate_input(self, input_data: Dict[str, Any]) -> None:
        """
        입력 데이터 검증
        
        Args:
            input_data: 입력 데이터
            
        Raises:
            ValueError: 입력 데이터가 유효하지 않은 경우
        """
        super()._validate_input(input_data)
        
        # 섹터 리서치 특화 검증
        if 'focus_sectors' in input_data:
            focus_sectors = input_data['focus_sectors']
            if not isinstance(focus_sectors, list):
                raise ValueError("focus_sectors는 리스트 형태여야 합니다")
            
            # 유효한 섹터인지 확인
            valid_sectors = self.research_engine.sectors
            invalid_sectors = [s for s in focus_sectors if s not in valid_sectors]
            if invalid_sectors:
                raise ValueError(f"유효하지 않은 섹터: {invalid_sectors}")
        
        # 분석 깊이 설정 검증
        if 'analysis_depth' in input_data:
            depth = input_data['analysis_depth']
            if depth not in ['basic', 'detailed', 'comprehensive']:
                raise ValueError("analysis_depth는 'basic', 'detailed', 'comprehensive' 중 하나여야 합니다")
    
    def _process(self, context: AgentContext) -> Dict[str, Any]:
        """
        섹터 리서치 프로세스 실행
        
        Args:
            context: 실행 컨텍스트
            
        Returns:
            Dict[str, Any]: 섹터 리서치 결과
        """
        input_data = context.input_data
        
        # 입력 파라미터 추출
        focus_sectors = input_data.get('focus_sectors', self.default_focus_sectors)
        analysis_depth = input_data.get('analysis_depth', 'detailed')
        force_refresh = input_data.get('force_refresh', False)
        
        logger.info(f"섹터 리서치 시작 - 대상 섹터: {len(focus_sectors)}개, 깊이: {analysis_depth}")
        
        try:
            # 캐시 확인 (강제 새로고침이 아닌 경우)
            cache_key = self._generate_cache_key(focus_sectors, analysis_depth)
            if not force_refresh and self._is_cache_valid(cache_key):
                logger.info("캐시된 분석 결과 사용")
                cached_result = self.analysis_cache[cache_key]
                return cached_result['data']
            
            # 실제 분석 수행
            if self.llm_available:
                research_result = self._perform_real_time_analysis(focus_sectors, analysis_depth)
            else:
                logger.info("Mock 모드로 섹터 분석 수행")
                research_result = self._perform_mock_analysis(focus_sectors, analysis_depth)
            
            # 결과 검증
            is_valid, validation_errors = self.research_engine.validate_research_result(research_result)
            if not is_valid:
                logger.warning(f"분석 결과 검증 실패: {validation_errors}")
                # 경고는 하지만 진행 (부분적 결과라도 제공)
            
            # 결과 구조화
            result_data = {
                'research_result': research_result.to_dict(),
                'analysis_metadata': {
                    'agent_type': self.agent_type,
                    'analysis_depth': analysis_depth,
                    'sectors_analyzed': len(focus_sectors),
                    'llm_mode': 'real' if self.llm_available else 'mock',
                    'cache_used': False,
                    'validation_passed': is_valid,
                    'validation_errors': validation_errors if not is_valid else None
                },
                'summary': self._generate_summary(research_result),
                'recommendations': self._generate_recommendations(research_result)
            }
            
            # 캐시 업데이트
            self._update_cache(cache_key, result_data)
            
            logger.info(f"섹터 리서치 완료 - 분석된 섹터: {len(research_result.sector_rankings)}개")
            return result_data
            
        except Exception as e:
            logger.error(f"섹터 리서치 중 오류 발생: {str(e)}")
            raise
    
    def _perform_real_time_analysis(self, focus_sectors: List[str], analysis_depth: str) -> SectorResearchResult:
        """
        실시간 Perplexity 기반 섹터 분석
        
        Args:
            focus_sectors: 분석 대상 섹터
            analysis_depth: 분석 깊이
            
        Returns:
            SectorResearchResult: 분석 결과
        """
        logger.info(f"Perplexity를 통한 실시간 섹터 분석 시작 - {self.llm_client.model_name}")
        
        # 분석 깊이에 따른 프롬프트 생성
        if analysis_depth == 'basic':
            sectors_to_analyze = focus_sectors[:5]  # 상위 5개만
        elif analysis_depth == 'detailed':
            sectors_to_analyze = focus_sectors[:10]  # 상위 10개
        else:  # comprehensive
            sectors_to_analyze = focus_sectors  # 전체
        
        # 분석 깊이에 따른 프롬프트 타입 결정
        analysis_type_mapping = {
            'basic': 'market_overview',
            'detailed': 'comprehensive', 
            'comprehensive': 'comprehensive'
        }
        prompt_type = analysis_type_mapping.get(analysis_depth, 'comprehensive')
        
        # Perplexity 최적화 프롬프트 생성
        prompt = self.research_engine.generate_sector_research_prompt(
            focus_sectors=sectors_to_analyze,
            analysis_type=prompt_type
        )
        
        # LLM 요청 생성
        llm_request = LLMRequest(
            prompt=prompt,
            agent_type=self.agent_type,
            max_tokens=4000 if analysis_depth == 'comprehensive' else 3000,
            temperature=0.3,  # 팩트 체크가 중요하므로 낮은 temperature
            metadata={
                'analysis_depth': analysis_depth,
                'sectors_count': len(sectors_to_analyze),
                'request_type': 'sector_research'
            }
        )
        
        # Perplexity 호출
        start_time = time.time()
        llm_response = self.llm_client.generate_response(llm_request)
        response_time = time.time() - start_time
        
        logger.info(f"Perplexity 응답 완료 - 소요시간: {response_time:.2f}초, "
                   f"토큰: {llm_response.tokens_used}, 비용: ${llm_response.cost:.4f}")
        
        # 응답 품질 검증
        if llm_response.confidence_score < 0.7:
            logger.warning(f"낮은 응답 품질 - 신뢰도: {llm_response.confidence_score:.2f}")
        
        # 응답 파싱 및 구조화
        research_result = self.research_engine.parse_llm_response(llm_response.content)
        
        # 메타데이터 추가
        research_result.confidence_indicators.update({
            'llm_confidence': llm_response.confidence_score,
            'response_time': response_time,
            'tokens_used': llm_response.tokens_used,
            'has_citations': llm_response.metadata.get('has_citations', False),
            'search_enhanced': llm_response.metadata.get('search_enhanced', True)
        })
        
        return research_result
    
    def _perform_mock_analysis(self, focus_sectors: List[str], analysis_depth: str) -> SectorResearchResult:
        """
        Mock 모드 섹터 분석 (개발/테스트용)
        
        Args:
            focus_sectors: 분석 대상 섹터
            analysis_depth: 분석 깊이
            
        Returns:
            SectorResearchResult: Mock 분석 결과
        """
        logger.info(f"Mock 모드로 섹터 분석 수행 - 대상: {len(focus_sectors)}개 섹터")
        
        # Mock 응답 생성 (실제 LLM 응답을 시뮬레이션)
        mock_response = f"""
        Mock 섹터 분석 결과 ({datetime.now().strftime('%Y-%m-%d %H:%M')})
        
        분석 대상 섹터: {', '.join(focus_sectors[:5])}
        
        주요 발견사항:
        1. {focus_sectors[0]} 섹터가 현재 가장 높은 성장 잠재력을 보임
        2. 정부 정책 변화로 {focus_sectors[1]} 섹터에 긍정적 영향 예상
        3. 글로벌 경제 상황으로 인해 {focus_sectors[2]} 섹터는 주의 필요
        
        투자 추천: {focus_sectors[0]}, {focus_sectors[1]} 섹터 우선 고려
        """
        
        # Mock 결과를 실제 결과 형태로 파싱
        research_result = self.research_engine.parse_llm_response(mock_response)
        
        # Mock 특화 메타데이터
        research_result.confidence_indicators.update({
            'mock_mode': True,
            'data_freshness': 0.5,  # Mock은 신선도가 낮음
            'source_reliability': 0.6  # Mock은 신뢰도가 낮음
        })
        
        return research_result
    
    def _generate_summary(self, research_result: SectorResearchResult) -> str:
        """
        분석 결과 요약 생성
        
        Args:
            research_result: 섹터 리서치 결과
            
        Returns:
            str: 분석 요약
        """
        top_sectors = research_result.sector_rankings[:3]
        
        summary = f"""
섹터 리서치 요약 ({research_result.research_timestamp.strftime('%Y-%m-%d %H:%M')})

🏆 최고 섹터 TOP 3:
1. {top_sectors[0].sector_name} (점수: {top_sectors[0].trend_score:.1f}/100)
2. {top_sectors[1].sector_name} (점수: {top_sectors[1].trend_score:.1f}/100)  
3. {top_sectors[2].sector_name} (점수: {top_sectors[2].trend_score:.1f}/100)

💡 주요 투자 기회: {len(research_result.top_opportunities)}개 발굴
🔄 섹터 로테이션 신호: {len(research_result.rotation_signals)}개 감지

📈 시장 개요: {research_result.market_overview}

신뢰도: {research_result.confidence_indicators.get('analysis_confidence', 0.8):.1%}
        """.strip()
        
        return summary
    
    def _generate_recommendations(self, research_result: SectorResearchResult) -> List[Dict[str, Any]]:
        """
        투자 추천 생성
        
        Args:
            research_result: 섹터 리서치 결과
            
        Returns:
            List[Dict[str, Any]]: 추천 목록
        """
        recommendations = []
        
        # 상위 3개 섹터 추천
        for i, sector_metrics in enumerate(research_result.sector_rankings[:3]):
            recommendation = {
                'rank': i + 1,
                'sector': sector_metrics.sector_name,
                'action': 'BUY' if sector_metrics.trend_score >= 70 else 'HOLD',
                'confidence': sector_metrics.trend_score / 100,
                'reasoning': f"트렌드 점수 {sector_metrics.trend_score:.1f}점, "
                           f"기회 수준 {sector_metrics.opportunity_level}",
                'risk_level': sector_metrics.risk_level,
                'time_horizon': '중기' if sector_metrics.trend_score >= 80 else '단기'
            }
            recommendations.append(recommendation)
        
        # 기회 기반 추천 추가
        for opportunity in research_result.top_opportunities:
            if opportunity.confidence_level >= 0.7:
                recommendations.append({
                    'rank': len(recommendations) + 1,
                    'sector': opportunity.sector_name,
                    'action': 'WATCH',
                    'confidence': opportunity.confidence_level,
                    'reasoning': opportunity.description,
                    'risk_level': '보통',
                    'time_horizon': opportunity.time_horizon,
                    'opportunity_type': opportunity.opportunity_type
                })
        
        return recommendations
    
    def _generate_cache_key(self, focus_sectors: List[str], analysis_depth: str) -> str:
        """캐시 키 생성"""
        sectors_key = '_'.join(sorted(focus_sectors))
        return f"{self.agent_type}_{analysis_depth}_{hash(sectors_key) % 10000}"
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """캐시 유효성 확인"""
        if cache_key not in self.analysis_cache:
            return False
        
        cache_entry = self.analysis_cache[cache_key]
        cache_time = cache_entry['timestamp']
        current_time = datetime.now()
        
        return (current_time - cache_time).total_seconds() < (self.cache_ttl_minutes * 60)
    
    def _update_cache(self, cache_key: str, data: Dict[str, Any]) -> None:
        """캐시 업데이트"""
        self.analysis_cache[cache_key] = {
            'timestamp': datetime.now(),
            'data': data
        }
        
        # 캐시 크기 제한 (최대 10개 항목)
        if len(self.analysis_cache) > 10:
            oldest_key = min(self.analysis_cache.keys(), 
                           key=lambda k: self.analysis_cache[k]['timestamp'])
            del self.analysis_cache[oldest_key]
    
    def _validate_output(self, output_data: Dict[str, Any]) -> None:
        """
        출력 데이터 검증
        
        Args:
            output_data: 출력 데이터
            
        Raises:
            ValueError: 출력 데이터가 유효하지 않은 경우
        """
        super()._validate_output(output_data)
        
        # 섹터 리서치 특화 검증
        required_fields = ['research_result', 'analysis_metadata', 'summary', 'recommendations']
        for field in required_fields:
            if field not in output_data:
                raise ValueError(f"필수 필드 '{field}'가 출력에 없습니다")
        
        # 연구 결과 검증
        research_result = output_data['research_result']
        if not research_result.get('sector_rankings'):
            raise ValueError("섹터 순위 데이터가 없습니다")
        
        # 추천 데이터 검증
        recommendations = output_data['recommendations']
        if not isinstance(recommendations, list):
            raise ValueError("추천 데이터는 리스트 형태여야 합니다")
    
    def _calculate_confidence(self, result_data: Dict[str, Any]) -> float:
        """
        결과에 대한 신뢰도 점수 계산
        
        Args:
            result_data: 결과 데이터
            
        Returns:
            float: 신뢰도 점수 (0.0 ~ 1.0)
        """
        try:
            research_result = result_data['research_result']
            confidence_indicators = research_result.get('confidence_indicators', {})
            
            # 여러 신뢰도 지표의 가중 평균
            base_confidence = confidence_indicators.get('analysis_confidence', 0.8)
            data_freshness = confidence_indicators.get('data_freshness', 0.8)
            source_reliability = confidence_indicators.get('source_reliability', 0.8)
            llm_confidence = confidence_indicators.get('llm_confidence', 0.8)
            
            # 가중 평균 계산
            weights = [0.3, 0.2, 0.2, 0.3]  # base, freshness, reliability, llm
            confidences = [base_confidence, data_freshness, source_reliability, llm_confidence]
            
            weighted_confidence = sum(w * c for w, c in zip(weights, confidences))
            
            # LLM 사용 여부에 따른 보정
            if not self.llm_available:
                weighted_confidence *= 0.7  # Mock 모드는 신뢰도 감소
            
            return max(0.0, min(1.0, weighted_confidence))
            
        except Exception as e:
            logger.warning(f"신뢰도 계산 중 오류: {e}")
            return 0.6  # 기본값
    
    def get_agent_info(self) -> Dict[str, Any]:
        """에이전트 정보 반환"""
        base_info = super().get_agent_info()
        
        # 섹터 리서치 특화 정보 추가
        base_info.update({
            'specialization': '실시간 섹터 트렌드 분석',
            'supported_sectors': len(self.research_engine.sectors),
            'analysis_depths': ['basic', 'detailed', 'comprehensive'],
            'cache_ttl_minutes': self.cache_ttl_minutes,
            'real_time_search': self.llm_available,
            'default_focus_sectors': self.default_focus_sectors
        })
        
        return base_info
    
    def clear_cache(self) -> None:
        """분석 캐시 클리어"""
        self.analysis_cache.clear()
        logger.info("섹터 분석 캐시가 클리어되었습니다")
    
    def get_cache_status(self) -> Dict[str, Any]:
        """캐시 상태 정보 반환"""
        return {
            'cache_entries': len(self.analysis_cache),
            'cache_ttl_minutes': self.cache_ttl_minutes,
            'cached_keys': list(self.analysis_cache.keys())
        }