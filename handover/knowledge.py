"""Reviewed answers to questions that users ask the system.

A user message is not always case input. People also ask what the service
does, what happens to their data, or what a term in an official letter means.
The system answers such questions from the fixed texts in this file.

The language model does not write these answers. It only names the topic of
the user's question (extract.py); the text shown is the one stored here. A
wrong choice of topic therefore gives an unhelpful answer, not an invented one.

Two kinds of entry:
  service_*  what the service is and how it works
  term_*     what a legal term means in general, with the statute it rests on

Special topics without a stored text are handled in engine.py:
  own_case       the user asks what applies in their own case
  question_help  the user does not understand one of the system's questions
  other          any other question

DRAFTS: every text here is to be reviewed by the legal lead. The term
explanations are general statements of law written by the AI assistant from
the statute; "service_cost" needs the facts from LexTec.
"""
from __future__ import annotations

import re

from .texts import DISCLOSURE_PARTS


def _topics(lang: str) -> str:
    return "; ".join(title for title, _ in DISCLOSURE_PARTS[lang]["topics"])


ENTRIES: dict[str, dict] = {
    # ---- the service ----------------------------------------------------------
    "service_scope": {
        "describe": "what the service can help with, which topics it covers",
        "title": {"de": "Wobei ich helfen kann", "en": "What I can help with"},
        "text": {
            "de": "Ich bin ein KI-System von LexTec für Fragen rund um Schulden im Kanton "
                  f"Zürich. Ich decke fünf Themen ab: {_topics('de')}. Sie schildern Ihr "
                  "Anliegen in eigenen Worten, und ich frage nach, was fehlt. Danach "
                  "erhalten Sie eine allgemeine rechtliche Einordnung mit den "
                  "Gesetzesstellen, auf die sie sich stützt. Wenn eine Frist drängt oder "
                  "der Fall heikel ist, schlage ich Ihnen vor, ihn an eine:n "
                  "Rechtsberater:in von LexTec zu übergeben. Bei anderen Themen (z. B. "
                  "Miete, Arbeit, Familie) schlage ich die Übergabe direkt vor.",
            "en": "I am an AI system of LexTec for questions about debt in the Canton of "
                  f"Zurich. I cover five topics: {_topics('en')}. You describe your "
                  "situation in your own words, and I ask for what is missing. You then "
                  "receive a general legal classification with the statute articles it "
                  "rests on. If a deadline is pressing or the case is delicate, I suggest "
                  "handing it to a legal advisor at LexTec. For other topics (e.g. "
                  "tenancy, employment, family) I suggest the hand-over straight away.",
        },
    },
    "service_process": {
        "describe": "how the conversation works, what happens next, what the user receives",
        "title": {"de": "So läuft das Gespräch ab", "en": "How the conversation works"},
        "text": {
            "de": "Sie beschreiben, was passiert ist. Ich stelle höchstens drei Rückfragen "
                  "auf einmal und erkläre jeweils, warum ich frage. Wo es geht, wählen Sie "
                  "die Antwort aus einer Liste; Fachbegriffe sind erklärt. Wenn alle nötigen "
                  "Angaben vorliegen, erhalten Sie eine allgemeine Einordnung mit Quellen. "
                  "Wenn eine Frist drängt, eine wichtige Angabe offen bleibt oder der Fall "
                  "heikel ist, schlage ich die Übergabe an unser Team vor. Übergeben wird "
                  "nur, wenn Sie zustimmen.",
            "en": "You describe what happened. I ask at most three follow-up questions at "
                  "a time and explain why I ask each one. Where possible you choose the "
                  "answer from a list; legal terms are explained. Once all necessary information "
                  "is there, you receive a general classification with sources. If a "
                  "deadline is pressing, an important point stays open or the case is "
                  "delicate, I suggest the hand-over to our team. Nothing is handed over "
                  "unless you agree.",
        },
    },
    "service_human": {
        "describe": "who the humans or legal advisors are, how to reach a person, "
                    "what a hand-over means",
        "title": {"de": "Menschen bei LexTec", "en": "The people at LexTec"},
        "text": {
            "de": "Rechtsberater:innen von LexTec sind Anwält:innen oder Personen mit einem "
                  "juristischen Masterabschluss. Sie können jederzeit sagen, dass Sie mit "
                  "einem Menschen sprechen möchten. Ich übergebe Ihr Anliegen nur mit "
                  "Ihrer Zustimmung; unser Team erhält dann eine Zusammenfassung dieses "
                  "Gesprächs, damit Sie nicht alles noch einmal erklären müssen.",
            "en": "Legal advisors at LexTec are lawyers or people with a master's degree "
                  "in law. You can say at any time that you would like to speak to a "
                  "human. I hand your matter over only with your agreement; our team then "
                  "receives a summary of this conversation, so that you do not have to "
                  "explain everything again.",
        },
    },
    "service_privacy": {
        "describe": "what happens to the user's messages and data, who can read them",
        "title": {"de": "Ihre Daten", "en": "Your data"},
        "text": {
            "de": "Ihre Nachrichten werden zur Verarbeitung an einen externen KI-Dienst "
                  "übermittelt. Unser Team erhält eine Zusammenfassung erst, wenn Sie der "
                  "Übergabe zustimmen. Schreiben Sie bitte nur, was für Ihr Anliegen nötig "
                  "ist.",
            "en": "Your messages are sent to an external AI service for processing. Our "
                  "team receives a summary only once you agree to the hand-over. Please "
                  "write only what is needed for your matter.",
        },
    },
    "service_limits": {
        "describe": "whether this is legal advice, whether it is binding, whether it "
                    "creates a mandate or keeps deadlines",
        "title": {"de": "Was dieses Gespräch nicht ist", "en": "What this conversation is not"},
        "text": {
            "de": "Sie schreiben mit einem KI-System, nicht mit einem Menschen. Ich gebe "
                  "eine allgemeine rechtliche Einordnung, keine Rechtsberatung im "
                  "Einzelfall. Das Gespräch begründet kein Mandat und wahrt keine Fristen: "
                  "Läuft eine Frist, müssen Sie selbst oder eine beauftragte Person "
                  "rechtzeitig handeln.",
            "en": "You are writing with an AI system, not with a human. I give a general "
                  "legal classification, not legal advice on your individual case. The "
                  "conversation does not establish a mandate and does not preserve any "
                  "deadlines: if a deadline is running, you or a person you instruct must "
                  "act in time.",
        },
    },
    "service_cost": {
        "describe": "what the service or a consultation costs, the conditions of LexTec",
        "title": {"de": "Kosten", "en": "Cost"},
        "text": {
            "de": "Dieses Gespräch ist unverbindlich und kostenlos. Nach den Angaben auf der "
                  "Website von LexTec (Stand 13.11.2026) ist eine erste Orientierung von 15 "
                  "Minuten kostenlos; eine vertiefte Beratung kostet CHF 45 für 30 Minuten "
                  "oder CHF 85 für 60 Minuten. Verbindlich sind die Angaben von LexTec "
                  "selbst.",
            "en": "This conversation carries no obligation and is free. According to "
                  "LexTec's website (as of 13.11.2026) a first orientation of 15 minutes is "
                  "free; an in-depth consultation costs CHF 45 for 30 minutes or CHF 85 for "
                  "60 minutes. Only LexTec's own information is binding.",
        },
    },

    # ---- terms ----------------------------------------------------------------
    "term_mahnung": {
        "describe": "what a reminder (Mahnung, Zahlungserinnerung) is, how many reminders "
                    "are needed",
        "title": {"de": "Mahnung und Zahlungserinnerung",
                  "en": "Reminder (Mahnung, Zahlungserinnerung)"},
        "source": ("or", "102", "Art. 102 Abs. 1 OR"),
        "text": {
            "de": "Eine Mahnung ist jede klare Aufforderung des Gläubigers, eine fällige "
                  "Rechnung zu bezahlen. Auch eine höflich formulierte «Zahlungserinnerung» "
                  "ist rechtlich eine Mahnung. Mit der Mahnung gerät der Schuldner in Verzug. "
                  "Eine Regel, dass es drei Mahnungen braucht, gibt es im Gesetz nicht: Eine "
                  "genügt. Eine Mahnung ist kein amtliches Dokument; die Frist für einen "
                  "Rechtsvorschlag läuft erst ab einem Zahlungsbefehl des Betreibungsamts.",
            "en": "A reminder is any clear request by the creditor to pay a bill that is "
                  "due. A politely worded 'Zahlungserinnerung' (payment reminder) is legally "
                  "a reminder too. The reminder puts the debtor in default. There is no rule "
                  "in the statute that three reminders are needed: one is enough. A reminder "
                  "is not an official document; the period for an objection only runs from "
                  "a payment order issued by the debt enforcement office.",
        },
    },
    "term_inkasso": {
        "describe": "what a collection agency (Inkassobüro) is, what it may do, and how it "
                    "differs from the debt enforcement office (Betreibungsamt)",
        "title": {"de": "Inkassobüro und Betreibungsamt",
                  "en": "Collection agency and debt enforcement office"},
        "text": {
            "de": "Ein Inkassobüro (z. B. Intrum, EOS, Pair Finance) ist ein privates "
                  "Unternehmen, das für Gläubiger Geld eintreibt. Es hat keine staatlichen "
                  "Befugnisse: Es kann nicht pfänden und selbst nichts ins "
                  "Betreibungsregister eintragen. Dafür muss es sich, wie jede Privatperson, "
                  "an das Betreibungsamt wenden. Das Betreibungsamt ist die staatliche Stelle "
                  "für die Zwangsvollstreckung. Ein Brief mit «Dossiernummer» und Strichcode "
                  "ist deshalb noch kein amtliches Schreiben.",
            "en": "A collection agency (Inkassobüro, e.g. Intrum, EOS, Pair Finance) is a "
                  "private company that collects money for creditors. It has no state "
                  "powers: it cannot seize wages or assets and cannot enter anything in the "
                  "debt enforcement register itself. For that it must apply to the debt "
                  "enforcement office (Betreibungsamt), like any private person. The debt "
                  "enforcement office is the state body for enforcement. A letter with a "
                  "'dossier number' and a barcode is therefore not yet an official document.",
        },
    },
    "term_verzugszins": {
        "describe": "what default interest (Verzugszins) is and what '5 % per year' means",
        "title": {"de": "Verzugszins (5 % pro Jahr)", "en": "Default interest (5 % per year)"},
        "source": ("or", "104", "Art. 104 OR"),
        "text": {
            "de": "Wer mit einer Geldschuld im Verzug ist, schuldet Verzugszins. Das Gesetz "
                  "sieht 5 Prozent pro Jahr vor; ein im Vertrag vereinbarter höherer Zins "
                  "kann weiter gelten. «Pro Jahr» heisst: 5 Prozent für ein ganzes Jahr "
                  "Verspätung, für eine kürzere Zeit entsprechend weniger. Beispiel: Bei "
                  "einer Rechnung von CHF 400, die 20 Tage nach Verzugsbeginn bezahlt wird, "
                  "sind das rund CHF 1.10, nicht CHF 20.",
            "en": "A person in default with a money debt owes default interest. The "
                  "statute sets 5 per cent per year; a higher rate agreed in the contract "
                  "can continue to apply. 'Per year' means: 5 per cent for a whole year of "
                  "delay, and proportionally less for a shorter time. Example: on a bill of "
                  "CHF 400 paid 20 days after default began, this is about CHF 1.10, not "
                  "CHF 20.",
        },
    },
    # ---- late fees: terms of the legal lead's glossary (2026-11-13) -------------
    "term_teilrechtsvorschlag": {
        "describe": "what a partial objection (Teil-Rechtsvorschlag) is, whether an objection "
                    "needs a lawyer or reasons",
        "title": {"de": "Teil-Rechtsvorschlag", "en": "Partial objection (Teil-Rechtsvorschlag)"},
        "source": ("schkg", "74", "Art. 74 SchKG"),
        "text": {
            "de": "Der Rechtsvorschlag ist kostenlos und braucht weder eine Begründung noch "
                  "eine Anwältin oder einen Anwalt: Der Satz «Ich erhebe Rechtsvorschlag» "
                  "genügt. Wer nur einen Teil der Forderung bestreitet, zum Beispiel nur die "
                  "Inkassogebühren, kann Teil-Rechtsvorschlag erheben. Dabei ist der "
                  "bestrittene Betrag in Franken genau anzugeben; sonst gilt die ganze "
                  "Forderung als bestritten.",
            "en": "The objection is free and needs neither reasons nor a lawyer: the "
                  "sentence 'Ich erhebe Rechtsvorschlag' (I raise an objection) is enough. A "
                  "person who disputes only part of the claim, for example only the "
                  "collection fees, can raise a partial objection. The disputed amount in "
                  "francs must then be stated exactly; otherwise the whole claim counts as "
                  "disputed.",
        },
    },
    "term_betreibungskosten": {
        "describe": "who pays the official costs of debt enforcement (Betreibungskosten)",
        "title": {"de": "Betreibungskosten", "en": "Enforcement costs (Betreibungskosten)"},
        "source": ("schkg", "68", "Art. 68 SchKG"),
        "text": {
            "de": "Die amtlichen Kosten der Betreibung, zum Beispiel für den Zahlungsbefehl, "
                  "trägt der Schuldner; der Gläubiger schiesst sie vor. Sie sind geschuldet, "
                  "wenn die betriebene Forderung bestand und nicht bezahlt war. Sie sind "
                  "etwas anderes als die Gebühren eines Inkassobüros.",
            "en": "The official costs of the enforcement, for example for the payment order, "
                  "are borne by the debtor; the creditor advances them. They are owed if the "
                  "claim under enforcement existed and was unpaid. They are something "
                  "different from the fees of a collection agency.",
        },
    },
    "term_forderungsart": {
        "describe": "the difference between a public-law claim (taxes, Serafe, mandatory "
                    "health insurance) and a private claim",
        "title": {"de": "Öffentlich-rechtliche und private Forderung",
                  "en": "Public-law and private claims"},
        "source": ("kvg", "64a", "Art. 64a KVG"),
        "text": {
            "de": "Private Forderungen stammen aus Verträgen, zum Beispiel mit einem Laden, "
                  "einem Telefonanbieter, einem Fitnessstudio oder einer Zusatzversicherung. "
                  "Für sie gilt das Obligationenrecht (OR). Öffentlich-rechtliche "
                  "Forderungen sind zum Beispiel Steuern, Gebühren wie Serafe und die "
                  "Prämien der obligatorischen Krankenversicherung (KVG). Für sie gelten "
                  "besondere Gesetze und Verordnungen. Mahngebühren sind dort oft vorgesehen "
                  "und dann geschuldet.",
            "en": "Private claims come from contracts, for example with a shop, a phone "
                  "provider, a gym or a supplementary insurer. They are governed by the Code "
                  "of Obligations (OR). Public-law claims are, for example, taxes, fees such "
                  "as Serafe, and the premiums of mandatory health insurance (KVG). They are "
                  "governed by special statutes and ordinances. Reminder fees are often "
                  "provided for there and are then owed.",
        },
    },
    "term_hauptforderung": {
        "describe": "the difference between the principal (Hauptforderung) and ancillary "
                    "claims (Nebenforderungen)",
        "title": {"de": "Hauptforderung und Nebenforderungen",
                  "en": "Principal and ancillary claims"},
        "text": {
            "de": "Die Hauptforderung ist der ursprüngliche Preis der Ware oder "
                  "Dienstleistung. Alles, was später dazukommt, ist eine Nebenforderung: "
                  "Zinsen, Mahngebühren, Dossiergebühren. Jede Nebenforderung braucht eine "
                  "eigene rechtliche Grundlage. Es lohnt sich deshalb, nicht nur den "
                  "Gesamtbetrag auf dem Einzahlungsschein anzuschauen.",
            "en": "The principal (Hauptforderung) is the original price of the goods or "
                  "service. Everything added later is an ancillary claim (Nebenforderung): "
                  "interest, reminder fees, dossier fees. Each ancillary claim needs its own "
                  "legal basis. It is therefore worth looking at more than the total on the "
                  "payment slip.",
        },
    },
    "term_faelligkeit_verzug": {
        "describe": "the difference between a bill being due (Fälligkeit) and being in "
                    "default (Verzug)",
        "title": {"de": "Fälligkeit und Verzug", "en": "Due date and default"},
        "source": ("or", "102", "Art. 75 und 102 OR"),
        "text": {
            "de": "Fällig ist eine Rechnung, sobald der Gläubiger die Zahlung verlangen darf. "
                  "Im Verzug ist man erst, wenn man rechtlich zu spät ist. Das ist nicht "
                  "dasselbe: Wer eine fällige Rechnung noch nicht bezahlt hat, ist nicht "
                  "automatisch im Verzug. Dafür braucht es in der Regel eine Mahnung oder "
                  "einen im Vertrag vereinbarten Zahlungstermin. Erst im Verzug können "
                  "Verzugszins und weitere Kosten anfallen.",
            "en": "A bill is due as soon as the creditor may ask for payment. A person is in "
                  "default only once they are legally late. This is not the same: someone "
                  "who has not yet paid a bill that is due is not automatically in default. "
                  "As a rule this needs a reminder or a payment date agreed in the contract. "
                  "Only in default can default interest and further costs arise.",
        },
    },
    "term_verfalltag": {
        "describe": "what an agreed payment date (Verfalltag) is and whether 'payable "
                    "within 30 days' on a bill is one",
        "title": {"de": "Verfalltag (vereinbarter Zahlungstermin)",
                  "en": "Agreed payment date (Verfalltag)"},
        "source": ("or", "102", "Art. 102 Abs. 2 OR"),
        "text": {
            "de": "Haben beide Seiten beim Vertragsabschluss einen bestimmten Zahlungstermin "
                  "vereinbart, zum Beispiel im unterschriebenen Mietvertrag oder bei der "
                  "Online-Bestellung, tritt der Verzug an diesem Tag ohne Mahnung ein. Der "
                  "Aufdruck «zahlbar innert 30 Tagen», der erst auf der Rechnung steht, ist "
                  "einseitig und genügt dafür nicht.",
            "en": "If both sides agreed a specific payment date when the contract was "
                  "concluded, for example in the signed lease or at the online checkout, "
                  "default begins on that day without a reminder. The line 'payable within "
                  "30 days' that appears only on the bill is one-sided and is not enough.",
        },
    },
    "term_zustellung": {
        "describe": "when a reminder takes effect (receipt) and when a bank payment counts "
                    "as made (value date, Valutadatum)",
        "title": {"de": "Zugang der Mahnung und Valutadatum",
                  "en": "Receipt of the reminder and value date"},
        "text": {
            "de": "Eine Mahnung wirkt erst an dem Tag, an dem sie bei Ihnen ankommt, also im "
                  "Briefkasten oder im Posteingang liegt. Das Datum oben im Brief ist nicht "
                  "entscheidend. Umgekehrt gilt eine Banküberweisung nur als rechtzeitig, "
                  "wenn sie bis zum Termin ausgeführt und verbucht ist (Valutadatum). Der "
                  "Tag, an dem Sie den Auftrag im E-Banking erfassen, genügt nicht.",
            "en": "A reminder takes effect only on the day it reaches you, i.e. when it is "
                  "in your letterbox or inbox. The date printed at the top of the letter is "
                  "not decisive. Conversely, a bank transfer is on time only if it is "
                  "executed and booked by the deadline (value date). The day on which you "
                  "enter the order in e-banking is not enough.",
        },
    },
    "term_verjaehrung": {
        "describe": "what the limitation period (Verjährung) is and how long it lasts",
        "title": {"de": "Verjährung", "en": "Limitation period (Verjährung)"},
        "source": ("or", "127", "Art. 127, 128 und 135 OR"),
        "text": {
            "de": "Nach Ablauf der Verjährungsfrist können Sie die Zahlung verweigern; die "
                  "Schuld verschwindet aber nicht von selbst. Die Frist beträgt im "
                  "Allgemeinen zehn Jahre. Fünf Jahre gelten unter anderem für Miete und "
                  "andere wiederkehrende Leistungen (z. B. Abonnemente), für Einkäufe im "
                  "Detailhandel sowie für Handwerks-, Arzt- und Anwaltsrechnungen. Ein "
                  "Zahlungsbefehl unterbricht die Verjährung; die Frist beginnt dann neu.",
            "en": "Once the limitation period has expired, you can refuse payment; but the "
                  "debt does not vanish by itself. The general period is ten years. Five "
                  "years apply, among others, to rent and other recurring payments (e.g. "
                  "subscriptions), retail purchases, and bills of craftsmen, doctors and "
                  "lawyers. A payment order interrupts the limitation period; it then "
                  "starts again.",
        },
    },
    "term_zinseszins": {
        "describe": "whether interest may be charged on default interest (compound "
                    "interest, Zinseszins)",
        "title": {"de": "Zinseszinsverbot", "en": "No interest on default interest"},
        "source": ("or", "105", "Art. 105 Abs. 3 OR"),
        "text": {
            "de": "Auf Verzugszinsen dürfen keine weiteren Verzugszinsen berechnet werden. "
                  "Der Zins wird nur auf der ursprünglichen, noch offenen Rechnung "
                  "(Hauptforderung) berechnet. Das ist zu beachten, wenn ein Inkassobüro "
                  "aufgelaufene Zinsen und Gebühren zu einem neuen «Gesamtsaldo» "
                  "zusammenzählt und darauf wieder Zins verlangt.",
            "en": "No further default interest may be charged on default interest. Interest "
                  "is calculated only on the original unpaid bill (the principal). This "
                  "matters when a collection agency adds accrued interest and fees into a "
                  "new 'total balance' and charges interest on it again.",
        },
    },
    "term_agb": {
        "describe": "what general terms and conditions (AGB) are and when they are binding",
        "title": {"de": "AGB (Allgemeine Geschäftsbedingungen)",
                  "en": "General terms and conditions (AGB)"},
        "source": ("or", "1", "Art. 1 OR"),
        "text": {
            "de": "AGB sind vorformulierte Vertragsbedingungen. Sie gelten nur, wenn Sie "
                  "ihnen vor oder beim Vertragsabschluss zugestimmt haben und sie vorher "
                  "leicht lesen konnten. Dass ein Unternehmen AGB irgendwo auf seiner "
                  "Website hat, genügt nicht. Was zum ersten Mal auf einer Rechnung oder "
                  "Mahnung steht, zum Beispiel «Mahngebühr CHF 20», ist nicht vereinbart.",
            "en": "General terms and conditions (AGB) are pre-formulated contract terms. "
                  "They apply only if you agreed to them before or when concluding the "
                  "contract and could easily read them beforehand. That a company has terms "
                  "somewhere on its website is not enough. Something that appears for the "
                  "first time on a bill or reminder, for example 'reminder fee CHF 20', has "
                  "not been agreed.",
        },
    },
    "term_bestimmtheit": {
        "describe": "whether a fee clause in general terms must state a concrete amount",
        "title": {"de": "Bestimmter Betrag in den AGB",
                  "en": "Concrete amount in the general terms"},
        "text": {
            "de": "Eine Gebührenklausel in den AGB muss einen konkreten, klar erkennbaren "
                  "Betrag nennen, zum Beispiel «CHF 20 pro Mahnung». Ein allgemeiner Satz "
                  "wie «Bei Zahlungsverzug werden Mahn- und Inkassokosten verrechnet» lässt "
                  "den Betrag offen und genügt nicht. Das gilt auch für den Verweis auf die "
                  "Gebührentabelle eines Inkassobüros.",
            "en": "A fee clause in general terms must state a concrete, transparent amount, "
                  "for example 'CHF 20 per reminder'. A general sentence such as 'In the "
                  "event of late payment, reminder and collection costs will be charged' "
                  "leaves the amount open and is not enough. The same applies to a reference "
                  "to a collection agency's fee table.",
        },
    },
    "term_ungewoehnlich": {
        "describe": "whether a customer who accepted general terms is bound by unusual or "
                    "unfair clauses",
        "title": {"de": "Ungewöhnliche und missbräuchliche Klauseln",
                  "en": "Unusual and unfair clauses"},
        "source": ("uwg", "8", "Art. 8 UWG"),
        "text": {
            "de": "Auch wer das Häkchen bei «Ich akzeptiere die AGB» gesetzt hat, ist nicht "
                  "an alles gebunden. Klauseln, mit denen eine vernünftige Kundin oder ein "
                  "vernünftiger Kunde nicht rechnen muss, gelten nicht, zum Beispiel CHF 150 "
                  "Strafe für eine Rechnung von CHF 30. Dasselbe gilt für Klauseln, die "
                  "Konsument:innen in treuwidriger Weise erheblich benachteiligen.",
            "en": "Even someone who ticked 'I accept the terms' is not bound by everything "
                  "in them. Clauses a reasonable customer would not expect do not apply, for "
                  "example a CHF 150 penalty for a CHF 30 bill. The same goes for clauses "
                  "that put consumers at a significant disadvantage contrary to good faith.",
        },
    },
    "term_verzugsschaden": {
        "describe": "what 'Verzugsschaden' (further damage from default, Art. 106 OR) on a "
                    "collection letter means",
        "title": {"de": "Verzugsschaden (Art. 106 OR)",
                  "en": "Damage from default (Verzugsschaden, Art. 106 OR)"},
        "source": ("or", "106", "Art. 106 OR"),
        "text": {
            "de": "Art. 106 OR legt keine pauschale Inkassogebühr fest. Der Artikel sagt nur: "
                  "Ist dem Gläubiger ein Schaden entstanden, der grösser ist als der "
                  "Verzugszins, kann er auch diesen Schaden verlangen. Dafür muss er einen "
                  "konkreten, aussergewöhnlichen Schaden nachweisen. Steht auf einem "
                  "Inkassoschreiben «Verzugsschaden nach Art. 106 OR: CHF 85», heisst das "
                  "also nicht, dass das Gesetz diesen Betrag vorschreibt.",
            "en": "Art. 106 OR does not set a flat collection fee. The article only says: if "
                  "the creditor suffered a loss greater than the default interest, the "
                  "creditor can also claim that loss. For this the creditor must prove a "
                  "concrete, extraordinary loss. If a collection letter says 'Verzugsschaden "
                  "nach Art. 106 OR: CHF 85', this does not mean that the statute prescribes "
                  "that amount.",
        },
    },
    "term_beweislast": {
        "describe": "who has to prove that a collection fee is justified (burden of proof)",
        "title": {"de": "Beweislast", "en": "Burden of proof"},
        "source": ("zgb", "8", "Art. 8 ZGB; Art. 27 Abs. 2 SchKG"),
        "text": {
            "de": "Nicht Sie müssen beweisen, dass eine Inkassogebühr zu hoch ist. Der "
                  "Gläubiger muss mit Belegen nachweisen, welchen konkreten Schaden er über "
                  "die üblichen Mahnungen hinaus hatte. Ein Inkassobüro beizuziehen ist der "
                  "Entscheid des Gläubigers; dessen Pauschalgebühren lassen sich nach der "
                  "Praxis nicht als Verzugsschaden auf den Schuldner überwälzen.",
            "en": "You do not have to prove that a collection fee is too high. The creditor "
                  "must prove with documents what concrete loss it suffered beyond routine "
                  "reminders. Hiring a collection agency is the creditor's own choice; in "
                  "practice its flat fees cannot be passed on to the debtor as damage from "
                  "default.",
        },
    },
    "term_schuldanerkennung": {
        "describe": "what signing an instalment agreement or acknowledgement of debt "
                    "(Schuldanerkennung, Ratenvereinbarung) means",
        "title": {"de": "Schuldanerkennung (z. B. Ratenvereinbarung)",
                  "en": "Acknowledgement of debt (e.g. instalment agreement)"},
        "source": ("schkg", "82", "Art. 82 SchKG"),
        "text": {
            "de": "Wer eine Ratenzahlungsvereinbarung unterschreibt oder im Portal eines "
                  "Inkassobüros «Ratenzahlung beantragen» wählt, anerkennt damit in der "
                  "Regel den ganzen aufgeführten Betrag, auch darin enthaltene Gebühren, die "
                  "sonst nicht geschuldet wären. Mit einer unterschriebenen "
                  "Schuldanerkennung kann der Gläubiger vor Gericht rasch die provisorische "
                  "Rechtsöffnung erhalten.",
            "en": "A person who signs an instalment agreement, or chooses 'request "
                  "instalment plan' in a collection agency's portal, as a rule acknowledges "
                  "the whole amount listed, including fees that would otherwise not be "
                  "owed. With a signed acknowledgement of debt the creditor can quickly "
                  "obtain provisional setting-aside of an objection (provisorische "
                  "Rechtsöffnung) in court.",
        },
    },
    "term_tilgung": {
        "describe": "how a partial payment is credited (interest and costs before the "
                    "principal)",
        "title": {"de": "Anrechnung von Teilzahlungen", "en": "Crediting of partial payments"},
        "source": ("or", "85", "Art. 85 OR"),
        "text": {
            "de": "Wer geschuldete Zinsen oder Kosten offen hat, kann eine Teilzahlung nicht "
                  "einfach auf die Hauptforderung anrechnen: Der Gläubiger darf sie zuerst "
                  "auf Zinsen und Kosten anrechnen. Wer zum Beispiel nur den Rechnungsbetrag "
                  "von CHF 200 zahlt, aber CHF 1.50 Verzugszins schuldet, hat danach noch "
                  "CHF 1.50 der Rechnung offen. Es hilft, im Zahlungszweck anzugeben, wofür "
                  "die Zahlung ist, zum Beispiel «Tilgung Hauptforderung inkl. 5 % "
                  "Verzugszins».",
            "en": "A person who owes interest or costs cannot simply credit a partial "
                  "payment to the principal: the creditor may credit it to interest and "
                  "costs first. Someone who pays only the bill amount of CHF 200 but owes "
                  "CHF 1.50 default interest still has CHF 1.50 of the bill open afterwards. "
                  "It helps to state in the payment reference what the payment is for, for "
                  "example 'Tilgung Hauptforderung inkl. 5 % Verzugszins'.",
        },
    },
    # ---- inheritance: terms of the flow of 2026-11-13 ---------------------------------
    "term_erbenstellung": {
        "describe": "the difference between a statutory heir (gesetzlicher Erbe) and an heir "
                    "appointed by will (eingesetzter Erbe)",
        "title": {"de": "Gesetzliche und eingesetzte Erben", "en": "Statutory and appointed heirs"},
        "source": ("zgb", "567", "Art. 567 ZGB"),
        "text": {
            "de": "Gesetzliche Erben erben, weil das Gesetz es so vorsieht: vor allem Kinder, "
                  "Ehepartner:in, Eltern und Geschwister, wenn es kein Testament gibt. "
                  "Eingesetzte Erben erben, weil ein Testament oder ein Erbvertrag sie nennt. "
                  "Der Unterschied ist für die Frist wichtig: Für gesetzliche Erben beginnt "
                  "sie in der Regel, wenn sie vom Tod erfahren, für eingesetzte Erben mit der "
                  "amtlichen Mitteilung über das Testament.",
            "en": "Statutory heirs inherit because the law provides so: above all children, "
                  "the spouse, parents and siblings, if there is no will. Appointed heirs "
                  "inherit because a will or an inheritance contract names them. The "
                  "difference matters for the period: for statutory heirs it normally starts "
                  "when they learn of the death, for appointed heirs with the official "
                  "notification of the will.",
        },
    },
    "term_zahlungsunfaehig": {
        "describe": "what it means that the deceased was officially or manifestly insolvent "
                    "at death (presumed disclaimer)",
        "title": {"de": "Offenkundige Zahlungsunfähigkeit", "en": "Manifest insolvency"},
        "source": ("zgb", "566", "Art. 566 Abs. 2 ZGB"),
        "text": {
            "de": "War die verstorbene Person beim Tod zahlungsunfähig und war das amtlich "
                  "festgestellt oder offenkundig, zum Beispiel wegen offener Verlustscheine "
                  "oder eines laufenden Konkurses, wird die Ausschlagung von Gesetzes wegen "
                  "vermutet. Die Erben müssen dann nichts erklären. Dass jemand viele "
                  "Schulden hatte, genügt allein nicht.",
            "en": "If the deceased was insolvent at death and this was officially "
                  "established or manifest, for example because of unpaid loss certificates "
                  "or ongoing bankruptcy proceedings, the disclaimer is presumed by law. The "
                  "heirs then do not have to declare anything. That someone had many debts "
                  "is not enough on its own.",
        },
    },
    "term_fristverlaengerung": {
        "describe": "whether the period for disclaiming an inheritance can be extended or "
                    "restored",
        "title": {"de": "Fristverlängerung und neue Frist", "en": "Extension and new period"},
        "source": ("zgb", "576", "Art. 576 ZGB"),
        "text": {
            "de": "Aus wichtigen Gründen kann die zuständige Behörde die Frist für die "
                  "Ausschlagung verlängern oder eine neue Frist ansetzen. Dafür braucht es "
                  "ein Gesuch mit einer Begründung. Wer die Frist ohne Verlängerung "
                  "verstreichen lässt, hat die Erbschaft angenommen.",
            "en": "For important reasons the competent authority can extend the period for "
                  "disclaiming or set a new one. This needs a request with reasons. A person "
                  "who lets the period pass without an extension has accepted the "
                  "inheritance.",
        },
    },
    "term_oeffentliches_inventar": {
        "describe": "what a public inventory (öffentliches Inventar) of an estate is",
        "title": {"de": "Öffentliches Inventar", "en": "Public inventory"},
        "source": ("zgb", "580", "Art. 580 und 588 ZGB"),
        "text": {
            "de": "Beim öffentlichen Inventar stellt die Behörde zusammen, was zum Nachlass "
                  "gehört, und ruft die Gläubiger auf, ihre Forderungen zu melden. Jeder "
                  "Erbe, der noch ausschlagen kann, kann es innert eines Monats verlangen. "
                  "Danach entscheidet er: ausschlagen, amtliche Liquidation verlangen, unter "
                  "öffentlichem Inventar annehmen oder vorbehaltlos annehmen.",
            "en": "For a public inventory the authority lists what belongs to the estate and "
                  "calls on the creditors to report their claims. Any heir who can still "
                  "disclaim can request it within one month. Afterwards the heir decides: "
                  "disclaim, request official liquidation, accept under public inventory, or "
                  "accept without reservation.",
        },
    },
    "term_amtliche_liquidation": {
        "describe": "what official liquidation (amtliche Liquidation) of an estate is",
        "title": {"de": "Amtliche Liquidation", "en": "Official liquidation"},
        "source": ("zgb", "593", "Art. 593 ZGB"),
        "text": {
            "de": "Bei der amtlichen Liquidation wickelt eine Behörde den Nachlass ab: Sie "
                  "zahlt die Schulden aus dem Nachlass. Die Erben haften dann nicht für die "
                  "Schulden. Jeder Erbe kann sie verlangen, statt auszuschlagen; das geht "
                  "aber nicht, solange ein Miterbe die Annahme erklärt.",
            "en": "In an official liquidation an authority winds up the estate: it pays the "
                  "debts from the estate. The heirs are then not liable for the debts. Any "
                  "heir can request it instead of disclaiming; but not as long as a co-heir "
                  "declares acceptance.",
        },
    },
    "term_betreibung": {
        "describe": "what debt enforcement (Betreibung) or the debt enforcement office "
                    "(Betreibungsamt) is",
        "title": {"de": "Betreibung", "en": "Debt enforcement (Betreibung)"},
        "source": ("schkg", "38", "Art. 38 ff. SchKG"),
        "text": {
            "de": "Die Betreibung ist das amtliche Verfahren, mit dem ein Gläubiger in der "
                  "Schweiz eine Geldforderung durchsetzt. Sie läuft über das "
                  "Betreibungsamt. Das Amt prüft zu Beginn nicht, ob die Forderung "
                  "berechtigt ist; dagegen kann sich die betriebene Person mit dem "
                  "Rechtsvorschlag wehren.",
            "en": "Debt enforcement is the official procedure by which a creditor enforces "
                  "a money claim in Switzerland. It runs through the debt enforcement "
                  "office. At the start the office does not check whether the claim is "
                  "justified; the person concerned can defend themselves with an "
                  "objection (Rechtsvorschlag).",
        },
    },
    "term_zahlungsbefehl": {
        "describe": "what a payment order (Zahlungsbefehl) is and how to recognise one",
        "title": {"de": "Zahlungsbefehl", "en": "Payment order (Zahlungsbefehl)"},
        "source": ("schkg", "69", "Art. 69 SchKG"),
        "text": {
            "de": "Der Zahlungsbefehl ist ein amtliches Formular, das nur das Betreibungsamt "
                  "ausstellt. Er eröffnet die Betreibung. Er wird persönlich übergeben, durch "
                  "die Post oder das Betreibungsamt, oder liegt zur Abholung bereit. Er "
                  "fordert dazu auf, die Forderung innert 20 Tagen zu bezahlen, und weist "
                  "darauf hin, dass innert 10 Tagen Rechtsvorschlag erhoben werden kann. Das "
                  "Amt stellt ihn auf Antrag des Gläubigers aus, ohne die Forderung zu "
                  "prüfen. Eine «letzte Mahnung vor Betreibung» oder ein Einzahlungsschein "
                  "eines Inkassobüros ist kein Zahlungsbefehl.",
            "en": "The payment order is an official form that only the debt enforcement "
                  "office issues. It opens the enforcement. It is handed over in person, by "
                  "the post or the office, or is ready for collection. It demands payment "
                  "within 20 days and states that an objection can be raised within 10 "
                  "days. The office issues it at the creditor's request without examining "
                  "the claim. A 'last reminder before enforcement' or a payment slip from a "
                  "collection agency is not a payment order.",
        },
    },
    "term_rechtsvorschlag": {
        "describe": "what an objection to a payment order (Rechtsvorschlag) is",
        "title": {"de": "Rechtsvorschlag", "en": "Objection (Rechtsvorschlag)"},
        "source": ("schkg", "74", "Art. 74, 75 und 78 SchKG"),
        "text": {
            "de": "Mit dem Rechtsvorschlag bestreitet die betriebene Person die Forderung "
                  "oder einen Teil davon. Er ist sofort bei der Übergabe des "
                  "Zahlungsbefehls oder innert 10 Tagen nach der Zustellung mündlich oder "
                  "schriftlich beim Betreibungsamt zu erklären. Eine Begründung ist nicht "
                  "nötig. Der Rechtsvorschlag stoppt die Betreibung, bis der Gläubiger ihn "
                  "beseitigen lässt.",
            "en": "With the objection, the person concerned disputes the claim or part of "
                  "it. It is declared at once when the payment order is handed over, or "
                  "within 10 days of service, orally or in writing, to the debt "
                  "enforcement office. No reasons are needed. The objection stops the "
                  "enforcement until the creditor has it set aside.",
        },
    },
    "term_rechtsoeffnung": {
        "describe": "what setting aside the objection (Rechtsöffnung) is",
        "title": {"de": "Rechtsöffnung", "en": "Setting aside the objection (Rechtsöffnung)"},
        "source": ("schkg", "80", "Art. 80 und 82 SchKG"),
        "text": {
            "de": "Die Rechtsöffnung ist das Gerichtsverfahren, mit dem der Gläubiger einen "
                  "Rechtsvorschlag beseitigen lässt. Er braucht dafür ein Urteil oder eine "
                  "unterschriebene Schuldanerkennung.",
            "en": "Rechtsöffnung is the court procedure by which the creditor has an "
                  "objection set aside. For this the creditor needs a judgment or a "
                  "signed acknowledgement of debt.",
        },
    },
    "term_pfaendung": {
        "describe": "what a seizure or wage seizure (Pfändung, Lohnpfändung) is",
        "title": {"de": "Pfändung", "en": "Seizure (Pfändung)"},
        "source": ("schkg", "93", "Art. 93 SchKG"),
        "text": {
            "de": "Wird die Betreibung fortgesetzt, pfändet das Betreibungsamt Vermögen "
                  "oder Einkommen des Schuldners. Einkommen darf nur gepfändet werden, "
                  "soweit es das Existenzminimum übersteigt.",
            "en": "If the enforcement continues, the debt enforcement office seizes assets "
                  "or income of the debtor. Income may be seized only to the extent that "
                  "it exceeds the subsistence minimum.",
        },
    },
    "term_existenzminimum": {
        "describe": "what the subsistence minimum (Existenzminimum) is",
        "title": {"de": "Existenzminimum", "en": "Subsistence minimum (Existenzminimum)"},
        "source": ("schkg", "93", "Art. 93 und 17 SchKG"),
        "text": {
            "de": "Das betreibungsrechtliche Existenzminimum ist der Betrag, der dem "
                  "Schuldner und seiner Familie zum Leben bleiben muss. Das Betreibungsamt "
                  "legt ihn im Einzelfall fest. Eine Beschwerde gegen die ursprüngliche Verfügung "
                  "ist grundsätzlich innert 10 Tagen ab Kenntnis einzureichen. Bei später "
                  "geänderten Verhältnissen oder Untätigkeit des Amtes gelten andere Regeln.",
            "en": "The subsistence minimum under debt enforcement law is the amount that "
                  "must be left to the debtor and their family to live on. The debt "
                  "enforcement office fixes it case by case. A complaint against the "
                  "original measure is generally filed within 10 days of learning of it. Later "
                  "changed circumstances and failure of the office to act follow different rules.",
        },
    },
    "term_betreibungsregister": {
        "describe": "what the debt enforcement register or an extract from it "
                    "(Betreibungsregister, Betreibungsauszug) is",
        "title": {"de": "Betreibungsregister", "en": "Debt enforcement register"},
        "source": ("schkg", "8a", "Art. 8a SchKG"),
        "text": {
            "de": "Das Betreibungsamt führt ein Register über die Betreibungen. Wer ein "
                  "Interesse glaubhaft macht, zum Beispiel vor einem Vertragsabschluss, "
                  "kann einen Auszug über eine Person verlangen. Einträge sind für Dritte "
                  "grundsätzlich bis fünf Jahre nach Abschluss des Verfahrens sichtbar; Art. 8a "
                  "sieht auch Gründe für eine frühere Nichtbekanntgabe vor. Das ist keine Löschung.",
            "en": "The debt enforcement office keeps a register of enforcement "
                  "proceedings. Anyone who shows a credible interest, for example before "
                  "concluding a contract, can request an extract about a person. Entries "
                  "are visible to third parties until five years after the proceedings "
                  "have ended, subject to statutory grounds for earlier non-disclosure. "
                  "Non-disclosure is not deletion.",
        },
    },
    "term_nichtbekanntgabe": {
        "describe": "what it means that an enforcement is no longer disclosed to third "
                    "parties (Nichtbekanntgabe), and that this is not a deletion",
        "title": {"de": "Nichtbekanntgabe an Dritte", "en": "Non-disclosure to third parties"},
        "source": ("schkg", "8a", "Art. 8a Abs. 3 SchKG"),
        "text": {
            "de": "Nichtbekanntgabe heisst: Das Betreibungsamt zeigt eine Betreibung auf "
                  "Auszügen für Dritte, zum Beispiel für Vermieter, nicht mehr an. Der "
                  "Eintrag wird nicht gelöscht; er bleibt im Register. Das Gesetz nennt die "
                  "Fälle, in denen das gilt.",
            "en": "Non-disclosure means: the debt enforcement office no longer shows an "
                  "enforcement on extracts for third parties, for example landlords. The "
                  "entry is not deleted; it stays in the register. The statute names the "
                  "cases in which this applies.",
        },
    },
    "term_rueckzug": {
        "describe": "what it means that the creditor withdraws an enforcement (Rückzug der "
                    "Betreibung), and that paying is not the same",
        "title": {"de": "Rückzug der Betreibung", "en": "Withdrawal of the enforcement"},
        "source": ("schkg", "8a", "Art. 8a Abs. 3 Bst. c SchKG"),
        "text": {
            "de": "Der Gläubiger kann eine Betreibung beim Betreibungsamt zurückziehen. Sie "
                  "wird Dritten dann nicht mehr bekannt gegeben. Eine Zahlung allein ist "
                  "kein Rückzug: Der Gläubiger muss ihn dem Amt erklären.",
            "en": "The creditor can withdraw an enforcement at the debt enforcement office. "
                  "It is then no longer disclosed to third parties. A payment alone is not "
                  "a withdrawal: the creditor has to declare it to the office.",
        },
    },
    "term_wiederherstellung": {
        "describe": "whether a missed period in debt enforcement can be restored "
                    "(Wiederherstellung der Frist)",
        "title": {"de": "Wiederherstellung der Frist", "en": "Restoration of a period"},
        "source": ("schkg", "33", "Art. 33 Abs. 4 SchKG"),
        "text": {
            "de": "Wer durch ein unverschuldetes Hindernis davon abgehalten wurde, eine "
                  "Frist einzuhalten, kann um Wiederherstellung ersuchen. Das begründete "
                  "Gesuch ist ab dem Wegfall des Hindernisses innert der gleichen Frist "
                  "einzureichen wie die verpasste, und die versäumte Handlung ist "
                  "nachzuholen.",
            "en": "A person who was prevented by an obstacle that was not their fault from "
                  "keeping a period can ask for it to be restored. The request, with "
                  "reasons, has to be filed from the day the obstacle ceased within the "
                  "same period as the one missed, and the missed act has to be made up.",
        },
    },
    "term_verlustschein": {
        "describe": "what a loss certificate (Verlustschein) is",
        "title": {"de": "Verlustschein", "en": "Loss certificate (Verlustschein)"},
        "source": ("schkg", "149", "Art. 149 SchKG"),
        "text": {
            "de": "Reicht das gepfändete Vermögen nicht, um die Forderung zu decken, erhält "
                  "der Gläubiger für den ungedeckten Betrag einen Verlustschein. Die "
                  "Forderung bleibt bestehen.",
            "en": "If the seized assets do not cover the claim, the creditor receives a "
                  "loss certificate for the uncovered amount. The claim continues to exist.",
        },
    },
    "term_ausschlagung": {
        "describe": "what disclaiming an inheritance (Ausschlagung) is",
        "title": {"de": "Ausschlagung", "en": "Disclaimer of an inheritance (Ausschlagung)"},
        "source": ("zgb", "566", "Art. 566, 567 und 570 ZGB"),
        "text": {
            "de": "Mit der Ausschlagung lehnt ein Erbe die Erbschaft ab, mit dem Vermögen "
                  "und den Schulden. Die Frist beträgt drei Monate; für gesetzliche Erben "
                  "beginnt sie in der Regel, sobald sie vom Tod erfahren. Die Ausschlagung "
                  "ist unbedingt und vorbehaltlos bei der zuständigen Behörde zu erklären. "
                  "Für eingesetzte Erben beginnt die Frist mit der amtlichen Mitteilung; "
                  "Inventare und andere Sonderfälle können den Fristlauf ändern.",
            "en": "By disclaiming, an heir refuses the inheritance, with its assets and "
                  "its debts. The period is three months; for statutory heirs it normally "
                  "starts when they learn of the death. The disclaimer is declared to the "
                  "competent authority, unconditionally and without reservations. For appointed "
                  "heirs the period starts with official notification; inventories and other "
                  "special circumstances can change the period.",
        },
    },
    "term_erbschaft_schulden": {
        "describe": "whether and why heirs are liable for the debts of a person who died",
        "title": {"de": "Schulden in der Erbschaft", "en": "Debts in an inheritance"},
        "source": ("zgb", "560", "Art. 560 und 566 ZGB"),
        "text": {
            "de": "Mit dem Tod gehen Vermögen und Schulden der verstorbenen Person auf die "
                  "Erben über; die Erben haften für die Schulden persönlich. Wer das nicht "
                  "will, kann die Erbschaft innert Frist ausschlagen.",
            "en": "On death, the assets and the debts of the deceased pass to the heirs; "
                  "the heirs are personally liable for the debts. An heir who does not "
                  "want this can disclaim the inheritance within the period.",
        },
    },
    "term_einmischung": {
        "describe": "what interference in the estate (Einmischung) means",
        "title": {"de": "Einmischung in die Erbschaft", "en": "Interference in the estate"},
        "source": ("zgb", "571", "Art. 571 Abs. 2 ZGB"),
        "text": {
            "de": "Wer sich als Erbe in die Angelegenheiten der Erbschaft einmischt, mehr "
                  "tut als bloss zu verwalten, oder Nachlassgegenstände an sich nimmt, "
                  "kann die Erbschaft nicht mehr ausschlagen. Was als Einmischung gilt, "
                  "hängt vom Einzelfall ab.",
            "en": "An heir who interferes in the affairs of the estate, does more than "
                  "merely administer it, or takes estate assets, can no longer disclaim "
                  "the inheritance. What counts as interference depends on the individual "
                  "case.",
        },
    },
}

