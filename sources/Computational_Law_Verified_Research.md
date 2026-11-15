# Computational Law — verified case-law and doctrine research

Research cut-off: **11 November 2026**. Work list: `sources/research_questions.md` (111 question IDs). This report is separate from the project; I made no edits to any project file.

## Scope and how to use this report

I read the question list, source instructions and schemas, candidate decisions, and the relevant prototype rules. Implementation comments refer to the version inspected during research; they are not a review of subsequent code changes. The answers below use judgments and directly inspected academic publications. Legislation was checked to detect amendments, but is not offered as a substitute for the requested case-law/doctrine evidence. General legal-information webpages are not authorities in this report.

**S — supported:** the stated answer is supported by the inspected authority. **P — partial:** useful authority exists, but an expressly identified part of the question remains unverified. **D — doctrinal position/dispute:** the proposition must be attributed to its author, not presented as settled case law. **G — gap:** no sufficiently verified authority obtained for the requested proposition. These labels concern coverage, not the probability of winning a case.

References **C01–C75** resolve to exact judgment citations and links in the source register. **D1–D5** identify directly inspected doctrine. A commentary cited *inside* a judgment has not thereby been independently verified: cite the judgment for that proposition unless the commentary appears separately in the doctrine register. Short original-language quotations in the register provide passage candidates; the English answers are summaries and must not be put in the JSON `passage` field.

The legal-text database reproduces the judgments themselves. Where the linked text is a database reproduction, that is expressly identified in the source register. I have **not** run the project's import verifier: it writes project files. A legally verified passage is not the same as a passage already tested against that script's HTML/PDF extraction. Preserve the stated limitations in `holding`, use `use: ["briefing"]` for disputed or fact-dependent propositions, and add the question IDs to the holding as your source instructions request.

## Findings that materially affect the prototype

1. **Collection fees are not established merely by a tariff or the label “Art. 106 OR”.** Separate contractual penalties, actual incremental default loss, lawyer costs, official enforcement costs, and collection-agency remuneration. C03–C16; D1–D2.
2. **Estate activity is a referral trigger, not an automatic acceptance rule.** Purpose, necessity, ownership knowledge and context matter. Even withdrawing estate money has been treated as potentially permissible administration in a narrowly defined case. C53–C60.
3. **The ten days may start before personal reading.** Valid service on a household member can start the period; a postal collection invitation is different. Faultless non-forwarding can support restoration. C18–C25.
4. **Register-disclosure sources need a 2026 update.** The former one-year application restriction and the old treatment of unsuccessful creditor applications must not be carried forward mechanically. C36–C37 address the revised provision. C35 also distinguishes payment before service from payment after service.
5. **The old “insurance premiums only if already paid” rule needs qualification.** Recent authority expressly recognises the direct-payment route under Art. 93(4) SchKG. C47.

## A. Disputed debts and collection fees

### A1. Default

**OR102-1 — S.** A reminder must convey an unequivocal demand for performance and identify what is demanded sufficiently for the debtor to understand it. A monetary demand normally specifies the amount, but a reference to an identifiable invoice can suffice; exceptional claims not yet quantifiable are treated differently. No ritual formula is required. An invoice can perform this function **if its actual wording communicates that demand**; the document's label alone does not decide it. **C01, E. 3.2.2**. Receipt remains necessary; **C02, E. 3.1.3–3.1.4**. Do not infer that every invoice immediately causes default.

**OR102-2 — P/D.** Distinguish an agreed due date from a term added unilaterally to an invoice. A term accepted as part of the contract requires the incorporation analysis in **C07, E. 2.1.1–2.1.3**. **D1, II.C, p. 1134**, challenges standard-term exclusions of a reminder. That is an author's position, not a verified categorical Federal Supreme Court holding. A directly applicable judgment on the precise wording “zahlbar innert 30 Tagen” was not verified; do not encode that wording as invariably sufficient or insufficient.

**OR102-3 — S.** Unless the contract or nature of the relationship provides otherwise, performance is due immediately. Maturity and default remain distinct: an immediately due claim is not necessarily already in default. **C01, E. 3.2–3.2.1**.

**OR102-4 — S.** The creditor bears the allegation and proof burden for the reminder. It is a declaration requiring receipt; even a claim or counterclaim serving as a reminder causes default only upon notification to the debtor. The date of court service can be judicially known and need not be proved again. **C02, E. 3.1.3–3.1.4**. This establishes the burden and receipt requirement, but does not supply a universal deemed-receipt rule for every postal or electronic channel.

**OR103-1 — P.** Fault must be distinguished from maturity, receipt and the separate no-fault interest obligation. **C04, E. 5.2**, treats fault as a requirement for additional default loss, whereas **C01, E. 3.1**, treats statutory default interest independently of fault. **D1, X.C, p. 1143**, addresses presumed fault and generally rejects lack of money as an excuse. Illness-specific exculpation remains unverified. An unclear demand can instead fail the reminder requirement in C01. Do not automatically import the stricter procedural-restoration test from C24 into substantive contract liability.

### A2. Default interest

**OR104-1 — P.** Interest presupposes both maturity and default; a reminder requiring receipt cannot trigger interest before receipt. **C01, E. 3.2; C02, E. 3.1.3**. The title for a principal claim can support statutory ancillary default interest without a separate interest judgment, but that does not establish every asserted fee as principal: **C15, E. 4.2.4**. The inspected judgments do not resolve every first-day arithmetic issue or interest on each kind of collection charge. Those should not be inferred from the label “costs”.

**OR104-2 — P.** The general incorporation and unusual-clause tests apply to standard terms: **C07, E. 2.1.1–2.1.3**. The research did not establish a single universal numerical ceiling for all consumer default-interest clauses. In particular, a consumer-credit maximum must not be applied without first establishing that the transaction falls within that regime. Current numerical ceilings and the distinction between agreed interest, penalties and usury remain a targeted research gap under the requested case-law/doctrine-only constraint.

**OR104-3 — S.** Statutory default interest does not require proof of actual loss or fault. Those requirements must not be imported from the additional-damages claim. **C01, E. 3.1**.

**OR105-1 — P.** The prohibition cannot be evaded merely by capitalising interest into a damages principal. **C74, E. 4c**, refuses to capitalise contractual damages interest and then charge default interest on it, expressly invoking Art. 105(3). **E. 4a** also excludes cumulative damages interest and default interest for the same deprivation of capital. The decision does not determine whether each reminder or collection charge is interest, a penalty, actual loss or an independently due principal claim; that classification remains unverified. Do not infer that all fees either bear interest or are categorically interest-free.

### A3. Additional loss and agreed fees

**OR106-1 — P/D.** The strongest verified judicial rule is that pursuing a claim can generate recoverable default loss only insofar as the expense is necessary and appropriate, relates to an existing claim, satisfies the liability requirements, and is not already compensated procedurally: **C04, E. 5.2**. For pre-litigation lawyers, the claimant must identify the concrete work and explain why it meets those conditions: **C05, E. 3 and 4.2.2**. **C06, E. 9.2.2**, stresses that pre-litigation work preparing, facilitating or avoiding an anticipated lawsuit is normally already covered by the procedural party-cost award; separate recovery is exceptional.

For the finer taxonomy—address searches, internal overhead, reminders and agency remuneration—see the attributed analyses in **D1, IV.C–VI.C, pp. 1136–1139**, and **D2, N 1043–1044, 1105–1111, 1162–1164, pp. 217, 230–231, 241–242**. **Do not turn the lawyer-cost rule into blanket permission to pass on an agency's invoice.** A Federal Supreme Court judgment squarely approving ordinary consumer collection-agency tariffs was not verified.

**OR106-2 — S/D.** Under the statutory damages route, prove the actual loss and its connection with the delay. **C03, E. 3a**, permits evidential assistance for particular financial-investment losses, not a general reversal of the burden or a universal tariff. Merely giving the total of a lawyer's bill and referring to an annex was insufficient: **C05, E. 4.2.2**. **D2, N 1164, pp. 241–242**, addresses industry schedules specifically. A separately valid contractual lump sum requires its own incorporation and enforceability analysis; it is not proof of actual loss. See OR106-6/7.

**OR106-3 — S/D.** Necessity and appropriateness must be shown for the particular expense; employing a professional is not itself enough. **C04, E. 5.2; C05, E. 4.2.2; C06, E. 9.2.2**. Ordinary overhead that would have arisen anyway is distinguishable from an incremental expenditure; the inspected overhead case concerned a different kind of loss and is not used as a collection-fee precedent. The agency-specific causation/mitigation objections are doctrinal: **D1, IV.C–VI.C; D2, N 1105–1107, 1148–1149**. A creditor should explain what was done, why that step was required, its incremental cost, and why interest/procedural compensation does not already absorb it. This last sentence is a research-derived evidence checklist, not a quotation.

**OR106-4 — P.** **C04, E. 5.2**, identifies fault alongside default and recoverable enforcement expense. The creditor still bears the loss/causation burden in **C03, E. 3a**. **D1, X.C, p. 1143**, explains the presumed-fault structure; ordinary lack of funds is not a general defence. No verified consumer-specific catalogue for illness or reliance on disputed invoices is supplied. These factual issues should remain for legal assessment; default interest itself is treated differently in C01.

**OR106-5 — S.** Compare the **total proven delay loss with the total default interest over the relevant period**. Recover only the excess. One cannot select particular loss components or favourable periods and add them to the full interest award without the required overall comparison. **C03, E. 4b**. This is particularly useful against a bill simply adding “interest + full collection tariff”.

**OR106-6 — S/D.** First establish actual agreement. Individual terms prevail over standard terms; globally accepted AGB must have been made reasonably accessible. An objectively unusual clause is excluded from global assent where it is also subjectively unusual for that contracting party and was not specifically brought to its attention. **C07, E. 2.1.1–2.1.3**. These are general rules, not a holding that every collection-fee clause is invalid.

For linked third-party fee schedules and fee-specific fairness arguments, **D1, I.C, pp. 1132–1133, VIII.C, pp. 1140–1142**, and **D2, N 1103, 1126–1129, pp. 230, 234**, are directly inspected doctrine. Their more restrictive conclusions must remain attributed. The requested comprehensive judicial application of **Art. 8 UWG to ordinary collection-fee clauses remains unverified**. Record the actual contract version, link/schedule available at conclusion, prominence, determinability and individual negotiation; do not accept a collection firm's current website as evidence of historic assent.

**OR106-7 — S/D.** Classification depends on the clause's function. Excessive contractual penalties are reduced with restraint, considering the creditor's performance interest, gravity and fault of the breach, parties' circumstances and disproportionality; absence of measurable damage does not alone invalidate a penalty. **C08, E. 4**. Reduction can also apply by analogy to agreed liquidated damages where actual loss is materially lower: **C09, E. 2.3.3**. These holdings establish the framework, not a fixed permitted CHF reminder fee. **D2, N 1101–1111**, discusses the fee classification.

**OR106-8 — P.** Assignment and representation are legally different. A party seeking provisional Rechtsöffnung as assignee must establish the relevant succession/document chain: **C14, E. 4.1.1**. **D2, N 1132–1139, pp. 234–236**, discusses the allocation of recovered accessories between principal and collecting agent. This does not verify a comprehensive rule on a purchaser's own post-assignment loss or acquisition discount. Do not treat the purchase price, agent's fee and creditor's default loss as interchangeable.

**OR106-9 — S.** A signed instalment agreement may become a provisional title if it contains a sufficiently definite payment undertaking; examine precisely what debt and fees it acknowledges. **C13, E. 2**. Silence in response to creditor documents is insufficient to create that title: **C13, E. 3.3**. Payment on account can interrupt limitation for a remaining balance, depending on what the conduct objectively acknowledges. An expressly final payment that denies any balance is different. **C10, E. 5.2.1–5.2.4**. Interruption does not itself prove that every fee was valid, and a title remains subject to available defences. **C14, E. 4.1.2**. Coerced acknowledgements require a separate validity assessment; C17 concerns extreme collection conduct, not ordinary instalment negotiations.

