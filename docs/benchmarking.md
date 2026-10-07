# Milestone 2 improvement — Independent tutoring benchmarks

This is an evaluation workbench, not a change to the live tutor. No candidate is
promoted on mechanical validity alone. Java and LanguageTool are optional local
tools; the app's Python dependency lock and existing model default are unchanged.

## What is implemented

- `benchmark.py`: fixed-input comparison of local LanguageTool and grammar-only
  Qwen, raw responses, failures, model identity, prompt/settings and dataset hash.
- `evaluation/benchmark_v2/development.json`: 60 draft cases (30 correct/30 errors),
  including the previous 20 development examples.
- `evaluation/benchmark_v2/heldout.json`: 40 fresh draft cases (20/20), never sent
  to a model during implementation. Running requires named label approval.
- All 100 labels require human review. Paired examples stay in the same split.
  They are synthetic and correlated; they do not establish real-world accuracy.
- A shuffled worksheet hides engine names. Review hashing prevents accidentally
  applying judgments to a changed report. Semantic metrics stay null while any
  successful response still needs review. Output files cannot be overwritten.
- `conversation_benchmark.py`: six scripted turns, including history recall,
  topic change, a fragment, and beginner/advanced comparisons. Uses temporary
  SQLite memory, not the learner's database. Quality ratings are manual.
- `speech_metrics.py`: verbatim-transcript word error rate and monotonic event
  timing helpers, with unit tests. These are measurement tools, not new audio
  features or evidence that live voice latency has been achieved.
- Aligned ERRANT export for complete valid runs with reviewed references.
- Six draft rule explanation templates, intentionally inactive pending review.

## Review protocol — do this before choosing a candidate

1. Review the development labels without reading candidate output. Correct
   ambiguous references, add acceptable alternatives, and document each change.
   Fill each `label_review` with `status: approved`, your reviewer name, and a
   rationale. Approval is a human declaration, not automatic certification.
2. Independently review held-out labels without tuning prompts against them.
   Ideally a second person handles this set. Do not inspect held-out outputs
   until you freeze a candidate. Using these labels to tune would contaminate it.
3. Run the frozen development comparison. Review the shuffled response worksheet.
   Count edits and judge explanations/meaning in the full sentence context.
4. Record the chosen engine, model digest, rule configuration, prompt hash,
   development-report hash, selection rationale and acceptance gates in a new
   selection JSON BEFORE evaluating held-out output. The current CLI enforces
   label approval, but this selection step is a documented human checkpoint.
5. Require no invented corrections on 20 acceptable inputs and useful feedback
   on at least 18/20 erroneous inputs in EACH of two held-out runs. These extend
   the previous project targets, not a capstone mandate or population guarantee.
   Report rejected/service responses separately; they cannot count as success.
6. If the candidate fails, retain the app default. After tuning from those
   failures, retire that held-out set and obtain a fresh one.

A single reviewer is an initial practical option. Two independent English
instructors, agreement reporting and adjudication would strengthen the evidence.
Do not call assistant-authored labels independently reviewed. Add natural
learner utterances, dialect variants, context-dependent fragments and multiple
errors in a later corpus version; don't inflate certainty with template variants.

## Setup and verification

Run commands from the project directory:

```bash
cd /Users/lovejit/PerScholas/AI_Solutions_dev/CAPSTONE/AI_Dev_CAPSTONE/lang_app
```
`cd` changes the shell's working directory; here it makes subsequent relative
paths resolve inside SpeakWell. Expected output: none; your prompt should show
`lang_app` (or use `pwd` to print the current directory).

```bash
uv run python scripts/setup_benchmark.py
```
`uv run` runs Python in the project's managed environment; this installer fetches
and verifies the optional Java and LanguageTool archives under `.tools/benchmark`.
Expected key output:

