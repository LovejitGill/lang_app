"""Experimental correction-first adapter using only a resident local checker.

This is rule-only evidence, not the reviewed LLM-plus-rule grammar pipeline.
The small allowlist deliberately abstains on ambiguous or unsupported inputs.
"""

import asyncio
import re
from time import perf_counter

import httpx

from benchmark import utf16_span
from grammar_gap_detector import explain_with_gaps

HOST = "http://127.0.0.1:8081"
PROVENANCE = "resident_languagetool_rule_only"
RULES = {"DID_PAST", "HE_VERB_AGR"}


def _present_forms(verb):
    """Limit the checker's suggestion to the same verb in third-person present."""
    if verb in {"have", "be", "do"}:
        return {{"have": "has", "be": "is", "do": "does"}[verb]}
    if re.search(r"[^aeiou]y$", verb):
        return {verb[:-1] + "ies"}
    if re.search(r"(?:s|sh|ch|x|z|o)$", verb):
        return {verb + "es"}
    return {verb + "s"}


def _select(text, raw):
    if (
        raw["software"]["version"] != "6.6"
        or raw["warnings"]["incompleteResults"] is not False
        or not isinstance(raw["matches"], list)
    ):
        raise ValueError("Incomplete, malformed or unsupported checker response")
    empty = {"state": "no_supported_correction"}
    # Several matches can be interacting edits; this adapter cannot resolve them.
    if len(raw["matches"]) != 1:
        return empty
    match = raw["matches"][0]
    rule = match["rule"]["id"]
    if rule not in RULES:
        return empty
    start, end = utf16_span(text, match["offset"], match["length"])
    old, prefix = text[start:end], text[:start]
    if not re.fullmatch(r"[a-z]+", old):
        return empty
    # A context mismatch suggests evidence for another input or invalid offsets.
    context = match["context"]
    left, right = utf16_span(context["text"], context["offset"], context["length"])
    if context["text"][left:right] != old or context["text"] not in text:
        raise ValueError("Checker context does not match this input")
    if rule == "HE_VERB_AGR":
        if not re.fullmatch(r"(?:He|She|It) ", prefix) or re.search(
            r"\b(?:yesterday|ago|last|earlier|previously|once|used to|(?:19|20)\d{2})\b",
            text,
            re.IGNORECASE,
        ):
            return empty
    else:
        # Limit evidence to straightforward personal-pronoun did constructions.
        subject = r"(?:I|you|he|she|it|we|they)"
        if not re.fullmatch(
            rf"(?:Did {subject} |{subject} did )(?:not )?", prefix, re.IGNORECASE
        ):
            return empty
    if not isinstance(match["replacements"], list):
        raise TypeError("Malformed replacements")
    candidates = {}
    for replacement in match["replacements"]:
        new = replacement["value"]
        if not isinstance(new, str):
            raise TypeError("Malformed replacement")
        if not re.fullmatch(r"[a-z]+", new) or new == old:
            continue
        if rule == "HE_VERB_AGR" and new not in _present_forms(old):
            continue
        proposed = text[:start] + new + text[end:]
        decision = explain_with_gaps(text, proposed, raw, {"matches": []})
        if decision["state"] == "provisional":
            candidates[new] = {
                "state": "offered",
                "corrected_text": proposed,
                "original": old,
                "replacement": new,
                "explanation": decision["explanation"],
                "rule_id": decision["rule_id"],
            }
    return next(iter(candidates.values())) if len(candidates) == 1 else empty


async def get_correction(text, *, budget=0.2, client=None):
    """Offer one supported edit within a small deadline, or explicitly abstain.

    Client setup, HTTP and validation share the deadline. Elapsed time is still
    measured: cancellation and synchronous setup cannot guarantee hard real time.
    """
    began = perf_counter()
    if not isinstance(text, str) or not text.strip() or len(text) > 1000:
        raise ValueError("Enter 1–1000 characters of learner text.")
    if not isinstance(budget, (int, float)) or not 0 < budget <= 0.3:
        raise ValueError("Use a correction budget above zero and at most 0.3 seconds.")
    result = {"state": "unavailable"}
    try:
        async with asyncio.timeout(budget):

            async def fetch(connection):
                response = await connection.post(
                    HOST + "/v2/check", data={"language": "en-US", "text": text}
                )
                response.raise_for_status()
                return response.json()

            if client is None:
                async with httpx.AsyncClient(trust_env=False, timeout=budget) as owned:
                    raw = await fetch(owned)
            else:
                raw = await fetch(client)
            result = _select(text, raw)
            # Synchronous setup/parsing may consume the deadline before yielding.
            if perf_counter() - began > budget:
                result = {"state": "unavailable", "diagnostic_type": "TimeoutError"}
    except (TimeoutError, httpx.HTTPError, ValueError, TypeError, KeyError) as exc:
        result = {"state": "unavailable", "diagnostic_type": type(exc).__name__}
    return {**result, "provenance": PROVENANCE, "seconds": perf_counter() - began}
