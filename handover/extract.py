"""Extraction: the only job the language model has before the gate.

The model fills the case record. Its output is then checked by code:
  * every item needs a verbatim quote from a user message (evidence check),
  * values must have the right type and, for choices, an allowed value,
  * an explicit date inside the quote must match the extracted date.
Anything that fails a check is discarded and stays "missing".
"""
from __future__ import annotations

import json
import re
import math
from copy import deepcopy
from datetime import date

from .areas import AREAS, FIELDS, FIELD_BY_NAME
from .legal_fields import REGISTRY
from .knowledge import TOPICS
from .llm import LLM
from .schema import Case, Status

SYSTEM = """You are the information-extraction component of a legal intake system \
for the Canton of Zurich, Switzerland. You do not give advice and you do not decide \
anything. Users write in German or English.

Rules:
- Extract only what the USER explicitly stated. Never guess, infer or assume a missing \
fact. If something was not stated, leave it out.
- Every item needs "evidence": a short quote copied character by character from a USER \
message. Items without a verbatim quote are discarded.
- If the user says they do not know something, return \
{"value": null, "user_does_not_know": true, "evidence": "<quote>"} for that fact.
- Dates: resolve relative dates ("yesterday", "letzten Montag") against today's date and \
return YYYY-MM-DD. An approximate time is an answer: return the EARLIEST day it can \
mean ("about two weeks ago" = 14 days before today; "early September" = 1 September; \
"in June" = 1 June; "three months ago" = the same day three months before today). \
Only if no time at all can be told ("recently", "vor kurzem", "a while ago"), leave the \
fact out.
- Do not equate paid with withdrawn, disputed with a formal objection, or a relative with a statutory heir.
- Extract jurisdiction and case_complexity only from explicit facts; do not assume Zurich.
- Legal exceptions (inventory, extension, earlier official papers) must be extracted even if volunteered outside the current questions.
- bool facts: true or false. number facts: a plain number. choice facts: one of the \
listed values.
- A fact listed under "Asked in the last reply" is being answered by the user's latest \
message: people answer in everyday words, so choose the listed value whose description \
fits what they say best (for example "never saw that in any contract" for a fee fits \
"not agreed"; "no receipts, just a lump sum" fits "flat"). Leave it out only if the \
message does not address it; if they say they do not know, use user_does_not_know.
- A latest message often answers more than the one question. Record every fact it \
answers in the same way, also facts that were not asked yet.
- For a fact that the user only touches in passing in an earlier message, return a \
choice value only if their words clearly state what its description says; otherwise \
leave it out, it will be asked.
- "uncovered": the user's matter lies in a covered legal field, but an important part of \
what they want to know is listed under "Not covered" for that field (for example whether \
a contract that was not cancelled is still owed). Then return a short plain name of that \
legal topic in the user's language (no article numbers, no digits) and a quote of the \
user's words that raise it. Otherwise null. A matter that belongs to no covered field \
is area "other", not "uncovered".
- "contradictions": pairs of user statements that cannot both be true. Leave empty if \
an earlier statement was simply corrected by the user.
- "user_questions": questions the USER asks in their LATEST message. Statements and \
answers to earlier questions are not questions. For each question choose the best \
topic id from "Question topics" and copy the question as evidence from the latest USER \
message. A question about what a term or the service means in general gets that topic \
even if the user's case involves it. Use "own_case" when the user asks what applies to \
them or what they should do. Use "other" if nothing fits. Leave empty if the latest \
message contains no question.

Return one JSON object:
{
  "language": "de" | "en",
  "areas": [{"area": "<area id>", "evidence": "<quote>"}],
  "facts": {"<fact name>": {"value": ..., "evidence": "<quote>"}},
  "wants_human": {"value": true, "evidence": "<quote>"} | null,
  "user_questions": [{"topic": "<topic id>", "evidence": "<quote>"}],
  "uncovered": {"topic": "<short name of the legal topic>", "evidence": "<quote>"} | null,
  "contradictions": [{"description": "...", "evidence_a": "<quote>", "evidence_b": "<quote>"}]__DISTRESS_SCHEMA__
}"""

DISTRESS_SCHEMA = (',\n  "distress": {"value": true, "evidence": "<quote>"} | null   '
                   "(signs of acute psychological distress or self-harm)")


