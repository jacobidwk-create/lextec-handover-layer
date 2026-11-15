"""User-visible regressions for approved work packages 1 and 3 only."""
from copy import deepcopy
from datetime import date

import pytest

from handover import briefing, texts
from handover.demo import DEMO_CONTACT as PERSON
from handover.engine import Session
from handover.extract import extract
from handover.llm import FakeLLM
from handover.schema import Case, Fact, Route, Status
from handover.view import reply_view

TODAY = date(2026, 11, 11)


def empty(lang="de"):
    return {"language": lang, "areas": [], "facts": {}}


def intake(lang="de"):
    s = Session(FakeLLM([]), today=TODAY, language=lang)
    s.case.areas["debt_collection"] = "Mahnung"
    # Deliberately leave only one prerequisite unresolved (default_trigger, gate 2).
    from test_handover import DEBT_PREREQUISITES
    for name, value in {**DEBT_PREREQUISITES, "document_type": "reminder", "claim_amount": 200}.items():
        s.case.facts[name] = Fact(name, Status.KNOWN, value, "test fixture")
    s._decide_and_respond()
    return s


def urgent(lang="de", received=date(2026, 11, 4)):
    s = Session(FakeLLM([]), today=TODAY, language=lang)
    s.case.areas["debt_collection"] = "payment order"
    s.case.facts["document_type"] = Fact("document_type", Status.KNOWN, "payment_order", "payment order")
    if received:
        s.case.facts["document_received_date"] = Fact("document_received_date", Status.KNOWN, received, "04.11.2026")
    # A payment order alone gets the urgent notice and the questions continue (decision
    # of 2026-11-13). The person asks for a human, so a hand-over is proposed.
    s.case.flags["wants_human"] = "user request"
    return s


@pytest.mark.parametrize("lang", ["de", "en"])
@pytest.mark.parametrize("outcome", ["accept", "decline", "failure"])
def test_urgent_guidance_survives_every_handover_outcome(lang, outcome, monkeypatch, tmp_path):
    s = urgent(lang)
    offer = s._decide_and_respond()
    assert offer.kind == "refer_offer"
    assert len(s.llm.calls) == 0
    monkeypatch.setattr(briefing, "deliver", lambda *_, **__: (tmp_path / "briefing.md", False))
    if outcome == "failure":
        def fail(*_, **__):
            raise OSError("simulated mail failure")
        monkeypatch.setattr(briefing, "deliver", fail)
    result = s.answer_handover(outcome != "decline", contact=PERSON)
    for reply in (offer, result):
        data = reply_view(s, reply)["data"]["next_steps"]
        assert data and "14.11.2026" in reply.text and "04.11.2026" in reply.text
        assert texts.PAYMENT_RECIPIENT[lang] in reply.text
        assert texts.PAYMENT_NO_WAIT[lang] in reply.text
        assert "Art. 74" in reply.text and "#art_74" in reply.text
        assert "Wochenenden" in reply.text if lang == "de" else "weekends" in reply.text
        assert all(p in reply.text for p in data[0]["paragraphs"])
    if outcome == "failure":
        assert result.kind == "handover_error" and not s.closed
    if outcome == "decline":
        assert result.kind == "refer_declined" and not s.closed


@pytest.mark.parametrize("lang", ["de", "en"])
def test_unknown_service_date_does_not_invent_date(lang):
    s = urgent(lang, received=None)
    r = s._decide_and_respond()
    assert texts.PAYMENT_DATE_UNKNOWN[lang] in r.text
    assert "14.11.2026" not in r.text


def test_reported_objection_is_acknowledged_in_proactive_guidance():
    s = urgent()
    s.case.facts["objection_filed"] = Fact("objection_filed", Status.KNOWN, True, "schon erhoben")
    assert texts.PAYMENT_REPORTED_ACTION["de"] in s._decide_and_respond().text


def test_guidance_not_shown_for_private_reminder():
    s = intake()
    assert not s.request_human().data["next_steps"]


@pytest.mark.parametrize("lang,pause", [("de", "Moment, ich hole den Brief"), ("en", "One moment, I'm getting the letter.")])
def test_pause_preserves_questions_and_all_attempts_without_model_call(lang, pause):
    s = intake(lang)
    before = deepcopy(s.case)
    r = s.step(pause)
    assert r.route is Route.ASK and texts.PAUSE_ACK[lang] in r.text
    assert s.llm.calls == []
    assert s.case.last_asked == before.last_asked
    assert s.case.rounds == before.rounds and s.case.no_progress_rounds == 0
    assert [(f.ask_count, f.failed_attempts) for f in s.case.facts.values()] == [
        (f.ask_count, f.failed_attempts) for f in before.facts.values()]


