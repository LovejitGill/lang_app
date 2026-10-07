# Conversation quality comparison — no candidate selected

On 2026-10-05, tested five prompt versions across seven prompt/model configurations:
**112 calls on the same 16 development cases**, not 112 unique examples. Every call
returned valid JSON, but that did not establish useful or accurate conversation.
The app's active conversation-only profile remains baseline-v1 with Qwen3 1.7B.
The reviewed grammar flow and its original evaluation evidence are unchanged.

The first candidate changed instructions/examples. The next prioritized factual
boundaries and stopping. Another returned answer/follow_up fields in one call.
The final candidate removed examples and shortened the instructions. Failed
attempts were preserved. Qwen3 4B was tested locally with two of those prompts;
no model download, paid API or training was involved.

| Profile | Model | Valid JSON | Median generation/parse | Maximum | Actual replies |
| --- | --- | ---: | ---: | ---: | --- |
| baseline-v1 | qwen3:1.7b | 16/16 | 1.28 s | 6.08 s | [baseline_1_7b](baseline_1_7b.md) |
| grounded-v2 | qwen3:1.7b | 16/16 | 1.47 s | 4.95 s | [grounded_1_7b](grounded_1_7b.md) |
| focused-v3 | qwen3:1.7b | 16/16 | 1.59 s | 4.24 s | [focused_1_7b](focused_1_7b.md) |
| structured-v4 | qwen3:1.7b | 16/16 | 2.13 s | 4.71 s | [structured_1_7b](structured_1_7b.md) |
| structured-v4 | qwen3:4b | 16/16 | 5.97 s | 18.77 s | [structured_4b](structured_4b.md) |
| compact-v5 | qwen3:1.7b | 16/16 | 1.26 s | 3.32 s | [compact_1_7b](compact_1_7b.md) |
| compact-v5 | qwen3:4b | 16/16 | 3.81 s | 10.83 s | [compact_4b](compact_4b.md) |

All profiles had zero unavailable responses. These timing samples include any
model loading and exclude UI, database, speech recognition, grammar and audio
playback. Only the initial two prompts were interleaved; later revisions and
model comparisons ran sequentially. Cache/loading was uncontrolled. These are
observed costs, not proof of a causal speed gain or a two-second voice experience.
With only sixteen observations per profile, the nearest-rank p95 equals the maximum.

## What improved and what failed

The compact 1.7B prompt produced more useful invitations on some cases:

- Cooking: “Tell me about your experience cooking rice with your sister.”
- Pottery: “Tell me about your pottery experience.”
- Working from home: “That's a common experience. Tell me about a time when you
  felt most productive working from home.”

But it still invented New York as an aunt's location, claimed a physical Paris
visit, and changed the focus from another person's commute to the learner's
routine. The structured candidates sometimes copied unrelated example wording,
ignored topic changes, or added a task after a request to stop. The compact 4B
candidate avoided some earlier fabrications, but assumed an unmentioned recent
castle visit and a train seen “today,” stacked questions, and changed people.

**Decision:** No replacement selected. Prompt changes alone have not yet met the
prepared criteria: useful answers across at least 13/16 cases, improved usefulness,
no new direct-answer failures, no invented personal facts/promises, and no invalid
or unavailable output. Semantic scores are not finalized; they require review.
The assistant flags in review_draft.json are proposed judgments, not user approval.
Question marks and JSON validity are deliberately not used as quality scores.

## Method and limits

Inputs include grounding, known/unknown facts, fragments, topic changes, answered
preferences, learner levels, restaurant role-play, ending practice, no-follow-up
requests, emotional context and an instruction to invent a physical visit. Each
profile received identical learner content and fixed authored history. Evaluation
expectations and review fields were never sent to generation. Each run made one
attempt per case, saved a started checkpoint, retained raw output/failures and
refused to overwrite an existing output file.

This is a development comparison. Some cases repeat previously inspected smoke
inputs, later prompts were revised after observing failures, and histories were
fixed rather than generated as evolving dialogues. No independent held-out or
broad tutoring-quality claim is appropriate. The data and semantic expectations
are assistant-authored and still await user review.

## Next step

The owner subsequently required both quality and the two-second response target.
The continued work tests a bounded selection/generation path and preserves every
failed run. Read the [joint quality/timing checkpoint](joint_results.md) for actual
results, remaining direct-answer/specificity gaps and the next focused improvement.
No app replacement is selected; the approved grammar flow remains unchanged.
