"""Sentence-specific reasons layered onto the frozen broader-rule detector.

This changes wording only. It cannot add corrections or repair wrong rule choices.
Use detected grammar and exact text; do not invent a deeper reason for conventions.
"""

import re

from grammar_rule_detector import explain_proposal

VARIANT = "sentence-specific-reasons-v2"
DO_RULES = {"DID_BASEFORM", "DOES_X_HAS", "AUXILIARY_DO_WITH_INCORRECT_VERB_FORM"}
MODALS = r"\b(can|could|should|must|might|would)\s+$"
NUMBER_WORDS = (
    r"two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|"
    r"fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty"
)


def sentence_reason(text, decision):
    """Link a matched rule to the learner's words; no new grammatical decisions."""
    edit = decision["edit"]
    old, new = edit["original"], edit["replacement"]
    prefix, suffix = text[: edit["start"]], text[edit["end"] :]
    rule = decision["rule_id"]
    if rule in {"MD_BASEFORM", "NON3PRS_VERB"}:
        modal = re.search(MODALS, prefix, re.IGNORECASE)
        if modal:
            return f"With ‘{modal[1]}’, the verb stays in its basic form for every subject: ‘{new}’."
    if rule in DO_RULES:
        auxiliaries = re.findall(r"\b(do|does|did)\b", prefix, re.IGNORECASE)
        if auxiliaries:
            auxiliary = auxiliaries[-1].lower()
            if auxiliary == "did":
                return f"‘Did’ already marks the past, so use ‘{new}’, not ‘{old}’."
            if auxiliary == "does":
                return f"‘Does’ already matches the subject, so ‘{new}’ does not take ‘-s’."
            return f"‘Do’ carries the tense, so the main verb keeps its basic form: ‘{new}’."
    if rule == "CD_NN":
        number = re.search(
            rf"(?<![\w.-])({NUMBER_WORDS}|\d+)\s+$", prefix, re.IGNORECASE
        )
        if number and (not number[1].isdigit() or int(number[1]) > 1):
            return f"‘{number[1].capitalize()}’ is more than one, so use the plural ‘{new}’."
        return f"You mean more than one ‘{old}’, so use the plural ‘{new}’."
    if rule == "EN_A_VS_AN":
        following = re.match(r"\s+([A-Za-z]+)\b", suffix)
        if following:
            sound = "vowel" if new.lower() == "an" else "consonant"
            return f"‘{following[1].capitalize()}’ starts with a {sound} sound, so use ‘{new}’."
    if rule == "MOST_COMPARATIVE":
        return f"‘{new.capitalize()}’ already makes a comparison, so adding ‘more’ repeats the same job."
    if rule == "SINCE_FOR":
        # Only quote a duration that actually appears immediately after the edit.
        duration = re.match(
            r"\s+([A-Za-z0-9 -]+?\b(?:seconds?|minutes?|hours?|days?|weeks?|months?|years?))(?=[.!?,]|$)",
            suffix,
        )
        if duration:
            return f"‘{duration[1].capitalize()}’ is a length of time, so use ‘for’."
        return "‘For’ introduces a length of time; ‘since’ introduces a starting point."
    if rule == "THERE_VBP_NN":
        noun = re.match(
            r"\s+((?:a|an) \w+)(?=\s+(?:on|under|near|in|at|by)\b|[.!?,]|$)", suffix
        )
        if noun:
            return f"‘{noun[1].capitalize()}’ names one thing, so use ‘there is’."
        return "The sentence introduces one thing, so its verb is ‘is’."
    if rule == "AGREEMENT_SENT_START":
        subject = prefix.strip()
        if subject and len(subject) <= 60 and re.fullmatch(r"[A-Za-z ]+", subject):
            return f"‘{subject}’ means more than one, so use ‘{new}’ without ‘-s’."
        return f"The subject is plural (more than one), so use ‘{new}’ without ‘-s’."
    if rule == "HE_VERB_AGR":
        subject = prefix.strip()
        if subject in {"He", "She", "It"}:
            return f"‘{subject}’ is singular, meaning one. In the present tense, use ‘{new}’."
    if rule == "ADMIT_ENJOY_VB":
        words = new.split()
        if len(words) == 2:
            return f"‘{words[1].capitalize()}’ names the activity. After ‘{words[0]}’, we use this ‘-ing’ form."
    if rule == "DEPEND_ON":
        return "‘Depend on’ is a fixed word pair meaning ‘rely on’; ‘depend of’ is not used."
    return None


def explain_with_reason(original, proposed, evidence):
    """Preserve detection; mark missing context rather than fabricate a reason."""
    decision = explain_proposal(original, proposed, evidence)
    if decision["state"] != "provisional":
        return decision
    message = sentence_reason(original, decision)
    return {
        **decision,
        "explanation": message or decision["explanation"],
        "previous_explanation": decision["explanation"],
        "reason_status": "contextual_draft" if message else "needs_context_review",
    }
