# Frozen held-out validation

The project owner approved all 40 labels in 20 displayed pairs. Approval is stored
separately from the original pending-label artifact and is tied to exact file hashes.
It does not approve the model's answers. The frozen protocol remains historical;
its original pending status is superseded by label_approval.json.

`rule_validation.py` checks the approved labels, frozen code and model digest,
then sends only the learner text to the existing sentence-generation function.
The rule filter sees only the original and proposed text. References never enter
either function. Each attempted input is saved before inference and completed
with raw output, error information and generation/rule/total processing timings.
No retries or best-of-several selection is allowed. Existing output blocks reruns.

Human useful-feedback scoring requires a necessary, correct correction, preserved
meaning, and an accurate, understandable explanation. Unchanged or withheld errors
remain misses. Matching a reference is only a diagnostic, not human approval.

The gate is at least 12/20 useful corrections, no offers on the 20 correct inputs,
precision of at least 80% among offered corrections, and no unavailable responses.
A small paired synthetic dataset cannot prove general reliability. Timing covers
text generation plus the rule check, not microphone-to-speaker voice latency.

## Verification

Run commands from the project directory.

1. `uv run python -m pytest tests/test_rule_validation.py -q`

   `uv run` uses the managed environment; pytest normally runs automated behavior
   checks. These tests check input isolation, frozen-label verification, failure
   retention, timing accounting and refusal to overwrite an existing run.

   Expected: `8 passed`. These tests use mocked generation, so they make no model calls.

2. `uv run python -c 'from rule_validation import verify_files; _, d = verify_files(); print(len(d["cases"]), "approved labels; frozen files verified")'`

   Python's `-c` option runs a small check directly from the terminal. This command
   verifies the recorded label approval and candidate file hashes without inference.

   Expected: `40 approved labels; frozen files verified`.

3. Open `evaluation/rule_validation/results.md` and `output_review.json` to review
   the completed run. Fields left null require human judgment, not a guessed score.

The execution command is `uv run python rule_validation.py`: it is an evaluation
entry point for one frozen run, not the app launcher. After this run exists, it
intentionally exits with `This validation already started; preserve evidence and
do not rerun.` Do not delete the report merely to generate a better result.

Next: review actual offers and record the decision against the frozen gates.
If this dataset informs another change, it becomes development evidence for that
change; obtain new untouched inputs for later independent validation.

Archived Python source is immutable evidence. For linting active code, use
`uv run ruff check . --extend-exclude evaluation/rule_validation/frozen`.
Ruff checks style and common code issues; the exclusion avoids reinterpreting
archived imports from their different directory. Expected: `All checks passed!`.
