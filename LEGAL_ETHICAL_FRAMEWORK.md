# Legal and Ethical Framework
## LexTec — Decision and Hand-over Layer for Legal AI

**Jurisdiction:** Switzerland, with a focus on the Canton of Zurich  
**Languages:** German and English  
**Date:** 11 November 2026, revised on 15 November 2026 to match the current prototype

## 1. Purpose and legal scope

People often describe legal problems without all the facts that matter. A missing date or an unclear letter can change the next legal step. This is important in debt matters, where short time limits may apply.

Our prototype helps with the first review of a legal question. It collects facts, identifies missing information, and decides when a person should receive human support. It is **not a lawyer** and does not provide legal representation.

The prototype covers three connected areas of Swiss law:

- **Late fees:** additional charges for late payment, such as default interest, reminder fees, and collection costs, including charges in a payment order.
- **Declining an inheritance:** possible debts in an estate, the period for a disclaimer, and the options of an heir.
- **Debt enforcement register entries:** how an entry can be hidden from third parties. For entries at private credit agencies the system proposes a hand-over to a human.

Other areas, such as seizure of wages, criminal, family, tenancy, employment, and migration law, are outside the selected scope. The system proposes a hand-over for these matters **when it identifies them as outside the scope**, and asks no questions about them. This identification is not complete for every possible expression or legal topic.

## 2. Decision rules and escalation

The design separates **fact extraction** from **the decision to continue**. A language model converts the user's words into a structured case record. The Python modules validate parts of that record and look for selected warning signs. The rules in `handover/rules.py` then select one route. The language model does not select the route.

The model also writes the reply to the user's messages. Program code checks that text. A legal statement from the model is shown only if it cites an article that is stored for the legal area and quotes it word for word. The model cannot remove a hand-over proposal or an urgent notice that the rules have set.

| Route | Meaning | Action in the prototype |
|---|---|---|
| `PROCEED` | The required facts are available and no referral rule applies. | Show the result for the legal area. The result consists of fixed texts with statutory references. |
| `ASK` | Important facts are missing, unclear, or contradictory. | Ask one question per message. Where the answers can be listed, the user can tap one. |
| `REFER` | The case presents a defined risk or cannot be handled within the scope. | Propose a hand-over to a human and ask for the user's agreement. Only after a yes is an expert briefing created and saved locally. E-mail delivery is optional. |

`ASK` can be an intermediate step. After the user answers, the rules run again. The case can then move to `PROCEED`, `ASK`, or `REFER`.

### 2.1 When the system refers a case

The following rules are implemented in the prototype:

| Reason for referral | Trigger |
|---|---|
| Model or case-record failure | Extraction fails twice, or a decisive fact cannot be established. |
| User choice | The user asks for human assistance. |
| Psychological distress | The user accepted optional screening and the system detects a warning sign. The case is marked urgent. |
| Legal scope | The system identifies an area outside its scope. |
| Urgent deadline | An estimated deadline has passed or has four working days or fewer remaining, and the required act is not confirmed. Two periods are treated separately, see below. |
| Defined case risks | A seizure notice or court document, action taken with estate assets, a register entry whose remedy leads through a court, a private credit-agency entry, or a claim above CHF 5,000. |
| Topic outside the sources | The language model names a part of the question that the stored legal sources do not cover. |
| Unresolved information | The legal area remains unknown, statements still conflict, or further questions produce no progress. |
| Conversation limit | Twenty-four rounds of questions have been reached. |

**A running period that the user can meet alone is not handed over at once.** For a payment order whose objection period is still running, and for a disclaimer period that ends within ten working days, the user receives an urgent notice with the estimated date and the steps to take, and the conversation continues. A hand-over is proposed only if the period may already have passed. The reason is that a hand-over does not preserve a deadline, while the user can act immediately.

**In some cases the proposal comes together with the answer.** Examples are action taken with estate assets and a register entry whose remedy leads through a court. The user is first told what applies. The hand-over is then proposed once, and the conversation continues if the user declines.

**A hand-over needs the user's agreement.** The rules decide that a case should go to a human. The user decides whether anything is passed on.

The **four-working-day margin** and the **CHF 5,000 threshold** are project rules. They are not limits set by Swiss legislation. The money threshold uses a strict *greater than* test. A claim of exactly CHF 5,000 does not trigger that rule by itself.

