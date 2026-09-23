# Milestone 4 — Streamlit UI (text input first)

`app.py` provides practice settings, a submitted text form, chronological chat,
separate language feedback, and a next-turn counter. It reuses `ask_tutor()` and
SQLite. This guide describes the text checkpoint; microphone recording and
transcription were added in [Milestone 5](recorded_voice.md). Speech output is
not implemented.

## How state works

Streamlit reruns the script after an interaction. `st.session_state` keeps the
conversation and display state through those reruns; the form batches typing
until Send. Generation happens only on submission, not on a normal display rerun.

A new conversation gets an opaque UUID, saved level/scenario metadata in the
SQLite `sessions` table, and a `?session=...` URL parameter. A fresh page reload
uses that ID to hydrate the transcript and counter from SQLite once. Settings
are fixed while a conversation is active so refresh cannot change its mode.

**Refresh limits:** Only successfully saved turns survive refresh. Unsent drafts
and generated-but-unsaved replies are not durable. Keep the session URL to resume
a conversation; opening the base URL starts a new selection screen. Old CLI-only
session IDs have no UI metadata and cannot be resumed in this UI.

**Local privacy:** URLs are lookup identifiers, not authentication. Anyone with
access to this local app and a session URL can view that transcript. The launcher
below binds to localhost; this is not a public multi-user service.

## Start and verify

### 1. Open the project directory

```bash
cd /Users/lovejit/PerScholas/AI_Solutions_dev/CAPSTONE/AI_Dev_CAPSTONE/lang_app
pwd
```

**Purpose:** `cd` changes the working directory and `pwd` prints it. These are
normally used to confirm that commands run against the intended project files.

**Expected output:** `/Users/lovejit/PerScholas/AI_Solutions_dev/CAPSTONE/AI_Dev_CAPSTONE/lang_app`

**Verification:** You are in the folder containing `app.py` and `uv.lock`.

### 2. Start Ollama if it is not already running

In Terminal A:

```bash
bash scripts/ollama.sh serve
```

**Purpose:** Runs the project's wrapper to start the local model server. This
service normally stays open while the UI sends model requests.

**Expected log fragment:** `Listening on 127.0.0.1:11434`

**Verification:** Ollama is ready. Keep this terminal open; do not start another
copy if the intended server already exists.

### 3. Start Streamlit

In Terminal B, from the same directory:

```bash
uv run --locked streamlit run app.py --server.address 127.0.0.1 --browser.gatherUsageStats false
```

**Purpose:** `uv run --locked` uses the project's locked environment, and
`streamlit run` serves the Python UI in a browser. The options bind it locally
and disable Streamlit usage-statistics collection for this launch.

**Expected key output:**

```text
You can now view your Streamlit app in your browser.
URL: http://127.0.0.1:8501
```

The URL label can differ by Streamlit version. Open the displayed address.

**Verification:** The page shows SpeakWell, Level, Scenario, and Start conversation.
There is no `python app.py` launch step: Streamlit supplies the runtime context.

### 4. Complete three turns in the browser

Choose settings and select **Start conversation**. Submit these messages one at
a time, waiting for each reply:

1. `My name is Maya and I enjoy hiking.`
2. `I usually hike on Saturdays.`
3. `What is my name and when do I usually hike?`

**Expected display:** Three learner/tutor pairs in order, a **Language feedback**
label under each reply, and **Turn #4** above the next input. The final reply should
identify Maya and Saturdays; model wording can vary.

**Verification:** Input, inference, persistence, and rendering work together.
Language feedback may be wrong even when the conversation and memory work.

### 5. Check refresh and failures

- Refresh the current session URL. Expect the same saved three turns, settings,
  and **Turn #4**, without a fourth model call or duplicated rows.
- Submit a blank message. Expect **Enter a message before sending.** and no
  counter increment.
- If you started Ollama for this exercise, stop it with Ctrl+C in Terminal A,
  then send a message. Expect a readable connection error and the draft to remain
  in the box; restart Ollama before pressing Send again.
- Select **New conversation**. Expect empty history and a new settings screen.
  This does not delete prior rows; the old saved URL can still restore them.

**Verification:** Display reruns preserve state, failures do not create completed
turns, and a new conversation does not mix old learner context.

### 6. Run automated checks

```bash
uv run --locked python -m pytest -q
```

**Purpose:** Runs the project's automated tests with concise output. Regression
tests are typically run after UI changes to catch backend and session-state bugs.

**Expected key output:** `96 passed in ...` (including later audio/evaluation checks).

**Verification:** Tests cover the existing backend plus three-turn UI flow,
fresh-session hydration, no regeneration on ordinary rerun, empty input,
connection failure, write failure, new conversations, and missing-session recovery.

## Implementation notes and limitations

- New, empty conversations show an authored practice prompt selected by level
  and scenario. It invites a description or explanation, with sentence starters
  for beginners, without calling the model or saving an artificial turn.
- To check the new prompts, select **New conversation**, choose beginner and
  introductions, then **Start conversation**. Expect “Introduce yourself and
  tell me about something you enjoy doing.” Submit `Hiking.`; an illustrative
  reply is “Tell me about a hike you enjoyed.” Wording varies; verify that the
  follow-up invites an experience or explanation rather than a one-word answer.
- Follow-up quality and correction accuracy require human review. The automated
  checks verify prompt selection and UI behavior, not whether English feedback
  is trustworthy. The earlier inaccurate-feedback limitation remains open.

- Read `restore_page()` first, then the settings/start path, transcript loop,
  and submitted-form branch in `app.py`.
- `turn_number` counts generated exchanges, including a visible unsaved reply.
  After refresh, it is reconstructed from persisted rows, so unsaved turns vanish.
- Save failures show a persistent **Not saved** warning while preserving the
  reply on the current page. There is no save-only retry control yet.
- Errors keep the draft available. A new successful submission clears it and
  advances the counter once.
- Full transcript loading occurs once per page session; the model still receives
  only bounded recent context. Very long transcripts are not paginated yet.
- `SPEAKWELL_DB_PATH` optionally selects a separate UI database for testing;
  it does not change CLI defaults. Normal use writes to `data/speakwell.sqlite`.
- Ordinary reruns are tested, but simultaneous tabs/submissions are not a
  transactionally deduplicated workflow. Use one active tab per conversation.
- UI settings changes do not implement separate curricula. Those still need
  learning content and evaluation.

The refresh design follows Streamlit's distinction between rerun state and a
new browser connection. [Session State documentation](https://docs.streamlit.io/develop/api-reference/caching-and-state/st.session_state).
Automated UI checks use simulated Streamlit execution; visual inspection is
separate. [AppTest documentation](https://docs.streamlit.io/develop/api-reference/app-testing/st.testing.v1.apptest).
