# Planned follow-ups and local answers — development results

**Targeted improvement implemented; candidate remains experimental.** The latest observed replies address the earlier bag assumption, completion assumption, repeated plan/feeling questions, generic hobby recall, and the two unanswered tutoring questions. These observations are not a human-approved quality score or proof of general conversation ability.

## Before and after on the targeted cases

| Case | Previous conversational reply | New conversational reply | New path |
| --- | --- | --- | --- |
| D01 | Did you put all the bottles in the bag? | How did you decide what to pack? | model_selected |
| D04 | In our recent conversation, you said: ‘My name is Maya and I enjoy hiking.’ Tell me more about that. | You said: ‘My name is Maya’ ‘I enjoy hiking.’ What do you enjoy most about hiking? | model_selected |
| D15 | What did you do to help you finish it? | I'm sorry you're feeling disappointed. What would help you finish your assignment? | model_selected |
| C05 | In our recent conversation, you said: ‘My name is Zoë and I enjoy weaving.’ Tell me more about that. | You said: ‘My name is Zoë’ ‘I enjoy weaving.’ What do you enjoy most about weaving? | model_selected |
| C10 | This guided mode doesn't have an answer to that question. Tell me which part you would like help understanding. | ‘Lend’ means give someone something for a short time, expecting it back. ‘Borrow’ means use something that belongs to someone else, then return it. Example: I lend you a book; you borrow the book from me. | deterministic |
| C13 | This guided mode doesn't have an answer to that question. Tell me which part you would like help understanding. | What do you enjoy most about playing games? | deterministic |
| N01 | Will you be cooking rice with your sister tomorrow? | What made you choose the rice? | model_selected |
| N05 | Did you feel any fresh air or enjoy the scenery? | What did you notice during your walk? | model_selected |
| N06 | How did she feel about catching the bus? | What did your sister do after catching the bus? | model_selected |

All 53 current inputs, histories and delivered responses appear in [the review](review.md). The 41 earlier cases and 12 new cases were inspected during development; the latter are structural counterexamples, not unseen validation. The X08 preparation note allows a direct comparison answer to finish without a forced follow-up question. No references, case IDs or expected outputs enter the model prompt.

## Timing and provenance

| Run | Cases | Generated prose | Model-selected authored | Authored deterministic | Authored fallback | Max complete text | Readiness |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| planned_v1 | 53 | 4 | 9 | 32 | 8 | 1.041 s | 5.442 s |
| planned_v2 | 53 | 4 | 9 | 32 | 8 | 1.000 s | 1.130 s |

**Latest run: 53/53 complete text responses within two seconds**, maximum 1.000 s, nearest-rank p95 0.901 s. The low median (0.036 s) is dominated by authored local replies. Two local-reference answers and five clarification responses are subsets of the 32 deterministic replies; they are not additional responses. Nine model selections and four generated replies do not mean 13 model-written answers.

The same 53 cases were run twice, producing 106 attempts rather than 106 independent examples. Readiness includes warm-up of the actual generator, selector and resident checker. Tests were idle during inference. Both required fast edits, D02 visited → visit and D12 go → goes, still appeared first; no checker was unavailable. The other rows without offers are not assertions of clean grammar.

Timing includes input preparation, concurrent reply/checker work and assembled complete text. It excludes readiness, SQLite/UI work, speech recognition, turn detection, speech synthesis and the reviewed full grammar workload. **Two-second spoken interaction is still unverified.** Budgets are best-effort and cancellation does not prove immediate server-side shutdown.

## What changed

- The planner extracts limited explicit information and supplies questions about information not already given. Qwen3 chooses an index among authored choices for recognized cases; it cannot add a bag, invent a destination or rewrite an unfinished task as finished on that path.
- Name/hobby recall quotes learner-only clauses from the last four turns, including separate-turn facts and supported retractions. It ignores tutor suggestions, other-person interests and obvious hypothetical/quoted statements.
- A two-entry authored catalog explains lend/borrow and teach/learn. Explicit question-intent mappings simplify selected tutor questions; unavailable or ambiguous context gets a targeted request.
- Other inputs retain the preserved natural-v4 path. The full grammar pipeline, model identities, app behavior, dependencies and earlier evidence remain unchanged.
- Read-only review found an empty-response boundary for expanded no-question wording and stale facts after explicit retractions. v2 supplies a nonempty acknowledgment and invalidates those facts; dedicated tests preserve the fixes. The v1 run and source remain available.

## Limits and next checkpoint

Observed review concerns remain for D08/C12’s generic wording and N07’s missing explicit acknowledgment of the dairy restriction. X04’s follow-up needs a naturalness judgment. Pattern coverage, semantic non-repetition and pronoun resolution remain narrow; an unknown word pair or question form is not made answerable by these two catalog entries. Discarding a repeated exact question does not establish that a paraphrase asks something new. No approved semantic pass rate is assigned.

The new helper is not a general fact store: complex retractions, interests or references may still be missed. Dialogue planning trades unrestricted model prose for bounded authored choices. This is a useful local design experiment, not evidence that prompt changes alone solved model capability or that model training occurred.

Next keep the same conversation-quality/latency focus: review the actual outputs, improve the remaining generic/constraint-sensitive responses, then freeze fresh multi-turn dialogues to test context retention and natural progress before app integration. Finally measure speech-end to first useful audio under real grammar load.

Learning and command verification: [dialogue planning guide](../../../docs/dialogue_planning.md). Full tests and protected-source verification are recorded in `verification.json`. Git commits/pushes remain the owner’s responsibility.
