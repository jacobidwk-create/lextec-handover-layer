"""Demo mode: example conversations with recorded model answers.

Purpose: anyone can try the prototype without an API key, and the pitch can
be shown with a fixed, repeatable outcome. Only the answers of the language
model are replayed from a file. Everything else runs for real: validation,
detectors, deadlines, the gate, the questions and the briefing.

The recording is tied to the exact prompts. If a prompt, a question text or
a scenario changes, record again with: python tools/record_demo.py
"""
from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path

from .llm import LLM

RECORDINGS = Path(__file__).resolve().parent.parent / "demo" / "recordings.json"

# The date on which the examples take place; deadlines are computed against it.
DEMO_TODAY = date(2026, 11, 11)

# A step of an example is either a typed message (text) or the answers chosen from
# the lists of the open questions: {"answers": {fact: value}}. Chosen answers need no
# model call, so the examples can be continued with other answers than the prepared ones.
SCENARIOS = [
    {
        "id": "fees",
        "expect": "PROCEED",
        "title": {"de": "Mahnung mit Inkassogebühren", "en": "Reminder with collection fees"},
        "summary": {"de": "Antworten aus Listen wählen, dann ordnet das System selbst ein.",
                    "en": "Choose answers from lists, then the system classifies itself."},
        "messages": {
            "de": [
                "Ich habe eine Handyrechnung über 300 Franken zu spät bezahlt. Jetzt verlangt "
                "ein Inkassobüro in einem Brief zusätzlich 200 Franken Gebühren. Muss ich "
                "das wirklich zahlen?",
                {"answers": {"principal_status": "paid_late", "default_trigger": "reminder"}},
                {"answers": {"interest_charge": "none", "reminder_fee": "not_agreed",
                             "collection_costs": "flat"}},
            ],
            "en": [
                "I paid a phone bill of 300 francs too late. Now a collection agency is "
                "demanding another 200 francs in fees in a letter. Do I really have to pay "
                "that?",
                {"answers": {"principal_status": "paid_late", "default_trigger": "reminder"}},
                {"answers": {"interest_charge": "none", "reminder_fee": "not_agreed",
                             "collection_costs": "flat"}},
            ],
        },
    },
    {
        "id": "payment_order",
        "expect": "PROCEED",
        "expect_urgent": True,
        "title": {"de": "Zahlungsbefehl mit Inkassokosten", "en": "Payment order with collection costs"},
        "summary": {"de": "Absender bestätigen, dringender Hinweis, dann Position für Position.",
                    "en": "Confirm the sender, urgent notice, then charge by charge."},
        "messages": {
            "de": [
                "Der Pöstler hat mir am 09.11.2026 ein Schreiben gebracht, darauf steht "
                "Zahlungsbefehl. Verlangt werden 500 Franken für meine Handyrechnung und dazu "
                "140 Franken Inkassokosten.",
                {"answers": {"document_type": "payment_order", "principal_status": "open",
                             "default_trigger": "reminder"}},
                {"answers": {"interest_charge": "none", "reminder_fee": "none",
                             "collection_costs": "flat"}},
            ],
            "en": [
                "On 09.11.2026 the postman brought me a document, it says payment order "
                "(Zahlungsbefehl). It demands 500 francs for my phone bill plus 140 francs "
                "in collection costs.",
                {"answers": {"document_type": "payment_order", "principal_status": "open",
                             "default_trigger": "reminder"}},
                {"answers": {"interest_charge": "none", "reminder_fee": "none",
                             "collection_costs": "flat"}},
            ],
        },
    },
    {
        "id": "not_covered",
        "expect": "REFER",
        "expect_rule": "R14-not-covered",
        "title": {"de": "Fitnessabo nicht gekündigt", "en": "Gym membership not cancelled"},
        "summary": {"de": "Eine Frage ausserhalb der Quellen: Das System sagt es und schlägt die Übergabe vor.",
                    "en": "A question outside the sources: the system says so and proposes the hand-over."},
        "messages": {
            "de": [
                "Ein Inkassobüro verlangt 900 Franken für ein Fitnessabo, in das ich gar nicht "
                "mehr gehe. Ich habe aber vergessen zu kündigen. Muss ich das Abo trotzdem "
                "bezahlen?",
            ],
            "en": [
                "A collection agency demands 900 francs for a gym membership I do not even "
                "use anymore. I forgot to cancel, though. Do I still have to pay for the "
                "membership?",
            ],
        },
    },
    {
        "id": "disclaim",
        "expect": "PROCEED",
        "title": {"de": "Erbschaft mit Schulden", "en": "An inheritance with debts"},
        "summary": {"de": "Frist, Umgang mit dem Nachlass, Finanzen: dann, was zu tun ist.",
                    "en": "Period, dealings with the estate, finances: then what to do."},
        "messages": {
            "de": [
                "Meine Mutter ist gestorben, ich habe es am 28.10.2026 erfahren. Ein Testament "
                "gibt es nicht. Sie hatte viele Schulden und kaum Vermögen. Was muss ich tun, "
                "damit ich die Schulden nicht erbe?",
                {"answers": {"heir_basis": "statutory", "estate_actions": "none",
                             "estate_finances": "overindebted"}},
            ],
            "en": [
                "My mother has died; I learned of it on 28.10.2026. There is no will. She had "
                "many debts and hardly any assets. What do I have to do so that I do not "
                "inherit the debts?",
                {"answers": {"heir_basis": "statutory", "estate_actions": "none",
                             "estate_finances": "overindebted"}},
            ],
        },
    },
    {
        "id": "register",
        "expect": "PROCEED",
        "title": {"de": "Wohnung abgelehnt wegen einer Betreibung",
                  "en": "Refused a flat because of an enforcement"},
        "summary": {"de": "Art des Eintrags, Zahlung, Rechtsvorschlag: dann, wie der Eintrag für Dritte verschwindet.",
                    "en": "Kind of entry, payment, objection: then how the entry disappears for third parties."},
        "messages": {
            "de": [
                "Ich habe eine Wohnung nicht bekommen, weil auf meinem Betreibungsauszug eine "
                "Betreibung steht. Die Forderung stimmt nicht, ich habe sie nie bezahlt. Der "
                "Zahlungsbefehl wurde mir am 12.05.2026 zugestellt, und ich habe damals "
                "Rechtsvorschlag erhoben. Wie bekomme ich den Eintrag weg?",
                {"answers": {"register_entry": "enforcement", "register_payment": "not_paid",
                             "register_objection": "yes", "register_creditor_step": "none"}},
            ],
            "en": [
                "I did not get a flat because there is an enforcement on my debt register "
                "extract. The claim is wrong and I never paid it. The payment order was "
                "served on me on 12.05.2026, and I raised an objection at the time. How do I "
                "get rid of the entry?",
                {"answers": {"register_entry": "enforcement", "register_payment": "not_paid",
                             "register_objection": "yes", "register_creditor_step": "none"}},
            ],
        },
    },
    {
        "id": "inheritance",
        "expect": "REFER",
        "expect_rule": "R5-estate-actions",
        "title": {"de": "Auto des verstorbenen Vaters verkauft",
                  "en": "Sold the car of a father who has died"},
        "summary": {"de": "Mögliche Einmischung: Das System sagt, was das heissen kann, und schlägt die Übergabe vor.",
                    "en": "Possible interference: the system says what that can mean and proposes the hand-over."},
        "messages": {
            "de": [
                "Mein Vater ist gestorben, ich habe es am 21.09.2026 erfahren. Ein Testament "
                "gibt es nicht. Jetzt melden sich Gläubiger wegen seiner Schulden. Ich habe "
                "sein Auto verkauft, um die Beerdigung zu bezahlen. Muss ich jetzt seine "
                "Schulden zahlen?",
                {"answers": {"heir_basis": "statutory", "estate_actions": "took"}},
            ],
            "en": [
                "My father has died; I learned of it on 21.09.2026. There is no will. Now "
                "creditors are contacting me about his debts. I sold his car to pay for the "
                "funeral. Do I have to pay his debts now?",
                {"answers": {"heir_basis": "statutory", "estate_actions": "took"}},
            ],
        },
    },
]


