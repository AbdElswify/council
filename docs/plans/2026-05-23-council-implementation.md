# Council v0.1.0 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Ship v0.1.0 of the `council` Claude Code plugin per the design in
`docs/plans/2026-05-23-council-design.md` — a `/council` slash command that
brainstorms a task, writes an integration contract, dispatches dynamic
specialist workers in parallel, and audits each in two passes against the
contract.

**Architecture:** Mayor runs in the main Claude Code session (the `/council`
slash command). It dispatches `council-worker` and `council-auditor` subagents
directly via `Agent`. Deterministic plumbing (run-id generation, workspace
creation, manifest I/O, audit-history append, verdict parsing) lives in
Python helper scripts under `scripts/`, with pytest coverage. Prompts in
`commands/` and `agents/` shell out to these scripts via Bash.

**Tech Stack:** Markdown (prompts), Python 3.10+ (helper scripts), pytest,
Claude Code plugin format (`.claude-plugin/plugin.json`,
`commands/*.md`, `agents/*.md`).

**Working directory for execution:** `C:\Users\abd\Projects\council\` (already
git-initialized; root commit `6398bb2` is the design doc).

---

## Notes for the implementing engineer

- You have zero context on this repo. Read the design doc
  (`docs/plans/2026-05-23-council-design.md`) **before starting Task 1**.
- The plan mixes two task styles:
  - **Script tasks (TDD)**: real Python, real tests. Follow the
    test-first-fail-then-implement-then-pass discipline literally.
  - **Prompt tasks (manual verification)**: Markdown for command/agent
    prompts. There is no automated test for prompt behavior — verification
    is "invoke and observe expected behavior." Each prompt task ends with
    a concrete manual-test recipe with expected outcomes.
- Commit after every task. Conventional commit prefixes:
  `feat:`, `fix:`, `docs:`, `chore:`, `test:`, `refactor:`.
- The `superpowers:test-driven-development` skill applies to all script
  tasks. The `superpowers:verification-before-completion` skill applies
  to every task: never claim done without observing the verification
  output yourself.
- Reference doc paths in this plan are repo-relative
  (e.g. `scripts/init_run.py`), absolute paths begin with
  `C:\Users\abd\Projects\council\`.

---

## Phase A: Repository scaffold

### Task 1: Plugin manifest

**Files:**
- Create: `.claude-plugin/plugin.json`

**Step 1: Create the manifest**

```json
{
  "name": "council",
  "version": "0.1.0",
  "description": "Flat multi-agent orchestration via /council — main session is the Mayor and dispatches dynamic specialist workers in parallel against an upfront integration contract, with two-pass audits (Mayor + neutral auditor) per worker.",
  "author": {
    "name": "Abdarrahman ElSwify",
    "url": "https://github.com/AbdElswify"
  },
  "homepage": "https://github.com/AbdElswify/council",
  "repository": "https://github.com/AbdElswify/council",
  "license": "MIT",
  "keywords": ["multi-agent", "orchestration", "council", "audit", "parallel"]
}
```

**Step 2: Verify JSON parses**

Run: `python -c "import json; json.load(open('.claude-plugin/plugin.json'))"`
Expected: no output (exit 0).

**Step 3: Commit**

```bash
git add .claude-plugin/plugin.json
git commit -m "chore: add plugin manifest"
```

---

### Task 2: .gitignore and pytest config

**Files:**
- Create: `.gitignore`
- Create: `pyproject.toml`

**Step 1: Write .gitignore**

```
# Python
__pycache__/
*.py[cod]
.pytest_cache/
*.egg-info/

# Council runs (local-only by default)
.council-runs/

# IDE
.idea/
.vscode/
*.swp

# OS
.DS_Store
Thumbs.db
```

**Step 2: Write pyproject.toml (minimal pytest config)**

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["scripts"]
```

**Step 3: Verify pytest discovers nothing yet (no tests written)**

Run: `pytest --collect-only`
Expected: "no tests ran" with exit 5 (no tests collected — fine for now).

**Step 4: Commit**

```bash
git add .gitignore pyproject.toml
git commit -m "chore: add gitignore and pytest config"
```

---

### Task 3: README skeleton

**Files:**
- Create: `README.md`

**Step 1: Write minimal README**

```markdown
# Council

A Claude Code plugin that orchestrates a flat Mayor-and-Workers multi-agent
workflow. You invoke `/council <task>`; the main Claude Code session
brainstorms the task with you, writes an integration contract, dispatches
specialist workers in parallel against it, audits each in two passes, and
presents the integrated result.

Sibling project: [tribunal](https://github.com/AbdElswify/tribunal). See
`docs/plans/2026-05-23-council-design.md` for the design rationale.

## Status

v0.1.0 — early. See design doc for known limitations.

## Installation

(TODO once the marketplace listing is wired up.)

## Usage

```
/council <task description>
```

(More detail to be added when the command is implemented.)

## License

MIT
```

**Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add README skeleton"
```

---

## Phase B: Helper scripts (TDD)

All scripts live in `scripts/`. All tests in `tests/`. Each task strictly
follows red-green-refactor.

### Task 4: Slugify helper

**Files:**
- Create: `scripts/slugify.py`
- Test: `tests/test_slugify.py`

**Step 1: Write the failing tests**

```python
# tests/test_slugify.py
import slugify

def test_basic():
    assert slugify.slugify("Hello World") == "hello-world"

def test_strips_special_chars():
    assert slugify.slugify("Fix bug #42!") == "fix-bug-42"

def test_truncates_to_40():
    assert len(slugify.slugify("a" * 100)) == 40

def test_empty_returns_placeholder():
    assert slugify.slugify("") == "task"

def test_whitespace_only_returns_placeholder():
    assert slugify.slugify("   \t\n  ") == "task"

def test_collapses_runs_of_non_alnum():
    assert slugify.slugify("a !!! b") == "a-b"
```

**Step 2: Run tests, verify they all fail**

Run: `pytest tests/test_slugify.py -v`
Expected: `ModuleNotFoundError: No module named 'slugify'` (all fail).

**Step 3: Implement minimal version**

```python
# scripts/slugify.py
"""Filesystem-safe slug helper for council run IDs and worker dir names."""
import re

SLUG_MAX = 40
EMPTY_PLACEHOLDER = "task"


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = text.strip("-")
    text = text[:SLUG_MAX].strip("-")
    return text or EMPTY_PLACEHOLDER
