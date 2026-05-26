"""Append-only JSONL audit history for a single worker."""
import json
from datetime import datetime, timezone
from pathlib import Path


def append(path: Path, verdict: dict) -> None:
    # Concurrency note: each worker owns exactly one audit_history.jsonl, and
    # the Mayor (main session) appends to it sequentially -- one audit verdict
    # per round, never two writers at once. So no file lock is needed here.
    # If that invariant ever changes (e.g. parallel auditors writing the same
    # file), this single open()/write() is NOT atomic across processes and
    # would need an OS-level lock or per-writer temp-file-then-append. The one
    # line written per call IS small enough to be a single write() syscall,
    # so interleaving within a line is not a concern; interleaving between
    # lines (lost/duplicated entries) would be.
    entry = dict(verdict)
    # Timezone-aware UTC; datetime.utcnow() is deprecated in Python 3.12+.
    entry["timestamp"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with Path(path).open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, sort_keys=True) + "\n")


def read(path: Path) -> list[dict]:
    text = Path(path).read_text(encoding="utf-8")
    return [json.loads(line) for line in text.splitlines() if line.strip()]