```text
java.tar.gz: SHA-256 verified
lt.zip: SHA-256 verified
Optional benchmark runtime ready; no system Java installation changed.
```
This verifies pinned archive bytes, not grammar accuracy. Java's checksum was
obtained from Adoptium metadata; LanguageTool's digest records the observed
versioned official download, not an independently signed publisher checksum.
Pinned versions: Temurin JRE 21.0.12.1+1 Intel macOS and LanguageTool 6.6. The
installer intentionally rejects other operating systems/architectures.
Downloads total approximately 294 MB; extracted files require additional space.
No `sudo`, Homebrew installation, paid API or global Java change is needed.

```bash
bash scripts/languagetool.sh
```
`bash` executes a shell script; this one starts the local Java HTTP service on
loopback port 8081 with a 1 GB Java heap ceiling. Expected key output:

```text
Starting LanguageTool 6.6 ... server on http://localhost:8081...
Server started
```
Leave this terminal open while evaluating; Ctrl+C stops the process. A fastText
warning is expected because the experiment explicitly selects `en-US` instead
of automatic language identification. No public-network or browser CORS flag is
used. LanguageTool logs requests/statistics; use synthetic inputs in this stage.

In another terminal, with the same project directory:

```bash
uv run python -m pytest tests/test_benchmark.py tests/test_speech_metrics.py -q
```
`python -m pytest` runs the test framework with the project root on Python's import
path; these tests verify accounting, validation and measurement behavior offline.
Expected key output: `29 passed` (elapsed time varies). This proves tested code
behavior, not human tutoring quality.

```bash
uv run python benchmark.py score --report evaluation/benchmark_v2/development_results.json --review evaluation/benchmark_v2/development_review.json
```
The `score` subcommand validates a review worksheet against its original report
and computes reviewed metrics; it does not call either model. Before review,
expected snippets include `"semantic_metrics": null`, positive `pending_reviews`
and `"label_status": "PROVISIONAL labels"`. That is deliberate, not a failed run.

To conduct a NEW comparison, start Ollama using the existing project instructions,
ensure `qwen3:4b` is already installed, and keep LanguageTool running:

```bash
uv run python benchmark.py run --dataset evaluation/benchmark_v2/development.json --output evaluation/benchmark_v2/my_development_results.json
```
The `run` subcommand sends each sentence to both local engines and saves every
completed attempt; it is used for reproducible candidate comparisons. Expected
lines resemble `development-01 languagetool valid 0.04s` and
`development-01 qwen valid 1.4s` (outputs/times vary), followed by timing summaries.
Exit code 1 means a rejected/error response was recorded or setup failed; inspect
the report. A rejection is preserved evidence, not a reason to delete the run.
An existing output filename is refused. Only the learner text is sent to engines.

```bash
uv run python benchmark.py review --report evaluation/benchmark_v2/my_development_results.json --output evaluation/benchmark_v2/my_development_review.json
```
The `review` subcommand prepares a shuffled, engine-name-hidden human worksheet;
it is used to separate semantic judgments from model generation. Expected:
`Review worksheet: 120 rows; semantic scores pending.` Fill reviewer, rationale,
TP/FP/FN and the explanation/meaning booleans for every valid response.
For valid empty feedback, mark explanation/meaning true only as not applicable
on acceptable English; it still cannot earn useful-feedback credit on erroneous
input. Leave scores blank when uncertain and seek adjudication.
Use a different name for a second reviewer's worksheet; adjudicate disagreements
in a new file without overwriting either reviewer's evidence.

TP = correct proposed edits; FP = incorrect or unnecessary proposed edits;
FN = genuine errors left unfixed. This simple scorer assumes one-to-one matching
between proposed edits and gold errors. If an edit combines multiple errors,
adjudicate with ERRANT or revise the protocol; don't force misleading counts.
Useful feedback requires all target errors fixed, no bad edits, preserved meaning
and accurate explanations. Failure rows contribute missed errors automatically.
Precision concerns accepted proposals; rejected raw proposals remain separately
visible and must not be presented as trustworthy corrections.

## Additional benchmarks

