"""What the person and the legal team see around the hand-over (decided by the legal
lead on 2026-11-15): the priority class of the briefing, the required contact details,
the case number, and LexTec's conditions in plain words. No API key or network needed.
"""
from datetime import date, timedelta

import pytest

from handover import briefing, config, contact, priority, texts
from handover.demo import DEMO_CONTACT as PERSON
from handover.engine import Session, conditions_text
from handover.llm import FakeLLM
from handover.schema import Deadline, Decision, Fact, Reason, Route, Status

TODAY = date(2026, 11, 11)


def decision(*rules, urgent=False, emergency=False, deadlines=()):
    return Decision(Route.REFER, [Reason(r, "") for r in rules], deadlines=list(deadlines),
                    urgent=urgent, emergency=emergency)


def far_deadline(done=False):
    return Deadline(key="objection", label="objection", legal_basis="Art. 74 SchKG",
                    due=TODAY + timedelta(days=30), working_days_left=20, action_done=done)


# ---- priority class ------------------------------------------------------------------

@pytest.mark.parametrize("rules, kwargs, expected", [
    (["R1-user-wants-human"], {"urgent": True}, (1, "urgent")),          # urgent mark
    (["R2-distress"], {"urgent": True, "emergency": True}, (1, "emergency")),
    (["R3-area-outside-scope"], {"urgent": True}, (1, "urgent")),        # urgent wins
    (["R5-high-amount"], {}, (2, "legal")),                              # legal reason
    (["R5-estate-actions"], {}, (2, "legal")),
    (["R5-register-court"], {}, (2, "legal")),
    (["R1-user-wants-human", "R5-high-amount"], {}, (2, "legal")),       # one is enough
    (["R6-critical-fact-unresolved"], {}, (2, "legal")),
    (["R0-technical-failure"], {}, (2, "legal")),                        # not assessed
    (["R99-a-rule-added-later"], {}, (2, "legal")),                      # unknown: fail closed
    (["R1-user-wants-human"], {}, (3, "none")),
    (["R3-area-outside-scope"], {}, (3, "none")),
    (["R14-not-covered"], {}, (3, "none")),
    (["R8-no-progress"], {}, (3, "none")),
    (["R7-area-unidentified", "R9-round-limit"], {}, (3, "none")),
])
def test_priority_class_follows_the_agreed_mapping(rules, kwargs, expected):
    level, basis, _ = priority.classify(decision(*rules, **kwargs))
    assert (level, basis) == expected


def test_an_open_deadline_that_is_not_close_makes_the_case_important():
    assert priority.classify(decision("R1-user-wants-human",
                                      deadlines=[far_deadline()]))[:2] == (2, "deadline")
    # A step the person already took leaves no open deadline.
    assert priority.priority_class(decision("R1-user-wants-human",
                                            deadlines=[far_deadline(done=True)])) == 3


def test_class_three_is_not_called_unimportant():
    for lang in ("de", "en"):
        label = priority.LABELS[3][lang].lower()
        assert "wichtig" not in label and "important" not in label
        assert priority.BASIS["none"][lang]          # says that no deadline was checked


def test_briefing_names_the_class_and_the_rules_that_carry_it(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "OUTBOX_DIR", str(tmp_path))
    s = Session(FakeLLM([]), today=TODAY, language="de")
    s.request_human()
    done = s.answer_handover(True, contact=PERSON)
    assert "- **Priorität:** Klasse 3 – keine Frist bekannt – Das System hat keine Frist" in done.briefing
    assert "_P3_" in done.briefing_path.name
    s = Session(FakeLLM([]), today=TODAY, language="de")
    s.case.areas["debt_collection"] = "Mahnung"
    s.case.facts["claim_amount"] = Fact("claim_amount", Status.KNOWN, 9000, "CHF 9000")
    s.request_human()
    doc = s.answer_handover(True, contact=PERSON).briefing
    assert ("Klasse 2 – wichtig, nicht dringend – rechtlicher Übergabegrund ohne nahe Frist: "
            "Hoher Betrag") in doc


# ---- contact details -----------------------------------------------------------------

@pytest.mark.parametrize("raw, missing", [
    (PERSON, []),
    ({**PERSON, "phone": "+41 79 000 00 00"}, []),
    ({**PERSON, "first_name": "  "}, ["first_name"]),
    ({**PERSON, "last_name": "123"}, ["last_name"]),
    ({**PERSON, "email": "max.muster"}, ["email"]),
    ({**PERSON, "email": "max@example"}, ["email"]),
    ({**PERSON, "email": "max muster@example.org"}, ["email"]),
    ({}, ["first_name", "last_name", "email"]),
    (None, ["first_name", "last_name", "email"]),
    ("079 000 00 00", ["first_name", "last_name", "email"]),      # the earlier free text
    ({"first_name": 1, "last_name": ["x"], "email": None}, ["first_name", "last_name", "email"]),
])
def test_first_name_surname_and_email_are_required_phone_is_not(raw, missing):
    assert contact.problems(contact.clean(raw)) == missing


def test_details_are_trimmed_and_limited():
    c = contact.clean({"first_name": "  Anna   Maria ", "last_name": "x" * 500,
                       "email": " a@b.ch ", "phone": "079\n000"})
    assert c == {"first_name": "Anna Maria", "last_name": "x" * 80, "email": "a@b.ch",
                 "phone": "079 000"}


