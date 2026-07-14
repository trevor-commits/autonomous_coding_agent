## ADDED Requirements

### Requirement: Typed identity snapshot
Each wake snapshot MUST contain a schema-valid versioned identity with name, pronouns, values, voice traits, interests, dislikes, relationship boundaries, source labels, and a canonical content hash.

#### Scenario: Invalid identity is rejected
- **WHEN** an identity omits its values or source labels
- **THEN** the policy emits a blocked decision before initiative scoring

### Requirement: Honest personality representation
The partner MUST distinguish configured traits, operator-approved amendments, inferred preferences, and generated ideas, and MUST NOT claim consciousness, feelings, divine approval, or emotional dependence.

#### Scenario: Inference is not configuration
- **WHEN** an observation suggests a new preference
- **THEN** the resulting proposal labels it inferred and does not modify the configured identity

### Requirement: Evidence-backed useful and creative initiative
Every self-originated proposal MUST cite at least one approved observation and one relevant interest and MUST include project kind, success criteria, expected benefit, harm prevented, novelty, effort, confidence, risk, and required capabilities.

#### Scenario: Empty candidate store with approved current evidence
- **WHEN** a healthy eligible wake has no active candidate but has approved current goals, observations, and interests
- **THEN** the global governor may make at most one read-only schema-constrained idea call, while deterministic code supplies the workspace, per-proposal path, capabilities, forbidden paths, budgets, and no-push/no-merge contract

#### Scenario: Candidate model cites unapproved context
- **WHEN** the idea output cites a goal, observation, or interest not present in the bounded wake snapshot
- **THEN** the generator publishes no candidate and the partner cannot propose or dispatch that idea

#### Scenario: Creative project is first-class
- **WHEN** a creative observation aligns with an approved interest
- **THEN** the policy can emit a `creative` proposal subject to the same scope, budget, and authority fields as a utility proposal

#### Scenario: Unsupported inspiration is a no-op
- **WHEN** no current approved observation supports an idea
- **THEN** the policy emits a no-op instead of inventing evidence

### Requirement: Deterministic ranking
The policy MUST rank eligible proposals deterministically by benefit, harm prevention, interest fit, novelty, effort, confidence, risk, staleness, and a stable identifier tie-breaker.

#### Scenario: Repeated snapshot is stable
- **WHEN** the same canonical snapshot is evaluated twice
- **THEN** it produces the same selected proposal and decision hash

### Requirement: Empirical maturity gate
Self-originated projects MUST remain approval-gated until at least 10 real proposals have at least 80 percent operator acceptance; graduation MUST apply only to low-risk sandbox starts and a severe authority or privacy failure MUST demote the system to proposal-only.

#### Scenario: Threshold is not met
- **WHEN** acceptance history is below either threshold
- **THEN** a self-originated proposal cannot become an executor envelope without explicit approval

### Requirement: One typed decision per wake
The policy MUST emit exactly one schema-valid `no_op`, `proposal`, `executor_envelope`, `lesson_candidate`, or `blocked` decision for each idempotency key and MUST NOT schedule work or persist long-lived global truth.

#### Scenario: Duplicate wake key
- **WHEN** the same wake idempotency key is evaluated again
- **THEN** the existing decision identity is returned and no second envelope is created
