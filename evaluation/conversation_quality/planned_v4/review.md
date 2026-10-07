# Actual multi-turn responses — planned_v4

All earlier tutor replies in a session are actual candidate outputs. This is inspected development evidence, not a held-out benchmark. Assistant usefulness judgments below are provisional; owner judgments remain pending.

The final run used 17 authored deterministic replies, six model-selected authored replies and one authored fallback. No newly generated prose survived in this run.

## S01 — Introduction, clarification, elaboration and recall

### S01-T01

**Learner:** My name is Nisha and I enjoy pottery.

**Expected behavior:** Ask a relevant question about pottery; do not invent details.

**Initial actual reply:** Tell me what interests you about pottery.

**Latest actual reply:** Tell me what interests you about pottery.

Path: `deterministic` · complete text: 0.079 s · rejection: `None`.

**Assistant review — provisionally_usable:** Relevant to the stated input/history; no blocking fact, correction or control failure observed in this reply.

**Owner review:** pending.

### S01-T02

**Learner:** What do you mean?

**Expected behavior:** Explain the actual previous question in easier English.

**Initial actual reply:** What makes pottery interesting to you?

**Latest actual reply:** What makes pottery interesting to you?

Path: `deterministic` · complete text: 0.070 s · rejection: `None`.

**Assistant review — provisionally_usable:** Relevant to the stated input/history; no blocking fact, correction or control failure observed in this reply.

**Owner review:** pending.

### S01-T03

**Learner:** I enjoy pottery because I can make useful things.

**Expected behavior:** Acknowledge the reason and develop the topic without asking that reason again.

**Initial actual reply:** Tell me what interests you about pottery because I can make useful things.

**Latest actual reply:** What else do you like about pottery?

Path: `model_selected` · complete text: 1.280 s · rejection: `None`.

**Assistant review — provisionally_usable:** Separates pottery from the supplied reason and asks for another aspect. Wording could still be more varied.

**Owner review:** pending.

### S01-T04

**Learner:** What is my name and what hobby did I mention? No follow-up.

**Expected behavior:** Recall Nisha and pottery from learner evidence; honor no follow-up.

**Initial actual reply:** You said: ‘My name is Nisha’ ‘I enjoy pottery.’

**Latest actual reply:** You said: ‘My name is Nisha’ ‘I enjoy pottery.’

Path: `deterministic` · complete text: 0.044 s · rejection: `None`.

**Assistant review — provisionally_usable:** Relevant to the stated input/history; no blocking fact, correction or control failure observed in this reply.

**Owner review:** pending.

## S02 — Food restriction, clarification, reason and revised preference

### S02-T01

**Learner:** I can't eat dairy and I would like lentil soup.

**Expected behavior:** Keep the dairy restriction; ask a natural question about this meal without inferring ingredients.

**Initial actual reply:** You can't eat dairy. How would you ask about dairy when ordering lentil soup?

**Latest actual reply:** You can't eat dairy. Apart from lentil soup, what other meals do you enjoy?

Path: `model_selected` · complete text: 0.241 s · rejection: `None`.

**Assistant review — provisionally_usable:** Preserves the dietary statement and asks about food. Authored meal wording, not a safety recommendation.

**Owner review:** pending.

### S02-T02

**Learner:** What do you mean?

**Expected behavior:** Clarify the actual prior question without changing the subject.

**Initial actual reply:** In ‘How would you ask about dairy when ordering lentil soup?’, which word or part would you like me to explain?

**Latest actual reply:** What other food do you like?

Path: `deterministic` · complete text: 0.044 s · rejection: `None`.

**Assistant review — provisionally_usable:** Relevant to the stated input/history; no blocking fact, correction or control failure observed in this reply.

**Owner review:** pending.

### S02-T03

**Learner:** I would like lentil soup because it is warm.

**Expected behavior:** Keep the restriction in context, do not ask why lentil soup was chosen again.

**Initial actual reply:** You can't eat dairy.

**Latest actual reply:** You can't eat dairy. What would you like to have with lentil soup?

Path: `deterministic` · complete text: 0.036 s · rejection: `None`.

**Assistant review — provisionally_usable:** Relevant to the stated input/history; no blocking fact, correction or control failure observed in this reply.

**Owner review:** pending.

### S02-T04

**Learner:** Actually, I can eat dairy now, but I don't like dairy. I would like lentil soup.

**Expected behavior:** Preserve permission versus dislike; do not claim inability or safe ingredients.

