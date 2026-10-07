# SpeakWell — Milestone Improvement Plan

This is an ongoing record of observed limitations and proposed improvements.
After implementing each milestone, append a new section whose heading starts
with that milestone's number and name. Preserve earlier findings; add dated
updates when an improvement is tested rather than erasing the original result.

Separate observed failures, untested risks, and intentional scope boundaries.
An optimization is a proposal until a recorded comparison shows it helped.

## Milestone 2 — Tutoring Prompt Design (text-only, no UI)

**Recorded:** 2026-09-22  
**Status:** Implementation checkpoint complete; tutoring-quality improvements open.  
**Evidence:** [Live evaluation and recorded outputs](docs/tutoring_evaluation.md).  
**Relevant files:** `prompts.py`, `llm_client.py`, `tests/test_tutoring.py`.

### What works

- The local model receives a system tutoring instruction and a separate learner message.
- Level/scenario settings alter the prompt.
- Responses are parsed and validated as `reply` and `feedback` fields.
- Malformed structured output is retried at most once; service errors remain explicit.
- All 38 offline tests passed, along with lint and formatting checks.
- Live calls produced relevant corrections for several learner mistakes.

### Observed limitations

| Limitation | Observed example | Why it matters |
|---|---|---|
| Unnecessary corrections | All three correct sentences in the final six-case check received feedback, including changing “a cup of tea” to identical wording | Learners may distrust valid English or learn incorrect rules |
| Incorrect explanations | Correctly changed “since three years” to “for three years,” but explained it as “Use for with since” | A correct replacement can still teach the wrong rule |
| Grammar errors in the tutor's own reply | “What kind of dog does you have?” | The tutor should not model incorrect language |
| Missed target errors | Treated “He go to school every day” as a preposition issue instead of correcting “go” to “goes” | Relevant-looking feedback can miss the actual learning need |
| Structural checks do not assess meaning | The above outputs passed JSON validation | Passing software tests does not establish tutoring accuracy |
| Evaluation is small and influenced by tuning | Several evaluation sentences were reused while revising prompts | Results cannot establish general accuracy or reliable improvement |

### Untested risks and scope boundaries

- Temperature reduction and examples have not established repeatable quality across new inputs.
- System/user separation is useful but has not been validated as robust against attempts to change the tutor's instructions.
- Full tutoring latency, retry frequency, and output truncation have not been systematically measured. The 30-second HTTP timeout is not a two-second response guarantee.
- This milestone intentionally has no memory, database, UI, speech, or pronunciation assessment. SQLite in the next milestone will add context, not solve inaccurate grammar feedback.

### Optimization plan, in priority order

| Priority | Improvement | How to implement or investigate | How to verify |
|---|---|---|---|
| 1 | Establish a dependable evaluation baseline | Create 40 reviewed examples: 20 for prompt development and 20 held out from tuning. Balance correct/incorrect English in each group; cover all practice levels and scenarios. Keep the existing failures as a separate regression set | Save input, expected issue or no correction, actual reply, feedback, prompt version, model digest, settings, and reviewer decision |
| 2 | Reduce overcorrection | Compare the current prompt against a shorter version emphasizing corrections only for clear errors. Use balanced examples of correct/incorrect English, and change one prompt element at a time | Count invented corrections on correct inputs and useful corrections on incorrect inputs; do not reward an always-empty feedback list |
| 3 | Improve explanation and reply quality | Compare brief rule explanations against more verbose explanations; review both the correction and the tutor's conversational grammar | Mark each replacement, explanation, and conversational reply separately as correct, incorrect, or uncertain |
| 4 | Detect obvious unsupported feedback | Experiment with structured correction fields such as original span, replacement, and reason, if prompt changes alone are insufficient. Validate that the original span exists in the input and that original/replacement are not identical | Test invented spans and identical replacements; update the schema and callers together. Do not equate these checks with semantic correctness or silently discard failures to inflate quality results |
| 5 | Assess whether the model is the limiting factor | If controlled prompt experiments plateau, compare one alternative local open-source model compatible with the Intel CPU and available memory. Record license, model identity, and settings before testing | Run the same fixed examples; compare quality and latency. Keep the current model unless the measured tradeoff justifies changing it; no paid API or training |
| 6 | Reduce latency after quality improves | Measure cold/warm calls, prompt size, output tokens, and retries. Compare shorter prompts and output limits without cutting off valid JSON or useful feedback | Report median, p95, maximum, truncation, and retry rate. Text-call timing alone does not establish end-to-end voice latency |

Changing the response schema or selected model is a proposed future change,
not something this document implements. Keep the existing public interface
stable until its replacement and dependent tests are designed together.

### Proposed acceptance checkpoints

These are small project gates, not claims of general model accuracy:

- [ ] All existing software tests continue to pass; add tests for any new validation behavior.
- [ ] On the 20 held-out cases, none of the 10 correct sentences receives an invented correction.
- [ ] At least 9 of the 10 incorrect sentences receive a useful correction with an accurate explanation and preserved meaning.
- [ ] No tutor reply in that held-out run introduces a grammatical error.
- [ ] Repeat the held-out check once to expose output variation; report both runs, including failures. If a case is subsequently used for tuning, it is no longer held out.
- [ ] Evaluate the original failures again and explain any remaining regressions.
- [ ] Record latency and retries for the chosen configuration; keep the broader two-second voice requirement open until the actual voice pipeline is measured.
- [ ] Review results manually; self-grading by the same model is not the sole evidence of correctness.

### Suggested work allocation

1. **Session 1 — 2 hours:** Prepare/review the evaluation set and record a baseline.
2. **Session 2 — 2 hours:** Compare two prompt variants, review outputs, and select a candidate based on development examples.
3. **Session 3 — 1–2 hours:** Run held-out and regression checks; measure timing and document a keep/revert decision.

If quality does not improve, record the failed experiment and investigate model
capability before adding increasingly specific rules for individual sentences.
Do not present this component as dependable tutoring merely because memory or
UI features have subsequently been added.

### Progress updates

- **2026-09-22:** Improvement plan created from recorded Milestone 2 results. No additional optimization was implemented or tested as part of creating this document. All improvement items remain open.

<!-- Future entries: append a heading in the form
## Milestone N — Exact milestone name
Include date/status, working behavior, observed limitations and evidence,
untested risks/scope boundaries, prioritized improvements, verification gates,
and dated progress updates. Do not claim an untested improvement is complete.
-->

## Milestone 3 — Session Memory in SQLite

**Recorded:** 2026-09-22  
**Status:** Implementation checkpoint complete; local persistence and one live recall example verified.  
**Evidence:** [Verification results](docs/session_memory_validation.md), [verification guide](docs/session_memory.md), and `tests/test_memory.py`.

### What works

- Completed learner/tutor turns and feedback are stored in SQLite, with parameterized SQL and explicit connection cleanup.
- A supplied session ID reloads its latest four turns; a 3,000-character history budget keeps the newest complete exchanges in order.
- Two separate live Python runs demonstrated recall of “Maya” and “hiking”; a third process found both rows on disk.
- All 55 tests passed, covering isolation, ordering, prompt contents, retries, generation failures, write failures, and stateless operation without a session ID.
- Generation failures save nothing. A save failure leaves the generated reply available and warns that it will not be remembered.

### Limitations and optimization plan

| Limitation or scope boundary | Evidence/status | Improvement plan | Verification criterion |
|---|---|---|---|
| Character limits are not exact token budgets | Four turns/3,000 history characters and 1,000 current-input characters bound size, but do not count system instructions and model tokens exactly | Measure complete prompt token counts; introduce a model-aware budget with output headroom if truncation occurs | Long/multibyte inputs keep the system instruction and latest message intact without exceeding the measured context budget |
| Older facts disappear from the prompt | Only the newest complete turns within both limits are sent | Make the memory window visible in the future UI; consider summaries only after validating that they preserve facts | A multi-turn test confirms which facts are included/omitted; any summary introduces no unsupported facts |
| Concurrent calls can see stale context or save out of conversational order | Not tested or supported; each request independently reads, generates, and writes | Keep one in-flight request per session; add session serialization before supporting concurrent requests | Two simultaneous calls to one session cannot both generate against stale history; separate sessions remain independent |
| Repeated successful submissions create duplicate turns | There is no request ID/deduplication mechanism | Add a per-request ID and unique constraint when UI reruns/retries are introduced | Repeating one request ID creates exactly one row and does not duplicate generation unnecessarily |
| Saved text persists locally without expiry or encryption | Intentional baseline; stopping the process does not delete rows | Add explicit clear-session controls and a documented retention policy; avoid promising encryption without implementation | Delete one session and verify its rows are gone while other sessions remain intact; explain backups/file remnants separately |
| Session IDs do not authenticate users or capture practice settings | IDs are caller-supplied; current settings apply to the next request | Use fresh IDs for separate learners/scenarios now; add session metadata and ownership checks if needed by a future UI | Settings changes cannot silently mix unrelated practice sessions; do not claim multi-user privacy based only on IDs |
| Save failure loses that turn's future context | Warning path verified; no automatic durable recovery queue | Show a prominent unsaved indicator in the UI and allow a safe save retry with a stable request ID | Generated output stays visible; retry saves exactly once; the UI never labels an unsaved turn as remembered |
| No schema migration system | First schema only; manually edited/corrupt databases are not repaired | Add schema versioning before changing tables and document backup/recovery behavior | An older fixture upgrades without losing turns; unreadable data yields a clear error instead of silent replacement |
| Tutoring inaccuracies remain | Live test recalled the facts but wrongly corrected valid “enjoy hiking” and “my name” phrases | Continue the Milestone 2 evaluation plan; do not assume memory improves linguistic accuracy | Re-run correct/incorrect sentence tests separately from recall tests, reporting both outcomes |

### Suggested next checks

1. Before connecting a UI, test its one-request-at-a-time behavior and duplicate submission handling.
2. Evaluate recall across at least ten turns, including facts deliberately outside the retained window; confirm the tutor does not invent absent facts.
3. Measure prompt size and warm generation latency with zero versus four saved turns using the same model/settings.
4. Add retention controls before using personal learner content or claiming session data disappears on exit.

### Progress updates

- **2026-09-22:** SQLite memory implemented and validated with 55 tests and a two-process live recall check. The improvements above remain proposals; no claim of concurrent operation, exact token budgeting, deletion, or repaired tutoring accuracy is made.

## Milestone 4 — Streamlit UI (text input first)

**Recorded:** 2026-09-22  
**Status:** Text-first UI implemented; three real model turns, browser rendering, and refresh recovery verified.  
**Evidence:** [UI verification](docs/streamlit_ui_validation.md), [user guide](docs/streamlit_ui.md), and `tests/test_app.py`.

### What works

- Level/scenario selection, submitted text input, chronological transcript, separately labeled feedback, and next-turn counter.
- Forms prevent generation while merely typing; ordinary display reruns do not duplicate requests in tested flows.
- URL session IDs and SQLite metadata restore saved turns/settings after browser reload; new conversations use new IDs.
- Errors preserve the draft. Unsaved replies remain visible with an explicit warning.
- All 61 tests passed. Three real model turns completed through AppTest, and a browser displayed/restored the resulting conversation with Turn #4.

### Limitations and optimization plan

| Limitation | Observed or untested status | Improvement plan | Verification criterion |
|---|---|---|---|
| Tutor corrections are still unreliable | Observed in the live UI run; “on Saturdays” was wrongly corrected | Continue Milestone 2's separate linguistic evaluation; keep the experimental notice visible | Correct/incorrect sentence quality gates pass independently of UI tests |
| No protection against concurrent same-session tabs or all repeated submissions | Ordinary reruns tested; transactional request deduplication absent | Add request IDs and per-session sequencing before concurrency or more complex UI events | Concurrent/repeated request test creates one intended exchange, without stale-history generation |
| Full transcript loads/renders without pagination | Intended small-session baseline; long sessions not benchmarked | Measure rendering and database cost with long histories, then paginate/display a recent window with older-turn access | A long fixture loads within a documented target and preserves chronological order |
| Drafts and unsaved replies disappear on refresh | Explicit current behavior; only committed rows are durable | Consider local draft recovery and a save-only retry flow if users need them; document privacy/retention | Retry persists exactly once; refreshed UI distinguishes saved and unsaved state honestly |
| Session URLs provide lookup, not authentication | Local demo only | Keep localhost binding; add ownership/authentication before any public hosting | Unauthorized users cannot retrieve another session if public access is ever introduced |
| No delete-session UI or retention expiry | New conversation preserves old records | Add deliberate clear-history controls and retention settings in a later privacy pass | Deleting a selected session removes its metadata/turns without touching others |
| UI resumes only sessions created with metadata | Older CLI sessions lack level/scenario metadata | Add an explicit import/resume design if needed; do not guess historical settings | Migrated fixtures retain turns and require/restore correct settings |
| Busy-state and cancellation handling are basic | Spinner shown; no model cancellation control or verified multi-tab lock | Introduce explicit pending state/cancellation if long model waits cause usability problems | Cancel/retry cannot append a stale reply to a new conversation |
| Accessibility and responsive behavior are only partially checked | Labels/native widgets used; one desktop browser visually checked | Test keyboard order, screen-reader feedback announcements, and narrow viewport layout | All controls and errors are usable without a mouse and without clipped content |
| No audio interaction | Intentional Milestone 4 boundary | Add recorded-turn audio only in Milestone 5, keeping typed input available | Audio and typed inputs share the tested tutoring flow without duplicate turns |

