"""The gate: decides PROCEED, ASK or REFER from the case record.

Plain Python. No model call happens in this file. Rules are checked in a
fixed order and the first REFER rule group that fires wins; every decision
carries the identifiers of the rules that fired, so it can be audited.
Unknown values never count as safe.
"""
from __future__ import annotations

from datetime import date

from . import config
from .areas import (ALWAYS_REFER_IMMEDIATELY, FIELD_BY_NAME, REFER_AFTER_COLLECTION,
                    disclaimer_state, established, needs_confirmation, needs_detail,
                    register_objection_open, required_fields)
from .deadlines import compute_deadlines
from .legal_logic import legal_referrals
from .schema import Case, Decision, Reason, Route, Status


def gate(case: Case, today: date) -> Decision:
    case.assessed_on = today             # questions that depend on a period read this
    deadlines = compute_deadlines(case, today)
    refer: list[Reason] = []
    notices: list[Reason] = []          # urgent notices that do not end the conversation
    urgent = emergency = False
    # A consequential value that the model read from free text (for example "payment
    # order") counts only once the person confirmed it; until then it is asked.
    doc = established(case, "document_type")
    doc_pending = needs_confirmation(case, "document_type")
    payment_order = doc in config.CONTINUE_AFTER_URGENT_NOTICE

    # R0 technical failure: fail closed.
    if case.technical_failure:
        refer.append(Reason("R0-technical-failure",
                            "The extraction step failed; the case cannot be assessed safely.",
                            case.technical_failure))

    # R1 the user asks for a human.
    if "wants_human" in case.flags:
        refer.append(Reason("R1-user-wants-human", "The user asked for a human.",
                            case.flags["wants_human"]))

    # R2 signs of distress (only screened with consent).
    if "distress" in case.flags and case.consent_distress_screening:
        refer.append(Reason("R2-distress", "Signs of psychological distress.",
                            case.flags["distress"]))
        urgent = emergency = True

    # R3 areas that are never handled by the system.
    for area in sorted(case.areas.keys() & ALWAYS_REFER_IMMEDIATELY):
        refer.append(Reason("R3-area-outside-scope",
                            "The matter touches an area the system does not handle.",
                            case.areas[area]))

    # R4 a deadline is close or may have passed, and the required step is not confirmed.
    for d in deadlines:
        if d.key in ("disclaimer", "inventory", "register_objection"):
            continue                    # inheritance and register entries: handled below
        own_objection = d.key == "objection" and "register" not in d.label
        if own_objection and doc_pending:
            continue                    # first confirm that it is a payment order
        if own_objection and payment_order and d.working_days_left >= 0:
            # The person can declare the objection themselves within the period: the
            # urgent notice says how, and the conversation continues.
            continue
        if not d.action_done and d.working_days_left <= config.DEADLINE_CLOSE_WORKING_DAYS:
            state = ("may already have passed" if d.working_days_left < 0
                     else f"{d.working_days_left} working day(s) left")
            refer.append(Reason("R4-deadline-close",
                                f"{d.label} ({d.legal_basis}): earliest end {d.due.isoformat()}, "
                                f"{state}."))
            urgent = True

    # R5 fact-based triggers.
    if doc in config.URGENT_DOCUMENTS:
        # Late fees, gate 1: a letter from the debt enforcement office is the one
        # urgent case of this area.
        urgent = True
        if payment_order:
            # Urgent notice with the fixed guidance; the questions about the charges
            # continue, so that the person learns which amount to dispute.
            notices.append(Reason("U1-payment-order",
                                  "Payment order: urgent notice shown; a short official "
                                  "period is running. The conversation continues.",
                                  case.facts["document_type"].evidence))
        else:
            refer.append(Reason("R5-enforcement-office",
                                f"Letter from the debt enforcement office (document: {doc}); "
                                "a short official period may be running.",
                                case.facts["document_type"].evidence))
    if doc == "court_document":
        refer.append(Reason("R5-advanced-proceedings",
                            "Proceedings are at an advanced stage (document from a court).",
                            case.facts["document_type"].evidence))
    # Declining an inheritance (flow of 2026-11-13). A proposal made alongside the
    # answer (config.SOFT_RULES) is not repeated once the person declined it.
    # A proposal waits while an answer read from free text still needs the person's
    # confirmation, so that all reasons are put together in one proposal.
    pending = [f.name for f in required_fields(case) if needs_confirmation(case, f.name)]

    def soft(rule: str, text: str, evidence: str = "") -> None:
        if (rule not in case.declined_rules and not pending
                and all(r.rule != rule for r in refer)):
            refer.append(Reason(rule, text, evidence))

    if "inheritance_debt" in case.areas:
        period = next((d for d in deadlines if d.key == "disclaimer"), None)
        insolvency = case.fact("estate_insolvency")
        if period and not period.action_done and disclaimer_state(case) == "passed":
            # Gate 1B. Manifest insolvency: the disclaimer is presumed, nothing is urgent.
            # Otherwise (also "I do not know"): urgent notice to apply for an extension,
            # and a hand-over proposal alongside. Until it is answered, it is asked.
            if case.value("estate_insolvency") != "manifest":
                urgent = True
                if insolvency.status is not Status.MISSING:
                    notices.append(Reason("U2-disclaimer-period",
                                          "The period for disclaiming may have passed: "
                                          "urgent notice shown."))
                    soft("R4-disclaimer-passed",
                         f"Disclaimer of the inheritance (Art. 567 ZGB): earliest end "
                         f"{period.due.isoformat()}, may already have passed; the deceased "
                         "was not manifestly insolvent. An extension has to be requested "
                         "at once (Art. 576 ZGB).", insolvency.evidence)
        elif (period and not period.action_done
              and period.working_days_left <= config.DISCLAIMER_NOTICE_WORKING_DAYS):
            # The period is close: urgent notice, the conversation continues.
            urgent = True
            notices.append(Reason("U2-disclaimer-period",
                                  f"The period for disclaiming ends soon (earliest end "
                                  f"{period.due.isoformat()}): urgent notice shown."))
        # Gate 2. Acts that can be interference, or "not sure whether it counts": the
        # result says what that can mean, and the hand-over is proposed alongside.
        actions = case.fact("estate_actions")
        if (established(case, "estate_actions") in ("took", "unsure")
                or actions.status in (Status.USER_UNKNOWN, Status.UNRESOLVABLE)):
            soft("R5-estate-actions",
                 "The user dealt with the estate in a way that can be interference; the "
                 "right to disclaim may be forfeited (Art. 571 para. 2 ZGB). Whether it is "
                 "depends on the individual case.", actions.evidence)
    # Entry in the debt enforcement register (flow of 2026-11-14). The result says what
    # applies; where the way leads through a court or the supervisory authority, or the
    # entry is outside the register, the hand-over is proposed alongside.
    if "credit_record" in case.areas:
        if case.value("register_entry") == "private_agency":
            soft("R5-private-credit-agency",
                 "The entry is held by a private credit agency, which is outside what the "
                 "stored sources cover.", case.facts["register_entry"].evidence)
        if case.value("register_entry") == "enforcement":
            payment, objection = case.value("register_payment"), case.value("register_objection")
            step = case.fact("register_creditor_step")
            if register_objection_open(case):
                # The ten days for the objection are still running: urgent notice with
                # the date, and the conversation continues.
                urgent = True
                notices.append(Reason("U3-register-objection",
                                      "The period for the objection against the payment "
                                      "order behind the register entry is still running: "
                                      "urgent notice shown."))
            elif objection == "no" and case.fact("register_service_date").status is not Status.MISSING:
                reason = case.fact("register_missed_reason")
                if payment == "paid_before":
                    soft("R5-register-court",
                         "Paid before the payment order was served, no objection raised: "
                         "withdrawal by the creditor, or setting aside by the court on "
                         "documentary proof (Art. 85 SchKG).",
                         case.facts["register_objection"].evidence)
                elif payment == "not_paid" and reason.status is not Status.MISSING:
                    soft("R5-register-court",
                         "No objection raised and the period may have passed (reason given: "
                         f"{reason.value or 'not known'}): restoration (Art. 33 para. 4 "
                         "SchKG), nullity (Art. 22 SchKG) or an action under Art. 85a or 86 "
                         "SchKG.", reason.evidence)
            if step.value in ("pending", "won") and step.status is Status.KNOWN:
                soft("R5-register-court",
                     "The creditor went to court to have the objection removed "
                     f"({step.value}); the request under Art. 8a para. 3 lit. d SchKG does "
                     "not help for now.", step.evidence)
    amount = case.value("claim_amount")
    if amount is not None and amount > config.CLAIM_AMOUNT_REFER_CHF:
        refer.append(Reason("R5-high-amount",
                            f"The amount (CHF {amount:,.0f}) exceeds the threshold of "
                            f"CHF {config.CLAIM_AMOUNT_REFER_CHF:,}.",
                            case.facts["claim_amount"].evidence))

    legal_reasons, legal_urgent = legal_referrals(case)
    refer.extend(legal_reasons)
    urgent |= legal_urgent

    # R14 a part of the matter is outside what the stored sources cover. The model
    # names it (extract.py); it can only add this proposal. It waits until a pending
    # confirmation is answered, and it is not repeated once the person declined it.
    un = case.uncovered
    # An entry at a private credit agency already has its own proposal (above).
    if (un and not un.get("declined") and not pending
            and case.value("register_entry") != "private_agency"):
        refer.append(Reason("R14-not-covered",
                            f"Part of the matter is outside what the stored sources cover: "
                            f"{un['topic']}.", un["evidence"]))

    # R6 a critical fact cannot be established.
    required = required_fields(case)
    for spec in required:
        f = case.fact(spec.name)
        if spec.critical and f.status in (Status.USER_UNKNOWN, Status.UNRESOLVABLE):
            refer.append(Reason("R6-critical-fact-unresolved",
                                f"Critical fact '{spec.name}' could not be established "
                                f"({f.status.value}).", f.evidence))

    # R7 the legal area could not be identified after asking.
    if not case.areas and case.area_asks >= config.MAX_ASKS_PER_FIELD:
        refer.append(Reason("R7-area-unidentified",
                            "The legal area could not be identified."))

    # R8 repeated substantive attempts resolved nothing. R9 safety backstop.
    if case.no_progress:
        refer.append(Reason("R8-no-progress", "Two substantive attempts resolved nothing."))
    if case.rounds >= config.MAX_ROUNDS:
        refer.append(Reason("R9-round-limit",
                            f"The conversation reached {config.MAX_ROUNDS} question rounds."))

    # R10 a contradiction remains after asking twice.
    if case.contradictions and case.contradiction_asks >= config.MAX_ASKS_PER_FIELD:
        refer.append(Reason("R10-contradiction-unresolved",
                            "Contradictory statements could not be clarified.",
                            " / ".join(case.contradictions)))

    if refer:
        # Intake may terminate before a service/knowledge date is obtained.
        # Preserve urgency for a potentially running official period.
        uncertain_official_period = (
            "inheritance_debt" in case.areas
            and not any(d.key in ("disclaimer", "inventory") for d in deadlines))
        urgent |= bool(uncertain_official_period)
        return Decision(Route.REFER, refer, deadlines=deadlines, urgent=urgent,
                        emergency=emergency, assessed_on=today)

    # ---- ASK ---------------------------------------------------------------
    if not case.areas:
        return Decision(Route.ASK, [Reason("A1-area-missing", "Legal area not yet clear.")],
                        questions=["__area__"], deadlines=deadlines, assessed_on=today)
    if case.contradictions:
        return Decision(Route.ASK, [Reason("A2-contradiction", "Contradictory statements.",
                                           " / ".join(case.contradictions))],
                        questions=["__contradiction__"], deadlines=deadlines, assessed_on=today)
    missing = [s.name for s in required if case.fact(s.name).status is Status.MISSING
               or needs_confirmation(case, s.name) or needs_detail(case, s.name)]
    if missing:
        ask = missing[:config.MAX_QUESTIONS_PER_ROUND]
        return Decision(Route.ASK,
                        [Reason("A3-facts-missing", "Required facts are missing or need "
                                "confirmation: " + ", ".join(missing)), *notices],
                        questions=ask, deadlines=deadlines, urgent=urgent,
                        assessed_on=today)

    # ---- facts complete ------------------------------------------------------
    for area in sorted(case.areas.keys() & REFER_AFTER_COLLECTION):
        return Decision(Route.REFER,
                        [Reason("R12-area-always-referred",
                                f"Matters in the area '{area}' are always reviewed by a human; "
                                "the facts have been collected.", case.areas[area])],
                        deadlines=deadlines, assessed_on=today)

    return Decision(Route.PROCEED,
                    [Reason("P1-sufficient", "The prerequisites for the limited general-information branch are established and no "
                            "escalation rule fired."), *notices],
                    deadlines=deadlines, urgent=urgent, assessed_on=today)


def open_uncertainties(case: Case) -> list[str]:
    """Required facts that are not established, for briefing and answer."""
    out = []
    for spec in required_fields(case):
        f = case.fact(spec.name)
        if f.status is not Status.KNOWN:
            out.append(f"{spec.name} ({f.status.value})")
    return out


__all__ = ["gate", "open_uncertainties", "FIELD_BY_NAME"]
