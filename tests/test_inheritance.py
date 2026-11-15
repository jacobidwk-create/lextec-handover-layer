"""Declining an inheritance: the four gates of the legal lead's flow (full_report.md section 3.4b).

No model, no network. Built like the late-fee tests: the questions are part of the
conversation with quick replies, the route comes from fixed rules, and the result
comes from fixed texts (handover/inheritance.py).
"""
from datetime import date

import pytest

from handover import config, inheritance, knowledge, texts
from handover.answer import classify_structured, load_corpus
from handover.areas import FIELD_BY_NAME, UNKNOWN_CHOICE, disclaimer_state, required_fields
from handover.engine import Session
from handover.legal_fields import REGISTRY
from handover.llm import FakeLLM
from handover.rules import gate
from handover.schema import Case, Fact, Route, Status

TODAY = date(2026, 11, 13)
OPEN = dict(heir_basis="statutory", date_learned_of_death=date(2026, 10, 20))      # ends 20.01.2027
LATE_FOR_INVENTORY = dict(heir_basis="statutory", date_learned_of_death=date(2026, 9, 1))
CLOSE = dict(heir_basis="statutory", date_learned_of_death=date(2026, 8, 20))      # ends 20.11.2026
PASSED = dict(heir_basis="statutory", date_learned_of_death=date(2026, 6, 1))      # ended 01.09.2026


def case(**facts):
    c = Case(areas={"inheritance_debt": "my father died"})
    for name, value in facts.items():
        c.facts[name] = (Fact(name, Status.USER_UNKNOWN) if value is None
                         else Fact(name, Status.KNOWN, value, "words of the person"))
    return c


def session(lang="de", **facts):
    s = Session(FakeLLM([]), today=TODAY, language=lang, answerer=classify_structured)
    s.case = case(**facts)
    s.case.language = lang
    return s, s._decide_and_respond()


def keys(c):
    d = gate(c, TODAY)
    a = inheritance.assess(c, d, "de")
    return [p["key"] for p in a["positions"]], [n["key"] for n in a["notes"]]


# ---- gate 1: the period ---------------------------------------------------------------

def test_first_how_the_person_became_an_heir_then_the_date_that_fits():
    assert gate(case(), TODAY).questions == ["heir_basis"]
    for basis, fact in (("statutory", "date_learned_of_death"),
                        ("appointed", "appointment_notice_date"),
                        ("successor", "heir_knowledge_date")):
        assert gate(case(heir_basis=basis), TODAY).questions == [fact]


@pytest.mark.parametrize("basis,fact", [("statutory", "date_learned_of_death"),
                                         ("appointed", "appointment_notice_date"),
                                         ("successor", "heir_knowledge_date")])
def test_three_months_run_from_the_start_that_fits_the_heir(basis, fact):
    c = case(**{"heir_basis": basis, fact: date(2026, 10, 20)})
    d = gate(c, TODAY)
    period = next(x for x in d.deadlines if x.key == "disclaimer")
    assert period.due == date(2027, 1, 20) and period.legal_basis == "Art. 567 ZGB"
    assert next(x for x in d.deadlines if x.key == "inventory").due == date(2026, 11, 20)
    assert disclaimer_state(c) == "open" and not d.urgent
    assert keys(c)[0] == ["period_" + basis]


def test_unknown_heir_basis_or_date_fails_closed():
    for c in (case(heir_basis=None), case(heir_basis="statutory", date_learned_of_death=None)):
        d = gate(c, TODAY)
        assert d.route is Route.REFER and d.urgent           # a period may be running
        assert [r.rule for r in d.reasons] == ["R6-critical-fact-unresolved"]


def test_period_close_gets_an_urgent_notice_and_the_conversation_continues():
    s, r = session(**CLOSE)
    assert r.route is Route.ASK and r.decision.urgent
    assert r.decision.questions[0] == "estate_actions"
    assert any(x.rule == "U2-disclaimer-period" for x in r.decision.reasons)
    notice = r.data["next_steps"][0]
    assert notice["title"] == texts.ESTATE_NEXT_TITLE["de"]
    assert "20.08.2026" in notice["paragraphs"][1] and "20.11.2026" in notice["paragraphs"][1]
    assert texts.ESTATE_WHERE["de"] in r.text and texts.ESTATE_CONTINUE["de"] in r.text
    # Not close: no notice.
    s, r = session(**OPEN)
    assert not r.decision.urgent and not r.data["next_steps"]


# ---- gate 1B: the period may have passed ------------------------------------------------

