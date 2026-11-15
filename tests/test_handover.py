"""Tests. Run with: python -m pytest -q   (no API key or network needed)"""
import os
import tempfile
from datetime import date

from handover import config
from handover.demo import DEMO_CONTACT as PERSON
from handover.answer import check_citations, classify
from handover.deadlines import add_months, working_days_left
from handover.engine import Session
from handover.llm import FakeLLM
from handover.schema import Route, Status

config.OUTBOX_DIR = tempfile.mkdtemp()
TODAY = date(2026, 11, 11)  # a Wednesday


def fact(value, evidence):
    return {"value": value, "evidence": evidence}


def run(messages, answers, consent=False, today=TODAY, lang="de", answerer=None, prerequisites=None):
    if prerequisites:
        import copy
        answers = copy.deepcopy(answers)
        messages = list(messages)
        for name, value in prerequisites.items():
            statement = f"{name}: {value}."
            messages[0] += " " + statement
            answers[0].setdefault("facts", {})[name] = fact(value, statement)
    s = Session(FakeLLM(answers), consent_distress_screening=consent, today=today,
                language=lang, answerer=answerer)
    replies = [s.step(m) for m in messages]
    return s, replies


# Late fees: every answer of the three gates except default_trigger (gate 2), so that
# a test can leave exactly one question open.
DEBT_PREREQUISITES = dict(principal_status="open", interest_charge="statutory",
                          reminder_fee="not_agreed", collection_costs="flat")
GATE_2 = {"language": "de", "areas": [],
          "facts": {"default_trigger": {"value": "reminder",
                                        "evidence": "Ich wurde schon gemahnt"}}}

# ---- deadlines ---------------------------------------------------------------

def test_working_days_skip_weekend():
    assert working_days_left(date(2026, 11, 11), date(2026, 11, 13)) == 2   # Thu, Fri
    assert working_days_left(date(2026, 11, 13), date(2026, 11, 16)) == 1   # Fri -> Mon
    assert working_days_left(date(2026, 11, 11), date(2026, 11, 11)) == 0
    assert working_days_left(date(2026, 11, 11), date(2026, 11, 10)) == -1


def test_working_days_skip_holiday():
    # 25 Dec 2026 is a Friday and a holiday
    assert working_days_left(date(2026, 12, 23), date(2026, 12, 28)) == 2   # Thu 24, Mon 28


def test_add_months_clamps():
    assert add_months(date(2026, 11, 30), 3) == date(2027, 2, 28)


# ---- gate: debt collection ---------------------------------------------------

def test_reminder_missing_facts_then_proceed():
    m1 = "Ich habe eine Mahnung von einem Inkassobüro über 480 Franken bekommen."
    m2 = "Ich wurde schon gemahnt."
    s, r = run(prerequisites=DEBT_PREREQUISITES, messages=[m1, m2], answers=[
        {"language": "de", "areas": [{"area": "debt_collection", "evidence": "Inkassobüro"}],
         "facts": {"document_type": fact("reminder", "Mahnung von einem Inkassobüro"),
                   "claim_amount": fact(480, "480 Franken")}},
        GATE_2,
    ])
    assert r[0].route is Route.ASK and r[0].decision.questions == ["default_trigger"]
    assert r[1].route is Route.PROCEED


def test_payment_order_close_deadline_refers_urgent():
    m = "Ich habe am 03.11.2026 einen Zahlungsbefehl erhalten."
    s, r = run([m], [
        {"language": "de", "areas": [{"area": "debt_collection", "evidence": "Zahlungsbefehl"}],
         "facts": {"document_type": fact("payment_order", "einen Zahlungsbefehl erhalten"),
                   "document_received_date": fact("2026-11-03", "am 03.11.2026")}},
    ])
    # The model read "Zahlungsbefehl" from free text: the sender is confirmed first, and
    # nothing is urgent yet.
    assert r[0].route is Route.ASK and not r[0].decision.urgent
    q = r[0].data["questions"][0]
    assert q["name"] == "document_type" and q["understood"] == "payment_order"
    # Confirmed: urgent notice with the date (due 13 Nov), and the questions continue.
    r1 = s.answer_form({"document_type": "payment_order"})
    assert r1.route is Route.ASK and r1.decision.urgent
    assert any(x.rule == "U1-payment-order" for x in r1.decision.reasons)
    assert "13.11.2026" in r1.data["next_steps"][0]["paragraphs"][1]
    # A hand-over is proposed when the person asks for it, not carried out before a yes.
    offer = s.request_human()
    assert offer.kind == "refer_offer" and offer.briefing_path is None and not s.closed
    assert offer.data["conditions"] and "CHF 45" in offer.text
    # A yes without first name, surname and e-mail address passes nothing on.
    early = s.answer_handover(True, contact={"first_name": "Anna", "email": "anna@"})
    assert early.kind == "handover_contact" and not s.closed and s.handover == "offered"
    assert early.data["contact"]["missing"] == ["last_name", "email"]
    assert early.data["next_steps"] and "13.11.2026" in early.text     # urgent notice stays
    assert not os.listdir(config.OUTBOX_DIR) or all("Anna" not in open(os.path.join(
        config.OUTBOX_DIR, f)).read() for f in os.listdir(config.OUTBOX_DIR))
    done = s.answer_handover(True, contact={**PERSON, "phone": "079 000 00 00"})
    assert done.kind == "refer" and s.closed and done.briefing_path.exists()
    doc = done.briefing_path.read_text()
    assert "DRINGEND" in doc and "Zustimmung zur Übergabe" in doc and "079 000 00 00" in doc
    assert "**Name:** Max Muster" in doc and "**E-Mail:** max.muster@example.org" in doc
    # The case number is shown to the person and stands in the briefing and its file name.
    number = done.data["case_number"]
    assert number.startswith("LX-20261111-") and len(number) == 16
    assert number in done.text and f"Fallnummer: {number}" in doc
    assert number in done.briefing_path.name and "_P1_" in done.briefing_path.name
    assert "info@lextec.ch" in done.data["case_number_note"]
    assert "**Priorität:** Klasse 1 – dringend und wichtig" in doc
    assert "13.11.2026" in doc and "Art. 74 SchKG" in doc


