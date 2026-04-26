"""
twitter_client.py

Twitter API v2 wrapper: user lookup, timeline fetch, reply post. OAuth 1.0a for writes, Bearer for reads.
Key dependencies: requests, requests-oauthlib, logging, config_loader, models
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any

import requests
from requests_oauthlib import OAuth1

from src.config_loader import AppConfig
from src.models import Tweet


class TwitterAPIError(Exception):
    """Base Twitter API error."""

    def __init__(self, message: str, status_code: int | None = None, body: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.body = body


class RateLimitError(TwitterAPIError):
    """HTTP 429 — caller may retry with backoff."""


def _parse_dt(s: str) -> datetime:
    if not s:
        return datetime.now(timezone.utc)
    # Twitter returns ISO8601 e.g. 2023-10-01T12:00:00.000Z
    s = s.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(s)
    except ValueError:
        return datetime.now(timezone.utc)


class TwitterClient:
    """
    Thin Twitter v2 client. Uses Bearer for GET, OAuth1 user context for POST /2/tweets.
    """

    BASE = "https://api.twitter.com/2"

    def __init__(
        self,
        cfg: AppConfig,
        logger: logging.Logger | None = None,
        session: requests.Session | None = None,
        replied_checker: Callable[[str], bool] | None = None,
        max_retries: int = 4,
    ):
        self._cfg = cfg
        self._log = logger or logging.getLogger("twitter_bot")
        self._session = session or requests.Session()
        self._replied_checker = replied_checker
        self._max_retries = max_retries
        self._oauth1 = OAuth1(
            cfg.twitter.api_key,
            client_secret=cfg.twitter.api_secret,
            resource_owner_key=cfg.twitter.access_token,
            resource_owner_secret=cfg.twitter.access_token_secret,
        )

    def _headers_bearer(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._cfg.twitter.bearer_token}"}

    def _request(
        self,
        method: str,
        url: str,
        *,
        use_oauth: bool = False,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        last_err: Exception | None = None
        delay = 1.0
        for attempt in range(self._max_retries):
            auth = self._oauth1 if use_oauth else None
            headers: dict[str, str] = {}
            if not use_oauth:
                headers.update(self._headers_bearer())
            if json_body is not None:
                headers["Content-Type"] = "application/json"
            resp = self._session.request(
                method,
                url,
                headers=headers,
                params=params,
                json=json_body,
                auth=auth,
                timeout=30,
            )
            if resp.status_code == 429:
                last_err = RateLimitError("rate limited", status_code=429, body=resp.text)
                self._log.warning(
                    "twitter rate limit",
                    extra={"metadata": {"attempt": attempt + 1, "url": url}},
                )
                time.sleep(delay)
                delay = min(delay * 2, 60)
                continue
            if resp.status_code >= 400:
                try:
                    body = resp.json()
                except Exception:
                    body = resp.text
                raise TwitterAPIError(
                    f"Twitter API error {resp.status_code}",
                    status_code=resp.status_code,
                    body=body,
                )
            if resp.status_code == 204 or not resp.content:
                return {}
            return resp.json()
        if last_err:
            raise last_err
        raise TwitterAPIError("request failed after retries")

    def get_user_profile(self, username: str) -> tuple[str, int]:
        """Return (user_id, followers_count)."""
        handle = username.lstrip("@").strip()
        url = f"{self.BASE}/users/by/username/{handle}"
        data = self._request(
            "GET",
            url,
            use_oauth=False,
            params={"user.fields": "id,username,public_metrics"},
        )
        if "data" not in data or "id" not in data["data"]:
            raise TwitterAPIError(f"user not found: {handle}", body=data)
        uid = str(data["data"]["id"])
        pm = data["data"].get("public_metrics") or {}
        followers = int(pm.get("followers_count", 0))
        return uid, followers

    def get_user_id(self, username: str) -> str:
        return self.get_user_profile(username)[0]

    def get_recent_tweets(self, user_id: str, count: int = 10) -> list[Tweet]:
        url = f"{self.BASE}/users/{user_id}/tweets"
        params: dict[str, Any] = {
            "max_results": min(max(count, 5), 100),
            "tweet.fields": "created_at,public_metrics,referenced_tweets,author_id",
            "expansions": "author_id",
            "user.fields": "username",
        }
        data = self._request("GET", url, use_oauth=False, params=params)
        tweets_raw = data.get("data") or []
        users_by_id: dict[str, str] = {}
        for u in data.get("includes", {}).get("users", []) or []:
            users_by_id[str(u["id"])] = u.get("username", "")

        out: list[Tweet] = []
        for t in tweets_raw:
            tid = str(t["id"])
            metrics = t.get("public_metrics") or {}
            ref = t.get("referenced_tweets") or []
            is_retweet = any(r.get("type") == "retweeted" for r in ref)
            is_reply = any(r.get("type") == "replied_to" for r in ref)
            aid = str(t.get("author_id", user_id))
            out.append(
                Tweet(
                    tweet_id=tid,
                    author_username=users_by_id.get(aid, ""),
                    author_id=aid,
                    text=t.get("text", ""),
                    created_at=_parse_dt(t.get("created_at", "")),
                    like_count=int(metrics.get("like_count", 0)),
                    retweet_count=int(metrics.get("retweet_count", 0)),
                    reply_count=int(metrics.get("reply_count", 0)),
                    is_retweet=is_retweet,
                    is_reply=is_reply,
                )
            )
        return out

    def post_reply(self, tweet_id: str, text: str) -> str:
        url = f"{self.BASE}/tweets"
        body = {"text": text, "reply": {"in_reply_to_tweet_id": tweet_id}}
        data = self._request("POST", url, use_oauth=True, json_body=body)
        if "data" not in data or "id" not in data["data"]:
            raise TwitterAPIError("unexpected post reply response", body=data)
        return str(data["data"]["id"])

    def has_already_replied(self, tweet_id: str) -> bool:
        if self._replied_checker is None:
            return False
        return self._replied_checker(tweet_id)

    def get_tweet_public_metrics(self, tweet_id: str) -> dict[str, int]:
        url = f"{self.BASE}/tweets/{tweet_id}"
        data = self._request(
            "GET",
            url,
            use_oauth=False,
            params={"tweet.fields": "public_metrics"},
        )
        tw = data.get("data") or {}
        pm = tw.get("public_metrics") or {}
        out: dict[str, int] = {}
        for k, v in pm.items():
            try:
                out[str(k)] = int(v)
            except (TypeError, ValueError):
                continue
        return out

    def get_following_usernames(self, user_id: str, max_results: int = 15) -> list[str]:
        """List usernames the user follows (requires API access)."""
        url = f"{self.BASE}/users/{user_id}/following"
        data = self._request(
            "GET",
            url,
            use_oauth=False,
            params={"max_results": min(max_results, 1000), "user.fields": "username"},
        )
        users = data.get("data") or []
        return [str(u.get("username", "")) for u in users if u.get("username")]
