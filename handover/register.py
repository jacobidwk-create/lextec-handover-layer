"""Entry in the debt enforcement register: what the answers to the gates mean.
Plain Python, no model.

The legal lead's flow of 2026-11-14 (full_report.md section 3.4c) examines the situation of a
person who is refused a flat, a job or a loan because of an entry on the register
extract (Betreibungsauszug):

  gate 1   what kind of entry it is and how old           (register_entry)
  gate 2   was the claim paid, and when                   (register_payment)
           track A, not paid: was an objection raised     (register_objection), has the
           waiting time passed (register_service_date), what did the creditor do
           (register_creditor_step), why was no objection raised (register_missed_reason)
           track B, paid: before or after the payment order was served

The questions are defined in areas.py and the route is decided in rules.py. This file
turns the answers into the result shown after PROCEED, built like the results for late
fees (late_fees.py) and for declining an inheritance (inheritance.py): one fixed text
per outcome, with the article or the decision it rests on and the terms it uses. The
model writes none of it. The one date in these texts, the first day on which a request
can be filed, is computed by code (areas.register_request_from).

DRAFTS: the texts follow the flow supplied by the legal lead and are to be reviewed.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from . import knowledge
from .areas import register_objection_open, register_request_from, register_wait
from .schema import Case, Decision, Status

CASE_LAW = Path(__file__).resolve().parent.parent / "sources" / "case_law.json"

VERDICTS = {
    "hidden": {"de": "Für Dritte nicht mehr sichtbar", "en": "No longer visible to third parties"},
    "delete": {"de": "Löschung nach Tilgung", "en": "Deleted once settled"},
    "request": {"de": "Gesuch möglich", "en": "Request possible"},
    "wait": {"de": "Gesuch noch nicht möglich", "en": "Request not yet possible"},
    "after_wait": {"de": "Gesuch nach drei Monaten", "en": "Request after three months"},
    "no_bar": {"de": "Zahlung steht dem Gesuch nicht entgegen",
               "en": "Payment does not bar the request"},
    "blocked": {"de": "Gesuch ausgeschlossen", "en": "Request excluded"},
    "creditor": {"de": "Nur der Gläubiger kann helfen", "en": "Only the creditor can help"},
    "court_running": {"de": "Gerichtsverfahren läuft", "en": "Court proceedings running"},
    "stays": {"de": "Eintrag bleibt sichtbar", "en": "Entry stays visible"},
    "court": {"de": "Weg über das Gericht", "en": "Through a court"},
    "authority": {"de": "Weg über die Aufsichtsbehörde",
                  "en": "Through the supervisory authority"},
    "act_now": {"de": "Sofort handeln", "en": "Act at once"},
    "check": {"de": "Zuerst klären", "en": "Clarify first"},
    "not_covered": {"de": "Ausserhalb meiner Quellen", "en": "Outside my sources"},
}

T = {
    "title": {"de": "Was für Ihren Registereintrag gilt",
              "en": "What applies to your register entry"},
    "basis": {
        "de": "Diese Einordnung folgt festen Regeln und stützt sich nur auf Ihre Antworten. "
              "Sie ist eine allgemeine Information, keine Rechtsberatung im Einzelfall, und "
              "sie wahrt keine Frist. Ob ein Gesuch Erfolg hat, entscheidet das "
              "Betreibungsamt.",
        "en": "This classification follows fixed rules and rests only on your answers. It is "
              "general information, not legal advice on your individual case, and it does "
              "not preserve any deadline. Whether a request succeeds is decided by the debt "
              "enforcement office."},
    "notes_title": {"de": "Gut zu wissen", "en": "Good to know"},
    "source": {"de": "Quelle", "en": "Source"},
    "terms": {"de": "Begriffe", "en": "Terms"},
}

# The sentence above the result, by what the answers lead to.
SUMMARY = {
    "hidden": {"de": "Nach Ihren Angaben sehen Dritte diesen Eintrag nicht mehr.",
               "en": "According to your answers third parties no longer see this entry."},
    "delete": {"de": "Der Eintrag wird gelöscht, sobald die Forderung aus dem Verlustschein "
                     "getilgt ist.",
               "en": "The entry is deleted once the claim in the loss certificate is settled."},
    "request": {"de": "Nach Ihren Angaben können Sie erreichen, dass Dritte diese Betreibung "
                      "nicht mehr sehen.",
                "en": "According to your answers you can reach that third parties no longer "
                      "see this enforcement."},
    "wait": {"de": "Nach Ihren Angaben ist das Gesuch um Nichtbekanntgabe noch nicht möglich.",
             "en": "According to your answers the request for non-disclosure is not yet "
                   "possible."},
    "blocked": {"de": "Nach Ihren Angaben können Sie die Bekanntgabe nicht selbst verhindern; "
                      "es kommt auf den Gläubiger an.",
                "en": "According to your answers you cannot prevent the disclosure yourself; "
                      "it depends on the creditor."},
    "court": {"de": "Nach Ihren Angaben führt der Weg über ein Gericht oder die "
                    "Aufsichtsbehörde.",
              "en": "According to your answers the way leads through a court or the "
                    "supervisory authority."},
    "act_now": {"de": "Nach Ihren Angaben können Sie den Rechtsvorschlag noch erheben.",
                "en": "According to your answers you can still raise the objection."},
    "check": {"de": "Mit Ihren Angaben lässt sich der Weg noch nicht bestimmen.",
              "en": "With your answers the way cannot be determined yet."},
    "not_covered": {"de": "Dieser Eintrag liegt ausserhalb dessen, was ich prüfen kann.",
                    "en": "This entry is outside what I can check."},
}

# How the request for non-disclosure works; used by several findings.
_PROCEDURE = {
    "de": "Das Amt setzt dem Gläubiger dann eine Frist von 20 Tagen. Weist er nicht nach, "
          "dass er rechtzeitig ein Verfahren zur Beseitigung des Rechtsvorschlags "
          "eingeleitet hat, zeigt das Amt die Betreibung Dritten nicht mehr. Das Gesuch "
          "kostet pauschal 40 Franken, unabhängig vom Ausgang. Erbringt der Gläubiger den "
          "Nachweis später oder wird die Betreibung fortgesetzt, wird sie wieder gezeigt.",
    "en": "The office then gives the creditor a period of 20 days. If the creditor does not "
          "prove that it started proceedings to remove the objection in time, the office "
          "no longer shows the enforcement to third parties. The request costs a flat 40 "
          "francs, whatever the outcome. If the creditor provides the proof later or the "
          "enforcement is continued, it is shown again.",
}
_LIT_D = ("schkg", "8a", "Art. 8a Abs. 3 Bst. d SchKG")
_FEE = ("gebv", "12b", "Art. 12b GebV SchKG")

# A source is (statute, article, citation) or ("decision", id in case_law.json, citation).
FINDINGS: dict[str, dict] = {
    # ---- gate 1: kind and age of the entry -------------------------------------------
    "old": {
        "title": {"de": "Betreibung seit über fünf Jahren abgeschlossen",
                  "en": "Enforcement ended more than five years ago"},
        "verdict": "hidden",
        "text": {
            "de": "Das Einsichtsrecht Dritter erlischt fünf Jahre nach Abschluss des "
                  "Verfahrens. Eine Betreibung, die so lange abgeschlossen ist, erscheint "
                  "auf einem Auszug für Vermieter, Arbeitgeber oder Banken nicht mehr. Dafür "
                  "müssen Sie nichts beantragen. Gerichte und Behörden können weiterhin "
                  "Auszüge verlangen. Erscheint die Betreibung trotzdem noch, fragen Sie "
                  "beim Betreibungsamt nach, an welchem Tag das Verfahren abgeschlossen "
                  "wurde: Die fünf Jahre zählen ab diesem Tag, nicht ab dem Zahlungsbefehl.",
            "en": "The right of third parties to inspect lapses five years after the "
                  "proceedings ended. An enforcement that ended that long ago no longer "
                  "appears on an extract for landlords, employers or banks. You do not have "
                  "to request anything for this. Courts and authorities can still ask for "
                  "extracts. If the enforcement still appears, ask the debt enforcement "
                  "office on which day the proceedings ended: the five years count from "
                  "that day, not from the payment order."},
        "sources": (("schkg", "8a", "Art. 8a Abs. 4 SchKG"),),
        "terms": ("term_betreibungsregister",),
    },
    "loss_certificate": {
        "title": {"de": "Verlustschein", "en": "Loss certificate"},
        "verdict": "delete",
        "text": {
            "de": "Die Forderung aus einem Verlustschein verjährt erst 20 Jahre nach dessen "
                  "Ausstellung. Der Eintrag wird gelöscht, sobald die Forderung getilgt ist. "
                  "Sie können sie jederzeit beim Betreibungsamt bezahlen, das den "
                  "Verlustschein ausgestellt hat; das Amt leitet den Betrag an den Gläubiger "
                  "weiter. Die Löschung wird Ihnen auf Verlangen bescheinigt. Einigen Sie "
                  "sich direkt mit dem Gläubiger, zum Beispiel auf einen tieferen Betrag, "
                  "braucht das Amt einen Nachweis der Tilgung, in der Regel den quittierten "
                  "Verlustschein. Ein tieferer Betrag ist Verhandlungssache; der Gläubiger "
                  "muss darauf nicht eingehen.",
            "en": "The claim in a loss certificate becomes time-barred only 20 years after "
                  "it was issued. The entry is deleted once the claim is settled. You can "
                  "pay it at any time at the debt enforcement office that issued the loss "
                  "certificate; the office passes the amount on to the creditor. On request "
                  "the deletion is certified to you. If you settle directly with the "
                  "creditor, for example on a lower amount, the office needs proof of the "
                  "settlement, as a rule the receipted loss certificate. A lower amount is "
                  "a matter of negotiation; the creditor does not have to agree."},
        "sources": (("schkg", "149a", "Art. 149a SchKG"),),
        "terms": ("term_verlustschein",),
    },
    "private_agency": {
        "title": {"de": "Eintrag bei einer privaten Auskunftei",
                  "en": "Entry at a private credit agency"},
        "verdict": "not_covered",
        "text": {
            "de": "Einträge bei privaten Wirtschaftsauskunfteien, zum Beispiel CRIF oder "
                  "Intrum, stehen nicht im Betreibungsregister. Für sie gelten andere "
                  "Regeln, vor allem das Datenschutzrecht. Das kann ich mit den "
                  "gespeicherten Quellen noch nicht prüfen. Ein:e Rechtsberater:in von "
                  "LexTec kann das.",
            "en": "Entries at private credit agencies, for example CRIF or Intrum, are not "
                  "in the debt enforcement register. Other rules apply to them, above all "
                  "data protection law. I cannot check this with the stored sources yet. A "
                  "legal advisor at LexTec can."},
        "sources": (),
        "terms": ("term_betreibungsregister",),
    },
    "get_extract": {
        "title": {"de": "Zuerst den eigenen Auszug bestellen",
                  "en": "First order your own extract"},
        "verdict": "check",
        "text": {
            "de": "Bestellen Sie einen Auszug über sich selbst beim Betreibungsamt Ihres "
                  "Wohnorts. Darauf steht, welche Betreibungen und Verlustscheine Dritte "
                  "sehen, und zu jeder Betreibung der Stand. Ein schriftlicher Auszug kostet "
                  "pauschal 17 Franken. Mit dem Auszug lässt sich sagen, was möglich ist.",
            "en": "Order an extract about yourself from the debt enforcement office at your "
                  "place of residence. It shows which enforcements and loss certificates "
                  "third parties see, and the status of each enforcement. A written extract "
                  "costs a flat 17 francs. With the extract it can be said what is "
                  "possible."},
        "sources": (("schkg", "8a", "Art. 8a Abs. 1 SchKG"),
                    ("gebv", "12a", "Art. 12a GebV SchKG")),
        "terms": ("term_betreibungsregister",),
    },
    # ---- gate 2, track A: not paid, objection raised -------------------------------------
    "request_possible": {
        "title": {"de": "Gesuch um Nichtbekanntgabe", "en": "Request for non-disclosure"},
        "verdict": "request",
        "text": {
            "de": "Sie haben Rechtsvorschlag erhoben, und seit der Zustellung des "
                  "Zahlungsbefehls sind nach Ihren Angaben mehr als drei Monate vergangen. "
                  "Sie können beim Betreibungsamt ein Gesuch stellen, dass die Betreibung "
                  "Dritten nicht mehr bekannt gegeben wird. " + _PROCEDURE["de"],
            "en": "You raised an objection, and according to your answers more than three "
                  "months have passed since the payment order was served. You can file a "
                  "request with the debt enforcement office that the enforcement is no "
                  "longer disclosed to third parties. " + _PROCEDURE["en"]},
        "sources": (_LIT_D, _FEE),
        "terms": ("term_nichtbekanntgabe", "term_rechtsvorschlag"),
    },
    "request_wait": {
        "title": {"de": "Gesuch um Nichtbekanntgabe", "en": "Request for non-disclosure"},
        "verdict": "wait",
        "text": {
            "de": "Das Gesuch um Nichtbekanntgabe ist erst möglich, wenn seit der Zustellung "
                  "des Zahlungsbefehls drei Monate vergangen sind. Nach Ihren Angaben ist "
                  "das ab dem {date} der Fall. Bis dahin gibt es zwei Wege. Der Gläubiger "
                  "kann die Betreibung zurückziehen; dann wird sie Dritten nicht mehr "
                  "gezeigt. Dazu zwingen können Sie ihn nicht. Und Sie können jederzeit "
                  "verlangen, dass der Gläubiger aufgefordert wird, seine Beweismittel beim "
                  "Betreibungsamt vorzulegen. Das ändert am Eintrag nichts und an laufenden "
                  "Fristen auch nicht, zeigt aber, worauf er sich stützt.",
            "en": "The request for non-disclosure is possible only once three months have "
                  "passed since the payment order was served. According to your answers "
                  "this is the case from {date}. Until then there are two ways. The creditor "
                  "can withdraw the enforcement; it is then no longer shown to third "
                  "parties. You cannot force the creditor to do so. And you can at any time "
                  "demand that the creditor is asked to present its evidence at the debt "
                  "enforcement office. This changes nothing about the entry or about "
                  "running periods, but it shows what the creditor relies on."},
        "sources": (("schkg", "8a", "Art. 8a Abs. 3 Bst. c und d SchKG"),
                    ("schkg", "73", "Art. 73 SchKG")),
        "terms": ("term_nichtbekanntgabe", "term_rueckzug"),
    },
    "request_after_wait": {
        "title": {"de": "Gesuch um Nichtbekanntgabe", "en": "Request for non-disclosure"},
        "verdict": "after_wait",
        "text": {
            "de": "Sie haben Rechtsvorschlag erhoben. Sobald seit der Zustellung des "
                  "Zahlungsbefehls drei Monate vergangen sind, können Sie beim "
                  "Betreibungsamt ein Gesuch stellen, dass die Betreibung Dritten nicht mehr "
                  "bekannt gegeben wird. Das Datum der Zustellung steht auf dem "
                  "Zahlungsbefehl. " + _PROCEDURE["de"],
            "en": "You raised an objection. Once three months have passed since the payment "
                  "order was served, you can file a request with the debt enforcement "
                  "office that the enforcement is no longer disclosed to third parties. The "
                  "date of service is on the payment order. " + _PROCEDURE["en"]},
        "sources": (_LIT_D, _FEE),
        "terms": ("term_nichtbekanntgabe", "term_rechtsvorschlag"),
    },
    "creditor_pending": {
        "title": {"de": "Der Gläubiger hat ein Gericht eingeschaltet",
                  "en": "The creditor went to court"},
        "verdict": "court_running",
        "text": {
            "de": "Solange ein Verfahren läuft, mit dem der Gläubiger den Rechtsvorschlag "
                  "beseitigen lassen will, hat das Gesuch um Nichtbekanntgabe keinen Erfolg: "
                  "Der Gläubiger kann dem Betreibungsamt nachweisen, dass er das Verfahren "
                  "rechtzeitig eingeleitet hat. Entscheidend ist der Ausgang. Wird das "
                  "Begehren des Gläubigers endgültig nicht gutgeheissen, können Sie das "
                  "Gesuch stellen und den Entscheid beilegen. In einem Gerichtsverfahren "
                  "gelten kurze Fristen; lassen Sie sich dafür beraten.",
            "en": "As long as proceedings are running by which the creditor wants the "
                  "objection removed, the request for non-disclosure does not succeed: the "
                  "creditor can prove to the debt enforcement office that it started the "
                  "proceedings in time. What decides is the outcome. If the creditor's "
                  "request is finally not granted, you can file the request and enclose "
                  "the decision. Short periods apply in court proceedings; take advice on "
                  "them."},
        "sources": (_LIT_D, ("schkg", "79", "Art. 79 SchKG")),
        "terms": ("term_rechtsoeffnung", "term_nichtbekanntgabe"),
    },
    "creditor_lost": {
        "title": {"de": "Der Gläubiger ist vor Gericht gescheitert",
                  "en": "The creditor failed in court"},
        "verdict": "request",
        "text": {
            "de": "Der Gläubiger hat ein Verfahren eingeleitet, um den Rechtsvorschlag zu "
                  "beseitigen, ist damit aber endgültig gescheitert. Seit dem 1. Januar 2026 "
                  "sagt das Gesetz dazu ausdrücklich: Weisen Sie nach, dass das Begehren des "
                  "Gläubigers definitiv nicht gutgeheissen wurde, wird die Betreibung "
                  "Dritten nicht bekannt gegeben. Stellen Sie beim Betreibungsamt das Gesuch "
                  "um Nichtbekanntgabe und legen Sie den rechtskräftigen Entscheid bei. Das "
                  "Gesuch kostet pauschal 40 Franken.",
            "en": "The creditor started proceedings to remove the objection but finally "
                  "failed. Since 1 January 2026 the statute says so expressly: if you prove "
                  "that the creditor's request was definitively not granted, the "
                  "enforcement is not disclosed to third parties. File the request for "
                  "non-disclosure with the debt enforcement office and enclose the final "
                  "decision. The request costs a flat 40 francs."},
        "sources": (_LIT_D, _FEE),
        "terms": ("term_nichtbekanntgabe", "term_rechtsoeffnung"),
    },
    "creditor_won": {
        "title": {"de": "Das Gericht hat den Rechtsvorschlag beseitigt",
                  "en": "The court removed the objection"},
        "verdict": "stays",
        "text": {
            "de": "Hat das Gericht den Rechtsvorschlag beseitigt, kann der Gläubiger die "
                  "Betreibung fortsetzen, und sie wird Dritten weiter gezeigt. Das Gesuch um "
                  "Nichtbekanntgabe hilft dann nicht. Besteht die Schuld aus Ihrer Sicht "
                  "trotzdem nicht, können Sie beim Gericht feststellen lassen, dass sie "
                  "nicht besteht; heisst es die Klage gut, hebt es die Betreibung auf, und "
                  "sie wird Dritten nicht mehr gezeigt. Sonst verschwindet der Eintrag fünf "
                  "Jahre nach Abschluss des Verfahrens, oder früher, wenn der Gläubiger die "
                  "Betreibung zurückzieht.",
            "en": "If the court removed the objection, the creditor can continue the "
                  "enforcement, and it is still shown to third parties. The request for "
                  "non-disclosure does not help then. If in your view the debt does not "
                  "exist all the same, you can have a court declare that it does not exist; "
                  "if the court grants the action, it sets the enforcement aside, and it is "
                  "no longer shown to third parties. Otherwise the entry disappears five "
                  "years after the proceedings ended, or earlier if the creditor withdraws "
                  "the enforcement."},
        "sources": (("schkg", "79", "Art. 79 SchKG"), ("schkg", "85a", "Art. 85a SchKG"),
                    ("schkg", "8a", "Art. 8a Abs. 3 Bst. a und c, Abs. 4 SchKG")),
        "terms": ("term_rechtsoeffnung", "term_rueckzug"),
    },
    # ---- gate 2, track A: not paid, no objection -------------------------------------------
    "objection_open": {
        "title": {"de": "Rechtsvorschlag noch möglich", "en": "Objection still possible"},
        "verdict": "act_now",
        "text": {
            "de": "Nach Ihren Angaben läuft die Frist für den Rechtsvorschlag noch. Erheben "
                  "Sie ihn jetzt, mündlich oder schriftlich beim Betreibungsamt; eine "
                  "Begründung ist nicht nötig. Er stoppt die Betreibung, und er ist die "
                  "Voraussetzung dafür, dass Sie später verlangen können, dass der Eintrag "
                  "Dritten nicht mehr gezeigt wird.",
            "en": "According to your answers the period for the objection is still running. "
                  "Raise it now, orally or in writing, at the debt enforcement office; no "
                  "reasons are needed. It stops the enforcement, and it is the condition "
                  "for asking later that the entry is no longer shown to third parties."},
        "sources": (("schkg", "74", "Art. 74 SchKG"), _LIT_D),
        "terms": ("term_rechtsvorschlag", "term_nichtbekanntgabe"),
    },
    "missed_obstacle": {
        "title": {"de": "Unverschuldet verhindert: Wiederherstellung der Frist",
                  "en": "Prevented through no fault: restoration of the period"},
        "verdict": "act_now",
        "text": {
            "de": "Wer durch ein unverschuldetes Hindernis, zum Beispiel einen "
                  "Spitalaufenthalt, davon abgehalten wurde, rechtzeitig Rechtsvorschlag zu "
                  "erheben, kann um Wiederherstellung der Frist ersuchen. Das Gesuch ist zu "
                  "begründen und innert zehn Tagen einzureichen, nachdem das Hindernis "
                  "weggefallen ist; gleichzeitig ist der Rechtsvorschlag nachzuholen. Ist "
                  "diese Zeit bei Ihnen schon vorbei, bleibt der Weg über das Gericht.",
            "en": "A person who was prevented by an obstacle that was not their fault, for "
                  "example a stay in hospital, from raising the objection in time can ask "
                  "for the period to be restored. The request needs reasons and has to be "
                  "filed within ten days after the obstacle ceased; the objection has to be "
                  "made up at the same time. If that time has already passed for you, the "
                  "way through a court remains."},
        "sources": (("schkg", "33", "Art. 33 Abs. 4 SchKG"), ("schkg", "74", "Art. 74 SchKG")),
        "terms": ("term_wiederherstellung", "term_rechtsvorschlag"),
    },
    "missed_abusive": {
        "title": {"de": "Reine Schikane: Nichtigkeit der Betreibung",
                  "en": "Pure harassment: nullity of the enforcement"},
        "verdict": "authority",
        "text": {
            "de": "Eine Betreibung kann nichtig sein, wenn der Gläubiger damit offensichtlich "
                  "Ziele verfolgt, die mit dem Eintreiben einer Forderung nichts zu tun "
                  "haben, etwa reine Schikane. Das ist die Ausnahme. Es genügt nicht, dass "
                  "Sie die Forderung für unberechtigt halten: Weder das Betreibungsamt noch "
                  "die Aufsichtsbehörde prüfen, ob die Forderung besteht. Die Nichtigkeit "
                  "stellt die Aufsichtsbehörde fest; eine nichtige Betreibung wird Dritten "
                  "nicht bekannt gegeben.",
            "en": "An enforcement can be void if the creditor obviously pursues aims with it "
                  "that have nothing to do with collecting a claim, such as pure harassment. "
                  "This is the exception. It is not enough that you consider the claim "
                  "unjustified: neither the debt enforcement office nor the supervisory "
                  "authority examines whether the claim exists. Nullity is established by "
                  "the supervisory authority; a void enforcement is not disclosed to third "
                  "parties."},
        "sources": (("schkg", "22", "Art. 22 SchKG"),
                    ("schkg", "8a", "Art. 8a Abs. 3 Bst. a SchKG"),
                    ("decision", "bge-140-iii-481", "BGE 140 III 481")),
        "terms": ("term_betreibung",),
    },
    "missed_court": {
        "title": {"de": "Ohne Rechtsvorschlag: Weg über das Gericht",
                  "en": "Without an objection: the way through a court"},
        "verdict": "court",
        "text": {
            "de": "Ohne Rechtsvorschlag läuft die Betreibung weiter, und das Gesuch um "
                  "Nichtbekanntgabe steht nicht offen. Sind seit der Zustellung des "
                  "Zahlungsbefehls noch keine zehn Tage vergangen, erheben Sie den "
                  "Rechtsvorschlag sofort. Sonst bleibt das Gericht: Sie können jederzeit "
                  "feststellen lassen, dass die Schuld nicht oder nicht mehr besteht; heisst "
                  "das Gericht die Klage gut, hebt es die Betreibung auf. Haben Sie eine "
                  "Nichtschuld bezahlt, weil der Rechtsvorschlag fehlte, können Sie den "
                  "Betrag innert eines Jahres nach der Zahlung zurückfordern. Nach einem "
                  "solchen Entscheid wird die Betreibung Dritten nicht mehr bekannt gegeben. "
                  "Vor Gericht müssen Sie nachweisen, dass Sie nichts schulden.",
            "en": "Without an objection the enforcement continues, and the request for "
                  "non-disclosure is not open. If ten days have not yet passed since the "
                  "payment order was served, raise the objection at once. Otherwise the "
                  "court remains: you can at any time have it declared that the debt does "
                  "not or no longer exist; if the court grants the action, it sets the "
                  "enforcement aside. If you paid a debt that was not owed because the "
                  "objection was missing, you can claim the amount back within one year "
                  "after the payment. After such a decision the enforcement is no longer "
                  "disclosed to third parties. In court you have to prove that you owe "
                  "nothing."},
        "sources": (("schkg", "85a", "Art. 85a SchKG"), ("schkg", "86", "Art. 86 SchKG"),
                    ("schkg", "8a", "Art. 8a Abs. 3 Bst. a und b SchKG")),
        "terms": ("term_rechtsvorschlag",),
    },
    # ---- gate 2, track B: paid --------------------------------------------------------------
    "paid_before": {
        "title": {"de": "Bezahlt vor dem Zahlungsbefehl", "en": "Paid before the payment order"},
        "verdict": "no_bar",
        "text": {
            "de": "Wer schon bezahlt hat, bevor ihm der Zahlungsbefehl zugestellt wurde, "
                  "kann das Gesuch um Nichtbekanntgabe stellen: Die Betreibung war dann von "
                  "Anfang an ungerechtfertigt. Massgebend ist der Tag der Zustellung des "
                  "Zahlungsbefehls, nicht der Tag, an dem der Gläubiger die Betreibung "
                  "verlangt hat. So hat es das Bundesgericht in einem Fall entschieden. "
                  "Belegen Sie die Zahlung und ihr Datum, zum Beispiel mit einem "
                  "Kontoauszug.",
            "en": "A person who had already paid before the payment order was served on "
                  "them can file the request for non-disclosure: the enforcement was then "
                  "unjustified from the start. What decides is the day the payment order "
                  "was served, not the day the creditor asked for the enforcement. The "
                  "Federal Supreme Court held so in one case. Document the payment and its "
                  "date, for example with a bank statement."},
        "sources": (_LIT_D, ("decision", "bge-150-iii-390", "BGE 150 III 390")),
        "terms": ("term_nichtbekanntgabe", "term_zustellung"),
    },
    "paid_before_no_objection": {
        "title": {"de": "Bezahlt vor dem Zahlungsbefehl, kein Rechtsvorschlag",
                  "en": "Paid before the payment order, no objection"},
        "verdict": "court",
        "text": {
            "de": "Ohne Rechtsvorschlag steht das Gesuch um Nichtbekanntgabe nicht offen. "
                  "Weil Sie schon vor der Betreibung bezahlt haben, gibt es zwei Wege. Der "
                  "einfachere: Zeigen Sie dem Gläubiger den Zahlungsbeleg und verlangen Sie, "
                  "dass er die Betreibung zurückzieht; dann wird sie Dritten nicht mehr "
                  "gezeigt. Tut er das nicht, können Sie beim Gericht des Betreibungsortes "
                  "die Aufhebung der Betreibung verlangen, wenn Sie mit Urkunden beweisen, "
                  "dass die Schuld samt Zinsen und Kosten getilgt ist. Eine aufgehobene "
                  "Betreibung wird Dritten nicht bekannt gegeben.",
            "en": "Without an objection the request for non-disclosure is not open. Because "
                  "you had already paid before the enforcement, there are two ways. The "
                  "simpler one: show the creditor the proof of payment and demand that it "
                  "withdraws the enforcement; it is then no longer shown to third parties. "
                  "If the creditor does not, you can ask the court at the place of "
                  "enforcement to set the enforcement aside if you prove by documents that "
                  "the debt including interest and costs is settled. An enforcement that "
                  "was set aside is not disclosed to third parties."},
        "sources": (("schkg", "85", "Art. 85 SchKG"),
                    ("schkg", "8a", "Art. 8a Abs. 3 Bst. a und c SchKG")),
        "terms": ("term_rueckzug", "term_rechtsvorschlag"),
    },
    "paid_after": {
        "title": {"de": "Bezahlt nach dem Zahlungsbefehl", "en": "Paid after the payment order"},
        "verdict": "blocked",
        "text": {
            "de": "Wer die Forderung bezahlt, nachdem ihm der Zahlungsbefehl zugestellt "
                  "wurde, kann die Bekanntgabe nicht mit dem Gesuch um Nichtbekanntgabe "
                  "verhindern. Die Zahlung wird als Anerkennung der Forderung verstanden; "
                  "die Betreibung gilt dann nicht als ungerechtfertigt. So hat es das "
                  "Bundesgericht in einem Fall entschieden. Der Eintrag bleibt für Dritte "
                  "bis fünf Jahre nach Abschluss des Verfahrens sichtbar, auch wenn er als "
                  "bezahlt vermerkt ist.",
            "en": "A person who pays the claim after the payment order was served on them "
                  "cannot prevent the disclosure with the request for non-disclosure. The "
                  "payment is understood as acknowledging the claim; the enforcement then "
                  "does not count as unjustified. The Federal Supreme Court held so in one "
                  "case. The entry stays visible to third parties until five years after "
                  "the proceedings ended, even if it is marked as paid."},
        "sources": (("decision", "bge-147-iii-486", "BGE 147 III 486"), _LIT_D,
                    ("schkg", "8a", "Art. 8a Abs. 4 SchKG")),
        "terms": ("term_nichtbekanntgabe",),
    },
    "withdrawal": {
        "title": {"de": "Rückzug durch den Gläubiger", "en": "Withdrawal by the creditor"},
        "verdict": "creditor",
        "text": {
            "de": "Es bleibt ein Weg: Der Gläubiger kann die Betreibung beim Betreibungsamt "
                  "zurückziehen. Dann wird sie Dritten nicht mehr bekannt gegeben. Bitten "
                  "Sie ihn schriftlich darum und weisen Sie darauf hin, dass alles bezahlt "
                  "ist. Einen Anspruch darauf haben Sie nicht; der Gläubiger entscheidet "
                  "frei.",
            "en": "One way remains: the creditor can withdraw the enforcement at the debt "
                  "enforcement office. It is then no longer disclosed to third parties. Ask "
                  "the creditor in writing and point out that everything is paid. You have "
                  "no right to it; the creditor decides freely."},
        "sources": (("schkg", "8a", "Art. 8a Abs. 3 Bst. c SchKG"),),
        "terms": ("term_rueckzug",),
    },
    # ---- an answer is not known ---------------------------------------------------------------
    "payment_unknown": {
        "title": {"de": "Es kommt auf die Zahlung an", "en": "It depends on the payment"},
        "verdict": "check",
        "text": {
            "de": "Ob und wann bezahlt wurde, entscheidet über den Weg. Wurde nicht bezahlt "
                  "oder schon vor der Zustellung des Zahlungsbefehls, und wurde "
                  "Rechtsvorschlag erhoben, steht drei Monate nach der Zustellung das Gesuch "
                  "um Nichtbekanntgabe offen. Wurde nach der Zustellung bezahlt, ist dieses "
                  "Gesuch ausgeschlossen; dann hilft nur, dass der Gläubiger die Betreibung "
                  "zurückzieht.",
            "en": "Whether and when the claim was paid decides the way. If it was not paid, "
                  "or already before the payment order was served, and an objection was "
                  "raised, the request for non-disclosure is open three months after "
                  "service. If it was paid after service, this request is excluded; then "
                  "only a withdrawal of the enforcement by the creditor helps."},
        "sources": (("schkg", "8a", "Art. 8a Abs. 3 Bst. c und d SchKG"),),
        "terms": ("term_nichtbekanntgabe", "term_rueckzug"),
    },
    "objection_unknown": {
        "title": {"de": "Es kommt auf den Rechtsvorschlag an",
                  "en": "It depends on the objection"},
        "verdict": "check",
        "text": {
            "de": "Ob Rechtsvorschlag erhoben wurde, sehen Sie auf Ihrem eigenen "
                  "Betreibungsauszug, oder Sie fragen beim Betreibungsamt nach. Mit "
                  "Rechtsvorschlag steht drei Monate nach der Zustellung des Zahlungsbefehls "
                  "das Gesuch um Nichtbekanntgabe offen; es kostet pauschal 40 Franken. Ohne "
                  "Rechtsvorschlag bleibt der Weg über das Gericht oder der Rückzug durch "
                  "den Gläubiger.",
            "en": "Whether an objection was raised is shown on your own register extract, "
                  "or you can ask the debt enforcement office. With an objection, the "
                  "request for non-disclosure is open three months after the payment order "
                  "was served; it costs a flat 40 francs. Without an objection, the way "
                  "through a court or a withdrawal by the creditor remains."},
        "sources": (("schkg", "8a", "Art. 8a Abs. 3 Bst. c und d SchKG"), _FEE),
        "terms": ("term_rechtsvorschlag", "term_nichtbekanntgabe"),
    },
}

# Shown under the result. Worded generally, so they need no question.
NOTES: dict[str, dict] = {
    "not_deletion": {
        "title": {"de": "Nichtbekanntgabe ist keine Löschung",
                  "en": "Non-disclosure is not deletion"},
        "text": {
            "de": "Die Betreibung bleibt im Register. Sie erscheint nur nicht mehr auf "
                  "Auszügen für Dritte wie Vermieter, Arbeitgeber oder Banken.",
            "en": "The enforcement stays in the register. It only no longer appears on "
                  "extracts for third parties such as landlords, employers or banks."},
        "sources": (("schkg", "8a", "Art. 8a Abs. 3 SchKG"),),
        "terms": (),
    },
    "pay_trap": {
        "title": {"de": "Bevor Sie doch bezahlen", "en": "Before you pay after all"},
        "text": {
            "de": "Bezahlen allein lässt den Eintrag nicht verschwinden, und nach einer "
                  "Zahlung ist das Gesuch um Nichtbekanntgabe ausgeschlossen. Wer eine "
                  "betriebene Forderung bezahlen will, lässt sich deshalb vorher schriftlich "
                  "zusichern, dass der Gläubiger die Betreibung zurückzieht.",
            "en": "Paying alone does not make the entry disappear, and after a payment the "
                  "request for non-disclosure is excluded. A person who wants to pay a "
                  "claim under enforcement therefore gets the creditor's written assurance "
                  "beforehand that it will withdraw the enforcement."},
        "sources": (("schkg", "8a", "Art. 8a Abs. 3 Bst. c SchKG"),
                    ("decision", "bge-147-iii-486", "BGE 147 III 486")),
        "terms": ("term_rueckzug",),
    },
    "five_years": {
        "title": {"de": "Spätestens nach fünf Jahren", "en": "After five years at the latest"},
        "text": {
            "de": "Jede Betreibung verschwindet von den Auszügen für Dritte fünf Jahre nach "
                  "Abschluss des Verfahrens.",
            "en": "Every enforcement disappears from the extracts for third parties five "
                  "years after the proceedings ended."},
        "sources": (("schkg", "8a", "Art. 8a Abs. 4 SchKG"),),
        "terms": (),
    },
}

_REQUEST = {"over": "request_possible", "running": "request_wait", "unknown": "request_after_wait"}


def _answered(case: Case, name: str) -> bool:
    f = case.facts.get(name)
    return f is not None and f.status is not Status.MISSING


def _keys(case: Case) -> tuple[str, list[str], list[str]]:
    """(key of the summary sentence, keys of the findings, keys of the notes). No
    findings while the answer that decides the next step is still missing."""
    none = ("", [], [])
    if not _answered(case, "register_entry"):
        return none
    entry = case.value("register_entry")
    if entry is None:                                     # "I do not know"
        return "check", ["get_extract"], []
    if entry == "old_enforcement":
        return "hidden", ["old"], []
    if entry == "loss_certificate":
        return "delete", ["loss_certificate"], []
    if entry == "private_agency":
        return "not_covered", ["private_agency"], []

    # Gate 2: a newer or running enforcement.
    if not _answered(case, "register_payment"):
        return none
    payment = case.value("register_payment")
    if payment is None:
        return "check", ["payment_unknown"], ["five_years"]
    if payment == "paid_after":
        return "blocked", ["paid_after", "withdrawal"], []
    before = payment == "paid_before"
    lead = ["paid_before"] if before else []
    trap = [] if before else ["pay_trap"]

    if not _answered(case, "register_objection"):
        return none
    objection = case.value("register_objection")
    if objection is None:
        return "check", lead + ["objection_unknown"], trap + ["five_years"]
    if not _answered(case, "register_service_date"):
        return none
    wait = register_wait(case)

    if objection == "yes":
        if before:
            return ("request" if wait == "over" else "wait",
                    lead + [_REQUEST[wait]], ["not_deletion"])
        if not _answered(case, "register_creditor_step"):
            return none
        step = case.value("register_creditor_step")       # None: "I do not know"
        if step == "pending":
            return "court", ["creditor_pending"], trap + ["five_years"]
        if step == "won":
            return "blocked", ["creditor_won"], []
        if step == "lost" and wait != "running":
            return "request", ["creditor_lost"], ["not_deletion"] + trap
        return ("request" if wait == "over" else "wait",
                [_REQUEST[wait]], ["not_deletion"] + trap)

    # No objection.
    if register_objection_open(case):
        return "act_now", lead + ["objection_open"], trap
    if before:
        return "court", ["paid_before_no_objection"], ["five_years"]
    if not _answered(case, "register_missed_reason"):
        return none
    reason = case.value("register_missed_reason") or "other"
    findings = {"obstacle": ["missed_obstacle", "missed_court"],
                "abusive": ["missed_abusive", "missed_court"],
                "other": ["missed_court"]}[reason]
    return "court", findings, trap + ["five_years"]


@lru_cache(maxsize=1)
def _decisions() -> dict:
    return json.loads(CASE_LAW.read_text(encoding="utf-8")) if CASE_LAW.exists() else {}


def _citation(source: tuple, lang: str) -> dict:
    kind, ref, citation = source
    if kind == "decision":
        return {"citation": citation, "url": _decisions().get(ref, {}).get("url", "")}
    return {"citation": knowledge.citation_text(citation, lang),
            "url": knowledge.fedlex_url(kind, ref, lang)}


def _item(entry: dict, lang: str, key: str, case: Case) -> dict:
    text = entry["text"][lang]
    if "{date}" in text:
        first = register_request_from(case)
        text = text.format(date=first.strftime("%d.%m.%Y") if first else "")
    out = {"key": key, "title": entry["title"][lang], "text": text,
           "citations": [_citation(s, lang) for s in entry["sources"]],
           "terms": knowledge.terms(entry["terms"], lang)}
    if "verdict" in entry:
        out["verdict"] = entry["verdict"]
        out["verdict_label"] = VERDICTS[entry["verdict"]][lang]
    return out


def assess(case: Case, decision: Decision | None = None, lang: str | None = None) -> dict | None:
    """The result for a register entry, from fixed texts, in the same shape as the
    results for late fees and for declining an inheritance. None if the case is not a
    register case or the deciding answer is still missing."""
    if "credit_record" not in case.areas:
        return None
    lang = lang or case.language
    state, findings, notes = _keys(case)
    if not findings:
        return None
    return {"title": T["title"][lang], "basis": T["basis"][lang],
            "summary": SUMMARY[state][lang],
            "positions": [_item(FINDINGS[k], lang, k, case) for k in findings],
            "notes_title": T["notes_title"][lang],
            "notes": [_item(NOTES[k], lang, k, case) for k in notes],
            "source_label": T["source"][lang], "terms_label": T["terms"][lang]}
