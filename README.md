# Decision and Hand-over Layer for Legal AI (LexTec Challenge)

Legal and technical documentation of the group project. Status: 15 November 2026.

Repository: https://github.com/jacobidwk-create/lextec-handover-layer

This file is the complete documentation in short form. Two more files give detail:

- `full_report.md` is the long form: the reason for each design decision, the open points and the dated progress log. Comments in the code cite its section numbers.
- `LEGAL_ETHICAL_FRAMEWORK.md` is the framework that section 6 summarises.

## 1. Summary

This project is a prototype for the first contact between a layperson and a legal service. The person describes a debt problem in a chat. The system collects the facts and gives general legal information from stored statute text. When a defined risk applies, it proposes a hand-over to a human legal advisor at LexTec.

One design rule controls the system. A language model reads and writes text. Fixed Python rules select the route, calculate each deadline and set the urgent mark. The model can add caution. It cannot remove a hand-over proposal or an urgent notice.

The prototype has a web page, a command-line chat and 352 automated tests that all pass. A demo mode operates without an API key:

```
python3 server.py --demo
```

Then open http://127.0.0.1:8000 and select one of the six examples.

Terms in this document:

| Term | Meaning |
|---|---|
| Person | The layperson who uses the chat |
| Legal advisor | The human expert at LexTec: a lawyer, or a person with a master's degree in law |
| Route | `PROCEED` (give the result), `ASK` (ask a question) or `REFER` (propose a hand-over) |
| Legal field | One of the three covered topics, with its own questions, rules and result texts |
| Briefing | The document for the legal advisor after a hand-over |

## 2. The legal problem

Laypeople describe legal problems with gaps. A missing date or an unclear letter can change the correct next step. A legal AI that fills such gaps with assumptions gives confident and wrong answers. In Swiss debt enforcement a short period can end a right before the person speaks to an expert.

The LexTec challenge has two parts. Sub-challenge 1 is technical: a layer that decides when the AI continues, asks, or gives the case to a human. Sub-challenge 2 is legal and ethical: the criteria for that decision, test scenarios, a regulatory analysis and a disclosure. This project covers both parts. The criteria are the rules in `handover/rules.py`. The scenarios are the test set in `scenarios/`.

## 3. Scope

| Topic | Decision |
|---|---|
| Jurisdiction | Canton of Zurich, Swiss federal law |
| Languages | German and English |
| Model | GPT 6 Luna through its hosted API |
| Theme | People who have debts. They can rarely pay a lawyer, and the periods are short |

The system covers three legal fields. The legal lead supplied the flow of each field. Detail: `full_report.md`, sections 3.4a to 3.4c.

### 3.1 Late fees

A letter demands more than the original bill. The flow has three gates.

1. **Sender.** A letter from a company or a collection agency has no official effect. A payment order from the debt enforcement office starts a period of ten days for the objection (Art. 74 SchKG).
2. **Default.** The person owes additional charges only after default starts (Art. 102 OR). The questions ask for the state of the original bill and for a reminder or an agreed payment date.
3. **Each charge.** Default interest is 5 % each year by law; a higher rate needs an agreement (Art. 104 OR). A reminder fee needs an agreement with a fixed amount at the time of the contract (Art. 1 OR, Art. 8 UWG). Collection costs need proof of a concrete loss (Art. 106 OR, Art. 27 para. 2 SchKG).

The result is one fixed card for each charge, with a label such as "Nicht geschuldet" (not owed), the articles and a link to Fedlex.

### 3.2 Declining an inheritance

An heir has three months to disclaim an inheritance (Art. 567 ZGB). The flow has four gates.

1. **The period.** The start of the period depends on the type of heir. If the period possibly ended, the system asks about manifest insolvency of the deceased (Art. 566 para. 2 ZGB).
2. **Acts on the estate.** An heir who takes or sells estate assets can lose the right to disclaim (Art. 571 para. 2 ZGB). The system says "possibly forfeited" and proposes a hand-over.
3. **Finances of the estate.** The result names the applicable option: disclaimer (Art. 570 ZGB), public inventory (Art. 580 ZGB) or official liquidation (Art. 593 ZGB).
4. **Traps.** Notes tell the person about the effect on their children (Art. 572 ZGB), earlier gifts (Art. 579 ZGB), their own creditors (Art. 578 ZGB) and supplementary benefits (Art. 11a ELG).

