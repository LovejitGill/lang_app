# Conversation quality and response time — development experiments

Latest checkpoint: [planned_v3 constraints and contextual follow-ups](constraint_followups.md).
GitHub checkpoint recommendation: yes for the tested experiment after owner review;
planned_v4 is the next experiment, not a stable app release.

Latest checkpoint: [planned follow-ups and local answers](dialogue_planning.md),
with [53 actual replies](../evaluation/conversation_quality/planned_v2/review.md).
Earlier experiment sections remain historical evidence; app integration is pending.

Latest October 6 revision: [natural follow-ups and timely corrections](natural_conversation.md),
with [all 41 actual responses](../evaluation/conversation_quality/natural_v4/review.md).
The earlier comparisons below remain historical evidence; no candidate is selected.

The active objective is **useful, grounded conversation with no more than two
seconds of response delay**. Neither requirement has been relaxed. These are
local comparison candidates; the app still uses its existing conversation model
and baseline prompt. The approved grammar flow is protected by source hashes.

Read the [original prompt comparison](../evaluation/conversation_quality/results.md)
and the [joint quality/timing report](../evaluation/conversation_quality/joint_results.md)
before interpreting any low latency as a successful tutoring result.

## What to learn

1. **Separate jobs.** A small model has less work when it supplies one relevant
   invitation instead of simultaneously inventing conversational facts, correcting
   grammar, explaining rules and formatting feedback.
2. **Ground a response in evidence.** The bounded candidate quotes a relevant
   learner statement for supported name/hobby/location questions. It does not
   treat the assistant's earlier assertions as evidence about the learner.
   These narrow patterns are not a general memory system or a truth detector.
3. **Use a wall-clock deadline.** An HTTP read timeout bounds an individual wait;
   it is not necessarily a deadline for the entire request. `asyncio.timeout`
   bounds the awaited operation, including local connection setup, and cancels
   the client request. OS scheduling and server cancellation are still imperfect.
4. **Make fallback measurable.** A fallback is an authored practice question
   returned when the model is late, unavailable or rejected. It is not generated
   output and is not automatically a quality pass. An unanswered question remains
   a failure even when the application responds immediately.
5. **Warm the actual configuration.** Loading a model with the default 4096-token
   context did not prepare the experimental 2048-token configuration. Warm-up must
   use the same configuration and an actual request; record its time separately.
6. **Validate format without claiming truth.** A lexical check can reject an
   unmentioned city or an obvious person change. It cannot establish that a
   question preserves meaning. Language explanations still require semantic review.

