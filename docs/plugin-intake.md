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

### 2026-04-17 | source: CodeRabbit versus Copilot comparison and re-activation | by: Codex

Plugins:
`CodeRabbit`, `GitHub Copilot`

Observation:
Compared the two specifically as code-review options for this small private
repo. The conclusion was not "Copilot is bad"; it was "Copilot likely wins on
price and GitHub-native convenience, but CodeRabbit is still the likelier
stronger dedicated PR-review tool." Trevor chose to try CodeRabbit anyway
because review quality is the variable worth testing first.

Evidence:
Current CodeRabbit/Copilot comparison chat; `.coderabbit.yaml`;
`docs/codex-april-16-2026-impact.md`;
`docs/codex-plugin-operator-cheatsheet.md`

Recommended ledger delta:
Move `CodeRabbit` from passive "configured, not yet proven" wording to the
active bounded review-trial path; keep GitHub App activation as the remaining
manual step; preserve Copilot only as the cheaper GitHub-native fallback
baseline in the narrative rather than making it the active review lane.

Canonical ledger updated:
Yes

Notes:
This is still not a task-backed PR-review success record. It is the durable
decision trail for why the repo is trying CodeRabbit first despite the cost
argument in Copilot's favor.

### 2026-04-17 | source: CodeRabbit settings capture for later AI review | by: Codex

Plugins:
`CodeRabbit`

Observation:
The repo needed a durable, reviewable record of the exact CodeRabbit settings
discussed in chat, not just the high-level trial decision. The correct split
is: repo-supported settings go into `.coderabbit.yaml`; operator rationale,
blank UI fields, and support caveats such as slop detection live in a dedicated
companion doc.

Evidence:
Current CodeRabbit settings thread; `.coderabbit.yaml`;
`docs/coderabbit-review-settings.md`;
CodeRabbit official configuration reference and YAML guide

Recommended ledger delta:
No change to the canonical plugin stance. This is a settings-detail capture,
not a stance change.

Canonical ledger updated:
No

Notes:
This entry exists so future AI reviewers can audit the exact CodeRabbit field
choices and their rationale without replaying the chat.

### 2026-04-17 | source: chat plugin research sweep follow-up | by: Codex

Plugins:
`Claude Code for Codex`, `Codex Be Serious`, `Playwright MCP`,
`Project Autopilot`, `Greptile`, `Qodo Merge`, `Sourcery`, `DeepSource`,
`Snyk Code`, `Semgrep`, `SonarQube`, `Checkmarx`, `codex-plugin-scanner`,
`hol-guard`

Observation:
A chat-only plugin-research sweep surfaced five durable, repo-relevant
signals that did not exist in prior intake entries:

1. The hol.org registry publishes per-plugin trust and security scores and
   lists roughly 79 plugins, while prior repo-side research covered only a
   minority of that registry. Future plugin spikes should start from the
   registry rather than repeating a narrow sweep.
2. `codex-plugin-scanner` and `hol-guard` exist on PyPI as plugin-validation
   and trust-scoring tooling. They are candidate inputs for any future
   `plugin-eval`-style adoption spike, not a replacement for a task-backed
   trial.
3. Microsoft's `playwright-mcp` is a concrete MCP-server match for the
   operator's standing "default to Python Playwright for visual audits"
   rule in `~/.claude/CLAUDE.md`. This ties a specific MCP surface to an
   already-documented operating rule rather than treating Playwright as a
   generic MCP.
4. An untried commercial AI code-review tier exists alongside `CodeRabbit`:
   `Greptile`, `Qodo Merge`, `Sourcery`, `DeepSource`, `Snyk Code`,
   `Semgrep`, `SonarQube`, and `Checkmarx`. This is the explicit fallback
   set if `CodeRabbit`'s bounded trial does not justify its cost; the repo
   should not repeat open research when that question is reopened.
5. The HOL trust signal specifically records `Claude Code for Codex` at
   `trust 78 / caution 65` and `Codex Be Serious` at `trust 84 /
   security 90`. These are adoption-risk data points the canonical ledger
   does not currently carry for either plugin.

Evidence:
Current chat plugin-research sweep; hol.org registry page; PyPI listings
for `codex-plugin-scanner` and `hol-guard`; Microsoft `playwright-mcp`
repository; `https://github.com/AlexMi64/codex-project-autopilot` reachable
with `.codex-plugin/plugin.json` present (a specific solo-author community
candidate for any future `Autopilot` disambiguation); publicly indexed
comparison content for the commercial review tier.

