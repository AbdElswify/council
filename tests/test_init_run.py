import json
from pathlib import Path

import pytest

import init_run
import run_id


def test_creates_run_directory(tmp_path):
    run_dir = init_run.init_run(root=tmp_path, task="Test task")
    assert run_dir.exists()
    assert run_dir.parent == tmp_path
    assert run_dir.name  # run-id

def test_creates_workers_subdir(tmp_path):
    run_dir = init_run.init_run(root=tmp_path, task="Test task")
    assert (run_dir / "workers").is_dir()

def test_writes_contract_stub(tmp_path):
    run_dir = init_run.init_run(root=tmp_path, task="Test task")
    contract = run_dir / "contract.md"
    assert contract.exists()
    assert "Test task" in contract.read_text()
    assert "## Worker roster" in contract.read_text()

def test_writes_run_log_with_init_event(tmp_path):
    run_dir = init_run.init_run(root=tmp_path, task="Test task")
    log = run_dir / "run.log"
    assert log.exists()
    assert "run_initialized" in log.read_text()

def test_returns_absolute_path(tmp_path):
    run_dir = init_run.init_run(root=tmp_path, task="Test task")
    assert run_dir.is_absolute()


# --- run_id collision handling ---

def test_retries_on_run_id_collision(tmp_path, monkeypatch):
    # First id collides with a pre-existing dir; second id is fresh.
    ids = iter(["20260525T000000-dead", "20260525T000000-beef"])
    monkeypatch.setattr(run_id, "new_run_id", lambda: next(ids))
    # Pre-create the directory the first id would claim.
    (tmp_path / "20260525T000000-dead" / "workers").mkdir(parents=True)

    run_dir = init_run.init_run(root=tmp_path, task="Collide then succeed")
    assert run_dir.name == "20260525T000000-beef"
    assert (run_dir / "contract.md").exists()
    assert (run_dir / "run.log").exists()

def test_raises_after_exhausting_attempts(tmp_path, monkeypatch):
    # Every generated id collides with an existing dir -> bounded failure.
    monkeypatch.setattr(run_id, "new_run_id", lambda: "20260525T000000-stuck")
    (tmp_path / "20260525T000000-stuck" / "workers").mkdir(parents=True)

    with pytest.raises(init_run.RunInitError, match="could not allocate a unique run_id"):
        init_run.init_run(root=tmp_path, task="Always collides")


# --- timezone-aware UTC timestamp in run.log ---

def test_run_log_timestamp_is_utc_aware(tmp_path):
    run_dir = init_run.init_run(root=tmp_path, task="Test task")
    first_line = (run_dir / "run.log").read_text().splitlines()[0]
    # datetime.now(timezone.utc).isoformat() yields a +00:00 offset.
    assert "+00:00" in first_line
    assert "run_initialized" in first_line