**OR106-10 — S.** The ordinary costs/interest-first allocation is dispositive. Crucially, **genuinely disputed** costs or interest need not prevent payment of the admitted principal: **C11, E. 4.2.1–4.2.3**. Interest on the admitted portion must still be accounted for. Distinguish allocation within one debt from allocation between several debts; the latter is not comprehensively resolved by this case. A payment message identifying the admitted principal and disputed extras is legally relevant, but its effect depends on the facts.

**OR106-11 — P.** There is no single limitation period for every “consumer debt”. **C72, E. 6**, confirms the five-year category for specified claims including retail sales, crafts and medical/professional services. **C10, E. 5.2**, supplies the debtor-acknowledgement interruption analysis. The requested complete ten-year/five-year classification and a directly verified passage on a creditor's ordinary reminder letter were not obtained. Do not infer interruption merely because a collector sends another letter; distinguish such a letter from a debtor's acknowledgement or formal enforcement step.

**OR106-12 — P.** In **C17, E. 15.3.2–15.5, pp. 39–43**, the Bern criminal appeal court addressed a particularly coercive collection business, including pressure to obtain payment/acknowledgements and intimidation. The fee assessment was tied to those facts. It is not a holding that every threat of lawful enforcement or every home visit is criminal. For the separate civil/enforcement test of proceedings brought solely to harass or damage credit, **C27, E. 2.3.1**. Ordinary private credit-rating entries require a distinct data-protection analysis; that gap is identified below.

### A4. Representation and official costs

**SchKG27-1 — S/P.** The representation-cost prohibition concerns proceedings **before enforcement and bankruptcy offices**. Judicial incidental proceedings, notably Rechtsöffnung, can carry a party-cost award. **C12, E. 6.1, pp. 5–8**, expressly distinguishes those settings and the 2018 renumbering. It does not decide the full pre-enforcement collection-agency question. For that contested extension, see D1 and SchKG27-2. Do not equate “no agency surcharge before the office” with “no recoverable court representation costs”.

**SchKG27-2 — D.** **D1, IV.C, pp. 1136–1137**, expressly argues against shifting the agency mandate through Art. 106 and discusses the pre-litigation extension. **D2, N 1142–1149, pp. 236–238**, supplies a separately inspected analysis of the distinction between private representation and official fees. These are strong citable doctrinal objections. This packet does **not** establish a Federal Supreme Court merits holding resolving every pre-enforcement agency mandate. Keep the prohibition within office proceedings distinct from the disputed wider argument; C12 supports the procedural boundary, not that entire wider proposition.

**SchKG68-1 — S/D.** **D2, N 1144–1147, p. 237**, distinguishes official tariff charges, advanced by the creditor, from privately agreed representation expenses; it addresses unsuccessful or unfounded enforcement. An objection merely suspends the proceeding and does not itself adjudicate who ultimately owes the debt or all costs. Court party costs require the separate analysis in **C12, E. 6.1**. Thus the collector cannot make its own tariff an official enforcement fee merely by calling it “Betreibungskosten”.

### A5. Service and objection

**SchKG74-1 — S.** Valid delivery to a qualifying adult household member or employee can start the period even before the debtor personally sees the document. **C18, E. 2**, also addresses refusal in a proper service situation. An invitation to collect the order from the **enforcement office is not itself service**, and there is no duty to collect it there: **C19, E. 3.2.3**. For postal delivery, **C75, E. 4**, identifies actual formal delivery on a second attempt after the seven-day collection period had expired; that period's expiry was not treated as the service date. Check the delivery certificate, which has evidential force unless disproved. A refusal announced in advance by telephone is not equivalent to actual proper tender; simply placing the document in a mailbox does not cure that defect: **C21, E. 3**. Record who received what, when, where and how. If substitute delivery was valid but the document was faultlessly not passed on, consider C25 rather than moving the service date automatically.

**SchKG74-2 — S.** An irregular service can be cured by actual receipt/knowledge sufficient to exercise the remedy, with the period then running from that point: **C20, E. 3b**. Where the order never reaches the debtor, the defect is materially different: **C21, E. 3**. These cases do not justify saying every service error makes the entire proceeding permanently void. Also distinguish the challenge to service from a precautionary objection.

**SchKG74-3 — P.** The periods for enforcement acts are not generally frozen throughout enforcement holidays. **C28, E. 4–5**, distinguishes the Art. 63 extension at the end of a period from suspension of its running, and limits the rule to the relevant enforcement context. **C29, E. I**, applies the next-working-day rule to a Sunday expiry through Art. 31 SchKG/Art. 142 ZPO. A complete verified calendar algorithm covering the first day, all cantonal holidays and all stays is not supplied here. The prototype's simple received-date-plus-ten computation should remain a conservative referral signal, not a conclusive last-day calculation.

**SchKG74-4 — P.** Objection is informal; telephone and fax can be effective. Withdrawal is different and requires the appropriate original signature or qualified electronic signature: **C22, E. 2.3–2.4**. **C29, E. II.a–b**, explains oral objection to the serving postal agent and the debtor's proof burden. Obtain an official acknowledgement of an oral objection. This packet does not establish the complete current technical requirements for every electronic platform or ordinary email; do not extrapolate withdrawal formalities to objection, or assume every email channel is effective.

**SchKG74-5 — S/P.** No fixed formula is indispensable if the declaration clearly conveys opposition: **C20, E. 3c**. The proper recipient is the serving official at service or the enforcement office: **C29, E. II.a**. A dispute letter to the creditor is not, without evidence of effective delivery to the competent recipient, a verified objection. No particular forwarding/agency exception for misaddressed letters was established.

**SchKG74-6 — P.** Representation is possible, and a dispute over the representative's authority belongs to the enforcement complaint route. **C30, pp. 3–4**, upheld an objection on established authority and, alternatively, subsequent express ratification. It concerned a corporate representative, not a universal rule that any family member can act without authorisation. The full household-member/unauthorised-agent distinction remains to be checked before using a blanket rule.

**SchKG74-7 — S.** “Exactly stated” does not invariably require numerals. Where the payment order separately identifies principal and a fee, an objection confined to the fee is sufficiently exact if its amount can be immediately and unambiguously calculated from the order. **C23, unnumbered consideration, pp. 10–11**. This is directly relevant to collection surcharges. An ambiguous partial objection should not be treated as a clearly quantified concession; the exact declaration and order must be retained.

**SchKG74-8 — S.** Failure to object does not by itself create substantive res judicata or necessarily acknowledge the debt. **C31, pp. 21–22**, rejected an inference of acknowledgement from one payment under enforcement pressure and referred to the recovery action. **C14, E. 4.1.1**, distinguishes title/enforcement proceedings from adjudicating the claim itself. The procedural consequence can nevertheless be serious: enforcement may continue unless another effective remedy intervenes.

**SchKG33-1 — S/P.** Restoration requires absence of even slight fault. The impediment must actually prevent timely action; sudden illness can qualify if it also prevents appointing a representative. Once the impediment ends, file the reasoned restoration request **within the same length of period as was missed** and simultaneously perform the omitted act. **C24, E. 2.3.1–2.3.2; C25, E. 3.1**. For an ordinary missed objection, that means the ten-day restoration framework, before the competent supervisory authority, with the objection made to its proper recipient.

**C25** adds an important distinction: fault of an ordinary household recipient who was not contractually appointed to receive documents is not automatically attributed to the debtor. Faultless late knowledge must be made credible; assertion alone is insufficient. Do not confuse this with fault attributable through an appointed representative. Absence, unfamiliar language and legal mistake are not automatically sufficient; their individual treatment was not comprehensively verified here.

**SchKG77-1 — S.** A creditor change during an existing enforcement can permit a later objection until distribution or bankruptcy opening. The debtor has ten days from learning of the change to apply in writing, with reasons, to the **judge at the place of enforcement**, not the supervisory authority. Only objections occasioned by the creditor change qualify, and credibility suffices. If the debtor already objected to the original creditor, the defences belong in the ensuing lifting/recognition proceedings. **C26, E. 3.1–3.1.2**. A new collecting representative alone is not necessarily a change of creditor.

**SchKG75-1 — P.** An ordinary objection needs no reasons. The lack of new assets after bankruptcy must be expressly raised or that special defence is forfeited; bill-of-exchange enforcement also has special requirements. **C29, E. II.a**. The inspected passage establishes those exceptions, but not every possible later effect of a voluntarily supplied explanation. Preserve the exact words rather than treating an explanatory letter as an exhaustive list of all future defences.

**SchKG74-9 — S.** Nullity for abuse is exceptional: enforcement used for goals wholly unrelated to collecting a claim, such as harassment or damaging credit through manifestly excessive/repeated demands, may qualify. A dispute about whether the claim exists is normally for the merits court, not the enforcement office. **C27, E. 2.3.1**. “I do not owe it” alone is not the nullity test.

### A6. Subsequent proceedings and alternative remedies

**SchKG79-1 — P.** The creditor needs an appropriate procedure to remove the objection; a title proceeding examines the title, while a merits action addresses the claim. **C14, E. 4.1.1; C37, E. II.2.1–II.3**. For register non-disclosure, the creditor's proceeding must concern the same enforced claim and seek the relevant removal; an unrelated pending action is insufficient. The full computation of the continuation year's excluded litigation time under Art. 88 is not independently verified in this packet.

**SchKG82-1 — S/P.** A signed acknowledgement must show an unconditional undertaking to pay a definite or readily determinable amount. Several documents can form a title when the signed document sufficiently refers to the necessary supplementary material. For a loan, disputed disbursement must be established. **C13, E. 2**. A creditor's invoice or an unsigned online confirmation does not acquire the debtor's signature merely by existing. Whether an actual electronic order qualifies requires checking its signature and linked documents; this judgment does not resolve every electronic-signature implementation.

**SchKG82-2 — S.** The debtor must immediately make a defence credible; mere unsupported denial is insufficient. Credibility requires objective indications that make the alleged fact probable without excluding all other possibilities. **C14, E. 4.1.2**. The procedure is not a final merits determination: E. 4.1.1. Payment, invalidity, lack of maturity and other defences must be assessed in relation to the actual title and the evidence immediately available.

**SchKG82-3 — S/P.** A title for the principal does not automatically establish every separately claimed fee. **C13, E. 2**, supplies the title/amount requirement. **C15, E. 4.2.4**, distinguishes ancillary statutory interest from charges requiring a sufficient title; it concerns definitive enforcement and must be used with that limit. **C16, E. 4.3.3**, holds that asserted reminder/default fees are not simply necessary procedural outlays under Art. 95 ZPO; its discussion of the lower court's rejection for lack of title is not a general ruling that all fees are substantively unlawful. Inspect the signed agreement and incorporation of any schedule before concluding that fees are covered.

**SchKG85-1 — P.** **C32, E. 3.3**, expressly recognises that the revised Art. 85a action is available irrespective of whether an objection was made. It also rejects automatic interim suspension before the enforcement has reached the statutorily relevant secured stage; do not promise that filing the action itself stops seizure. The case reviews the challenged interim interpretation for arbitrariness. A complete independently verified treatment of Art. 85's documentary proof and the comparative strength of “sehr wahrscheinlich” was not obtained.

**SchKG86-1 — S/P.** **C31, pp. 21–22**, confirms recovery within one year of a non-debt paid following failure to object, without making recovery depend on ignorance of the non-debt or a separate showing that payment was involuntary. The claimant must still establish that the amount was not owed. This is not a general one-year limitation rule for all voluntary collection payments or all unjust-enrichment claims. Fine points about the start of the period for instalments remain unverified.

