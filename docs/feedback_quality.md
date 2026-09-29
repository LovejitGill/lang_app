# Focused improvement — feedback evaluation

## Why this work comes before another prompt change

The tutor has repeatedly corrected valid English. Conversely, a prompt that
always returns empty feedback can appear safe while failing to teach. This
experiment measures both unnecessary corrections and useful error corrections.
It does not modify the model weights or train a model.

The dataset has 40 original sentences: 20 development cases used for comparison
and 20 held-out cases reserved for testing a selected candidate. Each half has
10 acceptable sentences and 10 with an expected error. Six historical failures
are stored separately as regressions. These are assistant-reviewed labels;
independent learner/instructor review remains pending.

`prompts.py` keeps the baseline and an explicit conservative experiment. The
existing `build_system_prompt(level, scenario)` interface still selects baseline.
Only the opt-in evaluator requests the candidate. The application's default is
not silently changed by running an experiment.

## Results and decision — 2026-09-24

The fixed development comparison made 40 live calls: each of 20 inputs received
one response from each variant. All parsed successfully; none required a format
retry. Assistant qualitative review is stored separately from raw results.

| Development measure | Baseline | Conservative |
|---|---:|---:|
| Acceptable inputs with unnecessary feedback | 10/10 | 0/10 |
| Erroneous inputs receiving explicit feedback | 10/10 | 0/10 |
| Useful corrections with accurate explanations and preserved meaning | 6/10 | 0/10 |
| Median measured call time | 5.299 s | 3.267 s |
| Maximum measured call time | 14.856 s | 6.084 s |

The baseline correctly replaced words in two additional cases but supplied a
misleading explanation: “for” expresses duration, not present tense; the base
verb after “can” is a modal rule, not a rule about “he” in present tense. These
are not counted as fully useful corrections. Two other target errors were missed
or wrongly corrected. Several unnecessary corrections proposed identical words
or phrases not present in the input.

The candidate produced empty feedback for every input. Silent rewrites such as
“She walks to work every morning” are not an explanation of the learner's error.
It also frequently omitted the requested follow-up, introduced unsupported
details, and produced comma splices in two replies. Its lower latency accompanies
less instructional output; this is not a like-for-like successful optimization.

**Decision: reject the candidate; keep the application default unchanged.**
Retaining the baseline does not endorse its accuracy. The shorter prompt did not
meet the development-selection criteria. The 20 held-out cases and their two-run
acceptance check remain reserved/unexecuted, not passed or silently dropped.
Running them now would consume the final check without an acceptable candidate.

The 12-call historical regression check showed the same pattern: baseline gave
false feedback on all four correct inputs and useful corrections on the two
incorrect inputs; candidate gave no explicit feedback on any. Its reply to the
Saturday routine also suggested adding “sometimes” unnecessarily. An empty
feedback array therefore does not guarantee that the conversational reply is
free of unsupported language advice.

Evidence:

- `evaluation/development_results.json`: exact responses, settings, model digest,
  prompt/dataset hashes, timing, and attempts.
- `evaluation/development_review.json`: separate assistant judgments for
  replacement, explanation, meaning, reply grammar, grounding, and elaboration.
- `evaluation/decision.json`: rejection recorded before held-out evaluation.
- `evaluation/regression_results.json`: outputs on historical failures.
- `evaluation/prompt_templates.json`: frozen templates for this experiment.

101 automated tests passed. These results are from one development comparison
and one regression comparison; no repeated-trial accuracy or p95 claim is made.
Hardware load/model loading were uncontrolled. The two-second end-to-end target
and multilingual/phonetic assessment are outside this text-only experiment.

## Code-reading order

1. `evaluation/README.md`: evaluation rules and acceptance targets.
2. `evaluation/development.json`: inputs and expected judgments, outside prompts.
3. `prompts.py`: compare the two templates. The candidate is shorter, emphasizes
   clear errors, preserves speaker meaning, and avoids stylistic rewrites.
4. `quality_eval.py`: model metadata → independent cases → real parser/retries →
   persisted outputs and timing. Labels are never sent to the model.
5. The experiment's results and review files under `evaluation/`.

**Held out** means not used to make prompt-selection decisions. Do not repeatedly
adjust a prompt against these examples and continue calling them unseen.

## Verification commands

```bash
cd /Users/lovejit/PerScholas/AI_Solutions_dev/CAPSTONE/AI_Dev_CAPSTONE/lang_app
```

**Purpose/typical use:** Selects the project folder before running its tools.
**Expected:** No output on success.

```bash
uv run --locked python -m pytest -q
```

**Purpose/typical use:** Runs regression tests after changes using the project's
locked dependencies. **Expected:** `101 passed in ...`; no live LLM is required.
These tests check experiment integrity and app behavior, not linguistic truth.

Keep the existing Ollama server running, then optionally repeat the comparison:

```bash
uv run --locked python quality_eval.py --split development --variants baseline conservative --output .tools/quality-development-repeat.json
```

**Purpose/typical use:** Compares the two prompts on the same development inputs
with the local model; use when reviewing prompt experiments.
**Expected, variable:** `run=1 development-01 baseline: ...s completed`, followed
by 39 more attempts and a summary. Existing output filenames are rejected so
earlier evidence cannot be accidentally overwritten. A repeat needs a new name.

The summary distinguishes acceptable inputs receiving feedback from erroneous
inputs receiving feedback. Neither feedback presence nor valid JSON establishes
that a correction is useful. Check the actual outputs and review them yourself.
Latency includes generation and any format retry, not speech, UI, or human review.

```bash
uv run --locked python quality_eval.py --split regression --variants baseline conservative --output .tools/quality-regression-repeat.json
```

**Purpose/typical use:** Rechecks six previously observed failures against both
prompts to detect regressions. **Expected, variable:** 12 completed/error attempt
lines and a summary. These familiar cases cannot establish held-out accuracy.

## Learning task

TODO: Independently score five development cases. Mark the replacement,
explanation, preserved meaning, grammar of the tutor's own reply, and whether
the reply invites relevant elaboration. Explain why a silent rewrite in the
reply does not replace explicit corrective feedback.

Use the saved prompt/dataset hashes and model digest when comparing results.
Keep missed errors, false corrections, invalid outputs, and slow calls visible.
Change only one experimental configuration at a time, and record unsuccessful
experiments as evidence rather than hiding them.
