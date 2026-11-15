# Research questions on the relevant articles

**Purpose.** The statute text alone does not answer many of the questions that decide a case in our areas. This list names those questions, article by article, so that the legal team can search case law and doctrine for each of them and store the answers as sources (see `README.md` in this folder).

**Level.** The questions are general ("which criteria make an act an interference in the estate?"), not case-specific ("does selling the deceased's phone count?"). Applying the criteria to a case is left to the lawyer, or to the model within the limits of the general classification.

**Status.** Drafted by the AI assistant on 2026-11-11 from the wording of the articles as published on Fedlex. The list contains questions only and asserts no answers. It has not yet been reviewed by the legal lead; the priorities are a proposal.

**Size.** 111 questions: 59 with priority 1, 38 with priority 2, 14 with priority 3.

## Suggested first batch

The full list is more than can be researched before the submission. These fourteen questions sit behind the two cases the prototype was built around and behind its most important deadline rule:

| Topic | Questions |
|---|---|
| Are collection fees owed? | OR106-1, OR106-2, OR106-6, SchKG27-2, SchKG82-3 |
| When is the right to disclaim lost, and can a missed period be repaired? | ZGB571-1, ZGB571-2, ZGB571-3, ZGB571-5, ZGB566-2, ZGB567-1, ZGB576-1 |
| When does the ten-day period for the objection start, and can it be restored? | SchKG74-1, SchKG33-1 |

## How to read the tables

| Column | Meaning |
|---|---|
| ID | Stable identifier. Use it to link a source to a question. |
| Type | **Term**: a legal term the statute does not define. **Discretion**: the statute leaves the decision to a judge or an office. **Procedure**: deadline, form, competent authority. **Proof**: burden or standard of proof. **Effect**: legal consequence. **Interplay**: relation between provisions. |
| Prio | **1**: the answer changes what our system tells a user or a lawyer in a typical case, or it stands behind one of the escalation rules. **2**: comes up regularly. **3**: rare or peripheral. |
| Search terms | German terms for Swisslex, legalis and entscheidsuche.ch. |

Articles marked "(in corpus)" are stored in `corpus.json` and can be cited by the system today. The others were read on Fedlex for this list; add them to `tools/fetch_sources.py` if the system should cite them.

---

## A. Disputed debts and collection fees

### A1. Default: Art. 102, 103 and 75 OR

Whether default interest and default damage are owed at all depends on whether and when the debtor was in default.

| ID | Question | Type | Prio | Search terms |
|---|---|---|---|---|
| OR102-1 | What must a "Mahnung" contain to put the debtor in default (clarity of the demand, amount, form)? Can an invoice itself be a reminder? | Term | 1 | Mahnung, Inverzugsetzung, unmissverständliche Aufforderung, Rechnung als Mahnung |
| OR102-2 | When is a "bestimmter Verfalltag verabredet" within para. 2? Does a payment term printed on an invoice or in general terms and conditions ("zahlbar innert 30 Tagen") count as agreed? | Term | 1 | Verfalltag, Verfalltagsgeschäft, Zahlungsfrist auf Rechnung, einseitige Fristansetzung |
| OR102-3 | When is a monetary claim due if nothing was agreed (Art. 75 OR)? | Term | 3 | Fälligkeit, Art. 75 OR |
| OR102-4 | Who must prove receipt of the reminder, and when is a reminder deemed received? | Proof | 2 | Zugang der Mahnung, Beweislast, Empfangsbedürftigkeit |
| OR103-1 | What does "ohne jedes Verschulden" (Art. 103 para. 2) require? Can lack of money, illness or an unclear invoice excuse the debtor? | Term | 2 | Exkulpation Verzug, Geldmangel, Verschulden Schuldnerverzug |

### A2. Default interest: Art. 104 and 105 OR (Art. 104 in corpus)

| ID | Question | Type | Prio | Search terms |
|---|---|---|---|---|
| OR104-1 | From which day does default interest run, and on which amount (principal only, or also costs)? | Effect | 2 | Verzugszins Beginn, Zinsenlauf, Verzugszins auf Mahnspesen |
| OR104-2 | Under which conditions is a contractual interest rate above five per cent valid, especially in general terms and conditions with consumers? Which upper limits apply? | Interplay | 2 | vertraglicher Verzugszins, AGB, Höchstzins, Konsumkreditgesetz, Übervorteilung |
| OR104-3 | Is default interest owed irrespective of fault and of actual damage? | Effect | 3 | Verzugszins verschuldensunabhängig |
| OR105-1 | How far does the prohibition of interest on interest (Art. 105 para. 3) reach? May interest be charged on reminder fees or collection costs? | Interplay | 2 | Zinseszinsverbot, Art. 105 Abs. 3 OR, Verzugszins auf Inkassokosten |

