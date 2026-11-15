"""Entry in the debt enforcement register: the legal lead's flow of 2026-11-14
(full_report.md section 3.4c).

No model, no network. Built like the tests for late fees and for declining an
inheritance: the questions are part of the conversation with quick replies, the route
comes from fixed rules, and the result comes from fixed texts (handover/register.py).
"""
import json
from datetime import date
from pathlib import Path

import pytest

from handover import config, knowledge, register, texts
from handover.answer import FIXED_RESULTS, classify_structured, load_corpus
from handover.areas import (FIELD_BY_NAME, NO_COMMON_QUESTIONS, UNKNOWN_CHOICE,
                            register_objection_open, register_request_from, register_wait,
                            required_fields)
from handover.engine import Session
from handover.legal_fields import REGISTRY
from handover.llm import FakeLLM
from handover.rules import gate
from handover.schema import Case, Fact, Route, Status

TODAY = date(2026, 11, 14)
E, P, O = "register_entry", "register_payment", "register_objection"
D, C, M = "register_service_date", "register_creditor_step", "register_missed_reason"
LONG_AGO = date(2026, 5, 1)          # three months over on 02.08.2026
RECENT = date(2026, 10, 1)           # three months over on 02.01.2027
THIS_WEEK = date(2026, 11, 9)        # ten days end on 19.11.2026
UNPAID = {E: "enforcement", P: "not_paid"}
OBJECTED = {**UNPAID, O: "yes", D: LONG_AGO}
MISSED = {**UNPAID, O: "no", D: LONG_AGO}


def case(facts):
    c = Case(areas={"credit_record": "refused a flat because of an entry"})
    for name, value in facts.items():
        c.facts[name] = (Fact(name, Status.USER_UNKNOWN) if value is None
                         else Fact(name, Status.KNOWN, value, "words of the person"))
    return c


def session(facts, lang="de"):
    s = Session(FakeLLM([]), today=TODAY, language=lang, answerer=classify_structured)
    s.case = case(facts)
    s.case.language = lang
    return s, s._decide_and_respond()


def result(facts):
    c = case(facts)
    d = gate(c, TODAY)
    a = register.assess(c, d, "de")
    return d, [p["key"] for p in a["positions"]], [n["key"] for n in a["notes"]], a


# ---- the questions, one after the other ---------------------------------------------------

def test_questions_follow_the_flow_and_none_of_the_general_scope_questions_is_asked():
    order = [({}, E), ({E: "enforcement"}, P), (UNPAID, O), ({**UNPAID, O: "yes"}, D),
             (OBJECTED, C), ({**UNPAID, O: "no"}, D), (MISSED, M),
             ({E: "enforcement", P: "paid_before"}, O)]
    for facts, question in order:
        assert gate(case(facts), TODAY).questions[0] == question, facts
    assert "credit_record" in NO_COMMON_QUESTIONS
    asked = {f.name for f in required_fields(case(OBJECTED))}
    assert not asked & {"jurisdiction", "case_complexity", "other_official_deadline"}


def test_questions_have_quick_replies_terms_and_an_i_do_not_know():
    for name in (E, P, O, C, M):
        spec = FIELD_BY_NAME[name]
        assert set(spec.options) == set(spec.choices) and spec.terms, name
        assert all(t in knowledge.ENTRIES for t in spec.terms), name
        assert not spec.critical, name             # "I do not know" never hands over alone
    s, r = session({})
    q = r.data["questions"][0]
    assert [o["value"] for o in q["options"]] == ["enforcement", "old_enforcement",
                                                  "loss_certificate", "private_agency",
                                                  UNKNOWN_CHOICE]
    assert [t["topic"] for t in q["terms"]] == ["term_betreibungsregister", "term_betreibung",
                                                "term_verlustschein"]
    # The date is typed, not chosen.
    assert FIELD_BY_NAME[D].kind == "date" and not FIELD_BY_NAME[D].options


# ---- gate 1: kind and age of the entry ------------------------------------------------------

