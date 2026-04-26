# 🤖 Twitter Dev-Bot — Complete PRD & Build Instructions

> **Project:** Autonomous Twitter engagement bot for a software developer / science & tech enthusiast  
> **Goal:** Grow audience by commenting on popular tech/science figures' posts in a human, witty, and knowledgeable way  
> **Stack decision:** Left to the agent — Python preferred, modular architecture required

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Architecture Overview](#2-architecture-overview)
3. [Phase & Module Breakdown](#3-phase--module-breakdown)
   - [Phase 1 — Foundation](#phase-1--foundation)
   - [Phase 2 — Intelligence Layer](#phase-2--intelligence-layer)
   - [Phase 3 — Engagement Engine](#phase-3--engagement-engine)
   - [Phase 4 — Growth & Self-Update](#phase-4--growth--self-update)
   - [Phase 5 — Dashboard & Controls](#phase-5--dashboard--controls)
4. [Module Specifications](#4-module-specifications)
5. [Data Models](#5-data-models)
6. [Configuration & Secrets](#6-configuration--secrets)
7. [Testing Rules](#7-testing-rules)
8. [Git Commit Rules](#8-git-commit-rules)
9. [Documentation Rules](#9-documentation-rules)
10. [Rate Limits & Safety](#10-rate-limits--safety)
11. [File & Folder Structure](#11-file--folder-structure)

---

## 1. Project Overview

### What This Bot Does

This bot acts as **you** — a software developer who loves science and technology — on Twitter/X. It:

- Watches a curated list of popular accounts in tech/science
- Reads their latest tweets
- Generates comments that sound genuinely human: witty, thoughtful, sometimes funny, always on-topic
- Posts those comments to grow your follower base organically
- Searches the web to stay current on topics before commenting
- Learns and updates its own knowledge base over time

### What This Bot Does NOT Do

- Spam or post gibberish
- Follow/unfollow bots
- Like-farm
- Post the same comment twice
- Comment faster than a human could
- Reveal it is a bot

### Core Persona

> "I'm a software developer who geeks out over science, tech, and the weird intersections between them. I love a good pun, I respect nuance, and I don't take myself too seriously."

This persona must be consistent across every comment the bot generates.

---

## 2. Architecture Overview

```
┌─────────────────────────────────────────────┐
│                  SCHEDULER                  │
│         (runs every N minutes)              │
└──────────────────┬──────────────────────────┘
                   │
         ┌─────────▼──────────┐
         │   TWEET FETCHER    │  ← Twitter/X API
         │  (target accounts) │
         └─────────┬──────────┘
                   │
         ┌─────────▼──────────┐
         │  CONTENT ANALYSER  │  ← OpenRouter LLM
         │  (understand tweet)│
         └─────────┬──────────┘
                   │
         ┌─────────▼──────────┐
         │   WEB SEARCHER     │  ← Search API
         │  (get context)     │
         └─────────┬──────────┘
                   │
         ┌─────────▼──────────┐
         │  COMMENT GENERATOR │  ← OpenRouter LLM
         │  (write reply)     │
         └─────────┬──────────┘
                   │
         ┌─────────▼──────────┐
         │  SAFETY FILTER     │
         │  (check before     │
         │   posting)         │
         └─────────┬──────────┘
                   │
         ┌─────────▼──────────┐
         │   TWITTER POSTER   │  ← Twitter/X API
         │  (reply to tweet)  │
         └─────────┬──────────┘
                   │
         ┌─────────▼──────────┐
         │   KNOWLEDGE STORE  │  ← Local DB / JSON
         │  (log + learn)     │
         └────────────────────┘
```

Every module is independently testable and swappable.

---

## 3. Phase & Module Breakdown

---

### Phase 1 — Foundation

**Goal:** Get the skeleton running. Config loads, Twitter auth works, basic logging works.

#### Module 1.1 — Project Setup & Config Loader

**What it does:**
- Reads a `config.yaml` (or `.env`) file where the user enters:
  - OpenRouter API key
  - Twitter/X API credentials (Bearer token, OAuth 1.0a keys)
  - Preferred LLM model names (primary + fallback)
  - Target account list
  - Posting frequency
  - Comment style toggles (humor level: low/medium/high)
- Validates that all required keys are present at startup
- Fails loudly and clearly if something is missing (tells the user exactly which key)

**Inputs:** `config.yaml` or `.env`  
**Outputs:** A validated, typed config object used by all other modules  
**Depends on:** Nothing (bootstraps everything else)

---

#### Module 1.2 — Logger

**What it does:**
- Structured logging (JSON preferred) with levels: DEBUG, INFO, WARN, ERROR
- Every action logged with timestamp, module name, tweet ID (when relevant)
- Logs to both console and rotating file (`logs/bot.log`)
- Sensitive values (API keys) must NEVER appear in logs

**Inputs:** Any module calling `log(level, message, metadata)`  
**Outputs:** Log files + console output  
**Depends on:** Config Loader

---

#### Module 1.3 — Twitter API Client

**What it does:**
- Wraps Twitter/X API v2 calls
- Handles authentication (OAuth 2.0 Bearer for reads, OAuth 1.0a for writes)
- Methods needed:
  - `get_recent_tweets(user_id, count)` — fetch N latest tweets from a user
  - `get_user_id(username)` — resolve @handle to numeric ID
  - `post_reply(tweet_id, text)` — reply to a tweet
  - `has_already_replied(tweet_id)` — check if bot already replied (check local log)
- Implements exponential backoff on rate limit errors (429)
- Throws typed exceptions so callers can handle cleanly

**Inputs:** Twitter API credentials from Config  
**Outputs:** Tweet objects, post confirmations  
**Depends on:** Config Loader, Logger

---

#### Module 1.4 — Target Account Manager

**What it does:**
- Maintains a YAML/JSON list of target accounts to watch
- Each entry has:
  - `username` — Twitter handle
  - `category` — e.g., "AI", "Physics", "Open Source"
  - `priority` — 1 (highest) to 5 (lowest); higher priority = checked more often
  - `enabled` — true/false toggle
- Provides `get_accounts_to_check()` — returns the list sorted by priority and last-checked time (don't re-check the same account too quickly)
- Caches resolved user IDs to avoid repeated API lookups

**Inputs:** `data/targets.yaml`  
**Outputs:** Ordered list of accounts to process  
**Depends on:** Config Loader, Twitter API Client

---

**✅ Phase 1 Completion Criteria:**
- Config loads and validates
- Logger writes to file and console
- Can fetch last 5 tweets from a given Twitter handle
- Can post a hardcoded test reply (to a test account) without errors
- All Phase 1 modules have passing unit tests

---

### Phase 2 — Intelligence Layer

**Goal:** The bot can understand a tweet, search for context, and generate a smart comment.

#### Module 2.1 — OpenRouter LLM Client

**What it does:**
- Wraps the OpenRouter API (`https://openrouter.ai/api/v1/chat/completions`)
- Accepts: model name, system prompt, user prompt, max tokens, temperature
- Returns: plain text response
- Supports model fallback: if primary model fails or returns an error, try the fallback model
- Tracks token usage per call for logging purposes
- Enforces a max token budget per run to avoid unexpected costs

**Inputs:** Prompt strings, model config from Config Loader  
**Outputs:** LLM text responses  
**Depends on:** Config Loader, Logger

---

#### Module 2.2 — Tweet Analyser

**What it does:**
- Takes a raw tweet text as input
- Calls LLM to extract:
  - `topic` — one-line summary of what the tweet is about
  - `sentiment` — positive / negative / neutral / excited / controversial
  - `tweet_type` — announcement / opinion / question / joke / link-share / thread
  - `technical_level` — beginner / intermediate / expert
  - `key_entities` — list of people, tools, companies, concepts mentioned
  - `requires_web_search` — true/false (does a good reply need current info?)
  - `search_query` — if web search needed, what query to run
- Returns a structured `TweetAnalysis` object (not raw text)

**Inputs:** Tweet text string  
**Outputs:** `TweetAnalysis` object  
**Depends on:** OpenRouter LLM Client

---

#### Module 2.3 — Web Searcher

**What it does:**
- Accepts a search query string
- Uses a free/cheap search API (DuckDuckGo unofficial API, Serper.dev, or Brave Search API — user picks in config)
- Returns top 3–5 results as: title, URL, snippet
- Passes results to LLM to extract a 2–3 sentence "context summary" relevant to the tweet
- Caches results for the same query for 30 minutes to avoid repeat searches
- Gracefully degrades: if search fails, bot continues without search context

**Inputs:** Search query string  
**Outputs:** `SearchContext` object with summary + source URLs  
**Depends on:** OpenRouter LLM Client, Config Loader, Logger

---

#### Module 2.4 — Comment Generator

**What it does:**
- The creative heart of the bot
- Takes: `TweetAnalysis`, `SearchContext` (optional), persona config
- Builds a detailed system prompt that defines the persona:
  - Developer who loves science/tech
  - Writes like a human — casual, smart, occasionally self-deprecating
  - Uses humor when appropriate (based on `humor_level` config)
  - Never uses corporate buzzwords or sounds like marketing
  - Never uses emojis unless the original tweet used them
  - Never says "Great tweet!" or sycophantic openers
  - Keeps replies under 260 characters (Twitter limit is 280, leave buffer)
- Calls LLM with this system prompt + tweet context
- Generates **3 candidate comments** (temperature: 0.8–0.9 for creativity)
- Returns all 3 so the Safety Filter can pick the best

**Comment style variants the LLM should choose from based on tweet type:**
- **Witty observation** — points out something clever or ironic
- **Genuine question** — asks a smart follow-up that invites engagement
- **Relate-and-add** — "I ran into this while building X, and also found that Y…"
- **Nerdy joke** — programming/science pun if the tone allows
- **Respectful pushback** — politely challenges an assumption with reasoning

**Inputs:** `TweetAnalysis`, optional `SearchContext`, persona config  
**Outputs:** List of 3 candidate comment strings  
**Depends on:** OpenRouter LLM Client

---

#### Module 2.5 — Comment Selector

**What it does:**
- Receives 3 candidate comments from the Comment Generator
- Runs each through a scoring LLM call that rates:
  - `human_likeness` (1–10) — does it sound like a real person?
  - `relevance` (1–10) — does it actually relate to the tweet?
  - `engagement_potential` (1–10) — would it make someone reply or follow?
  - `risk_score` (1–10, lower is safer) — could it be misinterpreted or offensive?
- Picks the highest total score, with `risk_score` acting as a veto (if > 7, discard)
- Returns the single best comment

**Inputs:** List of 3 comment strings, original tweet for context  
**Outputs:** Single best comment string + score breakdown  
**Depends on:** OpenRouter LLM Client

---

**✅ Phase 2 Completion Criteria:**
- Given a tweet text, the system produces a coherent, on-topic comment
- Web search integration works and context is incorporated when relevant
- 3 candidates are generated and scored; best one is selected
- Comments do not exceed 260 characters
- All Phase 2 modules have passing unit tests with mocked LLM/search calls

---

### Phase 3 — Engagement Engine

**Goal:** The bot runs on a schedule, processes real tweets, posts real replies, and avoids doing anything stupid.

#### Module 3.1 — Safety Filter

**What it does:**
- Last line of defense before posting — runs every time, no exceptions
- Checks:
  - **Length check:** comment must be ≤ 280 characters
  - **Duplicate check:** has this tweet already been replied to? (check local DB)
  - **Cooldown check:** has the bot posted in the last N minutes? (prevent burst posting)
  - **Daily limit check:** has the bot hit its daily reply cap? (configurable, default: 20)
  - **Keyword blacklist:** comment must not contain any words from a configurable blacklist (politics, slurs, etc.)
  - **Bot-reveal check:** LLM call that asks "does this comment reveal the author is a bot?" — if yes, regenerate
  - **Repetition check:** is this comment too similar (>70% overlap) to any recent comment in the log?
- Returns: `APPROVED`, `REJECTED_WITH_REASON`, or `REGENERATE`

**Inputs:** Candidate comment, tweet ID, posting history  
**Outputs:** Safety decision + reason  
**Depends on:** Knowledge Store, Config Loader

---

#### Module 3.2 — Scheduler

**What it does:**
- Controls when the bot runs its full cycle
- Configurable: run every X minutes (default: 45 minutes)
- Adds human-like randomness: actual interval = X ± 20% random jitter
- Tracks: last run time, total replies today, errors in last run
- Can be paused/resumed via a simple `bot_state.json` flag file
- On startup, logs a summary of what it plans to do

**Inputs:** Config (schedule settings), `bot_state.json`  
**Outputs:** Triggers the main processing loop  
**Depends on:** All other modules (orchestrates them)

---

#### Module 3.3 — Main Processing Loop

**What it does:**
This is the orchestrator — it chains all modules together for each run cycle:

```
1. Load accounts → pick N accounts to process this cycle (based on priority)
2. For each account:
   a. Fetch latest tweets (last 10)
   b. Filter: skip tweets older than 24h, skip already-replied, skip retweets
   c. Pick the tweet with highest engagement (likes + retweets)
   d. Analyse the tweet (Module 2.2)
   e. Search web if needed (Module 2.3)
   f. Generate 3 comment candidates (Module 2.4)
   g. Select best comment (Module 2.5)
   h. Run safety filter (Module 3.1)
   i. If APPROVED: post reply, log to DB
   j. If REJECTED: log reason, skip
   k. If REGENERATE: try once more, then skip if still fails
3. Update knowledge store with topics seen today
4. Log summary of the cycle
```

**Inputs:** All module outputs  
**Outputs:** Posted replies + cycle summary log  
**Depends on:** All Phase 1, 2, and 3 modules

---

#### Module 3.4 — Knowledge Store

**What it does:**
- Local SQLite database (no external DB needed)
- Tables:
  - `replied_tweets` — tweet_id, account, reply_text, posted_at, score_breakdown
  - `seen_topics` — topic, first_seen, last_seen, count (how often seen)
  - `daily_stats` — date, replies_posted, accounts_checked, tokens_used, errors
  - `knowledge_snippets` — topic, summary, source_url, learned_at (from web searches)
- Provides query methods used by Safety Filter and the main loop
- Exports a weekly summary JSON for review

**Inputs:** Data from all modules throughout each run cycle  
**Outputs:** Persisted records, query results  
**Depends on:** Nothing (pure storage layer)

---

**✅ Phase 3 Completion Criteria:**
- Bot runs end-to-end cycle without crashing
- Posts at least one real reply to a real tweet (on a test/alt account first)
- Safety filter catches: duplicates, long comments, blacklisted words
- Daily limit is respected
- Scheduler runs with jitter and doesn't double-fire
- All Phase 3 modules have passing integration tests

---

### Phase 4 — Growth & Self-Update

**Goal:** The bot stays current, learns from what works, and keeps improving its comments over time.

#### Module 4.1 — Knowledge Updater

**What it does:**
- Runs once per day (separate from the main cycle)
- Reads `seen_topics` from Knowledge Store — finds topics seen 3+ times
- For each hot topic, runs a web search for "latest news on [topic]"
- Summarises the results and saves them as `knowledge_snippets`
- The Comment Generator will inject relevant snippets into prompts automatically
- Also fetches and summarises the bio/recent activity of top target accounts (so comments feel informed)

**Inputs:** Knowledge Store data, Web Searcher  
**Outputs:** Updated `knowledge_snippets` in Knowledge Store  
**Depends on:** Knowledge Store, Web Searcher, OpenRouter LLM Client

---

#### Module 4.2 — Performance Analyser

**What it does:**
- Runs once per week
- Checks which posted replies have gotten engagement (likes, replies) via Twitter API
- Tags high-performing replies in the DB
- Runs an LLM analysis: "What patterns do the best-performing replies share?"
- Writes findings to `data/performance_insights.md`
- Optionally adjusts persona config (humor level, reply style) based on findings

**Inputs:** `replied_tweets` from Knowledge Store, Twitter API  
**Outputs:** `performance_insights.md`, optional config adjustments  
**Depends on:** Knowledge Store, Twitter API Client, OpenRouter LLM Client

---

#### Module 4.3 — Target Account Expander

**What it does:**
- Analyses who your existing targets are followed by and follow
- Suggests 5 new accounts to add each week based on:
  - High follower count in tech/science
  - High engagement rate (not just follower count)
  - Content overlapping with your persona's interests
- Writes suggestions to `data/suggested_targets.md` for human review
- Does NOT auto-add accounts — human approval required

**Inputs:** Twitter API, current `targets.yaml`  
**Outputs:** `data/suggested_targets.md`  
**Depends on:** Twitter API Client, Config Loader

---

**✅ Phase 4 Completion Criteria:**
- Knowledge Updater runs without errors and populates `knowledge_snippets`
- Comment Generator uses knowledge snippets when relevant topic is detected
- Performance Analyser produces a readable `performance_insights.md`
- Target Account Expander produces a `suggested_targets.md` with at least 3 suggestions

---

### Phase 5 — Dashboard & Controls

**Goal:** A simple way to monitor, control, and review the bot without touching code.

#### Module 5.1 — CLI Control Interface

**What it does:**
- A command-line tool (`bot.py` or `manage.py`) with subcommands:
  - `start` — start the scheduler
  - `stop` — gracefully stop (sets pause flag)
  - `status` — show: is it running? last run time? replies today? errors?
  - `dry-run` — run one full cycle but don't post anything (just log what it would do)
  - `add-target @handle` — add an account to targets list
  - `remove-target @handle` — disable an account
  - `stats` — show weekly reply stats
  - `review` — show last 10 posted comments for manual review
  - `clear-history` — wipe the `replied_tweets` log (use carefully)

**Inputs:** CLI arguments  
**Outputs:** Console output, state changes  
**Depends on:** All modules

---

#### Module 5.2 — Simple HTML Report (Optional)

**What it does:**
- Generates a static `report.html` on demand
- Shows: replies posted this week, top accounts targeted, top topics covered, errors
- No server needed — just opens in a browser
- Generated by `bot.py report` command

**Inputs:** Knowledge Store data  
**Outputs:** `report.html`  
**Depends on:** Knowledge Store

---

**✅ Phase 5 Completion Criteria:**
- `dry-run` works and shows expected output without posting
- `status` shows accurate info
- `add-target` and `remove-target` persist correctly
- Report generates without errors

---

## 4. Module Specifications

### Prompt Engineering Standards

All LLM prompts must follow this structure:

```
[SYSTEM PROMPT]
- Who you are (the persona)
- What your task is for this call
- Hard rules (never do X, always do Y)
- Output format (plain text / JSON / etc.)

[USER PROMPT]
- The actual content (tweet text, context, etc.)
- Any dynamic data
```

Every prompt must be stored in `prompts/` as its own `.txt` or `.yaml` file — not hardcoded in source files. This makes them easy to tweak without changing code.

### Token Budget Per Action

| Action | Max Tokens |
|---|---|
| Tweet analysis | 300 |
| Web search summary | 400 |
| Comment generation (3 candidates) | 600 |
| Comment scoring | 200 |
| Bot-reveal safety check | 150 |
| Knowledge update summary | 500 |
| Performance analysis | 800 |

---

## 5. Data Models

### `Tweet`
```
tweet_id: string
author_username: string
author_id: string
text: string
created_at: datetime
like_count: int
retweet_count: int
reply_count: int
is_retweet: bool
is_reply: bool
```

### `TweetAnalysis`
```
tweet_id: string
topic: string
sentiment: enum(positive, negative, neutral, excited, controversial)
tweet_type: enum(announcement, opinion, question, joke, link_share, thread)
technical_level: enum(beginner, intermediate, expert)
key_entities: list[string]
requires_web_search: bool
search_query: string | null
```

### `SearchContext`
```
query: string
results: list[{title, url, snippet}]
summary: string
searched_at: datetime
```

### `CommentCandidate`
```
text: string
style: string (witty / question / relate / joke / pushback)
human_likeness_score: int (1-10)
relevance_score: int (1-10)
engagement_score: int (1-10)
risk_score: int (1-10)
total_score: float
```

### `PostedReply`
```
tweet_id: string
target_account: string
reply_text: string
posted_at: datetime
style_used: string
score_breakdown: dict
engagement_received: dict | null (filled later by Performance Analyser)
```

---

## 6. Configuration & Secrets

### `config.yaml` Structure

```yaml
# OpenRouter
openrouter:
  api_key: "sk-or-..."          # User enters this
  primary_model: "mistralai/mistral-7b-instruct:free"
  fallback_model: "google/gemma-2-9b-it:free"
  max_tokens_per_run: 5000      # Safety budget

# Twitter/X API
twitter:
  bearer_token: "..."
  api_key: "..."
  api_secret: "..."
  access_token: "..."
  access_token_secret: "..."

# Bot Behaviour
bot:
  schedule_interval_minutes: 45
  schedule_jitter_percent: 20
  max_replies_per_day: 20
  accounts_per_cycle: 3        # How many target accounts to check per run
  min_tweet_age_minutes: 5     # Don't reply to tweets newer than 5 min (Twitter quirk)
  max_tweet_age_hours: 24      # Don't reply to old tweets
  humor_level: "medium"        # low / medium / high
  dry_run: false               # Set true to test without posting

# Search
search:
  provider: "duckduckgo"       # duckduckgo / serper / brave
  serper_api_key: ""           # Only if using Serper
  brave_api_key: ""            # Only if using Brave
  cache_ttl_minutes: 30

# Safety
safety:
  daily_reply_cap: 20
  min_minutes_between_posts: 20
  blacklisted_words: []        # User can add words here
  max_similarity_to_recent: 0.70

# Logging
logging:
  level: "INFO"
  log_file: "logs/bot.log"
  max_log_size_mb: 10
  backup_count: 5
```

### Secret Handling Rules

- API keys live ONLY in `config.yaml` or `.env`
- `config.yaml` is listed in `.gitignore` — it is NEVER committed
- A `config.example.yaml` with placeholder values IS committed
- The Config Loader raises a hard error if a key is missing and there's no default

---

## 7. Testing Rules

The code agent must follow these rules for all tests:

### Rule T1 — Test File Location
Every module `src/module_name.py` must have a corresponding `tests/test_module_name.py`.

### Rule T2 — Test Before Moving On
No phase is considered complete until all its module tests pass with `pytest` and show 0 failures.

### Rule T3 — Mock External Services
- All Twitter API calls must be mocked in tests — never hit the real API in a test
- All OpenRouter LLM calls must be mocked — never spend tokens in tests
- All web search calls must be mocked
- Use `pytest-mock` or `unittest.mock` for mocking

### Rule T4 — Test Coverage Minimum
- Every module must achieve at least **80% line coverage**
- Run: `pytest --cov=src --cov-report=term-missing`
- Coverage report is printed after every test run

### Rule T5 — Test Categories
Each module must have at minimum:
- **Happy path test** — normal input produces expected output
- **Edge case test** — empty input, null values, missing fields
- **Error handling test** — what happens when an external service fails

### Rule T6 — Integration Tests
A separate `tests/test_integration.py` file runs the full main loop in dry-run mode with all external calls mocked. This confirms modules chain correctly.

### Rule T7 — Test Naming Convention
```
test_[module]_[scenario]_[expected_outcome]

Examples:
test_comment_generator_short_tweet_produces_comment_under_260_chars
test_safety_filter_duplicate_tweet_returns_rejected
test_twitter_client_rate_limit_triggers_backoff
```

### Rule T8 — No Silent Failures
Every test must have an explicit assertion. `assert True` is banned. Every test must assert something meaningful.

### Rule T9 — Fixtures File
Common test data (sample tweets, sample LLM responses, sample configs) live in `tests/fixtures.py` and are shared across all test files.

---

## 8. Git Commit Rules

The code agent must follow these rules exactly:

### Rule G1 — When to Commit

Commit after each of these events:
1. A new module file is created (even if incomplete)
2. A module passes all its unit tests
3. A phase is fully complete (all modules + tests passing)
4. A config file is added or significantly changed
5. A bug is fixed that was causing test failures
6. Documentation is added or updated

### Rule G2 — Commit Command

Always use:
```bash
git add .
git commit -m "[type]: [short description]"
```

### Rule G3 — Commit Message Format

```
type: short description (max 72 chars)

[optional body: what changed and why, max 3 sentences]
```

**Types:**
- `feat` — new module or feature
- `test` — adding or fixing tests
- `fix` — bug fix
- `docs` — documentation only
- `config` — config files changed
- `refactor` — code restructured, no behaviour change
- `chore` — build scripts, gitignore, project setup

**Examples:**
```
feat: add OpenRouter LLM client with model fallback

test: add unit tests for Tweet Analyser module (94% coverage)

fix: safety filter was not checking duplicate tweets correctly

docs: add Phase 2 module specs to instruction.md

feat: complete Phase 1 - all modules passing, Twitter auth works
```

### Rule G4 — One Thing Per Commit
Do not bundle unrelated changes. If you fixed a bug AND added a feature, that is two commits.

### Rule G5 — Never Commit Secrets
`config.yaml`, `.env`, any file containing real API keys — must be in `.gitignore` before the first commit. Verify this before every `git add .`.

### Rule G6 — Phase Milestone Tag
After each phase is fully complete and all tests pass, create a tag:
```bash
git tag -a phase-1-complete -m "Phase 1 complete: foundation modules working"
git tag -a phase-2-complete -m "Phase 2 complete: intelligence layer working"
# etc.
```

---

## 9. Documentation Rules

### Rule D1 — Module Docstring
Every Python file must start with a module-level docstring:
```python
"""
module_name.py

What this module does in 1-2 sentences.
Key dependencies: [list them]
"""
```

### Rule D2 — Function Docstring
Every public function must have a docstring:
```python
def generate_comment(tweet: Tweet, context: SearchContext) -> list[CommentCandidate]:
    """
    Generate 3 comment candidates for a given tweet.
    
    Args:
        tweet: The Tweet object to reply to
        context: Optional web search context to incorporate
    
    Returns:
        List of 3 CommentCandidate objects with scores
    
    Raises:
        LLMError: If OpenRouter API call fails after fallback
    """
```

### Rule D3 — README.md
A `README.md` must exist in the project root. It must contain:
- What the bot does (2 paragraphs)
- Prerequisites (Python version, Twitter API access level needed)
- Setup instructions (step by step, no assumptions)
- How to run: `python bot.py start`
- How to dry-run: `python bot.py dry-run`
- How to add a target account
- Troubleshooting section (top 5 likely errors + fixes)

### Rule D4 — CHANGELOG.md
A `CHANGELOG.md` is updated after each phase:
```markdown
## Phase 2 Complete — [date]
- Added OpenRouter LLM Client with fallback support
- Added Tweet Analyser (structured output via LLM)
- Added Web Searcher with DuckDuckGo + caching
- Added Comment Generator with 3-candidate system
- Added Comment Selector with scoring
- All modules: >80% test coverage
```

### Rule D5 — Inline Comments
Non-obvious logic must have inline comments. Obvious code must NOT have comments (no `# increment i by 1`). The bar: "would a competent developer be confused by this in 6 months?"

### Rule D6 — Prompt Files
Every LLM prompt file in `prompts/` must have a header comment:
```
# prompt: comment_generator.txt
# used by: Module 2.4 Comment Generator
# model: any OpenRouter compatible model
# output format: plain text, 3 candidates separated by ---
# last updated: [date]
```

---

## 10. Rate Limits & Safety

### Twitter API Rate Limits (Free Tier)

| Endpoint | Limit |
|---|---|
| Read tweets | 500,000 tweets/month |
| Post tweets/replies | 1,500/month (50/day) |
| User lookup | 300 requests/15 min |

**The bot must never exceed 20 replies/day.** This gives comfortable headroom.

### Human-Like Behaviour Rules

- Never post two replies within 20 minutes of each other
- Add random delay of 5–30 seconds before posting (simulates typing)
- Don't reply to every tweet from the same account — maximum 1 reply per account per day
- Skip accounts that have posted in the last 5 minutes (avoid pile-ons)
- If 3+ errors occur in one cycle, pause and alert via log

### Persona Safety Rules

- Never claim to be human if directly asked
- Never engage with political topics (add "politics" related keywords to blacklist)
- Never comment on personal/tragedy content (Safety Filter must detect and skip)
- Never reply to accounts with fewer than 10,000 followers (low ROI + risk)
- If a tweet contains ANY of: violence, death, mental health crisis — skip it

---

## 11. File & Folder Structure

```
twitter-bot/
│
├── bot.py                     # CLI entry point
├── config.yaml                # GITIGNORED - user's real config
├── config.example.yaml        # Committed - template with placeholders
├── requirements.txt           # Python dependencies
├── README.md
├── CHANGELOG.md
├── .gitignore
│
├── src/
│   ├── __init__.py
│   ├── config_loader.py       # Module 1.1
│   ├── logger.py              # Module 1.2
│   ├── twitter_client.py      # Module 1.3
│   ├── target_manager.py      # Module 1.4
│   ├── llm_client.py          # Module 2.1
│   ├── tweet_analyser.py      # Module 2.2
│   ├── web_searcher.py        # Module 2.3
│   ├── comment_generator.py   # Module 2.4
│   ├── comment_selector.py    # Module 2.5
│   ├── safety_filter.py       # Module 3.1
│   ├── scheduler.py           # Module 3.2
│   ├── main_loop.py           # Module 3.3
│   ├── knowledge_store.py     # Module 3.4
│   ├── knowledge_updater.py   # Module 4.1
│   ├── performance_analyser.py # Module 4.2
│   ├── target_expander.py     # Module 4.3
│   └── report_generator.py    # Module 5.2
│
├── prompts/
│   ├── tweet_analyser.txt
│   ├── comment_generator.txt
│   ├── comment_scorer.txt
│   ├── bot_reveal_check.txt
│   ├── web_search_summariser.txt
│   ├── knowledge_updater.txt
│   └── performance_analyser.txt
│
├── data/
│   ├── targets.yaml           # Target accounts list
│   ├── bot_state.json         # Runtime state (paused/running)
│   ├── bot.db                 # SQLite knowledge store (GITIGNORED)
│   ├── performance_insights.md  # Generated by Module 4.2
│   └── suggested_targets.md   # Generated by Module 4.3
│
├── logs/
│   └── bot.log               # GITIGNORED
│
└── tests/
    ├── fixtures.py            # Shared test data
    ├── test_config_loader.py
    ├── test_logger.py
    ├── test_twitter_client.py
    ├── test_target_manager.py
    ├── test_llm_client.py
    ├── test_tweet_analyser.py
    ├── test_web_searcher.py
    ├── test_comment_generator.py
    ├── test_comment_selector.py
    ├── test_safety_filter.py
    ├── test_scheduler.py
    ├── test_main_loop.py
    ├── test_knowledge_store.py
    └── test_integration.py
```

---

## Final Notes for the Code Agent

1. **Build in order.** Phase 1 before Phase 2. Do not skip ahead.
2. **Test as you go.** Never leave a module untested before starting the next.
3. **Commit frequently.** Every meaningful milestone gets a commit.
4. **Fail loudly.** If config is wrong or an API is unreachable, raise a clear error — don't silently skip.
5. **The Safety Filter is sacred.** It runs every single time. It is never bypassed. Ever.
6. **The persona is the product.** If a comment sounds like a bot or sounds like marketing copy, it failed. Make it sound like a smart, curious developer wrote it at 11pm.
7. **Dry-run mode must work perfectly.** This is how the owner will test changes. Every action that would post to Twitter must be skippable in dry-run mode with a clear log entry instead.
8. **Document the `prompts/` folder.** Prompts are the most important thing to get right and the easiest thing to iterate. Keep them clean and commented.

---

*End of PRD & Instruction Document*
