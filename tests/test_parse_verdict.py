import pytest

import parse_verdict


CLEAN = '''Some preamble.

```json
{"verdict": "APPROVED", "round": 1, "findings": [], "contract_concerns": []}
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
    bad = '```json\n{"round": 1}\n```'
    with pytest.raises(parse_verdict.VerdictError, match="missing 'verdict'"):
        parse_verdict.parse(bad)

def test_invalid_verdict_value_raises():
    bad = '```json\n{"verdict": "MAYBE"}\n```'
    with pytest.raises(parse_verdict.VerdictError, match="verdict must be"):
        parse_verdict.parse(bad)

def test_picks_last_block_if_multiple():
    text = (
        "```json\n{\"verdict\": \"NEEDS_REVISION\"}\n```\n"
        "thinking out loud\n"
        "```json\n{\"verdict\": \"APPROVED\"}\n```"
    )
    assert parse_verdict.parse(text)["verdict"] == "APPROVED"
