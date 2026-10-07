# Partial owner review — contextual_v2 — 2026-10-06

Nine named cases plus the exact uncle/work example mapped to C09. No blanket approval, no new candidate selection, and no full benchmark score.

**No full pass rate or candidate promotion follows from this review.** C01 is conditional approval of the question direction after removing the example tail. Other named replies require revision. Unmentioned cases remain unreviewed.

All proposed revised replies and new counterexamples are assistant-authored proposals, not model outputs or owner-approved text.

## Source binding

| Preserved source | SHA-256 |
| --- | --- |
| `warm_results.json` | `c7baa98936c1193bc034707ab3ee00a96c593cd375c719c1d188e50a8d7d3b76` |
| `review_draft.json` | `d21da161e52b611e224a39576a04681daef1943cf9201aeaf8e798a0f00cdfac` |

The draft review’s source hash matches the bound warm results. The original results, dataset, draft review, and previous selection were not edited by this review.

## Case-specific feedback

### D02 — needs revision

**Original learner input:** Did you visited the castle?

**Original delivered reply:** I'm an AI, so I don't have real-world experiences. Describe a place you would like to visit and why.

**Owner feedback (verbatim):**

> D02 response can be improved by stating something like I'm an AI, I can't visit castles. What castle would want to visit ? Should also start with a correction since it should be visit, not visited.

**Assistant assessment:** Keep the castle topic when explaining the lack of physical experiences.

**Assistant-proposed conversational reference, not approved:** I'm an AI, so I can't visit castles. Which castle would you like to visit?

**Separate grammar request:** `visited → visit`.

This is a necessary correction: did takes the base verb visit.

**Proposed display only after verifying the correction:** “Did you visit the castle?” Use “visit” after “did.”

Start with the correction.

### D09 — needs revision

**Original learner input:** I cooked rice with my sister.

**Original delivered reply:** Tell me what you did with your sister.

**Owner feedback (verbatim):**

> D09 response not sufficient, should either as how the rice tasted or even ask what type or rice. Convo should flow almost as a true human to human convo

**Assistant assessment:** Ask about the cooking result or rice itself, rather than repeating a broad activity question.

**Assistant-proposed conversational reference, not approved:** How did the rice you cooked with your sister turn out?

### D10 — needs revision

**Original learner input:** Working from home helps me focus, but I miss talking to colleagues.

**Original delivered reply:** Tell me about the benefits and difficulties of working from home, with an example.

**Owner feedback (verbatim):**

> D10 stop ending questions with "with an example/ with a few details" or any other variation of the same.

**Assistant assessment:** Remove automatic example/details tails and follow the stated benefit/trade-off.

**Assistant-proposed conversational reference, not approved:** What do you miss most about talking with your colleagues?

### D11 — needs revision

**Original learner input:** I would like vegetable soup, and I prefer food that is not spicy.

**Original delivered reply:** Describe what your ideal meal would be like.

**Owner feedback (verbatim):**

> D11 response should ask about the soup or at least ask in a way that acknowledges the statement for example: "what about other food, what would be your Ideal meal?"

**Assistant assessment:** Retain the soup context and respect the non-spicy preference; do not invent a menu or promise food preparation.

**Assistant-proposed conversational reference, not approved:** What would you like to have with your vegetable soup?

### D12 — needs revision

**Original learner input:** She go to work by train.

**Original delivered reply:** Tell me more about them and what happens.

**Owner feedback (verbatim):**

> D12 No correction for go to goes* and and show resonse was generic, could've asked how long does it take her

**Assistant assessment:** Preserve she/her and connect the follow-up to her commute.

**Assistant-proposed conversational reference, not approved:** How long does her train journey to work take?

**Separate grammar request:** `go → goes`.

This is a necessary correction for third-person singular present she.

**Proposed display only after verifying the correction:** “She goes to work by train.” Use “goes” with “she” in the present tense.

A correction is requested; a specific order was not separately stated for this case.

### C01 — conditional approval with revision

**Original learner input:** My name is Luis and I enjoy sketching.

**Original delivered reply:** Tell me what interests you about sketching, with an example.

**Owner feedback (verbatim):**

> C01 great response, just exclude the with an example portion

**Assistant assessment:** The owner accepts the question direction conditionally on removing the example tail.

**Assistant-proposed conversational reference, not approved:** Tell me what interests you about sketching.

### C04 — needs revision

**Original learner input:** My friend said "goodbye" and left.

**Original delivered reply:** Tell me more about them and what happens.

**Owner feedback (verbatim):**

> C04  response sounds somewhat generic

**Assistant assessment:** Treat goodbye as reported speech in a completed event, not a command to end this conversation.

**Assistant-proposed conversational reference, not approved:** What happened before your friend said goodbye?

### C11 — needs revision

**Original learner input:** My brother is upset because he missed his train.

**Original delivered reply:** Tell me more about them and what happens.

**Owner feedback (verbatim):**

> C11 generic response that doesn't even make sense

