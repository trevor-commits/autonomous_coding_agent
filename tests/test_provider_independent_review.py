from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import tempfile
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

    def assert_current_hidden_and_cadence_guidance(self, root: Path) -> None:
        active = root / '.codex-agent'
        self.assertEqual({'README.md'}, {str(p.relative_to(active)) for p in active.rglob('*') if p.is_file()})
        pointer = (active / 'README.md').read_text()
        self.assertIn('historical-read-only', pointer)
        self.assertIn('design-history/codex-agent-2026-04-17/', pointer)
        self.assertIn('AGENTS.project.md', pointer)
        self.assertIn('preserving Trevor\'s selected model and reasoning effort', pointer)
        todo = (root / 'todo.md').read_text()
        section = todo.split('## Testing Cadence Matrix\n', 1)[1].split('\n## ', 1)[0]
        rows = '\n'.join(line for line in section.splitlines() if line.startswith('|'))
        self.assertNotIn('Claude', rows)
        self.assertNotIn('Paired audit: Pro', rows)
        self.assertIn('Separate non-author native Codex review covers strategic alignment', rows)
        self.assertIn('Both review angles clean with evidence', rows)
        self.assertIn('human/governor gates remain', rows)

    def test_current_hidden_and_cadence_surfaces(self) -> None:
        self.assert_current_hidden_and_cadence_guidance(ROOT)

    def test_active_snapshot_and_provider_cadence_regressions_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix='aca-review-contract-') as temp:
            root = Path(temp)
            active = root / '.codex-agent'
            active.mkdir()
            (active / 'README.md').write_bytes((ROOT / '.codex-agent/README.md').read_bytes())
            (root / 'todo.md').write_bytes((ROOT / 'todo.md').read_bytes())
            self.assert_current_hidden_and_cadence_guidance(root)
            (active / 'state.json').write_text('{"phase":"execution","selected_stack":{"audit_path":"Claude Code plus Cowork"}}')
            with self.assertRaises(AssertionError):
                self.assert_current_hidden_and_cadence_guidance(root)
            (active / 'state.json').unlink()
            todo = (root / 'todo.md').read_text()
            (root / 'todo.md').write_text(todo.replace('Separate non-author native Codex review covers strategic alignment',
                                                      'Paired audit: Pro + Claude Code'))
            with self.assertRaises(AssertionError):
                self.assert_current_hidden_and_cadence_guidance(root)

    def test_historical_packet_payloads_and_approval_are_preserved(self) -> None:
        archive = ROOT / 'design-history/codex-agent-2026-04-17'
        manifest = json.loads((archive / 'manifest.json').read_text())
        self.assertEqual('973b7d1c573d565ef201764b4d670bf8958cec7e', manifest['source_commit'])
        self.assertEqual('.codex-agent/', manifest['original_prefix'])
        self.assertEqual(23, len(manifest['files']))
        payloads = {str(p.relative_to(archive)) for p in archive.rglob('*') if p.is_file()} - {'README.md', 'manifest.json'}
        self.assertEqual(set(manifest['files']), payloads)
        for name, expected in manifest['files'].items():
            with self.subTest(payload=name):
                self.assertEqual(expected, hashlib.sha256((archive / name).read_bytes()).hexdigest())
        approval = json.loads((archive / 'approval-snapshot.json').read_text())
        self.assertTrue(approval['locked'])
        self.assertEqual('Claude Code plus Cowork plus Trevor verify', approval['selected_stack']['audit_path'])

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
