# Verify context checks

Run commands from the project directory. These checks use saved proposals and
make no model calls. The app is unchanged.

1. `uv run python -m pytest tests/test_rule_explanations.py -q`

   `uv run` uses the managed Python environment; pytest normally checks code
   behavior automatically. Here it verifies the rule tests and all context checks.

   Expected: `44 passed` (time varies). This verifies the declared engineering
   behavior, not general grammar accuracy.

2. `uv run python rule_challenge_eval.py --output /tmp/speakwell-context-check.json`

   This runs a fixed-case evaluation, commonly used to detect regressions after a
   change. Choose a new output filename if the file already exists.

   Expected: `"cases": 24`, `"passed": 24`, `"failed": 0`, `"model_calls": 0`.
   This confirms that the candidate handles the current challenge expectations.

3. `uv run python rule_explanation_eval.py --output /tmp/speakwell-context-development.json`

   This replays saved model answers to check the effect on development coverage.
   It preserves the original inference evidence and creates a separate report.

   Expected: `"provisional_offers": 18`, `"false_offers_on_correct_inputs": 0`,
   `"error_denominator": 30`. Raw `human_useful_feedback` remains null because
   human approvals live in the separate `evaluation/rule_challenges/development_review.json`.

Learning checkpoint: explain why “they” does not always mean multiple people,
and why blocking all quoted text can prevent both bad edits and useful edits.
The engineering fix trades some coverage for a narrower supported scope.

Next: define and freeze independent validation criteria before using held-out
cases. The challenge results are development evidence because fixes used them.
