"""Briefing for the legal advisor who takes over.

Built from the case record with fixed templates (no model call), so nothing in
the briefing can be invented. It is written only after the user agreed to the
hand-over (engine.py), to the outbox folder and, if a mail server is
configured, to the company inbox.

What the reader needs depends on why the case was referred:
  person   the person asked for a human or showed signs of distress
  process  the system could not establish the facts (failure, no progress, ...)
  legal    a legal trigger fired (deadline, estate actions, area always referred, ...)
The briefing therefore starts with a short overview that names the kind of
referral and the first step. Legal sources follow only for the legal issues
that the established facts actually raise (issues.py). A case with few facts
gets a list of what is unknown, not case law. A court decision is printed in
full only if, in addition, its own condition on the established facts is met
(relevance.py); the other decisions on a raised issue are listed in one line.
"""
from __future__ import annotations

import os
import secrets
import smtplib
from datetime import date, datetime
from email.message import EmailMessage
from pathlib import Path

from . import config, priority, texts
from .answer import fixed_results, load_corpus
from .contact import full_name
from .areas import AREA_LABELS, LABELS, display_value, required_fields
from .issues import ISSUE_BY_ID, assess
from .relevance import (DERIVED_LABELS, DERIVED_VALUE_LABELS, MANUAL, MET, NOT_MET, OPEN,
                        decision_state, derived)
from .schema import Case, Decision, Status

STATUTE_FOR_BASIS = {"Art. 74 SchKG": "schkg-74", "Art. 567 ZGB": "zgb-567",
                     "Art. 17 SchKG": "schkg-17", "Art. 580 ZGB": "zgb-580"}

# Kind of referral, by the rule that fired. Everything not listed is "legal".
_PERSON = {"R1", "R2"}
_PROCESS = {"R0", "R6", "R7", "R8", "R9", "R10"}