### Suggested follow-up allocation

1. Before expanding the UI, add explicit pending-request/deduplication behavior if repeated or concurrent submissions are needed.
2. Reserve one session for keyboard/narrow-screen checks and long-history timing.
3. Keep grammar-quality evaluation separate from UI and memory success; neither proves the tutor's corrections are correct.

### Progress updates

- **2026-09-22:** Implemented and tested the text UI and saved-session refresh recovery. Limitations above are documented; proposed optimizations have not been represented as completed work.

## Milestone 2 — Tutoring Prompt Design (text-only, no UI)

### Follow-up improvement — 2026-09-22

Updated instructions and examples to invite descriptions, experiences, and
reasons through one focused follow-up. Short beginner answers receive a sentence
starter. The initial practice task is supplied to the model as context.

**Evidence:** [Conversation evaluation](docs/conversation_questions.md). All 71
automated tests passed and Ruff checks passed. Three live calls produced open
invitations, but two repeated supplied information or mismatched the level.
Two also produced false corrections. **Inaccurate feedback remains unresolved.**

| Priority | Limitation | Optimization plan | Verification criterion |
|---|---|---|---|
| 1 | False corrections persist, including identical wording and valid word choice | Build the balanced grammar evaluation set first; compare a separate conservative feedback pass against the current combined response, measuring accuracy and CPU cost before adoption | Review 20 correct and 20 incorrect sentences; target zero false corrections on the correct set and report error-detection coverage separately |
| 2 | Generated follow-ups sometimes repeat known facts and use beginner scaffolding for advanced learners | Add examples of grounded follow-ups and evaluate ten multi-turn scripts; revise one prompt variable at a time | At least 90% meet each of relevance, elaboration, no repetition, single focus, and level-fit criteria |
| 3 | Larger prompts or separate feedback passes may increase CPU delay; not benchmarked here | Measure warm and cold response time before adopting additional inference calls | Report latency distribution separately from quality; do not claim the two-second voice target is met |

## Milestone 4 — Streamlit UI (text input first)

### Follow-up improvement — 2026-09-22

Empty conversations now display one of nine authored, level/scenario-specific
opening tasks. This requires no model call and adds no artificial saved turn.
The initial task and model instructions share a single prompt-selection helper.

| Limitation | Optimization plan | Verification criterion |
|---|---|---|
| Only one starter per level/scenario; repeated sessions can feel repetitive | After conversation quality improves, add a small reviewed bank and persist the chosen starter | Reload preserves the selected starter; both UI and model receive identical text |
| Starter wording is not versioned in saved sessions | Store the selected task or prompt version before introducing randomized starters or curriculum changes | An older saved session retains its original task after a prompt update |
| Automated UI tests do not judge teaching quality | Retain the experimental-feedback notice and run the separate human evaluation above | UI success is never reported as proof of accurate corrections |

## Milestone 5 — Recorded-Turn Voice Input

**Recorded:** 2026-09-22  
**Status:** Recorded-input implementation and component tests complete; real CPU
inference checked. Personal microphone/voice acceptance remains manual.  
**Evidence:** [Verification guide](docs/recorded_voice.md),
[validation results](docs/recorded_voice_validation.md), `tests/test_stt.py`, and
audio-review tests in `tests/test_app.py`.

### What works

- Local `base.en` CPU INT8 transcription with a pinned model revision, explicit
  download step, and no model download during normal inference.
- Recording validation and silence/VAD checks; transcript is editable before
  the existing Send/tutor/history workflow runs. Typed input remains available.
- 87 automated tests and Ruff checks passed. An 11-second public reference clip
  took 3.50 seconds on the first call and 0.84 seconds on a warm repeat.
- Intel macOS wheel resolution is required explicitly; uv selected ONNX Runtime
  1.23.2 because newer 1.30.0 lacked a compatible wheel.
- A real-STT/real-Ollama AppTest run saved exactly one turn after Send and no
  duplicate after rerun, using a temporary database. It also reproduced an
  invalid correction; pipeline success does not establish feedback accuracy.

### Limitations and prioritized optimization plan

| Priority | Limitation / evidence | Plan | Measurable verification |
|---|---|---|---|
| 1 | **Inaccurate tutoring feedback remains unresolved**; transcription does not repair it | Continue the Milestone 2 grammar evaluation independently of audio; require transcript review | Report false corrections on correct sentences and missed errors on incorrect sentences separately |
| 1 | Real recognition changed “ask” to “asked” twice in the reference clip; learner grammar can also be normalized | Collect original spoken/reference pairs, compare base.en and alternatives only after establishing a baseline | Evaluate at least 20 clips across names, deliberate errors, accents, and noise; report substitutions/omissions and meaning preservation |
| 1 | Browser microphone capture and the user's voice have not been verified by automated tests | Complete the five-sentence manual exercise, silence test, permission-denied test, and one reviewed voice-to-tutor turn | Record browser/version and outcomes; successful capture and exactly one saved turn after Send |
| 2 | Energy/VAD/confidence thresholds are heuristics; quiet speech may be rejected and noise may still yield text | Evaluate labeled quiet-speech, silence, and noise clips before adjusting thresholds | Report false rejection and false speech-acceptance rates; do not present confidence as a pronunciation score |
| 2 | Warm STT timing is only one sample and excludes LLM/UI time; two-second target unproven | Measure cold/warm full-turn latency across 20 clips before testing smaller models or streaming | Report median and p95 by stage; keep the two-second goal open until end-to-end measurements meet it |
| 2 | Clips must be stopped manually; no speech output or pronunciation evidence analysis | Keep these as distinct later enhancements, after evaluation checkpoint | Do not claim automatic endpointing or pronunciation assessment from transcript-only behavior |
| 3 | Audio stays in widget/process memory temporarily; reset is not secure erasure | Document retention, test widget cleanup, and avoid persisting raw audio | Verify app-created storage contains text/model files, not learner WAVs; describe browser-memory limitations honestly |
| 3 | Serialization bounds CPU use but can queue concurrent sessions; no cancellation control | Keep the single-user demo scope; measure before adding workers or cancellation | No duplicate turns or stale replies in explicit concurrency/cancellation tests before those features are advertised |
| 3 | 60-second limit is checked after recording; raw widget upload has its own resource cost | Explain the limit now; assess duration/size controls if long clips become common | Oversized clips fail before inference without changing draft/history; do not claim the widget auto-stops |

### Learning checkpoint

Explain why model loading is cached, why inference consumes the segment iterator
inside the error handler, and why transcription must not be treated as a
pronunciation score. Complete the manual exercise before calling personal speech
accuracy validated. No proposed optimization above is represented as completed.

## Milestone 6 — Testing, Error Handling, Evaluation Pass

**Recorded:** 2026-09-22  
**Status:** Evaluation pass complete with documented quality/performance failures;
not a claim that the application is ready for unrestricted tutoring.  
**Evidence:** [Evaluation guide/report](docs/evaluation.md), exact text and audio
JSON reports in `docs/`, 96 passing automated tests, and passing Ruff checks.

### Changes and observations

- Shared `errors.py` error types/codes are wired into model, speech, storage,
  and UI paths. Offline Ollama reports TUTOR_UNAVAILABLE. Unexpected runtime
  failures receive a sanitized message; normal rerun/stop signals are preserved.
- Tests cover retry after failure, malformed output, controlled silent WAV,
  excessive transcript length, and evaluator isolation from learner history.
- Five real text turns and five recorded-audio processing turns saved correctly
  with no duplicate on rerun. Three correct text inputs received false feedback;
  the model also failed a direct recall question despite available history.
- Median text latency was 4.061 s; median completed-audio processing latency was
  5.572 s. Neither meets the original two-second target. Five samples do not
  establish tail latency or general recognition/grammar accuracy.

### Prioritized optimization plan

| Priority | Limitation / evidence | Next action | Measurable verification |
|---|---|---|---|
| 1 | False corrections on all three correct text inputs in this run | Establish the balanced 20-correct/20-incorrect set before another prompt change; compare separate conservative correction logic or a candidate local model | Report false-positive and missed-error counts independently; zero false corrections on the fixed correct set before claiming that gate passes |
| 1 | Direct question ignored; repetitive follow-ups | Evaluate ten conversations with factual questions and open-ended follow-ups; adjust examples without obscuring direct answers | Supplied facts answered correctly and unknown facts acknowledged; score grounding and question quality separately |
| 1 | Two-second goal missed even without spoken output | Measure stage timings over 20+ trials, then compare smaller model/context budgets and streaming prototypes only as separate experiments | End-to-end timing includes actual endpointing and speech start before claiming conversational latency; report median/p95 and accuracy tradeoffs |
| 2 | Small evaluation set, assistant-reviewed ratings, repeated reference audio | Have learner/instructor review exact outputs and add original microphone recordings across conditions | At least 20 varied recordings and balanced sentence evaluations, with reviewer identity and failure examples retained |
| 2 | Final UI boundary hides unanticipated failures but cannot prevent process/import/browser failures | Retain regression cases as failures are reproduced; consider privacy-safe diagnostic IDs if type alone is insufficient | Expected failures preserve draft/history; no private exception message exposed; document any non-recoverable case |
| 3 | Readiness still depends on starting Ollama separately; stale imports previously observed | Document restart order now; consider a read-only readiness indicator later | Offline startup explains recovery without modifying sessions; model availability checked before claiming ready |
| 3 | No protection against every concurrent-tab or duplicate-request scenario | Keep single-user, one-tab scope until request IDs/serialization are implemented | Concurrent retries save one intended turn with correct context in explicit tests |

### Learning checkpoint

Review the recorded ratings yourself and repeat one controlled prompt experiment.
Testing completed is distinct from all quality gates passing. No MVP freeze/tag
or optional enhancement was performed; unresolved failures remain visible.

## Milestone 7 — MVP Freeze, Then (Optional) Phase 2

**Recorded:** 2026-09-22  
**Scope:** Preserve a reproducible functional baseline under local tag `mvp-v1`;
optional enhancement and GitHub publication are separate work.

### Limitations and optimization plan

| Priority | Limitation | Next action | Verification criterion |
|---|---|---|---|
| 1 | A freeze does not repair inaccurate corrections, failed recall, or slow responses | Preserve Milestone 6 evidence; test one quality change at a time in a separate branch | Re-run the fixed evaluation inputs and report improvements/regressions before creating another release tag |
| 1 | Git excludes the model weights needed for inference | Keep current caches for the demonstration; follow setup instructions for new copies and compare the Qwen digest | A prepared checkout loads the pinned speech model and verified Qwen identity without paid services |
| 2 | Initial bootstrap depends on upstream download availability | Retain verified installers/model caches locally; document version/hash changes deliberately | Recreate dependencies from the lockfile and verify downloads without silently changing versions |
| 2 | Tests use controlled model substitutes; personal microphone behavior is not reproduced by Git | Repeat the manual recorded-voice exercise before presenting on a new machine/browser | Record microphone permission, transcript, one saved response, and silence-handling outcomes |
| 2 | Local commit/tag is not GitHub publication or final submission | Prepare final documents and presentation, then publish when requested | Remote repository contains code, lockfile, instructions and deliverables, excluding private runtime data |
| 3 | Optional audio output/automatic turns/pronunciation remain unimplemented | Choose one later enhancement with a time budget and separate branch | Existing baseline stays recoverable and tests pass independently of the experiment |

### Learning checkpoint

Use [the freeze guide](docs/mvp_freeze.md) to inspect the tag and create a
separate worktree. Understand why ignored weights/data are not in Git, and why
a functional baseline does not establish trustworthy teaching quality.

### Progress update — 2026-09-22

The working source passed 96 tests and Ruff checks. A separate source copy
recreated 63 locked packages offline from the local cache and passed all 96
tests in 13.82 seconds. This verifies source/environment isolation, not a fresh
internet bootstrap or new-machine model inference. No commit, tag, or push was
created. Per the user's preference, all Git changes are user-managed; follow
the freeze guide to finish the checkpoint. Optional enhancements remain pending.

## Milestone 2 — Tutoring Prompt Design (text-only, no UI)

### Focused evaluation improvement — 2026-09-24

Implemented the balanced evaluation workflow: 20 development cases and 20
held-out cases, each with 10 acceptable and 10 erroneous inputs; six historical
failures stay separate. Both main sets cover all levels and scenarios. Labels
were authored/reviewed by the assistant; independent human review is pending.

The opt-in evaluator uses the existing parser and retry path, excludes labels
from model messages, leaves learner history untouched, and records model digest,
settings, prompt/dataset hashes, exact output, timing, and retry count. Frozen
template snapshots, raw results, separate semantic review, and the selection
decision are retained under `evaluation/`. 101 software tests and Ruff pass.