### A3. Damage beyond default interest: Art. 106 OR (in corpus)

This is the core of the "disputed collection fees" case. The statute only says that a "grösserer Schaden" must be compensated.

| ID | Question | Type | Prio | Search terms |
|---|---|---|---|---|
| OR106-1 | Which items can be a "grösserer Schaden"? In particular: reminder fees, address searches, the creditor's own administrative effort, fees of a collection agency, pre-litigation lawyer's fees. | Term | 1 | Verzugsschaden, Art. 106 OR, Inkassokosten, Mahnspesen, vorprozessuale Anwaltskosten, Bearbeitungsgebühr |
| OR106-2 | Must the creditor substantiate and prove the damage concretely, or are flat amounts admissible (for example tariffs published by collection industry associations)? | Proof | 1 | Pauschale Verzugsschaden, Substantiierung, konkreter Schadensnachweis, Verbandstarif Inkasso |
| OR106-3 | Are the costs of instructing a collection agency caused by the default in the legal sense, and were they necessary and appropriate? Does the creditor have a duty to keep the damage low (Art. 44 OR)? | Discretion | 1 | Schadenminderungspflicht, Notwendigkeit Inkassobüro, adäquater Kausalzusammenhang, Art. 44 OR |
| OR106-4 | How does the fault requirement work ("wenn er nicht beweist, dass ihm keinerlei Verschulden zur Last falle")? What can exonerate a consumer debtor? | Proof | 2 | Exkulpationsbeweis Art. 106 OR, Verschulden Schuldner |
| OR106-5 | How do default interest and further damage relate: is only the amount exceeding the interest recoverable? | Interplay | 2 | Anrechnung Verzugszins, grösserer Schaden, Subsidiarität |
| OR106-6 | Can reminder and collection fees be agreed in the contract or in general terms and conditions? What is required for valid incorporation and sufficient certainty of the amount, and when is such a clause unusual or unfair (Art. 8 UWG)? | Interplay | 1 | Mahngebühren AGB, Inkassokosten vertraglich vereinbart, Ungewöhnlichkeitsregel, Art. 8 UWG, Bestimmtheit |
| OR106-7 | Is an agreed fee for late payment a contractual penalty (Art. 160 OR), and by which criteria does the judge reduce an excessive penalty (Art. 163 para. 3 OR)? | Discretion | 2 | Konventionalstrafe, Herabsetzung, übermässig, Art. 163 Abs. 3 OR, Mahngebühr als Konventionalstrafe |
| OR106-8 | Does it matter whether the collection agency acts on behalf of the creditor or has acquired the claim by assignment? Whose damage can be claimed in each case? | Interplay | 2 | Inkassozession, Inkassovollmacht, Schaden des Zessionars, Abtretung |
| OR106-9 | What are the effects of a partial payment, an instalment agreement or an acknowledgement of debt signed at the request of a collection agency (acknowledgement of the fees, title for provisional setting aside of the objection, interruption of the limitation period under Art. 135 OR)? | Effect | 1 | Schuldanerkennung Inkasso, Abzahlungsvereinbarung, Ratenzahlung, Art. 135 OR, Art. 82 SchKG |
| OR106-10 | To which part of the debt is a partial payment credited (Art. 85 OR)? May the creditor credit payments to collection costs first, and can the debtor determine otherwise? | Effect | 2 | Anrechnung Teilzahlung, Art. 85 OR, Art. 86 OR, Tilgungserklärung |
| OR106-11 | Which limitation period applies to typical consumer debts (Art. 127, 128 OR), and do reminders or collection letters interrupt it? | Effect | 2 | Verjährung, Art. 128 OR, Verjährungsunterbrechung, Mahnung |
| OR106-12 | When do the methods of a collection agency (threat of debt enforcement, of a register entry, of a credit-rating entry, of home visits) become unlawful? | Term | 2 | Inkassomethoden, Drohung Betreibung, unlauter, Nötigung, UWG Inkasso |

### A4. Costs of representation and of enforcement: Art. 27 and 68 SchKG (Art. 27 in corpus)

