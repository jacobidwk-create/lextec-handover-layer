"""Data structures shared by all components.

The case record is the only thing the gate (rules.py) looks at. The language
model fills it; it never decides the route.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Any, Callable, Optional


class Route(str, Enum):
    PROCEED = "PROCEED"
    ASK = "ASK"
    REFER = "REFER"


class Status(str, Enum):
    MISSING = "missing"            # not stated yet
    KNOWN = "known"                # stated by the user, evidence verified
    USER_UNKNOWN = "user_unknown"  # the user said they do not know
    UNRESOLVABLE = "unresolvable"  # repeated substantive attempts without a usable answer

    @property
    def resolved(self) -> bool:
        return self is not Status.MISSING


@dataclass
class FieldSpec:
    """Definition of one fact the system may need."""
    name: str
    area: str
    kind: str                      # "bool" | "date" | "choice" | "number" | "text"
    critical: bool                 # a deadline or escalation trigger depends on it
    question: dict[str, str]       # {"de": ..., "en": ...}
    description: str               # shown to the extraction model
    choices: tuple[str, ...] = ()
    when: Optional[Callable[["Case"], bool]] = None  # only required if this holds
    # Answers offered as a list on the web page: value -> {"de": ..., "en": ...}.
    # A field with options is answered by choosing from the list (no model call).
    options: dict = field(default_factory=dict)
    # Terms explained next to the question: topic ids of knowledge.py.
    terms: tuple[str, ...] = ()
    # False: the fact is never asked for. It is recorded only if the user mentions it.
    ask: bool = True
    # Values that carry consequences (urgency, hand-over). If the model reads such a
    # value from free text, the person is asked to confirm it before any rule acts on it.
    confirm: tuple[str, ...] = ()
    # Partial answers: values that say "yes" without the detail that decides the
    # outcome (for example "a reminder fee is claimed", not yet "was it agreed?").
    # Such a value is recorded, and the detail is asked once with its own question:
    # detail = {"question": {"de": ..., "en": ...}, "values": (...)}.
    partial: tuple[str, ...] = ()
    detail: dict = field(default_factory=dict)
    # Values offered as quick replies when the question is first asked. Empty: all
    # listed answers except the detail values.
    first: tuple[str, ...] = ()


@dataclass
class Fact:
    name: str
    status: Status = Status.MISSING
    value: Any = None
    evidence: str = ""
    ask_count: int = 0
    failed_attempts: int = 0       # substantive attempts, not question displays
    # False: the model read the value from free text although the question had not been
    # put to the person. Matters only for values listed in FieldSpec.confirm.
    confirmed: bool = True
    # How often the detail of a partial answer was asked for without result.
    detail_asks: int = 0


@dataclass
class Deadline:
    label: str
    legal_basis: str
    due: date
    working_days_left: int         # negative: may already have passed
    action_done: bool
    key: str = ""                  # "objection" | "disclaimer" | "inventory" | "register_objection"


@dataclass
class Reason:
    rule: str                      # rule identifier, e.g. "R4-deadline-close"
    text: str
    evidence: str = ""


@dataclass
class Decision:
    route: Route
    reasons: list[Reason]
    questions: list[str] = field(default_factory=list)   # field names to ask
    deadlines: list[Deadline] = field(default_factory=list)
    urgent: bool = False
    emergency: bool = False
    assessed_on: Optional[date] = None


@dataclass
class Case:
    language: str = "de"
    areas: dict[str, str] = field(default_factory=dict)       # area -> evidence
    facts: dict[str, Fact] = field(default_factory=dict)
    flags: dict[str, str] = field(default_factory=dict)       # trigger -> evidence
    contradictions: list[str] = field(default_factory=list)
    contradiction_asks: int = 0
    messages: list[tuple[str, str]] = field(default_factory=list)  # (role, text)
    consent_distress_screening: bool = False
    rounds: int = 0
    last_asked: list[str] = field(default_factory=list)
    area_asks: int = 0
    no_progress_rounds: int = 0
    technical_failure: str = ""
    audit: list[str] = field(default_factory=list)
    # Questions the user asked in the latest message (topic ids, see knowledge.py).
    turn_questions: list[str] = field(default_factory=list)
    # Number of messages that only asked a question; they do not count as failed answers.
    question_turns: int = 0
    # Who the person is and how the legal team reaches them: first_name, last_name,
    # email, phone (contact.py). Entered at the hand-over, never sent to the model.
    contact: dict[str, str] = field(default_factory=dict)
    # Given to the case when the person agrees to the hand-over (briefing.py).
    case_number: str = ""
    # A part of the matter that the stored sources do not cover, as named by the model:
    # {"topic": short name, "evidence": the person's words, "declined": bool}. It can
    # only add a hand-over proposal (rule R14); it never removes one.
    uncovered: Optional[dict] = None
    # Number of messages the person typed (buttons and list answers are not counted).
    typed: int = 0
    # The day the gate last assessed the case; questions that depend on whether a
    # period has passed (areas.py) read it.
    assessed_on: Optional[date] = None
    # Hand-over proposals the person declined and that are not repeated (config.SOFT_RULES).
    declined_rules: set = field(default_factory=set)

    @property
    def no_progress(self) -> bool:
        return self.no_progress_rounds >= 2

    def fact(self, name: str) -> Fact:
        if name not in self.facts:
            self.facts[name] = Fact(name)
        return self.facts[name]

    def value(self, name: str) -> Any:
        f = self.facts.get(name)
        return f.value if f and f.status is Status.KNOWN else None

    def user_text(self) -> str:
        return "\n".join(t for r, t in self.messages if r == "user")
