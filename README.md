# Twitter Dev-Bot

An autonomous engagement assistant for **X (Twitter)**. It watches curated accounts, reads new posts, optionally gathers web context, and drafts short replies in a consistent developer voice. The design favors **human-paced** operation: safety filters, daily caps, scheduler jitter, and **dry-run** support before anything is posted.

The codebase is split into small modules—config, logging, X API client, OpenRouter LLM, search, SQLite knowledge store, scheduling, main loop—so you can test and replace pieces without rewriting the stack.

## Contents

- [Prerequisites](#prerequisites)
- [Quick start](#quick-start)
- [Project layout](#project-layout)
- [CLI (`bot.py`)](#cli-botpy)
- [Admin panel](#admin-panel)
- [Helper script (`dev.sh`)](#helper-script-devsh)
- [Tests](#tests)
- [Troubleshooting](#troubleshooting)
- [Compliance](#compliance)

## Prerequisites

- **Python 3.11+** (tested on 3.13)
- An [X Developer Portal](https://developer.twitter.com/) app with **OAuth 1.0a user** credentials (posting) and a **Bearer token** (reads such as timelines and user lookup)
- An [OpenRouter](https://openrouter.ai/) API key
- Optional: [Serper](https://serper.dev/) or [Brave Search API](https://brave.com/search/api/) if you set `search.provider` to something other than `duckduckgo`
- Optional (admin UI): **Node.js** 18+ for `admin-ui` (`npm install`, `npm run dev` / `npm run build`)

## Quick start

1. Clone the repository and enter the directory.

2. Create a virtual environment and install Python dependencies:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

   Or use the helper: `bash dev.sh setup`

3. Copy `config.example.yaml` to `config.yaml` and replace placeholders with real secrets. **Do not commit `config.yaml`.**

4. Edit `data/targets.yaml` with the handles you want to monitor (see the example format).

5. Confirm configuration loads:

   ```bash
   python bot.py bootstrap --config config.yaml
   ```

6. Prefer **dry-run** until behaviour and safety settings look right (`python bot.py dry-run --config config.yaml`, or `bot.dry_run: true` in `config.yaml`).

## Project layout

| Path | Role |
|------|------|
| `bot.py` | Command-line interface |
| `run_admin.py` | Local admin API + WebSocket (FastAPI / uvicorn) |
| `src/` | Application library (config, Twitter, LLM, loop, store, …) |
| `src/admin/` | Admin backend (REST, runtime service, config repo, log broadcast) |
| `admin-ui/` | React + TypeScript + Vite + Tailwind SPA |
| `data/` | Runtime data (e.g. `targets.yaml`, `bot_state.json`, SQLite) |
| `prompts/` | Externalized LLM prompts |
| `tests/` | `pytest` suite |
| `docs/ADMIN_PANEL.md` | Admin architecture, env vars, security, troubleshooting |

## CLI (`bot.py`)

All examples use `config.yaml`; pass a different file with `--config path/to.yaml`.

| Action | Command |
|--------|---------|
| Validate / warm up services | `python bot.py bootstrap --config config.yaml` |
| Run scheduler loop (until pause or interrupt) | `python bot.py start --config config.yaml` |
| Single cycle, no post | `python bot.py dry-run --config config.yaml` |
| Pause (writes `data/bot_state.json`) | `python bot.py stop --config config.yaml` |
| Resume | `python bot.py resume --config config.yaml` |
| Status | `python bot.py status --config config.yaml` |
| Add target | `python bot.py add-target SomeHandle --category "AI" --config config.yaml` |
| Disable target | `python bot.py remove-target SomeHandle --config config.yaml` |
| Stats | `python bot.py stats --config config.yaml` |
| Review | `python bot.py review --config config.yaml` |
| Clear reply history (SQLite) | `python bot.py clear-history --config config.yaml` |
| HTML report | `python bot.py report --out report.html --config config.yaml` |
| Knowledge update | `python bot.py knowledge-update --config config.yaml` |
| Performance analysis | `python bot.py performance --config config.yaml` |
| Suggest targets | `python bot.py suggest-targets --config config.yaml` |

Run `python bot.py --help` for the full command list and flags.

## Admin panel

The **local admin** stack gives you a browser UI and JSON API for runtime control (start/stop/pause/resume, dry-run), **masked** config editing, targets, maintenance jobs, and **live logs** over WebSocket. It binds to **`127.0.0.1:8080`** by default—not the public internet without extra hardening.

**API only:**

```bash
source .venv/bin/activate
python run_admin.py
```

Open `http://127.0.0.1:8080/docs` for OpenAPI.

**API + built SPA (single origin):**

```bash
cd admin-ui && npm ci && npm run build && cd ..
python run_admin.py
```

Then open `http://127.0.0.1:8080/`.

**Development** (Vite hot reload, proxy to the API):

```bash
# Terminal 1
python run_admin.py

# Terminal 2
cd admin-ui && npm install && npm run dev
```

Optional **`ADMIN_TOKEN`**: send `Authorization: Bearer <token>` on REST calls; for WebSocket use `?token=<token>` (or the same Bearer header if your client supports it). If the token is unset, anyone on the machine who can reach the bind address can use the panel—fine for solo local dev; set a token on shared machines.

Full detail: **[docs/ADMIN_PANEL.md](docs/ADMIN_PANEL.md)**.

## Helper script (`dev.sh`)

`dev.sh` wraps common tasks from the repo root (uses `.venv` when present). If `./dev.sh` is not executable on your filesystem, run `bash dev.sh …`.

```bash
bash dev.sh help          # list commands
bash dev.sh setup         # venv + pip install
bash dev.sh test          # pytest (drops stale .coverage first)
bash dev.sh test -- tests/test_admin_api.py -q
bash dev.sh admin         # same as python run_admin.py
bash dev.sh admin-build   # npm ci + build admin-ui
bash dev.sh admin-dev     # npm install + vite dev
CONFIG=config.yaml bash dev.sh dry-run
```

## Tests

```bash
rm -f .coverage
pytest
```

Or: `bash dev.sh test`

External services are mocked. If `pytest-cov` fails with odd SQLite errors, remove `.coverage` and run again.

## Troubleshooting

1. **`config validation failed` / missing keys** — Align with `config.example.yaml`. Placeholders like `REPLACE_ME` are rejected.
2. **`403` or `401` from X** — Bearer and OAuth 1.0a keys must belong to the same app; confirm endpoint access (read timelines, write tweets).
3. **`429` rate limits** — The client backs off; lower `accounts_per_cycle` or raise `schedule_interval_minutes`.
4. **OpenRouter errors** — Check `openrouter.api_key` and model IDs; a fallback model is attempted when configured.
5. **Search / DuckDuckGo** — Some networks block or throttle DDG; switch to `serper` or `brave` with keys, or rely on LLM-only replies when search is empty.
6. **Admin UI 404 in “prod” mode** — Run `npm run build` in `admin-ui` so `admin-ui/dist` exists before `run_admin.py`.
7. **401 on admin API** — Set the `Authorization` header to match `ADMIN_TOKEN`, or unset `ADMIN_TOKEN` for local-only use.

## Compliance

Automating activity on X may violate platform rules or applicable law. Use only accounts and settings you are permitted to use, respect rate limits, and stay in **dry-run** until you trust behaviour and safety settings.
