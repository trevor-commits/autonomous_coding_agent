## ADDED Requirements

### Requirement: Frozen executor envelope
An executor envelope MUST contain a schema version, envelope/work-order ID, executor identifier, strategy, wake/proposal bindings, the complete exact proposal-approval document and its canonical SHA-256, the complete embedded run contract and its canonical SHA-256, capability classes, risk, and envelope SHA-256; unknown fields or binding mismatches MUST fail closed. The executor MUST require the identical approval to remain current, unrevoked, unambiguous, and unexpired immediately before effects. Embedding both documents removes the external-path time-of-check/time-of-use gap while the current-store check preserves revocation.

#### Scenario: Contract changes after queueing
- **WHEN** the embedded run contract no longer matches the queued canonical SHA-256
- **THEN** the adapter blocks before invoking ACA

#### Scenario: Trace identity mismatch
- **WHEN** work-order ID, run ID, or run-trace ID do not satisfy the binding rule
- **THEN** the adapter rejects the envelope

#### Scenario: Approval is revoked after queueing
- **WHEN** the exact approval embedded in the envelope is absent or changed in the current approval store at effect time
- **THEN** the executor blocks before starting ACA

#### Scenario: Approval expires while queued
- **WHEN** the embedded approval is no longer active at effect time
- **THEN** the executor blocks before starting ACA

### Requirement: Existing global queue remains sole dispatcher
The partner bridge MUST place at most one already-authorized immutable envelope in the existing autonomous-loop ready queue and MUST NOT create another scheduler, daemon, packet queue, or execution lock.

#### Scenario: Healthy eligible wake
- **WHEN** exactly one approved low-risk decision is eligible and no packet is inflight
- **THEN** one no-clobber envelope is queued for the existing autonomous loop

### Requirement: Kill switches remain authoritative
All existing autonomous-loop kill switches MUST block partner queueing and execution, including a switch that appears between observation and dispatch.

#### Scenario: Kill switch races dispatch
- **WHEN** a kill switch appears after snapshot creation but before queue publish
- **THEN** no new envelope is queued and the decision receipt records the stop

### Requirement: Structured adapter result
The adapter MUST return a bounded structured result containing terminal state, readiness verdict, retained worktree path, report path, and report SHA-256; it MUST NOT copy raw worker output, secrets, or private observation content into the global dispatch receipt.

#### Scenario: Successful episode
- **WHEN** ACA returns a schema-valid `COMPLETE` plus `READY` report backed by final evidence
- **THEN** the adapter exits zero and returns the report path/hash

#### Scenario: Failed episode
- **WHEN** ACA times out, blocks, or returns invalid output
- **THEN** the adapter exits nonzero and the existing global loop moves the packet to failed without promoting success learning
