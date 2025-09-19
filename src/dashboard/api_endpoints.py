#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
대시보드 API 엔드포인트
Flask 기반 REST API로 실시간 성과 데이터 제공
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import traceback

from .dashboard_data_pipeline import get_dashboard_pipeline
from .performance_metrics import PerformanceMetricsCalculator


class DashboardAPI:
    """대시보드 API 서버"""
    
    def __init__(self, host: str = "localhost", port: int = 8080, debug: bool = True):
        self.app = Flask(__name__)
        self.host = host
        self.port = port
        self.debug = debug
        
        # CORS 설정 (프론트엔드와의 연동을 위해)
        CORS(self.app)
        
        # 파이프라인 및 계산기 인스턴스
        self.pipeline = get_dashboard_pipeline()
        self.metrics_calculator = PerformanceMetricsCalculator()
        
        # API 라우트 설정
        self._setup_routes()
        
        print(f"🌐 대시보드 API 서버 초기화: http://{host}:{port}")
    
    def _setup_routes(self):
        """API 라우트 설정"""
        
        @self.app.route('/api/health', methods=['GET'])
        def health_check():
            """헬스 체크"""
            try:
                pipeline_status = self.pipeline.get_health_status()
                return jsonify({
                    'status': 'healthy',
                    'timestamp': datetime.now().isoformat(),
                    'pipeline': pipeline_status
                })
            except Exception as e:
                return jsonify({
                    'status': 'error',
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500
        
        @self.app.route('/api/metrics/realtime', methods=['GET'])
        def get_realtime_metrics():
            """실시간 성과 메트릭 조회"""
            try:
                # 강제 새로고침 옵션
                refresh = request.args.get('refresh', 'false').lower() == 'true'
                
                metrics = self.metrics_calculator.get_real_time_metrics(refresh_cache=refresh)
                
                return jsonify({
                    'success': True,
                    'data': metrics.to_dict(),
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500
        
        @self.app.route('/api/metrics/history', methods=['GET'])
        def get_metrics_history():
            """메트릭 히스토리 조회"""
            try:
                hours = int(request.args.get('hours', '24'))
                
                history = self.pipeline.get_cached_metrics(hours_back=hours)
                
                return jsonify({
                    'success': True,
                    'data': history,
                    'period_hours': hours,
                    'count': len(history),
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500
        
        @self.app.route('/api/agents/ranking', methods=['GET'])
        def get_agent_ranking():
            """에이전트 성과 순위"""
            try:
                period_days = int(request.args.get('days', '7'))
                
                ranking = self.metrics_calculator.get_agent_ranking(period_days=period_days)
                
                return jsonify({
                    'success': True,
                    'data': ranking,
                    'period_days': period_days,
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500
        
        @self.app.route('/api/agents/<agent_name>/performance', methods=['GET'])
        def get_agent_performance(agent_name: str):
            """특정 에이전트 성과 상세"""
            try:
                days = int(request.args.get('days', '30'))
                
                # 에이전트별 성과 데이터 조회
                contribution_analysis = self.metrics_calculator.db_manager.get_agent_contribution_analysis(days=days)
                agent_impact = contribution_analysis.get('agent_impact', {}).get(agent_name)
                
                if not agent_impact:
                    return jsonify({
                        'success': False,
                        'error': f'에이전트 {agent_name}의 데이터를 찾을 수 없습니다',
                        'timestamp': datetime.now().isoformat()
                    }), 404
                
                # 추가 상세 정보
                performance_history = self.metrics_calculator.db_manager.get_agent_performance(
                    agent_name=agent_name, days=days
                )
                
                return jsonify({
                    'success': True,
                    'data': {
                        'agent_name': agent_name,
                        'impact_analysis': agent_impact,
                        'performance_history': performance_history,
                        'period_days': days
                    },
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500
        
        @self.app.route('/api/llm/usage', methods=['GET'])
        def get_llm_usage():
            """LLM 사용량 통계"""
            try:
                days = int(request.args.get('days', '7'))
                
                usage_stats = self.metrics_calculator.db_manager.get_llm_usage_stats(days=days)
                
                return jsonify({
                    'success': True,
                    'data': usage_stats,
                    'period_days': days,
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500
        
        @self.app.route('/api/cost/efficiency', methods=['GET'])
        def get_cost_efficiency():
            """비용 효율성 분석"""
            try:
                analysis = self.metrics_calculator.get_cost_efficiency_analysis()
                
                return jsonify({
                    'success': True,
                    'data': analysis,
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500
        
        @self.app.route('/api/system/overview', methods=['GET'])
        def get_system_overview():
            """시스템 전체 개요"""
            try:
                # 실시간 메트릭
                realtime_metrics = self.metrics_calculator.get_real_time_metrics()
                
                # 에이전트 순위
                agent_ranking = self.metrics_calculator.get_agent_ranking(period_days=7)
                
                # 비용 효율성
                cost_efficiency = self.metrics_calculator.get_cost_efficiency_analysis()
                
                # LLM 사용량
                llm_usage = self.metrics_calculator.db_manager.get_llm_usage_stats(days=1)
                
                return jsonify({
                    'success': True,
                    'data': {
                        'realtime_metrics': realtime_metrics.to_dict(),
                        'top_agents': agent_ranking[:5],  # 상위 5개만
                        'cost_efficiency': cost_efficiency,
                        'llm_summary': {
                            'total_requests': sum(
                                p.get('total_requests', 0) 
                                for p in llm_usage.get('provider_stats', {}).values()
                            ),
                            'total_cost': sum(
                                p.get('total_cost', 0)
                                for p in llm_usage.get('provider_stats', {}).values() 
                            ),
                            'providers': list(llm_usage.get('provider_stats', {}).keys())
                        }
                    },
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'traceback': traceback.format_exc() if self.debug else None,
                    'timestamp': datetime.now().isoformat()
                }), 500
        
        @self.app.route('/api/export/snapshot', methods=['POST'])
        def export_snapshot():
            """현재 상태 스냅샷 export"""
            try:
                filename = request.json.get('filename') if request.is_json else None
                
                filepath = self.pipeline.export_current_snapshot(filename=filename)
                
                return jsonify({
                    'success': True,
                    'filepath': filepath,
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500
        
        @self.app.route('/api/pipeline/control', methods=['POST'])
        def control_pipeline():
            """파이프라인 제어 (시작/중지/새로고침)"""
            try:
                if not request.is_json:
                    return jsonify({'success': False, 'error': 'JSON 요청이 필요합니다'}), 400
                
                action = request.json.get('action')
                
                if action == 'start':
                    self.pipeline.start()
                    message = '파이프라인이 시작되었습니다'
                    
                elif action == 'stop':
                    self.pipeline.stop()
                    message = '파이프라인이 중지되었습니다'
                    
                elif action == 'refresh':
                    self.pipeline.force_update()
                    message = '파이프라인이 새로고침되었습니다'
                    
                else:
                    return jsonify({
                        'success': False, 
                        'error': f'알 수 없는 액션: {action}',
                        'valid_actions': ['start', 'stop', 'refresh']
                    }), 400
                
                return jsonify({
                    'success': True,
                    'message': message,
                    'action': action,
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500
        
        @self.app.errorhandler(404)
        def not_found(error):
            return jsonify({
                'success': False,
                'error': 'API 엔드포인트를 찾을 수 없습니다',
                'timestamp': datetime.now().isoformat()
            }), 404
        
        @self.app.errorhandler(500)
        def internal_error(error):
            return jsonify({
                'success': False,
                'error': '서버 내부 오류가 발생했습니다',
                'timestamp': datetime.now().isoformat()
            }), 500
    
    def run(self, **kwargs):
        """API 서버 실행"""
        print(f"🚀 대시보드 API 서버 시작: http://{self.host}:{self.port}")
        
        # 파이프라인이 시작되지 않았으면 시작
        if not self.pipeline.get_health_status()['is_running']:
            self.pipeline.start()
        
        # Flask 서버 실행
        self.app.run(
            host=self.host,
            port=self.port,
            debug=self.debug,
            **kwargs
        )
    
    def get_app(self):
        """Flask 앱 인스턴스 반환 (WSGI 서버용)"""
        return self.app


def create_dashboard_api(host: str = "localhost", port: int = 8080, debug: bool = True) -> DashboardAPI:
    """대시보드 API 인스턴스 생성"""
    return DashboardAPI(host=host, port=port, debug=debug)


# 개발용 실행 스크립트
if __name__ == "__main__":
    api = create_dashboard_api(debug=True)
    api.run()