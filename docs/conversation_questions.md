# Open-ended conversation checks — 2026-09-22

The UI now selects one of nine authored opening tasks by scenario and level.
The same task is included in the system prompt so the model can interpret the
learner's answer. Beginners receive sentence starters; generated replies are
instructed to invite one description, experience, or explanation.

## Automated evidence

71 tests passed; Ruff checks passed. Added checks cover all nine starter/settings
combinations and verify that displaying a starter neither calls the model nor
inserts a conversation turn. These checks do not establish language quality.

## Live evidence

Three independent, stateless calls to local `qwen3:1.7b` with the updated prompt:

| Level/scenario | Input | Actual reply | Human assessment |
|---|---|---|---|
| Beginner / introductions | Hiking. | Tell me about a hike you enjoyed. You can begin: 'I went to…' | Invites an experience using simple language; useful expansion of a one-word answer. |
| Intermediate / daily activities | Yesterday I worked late because we had an important deadline. | Tell me about a time when you had to work late. What made it different from your usual routine? | Invites elaboration, but asks for an experience already supplied rather than directly developing it. |
| Advanced / ordering food | I would choose a vegetable curry because two of my friends are vegetarian. | Tell me about a meal you'd like to eat with your friends. You can begin: 'I'd like to eat...' | Broad invitation, but repeats the meal-selection task and provides beginner-like scaffolding. |

The last two cases also returned inaccurate feedback:

- `Change 'worked' to 'worked' (correct). Use 'worked' with 'did' in the past tense.`
- `Change 'choose' to 'pick'. Use pick with a noun in this context.`

Neither correction is justified. These observations confirm the earlier
inaccurate-feedback limitation remains unresolved. Three samples are not a
reliable estimate of overall model quality, and no latency claim follows.

## Next evaluation exercise

Create ten short multi-turn scripts across the three scenarios. For each reply,
mark whether it invites elaboration, builds on a supplied detail, avoids asking
for known information, has one focus, and suits the level. Aim for at least 90%
on each criterion before claiming reliable follow-ups. Separately review a
balanced set of 20 correct and 20 incorrect learner sentences; report false
corrections and missed errors rather than mixing them into conversation scores.
