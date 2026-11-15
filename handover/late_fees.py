"""Late fees: what the answers to the three gates mean. Plain Python, no model call.

The legal lead's framework (full_report.md section 3.4a) examines a letter that claims
additional charges for late payment in three steps:

  gate 1  who sent the letter               (fact document_type)
  gate 2  is the person in default at all   (facts principal_status, default_trigger)
  gate 3  each charge on its own            (facts interest_charge, reminder_fee,
                                             collection_costs)

The questions are defined in areas.py. This file turns the answers into the result
shown after PROCEED: one fixed text per outcome, with the article it rests on and
the terms it uses. The model writes none of it. An answer "I do not know" at gate 3
gives a conditional text that names what to check; it is never treated as a yes or a
no. A payment order gets the urgent notice (rules.py, guidance.py) and is then examined
at gates 2 and 3 like a private letter, with notes on the objection. Other letters
from the debt enforcement office and letters from a court never reach this file: the
gate refers them.

DRAFTS: the texts follow the framework and glossary supplied by the legal lead on
2026-11-13 and are to be reviewed by the legal lead.
"""
from __future__ import annotations

from . import knowledge
from .areas import established
from .schema import Case, Status

# ---- where a case stands in the framework ---------------------------------------

ENFORCEMENT, COURT, PUBLIC = "enforcement_office", "court", "public_claim"
PAID_ON_TIME, NOT_DUE, DISPUTED = "paid_on_time", "not_due", "principal_disputed"
NO_DEFAULT, IN_DEFAULT = "no_default", "in_default"


def branch(case: Case) -> str | None:
    """The outcome of gates 1 and 2, or None while an answer is still missing."""
    doc = established(case, "document_type")      # an unconfirmed official sender: not yet
    if doc == "seizure_notice":
        return ENFORCEMENT
    if doc == "court_document":
        return COURT
    if doc == "public_claim":
        return PUBLIC
    if doc not in ("reminder", "payment_order"):
        return None
    principal = case.value("principal_status")
    if principal == "paid_on_time":
        return PAID_ON_TIME
    if principal == "not_due":
        return NOT_DUE
    if principal == "disputed":
        return DISPUTED
    if principal not in ("open", "paid_late"):
        return None
    trigger = case.value("default_trigger")
    if trigger == "none":
        return NO_DEFAULT
    if trigger in ("reminder", "fixed_date"):
        return IN_DEFAULT
    return None


# ---- fixed texts ------------------------------------------------------------------

VERDICTS = {
    "owed": {"de": "Geschuldet", "en": "Owed"},
    "owed_if_agreed": {"de": "Geschuldet, wenn gültig vereinbart", "en": "Owed if validly agreed"},
    "owed_if_proven": {"de": "Geschuldet, soweit nachgewiesen", "en": "Owed to the proven extent"},
    "reduced": {"de": "Nur 5 % pro Jahr geschuldet", "en": "Owed only at 5 % per year"},
    "not_owed": {"de": "Nicht geschuldet", "en": "Not owed"},
    "depends": {"de": "Hängt vom Vertrag ab", "en": "Depends on the contract"},
    "depends_proof": {"de": "Hängt vom Nachweis ab", "en": "Depends on the proof"},
    "dispute": {"de": "Schriftlich bestreiten", "en": "Dispute in writing"},
    "special": {"de": "Besondere Regeln", "en": "Special rules"},
}

