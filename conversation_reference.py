"""Small authored English references and last-question clarification.

This catalog is intentionally limited. A non-match means "not supported here",
not that a question is incorrect. Examples describe imaginary teaching examples,
never facts about the learner. No model, network, or grammar checker is called.
"""

import re

CATALOG = {
    frozenset({"lend", "borrow"}): {
        "id": "lend_borrow",
        "definitions": {
            "lend": "give someone something for a short time, expecting it back",
            "borrow": "use something that belongs to someone else, then return it",
        },
        "example": "Example: I lend you a book; you borrow the book from me.",
    },
    frozenset({"teach", "learn"}): {
        "id": "teach_learn",
        "definitions": {
            "teach": "help someone gain knowledge or a skill",
            "learn": "gain knowledge or a skill",
        },
        "example": "Example: A teacher teaches English; a student learns English.",
    },
}

# Full matches prevent an incidental mention, extra pair, or negative instruction
# from becoming a positive request. Each pair member is one uninflected word.
PAIR = r"(?:the words? )?['\"]?(\w+)['\"]? (?:and|versus|vs\.?) ['\"]?(\w+)['\"]?"
COMPARISONS = tuple(
    re.compile(pattern + r"[?.!]?", re.IGNORECASE)
    for pattern in (
        rf"(?:what is|what's) the difference between {PAIR}",
        rf"(?:can|could) you explain the difference between {PAIR}",
        rf"(?:please )?explain the difference between {PAIR}",
        rf"how (?:do {PAIR} differ|are {PAIR} different)",
        rf"(?:can|could) you compare {PAIR}",
        rf"(?:please )?compare {PAIR}",
        rf"when (?:do|should) I use {PAIR}",
    )
)
CLARIFY = re.compile(
    r"(?:"
    r"(?:can|could) you explain (?:what )?(?:your|the) (?:last |previous |first |second )?question(?: means)?"
    r"|what do you mean(?: by (?:your|the|that) (?:last |previous |first |second )?question)?"
    r"|(?:can|could) you (?:ask|say) (?:that|your question) (?:more simply|in simpler words)"
    r"|I (?:don't|do not) understand (?:your|the) (?:last |previous |first |second )?question"
    r"|(?:please )?explain (?:your|the) (?:last |previous |first |second )?question in simpler words"
    r")[?.!]?",
    re.IGNORECASE,
)
TOPIC = r"[\w][\w' -]{0,65}"
NO_FOLLOWUP = re.compile(
    r"(?:\s+|[,;]\s*)(?:no follow[- ]up(?: questions?)?|without a follow[- ]up(?: question)?)[.!]?\s*$",
    re.IGNORECASE,
)
CONTEXT_COMPARISON = re.compile(
    rf"(?:what is|what's) the difference between {PAIR} in this sentence[?.!]?",
    re.IGNORECASE,
)


def _normalize(text):
    return " ".join(text.strip().replace("’", "'").replace("‘", "'").split())


def _topic(learner_text):
    """Resolve 'that' only for a simple explicit positive interest statement."""
    match = re.fullmatch(
        rf"I (?:like|enjoy|love) ({TOPIC})[.!]?",
        _normalize(learner_text),
        re.IGNORECASE,
    )
    if not match or re.search(
        r"\b(?:but|because|not|don't|I|he|she|we|they|you)\b", match[1], re.IGNORECASE
    ):
        return None
    return match[1]


def _result_topic(learner_text):
    """Resolve a result only from a short affirmative statement of making it."""
    match = re.fullmatch(
        rf"(?:I|We) (?:made|cooked|prepared|baked) ({TOPIC}?)(?: for (?:breakfast|lunch|dinner|supper))?[.!]?",
        _normalize(learner_text),
        re.IGNORECASE,
    )
    if not match or re.search(
        r"\b(?:but|because|not|and|I|he|she|we|they|you|it|that)\b",
        match[1],
        re.IGNORECASE,
    ):
        return None
    result = re.sub(r"^(?:a|an) ", "the ", match[1], flags=re.IGNORECASE)
    result = re.sub(r"^(?:my|our) ", "your ", result, flags=re.IGNORECASE)
    if not re.match(r"(?:the|some|your) ", result, re.IGNORECASE):
        result = "the " + result
    return result


def _select_question(tutor_reply, request):
    """Select within the latest reply, never silently use another history row."""
    questions = [part.strip() for part in re.findall(r"[^.?!]*\?", tutor_reply)]
    position = (
        "first"
        if re.search(r"\bfirst question\b", request, re.IGNORECASE)
        else (
            "second"
            if re.search(r"\bsecond question\b", request, re.IGNORECASE)
            else "last"
        )
    )
    if not questions:
        # A single imperative such as "Tell me what interests you..." is useful
        # question context too; a requested second question cannot be invented.
        return tutor_reply if position != "second" else ""
    if position == "second":
        return questions[1] if len(questions) > 1 else ""
    return questions[0] if position == "first" else questions[-1]


