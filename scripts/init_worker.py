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
    (worker_dir / "artifacts").mkdir(parents=True, exist_ok=False)
    (worker_dir / "audit_history.jsonl").write_text("", encoding="utf-8")
    return worker_dir


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: init_worker.py <run_dir> <slug>", file=sys.stderr)
        sys.exit(2)
    print(init_worker(Path(sys.argv[1]), sys.argv[2]))