# First step for the reader, per rule, in order of priority.
FIRST_STEP = {
    "R2": {"de": "Zuerst persönlich Kontakt aufnehmen: Die Person hat Anzeichen einer akuten "
                 "Belastung geäussert (Zitat unten). Die Notfallnummern wurden ihr angezeigt. "
                 "Die Rechtsfragen sind zweitrangig.",
           "en": "First get in touch in person: the person expressed signs of acute distress "
                 "(quote below). The emergency numbers were shown to them. The legal "
                 "questions come second."},
    "R4": {"de": "Frist prüfen und wahren (siehe Fristen). Die Berechnung des Systems ist "
                 "vorsichtig (frühestes mögliches Ende) und ersetzt die eigene "
                 "Fristberechnung nicht.",
           "en": "Check and preserve the deadline (see Deadlines). The system's calculation "
                 "is cautious (earliest possible end) and does not replace your own."},
    "R0": {"de": "Technischer Fehler bei der Verarbeitung: Der Sachverhalt ist unvollständig "
                 "erfasst und im Gespräch zu erheben.",
           "en": "Technical failure during processing: the facts are incomplete and have to "
                 "be established in conversation."},
    "R4-disclaimer-passed": {
        "de": "Ausschlagungsfrist möglicherweise abgelaufen: sofort Gesuch um "
              "Fristverlängerung oder neue Frist aus wichtigen Gründen prüfen (Art. 576 ZGB); "
              "Fristbeginn und offenkundige Zahlungsunfähigkeit (Art. 566 Abs. 2 ZGB) klären.",
        "en": "Disclaimer period possibly passed: consider at once a request for an "
              "extension or new period for important reasons (Art. 576 ZGB); establish the "
              "start of the period and manifest insolvency (Art. 566 para. 2 ZGB)."},
    "R5-estate-actions": {
        "de": "Prüfen, ob die Handlungen am Nachlass eine Einmischung nach Art. 571 Abs. 2 "
              "ZGB sind, bevor weitere Schritte zum Nachlass erfolgen.",
        "en": "Assess whether the acts concerning the estate amount to interference under "
              "Art. 571 para. 2 ZGB before any further step regarding the estate."},
    "R5-register-court": {
        "de": "Registereintrag: anhand des Betreibungsauszugs und der Unterlagen klären, "
              "welcher Weg offensteht (Wiederherstellung nach Art. 33 Abs. 4 SchKG, "
              "Nichtigkeit nach Art. 22 SchKG, Klage nach Art. 85, 85a oder 86 SchKG) und ob "
              "in einem laufenden Gerichtsverfahren Fristen laufen.",
        "en": "Register entry: establish from the register extract and the documents which "
              "way is open (restoration under Art. 33 para. 4 SchKG, nullity under Art. 22 "
              "SchKG, an action under Art. 85, 85a or 86 SchKG) and whether periods are "
              "running in pending court proceedings."},
    "R5-enforcement-office": {
        "de": "Schreiben des Betreibungsamts: Zustelldatum erfragen, Frist für den "
              "(Teil-)Rechtsvorschlag prüfen (Art. 74 SchKG) und klären, welche Positionen "
              "bestritten sind.",
        "en": "Document from the debt enforcement office: ask for the date of service, "
              "check the period for the (partial) objection (Art. 74 SchKG) and establish "
              "which items are disputed."},
    "R5-advanced-proceedings": {
        "de": "Stand des Verfahrens anhand der Dokumente klären (Rechtsöffnung, Pfändung) "
              "und laufende Fristen prüfen.",
        "en": "Establish the stage of the proceedings from the documents (setting aside "
              "the objection, seizure) and check running deadlines."},
    "R12": {"de": "Rechtsgebiet, das immer ein Mensch prüft: Sachverhalt anhand der "
                  "Unterlagen prüfen.",
            "en": "A legal field that a human always reviews: check the facts against the "
                  "documents."},
    "R5-high-amount": {"de": "Hoher Betrag: Forderung und Unterlagen im Einzelnen prüfen.",
                       "en": "High amount: review the claim and the documents in detail."},
    "R5-private-credit-agency": {
        "de": "Eintrag bei einer privaten Auskunftei: ausserhalb des vom System abgedeckten "
              "Bereichs.",
        "en": "Entry at a private credit agency: outside the scope covered by the system."},
    "R3": {"de": "Thema ausserhalb des vom System abgedeckten Bereichs: Zuständigkeit klären.",
           "en": "Topic outside the scope covered by the system: clarify who handles it."},
    "R1": {"de": "Die Person wünscht ein Gespräch mit einer Rechtsberaterin oder einem "
                 "Rechtsberater.",
           "en": "The person would like to speak to a legal advisor."},
    "R6": {"de": "Eine entscheidende Angabe liess sich nicht klären (siehe «Zuerst zu "
                 "klären»).",
           "en": "A critical fact could not be established (see 'To clarify first')."},
    "R7": {"de": "Das Rechtsgebiet liess sich nicht erkennen: Anliegen im Gespräch klären.",
           "en": "The legal area could not be identified: clarify the matter in conversation."},
    "R8": {"de": "Die Rückfragen des Systems brachten keinen Fortschritt: Sachverhalt im "
                 "Gespräch erheben.",
           "en": "The system's questions brought no progress: establish the facts in "
                 "conversation."},
    "R9": {"de": "Höchstzahl an Rückfragerunden erreicht: offene Punkte im Gespräch klären.",
           "en": "Limit of question rounds reached: clarify the open points in conversation."},
    "R10": {"de": "Widersprüchliche Angaben (siehe unten) im Gespräch klären.",
            "en": "Clarify the contradictory statements (see below) in conversation."},
}