**Observed result:** The baseline falsely corrected 10/10 acceptable development
inputs; it supplied useful, accurately explained corrections on 6/10 erroneous
inputs. The shorter conservative candidate produced no feedback on all 20
inputs—zero false corrections in the feedback array, but zero explicit useful
corrections. Conversation quality also regressed. Median measured call times
were 5.299 s and 3.267 s respectively; reduced output does not establish a useful
latency improvement. All 40 development calls parsed without retry.

**Decision:** Candidate rejected; app default unchanged. No candidate qualified
for held-out validation, so the held-out set and repeated-run acceptance gate
remain unused. This is an unsuccessful prompt experiment with improved evaluation
infrastructure, **not a fix for inaccurate feedback**. The historical regression
check reproduced baseline false corrections and candidate missed corrections.
See [results and rationale](docs/feedback_quality.md).

| Priority | Remaining limitation | Next bounded experiment | Verification |
|---|---|---|---|
| 1 | Baseline overcorrects; conservative instructions suppress all feedback | Compare one further development-only approach that separates deciding whether an error exists from phrasing the correction; preserve current outputs as controls | Count both false corrections and useful explained corrections; reject always-empty output and silent rewrites |
| 1 | Model capability may limit improvement | If further controlled prompting fails, evaluate one alternative local model with measured CPU cost rather than accumulating rules per sentence | Same development labels/settings where applicable; no model switch without a recorded quality/latency comparison |
| 1 | Labels and semantic scores have only assistant review | Learner/instructor independently reviews ambiguous labels and output judgments before relying on the acceptance gate | Identify reviewer and disagreements; version changed datasets and never relabel cases just to improve a score |
| 2 | Conversation replies may contain misleading advice despite empty feedback | Continue scoring reply grammar, grounding, and elaboration independently | Check false suggestions in the reply as well as the feedback field |
| 2 | Held-out gates not reached | Reserve held-out cases until a development-selected candidate exists, then run twice without further tuning | Zero invented corrections on 10 correct inputs and at least 9/10 useful explained corrections in each run; retain failures |
| 2 | Single-run timings, no voice/UI cost, uncontrolled model loading | Repeat stage timing only for an acceptable candidate, including cold/warm conditions and full pipeline separately | Report median, tails, retries, and output quality together; no two-second claim from this experiment |

### Learning checkpoint

Review five cases yourself and compare replacement, explanation, preserved
meaning, reply grammar and follow-up usefulness. Explain why a candidate that
never corrects anything can have zero false corrections and still fail as a tutor.
Git operations remain user-managed; no commit, tag, or push was performed.

## Milestone 2 — Tutoring Prompt Design (text-only, no UI)

### Separate grammar experiment — 2026-09-29

**Implemented:** `grammar.py` makes an isolated grammar-only call and returns
structured original/replacement/explanation entries. Mechanical validation rejects
invented word spans, no-op replacements (including whitespace/Unicode-only
changes), duplicate originals, and invalid schemas. Entire rejected responses
remain auditable; they are not reported as error-free English. The shared client
supports optional schema/model overrides while preserving existing tutor defaults.
`grammar_eval.py` compares fixed cases without writing learner history. No UI
integration, automatic text replacement, or change to transcript review occurred.

**Development evidence:** A fresh combined 1.7B baseline falsely corrected 10/10
acceptable sentences and supplied 6/10 useful explained corrections. Grammar-only
1.7B accepted false corrections on 8/10 correct sentences and rejected the other
two; it supplied only 2/10 fully useful corrections on erroneous inputs. Four
responses in total were rejected. Validation cannot establish semantic accuracy.

Because quality remained poor, one optional local model, `qwen3:4b`, was downloaded
and tested with the unchanged grammar prompt. Its digest is recorded in reports;
it remains an experiment, not the application's selected model. Development
results: 0/10 false corrections, 6/10 useful explained corrections, one rejected
response, and one missed error. Median grammar time: 2.489 s; first call 9.447 s.
The 1.7B grammar median was 1.821 s; combined baseline median was 3.756 s. These
are standalone measurements, not full conversational latency or a measured sum.

**Held-out decision:** Selected 4B for validation based on development results,
recorded the decision, then ran two unchanged held-out evaluations. Both left
all ten acceptable inputs unchanged, but useful explained corrections were only
4/10 and 5/10, below the 9/10 target. Each run rejected one no-op correction.
Neither configuration is approved for app integration. The held-out set is now
evaluated; if used for tuning later it must be replaced for unseen evaluation.

**Conversation control:** Five original-app turns completed with persistence,
but the routine follow-up repeated and the brother-workplace question went
unanswered despite available history. Grammar quality and dialogue quality remain
separate open issues. The user's transcript-review step remains intact.

**Evidence:** [Experiment guide](docs/grammar_experiment.md), raw reports and
separate assistant reviews under `evaluation/grammar_*`, and 131 passing tests.
Independent learner/instructor review remains pending. No commit/tag/push made.

| Priority | Limitation | Next bounded action | Verification criterion |
|---|---|---|---|
| 1 | Correct spans can still carry wrong edits or change meaning | Independently review replacements in their full sentence context before another development-only experiment | Score replacement, explanation and meaning separately; do not count a mechanical pass as accuracy |
| 1 | 4B abstains correctly but misses/mishandles too many real errors | Preserve this control; evaluate one further approach on development cases only, with no silent model switch | Maintain low false corrections and improve useful-correction coverage; validate on fresh held-out data if these held-out failures inform tuning |
| 1 | Inaccurate/unfinished explanations despite a correct replacement | Include explanation completeness and actual-rule accuracy in manual review | A correction is useful only when both edit and reason are correct |
| 2 | Separate calls add CPU work; asynchronous feedback not implemented | Measure a prototype conversation-first/feedback-later flow only after quality earns integration | Report conversation-start and feedback-ready times independently, including failures and cold/warm behavior |
| 2 | Direct questions still ignored and follow-ups repeated | Keep conversation tests independent of grammar tests | Direct answers reflect known facts; follow-ups build on new details without repetition |
| 2 | Labels and reviews are assistant-only; some usage judgments may be debatable | Have learner/instructor review and record disagreements without selectively relabeling to pass | Version reviewed labels and disclose score sensitivity; current failed gate is not treated as passed |
| 3 | Extra 4B weights consume about 2.5 GB and must be downloaded separately on other machines | Keep weights ignored and record model identity/source in setup evidence | No model weights/private audio enter Git; app default remains unchanged unless explicitly selected later |

### Learning checkpoint

Explain why “near” → “away from” passes span validation but changes meaning,
why identical proposals must not become an empty success, and why a correct
replacement with a wrong explanation still fails. Review the two held-out runs
and the separate conversation results before proposing the next change.

## Milestone 2 — Smallest Working Component: Call the LLM

### 2026-09-29 — Reproducible benchmark workbench and LanguageTool comparison

**Implemented:** `benchmark.py` compares grammar-only Qwen3 4B with pinned local
LanguageTool 6.6. An Intel-macOS Temurin JRE is isolated under ignored `.tools/`.
No application default changed. A 100-case draft corpus has 60 development and
40 fresh held-out cases; all labels are explicitly pending human review. The
runner gates held-out execution on named label approval, retains raw failures,
creates shuffled engine-name-hidden review worksheets, and reports precision,
recall, F0.5, false corrections and useful feedback only after review. Per-run
scores remain separate. ERRANT export refuses ambiguous edits and incomplete
runs. Conversation and speech measurement tools are separate from grammar.

**Observed evidence:** All 120 development calls completed. LanguageTool produced
60 mechanically valid responses with median 0.03245 s, p95 0.0599 s and maximum
4.4212 s. Qwen produced 56 valid and four rejected responses, median 2.75195 s,
p95 7.3238 s and maximum 12.6218 s. These include first calls and are standalone
request timings, not controlled cold/warm or end-to-end spoken latency. Raw
LanguageTool output contains a past-context mistake (bring -> brings with
Yesterday) and an optional cafe -> café change. A rule engine is not an oracle.
Quality scores remain null: independent reviews have not been supplied.

Six conversation turns completed in temporary SQLite history. This run correctly
recalled the bank and changed to cooking, but still supplied inappropriate
feedback (including works -> works, instead -> instead of, and I like -> I enjoy).
Beginner/advanced replies were nearly identical. These observations do not erase
previous failures or establish a reliable improvement.

**Intentional gates:** The 40 fresh held-out inputs were not sent to a model.
No engine is adopted. Rule explanation templates remain drafts, not activated or
represented as human-reviewed. No GPU service, pretrained pronunciation scorer,
public corpus or ERRANT scoring runtime was installed. The speech metrics are
unit-tested helpers; actual voice timing and pronunciation accuracy are unmeasured.
No Git staging, commit, tag or push was performed.

| Priority | Limitation | Next action | Verification criterion |
|---|---|---|---|
| 1 | Labels and explanations are not independently reviewed | Review the first ten labels, then complete all development labels and shuffled output judgments | Named reviewer, rationale, adjudicated alternatives; pending semantic scores never reported as passed |
| 1 | LanguageTool includes stylistic suggestions and wrong first alternatives | Review errors, then freeze a separately named curated rule/template candidate on development only | Improve useful correction coverage while preserving precision; raw baseline remains unchanged |
| 1 | Corpus is synthetic, paired and narrow | Add consented natural speech transcripts, fragments, regional variants and multiple-error cases in a versioned corpus | Report category coverage and correlated examples; do not infer population certainty from this set |
| 1 | Selection gate is documented, not fully automated | Record model/rules/prompt/report hashes and rationale before held-out execution | Two fixed held-out runs each meet 0/20 invented corrections and >=18/20 useful explained fixes, or explicitly reject adoption |
| 2 | Human scoring assumes one-to-one edits | Use an independently versioned ERRANT environment and approved reference data for richer cases | Publish tool/model versions, TP/FP/FN, failure counts and separate explanation ratings |
| 2 | First-choice LanguageTool suggestions can miss contextual tense | Review full sentences and all raw alternatives; do not auto-apply changes | No accepted correction changes time/meaning; unsupported explanations remain visible |
| 2 | Continuous audio timing not instrumented | Collect actual speech-end/playback events on a shared clock and verbatim speech references | Report full latency p50/p95, failures, cold/warm conditions, grammar-error preservation and WER |
| 3 | Larger models/GPU and pronunciation methods are untested | Consider borrowed hardware only after identifying a promising accuracy candidate; select an existing audio scorer separately | Same frozen benchmark on each platform; no paid dependency or training; no latency or pronunciation claims without data |

**Learning checkpoint:** See `docs/benchmarking.md` for commands, expected output
and explanations. Start with `evaluation/benchmark_v2/first_review_batch.md`.
Learn why abstention, failure, and an accurate explained correction are different
outcomes, and why median grammar latency does not prove the voice target.

**Verification:** 160 tests passed; Ruff, dependency-lock consistency and shell
syntax checks passed. The optional Java server was stopped after the experiment.

### 2026-09-30 — First benchmark label-review batch approved

The project owner accepted development-01 through development-10 without changes.
Recorded the exact approval and date; no additional linguistic rationale or
instructor credentials were inferred. Progress: 10/60 development labels approved;
40/40 held-out labels and all model-response judgments remain pending. Existing
result snapshots and their review hashes were preserved. The next action is
reviewing development-11 through development-20 in second_review_batch.md.
Acceptance still requires completing label review and separately judging model
corrections; this approval alone does not establish tutoring accuracy.

### 2026-09-30 — All development labels approved

The project owner accepted remaining development labels 11–60 without changes.
All 60 development labels are now approved; the first ten approvals were preserved.
No sentence, reference correction, or expected rule changed. Model-response
judgments and all 40 held-out labels remain pending. Historical inference reports
and their review worksheet hashes were preserved, so their embedded label status
still reflects the earlier provisional snapshot. Next: review the generated
corrections and explanations separately; reconcile approved-label provenance in
a new derived scoring artifact before candidate selection. No accuracy improvement
or instructor certification is inferred from label approval. The corpus test now
allows review progress; a fixture-based test checks the approval gate instead.

### 2026-09-30 — Targeted review of actual grammar outputs

Recorded project-owner observations on rows 6, 8, 18, 25, 35, 45, 53, 55 and 57
in user_feedback_2026-09-30.json and the response worksheet. Original outputs and
reference labels were preserved. This review was not blinded: engine names were
visible. Missing articles, rejected no-op proposals and incorrect edit spans remain
observed limitations. Wording preferences on rows 8/35 are recorded separately
from factual grammar errors. Row 53 is provisionally interpreted as to swim ->
swimming; row 25 distinguishes the rejected chef -> chef proposal from desired
an -> a. Unmentioned responses are not approved, and full metric fields remain
pending. Next: finish response adjudication, then test focused article/span
improvements on development data while preserving held-out separation. Verify
full corrected sentences and explanation accuracy before claiming useful feedback.

### 2026-09-30 — Draft complete development scorecard

