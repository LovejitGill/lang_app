# Resolving the three detection gaps

DID_PAST was already detected by LanguageTool, but our explanation catalogue did
not recognize its name. A versioned adapter now connects it to the existing did
reason while preserving the original rule ID for review.

The two plural misses required more than adding names. Local tagger output shows
bottle and coin as NN:UN; the installed CD_NN rule excludes that tag. LanguageTool
uses NN:UN for nouns whose countable use depends on meaning, distinct from NN:U
for always-uncountable nouns ([official tag definitions](https://github.com/languagetool-org/languagetool/blob/master/languagetool-language-modules/en/src/main/resources/org/languagetool/resource/en/tagset.txt)).

`rules/en-speakwell.xml` adds one conservative pattern using grammatical tags:
pronoun + verb + integer quantity + singular noun ending the sentence. It asks
LanguageTool's existing synthesizer for the plural rather than adding an “s” or
keeping a noun list. It rejects mass-only tags, already-plural readings, proper
nouns and noun modifiers. XML patterns can match part-of-speech tags and generate
inflected suggestions using the engine's facilities ([rule-development documentation](https://dev.languagetool.org/development-overview.html)).

`grammar_gap_detector.py` combines this separate evidence with the original checker,
requires an exact proposal match, retains existing decisions, and reuses the
sentence-specific explanations. `grammar_gap_eval.py` records regressions and fresh
component checks. Earlier source and result snapshots remain intact. This is
symbolic rule engineering and evaluation, not machine-learning training.

## Verification steps

Run from the project directory. No paid services or new model downloads are needed.

1. `uv run python -m pytest tests/test_grammar_gaps.py -q`

   `uv run` uses the project environment; pytest normally runs automated behavior
   checks. Here it checks rule mapping, evidence provenance, Unicode offsets and
   one real local Java batch of positive and negative controls.

   Expected on this configured Mac: `13 passed`. Without the optional local Java/
   LanguageTool installation, the integration check is skipped; a skip does not
   verify the real rule. The remaining tests use synthetic evidence.

2. `uv run python grammar_gap_eval.py regression --output /tmp/speakwell-gap-regression.json`

   This replays existing proposals to check for regressions while executing the
   supplemental XML rule locally. Choose an unused output filename.

   Expected: `"cases": 88`, `"component_checks": 28`, `"component_passes": 28`,
   `"development_offers_on_errors": 20`, `"development_offers_on_correct": 0`.
   This verifies that the original three gaps are covered without losing earlier
   behavior; it is not a new human useful-feedback score.

3. Read `evaluation/detection_gaps/results.md` and `review.json` for the new outputs.
   The frozen candidate passed 12/12 new intended corrections and withheld all 16
   counterexamples. These were authored component proposals, not generated LLM replies.

To reproduce the component run, the installed server must be reachable at localhost
port 8081. If it is stopped, `bash scripts/languagetool.sh` starts that local server
in a separate terminal; expect startup logs mentioning port 8081.

`uv run python grammar_gap_eval.py fresh --output /tmp/speakwell-gap-components.json`
checks the frozen identities and replays those saved component inputs. This uses
local HTTP for built-in rules and one local Java CLI batch for the supplemental
rule. Expected: `"component_checks": 28`, `"component_passes": 28`,
`"unavailable": 0`, `"llm_calls": 0`.

The fresh-mode summary has zero development offers because this mode contains no
development cohort; that field is not a development-score measurement. Repeating
these same examples does not create independent validation.

## Learning checkpoint and scope

Explain why changing “fish” to “fishes” is not automatically right after a number,
and why “box” stays singular inside “box sets”. Inspect how noun tags and the end
of the noun phrase distinguish those cases from “seven bottle”. The added rule is
intentionally limited; unfamiliar contexts can still defeat grammatical tagging.

Explanation wording refinement is deferred to a later iteration per user direction.
The current detection gaps are addressed at component level. Next, review new rule
applications and test the combined model/detector on additional untouched inputs
before considering integration. The app is unchanged and no latency improvement
is claimed for this offline batch implementation.

## Approval update

The project owner approved the 15 displayed rule applications on 2026-10-01.
See review_approved.json. Next: prepare reviewed fresh inputs and run the complete
model-plus-detector validation. Component approvals do not establish that the LLM
will produce the same corrections. Explanation refinement stays deferred.
