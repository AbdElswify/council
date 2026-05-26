import pytest

import parse_verdict


CLEAN = '''Some preamble.

```json
{"verdict": "APPROVED", "round": 1, "pass": 2, "findings": [], "contract_concerns": []}
```

Some postamble.'''


def test_extracts_clean_block():
    v = parse_verdict.parse(CLEAN)
    assert v["verdict"] == "APPROVED"

def test_no_block_raises():
    with pytest.raises(parse_verdict.VerdictError, match="no fenced JSON"):
        parse_verdict.parse("no block here")

def test_malformed_json_raises():
    bad = "```json\n{not valid}\n```"
    with pytest.raises(parse_verdict.VerdictError, match="invalid JSON"):
        parse_verdict.parse(bad)

def test_missing_verdict_key_raises():
    bad = '```json\n{"round": 1, "pass": 2, "findings": [], "contract_concerns": []}\n```'
    with pytest.raises(parse_verdict.VerdictError, match="missing 'verdict'"):
        parse_verdict.parse(bad)

def test_invalid_verdict_value_raises():
    bad = '```json\n{"verdict": "MAYBE", "round": 1, "pass": 2, "findings": [], "contract_concerns": []}\n```'
    with pytest.raises(parse_verdict.VerdictError, match="verdict must be"):
        parse_verdict.parse(bad)

def test_picks_last_block_if_multiple():
    text = (
        '```json\n{"verdict": "NEEDS_REVISION", "round": 1, "pass": 2, "findings": [], "contract_concerns": []}\n```\n'
        "thinking out loud\n"
        '```json\n{"verdict": "APPROVED", "round": 1, "pass": 2, "findings": [], "contract_concerns": []}\n```'
    )
    assert parse_verdict.parse(text)["verdict"] == "APPROVED"


# --- Fix 5b: enforce round, pass, findings, contract_concerns, notes ---

def test_missing_round_raises():
    bad = '```json\n{"verdict": "APPROVED", "pass": 2, "findings": [], "contract_concerns": []}\n```'
    with pytest.raises(parse_verdict.VerdictError, match="missing 'round'"):
        parse_verdict.parse(bad)

def test_round_wrong_type_raises():
    bad = '```json\n{"verdict": "APPROVED", "round": "1", "pass": 2, "findings": [], "contract_concerns": []}\n```'
    with pytest.raises(parse_verdict.VerdictError, match="round must be an int"):
        parse_verdict.parse(bad)

def test_round_zero_raises():
    bad = '```json\n{"verdict": "APPROVED", "round": 0, "pass": 2, "findings": [], "contract_concerns": []}\n```'
    with pytest.raises(parse_verdict.VerdictError, match="round must be >= 1"):
        parse_verdict.parse(bad)

def test_missing_pass_raises():
    bad = '```json\n{"verdict": "APPROVED", "round": 1, "findings": [], "contract_concerns": []}\n```'
    with pytest.raises(parse_verdict.VerdictError, match="missing 'pass'"):
        parse_verdict.parse(bad)

def test_pass_invalid_value_raises():
    bad = '```json\n{"verdict": "APPROVED", "round": 1, "pass": 3, "findings": [], "contract_concerns": []}\n```'
    with pytest.raises(parse_verdict.VerdictError, match="pass must be 1 or 2"):
        parse_verdict.parse(bad)

def test_missing_findings_raises():
    bad = '```json\n{"verdict": "APPROVED", "round": 1, "pass": 2, "contract_concerns": []}\n```'
    with pytest.raises(parse_verdict.VerdictError, match="missing 'findings'"):
        parse_verdict.parse(bad)

def test_findings_wrong_type_raises():
    bad = '```json\n{"verdict": "APPROVED", "round": 1, "pass": 2, "findings": {}, "contract_concerns": []}\n```'
    with pytest.raises(parse_verdict.VerdictError, match="findings must be a list"):
        parse_verdict.parse(bad)

def test_missing_contract_concerns_raises():
    bad = '```json\n{"verdict": "APPROVED", "round": 1, "pass": 2, "findings": []}\n```'
    with pytest.raises(parse_verdict.VerdictError, match="missing 'contract_concerns'"):
        parse_verdict.parse(bad)

def test_notes_wrong_type_raises():
    bad = '```json\n{"verdict": "APPROVED", "round": 1, "pass": 2, "findings": [], "contract_concerns": [], "notes": 5}\n```'
    with pytest.raises(parse_verdict.VerdictError, match="notes must be a string"):
        parse_verdict.parse(bad)

def test_notes_absent_is_fine():
    text = '```json\n{"verdict": "APPROVED", "round": 1, "pass": 2, "findings": [], "contract_concerns": []}\n```'
    v = parse_verdict.parse(text)
    assert "notes" not in v