@pytest.mark.parametrize("entry,key,verdict,article", [
    ("old_enforcement", "old", "hidden", "Art. 8a Abs. 4 SchKG"),
    ("loss_certificate", "loss_certificate", "delete", "Art. 149a SchKG"),
    (None, "get_extract", "check", "Art. 12a GebV SchKG"),
])
def test_gate_1_answers_that_end_the_flow(entry, key, verdict, article):
    d, positions, notes, a = result({E: entry})
    assert d.route is Route.PROCEED and not d.urgent
    assert positions == [key] and a["positions"][0]["verdict"] == verdict
    assert article in [c["citation"] for c in a["positions"][0]["citations"]]
    assert required_fields(case({E: entry}))[1:] == []      # nothing else is asked


def test_loss_certificate_is_deleted_after_settlement_under_paragraph_3():
    # The flow named para. 2 for the deletion; on Fedlex para. 2 is the payment to the
    # office and para. 3 the deletion. The text states both without a paragraph number.
    text = load_corpus()["schkg-149a"]["text"]
    assert "3 Nach der Tilgung wird der Eintrag des Verlustscheines in den Registern gelöscht" in text
    assert "20 Jahre nach der Ausstellung" in text
    assert "gelöscht, sobald die Forderung getilgt ist" in register.FINDINGS["loss_certificate"]["text"]["de"]


def test_private_credit_agency_is_said_to_be_outside_and_the_hand_over_proposed_once():
    s, r = session({})
    r = s.answer_form({E: "private_agency"})
    assert r.kind == "refer_offer" and not r.decision.urgent
    assert [x.rule for x in r.decision.reasons] == ["R5-private-credit-agency"]
    assert r.data["reasons"] == [texts.REFER_WHY["R5-private-credit-agency"]["de"]]
    r = s.answer_handover(False)
    assert r.route is Route.PROCEED and "R5-private-credit-agency" in s.case.declined_rules
    assert [p["key"] for p in r.data["assessment"]["positions"]] == ["private_agency"]
    assert r.data["assessment"]["positions"][0]["citations"] == []     # no source, said so


# ---- gate 2, track A: not paid, objection raised --------------------------------------------

def test_three_months_since_service_are_computed_by_code():
    c = case(OBJECTED)
    gate(c, TODAY)
    assert register_request_from(c) == date(2026, 8, 2) and register_wait(c) == "over"
    c = case({**UNPAID, O: "yes", D: date(2026, 8, 14)})
    gate(c, TODAY)                                   # three months end today: not yet "after"
    assert register_request_from(c) == date(2026, 11, 15) and register_wait(c) == "running"
    c = case({**UNPAID, O: "yes", D: None})
    assert register_wait(c) == "unknown"


def test_request_is_possible_after_three_months_with_fee_and_twenty_days():
    d, positions, notes, a = result({**OBJECTED, C: "none"})
    assert d.route is Route.PROCEED and not d.urgent and not d.deadlines
    assert positions == ["request_possible"] and notes == ["not_deletion", "pay_trap"]
    p = a["positions"][0]
    assert p["verdict_label"] == "Gesuch möglich"
    assert "Frist von 20 Tagen" in p["text"] and "pauschal 40 Franken" in p["text"]
    assert [c["citation"] for c in p["citations"]] == ["Art. 8a Abs. 3 Bst. d SchKG",
                                                       "Art. 12b GebV SchKG"]
    assert "pauschal 40 Franken" in load_corpus()["gebv-12b"]["text"]
    # "I do not know" what the creditor did: the office finds out, the request is the way.
    assert result({**OBJECTED, C: None})[1] == ["request_possible"]


def test_before_three_months_the_result_names_the_first_day_and_what_helps_until_then():
    d, positions, notes, a = result({**UNPAID, O: "yes", D: RECENT, C: "none"})
    assert d.route is Route.PROCEED and positions == ["request_wait"]
    text = a["positions"][0]["text"]
    assert "ab dem 02.01.2027" in text and "zurückziehen" in text and "Beweismittel" in text
    assert "Art. 73 SchKG" in [c["citation"] for c in a["positions"][0]["citations"]]
    assert a["summary"] == register.SUMMARY["wait"]["de"]


def test_unknown_day_of_service_gives_the_conditional_text():
    d, positions, _, a = result({**UNPAID, O: "yes", D: None, C: "none"})
    assert d.route is Route.PROCEED and positions == ["request_after_wait"]
    assert a["positions"][0]["verdict"] == "after_wait"


