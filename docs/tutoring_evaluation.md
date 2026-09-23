# Milestone 2 — Live tutoring evaluation

Verified on 2026-09-22 using the existing local Ollama 0.34.3 server,
Qwen3-1.7B, non-thinking mode, and the final prompt in `prompts.py`.
The existing server was not started or stopped by this milestone.

## Result

The component returns parsed reply/feedback data, supports practice settings,
and passes all 38 offline tests plus Ruff lint/format checks. Live outputs
demonstrate specific corrections for at least three different sentences:
Yesterday I go → went; She does not likes → does not like; and interested on
→ interested in. This meets the narrow single-turn implementation checkpoint.

**Tutoring quality is not reliable yet.** In the six-case final check, all
outputs were valid JSON, but all three correct sentences received unnecessary
feedback. The duration correction used the right word, “for,” but gave the
misleading explanation “Use for with since.” An additional test corrected
“I has” but introduced “does you” in the tutor reply. Another missed the
actual third-person agreement error in “He go to school every day.”

Do not count schema validity as correctness. These failures remain open
quality issues for prompt/model evaluation before presenting this as a
dependable tutor. No general accuracy percentage or latency claim is made.

## Prompt-development observations

The initial zero-example prompt produced a vague feedback item (“Don't like”),
an incorrect preposition suggestion (“interested about”), and a false
correction on a polite tea order. Adding examples, lowering temperature, and
clarifying no-correction behavior improved some corrections but did not solve
overcorrection. Test sentences used during tuning are not an independent
benchmark; new sentences are still needed for evaluation.

Next quality experiment: compare a shorter prompt and a larger local model
only if CPU latency permits, using a fixed set containing both correct and
incorrect sentences. Do not silently replace the selected model or hide
failed samples. SQLite memory is the next implementation milestone, not a
solution to these linguistic errors.

## Recorded outputs

The following are actual outputs, not examples of guaranteed behavior.

### Final six-case check

```json
[
  {
    "input": "Yesterday I go to the store.",
    "level": "beginner",
    "scenario": "daily activities",
    "output": {
      "reply": "What did you do at the store?",
      "feedback": [
        "Change 'go' to 'went'. Use went with yesterday in the past tense."
      ]
    }
  },
  {
    "input": "She does not likes coffee.",
    "level": "intermediate",
    "scenario": "daily activities",
    "output": {
      "reply": "What does she like instead of coffee?",
      "feedback": [
        "Change 'does not likes' to 'does not like'. Use 'like' with 'does' in the present tense."
      ]
    }
  },
  {
    "input": "I have lived here since three years.",
    "level": "advanced",
    "scenario": "introductions",
    "output": {
      "reply": "How have you been living here?",
      "feedback": [
        "Change 'lived here since three years' to 'lived here for three years'. Use 'for' with 'since' in this context."
      ]
    }
  },
  {
    "input": "I would like a cup of tea, please.",
    "level": "beginner",
    "scenario": "ordering food",
    "output": {
      "reply": "Of course! Would you like anything else?",
      "feedback": [
        "Change 'a cup of tea' to 'a cup of tea' (it's correct)."
      ]
    }
  },
  {
    "input": "My sister works at a library.",
    "level": "intermediate",
    "scenario": "introductions",
    "output": {
      "reply": "What does your sister do at the library?",
      "feedback": [
        "Change 'works' to 'works' (correct). No correction needed."
      ]
    }
  },
  {
    "input": "I went for a walk yesterday.",
    "level": "advanced",
    "scenario": "daily activities",
    "output": {
      "reply": "How did you feel during your walk?",
      "feedback": [
        "Change 'went for a walk' to 'went for a walk'. Use went with you in the past tense."
      ]
    }
  }
]
```

### Additional simple-sentence check

```json
[
  {
    "input": "I has a dog.",
    "output": {
      "reply": "What kind of dog does you have?",
      "feedback": [
        "Change 'I has' to 'I have'. Use have with I in the present tense."
      ]
    }
  },
  {
    "input": "He go to school every day.",
    "output": {
      "reply": "What does he do at school?",
      "feedback": [
        "Change 'go' to 'go to' for correct preposition usage. 'Go to school' is the correct phrase."
      ]
    }
  },
  {
    "input": "I am interested on music.",
    "output": {
      "reply": "What kind of music do you like?",
      "feedback": [
        "Change 'interested on' to 'interested in'. The correct phrase is 'interested in'."
      ]
    }
  }
]
```
