"""Bounded follow-up intents for stated reasons, feelings and interview context.

Return authored choices plus supporting information. No generation, lookup,
clinical advice or general semantic inference happens in this module.
"""

import re


def _result(frame, prefix, known, *choices):
    return {
        "frame": frame,
        "prefix": prefix,
        "known_information": known,
        "choices": [
            {"intent": intent, "question": question} for intent, question in choices
        ],
    }


def plan_context(text, history=()):
    text = text.replace("’", "'").strip()
    journey = re.fullmatch(
        r"I( take| took| will take|'ll take) (?:the )?(bus|train|tram|ferry|subway)"
        r"(?: (tomorrow|today|next week))? because (?:it is|it's|it was) "
        r"(cheaper|faster) than ([\w -]+?)"
        r"(?:\. The (?:ride|journey) took [\w -]+)?[.!]?",
        text,
        re.IGNORECASE,
    )
    if journey:
        action, mode, when, reason, alternative = journey.groups()
        action, mode = action.strip().lower(), mode.lower()
        known = {
            "mode": mode,
            "when": when,
            "reason": reason,
            "alternative": alternative,
            "time": "past"
            if action == "took"
            else "future"
            if "take" != action or when in {"tomorrow", "next week"}
            else "habit",
        }
        if known["time"] == "future":
            return _result(
                "future_cost_choice",
                "",
                known,
                ("journey_plan", f"How will you plan your {mode} journey?"),
                ("journey_activity", f"What will you do during your {mode} journey?"),
            )
        if known["time"] == "past":
            return _result(
                "completed_cost_choice",
                "",
                known,
                ("journey_experience", f"What was the {mode} journey like?"),
                ("journey_next_choice", f"Would you choose the {mode} again?"),
            )
        return _result(
            "habit_cost_choice",
            "",
            known,
            ("journey_experience", f"What is your usual {mode} journey like?"),
            ("journey_routine", f"How does taking the {mode} fit into your day?"),
        )

    expected = re.fullmatch(
        r"I(?: am not|'m not| don't feel| do not feel) (disappointed|upset|surprised)\. "
        r"I expected (?:this|that|the) (?:result|outcome)(?: because (.+?))?[.!]?",
        text,
        re.IGNORECASE,
    )
    if expected:
        feeling, reason = expected.groups()
        choices = [("result_next_step", "What does this result mean for you?")]
        if reason:
            if re.search(
                r"^I (?:didn't|did not) finish the last question\b",
                reason,
                re.IGNORECASE,
            ):
                choices.insert(
                    0,
                    (
                        "unfinished_question_help",
                        "What would help you finish the last question?",
                    ),
                )
        else:
            choices.insert(
                0, ("expectation_reason", "What made you expect this result?")
            )
        return _result(
            "expected_result",
            "This was the result you expected.",
            {"expected": True, "negated_feeling": feeling.lower(), "reason": reason},
            *choices,
        )

    differing = re.fullmatch(
        r"I(?: am|'m) disappointed, but my ([\w-]+) (?:isn't|is not)\. "
        r"(He|She|They) expected (?:this|that|the) result[.!]?",
        text,
        re.IGNORECASE,
    )
    if differing:
        return _result(
            "different_feelings",
            f"You and your {differing[1]} feel differently about the result.",
            {
                "learner_feeling": "disappointed",
                "other_disappointed": False,
                "other_expected_result": True,
                "relative": differing[1],
            },
            ("hoped_result", "What result were you hoping for?"),
            ("disappointment_reason", "What about the result disappointed you?"),
        )

    finished = re.fullmatch(
        r"The interview is over now\. (He|She|They) (?:feels|feel) "
        r"(pleased|happy|relieved) because (he|she|they) answered every question[.!]?",
        text,
        re.IGNORECASE,
    )
    if finished:
        pronoun, feeling, actor = finished.groups()
        if pronoun.lower() != actor.lower():
            return None
        verb = "feel" if pronoun.lower() == "they" else "feels"
        return _result(
            "completed_interview",
            f"{pronoun.capitalize()} {verb} {feeling} after the interview.",
            {
                "interview_completed": True,
                "feeling": feeling,
                "answered_every_question": True,
            },
            ("interview_next_step", "What happens next after the interview?"),
            (
                "interview_interest",
                f"What did {pronoun.lower()} find most interesting about the interview?",
            ),
        )

    caught = re.fullmatch(
        r"My ([\w-]+) caught (?:the|his|her|their) ([\w-]+) and is (relieved|happy|glad)[.!]?",
        text,
        re.IGNORECASE,
    )
    if not caught:
        return None
    relative, transport, feeling = caught.groups()
    # Use the latest relevant learner mention, never the tutor's guessed destination.
    for row in reversed(history[-4:]):
        source = row["learner_text"].replace("’", "'").strip()
        if re.search(r"\binterview\b", source, re.IGNORECASE) and re.search(
            r"\b(?:over|finished|completed|had|yesterday|cancelled|canceled|not|isn't|wasn't)\b",
            source,
            re.IGNORECASE,
        ):
            return None
        if not re.match(rf"My {re.escape(relative)}\b", source, re.IGNORECASE):
            continue
        context = re.fullmatch(
            rf"My {re.escape(relative)} needs (?:the |his |her |their )?{re.escape(transport)} "
            r"to reach (?:his|her|their) (college|job) interview"
            r"(?: this afternoon| today| tomorrow)?[.!]?",
            source,
            re.IGNORECASE,
        )
        if not context:
            return None
        kind = context[1].lower()
        questions = [
            (
                "interview_preparation",
                f"How is your {relative} preparing for the interview?",
            )
        ]
        people = {
            m[1].lower()
            for h in history[-4:]
            if (m := re.match(r"My ([\w-]+)\b", h["learner_text"], re.IGNORECASE))
        }
        study_known = any(
            re.fullmatch(
                rf"My {re.escape(relative)} (?:wants|plans) to study [\w -]+[.!]?",
                h["learner_text"],
                re.IGNORECASE,
            )
            or (
                people <= {relative.lower()}
                and re.fullmatch(
                    r"(?:He|She|They) (?:wants?|plans?) to study [\w -]+[.!]?",
                    h["learner_text"],
                    re.IGNORECASE,
                )
            )
            for h in history[-4:]
        )
        if kind == "college" and not study_known:
            questions.insert(
                0,
                ("study_interest", f"What subject does your {relative} want to study?"),
            )
        if kind == "job":
            questions.insert(
                0, ("interview_role", f"What job is your {relative} interviewing for?")
            )
        return _result(
            "upcoming_interview",
            f"That sounds like a relief for your {relative}.",
            {
                "relative": relative,
                "transport": transport,
                "feeling": feeling,
                "interview_completed": False,
                "caught": True,
                "kind": kind,
                "source": source,
            },
            *questions,
        )
    return None