These rules reduce unsafe assumptions. They do not prove that the extracted facts are correct. The model can still misunderstand a user's message. The keyword checks also cover only selected words and expressions.

### 2.2 Time limits and legal sources

The prototype estimates three kinds of legal time limit:

- An objection to a payment order: **Art. 74 SchKG**.
- A disclaimer of inheritance: **Art. 567 ZGB**.
- A request for a public inventory: **Art. 580 ZGB**.

It also calculates the first day on which a request for non-disclosure of a register entry is possible (**Art. 8a para. 3 lit. d SchKG**).

The code uses dates taken from the case record. It makes a cautious estimate and does not apply every rule on public holidays, extensions, or debt-enforcement periods. The starting date can also be wrong.

Inheritance needs special care. The three-month period does not start on the same event for every heir. Arts. 567–569 ZGB distinguish several cases. The current program asks how the user became an heir and uses the matching start: knowledge of the death, official notification of the will, or knowledge that the inheritance falls to the user after another heir disclaimed. It does not model every legal exception. For this reason, its date is **not an authoritative legal deadline**.

The result that the user receives on `PROCEED` consists of fixed texts, chosen by program rules. For a legal statement that the model writes in its reply, the code checks that the cited article exists in the local statute collection and that the quoted text appears there. A further model check assesses whether the text supports the statement. This check is **not an independent review by a lawyer**. The collection contains 61 statutory provisions from Fedlex. A small number of verified passages from court decisions is stored for the expert briefing only; this is not a full set of court decisions.

## 3. Data protection and confidentiality

The Swiss Federal Act on Data Protection (**FADP**, SR 235.1) applies to relevant personal-data processing. Art. 6 sets principles such as lawful and proportionate use. Arts. 7–9 concern data protection by design, security, and processing by third parties. Art. 19 sets information duties. Art. 22 requires a data protection impact assessment when processing is likely to create a high risk.

The prototype processes information about debts, household conditions, and inheritance. The user can also share health-related information. Some information may be sensitive personal data under Art. 5(c) FADP. Not all financial data are automatically sensitive data under that provision.

**The current data flow is as follows:**

1. The user writes messages in the chat.
2. An external model service receives the conversation for fact extraction and, where applicable, answer drafting and citation screening.
3. The program stores extracted facts, user quotations, and decision reasons in the case record.
4. On `REFER`, the program proposes a hand-over. If the user agrees, the user enters a first name, a surname and an e-mail address; a phone number is optional. These details are not sent to the model service.
5. The program then writes a Markdown briefing to the local `outbox/` directory. The briefing contains these details, a case number and the conversation.
6. The program also sends the briefing by e-mail if SMTP has been configured.

The local briefing is **not encrypted by the application**. The program does not provide automatic deletion, an access-control system, or a full process for data-subject requests. The model provider's storage location and retention terms are not established by the Python code. These are material limits for any use with real client information.

A deployed service must identify the responsible organisation, explain the purposes and recipients of the data, and assess any transfers abroad. It must also set suitable access, storage, deletion, and incident procedures. The need for a data protection impact assessment depends on the actual risk and scale of processing.

### Professional confidentiality

Legal information calls for careful handling even when professional secrecy does not apply. Swiss lawyers have specific duties under **Art. 13 BGFA** and **Art. 321 of the Swiss Criminal Code**. A person who has a master's degree in law does not automatically have the same professional status as a registered lawyer.

The prototype uses a lawyer, or a person with at least a master's degree in law, as its definition of a human expert. This is a project staffing rule. It does not establish a right to represent clients or prove that every confidentiality duty applies to that person.

## 4. Liability, transparency, and human control

A wrong legal classification can cause loss or delay. The organisation that uses the system and the people who provide legal services can have duties under Swiss law. Depending on the facts, liability may involve **Art. 41 OR** or **Art. 97 OR**. A warning that the system does not give legal advice does not remove all possible legal responsibility.

Human control is central to the design. After the user agrees to a hand-over, the program attempts to create a briefing with known facts, user quotations, open questions, estimated deadlines, the conversation, and decision reasons. The briefing uses a fixed template. However, it can repeat an error in the extracted facts. A human expert must check the facts and original documents before giving advice.