def test_payment_order_bare_objection_no_longer_proceeds():
    m = "Zahlungsbefehl am 03.11.2026 erhalten, Rechtsvorschlag habe ich schon erhoben. " \
        "Ich bestreite alles, es geht um 300 Franken."
    s, r = run([m], [
        {"language": "de", "areas": [{"area": "debt_collection", "evidence": "Zahlungsbefehl"}],
         "facts": {"document_type": fact("payment_order", "Zahlungsbefehl am 03.11.2026 erhalten"),
                   "document_received_date": fact("2026-11-03", "am 03.11.2026"),
                   "objection_filed": fact(True, "Rechtsvorschlag habe ich schon erhoben"),
                   "claim_amount": fact(300, "300 Franken")}},
    ])
    r1 = s.answer_form({"document_type": "payment_order"})      # confirm the sender
    # A bare "I objected" does not switch the urgent notice off; the questions continue.
    assert r1.route is Route.ASK and r1.decision.urgent
    from handover import texts
    assert texts.PAYMENT_REPORTED_ACTION["de"] in r1.text


def test_detector_overrides_model_that_calls_payment_order_a_reminder():
    m = "Ich habe einen Zahlungsbefehl bekommen, wegen 200 Franken, ich bestreite alles."
    s, r = run([m], [
        {"language": "de", "areas": [{"area": "debt_collection", "evidence": "200 Franken"}],
         "facts": {"document_type": fact("reminder", "Zahlungsbefehl bekommen"),
                   "claim_amount": fact(200, "200 Franken")}},
    ])
    # the model said "reminder", the detector saw "Zahlungsbefehl": ask directly
    assert r[0].route is Route.ASK and "document_type" in r[0].decision.questions


def test_high_amount_refers():
    m = "Mahnung über 12000 Franken, ich bestreite alles."
    s, r = run([m], [
        {"language": "de", "areas": [{"area": "debt_collection", "evidence": "Mahnung"}],
         "facts": {"document_type": fact("reminder", "Mahnung"),
                   "claim_amount": fact(12000, "12000 Franken")}},
    ])
    assert r[0].route is Route.REFER
    assert any(x.rule == "R5-high-amount" for x in r[0].decision.reasons)


# ---- evidence check ----------------------------------------------------------

def test_fact_without_verbatim_evidence_is_discarded():
    m = "Ich habe Post von einem Inkassobüro bekommen."
    s, r = run([m], [
        {"language": "de", "areas": [{"area": "debt_collection", "evidence": "Inkassobüro"}],
         "facts": {"document_type": fact("reminder", "Mahnung erhalten"),      # not in text
                   "objection_filed": fact(True, "Rechtsvorschlag erhoben")}},  # invented
    ])
    assert s.case.fact("document_type").status is Status.MISSING
    assert s.case.fact("objection_filed").status is Status.MISSING
    assert r[0].route is Route.ASK


def test_date_not_matching_quote_is_discarded():
    m = "Zahlungsbefehl am 03.11.2026 erhalten."
    s, _ = run([m], [
        {"language": "de", "areas": [{"area": "debt_collection", "evidence": "Zahlungsbefehl"}],
         "facts": {"document_type": fact("payment_order", "Zahlungsbefehl"),
                   "document_received_date": fact("2026-10-03", "am 03.11.2026")}},
    ])
    assert s.case.fact("document_received_date").status is Status.MISSING


# ---- inheritance -------------------------------------------------------------

INH = {"area": "inheritance_debt", "evidence": "Vater ist gestorben"}


STATUTORY = {"heir_basis": fact("statutory", "Ein Testament gibt es nicht")}


def test_inheritance_estate_actions_refers():
    m = "Mein Vater ist gestorben, ich habe es am 01.11.2026 erfahren. Ein Testament gibt es " \
        "nicht. Ich habe schon seine Möbel verkauft."
    s, r = run([m], [
        {"language": "de", "areas": [INH],
         "facts": {**STATUTORY,
                   "date_learned_of_death": fact("2026-11-01", "am 01.11.2026 erfahren"),
                   "estate_actions": fact("took", "seine Möbel verkauft")}},
    ])
    # Read from free text: the person confirms it first, then the hand-over is proposed.
    assert r[0].route is Route.ASK and r[0].data["questions"][0]["understood"] == "took"
    offer = s.answer_form({"estate_actions": "took"})
    assert offer.route is Route.REFER and not offer.decision.urgent
    assert any(x.rule == "R5-estate-actions" for x in offer.decision.reasons)


def test_inheritance_user_does_not_know_critical_fact_refers():
    m1 = "Mein Vater ist gestorben und hatte Schulden. Ein Testament gibt es nicht."
    m2 = "Das weiss ich nicht mehr genau."
    s, r = run([m1, m2], [
        {"language": "de", "areas": [INH], "facts": STATUTORY},
        {"language": "de", "areas": [],
         "facts": {"date_learned_of_death": {"value": None, "user_does_not_know": True,
                                             "evidence": "Das weiss ich nicht mehr genau"}}},
    ])
    assert r[0].route is Route.ASK and r[0].decision.questions == ["date_learned_of_death"]
    assert r[1].route is Route.REFER
    assert any(x.rule == "R6-critical-fact-unresolved" for x in r[1].decision.reasons)


def test_inheritance_complete_answers_give_the_fixed_result_with_the_deadline():
    m = "Mein Vater ist gestorben, erfahren am 01.11.2026. Ein Testament gibt es nicht. " \
        "Nichts angerührt. Er hatte nur Schulden."
    s, r = run([m], [
        {"language": "de", "areas": [INH],
         "facts": {**STATUTORY,
                   "date_learned_of_death": fact("2026-11-01", "erfahren am 01.11.2026"),
                   "estate_actions": fact("none", "Nichts angerührt"),
                   "estate_finances": fact("overindebted", "Er hatte nur Schulden")}},
    ])
    assert r[0].route is Route.PROCEED
    assert r[0].decision.deadlines[0].due == date(2027, 2, 1)


