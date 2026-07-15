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


AUTO_DENY_GIT_SUBCOMMANDS = {
    "push",
    "pull",
    "merge",
    "rebase",
    "checkout",
    "switch",
}

SAFE_GIT_SUBCOMMANDS = {"diff", "log", "rev-parse", "status"}

AUTO_DENY_EXECUTABLES = {
    "afplay",
    "alias",
    "curl",
    "defaults",
    "diskutil",
    "env",
    "eval",
    "launchctl",
    "kill",
    "killall",
    "nc",
    "ncat",
    "open",
    "osascript",
    "pbcopy",
    "pbpaste",
    "pkill",
    "reboot",
    "say",
    "scp",
    "security",
    "shutdown",
    "socat",
    "source",
    "ssh",
    "sudo",
    "wget",
}

SAFE_CONTRACT_ENVIRONMENT = {
    "CI": {"0", "1", "false", "true"},
    "NODE_ENV": {"test"},
    "PYTHONDONTWRITEBYTECODE": {"1"},
    "PYTHONUNBUFFERED": {"1"},
}

INLINE_EVALUATOR_FLAGS = {
    "node": {"-e", "--eval", "-p", "--print"},
    "perl": {"-e"},
    "python": {"-c"},
    "python3": {"-c"},
    "ruby": {"-e"},
}

PYTHON_EFFECT_MODULES = {"ensurepip", "pip", "venv", "virtualenv"}

UNSAFE_GIT_HELPER_FLAGS = {"--ext-diff", "--textconv"}

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

AUTO_DENY_PATH_COMPONENTS = {".git", ".agent", ".autoclaw"}

_FIND_NO_ARGUMENT = {"-print", "-print0", "-prune", "-o", "-a", "-not", "!", "(", ")"}
_FIND_STRING_ARGUMENT = {"-name", "-iname", "-path", "-wholename", "-type"}
_FIND_INTEGER_ARGUMENT = {"-maxdepth", "-mindepth"}
_FIND_EFFECT_ACTIONS = {
    "-delete",
    "-exec",
    "-execdir",
    "-ok",
    "-okdir",
    "-fprint",
    "-fprintf",
    "-fls",
}
_READ_ONLY_METADATA_COMMANDS = {
    ("pwd",),
}


def classify_command(
    command: str,
    repo_contract: RepoContract | None = None,
    *,
    allowed_commands: tuple[str, ...] = (),
) -> CommandDecision:
    normalized = command.strip()
    if _contains_absolute_deny(normalized):
        return CommandDecision(
            shell_class=ShellClass.AUTO_DENY,
            reason="contains an absolute deny-list shell operation",
        )
    contract_commands = (
        repo_contract.commands.auto_allow_commands() if repo_contract else ()
    )
    if normalized in {*contract_commands, *allowed_commands}:
        return CommandDecision(
            shell_class=ShellClass.AUTO_ALLOW,
            reason="repo contract command",
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


def _contains_absolute_deny(command: str) -> bool:
    """Find effect-time denials anywhere in a shell expression.

    Repo contracts are input, not authority to weaken these denials. Scanning
    every token is intentionally conservative: a harmless command that merely
    quotes one of these operation shapes is rejected instead of risking a
    compound or nested-shell bypass.
    """

    if not command or len(command) > 100_000:
        return True
    if any(character in command for character in ("\n", "\r", "$", "`")):
        return True
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars="|&;<>()")
        lexer.whitespace_split = True
        lexer.commenters = ""
        tokens = list(lexer)
    except ValueError:
        return True
    if not tokens:
        return True

    for index, token in enumerate(tokens):
        assignment = re.fullmatch(r"([A-Za-z_][A-Za-z0-9_]*)=(.*)", token, re.DOTALL)
        if assignment:
            allowed_values = SAFE_CONTRACT_ENVIRONMENT.get(assignment.group(1))
            if allowed_values is None or assignment.group(2) not in allowed_values:
                return True
            continue
        executable = Path(token).name.lower()
        if executable in AUTO_DENY_EXECUTABLES:
            return True
        if executable in {
            "bash",
            "dash",
            "sh",
            "zsh",
        } and _shell_script_is_absolute_deny(tokens, index):
            return True
        if executable in {"awk", "gawk"} and _awk_is_absolute_deny(tokens, index):
            return True
        evaluator = re.sub(r"[0-9.]+$", "", executable)
        if evaluator in INLINE_EVALUATOR_FLAGS:
            segment = [value.lower() for value in _command_segment(tokens, index)]
            if any(flag in INLINE_EVALUATOR_FLAGS[evaluator] for flag in segment):
                return True
            if evaluator in {"python", "python3"}:
                for position, candidate in enumerate(segment[:-1]):
                    if (
                        candidate == "-m"
                        and segment[position + 1] in PYTHON_EFFECT_MODULES
                    ):
                        return True
        if executable == "git" and _git_command_is_absolute_deny(tokens, index):
            return True
        if executable == "rm":
            flags = "".join(
                candidate[1:]
                for candidate in tokens[index + 1 :]
                if candidate.startswith("-") and candidate != "--"
            ).lower()
            if "f" in flags and ("r" in flags or "R" in flags):
                return True
    return False


