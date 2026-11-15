"""Reviewed procedural information, independent of agreement to a referral.

No merits assessment or new deadline arithmetic. The existing screening date
is explicitly provisional; the broader deadline redesign is deferred.
"""
from . import knowledge, texts
from .areas import established
from .schema import Case, Decision, Route


def next_steps(case: Case, decision: Decision) -> list[dict]:
    """The urgent notices that fit the case: a payment order, a disclaimer period that is
    close or may have passed, and an objection that is still possible against the
    enforcement behind a register entry."""
    return (_payment_order(case, decision) + _disclaimer(case, decision)
            + _register_objection(case, decision))


def _register_objection(case: Case, decision: Decision) -> list[dict]:
    """Register entries: no objection was raised and the ten days are still running."""
    period = next((d for d in decision.deadlines if d.key == "register_objection"), None)
    if period is None:
        return []
    lang = case.language
    term = knowledge.answer("term_rechtsvorschlag", lang)
    paragraphs = [term["text"],
                  texts.PAYMENT_DATE[lang].format(
                      received=case.value("register_service_date").strftime("%d.%m.%Y"),
                      due=period.due.strftime("%d.%m.%Y")),
                  texts.REGISTER_OBJECTION_WHY[lang], texts.PAYMENT_RECIPIENT[lang],
                  texts.PAYMENT_NO_WAIT[lang]]
    return [{"title": texts.REGISTER_NEXT_TITLE[lang], "paragraphs": paragraphs,
             "citation": term["citation"], "url": term["url"]}]


def _disclaimer(case: Case, decision: Decision) -> list[dict]:
    from . import config
    from .areas import disclaimer_state, inheritance_start
    period = next((d for d in decision.deadlines if d.key == "disclaimer"), None)
    if not decision.urgent or period is None or period.action_done:
        return []
    passed = disclaimer_state(case) == "passed"
    if passed and case.value("estate_insolvency") == "manifest":
        return []                               # presumed disclaimer: nothing is urgent
    if not passed and period.working_days_left > config.DISCLAIMER_NOTICE_WORKING_DAYS:
        return []
    lang = case.language
    term = knowledge.answer("term_fristverlaengerung" if passed else "term_ausschlagung", lang)
    paragraphs = [term["text"],
                  texts.ESTATE_DATE[lang].format(start=inheritance_start(case).strftime("%d.%m.%Y"),
                                                 due=period.due.strftime("%d.%m.%Y"))]
    if passed:
        paragraphs.append(texts.ESTATE_PASSED[lang])
    paragraphs += [texts.ESTATE_WHERE[lang], texts.ESTATE_NO_WAIT[lang]]
    if decision.route is not Route.REFER:
        paragraphs.append(texts.ESTATE_CONTINUE[lang])
    return [{"title": texts.ESTATE_NEXT_TITLE[lang], "paragraphs": paragraphs,
             "citation": term["citation"], "url": term["url"]}]


def _payment_order(case: Case, decision: Decision) -> list[dict]:
    if not decision.urgent or established(case, "document_type") != "payment_order":
        return []
    objection = [d for d in decision.deadlines if d.key == "objection"]
    deadlines = [d for d in objection if not d.action_done]
    if objection and not deadlines:
        return []
    lang = case.language
    term = knowledge.answer("term_rechtsvorschlag", lang)
    paragraphs = [term["text"]]
    received = case.value("document_received_date")
    if received and deadlines:
        paragraphs.append(texts.PAYMENT_DATE[lang].format(
            received=received.strftime("%d.%m.%Y"), due=deadlines[0].due.strftime("%d.%m.%Y")))
    else:
        paragraphs.append(texts.PAYMENT_DATE_UNKNOWN[lang])
    if case.value("objection_filed") is True:
        paragraphs.append(texts.PAYMENT_REPORTED_ACTION[lang])
    paragraphs += [texts.PAYMENT_PARTIAL_OBJECTION[lang], texts.PAYMENT_OFFICIAL_COSTS[lang],
                   texts.PAYMENT_RECIPIENT[lang], texts.PAYMENT_NO_WAIT[lang]]
    if decision.route is not Route.REFER:
        paragraphs.append(texts.PAYMENT_CONTINUE[lang])
    return [{"title": texts.PAYMENT_NEXT_TITLE[lang], "paragraphs": paragraphs,
             "citation": term["citation"], "url": term["url"]}]


def render_next_steps(items: list[dict]) -> str:
    return "\n\n".join("\n\n".join([item["title"], *item["paragraphs"],
                                     f"{item['citation']}: {item['url']}"])
                       for item in items)