Prepared `evaluation/benchmark_v2/draft_scorecard.md` and its JSON evidence for
all 120 responses. The assessor is explicitly the assistant; human confirmation
is pending, and the review is not blinded. All 60 approved labels were reconciled
in memory against the original run after verifying unchanged text, references,
expected issues and error counts. Existing reports, canonical response worksheet,
user observations and held-out data were preserved byte-for-byte.

Draft edit counts: LanguageTool TP=21, FP=2, FN=9; Qwen TP=20, FP=5, FN=10.
Both leave the 30 acceptable sentences unchanged, but false proposals on erroneous
inputs remain counted in precision. Qwen's four rejected responses remain misses.
Under the proposed requirement that useful feedback states the applicable rule,
LanguageTool has 15/30 useful responses and Qwen 17/30. These are assistant draft
scores, not human-approved or held-out results. They must not be cited as certified
accuracy or used to silently adopt a candidate.

Explanation adequacy is subjective on several cases: LanguageTool's countability
and generic agreement messages, and Qwen's awkward preposition explanations need
explicit adjudication. The user's wording improvements on rows 8/35 do not alone
make the original explanations factually wrong. Row 53 follows the approved
reference to swim -> swimming; its separate user-feedback interpretation remains
flagged. The next checkpoint is confirmation/revision of the draft scoring policy
and disputed judgments. Then freeze a development-only next experiment. Even
crediting every correct edit, neither current engine reaches 90% correction coverage
on these development errors; explanation templates alone cannot solve missed edits.

Verification: 120 distinct response proposals accounted for; source hashes and
original evaluation evidence unchanged; numeric counts pass the existing scorer's
consistency checks. No application changes, new inference, held-out testing, or
Git history changes were made.

### 2026-09-30 — Useful-feedback scoring requirement approved

The project owner confirmed that useful feedback requires a correct edit and an
accurate explanation of the applicable grammar rule, with meaning preserved and
no unnecessary edits. Approval is recorded in scoring_policy_approval.json.
Individual assistant ratings and provisional totals remain unapproved; agreement
with the requirement was not expanded into approval of all response judgments.
Next: adjudicate the flagged explanations under this fixed rule, then finalize
the reviewed scorecard before choosing a development-only improvement. No model
outputs, reference labels, held-out data, or application behavior changed.

### 2026-09-30 — Flagged judgments approved; row 16 borderline

The project owner approved all nine displayed flagged judgment groups (14 engine
responses), explicitly describing Qwen row 16 as barely a pass. Pass credit is
retained; improve its explanation by stating that interested takes the preposition
in. Approval is recorded per response and in flagged_judgments_approval.json.
The row 53 interpretation to swim -> swimming is now confirmed within this
approval. Earlier observations remain historical evidence. No approval was
extended to the other 106 draft response judgments, and overall draft totals
remain provisional. Raw model output, reference labels and held-out data were
preserved. Prioritize explanation clarity without hiding missed or incorrect edits;
any future candidate must demonstrate improved useful coverage on development
data before held-out evaluation. No application or Git history changes made.

### 2026-09-30 — Remaining response review consolidated

Reconciled eight failures already explicitly identified by the project owner in
earlier feedback: both engines on row 6, Qwen on 18/25/45/57, and both on 55.
This avoids duplicate approval requests; 22/120 response judgments are now
confirmed. The remaining 98 are grouped in remaining_review.md: 60 correctly
unchanged inputs, 28 proposed useful corrections, six misses and four wrong edits.
No additional judgments were assumed approved. Next: obtain the remaining
decisions and produce a separately versioned final score sheet before selecting
a development-only improvement. Existing raw report/source hashes were verified
unchanged; draft metric totals remain provisional.

### 2026-09-30 — Review sections A and B approved

The project owner approved 60 correctly unchanged responses and 28 useful
corrections, bringing confirmed judgments to 110/120. The ten section C failures
(six missed errors and four incorrect edits) remain pending; original inputs
are shown for that review. Row 16 retains its earlier borderline-pass annotation.
Draft totals were not changed or promoted to final scores. Raw report, reference
labels, held-out data and original worksheet hashes were verified unchanged.
Next: resolve section C, finalize the reviewed score sheet, and prioritize missed
errors and incorrect replacement spans in the next development-only experiment.

### 2026-09-30 — Development review complete and scores finalized

The project owner confirmed the ten section C failures, completing 120/120
response judgments. Final derived report/review/scores preserve original inference
rows and reconcile only approved label metadata with source hashes. Recomputed
results: LanguageTool TP21/FP2/FN9 and 15/30 useful responses; Qwen TP20/FP5/FN10
and 17/30 useful responses, including borderline-pass row 16. Both leave 30/30
correct sentences unchanged; Qwen has four rejected responses counted as misses.
Neither reaches 90% useful coverage. These are single-owner, unblinded reviews
of synthetic development data, not an independently expert-validated benchmark.

Next proposed experiment: a full-corrected-sentence grammar output with code-derived
replacement spans, compared against the frozen baseline on development only. This
addresses observed wrong-span failures but does not guarantee grammar/meaning
accuracy. Keep explanation changes separate to identify what helps. Verify useful
coverage, false edits, explanation adequacy, rejection rate and request latency
before selecting any candidate for held-out evaluation. No new inference, app
change, held-out testing or Git history operation occurred during finalization.

Verification: all 120 approvals accounted for, 0 pending reviews, original source
hashes unchanged, all inference rows preserved, edit counts checked against
expected totals, and final scores reproduced through the existing CLI. See
evaluation/benchmark_v2/final_scorecard.md for the command and expected output.

## Milestone 2 — Smallest Working Component: Call the LLM

### 2026-09-30 — Corrected-sentence experiment with Python-derived spans

Implemented isolated `sentence_grammar.py` and development-only `sentence_eval.py`.
The same Qwen3 4B returns complete corrected text and one response-level explanation;
Python token diff derives exact offsets, including empty-span insertions/deletions,
and verifies reconstruction. More than two edit regions or invalid output contracts
are rejected with raw output preserved. No live tutor or conversation code changed.
A versioned protocol was saved before inference, recording dataset/prompt/model
identity, settings and selection criteria. Explanations still need semantic review.

**Observed:** All 60 development calls produced mechanically valid results.
29/30 erroneous inputs matched their approved reference sentences (baseline 20/30
human-confirmed corrected inputs); all five earlier wrong-span examples now match.
However, only 29/30 correct inputs were unchanged. Row 58 was unnecessarily rewritten
and the explanation falsely claimed the original was incorrect. Row 57 retains
incorrect to I despite inserting me. Therefore this run fails the frozen
unchanged-input gate and is not selected for held-out evaluation or app adoption.
No extra repeat was run merely to find a passing sample.

Explanations remain unreliable: row 6 labels an a definite article/adjective phrase;
row 4 invents a comma change and calls please a conjunction; rows 20/41/43 misstate
verb rules. Other weak explanations are flagged in focused_review.json. Human
candidate grading is pending; 29 reference matches are not 29 useful tutor replies.
The older 17/30 useful-feedback baseline remains intact.

Standalone median request time was 4.324 s (archived baseline 2.752 s), p95 7.457 s,
maximum 15.639 s. Different runs, variable seed and uncontrolled host workload limit
speed comparisons. Full voice latency and the two-second target remain unmeasured
by this experiment. Copying complete sentences also produces more output than an
empty corrections list on already-correct inputs.

**Verification:** 191 tests passed, including 30 new cases for exact offset
reconstruction, Unicode, repeated text, insertion/deletion, invalid contracts,
raw rejected-output retention and mechanically accepted but incorrect grammar.
Ruff and uv lock consistency checks passed. Source evidence is retained under
evaluation/sentence_experiment; instructions and expected command output are in
docs/sentence_experiment.md. No commits or pushes were made.

**Next improvement checkpoints:** Review focused candidate failures; choose one
separately versioned development-only change addressing explanation reliability
or false correction, while preserving this baseline. Templates alone cannot fix
missed/incorrect edits. Keep zero unnecessary changes on correct inputs as a gate,
require improved useful coverage without a precision collapse, and leave held-out
inputs untouched until a candidate earns selection. Token alignment can split one
linguistic edit into several regions; do not force misleading TP/FP counts where
the prior scorer's one-to-one assumption does not apply.

## Milestone 2 — Smallest Working Component: Call the LLM

### 2026-09-30 — Separate explanation and justification pass

Implemented isolated `explanation_review.py` and `explanation_eval.py`. A second
Qwen3 4B call sees only original/proposed text and code-derived edits; prior
explanations and gold labels are not sent. It returns supported/unsupported with
an explanation. Frozen source proposals are never regenerated or rewritten.
Unsupported proposals would be withheld, with genuine errors still counted as
misses; model support is explicitly not independent semantic verification.
Protocol/source/prompt/schema/model identities were frozen before inference.

**Observed outcome:** All 60 source cases were accounted for: 29 unchanged cases
skipped, 31 review calls, all 31 supported, no withheld proposals and no unavailable
responses. It approved both the still-wrong row 57 and the unnecessary rewrite of
correct row 58. On row 58 it even acknowledged the original was grammatical.
The frozen zero-offered-changes-on-correct-inputs gate therefore fails again.
No repeated run was used to shop for a pass; this configuration is not selected
for app adoption or held-out validation.

Explanations also remain unreliable: definite/indefinite confusion on an, wrong
verb reasoning after did/should, and a wrong initial sound for chef. Several
outputs end unfinished. The model's supported label cannot establish that its
explanation is accurate or complete. A full human useful-feedback score remains
pending and is not necessary to establish the known gate failure.

**Measured cost:** Median extra review-call time 12.500 s; p95 15.112 s; maximum
23.772 s. These are second-pass times only. Do not claim a measured full pipeline
latency by adding timings from separate runs or including skipped zero-time cases
in the model-call median. No voice-latency improvement was demonstrated.

**Verification:** 216 tests passed, including 25 new tests for contract validation,
input isolation, skip/withhold accounting, source preservation and failure handling.
Ruff and dependency-lock checks passed. Source correction report hash matches the
frozen protocol. Evidence is under evaluation/explanation_experiment; learning
instructions and expected command output are in docs/explanation_experiment.md.
The live tutor, held-out set and model weights are unchanged; no Git actions made.

**Next improvement:** Test a small catalogue of human-reviewed rule explanations
with explicit applicability checks. Measure rule selection and coverage separately:
a correct template attached to the wrong edit still fails. Unsupported rules must
remain uncertain and missing corrections must not disappear from evaluation.
This approach is proposed only; no reviewed template catalogue has yet been
activated and no improvement is assumed before development-set measurement.

## Milestone 2 — Smallest Working Component: Call the LLM

### 2026-09-30 — Short, provisional rule explanations

Implemented an offline five-family explanation catalogue and deterministic
applicability checks in `rule_explanations.py`, with a saved-proposal replay in
`rule_explanation_eval.py`. Wording favors short, familiar language; one sentence
is not required. No model call is added. Unsupported edits are withheld without
claiming the original is correct. The live tutor remains unchanged.

**Observed:** Latest replay (`evaluation/rule_explanation_experiment/development_results_v2.json`)
offers 14 reference-matching corrections out of all 30 erroneous inputs, withholds
17 of 31 proposals, and leaves 29 unchanged proposals. Zero offers on 30 correct
inputs; both known bad proposals (57, 58) are withheld. Human applicability and
clarity judgments are still blank. Even a perfect review gives only 14/30 useful
coverage, below the earlier 17/30 baseline: not selected for app adoption or held-out
validation. The initial replay is preserved; v2 adds a noun-modifier guard without
changing development counts. Existing source inference evidence is unmodified.

**Intentional limits and untested risks:** Finite word lists and narrow contexts
miss many real errors. Rules are development-informed, not independently selected.
Matching text cannot prove grammatical correctness in quoted or unusual contexts.
Short wording alone does not prove learner understanding. There is no pronunciation
assessment and no measured full voice latency improvement; original inference
still takes time. No new dependencies or model training were introduced.

**Verification and optimization:** Tests cover five rule families with new phrases,
unknown words, style changes, extra edits, noun modifiers, invalid input, and all
60 cases remaining in the denominator. Next, human-review the 14 offers and check
whether learners understand “basic verb form” and “plural”. Add one rule family
with counterexamples, then measure useful coverage against all 30 errors and
false offers on all 30 correct inputs. Require improvement over 17/30 useful
feedback without introducing false corrections before considering held-out work.
See docs/rule_explanations.md for commands, expected output and a learning exercise.

Completed verification: 238 tests passed (22 new rule/replay tests); repository-wide
Ruff checks passed. No commits or pushes were performed.

## Milestone 2 — Smallest Working Component: Call the LLM

### 2026-09-30 — Human approval of 14 short explanations

The project owner approved all 14 displayed corrections and explanations with
“approve the 14”. Recorded case-level rule applicability, explanation clarity,
and useful-feedback approval in
`evaluation/rule_explanation_experiment/development_review_v2.json`, tied to the
unchanged replay report by SHA-256. This approval applies to these cases, not all
future rule matches or live app integration.

