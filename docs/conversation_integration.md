# Conversation continuity and optional Streamlit integration — planned_v4

The priority is now to bring a usable conversation candidate into the app, then
improve it through actual use. UI redesign and another open-ended model/prompt
experiment are deferred. The existing combined mode remains available, and the
reviewed full grammar checker is unchanged.

## What changed and what to learn

Earlier experiments supplied fixed history independently for each example. This
iteration uses **multi-turn evaluation**: each actual tutor reply becomes part of
the next turn's history. A plausible response to one sentence can still fail when
the learner answers its question. `conversation_sessions_eval.py` records that
history explicitly, isolates sessions, keeps the last four turns, and never sends
review expectations to the model. A failed turn stops dependent turns rather than
inventing the missing tutor reply. Every attempt is saved before summary processing.

`conversation_continuity.py` handles bounded cases where a reason or duration is
already supplied, a meal has not been prepared, or a relative's interview is
upcoming or cancelled. `food_constraints.py` asks about meals and accompaniments
instead of automatically turning food preferences into an ordering-language task.
`conversation_reference.py` simplifies supported questions the tutor actually asked.
These are authored conversation policies; model selection of wording is distinct
from newly generated prose. Unsupported syntax can still fall back poorly.

`planned_conversation.py` adapts this asynchronous candidate to Streamlit. It checks
the prepared local model identity and reads only learner text and conversational
replies from SQLite. Quick corrections stay separate from that history. The app
stores their provenance and the response path in an additive `conversation_details`
table, atomically with the reply and pending full-grammar job. Older rows need no
rewrite. Refresh restores the latest saved mode and the quick correction without
calling the model again. An unsaved reply remains visible with its existing warning.

The new mode is optional and requires **Separate grammar feedback (experimental)**.
Its limited quick checker can display a supported correction before the reply;
the approved full checker still runs afterward on the exact submitted text. The
quick checker supports only selected rule patterns, so an absent quick correction
does not mean correct grammar. Full grammar work still disables Send and Transcribe
until it finishes; the mode does not yet deliver phone-like continuous conversation.

## Usability gate and evidence

The prospective small-sample gate was at least 22 useful turns out of 24, no blocking
invented facts, wrong-person claims, stop violations, incorrect offered corrections
or repeated topic loops, and complete warm text within two seconds. This is an
engineering gate for an **optional in-app trial**, not validated educational accuracy.
Assistant judgments and owner approval remain separate. Stylistic perfection is not
required before integration; app failures now take priority over new experiments.

Six assistant-authored, inspected conversations cover introductions, food restrictions,
commuting, an interview, meal preparation, and fact recall/direct language questions.
These are development cases, not a held-out test or owner-approved references.
The same cases were rerun after fixes, with each version's sources/results retained.

- The initial run exposed repeated reasons, lost short answers and unclear references.
  All 24 raw replies survived a summary-only `KeyError`; `initial_summary.json` was
  derived from those saved replies without additional inference.
- Revision 1 improved continuity; revision 2 added simpler clarification of
  “Apart from ... what other meals ...?” The final 24 text replies were within two
  seconds, with a maximum of 1.408 s. Readiness and full grammar were excluded.
- The final response paths were 17 authored deterministic, six model-selected
  authored, and one authored fallback; none was newly generated prose in that run.
- Two final responses need further work: S02-T04 acknowledges a preference revision
  but gives no continuation; S06-T02 timed out into a generic relative follow-up.
  They remain flagged rather than being rerun until a preferred answer appears.
- 731 automated tests passed, including actual temporary SQLite and Streamlit
  AppTest checks for refresh, correction-first display, model failure, and unchanged
  approved full-grammar decisions. Automated wiring tests do not establish naturalness.

See [all before/after responses](../evaluation/conversation_quality/planned_v4/review.md),
the [decision](../evaluation/conversation_quality/planned_v4/decision.json), and the
[live app results](../evaluation/conversation_quality/planned_v4/app_integration/results.json).
The latter exercises real local models through Streamlit's Python testing interface,
not browser rendering, microphone capture, speech recognition or speech playback.
All eight app turns completed with refresh preserved and no unavailable grammar
result. Reply rendering took 0.131–1.504 s; full grammar processing took 8.388–25.391 s.
The next Send remained blocked by grammar. Three conversation selections/generations
used local fallbacks under that workload, so fast timing does not prove model generation
finished or that conversational quality is unchanged under full app load.

