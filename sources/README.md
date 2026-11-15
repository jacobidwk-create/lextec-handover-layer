# Legal sources

The system only cites what is stored in this folder. There are three kinds of source.

| File | Content | How it gets there | Checked by code? |
|---|---|---|---|
| `corpus.json` | Statute articles | `python tools/fetch_sources.py` copies them from Fedlex | Yes, copied directly |
| `case_law.json` | Passages from court decisions | Built by `python tools/verify_case_law.py` from `case_law_selection.json` | Yes, each passage must appear word for word in the decision |
| `licensed/commentary.json` | Excerpts from commentaries and other licensed literature | Pasted by hand | No |

Do not edit `corpus.json` or `case_law.json` by hand.

## Adding a court decision

1. Find the decision (Swisslex, legalis, bger.ch) and decide which passage matters.
2. Find the same decision at a public address: `https://entscheidsuche.ch` or `https://www.bger.ch`. The check needs a web page or PDF file that can be downloaded without a login.
3. Add an entry to `case_law_selection.json`:

```json
{
  "id": "bge-133-iii-1",
  "citation": "BGE 133 III 1",
  "consideration": "3.3",
  "url": "https://entscheidsuche.ch/docs/CH_BGE/CH_BGE_005_BGE-133-III-1_2007.html",
  "passage": "The passage, copied word for word from the decision, in its original language.",
  "holding": "One sentence in your own words: what the court decided here.",
  "areas": ["inheritance_debt"],
  "issues": ["estate_interference"],
  "question": {"de": "Welche Frage beantwortet die Passage?", "en": "Which question does the passage answer?"},
  "when": [{"disclaimer_filed": [true]}, {"estate_procedure": ["extension"]}],
  "use": ["briefing"],
  "selected_by": "Name"
}
```

4. Run `python tools/verify_case_law.py`. An entry whose passage is not found in the decision is rejected.

Notes on the passage:

- Take a whole paragraph of the court's reasoning, not a single sentence, so that the lawyer can see the context. The briefing shows the passage in full.
- The decision may be a web page or a PDF file. The comparison ignores upper and lower case, white space and hyphens, so a word that the PDF splits at the end of a line ("Verwal- tungshandlung") can be written normally. Every word must otherwise be identical, including typing errors in the published text.
- Do not let the passage run across a page break of the published decision (in a BGE the marker "BGE 133 III 1 S. 4", in a PDF the page number); the marker would be part of the text and the passage would be rejected.
- A scanned PDF without readable text is rejected.

Fields:

- `areas`: one or more of `debt_collection`, `inheritance_debt`, `credit_record`.
- `issues`: the legal issues the source is about, from the list in `handover/issues.py` (`collection_fees`, `payment_order_objection`, `objection_deadline_missed`, `advanced_enforcement`, `register_entry`, `loss_certificate`, `estate_interference`, `disclaimer_period`, `disclaimer_effect`). The source appears in a briefing only if the established facts of the case raise one of its issues, and never outside its `areas`. If no issue fits, a new issue has to be defined in that file first.
- `question`: the question the passage answers, in one sentence, in German (`de`) and English (`en`). It is printed with the decision.
- `when`: the condition under which the decision is printed in full once its issue is raised. This is a legal judgement: on which facts does the question of this decision arise? Three forms:
  - `"always"`: whenever the issue is raised. Use it only if the issue itself is narrow.
  - A list of alternatives, each a set of facts with the values they must have. The decision is printed if any alternative is met; an alternative is met if every fact in it has one of the listed values. Example: `[{"service_disputed": [true]}, {"document_received_date": ["unknown"]}]` means "service is disputed, or the date of service is not known". Fact names and their values are those of `handover/areas.py`. For a yes/no fact write `true` or `false`; for a fact with fixed choices one or more of its choices; for any fact `"known"` (established, whatever the value) or `"unknown"` (the user does not know it, or it could not be clarified).
  - `"manual"`: the question depends on something the system records only as free text. The decision is then never printed in full; it is listed in one line with its question whenever its issue is raised.
  - Six derived values can be used like facts. `@objection_deadline`, `@disclaimer_deadline`, `@inventory_deadline` and `@complaint_deadline` take `passed`, `close`, `running` or `met` (the step is reported as taken). `@heir_knowledge` takes `same_day` or `differs` (a statutory heir learned of being an heir on the day of learning of the death, or not). `@register_service_age` takes `within_one_year` or `over_one_year` (time since service of the payment order behind a register entry).
  - A decision whose condition is not met is not hidden: it is listed in one line, with the note that it is still open (a fact is missing), not relevant on the established facts, or cannot be checked.
  - After adding or changing an entry, add its test case to `tests/test_relevance.py` (one case in which the decision is printed, one in which it is not). The tests fail if a stored decision has no case, an unknown fact name or an impossible value.
- `rules` and `facts` (older form, still understood for entries without `issues`): escalation rules that must have fired, and facts that must have the listed values.
- `use`: `["briefing"]` shows the source only to the lawyer. `["briefing", "user"]` additionally allows the system to use it in the general classification shown to the user. Choose `user` only for settled, general statements.
- `holding`: written by the person who selected the decision. It is shown to the lawyer, marked as a summary.

## Adding a commentary excerpt

Copy `licensed/commentary.example.json` to `licensed/commentary.json` and add entries in the same shape. The `licensed/` folder is excluded from the repository (except the example file), because the texts are protected by copyright and may only be used under an agreement between the operator and the publisher. Commentary excerpts are shown to the lawyer only, never to the user, whatever `use` says.

## Research questions

`research_questions.md` lists, article by article, the questions that the statute text leaves open (undefined terms, discretion, burden of proof, deadlines). Use it as the work list for the research: for each question, look for the leading decisions and commentary passages, and note the question identifier (for example `ZGB571-1`) in the `holding` of the entry you add, so that it is clear which question a source answers.

## What is stored now, and the AI research report

`case_law_selection.json` holds 28 passages from 26 decisions (34 passages were imported on 2026-11-11; `question` and `when` were added on 2026-11-12; six passages were removed on 2026-11-14 together with their legal field). They were taken from `Computational_Law_Verified_Research.md`, the report of an AI research tool, which refers to 75 decisions (C01 to C75) and five publications (D1 to D5). The AI assistant chose the passages from the public texts and drafted the `holding`, `areas`, `issues`, `question` and `when` fields. Every such entry says so in `selected_by`.

**To review an entry** (legal team):

1. Open the decision at `url` and read the cited consideration. Check that the passage is the right one and that the `holding` is correct and not too broad. Check that `question` states what the passage answers, and that `when` names the facts on which that question arises: not so wide that the decision is printed where it does not matter, not so narrow that it is missing where it does.
2. Check in Swisslex or legalis that the decision has not been overruled.
3. If you accept the entry, replace the text in `selected_by` with your name. If not, delete or change the entry.
4. Run `python tools/verify_case_law.py`.

The field `research_report_ref` (for example `C55`) points to the decision's number in the report; the program ignores it. The other 43 decisions of the report are listed in `case_law_candidates.md`. The publications D1 to D5 are doctrine and belong in the commentary file; they have not been checked.

## Candidate decisions

`case_law_candidates.md` has two parts. The first lists keyword hits from a first search; they have not been read or assessed. The second lists all 75 decisions of the AI research report with their public address, format and status.
