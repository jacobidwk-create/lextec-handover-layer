"""Late fees: the three gates of the legal lead's framework (full_report.md section 3.4a).

No model, no network. The questions are answered from lists (answer_form); the
result per charge comes from fixed rules and fixed texts (handover/late_fees.py).
"""
import json
import shutil
import subprocess
from datetime import date

import pytest

from handover import knowledge, late_fees, texts
from handover.answer import classify_structured
from handover.areas import FIELD_BY_NAME, FIELDS, UNKNOWN_CHOICE, required_fields
from handover.engine import Session
from handover.llm import FakeLLM
from handover.rules import gate
from handover.schema import Case, Fact, Route, Status
from handover.view import reply_view

TODAY = date(2026, 11, 13)
LATE_FEE_FIELDS = ("document_type", "principal_status", "default_trigger",
                   "interest_charge", "reminder_fee", "collection_costs")


def case(**facts):
    """A case with the given answers. A partial answer ("claimed") counts here as already
    followed up once, so that the outcome is tested; the follow-up itself is tested below
    with fresh() cases."""
    c = Case(areas={"debt_collection": "a letter"})
    for name, value in facts.items():
        c.facts[name] = (Fact(name, Status.USER_UNKNOWN) if value is None
                         else Fact(name, Status.KNOWN, value, "words of the person",
                                   detail_asks=1 if value == "claimed" else 0))
    return c


def fresh(**facts):
    c = case(**facts)
    for f in c.facts.values():
        f.detail_asks = 0
    return c


def asked(c):
    return gate(c, TODAY).questions


def verdicts(c, lang="de"):
    return {p["key"]: p["verdict"] for p in late_fees.assess(c, lang)["positions"]}


def session(lang="de", **facts):
    """A conversation in which the model is never called again."""
    s = Session(FakeLLM([]), today=TODAY, language=lang, answerer=classify_structured)
    s.case = case(**facts)
    s.case.language = lang
    return s, s._decide_and_respond()


# ---- gate 1: who sent the letter ------------------------------------------------

def test_gate_1_is_asked_first_and_alone():
    c = case()
    assert asked(c) == ["document_type"]
    assert [f.name for f in required_fields(c)] == ["document_type"]


def test_letter_from_the_enforcement_office_is_the_only_urgent_case():
    # Another document of the office (for example a notice of seizure): handed over.
    d = gate(case(document_type="seizure_notice"), TODAY)
    assert d.route is Route.REFER and d.urgent and d.questions == []
    assert [r.rule for r in d.reasons] == ["R5-enforcement-office"]
    # A payment order: urgent notice, and the questions about the charges continue.
    d = gate(case(document_type="payment_order"), TODAY)
    assert d.route is Route.ASK and d.urgent
    assert d.questions == ["principal_status", "default_trigger"]
    assert [r.rule for r in d.reasons] == ["A3-facts-missing", "U1-payment-order"]


def test_payment_order_is_handed_over_only_if_the_objection_period_may_have_passed():
    running = case(document_type="payment_order", document_received_date=date(2026, 11, 9))
    assert gate(running, TODAY).route is Route.ASK
    passed = case(document_type="payment_order", document_received_date=date(2026, 10, 20))
    d = gate(passed, TODAY)
    assert d.route is Route.REFER and d.urgent
    assert [r.rule for r in d.reasons] == ["R4-deadline-close"]


def test_payment_order_result_tells_what_to_put_in_the_objection():
    c = case(document_type="payment_order", principal_status="open", default_trigger="reminder",
             interest_charge="statutory", reminder_fee="none", collection_costs="flat")
    d = gate(c, TODAY)
    assert d.route is Route.PROCEED and d.urgent
    a = late_fees.assess(c)
    assert verdicts(c) == {"interest_statutory": "owed", "costs_flat": "not_owed"}
    assert [n["key"] for n in a["notes"]] == ["objection", "official_costs",
                                              "instalment_agreement"]
    assert "Teil-Rechtsvorschlag" in a["notes"][0]["text"]