# ---- other routes ------------------------------------------------------------

def test_mixed_areas_ask_for_both():
    m = "Mein Vater ist gestorben und jetzt schickt mir ein Inkassobüro seine Rechnung."
    s, r = run([m], [
        {"language": "de", "areas": [INH, {"area": "debt_collection", "evidence": "Inkassobüro"}],
         "facts": {}},
    ])
    assert r[0].route is Route.ASK
    assert set(s.case.areas) == {"inheritance_debt", "debt_collection"}
    # critical facts of both areas come first
    assert set(r[0].decision.questions) <= {"document_type", "heir_basis"}


def test_hard_area_keyword_refers_even_if_model_misses_it():
    m = "Ich habe einen Strafbefehl bekommen und kann die Busse nicht zahlen."
    s, r = run([m], [{"language": "de", "areas": [], "facts": {}}])
    assert r[0].route is Route.REFER
    assert any(x.rule == "R3-area-outside-scope" for x in r[0].decision.reasons)


def test_user_asks_for_human():
    s, r = run(["I want to speak to a lawyer about a bill."],
               [{"language": "en", "areas": [], "facts": {}}], lang="en")
    assert r[0].route is Route.REFER
    assert any(x.rule == "R1-user-wants-human" for x in r[0].decision.reasons)


def test_seizure_and_subsistence_minimum_are_handed_over_like_any_topic_outside_the_fields():
    # The field was removed on 2026-11-14: the system has no flow for it, so it belongs
    # to the topics that are proposed for hand-over at once (rule R3), without questions.
    m1 = "Mein Lohn wird gepfändet und es bleibt mir zu wenig zum Leben."
    s, r = run([m1], [
        {"language": "de", "areas": [{"area": "other", "evidence": "gepfändet"}], "facts": {}},
    ])
    assert r[0].route is Route.REFER and r[0].kind == "refer_offer"
    assert [x.rule for x in r[0].decision.reasons] == ["R3-area-outside-scope"]
    from handover.areas import AREAS, FIELD_BY_NAME
    assert "subsistence_minimum" not in AREAS and "Existenzminimum" in AREAS["other"]
    assert not [n for n in FIELD_BY_NAME if "seizure" in n or "subsistence" in n]


def test_clarification_question_does_not_count_as_failed_answer():
    m1 = "Ich habe eine Mahnung von einem Inkassobüro bekommen, 100 Franken."
    s, r = run([m1, "Warum fragen Sie das?"], [
        {"language": "de", "areas": [{"area": "debt_collection", "evidence": "Inkassobüro"}],
         "facts": {"document_type": fact("reminder", "Mahnung"),
                   "claim_amount": fact(100, "100 Franken")}},
        {"language": "de", "areas": [], "facts": {}},
    ])
    assert r[1].route is Route.ASK
    assert s.case.no_progress_rounds == 0
    assert r[1].data["answers"][0]["topic"] == "question_help"


def test_model_failure_fails_closed():
    s, r = run(["Hallo"], [RuntimeError("api down"), RuntimeError("api down")])
    assert r[0].route is Route.REFER
    assert any(x.rule == "R0-technical-failure" for x in r[0].decision.reasons)


# ---- distress screening and consent ------------------------------------------

DISTRESS_MSG = "Ich habe eine Mahnung bekommen und sehe keinen Ausweg mehr."
DISTRESS_OUT = {"language": "de",
                "areas": [{"area": "debt_collection", "evidence": "Mahnung"}],
                "facts": {"document_type": fact("reminder", "Mahnung")},
                "distress": {"value": True, "evidence": "sehe keinen Ausweg mehr"}}


def test_distress_with_consent_refers_with_emergency_info():
    s, r = run([DISTRESS_MSG], [DISTRESS_OUT], consent=True)
    assert r[0].route is Route.REFER and r[0].decision.emergency
    assert "143" in r[0].text


def test_distress_without_consent_is_not_screened():
    s, r = run([DISTRESS_MSG], [DISTRESS_OUT], consent=False)
    assert "distress" not in s.case.flags
    assert r[0].route is Route.ASK
    # the model is not even asked for it
    assert "distress" not in s.llm.calls[0][0]


# ---- citation check ----------------------------------------------------------

CORPUS = {"schkg-74": {"citation": "Art. 74 SchKG", "url": "https://example.invalid",
                       "areas": ["debt_collection"],
                       "text": "Dies ist ein Platzhaltertext nur für den Test des Zitatprüfers."}}


def test_citation_check_drops_bad_quotes_and_unsupported_statements():
    audit = []
    llm = FakeLLM([{"results": [{"index": 0, "supported": True, "relevant": True},
                                {"index": 1, "supported": False}]}])
    kept = check_citations([
        {"text": "A", "source_id": "schkg-74", "quote": "Platzhaltertext nur für den Test"},
        {"text": "B", "source_id": "schkg-74", "quote": "nur für den Test des Zitatprüfers"},
        {"text": "C", "source_id": "schkg-74", "quote": "dieser Satz steht nicht in der Quelle"},
        {"text": "D", "source_id": "or-999", "quote": "Platzhaltertext nur für den Test"},
    ], CORPUS, llm, audit)
    assert [s["text"] for s in kept] == ["A"]
    assert len(audit) == 3


def test_classify_without_corpus_makes_no_legal_statement():
    from handover.schema import Case, Decision
    case = Case(areas={"credit_record": "Betreibungsregister"})
    llm = FakeLLM([])                       # any model call would raise
    text = classify(case, Decision(Route.PROCEED, []), llm, corpus={})
    assert "keine geprüften Quellen" in text and llm.calls == []