# --- Fence-regex robustness: closing fence without a preceding newline ---

def test_no_trailing_newline_before_closing_fence():
    # JSON ends right against the closing fence (no blank line in between).
    text = '```json\n{"verdict": "APPROVED", "round": 1, "pass": 2, "findings": [], "contract_concerns": []}```'
    assert parse_verdict.parse(text)["verdict"] == "APPROVED"

def test_multiline_body_without_trailing_newline():
    text = (
        "```json\n"
        "{\n"
        '  "verdict": "NEEDS_REVISION",\n'
        '  "round": 2,\n'
        '  "pass": 1,\n'
        '  "findings": [{"severity": "blocker", "loc": "x.py:1", "issue": "boom"}],\n'
        '  "contract_concerns": []\n'
        "}```"
    )
    v = parse_verdict.parse(text)
    assert v["verdict"] == "NEEDS_REVISION"
    assert v["round"] == 2


# --- Item 2: findings-empty-iff-APPROVED + findings[] element shape ---

def _verdict(verdict, findings):
    import json
    return "```json\n" + json.dumps({
        "verdict": verdict, "round": 1, "pass": 2,
        "findings": findings, "contract_concerns": [],
    }) + "\n```"

def test_approved_with_nonempty_findings_raises():
    bad = _verdict("APPROVED", [{"severity": "should-fix", "issue": "x"}])
    with pytest.raises(parse_verdict.VerdictError, match="APPROVED.*empty findings"):
        parse_verdict.parse(bad)

def test_needs_revision_with_empty_findings_raises():
    bad = _verdict("NEEDS_REVISION", [])
    with pytest.raises(parse_verdict.VerdictError, match="NEEDS_REVISION.*at least one finding"):
        parse_verdict.parse(bad)

def test_finding_not_object_raises():
    bad = _verdict("NEEDS_REVISION", ["oops"])
    with pytest.raises(parse_verdict.VerdictError, match=r"findings\[0\] must be an object"):
        parse_verdict.parse(bad)

def test_finding_missing_severity_raises():
    bad = _verdict("NEEDS_REVISION", [{"issue": "x"}])
    with pytest.raises(parse_verdict.VerdictError, match=r"findings\[0\] missing 'severity'"):
        parse_verdict.parse(bad)

def test_finding_invalid_severity_raises():
    bad = _verdict("NEEDS_REVISION", [{"severity": "critical", "issue": "x"}])
    with pytest.raises(parse_verdict.VerdictError, match="severity must be"):
        parse_verdict.parse(bad)

def test_finding_missing_issue_raises():
    bad = _verdict("NEEDS_REVISION", [{"severity": "blocker"}])
    with pytest.raises(parse_verdict.VerdictError, match=r"findings\[0\] missing 'issue'"):
        parse_verdict.parse(bad)

def test_finding_issue_wrong_type_raises():
    bad = _verdict("NEEDS_REVISION", [{"severity": "blocker", "issue": 5}])
    with pytest.raises(parse_verdict.VerdictError, match="issue must be a string"):
        parse_verdict.parse(bad)

def test_finding_loc_wrong_type_raises():
    bad = _verdict("NEEDS_REVISION", [{"severity": "blocker", "issue": "x", "loc": 5}])
    with pytest.raises(parse_verdict.VerdictError, match="loc must be a string"):
        parse_verdict.parse(bad)

def test_valid_needs_revision_with_finding_passes():
    text = _verdict("NEEDS_REVISION", [{"severity": "blocker", "loc": "x.py:1", "issue": "boom"}])
    v = parse_verdict.parse(text)
    assert v["verdict"] == "NEEDS_REVISION"
    assert v["findings"][0]["severity"] == "blocker"

def test_finding_loc_optional():
    text = _verdict("NEEDS_REVISION", [{"severity": "should-fix", "issue": "no loc needed"}])
    assert parse_verdict.parse(text)["verdict"] == "NEEDS_REVISION"

def test_crlf_line_endings_parse():
    text = (
        "```json\r\n"
        '{"verdict": "APPROVED", "round": 1, "pass": 2, "findings": [], "contract_concerns": []}'
        "\r\n```"
    )
    assert parse_verdict.parse(text)["verdict"] == "APPROVED"

def test_last_block_wins_when_final_block_has_no_trailing_newline():
    text = (
        '```json\n{"verdict": "NEEDS_REVISION", "round": 1, "pass": 2, "findings": [], "contract_concerns": []}\n```\n'
        "thinking out loud\n"
        '```json\n{"verdict": "APPROVED", "round": 1, "pass": 2, "findings": [], "contract_concerns": []}```'
    )
    assert parse_verdict.parse(text)["verdict"] == "APPROVED"
