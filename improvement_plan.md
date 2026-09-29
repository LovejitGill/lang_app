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
