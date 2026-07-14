# outcome-benefit-learning Specification

## Purpose
TBD - created by archiving change autonomous-partner-reposition. Update Purpose after archive.
## Requirements
### Requirement: Provenance-bound lesson candidates
The partner policy MUST create lesson candidates only from a schema-valid executor outcome and MUST include source receipt hash, claim, scope, confidence, contradiction state, and expiry or review date.

#### Scenario: Successful verified outcome
- **WHEN** an episode is `COMPLETE` and `READY` with a valid report hash
- **THEN** the policy may emit a scoped operational lesson candidate tied to that outcome

#### Scenario: Failed outcome
- **WHEN** an episode blocks, times out, or has invalid evidence
- **THEN** the policy cannot emit a success lesson and may emit only a failure-prevention candidate

### Requirement: Measured benefit candidate
An outcome candidate MUST distinguish produced artifact, adopted use, time saved, harm prevented, quality change, operator feedback, and unknown benefit rather than treating completion as benefit.

#### Scenario: Completion without adoption evidence
- **WHEN** an episode produces an artifact but no use or operator feedback exists
- **THEN** benefit status remains unknown rather than positive

### Requirement: Existing global memory owns promotion
ACA MUST emit candidates only; existing global memory, improvement, goal, and benefit surfaces MUST decide promotion, deduplication, staleness, and contradiction resolution.

#### Scenario: Candidate is returned
- **WHEN** ACA emits a lesson candidate
- **THEN** ACA does not create a long-lived partner-memory record or silently rewrite global truth

### Requirement: Identity and values change only by approval
Any candidate that changes configured values, authority, spiritual framing, relationship boundaries, or durable identity MUST require an exact operator approval binding before it can become active.

#### Scenario: Outcome suggests value change
- **WHEN** a lesson candidate proposes changing a configured value
- **THEN** it is labeled `identity_amendment` and remains inactive without operator approval
