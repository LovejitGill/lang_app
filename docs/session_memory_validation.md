# Milestone 3 — Session memory validation

Verified 2026-09-22 on the existing local Ollama server. Two separate CLI
processes used session `milestone3-maya` and `data/milestone3_check.sqlite`.
The server was already running and was left running.

The second reply was “You are Maya and you enjoy hiking.” Inspection from a
third Python process found exactly two persisted turns, in chronological order.
This demonstrates local persistence and successful recall for this example; it
is not a guarantee of recall quality on arbitrary conversations.

All 55 automated tests passed, including an assertion that the second model
request contains the first learner/assistant pair, session isolation, bounded
history, failed-generation handling, and an actual SQLite write lock. Tests
use temporary databases and a fake model; the CLI check provides real inference
evidence separately.

The generated feedback remained inaccurate: the model unnecessarily changed
“enjoy hiking” to “like hiking,” then incorrectly criticized “my name” in the
recall question. These are unresolved Milestone 2 quality failures; memory
does not fix them. Old feedback is saved but not resent as prompt instructions.

## Actual stored turns

```json
[
  {
    "id": 1,
    "session_id": "milestone3-maya",
    "learner_text": "My name is Maya and I enjoy hiking.",
    "tutor_reply": "What kind of hiking do you like?",
    "created_at": "2026-09-23 00:25:39",
    "feedback": [
      "Change 'enjoy hiking' to 'like hiking'. Use 'like' with 'hiking' to match the verb form."
    ]
  },
  {
    "id": 2,
    "session_id": "milestone3-maya",
    "learner_text": "What is my name and what hobby did I mention?",
    "tutor_reply": "You are Maya and you enjoy hiking.",
    "created_at": "2026-09-23 00:25:46",
    "feedback": [
      "Change 'my name' to 'your name' for proper pronoun usage. 'Your name' is correct, but 'my name' is not appropriate here."
    ]
  }
]
```

The verification database contains only the synthetic examples shown above and
is excluded from Git. No UI, commit, push, or deployment was created.
