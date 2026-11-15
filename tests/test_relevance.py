"""Which stored court decisions a briefing prints. No model, no network.

Every stored decision has its own condition on the established facts
(sources/case_law_selection.json, field "when"; handover/relevance.py). For each
decision the table below names one case in which it must be printed in full and
one in which it must not. Decisions marked "manual" are never printed in full.
"""
import json
from datetime import date
from pathlib import Path

import pytest

from handover import briefing
from handover.answer import load_corpus
from handover.relevance import MANUAL, NOT_MET, OPEN, check_when
from handover.rules import gate
from handover.schema import Case, Fact, Status

ROOT = Path(__file__).resolve().parent.parent
TODAY = date(2026, 11, 12)
CORPUS = load_corpus()
STORED = json.loads((ROOT / "sources" / "case_law.json").read_text(encoding="utf-8"))

COMMON = dict(jurisdiction="zurich", case_complexity=False, other_official_deadline=False)
# Late fees: a private letter, the person is in default by an agreed payment date, and
# only statutory default interest is claimed.
FEES = dict(document_type="reminder", claim_amount=400, principal_status="open",
            default_trigger="fixed_date", interest_charge="statutory",
            reminder_fee="none", collection_costs="none")
COURT = {**FEES, "document_type": "court_document"}
PAYMENT = dict(document_type="payment_order", claim_amount=400,
               document_received_date=date(2026, 11, 9), service_disputed=False,
               objection_filed=False)
REGISTER = dict(register_entry="enforcement", register_payment="not_paid",
                register_objection="yes", register_service_date=date(2026, 5, 1),
                register_creditor_step="none")
REGISTER_MISSED = dict(register_entry="enforcement", register_payment="not_paid",
                       register_objection="no", register_service_date=date(2026, 5, 1),
                       register_missed_reason="other")
ESTATE = dict(heir_basis="statutory",
              date_learned_of_death=date(2026, 11, 1), heir_knowledge_date=date(2026, 11, 1),
              disclaimer_filed=False, estate_actions="none", relationship="child",
              estate_insolvency="none_known", estate_finances="overindebted")
ESTATE_ACT = {**ESTATE, "estate_actions": "took"}
OBJECTED_TO_CREDITOR = {**PAYMENT, "objection_filed": True, "objection_date": date(2026, 11, 10),
                        "objection_recipient": "creditor", "objection_scope": "full"}
D, I, R = "debt_collection", "inheritance_debt", "credit_record"

# decision -> (legal area, facts with which it is printed, facts with which it is not)
CASES = {
    "bge-123-iii-241": (D, {**FEES, "collection_costs": "flat"}, FEES),
    "bge-129-iii-535": (D, {**FEES, "default_trigger": "reminder"}, FEES),
    "bger-4c-11-2003": (D, {**FEES, "collection_costs": "unsure"}, FEES),
    "bge-133-iii-598": (D, FEES, {**FEES, "principal_status": "disputed"}),
    "bger-5d-23-2017": (D, {**COURT, "reminder_fee": "not_agreed"}, COURT),
    "bge-136-iii-627": (D, COURT, {k: v for k, v in COURT.items() if k != "principal_status"}),
    "bge-120-iii-114": (D, {**PAYMENT, "service_disputed": True}, PAYMENT),
    "bger-5a-1052-2021": (D, {**PAYMENT, "service_disputed": True}, PAYMENT),
    "bger-5a-870-2019": (D, OBJECTED_TO_CREDITOR, PAYMENT),
    "bge-89-iii-10": (D, {**PAYMENT, "principal_status": "open"}, PAYMENT),
    "bger-5a-673-2017": (D, {**PAYMENT, "document_received_date": date(2026, 10, 1)}, PAYMENT),
    "bge-147-iii-486": (R, {**REGISTER, "register_payment": "paid_after"}, REGISTER),
    "bge-150-iii-390": (R, {**REGISTER, "register_payment": "paid_before"}, REGISTER),
    "og-so-scbes-2026-116": (R, {**REGISTER, "register_creditor_step": "lost"}, REGISTER),
    "bge-140-iii-481": (R, {**REGISTER_MISSED, "register_missed_reason": "abusive"},
                        REGISTER_MISSED),
    "bge-133-iii-1": (I, ESTATE_ACT, ESTATE),
    "bger-4a-110-2026-e321": (I, ESTATE_ACT, ESTATE),
    "og-zh-lb140092": (I, ESTATE_ACT, ESTATE),
    "bger-4a-394-2014": (I, {**ESTATE_ACT, "disclaimer_filed": True}, ESTATE_ACT),
    "bger-4a-110-2026-e315": (I, {**ESTATE, "estate_insolvency": "manifest"}, ESTATE),
    "bger-5a-823-2023": (I, {**ESTATE, "date_learned_of_death": date(2026, 6, 1),
                             "heir_knowledge_date": date(2026, 6, 1)}, ESTATE),
    "og-zh-lf240127": (I, {**ESTATE, "heir_knowledge_date": date(2026, 11, 3)}, ESTATE),
    "bger-5a-398-2021": (I, {**ESTATE, "disclaimer_filed": True}, ESTATE),
}
# decision -> (legal area, facts that raise its issue); listed as a pointer, never printed
MANUAL_CASES = {
    "bge-148-iii-57": (D, {**FEES, "reminder_fee": "agreed_amount"}),
    "bge-150-iii-223": (D, {**PAYMENT, "service_disputed": True}),
    "bge-109-iii-1": (D, {**PAYMENT, "service_disputed": True}),
    "bger-4a-110-2026-e322": (I, ESTATE_ACT),
    "og-zh-lf120057": (I, ESTATE_ACT),
}