def test_every_other_outcome_of_the_late_fee_questions_is_not_urgent():
    """All combinations of answers: urgent if and only if the letter is from the
    debt enforcement office."""
    from itertools import product
    names = LATE_FEE_FIELDS
    values = [FIELD_BY_NAME[n].choices + (None,) for n in names]
    seen = set()
    for combo in product(*values):
        c = case(**dict(zip(names, combo)))
        d = gate(c, TODAY)
        seen.add(d.route)
        assert d.urgent == (combo[0] in ("payment_order", "seizure_notice")), combo
    assert seen == {Route.REFER, Route.PROCEED}        # complete answers never end in ASK


def test_court_letter_is_referred_and_unknown_sender_fails_closed():
    d = gate(case(document_type="court_document"), TODAY)
    assert d.route is Route.REFER and not d.urgent
    d = gate(case(document_type=None), TODAY)
    assert d.route is Route.REFER and not d.urgent
    assert [r.rule for r in d.reasons] == ["R6-critical-fact-unresolved"]


def test_public_law_claim_gets_the_special_rules_text_and_no_further_question():
    c = case(document_type="public_claim")
    assert gate(c, TODAY).route is Route.PROCEED
    a = late_fees.assess(c, "de")
    assert [p["key"] for p in a["positions"]] == ["public"]
    assert "besondere Gesetze" in a["positions"][0]["text"]
    assert a["positions"][0]["citations"][0]["citation"] == "Art. 64a KVG"


def test_payment_order_guidance_names_partial_objection_and_official_costs():
    s, reply = session(document_type="payment_order")
    assert reply.kind == "ask" and reply.decision.urgent        # no hand-over: it continues
    text = reply.text
    assert texts.PAYMENT_PARTIAL_OBJECTION["de"] in text
    assert texts.PAYMENT_OFFICIAL_COSTS["de"] in text and "Art. 68 SchKG" in text
    assert texts.PAYMENT_CONTINUE["de"] in text
    # The guidance is shown in full once; the next reply repeats only the date line.
    nxt = s.answer_form({"principal_status": "open", "default_trigger": "reminder"})
    assert nxt.data["next_steps"][0].get("compact")
    assert texts.PAYMENT_PARTIAL_OBJECTION["de"] not in nxt.text
    assert texts.PAYMENT_DATE_UNKNOWN["de"] in nxt.text


# ---- gate 2: is the person in default ----------------------------------------------

def test_gate_2_asks_about_the_bill_and_the_reminder_together():
    assert asked(case(document_type="reminder")) == ["principal_status", "default_trigger"]


@pytest.mark.parametrize("principal,key,verdict", [
    ("paid_on_time", "paid_on_time", "not_owed"),
    ("not_due", "not_due", "not_owed"),
    ("disputed", "principal_disputed", "dispute"),
])
def test_bill_not_owed_or_not_late_ends_the_questions(principal, key, verdict):
    c = case(document_type="reminder", principal_status=principal)
    d = gate(c, TODAY)
    assert d.route is Route.PROCEED                  # default_trigger is no longer needed
    assert verdicts(c) == {key: verdict}


@pytest.mark.parametrize("principal,reminds", [("open", True), ("paid_late", False)])
def test_no_reminder_and_no_agreed_date_means_no_default(principal, reminds):
    c = case(document_type="reminder", principal_status=principal, default_trigger="none")
    assert gate(c, TODAY).route is Route.PROCEED
    a = late_fees.assess(c)
    assert verdicts(c) == {"no_default": "not_owed"}
    # Only an unpaid bill is told that this letter itself can count as a reminder.
    assert ("this_letter_reminds" in [n["key"] for n in a["notes"]]) == reminds


