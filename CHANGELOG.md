# Changelog

## v0.1.2 — 2026-05-25

Closes the four follow-ups deferred from the v0.1.1 self-improvement run.

### Fixed
- `run.log` `force_accepted` event arg generalized from a hardcoded
  `round=2` to `round=<n>` — force-accept can also fire in round 1 (the
  3rd-Pass-1-NEEDS_REVISION-in-a-single-round cap), so the logged round is
  now accurate.

### Changed
- `parse_verdict.py` now enforces verdict↔findings consistency that was
  previously only asserted in the auditor prompt: an `APPROVED` verdict must
  have empty `findings`, a `NEEDS_REVISION` verdict must list at least one,
  and each finding must be an object with `severity` (`blocker`/`should-fix`)
  and `issue` (string), plus an optional string `loc`. The `council-auditor`
  prompt's findings field-rule documents the same.
- Design-doc "Testing strategy" rewritten to distinguish the two test layers
  — the pytest unit suite (now 65 tests) over the `scripts/` plumbing, and
  the end-to-end scenario tests — instead of framing scenarios as the only
  tests.
- Implementation-plan CHANGELOG date placeholder (`2026-MM-DD (TBD)`)
  corrected to the real `2026-05-24`.

### Tests
- 55 → 65 (added 10 findings-validation cases for `parse_verdict`).

## v0.1.1 — 2026-05-25

Hardening release. Produced by a council self-improvement run (`/council`
analyzing its own plugin), with four file-owned workers under two-pass audit.

### Fixed
- **Dispatch was broken when the plugin is installed.** `commands/council.md`
  told the Mayor to dispatch `subagent_type: "council-worker"` /
  `"council-auditor"`, but installed plugins namespace agent types as
  `council:council-worker` / `council:council-auditor`; the bare names fail
  with "Agent type not found". All dispatch sites now use the namespaced form
  (bare name documented as the dev-checkout fallback).
- **`init_worker` wiped audit history on re-dispatch.** It used
  `mkdir(exist_ok=False)` and unconditionally truncated `audit_history.jsonl`,
  so re-initializing a worker after an audit destroyed the append-only history.
  Now idempotent: dirs may pre-exist and the history file is created only when
  missing.
- `datetime.utcnow()` (deprecated in Python 3.12+) replaced with
  timezone-aware `datetime.now(timezone.utc)` in `run_id`, `init_run`,
  `audit_log`; timestamps now carry a `+00:00` offset.
- `run_id` collisions are now handled with a bounded retry + `RunInitError`
  instead of an unhandled `FileExistsError`.
- `parse_verdict` fence regex is CRLF-tolerant and accepts a verdict block
  with no blank line before the closing fence, while preserving last-block-wins.

### Changed
- Agent prompts hardened: verdict values documented as case-sensitive; the
  round-2 novel-finding rule rewritten as an enforceable allow-list procedure;
  worker re-dispatch and the frozen manifest schema spelled out field-by-field.
- Orchestration prompt: inline `run.log` emit-reminders at every emission
  point; `files_written` named in the dispatch template; Phase 5 seam
  re-dispatch routed through the Phase 4 re-dispatch path.
- Docs: corrected the tribunal comparison rows (tribunal dispatches in
  parallel where deps allow, then synthesizes — not "Sequential"); CHANGELOG
  and design-doc reconciled with shipped state; removed a stale `slugify`
  shipped-script over-claim.
- Tests: 43 → 55 (added coverage for timezone offset, run_id collision,
  `init_worker` idempotency, and the CRLF/no-trailing-newline verdict fence).

### Known follow-ups (deferred)
- `parse_verdict` does not yet enforce `findings`-empty-iff-`APPROVED` or
  `findings[]` element shape (asserted in the auditor prompt only).
- The `force_accepted ... round=2` run.log arg is imperfect for a
  3rd-Pass-1-in-round-1 force-accept; needs a cross-file contract revision.

## v0.1.0 — 2026-05-24

Initial release.

### Added
- `/council` slash command (brainstorm → contract → parallel dispatch →
  two-pass audit → integration check → final report).
- `council-worker` subagent (generic, dynamic specialty; `Read, Write,
  Edit, Glob, Grep, Bash` only — no `Agent`/`Task`, enforcing the flat
  hierarchy at the plugin layer).
- `council-auditor` subagent (read-only `Read, Glob, Grep`; fenced-JSON
  verdict with a frozen `verdict`/`round`/`pass`/`findings`/
  `contract_concerns` schema, optional `notes`).
- Python helper scripts: `init_run`, `init_worker`, `manifest`,
  `audit_log`, `parse_verdict`, `run_id`, all with pytest
  coverage.
- Worker manifest schema with a `files_written` field — the union of
  every path a worker created or modified — consumed by the Phase 5
  cross-worker file-conflict scan.
- Canonical 13-event `run.log` vocabulary, defined in `commands/council.md`
  (`run_initialized`, `worker_dispatched`, `worker_failed`, `audit_pass1`,
  `audit_pass2`, `pass2_synthetic_approval`, `worker_redispatched`,
  `force_accepted`, `phase5_entered`, `seam_unresolved`,
  `pushback_received`, `worker_reset`, `run_completed`).
- 2-round convergence cap with contracting scope on round 2, plus a
  defensive in-round cap on Pass-1 re-dispatches.
- Workspace layout under `.council-runs/<run-id>/`.

### Fixed (post-design hardening before release)
- `manifest.py` and `parse_verdict.py` now validate nested element
  shapes (per-finding severity, list-element types, verdict `round`/`pass`
  bounds) rather than only top-level field presence and type.
- Eight orchestration fixes in `commands/council.md` (re-dispatch
  protocol, Phase 6 pushback reset, the run.log event table, and related
  consistency gaps).
- `.claude-plugin/marketplace.json` uses the object `source` form
  (`{"source": "url", "url": "https://github.com/AbdElswify/council.git"}`)
  instead of a bare `"."` string, which Claude Code rejects on install.

### Known limitations
- Flat hierarchy only (no recursion past depth 1).
- No mid-run user gating.
- No `/council:resume` for crash recovery.
- See `docs/plans/2026-05-23-council-design.md` for the full list.
