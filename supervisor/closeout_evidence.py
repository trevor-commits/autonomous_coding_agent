from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


PLACEHOLDER_PATTERNS = (
    re.compile(r"<\s*sha\s*>", re.IGNORECASE),
    re.compile(r"(?<![\w./-])tbd(?![\w./-])", re.IGNORECASE),
    re.compile(r"(?<![\w./-])todo(?![\w./-])", re.IGNORECASE),
    re.compile(r"(?<![\w./-])placeholder(?![\w./-])", re.IGNORECASE),
)
HASH_RE = re.compile(r"\b[0-9a-f]{7,40}\b")
LANDINGS_RE = re.compile(r"^Landings:\n(?P<body>(?:- .+\n?)+)", re.MULTILINE)
COMPLETED_RE = re.compile(
    r"^- \[x\] (?P<date>\d{4}-\d{2}-\d{2}) \| (?P<issue>GIL-\d+): .* — landed as "
    r"(?P<landed>.+?); full record in Work Record Log (?P<record_date>\d{4}-\d{2}-\d{2})$",
    re.MULTILINE,
)
WORK_RECORD_RE = re.compile(
    r"^### (?P<date>\d{4}-\d{2}-\d{2}) \| (?P<label>[^\n]+?) \| by: (?P<actor>[^\n]+)$",
    re.MULTILINE,
)


@dataclass
class ValidationIssue:
    level: str
    message: str


@dataclass
class ValidationResult:
    issue_id: str
    errors: list[ValidationIssue]
    warnings: list[ValidationIssue]

    @property
    def ok(self) -> bool:
        return not self.errors


@dataclass
class CloseoutBundle:
    issue_id: str
    title: str
    work_record_date: str
    landed_refs: list[str]
    led_to_refs: list[str]

    def render_completed_entry(self) -> str:
        landed = " + ".join(f"`{ref}`" for ref in self.landed_refs)
        return (
            f"- [x] {self.work_record_date} | {self.issue_id}: {self.title} "
            f"— landed as {landed}; full record in Work Record Log {self.work_record_date}"
        )

    def render_led_to_block(self) -> str:
        refs = "; ".join(f"`{ref}`" for ref in self.led_to_refs)
        return f"led to:\n{refs}"

    def render_comment(
        self,
        summary_lines: Sequence[str],
        verification_lines: Sequence[str],
        follow_up_lines: Sequence[str],
    ) -> str:
        lines = [
            "Implemented and pushed on `main`.",
            "",
            "Landings:",
        ]
        lines.extend(f"- `{ref}`" for ref in self.landed_refs)
        if summary_lines:
            lines.extend(["", "What changed:"])
            lines.extend(f"- {line}" for line in summary_lines)
        if verification_lines:
            lines.extend(["", "Verification:"])
            lines.extend(f"- {line}" for line in verification_lines)
        if follow_up_lines:
            lines.extend(["", "Follow-ups:"])
            lines.extend(f"- {line}" for line in follow_up_lines)
        return "\n".join(lines)


def _contains_placeholder(value: str) -> bool:
    return any(pattern.search(value) for pattern in PLACEHOLDER_PATTERNS)


def _extract_hashes(value: str) -> set[str]:
    return set(HASH_RE.findall(value))


def _refs_cover(expected_refs: set[str], actual_refs: set[str]) -> list[str]:
    missing: list[str] = []
    for expected in sorted(expected_refs):
        if not any(
            expected.startswith(actual) or actual.startswith(expected)
            for actual in actual_refs
        ):
            missing.append(expected)
    return missing


def _find_completed_entry(todo_text: str, issue_id: str) -> re.Match[str] | None:
    for match in COMPLETED_RE.finditer(todo_text):
        if match.group("issue") == issue_id:
            return match
    return None


def _find_completed_entries(todo_text: str, issue_id: str) -> list[re.Match[str]]:
    return [
        match for match in COMPLETED_RE.finditer(todo_text) if match.group("issue") == issue_id
    ]


def _find_work_records(todo_text: str, issue_id: str) -> list[tuple[str, str]]:
    matches = list(WORK_RECORD_RE.finditer(todo_text))
    records: list[tuple[str, str]] = []
    for idx, match in enumerate(matches):
        label = match.group("label")
        if issue_id not in label:
            continue
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(todo_text)
        records.append((match.group("date"), todo_text[start:end]))
    return records