## B. Enforcement-register entries and private credit records

**SchKG8a-1 — S/D.** Credible, concrete interest is required; a prospective contractual relationship can establish it. An ordinary employer generally lacks the same credit-risk rationale as a landlord. Abstract collection of data is insufficient. **D3, N 12–17**. Do not equate a business's general interest in information with an unrestricted right to every person's extract.

**SchKG8a-2 — S.** Abuse/nullity is assessed under the narrow test in **C27, E. 2.3.1**, not by deciding the debt's merits at the office. **C35, E. 3.3**, confirms that the non-disclosure procedure does not enlarge the office's jurisdiction to decide disputed substantive issues. Seek a nullity determination through the competent enforcement-supervision route; where the complaint period is still open, do not rely exclusively on characterising the defect as nullity. See X-2.

**SchKG8a-3 — S/D.** Payment **after service** does not by itself entitle the debtor to non-disclosure under lit. d: **C34, E. 3.4; C35, E. 4.1–4.4**. A creditor's withdrawal is a different route. **D3, N 41–43**, rejects a general automatic duty to withdraw after payment. Obtain an express withdrawal agreement if that is part of a settlement; payment and withdrawal are not synonyms.

**SchKG8a-4 — S/P.** After objection, the application route involves the three-month waiting period and the creditor's opportunity to prove a relevant removal proceeding. **C36, E. 3b/cc–ff; C37, E. II.2.1–II.3**, apply/discuss the 2026 revision; the old rule closing the application route after the continuation year must not be reused. **C35, E. 4.3–4.5**, is particularly useful: payment **before service**, even after the creditor submitted the enforcement request, does not automatically bar an application. The debtor must document the payment, and the decision still turns on the formal procedural conditions. Payment after service is treated differently in C34.

**SchKG8a-5 — S/P.** **C37, E. II.2.1–II.3**, requires a proceeding directed at the same enforced claim; an already pending non-monetary dispute is not enough, nor is a future intention to amend it. **D3, N 65–66**, discusses a conciliation/recognition request expressly seeking removal of the specified objection and proof of filing. The current treatment of every conciliation withdrawal or expired permission to sue is not conclusively resolved by the older commentary. Do not cite its old unsuccessful-application rule without the 2026 qualification.

**SchKG8a-6 — P.** The 2026 rule expressly changes the effect of a creditor's definitively unsuccessful application: **C36, E. 3b/cc; C37, E. II.2.1**. Accordingly, “any creditor filing permanently defeats non-disclosure” is outdated. These authorities do not settle every meaning of final failure, including all forms of withdrawal, non-entry and renewed proceedings. Record the exact procedural outcome, finality and identity of the claim; those are material gaps for automated classification.

**SchKG8a-7 — S/D.** The five years run from completion, including loss of the ordinary ability to continue the proceeding, not automatically from its first entry. Open loss certificates have a separate disclosure rule linked to deletion. **D3, N 68–69**. Keep the limitation of the underlying certificate claim distinct from the lifetime of the original enforcement entry.

**SchKG8a-8 — S/P.** **C33, E. 2.7**, recognises that being pursued normally gives a sufficient interest in an ordinary negative declaration without separately proving economic harm; it discusses an exception for enforcement genuinely used to interrupt limitation in particular circumstances. Its old restriction of Art. 85a to cases without objection is superseded: **C32, E. 3.3**, expressly explains the 2019 change. An office non-disclosure request, an ordinary declaratory action and an Art. 85a action are distinct remedies.

**SchKG8a-9 — S/D.** Apply to the enforcement office, in writing or orally; the model form is optional. The CHF 40 flat fee and Art. 17 complaint against refusal are addressed in **D3, N 55, 70, 72**. The fee is not contingent on success. The cited commentary dates from 2023; its obsolete substantive eligibility restrictions must be separated from these procedural propositions. C36–C37 supply the newer eligibility context.

**DSG31-1 — S/D.** **D5, N 42(b)**, analyses the revised creditworthiness justification: adult subjects; underlying data no more than ten years old; no sensitive data or high-risk profiling; disclosure to persons intending to conclude or perform a contract with the subject. Rosenthal distinguishes ongoing facts from historical events and credit agencies from their customers. His qualifications concerning objections and other justifications are doctrinal, not a blanket ten-year retention permission. Register access alone does not decide onward processing.

**DSG32-1 — S/P/D.** **D5, N 137–141**, distinguishes correction of inaccurate data, objection/deletion subject to justification, and a dispute note where accuracy remains unresolved. N 141 discusses court-ordered communication of measures to third parties. Inference: distinguish “a creditor alleges a disputed debt” from “an established unpaid debt”; an objection alone does not adjudicate the debt. A verified credit-agency-specific allocation of the litigation burden of proof remains missing.

## C. Subsistence minimum and enforcement complaints

### C1. Income seizure

**SchKG93-1 — S/P.** Guidelines guide discretion; the office must still check whether applying them produces a result appropriate to the concrete circumstances. **C38, E. 2.3–2.4**. They are not a substitute for individual assessment or superior federal law; **C41, E. 4.4.1–4.4.3**, rejects the inclusion of current taxes despite contrary cantonal practice. The exact currently applicable Zurich circular and its numerical allowances were not independently established through a judgment/doctrine source. Historic CHF figures in C38 must not be copied as today's rates.

**SchKG93-2 — S/P.** The discretion is legally bounded: considering irrelevant factors or ignoring material circumstances is reviewable. **C38, E. 2.1, 2.4**. The Federal Supreme Court's review of discretion is narrower than a fresh calculation of the most appropriate budget. That judgment predates the BGG; use it for the substantive discretion standard, not its obsolete federal-appeal article. The complete modern division between supervisory merits review and federal review remains partly unverified.

**SchKG93-3 — S/P.** Expenses generally require an actual expenditure basis: **C39, E. 3b–3c**. Excessive housing costs can be reduced only after an appropriate transition allowing reasonable adjustment, not mechanically overnight: **C40, E. 2**. A necessary leased vehicle can be recognised in the circumstances considered in **C41, E. 5.2**. A recent court rejected imposing an impossible advance-payment condition for rent where the protected amount itself was too small to make the payment: **C48, E. II.2.6**. Health premiums require the additional qualification in SchKG93-10. The packet does not supply a complete allowance catalogue or current Zurich amounts for every medical, maintenance or occupational expense.

**SchKG93-4 — S.** Current taxes are ordinarily excluded from the debt-enforcement subsistence minimum. Do not transplant a family-law or procedural-legal-aid budget into the enforcement calculation. **C41, E. 4.4.1–4.4.3**. The distinct process-cost minimum is illustrated by **C73, E. 4**, not an exception allowing current taxes in ordinary wage seizure.

**SchKG93-5 — S/P.** Childless cohabitation does not create the same support duty as marriage. The contribution attributed to the non-debtor partner towards shared household costs cannot exceed half on the reasoning in **C38, E. 2.2–2.4**; creditors must not indirectly seize a partner's property without an underlying support entitlement. Cohabitation with common children is treated substantially like a marital family for this purpose. The packet does not establish every proportional-allocation rule for spouses or registered partners; avoid a universal 50/50 rule across those different configurations.

**SchKG93-6 — S/P.** Distinguish exempt benefits from ordinary earnings subject to a protected minimum. **C42, E. 4.6**, recognises federal and cantonal supplementary benefits as exempt; **E. 5.1** explains that exempt income can nevertheless meet needs and thereby leave more *other* income seizable. **C43, E. 2.3**, distinguishes current protected AHV/IV/EL payments from accumulated savings not used for living costs, even where retained in the same account. This is not authority to seize every account into which a pension has ever been paid. The full classification of all social-assistance and replacement-income categories remains outside the verified coverage.

**SchKG93-7 — S.** Net self-employment income requires deduction of necessary earning costs and social charges; the office examines the accounts and may estimate using suitable comparisons where necessary. Fluctuating income can require an average or assessment of actual monthly excess with an accounting obligation. **C44, E. 2.1, 2.5**. Gross business receipts are not automatically the seizable personal income.

**SchKG93-8 — P.** **C45, E. 3**, distinguishes a first attachment yielding an actual seizable quota from an initially unsuccessful attempt, and holds that merely increasing an already seizable quota through a remedy does not restart the period. Do not infer that a year extinguishes the debt or permanently exempts future income. The complete interaction of successive creditor groups and renewed seizures needs additional authority.

**SchKG93-9 — P.** Material changes should be brought to the office through a revision request; an appeal against the original decision is not a substitute for assessment of later changes. **C46, E. 3–4**. Income, household needs and supported actual expenses should be documented. The packet does not establish a universal retrospective correction date, or that submitting a request itself changes the deduction. Existing facts wrongly assessed and later changes must be distinguished.

**SchKG93-10 — P.** **C47, E. 3**, expressly points the debtor to the direct-payment mechanism under Art. 93(4), alongside the ordinary actual-payment approach. Thus C39 must not be used to say that unpaid current premiums can never be accommodated. The mechanism involves a debtor request and direct handling through the enforcement office. A complete judgment/doctrine treatment of every employer-remittance condition and cost-sharing category was not obtained; do not present this short passage as a full operational manual.

**SchKG93-11 — S.** A manifest, intolerable intrusion into the indispensable minimum can be void and therefore examinable after the normal complaint period. **C49, pp. 48–49**. Ordinary disagreement over an allowance or discretion does not automatically meet that threshold. The judgment also addresses the special position of maintenance enforcement; do not flatten all minimum-intrusion cases into one rule. If still within ten days, preserve the ordinary complaint rather than relying on nullity.

**SchKG93-12 — S.** Official fact-finding coexists with the debtor's cooperation duty. Failure to supply expense documents can leave the office to assess on the available material: **C46, E. 3**. The duty to disclose assets is broad, including items whose exempt status the office must assess: **D4, N 10–12**. The debtor should not decide unilaterally to omit assets because they seem unseizable. Criminal-warning and compulsion issues require their own conditions; **D4, N 1, 8–9**.

**SchKG93-13 — S.** A “silent” wage seizure avoiding employer notification is discretionary, not a right of the debtor. **C48, E. II.4.3**. The office assesses whether the arrangement is reliable; the debtor's wish to avoid embarrassment does not alone require it. Do not promise confidentiality from the employer as an ordinary feature of wage enforcement.

### C2. Complaint

**SchKG17-1 — S.** A reviewable act produces external procedural effects in a concrete enforcement proceeding. **C50, E. 3.1–3.2**, discusses the distinction and confirms that a mere request to reconsider does not restart a missed complaint period in the absence of a new decision/new circumstances. Use the seizure measure, communicated calculation or actual refusal as the target; a casual information letter is not automatically an appealable disposition.

**SchKG17-2 — P.** Actual knowledge sufficient to understand and challenge the measure matters; an office need not always append a formal appeal instruction: **C50, E. 3.2**. **C28, E. 4–5; C29, E. I**, address special holiday and weekend rules. Do not apply the ordinary ZPO holiday suspension indiscriminately to supervisory complaints. The complete modern Art. 145(4)/Art. 63 interaction across all categories is a remaining gap, detailed in X-3.

**SchKG17-3 — S/P.** Unlawful exercise of discretion includes irrelevant considerations and failure to consider legally material facts: **C38, E. 2.1, 2.4**. This is distinct from simply preferring another result. The supervisory complaint also addresses inappropriate measures, but the inspected Federal Supreme Court judgment must not be quoted as if it allowed unrestricted federal reconsideration of expediency.

