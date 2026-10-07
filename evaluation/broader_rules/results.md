# Broader grammar-rule detection — experimental

**Active improvement remains broader rule detection with short explanations.** No app integration or new LLM inference.

| Measure | Result |
| --- | --- |
| Development offers on erroneous inputs | 20/30 (previous word filter: 18/30) |
| Development offers on correct inputs | 0/30 |
| Fresh intended corrections recognized | 13/16 (81.25%) |
| Fresh unwanted changes withheld | 12/12 |
| Fresh component checks passing | 25/28 |
| New human useful-feedback score | Pending |

Development coverage counts proposals, not approved useful feedback. The cohorts have different purposes and must not be combined into one accuracy score. Fresh tests supplied proposed corrections; they did not test whether the LLM would generate them.

## Fresh explanations for review

| Input | Proposed sentence | Short explanation |
| --- | --- | --- |
| We should explores the cave. | We should explore the cave. | After words like ‘can’ or ‘should’, use the basic verb form. |
| He can repairs the bicycle. | He can repair the bicycle. | After words like ‘can’ or ‘should’, use the basic verb form. |
| She might dances tonight. | She might dance tonight. | After words like ‘can’ or ‘should’, use the basic verb form. |
| He does not calls often. | He does not call often. | After ‘do’, ‘does’, or ‘did’, use the basic verb form. |
| This lamp is more brighter. | This lamp is brighter. | Use ‘brighter’ without ‘more’ when comparing. |
| She is a honest person. | She is an honest person. | Use ‘an’ before a vowel sound. |
| He wears an uniform. | He wears a uniform. | Use ‘a’ before a consonant sound. |
| I enjoy to sketch. | I enjoy sketching. | After ‘enjoy’, use the ‘-ing’ form. |
| The kittens needs water. | The kittens need water. | Use the basic verb form with a plural subject. |
| She bake bread. | She bakes bread. | With ‘she’, use ‘bakes’ in the present tense. |
| We have worked here since six weeks. | We have worked here for six weeks. | Use ‘for’ to say how long something lasts. |
| It depends of the weather. | It depends on the weather. | Use ‘depend on’ when something relies on something else. |
| There are a lamp near the window. | There is a lamp near the window. | Use ‘there is’ for one thing. |

## Remaining gaps

| Input | Proposed correction | Observed reason for withholding |
| --- | --- | --- |
| Did you visited the castle? | Did you visit the castle? | Checker reports DID_PAST; catalogue does not map this rule yet. |
| I packed seven bottle. | I packed seven bottles. | Local checker returns no matches. |
| We found eight coin. | We found eight coins. | Local checker returns no matches. |

The frozen candidate was not changed after these results. These cases can guide the next revision, but then become development cases for that revision. Use additional untouched examples for later validation.

## Development offers for review

| Input | Proposed sentence | Short explanation |
| --- | --- | --- |
| She walk to work every morning. | She walks to work every morning. | With ‘she’, use ‘walks’ in the present tense. |
| I would like two sandwich, please. | I would like two sandwiches, please. | Use a plural noun for more than one item. |
| This restaurant is more cheaper than the cafe. | This restaurant is cheaper than the cafe. | Use ‘cheaper’ without ‘more’ when comparing. |
| I have lived here since five years. | I have lived here for five years. | Use ‘for’ to say how long something lasts. |
| He can speaks Spanish. | He can speak Spanish. | After words like ‘can’ or ‘should’, use the basic verb form. |
| There are a bowl on the table. | There is a bowl on the table. | Use ‘there is’ for one thing. |
| I did not ordered dessert. | I did not order dessert. | After ‘do’, ‘does’, or ‘did’, use the basic verb form. |
| The students needs more time. | The students need more time. | Use the basic verb form with a plural subject. |
| He is an chef. | He is a chef. | Use ‘a’ before a consonant sound. |
| We saw a elephant. | We saw an elephant. | Use ‘an’ before a vowel sound. |
| I packed four shirt. | I packed four shirts. | Use a plural noun for more than one item. |
| You should takes a break. | You should take a break. | After words like ‘can’ or ‘should’, use the basic verb form. |
| They might arrives early. | They might arrive early. | After words like ‘can’ or ‘should’, use the basic verb form. |
| Does she likes tea? | Does she like tea? | After ‘do’, ‘does’, or ‘did’, use the basic verb form. |
| He did not wrote the note. | He did not write the note. | After ‘do’, ‘does’, or ‘did’, use the basic verb form. |
| This route is more shorter. | This route is shorter. | Use ‘shorter’ without ‘more’ when comparing. |
| Today is more colder than Monday. | Today is colder than Monday. | Use ‘colder’ without ‘more’ when comparing. |
| She has worked here since two months. | She has worked here for two months. | Use ‘for’ to say how long something lasts. |
| They depend of public transport. | They depend on public transport. | Use ‘depend on’ when something relies on something else. |
| I enjoy to swim. | I enjoy swimming. | After ‘enjoy’, use the ‘-ing’ form. |

## Interpretation and next work

The detector now relies on local LanguageTool rule IDs, grammatical analysis and suggestions instead of a custom learner-word list. An exact whole-sentence replacement is required. Curated explanations still cover only selected rule IDs, one matched edit and restricted contexts. Two agreeing tools can still be wrong; template selection and learner clarity require human review.

The evidence supports broader vocabulary coverage, not production readiness or general language accuracy. No latency optimization was attempted and no two-second voice claim is made.

Next within this same improvement: review these explanations; investigate the missing DID_PAST mapping and noun-plural detections without inserting the failed words into a custom list. Validate the next revision on additional fresh examples. Active status: in progress.
