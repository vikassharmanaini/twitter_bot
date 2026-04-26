"""
knowledge_store.py

SQLite persistence: replied tweets, topics, daily stats, knowledge snippets.
Key dependencies: sqlite3, json, datetime, config_loader
"""

from __future__ import annotations

import json
import sqlite3
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from src.config_loader import AppConfig


class KnowledgeStore:
    def __init__(self, cfg: AppConfig):
        self._path = Path(cfg.paths.knowledge_db)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self._path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        c = self._conn.cursor()
        c.executescript(
            """
            CREATE TABLE IF NOT EXISTS replied_tweets (
                tweet_id TEXT PRIMARY KEY,
                account TEXT,
                reply_text TEXT,
                posted_at TEXT,
                score_breakdown TEXT
            );
            CREATE TABLE IF NOT EXISTS seen_topics (
                topic TEXT PRIMARY KEY,
                first_seen TEXT,
                last_seen TEXT,
                count INTEGER DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS daily_stats (
                date TEXT PRIMARY KEY,
                replies_posted INTEGER DEFAULT 0,
                accounts_checked INTEGER DEFAULT 0,
                tokens_used INTEGER DEFAULT 0,
                errors INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS knowledge_snippets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic TEXT,
                summary TEXT,
                source_url TEXT,
                learned_at TEXT
            );
            """
        )
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def has_replied_to(self, tweet_id: str) -> bool:
        row = self._conn.execute(
            "SELECT 1 FROM replied_tweets WHERE tweet_id = ?",
            (tweet_id,),
        ).fetchone()
        return row is not None

    def record_reply(
        self,
        tweet_id: str,
        account: str,
        reply_text: str,
        posted_at: datetime,
        score_breakdown: dict[str, Any],
    ) -> None:
        self._conn.execute(
            """INSERT OR REPLACE INTO replied_tweets
            (tweet_id, account, reply_text, posted_at, score_breakdown)
            VALUES (?, ?, ?, ?, ?)""",
            (tweet_id, account, reply_text, posted_at.isoformat(), json.dumps(score_breakdown)),
        )
        self._conn.commit()

    def recent_reply_texts(self, limit: int = 50) -> list[str]:
        rows = self._conn.execute(
            "SELECT reply_text FROM replied_tweets ORDER BY posted_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [str(r[0]) for r in rows]

    def bump_topic(self, topic: str, when: datetime | None = None) -> None:
        when = when or datetime.now(timezone.utc)
        t = topic.strip()
        if not t:
            return
        row = self._conn.execute("SELECT count FROM seen_topics WHERE topic = ?", (t,)).fetchone()
        if row:
            self._conn.execute(
                "UPDATE seen_topics SET last_seen = ?, count = count + 1 WHERE topic = ?",
                (when.isoformat(), t),
            )
        else:
            self._conn.execute(
                "INSERT INTO seen_topics (topic, first_seen, last_seen, count) VALUES (?, ?, ?, 1)",
                (t, when.isoformat(), when.isoformat()),
            )
        self._conn.commit()

    def get_daily_reply_count(self, d: date | None = None) -> int:
        d = d or date.today()
        row = self._conn.execute(
            "SELECT replies_posted FROM daily_stats WHERE date = ?",
            (d.isoformat(),),
        ).fetchone()
        return int(row[0]) if row else 0

    def increment_daily_replies(self, delta: int = 1, d: date | None = None) -> None:
        d = d or date.today()
        ds = d.isoformat()
        self._conn.execute(
            """INSERT INTO daily_stats (date, replies_posted, accounts_checked, tokens_used, errors)
            VALUES (?, ?, 0, 0, 0)
            ON CONFLICT(date) DO UPDATE SET replies_posted = replies_posted + excluded.replies_posted""",
            (ds, delta),
        )
        self._conn.commit()

    def increment_daily_stat(
        self,
        *,
        accounts_checked: int = 0,
        tokens_used: int = 0,
        errors: int = 0,
        d: date | None = None,
    ) -> None:
        d = d or date.today()
        ds = d.isoformat()
        self._conn.execute(
            """INSERT INTO daily_stats (date, replies_posted, accounts_checked, tokens_used, errors)
            VALUES (?, 0, 0, 0, 0)
            ON CONFLICT(date) DO NOTHING""",
            (ds,),
        )
        self._conn.execute(
            """UPDATE daily_stats SET
              accounts_checked = accounts_checked + ?,
              tokens_used = tokens_used + ?,
              errors = errors + ?
            WHERE date = ?""",
            (accounts_checked, tokens_used, errors, ds),
        )
        self._conn.commit()

    def last_post_time(self) -> datetime | None:
        row = self._conn.execute(
            "SELECT posted_at FROM replied_tweets ORDER BY posted_at DESC LIMIT 1"
        ).fetchone()
        if not row:
            return None
        try:
            return datetime.fromisoformat(str(row[0]))
        except ValueError:
            return None

    def replies_today_for_account(self, account: str, d: date | None = None) -> int:
        d = d or date.today()
        start = datetime(d.year, d.month, d.day, tzinfo=timezone.utc).isoformat()
        end = (datetime(d.year, d.month, d.day, tzinfo=timezone.utc) + timedelta(days=1)).isoformat()
        row = self._conn.execute(
            """SELECT COUNT(*) FROM replied_tweets
            WHERE account = ? AND posted_at >= ? AND posted_at < ?""",
            (account.lstrip("@"), start, end),
        ).fetchone()
        return int(row[0]) if row else 0

    def add_knowledge_snippet(self, topic: str, summary: str, source_url: str) -> None:
        self._conn.execute(
            """INSERT INTO knowledge_snippets (topic, summary, source_url, learned_at)
            VALUES (?, ?, ?, ?)""",
            (topic, summary, source_url, datetime.now(timezone.utc).isoformat()),
        )
        self._conn.commit()

    def get_snippets_for_topic(self, topic: str, limit: int = 3) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            """SELECT topic, summary, source_url FROM knowledge_snippets
            WHERE topic LIKE ? ORDER BY learned_at DESC LIMIT ?""",
            (f"%{topic}%", limit),
        ).fetchall()
        return [{"topic": r[0], "summary": r[1], "source_url": r[2]} for r in rows]

    def hot_topics(self, min_count: int = 3) -> list[str]:
        rows = self._conn.execute(
            "SELECT topic FROM seen_topics WHERE count >= ? ORDER BY count DESC",
            (min_count,),
        ).fetchall()
        return [str(r[0]) for r in rows]

    def list_replied_tweet_ids(self) -> set[str]:
        rows = self._conn.execute("SELECT tweet_id FROM replied_tweets").fetchall()
        return {str(r[0]) for r in rows}

    def weekly_summary_rows(self) -> list[sqlite3.Row]:
        week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        return self._conn.execute(
            "SELECT * FROM replied_tweets WHERE posted_at >= ? ORDER BY posted_at DESC",
            (week_ago,),
        ).fetchall()

    def clear_replied_history(self) -> None:
        self._conn.execute("DELETE FROM replied_tweets")
        self._conn.commit()

    def list_recent_replies(self, limit: int = 10) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            """SELECT tweet_id, account, reply_text, posted_at
            FROM replied_tweets ORDER BY posted_at DESC LIMIT ?""",
            (limit,),
        ).fetchall()
        return [
            {"tweet_id": r[0], "account": r[1], "reply_text": r[2], "posted_at": r[3]} for r in rows
        ]

    def update_reply_engagement(self, tweet_id: str, engagement: dict[str, Any]) -> None:
        # store in score_breakdown or new column - merge into score_breakdown JSON
        row = self._conn.execute(
            "SELECT score_breakdown FROM replied_tweets WHERE tweet_id = ?",
            (tweet_id,),
        ).fetchone()
        if not row:
            return
        try:
            bd = json.loads(row[0] or "{}")
        except json.JSONDecodeError:
            bd = {}
        bd["engagement_received"] = engagement
        self._conn.execute(
            "UPDATE replied_tweets SET score_breakdown = ? WHERE tweet_id = ?",
            (json.dumps(bd), tweet_id),
        )
        self._conn.commit()

    def export_weekly_summary_json(self) -> dict[str, Any]:
        rows = self.weekly_summary_rows()
        return {
            "count": len(rows),
            "items": [dict(r) for r in rows],
        }
