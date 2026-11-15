"""All fixed user-facing texts, German and English.

Wording follows the public LexTec website: formal address ("Sie"), short
plain sentences, inclusive forms with a colon ("Rechtsberater:in"), Swiss
spelling. The AI system speaks as "ich"; humans are "unser Team" or
"Rechtsberater:in von LexTec", so that it stays clear who is who.

DRAFTS: the disclosure and the messages are to be reviewed and finalised by
the legal lead (sub-challenge 2, user-facing disclosure).
"""

# The disclosure in parts, so that the command line and the web page show the
# same content from one source.
DISCLOSURE_PARTS = {
    "de": {
        "welcome": "Schön, dass Sie sich melden. Geldsorgen und amtliche Schreiben sind "
                   "belastend, und viele Menschen warten zu lange, bevor sie Hilfe suchen.",
        "topics_title": "Wobei wir helfen",
        "topics": [
            ("Rechnungen, Mahnungen und Inkassogebühren",
             "wenn Sie Zusatzkosten für nicht gerechtfertigt halten"),
            ("Zahlungsbefehle und Betreibungen",
             "wenn das Betreibungsamt Ihnen ein Schreiben zugestellt hat"),
            ("Schulden einer verstorbenen Person",
             "wenn eine Erbschaft vor allem aus Schulden besteht"),
            ("Einträge im Betreibungsregister",
             "wenn ein Eintrag Sie bei Wohnung oder Vertrag behindert"),
        ],
        "other": "Bei anderen Themen (z. B. Lohnpfändung, Miete, Arbeit, Familie, Strafsachen, "
                 "Migration) "
                 "schlagen wir Ihnen direkt die Übergabe an eine:n Rechtsberater:in vor.",
        "know_title": "Was Sie wissen sollten",
        "know": [
            "Sie schreiben mit einem KI-System, nicht mit einem Menschen.",
            "Das System fragt nach, statt etwas anzunehmen, und gibt Ihnen eine allgemeine "
            "rechtliche Einordnung. Das ist keine Rechtsberatung im Einzelfall.",
            "Wenn eine Frist drängt, wichtige Angaben fehlen oder Ihr Fall heikel ist, "
            "schlägt das System vor, ihn mit einer Zusammenfassung an eine:n "
            "Rechtsberater:in von LexTec zu übergeben. Übergeben wird nur mit Ihrer "
            "Zustimmung.",
            "Das Gespräch begründet kein Mandat und wahrt keine Fristen.",
            "Ihre Nachrichten werden zur Verarbeitung an einen externen KI-Dienst übermittelt.",
        ],
        "emergency": "In einem Notfall: Polizei 117, Sanität 144, Dargebotene Hand 143.",
    },
    "en": {
        "welcome": "It is good that you got in touch. Money worries and official letters are "
                   "stressful, and many people wait too long before looking for help.",
        "topics_title": "What we help with",
        "topics": [
            ("Bills, reminders and collection fees",
             "when you think additional charges are not justified"),
            ("Payment orders and debt enforcement",
             "when the debt enforcement office has served you a document"),
            ("Debts of a person who has died",
             "when an inheritance consists mainly of debts"),
            ("Entries in the debt enforcement register",
             "when an entry stands in the way of a flat or a contract"),
        ],
        "other": "For other topics (e.g. seizure of wages, tenancy, employment, family, "
                 "criminal matters, migration) we suggest the hand-over to a legal advisor "
                 "straight away.",
        "know_title": "What you should know",
        "know": [
            "You are writing with an AI system, not with a human.",
            "The system asks instead of assuming, and gives you a general legal "
            "classification. This is not legal advice on your individual case.",
            "If a deadline is pressing, important information is missing or your case is "
            "delicate, the system suggests handing it to a legal advisor at LexTec together "
            "with a summary. Nothing is handed over without your agreement.",
            "The conversation does not establish a mandate and does not preserve any deadlines.",
            "Your messages are sent to an external AI service for processing.",
        ],
        "emergency": "In an emergency: police 117, ambulance 144, helpline 143 "
                     "(Dargebotene Hand).",
    },
}


def _disclosure_text(p: dict) -> str:
    lines = [p["welcome"], "", p["topics_title"] + ":"]
    lines += [f"- {title} ({sub})" for title, sub in p["topics"]]
    lines += [p["other"], "", p["know_title"] + ":"]
    lines += [f"- {k}" for k in p["know"]]
    lines += [f"- {p['emergency']}"]
    return "\n".join(lines)


DISCLOSURE = {lang: _disclosure_text(p) for lang, p in DISCLOSURE_PARTS.items()}

CONSENT_QUESTION = {
    "de": ("Eine Frage vorab: Darf ich Ihre Nachrichten zusätzlich auf Anzeichen einer "
           "starken seelischen Belastung prüfen und Sie in diesem Fall an eine Person bei "
           "LexTec verweisen? Das ist freiwillig; ohne Ihre Zustimmung findet diese Prüfung "
           "nicht statt. (ja/nein)"),
    "en": ("One question first: may I also check your messages for signs of severe emotional "
           "distress and, if I find any, refer you to a person at LexTec? This is voluntary; "
           "without your consent this check does not take place. (yes/no)"),
}

# The same question as a tick box on the web page.
CONSENT_LABEL = {
    "de": "Das System darf meine Nachrichten zusätzlich auf Anzeichen einer starken "
          "seelischen Belastung prüfen und mich in diesem Fall an eine Person bei LexTec "
          "verweisen. Freiwillig – ohne Zustimmung findet diese Prüfung nicht statt.",
    "en": "The system may also check my messages for signs of severe emotional distress "
          "and, if it finds any, refer me to a person at LexTec. Voluntary – without "
          "consent this check does not take place.",
}

CONSENT_ACK = {
    True: {"de": "Danke, die Prüfung ist eingeschaltet.",
           "en": "Thank you, the check is switched on."},
    False: {"de": "In Ordnung, die Prüfung bleibt ausgeschaltet.",
            "en": "All right, the check stays switched off."},
}

START_PROMPT = {
    "de": ("Bitte beschreiben Sie jetzt in Ihren eigenen Worten, was passiert ist: Welches "
           "Schreiben oder welche Forderung haben Sie erhalten, von wem und wann? Sie müssen "
           "nichts Juristisches wissen – ich frage nach, wenn mir etwas fehlt."),
    "en": ("Please describe in your own words what happened: which letter or claim did you "
           "receive, from whom, and when? You do not need any legal knowledge – I will ask if "
           "something is missing."),
}
EXIT_HINT = {"de": "(Zum Beenden «exit» eingeben.)", "en": "(Type 'exit' to end.)"}

