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
    def test_codex_is_valid_platform(self):
        self.assertIn('codex', load_validator().VALID_PLATFORMS)

    def test_missing_yaml_fails_gate(self):
        result = subprocess.run([__import__('sys').executable, '-S',
                                 str(ROOT / 'scripts/validate-versions.py')],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn('PyYAML', result.stdout + result.stderr)


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


if __name__ == '__main__':
    unittest.main()
