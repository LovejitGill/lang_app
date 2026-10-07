# Plan the next question before choosing its wording

Current verification below targets planned_v3. See [constraint follow-ups](constraint_followups.md)
for its new behavior and [GitHub checkpoint guidance](github_checkpoints.md).

This experiment continues the same improvement: natural, grounded conversation
within the response-time target. Read the [before/after results](../evaluation/conversation_quality/planned_v3/results.md)
and [all 63 actual replies](../evaluation/conversation_quality/planned_v3/review.md).
It remains an experimental module; Streamlit still uses its existing conversation flow.

## Concepts to understand

A **dialogue policy** chooses what a tutor should do next: answer a question,
clarify a previous question, recall a learner fact, or ask for new information.
Here the policy covers a small set of explicit constructions. It is not a general
language-understanding system.

`dialogue_planner.py` records limited known information before forming choices.
For an unfinished assignment, it records that the task is unfinished and keeps the
stated feeling. Both offered questions concern an obstacle or needed help; neither
assumes the assignment was completed. For a future meal, questions concern a method
or choice reason rather than confirming the already-stated plan. Simple history
checks remove some questions whose answers are already supplied.

When several choices remain, Qwen3 selects an integer index. This is still an LLM
call, but the wording is authored. The model cannot introduce an unsupported bag
into a question that has no bag in its choices. The choice itself can still be
unnatural, and incorrect extraction can make every choice inappropriate: human
review is necessary. Unrecognized inputs keep the earlier natural-v4 generation path.

`learner_recall.py` quotes explicit learner statements from the last four turns.
Name and hobby statements can come from different turns. Supported newer retractions
replace or invalidate earlier facts. Tutor suggestions and other-person interests
are not learner evidence. Complex retractions and references remain a coverage risk.

`conversation_reference.py` supplies two authored word-pair explanations and a few
explicit question-meaning mappings. It distinguishes an illustrative example from
a fact about the learner. Unknown forms cannot silently inherit a known answer;
missing context receives a targeted request where supported. This is a small
reference catalog, not broad English question answering or retrieval from the web.

`dialogue_planner_eval.py` records model-generated prose, model-selected authored
questions, authored local replies and fallbacks separately. The fast two-rule grammar
adapter runs concurrently and can place a supported correction first. The approved
full grammar pipeline and the earlier conversation candidates remain preserved.

This is workflow development, prompt engineering and evaluation. No weights are
updated, no model is trained and no new paid service is introduced.

## Verification steps

1. Select the project directory.

   ```bash
   cd /Users/lovejit/PerScholas/AI_Solutions_dev/CAPSTONE/AI_Dev_CAPSTONE/lang_app
   pwd
   ```

   `cd` normally changes your working directory; here it selects SpeakWell.
   `pwd` normally prints that directory so relative file paths resolve as intended.

   Expected output:

   ```text
   /Users/lovejit/PerScholas/AI_Solutions_dev/CAPSTONE/AI_Dev_CAPSTONE/lang_app
   ```

   This verifies the checkout location, not whether local services are available.

2. Run the focused checks without real model inference.

   ```bash
   uv run --locked python -m pytest tests/test_dialogue_planner.py tests/test_conversation_reference.py tests/test_learner_recall.py -q
   ```

   `uv run --locked` uses the locked environment; `python -m pytest` normally runs
   Python tests. Here it checks planning, reference boundaries, retracted facts,
   no-follow-up controls and selector error handling.

   Expected output:

   ```text
   152 passed in ...s
   ```

   The duration varies. This verifies component behavior, not conversational
   usefulness. Stop here and explain why a recalled fact must come from the learner
   and why an absent grammar suggestion does not mean the sentence is correct.

3. Read the saved benchmark summary without more model calls.

   ```bash
   uv run --locked python -c 'import json; from pathlib import Path; print(json.dumps(json.loads(Path("evaluation/conversation_quality/planned_v3/warm_results.json").read_text())["summary"], indent=2))'
   ```

   `python -c` normally executes a short Python statement; this one reads a saved
   result. It verifies the recorded response counts while keeping quality labels separate.

   Key fields within the larger JSON output:

   ```json
   "completed": 63,
   "within_two_seconds": 63,
   "model_generated": 1,
   "model_selected": 21,
   "local_fallback": 10,
   "deterministic": 31,
   "human_useful": null
   ```

   The four path counts sum to 63. Reference and clarification counts are subsets
   of deterministic replies. `human_useful: null` means review is pending.

4. Optionally rerun the frozen experiment with an idle CPU.

   The existing Ollama service must be running on localhost:11434 with Qwen3 1.7B,
   and LanguageTool 6.6 on localhost:8081. Use the existing
   [service setup guide](separate_grammar_feedback.md) if needed, and choose an
   unused output filename to preserve earlier attempts.

   ```bash
   uv run --locked python dialogue_planner_eval.py --output /tmp/speakwell-planned-review-01.json
   ```

   This normally executes a prepared evaluation script; here it checks source,
   dataset and model identities, warms both inference paths and records every reply.

   Expected line shapes; model choices and timings vary:

   ```text
   D01 model_selected ...s: How did you decide what to pack?
   C10 deterministic ...s: ‘Lend’ means ...
   C13 deterministic ...s: What do you enjoy most about playing games?
   ```

   The saved result should contain 63 completed rows plus raw responses, plans,
   correction provenance and separate readiness timing. Review actual outputs;
   completion and a low delay are not quality scores. A changed-source error means
   a new candidate/protocol must be prepared before inference; do not rewrite old
   evidence to claim it measured different code.

## Practice exercise and next checkpoint

Trace D15 from its unfinished-task flag through the available question intents,
selected index and final reply. Then trace C13 to the actual prior tutor question
and learner topic; explain why an unrelated history row must not supply its meaning.

Propose a learner statement that falls outside the recognized patterns and predict
which path will handle it. This is a useful way to distinguish bounded coverage
from general intelligence. Test a name/hobby retraction and verify that the old
positive statement does not become the next question’s premise.

Next review D08/C12’s generic wording, N07’s dairy restriction and X04’s event flow.
Then freeze fresh multi-turn dialogues to test natural progress and context retention
within the same time budget. Only after quality review should this candidate be
considered for app integration and speech-end-to-first-useful-audio measurement
under real grammar load. The measured text result excludes speech,
UI/database work, readiness and the full grammar pass. Git commits/pushes remain
with the project owner.

GitHub checkpoint recommendation: yes for the tested planned_v3 experiment after reviewing accumulated changes; planned_v4 may hold the next iteration. Stable app promotion remains pending.