def test_late_fee_result_is_fixed_text_and_needs_no_model_call_or_corpus():
    m = "Mahnung von einem Inkassobüro über 480 Franken. Ich wurde schon gemahnt."
    s, r = run(prerequisites=DEBT_PREREQUISITES, messages=[m], answers=[
        {"language": "de", "areas": [{"area": "debt_collection", "evidence": "Inkassobüro"}],
         "facts": {"document_type": fact("reminder", "Mahnung"),
                   "claim_amount": fact(480, "480 Franken"),
                   "default_trigger": fact("reminder", "Ich wurde schon gemahnt")}},
    ], answerer=lambda c, d, l: classify(c, d, l, corpus={}))
    assert r[0].route is Route.PROCEED and len(s.llm.calls) == 1      # extraction only
    assert "keine geprüften Quellen" not in r[0].text
    assert "Mahngebühren: Nicht geschuldet" in r[0].text
    assert "Verzugszins: Geschuldet" in r[0].text and "#art_104" in r[0].text


# ---- evaluation harness ------------------------------------------------------

def test_evaluation_harness_runs_example_scenario():
    import evaluate
    sc = evaluate.load("example")[0]
    ev = lambda v, e: {"value": v, "evidence": e}
    llm = FakeLLM([
        # extraction 1: area only
        {"language": "de", "areas": [{"area": "debt_collection", "evidence": "Handyrechnung"}],
         "facts": {}},
        # simulated user
        {"reply": "Es ist ein Zahlungsbefehl vom Betreibungsamt, bekommen am 28.10.2026."},
        # extraction 2
        {"language": "de", "areas": [],
         "facts": {"document_type": ev("payment_order", "Zahlungsbefehl vom Betreibungsamt"),
                   "document_received_date": ev("2026-10-28", "am 28.10.2026")}},
    ])
    rows = evaluate.evaluate(llm, [sc], runs=1)
    assert rows[0]["route_ok"] and rows[0]["deadline_ok"] and not rows[0]["missed_escalation"]
    assert "1/1" in evaluate.report(rows)


# ---- user experience ---------------------------------------------------------

REMINDER_1 = {"language": "de",
              "areas": [{"area": "debt_collection", "evidence": "Inkassobüro"}],
              "facts": {"document_type": fact("reminder", "Mahnung"),
                        "claim_amount": fact(480, "480 Franken")}}
REMINDER_MSG = "Ich habe eine Mahnung von einem Inkassobüro über 480 Franken bekommen."


def test_questions_come_with_an_explanation():
    s, r = run([REMINDER_MSG], [REMINDER_1])
    assert "Warum ich das frage:" in r[0].text and len(r[0].data["questions"]) <= 3


def test_model_reply_with_legal_content_outside_a_citation_is_replaced():
    draft = {"segments": [{"type": "talk",
                           "text": "Keine Sorge, die Gebühren müssen Sie nicht zahlen."}]}
    s = Session(FakeLLM([REMINDER_1, draft]), today=TODAY, compose=True)
    text = s.step(REMINDER_MSG).text
    assert "Keine Sorge" not in text and text.startswith("Danke für Ihre Angaben.")


def test_harmless_model_reply_is_used():
    draft = {"segments": [{"type": "talk", "text": "Das klingt nach einer belastenden Situation."}]}
    check = {"results": [{"index": 0, "legal_claim": False}]}
    s = Session(FakeLLM([REMINDER_1, draft, check]), today=TODAY, compose=True)
    assert s.step(REMINDER_MSG).text.startswith("Das klingt nach einer belastenden Situation.")


def test_referral_message_explains_the_reason():
    s, r = run(["Mahnung über 12000 Franken."], [
        {"language": "de", "areas": [{"area": "debt_collection", "evidence": "Mahnung"}],
         "facts": {"document_type": fact("reminder", "Mahnung"),
                   "claim_amount": fact(12000, "12000 Franken")}}])
    assert "Der Grund dafür:" in r[0].text and "Bei diesem Betrag" in r[0].text
    assert "So arbeitet LexTec" in r[0].text


def test_conversation_continues_after_proceed_and_user_can_ask_for_human():
    empty = {"language": "de", "areas": [], "facts": {}}
    s, r = run(prerequisites=DEBT_PREREQUISITES, messages=[REMINDER_MSG, "Ich wurde schon gemahnt.", "Danke.",
                "Ich möchte mit einem Anwalt sprechen."],
               answers=[REMINDER_1, GATE_2, empty, empty],
               answerer=lambda c, d, l: classify(c, d, l, corpus={}))
    assert [x.route for x in r] == [Route.ASK, Route.PROCEED, Route.PROCEED, Route.REFER]
    assert "Absender des Schreibens: Von einem Unternehmen oder einem Inkassobüro" in r[1].text
    assert "Mehr als die allgemeine Einordnung" in r[2].text            # no repeat
    # A typed wish for a human is confirmed before anything is passed on.
    assert r[3].kind == "refer_offer" and not s.closed
    # The typed yes still needs name and e-mail address; nothing is sent before.
    assert s.step("Ja, bitte.").kind == "handover_contact" and not s.closed
    assert s.answer_handover(True, contact=PERSON).kind == "refer" and s.closed


# ---- case law and commentary -------------------------------------------------

