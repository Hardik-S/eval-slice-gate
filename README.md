# Eval Slice Gate

`eval-slice-gate` is an offline, standard-library Python CLI that checks whether every declared evaluation slice has enough examples and meets a minimum asserted pass rate. It is intended to reveal coverage gaps that an aggregate score can hide.

## Quickstart

Requires Python 3.10 or newer. Install the package and optional test tool in a fresh environment:

```console
python -m venv .venv
# Activate .venv using the command for your shell, then:
python -m pip install ".[test]"
eval-slice-gate examples/results.jsonl examples/policy.json
```

The synthetic example exits `0` and prints one compact JSON report. Exit `1` means valid inputs failed a gate; exit `2` means invalid input or command misuse. `--help` prints standard usage.

## Input contract

The policy is a strict UTF-8 JSON object with exactly one key, `slices`. Its nonempty array contains objects with exactly `name`, `min_count`, and `min_pass_rate`. Names are nonempty and unique. `min_count` is an integer of at least one (booleans do not count as integers). `min_pass_rate` is a string from `0` to `1`, with at most six decimal digits; a `1` threshold may contain only zeroes after the decimal point.

Results are strict UTF-8 JSON Lines. Every nonblank line must be exactly `{"slice":"declared name","passed":true}` or the same with `false`. Blank lines are invalid; an empty results file is valid. LF, CR, and CRLF separators are accepted. Duplicate keys, unknown keys/slices, malformed JSON/UTF-8, and nonstandard numeric constants such as NaN or Infinity invalidate the input. Both files are fully read and validated before a report is emitted.

## Output and privacy

Valid input produces exactly one JSON object on stdout: overall `status` and a `slices` array in policy order. Each slice reports zero-based `index`, `count`, `passed`, `count_ok`, and `rate_ok`. The pass rate is compared using exact rational arithmetic, without float rounding. Missing slices report zero counts and both checks false. Invalid input produces exactly `{"status":"invalid_input"}` and exit `2`; stderr remains empty except for standard `--help` output. Source labels, paths, values, parser exceptions, and JSON fragments are never included in reports.

## Limitations

The example data is synthetic. This tool does not run an evaluator, verify whether asserted booleans are truthful, infer slice membership, or deduplicate cases. It makes no guarantee about fairness, statistical significance, judge accuracy, or evaluation quality. Results and policy are buffered in memory; memory usage grows with the input. The runtime has no network or model dependencies.

## Development

```console
python -m pip install ".[test]"
python -m pytest
```

The CI matrix covers Ubuntu and Windows on Python 3.10 and 3.13.
