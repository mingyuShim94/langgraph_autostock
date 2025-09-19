# Repository Guidelines

## Project Structure & Module Organization
`src/` contains the observer workflow: `graph.py` wires nodes, `state.py` defines shared dataclasses, and API clients such as `kis_client.py` and `news_client.py` integrate external services. Runtime configuration lives in `config/settings.py`, while prompts belong under `prompts/` and architecture guidance sits in `docs/` (start with `all_architecture.md`). Tests mirror runtime modules in `tests/`, and keep transient output in `logs/` (ignore in Git).

## Build, Test, and Development Commands
Create a local environment with `python -m venv venv && source venv/bin/activate` (Windows: `venv\\Scripts\\activate`). Install dependencies via `pip install -r requirements.txt` after any dependency change. Run the full suite using `python -m pytest`; target the workflow with `pytest tests/test_langgraph_integration.py -vv`, or isolate KIS client behaviour with `pytest tests/test_kis_client.py -vv`. Set `PYTHONPATH=.` when shells require explicit module resolution.

## Coding Style & Naming Conventions
Follow PEP 8 with four-space indentation and explicit type hints that match the patterns in `state.py`. Modules and functions stay in `snake_case`, classes use `PascalCase`, and constants remain `UPPER_SNAKE_CASE`. Add concise docstrings for non-trivial nodes or API clients, and prefer the shared logger from `logging_config.py` instead of ad-hoc print statements.

## Testing Guidelines
Tests use `pytest` with offline mocks by default. Only run live KIS calls when `.env` provides paper-trading credentials and `KIS_ENVIRONMENT=paper`. Create reusable payloads under `tests/fixtures/` and assert on key fields (e.g., portfolio balances, news tickers). Name new tests `test_<feature>.py` to mirror the module exercised, and keep integration checks idempotent.

## Commit & Pull Request Guidelines
Write compact, action-first commit messages similar to `lv1 기능 보완 - add retry for KIS feed`. Pull requests should summarise behavioural changes, list touched modules, link issues or docs, and include the exact commands run (paste `python -m pytest` output when relevant). Attach terminal snippets or screenshots whenever the user-facing output shifts.

## Security & Configuration Tips
Never commit `.env`, API keys, or the `logs/` directory. Document new secret requirements in `docs/api_setup_guide.md` and verify them through `Settings.validate_required_settings()`. Stick to paper-trading credentials for new flows and flag any production-only steps so reviewers can reproduce safely.
