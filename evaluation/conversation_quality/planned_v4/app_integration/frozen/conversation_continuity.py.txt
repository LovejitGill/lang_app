"""Bounded continuations for reasons, short answers and changes of event state.

Only explicit learner clauses supply facts. These authored questions are scoped
conversation aids, not general semantic understanding or model-generated prose.
"""

import re


def _plan(frame, known, *questions, prefix=""):
    return {
        "frame": frame,
        "prefix": prefix,
        "known_information": known,
        "choices": [{"intent": intent, "question": q} for intent, q in questions],
    }


def _clean(text):
    return text.replace("’", "'").strip()


def _meal_context(history):
    """Only use an immediately preceding explicit future meal, not a tutor claim."""
    for row in reversed(history[-4:]):
        text = _clean(row["learner_text"])
        match = re.fullmatch(
            r"I (?:will|am going to) (?:cook|bake|prepare) ([\w -]{1,35}?) (?:tomorrow|tonight|next week)[.!]?",
            text,
            re.IGNORECASE,
        )
        if match:
            return match[1]
        if not re.fullmatch(
            r"I chose [\w -]{1,35} because [\w ', -]{1,90}[.!]?", text, re.IGNORECASE
        ):
            return None  # Do not carry meal references across a topic change.
    return None


def plan_continuation(text, history=()):
    text = _clean(text)
    reason = re.fullmatch(
        r"I (?:enjoy|like|love) ([\w -]{1,45}?) because ([\w ', -]{1,100})[.!]?",
        text,
        re.IGNORECASE,
    )
    if reason:
        topic, why = reason.groups()
        return _plan(
            "interest_reason_given",
            {"interest": topic, "reason": why},
            ("interest_beginning", f"When did you first become interested in {topic}?"),
            ("interest_other_aspect", f"What else do you like about {topic}?"),
        )

    commute = re.fullmatch(
        r"I take (?:the )?(bus|train|tram|ferry|subway)(?: to (work|school|college))? because (?:it costs less|it is cheaper|it's cheaper)[.!]?",
        text,
        re.IGNORECASE,
    )
    if commute:
        mode, destination = commute.groups()
        return _plan(
            "commute_reason_given",
            {"mode": mode, "destination": destination, "reason": "lower cost"},
            ("journey_activity", f"What do you usually do during your {mode} journey?"),
            ("journey_duration", f"How long does your {mode} journey take?"),
        )
    duration = re.fullmatch(
        r"The (?:journey|ride|trip) takes ([\w -]{1,35})[.!]?", text, re.IGNORECASE
    )
    if duration and history:
        # Stay with the latest learner's explicit first-person commute.
        source = _clean(history[-1]["learner_text"])
        source_mode = re.fullmatch(
            r"I take (?:the )?(bus|train|tram|ferry|subway)(?: to (?:work|school|college))?(?: because [\w ', -]{1,90})?[.!]?",
            source,
            re.IGNORECASE,
        )
        if source_mode:
            mode = source_mode[1].lower()
            return _plan(
                "commute_duration_given",
                {"mode": mode, "duration": duration[1]},
                (
                    "journey_activity",
                    f"What do you usually do during your {mode} journey?",
                ),
                ("journey_preference", f"What do you like about travelling by {mode}?"),
            )

    chosen = re.fullmatch(
        r"I chose ([\w -]{1,35}) because ([\w ', -]{1,90})[.!]?", text, re.IGNORECASE
    )
    meal = _meal_context(history)
    if chosen and meal and chosen[1].casefold() == meal.casefold():
        return _plan(
            "future_meal_reason_given",
            {"dish": meal, "reason": chosen[2], "completed": False},
            ("preparation_method", f"How will you prepare the {meal}?"),
            ("preparation_plan", f"What do you need to prepare the {meal}?"),
        )
    if meal and re.fullmatch(
        r"I (?:have not|haven't) (?:cooked|prepared|made) (?:them|it) yet[.!]?",
        text,
        re.IGNORECASE,
    ):
        return _plan(
            "meal_not_completed",
            {"dish": meal, "completed": False},
            ("preparation_plan", f"What do you need to prepare the {meal}?"),
            ("preparation_company", f"Who will you cook the {meal} with, if anyone?"),
            prefix=f"You haven't cooked the {meal} yet.",
        )

    cancelled = re.fullmatch(
        r"The interview (?:was|has been) (cancelled|canceled)[.!]?", text, re.IGNORECASE
    )
    if cancelled:
        return _plan(
            "interview_cancelled",
            {"interview_cancelled": True},
            (
                "cancellation_next_step",
                "What will happen now that the interview is cancelled?",
            ),
            prefix="The interview is cancelled.",
        )

    upcoming_pattern = r"My ([\w-]+) has (?:an?|the) interview at (?:an?|the) (college|university|company) (tomorrow|today|next week)[.!]?"
    upcoming = re.fullmatch(upcoming_pattern, text, re.IGNORECASE)
    if upcoming:
        person, place, when = upcoming.groups()
        return _plan(
            "relative_interview_plan",
            {"relative": person, "place": place, "when": when},
            (
                "interview_preparation",
                f"How is your {person} preparing for the interview?",
            ),
            ("interview_feeling", f"How does your {person} feel about the interview?"),
        )

    # Find one recent explicit interview; ambiguous people or revisions abstain.
    context = None
    relatives = set()
    for row in history[-4:]:
        source = _clean(row["learner_text"])
        relatives.update(
            p.lower() for p in re.findall(r"\bmy ([\w-]+)\b", source, re.IGNORECASE)
        )
        candidate = re.fullmatch(upcoming_pattern, source, re.IGNORECASE)
        if candidate:
            context = candidate.groups()
        elif re.search(r"\binterview\b", source, re.IGNORECASE):
            context = None
    if not context or relatives != {context[0].lower()}:
        return None
    person, place, when = context
    caught = re.fullmatch(
        rf"My {re.escape(person)} is (relieved|happy|glad) because (?:he|she|they) caught (?:his|her|their|the) ([\w-]+)[.!]?",
        text,
        re.IGNORECASE,
    )
    if caught:
        return _plan(
            "relative_interview_transport",
            {"relative": person, "transport": caught[2], "interview_completed": False},
            (
                "interview_preparation",
                f"How is your {person} preparing for the interview?",
            ),
            ("interview_feeling", f"How does your {person} feel about the interview?"),
            prefix=f"Your {person} feels {caught[1]}.",
        )
    subject = re.fullmatch(
        r"(He|She|They) wants? to study ([\w -]{1,40})[.!]?", text, re.IGNORECASE
    )
    if subject and place.lower() in {"college", "university"}:
        pronouns = {
            "daughter": "she",
            "niece": "she",
            "sister": "she",
            "mother": "she",
            "son": "he",
            "nephew": "he",
            "brother": "he",
            "father": "he",
        }
        if pronouns.get(person.lower()) != subject[1].lower():
            return None  # Do not silently assign a mismatched or ambiguous pronoun.
        topic = subject[2]
        if re.search(r"\b(?:but|not|because|he|she|they)\b", topic, re.IGNORECASE):
            return None
        return _plan(
            "relative_subject_given",
            {"relative": person, "subject": topic},
            ("study_interest_reason", f"What interests your {person} about {topic}?"),
            prefix=f"Your {person} wants to study {topic}.",
        )
    return None
