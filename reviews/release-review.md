# Independent release review

**Verdict: FAIL**

**Reviewed PR head:** `9ddcfbbb1fc667a71f0f71e4fb139d24e43249d4`  
**Branch:** `feat/eval-slice-gate-v0.1.0`  
**Contract:** `CONTRACT.md`, frozen 2026-10-10 11:06:04 EDT  
**Scope:** Independent review of the frozen contract, implementation, tests, installed CLI, examples, documentation, and CI. No product files were changed.

## Finding

The bundled quickstart example does not pass, despite two user-facing claims that it does:

- `README.md` says: “The synthetic example exits `0`”.
- `LAUNCH.md` says the bundled policy/results “demonstrate an overall pass”.

On the reviewed SHA, the installed command exits `1` and reports `status: fail`. The `general` slice has 2 passing rows out of 3, while its required decimal threshold is `0.666667`. Exact rational comparison correctly finds `2/3 < 0.666667`. The adversarial and Unicode slices pass their own thresholds. This makes the published quickstart instructions and launch note inaccurate and warrants a release-blocking correction. Per review scope, no fix was made.

Reproduction from the repository root after the fresh install below:

```powershell
eval-slice-gate examples/results.jsonl examples/policy.json
```

Observed stdout:

```json
{"status":"fail","slices":[{"index":0,"count":3,"passed":2,"count_ok":true,"rate_ok":false},{"index":1,"count":2,"passed":1,"count_ok":true,"rate_ok":true},{"index":2,"count":1,"passed":1,"count_ok":true,"rate_ok":true}]}
```

Observed exit code: `1`.

## Independent verification

Fresh install in an external temporary environment using Python `3.13.1`:

```powershell
python -m venv "$env:TEMP\eval-slice-review-20261011"
& "$env:TEMP\eval-slice-review-20261011\Scripts\python.exe" -m pip install -e "C:\Users\hshre\OneDrive\Documents\42 - Agents\Codex\MeaningfulGitContributionGardener\automation-runs\eval-slice-gate[test]"
& "$env:TEMP\eval-slice-review-20261011\Scripts\python.exe" -m pytest -q -ra
```

Result: `29 passed in 1.13s`; no skips.

Direct installed console-script probes (`%TEMP%\eval-slice-review-20261011\Scripts\eval-slice-gate.exe`, with UTF-8 inputs written without a BOM):

| Probe | Exit | Result |
|---|---:|---|
| One declared row passes a 100% gate | 0 | `{"status":"pass","slices":[{"index":0,"count":1,"passed":1,"count_ok":true,"rate_ok":true}]}` |
| One declared row fails a 100% gate | 1 | `{"status":"fail","slices":[{"index":0,"count":1,"passed":0,"count_ok":true,"rate_ok":false}]}` |
| Unknown input label `secret-marker` | 2 | `{"status":"invalid_input"}`; stderr empty and marker absent |
| Duplicate key in malformed policy, with secret markers in inputs | 2 | `{"status":"invalid_input"}`; stderr empty and markers absent |
| Exact 1/3 result at threshold `0.333333` | 0 | Pass |
| Exact 1/3 result at threshold `0.333334` | 1 | Fail |
| Bundled adversarial and Unicode example | 1 | Output shown above; general slice fails as documented in finding |
| `--help` | 0 | Standard argparse usage shown |

The inspected implementation rejects duplicate keys at all object depths, nonstandard JSON constants, malformed UTF-8, unknown keys/slices, invalid rate forms, and booleans as `min_count`; it parses all inputs before emitting the report and uses `fractions.Fraction` for comparisons. The tests exercise these cases, newline variants, Unicode labels, empty results, no-echo output, CLI exit paths, and the rational boundary.

## CI and limits

`gh pr checks 2 --repo Hardik-S/eval-slice-gate` reported GitGuardian pass and eight passing matrix jobs across two workflow runs: Ubuntu and Windows on Python 3.10 and 3.13. `.github/workflows/ci.yml` defines the same four-platform/version combinations and installs `.[test]` before pytest.

The local independent install/run was on Windows with Python 3.13.1 only; the other OS/version combinations rely on the observed CI checks. This review did not modify code, rerun remote CI, merge, tag, or publish a release. CI and the 29 passing tests do not cover the contradictory quickstart/launch claim identified above.

## Publish preflight

The shared preflight reported account `Hardik-S`, target `Hardik-S/eval-slice-gate`, remote `origin` at the matching GitHub repository, and `auth-ok,dirty-worktree`. The only dirty path was the owned `reviews/` directory containing this report. Org/team/project was `none`; public/private ACL state was unknown. The commit and push are scoped to `reviews/release-review.md`.
