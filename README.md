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
