"""The model leads, the rules guard (full_report.md section 3.12). No live model, no network.

The tests feed the checks deliberately bad model output and confirm that each rail
catches it, and that what the rules decide (urgency, deadlines, hand-over, the fixed
result) stays outside the model's reach.
"""
import json
import shutil
import subprocess
from datetime import date
from pathlib import Path

import pytest

from handover import briefing, compose, config, legal_fields, texts
from handover.demo import DEMO_CONTACT as PERSON
from handover.answer import classify_structured, load_corpus
from handover.areas import AREAS, AREA_LABELS, FIELD_BY_NAME, needs_confirmation
from handover.engine import Session
from handover.llm import FakeLLM
from handover.rules import gate
from handover.schema import Case, Fact, Route, Status
from handover.view import reply_view

TODAY = date(2026, 11, 13)
CORPUS = load_corpus()
QUOTE_104 = "so hat er Verzugszinse zu fünf vom Hundert für das Jahr zu bezahlen"
D = {"area": "debt_collection", "evidence": "Inkassobüro"}


def fact(value, evidence):
    return {"value": value, "evidence": evidence}


def debt_case(**facts):
    c = Case(areas={"debt_collection": "a letter"})
    for name, value in facts.items():
        c.facts[name] = Fact(name, Status.KNOWN, value, "words of the person")
    return c


def legal(text="Im Verzug ist ein Zins von fünf Prozent pro Jahr vorgesehen.",
          source="or-104", quote=QUOTE_104):
    return {"type": "legal", "text": text, "source_id": source, "quote": quote}


def talk(text):
    return {"type": "talk", "text": text}


def run_check(segments, verdicts=None, case=None):
    """Apply the rails to a draft; returns (segments shown, audit, number of model calls)."""
    case = case or debt_case(document_type="reminder")
    llm = FakeLLM([] if verdicts is None else [verdicts])
    shown = compose.check(llm, case, {"segments": segments}, compose.sources_for(case, CORPUS))
    return shown, case.audit, len(llm.calls)


# ---- rails applied by code -------------------------------------------------------

@pytest.mark.parametrize("bad", [
    legal(source="or-999"),                                  # an article that is not stored
    legal(source="zgb-566"),                                 # stored, but not for this field
    legal(quote="Der Schuldner zahlt immer fünf Prozent."),  # a quote that is not in the article
    legal(quote="fünf vom Hund"),                            # too short to pin anything
    {"type": "legal", "text": "Fünf Prozent sind geschuldet."},   # no source at all
    talk("Nach Art. 104 OR ist das so."),                    # an article in talk
    talk("Die Gebühr von 350 Franken ist hoch."),            # an amount the person never wrote
    talk("Das sind fünf Prozent, also 5 % im Jahr."),        # a percentage
    talk("Sie haben dafür 10 Tage."),                        # a period
    talk("Das wäre dann im November."),                      # a date in words
    talk("Die Mahngebühr ist nicht geschuldet."),            # a verdict in talk
    talk("Sie haben zehn Tage Zeit, bis zum 23.11.2026."),   # a date in talk
    talk("Die Frist läuft bald ab."),                        # a deadline in talk
    talk("Sie müssen das nicht bezahlen."),                  # advice in talk
    talk("Keine Sorge, das kommt gut."),                     # reassurance about the outcome
    talk("x" * 800),                                         # too long
    {"type": "advice", "text": "Zahlen Sie nicht."},         # unknown kind
    "not an object",
])
def test_bad_segment_is_dropped_by_code_without_asking_the_checker(bad):
    shown, audit, calls = run_check([bad])
    assert shown == [] and calls == 0
    assert bad == "not an object" or any("rejected" in line for line in audit)


def test_statement_with_source_and_quote_passes_and_carries_its_link():
    ok = {"results": [{"index": 0, "legal_claim": False},
                      {"index": 1, "supported": True, "relevant": True}]}
    shown, _, calls = run_check([talk("Danke, das hilft mir weiter."), legal()], ok)
    assert calls == 1 and [s["type"] for s in shown] == ["talk", "legal"]
    assert shown[1]["citation"] == "Art. 104 OR"
    assert shown[1]["url"].startswith("https://www.fedlex.admin.ch/") and "quote" not in shown[1]