def _work_record_matches_completed(
    completed: re.Match[str],
    work_record_date: str,
    block: str,
) -> tuple[bool, list[ValidationIssue]]:
    errors: list[ValidationIssue] = []
    issue_id = completed.group("issue")

    led_to_match = re.search(r"^led to:\n(?P<value>.+)$", block, re.MULTILINE)
    if not led_to_match:
        errors.append(
            ValidationIssue("error", f"Work Record for {issue_id} is missing `led to:`.")
        )
    else:
        led_to_value = led_to_match.group("value").strip()
        if _contains_placeholder(led_to_value):
            errors.append(
                ValidationIssue(
                    "error",
                    f"Work Record `led to:` for {issue_id} still contains a placeholder: {led_to_value}",
                )
            )
        completed_hashes = _extract_hashes(completed.group("landed"))
        led_to_hashes = _extract_hashes(led_to_value)
        missing_hashes = _refs_cover(completed_hashes, led_to_hashes)
        if missing_hashes:
            errors.append(
                ValidationIssue(
                    "error",
                    f"Completed hashes for {issue_id} are missing from `led to:`: {', '.join(missing_hashes)}",
                )
            )

    linear_match = re.search(r"^linear:\n(?P<value>.+)$", block, re.MULTILINE)
    if not linear_match:
        errors.append(
            ValidationIssue("error", f"Work Record for {issue_id} is missing `linear:`.")
        )
    else:
        linear_value = linear_match.group("value").strip()
        if issue_id not in linear_value and not linear_value.startswith(
            ("no-action:", "self-contained:")
        ):
            errors.append(
                ValidationIssue(
                    "warning",
                    f"`linear:` for {issue_id} does not reference the issue directly: {linear_value}",
                )
            )

    if completed.group("record_date") != work_record_date:
        errors.append(
            ValidationIssue(
                "error",
                f"Completed entry for {issue_id} points at Work Record date "
                f"{completed.group('record_date')} but the Work Record is {work_record_date}.",
            )
        )

    return not any(issue.level == "error" for issue in errors), errors


def validate_issue(todo_text: str, issue_id: str) -> ValidationResult:
    result = ValidationResult(issue_id=issue_id, errors=[], warnings=[])

    completed_entries = _find_completed_entries(todo_text, issue_id)
    if not completed_entries:
        result.errors.append(
            ValidationIssue("error", f"Missing Completed entry for {issue_id}.")
        )
    work_records = _find_work_records(todo_text, issue_id)
    if not work_records:
        result.errors.append(
            ValidationIssue("error", f"Missing Work Record entry for {issue_id}.")
        )
        return result

    for completed in completed_entries:
        landed = completed.group("landed")
        if _contains_placeholder(landed):
            result.errors.append(
                ValidationIssue(
                    "error",
                    f"Completed entry for {issue_id} still contains a placeholder: {landed}",
                )
            )

        matching_warnings: list[ValidationIssue] = []
        matched = False
        candidate_errors: list[ValidationIssue] = []
        for work_record_date, block in work_records:
            record_matches, record_findings = _work_record_matches_completed(
                completed,
                work_record_date,
                block,
            )
            candidate_errors = record_findings
            if record_matches:
                matched = True
                matching_warnings.extend(
                    finding for finding in record_findings if finding.level == "warning"
                )
                break

        if not matched:
            result.errors.extend(candidate_errors)
        else:
            result.warnings.extend(matching_warnings)

    return result


def validate_comment(
    comment_text: str,
    issue_id: str,
    landed_refs: Sequence[str],
    follow_up_refs: Sequence[str] = (),
) -> ValidationResult:
    result = ValidationResult(issue_id=issue_id, errors=[], warnings=[])

    landings_match = LANDINGS_RE.search(comment_text)
    if not landings_match:
        result.errors.append(
            ValidationIssue(
                "error",
                f"Linear completion comment for {issue_id} is missing a `Landings:` block.",
            )
        )
        return result

    landings_block = landings_match.group("body")
    missing_landed = _refs_cover(set(landed_refs), _extract_hashes(landings_block))
    if missing_landed:
        result.errors.append(
            ValidationIssue(
                "error",
                f"Linear completion comment for {issue_id} is missing landed refs in `Landings:`: {', '.join(missing_landed)}",
            )
        )

    for ref in follow_up_refs:
        if f"`{ref}`" in landings_block:
            result.errors.append(
                ValidationIssue(
                    "error",
                    f"Linear completion comment for {issue_id} misattributes follow-up ref `{ref}` as a landing.",
                )
            )

    return result