@pytest.mark.parametrize("name", ["principal_status", "default_trigger"])
def test_unknown_answer_at_gate_2_fails_closed(name):
    facts = dict(document_type="reminder", principal_status="open", default_trigger="reminder")
    facts[name] = None
    d = gate(case(**facts), TODAY)
    assert d.route is Route.REFER and not d.urgent
    assert any(r.rule == "R6-critical-fact-unresolved" for r in d.reasons)


# ---- gate 3: each charge on its own ---------------------------------------------------

IN_DEFAULT = dict(document_type="reminder", principal_status="open", default_trigger="reminder")


def test_gate_3_asks_the_three_charges_in_one_round():
    assert asked(case(**IN_DEFAULT)) == ["interest_charge", "reminder_fee", "collection_costs"]


@pytest.mark.parametrize("fact,value,key,verdict", [
    ("interest_charge", "statutory", "interest_statutory", "owed"),
    ("interest_charge", "higher_agreed", "interest_higher_agreed", "owed_if_agreed"),
    ("interest_charge", "higher_not_agreed", "interest_higher_not_agreed", "reduced"),
    ("interest_charge", "unclear", "interest_unclear", "depends"),
    ("interest_charge", None, "interest_unclear", "depends"),
    ("interest_charge", "claimed", "interest_unclear", "depends"),
    ("reminder_fee", "claimed", "fee_unsure", "depends"),
    ("collection_costs", "claimed", "costs_unsure", "depends_proof"),
    ("reminder_fee", "agreed_amount", "fee_agreed_amount", "owed"),
    ("reminder_fee", "agreed_vague", "fee_agreed_vague", "not_owed"),
    ("reminder_fee", "not_agreed", "fee_not_agreed", "not_owed"),
    ("reminder_fee", "unsure", "fee_unsure", "depends"),
    ("reminder_fee", None, "fee_unsure", "depends"),
    ("collection_costs", "flat", "costs_flat", "not_owed"),
    ("collection_costs", "proven", "costs_proven", "owed_if_proven"),
    ("collection_costs", "unsure", "costs_unsure", "depends_proof"),
    ("collection_costs", None, "costs_unsure", "depends_proof"),
])
def test_each_answer_at_gate_3_has_its_result(fact, value, key, verdict):
    others = {n: "none" for n in ("interest_charge", "reminder_fee", "collection_costs")}
    c = case(**{**IN_DEFAULT, **others, fact: value})
    assert gate(c, TODAY).route is Route.PROCEED     # "I do not know" gives a conditional text
    assert verdicts(c) == {key: verdict}


def test_charges_that_are_not_claimed_are_not_mentioned():
    c = case(**IN_DEFAULT, interest_charge="none", reminder_fee="none", collection_costs="none")
    a = late_fees.assess(c)
    assert a["positions"] == [] and a["summary"] == late_fees.T["nothing_claimed"]["de"]


def test_notes_fit_the_situation():
    c = case(**IN_DEFAULT, interest_charge="statutory", reminder_fee="not_agreed",
             collection_costs="flat")
    notes = [n["key"] for n in late_fees.assess(c)["notes"]]
    assert notes == ["dispute_in_writing", "partial_payment", "instalment_agreement",
                     "later_payment_order"]
    paid = case(**{**IN_DEFAULT, "principal_status": "paid_late"}, interest_charge="statutory",
                reminder_fee="none", collection_costs="none")
    assert [n["key"] for n in late_fees.assess(paid)["notes"]] == ["later_payment_order"]


# ---- partial answers: "yes" is an answer, the detail is asked once -------------------------