**A referral is not the same as accepted human assistance.** The program saves a local file and can attempt to send an e-mail. It does not track whether an expert accepts the case or responds before a deadline. The confirmation states that the team will contact the user by e-mail, but the software cannot confirm that contact. Before the user agrees, the proposal states that the hand-over does not preserve a deadline and that no fixed response time is given, together with the prices and the main rules of LexTec's general terms. After the hand-over the user receives a case number to refer to. The briefing carries a priority class, so that the team sees which case to open first. These measures inform the user and the team; they do not guarantee a timely response. This remains a limit of the current hand-over process.

The system does not file legal documents, contact public authorities, or call emergency services. It must not be treated as an emergency service.

## 5. Optional psychological distress screening

Debt problems can place people under emotional pressure. For this reason, the prototype includes a **separate, optional check** for signs of psychological distress.

The user can accept or refuse this check. When the user accepts, the program uses a model field and selected German and English keyword patterns to find possible warning signs. A detected sign activates an urgent `REFER` decision: the system proposes a hand-over and shows emergency contact information above the proposal. The user still decides whether anything is passed on. It does **not** make a medical diagnosis or contact emergency services.

When the user refuses, the distress-specific checks do not run. The normal legal-intake process still sends user messages to the model service. Therefore, refusal does **not** prevent incidental health information in those messages from reaching the provider.

This mechanism has limits. A sentence can be misunderstood because of a quotation, a joke, a negation, or an unusual expression. The system may also miss a genuine warning sign. A positive result is not proof of a mental-health condition. A negative result is not proof that the user is safe. The stored briefing can contain sensitive information, and the current outbox has no application-level encryption.

The screening respects a basic ethical choice: the user can refuse the additional check without losing access to the ordinary legal-intake process. Emergency numbers remain available regardless of that choice.

## 6. Ethical risks and safeguards

| Risk | Present design measure | Remaining limitation |
|---|---|---|
| Wrong facts or legal area | Structured fields, user quotations, and confirmation by the user of consequential facts read from free text | A correct quotation can still support a wrong interpretation. |
| Invented legal statements | Restricted statute collection and citation screening | The final support check still uses a model. |
| Missed deadlines | Python date estimates, urgent notices, and urgent referral rule | Legal starting dates and exceptions can be misunderstood. |
| Excessive referral | Separate `ASK` and `PROCEED` routes | Too much referral can delay access to help. |
| Unequal treatment | German and English question templates | Dialect, spelling, and language style can change results. |
| Privacy or security failure | Limited scope, optional distress consent, and hand-over only with the user's agreement | Unencrypted briefings and no built-in deletion process. |
| Excessive trust in the system | Referral reasons and quotations in briefings | Users or experts may trust an incorrect result. |
| Malicious or misleading text | Evidence and type checks after extraction | These checks do not fully prevent prompt injection. |

These risks show why safe routing cannot be measured by overall accuracy alone. **A missed referral can be more harmful than an unnecessary referral.** Both outcomes still matter, because users need timely and affordable access to legal help.

## 7. EU AI Act and cross-border use

The **EU AI Act** (Regulation (EU) 2024/1689, as amended in 2026) may apply if the service is placed on the EU market, used by an EU-based operator, or otherwise falls within the Act's territorial rules. Its application depends on the real service and use of its outputs.

A private intake tool is **not automatically a high-risk system** simply because it concerns law. Annex III includes certain systems used by or on behalf of judicial authorities and some dispute-resolution activities. A different deployment could change the legal classification.

The Act also contains rules on AI literacy and transparency. Under the 2026 amendment, the main high-risk provisions for Annex III systems are scheduled to apply from **2 December 2027**. The relevant Annex I date is **2 August 2028**. These dates do not remove other applicable duties. An EU deployment may also require a separate assessment under the GDPR.

## 8. User-facing disclosure

The chat program includes short opening and consent messages in German and English (`handover/texts.py`). This framework also provides the fuller disclosure below. The program does not yet display this exact wording. Neither version can guarantee a response from a human.

### English