def scenario(scenario_id: str) -> dict | None:
    return next((s for s in SCENARIOS if s["id"] == scenario_id), None)


def pool(steps) -> dict:
    """The prepared list answers of an example, by question."""
    return {k: v for step in steps if isinstance(step, dict) for k, v in step["answers"].items()}


def prepared(answers: dict, question: dict):
    """The prepared answer to tap for a question as it is shown now, or None. A question
    may first offer only "no" and "yes"; a prepared detail then means "yes" for now and
    is tapped at the follow-up."""
    offered = [o["value"] for o in question.get("options", [])]
    value = answers.get(question["name"])
    if value in offered:
        return value
    if value is not None and value != "none" and "claimed" in offered:
        return "claimed"
    return None


# An invented person for the examples: the hand-over requires first name, surname and
# e-mail address (contact.py). Used by the recording tool, the tests and the automatic
# demo of the page; never a real person.
DEMO_CONTACT = {"first_name": "Max", "last_name": "Muster",
                "email": "max.muster@example.org", "phone": ""}


def run(session, steps):
    """Play an example as the web page does: the typed messages in order, and after each
    reply the prepared answers for whichever questions are open. Which questions are
    open depends on what the model read from the message, so the prepared answers are
    a pool, not a fixed sequence. Returns the last reply."""
    from .schema import Route
    answers = pool(steps)
    reply = None
    for text in (step for step in steps if isinstance(step, str)):
        reply = session.step(text)
        for _ in range(12):
            if session.closed or reply.route is not Route.ASK:
                break
            taps = {q["name"]: prepared(answers, q) for q in reply.data["questions"]}
            taps = {k: v for k, v in taps.items() if v is not None}
            if not taps:
                break
            reply = session.answer_form(taps)
        if session.closed:
            break
    return reply


def _key(system: str, user: str) -> str:
    return hashlib.sha256((system + "\x00" + user).encode("utf-8")).hexdigest()


class RecordingLLM:
    """Passes calls to the real model and remembers every answer."""

    def __init__(self, inner: LLM, store: dict):
        self.inner, self.store = inner, store

    def complete_json(self, system: str, user: str) -> dict:
        out = self.inner.complete_json(system, user)
        self.store[_key(system, user)] = out
        return out


class ReplayLLM:
    """Answers from the recording. A prompt that was not recorded is an error,
    which the engine treats like any model failure: it refers the case."""

    def __init__(self, path: Path = RECORDINGS):
        self.store = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}

    def complete_json(self, system: str, user: str) -> dict:
        key = _key(system, user)
        if key not in self.store:
            raise LookupError("no recorded model answer for this prompt")
        return self.store[key]
