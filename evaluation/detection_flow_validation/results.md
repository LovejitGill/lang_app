# Complete grammar-flow validation — targeted quality gates passed

> Wording update after this run: number-based explanations now use “is more than one.”
> See [revised explanations](wording_update.md). The actual-output table below preserves the evaluated wording.

Completed all **32** single-attempt inputs. Offered corrections on **16/16** erroneous inputs; **16** of those match approved references. Offered changes on acceptable inputs: **0/16**. Unavailable responses: **0**.

Withheld errors: **0**; errors left unchanged by generation: **0**. These stay in the denominator. The required human-useful score is **13/16**. Reference matching is not a substitute for reviewing the explanation and preserved meaning.

Final review (2026-10-01): the project owner approved **16/16 useful corrections** (required: **13/16**) and **16/16 acceptable-input preservation checks**. All targeted quality gates passed; no judgments remain pending. Approval is recorded in [output_review_approved.json](output_review_approved.json). The app has not been integrated.

## Measured processing time

| Stage | Median | p95 | Maximum |
| --- | --- | --- | --- |
| Model generation | 3.279 s | 6.566 s | 15.004 s |
| Built-in grammar check | 0.022 s | 0.038 s | 0.068 s |
| Supplemental Java check | 3.623 s | 4.537 s | 4.738 s |
| Complete grammar processing | 7.430 s | 10.400 s | 18.722 s |

First attempt total: **18.722 s**. Median excluding first: **7.341 s**. Stage medians must not be added to infer a total; the total column was measured directly. Supplemental checking starts a Java process per input. This is current offline grammar-processing cost, not microphone-to-speaker latency or an optimized streaming implementation. No repeated run was used to seek a better result.

## Actual outputs

| ID | Input | Actual model proposal | Detector state | Offered explanation |
| --- | --- | --- | --- | --- |
| E1 | Did your manager approved the schedule? | Did your manager approve the schedule? | provisional | ‘Did’ already marks the past, so use ‘approve’, not ‘approved’. |
| C1 | Did your manager approve the schedule? | Did your manager approve the schedule? | no_proposal | — |
| E2 | Did Elena borrowed your umbrella? | Did Elena borrow your umbrella? | provisional | ‘Did’ already marks the past, so use ‘borrow’, not ‘borrowed’. |
| C2 | Did Elena borrow your umbrella? | Did Elena borrow your umbrella? | no_proposal | — |
| E3 | Did the courier delivered the package? | Did the courier deliver the package? | provisional | ‘Did’ already marks the past, so use ‘deliver’, not ‘delivered’. |
| C3 | Did you forget the password? | Did you forget the password? | no_proposal | — |
| E4 | Did our neighbors moved last month? | Did our neighbors move last month? | provisional | ‘Did’ already marks the past, so use ‘move’, not ‘moved’. |
| C4 | Did they choose a different route? | Did they choose a different route? | no_proposal | — |
| E5 | Did you forgot the password? | Did you forget the password? | provisional | ‘Did’ already marks the past, so use ‘forget’, not ‘forgot’. |
| C5 | I bought six oranges. | I bought six oranges. | no_proposal | — |
| E6 | Did the mechanic fixed the engine? | Did the mechanic fix the engine? | provisional | ‘Did’ already marks the past, so use ‘fix’, not ‘fixed’. |
| C6 | We packed nine towels. | We packed nine towels. | no_proposal | — |
| E7 | Did they chose a different route? | Did they choose a different route? | provisional | ‘Did’ already marks the past, so use ‘choose’, not ‘chose’. |
| C7 | I counted seven cherries. | I counted seven cherries. | no_proposal | — |
| E8 | Did your brother broke the glass? | Did your brother break the glass? | provisional | ‘Did’ already marks the past, so use ‘break’, not ‘broke’. |
| C8 | We washed five dishes. | We washed five dishes. | no_proposal | — |
| E9 | I bought six orange. | I bought six oranges. | provisional | ‘Six’ means more than one, so use the plural ‘oranges’. |
| C9 | Did the person called Alex leave early? | Did the person called Alex leave early? | no_proposal | — |
| E10 | We packed nine towel. | We packed nine towels. | provisional | ‘Nine’ means more than one, so use the plural ‘towels’. |
| C10 | Did you see the damaged window? | Did you see the damaged window? | no_proposal | — |
| E11 | They found four feather. | They found four feathers. | provisional | ‘Four’ means more than one, so use the plural ‘feathers’. |
| C11 | I bought four coffee mugs. | I bought four coffee mugs. | no_proposal | — |
| E12 | I collected twelve button. | I collected twelve buttons. | provisional | ‘Twelve’ means more than one, so use the plural ‘buttons’. |
| C12 | We watched seven sheep. | We watched seven sheep. | no_proposal | — |
| E13 | We ordered eight cup. | We ordered eight cups. | provisional | ‘Eight’ means more than one, so use the plural ‘cups’. |
| C13 | They photographed three deer. | They photographed three deer. | no_proposal | — |
| E14 | They planted fifteen seed. | They planted fifteen seeds. | provisional | ‘Fifteen’ means more than one, so use the plural ‘seeds’. |
| C14 | I bought a six-cup tray. | I bought a six-cup tray. | no_proposal | — |
| E15 | I counted seven cherry. | I counted seven cherries. | provisional | ‘Seven’ means more than one, so use the plural ‘cherries’. |
| C15 | We need more equipment. | We need more equipment. | no_proposal | — |
| E16 | We washed five dish. | We washed five dishes. | provisional | ‘Five’ means more than one, so use the plural ‘dishes’. |
| C16 | I paid five dollars. | I paid five dollars. | no_proposal | — |

## Flagged cases

No automatic mismatch/failure flags. The delivered explanations are approved. The original number wording was accepted as accurate; the revised “is more than one” wording was separately approved as a clarity improvement. This review does not approve the raw model-generated explanations, which are not the delivered feedback.

## Limits and next step

This is a targeted synthetic grammar evaluation, not broad tutoring, pronunciation or voice validation. Eight acceptable cases are paired reference sentences. The code/model/settings remained frozen, and labels were not sent to the model or detectors. Raw stage evidence, errors and timing are preserved in results.json. Human judgments belong in a separate review artifact; preserve this source run.

Next proposed improvement: Prepare an opt-in integration of the reviewed grammar flow, keeping conversational replies and grammar feedback separate. Measure reply and feedback delays separately. Broader explanation refinement remains deferred.

The targeted detection-validation step is complete. The measured 7.430-second grammar-processing median remains a limitation; this quality pass does not establish the two-second voice target. Original source results and protocol remain unchanged. The current number wording has a separate revision record; no inference was repeated to finalize this review.