def test_talk_may_name_an_amount_the_person_wrote_but_no_other_number():
    c = debt_case(document_type="reminder")
    c.messages = [("user", "Sie wollen 200 Franken für die Rechnung und CHF 4'900.00 Gebühr, "
                           "zahlbar in 10 Tagen.")]
    ok = {"results": [{"index": 0, "legal_claim": False}]}
    for text in ("Sie nennen eine Gebühr von CHF 200 zusätzlich zur Rechnung.",
                 "Zu den 4900 Franken habe ich eine Rückfrage."):
        shown, _, _ = run_check([talk(text)], ok, case=c)
        assert [s["text"] for s in shown] == [text]
    assert compose.numbers_ok("CHF 4'900.– und 200.00", c.user_text())
    assert not compose.numbers_ok("CHF 201", c.user_text())
    assert not compose.numbers_ok("in 10 Tagen", c.user_text())      # a period, even if quoted
    question = {"type": "question", "text": "Wofür genau sind die CHF 200, die dazukommen?"}
    shown, _, _ = run_check([question], ok, case=c)
    assert shown == [{"type": "question", "text": question["text"]}]


def test_at_most_five_segments_are_considered():
    many = [talk(f"Satz {w}.") for w in ("eins", "zwei", "drei", "vier", "fünf", "sechs", "sieben")]
    ok = {"results": [{"index": i, "legal_claim": False} for i in range(7)]}
    shown, audit, _ = run_check(many, ok)
    assert len(shown) == compose.MAX_SEGMENTS and any("too many" in line for line in audit)


# ---- rails applied by the checking model ------------------------------------------

@pytest.mark.parametrize("verdicts", [
    {"results": [{"index": 0, "supported": False, "relevant": True}]},
    {"results": [{"index": 0, "supported": True, "relevant": False}]},
    {"results": []},                                         # no verdict is not a pass
    {"results": "nonsense"},
    TimeoutError(),                                          # the checker is unavailable
])
def test_legal_statement_needs_an_explicit_pass_from_the_checker(verdicts):
    shown, _, calls = run_check([legal()], verdicts)
    assert shown == [] and calls == 1


@pytest.mark.parametrize("verdict", [{"index": 0, "legal_claim": True}, {"index": 0}])
def test_talk_that_the_checker_calls_a_legal_claim_is_dropped(verdict):
    shown, _, _ = run_check([talk("Solche Gebühren zahlt man eigentlich nie.")],
                            {"results": [verdict]})
    assert shown == []


# ---- the model cannot touch what the rules decide -----------------------------------

def session(answers, **kw):
    return Session(FakeLLM(answers), today=TODAY, answerer=classify_structured, compose=True, **kw)


LOOSE = "Ich habe einen Zahlungsbefehl bekommen, 900 Franken für mein Fitnessabo."
LOOSE_OUT = {"language": "de", "areas": [{"area": "debt_collection", "evidence": "Fitnessabo"}],
             "facts": {"document_type": fact("payment_order", "einen Zahlungsbefehl bekommen")}}


def test_reply_falls_back_to_the_fixed_text_when_the_model_fails():
    s = session([LOOSE_OUT, TimeoutError()])
    r = s.step(LOOSE)
    assert r.route is Route.ASK and r.data["segments"] == []
    assert r.data["ack"] == texts.ACK_FALLBACK["de"]
    assert any("reply draft failed" in line for line in s.case.audit)


