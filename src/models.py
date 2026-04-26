"""
models.py

Shared domain types for tweets, analysis, search, and replies.
Key dependencies: pydantic (validation), datetime
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class Sentiment(str, Enum):
    positive = "positive"
    negative = "negative"
    neutral = "neutral"
    excited = "excited"
    controversial = "controversial"


class TweetType(str, Enum):
    announcement = "announcement"
    opinion = "opinion"
    question = "question"
    joke = "joke"
    link_share = "link_share"
    thread = "thread"


class TechnicalLevel(str, Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    expert = "expert"


class Tweet(BaseModel):
    tweet_id: str
    author_username: str
    author_id: str
    text: str
    created_at: datetime
    like_count: int = 0
    retweet_count: int = 0
    reply_count: int = 0
    is_retweet: bool = False
    is_reply: bool = False


class TweetAnalysis(BaseModel):
    tweet_id: str
    topic: str
    sentiment: Sentiment
    tweet_type: TweetType
    technical_level: TechnicalLevel
    key_entities: list[str] = Field(default_factory=list)
    requires_web_search: bool = False
    search_query: str | None = None


class SearchResultItem(BaseModel):
    title: str
    url: str
    snippet: str


class SearchContext(BaseModel):
    query: str
    results: list[SearchResultItem] = Field(default_factory=list)
    summary: str = ""
    searched_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CommentCandidate(BaseModel):
    text: str
    style: str = ""
    human_likeness_score: int = 0
    relevance_score: int = 0
    engagement_score: int = 0
    risk_score: int = 0
    total_score: float = 0.0


class PostedReply(BaseModel):
    tweet_id: str
    target_account: str
    reply_text: str
    posted_at: datetime
    style_used: str = ""
    score_breakdown: dict[str, Any] = Field(default_factory=dict)
    engagement_received: dict[str, Any] | None = None


class SafetyDecision(str, Enum):
    APPROVED = "APPROVED"
    REJECTED_WITH_REASON = "REJECTED_WITH_REASON"
    REGENERATE = "REGENERATE"


class SafetyResult(BaseModel):
    decision: SafetyDecision
    reason: str = ""
