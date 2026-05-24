# scripts/manifest.py
"""Read, write, and validate a council worker manifest."""
import json
from pathlib import Path
from typing import Any


REQUIRED_FIELDS = {
    "specialty": str,
    "summary": str,
    "artifacts": list,
    "files_written": list,
    "contract_concerns": list,
    "seams_touched": list,
}

VALID_CONCERN_SEVERITIES = {"blocker", "should-fix"}


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

    # Element-shape checks for list fields.
    for i, item in enumerate(data["artifacts"]):
        if not isinstance(item, str):
            raise ManifestError(f"artifacts[{i}] must be a string")

    for i, item in enumerate(data["files_written"]):
        if not isinstance(item, str):
            raise ManifestError(f"files_written[{i}] must be a string")

    for i, item in enumerate(data["seams_touched"]):
        if not isinstance(item, str):
            raise ManifestError(f"seams_touched[{i}] must be a string")

    for i, item in enumerate(data["contract_concerns"]):
        if not isinstance(item, dict):
            raise ManifestError(f"contract_concerns[{i}] must be an object")
        if "severity" not in item:
            raise ManifestError(f"contract_concerns[{i}] missing 'severity'")
        if item["severity"] not in VALID_CONCERN_SEVERITIES:
            raise ManifestError(
                f"contract_concerns[{i}].severity must be 'blocker' or 'should-fix'"
            )
        if "issue" not in item:
            raise ManifestError(f"contract_concerns[{i}] missing 'issue'")
        if not isinstance(item["issue"], str):
            raise ManifestError(f"contract_concerns[{i}].issue must be a string")


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