| ID | Question | Type | Prio | Search terms |
|---|---|---|---|---|
| SchKG27-1 | What are "Kosten der Vertretung im Verfahren vor den Betreibungs- und Konkursämtern"? Does the prohibition cover only steps inside the enforcement proceeding, or also the collection agency's work before it? | Term | 1 | Art. 27 Abs. 2 SchKG, Vertretungskosten, gewerbsmässige Vertretung, Inkassobüro |
| SchKG27-2 | How does Art. 27 para. 2 SchKG relate to Art. 106 OR: can representation costs that may not be charged in the proceeding be claimed as default damage instead? | Interplay | 1 | Art. 27 SchKG Verzugsschaden, Überwälzung Inkassokosten, Parteientschädigung Betreibung |
| SchKG68-1 | Which costs are "Betreibungskosten" borne by the debtor (Art. 68), and who bears them if the objection succeeds or the enforcement turns out to be unfounded? | Effect | 2 | Betreibungskosten, Art. 68 SchKG, GebV SchKG, Kostentragung |

### A5. The payment order and the objection: Art. 74 SchKG (in corpus), with Art. 31, 33, 56, 63, 64, 69, 72, 75, 77, 78 SchKG and Art. 142, 143 ZPO

Behind rule R4 (deadline close) and the facts `document_type`, `document_received_date`, `objection_filed`.

| ID | Question | Type | Prio | Search terms |
|---|---|---|---|---|
| SchKG74-1 | When is a payment order validly "zugestellt"? What applies to delivery to a household member or employee, to a postal collection notice, and to refusal of acceptance (Art. 64, 72)? Which date counts? | Term | 1 | Zustellung Zahlungsbefehl, Ersatzzustellung, Art. 64 SchKG, Abholungseinladung, Annahmeverweigerung |
| SchKG74-2 | What are the consequences of defective service: is the payment order void or merely challengeable, and when does the period start if the debtor learns of it later? | Effect | 2 | fehlerhafte Zustellung, Nichtigkeit Zahlungsbefehl, tatsächliche Kenntnisnahme |
| SchKG74-3 | How are the ten days computed: first day, end on a Saturday, Sunday or public holiday (Art. 31 SchKG with Art. 142 ZPO), and the effect of enforcement holidays and stay of enforcement (Art. 56, 63)? | Procedure | 1 | Fristberechnung Rechtsvorschlag, Betreibungsferien, Art. 63 SchKG, Art. 142 ZPO |
| SchKG74-4 | When is an objection made in time (handing over to the post, electronic transmission, oral declaration at the counter or by telephone)? | Procedure | 1 | Fristwahrung Rechtsvorschlag, Postaufgabe, telefonischer Rechtsvorschlag, elektronisch |
| SchKG74-5 | Which declarations count as an objection? Is specific wording needed, and what if the declaration is addressed to the creditor or the collection agency and not to the office? | Term | 1 | Form Rechtsvorschlag, Erklärung, Adressat, Rechtsvorschlag beim Gläubiger |
| SchKG74-6 | Who can declare the objection on behalf of the debtor (family member, representative without written authority)? | Procedure | 3 | Vertretung Rechtsvorschlag, Vollmacht |
| SchKG74-7 | How precisely must the disputed amount be stated in a partial objection (para. 2)? Can the objection be limited to interest and costs? What follows from an imprecise statement? | Term | 1 | Teilrechtsvorschlag, bestrittener Betrag genau angeben, Art. 74 Abs. 2 SchKG |
| SchKG74-8 | Does failing to object mean that the debt is recognised in substance, or only that the enforcement continues? | Effect | 1 | unterlassener Rechtsvorschlag, materielle Rechtskraft Zahlungsbefehl, Anerkennung |
| SchKG33-1 | What is an "unverschuldetes Hindernis" that allows restoration of a missed deadline (Art. 33 para. 4): illness, absence, language, mistake, reliance on wrong information? Within which time and before which authority must it be requested? | Discretion | 1 | Wiederherstellung der Frist, Art. 33 Abs. 4 SchKG, unverschuldetes Hindernis |
| SchKG77-1 | When is there a "Gläubigerwechsel" that opens the late objection (Art. 77), for example assignment of the claim to a collection agency, and what must be shown as "glaubhaft"? | Term | 2 | nachträglicher Rechtsvorschlag, Gläubigerwechsel, Art. 77 SchKG, Zession |
| SchKG75-1 | Does giving reasons for the objection limit the debtor later, and in which special cases must something be declared expressly (Art. 75)? | Effect | 3 | Begründung Rechtsvorschlag, Art. 75 SchKG |
| SchKG74-9 | Under which criteria is an enforcement abusive and therefore void (enforcement used only to harass or to damage creditworthiness)? | Term | 2 | rechtsmissbräuchliche Betreibung, Schikanebetreibung, Nichtigkeit, Art. 2 ZGB |

### A6. After the objection, and remedies without an objection: Art. 78 to 88 SchKG

