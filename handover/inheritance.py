"""Declining an inheritance: what the answers to the gates mean. Plain Python, no model.

The legal lead's flow of 2026-11-13 (full_report.md section 3.4b) examines the situation of an
heir who fears debts in four steps:

  gate 1   is the three-month period still open        (heir_basis and the start date)
  gate 1B  if it passed: was the deceased manifestly insolvent   (estate_insolvency)
  gate 2   did the heir interfere in the estate        (estate_actions)
  gate 3   what is known about the estate's finances   (estate_finances)
  gate 4   traps on disclaiming                        (shown as notes, not asked)

The questions are defined in areas.py, the dates are computed in deadlines.py, and the
route is decided in rules.py. This file turns the answers into the result shown after
PROCEED, built like the late-fee result (late_fees.py): one fixed text per outcome,
with the article it rests on and the terms it uses. The model writes none of it.

DRAFTS: the texts follow the flow supplied by the legal lead and are to be reviewed.
"""
from __future__ import annotations

from . import knowledge
from .areas import disclaimer_state, established
from .schema import Case, Decision, Status

VERDICTS = {
    "running": {"de": "Frist läuft", "en": "Period running"},
    "act_now": {"de": "Sofort handeln", "en": "Act at once"},
    "presumed": {"de": "Ausschlagung wird vermutet", "en": "Disclaimer presumed"},
    "intact": {"de": "Recht auszuschlagen bleibt", "en": "Right to disclaim remains"},
    "at_risk": {"de": "Möglicherweise verwirkt", "en": "Possibly forfeited"},
    "case_by_case": {"de": "Hängt vom Einzelfall ab", "en": "Depends on the individual case"},
    "disclaim": {"de": "Ausschlagung erklären", "en": "Declare the disclaimer"},
    "option": {"de": "Möglichkeit", "en": "Option"},
    "info": {"de": "Kein Schuldenrisiko erkennbar", "en": "No debt risk apparent"},
}

T = {
    "title": {"de": "Was für Ihre Erbschaft gilt", "en": "What applies to your inheritance"},
    "basis": {
        "de": "Diese Einordnung folgt festen Regeln und stützt sich nur auf Ihre Antworten. "
              "Sie ist eine allgemeine Information, keine Rechtsberatung im Einzelfall, und "
              "sie wahrt keine Frist.",
        "en": "This classification follows fixed rules and rests only on your answers. It is "
              "general information, not legal advice on your individual case, and it does "
              "not preserve any deadline."},
    "open": {
        "de": "Nach Ihren Angaben läuft die Frist für die Ausschlagung noch.",
        "en": "According to your answers the period for disclaiming is still running."},
    "passed": {
        "de": "Nach Ihren Angaben könnte die Frist für die Ausschlagung abgelaufen sein.",
        "en": "According to your answers the period for disclaiming may have passed."},
    "notes_title": {"de": "Gut zu wissen, bevor Sie ausschlagen",
                    "en": "Good to know before you disclaim"},
    "source": {"de": "Quelle", "en": "Source"},
    "terms": {"de": "Begriffe", "en": "Terms"},
}

_AUTHORITY = {
    "de": "Zuständig ist die Behörde am letzten Wohnsitz der verstorbenen Person; im Kanton "
          "Zürich ist das das Bezirksgericht.",
    "en": "The competent authority is the one at the last domicile of the deceased; in the "
          "Canton of Zurich this is the district court (Bezirksgericht).",
}

