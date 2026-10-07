# Separate conversation and grammar feedback

This optional mode displays the conversational reply first, then checks the
confirmed learner text with the reviewed grammar flow. Enable **Separate grammar
feedback (experimental)** in the sidebar. Existing conversations and the earlier
combined mode remain available.

The sidebar now also offers **Context-aware conversation (experimental)** within
this mode. It integrates the planned_v4 conversation candidate while retaining this
same full grammar flow. See the [current integration guide](conversation_integration.md)
for activation, actual app timings and remaining limitations. The timings and test
counts below describe the original separate-feedback checkpoint.

The conversational model receives a reply-only prompt and recent saved history.
The grammar model sees only the submitted learner text; it does not receive
reference answers or conversation history. The app displays a correction only
when the existing rule detector supports the model's exact proposed edit. It
uses the reviewed explanations, including “is more than one,” rather than the
raw model's grammar explanation.

## What to learn from the implementation

- `separate_feedback.py`: one conversation-only request and one separately timed
  grammar pass. The conversation still uses Qwen3 1.7B; grammar uses the evaluated
  Qwen3 4B model digest and LanguageTool 6.6 with the existing supplemental rule.
- `feedback_store.py`: **atomic persistence** means saving both the reply and its
  pending grammar job in one SQLite transaction. Matching the turn ID, job ID,
  session and exact learner text prevents an old result being attached to a newer
  message. No database transaction stays open during inference.
- `feedback_worker.py`: a **background worker** is a separate thread that performs
  the grammar request while Streamlit can render the reply. It calls no Streamlit
  APIs; it saves results to SQLite for the UI to read. One worker processes jobs
  sequentially. This is scheduling, not faster inference or model training.
- `app.py`: render the reply before scheduling grammar, then poll local status
  once a second using a Streamlit fragment. A fragment reruns a small section
  of the interface without resending the learner message.

The additive `grammar_jobs` table stores status, accepted feedback and timing for
that exact turn. Historical turns are not rewritten. Accepted feedback is also
saved in the existing turn's feedback field; it is excluded from LLM history.

## Failure behavior and limits

- The reply survives a failed grammar model, invalid grammar response, unavailable
  checker or missing local runtime. Failed feedback is clearly **unavailable**,
  rather than presented as “no correction.” Raw model suggestions are not exposed
  when rule support is missing.
- An unsaved reply stays on screen with a warning; grammar is not scheduled for
  it because it lacks a persistent turn identity.
- Refresh restores completed feedback without another model call. If the app
  process restarts during a check, unfinished jobs become unavailable; they are
  not silently retried. This implementation assumes one Streamlit server process.
- The next Send and Transcribe actions wait for the current conversation's grammar
  check. You can draft the next message during that time. This limits CPU contention
  but does **not** deliver continuous phone-like conversation.
- New conversation preserves old results and cannot receive an old turn's result.
- Multiline input still gets a conversational reply; grammar reports that its
  single-line input scope is unsupported. Existing guards may also withhold
  corrections for quotes, compound clauses or unsupported rules.
- The targeted 32-case approval is not broad English accuracy. Conversation-only
  prompting and real learner comprehension need separate quality evaluation.
- No new dependency or paid service was added. The local grammar tools are now
  required when this option is enabled. Java still starts once per grammar input.
- Text and accepted feedback are persisted locally. The supplemental checker
  briefly writes text in its automatically cleaned temporary directory. This
  remains a local demonstration without accounts or encryption.

## Verify locally

Run the following from the project directory. Expected wording from a model is
variable; an unexpected correction is a quality failure, not a reason to rerun
until a preferred answer appears.

1. Locate the project:

   ```bash
   cd /Users/lovejit/PerScholas/AI_Solutions_dev/CAPSTONE/AI_Dev_CAPSTONE/lang_app
   pwd
   ```

   `cd` changes the working directory; `pwd` prints it. These commands are normally
   used to make sure relative script and data paths resolve to the correct project.

   Expected: the directory above. This verifies which checkout you are using.

2. Run the focused automated checks:

   ```bash
   uv run --locked python -m pytest tests/test_separate_feedback.py tests/test_feedback_store.py tests/test_separate_feedback_ui.py -q
   ```

   `uv run --locked` uses the locked Python environment; `python -m pytest` runs
   regression tests. Here the tests check saved evaluation evidence, real temporary
   SQLite storage, failure handling and UI behavior with controlled model responses.

   Expected: `27 passed`. This checks wiring and preservation of reviewed
   decisions, not fresh model quality or response speed.

