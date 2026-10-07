# Held-out validation — not selected

All 40 labels were approved by the user. One attempt per case completed, with no unavailable responses. Only **1/20** error cases received an offered correction; even approval would give at most **5%** useful coverage, below the required **12/20 (60%)**. There were **0/20** offers on correct inputs. Human output judgments remain pending; this coverage upper bound already establishes failure.

The raw sentence generator matched references for **20/20** errors. Reference matches do not establish explanation accuracy. The fixed rule filter withheld 19 erroneous cases, exposing poor generalization of its finite vocabulary and narrow patterns.

Generation plus rule-check time: median **3.543 s**, p95 **5.899 s**, maximum/first attempt **19.589 s**. Excluding the first attempt, median **3.537 s**. These are text-processing measurements, not full voice latency; the two-second target was not met by median text processing.

## Offered correction (human review pending)

| Original | Proposal | Delivered explanation |
| --- | --- | --- |
| She does not eats meat. | She does not eat meat. | After ‘do’, ‘does’, or ‘did’, use the basic verb form. |

## All error-case outputs

Original model explanations below are raw evidence, not delivered feedback when withheld. Several contain wrong reasoning despite correct edits.

| Input | Raw proposed sentence | Raw model explanation | Rule state |
| --- | --- | --- | --- |
| Each visitor receive a badge. | Each visitor receives a badge. | Use plural verb 'receives' for singular subject 'each visitor'. | withheld |
| My neighbors has a dog. | My neighbors have a dog. | Use have with the plural subject neighbors. | withheld |
| It was an useful lesson. | It was a useful lesson. | Use article 'a' before the adjective 'useful'. | withheld |
| She waited for a hour. | She waited for an hour. | Use 'an' before 'hour' because 'hour' starts with a vowel sound. | withheld |
| We meet him last Friday. | We met him last Friday. | Use past tense met for the past event. | withheld |
| Last summer he teach English. | Last summer he taught English. | Use past tense for the verb 'teach' when referring to a completed action in the past. | withheld |
| There are six chair upstairs. | There are six chairs upstairs. | Plural form of chair is chairs. | withheld |
| She bought two ticket online. | She bought two tickets online. | Use plural form 'tickets' for the countable noun 'ticket' when referring to more than one. | withheld |
| We must finishes before noon. | We must finish before noon. | Use singular verb 'finish' with plural subject 'we'. | withheld |
| She could sings very well. | She could sing very well. | Use sing (base form) after could for past ability. | withheld |
| Did they left already? | Did they leave already? | Use past simple tense 'leave' instead of 'left' for the question structure. | withheld |
| She does not eats meat. | She does not eat meat. | Use 'eat' (base form) after 'does not' for the third person singular. | provisional |
| My bag is more heavier than yours. | My bag is heavier than yours. | Remove the redundant adjective 'more' as 'heavier' already implies comparison. | withheld |
| The second task was more easier. | The second task was easier. | Use 'easier' instead of 'more easier' to avoid double comparison. | withheld |
| We have waited since twenty minutes. | We have waited for twenty minutes. | Add 'for' before the time duration and use the correct time expression format. | withheld |
| She is afraid from spiders. | She is afraid of spiders. | Use 'of' instead of 'from' with the preposition for fear. | withheld |
| They avoided to argue. | They avoided arguing. | Use the gerund form after the verb 'avoid'. | withheld |
| He hopes finding a job. | He hopes to find a job. | Add 'to' after the verb 'hopes' to form the infinitive phrase. | withheld |
| The invitation is for she. | The invitation is for her. | Use her instead of she for the correct pronoun case. | withheld |
| That is mine bicycle. | That is my bicycle. | Use my before the noun to show possession. | withheld |

## Decision and next step

Do not integrate this candidate. Short fixed wording remains promising, but the current word lists do not support unfamiliar vocabulary. Redesign rule detection using development material and evaluate a broader range of words and contexts. Preserve this failed validation; if its cases guide fixes, use fresh independent cases for future validation. No model training or app changes occurred.

Verification: eight runner tests passed; the full suite previously passed 267 tests before adding the eighth bookkeeping test. Active-code lint and uv lock checks passed. Frozen snapshots were excluded from lint because their relocated imports produce a sorting warning; no archived source was modified.
