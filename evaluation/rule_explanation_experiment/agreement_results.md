# Subject–verb agreement improvement — four new judgments approved

Project owner approved the four new corrections and explanations on 2026-09-30 ("APPROVE"). Combined with the 14 earlier approvals, confirmed useful feedback is **18/30 (60%)**, compared with the original grammar-only baseline of **17/30 (56.7%)**. Twelve erroneous inputs remain uncovered. Zero offers on the 30 correct development inputs. This small development-set gain does not establish general reliability.

| Original input | Proposed correction | Explanation |
| --- | --- | --- |
| She walk to work every morning. | She walks to work every morning. | For one person, use ‘walks’ in the present tense. |
| There are a bowl on the table. | There is a bowl on the table. | Use ‘there is’ for one thing. |
| My aunt drive a bus. | My aunt drives a bus. | For one person, use ‘drives’ in the present tense. |
| The students needs more time. | The students need more time. | For more than one person, use ‘need’ in the present tense. |

Evidence: development_results_agreement_v3.json and agreement_review_approved.json (prior pending review preserved in agreement_review_v3.json). v1 is preserved; v2 excludes ambiguous read→reads because read may already be past tense. Development counts are unchanged.

Next: challenge the narrow rules on new contexts before any integration decision. No held-out cases were used, no model calls were made, and the live app is unchanged.