def test_a_payment_order_read_from_free_text_is_confirmed_before_anything_is_urgent():
    s = session([LOOSE_OUT, {"segments": []}])
    r = s.step(LOOSE)
    assert r.route is Route.ASK and not r.decision.urgent and not r.data["next_steps"]
    q = r.data["questions"][0]
    assert q["name"] == "document_type" and q["understood"] == "payment_order"
    assert q["confirm_note"] == texts.CONFIRM_NOTE["de"]
    assert needs_confirmation(s.case, "document_type")
    # In the conversation the questions come one at a time.
    assert [x["name"] for x in r.data["questions"]] == ["document_type"]
    # "No, that is not it": the person chooses the collection agency. Nothing was urgent.
    r = s.answer_form({"document_type": "reminder"})
    assert r.route is Route.ASK and not r.decision.urgent
    assert [x["name"] for x in r.data["questions"]] == ["principal_status"]
    r = s.answer_form({"principal_status": "disputed"})
    assert r.route is Route.PROCEED and not r.decision.urgent
    assert not needs_confirmation(s.case, "document_type")


def test_a_typed_correction_replaces_the_fact():
    fix = {"language": "de", "areas": [],
           "facts": {"document_type": fact("reminder", "es ist vom Inkassobüro des Fitnessstudios")}}
    s = session([LOOSE_OUT, {"segments": []}, fix, {"segments": []}])
    s.step(LOOSE)
    r = s.step("Nein, es ist vom Inkassobüro des Fitnessstudios, nicht vom Amt.")
    assert s.case.value("document_type") == "reminder" and not r.decision.urgent
    assert r.route is Route.ASK and "document_type" not in r.decision.questions


def test_urgent_notice_is_added_by_the_engine_whatever_the_model_writes():
    calm = {"segments": [talk("Das ist alles halb so wild, lassen Sie sich Zeit.")]}
    passed = {"results": [{"index": 0, "legal_claim": False}]}
    s = session([LOOSE_OUT, {"segments": []},
                 {"language": "de", "areas": [], "facts": {}}, calm, passed])
    s.step(LOOSE)
    s.answer_form({"document_type": "payment_order"})          # confirmed: now urgent
    r = s.step("Okay.")
    assert r.decision.urgent and r.data["urgent"]
    assert r.data["segments"][0]["text"].startswith("Das ist alles halb so wild")
    assert r.data["next_steps"] and "Zahlungsbefehl" in r.data["next_steps"][0]["title"]
    assert r.text.index(r.data["next_steps"][0]["title"]) < r.text.index("halb so wild")


def test_an_old_sentence_cannot_confirm_a_reopened_answer():
    s = session([LOOSE_OUT, {"segments": []}])
    s.step(LOOSE)
    s.answer_form({"document_type": "payment_order"})
    r = s.revise("document_type")                               # "that is not right"
    assert r.route is Route.ASK and r.decision.questions == ["document_type"]
    assert s.case.fact("document_type").status is Status.MISSING and not r.decision.urgent
    # The model reads the old sentence again. That does not count as the person's answer.
    s.llm = FakeLLM([{**LOOSE_OUT, "areas": []}, {"segments": []}])
    r = s.step("Moment, ich schaue nach.")
    assert needs_confirmation(s.case, "document_type") and not r.decision.urgent


def test_revise_needs_no_model_and_only_reopens_list_answers():
    s = Session(FakeLLM([]), today=TODAY, answerer=classify_structured)
    s.case = debt_case(document_type="reminder", principal_status="paid_on_time", claim_amount=90.0)
    assert s._decide_and_respond().route is Route.PROCEED
    for bad in ("claim_amount", "default_trigger", "nope"):       # no list, not answered, unknown
        with pytest.raises(ValueError):
            s.revise(bad)
    r = s.revise("principal_status")
    assert r.route is Route.ASK and r.data["ack"] == texts.REVISE_ACK["de"]
    assert s.llm.calls == [] and "principal_status" in r.decision.questions
    r = s.answer_form({"principal_status": "open", "default_trigger": "none"})
    assert r.route is Route.PROCEED and r.kind == "proceed"       # a new result, not a repeat
    names = {x["name"]: x["revisable"] for x in r.data["understood"]["items"]}
    assert names == {"document_type": True, "principal_status": True, "claim_amount": False,
                     "default_trigger": True}


