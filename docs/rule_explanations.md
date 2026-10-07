# Short learner explanations: offline experiment

The aim is brief, familiar language, with enough detail to teach the rule.
One sentence is a preference, not a requirement. A second sentence or example is
welcome when it helps; do not cut off text simply to meet a word limit.

`rule_explanations.py` matches a proposed whole-sentence change against five
small rule families. It chooses fixed wording instead of asking the LLM to invent
an explanation. Exact reconstruction prevents a matching rule from hiding an
additional edit elsewhere. This is a limited pattern check, not a grammar proof.
Unknown changes are `withheld`; unchanged proposals are `no_proposal`, which does
not mean the learner's input is correct. `provisional` means wording and assignment
still need human review. The live app does not use this module.

Examples of the wording:

| Rule | Learner explanation |
| --- | --- |
| Modal verb | After words like ‘can’ or ‘should’, use the basic verb form. |
| Do/does/did | After ‘do’, ‘does’, or ‘did’, use the basic verb form. |
| Number and noun | Use a plural noun for more than one item. |
| Duration | Use ‘for’ to say how long something lasts. |
| Comparison | Use only ‘shorter’, without ‘more’, when comparing. |

Show the original and replacement alongside the explanation so “basic verb form”
and “plural” have concrete examples. Next learner review should check whether
those two terms need a brief example, rather than assuming readability from length.

## Verify it yourself

Run these commands from the project directory.

1. `uv run python -m pytest tests/test_rule_explanations.py -q`

   `uv run` executes in the project's managed environment; `python -m pytest`
   normally runs automated tests. Here it checks rule coverage, unsupported edits,
   noun modifiers, input errors, and retention of all benchmark cases.

   Expected: `22 passed` (elapsed time varies).

2. `uv run python rule_explanation_eval.py --output /tmp/speakwell-short-rules-review.json`

   This runs the offline replay script, a common way to compare an experimental
   filter against saved model outputs. It creates a new report without calling
   Ollama; choose a new output name if the file already exists.

   Expected key output:

   ```json
   {"cases": 60, "model_calls": 0, "provisional_offers": 14,
    "withheld_proposals": 17, "no_proposal": 29,
    "false_offers_on_correct_inputs": 0,
    "error_reference_matches_offered": 14, "error_denominator": 30,
    "human_useful_feedback": null}
   ```

   This verifies accounting and reference matches, not semantic quality. Each
   output row has blank human judgments; review the whole proposed sentence,
   applicability of its rule, and clarity of its explanation before filling them.

## Results and limits

Latest evidence: `evaluation/rule_explanation_experiment/development_results_v2.json`.
The initial report is retained; v2 restricts number/noun matches to punctuation or
sentence end to withhold noun modifiers such as “three box sets”. Both replay
results have the same development counts. Source proposals were not regenerated.

Fourteen of 30 erroneous inputs have an offered reference-matching correction;
16 remain uncovered. None of the 30 acceptable inputs receives a correction.
The known bad proposals on rows 57 and 58 are withheld. This does not establish
zero false corrections outside this small dataset. Even if all 14 offers pass
human review, 14/30 is below the earlier 17/30 useful-feedback baseline: this
candidate is **not selected for app integration or held-out testing**.

Rules were designed with prior development failures in view, so this is
exploratory development evidence, not an independent evaluation. Finite word lists,
case/spacing restrictions and narrow patterns miss valid corrections. Quoted
language, unusual context, and multiple errors can still fool a matched pattern.
There is no full syntactic analysis. No additional inference is used, but original
sentence-generation latency still applies; no two-second voice target is proved.

## Next learning exercise

Review the 14 proposed explanations in the results table. Then add one bounded
rule family, with new positive and adversarial examples before re-running this
same development replay. Keep unknown cases in the denominator. Test with a
learner whether the short wording explains why the correction is necessary.
Do not use held-out sentences to design the next rule. Preserve all prior reports.

## Subject–verb agreement extension (2026-09-30)

The latest candidate adds simple present-tense agreement for a small set of known
people/verbs and singular “there is” clauses. Its pattern must match a complete
simple clause and reproduce the proposed sentence exactly. Unknown words,
coordinated subjects, relative clauses, quotes, and explicit past-time markers
are withheld. “Read” is excluded because its spelling can already represent past
tense; adding “s” could change the meaning. These checks are intentionally narrow,
not a full English parser. Multiple errors and unusual contexts remain risks.

The latest replay is `development_results_agreement_v3.json`; v1 is preserved.
The new review is `agreement_review_v3.json`. Four new offers await approval;
14 earlier approvals carry forward only after exact comparison of original text,
proposed text, rule, and explanation. Useful feedback is confirmed for 14/30;
18/30 (60%) is potential coverage, not a completed human score. Twelve erroneous
inputs remain uncovered, and zero of 30 correct inputs receives an offer.

Run `uv run python -m pytest tests/test_rule_explanations.py -q` to test the rules
in the managed Python environment; pytest is used to check behavior automatically.
Expected: `43 passed`, including new agreement examples and counterexamples.

Run `uv run python rule_explanation_eval.py --output /tmp/speakwell-agreement-review.json`
to replay saved model proposals; offline replay compares a code change without
regenerating model answers. Choose an unused output filename.

Expected key output: `"provisional_offers": 18`, `"withheld_proposals": 13`,
`"false_offers_on_correct_inputs": 0`, `"error_denominator": 30`, and
`"human_useful_feedback": null`. The null value is intentional: the raw replay
never manufactures human judgments; the separate review file holds approvals.

Learning exercise: explain why “She read books” must not automatically become
“She reads books”. Add a fresh ambiguous example before extending the vocabulary.
Next, review the four new offers in the agreement results table, then challenge
rule selection further before any app or held-out evaluation decision.

### Review update: all four new offers approved

The project owner approved the four agreement offers on 2026-09-30.
`agreement_review_approved.json` records 18/30 confirmed useful feedback (60%),
with zero pending offers and 12 uncovered erroneous inputs. Earlier pending
review artifacts are retained. Next: challenge rule applicability on new contexts
before integration; this approval does not establish general reliability.