def test_briefing_lists_sources_for_the_rule_that_fired():
    from handover import briefing
    from handover.rules import gate
    m = "Mein Vater ist gestorben, erfahren am 01.11.2026. Ein Testament gibt es nicht. " \
        "Ich habe seine Möbel verkauft."
    s, r = run([m], [{"language": "de", "areas": [INH], "facts": {
        **STATUTORY,
        "date_learned_of_death": fact("2026-11-01", "erfahren am 01.11.2026"),
        "estate_actions": fact("took", "seine Möbel verkauft")}}])
    r = [s.answer_form({"estate_actions": "took"})]            # confirm; now R5 fires
    corpus = {
        "zgb-571": {"citation": "Art. 571 ZGB", "url": "u", "areas": ["inheritance_debt"],
                    "text": "Gesetzestext"},
        "dec-1": {"type": "decision", "citation": "BGE X", "url": "u", "use": ["briefing"],
                  "areas": ["inheritance_debt"], "rules": ["R5-estate-actions"],
                  "holding": "Zusammenfassung", "selected_by": "L", "text": "Erwägung"},
        "dec-2": {"type": "decision", "citation": "BGE Y", "url": "u", "use": ["briefing"],
                  "areas": ["debt_collection"], "rules": ["R4-deadline-close"], "text": "Anderes"},
        "com-1": {"type": "commentary", "citation": "Kommentar N 5", "use": ["briefing"],
                  "areas": ["inheritance_debt"], "rules": [], "text": "Lehre"},
    }
    doc = briefing.render(s.case, r[0].decision, TODAY, corpus=corpus)
    assert "Art. 571 ZGB" in doc and "BGE X" in doc and "Kommentar N 5" in doc
    assert "BGE Y" not in doc


def test_commentary_and_unreleased_decisions_never_reach_the_user():
    from handover.answer import usable_for_user
    assert usable_for_user({"citation": "Art. 74 SchKG"})
    assert not usable_for_user({"type": "decision", "use": ["briefing"]})
    assert usable_for_user({"type": "decision", "use": ["briefing", "user"]})
    assert not usable_for_user({"type": "commentary", "use": ["briefing", "user"]})


def test_case_law_passage_must_appear_word_for_word():
    import importlib.util, pathlib
    spec = importlib.util.spec_from_file_location(
        "verify_case_law", pathlib.Path(__file__).parent.parent / "tools" / "verify_case_law.py")
    v = importlib.util.module_from_spec(spec); spec.loader.exec_module(v)
    page = "<html><body><p>Das Gericht hält fest, dass die blosse Verwaltung der " \
           "Erb&shy;schaft keine Einmischung darstellt.</p></body></html>"
    entry = {"id": "x", "citation": "BGE X", "url": "u", "areas": ["inheritance_debt"],
             "selected_by": "L",
             "passage": "dass die blosse Verwaltung der Erbschaft keine Einmischung darstellt"}
    assert v.verify_entry(entry, fetcher=lambda u: page) == (True, "ok")
    entry["passage"] = "dass die blosse Verwaltung der Erbschaft stets eine Einmischung darstellt"
    assert v.verify_entry(entry, fetcher=lambda u: page)[0] is False


def _load_verifier():
    import importlib.util, pathlib
    spec = importlib.util.spec_from_file_location(
        "verify_case_law", pathlib.Path(__file__).parent.parent / "tools" / "verify_case_law.py")
    v = importlib.util.module_from_spec(spec); spec.loader.exec_module(v)
    return v