def _simple_question(question, learner_text):
    # Each mapping names a question intent explicitly, rather than treating any
    # question containing a known adjective as having the same meaning.
    source = _normalize(question)
    match = re.fullmatch(
        rf"What do you find most rewarding about ({TOPIC})\?", source, re.IGNORECASE
    )
    if match:
        topic = _topic(learner_text) if match[1].lower() == "that" else match[1]
        if topic:
            return f"What do you enjoy most about {topic}?", "rewarding_to_enjoy"
    match = re.fullmatch(
        rf"Tell me what interests you about ({TOPIC})[.!]?", source, re.IGNORECASE
    )
    if match:
        topic = _topic(learner_text) if match[1].lower() == "that" else match[1]
        if topic:
            return f"What makes {topic} interesting to you?", "interest_to_interesting"
    match = re.fullmatch(rf"How did ({TOPIC}) turn out\?", source, re.IGNORECASE)
    if match:
        topic = _result_topic(learner_text) if match[1].lower() == "it" else match[1]
        if topic:
            return f"How was {topic}?", "turn_out_to_result"
    match = re.fullmatch(rf"What drew you to ({TOPIC})\?", source, re.IGNORECASE)
    if match:
        topic = _topic(learner_text) if match[1].lower() == "that" else match[1]
        if topic:
            return (
                f"Why did you become interested in {topic}?",
                "drew_to_interest_origin",
            )
    return None


def _meaning_statement(simple_question, reference_id):
    """Explain the requested question instead of posing it again when asked."""
    if reference_id == "rewarding_to_enjoy":
        topic = simple_question.removeprefix("What do you enjoy most about ")[:-1]
        return f"I was asking which part of {topic} you enjoy most."
    if reference_id == "interest_to_interesting":
        return f"I was asking {simple_question[0].lower() + simple_question[1:-1]}."
    if reference_id == "drew_to_interest_origin":
        topic = simple_question.removeprefix("Why did you become interested in ")[:-1]
        return f"I was asking why you became interested in {topic}."
    topic = simple_question.removeprefix("How was ")[:-1]
    return f"I was asking how {topic} was."


def answer(text, history=()):
    """Return an explicitly supported authored answer, or None for other inputs.

    The caller remains responsible for stop controls. Simple trailing no-follow-up
    instructions are honored here too. History uses
    completed rows containing learner_text and tutor_reply; only the latest row
    can explain the *last* question, so an older familiar question is never reused.
    """
    if not isinstance(text, str) or not text.strip():
        return None
    normalized = _normalize(text)
    no_followup = bool(NO_FOLLOWUP.search(normalized))
    normalized = NO_FOLLOWUP.sub("", normalized).strip()
    context_comparison = CONTEXT_COMPARISON.fullmatch(normalized)
    if context_comparison:
        first, second = (word.lower() for word in context_comparison.groups())
        if first == second:
            return None
        return {
            "reply": (
                f"I need the sentence containing ‘{first}’ and ‘{second}’ to explain those meanings."
                if no_followup
                else f"Please share the sentence that uses ‘{first}’ and ‘{second}’."
            ),
            "support": "question_clarification",
            "reference_id": "missing_comparison_context",
            "provenance": "authored_context_request_v1",
        }
    for pattern in COMPARISONS:
        match = pattern.fullmatch(normalized)
        if not match:
            continue
        words = [word.lower() for word in match.groups() if word is not None]
        entry = CATALOG.get(frozenset(words))
        if not entry or len(words) != 2:
            return None
        first, second = words
        definitions = entry["definitions"]
        return {
            "reply": (
                f"‘{first.capitalize()}’ means {definitions[first]}. "
                f"‘{second.capitalize()}’ means {definitions[second]}. {entry['example']}"
            ),
            "support": "local_reference",
            "reference_id": entry["id"],
            "provenance": "authored_comparison_catalog_v1",
        }
    if not CLARIFY.fullmatch(normalized):
        return None
    row = history[-1] if history and isinstance(history[-1], dict) else {}
    question = row.get("tutor_reply", "")
    learner = row.get("learner_text", "")
    if not isinstance(question, str) or not isinstance(learner, str):
        question, learner = "", ""
    question = _select_question(question, normalized)
    simplified = _simple_question(question, learner)
    if simplified:
        reply, reference_id = simplified
        if no_followup:
            reply = _meaning_statement(reply, reference_id)
    elif question and len(question) <= 180 and "?" in question:
        reply = (
            f"I don't have a checked simpler explanation for ‘{question}’."
            if no_followup
            else f"In ‘{question}’, which word or part would you like me to explain?"
        )
        reference_id = "unknown_question_form"
    else:
        reply = (
            "I don't have the question needed to explain its meaning."
            if no_followup
            else "I don't have that question here. Could you repeat it?"
        )
        reference_id = "missing_or_unsupported_question_context"
    return {
        "reply": reply,
        "support": "question_clarification",
        "reference_id": reference_id,
        "provenance": "authored_question_intent_mapping_v1",
    }
