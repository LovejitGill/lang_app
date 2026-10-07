# Natural follow-ups and timely corrections — learning and verification

The next iteration is documented in [dialogue planning](dialogue_planning.md).
This page preserves the natural-v4 experiment and its reproducible checks.

This October 6 experiment implements the owner’s topic/style feedback while
keeping natural conversation and response speed as joint requirements. It is
**not enabled in Streamlit**. Read the [measured results](../evaluation/conversation_quality/natural_v4/results.md)
and [all 41 actual replies](../evaluation/conversation_quality/natural_v4/review.md).
Some targeted responses improved, but remaining failures prevent selection.

## What the design teaches

`natural_conversation.py` prepares an authored fallback from the learner’s stated
topic, requests a short Qwen3 question when appropriate, and rejects observable
problems such as padded endings or a changed subject. Model generation has a
1.4-second best-effort budget. Authored replies are explicitly labeled; they are
not evidence that the LLM learned the owner’s preferred wording.

`timely_corrections.py` independently asks the resident local LanguageTool server
for rule evidence, with a 0.2-second budget. Only two narrow rule families can
offer an edit: the base verb after “did,” and simple third-person present agreement.
It checks exact text positions, context, conflicts, tense and supported replacements.
Unsupported, ambiguous or late results yield no fast offer. This does **not** mean
the sentence is correct, and it does not replace the approved full grammar pass.

`asyncio.gather` waits for both tasks while allowing their network waits to overlap.
When supported correction evidence arrives in time, the assembled text places the
corrected sentence and explanation before the conversational reply. Concurrent
work avoids adding the two delays sequentially; it cannot remove CPU contention.
The actual elapsed time is measured, since timers cannot promise hard real time.

For C15, “I take a short walk because it helps me relax” describes a habit. Changing
“take” to “took” would change its meaning without evidence. “Yesterday I take a
short walk” needs “took,” but that tense rule is outside this fast adapter’s scope.

Topic matching is not truth checking: a question can mention the right food while
inventing a location. Human review remains necessary. Current failures include
invented premises, repeated information, generic recall and unanswered language
questions. No model weights are updated; this is prompt/workflow development and
evaluation, not model training.

## Verify in small steps

1. Open the project directory and confirm its location.

   ```bash
   cd /Users/lovejit/PerScholas/AI_Solutions_dev/CAPSTONE/AI_Dev_CAPSTONE/lang_app
   pwd
   ```

   `cd` normally changes the current directory; here it selects this checkout.
   `pwd` normally prints the current directory, confirming where later relative paths resolve.

   Expected output:

   ```text
   /Users/lovejit/PerScholas/AI_Solutions_dev/CAPSTONE/AI_Dev_CAPSTONE/lang_app
   ```

   This verifies the path, not whether local model services are running.

2. Run the isolated component checks without model inference.

   ```bash
   uv run --locked python -m pytest tests/test_natural_conversation.py tests/test_timely_corrections.py -q
   ```

   `uv run --locked` uses the locked Python environment; `python -m pytest` normally
   runs automated Python tests. Here it checks topic handling, correction boundaries,
   malformed output, cancellation and correction-first assembly.

   Expected output:

   ```text
   111 passed in ...s
   ```

   Duration varies. This verifies observable program behavior, not naturalness or
   speech latency. Stop and trace one fallback and one supported correction before
   continuing; understand why an absent correction is not a clean-grammar judgment.

3. Inspect the saved live result without making new model calls.

   ```bash
   uv run --locked python -c 'import json; from pathlib import Path; print(json.dumps(json.loads(Path("evaluation/conversation_quality/natural_v4/warm_results.json").read_text())["summary"], indent=2))'
   ```

   `python -c` normally executes a short Python statement; here it prints the saved
   benchmark summary. This distinguishes timing and response paths from human quality scores.

   Key expected fields:

   ```json
   "completed": 41,
   "within_two_seconds": 41,
   "model_generated": 9,
   "local_fallback": 8,
   "deterministic": 24,
   "timely_corrections": 2,
   "human_useful": null
   ```

   These are fields within a larger JSON object. `null` means review is pending;
   it is neither a passing score nor zero useful replies.

4. Optionally rerun the prepared live experiment, with the CPU otherwise idle.

   Prerequisites: the existing Ollama service on localhost:11434 with the prepared
   Qwen3 1.7B digest, and LanguageTool 6.6 on localhost:8081. Reuse the project’s
   [local service setup](separate_grammar_feedback.md); no paid service is required.
   Choose an unused output filename so previous evidence remains preserved.

   ```bash
   uv run --locked python natural_conversation_eval.py --output /tmp/speakwell-natural-review-01.json
   ```

   This command normally runs a Python evaluation script; here it verifies frozen
   identities, warms the actual configuration and records every attempted reply.

   Expected line shapes (wording, paths and timings may vary on a new model run):

   ```text
   D02 deterministic ...s: “Did you visit the castle?” ...
   D09 local_fallback ...s: How did the rice turn out?
   D12 local_fallback ...s: “She goes to work by train.” ...
   ```

   The saved report should contain 41 completed rows plus raw output and path labels.
   A completed run verifies execution; review the actual replies before deciding
   quality. A deadline or a sub-two-second text result does not establish a passing
   conversation or phone-like spoken performance.

   If the script reports `Prepared source changed`, stop: freeze the intentional
   new revision and a new protocol before measuring it. Do not edit old evidence
   to make a changed implementation appear to be the previous candidate.

## Practice task and next improvement

Trace D09’s rejected model reply and authored fallback, then compare D12’s separate
checker evidence with its conversational output. Explain why the system can offer
“goes” quickly while leaving another genuine error such as “Yesterday I take…”
unaddressed in this fast path.

Next keep the same focus: eliminate repeated questions, invented premises, generic
recall and unanswered tutoring questions within the latency budget. Review fresh
multi-turn conversations before integration, then measure speech-end to first
useful audio with full grammar processing active. Broader grammar explanations
remain a later iteration. Git staging, commits and pushes remain the owner’s work.