AREA_QUESTION = {
    "de": "Worum geht es genau? Bitte beschreiben Sie kurz, was passiert ist und welches "
          "Schreiben oder welche Forderung Sie erhalten haben.",
    "en": "What exactly is this about? Please describe briefly what happened and which "
          "letter or claim you received.",
}
AREA_WHY = {
    "de": "Ich muss zuerst verstehen, um welches Thema es geht, damit ich Ihnen die "
          "richtigen Fragen stelle und nichts Falsches annehme.",
    "en": "I first need to understand what the matter is about, so that I ask you the right "
          "questions and do not assume anything wrong.",
}

CONTRADICTION_QUESTION = {
    "de": "Zwei Ihrer Angaben passen für mich nicht zusammen: {items}. Was trifft zu?",
    "en": "Two of your statements do not fit together for me: {items}. Which one is correct?",
}
CONTRADICTION_WHY = {
    "de": "Das kann leicht passieren. Ich frage nach, weil die Einordnung davon abhängt, "
          "welche Angabe stimmt.",
    "en": "This happens easily. I am asking because the classification depends on which "
          "statement is right.",
}

# Fallback acknowledgement if no model-written one is available.
ACK_FALLBACK = {
    "de": "Danke für Ihre Angaben.",
    "en": "Thank you for the information.",
}

ASK_INTRO = {
    "de": "Damit ich nichts annehmen muss, was vielleicht nicht stimmt, habe ich noch "
          "{n} an Sie. Wenn Sie etwas nicht wissen, schreiben Sie das einfach – auch das "
          "hilft weiter.",
    "en": "So that I do not have to assume anything that may be wrong, I have {n} for you. "
          "If you do not know something, just say so – that helps too.",
}
ASK_COUNT = {
    "de": {1: "eine Frage", 2: "zwei Fragen", 3: "drei Fragen"},
    "en": {1: "one question", 2: "two questions", 3: "three questions"},
}
WHY_LABEL = {"de": "Warum ich das frage:", "en": "Why I am asking:"}

# ---- hand-over: proposed by the system, carried out only with the user's agreement ----

HANDOVER_OFFER = {
    "de": "Ich schlage vor, Ihr Anliegen an eine:n Rechtsberater:in von LexTec zu übergeben.",
    "en": "I suggest handing your matter to a legal advisor at LexTec.",
}
HANDOVER_OFFER_ON_REQUEST = {
    "de": "Gerne übergebe ich Ihr Anliegen an eine:n Rechtsberater:in von LexTec.",
    "en": "I will gladly hand your matter to a legal advisor at LexTec.",
}
HANDOVER_OFFER_AGAIN = {
    "de": "Ich kann Ihr Anliegen weiterhin nicht selbst einordnen. Mein Vorschlag bleibt, es "
          "an eine:n Rechtsberater:in von LexTec zu übergeben.",
    "en": "I still cannot classify your matter myself. My suggestion remains to hand it to "
          "a legal advisor at LexTec.",
}
HANDOVER_SENT_NOTE = {
    "de": "Wenn Sie zustimmen, erhält unser Team eine Zusammenfassung dieses Gesprächs mit "
          "Ihren Nachrichten sowie Ihren Namen und Ihre E-Mail-Adresse, damit Sie nicht "
          "alles noch einmal erklären müssen. Ohne Ihre Zustimmung gebe ich nichts weiter.",
    "en": "If you agree, our team receives a summary of this conversation including your "
          "messages, together with your name and e-mail address, so that you do not have "
          "to explain everything again. Without your agreement I pass nothing on.",
}
HANDOVER_QUESTION = {"de": "Darf ich Ihr Anliegen übergeben?",
                     "en": "May I hand your matter over?"}
HANDOVER_TYPE_HINT = {"de": "(Bitte antworten Sie mit «ja» oder «nein».)",
                      "en": "(Please answer 'yes' or 'no'.)"}
HANDOVER_YES = {"de": "Ja, bitte übergeben", "en": "Yes, please hand it over"}
HANDOVER_NO = {"de": "Nein, nichts weitergeben", "en": "No, do not pass anything on"}
# What the user "says" by pressing one of the two buttons.
HANDOVER_YES_SAID = {"de": "Ja, bitte übergeben. (Schaltfläche gedrückt)",
                     "en": "Yes, please hand it over. (Button pressed)"}
HANDOVER_NO_SAID = {"de": "Nein, bitte nichts weitergeben. (Schaltfläche gedrückt)",
                    "en": "No, please do not pass anything on. (Button pressed)"}
# Who the person is and how our team reaches them (contact.py). First name, surname and
# e-mail address are required, the phone number is optional (decided by the legal lead
# on 2026-11-15). These details go into the briefing only, never into a model prompt.
CONTACT_TITLE = {"de": "Ihre Angaben für unser Team", "en": "Your details for our team"}
CONTACT_FIELD_LABELS = {
    "first_name": {"de": "Vorname", "en": "First name"},
    "last_name": {"de": "Nachname", "en": "Surname"},
    "email": {"de": "E-Mail-Adresse", "en": "E-mail address"},
    "phone": {"de": "Telefon (freiwillig)", "en": "Phone (optional)"},
}
CONTACT_NOTE = {
    "de": "Vorname, Nachname und E-Mail-Adresse brauche ich für die Übergabe: Unser Team "
          "muss wissen, mit wem es spricht, und meldet sich per E-Mail. Diese Angaben gehen "
          "nur an unser Team, nicht an den KI-Dienst.",
    "en": "I need your first name, surname and e-mail address for the hand-over: our team "
          "has to know whom it is talking to, and it replies by e-mail. These details go "
          "only to our team, not to the AI service.",
}
CONTACT_ERRORS = {
    "first_name": {"de": "Bitte geben Sie Ihren Vornamen an.",
                   "en": "Please enter your first name."},
    "last_name": {"de": "Bitte geben Sie Ihren Nachnamen an.",
                  "en": "Please enter your surname."},
    "email": {"de": "Bitte geben Sie eine gültige E-Mail-Adresse an.",
              "en": "Please enter a valid e-mail address."},
}
# The person said yes, but a required detail is missing or unusable. Nothing is sent.
CONTACT_REQUIRED = {
    "de": "Danke für Ihre Zustimmung. Ich habe noch nichts weitergegeben, weil mir für die "
          "Übergabe noch etwas fehlt:",
    "en": "Thank you for agreeing. I have not passed anything on yet, because I still need "
          "something for the hand-over:",
}
CONTACT_SUBMIT = {"de": "Angaben senden und übergeben", "en": "Send details and hand over"}

