"""Tests for twitter_client."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
import requests

from src.config_loader import AppConfig
from src.twitter_client import RateLimitError, TwitterAPIError, TwitterClient
from tests.fixtures import MINIMAL_CONFIG_DICT


def _cfg() -> AppConfig:
    return AppConfig.model_validate(MINIMAL_CONFIG_DICT)


def test_get_user_id_success() -> None:
    session = MagicMock(spec=requests.Session)
    resp = MagicMock()
    resp.status_code = 200
    resp.content = b'{"data":{"id":"99","username":"x"}}'
    resp.json.return_value = {"data": {"id": "99", "username": "x"}}
    session.request.return_value = resp
    c = TwitterClient(_cfg(), session=session, max_retries=2)
    assert c.get_user_id("x") == "99"
    session.request.assert_called()


def test_get_user_id_not_found() -> None:
    session = MagicMock(spec=requests.Session)
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {"errors": []}
    session.request.return_value = resp
    c = TwitterClient(_cfg(), session=session)
    with pytest.raises(TwitterAPIError, match="user not found"):
        c.get_user_id("nope")


def test_rate_limit_retries_then_raises() -> None:
    session = MagicMock(spec=requests.Session)
    bad = MagicMock(status_code=429, text="limit")
    ok = MagicMock(status_code=200)
    ok.json.return_value = {"data": {"id": "1"}}
    session.request.side_effect = [bad, ok]
    c = TwitterClient(_cfg(), session=session, max_retries=3)
    assert c.get_user_id("u") == "1"


def test_rate_limit_exhausted() -> None:
    session = MagicMock(spec=requests.Session)
    bad = MagicMock(status_code=429, text="limit")
    session.request.return_value = bad
    c = TwitterClient(_cfg(), session=session, max_retries=2)
    with pytest.raises(RateLimitError):
        c.get_user_id("u")


def test_post_reply_success() -> None:
    session = MagicMock(spec=requests.Session)
    resp = MagicMock()
    resp.status_code = 201
    resp.content = b'{"data":{"id":"newid"}}'
    resp.json.return_value = {"data": {"id": "newid"}}
    session.request.return_value = resp
    c = TwitterClient(_cfg(), session=session)
    assert c.post_reply("123", "hi") == "newid"


def test_has_already_replied_delegates() -> None:
    c = TwitterClient(_cfg(), replied_checker=lambda tid: tid == "a")
    assert c.has_already_replied("a") is True
    assert c.has_already_replied("b") is False


def test_get_user_profile() -> None:
    session = MagicMock(spec=requests.Session)
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {
        "data": {
            "id": "42",
            "username": "u",
            "public_metrics": {"followers_count": 12345},
        }
    }
    session.request.return_value = resp
    c = TwitterClient(_cfg(), session=session)
    uid, n = c.get_user_profile("u")
    assert uid == "42"
    assert n == 12345


def test_get_tweet_public_metrics() -> None:
    session = MagicMock(spec=requests.Session)
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {"data": {"public_metrics": {"like_count": 7}}}
    session.request.return_value = resp
    c = TwitterClient(_cfg(), session=session)
    m = c.get_tweet_public_metrics("tid")
    assert m.get("like_count") == 7


def test_get_following_usernames() -> None:
    session = MagicMock(spec=requests.Session)
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {"data": [{"username": "a"}, {"username": "b"}]}
    session.request.return_value = resp
    c = TwitterClient(_cfg(), session=session)
    assert c.get_following_usernames("99") == ["a", "b"]


def test_get_recent_tweets_parses() -> None:
    session = MagicMock(spec=requests.Session)
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {
        "data": [
            {
                "id": "t1",
                "text": "hello",
                "created_at": "2024-01-01T00:00:00.000Z",
                "author_id": "42",
                "public_metrics": {"like_count": 1, "retweet_count": 2, "reply_count": 3},
            }
        ],
        "includes": {"users": [{"id": "42", "username": "dev"}]},
    }
    session.request.return_value = resp
    c = TwitterClient(_cfg(), session=session)
    tweets = c.get_recent_tweets("42", count=5)
    assert len(tweets) == 1
    assert tweets[0].tweet_id == "t1"
    assert tweets[0].author_username == "dev"
