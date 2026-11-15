"""Tests may write temporary briefings but must never send real email."""
import pytest


@pytest.fixture(autouse=True)
def disable_real_email(monkeypatch):
    # config can load .env during test collection; disable delivery afterwards.
    monkeypatch.delenv("SMTP_HOST", raising=False)
    monkeypatch.delenv("BRIEFING_TO", raising=False)