T = {
    "de": {
        "title": "Übergabe an die Rechtsberatung", "urgent": "DRINGEND – ",
        "date": "Datum", "user_lang": "Sprache der Person", "consent": "Zustimmung zur Übergabe",
        "langs": {"de": "Deutsch", "en": "Englisch"},
        "consent_button": "ja, per Schaltfläche", "consent_typed": "ja, getippt: «{said}»",
        "overview": "Kurzüberblick",
        "kind": "Art der Übergabe",
        "kinds": {"person": "Anliegen der Person (Gesprächswunsch oder Belastung)",
                  "process": "Sachverhalt vom System nicht klärbar",
                  "legal": "Rechtlicher Auslöser"},
        "reason": "Grund", "urgency": "Dringlichkeit",
        "urgency_none": "keine Frist berechnet",
        "urgency_calm": "Frist berechnet, nicht als dringend eingestuft",
        "urgency_urgent": "dringend", "urgency_emergency": "dringend, Hinweis auf akute Belastung",
        "topics": "Themen", "topics_none": "nicht erkannt",
        "facts_count": "Angaben", "facts_n": "{k} gesichert, {m} offen",
        "case_number": "Fallnummer", "priority": "Priorität",
        "person": "Name", "email": "E-Mail", "phone": "Telefon",
        "contact_none": "nicht angegeben",
        "first": "Empfohlene erste Schritte",
        "why": "Grund der Übergabe", "wrote": "die Person schrieb",
        "deadlines": "Fristen (frühestes mögliches Ende, zu überprüfen)",
        "deadlines_none": "Aus den gesicherten Angaben wurde keine Frist berechnet.",
        "passed": "möglicherweise bereits abgelaufen", "days": "{n} Arbeitstag(e) verbleibend",
        "done": "Schritt nach Angabe der Person erfolgt", "not_done": "Schritt NICHT bestätigt",
        "facts": "Gesicherte Angaben (mit den Worten der Person)", "none": "Keine.",
        "open": "Zuerst zu klären",
        "open_none": "Keine der nötigen Angaben fehlt.",
        "contradiction": "Widerspruch",
        "issues": "Rechtsfragen",
        "uncovered": "Vom System nicht geprüft (Thema ausserhalb der hinterlegten Quellen, "
                     "Bezeichnung durch das Sprachmodell)",
        "fees": "Vorprüfung nach festen Regeln (nur nach den Angaben der Person; der Person "
                "erst mit der Einordnung durch das System angezeigt)",
        "raised": "Aufgeworfen", "possible": "Noch nicht beurteilbar", "missing": "es fehlt",
        "issues_none": "Aus den gesicherten Angaben ergibt sich noch keine bestimmte Rechtsfrage.",
        "sources": "Quellen zu den aufgeworfenen Rechtsfragen (nach festen Regeln ausgewählt, "
                   "nicht vom Sprachmodell)",
        "sources_none": "Keine. Quellen werden erst angezeigt, wenn die Angaben vorliegen, aus "
                        "denen sich eine Rechtsfrage ergibt.",
        "sources_empty": "Zu den aufgeworfenen Rechtsfragen sind keine Quellen hinterlegt.",
        "kinds_src": {"statute": "Gesetz", "decision": "Entscheid", "commentary": "Kommentar"},
        "summary": "Zusammenfassung (englisch) von",
        "answers": "Beantwortet die Frage",
        "shown_because": "Abgedruckt, weil",
        "shown_issue": "die Rechtsfrage «{issue}» aufgeworfen ist (keine weitere Bedingung "
                       "hinterlegt)",
        "pointers": "Weitere hinterlegte Entscheide zu diesen Rechtsfragen (nicht abgedruckt)",
        "pointers_note": "Die Bedingung dieser Entscheide ist nach den gesicherten Angaben "
                         "nicht erfüllt, noch offen oder nicht prüfbar. Nach festen Regeln "
                         "zugeordnet, nicht vom Sprachmodell.",
        "state_manual": "aus den erfassten Angaben nicht prüfbar",
        "state_open": "noch offen, es fehlt: {lacking}",
        "state_not_met": "nach den gesicherten Angaben nicht einschlägig",
        "team": "dem Rechtsteam",
        "conversation": "Gespräch", "user": "Person", "system": "System",
        "audit": "Protokoll der Prüfschritte", "audit_none": "Keine Einträge.",
        "footer": "Automatisch erstellt. Die Angaben stammen von der Person und sind nicht "
                  "überprüft. Fristen sind vorsichtige Schätzungen.",
    },
    "en": {
        "title": "Case briefing (REFER)", "urgent": "URGENT - ",
        "date": "Date", "user_lang": "Language of the person", "consent": "Agreement to the hand-over",
        "langs": {"de": "German", "en": "English"},
        "consent_button": "yes, by button", "consent_typed": "yes, typed: '{said}'",
        "overview": "Overview",
        "kind": "Kind of referral",
        "kinds": {"person": "Concern of the person (wants a human, or distress)",
                  "process": "Facts could not be established by the system",
                  "legal": "Legal trigger"},
        "reason": "Reason", "urgency": "Urgency",
        "urgency_none": "no deadline computed",
        "urgency_calm": "deadline computed, not classified as urgent",
        "urgency_urgent": "urgent", "urgency_emergency": "urgent, signs of acute distress",
        "topics": "Topics", "topics_none": "not identified",
        "facts_count": "Facts", "facts_n": "{k} established, {m} open",
        "case_number": "Case number", "priority": "Priority",
        "person": "Name", "email": "E-mail", "phone": "Phone",
        "contact_none": "not given",
        "first": "Recommended first steps",
        "why": "Why this case was routed here", "wrote": "the person wrote",
        "deadlines": "Deadlines (earliest possible end, to be verified)",
        "deadlines_none": "No deadline was computed from the established facts.",
        "passed": "may already have passed", "days": "{n} working day(s) left",
        "done": "step taken according to the person", "not_done": "step NOT confirmed",
        "facts": "Established facts (with the person's own words)", "none": "None.",
        "open": "To clarify first",
        "open_none": "None of the required facts is missing.",
        "contradiction": "Contradiction",
        "issues": "Legal issues",
        "uncovered": "Not checked by the system (topic outside the stored sources, named "
                     "by the language model)",
        "fees": "Preliminary check by fixed rules (on the person's statements only; shown to "
                "the person only with the classification by the system)",
        "raised": "Raised", "possible": "Cannot be assessed yet", "missing": "missing",
        "issues_none": "The established facts do not yet raise a specific legal issue.",
        "sources": "Sources on the issues raised (selected by fixed rules, not by the model)",
        "sources_none": "None. Sources are shown only once the facts that raise a legal "
                        "issue are established.",
        "sources_empty": "No sources are stored for the issues raised.",
        "kinds_src": {"statute": "Statute", "decision": "Court decision", "commentary": "Commentary"},
        "summary": "Summary by",
        "answers": "Answers the question",
        "shown_because": "Printed because",
        "shown_issue": "the issue '{issue}' is raised (no further condition stored)",
        "pointers": "Other stored decisions on these issues (not printed)",
        "pointers_note": "The condition of these decisions is not met on the established "
                         "facts, still open, or cannot be checked. Assigned by fixed rules, "
                         "not by the model.",
        "state_manual": "cannot be checked on the recorded facts",
        "state_open": "still open, missing: {lacking}",
        "state_not_met": "not relevant on the established facts",
        "team": "the legal team",
        "conversation": "Conversation", "user": "Person", "system": "System",
        "audit": "Audit trail", "audit_none": "No entries.",
        "footer": "Generated automatically. Facts are as stated by the person and have not "
                  "been verified. Deadlines are conservative estimates.",
    },
}