def test_creditor_who_definitively_lost_opens_the_request_since_2026():
    d, positions, _, a = result({**OBJECTED, C: "lost"})
    assert d.route is Route.PROCEED and positions == ["creditor_lost"]
    assert "definitiv nicht gutgeheissen" in a["positions"][0]["text"]
    assert "definitiv nicht gutgeheissen wurde" in load_corpus()["schkg-8a"]["text"]
    # Still within the three months: the waiting time comes first.
    assert result({**UNPAID, O: "yes", D: RECENT, C: "lost"})[1] == ["request_wait"]


@pytest.mark.parametrize("step,key,verdict", [("pending", "creditor_pending", "court_running"),
                                              ("won", "creditor_won", "stays")])
def test_creditor_in_court_is_explained_and_the_hand_over_proposed(step, key, verdict):
    s, r = session(OBJECTED)
    r = s.answer_form({C: step})
    assert r.kind == "refer_offer" and not r.decision.urgent
    assert [x.rule for x in r.decision.reasons] == ["R5-register-court"]
    assert r.data["reasons"] == [texts.REFER_WHY["R5-register-court"]["de"]]
    assert r.data["conditions"]                                 # LexTec's conditions
    r = s.answer_handover(False)
    assert r.route is Route.PROCEED and "R5-register-court" in s.case.declined_rules
    p = r.data["assessment"]["positions"]
    assert [x["key"] for x in p] == [key] and p[0]["verdict"] == verdict


# ---- gate 2, track A: not paid, no objection ------------------------------------------------

def test_objection_still_possible_gets_an_urgent_notice_and_no_hand_over():
    s, r = session({**UNPAID, O: "no"})
    s.case.facts[D] = Fact(D, Status.KNOWN, THIS_WEEK, "letzten Montag")
    r = s._decide_and_respond()
    assert register_objection_open(s.case)
    assert r.route is Route.PROCEED and r.decision.urgent
    assert "U3-register-objection" in [x.rule for x in r.decision.reasons]
    assert M not in [f.name for f in required_fields(s.case)]     # no "why did you not"
    notice = r.data["next_steps"][0]
    assert notice["title"] == texts.REGISTER_NEXT_TITLE["de"]
    assert "09.11.2026" in notice["paragraphs"][1] and "19.11.2026" in notice["paragraphs"][1]
    assert texts.REGISTER_OBJECTION_WHY["de"] in notice["paragraphs"]
    period = next(x for x in r.decision.deadlines if x.key == "register_objection")
    assert period.due == date(2026, 11, 19) and period.legal_basis == "Art. 74 SchKG"
    a = r.data["assessment"]
    assert [p["key"] for p in a["positions"]] == ["objection_open"]
    assert a["positions"][0]["verdict"] == "act_now"


def test_the_urgent_notice_does_not_wait_for_the_question_about_the_objection():
    # The day of service is known from the first message and lies within ten days: the
    # notice is shown at once, while the questions about payment and objection follow.
    s, r = session({E: "enforcement"})
    s.case.facts[D] = Fact(D, Status.KNOWN, THIS_WEEK, "letzten Montag")
    r = s._decide_and_respond()
    assert r.route is Route.ASK and r.decision.questions[0] == P and r.decision.urgent
    assert r.data["next_steps"][0]["title"] == texts.REGISTER_NEXT_TITLE["de"]
    # Once the person says the objection was raised, or that they paid after service,
    # nothing is urgent any more.
    for facts in ({P: "not_paid", O: "yes"}, {P: "paid_after"}):
        c = case({E: "enforcement", D: THIS_WEEK, **facts})
        d = gate(c, TODAY)
        assert not d.urgent and not d.deadlines, facts
    # "I do not know whether I objected": the notice stays, with the conditional text.
    d, positions, _, _ = result({**UNPAID, O: None, D: THIS_WEEK})
    assert d.route is Route.PROCEED and d.urgent and positions == ["objection_unknown"]


def test_a_period_that_passed_long_ago_is_neither_urgent_nor_listed_as_a_deadline():
    d = gate(case(MISSED), TODAY)
    assert d.route is Route.ASK and d.questions == [M] and not d.urgent and not d.deadlines


