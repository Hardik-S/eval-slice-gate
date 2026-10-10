# v0.1.0 launch note

Eval Slice Gate provides a small, offline guard against missing or underperforming declared evaluation slices. It accepts a strict JSON policy and JSONL assertions, then emits a deterministic compact JSON report with exact pass-rate comparisons.

The bundled policy/results are synthetic and demonstrate an overall pass with multiple slices, including an adversarial ambiguity slice and a Unicode label. The CLI does not execute or assess an evaluator; a `passed` value is trusted as supplied. See README for the complete input contract, exit codes, privacy behavior, and limitations.

For a fresh installation, create and activate a Python 3.10+ virtual environment, run `python -m pip install .`, then run `eval-slice-gate examples/results.jsonl examples/policy.json`. The command returns `0` for pass, `1` for valid gate failure, and `2` for invalid input or misuse.
