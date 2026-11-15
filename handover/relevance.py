"""Which stored court decisions belong in a briefing. Plain Python, no model call.

A decision answers one narrow question. It is printed in full only if

  1. the case is in one of the decision's legal areas,
  2. the established facts raise one of its legal issues (issues.py), and
  3. the decision's own condition ("when", written by the legal team in
     sources/case_law_selection.json) is met by the established facts.

"when" is one of:

  "always"   the decision is relevant whenever its issue is raised
  "manual"   the question depends on something the system records only as free
             text; code cannot check it, so the decision is never printed in
             full and is listed as a pointer only
  a list of alternatives, e.g.
      [{"service_disputed": [true]}, {"document_received_date": ["unknown"]}]
             the condition is met if ANY alternative is met; an alternative is
             met if EVERY item named in it has one of the listed values

Items are facts from areas.py, or the derived items below (names start with
"@"). Values are the fact's own values, plus two words:

  "known"    the fact is established, whatever its value
  "unknown"  the user does not know it, or it could not be clarified

A decision on a raised issue therefore has one of four states:

  met      printed in full, with the facts that triggered it
  open     a fact the condition needs is not established yet
  not_met  an established fact shows that the question does not arise
  manual   cannot be checked by code

Decisions in the last three states are listed in one line each. Decisions whose
issue is not raised are not mentioned at all. An entry without "when" (older
form) is treated as "always"; an entry without "issues" keeps the older test on
escalation rules and facts.
"""
from __future__ import annotations

from datetime import date

from . import config
from .areas import FIELD_BY_NAME
from .deadlines import add_months
from .schema import Case, Decision, Status

MET, OPEN, NOT_MET, MANUAL, OUT = "met", "open", "not_met", "manual", "out"

# Derived items and the values each can take.
DERIVED: dict[str, tuple[str, ...]] = {
    "@objection_deadline": ("passed", "close", "running", "met"),
    "@disclaimer_deadline": ("passed", "close", "running", "met"),
    "@inventory_deadline": ("passed", "close", "running", "met"),
    # Statutory heir: knowledge of being an heir on the day of learning of the death, or not.
    "@heir_knowledge": ("same_day", "differs"),
    # Register: more than one year since service of the payment order (Art. 88 para. 2 SchKG).
    "@register_service_age": ("within_one_year", "over_one_year"),
}

DERIVED_LABELS = {
    "@objection_deadline": {"de": "Frist für den Rechtsvorschlag", "en": "Objection period"},
    "@disclaimer_deadline": {"de": "Ausschlagungsfrist", "en": "Disclaimer period"},
    "@inventory_deadline": {"de": "Frist für das öffentliche Inventar",
                            "en": "Period for the public inventory"},
    "@heir_knowledge": {"de": "Kenntnis der Erbenstellung im Verhältnis zur Kenntnis vom Tod",
                        "en": "Knowledge of being an heir compared with knowledge of the death"},
    "@register_service_age": {"de": "Zeit seit Zustellung des Zahlungsbefehls",
                              "en": "Time since service of the payment order"},
}
DERIVED_VALUE_LABELS = {
    "passed": {"de": "möglicherweise abgelaufen (vorsichtige Berechnung)",
               "en": "may have passed (cautious calculation)"},
    "close": {"de": "läuft bald ab (vorsichtige Berechnung)",
              "en": "ends soon (cautious calculation)"},
    "running": {"de": "läuft", "en": "running"},
    "met": {"de": "Schritt nach Angabe der Person erfolgt", "en": "step taken according to the person"},
    "same_day": {"de": "am selben Tag", "en": "on the same day"},
    "differs": {"de": "an einem anderen Tag", "en": "on a different day"},
    "within_one_year": {"de": "höchstens ein Jahr", "en": "one year or less"},
    "over_one_year": {"de": "mehr als ein Jahr", "en": "more than one year"},
}


