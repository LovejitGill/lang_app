# Run and review the complete grammar flow

This validation uses 32 approved inputs: eight did-question errors, eight counted-
noun errors, and sixteen acceptable inputs. The model generates each proposal;
we do not substitute the reference sentence. Built-in LanguageTool evidence and
the supplemental count rule then decide whether a correction can be offered with
an existing explanation. All generation code, model identity, rule files and
settings are checked against the frozen protocol before starting.

The project owner approved the labels and explicitly requested execution. The
historical protocol retains its original pending-label status; label_approval.json
records the later approval. Input-label approval is not approval of model output.

The runner saves the start of every attempt and checkpoints generation, built-in
checker and supplemental-checker evidence. Failures and invalid output are retained.
There are no retries. An existing results file blocks another run; never remove
it to seek a better result. Rejected or withheld errors remain in the denominator.

## Timing

The current offline implementation starts the supplemental Java checker once per
input. Stage timings measure generation, built-in HTTP checking, supplemental
checking and decision processing. Total time also includes checkpoint overhead.
These are measured in the same run, not estimated by adding earlier benchmarks.
They are not full voice latency, and repeated Java startup is a material cost.
Detection validation is now complete. Any integration must measure conversational
reply delay separately from complete grammar-feedback processing.

## Verification

Run commands from the project directory.

1. `uv run python -m pytest tests/test_detection_flow_eval.py -q`

   `uv run` uses the managed environment; pytest normally checks code behavior.
   These tests verify label protection, input isolation, stage checkpoints,
   failure retention, timing accounting and refusal to overwrite a run.

   Expected: `8 passed`. Tests fake inference and do not call the real model.

2. `uv run python -c 'import json; from pathlib import Path; d = json.loads(Path("evaluation/detection_flow_validation/decision.json").read_text()); print(d["status"], d["human_useful_feedback"], "/", d["error_denominator"])'`

   Python's `-c` option executes a short check directly. This reads the finalized
   scorecard without generating new answers.

   Expected: `passed_targeted_validation 16 / 16`. This verifies the recorded
   decision, not a fresh model run.

3. Open `evaluation/detection_flow_validation/results.md` to inspect the actual
   outcomes. Source evidence is `results.json`; approved judgments are in
   `output_review_approved.json`. The pending draft `output_review.json` is kept
   for provenance. E1–E16 are error cases; C1–C16 are acceptable cases.

The working explanation template changed after evaluation. Calling `verify()`
against current working files now intentionally reports
`Frozen candidate changed: grammar_explanation_reasons.py`. The tests verify the
archived reason source against the original protocol; do not rewrite frozen hashes
or rerun the completed evaluation to accommodate a wording change.

The execution command is `uv run python detection_flow_eval.py`. It normally starts
this one frozen validation, not the app; after a run exists, it intentionally
reports `Validation already started; preserve evidence and do not rerun.`

## Review and next step

At least 13/16 erroneous inputs must receive useful feedback, with zero offers on
acceptable inputs and zero unavailable results. Reference matches help assess
edits but do not establish explanation quality. Review the actual edit, preserved
meaning and explanation before marking useful feedback.

These are targeted, partly paired synthetic cases, not broad English accuracy.
Once results inform edits, use new untouched inputs for another independent test.
The project owner approved all 16 usefulness judgments and 16 preservation
checks. Next proposed improvement: opt-in app integration that shows conversation
first and grammar feedback separately, with separate timing measurements. Keep
later explanation refinement separate, as requested.

## Recorded run outcome

All 32 attempts completed: 16/16 reference-matching error corrections, no changes
on 16/16 acceptable inputs, and no unavailable responses. Actual offered reasons
are now approved: 16/16 useful corrections against the 13/16 threshold. The
original number wording was accepted as accurate; the clearer “is more than one”
revision is approved separately. Raw model explanations were not approved.

Measured total grammar-processing median was 7.430 s (p95 10.400 s). Model-generation
median was 3.279 s; supplemental Java-check median was 3.623 s. This run does not
demonstrate the two-second conversational target. The targeted quality step is
complete; latency and broader coverage remain limitations in improvement_plan.md.

The full suite passed 314 tests after inference completed; active-code Ruff and
uv lock checks passed. Those checks belong to the recorded run. Finalizing this
approval did not rerun inference or alter source results, app code or Git history.