def _key(rule: str) -> str:
    return rule if rule in FIRST_STEP else rule.split("-")[0]


def referral_kind(decision: Decision) -> str:
    """'legal' if a legal trigger fired, else 'person', else 'process'."""
    keys = {r.rule.split("-")[0] for r in decision.reasons}
    if keys - _PERSON - _PROCESS:
        return "legal"
    return "person" if keys & _PERSON else "process"


def select_decisions(case: Case, decision: Decision,
                     corpus: dict) -> tuple[list[tuple[dict, list[str]]],
                                            list[tuple[dict, str, list[str]]]]:
    """Stored decisions and commentary excerpts for this case, by fixed rules.

    Returns (printed, pointers). "printed" holds the entries whose issue is raised and
    whose own condition is met, each with the names of the facts that triggered it.
    "pointers" holds the other entries on a raised issue, each with its state (open,
    not met, cannot be checked) and the names of the facts still missing. Entries
    whose issue is not raised appear in neither list.
    """
    fired = {r.rule for r in decision.reasons}
    raised = {i.id for i in assess(case, decision)[0]}
    printed, pointers = [], []
    for e in corpus.values():
        if e.get("type", "statute") == "statute" or "briefing" not in e.get("use", ["briefing"]):
            continue
        state, triggers, lacking = decision_state(e, case, decision, raised, fired)
        if state == MET:
            printed.append((e, triggers))
        elif state in (MANUAL, OPEN, NOT_MET):
            pointers.append((e, state, lacking))
    order = {MANUAL: 0, OPEN: 1, NOT_MET: 2}
    pointers.sort(key=lambda x: order[x[1]])
    return printed, pointers


