"""Turns the state of a conversation into plain data for the web page.

Nothing is decided here; this module only describes what the engine and the
gate already did, in the user's language.
"""
from __future__ import annotations

from . import texts
from .areas import AREA_LABELS, FIELD_BY_NAME, LABELS, display_value, required_fields
from .engine import Reply, Session
from .schema import Status


def decision_view(session: Session) -> dict:
    """What the gate decided and on what basis."""
    c, d = session.case, session.last_decision
    lang = c.language
    if d is None:
        return {}
    facts, open_points = [], []
    for f in c.facts.values():
        if f.name not in LABELS:
            continue
        spec = FIELD_BY_NAME.get(f.name)
        if f.status is Status.KNOWN:
            facts.append({"label": LABELS[f.name][lang],
                          "value": display_value(f.value, lang, f.name),
                          "evidence": f.evidence,
                          "critical": bool(spec and spec.critical)})
    for spec in required_fields(c):
        f = c.fact(spec.name)
        if f.status is not Status.KNOWN:
            open_points.append({"label": LABELS[spec.name][lang],
                                "status": texts.STATUS_LABELS[f.status.value][lang],
                                "critical": spec.critical})
    # A referral first waits for the user's agreement; the label says which state it is in.
    route_label = texts.ROUTE_LABELS[d.route.value][lang]
    if d.route.value == "REFER" and session.handover in texts.HANDOVER_STATE_LABELS:
        route_label = texts.HANDOVER_STATE_LABELS[session.handover][lang]
    return {
        "route": d.route.value,
        "route_label": route_label,
        "handover": session.handover,
        "urgent": d.urgent,
        "emergency": d.emergency,
        "today": session.today.strftime("%d.%m.%Y"),
        "consent": c.consent_distress_screening,
        "rounds": c.rounds,
        "areas": [AREA_LABELS.get(a, {}).get(lang, a) for a in sorted(c.areas)],
        "reasons": [{"rule": r.rule, "label": texts.rule_label(r.rule, lang),
                     # the technical wording of the rule exists in English only
                     "detail": r.text if lang == "en" else "",
                     "evidence": r.evidence} for r in d.reasons],
        "deadlines": [{"label": texts.DEADLINE_LABELS.get(x.key, {}).get(lang, x.label),
                       "basis": x.legal_basis, "due": x.due.strftime("%d.%m.%Y"),
                       "days_left": x.working_days_left, "done": x.action_done}
                      for x in d.deadlines],
        "facts": facts,
        "open": open_points,
        "contradictions": list(c.contradictions),
        "audit": list(c.audit),
    }


def reply_view(session: Session, reply: Reply) -> dict:
    """One reply of the system, for the web page."""
    return {
        "kind": reply.kind,
        "route": reply.route.value,
        "text": reply.text,
        "data": reply.data,
        "closed": session.closed,
        "language": session.case.language,
        "briefing": reply.briefing,
        "decision": decision_view(session),
    }