# The address LexTec shows on its public website (lextec-rechtsberatung.ch, read on
# 2026-11-15). To be confirmed by LexTec.
LEXTEC_CONTACT_EMAIL = "info@lextec.ch"

# After the user agreed.
REFER_MESSAGE = {
    "de": "Danke. Ich habe Ihr Anliegen an eine:n Rechtsberater:in von LexTec übergeben. "
          "Unser Team hat eine Zusammenfassung dieses Gesprächs erhalten und meldet sich "
          "per E-Mail bei Ihnen.",
    "en": "Thank you. I have handed your matter to a legal advisor at LexTec. Our team has "
          "received a summary of this conversation and will get in touch with you by "
          "e-mail.",
}
CASE_NUMBER_LABEL = {"de": "Ihre Fallnummer", "en": "Your case number"}
CASE_NUMBER_NOTE = {
    "de": "Bitte notieren Sie diese Nummer. Wenn Sie nachfragen möchten, zum Beispiel weil "
          "Sie länger nichts hören, nennen Sie sie LexTec ({email}). Eine feste Antwortzeit "
          "nennt LexTec auf der Website nicht.",
    "en": "Please note this number. If you want to ask about your matter, for example "
          "because you have not heard back for some time, quote it to LexTec ({email}). "
          "LexTec's website does not state a fixed response time.",
}

# After the user declined.
HANDOVER_DECLINED = {
    "de": "In Ordnung, ich habe nichts weitergegeben. Eine rechtliche Einordnung kann ich "
          "Ihnen in dieser Situation nicht selbst geben, weil ich dafür etwas annehmen "
          "müsste. Sie können es sich jederzeit anders überlegen: Schreiben Sie mir dann "
          "einfach, dass Sie die Übergabe wünschen. Wenn Sie etwas ergänzen oder "
          "korrigieren möchten, schreiben Sie es mir.",
    "en": "All right, I have not passed anything on. I cannot give you a legal "
          "classification myself in this situation, because I would have to assume things. "
          "You can change your mind at any time: just write to me that you would like the "
          "hand-over. If you want to add or correct something, tell me.",
}
HANDOVER_DECLINED_DEADLINE = {
    "de": "Wichtig: Nach Ihren Angaben könnte die Frist für «{label}» am {date} ablaufen "
          "oder bereits abgelaufen sein. Das ist eine vorsichtige Berechnung. Bitte warten "
          "Sie nicht zu und wenden Sie sich rasch an eine Rechtsberatungsstelle oder an das "
          "zuständige Amt.",
    "en": "Important: according to what you told me, the deadline for '{label}' may end on "
          "{date} or may already have passed. This is a cautious calculation. Please do "
          "not wait; contact a legal advice service or the competent office quickly.",
}

# ---- answers to questions the user asks (texts for the topics: knowledge.py) ----------

ANSWER_TERM_NOTE = {
    "de": "Das ist eine allgemeine Erklärung, noch keine Einschätzung Ihres Falls.",
    "en": "This is a general explanation, not yet an assessment of your case.",
}
ANSWER_DEFAULT_TITLE = {"de": "Zu Ihrer Frage", "en": "About your question"}
ANSWER_OWN_CASE = {
    "ASK": {
        "de": "Was in Ihrem Fall gilt, kann ich noch nicht sagen: Dafür fehlen mir noch "
              "Angaben, nach denen ich unten frage. Sobald ich sie habe, erhalten Sie eine "
              "allgemeine Einordnung, oder ich schlage Ihnen die Übergabe an unser Team vor.",
        "en": "I cannot yet tell you what applies in your case: I still need the "
              "information I ask for below. Once I have it, you receive a general "
              "classification, or I suggest the hand-over to our team.",
    },
    "REFER": {
        "de": "Was in Ihrem Fall gilt, kann ich nicht selbst beantworten. Den Grund lesen "
              "Sie unten.",
        "en": "I cannot answer myself what applies in your case. You find the reason below.",
    },
}
ANSWER_QUESTION_HELP = {
    "de": "Wenn eine meiner Fragen unklar ist: Antworten Sie in Ihren eigenen Worten mit "
          "dem, was Sie wissen. «Das weiss ich nicht» ist auch eine Antwort. Unter jeder "
          "Frage steht, warum ich sie stelle. Bei Fragen mit einer Auswahlliste sind die "
          "Begriffe unter der Frage erklärt.",
    "en": "If one of my questions is unclear: answer in your own words with what you know. "
          "'I do not know' is an answer too. Under each question you find why I ask it. For "
          "questions with a list of answers, the terms are explained under the question.",
}
ANSWER_OTHER = {
    "de": "Diese Frage kann ich leider nicht beantworten. Was ich kann:",
    "en": "Unfortunately I cannot answer this question. What I can do:",
}
# Used instead of the acknowledgement when the user's message was only a question.
ASK_INTRO_AFTER_ANSWER = {
    "de": "Damit ich Ihnen weiterhelfen kann, habe ich {n} an Sie. Wenn Sie etwas nicht "
          "wissen, schreiben Sie das einfach – auch das hilft weiter.",
    "en": "So that I can help you further, I have {n} for you. If you do not know "
          "something, just say so – that helps too.",
}

REFER_WHY_LABEL = {"de": "Der Grund dafür:", "en": "The reason:"}

# What the user "says" by pressing the button for a human on the web page.
HUMAN_BUTTON = {
    "de": "Ich möchte mit einer Rechtsberaterin oder einem Rechtsberater sprechen. "
          "(Schaltfläche gedrückt)",
    "en": "I would like to speak to a legal advisor. (Button pressed)",
}

