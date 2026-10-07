# Final development scorecard — 2026-09-30

All 60 reference labels and 120 engine-response judgments were confirmed by the
project owner. These scores are final for this recorded development run, not a
held-out test or an independently expert-validated benchmark. The reviewer saw
engine names and reviewed assistant-proposed judgments. Synthetic paired sentences
limit generalization to natural learner speech.

| Measure | LanguageTool 6.6 | Qwen3 4B |
|---|---:|---:|
| Correct sentences left unchanged | 30/30 | 30/30 |
| Erroneous inputs receiving a correct edit | 21/30 | 20/30 |
| Useful correction and explanation | 15/30 (50.0%) | 17/30 (56.7%) |
| Accepted correct edits (TP) | 21 | 20 |
| Accepted wrong/unnecessary edits (FP) | 2 | 5 |
| Target errors missed or left unfixed (FN) | 9 | 10 |
| Accepted-edit precision | 91.3% | 80.0% |
| Correction recall | 70.0% | 66.7% |
| F0.5, from reviewed one-to-one edit counts | 86.1% | 76.9% |
| Rejected responses | 0/60 | 4/60 |
| Median request time | 0.032 s | 2.752 s |
| p95 request time | 0.060 s | 7.324 s |
| Maximum request time | 4.421 s | 12.622 s |

No unnecessary edits on correct inputs does not mean all proposed edits were
correct. Both engines still proposed wrong edits on erroneous inputs. Precision
uses accepted proposals; Qwen's four rejected no-op responses are separately
reported and remain missed target errors. Timing includes first calls and covers
standalone grammar requests, not speech-end-to-audible-response latency.

Useful feedback requires the correct complete edit, no unnecessary edits,
preserved meaning, and an accurate explanation of the applicable rule. A vague
suggestion without the rule fails explanation adequacy. Qwen row 16 remains an
explicit borderline pass. Changing it to a failure would reduce Qwen to 16/30;
the recorded score honors the user's pass decision.

## Decision

Neither engine meets the project's 90% useful-correction target. Do not adopt a
candidate or use the fresh held-out set to shop for a winner. The 40 held-out
labels remain pending review and their inputs have not been sent to a model.
The application's existing behavior is unchanged.

## Evidence and verification

- `development_results.json`: original, immutable model outputs.
- `final_development_report.json`: derived report with the approved label metadata,
  source hashes and identical inference rows. No model was rerun to finalize scores.
- `final_development_review.json`: 120 confirmed ratings and per-response provenance.
- `final_development_scores.json`: recomputed counts, rates, timing and limitations.
- `section_c_approval.json`: final ten failure approvals.
- `draft_scorecard.json`: review history, now marked complete; use final artifacts
  for reporting. Earlier pending worksheets remain historical snapshots.

From the project directory:

```bash
uv run python benchmark.py score --report evaluation/benchmark_v2/final_development_report.json --review evaluation/benchmark_v2/final_development_review.json
```
`uv run` executes the scorer in the managed Python environment; this command is
used to verify saved judgments and recompute metrics without model inference.
Expected key values:

```text
languagetool: pending_reviews = 0, tp = 21, fp = 2, fn = 9, useful_feedback_rate = 0.5
qwen:        pending_reviews = 0, tp = 20, fp = 5, fn = 10, useful_feedback_rate = 0.566666...
label_status = reviewed
```
The actual output is JSON. These values verify complete accounting and reproduce
the reviewed scores; they do not prove performance on unseen examples.

## Next improvement experiment

Test one change on development data: ask the grammar model for a full corrected
sentence, then derive replacement spans programmatically instead of relying on
model-selected original substrings. Retain the current grammar-only evaluator
as the baseline. Incorrect spans in Qwen rows 10, 45, 47, 53 and 59 motivate this
experiment, but a full-sentence response can still rewrite unnecessarily or be
wrong; no accuracy improvement is assumed.

Before coding, freeze the candidate output contract, minimal-edit/meaning policy,
model/settings, evaluation metrics and failure handling. Score actual candidate
outputs, including their explanations, using the same approved rubric. Do not
substitute human-preferred explanations into outputs before grading. Derived
spans prove where text changed, not whether it should have changed. Track unchanged
correct inputs, accepted-edit precision, useful coverage and latency together.

Explanation templates can be a separate later experiment. They can improve weak
explanations but cannot, by themselves, recover missed articles or fix bad edits.
Use the fresh held-out set only after a candidate earns selection on development.
