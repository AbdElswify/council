"""Initialize a per-run workspace under .council-runs/<run-id>/."""
from datetime import datetime, timezone
from pathlib import Path

import run_id


# How many fresh run_ids to try before giving up. A collision requires the
# same second AND the same 16-bit random suffix, so it is astronomically
# unlikely; a tiny bound is plenty and prevents an unbounded loop if the
# parent directory is somehow unwritable in a way that masquerades as a
# collision.
MAX_RUN_ID_ATTEMPTS = 8


class RunInitError(RuntimeError):
    pass


CONTRACT_TEMPLATE = """# Council Run {run_id}: Contract

## Task statement
{task}

## Shared interfaces
<!-- file paths, function signatures, data shapes, schemas -->

## Naming conventions
<!-- variable, file, identifier conventions -->

## Worker roster
| slug | specialty | scope | depends_on |
|---|---|---|---|

## Acceptance criteria
<!-- concrete, testable bullets -->
"""


def init_run(root: Path, task: str) -> Path:
    # Retry on the (astronomically unlikely) run_id collision. mkdir with
    # exist_ok=False is the atomic test-and-claim: if the dir already exists
    # we get FileExistsError, generate a fresh id, and try again. Bounded so a
    # genuinely broken filesystem surfaces as RunInitError rather than hanging.
    for _ in range(MAX_RUN_ID_ATTEMPTS):
        rid = run_id.new_run_id()
        run_dir = (Path(root) / rid).resolve()
        try:
            (run_dir / "workers").mkdir(parents=True, exist_ok=False)
        except FileExistsError:
            continue
        break
    else:
        raise RunInitError(
            f"could not allocate a unique run_id under {root!r} after "
            f"{MAX_RUN_ID_ATTEMPTS} attempts"
        )

    # Timezone-aware UTC; datetime.utcnow() is deprecated in Python 3.12+.
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    (run_dir / "contract.md").write_text(
        CONTRACT_TEMPLATE.format(run_id=rid, task=task), encoding="utf-8"
    )
    (run_dir / "run.log").write_text(
        f"{ts} run_initialized task={task!r}\n", encoding="utf-8"
    )
    return run_dir


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: init_run.py <task>", file=sys.stderr)
        sys.exit(2)
    default_root = Path(".council-runs").resolve()
    default_root.mkdir(exist_ok=True)
    print(init_run(default_root, sys.argv[1]))