# Plain-language reason per rule (matched by rule identifier or its prefix).
REFER_WHY = {
    "R0": {"de": "Bei der Verarbeitung ist ein technisches Problem aufgetreten. Ich möchte "
                 "nicht riskieren, Ihnen etwas Falsches zu sagen.",
           "en": "A technical problem occurred during processing. I do not want to risk "
                 "telling you something wrong."},
    "R1": {"de": "Sie möchten mit einem Menschen sprechen.",
           "en": "You would like to speak to a human."},
    "R2": {"de": "Aus Ihren Nachrichten lese ich, dass Sie die Situation sehr belastet. Mir "
                 "ist wichtig, dass sich ein Mensch um Sie kümmert.",
           "en": "From your messages I understand that the situation weighs heavily on you. "
                 "It matters to me that a human looks after you."},
    "R3": {"de": "Ihr Anliegen betrifft ein Thema, das ich nicht abdecke.",
           "en": "Your matter concerns a topic I do not cover."},
    "R4": {"de": "In Ihrem Fall könnte eine Frist bald ablaufen oder bereits abgelaufen "
                 "sein. Ich würde Ihren Fall deshalb als dringend markieren.",
           "en": "A deadline in your case may end soon or may already have passed. I would "
                 "therefore mark your case as urgent."},
    "R5-enforcement-office": {
        "de": "Sie haben ein Schreiben des Betreibungsamts erhalten. Dabei kann eine kurze "
              "Frist laufen. Ich würde Ihren Fall deshalb als dringend markieren.",
        "en": "You have received a document from the debt enforcement office. A short "
              "period may be running. I would therefore mark your case as urgent."},
    "R5-advanced-proceedings": {
        "de": "Das Verfahren ist bereits fortgeschritten; das sollte ein:e Rechtsberater:in "
              "anschauen.",
        "en": "The proceedings are already at an advanced stage; a legal advisor should "
              "look at this."},
    "R5-estate-actions": {
        "de": "Sie haben etwas mit dem Nachlass gemacht, das über das Nötigste hinausgehen "
              "kann. Wer Nachlassgegenstände an sich nimmt oder mehr tut als bloss zu "
              "verwalten, kann die Erbschaft nicht mehr ausschlagen und haftet dann selbst "
              "für die Schulden. Ob das bei Ihnen zutrifft, hängt vom Einzelfall ab; das "
              "sollte ein:e Rechtsberater:in beurteilen. Nehmen oder verändern Sie bis "
              "dahin nichts weiter.",
        "en": "You did something with the estate that can go beyond what was necessary. A "
              "person who takes estate assets or does more than merely administer can no "
              "longer disclaim the inheritance and is then personally liable for the "
              "debts. Whether this applies to you depends on the individual case; a legal "
              "advisor should assess it. Until then, take or change nothing further."},
    "R4-disclaimer-passed": {
        "de": "Nach Ihren Angaben könnte die Frist von drei Monaten für die Ausschlagung "
              "abgelaufen sein. Dann bleibt ein Gesuch um Fristverlängerung oder eine neue "
              "Frist aus wichtigen Gründen; es ist sofort bei der zuständigen Behörde zu "
              "stellen und zu begründen. Dabei kann Sie ein:e Rechtsberater:in "
              "unterstützen. Warten Sie mit dem Gesuch nicht auf eine Rückmeldung.",
        "en": "According to your answers the three-month period for disclaiming may have "
              "passed. What remains is a request for an extension or a new period for "
              "important reasons; it has to be made at once to the competent authority, "
              "with reasons. A legal advisor can support you with it. Do not wait for a "
              "reply before making the request."},
    "R5-private-credit-agency": {
        "de": "Der Eintrag liegt bei einer privaten Auskunftei, nicht im Betreibungsregister. "
              "Dafür gelten andere Regeln, vor allem das Datenschutzrecht. Das kann ich mit "
              "den gespeicherten Quellen noch nicht prüfen; ein:e Rechtsberater:in kann das.",
        "en": "The entry is held by a private credit agency, not in the debt enforcement "
              "register. Other rules apply to it, above all data protection law. I cannot "
              "check this with the stored sources yet; a legal advisor can."},
    "R5-register-court": {
        "de": "Nach Ihren Angaben führt der Weg zu einem Eintrag, den Dritte nicht mehr "
              "sehen, über ein Gericht oder die Aufsichtsbehörde, oder es läuft bereits ein "
              "Gerichtsverfahren. Dort gelten Fristen und Formen, und es kommt auf die "
              "Unterlagen an. Dabei kann Sie ein:e Rechtsberater:in unterstützen.",
        "en": "According to your answers the way to an entry that third parties no longer "
              "see leads through a court or the supervisory authority, or court proceedings "
              "are already running. Periods and formal rules apply there, and it depends on "
              "the documents. A legal advisor can support you with this."},
    "R5-high-amount": {
        "de": "Bei diesem Betrag steht für Sie viel auf dem Spiel; das sollte ein:e "
              "Rechtsberater:in prüfen.",
        "en": "With this amount a lot is at stake for you; a legal advisor should review it."},
    "R6": {"de": "Eine Angabe, von der viel abhängt, liess sich im Gespräch nicht klären. "
                 "Ich möchte an dieser Stelle nichts annehmen.",
           "en": "A piece of information on which a lot depends could not be clarified in "
                 "this conversation. I do not want to assume anything here."},
    "R7": {"de": "Ich konnte nicht sicher erkennen, um welches rechtliche Thema es geht.",
           "en": "I could not reliably identify which legal topic this is about."},
    "R8": {"de": "Mit meinen Rückfragen kommen wir gerade nicht weiter. Ein Gespräch mit "
                 "einem Menschen ist dann der bessere Weg.",
           "en": "My follow-up questions are not getting us further. Talking to a human is "
                 "then the better way."},
    "R9": {"de": "Wir haben schon viele Rückfragen geklärt; den Rest bespricht besser ein:e "
                 "Rechtsberater:in mit Ihnen.",
           "en": "We have already been through many questions; the rest is better discussed "
                 "with a legal advisor."},
    "R10": {"de": "Einige Angaben widersprechen sich und liessen sich nicht klären.",
            "en": "Some statements contradict each other and could not be clarified."},
    "R12": {"de": "Solche Fragen prüft bei uns immer ein Mensch, weil es auf den Einzelfall "
                  "ankommt. Ihre Angaben habe ich dafür aufgenommen.",
            "en": "Questions of this kind are always reviewed by a human here, because they "
                  "depend on the individual case. I have recorded your information for "
                  "that."},
}

EMERGENCY = {
    "de": "Wenn Sie in einer akuten Krise sind, sind diese Stellen sofort für Sie da: "
          "Dargebotene Hand 143 (rund um die Uhr), Sanität 144, Polizei 117.",
    "en": "If you are in an acute crisis, these services are there for you right away: "
          "helpline 143 (Dargebotene Hand, 24 hours), ambulance 144, police 117.",
}

