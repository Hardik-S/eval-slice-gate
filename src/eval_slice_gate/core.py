"""Strict parsers and deterministic slice-gate evaluation."""

from __future__ import annotations

import json
import re
from fractions import Fraction
from typing import Any


class InvalidInput(ValueError):
    """An input file does not satisfy the public contract."""


_RATE = re.compile(r"(?:0(?:\.[0-9]{1,6})?|1(?:\.0{1,6})?)\Z")


def _pairs_without_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise InvalidInput
        result[key] = value
    return result


def _reject_constant(_: str) -> None:
    raise InvalidInput


def _json_loads(text: str) -> Any:
    try:
        return json.loads(
            text,
            object_pairs_hook=_pairs_without_duplicates,
            parse_constant=_reject_constant,
        )
    except (json.JSONDecodeError, RecursionError, ValueError) as exc:
        raise InvalidInput from exc


def parse_policy(data: bytes) -> list[tuple[str, int, Fraction]]:
    try:
        text = data.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise InvalidInput from exc
    document = _json_loads(text)
    if not isinstance(document, dict) or set(document) != {"slices"}:
        raise InvalidInput
    entries = document["slices"]
    if not isinstance(entries, list) or not entries:
        raise InvalidInput
    policy: list[tuple[str, int, Fraction]] = []
    names: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != {"name", "min_count", "min_pass_rate"}:
            raise InvalidInput
        name, minimum, rate = entry["name"], entry["min_count"], entry["min_pass_rate"]
        if not isinstance(name, str) or not name or name in names:
            raise InvalidInput
        if isinstance(minimum, bool) or not isinstance(minimum, int) or minimum < 1:
            raise InvalidInput
        if not isinstance(rate, str) or _RATE.fullmatch(rate) is None:
            raise InvalidInput
        names.add(name)
        policy.append((name, minimum, Fraction(rate)))
    return policy


def parse_results(data: bytes, names: set[str]) -> list[tuple[str, bool]]:
    try:
        text = data.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise InvalidInput from exc
    results: list[tuple[str, bool]] = []
    if not text:
        return results
    # Only the three contracted newline forms separate records; splitlines()
    # would also treat several Unicode separators as record boundaries.
    lines = re.split(r"\r\n|\r|\n", text)
    if lines[-1] == "":
        lines.pop()  # One terminal line ending terminates the last record.
    for line in lines:
        if not line.strip():
            raise InvalidInput
        row = _json_loads(line)
        if not isinstance(row, dict) or set(row) != {"slice", "passed"}:
            raise InvalidInput
        label, passed = row["slice"], row["passed"]
        if not isinstance(label, str) or label not in names or not isinstance(passed, bool):
            raise InvalidInput
        results.append((label, passed))
    return results


def evaluate(policy: list[tuple[str, int, Fraction]], results: list[tuple[str, bool]]) -> dict[str, Any]:
    counts = {name: 0 for name, _, _ in policy}
    passed_counts = counts.copy()
    for name, passed in results:
        counts[name] += 1
        passed_counts[name] += int(passed)
    checks: list[dict[str, Any]] = []
    overall = True
    for index, (name, minimum, threshold) in enumerate(policy):
        count, passed = counts[name], passed_counts[name]
        count_ok = count >= minimum
        rate_ok = count > 0 and Fraction(passed, count) >= threshold
        checks.append({"index": index, "count": count, "passed": passed,
                       "count_ok": count_ok, "rate_ok": rate_ok})
        overall = overall and count_ok and rate_ok
    return {"status": "pass" if overall else "fail", "slices": checks}
