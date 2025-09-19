#!/usr/bin/env python3
"""
LLM 클라이언트 연결 테스트 스크립트

모든 LLM API 키가 올바르게 설정되고 연결되는지 검증합니다.
"""

import os
import sys

# 환경 변수에서 API 키 읽기 (로컬에서 설정 필요)
# export ANTHROPIC_API_KEY="your_key_here"
# export OPENAI_API_KEY="your_key_here" 
# export GOOGLE_AI_API_KEY="your_key_here"
# export PERPLEXITY_API_KEY="your_key_here"

# 프로젝트 경로 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.llm_clients.base import LLMRequest
from src.llm_clients.claude import ClaudeClient
from src.llm_clients.gpt import GPTClient
from src.llm_clients.gemini import GeminiClient
from src.llm_clients.perplexity import PerplexityClient
from src.llm_clients.client_factory import get_llm_factory
# LLM 예외 클래스들은 개별 클라이언트에서 처리


def print_status(message: str, status: str = "INFO"):
    """상태 메시지 출력"""
    colors = {
        "INFO": "\033[94m",      # 파란색
        "SUCCESS": "\033[92m",   # 초록색
        "ERROR": "\033[91m",     # 빨간색
        "WARNING": "\033[93m"    # 노란색
    }
    reset = "\033[0m"
    print(f"{colors.get(status, '')}{status}: {message}{reset}")


def test_claude_client():
    """Claude 클라이언트 테스트"""
    print_status("🤖 Claude 클라이언트 테스트 시작...")
    
    try:
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            print_status("ANTHROPIC_API_KEY가 설정되지 않았습니다", "ERROR")
            return False
        
        # 클라이언트 생성
        client = ClaudeClient(model_name="sonnet-3.5", api_key=api_key)
        
        # 테스트 요청
        request = LLMRequest(
            prompt="안녕하세요! 간단한 연결 테스트입니다. '연결 성공'이라고 답해주세요.",
            agent_type="test",
            max_tokens=50
        )
        
        response = client.generate_response(request)
        
        print_status(f"Claude 응답: {response.content[:100]}...", "SUCCESS")
        print_status(f"토큰 사용: {response.tokens_used}, 비용: ${response.cost:.4f}", "INFO")
        return True
        
    except Exception as e:
        print_status(f"Claude 테스트 실패: {e}", "ERROR")
        return False


def test_gpt_client():
    """GPT 클라이언트 테스트"""
    print_status("🧠 GPT 클라이언트 테스트 시작...")
    
    try:
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            print_status("OPENAI_API_KEY가 설정되지 않았습니다", "ERROR")
            return False
        
        # 클라이언트 생성
        client = GPTClient(model_name="gpt-4o", api_key=api_key)
        
        # 테스트 요청
        request = LLMRequest(
            prompt="Hello! This is a connection test. Please respond with 'Connection successful'.",
            agent_type="test",
            max_tokens=50
        )
        
        response = client.generate_response(request)
        
        print_status(f"GPT 응답: {response.content[:100]}...", "SUCCESS")
        print_status(f"토큰 사용: {response.tokens_used}, 비용: ${response.cost:.4f}", "INFO")
        return True
        
    except Exception as e:
        print_status(f"GPT 테스트 실패: {e}", "ERROR")
        return False


def test_gemini_client():
    """Gemini 클라이언트 테스트"""
    print_status("💎 Gemini 클라이언트 테스트 시작...")
    
    try:
        api_key = os.getenv('GOOGLE_AI_API_KEY')
        if not api_key:
            print_status("GOOGLE_AI_API_KEY가 설정되지 않았습니다", "ERROR")
            return False
        
        # 클라이언트 생성
        client = GeminiClient(model_name="flash-1.5", api_key=api_key)
        
        # 테스트 요청
        request = LLMRequest(
            prompt="안녕하세요! 연결 테스트입니다. '연결 성공'이라고 답해주세요.",
            agent_type="test",
            max_tokens=50
        )
        
        response = client.generate_response(request)
        
        print_status(f"Gemini 응답: {response.content[:100]}...", "SUCCESS")
        print_status(f"토큰 사용: {response.tokens_used}, 비용: ${response.cost:.6f}", "INFO")
        return True
        
    except Exception as e:
        print_status(f"Gemini 테스트 실패: {e}", "ERROR")
        return False


