# Focused feedback-quality experiment

These are original, assistant-authored evaluation sentences with expected
standard-English judgments. The assistant reviewed their labels; independent
learner/instructor review remains necessary. They are not a certified benchmark.

## Protocol fixed before comparison

- `development.json`: 20 sentences, 10 acceptable and 10 with a target error.
- `heldout.json`: 20 different sentences, similarly balanced, reserved from
  prompt selection. Authoring the set does not mean it was used to tune prompts.
- `regression.json`: six previously observed failures; explicitly not held out.
- Both main sets cover all three levels and scenarios. Sentences test language
  features across settings; not every sentence is an ideal scenario opener.
- Compare `baseline` and `conservative` using development cases only. Both use
  the same Qwen model, JSON schema, temperature, output limit, and retry policy.
- Cases are independent, with no prior learner history or database writes.
  This experiment evaluates sentence feedback, not multi-turn recall.
- Variant order alternates by case. Loading state and host workload are not
  controlled; report elapsed time without claiming an isolated speed benchmark.
- Record actual feedback and conversational replies, not only schema validity.
  An empty list on erroneous input is a miss even if the reply silently rewrites it.
- Review correction, explanation, preserved meaning, reply grammar, and whether
  the reply invites relevant elaboration separately. Nonempty feedback alone is
  not proof that a useful correction was made.
- Select based on development results before looking at held-out output. A
  candidate that simply suppresses all feedback is not an improvement.
- If a candidate is selected, run held-out cases twice, plus regressions. Do not
  change the prompt after seeing held-out failures and still call those cases
  unseen; create a fresh held-out set for a subsequent tuning cycle.
- If neither candidate is acceptable, keep the existing application default,
  report the failed experiment, and leave held-out cases reserved for a future
  development-selected candidate. Do not run them just to find easier successes.

## Acceptance targets

For each held-out run: no invented correction on 10 acceptable sentences, at
least 9/10 useful corrections with accurate explanations on erroneous sentences,
and no grammatical error introduced in the conversational replies. Repeat once
and report both runs. These are small project gates, not general guarantees.

Development selection must reduce false corrections without a collapse in useful
error correction or conversational quality. Report timing and retries separately.
Original regression failures must stay visible, even if a new set performs well.

## Reading the runner

`quality_eval.py` uses the real `ask_tutor()` parser/retry path with a temporary
in-process prompt override. It never changes application settings or writes
learner history. The expected labels stay in the report, outside model messages.
Prompt and dataset hashes identify the exact inputs; the model digest and
generation settings identify the runtime. A new output filename is required to
avoid overwriting past evidence. Partial results are saved after every call.

Mechanical summary fields describe feedback presence and completed calls only.
`review: null` means semantic review has not been recorded. Do not interpret that
as success. Any populated review must identify its reviewer and rationale.

## Learning exercise

TODO: Review five acceptable and five erroneous sentences yourself before reading
the model results. Compare your judgments with the recorded assistant review,
flag ambiguous labels, and explain why fewer corrections alone is insufficient.
Once a held-out item influences a prompt decision, retire it from the held-out set.
