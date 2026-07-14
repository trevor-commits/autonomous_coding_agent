from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path, PurePosixPath
import re
import shlex

from supervisor.contracts import RepoContract, RunContract


class ShellClass(str, Enum):
    AUTO_ALLOW = "auto_allow"
    AUTO_DENY = "auto_deny"
    ESCALATE = "escalate"


class PolicyViolationError(RuntimeError):
    """Raised when a policy rule is violated."""


class BudgetExceededError(PolicyViolationError):
    """Raised when a run exceeds one of its configured budgets."""


@dataclass(frozen=True)
class CommandDecision:
    shell_class: ShellClass
    reason: str


AUTO_DENY_PREFIXES = (
    "git push",
    "git pull",
    "git merge",
    "git rebase",
    "git checkout",
    "git switch",
    "sudo",
    "ssh",
    "scp",
    "rm -rf",
)

ESCALATE_PREFIXES = (
    "npm install",
    "pnpm install",
    "yarn install",
    "pip install",
    "uv pip install",
    "poetry install",
    "prisma migrate",
    "alembic upgrade",
    "rake db:migrate",
    "terraform ",
    "pulumi ",
    "kubectl ",
    "docker compose build",
    "docker build",
)

ESCALATE_PATH_PARTS = (
    ".github/",
    "infra/",
    "deploy/",
    "migrations/",
    "auth",
)

AUTO_DENY_PATHS = (
    ".env",
    ".env.local",
)

_FIND_NO_ARGUMENT = {"-print", "-print0", "-prune", "-o", "-a", "-not", "!", "(", ")"}
_FIND_STRING_ARGUMENT = {"-name", "-iname", "-path", "-wholename", "-type"}
_FIND_INTEGER_ARGUMENT = {"-maxdepth", "-mindepth"}
_FIND_EFFECT_ACTIONS = {"-delete", "-exec", "-execdir", "-ok", "-okdir", "-fprint", "-fprintf", "-fls"}
_READ_ONLY_METADATA_COMMANDS = {
    ("pwd",),
    ("git", "status", "-sb"),
    ("git", "status", "--short"),
    ("git", "rev-parse", "--show-toplevel"),
    ("git", "log", "-1", "--oneline"),
    ("git", "diff", "--check"),
    ("git", "diff", "--stat"),
    ("git", "diff", "--name-only"),
}


def classify_command(
    command: str,
    repo_contract: RepoContract | None = None,
    *,
    allowed_commands: tuple[str, ...] = (),
) -> CommandDecision:
    normalized = command.strip()
    contract_commands = repo_contract.commands.auto_allow_commands() if repo_contract else ()
    if normalized in {*contract_commands, *allowed_commands}:
        return CommandDecision(
            shell_class=ShellClass.AUTO_ALLOW,
            reason="repo contract command",
        )
    if any(normalized.startswith(prefix) for prefix in AUTO_DENY_PREFIXES):
        return CommandDecision(
            shell_class=ShellClass.AUTO_DENY,
            reason="matches deny-list shell policy",
        )
    if any(normalized.startswith(prefix) for prefix in ESCALATE_PREFIXES):
        return CommandDecision(
            shell_class=ShellClass.ESCALATE,
            reason="matches escalate-only shell policy",
        )
    if _is_bounded_read_only_discovery(normalized):
        return CommandDecision(
            shell_class=ShellClass.AUTO_ALLOW,
            reason="bounded read-only discovery command",
        )
    return CommandDecision(
        shell_class=ShellClass.ESCALATE,
        reason="command is not an exact repo-contract command or a classified policy command",
    )


def _is_bounded_read_only_discovery(command: str) -> bool:
    if len(command) > 4000:
        return False
    # Fail closed before shell parsing. These bytes can create a second command,
    # expand data outside the repository, or execute command substitution even
    # when the tokenized shape later resembles a read-only discovery command.
    if any(character in command for character in ("\n", "\r", "$", "`")):
        return False
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars="|&;<>")
        lexer.whitespace_split = True
        lexer.commenters = ""
        tokens = list(lexer)
    except ValueError:
        return False
    if not tokens or len(tokens) > 80:
        return False
    if any(token in {";", "||", ">", ">>", "<", "<<", "&"} for token in tokens):
        return False

    sequences = _split_tokens(tokens, "&&")
    if sequences is None:
        return False
    for sequence in sequences:
        pipeline = _split_tokens(sequence, "|")
        if pipeline is None or len(pipeline) > 3:
            return False
        source = pipeline[0]
        if tuple(source) in _READ_ONLY_METADATA_COMMANDS:
            if len(pipeline) != 1:
                return False
            continue
        if not (_is_bounded_find_tokens(source) or _is_bounded_rg_files_tokens(source)):
            return False
        if any(not _is_output_only_filter(stage) for stage in pipeline[1:]):
            return False
    return True


