"""Conversation engine: one user message in, one system reply out.

Order of work per message:
  1. extraction by the model, validated by code      (extract.py)
  2. keyword detectors                               (detectors.py)
  3. progress bookkeeping (no-progress rule)
  4. the gate decides the route                      (rules.py)
  5. the reply: first the answer to a question the user asked (fixed texts,
     knowledge.py), then
       ASK      fixed-template questions
       PROCEED  the classification (only reachable when the gate returned PROCEED)
       REFER    the system proposes the hand-over and asks for the user's agreement

The model leads, the rules guard (2026-11-13). With compose=True the reply to a typed
message is written by the model from the playbook of the legal field and checked by
compose.py: a legal statement is shown only with a source and a word-for-word quote.
Route, urgency, deadlines, the hand-over proposal and the fixed result are added by
this engine around that text; the model cannot change them. A consequential fact read
from free text (for example "payment order") is confirmed with the person before a
rule acts on it, and every list answer can be reopened by the person (revise).

Answers from a list. A question whose field has options (areas.py) is shown with a
list of plain answers and the explanation of the terms it uses. An answer chosen
from the list is recorded directly (answer_form): no model reads it, so it cannot be
misread, and the gate runs on it at once. The user may still answer in free text.

Hand-over and consent. The gate decides that a case should go to a human; it does
not send anything. The engine then asks the user. Only an explicit yes (a button
or a plain "ja"/"yes") writes the briefing and delivers it. After a no, nothing
is passed on, the conversation stays open, and the system still gives no
classification unless new facts or explicit recovery allow the gate to return PROCEED.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Optional

from . import briefing, compose, config, knowledge, texts
from . import contact as contact_details
from .areas import (FIELD_BY_NAME, LABELS, UNKNOWN_CHOICE, WHY, display_value,
                    needs_confirmation, needs_detail, options_for, required_fields)
from .detectors import run_detectors
from .extract import extract
from .guidance import next_steps, render_next_steps
from .llm import LLM
from .priority import priority_class
from .rules import gate
from .schema import Case, Decision, Route, Status

# Typed answers to "May I hand your matter over?". Only these exact short answers
# count; anything else is treated as a normal message and never as consent.
_YES = {"ja", "ja bitte", "ja gerne", "ja danke", "gerne", "einverstanden", "ok", "okay",
        "in ordnung", "bitte übergeben", "ja bitte übergeben", "ja übergeben",
        "yes", "yes please", "yes thanks", "sure", "agreed", "please do", "go ahead",
        "yes please hand it over", "please hand it over", "j", "y"}
_NO = {"nein", "nein danke", "nein bitte nicht", "lieber nicht", "bitte nicht",
       "nicht übergeben", "nichts weitergeben", "nein nichts weitergeben",
       "no", "no thanks", "no thank you", "rather not", "please don't", "please do not",
       "do not", "don't", "n"}


def consent_answer(text: str) -> Optional[bool]:
    """True for a clear yes, False for a clear no, None for anything else."""
    t = " ".join(re.sub(r"[^\w\s']", " ", text.lower()).split())
    return True if t in _YES else False if t in _NO else None


@dataclass
class Reply:
    route: Route
    text: str                       # the full reply as plain text
    decision: Decision
    briefing_path: Optional[Path] = None
    # "ask" | "proceed" | "proceed_repeat" | "refer_offer" | "refer" | "refer_declined"
    kind: str = ""
    data: dict = field(default_factory=dict)   # the same reply in parts, for the web page
    briefing: str = ""              # briefing text on REFER


class Session:
    def __init__(self, llm: LLM, consent_distress_screening: bool = False,
                 today: Optional[date] = None, language: str = "de", answerer=None,
                 empathy: bool = False, compose: bool = False):
        self.llm = llm
        self._fixed_today = today
        self.today = today or date.today()
        self.case = Case(language=language,
                         consent_distress_screening=consent_distress_screening)
        # callable(case, decision, llm) -> text, or -> (text, data)
        self.answerer = answerer
        # The model writes the reply to typed messages, checked by compose.py.
        # (empathy=True is the earlier name of this switch.)
        self.compose = compose or empathy
        self._guidance_seen = None      # the urgent guidance already shown in full
        self._result_summary: list = [] # the fixed result, for the model to respect
        self._asked_texts: dict = {}    # question -> the words it was last asked in
        self._detail_asked: set = set() # partial answers whose detail was just asked for
        self.closed = False
        self.last_decision: Optional[Decision] = None
        self._answered_for: Optional[tuple] = None
        # "" | "offered" (waiting for the user's answer) | "declined" | "done"
        self.handover = ""
        self._declined_signature = None
        # The words of a typed yes that still waits for the person's contact details.
        self._typed_yes = ""

    # ------------------------------------------------------------------ one message
    def step(self, user_text: str) -> Reply:
        if self.closed:
            raise RuntimeError("This conversation has ended.")
        c = self.case
        if self.handover == "offered":
            answer = consent_answer(user_text)
            if answer is not None:
                return self.answer_handover(answer, typed=user_text)

        command = " ".join(re.sub(r"[^\w\s']", " ", user_text.lower()).split())
        if command in {"weiter selbst klären", "continue self service", "continue self-service"}:
            return self.recover()
        if command in {"verarbeitung erneut versuchen", "retry processing"}:
            return self.recover(retry=True)
        c.messages.append(("user", user_text))
        c.typed += 1
        # Only whole, unambiguous pause messages skip extraction. A message that
        # also supplies facts or a risk signal always takes the normal path.
        pause = re.fullmatch(
            r"(?:moment|einen moment|bitte warten|one moment|please wait|hold on)"
            r"(?: ich (?:hole|suche) (?:den brief|das schreiben)| (?:i am|i'm|i will|i'll) "
            r"(?:getting|looking for|get) (?:the letter|the document))?", command)
        if pause:
            c.turn_questions = []
            c.audit.append("pause: no answer attempt counted")
            return self._decide_and_respond(count=False, ack=texts.PAUSE_ACK[c.language])
        return self._process_turn()

    def _process_turn(self, count_attempt: bool = True) -> Reply:
        c = self.case
        had_question = bool(c.last_asked) and (self.last_decision is None
                                              or self.last_decision.route is Route.ASK)
        before = {n: (f.status, str(f.value)) for n, f in c.facts.items()}
        other_before = (len(c.areas), len(c.flags), tuple(c.contradictions))
        recovering_failure = bool(c.technical_failure)
        self.today = self._fixed_today or date.today()
        extract(self.llm, c, self.today)
        changed = any(before.get(n) != (f.status, str(f.value))
                      for n, f in c.facts.items())
        if count_attempt and not c.technical_failure:
            # The detail of a partial answer ("yes, a fee is claimed") is asked for once.
            # If the reply does not give it, the conversation moves on with what is known.
            for name in self._detail_asked:
                f, spec = c.fact(name), FIELD_BY_NAME[name]
                if f.status is Status.KNOWN and f.value in spec.partial:
                    f.detail_asks += 1
                    c.audit.append(f"{name}: detail asked once without result; kept as "
                                   f"'{f.value}'")
            self._detail_asked = set()
        run_detectors(c)
        latest = next((t for r, t in reversed(c.messages) if r == "user"), "")
        if (not c.technical_failure and re.fullmatch(
                r"\s*(?:Warum fragen Sie das|Was meinen Sie|Ich verstehe die Frage nicht|"
                r"Why are you asking|What do you mean|I don['’]t understand the question)[?.! ]*",
                latest, re.IGNORECASE) and "question_help" not in c.turn_questions):
            c.turn_questions.append("question_help")
        if c.flags.get("wants_human") and c.flags["wants_human"].lower() in latest.lower():
            self._declined_signature = None  # a renewed explicit request, including typed requests
        nothing_new = not changed and other_before == (len(c.areas), len(c.flags), tuple(c.contradictions))
        question_only = bool(c.turn_questions) and nothing_new
        if question_only:
            c.question_turns += 1
            c.audit.append("user question: no answer attempt counted")
        substantive = count_attempt and not question_only and not c.technical_failure and not recovering_failure
        if not nothing_new and not c.technical_failure:
            c.no_progress_rounds = 0
            c.audit.append("new or corrected information: no-progress counter cleared")
        elif had_question and substantive and nothing_new:
            c.no_progress_rounds = min(2, c.no_progress_rounds + 1)
            c.audit.append(f"substantive attempt without progress: {c.no_progress_rounds}")
            for name in c.last_asked:
                if name == "__area__":
                    c.area_asks += 1
                elif name == "__contradiction__":
                    c.contradiction_asks += 1
                elif name in FIELD_BY_NAME:
                    f = c.fact(name)
                    if f.status is Status.MISSING:
                        f.failed_attempts += 1
                        if f.failed_attempts >= config.MAX_ASKS_PER_FIELD:
                            f.status = Status.UNRESOLVABLE
                            c.audit.append(f"{name}: repeated attempts without usable answer")
        ack = texts.CLARIFY_ACK[c.language] if substantive and had_question and nothing_new else None
        return self._decide_and_respond(count=substantive, ack=ack,
                                        typed=not c.technical_failure)

    def answer_form(self, answers: dict) -> Reply:
        """The user chose answers from the lists of the open questions.

        answers: {fact name: chosen value, or UNKNOWN_CHOICE for "I do not know"}
        No model call is involved. Only questions that are open right now and that
        have a list can be answered this way; anything else is rejected as a whole.
        """
        if self.closed:
            raise RuntimeError("This conversation has ended.")
        c, lang = self.case, self.case.language
        asking = self.last_decision is not None and self.last_decision.route is Route.ASK
        if not isinstance(answers, dict) or not answers or not asking:
            raise ValueError("no open list question to answer")
        for name, value in answers.items():
            spec = FIELD_BY_NAME.get(name)
            if spec is None or not spec.options or name not in c.last_asked:
                raise ValueError("not an open list question")
            if value != UNKNOWN_CHOICE and value not in spec.options:
                raise ValueError("not one of the listed answers")
        lines = []
        for name in [n for n in c.last_asked if n in answers]:     # in the order asked
            value, f = answers[name], c.fact(name)
            if value == UNKNOWN_CHOICE:
                label = texts.FORM_UNKNOWN[lang]
                f.status, f.value, f.evidence = Status.USER_UNKNOWN, None, label
            else:
                label = FIELD_BY_NAME[name].options[value][lang]
                f.status, f.value, f.evidence = Status.KNOWN, value, label
                f.failed_attempts, f.confirmed = 0, True
            lines.append(f"{LABELS[name][lang]}: {label}")
            self._detail_asked.discard(name)
            c.audit.append(f"{name}: answer chosen from the list ({value}); no model call")
        c.messages.append(("user", "\n".join(lines)))
        c.turn_questions = []
        c.no_progress_rounds = 0
        return self._decide_and_respond(count=True, ack=texts.FORM_ACK[lang])

    def revise(self, name: str) -> Reply:
        """The person says "that is not right" about an answer and wants to choose
        again. No model call. Only list questions can be reopened this way; anything
        typed in free text corrects a fact through the normal path."""
        if self.closed:
            raise RuntimeError("This conversation has ended.")
        c, lang = self.case, self.case.language
        spec, f = FIELD_BY_NAME.get(name), self.case.facts.get(name)
        if spec is None or not spec.options or not spec.ask or f is None \
                or f.status is Status.MISSING:
            raise ValueError("not an answer that can be changed")
        c.messages.append(("user", texts.REVISE_SAID[lang].format(label=LABELS[name][lang])))
        f.status, f.value, f.evidence, f.confirmed = Status.MISSING, None, "", True
        f.ask_count = max(f.ask_count, 1)     # it is asked directly now
        f.failed_attempts = 0
        c.audit.append(f"{name}: reopened by the person")
        c.turn_questions = []
        c.no_progress_rounds = 0
        self._answered_for = None
        if self.handover == "offered":
            self.handover = ""
        return self._decide_and_respond(count=False, ack=texts.REVISE_ACK[lang])

    def recover(self, retry: bool = False) -> Reply:
        """Explicit recovery never clears legal facts or unknown prerequisites."""
        if self.closed:
            raise RuntimeError("This conversation has ended.")
        c = self.case
        if retry:
            if not c.technical_failure:
                raise RuntimeError("No processing failure to retry.")
            c.audit.append("user requested another processing attempt")
            return self._process_turn(count_attempt=False)
        c.messages.append(("user", texts.RESUME_LABEL[c.language]))
        c.flags.pop("wants_human", None)
        c.no_progress_rounds = 0
        c.area_asks = c.contradiction_asks = c.rounds = 0
        for f in c.facts.values():
            f.failed_attempts = 0
            if f.status is Status.UNRESOLVABLE:
                f.status = Status.MISSING
        c.turn_questions = []
        c.audit.append("user resumed self-service; human preference withdrawn; legal facts retained")
        # Do not repeat a declined legal offer simply because intake was restarted.
        if self.handover == "offered" and self.last_decision:
            self._declined_signature = self._referral_signature(self.last_decision)
            self.handover = "declined"
            self._decline_uncovered(self.last_decision)
        return self._decide_and_respond(count=False)

    def request_human(self) -> Reply:
        """The user pressed the button for a human. No model call is involved: the
        flag is set directly, the gate refers under rule R1, and the user is asked
        to confirm the hand-over like for any other referral."""
        if self.closed:
            raise RuntimeError("This conversation has ended.")
        c = self.case
        label = texts.HUMAN_BUTTON[c.language]
        c.messages.append(("user", label))
        self._declined_signature = None
        c.flags["wants_human"] = label
        c.turn_questions = []
        c.audit.append("the user pressed the button for a human")
        return self._decide_and_respond(count=False)

    def _decide_and_respond(self, count: bool = True, ack: str | None = None,
                            typed: bool = False) -> Reply:
        """typed: the turn was a typed message, so the model may write the reply."""
        c = self.case
        self.today = self._fixed_today or date.today()
        decision = gate(c, self.today)
        decision.assessed_on = self.today
        self.last_decision = decision
        c.audit.append(f"gate -> {decision.route.value}: "
                       + "; ".join(r.rule for r in decision.reasons))
        answers = self._answers(decision)

        if decision.route is Route.ASK:
            self.handover = ""
            reply = self._ask(decision, answers, count, ack, typed)
        elif decision.route is Route.REFER:
            reply = self._offer(decision, answers)
        else:
            self.handover = ""
            reply = self._proceed(decision, answers, ack, typed)
        c.messages.append(("assistant", reply.text))
        return reply

    # ------------------------------------------------------------------ user questions
    def _answers(self, decision: Decision) -> list[dict]:
        """Answers to the questions the user asked in this message, from fixed texts."""
        c, lang = self.case, self.case.language
        route = decision.route.value
        out: list[dict] = []
        for topic in c.turn_questions:
            stored = knowledge.answer(topic, lang)
            if stored:
                if stored["kind"] == "term":
                    stored["note"] = texts.ANSWER_TERM_NOTE[lang]
                out.append(stored)
            elif topic == "own_case" and route in texts.ANSWER_OWN_CASE:
                out.append({"topic": topic, "title": texts.ANSWER_DEFAULT_TITLE[lang],
                            "text": texts.ANSWER_OWN_CASE[route][lang]})
            elif topic == "question_help" and route == "ASK":
                out.append({"topic": topic, "title": texts.ANSWER_DEFAULT_TITLE[lang],
                            "text": texts.ANSWER_QUESTION_HELP[lang]})
            elif topic == "other" and "service_scope" not in c.turn_questions:
                scope = knowledge.answer("service_scope", lang)
                out.append({"topic": topic, "title": texts.ANSWER_DEFAULT_TITLE[lang],
                            "text": texts.ANSWER_OTHER[lang] + " " + scope["text"]})
        return out

    @staticmethod
    def _answers_text(answers: list[dict]) -> str:
        blocks = []
        for a in answers:
            line = f"{a['title']}: {a['text']}"
            if a.get("citation"):
                line += f" ({a['citation']})"
            if a.get("note"):
                line += f" {a['note']}"
            blocks.append(line)
        return "\n\n".join(blocks)

    # ------------------------------------------------------------------ shared parts
    def _compose(self, decision: Decision, state: str, typed: bool, pending=None) -> list[dict]:
        """The model-written, checked part of a reply; [] if switched off or nothing passed."""
        if not (typed and self.compose) or self.case.technical_failure:
            return []
        return compose.compose(self.llm, self.case, decision, state, pending=pending,
                               result=self._result_summary if state != "asking" else None)

    @staticmethod
    def _drop_placeholder_answers(answers: list[dict]) -> list[dict]:
        """The fixed "I cannot say yet" texts are not needed when the model replied."""
        return [a for a in answers if a["topic"] not in ("own_case", "other", "question_help")]

    def _guidance(self, decision: Decision) -> list[dict]:
        """Urgent guidance for a payment order while the conversation continues: in
        full the first time and whenever it changes, afterwards only the date."""
        items = next_steps(self.case, decision)
        signature = tuple(tuple(i["paragraphs"]) for i in items)
        if items and signature == self._guidance_seen:
            return [{**i, "paragraphs": i["paragraphs"][1:2], "compact": True} for i in items]
        if items:
            self._guidance_seen = signature
        return items

    def _understood(self) -> dict:
        """The answers recorded so far, so that the person can say "that is not right"."""
        c, lang = self.case, self.case.language
        items = []
        for f in c.facts.values():
            spec = FIELD_BY_NAME.get(f.name)
            if spec is None or f.name not in LABELS or f.status is Status.MISSING:
                continue
            if f.status is Status.KNOWN:
                value = display_value(f.value, lang, f.name)
            elif spec.options:
                value = texts.FORM_UNKNOWN[lang]
            else:
                continue
            items.append({"name": f.name, "label": LABELS[f.name][lang], "value": value,
                          "revisable": bool(spec.options and spec.ask)})
        return {"label": texts.UNDERSTOOD_LABEL[lang], "change": texts.CHANGE_LABEL[lang],
                "items": items}

    def _decline_uncovered(self, decision: Decision) -> None:
        """A declined proposal that was made alongside the answer is not repeated
        (config.SOFT_RULES): the uncovered topic (R14), the passed disclaimer period,
        possible interference in the estate."""
        c = self.case
        if c.uncovered and any(r.rule == "R14-not-covered" for r in decision.reasons):
            c.uncovered["declined"] = True
            c.audit.append("hand-over for the uncovered topic declined; not repeated")
        for r in decision.reasons:
            if r.rule in config.SOFT_RULES and r.rule != "R14-not-covered":
                c.declined_rules.add(r.rule)
                c.audit.append(f"hand-over proposal {r.rule} declined; not repeated")

    # ------------------------------------------------------------------ PROCEED
    def _proceed(self, decision: Decision, answers: list[dict], ack: str | None = None,
                 typed: bool = False) -> Reply:
        # The conversation stays open after PROCEED: the user can add facts
        # (the gate runs again), ask a question or ask for a human (rule R1).
        c = self.case
        c.last_asked = []
        guidance = self._guidance(decision)
        snapshot = tuple(sorted((f.name, str(f.value), f.status.value)
                                for f in c.facts.values()))
        if snapshot == self._answered_for:
            # Nothing changed: no second result. The model may answer a follow-up.
            segments = self._compose(decision, "after_result", typed)
            if segments:
                answers = self._drop_placeholder_answers(answers)
            message = "" if segments else texts.AFTER_PROCEED[c.language]
            text = "\n\n".join(p for p in (ack, render_next_steps(guidance),
                                           self._answers_text(answers),
                                           compose.render(segments), message) if p)
            return Reply(Route.PROCEED, text, decision, kind="proceed_repeat",
                         data={"ack": ack or "", "message": message, "answers": answers,
                               "segments": segments, "next_steps": guidance,
                               "urgent": decision.urgent})
        self._answered_for = snapshot
        result = (self.answerer(c, decision, self.llm) if self.answerer
                  else "PROCEED (classification component not attached)")
        text, data = result if isinstance(result, tuple) else (result, {})
        assessment = data.get("assessment") if isinstance(data, dict) else None
        results = (data.get("assessments") or ([assessment] if assessment else [])
                   if isinstance(data, dict) else [])
        self._result_summary = [f"{p['title']}: {p['verdict_label']}"
                                for a in results for p in a["positions"]]
        # Around a fixed result the model may react to what the person wrote. Where the
        # classification itself is drafted by the model (other areas), it adds nothing.
        segments = self._compose(decision, "result", typed) if assessment else []
        if segments:
            answers = self._drop_placeholder_answers(answers)
        text = "\n\n".join(p for p in (ack, render_next_steps(guidance),
                                       self._answers_text(answers),
                                       compose.render(segments), text) if p)
        if data:
            data = {**data, "ack": ack or "", "answers": answers, "segments": segments,
                    "next_steps": guidance, "urgent": decision.urgent,
                    "understood": self._understood()}
        return Reply(Route.PROCEED, text, decision, kind="proceed", data=data)

    # ------------------------------------------------------------------ ASK
    def _ask(self, decision: Decision, answers: list[dict], count: bool,
             ack: str | None = None, typed: bool = False) -> Reply:
        c, lang = self.case, self.case.language
        why = texts.WHY_LABEL[lang]
        questions = []
        # In a conversation the questions come one at a time; the others stay open and
        # follow in the next turns. (Without the model-written reply, e.g. in tests and
        # the evaluation, a round still shows up to three.)
        names = decision.questions[:1] if self.compose else decision.questions
        for name in names:
            if name == "__area__":
                q, w = texts.AREA_QUESTION[lang], texts.AREA_WHY[lang]
            elif name == "__contradiction__":
                q = texts.CONTRADICTION_QUESTION[lang].format(items="; ".join(c.contradictions))
                w = texts.CONTRADICTION_WHY[lang]
            else:
                c.fact(name).ask_count += count
                q, w = FIELD_BY_NAME[name].question[lang], WHY[name][lang]
            item = {"name": name, "question": q, "why": w}
            spec = FIELD_BY_NAME.get(name)
            detail = spec is not None and needs_detail(c, name)
            if detail:
                # A partial answer is recorded ("yes, that is claimed"); now the one
                # detail that decides the outcome, with its own question.
                item["question"] = spec.detail["question"][lang]
                item["detail"] = True
                self._detail_asked.add(name)
            if spec is not None and spec.options:
                # Quick replies: plain answers plus "I do not know", and the fixed
                # explanations of the terms that appear (knowledge.py). The detail
                # values include their own "I do not know what the contract says".
                item["options"] = options_for(name, lang, detail=detail) + ([] if detail else [
                    {"value": UNKNOWN_CHOICE, "label": texts.FORM_UNKNOWN[lang]}])
                item["terms"] = knowledge.terms(spec.terms, lang)
                if needs_confirmation(c, name):
                    # Read from free text: shown as chosen, for the person to confirm
                    # or change. Nothing follows from it until then.
                    item["understood"] = c.facts[name].value
                    item["confirm_note"] = texts.CONFIRM_NOTE[lang]
            questions.append(item)
        n = texts.ASK_COUNT[lang][len(questions)]
        for x in questions:
            # The model is told when a question was put before, so that it does not
            # repeat it in the same words.
            if self._asked_texts.get((x["name"], x["question"])):
                x["asked_before"] = True
        segments = self._compose(decision, "asking", typed, pending=questions)
        # The model may ask the question in its own words; otherwise the fixed wording.
        asked = [x["text"] for x in segments if x["type"] == "question"]
        segments = [x for x in segments if x["type"] != "question"]
        reask = ""
        for i, x in enumerate(questions):
            x["asked"] = asked[-1] if (asked and i == 0) else x["question"]
            key = (x["name"], x["question"])
            if self.compose and x["asked"] == self._asked_texts.get(key):
                # Never the same words twice without saying why.
                reask = texts.REASK[lang]
            self._asked_texts[key] = x["asked"]
            x.pop("asked_before", None)
        if segments:
            answers = self._drop_placeholder_answers(answers)
        if answers and not count:
            # The message was only a question: answer it, then come back to the open points.
            ack, intro = "", texts.ASK_INTRO_AFTER_ANSWER[lang].format(n=n)
        else:
            ack = "" if segments else (ack or texts.ACK_FALLBACK[lang])
            intro = texts.ASK_INTRO[lang].format(n=n)
        if self.compose:
            # Chat: no announcement of "n questions"; the question is part of the message,
            # and a tapped answer is followed by the next question without a thank-you.
            if segments or asked or (answers and not count) or ack == texts.FORM_ACK[lang]:
                ack = ""
            if reask:
                ack = reask
            intro = ""
        c.last_asked = list(names)
        c.rounds += count
        guidance = self._guidance(decision)
        blocks = []
        for i, x in enumerate(questions, 1):
            block = x["asked"] if self.compose else f"{i}. {x['question']}"
            if x.get("options"):
                block += f"\n   {texts.OPTIONS_LABEL[lang]}" + "".join(
                    f"\n   - {o['label']}" for o in x["options"])
            if x.get("confirm_note"):
                understood = FIELD_BY_NAME[x["name"]].options[x["understood"]][lang]
                block += f"\n   {x['confirm_note']} ({understood})"
            block += f"\n   {why} {x['why']}"
            if x.get("terms"):
                block += (f"\n   {texts.TERMS_LABEL[lang]}: "
                          + ", ".join(t["title"] for t in x["terms"]))
            blocks.append(block)
        form = any(x.get("options") for x in questions)
        parts = [render_next_steps(guidance), self._answers_text(answers),
                 compose.render(segments), f"{ack} {intro}".strip()] + blocks
        text = "\n\n".join(p for p in parts if p)
        data = {"answers": answers, "ack": ack, "intro": intro, "segments": segments,
                "chat": self.compose,
                "why_label": why, "questions": questions, "next_steps": guidance,
                "urgent": decision.urgent, "understood": self._understood()}
        if form:
            data.update(form_hint=texts.FORM_HINT[lang], submit_label=texts.FORM_SUBMIT[lang],
                        placeholder=texts.FORM_PLACEHOLDER[lang],
                        terms_label=texts.TERMS_LABEL[lang],
                        source_label=texts.SOURCE_LABEL[lang])
        return Reply(Route.ASK, text, decision, kind="ask", data=data)

    # ------------------------------------------------------------------ REFER
    def _reasons(self, decision: Decision, skip: tuple = ()) -> list[str]:
        """The reasons for the referral in plain words, one per kind of rule."""
        lang = self.case.language
        reasons, seen = [], set()
        for r in decision.reasons:
            key = r.rule if r.rule in texts.REFER_WHY else r.rule.split("-")[0]
            if key in texts.REFER_WHY and key not in seen and key not in skip:
                seen.add(key)
                reason = texts.REFER_WHY[key][lang]
                if key == "R14":
                    reason = reason.format(topic=(self.case.uncovered or {}).get("topic", ""))
                reasons.append(reason)
        return reasons

    @staticmethod
    def _referral_signature(decision: Decision) -> tuple:
        return (tuple((r.rule, r.text, r.evidence) for r in decision.reasons),
                tuple((d.key, d.due, d.action_done) for d in decision.deadlines),
                decision.urgent, decision.emergency)

    def _recovery_data(self) -> dict:
        lang = self.case.language
        return {"recovery_hint": texts.RECOVERY_HINT[lang],
                "resume_label": texts.RESUME_LABEL[lang],
                "retry_label": texts.RETRY_LABEL[lang] if self.case.technical_failure else "",
                "retry_hint": texts.RETRY_HINT[lang] if self.case.technical_failure else ""}

    def _offer(self, decision: Decision, answers: list[dict]) -> Reply:
        """The gate says REFER: propose the hand-over and ask. Nothing is sent here."""
        c, lang = self.case, self.case.language
        if self.handover == "declined" and self._declined_signature == self._referral_signature(decision):
            guidance = next_steps(c, decision)
            data = {"message": texts.DECLINED_CONTINUE[lang], "answers": answers,
                    "next_steps": guidance, "urgent": decision.urgent,
                    "emergency": texts.EMERGENCY[lang] if decision.emergency else "",
                    **self._recovery_data()}
            text = "\n\n".join(p for p in (data["emergency"], self._answers_text(answers),
                data["message"], render_next_steps(guidance), data["retry_hint"], data["recovery_hint"]) if p)
            return Reply(Route.REFER, text, decision, kind="refer_declined", data=data)
        again = self.handover in ("offered", "declined")
        on_request = any(r.rule == "R1-user-wants-human" for r in decision.reasons)
        lead = (texts.HANDOVER_OFFER_ON_REQUEST if on_request
                else texts.HANDOVER_OFFER_AGAIN if again else texts.HANDOVER_OFFER)[lang]
        if decision.urgent and not decision.emergency:
            lead += "\n\n" + texts.URGENT_REVIEW_WARNING[lang]
        reasons = self._reasons(decision, skip=("R1",))
        emergency = texts.EMERGENCY[lang] if decision.emergency else ""

        # In an emergency the helpline numbers come before everything else.
        guidance = next_steps(c, decision)
        recovery = self._recovery_data()
        parts = [emergency, render_next_steps(guidance), self._answers_text(answers), lead,
                 recovery["retry_hint"], recovery["recovery_hint"]]
        if reasons:
            parts.append(texts.REFER_WHY_LABEL[lang] + "\n" + "\n".join("- " + r for r in reasons))
        parts += [texts.HANDOVER_SENT_NOTE[lang], conditions_text(lang),
                  texts.CONTACT_NOTE[lang],
                  texts.HANDOVER_QUESTION[lang] + " " + texts.HANDOVER_TYPE_HINT[lang]]
        text = "\n\n".join(p for p in parts if p)

        self.handover = "offered"
        self._typed_yes = ""
        c.audit.append("hand-over proposed; waiting for the user's agreement")
        return Reply(Route.REFER, text, decision, kind="refer_offer",
                     data={"answers": answers, "message": lead, "next_steps": guidance, **recovery,
                           "why_label": texts.REFER_WHY_LABEL[lang], "reasons": reasons,
                           "urgent": decision.urgent, "emergency": emergency,
                           "sent_note": texts.HANDOVER_SENT_NOTE[lang],
                           **conditions_data(lang),
                           "understood": self._understood(),
                           "question": texts.HANDOVER_QUESTION[lang],
                           "yes": texts.HANDOVER_YES[lang], "no": texts.HANDOVER_NO[lang],
                           "contact": contact_form(lang)})

    def answer_handover(self, accept: bool, contact: Optional[dict] = None,
                        typed: str = "") -> Reply:
        """The user's answer to the proposed hand-over. No model call is involved.

        accept=True   the briefing is written and delivered; the conversation ends
        accept=False  nothing is passed on; the conversation stays open
        contact       who the person is and how the team reaches them: first_name,
                      last_name and email are required, phone is optional (contact.py).
                      They go into the briefing only and are never part of a model
                      prompt. A yes without them passes nothing on: the reply asks for
                      them and the proposal stays open.
        typed         the user's own words if the answer was typed, else a button was used
        """
        if self.closed:
            raise RuntimeError("This conversation has ended.")
        decision = self.last_decision
        if self.handover != "offered" or decision is None or decision.route is not Route.REFER:
            raise RuntimeError("No hand-over is waiting for an answer.")
        c, lang = self.case, self.case.language
        # Keep the procedural guidance current even when consent arrives later.
        self.today = self._fixed_today or date.today()
        decision = gate(c, self.today)
        self.last_decision = decision
        guidance = next_steps(c, decision)
        how = "typed" if typed else "button"
        said = typed or (texts.HANDOVER_YES_SAID if accept else texts.HANDOVER_NO_SAID)[lang]
        c.messages.append(("user", said))
        emergency = texts.EMERGENCY[lang] if decision.emergency else ""

        if accept:
            details = contact_details.clean(contact)
            missing = contact_details.problems(details)
            if missing:
                # Agreed, but the team could not reach the person: nothing is sent.
                self._typed_yes = typed or self._typed_yes
                c.audit.append(f"the user agreed to the hand-over ({how}); required contact "
                               f"details missing ({', '.join(missing)}); nothing was passed on")
                form = contact_form(lang, missing)
                lines = [texts.CONTACT_ERRORS[m][lang] for m in missing]
                # The urgent guidance stays in every reply, also in this one.
                text = "\n\n".join(p for p in (
                    emergency, render_next_steps(guidance),
                    texts.CONTACT_REQUIRED[lang] + "\n" + "\n".join("- " + x for x in lines),
                    texts.CONTACT_NOTE[lang]) if p)
                reply = Reply(Route.REFER, text, decision, kind="handover_contact",
                              data={"message": texts.CONTACT_REQUIRED[lang], "problems": lines,
                                    "contact": form, "emergency": emergency,
                                    "next_steps": guidance,
                                    "urgent": decision.urgent,
                                    "yes": texts.CONTACT_SUBMIT[lang],
                                    "no": texts.HANDOVER_NO[lang]})
                c.messages.append(("assistant", reply.text))
                return reply
            # A yes that was typed first and completed with the details stays a typed yes.
            typed = typed or self._typed_yes
            how = "typed" if typed else "button"
            c.contact = details
            c.case_number = briefing.new_case_number(self.today)
            c.audit.append(f"the user agreed to the hand-over ({how}); "
                           f"case number {c.case_number}")
            # A short description for the advisor, written by the model from what the
            # person typed. Contact details are not part of that prompt.
            note = (compose.summary(self.llm, c, config.BRIEFING_LANGUAGE
                                    if config.BRIEFING_LANGUAGE in ("de", "en") else "de")
                    if self.compose and c.typed else "")
            doc = briefing.render(c, decision, self.today, consent=(how, typed), summary=note)
            try:
                path, _ = briefing.deliver(doc, decision.urgent, case_number=c.case_number,
                                           priority=priority_class(decision))
            except Exception as exc:
                c.audit.append(f"delivery could not be confirmed: {type(exc).__name__}")
                message = texts.DELIVERY_GUIDANCE_ERROR[lang]
                reply = Reply(Route.REFER, "\n\n".join(filter(None, [emergency, message,
                              render_next_steps(guidance)])), decision, kind="handover_error",
                              data={"message": message, "next_steps": guidance, "emergency": emergency})
                c.messages.append(("assistant", reply.text))
                return reply
            self.closed, self.handover = True, "done"
            message = texts.REFER_MESSAGE[lang]
            number_note = texts.CASE_NUMBER_NOTE[lang].format(email=texts.LEXTEC_CONTACT_EMAIL)
            text = "\n\n".join(p for p in (
                emergency, render_next_steps(guidance), message,
                f"{texts.CASE_NUMBER_LABEL[lang]}: {c.case_number}", number_note) if p)
            reply = Reply(Route.REFER, text, decision, briefing_path=path, kind="refer",
                          data={"message": message, "next_steps": guidance, "urgent": decision.urgent,
                                "case_number": c.case_number,
                                "case_number_label": texts.CASE_NUMBER_LABEL[lang],
                                "case_number_note": number_note,
                                "emergency": emergency, "reasons": [], "why_label": ""},
                          briefing=doc)
        else:
            c.audit.append(f"the user declined the hand-over ({how}); nothing was passed on")
            self.handover = "declined"
            self._typed_yes = ""
            self._declined_signature = self._referral_signature(decision)
            self._decline_uncovered(decision)
            if gate(c, self.today).route is not Route.REFER:
                # The proposal was the only reason to stop: carry on with the questions
                # or the result instead of leaving the person with nothing to do.
                return self._decide_and_respond(count=False, ack=texts.DECLINED_SHORT[lang])
            message = texts.DECLINED_CONTINUE[lang]
            notes = [texts.HANDOVER_DECLINED_DEADLINE[lang].format(
                         label=texts.DEADLINE_LABELS.get(d.key, {}).get(lang, d.label),
                         date=d.due.strftime("%d.%m.%Y"))
                     for d in decision.deadlines
                     if not d.action_done
                     and d.working_days_left <= config.DEADLINE_CLOSE_WORKING_DAYS]
            if decision.urgent and not decision.emergency and not notes:
                notes.append(texts.URGENT_REVIEW_WARNING[lang])
            if guidance:
                notes = []  # the shared component already explains this date more precisely
            recovery = self._recovery_data()
            text = "\n\n".join(p for p in (emergency, render_next_steps(guidance), message,
                                *notes, recovery["retry_hint"], recovery["recovery_hint"]) if p)
            reply = Reply(Route.REFER, text, decision, kind="refer_declined",
                          data={"message": message, "next_steps": guidance, **recovery, "deadline_notes": notes, "urgent": decision.urgent,
                                "emergency": emergency})
        c.messages.append(("assistant", reply.text))
        return reply


def conditions_data(lang: str) -> dict:
    """LexTec's conditions as shown with every hand-over proposal (fixed texts)."""
    return {"conditions_title": texts.HANDOVER_CONDITIONS_TITLE[lang],
            "conditions": texts.HANDOVER_CONDITIONS[lang],
            "rules_title": texts.HANDOVER_RULES_TITLE[lang],
            "rules": list(texts.HANDOVER_RULES[lang]),
            "terms_label": texts.HANDOVER_TERMS_LABEL[lang],
            "terms_url": texts.HANDOVER_TERMS_URL}


def conditions_text(lang: str) -> str:
    d = conditions_data(lang)
    return "\n\n".join([
        f"{d['conditions_title']}: {d['conditions']}",
        d["rules_title"] + ":\n" + "\n".join("- " + r for r in d["rules"]),
        f"{d['terms_label']}: {d['terms_url']}"])


def contact_form(lang: str, missing=()) -> dict:
    """The details asked for at the hand-over; they never reach a model."""
    return {"title": texts.CONTACT_TITLE[lang], "note": texts.CONTACT_NOTE[lang],
            "missing": list(missing),
            "fields": [{"name": name, "label": texts.CONTACT_FIELD_LABELS[name][lang],
                        "required": name in contact_details.REQUIRED,
                        "max": contact_details.MAX_LENGTH[name],
                        "error": texts.CONTACT_ERRORS.get(name, {}).get(lang, "")}
                       for name in contact_details.FIELDS]}


__all__ = ["Session", "Reply", "consent_answer", "required_fields", "conditions_data",
           "conditions_text", "contact_form"]
