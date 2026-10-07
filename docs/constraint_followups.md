# Constraint acknowledgment and specific follow-ups — planned_v3

This iteration continues conversation quality and latency. It adds correct-person
food acknowledgments and better questions about journeys, expected results and
interviews. It remains outside the live Streamlit conversation flow.

Read the [before/after results](../evaluation/conversation_quality/planned_v3/results.md)
and [all 63 actual replies](../evaluation/conversation_quality/planned_v3/review.md).
All human usefulness judgments remain pending; a rendered reply is not a quality pass.

## What to learn

A **constraint** limits suitable responses: the learner cannot eat dairy, for
example. Acknowledging that statement does not establish which soups contain dairy
or which foods are safe. `food_constraints.py` records explicit statements with
the correct person, separates ability from preference, and applies supported recent
corrections. A sister’s restriction must not become the learner’s restriction.

`contextual_followups.py` avoids asking again for a supplied reason or feeling.
It distinguishes habitual, future and completed travel, preserves negated emotions,
and uses explicit learner history for an upcoming interview. A completed interview
needs a different next question; answering every question does not prove correct
answers or an admission decision.

The helpers supply authored choices to `dialogue_planner.py`. Qwen3 selects an
index when several choices remain; the prefix acknowledging a restriction stays
attached even if selection times out. These are model-selected authored replies,
not newly generated prose. Exact-repeat filtering removes some repeated questions;
when all choices are exhausted, the new route returns an acknowledgment instead
of switching to unrestricted generation. Its conversational usefulness still needs review.

The helpers support limited declarative syntax and four recent learner turns.
Unsupported wording can cause abstention or conservative loss of remembered facts.
No model is trained, and the approved full grammar pipeline is unchanged.

## Verify the implementation

1. Select the checkout.

   ```bash
   cd /Users/lovejit/PerScholas/AI_Solutions_dev/CAPSTONE/AI_Dev_CAPSTONE/lang_app
   pwd
   ```

   `cd` normally changes the working directory; here it selects SpeakWell.
   `pwd` normally prints it, confirming where subsequent relative paths resolve.

   Expected: `/Users/lovejit/PerScholas/AI_Solutions_dev/CAPSTONE/AI_Dev_CAPSTONE/lang_app`.
   This verifies the directory, not service availability.

2. Run the focused component checks without real inference.

   ```bash
   uv run --locked python -m pytest tests/test_contextual_followups.py tests/test_food_constraints.py tests/test_dialogue_planner.py -q
   ```

   `uv run --locked` uses the locked environment; `python -m pytest` normally runs
   Python tests. This set checks person/negation/time boundaries, recent revisions,
   no-follow-up controls and preserved acknowledgments.

   Expected: `96 passed in ...s` (duration varies).
   This verifies observable behavior, not general conversational naturalness.

3. Inspect saved results without another model run.

   ```bash
   uv run --locked python -c 'import json; from pathlib import Path; print(json.dumps(json.loads(Path("evaluation/conversation_quality/planned_v3/warm_results.json").read_text())["summary"], indent=2))'
   ```

   `python -c` normally runs a short Python statement; here it reads the saved
   benchmark. This verifies recorded counts without confusing them with a quality score.

   Key fields within the larger JSON object:

   ```json
   "completed": 63,
   "within_two_seconds": 63,
   "model_generated": 1,
   "model_selected": 21,
   "local_fallback": 10,
   "deterministic": 31,
   "human_useful": null
   ```

   Path counts sum to 63. `null` means quality review is pending, not passed.
   Maximum complete text time was 1.407 seconds; readiness was 6.249 seconds separately.

4. Optionally repeat the frozen live experiment with other benchmarks/tests idle.

   Prerequisites are the existing local Ollama service with the prepared Qwen3 1.7B
   model and resident LanguageTool 6.6. Reuse the [service setup guide](separate_grammar_feedback.md)
   and choose a new output filename so earlier evidence remains intact.

   ```bash
   uv run --locked python dialogue_planner_eval.py --output /tmp/speakwell-planned-v3-review-01.json
   ```

   This normally runs an evaluation script; here it verifies prepared source/data/model
   identities, warms both model paths and records every response and fallback.

   Example line shapes; model choices, paths and timings can vary:

   ```text
   D08 model_selected ...s: How does taking the bus fit into your day?
   N07 model_selected ...s: You can't eat dairy. ...
   X04 model_selected ...s: That sounds like a relief for your son. ...
   ```

   Verify all 63 rows are complete, then review their actual wording and histories.
   If prepared-source verification fails after an intentional code change, create
   the next protocol/version; do not rewrite old results to match new code.

## Practice task and next improvement

Trace N07 from the explicit dairy statement to its authored prefix and selected
question. Then trace Y03/Y04: explain why the prefix still identifies the right
person after a timeout and why a current correction outranks older history.
Compare X04’s upcoming interview with Y10’s completed interview and identify what
information may be asked next without claiming acceptance or arrival.

Next review the exercise-like food wording and abstract phrases such as “fit into
your day,” then test fresh multi-turn conversation using actual tutor replies as
history. Preserve the original quality and two-second objectives. Text timing
excludes readiness, UI/database work, STT, turn detection, speech synthesis/playback
and full grammar contention; spoken latency remains unverified.

**GitHub checkpoint: yes**, after reviewing the accumulated source, tests, docs and
synthetic evidence. This is a useful experimental snapshot; [checkpoint steps](github_checkpoints.md)
leave Git operations with you. Current experiment is `planned_v3`; `planned_v4`
can hold the next reviewed experiment. Neither label promotes the app to a stable
v3/v4 release or changes package version `0.1.0`.
