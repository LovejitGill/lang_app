# Development scorecard — review history

**Review complete:** All 120 judgments are confirmed. See [final_scorecard.md](final_scorecard.md) for authoritative scores and next steps. The draft-era wording below records the review process; its pending statuses are superseded.

The nine flagged groups (14 engine responses) were approved by the project owner on 2026-09-30. Eight additional failures were reconciled from earlier explicit user feedback. Sections A and B were subsequently approved (110/120 confirmed in total). The ten section C failure judgments remain pending; overall scores remain provisional. Your nine targeted findings are preserved separately. Seeing engine names means this review is not blinded. The historical report and response worksheet have not been changed.

All 60 reference labels are approved. This draft reconciles those labels with the saved run after checking that all sentences, reference corrections, expected rules and error counts are unchanged.

## Approved grading rule

A useful response must correct the target error, avoid unnecessary edits, preserve meaning, and explain the applicable rule. Merely suggesting a replacement does not supply the rule. The project owner approved this explanation-adequacy threshold on 2026-09-30. Individual response ratings remain assistant proposals.

| Engine | Correct inputs left alone | Errors with a correct edit | Fully useful feedback | Rejected |
|---|---:|---:|---:|---:|
| languagetool | 30/30 | 21/30 | 15/30 | 0 |
| qwen | 30/30 | 20/30 | 17/30 | 4 |

A correct edit may coexist with an unnecessary edit or an inadequate explanation; therefore the two correction columns differ. These are development results, not a passed held-out benchmark. No-correction responses on erroneous inputs and all rejected responses remain misses.

## Flagged judgments — approved 2026-09-30

| Rows / engine | Approved judgment |
|---|---|
| 4, 33 / LanguageTool | Correct plural edits, but mentioning countability alone does not explain why plural is required. |
| 18, 23 / LanguageTool | Correct edits, but the explanation does not state the relevant agreement rule. |
| 39 / both | Correct edit; explanation should refer to the base form after might. |
| 20 / Qwen | Correct edit; explanation wrongly directs a past-tense verb rather than the base form after did. |
| 41 / Qwen | Correct edit; contradictory, unfinished explanation fails. |
| 16 / Qwen | Borderline pass: user says it is barely a pass. Credit retained; improve the explanation of interested in. |
| 51 / Qwen | Pass accepted despite awkward wording about the preposition. |
| 8, 35 / Qwen | Count original explanations as accurate; keep your wording improvements as editorial preferences. |
| 10 / LanguageTool | Correct comparative edit plus unnecessary cafe -> café; whole feedback fails strict usefulness. |
| 53 / Qwen | Wrong edit span; intended correction is to swim -> swimming. This interpretation matches the already-approved reference. |

## Complete proposed response review

The table covers all 120 responses. Flagged outcomes above are approved; remaining outcomes are assistant proposals. The JSON records approval per response; unmentioned outputs have not been approved on your behalf.

