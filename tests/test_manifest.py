# tests/test_manifest.py
import json
from pathlib import Path

import pytest

import manifest


VALID = {
    "specialty": "API schema designer",
    "summary": "Defined OpenAPI 3.0 spec for user service.",
    "artifacts": ["artifacts/openapi.yaml"],
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
