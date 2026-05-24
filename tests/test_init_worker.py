from pathlib import Path

import init_worker


def test_creates_worker_dir(tmp_path):
    run_dir = tmp_path / "run-X"
    (run_dir / "workers").mkdir(parents=True)
    worker_dir = init_worker.init_worker(run_dir, "schema-designer")
    assert worker_dir == run_dir / "workers" / "schema-designer"
    assert worker_dir.is_dir()
    assert (worker_dir / "artifacts").is_dir()

def test_creates_empty_audit_history(tmp_path):
    run_dir = tmp_path / "run-X"
    (run_dir / "workers").mkdir(parents=True)
    worker_dir = init_worker.init_worker(run_dir, "schema-designer")
    history = worker_dir / "audit_history.jsonl"
    assert history.exists()
    assert history.read_text() == ""

def test_rejects_unsafe_slug(tmp_path):
    run_dir = tmp_path / "run-X"
    (run_dir / "workers").mkdir(parents=True)
    import pytest
    for bad in ["..", "../escape", "with/slash", "with\\slash"]:
        with pytest.raises(ValueError):
            init_worker.init_worker(run_dir, bad)
