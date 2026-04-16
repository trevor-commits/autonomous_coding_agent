# Queue Upgrade Research And Decisions — 2026-04-16

## Purpose

Preserve the reasoning behind the 2026-04-16 unattended-queue upgrade so later AI auditors can reconstruct:

- what Trevor asked for
- what external evidence was consulted
- which improvements were adopted into current repo truth
- which weaker alternatives were rejected
- which implementation choices remain intentionally open

This is a design-history memo, not an active source-of-truth doc. Current truth lives in `canonical-architecture.md`, `QUEUE-RUNS.md`, `LINEAR.md`, `PROMPTS.md`, `RULES.md`, `IMPLEMENTATION-PLAN.md`, and `todo.md`.

## Trigger

Trevor asked whether there was anything current on the internet that should improve the unattended Codex queue, then asked for all worthwhile improvements to be implemented thoroughly and documented in a way other AIs could audit later.

He also kept tightening the bar:

- keep Linear as routing metadata, not a command surface
- keep later Claude audit/test work as explicit separate issues rather than letting the Codex queue absorb it
- require Codex to self-test frequently during queue execution
- let the orchestrator skip, defer, or split non-queueable work instead of stalling the entire lane
- add stronger guardrails against drift and opportunistic scope expansion
- preserve the reasoning path in-repo so later AIs can audit not just the destination, but how the decision was reached

## Working Question

How should the unattended supervisor-mediated queue be upgraded so it is:

- more durable
- more observable
- better guarded against drift and overreach
- easier to resume after failures
- better at intake normalization before Codex starts writing
- easier to evaluate empirically instead of by anecdote

And how should that reasoning be recorded so another AI can later audit whether the adopted contract actually matches Trevor's intent?

## Conversation Progression

1. The first design question was whether Linear should directly command Codex or whether one giant long-running Codex session should process issues indefinitely.
   The answer was no on both counts. The repo already favored fresh Codex sessions per bounded issue and supervisor-owned legality, so the correct shape remained one issue per fresh Codex run, with the supervisor choosing the next eligible issue.
2. The next step was to define the unattended queue contract itself.
   That work established the supervisor-mediated queue, separate Claude audit/test issues, per-issue commits, continuous Codex self-testing, and skip/block behavior for non-queueable work.
3. Trevor then asked for stronger guardrails against drift and scope creep.
   That added frozen issue snapshots, versioned queue/prompt contracts, allowed-path boundaries, post-claim drift invalidation, and the adjacent-blocker rule for unspecced discoveries.
4. Trevor then asked for a heavy review of the landing.
   That review repaired stale or under-specified queue truth in the repo before more upgrades were layered on top.
5. Only after those contract repairs did the external-research pass happen.
   That sequencing matters: the internet-backed upgrades were applied onto a coherent base instead of being sprayed onto a still-drifting design.

## Adopted Operator Constraints

The final contract is not just "what the internet suggested." It is the intersection of current external guidance with Trevor's local operating constraints:

- Linear may wake and enrich the queue, but it still may not directly command Codex.
- Codex remains a bounded executor. The supervisor owns legality, claiming, retries, resume, and queue correctness.
- Claude Code audit/test work stays in a separate issue lane and should not be opportunistically consumed by the unattended Codex queue.
- Codex is expected to test its own work frequently during queue execution; later external audit is an additional layer, not a replacement for self-verification.
- New issues or defects discovered during queue execution should be fixed in-run only when they satisfy the adjacent-blocker rule. Otherwise they are skipped, split, or deferred.
- Reasoning must be durable. A chat-only explanation is treated as operationally insufficient.

## External Evidence Consulted

### Linear

- Linear documents webhooks as HTTP(S) push notifications for created or updated data and explicitly suggests using them to trigger downstream automation and integrations.
- Linear Triage exists as a distinct inbound queue, and Triage-side enrichment features exist for routing and categorization.

Design implication:

- queue intake should be webhook-first, not polling-first
- intake should normalize and enrich routing metadata before an issue reaches the Codex queue
- Linear may wake the supervisor and enrich routing metadata, but it still must not become the workflow owner or the source of repo truth

### OpenAI

- OpenAI's practical guide to building agents emphasizes strong foundations, structured instructions, guardrails, human intervention for safety, and iterative deployment instead of all-at-once autonomy.
- OpenAI's Agents SDK evolution article emphasizes controlled harnesses, externalized state, durability, snapshotting, and rehydration after sandbox or container failure.

Design implication:

- queue runs should remain schema-bound and supervisor-owned
- high-risk actions need explicit approval gates instead of "careful autonomy"
- run state should be externalized so interrupted work can resume safely from durable checkpoints

### Durable Workflow Runtime

- Vercel Workflow documents resumable, durable, observable workflows with persisted state, event logs, retries, hooks, and pause/resume semantics.

Design implication:

- the supervisor should be expressible as a durable workflow rather than as a fragile forever-process
- the canonical architecture should describe durability and resumability as requirements, while leaving the exact runtime substrate open

### Observability

- OpenTelemetry traces are described as structured logs with correlation and hierarchy, enabling end-to-end understanding across processes and services.

Design implication:

- queue runs need a first-class `run_trace_id` and structured lifecycle events, not just a pile of unrelated logs
- comments, artifacts, and final reports should correlate back to the same run trace

## Decisions Adopted

### 1. Verified webhooks become the preferred unattended intake trigger

Adopted because webhook-driven intake is a cleaner primary trigger than blind polling when the source system already supports authenticated push notifications.

Not adopted as "webhooks only." A reconciliation sweep remains part of the design so missed or delayed events cannot silently desynchronize the queue.

### 2. A pre-queue normalization lane becomes part of the design

