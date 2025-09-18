# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **LangGraph-based autonomous trading system implementation** repository that demonstrates progressive AI agent development through 5 complexity levels. Currently implements **LV1 Observer** pattern with Korean Investment & Securities (KIS) API integration for real-time portfolio monitoring and news analysis.

## Commands and Development

### Environment Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables (create .env file)
cp .env.example .env  # Then edit with your API keys
```

### Running the System
```bash
# Run LV1 Observer (main entry point)
python src/graph.py

# Run individual tests
pytest tests/test_langgraph_integration.py
pytest tests/test_kis_client.py
pytest tests/test_news_perplexity.py

# Debug KIS API connection
python tests/debug_kis_api.py
```

### Common Development Tasks
- **Adding new nodes**: Extend `src/graph.py` with new node functions
- **Modifying state**: Update schemas in `src/state.py`
- **API integrations**: Add clients in `src/` (following `kis_client.py` pattern)
- **Testing**: Create tests in `tests/` directory

## Architecture and Core Components

### Current Implementation (LV1 Observer)
The system operates as a **sequential LangGraph workflow**:

1. **Portfolio Fetching** (`fetch_portfolio_status`): KIS API integration for real-time account data
2. **News Collection** (`collect_news_data`): Perplexity AI for stock-specific news analysis
3. **Report Generation** (`generate_daily_report`): AI-powered portfolio briefing

### State Management (`src/state.py`)
- **ObserverState**: Central TypedDict managing workflow state
- **PortfolioStatus**: Real-time account and holdings data
- **NewsData**: AI-processed news with sentiment analysis
- **Pydantic Models**: Type-safe data validation throughout

### Key Classes and Files
- **`src/graph.py`**: Main LangGraph workflow definition and execution
- **`src/state.py`**: State schemas and update functions  
- **`src/kis_client.py`**: KIS API wrapper with authentication
- **`src/news_processor.py`**: Perplexity AI news analysis
- **`config/settings.py`**: Centralized configuration management

## API Integrations

### KIS (Korea Investment & Securities) API
- **Environment**: Supports both paper trading (`KIS_ENVIRONMENT=paper`) and production
- **Authentication**: Automatic token management via `src/kis_auth.py`
- **Configuration**: All credentials managed through `config/settings.py`

### News APIs
- **Perplexity AI**: Real-time news search and analysis
- **Naver News**: Korean market news (optional)
- **Features**: Sentiment analysis, relevance scoring, importance ranking

### LLM APIs
- **OpenAI**: GPT models for analysis and reporting
- **Google Gemini**: Alternative LLM provider (configured but not actively used)

## Development Progression (5-Level System)

### Implemented: LV1 Observer Pattern
- **Goal**: Portfolio monitoring and news briefing
- **Pattern**: Sequential node execution (`A → B → C`)
- **Features**: Data collection, analysis, reporting

### Planned: LV2+ Patterns
- **LV2 Rule-Follower**: Conditional trading based on technical indicators
- **LV3 Strategist**: Multi-agent analysis with consensus decisions
- **LV4 Fund Manager**: Portfolio optimization and risk management
- **LV5 Master**: Self-learning system with performance feedback loops

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

# Optional: Production KIS API
KIS_APP_KEY=your_production_key
KIS_APP_SECRET=your_production_secret
KIS_ACCOUNT_NUMBER=your_production_account
```

### Configuration Pattern
- All settings centralized in `config/settings.py`
- Environment-aware (development/production)
- Automatic validation of required credentials
- KIS-compatible configuration format

## Error Handling and Logging

### Exception Hierarchy
- **`src/exceptions.py`**: Custom exception classes
- **KISAPIError**: Specific to trading API failures
- **NewsAPIError**: News collection failures

### Logging Strategy
- **`src/logging_config.py`**: Centralized logging setup
- **File logging**: `logs/` directory for persistence
- **Console output**: Real-time execution feedback

## Testing Strategy

### Test Categories
- **Integration tests**: Full workflow testing (`test_langgraph_integration.py`)
- **API tests**: Individual service testing (`test_kis_client.py`, `test_news_perplexity.py`)
- **Auth tests**: Credential and token management
- **Mock tests**: Virtual trading simulation

### Running Tests
```bash
# All tests
pytest

# Specific test categories
pytest tests/test_kis_* -v
pytest tests/test_news_* -v
pytest tests/test_langgraph_* -v
```

## Key Development Patterns

### LangGraph Node Development
1. **Function signature**: `def node_name(state: ObserverState) -> ObserverState`
2. **State updates**: Use helper functions from `src/state.py`
3. **Error handling**: Catch exceptions and update state with error info
4. **Logging**: Print step-by-step progress for debugging

### Adding New APIs
1. **Client class**: Create in `src/` following `kis_client.py` pattern
2. **Configuration**: Add settings to `config/settings.py`
3. **State integration**: Update state schemas in `src/state.py`
4. **Error handling**: Add custom exceptions to `src/exceptions.py`

### Progressive Enhancement
- Start with stub implementations for new features
- Add real API integrations incrementally
- Maintain backward compatibility with existing nodes
- Follow the 5-level progression model for complexity

## Security and Credentials

### API Key Management
- **Never commit credentials** to repository
- **Use .env files** for local development
- **Environment variables** for production deployment
- **Validation checks** in settings for missing credentials

### Trading Safety
- **Paper trading default**: All trading starts in simulation mode
- **Explicit production mode**: Must set `KIS_ENVIRONMENT=prod`
- **Credential separation**: Different keys for paper vs production
- **Amount limits**: Built-in safeguards for order sizes