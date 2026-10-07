# Number explanation wording — 2026-10-01

User-requested change: use “is more than one” in number-based explanations.
The current template is `sentence-specific-reasons-v2`.

Replayed the 32 saved proposals and checker outputs locally: eight explanation
strings changed, and every other decision field stayed identical. No model or
checker calls were made; this is a wording replay, not a new accuracy or timing
evaluation. Original results, human judgments, protocol and source hashes are
preserved. The pre-edit reason source is in
`frozen/grammar_explanation_reasons.py.txt`.

## Revised offered explanations

| ID | Current explanation |
| --- | --- |
| E9 | ‘Six’ is more than one, so use the plural ‘oranges’. |
| E10 | ‘Nine’ is more than one, so use the plural ‘towels’. |
| E11 | ‘Four’ is more than one, so use the plural ‘feathers’. |
| E12 | ‘Twelve’ is more than one, so use the plural ‘buttons’. |
| E13 | ‘Eight’ is more than one, so use the plural ‘cups’. |
| E14 | ‘Fifteen’ is more than one, so use the plural ‘seeds’. |
| E15 | ‘Seven’ is more than one, so use the plural ‘cherries’. |
| E16 | ‘Five’ is more than one, so use the plural ‘dishes’. |

Source results SHA-256: `e9ae2ada70dc5b5a698fa1717b7384eceae4faaad56767062f98efab6759a938`.

Verification: 21 focused tests passed; Ruff passed. The existing 88-case replay
also preserved every detection decision.

Next: finish the pending usefulness review of the completed run. Record this
wording preference separately from judgments of the original delivered outputs;
no other output approvals are inferred. Broader explanation refinement remains
deferred.
