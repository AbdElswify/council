import json
from pathlib import Path

import init_run


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
