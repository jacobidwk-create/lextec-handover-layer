"""PROCEED output: a general legal classification with the facts of the case.

Only reachable after the gate returned PROCEED.

Late fees (area debt_collection) are not drafted by the model at all: their result
comes from the fixed texts and rules in late_fees.py. For the other areas, legal
statements are drafted by the model, but each one must pass the citation check
before it is shown:
  1. the cited source must exist in the local corpus (code),
  2. the quoted passage must appear word for word in that source (code),
  3. a separate model call must confirm the passage supports the statement.
Statements that fail any step are dropped. Deadlines are never written by the
model; they come from deadlines.py.
"""
from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

from . import inheritance, late_fees, register, texts
from .areas import LABELS, display_facts, required_fields
from .llm import LLM
from .legal_fields import playbooks, statute_keys
from .legal_logic import legal_context
from .schema import Case, Decision, Status

CORPUS_PATH = Path(__file__).resolve().parent.parent / "sources" / "corpus.json"

DRAFT_SYSTEM = """You write a general legal classification for a layperson in \
Switzerland (Canton of Zurich) who has a debt-related problem. Write in the language \
given, in a warm, calm and respectful tone, in plain everyday words. You are given the \
established facts and a set of statutory sources.

Rules:
- Follow legal_branch_limits in the facts. They restrict what may be said.
- Use ONLY the given sources. If the sources do not cover a point, do not mention it.
- Every statement must be RELEVANT to the facts of this user. Start with what matters \
in the user's present situation. Rules about a later stage that the user has not reached \
(for example a payment order when the user has only received a bill or reminder) may be \
mentioned only as what could come next, and must be worded that way ("If you later \
receive ...").
- Sources marked [court decision] decided one specific case. Present them as such \
("The Federal Supreme Court held in one case that ..."), never as a general rule.
- General information only: explain what the law provides for situations like this. \
Do not predict the outcome of this case, and do not say whether a specific charge is \
owed or not.
- You may state periods exactly as the source states them (for example "within ten \
days"). Never compute calendar dates.
- 3 to 5 statements. Each has two or three sentences: what the law provides, and what \
that means in practice for someone in this situation.
- For every statement give "source_id" and "quote": a passage copied word for word \
from that source which supports the statement.

Return JSON: {"statements": [{"text": "...", "source_id": "...", "quote": "..."}]}"""

CHECK_SYSTEM = """You verify a legal information text. You get the established facts of \
a user and numbered items, each with a statement and a passage from a Swiss statute. \
For each item decide two things:
- "supported": does the passage, read on its own, support the statement? Be strict: if \
the statement claims more than the passage says, answer false.
- "relevant": is the statement relevant to this user's facts, and if it concerns a stage \
the user has not reached, is it clearly worded as a possible later step?

Return JSON: {"results": [{"index": 0, "supported": true, "relevant": true}]}"""

T = {
    "de": {"intro": "Danke, jetzt habe ich ein klares Bild. Hier ist meine Einordnung.",
           "correct_me": "Stimmt etwas davon nicht? Dann schreiben Sie es mir bitte, denn "
                         "die Einordnung hängt davon ab.",
           "facts": "So habe ich Ihre Angaben verstanden", "class": "Allgemeine rechtliche Einordnung",
           "deadlines": "Fristen (frühestmögliches Ende, bitte selbst prüfen)",
           "open": "Offene Punkte", "none_src": "Für diese Einordnung liegen keine geprüften "
           "Quellen vor. Es wird deshalb keine rechtliche Aussage gemacht.",
           "left": "Arbeitstag(e) verbleibend", "done": "Schritt berichtet; Wirksamkeit nicht geprüft",
           "disclaimer": "Dies ist eine allgemeine Information und keine Rechtsberatung. Sie "
           "beruht nur auf Ihren Angaben und wahrt keine Fristen. Wenn Sie mit einer "
           "Rechtsberaterin oder einem Rechtsberater sprechen möchten, schreiben Sie das "
           "einfach."},
    "en": {"intro": "Thank you, I now have a clear picture. Here is my classification.",
           "correct_me": "Is any of this wrong? Then please tell me, because the "
                         "classification depends on it.",
           "facts": "This is how I understood your information", "class": "General legal classification",
           "deadlines": "Deadlines (earliest possible end, please verify yourself)",
           "open": "Open points", "none_src": "No verified sources are available for this "
           "classification, so no legal statement is made.",
           "left": "working day(s) left", "done": "step reported; legal validity not verified",
           "disclaimer": "This is general information, not legal advice. It is based only on "
           "what you told me and does not preserve any deadlines. If you would like to speak "
           "to a legal advisor, just say so."},
}


