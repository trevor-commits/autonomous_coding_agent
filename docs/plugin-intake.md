# Plugin Intake Log

This file is the append-only intake surface for plugin observations, trials,
and partial conclusions from any Codex conversation working in this repo.

Use this log when:

- a chat used a plugin on a real repo task
- a chat learned something new about a plugin's fit, limits, or failure modes
- a chat has evidence that may change the canonical plugin stance later

Do not use this log to silently replace the repo's current plugin stance. The
curated current-truth surface remains
`docs/codex-april-16-2026-impact.md` section `Plugin decision ledger`.

## Workflow

1. Append a new entry here with source, evidence, and the recommended ledger
   delta.
2. Update the canonical `Plugin decision ledger` only when the repo's current
   stance, `Tried here?` status, allowed use, forbidden use, or revisit trigger
   actually changes.
3. Leave prior entries intact. Corrections, disagreements, and later evidence
   are new entries, not rewrites.

## Entry Template

```text
### YYYY-MM-DD | source: GIL-N / chat label | by: Codex
Plugins:
Observation:
Evidence:
Recommended ledger delta:
Canonical ledger updated:
Notes:
```

## Entries

### 2026-04-17 | source: GIL-53 plugin decision ledger landing | by: Codex

Plugins:
`Linear`, `GitHub`, `Superpowers`, `Figma`, `Vercel`, `Cloudflare`, `Gmail`,
`Google Calendar`, `Hugging Face`

Observation:
Established the first durable per-plugin stance table for this repo, including
`Tried here?`, current stance, allowed use, forbidden use, and revisit
triggers.

Evidence:
`docs/codex-april-16-2026-impact.md`; `README.md`; `GUIDE.md`; `todo.md`
`Work Record Log` 2026-04-17 `GIL-53`

Recommended ledger delta:
None. This entry records the ledger's initial creation event.

Canonical ledger updated:
Yes

Notes:
This counts as the ledger bootstrap, not a task-backed trial for plugins that
were merely available in the session.

### 2026-04-17 | source: GIL-54 operator guide and plugin research | by: Codex

Plugins:
`Autopilot`, `HOTL`, `Cavekit`, `CodeRabbit`, `plugin-eval`, `Brooks Lint`,
`Session Orchestrator`, `Agent Message Queue`, `Registry Broker`,
`Claude Code for Codex`, `ECC`

Observation:
Expanded the repo's plugin coverage from the initial enabled-session surface
into locally installed workflow plugins plus researched later-spike candidates,
and separated "what this plugin should own" from the canonical use/not-use
stance.

Evidence:
`docs/codex-plugin-operator-cheatsheet.md`;
`docs/codex-april-16-2026-impact.md`; `todo.md` `Work Record Log` 2026-04-17
`GIL-54`

Recommended ledger delta:
Already applied in `GIL-54` for the covered plugins. Future task-backed trials
should append here first before further curating the canonical ledger.

Canonical ledger updated:
Yes

Notes:
Installation, docs review, and operator-fit research do not count as
task-backed proof that a plugin improves real repo work.
