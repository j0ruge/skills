"""Provas locais reais do CLI; não executam modelo nem operações dos workflows."""

import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import select
import subprocess
import tarfile
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
CLI = shutil.which('codex')
BWRAP = shutil.which('bwrap')
PERSONAL_HOME = Path.home()


@unittest.skipUnless(CLI and BWRAP, 'Prova real requer Codex CLI e Bubblewrap no Linux')
class DistributionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.profile = self.base / 'profile'
        self.fixture = self.base / 'fixture'
        self.profile.mkdir(); self.fixture.mkdir()
        self.evidence = dict(client=subprocess.check_output([CLI, '--version'], text=True).strip(),
                             revision=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                             commands=[])

    def tearDown(self):
        # Saída estruturada preservada pelo comando de unittest no relatório do executor.
        print('DISTRIBUTION_EVIDENCE ' + json.dumps(self.evidence, ensure_ascii=False))

    def sandbox(self, *args):
        binary_dir = Path(CLI).resolve().parent
        return [BWRAP, '--ro-bind', '/', '/', '--tmpfs', '/tmp',
                '--ro-bind', str(binary_dir), '/tmp/codex-bin',
                '--bind', str(self.fixture), '/tmp/work',
                '--bind', str(self.profile), str(PERSONAL_HOME),
                '--dev', '/dev', '--proc', '/proc', '--clearenv',
                '--setenv', 'HOME', str(PERSONAL_HOME), '--setenv', 'PATH', '/usr/bin:/bin',
                '--chdir', '/tmp/work', '/tmp/codex-bin/codex', *args]

    def cli(self, *args):
        result = subprocess.run(self.sandbox(*args), capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.evidence['commands'].append(dict(args=args, result=data))
        return data

    def git(self, cwd, *args):
        result = subprocess.run(['git', *args], cwd=cwd, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.strip()

    def candidate(self, target):
        archive = subprocess.check_output(['git', 'archive', 'HEAD'], cwd=ROOT)
        target.mkdir(parents=True, exist_ok=True)
        with tarfile.open(fileobj=io.BytesIO(archive)) as bundle:
            bundle.extractall(target, filter='data')

    def installed(self, data):
        return self.profile / Path(data['installedPath']).relative_to(PERSONAL_HOME)

    def assert_payload(self, source, installed):
        hashes = {}
        for path in sorted(source.rglob('*')):
            if path.is_file():
                relative = path.relative_to(source)
                copied = installed / relative
                self.assertTrue(copied.is_file(), str(relative))
                self.assertEqual(copied.read_bytes(), path.read_bytes(), str(relative))
                hashes[str(relative)] = dict(sha256=hashlib.sha256(copied.read_bytes()).hexdigest())
        return hashes

    def discovered_skills(self):
        process = subprocess.Popen(self.sandbox('app-server', '--stdio'), stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=0)
        try:
            for message in [dict(id=1, method='initialize',
                                 params=dict(clientInfo=dict(name='distribution-test', version='1'))),
                            dict(method='initialized'),
                            dict(id=2, method='skills/list', params=dict(cwds=['/tmp/work'], forceReload=True))]:
                process.stdin.write((json.dumps(message)+'\n').encode('utf-8'))
                process.stdin.flush()
            pending = b''
            deadline = time.monotonic() + 10
            while (remaining := deadline - time.monotonic()) > 0:
                if not select.select([process.stdout], [], [], remaining)[0]:
                    break
                chunk = os.read(process.stdout.fileno(), 65536)
                if not chunk:
                    break
                pending += chunk
                while b'\n' in pending:
                    line, pending = pending.split(b'\n', 1)
                    message = json.loads(line)
                    if message.get('id') == 2:
                        rows = message['result']['data']
                        self.assertFalse(any(row['errors'] for row in rows), rows)
                        return sorted(s['name'] for row in rows for s in row['skills'] if s.get('pluginId'))
            self.fail('skills/list não respondeu')
        finally:
            process.terminate()
            process.wait(timeout=10)
            process.stdin.close()
            process.stdout.close()

    def test_candidate_exact_catalog_individual_install_and_payloads(self):
        self.candidate(self.fixture)
        expected = json.loads((self.fixture / '.agents/plugins/marketplace.json').read_text())
        names = [p['name'] for p in expected['plugins']]
        self.cli('plugin', 'marketplace', 'add', '/tmp/work', '--json')
        listed = self.cli('plugin', 'list', '--marketplace', 'chewiesoft-marketplace', '--available', '--json')
        self.assertEqual(sorted(p['name'] for p in listed['available']), names)
        self.assertEqual(listed['installed'], [])
        added = self.cli('plugin', 'add', 'skill-quality-audit@chewiesoft-marketplace', '--json')
        listed = self.cli('plugin', 'list', '--marketplace', 'chewiesoft-marketplace', '--json')
        self.assertEqual([p['name'] for p in listed['installed']], ['skill-quality-audit'])
        copied = self.installed(added)
        self.assertEqual(sorted(p.parent.name for p in (copied / 'skills').glob('*/SKILL.md')),
                         ['skill-claim-check', 'skill-quality-audit', 'skill-refactoring', 'skill-self-containment'])
        discovered = self.discovered_skills()
        self.assertEqual(discovered, ['skill-quality-audit:skill-claim-check',
                                     'skill-quality-audit:skill-quality-audit',
                                     'skill-quality-audit:skill-refactoring',
                                     'skill-quality-audit:skill-self-containment'])
        self.evidence['individual_skills'] = discovered
        audit_command = self.sandbox()[:-1] + [
            '/usr/bin/python3', added['installedPath'] +
            '/skills/skill-quality-audit/scripts/audit_skill_quality.py',
            '--family', '--external', 'off', '--no-changelog-required',
            '--desc-budget', '0', '--format', 'json']
        audit = subprocess.run(audit_command, capture_output=True, text=True, timeout=45)
        self.assertEqual(audit.returncode, 0, audit.stderr)
        family = json.loads(audit.stdout)
        self.assertFalse(family['skipped_family'], family['skipped_family'])
        self.assertEqual(sorted(s['name'] for s in family['skills']),
                         ['skill-claim-check', 'skill-quality-audit', 'skill-refactoring', 'skill-self-containment'])
        self.evidence['family_audit'] = family['summary']
        payloads = {}
        for name in names:
            added = self.cli('plugin', 'add', name + '@chewiesoft-marketplace', '--json')
            payloads[name] = dict(version=added['version'],
                                 hashes=self.assert_payload(self.fixture / 'plugins' / name, self.installed(added)))
        self.evidence['payloads'] = payloads

    def test_missing_resource_is_detected_in_fresh_installed_package(self):
        self.candidate(self.fixture)
        (self.fixture / 'plugins/criar-prd/codex-skills/criar-prd/assets/prd-template.md').unlink()
        self.cli('plugin', 'marketplace', 'add', '/tmp/work', '--json')
        added = self.cli('plugin', 'add', 'criar-prd@chewiesoft-marketplace', '--json')
        copied = self.installed(added)
        with self.assertRaises(AssertionError):
            self.assert_payload(ROOT / 'plugins/criar-prd', copied)
        self.assertFalse((copied / 'codex-skills/criar-prd/assets/prd-template.md').exists())
        self.evidence['sabotage'] = 'template ausente detectado na cópia instalada em perfil novo'

    def test_git_refresh_reinstall_and_removal(self):
        origin = self.fixture / 'origin'
        self.candidate(origin)
        self.git(origin, 'init', '-q', '-b', 'main')
        self.git(origin, 'config', 'user.name', 'Teste de distribuição')
        self.git(origin, 'config', 'user.email', 'test@example.test')
        self.git(origin, 'add', '.')
        self.git(origin, 'commit', '-qm', 'Primeiro candidato')
        first_revision = self.git(origin, 'rev-parse', 'HEAD')
        # O CLI trata esta origem como Git; apenas o transporte é redirecionado localmente.
        (self.profile / '.gitconfig').write_text(
            '[url "file:///tmp/work/origin"]\n'
            '    insteadOf = https://example.invalid/codex-marketplace.git\n')
        registered = self.cli('plugin', 'marketplace', 'add',
                              'https://example.invalid/codex-marketplace.git', '--ref', 'main', '--json')
        added = self.cli('plugin', 'add', 'cors@chewiesoft-marketplace', '--json')
        old_cache = self.installed(added)
        old_skill = (old_cache / 'skills/cors/SKILL.md').read_bytes()
        old_version = added['version']
        for path in [origin / 'plugins/cors/.claude-plugin/plugin.json',
                     origin / '.claude-plugin/marketplace.json']:
            data = json.loads(path.read_text())
            if 'plugins' in data:
                next(p for p in data['plugins'] if p['name'] == 'cors')['version'] = '99.0.0'
            else:
                data['version'] = '99.0.0'
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n')
        skill = origin / 'plugins/cors/skills/cors/SKILL.md'
        skill.write_text(skill.read_text()+'\nMarcador da segunda revisão de teste.\n')
        self.git(origin, 'add', '.')
        self.git(origin, 'commit', '-qm', 'Segunda revisão para provar refresh')
        second_revision = self.git(origin, 'rev-parse', 'HEAD')
        refreshed = self.cli('plugin', 'marketplace', 'upgrade', 'chewiesoft-marketplace', '--json')
        self.assertFalse(refreshed.get('errors'), refreshed)
        after_refresh = self.cli('plugin', 'list', '--marketplace', 'chewiesoft-marketplace', '--json')
        self.assertEqual([p['version'] for p in after_refresh['installed']], ['99.0.0'])
        refreshed_cache = old_cache.parent / '99.0.0'
        self.assertIn(b'Marcador da segunda revis', (refreshed_cache / 'skills/cors/SKILL.md').read_bytes())
        self.assertFalse(old_cache.exists())
        self.evidence['git'] = dict(first=first_revision, second=second_revision,
                                    old_version=old_version, version_after_refresh='99.0.0',
                                    old_cache_removed=True,
                                    updated_skill_sha256=hashlib.sha256(
                                        (refreshed_cache / 'skills/cors/SKILL.md').read_bytes()).hexdigest())
        readded = self.cli('plugin', 'add', 'cors@chewiesoft-marketplace', '--json')
        self.evidence['git']['version_after_add'] = readded['version']
        self.cli('plugin', 'remove', 'cors@chewiesoft-marketplace', '--json')
        added = self.cli('plugin', 'add', 'cors@chewiesoft-marketplace', '--json')
        self.assertEqual(added['version'], '99.0.0')
        self.assertIn(b'Marcador da segunda revis', (self.installed(added) / 'skills/cors/SKILL.md').read_bytes())
        new_cache = self.installed(added)
        self.cli('plugin', 'remove', 'cors@chewiesoft-marketplace', '--json')
        listed = self.cli('plugin', 'list', '--marketplace', 'chewiesoft-marketplace', '--json')
        self.assertEqual(listed['installed'], [])
        self.assertFalse(new_cache.exists())
        self.cli('plugin', 'marketplace', 'remove', 'chewiesoft-marketplace', '--json')
        marketplaces = self.cli('plugin', 'marketplace', 'list', '--json')
        self.assertNotIn('chewiesoft-marketplace', [m['name'] for m in marketplaces['marketplaces']])


if __name__ == '__main__':
    unittest.main()
