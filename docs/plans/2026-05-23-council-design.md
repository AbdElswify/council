# Council — Design

**Status**: implemented in v0.1.0 (with minor beneficial deltas from this design — see CHANGELOG and post-implementation review notes in `docs/plans/2026-05-23-council-implementation.md`).
**Date**: 2026-05-23
**Author**: Abdarrahman ElSwify (with Claude)

## Overview

Council is a Claude Code plugin that orchestrates a flat, two-pass-audited
multi-agent workflow. The user invokes `/council <task>`; the main Claude Code
session becomes the **Mayor**, brainstorms the task with the user, writes an
integration contract, dispatches a set of dynamically-conceived specialist
**Workers** in parallel against that contract, audits each worker's output in
two passes (Mayor first, neutral Auditor second), and presents the final
integrated result.

Council is the leaner sibling of [tribunal][tribunal]. Both plugins solve
overlapping problems with different shapes:

| | Tribunal | Council |
|---|---|---|
| Orchestrator | Judge (main session) → Mayors (subagents) | Mayor (main session) |
| Hierarchy | Recursive: Judge → Mayor → Department → … (depth > 1) | Flat: 1 level (Mayor → Workers) |
| Integration | Recursive synthesis: each Mayor dispatches its children in dependency-ordered parallel batches, then synthesizes their manifests up the tree | Upfront contract + parallel dispatch + optional `depends_on`; the Mayor integration-checks seams rather than synthesizing |
| `recruit_plan` indirection | Yes (every Mayor/Department may recruit) | No (Mayor is in-session, dispatches directly) |
| Best fit | Complex tasks with natural decomposition trees | Tasks that fan out cleanly into 3–7 parallel pieces |

