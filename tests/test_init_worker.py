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


# --- idempotency on re-dispatch ---

def test_reinit_is_idempotent(tmp_path):
    # Re-dispatch after an audit calls init_worker again for the same slug;
    # it must not raise and must return the same dir.
    run_dir = tmp_path / "run-X"
    (run_dir / "workers").mkdir(parents=True)
    first = init_worker.init_worker(run_dir, "schema-designer")
    second = init_worker.init_worker(run_dir, "schema-designer")
    assert first == second
    assert second.is_dir()
    assert (second / "artifacts").is_dir()

def test_reinit_preserves_existing_audit_history(tmp_path):
    # An accumulated, append-only audit history must survive re-init.
    run_dir = tmp_path / "run-X"
    (run_dir / "workers").mkdir(parents=True)
    worker_dir = init_worker.init_worker(run_dir, "schema-designer")
    history = worker_dir / "audit_history.jsonl"
    history.write_text('{"round": 1}\n', encoding="utf-8")

    init_worker.init_worker(run_dir, "schema-designer")
    assert history.read_text() == '{"round": 1}\n'

def test_reinit_preserves_existing_artifacts(tmp_path):
    run_dir = tmp_path / "run-X"
    (run_dir / "workers").mkdir(parents=True)
    worker_dir = init_worker.init_worker(run_dir, "schema-designer")
    artifact = worker_dir / "artifacts" / "findings.md"
    artifact.write_text("round-1 findings", encoding="utf-8")

    init_worker.init_worker(run_dir, "schema-designer")
    assert artifact.read_text() == "round-1 findings"
