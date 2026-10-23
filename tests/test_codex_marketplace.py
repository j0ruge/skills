import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/codex-marketplace.py'


class MarketplaceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.catalog = self.root / '.agents/plugins/marketplace.json'
        self.entries = []
        for name, platforms in [('ready', ['claude-code', 'codex']),
                                ('excluded', ['claude-code'])]:
            plugin = self.root / 'plugins' / name
            (plugin / '.claude-plugin').mkdir(parents=True)
            (plugin / 'skills' / name).mkdir(parents=True)
            (plugin / 'skills' / name / 'SKILL.md').write_text(
                f'---\nname: {name}\ndescription: "Example skill"\n---\nRead input.\n')
            data = dict(name=name, version='1.0.0', description='Example skill',
                        author=dict(name='Chewiesoft'), platforms=platforms, skills='./skills')
            self.write_json(plugin / '.claude-plugin/plugin.json', data)
            self.entries.append(dict(name=name, source='./plugins/' + name,
                                     version='1.0.0', description='Example skill',
                                     platforms=platforms, category='development'))
        self.source = self.root / '.claude-plugin/marketplace.json'
        self.save_source()

    def write_json(self, path, data):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data), encoding='utf-8')

    def save_source(self):
        self.write_json(self.source, dict(name='chewiesoft-marketplace',
                                        owner=dict(name='Chewiesoft'), plugins=self.entries))

    def run_script(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), '--root', str(self.root), *args],
                              capture_output=True, text=True)

    def assert_rejected(self, reason):
        before = self.catalog.read_bytes() if self.catalog.exists() else None
        result = self.run_script('--write')
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn(reason, result.stderr)
        self.assertEqual(self.catalog.read_bytes() if self.catalog.exists() else None, before)

    def test_exact_subset_and_check_does_not_write(self):
        result = self.run_script('--write')
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(self.catalog.read_text())
        self.assertEqual(data['name'], 'chewiesoft-marketplace')
        self.assertEqual([p['name'] for p in data['plugins']], ['ready'])
        self.assertEqual(data['plugins'][0]['source'],
                         {'source': 'local', 'path': './plugins/ready'})
        self.assertEqual(data['plugins'][0]['policy'],
                         {'installation': 'AVAILABLE', 'authentication': 'ON_INSTALL'})
        before = self.catalog.stat().st_mtime_ns, self.catalog.read_bytes()
        self.assertEqual(self.run_script().returncode, 0)
        self.assertEqual((self.catalog.stat().st_mtime_ns, self.catalog.read_bytes()), before)
        self.assertEqual(self.run_script('--write').returncode, 0)
        self.assertEqual(self.catalog.read_bytes(), before[1])

    def test_missing_derived_fails_without_write(self):
        result = self.run_script()
        self.assertEqual(result.returncode, 1)
        self.assertFalse(self.catalog.exists())

    def test_invalid_source_json(self):
        self.source.write_text('{')
        self.assert_rejected('JSON')

    def test_invalid_derived_json(self):
        self.write_json(self.catalog, {})
        self.catalog.write_text('{')
        self.assertEqual(self.run_script().returncode, 1)
        self.assertEqual(self.catalog.read_text(), '{')

    def test_excluded_plugin_injected(self):
        self.assertEqual(self.run_script('--write').returncode, 0)
        data = json.loads(self.catalog.read_text())
        data['plugins'].append(dict(name='excluded'))
        self.write_json(self.catalog, data)
        self.assertEqual(self.run_script().returncode, 1)

    def test_duplicate_name(self):
        self.entries.append(self.entries[0].copy())
        self.save_source()
        self.assert_rejected('duplicado')

    def test_source_outside_plugins(self):
        self.entries[0]['source'] = './outside'
        self.save_source()
        self.assert_rejected('plugins/')

    def test_symlink_escape(self):
        with tempfile.TemporaryDirectory() as outside:
            (self.root / 'plugins/ready/escape').symlink_to(outside, target_is_directory=True)
            self.assert_rejected('escape')

    def test_missing_manifest(self):
        (self.root / 'plugins/ready/.claude-plugin/plugin.json').unlink()
        self.assert_rejected('plugin.json')

    def test_advertised_skill_must_exist(self):
        (self.root / 'plugins/ready/skills/ready/SKILL.md').unlink()
        self.assert_rejected('skills')

    def test_default_skills_directory_is_discovered_without_manifest_field(self):
        manifest_path = self.root / 'plugins/ready/.claude-plugin/plugin.json'
        manifest = json.loads(manifest_path.read_text())
        manifest.pop('skills')
        self.write_json(manifest_path, manifest)
        result = self.run_script('--write')
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_plugins_directory_symlink_cannot_escape_root(self):
        with tempfile.TemporaryDirectory() as outside:
            import shutil
            shutil.move(str(self.root / 'plugins'), str(Path(outside) / 'plugins'))
            (self.root / 'plugins').symlink_to(Path(outside) / 'plugins', target_is_directory=True)
            self.assert_rejected('escape')

    def test_policy_drift(self):
        self.assertEqual(self.run_script('--write').returncode, 0)
        data = json.loads(self.catalog.read_text())
        data['plugins'][0]['policy']['installation'] = 'INSTALLED_BY_DEFAULT'
        self.write_json(self.catalog, data)
        self.assertEqual(self.run_script('--check').returncode, 1)

    def test_platform_mismatch(self):
        self.entries[0]['platforms'] = ['claude-code']
        self.save_source()
        self.assert_rejected('platforms')

    def test_platform_order_does_not_change_support_set(self):
        self.entries[0]['platforms'] = list(reversed(self.entries[0]['platforms']))
        self.save_source()
        result = self.run_script('--write')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual([p['name'] for p in json.loads(self.catalog.read_text())['plugins']],
                         ['ready'])

    def test_excluded_plugin_platform_order_is_irrelevant(self):
        manifest_path = self.root / 'plugins/excluded/.claude-plugin/plugin.json'
        manifest = json.loads(manifest_path.read_text())
        manifest['platforms'] = ['claude-code', 'cursor']
        self.write_json(manifest_path, manifest)
        self.entries[1]['platforms'] = ['cursor', 'claude-code']
        self.save_source()
        result = self.run_script('--write')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual([p['name'] for p in json.loads(self.catalog.read_text())['plugins']],
                         ['ready'])

    def test_changed_identity_metadata_is_rejected(self):
        for key in ['version', 'description', 'name']:
            with self.subTest(key=key):
                manifest = self.root / 'plugins/ready/.claude-plugin/plugin.json'
                original = manifest.read_text()
                data = json.loads(original)
                data[key] = 'changed'
                self.write_json(manifest, data)
                self.assert_rejected(key)
                manifest.write_text(original)

    def test_unknown_platform(self):
        self.entries[0]['platforms'].append('unknown')
        self.save_source()
        self.assert_rejected('platforms')

    def test_invalid_arguments(self):
        self.assertEqual(self.run_script('--check', '--write').returncode, 2)

    def test_atomic_write_failure_preserves_original_and_cleans_temporary(self):
        self.write_json(self.catalog, {'original': True})
        original = self.catalog.read_bytes()
        spec = importlib.util.spec_from_file_location('marketplace_atomic_test', SCRIPT)
        marketplace = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(marketplace)
        with mock.patch.object(marketplace.os, 'replace', side_effect=OSError('falha simulada')):
            with self.assertRaisesRegex(OSError, 'falha simulada'):
                marketplace.atomic_write(self.catalog, b'{"new":true}\n')
        self.assertEqual(self.catalog.read_bytes(), original)
        self.assertEqual(list(self.catalog.parent.iterdir()), [self.catalog])


if __name__ == '__main__':
    unittest.main()
