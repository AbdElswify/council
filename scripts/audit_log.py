"""Append-only JSONL audit history for a single worker."""
import json
from datetime import datetime
from pathlib import Path


def append(path: Path, verdict: dict) -> None:
    entry = dict(verdict)
    entry["timestamp"] = datetime.utcnow().isoformat(timespec="seconds")
    with Path(path).open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, sort_keys=True) + "\n")


def read(path: Path) -> list[dict]:
    text = Path(path).read_text(encoding="utf-8")
    return [json.loads(line) for line in text.splitlines() if line.strip()]