AFTER_PROCEED = {
    "de": "Mehr als die allgemeine Einordnung oben kann ich zu Ihrem Fall nicht sagen, ohne "
          "etwas anzunehmen. Wenn sich etwas geändert hat oder Sie etwas ergänzen möchten, "
          "schreiben Sie es mir. Wenn Sie Ihren Fall mit einer Rechtsberaterin oder einem "
          "Rechtsberater besprechen möchten, schreiben Sie zum Beispiel: «Ich möchte mit "
          "einer Anwältin sprechen.» Auch allgemeine Fragen zu Begriffen können Sie mir "
          "stellen.",
    "en": "I cannot say more about your case than the general classification above without "
          "assuming things. If something has changed or you want to add something, tell me. "
          "If you would like to discuss your case with a legal advisor, write for example: "
          "'I want to speak to a lawyer.' You can also ask me general questions about terms.",
}

# ---- labels for the web page's view of how the system decided -----------------

ROUTE_LABELS = {
    "ASK": {"de": "Rückfragen", "en": "Follow-up questions"},
    "PROCEED": {"de": "Einordnung durch das System", "en": "Classification by the system"},
    "REFER": {"de": "Übergabe an Rechtsberater:in", "en": "Handed to a legal advisor"},
}
# While the hand-over waits for the user's agreement, or after the user declined.
HANDOVER_STATE_LABELS = {
    "offered": {"de": "Übergabe vorgeschlagen", "en": "Hand-over proposed"},
    "declined": {"de": "Übergabe abgelehnt", "en": "Hand-over declined"},
}

RULE_LABELS = {
    "R0": {"de": "Technischer Fehler – sicherheitshalber Übergabe",
           "en": "Technical failure – handed over to be safe"},
    "R1": {"de": "Wunsch nach einem Menschen", "en": "Request for a human"},
    "R2": {"de": "Anzeichen starker Belastung", "en": "Signs of severe distress"},
    "R3": {"de": "Thema ausserhalb des abgedeckten Bereichs",
           "en": "Topic outside the covered scope"},
    "R4": {"de": "Frist läuft bald ab oder ist möglicherweise abgelaufen",
           "en": "Deadline close or possibly passed"},
    "R5-enforcement-office": {"de": "Schreiben des Betreibungsamts",
                              "en": "Document from the debt enforcement office"},
    "R5-advanced-proceedings": {"de": "Verfahren bereits fortgeschritten",
                                "en": "Proceedings at an advanced stage"},
    "R5-estate-actions": {"de": "Umgang mit dem Nachlass: mögliche Einmischung",
                          "en": "Dealings with the estate: possible interference"},
    "R4-disclaimer-passed": {"de": "Ausschlagungsfrist möglicherweise abgelaufen",
                             "en": "Disclaimer period possibly passed"},
    "U2": {"de": "Ausschlagungsfrist: dringender Hinweis, Gespräch läuft weiter",
           "en": "Disclaimer period: urgent notice, conversation continues"},
    "R5-private-credit-agency": {"de": "Eintrag bei privater Auskunftei",
                                 "en": "Entry at a private credit agency"},
    "R5-register-court": {"de": "Registereintrag: Weg über Gericht oder Aufsichtsbehörde",
                          "en": "Register entry: way through a court or the supervisory "
                                "authority"},
    "U3": {"de": "Rechtsvorschlag noch möglich: dringender Hinweis, Gespräch läuft weiter",
           "en": "Objection still possible: urgent notice, conversation continues"},
    "R5-high-amount": {"de": "Hoher Betrag", "en": "High amount"},
    "R6": {"de": "Entscheidende Angabe nicht klärbar",
           "en": "Critical fact could not be established"},
    "R7": {"de": "Rechtsgebiet nicht erkennbar", "en": "Legal area not identifiable"},
    "R8": {"de": "Rückfragen ohne Fortschritt", "en": "Questions brought no progress"},
    "R9": {"de": "Höchstzahl an Rückfragerunden erreicht", "en": "Limit of question rounds"},
    "R10": {"de": "Widerspruch nicht klärbar", "en": "Contradiction not resolved"},
    "R12": {"de": "Gebiet wird immer von einem Menschen geprüft",
            "en": "Area always reviewed by a human"},
    "A1": {"de": "Thema noch unklar", "en": "Topic not yet clear"},
    "A2": {"de": "Widersprüchliche Angaben", "en": "Contradictory statements"},
    "A3": {"de": "Nötige Angaben fehlen", "en": "Required facts missing"},
    "P1": {"de": "Alle nötigen Angaben vorhanden, keine Übergaberegel ausgelöst",
           "en": "All required facts established, no escalation rule fired"},
}


def rule_label(rule: str, lang: str) -> str:
    key = rule if rule in RULE_LABELS else rule.split("-")[0]
    return RULE_LABELS.get(key, {}).get(lang, rule)


DEADLINE_LABELS = {
    "objection": {"de": "Rechtsvorschlag gegen den Zahlungsbefehl",
                  "en": "Objection to the payment order (Rechtsvorschlag)"},
    "disclaimer": {"de": "Ausschlagung der Erbschaft",
                   "en": "Disclaimer of the inheritance (Ausschlagung)"},
}

STATUS_LABELS = {
    "missing": {"de": "noch offen", "en": "still open"},
    "user_unknown": {"de": "Ihnen nicht bekannt", "en": "not known to you"},
    "unresolvable": {"de": "liess sich nicht klären", "en": "could not be clarified"},
    "known": {"de": "bekannt", "en": "known"},
}

# Legal prerequisite review is distinct from a finding against the user.
REFER_WHY["R13"] = {"de": "Für diesen Punkt müssen die rechtlichen Voraussetzungen oder amtlichen Unterlagen individuell geprüft werden.", "en": "This point needs individual review of the legal prerequisites or official documents."}
RULE_LABELS["R13"] = {"de": "Individuelle rechtliche Prüfung erforderlich", "en": "Individual legal review needed"}
DEADLINE_LABELS["inventory"] = {"de": "Gesuch um öffentliches Inventar", "en": "Request for a public inventory"}

