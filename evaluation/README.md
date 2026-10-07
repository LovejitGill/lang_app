# Focused feedback-quality experiment

**2026-10-05 conversation checkpoint:** The separate
[joint conversation-quality/latency report](conversation_quality/joint_results.md)
preserves prompt/model comparisons, warm/cold response paths, raw rejections and
remaining direct-answer failures. Its semantic review is pending; low latency
is not a pass when the response is generic or fails to answer. The approved
grammar evidence is unchanged, and no new conversation candidate is active in
the app. Next focus remains conversational quality and latency together.

**2026-09-29 update:** The original prompt comparison below remains historical
evidence. A subsequent isolated grammar experiment selected Qwen3 4B on development
results, then ran the existing held-out set twice without prompt changes. Both
runs failed the useful-correction gate. See `grammar_selection.json`,
`grammar_heldout_review.json`, and `grammar_final_decision.json`. This held-out
set is no longer unused; do not tune against its outputs and call it unseen.

These are original, assistant-authored evaluation sentences with expected
standard-English judgments. The assistant reviewed their labels; independent
learner/instructor review remains necessary. They are not a certified benchmark.

## Protocol fixed before comparison

- `development.json`: 20 sentences, 10 acceptable and 10 with a target error.
- `heldout.json`: 20 different sentences, similarly balanced, reserved from
  prompt selection. Authoring the set does not mean it was used to tune prompts.
- `regression.json`: six previously observed failures; explicitly not held out.
- Both main sets cover all three levels and scenarios. Sentences test language
  features across settings; not every sentence is an ideal scenario opener.
- Compare `baseline` and `conservative` using development cases only. Both use
  the same Qwen model, JSON schema, temperature, output limit, and retry policy.
- Cases are independent, with no prior learner history or database writes.
  This experiment evaluates sentence feedback, not multi-turn recall.
- Variant order alternates by case. Loading state and host workload are not
  controlled; report elapsed time without claiming an isolated speed benchmark.
- Record actual feedback and conversational replies, not only schema validity.
  An empty list on erroneous input is a miss even if the reply silently rewrites it.
- Review correction, explanation, preserved meaning, reply grammar, and whether
  the reply invites relevant elaboration separately. Nonempty feedback alone is
  not proof that a useful correction was made.
- Select based on development results before looking at held-out output. A
  candidate that simply suppresses all feedback is not an improvement.
- If a candidate is selected, run held-out cases twice, plus regressions. Do not
  change the prompt after seeing held-out failures and still call those cases
  unseen; create a fresh held-out set for a subsequent tuning cycle.
- If neither candidate is acceptable, keep the existing application default,
  report the failed experiment, and leave held-out cases reserved for a future
  development-selected candidate. Do not run them just to find easier successes.

## Acceptance targets

For each held-out run: no invented correction on 10 acceptable sentences, at
least 9/10 useful corrections with accurate explanations on erroneous sentences,
and no grammatical error introduced in the conversational replies. Repeat once
and report both runs. These are small project gates, not general guarantees.

Development selection must reduce false corrections without a collapse in useful
error correction or conversational quality. Report timing and retries separately.
Original regression failures must stay visible, even if a new set performs well.

## Reading the runner

`quality_eval.py` uses the real `ask_tutor()` parser/retry path with a temporary
in-process prompt override. It never changes application settings or writes
learner history. The expected labels stay in the report, outside model messages.
Prompt and dataset hashes identify the exact inputs; the model digest and
generation settings identify the runtime. A new output filename is required to
avoid overwriting past evidence. Partial results are saved after every call.

Mechanical summary fields describe feedback presence and completed calls only.
`review: null` means semantic review has not been recorded. Do not interpret that
as success. Any populated review must identify its reviewer and rationale.

## Learning exercise

TODO: Review five acceptable and five erroneous sentences yourself before reading
the model results. Compare your judgments with the recorded assistant review,
flag ambiguous labels, and explain why fewer corrections alone is insufficient.
Once a held-out item influences a prompt decision, retire it from the held-out set.

## Benchmark v2 workbench (2026-09-29)

`benchmark_v2/` contains 60 draft development cases, 40 fresh draft held-out cases,
local LanguageTool/Qwen development responses, a blank shuffled human worksheet,
and separate dialogue checks. Old evaluation reports remain historical evidence.
No new held-out inference has been run. See `../docs/benchmarking.md` for the review
protocol, provisional-label caveats, expected command output, and subsequent gates.

## Development review completed (2026-09-30)

All 60 development labels and 120 response judgments are confirmed by the project
owner. See [final scorecard](benchmark_v2/final_scorecard.md). Useful feedback:
LanguageTool 15/30, Qwen 17/30. Neither reaches the target; no app adoption or new
held-out inference. Earlier provisional reports remain historical evidence.

## Separate explanation review (2026-09-30)

`explanation_experiment/` preserves the protocol, 60 replayed source cases (31 model
calls), raw reviews and side-by-side explanations. All 31 proposals were supported,
including a bad correction and an unnecessary rewrite. The selection gate failed;
no new held-out inference or live integration occurred. See its `results.md` and
`decision.json`; full candidate semantic ratings remain pending, not implied by
valid JSON or the model's supported decision.