T = {
    "title": {"de": "Was für Ihre Zusatzkosten gilt", "en": "What applies to your additional charges"},
    "basis": {
        "de": "Diese Einordnung folgt festen Regeln und stützt sich nur auf Ihre Antworten. "
              "Sie ist eine allgemeine Information, keine Rechtsberatung im Einzelfall.",
        "en": "This classification follows fixed rules and rests only on your answers. It is "
              "general information, not legal advice on your individual case."},
    "in_default": {
        "de": "Nach Ihren Angaben sind Sie mit der ursprünglichen Rechnung im Verzug. Jede "
              "Zusatzposition ist für sich zu prüfen.",
        "en": "According to your answers you are in default with the original bill. Each "
              "additional charge has to be examined on its own."},
    "in_default_paid": {
        "de": "Nach Ihren Angaben waren Sie mit der ursprünglichen Rechnung im Verzug, bis "
              "Sie bezahlt haben. Jede Zusatzposition ist für sich zu prüfen.",
        "en": "According to your answers you were in default with the original bill until "
              "you paid. Each additional charge has to be examined on its own."},
    "nothing_claimed": {
        "de": "Nach Ihren Angaben werden weder Zins noch Gebühren verlangt. Dann gibt es "
              "keine Zusatzposition zu prüfen.",
        "en": "According to your answers neither interest nor fees are claimed. There is "
              "then no additional charge to examine."},
    "notes_title": {"de": "Gut zu wissen", "en": "Good to know"},
    "source": {"de": "Quelle", "en": "Source"},
    "terms": {"de": "Begriffe", "en": "Terms"},
}

