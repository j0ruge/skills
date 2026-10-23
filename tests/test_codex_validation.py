import importlib.util
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load_validator():
    spec = importlib.util.spec_from_file_location('versions', ROOT / 'scripts/validate-versions.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ValidationTests(unittest.TestCase):
    def test_codex_does_not_accept_claude_frontmatter_by_intersection(self):
        validator = load_validator()
        self.assertIn('codex', validator.TOP_FIELDS_BY_PLATFORM)
        self.assertNotIn('argument-hint', validator.TOP_FIELDS_BY_PLATFORM['codex'])
        self.assertNotIn('disable-model-invocation', validator.TOP_FIELDS_BY_PLATFORM['codex'])

    def test_codex_is_valid_platform(self):
        self.assertIn('codex', load_validator().VALID_PLATFORMS)

    def test_missing_yaml_fails_gate(self):
        result = subprocess.run([__import__('sys').executable, '-S',
                                 str(ROOT / 'scripts/validate-versions.py')],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn('PyYAML', result.stdout + result.stderr)

    def test_explicit_skill_needs_codex_invocation_policy(self):
        import json
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plugin = root / 'plugins/demo'
            (plugin / '.claude-plugin').mkdir(parents=True)
            (plugin / '.claude-plugin/plugin.json').write_text(json.dumps(
                dict(platforms=['claude-code', 'codex'])))
            skill = plugin / 'skills/demo'
            skill.mkdir(parents=True)
            (skill / 'SKILL.md').write_text('---\nname: demo\ndescription: "Example"\n'
                                          'disable-model-invocation: true\n---\nRead.\n')
            validator = load_validator()
            errors, _ = validator._check_skill_spec(root)
            self.assertTrue(any('allow_implicit_invocation' in e for e in errors), errors)
            (skill / 'agents').mkdir()
            (skill / 'agents/openai.yaml').write_text('policy:\n  allow_implicit_invocation: false\n')
            errors, _ = validator._check_skill_spec(root)
            self.assertFalse(errors, errors)


class HookTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.git('init', '-q')
        self.git('config', 'user.email', 'test@example.test')
        self.git('config', 'user.name', 'Teste')
        (self.root / 'scripts').mkdir()
        (self.root / 'scripts/validate-versions.py').write_text(
            'from pathlib import Path\nimport sys\n'
            'print("validator-ran")\n'
            'sys.exit(1 if (Path(__file__).resolve().parents[1]/"invalid").exists() else 0)\n')
        (self.root / 'README.md').write_text('baseline')
        self.git('add', '.')
        self.git('commit', '-qm', 'Base para teste')

    def git(self, *args):
        return subprocess.run(['git', *args], cwd=self.root, capture_output=True,
                              text=True, check=True)

    def hook(self):
        return subprocess.run(['bash', str(ROOT / 'scripts/pre-commit')], cwd=self.root,
                              capture_output=True, text=True)

    def test_triggers_for_every_distribution_input(self):
        for name in ['scripts/codex-marketplace.py', 'scripts/validate-versions.py',
                     'install.py', 'plugins/demo/codex-adapter.json',
                     'plugins/demo/skills/demo/agents/openai.yaml',
                     'plugins/demo/commands/demo.md', 'plugins/demo/templates/demo.md',
                     'plugins/demo/skills/demo/references/example.md', 'scripts/pre-commit']:
            with self.subTest(name=name):
                path = self.root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                if name != 'scripts/validate-versions.py':
                    path.write_text('example')
                else:
                    path.write_text(path.read_text() + '\n')
                self.git('add', name)
                result = self.hook()
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn('validator-ran', result.stdout)
                self.git('reset', '-q')

    def test_fixed_worktree_cannot_hide_invalid_staged_snapshot(self):
        (self.root / 'invalid').touch()
        (self.root / 'plugins/demo/skills/demo').mkdir(parents=True)
        (self.root / 'plugins/demo/skills/demo/SKILL.md').write_text('invalid')
        self.git('add', '.')
        (self.root / 'invalid').unlink()
        result = self.hook()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('validator-ran', result.stdout)

    def test_quoted_plugin_path_still_triggers_gate(self):
        path = self.root / 'plugins/demo/ação.md'
        path.parent.mkdir(parents=True)
        path.touch()
        self.git('config', 'core.quotePath', 'true')
        self.git('add', '.')
        result = self.hook()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('validator-ran', result.stdout)

    def test_rename_out_of_distribution_paths_still_runs_gate(self):
        source = self.root / 'plugins/demo/templates/example.md'
        source.parent.mkdir(parents=True)
        source.write_text('# Template de distribuição\n')
        # O snapshot inválido obriga o gate a bloquear o commit desse rename.
        (self.root / 'scripts/validate-versions.py').write_text(
            'from pathlib import Path\nimport sys\n'
            'print("validator-ran")\n'
            'sys.exit(0 if (Path(__file__).resolve().parents[1]/'
            '"plugins/demo/templates/example.md").exists() else 1)\n')
        self.git('add', '.')
        self.git('commit', '-qm', 'Base com recurso distribuído e seu validador')
        self.git('config', 'diff.renames', 'true')
        target = self.root / 'docs/example.md'
        target.parent.mkdir()
        self.git('mv', str(source), str(target))
        self.assertEqual(self.git('diff', '--cached', '--name-only').stdout.strip(),
                         'docs/example.md')
        result = self.hook()
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('validator-ran', result.stdout)

    def test_detector_failure_blocks_commit(self):
        import os
        from unittest import mock
        tools = self.root / 'test-bin'
        tools.mkdir()
        detector = tools / 'rg'
        detector.write_text('#!/bin/sh\nexit 2\n')
        detector.chmod(0o755)
        path = self.root / 'plugins/demo/SKILL.md'
        path.parent.mkdir(parents=True)
        path.touch()
        (self.root / 'invalid').touch()
        self.git('add', '.')
        with mock.patch.dict(os.environ, {'PATH': str(tools) + os.pathsep + os.environ['PATH']}):
            result = self.hook()
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_git_diff_failure_blocks_commit(self):
        import os
        from unittest import mock
        tools = self.root / 'test-bin'
        tools.mkdir()
        git = tools / 'git'
        git.write_text('#!/bin/sh\nexit 2\n')
        git.chmod(0o755)
        with mock.patch.dict(os.environ, {'PATH': str(tools) + os.pathsep + os.environ['PATH']}):
            result = self.hook()
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_large_staged_set_does_not_skip_gate_on_sigpipe(self):
        plugin = self.root / 'plugins/demo'
        plugin.mkdir(parents=True)
        for index in range(2500):
            (plugin / f'resource-{index:05d}-long-path-for-pipe-capacity.md').touch()
        self.git('add', '.')
        result = self.hook()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('validator-ran', result.stdout)

    def test_git_actually_invokes_hook_and_blocks_invalid_commit(self):
        (self.root / 'plugins').mkdir()
        (self.root / 'plugins/change.md').touch()
        (self.root / 'invalid').touch()
        self.git('add', '.')
        result = subprocess.run(['git', '-c', f'core.hooksPath={ROOT / "scripts"}',
                                 'commit', '-qm', 'Deve bloquear snapshot inválido'],
                                cwd=self.root, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0, result.stderr)
        self.assertIn('validator-ran', result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
