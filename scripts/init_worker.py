"""Create per-worker subdirectories under a run directory."""
import re
from pathlib import Path


SAFE_SLUG = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")


def init_worker(run_dir: Path, slug: str) -> Path:
    if not SAFE_SLUG.match(slug):
        raise ValueError(
            f"Unsafe worker slug {slug!r}: must match {SAFE_SLUG.pattern}"
        )
    worker_dir = Path(run_dir) / "workers" / slug
    # Idempotent: a worker is re-initialized on re-dispatch after an audit, so
    # calling this twice for the same slug must NOT clobber accumulated state.
    # exist_ok=True lets the dirs already be present; we create audit_history
    # only if it is missing so an existing append-only history is preserved.
    (worker_dir / "artifacts").mkdir(parents=True, exist_ok=True)
    history = worker_dir / "audit_history.jsonl"
    if not history.exists():
        history.write_text("", encoding="utf-8")
    return worker_dir


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: init_worker.py <run_dir> <slug>", file=sys.stderr)
        sys.exit(2)
    print(init_worker(Path(sys.argv[1]), sys.argv[2]))