# One entry per outcome: title, verdict, text, the articles it rests on and the terms
# it uses. "sources" are (statute, article, citation) as in knowledge.py.
FINDINGS: dict[str, dict] = {
    # ---- gate 1 ------------------------------------------------------------------
    "public": {
        "title": {"de": "Forderung einer Behörde oder der obligatorischen Krankenversicherung",
                  "en": "Claim by an authority or the mandatory health insurer"},
        "verdict": "special",
        "text": {
            "de": "Für Steuern, Gebühren wie Serafe und die Prämien der obligatorischen "
                  "Krankenversicherung gilt nicht das Obligationenrecht, sondern es gelten "
                  "besondere Gesetze und Verordnungen. Mahngebühren und Verzugszinsen sind "
                  "dort oft ausdrücklich vorgesehen und dann geschuldet. Die Prüfung, die "
                  "ich für private Rechnungen anbiete, passt deshalb nicht auf Ihr "
                  "Schreiben. Steht auf dem Schreiben, wie und bis wann Sie sich dagegen "
                  "wehren können (Rechtsmittelbelehrung), gilt diese Frist.",
            "en": "Taxes, fees such as Serafe and the premiums of mandatory health insurance "
                  "are not governed by the Code of Obligations but by special statutes and "
                  "ordinances. Reminder fees and default interest are often expressly "
                  "provided for there and are then owed. The examination I offer for private "
                  "bills therefore does not fit your letter. If the letter states how and by "
                  "when you can challenge it (Rechtsmittelbelehrung), that period applies."},
        "sources": (("kvg", "64a", "Art. 64a KVG"),),
        "terms": ("term_forderungsart",),
    },
    # ---- gate 2: no default ----------------------------------------------------------
    "paid_on_time": {
        "title": {"de": "Rechtzeitig bezahlte Rechnung", "en": "Bill paid on time"},
        "verdict": "not_owed",
        "text": {
            "de": "Wer rechtzeitig bezahlt hat, war nie im Verzug. Dann sind weder Verzugszins "
                  "noch Mahngebühren oder Inkassokosten geschuldet. Sie können die "
                  "Zusatzkosten schriftlich bestreiten und den Zahlungsbeleg beilegen. "
                  "Massgebend ist, wann die Zahlung verbucht wurde, nicht wann Sie den "
                  "Auftrag erfasst haben.",
            "en": "A person who paid on time was never in default. Then neither default "
                  "interest nor reminder fees or collection costs are owed. You can dispute "
                  "the additional charges in writing and enclose the proof of payment. What "
                  "counts is when the payment was booked, not when you entered the order."},
        "sources": (("or", "102", "Art. 102 OR"), ("or", "104", "Art. 104 OR")),
        "terms": ("term_faelligkeit_verzug", "term_zustellung"),
    },
    "not_due": {
        "title": {"de": "Rechnung noch nicht fällig", "en": "Bill not yet due"},
        "verdict": "not_owed",
        "text": {
            "de": "Solange die Zahlungsfrist läuft, sind Sie nicht im Verzug. Zusatzkosten "
                  "wegen verspäteter Zahlung sind dann nicht geschuldet. Sie können sie "
                  "schriftlich bestreiten.",
            "en": "As long as the payment period is running, you are not in default. "
                  "Additional charges for late payment are then not owed. You can dispute "
                  "them in writing."},
        "sources": (("or", "75", "Art. 75 OR"), ("or", "102", "Art. 102 OR")),
        "terms": ("term_faelligkeit_verzug",),
    },
    "principal_disputed": {
        "title": {"de": "Bestrittene Rechnung", "en": "Disputed bill"},
        "verdict": "dispute",
        "text": {
            "de": "Zusatzkosten setzen voraus, dass die ursprüngliche Rechnung geschuldet "
                  "ist. Soweit Sie den Betrag nicht schulden, schulden Sie darauf auch keinen "
                  "Verzugszins und keine Mahn- oder Inkassokosten. Sie können die gesamte "
                  "Forderung schriftlich bestreiten und kurz angeben, weshalb. Ob die "
                  "Rechnung selbst berechtigt ist, kann ich nicht beurteilen.",
            "en": "Additional charges require that the original bill is owed. To the extent "
                  "that you do not owe the amount, you owe neither default interest nor "
                  "reminder or collection costs on it. You can dispute the whole claim in "
                  "writing and briefly state why. Whether the bill itself is justified is "
                  "something I cannot assess."},
        "sources": (("or", "102", "Art. 102 OR"), ("or", "104", "Art. 104 OR")),
        "terms": ("term_hauptforderung",),
    },
    "no_default": {
        "title": {"de": "Noch kein Verzug", "en": "Not yet in default"},
        "verdict": "not_owed",
        "text": {
            "de": "Nach Ihren Angaben gab es vor den Zusatzkosten weder eine Mahnung noch "
                  "einen im Vertrag vereinbarten Zahlungstermin. Dann waren Sie zu diesem "
                  "Zeitpunkt nicht im Verzug, und für diese Zeit sind weder Verzugszins noch "
                  "Mahn- oder Inkassokosten geschuldet.",
            "en": "According to your answers there was neither a reminder nor a payment date "
                  "agreed in the contract before the additional charges. You were then not "
                  "in default at that time, and for that time neither default interest nor "
                  "reminder or collection costs are owed."},
        "sources": (("or", "102", "Art. 102 OR"),),
        "terms": ("term_faelligkeit_verzug", "term_mahnung", "term_verfalltag"),
    },
    # ---- gate 3, position A: default interest ---------------------------------------------
    "interest_statutory": {
        "title": {"de": "Verzugszins", "en": "Default interest"},
        "verdict": "owed",
        "text": {
            "de": "Im Verzug ist ein Verzugszins von 5 % pro Jahr von Gesetzes wegen "
                  "geschuldet. Er läuft erst ab dem Tag, an dem der Verzug begonnen hat, "
                  "nicht ab dem Rechnungsdatum, und nur auf der ursprünglichen Rechnung, "
                  "nicht auf Zinsen oder Gebühren. «Pro Jahr» heisst anteilig: Bei CHF 400 "
                  "und 20 Tagen Verzug sind das rund CHF 1.10.",
            "en": "In default, default interest of 5 % per year is owed by law. It runs only "
                  "from the day default began, not from the date of the bill, and only on "
                  "the original bill, not on interest or fees. 'Per year' means "
                  "proportionally: on CHF 400 and 20 days of default this is about CHF 1.10."},
        "sources": (("or", "104", "Art. 104 OR"), ("or", "105", "Art. 105 Abs. 3 OR")),
        "terms": ("term_verzugszins", "term_zinseszins"),
    },
    "interest_higher_agreed": {
        "title": {"de": "Verzugszins über 5 %", "en": "Default interest above 5 %"},
        "verdict": "owed_if_agreed",
        "text": {
            "de": "Ein höherer Zins als 5 % pro Jahr ist geschuldet, wenn er im Vertrag oder "
                  "in den AGB gültig vereinbart wurde. Sehr hohe Zinssätze können unzulässig "
                  "sein; als Richtwert gelten bei Konsument:innen rund 15 % pro Jahr. Auch "
                  "der vereinbarte Zins läuft erst ab Verzugsbeginn und nur auf der "
                  "ursprünglichen Rechnung.",
            "en": "A rate above 5 % per year is owed if it was validly agreed in the "
                  "contract or the general terms. Very high rates can be inadmissible; for "
                  "consumers about 15 % per year serves as a guide. The agreed interest, "
                  "too, runs only from the start of default and only on the original bill."},
        "sources": (("or", "104", "Art. 104 Abs. 2 OR"), ("or", "105", "Art. 105 Abs. 3 OR")),
        "terms": ("term_verzugszins", "term_agb", "term_zinseszins"),
    },
    "interest_higher_not_agreed": {
        "title": {"de": "Verzugszins über 5 %", "en": "Default interest above 5 %"},
        "verdict": "reduced",
        "text": {
            "de": "Ohne Vereinbarung im Vertrag oder in den AGB ist nur der gesetzliche "
                  "Verzugszins von 5 % pro Jahr geschuldet, anteilig ab Verzugsbeginn. Der "
                  "Teil, der darüber hinausgeht, ist nicht geschuldet.",
            "en": "Without an agreement in the contract or the general terms, only the "
                  "statutory default interest of 5 % per year is owed, proportionally from "
                  "the start of default. The part above that is not owed."},
        "sources": (("or", "104", "Art. 104 OR"),),
        "terms": ("term_verzugszins", "term_agb"),
    },
    "interest_unclear": {
        "title": {"de": "Verzugszins", "en": "Default interest"},
        "verdict": "depends",
        "text": {
            "de": "Von Gesetzes wegen geschuldet ist ein Verzugszins von 5 % pro Jahr, "
                  "anteilig ab Verzugsbeginn und nur auf der ursprünglichen Rechnung. Mehr "
                  "ist nur geschuldet, wenn ein höherer Zins im Vertrag oder in den AGB "
                  "vereinbart wurde. Sie können vom Gläubiger verlangen, dass er Zinssatz, "
                  "Zeitraum und Berechnung offenlegt.",
            "en": "By law, default interest of 5 % per year is owed, proportionally from the "
                  "start of default and only on the original bill. More is owed only if a "
                  "higher rate was agreed in the contract or the general terms. You can ask "
                  "the creditor to disclose the rate, the period and the calculation."},
        "sources": (("or", "104", "Art. 104 OR"), ("or", "105", "Art. 105 Abs. 3 OR")),
        "terms": ("term_verzugszins", "term_zinseszins", "term_agb"),
    },
    # ---- gate 3, position B: reminder fees ------------------------------------------------
    "fee_agreed_amount": {
        "title": {"de": "Mahngebühren", "en": "Reminder fees"},
        "verdict": "owed",
        "text": {
            "de": "Eine Mahngebühr ist geschuldet, wenn Sie ihr beim Vertragsabschluss "
                  "zugestimmt haben und der Vertrag oder die AGB einen konkreten Betrag "
                  "nennen. Das trifft nach Ihren Angaben zu. Eine Ausnahme gilt für "
                  "übersetzte oder missbräuchliche Beträge.",
            "en": "A reminder fee is owed if you agreed to it when concluding the contract "
                  "and the contract or the general terms state a concrete amount. According "
                  "to your answers this is the case. An exception applies to excessive or "
                  "unfair amounts."},
        "sources": (("or", "1", "Art. 1 OR"), ("uwg", "8", "Art. 8 UWG")),
        "terms": ("term_agb", "term_ungewoehnlich"),
    },
    "fee_agreed_vague": {
        "title": {"de": "Mahngebühren", "en": "Reminder fees"},
        "verdict": "not_owed",
        "text": {
            "de": "Eine Klausel, die nur allgemein von Mahnkosten spricht und keinen Betrag "
                  "nennt, genügt nicht. Die Mahngebühr ist dann nicht geschuldet.",
            "en": "A clause that speaks only in general of reminder costs and states no "
                  "amount is not enough. The reminder fee is then not owed."},
        "sources": (("or", "1", "Art. 1 OR"),),
        "terms": ("term_bestimmtheit", "term_agb"),
    },
    "fee_not_agreed": {
        "title": {"de": "Mahngebühren", "en": "Reminder fees"},
        "verdict": "not_owed",
        "text": {
            "de": "Mahngebühren stehen nicht im Gesetz; sie müssen vereinbart sein. Eine "
                  "Gebühr, die zum ersten Mal auf der Rechnung oder Mahnung steht, ist eine "
                  "einseitige Behauptung des Gläubigers. Ohne Vereinbarung beim "
                  "Vertragsabschluss ist sie nicht geschuldet.",
            "en": "Reminder fees are not in the statute; they must be agreed. A fee that "
                  "appears for the first time on the bill or reminder is a one-sided "
                  "assertion by the creditor. Without an agreement at the conclusion of the "
                  "contract it is not owed."},
        "sources": (("or", "1", "Art. 1 OR"),),
        "terms": ("term_agb",),
    },
    "fee_unsure": {
        "title": {"de": "Mahngebühren", "en": "Reminder fees"},
        "verdict": "depends",
        "text": {
            "de": "Mahngebühren sind nur geschuldet, wenn Sie ihnen beim Vertragsabschluss "
                  "zugestimmt haben und der Vertrag oder die AGB einen konkreten Betrag "
                  "nennen. Eine Gebühr, die erst auf der Rechnung oder Mahnung auftaucht, "
                  "oder eine Klausel ohne Betrag genügt nicht. Sie können im Vertrag "
                  "nachsehen oder vom Gläubiger verlangen, dass er die Klausel vorlegt.",
            "en": "Reminder fees are owed only if you agreed to them when concluding the "
                  "contract and the contract or the general terms state a concrete amount. A "
                  "fee that first appears on the bill or reminder, or a clause without an "
                  "amount, is not enough. You can check the contract or ask the creditor to "
                  "produce the clause."},
        "sources": (("or", "1", "Art. 1 OR"), ("uwg", "8", "Art. 8 UWG")),
        "terms": ("term_agb", "term_bestimmtheit", "term_ungewoehnlich"),
    },
    # ---- gate 3, position C: collection costs ---------------------------------------------
    "costs_flat": {
        "title": {"de": "Weitere Kosten für das Eintreiben", "en": "Further collection costs"},
        "verdict": "not_owed",
        "text": {
            "de": "Pauschale Inkassokosten, «Dossiergebühren» oder Kosten für die "
                  "Adressnachforschung sind nicht geschuldet. Art. 106 OR legt keine "
                  "Pauschale fest; der übliche Aufwand für das Eintreiben ist mit dem "
                  "Verzugszins abgegolten. Ein Inkassobüro beizuziehen ist der Entscheid des "
                  "Gläubigers.",
            "en": "Flat collection costs, 'dossier fees' or costs of an address search are "
                  "not owed. Art. 106 OR does not set a flat amount; the routine effort of "
                  "collecting is covered by the default interest. Hiring a collection agency "
                  "is the creditor's own choice."},
        "sources": (("or", "106", "Art. 106 OR"), ("schkg", "27", "Art. 27 Abs. 2 SchKG")),
        "terms": ("term_verzugsschaden", "term_beweislast"),
    },
    "costs_proven": {
        "title": {"de": "Weitere Kosten für das Eintreiben", "en": "Further collection costs"},
        "verdict": "owed_if_proven",
        "text": {
            "de": "Weist der Gläubiger einen konkreten, aussergewöhnlichen Schaden nach, der "
                  "höher ist als der Verzugszins, ist dieser Schaden im nachgewiesenen "
                  "Umfang geschuldet.",
            "en": "If the creditor proves a concrete, extraordinary loss that is higher than "
                  "the default interest, that loss is owed to the proven extent."},
        "sources": (("or", "106", "Art. 106 OR"), ("zgb", "8", "Art. 8 ZGB")),
        "terms": ("term_verzugsschaden", "term_beweislast"),
    },
    "costs_unsure": {
        "title": {"de": "Weitere Kosten für das Eintreiben", "en": "Further collection costs"},
        "verdict": "depends_proof",
        "text": {
            "de": "Solche Kosten sind nur geschuldet, wenn der Gläubiger einen konkreten, "
                  "aussergewöhnlichen Schaden nachweist, der höher ist als der Verzugszins. "
                  "Pauschalen ohne Belege sind nicht geschuldet. Den Nachweis muss der "
                  "Gläubiger erbringen; Sie können die Belege verlangen.",
            "en": "Such costs are owed only if the creditor proves a concrete, extraordinary "
                  "loss that is higher than the default interest. Flat amounts without "
                  "documents are not owed. The proof is for the creditor to provide; you can "
                  "ask for the documents."},
        "sources": (("or", "106", "Art. 106 OR"), ("zgb", "8", "Art. 8 ZGB")),
        "terms": ("term_verzugsschaden", "term_beweislast"),
    },
}

