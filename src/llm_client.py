"""
llm_client.py

OpenRouter chat completions with model fallback, per-run token budget, usage logging.
Key dependencies: httpx, config_loader, logging
"""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from src.config_loader import AppConfig

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


class LLMError(Exception):
    """LLM request failed after fallback."""


class LLMClient:
    def __init__(self, cfg: AppConfig, logger: logging.Logger | None = None):
        self._cfg = cfg
        self._log = logger or logging.getLogger("twitter_bot")
        self._budget_remaining = cfg.openrouter.max_tokens_per_run
        self._total_prompt_tokens = 0
        self._total_completion_tokens = 0
        self._client = httpx.Client(timeout=120.0)

    def reset_budget(self) -> None:
        self._budget_remaining = self._cfg.openrouter.max_tokens_per_run
        self._total_prompt_tokens = 0
        self._total_completion_tokens = 0

    def _charge(self, usage: dict[str, Any] | None) -> None:
        if not usage:
            return
        pt = int(usage.get("prompt_tokens") or 0)
        ct = int(usage.get("completion_tokens") or 0)
        self._total_prompt_tokens += pt
        self._total_completion_tokens += ct
        self._budget_remaining -= pt + ct

    def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        max_tokens: int,
        temperature: float = 0.7,
        model: str | None = None,
    ) -> str:
        if max_tokens > self._budget_remaining:
            raise LLMError(
                f"token budget exceeded: need {max_tokens}, remaining {self._budget_remaining}"
            )
        models_to_try = [model or self._cfg.openrouter.primary_model, self._cfg.openrouter.fallback_model]
        last_err: Exception | None = None
        for m in models_to_try:
            if not m:
                continue
            try:
                body = {
                    "model": m,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                }
                r = self._client.post(
                    OPENROUTER_URL,
                    headers={
                        "Authorization": f"Bearer {self._cfg.openrouter.api_key}",
                        "Content-Type": "application/json",
                    },
                    json=body,
                )
                if r.status_code >= 400:
                    raise LLMError(f"OpenRouter HTTP {r.status_code}: {r.text[:500]}")
                data = r.json()
                choice = (data.get("choices") or [{}])[0]
                msg = (choice.get("message") or {}).get("content")
                if not msg:
                    raise LLMError(f"empty completion: {data!r}"[:500])
                self._charge(data.get("usage"))
                self._log.debug(
                    "llm ok",
                    extra={"metadata": {"model": m, "usage": data.get("usage")}},
                )
                return str(msg).strip()
            except (LLMError, httpx.HTTPError, json.JSONDecodeError, KeyError) as e:
                last_err = e
                self._log.warning("llm model failed, trying fallback", extra={"metadata": {"model": m}})
                continue
        raise LLMError(f"all models failed: {last_err}") from last_err

    def close(self) -> None:
        self._client.close()

    @property
    def usage_summary(self) -> dict[str, int]:
        return {
            "prompt_tokens": self._total_prompt_tokens,
            "completion_tokens": self._total_completion_tokens,
            "budget_remaining": self._budget_remaining,
        }
