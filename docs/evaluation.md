# Milestone 6 — Testing, Error Handling, Evaluation Pass

## What this milestone teaches

Component tests isolate behavior using controlled inputs and substitute model
responses. Integration tests check how components cooperate. Live evaluations
use the real model and require reviewing whether its answer is actually useful.
A valid JSON response and a saved turn do not establish correct teaching.

`errors.py` now owns shared exception types and stable error codes. The LLM,
speech, and storage modules raise these deliberately worded errors; the UI
formats them consistently. Existing imports of these exception classes from the
older modules remain usable. A final UI exception boundary hides unexpected
internal messages and displays the exception type for diagnosis. Streamlit's
normal stop/rerun control signals pass through unchanged.

For example, connection failure now displays `TUTOR_UNAVAILABLE` with the Ollama
startup instruction. It preserves the draft and does not save a completed turn.
Tests verify that retrying after recovery saves one intended exchange.

This is defense against tested runtime failures, not a guarantee against all
crashes: import errors, process termination, resource exhaustion, browser failure,
and arbitrary future bugs remain possible. Restart Streamlit after structural
module/dependency changes; refreshing a browser alone can retain stale imports.

## Recorded results — 2026-09-22 local time

96 automated tests passed in 9.14 seconds; Ruff passed. The test suite runs
without model downloads or live model calls. Local live results below are
separate evidence, collected with Qwen3 1.7B and the existing generation settings.

### Section 13 cases

| Case | Outcome | Evidence |
|---|---|---|
| Obvious tense error | PASS in this run | Live response corrected go → went |
| Correct sentence | QUALITY FAIL | Live response wrongly corrected enjoy hiking |
| Blank input | PASS | UI test blocks it without inference or history changes |
| Silent recording | PASS for controlled silence | Real WAV validation through simulated UI shows RECORDING_ERROR; no tutor call |
| Ollama unavailable | PASS for injected service failure and recovery | TUTOR_UNAVAILABLE, retained draft, no saved turn until successful retry |
| Long input | PASS at implemented boundary | Backend limit is 1,000 characters and oversized audio transcripts are rejected |

The plan suggested a stretch threshold above 500 characters. This pass preserves
the established 1,000-character UI/backend contract; 501 characters are allowed.
Ollama outage is injected in automated tests instead of stopping the user's
running service. The earlier actual outage also confirmed the connection error.

### Five live text turns

One sequential beginner/daily-activities conversation used a temporary database.
Timing starts at Send and ends after the rendered reply: it includes LLM,
history access, saving, and simulated Streamlit reruns. It excludes speech capture,
transcription, human review, browser networking, and speech synthesis. Model
loading state was uncontrolled; do not label these controlled cold/warm trials.

Ratings below are **assistant qualitative review**, for the learner/instructor
to check. Scale: 1 wrong/irrelevant; 2 partially correct; 3 correct and specific.

| Input | Seconds | Feedback rating | Assessment |
|---|---:|---:|---|
| Yesterday I go to the store. | 2.774 | 3 | Correct go → went; relevant past-tense explanation |
| I enjoy hiking with my friends. | 4.073 | 1 | Incorrectly changes hiking to a hike; original is valid |
| My brother work in a bank. | 3.274 | 3 | Correct work → works with third-person singular subject |
| I usually hike on Saturdays. | 4.061 | 1 | Incorrectly changes hike to hikes and invents a rule |
| Where does my brother work? | 4.404 | 1 | Incorrectly changes my to your; reply also fails to recall the bank |

All five generated/saved successfully, and a rerun added no duplicate. Median:
**4.061 seconds**, maximum: **4.404 seconds**. Two genuine-error cases received
useful corrections; all three correct-input cases received false corrections.
This small, connected sample is not an independent benchmark or general accuracy
estimate. [Exact responses and review](milestone6_results.json).

### Five recorded-audio processing turns

A separate run repeated the 11-second public Whisper reference clip used in
Milestone 5. AppTest substitutes only the recording widget; STT, LLM, SQLite and
UI reruns are real. It transcribes then sends immediately, without human editing.
This timing probe does not establish microphone operation or recognition across
different speakers. [Exact results](milestone6_voice_results.json).

| Repeat | Completed-WAV-to-render seconds |
|---|---:|
| 1 | 7.844 |
| 2 | 5.382 |
| 3 | 5.572 |
| 4 | 5.551 |
| 5 | 5.702 |

Median: **5.572 seconds**; maximum: **7.844 seconds**. Five turns saved, no
duplicate on rerun. Recording duration, user review, browser transport, and spoken
output are excluded. **The two-second conversation target is not met.** No p95
claim is made from five measurements. The fixture is a timing probe, not learner
speech; repetition and prior context may affect later calls.

## Run the checks yourself

```bash
cd /Users/lovejit/PerScholas/AI_Solutions_dev/CAPSTONE/AI_Dev_CAPSTONE/lang_app
```

**Purpose/typical use:** Selects the project directory before running its tools.
**Expected:** No output on success.

```bash
uv run --locked python -m pytest -q
```

**Purpose/typical use:** Runs repeatable regression tests using locked dependencies;
use after changes to catch input, state, and recovery bugs.
**Expected:** `96 passed in ...`. This does not grade a live model's language.

```bash
uv run --locked ruff check .
```

**Purpose/typical use:** Checks Python source for common mistakes and style issues
before sharing changes. **Expected:** `All checks passed!`

Keep Ollama running, then:

```bash
uv run --locked python evaluate.py --output .tools/my-evaluation.json
```

**Purpose/typical use:** Runs five live text turns in simulated Streamlit against
the local model and isolated temporary history; use to compare prompt changes.

**Expected, variable:** `past_tense: ...s; completed`, followed by four more
cases and `Results: .tools/my-evaluation.json; ratings still require review.`
`completed` means the processing path succeeded, not that the answer was correct.
If Ollama is unavailable, cases report `FAIL`; errors appear in the JSON and the
command exits unsuccessfully. Normal learner history is not modified.

For an optional recorded-audio measurement, replace the sample path below with
a local mono, 16 kHz, 16-bit PCM WAV:

```bash
uv run --locked python evaluate.py --audio /absolute/path/to/recording.wav --output .tools/my-voice-evaluation.json
```

**Purpose/typical use:** Repeats the same completed recording through five full
processing turns to measure local pipeline cost, without needing a microphone.
**Expected, variable:** `audio_repeat_1: ...s; completed` through repeat 5, then
the results path. This requires downloaded speech weights; it cannot assess
speaker diversity. Output includes transcripts, so keep personal reports private.

## Your learning exercise and stop checkpoint

1. Inspect `errors.py`, then follow the unavailable-service exception from
   `llm_client.py` to the UI. Explain why it does not become a tutor reply.
2. Run the live evaluator and open its JSON. Fill in each null feedback rating
   and TODO review note yourself; give reasons, not only scores.
3. Add five original sentences to a separate evaluation copy, including two
   correct sentences and one question whose answer is in earlier context.
4. Change only one prompt variable and compare results using the same inputs.
   A prettier reply is not a fix if false corrections remain.

The evaluation milestone is complete as a testing pass with understood failures.
**Do not treat feedback accuracy, recall, or latency as passing release gates.**
No model training, public deployment, Git tag, or optional voice-output feature
was added in this milestone.