**Initial actual reply:** You can eat dairy. You don't like dairy.

**Latest actual reply:** You can eat dairy. You don't like dairy.

Path: `deterministic` · complete text: 0.045 s · rejection: `None`.

**Assistant review — needs_improvement:** The revised ability/preference is correctly acknowledged, but all authored questions are exhausted and the reply ends abruptly.

**Owner review:** pending.

## S03 — Commute, supplied duration, clarification and no-question control

### S03-T01

**Learner:** I take the bus to work because it costs less.

**Expected behavior:** Develop the bus commute without asking the already-stated cost reason.

**Initial actual reply:** Why do you think it's cheaper than other options?

**Latest actual reply:** How long does your bus journey take?

Path: `model_selected` · complete text: 1.161 s · rejection: `None`.

**Assistant review — provisionally_usable:** Relevant to the stated input/history; no blocking fact, correction or control failure observed in this reply.

**Owner review:** pending.

### S03-T02

**Learner:** The journey takes twenty minutes.

**Expected behavior:** Use the duration as an answer about the bus journey; do not reask duration.

**Initial actual reply:** Tell me a little more.

**Latest actual reply:** What do you like about travelling by bus?

Path: `model_selected` · complete text: 0.242 s · rejection: `None`.

**Assistant review — provisionally_usable:** Usable new question after the duration, but it may invite repetition of the earlier cost reason; owner review should consider whether it advances the conversation enough.

**Owner review:** pending.

### S03-T03

**Learner:** What do you mean?

**Expected behavior:** Explain the actual previous question simply.

**Initial actual reply:** I don't have that question here. Could you repeat it?

**Latest actual reply:** What makes travelling by bus good for you?

Path: `deterministic` · complete text: 0.042 s · rejection: `None`.

**Assistant review — provisionally_usable:** Simplifies the question actually asked. As above, the topic may invite repeating the cost reason.

**Owner review:** pending.

### S03-T04

**Learner:** Please don't ask another question.

**Expected behavior:** Acknowledge the request without a question or a command to elaborate.

**Initial actual reply:** Understood. I will leave out the follow-up question.

**Latest actual reply:** Understood. I will leave out the follow-up question.

Path: `deterministic` · complete text: 0.036 s · rejection: `None`.

**Assistant review — provisionally_usable:** Relevant to the stated input/history; no blocking fact, correction or control failure observed in this reply.

**Owner review:** pending.

## S04 — Relative, upcoming interview, subject and cancellation

### S04-T01

**Learner:** My daughter has an interview at a college tomorrow.

**Expected behavior:** Keep daughter and future timing; do not imply admission.

**Initial actual reply:** How are you feeling about the interview?

**Latest actual reply:** How does your daughter feel about the interview?

Path: `model_selected` · complete text: 0.354 s · rejection: `None`.

**Assistant review — provisionally_usable:** Relevant to the stated input/history; no blocking fact, correction or control failure observed in this reply.

**Owner review:** pending.

### S04-T02

**Learner:** My daughter is relieved because she caught her bus.

**Expected behavior:** Keep the daughter/interview context without implying arrival or admission.

**Initial actual reply:** What did your daughter do after catching the bus?

**Latest actual reply:** Your daughter feels relieved. How is your daughter preparing for the interview?

Path: `deterministic` · complete text: 0.057 s · rejection: `None`.

**Assistant review — provisionally_usable:** Relevant to the stated input/history; no blocking fact, correction or control failure observed in this reply.

**Owner review:** pending.

### S04-T03

**Learner:** She wants to study chemistry.

**Expected behavior:** Connect her stated subject to the same daughter without reasking it.

**Initial actual reply:** Tell me more about them and what happens.

**Latest actual reply:** Your daughter wants to study chemistry. What interests your daughter about chemistry?

Path: `deterministic` · complete text: 0.038 s · rejection: `None`.

**Assistant review — provisionally_usable:** Relevant to the stated input/history; no blocking fact, correction or control failure observed in this reply.

**Owner review:** pending.

### S04-T04

**Learner:** The interview was cancelled.

**Expected behavior:** Acknowledge cancellation; do not imply she attended or remains scheduled.

**Initial actual reply:** What did they say about the interview?

**Latest actual reply:** The interview is cancelled. What will happen now that the interview is cancelled?

Path: `deterministic` · complete text: 0.035 s · rejection: `None`.

**Assistant review — provisionally_usable:** Acknowledges cancellation without claiming attendance or admission. The repetition of cancelled is stylistic rather than a fact error.

