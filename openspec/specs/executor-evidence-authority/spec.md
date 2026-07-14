# executor-evidence-authority Specification

## Purpose
TBD - created by archiving change autonomous-partner-reposition. Update Purpose after archive.
## Requirements
### Requirement: Pre-effect unattended authority
The executor MUST reject a run marked high risk or approval-required before creating a builder worktree or starting a builder session unless the governed envelope embeds a complete schema-valid exact proposal approval and the global adapter confirms that identical approval remains current and active immediately before effects.

#### Scenario: High-risk direct run is blocked
- **WHEN** a run contract has `risk_level` equal to `high`
- **THEN** the executor records a blocked preflight outcome and does not create a builder worktree or session

#### Scenario: Pending approval is blocked
- **WHEN** a run contract has `approval_required` equal to true and no exact approval binding
- **THEN** the executor blocks before builder effects

#### Scenario: Approval id and hash lack the source document
- **WHEN** an envelope supplies only an approval id/hash or a binding for a different proposal or capability set
- **THEN** validation fails before builder effects

### Requirement: Evidence-derived final readiness
The executor MUST derive final-gate evidence from a fresh authoritative verification rerun and artifacts that exist on disk; it MUST NOT mark evidence booleans true by assertion alone.

#### Scenario: Missing artifact prevents readiness
- **WHEN** a required artifact named by the final gate is absent
- **THEN** a strategy proposal of `COMPLETE` cannot produce `READY`

#### Scenario: Final rerun failure prevents readiness
- **WHEN** any authoritative final verification command fails
- **THEN** the run returns to repair or blocks when its evidence-loop budget is exhausted

### Requirement: Actual worktree activity is authoritative
The executor MUST compare the actual worktree diff with builder-reported files and MUST enforce path policy over their union.

#### Scenario: Unreported forbidden change is caught
- **WHEN** a builder changes an out-of-scope file but omits it from `files_changed`
- **THEN** the executor blocks and names the actual path

### Requirement: Unknown commands fail closed
The shell classifier MUST classify an unmatched command as escalation-required or denied; only exact repo-contract commands and explicit safe built-ins may be auto-allowed.

#### Scenario: Unknown network command is not auto-allowed
- **WHEN** a builder reports `curl https://example.com`
- **THEN** command classification is not `AUTO_ALLOW`

### Requirement: Atomic run truth
Every JSON state or report update MUST be written to a same-directory temporary file, flushed, fsynced, and atomically replaced so a failed publish preserves the prior complete JSON document.

#### Scenario: Publish fails
- **WHEN** atomic replacement fails after a previous state exists
- **THEN** the previous state remains valid and temporary residue is removed