Recommended ledger delta:
None today. No plugin was run on a real repo task, so the canonical
ledger's `Tried here?` column should not flip on any row. Treat this as
evidence that may shape three later moves:

- Before the next `plugin-eval`-scoped spike, install
  `codex-plugin-scanner` and optionally `hol-guard` and run them across
  the HOL registry to produce a trust-filtered candidate shortlist.
- When `Playwright MCP` is formally evaluated, wire the decision to the
  existing operator visual-audit rule rather than treating it as an
  unrelated MCP.
- If `CodeRabbit`'s bounded trial does not justify the cost, the
  commercial fallback set above is the pre-catalogued next round rather
  than another open research sweep.

Canonical ledger updated:
No.

Notes:
This entry is chat-research evidence only, not a task-backed trial.
Availability in session, reachability of a repo URL, and published trust
scores do not count as "tried here." The `Autopilot` row in the canonical
ledger was not disambiguated to `AlexMi64/codex-project-autopilot` because
the chat did not establish that the locally installed `Autopilot` and that
repository are the same artifact.

### 2026-04-17 | source: GIL-54 installed workflow-plugin state capture | by: Codex

Plugins:
`Autopilot`, `HOTL`, `Cavekit`

Observation:
The repo previously documented these as locally installed workflow plugins, but
did not yet capture their actual successful Codex install state, marketplace
identifier, enabled state, or the fact that `Cavekit` is installed under the
plugin id `ck`. The repo also lacked one durable setup companion explaining
that these three have no repo-committed config and are governed here by an
operational split rather than a checked-in settings file.

Evidence:
`~/.agents/plugins/marketplace.json`; `~/.codex/config.toml`;
`/Users/gillettes/plugins/codex-project-autopilot/.codex-plugin/plugin.json`;
`/Users/gillettes/plugins/hotl/.codex-plugin/plugin.json`;
`/Users/gillettes/plugins/cavekit/.codex-plugin/plugin.json`;
`docs/codex-workflow-plugin-setup.md`; `todo.md` `Work Record Log`
2026-04-17 `GIL-54`

Recommended ledger delta:
Update the canonical plugin ledger rows for `Autopilot`, `HOTL`, and
`Cavekit` from generic "installed locally" wording to "installed and enabled
in Codex", and add a durable companion-doc pointer for the exact install
state and settings posture.

Canonical ledger updated:
Yes

Notes:
This still does not count as a task-backed plugin trial. The durable change is
about install state and operating guidance, not proof that any of the three
improves real repo work yet.

### 2026-04-17 | source: Claude Code second-pass audit of CodeRabbit settings | by: Claude Code

Plugins:
`CodeRabbit`

Observation:
A deeper schema-aware audit of `.coderabbit.yaml` and
`docs/coderabbit-review-settings.md` surfaced two kinds of gap the first-pass
Codex self-audit did not catch:

1. `slop_detection` is a repo-config-supported `reviews.*` field per the live
   CodeRabbit schema, not a UI-only setting. The companion doc previously
   classified it under "UI-only and caveated settings" and described the
   desired enabled/label pair as a "Desired UI setting."
2. Four configurable surfaces are declared in the schema but not encoded in
   `.coderabbit.yaml`: `reviews.tools` (49 tools default to enabled),
   `reviews.pre_merge_checks` (docstring/title/description/issue_assessment
   checks default to warning mode), `reviews.finishing_touches` (per-PR
   docstring/unit-test generation toggles), top-level `code_generation`, and
   top-level `issue_enrichment`. The companion doc's "field-by-field" framing
   implied coverage it did not actually have.

Evidence:
Resolved `#/definitions/schema` from
`https://coderabbit.ai/integrations/schema.v2.json`; `jsonschema.validate`
against the full resolved schema; enumeration of `reviews.tools` sub-keys
with their `enabled.default` values; `.coderabbit.yaml`;
`docs/coderabbit-review-settings.md`.

Recommended ledger delta:
No stance change on the canonical plugin ledger. The repo still treats
`CodeRabbit` as the active bounded review trial. The fixes are settings-detail
corrections, not a new trial decision.

Canonical ledger updated:
No

Notes:
The companion doc was updated in the same landing to (a) move
`slop_detection` into the repo-supported settings table with the
public-repo caveat preserved, and (b) add a "Defaults we accept" section that
names the four unconfigured schema surfaces, the default behavior they imply,
and the known trial-scope risks they carry. `.coderabbit.yaml` gained an
explicit `slop_detection` block so the operator's documented preference is
encoded even if it is a no-op on private repos today.
