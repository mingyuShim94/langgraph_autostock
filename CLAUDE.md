# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **LangGraph-based autonomous trading system** that learns from its trading decisions and continuously improves. The system integrates with Korean Investment & Securities (KIS) API for real-time portfolio management, market analysis, and automated trading execution. The architecture features dual graph approach:

- **Trading Graph**: 6-node operational workflow for real-time trading execution
- **Reflection Graph**: 4-node learning system for continuous strategy improvement
- **Central Database**: SQLite-based memory system storing all decisions and outcomes

### Current Implementation Status
- **Phase 2 Complete**: Trading Graph fully implemented with 6 operational nodes
- **Phase 3 Planned**: Multi-agent specialist team with hybrid LLM strategy (see `docs/system_prd_0919.md`)

## Commands and Development

### Environment Setup
```bash
# Install dependencies using uv (preferred)
uv sync

# Alternative: pip install
pip install -r requirements.txt

# Set up KIS API configuration (create config directory)
mkdir -p ~/KIS/config
# Configure ~/KIS/config/kis_devlp.yaml with your API keys
```

### Running the System
```bash
# Run main trading workflow (default: paper trading + mock mode)
python src/trading_graph/main.py

# Run with different configurations
python src/trading_graph/main.py --env paper --live  # Paper trading with real API
python src/trading_graph/main.py --env prod --live   # Production trading
python src/trading_graph/main.py --test              # Test mode with validation
python src/trading_graph/main.py --viz               # Display workflow visualization only

# Test KIS API connection
python test_kis_auth.py
python test_kis_auth_simple.py
```

### Testing
```bash
# Run all tests
pytest tests/

# Run specific test categories
python tests/test_kis_client.py
python tests/test_database.py

# Run individual test files with debug output
python test_kis_debug.py
```

### Development Commands
```bash
# Test individual components
python -c "from src.kis_client.client import get_kis_client; print('KIS Client OK')"
python -c "from src.database.schema import db_manager; print('Database OK')"

# Check system status
python src/trading_graph/main.py --test  # Comprehensive system validation
```

## Architecture and Core Components

### Trading Graph Workflow (Phase 2 - Current)
The system operates as a **sequential LangGraph workflow** with conditional branching:

1. **`fetch_portfolio_status`**: KIS API integration for real-time account data
2. **`analyze_market_conditions`**: Market analysis and opportunity/risk detection  
3. **`generate_trading_plan`**: AI-powered decision engine with structured planning
4. **`validate_trading_plan`**: Risk management and validation (conditional routing)
5. **`execute_trading_plan`**: Order execution via KIS API (if validation passes)
6. **`record_and_report`**: Database storage and comprehensive reporting

### State Management (`src/trading_graph/state.py`)
- **`TradingState`**: Central TypedDict managing workflow state
- **Structured Data Classes**: `PortfolioStatus`, `MarketAnalysis`, `TradingPlan`, `RiskValidation`, `ExecutionResult`
- **State Update Helpers**: 11 helper functions for type-safe state updates

### Database Layer (`src/database/schema.py`)
- **`DatabaseManager`**: Central CRUD operations for trade records
- **`TradeRecord`**: Structured trade data with decision justification and market context
- **Performance Tracking**: Automatic P&L calculation and trade statistics

### KIS API Integration (`src/kis_client/client.py`)
- **`KISClient`**: Main API client with authentication management
- **Environment Support**: Paper trading vs production with automatic API endpoint selection
- **Mock Mode**: Development/testing mode with simulated data
- **Error Handling**: Robust fallback mechanisms and environment-specific error handling

## Planned Evolution (Phase 3)

### Multi-Agent Specialist Team Architecture
Based on `docs/system_prd_0919.md`, the system will evolve to:

1. **Specialist Agents with Hybrid LLM Strategy**:
   - **Portfolio Rebalancer** (GPT-5 nano): Portfolio diagnostics
   - **Sector Research Agent** (Perplexity sonar-pro): Real-time market research  
   - **Fundamental Analysts** (Gemini 2.5 Flash): Value, flow, and risk analysis
   - **Technical Analyst** (GPT-5): Chart-based timing analysis
   - **CIO Agent** (Claude Opus 4.1): Final decision synthesis

2. **Self-Modification Capabilities**:
   - Performance attribution to specific agents
   - Dynamic LLM model selection based on performance
   - Automatic prompt optimization and model upgrades

## Configuration and Environment

### Required Environment Variables
```bash
# Core APIs
OPENAI_API_KEY=your_openai_key
PERPLEXITY_API_KEY=your_perplexity_key

# KIS Trading API (Paper Trading)
KIS_PAPER_APP_KEY=your_paper_app_key
KIS_PAPER_APP_SECRET=your_paper_secret
KIS_PAPER_ACCOUNT_NUMBER=your_paper_account

# Production KIS API (Optional)
KIS_APP_KEY=your_production_key
KIS_APP_SECRET=your_production_secret
KIS_ACCOUNT_NUMBER=your_production_account
```

### Configuration Files
- **`config/settings.py`**: Centralized configuration management
- **`~/KIS/config/kis_devlp.yaml`**: KIS API credentials (Git-ignored)
- **`prompts/core_decision_prompt.md`**: AI decision-making instructions

## Development Patterns

### Adding New Trading Nodes
1. **Function Signature**: `def node_name(state: TradingState) -> TradingState`
2. **State Updates**: Use helper functions from `src/trading_graph/state.py`
3. **Error Handling**: Catch exceptions and update state with error info using `add_error()`
4. **Integration**: Add to workflow in `src/trading_graph/workflow.py`

### KIS API Development
- **Environment Handling**: Always support both `paper` and `prod` environments
- **Mock Mode**: Implement mock responses for development/testing
- **Error Recovery**: Use fallback mechanisms for API failures
- **Authentication**: Leverage automatic token management in `KISClient`

### Database Operations
- **Trade Recording**: Use `TradeRecord` dataclass for structured data
- **Performance Tracking**: Automatic P&L updates via `update_pnl()`
- **Analytics**: Leverage `get_trade_statistics()` for performance analysis

## Testing Strategy

### Test Categories
- **Unit Tests**: Individual component testing (`tests/test_*.py`)
- **Integration Tests**: Full workflow testing via `--test` mode
- **API Tests**: KIS client functionality (`test_kis_*.py` files)
- **Mock Tests**: Virtual trading simulation with `mock_mode=True`

### Safety and Risk Management
- **Paper Trading Default**: All trading starts in simulation mode
- **Explicit Production**: Must set `--env prod --live` for real trading
- **Risk Validation**: Built-in position sizing and loss limits
- **Conditional Execution**: Orders only execute after passing risk checks

## Key Implementation Files

### Core System
- **`src/trading_graph/main.py`**: Primary execution entry point with CLI interface
- **`src/trading_graph/workflow.py`**: LangGraph workflow definition and routing logic
- **`src/trading_graph/nodes.py`**: All 6 trading workflow node implementations
- **`src/trading_graph/state.py`**: State management and data structures

### Infrastructure  
- **`src/kis_client/client.py`**: KIS API client with authentication and error handling
- **`src/database/schema.py`**: Database schema and CRUD operations
- **`config/settings.py`**: Environment configuration and API settings

### Development Roadmap
- **`docs/development_roadmap.md`**: Current progress and implementation details
- **`docs/system_prd_0919.md`**: Next-generation multi-agent architecture plan