### 3.3 Entry in the debt enforcement register

A register entry can cost a person a flat or a job. The flow has two gates.

1. **Type of entry.** An enforcement, a loss certificate, or an entry at a private credit agency. The system assumes an enforcement when the person has no extract.
2. **The remedy.** The questions ask about payment, the objection, the date of service and the acts of the creditor. The usual remedy is a request for non-disclosure to third parties after three months (Art. 8a para. 3 lit. d SchKG, fee CHF 40, Art. 12b GebV SchKG). Payment after service of the payment order closes this remedy (BGE 147 III 486). Payment before service keeps it open (BGE 150 III 390). Other ways go through a court (Art. 85, 85a, 86 SchKG); for these the system proposes a hand-over.

### 3.4 All other matters

A matter outside the three fields gets a hand-over proposal immediately and no questions (rule R3). Examples are seizure of wages, family law and tenancy.

## 4. Technical design

### 4.1 Principles

1. **The model leads the conversation and the rules guard it.** The model reads each message into the case record and writes the reply. The case record is the typed data about the conversation. Python rules decide the route, the urgency and each deadline. An unknown value always causes the cautious result.
2. **Each legal statement has a stored source.** A legal statement from the model appears only when three conditions are true. The statement names an article that the legal field lists. It quotes the article word for word, and code compares the quote with the stored text. A second model call confirms that the quote supports the statement. The conversational part of a reply contains no article, date, period or percentage. The only numbers in it are amounts that the person wrote.
3. **Results are fixed text.** The result in each legal field comes from fixed rules and fixed texts. The model explains around the result.
4. **The person confirms important readings.** The model can read a consequential value from free text, for example an official sender. The system then asks the person to confirm it. Each list answer stays changeable.
5. **The person decides about the hand-over.** The rules decide that a hand-over is necessary. The person decides whether the system sends anything.
6. **The system sends no automatic alert to an authority.** In an emergency it shows emergency numbers.

### 4.2 One message, step by step

| Step | Action | Model call | File |
|---|---|---|---|
| 1. Extraction | The model fills the case record. Each item carries a word-for-word quote from the person. | Yes | `handover/extract.py` |
| 2. Validation | Code deletes each item whose quote is absent from the messages, whose type is wrong or whose date is in the future. | No | `handover/extract.py` |
| 3. Detectors | Keyword patterns find a request for a human, terms of other legal areas and, with consent, signs of distress. A detector can only add caution. | No | `handover/detectors.py` |
| 4. Deadlines | Code calculates each deadline from the established dates. | No | `handover/deadlines.py` |
| 5. Gate | The rules select the route. | No | `handover/rules.py` |
| 6. Reply | `ASK`: one question for each message. `PROCEED`: the fixed result. `REFER`: the hand-over proposal. The model writes the text around these parts, and code examines that text. | Yes, examined | `handover/compose.py`, `handover/engine.py` |

A question can show its listed answers as quick replies. A tapped answer goes directly into the case record with no model call. Free text is also possible. Fixed texts explain each legal term (`handover/knowledge.py`).

A "yes" without the deciding detail is a valid answer. The system records it and asks for the detail one time.

Each legal field is a file in `legal_fields/` with its scope, its citable articles and its flow. The model receives this file as its instruction for the field.

### 4.3 The rules of the gate

Each decision records the rules that applied and the words of the person behind them. Detail: `full_report.md`, section 3.3.

| Rule | Condition | Result |
|---|---|---|
| R0 | The model step fails two times | Proposal |
| R1 | The person asks for a human | Proposal |
| R2 | Signs of acute distress, only with consent to the screening | Proposal, urgent, emergency numbers |
| R3 | The matter is outside the three legal fields | Proposal immediately |
| R4 | A deadline has four working days or fewer, or possibly ended, and the necessary step is unconfirmed | Proposal, urgent |
| R5 | A defined fact: an official document from the debt enforcement office other than a payment order; a court document; an amount above CHF 5,000; acts on estate assets; a register remedy through a court; an entry at a private credit agency | Proposal |
| R6 | A critical fact stays unknown | Proposal |
| R7 to R10 | The legal area stays unclear; two attempts bring no progress; 24 question rounds; a contradiction stays | Proposal |
| R13 | A legal exception needs individual review, for example another jurisdiction or another official deadline | Proposal |
| R14 | The model names a topic that the stored sources do not cover | Proposal |
| U1 to U3 | A period runs and the person can act alone: objection to a payment order, a disclaimer period near its end, objection behind a register entry | Urgent notice; the conversation continues |
| A1 to A3 | The area is unclear, statements contradict, or necessary facts are missing | Question |
| P1 | No other rule applies | Result |