FINDINGS: dict[str, dict] = {
    # ---- gate 1: the period ---------------------------------------------------------
    "period_statutory": {
        "title": {"de": "Frist für die Ausschlagung", "en": "Period for disclaiming"},
        "verdict": "running",
        "text": {
            "de": "Die Frist beträgt drei Monate. Für gesetzliche Erben beginnt sie in der "
                  "Regel an dem Tag, an dem sie vom Tod erfahren. Das früheste Fristende "
                  "nach Ihren Angaben steht unten bei den Fristen; es ist ein vorsichtiger "
                  "Prüfwert.",
            "en": "The period is three months. For statutory heirs it normally starts on the "
                  "day they learn of the death. The earliest end of the period according to "
                  "your answers is shown below under deadlines; it is a cautious screening "
                  "date."},
        "sources": (("zgb", "567", "Art. 567 ZGB"),),
        "terms": ("term_ausschlagung", "term_erbenstellung"),
    },
    "period_appointed": {
        "title": {"de": "Frist für die Ausschlagung", "en": "Period for disclaiming"},
        "verdict": "running",
        "text": {
            "de": "Die Frist beträgt drei Monate. Für Erben aus einem Testament oder "
                  "Erbvertrag beginnt sie mit der amtlichen Mitteilung der Verfügung. Das "
                  "früheste Fristende nach Ihren Angaben steht unten bei den Fristen; es ist "
                  "ein vorsichtiger Prüfwert.",
            "en": "The period is three months. For heirs named in a will or an inheritance "
                  "contract it starts with the official notification of the disposition. "
                  "The earliest end of the period according to your answers is shown below "
                  "under deadlines; it is a cautious screening date."},
        "sources": (("zgb", "567", "Art. 567 ZGB"),),
        "terms": ("term_ausschlagung", "term_erbenstellung"),
    },
    "period_successor": {
        "title": {"de": "Frist für die Ausschlagung", "en": "Period for disclaiming"},
        "verdict": "running",
        "text": {
            "de": "Die Frist beträgt drei Monate. Wer erst erbt, weil jemand vor ihm "
                  "ausgeschlagen hat, hat sie ab dem Tag, an dem er davon erfährt. Hat die "
                  "Behörde Sie nach der Ausschlagung anderer angefragt, gilt etwas anderes: "
                  "Wer dann nicht innert eines Monats die Annahme erklärt, hat ebenfalls "
                  "ausgeschlagen.",
            "en": "The period is three months. A person who inherits only because someone "
                  "before them disclaimed has it from the day they learn of this. If the "
                  "authority asked you after others disclaimed, something else applies: a "
                  "person who then does not declare acceptance within one month has also "
                  "disclaimed."},
        "sources": (("zgb", "567", "Art. 567 ZGB"), ("zgb", "575", "Art. 575 ZGB")),
        "terms": ("term_ausschlagung",),
    },
    "period_passed": {
        "title": {"de": "Frist abgelaufen", "en": "Period passed"},
        "verdict": "act_now",
        "text": {
            "de": "Wer nicht innert der Frist ausschlägt, hat die Erbschaft vorbehaltlos "
                  "erworben. Aus wichtigen Gründen kann die zuständige Behörde die Frist "
                  "verlängern oder eine neue Frist ansetzen. Ein solches Gesuch ist sofort "
                  "zu stellen und zu begründen. " + _AUTHORITY["de"],
            "en": "A person who does not disclaim within the period has acquired the "
                  "inheritance without reservation. For important reasons the competent "
                  "authority can extend the period or set a new one. Such a request has to "
                  "be made at once, with reasons. " + _AUTHORITY["en"]},
        "sources": (("zgb", "571", "Art. 571 Abs. 1 ZGB"), ("zgb", "576", "Art. 576 ZGB")),
        "terms": ("term_fristverlaengerung",),
    },
    "presumed": {
        "title": {"de": "Frist abgelaufen, Erblasser offenkundig zahlungsunfähig",
                  "en": "Period passed, deceased manifestly insolvent"},
        "verdict": "presumed",
        "text": {
            "de": "War die Zahlungsunfähigkeit der verstorbenen Person beim Tod amtlich "
                  "festgestellt oder offenkundig, wird die Ausschlagung von Gesetzes wegen "
                  "vermutet. Eine Erklärung ist dann nicht nötig. Das gilt nicht für "
                  "jemanden, der sich in den Nachlass eingemischt hat. Ob die "
                  "Zahlungsunfähigkeit offenkundig war, kann im Streitfall zu beweisen sein.",
            "en": "If the insolvency of the deceased at death was officially established or "
                  "manifest, the disclaimer is presumed by law. A declaration is then not "
                  "needed. This does not apply to someone who interfered in the estate. "
                  "Whether the insolvency was manifest may have to be proven in a dispute."},
        "sources": (("zgb", "566", "Art. 566 Abs. 2 ZGB"),),
        "terms": ("term_zahlungsunfaehig",),
    },
    # ---- gate 2: interference -----------------------------------------------------------
    "actions_safe": {
        "title": {"de": "Umgang mit dem Nachlass", "en": "Dealings with the estate"},
        "verdict": "intact",
        "text": {
            "de": "Wer nichts anrührt oder nur das Nötigste verwaltet, zum Beispiel die "
                  "Wohnung sichert, dringende Rechnungen wie die Bestattung bezahlt oder "
                  "Auskünfte einholt, verliert das Recht auszuschlagen nicht. Solange Sie "
                  "nicht entschieden haben, gilt: nichts aus dem Nachlass an sich nehmen, "
                  "verkaufen oder verschenken und keine Konten leeren.",
            "en": "A person who touches nothing or only administers what is necessary, for "
                  "example secures the home, pays urgent bills such as the funeral or asks "
                  "for information, does not lose the right to disclaim. As long as you have "
                  "not decided: take, sell or give away nothing from the estate, and do not "
                  "empty any accounts."},
        "sources": (("zgb", "571", "Art. 571 Abs. 2 ZGB"),),
        "terms": ("term_einmischung",),
    },
    "actions_took": {
        "title": {"de": "Umgang mit dem Nachlass", "en": "Dealings with the estate"},
        "verdict": "at_risk",
        "text": {
            "de": "Wer Nachlassgegenstände an sich nimmt oder verheimlicht oder mehr tut als "
                  "die blosse Verwaltung, kann die Erbschaft nicht mehr ausschlagen. Sie "
                  "gilt dann als angenommen, und die Schulden der verstorbenen Person werden "
                  "zu eigenen Schulden. Ob Ihre Handlungen so weit gehen, hängt vom "
                  "Einzelfall ab; das sollte ein:e Rechtsberater:in beurteilen. Bis dahin "
                  "gilt: nichts weiter aus dem Nachlass nehmen oder verändern.",
            "en": "A person who takes or hides estate assets, or does more than merely "
                  "administer, can no longer disclaim the inheritance. It then counts as "
                  "accepted, and the debts of the deceased become the heir's own debts. "
                  "Whether your acts go that far depends on the individual case; a legal "
                  "advisor should assess it. Until then: take or change nothing further in "
                  "the estate."},
        "sources": (("zgb", "571", "Art. 571 Abs. 2 ZGB"), ("zgb", "560", "Art. 560 ZGB")),
        "terms": ("term_einmischung", "term_erbschaft_schulden"),
    },
    # ---- gate 3: the finances of the estate ---------------------------------------------
    "finances_overindebted": {
        "title": {"de": "Überschuldeter Nachlass", "en": "Over-indebted estate"},
        "verdict": "disclaim",
        "text": {
            "de": "Die Ausschlagung erklären Sie mündlich oder schriftlich bei der "
                  "zuständigen Behörde, unbedingt und vorbehaltlos, innert der Frist. "
                  + _AUTHORITY["de"],
            "en": "You declare the disclaimer orally or in writing to the competent "
                  "authority, unconditionally and without reservation, within the period. "
                  + _AUTHORITY["en"]},
        "sources": (("zgb", "570", "Art. 570 ZGB"),),
        "terms": ("term_ausschlagung",),
    },
    "finances_uncertain_inventory": {
        "title": {"de": "Unklare Finanzen: öffentliches Inventar",
                  "en": "Unclear finances: public inventory"},
        "verdict": "option",
        "text": {
            "de": "Ist unklar, ob Schulden da sind, können Sie innert eines Monats ein "
                  "öffentliches Inventar verlangen, in derselben Form wie die Ausschlagung. "
                  "Die Behörde ruft dann die Gläubiger auf. Danach wählen Sie: ausschlagen, "
                  "die amtliche Liquidation verlangen, unter öffentlichem Inventar annehmen "
                  "oder vorbehaltlos annehmen. Wer unter öffentlichem Inventar annimmt, "
                  "haftet für die darin verzeichneten Schulden auch mit dem eigenen "
                  "Vermögen. Das Inventar ist mit Kosten verbunden.",
            "en": "If it is unclear whether there are debts, you can request a public "
                  "inventory within one month, in the same form as the disclaimer. The "
                  "authority then calls on the creditors. Afterwards you choose: disclaim, "
                  "request official liquidation, accept under public inventory, or accept "
                  "without reservation. A person who accepts under public inventory is "
                  "liable for the debts listed in it also with their own assets. The "
                  "inventory involves costs."},
        "sources": (("zgb", "580", "Art. 580 ZGB"), ("zgb", "588", "Art. 588 ZGB"),
                    ("zgb", "589", "Art. 589 ZGB")),
        "terms": ("term_oeffentliches_inventar", "term_amtliche_liquidation"),
    },
    "finances_uncertain_late": {
        "title": {"de": "Unklare Finanzen: amtliche Liquidation oder Ausschlagung",
                  "en": "Unclear finances: official liquidation or disclaimer"},
        "verdict": "option",
        "text": {
            "de": "Die Monatsfrist für ein öffentliches Inventar ist nach Ihren Angaben "
                  "abgelaufen; die Frist für die Ausschlagung läuft noch. Statt auszuschlagen "
                  "können Sie die amtliche Liquidation verlangen: Dann haften Sie nicht für "
                  "die Schulden des Nachlasses. Das geht nicht, solange ein Miterbe die "
                  "Annahme erklärt. Sonst bleibt die Ausschlagung.",
            "en": "The one-month period for a public inventory has passed according to your "
                  "answers; the period for disclaiming is still running. Instead of "
                  "disclaiming you can request official liquidation: you are then not "
                  "liable for the debts of the estate. This is not possible as long as a "
                  "co-heir declares acceptance. Otherwise the disclaimer remains."},
        "sources": (("zgb", "593", "Art. 593 ZGB"), ("zgb", "580", "Art. 580 Abs. 2 ZGB"),
                    ("zgb", "570", "Art. 570 ZGB")),
        "terms": ("term_amtliche_liquidation", "term_oeffentliches_inventar"),
    },
    "finances_solvent": {
        "title": {"de": "Nachlass mit mehr Vermögen als Schulden",
                  "en": "Estate with more assets than debts"},
        "verdict": "info",
        "text": {
            "de": "Ist klar mehr Vermögen da als Schulden, gibt es wegen der Schulden keinen "
                  "Grund auszuschlagen. Wer trotzdem ausschlägt, verzichtet auf Vermögen; das "
                  "kann eigene Folgen haben, siehe unten.",
            "en": "If there are clearly more assets than debts, the debts are no reason to "
                  "disclaim. A person who disclaims all the same gives up assets; this can "
                  "have consequences of its own, see below."},
        "sources": (("zgb", "560", "Art. 560 ZGB"),),
        "terms": ("term_erbschaft_schulden",),
    },
}

