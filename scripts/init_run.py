"""Initialize a per-run workspace under .council-runs/<run-id>/."""
from datetime import datetime
from pathlib import Path

import run_id


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
    rid = run_id.new_run_id()
    run_dir = (Path(root) / rid).resolve()
    (run_dir / "workers").mkdir(parents=True, exist_ok=False)
    (run_dir / "contract.md").write_text(
        CONTRACT_TEMPLATE.format(run_id=rid, task=task), encoding="utf-8"
    )
    ts = datetime.utcnow().isoformat(timespec="seconds")
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
