# Council

A Claude Code plugin that orchestrates a flat, two-pass-audited multi-agent
workflow. You invoke `/council <task>`; the main Claude Code session becomes
the **Mayor**, brainstorms the task with you, writes an integration contract,
dispatches a set of dynamically-conceived specialist **Workers** in parallel
against that contract, audits each worker's output in two passes (Mayor first,
neutral Auditor second), and presents the integrated result.

Council is the leaner sibling of [tribunal](https://github.com/AbdElswify/tribunal).
Where tribunal walks a recursive Judge → Mayor → Department tree for tasks
with natural decomposition hierarchies, council stays flat: one orchestrator
in the main session, N specialist workers underneath, no recursion. It is
designed for tasks that fan out cleanly into 3–7 parallel pieces against an
agreed-upon contract.

## Status

v0.1.0 — early. See `## Known limitations` below for what hasn't shipped.

## Installation

### Via marketplace (recommended)

In a Claude Code session:

```
/plugin marketplace add AbdElswify/council
/plugin install council@council-marketplace
/reload-plugins
```

Then `/help` should list `/council` (it may appear as the namespaced
`/council:council` depending on Claude Code version).

### Manual (development)

If you're working on the plugin and want edits to take effect without
re-publishing, junction/symlink the working tree into Claude Code's plugin
directory:

**Windows (PowerShell, no admin needed):**

```powershell
New-Item -ItemType Junction `
  -Path "$env:USERPROFILE\.claude\plugins\council" `
  -Target "<absolute path to this directory>"
```

**macOS / Linux:**

```bash
ln -s "$(pwd)" ~/.claude/plugins/council
```

Then **fully restart Claude Code** so it scans plugins.

> Note: the marketplace path is the supported install method. The manual
> junction only works for development because Claude Code's plugin registry
> (`~/.claude/plugins/installed_plugins.json`) won't have an entry for your
> plugin, so it may not load in all Claude Code versions.

## Usage

```
/council write a haiku about autumn
```

You can also invoke `/council` with no arguments — the Mayor will ask what
task you want to take on.

### What happens

A council run walks six phases. The Mayor (the `/council` command running in
your main session) drives all of them.

1. **Brainstorm.** The Mayor asks one Socratic question at a time to pin down
   what "done" means, what the seams between sub-tasks should be, and how
   many workers are realistically needed (3–7 is the council sweet spot).
   Say "ready to dispatch" (or any clear green light) when the task is
   crisp.

2. **Contract.** The Mayor creates a per-run workspace at
   `.council-runs/<run-id>/` and writes `contract.md` — the single binding
   document for the run. It captures the task statement, shared interfaces
   (file paths, function signatures, data shapes), naming conventions, the
   worker roster (slug, specialty, scope, `depends_on`), and acceptance
   criteria. You confirm the contract before any worker is dispatched.

3. **Dispatch.** For each dependency layer, the Mayor creates a per-worker
   directory and fires N `Agent` calls in parallel — one per worker —
   handing each one its specialty, scope, the contract path, its workspace
   path, and the manifests of any upstream workers it depends on. Workers
   write artifacts under their own `artifacts/` directory and report back
   via a `manifest.json`.

4. **Audit (per worker, two-pass, max 2 rounds).** Pass 1 is the Mayor
   reviewing the worker in-session against the contract. APPROVED → Pass 2
   dispatches the neutral `council-auditor` subagent for a read-only
   independent verdict. NEEDS_REVISION at either pass re-dispatches the
   worker with the combined findings. Round 2 (if reached) contracts scope
   to "did you fix what was asked in round 1" — no novel findings. Round 3
   is never dispatched; if round 2 still fails, the Mayor force-accepts and
   logs the unresolved items.

5. **Integration check.** Once every worker has cleared audit, the Mayor
   reads all manifests together and verifies the seams declared in the
   contract actually hold across workers' outputs. A broken seam
   re-dispatches the responsible worker(s) and consumes their round budget.

6. **Final report.** The Mayor presents per-worker results, acceptance
   criteria PASS/FAIL/PARTIAL, any unresolved items, and a pointer to the
   workspace. You accept or push back; pushback re-runs only the affected
   workers, starting fresh at round 1.

### Worked example

```
/council write a haiku about autumn
```

The Mayor will ask one or two clarifying questions (e.g. "5/7/5 syllables
required?", "English only or include a translation?"), then propose a
single-worker contract (`haiku-author`, no deps, acceptance criteria along
the lines of "3 lines, autumn imagery, 5/7/5"). You confirm; the worker is
dispatched; the Mayor audits Pass 1, the auditor audits Pass 2; the final
report shows the haiku, the per-pass verdicts, and where the artifact lives
on disk. End-to-end this is a couple of minutes.

## Workspace layout

```
.council-runs/<run-id>/
  contract.md
  run.log
  workers/
    <specialty-slug>/
      manifest.json
      audit_history.jsonl
      contract_concern.md         # optional; only if worker flagged something
      artifacts/
        <files...>
```

`<run-id>` is an ISO-like timestamp plus a short random suffix
(e.g. `20260523T142301-a3f9`). Workspaces persist on disk after the run so
you can inspect artifacts and audit history. The Mayor does not consult
prior runs on a fresh invocation.

## Design rationale

See `docs/plans/2026-05-23-council-design.md` for the full design.

The headline decision is the **flat hierarchy**. The Mayor lives in the main
Claude Code session and dispatches `council-worker` and `council-auditor`
subagents directly; nothing recurses past depth 1. This sidesteps Claude
Code [issue #19077](https://github.com/anthropics/claude-code/issues/19077)
(subagent-to-subagent dispatch is blocked) by design rather than by
workaround — workers and auditors do not have `Agent` or `Task` in their
tool list, so the platform constraint is enforced at the plugin layer.

## Differences vs tribunal

| | Tribunal | Council |
|---|---|---|
| Orchestrator | Judge (main session) → Mayors (subagents) | Mayor (main session) |
| Hierarchy | Up to 4 levels (Judge → Mayor → Department → …) | Flat: 1 level (Mayor → Workers) |
| Integration | Sequential via `depends_on` + Mayor synthesis | Upfront contract + parallel + optional `depends_on` |
| `recruit_plan` indirection | Yes (every Mayor/Department may recruit) | No (Mayor dispatches workers directly) |
| Best fit | Complex tasks with natural decomposition trees | Tasks that fan out cleanly into 3–7 parallel pieces |

## Known limitations

- **Hard cap on flat hierarchy.** Tasks needing 3+ levels of decomposition
  do not fit. Use tribunal.
- **Contract quality determines run quality.** A weak contract produces
  coherent-but-wrong output. Mitigated (not eliminated) by the brainstorm
  being explicit about contract construction.
- **No mid-run user gating.** The user cannot approve individual audits or
  pause between phases. Intentional for v1 (matches tribunal); revisit if
  the autonomous run-to-completion model proves frustrating.
- **No persistent run history across invocations.** Each `/council` call is
  independent. Past runs in `.council-runs/` are kept on disk but the
  Mayor does not consult them.
- **No inter-worker channel.** Workers in the same dispatch layer cannot
  coordinate mid-task. The only coordination mechanism is the upfront
  contract or serialization via `depends_on`.

## License

MIT
