# Corrected-sentence experiment — measured results

Step 2 replacement-span experiment is implemented. Step 3 has mechanical measurements and a failed selection gate; useful-feedback grading remains pending. This is not an app change.

| Measurement | Archived Qwen baseline | Sentence-diff candidate |
|---|---:|---:|
| Correct inputs left unchanged | 30/30 | 29/30 |
| Erroneous sentences corrected / matching approved reference | 20/30 human-confirmed | 29/30 exact matches |
| Rejected/error responses | 4/60 | 0/60 |
| Useful correction plus explanation | 17/30 human-confirmed | Pending review |
| Median standalone request | 2.752 s | 4.324 s |
| p95 standalone request | 7.324 s | 7.457 s |
| Maximum standalone request | 12.622 s | 15.639 s |

The baseline is archived, not a concurrent randomized speed control. Seed and host load were not controlled; request timing does not measure full voice latency. All five earlier wrong-span cases (10, 45, 47, 53, 59) now produce the approved reference sentence, but some explanations still fail. That is promising mechanical evidence, not approved useful-feedback coverage.

## Selection decision

Not selected. The frozen protocol requires all 30 acceptable inputs unchanged; row 58 violates that requirement. Do not change the criterion after seeing the result. No additional full evaluation repeat is needed to establish that this run fails selection.

- Row 57: “Please give the key to I.” became “Please give me the key to I.” The target error remains.
- Row 58: already-correct “Please give the key to me.” became “Please give me the key.” The rewrite is valid English but unnecessary, and the explanation falsely says the original is incorrect.
- Row 6: the sentence became correct, but the model called an a definite article and described an adjective phrase.
- Rows 20, 41 and 43: the replacements are correct but their explanations misidentify the verb rule.

## Focused human review

The complete side-by-side output is in comparison.md. The following explanations/edits deserve attention before choosing another change. These are assistant observations, not user-approved ratings.

| Row | Actual candidate sentence | Actual explanation | Review observation |
|---:|---|---|---|
| 4 | I would like two sandwiches, please. | Add an 's' to 'sandwich' to make it plural, and add a comma before the conjunction 'please' for proper punctuation. | Correct sentence, but explanation says add s rather than es, calls please a conjunction, and claims a comma change even though the comma was already present. |
| 6 | I am an engineer. | Add the definite article 'an' before the noun 'engineer' to form a correct adjective phrase. | Correct article insertion; explanation incorrectly calls an definite and the phrase adjectival. |
| 16 | I am interested in photography. | Use 'in' with the preposition for interests. | Correct preposition; explanation remains vague, similar to the previously accepted borderline baseline case. New output still needs its own judgment. |
| 20 | I did not order dessert. | Use past tense 'ordered' instead of past participle 'ordered' (incorrectly used as past tense). | Correct base-form replacement, but explanation contradictorily recommends ordered and confuses past tense with past participle. |
| 25 | He is a chef. | Use article 'a' before the singular noun 'chef'. | Correct article; explanation mentions singular noun but omits the consonant-sound distinction that chooses a over an. |
| 33 | I packed four shirts. | Plural form of shirt is shirts. | Correct plural; explanation only identifies the form, without linking it to four. Adequacy needs review. |
| 35 | We need three boxes. | Use plural noun 'boxes' for countable object 'box'. | Correct plural; explanation mentions countability without linking plural to three. Adequacy needs review. |
| 41 | Does she like tea? | Use like with the third person singular subject she. | Correct replacement, but explanation appeals to she rather than the base form after does. |
| 43 | He did not write the note. | Use write instead of wrote for the simple past tense. | Correct replacement, but write is not the simple-past form; the relevant rule is the base form after did. |
| 45 | This route is shorter. | Remove the unnecessary adjective 'more' as 'shorter' already implies comparison. | Correct comparative correction, but more modifies the adjective here; calling it an adjective is inaccurate terminology. |
| 51 | They depend on public transport. | Use 'on' instead of 'of' with the preposition for public transport. | Correct preposition; explanation refers to public transport rather than the construction depend on. |
| 57 | Please give me the key to I. | Add 'me' to indicate the indirect object of the verb 'give'. | Incorrect full sentence: adds me but retains to I. Exact offset reconstruction cannot establish semantic accuracy. |
| 58 | Please give me the key. | The word order in the phrase 'give the key to me' is incorrect. In English, the indirect object (me) should come after the direct object (the key) when using 'give'. The correct structure is 'give me the key'. | Unnecessary rewrite of approved correct English; explanation falsely calls the original word order incorrect and contradicts its own proposed ordering. This fails the frozen unchanged-correct-input criterion. |
| 59 | This is her coat. | Use her instead of hers for the possessive pronoun. | Correct replacement; explanation does not state that her precedes the noun and hers stands alone. Terminology and adequacy need review. |

## Verification and next steps

191 automated tests passed (including 30 new sentence-correction tests). Ruff and uv lock checks passed. All 60 actual calls completed without rejection or service errors. Exact-offset edits reconstructed each accepted corrected text. No held-out input was sent, no app prompt was replaced, and no Git history action was performed.

Next, review the focused failures and choose one further development-only change. Explanation templates may improve rule accuracy but cannot by themselves prevent unnecessary rewrites or missed errors. Keep these concerns and their measurements separate. Do not claim a useful-feedback score from reference matching.