The flat hierarchy is the central simplification. Because the Mayor lives in
the main session, it can dispatch workers directly with `Agent` calls; nothing
recurses past depth 1. This sidesteps Claude Code [issue #19077][19077]
(subagent-to-subagent dispatch is blocked) by design rather than by workaround.

[tribunal]: https://github.com/AbdElswify/tribunal
[19077]: https://github.com/anthropics/claude-code/issues/19077

## Architecture

Council ships three artifacts:

1. **`/council` command** (`commands/council.md`) — the entry point. Contains
   the brainstorm prompt, the contract-writing instructions, the dispatch
   loop, the two-pass audit loop, the integration check, and the final report
   format. The "Mayor" is just this command's prompt logic running in the
   main session.

2. **`council-worker` subagent** (`agents/council-worker.md`) — a generic,
   dynamic specialist. The Mayor invents a specialty per worker
   (e.g. "API schema designer", "frontend integrator", "test author") and
   passes it as part of the prompt.
   - Tools: `Read, Write, Edit, Glob, Grep, Bash`
   - Explicitly excludes `Agent` and `Task` to enforce flat-hierarchy.

3. **`council-auditor` subagent** (`agents/council-auditor.md`) — neutral
   reviewer. Reads a worker's manifest, artifacts, the shared contract, and
   the audit history, then returns a fenced-JSON verdict
   (`APPROVED` or `NEEDS_REVISION`).
   - Tools: `Read, Glob, Grep` (read-only — cannot tamper with artifacts).

### Lifecycle

```
/council <task>
  │
  ├─ Phase 1: Brainstorm                      [Mayor ↔ User]
  │     Socratic questioning to pin down: definition of done,
  │     scope boundaries, constraints. User signals "ready to dispatch."
  │
  ├─ Phase 2: Contract                        [Mayor]
  │     Mayor writes .council-runs/<run-id>/contract.md:
  │       - Shared interfaces (file paths, function signatures, data shapes)
  │       - Naming conventions
  │       - Worker roster (specialty + scope per worker)
  │       - Dependency declarations (if any)
  │
  ├─ Phase 3: Dispatch                        [Mayor → Workers]
  │     For each dep-order layer:
  │       - Create workers/<specialty-slug>/ dir per worker
  │       - Dispatch council-worker with: specialty, scope,
  │         contract path, workspace path, upstream manifest paths
  │     Workers in the same layer run in parallel.
  │
  ├─ Phase 4: Audit (per worker, two-pass)    [Mayor + Auditor]
  │     Round 1:
  │       Pass 1: Mayor reviews manifest + artifacts vs contract.
  │               NEEDS_REVISION → re-dispatch worker, skip Pass 2.
  │               APPROVED → continue to Pass 2.
  │       Pass 2: Dispatch council-auditor (neutral).
  │               NEEDS_REVISION → re-dispatch worker with combined findings.
  │               APPROVED → worker done.
  │     Round 2 (if reached):
  │       Same passes, but contracted scope — auditors may ONLY check
  │       "did you fix what was asked in round 1." No new findings allowed.
  │     Round 3+ forbidden. If round 2 fails, force-accept and log unresolved.
  │
  ├─ Phase 5: Integration check               [Mayor]
  │     Mayor reads all worker manifests + the contract.
  │     Verifies seams: do the pieces actually compose?
  │     A broken seam re-dispatches the responsible worker(s) with the
  │     seam description (counts toward their round budget).
  │
  └─ Phase 6: Final report                    [Mayor → User]
        Summarize artifacts, audit verdicts, unresolved items.
        User accepts or pushes back. Pushback re-runs only the affected
        workers starting fresh at round 1.
```

## Components in detail

### Brainstorm (Phase 1)

Embedded in the `/council` command — **not** delegated to
`superpowers:brainstorming`. The brainstorm has a specific output (a
populated contract + worker roster), not a generic design doc.

The brainstorm prompt instructs the Mayor to:
- Ask one question at a time
- Prefer multiple-choice when possible
- Specifically surface:
  - what the seams between sub-tasks should be,
  - how many workers are realistically needed (3–7 is the council sweet
    spot; fewer means use a single agent, more means use tribunal),
  - what shared interfaces or files everyone will touch
- Stop when the user says "ready to dispatch" (or equivalent)

### Contract (Phase 2)

The contract is the single most important artifact. It is what makes
parallel dispatch safe.

`contract.md` schema:

```markdown
# Council Run <run-id>: Contract

## Task statement
<one paragraph distilled from the brainstorm>

## Shared interfaces
<file paths, function signatures, data shapes, schemas — anything two
or more workers must agree on>

## Naming conventions
<variable, file, identifier conventions>

## Worker roster
| slug | specialty | scope | depends_on |
|---|---|---|---|
| schema-designer | API schema designer | Define OpenAPI spec for user service | — |
| backend-impl    | Backend implementer | Implement endpoints conforming to spec | schema-designer |
| frontend-impl   | Frontend integrator | Build UI calling new endpoints | schema-designer |
| test-author     | Test author         | Integration tests for full flow | backend-impl, frontend-impl |

## Acceptance criteria
<concrete, testable bullets used by Mayor and Auditor>
```

`depends_on` is the escape hatch from pure parallel. Most workers should
have no dependencies; declare a dependency only for true blocking
relationships (e.g. backend cannot begin until schema is fixed).

### Worker (Phase 3)

`agents/council-worker.md` frontmatter:

```yaml
---
description: |
  Specialist worker dispatched by the council Mayor. Receives a specialty,
  scope, contract path, and workspace path. Does the work, writes artifacts
  and a manifest.json. Does NOT recruit further subagents.
tools: [Read, Write, Edit, Glob, Grep, Bash]
---
```

Dispatch prompt template (filled in by the Mayor):

```
You are a council worker.
Specialty: <specialty>
Scope: <scope>

Read the shared contract: <path to contract.md>.
You MUST conform to it. If the contract is ambiguous or wrong for your
scope, do NOT silently deviate — write your concern to
<workspace>/contract_concern.md and continue with your best interpretation.

Workspace: <workspace path>.
Write all artifacts to <workspace>/artifacts/.
Write a manifest at <workspace>/manifest.json with:
  - artifact paths (relative to workspace)
  - one-paragraph summary of what you did
  - any contract concerns
  - any seams you touched that other workers will need to align with

You may read the manifests of workers you depend on:
<list of upstream manifest paths>
```

The manifest also includes a `files_written` field — the union of every path the worker created or modified, used by Phase 5 for a cross-worker file-conflict scan.

### Auditor (Phase 4 Pass 2)

`agents/council-auditor.md` frontmatter:

```yaml
---
description: |
  Neutral Pass-2 auditor for a council worker. Read-only. Reads the
  worker's manifest, artifacts, the contract, and the audit history.
  Returns a fenced-JSON verdict.
tools: [Read, Glob, Grep]
---
```

Verdict format (fenced JSON in the auditor's return message):

```json
{
  "verdict": "NEEDS_REVISION",
  "round": 1,
  "pass": 2,
  "findings": [
    {"severity": "blocker",    "loc": "artifacts/schema.yaml:12", "issue": "..."},
    {"severity": "should-fix", "loc": "manifest.json",            "issue": "..."}
  ],
  "contract_concerns": [
    {"issue": "Contract section X under-specifies Y; suggest Z"}
  ]
}
```

`parse_verdict.py` requires `verdict`, `round`, `pass`, `findings`, and
`contract_concerns` and validates their types; `notes` is optional. See
`commands/council.md` for the canonical run.log event vocabulary.

Round 2 verdicts MUST only reference findings already present in
`audit_history.jsonl`. The auditor prompt explicitly forbids novel findings
on round 2 — it may only either approve or re-flag the unresolved subset.

## Convergence and audit memory

Policy: **contracting scope + hard cap of 2 rounds**.

- Each audit appends one line to `workers/<slug>/audit_history.jsonl`:
  `{round, pass, verdict, findings, contract_concerns, timestamp}`
- Both Mayor and Auditor are given the path to this file each round and
  instructed to read it before judging
- Round 1: full critique allowed
- Round 2: auditors instructed to refuse novel findings — they may only
  judge whether round 1's findings were addressed
- Round 3 is never dispatched. If round 2 still fails, the Mayor
  force-accepts and the final report lists unresolved findings with the
  full audit history attached
- Additional defensive cap: within a single round, no more than 2 Pass-1 NEEDS_REVISION re-dispatches before force-accepting that round. Prevents the Mayor from looping Pass 1 forever without ever reaching Pass 2.

Worst-case cost per worker:
- 1 initial worker run
- 1 re-dispatch (round 1 fix)
- up to 2 Mayor Pass-1 audits (rounds 1 + 2)
- up to 2 Auditor Pass-2 audits (rounds 1 + 2)
= **6 invocations**.

Worst-case for 5 workers: 30 invocations. Predictable ceiling.

## Integration model

**Upfront contract + shared workspace + parallel default + optional
`depends_on`.**

The contract is binding: workers conform or flag concerns. Both audit passes
check contract compliance AND work quality. If a contract concern is raised
by enough workers (heuristic: ≥2 workers flag the same section), the Mayor
revises the contract and re-dispatches affected workers — rare path,
treated as exceptional.

Phase 5 (integration check) is the Mayor's final seam audit. Even when each
worker passes audit individually, seams between workers can still break.
The Mayor reads all manifests and verifies the contract was actually
achieved in practice. A broken seam re-dispatches the responsible worker(s)
and consumes their round budget.

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

`<run-id>` = ISO-like timestamp + short random suffix
(e.g. `20260523T142301-a3f9`).

Runs are kept on disk. The Mayor does not consult prior runs by default
(see Known Limitations).

## Error handling

| Failure | Response |
|---|---|
| Worker crashes or returns malformed manifest | Mayor re-dispatches once with explicit "your last run failed to produce a valid manifest" prompt. Second failure → mark worker failed, log to final report, continue with remaining workers. |
| Auditor returns malformed JSON | Mayor re-dispatches auditor once with parse error. Second failure: synthesize an APPROVED Pass-2 verdict (with explanatory `notes` field) and append it to `audit_history.jsonl` so the audit trail is complete. Log a `pass2_synthetic_approval <slug>` event to `run.log` and surface in Phase 6's unresolved section. |
| Worker raises a *blocker* contract concern | Mayor pauses, revises contract, re-dispatches affected workers from round 1. |
| Worker raises a *should-fix* contract concern | Logged in final report, contract unchanged for this run. |
| Claude Code rate limit hit mid-dispatch | Mayor surfaces to user and pauses; user resumes when ready. |
| User pushback after final report | Mayor re-runs only affected workers, starting fresh at round 1. Previous `audit_history.jsonl` is preserved on disk but not consulted for the rerun. |

## Testing strategy

Following tribunal's pattern (`tests/` directory at repo root):

- **Smoke test**: `/council write a haiku about <topic>` — exercises
  brainstorm → dispatch (1 worker) → audit → report. Tiny, runs in <2 min.
- **Parallel test**: a task that naturally splits 3 ways (e.g. "explain X,
  give a Python impl, give a JS impl") — exercises parallel dispatch.
- **Dependency test**: a task with a true dep (e.g. "design schema then
  build CRUD against it") — exercises `depends_on` ordering.
- **Convergence test**: a worker designed to fail audit twice — verifies
  round 2 contraction and round-3 force-accept.
- **Auditor neutrality test**: a worker whose output the Mayor would
  approve but a neutral reviewer would reject (subtle bug) — verifies
  Pass 2 actually catches Mayor blind spots.

Tests are scripted prompts + expected-state assertions on
`.council-runs/<run-id>/` artifacts.

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

## Open questions for v1+

- Should the Mayor be able to dispatch a *third* worker mid-audit to
  investigate a contested finding? (Probably no for v1 — adds unbounded
  dispatch.)
- Should there be a `/council:resume <run-id>` command for picking up
  after pushback or crash? (Yes, but v2.)
- Should the auditor see the *other workers'* manifests when judging one
  worker? (Currently no — workers are audited in isolation against the
  contract; Phase 5 catches cross-worker correctness. Reconsider if
  Phase 5 misses too much.)
- Should the brainstorm step itself dispatch a worker to research an
  unfamiliar domain before the contract is written? (Tempting; defer to
  v2 to avoid blurring the brainstorm/dispatch phase boundary.)