@pytest.mark.parametrize("lang", ["de", "en"])
def test_yes_without_details_passes_nothing_on_and_says_what_is_needed(lang, tmp_path, monkeypatch):
    monkeypatch.setattr(config, "OUTBOX_DIR", str(tmp_path))
    s = Session(FakeLLM([]), today=TODAY, language=lang)       # any model call would raise
    offer = s.request_human()
    assert texts.CONTACT_NOTE[lang] in offer.text and texts.HANDOVER_SENT_NOTE[lang] in offer.text
    assert [f["name"] for f in offer.data["contact"]["fields"] if f["required"]] == [
        "first_name", "last_name", "email"]
    r = s.answer_handover(True, contact={"first_name": "Anna", "last_name": "Beispiel"})
    assert r.kind == "handover_contact" and r.route is Route.REFER
    assert not s.closed and s.handover == "offered" and not list(tmp_path.iterdir())
    assert r.data["problems"] == [texts.CONTACT_ERRORS["email"][lang]]
    assert texts.CONTACT_ERRORS["email"][lang] in r.text and not s.case.contact
    # The person can still say no; then nothing is kept for a hand-over.
    assert s.answer_handover(False).kind == "refer_declined"
    assert not list(tmp_path.iterdir()) and not s.case.case_number


# ---- case number ---------------------------------------------------------------------

def test_case_number_is_dated_unambiguous_and_unique_in_the_outbox(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "OUTBOX_DIR", str(tmp_path))
    numbers = {briefing.new_case_number(TODAY) for _ in range(200)}
    assert len(numbers) > 190
    for n in numbers:
        prefix, day, tail = n.split("-")
        assert (prefix, day, len(tail)) == ("LX", "20261111", 4)
        assert not set(tail) & set("01OIL")                    # easily confused characters
    # A number that already names a briefing in the outbox is not given again.
    taken = "LX-20261111-AAAA"
    (tmp_path / f"briefing_x_P1_{taken}.md").write_text("x")
    monkeypatch.setattr(briefing, "_CASE_ALPHABET", "A")
    with pytest.raises(RuntimeError):
        briefing.new_case_number(TODAY)


@pytest.mark.parametrize("lang", ["de", "en"])
def test_person_sees_the_case_number_and_how_to_ask_about_the_matter(lang, tmp_path, monkeypatch):
    monkeypatch.setattr(config, "OUTBOX_DIR", str(tmp_path))
    s = Session(FakeLLM([]), today=TODAY, language=lang)
    s.request_human()
    done = s.answer_handover(True, contact=PERSON)
    number = s.case.case_number
    assert done.kind == "refer" and done.data["case_number"] == number
    assert f"{texts.CASE_NUMBER_LABEL[lang]}: {number}" in done.text
    assert texts.LEXTEC_CONTACT_EMAIL in done.text
    # The briefing is German whatever the person's language.
    assert f"Fallnummer: {number}" in done.briefing and number in done.briefing_path.name
    assert done.briefing_path.read_text() == done.briefing


def test_mail_subject_carries_class_urgency_and_case_number(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "OUTBOX_DIR", str(tmp_path))
    sent = []

    class Server:
        def __init__(self, *a): pass
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def starttls(self): pass
        def send_message(self, msg): sent.append(msg)

    monkeypatch.setattr(briefing.smtplib, "SMTP", Server)
    monkeypatch.setenv("SMTP_HOST", "mail.invalid")
    monkeypatch.setenv("BRIEFING_TO", "team@example.org")
    monkeypatch.delenv("SMTP_USER", raising=False)
    path, mailed = briefing.deliver("text", True, case_number="LX-20261111-7K3F", priority=1)
    assert mailed and path.name.endswith("_P1_LX-20261111-7K3F.md")
    assert sent[0]["Subject"] == "[P1] [URGENT] Case briefing from intake system LX-20261111-7K3F"
    # Called as before (no class, no number), nothing is added.
    path, _ = briefing.deliver("text", False)
    assert "_P" not in path.name and sent[1]["Subject"] == "Case briefing from intake system"


# ---- LexTec's conditions ---------------------------------------------------------------

@pytest.mark.parametrize("lang", ["de", "en"])
def test_proposal_states_prices_main_rules_and_links_the_full_terms(lang):
    s = Session(FakeLLM([]), today=TODAY, language=lang)
    offer = s.request_human()
    d = offer.data
    assert d["conditions"] == texts.HANDOVER_CONDITIONS[lang]
    assert d["rules"] == texts.HANDOVER_RULES[lang] and len(d["rules"]) == 6
    assert d["terms_url"] == "https://lextec-rechtsberatung.ch/datenschutz-agb/"
    assert conditions_text(lang) in offer.text
    for part in (d["conditions"], *d["rules"], d["terms_url"], d["terms_label"]):
        assert part in offer.text
    # Prices of the website and the figures of the terms, each stated once.
    for figure in ("CHF 45", "CHF 85", "15", "48", "10", "5 %", "CHF 30"):
        assert figure in offer.text
    # The proposal says that the yes itself costs nothing and that no response time is promised.
    assert ("kostet nichts" if lang == "de" else "costs nothing") in d["conditions"]
    assert ("feste Antwortzeit" if lang == "de" else "fixed response time") in d["rules"][-1]


def test_rules_are_short_plain_sentences_not_the_wording_of_the_terms():
    # Words of the AGB that a layperson may not know are not taken over.
    for word in ("Klient", "rückerstattungsfähig", "No-Show", "konsumiert", "Verzugszins",
                 "BGFA", "Honorar", "Mandat"):
        assert all(word not in rule for rule in texts.HANDOVER_RULES["de"]), word
    for lang in ("de", "en"):
        for rule in texts.HANDOVER_RULES[lang]:
            assert len(rule) <= 230 and "ß" not in rule