def test_passed_period_asks_about_manifest_insolvency_first():
    s, r = session(**PASSED)
    assert r.route is Route.ASK and r.decision.questions[0] == "estate_insolvency"
    assert r.decision.urgent                                 # until it is answered
    q = r.data["questions"][0]
    assert [o["value"] for o in q["options"]] == ["manifest", "none_known", UNKNOWN_CHOICE]
    assert [t["topic"] for t in q["terms"]] == ["term_zahlungsunfaehig", "term_verlustschein",
                                                "term_fristverlaengerung"]


def test_manifest_insolvency_means_presumed_disclaimer_and_nothing_urgent():
    c = case(**PASSED, estate_insolvency="manifest", estate_actions="none")
    d = gate(c, TODAY)
    assert d.route is Route.PROCEED and not d.urgent
    positions, notes = keys(c)
    assert positions == ["presumed", "actions_safe"] and notes == ["children", "gifts"]
    assert "estate_finances" not in [f.name for f in required_fields(c)]


@pytest.mark.parametrize("answer", ["none_known", None])
def test_passed_without_manifest_insolvency_gets_notice_and_a_hand_over_proposal(answer):
    s, r = session(**PASSED)
    r = s.answer_form({"estate_insolvency": UNKNOWN_CHOICE if answer is None else answer})
    assert r.kind == "refer_offer" and r.decision.urgent
    assert [x.rule for x in r.decision.reasons] == ["R4-disclaimer-passed"]
    assert r.data["reasons"] == [texts.REFER_WHY["R4-disclaimer-passed"]["de"]]
    notice = r.data["next_steps"][0]
    assert texts.ESTATE_PASSED["de"] in notice["paragraphs"] and "Art. 576 ZGB" in r.text
    assert r.data["conditions"]                              # LexTec's conditions
    # Declined: the conversation continues, the notice stays, the proposal is not repeated.
    r = s.answer_handover(False)
    assert r.kind == "ask" and r.decision.questions == ["estate_actions"] and r.decision.urgent
    assert "R4-disclaimer-passed" in s.case.declined_rules
    r = s.answer_form({"estate_actions": "none"})
    assert r.route is Route.PROCEED and r.decision.urgent
    a = r.data["assessment"]
    assert [p["key"] for p in a["positions"]] == ["period_passed", "actions_safe"]
    assert a["positions"][0]["verdict"] == "act_now"
    assert r.data["next_steps"]                              # the notice is still shown


# ---- gate 2: interference ------------------------------------------------------------------

@pytest.mark.parametrize("answer,verdict", [("took", "at_risk"), ("unsure", "case_by_case"),
                                            (None, "case_by_case")])
def test_possible_interference_is_explained_and_the_hand_over_proposed(answer, verdict):
    s, r = session(**OPEN)
    r = s.answer_form({"estate_actions": UNKNOWN_CHOICE if answer is None else answer})
    assert r.kind == "refer_offer" and not r.decision.urgent
    assert [x.rule for x in r.decision.reasons] == ["R5-estate-actions"]
    why = r.data["reasons"][0]
    assert "kann die Erbschaft nicht mehr ausschlagen" in why and "hängt vom Einzelfall ab" in why
    # Declined: gate 3 follows, and the result still says what the acts can mean.
    r = s.answer_handover(False)
    assert r.kind == "ask" and r.decision.questions == ["estate_finances"]
    r = s.answer_form({"estate_finances": "overindebted"})
    assert r.route is Route.PROCEED
    took = next(p for p in r.data["assessment"]["positions"] if p["key"] == "actions_took")
    assert took["verdict"] == verdict
    assert "sollte ein:e Rechtsberater:in beurteilen" in took["text"]


@pytest.mark.parametrize("answer", ["none", "administration"])
def test_necessary_administration_keeps_the_right_to_disclaim(answer):
    c = case(**OPEN, estate_actions=answer, estate_finances="overindebted")
    assert gate(c, TODAY).route is Route.PROCEED
    assert "actions_safe" in keys(c)[0]


def test_took_read_from_free_text_is_confirmed_before_the_proposal():
    out = {"language": "de", "areas": [],
           "facts": {"estate_actions": {"value": "took", "evidence": "sein Auto verkauft"}}}
    s = Session(FakeLLM([out]), today=TODAY, answerer=classify_structured)
    s.case = case(**OPEN, estate_finances="overindebted")
    s._decide_and_respond()
    s.case.last_asked = []                                   # volunteered, not asked
    r = s.step("Ich habe übrigens sein Auto verkauft.")
    assert r.route is Route.ASK and r.data["questions"][0]["understood"] == "took"
    assert s.answer_form({"estate_actions": "administration"}).route is Route.PROCEED


# ---- gate 3: the finances of the estate -------------------------------------------------