> You are using an AI tool, not speaking with a lawyer. It covers selected questions about debts and debt enforcement under Swiss law, with a focus on Zurich. It may ask for more facts, give general legal information, or propose to hand your case to a human. It cannot file documents or confirm legal deadlines. If a deadline is close, seek legal help directly. Your messages are processed by an external AI service. Nothing is passed on to a human without your agreement. If you agree, a summary with your name and e-mail address is saved and may be sent by e-mail. This does not confirm that a professional has accepted your case. You can choose whether the tool also checks for signs of psychological distress. If you refuse, this extra check does not run. For an emergency in Switzerland, call 117 or 144. For emotional support, call 143.

### Deutsch

> Sie nutzen ein KI-System und sprechen nicht mit einer Anwältin oder einem Anwalt. Das System behandelt ausgewählte Fragen zu Schulden und Betreibungen nach Schweizer Recht, mit Schwerpunkt Zürich. Es kann Rückfragen stellen, allgemeine rechtliche Informationen geben oder vorschlagen, Ihren Fall an eine Fachperson zu übergeben. Es reicht keine Dokumente ein und bestätigt keine verbindlichen Fristen. Wenn eine Frist bald abläuft, holen Sie direkt rechtliche Hilfe. Ihre Nachrichten werden von einem externen KI-Dienst verarbeitet. Ohne Ihre Zustimmung wird nichts an eine Fachperson weitergegeben. Wenn Sie zustimmen, wird eine Zusammenfassung mit Ihrem Namen und Ihrer E-Mail-Adresse gespeichert und kann per E-Mail gesendet werden. Das bedeutet nicht, dass eine Fachperson den Fall angenommen hat. Sie können entscheiden, ob das System zusätzlich nach Anzeichen psychischer Belastung suchen darf. Ohne Zustimmung findet diese zusätzliche Prüfung nicht statt. In einem Notfall in der Schweiz: 117 oder 144. Für ein vertrauliches Gespräch: 143.

The messages above explain the purpose and limits of the intake tool. They do not replace the full data-protection information required for a live service, including the responsible organisation's identity and contact details.

## 9. Evaluation and conclusion

The evaluation dataset contains **24 synthetic Swiss legal scenarios**: **14 development cases** and **10 held-out cases**. Each scenario has an expected final route (`PROCEED` or `REFER`). The `must_ask` field records the facts that the system should ask about first. In this design, `ASK` is a step in the conversation, not a third final outcome.

The evaluation plan compares the system's route, questions, and urgency signals with these expected results. The main safety measure is **missed escalation**: a case that needs human review but receives an automated answer. Other measures include missed urgent deadlines and unnecessary referrals. The prepared scenarios and code-level checks do not, by themselves, establish performance with the live model. The expected routes were written for an earlier version of the questions and rules. They have to be revised before a new run, for example because a payment order with a running objection period now receives an urgent notice and no immediate hand-over.

The prototype makes one important choice: **a language model extracts facts and writes the reply, but Python rules decide when the system must stop**. This makes the decision policy easier to inspect and test. The design still depends on the quality of fact extraction, the legal accuracy of its rules, and the availability of real human support. It is a prototype for responsible legal intake, not a complete legal service.

## Legal sources

1. [Swiss Federal Act on Debt Enforcement and Bankruptcy (SchKG), SR 281.1](https://www.fedlex.admin.ch/eli/cc/11/529_488_529/de) — Arts. 8a, 27, 33, 74, 85, 85a, 86.
2. [Swiss Civil Code (ZGB), SR 210](https://www.fedlex.admin.ch/eli/cc/24/233_245_233/de) — Arts. 566–580, 593.
3. [Swiss Code of Obligations (OR), SR 220](https://www.fedlex.admin.ch/eli/cc/27/317_321_377/de) — Arts. 41, 97, 102, 104, 106.
4. [Swiss Federal Act on Data Protection (FADP), SR 235.1](https://www.fedlex.admin.ch/eli/cc/2022/491/en) — Arts. 5–9, 19, 22, 24.
5. [Federal Act on the Free Movement of Lawyers (BGFA), SR 935.61](https://www.fedlex.admin.ch/eli/cc/2002/153/de) — Art. 13.
6. [Swiss Criminal Code (StGB), SR 311.0](https://www.fedlex.admin.ch/eli/cc/54/757_781_799/de) — Art. 321.
7. [EU AI Act, Regulation (EU) 2024/1689, consolidated text of 27 July 2026](https://eur-lex.europa.eu/eli/reg/2024/1689/2026-07-27/eng), including amendment [Regulation (EU) 2026/1744](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32026R1744).