Five proposals appear together with the answer, for example for acts on estate assets. The person first reads the applicable information. The system then makes one proposal. After a "no" the conversation continues.

The margin of four working days and the amount of CHF 5,000 are project rules. Swiss law sets neither value. Four working days give the advisors time to act when a weekend is in between.

### 4.4 Deadlines

Code calculates each date. The model never states or calculates a date. The calculation is cautious: it gives the earliest possible end. It ignores rules that only extend a period, such as public holidays. The person and the advisor both read that the date is a screening value.

| Deadline | Basis | Calculation |
|---|---|---|
| Objection to a payment order | Art. 74 SchKG | Date of service plus ten days |
| Disclaimer of an inheritance | Art. 567 ZGB | Three months from the start that applies to the type of heir |
| Request for a public inventory | Art. 580 ZGB | The same start plus one month |
| First day for the request for non-disclosure | Art. 8a para. 3 lit. d SchKG | The day after three months from service |

### 4.5 Sources

The statute collection (`sources/corpus.json`) holds 61 articles. A script copies them from Fedlex (`tools/fetch_sources.py`). The collection for court decisions holds 28 passages. A script downloads each decision and accepts a passage only when the public text contains it word for word (`tools/verify_case_law.py`). The decisions appear only in the briefing, and fixed rules attach them to a case. Detail: `full_report.md`, sections 3.7 and 3.8.

## 5. The hand-over

Detail: `full_report.md`, section 3.6.

### 5.1 Proposal and agreement

On `REFER` the system proposes the hand-over and gives the reasons in plain words. It then asks: "Darf ich Ihr Anliegen übergeben?" Only a button or an exact short answer counts as yes or no. No model call reads this answer. After a "no" the system sends nothing, and the conversation continues where that is possible.

### 5.2 What the person reads before the answer

The legal lead decided that the person must know the conditions before the answer. Each proposal has three fixed parts (`handover/texts.py`).

1. **What the system sends.** A summary of the conversation with the messages of the person, the name and the e-mail address.
2. **Costs.** The yes costs nothing. A first orientation of 15 minutes is free. A consultation costs CHF 45 for 30 minutes or CHF 85 for 60 minutes. Costs start only when the person books an appointment.
3. **Six rules from the general terms of LexTec, with a link to the full text.**

| Rule as the person reads it | Source |
|---|---|
| The hand-over is the first step only; LexTec has not yet taken the case. It preserves no deadline. | Website of LexTec |
| A confirmed appointment is binding. LexTec gives no refund for a paid appointment. | General terms, section 3 |
| The person can move an appointment one time, free of charge, with an e-mail 48 hours or more before it. | General terms, section 3 |
| Invoices are due in 10 days. After that, LexTec can charge 5 % interest each year and CHF 30 for each reminder. | General terms, section 4 |
| LexTec is a legal advice service without the status of a law firm. Representation before courts and authorities needs a special agreement. | General terms, section 2 |
| LexTec answers by e-mail and gives no fixed response time. | Website of LexTec |

The AI assistant wrote the rules in plain words from the public pages on 15 November 2026.

### 5.3 The details of the person

First name, surname and e-mail address are necessary for a hand-over. The phone number is optional. Code examines the form of the e-mail address (`handover/contact.py`). A yes without these details sends nothing; the reply names the missing detail and shows the fields again. The details go into the briefing only. No prompt to the model contains them, and a test confirms this.

### 5.4 The case number

After the yes, the case gets a number such as `LX-20261115-7K3F`: the date and four random characters. The person sees the number in the confirmation and can quote it to LexTec. The briefing and its file name carry the same number. The number is unique in the `outbox/` folder only, because the prototype has no database of cases.

### 5.5 The briefing