URGENT_REVIEW_WARNING = {
    "de": "Ihr Anliegen braucht dringende Prüfung. Eine kurze amtliche oder gerichtliche Frist kann laufen oder bereits abgelaufen sein. Warten Sie mit der Klärung bei der zuständigen Stelle oder einer Rechtsberaterin bzw. einem Rechtsberater nicht auf dieses Gespräch. Dieses Gespräch wahrt keine Frist.",
    "en": "Your matter needs urgent review. A short official or court deadline may be running or may already have passed. Do not wait for this conversation to clarify the position with the competent office, court or a legal advisor. This conversation does not preserve any deadline.",
}

# Proactive fixed information: shown independently of hand-over consent.
PAYMENT_NEXT_TITLE = {"de": "Zahlungsbefehl: Was jetzt wichtig ist", "en": "Payment order: what matters now"}
PAYMENT_RECIPIENT = {
    "de": "Wenden Sie sich direkt an das auf Ihrem Zahlungsbefehl genannte Betreibungsamt. Name und Kontakt stehen auf dem Schreiben. Wenn Sie die Forderung bestreiten möchten, können Sie dort Rechtsvorschlag mündlich oder schriftlich erklären. Lassen Sie sich die Erklärung bestätigen.",
    "en": "Contact the debt enforcement office named on your payment order directly; its name and contact details are on the document. If you wish to dispute the claim, you can declare an objection there orally or in writing. Ask for confirmation of your declaration.",
}
PAYMENT_DATE = {
    "de": "Angegebenes Zustelldatum: {received}. Daraus ergibt sich als vorsichtiger Prüfwert für die Rechtsvorschlagsfrist: {due} (Zustellung plus zehn Kalendertage). Das ist keine abschliessend geprüfte Frist: Wochenenden, Feiertage und Sonderregeln sind nicht eingerechnet. Lassen Sie die Frist umgehend anhand des Schreibens prüfen; aus diesem Prüfwert allein folgt nicht, dass sie bereits abgelaufen ist.",
    "en": "Reported service date: {received}. The cautious screening date for the objection period is {due} (service plus ten calendar days). This is not a verified legal deadline: weekends, holidays and special rules have not been applied. Have the period checked promptly against the document; this screening date alone does not establish that the deadline has expired.",
}
PAYMENT_DATE_UNKNOWN = {
    "de": "Das Zustelldatum ist noch nicht geklärt. Deshalb kann ich hier kein Datum nennen. Eine kurze Frist kann bereits laufen; lassen Sie das Schreiben umgehend prüfen. Wenn Sie mir schreiben, an welchem Datum Sie den Zahlungsbefehl erhalten haben, nenne ich einen vorsichtigen Prüfwert für die Frist.",
    "en": "The service date is not yet established, so I cannot give a date here. A short period may already be running; have the document checked promptly. If you tell me on which date you received the payment order, I will give a cautious screening date for the period.",
}
# Late fees, gate 1: what the framework says about a payment order with disputed charges.
PAYMENT_PARTIAL_OBJECTION = {
    "de": "Wer nur einen Teil bestreitet, zum Beispiel nur Gebühren eines Inkassobüros, kann Teil-Rechtsvorschlag erheben. Dabei ist der bestrittene Betrag in Franken genau anzugeben; sonst gilt die ganze Forderung als bestritten.",
    "en": "A person who disputes only part, for example only the fees of a collection agency, can raise a partial objection (Teil-Rechtsvorschlag). The disputed amount in francs must then be stated exactly; otherwise the whole claim counts as disputed.",
}
PAYMENT_OFFICIAL_COSTS = {
    "de": "Die amtlichen Kosten der Betreibung selbst (Art. 68 SchKG) sind geschuldet, wenn die betriebene Forderung bestand und nicht bezahlt war. Sie sind etwas anderes als die Gebühren eines Inkassobüros.",
    "en": "The official costs of the enforcement itself (Art. 68 SchKG) are owed if the claim under enforcement existed and was unpaid. They are something different from the fees of a collection agency.",
}
PAYMENT_REPORTED_ACTION = {
    "de": "Sie haben angegeben, bereits Rechtsvorschlag erhoben zu haben. Ob Zeitpunkt, Empfänger und Umfang passen, ist noch nicht vollständig geklärt. Halten Sie eine Bestätigung bereit und lassen Sie diese Angaben prüfen.",
    "en": "You reported that you have already filed an objection. Its timing, recipient and scope have not yet been fully established. Keep any confirmation available and have these details checked.",
}
PAYMENT_NO_WAIT = {
    "de": "Warten Sie bei einer dringenden Frist nicht auf eine Rückmeldung von LexTec. Für diese Anfrage ist keine Antwortzeit garantiert. Dieses Gespräch und die Übergabe wahren keine Frist und begründen kein Mandat.",
    "en": "Do not wait for a reply from LexTec when a deadline is urgent. No response time is guaranteed for this request. This conversation and the hand-over do not preserve a deadline or establish a mandate.",
}
PAUSE_ACK = {
    "de": "Natürlich. Holen Sie das Schreiben in Ruhe dazu. Die offenen Fragen bleiben bestehen; diese Pause zählt nicht als fehlgeschlagene Antwort.",
    "en": "Of course. Take a moment to get the letter. The open questions remain; this pause does not count as an unsuccessful answer.",
}
CLARIFY_ACK = {
    "de": "Ich konnte noch keine neue Angabe zuordnen. Nehmen Sie zunächst nur die erste Frage unten: Sie können die passende Stelle aus dem Schreiben abschreiben oder sagen, welcher Teil der Frage unklar ist.",
    "en": "I could not identify any new information yet. Start with just the first question below: you can copy the relevant part of the letter or tell me which part of the question is unclear.",
}
RESUME_LABEL = {"de": "Weiter selbst klären", "en": "Continue self-service"}
RETRY_LABEL = {"de": "Verarbeitung erneut versuchen", "en": "Retry processing"}
RECOVERY_HINT = {
    "de": "Sie können Angaben ergänzen oder berichtigen. Mit «Weiter selbst klären» ziehen Sie einen früheren Gesprächswunsch zurück und versuchen die offenen Fragen erneut. Rechtliche Gründe für eine Übergabe werden weiterhin geprüft.",
    "en": "You can add or correct information. Choose 'Continue self-service' to withdraw an earlier request for a human and try the open questions again. Legal reasons for referral will still be checked.",
}
RETRY_HINT = {
    "de": "Die Verarbeitung ist fehlgeschlagen. Ihre bisherigen Angaben bleiben erhalten. Sie können «Verarbeitung erneut versuchen» wählen oder eine neue Nachricht senden; alternativ können Sie die Übergabe an unser Team annehmen.",
    "en": "Processing failed. Your previous information is preserved. Choose 'Retry processing' or send a new message; alternatively, you can accept a hand-over to our team.",
}
DECLINED_CONTINUE = {
    "de": "Ich habe nichts weitergegeben. Sie können weiter Fragen stellen und Angaben ergänzen oder korrigieren. Eine erneute Übergabe können Sie über «Mit einem Menschen sprechen» anfordern.",
    "en": "I have not passed anything on. You can keep asking questions and add or correct information. You can request the hand-over again using 'Speak to a human'.",
}
DELIVERY_GUIDANCE_ERROR = {
    "de": "Die Übergabe konnte nicht bestätigt werden. Die wichtigen Hinweise unten gelten weiterhin. Warten Sie bei einer dringenden Frist nicht auf diese Übergabe.",
    "en": "The hand-over could not be confirmed. The important information below still applies. Do not wait for this hand-over when a deadline is urgent.",
}

