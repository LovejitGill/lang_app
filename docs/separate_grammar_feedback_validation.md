# Separate feedback integration — verification, 2026-10-01

The optional app integration is implemented. **341 automated tests passed**,
including **27 new tests** for the adapter, persistence and UI. Ruff and the uv
lock check passed. The 32 saved evaluation inputs retained their reviewed edits,
with the approved “is more than one” wording. Original benchmark source data and
frozen candidate hashes were verified unchanged.

## Actual local run

Four synthetic messages ran through Streamlit AppTest with real local Ollama and
LanguageTool. In every case the reply was rendered while grammar was still
running. The two erroneous inputs received the expected corrections; the two
acceptable inputs remained unchanged. Refresh restored all four turns and their
feedback. The saved conversation was then opened in the browser, where visual
and accessibility-tree inspection confirmed the option, turn separation,
corrections, timing labels and restored history. Microphone interaction was not
part of this run.

| Input | Reply generation | Grammar processing | Feedback ready after Send | Grammar result |
| --- | ---: | ---: | ---: | --- |
| I packed seven bottle. | 2.33 s | 8.19 s | 10.53 s | bottle → bottles |
| Did you visited the castle? | 1.43 s | 7.94 s | 9.37 s | visited → visit |
| My name is Maya and I enjoy hiking. | 1.72 s | 6.27 s | 8.00 s | No correction suggested |
| What is my name and what hobby did I mention? | 1.36 s | 7.36 s | 8.72 s | No correction suggested |

Median reply generation: **1.58 s**. Median grammar processing: **7.65 s**.
Median feedback readiness from handling Send: **9.05 s**. These are four
server-side observations, not a percentile benchmark or evidence that the
complete voice experience meets two seconds. The first reply in this run took
2.33 seconds. Browser rendering and up to about one second of polling are extra.
Models were already used before this run; this was not a controlled cold-start
experiment. Stage medians must not be added to infer total time.

Raw results and prompt/source identity are in `separate_feedback_smoke_v2.json`.

## Observed conversational limitations

The initial smoke run is preserved in `separate_feedback_smoke.json`. It showed
that the model sometimes answered the opening exercise as the learner, promised
to check facts later, or omitted a useful follow-up. A bounded prompt revision
removed the opening-task instruction from the conversation pass and explicitly
identified the model as the tutor. The subsequent four-input smoke run above used
that revision; it was an integration check, not a controlled quality comparison.

The revised prompt still produced weak conversation in places:

- For “I packed seven bottle.” it said “That's great! You're organized. What did
  you put in the bottle?” The singular follow-up and praise are weakly grounded.
- For “Did you visited the castle?” it said “I don't know. Have you been to the
  castle?” The yes/no follow-up does not encourage a longer learner response.
- It recalled Maya and hiking correctly when asked. That is one successful recall
  example, not a broad memory-quality score.

These are limitations of the conversational reply, separate from the accepted
rule-based grammar corrections. The original combined mode remains the default
for a new browser session. The new mode is opt-in; restoring a conversation whose
latest turn used it selects it again.

## Reliability evidence

Controlled UI tests pause the real background thread and verify that the reply
is visible while feedback is pending, duplicate display reruns do not repeat
inference, and Send remains disabled until the check finishes. Tests also cover
checker failure, an unsaved reply, an edited transcript, a new conversation while
an older result is pending, and interrupted jobs after server restart.

SQLite tests reject mismatched turn/job/session/text identities and duplicate
claims, and preserve replies on failed checks. Component tests replay all 32
approved outputs through the app adapter; no source proposals are changed to make
these checks pass. Model/HTTP errors and malformed output do not leak raw messages
or turn missing feedback into a correctness claim.

## Current scope and next improvement

The integration step is complete. It assumes one Streamlit process and one active
learner conversation. The next message can be drafted while grammar runs, but Send
and Transcribe wait for that conversation's pending check. Consequently this is
not yet continuous phone-like dialogue. Java startup remains repeated per check.

**Next improvement:** evaluate and improve conversational grounding and open-ended
follow-up questions using a small reviewed dialogue set, keeping the grammar
candidate fixed. Judge direct answers, use of known facts, relevant questions,
and encouragement of longer answers independently of grammar accuracy. Record
failures before changing prompts and compare against the current prompt; do not
make reference replies available to generation. Timing optimization and broader
grammar-explanation refinement stay queued behind that focused improvement.

The preview server uses a separate synthetic database at
`/tmp/speakwell-separate-feedback-ui.sqlite`; the user's default saved history was
not modified. No Git staging, commits or pushes were performed.
