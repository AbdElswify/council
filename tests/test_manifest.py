# tests/test_manifest.py
import json
from pathlib import Path

import pytest

import manifest


VALID = {
    "specialty": "API schema designer",
    "summary": "Defined OpenAPI 3.0 spec for user service.",
    "artifacts": ["artifacts/openapi.yaml"],
    "files_written": ["artifacts/openapi.yaml"],
    "contract_concerns": [],
    "seams_touched": ["GET /users/{id} response shape"],
}


def test_roundtrip(tmp_path):
    path = tmp_path / "manifest.json"
    manifest.write(path, VALID)
    assert manifest.read(path) == VALID

def test_validate_missing_field():
    bad = {k: v for k, v in VALID.items() if k != "summary"}
    with pytest.raises(manifest.ManifestError, match="missing required field: summary"):
        manifest.validate(bad)

def test_validate_wrong_type():
    bad = dict(VALID, artifacts="not a list")
    with pytest.raises(manifest.ManifestError, match="artifacts must be a list"):
        manifest.validate(bad)

def test_read_invalid_json(tmp_path):
    path = tmp_path / "manifest.json"
    path.write_text("not json", encoding="utf-8")
    with pytest.raises(manifest.ManifestError, match="invalid JSON"):
        manifest.read(path)


# --- Fix 5a: nested element shape enforcement ---

def test_artifacts_must_contain_strings():
    bad = dict(VALID, artifacts=["artifacts/openapi.yaml", "artifacts/schema.json", 42])
    with pytest.raises(manifest.ManifestError, match=r"artifacts\[2\] must be a string"):
        manifest.validate(bad)

def test_seams_touched_must_contain_strings():
    bad = dict(VALID, seams_touched=[None])
    with pytest.raises(manifest.ManifestError, match=r"seams_touched\[0\] must be a string"):
        manifest.validate(bad)

def test_contract_concerns_item_must_be_dict():
    bad = dict(VALID, contract_concerns=["just a string"])
    with pytest.raises(manifest.ManifestError, match=r"contract_concerns\[0\] must be an object"):
        manifest.validate(bad)

def test_contract_concerns_item_missing_severity():
    bad = dict(VALID, contract_concerns=[{"issue": "missing sev"}])
    with pytest.raises(manifest.ManifestError, match=r"contract_concerns\[0\] missing 'severity'"):
        manifest.validate(bad)

def test_contract_concerns_item_invalid_severity():
    bad = dict(VALID, contract_concerns=[{"severity": "critical", "issue": "bad sev"}])
    with pytest.raises(
        manifest.ManifestError,
        match=r"contract_concerns\[0\]\.severity must be 'blocker' or 'should-fix'",
    ):
        manifest.validate(bad)

def test_contract_concerns_item_missing_issue():
    bad = dict(VALID, contract_concerns=[{"severity": "blocker"}])
    with pytest.raises(manifest.ManifestError, match=r"contract_concerns\[0\] missing 'issue'"):
        manifest.validate(bad)


# --- Fix 7-schema: files_written field ---

def test_files_written_required():
    bad = {k: v for k, v in VALID.items() if k != "files_written"}
    with pytest.raises(manifest.ManifestError, match="missing required field: files_written"):
        manifest.validate(bad)

def test_files_written_must_be_list():
    bad = dict(VALID, files_written="artifacts/openapi.yaml")
    with pytest.raises(manifest.ManifestError, match="files_written must be a list"):
        manifest.validate(bad)

def test_files_written_items_must_be_strings():
    bad = dict(VALID, files_written=["artifacts/openapi.yaml", 7])
    with pytest.raises(manifest.ManifestError, match=r"files_written\[1\] must be a string"):
        manifest.validate(bad)
