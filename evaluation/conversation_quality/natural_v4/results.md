# Natural conversation revision — results and decision

Implemented the owner’s October 6 feedback in an experimental candidate. **No candidate is selected for app integration:** several conversation failures remain. Both natural conversation and the two-second goal remain required.

## Measured results

All runs below reused the same 41 inspected development cases. Four runs are 164 attempts, not 164 independent examples or a controlled held-out quality comparison. Tests were idle during each inference run. Human usefulness scores remain unassigned.

| Revision | Generated | Authored fallback | Authored deterministic | Maximum complete text | Readiness |
| --- | ---: | ---: | ---: | ---: | ---: |
| natural_v1 | 13 | 5 | 23 | 0.973 s | 4.942 s |
| natural_v2 | 10 | 7 | 24 | 1.012 s | 0.489 s |
| natural_v3 | 9 | 8 | 24 | 0.937 s | 0.455 s |
| natural_v4 | 9 | 8 | 24 | 0.939 s | 0.439 s |

In the latest run, **41/41 complete text responses were under two seconds**, with a maximum of **0.939 s** and nearest-rank p95 of **0.824 s**. Both requested edits (D02 and D12) were offered before the reply, with approximately 0.035 s and 0.034 s checker time. No checker was unavailable. The other 39 rows had no supported fast offer; this is not a claim that those sentences are error-free.

The all-path median of 0.038 s is dominated by authored deterministic responses. Only **9/41 replies were model-generated**; 24 were authored deterministic responses and eight were authored fallbacks. This is a hybrid experiment, not evidence that Qwen3 now generates all the improved wording.

Timing starts with confirmed text in memory and ends with assembled correction-first text. It includes concurrent local conversation/checker work. It excludes model/checker readiness, database/UI work, speech recognition, end-of-turn detection, spoken playback, and the reviewed full grammar pass. **Phone-like two-second spoken interaction is not demonstrated.** Readiness was measured separately; none of these four runs is a fully cold-system benchmark.

## Changes and preserved evidence

- Removed repetitive example/detail endings and allowed short, natural questions.
- Added reusable topic patterns for cooked food, meal preferences, commutes, missed transport, departures, walks, interests and relative-location questions. These are narrow patterns, not general language understanding.
- Unknown relative facts mention the relative and relation. A newer job-change statement prevents reuse of a stale workplace.
- C15 remains habitual present. A completed past walk permits “How did your walk feel?”; “Yesterday I take…” is erroneous but outside the fast adapter’s current rule coverage.
- Kept conversation generation and grammar detection separate and concurrent. The fast adapter allows only supported DID_PAST and HE_VERB_AGR edits; it checks exact offsets, conflicts, context and simple tense/subject conditions.
- v1 still delivered a weak yes/no rice question. v2 rejected that and improved continuation/hobby/habit handling. v3 required the dish noun so soup would not become a general vegetables question. v4 added malformed-response handling and a post-validation elapsed-time check.
- Original contextual results and draft judgments are unchanged. The owner review is partial: nine named cases plus the C09 example, not approval of the remaining 22.
- Every attempt retains raw generated text, delivered text, path, rejection reason, checker provenance, model identity and prepared source/data hashes. Earlier attempts are not overwritten.

## Remaining failures and scope

- C10/C13 still fail to answer direct tutoring/clarification questions.
- N01/N06 repeat supplied information; D01 assumes an unstated bag. D15 presumes finishing despite the learner saying they could not finish. D04/C05 retain generic recall follow-ups.
- Topic-word checks cannot establish factual grounding or naturalness. A question can mention rice while inventing Paris and still pass this type of filter.
- Only two grammar rules have fast coverage. D01 plural bottles and N05 past-tense took remain uncovered here; the unchanged full grammar pipeline is separate.
- The 1.4 s conversation and 0.2 s checker deadlines are best-effort. A custom conversation budget below 0.2 s does not cap the checker; synchronous work/scheduling may exceed a timer. Actual elapsed time is always the performance evidence.
- Client cancellation does not prove immediate server-side cancellation. Full grammar CPU contention and a live multi-turn audio workload remain untested.

## Verification and next step

**499 tests passed in 17.22 s**, including 111 new focused conversation/correction tests. Targeted Ruff checks passed. These tests cover observable behavior and failure handling, not semantic tutoring quality. The approved grammar source hashes and grammar-function identity remain verified; no app integration, dependency change or Git history/publishing operation occurred.

Next: review the [actual 41 responses](review.md), prioritizing repeated questions, invented premises, generic recall and unanswered language questions within the same deadline. Preserve the useful topic changes, then test fresh multi-turn conversations before selecting a candidate. After quality passes, measure speech-end to first useful audio under the real grammar workload.

Learn and rerun using [the verification guide](../../../docs/natural_conversation.md). The [partial owner review](../contextual_v2/owner_review_2026_10_06.md) binds the original feedback to its original run.
