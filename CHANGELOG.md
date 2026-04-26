# Changelog

## Initial implementation — 2026-04-26

- Phase 1: `config_loader`, `logger`, `twitter_client`, `target_manager`, tests, and project scaffold.
- Phase 2: OpenRouter `llm_client`, `tweet_analyser`, `web_searcher`, `comment_generator`, `comment_selector`, externalized prompts under `prompts/`.
- Phase 3: SQLite `knowledge_store`, `safety_filter`, `scheduler`, `main_loop`, integration dry-run test.
- Phase 4: `knowledge_updater`, `performance_analyser`, `target_expander`.
- Phase 5: `bot.py` CLI (`start`, `stop`, `resume`, `status`, `dry-run`, targets, stats, review, report, maintenance commands), `report_generator`.
- Documentation: `README.md`; configuration template `config.example.yaml`.

All modules include unit tests with external services mocked; run `pytest` for coverage.