def _split_tokens(tokens: list[str], delimiter: str) -> list[list[str]] | None:
    groups: list[list[str]] = [[]]
    for token in tokens:
        if token == delimiter:
            if not groups[-1]:
                return None
            groups.append([])
        else:
            groups[-1].append(token)
    return groups if groups[-1] else None


def _is_bounded_find_tokens(tokens: list[str]) -> bool:
    if not tokens or tokens[0] != "find":
        return False
    index = 1
    expression_started = False
    while index < len(tokens):
        token = tokens[index]
        if token in _FIND_EFFECT_ACTIONS:
            return False
        if token in _FIND_NO_ARGUMENT:
            expression_started = True
            index += 1
            continue
        if token in _FIND_INTEGER_ARGUMENT:
            expression_started = True
            if index + 1 >= len(tokens) or not tokens[index + 1].isdigit():
                return False
            index += 2
            continue
        if token in _FIND_STRING_ARGUMENT:
            expression_started = True
            if index + 1 >= len(tokens) or len(tokens[index + 1]) > 300:
                return False
            index += 2
            continue
        if token.startswith("-") or expression_started:
            return False
        if token == "~" or token.startswith("~/"):
            return False
        root = PurePosixPath(token)
        if root.is_absolute() or ".." in root.parts:
            return False
        index += 1
    return True


def _is_bounded_rg_files_tokens(tokens: list[str]) -> bool:
    if len(tokens) < 2 or tokens[:2] != ["rg", "--files"]:
        return False
    index = 2
    while index < len(tokens):
        token = tokens[index]
        if token in {"-g", "--glob"}:
            if index + 1 >= len(tokens) or len(tokens[index + 1]) > 300:
                return False
            index += 2
            continue
        if token in {"--hidden", "--no-hidden", "--no-ignore", "--no-ignore-vcs"}:
            index += 1
            continue
        if token.startswith("-"):
            return False
        if token == "~" or token.startswith("~/"):
            return False
        root = PurePosixPath(token)
        if len(token) > 300 or root.is_absolute() or ".." in root.parts:
            return False
        index += 1
    return True


def _is_output_only_filter(tokens: list[str]) -> bool:
    if tokens == ["sort"]:
        return True
    if len(tokens) != 3 or tokens[:2] != ["sed", "-n"]:
        return False
    match = re.fullmatch(r"(\d{1,6})(?:,(\d{1,6}))?p", tokens[2])
    if match is None:
        return False
    start = int(match.group(1))
    end = int(match.group(2) or match.group(1))
    return 1 <= start <= end <= 10000


def classify_path_change(relative_path: str) -> CommandDecision:
    normalized = relative_path.strip()
    while normalized.startswith("./"):
        normalized = normalized[2:]
    if normalized in AUTO_DENY_PATHS or normalized.startswith(".env."):
        return CommandDecision(
            shell_class=ShellClass.AUTO_DENY,
            reason="secret file writes are denied",
        )
    if any(part in normalized for part in ESCALATE_PATH_PARTS):
        return CommandDecision(
            shell_class=ShellClass.ESCALATE,
            reason="high-risk path requires review or approval",
        )
    return CommandDecision(
        shell_class=ShellClass.AUTO_ALLOW,
        reason="path is inside normal repo scope",
    )


def enforce_scope(repo_root: Path | str, run_contract: RunContract, candidate: Path | str) -> None:
    run_contract.scope.assert_allows(Path(repo_root), Path(candidate))


def enforce_budget(
    run_contract: RunContract,
    *,
    iterations_used: int,
    cost_spent: float,
    started_at: datetime,
    now: datetime | None = None,
) -> None:
    current_time = now or datetime.now(timezone.utc)
    constraints = run_contract.constraints
    if iterations_used > constraints.max_iterations:
        raise BudgetExceededError(
            f"Iteration budget exceeded: {iterations_used} > {constraints.max_iterations}."
        )
    if cost_spent > constraints.max_cost_dollars:
        raise BudgetExceededError(
            f"Cost budget exceeded: {cost_spent} > {constraints.max_cost_dollars}."
        )
    deadline = started_at + timedelta(seconds=constraints.hard_timeout_seconds)
    if current_time > deadline:
        raise BudgetExceededError(
            "Hard timeout exceeded: "
            f"{current_time.isoformat()} > {deadline.isoformat()}."
        )
