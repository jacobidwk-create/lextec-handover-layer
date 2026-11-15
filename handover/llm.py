"""Model access behind one small interface, so the provider can be swapped.

To use a locally hosted model instead of the hosted API, point LLM_BASE_URL at
a local server that speaks the same protocol, or add another class with the
same `complete_json` method.
"""
from __future__ import annotations

import json
from typing import Protocol

from . import config


class LLM(Protocol):
    def complete_json(self, system: str, user: str) -> dict: ...


class OpenAILLM:
    """Hosted API. Reads OPENAI_API_KEY from the environment."""

    def __init__(self, model: str | None = None):
        from openai import OpenAI
        # A call that stalls must not freeze the conversation: after the time limit it
        # fails, and the engine falls back (fixed text, or the retry option).
        self.client = OpenAI(base_url=config.LLM_BASE_URL, timeout=config.LLM_TIMEOUT_SECONDS,
                             max_retries=1)
        self.model = model or config.LLM_MODEL

    def complete_json(self, system: str, user: str) -> dict:
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": user}],
            response_format={"type": "json_object"},
        )
        return json.loads(resp.choices[0].message.content)


class FakeLLM:
    """Returns prepared answers in order. Used by the tests; no network access."""

    def __init__(self, answers: list):
        self.answers = list(answers)
        self.calls: list[tuple[str, str]] = []

    def complete_json(self, system: str, user: str) -> dict:
        self.calls.append((system, user))
        if not self.answers:
            raise RuntimeError("FakeLLM has no prepared answer left")
        a = self.answers.pop(0)
        if isinstance(a, Exception):
            raise a
        return a
