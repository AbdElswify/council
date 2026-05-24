import json
from pathlib import Path

import audit_log


VERDICT_1 = {
    "verdict": "NEEDS_REVISION",
    "round": 1,
    "pass": 1,
    "findings": [{"severity": "blocker", "loc": "x.py:1", "issue": "..."}],
    "contract_concerns": [],
}

VERDICT_2 = {
    "verdict": "APPROVED",
    "round": 1,
    "pass": 2,
    "findings": [],
    "contract_concerns": [],
}


def test_append_creates_file(tmp_path):
    history = tmp_path / "audit_history.jsonl"
    audit_log.append(history, VERDICT_1)
    assert history.exists()

def test_append_adds_timestamp(tmp_path):
    history = tmp_path / "audit_history.jsonl"
    audit_log.append(history, VERDICT_1)
    line = json.loads(history.read_text().strip())
    assert "timestamp" in line
    assert line["verdict"] == "NEEDS_REVISION"

def test_read_returns_list_in_order(tmp_path):
    history = tmp_path / "audit_history.jsonl"
    audit_log.append(history, VERDICT_1)
    audit_log.append(history, VERDICT_2)
    entries = audit_log.read(history)
    assert len(entries) == 2
    assert entries[0]["verdict"] == "NEEDS_REVISION"
    assert entries[1]["verdict"] == "APPROVED"

def test_read_empty_returns_empty_list(tmp_path):
    history = tmp_path / "audit_history.jsonl"
    history.write_text("", encoding="utf-8")
    assert audit_log.read(history) == []