# General notes shown under the result. "when" names the situations they fit.
NOTES: dict[str, dict] = {
    "this_letter_reminds": {
        "title": {"de": "Dieses Schreiben kann als Mahnung gelten",
                  "en": "This letter can count as a reminder"},
        "text": {
            "de": "Das Schreiben, das Sie jetzt erhalten haben, kann selbst eine Mahnung "
                  "sein. Ab seinem Eingang kann auf der offenen Rechnung ein Verzugszins von "
                  "5 % pro Jahr laufen.",
            "en": "The letter you have now received can itself be a reminder. From its "
                  "receipt, default interest of 5 % per year can run on the unpaid bill."},
        "sources": (("or", "102", "Art. 102 Abs. 1 OR"), ("or", "104", "Art. 104 OR")),
        "terms": ("term_mahnung", "term_zustellung"),
    },
    "dispute_in_writing": {
        "title": {"de": "Nicht geschuldete Positionen", "en": "Charges that are not owed"},
        "text": {
            "de": "Positionen, die nicht geschuldet sind, können Sie gegenüber dem Gläubiger "
                  "oder dem Inkassobüro schriftlich bestreiten. Geschuldet bleiben die "
                  "ursprüngliche Rechnung und der berechtigte Verzugszins.",
            "en": "Charges that are not owed can be disputed in writing with the creditor or "
                  "the collection agency. The original bill and the justified default "
                  "interest remain owed."},
        "sources": (),
        "terms": ("term_hauptforderung",),
    },
    "partial_payment": {
        "title": {"de": "Beim Bezahlen", "en": "When paying"},
        "text": {
            "de": "Der Gläubiger darf eine Teilzahlung zuerst auf geschuldete Zinsen und "
                  "Kosten anrechnen. Es hilft, die ursprüngliche Rechnung zusammen mit dem "
                  "berechtigten Zins zu zahlen und im Zahlungszweck anzugeben, wofür die "
                  "Zahlung ist.",
            "en": "The creditor may credit a partial payment to owed interest and costs "
                  "first. It helps to pay the original bill together with the justified "
                  "interest and to state in the payment reference what the payment is for."},
        "sources": (("or", "85", "Art. 85 OR"),),
        "terms": ("term_tilgung",),
    },
    "instalment_agreement": {
        "title": {"de": "Vor einer Ratenvereinbarung", "en": "Before an instalment agreement"},
        "text": {
            "de": "Wer eine Ratenvereinbarung unterschreibt, anerkennt in der Regel den "
                  "ganzen aufgeführten Betrag, auch darin enthaltene Gebühren, die sonst "
                  "nicht geschuldet wären.",
            "en": "A person who signs an instalment agreement as a rule acknowledges the "
                  "whole amount listed, including fees that would otherwise not be owed."},
        "sources": (("schkg", "82", "Art. 82 SchKG"),),
        "terms": ("term_schuldanerkennung",),
    },
    "objection": {
        "title": {"de": "Was Sie bestreiten: Rechtsvorschlag beim Betreibungsamt",
                  "en": "What you dispute: objection with the debt enforcement office"},
        "text": {
            "de": "Bei einem Zahlungsbefehl genügt es nicht, dem Gläubiger zu schreiben. Was "
                  "Sie bestreiten, erklären Sie innert 10 Tagen seit der Zustellung dem "
                  "Betreibungsamt mit Rechtsvorschlag. Bestreiten Sie nur einzelne "
                  "Positionen, nennen Sie den bestrittenen Betrag in Franken genau "
                  "(Teil-Rechtsvorschlag); sonst gilt die ganze Forderung als bestritten.",
            "en": "With a payment order it is not enough to write to the creditor. What you "
                  "dispute is declared to the debt enforcement office by objection within "
                  "10 days of service. If you dispute only single charges, state the "
                  "disputed amount in francs exactly (partial objection); otherwise the "
                  "whole claim counts as disputed."},
        "sources": (("schkg", "74", "Art. 74 SchKG"),),
        "terms": ("term_rechtsvorschlag", "term_teilrechtsvorschlag"),
    },
    "official_costs": {
        "title": {"de": "Amtliche Kosten der Betreibung", "en": "Official costs of the enforcement"},
        "text": {
            "de": "Die amtlichen Kosten der Betreibung, zum Beispiel für den Zahlungsbefehl, "
                  "trägt der Schuldner, wenn die betriebene Forderung bestand und nicht "
                  "bezahlt war. Sie sind etwas anderes als die Gebühren eines Inkassobüros.",
            "en": "The official costs of the enforcement, for example for the payment order, "
                  "are borne by the debtor if the claim under enforcement existed and was "
                  "unpaid. They are something different from the fees of a collection "
                  "agency."},
        "sources": (("schkg", "68", "Art. 68 SchKG"),),
        "terms": ("term_betreibungskosten",),
    },
    "later_payment_order": {
        "title": {"de": "Falls später ein Zahlungsbefehl kommt",
                  "en": "If a payment order arrives later"},
        "text": {
            "de": "Erhalten Sie später einen Zahlungsbefehl vom Betreibungsamt, läuft eine "
                  "Frist von 10 Tagen für den Rechtsvorschlag. Wer nur einzelne Positionen "
                  "bestreitet, kann Teil-Rechtsvorschlag erheben und den bestrittenen Betrag "
                  "genau angeben.",
            "en": "If you later receive a payment order from the debt enforcement office, a "
                  "period of 10 days for the objection runs. A person who disputes only "
                  "single charges can raise a partial objection and state the disputed "
                  "amount exactly."},
        "sources": (("schkg", "74", "Art. 74 SchKG"),),
        "terms": ("term_zahlungsbefehl", "term_teilrechtsvorschlag"),
    },
}