def test_pause_with_additional_risk_content_is_processed():
    s = intake()
    s.llm = FakeLLM([empty()])
    r = s.step("Moment, ich hole den Brief. Darauf steht Strafbefehl.")
    assert len(s.llm.calls) == 1 and r.route is Route.REFER


def test_one_unusable_reply_then_answer_recovers():
    s = intake()
    s.llm = FakeLLM([empty(), {**empty(), "facts": {
        "default_trigger": {"value": "reminder", "evidence": "Ich wurde schon gemahnt"}}}])
    r = s.step("Hm.")
    assert r.route is Route.ASK and texts.CLARIFY_ACK["de"] in r.text
    assert s.case.no_progress_rounds == 1
    r = s.step("Ich wurde schon gemahnt")
    assert r.route is Route.PROCEED and s.case.no_progress_rounds == 0


def test_repeated_failed_answers_can_be_resolved_by_later_fact():
    s = intake()
    s.llm = FakeLLM([empty(), empty(), {**empty(), "facts": {
        "default_trigger": {"value": "reminder", "evidence": "Ich wurde schon gemahnt"}}}])
    assert s.step("Hm.").route is Route.ASK
    assert s.step("Das weiss ich gerade nicht zu sagen.").route is Route.REFER
    assert s.case.fact("default_trigger").status is Status.UNRESOLVABLE
    assert s.step("Ich wurde schon gemahnt").route is Route.PROCEED
    assert not s.case.no_progress


@pytest.mark.parametrize("lang", ["de", "en"])
def test_declined_human_request_can_be_withdrawn_and_stays_withdrawn(lang):
    s = intake(lang)
    s.request_human()
    declined = s.answer_handover(False)
    assert declined.data["resume_label"] == texts.RESUME_LABEL[lang]
    assert s.step(texts.RESUME_LABEL[lang]).route is Route.ASK
    assert "wants_human" not in s.case.flags
    # Model repeats the old human request. Its evidence isn't in the new message.
    s.llm = FakeLLM([{**empty(lang), "wants_human": {
        "value": True, "evidence": texts.HUMAN_BUTTON[lang]}, "facts": {
        "default_trigger": {"value": "reminder", "evidence": "had a reminder"}}}])
    assert s.step("I had a reminder before").route is Route.PROCEED
    assert "wants_human" not in s.case.flags
    assert s.request_human().kind == "refer_offer"


def test_resume_does_not_clear_legal_unknown_or_deadline():
    s = urgent()
    s.case.facts["jurisdiction"] = Fact("jurisdiction", Status.USER_UNKNOWN, None, "weiss nicht")
    s.request_human()
    s.answer_handover(False)
    r = s.recover()
    # The request for a human is withdrawn: the questions continue, the urgent notice
    # and the unknown fact stay.
    assert r.route is Route.ASK and r.decision.urgent
    assert s.case.fact("jurisdiction").status is Status.USER_UNKNOWN
    assert "wants_human" not in s.case.flags


@pytest.mark.parametrize("use_retry_button", [True, False])
def test_extraction_failure_can_recover_without_spending_answer_attempt(use_retry_button):
    s = intake()
    s.llm = FakeLLM([TimeoutError(), TimeoutError(), empty()])
    r = s.step("Hier ist noch eine Angabe.")
    assert r.route is Route.REFER and s.case.technical_failure
    assert s.case.no_progress_rounds == 0
    assert r.data["retry_label"] == texts.RETRY_LABEL["de"]
    r = s.recover(retry=True) if use_retry_button else s.step("Noch einmal bitte.")
    assert r.route is Route.ASK and not s.case.technical_failure
    assert s.case.no_progress_rounds == 0
    assert s.case.fact("claim_amount").value == 200


def test_malformed_extraction_is_transactional():
    c = Case(messages=[("user", "200 Franken")])
    original = deepcopy(c)
    malformed = {"language": "en", "facts": {"claim_amount": {"value": 200, "evidence": "200 Franken"}},
                 "user_questions": 42}
    extract(FakeLLM([malformed, malformed]), c, TODAY)
    assert c.technical_failure and c.language == original.language
    assert c.facts == original.facts and c.messages == original.messages


