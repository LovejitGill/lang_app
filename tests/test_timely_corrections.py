"""Fast rule evidence is narrow and experimental, not a grammar correctness claim."""

import asyncio
import copy
from urllib.parse import parse_qs

import httpx
import pytest

import timely_corrections as flow


def evidence(text, old=None, replacements=(), rule="DID_PAST"):
    matches = []
    if old is not None:
        start = text.index(old)
        offset = len(text[:start].encode("utf-16-le")) // 2
        length = len(old.encode("utf-16-le")) // 2
        matches.append(
            {
                "offset": offset,
                "length": length,
                "context": {"text": text, "offset": offset, "length": length},
                "rule": {"id": rule},
                "replacements": [{"value": value} for value in replacements],
            }
        )
    return {
        "software": {"version": "6.6"},
        "warnings": {"incompleteResults": False},
        "matches": matches,
    }


def run(text, raw, **kwargs):
    async def exercise():
        def handler(request):
            assert str(request.url) == flow.HOST + "/v2/check"
            assert parse_qs(request.content.decode()) == {
                "language": ["en-US"],
                "text": [text],
            }
            return httpx.Response(200, json=raw)

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await flow.get_correction(text, client=client, **kwargs)

    return asyncio.run(exercise())


def test_did_correction_preserves_sentence_and_original_rule_identity():
    text = "Did you visited the castle?"
    raw = evidence(text, "visited", ["visit"])
    before = copy.deepcopy(raw)
    result = run(text, raw)
    assert result["state"] == "offered"
    assert result["corrected_text"] == "Did you visit the castle?"
    assert result["original"] == "visited" and result["replacement"] == "visit"
    assert result["rule_id"] == "DID_PAST"
    assert "‘Did’ already marks the past" in result["explanation"]
    assert result["provenance"] == "resident_languagetool_rule_only"
    assert result["seconds"] >= 0
    assert raw == before


def test_agreement_filters_past_alternative_without_changing_subject():
    text = "She go to work by train."
    result = run(text, evidence(text, "go", ["goes", "went"], "HE_VERB_AGR"))
    assert result["state"] == "offered"
    assert result["corrected_text"] == "She goes to work by train."
    assert result["replacement"] == "goes"
    assert "‘She’ is singular" in result["explanation"]


@pytest.mark.parametrize(
    "text,old,choices,rule",
    [
        (
            "I take a short walk because it helps me relax.",
            "take",
            ["took"],
            "HE_VERB_AGR",
        ),
        ("She does not go to work by train.", "go", ["goes"], "HE_VERB_AGR"),
        ("They go to work by train.", "go", ["goes"], "HE_VERB_AGR"),
        ("She go to work yesterday.", "go", ["goes", "went"], "HE_VERB_AGR"),
        ("She go to work last Monday.", "go", ["goes", "went"], "HE_VERB_AGR"),
        ("She go to work in 2020.", "go", ["goes", "went"], "HE_VERB_AGR"),
        ("She go to work.", "go", ["is"], "HE_VERB_AGR"),
        ("She go and return.", "go", ["goes"], "HE_VERB_AGR"),
        ("I visited the castle.", "visited", ["visit"], "DID_PAST"),
        ("Did you visit the castle?", "visit", ["visit"], "DID_PAST"),
        ("Did you visited the castle?", "visited", ["visit", "see"], "DID_PAST"),
    ],
)
def test_unsupported_or_ambiguous_evidence_never_becomes_a_correction(
    text, old, choices, rule
):
    result = run(text, evidence(text, old, choices, rule))
    assert result["state"] == "no_supported_correction"
    assert "corrected_text" not in result


def test_multiple_matches_withhold_even_an_individually_supported_edit():
    text = "Did you visited the castle?"
    raw = evidence(text, "visited", ["visit"])
    extra = copy.deepcopy(raw["matches"][0])
    extra["rule"]["id"] = "SOME_OTHER_RULE"
    raw["matches"].append(extra)
    assert run(text, raw)["state"] == "no_supported_correction"


