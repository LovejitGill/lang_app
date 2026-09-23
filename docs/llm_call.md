# Milestone 1 — Call the LLM from Python

The component is `ask_llm(prompt: str) -> str` in `llm_client.py`.
It validates input, calls local Qwen3 through the installed Ollama Python SDK,
and returns only the generated reply. There is no history, system tutoring
prompt, feedback parsing, database, or UI yet.

## How the component works

1. Validate before contacting the model. Blank or non-string input raises
   `ValueError` so callers can distinguish bad input from a service failure.
2. Create a client for `http://127.0.0.1:11434`. The SDK sends an HTTP request
   containing JSON to the local Ollama server; the Python package does not run
   the model itself. The client closes at the end of the `with` block.
3. Send one user message to `qwen3:1.7b`, with `think=False`, `stream=False`,
   a 4,096-token context and a 128-token generation cap. These bound this small
   experiment; longer requested answers can be cut short by the output cap.
4. Extract `response.message.content`, trim it, and reject an empty reply.
5. Translate expected network/server failures into `LLMError`. Errors are never
   returned as if they were model-generated text.

The client has a three-second connection timeout and 30-second timeouts for
other HTTP operations. These are transport limits, not a strict end-to-end
deadline or a two-second responsiveness claim. HTTPX is now a direct dependency
because the component uses its timeout and exception types explicitly.

The terminal entry point catches `ValueError` and `LLMError` and prints a short
message without a traceback. A Python caller should catch these exceptions too.
Exit codes are 0 for success, 2 for invalid input, and 1 for service failure.

## Verify it yourself

### 1. Open the repository in two terminals

Run in both Terminal A and Terminal B:

```bash
cd /Users/lovejit/PerScholas/AI_Solutions_dev/CAPSTONE/AI_Dev_CAPSTONE/lang_app
pwd
```

Expected output:

```text
/Users/lovejit/PerScholas/AI_Solutions_dev/CAPSTONE/AI_Dev_CAPSTONE/lang_app
```

**What this verifies:** Both terminals use the same project, scripts, model
directory, and dependency lockfile.

### 2. Synchronize dependencies in Terminal B

```bash
uv sync --locked
```

Expected key output resembles:

```text
Resolved ... packages ...
Checked ... packages ...
```

On a fresh checkout, `Installed ... packages` may appear instead. Counts and
timings are not the acceptance criterion; successful completion is.

**What this verifies:** The project environment matches the lockfile, including
the directly declared HTTPX dependency.

### 3. Start the model server in Terminal A

```bash
bash scripts/ollama.sh serve
```

Expected log fragment:

```text
Listening on 127.0.0.1:11434
```

**What this verifies:** The local service is listening for requests. Leave this
terminal running. If the port is already in use, confirm whether your intended
Ollama instance is already running rather than starting another or killing it.

### 4. Run the Python component in Terminal B

```bash
uv run --locked python llm_client.py
```

Expected shape (generated wording can vary):

```text
Tutor: Hello! How can I assist you today?
```

**What this verifies:** Python successfully sends the default hardcoded greeting
prompt, receives model-generated text, and prints a non-empty reply. `Tutor:` is
only a display label; a tutoring system prompt is a later milestone.

### 5. Supply your own prompt

```bash
uv run --locked python llm_client.py "Name one common fruit. Keep it brief."
```

Example output, not a fixed expected answer:

```text
Tutor: Apple.
```

**What this verifies:** The component sends the provided prompt rather than
always generating a greeting. For this manual check, look for a relevant,
non-empty answer; exact model wording is not deterministic.

### 6. Check empty-input handling

```bash
uv run --locked python llm_client.py ""
echo $?
```

Expected output:

```text
Input error: Enter a non-empty text prompt.
2
```

**What this verifies:** Invalid input is rejected before a network call, with a
readable message and a deliberate nonzero exit status rather than a traceback.

### 7. Run offline component tests and lint checks

```bash
uv run --locked python -m pytest -q
uv run --locked ruff check llm_client.py tests/test_llm_client.py
uv run --locked ruff format --check llm_client.py tests/test_llm_client.py
```

Expected key output:

```text
14 passed in ...
All checks passed!
2 files already formatted
```

**What this verifies:** Tests use a fake client to check success, blank/non-string
input, connection failure, timeout, missing model, server errors, interrupted
connections, empty model replies, and CLI error handling. They do not need the
server. The real call in Step 4 separately verifies actual inference. Ruff checks
basic code issues and consistent formatting.

### 8. Check the server-unavailable case

If you started Terminal A's server, stop it with Ctrl+C there. The normal shell
prompt should return. Then run in Terminal B:

```bash
uv run --locked python llm_client.py
echo $?
```

Expected output:

```text
LLM error: Cannot reach Ollama. Start it with: bash scripts/ollama.sh serve
1
```

**What this verifies:** A stopped server produces an actionable error, not a
crash traceback or a fabricated tutor reply. Restart the server before further
LLM work. Stop only the server you started for this exercise.

## Learning checkpoint

### Verified results on 2026-09-22

The real Python greeting call returned `Tutor: Hello! How can I assist you today?`.
The custom fruit prompt returned `Tutor: Apple.`. Empty input exited with status
2 and the documented input message. With Ollama stopped, the command exited with
status 1 and the documented connection message. All 14 offline tests passed;
Ruff lint and formatting checks passed. The server started for verification was
stopped afterward. No Git commit or push was made.

Read `llm_client.py` and explain why input validation happens before `Client`,
why `think=False` and `stream=False` are separate settings, why errors are raised
rather than returned as strings, and why the CLI catches them. Then change only
the prompt and observe the response before moving to tutoring prompt design.

This milestone does not demonstrate grammar correction quality, memory, audio,
or near-real-time conversation. The existing implementation plan remains
unchanged; the next milestone is tutoring prompt design.