**Reviewed result:** 14/30 useful corrections (46.7%); 16 erroneous inputs remain
uncovered. All 14 offered corrections passed review; zero false offers occurred
on the 30 correct development inputs. Coverage remains below the earlier 17/30
useful-feedback baseline, so this candidate is not selected for app adoption.

**Next improvement:** Extend one bounded rule family, starting with
subject–verb agreement, and add new positive and adversarial examples before
replaying development cases. Review new offers, keep all 30 erroneous cases in
the denominator, and require improved useful coverage without false corrections.
No model calls, application changes, commits or pushes were made for this review.

## Milestone 2 — Smallest Working Component: Call the LLM

### 2026-09-30 — Bounded subject–verb agreement explanations

Added simple present-tense agreement for explicit person/verb lists and singular
“there is” clauses. Explanations are short; sentence count is not restricted.
Whole-clause matching and exact reconstruction prevent unrelated extra edits
from being covered by an agreement explanation. Quotes, compound subjects,
relative clauses and explicit past-time contexts are withheld. Excluded read→reads
because “read” can already express the past, even without an explicit time word.

**Observed:** Replay now offers 18 reference-matching corrections across all 30
erroneous cases, with 12 uncovered. No offers on the 30 correct inputs. The four new
cases address walk→walks, are→is, drive→drives and needs→need. Previous 14 approvals
carry forward only for exact original/proposed/rule/explanation matches; the four
new judgments remain pending. Thus confirmed useful feedback stays 14/30, with
18/30 potential if approved, versus the original 17/30 grammar-only baseline.
No app integration or held-out evaluation is authorized by these numbers alone.

**Limits:** This remains development-informed pattern matching with finite word
lists, not a grammar parser. Unknown words and complex clauses are intentionally
missed; unfamiliar context or additional errors can still defeat the checks.
Zero false offers on this sample is not evidence of zero errors generally. No new
model calls or voice-latency measurements were made. Both replay versions remain
saved; v2 removes the ambiguous read pair without changing development counts.

**Next improvement:** Review the four new offers, then challenge rule selection
with additional contexts before considering held-out validation. Keep all 30 error
cases in the denominator, retain concise wording, and require human-confirmed
useful coverage above 17/30 without false corrections. Evidence and review are
in evaluation/rule_explanation_experiment/ with agreement-specific filenames.

Completed verification: 259 tests passed, including 21 new agreement cases;
repository-wide Ruff checks passed after replacing re.I with re.IGNORECASE.
Final raw replay and carried-forward review use agreement_v3 filenames; earlier
artifacts remain preserved. The alias-only cleanup leaves behavior unchanged.
No Git staging, commits or pushes were performed.

## Milestone 2 — Smallest Working Component: Call the LLM

### 2026-09-30 — Four agreement judgments approved

Recorded the project owner's “APPROVE” for the four new agreement corrections
and explanations in agreement_review_approved.json, retaining the pending review
and raw replay unchanged. All 18 offered corrections now have human approval.
Confirmed useful feedback is 18/30 (60%), versus 17/30 (56.7%) for the original
grammar-only baseline; 12 erroneous inputs remain uncovered. There were zero
offers on the 30 correct development inputs. This is a small development-set
improvement, not evidence of general reliability or authorization to integrate.

Verified all 18 unique reviewed case IDs, all useful-feedback approvals, and the
unchanged source SHA-256. Next: test new challenging contexts for incorrect rule
selection before considering held-out validation or app integration. No model
calls, application edits, commits or pushes were made.

## Milestone 2 — Smallest Working Component: Call the LLM

### 2026-09-30 — Context challenges and narrower rule matching

Built a fixed 24-case engineering challenge set and reusable offline runner.
Before changes, 18/24 expectations passed. Six failures involved quoted language,
“since five years ago”, partial fractional/compound numbers, singular they, and
an unchecked second clause. Some were unsupported-scope or explanation failures,
not incorrect word replacements. Labels are assistant-authored engineering
expectations and have not been presented as user-approved grammar judgments.

Added guards for quotes and coordinated clauses, whole-number boundaries and
sentence-ending durations; removed ambiguous they from the multiple-person rule.
After changes, 24/24 challenges pass. Development replay retains all 18 approved
corrections (18/30 useful feedback) and zero offers on 30 correct inputs. Exact
input/proposal/rule/explanation comparison supports carrying forward all 18 user
approvals; no new semantic approvals were manufactured. Twelve errors remain
uncovered. Before/after reports, data/code hashes and review provenance are saved
under evaluation/rule_challenges. No model calls or application changes occurred.

**Observed tradeoff:** Broad guards intentionally reject useful cases as well,
including singular-they agreement, fractional quantities, contractions and quoted
or coordinated text. The original development score does not measure that lost
coverage. The challenge set guided the fixes, so passing it is regression evidence,
not independent validation. Other contextual failures remain possible.

**Next:** Freeze this candidate, establish a separate validation protocol and
review held-out labels before a single held-out evaluation. Count abstained errors
as misses, assess explanation correctness and latency, and avoid tuning on the
held-out results. No app integration until that evidence supports it. Verification
commands and expected outputs are in docs/rule_challenges.md.

Completed checks: 260 tests passed and repository-wide Ruff checks passed.
All 18 carried-forward review entries matched exactly. No commits or pushes made.

## Milestone 2 — Smallest Working Component: Call the LLM

### 2026-09-30 — Frozen candidate and validation label review

Preserved candidate rule, sentence-generation and client source, error definitions,
project dependencies and lockfile under evaluation/rule_validation/frozen with
verified SHA-256 identities. Prepared the existing 40 held-out labels (20 erroneous,
20 correct, shown as 20 pairs) for user review without running inference or changing
rules. protocol.json records model/settings, one attempt per case, output retention,
human-review metrics and gates before inference. Criteria were recorded after
reading draft labels; this is disclosed rather than called blind preregistration.

**Gates:** At least 12/20 human-useful corrections, zero offered changes on 20 correct
inputs, offered-correction precision at least 80%, and no unavailable results.
Withheld errors remain misses; reference matching alone cannot pass human review.
The 60% target is not a same-input comparison against the prior 17/30 development
baseline. Generation/check/total timings must be measured in the same run; they do
not prove two-second full voice latency. A pass does not automatically permit app
adoption. Failed validation must not trigger tuning followed by rebranding these
same cases as untouched held-out evidence.

**Limitations and next step:** Labels are still pending user approval; no held-out
model output or scores exist. Synthetic pairs are correlated and narrow, and known
finite vocabulary may generalize poorly. Review labels and intended meanings, then
implement and execute the frozen validation with all failures retained. Verified
40 unique IDs, 20/20 class balance, paired references and six matching frozen file
hashes. No app edits, model calls, commits or pushes were performed.

## Milestone 2 — Smallest Working Component: Call the LLM

### 2026-09-30 — Approved labels and failed held-out validation

Recorded user approval of all 40 labels in a separate hash-linked artifact.
Implemented and tested a single-attempt validation runner: verified frozen files,
labels and model digest, persisted started/completed attempts, retained raw outputs
and errors, and measured generation/rule/total processing in the same run. Existing
output blocks repeat execution. Candidate code and generation settings were not
changed during validation.

**Observed failure:** All 40 attempts completed without unavailable responses, but
only 1/20 erroneous inputs received a correction. Nineteen were withheld. Even if
human review approves that offer, maximum useful coverage is 5%, far below the
frozen 12/20 (60%) gate. Zero offers on 20 correct inputs does not compensate for
missing errors. Human output judgments remain pending; no semantic score was
invented. Candidate is not selected for integration. Evidence: heldout_results.json,
output_review.json, decision.json and results.md under evaluation/rule_validation.

**Latency:** Median generation-plus-rule time 3.543 s, p95 5.899 s, maximum/first
attempt 19.589 s. Excluding first attempt, median 3.537 s. This is text processing,
not a full voice measurement; it does not meet the desired two-second target.

**Lesson and next improvement:** Short fixed explanations avoid invented wording,
but finite word lists and restrictive context patterns generalize poorly. Redesign
rule detection using broader development vocabulary and grammar information, rather
than simply adding the failed held-out words. Retain this failed run. Any tuning
informed by these cases requires fresh independent validation inputs afterward.
No app integration, model training, commits or pushes were performed.

**Verification:** Full suite passed 267 tests before adding one final bookkeeping
test; all eight runner tests then passed. Active-code Ruff checks and uv lock checks
passed. Repository-wide lint initially reported a relocated-import sorting warning
inside immutable frozen source; active-code lint excludes that archive instead of
altering evidence. Commands and expected output are in docs/rule_validation.md.

## Milestone 2 — Smallest Working Component: Call the LLM

### 2026-10-01 — Broader grammar-rule detection with short explanations

**Active improvement: in progress.** Keep this focus until addressed or the user
explicitly changes direction. Latency work remains deferred.

Added an isolated LanguageTool-backed detector and evaluation runner. The already
installed local LanguageTool 6.6 supplies rule IDs, Unicode spans and suggestions;
short curated explanations replace its raw messages. A single supported replacement
must reconstruct the complete proposal exactly. This removes our learner-word
whitelist from this experimental path. Candidate code, rule source and server
identities were frozen before constructing fresh component cases. No candidate
changes were made after viewing those fresh results.

**Observed:** Saved development replay offers 20/30 corrections, versus 18/30 from
the previous filter, with zero offers on 30 correct inputs. This is offered coverage,
not a newly approved useful-feedback score. Fresh component tests recognize 13/16
intended corrections (81.25%) and withhold all 12 unwanted proposals: 25/28 checks
pass. Zero unavailable responses. New rule/explanation assignments await human
review. The fresh proposals were evaluator-authored, not LLM-generated; these
results do not establish whole-pipeline accuracy or independent expert review.

**Remaining failures:** DID_PAST is not mapped to an explanation; LanguageTool
returns no matches for “seven bottle” and “eight coin” in the new examples.
Catalogue limits and checker misses remain bottlenecks. Quoted/compound text,
multiple edits and ambiguous matches are intentionally withheld; other errors and
false explanations remain possible. No original held-out outputs were used here.
New dependency/model downloads, training and live-app changes were unnecessary.

**Same improvement, next actions:** Human-review the new explanations, investigate
DID_PAST and the plural misses using rule evidence instead of adding individual
words, then test the revised detector on additional fresh inputs. Keep the frozen
25/28 report and treat its cases as development evidence if they inform changes.
Do not switch to latency or integrate the app while this quality work is unresolved.

**Verification:** 280 tests passed, including 12 new mechanical detector tests.
Active-code Ruff passed with immutable prior snapshots excluded. Stored raw
checker responses, source hashes, pending review and results under
evaluation/broader_rules; commands and expected outputs are in
docs/broader_rules.md. No Git commits or pushes were performed.

## Milestone 2 — Smallest Working Component: Call the LLM

### 2026-10-01 — Explain the sentence-specific reason, not just the rule

User feedback: the prior explanations were correct but did not sufficiently show
why the proposed sentence makes sense. This refines the same active improvement:
broader rule detection with concise, useful explanations. It is not a change of
direction or evidence that coverage work is complete.

Added an isolated reason layer that connects the learner's actual words to the
rule: did already marks past time; a quantity means more than one; a duration
is a length of time; a comparative already expresses comparison. Fixed language
patterns are identified as conventions rather than given invented causal stories.
A second short sentence is allowed. The original detector and all archived reports
remain unchanged; the app does not use the experimental layer.

**Observed:** Replay across 60 development and 28 already-inspected component cases
preserved all 88 detection decisions, edits, rule IDs and selected match indices.
All 33 offers received a contextual draft. No model or checker calls were required.
Human accuracy, clarity and explains-why judgments for the new wording remain
pending. The user's acknowledgment of prior correctness is not a usefulness score
for this revision. Evidence and side-by-side wording are in
`evaluation/broader_rules/reasons_v1/`.

**Limits:** This improves wording, not grammar recognition. Wrong rule selection
can still yield a convincing but incorrect explanation. Short reasons still need
learner review, especially terms such as subject, tense and basic form. Three
coverage failures from the prior broader detector remain unresolved: DID_PAST
mapping and the two plural misses. No new independent validation is claimed.

**Next in the same improvement:** Review whether the new reasons teach why the
edit fits, then continue the three existing coverage gaps and test additional
fresh examples. Keep latency work deferred. Verification instructions and a
learning exercise are in docs/grammar_reasons.md. No commits or pushes performed.

Completed verification: 293 tests passed, including 13 new reasoning checks;
active-code Ruff passed with immutable archived snapshots excluded. Source hashes
match the wording replay. All 88 prior decisions remained unchanged.

## Milestone 2 — Smallest Working Component: Call the LLM

### 2026-10-01 — Deferred explanation refinement; address existing detection gaps

**User direction:** Revised reasons are better but still need work. Record further
clarity/teaching refinement for later iterations; do not let it displace the current
work on the three known detection gaps. This feedback is not blanket semantic
approval of future outputs. No explanation-style rewriting was done in this step.