**SchKG17-4 — P.** Zurich district courts act as lower supervisory authorities, with the Obergericht above them, as the procedural course in **C51** illustrates. Ordinary supervisory proceedings are generally free and carry no party compensation; vexatious/bad-faith litigation is an exception, **C51, E. 11**. Distinguish this from a ZPO appeal against a Rechtsöffnung judgment, which the same decision also discusses. A complete current Zurich filing-form and competence analysis was not obtained from the permitted source types; preserve the challenged act, requested correction, reasons and supporting documents for lawyer review.

**SchKG17-5 — P.** A supervisory complaint has no automatic suspensive effect; **C51, E. 11**, identifies the separate SchKG rule. Seek an express suspension where needed. The complete balancing test for granting it was not verified. Do not confuse the existence of a complaint with an instruction to the employer to stop deducting.

**SchKG17-6 — S.** A reasoned refusal is ordinarily a substantive decision that must be challenged within ten days; it does not become an indefinitely challengeable denial of justice merely because the applicant disagrees. An unjustified continuing postponement can constitute delay, however. **C52, E. 1**. The distinction prevents using “Rechtsverweigerung” to revive an expired ordinary complaint.

## D. Inheriting debts

### D1. Liability

**ZGB560-1 — P.** Universal succession makes the deceased's transmissible debts personal debts of the heirs: **C68, E. 2.2**. Distinguish those debts from obligations generated by administration/death and from public-law special regimes. **C70, E. 9.2.3–9.2.4.4**, illustrates why a charge assessed after death is not necessarily an estate-administration debt: the underlying work may have generated a transmissible claim earlier. The requested category-by-category treatment of fines, future maintenance, taxes and social-assistance recovery was not fully verified. Do not state that all public-law liabilities either pass or disappear together.

**ZGB603-1 — S.** External solidarity permits a creditor to pursue a liable heir; internal allocation does not itself bind that creditor. **C71, E. 2.2**, recognises proportional recourse by inheritance shares, including before division, with supplementary solidarity rules. The court rejected the asserted need to join every co-heir in the recourse action. The judgment's tax-debt classification discussion was partly left open; cite it for solidarity/recourse, not a universal tax rule.

**SchKG59-1 — G.** The statutory stay was checked, but a sufficiently precise current judgment/doctrine passage on enforcement against the heir during this period and the consequence of premature service was not verified. An old search result about public inventory is not enough to settle the ordinary disclaimer-period question. Do not advise an heir to ignore a payment order on the strength of the stay alone; service, objection and the stay need separate legal assessment.

**ZGB560-2 — P.** Paying an estate debt is not automatically acceptance: **C55, E. 3.2.1–3.2.3**, upheld the treatment of a nursing-home closing bill as ordinary administration on the particular facts. It did **not** establish a universal safe harbour for payment from personal funds: the creditor had failed properly to allege that estate funds were used. A distinct personal payment promise or signed acknowledgement can create separate issues under **C13, E. 2**, independently of heir status. Merely requesting information is materially different from promising payment; the final distinction is a synthesis, not a blanket court-approved script.

### D2. Disclaimer and the insolvency presumption

**ZGB566-1 — S/P.** A loss certificate can establish official insolvency evidence. Its age does not automatically deprive it of probative force: **C55, E. 3.1.1–3.1.5**, upheld reliance on a 2015 certificate for a 2021 death in light of continued supplementary benefits, pension income, nursing-home residence and absence of an intervening asset acquisition. The question is whether later financial improvement undermines the certificate, not simply whether fresh debts appeared. This is not a conclusive rule that every historic certificate establishes insolvency forever. The full treatment of bankruptcy and every form of fruitless attachment remains unverified.

**ZGB566-2 — S/P.** The decisive financial state is at death. Actual over-indebtedness alone is not the same as its obviousness. **C56, E. 2.1–2.3**, involved a heavily over-indebted estate whose deceased owner nevertheless appeared wealthy; the presumption could not be established merely by saying the heirs could theoretically have inspected company books. The party invoking obviousness/knowledge had to prove it. Documents created after death did not establish prior knowledge. The court did **not** finally resolve the abstract relationship between over-indebtedness and insolvency, nor formulate one exhaustive audience test for all situations. Preserve evidence of public appearance, official records and the relevant persons' actual knowledge rather than using “debts exceed assets” as the complete rule.

**ZGB566-3 — S/P.** The presumption can protect an heir without a constitutive express disclaimer, but its factual foundation must be established and acceptance/interference remains a separate issue: **C55, E. 3.1–3.2**. **C56, E. 2.1**, allocates proof to the party invoking the relevant presumption in that litigation; that party was not simply “always the heir”. A recorded disclaimer does not finally bind creditors on validity: **C61, E. 2.2**. A precautionary declaration may reduce avoidable dispute, but the court's recording is not a guarantee that acceptance has not already occurred.

**ZGB566-4 — P.** **C70, E. 5.1**, documents protective intervention where parents proposed disclaiming for a minor despite no established insolvency; an identified conflict led to displacement of parental representation and an inventory. That paragraph is the procedural background, **not the appeal court's principal holding on every consent requirement**. The appeal decided costs/liability. The full distinction between parental representation, a deputy's authority, conflicts and KESB consent under current law needs a direct merits authority. Do not generalise either “parents always need approval” or “parents can always disclaim unaided”.

### D3. Time limits

**ZGB567-1 — S.** For a statutory heir, reliable knowledge of death and of the person's own calling as heir matter. Knowledge of heir status is normally presumed when death becomes known; later knowledge must be proved by the person relying on it. **C58, E. 3.1.1; C63, E. 2.3**. This is distinct from knowledge of the estate's debts. The three-month period is individual to the heir. The prototype's `date_learned_of_death` is therefore a useful initial fact, but not a complete representation of every later-calling or unknown-heir-status case.

**ZGB567-2 — P.** For appointed heirs, **C58, E. 3.1.1**, identifies official notification of the testamentary provision as the relevant event. **C63, E. 2.3**, confirms individual commencement. The exact transmitted-period rules for the heirs of an heir, and each downstream calling after disclaimer, were not fully verified through a directly applicable authority. Do not start every descendant's clock on the original death date merely because the first heir's clock started then.

**ZGB567-3 — P.** **C64, E. 3**, treats prompt posting of a disclaimer after a misleadingly late court communication as protected in that concrete reliance situation. **C65, E. 2b/aa–bb**, illustrates that substantive inheritance periods and inventory requests require their own analysis. No sufficiently general verified authority was obtained establishing all month-end, weekend, posting/receipt and holiday rules for the ordinary three-month period. In particular, do not mechanically apply the full procedural ZPO suspension regime to a substantive forfeiture period. This remains a material gap for an exact deadline calculator.

**ZGB567-4 — S.** Later discovery of debt does not simply restart the ordinary clock. It may be relevant to a request for an extension/new period if the conditions are met. **C58, E. 3.1.1, 3.2–3.6**, requires diligence and timely action once sufficient information exists; the heirs could not wait until every tax consequence was finally quantified. **C54, E. 2.2**, also rejects treating ignorance of liabilities as automatically erasing interference. Keep commencement, restoration and mistake distinct.

**ZGB568-1 — P.** A protective inventory and a public inventory serve different functions. **C65, E. 2a–2b, 3**, distinguishes asset preservation from the liability-related public inventory and examines whether a protective inventory affects the **one-month request for a public inventory**. The Federal Supreme Court found Zurich's restrictive approach not arbitrary; it did not settle every disputed interpretation under unrestricted review. The ordinary Art. 568 disclaimer effect must not be extended automatically to the separate Art. 580 request. **C66, E. 1.2.2**, addresses consequences of an expiring post-inventory declaration period.

**ZGB576-1 — S.** A new period can be granted after expiry where important reasons justify it. The authority weighs the heir's ability and diligence in establishing the estate's position, personal circumstances, complexity and creditors' interest in legal certainty. It is not a general cure for negligence or a later-regretted acceptance. **C57, E. 2–4; C58, E. 3.1.1–3.1.2**. Once important reasons exist, the power is not an invitation to refuse arbitrarily; C58 describes the duty to extend/set a new period.

**Forfeiture through actual interference is a separate barrier:** extending time does not undo it, **C54, E. 2.1; C58, E. 3.1.1**. The heir must act promptly after the obstacle/uncertainty is sufficiently resolved. C57 rejected excessive delay; C58 shows that awaiting an exact eventual tax assessment is not necessarily justified. There is no verified fixed “extra three months” entitlement.

### D4. Declaration

**ZGB570-1 — S/P.** Zurich's competent authority is the single judge in summary proceedings at the deceased's last domicile: **C64, E. 2**. Oral or written declaration and recording are described in **C61, E. 2.2**. The applicant ordinarily bears the recording cost, **C60, E. VI.1; C64, E. 4**. The CHF 150 appearing in C64 is a case amount, **not a verified universal current tariff**. No general email-validity rule is established here.

**ZGB570-2 — S/P.** Conditions/reservations are excluded because disclaimer must create a clear situation for creditors and other successors. **C60, E. III.2**, distinguishes a genuine reservation from an explanatory statement: the purported reservation about forwarding insurance proceeds could be clarified as intended administration, not retention of selected assets. The result must not be reduced to “any added words invalidate the form”. A full treatment of partial disclaimer or a disclaimer in favour of a named person remains unverified.

**ZGB570-3 — S/P.** Disclaimer is a unilateral declaration, in principle irrevocable, but defects of consent can be invoked through the general rules: **C61, E. 2.1; C62, E. 2.1–2.2**. Known uncertainty is not an essential mistake; invoking mistake contrary to good faith can fail where the claimant ignored information already possessed: **C62, E. 4**. For acceptance, **C66, E. 3.4**, similarly rejects reliance on an alleged mistake where uncertainty was consciously known and notes the need to challenge the declaration before the competent authority. The complete deception/duress procedure and periods were not independently established.

**ZGB570-4 — S.** The protocol proves the making and time of the declaration, **not its substantive effectiveness against creditors**. Even a declaration that is late or affected by forfeiture can be recorded. The authority has limited preliminary cognition where consequential measures depend on validity; ordinary litigation can still resolve the disputed heir liability. **C61, E. 2.2; C54, E. 2–2.1**. Therefore “the court accepted my form” must not be equated with a final judgment that no creditor can sue.

### D5. Loss of the disclaimer right

**ZGB571-1 — S/P.** The starting point is the objective character of the conduct and whether it exceeds required administration/preservation. An intention specifically to accept the inheritance is not invariably necessary, but knowledge that the affected asset belongs to the estate matters. **C59, E. III.3.1–3.2**, explains the objective approach, the subjective ownership-knowledge element and the scholarly disagreement. **C53, E. 3.1, 3.3.1–3.3.2**, requires context and avoids an excessively narrow view of permissible administration; **C55, E. 3.2.1**, reaffirms the individual assessment. The system should collect the act, purpose, urgency, funds, beneficiary and knowledge, then refer under R5 rather than declare automatic acceptance.

**ZGB571-2 — S/P.** Preserving value and continuing necessary business can remain administration. **C59, E. III.3.1**, gives examples including urgent repairs and dealing with due claims; these examples must be read with the circumstances. **C57, E. 3**, upheld treating clearance of modest household effects required in connection with sale as permissible under the applicable review standard. **C60, E. III.3, pp. 7–9**, discusses funeral/urgent bill administration and expressly cautions that paying selected creditors in an insolvent estate is not invariably harmless.

The recent concrete example is **C55, E. 3.2.2–3.2.3**: the nursing-home closing payment avoided further costs and conferred no personal benefit on the heir. The court upheld its classification as ordinary administration. This does not establish blanket permission to liquidate the household, terminate every contract, pay oneself or select favoured creditors.

