import contextlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]


class InstallTests(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location('installer', ROOT / 'install.py')
        self.install = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.install)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.install.REPO_ROOT = self.root
        self.catalog_path = self.root / '.agents/plugins/marketplace.json'
        self.catalog_path.parent.mkdir(parents=True)
        self.catalog([])

    def catalog(self, names):
        entries = []
        for name in names:
            plugin = self.root / 'plugins' / name
            (plugin / '.claude-plugin').mkdir(parents=True, exist_ok=True)
            (plugin / '.claude-plugin/plugin.json').write_text(json.dumps(
                dict(name=name, platforms=['claude-code', 'codex'])))
            entries.append(dict(name=name, source=dict(source='local', path='./plugins/'+name),
                                policy=dict(installation='AVAILABLE', authentication='ON_INSTALL'),
                                category='development'))
        self.catalog_path.write_text(json.dumps(dict(name='chewiesoft-marketplace', plugins=entries)))

    def flow(self):
        output = io.StringIO()
        with contextlib.ExitStack() as stack:
            for name in ['write_text', 'write_bytes', 'mkdir', 'unlink']:
                stack.enter_context(mock.patch.object(Path, name, side_effect=AssertionError('escrita proibida')))
            for name in ['run', 'Popen', 'call', 'check_call', 'check_output']:
                stack.enter_context(mock.patch.object(subprocess, name, side_effect=AssertionError('processo proibido')))
            stack.enter_context(mock.patch.object(shutil, 'copytree', side_effect=AssertionError('cópia proibida')))
            stack.enter_context(mock.patch.object(shutil, 'which', return_value=None))
            stack.enter_context(contextlib.redirect_stdout(output))
            self.install._codex_install_flow()
        return output.getvalue()

    def test_one_plugin_only_shows_commands_without_codex_binary(self):
        self.catalog(['cors'])
        output = self.flow()
        self.assertIn('codex plugin marketplace add j0ruge/skills', output)
        self.assertIn('codex plugin add cors@chewiesoft-marketplace', output)
        self.assertNotIn('codex plugin add excluded@', output)

    def test_multiple_plugins(self):
        self.catalog(['cors', 'example'])
        output = self.flow()
        self.assertEqual(output.count('codex plugin add '), 2)

    def test_empty_catalog_does_not_claim_installation(self):
        output = self.flow()
        self.assertIn('Nenhum plugin', output)
        self.assertNotIn('codex plugin add ', output)
        self.assertNotIn('Done', output)

    def test_missing_invalid_and_wrong_shape_catalog_are_errors(self):
        for data in ['{', '[]', '{}', '{"name":"other","plugins":[]}']:
            with self.subTest(data=data):
                self.catalog_path.write_text(data)
                with self.assertRaises((ValueError, OSError)):
                    self.flow()
        self.catalog_path.unlink()
        with self.assertRaises((ValueError, OSError)):
            self.flow()

    def test_nonexistent_source_and_injected_name_are_errors(self):
        for name in ['cors', 'bad;command']:
            self.catalog([name])
            if name == 'cors':
                shutil.rmtree(self.root / 'plugins/cors')
            with self.assertRaises((ValueError, OSError)):
                self.flow()

    def test_excluded_plugin_cannot_be_injected(self):
        self.catalog(['cors'])
        manifest = self.root / 'plugins/cors/.claude-plugin/plugin.json'
        manifest.write_text(json.dumps(dict(name='cors', platforms=['claude-code'])))
        with self.assertRaises(ValueError):
            self.flow()

    def test_menu_routes_all_options_by_name(self):
        for selected in ['Claude Code', 'Cursor', 'Claude Code + Cursor', 'Codex']:
            with self.subTest(selected=selected), contextlib.ExitStack() as stack:
                output = io.StringIO()
                stack.enter_context(contextlib.redirect_stdout(output))
                stack.enter_context(mock.patch.object(self.install, '_choose',
                    side_effect=lambda prompt, options, **kw: options.index(selected)))
                stack.enter_context(mock.patch.object(self.install, '_cursor_install_flow',
                                                      side_effect=lambda: print('cursor-flow')))
                stack.enter_context(mock.patch.object(self.install, '_codex_install_flow',
                                                      side_effect=lambda: print('codex-flow')))
                stack.enter_context(mock.patch.object(self.install, '_CLAUDE_CODE_INSTRUCTIONS', 'claude-flow'))
                self.install.main()
                text = output.getvalue()
                self.assertEqual('claude-flow' in text, selected in ['Claude Code', 'Claude Code + Cursor'])
                self.assertEqual('cursor-flow' in text, selected in ['Cursor', 'Claude Code + Cursor'])
                self.assertEqual('codex-flow' in text, selected == 'Codex')

    def test_cli_missing_catalog_returns_one_without_yaml_dependency(self):
        shutil.copy2(ROOT / 'install.py', self.root / 'install.py')
        self.catalog_path.unlink()
        result = subprocess.run([sys.executable, '-S', str(self.root / 'install.py')],
                                input='3\n', capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertNotIn('Done.', result.stdout)


if __name__ == '__main__':
    unittest.main()