| ID | Question | Type | Prio | Search terms |
|---|---|---|---|---|
| SchKG79-1 | What must the creditor do after an objection (Art. 79), and how long can the creditor continue the enforcement (Art. 88)? | Procedure | 2 | Beseitigung Rechtsvorschlag, Anerkennungsklage, Fortsetzungsbegehren, Jahresfrist Art. 88 |
| SchKG82-1 | What is a "durch Unterschrift bekräftigte Schuldanerkennung" (Art. 82)? Do a signed contract, an order confirmation, an online order or an invoice qualify? | Term | 1 | provisorische Rechtsöffnung, Schuldanerkennung, Rechtsöffnungstitel, zweiseitiger Vertrag |
| SchKG82-2 | Which defences can the debtor raise against provisional setting aside, and what does "sofort glaubhaft machen" require? | Proof | 2 | Einwendungen Rechtsöffnung, glaubhaft machen, Art. 82 Abs. 2 SchKG |
| SchKG82-3 | Can collection costs and reminder fees be included in the setting aside of the objection, or only what the acknowledgement of debt covers? | Interplay | 1 | Rechtsöffnung für Inkassokosten, Verzugsschaden Rechtsöffnung, Mahnspesen Rechtsöffnungstitel |
| SchKG85-1 | When can the debtor have the enforcement cancelled or suspended by the court although no objection was made: proof by documents of payment or deferral (Art. 85), declaratory action (Art. 85a) and its standard "sehr wahrscheinlich begründet"? | Proof | 2 | Art. 85 SchKG, Art. 85a SchKG, negative Feststellungsklage, vorläufige Einstellung |
| SchKG86-1 | What must be shown to reclaim a payment made on a debt that did not exist (Art. 86), and within which time? | Proof | 3 | Rückforderungsklage, Art. 86 SchKG, Nichtschuld |

---

## B. Entries in the debt enforcement register: Art. 8a SchKG (in corpus)