def relevant_sources(case: Case, decision: Decision, corpus: dict) -> list[dict]:
    """Sources printed for the lawyer: the statutes of the issues raised, the statute
    of a deadline that fired, and the stored decisions and excerpts whose issue is
    raised and whose own condition is met. No model is involved, so no source can be
    invented."""
    fired = {r.rule for r in decision.reasons}
    raised_issues, _ = assess(case, decision)
    keys: list[str] = [k for i in raised_issues for k in i.statutes]
    if "R4-deadline-close" in fired:
        keys += [STATUTE_FOR_BASIS[d.legal_basis] for d in decision.deadlines
                 if d.legal_basis in STATUTE_FOR_BASIS and not d.action_done]
    seen, out = set(), []
    for k in keys:
        if k in corpus and k not in seen:
            seen.add(k)
            out.append(corpus[k])
    out += [e for e, _ in select_decisions(case, decision, corpus)[0]]
    return out


def _excerpt(text: str, limit: int = 400) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[:limit].rsplit(" ", 1)[0] + " [...]"


def _d(day: date, lang: str) -> str:
    return day.strftime("%d.%m.%Y") if lang == "de" else day.isoformat()


def render(case: Case, decision: Decision, today: date, corpus: dict | None = None,
           consent: tuple | None = None, lang: str | None = None, summary: str = "") -> str:
    """consent: how the user agreed to the hand-over, ("button", "") or ("typed", words).
    summary: a short description written by the model (compose.summary); it is the only
    model-written part of the briefing and is labelled as unverified."""
    lang = lang if lang in T else (config.BRIEFING_LANGUAGE if config.BRIEFING_LANGUAGE in T
                                   else "de")
    t = T[lang]
    L: list[str] = []
    fired = [r.rule for r in decision.reasons]
    required = required_fields(case)
    known = [f for f in case.facts.values() if f.status is Status.KNOWN]
    missing = [s for s in required if case.fact(s.name).status is not Status.KNOWN]
    raised, possible = assess(case, decision)
    open_deadlines = [d for d in decision.deadlines if not d.action_done]

    def label(name: str) -> str:
        return LABELS.get(name, {}).get(lang, name)

    def deadline_line(d) -> str:
        left = (t["passed"] if d.working_days_left < 0
                else t["days"].format(n=d.working_days_left))
        name = texts.DEADLINE_LABELS.get(d.key, {}).get(lang, d.label)
        return (f"{name}, {d.legal_basis}: {_d(d.due, lang)} "
                f"({left}; {t['done'] if d.action_done else t['not_done']})")

    # ---- head and overview ------------------------------------------------------
    L.append(f"# {t['urgent'] if decision.urgent else ''}{t['title']}")
    level, basis, carrying = priority.classify(decision)
    meta = [f"{t['date']}: {_d(today, lang)}", f"{t['user_lang']}: {t['langs'][case.language]}"]
    if case.case_number:
        meta.insert(0, f"{t['case_number']}: {case.case_number}")
    if consent:
        how, said = consent
        meta.append(f"{t['consent']}: "
                    + (t["consent_typed"].format(said=said) if how == "typed"
                       else t["consent_button"]))
    L.append(" | ".join(meta))

    L.append(f"\n## {t['overview']}")
    # Priority class for the team's work queue: fixed rules (priority.py), no model call.
    carried = "; ".join(dict.fromkeys(texts.rule_label(r, lang) for r in carrying))
    L.append(f"- **{t['priority']}:** {priority.LABELS[level][lang]} – "
             + priority.BASIS[basis][lang].format(reasons=carried))
    L.append(f"- **{t['kind']}:** {t['kinds'][referral_kind(decision)]}")
    reasons, seen = [], set()
    for rule in fired:
        text = texts.rule_label(rule, lang)
        if text not in seen:
            seen.add(text)
            reasons.append(text)
    L.append(f"- **{t['reason']}:** {'; '.join(reasons)}")
    if decision.emergency:
        urgency = t["urgency_emergency"]
    elif decision.urgent:
        urgency = t["urgency_urgent"]
    else:
        urgency = t["urgency_calm"] if open_deadlines else t["urgency_none"]
    if decision.urgent and open_deadlines:
        urgency += " – " + deadline_line(min(open_deadlines, key=lambda d: d.due))
    L.append(f"- **{t['urgency']}:** {urgency}")
    topics = ", ".join(AREA_LABELS.get(a, {}).get(lang, a) for a in sorted(case.areas))
    L.append(f"- **{t['topics']}:** {topics or t['topics_none']}")
    L.append(f"- **{t['facts_count']}:** {t['facts_n'].format(k=len(known), m=len(missing))}")
    who = case.contact or {}
    L.append(f"- **{t['person']}:** {full_name(who) or t['contact_none']}")
    L.append(f"- **{t['email']}:** {who.get('email') or t['contact_none']}")
    L.append(f"- **{t['phone']}:** {who.get('phone') or t['contact_none']}")
    L.append(f"- **{t['first']}:**")
    order = list(FIRST_STEP)
    keys = sorted({_key(r) for r in fired if _key(r) in FIRST_STEP}, key=order.index)
    for k in keys:
        L.append(f"  {FIRST_STEP[k][lang]}")

    if case.uncovered:
        L.append(f"- **{t['uncovered']}:** {case.uncovered['topic']} – {t['wrote']}: "
                 f"«{case.uncovered['evidence']}»")
    if summary:
        L.append(f"\n## {texts.SUMMARY_LABEL[lang]}")
        L.append(summary)

    # ---- why ----------------------------------------------------------------------
    L.append(f"\n## {t['why']}")
    for r in decision.reasons:
        detail = f" ({r.text})" if lang == "en" else ""
        ev = f' – {t["wrote"]}: «{r.evidence}»' if r.evidence else ""
        L.append(f"- [{r.rule}] {texts.rule_label(r.rule, lang)}{detail}{ev}")

    L.append(f"\n## {t['deadlines']}")
    if decision.deadlines:
        L.extend(f"- {deadline_line(d)}" for d in decision.deadlines)
    else:
        L.append(f"- {t['deadlines_none']}")

    L.append(f"\n## {t['facts']}")
    if known:
        for f in known:
            L.append(f"- {label(f.name)}: {display_value(f.value, lang, f.name)} – «{f.evidence}»")
    else:
        L.append(f"- {t['none']}")

    L.append(f"\n## {t['open']}")
    for s in missing:
        status = texts.STATUS_LABELS[case.fact(s.name).status.value][lang]
        L.append(f"- {label(s.name)} ({status})")
    for c in case.contradictions:
        L.append(f"- {t['contradiction']}: {c}")
    if not missing and not case.contradictions:
        L.append(f"- {t['open_none']}")

    # ---- legal issues and their sources -------------------------------------------
    L.append(f"\n## {t['issues']}")
    for issue in raised:
        L.append(f"- **{t['raised']}:** {issue.title[lang]}")
    for issue, lacking in possible:
        L.append(f"- {t['possible']}: {issue.title[lang]} – {t['missing']}: "
                 + ", ".join(label(n) for n in lacking))
    if not raised and not possible:
        L.append(f"- {t['issues_none']}")

    # What the fixed rules of the fields give for the answers so far (late fees,
    # declining an inheritance).
    for result in fixed_results(case, decision, lang):
        if not result["positions"]:
            continue
        L.append(f"\n## {t['fees']}: {result['title']}")
        if result["summary"]:
            L.append(result["summary"])
        for p in result["positions"]:
            cites = ", ".join(c["citation"] for c in p["citations"])
            L.append(f"- **{p['title']}: {p['verdict_label']}**" + (f" ({cites})" if cites else ""))
            L.append(f"  {p['text']}")

    L.append(f"\n## {t['sources']}")
    corpus = load_corpus() if corpus is None else corpus
    srcs = relevant_sources(case, decision, corpus)
    printed, pointers = select_decisions(case, decision, corpus)
    triggers_of = {id(e): names for e, names in printed}
    derived_values = derived(case, decision)
    raised_ids = {i.id for i in raised}

    def item_text(name: str) -> str:
        """One fact or derived item that a condition refers to, in plain words."""
        if name.startswith("@"):
            value = derived_values.get(name)
            return (f"{DERIVED_LABELS[name][lang]}: "
                    f"{DERIVED_VALUE_LABELS.get(value, {}).get(lang, value)}")
        f = case.facts.get(name)
        if f and f.status is Status.KNOWN:
            ev = f" – «{f.evidence}»" if f.evidence else ""
            return f"{label(name)}: {display_value(f.value, lang, name)}{ev}"
        status = (f.status if f else Status.MISSING).value
        return f"{label(name)}: {texts.STATUS_LABELS[status][lang]}"

    def question(e: dict) -> str:
        q = e.get("question") or {}
        return q.get(lang) or q.get("de") or q.get("en") or ""

    if srcs:
        for e in srcs:
            kind = t["kinds_src"].get(e.get("type", "statute"), "")
            link = f" - {e['url']}" if e.get("url") else ""
            L.append(f"- **{kind}: {e['citation']}**{link}")
            if id(e) in triggers_of:
                if question(e):
                    L.append(f"  {t['answers']}: {question(e)}")
                names = triggers_of[id(e)]
                if names:
                    L.append(f"  {t['shown_because']}: " + "; ".join(item_text(n) for n in names))
                elif e.get("issues"):
                    titles = ", ".join(ISSUE_BY_ID[i].title[lang] for i in e["issues"]
                                       if i in raised_ids and i in ISSUE_BY_ID)
                    L.append(f"  {t['shown_because']}: {t['shown_issue'].format(issue=titles)}")
            if e.get("holding"):
                L.append(f"  {t['summary']} {e.get('selected_by') or t['team']}: {e['holding']}")
            # Statutes are shown as a short reminder; passages of decisions and
            # commentary in full, because the lawyer needs their reasoning.
            limit = 400 if e.get("type", "statute") == "statute" else 2500
            L.append(f"  \"{_excerpt(e['text'], limit)}\"")
    else:
        L.append(f"- {t['sources_empty'] if raised else t['sources_none']}")

    if pointers:
        L.append(f"\n### {t['pointers']}")
        L.append(t["pointers_note"])
        for e, state, lacking in pointers:
            if state == OPEN:
                names = [DERIVED_LABELS[n][lang] if n.startswith("@") else label(n)
                         for n in lacking]
                note = t["state_open"].format(lacking="; ".join(names))
            else:
                note = t["state_manual"] if state == MANUAL else t["state_not_met"]
            kind = t["kinds_src"].get(e.get("type", "statute"), "")
            link = f" - {e['url']}" if e.get("url") else ""
            q = f" – {question(e)}" if question(e) else ""
            L.append(f"- {kind}: {e['citation']}{q} ({note}){link}")

    L.append(f"\n## {t['conversation']}")
    for role, text in case.messages:
        L.append(f"**{t['user'] if role == 'user' else t['system']}:** {text}")

    L.append(f"\n## {t['audit']}")
    L.extend(f"- {a}" for a in case.audit) if case.audit else L.append(f"- {t['audit_none']}")
    L.append(f"\n_{t['footer']}_")
    return "\n".join(L)