**Owner review:** pending.

## S05 — Meal preparation, supplied reason, future event and stop

### S05-T01

**Learner:** I will cook noodles tomorrow.

**Expected behavior:** Ask about a future meal, not its completed taste.

**Initial actual reply:** What made you choose the noodles?

**Latest actual reply:** How will you prepare the noodles?

Path: `model_selected` · complete text: 0.226 s · rejection: `None`.

**Assistant review — provisionally_usable:** Relevant to the stated input/history; no blocking fact, correction or control failure observed in this reply.

**Owner review:** pending.

### S05-T02

**Learner:** I chose noodles because they are quick to make.

**Expected behavior:** Develop preparation or preference without repeating the given reason.

**Initial actual reply:** Describe what that is like.

**Latest actual reply:** What do you need to prepare the noodles?

Path: `deterministic` · complete text: 0.054 s · rejection: `None`.

**Assistant review — provisionally_usable:** Relevant to the stated input/history; no blocking fact, correction or control failure observed in this reply.

**Owner review:** pending.

### S05-T03

**Learner:** I have not cooked them yet.

**Expected behavior:** Honor the uncompleted meal and resolve them from context.

**Initial actual reply:** What will you do next?

**Latest actual reply:** You haven't cooked the noodles yet. Who will you cook the noodles with, if anyone?

Path: `deterministic` · complete text: 0.040 s · rejection: `None`.

**Assistant review — provisionally_usable:** Keeps the meal uncompleted and names the noodles. It does not assume the learner cooks with someone.

**Owner review:** pending.

### S05-T04

**Learner:** Thanks, that's enough practice for today.

**Expected behavior:** End without another question.

**Initial actual reply:** Thanks for practicing. Goodbye!

**Latest actual reply:** Thanks for practicing. Goodbye!

Path: `deterministic` · complete text: 0.039 s · rejection: `None`.

**Assistant review — provisionally_usable:** Relevant to the stated input/history; no blocking fact, correction or control failure observed in this reply.

**Owner review:** pending.

## S06 — Unknown fact, provided fact, recall and direct teaching

### S06-T01

**Learner:** Where does my cousin work?

**Expected behavior:** Admit the workplace is unknown; mention cousin or work.

**Initial actual reply:** I don't know where your cousin works. What kind of work does your cousin do?

**Latest actual reply:** I don't know where your cousin works. What kind of work does your cousin do?

Path: `deterministic` · complete text: 0.038 s · rejection: `None`.

**Assistant review — provisionally_usable:** Relevant to the stated input/history; no blocking fact, correction or control failure observed in this reply.

**Owner review:** pending.

### S06-T02

**Learner:** My cousin works at a bakery.

**Expected behavior:** Use the supplied workplace without inventing the cousin's role.

**Initial actual reply:** Does your cousin like working at the bakery?

**Latest actual reply:** Tell me more about them and what happens.

Path: `local_fallback` · complete text: 1.408 s · rejection: `TimeoutError`.

**Assistant review — needs_improvement:** Timeout delivered the generic fallback instead of developing the explicitly supplied bakery workplace.

**Owner review:** pending.

### S06-T03

**Learner:** Where does my cousin work? No follow-up.

**Expected behavior:** Answer bakery from learner history without a follow-up.

**Initial actual reply:** In our recent conversation, you said: ‘My cousin works at a bakery.’

**Latest actual reply:** In our recent conversation, you said: ‘My cousin works at a bakery.’

Path: `deterministic` · complete text: 0.082 s · rejection: `None`.

**Assistant review — provisionally_usable:** Relevant to the stated input/history; no blocking fact, correction or control failure observed in this reply.

**Owner review:** pending.

### S06-T04

**Learner:** Could you compare learn and teach?

**Expected behavior:** Explain both words correctly with an accessible example.

**Initial actual reply:** ‘Learn’ means gain knowledge or a skill. ‘Teach’ means help someone gain knowledge or a skill. Example: A teacher teaches English; a student learns English.

**Latest actual reply:** ‘Learn’ means gain knowledge or a skill. ‘Teach’ means help someone gain knowledge or a skill. Example: A teacher teaches English; a student learns English.

Path: `deterministic` · complete text: 0.058 s · rejection: `None`.

**Assistant review — provisionally_usable:** Relevant to the stated input/history; no blocking fact, correction or control failure observed in this reply.

**Owner review:** pending.