def _command_segment(tokens: list[str], executable_index: int) -> list[str]:
    separators = {"&&", "||", ";", "|", "&", "(", ")"}
    segment: list[str] = []
    for candidate in tokens[executable_index + 1 :]:
        if candidate in separators:
            break
        segment.append(candidate)
    return segment


def _safe_repo_script_path(value: str, suffix: str) -> bool:
    path = PurePosixPath(value.replace("\\", "/"))
    return (
        bool(path.parts)
        and not path.is_absolute()
        and "." not in path.parts
        and ".." not in path.parts
        and path.suffix == suffix
        and all(re.fullmatch(r"[A-Za-z0-9._-]+", part) for part in path.parts)
    )


def _shell_script_is_absolute_deny(tokens: list[str], executable_index: int) -> bool:
    segment = _command_segment(tokens, executable_index)
    if not segment or segment[0] in {"-c", "-lc", "-s", "--stdin"}:
        return True
    position = 0
    while position < len(segment) and segment[position] in {
        "--",
        "-e",
        "-u",
        "-eu",
        "-ue",
        "-x",
        "-ex",
        "-eux",
    }:
        position += 1
    if position >= len(segment) or not _safe_repo_script_path(segment[position], ".sh"):
        return True
    return any(
        not re.fullmatch(r"[A-Za-z0-9._/:=@+-]+", candidate)
        for candidate in segment[position + 1 :]
    )


def _awk_is_absolute_deny(tokens: list[str], executable_index: int) -> bool:
    segment = _command_segment(tokens, executable_index)
    return not (
        len(segment) >= 2
        and segment[0] == "-f"
        and _safe_repo_script_path(segment[1], ".awk")
        and all(
            re.fullmatch(r"[A-Za-z0-9._/:=@+-]+", candidate)
            for candidate in segment[2:]
        )
    )


def _git_command_is_absolute_deny(tokens: list[str], git_index: int) -> bool:
    segment = _command_segment(tokens, git_index)
    if not segment:
        return True

    lowered = [candidate.lower() for candidate in segment]
    if any(candidate in AUTO_DENY_GIT_SUBCOMMANDS for candidate in lowered):
        return True
    if any(candidate in UNSAFE_GIT_HELPER_FLAGS for candidate in lowered):
        return True
    if any(candidate == "-c" for candidate in segment) or any(
        candidate.startswith("--config-env")
        or candidate.startswith("--exec-path")
        or candidate.startswith("--git-dir")
        or candidate.startswith("--work-tree")
        or candidate.startswith("--namespace")
        for candidate in lowered
    ):
        return True

    position = 0
    while position < len(segment):
        candidate = segment[position]
        if candidate == "-C":
            if position + 1 >= len(segment) or segment[position + 1] != ".":
                return True
            position += 2
            continue
        if candidate in {"--no-pager", "--no-optional-locks"}:
            position += 1
            continue
        if candidate.startswith("-"):
            return True
        return candidate.lower() not in SAFE_GIT_SUBCOMMANDS
    return True


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
    parts = PurePosixPath(normalized.replace("\\", "/")).parts
    basename = parts[-1] if parts else ""
    if basename.startswith(".env") or any(
        part in AUTO_DENY_PATH_COMPONENTS for part in parts
    ):
        return CommandDecision(
            shell_class=ShellClass.AUTO_DENY,
            reason="secret and supervisor/control metadata writes are denied",
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


def enforce_scope(
    repo_root: Path | str, run_contract: RunContract, candidate: Path | str
) -> None:
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
