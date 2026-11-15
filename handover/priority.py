"""Priority class of a handed-over case, for the legal team's work queue.

The classes follow the Eisenhower matrix (urgent / important). The quadrant
"urgent, not important" does not exist here: urgency comes from a deadline, and
a matter with a looming deadline is important (decided by the legal lead on
2026-11-15). That leaves three classes:

  1  urgent and important   the gate set the urgent mark: a deadline is close or may
                            have passed, a letter from the debt enforcement office,
                            or signs of acute distress
  2  important, not urgent  a legal reason for the hand-over without a close deadline,
                            or a deadline that was computed and is not close
  3  no deadline known      the person only wants a human, the matter is outside the
                            three legal fields, or the conversation brought no result

Class 3 is deliberately not called "not important": for a matter outside the
three fields the system checked no deadline, so it cannot say that none runs.

Fixed rules only, no model call. The class is a service policy for the order of
work; it is not a legal assessment and changes nothing the person sees. A rule
this module does not know counts as class 2, never as class 3 (fail closed).
"""
from __future__ import annotations

from . import config
from .schema import Decision

LABELS = {
    1: {"de": "Klasse 1 – dringend und wichtig", "en": "Class 1 – urgent and important"},
    2: {"de": "Klasse 2 – wichtig, nicht dringend", "en": "Class 2 – important, not urgent"},
    3: {"de": "Klasse 3 – keine Frist bekannt", "en": "Class 3 – no deadline known"},
}

BASIS = {
    "emergency": {"de": "Hinweis auf akute Belastung", "en": "signs of acute distress"},
    "urgent": {"de": "vom System als dringend eingestuft (siehe Dringlichkeit)",
               "en": "marked urgent by the system (see Urgency)"},
    "legal": {"de": "rechtlicher Übergabegrund ohne nahe Frist: {reasons}",
              "en": "legal reason for the hand-over without a close deadline: {reasons}"},
    "deadline": {"de": "Frist berechnet, nicht nah",
                 "en": "a deadline was computed and is not close"},
    "none": {"de": "Das System hat keine Frist festgestellt. Bei einem Thema ausserhalb der "
                   "drei Rechtsgebiete hat es Fristen nicht geprüft; eine Frist kann laufen.",
             "en": "The system found no deadline. For a topic outside the three legal "
                   "fields it checked no deadline; one may be running."},
}


def _key(rule: str) -> str:
    return rule.split("-")[0]


def classify(decision: Decision) -> tuple[int, str, list[str]]:
    """(class, key of the basis text, rules that carry the class)."""
    if decision.emergency:
        return 1, "emergency", []
    if decision.urgent:
        return 1, "urgent", []
    weighty = [r.rule for r in decision.reasons
               if _key(r.rule) not in config.PRIORITY_NO_DEADLINE_RULES]
    if weighty:
        return 2, "legal", weighty
    if any(not d.action_done for d in decision.deadlines):
        return 2, "deadline", []
    return 3, "none", []


def priority_class(decision: Decision) -> int:
    return classify(decision)[0]


__all__ = ["LABELS", "BASIS", "classify", "priority_class"]