**Implementation:** Added a versioned DID_PAST mapping and a separate experimental
LanguageTool XML count rule. Source rule IDs remain distinct in evidence. Existing
reason templates are reused through canonical rule mapping. The local tagger marked
bottle and coin as NN:UN; the installed CD_NN rule explicitly excludes this tag.
The new rule uses grammatical context and the installed plural synthesizer rather
than a noun whitelist: pronoun + verb + supported integer + singular noun at sentence
end. Mass-only nouns, plural readings and noun modifiers are withheld. Original
installed rules, frozen detectors and historical results remain unchanged.

**Observed:** All three known gaps now recognized. Prior component checks improve
from 25/28 to 28/28. Original 60-case development states are identical: 20 offers on
30 erroneous inputs, none on 30 correct inputs. A frozen follow-up candidate then
recognized 12/12 new intended corrections and withheld 16/16 counterexamples/scope
controls. No unavailable responses or new LLM calls. New rule applications remain
pending human review; component proposals were evaluator-authored, not LLM outputs.
The three gaps are addressed at component level, not proof of general reliability.

**Limits:** The added count rule covers a deliberately narrow sentence shape and
integer quantities (word forms two–twenty or digits 2–99). It excludes adjectives,
trailing phrases, fractions and many other constructions. Countability and tagging
can still be ambiguous. The custom rule currently runs in an offline Java batch;
it is not enabled in the live app/server. No training, new paid dependency or latency
optimization was introduced.

**Next within detection validation:** Human-review the new rule applications and
validate the combined LLM-plus-detector on additional untouched inputs before
integration. Preserve these now-inspected component cases. Later backlog: improve
explanations' sentence-specific reasons and accessibility with learner feedback;
no strict one-sentence requirement. Do not switch to that wording work unprompted.

**Verification:** 306 tests passed, including 13 new gap checks and real local Java
rule execution. Active-code Ruff passed. Frozen code/rule identities and all original
development states verified. Evidence is in evaluation/detection_gaps; commands,
expected output and learning checkpoints are in docs/detection_gaps.md. No commits
or pushes performed.

## Milestone 2 — Smallest Working Component: Call the LLM

### 2026-10-01 — Detection rule applications approved

Recorded the project owner's “approve” for all 15 displayed applications: the
three original gap fixes and 12 new component corrections. Correct-edit and
rule-applicability judgments are approved in
`evaluation/detection_gaps/review_approved.json`, linked to unchanged source reports
and the preserved pending review by hashes. There are no pending judgments among
these 15 applications. This does not convert component checks into an LLM score.

Explanation refinement remains a later-iteration item, as explicitly requested.
The app remains unchanged. Prepared targeted combined-flow validation in
`evaluation/detection_flow_validation/preparation.json`: 16 new error inputs and
16 correct inputs, reviewed labels before inference, one model attempt per case,
at least 13/16 human-useful corrections, zero changes to correct inputs and zero
unavailable results. Dataset and runner have not yet been created; no new model
output or quality score exists.

**Next:** Create and review the fresh validation inputs, then test actual model
proposals through the detector before considering integration. Preserve misses and
failures, and keep this detection-validation focus. Verified 15 unique approved
case IDs and unchanged evidence hashes. No model calls, commits or pushes made.

## Milestone 2 — Smallest Working Component: Call the LLM

### 2026-10-01 — Fresh combined-flow validation inputs prepared

Prepared 32 new standalone inputs: eight did-question errors, eight counted-noun
errors and sixteen acceptable inputs. Eight acceptable inputs are paired references;
eight exercise modifiers, unchanged plurals and mass nouns. All labels remain
pending user review. References and expected-error labels will be scoring-only,
never inputs to generation or rule selection.

Verified 32 unique normalized inputs and no collisions with sentence/reference
strings in 83 prior evaluation JSON artifacts (Unicode normalization, case folding,
whitespace normalization and terminal punctuation ignored). This establishes exact
sentence novelty, not statistical independence: grammar families and vocabulary
still overlap, and some new cases are paired. No new checker or model calls were
made. Candidate identities match the approved frozen detection version.

Recorded dataset hash, generation settings/model identity, candidate/dependency
hashes, alternating case order and existing gates in
`evaluation/detection_flow_validation/protocol.json`. Dataset and review table are
`labels_pending.json` and `label_review.md`; `novelty_check.json` preserves the
checked source identities. The gate remains at least 13/16 human-useful corrections,
zero offers on correct inputs and zero unavailable results. No test score exists.

**Next:** Review these labels, record approval against the exact draft, then build
and run the single-attempt combined-flow validation with raw evidence retained.
Do not change the detector to fit these cases. Explanation refinement and latency
optimization remain deferred. No app edits, commits or pushes performed.

## Milestone 2 — Smallest Working Component: Call the LLM

### 2026-10-01 — Complete frozen grammar-flow run on 32 approved inputs

Recorded the user's label confirmation and explicit “run it” authorization against
the frozen draft. Added a single-attempt runner that verifies candidate/model/label
identities, persists each started attempt and each completed stage, sends only the
learner text into inference, and refuses to overwrite a run. The candidate,
explanations, XML rules, model and settings were unchanged. The supplemental rule
ran once per input, so its real startup cost is included rather than hidden by a
batch average. No retries or replacement of model output with references occurred.

**Observed:** All 32 attempts completed. All 16 erroneous inputs received offered
corrections matching their approved references; all 16 acceptable inputs remained
unchanged. No withheld errors, unchanged errors, unavailable responses or automatic
mismatch flags. These are targeted edit/reference results, not a broad accuracy
claim. Human output judgments remain pending: the frozen threshold is 13/16 useful
corrections, including accurate explanations and preserved meaning. No final pass
or app integration has been declared from reference matching alone.

**Measured current cost:** Median generation 3.279 s; built-in checker 0.022 s;
supplemental Java checker 3.623 s. Measured complete grammar processing median
7.430 s, p95 10.400 s, maximum/first attempt 18.722 s. Median excluding first attempt
7.341 s. Stage medians must not be summed to infer a total. This excludes voice
capture, speech recognition and playback, and exceeds the two-second target.
Per-input Java process startup is material overhead. Latency optimization remains
deferred; no separate performance improvement was made in this quality-validation
step. Full automated checks ran after model evaluation to avoid their CPU workload
affecting the recorded cases.

**Verification:** 314 tests passed, including eight new runner checks. Active-code
Ruff and uv lock checks passed. All 32 IDs/order and completed states, frozen source
identities, runner identity and review/report hashes verified. Evidence is in
`evaluation/detection_flow_validation/results.json`, readable outcomes in results.md,
review fields in output_review.json and current status in decision.json. Setup and
verification instructions are in docs/detection_flow_validation.md.

**Next:** Review the actual offered edits/reasons and record useful-feedback
judgments against the frozen criteria before deciding on integration. Explanation
refinement remains an explicit later-iteration item. Synthetic targeted sentences
and paired references limit generalization; if these results guide changes, use
new untouched inputs for independent evaluation. No app edits, model training,
Git staging, commits or pushes were performed.

## Milestone 2 — Smallest Working Component: Call the LLM

### 2026-10-01 — Use direct number wording in plural explanations

**Observed limitation:** The user requested “‘Fifteen’ is more than one” instead
of “means more than one.” Applied that wording to the shared explicit-number
template and identified it as sentence-specific-reasons-v2. Subject-agreement
wording and correction selection are unchanged.

**Verification:** 21 focused tests and Ruff passed. Replaying the 32 saved model
proposals and checker outputs changed exactly E9–E16 explanation strings; every
other decision field stayed identical. The existing 88-case replay also preserved
all detection decisions. No model or checker inference was repeated. Historical
results, protocols and review judgments remain unchanged; the old reason source
is archived with its original hash. Frozen-candidate tests now verify that source
snapshot, while the original runner intentionally rejects changed working code.
Current wording is listed in evaluation/detection_flow_validation/wording_update.md.

**Limitations and next steps:** This is a requested wording refinement, not evidence
of improved detection or measured learner comprehension. Continue the pending
human usefulness review against the existing 13/16 threshold, recording revised
wording separately from original-run judgments. Broader explanation work and
latency optimization remain deferred. A future model evaluation needs its own
protocol; do not rewrite the completed run's frozen hashes. No app integration,
Git staging, commits or pushes were performed.

## Milestone 2 — Smallest Working Component: Call the LLM

### 2026-10-01 — Targeted detection validation approved and closed

The project owner approved all displayed judgments: 16/16 delivered error
corrections are useful, with necessary edits, preserved meaning and accurate
explanations; 16/16 acceptable inputs are preserved. The original number reasons
were accepted as accurate and the clearer “is more than one” wording was approved
separately. This approval applies to delivered rule-based explanations, not raw
model-generated reasons. Correct-input checks mark edit/explanation fields as
not applicable rather than counting them as corrective-feedback successes.

**Result:** All frozen targeted quality gates passed: useful feedback 16/16
(required 13/16), zero offers on acceptable inputs, and zero unavailable results.
No judgments remain pending for this run. Approved judgments are in
evaluation/detection_flow_validation/output_review_approved.json, linked by hashes
to unchanged source results and the preserved pending review. decision.json and
results.md now show the final outcome. The source run, labels and protocol were
not overwritten, and no new model or checker inference was performed.

**Observed limitations:** Complete grammar processing still takes a median
7.430 seconds. These 32 synthetic inputs cover only two targeted grammar families
and include paired references. This pass is not broad tutoring accuracy, a
measured learner-comprehension result, or validation of the two-second voice
target. Wider explanation refinement remains a later-iteration item.

**Next proposed improvement:** Prepare an opt-in app integration with the reviewed
grammar flow separate from conversation generation. Show the conversational reply
first and associate later grammar feedback with the confirmed learner text and
turn. Before adopting it, verify the reviewed corrections still work, acceptable
inputs remain unchanged, checker failure does not lose the conversational reply,
and stale feedback cannot attach to another turn. Measure time to first reply and
time to complete feedback separately; do not assume concurrency improves CPU
latency. Address per-input Java startup in a separately measured optimization if
needed. This proposal follows completion of detection validation; no integration
or performance change was implemented during approval recording.

**Verification:** Checked all 32 IDs and approved decisions against unchanged
source evidence, recomputed gate counts, verified eight separate wording approvals
and review/source hashes, and confirmed protected evidence files are byte-identical.
No Git staging, commits or pushes were performed.

## Milestone 2 — Smallest Working Component: Call the LLM

### 2026-10-01 — Optional reply-first grammar integration implemented

**What changed:** Added an opt-in Separate grammar feedback mode to the existing
Streamlit app. Qwen3 1.7B receives a conversation-only prompt and saved history;
the reviewed Qwen3 4B grammar flow independently receives only the learner's
confirmed text. The reply and pending job are saved atomically before the reply
is rendered and the grammar worker starts. Accepted rule explanations use the
approved number wording. The older combined mode remains available.

Background work has no Streamlit access. The UI polls local SQLite status; all
updates match the saved turn ID, job ID, session and original text. Failures retain
the reply, uncertain proposals are withheld, and interrupted jobs are not silently
retried. An additive grammar_jobs table stores per-turn status and separate timing;
existing history is preserved. No dependency or frozen detector changes were needed.

**Observed limitations:** The first real run exposed a conversation-prompt role
ambiguity, an unsupported promise to check later, and missing useful follow-ups.
That run and its prompt are preserved in docs/separate_feedback_smoke.json. A
bounded revision removed the opening task from the conversation prompt and
clarified tutor identity. A subsequent four-input smoke run used the revision.
It recalled Maya/hiking but still produced a yes/no follow-up and weakly grounded
praise. This is not evidence that conversational quality is solved.

Four revised-prompt turns measured reply generation of 1.36–2.33 seconds (median
1.58), grammar processing of 6.27–8.19 seconds (median 7.65), and feedback readiness
after handling Send of 8.00–10.53 seconds (median 9.05). These are server timings,
exclude voice input/output and browser paint, and do not establish the two-second
target. The initial run had a reply over six seconds; startup/steady-state timing
has not been controlled. Per-input Java startup still costs roughly 3.4–3.9 seconds
in the revised run. No performance claim is inferred from moving work to a thread.

**Intentional scope:** One Streamlit process, a single grammar worker, and one
pending check per conversation. Learners may draft while waiting, but Send and
Transcribe wait for grammar completion. Multiline grammar feedback is unsupported;
existing sentence/rule guards remain. This is not continuous phone-like dialogue.
The limited grammar benchmark does not establish broad-English tutoring quality.

**Verification:** 341 tests passed, including 27 new adapter/storage/UI checks.
All 32 reviewed decisions survived replay through the app adapter. Actual local
model tests delivered the expected two corrections, preserved two acceptable
inputs, displayed replies while grammar ran, and restored four completed turns
and feedback on refresh. Browser visual/accessibility inspection confirmed the
rendered results. Ruff and uv lock checks passed. Original benchmark sources and
frozen identities were verified unchanged. The real runs used a separate synthetic
database and are documented in docs/separate_grammar_feedback_validation.md;
verification commands, expected outputs and learning checkpoints are in
docs/separate_grammar_feedback.md.