Adopted because the queue should not be the first place where malformed, under-specified, or risky work is discovered.

This was modeled as:

- Linear Triage when available
- `Inbox` as the manual equivalent when Triage is unavailable
- queue eligibility only after routing metadata, spec links, and risk posture are normalized

### 3. Risk and approval posture become explicit queue metadata

Adopted because the old queue contract bounded scope and drift, but it did not make high-risk or approval-bound work explicit enough.

The design now treats high-risk actions as manual by default and blocks a run when new approval-bound work is discovered mid-run.

### 4. Durable workflow semantics are now part of the canonical architecture

Adopted because a walk-away queue that cannot resume safely after interruption is operationally weak, even if the policy is otherwise correct.

The docs now require:

- durable claim and trace identifiers
- externalized run state
- checkpoint-based resume

The exact runtime substrate is still open.

### 5. Trace-linked observability is now first-class

Adopted because detached logs are not enough for later audit, replay, or comparative evaluation.

The docs now require:

- `run_trace_id`
- structured lifecycle events
- trace-linked reports and artifacts

The design deliberately stops short of requiring a specific vendor backend. The requirement is correlation and reconstructability, not premature platform lock-in.

### 6. Benchmark or eval evidence is required before widening autonomy

Adopted because queue or prompt changes should not be justified only by intuition or isolated anecdote.

The docs now require trace-backed benchmark or eval comparison when autonomy boundaries or queue behavior change materially.

### 7. Untrusted queue text stays untrusted

Adopted because issue descriptions, logs, and webhook payloads should not be silently blended into higher-privilege prompt instructions.

The prompt system now requires untrusted-input separation.

### 8. The reasoning trail itself becomes a first-class artifact

Adopted because unattended execution governance is unusually vulnerable to "we remember why we did that" drift.

The repo therefore stores:

- active truth in source-of-truth docs
- durable execution/audit records in `todo.md`
- dated reasoning and design-history context in this memo

This separates current law from historical reasoning without letting the reasoning disappear.

## Weaker Alternatives Rejected

### Direct Codex-in-Linear delegation

Rejected again. It would make Linear behave like a command surface rather than a routing surface and would weaken the supervisor-owned legality model.

### Polling-only queue discovery

Rejected as the preferred design. Polling can remain a recovery path, but not the primary control plane when webhook delivery exists.

### Logs-only observability

Rejected because later audits need correlation across intake, claim, verification, push, comment, and exit.

### "Just let Codex decide when it found something risky"

Rejected because risk and approval posture need explicit gates, not only model judgment.

### Vendor lock-in at the architecture layer

Rejected. Durable workflow semantics were adopted, but not a hard platform lock. Vercel Workflow is a strong fit and useful reference, not a canonical requirement.

### "The chat transcript is enough context for later auditors"

Rejected because chats are transient, hard to cite cleanly, and too easy to summarize selectively after the fact. Repo-visible records are required.

## Mapping To Repo Truth

The decisions above were threaded into:

- `canonical-architecture.md`
- `QUEUE-RUNS.md`
- `LINEAR.md`
- `PROMPTS.md`
- `RULES.md`
- `IMPLEMENTATION-PLAN.md`

Navigation and placement support were also updated so later agents can find this memo quickly:

- `STRUCTURE.md`
- `GUIDE.md`
- `README.md`

Durable task records live in `todo.md`.

## Still Intentionally Open

- Which durable workflow substrate to use in the eventual implementation
- Whether the actual Linear workspace enables Triage immediately or keeps `Inbox` as the manual equivalent for a while
- Which concrete tracing backend sits behind the trace IDs and structured events
- Whether OpenAI background execution should be used directly in the eventual implementation, versus only adopting the durability pattern at the supervisor layer

These are open by design because the repo is currently defining the contract and implementation plan, not prematurely locking the runtime substrate before the build phases.

## Audit Guidance For Later AIs

If you are auditing this decision later, verify in this order:

1. `canonical-architecture.md` for the system-level contract
2. `QUEUE-RUNS.md` for issue-run semantics and stop/skip behavior
3. `LINEAR.md` for what Linear may and may not do
4. `PROMPTS.md` and `RULES.md` for executor/prompt-level enforcement
5. `IMPLEMENTATION-PLAN.md` for where these ideas are expected to land in code later
6. `todo.md` `Work Record Log`, `Audit Record Log`, `Test Evidence Log`, and `Feedback Decision Log` for what actually happened in this change
7. this memo for why the contract took this shape and which alternatives were deliberately rejected

The main thing to challenge is not "could the system be more autonomous?" The better audit question is "did autonomy expand in the supervisor and evidence layers, or did it accidentally expand in the wrong place by making Linear or Codex more authoritative than intended?"

These are implementation-phase decisions, not current architecture gaps.

## Sources

- Linear API and Webhooks: [linear.app/docs/api-and-webhooks](https://linear.app/docs/api-and-webhooks)
- Linear Triage: [linear.app/docs/triage](https://linear.app/docs/triage)
- OpenAI, *A practical guide to building agents*: [cdn.openai.com/business-guides-and-resources/a-practical-guide-to-building-agents.pdf](https://cdn.openai.com/business-guides-and-resources/a-practical-guide-to-building-agents.pdf)
- OpenAI, *The next evolution of the Agents SDK*: [openai.com/index/the-next-evolution-of-the-agents-sdk](https://openai.com/index/the-next-evolution-of-the-agents-sdk/)
- Vercel Workflow: [vercel.com/docs/workflow](https://vercel.com/docs/workflow)
- OpenTelemetry traces: [opentelemetry.io/docs/concepts/signals/traces](https://opentelemetry.io/docs/concepts/signals/traces/)