@pytest.mark.parametrize(
    "change",
    [
        "wrong_version",
        "incomplete",
        "missing_warnings",
        "matches_type",
        "bad_span",
        "context_mismatch",
        "replacement_type",
    ],
)
def test_broken_or_incomplete_evidence_is_unavailable_not_clean_text(change):
    text = "Did you visited the castle?"
    raw = evidence(text, "visited", ["visit"])
    if change == "wrong_version":
        raw["software"]["version"] = "6.7"
    elif change == "incomplete":
        raw["warnings"]["incompleteResults"] = True
    elif change == "missing_warnings":
        del raw["warnings"]
    elif change == "matches_type":
        raw["matches"] = None
    elif change == "bad_span":
        raw["matches"][0]["offset"] = len(text) + 1
    elif change == "context_mismatch":
        raw["matches"][0]["context"]["text"] = "Did you painted the castle?"
    else:
        raw["matches"][0]["replacements"][0]["value"] = None
    result = run(text, raw)
    assert result["state"] == "unavailable"
    assert "diagnostic_type" in result and "corrected_text" not in result


def test_utf16_offsets_do_not_split_or_replace_adjacent_unicode():
    text = "Did you visited the 🏰?"
    result = run(text, evidence(text, "visited", ["visit"]))
    assert result["corrected_text"] == "Did you visit the 🏰?"
    raw = evidence(text, "visited", ["visit"])
    raw["matches"][0]["offset"] = (
        len(text[: text.index("🏰")].encode("utf-16-le")) // 2 + 1
    )
    raw["matches"][0]["length"] = 1
    assert run(text, raw)["state"] == "unavailable"


def test_complete_no_match_is_distinct_from_failed_service():
    result = run("I take a short walk because it helps me relax.", evidence("unused"))
    assert result["state"] == "no_supported_correction"
    assert "diagnostic_type" not in result and "corrected_text" not in result


def test_deadline_cancels_slow_checker_without_calling_it_clean():
    cancelled = []

    async def slow(request):
        try:
            await asyncio.sleep(5)
        finally:
            cancelled.append(True)

    async def exercise():
        async with httpx.AsyncClient(transport=httpx.MockTransport(slow)) as client:
            return await flow.get_correction(
                "She go to work.", client=client, budget=0.01
            )

    result = asyncio.run(exercise())
    assert result["state"] == "unavailable"
    assert result["diagnostic_type"] == "TimeoutError"
    assert cancelled == [True]


def test_synchronous_overrun_also_withholds_correction(monkeypatch):
    ticks = iter([0.0, 0.5, 0.5])
    monkeypatch.setattr(flow, "perf_counter", lambda: next(ticks))
    text = "She go to work."
    result = run(text, evidence(text, "go", ["goes"], "HE_VERB_AGR"))
    assert result["state"] == "unavailable"
    assert result["diagnostic_type"] == "TimeoutError" and result["seconds"] == 0.5


def test_owned_client_disables_environment_proxy_and_shares_budget(monkeypatch):
    text = "Did you visited the castle?"
    raw = evidence(text, "visited", ["visit"])
    original_factory = httpx.AsyncClient
    configurations = []

    def factory(**options):
        configurations.append(options)
        return original_factory(
            **options,
            transport=httpx.MockTransport(
                lambda request: httpx.Response(200, json=raw)
            ),
        )

    monkeypatch.setattr(flow.httpx, "AsyncClient", factory)
    result = asyncio.run(flow.get_correction(text, budget=0.15))
    assert result["state"] == "offered"
    assert configurations == [{"trust_env": False, "timeout": 0.15}]


@pytest.mark.parametrize("mode", ["offline", "http_error", "invalid_json"])
def test_service_failure_returns_only_diagnostic_type(mode):
    async def exercise():
        def handler(request):
            if mode == "offline":
                raise httpx.ConnectError("private service detail", request=request)
            if mode == "http_error":
                return httpx.Response(503, text="private service detail")
            return httpx.Response(200, text="private service detail")

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await flow.get_correction("She go to work.", client=client)

    result = asyncio.run(exercise())
    assert result["state"] == "unavailable"
    assert "private service detail" not in str(result)


@pytest.mark.parametrize(
    "text,budget", [("", 0.2), (None, 0.2), ("x" * 1001, 0.2), ("Hi", 0), ("Hi", 1)]
)
def test_invalid_input_is_rejected_before_network(text, budget):
    with pytest.raises(ValueError):
        asyncio.run(flow.get_correction(text, budget=budget))
