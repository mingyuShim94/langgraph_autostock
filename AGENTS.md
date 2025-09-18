# Repository Guidelines

## Project Structure & Module Organization
- `src/` holds the observer workflow: `graph.py` wires nodes, `state.py` shapes shared data, and API clients (e.g., `kis_client.py`, `news_client.py`) bridge external services.
- Configuration lives in `config/settings.py`; load secrets from `.env` before touching KIS, Perplexity, or Gemini integrations.
- Reference architecture notes in `docs/` (start with `all_architecture.md` and `api_setup_guide.md`); reusable prompt drafts live under `prompts/`.
- Tests mirror module names inside `tests/`; use `logs/` for runtime output but keep it out of Git.

## Build, Test, and Development Commands
- Create an environment with `python -m venv venv && source venv/bin/activate` (or `venv\Scripts\activate` on Windows).
- Install requirements via `pip install -r requirements.txt`; rerun after updating LangGraph or pandas versions.
- Run the suite with `python -m pytest`; focus on the workflow using `pytest tests/test_langgraph_integration.py -vv`.
- When tuning API layers, run `pytest tests/test_kis_client.py -vv` for quick coverage, and export `PYTHONPATH=.` if your shell needs it.

## Coding Style & Naming Conventions
- Follow PEP 8, four-space indentation, and keep type hints consistent with `state.py`.
- Functions and modules use `snake_case`, classes use `PascalCase`, constants stay `UPPER_SNAKE_CASE`.
- Describe non-trivial nodes or clients with short docstrings and prefer the shared logger from `logging_config.py` over ad-hoc prints.

## Testing Guidelines
- Default to offline tests with mocked HTTP responses; only call live KIS endpoints when credentials are present and the environment is set to paper trading.
- Integration tests require `.env` secrets: set `KIS_ENVIRONMENT=paper` before running `tests/test_langgraph_integration.py` or `tests/test_kis_real_connection.py`.
- Store reusable payloads under `tests/fixtures/` (create it if needed) and assert portfolio/news fields explicitly.

## Commit & Pull Request Guidelines
- Git history shows compact, action-oriented messages (`lv1 프로젝트 구현 완료 - 테스트 필요`); follow that tone, keep verbs imperative, and add a short English clause when changes affect shared workflows.
- PRs should outline behaviour changes, list touched modules, link related issues or docs, and state the exact test commands executed. Attach terminal snippets or screenshots when output changes.

## Security & Configuration Tips
- Keep `.env`, API keys, and `logs/` out of version control. Document new secrets in `docs/api_setup_guide.md` and verify them with `Settings.validate_required_settings()`.
- Use paper-trading credentials for new features and flag any production-only steps so reviewers can reproduce safely.
