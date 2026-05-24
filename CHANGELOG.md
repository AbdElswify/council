# Changelog

## v0.1.0 — 2026-05-23 (TBD)

Initial release.

### Added
- `/council` slash command (brainstorm → contract → parallel dispatch →
  two-pass audit → integration check → final report).
- `council-worker` subagent (generic, dynamic specialty).
- `council-auditor` subagent (read-only, fenced-JSON verdict).
- Python helper scripts: `init_run`, `init_worker`, `manifest`,
  `audit_log`, `parse_verdict`, `slugify`, `run_id`.
- 2-round convergence cap with contracting scope on round 2.
- Workspace layout under `.council-runs/<run-id>/`.

### Known limitations
- Flat hierarchy only (no recursion past depth 1).
- No mid-run user gating.
- No `/council:resume` for crash recovery.
- See `docs/plans/2026-05-23-council-design.md` for the full list.