def _tiny_pdf(lines):
    """A one-page PDF file with the given lines of text."""
    content = "BT /F1 12 Tf 72 720 Td " + " ".join(f"({l}) Tj 0 -16 Td" for l in lines) + " ET"
    objs = ["<< /Type /Catalog /Pages 2 0 R >>",
            "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R "
            "/Resources << /Font << /F1 5 0 R >> >> >>",
            f"<< /Length {len(content)} >>\nstream\n{content}\nendstream",
            "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]
    out, offsets = b"%PDF-1.4\n", []
    for i, o in enumerate(objs, 1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n{o}\nendobj\n".encode("latin-1")
    xref = len(out)
    out += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode()
    out += b"".join(f"{o:010d} 00000 n \n".encode() for o in offsets)
    out += f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    return out


def test_case_law_passage_is_found_in_a_pdf_decision():
    # Cantonal courts publish decisions as PDF. A word split at the end of a line
    # ("Verwal-" / "tungshandlung") must not prevent the match; a changed word must.
    v = _load_verifier()
    pdf = _tiny_pdf(["Die Bezahlung faelliger Schulden kann nicht generell als blosse Verwal-",
                     "tungshandlung angesehen werden. Es ist im Einzelfall zu entscheiden."])
    entry = {"id": "x", "citation": "OGer X", "url": "u", "areas": ["inheritance_debt"],
             "selected_by": "L",
             "passage": "kann nicht generell als blosse Verwaltungshandlung angesehen werden"}
    assert v.verify_entry(entry, fetcher=lambda u: pdf) == (True, "ok")
    entry["passage"] = "kann generell als blosse Verwaltungshandlung angesehen werden"
    assert v.verify_entry(entry, fetcher=lambda u: pdf)[0] is False
    # A PDF without readable text (for example a scan) is rejected, not accepted.
    assert v.verify_entry(entry, fetcher=lambda u: _tiny_pdf([]))[0] is False


def test_decision_is_listed_only_for_its_area_rule_and_facts():
    from handover import briefing
    # Inheritance case in which rule R5 fires (the heir sold estate items).
    m = "Mein Vater ist gestorben, das habe ich am 14.10.2026 erfahren. Ein Testament gibt es " \
        "nicht. Ich habe seine Möbel verkauft."
    s, r = run([m], [{"language": "de", "areas": [INH], "facts": {
        **STATUTORY,
        "date_learned_of_death": fact("2026-10-14", "am 14.10.2026 erfahren"),
        "estate_actions": fact("took", "seine Möbel verkauft")}}])
    r = [s.answer_form({"estate_actions": "took"})]
    fired = {x.rule for x in r[0].decision.reasons}
    assert fired == {"R5-estate-actions"}
    dec = lambda **kw: {"type": "decision", "url": "u", "use": ["briefing"], "text": "t", **kw}
    corpus = {
        # same rule, other legal area: must stay out
        "other-area": dec(citation="BGE OBJECTION", areas=["debt_collection"],
                          rules=["R5-estate-actions"]),
        "same-area": dec(citation="BGE DISCLAIMER", areas=["inheritance_debt"],
                         rules=["R5-estate-actions"]),
        # right area, but the rule did not fire
        "other-rule": dec(citation="BGE ESTATE", areas=["inheritance_debt"],
                          rules=["R4-deadline-close"]),
        # right area, fact condition not met (nothing is known about a disclaimer)
        "fact-unmet": dec(citation="BGE RECORD", areas=["inheritance_debt"], rules=[],
                          facts={"disclaimer_filed": [True]}),
        "no-condition": dec(citation="BGE GENERAL", areas=["inheritance_debt"], rules=[]),
    }
    listed = {e["citation"] for e in briefing.relevant_sources(s.case, r[0].decision, corpus)}
    assert listed == {"BGE DISCLAIMER", "BGE GENERAL"}

    # Fact condition met: a payment-order decision appears once the document is a payment order.
    m = "Ich habe am 09.11.2026 einen Zahlungsbefehl erhalten."
    debt = {"area": "debt_collection", "evidence": "einen Zahlungsbefehl erhalten"}
    s, r = run([m], [{"language": "de", "areas": [debt], "facts": {
        "document_type": fact("payment_order", "einen Zahlungsbefehl erhalten"),
        "document_received_date": fact("2026-11-09", "am 09.11.2026")}}])
    corpus = {"po": dec(citation="BGE PO", areas=["debt_collection"], rules=[],
                        facts={"document_type": ["payment_order"]}),
              "fees": dec(citation="BGE FEES", areas=["debt_collection"], rules=[],
                          facts={"document_type": ["reminder", "none"]})}
    listed = {e["citation"] for e in briefing.relevant_sources(s.case, r[0].decision, corpus)}
    assert listed == {"BGE PO"}


def test_stored_decisions_are_well_formed_and_not_released_to_users_by_accident():
    # A misspelt rule or fact name would silently hide a decision from every briefing.
    import json, pathlib, re
    from handover.areas import AREAS, FIELD_BY_NAME
    from handover.issues import ISSUE_BY_ID
    root = pathlib.Path(__file__).parent.parent
    rules = set(re.findall(r'"(R\d+-[a-z-]+)"', (root / "handover" / "rules.py").read_text()))
    stored = json.loads((root / "sources" / "case_law.json").read_text(encoding="utf-8"))
    for key, e in stored.items():
        assert e["type"] == "decision" and e["url"].startswith("https://"), key
        assert e["areas"] and set(e["areas"]) <= set(AREAS), key
        assert set(e["rules"]) <= rules, key
        assert e["issues"] and set(e["issues"]) <= set(ISSUE_BY_ID), key
        for name, allowed in e.get("facts", {}).items():
            spec = FIELD_BY_NAME[name]
            assert isinstance(allowed, list) and allowed, key
            if spec.choices:
                assert set(allowed) <= set(spec.choices), key
        assert len(e["text"]) >= 200 and e["holding"] and e["selected_by"], key
        # Releasing a decision to users is a decision of the legal lead and changes the
        # prompts, so the demo must be recorded again. Update this test when that happens.
        assert e["use"] == ["briefing"], key


def test_detector_reset_does_not_count_as_no_progress():
    # Round 2 answers the question asked, but also mentions "Betreibungsamt" (negated).
    # The detector sends document_type back to be asked directly; the useful answer
    # must not be treated as "no progress".
    m1 = "Ich habe eine Mahnung von einem Inkassobüro über 480 Franken bekommen."
    m2 = "Kein Schreiben vom Betreibungsamt. Ich bestreite nur die Gebühren."
    s, r = run([m1, m2], [
        REMINDER_1,
        {"language": "de", "areas": [],
         "facts": {"debt_disputed": fact("partly", "Ich bestreite nur die Gebühren")}},
    ])
    assert r[1].route is Route.ASK and "document_type" in r[1].decision.questions
    assert not s.case.no_progress


# ---- hand-over only with the user's agreement ---------------------------------

def _outbox_files():
    return len(os.listdir(config.OUTBOX_DIR))


def test_handover_is_proposed_and_only_carried_out_after_a_clear_yes():
    before = _outbox_files()
    empty = {"language": "de", "areas": [], "facts": {}}
    s, r = run([DISTRESS_MSG], [DISTRESS_OUT, empty, empty], consent=True)
    offer = r[0]
    assert offer.route is Route.REFER and offer.kind == "refer_offer"
    assert "Darf ich Ihr Anliegen übergeben?" in offer.text and "143" in offer.text
    assert not s.closed and s.handover == "offered" and _outbox_files() == before

    # An answer that is not a plain yes or no is never taken as agreement.
    again = s.step("Ja, aber was passiert dann mit meinen Daten?")
    assert again.kind == "refer_offer" and not s.closed and _outbox_files() == before
    assert len(s.llm.calls) == 2            # it was processed as a normal message

    declined = s.step("Nein")
    assert declined.kind == "refer_declined" and s.handover == "declined" and not s.closed
    assert "nichts weitergegeben" in declined.text and "143" in declined.text
    assert _outbox_files() == before and len(s.llm.calls) == 2   # no model call for the answer

    # The conversation stays open; the system still gives no classification.
    later = s.step("Ich weiss nicht weiter.")
    assert later.route is Route.REFER and later.kind == "refer_declined"
    assert "Darf ich Ihr Anliegen übergeben?" not in later.text
    s.request_human()  # a fresh explicit request renews the offer

    # A typed yes is agreement, but without name and e-mail address nothing is sent:
    # the reply asks for them, with no model call, and the proposal stays open.
    calls = len(s.llm.calls)
    asked = s.step("ja")
    assert asked.kind == "handover_contact" and not s.closed and _outbox_files() == before
    assert asked.data["contact"]["missing"] == ["first_name", "last_name", "email"]
    assert "noch nichts weitergegeben" in asked.text and "143" in asked.text
    assert len(s.llm.calls) == calls
    done = s.answer_handover(True, contact=PERSON)
    assert done.kind == "refer" and s.closed and _outbox_files() == before + 1
    assert any(a.startswith("the user agreed to the hand-over (typed); case number LX-")
               for a in s.case.audit)
    assert "ja, getippt: «ja»" in done.briefing            # the typed yes is on record
    assert "Klasse 1 – dringend und wichtig – Hinweis auf akute Belastung" in done.briefing


def test_declining_with_a_close_deadline_shows_the_date():
    m = "Ich habe am 03.11.2026 einen Zahlungsbefehl erhalten."
    s, r = run([m], [
        {"language": "de", "areas": [{"area": "debt_collection", "evidence": "Zahlungsbefehl"}],
         "facts": {"document_type": fact("payment_order", "einen Zahlungsbefehl erhalten"),
                   "document_received_date": fact("2026-11-03", "am 03.11.2026")}}])
    s.answer_form({"document_type": "payment_order"})           # confirm the sender
    s.request_human()
    declined = s.answer_handover(False)
    assert declined.kind == "refer_declined" and not s.closed
    assert "13.11.2026" in declined.text and "Rechtsvorschlag" in declined.text
    import pytest
    with pytest.raises(RuntimeError):       # there is nothing left to answer
        s.answer_handover(True, contact=PERSON)


# ---- questions the user asks ---------------------------------------------------

def _q(topic, evidence, **extra):
    return {"language": "de", "areas": [], "facts": {},
            "user_questions": [{"topic": topic, "evidence": evidence}], **extra}


def test_user_question_is_answered_from_fixed_text_and_not_counted_as_failed_answer():
    q1, q2 = "Wobei können Sie mir helfen?", "Und was ist eine Mahnung?"
    s, r = run([q1, q2, "Hm."], [
        _q("service_scope", q1),
        {**_q("term_mahnung", "was ist eine Mahnung?"),
         "user_questions": [{"topic": "term_mahnung", "evidence": "was ist eine Mahnung?"},
                            {"topic": "term_zahlungsbefehl", "evidence": "not in the message"},
                            {"topic": "made_up_topic", "evidence": q2}]},
        {"language": "de", "areas": [], "facts": {}}])
    a = r[0].data["answers"]
    assert r[0].route is Route.ASK and [x["topic"] for x in a] == ["service_scope"]
    assert "fünf Themen" in r[0].text and r[0].text.index("fünf Themen") < r[0].text.index("Worum geht es")
    assert s.llm.calls and len(s.llm.calls) == 3     # no extra model call writes the answer
    # second question: only the topic with a quote from this message is answered
    b = r[1].data["answers"]
    assert [x["topic"] for x in b] == ["term_mahnung"]
    assert b[0]["citation"] == "Art. 102 Abs. 1 OR" and b[0]["url"].endswith("#art_102")
    assert "noch keine Einschätzung Ihres Falls" in r[1].text
    # Only the third, non-question message consumed an attempt and a round.
    assert r[1].route is Route.ASK and s.case.area_asks == 1 and s.case.rounds == 1
    assert s.case.question_turns == 2
    # The first unsuccessful answer receives clarification, not a permanent stop.
    assert r[2].route is Route.ASK
    assert s.case.no_progress_rounds == 1


def test_scope_question_is_answered_even_if_the_model_does_not_label_it():
    s, r = run(["Hey can you tell me what you can help me with?"],
               [{"language": "en", "areas": [], "facts": {}}], lang="en")
    assert [x["topic"] for x in r[0].data["answers"]] == ["service_scope"]
    assert "five topics" in r[0].text and s.case.area_asks == 0


def test_question_about_own_case_is_answered_honestly_before_the_facts_are_complete():
    m = "Ich habe eine Mahnung vom Inkassobüro bekommen. Muss ich das zahlen?"
    out = {**REMINDER_1, "user_questions": [{"topic": "own_case",
                                             "evidence": "Muss ich das zahlen?"}]}
    s, r = run([m], [out])
    assert r[0].route is Route.ASK
    assert "kann ich noch nicht sagen" in r[0].text


def test_questions_never_exhaust_substantive_answer_attempts():
    q = "Was ist eine Mahnung?"
    n = 8
    s, r = run([q] * n, [_q("term_mahnung", q)] * n)
    assert all(x.route is Route.ASK for x in r)
    assert s.case.area_asks == s.case.rounds == s.case.no_progress_rounds == 0


# ---- briefing: sources only for issues the facts raise --------------------------

def test_thin_distress_case_gets_a_briefing_without_case_law():
    # The case from the legal lead's test: a question, then one fact and a sign of distress.
    m1 = "Hey can you tell me what you can help me with?"
    m2 = ("I have recieved a letter asking me to pay my rent. I will kill myself if I need "
          "to pay that much of a late fee...")
    s, r = run([m1, m2], [
        {"language": "en", "areas": [], "facts": {}},
        {"language": "en", "areas": [{"area": "debt_collection", "evidence": "pay my rent"}],
         "facts": {"document_type": fact("reminder", "a letter asking me to pay my rent")},
         "distress": {"value": True, "evidence": "I will kill myself"}}],
        consent=True, lang="en")
    assert r[1].kind == "refer_offer" and r[1].decision.emergency
    doc = s.answer_handover(True, contact=PERSON).briefing   # uses the stored statutes and decisions
    assert "Anliegen der Person" in doc and "Zuerst persönlich Kontakt aufnehmen" in doc
    assert "**Entscheid:" not in doc and "**Gesetz:" not in doc
    assert "Noch nicht beurteilbar" in doc and "es fehlt: Verzugszins, Mahngebühren" in doc
    assert "Absender des Schreibens: Von einem Unternehmen" in doc   # plain labels, no field names
    assert "document_type" not in doc.split("## Gespräch")[0]


def test_decision_attached_to_an_issue_appears_only_when_the_facts_raise_it():
    from handover import briefing
    corpus = {"fees": {"type": "decision", "citation": "BGE FEES", "url": "u", "text": "t",
                       "use": ["briefing"], "areas": ["debt_collection"],
                       "issues": ["collection_fees"]}}
    done = {"language": "de", "areas": [],
            "facts": {"reminder_fee": fact("not_agreed", "Die Mahngebühr steht erstmals auf der Mahnung"),
                      "claim_amount": fact(9000, "9000 Franken")}}
    msg = "Die Mahngebühr steht erstmals auf der Mahnung, insgesamt 9000 Franken."
    s, r = run([REMINDER_MSG, msg], [REMINDER_1, done])
    assert any(x.rule == "R5-high-amount" for x in r[1].decision.reasons)
    assert [e["citation"] for e in briefing.relevant_sources(s.case, r[1].decision, corpus)] == ["BGE FEES"]
    # Same area and document, but no charge is established: the issue is not raised.
    s, r = run([REMINDER_MSG], [REMINDER_1])
    s.request_human()
    assert briefing.relevant_sources(s.case, s.last_decision, corpus) == []


# ---- demo mode and web view --------------------------------------------------

def test_demo_scenarios_replay_offline_and_end_as_expected():
    from handover import demo
    from handover.answer import classify_structured
    from handover.view import reply_view
    llm = demo.ReplayLLM()
    for sc in demo.SCENARIOS:
        for lang in ("de", "en"):
            s = Session(llm, today=demo.DEMO_TODAY, language=lang,
                        answerer=classify_structured, empathy=True)
            reply = demo.run(s, sc["messages"][lang])
            rules = [x.rule for x in reply.decision.reasons]
            assert "R0-technical-failure" not in rules, (sc["id"], lang, "recording out of date")
            assert reply.route.value == sc["expect"], (sc["id"], lang, rules)
            if "expect_rule" in sc:
                assert sc["expect_rule"] in rules
            view = reply_view(s, reply)
            assert view["decision"]["route"] == sc["expect"] and view["kind"]
            if sc["expect"] == "PROCEED":
                # Late fees: the result per charge comes from fixed texts, with sources.
                positions = view["data"]["assessment"]["positions"]
                assert positions, "the result should name each charge"
                assert all(c["url"].startswith("https://www.fedlex.admin.ch/")
                           for p in positions for c in p["citations"])
                assert not view["data"]["statements"]
                assert reply.decision.urgent == sc.get("expect_urgent", False)
                if reply.decision.urgent:      # payment order: the notes name the objection
                    notes = [n["key"] for n in view["data"]["assessment"]["notes"]]
                    assert notes[:2] == ["objection", "official_costs"]
            else:
                # the example ends with the proposal; the briefing exists only after a yes
                assert view["kind"] == "refer_offer" and not view["briefing"] and not s.closed
                assert view["data"]["conditions"]
                view = reply_view(s, s.answer_handover(True, contact=PERSON))
                assert view["kind"] == "refer" and view["closed"]
                assert view["briefing"].startswith("# ")
                # the recorded description for the advisor, labelled as model-written
                assert "vom Sprachmodell" in view["briefing"]


def test_button_for_a_human_refers_without_a_model_call():
    llm = FakeLLM([])                       # any model call would raise
    s = Session(llm, today=TODAY, language="de")
    reply = s.request_human()
    assert reply.route is Route.REFER and reply.kind == "refer_offer" and not s.closed
    assert any(x.rule == "R1-user-wants-human" for x in reply.decision.reasons)
    assert s.answer_handover(True, contact=PERSON).kind == "refer" and s.closed and llm.calls == []


def test_server_serves_page_and_runs_a_demo_conversation():
    import json as _json, threading, urllib.request
    from http.server import ThreadingHTTPServer
    import server
    server.Handler.app = server.App(demo_mode=True, today=None)
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{httpd.server_address[1]}"

    def call(path, body=None):
        data = None if body is None else _json.dumps(body).encode()
        req = urllib.request.Request(base + path, data, {"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, r.read().decode()
    try:
        assert "<!doctype html>" in call("/")[1]
        assert call("/static/app.js")[0] == 200
        cfg = _json.loads(call("/api/config?lang=de")[1])
        assert cfg["demo"] and len(cfg["examples"]) == 6
        sess = _json.loads(call("/api/session", {"lang": "de", "scenario": "not_covered"})[1])
        reply = None
        for msg in sess["script"]:
            reply = _json.loads(call("/api/message", {"id": sess["id"], "text": msg})[1])
        assert reply["route"] == "REFER" and not reply["decision"]["urgent"]
        assert reply["decision"]["reasons"][0]["rule"] == "R14-not-covered"
        assert reply["kind"] == "refer_offer" and not reply["closed"] and not reply["briefing"]
        assert reply["decision"]["handover"] == "offered"
        try:                                  # only true or false is an answer
            call("/api/handover", {"id": sess["id"], "accept": "yes"})
            assert False
        except urllib.error.HTTPError as e:
            assert e.code == 400
        # A yes without the required details is answered with the request for them.
        early = _json.loads(call("/api/handover", {"id": sess["id"], "accept": True,
                                                   "contact": "name@example.org"})[1])
        assert early["kind"] == "handover_contact" and not early["closed"]
        assert early["data"]["contact"]["missing"] == ["first_name", "last_name", "email"]
        done = _json.loads(call("/api/handover", {"id": sess["id"], "accept": True, "contact": {
            "first_name": "Nora", "last_name": "Beispiel", "email": "name@example.org"}})[1])
        assert done["kind"] == "refer" and done["closed"]
        assert "name@example.org" in done["briefing"] and "Nora Beispiel" in done["briefing"]
        assert done["data"]["case_number"] in done["briefing"]
        assert "Klasse 3 – keine Frist bekannt" in done["briefing"]     # topic outside the fields
        try:                                  # files outside the web folder are not served
            call("/static/../server.py")
            assert False
        except urllib.error.HTTPError as e:
            assert e.code == 404
    finally:
        httpd.shutdown()