**Assistant assessment:** Acknowledge the stated upset and ask about the specific event without inventing what happened afterward.

**Assistant-proposed conversational reference, not approved:** That sounds frustrating for him. What did your brother do after he missed the train?

### C15 — needs revision

**Original learner input:** I take a short walk because it helps me relax.

**Original delivered reply:** Tell me what that walk feels like, with a few details.

**Owner feedback (verbatim):**

> C15 response didn't have correction for take -> took. weird what to phrase response, can moreso ask how did the walk feel.

**Assistant assessment:** Revise the unnatural tail, but retain habitual present unless a completed-past meaning is established.

**Assistant-proposed conversational reference, not approved:** What is it about a short walk that helps you relax?

**Separate grammar request:** `take → took`.

The recorded sentence is grammatical habitual present. No necessary take→took correction is established.

If the intended meaning is one completed walk, “I took a short walk because it helps me relax” is possible. That changes the temporal meaning rather than correcting the recorded habitual-present sentence.

**Do not adopt this requested tense change as a necessary reference correction for the recorded input.**

### C09 — needs revision

**Original learner input:** Where does my uncle work?

**Original delivered reply:** I don't have that information in our recent conversation. Tell me more about that person or place, with a few details.

**Owner feedback (verbatim):**

> also various responses state some variation of "I don't have that information in our recent conversation. Tell me more about that person or place, with a few details."
> response should always tie back to the statement. for example: if a learner states "Where does my uncle work?" tutor should respond with a statement/question that mentions either the uncle or work or both.

**Assistant assessment:** The owner supplied this input as an example without naming C09; it matches C09 exactly. Preserve the uncle/work relation while admitting uncertainty.

**Assistant-proposed conversational reference, not approved:** I don't know where your uncle works. What do you know about his job?

## General acceptance rules

- **R01 (owner feedback):** Tie every reply to the learner statement or available history. For unknown facts, retain the requested person, place, or relationship.
- **R02 (owner feedback):** Remove automatic endings such as “with an example” and “with a few details,” including equivalent variants.
- **R03 (assistant operationalization of owner feedback):** Connect the follow-up to the event or relationship, not merely one shared noun: cooking result, commute duration, or what happened after a missed train.
- **R04 (assistant proposal):** Preserve person, tense, negation, topic changes, and stated preferences. A question must not assume a future event already occurred.
- **R05 (assistant proposal):** Prefer one natural, specific question. A useful specific question may permit a short answer; do not add unnatural tails merely to demand a longer answer.
- **R06 (assistant proposal):** Keep conversational quality, grammar correctness, and correction presentation as distinct review dimensions. Show only a verified correction; do not invent an error to satisfy a display request.
- **R07 (assistant proposal):** Answer direct questions when supported. Unknown personal facts and language questions require different handling; an irrelevant follow-up is not an answer.
- **R08 (existing requirement retained):** Evaluate quality and response time together. Existing warm text measurements exclude DB, UI, STT, TTS, and readiness setup and cannot establish a two-second spoken response.

## Proposed counterexamples

These are new assistant-authored checks, not model runs, approved reference data, or a held-out evaluation claim.

| Proposal | Input and relevant history | Expected distinction |
| --- | --- | --- |
| N01 | I will cook rice with my sister tomorrow. | Discuss the plan; do not ask how the rice tasted already. |
| N02 | I cooked pasta with my brother. | Transfer cooking follow-ups to other foods and people without assuming success. |
| N03 | She doesn’t go to work by train. | Do not change go to goes after does not; do not assume she commutes by train. |
| N04 | Did you go to the museum? | Give an honest AI boundary tied to the museum topic; do not invent a grammar error. |
| N05 | Yesterday I take a short walk. | The explicit past-time cue supports take→took, unlike habitual-present C15. |
| N06 | My sister is relieved because she caught her bus. | Preserve the positive outcome and emotion; do not apply missed-train frustration. |
| N07 | I’d like soup, but I can’t eat dairy. | Retain the food constraint without claiming menu availability or promising to prepare food. |
| N08 | Where does my uncle work? Earlier learner: My uncle works at a library. | Use the learner-provided library fact instead of the unknown-fact fallback. |
| N09 | Where does my uncle work? Earlier learner: My uncle used to work at a library, but he changed jobs. | Do not report the library as his current workplace; acknowledge that the current job is unknown. |

## Review boundaries and next improvement

Unreviewed case IDs: D01, D03, D04, D05, D06, D07, D08, D13, D14, D15, D16, C02, C03, C05, C06, C07, C08, C10, C12, C13, C14, C16.

General wording instructions also apply to unreviewed cases but do not constitute individual quality approvals or rejections.

All per-case binary score fields remain unset. Grammar requests do not retrospectively turn this conversation-only run into a grammar evaluation.

Implement general context-specific follow-ups and evaluate them against current cases plus varied counterexamples under the same latency budget. Preserve correction ordering as an explicit presentation requirement and resolve it without silently accepting the C15 tense change.