The Ollama API exposes `keep_alive`, context options and per-stage duration fields.
Its documentation describes [model residency and preloading](https://docs.ollama.com/faq)
and [chat response timings](https://docs.ollama.com/api/chat). These controls help
measure and reduce loading; they do not guarantee latency or answer quality.

## Files to study

| File | Responsibility |
| --- | --- |
| `conversation_prompts.py` | Preserve five prompt versions; the default remains baseline-v1. |
| `conversation_quality_eval.py` | Compare prompts on identical fixed histories; retain every attempt. |
| `bounded_conversation.py` | Supported session controls/quoted recall and authored questions; optional integer selection under a 0.9 s budget. |
| `bounded_conversation_eval.py` | Measure prepared, warm and cold-first conditions and record fallback counts. |
| `contextual_conversation.py` | Generate a short contextual invitation or language answer under a 1.4 s budget; reject detectable failures and retain raw output. |
| `contextual_conversation_eval.py` | Measure the current contextual candidate against its frozen protocol. |
| `conversation_model_eval.py` | Apply a prepared model identity only inside a separate evaluation process. |
| `evaluation/conversation_quality/` | Cases, protocols, raw results, diagnostics, historical source snapshots and pending reviews. |

The separate-grammar adapter delegates prompt construction/response parsing to
the new helpers. Its active conversation prompt is unchanged. No experimental
deadline path has been silently enabled in Streamlit.

## Verify locally

1. Open the project directory.

   ```bash
   cd /Users/lovejit/PerScholas/AI_Solutions_dev/CAPSTONE/AI_Dev_CAPSTONE/lang_app
   pwd
   ```

   `cd` changes the shell's working directory, and `pwd` prints it. They are
   normally used to ensure relative paths point to the intended checkout.

   Expected: `/Users/lovejit/PerScholas/AI_Solutions_dev/CAPSTONE/AI_Dev_CAPSTONE/lang_app`.
   This verifies the checkout, not model availability.

2. Run the experiment's component tests.

   ```bash
   uv run --locked python -m pytest tests/test_conversation_quality_eval.py tests/test_bounded_conversation.py tests/test_bounded_conversation_eval.py tests/test_contextual_conversation.py -q
   ```

   `uv run --locked` uses the locked environment; `python -m pytest` normally
   runs Python tests. These checks exercise evidence boundaries, malformed output,
   cancellation, raw-output retention and report checkpoints without real inference.

   Expected: `47 passed`. This verifies component behavior, not actual response
   quality or voice latency. In particular, the cancellation test proves that the
   client task stops; it does not prove immediate server-side cancellation.

3. Check which local models are available.

   ```bash
   bash scripts/ollama.sh list
   ```

   `bash` runs the local Ollama wrapper, and `list` normally displays installed
   models. This checks availability before running a prepared comparison.

   Expected entries include `qwen3:1.7b` and `qwen3:4b`; the later model comparison
   also uses `qwen2.5:1.5b`. Each evaluator verifies the exact prepared model digest.

4. Rerun the contextual Qwen3 candidate only when no other benchmark/tests are
   using the CPU, and choose an unused output filename.

   ```bash
   uv run --locked python contextual_conversation_eval.py --output /tmp/speakwell-contextual-review-01.json
   ```

   This command normally executes a prepared evaluation script; here it checks
   source/data/model identities, warms the exact configuration and saves every reply.

   Expected line shapes: `D03 model_generated ...s: ...` and
   `D13 deterministic ...s: Thanks for practicing. Goodbye!`. Model wording and
   timings vary; `local_fallback` means the model response was not used, not a pass.
   The report includes all 32 cases, startup time, raw rejected output and path counts.

5. Inspect the aggregate counts without making more model calls.

   ```bash
   uv run --locked python -c 'import json; print(json.dumps(json.load(open("/tmp/speakwell-contextual-review-01.json"))["summary"], indent=2))'
   ```

   `python -c` normally executes a short Python expression or script. Here it
   reads the saved report so you can separate generated replies, fallbacks and timings.

   Expected keys: `denominator`, `within_two_seconds`, `model_generated`,
   `local_fallback`, `unsupported_questions`, and `human_useful: null`.
   A null usefulness score is pending review, not zero or a passing score.

## Review the actual responses

For each input, read its history and the delivered reply, then assess whether it:

- answers a direct question when an answer is available;
- preserves the learner's people, negations, events and stated preferences;
- invites a relevant description, reason or example without repetitive questioning;
- respects requests to stop or omit a follow-up;
- uses understandable language without inventing praise, experiences or facts.

Review generated, deterministic and fallback paths separately. Do not count the
same input in repeated runs as a new independent example. These assistant-authored
cases and judgments need user review; they are development evidence, not held-out
validation. A prompt containing a known answer would invalidate the comparison.

## Limits and next checkpoint

The measured interval starts with confirmed text already in memory and ends with
a complete text reply. It excludes SQLite access, Streamlit rendering, microphone
capture, end-of-turn detection, speech recognition and spoken playback. Startup
is separately disclosed. The app also still blocks the next Send while grammar
is pending. None of these experiments proves a two-second phone-like experience.

The next checkpoint remains **conversation quality plus latency**: resolve direct
language-question failures and generic/repetitive invitations, review every path,
then validate on fresh conversations before app integration. Once a candidate
passes, measure speech-end to the first useful audible response under real grammar
workload. Both thresholds must remain explicit; fast text alone cannot finish it.

Learning exercise: trace one accepted question, one rejected question and one
timeout through `respond()`. Explain what information reaches the model, why a
fallback is recorded separately, and what failures can still pass the lexical
checks. Then propose two unfamiliar learner messages for the next review set.