# ---- questions answered from a list (web page) -----------------------------------
FORM_UNKNOWN = {"de": "Ich weiss es nicht", "en": "I do not know"}
FORM_PLACEHOLDER = {"de": "Bitte wählen …", "en": "Please choose …"}
FORM_SUBMIT = {"de": "Antworten senden", "en": "Send answers"}
FORM_HINT = {
    "de": "Wählen Sie zu jeder Frage die Antwort, die am besten passt. Sie können "
          "stattdessen auch in eigenen Worten schreiben.",
    "en": "For each question, choose the answer that fits best. You can also write in "
          "your own words instead.",
}
FORM_ACK = {"de": "Danke für Ihre Antworten.", "en": "Thank you for your answers."}
TERMS_LABEL = {"de": "Begriffe einfach erklärt", "en": "Terms explained simply"}
OPTIONS_LABEL = {"de": "Mögliche Antworten:", "en": "Possible answers:"}
SOURCE_LABEL = {"de": "Quelle", "en": "Source"}

# ---- model-led conversation (2026-11-13) ------------------------------------------
REFER_WHY["R14"] = {
    "de": "Ein Teil Ihres Anliegens betrifft ein Thema, das ich mit den hinterlegten Quellen "
          "noch nicht prüfen kann: {topic}. Dazu möchte ich nichts behaupten, was ich nicht "
          "belegen kann. Ein:e Rechtsberater:in von LexTec kann das beurteilen.",
    "en": "Part of your matter concerns a topic I cannot check with the stored sources yet: "
          "{topic}. I do not want to claim anything about it that I cannot back up. A legal "
          "advisor at LexTec can assess it.",
}
RULE_LABELS["R14"] = {"de": "Thema von den hinterlegten Quellen nicht abgedeckt",
                      "en": "Topic not covered by the stored sources"}
RULE_LABELS["U1"] = {"de": "Zahlungsbefehl: dringender Hinweis, Gespräch läuft weiter",
                     "en": "Payment order: urgent notice, conversation continues"}
# What LexTec states on its public website about a consultation. Shown with every
# hand-over proposal. Source: lextec-rechtsberatung.ch, section "Preise und Leistungen"
# and the request form, retrieved on 2026-11-13. DRAFT: to be confirmed by LexTec.
# LexTec's conditions, stated with every hand-over proposal. Sources: the public website
# lextec-rechtsberatung.ch (prices, "kein Mandat", "wahrt keine Rechtsfristen", "melden
# uns per E-Mail") and LexTec's general terms (AGB, "Zuletzt aktualisiert: 2. Februar
# 2026": sections 2, 3 and 4), both read on 2026-11-15. The rules are given by their
# meaning in plain words, not in the wording of the AGB (decided by the legal lead on
# 2026-11-15); the link leads to the full text. To be confirmed by LexTec.
HANDOVER_CONDITIONS_TITLE = {"de": "So arbeitet LexTec", "en": "How LexTec works"}
HANDOVER_CONDITIONS = {
    "de": "Nach den Angaben auf der Website von LexTec (Stand 15.11.2026): Mit Ihrem Ja "
          "geben Sie nur die Zusammenfassung und Ihre Kontaktangaben weiter. Das kostet "
          "nichts und verpflichtet Sie zu nichts. Eine erste Orientierung von 15 Minuten "
          "ist kostenlos. Eine vertiefte Beratung kostet CHF 45 für 30 Minuten oder CHF 85 "
          "für 60 Minuten; zusätzliche Zeit kostet gleich viel. Kosten entstehen erst, wenn "
          "Sie selbst einen solchen Termin buchen.",
    "en": "According to LexTec's website (as of 15.11.2026): with your yes you only pass "
          "on the summary and your contact details. That costs nothing and commits you to "
          "nothing. A first orientation of 15 minutes is free. An in-depth consultation "
          "costs CHF 45 for 30 minutes or CHF 85 for 60 minutes; additional time costs the "
          "same. Costs arise only if you book such an appointment yourself.",
}
HANDOVER_RULES_TITLE = {"de": "Das Wichtigste aus den Bedingungen von LexTec",
                        "en": "The most important points of LexTec's terms"}