def test_decline_does_not_repeat_offer_until_new_reason_or_request():
    s = urgent()
    s._decide_and_respond()
    s.answer_handover(False)
    s.llm = FakeLLM([empty()])
    r = s.step("Danke.")
    assert r.kind == "refer_declined"
    assert texts.HANDOVER_QUESTION["de"] not in r.text
    assert r.data["next_steps"]
    assert s.request_human().kind == "refer_offer"
    s.answer_handover(False)
    s.case.facts["claim_amount"] = Fact("claim_amount", Status.KNOWN, 9000, "9000")
    assert s._decide_and_respond().kind == "refer_offer"


def test_server_recovery_api_uses_same_engine_transition():
    from server import App
    app = App(demo_mode=True, today=TODAY)
    result = app.start("de", False, "payment_order")
    sid = result["id"]
    app.human(sid)
    app.handover(sid, False, "")
    r = app.recover(sid, retry=False)
    assert r["kind"] == "ask" and r["decision"]["handover"] == ""


def test_web_renders_guidance_and_recovery_controls(monkeypatch, tmp_path):
    import json
    import shutil
    import subprocess
    if not shutil.which("node"):
        pytest.skip("Node.js is required for the frontend renderer test")
    monkeypatch.setattr(briefing, "deliver", lambda *_, **__: (tmp_path / "briefing.md", False))
    replies = []
    for lang in ("de", "en"):
        for accept in (True, False):
            s = urgent(lang)
            replies.append(reply_view(s, s._decide_and_respond()))
            replies.append(reply_view(s, s.answer_handover(accept, contact=PERSON)))
        s = urgent(lang)
        s._decide_and_respond()
        def fail(*_, **__):
            raise OSError("simulated failure")
        with monkeypatch.context() as patch:
            patch.setattr(briefing, "deliver", fail)
            replies.append(reply_view(s, s.answer_handover(True, contact=PERSON)))
        s = intake(lang)
        s.llm = FakeLLM([TimeoutError(), TimeoutError()])
        replies.append(reply_view(s, s.step("Please process this.")))
    result = subprocess.run(["node", "tests/web_rendering.cjs"], input=json.dumps(replies),
                            text=True, capture_output=True, check=False)
    assert result.returncode == 0, result.stderr


def test_area_resolution_clears_no_progress_blockage():
    s = Session(FakeLLM([empty(), empty(), empty(), {
        **empty(), "areas": [{"area": "debt_collection", "evidence": "Inkasso"}]}]), today=TODAY)
    s.step("Hallo")
    s.step("Hm")
    assert s.step("Hm").route is Route.REFER
    assert s.step("Es geht um Inkasso").route is Route.ASK
    assert s.case.no_progress_rounds == 0


def test_typed_renewed_human_request_reopens_offer():
    s = intake("en")
    s.llm = FakeLLM([empty("en"), empty("en")])
    assert s.step("I want to speak to a human").kind == "refer_offer"
    s.answer_handover(False)
    assert s.step("I want to speak to a human").kind == "refer_offer"


def test_referral_messages_do_not_count_as_failed_intake_answers():
    s = urgent()
    s.case.last_asked = ["debt_disputed", "claim_amount"]
    s._decide_and_respond()
    s.answer_handover(False)
    s.llm = FakeLLM([empty(), empty(), empty()])
    for _ in range(3):
        assert s.step("Danke.").kind == "refer_declined"
    assert s.case.no_progress_rounds == 0
    assert s.case.fact("default_trigger").status is Status.MISSING


def test_new_facts_after_resume_can_still_trigger_legal_referral():
    s = intake()
    s.request_human()
    s.answer_handover(False)
    s.recover()
    s.llm = FakeLLM([{**empty(), "facts": {"claim_amount": {
        "value": 9000, "evidence": "9000 Franken"}}}])
    r = s.step("Es sind 9000 Franken.")
    assert r.route is Route.REFER
    assert any(reason.rule == "R5-high-amount" for reason in r.decision.reasons)


def test_resume_reopens_attempt_exhausted_fields_but_not_unknown_fields():
    s = intake()
    s.case.fact("default_trigger").status = Status.UNRESOLVABLE
    s.case.fact("principal_status").status = Status.USER_UNKNOWN
    s.case.no_progress_rounds = 2
    s._decide_and_respond()
    s.recover()
    assert s.case.fact("default_trigger").status is Status.MISSING
    assert s.case.fact("principal_status").status is Status.USER_UNKNOWN
    assert not s.case.no_progress
    assert s.last_decision.route is Route.REFER