Fixed templates build the briefing from the case record. One paragraph comes from the model: a short description of the matter. The briefing labels this paragraph as model-written and unverified. The briefing is in German by default. Its parts are:

1. the case number, the priority class, the reason for the hand-over, the urgency, and the name and e-mail address of the person;
2. the rules that applied, the deadlines, and each established fact with the quote of the person;
3. the legal questions that the facts raise, and the facts that are still missing;
4. the statutes and court decisions for these questions, then the full conversation and the audit trail.

The system writes the briefing to the `outbox/` folder and can also send it by e-mail.

### 5.6 The priority class

Each briefing has a priority class, so that the team sees which case to open first. The classes follow the Eisenhower matrix. The legal lead removed the quadrant "urgent and unimportant", because a deadline makes a matter important.

| Class | Condition |
|---|---|
| 1, urgent and important | The gate set the urgent mark: a deadline is near or possibly ended, a document from the debt enforcement office, or signs of acute distress |
| 2, important | A legal reason for the hand-over with no near deadline, or a calculated deadline that is far |
| 3, no deadline known | The person only wants a human, the matter is outside the three fields, or the conversation brought no result |

Fixed rules assign the class (`handover/priority.py`). An unknown rule gives class 2. Class 3 has the name "no deadline known" because the system examined no deadline for a matter outside the three fields.

## 6. Legal and ethical framework

This section is a short version of the framework that Leonardo wrote (`LEGAL_ETHICAL_FRAMEWORK.md`, revised on 15 November 2026).

### 6.1 When the AI must step back

The escalation criteria are the rules in section 4.3. They reduce unsafe assumptions. The model can still misunderstand a message. For this reason an unknown or unclear critical fact always leads to a question or a proposal.

A missed hand-over can cause more harm than an unnecessary one. An unnecessary hand-over still has a cost, because people need fast and affordable help.

### 6.2 Data protection

The Federal Act on Data Protection (FADP, SR 235.1) applies. Art. 6 sets the principles, for example lawful and proportionate processing. Art. 7 to 9 cover data protection by design, security and processing by third parties. Art. 19 sets the duty to inform. Art. 22 requires a data protection impact assessment when the processing is likely to cause a high risk.

The system processes data about debts, households and inheritance. A person can also write about health. Some of these data can be sensitive personal data (Art. 5 lit. c FADP).

The data flow is as follows.

1. An external model service receives the conversation for extraction, for the reply and for the examination of the reply.
2. The case record stores the facts, the quotes and the reasons for each decision. It stays in memory until the server stops.
3. After a yes to the hand-over, the system writes the briefing to `outbox/` and optionally sends it by e-mail. The briefing contains the name, the e-mail address and the full conversation.

The prototype has limits for use with real clients. The briefing file has no encryption. Automatic deletion, access control and a procedure for requests of data subjects are absent. The retention terms of the model provider are outside the code. A live service must name the responsible organisation, the purposes and the recipients. It must also assess transfers to other countries. A local model can replace the hosted model, because all model access goes through one interface (`handover/llm.py`, setting `LLM_BASE_URL`).

### 6.3 Confidentiality

Registered lawyers have duties under Art. 13 BGFA and Art. 321 of the Swiss Criminal Code. A master's degree in law gives a different professional status. LexTec states in its general terms that it has no status as a law firm under the BGFA. The project defines the human expert as a lawyer or a person with a master's degree in law. This staffing rule gives no right to represent clients, and the duties of professional secrecy can be different for such a person.

### 6.4 Liability and human control

A wrong legal classification can cause loss or delay. Liability can arise under Art. 41 OR or Art. 97 OR, and the facts of each case decide this. A notice that the system gives no legal advice leaves this responsibility in place.

Human control is central to the design. The briefing gives the advisor the facts, the quotes, the open questions and the calculated deadlines. The briefing can repeat an error of the extraction. The advisor must examine the facts and the original documents before any advice.

A hand-over is a request for human help. The software cannot confirm that an advisor accepted the case. The proposal tells the person that the hand-over preserves no deadline. For a running period, the urgent notice tells the person how to act alone.

### 6.5 Distress screening

The chat offers an optional screening for signs of acute distress. The person accepts or refuses it at the start. After a refusal, the model receives no question about distress and the distress keywords stay inactive. The normal process still sends the messages to the model service, so health information in a message can reach the provider.

