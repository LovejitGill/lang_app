# Joint conversation quality and latency checkpoint — 2026-10-05

**Decision: no app replacement selected.** Both requirements remain acceptance targets. The bounded response mechanism keeps the measured text path below two seconds, but useful direct answers and natural, specific follow-ups are not yet established across all paths. Voice latency is unmeasured.

Each condition below contains the same 32 development/challenge inputs, not 32 new learners per row. Sixteen inputs extend the original sixteen prompt-comparison cases. All case expectations and draft observations are assistant-authored; human quality judgments are pending. No held-out claim applies.

| Condition | Generated / selected | Fallback | Deterministic | Maximum text delay | Under 2 s | Setup time* |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| [Authored selection, initial mismatched warm-up](bounded_v1/warm_results_v2.json) | 0/32 | 17/32 | 15/32 | 0.902 s | 32/32 | 2.821 s |
| [Authored selection, matching warm-up](bounded_v1/warm_results_v3.json) | 17/32 | 0/32 | 15/32 | 0.721 s | 32/32 | 0.537 s |
| [Authored selection, cold first request](bounded_v1/cold_results_v3.json) | 0/32 | 17/32 | 15/32 | 0.909 s | 32/32 | 0.003 s |
| [Contextual v1, warm (CPU test overlap)](contextual_v1/warm_results.json) | 10/32 | 9/32 | 13/32 | 1.402 s | 32/32 | 3.888 s |
| [Contextual v2, Qwen3 1.7B, warm](contextual_v2/warm_results.json) | 15/32 | 4/32 | 13/32 | 1.404 s | 32/32 | 1.145 s |
| [Contextual v2, Qwen3 1.7B, cold first request](contextual_v2/cold_results.json) | 0/32 | 19/32 | 13/32 | 1.403 s | 32/32 | 0.003 s |
| [Contextual v2, Qwen2.5 1.5B, warm](qwen25_contextual_v2/warm_results.json) | 2/32 | 17/32 | 13/32 | 1.402 s | 32/32 | 3.368 s |

*Warm setup includes preload and, for corrected runners, a real probe with matching options; it is not necessarily a fresh process/model load. Cold setup measures unloading, not loading. Actual loading then falls inside the deadline-limited request. These are sequential runs with different starting states, not a controlled causal speed estimate.

The interval covers in-memory preparation, HTTP setup/wait/cancellation and assembling a complete text response. It excludes storage, browser rendering, end-of-turn detection, STT and TTS. A 0.9 s selector budget and a 1.4 s contextual-generation budget are soft deadlines; observed overshoot is retained. No hard real-time guarantee is possible from this sample.

## Useful findings

- Matching warm-up matters: a diagnostic after the original preload recorded 2.56 s of loading because the test used a 2048-token context while preload used the default 4096. Corrected warm-up made all 17 actual selector requests complete in 0.491–0.721 s. Fifteen additional cases were handled without inference.
- In the current Qwen3 contextual warm run, 15/32 replies used generated text, 4/32 fell back, and 13/32 used deterministic handling. The longest full text reply took 1.404 s. This is a timing result, not a usefulness score.
- The cold contextual run used 19 fallbacks and 13 deterministic replies; no generated reply completed within the budget. Repeated deadline cancellation did not establish model readiness. A separate readiness phase is necessary; continuously retrying while cold can keep the session on fallback.
- Stop handling and quoted recall remove some opportunities for invented personal facts. They cover narrow explicit forms and the recent four learner turns; they do not prove general understanding or resolve all contradictory history.
- Connection, stalled-request, invalid-output and cancellation behavior is covered by component tests. Live CPU contention with grammar inference, server-side cancellation latency and continuous speech have not been established.

## Quality still blocks selection

[Review all 32 current delivered replies, context and withheld model output](contextual_v2/review.md). These examples are actual outputs:

| Input | Delivered Qwen3 contextual-v2 reply | Observation |
| --- | --- | --- |
| I cooked rice with my sister. | Tell me what you did with your sister. | Relevant people, but loses the cooking detail; naturalness/specificity needs review. |
| Working from home helps me focus, but I miss talking to colleagues. | Tell me about the benefits and difficulties of working from home, with an example. | Relevant invitation; user usefulness judgment pending. |
| What is the difference between lend and borrow? | This guided mode doesn't have an answer to that question. Tell me which part you would like help understanding. | Timeout fallback; fails to answer the question. |
| Can you explain what your last question means? | This guided mode doesn't have an answer to that question. Tell me which part you would like help understanding. | Timeout fallback; fails to clarify the earlier question. |

Earlier contextual-v1 output copied “I miss talking to colleagues” into the tutor's reply. The lexical filter incorrectly accepted it. Its raw result remains preserved; v2 rejects additional sentences and first-person claims. New vocabulary checks also reject some reasonable paraphrases. Neither passing nor failing those checks is a semantic score.

A four-case short-answer diagnostic used a 12–18-word instruction. It omitted the temporary nature of lending/borrowing and changed the learner's perspective to “what brings me joy.” Shortening instructions/output alone did not solve accuracy. The diagnostic is retained in contextual_v2/short_answer_diagnostic.json and is not folded into the frozen main run.

The alternative Qwen2.5 run generated only its two language answers; both have substantive problems:

- Lend/borrow: “Lend gives permission to use something temporarily; borrow needs item back.” The second definition is unclear and does not explain receiving/using something temporarily.
- Clarification: “Sure, I like playing games because it makes me happy.” This answers as the learner instead of explaining the tutor's previous question.

Seventeen other Qwen2.5 attempts fell back due to deadline or validation failures. A zero value for `unsupported_questions` in that run only describes routing; it does not mean those two generated answers are correct. This model is not selected. Its local download is approximately 986 MB; the [Ollama model page](https://ollama.com/library/qwen2.5:1.5b) and [publisher card](https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct) identify the Apache-2.0 model. Its full installed digest is recorded in the protocol.

## Evidence and implementation integrity

- Protocols, settings, model digests and source hashes were recorded before each measured run. Cases, raw responses, withheld output, timing, fallback paths and started checkpoints are retained.
- The first bounded runner failed while aggregating its first result because the shared timing helper required a status field. That response was not saved; the started checkpoint and failure note remain. The repaired runner saves every completed result before aggregation, and a test deliberately crashes aggregation to verify preservation.
- Historical runner/generator snapshots preserve the versions preceding fixes. Existing raw measurements and approved grammar evidence were not rewritten.
- 388 tests passed in 16.91 s after the implementation changes. Source/data identities and the frozen grammar function are verified by the evaluation runners. No dependency lock changes, app-model switch, model training or Git commits/pushes were made.

## Next improvement — same objective

Review the specificity of current invitations, then address direct language questions under the same deadline. A concrete next design is to retain the intent and a plain-language explanation with each authored tutor question, so clarification does not require the model to reinterpret its own wording. For vocabulary answers, investigate a small local reference source with reviewed definitions/examples rather than compressing uncertain model knowledge further. Test coverage and helpfulness on unfamiliar questions, including misses; these are proposals, not implemented or proven solutions.

Do not promote the candidate merely because fallback is fast. Require useful direct answers, preserved facts/people, context-specific invitations and acceptable fallback behavior in fresh multi-turn dialogues. Then integrate and measure speech-end to first useful audio under grammar workload; the existing app still blocks Send while grammar runs. The active improvement remains conversational quality plus latency, with explanation polishing deferred.