**ZGB571-3 — P.** **C59, E. III.3.1**, distinguishes worthless or very minor items from acts demonstrating appropriation. It does not fix a CHF safe harbour. **C60, E. III.3, p. 9**, found no established forfeiting appropriation where openly withdrawn funds were preserved for specified payments and, after the dispute arose, were to be returned or made available to the bankruptcy office. **That is not a holding that returning assets cures an appropriation which already forfeited the right.** A direct authority on undoing completed appropriation/concealment remains missing. Sentimental value, market value, disclosure and intended use must be recorded separately.

**ZGB571-4 — P.** The funding source and purpose are material, but no binary safe rule follows. **C55, E. 3.2.2–3.2.3**, turned partly on failure properly to allege estate-fund use. **C60, E. III.3**, involved actual account withdrawals for forwarding medical/benefit amounts yet still required contextual assessment. The treatment of private use of the deceased's vehicle, subscriptions or accounts is not directly decided by those facts. Do not translate “account used” into automatic acceptance or “own money” into automatic immunity.

**ZGB571-5 — S/P.** Distinguish **knowledge of ownership**, **knowledge of debt**, and **knowledge of legal consequences**. **C59, E. III.3.1–3.2**, makes ownership knowledge relevant; an heir who plausibly believed shares already belonged to him was not treated as knowingly disposing of estate property. **C54, E. 2.2**, does not allow ignorance of estate debts automatically to remove interference, and leaves the separate mistake issue unresolved on that record. **C62, E. 2.2, 4; C66, E. 3.4**, establish limits on mistake where uncertainty was known or pertinent information ignored. A blanket rule about ignorance of the legal right to disclaim was not verified. Good faith is not a general exemption from the consequences of every voluntary act.

**ZGB571-6 — P.** **C55, E. 3.2.2–3.2.3**, shows that the creditor alleging interference cannot fill an allegation/proof gap about estate-fund use for the first time on appeal. **C59, E. III.3.1–3.2**, evaluates ownership knowledge and the evidence. These are useful evidential holdings, but a complete abstract burden allocation and proof standard for each alternative—interference, appropriation, concealment—was not independently verified. Do not label mere suspicion “proved interference”.

**ZGB571-7 — S/P.** Applying for an inheritance certificate **alone** is not necessarily interference. Purpose and context matter, notably whether the certificate is required for an act within administration or an act exercising ownership. **C53, E. 3.3.1**. Necessary executor actions are also distinguished in **E. 3.3.2**. The judgment does not specifically decide every bank-information request, postal collection or death registration. Those actions should be assessed by the same contextual framework, expressly as an analogy rather than an enumerated holding.

**ZGB571-8 — S/P.** Late-discovered liabilities can support a new-period request in a sufficiently diligent case, but not automatic reopening: **C57, E. 2–4; C58, E. 3.1.1–3.1.2**. Existing interference bars that time remedy. Challenge for a qualifying mistake is conceptually separate; **C66, E. 3.4**, confirms the need for an actual essential mistake and proper challenge. The packet does not establish that every acceptance by mere lapse of time can be rescinded on the same terms as an express declaration. That specific issue remains open for further verification.

**ZGB571-9 — S/P.** **C60, E. IV**, expressly refused to attribute one brother's declaration/actions to the other without evidence of the latter's interference. Each heir's position must be examined. **C53, E. 3.2**, discusses the shared effect of a public-inventory request but leaves aspects concerning an already accepting co-heir open; that must not be converted into a collective-acceptance rule. Authorised representation or joint acts would need their own analysis.

### D6. Consequences and alternatives

**ZGB572-1 — S/P.** Individual disclaimer normally treats the disclaiming heir as predeceased for the distribution of that share; where all closest heirs disclaim, the special bankruptcy-liquidation regime intervenes. **C67, E. 5.1**. Hence “children always inherit next and must all disclaim” is unsafe without checking whether this is individual substitution or disclaimer by the whole closest class. The exact later-called heir's commencement rules remain partly unverified as noted under ZGB567-2.

**ZGB573-1 — S/P.** If all closest heirs disclaim, bankruptcy liquidation is the relevant route. **C67, E. 5.1, 5.4**, also explains that a surplus is distributed as though disclaimer had not occurred, including the position of an appointed heir on the facts. **C60, E. III.3, p. 9**, requires preserved estate money to be returned/made available to the bankruptcy office. These holdings do not authorise disclaiming relatives to dispose freely of household assets. Funeral liability can arise on distinct contractual/public-law bases; the full requested allocation and post-disclaimer clearance duties were not verified.

**ZGB574-1 — G.** No sufficiently specific judgment or directly inspected doctrinal passage was obtained on the spouse's special position and the separate invitation procedure for subsequent heirs, including the precise one-month effects. Do not merge this mechanism with ordinary descent/substitution under Art. 572 or the all-closest-heirs rule in Art. 573.

**ZGB579-1 — S/P.** Disclaimer does not necessarily eliminate liability for qualifying pre-death transfers. **C68, E. 2.2–2.3**, describes a subsidiary statutory value liability for transfers received within the preceding five years that would be subject to collation; it is not necessary first to invalidate the disclaimer or establish an intent to prejudice creditors. Liability covers what remains unavailable from accepting heirs or the estate. The bankruptcy estate can assert it. The complete treatment of customary endowments, dispensation from collation and good-faith enrichment limits was not fully verified in the inspected passages; retain those as separate issues.

**ZGB580-1 — S/P.** Public inventory may help where liabilities are uncertain and the heir needs the protected election, but it is **not** a universal cap of liability at the value inherited. **C70, E. 7.3–7.4.2**, explains personal liability, including own assets, for inventoried debts, exclusion of culpably unregistered claims and important exceptions. **C65, E. 2b**, addresses the short one-month request and the distinction from a protective inventory. **C69, E. 3a–3b**, distinguishes costs of a later bankruptcy opened at the authority's request from costs imposed because the heir personally requested bankruptcy liquidation. The current Zurich inventory advance/fee scale was not verified. Do not wait for the three-month disclaimer period before considering the one-month inventory request.

**ZGB588-1 — P.** Silence after the post-inventory election period can produce acceptance under inventory; **C66, E. 1.2.2**, discusses that consequence and the loss of a practical interest in challenging the inventory. **E. 3.4** addresses the limited ability to undo an acceptance declaration. This is not an indefinite opportunity to wait for all disputed assets or debts to be resolved. The full four-option election and every extension condition were not independently established in a single inspected merits passage.

**ZGB593-1 — P.** **C69, E. 3a**, confirms the distinction between official liquidation requested under inheritance law and an heir personally requesting bankruptcy liquidation; the cost consequences differ. A complete merits authority on eligibility, acceptance by a co-heir and all blocking acts was not verified. An Obwalden search hit contained inconsistent date metadata and was excluded rather than presented as a secure citation. The official-liquidation route should remain a lawyer-assessed alternative, not an automatic recommendation after an effective disclaimer.

## E. Cross-cutting questions

**X-1 — S/P.** Credibility is a lower threshold than full proof: objective indications can suffice even though other possibilities remain. **C14, E. 4.1.2**. **C26, E. 3.1.1–3.1.2**, expressly applies credibility to objections caused by a creditor change. **C25, E. 3.1**, uses credibility for the faultless procedural impediment. **D3, N 12–14**, addresses register-access interest. Do not replace these context-specific tests with one invented numerical probability or reverse the burden simply because credibility is sufficient.

**X-2 — S.** An ordinary unlawful act is generally challengeable within its period; only the more serious nullity category escapes that limitation. The concrete tested categories here are manifest/intolerable deprivation of the necessary minimum (**C49**) and exceptional abusive enforcement (**C27**). Defective service can instead be cured by actual knowledge (**C20**) or remain ineffective where no legally sufficient service/knowledge occurred (**C21**). Classification changes the remedy and time consequences; the mere strength of disagreement with the office does not establish nullity.

**X-3 — P.** Keep four tracks separate: (1) acts towards the enforcement office; (2) supervisory complaints; (3) judicial SchKG litigation under the applicable ZPO procedure; (4) substantive inheritance election periods. **C28, E. 4–5**, demonstrates that enforcement holidays are not a general clock suspension; **C29, E. I**, applies the weekend rule through Art. 31; **C52, E. 1**, distinguishes bankruptcy-related timing; **C65**, separates inheritance periods. A complete verified matrix of all starts, holidays, extensions, restoration and filing channels is **not** established here. The prototype should flag urgency and preserve dates, not produce a definitive deadline from a single universal function.

**X-4 — P; synthesis.** The safer information-gathering response distinguishes the alleged claim, its documents and the person's undecided heir status, without asserting a personal payment undertaking or exercising ownership over estate assets. This is an inference from **C13, C53–C55, C59–C60**, not a court-approved standard form. Preserve the letter, deadline and payment order, if any; a response to the creditor does not replace an objection to the office. Paying, signing an instalment plan, taking funds or paying oneself requires a specific assessment of both inheritance consequences and any independent acknowledgement.

**X-5 — P.** **C73, E. 4**, supports the legal-aid framework of insufficient means and a case not devoid of prospects; the process-cost minimum is distinct from the enforcement minimum. Free supervisory proceedings are addressed in **C51, E. 11**, but that does not automatically provide a free lawyer. A current directory of Zurich debt-counselling services, opening hours or eligibility cannot responsibly be established from judgments and doctrine alone. No generic advice-site directory has been substituted for the requested source types.

## F. Verified source register

Each entry identifies the judgment actually inspected, its relevant consideration or page, and the question IDs that cite it. **E.** means *Erwägung/considérant*; **N** means a doctrinal marginal number. Dates are judgment dates, not upload dates. A BGE publication year can differ from the judgment year. The links labelled “Judgment text” open the judgment reproduced in Lexplorer; they are primary judicial texts, not legal-information articles. An additional public PDF is given where directly inspected. A database chunk number is not substituted for a judgment's own numbering.

Short quotations below were checked against the retrieved original-language text with whitespace normalisation. They are **passage candidates**, not complete statements of every qualification: retain the answer and scope note when using them. The source importer has not been run.

### C01 — BGE 129 III 535, Urteil vom 16.05.2003