@pytest.mark.parametrize("reason,keys,articles", [
    ("obstacle", ["missed_obstacle", "missed_court"], "Art. 33 Abs. 4 SchKG"),
    ("abusive", ["missed_abusive", "missed_court"], "Art. 22 SchKG"),
    ("other", ["missed_court"], "Art. 85a SchKG"),
    (None, ["missed_court"], "Art. 86 SchKG"),
])
def test_missed_objection_names_the_way_and_proposes_the_hand_over(reason, keys, articles):
    s, r = session(MISSED)
    r = s.answer_form({M: UNKNOWN_CHOICE if reason is None else reason})
    assert r.kind == "refer_offer" and not r.decision.urgent
    assert [x.rule for x in r.decision.reasons] == ["R5-register-court"]
    r = s.answer_handover(False)
    assert r.route is Route.PROCEED
    a = r.data["assessment"]
    assert [p["key"] for p in a["positions"]] == keys
    assert articles in [c["citation"] for p in a["positions"] for c in p["citations"]]
    assert [n["key"] for n in a["notes"]] == ["pay_trap", "five_years"]
    # The cautious sentence for an approximate date is always there.
    assert "noch keine zehn Tage vergangen" in a["positions"][-1]["text"]


def test_restoration_period_is_the_missed_period_from_the_end_of_the_obstacle():
    text = load_corpus()["schkg-33"]["text"]
    assert "vom Wegfall des Hindernisses an, in der gleichen Frist wie der versäumten" in text
    assert "innert zehn Tagen einzureichen, nachdem das Hindernis" in \
        register.FINDINGS["missed_obstacle"]["text"]["de"]


# ---- gate 2, track B: paid ----------------------------------------------------------------------

def test_paid_after_service_excludes_the_request_and_leaves_only_the_withdrawal():
    d, positions, notes, a = result({E: "enforcement", P: "paid_after"})
    assert d.route is Route.PROCEED and not d.urgent
    assert positions == ["paid_after", "withdrawal"] and notes == []
    assert [p["verdict"] for p in a["positions"]] == ["blocked", "creditor"]
    assert a["positions"][0]["citations"][0]["citation"] == "BGE 147 III 486"
    assert "entscheidet frei" in a["positions"][1]["text"]
    assert required_fields(case({E: "enforcement", P: "paid_after"}))[2:] == []


def test_paid_before_service_with_objection_keeps_the_request_open():
    d, positions, notes, a = result({E: "enforcement", P: "paid_before", O: "yes", D: LONG_AGO})
    assert d.route is Route.PROCEED
    assert positions == ["paid_before", "request_possible"] and notes == ["not_deletion"]
    assert "BGE 150 III 390" in [c["citation"] for c in a["positions"][0]["citations"]]
    assert C not in [f.name for f in required_fields(
        case({E: "enforcement", P: "paid_before", O: "yes", D: LONG_AGO}))]
    assert result({E: "enforcement", P: "paid_before", O: "yes", D: RECENT})[1] == [
        "paid_before", "request_wait"]


def test_paid_before_service_without_objection_goes_to_the_creditor_or_the_court():
    s, r = session({E: "enforcement", P: "paid_before", O: "no"})
    s.case.facts[D] = Fact(D, Status.KNOWN, LONG_AGO, "im Mai")
    r = s._decide_and_respond()
    assert r.kind == "refer_offer"
    assert [x.rule for x in r.decision.reasons] == ["R5-register-court"]
    r = s.answer_handover(False)
    a = r.data["assessment"]
    assert [p["key"] for p in a["positions"]] == ["paid_before_no_objection"]
    assert "Art. 85 SchKG" in [c["citation"] for c in a["positions"][0]["citations"]]


@pytest.mark.parametrize("facts,key", [({E: "enforcement", P: None}, "payment_unknown"),
                                       ({**UNPAID, O: None}, "objection_unknown")])
def test_an_unknown_answer_gives_the_conditional_text_not_a_hand_over(facts, key):
    d, positions, _, a = result(facts)
    assert d.route is Route.PROCEED and positions[-1] == key
    assert a["positions"][-1]["verdict"] == "check"


# ---- the texts and their sources -------------------------------------------------------------

