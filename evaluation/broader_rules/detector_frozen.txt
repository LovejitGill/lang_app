"""Explain an LLM proposal using local LanguageTool rule evidence, offline only.

No learner-word whitelist: LanguageTool supplies rule IDs, spans and suggestions.
Exact full-sentence agreement is required. Agreement between tools is not proof.
"""

import re

from benchmark import utf16_span

VARIANT = "languagetool-backed-explanations-v1"
FIXED = {
    "MD_BASEFORM": "After words like ‘can’ or ‘should’, use the basic verb form.",
    "DID_BASEFORM": "After ‘do’, ‘does’, or ‘did’, use the basic verb form.",
    "DOES_X_HAS": "After ‘do’, ‘does’, or ‘did’, use the basic verb form.",
    "AUXILIARY_DO_WITH_INCORRECT_VERB_FORM": "After ‘do’, ‘does’, or ‘did’, use the basic verb form.",
    "CD_NN": "Use a plural noun for more than one item.",
    "SINCE_FOR": "Use ‘for’ to say how long something lasts.",
    "THERE_VBP_NN": "Use ‘there is’ for one thing.",
    "AGREEMENT_SENT_START": "Use the basic verb form with a plural subject.",
    "DEPEND_ON": "Use ‘depend on’ when something relies on something else.",
}


def explanation(rule, old, new, prefix, text):
    """Use rule semantics, not the checker's potentially vague message text."""
    name = rule["id"]
    if name in FIXED:
        return FIXED[name]
    if name == "EN_A_VS_AN":
        if (old.lower(), new.lower()) == ("a", "an"):
            return "Use ‘an’ before a vowel sound."
        if (old.lower(), new.lower()) == ("an", "a"):
            return "Use ‘a’ before a consonant sound."
    if name == "MOST_COMPARATIVE" and old == "more " + new:
        return f"Use ‘{new}’ without ‘more’ when comparing."
    if name == "ADMIT_ENJOY_VB" and rule.get("subId") == "1":
        before, after = old.split(), new.split()
        if (
            len(before) == 3
            and before[1] == "to"
            and len(after) == 2
            and before[0] == after[0]
            and after[1].endswith("ing")
        ):
            return f"After ‘{before[0]}’, use the ‘-ing’ form."
    if name == "NON3PRS_VERB" and re.search(
        r"\b(can|could|should|must|might|would) $", prefix
    ):
        return FIXED["MD_BASEFORM"]
    if name == "HE_VERB_AGR":
        subject = re.fullmatch(r"(He|She|It) ", prefix)
        # This rule also suggests past forms. Never label those as present tense.
        if (
            subject
            and new.endswith("s")
            and not re.search(r"\b(yesterday|ago|last)\b", text, re.IGNORECASE)
        ):
            return f"With ‘{subject[1].lower()}’, use ‘{new}’ in the present tense."
    return None


def explain_proposal(original, proposed, evidence):
    """Return offered/withheld with traceable rule evidence; no network or labels."""
    if not all(
        isinstance(x, str) and x.strip() and len(x) <= 1200
        for x in (original, proposed)
    ):
        raise ValueError("Provide nonempty text of at most 1200 characters.")
    empty = {"rule_id": None, "explanation": None, "edit": None}
    if original == proposed:
        return {
            **empty,
            "state": "no_proposal",
            "reason": "No change proposed; not a correctness claim.",
        }
    # Preserve the established narrow policy for quotes and compound clauses.
    if re.search(r"[\"'‘’“”\n\r]|\b(?:and|or)\b", original, re.IGNORECASE):
        return {
            **empty,
            "state": "withheld",
            "reason": "Quoted or coordinated text needs review.",
        }
    if not isinstance(evidence, dict) or not isinstance(evidence.get("matches"), list):
        raise TypeError("Malformed LanguageTool evidence.")
    candidates = []
    for index, match in enumerate(evidence["matches"]):
        rule = match["rule"]
        # Grammar/usage IDs are curated above; spelling/style matches cannot explain edits.
        start, end = utf16_span(original, match["offset"], match["length"])
        old = original[start:end]
        for choice in match["replacements"]:
            new = choice["value"]
            if new == old or original[:start] + new + original[end:] != proposed:
                continue
            message = explanation(rule, old, new, original[:start], original)
            if message:
                candidates.append(
                    {
                        "rule_id": rule["id"],
                        "explanation": message,
                        "edit": {
                            "start": start,
                            "end": end,
                            "original": old,
                            "replacement": new,
                        },
                        "match_index": index,
                    }
                )
    # Do not let multiple agreeing or conflicting matches silently choose wording.
    if len(candidates) != 1:
        return {
            **empty,
            "state": "withheld",
            "reason": "No single supported rule exactly reconstructs the proposal.",
        }
    return {
        **candidates[0],
        "state": "provisional",
        "reason": "Matching local rule and proposal; human review pending.",
    }