# Gate 4: traps on disclaiming, shown as notes. They are worded conditionally ("if you
# have children ..."), so they need no question.
NOTES: dict[str, dict] = {
    "children": {
        "title": {"de": "Wenn Sie Kinder haben", "en": "If you have children"},
        "text": {
            "de": "Schlagen Sie aus, geht Ihr Anteil in der Regel an Ihre eigenen Kinder "
                  "weiter, wie wenn Sie vor der verstorbenen Person gestorben wären. Sollen "
                  "auch sie nicht erben, ist auch für sie auszuschlagen. Volljährige Kinder "
                  "erklären das selbst. Für minderjährige handeln die Eltern; bei einem "
                  "Interessenkonflikt entscheidet die Kindesschutzbehörde (KESB).",
            "en": "If you disclaim, your share as a rule passes on to your own children, as "
                  "if you had died before the deceased. If they are not to inherit either, "
                  "a disclaimer is needed for them too. Adult children declare it "
                  "themselves. For minors the parents act; where there is a conflict of "
                  "interest the child protection authority (KESB) decides."},
        "sources": (("zgb", "572", "Art. 572 Abs. 1 ZGB"), ("zgb", "306", "Art. 306 ZGB")),
        "terms": (),
    },
    "gifts": {
        "title": {"de": "Geschenke und Vorbezüge der letzten fünf Jahre",
                  "en": "Gifts and advances of the last five years"},
        "text": {
            "de": "War die verstorbene Person zahlungsunfähig, haften Erben trotz "
                  "Ausschlagung gegenüber deren Gläubigern, soweit sie in den letzten fünf "
                  "Jahren vor dem Tod Vermögenswerte erhalten haben, die bei der Erbteilung "
                  "auszugleichen wären. Die übliche Ausstattung bei der Heirat und die Kosten "
                  "von Erziehung und Ausbildung sind ausgenommen.",
            "en": "If the deceased was insolvent, heirs are liable to the deceased's "
                  "creditors despite the disclaimer, to the extent that they received assets "
                  "in the last five years before the death that would have to be brought "
                  "into account in the division of the estate. The customary outfitting on "
                  "marriage and the costs of upbringing and education are excepted."},
        "sources": (("zgb", "579", "Art. 579 ZGB"),),
        "terms": (),
    },
    "own_debts": {
        "title": {"de": "Wenn Sie selbst Schulden haben", "en": "If you have debts yourself"},
        "text": {
            "de": "Schlägt ein überschuldeter Erbe aus, damit die Erbschaft seinen eigenen "
                  "Gläubigern entzogen bleibt, können diese die Ausschlagung innert sechs "
                  "Monaten anfechten.",
            "en": "If an over-indebted heir disclaims so that the inheritance stays out of "
                  "reach of the heir's own creditors, they can challenge the disclaimer "
                  "within six months."},
        "sources": (("zgb", "578", "Art. 578 ZGB"),),
        "terms": (),
    },
    "benefits": {
        "title": {"de": "Wenn Sie Ergänzungsleistungen oder Sozialhilfe beziehen",
                  "en": "If you receive supplementary benefits or social assistance"},
        "text": {
            "de": "Wer ohne Rechtspflicht auf Vermögen verzichtet, dem wird es bei den "
                  "Ergänzungsleistungen angerechnet, als hätte er nicht verzichtet. Die "
                  "Ausschlagung einer Erbschaft mit Vermögen kann deshalb zu einer Kürzung "
                  "führen. Für die Sozialhilfe gelten kantonale Regeln.",
            "en": "For a person who gives up assets without a legal duty, they are counted "
                  "for supplementary benefits as if they had not been given up. Disclaiming "
                  "an inheritance with assets can therefore lead to a reduction. Social "
                  "assistance is governed by cantonal rules."},
        "sources": (("elg", "11a", "Art. 11a ELG"),),
        "terms": (),
    },
}


