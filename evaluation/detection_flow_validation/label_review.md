# Targeted combined-flow labels — approved

Thirty-two new inputs: 16 errors (8 did questions, 8 counted nouns) and 16 acceptable inputs. Eight acceptable inputs reuse references within this new dataset; eight are boundary cases. No input repeats a prior evaluated sentence under the recorded normalization. No inference has been run.

## Error inputs and proposed references

| ID | Input | Reference correction |
| --- | --- | --- |
| E1 | Did your manager approved the schedule? | Did your manager approve the schedule? |
| E2 | Did Elena borrowed your umbrella? | Did Elena borrow your umbrella? |
| E3 | Did the courier delivered the package? | Did the courier deliver the package? |
| E4 | Did our neighbors moved last month? | Did our neighbors move last month? |
| E5 | Did you forgot the password? | Did you forget the password? |
| E6 | Did the mechanic fixed the engine? | Did the mechanic fix the engine? |
| E7 | Did they chose a different route? | Did they choose a different route? |
| E8 | Did your brother broke the glass? | Did your brother break the glass? |
| E9 | I bought six orange. | I bought six oranges. |
| E10 | We packed nine towel. | We packed nine towels. |
| E11 | They found four feather. | They found four feathers. |
| E12 | I collected twelve button. | I collected twelve buttons. |
| E13 | We ordered eight cup. | We ordered eight cups. |
| E14 | They planted fifteen seed. | They planted fifteen seeds. |
| E15 | I counted seven cherry. | I counted seven cherries. |
| E16 | We washed five dish. | We washed five dishes. |

## Acceptable inputs — no correction expected

| ID | Input |
| --- | --- |
| C1 | Did your manager approve the schedule? |
| C2 | Did Elena borrow your umbrella? |
| C3 | Did you forget the password? |
| C4 | Did they choose a different route? |
| C5 | I bought six oranges. |
| C6 | We packed nine towels. |
| C7 | I counted seven cherries. |
| C8 | We washed five dishes. |
| C9 | Did the person called Alex leave early? |
| C10 | Did you see the damaged window? |
| C11 | I bought four coffee mugs. |
| C12 | We watched seven sheep. |
| C13 | They photographed three deer. |
| C14 | I bought a six-cup tray. |
| C15 | We need more equipment. |
| C16 | I paid five dollars. |

C9: “called Alex” identifies the person; “leave” is the main verb after “did”. C10: “damaged” describes the window. C11 and C14 use singular noun modifiers. C12–C13 have plurals that keep their spelling. C15 uses uncountable “equipment”.

Review assumes ordinary standalone English. Approve all labels or identify changes by E/C number. This approves test expectations only, not unseen model outputs or integration.

Next: record label approval, then validate actual generated proposals through the frozen detector. Require at least 13/16 human-useful corrections, zero offers on 16 correct inputs and zero unavailable results. Explanation refinement and latency optimization remain deferred.

Approval update: the project owner confirmed the references and acceptable inputs, then instructed “run it”. All 32 labels are recorded in labels_approved.json and label_approval.json. Model outputs require separate review.