SOURCES_DIR = CORPUS_PATH.parent
EXTRA_CORPORA = (SOURCES_DIR / "case_law.json", SOURCES_DIR / "licensed" / "commentary.json")


def load_corpus(path: Path = CORPUS_PATH) -> dict:
    """Statutes, verified court decisions and (if present) licensed commentary."""
    corpus: dict = {}
    for p in (path, *EXTRA_CORPORA):
        if p.exists():
            for key, entry in json.loads(p.read_text(encoding="utf-8")).items():
                entry.setdefault("type", "statute")
                entry.setdefault("use", ["briefing", "user"] if entry["type"] == "statute"
                                 else ["briefing"])
                corpus[key] = entry
    return corpus


def usable_for_user(entry: dict) -> bool:
    """Commentary never reaches the user; decisions only if released for it."""
    return entry.get("type", "statute") != "commentary" and "user" in entry.get("use", ["user"])


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip().lower()


def check_citations(statements: list, sources: dict, llm: LLM, audit: list,
                    facts: dict | None = None) -> list[dict]:
    """Return only the statements that pass all three checks."""
    candidates = []
    for s in statements:
        if not isinstance(s, dict):
            continue
        src = sources.get(s.get("source_id"))
        quote = s.get("quote") or ""
        if src is None:
            audit.append(f"citation rejected: unknown source {s.get('source_id')!r}")
        elif len(quote.strip()) < 15 or _norm(quote) not in _norm(src["text"]):
            audit.append(f"citation rejected: quote not found in {s.get('source_id')}")
        elif not (s.get("text") or "").strip():
            audit.append("citation rejected: empty statement")
        else:
            candidates.append(s)
    if not candidates:
        return []
    items = (f"Facts: {json.dumps(facts or {}, ensure_ascii=False)}\n\n"
             + "\n\n".join(f"[{i}] Statement: {s['text']}\nPassage: {s['quote']}"
                           for i, s in enumerate(candidates)))
    try:
        res = llm.complete_json(CHECK_SYSTEM, items)
        supported = {r["index"] for r in res.get("results", [])
                     if isinstance(r, dict) and r.get("supported") is True
                     and r.get("relevant") is True}
    except Exception as e:
        audit.append(f"citation check failed ({type(e).__name__}); all statements dropped")
        return []
    for i, s in enumerate(candidates):
        if i not in supported:
            audit.append("citation rejected: statement not supported by the passage or not "
                         f"relevant to the facts ({s['source_id']})")
    return [s for i, s in enumerate(candidates) if i in supported]


# Legal fields whose result is built from fixed rules and texts, not drafted by the model.
FIXED_RESULTS = {
    "debt_collection": lambda case, decision, lang: late_fees.assess(case, lang),
    "inheritance_debt": lambda case, decision, lang: inheritance.assess(case, decision, lang),
    "credit_record": lambda case, decision, lang: register.assess(case, decision, lang),
}


def fixed_results(case: Case, decision: Decision | None, lang: str | None = None) -> list[dict]:
    """The fixed results of the case's fields, in the order of FIXED_RESULTS."""
    out = []
    for area, build in FIXED_RESULTS.items():
        if area in case.areas:
            result = build(case, decision, lang)
            if result:
                out.append(result)
    return out


def _open_points(case: Case) -> list[str]:
    """Required facts that are not established, in the user's words."""
    lang, out = case.language, []
    for spec in required_fields(case):
        f = case.fact(spec.name)
        if f.status is not Status.KNOWN and spec.name in LABELS:
            out.append(f"{LABELS[spec.name][lang]}: {texts.STATUS_LABELS[f.status.value][lang]}")
    return out