# Letters and digits that are not mistaken for one another when read out or copied.
_CASE_ALPHABET = "23456789ABCDEFGHJKMNPQRSTUVWXYZ"


def new_case_number(today: date) -> str:
    """A case number such as LX-20261115-7K3F: the day of the hand-over and four random
    characters. It is not a running count, so it does not reveal how many cases there
    are. It is unique among the briefings in the outbox folder; the prototype has no
    database of cases."""
    out = Path(config.OUTBOX_DIR)
    for _ in range(100):
        number = (f"LX-{today.strftime('%Y%m%d')}-"
                  + "".join(secrets.choice(_CASE_ALPHABET) for _ in range(4)))
        if not out.is_dir() or not any(out.glob(f"*{number}*")):
            return number
    raise RuntimeError("no free case number")


def deliver(text: str, urgent: bool, case_number: str = "",
            priority: int = 0) -> tuple[Path, bool]:
    """Write to the outbox; send by e-mail if SMTP is configured. Returns (path, mailed).
    The priority class and the case number are part of the file name and of the subject,
    so the team sees what to work on first without opening the briefing."""
    out = Path(config.OUTBOX_DIR)
    out.mkdir(parents=True, exist_ok=True)
    tags = "".join(f"_{x}" for x in (f"P{priority}" if priority else "", case_number) if x)
    path = out / f"briefing_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}{tags}.md"
    path.write_text(text, encoding="utf-8")

    host, to = os.environ.get("SMTP_HOST"), os.environ.get("BRIEFING_TO")
    if not (host and to):
        return path, False
    msg = EmailMessage()
    msg["Subject"] = ((f"[P{priority}] " if priority else "") + ("[URGENT] " if urgent else "")
                      + "Case briefing from intake system"
                      + (f" {case_number}" if case_number else ""))
    msg["From"] = os.environ.get("BRIEFING_FROM", to)
    msg["To"] = to
    msg.set_content(text)
    with smtplib.SMTP(host, int(os.environ.get("SMTP_PORT", "587"))) as s:
        s.starttls()
        if os.environ.get("SMTP_USER"):
            s.login(os.environ["SMTP_USER"], os.environ.get("SMTP_PASSWORD", ""))
        s.send_message(msg)
    return path, True


__all__ = ["render", "deliver", "new_case_number", "required_fields"]

FIRST_STEP["R13"] = {"de": "Genannten Sonderfall und amtliche Unterlagen prüfen; Fristen und die Wirksamkeit berichteter Erklärungen unabhängig kontrollieren.", "en": "Review the identified exception and official documents; independently check deadlines and the validity of reported declarations."}
FIRST_STEP["R14"] = {"de": "Die Person fragt nach einem Thema, das die hinterlegten Quellen nicht abdecken (siehe «Vom System nicht geprüft»). Das System hat dazu nichts gesagt; diese Frage zuerst klären.", "en": "The person asks about a topic the stored sources do not cover (see 'Not checked by the system'). The system said nothing on it; clarify this question first."}