def test_first_question_offers_no_and_yes_and_the_follow_up_offers_the_details():
    s, r = session(**IN_DEFAULT)
    q = {x["name"]: x for x in r.data["questions"]}
    assert [o["value"] for o in q["reminder_fee"]["options"]] == ["none", "claimed", UNKNOWN_CHOICE]
    assert [o["value"] for o in q["collection_costs"]["options"]] == ["none", "claimed",
                                                                     UNKNOWN_CHOICE]
    r = s.answer_form({"interest_charge": "none", "reminder_fee": "claimed",
                       "collection_costs": "claimed"})
    assert r.route is Route.ASK and r.decision.questions == ["reminder_fee", "collection_costs"]
    q = {x["name"]: x for x in r.data["questions"]}
    assert q["reminder_fee"]["detail"] and q["reminder_fee"]["question"] == \
        FIELD_BY_NAME["reminder_fee"].detail["question"]["de"]
    assert [o["value"] for o in q["reminder_fee"]["options"]] == [
        "agreed_amount", "agreed_vague", "not_agreed", "unsure"]
    assert [o["value"] for o in q["collection_costs"]["options"]] == ["flat", "proven", "unsure"]
    r = s.answer_form({"reminder_fee": "not_agreed", "collection_costs": "flat"})
    assert r.route is Route.PROCEED
    assert [(p["key"], p["verdict"]) for p in r.data["assessment"]["positions"]] == [
        ("fee_not_agreed", "not_owed"), ("costs_flat", "not_owed")]


def test_yes_without_the_detail_is_recorded_and_followed_up_once_never_repeated():
    """The hand-over of 2026-11-13: "yes they are Mahngebühren" could not be recorded,
    the same question came again, and the conversation was handed over."""
    yes = {"language": "de", "areas": [],
           "facts": {"reminder_fee": {"value": "claimed", "evidence": "ja, das sind Mahngebühren"}}}
    nothing = {"language": "de", "areas": [], "facts": {}}
    s = Session(FakeLLM([yes, nothing]), today=TODAY, answerer=classify_structured)
    s.case = fresh(**IN_DEFAULT, interest_charge="none", collection_costs="none")
    first = s._decide_and_respond()
    assert first.decision.questions == ["reminder_fee"]
    r = s.step("ja, das sind Mahngebühren")
    assert s.case.value("reminder_fee") == "claimed" and s.case.no_progress_rounds == 0
    q = r.data["questions"][0]
    assert q["detail"] and q["question"] != first.data["questions"][0]["question"]
    # The person cannot say more. The detail was asked once: the conversation moves on
    # to the result with the conditional text, instead of asking again or handing over.
    r = s.step("das habe ich doch schon gesagt!")
    assert r.route is Route.PROCEED and r.kind == "proceed"
    assert [(p["key"], p["verdict"]) for p in r.data["assessment"]["positions"]] == [
        ("fee_unsure", "depends")]
    assert any("detail asked once without result" in line for line in s.case.audit)


def test_fresh_partial_answer_asks_for_the_detail_before_any_result():
    c = fresh(**IN_DEFAULT, interest_charge="claimed", reminder_fee="none", collection_costs="flat")
    d = gate(c, TODAY)
    assert d.route is Route.ASK and d.questions == ["interest_charge"]
    c.facts["interest_charge"].detail_asks = 1
    assert gate(c, TODAY).route is Route.PROCEED


