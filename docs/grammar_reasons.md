# Explain why the correction fits

The current improvement remains broader grammar-rule detection with useful, short
explanations. A correct rule statement can still be weak teaching feedback.

Use this pattern: **sentence evidence → relevant rule → why this replacement fits**.
For example, “Did already marks the past, so use order, not ordered.” This ties the
rule to the auxiliary and verb in the learner's sentence. Number, duration and
comparison explanations likewise name the actual words rather than only giving
an instruction. One or two short sentences are welcome; there is no sentence cap.

`grammar_explanation_reasons.py` wraps the frozen detector. The detector continues
to select or withhold edits; the new layer only changes the explanation. Reasons
come from the rule ID and exact input/replacement text. Missing context is marked
for review rather than filled with an invented fact. Word-sound claims for a/an
rely on the checker's existing grammar decision, not a guessed first-letter rule;
this is not an assessment of anyone's spoken pronunciation.

Some grammar is conventional. “Depend on” is a fixed word pairing; do not invent
an extra causal story about why English chose “on”. Similarly, after “enjoy”, the
“-ing” form names the activity. A brief example or second sentence can help more
than an abstract label.

## Verify

Run from the project directory.

1. `uv run python -m pytest tests/test_grammar_reasons.py -q`

   `uv run` uses the managed Python environment; pytest normally checks code
   behavior. Here it verifies that reasons use actual context and that all saved
   detection decisions remain unchanged.

   Expected: `13 passed` (time varies). This does not establish learner comprehension.

2. `uv run python grammar_reason_eval.py --output /tmp/speakwell-reason-review.json`

   This replays saved evidence to isolate a wording change, a common controlled
   comparison technique. Choose a new output name if it already exists.

   Expected: `"cases": 88`, `"detection_changes": 0`,
   `"offered_explanations": 33`, `"contextual_drafts": 33`,
   `"model_calls": 0`, `"checker_calls": 0`.

3. Review `evaluation/broader_rules/reasons_v1/comparison.md`. Judge factual accuracy,
   whether the reasoning fits this sentence, and whether a learner can understand
   it. Do not infer usefulness from word count or a passing unit test.

Learning exercise: explain why “Use the plural” teaches less than “Two is more
than one, so use sandwiches.” Then identify where a fixed language convention
needs an example instead of a made-up justification.

The live app and original frozen detector are unchanged. The three known detector
coverage gaps remain. Next, review this wording and continue those gaps within
the same active improvement; do not switch to latency or integration yet.

## 2026-10-01 — Number wording update

Number-based reasons now use “is more than one,” as requested. For example:
“‘Fifteen’ is more than one, so use the plural ‘seeds’.” Correction selection is
unchanged. The completed 32-input run retains its original wording and hashes;
its frozen reason source is archived in
`evaluation/detection_flow_validation/frozen/grammar_explanation_reasons.py.txt`.
The original protocol intentionally rejects the edited working source. Future
model evaluations require a new protocol; do not change the old frozen hashes.

Next: complete the existing human usefulness review. Broader explanation changes
remain deferred.
