"""Keyword detectors that run independently of the language model.

They are a second, deterministic line of defence: if the model misses a hard
trigger, a detector can still fire. A detector can only make the system more
cautious (add an area, force a direct question, refer); it never clears one.
"""
from __future__ import annotations

import re

from .schema import Case, Status

_F = re.IGNORECASE


def _find(pattern: str, text: str) -> str:
    m = re.search(pattern, text, _F)
    return m.group(0) if m else ""


HUMAN_REQUEST = (r"\b(mit (einem|einer) (mensch\w*|anwalt|anwältin|jurist\w*|person) (sprechen|reden)"
                 r"|(einen|eine) (anwalt|anwältin|mensch\w*) (sprechen|bitte)"
                 r"|(speak|talk) (to|with) (a|an) (human|lawyer|person|attorney)"
                 r"|real person|human being please)\b")

# Matters the system never handles on its own: criminal, migration, child protection.
HARD_AREA = (r"\b(strafbefehl\w*|geldstrafe\w*|ersatzfreiheitsstrafe\w*|busse|bussen|"
             r"ausschaffung\w*|wegweisung\w*|landesverweis\w*|kesb|"
             r"penalty order|criminal|deportation|expulsion|imprison\w*|prison|jail)\b")

ENFORCEMENT_DOC = (r"\b(zahlungsbefehl\w*|betreibungsamt\w*|betreibung\w*|pfändung\w*|"
                   r"lohnpfändung\w*|payment order|debt enforcement|seizure|garnish\w*)\b")

INHERITANCE = (r"\b(erbschaft\w*|erbe|erben|nachlass\w*|ausschlag\w*|ausschlagen|"
               r"inherit\w*|disclaim\w*)\b")

DISTRESS = (r"\b(suizid\w*|selbstmord\w*|umbringen|nicht mehr leben|keinen ausweg|"
            r"suicid\w*|kill myself|end my life|no way out|can't go on|cannot go on)\b")

# The most common question about the service. If the model does not label it, this
# pattern still makes sure the user is told what the service covers.
SCOPE_QUESTION = (r"((wobei|womit|bei was|was) (genau )?(können|kannst|könnt) (sie|du|ihr) "
                  r"(mir |uns )?(denn )?(genau )?(helfen|tun|machen)"
                  r"|(wobei|womit) (sie|du) (mir |uns )?(genau )?helfen (können|kannst)"
                  r"|what (exactly )?can you (help|do)|what do you (help|do)"
                  r"|what (exactly )?you can (help|do)|how can you help|how you can help)")

# Values of document_type that already escalate or carry a deadline.
_ESCALATING_DOCS = {"payment_order", "seizure_notice", "court_document"}


def run_detectors(case: Case) -> None:
    text = case.user_text()

    latest = next((t for r, t in reversed(case.messages) if r == "user"), "")
    if (_find(SCOPE_QUESTION, latest) and not case.technical_failure
            and "service_scope" not in case.turn_questions):
        case.turn_questions.insert(0, "service_scope")

    # A withdrawn preference must not be restored by an older message.
    if hit := _find(HUMAN_REQUEST, latest):
        case.flags.setdefault("wants_human", hit)

    if hit := _find(HARD_AREA, text):
        if "other" not in case.areas:
            case.areas["other"] = hit
            case.audit.append(f"detector: hard area keyword '{hit}' -> area 'other'")

    if hit := _find(INHERITANCE, text):
        if "inheritance_debt" not in case.areas:
            case.areas["inheritance_debt"] = hit
            case.audit.append(f"detector: inheritance keyword '{hit}' -> area added")

    if hit := _find(ENFORCEMENT_DOC, text):
        if not case.areas.keys() & {"debt_collection", "credit_record"}:
            case.areas["debt_collection"] = hit
            case.audit.append(f"detector: enforcement keyword '{hit}' -> area added")
        # The user mentioned an enforcement term, but the model classified the
        # document as harmless without the user having been asked directly:
        # do not trust it, ask the direct question once.
        f = case.facts.get("document_type")
        if (f and f.status is Status.KNOWN and f.value not in _ESCALATING_DOCS
                and f.ask_count == 0):
            case.audit.append(
                f"detector: enforcement keyword '{hit}' but document_type='{f.value}' "
                "was never asked directly -> reset, will be asked")
            f.status, f.value, f.evidence = Status.MISSING, None, ""

    if case.consent_distress_screening:
        if hit := _find(DISTRESS, text):
            case.flags.setdefault("distress", hit)