**Next focused improvement:** Improve conversation-only grounding and useful
open-ended follow-ups against a small reviewed dialogue set. First record the
current prompt's direct-answer, fact-use, follow-up-relevance and level-fit failures;
then compare a bounded revision without changing the reviewed grammar flow.
Success requires relevant questions that invite descriptions or reasons, no
invented personal facts/promises, and preserved recall/direct answers. Latency
optimization (including reusable Java checking) and broader explanation refinement
remain queued. The integration work is complete; this next quality improvement
has not been implemented or declared successful. No commits or pushes performed.

## Milestone 2 — Smallest Working Component: Call the LLM

### 2026-10-05 — Joint conversational-quality and latency experiments

**Owner direction:** Keep both useful, grounded conversation and the two-second
response target. Do not trade either away or move to another improvement before
this one is addressed. Grammar-explanation refinement remains deferred.

**Implemented for evaluation:** Extracted versioned conversation prompts and
shared message/schema parsing without switching the app's baseline prompt. Added
controlled prompt comparisons, a bounded question selector and a short contextual
generation candidate. The selector chooses among authored invitations within
0.9 seconds. The contextual candidate has a 1.4-second generation budget and
falls back to an authored question on delay or detectable output problems.
Explicit controls handle stopping, limited recent-fact quotation and AI identity.
Raw rejected output and the response path remain visible in evaluation records.
These candidates are not yet integrated into Streamlit.

**Observed evidence:** The initial seven prompt/model profiles made 112 calls on
the same sixteen inputs; all returned valid JSON, but each retained material
quality failures. Qwen3 4B took median 3.81–5.97 seconds in its two configurations
and did not solve quality. These profiles remain preserved and unselected.

The bounded experiments use 32 development/challenge inputs, including those
sixteen earlier examples. With matching warm-up, all seventeen model selections
completed in 0.491–0.721 seconds; the other fifteen responses were deterministic.
Cold-start selection instead used seventeen fallbacks, with a maximum complete
text-response time of 0.909 seconds. The current contextual Qwen3 warm run used
fifteen generated replies, four fallbacks and thirteen deterministic replies;
its maximum text delay was 1.404 seconds. Its cold run used nineteen fallbacks
and thirteen deterministic replies, with no generated reply completed inside
the budget. These are repeated development cases, not independent successes.

**Observed limitations:** Two direct language questions remain unanswered in the
current Qwen3 run: explaining lend/borrow and clarifying the tutor's earlier
question. Their timeout fallbacks are quality failures despite fast delivery.
Other replies remain generic or omit useful details such as cooking/rice or a
train commute. Human review of naturalness, relevance and useful answers remains
pending; no semantic pass rate is claimed.

The first contextual candidate copied a learner's first-person statement into
the tutor's voice and passed the lexical filter. A later check rejects extra
sentences/first-person claims, and false rejections of self-introductions were
fixed. The preserved failure shows why vocabulary matching cannot prove meaning.
A shorter language-answer prompt reduced some delays but produced incomplete
definitions and a perspective error. It was not adopted.

Qwen2.5 1.5B was downloaded locally for a separate comparison (approximately
986 MB; Apache-2.0, with publisher/source links and exact digest recorded). It
generated only two accepted-format language answers, both substantively poor;
seventeen other requests fell back. It is unselected, and the app/grammar model
identities have not changed. No model training, paid service or dependency change
was introduced.

**Implementation lessons and evidence integrity:** An initial runner failed
while aggregating its first result; its started checkpoint and failure note are
preserved. The runner now saves each completed response before aggregation, with
a regression test for a deliberately failing summary. Another diagnostic found
2.56 seconds of model loading because preload used a different context size.
Warm-up now uses the actual options plus a real request. Historical source and
protocol revisions are preserved. One earlier contextual run overlapped the
regression suite; that CPU-load confound is explicitly recorded rather than
presented as a clean performance comparison.

**Intentional scope and untested risks:** Timing starts with confirmed text in
memory and excludes storage, UI, speech recognition, turn detection and spoken
playback. Readiness is recorded separately. The active app still blocks Send
while grammar is pending. The CPU cancellation tests prove client cancellation,
not prompt server-side termination or performance during live grammar workload.
Repeated requests against a cold model can remain on fallback; a readiness
phase must precede a claim about warm inference. Pattern-based recall has narrow
coverage and can miss complex changes in facts. No two-second voice claim or
general tutoring-quality claim is justified.

**Verification:** 388 tests passed in 16.91 seconds after the implementation
changes. Evaluators check prepared source/data/model identities and the approved
grammar flow. Actual replies, fallback counts, failure diagnostics and pending
review are in evaluation/conversation_quality/joint_results.md and
evaluation/conversation_quality/contextual_v2/review.md. The learning/verification
guide is docs/conversation_quality.md. No Git staging, commits or pushes occurred.

**Next focused improvement — unchanged objective:**

1. Review whether the current invitations are specific and natural enough;
   assess generated, deterministic and fallback replies separately. Keep the
   direct-answer failures visible, and do not turn missing answers into passes.
2. Address direct clarification and language questions without extending the
   deadline. Next design to evaluate: retain the intent and a plain-language
   explanation alongside authored questions, and use a small reviewed local
   reference source for language definitions/examples. These are proposed
   mechanisms, not installed features or proven solutions; test unfamiliar
   phrasing and unsupported questions rather than hardcoding the failed examples.
3. Require useful direct answers, preserved people/facts, relevant invitations
   and acceptable fallback behavior in new multi-turn conversations before app
   integration. Report every response over two seconds, all failures and model
   versus fallback rates. After quality passes, measure speech-end to first useful
   audio with grammar running; fast text alone cannot satisfy the final target.

**Decision:** Preserve the bounded mechanism as an experiment, with no replacement
selected. Both requirements remain active; this improvement is not complete.

## Milestone 2 — Smallest Working Component: Call the LLM

### 2026-10-06 — Natural follow-ups and correction-first text experiment

**Owner feedback and objective:** Replies should follow the actual person, food,
event and tense, without repeated “with an example/details” endings. Keep the
castle topic and AI identity; ask about rice, soup, journey duration, the departing
friend and the brother’s missed train. Unknown facts must name the relevant person
or relation. Supported corrections should appear first. Natural conversation and
the two-second response target both remain required; no change of improvement focus.

**Implemented for evaluation:** Added `natural_conversation.py` with narrow reusable
topic patterns and explicitly labeled authored fallbacks. Unknown relative-location
questions retain the relative and relation, and a newer job-change statement blocks
reuse of an old workplace. The short-generation prompt permits natural questions
without demanding examples or longer answers. Malformed response types fall back
safely, raw rejected text is retained, and a post-validation elapsed-time check
rejects generated output that arrived beyond the conversation budget.

Added `timely_corrections.py`, a separate resident-LanguageTool **rule-only** adapter
for DID_PAST and simple HE_VERB_AGR. Exact offsets, context, conflict checks and
subject/tense guards restrict offered edits. Conversation and this checker run
concurrently; a supported correction precedes the reply in `display_text`.
This does not alter or inherit the approval of the frozen LLM-plus-rule grammar
pipeline. The app remains on its existing conversation flow; this candidate is
not integrated or selected. No dependencies, model weights or Git history changed.

**C15 clarification:** The recorded sentence is “I take a short walk because it
helps me relax.” With no past cue, it is valid habitual present; take → took is
not a required correction. The candidate asks what about the walk helps relaxation.
A completed walk uses a past-tense question. The counterexample “Yesterday I take
a short walk” genuinely needs “took,” but is outside the fast adapter’s two rules.

**Observed evidence:** Four preserved revisions reused the same 41 inspected
cases: 32 prior development/challenge inputs plus nine structural counterexamples.
They are 164 attempts, not 164 independent validation examples. The latest v4
run completed 41/41 text replies under two seconds; maximum 0.939 s, nearest-rank
p95 0.824 s, with 0.439 s readiness reported separately. Paths were nine generated,
eight authored fallbacks and 24 authored deterministic replies. Both requested
D02 visited → visit and D12 go → goes appeared first, with approximately 0.035 s
and 0.034 s checker time. No checker was unavailable. The 39 absent fast offers
are not 39 claims of grammatical correctness. Human usefulness scores remain null.

v1 retained a weak yes/no rice question; v2 rejected it and improved hobby,
continuation and habit handling. v3 kept the soup dish rather than only its vegetable
modifier; v4 hardened malformed-output and over-budget handling. The final delivered
rice, soup and journey questions were authored fallbacks, not improved raw model
answers. Earlier raw results remain available for comparison. The original owner
review is partial (nine named IDs plus C09), not approval of the other 22 replies.

**Observed remaining failures:** C10/C13 still do not answer ordinary language and
clarification questions. N01/N06 reask supplied information. D01 assumes an unstated
bag; D15 presumes finishing despite the learner saying they could not finish.
D04/C05 retain generic recall follow-ups. Fast grammar intentionally misses plural
bottles and past-tense took. These failures prevent claiming natural conversation
is solved even though the measured text delay is low.

**Intentional scope and untested risks:** Topic word matching does not prove meaning
or factual grounding. Rule patterns cover limited syntax. The 1.4 s conversation
and 0.2 s checker deadlines are best-effort; synchronous work, scheduling and
cancellation can exceed them, and a smaller caller conversation budget does not
cap the checker. Client cancellation does not establish immediate server cancellation.
Timing excludes readiness, UI/DB work, STT, turn detection, TTS and the full grammar
pass. Warm text results cannot establish the two-second spoken goal. Full grammar
CPU contention, broader syntax and fresh multi-turn conversations remain untested.

**Verification:** 499 tests passed in 17.22 seconds, including 111 focused new
conversation/correction checks. Targeted Ruff checks passed. Prepared sources,
datasets, original review evidence and protected grammar identities were verified.
Evidence: `evaluation/conversation_quality/natural_v4/results.md`, all actual
responses in `review.md`, immutable raw results in `warm_results.json`, and pending
human judgments in `review_draft.json`. Learning steps and expected command outputs
are in `docs/natural_conversation.md`. No Git staging, commit or push occurred.

**Next focused improvement — same objective:**

1. Review the revised delivered responses while keeping generated and authored
   paths separate. Do not count pending judgments or merely fast fallbacks as passes.
2. Address invented premises, repeated information, generic recall and unanswered
   language/clarification questions within the same response budget. Preserve the
   topic-specific fixes and correct-versus-incorrect tense controls. Require useful
   direct answers, no known invented premises and no repeated answered questions
   across the current failures before advancing to fresh multi-turn cases.
3. Freeze a fresh conversation set before inference and review naturalness,
   grounding, follow-up relevance and every response over two seconds. Only then
   consider app integration and measure speech-end to useful audio under real
   grammar load. Broader explanation refinement remains deferred.

**Decision:** Useful targeted changes are recorded, but conversation quality plus
latency is still the active, unfinished improvement. No candidate is promoted.

## Milestone 2 — Smallest Working Component: Call the LLM

### 2026-10-06 — Plan unanswered follow-ups and supply bounded local explanations

**Same active objective:** Improve the remaining repeated questions, invented
premises, generic recall and unanswered tutoring questions without relaxing the
two-second target. The previous topic corrections remain preserved. Broader grammar
explanation refinement and app integration are not the focus of this iteration.

**Implemented experiment:** `dialogue_planner.py` separates limited known facts from
candidate question intents. Recognized packing, unfinished-action, future-meal,
past-walk and caught-transport patterns produce authored questions about information
not already supplied. A small Qwen3 request selects an index when several choices
remain; generation continues through natural-v4 for other inputs. Exact recent
questions and some already-answered intents are filtered before selection.
Model selection is recorded separately from model-written prose.

`learner_recall.py` quotes explicit learner-only name/hobby clauses from the last
four turns, including separate-turn facts, newer hobby changes and supported
retractions. `conversation_reference.py` gives authored lend/borrow and teach/learn
explanations and simplifies a small set of question intents using actual history.
Missing or ambiguous context receives a targeted request where supported. These
are bounded rules and a small catalog, not broad semantic memory or general English
question answering. The existing full grammar flow and model identities are unchanged.

**Observed targeted progress:** D01 no longer assumes an unstated bag; D15 preserves
the unfinished assignment and disappointment. D04/C05 ask about the recalled hobbies.
C10 now receives a direct lend/borrow explanation with an illustrative example;
C13 simplifies the actual prior question about playing games. N01 asks why the
learner chose rice rather than restating the future plan; N06 moves beyond the
already-stated relief. N05 asks about the walk without inventing scenery. Its
underlying take/took error remains outside the unchanged fast checker’s coverage.
These are assistant observations of actual delivered replies, not owner-approved
quality scores. Word-pair and other local answers are authored, not generated.

