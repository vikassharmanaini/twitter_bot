# Changelog

## Local admin panel — 2026-04-26

- FastAPI app (`src/admin/`, `run_admin.py`): REST for config (masked GET, atomic save), runtime, targets, replies/stats/db summary, maintenance jobs; WebSocket `/ws/events` for logs and status; optional `ADMIN_TOKEN`; static SPA from `admin-ui/dist` when built.
- React + Vite + TypeScript + Tailwind SPA in `admin-ui/` (Dashboard, Configuration, Activity, Targets, Tools, Settings).
- `BotRuntimeService` background thread with cooperative stop; logging bridge via `BroadcastLogHandler`.
- `KnowledgeStore.table_row_counts()` for admin DB summary.
- Tests: `tests/test_admin_api.py`, `tests/conftest.py` (singleton reset); documentation: `docs/ADMIN_PANEL.md`, README admin section.

## Initial implementation — 2026-04-26

- Phase 1: `config_loader`, `logger`, `twitter_client`, `target_manager`, tests, and project scaffold.
- Phase 2: OpenRouter `llm_client`, `tweet_analyser`, `web_searcher`, `comment_generator`, `comment_selector`, externalized prompts under `prompts/`.
- Phase 3: SQLite `knowledge_store`, `safety_filter`, `scheduler`, `main_loop`, integration dry-run test.
- Phase 4: `knowledge_updater`, `performance_analyser`, `target_expander`.
- Phase 5: `bot.py` CLI (`start`, `stop`, `resume`, `status`, `dry-run`, targets, stats, review, report, maintenance commands), `report_generator`.
- Documentation: `README.md`; configuration template `config.example.yaml`.

All modules include unit tests with external services mocked; run `pytest` for coverage.
