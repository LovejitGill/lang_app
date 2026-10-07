"""Versioned detection-gap extension; keep earlier frozen detectors intact."""

import copy
import json
import subprocess
import tempfile
from pathlib import Path

from benchmark import ROOT, utf16_span
from grammar_explanation_reasons import explain_with_reason

VARIANT = "broader-rules-gap-fixes-v1"
COUNT_RULE = "SPEAKWELL_COUNT_HEAD"
RULEFILE = ROOT / "rules/en-speakwell.xml"
JAVA = ROOT / ".tools/benchmark/jdk-21.0.12.1+1-jre/Contents/Home/bin/java"
CLI = ROOT / ".tools/benchmark/LanguageTool-6.6/languagetool-commandline.jar"
ALIASES = {"DID_PAST": "DID_BASEFORM", COUNT_RULE: "CD_NN"}


def explain_with_gaps(original, proposed, base_evidence, count_evidence):
    """Reuse existing reasoning; retain actual rule IDs after canonical mapping."""
    prior = explain_with_reason(original, proposed, base_evidence)
    if prior["state"] != "withheld":
        return {**prior, "evidence_source": "builtin"}
    if not isinstance(count_evidence, dict) or not isinstance(
        count_evidence.get("matches"), list
    ):
        raise TypeError("Malformed supplemental count evidence.")
    combined = copy.deepcopy(base_evidence)
    base_count = len(combined["matches"])
    combined["matches"].extend(copy.deepcopy(count_evidence["matches"]))
    source_rules = [match["rule"]["id"] for match in combined["matches"]]
    for index, match in enumerate(combined["matches"]):
        name = source_rules[index]
        # Builtin DID_PAST can only come from builtin evidence; custom matches
        # can only authorize our separately stored count rule.
        alias = ALIASES.get(name) if index < base_count and name == "DID_PAST" else None
        if index >= base_count:
            if name != COUNT_RULE:
                raise ValueError("Unexpected supplemental rule.")
            alias = "CD_NN"
        if alias:
            match["rule"]["id"] = alias
    result = explain_with_reason(original, proposed, combined)
    if result["state"] == "provisional":
        index = result["match_index"]
        result = {
            **result,
            "canonical_rule_id": result["rule_id"],
            "rule_id": source_rules[index],
            "evidence_source": "supplemental" if index >= base_count else "builtin",
        }
    return result


def split_count_matches(texts, raw):
    """Convert batch UTF-16 offsets to each exact input; reject crossing spans."""
    joined = "\n".join(texts)
    boundaries = []
    start = 0
    for text in texts:
        boundaries.append((start, start + len(text)))
        start += len(text) + 1
    result = [{"matches": []} for _ in texts]
    for match in raw["matches"]:
        if match["rule"]["id"] != COUNT_RULE:
            raise ValueError("Unexpected custom-rule output.")
        a, b = utf16_span(joined, match["offset"], match["length"])
        target = next(
            (i for i, (left, right) in enumerate(boundaries) if left <= a < b <= right),
            None,
        )
        if target is None:
            raise ValueError("Custom match crosses input boundary.")
        local = copy.deepcopy(match)
        left, _ = boundaries[target]
        local["offset"] = len(joined[left:a].encode("utf-16-le")) // 2
        local["length"] = len(joined[a:b].encode("utf-16-le")) // 2
        result[target]["matches"].append(local)
    return result


def collect_count_evidence(texts):
    """Batch an external XML rule with the already installed local Java runtime."""
    if not texts or any(
        not isinstance(t, str)
        or not t.strip()
        or len(t) > 1200
        or "\n" in t
        or "\r" in t
        for t in texts
    ):
        raise ValueError(
            "Expected nonempty, single-line texts of at most 1200 characters."
        )
    if not JAVA.exists() or not CLI.exists():
        raise FileNotFoundError("Install the documented local benchmark tools first.")
    with tempfile.TemporaryDirectory(prefix="speakwell-count-") as folder:
        path = Path(folder) / "inputs.txt"
        path.write_text("\n".join(texts), encoding="utf-8")
        process = subprocess.run(
            [
                str(JAVA),
                "-Xmx1g",
                "-jar",
                str(CLI),
                "-l",
                "en-US",
                "--json",
                "--rulefile",
                str(RULEFILE),
                "--enabledonly",
                "--enable",
                COUNT_RULE,
                str(path),
            ],
            capture_output=True,
            text=True,
            timeout=90,
            check=True,
        )
    raw = json.loads(process.stdout)
    if raw["software"]["version"] != "6.6" or raw.get("warnings", {}).get(
        "incompleteResults"
    ):
        raise ValueError("Incomplete results or wrong LanguageTool version.")
    return {
        "raw": raw,
        "stderr": process.stderr,
        "per_input": split_count_matches(texts, raw),
    }