## Try the integrated mode

Use the existing running app, or follow the local service/startup commands in
[separate grammar feedback](separate_grammar_feedback.md). Do not launch duplicate
servers on occupied ports. In the app:

1. Start a conversation with your chosen level and scenario.
2. Enable **Separate grammar feedback (experimental)**, then enable
   **Context-aware conversation (experimental)**. Both should be checked. This
   selects the new candidate while retaining the existing full grammar pipeline.
3. Try `I take the bus to work because it costs less.` The reply should ask about
   the journey, not ask why you chose the bus again. Example output, variable:
   `How long does your bus journey take?`
4. Send `The journey takes twenty minutes.` Expect a relevant new aspect, such as
   `What do you like about travelling by bus?` It should not ask the duration again.
5. Send `What do you mean?` Expect a simpler version of the actual preceding question.
6. In a new conversation, try `She go to school by bus.` When the resident checker
   responds within its budget, expect **Quick correction**, `She goes to school by bus.`,
   an explanation, then a bus-related reply. Broader grammar feedback appears later.
7. Refresh after grammar finishes. The latest saved mode, replies and quick correction
   should remain. A new conversation should have no old turns. These checks verify
   UI routing and persistence; review the actual wording for usefulness.

## Repeat verification from the project directory

```bash
uv run --locked python -m pytest -q
```

`uv run --locked` uses the pinned project environment; `python -m pytest` normally
runs automated checks. Here it verifies existing behavior and the new integration.
Expected: `731 passed in ...s` (time varies).

```bash
uv run --locked python conversation_sessions_eval.py --directory evaluation/conversation_quality/planned_v4/app_integration --output /tmp/speakwell-conversation-review-01.json
```

This runs the six prepared conversations against the current frozen integration
identities, using actual previous replies. Benchmark scripts normally produce
repeatable evidence; choose an unused output filename to preserve earlier attempts.
Expected line shape: `S03-T02 complete ...s: ...`, with 24 completed rows in the JSON.
Wording and timings can vary; retain every fallback and response above two seconds.
Use the explicit directory: older protocols deliberately pin earlier sources.

```bash
uv run --locked python scripts/smoke_planned_conversation.py --output /tmp/speakwell-streamlit-review-01.json
```

This normally performs an integration smoke check; here it runs eight synthetic
turns through Streamlit AppTest with real local services and a temporary database.
Expected line shape: `UI1-T1 reply=...s rendered=...s grammar=...: ...`, followed by
eight completed rows and `refresh_verified: true` in the saved JSON. It takes longer
because it waits for full grammar after every reply; run with other benchmarks idle.
An unavailable grammar result is recorded, not counted as a successful grammar check.

Historical run protocols remain immutable. The integration protocol separately pins
the current UI/storage and lint-cleaned smoke runner; the approved grammar identities
cannot be overridden. No prior result was edited to match new code.

## Practice task and next improvement

Trace a confirmed learner message through `planned_conversation.conversation_reply`,
then `app.send_separate`, `feedback_store.save_reply`, and `app.render_turn`. Explain
why the saved `tutor_reply` excludes the quick correction and why refresh must not
resubmit inference. Try a different commute, relation or preference and note the
exact first turn where conversation loses continuity; do not rewrite the benchmark
references after seeing a model response.

**Next improvement:** review real in-app conversations, especially generic fallback
and exhausted follow-up choices, and fix those concrete failures before another
model comparison or UI redesign. Keep full-grammar waiting time and the original
two-second spoken target visible as separate unresolved work.

**GitHub checkpoint:** `mvp-v2` already exists locally. The integrated, tested candidate
is a useful checkpoint after your in-app verification and file review; a new tag may
be **mvp-v3**. `planned_v4` is the experiment name, not a Git tag or stable app v4
release. Do not start `planned_v5` merely to polish wording. Git actions remain yours.