def test_fixed_result_is_shown_whatever_the_model_writes_around_it():
    draft = {"segments": [talk("Danke für Ihre Geduld."),
                          legal("Die Inkassokosten sind in jedem Fall geschuldet.",
                                "or-106", "Hat der Gläubiger einen grösseren Schaden erlitten")]}
    verdict = {"results": [{"index": 0, "legal_claim": False},
                           {"index": 1, "supported": False, "relevant": True}]}
    out = {"language": "de", "areas": [],
           "facts": {"collection_costs": fact("flat", "eine Pauschale ohne Belege")}}
    s = session([out, draft, verdict])
    s.case = debt_case(document_type="reminder", principal_status="open",
                       default_trigger="reminder", interest_charge="none", reminder_fee="none")
    s._decide_and_respond()
    r = s.step("Es ist eine Pauschale ohne Belege.")
    assert r.kind == "proceed"
    assert [p["verdict"] for p in r.data["assessment"]["positions"]] == ["not_owed"]
    assert [x["type"] for x in r.data["segments"]] == ["talk"]     # the false statement is gone
    assert "in jedem Fall geschuldet" not in r.text


def test_model_gets_the_playbook_and_only_the_sources_of_the_field():
    s = session([LOOSE_OUT, {"segments": []}])
    s.step(LOOSE)
    system, user = s.llm.calls[1]
    assert system == compose.SYSTEM
    assert "Late fees: the three gates" in user and "Gate 1: who sent the letter" in user
    assert "[or-104] Art. 104 OR" in user and "[uwg-8] Art. 8 UWG" in user
    assert "[zgb-566]" not in user and "[schkg-93]" not in user     # other fields
    # The model is handed the next question to ask, with the answers offered as quick replies.
    assert '"route": "ASK"' in user and '"ask_next"' in user
    assert FIELD_BY_NAME["document_type"].question["de"] in user
    assert FIELD_BY_NAME["document_type"].options["reminder"]["de"] in user


# ---- the question is part of the conversation ------------------------------------------

def test_model_asks_the_next_question_in_its_own_words_and_the_fixed_wording_is_the_fallback():
    own = "Darf ich zuerst fragen, von wem der Brief kommt?"
    draft = {"segments": [talk("Danke für Ihre Nachricht."), {"type": "question", "text": own}]}
    ok = {"results": [{"index": 0, "legal_claim": False}, {"index": 1, "legal_claim": False}]}
    m = "Ich habe einen Brief wegen einer Rechnung bekommen."
    out = {"language": "de", "facts": {},
           "areas": [{"area": "debt_collection", "evidence": "wegen einer Rechnung"}]}
    s = session([out, draft, ok])
    r = s.step(m)
    q = r.data["questions"]
    assert len(q) == 1 and q[0]["name"] == "document_type" and q[0]["asked"] == own
    assert [x["type"] for x in r.data["segments"]] == ["talk"] and r.data["intro"] == ""
    assert own in r.text and texts.OPTIONS_LABEL["de"] in r.text       # the record keeps it
    assert s.case.last_asked == ["document_type"]
    # A question with law or a number in it, or one the checker rejects: fixed wording.
    fixed = FIELD_BY_NAME["document_type"].question["de"]
    for bad, verdicts in (
            ({"type": "question", "text": "Haben Sie innert 10 Tagen Rechtsvorschlag erhoben?"}, None),
            ({"type": "question", "text": "Bitte nennen Sie den Absender."}, None),      # no question
            ({"type": "question", "text": own}, {"results": [{"index": 0, "legal_claim": True}]})):
        s = session([out, {"segments": [bad]}] + ([verdicts] if verdicts else []))
        r = s.step(m)
        assert r.data["questions"][0]["asked"] == fixed and fixed in r.text
        assert r.data["ack"] == texts.ACK_FALLBACK["de"]