HANDOVER_RULES = {
    "de": [
        "Die Übergabe heisst noch nicht, dass LexTec Ihren Fall übernimmt. Sie wahrt keine "
        "Frist: Für Fristen bleiben Sie selbst verantwortlich.",
        "Ein bestätigter Termin ist verbindlich. Ein bezahlter Termin wird nicht "
        "zurückerstattet, auch wenn Sie absagen.",
        "Sie können einen Termin einmal kostenlos verschieben, wenn Sie das mindestens 48 "
        "Stunden vorher per E-Mail melden. Wer ohne Abmeldung nicht erscheint, verliert den "
        "Termin.",
        "Rechnungen sind innert 10 Tagen zu bezahlen. Danach kann LexTec 5 % Zins pro Jahr "
        "und CHF 30 pro Mahnung verlangen.",
        "LexTec ist keine Anwaltskanzlei und vertritt Sie nicht vor Gericht oder Behörden, "
        "ausser das wird ausdrücklich vereinbart. Wenn eine Vertretung vor Gericht nötig "
        "wird, empfiehlt LexTec spezialisierte Kanzleien.",
        "LexTec meldet sich per E-Mail. Eine feste Antwortzeit nennt LexTec nicht.",
    ],
    "en": [
        "The hand-over does not yet mean that LexTec takes on your case. It does not "
        "preserve any deadline: you remain responsible for deadlines yourself.",
        "A confirmed appointment is binding. A paid appointment is not refunded, even if "
        "you cancel.",
        "You can move an appointment once free of charge if you say so by e-mail at least "
        "48 hours before. If you do not show up without cancelling, the appointment is "
        "lost.",
        "Invoices have to be paid within 10 days. After that LexTec can charge 5 % "
        "interest per year and CHF 30 per reminder.",
        "LexTec is not a law firm and does not represent you before courts or "
        "authorities, unless that is expressly agreed. If representation in court becomes "
        "necessary, LexTec recommends specialised law firms.",
        "LexTec replies by e-mail. LexTec does not state a fixed response time.",
    ],
}
HANDOVER_TERMS_URL = "https://lextec-rechtsberatung.ch/datenschutz-agb/"
HANDOVER_TERMS_LABEL = {
    "de": "Vollständige Bedingungen (AGB) und Datenschutzerklärung von LexTec",
    "en": "LexTec's full terms (AGB) and privacy policy, in German",
}
CONFIRM_NOTE = {
    "de": "So habe ich Ihre Nachricht verstanden. Bitte bestätigen Sie die Auswahl oder "
          "ändern Sie sie.",
    "en": "This is how I understood your message. Please confirm the selection or change it.",
}
UNDERSTOOD_LABEL = {"de": "So habe ich Sie verstanden", "en": "This is how I understood you"}
CHANGE_LABEL = {"de": "Ändern", "en": "Change"}
REVISE_SAID = {"de": "Ich möchte eine Angabe ändern: {label}.",
               "en": "I would like to change an answer: {label}."}
REVISE_ACK = {"de": "In Ordnung. Bitte wählen Sie neu.", "en": "All right. Please choose again."}
DECLINED_SHORT = {"de": "In Ordnung, ich habe nichts weitergegeben. Wir machen hier weiter.",
                  "en": "All right, I have not passed anything on. We continue here."}
PAYMENT_CONTINUE = {
    "de": "Ich gehe jetzt mit Ihnen die einzelnen Positionen durch, damit Sie sehen, welche Beträge sich bestreiten lassen.",
    "en": "I will now go through the single charges with you, so that you can see which amounts can be disputed.",
}
SUMMARY_LABEL = {
    "de": "Kurzbeschreibung (vom Sprachmodell aus den Nachrichten der Person verfasst, ungeprüft)",
    "en": "Short description (written by the language model from the person's messages, unverified)",
}

# Shown when a question has to be put again and the model offered no new wording: the
# same words are never repeated without saying why.
REASK = {
    "de": "Ihre Antwort konnte ich noch nicht einordnen. Tippen Sie bitte auf die Antwort, "
          "die am ehesten passt, oder sagen Sie mir, was an der Frage unklar ist.",
    "en": "I could not place your answer yet. Please tap the answer that fits best, or "
          "tell me what is unclear about the question.",
}

# ---- declining an inheritance: urgent notice (shown while the conversation continues) ---
ESTATE_NEXT_TITLE = {"de": "Ausschlagung: Was jetzt wichtig ist", "en": "Disclaimer: what matters now"}
ESTATE_DATE = {
    "de": "Angegebenes Datum: {start}. Daraus ergibt sich als vorsichtiger Prüfwert für das Ende der Ausschlagungsfrist: {due} (drei Monate). Das ist keine abschliessend geprüfte Frist; lassen Sie sie umgehend prüfen.",
    "en": "Date given: {start}. The cautious screening date for the end of the disclaimer period is {due} (three months). This is not a verified legal deadline; have it checked promptly.",
}
ESTATE_PASSED = {
    "de": "Nach diesem Prüfwert könnte die Frist abgelaufen sein. Dann bleibt ein Gesuch um Fristverlängerung oder eine neue Frist aus wichtigen Gründen (Art. 576 ZGB). Stellen Sie es sofort und begründen Sie es.",
    "en": "By this screening date the period may have passed. What remains is a request for an extension or a new period for important reasons (Art. 576 ZGB). Make it at once and give reasons.",
}
ESTATE_WHERE = {
    "de": "Die Ausschlagung und ein solches Gesuch gehen an die zuständige Behörde am letzten Wohnsitz der verstorbenen Person; im Kanton Zürich ist das das Bezirksgericht. Die Ausschlagung können Sie mündlich oder schriftlich erklären, ohne Bedingungen. Lassen Sie sich den Eingang bestätigen.",
    "en": "The disclaimer and such a request go to the competent authority at the last domicile of the deceased; in the Canton of Zurich this is the district court (Bezirksgericht). You can declare the disclaimer orally or in writing, without conditions. Ask for confirmation of receipt.",
}
ESTATE_NO_WAIT = {
    "de": "Warten Sie bei einer dringenden Frist nicht auf eine Rückmeldung von LexTec. Dieses Gespräch und eine Übergabe wahren keine Frist und begründen kein Mandat. Nehmen Sie bis zum Entscheid nichts aus dem Nachlass an sich.",
    "en": "Do not wait for a reply from LexTec when a deadline is urgent. This conversation and a hand-over do not preserve a deadline or establish a mandate. Until you have decided, take nothing from the estate.",
}
ESTATE_CONTINUE = {
    "de": "Ich gehe jetzt mit Ihnen die weiteren Punkte durch.",
    "en": "I will now go through the further points with you.",
}


# ---- register entries: urgent notice while the objection is still possible ---------------
REGISTER_NEXT_TITLE = {"de": "Rechtsvorschlag: Was jetzt wichtig ist",
                       "en": "Objection: what matters now"}
REGISTER_OBJECTION_WHY = {
    "de": "Für Ihren Registereintrag ist der Rechtsvorschlag entscheidend: Nur wer ihn erhoben hat, kann später beim Betreibungsamt verlangen, dass die Betreibung Dritten nicht mehr gezeigt wird.",
    "en": "For your register entry the objection is decisive: only a person who raised it can later ask the debt enforcement office to stop showing the enforcement to third parties.",
}
DEADLINE_LABELS["register_objection"] = {
    "de": "Rechtsvorschlag gegen den Zahlungsbefehl hinter dem Registereintrag",
    "en": "Objection to the payment order behind the register entry"}