3. Confirm the two local model names:

   ```bash
   bash scripts/ollama.sh list
   ```

   `bash` executes the project's Ollama wrapper, and `list` normally lists models
   installed in its local model store. This checks the names needed by both passes.

   Expected table entries: `qwen3:1.7b` and `qwen3:4b`. Grammar also verifies the
   evaluated 4B digest before using it; another model version is not silently accepted.

   If the intended Ollama server is not already running, start it in a separate terminal:

   ```bash
   bash scripts/ollama.sh serve
   ```

   `serve` starts the local inference service used by Python requests. It normally
   remains running while the application is in use.

   Expected log fragment: `127.0.0.1:11434`. Keep that terminal open; do not start
   another instance if this port is already in use by your intended server.

4. Start the local grammar server only if it is not already running:

   ```bash
   bash scripts/languagetool.sh
   ```

   This wrapper starts the installed LanguageTool 6.6 HTTP server with local Java.
   It is normally kept running so Python can request grammatical rule evidence.

   Expected log fragment: `8081`, with the process remaining running. If the
   wrapper reports missing tools, follow `docs/benchmarking.md`; the optional
   installer is pinned for Intel macOS and downloads free local tools.

5. Start Streamlit if it is not already running; otherwise refresh the app:

   ```bash
   uv run --locked streamlit run app.py --server.address 127.0.0.1 --server.port 8501
   ```

   This starts the Python UI server in the locked environment, bound to your
   computer's loopback interface. Streamlit normally serves the app to a local browser.

   Expected: a URL containing `http://127.0.0.1:8501`. Open it and enable
   **Separate grammar feedback (experimental)** before sending a message.

6. Send `They planted fifteen seed.`.

   Expected sequence: a conversational reply, **Checking grammar…**, then
   `seed → seeds` and `‘Fifteen’ is more than one, so use the plural ‘seeds’.`
   A suggested full sentence and separate timings appear with this turn.
   This verifies that the reply renders before feedback and that the approved
   counted-noun explanation is used. The model's reply wording may vary.

7. Send `I enjoy hiking.` after the first check finishes.

   Expected grammar status: **No correction suggested. This does not guarantee
   the message is error-free.** This checks that acceptable language is preserved.
   Reload the page: both turns and completed feedback should remain, without
   another “checking” cycle.

8. To check failure behavior, stop only the grammar server you started with
   Ctrl+C, then send a short message while Ollama remains running.

   Ctrl+C normally interrupts the foreground terminal process. Here it simulates
   an unavailable grammar service without stopping conversation generation.

   Expected: the conversational reply remains, followed by a grammar-unavailable
   message. Restart the grammar server for later turns; an unavailable old check
   is not automatically retried. Do not interrupt someone else's server.

## Read the measurements correctly

- **Reply generation:** server time from handling the submitted text through
  history loading, conversation generation and parsing; it excludes saving the
  reply and browser rendering.
- **Grammar processing:** time inside the separate grammar pass, including model
  identity checking, generation and both grammar checkers.
- **Feedback ready after Send:** server time from handling the submission through
  completion of the feedback computation, including reply work and queue delay;
  it excludes the final database commit, browser polling and rendering. The label
  refers to server readiness, not a measured browser paint timestamp.

Polling can add up to about one second before a completed result appears. These
numbers exclude microphone capture, speech recognition and spoken output; they
cannot establish the two-second voice target. Measure first-run and subsequent
turns separately before optimizing model loading or Java startup.

## Learning checkpoint

Trace one job from `send_separate()` to `save_reply()`, `run_job()`, `finish()` and
`refresh_grammar()`. Explain why using “the last turn” would be unsafe, why a failed
check is different from a clean sentence, and why displaying a reply earlier does
not reduce total inference work. Then inspect a saved timing record and identify
which portion is model time and which is supplemental checker time.

## Verification outcome

See [the verification report](separate_grammar_feedback_validation.md) for the
341-test result, actual outputs, measured delays, failed first-prompt observations
and the next focused improvement. The completed integration does not imply that
conversation quality or the two-second target is solved.