def test_a_question_is_never_put_twice_in_the_same_words():
    out = {"language": "de", "facts": {},
           "areas": [{"area": "debt_collection", "evidence": "wegen einer Rechnung"}]}
    nothing = {"language": "de", "areas": [], "facts": {}}
    s = session([out, {"segments": []}, nothing, {"segments": []}, nothing, {"segments": []}])
    first = s.step("Ich habe einen Brief wegen einer Rechnung bekommen.")
    fixed = FIELD_BY_NAME["document_type"].question["de"]
    assert first.data["questions"][0]["asked"] == fixed and first.data["ack"] == texts.ACK_FALLBACK["de"]
    # The model offers no new wording: the fixed text would come again word for word.
    again = s.step("Na ja, ein Brief halt.")
    assert again.data["questions"][0]["asked"] == fixed
    assert again.data["ack"] == texts.REASK["de"] and texts.REASK["de"] in again.text
    # The model is told that the question was put before.
    system, user = s.llm.calls[3]
    assert system == compose.SYSTEM and '"asked_before": true' in user
    # A new wording by the model needs no such notice.
    own = "Steht auf dem Brief, wer ihn geschickt hat?"
    s.llm = FakeLLM([nothing, {"segments": [{"type": "question", "text": own}]},
                     {"results": [{"index": 0, "legal_claim": False}]}])
    third = s.step("Keine Ahnung, was Sie meinen.")
    if third.route is Route.ASK:               # (a third unclear reply may also be handed over)
        assert third.data["questions"][0]["asked"] == own and third.data["ack"] == ""


def test_an_answer_tapped_from_the_quick_replies_needs_no_model_and_brings_the_next_question():
    s = session([LOOSE_OUT, {"segments": []}])
    s.step(LOOSE)
    calls = len(s.llm.calls)
    r = s.answer_form({"document_type": "reminder"})
    assert len(s.llm.calls) == calls                       # nothing was sent to the model
    q = r.data["questions"]
    assert len(q) == 1 and q[0]["asked"] == q[0]["question"] and r.data["chat"] is True
    with pytest.raises(ValueError):                        # only the question that was asked
        s.answer_form({"default_trigger": "reminder"})


# ---- a topic the sources do not cover (rule R14) ---------------------------------------

GYM = ("Ein Inkassobüro verlangt 900 Franken für ein Fitnessabo. Ich habe vergessen zu "
       "kündigen. Muss ich das Abo trotzdem bezahlen?")
GYM_OUT = {"language": "de", "areas": [D],
           "facts": {"document_type": fact("reminder", "Ein Inkassobüro verlangt 900 Franken")},
           "uncovered": {"topic": "Vertrags- und AGB-Recht: Kündigung eines Abonnements",
                         "evidence": "Ich habe vergessen zu kündigen"}}


def test_uncovered_topic_is_named_and_the_hand_over_proposed_with_lextecs_conditions():
    s = session([GYM_OUT])
    r = s.step(GYM)
    assert r.kind == "refer_offer" and not r.decision.urgent
    assert [x.rule for x in r.decision.reasons] == ["R14-not-covered"]
    assert "Vertrags- und AGB-Recht: Kündigung eines Abonnements" in r.data["reasons"][0]
    assert "noch nicht prüfen kann" in r.data["reasons"][0]
    assert r.data["conditions"] == texts.HANDOVER_CONDITIONS["de"]
    assert "15 Minuten ist kostenlos" in r.text and "CHF 85" in r.text
    assert len(s.llm.calls) == 1                     # the proposal itself is fixed text


def test_declined_proposal_for_an_uncovered_topic_continues_and_is_not_repeated():
    s = session([GYM_OUT, GYM_OUT, {"segments": []}])
    s.step(GYM)
    r = s.answer_handover(False)
    assert r.kind == "ask" and r.data["ack"] == texts.DECLINED_SHORT["de"]
    assert r.decision.questions == ["principal_status", "default_trigger"]
    assert [x["name"] for x in r.data["questions"]] == ["principal_status"]   # one at a time
    assert s.handover == "" and s.case.uncovered["declined"] is True
    r = s.step("Okay, machen wir weiter.")           # the model names the topic again
    assert r.route is Route.ASK                      # no second proposal