def test_office_fee_as_large_as_the_bill_is_sorted_as_a_collection_cost_and_listed_charges_end_the_questions():
    """What the model is asked to do with "interest and an additional fee for the office
    of CHF 200": the instruction is part of the fact descriptions and the field file."""
    costs = FIELD_BY_NAME["collection_costs"].description
    assert "'the office'" in costs and "also if the user calls it a late fee" in costs
    assert "NOT a charge for the collection agency" in FIELD_BY_NAME["reminder_fee"].description
    assert all("lists what the letter claims" in FIELD_BY_NAME[n].description
               for n in ("interest_charge", "reminder_fee", "collection_costs"))
    from handover.legal_fields import REGISTRY
    book = REGISTRY["debt_collection"].playbook
    assert "typical collection-agency pattern" in book and "One amount belongs to one charge" in book
    assert {"or-160", "or-161", "or-163"} <= set(REGISTRY["debt_collection"].statutes)
    # The reading the model is expected to return, played through without it.
    out = {"language": "en", "areas": [], "facts": {
        "interest_charge": {"value": "claimed", "evidence": "it claims interest"},
        "collection_costs": {"value": "claimed", "evidence": "an additional fee for the office"},
        "reminder_fee": {"value": "none", "evidence": "it claims interest and an additional fee for the office"}}}
    s = Session(FakeLLM([out]), today=TODAY, language="en", answerer=classify_structured)
    s.case = fresh(**IN_DEFAULT)
    s.case.language = "en"
    s._decide_and_respond()
    r = s.step("Yes it claims interest and an additional fee for the office in the height of CHF 200!!!")
    assert r.route is Route.ASK and r.decision.questions == ["interest_charge", "collection_costs"]
    assert all(x["detail"] for x in r.data["questions"])
    r = s.answer_form({"interest_charge": "unclear", "collection_costs": "flat"})
    assert [(p["key"], p["verdict"]) for p in r.data["assessment"]["positions"]] == [
        ("interest_unclear", "depends"), ("costs_flat", "not_owed")]


# ---- texts: complete, bilingual, plain ---------------------------------------------------

def test_all_texts_exist_in_both_languages_without_sharp_s_and_with_fedlex_links():
    for table in (late_fees.FINDINGS, late_fees.NOTES):
        for key, e in table.items():
            for lang in ("de", "en"):
                assert e["title"][lang] and e["text"][lang], key
            assert "ß" not in e["title"]["de"] + e["text"]["de"], key
            assert e.get("verdict", "owed") in late_fees.VERDICTS, key
            for law, art, citation in e["sources"]:
                assert knowledge.fedlex_url(law, art, "de").startswith(
                    "https://www.fedlex.admin.ch/eli/cc/"), key
            assert all(t in knowledge.ENTRIES for t in e["terms"]), key
    for key, e in knowledge.ENTRIES.items():
        assert "ß" not in e["title"]["de"] + e["text"]["de"], key


def test_every_cited_article_is_in_the_local_statute_corpus():
    """The texts cite only articles whose wording was fetched from Fedlex."""
    from handover.answer import load_corpus
    corpus = load_corpus()
    cited = {(law, art) for table in (late_fees.FINDINGS, late_fees.NOTES)
             for e in table.values() for law, art, _ in e["sources"]}
    cited |= {e["source"][:2] for k, e in knowledge.ENTRIES.items()
              if "source" in e and k in {t for f in FIELDS for t in f.terms}}
    assert not [f"{law}-{art}" for law, art in cited if f"{law}-{art}" not in corpus]


def test_list_questions_are_complete_and_explain_their_terms():
    for name in LATE_FEE_FIELDS:
        spec = FIELD_BY_NAME[name]
        assert set(spec.options) == set(spec.choices), name
        for value, label in spec.options.items():
            assert label["de"] and label["en"] and "ß" not in label["de"], (name, value)
        assert spec.terms and all(t in knowledge.ENTRIES for t in spec.terms), name
    # Only the letter from the enforcement office names it; the other answers must not
    # trip the keyword detector for enforcement documents.
    private = FIELD_BY_NAME["document_type"].options["reminder"]["de"]
    assert "Betreibung" not in private and "Zahlungsbefehl" not in private


# ---- answers chosen from a list: no model call --------------------------------------------