# Topics that have no stored text; the reply is built from the state of the case.
SPECIAL_TOPICS = {
    "own_case": "the user asks what applies in their own case or what they should do "
                "(for example 'do I have to pay?')",
    "question_help": "the user does not understand a question the system asked, or asks "
                     "why it is asked",
    "other": "any other question",
}

TOPICS = {**{k: v["describe"] for k, v in ENTRIES.items()}, **SPECIAL_TOPICS}

# Base addresses of the three statutes on Fedlex, for the link under a term.
_FEDLEX = {
    "schkg": "https://www.fedlex.admin.ch/eli/cc/11/529_488_529/{lang}#art_{art}",
    "or": "https://www.fedlex.admin.ch/eli/cc/27/317_321_377/{lang}#art_{art}",
    "zgb": "https://www.fedlex.admin.ch/eli/cc/24/233_245_233/{lang}#art_{art}",
    "uwg": "https://www.fedlex.admin.ch/eli/cc/1988/223_223_223/{lang}#art_{art}",
    "kvg": "https://www.fedlex.admin.ch/eli/cc/1995/1328_1328_1328/{lang}#art_{art}",
    "elg": "https://www.fedlex.admin.ch/eli/cc/2007/804/{lang}#art_{art}",
    "gebv": "https://www.fedlex.admin.ch/eli/cc/1996/2937_2937_2937/{lang}#art_{art}",
}


def fedlex_url(law: str, art: str, lang: str) -> str:
    """Address of one article on Fedlex. Fedlex writes article 8a as "art_8_a"."""
    return _FEDLEX[law].format(lang=lang, art=re.sub(r"(\d+)([a-z])$", r"\1_\2", art))


def citation_text(citation: str, lang: str) -> str:
    """The German citation, or its English form."""
    if lang == "en":
        citation = citation.replace(" und ", " and ").replace("Abs.", "para.")
    return citation


def answer(topic: str, lang: str) -> dict | None:
    """The stored answer for a topic, or None for special and unknown topics."""
    e = ENTRIES.get(topic)
    if e is None:
        return None
    out = {"topic": topic, "title": e["title"][lang], "text": e["text"][lang],
           "kind": "term" if topic.startswith("term_") else "service"}
    if "source" in e:
        law, art, citation = e["source"]
        out["citation"] = citation_text(citation, lang)
        out["url"] = fedlex_url(law, art, lang)
    return out


def terms(names, lang: str) -> list[dict]:
    """The explanations of the terms that appear in a question or a result."""
    return [a for a in (answer(n, lang) for n in names) if a]
