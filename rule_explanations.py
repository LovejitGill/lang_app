"""Provisional, offline explanation rules; matching is not proof of correctness.

Finite word lists deliberately limit coverage. No model calls or gold labels.
Short language is preferred, but sentence count is not a validation requirement.
"""

import re

VARIANT = "provisional-short-rules-context-v1"

TEMPLATES = {
    "singular_agreement": "For one person, use ‘{verb}’ in the present tense.",
    "plural_agreement": "For more than one person, use ‘{verb}’ in the present tense.",
    "there_singular": "Use ‘there is’ for one thing.",
    "modal_base": "After words like ‘can’ or ‘should’, use the basic verb form.",
    "do_base": "After ‘do’, ‘does’, or ‘did’, use the basic verb form.",
    "number_plural": "Use a plural noun for more than one item.",
    "duration_for": "Use ‘for’ to say how long something lasts.",
    "single_comparative": "Use only ‘shorter’, without ‘more’, when comparing.",
}
# Small, explicit morphology lists: unknown words are withheld, never guessed.
VERBS = {
    "speaks": "speak",
    "takes": "take",
    "arrives": "arrive",
    "likes": "like",
    "ordered": "order",
    "wrote": "write",
    "eats": "eat",
    "works": "work",
    "played": "play",
}
NOUNS = {
    "sandwich": "sandwiches",
    "shirt": "shirts",
    "box": "boxes",
    "book": "books",
    "apple": "apples",
    "child": "children",
}
COMPARATIVES = "shorter|colder|cheaper|taller|smaller|faster"


# Explicit present-tense pairs avoid guessing irregular forms or noun number.
PRESENT_VERBS = {
    "walk": "walks",
    "drive": "drives",
    "need": "needs",
    "work": "works",
    "like": "likes",
    "eat": "eats",
    "play": "plays",
}
SINGULAR_PEOPLE = (
    "He|She|My (?:aunt|uncle|sister|brother)|The (?:teacher|student|driver)"
)
PLURAL_PEOPLE = "We|The (?:students|teachers|drivers)|My (?:sisters|brothers)"


def agreement_change(original: str, proposed: str):
    """Accept only a simple whole clause; abstain on complex/quoted contexts."""
    # A small allowlist of characters and explicit exclusions keep this bounded.
    if not re.fullmatch(r"[A-Za-z0-9 ,]+[.!]?", original):
        return None
    if re.search(
        r"\b(and|or|who|which|that|if|wish|yesterday|ago|last|not|never)\b",
        original,
        re.IGNORECASE,
    ):
        return None
    for subject, pairs, rule in (
        (SINGULAR_PEOPLE, PRESENT_VERBS, "singular_agreement"),
        (PLURAL_PEOPLE, {v: k for k, v in PRESENT_VERBS.items()}, "plural_agreement"),
    ):
        match = re.fullmatch(
            rf"({subject}) ({'|'.join(pairs)})([ .,].*|[.!]|)", original
        )
        if match:
            verb = pairs[match[2]]
            if proposed == match[1] + " " + verb + match[3]:
                return rule, TEMPLATES[rule].format(verb=verb)
    # Avoid lists ('a bowl and a cup') and plural-headed noun phrases.
    match = re.fullmatch(
        r"There are (a (?:bowl|cup|book|chair|table|box))"
        r"((?: (?:on|under|near) the (?:table|chair|desk|door))?)[.!]?",
        original,
    )
    if match and proposed == original.replace("There are ", "There is ", 1):
        return "there_singular", TEMPLATES["there_singular"]
    return None


def explain_change(original: str, proposed: str) -> dict:
    """Match one complete transformation; extra edits or unknown rules abstain."""
    if not all(isinstance(s, str) and s.strip() for s in (original, proposed)):
        raise ValueError("Provide two nonempty strings.")
    if max(len(original), len(proposed)) > 1200:
        raise ValueError("Text must be at most 1200 characters.")
    if original == proposed:
        return {"state": "no_proposal", "rule": None, "explanation": None}
    # Quoted examples and multiple clauses need context this matcher lacks.
    if re.search(r"[\"'‘’“”\n\r]|\b(?:and|or)\b", original, re.IGNORECASE):
        return {"state": "withheld", "rule": None, "explanation": None}
    agreement = agreement_change(original, proposed)
    matches = [agreement] if agreement else []

    def consider(pattern, transform, rule, explanation=None):
        for match in re.finditer(pattern, original):
            replacement = transform(match)
            if replacement is None:
                continue
            candidate = (
                original[: match.start()] + replacement + original[match.end() :]
            )
            if candidate == proposed:
                matches.append(
                    (rule, explanation(match) if explanation else TEMPLATES[rule])
                )

    verbs = "|".join(VERBS)
    # Require a pronoun subject to avoid treating the noun 'can' as a modal.
    consider(
        rf"\b((?:I|You|you|He|he|She|she|We|we|They|they) (?:can|could|should|must|might|would) )(?:({verbs}))\b",
        lambda m: m[1] + VERBS[m[2]],
        "modal_base",
    )
    consider(
        rf"\b((?:(?:I|You|you|He|he|She|she|We|we|They|they) (?:do|does|did) not |(?:Do|Does|Did) (?:I|you|he|she|we|they) ))({verbs})\b",
        lambda m: m[1] + VERBS[m[2]],
        "do_base",
    )
    consider(
        rf"(?<![\w.-])((?:two|three|four|five|six|seven|eight|nine|ten|[2-9]) )({'|'.join(NOUNS)})(?=[.!?,;:]|$)",
        lambda m: m[1] + NOUNS[m[2]],
        "number_plural",
    )
    # Only a present-perfect clause with a known verb and explicit duration.
    consider(
        r"\b((?:I|You|you|We|we|They|they) have (?:lived|worked|waited)|(?:He|he|She|she) has (?:lived|worked|waited))( here)? since ((?:two|three|four|five|six|seven|eight|nine|ten|[2-9]) (?:days|weeks|months|years))(?=[.!]?$)",
        lambda m: m[1] + (m[2] or "") + " for " + m[3],
        "duration_for",
    )
    consider(
        rf"\b(is )more ({COMPARATIVES})\b",
        lambda m: m[1] + m[2],
        "single_comparative",
        lambda m: f"Use only ‘{m[2]}’, without ‘more’, when comparing.",
    )
    if len(matches) != 1:
        return {"state": "withheld", "rule": None, "explanation": None}
    rule, explanation = matches[0]
    return {"state": "provisional", "rule": rule, "explanation": explanation}