@pytest.mark.parametrize("lang", ["de", "en"])
def test_whole_flow_with_list_answers_needs_no_model_call(lang):
    s, r1 = session(lang, document_type="reminder")
    q = r1.data["questions"]
    assert [x["name"] for x in q] == ["principal_status", "default_trigger"]
    assert all(x["options"][-1]["value"] == UNKNOWN_CHOICE for x in q)
    assert [t["topic"] for t in q[0]["terms"]] == ["term_hauptforderung", "term_faelligkeit_verzug"]
    assert r1.data["submit_label"] == texts.FORM_SUBMIT[lang]
    assert texts.OPTIONS_LABEL[lang] in r1.text          # the command line shows the answers too

    r2 = s.answer_form({"principal_status": "open", "default_trigger": "reminder"})
    assert r2.route is Route.ASK
    assert [x["name"] for x in r2.data["questions"]] == ["interest_charge", "reminder_fee",
                                                         "collection_costs"]
    assert r2.data["ack"] == texts.FORM_ACK[lang]        # fixed text, no model-written line
    r3 = s.answer_form({"interest_charge": "statutory", "reminder_fee": "not_agreed",
                        "collection_costs": UNKNOWN_CHOICE})
    assert r3.route is Route.PROCEED and r3.kind == "proceed"
    assert s.llm.calls == []                             # nothing was sent to the model
    a = r3.data["assessment"]
    assert [(p["key"], p["verdict"]) for p in a["positions"]] == [
        ("interest_statutory", "owed"), ("fee_not_agreed", "not_owed"),
        ("costs_unsure", "depends_proof")]
    assert not r3.data["statements"] and not r3.data["no_sources"]
    # The record keeps the chosen wording as the person's statement.
    f = s.case.fact("reminder_fee")
    assert f.evidence == FIELD_BY_NAME["reminder_fee"].options["not_agreed"][lang]
    assert f.evidence in s.case.user_text()
    assert s.case.fact("collection_costs").status is Status.USER_UNKNOWN
    assert any("chosen from the list" in line for line in s.case.audit)
    assert late_fees.VERDICTS["not_owed"][lang] in r3.text


def test_list_answer_is_rejected_unless_it_answers_an_open_question():
    s, _ = session(document_type="reminder")
    for bad in ({}, {"principal_status": "banana"}, {"interest_charge": "none"},
                {"claim_amount": "5"}, {"nope": "x"},
                {"principal_status": "open", "nope": "x"}):
        with pytest.raises(ValueError):
            s.answer_form(bad)
    assert s.case.fact("principal_status").status is Status.MISSING    # nothing was applied
    s, _ = session(document_type="seizure_notice")                      # a hand-over is offered
    with pytest.raises(ValueError):
        s.answer_form({"document_type": "reminder"})


def test_partial_list_answer_keeps_the_rest_open():
    s, _ = session(document_type="reminder")
    r = s.answer_form({"principal_status": "paid_late"})
    assert r.route is Route.ASK and r.decision.questions == ["default_trigger"]


def test_unknown_sender_from_the_list_is_referred_without_urgency():
    s, r = session()
    assert [x["name"] for x in r.data["questions"]] == ["document_type"]
    r = s.answer_form({"document_type": UNKNOWN_CHOICE})
    assert r.kind == "refer_offer" and not r.decision.urgent


def test_free_text_still_works_for_a_list_question():
    out = {"language": "de", "areas": [],
           "facts": {"principal_status": {"value": "paid_on_time",
                                          "evidence": "ich habe pünktlich bezahlt"}}}
    s = Session(FakeLLM([out]), today=TODAY, answerer=classify_structured)
    s.case = case(document_type="reminder")
    s._decide_and_respond()
    r = s.step("Die Rechnung stimmt, ich habe pünktlich bezahlt.")
    assert r.route is Route.PROCEED
    assert [p["key"] for p in r.data["assessment"]["positions"]] == ["paid_on_time"]


def test_common_scope_questions_are_not_asked_for_late_fees_but_their_rules_still_apply():
    c = case(**IN_DEFAULT, interest_charge="none", reminder_fee="none", collection_costs="none")
    assert not {"jurisdiction", "case_complexity", "other_official_deadline"} & {
        f.name for f in required_fields(c)}
    c.facts["jurisdiction"] = Fact("jurisdiction", Status.KNOWN, "international", "in Germany")
    assert gate(c, TODAY).route is Route.REFER