def _inventory_open(decision: Decision | None) -> bool:
    """True while the one-month period for a public inventory has not passed."""
    days = [d.working_days_left for d in (decision.deadlines if decision else [])
            if d.key == "inventory"]
    return bool(days) and min(days) >= 0


def _keys(case: Case, decision: Decision | None) -> tuple[str, list[str], list[str]]:
    """(key of the summary sentence, keys of the findings, keys of the notes)."""
    state = disclaimer_state(case)
    if state == "unknown":
        return "", [], []
    findings: list[str] = []
    presumed = False
    if state == "open":
        findings.append("period_" + case.value("heir_basis"))
    else:
        insolvency = case.facts.get("estate_insolvency")
        if insolvency is None or insolvency.status is Status.MISSING:
            pass                                      # gate 1B not answered yet
        elif insolvency.value == "manifest":
            presumed = True
            findings.append("presumed")
        else:                                         # "no", or "I do not know"
            findings.append("period_passed")

    actions = case.facts.get("estate_actions")
    if actions is not None and actions.status is not Status.MISSING:
        value = established(case, "estate_actions")
        if value in ("none", "administration"):
            findings.append("actions_safe")
        elif value is not None or actions.status is not Status.KNOWN:
            findings.append("actions_took")           # took, unsure, or "I do not know"

    finances = case.facts.get("estate_finances")
    known = finances is not None and finances.status is not Status.MISSING
    kind = finances.value if known and finances.status is Status.KNOWN else "uncertain"
    if state == "open" and known:
        if kind == "uncertain":
            findings.append("finances_uncertain_inventory" if _inventory_open(decision)
                            else "finances_uncertain_late")
        else:
            findings.append("finances_" + kind)

    # Gate 4. Children: whenever disclaiming is on the table. Gifts: where the estate
    # may be insolvent. Own debts and benefits: where the estate may hold assets.
    notes: list[str] = []
    if presumed or state == "passed" or (known and kind != "solvent"):
        notes += ["children", "gifts"]
    if state == "open" and known and kind in ("solvent", "uncertain"):
        notes += ([] if "children" in notes else ["children"]) + ["own_debts", "benefits"]
    return state, findings, notes