def make(area, facts, unknown=()):
    c = Case(areas={area: "words of the person"})
    c.facts = {k: Fact(k, Status.KNOWN, v, "words of the person")
               for k, v in {**COMMON, **facts}.items()}
    for name in unknown:
        c.facts[name] = Fact(name, Status.USER_UNKNOWN)
    return c


def select(case):
    printed, pointers = briefing.select_decisions(case, gate(case, TODAY), CORPUS)
    key = {id(e): k for k, e in CORPUS.items()}
    return ({key[id(e)] for e, _ in printed},
            {key[id(e)]: state for e, state, _ in pointers})


def test_every_stored_decision_has_a_question_a_valid_condition_and_a_test_case():
    assert set(CASES) | set(MANUAL_CASES) == set(STORED)
    assert not set(CASES) & set(MANUAL_CASES)
    for key, e in STORED.items():
        assert e["question"].get("de") and e["question"].get("en"), key
        assert "ß" not in e["question"]["de"], key
        assert check_when(e["when"]) == [], (key, check_when(e["when"]))
        assert (e["when"] == "manual") == (key in MANUAL_CASES), key


def test_verified_file_matches_the_selection():
    # case_law.json is built by tools/verify_case_law.py; a condition changed in the
    # selection without running the tool would silently not apply.
    selection = json.loads((ROOT / "sources" / "case_law_selection.json").read_text(encoding="utf-8"))
    assert {e["id"] for e in selection} == set(STORED)
    for e in selection:
        assert STORED[e["id"]]["when"] == e["when"], e["id"]
        assert STORED[e["id"]]["question"] == e["question"], e["id"]


@pytest.mark.parametrize("key", sorted(CASES))
def test_decision_is_printed_only_when_its_condition_is_met(key):
    area, shown, hidden = CASES[key]
    printed, _ = select(make(area, shown))
    assert key in printed
    printed, _ = select(make(area, hidden))
    assert key not in printed


@pytest.mark.parametrize("key", sorted(MANUAL_CASES))
def test_decision_that_code_cannot_check_is_only_listed(key):
    area, facts = MANUAL_CASES[key]
    printed, pointers = select(make(area, facts))
    assert key not in printed and pointers[key] == MANUAL


def test_alternative_conditions():
    # The certificate of service matters when the date of service is not known.
    printed, _ = select(make(D, {k: v for k, v in PAYMENT.items() if k != "document_received_date"},
                             unknown=["document_received_date"]))
    assert "bger-5a-1052-2021" in printed and "bge-120-iii-114" not in printed
    # More than one year since service: the one-year period of Art. 88 para. 2 SchKG.
    printed, _ = select(make(R, {**REGISTER, "register_service_date": date(2025, 5, 1)}))
    assert "og-so-scbes-2026-116" in printed
    # A partial objection that was actually declared.
    printed, _ = select(make(D, {**OBJECTED_TO_CREDITOR, "objection_recipient": "office",
                                 "objection_scope": "partial", "objection_amount": 50}))
    assert "bge-89-iii-10" in printed


def test_states_open_and_not_met():
    # A fact the condition needs is not established: open. A fact that excludes it: not met.
    c = make(D, {k: v for k, v in FEES.items() if k != "collection_costs"})
    _, pointers = select(c)
    assert pointers["bge-123-iii-241"] == OPEN
    _, pointers = select(make(D, FEES))
    assert pointers["bge-123-iii-241"] == NOT_MET
    # "The user does not know" is not a contrary fact.
    c = make(D, {k: v for k, v in FEES.items() if k != "collection_costs"},
             unknown=["collection_costs"])
    assert select(c)[1]["bge-123-iii-241"] == OPEN


def test_no_decision_is_mentioned_when_its_issue_is_not_raised():
    # Thin case: the area is known, nothing else. No decision, not even a pointer.
    c = Case(areas={D: "a letter"})
    assert select(c) == (set(), {})
    # Private letter that claims no additional charge: the question of fees is not raised.
    assert select(make(D, {**FEES, "interest_charge": "none"})) == (set(), {})


def test_hand_over_of_2026_11_12_prints_no_decision():
    # Court letter, CHF 4,900, nothing else established. The old
    # mapping printed two decisions on the title for setting aside an objection.
    c = Case(areas={D: "x"})
    for k, v in dict(document_type="court_document", claim_amount=4900).items():
        c.facts[k] = Fact(k, Status.KNOWN, v, "words of the person")
    printed, pointers = select(c)
    assert printed == set()
    assert pointers == {"bger-5d-23-2017": OPEN, "bge-136-iii-627": OPEN}


@pytest.mark.parametrize("lang,because,other", [
    ("de", "Abgedruckt, weil", "Weitere hinterlegte Entscheide"),
    ("en", "Printed because", "Other stored decisions")])
def test_briefing_says_why_a_decision_is_printed_and_lists_the_others(lang, because, other):
    c = make(D, {**PAYMENT, "service_disputed": True})
    c.facts["service_disputed"].evidence = "nobody handed it to me"
    doc = briefing.render(c, gate(c, TODAY), TODAY, lang=lang)
    printed, rest = doc.split(other)
    assert "BGE 120 III 114" in printed and "BGE 150 III 223" not in printed
    assert because in printed and "«nobody handed it to me»" in printed
    assert STORED["bge-120-iii-114"]["question"][lang] in printed
    # Pointers: citation and question in one line, no passage.
    assert "BGE 150 III 223" in rest and STORED["bge-150-iii-223"]["question"][lang] in rest
    assert STORED["bge-150-iii-223"]["text"][:60] not in doc