Short explanation experiment: `rule_explanation_experiment/results.md` lists 14
provisional offers for human review. Latest replay is `development_results_v2.json`;
coverage is insufficient for adoption. See `../docs/rule_explanations.md`.

Latest agreement extension: `rule_explanation_experiment/agreement_results.md`.
Four new judgments are pending; 14 exact-match approvals carry forward in
`agreement_review_v3.json`. Raw replay: `development_results_agreement_v3.json`.

Agreement review completed: `rule_explanation_experiment/agreement_review_approved.json`
records 18/30 confirmed useful feedback; earlier pending reviews are preserved.
Next: challenge-context validation before integration.

Context regression checks: `rule_challenges/results.md` (18/24 before, 24/24 after).
The new development replay preserves all 18 previously approved offers; provenance
is in `rule_challenges/development_review.json`. Independent validation remains.

Held-out preparation: `rule_validation/protocol.json` freezes candidate identities
and gates. Review `rule_validation/label_review.md` (20 pairs covering 40 pending
labels). Frozen copies are under `rule_validation/frozen/`; no inference yet.

Held-out run complete: `rule_validation/results.md` and `decision.json`. Only one
of 20 error cases was offered feedback (maximum useful coverage 5%); candidate
failed the 60% coverage gate. All input labels approved; model-output review remains
separate and pending. Do not integrate this candidate.

Active improvement: `broader_rules/results.md` compares rule-ID-based explanation
assignment with the earlier word filter. Fresh component checks pass 25/28;
three misses and new human judgments remain open. These are not LLM end-to-end
held-out results. See `../docs/broader_rules.md`.

Sentence-specific reasoning revision: `broader_rules/reasons_v1/comparison.md`
compares old/new explanations on identical decisions. All 33 drafts need teaching
quality review; detector coverage is unchanged. See `../docs/grammar_reasons.md`.

Three detection-gap fixes: `detection_gaps/results.md`. Prior component checks now
pass 28/28; a frozen follow-up passes 28/28 new component checks (12 positive,
16 counterexamples). New rule applications await review in `detection_gaps/review.json`.
Explanation refinement is deferred; these checks do not establish LLM end-to-end quality.

All 15 detection-gap rule applications are now approved in
`detection_gaps/review_approved.json`. Next-run preparation is in
`detection_flow_validation/preparation.json`; there are no combined-flow results yet.
Explanation refinement remains deferred.

Targeted combined-flow labels are ready for review in
`detection_flow_validation/label_review.md`: 32 new inputs, labels still pending.
`protocol.json` freezes identities and gates; `novelty_check.json` records no
normalized matches against 83 earlier JSON artifacts. No inference yet.

Combined grammar-flow run completed: `detection_flow_validation/results.md`.
All 16 erroneous inputs received reference-matching offers; all 16 acceptable
inputs stayed unchanged. No unavailable responses. Human usefulness judgments
remain pending in `output_review.json`; `decision.json` does not approve integration.
Actual generation and checker timing are recorded separately.

Final combined-flow review (2026-10-01): the project owner approved all 16 delivered
corrections as useful and all 16 acceptable-input preservation checks. The targeted
13/16 usefulness gate, zero-false-offer gate and zero-unavailable gate passed.
`detection_flow_validation/output_review_approved.json` links approval to the
unchanged run and pending review by hashes; `decision.json` records the final
score. The earlier preparation and pending-review records above are historical.
The eight revised number explanations are approved separately from original
run output. This is not a broad grammar score or approval of raw LLM reasons.

Next proposed improvement: opt-in integration with conversational replies and
grammar feedback shown separately, measuring both delays. No app integration
has been performed; broader explanation refinement remains deferred.

October 6 conversation checkpoint: `conversation_quality/natural_v4/results.md`
records 41 inspected development cases, their response paths and text-only timings.
`review.md` shows all actual delivered replies; `review_draft.json` remains pending.
The original October 5 results and the partial owner review remain preserved.
Earlier notes about absent app integration are historical: optional separate grammar
feedback was integrated October 1; the new conversation candidates are still not
selected or integrated. Next focus remains conversation quality plus response time.

Latest conversation checkpoint: `conversation_quality/planned_v2/results.md`.
53 inspected development cases exercise planned follow-ups, learner-only recall
and bounded local explanations. Generated, selected and authored responses remain
separate; all usefulness judgments are pending in `review_draft.json`.
The preceding candidate and both new revisions remain preserved. Next: review
generic/constraint-sensitive responses and test fresh multi-turn dialogue before
integration; no general quality or two-second spoken-latency claim is established.

Current checkpoint: `conversation_quality/planned_v3/results.md` — 63 inspected
development cases, dietary/person/time boundaries, separate path/timing counts
and pending human judgments. Next: review tone and then freeze fresh multi-turn
dialogues for planned_v4. GitHub checkpoint recommendation: yes after reviewing
the tested experimental files; no stable app release or publication is implied.