**Pinpoint:** E. 3.1–3.2.2. [Judgment text](https://law.lexplorer.ch/s/d/bge_BGE_129_III_535).

Default interest, maturity and content of a reminder.

**Original passage (E. 3.2.2):**

> Mit der Mahnung muss die zu erbringende Leistung so genau bezeichnet werden, dass der Schuldner erkennt, was der Gläubiger fordern will.

**Question IDs:** OR102-1, OR102-3, OR103-1, OR104-1, OR104-3, OR106-4.

### C02 — BGer, Urteil 4A_78/2023 vom 12.07.2023

**Pinpoint:** E. 3.1.3–3.1.4. [Judgment text](https://law.lexplorer.ch/s/d/bger_4A_78_2023).

Receipt of a reminder; creditor's burden; service of a pleading.

**Question IDs:** OR102-1, OR102-4, OR104-1.

### C03 — BGE 123 III 241, Urteil vom 07.05.1997

**Pinpoint:** E. 3a and 4b. [Judgment text](https://law.lexplorer.ch/s/d/bge_BGE_123_III_241).

Proof of additional default loss; overall crediting of default interest.

**Original passage (E. 4b):**

> Der Verspätungsschaden nach Art. 106 OR tritt nicht kumulativ hinzu, sondern wird nur dann geschuldet, wenn er die Verzugszinse übersteigt.

**Question IDs:** OR106-2, OR106-4, OR106-5.

### C04 — BGer, Urteil 4C.11/2003 vom 19.05.2003

**Pinpoint:** E. 5.2. [Judgment text](https://law.lexplorer.ch/s/d/bger_4C.11_2003).

Necessary, appropriate and uncompensated expenses of pursuing an existing claim.

**Original passage (E. 5.2):**

> Notwendig und angemessen sind Kosten zur Durchsetzung streitiger Forderungen nur insoweit, als diese Forderungen auch bestehen

**Question IDs:** OR103-1, OR106-1, OR106-3, OR106-4.

### C05 — BGer, Urteil 4A 264/2015 vom 10.08.2015

**Pinpoint:** E. 3 and 4.2.2. [Judgment text](https://law.lexplorer.ch/s/d/bger_4A_264_2015).

Concrete pleading of pre-litigation lawyer costs; a bill alone is insufficient.

**Original passage (E. 4.2.2):**

> Der blosse Verweis auf Beilagen zur Klage erfüllt die Behauptungslast in aller Regel nicht

**Question IDs:** OR106-1, OR106-2, OR106-3.

### C06 — BGer, Urteil 4A 501/2021 vom 22.02.2022

**Pinpoint:** E. 9.2.2. [Judgment text](https://law.lexplorer.ch/s/d/bger_4A_501_2021).

Pre-litigation work normally absorbed by procedural party compensation.

**Question IDs:** OR106-1, OR106-3.

### C07 — BGE 148 III 57, Urteil vom 05.01.2022

**Pinpoint:** E. 2.1.1–2.1.3.3. [Judgment text](https://law.lexplorer.ch/s/d/bge_BGE_148_III_57).

AGB incorporation and subjective/objective unusualness; general doctrine, not a collection-fee holding.

**Original passage (E. 2.1.3):**

> Entsprechend sind von der global erklärten Zustimmung alle ungewöhnlichen Klauseln ausgenommen, auf deren Vorhandensein die zustimmende Partei nicht gesondert aufmerksam gemacht worden ist

**Question IDs:** OR102-2, OR104-2, OR106-6.

### C08 — BGE 103 II 129, Urteil vom 05.04.1977

**Pinpoint:** E. 4. [Judgment text](https://law.lexplorer.ch/s/d/bge_BGE_103_II_129).

Discretion and restraint in reducing excessive contractual penalties.

**Question IDs:** OR106-7.

### C09 — BGer, Urteil 4A_601/2015 vom 19.04.2016

**Pinpoint:** E. 2.3.3. [Judgment text](https://law.lexplorer.ch/s/d/bger_4A_601_2015).

Analogous reduction of liquidated damages.

**Question IDs:** OR106-7.

### C10 — BGE 134 III 591, Urteil vom 01.10.2008

**Pinpoint:** E. 5.2.1–5.2.4. [Judgment text](https://law.lexplorer.ch/s/d/bge_BGE_134_III_591).

Acknowledgement by payment on account versus an expressly final payment.

**Question IDs:** OR106-9, OR106-11.

### C11 — BGE 133 III 598, Urteil vom 28.08.2007

**Pinpoint:** E. 4.2.1–4.2.3. [Judgment text](https://law.lexplorer.ch/s/d/bge_BGE_133_III_598).

Payment allocation where interest or costs are genuinely disputed.

**Question IDs:** OR106-10.

### C12 — Obergericht Zürich, RT180012, 13.04.2018

**Pinpoint:** E. 6.1, pp. 5–8. [Judgment text](https://law.lexplorer.ch/s/d/zh_obergericht_RT180012).

Art. 27 office proceedings distinguished from judicial Rechtsöffnung and its party costs.

**Question IDs:** SchKG27-1, SchKG27-2, SchKG68-1.

### C13 — BGE 136 III 627, Urteil vom 09.11.2010

**Pinpoint:** E. 2 and 3.3. [Judgment text](https://law.lexplorer.ch/s/d/bge_BGE_136_III_627).

Signed, definite acknowledgement and incorporated documents; silence alone is insufficient.

**Original passage (E. 2):**

> Dabei kann sich die Schuldanerkennung auch aus einer Gesamtheit von Urkunden ergeben, sofern die notwendigen Elemente daraus hervorgehen.

**Question IDs:** OR106-9, SchKG82-1, SchKG82-3, ZGB560-2, X-4.

### C14 — BGE 132 III 140, Urteil vom 07.10.2005

**Pinpoint:** E. 4.1.1–4.1.2. [Judgment text](https://law.lexplorer.ch/s/d/bge_BGE_132_III_140).

Documentary title, creditor succession and credibility of the debtor's defences.

**Question IDs:** OR106-8, OR106-9, SchKG74-8, SchKG79-1, SchKG82-2, X-1.

### C15 — BGE 148 III 225, Urteil vom 31.03.2022

**Pinpoint:** E. 4.2.4. [Judgment text](https://law.lexplorer.ch/s/d/bge_BGE_148_III_225).

Ancillary interest in definitive Rechtsöffnung; distinguish separate fees and other claims.

**Question IDs:** OR104-1, SchKG82-3.

### C16 — BGer, Urteil 5D 23/2017 vom 08.05.2017

**Pinpoint:** E. 4.3.3. [Judgment text](https://law.lexplorer.ch/s/d/bger_5D_23_2017).

The collection charge is not a procedural outlay under Art. 95 ZPO. This is not a merits finding that it is owed.

**Question IDs:** SchKG82-3.

### C17 — Obergericht Bern, SK 2022 324 / SK 2022 325, 30.08.2023

**Pinpoint:** E. 15.3.2–15.5, pp. 39–43. [Judgment text](https://law.lexplorer.ch/s/d/be_zivilstraf_SK_2022_324).

Extreme coercive collection practices in criminal proceedings. E. 15.3.1 reports the lower court's assessment.

[Inspected judgment PDF](https://entscheidsuche.ch/docs/BE_ZivilStraf/BE_OG_005_SK-2022-324_2023-08-30.pdf).

**Question IDs:** OR106-9, OR106-12.

### C18 — BGE 109 III 1, Urteil vom 28.03.1983

**Pinpoint:** E. 2a–c. [Judgment text](https://law.lexplorer.ch/s/d/bge_BGE_109_III_1).

Substitute service and refusal. Its historical reference to the old Art. 77 restoration route must not be used as current procedure.

**Original passage (E. 2, opening paragraph):**

> so kann die Zustellung an eine zu seiner Haushaltung gehörende erwachsene Person oder an einen Angestellten geschehen

**Question IDs:** SchKG74-1.

### C19 — BGE 150 III 223, Urteil vom 20.03.2024

**Pinpoint:** E. 3.2.3. [Judgment text](https://law.lexplorer.ch/s/d/bge_BGE_150_III_223).

Invitation to collect at the enforcement office is not service; no obligation to collect there. Postal second delivery is addressed in C75.

**Original passage (E. 3.2.3):**

> Die Abholungseinladung ist eine blosse Mitteilung, dass der Zahlungsbefehl für den Betriebenen bereit liegt

**Question IDs:** SchKG74-1.

### C20 — BGE 120 III 114, Urteil vom 20.10.1994

**Pinpoint:** E. 3b–c. [Judgment text](https://law.lexplorer.ch/s/d/bge_BGE_120_III_114).

Cure through actual knowledge and informal objection.

**Question IDs:** SchKG74-2, SchKG74-5, X-2.

### C21 — BGE 117 III 7, Urteil vom 26.04.1991

**Pinpoint:** E. 3a–c. [Judgment text](https://law.lexplorer.ch/s/d/bge_BGE_117_III_7).

Telephone announcement of refusal and mailbox delivery do not establish valid service.

**Original passage (E. 3c):**

> Die fehlerhafte Zustellung der Zahlungsbefehle ist eine nichtige Betreibungshandlung, die von Amtes wegen jederzeit festgestellt werden kann und muss

**Question IDs:** SchKG74-1, SchKG74-2, X-2.

### C22 — BGer, Urteil 5A_870/2019 vom 17.06.2020

**Pinpoint:** E. 2.3–2.4. [Judgment text](https://law.lexplorer.ch/s/d/bger_5A_870_2019).

Informal objection versus formal withdrawal.

**Question IDs:** SchKG74-4.

### C23 — BGE 89 III 10, Urteil vom 23.04.1963

**Pinpoint:** Unnumbered consideration, pp. 10–11. [Judgment text](https://law.lexplorer.ch/s/d/bge_BGE_89_III_10).

A precisely calculable fee-only objection can suffice without stating numerals.

**Original passage (pp. 10–11):**

> Diese sagt nicht, der Schuldner habe den bestrittenen Teilbetrag ziffermässig, sondern nur, er habe ihn genau anzugeben.

**Question IDs:** SchKG74-7.

### C24 — BGer, Urteil 5A_673/2017 vom 22.03.2018

**Pinpoint:** E. 2.3.1–2.3.2. [Judgment text](https://law.lexplorer.ch/s/d/bger_5A_673_2017).

Strict faultlessness; illness, representation and commencement of restoration period.

**Original passage (E. 2.3.1):**

> Das Fristversäumnis muss im Rahmen von Art. 33 Abs. 4 SchKG gänzlich schuldlos gewesen sein

**Question IDs:** OR103-1, SchKG33-1.

### C25 — BGer, Urteil 5A_87/2018 vom 21.09.2018

**Pinpoint:** E. 3.1. [Judgment text](https://law.lexplorer.ch/s/d/bger_5A_87_2018).

Restoration; non-appointed household recipient distinguished from a procedural representative.

**Question IDs:** SchKG74-1, SchKG33-1, X-1.

### C26 — BGer, Urteil 5A_736/2017 vom 08.06.2018

**Pinpoint:** E. 3.1–3.1.2. [Judgment text](https://law.lexplorer.ch/s/d/bger_5A_736_2017).

Late objection after a creditor change; credibility of change-related defences.

**Question IDs:** SchKG77-1, X-1.

### C27 — BGE 140 III 481, Urteil vom 19.09.2014

**Pinpoint:** E. 2.3.1. [Judgment text](https://law.lexplorer.ch/s/d/bge_BGE_140_III_481).

Exceptional nullity for abusive enforcement; no supervisory trial of the debt's merits.

**Original passage (E. 2.3.1):**

> Allerdings steht es weder dem Betreibungsamt noch der Aufsichtsbehörde zu, die Begründetheit der in Betreibung gesetzten Forderung zu beurteilen.

**Question IDs:** OR106-12, SchKG74-9, SchKG8a-2, X-2.

### C28 — BGE 115 III 6, Urteil vom 20.01.1989

**Pinpoint:** E. 4–5. [Judgment text](https://law.lexplorer.ch/s/d/bge_BGE_115_III_6).

Enforcement holidays and expiry extension are not a general suspension of all periods.

**Question IDs:** SchKG74-3, SchKG17-2, X-3.

### C29 — Tribunal cantonal vaudois, Cour des poursuites et faillites, Plainte/2016/18, 10.03.2016

**Pinpoint:** E. I, II.a–b and III. [Judgment text](https://law.lexplorer.ch/s/d/vd_findinfo_Plainte___2016___18).

Sunday expiry; oral objection and proof; express no-new-assets objection.

**Question IDs:** SchKG74-3, SchKG74-4, SchKG74-5, SchKG75-1, SchKG17-2, X-3.

### C30 — Obergericht Zug, BA 2025 50, 16.09.2025

**Pinpoint:** pp. 3–4. [Judgment text](https://law.lexplorer.ch/s/d/zg_obergericht_BA_2025_50).

Authority to lodge an objection and alternative subsequent ratification. Page numbers, not the database's artificial chunk labels.

**Question IDs:** SchKG74-6.

### C31 — Obergericht Zürich, RT220209, 12.07.2023

**Pinpoint:** pp. 21–22. [Judgment text](https://law.lexplorer.ch/s/d/zh_obergericht_RT220209).

Recovery following payment without objection; not an automatic substantive acknowledgement.

**Question IDs:** SchKG74-8, SchKG86-1.

### C32 — BGer, Urteil 4A_580/2019 vom 16.04.2020

**Pinpoint:** E. 3.3. [Judgment text](https://law.lexplorer.ch/s/d/bger_4A_580_2019).

Art. 85a after the 2019 amendment; interim suspension. Read with the limited arbitrariness review in this appeal.

**Question IDs:** SchKG85-1, SchKG8a-8.

### C33 — BGE 141 III 68, Urteil vom 16.01.2015

**Pinpoint:** E. 2.7. [Judgment text](https://law.lexplorer.ch/s/d/bge_BGE_141_III_68).

Interest in declaratory proceedings after enforcement. The old restriction on Art. 85a is superseded.

**Question IDs:** SchKG8a-8.

### C34 — BGE 147 III 486, Urteil vom 23.07.2021

**Pinpoint:** E. 3.4; contrast E. 3.2. [Judgment text](https://law.lexplorer.ch/s/d/bge_BGE_147_III_486).

Payment after service does not alone trigger non-disclosure. The unsuccessful-proceeding discussion must be updated for 2026.

**Question IDs:** SchKG8a-3, SchKG8a-4.

### C35 — BGE 150 III 390, Urteil vom 29.08.2024

**Pinpoint:** E. 3.3 and 4.1–4.5. [Judgment text](https://law.lexplorer.ch/s/d/bge_BGE_150_III_390).

Payment before service, including after the enforcement request, distinguished from payment after service.

**Question IDs:** SchKG8a-2, SchKG8a-3, SchKG8a-4.

### C36 — Kantonsgericht Schwyz, BEK 2025 174, 27.02.2026

**Pinpoint:** E. 3b/cc–ff. [Judgment text](https://law.lexplorer.ch/s/d/sz_gerichte_BEK%202025%20174).

2026 revision and temporal application; renewed request under new law.

**Question IDs:** SchKG8a-4, SchKG8a-6, SchKG8a-9.

### C37 — Obergericht Solothurn, Aufsichtsbehörde für Schuldbetreibung und Konkurs, SCBES.2026.116, 27.10.2026

**Pinpoint:** E. II.2.1–II.3. [Judgment text](https://law.lexplorer.ch/s/d/so_gerichte_SCBES.2026.116).

2026 non-disclosure test; litigation must concern enforcement of the same monetary claim.

**Question IDs:** SchKG79-1, SchKG8a-4, SchKG8a-5, SchKG8a-6, SchKG8a-9.

### C38 — BGE 130 III 765, Urteil vom 10.09.2004

**Pinpoint:** E. 2.1–2.4. [Judgment text](https://law.lexplorer.ch/s/d/bge_BGE_130_III_765).

Discretion, cohabitation, household costs and individual assessment. Historic CHF allowances are not current rates.

**Question IDs:** SchKG93-1, SchKG93-2, SchKG93-5, SchKG17-3.

### C39 — BGE 121 III 20, Urteil vom 29.03.1995

**Pinpoint:** E. 3b–c. [Judgment text](https://law.lexplorer.ch/s/d/bge_BGE_121_III_20).

Actual payment of minimum-budget expenses; qualify the older insurance rule using C47.

**Question IDs:** SchKG93-3, SchKG93-10.

### C40 — BGE 129 III 526, Urteil vom 17.07.2003

**Pinpoint:** E. 2–2.3. [Judgment text](https://law.lexplorer.ch/s/d/bge_BGE_129_III_526).

Reduction of excessive housing costs after an appropriate transition.

**Original passage (E. 2):**

> Dem Schuldner ist die Möglichkeit zu geben, seine Wohnkosten innert einer angemessenen Frist den für die Berechnung des Notbedarfs massgebenden Verhältnissen anzupassen

**Question IDs:** SchKG93-3.

### C41 — BGE 140 III 337, Urteil vom 22.05.2014

**Pinpoint:** E. 4.4.1–4.4.3 and 5.2. [Judgment text](https://law.lexplorer.ch/s/d/bge_BGE_140_III_337).

Taxes and necessary leased vehicles in the enforcement minimum.

**Question IDs:** SchKG93-1, SchKG93-3, SchKG93-4.

### C42 — BGE 135 III 20, Urteil vom 04.09.2008

**Pinpoint:** E. 4.6 and 5.1. [Judgment text](https://law.lexplorer.ch/s/d/bge_BGE_135_III_20).

Exempt supplementary benefits and the attachable share of other income.

**Question IDs:** SchKG93-6.

### C43 — BGE 150 III 408, Urteil vom 02.08.2024

**Pinpoint:** E. 2.3. [Judgment text](https://law.lexplorer.ch/s/d/bge_BGE_150_III_408).

Accumulated savings from exempt social benefits can become attachable assets.

**Question IDs:** SchKG93-6.

### C44 — BGer, Urteil 5A_1/2017 vom 07.07.2017

**Pinpoint:** E. 2.1 and 2.5. [Judgment text](https://law.lexplorer.ch/s/d/bger_5A_1_2017).

Self-employment, net income, accounts, estimates and fluctuation.

**Original passage (E. 2.1):**

> Gepfändet wird das Nettoeinkommen, soweit es das Existenzminimum des Schuldners und seiner Familie übersteigt.

**Question IDs:** SchKG93-7.

### C45 — BGE 116 III 15, Urteil vom 20.04.1990

**Pinpoint:** E. 3. [Judgment text](https://law.lexplorer.ch/s/d/bge_BGE_116_III_15).

Annual attachment period starts with an actual seizure; increasing a quota does not restart it.

**Question IDs:** SchKG93-8.

### C46 — BGE 108 III 10, Urteil vom 08.02.1982

**Pinpoint:** E. 3–4. [Judgment text](https://law.lexplorer.ch/s/d/bge_BGE_108_III_10).

Office investigation, cooperation and revision after changed circumstances.

**Question IDs:** SchKG93-9, SchKG93-12.

### C47 — Obergericht Solothurn, Aufsichtsbehörde für Schuldbetreibung und Konkurs, SCBES.2026.49, 28.05.2026

**Pinpoint:** E. 3. [Judgment text](https://law.lexplorer.ch/s/d/so_gerichte_SCBES.2026.49).

Direct payment of current compulsory health-insurance premiums under Art. 93(4).

**Question IDs:** SchKG93-10.

### C48 — Obergericht Solothurn, Aufsichtsbehörde für Schuldbetreibung und Konkurs, SCBES.2026.70, 15.09.2026

**Pinpoint:** E. II.2.6 and II.4.3. [Judgment text](https://law.lexplorer.ch/s/d/so_gerichte_SCBES.2026.70).

Disproportionate rent-prepayment condition; no entitlement to a silent wage attachment.

**Original passage (E. II.4.3):**

> Ein Anspruch auf eine stille Lohnpfändung besteht nicht.

**Question IDs:** SchKG93-3, SchKG93-13.

### C49 — BGE 105 III 48, Urteil vom 06.09.1979

**Pinpoint:** pp. 48–49. [Judgment text](https://law.lexplorer.ch/s/d/bge_BGE_105_III_48).

Exceptional nullity where seizure intolerably undermines the minimum; maintenance-creditor qualification.

**Question IDs:** SchKG93-11, X-2.

### C50 — BGE 142 III 643, Urteil vom 17.08.2016

**Pinpoint:** E. 3.1–3.2. [Judgment text](https://law.lexplorer.ch/s/d/bge_BGE_142_III_643).

Reviewable office decision; reconsideration does not simply reopen a missed complaint period.

**Question IDs:** SchKG17-1, SchKG17-2.

### C51 — Obergericht Zürich, PS200237, 15.12.2020

**Pinpoint:** E. 1 and 11. [Judgment text](https://law.lexplorer.ch/s/d/zh_obergericht_PS200237).

Zurich supervisory route and costs; distinguish the judgment's judicial Rechtsöffnung-appeal context.

**Question IDs:** SchKG17-4, SchKG17-5, X-5.

### C52 — BGE 88 III 28, Urteil vom 28.02.1962

**Pinpoint:** E. 1. [Judgment text](https://law.lexplorer.ch/s/d/bge_BGE_88_III_28).

Reasoned refusal versus denial of justice or indefinite delay; procedural context matters.

**Question IDs:** SchKG17-6, X-3.

### C53 — BGE 133 III 1, Urteil vom 23.08.2006

**Pinpoint:** E. 3.1–3.3.2. [Judgment text](https://law.lexplorer.ch/s/d/bge_BGE_133_III_1).

Estate interference; certificate request alone is insufficient; protective administration and inventory. Other alleged acts required separate examination.

**Original passage (E. 3.3.1):**

> Daraus folgt, dass die Tatsache des Einholens einer Erbenbescheinigung für sich allein keine Einmischung bedeutet.

**Question IDs:** ZGB571-1, ZGB571-7, ZGB571-9, X-4.

### C54 — BGer, Urteil 4A_394/2014 vom 01.12.2014

**Pinpoint:** E. 2–2.2. [Judgment text](https://law.lexplorer.ch/s/d/bger_4A_394_2014).

Disclaimer record does not conclusively settle material validity; interference bars extension.

**Question IDs:** ZGB567-4, ZGB576-1, ZGB570-4, ZGB571-5, X-4.

### C55 — BGer, Urteil 4A_110_2026 vom 03.07.2026

**Pinpoint:** E. 3.1.1–3.1.5 and 3.2.1–3.2.3. [Judgment text](https://law.lexplorer.ch/s/d/bger_4A_110_2026).

Evidence of insolvency and ordinary administration through payment of a nursing-home final bill; narrow facts matter.

**Original passage (E. 3.2.1):**

> Die Beurteilung, ob eine Handlung als eine Verwaltungs- oder Einmischungshandlung zu qualifizieren ist, hat aufgrund der Umstände im Einzelfall zu erfolgen

**Question IDs:** ZGB560-2, ZGB566-1, ZGB566-3, ZGB571-1, ZGB571-2, ZGB571-4, ZGB571-6, X-4.

### C56 — BGer, Urteil 5A 97/2014 vom 23.10.2014

**Pinpoint:** E. 2.1–2.3. [Judgment text](https://law.lexplorer.ch/s/d/bger_5A_97_2014).

Burden and evidence concerning obvious insolvency or heirs' knowledge at death.

**Question IDs:** ZGB566-2, ZGB566-3.

### C57 — BGE 114 II 220, Urteil vom 20.07.1988

**Pinpoint:** E. 2–4. [Judgment text](https://law.lexplorer.ch/s/d/bge_BGE_114_II_220).

Equitable extension, modest household clearance and prompt action after the obstacle ends.

**Question IDs:** ZGB576-1, ZGB571-2, ZGB571-8.

### C58 — BGer, Urteil 5A_823/2023 vom 05.03.2024

**Pinpoint:** E. 3.1.1–3.1.2 and 3.2–3.6. [Judgment text](https://law.lexplorer.ch/s/d/bger_5A_823_2023).

Commencement, diligence, just reasons, creditors' interests and inheritance-period extension.

**Original passage (E. 3.1.1):**

> La prolongation ou la restitution exigent la preuve d'un juste motif

**Question IDs:** ZGB567-1, ZGB567-2, ZGB567-4, ZGB576-1, ZGB571-8.

### C59 — Obergericht Zürich, LB140092, 01.06.2015

**Pinpoint:** E. III.3.1–III.4. [Judgment text](https://law.lexplorer.ch/s/d/zh_obergericht_LB140092).

Ownership knowledge, estate interference and prompt extension application.

**Question IDs:** ZGB571-1, ZGB571-2, ZGB571-3, ZGB571-5, ZGB571-6, X-4.

### C60 — Obergericht Zürich, LF120057, 03.10.2012

**Pinpoint:** E. III.2–III.3, pp. 5–9; IV and VI.1. [Judgment text](https://law.lexplorer.ch/s/d/zh_obergericht_LF120057).

Clarifying reservation, medical bill paid from estate account, individual attribution and fees. No blanket permission to distribute an insolvent estate.

**Question IDs:** ZGB570-1, ZGB570-2, ZGB571-2, ZGB571-3, ZGB571-4, ZGB571-9, ZGB573-1, X-4.

### C61 — BGer, Urteil 5A_398/2021 vom 07.01.2022

**Pinpoint:** E. 2.1–2.4. [Judgment text](https://law.lexplorer.ch/s/d/bger_5A_398_2021).

Irrevocability, mistake, recording versus material validity and cantonal procedure.

**Original passage (E. 2.1):**

> Sie wird in der Lehre fast einhellig als prinzipiell unwiderruflich bezeichnet.

**Question IDs:** ZGB566-3, ZGB570-1, ZGB570-3, ZGB570-4.

### C62 — BGer, Urteil 5A 594/2009 vom 20.04.2010

**Pinpoint:** E. 2.1–2.2, 4 and 5. [Judgment text](https://law.lexplorer.ch/s/d/bger_5A_594_2009).

Mistake, accepted uncertainty, good faith and negligent failure to investigate.

**Question IDs:** ZGB570-3, ZGB571-5.

### C63 — Obergericht Zürich, LF240127, 23.01.2025

**Pinpoint:** E. 2.3. [Judgment text](https://law.lexplorer.ch/s/d/zh_obergericht_LF240127).

Knowledge of death and heir status; individual commencement.

**Question IDs:** ZGB567-1, ZGB567-2.

### C64 — Obergericht Zürich, LF220058, 25.08.2022

**Pinpoint:** E. 2–4. [Judgment text](https://law.lexplorer.ch/s/d/zh_obergericht_LF220058).

Zurich authority and protection against a court communication received only after the extended period had expired.

**Question IDs:** ZGB567-3, ZGB570-1.

### C65 — BGer, Urteil 5P.155/2001 vom 24.07.2001

**Pinpoint:** E. 2a, 2b/aa–bb and 3. [Judgment text](https://law.lexplorer.ch/s/d/bger_5P.155_2001).

Security inventory versus public inventory and protective extension; limited arbitrariness review.

**Question IDs:** ZGB567-3, ZGB568-1, ZGB580-1, X-3.

### C66 — BGer, Urteil 5A_739/2019 vom 27.01.2020

**Pinpoint:** E. 1.2.2 and 3.4. [Judgment text](https://law.lexplorer.ch/s/d/bger_5A_739_2019).

Silence after public inventory; restricted ability to undo acceptance based on known uncertainty.

**Question IDs:** ZGB568-1, ZGB570-3, ZGB571-5, ZGB571-8, ZGB588-1.

### C67 — BGE 149 III 345, Urteil vom 11.05.2023 (publiziert als BGE 149 III 345)

**Pinpoint:** E. 5.1 and 5.4. [Judgment text](https://law.lexplorer.ch/s/d/bger_5A_961_2022).

Individual disclaimer versus all closest heirs disclaiming; liquidation surplus.

**Question IDs:** ZGB572-1, ZGB573-1.

### C68 — BGE 131 III 49, Urteil vom 19.11.2004 (publiziert als BGE 131 III 49)

**Pinpoint:** E. 2.2–2.3 and 3. [Judgment text](https://law.lexplorer.ch/s/d/bger_5C.67_2004).

Subsidiary liability after disclaimer for specified five-year transfers; standing and limitation.

**Question IDs:** ZGB560-1, ZGB579-1.

### C69 — BGE 124 III 286, Urteil vom 22.07.1998

**Pinpoint:** E. 3a–b. [Judgment text](https://law.lexplorer.ch/s/d/bge_BGE_124_III_286).

Bankruptcy-liquidation cost liability; distinguish the requesting inheritance authority and an heir acting personally.

**Question IDs:** ZGB580-1, ZGB593-1.

### C70 — Kantonsgericht Basel-Landschaft, 810 23 152, 06.11.2023

**Pinpoint:** E. 5.1, 7.3–7.4 and 9.2.3–9.2.4.4. [Judgment text](https://law.lexplorer.ch/s/d/bl_gerichte_810%2023%20152).

Public inventory and omitted deputy-fee claims. Minor/KESB observations are background, not a comprehensive minority-protection holding.

**Question IDs:** ZGB560-1, ZGB566-4, ZGB580-1.

### C71 — BGer, Urteil 5P.134/2002 vom 05.09.2002

**Pinpoint:** E. 2.2. [Judgment text](https://law.lexplorer.ch/s/d/bger_5P.134_2002).

Heirs' solidary external liability, internal allocation and recourse.

**Question IDs:** ZGB603-1.

### C72 — BGE 132 III 61, Urteil vom 31.08.2005 (publiziert als BGE 132 III 61)

**Pinpoint:** E. 6 of the full judgment 4C.188/2005. [Judgment text](https://law.lexplorer.ch/s/d/bger_4C.188_2005).

Five-year categories under Art. 128. Pinpoint refers to the full judgment, not assumed identical numbering in the published extract.

**Question IDs:** OR106-11.

### C73 — BGer, Urteil 5A_83/2009 vom 25.03.2009

**Pinpoint:** E. 4. [Judgment text](https://law.lexplorer.ch/s/d/bger_5A_83_2009).

Legal aid and the process-cost minimum; not an authority approving collection-agency fees.

**Question IDs:** SchKG93-4, X-5.

### C74 — BGE 122 III 53, Urteil vom 25.01.1996

**Pinpoint:** E. 4a–c. [Judgment text](https://law.lexplorer.ch/s/d/bge_BGE_122_III_53).

Damages interest, no cumulation, and prohibition on capitalising contractual damages interest for further default interest.

**Question IDs:** OR105-1.

### C75 — BGer, Urteil 5A_1052/2021 vom 01.06.2022

**Pinpoint:** E. 4. [Judgment text](https://law.lexplorer.ch/s/d/bger_5A_1052_2021).

Proof of service; actual second delivery after expiry of the postal collection period.

**Question IDs:** SchKG74-1.

## G. Directly inspected doctrine

These are academic publications or named scholarly commentaries. Author-hosted and university-repository PDFs reproduce the publications themselves. Bibliographic references to other works within them are not separately verified sources.

### D1 — Arnold F. Rusch, *Verzug, Inkasso und AGB*, AJP/PJA 9/2021, pp. 1131–1145

[Original publication](https://arnoldrusch.ch/wp-content/uploads/2022/03/210901-ajp-rusch-agb-verzug-inkasso.pdf). **Pinpoints:** I.C, pp. 1132–1133; II.C, p. 1134; IV.C–VI.C, pp. 1136–1139; VIII.C, pp. 1140–1142; X.C, p. 1143; XI.C–XII, pp. 1144–1145.

The article argues a position; its conclusions are not automatically holdings of the courts it discusses.

**Question IDs:** OR102-2, OR103-1, OR106-1, OR106-3, OR106-4, OR106-6, SchKG27-1, SchKG27-2, SchKG17-6.

### D2 — Grégoire Geissbühler, *Le recouvrement privé de créances: aspects contractuels et protection du débiteur*, Genève/Zurich: Schulthess, 2016, thèse no 917, ISBN 978-3-7255-8613-4

[Original publication](https://access.archive-ouverte.unige.ch/access/metadata/e32d5c10-7f2c-4438-8ce6-3be10effcd0a/download). **Pinpoints:** N 1043–1044, p. 217; N 1101–1111, pp. 229–231; N 1126–1129, p. 234; N 1132–1139, pp. 234–236; N 1142–1149, pp. 236–238; N 1162–1165, pp. 241–242.

Original publication uses the then-current Art. 27 numbering. The office-representation prohibition moved to para. 2 in 2018; see C12.

**Question IDs:** OR106-1, OR106-2, OR106-3, OR106-6, OR106-7, OR106-8, SchKG27-2, SchKG68-1, ZGB560-2.

[University repository bibliographic record](https://archive-ouverte.unige.ch/unige:98522).

### D3 — Tobias Aggteleky / Philip Carr, *Kommentierung zu Art. 8a SchKG*, in: Bruno Pasquier / Michel Heinzmann (Hrsg.), Onlinekommentar, 15 September 2023, DOI 10.17176/20230915-085058-0

[Original publication](https://onlinekommentar.ch/de/kommentare/schkg8a). **Pinpoints:** N 12–17, 41–43, 49–55, 65–70 and 72.

The 2023 edition predates the 2026 amendment. Do not reuse N 56–58 or 61–64 on application timing/unsuccessful proceedings without the updates in C36–C37.

**Question IDs:** SchKG8a-1, SchKG8a-3, SchKG8a-5, SchKG8a-7, SchKG8a-9, ZGB566-4, X-1.

### D4 — Selim Marasco-Keller, *Kommentierung zu Art. 91 SchKG*, in: Bruno Pasquier / Michel Heinzmann (Hrsg.), Onlinekommentar, 16 January 2026

[Original publication](https://onlinekommentar.ch/de/kommentare/schkg91). **Pinpoints:** N 1 and 4–12, especially N 8–12.

Original German commentary inspected.

**Question IDs:** SchKG93-12, ZGB576-1.

### D5 — David Rosenthal, *Das neue Datenschutzgesetz*, Jusletter, 16 November 2020

[Original publication](https://www.rosenthal.ch/downloads/Rosenthal-revidiertesDSG.pdf). **Pinpoints:** N 37–42, especially N 42(b), and N 137–141.

Discusses the adopted revised DSG; the relevant Art. 31–32 wording was cross-checked against the current consolidation. Attribute interpretive qualifications to the author.

**Question IDs:** DSG31-1, DSG32-1, ZGB570-4.

## H. Limits, excluded hits and handover to the source corpus

**Remaining complete gaps:** SchKG59-1 and ZGB574-1. The P-labelled answers identify additional unresolved subquestions, including complete deadline computation, particular collection-fee limits, the private credit-agency burden of proof, and specialised inheritance exceptions. A gap means this research did not establish a citable answer; it does not mean that no authority exists.

Several apparently useful search hits were excluded or confined to their actual scope: 4D_66/2024 did not supply a collection-fee merits ruling; 4A_665/2018 concerned another subject; 5A_429/2023 did not establish the substantive interference test; and an Obwalden inventory/liquidation hit had inconsistent date metadata. C73 is used only for legal aid. Older Art. 8a and Art. 85a authorities are retained only with the stated amendment qualifications. A source mentioned inside another judgment or article has not been represented as personally inspected.

For later population of the existing files:

1. Copy the exact citation and pinpoint; distinguish a Federal Supreme Court merits holding, limited-review decision, cantonal decision and attributed scholarly position.
2. Use an original-language, contiguous source excerpt in `passage`; do not substitute the English summary. Fetch and validate it through the project's importer in a separate authorised edit task. Short quotations here may need a larger context passage for a useful corpus entry.
3. Put the question IDs, holding, factual limits and amendment warnings in the appropriate descriptive fields. Keep disputed or case-sensitive material at `use: ["briefing"]`; a source's inclusion is not by itself permission for autonomous user advice.
4. Preserve the distinction between R5's escalation trigger and actual acceptance of an estate, and between R4's conservative urgency trigger and a legally calculated final deadline.
5. Leave the identified gaps unfilled until a directly inspected authority resolves them. No invented paragraph numbers, inferred quotations or second-hand commentary citations should be added.

**Verification record:** 75 judgment identities checked; relevant judicial text inspected; five doctrinal publications directly inspected; all 111 question IDs addressed; 19 short judicial passage candidates checked against retrieved text. This is a source-research report, not an executed corpus import or a representation that every subquestion has been fully resolved.

**Workspace preservation:** all my written research materials were created outside the project directory. The final hash comparison detected concurrent changes to application code and documentation, plus new demo files; I did not make or revert those changes. The question list and the existing source files matched the initial snapshot.
