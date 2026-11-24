"""Testes da loja fixture (fixture_store.py): ela passa nas próprias portas, os remotos ficam sob o
diretório temporário e os auxiliares fazem commits que as portas reais aceitam ou recusam.

Rodar: python3 plugins/retrofit-watch/skills/retrofit-watch/tests/test_fixture_store.py
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import fixture_store as fs  # noqa: E402
import rw_auto  # noqa: E402  (o test_retrofit_watch, importado pela fixture, põe scripts/ no path)


def a_real_remote():
    # Montado em tempo de execução: um literal de URL faria o portão do ramo reprovar este arquivo.
    return "https" + "://" + "example" + ".invalid/" + "loja.git"


@fs.requires_store
class StoreWorldTest(unittest.TestCase):
    def setUp(self):
        self.w = fs.StoreWorld()

    def tearDown(self):
        self.w.cleanup()

    def validate(self, repo):
        return self.w.run_script(repo, "scripts/validate-versions.py")

    def assertRc(self, proc, rc):
        self.assertEqual(proc.returncode, rc, proc.stdout + proc.stderr)

    def test_fixture_passes_its_own_gates(self):
        store = self.w.store
        proc = self.validate(store)
        self.assertRc(proc, 0)
        self.assertIn("All checks passed.", proc.stdout)
        for tests in ("plugins/demo/skills/demo/tests", "plugins/demo2/skills/demo2/tests",
                      "plugins/demo-cmd/tests", "tests"):
            with self.subTest(tests=tests):
                proc = self.w.run_tests(store, tests)
                self.assertRc(proc, 0)
                self.assertIn("OK", proc.stderr)
                self.assertNotIn("Ran 0 tests", proc.stderr)
        audit = self.w.run_script(store, fs.AUDITOR, "plugins/demo/skills/demo", "--format", "json",
                                  "--claims", "--desc-budget", "0", "--external", "off")
        self.assertRc(audit, 0)
        findings = json.loads(audit.stdout)["skills"][0]["findings"]
        self.assertEqual([f for f in findings if f["level"] == "ERRO"], [])
        self.assertTrue((store / fs.AUDIT_GATE).is_file())
        # O comparador do gate da auditoria roda na fixture: a mesma auditoria dos dois lados não dá NOVO.
        box = self.w.tmp / "gate"
        box.mkdir()
        for name in ("antes", "depois"):
            (box / f"{name}.json").write_text(audit.stdout, encoding="utf-8")
        (box / "diff.txt").write_text("", encoding="utf-8")
        gate = self.w.run_script(store, fs.AUDIT_GATE, str(box))
        self.assertRc(gate, 0)
        self.assertFalse([line for line in gate.stdout.splitlines() if line.startswith("NOVO")], gate.stdout)
        # Ruling C7: sem install.py (as verificações 5 e 8 se pulam) e com o catálogo Codex vazio.
        self.assertFalse((store / "install.py").exists())
        catalog = json.loads((store / ".agents/plugins/marketplace.json").read_text(encoding="utf-8"))
        self.assertEqual(catalog["plugins"], [])
        # O auditor vem sem o SKILL.md dele: nenhuma skill a mais para as portas.
        self.assertFalse((store / fs.AUDITOR).parent.parent.joinpath("SKILL.md").exists())

    def test_every_remote_is_under_the_temp_dir(self):
        for repo in (self.w.store, self.w.repo):
            with self.subTest(repo=repo):
                url = self.w.git(repo, "remote", "get-url", "origin")
                self.assertTrue(Path(url).is_relative_to(self.w.tmp), url)
                self.assertEqual(Path(os.path.realpath(url)), self.w.origin)
                remotes = self.w.git(repo, "remote", "-v")
                self.assertNotIn("git" + "hub", remotes)
                self.w.assert_fixture_origin(repo)

    def test_assert_fixture_origin_rejects_a_real_remote(self):
        repo = self.w.tmp / "real-remote"
        self.w.git(self.w.tmp, "clone", "-q", str(self.w.origin), str(repo))
        self.w.git(repo, "remote", "set-url", "origin", a_real_remote())
        with self.assertRaisesRegex(AssertionError, "origin fora da fixture"):
            self.w.assert_fixture_origin(repo)

    def test_assert_fixture_origin_checks_the_push_url(self):
        wt = self.w.worktree("push-url")
        self.w.git(self.w.store, "remote", "set-url", "--push", "origin", a_real_remote())
        for repo in (self.w.store, wt):
            with self.subTest(repo=repo):
                with self.assertRaisesRegex(AssertionError, "origin fora da fixture"):
                    self.w.assert_fixture_origin(repo)

    def test_assert_fixture_origin_rejects_a_repo_without_origin(self):
        repo = self.w.tmp / "no-origin"
        repo.mkdir()
        self.w.git(repo, "init", "-q")
        with self.assertRaisesRegex(AssertionError, "sem origin"):
            self.w.assert_fixture_origin(repo)

    def test_assert_fixture_origin_rejects_a_path_outside_the_temp_dir(self):
        outside = Path(os.path.realpath(tempfile.mkdtemp(prefix="rw-outside-")))
        try:
            self.w.git(self.w.store, "remote", "set-url", "origin", str(outside))
            with self.assertRaisesRegex(AssertionError, "origin fora da fixture"):
                self.w.assert_fixture_origin(self.w.store)
        finally:
            outside.rmdir()

    def test_assert_fixture_origin_rejects_a_relative_remote(self):
        # O git resolve um remoto relativo pelo repo, não pelo cwd de quem confere: mesmo com o cwd
        # na pasta da fixture, o caminho relativo não prova nada.
        self.w.git(self.w.store, "remote", "set-url", "origin", "origin.git")
        cwd = os.getcwd()
        os.chdir(self.w.tmp)
        try:
            with self.assertRaisesRegex(AssertionError, "origin fora da fixture"):
                self.w.assert_fixture_origin(self.w.store)
        finally:
            os.chdir(cwd)

    def test_retrofit_refuses_a_doc_without_the_version_line(self):
        wt = self.w.worktree("retro-sem-versao")
        with self.assertRaisesRegex(ValueError, "esperava"):
            self.w.retrofit(wt, files={"plugins/demo/skills/demo/SKILL.md": "---\nname: demo\n---\n"})

    def test_retrofit_helper_makes_a_valid_full_mode_commit(self):
        wt = self.w.worktree("retro-demo")
        before = self.w.shared_state()
        sha = self.w.retrofit(wt)
        self.assertRc(self.validate(wt), 0)
        self.assertEqual(self.w.git(wt, "rev-parse", "HEAD"), sha)
        self.assertEqual(self.w.git(wt, "rev-list", "--count", "origin/main..HEAD"), "1")
        self.assertEqual(self.w.git(wt, "log", "-1", "--format=%(trailers:key=Retrofit-Mode,valueonly)"),
                         "autonomous")
        changed = set(self.w.git(wt, "diff", "--name-only", "origin/main..HEAD").splitlines())
        self.assertEqual(changed, {"plugins/demo/.claude-plugin/plugin.json", "plugins/demo/CHANGELOG.md",
                                   "plugins/demo/skills/demo/SKILL.md", ".claude-plugin/marketplace.json",
                                   "README.md"})
        self.assertIn('version: "1.0.1"', (wt / "plugins/demo/skills/demo/SKILL.md").read_text(encoding="utf-8"))
        self.assertIn("- **demo** 1.0.1 ", (wt / "README.md").read_text(encoding="utf-8"))
        self.assertEqual(self.w.shared_state(), before, "o clone compartilhado não muda")

    def test_retrofit_helper_takes_files_message_and_no_trailer(self):
        wt = self.w.worktree("retro-files")
        self.w.retrofit(wt, files={"plugins/demo/skills/demo/references/nota.md": "# Nota\n"},
                        message="fix(demo): nota nova", trailer=None)
        self.assertRc(self.validate(wt), 0)
        self.assertEqual(self.w.git(wt, "log", "-1", "--format=%s"), "fix(demo): nota nova")
        self.assertEqual(self.w.git(wt, "log", "-1", "--format=%(trailers:key=Retrofit-Mode,valueonly)"), "")
        self.assertTrue((wt / "plugins/demo/skills/demo/references/nota.md").is_file())

    def test_retrofit_of_a_commands_only_plugin_is_valid(self):
        wt = self.w.worktree("retro-cmd")
        self.w.retrofit(wt, plugin="demo-cmd")
        self.assertRc(self.validate(wt), 0)
        self.assertFalse(list((wt / "plugins/demo-cmd").rglob("SKILL.md")))
        self.assertIn("version: 1.0.1\n", (wt / "plugins/demo-cmd/commands/demo-cmd.md").read_text(encoding="utf-8"))
        self.assertRc(self.w.run_tests(wt, "plugins/demo-cmd/tests"), 0)

    def test_broken_fixture_is_caught_by_the_real_gates(self):
        wt = self.w.worktree("retro-broken")
        self.w.retrofit(wt)
        path = wt / ".claude-plugin/marketplace.json"
        text = path.read_text(encoding="utf-8")
        self.assertEqual(text.count('"version": "1.0.1"'), 1)
        path.write_text(text.replace('"version": "1.0.1"', '"version": "1.0.2"'), encoding="utf-8")
        proc = self.validate(wt)
        self.assertRc(proc, 1)
        self.assertIn("demo: marketplace.json=1.0.2 != plugin.json=1.0.1", proc.stdout)

    def test_two_plugins_retrofitted_from_the_same_base_rebase_cleanly(self):
        # Ruling C7: uma linha intacta entre os blocos de cada arquivo compartilhado.
        previous = None
        for plugin in ("demo", "demo2", "demo-cmd"):
            wt = self.w.worktree(f"retro-{plugin}")
            self.w.retrofit(wt, plugin=plugin)
            if previous is not None:
                self.w.git(wt, "rebase", "-q", previous)
            previous = self.w.git(wt, "rev-parse", "HEAD")
        self.assertRc(self.validate(wt), 0)
        self.assertEqual(self.w.git(wt, "rev-list", "--count", "origin/main..HEAD"), "3")

    def test_advance_origin_moves_origin_main(self):
        old = self.w.origin_main()
        sha = self.w.advance_origin({"tests/extra.txt": "linha\n"}, "chore: outro clone", date="2026-11-01T12:00:00")
        self.assertNotEqual(sha, old)
        self.assertEqual(self.w.origin_main(), sha)
        self.assertNotEqual(self.w.git(self.w.store, "rev-parse", "origin/main"), sha, "antes do fetch")
        self.w.git(self.w.store, "fetch", "-q", "origin")
        self.assertEqual(self.w.git(self.w.store, "rev-parse", "origin/main"), sha)
        self.assertEqual(self.w.git(self.w.store, "log", "-1", "--format=%cI", "origin/main")[:19],
                         "2026-11-01T12:00:00")
        second = self.w.advance_origin({"tests/extra.txt": "outra\n"}, "chore: de novo")
        self.assertEqual(self.w.git(self.w.origin, "rev-parse", f"{second}^"), sha)

    def test_shared_state_is_head_branch_and_status(self):
        head, branch, status = self.w.shared_state()
        self.assertEqual(head, self.w.origin_main())
        self.assertEqual(branch, "main")
        self.assertEqual(status, "")
        (self.w.store / "solto.txt").write_text("x\n")
        self.assertEqual(self.w.shared_state()[2], "?? solto.txt")

    def test_config_is_auto_with_the_store(self):
        ctx = self.w.ctx()
        self.assertEqual(ctx.mode, "auto")
        self.assertEqual(ctx.store, self.w.store)

    def test_retro_writes_files_the_loaders_accept(self):
        rid = self.w.retro([{}, {"plugin": "demo-cmd"}], [{}, {"coberta": "x.md:3"}], skills=("demo", "demo-cmd"))
        folder = rw_auto.retro_dir(self.w.ctx(), rid)
        pedido = rw_auto.load_pedido(folder / "pedido.json")
        self.assertEqual(pedido["id"], rid)
        self.assertEqual(pedido["modo"], "auto")
        self.assertEqual(pedido["cwd"], str(self.w.proj))
        self.assertEqual([(e["plugin"], e["skills"]) for e in pedido["skills"]],
                         [("demo", ["demo"]), ("demo-cmd", [])])
        licoes = rw_auto.load_licoes(folder / "licoes.json")
        self.assertEqual([(l["n"], l["plugin"], l["skill"]) for l in licoes.values()],
                         [(1, "demo", "demo"), (2, "demo-cmd", "demo-cmd")])
        veredito = rw_auto.load_veredito(folder / "veredito.json")
        self.assertEqual(veredito["2"]["coberta"], "x.md:3")
        base = json.loads((folder / "veredito.json").read_text(encoding="utf-8"))["base"]
        self.assertEqual(base, self.w.origin_main())
        ctx = self.w.ctx()
        self.assertEqual(rw_auto.classify(licoes["1"], veredito["1"]), ("publicar", None))
        self.assertTrue(all(rw_auto.in_request(ctx, pedido, l) for l in licoes.values()))
        self.assertNotEqual(self.w.retro([{}], [{}]), rid, "um id por retro")

    def test_retro_without_verdict_writes_no_veredito(self):
        rid = self.w.retro([{}], None)
        folder = rw_auto.retro_dir(self.w.ctx(), rid)
        self.assertTrue((folder / "licoes.json").is_file())
        self.assertFalse((folder / "veredito.json").exists())

    def test_git_ignores_location_variables_of_the_environment(self):
        # Um GIT_DIR herdado (o de um hook de pré-commit, por exemplo) faria a fixture escrever no
        # repo de fora.
        decoy = self.w.tmp / "decoy"
        decoy.mkdir()
        self.w.git(decoy, "init", "-q")
        trap = {"GIT_DIR": str(decoy / ".git"), "GIT_WORK_TREE": str(decoy),
                "GIT_INDEX_FILE": str(decoy / ".git/index")}
        with mock.patch.dict(os.environ, trap):
            other = fs.StoreWorld()
        try:
            self.assertEqual(other.git(other.store, "rev-parse", "HEAD"), other.origin_main())
            self.assertFalse((decoy / ".git/refs/heads/main").exists())
            self.assertEqual(subprocess.run(["git", "-C", str(decoy), "rev-parse", "-q", "--verify", "HEAD"],
                                            capture_output=True, env=other.env).returncode, 1)
        finally:
            other.cleanup()

    def test_clean_env_drops_an_inherited_plugin_data_dir(self):
        # O script lê o CLAUDE_PLUGIN_DATA: herdado, ele apontaria a pasta de dados real do plugin.
        with mock.patch.dict(os.environ, {"CLAUDE_PLUGIN_DATA": str(self.w.tmp / "dados-reais")}):
            env = fs._clean_env(self.w.home)
        self.assertNotIn("CLAUDE_PLUGIN_DATA", env)
        self.assertEqual(env["HOME"], str(self.w.home))

    def test_git_reads_the_fixture_home_config(self):
        (self.w.home / ".gitconfig").write_text("[user]\n\tname = fixture-only\n")
        self.assertEqual(self.w.git(self.w.store, "config", "--global", "user.name"), "fixture-only")


class RequiresStoreTest(unittest.TestCase):
    def test_skips_without_the_store_root_above(self):
        installed = Path(os.path.realpath(tempfile.mkdtemp(prefix="rw-installed-")))
        try:
            tests = installed / "retrofit-watch/0.3.7/skills/retrofit-watch/tests"
            tests.mkdir(parents=True)
            self.assertIsNone(fs.find_store_root(tests))
            self.assertIn("cópia instalada", fs.store_skip_reason(None, True))
        finally:
            shutil.rmtree(installed)

    def test_finds_the_store_root_of_this_checkout(self):
        root = fs.find_store_root(HERE)
        if root is None:
            self.skipTest("cópia instalada: sem a raiz da loja acima")
        self.assertTrue((root / "scripts/validate-versions.py").is_file())
        self.assertEqual(root, HERE.parents[4])

    def test_skips_without_pyyaml(self):
        self.assertIn("PyYAML", fs.store_skip_reason(Path("."), False))

    def test_runs_with_both(self):
        self.assertIsNone(fs.store_skip_reason(Path("."), True))

    def test_the_decorator_skips_with_the_reason(self):
        with mock.patch.object(fs, "STORE_ROOT", None):
            @fs.requires_store
            class Probe(unittest.TestCase):
                def test_x(self):
                    pass
        result = unittest.TestResult()
        Probe("test_x").run(result)
        self.assertEqual(len(result.skipped), 1)
        self.assertIn("cópia instalada", result.skipped[0][1])


if __name__ == "__main__":
    unittest.main()