def build_prompt(case: Case, today: date) -> tuple[str, str]:
    system = SYSTEM.replace(
        "__DISTRESS_SCHEMA__", DISTRESS_SCHEMA if case.consent_distress_screening else "")
    areas = "\n".join(f"- {k}: {v}" for k, v in AREAS.items())
    facts = "\n".join(
        f"- {f.name} [{f.kind}{': ' + ' | '.join(f.choices) if f.choices else ''}] "
        f"(area {f.area}): {f.description}" for f in FIELDS)
    convo = "\n".join(f"{role.upper()}: {text}" for role, text in case.messages)
    topics = "\n".join(f"- {k}: {v}" for k, v in TOPICS.items())
    scope = "\n".join(f"- {f.id}. Covers: {f.covers} Not covered: {f.not_covered}"
                      for f in REGISTRY.values())
    asked = ", ".join(n for n in case.last_asked if n in FIELD_BY_NAME) or "nothing"
    user = (f"Today's date: {today.isoformat()} ({today.strftime('%A')})\n\n"
            f"Area ids:\n{areas}\n\nLegal fields:\n{scope}\n\nFacts:\n{facts}\n\n"
            f"Question topics:\n{topics}\n\nAsked in the last reply: {asked}\n\n"
            f"Conversation:\n{convo}")
    return system, user


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip().lower()


def evidence_ok(quote, case: Case) -> bool:
    """True if the quote literally appears in what the user wrote."""
    return (isinstance(quote, str) and len(quote.strip()) > 0
            and _norm(quote) in _norm(case.user_text()))


_DMY = re.compile(r"\b(\d{1,2})\.\s?(\d{1,2})\.\s?(\d{4}|\d{2})\b")
_ISO = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")


def _explicit_dates(text: str) -> list[date]:
    out = []
    for d, m, y in _DMY.findall(text):
        y = int(y) + (2000 if len(y) == 2 else 0)
        try:
            out.append(date(y, int(m), int(d)))
        except ValueError:
            pass
    for y, m, d in _ISO.findall(text):
        try:
            out.append(date(int(y), int(m), int(d)))
        except ValueError:
            pass
    return out


def _coerce(spec, raw, evidence: str, today: date):
    """Return (ok, value). Rejects wrong types and implausible values."""
    if spec.kind == "bool":
        return (isinstance(raw, bool), raw)
    if spec.kind == "choice":
        return (raw in spec.choices, raw)
    if spec.kind == "number":
        ok = isinstance(raw, (int, float)) and not isinstance(raw, bool) and math.isfinite(raw) and raw >= 0
        return (ok, float(raw) if ok else None)
    if spec.kind == "text":
        ok = isinstance(raw, str) and raw.strip() != ""
        return (ok, raw.strip() if ok else None)
    if spec.kind == "date":
        try:
            value = date.fromisoformat(raw)
        except (TypeError, ValueError):
            return (False, None)
        if value > today:                       # events in the future are implausible
            return (False, None)
        explicit = _explicit_dates(evidence)
        if len(explicit) == 1 and explicit[0] != value:
            return (False, None)                # quote says a different date
        return (True, value)
    return (False, None)