def test_accepted_hand_over_carries_the_model_written_description_labelled_as_unverified(tmp_path,
                                                                                         monkeypatch):
    monkeypatch.setattr(config, "OUTBOX_DIR", str(tmp_path))
    note = {"summary": "Die Person erhielt eine Forderung eines Inkassobüros für ein Fitnessabo, "
                       "das sie nicht gekündigt hat. Sie möchte wissen, ob sie zahlen muss."}
    s = session([GYM_OUT, note])
    s.step(GYM)
    done = s.answer_handover(True, contact={**PERSON, "phone": "079 000 00 00"})
    doc = done.briefing
    assert texts.SUMMARY_LABEL["de"] in doc and note["summary"] in doc
    assert "Vom System nicht geprüft" in doc and "«Ich habe vergessen zu kündigen»" in doc
    assert "Thema von den hinterlegten Quellen nicht abgedeckt" in doc
    # Name, e-mail and phone go into the briefing only, never into a prompt.
    assert "079 000 00 00" in doc and "Max Muster" in doc and "max.muster@example.org" in doc
    assert all(x not in sy + u for sy, u in s.llm.calls for x in ("079 000", "Muster", "example.org"))
    assert s.llm.calls[-1][0] == compose.SUMMARY_SYSTEM


def test_no_description_without_a_typed_message_or_when_the_model_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "OUTBOX_DIR", str(tmp_path))
    s = session([])                                  # only the button for a human
    s.request_human()
    assert (texts.SUMMARY_LABEL["de"] not in s.answer_handover(True, contact=PERSON).briefing
            and s.llm.calls == [])
    s = session([GYM_OUT, TimeoutError()])
    s.step(GYM)
    done = s.answer_handover(True, contact=PERSON)
    assert done.kind == "refer" and texts.SUMMARY_LABEL["de"] not in done.briefing


@pytest.mark.parametrize("uncovered", [
    {"topic": "Art. 266 OR Kündigung", "evidence": "Ich habe vergessen zu kündigen"},
    {"topic": "Vertragsrecht", "evidence": "words the person never wrote"},
    {"topic": "x" * 200, "evidence": "Ich habe vergessen zu kündigen"},
    {"topic": "", "evidence": "Ich habe vergessen zu kündigen"},
    "Vertragsrecht",
])
def test_uncovered_topic_needs_the_persons_words_and_a_plain_name(uncovered):
    s = session([{**GYM_OUT, "uncovered": uncovered}, {"segments": []}])
    r = s.step(GYM)
    assert s.case.uncovered is None and r.route is Route.ASK


def test_uncovered_topic_waits_for_a_pending_confirmation_and_never_removes_a_rule():
    c = debt_case()
    c.facts["document_type"] = Fact("document_type", Status.KNOWN, "payment_order", "x",
                                    confirmed=False)
    c.uncovered = {"topic": "Vertragsrecht", "evidence": "x", "declined": False}
    d = gate(c, TODAY)
    assert d.route is Route.ASK and d.questions[0] == "document_type"
    c.facts["document_type"].confirmed = True
    c.facts["document_received_date"] = Fact("document_received_date", Status.KNOWN,
                                             date(2026, 10, 1), "x")
    d = gate(c, TODAY)                               # the period may have passed: both reasons
    assert d.route is Route.REFER and d.urgent
    assert {r.rule for r in d.reasons} == {"R4-deadline-close", "R14-not-covered"}


# ---- legal fields: one file per field ----------------------------------------------------

def test_every_field_file_is_complete_and_cites_only_stored_articles():
    assert set(legal_fields.REGISTRY) == {"debt_collection", "inheritance_debt",
                                          "credit_record"}
    for f in legal_fields.REGISTRY.values():
        assert f.title["de"] and f.title["en"] and "ß" not in f.title["de"], f.file
        assert f.playbook and f.covers and f.not_covered, f.file
        assert [k for k in f.statutes if k not in CORPUS] == [], f.file
    assert set(AREAS) == set(legal_fields.REGISTRY) | {"other"}
    assert AREA_LABELS["debt_collection"] == legal_fields.REGISTRY["debt_collection"].title


