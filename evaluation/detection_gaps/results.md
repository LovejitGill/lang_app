# Detection gaps addressed — component evidence

The project owner approved all 15 displayed rule applications on 2026-10-01: the three original fixes and 12 fresh component corrections. Approval is recorded in review_approved.json; the original pending review is preserved. The three known misses now receive matching rule evidence. Explanation wording was reused; further wording refinement is deliberately deferred at the user’s request.

| Check | Result |
| --- | --- |
| Original three gaps | 3/3 recognized |
| Prior component checks | 28/28, previously 25/28 |
| New intended corrections | 12/12 recognized |
| New counterexamples / scope controls | 16/16 withheld |
| Original development offers | 20/30 errors; 0/30 correct inputs, unchanged |
| New LLM calls | 0 |
| Automated tests | 306 passed |

## The original gaps

| Input | Proposed sentence | Evidence | Explanation |
| --- | --- | --- | --- |
| Did you visited the castle? | Did you visit the castle? | DID_PAST | ‘Did’ already marks the past, so use ‘visit’, not ‘visited’. |
| I packed seven bottle. | I packed seven bottles. | SPEAKWELL_COUNT_HEAD | ‘Seven’ means more than one, so use the plural ‘bottles’. |
| We found eight coin. | We found eight coins. | SPEAKWELL_COUNT_HEAD | ‘Eight’ means more than one, so use the plural ‘coins’. |

## New positive cases — approved

| Input | Proposed sentence | Evidence source | Explanation |
| --- | --- | --- | --- |
| Did Maria mailed the parcel? | Did Maria mail the parcel? | DID_PAST | ‘Did’ already marks the past, so use ‘mail’, not ‘mailed’. |
| Did they opened the gate? | Did they open the gate? | DID_PAST | ‘Did’ already marks the past, so use ‘open’, not ‘opened’. |
| Did your assistant sent the invoice? | Did your assistant send the invoice? | DID_PAST | ‘Did’ already marks the past, so use ‘send’, not ‘sent’. |
| We collected six pebble. | We collected six pebbles. | CD_NN | ‘Six’ means more than one, so use the plural ‘pebbles’. |
| I bought four onion. | I bought four onions. | SPEAKWELL_COUNT_HEAD | ‘Four’ means more than one, so use the plural ‘onions’. |
| They found nine shell. | They found nine shells. | SPEAKWELL_COUNT_HEAD | ‘Nine’ means more than one, so use the plural ‘shells’. |
| We printed twelve label. | We printed twelve labels. | CD_NN | ‘Twelve’ means more than one, so use the plural ‘labels’. |
| I packed five knife. | I packed five knives. | CD_NN | ‘Five’ means more than one, so use the plural ‘knives’. |
| We saw three child. | We saw three children. | CD_NN | ‘Three’ means more than one, so use the plural ‘children’. |
| I counted eleven leaf. | I counted eleven leaves. | CD_NN | ‘Eleven’ means more than one, so use the plural ‘leaves’. |
| They purchased 24 candle. | They purchased 24 candles. | CD_NN | ‘24’ means more than one, so use the plural ‘candles’. |
| We collected four stamp. | We collected four stamps. | CD_NN | ‘Four’ means more than one, so use the plural ‘stamps’. |

## Root cause and change

DID_PAST already supplied the correct replacement; it lacked an explanation mapping. The new adapter maps its semantics to the existing do/did explanation while retaining DID_PAST as the recorded source.

Local tagger output marks bottle and coin as NN:UN. The installed CD_NN rule explicitly excludes NN:UN, even in these counted-object examples. The additional XML rule uses the installed noun tags and plural synthesizer. It requires a simple pronoun + verb + integer + singular noun + sentence end pattern, and rejects mass-only tags, already-plural readings and proper nouns. There is no noun lookup table. The original LanguageTool installation and frozen Python detectors are unmodified.

## Limits and next step

The new rule covers a narrow sentence shape: adjacent integer quantities (number words two–twenty or digits 2–99), no adjectives or trailing phrases. It does not solve every count/mass ambiguity. Human rule review is complete for the displayed cases; authored proposed corrections were supplied for component tests. No end-to-end LLM accuracy or voice latency claim follows. The custom rule currently runs as an offline Java batch, not as a configured live server rule.

These three detection gaps are addressed at component level. Next, validate the combined LLM-plus-detector flow using additional untouched inputs before app integration. Explanation clarity remains a recorded later-iteration item. No application edits, model training, commits or pushes were made.
