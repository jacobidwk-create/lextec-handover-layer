# Legal intake implementation review — 2026-11-12

## Scope

Federal Swiss debt-related law, domestic Canton Zurich, general information and consent-based referral. The system is not a merits adjudicator. A legal branch that cannot be safely established is referred, not silently treated as negative. The four topics remain supported: debt/fees, inherited debts, enforcement-register entries, and subsistence minimum (always human review).

## Research and implementation mapping

- **Debt:** Art. 102 OR establishes default; Arts. 104–106 distinguish interest and additional loss. Art. 27(2) SchKG concerns representation before enforcement offices, not a blanket rule about every collection fee. BGE 123 III 241 E. 3a and 4b (read and verified during the initial audit) addresses proof and crediting interest against additional loss. Intake records the claim, itemisation, payments, default history and asserted fee basis; no automated liability finding.
- **Objection:** Arts. 64 and 74 SchKG require service-sensitive timing and proper recipient; a partial objection has its own scope. Full reported objections only suppress the conservative alarm if service, recipient, date and scope support that narrow screening result. Disputed service, partial/late/other-recipient declarations require human review, including Art. 33(4) restoration where applicable. Arts. 31 and 63 mean actual time can exceed the conservative screening date. Referral is not a finding of lateness.
- **Inheritance:** Arts. 566–571 distinguish heir status, official notification, protective inventories, successor heirs, form, acceptance and interference. Arts. 576, 580 and 587–588 govern extensions and the distinct public-inventory procedure. Ordinary statutory/appointed starts are computed; special situations are referred urgently. Zurich courts expressly confirm that the public-inventory request period is one month from the start of the disclaimer period. Financial uncertainty triggers screening of that shorter period. No estate solvency finding is inferred from 'none known'. BGE 133 III 1 E. 3.3.1–3.3.2 (read and verified in the initial audit) illustrates why estate activity does not mechanically establish forfeiture; the broad activity trigger remains a referral policy.
- **Register:** Current Art. 8a(3)(a–d) and (4), effective 1 January 2026, governs separate outcomes, objection, waiting period, request, creditor proof and final failure, and five years after conclusion. Payment is distinct from withdrawal. Pending litigation and requests/refusals are reviewed. The system does not certify eligibility, finality or deletion. Official request correspondence, including creditor proof within twenty days, belongs to office procedure.
- **Subsistence:** Art. 93 SchKG and Zurich guidance require income, family/household, necessary expenses and supporting payment evidence. Art. 93(3) adjustment is distinguished from the original Art. 17 complaint; Art. 17(3) inaction is not forced into a ten-day timer. Immediate deprivation triggers urgent review. Art. 22 nullity remains for human assessment; the app never says that all remedies are lost after ten days.

## Verified source access

The project fetcher downloaded 23 articles directly from Fedlex on 2026-11-12. Texts were not manually authored. Lexplorer full article outputs were used for the legal distinctions; the audit read the cited judgments and verified their references. A later-citation lookup was performed, but no blanket assertion that all stored case law remains good law is made.

