# Twitter Dev-Bot

This project is an autonomous engagement assistant for X (Twitter): it monitors curated tech and science accounts, reads new posts, optionally pulls web context, and drafts short replies that match a consistent developer persona. It is built for careful, human-paced use with safety checks, daily caps, and a mandatory dry-run mode for testing.

The bot is modular: configuration, logging, the X API client, LLM calls via OpenRouter, search, storage, scheduling, and the main loop are separate Python modules so you can test and swap pieces without rewriting the whole stack.

## Prerequisites

- Python **3.11+** (tested on 3.13)
- An [X Developer Portal](https://developer.twitter.com/) project with **OAuth 1.0a user** credentials (for posting replies) and a **Bearer token** (for reads such as timelines and user lookup)
- An [OpenRouter](https://openrouter.ai/) API key
- Optional: [Serper](https://serper.dev/) or [Brave Search API](https://brave.com/search/api/) keys if you switch `search.provider` from `duckduckgo`

## Setup

1. Clone or copy this repository.
2. Create a virtual environment and install dependencies:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. Copy `config.example.yaml` to `config.yaml` and fill in real secrets. Never commit `config.yaml`.
4. Edit `data/targets.yaml` with the handles you want to watch (see the example format).
5. Verify configuration loads:

   ```bash
   python bot.py bootstrap --config config.yaml
   ```

## How to run

- **Start the scheduler loop** (runs cycles with jitter until paused or interrupted):

  ```bash
  python bot.py start --config config.yaml
  ```

- **Dry-run one cycle** (no post; logs what would happen):

  ```bash
  python bot.py dry-run --config config.yaml
  ```

  Set `bot.dry_run: true` in `config.yaml` for extra safety during development.

- **Pause / resume** (uses `data/bot_state.json`):

  ```bash
  python bot.py stop --config config.yaml
  python bot.py resume --config config.yaml
  ```

- **Status**:

  ```bash
  python bot.py status --config config.yaml
  ```

- **Add or disable a target**:

  ```bash
  python bot.py add-target SomeHandle --category "AI" --config config.yaml
  python bot.py remove-target SomeHandle --config config.yaml
  ```

- **Stats, review, report**:

  ```bash
  python bot.py stats --config config.yaml
  python bot.py review --config config.yaml
  python bot.py report --out report.html --config config.yaml
  ```

- **Maintenance jobs**:

  ```bash
  python bot.py knowledge-update --config config.yaml
  python bot.py performance --config config.yaml
  python bot.py suggest-targets --config config.yaml
  ```

## Tests

```bash
rm -f .coverage
pytest
```

External APIs are mocked; a stale `.coverage` file can break `pytest-cov` on some systems—delete it if you see SQLite errors from coverage.

## Troubleshooting

1. **`config validation failed` / missing keys** — Compare your file to `config.example.yaml`. The loader rejects placeholder values such as `REPLACE_ME`.
2. **`403` or `401` from X** — Confirm Bearer and OAuth 1.0a keys match the same app and that your project has access to the endpoints you need (timeline read and tweet write).
3. **`429` rate limit** — The client retries with backoff; reduce `accounts_per_cycle` or increase `schedule_interval_minutes`.
4. **OpenRouter errors** — Check `openrouter.api_key` and model IDs; a fallback model is tried automatically.
5. **Search errors** — DuckDuckGo results can fail from some networks; try `serper` or `brave` with API keys, or rely on LLM-only replies when search returns no results.

## Compliance

Automating activity on X may violate the platform rules or applicable law. Run this software only with accounts and settings you are allowed to use, respect rate limits, and prefer dry-run until you are confident in behaviour and safety settings.
