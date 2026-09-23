# Milestone 2 — Tutoring Prompt Design

SpeakWell now has a text-only, single-turn tutoring mode. It returns
`{"reply": "...", "feedback": ["..."]}` rather than a generic text answer.
There is no conversation history, database, audio, or UI in this milestone.

## Read the implementation in this order

1. `prompts.py`: `LEVELS` and `SCENARIOS` contain trusted practice settings.
   `build_system_prompt()` selects the guidance and fills the system template.
2. `llm_client.py`: `ask_tutor()` separates the trusted **system message** (how
   to behave) from the **user message** (the learner's sentence).
3. `TUTOR_SCHEMA` supplies an output schema to Ollama. A schema defines the
   expected keys, types, and bounds; it cannot prove a correction is accurate.
4. `parse_tutor_response()` uses `json.loads`, then checks the exact keys,
   non-empty reply, and zero to two non-empty feedback strings. Correct input
   should receive `feedback: []`. No regex extraction or Markdown stripping is used.
5. Invalid structured output is retried once with a stricter format reminder.
   A second invalid result becomes a readable error. Connection/server failures
   are not automatically retried. A retry can add latency.

The prompt contains short examples of the desired behavior, called **few-shot
prompting**. They demonstrate corrections and correct sentences needing no
correction. This is inference-time guidance, not model training. A temperature
of 0.2 reduces output variation; it does not guarantee correctness or identical
answers. Keep thinking disabled and evaluate actual language feedback manually.

The original `ask_llm(prompt) -> str` function and its terminal behavior remain
available. The new API is `ask_tutor(text, level=..., scenario=...) -> dict`.
Each call is independent; it must not pretend to remember prior turns. Levels
change prompt wording only—they are not implemented courses or certified levels.

## Verification steps

Run commands from the `lang_app` repository root. If needed, in both terminals:

```bash
cd /Users/lovejit/PerScholas/AI_Solutions_dev/CAPSTONE/AI_Dev_CAPSTONE/lang_app
pwd
```

**Command purpose:** `cd` changes your working directory; `pwd` prints it. They
are commonly used to ensure subsequent commands operate on the intended project.

**Expected output:** `/Users/lovejit/PerScholas/AI_Solutions_dev/CAPSTONE/AI_Dev_CAPSTONE/lang_app`

**Verification:** Both terminals are using the same repository.

### 1. Ensure Ollama is running

In Terminal A, if your project server is not already running:

```bash
bash scripts/ollama.sh serve
```

**Command purpose:** `bash` runs the project helper script, and `serve` starts
Ollama's local HTTP service. A persistent server is normally used so Python
clients can request model inference without starting a new server each time.

**Expected log fragment:** `Listening on 127.0.0.1:11434`

**Verification:** Ollama is accepting local requests; leave this terminal open.
Do not start another server if your intended instance is already running.

### 2. Request tutoring feedback

In Terminal B:

```bash
uv run --locked python llm_client.py --tutor "Yesterday I go to the store."
```

**Command purpose:** `uv run --locked` runs Python using the project's locked
environment; it is normally used to run project tools reproducibly. Here,
`--tutor` selects structured tutoring instead of the original plain reply mode.

**Expected output shape** (wording can vary):

```json
{
  "reply": "What did you buy at the store?",
  "feedback": ["Change 'go' to 'went' because Yesterday refers to the past."]
}
```

**Verification:** You get both a relevant conversational reply and a specific
past-tense correction, with no text outside the JSON object.

### 3. Select a practice level and scenario

```bash
uv run --locked python llm_client.py --tutor --level beginner \
  --scenario "ordering food" "I would like a cup of tea, please."
```

**Command purpose:** Command-line flags supply configuration to the Python
program, a common way to test behavior before building a UI. These flags select
the trusted level/scenario instructions used in the system message.

**Expected output shape:**

```json
{
  "reply": "Would you like anything else with your tea?",
  "feedback": []
}
```

**Verification:** The reply fits the scenario, and the correct sentence is not
given an invented correction. A false correction is a model-quality failure
even when the JSON is valid.

**Observed limitation:** The current model failed this check during development:
it sometimes suggested changing “a cup of tea” to the identical phrase. The
empty-feedback example above is the desired behavior, not a claimed passing
result; see the evaluation document for the recorded output.

Available levels: `beginner`, `intermediate`, `advanced`.
Available scenarios: `daily activities`, `introductions`, `ordering food`.

### 4. Check the return value directly from Python

```bash
uv run --locked python -c 'from llm_client import ask_tutor; r = ask_tutor("She does not likes coffee."); print(type(r).__name__); print(sorted(r)); print(r["feedback"])'
```

**Command purpose:** Python's `-c` executes a short inline program and is often
used for quick component checks. This calls the reusable function and inspects
its return value without the CLI's JSON formatting.

**Expected key output:**

```text
dict
['feedback', 'reply']
[...a correction from 'likes' to 'like' after 'does not'...]
```

**Verification:** The function returns parsed data, not a JSON string, and its
feedback addresses the submitted sentence. The final line above describes the
expected content; it is not a literal output requirement.

### 5. Verify empty-input handling

```bash
uv run --locked python llm_client.py --tutor ""
echo $?
```

**Command purpose:** An empty quoted argument tests input validation; `echo $?`
prints the preceding command's exit status. Exit statuses are commonly used by
shell scripts to distinguish success from failure.

**Expected output:**

```text
Input error: Enter a non-empty text prompt.
2
```

**Verification:** Invalid input is rejected without contacting the model or
printing a traceback.

### 6. Run regression and structured-output tests

```bash
uv run --locked python -m pytest -q
```

**Command purpose:** `python -m pytest` runs the automated test suite, and `-q`
requests concise output. Tests are normally run after changes to catch broken
behavior in both new and previously working components.

**Expected key output:** `38 passed in ...`

**Verification:** Original LLM calls still work under test doubles, and prompt
settings, JSON validation, retry bounds, and error behavior pass their checks.
These offline tests do not prove the model's linguistic accuracy.

```bash
uv run --locked ruff check llm_client.py prompts.py tests
```

**Command purpose:** Ruff performs static checks for common Python mistakes.
It is typically run alongside tests because tests and static analysis catch
different problems.

**Expected output:** `All checks passed!`

**Verification:** The implementation passes the configured lint rules.

## What still requires judgment

The parser checks structure, not truth, tone, dialect fairness, or semantic
meaning. Separating system/user messages helps instruction handling but does
not make prompt injection impossible. A small model can still invent a rule,
miss a correction, or omit a requested follow-up question.

See `docs/tutoring_evaluation.md` for observed live results and failures during
prompt development. No pronunciation claim is justified by this text-only
component. Do not describe these checks as a comprehensive tutoring benchmark.

## Practice before moving on

Read one prompt and predict its effect. Then try a new incorrect sentence and a
correct sentence not present in the template; inspect both the conversation and
feedback. Explain why valid JSON is necessary but insufficient, and why empty
feedback can be the correct result. The next milestone adds session memory in
SQLite, which is intentionally not part of this step.