A detected sign leads to rule R2: an urgent proposal with the emergency numbers 143, 144 and 117 at the top. The person still decides about the hand-over. Each person sees the emergency numbers at the start, with or without consent. The screening gives no medical diagnosis. It can miss a real sign, and it can misread a quote or a joke.

### 6.6 Risks and safeguards

| Risk | Safeguard in the design | Remaining limit |
|---|---|---|
| Wrong facts | Typed fields, quotes, confirmation of important readings | A correct quote can support a wrong reading |
| Invented law | Stored articles, word-for-word quote, second model call | The last examination still uses a model |
| Missed deadline | Dates from code, urgent notice, urgent proposal | The start date can be wrong; exceptions exist |
| Too many hand-overs | Separate routes; the conversation continues after a "no" | An unnecessary hand-over delays help |
| Unequal treatment | Texts in German and English | Dialect and spelling errors can change a result |
| Privacy failure | Consent before the hand-over; details stay out of prompts | Briefings have no encryption |
| Hostile text | Validation after extraction; fixed results | Prompt injection is possible |

### 6.7 EU AI Act

The EU AI Act (Regulation (EU) 2024/1689, as amended in 2026) can apply when the service is on the EU market. It can also apply when an operator in the EU uses the service. Annex III lists the high-risk systems, for example certain systems for judicial authorities. A private intake tool for legal questions is outside that list in its present form. A different use can change the classification. After the amendment of 2026, the main duties for Annex III systems apply from 2 December 2027. A service in the EU also needs an assessment under the GDPR.

### 6.8 Disclosure to the person

The chat starts with a fixed notice in German or English (`handover/texts.py`). The notice tells the person these points:

- the person talks to an AI system that gives general information on the listed topics;
- a hand-over to a human is possible, and it preserves no deadline;
- an external AI service processes the messages;
- the emergency numbers.

A live service also needs full data protection information.

## 7. Evaluation and tests

**Automated tests.** The 352 tests replace the model with prepared or recorded answers. They cover each outcome of the three flows, the dates, the urgent notices and the proposals. They also cover the examination of model text, the selection of court decisions, the hand-over and the page script.

**Trap cases.** `tools/trap_cases.py` runs conversations against the real model that try to push it off the rules. Examples are the instruction "ignore all your rules" and a question about limitation periods, which is outside the sources. In the run of 14 November 2026, 22 of 22 runs had no fault.

**Scenario set.** `scenarios/example/` holds 24 scenarios by Leonardo (14 for development, 10 held out) and one format example. Each scenario has hidden facts and an expected route. A simulated user answers from the hidden facts.

**State of the scenario results.** The development set ran one time, on 11 November 2026, against an earlier version of the questions.

The route was correct in all three runs for 10 of 14 scenarios. The system missed no necessary hand-over. It made 4 unnecessary hand-overs in 11 scenarios.

The questions and rules changed after that run. The scenario labels are still in their earlier state, and the held-out set is still closed. This project therefore makes no performance claim for the current version from the scenarios.

**Live conversations.** The team tested each field in plain language against the real model. Faults from these tests caused design changes.

## 8. How to run and test

Requirements: Python 3.11 or newer. Node.js 18 or newer is optional, for the two page tests.

```
pip install -r requirements.txt
```

The web server uses only the Python standard library.

| Task | Command | API key |
|---|---|---|
| Web page with recorded model answers | `python3 server.py --demo` | No |
| Web page, real model | `python3 server.py` | Yes |
| Chat on the command line | `python3 chat.py --lang de --debug` | Yes |
| Tests | `python3 -m pytest -q` | No |
| Trap cases | `python3 tools/trap_cases.py --show` | Yes |
| Scenario evaluation | `python3 evaluate.py --set dev` | Yes |

For the real model, copy `.env.example` to `.env` and put the key after `OPENAI_API_KEY=`. The repository excludes the `.env` file.

The other settings are optional, for example `LLM_MODEL` (default `gpt-6-luna`), `LLM_BASE_URL` (a local model server), `SMTP_HOST` and `BRIEFING_TO` (e-mail delivery) and `BRIEFING_LANGUAGE` (`de` or `en`). The file `.env.example` lists all settings.