# Answer at gate 3 -> finding. None: the charge is not claimed, nothing is said.
_INTEREST = {"none": None, "claimed": "interest_unclear", "statutory": "interest_statutory",
             "higher_agreed": "interest_higher_agreed",
             "higher_not_agreed": "interest_higher_not_agreed", "unclear": "interest_unclear"}
_FEE = {"none": None, "claimed": "fee_unsure", "agreed_amount": "fee_agreed_amount",
        "agreed_vague": "fee_agreed_vague",
        "not_agreed": "fee_not_agreed", "unsure": "fee_unsure"}
_COSTS = {"none": None, "claimed": "costs_unsure", "flat": "costs_flat",
          "proven": "costs_proven", "unsure": "costs_unsure"}
_POSITIONS = (("interest_charge", _INTEREST, "interest_unclear"),
              ("reminder_fee", _FEE, "fee_unsure"),
              ("collection_costs", _COSTS, "costs_unsure"))
_NOT_OWED = {"not_owed", "reduced", "dispute"}


def _finding_keys(case: Case) -> tuple[str | None, list[str]]:
    """(key of the summary sentence, keys of the findings) for a case, by fixed rules."""
    where = branch(case)
    if where == PUBLIC:
        return None, ["public"]
    if where in (PAID_ON_TIME, NOT_DUE, DISPUTED, NO_DEFAULT):
        return None, [where]
    if where != IN_DEFAULT:
        return None, []
    keys = []
    for name, table, unknown in _POSITIONS:
        f = case.facts.get(name)
        if f is None or f.status is Status.MISSING:
            continue                      # not answered yet: say nothing about it
        # "I do not know" or not clarified: the conditional text, never a yes or a no.
        key = table.get(f.value, unknown) if f.status is Status.KNOWN else unknown
        if key:
            keys.append(key)
    paid = case.value("principal_status") == "paid_late"
    return ("in_default_paid" if paid else "in_default"), keys