def _build_bundle(args: argparse.Namespace) -> CloseoutBundle:
    landed_refs = list(args.landed)
    led_to_refs = list(args.landed)
    led_to_refs.extend(args.follow_up_ref or [])
    return CloseoutBundle(
        issue_id=args.issue,
        title=args.title,
        work_record_date=args.date,
        landed_refs=landed_refs,
        led_to_refs=led_to_refs,
    )


def _cmd_validate(args: argparse.Namespace) -> int:
    todo_text = Path(args.todo).read_text()
    result = validate_issue(todo_text, args.issue)

    if result.ok:
        print(f"PASS: {args.issue} closeout evidence is internally consistent.")
    for warning in result.warnings:
        print(f"WARNING: {warning.message}")
    for error in result.errors:
        print(f"ERROR: {error.message}")
    return 0 if result.ok else 1


def _cmd_validate_comment(args: argparse.Namespace) -> int:
    comment_text = Path(args.comment_file).read_text()
    result = validate_comment(
        comment_text=comment_text,
        issue_id=args.issue,
        landed_refs=args.landed,
        follow_up_refs=args.follow_up_ref or [],
    )

    if result.ok:
        print(f"PASS: {args.issue} completion comment is internally consistent.")
    for warning in result.warnings:
        print(f"WARNING: {warning.message}")
    for error in result.errors:
        print(f"ERROR: {error.message}")
    return 0 if result.ok else 1


def _cmd_render_completed(args: argparse.Namespace) -> int:
    bundle = _build_bundle(args)
    print(bundle.render_completed_entry())
    return 0


def _cmd_render_led_to(args: argparse.Namespace) -> int:
    bundle = _build_bundle(args)
    print(bundle.render_led_to_block())
    return 0


def _cmd_render_comment(args: argparse.Namespace) -> int:
    bundle = _build_bundle(args)
    print(
        bundle.render_comment(
            summary_lines=args.summary or [],
            verification_lines=args.verification or [],
            follow_up_lines=args.follow_up or [],
        )
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate and render closeout-evidence artifacts for queue issues."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate", help="Validate issue closeout evidence in todo.md.")
    validate.add_argument("--todo", default="todo.md", help="Path to todo.md.")
    validate.add_argument("--issue", required=True, help="Issue id, e.g. GIL-46.")
    validate.set_defaults(func=_cmd_validate)

    validate_comment = subparsers.add_parser(
        "validate-comment",
        help="Validate a Linear completion comment against the intended landed refs.",
    )
    validate_comment.add_argument("--issue", required=True, help="Issue id, e.g. GIL-46.")
    validate_comment.add_argument(
        "--comment-file",
        required=True,
        help="Path to the comment body text file.",
    )
    validate_comment.add_argument(
        "--landed",
        action="append",
        required=True,
        help="Landing ref expected in the comment. Repeat for multiple refs.",
    )
    validate_comment.add_argument(
        "--follow-up-ref",
        action="append",
        help="Ref that must not appear as a landing in the comment.",
    )
    validate_comment.set_defaults(func=_cmd_validate_comment)

    common_parsers: list[argparse.ArgumentParser] = []
    for name, help_text, func in [
        ("render-completed", "Render a Completed index entry.", _cmd_render_completed),
        ("render-led-to", "Render a Work Record `led to:` block.", _cmd_render_led_to),
        ("render-comment", "Render a Linear completion comment.", _cmd_render_comment),
    ]:
        sub = subparsers.add_parser(name, help=help_text)
        sub.add_argument("--issue", required=True, help="Issue id, e.g. GIL-46.")
        sub.add_argument("--title", required=True, help="Completed-entry title.")
        sub.add_argument("--date", required=True, help="Work Record date in YYYY-MM-DD.")
        sub.add_argument(
            "--landed",
            action="append",
            required=True,
            help="Landing ref to include. Repeat for multiple refs.",
        )
        sub.add_argument(
            "--follow-up-ref",
            action="append",
            help="Additional refs to include in `led to:` only.",
        )
        if name == "render-comment":
            sub.add_argument("--summary", action="append", help="Summary bullet. Repeat as needed.")
            sub.add_argument(
                "--verification", action="append", help="Verification bullet. Repeat as needed."
            )
            sub.add_argument(
                "--follow-up", action="append", help="Follow-up bullet. Repeat as needed."
            )
        sub.set_defaults(func=func)
        common_parsers.append(sub)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
