# Explanation review experiment — results

**Decision: do not select this configuration for app integration or held-out validation.** It supported all 31 proposed changes, including both known bad proposals. No extra repeat was run to search for a passing result.

| Measurement | Result |
|---|---:|
| Source cases accounted for | 60 |
| Unchanged cases skipped by second pass | 29 |
| Second-pass calls | 31 |
| Proposed changes supported | 31 |
| Proposed changes withheld | 0 |
| Unavailable/rejected reviews | 0 |
| Approved correct inputs still offered an unnecessary change | 1/30 |
| Erroneous inputs with reference-matching offered correction | 29/30 |
| Median review-call time | 12.500 s |
| p95 review-call time | 15.112 s |
| Maximum review-call time | 23.772 s |

Timing is for the extra review call only. It excludes first-stage generation, STT, UI and TTS. Zero-time skipped cases are excluded from inference latency statistics. Do not claim a measured end-to-end total by summing separate runs.

## Observed failures

- Row 57: approved the still-incorrect “Please give me the key to I.” It failed to notice the remaining pronoun error.
- Row 58: acknowledged that “Please give the key to me.” is grammatically correct, yet supported rewriting it as “Please give me the key.” This directly contradicts the no-style-correction instruction and fails the frozen gate.
- Row 6: again called an a definite article.
- Row 20: still failed to explain the base form after did.
- Row 25: correctly chose a before chef, but incorrectly described chef as beginning with /tʃ/ like cheese; the usual initial sound is /ʃ/.
- Row 37: explained subject agreement instead of the base verb after should.
- Multiple explanations visibly stop mid-sentence. Valid JSON and the length constraint do not establish a complete explanation; the cause of unfinished output was not diagnosed.

New explanations need human review for any full useful-feedback score. We can reject this configuration on the known failed gate without grading every explanation or pretending it improved aggregate accuracy.

## Key actual outputs

| Row | Frozen proposed sentence | Review decision | Actual new explanation |
|---:|---|---|---|
| 6 | I am an engineer. | supported | The original sentence 'I am engineer.' is missing the definite article 'an' before the noun 'engineer' in the context of a job title. In English, job titles typically require an article when used in this way. The proposed change adds 'an' ( |
| 20 | I did not order dessert. | supported | The original uses the past tense verb 'ordered' incorrectly. The correct past tense form of 'order' is 'ordered', but in this context, the verb should be in the simple past tense for the past action. The proposed change replaces 'ordered' ( |
| 25 | He is a chef. | supported | The original uses 'an' before 'chef' which is incorrect because 'chef' starts with a consonant sound /tʃ/ (like 'ch' in 'cheese'), so the article 'a' is required. The change from 'an' to 'a' is grammatically correct for this context. |
| 37 | You should take a break. | supported | The original uses 'takes' which is third person singular form of 'take' (e.g., 'he takes'). But the subject 'you' requires second person singular form 'take'. The verb must agree with the subject pronoun. The change from 'takes' to 'take' ( |
| 57 | Please give me the key to I. | supported | The original 'Please give the key to I.' is grammatically incorrect because 'I' is a pronoun that requires a possessive or object marker. Adding 'me' as the object pronoun (as in 'give me the key') is correct. The edit inserts ' me' at the  |
| 58 | Please give me the key. | supported | The original sentence 'Please give the key to me.' is grammatically correct but less common in English. The proposed change 'Please give me the key.' follows standard word order for indirect objects in English. The change moves 'me' before  |

## Evidence and verification

The source correction report is unchanged and its hash matches the frozen protocol. `development_results.json` retains every attempt and both stages of text, while `comparison.md` shows all 31 before/after explanations. `human_review.json` is an unfilled review worksheet, not approved ratings.

216 tests passed (25 new tests for this experiment); Ruff and uv lock checks passed. No app changes, model training, paid services, new model downloads, held-out inference, commits or pushes occurred.

## Next improvement

Test a small catalogue of reviewed grammar-rule explanations. The catalogue can eliminate invented rule wording, but selection of the correct rule and justification of the edit remain separate problems. Check applicability explicitly and report unsupported coverage; do not silently call unrecognized grammar correct. Keep this as a new development-only experiment with a frozen protocol.