def _item(entry: dict, lang: str, key: str) -> dict:
    out = {"key": key, "title": entry["title"][lang], "text": entry["text"][lang],
           "citations": [{"citation": knowledge.citation_text(c, lang),
                          "url": knowledge.fedlex_url(law, art, lang)}
                         for law, art, c in entry["sources"]],
           "terms": knowledge.terms(entry["terms"], lang)}
    if "verdict" in entry:
        out["verdict"] = entry["verdict"]
        out["verdict_label"] = VERDICTS[entry["verdict"]][lang]
    return out


def assess(case: Case, decision: Decision | None = None, lang: str | None = None) -> dict | None:
    """The result for an inheritance case, from fixed texts, in the same shape as the
    late-fee result. None if the case is not an inheritance case or the start of the
    period is not established yet."""
    if "inheritance_debt" not in case.areas:
        return None
    lang = lang or case.language
    state, findings, notes = _keys(case, decision)
    if not findings:
        return None
    positions = [_item(FINDINGS[k], lang, k) for k in findings]
    for p in positions:
        # "I am not sure whether it counts" is put as a question of the individual case.
        if p["key"] == "actions_took" and established(case, "estate_actions") != "took":
            p["verdict"], p["verdict_label"] = "case_by_case", VERDICTS["case_by_case"][lang]
    return {"title": T["title"][lang], "basis": T["basis"][lang], "summary": T[state][lang],
            "positions": positions, "notes_title": T["notes_title"][lang],
            "notes": [_item(NOTES[k], lang, k) for k in notes],
            "source_label": T["source"][lang], "terms_label": T["terms"][lang]}