def test_every_cited_article_and_decision_is_stored_and_every_term_exists():
    corpus = load_corpus()
    decisions = json.loads((Path(register.CASE_LAW)).read_text(encoding="utf-8"))
    for table in (register.FINDINGS, register.NOTES):
        for key, e in table.items():
            assert set(e["text"]) == {"de", "en"} and "ß" not in e["text"]["de"], key
            for kind, ref, citation in e["sources"]:
                if kind == "decision":
                    assert ref in decisions and decisions[ref]["url"].startswith("https://"), key
                else:
                    assert f"{kind}-{ref}" in corpus, (key, kind, ref)
                    assert knowledge.fedlex_url(kind, ref, "de").startswith("https://www.fedlex")
            assert all(t in knowledge.ENTRIES for t in e["terms"]), key
            assert e.get("verdict", "check") in register.VERDICTS, key
    for key in register.FINDINGS:
        assert "verdict" in register.FINDINGS[key], key


def test_every_outcome_of_the_flow_has_a_summary_and_a_result_in_both_languages():
    reached = set()
    for entry in ("enforcement", "old_enforcement", "loss_certificate", "private_agency", None):
        for payment in ("not_paid", "paid_before", "paid_after", None):
            for objection in ("yes", "no", None):
                for served in (LONG_AGO, RECENT, THIS_WEEK, None):
                    for step in ("none", "pending", "lost", "won", None):
                        for reason in ("obstacle", "abusive", "other", None):
                            c = case({E: entry, P: payment, O: objection, D: served,
                                      C: step, M: reason})
                            c.assessed_on = TODAY
                            for lang in ("de", "en"):
                                a = register.assess(c, None, lang)
                                assert a and a["positions"] and a["summary"]
                                assert "{date}" not in json.dumps(a)
                            reached |= {p["key"] for p in a["positions"]}
    assert reached == set(register.FINDINGS)


def test_field_file_carries_the_flow_and_the_result_is_registered():
    field = REGISTRY["credit_record"]
    assert field.handling == "answer"
    assert field.title == {"de": "Eintrag im Betreibungsregister",
                           "en": "Entry in the debt enforcement register"}
    for part in ("Gate 1: what kind of entry", "Gate 2: was the claim paid",
                 "BGE 150 III 390", "BGE 147 III 486", "Never state or calculate a date",
                 "private credit agencies"):
        assert part in field.playbook
    assert {"schkg-8a", "schkg-149a", "schkg-85a", "schkg-86", "schkg-33", "schkg-73",
            "gebv-12b"} <= set(field.statutes)
    assert set(field.statutes) <= set(load_corpus())
    assert "credit_record" in FIXED_RESULTS
    assert {"R5-register-court", "R5-private-credit-agency"} <= set(config.SOFT_RULES)


def test_briefing_names_the_first_step_and_the_preliminary_check():
    from handover import briefing
    s, r = session(MISSED)
    offer = s.answer_form({M: "obstacle"})
    doc = briefing.render(s.case, offer.decision, TODAY, lang="de")
    assert "Wiederherstellung nach Art. 33 Abs. 4 SchKG" in doc
    assert "Vorprüfung nach festen Regeln" in doc
    assert "**Unverschuldet verhindert: Wiederherstellung der Frist: Sofort handeln**" in doc
    assert "Grund für den fehlenden Rechtsvorschlag: Ich war ohne mein Verschulden" in doc


def test_page_renders_the_questions_the_proposal_and_the_result():
    import shutil
    import subprocess
    from handover.view import reply_view
    if not shutil.which("node"):
        pytest.skip("Node.js is required for the frontend renderer test")
    replies = []
    for lang in ("de", "en"):
        s, r = session({}, lang)
        replies.append(reply_view(s, r))                       # gate 1, quick replies
        r = s.answer_form({E: "enforcement"})
        r = s.answer_form({P: "not_paid"})
        r = s.answer_form({O: "yes"})
        replies.append(reply_view(s, r))                       # the date: typed, no chips
        s.case.facts[D] = Fact(D, Status.KNOWN, LONG_AGO, "im Mai")
        r = s._decide_and_respond()
        replies.append(reply_view(s, r))                       # what the creditor did
        r = s.answer_form({C: "pending"})
        replies.append(reply_view(s, r))                       # proposal alongside
        r = s.answer_handover(False)
        replies.append(reply_view(s, r))                       # the result
        s, r = session({E: "enforcement"}, lang)
        replies.append(reply_view(s, s.answer_form({P: "paid_after"})))   # cites a decision
    result = subprocess.run(["node", "tests/web_form.cjs"], input=json.dumps(replies),
                            text=True, capture_output=True, check=False)
    assert result.returncode == 0, result.stderr + result.stdout