def apply_extraction(case: Case, data: dict, today: date) -> None:
    """Validate the model output and merge the valid parts into the case."""
    if data.get("language") in ("de", "en"):
        case.language = data["language"]

    for item in data.get("areas") or []:
        area, ev = item.get("area"), item.get("evidence")
        if area in AREAS and evidence_ok(ev, case):
            case.areas.setdefault(area, ev)
        else:
            case.audit.append(f"rejected area {area!r}: unknown id or evidence not found")

    for name, item in (data.get("facts") or {}).items():
        spec = FIELD_BY_NAME.get(name)
        if spec is None or not isinstance(item, dict):
            case.audit.append(f"rejected fact {name!r}: unknown fact")
            continue
        ev = item.get("evidence")
        if not evidence_ok(ev, case):
            case.audit.append(f"rejected fact {name}: evidence not found in user text")
            continue
        fact = case.fact(name)
        if item.get("user_does_not_know") is True:
            latest_user = next((t for role, t in reversed(case.messages) if role == "user"), "")
            if fact.status is not Status.KNOWN or _norm(ev) in _norm(latest_user):
                fact.status, fact.value, fact.evidence = Status.USER_UNKNOWN, None, ev
            continue
        ok, value = _coerce(spec, item.get("value"), ev, today)
        if not ok:
            # A newly reported unusable value must not leave an old safe value active.
            fact.status, fact.value, fact.evidence = Status.MISSING, None, ""
            case.audit.append(f"rejected fact {name}: invalid value {item.get('value')!r}")
            continue
        if fact.status is Status.KNOWN and fact.value != value:
            case.audit.append(f"fact {name} changed: {fact.value!r} -> {value!r}")
        if not (fact.status is Status.KNOWN and fact.value == value and fact.confirmed):
            # Read from free text. It counts as confirmed only if the question had
            # been put to the person and the words come from their latest message (an
            # older sentence that the model reads again is not an answer). This matters
            # for values in FieldSpec.confirm.
            newest = next((t for role, t in reversed(case.messages) if role == "user"), "")
            fact.confirmed = name in case.last_asked and _norm(ev) in _norm(newest)
        fact.status, fact.value, fact.evidence = Status.KNOWN, value, ev
        fact.failed_attempts = 0

    wh = data.get("wants_human")
    latest = next((t for r, t in reversed(case.messages) if r == "user"), "")
    if (isinstance(wh, dict) and wh.get("value") is True
            and evidence_ok(wh.get("evidence"), case)
            and _norm(wh["evidence"]) in _norm(latest)):
        case.flags.setdefault("wants_human", wh["evidence"])

    if case.consent_distress_screening:
        ds = data.get("distress")
        if (isinstance(ds, dict) and ds.get("value") is True
                and evidence_ok(ds.get("evidence"), case)):
            case.flags.setdefault("distress", ds["evidence"])

    # Questions the user asked in the latest message. The model only names the topic;
    # the answer comes from fixed texts (knowledge.py). At most three per message.
    latest = next((t for r, t in reversed(case.messages) if r == "user"), "")
    case.turn_questions = []
    for q in data.get("user_questions") or []:
        if not isinstance(q, dict):
            continue
        topic, ev = q.get("topic"), q.get("evidence")
        if (topic in TOPICS and isinstance(ev, str) and ev.strip()
                and _norm(ev) in _norm(latest) and topic not in case.turn_questions):
            case.turn_questions.append(topic)
    case.turn_questions = case.turn_questions[:3]

    # A part of the matter the stored sources do not cover. The model names the topic;
    # the quote must be the person's own words. A declined proposal is not repeated
    # for the same words.
    un = data.get("uncovered")
    topic = " ".join(str(un.get("topic") or "").split()) if isinstance(un, dict) else ""
    if (topic and len(topic) <= 120 and not re.search(r"\d|§|\bart\.", topic, re.IGNORECASE)
            and evidence_ok(un.get("evidence"), case)):
        old = case.uncovered or {}
        same = _norm(old.get("evidence", "")) == _norm(un["evidence"])
        case.uncovered = {"topic": topic, "evidence": un["evidence"],
                          "declined": bool(old.get("declined")) and same}
    elif case.uncovered and not case.uncovered.get("declined"):
        case.uncovered = None            # no longer raised by what the person wrote

    case.contradictions = [
        f"«{c['evidence_a']}» vs. «{c['evidence_b']}»"
        for c in data.get("contradictions") or []
        if isinstance(c, dict) and evidence_ok(c.get("evidence_a"), case)
        and evidence_ok(c.get("evidence_b"), case)
    ]


def extract(llm: LLM, case: Case, today: date) -> None:
    """Call the model (one retry) and merge. On failure, mark the case: fail closed."""
    system, user = build_prompt(case, today)
    case.turn_questions = []
    last_error = ""
    for _ in range(2):
        try:
            data = llm.complete_json(system, user)
            if not isinstance(data, dict):
                raise ValueError("model did not return a JSON object")
            candidate = deepcopy(case)
            apply_extraction(candidate, data, today)
            if candidate.technical_failure:
                candidate.audit.append("extraction recovered; technical failure cleared")
            candidate.technical_failure = ""
            case.__dict__.update(candidate.__dict__)
            return
        except (json.JSONDecodeError, ValueError, KeyError, TypeError, AttributeError) as e:
            last_error = f"{type(e).__name__}: {e}"
        except Exception as e:  # network or API errors
            last_error = f"{type(e).__name__}: {e}"
    case.technical_failure = last_error
    case.audit.append(f"extraction failed twice: {last_error}")