FIELD_FILE = """---
id: tenancy_deposit
title_de: Mietkaution
title_en: Rental deposit
handling: answer
description: A tenant wants the rental deposit back.
covers: return of the deposit.
not_covered: termination of the lease.
statutes: or-102, or-104
---
# Rental deposit
The landlord returns the deposit when the lease has ended.
"""


def test_a_new_field_is_one_file(tmp_path):
    (tmp_path / "tenancy.md").write_text(FIELD_FILE, encoding="utf-8")
    fields = legal_fields.load(tmp_path)
    f = fields["tenancy_deposit"]
    assert f.title == {"de": "Mietkaution", "en": "Rental deposit"}
    assert f.statutes == ("or-102", "or-104") and f.handling == "answer"
    assert f.playbook.startswith("# Rental deposit")


@pytest.mark.parametrize("broken,problem", [
    (FIELD_FILE.replace("handling: answer", "handling: decide"), "handling"),
    (FIELD_FILE.replace("covers: return of the deposit.\n", ""), "covers"),
    (FIELD_FILE.replace("---\n# Rental", "# Rental"), "not closed"),
    (FIELD_FILE.split("# Rental deposit")[0], "playbook"),
    ("no head at all", "three dashes"),
])
def test_a_broken_field_file_is_reported_by_name(broken, problem):
    with pytest.raises(ValueError, match="tenancy.md.*" + problem):
        legal_fields.parse(broken, "tenancy.md")


# ---- server and page ----------------------------------------------------------------------

def test_server_reopens_an_answer_and_rejects_anything_else():
    import server
    app = server.App(demo_mode=True, today=None)
    sid = app.start("de", False, "fees")["id"]
    s = app.sessions[sid]["session"]
    s.case = debt_case(document_type="reminder", principal_status="paid_on_time")
    s._decide_and_respond()
    with pytest.raises(ValueError):
        app.revise(sid, "claim_amount")
    reply = app.revise(sid, "principal_status")
    assert reply["kind"] == "ask" and reply["data"]["questions"][0]["name"] == "principal_status"
    assert reply["data"]["understood"]["items"][0]["revisable"] is True


def test_page_renders_model_reply_confirmation_change_buttons_and_conditions(tmp_path, monkeypatch):
    if not shutil.which("node"):
        pytest.skip("Node.js is required for the frontend renderer test")
    monkeypatch.setattr(config, "OUTBOX_DIR", str(tmp_path))
    replies = []
    for lang in ("de", "en"):
        ok = {"results": [{"index": 0, "legal_claim": False},
                          {"index": 1, "supported": True, "relevant": True}]}
        draft = {"segments": [talk("Danke, das hilft mir weiter."), legal()]}
        s = Session(FakeLLM([{**LOOSE_OUT, "language": lang}, draft, ok]), today=TODAY,
                    language=lang, answerer=classify_structured, compose=True)
        replies.append(reply_view(s, s.step(LOOSE)))                       # confirm + model text
        replies.append(reply_view(s, s.answer_form({"document_type": "payment_order"})))  # urgent
        s = Session(FakeLLM([{**GYM_OUT, "language": lang}, {"summary": "Fitnessabo."}]),
                    today=TODAY, language=lang, answerer=classify_structured, compose=True)
        replies.append(reply_view(s, s.step(GYM)))                         # offer + conditions
        replies.append(reply_view(s, s.step("ja")))                        # details still needed
        replies.append(reply_view(s, s.answer_handover(True, contact=PERSON)))   # case number
    assert [r["kind"] for r in replies[-3:]] == ["refer_offer", "handover_contact", "refer"]
    result = subprocess.run(["node", "tests/web_form.cjs"], input=json.dumps(replies),
                            text=True, capture_output=True, check=False)
    assert result.returncode == 0, result.stderr + result.stdout
    # Per language: the details form in the proposal and after a typed yes, and the number.
    assert json.loads(result.stdout.splitlines()[-1]) == {"offers": 2, "details": 4, "numbers": 2}
    assert Path("tests/web_form.cjs").read_text().count("/api/revise") >= 1
    assert briefing  # imported for the monkeypatched outbox