```

**Step 4: Run tests, verify all pass**

Run: `pytest tests/test_slugify.py -v`
Expected: 6 passed.

**Step 5: Commit**

```bash
git add scripts/slugify.py tests/test_slugify.py
git commit -m "feat(scripts): add slugify helper"
```

---

### Task 5: Run-ID generator

**Files:**
- Create: `scripts/run_id.py`
- Test: `tests/test_run_id.py`

**Step 1: Write the failing tests**

```python
# tests/test_run_id.py
import re
import run_id

RUN_ID_PATTERN = re.compile(r"^\d{8}T\d{6}-[a-z0-9]{4}$")

def test_format():
    assert RUN_ID_PATTERN.match(run_id.new_run_id())

def test_two_calls_differ():
    # Suffix randomness should make collisions astronomically unlikely
    assert run_id.new_run_id() != run_id.new_run_id()
```

**Step 2: Run tests, verify they fail**

Run: `pytest tests/test_run_id.py -v`
Expected: ModuleNotFoundError.

**Step 3: Implement**

```python
# scripts/run_id.py
"""Generate a council run identifier: ISO-like timestamp + 4-char random suffix."""
import secrets
from datetime import datetime


def new_run_id() -> str:
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
    suffix = secrets.token_hex(2)  # 4 hex chars
    return f"{ts}-{suffix}"
```

**Step 4: Run tests, verify pass**

Run: `pytest tests/test_run_id.py -v`
Expected: 2 passed.

**Step 5: Commit**

```bash
git add scripts/run_id.py tests/test_run_id.py
git commit -m "feat(scripts): add run-id generator"
```

---

### Task 6: Workspace initializer

**Files:**
- Create: `scripts/init_run.py`
- Test: `tests/test_init_run.py`

**Step 1: Write the failing tests**

```python
# tests/test_init_run.py
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
```

**Step 2: Verify tests fail**

Run: `pytest tests/test_init_run.py -v`
Expected: ModuleNotFoundError.

**Step 3: Implement**

```python
# scripts/init_run.py
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
```

**Step 4: Verify tests pass**

Run: `pytest tests/test_init_run.py -v`
Expected: 5 passed.

**Step 5: Commit**

```bash
git add scripts/init_run.py tests/test_init_run.py
git commit -m "feat(scripts): add run workspace initializer"
```

---

### Task 7: Worker workspace initializer

**Files:**
- Create: `scripts/init_worker.py`
- Test: `tests/test_init_worker.py`

**Step 1: Write the failing tests**

```python
# tests/test_init_worker.py
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
```

**Step 2: Verify tests fail**

Run: `pytest tests/test_init_worker.py -v`
Expected: ModuleNotFoundError.

**Step 3: Implement**

```python
# scripts/init_worker.py
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
```

**Step 4: Verify tests pass**

Run: `pytest tests/test_init_worker.py -v`
Expected: 3 passed.

**Step 5: Commit**

```bash
git add scripts/init_worker.py tests/test_init_worker.py
git commit -m "feat(scripts): add worker workspace initializer"
```

---

### Task 8: Manifest I/O

**Files:**
- Create: `scripts/manifest.py`
- Test: `tests/test_manifest.py`

**Step 1: Write the failing tests**

```python
# tests/test_manifest.py
import json
from pathlib import Path

import pytest

import manifest


VALID = {
    "specialty": "API schema designer",
    "summary": "Defined OpenAPI 3.0 spec for user service.",
    "artifacts": ["artifacts/openapi.yaml"],
    "contract_concerns": [],
    "seams_touched": ["GET /users/{id} response shape"],
}


def test_roundtrip(tmp_path):
    path = tmp_path / "manifest.json"
    manifest.write(path, VALID)
    assert manifest.read(path) == VALID

def test_validate_missing_field():
    bad = {k: v for k, v in VALID.items() if k != "summary"}
    with pytest.raises(manifest.ManifestError, match="missing required field: summary"):
        manifest.validate(bad)

def test_validate_wrong_type():
    bad = dict(VALID, artifacts="not a list")
    with pytest.raises(manifest.ManifestError, match="artifacts must be a list"):
        manifest.validate(bad)

def test_read_invalid_json(tmp_path):
    path = tmp_path / "manifest.json"
    path.write_text("not json", encoding="utf-8")
    with pytest.raises(manifest.ManifestError, match="invalid JSON"):
        manifest.read(path)
```

**Step 2: Verify tests fail**

Run: `pytest tests/test_manifest.py -v`
Expected: ModuleNotFoundError.

**Step 3: Implement**

```python
# scripts/manifest.py
"""Read, write, and validate a council worker manifest."""
import json
from pathlib import Path
from typing import Any


REQUIRED_FIELDS = {
    "specialty": str,
    "summary": str,
    "artifacts": list,
    "contract_concerns": list,
    "seams_touched": list,
}


class ManifestError(ValueError):
    pass


def validate(data: Any) -> None:
    if not isinstance(data, dict):
        raise ManifestError("manifest must be a JSON object")
    for field, typ in REQUIRED_FIELDS.items():
        if field not in data:
            raise ManifestError(f"missing required field: {field}")
        if not isinstance(data[field], typ):
            raise ManifestError(f"{field} must be a {typ.__name__}")


def read(path: Path) -> dict:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ManifestError(f"invalid JSON in {path}: {e}") from e
    validate(data)
    return data


