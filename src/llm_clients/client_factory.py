"""
LLM 클라이언트 팩토리 패턴 구현

에이전트별 최적 LLM 클라이언트를 생성하고 관리하는 팩토리 클래스
"""

import yaml
import os
from typing import Dict, Any, Optional, Union
from pathlib import Path

from .base import BaseAgentLLM
from .claude import ClaudeClient
from .gpt import GPTClient
from .gemini import GeminiClient
from .perplexity import PerplexityClient
from .exceptions import ConfigurationError, ModelNotSupportedError


class LLMClientFactory:
    """LLM 클라이언트 생성 및 관리 팩토리"""
    
    # 지원하는 제공사별 클라이언트 클래스 매핑
    PROVIDER_CLASSES = {
        'claude': ClaudeClient,
        'gpt': GPTClient,
        'gemini': GeminiClient,
        'perplexity': PerplexityClient
    }
    
    def __init__(self, config_path: Optional[str] = None):
        """
        팩토리 초기화
        
        Args:
            config_path: agent_llm_mapping.yaml 파일 경로
        """
        self.config_path = config_path or "config/agent_llm_mapping.yaml"
        self.agent_mapping = {}
        self.api_keys = {}
        self.client_cache = {}  # 클라이언트 인스턴스 캐시
        
        # 설정 로드
        self._load_configuration()
        self._load_api_keys()
    
    def _load_configuration(self) -> None:
        """에이전트-LLM 매핑 설정 로드"""
        try:
            config_file_path = Path(self.config_path)
            if not config_file_path.exists():
                # 기본 설정 생성
                self._create_default_config()
            
            with open(config_file_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            self.agent_mapping = config.get('agents', {})
            
        except Exception as e:
            raise ConfigurationError("factory", f"설정 파일 로드 실패: {e}")
    
    def _load_api_keys(self) -> None:
        """환경 변수에서 API 키 로드"""
        self.api_keys = {
            'claude': os.getenv('ANTHROPIC_API_KEY'),
            'gpt': os.getenv('OPENAI_API_KEY'),
            'gemini': os.getenv('GOOGLE_AI_API_KEY'),
            'perplexity': os.getenv('PERPLEXITY_API_KEY')
        }
    
    def _create_default_config(self) -> None:
        """기본 에이전트-LLM 매핑 설정 파일 생성"""
        default_config = {
            'agents': {
                # 포트폴리오 및 기본 작업 (GPT-5 nano - 빠르고 경제적)
                'portfolio_rebalancer': {
                    'provider': 'gpt',
                    'model': 'gpt-5-nano',
                    'temperature': 0.1,
                    'max_tokens': 1000
                },
                'ticker_screener': {
                    'provider': 'gpt',
                    'model': 'gpt-5-nano',
                    'temperature': 0.2,
                    'max_tokens': 1500
                },
                'allocator': {
                    'provider': 'gpt',
                    'model': 'gpt-5-nano',
                    'temperature': 0.1,
                    'max_tokens': 800
                },
                'trade_planner': {
                    'provider': 'gpt',
                    'model': 'gpt-5-nano',
                    'temperature': 0.1,
                    'max_tokens': 1000
                },
                
                # 실시간 시장 조사 (Perplexity - 검색 특화)
                'sector_researcher': {
                    'provider': 'perplexity',
                    'model': 'sonar-pro',
                    'temperature': 0.3,
                    'max_tokens': 3000
                },
                
                # 펀더멘털 분석 전문가 팀 (Gemini Flash - 긴 컨텍스트)
                'fundamental_fetcher': {
                    'provider': 'gemini',
                    'model': 'flash-lite',
                    'temperature': 0.4,
                    'max_tokens': 2000
                },
                'valuation_analyst': {
                    'provider': 'gemini',
                    'model': 'flash-2.5',
                    'temperature': 0.5,
                    'max_tokens': 4000
                },
                'flow_analyst': {
                    'provider': 'gemini',
                    'model': 'flash-2.5',
                    'temperature': 0.5,
                    'max_tokens': 3000
                },
                'risk_analyst': {
                    'provider': 'gemini',
                    'model': 'flash-2.5',
                    'temperature': 0.3,
                    'max_tokens': 3000
                },
                
                # 기술적 분석 (GPT-5 - 정확한 계산 능력)
                'technical_analyst': {
                    'provider': 'gpt',
                    'model': 'gpt-5',
                    'temperature': 0.2,
                    'max_tokens': 3000
                },
                
                # 최종 의사결정 (Claude Opus - 최고 추론 능력)
                'cio': {
                    'provider': 'claude',
                    'model': 'opus-4.1',
                    'temperature': 0.6,
                    'max_tokens': 4000
                },
                
                # 성찰 및 자기 개조 시스템 (Claude Opus - 메타 인지)
                'performance_analyzer': {
                    'provider': 'claude',
                    'model': 'opus-4.1',
                    'temperature': 0.4,
                    'max_tokens': 5000
                },
                'failure_attribution': {
                    'provider': 'claude',
                    'model': 'opus-4.1',
                    'temperature': 0.3,
                    'max_tokens': 4000
                },
                'model_benchmarker': {
                    'provider': 'claude',
                    'model': 'opus-4.1',
                    'temperature': 0.2,
                    'max_tokens': 3000
                },
                'strategy_optimizer': {
                    'provider': 'claude',
                    'model': 'opus-4.1',
                    'temperature': 0.5,
                    'max_tokens': 4000
                }
            },
            
            'global_settings': {
                'cost_limit_daily': 50.0,  # 일일 비용 한도 (USD)
                'retry_attempts': 3,
                'timeout_seconds': 60,
                'enable_caching': True,
                'log_all_requests': True
            }
        }
        
        # 설정 디렉토리 생성
        config_dir = Path(self.config_path).parent
        config_dir.mkdir(parents=True, exist_ok=True)
        
        # 설정 파일 저장
        with open(self.config_path, 'w', encoding='utf-8') as f:
            yaml.dump(default_config, f, default_flow_style=False, allow_unicode=True)
    
    def create_client(self, agent_type: str, **override_config) -> BaseAgentLLM:
        """
        특정 에이전트를 위한 LLM 클라이언트 생성
        
        Args:
            agent_type: 에이전트 타입 (cio, technical_analyst 등)
            **override_config: 기본 설정을 덮어쓸 설정들
            
        Returns:
            BaseAgentLLM: 설정된 LLM 클라이언트
            
        Raises:
            ConfigurationError: 설정 오류
            ModelNotSupportedError: 지원하지 않는 모델
        """
        # 캐시에서 확인
        cache_key = f"{agent_type}_{hash(str(override_config))}"
        if cache_key in self.client_cache:
            return self.client_cache[cache_key]
        
        # 에이전트 설정 조회
        if agent_type not in self.agent_mapping:
            raise ConfigurationError("factory", f"정의되지 않은 에이전트 타입: {agent_type}")
        
        agent_config = self.agent_mapping[agent_type].copy()
        agent_config.update(override_config)  # 덮어쓰기 설정 적용
        
        # 제공사 및 모델 정보 추출
        provider = agent_config.pop('provider')
        model = agent_config.pop('model')
        
        # API 키 확인
        api_key = self.api_keys.get(provider)
        if not api_key:
            raise ConfigurationError("factory", f"{provider} API 키가 설정되지 않았습니다")
        
        # 제공사별 클라이언트 클래스 조회
        if provider not in self.PROVIDER_CLASSES:
            raise ConfigurationError("factory", f"지원하지 않는 제공사: {provider}")
        
        client_class = self.PROVIDER_CLASSES[provider]
        
        try:
            # 클라이언트 인스턴스 생성
            client = client_class(model, api_key, **agent_config)
            
            # 캐시에 저장
            self.client_cache[cache_key] = client
            
            return client
            
        except Exception as e:
            raise ConfigurationError("factory", f"{agent_type} 클라이언트 생성 실패: {e}")
    
    def get_agent_config(self, agent_type: str) -> Dict[str, Any]:
        """특정 에이전트의 설정 정보 반환"""
        if agent_type not in self.agent_mapping:
            raise ConfigurationError("factory", f"정의되지 않은 에이전트 타입: {agent_type}")
        
        return self.agent_mapping[agent_type].copy()
    
    def update_agent_config(self, agent_type: str, new_config: Dict[str, Any]) -> None:
        """
        에이전트 설정 업데이트 (자기 개조 시스템에서 사용)
        
        Args:
            agent_type: 에이전트 타입
            new_config: 새로운 설정 (provider, model 등)
        """
        if agent_type not in self.agent_mapping:
            raise ConfigurationError("factory", f"정의되지 않은 에이전트 타입: {agent_type}")
        
        # 기존 설정 업데이트
        self.agent_mapping[agent_type].update(new_config)
        
        # 캐시 무효화 (해당 에이전트 관련)
        keys_to_remove = [key for key in self.client_cache.keys() if key.startswith(agent_type)]
        for key in keys_to_remove:
            del self.client_cache[key]
        
        # 설정 파일 저장
        self._save_configuration()
    
    def _save_configuration(self) -> None:
        """현재 설정을 파일에 저장"""
        try:
            config = {
                'agents': self.agent_mapping,
                'global_settings': {
                    'cost_limit_daily': 50.0,
                    'retry_attempts': 3,
                    'timeout_seconds': 60,
                    'enable_caching': True,
                    'log_all_requests': True
                }
            }
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
                
        except Exception as e:
            raise ConfigurationError("factory", f"설정 파일 저장 실패: {e}")
    
    def get_all_agents(self) -> Dict[str, Dict[str, Any]]:
        """모든 에이전트 설정 반환"""
        return self.agent_mapping.copy()
    
    def clear_cache(self) -> None:
        """클라이언트 캐시 초기화"""
        self.client_cache.clear()
    
    def get_usage_summary(self) -> Dict[str, Any]:
        """캐시된 클라이언트들의 사용량 요약"""
        summary = {
            'total_clients': len(self.client_cache),
            'clients_by_provider': {},
            'total_requests': 0,
            'total_cost': 0.0
        }
        
        for client in self.client_cache.values():
            provider = client.provider_name
            if provider not in summary['clients_by_provider']:
                summary['clients_by_provider'][provider] = {
                    'count': 0,
                    'requests': 0,
                    'cost': 0.0
                }
            
            summary['clients_by_provider'][provider]['count'] += 1
            summary['clients_by_provider'][provider]['requests'] += client.usage_stats.total_requests
            summary['clients_by_provider'][provider]['cost'] += client.usage_stats.total_cost
            
            summary['total_requests'] += client.usage_stats.total_requests
            summary['total_cost'] += client.usage_stats.total_cost
        
        return summary
    
    def get_client_health_report(self) -> Dict[str, Dict[str, Any]]:
        """모든 클라이언트의 건강 상태 리포트"""
        health_report = {}
        
        for cache_key, client in self.client_cache.items():
            agent_type = cache_key.split('_')[0]
            health_report[agent_type] = {
                'provider': client.provider_name,
                'model': client.model_name,
                'is_healthy': client.is_healthy(),
                'success_rate': (client.usage_stats.successful_requests / 
                               max(client.usage_stats.total_requests, 1)),
                'total_requests': client.usage_stats.total_requests,
                'total_cost': client.usage_stats.total_cost,
                'avg_response_time': client.usage_stats.average_response_time
            }
        
        return health_report


# 글로벌 팩토리 인스턴스 (싱글톤 패턴)
_factory_instance = None

def get_llm_factory(config_path: Optional[str] = None) -> LLMClientFactory:
    """LLM 클라이언트 팩토리 싱글톤 인스턴스 반환"""
    global _factory_instance
    
    if _factory_instance is None:
        _factory_instance = LLMClientFactory(config_path)
    
    return _factory_instance


def create_agent_client(agent_type: str, **override_config) -> BaseAgentLLM:
    """편의 함수: 특정 에이전트용 클라이언트 생성"""
    factory = get_llm_factory()
    return factory.create_client(agent_type, **override_config)