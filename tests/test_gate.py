import json
import subprocess
import sys
from fractions import Fraction

import pytest

from eval_slice_gate.core import InvalidInput, evaluate, parse_policy, parse_results


def policy_bytes(entries=None):
    return json.dumps({"slices": entries or [
        {"name": "alpha", "min_count": 3, "min_pass_rate": "0.666667"},
        {"name": "β", "min_count": 1, "min_pass_rate": "1"},
    ]}, ensure_ascii=False).encode()


def valid_policy():
    return parse_policy(policy_bytes())


def results_bytes(rows):
    return "\n".join(json.dumps(row, ensure_ascii=False) for row in rows).encode()


def test_exact_boundary_is_rational_not_rounded_float():
    policy = [("x", 1, Fraction("0.333334"))]
    assert evaluate(policy, [("x", True), ("x", False), ("x", False)])["status"] == "fail"
    assert evaluate([("x", 1, Fraction("0.333333"))], [("x", True), ("x", False), ("x", False)])["status"] == "pass"


def test_results_order_follows_policy_and_missing_slice_fails_both():
    report = evaluate(valid_policy(), [("alpha", True), ("alpha", True), ("alpha", True)])
    assert report == {"status": "fail", "slices": [
        {"index": 0, "count": 3, "passed": 3, "count_ok": True, "rate_ok": True},
        {"index": 1, "count": 0, "passed": 0, "count_ok": False, "rate_ok": False},
    ]}


@pytest.mark.parametrize("data", [
    b'{"slices":[],"slices":[]}',
    b'{"slices":[{"name":"x","name":"y","min_count":1,"min_pass_rate":"1"}]}',
    b'{"slices":[{"name":"x","min_count":1,"min_pass_rate":"1","extra":0}]}',
    b'{"slices":[{"name":"x","min_count":true,"min_pass_rate":"1"}]}',
    b'{"slices":[{"name":"x","min_count":1,"min_pass_rate":1}]}',
    b'{"slices":[{"name":"x","min_count":1,"min_pass_rate":"1.1"}]}',
    b'{"slices":[{"name":"x","min_count":1,"min_pass_rate":"0.1234567"}]}',
    b'{"slices":[{"name":"x","min_count":1,"min_pass_rate":"1.00"}],"x":NaN}',
    b'{"slices":[{"name":"x","min_count":1,"min_pass_rate":"1"}],"nested":{"a":1,"a":2}}',
    b'{"slices":[{"name":"x","min_count":1,"min_pass_rate":"1"}]}\xff',
])
def test_rejects_invalid_policies(data):
    with pytest.raises(InvalidInput):
        parse_policy(data)


def test_policy_distinguishes_bool_from_int_and_requires_unique_names():
    for entries in [
        [{"name": "x", "min_count": False, "min_pass_rate": "0"}],
        [{"name": "x", "min_count": 1, "min_pass_rate": "0"}, {"name": "x", "min_count": 1, "min_pass_rate": "0"}],
    ]:
        with pytest.raises(InvalidInput):
            parse_policy(policy_bytes(entries))


@pytest.mark.parametrize("text", [
    '{"slice":"alpha","passed":1}',
    '{"slice":"unknown","passed":true}',
    '{"slice":"alpha","passed":true,"extra":0}',
    '{"slice":"alpha","passed":true,"passed":false}',
    '{"slice":"alpha","passed":true}\n\n',
    '{"slice":"alpha","passed":true}\nnope',
    '{"slice":"alpha","passed":true}garbage',
    '{"slice":"alpha","passed":true}\n{',
    '{"slice":"alpha","passed":true,"x":Infinity}',
])
def test_rejects_invalid_results(text):
    with pytest.raises(InvalidInput):
        parse_results(text.encode(), {"alpha", "β"})


def test_empty_file_is_valid_and_unicode_label_is_supported():
    assert parse_results(b"", {"alpha"}) == []
    assert parse_results('{"slice":"β","passed":true}'.encode(), {"β"}) == [("β", True)]


@pytest.mark.parametrize("newline", ["\n", "\r", "\r\n"])
def test_supported_newline_modes(newline):
    data = newline.join(['{"slice":"alpha","passed":true}', '{"slice":"β","passed":false}']).encode()
    assert parse_results(data, {"alpha", "β"}) == [("alpha", True), ("β", False)]


def test_empty_crlf_file_and_terminal_newline():
    assert parse_results(b"", {"x"}) == []
    assert parse_results(b'{"slice":"x","passed":true}\r\n', {"x"}) == [("x", True)]


def run_cli(tmp_path, policy, results, *args):
    p = tmp_path / "policy.json"
    r = tmp_path / "results.jsonl"
    p.write_bytes(policy)
    r.write_bytes(results)
    return subprocess.run([sys.executable, "-m", "eval_slice_gate.cli", *args, str(r), str(p)],
                          capture_output=True, text=True)


def test_console_pass_fail_invalid_and_noecho_paths(tmp_path):
    good = run_cli(tmp_path, b'{"slices":[{"name":"secret-label","min_count":1,"min_pass_rate":"1"}]}',
                   b'{"slice":"secret-label","passed":true}')
    assert (good.returncode, good.stdout, good.stderr) == (0, '{"status":"pass","slices":[{"index":0,"count":1,"passed":1,"count_ok":true,"rate_ok":true}]}\n', "")
    fail = run_cli(tmp_path, b'{"slices":[{"name":"secret-label","min_count":2,"min_pass_rate":"1"}]}',
                   b'{"slice":"secret-label","passed":false}')
    assert fail.returncode == 1 and json.loads(fail.stdout)["status"] == "fail" and fail.stderr == ""
    invalid = run_cli(tmp_path, b'{"slices":[{"name":"secret-label","min_count":1,"min_pass_rate":"1"}]}',
                      b'{"slice":"not-to-echo","passed":false}')
    assert (invalid.returncode, invalid.stdout, invalid.stderr) == (2, '{"status":"invalid_input"}\n', "")
    bad_args = subprocess.run([sys.executable, "-m", "eval_slice_gate.cli"], capture_output=True, text=True)
    assert (bad_args.returncode, bad_args.stdout, bad_args.stderr) == (2, '{"status":"invalid_input"}\n', "")


def test_help_uses_standard_argparse_output():
    result = subprocess.run([sys.executable, "-m", "eval_slice_gate.cli", "--help"], capture_output=True, text=True)
    assert result.returncode == 0 and "usage:" in result.stdout and result.stderr == ""
