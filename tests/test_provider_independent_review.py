from __future__ import annotations

import os
from pathlib import Path
import unittest
from unittest.mock import patch

from supervisor import main as runtime
from supervisor.strategy_simple import SimpleStrategy


ROOT = Path(__file__).resolve().parents[1]


class ProviderIndependentReviewTests(unittest.TestCase):
    def test_default_cli_needs_no_claude_auth_or_adapter(self) -> None:
        with (
            patch.dict(os.environ, {}, clear=True),
            patch('sys.argv', ['aca', '--repo-path', '/unused']),
            patch.object(runtime, 'ClaudeStrategy', side_effect=AssertionError('Claude unavailable')),
            patch.object(runtime, '_build_strategy', wraps=runtime._build_strategy) as build,
            patch('urllib.request.urlopen', side_effect=AssertionError('provider access forbidden')),
        ):
            with self.assertRaisesRegex(SystemExit, '--run-contract'):
                runtime.main()
            build.assert_called_once_with('simple')
            strategy = runtime._build_strategy('simple')
            self.assertIsInstance(strategy, SimpleStrategy)
            self.assertEqual(0, strategy.consume_pending_cost())

    def test_current_guidance_keeps_review_independent_and_authority_separate(self) -> None:
        entry = (ROOT / 'AGENTS.project.md').read_text()
        architecture = (ROOT / 'canonical-architecture.md').read_text()
        self.assertIn('did not author the patch', entry)
        self.assertIn('preserving Trevor\'s selected model and reasoning effort', entry)
        self.assertIn('passing tests alone do not satisfy this gate', entry)
        self.assertIn('Same-model fresh-context review is acceptable', architecture)
        self.assertIn('**Supervisor owns:**', entry)
        self.assertIn('**Trevor owns:** `Done`', entry)
        self.assertIn('Runtime `COMPLETE`/`READY` is evidence for a retained candidate', entry)
        for path in ('AGENTS.project.md', 'LINEAR.md', 'QUEUE-RUNS.md', 'PROMPTS.md',
                     'CONTINUITY.md', 'RULES.md', 'IMPLEMENTATION-PLAN.md'):
            with self.subTest(path=path):
                text = (ROOT / path).read_text()
                for revoked in ('Claude Code is the primary auditor', 'Cowork moves',
                                'Claude Code must spot-check', 'Claude API returns valid responses',
                                'Claude access is configured and functional',
                                'Execution lane: Claude Code'):
                    self.assertNotIn(revoked, text)


if __name__ == '__main__':
    unittest.main()