def write(path: Path, data: dict) -> None:
    validate(data)
    Path(path).write_text(
        json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
```

**Step 4: Verify tests pass**

Run: `pytest tests/test_manifest.py -v`
Expected: 4 passed.

**Step 5: Commit**

```bash
git add scripts/manifest.py tests/test_manifest.py
git commit -m "feat(scripts): add manifest I/O with validation"
```

---

### Task 9: Audit log append/read

**Files:**
- Create: `scripts/audit_log.py`
- Test: `tests/test_audit_log.py`

**Step 1: Write the failing tests**

```python
# tests/test_audit_log.py
import json
from pathlib import Path

import audit_log


VERDICT_1 = {
    "verdict": "NEEDS_REVISION",
    "round": 1,
    "pass": 1,
    "findings": [{"severity": "blocker", "loc": "x.py:1", "issue": "..."}],
    "contract_concerns": [],
}

VERDICT_2 = {
    "verdict": "APPROVED",
    "round": 1,
    "pass": 2,
    "findings": [],
    "contract_concerns": [],
}


def test_append_creates_file(tmp_path):
    history = tmp_path / "audit_history.jsonl"
    audit_log.append(history, VERDICT_1)
    assert history.exists()

def test_append_adds_timestamp(tmp_path):
    history = tmp_path / "audit_history.jsonl"
    audit_log.append(history, VERDICT_1)
    line = json.loads(history.read_text().strip())
    assert "timestamp" in line
    assert line["verdict"] == "NEEDS_REVISION"

def test_read_returns_list_in_order(tmp_path):
    history = tmp_path / "audit_history.jsonl"
    audit_log.append(history, VERDICT_1)
    audit_log.append(history, VERDICT_2)
    entries = audit_log.read(history)
    assert len(entries) == 2
    assert entries[0]["verdict"] == "NEEDS_REVISION"
    assert entries[1]["verdict"] == "APPROVED"

def test_read_empty_returns_empty_list(tmp_path):
    history = tmp_path / "audit_history.jsonl"
    history.write_text("", encoding="utf-8")
    assert audit_log.read(history) == []
```

**Step 2: Verify tests fail**

Run: `pytest tests/test_audit_log.py -v`
Expected: ModuleNotFoundError.

**Step 3: Implement**

```python
# scripts/audit_log.py
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
```

**Step 4: Verify tests pass**

Run: `pytest tests/test_audit_log.py -v`
Expected: 4 passed.

**Step 5: Commit**

```bash
git add scripts/audit_log.py tests/test_audit_log.py
git commit -m "feat(scripts): add audit history append/read"
```

---

### Task 10: Verdict JSON parser

**Files:**
- Create: `scripts/parse_verdict.py`
- Test: `tests/test_parse_verdict.py`

**Step 1: Write the failing tests**

```python
# tests/test_parse_verdict.py
import pytest

import parse_verdict


CLEAN = '''Some preamble.

```json
{"verdict": "APPROVED", "round": 1, "findings": [], "contract_concerns": []}
```

Some postamble.'''


def test_extracts_clean_block():
    v = parse_verdict.parse(CLEAN)
    assert v["verdict"] == "APPROVED"

def test_no_block_raises():
    with pytest.raises(parse_verdict.VerdictError, match="no fenced JSON"):
        parse_verdict.parse("no block here")

def test_malformed_json_raises():
    bad = "```json\n{not valid}\n```"
    with pytest.raises(parse_verdict.VerdictError, match="invalid JSON"):
        parse_verdict.parse(bad)

def test_missing_verdict_key_raises():
    bad = '```json\n{"round": 1}\n```'
    with pytest.raises(parse_verdict.VerdictError, match="missing 'verdict'"):
        parse_verdict.parse(bad)

def test_invalid_verdict_value_raises():
    bad = '```json\n{"verdict": "MAYBE"}\n```'
    with pytest.raises(parse_verdict.VerdictError, match="verdict must be"):
        parse_verdict.parse(bad)

def test_picks_last_block_if_multiple():
    text = (
        "```json\n{\"verdict\": \"NEEDS_REVISION\"}\n```\n"
        "thinking out loud\n"
        "```json\n{\"verdict\": \"APPROVED\"}\n```"
    )
    assert parse_verdict.parse(text)["verdict"] == "APPROVED"
```

**Step 2: Verify tests fail**

Run: `pytest tests/test_parse_verdict.py -v`
Expected: ModuleNotFoundError.

**Step 3: Implement**

```python
# scripts/parse_verdict.py
"""Extract and validate the council-auditor's fenced-JSON verdict."""
import json
import re


VALID_VERDICTS = {"APPROVED", "NEEDS_REVISION"}
FENCE_RE = re.compile(r"```json\s*\n(.*?)\n```", re.DOTALL)


class VerdictError(ValueError):
    pass


def parse(text: str) -> dict:
    matches = FENCE_RE.findall(text)
    if not matches:
        raise VerdictError("no fenced JSON block (```json ... ```) found")
    payload = matches[-1]  # last block wins (allow auditor preamble drafts)
    try:
        data = json.loads(payload)
    except json.JSONDecodeError as e:
        raise VerdictError(f"invalid JSON in verdict block: {e}") from e
    if "verdict" not in data:
        raise VerdictError("missing 'verdict' key in JSON")
    if data["verdict"] not in VALID_VERDICTS:
        raise VerdictError(
            f"verdict must be one of {sorted(VALID_VERDICTS)}; got {data['verdict']!r}"
        )
    return data
```

**Step 4: Verify tests pass**

Run: `pytest tests/test_parse_verdict.py -v`
Expected: 6 passed.

**Step 5: Commit**

```bash
git add scripts/parse_verdict.py tests/test_parse_verdict.py
git commit -m "feat(scripts): add verdict JSON parser"
```

---

### Task 11: Full-suite green check

**Step 1: Run the whole pytest suite**

Run: `pytest -v`
Expected: 26 tests pass, 0 fail.

**Step 2: Commit a pytest CI placeholder (optional — skip if no CI yet)**

(no-op for v0.1.0; revisit in Phase J)

---

## Phase C: Worker agent

### Task 12: `council-worker` subagent

**Files:**
- Create: `agents/council-worker.md`

**Step 1: Write the agent file**

```markdown
---
description: |
  Specialist worker dispatched by the council Mayor (the /council command
  running in the main session). Receives a specialty, scope, contract
  path, and workspace path. Does the work. Writes artifacts to
  <workspace>/artifacts/ and a manifest.json describing them. Does NOT
  recruit further subagents (Claude Code does not support subagent
  recursion: anthropics/claude-code#19077).
tools: [Read, Write, Edit, Glob, Grep, Bash]
---

You are a council worker. The Mayor (the /council command in the main
session) has dispatched you with a single specialty and scope. Your job
is to complete that scope, conform to the shared contract, and report
back via a manifest.

## Inputs the Mayor will pass in your prompt

- **Specialty**: a short role label (e.g. "API schema designer").
- **Scope**: a concrete description of what you must produce.
- **Contract path**: absolute path to `.council-runs/<run-id>/contract.md`.
- **Workspace path**: absolute path to your worker dir
  `.council-runs/<run-id>/workers/<your-slug>/`.
- **Upstream manifests** (optional): paths to `manifest.json` files of
  workers you depend on. Read them before starting work.

## Your obligations

1. **Read the contract first.** Every artifact you produce must conform
   to it. If the contract is ambiguous or genuinely wrong for your scope,
   do NOT silently deviate — write your concern to
   `<workspace>/contract_concern.md` and continue with your best
   interpretation. The Mayor will see the concern and decide what to do.

2. **Write all artifacts under `<workspace>/artifacts/`.** Do not write
   anywhere else in the repo without an explicit instruction from the
   Mayor saying so.

3. **Write `<workspace>/manifest.json`** with this schema:

   ```json
   {
     "specialty": "<your specialty>",
     "summary": "<one paragraph: what you did, the key decisions, anything the Mayor needs to know>",
     "artifacts": ["artifacts/<file>", "..."],
     "contract_concerns": [
       {"severity": "blocker"|"should-fix", "issue": "<text>"}
     ],
     "seams_touched": [
       "<short description of an interface, file, or behavior other workers depend on>"
     ]
   }
   ```

   `contract_concerns` is an empty list if you have none.
   `seams_touched` is an empty list if nothing you produced needs to
   align with another worker's output.

4. **Do not dispatch other subagents.** The `Agent` and `Task` tools are
   not in your tool list. If your scope requires recruiting help, that
   is a sign the Mayor mis-specialized — flag it in `contract_concerns`
   and continue with what you can do alone.

5. **End your turn with one line summarizing where you wrote the
   manifest.** Example:

   `Wrote manifest: <absolute path to manifest.json>`

   This is how the Mayor finds your output programmatically.

## If you are re-dispatched after an audit

You will receive an additional input: `audit_findings` — a list of
issues the Mayor and/or Auditor raised. Address ONLY those findings.
Do not rewrite work that was already approved. Re-write your manifest
when done.
```

**Step 2: Verify the frontmatter parses**

Run: `python -c "
import re, sys
text = open('agents/council-worker.md').read()
m = re.match(r'^---\n(.*?)\n---\n', text, re.DOTALL)
assert m, 'no frontmatter'
import yaml
fm = yaml.safe_load(m.group(1))
assert fm['tools'] == ['Read', 'Write', 'Edit', 'Glob', 'Grep', 'Bash'], fm['tools']
assert 'Agent' not in fm['tools']
assert 'Task' not in fm['tools']
print('OK')
"`
Expected: `OK`. If PyYAML isn't installed, run `pip install pyyaml` first.

**Step 3: Commit**

```bash
git add agents/council-worker.md
git commit -m "feat(agents): add council-worker subagent"
```

---

## Phase D: Auditor agent

### Task 13: `council-auditor` subagent

**Files:**
- Create: `agents/council-auditor.md`

**Step 1: Write the agent file**

```markdown
---
description: |
  Neutral Pass-2 auditor for a council worker. Read-only by design.
  Reads the worker's manifest.json, the worker's artifacts, the shared
  contract, and the audit_history.jsonl. Returns a fenced-JSON verdict
  in its final message.
tools: [Read, Glob, Grep]
---

You are a council auditor. The Mayor (the /council command in the main
session) is using you for Pass 2 of a two-pass audit. Pass 1 was done
by the Mayor itself; you are the neutral check on the Mayor's bias —
the Mayor selected the worker and wrote the scope, so it has an
incentive to approve. You do not.

## Inputs the Mayor will pass in your prompt

- **Worker workspace path**: `.council-runs/<run-id>/workers/<slug>/`
- **Contract path**: `.council-runs/<run-id>/contract.md`
- **Round number**: 1 or 2.

## Your obligations

1. **Read the contract.** That is the standard the worker must meet.
2. **Read the worker's manifest.json and every file under `artifacts/`.**
3. **Read `audit_history.jsonl`.** It contains every prior verdict
   (round 1 Pass 1 and Pass 2 if you are now on round 2).
4. **Judge the worker against the contract** AND against general
   correctness of its specialty.

## Round-2 constraint (IMPORTANT)

If `Round number == 2`, you are FORBIDDEN from raising novel findings.
You may ONLY:
- Approve if the round-1 findings in `audit_history.jsonl` were addressed.
- Re-flag those same findings as `NEEDS_REVISION` if they were not.

If you discover a new problem on round 2, **do not raise it** — log it
in your verdict's `notes` field instead. The Mayor will see it but the
worker will not be re-dispatched for it. This is the convergence rule.

## Your final message MUST end with a fenced-JSON verdict

```json
{
  "verdict": "APPROVED" | "NEEDS_REVISION",
  "round": <int>,
  "pass": 2,
  "findings": [
    {"severity": "blocker"|"should-fix", "loc": "<file:line or section>", "issue": "<text>"}
  ],
  "contract_concerns": [
    {"issue": "<text>"}
  ],
  "notes": "<optional, free-form, e.g. round-2 novel issue you spotted but withheld>"
}
```

`findings` is empty if APPROVED.
`contract_concerns` is empty if the contract is fine as-written.
`notes` is omitted unless needed.

You may write preamble (your reasoning) above the JSON block — only the
LAST fenced ```json``` block is parsed. Do NOT write any text after the
fenced block.
```

**Step 2: Verify frontmatter constraints**

Run: `python -c "
import re, yaml
text = open('agents/council-auditor.md').read()
fm = yaml.safe_load(re.match(r'^---\n(.*?)\n---\n', text, re.DOTALL).group(1))
assert fm['tools'] == ['Read', 'Glob', 'Grep'], fm['tools']
for t in ['Write', 'Edit', 'Bash', 'Agent', 'Task']:
    assert t not in fm['tools'], f'forbidden tool present: {t}'
print('OK')
"`
Expected: `OK`.

**Step 3: Commit**

```bash
git add agents/council-auditor.md
git commit -m "feat(agents): add council-auditor subagent"
```

---

## Phase E: `/council` command — brainstorm + contract

The `/council` command is large. Build it in sections, committing after
each. Each prompt section is one task.

### Task 14: Command shell + brainstorm phase

**Files:**
- Create: `commands/council.md`

**Step 1: Write the command file**

```markdown
---
description: Flat multi-agent orchestration. Main session brainstorms, dispatches dynamic specialist workers in parallel against a shared contract, audits each in two passes, and presents the integrated result.
---

You are the Mayor in a council run. The user has invoked you with a task
(provided as $ARGUMENTS, or asked in the first turn if empty). You will
walk this task through six phases:

1. **Brainstorm** (with user) — pin down what "done" means.
2. **Contract** — write the shared integration spec.
3. **Dispatch** — spawn specialist workers in parallel.
4. **Audit** — two-pass verdict per worker, with convergence cap.
5. **Integration check** — verify seams hold across workers.
6. **Final report** — present results, accept pushback.

The full design is in `docs/plans/2026-05-23-council-design.md` if you
need to consult it. The deterministic plumbing is in `scripts/`:
- `scripts/init_run.py` — create the run workspace
- `scripts/init_worker.py` — create a per-worker dir
- `scripts/manifest.py` — read/write/validate manifests
- `scripts/audit_log.py` — append/read audit history
- `scripts/parse_verdict.py` — parse the auditor's JSON verdict

DO NOT reimplement any of those — shell out to them.

---

## Phase 1: Brainstorm

If $ARGUMENTS is empty, ask the user: "What task do you want council to
take on?" If $ARGUMENTS is present, treat it as the initial task statement.

Then enter a Socratic loop with these rules:

- **One question per message.** Never ask more than one thing at a time.
- **Prefer multiple-choice** when possible — easier to answer than
  open-ended. Use the `AskUserQuestion` tool when available.
- **Aim explicitly at three deliverables** the brainstorm must produce
  before moving on:
  1. **The seams** between sub-tasks: what shared files, function
     signatures, data shapes, or naming conventions multiple workers
     will touch.
  2. **The worker roster**: 3–7 specialties (fewer means use a single
     agent; more means this task is better suited to tribunal). For
     each, a one-line scope.
  3. **The dependencies**: any worker that genuinely cannot start
     until another finishes (e.g. backend cannot begin until schema is
     designed). Default to none. Use sparingly.
- **Acceptance criteria**: a short list of concrete bullets describing
  what makes the final result "done." These will guide the audits.

Stop the brainstorm when the user says "ready to dispatch" (or any clear
green-light: "go", "proceed", "looks good, dispatch"). At that point,
write a brief one-paragraph task statement back to the user for
confirmation, then move to Phase 2.
```

**Step 2: Manual verification**

Install the plugin locally (junction trick — see tribunal README for
Windows / `ln -s` for macOS/Linux), restart Claude Code, then run:

```
/council
```

Expected: Claude asks "What task do you want council to take on?"
Reply with a tiny scope (e.g. "write a haiku about autumn"). Expected:
Claude enters one-question-at-a-time brainstorm mode. Stop after the
first 1–2 questions — you are only verifying the brainstorm starts.

**Step 3: Commit**

```bash
git add commands/council.md
git commit -m "feat(commands): /council shell + brainstorm phase"
```

---

### Task 15: Contract phase

**Files:**
- Modify: `commands/council.md` (append Phase 2 section)

**Step 1: Append to the command file**

```markdown

---

## Phase 2: Contract

When the brainstorm ends, do the following:

1. **Create the run workspace.** Shell out:

   ```bash
   python scripts/init_run.py "<task statement from brainstorm>"
   ```

   This prints the absolute run directory path. Store it as `$RUN_DIR`.
   The script has already written a `contract.md` stub at
   `$RUN_DIR/contract.md`.

2. **Fill in the contract.** Edit `$RUN_DIR/contract.md` to populate:
   - **Task statement** — already filled, but rewrite if you want it
     tighter.
   - **Shared interfaces** — every concrete artifact two or more workers
     will agree on: file paths, function signatures, data shapes,
     schemas, API contracts. Be specific. Example:
     `POST /users — request {name: string, email: string}, response {id: uuid}`.
   - **Naming conventions** — anything where consistency matters and
     could drift across workers.
   - **Worker roster** — fill the table with one row per worker:
     `slug` (kebab-case, matches `[a-z0-9][a-z0-9-]{0,63}`),
     `specialty` (short label, e.g. "API schema designer"),
     `scope` (one sentence describing what they produce),
     `depends_on` (comma-separated slugs of upstream workers, or `—`).
   - **Acceptance criteria** — 3–6 bullets describing what "done" looks
     like across the whole task. The audits will check against these.

3. **Show the user the populated contract** and ask: "Contract looks
   right? Reply 'dispatch' to launch workers, or call out anything to
   change."

4. **Loop on contract edits** until the user gives the green light.
   Each edit is a normal text/Edit operation on `$RUN_DIR/contract.md`.

5. **Validate worker slugs are unique and dep-safe**:
   - Every `depends_on` slug must exist elsewhere in the roster.
   - No cycles (do a topological-sort sanity check by hand —
     for ≤7 workers this is trivial).
   - All slugs match `^[a-z0-9][a-z0-9-]{0,63}$`.

   If validation fails, fix the contract and reshow to the user.
```

**Step 2: Manual verification**

Re-install the plugin (junction is already in place; just restart
Claude Code if needed). Run:

```
/council write a haiku about autumn, plus an English translation of it
```

In the brainstorm, settle on something like two workers
(`haiku-author`, `translator` with `depends_on: haiku-author`). Reach
the contract phase. Expected: `init_run.py` is invoked, a directory
appears under `.council-runs/`, the Mayor populates the contract table
and asks for confirmation.

After confirmation, abort the session (Ctrl-C is fine — we have not
implemented Phase 3 yet). Verify on disk:

```bash
ls -la .council-runs/
cat .council-runs/<latest-run-id>/contract.md
```

Expected: contract has the worker roster table with two rows and a
populated `depends_on`.

**Step 3: Commit**

```bash
git add commands/council.md
git commit -m "feat(commands): /council Phase 2 — contract"
```

---

## Phase F: Dispatch + audit loop

### Task 16: Dispatch phase

**Files:**
- Modify: `commands/council.md` (append Phase 3)

**Step 1: Append to the command file**

```markdown

---

## Phase 3: Dispatch

For each layer in the dependency graph (workers with no remaining
unsatisfied upstream deps form layer 1; once layer 1 finishes, workers
whose deps are all in layer 1 form layer 2; etc.):

1. **Create each worker's dir.** For every worker `<slug>` in this layer:

   ```bash
   python scripts/init_worker.py "$RUN_DIR" "<slug>"
   ```

2. **Dispatch all workers in this layer in PARALLEL** with one message
   containing N `Agent` tool calls (one per worker). Each call uses
   `subagent_type: "council-worker"` and a prompt with this template:

   ```
   You are dispatched as a council worker.

   Specialty: <specialty from contract roster>
   Scope: <scope from contract roster>
   Contract path: $RUN_DIR/contract.md
   Workspace path: $RUN_DIR/workers/<slug>/
   Upstream manifests: <comma-separated paths to upstream workers' manifest.json, or "none">

   Read the contract. Do the work. Write artifacts under
   <workspace>/artifacts/. Write your manifest at <workspace>/manifest.json.
   End your turn with: "Wrote manifest: <absolute manifest path>".
   ```

3. **Wait for all parallel Agent calls to return.** When each worker
   subagent finishes, validate its manifest:

   ```bash
   python -c "import sys; sys.path.insert(0, 'scripts'); import manifest; manifest.read('$RUN_DIR/workers/<slug>/manifest.json')"
   ```

   If exit code is nonzero, the manifest is invalid or missing —
   re-dispatch ONCE with an explicit prompt: "Your previous run did
   not produce a valid manifest at <path>. Error was: <error>. Try
   again." If second attempt also fails, mark worker as failed in the
   run log and skip it (Phase 6 will report this to the user).

4. **Append a `dispatched` event** to `$RUN_DIR/run.log` for each
   worker (manual `echo "<timestamp> dispatched <slug>" >> $RUN_DIR/run.log`).

5. **Move to Phase 4 (audit) for THIS layer's workers** before
   dispatching the next layer. (Audit completes before downstream
   workers see upstream manifests, so downstreams only ever read
   audit-passed artifacts.)
```

**Step 2: Manual verification**

Run a one-worker scenario:

```
/council write a haiku about autumn
```

Brainstorm to a single worker (`haiku-author`, no deps), confirm
contract, let dispatch run. After the worker subagent finishes,
abort before Phase 4 (not yet implemented). Verify on disk:

```bash
ls .council-runs/<latest>/workers/haiku-author/
cat .council-runs/<latest>/workers/haiku-author/manifest.json
ls .council-runs/<latest>/workers/haiku-author/artifacts/
```

Expected: manifest.json is present and valid; artifacts/ contains at
least one file (e.g. `haiku.txt`).

**Step 3: Commit**

```bash
git add commands/council.md
git commit -m "feat(commands): /council Phase 3 — dispatch"
```

---

### Task 17: Audit phase (Pass 1)

**Files:**
- Modify: `commands/council.md` (append Phase 4 Pass 1)

**Step 1: Append**

```markdown

---

## Phase 4: Audit (per worker, two-pass, max 2 rounds)

For each worker in the layer just dispatched, run this audit loop:

### Pass 1 — Mayor in-session audit

Read `$RUN_DIR/contract.md`, the worker's `manifest.json`, every file
under its `artifacts/`, and its `audit_history.jsonl`.

Judge the worker against the contract AND the worker's stated scope.
Look for:
- Contract conformance (interfaces match, naming matches, etc.)
- Correctness within the specialty.
- Whether `seams_touched` in the manifest matches reality.
- Whether any `contract_concerns` raised by the worker are blockers.

Form your verdict as a Python dict matching:

```python
{
  "verdict": "APPROVED" | "NEEDS_REVISION",
  "round": <current round>,
  "pass": 1,
  "findings": [{"severity": "blocker"|"should-fix", "loc": "<>", "issue": "<>"}],
  "contract_concerns": [{"issue": "<>"}],
}
```

Append to history:

```bash
python -c "import sys; sys.path.insert(0, 'scripts'); import audit_log; audit_log.append('$RUN_DIR/workers/<slug>/audit_history.jsonl', <verdict dict>)"
```

(Use a heredoc and `json.loads` to keep the dict literal clean.)

**If `NEEDS_REVISION`**: re-dispatch the worker (see "Worker
re-dispatch" below) and start the round over from Pass 1. Do NOT call
Pass 2 — the worker will be re-evaluated from scratch.

**If `APPROVED`**: proceed to Pass 2.
```

**Step 2: Commit (verification deferred to after Pass 2)**

```bash
git add commands/council.md
git commit -m "feat(commands): /council Phase 4 Pass 1 — Mayor audit"
```

---

### Task 18: Audit phase (Pass 2 + re-dispatch + convergence)

**Files:**
- Modify: `commands/council.md` (append Phase 4 Pass 2 and helpers)

**Step 1: Append**

```markdown

### Pass 2 — Neutral auditor

Dispatch one `Agent` call with `subagent_type: "council-auditor"` and
prompt:

```
You are dispatched as a council auditor for Pass 2.

Worker workspace: $RUN_DIR/workers/<slug>/
Contract: $RUN_DIR/contract.md
Round number: <current round>

Read everything per your agent instructions. Return your verdict as a
fenced-JSON block at the end of your message.
```

When the auditor returns, capture its final message as `$AUDITOR_TEXT`
and parse:

```bash
python -c "
import sys, json, os
sys.path.insert(0, 'scripts')
import parse_verdict
v = parse_verdict.parse(os.environ['AUDITOR_TEXT'])
print(json.dumps(v))
" | tee /tmp/v.json
```

If `parse_verdict` raises a `VerdictError`, re-dispatch the auditor
ONCE with an explicit "your previous verdict was malformed: <error>"
prompt. If the second auditor call also fails to produce a valid
verdict, log a warning to `run.log` and treat Pass 2 as APPROVED with
a note in the final report.

Append the verdict to history (same `audit_log.append` invocation as
Pass 1, but with `pass: 2`).

**If `APPROVED`**: worker is done. Proceed to next worker in the layer.

**If `NEEDS_REVISION`**: re-dispatch the worker (see below) and start
round+1 from Pass 1.

### Worker re-dispatch (for NEEDS_REVISION)

Re-issue an `Agent` call with `subagent_type: "council-worker"` and
prompt:

```
You are being re-dispatched after audit feedback.

Specialty: <same as before>
Scope: <same as before>
Contract path: $RUN_DIR/contract.md
Workspace path: $RUN_DIR/workers/<slug>/

Audit findings to address:
<formatted list of findings from the verdict that triggered re-dispatch>

Address ONLY these findings. Do not rewrite work that was already
approved. Update <workspace>/manifest.json when done. End your turn
with: "Wrote manifest: <absolute manifest path>".
```

### Convergence rule

After round 1, if either Pass 1 or Pass 2 returned `NEEDS_REVISION`,
you may run round 2 — but BOTH the Mayor (you) and the auditor are
restricted on round 2 to ONLY checking whether the round-1 findings
were addressed. No novel findings.

The auditor enforces this in its own prompt (it has been instructed in
`agents/council-auditor.md` to refuse novel round-2 findings). You
enforce the same on Pass 1 by re-reading `audit_history.jsonl` before
forming your verdict and checking that every finding in your round-2
verdict appears in some round-1 entry.

After round 2, regardless of verdict, **force-accept**: do not run
round 3. If round 2 still flagged issues, log them as `unresolved` in
the final report (Phase 6).
```

**Step 2: Manual verification (the haiku scenario, this time end-to-end
through audit)**

```
/council write a haiku about autumn
```

Use a single-worker contract. Let the worker run, then watch the Mayor
do Pass 1 (in-session) and then dispatch the auditor for Pass 2.
Expected: `audit_history.jsonl` ends up with 2 lines (or more if a
re-dispatch happened). Both should validate as JSON.

Inspect:

```bash
cat .council-runs/<latest>/workers/haiku-author/audit_history.jsonl
```

**Step 3: Commit**

```bash
git add commands/council.md
git commit -m "feat(commands): /council Phase 4 Pass 2 + convergence"
```

---

## Phase G: Integration check + final report

### Task 19: Integration check

**Files:**
- Modify: `commands/council.md` (append Phase 5)

**Step 1: Append**

```markdown

---

## Phase 5: Integration check

After ALL workers have passed audit (or hit force-accept), read every
worker's `manifest.json` and the contract together. Cross-check:

1. **Seam alignment.** For each entry in any worker's `seams_touched`,
   verify that the corresponding artifact in the dependent worker(s)
   actually conforms. Example: if `schema-designer` declares
   `POST /users response shape = {id, name, email}` and `backend-impl`
   produced an endpoint returning `{user_id, name}`, that is a broken
   seam.

2. **Contract acceptance criteria.** Walk the contract's "Acceptance
   criteria" bullets one-by-one. For each, decide
   PASS / FAIL / PARTIAL with one line of justification.

If you find any broken seam, **re-dispatch the responsible worker(s)**
with a precise description of the seam break. This re-dispatch counts
toward that worker's round budget (so if the worker is already at
round 2, you cannot re-dispatch further — log as unresolved).

If a re-dispatch occurs, re-run Phase 4 (audit) for that worker, then
re-run Phase 5. Cap Phase 5 iterations at 2 to prevent infinite loops.
```

**Step 2: Commit**

```bash
git add commands/council.md
git commit -m "feat(commands): /council Phase 5 — integration check"
```

---

### Task 20: Final report + pushback

**Files:**
- Modify: `commands/council.md` (append Phase 6)

**Step 1: Append**

```markdown

---

## Phase 6: Final report

Present to the user:

```
# Council Run <run-id>

**Task:** <task statement>

**Workers:** <count>

## Per-worker results
- **<slug>** (<specialty>): <APPROVED in round N | UNRESOLVED in round 2 | FAILED>
  - Artifacts: <list of paths under artifacts/>
  - Audit history: <run-dir>/workers/<slug>/audit_history.jsonl

## Acceptance criteria
- ✓ <criterion> — PASS
- ✗ <criterion> — FAIL: <reason>
- ~ <criterion> — PARTIAL: <reason>

## Unresolved
<bullets for anything force-accepted at round 2, contract concerns not
addressed, workers that failed twice, or seams that could not be fixed>

## Workspace
<run-dir> (kept on disk for inspection)
```

Then: "Anything to push back on? Tell me which worker(s) need a
re-run, and I'll restart them at round 1."

If the user pushes back, identify the affected workers, reset their
`audit_history.jsonl` to empty (but back up the old one to
`audit_history.previous.jsonl` for the user's reference), and re-run
Phases 3–5 for ONLY those workers. Other workers' artifacts and
manifests are untouched.

If the user accepts, write a final `run_completed` line to
`$RUN_DIR/run.log` and end your turn.
```

**Step 2: Manual verification — full end-to-end haiku run**

```
/council write a haiku about autumn
```

Run the full thing (brainstorm → contract → 1 worker → audit → final
report). Expected: a final report appears with the worker's status,
the artifact path, and a workspace pointer. Verify:

```bash
ls .council-runs/<latest>/
cat .council-runs/<latest>/run.log
cat .council-runs/<latest>/workers/haiku-author/audit_history.jsonl
cat .council-runs/<latest>/workers/haiku-author/artifacts/*.txt
```

Expected: run.log has `run_initialized`, `dispatched haiku-author`,
and `run_completed` events; audit_history has at least one APPROVED
verdict.

**Step 3: Commit**

```bash
git add commands/council.md
git commit -m "feat(commands): /council Phase 6 — final report and pushback"
```

---

## Phase H: End-to-end test scenarios

These are manual test scripts, not automated. Each one is a separate
task with explicit expected observations. Run each, then commit a
documentation file recording the result.

### Task 21: Smoke test — single-worker haiku

(Already exercised in Task 20. Document the result.)

**Files:**
- Create: `tests/scenarios/01-smoke-haiku.md`

**Step 1: Write the scenario doc**

```markdown
# Scenario 01: Smoke — single-worker haiku

## Invocation
```
/council write a haiku about autumn
```

## Expected brainstorm outcome
- 1 worker: `haiku-author`
- No dependencies
- Acceptance criteria: "3 lines, 5/7/5 syllables, autumn imagery"

## Expected post-run state
- `.council-runs/<run-id>/contract.md` populated.
- `.council-runs/<run-id>/workers/haiku-author/manifest.json` valid.
- `.council-runs/<run-id>/workers/haiku-author/artifacts/` contains
  at least one text file with a haiku.
- `audit_history.jsonl` contains ≥2 entries (Pass 1 + Pass 2),
  ending APPROVED.

## Last observed run
- Run ID: <fill in after running>
- Outcome: <PASS / FAIL>
- Notes: <anything>
```

**Step 2: Run the scenario and fill in the "Last observed run" section.**

**Step 3: Commit**

```bash
git add tests/scenarios/01-smoke-haiku.md
git commit -m "test: scenario 01 — smoke (haiku)"
```

---

### Task 22: Parallel test — 3 workers, no deps

**Files:**
- Create: `tests/scenarios/02-parallel-explain.md`

**Step 1: Write the scenario doc**

```markdown
# Scenario 02: Parallel — explain quicksort with two impls

## Invocation
```
/council explain quicksort with a written description, a Python implementation, and a JavaScript implementation
```

## Expected brainstorm outcome
- 3 workers, no deps:
  - `explainer` — natural-language description
  - `python-impl` — Python version
  - `js-impl` — JavaScript version
- Shared contract: a fixed example input list to use across all three.

## Expected post-run state
- All 3 worker manifests present.
- All 3 dispatched in PARALLEL (verify by looking at the message
  history — there should be one assistant message with 3 `Agent`
  tool calls).
- All 3 use the same example input from the contract.
- Phase 5 integration check passes (all three describe the same
  algorithm on the same input).

## Last observed run
- Run ID: ...
- Outcome: ...
- Notes: ...
```

**Step 2: Run, fill in result.**

**Step 3: Commit**

```bash
git add tests/scenarios/02-parallel-explain.md
git commit -m "test: scenario 02 — parallel dispatch (quicksort)"
```

---

### Task 23: Dependency test — schema → CRUD

**Files:**
- Create: `tests/scenarios/03-dependency-schema-crud.md`

**Step 1: Write the scenario doc**

```markdown
# Scenario 03: Dependency — schema then CRUD

## Invocation
```
/council design a JSON schema for a Book resource (title, author, isbn, published_year) and then write a CRUD module in Python that uses it
```

## Expected brainstorm outcome
- 2 workers:
  - `schema-designer` — JSON schema artifact (no deps)
  - `crud-impl` — Python module (`depends_on: schema-designer`)

## Expected post-run state
- `schema-designer` dispatched first; `crud-impl` dispatched only
  after `schema-designer` is audit-approved.
- `crud-impl`'s prompt included the path to `schema-designer`'s
  `manifest.json` and the worker read it.
- Phase 5 verifies that `crud-impl`'s validation logic actually
  references the fields in the schema.

## Last observed run
- ...
```

**Step 2: Run, fill in.**

**Step 3: Commit**

```bash
git add tests/scenarios/03-dependency-schema-crud.md
git commit -m "test: scenario 03 — dependency ordering (schema → CRUD)"
```

---

### Task 24: Convergence test — forced failure

**Files:**
- Create: `tests/scenarios/04-convergence-forced.md`

**Step 1: Write the scenario doc**

```markdown
# Scenario 04: Convergence — forced failure

## Setup
This scenario is contrived to exercise the round-2 cap. After the
worker produces its initial output, the operator (you, the developer)
manually inserts a `NEEDS_REVISION` finding the worker cannot
plausibly fix, to verify that:
- Round 2 happens
- Round 3 does NOT happen
- The worker is force-accepted with an `unresolved` entry in the final
  report.

## Invocation
```
/council write a 4-line poem about rain
```

In the brainstorm, set acceptance criteria to include
"line 4 must rhyme with line 1." Manually steer the Mayor's Pass 1
verdict to find a rhyme failure even when the worker complies — i.e.,
push back on every audit verbally to force `NEEDS_REVISION`.

## Expected post-run state
- `audit_history.jsonl` contains 4 entries (round 1 P1 + P2, round 2
  P1 + P2). No round 3.
- Final report includes the worker under "Unresolved" with the
  round-2 finding.

## Last observed run
- ...
```

**Step 2: Run, fill in.**

**Step 3: Commit**

```bash
git add tests/scenarios/04-convergence-forced.md
git commit -m "test: scenario 04 — convergence (forced failure)"
```

---

### Task 25: Auditor neutrality test

**Files:**
- Create: `tests/scenarios/05-auditor-neutrality.md`

**Step 1: Write the scenario doc**

```markdown
# Scenario 05: Auditor neutrality

## Goal
Verify Pass 2 actually catches things Pass 1 misses. Construct a task
where the obvious-correct output has a subtle, easy-to-miss bug.

## Invocation
```
/council write a Python function that returns the median of a list of integers, with tests
```

Set the acceptance criteria to specifically mention "handles even-length
lists correctly (average of two middle values)." A common worker
implementation will compute `sorted_list[len(sorted_list) // 2]` —
correct for odd, wrong for even. The Mayor often approves this on
Pass 1 because the worker also writes tests, and the worker's tests
may be skewed toward odd-length cases.

## Expected outcome
- Pass 1 (Mayor) APPROVES.
- Pass 2 (auditor) NEEDS_REVISION with finding pointing at the even-
  length case.
- Round 2: worker fixes it. Both passes APPROVE.

## Last observed run
- ...
```

**Step 2: Run, fill in.**

**Step 3: Commit**

```bash
git add tests/scenarios/05-auditor-neutrality.md
git commit -m "test: scenario 05 — auditor neutrality (median bug)"
```

---

## Phase I: Documentation, marketplace, release

### Task 26: Expand README

**Files:**
- Modify: `README.md`

**Step 1: Replace the README with a full version covering install,
usage, workspace layout, design link, and known limitations.** Use
the tribunal README as a structural reference (`C:\Users\abd\Projects\tribunal\README.md`).
Sections to include:

- Overview (1–2 paragraphs)
- Status (v0.1.0)
- Installation (marketplace path + manual junction/symlink for
  development)
- Usage (the `/council` command, what each phase produces)
- Workspace layout (the `.council-runs/<run-id>/` tree)
- Design rationale (link to design doc)
- Differences vs tribunal (1-paragraph or table)
- Known limitations (copy from design doc)
- License

**Step 2: Commit**

```bash
git add README.md
git commit -m "docs: expand README for v0.1.0"
```

---

### Task 27: CHANGELOG

**Files:**
- Create: `CHANGELOG.md`

**Step 1: Write**

```markdown
# Changelog

## v0.1.0 — 2026-MM-DD (TBD)

Initial release.

### Added
- `/council` slash command (brainstorm → contract → parallel dispatch →
  two-pass audit → integration check → final report).
- `council-worker` subagent (generic, dynamic specialty).
- `council-auditor` subagent (read-only, fenced-JSON verdict).
- Python helper scripts: `init_run`, `init_worker`, `manifest`,
  `audit_log`, `parse_verdict`, `run_id`.
- 2-round convergence cap with contracting scope on round 2.
- Workspace layout under `.council-runs/<run-id>/`.

### Known limitations
- Flat hierarchy only (no recursion past depth 1).
- No mid-run user gating.
- No `/council:resume` for crash recovery.
- See `docs/plans/2026-05-23-council-design.md` for the full list.
```

**Step 2: Commit**

```bash
git add CHANGELOG.md
git commit -m "docs: add CHANGELOG"
```

---

### Task 28: Marketplace manifest

**Files:**
- Create: `.claude-plugin/marketplace.json`

**Step 1: Write**

```json
{
  "name": "council-marketplace",
  "owner": {
    "name": "Abdarrahman ElSwify",
    "url": "https://github.com/AbdElswify"
  },
  "plugins": [
    {
      "name": "council",
      "source": ".",
      "description": "Flat multi-agent orchestration via /council. Main session is the Mayor; dispatches dynamic specialist workers in parallel against an upfront integration contract, with two-pass audits per worker.",
      "category": "agents",
      "version": "0.1.0"
    }
  ]
}
```

**Step 2: Commit**

```bash
git add .claude-plugin/marketplace.json
git commit -m "chore: add marketplace manifest"
```

---

### Task 29: Create GitHub repo + push

**Manual steps for the user, not the implementing engineer:**

```bash
cd C:/Users/abd/Projects/council
gh repo create AbdElswify/council --public --source=. --remote=origin --description "Flat multi-agent orchestration plugin for Claude Code"
git push -u origin main
```

(This is a user-action task. The engineer should pause and ask the
user to run these before continuing.)

---

### Task 30: Tag v0.1.0

**Once the smoke + parallel + dependency scenarios (21, 22, 23) have
all observed a PASS:**

```bash
git tag -a v0.1.0 -m "v0.1.0 — initial release"
git push --tags
```

(Skip auditor-neutrality and forced-convergence scenarios if they need
more polish — they can land in v0.1.1.)

---

## Done

When all 30 tasks are committed, v0.1.0 of council is shippable. Next
sprint candidates:
- `/council:resume <run-id>` for crash recovery.
- Mid-run user gating (approve audit verdicts inline).
- Cross-run learning (Mayor consults prior `audit_history.jsonl` for
  similar workers).
- Tighter integration with the brainstorming skill (vs the embedded
  brainstorm prompt).