def derived(case: Case, decision: Decision) -> dict[str, str]:
    """Derived items that can be computed from the established facts."""
    out: dict[str, str] = {}
    for key in ("objection", "disclaimer", "inventory"):
        ds = [d for d in decision.deadlines if d.key == key]
        if not ds:
            continue
        pending = [d for d in ds if not d.action_done]
        if not pending:
            out[f"@{key}_deadline"] = "met"
            continue
        left = min(d.working_days_left for d in pending)
        out[f"@{key}_deadline"] = ("passed" if left < 0 else
                                   "close" if left <= config.DEADLINE_CLOSE_WORKING_DAYS
                                   else "running")
    death, heir = case.value("date_learned_of_death"), case.value("heir_knowledge_date")
    if death and heir:
        out["@heir_knowledge"] = "same_day" if death == heir else "differs"
    served = case.value("register_service_date")
    today = decision.assessed_on
    if isinstance(served, date) and today:
        out["@register_service_age"] = ("over_one_year" if today > add_months(served, 12)
                                        else "within_one_year")
    return out


def _item(name: str, allowed: list, case: Case, values: dict) -> str:
    """State of one item of an alternative: MET, OPEN or NOT_MET."""
    if name.startswith("@"):
        if name not in values:
            return OPEN
        return MET if values[name] in allowed else NOT_MET
    f = case.facts.get(name)
    status = f.status if f else Status.MISSING
    if status is Status.MISSING:
        return OPEN
    if status is Status.KNOWN:
        if "known" in allowed or any(f.value == a and type(f.value) is type(a)
                                     for a in allowed if a not in ("known", "unknown")):
            return MET
        return NOT_MET
    # The user does not know it, or it could not be clarified.
    return MET if "unknown" in allowed else OPEN


def evaluate(when, case: Case, decision: Decision) -> tuple[str, list[str], list[str]]:
    """Return (state, names of the items that triggered, names of the items still missing)."""
    if when is None or when == "always":
        return MET, [], []
    if when == "manual":
        return MANUAL, [], []
    values = derived(case, decision)
    triggers: list[str] = []
    lacking: list[str] = []
    any_open = False
    for alternative in when:
        states = {name: _item(name, allowed, case, values)
                  for name, allowed in alternative.items()}
        if all(s == MET for s in states.values()):
            triggers += [n for n in states if n not in triggers]
        elif NOT_MET not in states.values():
            any_open = True
            lacking += [n for n, s in states.items() if s == OPEN and n not in lacking]
    if triggers:
        return MET, triggers, []
    if any_open:
        return OPEN, [], lacking
    return NOT_MET, [], []


def decision_state(entry: dict, case: Case, decision: Decision, raised: set,
                   fired: set) -> tuple[str, list[str], list[str]]:
    """State of one stored decision or commentary excerpt in this case."""
    if not set(entry.get("areas", [])) & set(case.areas):
        return OUT, [], []
    if entry.get("issues"):
        if not set(entry["issues"]) & raised:
            return OUT, [], []
        return evaluate(entry.get("when"), case, decision)
    # Older form: escalation rules that must have fired, facts with listed values.
    if entry.get("rules") and not set(entry["rules"]) & fired:
        return OUT, [], []
    ok = all(case.value(name) in allowed for name, allowed in (entry.get("facts") or {}).items())
    return (MET if ok else OUT), [], []


def check_when(when) -> list[str]:
    """Problems in a condition, for the tests: unknown items or impossible values."""
    if when in ("always", "manual"):
        return []
    if not isinstance(when, list) or not when:
        return ["'when' must be \"always\", \"manual\" or a non-empty list of alternatives"]
    problems = []
    for alternative in when:
        if not isinstance(alternative, dict) or not alternative:
            problems.append("each alternative must name at least one item")
            continue
        for name, allowed in alternative.items():
            if not isinstance(allowed, list) or not allowed:
                problems.append(f"{name}: the allowed values must be a non-empty list")
                continue
            if name.startswith("@"):
                if name not in DERIVED:
                    problems.append(f"{name}: unknown derived item")
                else:
                    problems += [f"{name}: impossible value {a!r}" for a in allowed
                                 if a not in DERIVED[name]]
                continue
            spec = FIELD_BY_NAME.get(name)
            if spec is None:
                problems.append(f"{name}: unknown fact")
                continue
            for a in allowed:
                if a in ("known", "unknown"):
                    continue
                if spec.kind == "bool" and not isinstance(a, bool):
                    problems.append(f"{name}: {a!r} is not true or false")
                elif spec.kind == "choice" and a not in spec.choices:
                    problems.append(f"{name}: {a!r} is not one of {spec.choices}")
                elif spec.kind not in ("bool", "choice"):
                    problems.append(f"{name}: only \"known\" or \"unknown\" can be tested "
                                    f"for a fact of kind {spec.kind}")
    return problems
