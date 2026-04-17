import textwrap
import unittest

from supervisor.closeout_evidence import CloseoutBundle, validate_comment, validate_issue


PASSING_TODO = textwrap.dedent(
    """
    ## Completed
    - [x] 2026-04-16 | GIL-46: automate closeout evidence backfill — landed as `abc1234`; full record in Work Record Log 2026-04-16

    ## Work Record Log
    ### 2026-04-16 | GIL-46 | by: Codex
    Problem:
    Example
    Reasoning:
    Example
    Diagnosis inputs:
    Example
    Implementation inputs:
    Example
    Fix:
    Example
    Self-audit:
    Example
    triggered by:
    Example
    led to:
    `abc1234`; `GIL-49`
    linear:
    GIL-46
    """
)


class ValidateIssueTests(unittest.TestCase):
    def test_validate_issue_passes_when_records_match(self) -> None:
        result = validate_issue(PASSING_TODO, "GIL-46")
        self.assertTrue(result.ok)
        self.assertEqual([], result.errors)

    def test_validate_issue_fails_on_placeholder_completed_sha(self) -> None:
        todo = PASSING_TODO.replace("`abc1234`", "`<SHA>`", 1)
        result = validate_issue(todo, "GIL-46")
        self.assertFalse(result.ok)
        self.assertTrue(any("placeholder" in error.message for error in result.errors))

    def test_validate_issue_fails_when_completed_hash_missing_from_led_to(self) -> None:
        todo = PASSING_TODO.replace("`abc1234`; `GIL-49`", "`GIL-49`")
        result = validate_issue(todo, "GIL-46")
        self.assertFalse(result.ok)
        self.assertTrue(any("missing from `led to:`" in error.message for error in result.errors))

    def test_validate_issue_warns_for_non_matching_linear_value(self) -> None:
        todo = PASSING_TODO.replace("GIL-46\n", "GIL-99\n", 1)
        result = validate_issue(todo, "GIL-46")
        self.assertTrue(result.ok)
        self.assertTrue(any("does not reference the issue directly" in warning.message for warning in result.warnings))

    def test_validate_issue_accepts_full_sha_in_led_to(self) -> None:
        todo = PASSING_TODO.replace("`abc1234`; `GIL-49`", "`abc1234def5678`; `GIL-49`")
        result = validate_issue(todo, "GIL-46")
        self.assertTrue(result.ok)

    def test_validate_issue_does_not_treat_todo_md_as_placeholder(self) -> None:
        todo = PASSING_TODO.replace("`abc1234`; `GIL-49`", "`abc1234`; `GIL-49`; touched `todo.md`")
        result = validate_issue(todo, "GIL-46")
        self.assertTrue(result.ok)

    def test_validate_issue_matches_the_right_work_record_when_issue_has_multiple_entries(self) -> None:
        todo = textwrap.dedent(
            """
            ## Completed
            - [x] 2026-04-16 | GIL-37: first landing — landed as `aaa1111`; full record in Work Record Log 2026-04-16
            - [x] 2026-04-16 | GIL-37: second landing — landed as `bbb2222`; full record in Work Record Log 2026-04-16

            ## Work Record Log
            ### 2026-04-16 | GIL-37 first pass | by: Codex
            Problem:
            Example
            Reasoning:
            Example
            Diagnosis inputs:
            Example
            Implementation inputs:
            Example
            Fix:
            Example
            Self-audit:
            Example
            triggered by:
            Example
            led to:
            `aaa1111abc`
            linear:
            GIL-37

            ### 2026-04-16 | GIL-37 second pass | by: Codex
            Problem:
            Example
            Reasoning:
            Example
            Diagnosis inputs:
            Example
            Implementation inputs:
            Example
            Fix:
            Example
            Self-audit:
            Example
            triggered by:
            Example
            led to:
            `bbb2222def`
            linear:
            GIL-37
            """
        )
        result = validate_issue(todo, "GIL-37")
        self.assertTrue(result.ok)


class ValidateCommentTests(unittest.TestCase):
    def test_validate_comment_passes_for_rendered_bundle(self) -> None:
        bundle = CloseoutBundle(
            issue_id="GIL-46",
            title="automate closeout evidence backfill",
            work_record_date="2026-04-16",
            landed_refs=["abc1234"],
            led_to_refs=["abc1234", "GIL-49"],
        )
        comment = bundle.render_comment(
            summary_lines=["Adds a closeout-evidence validator."],
            verification_lines=["python3 -m unittest tests.test_closeout_evidence"],
            follow_up_lines=["None."],
        )

        result = validate_comment(comment, "GIL-46", landed_refs=["abc1234"], follow_up_refs=["GIL-49"])
        self.assertTrue(result.ok)

    def test_validate_comment_fails_when_follow_up_ref_is_listed_as_landing(self) -> None:
        comment = textwrap.dedent(
            """
            Implemented and pushed on `main`.

            Landings:
            - `abc1234`
            - `GIL-49`
            """
        ).strip()

        result = validate_comment(comment, "GIL-46", landed_refs=["abc1234"], follow_up_refs=["GIL-49"])
        self.assertFalse(result.ok)
        self.assertTrue(any("misattributes follow-up ref" in error.message for error in result.errors))


class RenderBundleTests(unittest.TestCase):
    def test_bundle_renders_completed_and_led_to(self) -> None:
        bundle = CloseoutBundle(
            issue_id="GIL-46",
            title="automate closeout evidence backfill",
            work_record_date="2026-04-16",
            landed_refs=["abc1234"],
            led_to_refs=["abc1234", "GIL-49"],
        )

        self.assertEqual(
            "- [x] 2026-04-16 | GIL-46: automate closeout evidence backfill — landed as `abc1234`; full record in Work Record Log 2026-04-16",
            bundle.render_completed_entry(),
        )
        self.assertEqual("led to:\n`abc1234`; `GIL-49`", bundle.render_led_to_block())


if __name__ == "__main__":
    unittest.main()
