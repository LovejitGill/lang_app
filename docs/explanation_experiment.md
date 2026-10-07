# Step 2 improvement: separate explanation and justification review

This isolated experiment adds a second Qwen3 4B call after the corrected-sentence
candidate. It replays the existing 60 development outputs; it does not regenerate
corrections, change the live app, train a model, or use paid services.

## What you are learning

Separate generation from checking a proposal. `explanation_review.py` sends only
the original sentence, proposed sentence, and Python-derived edit offsets to a
focused prompt. The previous generated explanation and benchmark reference labels
are excluded so the second pass cannot simply copy either one.

The model returns `decision` (supported or unsupported) and `explanation`:

- Supported: it claims the edit fixes a real error and explains the applicable rule.
- Unsupported: it cannot justify the proposed edit; the reason is retained for review.
- A malformed response or service failure is unavailable, not a clean result.
- An unchanged sentence skips this call. This is not independent grammar validation.

A model judging its own proposal is not an independent expert. Both passes can
share the same misconception. The second pass cannot repair the corrected text:
if it is wrong, the appropriate behavior is to withhold it. It also cannot recover
errors missed by the first pass when no change was proposed.

`explanation_eval.py` simulates offering only supported corrections. Unsupported
results are labeled withheld, never “your grammar is correct.” It preserves the
proposed correction, original explanation, raw second-pass response and timing.
A withheld genuine error is a miss in the full 30-error denominator. It must not
be counted as improved precision without also reporting the lost coverage.

This experiment changes explanation generation and the decision to offer an edit
together. It does not isolate wording alone. Compare rule quality on the same
supported edits, and measure coverage/false corrections separately.

## Frozen protocol and measurement

`evaluation/explanation_experiment/protocol.json` was written before inference.
It fixes the source-file hash, prompt/schema, model digest, temperature 0.2,
non-thinking mode, 256 output tokens, context 4096, unset seed and zero retries.
The runner refuses a changed source, prompt, schema or model digest. The complete
60-case source is retained; 31 changed proposals receive second-pass calls.

Selection requires zero offered changes on all 30 correct inputs, no unavailable
results, more than 17/30 useful explained corrections and at least 80% accepted-edit
precision. A human still has to assess whether “supported” is actually justified.
Any promising result must be repeated before held-out validation or app adoption.

Review-call time is measured separately. Adding it to the old generation time
would only estimate a pipeline using separate runs; it is not a measurement of
actual conversation delay. Do not count zero-time skipped calls as fast inference
when reporting model-call latency.

## Verification steps

Start in the project directory:

```bash
cd /Users/lovejit/PerScholas/AI_Solutions_dev/CAPSTONE/AI_Dev_CAPSTONE/lang_app
```
`cd` changes your working directory; here it makes subsequent relative file paths
resolve in SpeakWell. Expected: no output; your prompt should indicate `lang_app`.

```bash
uv run python -m pytest tests/test_explanation_review.py -q
```
`uv run` uses the project's managed Python environment; pytest exercises the new
review contract and failure handling without calling a model. Expected: `25 passed`
(elapsed time varies). Tests cover skipped cases, input isolation, unsupported
corrections, raw rejected responses, service failures and source preservation.
One test explicitly shows that a bad correction can receive mechanically valid
model support: parsing JSON does not establish correctness.

```bash
uv run python explanation_eval.py --output evaluation/explanation_experiment/my_development_results.json
```
This evaluator replays frozen proposals against local Ollama; such runners collect
auditable evidence outside the UI. Ollama and the existing `qwen3:4b` model must be
available. Expected lines resemble:

```text
development-01 skipped no_proposal 0.0s
development-02 valid proposed 5.0s
```
Statuses and timings vary. The final summary includes `second_pass_calls`,
`withheld_proposals`, `correct_inputs_with_offered_change` and per-call timing.
An existing output filename is refused. Exit code 1 indicates an unavailable
result or setup failure; unsupported decisions are recorded without pretending
they are service errors.

## Review and improvement checkpoint

Read the original/proposed text beside both explanations. Ask whether the change
was needed, whether it fixed the error without changing meaning, and whether the
new explanation states the actual rule. Do not approve a pass just because the
model says supported. Keep original outputs immutable and record human judgments
separately. Next, use the resulting error analysis to select one further bounded
change; do not keep adding model calls unless the quality gain justifies the cost.

## Recorded outcome and next step

See [measured results](../evaluation/explanation_experiment/results.md) and the
[actual comparison](../evaluation/explanation_experiment/comparison.md). The pass
supported all 31 proposed changes, including both known bad proposals, so it failed
the frozen gate. Median extra review time was 12.500 seconds per reviewed proposal.
The app remains unchanged. Verification: 216 tests passed, including 25 new tests;
lint and lock consistency checks passed.

Next, consider reviewed rule explanations with explicit applicability checks as
a separate development-only experiment. Do not add this second pass to the app
or treat model self-approval as validated grammar feedback.