**Demo mode.** The demo has six examples: two letters with late fees, two inheritance cases, a register entry and a topic outside the sources. The demo replays only the answers of the model (`demo/recordings.json`). The rules, the deadlines and the briefing run for real. The date is fixed to 11 November 2026.

**Main files.** Section 4.2 names the file of each step. Other main files are `handover/areas.py` (questions), `handover/late_fees.py`, `handover/inheritance.py` and `handover/register.py` (fixed results) and `handover/briefing.py`. `full_report.md`, section 7, lists each file.

## 9. Team contributions and disclosures

The two members divided the work along the two parts of the challenge.

| Member | Part | Contribution |
|---|---|---|
| Dario | The prototype (sub-challenge 1) | Scope and design decisions; the three legal flows and the glossary of legal terms; the thresholds; direction and review of the AI coding assistant; live tests; one half of the pitch video. Dario is the "legal lead" in this document. |
| Leonardo | The framework (sub-challenge 2) and the pitch | The legal and ethical framework (section 6); the test scenarios with their expected routes; the pitch slides; one half of the pitch video. |

**AI tools**

- Claude Code (Anthropic) wrote the code, the tests, the web page, the fixed texts and this documentation. It worked from the decisions and the legal flows of the legal lead. It also compared the flows with Fedlex, drafted four pitch slides from the framework and adapted the framework document to the current prototype.
- Codex (OpenAI) implemented two work packages on 12 November 2026: the guidance for a payment order and the recovery after a failed step. It used the Lexplorer research connector. A second AI agent reviewed this work.
- GPT 6 Luna is a component of the prototype. It does the extraction, the reply and the examination of the reply. It also writes the short description in the briefing and simulates the user in the evaluation.
- ChatGPT (OpenAI) composed the music of the demo video, a new track.
- An AI research tool answered legal research questions (`sources/Computational_Law_Verified_Research.md`). The team used the report as research material only. (Product name: to be added by the team.)
- whisper.cpp (model large-v3-turbo) transcribed the recorded slides for the pitch.

**Open-source components and external sources**

- Python packages `openai`, `certifi`, `pypdf`, `pytest`.
- `puppeteer-core` (Node.js), Pillow (Python), ffmpeg and a headless Google Chrome: render the demo video from the real page; ffmpeg also builds the pitch video. The prototype uses none of them.
- Lucide icons (ISC licence): icons on the pitch slides.
- Fedlex (fedlex.admin.ch): source of all statute text.
- entscheidsuche.ch and the public pages of the courts: source of the court decision passages.
- lextec-rechtsberatung.ch: design language of the page, prices and general terms (section 5.2). The project uses no logo and no image from LexTec.
- Directive No. 5 of the Federal Office of Justice on Art. 8a SchKG, and the pages law.lexplorer.ch, law.ch, servat.unibe.ch and gerichte-zh.ch: read to examine the legal logic. The project stores no text from them.
- Swisslex and legalis: research by the legal team.
- The fonts Inter and Manrope (Google Fonts, SIL Open Font License).

`full_report.md`, section 8, gives the date and the purpose of each use.

**Pitch.** The pitch video, the slides and the scripts that built the video are in the folder `pitch/`. That folder is not in this repository, because its files are too large. The team hands in the pitch video separately.

## 10. Limits and open points

This project is a student prototype with no official LexTec status.

1. **Legal review.** The AI assistant wrote the texts for the person from the flows of the legal lead. A full review of each text and of the 28 decision passages is still open. The passages keep the note "legal review pending".
2. **Confirmation by LexTec.** The conditions in section 5.2 and the contact address in the confirmation come from the public website. LexTec has to confirm them.
3. **Reading by the model.** The gate is exact for a given case record, and the model fills that record. The validation and the confirmation steps reduce this risk.
4. **Deadlines.** The dates are cautious screening values (section 4.4).
5. **Evaluation.** The scenario labels need an update before a new run (section 7).
6. **Data protection.** Section 6.2 lists what a live service needs.
7. **Identity.** The system examines only the form of the e-mail address.
8. **Project thresholds.** The amount of CHF 5,000 and the hand-over choices in the register field wait for the confirmation of the legal lead.
9. **Pitch.** Slide 3 of the pitch says "up to 3 targeted questions". This describes an earlier version. The system now asks one question for each message (section 4.2).

`full_report.md`, section 10, has the full list of open points.