def test_briefing_carries_the_preliminary_check_of_the_charges():
    from handover import briefing
    s, _ = session(**IN_DEFAULT, interest_charge="higher_not_agreed", reminder_fee="agreed_vague",
                   collection_costs="flat")
    offer = s.request_human()
    doc = briefing.render(s.case, offer.decision, TODAY, lang="de")
    assert "Vorprüfung nach festen Regeln" in doc and "Was für Ihre Zusatzkosten gilt" in doc
    assert "**Verzugszins über 5 %: Nur 5 % pro Jahr geschuldet**" in doc
    assert "Absender des Schreibens: Von einem Unternehmen oder einem Inkassobüro" in doc
    assert "**Aufgeworfen:** Zusatzkosten bei verspäteter Zahlung" in doc
    assert "Art. 105 OR" in doc and "Art. 8 UWG" in doc      # statutes of the issue raised


# ---- server and page -----------------------------------------------------------------------

def test_server_accepts_list_answers_and_rejects_anything_else(monkeypatch):
    import threading
    import urllib.error
    import urllib.request
    from http.server import ThreadingHTTPServer
    import server
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-not-used")
    app = server.App(demo_mode=True, today=None)
    server.Handler.app = app
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{httpd.server_address[1]}"

    def call(path, body):
        req = urllib.request.Request(base + path, json.dumps(body).encode(),
                                     {"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                return r.status, json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            return e.code, {}
    try:
        sess = call("/api/session", {"lang": "de", "scenario": "fees"})[1]
        assert all(isinstance(m, str) for m in sess["script"])
        # Put the conversation at gate 2 without a model call.
        s = app.sessions[sess["id"]]["session"]
        s.case = case(document_type="reminder")
        s._decide_and_respond()
        sid = sess["id"]
        assert call("/api/answers", {"id": sid, "answers": {"principal_status": 5}})[0] == 400
        assert call("/api/answers", {"id": sid, "answers": {"principal_status": "x"}})[0] == 400
        assert call("/api/answers", {"id": sid, "answers": []})[0] == 400
        assert call("/api/answers", {"id": "nope", "answers": {"principal_status": "open"}})[0] == 404
        # In the conversation the questions come one at a time.
        assert call("/api/answers", {"id": sid, "answers": {
            "principal_status": "open", "default_trigger": "none"}})[0] == 400
        status, reply = call("/api/answers", {"id": sid, "answers": {"principal_status": "open"}})
        assert status == 200 and reply["data"]["questions"][0]["name"] == "default_trigger"
        # Demo: the prepared answer of the example is marked on the question.
        assert reply["data"]["questions"][0]["prepared"] == "reminder"
        status, reply = call("/api/answers", {"id": sid, "answers": {"default_trigger": "none"}})
        assert status == 200 and reply["route"] == "PROCEED"
        assert reply["data"]["assessment"]["positions"][0]["key"] == "no_default"
        facts = {f["label"]: f["value"] for f in reply["decision"]["facts"]}
        assert facts["Ursprüngliche Rechnung"].startswith("Die Rechnung stimmt")
    finally:
        httpd.shutdown()


def test_page_renders_lists_terms_and_result_and_sends_the_chosen_answers():
    if not shutil.which("node"):
        pytest.skip("Node.js is required for the frontend renderer test")
    replies = []
    for lang in ("de", "en"):
        s, r1 = session(lang, document_type="reminder")
        replies.append(reply_view(s, r1))
        r2 = s.answer_form({"principal_status": "open", "default_trigger": "reminder"})
        replies.append(reply_view(s, r2))
        r3 = s.answer_form({"interest_charge": "higher_not_agreed", "reminder_fee": "unsure",
                            "collection_costs": "flat"})
        replies.append(reply_view(s, r3))
    result = subprocess.run(["node", "tests/web_form.cjs"], input=json.dumps(replies),
                            text=True, capture_output=True, check=False)
    assert result.returncode == 0, result.stderr + result.stdout