def _note_keys(case: Case, keys: list[str]) -> list[str]:
    where = branch(case)
    unpaid = case.value("principal_status") == "open"
    verdicts = {FINDINGS[k]["verdict"] for k in keys}
    if established(case, "document_type") == "payment_order" and where != PUBLIC:
        # The enforcement is running: what is disputed goes to the office, in time.
        return ["objection", "official_costs"] + (["instalment_agreement"] if unpaid else [])
    notes = []
    if where == NO_DEFAULT and unpaid:
        notes.append("this_letter_reminds")
    if where == IN_DEFAULT and verdicts & _NOT_OWED:
        notes.append("dispute_in_writing")
    if where in (IN_DEFAULT, NO_DEFAULT) and unpaid:
        notes += ["partial_payment", "instalment_agreement"]
    if where in (IN_DEFAULT, NO_DEFAULT, PAID_ON_TIME, NOT_DUE, DISPUTED):
        notes.append("later_payment_order")
    return notes


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


def assess(case: Case, lang: str | None = None) -> dict | None:
    """The result for a late-fee case, from fixed texts. None if the case is not a
    late-fee case or the framework gives no result for it (missing answers, letters
    from the debt enforcement office or a court)."""
    if "debt_collection" not in case.areas:
        return None
    lang = lang or case.language
    summary_key, keys = _finding_keys(case)
    if not keys and summary_key is None:
        return None
    if summary_key and not keys:
        summary = T["nothing_claimed"][lang]
    else:
        summary = T[summary_key][lang] if summary_key else ""
    return {"title": T["title"][lang], "basis": T["basis"][lang], "summary": summary,
            "positions": [_item(FINDINGS[k], lang, k) for k in keys],
            "notes_title": T["notes_title"][lang],
            "notes": [_item(NOTES[k], lang, k) for k in _note_keys(case, keys)],
            "source_label": T["source"][lang], "terms_label": T["terms"][lang]}


def render(a: dict) -> str:
    """The result as plain text, for the command line and the conversation record."""
    out = [f"**{a['title']}**"]
    if a["summary"]:
        out.append(a["summary"])
    for p in a["positions"]:
        cites = ", ".join(f"{c['citation']}: {c['url']}" for c in p["citations"])
        out.append(f"- {p['title']}: {p['verdict_label']}. {p['text']}"
                   + (f" ({cites})" if cites else ""))
    if a["notes"]:
        out.append(f"\n**{a['notes_title']}**")
        for n in a["notes"]:
            cites = ", ".join(f"{c['citation']}: {c['url']}" for c in n["citations"])
            out.append(f"- {n['title']}: {n['text']}" + (f" ({cites})" if cites else ""))
    out.append("\n" + a["basis"])
    return "\n".join(out)
