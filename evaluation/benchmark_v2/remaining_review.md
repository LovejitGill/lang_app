# Development review — completed

**Completed:** Sections A, B and C are approved. See [final_scorecard.md](final_scorecard.md). The original grouped review below is retained as history.

Update 2026-09-30: sections A (60 correctly unchanged responses) and B (28 useful corrections) are approved, bringing the total to 110/120. Only section C (six misses and four incorrect edits) remains pending. Row 16 Qwen remains an approved borderline pass.

| Category | Count | Proposed decision |
|---|---:|---|
| correct_abstention | 60 | Pass |
| useful | 28 | Pass |
| missed | 6 | Fail |
| incorrect_edit | 4 | Fail |

## Correctly unchanged inputs — 60 responses

Both engines returned no edits for these 30 approved correct inputs. Proposed decision: accept all as correctly unchanged.

1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 22, 24, 26, 28, 30, 32, 34, 36, 38, 40, 42, 44, 46, 48, 50, 52, 54, 56, 58, 60

## Remaining error-containing inputs — 38 responses

These preserve the actual output. Reasons are proposed assessments, not rewritten model explanations.

| Row | Engine | Input | Actual edit and explanation | Proposed decision |
|---:|---|---|---|---|
| 2 | languagetool | She walk to work every morning. | walk → walks: The pronoun ‘She’ is usually used with a third-person or a past tense verb. | Pass |
| 2 | qwen | She walk to work every morning. | walk → walks: Subject 'She' requires third person singular verb form. | Pass |
| 4 | qwen | I would like two sandwich, please. | sandwich → sandwiches: Plural form needed for 'two'. | Pass |
| 8 | languagetool | We visited the museum yesterday and buy a postcard. | No correction returned. | Fail — missed |
| 10 | qwen | This restaurant is more cheaper than the cafe. | is → cheaper: The phrase 'more cheaper' is incorrect; 'cheaper' is already comparative form, so use 'cheaper' directly without 'more'. | Fail — incorrect_edit |
| 12 | languagetool | I have lived here since five years. | since → for: Did you mean “for”? (‘since’ refers to a point in time, whereas ‘for’ refers to a period) | Pass |
| 12 | qwen | I have lived here since five years. | since → for: Use 'for' with a duration of time, not 'since'. | Pass |
| 14 | languagetool | He can speaks Spanish. | speaks → speak: The modal verb ‘can’ requires the verb’s base form. | Pass |
| 14 | qwen | He can speaks Spanish. | speaks → speak: The verb 'speak' is used in the base form after 'can' for ability. | Pass |
| 16 | languagetool | I am interested on photography. | No correction returned. | Fail — missed |
| 20 | languagetool | I did not ordered dessert. | ordered → order: The auxiliary verb ‘do’ requires the base form of the verb. | Pass |
| 21 | languagetool | My aunt drive a bus. | No correction returned. | Fail — missed |
| 21 | qwen | My aunt drive a bus. | drive → drives: Use third person singular verb form for the subject aunt. | Pass |
| 23 | qwen | The students needs more time. | needs → need: The plural subject 'students' requires the plural verb form 'need'. | Pass |
| 25 | languagetool | He is an chef. | an → a: Use “a” instead of ‘an’ if the following word doesn’t start with a vowel sound, e.g. ‘a sentence’, ‘a university’. | Pass |
| 27 | languagetool | We saw a elephant. | a → an: Use “an” instead of ‘a’ if the following word starts with a vowel sound, e.g. ‘an article’, ‘an hour’. | Pass |
| 27 | qwen | We saw a elephant. | a → an: Use 'an' before words starting with a vowel sound. | Pass |
| 29 | languagetool | Last night I watch a film. | No correction returned. | Fail — missed |
| 29 | qwen | Last night I watch a film. | watch → watched: The past tense of watch is watched, and the sentence describes a completed action in the past. | Pass |
| 31 | languagetool | Yesterday she bring her lunch. | bring → brings: The pronoun ‘she’ is usually used with a third-person or a past tense verb. | Fail — incorrect_edit |
| 31 | qwen | Yesterday she bring her lunch. | bring → brought: The past tense of 'bring' is 'brought' for a completed action in the past. | Pass |
| 33 | qwen | I packed four shirt. | shirt → shirts: Plural form needed for countable noun 'shirt' when referring to multiple items. | Pass |
| 35 | languagetool | We need three box. | No correction returned. | Fail — missed |
| 37 | languagetool | You should takes a break. | takes → take: The modal verb ‘should’ requires the verb’s base form. | Pass |
| 37 | qwen | You should takes a break. | takes → take: Use base verb form after 'should'. | Pass |
| 41 | languagetool | Does she likes tea? | likes → like: Did you mean “like”? As ‘do’ is already inflected, the verb cannot also be inflected. | Pass |
| 43 | languagetool | He did not wrote the note. | wrote → write: After the auxiliary verb ‘do’, use the base form of a verb. Did you mean “write”? | Pass |
| 43 | qwen | He did not wrote the note. | wrote → write: Use base verb form after did not. | Pass |
| 45 | languagetool | This route is more shorter. | more shorter → shorter: Use only “shorter” (without ‘more’) when you use the comparative. | Pass |
| 47 | languagetool | Today is more colder than Monday. | more colder → colder: Use only “colder” (without ‘more’) when you use the comparative. | Pass |
| 47 | qwen | Today is more colder than Monday. | is → cold: The phrase 'more colder' is incorrect; 'colder' is already comparative form, so 'more' is redundant. Use 'cold' for the base form to compare temperatures. | Fail — incorrect_edit |
| 49 | languagetool | She has worked here since two months. | since → for: Did you mean “for”? (‘since’ refers to a point in time, whereas ‘for’ refers to a period) | Pass |
| 49 | qwen | She has worked here since two months. | since → for: Use 'for' with durations of time like 'two months'. | Pass |
| 51 | languagetool | They depend of public transport. | depend of → depend on: The verb ‘to depend’ requires the preposition ‘(up)on’. | Pass |
| 53 | languagetool | I enjoy to swim. | enjoy to swim → enjoy swimming: The verb ‘enjoy’ is used with the gerund form. | Pass |
| 57 | languagetool | Please give the key to I. | to I → to me: The object form of the pronoun may be required here. Did you mean “to me”, “to her”, “to him”, “to us”, or “to them”? | Pass |
| 59 | languagetool | This is hers coat. | No correction returned. | Fail — missed |
| 59 | qwen | This is hers coat. | is → her: The possessive pronoun 'her' should be used here to indicate ownership. | Fail — incorrect_edit |

## Next steps

Approve these remaining proposed judgments or specify row/engine changes. Then finalize a separate human-reviewed report and score sheet with provenance, keeping model outputs immutable. Use the confirmed errors to choose a development-only improvement; do not expose held-out outputs for candidate selection.