def classify_structured(case: Case, decision: Decision, llm: LLM,
                        corpus: dict | None = None) -> tuple[str, dict]:
    """The classification as plain text and as structured data for the web page."""
    lang = case.language
    t = T[lang]
    corpus = load_corpus() if corpus is None else corpus
    # Fields with a fixed result (late fees, declining an inheritance, register entries): the result comes
    # from fixed rules and texts. The model drafts nothing for these fields, so their
    # sources are not offered to the drafting model either.
    assessments = fixed_results(case, decision)
    assessment = assessments[0] if assessments else None
    drafted_areas = set(case.areas) - set(FIXED_RESULTS)
    listed = set(statute_keys(drafted_areas))        # articles named by the field files
    sources = {k: v for k, v in corpus.items()
               if (set(v.get("areas", [])) & drafted_areas or k in listed)
               and usable_for_user(v)}

    known = {f.name: (f.value.isoformat() if isinstance(f.value, date) else f.value)
             for f in case.facts.values() if f.status is Status.KNOWN}

    known["legal_branch_limits"] = legal_context(case, getattr(decision, "assessed_on", None) or date.today())
    statements: list[dict] = []
    if sources:
        src_text = "\n\n".join(
            f"[{k}] {v['citation']}{' [court decision]' if v.get('type') == 'decision' else ''}"
            f"\n{v['text']}" for k, v in sources.items())
        user = (f"Language: {lang}\nAreas: {', '.join(sorted(case.areas))}\n"
                f"Facts: {json.dumps(known, ensure_ascii=False)}\n\n"
                f"Legal flow of the field (follow it):\n{playbooks(drafted_areas)}\n\n"
                f"Sources:\n{src_text}")
        try:
            draft = llm.complete_json(DRAFT_SYSTEM, user)
            statements = check_citations(draft.get("statements") or [], sources, llm,
                                         case.audit, known)
        except Exception as e:
            case.audit.append(f"classification draft failed: {type(e).__name__}")

    deadlines = []
    for d in decision.deadlines:
        deadlines.append({
            "label": texts.DEADLINE_LABELS.get(d.key, {}).get(lang, d.label),
            "basis": d.legal_basis,
            "due": d.due.strftime("%d.%m.%Y"),
            "done": d.action_done,
            "state": t["done"] if d.action_done else f"{d.working_days_left} {t['left']}",
        })

    data = {
        "intro": t["intro"],
        "facts_title": t["facts"], "facts": display_facts(case), "correct_me": t["correct_me"],
        "class_title": t["class"],
        "statements": [{"text": s["text"], "citation": sources[s["source_id"]]["citation"],
                        "url": sources[s["source_id"]].get("url", ""),
                        "type": sources[s["source_id"]].get("type", "statute")}
                       for s in statements],
        "assessment": assessment, "assessments": assessments,
        "no_sources": "" if statements or assessment else t["none_src"],
        "deadlines_title": t["deadlines"], "deadlines": deadlines,
        "open_title": t["open"], "open": _open_points(case),
        "disclaimer": t["disclaimer"],
    }
    return render_classification(data), data


def render_classification(d: dict) -> str:
    out = [d["intro"], "", f"**{d['facts_title']}**"] + [f"- {x}" for x in d["facts"]]
    out.append(d["correct_me"])
    for a in d.get("assessments") or ([d["assessment"]] if d.get("assessment") else []):
        out.append("\n" + late_fees.render(a))
    if d["statements"] or not d.get("assessment"):
        out.append(f"\n**{d['class_title']}**")
        if d["statements"]:
            out += [f"- {s['text']} ({s['citation']}, {s['url']})" for s in d["statements"]]
        else:
            out.append(d["no_sources"])
    if d["deadlines"]:
        out.append(f"\n**{d['deadlines_title']}**")
        out += [f"- {x['label']}, {x['basis']}: {x['due']} ({x['state']})" for x in d["deadlines"]]
    if d["open"]:
        out.append(f"\n**{d['open_title']}**")
        out += [f"- {u}" for u in d["open"]]
    out.append("\n" + d["disclaimer"])
    return "\n".join(out)


def classify(case: Case, decision: Decision, llm: LLM, corpus: dict | None = None) -> str:
    return classify_structured(case, decision, llm, corpus)[0]
