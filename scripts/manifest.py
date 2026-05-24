# scripts/manifest.py
"""Read, write, and validate a council worker manifest."""
import json
from pathlib import Path
from typing import Any


REQUIRED_FIELDS = {
    "specialty": str,
    "summary": str,
    "artifacts": list,
    "contract_concerns": list,
    "seams_touched": list,
}


class ManifestError(ValueError):
    pass


def validate(data: Any) -> None:
    if not isinstance(data, dict):
        raise ManifestError("manifest must be a JSON object")
    for field, typ in REQUIRED_FIELDS.items():
        if field not in data:
            raise ManifestError(f"missing required field: {field}")
        if not isinstance(data[field], typ):
            raise ManifestError(f"{field} must be a {typ.__name__}")


def read(path: Path) -> dict:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ManifestError(f"invalid JSON in {path}: {e}") from e
    validate(data)
    return data


def write(path: Path, data: dict) -> None:
    validate(data)
    Path(path).write_text(
        json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