| ID | Question | Type | Prio | Search terms |
|---|---|---|---|---|
| SchKG8a-1 | What is a sufficient "Interesse" of a third party to obtain an extract, and how is it made "glaubhaft" (landlords, employers, credit agencies)? | Term | 2 | Einsichtsrecht, Interessennachweis, Art. 8a Abs. 1 SchKG, Betreibungsauskunft |
| SchKG8a-2 | When is an enforcement "nichtig" within para. 3 lit. a, and how does the debtor obtain that finding? | Term | 2 | nichtige Betreibung, Art. 8a Abs. 3 lit. a SchKG, Art. 22 SchKG |
| SchKG8a-3 | Does payment of the claim end the disclosure of the enforcement to third parties, or is a withdrawal by the creditor (lit. c) needed? Can the debtor demand a withdrawal? | Effect | 1 | bezahlte Betreibung Registerauszug, Rückzug der Betreibung, Löschung Betreibung nach Zahlung |
| SchKG8a-4 | What exactly are the requirements of the request under lit. d (objection made, three months, request before the right of inspection expires)? Is the request open to a debtor who paid after the payment order? | Term | 1 | Art. 8a Abs. 3 lit. d SchKG, Gesuch um Nichtbekanntgabe, ungerechtfertigte Betreibung |
| SchKG8a-5 | Which steps of the creditor count as "Verfahren zur Beseitigung des Rechtsvorschlags", and when are they "rechtzeitig"? Does a conciliation request suffice? | Term | 1 | Verfahren zur Beseitigung des Rechtsvorschlags, Nachweis Gläubiger, 20 Tage, Schlichtungsgesuch |
| SchKG8a-6 | When is the enforcement disclosed again, and what does "definitiv nicht gutgeheissen" cover (dismissal, non-entry, withdrawal of the creditor's application)? | Term | 2 | Wiederbekanntgabe, definitiv nicht gutgeheissen, Abweisung Rechtsöffnung |
| SchKG8a-7 | When is a proceeding "abgeschlossen" so that the five years of para. 4 start? How long do unpaid enforcements and certificates of loss remain visible? | Term | 2 | Erlöschen Einsichtsrecht, fünf Jahre, Abschluss des Verfahrens, Verlustschein Registerauszug |
| SchKG8a-8 | Which other ways remove an unjustified entry (declaratory action that the debt does not exist), and what interest in a declaration is required? | Interplay | 2 | negative Feststellungsklage Betreibung, Feststellungsinteresse, Art. 85a SchKG |
| SchKG8a-9 | Procedure of the request: form, fee, and remedy if the office refuses (Art. 17). | Procedure | 3 | Gebühr Gesuch Art. 8a, GebV SchKG, Beschwerde |

### B2. Private credit agencies (outside the covered scope; always referred)

Only relevant for the lawyer's briefing. Based on Art. 25, 31 and 32 DSG.

| ID | Question | Type | Prio | Search terms |
|---|---|---|---|---|
| DSG31-1 | Under which conditions may a credit agency process and pass on creditworthiness data (Art. 31 para. 2 lit. c DSG), and how old may the data be? | Term | 3 | Kreditwürdigkeit, Bonitätsdaten, Art. 31 Abs. 2 lit. c DSG, Wirtschaftsauskunftei |
| DSG32-1 | What can the person demand if data are incorrect or disputed (access, correction, deletion, note of dispute), and who must prove correctness? | Proof | 3 | Auskunftsrecht, Berichtigung, Bestreitungsvermerk, Art. 32 DSG |

---

## C. Subsistence minimum during seizure: Art. 93 and 17 SchKG (both in corpus), with Art. 20a, 22, 36, 91, 92 SchKG

The system always refers these cases (rule R12). The questions serve the lawyer's briefing.

### C1. Seizure of income: Art. 93 SchKG

| ID | Question | Type | Prio | Search terms |
|---|---|---|---|---|
| SchKG93-1 | How is what is "unbedingt notwendig" determined? What is the legal status of the guidelines of the conference of enforcement officers and of the Zurich circular, and how binding are they? | Discretion | 1 | betreibungsrechtliches Existenzminimum, Notbedarf, Richtlinien, Kreisschreiben Obergericht Zürich, Grundbetrag |
| SchKG93-2 | How wide is the "Ermessen des Betreibungsbeamten", and how intensively do the supervisory authorities and the Federal Supreme Court review it? | Discretion | 1 | Ermessen Betreibungsbeamter, Ermessensüberschreitung, Kognition Aufsichtsbehörde |
| SchKG93-3 | Which expenses are recognised on top of the basic amount, and under which conditions: rent (and when it is too high), health insurance premiums, work-related costs, maintenance payments, medical costs? Must the expense actually be paid? | Term | 1 | Zuschläge Existenzminimum, Wohnkosten, Krankenkassenprämien, effektiv bezahlt, Berufsauslagen |
| SchKG93-4 | Are current taxes part of the subsistence minimum? | Term | 1 | Steuern Existenzminimum, Steuerschulden Notbedarf |
| SchKG93-5 | Who belongs to "seine Familie", and how is the income of a spouse, registered partner or cohabiting partner taken into account? | Term | 1 | Familie Art. 93 SchKG, Konkubinat Existenzminimum, Ehegatte Beitrag, proportionale Aufteilung |
| SchKG93-6 | Which kinds of income are seizable to a limited extent, and which are entirely exempt (Art. 92), for example old-age and disability pensions, social assistance, supplementary benefits? | Term | 2 | beschränkt pfändbar, unpfändbar, Art. 92 SchKG, AHV-Rente Pfändung, Sozialhilfe |
| SchKG93-7 | How is the income of self-employed persons or irregular income determined? | Discretion | 3 | Pfändung Selbständigerwerbender, schwankendes Einkommen |
| SchKG93-8 | What follows from the one-year limit of para. 2, and what happens with several creditors or renewed seizures? | Effect | 3 | Lohnpfändung Jahresfrist, Art. 93 Abs. 2 SchKG, Pfändungsgruppe |
| SchKG93-9 | Which changes of circumstances lead to an adjustment (para. 3), how is it requested, and from when does it apply? | Procedure | 1 | Revision Lohnpfändung, veränderte Verhältnisse, Art. 93 Abs. 3 SchKG, Anpassung |
| SchKG93-10 | How does the direct payment of health insurance premiums under para. 4 work, and what are its conditions? | Procedure | 2 | Art. 93 Abs. 4 SchKG, Krankenkassenprämien Lohnpfändung, Überweisung Arbeitgeber |
| SchKG93-11 | When is a seizure that cuts into the subsistence minimum void (Art. 22), so that it can be challenged after the ten days, and when only challengeable? | Effect | 1 | Eingriff in das Existenzminimum, Nichtigkeit Pfändung, Art. 22 SchKG, offensichtlich |
| SchKG93-12 | Which duties of information does the debtor have (Art. 91), and what follows if documents are not provided? | Procedure | 2 | Auskunftspflicht Schuldner, Art. 91 SchKG, Mitwirkung Pfändung |
| SchKG93-13 | Must the employer be notified of a seizure of wages, and can this be avoided? | Procedure | 2 | Anzeige an Arbeitgeber, stille Lohnpfändung, Art. 99 SchKG |

### C2. Complaint: Art. 17 SchKG

| ID | Question | Type | Prio | Search terms |
|---|---|---|---|---|
| SchKG17-1 | What is a "Verfügung" open to complaint (seizure record, calculation of the subsistence minimum, refusal to adjust), and what is not? | Term | 1 | Verfügung Betreibungsamt, Anfechtungsobjekt, Art. 17 SchKG, Pfändungsurkunde |
| SchKG17-2 | When did the complainant obtain "Kenntnis", and how are the ten days computed? Note Art. 145 para. 4 ZPO on the suspension of time limits. | Procedure | 1 | Beschwerdefrist, Kenntnisnahme, Fristenstillstand Beschwerde, Art. 145 Abs. 4 ZPO |
| SchKG17-3 | What do "Gesetzesverletzung oder Unangemessenheit" cover, and how far is discretion reviewed? | Discretion | 2 | Unangemessenheit, Ermessenskontrolle, Beschwerdegründe |
| SchKG17-4 | Which authority is competent in the Canton of Zurich, what must the complaint contain, and what does it cost (Art. 20a)? | Procedure | 1 | Aufsichtsbehörde Zürich, Bezirksgericht untere Aufsichtsbehörde, kostenlos Art. 20a SchKG |
| SchKG17-5 | Does a complaint suspend the seizure (Art. 36)? When is suspensive effect granted? | Discretion | 2 | aufschiebende Wirkung, Art. 36 SchKG |
| SchKG17-6 | What counts as denial or delay of justice (para. 3), which can be raised at any time? | Term | 3 | Rechtsverweigerung, Rechtsverzögerung, Art. 17 Abs. 3 SchKG |

---

## D. Inheriting debts: Art. 566, 567 and 571 ZGB (in corpus), with Art. 560, 568 to 570, 572 to 576, 579, 580, 587 to 590, 593, 603 ZGB and Art. 59 SchKG

### D1. Liability of heirs: Art. 560 and 603 ZGB

| ID | Question | Type | Prio | Search terms |
|---|---|---|---|---|
| ZGB560-1 | Which debts of the deceased pass to the heirs and which end with death (for example fines, maintenance, tax debts, repayment of social assistance)? | Term | 1 | Erbschaftsschulden, Universalsukzession, höchstpersönliche Schulden, Erbgangsschulden |
| ZGB603-1 | What does joint and several liability mean for a single heir towards a creditor, and how is recourse among heirs arranged? | Effect | 2 | Solidarhaftung Erben, Art. 603 ZGB, Regress |
| SchKG59-1 | Can a creditor enforce estate debts against an heir during the period for disclaiming (Art. 59 SchKG)? How should an heir react to a payment order in this time? | Interplay | 1 | Rechtsstillstand Erbschaftsschulden, Art. 59 SchKG, Überlegungsfrist |
| ZGB560-2 | Does answering a creditor, promising payment or paying a debt of the deceased from the heir's own money affect the heir's position? | Effect | 1 | Zahlung Erbschaftsschulden aus eigenem Vermögen, Einmischung, Anerkennung |

### D2. Right to disclaim and presumed disclaimer: Art. 566 ZGB

| ID | Question | Type | Prio | Search terms |
|---|---|---|---|---|
| ZGB566-1 | When is the insolvency of the deceased "amtlich festgestellt" (certificates of loss, bankruptcy, fruitless seizure)? | Term | 1 | amtlich festgestellte Zahlungsunfähigkeit, Verlustscheine, Art. 566 Abs. 2 ZGB |
| ZGB566-2 | When is insolvency "offenkundig", and for whom must it be obvious (the heirs, the creditors, the public)? Which moment is decisive? | Term | 1 | offenkundige Überschuldung, offenkundige Zahlungsunfähigkeit, vermutete Ausschlagung |
| ZGB566-3 | What is the effect of the presumption: is a declaration still advisable or necessary, who bears the burden of proof towards creditors, and how is the presumption rebutted or lost (for example by interference)? | Proof | 1 | Vermutung der Ausschlagung, Widerlegung, Beweislast, Einmischung trotz Überschuldung |
| ZGB566-4 | Who declares the disclaimer for minors or persons under a deputyship, and is consent of the child and adult protection authority required (Art. 416 ZGB)? | Procedure | 1 | Ausschlagung Minderjährige, KESB Zustimmung, Art. 416 ZGB, gesetzliche Vertretung |

### D3. The three-month period: Art. 567, 568, 569, 576 ZGB

Behind rule R4 and the fact `date_learned_of_death`.

| ID | Question | Type | Prio | Search terms |
|---|---|---|---|---|
| ZGB567-1 | What must the heir know for the period to start: only the death, or also the own position as heir? What does "nachweisbar erst später von dem Erbfall Kenntnis erhalten" mean, and who must prove later knowledge? | Term | 1 | Fristbeginn Ausschlagung, Kenntnis vom Erbfall, Kenntnis der Berufung, Beweislast |
| ZGB567-2 | When does the period start for heirs who are called only because others disclaimed (Art. 569 para. 3), for appointed heirs, and for the heirs of an heir? | Procedure | 1 | Fristbeginn nachberufene Erben, Kenntnis von der Ausschlagung, Art. 569 ZGB |
| ZGB567-3 | How are the three months computed, and how is the period met (receipt by the authority or posting)? Do procedural rules such as Art. 142 ZPO apply to this period of substantive law? | Procedure | 1 | Fristberechnung Ausschlagung, Verwirkungsfrist, Fristwahrung, Postaufgabe |
| ZGB567-4 | Does ignorance of the debts, or discovering them late, delay the start of the period? | Effect | 1 | Unkenntnis der Überschuldung, Fristbeginn, Irrtum |
| ZGB568-1 | How do a protective inventory (Art. 568) and a public inventory (Art. 580, 587) change the period? | Interplay | 2 | Sicherungsinventar, öffentliches Inventar, Fristbeginn |
| ZGB576-1 | What are "wichtige Gründe" for an extension or a new period (Art. 576)? Can it be granted after the period has expired, and after an interference? How does the authority exercise its discretion? | Discretion | 1 | Fristverlängerung Ausschlagung, wichtige Gründe, Art. 576 ZGB, Fristwiederherstellung |

### D4. Declaring the disclaimer: Art. 570 ZGB

| ID | Question | Type | Prio | Search terms |
|---|---|---|---|---|
| ZGB570-1 | Which authority is competent in the Canton of Zurich, in which form is the declaration made, and what does it cost? | Procedure | 1 | zuständige Behörde Ausschlagung Zürich, Einzelgericht Erbschaftssachen, Bezirksgericht, Protokoll |
| ZGB570-2 | What does "unbedingt und vorbehaltlos" exclude (partial disclaimer, disclaimer in favour of a certain person, conditional declaration)? | Term | 2 | bedingte Ausschlagung, Teilausschlagung, Ausschlagung zugunsten |
| ZGB570-3 | Can a disclaimer or an acceptance be revoked or challenged for mistake, deception or duress? | Effect | 2 | Widerruf Ausschlagung, Willensmängel, Anfechtung Annahme Erbschaft, Irrtum |
| ZGB570-4 | Does the authority examine whether the disclaimer is valid (in time, no interference), or does it only record it? Who decides on validity if a creditor disputes it? | Procedure | 1 | Protokollierung Ausschlagung, Prüfungsbefugnis, Gültigkeit Ausschlagung, ordentlicher Richter |

### D5. Losing the right to disclaim: Art. 571 ZGB

Behind rule R5 (the user has dealt with estate assets) and the fact `estate_actions_taken`.

| ID | Question | Type | Prio | Search terms |
|---|---|---|---|---|
| ZGB571-1 | By which criteria has an heir "sich in die Angelegenheiten der Erbschaft eingemischt"? Is it an objective test of the act, or is a will to accept the inheritance required? | Term | 1 | Einmischung, Art. 571 Abs. 2 ZGB, Verwirkung Ausschlagungsrecht, konkludente Annahme, pro herede gestio |
| ZGB571-2 | Where is the line to acts that are "durch die blosse Verwaltung der Erbschaft und durch den Fortgang der Geschäfte des Erblassers gefordert"? Which acts are regarded as mere administration or urgent preservation (funeral, termination of the lease, clearing the home, urgent bills)? | Term | 1 | blosse Verwaltungshandlungen, Erhaltungshandlungen, dringliche Massnahmen, Wohnungsräumung, Bestattungskosten |
| ZGB571-3 | When has an heir "Erbschaftssachen sich angeeignet oder verheimlicht"? Does the value of the item matter (personal effects, items of little value), and does returning it or its proceeds undo the consequence? | Term | 1 | Aneignung Erbschaftssachen, Verheimlichung, geringwertige Gegenstände, Rückgabe |
| ZGB571-4 | Does it matter from which funds a payment is made (estate money or the heir's own money), and whether the heir uses accounts, a vehicle or subscriptions of the deceased? | Term | 1 | Zahlung aus Nachlassmitteln, Verfügung über Bankkonto Erblasser, Gebrauch Nachlassgegenstände |
| ZGB571-5 | Must the heir have known of the right to disclaim, of the status as heir or of the debts for an interference to have this effect? What is the role of mistake and good faith? | Term | 1 | Kenntnis Ausschlagungsrecht, Irrtum Einmischung, Rechtsirrtum |
| ZGB571-6 | Who must prove the interference, and by which standard? | Proof | 1 | Beweislast Einmischung, Gläubiger |
| ZGB571-7 | Do formal steps count as interference: applying for a certificate of inheritance, requesting information from banks, collecting the deceased's post, registering the death with authorities? | Term | 1 | Erbenbescheinigung Einmischung, Auskunftsbegehren Bank, BGE 133 III 1 |
| ZGB571-8 | After the period has passed without a declaration (para. 1), is there any remedy for an heir who discovers the debts only later (extension under Art. 576, challenge for mistake)? | Interplay | 1 | vorbehaltloser Erwerb, verpasste Ausschlagungsfrist, nachträglich entdeckte Schulden |
| ZGB571-9 | Does an interference by one heir affect the other heirs? | Effect | 3 | Einmischung Miterbe, Wirkung |

### D6. Consequences of a disclaimer and alternatives: Art. 572 to 575, 579, 580, 587 to 590, 593 ZGB

| ID | Question | Type | Prio | Search terms |
|---|---|---|---|---|
| ZGB572-1 | To whom does the share of a disclaiming heir pass? Do the heir's own children then become heirs and have to disclaim as well, and from when does their period run? | Effect | 1 | Ausschlagung Nachkommen, Eintritt der Kinder, Art. 572 ZGB, Fristbeginn nachberufene Erben |
| ZGB573-1 | What happens when all next heirs disclaim (liquidation by the bankruptcy office)? What may and must the disclaiming heirs still do with the home and belongings of the deceased, and who pays the funeral? | Effect | 1 | konkursamtliche Liquidation, Art. 573 ZGB, ausgeschlagene Erbschaft, Wohnungsräumung, Bestattungskosten |
| ZGB574-1 | What are the roles of the surviving spouse (Art. 574) and of subsequent heirs who are asked (Art. 575), and how do the one-month periods work? | Procedure | 3 | Art. 574 ZGB, Art. 575 ZGB, Monatsfrist |
| ZGB579-1 | When are disclaiming heirs still liable to creditors (Art. 579)? What are "Vermögenswerte ... die bei der Erbteilung der Ausgleichung unterworfen sein würden", what is a customary endowment, and what does good faith change? | Term | 2 | Haftung trotz Ausschlagung, Art. 579 ZGB, Ausgleichung, Erbvorbezug, Schenkung |
| ZGB580-1 | When is a public inventory the better choice than disclaiming? What are its conditions, costs, the one-month period, and its effect on liability (Art. 589, 590)? | Interplay | 1 | öffentliches Inventar, Art. 580 ZGB, Haftungsbeschränkung, Kostenvorschuss, Rechnungsruf |
| ZGB588-1 | What are the options after the inventory is closed, and what applies if the heir remains silent (Art. 588)? | Effect | 2 | Annahme unter öffentlichem Inventar, Art. 588 ZGB |
| ZGB593-1 | When is official liquidation available and sensible (Art. 593), and what blocks it? | Interplay | 3 | amtliche Liquidation, Art. 593 ZGB |

---

## E. Questions that cut across the areas

| ID | Question | Type | Prio | Search terms |
|---|---|---|---|---|
| X-1 | Which standard does "glaubhaft machen" set in the SchKG (Art. 8a, 77, 82), compared with full proof? | Proof | 2 | Glaubhaftmachung, Beweismass SchKG |
| X-2 | How is the line drawn between void and merely challengeable acts of the enforcement office (Art. 22 SchKG), and why does it matter for deadlines? | Effect | 1 | Nichtigkeit, Anfechtbarkeit, Art. 22 SchKG |
| X-3 | Which rules on computing and suspending time limits apply to which kind of deadline: deadlines towards the enforcement office, complaints, court actions under the SchKG, and periods of substantive law such as the disclaimer period (Art. 31, 56, 63 SchKG; Art. 142, 143, 145 ZPO)? | Procedure | 1 | Fristenlauf, Betreibungsferien, Fristenstillstand, Verwirkungsfrist |
| X-4 | When a creditor of the deceased writes to an heir who has not yet decided: which reactions are safe, and which could be read as acceptance or acknowledgement? | Interplay | 1 | Erbe Gläubiger Überlegungsfrist, Einmischung, Schuldanerkennung |
| X-5 | Which low-cost or free advice and procedural aid exists for debtors in the Canton of Zurich (debt counselling, legal aid)? | Procedure | 2 | Schuldenberatung Zürich, unentgeltliche Rechtspflege, Rechtsauskunft |
