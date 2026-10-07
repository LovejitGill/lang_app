# Step 2 improvement: corrected sentences with code-derived spans

This is an isolated experiment, not an app change or model training. Step 1's
project-owner-reviewed development baseline is frozen. This experiment implements
the replacement-span part of step 2 and collects evidence for step 3. Clearer
explanation templates remain a separate potential change.

## What changed and what to learn

`sentence_grammar.py` asks the same Qwen3 4B model for `corrected_text` and one
sentence-level `explanation`. Python compares the original and corrected text,
derives exact start/end offsets, and verifies that applying those edits recreates
the returned sentence exactly. It does not ask the model to select original spans.

Example of the intended behavior (illustrative, not a measured model result):

```text
Original:  I am engineer.
Corrected: I am an engineer.
Derived:   insert "an " at character offset 5
```

The tokenizer retains words, punctuation and whitespace. `SequenceMatcher` finds
matching token sequences and identifies insertions, deletions and replacements.
Offsets refer to Python Unicode character positions, not browser UTF-16 positions.
Repeated words can admit multiple valid alignments; this algorithm chooses one
reproducible alignment, not a linguistically authoritative one. Spaces may appear
inside a derived edit. Keep the full sentence visible during review.

The old experiment could describe the right rule but target the wrong words.
Deriving spans removes that particular mismatch between model-selected spans and
its intended corrected sentence. It cannot stop the model from returning a wrong
sentence, unnecessary rewrite or inaccurate explanation. Validation is mechanical.

## Contract fixed before inference

`evaluation/sentence_experiment/protocol.json` records the dataset, baseline and
prompt hashes, model digest, settings, selection criteria and known limits.
The candidate keeps temperature 0.2, 256 output tokens, context 4096, non-thinking
mode, no retries, and the two original prompt example sentences. Its schema asks
for a full sentence and one explanation shared by all derived edits. That is an
output-format change, so this is not a perfectly isolated change to diff code alone.

- Unchanged input needs an empty explanation.
- Changed input needs a nonempty explanation of at most 240 characters.
- Corrected text must be nonempty and at most 1200 characters.
- At most two derived edit regions are accepted; a region is not necessarily one
  linguistic error. More regions are rejected rather than silently truncated.
- Raw rejected output is retained. It never becomes a successful empty correction.
- Correct-looking JSON, reconstruction and exact-reference matching do not establish
  explanation accuracy or preserved meaning. Human review still uses the approved rubric.

Only the 60 approved development cases are used. The existing baseline is an
archived run, not a simultaneous randomized control. The seed remains unset;
repeat promising results before attributing gains to the new design. Keep the
held-out set untouched while making design decisions.

## Verification commands

Run from the project directory:

```bash
cd /Users/lovejit/PerScholas/AI_Solutions_dev/CAPSTONE/AI_Dev_CAPSTONE/lang_app
```
`cd` changes the shell's working directory; here it makes project-relative commands
resolve correctly. Expected output: none; the shell prompt should identify `lang_app`.

```bash
uv run python -m pytest tests/test_sentence_grammar.py -q
```
`uv run` executes the project Python environment; `python -m pytest` runs the tests
with project modules importable. Expected: `30 passed` (elapsed time varies).
This checks exact reconstruction, insertion/deletion offsets, repeated text,
Unicode, invalid responses and preservation of rejected raw output. One test
explicitly demonstrates that incorrect English can pass mechanical validation.

```bash
uv run python sentence_eval.py --output evaluation/sentence_experiment/my_development_results.json
```
The evaluator calls the local model on the frozen development set and saves each
attempt; evaluation runners are used to collect repeatable evidence outside the UI.
Ollama must be running with the already-installed `qwen3:4b` model. Expected lines
resemble `development-01 valid 3.0s` followed by a summary (times/statuses vary).
An existing output filename is refused. Exit code 1 can indicate retained rejected
or failed responses; inspect the saved evidence before interpreting the run.
No LanguageTool service is needed for this experiment.

```bash
uv run python benchmark.py review --report evaluation/sentence_experiment/my_development_results.json --output evaluation/sentence_experiment/my_development_review.json
```
The existing review command creates an engine-name-hidden, shuffled worksheet;
it is used to separate model generation from human semantic judgment. Expected:
`Review worksheet: 60 rows; semantic scores pending.` Review sentence correctness,
meaning preservation, unnecessary edits, and the actual generated explanation.
Do not replace the generated explanation with a better human-written version
before scoring. For insertions/deletions, inspect the offsets and full sentence.

## How to read results

The runner's `exact_reference_matches_on_errors` is a diagnostic count, not the
number of useful tutor responses. A matching corrected sentence can have a wrong
explanation. A nonmatching sentence can be an acceptable alternative. An unchanged
erroneous sentence is a miss. Rejected outputs remain failures even if part of the
raw output looks useful. Metrics must include all 60 attempts.

For multiple derived regions addressing one grammatical error, the earlier scorer's
one-to-one edit assumption can be unsuitable. Adjudicate the alignment explicitly
or use an appropriately configured edit scorer; don't label a valid second region
as a false positive simply to make the counts fit.

The frozen development selection requires: all 30 acceptable inputs unchanged
without failure; more than the baseline 17/30 useful explained corrections; no
accepted-edit precision decrease below 80%; at most four rejected/failed responses.
Report all-attempt median/p95/max request latency. This is standalone grammar
latency, not speech-end-to-first-audio latency. Selection on development earns
further validation, not immediate app adoption.

## Next steps for improvement

Review the measured corrections and explanations alongside the approved baseline.
If the candidate improves the joint quality criteria, repeat with the same protocol
and then consider the existing held-out gates. If not, keep the baseline and report
what failed. Test explanation templates as a separate experiment so their effect
is distinguishable. No model weights, prompts in the live tutor, or Git history
are changed automatically.

## Recorded first run

See [results](../evaluation/sentence_experiment/results.md) and the complete
[comparison](../evaluation/sentence_experiment/comparison.md). All 60 calls completed;
29/30 erroneous inputs matched references and 29/30 correct inputs were unchanged.
The latter fails the frozen selection gate. Automated verification: 191 tests pass,
including 30 new tests; lint and dependency-lock checks pass. The app remains on
its existing behavior. Next: review the focused failures before choosing a new
candidate; do not promote this run or claim a useful-feedback score prematurely.
