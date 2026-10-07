# Context challenge results

The fixed set contains 24 assistant-authored engineering expectations, including
positive controls, scope checks and troublesome contexts. These are new development
checks, not an untouched held-out benchmark or user-approved grammar judgments.

| Check | Before | After |
| --- | --- | --- |
| Expected challenge behavior | 18/24 | 24/24 |
| User-approved useful development feedback | 18/30 | 18/30 |
| Offers on correct development inputs | 0/30 | 0/30 |

Six failures triggered changes:

| Case | Problem | Response |
| --- | --- | --- |
| Quoted “He can speaks French” | Edited a quoted example | Withhold quoted input |
| Since five years ago | Produced “for five years ago” | Require the supported duration to end the sentence |
| 2.5 book | Matched the trailing 5 as a whole integer | Reject partial numeric matches |
| Twenty-two box | Matched only the suffix “two” | Reject hyphenated number suffixes |
| They likes tea | Explanation incorrectly assumed several people | Withhold this subject in the plural-person rule |
| She can takes a break and he need rest | Offered a sentence with an unchecked second clause | Withhold coordinated clauses |

Some of these are scope or explanation failures, not incorrect word replacements.
For example, “They like tea” is valid for singular or plural they, and “2.5 books”
may be a useful correction. This candidate deliberately withholds these cases
until it can explain them within its declared scope.

The 18 earlier approvals carry forward only after exact comparison of input,
proposed correction, rule and explanation; development_review.json records that
provenance. Raw reports and before/after code hashes are preserved. No new inference,
model training, held-out input access or live-app changes occurred.

## Limits and next step

Passing checks used to guide fixes is regression evidence, not independent proof.
Broad guards also withhold valid corrections in contractions, quotations and
coordinated sentences. These coverage costs are not visible in the original 60-case
sample. Other contextual failures can remain; regex matching is not a full parser.

Next: freeze this candidate and establish a separate validation protocol and
reviewed labels before one held-out run. Count withheld genuine errors as misses,
review explanation correctness, and measure latency separately. Do not tune against
the held-out outputs and then report them as independent validation.
