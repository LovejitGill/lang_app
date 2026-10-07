# Constraint acknowledgment and relevant follow-ups — planned_v3

**The targeted changes are implemented and measured.** This remains an experimental conversation candidate outside the live app. The result supports an experimental GitHub checkpoint, not a stable release or a general tutoring-quality claim.

## Targeted before and after

| Case | Prior reply | Latest actual reply |
| --- | --- | --- |
| D08 | Why do you think it's cheaper than driving? | How does taking the bus fit into your day? |
| C12 | What did you think of the outcome? | This was the result you expected. What does this result mean for you? |
| N07 | What kind of soup do you prefer? | You can't eat dairy. How would you ask about dairy when ordering soup? |
| X04 | What did your son do after catching the ferry? | That sounds like a relief for your son. What subject does your son want to study? |

See [all 63 actual responses](review.md), including their histories, generated versus authored paths, and rejection reasons. The ten Y cases vary people, negation, revisions, time and supplied reasons; their expectations are assistant-authored, inspected during development and not owner-approved references.

## Measured results

- 63/63 complete text replies within two seconds; maximum **1.407 s**, nearest-rank p95 **1.394 s**, median **0.558 s**.
- Paths: **1 generated**, **21 model-selected authored**, **31 authored deterministic**, **10 authored fallbacks**. The two local word-pair answers and five clarification replies are subsets of deterministic responses.
- Three timeouts (D10, Y03, Y04) used recorded fallbacks. The two selector timeouts did not discard the dietary acknowledgment. A 1.4 s configured budget was slightly exceeded by measured end-to-end text assembly/cancellation; it is best-effort, not a hard deadline.
- Both supported fast edits (D02 visited → visit and D12 go → goes) remained first. No fast checker was unavailable. Other absent offers are not clean-grammar judgments.
- Warm-up/readiness was **6.249 s**, separate from the response measurements. Tests were idle during inference.
- **703 tests passed in 18.40 s**, including 58 checks added this iteration. Targeted lint/format and frozen-source checks are recorded in `verification.json`.

Timing starts with confirmed text already in memory and ends with complete assembled text, including the concurrent limited checker. It excludes readiness, database/UI, speech recognition, turn detection, spoken synthesis/playback, and the full grammar workload. Two-second spoken dialogue remains unverified. This run has more cases and selection calls than planned_v2, so it is not a controlled claim of faster inference.

## Implementation and boundaries

`food_constraints.py` attaches explicit food restrictions/preferences to the correct person and applies supported recent revisions. A positive ability and a dislike remain separate. It never infers ingredients, diagnoses an allergy, recommends a medically safe substitute or promises preparation. The authored prefix remains attached even if selection times out.

`contextual_followups.py` asks about an unstated aspect of a journey or result, preserves negated feelings, and uses explicit learner history for upcoming interviews. A completed interview produces a question about the experience or next step. Neither catching transport nor answering every question establishes arrival, admission or success.

Review found five boundaries before freezing: scheduled present-tense travel, another person’s unfinished question, cancelled interviews, another relative’s study subject, and mismatched interview/emotion pronouns. Each received a regression check. Stop/no-follow-up controls precede the new helpers. Exhausted authored choices produce a nonempty acknowledgment instead of unrestricted generation.

## Remaining limits

Patterns cover limited syntax and four recent learner turns, not general semantic understanding. Unsupported food/history clauses can conservatively discard remembered constraints. Topic extraction and exact-repeat checks can still miss more complex references or reasked meanings. When questions are exhausted, a bare acknowledgment may feel abrupt.

The N07/Y01/Y02 ordering-wording prompts read as language exercises; their naturalness needs owner review. D08’s “fit into your day” may need simpler phrasing for a beginner. Y06 asks a yes/no follow-up; that may be natural but does not ensure longer answers. No human semantic pass rate is assigned, and no candidate is promoted into Streamlit.

## Next improvement and GitHub checkpoint

1. Review these actual replies, especially the practice-style food questions, abstract wording and completed/future event flow. Keep generated and authored paths distinct.
2. Continue the same conversation-quality objective with fresh multi-turn dialogues that use actual tutor replies in later history. Test learner corrections, ambiguous references, follow-up clarification and repeated questions under the same two-second text threshold.
3. **GitHub checkpoint: yes, after reviewing the complete accumulated changes.** This is a reproducible experimental snapshot; many earlier dependencies/evidence files are still untracked. Do not stage only the newest two modules.
4. Current experiment: **planned_v3**. The next experiment may be **planned_v4** after this checkpoint/review. That does not change package version 0.1.0 or imply a stable app v3/v4 release. Preserve the existing local mvp-v1 tag. No commit, tag, push or remote-publication verification was performed.

Use the [learning/verification guide](../../../docs/constraint_followups.md) and [GitHub checkpoint steps](../../../docs/github_checkpoints.md).
