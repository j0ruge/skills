import json
from pathlib import Path
import subprocess
import sys
import unittest

import test_codex_marketplace

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/codex-adapters.py'


class AdapterTests(unittest.TestCase):
    write_json = test_codex_marketplace.MarketplaceTests.write_json
    save_source = test_codex_marketplace.MarketplaceTests.save_source

    def setUp(self):
        test_codex_marketplace.MarketplaceTests.setUp(self)
        self.plugin = self.root / 'plugins/ready'
        self.config = self.plugin / 'codex-adapter.json'
        (self.plugin / 'commands').mkdir()
        (self.plugin / 'templates').mkdir()
        (self.plugin / 'commands/ready.md').write_text(
            '---\ndescription: "Example command"\n---\n'
            'Use $ARGUMENTS. Prefer templates/demo.md in the project; otherwise use '
            '${CLAUDE_PLUGIN_ROOT}/templates/demo.md. Then /next:go.\n')
        (self.plugin / 'templates/demo.md').write_text('# Template\n')
        self.mapping = dict(commands=[dict(name='ready', source='./commands/ready.md',
                              explicit=True, invocations={'/next:go': '$next:go'},
                              resources=[dict(source='./templates/demo.md', target='assets/demo.md')])])
        self.write_json(self.config, self.mapping)

    def adapter(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), '--root', str(self.root), *args],
                              capture_output=True, text=True)

    def test_generates_arguments_template_policy_and_no_legacy_duplicate(self):
        result = self.adapter('--write')
        self.assertEqual(result.returncode, 0, result.stderr)
        skill = self.plugin / 'codex-skills/ready'
        text = (skill / 'SKILL.md').read_text()
        self.assertIn('name: ready', text)
        self.assertNotIn('$ARGUMENTS', text)
        self.assertNotIn('${CLAUDE_PLUGIN_ROOT}', text)
        self.assertIn('assets/demo.md', text)
        self.assertIn('$next:go', text)
        self.assertEqual((skill / 'assets/demo.md').read_text(), '# Template\n')
        self.assertIn('allow_implicit_invocation: false', (skill / 'agents/openai.yaml').read_text())
        manifest = json.loads((self.plugin / '.codex-plugin/plugin.json').read_text())
        self.assertEqual(manifest['version'], '1.0.0')
        self.assertEqual(manifest['commands'], [])
        self.assertEqual(manifest['skills'], ['./skills', './codex-skills'])
        before = {p: p.read_bytes() for p in self.plugin.rglob('*') if p.is_file()}
        self.assertEqual(self.adapter('--check').returncode, 0)
        self.assertEqual({p: p.read_bytes() for p in self.plugin.rglob('*') if p.is_file()}, before)

    def test_missing_resource_rejects_before_any_write(self):
        (self.plugin / 'templates/demo.md').unlink()
        result = self.adapter('--write')
        self.assertEqual(result.returncode, 1)
        self.assertIn('demo.md', result.stderr)
        self.assertFalse((self.plugin / 'codex-skills').exists())

    def test_changed_source_and_resource_make_check_fail(self):
        self.assertEqual(self.adapter('--write').returncode, 0)
        for rel in ['commands/ready.md', 'templates/demo.md', '.claude-plugin/plugin.json']:
            path = self.plugin / rel
            original = path.read_text()
            if path.suffix == '.json':
                data = json.loads(original); data['version'] = '1.1.0'
                path.write_text(json.dumps(data))
                self.entries[0]['version'] = '1.1.0'; self.save_source()
            else:
                path.write_text(original + '\nChanged\n')
            self.assertEqual(self.adapter().returncode, 1, rel)
            path.write_text(original)
            self.entries[0]['version'] = '1.0.0'; self.save_source()

    def test_multiple_commands_preserve_group(self):
        self.mapping['commands'].append(dict(name='second', source='./commands/ready.md',
                                            resources=self.mapping['commands'][0]['resources']))
        self.write_json(self.config, self.mapping)
        self.assertEqual(self.adapter('--write').returncode, 0)
        self.assertTrue((self.plugin / 'codex-skills/second/SKILL.md').is_file())
        self.assertTrue((self.plugin / 'codex-skills/ready/SKILL.md').is_file())

    def test_resource_target_escape_is_rejected(self):
        self.mapping['commands'][0]['resources'][0]['target'] = '../SKILL.md'
        self.write_json(self.config, self.mapping)
        result = self.adapter('--write')
        self.assertEqual(result.returncode, 1)
        self.assertIn('target', result.stderr)

    def test_unmapped_plugin_variable_is_rejected(self):
        path = self.plugin / 'commands/ready.md'
        path.write_text(path.read_text() + '${CLAUDE_PLUGIN_ROOT}/missing/file')
        self.assertEqual(self.adapter('--write').returncode, 1)

    def test_stale_generated_file_is_rejected(self):
        self.assertEqual(self.adapter('--write').returncode, 0)
        (self.plugin / 'codex-skills/ready/stale.md').touch()
        self.assertEqual(self.adapter('--check').returncode, 1)

    def test_source_explicit_invocation_cannot_be_lost(self):
        self.mapping['commands'][0].pop('explicit')
        self.write_json(self.config, self.mapping)
        source = self.plugin / 'commands/ready.md'
        source.write_text(source.read_text().replace('description:',
                          'disable-model-invocation: true\ndescription:', 1))
        self.assertEqual(self.adapter('--write').returncode, 0)
        policy = self.plugin / 'codex-skills/ready/agents/openai.yaml'
        self.assertTrue(policy.is_file())
        self.assertIn('allow_implicit_invocation: false', policy.read_text())


if __name__ == '__main__':
    unittest.main()
