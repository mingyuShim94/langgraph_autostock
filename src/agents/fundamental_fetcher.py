"""
펀더멘털 페처 에이전트 (Gemini 2.5 Flash-Lite)

재무제표, 공시 정보, 뉴스 데이터를 효율적으로 수집하고 
Gemini 2.5 Flash-Lite를 활용하여 구조화된 분석 리포트를 생성하는 에이전트
"""

import logging
import time
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import asdict

from src.agents.base_agent import BaseAgent, AgentContext
from src.utils.fundamental_data_engine import (
    FundamentalDataEngine, FundamentalData, FinancialRatio, 
    NewsData, IndustryComparison, DataQuality
)


class FundamentalFetcherAgent(BaseAgent):
    """펀더멘털 데이터 수집 및 분석 에이전트"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        펀더멘털 페처 에이전트 초기화
        
        Args:
            config: 에이전트 설정
        """
        # BaseAgent 초기화 (agent_llm_mapping.yaml의 fundamental_fetcher 설정 사용)
        super().__init__("fundamental_fetcher", config)
        
        # 펀더멘털 데이터 엔진 초기화
        engine_config = config or {}
        self.data_engine = FundamentalDataEngine(
            cache_ttl_minutes=engine_config.get('cache_ttl_minutes', 5),
            mock_mode=engine_config.get('mock_mode', False)
        )
        
        # 에이전트 설정
        self.max_tickers_per_request = engine_config.get('max_tickers_per_request', 10)
        self.include_ai_analysis = engine_config.get('include_ai_analysis', True)
        self.analysis_depth = engine_config.get('analysis_depth', 'medium')  # light, medium, deep
        
        self.logger.info("✅ 펀더멘털 페처 에이전트 초기화 완료")
    
    def _validate_input(self, input_data: Dict[str, Any]) -> None:
        """입력 데이터 검증"""
        super()._validate_input(input_data)
        
        if 'tickers' not in input_data:
            raise ValueError("'tickers' 필드가 필요합니다")
        
        tickers = input_data['tickers']
        if not isinstance(tickers, list) or len(tickers) == 0:
            raise ValueError("'tickers'는 비어있지 않은 리스트여야 합니다")
        
        if len(tickers) > self.max_tickers_per_request:
            raise ValueError(f"한 번에 처리할 수 있는 종목 수는 최대 {self.max_tickers_per_request}개입니다")
        
        # 종목 코드 형식 검증
        for ticker in tickers:
            if not isinstance(ticker, str) or len(ticker) != 6 or not ticker.isdigit():
                raise ValueError(f"잘못된 종목 코드 형식: {ticker}")
    
    def _validate_output(self, output_data: Dict[str, Any]) -> None:
        """출력 데이터 검증"""
        super()._validate_output(output_data)
        
        required_fields = ['fundamental_data', 'analysis_summary', 'data_quality', 'collection_stats']
        for field in required_fields:
            if field not in output_data:
                raise ValueError(f"출력 데이터에 '{field}' 필드가 누락되었습니다")
    
    def _process(self, context: AgentContext) -> Dict[str, Any]:
        """
        펀더멘털 데이터 수집 및 분석 처리
        
        Args:
            context: 에이전트 실행 컨텍스트
            
        Returns:
            Dict[str, Any]: 처리 결과 데이터
        """
        input_data = context.input_data
        tickers = input_data['tickers']
        
        # 선택적 설정
        include_news = input_data.get('include_news', True)
        include_industry_comparison = input_data.get('include_industry_comparison', True)
        sector_context = input_data.get('sector_context', {})  # 섹터 리서치 결과
        screening_context = input_data.get('screening_context', {})  # 티커 스크리닝 결과
        
        self.logger.info(f"🔍 펀더멘털 데이터 수집 시작: {len(tickers)}개 종목")
        
        # 1. 펀더멘털 데이터 수집
        fundamental_data_dict = self._collect_fundamental_data(
            tickers, include_news, include_industry_comparison
        )
        
        # 2. AI 기반 분석 및 요약 (Gemini 2.5 Flash-Lite)
        analysis_summary = {}
        if self.include_ai_analysis:
            analysis_summary = self._perform_ai_analysis(
                fundamental_data_dict, sector_context, screening_context
            )
        
        # 3. 데이터 품질 평가
        data_quality = self._assess_data_quality(fundamental_data_dict)
        
        # 4. 수집 통계
        collection_stats = self._calculate_collection_stats(fundamental_data_dict)
        
        # 5. 결과 데이터 구성
        result_data = {
            'fundamental_data': {ticker: asdict(data) for ticker, data in fundamental_data_dict.items()},
            'analysis_summary': analysis_summary,
            'data_quality': data_quality,
            'collection_stats': collection_stats,
            'metadata': {
                'processed_tickers': tickers,
                'total_tickers': len(tickers),
                'processing_timestamp': datetime.now().isoformat(),
                'agent_version': "1.0.0",
                'engine_config': {
                    'cache_ttl_minutes': self.data_engine.cache_ttl_minutes,
                    'mock_mode': self.data_engine.mock_mode,
                    'kis_authenticated': self.data_engine.kis_authenticated
                }
            }
        }
        
        self.logger.info(f"✅ 펀더멘털 데이터 수집 완료: {len(fundamental_data_dict)}개 종목")
        return result_data
    
    def _collect_fundamental_data(
        self, 
        tickers: List[str], 
        include_news: bool, 
        include_industry_comparison: bool
    ) -> Dict[str, FundamentalData]:
        """펀더멘털 데이터 수집"""
        fundamental_data = {}
        
        for ticker in tickers:
            try:
                self.logger.info(f"📊 데이터 수집 중: {ticker}")
                
                data = self.data_engine.collect_fundamental_data(
                    ticker=ticker,
                    include_news=include_news,
                    include_industry_comparison=include_industry_comparison
                )
                
                fundamental_data[ticker] = data
                
            except Exception as e:
                self.logger.error(f"❌ 데이터 수집 실패: {ticker} - {e}")
                # 실패한 종목도 Mock 데이터로 포함
                try:
                    mock_data = self.data_engine._generate_mock_fundamental_data(ticker)
                    fundamental_data[ticker] = mock_data
                except Exception as mock_error:
                    self.logger.error(f"❌ Mock 데이터 생성도 실패: {ticker} - {mock_error}")
        
        return fundamental_data
    
    def _perform_ai_analysis(
        self, 
        fundamental_data: Dict[str, FundamentalData],
        sector_context: Dict[str, Any],
        screening_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Gemini 2.5 Flash-Lite를 활용한 AI 분석"""
        try:
            # 분석용 프롬프트 구성
            analysis_prompt = self._build_analysis_prompt(
                fundamental_data, sector_context, screening_context
            )
            
            # Gemini 2.5 Flash-Lite로 분석 요청
            response = self.query_llm(
                prompt=analysis_prompt,
                temperature=0.4,  # 일관된 분석을 위한 낮은 temperature
                max_tokens=2000
            )
            
            # 응답 파싱 및 구조화
            analysis_result = self._parse_ai_analysis_response(response.content)
            
            return {
                'ai_analysis': analysis_result,
                'llm_metadata': {
                    'model_used': response.model_used,
                    'tokens_used': response.tokens_used,
                    'cost': response.cost,
                    'response_time': response.response_time,
                    'confidence_score': response.confidence_score
                }
            }
            
        except Exception as e:
            self.logger.error(f"❌ AI 분석 실패: {e}")
            return {
                'ai_analysis': {
                    'error': str(e),
                    'fallback_summary': self._generate_fallback_analysis(fundamental_data)
                },
                'llm_metadata': {'error': str(e)}
            }
    
    def _build_analysis_prompt(
        self, 
        fundamental_data: Dict[str, FundamentalData],
        sector_context: Dict[str, Any],
        screening_context: Dict[str, Any]
    ) -> str:
        """AI 분석용 프롬프트 구성"""
        
        # 기본 데이터 요약
        tickers = list(fundamental_data.keys())
        data_summary = []
        
        for ticker in tickers[:5]:  # 최대 5개 종목만 상세 분석
            data = fundamental_data[ticker]
            fr = data.financial_ratios
            
            ticker_summary = f"""
종목 {ticker} ({data.company_name}):
- 재무지표: PER={fr.per}, PBR={fr.pbr}, ROE={fr.roe}%, 부채비율={fr.debt_ratio}%
- 수익성: 영업이익률={fr.operating_margin}%, 순이익률={fr.net_margin}%
- 성장성: 매출성장률={fr.revenue_growth}%, 순이익성장률={fr.profit_growth}%
- 최근 뉴스: {len(data.news_data)}건 (평균 감정점수: {sum(n.sentiment_score for n in data.news_data)/len(data.news_data) if data.news_data else 0:.2f})
- 업계 순위: {data.industry_comparison.rank_in_industry}/{data.industry_comparison.total_companies} (상위 {data.industry_comparison.percentile:.1f}%)
"""
            data_summary.append(ticker_summary)
        
        # 섹터 컨텍스트 요약
        sector_summary = ""
        if sector_context:
            sector_summary = f"""
섹터 리서치 결과:
- 유망 섹터: {sector_context.get('top_sectors', [])}
- 시장 트렌드: {sector_context.get('market_trends', 'N/A')}
- 섹터 모멘텀: {sector_context.get('sector_momentum', 'N/A')}
"""
        
        # 스크리닝 컨텍스트 요약
        screening_summary = ""
        if screening_context:
            screening_summary = f"""
티커 스크리닝 결과:
- 선별 기준: {screening_context.get('selection_criteria', 'N/A')}
- 순위 방법: {screening_context.get('ranking_method', 'N/A')}
- 필터링 조건: {screening_context.get('filtering_conditions', 'N/A')}
"""
        
        prompt = f"""당신은 펀더멘털 분석 전문가입니다. 다음 종목들의 펀더멘털 데이터를 분석하여 투자 관점에서 종합적인 인사이트를 제공해주세요.

{sector_summary}
{screening_summary}

== 분석 대상 종목 데이터 ==
{''.join(data_summary)}

== 분석 요청 사항 ==
1. **종목별 펀더멘털 평가**: 각 종목의 재무 건전성과 투자 매력도 평가
2. **상대적 비교 분석**: 종목 간 비교를 통한 우선순위 제시
3. **리스크 요인 식별**: 주요 투자 리스크와 주의사항
4. **투자 전략 제안**: 펀더멘털 관점에서의 투자 전략 및 타이밍

== 응답 형식 ==
JSON 형태로 다음과 같이 응답해주세요:
{{
  "overall_assessment": "전체적인 펀더멘털 평가",
  "top_picks": ["상위 추천 종목 3개"],
  "risk_warnings": ["주요 리스크 요인들"],
  "investment_strategy": "펀더멘털 기반 투자 전략",
  "market_outlook": "시장 전망 및 관련 이슈",
  "confidence_level": "분석 신뢰도 (1-10점)"
}}

분석은 한국 주식시장 특성을 고려하여 실용적이고 구체적으로 작성해주세요."""
        
        return prompt
    
    def _parse_ai_analysis_response(self, response_content: str) -> Dict[str, Any]:
        """AI 분석 응답 파싱"""
        try:
            # JSON 응답 파싱 시도
            if '{' in response_content and '}' in response_content:
                start = response_content.find('{')
                end = response_content.rfind('}') + 1
                json_str = response_content[start:end]
                
                analysis = json.loads(json_str)
                
                # 필수 필드 검증 및 기본값 설정
                required_fields = {
                    'overall_assessment': '분석 결과를 파싱할 수 없습니다.',
                    'top_picks': [],
                    'risk_warnings': [],
                    'investment_strategy': '전략을 파싱할 수 없습니다.',
                    'market_outlook': '전망을 파싱할 수 없습니다.',
                    'confidence_level': 5
                }
                
                for field, default in required_fields.items():
                    if field not in analysis:
                        analysis[field] = default
                
                return analysis
            
            # JSON 파싱 실패 시 텍스트 분석
            return self._parse_text_analysis(response_content)
            
        except Exception as e:
            self.logger.error(f"❌ AI 응답 파싱 실패: {e}")
            return {
                'overall_assessment': response_content[:500] + "..." if len(response_content) > 500 else response_content,
                'top_picks': [],
                'risk_warnings': ['AI 응답 파싱 오류'],
                'investment_strategy': '분석 결과를 확인할 수 없습니다.',
                'market_outlook': '파싱 오류로 인해 전망을 확인할 수 없습니다.',
                'confidence_level': 3,
                'parsing_error': str(e)
            }
    
    def _parse_text_analysis(self, text: str) -> Dict[str, Any]:
        """텍스트 형태 응답을 구조화"""
        # 간단한 키워드 기반 파싱
        lines = text.split('\n')
        
        assessment = ""
        strategy = ""
        
        for line in lines:
            if any(keyword in line.lower() for keyword in ['평가', '전체', '종합']):
                assessment += line + " "
            elif any(keyword in line.lower() for keyword in ['전략', '투자', '추천']):
                strategy += line + " "
        
        return {
            'overall_assessment': assessment.strip() or text[:200] + "...",
            'top_picks': [],
            'risk_warnings': ['텍스트 형태 응답으로 일부 정보 누락 가능'],
            'investment_strategy': strategy.strip() or '구체적인 전략 정보 없음',
            'market_outlook': '텍스트 파싱 결과 전망 정보 없음',
            'confidence_level': 4
        }
    
    def _generate_fallback_analysis(self, fundamental_data: Dict[str, FundamentalData]) -> Dict[str, Any]:
        """AI 분석 실패 시 기본 분석 생성"""
        tickers = list(fundamental_data.keys())
        
        # 간단한 점수 기반 순위
        scores = {}
        for ticker, data in fundamental_data.items():
            fr = data.financial_ratios
            score = 0
            
            # PER 점수 (낮을수록 좋음)
            if fr.per and fr.per > 0:
                score += max(0, 25 - fr.per) / 25 * 20
            
            # ROE 점수 (높을수록 좋음)
            if fr.roe and fr.roe > 0:
                score += min(fr.roe, 20) / 20 * 20
            
            # 부채비율 점수 (낮을수록 좋음)
            if fr.debt_ratio and fr.debt_ratio > 0:
                score += max(0, 50 - fr.debt_ratio) / 50 * 15
            
            # 뉴스 감정 점수
            if data.news_data:
                avg_sentiment = sum(n.sentiment_score for n in data.news_data) / len(data.news_data)
                score += (avg_sentiment + 1) / 2 * 10  # -1~1을 0~10으로 변환
            
            scores[ticker] = score
        
        # 상위 3개 종목
        top_picks = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)[:3]
        
        return {
            'overall_assessment': f'{len(fundamental_data)}개 종목 중 기본 재무지표 기반 분석을 수행했습니다.',
            'top_picks': top_picks,
            'risk_warnings': ['AI 분석 실패로 기본 분석만 제공됩니다.'],
            'investment_strategy': '재무지표 기반 상위 종목을 우선 검토하시기 바랍니다.',
            'market_outlook': 'AI 분석 없이는 시장 전망을 제공할 수 없습니다.',
            'confidence_level': 2
        }
    
    def _assess_data_quality(self, fundamental_data: Dict[str, FundamentalData]) -> Dict[str, Any]:
        """데이터 품질 평가"""
        if not fundamental_data:
            return {'overall_quality': 'poor', 'quality_score': 0.0}
        
        quality_scores = []
        source_distribution = {}
        
        for ticker, data in fundamental_data.items():
            # 개별 종목 품질 점수
            ticker_score = data.confidence_score
            quality_scores.append(ticker_score)
            
            # 데이터 소스 분포
            source = data.financial_ratios.source
            source_distribution[source] = source_distribution.get(source, 0) + 1
        
        avg_quality = sum(quality_scores) / len(quality_scores)
        
        # 품질 등급 결정
        if avg_quality >= 0.8:
            quality_grade = 'excellent'
        elif avg_quality >= 0.6:
            quality_grade = 'good'
        elif avg_quality >= 0.4:
            quality_grade = 'fair'
        else:
            quality_grade = 'poor'
        
        return {
            'overall_quality': quality_grade,
            'quality_score': round(avg_quality, 3),
            'individual_scores': {ticker: round(score, 3) for ticker, score in zip(fundamental_data.keys(), quality_scores)},
            'source_distribution': source_distribution,
            'total_tickers': len(fundamental_data),
            'assessment_timestamp': datetime.now().isoformat()
        }
    
    def _calculate_collection_stats(self, fundamental_data: Dict[str, FundamentalData]) -> Dict[str, Any]:
        """수집 통계 계산"""
        if not fundamental_data:
            return {}
        
        # 수집 시간 통계
        collection_times = [data.collection_time for data in fundamental_data.values()]
        avg_collection_time = sum(collection_times) / len(collection_times)
        
        # 데이터 완성도 통계
        completeness_scores = []
        for data in fundamental_data.values():
            fr = data.financial_ratios
            fields = [fr.per, fr.pbr, fr.roe, fr.debt_ratio, fr.operating_margin]
            completed_fields = sum(1 for field in fields if field is not None)
            completeness = completed_fields / len(fields)
            completeness_scores.append(completeness)
        
        avg_completeness = sum(completeness_scores) / len(completeness_scores)
        
        # 뉴스 통계
        news_stats = {
            'total_news': sum(len(data.news_data) for data in fundamental_data.values()),
            'avg_news_per_ticker': sum(len(data.news_data) for data in fundamental_data.values()) / len(fundamental_data),
            'avg_sentiment': 0.0
        }
        
        all_sentiments = []
        for data in fundamental_data.values():
            for news in data.news_data:
                all_sentiments.append(news.sentiment_score)
        
        if all_sentiments:
            news_stats['avg_sentiment'] = sum(all_sentiments) / len(all_sentiments)
        
        # 캐시 통계
        cache_stats = self.data_engine.get_cache_stats()
        
        return {
            'collection_performance': {
                'avg_collection_time': round(avg_collection_time, 3),
                'min_collection_time': round(min(collection_times), 3),
                'max_collection_time': round(max(collection_times), 3),
                'total_collection_time': round(sum(collection_times), 3)
            },
            'data_completeness': {
                'avg_completeness': round(avg_completeness, 3),
                'completeness_scores': {ticker: round(score, 3) for ticker, score in zip(fundamental_data.keys(), completeness_scores)}
            },
            'news_statistics': news_stats,
            'cache_statistics': cache_stats,
            'timestamp': datetime.now().isoformat()
        }
    
    def _calculate_confidence(self, result_data: Dict[str, Any]) -> float:
        """결과 신뢰도 계산"""
        if not result_data.get('fundamental_data'):
            return 0.0
        
        # 데이터 품질 기반 신뢰도
        data_quality_score = result_data.get('data_quality', {}).get('quality_score', 0.0)
        
        # AI 분석 신뢰도
        ai_confidence = 0.0
        if 'analysis_summary' in result_data and 'ai_analysis' in result_data['analysis_summary']:
            ai_analysis = result_data['analysis_summary']['ai_analysis']
            if isinstance(ai_analysis, dict) and 'confidence_level' in ai_analysis:
                ai_confidence = ai_analysis['confidence_level'] / 10.0
        
        # 전체 신뢰도 (데이터 품질 70% + AI 분석 30%)
        overall_confidence = data_quality_score * 0.7 + ai_confidence * 0.3
        
        return round(overall_confidence, 3)


# 편의 함수들
def create_fundamental_fetcher(mock_mode: bool = False) -> FundamentalFetcherAgent:
    """펀더멘털 페처 에이전트 생성 편의 함수"""
    config = {'mock_mode': mock_mode}
    return FundamentalFetcherAgent(config)


def fetch_fundamental_data(tickers: List[str], mock_mode: bool = False) -> Dict[str, Any]:
    """펀더멘털 데이터 수집 편의 함수"""
    from src.agents.base_agent import AgentContext
    from datetime import datetime
    
    agent = create_fundamental_fetcher(mock_mode)
    
    context = AgentContext(
        agent_id="fundamental_fetcher",
        execution_id=f"fetch_{int(time.time())}",
        timestamp=datetime.now(),
        input_data={'tickers': tickers}
    )
    
    result = agent.execute(context)
    return result.result_data if result.success else {}


if __name__ == "__main__":
    # 테스트 실행
    logging.basicConfig(level=logging.INFO)
    
    # 단일 종목 테스트
    print("🧪 펀더멘털 페처 에이전트 테스트")
    tickers = ["005930", "000660", "035420"]
    
    result = fetch_fundamental_data(tickers, mock_mode=True)
    
    if result:
        print(f"✅ 테스트 성공: {len(result.get('fundamental_data', {}))}개 종목 처리")
        print(f"📊 데이터 품질: {result.get('data_quality', {}).get('overall_quality', 'unknown')}")
        
        if 'analysis_summary' in result:
            ai_analysis = result['analysis_summary'].get('ai_analysis', {})
            if isinstance(ai_analysis, dict):
                print(f"🤖 AI 분석 신뢰도: {ai_analysis.get('confidence_level', 'N/A')}")
                print(f"📈 추천 종목: {ai_analysis.get('top_picks', [])}")
    else:
        print("❌ 테스트 실패")