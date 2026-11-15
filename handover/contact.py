"""Who the person is and how the legal team reaches them.

These details are entered at the hand-over. First name, surname and e-mail
address are required (decided by the legal lead on 2026-11-15): the advisor has
to know whom they are talking to, and LexTec answers requests by e-mail. The
phone number is optional. The details go into the briefing only; they are never
part of a model prompt, and no model reads or checks them.
"""
from __future__ import annotations

import re

FIELDS = ("first_name", "last_name", "email", "phone")
REQUIRED = ("first_name", "last_name", "email")
MAX_LENGTH = {"first_name": 80, "last_name": 80, "email": 200, "phone": 40}

# One @, no spaces, a dot in the domain. Whether the address exists is not checked.
_EMAIL = re.compile(r"[^@\s]+@[^@\s.]+(\.[^@\s.]+)+")


def clean(raw) -> dict[str, str]:
    """The four details as trimmed text. Anything that is not text counts as empty."""
    raw = raw if isinstance(raw, dict) else {}
    out = {}
    for name in FIELDS:
        value = raw.get(name)
        value = " ".join(value.split()) if isinstance(value, str) else ""
        out[name] = value[:MAX_LENGTH[name]]
    return out


def problems(contact: dict[str, str]) -> list[str]:
    """The required details that are missing or unusable, in the order of the form."""
    out = []
    for name in ("first_name", "last_name"):
        if not any(ch.isalpha() for ch in contact.get(name, "")):
            out.append(name)
    if not _EMAIL.fullmatch(contact.get("email", "")):
        out.append("email")
    return out


def full_name(contact: dict[str, str]) -> str:
    return " ".join(p for p in (contact.get("first_name", ""), contact.get("last_name", "")) if p)


__all__ = ["FIELDS", "REQUIRED", "MAX_LENGTH", "clean", "problems", "full_name"]