**Measured evidence:** The current candidate used 53 inspected development cases
(41 earlier plus 12 structural counterexamples). Two preserved revisions made
106 attempts, not 106 independent validation examples. Latest run: 53/53 complete
text responses within two seconds, maximum 1.000 s and nearest-rank p95 0.901 s.
Readiness was 1.130 s, recorded separately. Paths: four generated replies, nine
model-selected authored questions, 32 authored deterministic replies and eight
fallbacks. Two word-pair answers and five clarification replies are subsets of the
32 deterministic responses. Both D02/D12 supported corrections still appeared first;
no fast checker was unavailable. Missing offers are not claims of clean grammar.

**Observed implementation boundaries fixed:** Inspection and component checks
found that broader “do not ask questions” wording could produce an empty response,
and unrecognized explicit retractions could leave stale facts. The second revision
adds a nonempty acknowledgment and handles no-longer hobby retractions and negative
name statements. Dedicated tests cover both. Earlier v1 results/sources are retained.

**Remaining observed review concerns:** D08/C12 still use somewhat generic generated
questions. N07 remains on soup but does not explicitly acknowledge the dairy
restriction. X04’s question about events after catching the ferry needs a naturalness
judgment in context. All semantic scores remain pending; the new reference routes
remove the tested generic refusals but do not make arbitrary language questions
answerable. No candidate is promoted to the app.

**Intentional scope and untested risks:** This policy trades unrestricted generated
wording for bounded authored choices on recognized constructions. Incorrect
extraction can make every offered choice inappropriate. Exact-repeat filtering
cannot detect every repeated meaning, and the history heuristics are not general
fact verification. Complex retractions, unseen wording and long multi-turn dialogue
remain unverified. The 1.4 s conversation and 0.2 s checker timers are best-effort;
actual elapsed time, not configured budget, is the timing evidence. Cancellation
only establishes client behavior. UI, database, readiness, STT, turn detection, TTS
and full grammar CPU contention are excluded, so two-second spoken interaction
remains unproven. No new dependencies, paid services or model training were used.

**Verification:** 645 tests passed in 17.60 s, including 146 new focused checks.
Targeted Ruff checks passed. Prepared source/data identities, earlier frozen
candidate/evidence and protected grammar were verified. See
`evaluation/conversation_quality/planned_v2/results.md`, all 53 responses in
`review.md`, the pending `review_draft.json`, and `docs/dialogue_planning.md` for
learning steps, commands, expected output and what each check verifies.
No Git staging, commit or push occurred.

**Next improvement — unchanged focus:**

1. Review the revised replies and remaining generic/constraint-sensitive cases;
   keep authored, selected and generated paths distinct. Require relevant
   development of the learner’s statement without invented premises, ignored
   constraints or reasked information.
2. Improve D08/C12/N07 and clarify whether X04 is natural before freezing fresh
   multi-turn dialogues. Test changed facts, repeated topic answers and unsupported
   language questions; retain failures and report every response over two seconds.
3. Consider app integration only after quality review and fresh dialogue checks;
   then measure speech-end to useful audio with the full grammar workload. Both
   original requirements remain active; low text latency does not finish the work.

## Milestone 2 — Smallest Working Component: Call the LLM

### 2026-10-06 — planned_v3: acknowledge constraints and develop stated context

**Owner direction:** Continue the existing conversation-quality improvement. In
future Next improvement sections, state whether this is a good GitHub checkpoint
and whether to advance experiment versions such as v3/v4. Commits, tags and pushes
remain owner-managed. This preference is saved in AGENTS.md; experiment versions
must not be confused with stable app releases.

**Implemented:** `food_constraints.py` records explicit food restrictions and
preferences with the correct person, applies supported recent revisions and keeps
ability distinct from dislike. The dietary acknowledgment remains attached to the
response even when model selection times out. No ingredients, allergies, food
suitability, substitutions or preparation promises are inferred.

`contextual_followups.py` avoids reasking a stated cost reason or emotion. It
preserves habitual/future/completed travel and negated disappointment, and uses
explicit learner history to distinguish an upcoming interview from a completed
one. `dialogue_planner.py` integrates these helpers after stop/no-follow-up controls.
Exhausted authored choices become an acknowledgment rather than unrestricted
regeneration. The new wording is authored and selected by the model; other paths
remain distinct. The app and approved full grammar flow are unchanged.

**Observed targeted progress:** D08 now asks how the bus fits into the learner’s
day instead of asking again about its lower cost. C12 acknowledges an expected
result without inventing disappointment, then asks what the result means. N07
acknowledges inability to eat dairy before asking about ordering wording. X04 uses
the upcoming college interview and asks about the son’s study subject. New cases
preserve another person’s restriction, a revised person assignment, an already-stated
reason/duration, different people’s emotions and completed interview context.
These are assistant observations of actual outputs, not owner-approved quality scores.

**Verification and timing:** 703 tests passed in 18.40 seconds, including 58 added
checks. A single frozen planned_v3 run used 63 inspected development cases: 53 prior
cases plus ten new structural counterexamples. These are not held-out validation.
All 63 complete text replies were within two seconds: maximum 1.407 s, nearest-rank
p95 1.394 s, median 0.558 s. Readiness took 6.249 s and is reported separately.

Response paths were one generated reply, 21 model-selected authored questions,
31 authored deterministic replies and ten fallbacks. D10, Y03 and Y04 timed out;
the dietary prefixes still survived the two selector timeouts. Both D02/D12 supported
fast corrections remained first, and no checker was unavailable. Absent suggestions
are not claims of clean grammar. This different case mix/run is not a controlled
speed improvement over planned_v2. Raw attempts, prior evidence and frozen source
snapshots remain preserved; human quality judgments remain pending.

**Boundary defects found and fixed before freezing:** Explicit tomorrow travel
was initially classified as habitual; another person’s unfinished question could
become the learner’s work; a cancelled interview could leave stale upcoming context;
another relative’s study subject could suppress the wrong question; and mismatched
emotion/interview pronouns could imply attendance by the wrong person. Each now
has a targeted guard and regression test. Integration checks preserve controls and
prevent empty outputs when authored choices are exhausted.

**Remaining observed review concerns:** N07/Y01/Y02 ordering-wording prompts sound
like language exercises; the owner should judge whether they are conversational
enough. “Fit into your day” may be abstract for a beginner. Y06’s yes/no question
is relevant but does not guarantee a longer reply. Semantic pass rates remain unset.

**Scope limits and untested risks:** The explicit patterns and four-turn history
are not general semantic parsing. Unsupported later food clauses can conservatively
clear remembered constraints. Exact-repeat filtering can miss repeated meanings,
and a bare acknowledgment after exhausted choices can feel abrupt. Full multi-turn
conversation with actual generated/selected history remains unvalidated. Best-effort
budgets and client cancellation do not establish hard real-time or server-stop
behavior. Timing excludes readiness, UI/database work, STT, turn detection, TTS
and the full grammar workload; two-second spoken conversation remains unverified.
No model training, dependency changes, paid services or app promotion occurred.

**Evidence and learning:** `evaluation/conversation_quality/planned_v3/results.md`
compares the four targeted cases. `review.md` includes all 63 actual responses;
`review_draft.json` preserves pending judgments. The learning/verification guide is
`docs/constraint_followups.md`; user-managed checkpoint steps are in
`docs/github_checkpoints.md`. Targeted lint/format, source/data/model bindings and
protected grammar identities were verified. No Git history or publication operation
was performed, and GitHub remote publication was not verified.

**Next improvement — same objective and explicit checkpoint:**

1. Review these actual replies, especially exercise-like wording, abstract language
   and event flow. Keep selection, authored responses and generated prose distinct;
   do not turn timing success into a semantic pass.
2. After that review, freeze fresh multi-turn dialogues as **planned_v4**, using
   actual tutor outputs in subsequent history. Check constraints, learner revisions,
   clarification of the tutor’s own questions, natural progress and every response
   above two seconds before app integration. Remain on conversation quality/latency.
3. **GitHub checkpoint: yes**, after reviewing the complete accumulated source,
   dependencies, tests, docs and synthetic evidence. It is a useful tested
   experimental snapshot; many earlier files are untracked, so staging only the
   newest helpers would omit dependencies. The owner handles commit/push actions.
4. **Version guidance:** current experiment is planned_v3; planned_v4 is the next
   experiment after this checkpoint/review. This is **not** a stable app v3/v4
   release and does not change package 0.1.0. Preserve the existing local mvp-v1 tag.
   An optional distinct Git label such as conversation-planned-v3 is only a proposal.

## Milestone 2 — Smallest Working Component: Call the LLM

### 2026-10-06 — planned_v4: multi-turn continuity and optional Streamlit integration

**Owner priority:** Complete the bounded conversation experiments with the goal of
integrating a usable candidate into Streamlit. Once usable, integration takes priority
over another model/prompt refinement cycle or UI redesign. This direction is recorded
in local AGENTS.md; the original spoken two-second target remains active and unverified.

**Implemented:** `conversation_sessions_eval.py` evaluates six four-turn conversations
using actual tutor replies as subsequent history. It keeps only conversation text in
history, isolates sessions, excludes expectations from inference, and records failed
and skipped turns rather than inventing missing replies. The initial 24 replies were
preserved when summary processing raised `KeyError` for a missing status field; the
summary was repaired from saved rows without repeating inference. A regression test
now checks completion/failure denominators and retains failure latency.

`conversation_continuity.py` develops already-supplied reasons and durations, preserves
future/incomplete meals and cancelled interviews, and avoids assigning an ambiguous
relative's study subject. Food questions now concern food rather than requiring ordering
dialogue. Supported clarification requests simplify the question actually asked.
The candidate remains a bounded combination of authored replies, model-selected wording,
validated generation and recorded fallbacks, not unrestricted semantic understanding.

`planned_conversation.py` and the new **Context-aware conversation (experimental)**
checkbox integrate the candidate into the separate-grammar mode. The adapter verifies
the prepared local model, reads completed SQLite dialogue, and retains quick corrections
separately from conversational history. Additive `conversation_details` storage keeps
the engine, response path and correction provenance with the exact turn. Refresh restores
the mode and correction without inference. A model/service failure preserves the draft;
an unsaved reply does not start an unattached grammar job. The combined/default mode and
the reviewed full grammar function, sources, model identity and evidence are unchanged.

**Verification:** 731 tests passed in 22.84 s, covering real temporary SQLite, Streamlit
AppTest, model failures, correction-first display, refresh and historical grammar decisions.
Targeted lint and whitespace checks passed. Final multi-turn revision_2 completed 24/24
text responses within two seconds: maximum 1.408 s, p95 1.280 s. Paths were 17 authored
deterministic, six model-selected authored and one authored fallback; none was newly
generated prose. Readiness and the full app/grammar/audio workload are excluded here.

A separate live Streamlit AppTest run used real local services and eight synthetic turns
in a temporary database. All eight replies rendered in 0.131–1.504 s, all survived refresh,
and the fast `go → goes` correction appeared before its reply. Full grammar returned seven
no-proposal results and one supported correction, with no unavailable outcomes. It took
8.388–25.391 s to process; the next Send/Transcribe remained disabled. Three conversation
calls used recorded fallbacks under the full workload. These are Python UI measurements,
not browser paint times, actual microphone/STT performance or spoken conversation latency.

**Observed limitations:** Assistant review flags S02-T04's abrupt acknowledgment after
exhausting authored questions and S06-T02's generic fallback on timeout. The bus-preference
question may also invite repeating the known cost reason. The assistant considers 22/24
final development turns provisionally usable for an optional trial; every owner quality
judgment remains pending. This is not benchmark approval or a broad accuracy estimate.
New syntax, long conversations and natural learner replies outside the inspected cases
remain unvalidated. The full grammar wait prevents phone-like turn-taking, despite fast
reply display. UI integration does not resolve the earlier inaccurate-feedback limitation.

**Evidence:** `evaluation/conversation_quality/planned_v4/` retains initial, revision_1,
revision_2 and app integration protocols, source snapshots and raw outputs. Historical
protocols are unchanged; current integration explicitly pins new app/storage identities
while continuing to verify approved grammar identities. The smoke runner's later lint
cleanup is pinned separately in the app protocol. `review.md` shows every initial/final
reply with provisional assistant notes and pending owner fields. The learning guide is
`docs/conversation_integration.md`; no model training, new dependency or paid service
was introduced. No staging, commit, tag, push or remote verification was performed.

**Next improvement — prioritize the integrated product:**

1. Try the optional mode in Streamlit and review actual conversational usefulness,
   including the two flagged outputs. Keep this as planned_v4; do not start planned_v5
   or a UI redesign simply to defer in-app validation.
2. Fix concrete in-app continuation/fallback failures before further stylistic tuning.
   Preserve the full grammar behavior and track reply display separately from the time
   until another message can be sent. Any scheduling change needs new contention and
   turn-association checks before claiming continuous conversation.
3. **GitHub checkpoint:** useful after your in-app verification and file review.
   Local tags mvp-v1 and mvp-v2 were verified; mvp-v3 is the next optional sequential
   checkpoint. planned_v4 is an experiment, not an app v4 release. The owner handles
   Git actions; remote publication is not established by the local tag inspection.