- [Art. 8a SchKG](https://law.lexplorer.ch/s/a/281.1/8a)
- [Art. 74 SchKG](https://law.lexplorer.ch/s/a/281.1/74)
- [Art. 64 SchKG](https://law.lexplorer.ch/s/a/281.1/64)
- [Art. 567 ZGB](https://law.lexplorer.ch/s/a/210/567)
- [Art. 580 ZGB](https://law.lexplorer.ch/s/a/210/580)
- [Art. 587 ZGB](https://law.lexplorer.ch/s/a/210/587)
- [Art. 588 ZGB](https://law.lexplorer.ch/s/a/210/588)
- [Zurich courts: public inventory](https://www.gerichte-zh.ch/de/themen/erbschaft/erbgangssicherung/oeffentliches-inventar)
- [Zurich subsistence calculation guidelines](https://www.zh.ch/de/steuern-finanzen/steuern/treuhaender/steuerbuch/steuerbuch-definition/zstb-183-3.html)
- [BGE 123 III 241 — additional default loss](https://law.lexplorer.ch/s/d/bge_BGE_123_III_241)
- [BGE 133 III 1 — estate administration and interference](https://law.lexplorer.ch/s/d/bge_BGE_133_III_1)

## Independent review and validation

Independent research review completed in three passes. Final demo/integration validation is recorded below. No claim of exhaustive correctness of Swiss law or legal-lead approval is made.

## Independent review, first pass

The independent agent researched the implementation and returned three P1 findings and one P2 finding. All were accepted and corrected:

1. Register-only reported objections bypassed the full procedural checks. Register intake now independently collects service uncertainty, objection date, recipient and scope, and uses the same completion predicate as debt intake. Partial objections require review: section 9 of the [BJ directive No. 5, V3.1.2026](https://www.bj.admin.ch/dam/de/sd-web/pu9YVpiLPWzD/weisung-5.pdf) excludes them from the paragraph 3(d) procedure.
2. Immediate referrals could lose urgency when official document dates were unknown. Court/seizure documents and unresolved potential official deadlines now preserve an urgent-review signal even without a computable date. This avoids pretending to calculate an unclassified remedy; provisional Rechtsöffnung, for example, may involve Art. 83(2) SchKG.
3. Changed circumstances could hide a new complaint period following an adjustment refusal/new calculation. Intake now asks whether a new decision exists; first knowledge then starts its own Art. 17 screening period. The reviewer independently read and verified [Zurich CB250007, E. 2.4–2.5](https://law.lexplorer.ch/s/d/zh_bezirksgericht_buelach_CB250007), concerning refusal and its complaint period.
4. The changed-circumstances briefing incorrectly required the original document date to raise the issue. It now raises the subsistence issue from the established issue category and attaches Arts. 93, 17 and 22 without requiring an irrelevant original date.

The review found the inheritance branching substantially aligned with the independently retrieved statutes, within the explicitly conservative human-review boundary. It did not certify all stored case law or model extraction reliability. A follow-up review of the fixes was requested.

## Independent review, second pass

The agent confirmed the four original counterexamples were corrected, then found two further P1 urgency issues. Both were accepted and corrected:

- In a mixed case, a completed objection deadline could mask an unknown inheritance start because the fallback checked the entire deadline list. It now checks inheritance-specific deadline keys independently.
- Unknown-date urgency was absent from the plain-text offer and disappeared after declined handover. A fixed bilingual urgent-review warning now appears in the offer text and structured message, and in decline notes when no imminent date can be computed. It invents no date and preserves the user's choice not to send a briefing.

Regression tests cover a completed objection plus unknown appointed-heir notification, and both language variants of offer/decline. The old-register/no-objection case remains a deliberately conservative over-referral policy: a potentially missed objection period is reviewed rather than suppressed. Referral does not establish that restoration or other remedies are unavailable. No false performance claim is made for this policy.

## Independent review, final verification

The independent agent reported: **Both remaining P1 findings are resolved. No unresolved material findings remain from this targeted review.** It ran all 47 legal-logic tests and independently reproduced the combined mixed-case offer/decline flow in both languages. The accepted old-register over-referral policy is documented above and in full_report.md 3.5a. This closes the identified findings within the declared general-information/triage scope; it does not certify exhaustive legal coverage or live model extraction.

## Final validation

- `python3 -u tools/record_demo.py`: all six German/English scenario runs reached their expected routes; 26 real model responses recorded for exact-prompt replay.
- `env -u SMTP_HOST -u BRIEFING_TO python3 -m pytest -q`: **94 passed**, including 47 legal-logic regression cases, demo replay, localhost HTTP integration, citation checking, and consent-before-delivery tests.
- No live development/held-out performance evaluation was rerun. Earlier evaluation results concern the old questionnaire; no extraction-accuracy claim is inferred from the deterministic tests or six demonstration runs.
- No runtime dependency was added. Statute texts were downloaded through the existing Fedlex fetcher. Existing case-law release restrictions and consent-based handover remain in place.

## Addendum, 2026-11-12 (later the same day)

A check of the legal logic against Fedlex and directive No. 5 of the Federal Office of Justice found that the briefing issue `disclaimer_effect` cited Art. 570 ZGB for the effect of a disclaimer towards creditors. Art. 570 ZGB governs form and record; liability towards the deceased's creditors despite a disclaimer is Art. 579 ZGB. The issue now names both articles, and Art. 579 ZGB was added through the Fedlex fetcher, so the corpus holds 24 articles. Four further points were reported to the legal lead and left unchanged; they are listed in README section 10, point 13. 95 tests pass.