def test_perplexity_client():
    """Perplexity 클라이언트 테스트"""
    print_status("🔍 Perplexity 클라이언트 테스트 시작...")
    
    try:
        api_key = os.getenv('PERPLEXITY_API_KEY')
        if not api_key:
            print_status("PERPLEXITY_API_KEY가 설정되지 않았습니다", "ERROR")
            return False
        
        # 클라이언트 생성
        client = PerplexityClient(model_name="sonar-pro", api_key=api_key)
        
        # 테스트 요청
        request = LLMRequest(
            prompt="Hello! This is a connection test. Please respond with 'Connection successful'.",
            agent_type="test",
            max_tokens=50
        )
        
        response = client.generate_response(request)
        
        print_status(f"Perplexity 응답: {response.content[:100]}...", "SUCCESS")
        print_status(f"토큰 사용: {response.tokens_used}, 비용: ${response.cost:.6f}", "INFO")
        return True
        
    except Exception as e:
        print_status(f"Perplexity 테스트 실패: {e}", "ERROR")
        return False


def test_llm_factory():
    """LLM 팩토리 통합 테스트"""
    print_status("🏭 LLM 팩토리 통합 테스트 시작...")
    
    try:
        # 팩토리 인스턴스 생성
        factory = get_llm_factory()
        
        # 각 에이전트 타입별 클라이언트 생성 테스트
        test_agents = [
            "cio",
            "technical_analyst", 
            "sector_researcher",
            "valuation_analyst"
        ]
        
        success_count = 0
        
        for agent_type in test_agents:
            try:
                client = factory.create_client(agent_type)
                print_status(f"✓ {agent_type}: {client}", "SUCCESS")
                success_count += 1
            except Exception as e:
                print_status(f"✗ {agent_type}: {e}", "ERROR")
        
        print_status(f"팩토리 테스트 완료: {success_count}/{len(test_agents)} 성공", "INFO")
        return success_count == len(test_agents)
        
    except Exception as e:
        print_status(f"팩토리 테스트 실패: {e}", "ERROR")
        return False


def test_error_handling():
    """에러 핸들링 테스트"""
    print_status("⚠️ 에러 핸들링 테스트 시작...")
    
    try:
        # 잘못된 API 키로 테스트
        client = ClaudeClient(model_name="sonnet-3.5", api_key="invalid-key")
        
        request = LLMRequest(
            prompt="테스트",
            agent_type="test",
            max_tokens=10
        )
        
        try:
            response = client.generate_response(request)
            print_status("에러가 발생해야 하는데 성공했습니다 - 테스트 실패", "ERROR")
            return False
        except Exception as e:
            # 어떤 종류의 에러든 발생하면 성공
            print_status(f"예상된 에러 발생: {e}", "SUCCESS")
            return True
            
    except Exception as e:
        print_status(f"에러 핸들링 테스트 실패: {e}", "ERROR")
        return False


def main():
    """메인 테스트 실행"""
    print_status("🚀 LLM 클라이언트 통합 테스트 시작", "INFO")
    print("=" * 60)
    
    test_results = {}
    
    # 개별 클라이언트 테스트
    test_results["claude"] = test_claude_client()
    print("-" * 60)
    
    test_results["gpt"] = test_gpt_client()
    print("-" * 60)
    
    test_results["gemini"] = test_gemini_client()
    print("-" * 60)
    
    test_results["perplexity"] = test_perplexity_client()
    print("-" * 60)
    
    # 통합 테스트
    test_results["factory"] = test_llm_factory()
    print("-" * 60)
    
    test_results["error_handling"] = test_error_handling()
    print("-" * 60)
    
    # 결과 요약
    print_status("📊 테스트 결과 요약", "INFO")
    print("=" * 60)
    
    success_count = 0
    total_tests = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅" if result else "❌"
        color = "SUCCESS" if result else "ERROR"
        print_status(f"{status} {test_name}: {'통과' if result else '실패'}", color)
        if result:
            success_count += 1
    
    print("-" * 60)
    
    if success_count == total_tests:
        print_status(f"🎉 모든 테스트 통과! ({success_count}/{total_tests})", "SUCCESS")
        print_status("Phase 1.1 하이브리드 LLM 인프라 구축 완료!", "SUCCESS")
    else:
        print_status(f"⚠️ 일부 테스트 실패 ({success_count}/{total_tests})", "WARNING")
        print_status("실패한 API 키를 확인하고 다시 시도해주세요.", "WARNING")
    
    return success_count == total_tests


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)