| Row | Engine | Learner input | Proposed outcome | Explanation assessment | Rationale |
|---:|---|---|---|---|---|
| 1 | languagetool | I live near the station. | correct_abstention | not_applicable | No correction is needed; no unnecessary edit was proposed. |
| 1 | qwen | I live near the station. | correct_abstention | not_applicable | No correction is needed; no unnecessary edit was proposed. |
| 2 | languagetool | She walk to work every morning. | useful | adequate | The edit fixes the approved target error and the explanation conveys the applicable rule. |
| 2 | qwen | She walk to work every morning. | useful | adequate | The edit fixes the approved target error and the explanation conveys the applicable rule. |
| 3 | languagetool | Could we have separate bills, please? | correct_abstention | not_applicable | No correction is needed; no unnecessary edit was proposed. |
| 3 | qwen | Could we have separate bills, please? | correct_abstention | not_applicable | No correction is needed; no unnecessary edit was proposed. |
| 4 | languagetool | I would like two sandwich, please. | correct_edit_explanation_fails | insufficient | Countability is mentioned, but the explanation does not state that two requires a plural noun. |
| 4 | qwen | I would like two sandwich, please. | useful | adequate | The edit fixes the approved target error and the explanation conveys the applicable rule. |
| 5 | languagetool | My sister and I cycle to work. | correct_abstention | not_applicable | No correction is needed; no unnecessary edit was proposed. |
| 5 | qwen | My sister and I cycle to work. | correct_abstention | not_applicable | No correction is needed; no unnecessary edit was proposed. |
| 6 | languagetool | I am engineer. | missed | missing | No correction was offered for the approved target error. |
| 6 | qwen | I am engineer. | missed | missing | No correction was offered for the approved target error. |
| 7 | languagetool | I have been a teacher for six years. | correct_abstention | not_applicable | No correction is needed; no unnecessary edit was proposed. |
| 7 | qwen | I have been a teacher for six years. | correct_abstention | not_applicable | No correction is needed; no unnecessary edit was proposed. |
| 8 | languagetool | We visited the museum yesterday and buy a postcard. | missed | missing | No correction was offered for the approved target error. |
| 8 | qwen | We visited the museum yesterday and buy a postcard. | useful | adequate | The edit fixes the approved target error and the explanation conveys the applicable rule. User-requested clearer wording is recorded separately; the original is not factually incorrect. |
| 9 | languagetool | There is some rice left. | correct_abstention | not_applicable | No correction is needed; no unnecessary edit was proposed. |
| 9 | qwen | There is some rice left. | correct_abstention | not_applicable | No correction is needed; no unnecessary edit was proposed. |
| 10 | languagetool | This restaurant is more cheaper than the cafe. | correct_edit_plus_unnecessary_edit | mixed | Comparative correction is right, but cafe -> café is an unnecessary orthographic preference for this grammar-only task. |
| 10 | qwen | This restaurant is more cheaper than the cafe. | incorrect_edit | rule_correct_but_edit_wrong | Assistant checked the full resulting sentence: this proposal fails the target correction; the difference is not merely an alternative valid reference. The explanation identifies the rule, but the selected edit span is wrong. |
| 11 | languagetool | I would rather stay home tonight. | correct_abstention | not_applicable | No correction is needed; no unnecessary edit was proposed. |
| 11 | qwen | I would rather stay home tonight. | correct_abstention | not_applicable | No correction is needed; no unnecessary edit was proposed. |
| 12 | languagetool | I have lived here since five years. | useful | adequate | The edit fixes the approved target error and the explanation conveys the applicable rule. |
| 12 | qwen | I have lived here since five years. | useful | adequate | The edit fixes the approved target error and the explanation conveys the applicable rule. |
| 13 | languagetool | I look forward to meeting you. | correct_abstention | not_applicable | No correction is needed; no unnecessary edit was proposed. |
| 13 | qwen | I look forward to meeting you. | correct_abstention | not_applicable | No correction is needed; no unnecessary edit was proposed. |
| 14 | languagetool | He can speaks Spanish. | useful | adequate | The edit fixes the approved target error and the explanation conveys the applicable rule. |
| 14 | qwen | He can speaks Spanish. | useful | adequate | The edit fixes the approved target error and the explanation conveys the applicable rule. |
| 15 | languagetool | Neither option appeals to me. | correct_abstention | not_applicable | No correction is needed; no unnecessary edit was proposed. |
| 15 | qwen | Neither option appeals to me. | correct_abstention | not_applicable | No correction is needed; no unnecessary edit was proposed. |
| 16 | languagetool | I am interested on photography. | missed | missing | No correction was offered for the approved target error. |
| 16 | qwen | I am interested on photography. | useful | adequate | The edit fixes the approved target error and the explanation conveys the applicable rule. The wording is awkward/context-bound; adequacy is a judgment for human confirmation. |
| 17 | languagetool | The soup tastes delicious. | correct_abstention | not_applicable | No correction is needed; no unnecessary edit was proposed. |
| 17 | qwen | The soup tastes delicious. | correct_abstention | not_applicable | No correction is needed; no unnecessary edit was proposed. |
| 18 | languagetool | There are a bowl on the table. | correct_edit_explanation_fails | insufficient | Names agreement but does not explain that a bowl is singular. |
| 18 | qwen | There are a bowl on the table. | rejected | unusable | The entire no-op response was rejected. Count the target error as missed, not as clean input. |
| 19 | languagetool | I used to play chess after school. | correct_abstention | not_applicable | No correction is needed; no unnecessary edit was proposed. |
| 19 | qwen | I used to play chess after school. | correct_abstention | not_applicable | No correction is needed; no unnecessary edit was proposed. |
| 20 | languagetool | I did not ordered dessert. | useful | adequate | The edit fixes the approved target error and the explanation conveys the applicable rule. |
| 20 | qwen | I did not ordered dessert. | correct_edit_explanation_fails | incorrect | The edit requires a base-form main verb after did, not a past-tense main verb. |
| 21 | languagetool | My aunt drive a bus. | missed | missing | No correction was offered for the approved target error. |
| 21 | qwen | My aunt drive a bus. | useful | adequate | The edit fixes the approved target error and the explanation conveys the applicable rule. |
| 22 | languagetool | My aunt drives a bus. | correct_abstention | not_applicable | No correction is needed; no unnecessary edit was proposed. |
| 22 | qwen | My aunt drives a bus. | correct_abstention | not_applicable | No correction is needed; no unnecessary edit was proposed. |
| 23 | languagetool | The students needs more time. | correct_edit_explanation_fails | insufficient | Suggests need without providing a grammar rule. |
| 23 | qwen | The students needs more time. | useful | adequate | The edit fixes the approved target error and the explanation conveys the applicable rule. |
| 24 | languagetool | The students need more time. | correct_abstention | not_applicable | No correction is needed; no unnecessary edit was proposed. |
| 24 | qwen | The students need more time. | correct_abstention | not_applicable | No correction is needed; no unnecessary edit was proposed. |
| 25 | languagetool | He is an chef. | useful | adequate | The edit fixes the approved target error and the explanation conveys the applicable rule. |
| 25 | qwen | He is an chef. | rejected | unusable | The entire no-op response was rejected. Count the target error as missed, not as clean input. |
| 26 | languagetool | He is a chef. | correct_abstention | not_applicable | No correction is needed; no unnecessary edit was proposed. |
| 26 | qwen | He is a chef. | correct_abstention | not_applicable | No correction is needed; no unnecessary edit was proposed. |
| 27 | languagetool | We saw a elephant. | useful | adequate | The edit fixes the approved target error and the explanation conveys the applicable rule. |
| 27 | qwen | We saw a elephant. | useful | adequate | The edit fixes the approved target error and the explanation conveys the applicable rule. |
| 28 | languagetool | We saw an elephant. | correct_abstention | not_applicable | No correction is needed; no unnecessary edit was proposed. |
| 28 | qwen | We saw an elephant. | correct_abstention | not_applicable | No correction is needed; no unnecessary edit was proposed. |
| 29 | languagetool | Last night I watch a film. | missed | missing | No correction was offered for the approved target error. |
| 29 | qwen | Last night I watch a film. | useful | adequate | The edit fixes the approved target error and the explanation conveys the applicable rule. |
| 30 | languagetool | Last night I watched a film. | correct_abstention | not_applicable | No correction is needed; no unnecessary edit was proposed. |
| 30 | qwen | Last night I watched a film. | correct_abstention | not_applicable | No correction is needed; no unnecessary edit was proposed. |
| 31 | languagetool | Yesterday she bring her lunch. | incorrect_edit | incorrect | Assistant checked the full resulting sentence: this proposal fails the target correction; the difference is not merely an alternative valid reference. |
| 31 | qwen | Yesterday she bring her lunch. | useful | adequate | The edit fixes the approved target error and the explanation conveys the applicable rule. |
| 32 | languagetool | Yesterday she brought her lunch. | correct_abstention | not_applicable | No correction is needed; no unnecessary edit was proposed. |
| 32 | qwen | Yesterday she brought her lunch. | correct_abstention | not_applicable | No correction is needed; no unnecessary edit was proposed. |
| 33 | languagetool | I packed four shirt. | correct_edit_explanation_fails | insufficient | Countability is mentioned, but the explanation does not state that four requires a plural noun. |
| 33 | qwen | I packed four shirt. | useful | adequate | The edit fixes the approved target error and the explanation conveys the applicable rule. |
| 34 | languagetool | I packed four shirts. | correct_abstention | not_applicable | No correction is needed; no unnecessary edit was proposed. |
| 34 | qwen | I packed four shirts. | correct_abstention | not_applicable | No correction is needed; no unnecessary edit was proposed. |
| 35 | languagetool | We need three box. | missed | missing | No correction was offered for the approved target error. |
| 35 | qwen | We need three box. | useful | adequate | The edit fixes the approved target error and the explanation conveys the applicable rule. User-requested clearer wording is recorded separately; the original is not factually incorrect. |
| 36 | languagetool | We need three boxes. | correct_abstention | not_applicable | No correction is needed; no unnecessary edit was proposed. |
| 36 | qwen | We need three boxes. | correct_abstention | not_applicable | No correction is needed; no unnecessary edit was proposed. |
| 37 | languagetool | You should takes a break. | useful | adequate | The edit fixes the approved target error and the explanation conveys the applicable rule. |
| 37 | qwen | You should takes a break. | useful | adequate | The edit fixes the approved target error and the explanation conveys the applicable rule. |
| 38 | languagetool | You should take a break. | correct_abstention | not_applicable | No correction is needed; no unnecessary edit was proposed. |
| 38 | qwen | You should take a break. | correct_abstention | not_applicable | No correction is needed; no unnecessary edit was proposed. |
| 39 | languagetool | They might arrives early. | correct_edit_explanation_fails | incorrect | The applicable rule is the base verb after might; they is itself a third-person plural pronoun. |
| 39 | qwen | They might arrives early. | correct_edit_explanation_fails | incorrect | Arrive follows modal might; the explanation incorrectly describes a present-simple agreement rule. |
| 40 | languagetool | They might arrive early. | correct_abstention | not_applicable | No correction is needed; no unnecessary edit was proposed. |
| 40 | qwen | They might arrive early. | correct_abstention | not_applicable | No correction is needed; no unnecessary edit was proposed. |
| 41 | languagetool | Does she likes tea? | useful | adequate | The edit fixes the approved target error and the explanation conveys the applicable rule. |
| 41 | qwen | Does she likes tea? | correct_edit_explanation_fails | incorrect | Contradictory and unfinished explanation, despite a correct replacement. |
| 42 | languagetool | Does she like tea? | correct_abstention | not_applicable | No correction is needed; no unnecessary edit was proposed. |
| 42 | qwen | Does she like tea? | correct_abstention | not_applicable | No correction is needed; no unnecessary edit was proposed. |
| 43 | languagetool | He did not wrote the note. | useful | adequate | The edit fixes the approved target error and the explanation conveys the applicable rule. |
| 43 | qwen | He did not wrote the note. | useful | adequate | The edit fixes the approved target error and the explanation conveys the applicable rule. |
| 44 | languagetool | He did not write the note. | correct_abstention | not_applicable | No correction is needed; no unnecessary edit was proposed. |
| 44 | qwen | He did not write the note. | correct_abstention | not_applicable | No correction is needed; no unnecessary edit was proposed. |
| 45 | languagetool | This route is more shorter. | useful | adequate | The edit fixes the approved target error and the explanation conveys the applicable rule. |
| 45 | qwen | This route is more shorter. | incorrect_edit | incorrect | Assistant checked the full resulting sentence: this proposal fails the target correction; the difference is not merely an alternative valid reference. |
| 46 | languagetool | This route is shorter. | correct_abstention | not_applicable | No correction is needed; no unnecessary edit was proposed. |
| 46 | qwen | This route is shorter. | correct_abstention | not_applicable | No correction is needed; no unnecessary edit was proposed. |
| 47 | languagetool | Today is more colder than Monday. | useful | adequate | The edit fixes the approved target error and the explanation conveys the applicable rule. |
| 47 | qwen | Today is more colder than Monday. | incorrect_edit | incorrect | Assistant checked the full resulting sentence: this proposal fails the target correction; the difference is not merely an alternative valid reference. |
| 48 | languagetool | Today is colder than Monday. | correct_abstention | not_applicable | No correction is needed; no unnecessary edit was proposed. |
| 48 | qwen | Today is colder than Monday. | correct_abstention | not_applicable | No correction is needed; no unnecessary edit was proposed. |
| 49 | languagetool | She has worked here since two months. | useful | adequate | The edit fixes the approved target error and the explanation conveys the applicable rule. |
| 49 | qwen | She has worked here since two months. | useful | adequate | The edit fixes the approved target error and the explanation conveys the applicable rule. |
| 50 | languagetool | She has worked here for two months. | correct_abstention | not_applicable | No correction is needed; no unnecessary edit was proposed. |
| 50 | qwen | She has worked here for two months. | correct_abstention | not_applicable | No correction is needed; no unnecessary edit was proposed. |
| 51 | languagetool | They depend of public transport. | useful | adequate | The edit fixes the approved target error and the explanation conveys the applicable rule. |
| 51 | qwen | They depend of public transport. | useful | adequate | The edit fixes the approved target error and the explanation conveys the applicable rule. The wording is awkward/context-bound; adequacy is a judgment for human confirmation. |
| 52 | languagetool | They depend on public transport. | correct_abstention | not_applicable | No correction is needed; no unnecessary edit was proposed. |
| 52 | qwen | They depend on public transport. | correct_abstention | not_applicable | No correction is needed; no unnecessary edit was proposed. |
| 53 | languagetool | I enjoy to swim. | useful | adequate | The edit fixes the approved target error and the explanation conveys the applicable rule. |
| 53 | qwen | I enjoy to swim. | incorrect_edit | rule_correct_but_edit_wrong | Assistant checked the full resulting sentence: this proposal fails the target correction; the difference is not merely an alternative valid reference. The explanation identifies the rule, but the selected edit span is wrong. |
| 54 | languagetool | I enjoy swimming. | correct_abstention | not_applicable | No correction is needed; no unnecessary edit was proposed. |
| 54 | qwen | I enjoy swimming. | correct_abstention | not_applicable | No correction is needed; no unnecessary edit was proposed. |
| 55 | languagetool | She decided studying medicine. | missed | missing | No correction was offered for the approved target error. |
| 55 | qwen | She decided studying medicine. | rejected | unusable | The entire no-op response was rejected. Count the target error as missed, not as clean input. |
| 56 | languagetool | She decided to study medicine. | correct_abstention | not_applicable | No correction is needed; no unnecessary edit was proposed. |
| 56 | qwen | She decided to study medicine. | correct_abstention | not_applicable | No correction is needed; no unnecessary edit was proposed. |
| 57 | languagetool | Please give the key to I. | useful | adequate | The edit fixes the approved target error and the explanation conveys the applicable rule. |
| 57 | qwen | Please give the key to I. | rejected | unusable | The entire no-op response was rejected. Count the target error as missed, not as clean input. |
| 58 | languagetool | Please give the key to me. | correct_abstention | not_applicable | No correction is needed; no unnecessary edit was proposed. |
| 58 | qwen | Please give the key to me. | correct_abstention | not_applicable | No correction is needed; no unnecessary edit was proposed. |
| 59 | languagetool | This is hers coat. | missed | missing | No correction was offered for the approved target error. |
| 59 | qwen | This is hers coat. | incorrect_edit | incorrect | Assistant checked the full resulting sentence: this proposal fails the target correction; the difference is not merely an alternative valid reference. |
| 60 | languagetool | This is her coat. | correct_abstention | not_applicable | No correction is needed; no unnecessary edit was proposed. |
| 60 | qwen | This is her coat. | correct_abstention | not_applicable | No correction is needed; no unnecessary edit was proposed. |

## Next checkpoint

The grading rule and flagged judgments are approved, with row 16 recorded as a borderline pass. Sections A and B are approved; only the ten section C failure judgments remain pending. Then finalize a separately versioned human-reviewed scorecard and choose a development-only improvement. Do not run held-out tests to select a winner. The existing inference outputs remain immutable; proposed explanations must not be substituted into model outputs before scoring.