@pytest.mark.parametrize("facts,finances,finding,notes", [
    (OPEN, "overindebted", "finances_overindebted", ["children", "gifts"]),
    (OPEN, "uncertain", "finances_uncertain_inventory",
     ["children", "gifts", "own_debts", "benefits"]),
    (OPEN, None, "finances_uncertain_inventory", ["children", "gifts", "own_debts", "benefits"]),
    (LATE_FOR_INVENTORY, "uncertain", "finances_uncertain_late",
     ["children", "gifts", "own_debts", "benefits"]),
    (OPEN, "solvent", "finances_solvent", ["children", "own_debts", "benefits"]),
])
def test_each_state_of_the_finances_has_its_result_and_its_traps(facts, finances, finding, notes):
    c = case(**facts, estate_actions="none", estate_finances=finances)
    assert gate(c, TODAY).route is Route.PROCEED             # "I do not know" = uncertain
    positions, shown = keys(c)
    assert positions[-1] == finding and shown == notes


def test_result_card_and_text_carry_sources_dates_and_terms():
    s, r = session(**OPEN, estate_actions="none")
    r = s.answer_form({"estate_finances": "uncertain"})
    assert r.kind == "proceed"
    a = r.data["assessment"]
    assert a["title"] == inheritance.T["title"]["de"] and a["summary"] == inheritance.T["open"]["de"]
    inv = a["positions"][-1]
    assert [c["citation"] for c in inv["citations"]] == ["Art. 580 ZGB", "Art. 588 ZGB",
                                                         "Art. 589 ZGB"]
    assert all(c["url"].startswith("https://www.fedlex.admin.ch/") for c in inv["citations"])
    assert [t["topic"] for t in inv["terms"]] == ["term_oeffentliches_inventar",
                                                  "term_amtliche_liquidation"]
    assert a["notes"][-1]["citations"][0]["url"].endswith("/cc/2007/804/de#art_11_a")
    # The dates come from the deadline computation, not from the texts.
    assert {(d["label"], d["due"]) for d in r.data["deadlines"]} == {
        ("Ausschlagung der Erbschaft", "20.01.2027"),
        ("Gesuch um öffentliches Inventar", "20.11.2026")}
    assert "öffentliches Inventar" in r.text and not r.data["statements"]
    assert s.llm.calls == []                                 # no model wrote any of it


# ---- texts and field file ----------------------------------------------------------------

def test_texts_are_bilingual_plain_and_cite_only_stored_articles():
    corpus = load_corpus()
    for table in (inheritance.FINDINGS, inheritance.NOTES):
        for key, e in table.items():
            for lang in ("de", "en"):
                assert e["title"][lang] and e["text"][lang], key
            assert "ß" not in e["title"]["de"] + e["text"]["de"], key
            assert e.get("verdict", "running") in inheritance.VERDICTS, key
            for law, art, _ in e["sources"]:
                assert f"{law}-{art}" in corpus, (key, law, art)
                assert knowledge.fedlex_url(law, art, "de").startswith("https://www.fedlex")
            assert all(t in knowledge.ENTRIES for t in e["terms"]), key


def test_questions_have_quick_replies_terms_and_the_field_file_carries_the_flow():
    for name in ("heir_basis", "estate_insolvency", "estate_actions", "estate_finances"):
        spec = FIELD_BY_NAME[name]
        assert set(spec.options) == set(spec.choices) and spec.terms, name
        assert all(t in knowledge.ENTRIES for t in spec.terms), name
    field = REGISTRY["inheritance_debt"]
    assert field.title == {"de": "Erbschaft ausschlagen", "en": "Declining an inheritance"}
    for part in ("Gate 1: is the three-month period still open", "Gate 2: did the heir lose",
                 "Gate 3: what is known about the finances", "Gate 4: traps on disclaiming",
                 "Never state or calculate a date"):
        assert part in field.playbook
    assert {"zgb-572", "zgb-575", "zgb-578", "zgb-593", "elg-11a"} <= set(field.statutes)
    assert "inheritance_debt" in __import__("handover.areas").areas.NO_COMMON_QUESTIONS


def test_soft_rules_are_exactly_the_alongside_proposals():
    assert set(config.SOFT_RULES) == {"R14-not-covered", "R4-disclaimer-passed",
                                      "R5-estate-actions", "R5-register-court",
                                      "R5-private-credit-agency"}


def test_briefing_names_the_first_step_and_the_preliminary_check():
    from handover import briefing
    s, r = session(**PASSED)
    offer = s.answer_form({"estate_insolvency": "none_known"})
    doc = briefing.render(s.case, offer.decision, TODAY, lang="de")
    assert doc.startswith("# DRINGEND")
    assert "sofort Gesuch um Fristverlängerung" in doc
    assert "Vorprüfung nach festen Regeln" in doc and "**Frist abgelaufen: Sofort handeln**" in doc
    assert "Zahlungsunfähigkeit beim Tod: Nein, davon ist mir nichts bekannt." in doc
