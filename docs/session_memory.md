# Milestone 3 — Session Memory in SQLite

`db.py` stores completed learner/tutor exchanges. `ask_tutor()` can load recent
turns before generation and save the validated result afterward. The LLM has no
persistent memory of its own: the application explicitly supplies earlier text
again with each request.

## What to read

- `init_db()` uses `CREATE TABLE IF NOT EXISTS` and creates a session/order index.
- `insert_turn()` uses a parameterized `INSERT`: values go through `?`
  placeholders rather than being interpolated into SQL. One row contains the
  learner text, tutor reply, feedback JSON, session ID, numeric ID, and UTC timestamp.
- `get_history()` selects the latest N turns for one session, then returns those
  turns in oldest-to-newest order. Row IDs determine ordering, even when multiple
  turns share a timestamp.
- `_history_messages()` builds alternating user/assistant messages from saved
  learner text and tutor replies. Old feedback is stored for review but is not
  resent as instructions or repeated corrections.
- `ask_tutor(..., session_id=...)` adds history between the system instruction
  and the new learner message, then saves only a successfully validated exchange.

The default prompt includes at most four previous complete exchanges, further
limited to 3,000 characters of historical learner/reply text. The latest learner
input is limited to 1,000 characters. This is a simple bound, not exact token
accounting or proof that every possible input fits the model's context window.

Connections are explicitly closed; write transactions commit or roll back.
No transaction stays open during a model call. SQLite is included with Python,
so no package installation or database server is required.

## Persistence and failure behavior

- Without `--session` (or `session_id` in Python), tutoring remains stateless and
  does not create or use a database.
- The default database is `data/speakwell.sqlite`, resolved relative to the
  project module. `--db` lets you use a separate test database.
- Reusing a session ID reloads that session across separate Python processes.
  Use a new ID for a new learner or practice scenario. IDs distinguish histories;
  they are not authentication credentials.
- Failed generation or invalid output after the bounded retry creates no row.
- A database initialization/read error stops the turn with a readable error;
  the application does not silently pretend it loaded context.
- A save failure preserves the generated reply and emits `HistorySaveWarning`
  in Python, or `History warning:` on CLI stderr. The unsaved turn will not be
  remembered; CLI success in this case means generation succeeded, not storage.
- History is plain text on disk and remains after exit. There is no automatic
  expiry, deletion UI, encryption, or multi-user access control. `data/` is
  excluded from Git; use synthetic content for these checks.

## Verification steps

### 1. Open the repository

```bash
cd /Users/lovejit/PerScholas/AI_Solutions_dev/CAPSTONE/AI_Dev_CAPSTONE/lang_app
pwd
```

**Purpose:** `cd` changes the working directory, and `pwd` displays it. These
commands are typically used to confirm that project-relative paths resolve as intended.

**Expected output:** `/Users/lovejit/PerScholas/AI_Solutions_dev/CAPSTONE/AI_Dev_CAPSTONE/lang_app`

**Verification:** You are in the repository containing `db.py` and `llm_client.py`.

### 2. Ensure the local model server is available

If your project server is not already running, use a separate terminal in the same directory:

```bash
bash scripts/ollama.sh serve
```

**Purpose:** `bash` executes the project's Ollama wrapper, and `serve` starts
the local inference service. A server normally stays running while separate
Python programs send requests to it.

**Expected log fragment:** `Listening on 127.0.0.1:11434`

**Verification:** Local model requests can be accepted. Keep that terminal open;
do not start a second server if your intended instance already exists.

### 3. Save a first turn

In the other terminal:

```bash
uv run --locked python llm_client.py --tutor --session memory-check-1 \
  --db data/memory_check.sqlite "My name is Maya and I enjoy hiking."
```

**Purpose:** `uv run --locked` executes Python in the project's reproducible
environment. `--session` groups saved turns, and `--db` selects a separate SQLite
file, a common way to keep verification data separate from normal use.

**Expected output shape** (model wording varies):

```json
{"reply": "What kind of hiking do you like?", "feedback": []}
```

**Verification:** The reply is generated and the completed exchange is saved
unless a history warning appears. The model may still overcorrect this valid
sentence; that known Milestone 2 limitation is independent of successful saving.

### 4. Recall it in a new Python process

```bash
uv run --locked python llm_client.py --tutor --session memory-check-1 \
  --db data/memory_check.sqlite "What is my name and what hobby did I mention?"
```

**Purpose:** Running the program again starts a new Python process and reloads
the same session from SQLite. Restarting between calls is a useful check that
memory is persisted rather than held only in a Python variable.

**Expected reply content:** The reply should identify **Maya** and **hiking**;
the exact wording and feedback can vary.

**Verification:** A sensible reference to the earlier facts demonstrates that
saved context reached the model and was used. An incorrect answer is a failed
recall check even if two rows were saved.

### 5. Inspect rows without invoking the model

```bash
uv run --locked python -c 'from pathlib import Path; from db import get_history; rows = get_history("memory-check-1", db_path=Path("data/memory_check.sqlite")); print("Stored turns:", len(rows)); print([r["learner_text"] for r in rows])'
```

**Purpose:** Python's `-c` runs a short inline inspection, commonly used to
check stored data without writing another script. This reads SQLite directly
through the helper and performs no inference.

**Expected output for a fresh verification session:**

```text
Stored turns: 2
['My name is Maya and I enjoy hiking.', 'What is my name and what hobby did I mention?']
```

**Verification:** Both complete turns survived separate process exits and are
returned in chronological order. Rerunning the earlier calls creates more rows;
use a new session ID consistently if you want a fresh two-turn check.

Alternatively, open `data/memory_check.sqlite` in your SQLite database viewer,
select the `turns` table, and inspect `session_id`, `learner_text`, `tutor_reply`,
`feedback_json`, and `created_at`. The visible rows should match this inspection.

### 6. Run automated checks

```bash
uv run --locked python -m pytest -q
```

**Purpose:** `python -m pytest` runs the test suite, and `-q` requests concise
output. Regression tests are commonly run after storage changes to catch
session leaks, ordering mistakes, or failure-handling regressions.

**Expected key output:** `55 passed in ...`

**Verification:** Tests cover existing behavior plus persistence, isolation,
parameterized SQL, chronological limits, history budgeting, actual prompt
assembly, retries, failed generation, and a real SQLite write lock. Temporary
test databases do not modify your saved learner history.

## Learning checkpoint

Explain why saving text alone does not give the model memory, why a descending
SQL query is reversed before prompt construction, and why a failed model call
must not create an apparently completed turn. Find the exact prior user and
assistant messages in `test_two_calls_send_prior_turn_and_save_only_once`.

The next milestone is the text-first Streamlit UI. This milestone has not added
that UI, voice input, account management, or a general-purpose memory service.
