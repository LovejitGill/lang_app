# Milestone 4 — Streamlit UI validation

Verified on 2026-09-22 using the existing local Ollama server and a separate
`data/ui_verification.sqlite` database containing synthetic learner text.

- All 61 tests passed, including six new Streamlit AppTest cases.
- Ruff lint and formatting checks passed.
- Three real Qwen requests were submitted through Streamlit AppTest using the
  same app entry point and real SQLite persistence. All completed and the next
  turn counter reached 4.
- A browser opened the saved conversation URL. Visual inspection confirmed
  distinct learner/tutor displays and Language feedback labels.
- Browser reload restored the three turns, saved settings, and Turn #4.
- The final reply correctly recalled Maya and Saturdays. Model feedback remained
  inaccurate, including an unjustified correction of “on Saturdays.”

The three inference submissions used Streamlit's simulated UI test driver; the
rendering and refresh checks used the browser. This is not a claim that every
browser, keyboard/screen-reader behavior, or concurrent interaction was tested.

The verification Streamlit server was shut down afterward. The user's existing
Ollama server was left running. No code was committed or pushed.

## Actual generated exchanges

```json
[
  {
    "learner_text": "My name is Maya and I enjoy hiking.",
    "tutor_reply": "What kind of hiking do you enjoy?",
    "feedback": [
      "Change 'My name is Maya' to 'My name is Maya.' Articles like 'my' are normal and don't need correction."
    ],
    "saved": true
  },
  {
    "learner_text": "I usually hike on Saturdays.",
    "tutor_reply": "What days do you usually hike?",
    "feedback": [
      "Change 'on Saturdays' to 'on Saturday'. Use 'Saturday' without the 's' for singular form."
    ],
    "saved": true
  },
  {
    "learner_text": "What is my name and when do I usually hike?",
    "tutor_reply": "Your name is Maya, and you usually hike on Saturdays.",
    "feedback": [
      "Change 'my name' to 'your name' for proper pronouns."
    ],
    "saved": true
  }
]
```