```bash
uv run python conversation_benchmark.py --output evaluation/benchmark_v2/my_conversation_results.json
```
This script runs the real conversation client with isolated temporary history;
it is used to check dialogue behavior independently of grammar-only candidates.
Expected: six `valid`/`error` lines, such as `recall-and-topic valid 3.2s` (variable).
Review direct answers, history use, follow-up relevance, and level fit separately.
No automated score claims that a response was relevant merely because it ran.

For speech, create a consented, human-transcribed corpus. Preserve grammatical
mistakes exactly, rather than proofreading the reference. A measurement JSON
can contain `transcriptions` entries with `reference` and `hypothesis`, and
`voice_turns` entries with `status` and an `events` object. Successful events need
`speech_end`, `turn_detected`, `transcript_ready`, `first_token`, and `first_audio`
monotonic timestamps in seconds; optional `feedback_ready` is measured separately.
Use a shared clock or calibrated clock mapping: server and browser clocks cannot
be subtracted directly. Ground-truth speech end and audible playback need actual
instrumentation/recorded measurement; a button-click time is not speech end.

```bash
uv run python speech_metrics.py data/my_measurements.json
```
This command scores an input measurement file; offline metric scripts typically
summarize collected evidence without running inference. Expected fields include
`corpus_wer`, `voice_turns_attempted`, `voice_turn_failures`, and
`voice_latency_successful_only`; values depend on your actual recordings.
Do not use fabricated timestamps as performance evidence. Keep private speech
under ignored `data/`, not in Git. Review ASR error preservation separately from
WER. WER alone cannot distinguish a harmless word change from erased grammar errors.

## ERRANT and public benchmarks

```bash
uv run python benchmark.py export-errant --report evaluation/benchmark_v2/my_development_results.json --engine languagetool --output data/errant-input
```
The export subcommand creates aligned source, hypothesis and reference text for
an external edit scorer; it is used to avoid hand-copying mismatched sentences.
Until labels are reviewed, expected: `Benchmark stopped: Review reference labels
before exporting ERRANT data.` After approval and a complete valid run, expected:
`Aligned ERRANT inputs exported; scoring requires the separate ERRANT environment.`
Ambiguous, overlapping edits and failed runs are refused, not silently omitted.

Use a separate uv-managed evaluation environment for ERRANT, pin its version and
English spaCy model, and record them with results. Do not add its NLP dependencies
to the live app just for scoring. ERRANT uses `errant_parallel` to extract edits
and `errant_compare` to score precision, recall and F0.5. Follow the official
installation/tokenization protocol: https://github.com/chrisjbryant/errant
and https://www.cl.cam.ac.uk/research/nl/bea2019st/ . Public-corpus download,
licensing review and actual ERRANT scoring remain a later evaluation stage;
no public benchmark score has been produced here. Explanation quality still
requires human review. Report failures alongside any external scorer result.

## Optional infrastructure and pronunciation stages

A larger pretrained correction/instruction model is a subsequent candidate, not
a dependency for this experiment. On a borrowed GPU machine, record hardware,
model/checkpoint and quantization, runner versions, context/output limits,
concurrency, prompts, failures and p50/p95 latency. Compare the same dataset and
model on CPU/GPU to isolate hardware effects. Availability of free school GPU
access is unconfirmed; no hosting or model training is introduced here.

Pronunciation evaluation needs a suitable existing pretrained scoring system and
human-rated audio, e.g. https://github.com/jimbozhang/speechocean762 . Honor dataset
terms and speaker separation. Report score error/agreement and false word-level
accusations; read-aloud results do not establish spontaneous-speech performance.
No pronunciation model was added and no pronunciation accuracy is claimed.

## Learning checkpoint

Explain why an empty correction list can be right on one input and a miss on
another, why a good replacement with a wrong explanation fails, and why a 30 ms
grammar request doesn't prove a two-second spoken response. Review ten development
labels and ten shuffled outputs before deciding whether to expand this experiment.

Verification at implementation: 160 tests passed; Ruff, uv lock consistency,
and shell syntax checks passed. LanguageTool was stopped after recording the
comparison; start it again with the command above when needed.
