# executor-evidence-authority Specification

## Purpose
Define the unattended executor's pre-effect authority, evidence-derived readiness, actual-diff enforcement, default-deny command boundary, and atomic run truth.
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

#### Scenario: Rename cannot hide the changed source path
- **WHEN** a builder renames a file from a forbidden or out-of-scope path into an allowed path
- **THEN** the executor evaluates both the source and destination paths and blocks the run

### Requirement: Unknown commands fail closed
The shell classifier MUST classify an unmatched command as escalation-required or denied; only exact repo-contract commands and explicit safe built-ins may be auto-allowed.

#### Scenario: Unknown network command is not auto-allowed
- **WHEN** a builder reports `curl https://example.com`
- **THEN** command classification is not `AUTO_ALLOW`

### Requirement: Model builder is edit-only
The model builder MUST be limited to scoped patch application plus bounded filename discovery. It MUST NOT execute repository code, contract checks, package managers, Git commands, network clients, or arbitrary shell commands. Exact command allowlists and reported command text MUST NOT expand this boundary.

#### Scenario: Contract command is supplied to the model builder
- **WHEN** a run contract names a verification command that would otherwise be allowed for deterministic execution
- **THEN** the model builder cannot execute it and the supervisor remains the only process allowed to run the command

#### Scenario: Compound or absolute-denied command is supplied
- **WHEN** a builder attempts a nested, compound, privileged, remote, destructive, or Git state-moving command
- **THEN** the request is denied before any narrower allowlist is considered

### Requirement: Deterministic execution is supervisor-sandboxed
Every repository command executed for setup, verification, or final evidence MUST run in a supervisor-owned no-network sandbox with a scrubbed environment, private runtime directories, closed stdin, read access limited to the exact worktree plus required system runtime files, and write access limited to declared run paths plus supervisor temporary state.

#### Scenario: Command reads host-private state
- **WHEN** a repository command attempts to read a file outside the exact worktree and approved system runtime roots or inspect another process's environment
- **THEN** the sandbox denies the access without exposing the host value

#### Scenario: Command writes sensitive control residue
- **WHEN** a repository command attempts to create or modify any `.env*`, nested `.git`, or nested `.agent` path
- **THEN** the sandbox denies the write and the run cannot become ready

#### Scenario: Verification mutates builder output
- **WHEN** any targeted or final verification command changes the authoritative worktree diff, including the bytes of an already changed file
- **THEN** the supervisor blocks the run because verification cannot become a second writer

### Requirement: Sensitive residue is independently checked
The supervisor MUST fingerprint sensitive residue before model or repository effects and recheck it after builder, verification, UI, and final-verification stages using direct filesystem inspection independent of Git visibility. Unexpected creation or mutation of `.env*`, nested `.git`, or nested `.agent` content MUST block readiness.

#### Scenario: Nested control directory is hidden from Git
- **WHEN** a nested `.git` or `.agent` directory is created but omitted from Git status
- **THEN** the filesystem residue check still detects it and blocks the run

#### Scenario: Sensitive path is replaced through a symlink
- **WHEN** an allowed runtime or worktree path resolves outside its approved root
- **THEN** the supervisor rejects the path before model or command execution

### Requirement: Atomic run truth
Every JSON state or report update MUST be written to a same-directory temporary file, flushed, fsynced, and atomically replaced so a failed publish preserves the prior complete JSON document.

#### Scenario: Publish fails
- **WHEN** atomic replacement fails after a previous state exists
- **THEN** the previous state remains valid and temporary residue is removed
