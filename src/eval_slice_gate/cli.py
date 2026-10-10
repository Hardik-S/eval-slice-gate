"""Command-line interface for eval-slice-gate."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .core import InvalidInput, evaluate, parse_policy, parse_results


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise InvalidInput from None


def main() -> int:
    parser = _Parser(prog="eval-slice-gate", description="Check JSONL evaluation results against a slice policy.")
    parser.add_argument("results", help="strict UTF-8 JSONL results file")
    parser.add_argument("policy", help="strict UTF-8 JSON policy file")
    try:
        args = parser.parse_args()
        policy = parse_policy(Path(args.policy).read_bytes())
        results = parse_results(Path(args.results).read_bytes(), {name for name, _, _ in policy})
        output = evaluate(policy, results)
        code = 0 if output["status"] == "pass" else 1
    except (InvalidInput, OSError, UnicodeError, RecursionError):
        output, code = {"status": "invalid_input"}, 2
    sys.stdout.write(json.dumps(output, separators=(",", ":")) + "\n")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
