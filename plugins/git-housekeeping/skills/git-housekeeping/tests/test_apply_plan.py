"""A CLI apply_plan.py: só o plano, só o escopo pedido, e cada item provado de novo na hora."""
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
SCRIPTS = HERE.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(HERE))
import apply_plan  # noqa: E402
from fixture import Fixture, snapshot  # noqa: E402


class ApplyTest(unittest.TestCase):
    """Cada teste: um repo, um plano, e o que acontece com ele depois."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.fx = Fixture(self.root / "fx")
        self.plan = self.root / "scratch" / "plano.json"

    def tearDown(self):
        self.tmp.cleanup()

    def analyze(self) -> Path:
        """Gera o plano como a skill gera."""
        r = subprocess.run([sys.executable, str(SCRIPTS / "analyze.py"), "--repo", str(self.fx.clone),
                            "--plan", str(self.plan)], capture_output=True, text=True,
                           encoding="utf-8", env=self.fx.env())
        self.assertEqual(r.returncode, 0, r.stderr)
        return self.plan

    def apply(self, *args):
        """Roda o apply_plan.py no ambiente da fixture."""
        return subprocess.run([sys.executable, str(SCRIPTS / "apply_plan.py"), *map(str, args)],
                              capture_output=True, text=True, encoding="utf-8", env=self.fx.env())

    def merged(self, name):
        """Branch publicada e mergeada por merge commit; devolve a ponta."""
        tip = self.fx.branch(name)
        self.fx.merge(name, pr=False)
        return tip

    def test_local_e_depois_remoto_com_desfazer(self):
        """As duas confirmações são duas chamadas: a local não toca no remoto, e vice-versa."""
        tip = self.merged("feat/a")
        plan = self.analyze()
        r = self.apply("--plan", plan, "--scope", "local")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertNotIn("feat/a", self.fx.local_branches())
        self.assertIn("feat/a", self.fx.remote_branches())
        self.assertIn(f"desfazer: git branch feat/a {tip}", r.stdout)
        cfg = self.fx.env()
        leftover = subprocess.run(["git", "-C", str(self.fx.clone), "config", "--get-regexp", r"^branch\.feat/a\."],
                                  capture_output=True, text=True, env=cfg)
        self.assertEqual(leftover.stdout, "")
        r = self.apply("--plan", plan, "--scope", "remote")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertNotIn("feat/a", self.fx.remote_branches())
        self.assertIn(f"desfazer: git push origin {tip}:refs/heads/feat/a", r.stdout)

    def test_desfazer_sai_na_ordem_inversa(self):
        """O worktree só volta depois da branch: as linhas de desfazer vêm do último apagado ao primeiro."""
        self.merged("feat/w")
        self.fx.worktree("wt-w", "feat/w")
        plan = self.analyze()
        r = self.apply("--plan", plan, "--scope", "local")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        undo = [line for line in r.stdout.splitlines() if line.startswith("desfazer: ")]
        self.assertEqual(len(undo), 2, undo)
        self.assertTrue(undo[0].startswith("desfazer: git branch feat/w "), undo)
        self.assertTrue(undo[1].startswith("desfazer: git worktree add "), undo)

    def test_gh_que_falha_no_apply_segura_a_remota(self):
        """O PR aberto pode ter nascido depois do plano; sem gh para conferir, a remota fica (I1)."""
        self.merged("feat/a")
        plan = self.analyze()
        r = subprocess.run([sys.executable, str(SCRIPTS / "apply_plan.py"), "--plan", str(plan),
                            "--scope", "remote"], capture_output=True, text=True, encoding="utf-8",
                           env=self.fx.env(FAKE_GH_FAIL="1"))
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("PR aberto não pode ser conferido", r.stdout)
        self.assertIn("feat/a", self.fx.remote_branches())

    def test_ignorado_novo_depois_do_plano_segura_o_worktree(self):
        """O usuário confirmou sem ver o .env.production: o worktree fica (I2)."""
        self.merged("feat/w")
        wt = self.fx.worktree("wt-w", "feat/w")
        plan = self.analyze()
        (wt / ".env.production").write_text("SEGREDO=1\n")
        r = self.apply("--plan", plan, "--scope", "local")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("ignorados novos", r.stdout)
        self.assertTrue((wt / ".env.production").exists())

    def test_apply_de_dentro_do_worktree_nao_o_remove(self):
        """O plano veio do checkout principal; o apply roda de dentro do worktree: ele fica (I3)."""
        self.merged("feat/w")
        wt = self.fx.worktree("wt-w", "feat/w")
        plan = self.analyze()
        r = subprocess.run([sys.executable, str(SCRIPTS / "apply_plan.py"), "--plan", str(plan),
                            "--scope", "local"], capture_output=True, text=True, encoding="utf-8",
                           env=self.fx.env(), cwd=wt)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertTrue(wt.exists())

    def test_escopo_trocado_a_mao_e_recusado(self):
        """Item local editado para o escopo remoto apagaria a remota sem classificá-la (M2)."""
        self.merged("feat/a")
        plan = self.analyze()
        data = json.loads(plan.read_text(encoding="utf-8"))
        data["items"] = [dict(i, scope="remote") if i["kind"] == "local-branch" else i
                         for i in data["items"] if i["kind"] != "remote-branch"]
        plan.write_text(json.dumps(data), encoding="utf-8")
        r = self.apply("--plan", plan, "--scope", "remote")
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn("escopo", r.stderr)
        self.assertIn("feat/a", self.fx.remote_branches())

    def test_ponta_local_que_andou_e_recusada(self):
        """Um commit depois do plano tira a prova: a branch fica, e o rc diz que algo foi recusado."""
        self.merged("feat/a")
        plan = self.analyze()
        self.fx.git(self.fx.clone, "switch", "-q", "feat/a")
        self.fx.commit("depois do plano")
        self.fx.git(self.fx.clone, "switch", "-q", "main")
        r = self.apply("--plan", plan, "--scope", "local")
        self.assertEqual(r.returncode, 1)
        self.assertIn("recusado: branch local feat/a", r.stdout)
        self.assertIn("feat/a", self.fx.local_branches())

    def test_item_editado_para_delete_e_recusado(self):
        """O plano é lista, não prova: um keep trocado à mão por delete não passa."""
        self.fx.branch("wip/x", push=False)
        plan = self.analyze()
        data = json.loads(plan.read_text(encoding="utf-8"))
        for i in data["items"]:
            if i["name"] == "wip/x":
                i["decision"] = "delete"
        plan.write_text(json.dumps(data), encoding="utf-8")
        r = self.apply("--plan", plan, "--scope", "local")
        self.assertEqual(r.returncode, 1)
        self.assertIn("agora é keep", r.stdout)
        self.assertIn("wip/x", self.fx.local_branches())

    def test_plano_de_outro_repo(self):
        """O plano de um repo não roda em outro."""
        self.merged("feat/a")
        plan = self.analyze()
        other = Fixture(self.root / "outro")
        data = json.loads(plan.read_text(encoding="utf-8"))
        data["repo"] = str(other.clone)
        plan.write_text(json.dumps(data), encoding="utf-8")
        r = self.apply("--plan", plan, "--scope", "local")
        self.assertEqual(r.returncode, 2)
        self.assertIn("outro repo", r.stderr)

    def test_escopo_invalido(self):
        """Não existe escopo "tudo": cada confirmação é uma chamada."""
        plan = self.analyze()
        r = self.apply("--plan", plan, "--scope", "tudo")
        self.assertEqual(r.returncode, 2)

    def test_worktree_que_sujou_depois_do_plano(self):
        """O arquivo novo é trabalho: o worktree fica, e a branch dele também."""
        self.merged("feat/w")
        wt = self.fx.worktree("wt-w", "feat/w")
        plan = self.analyze()
        (wt / "novo.txt").write_text("trabalho novo")
        r = self.apply("--plan", plan, "--scope", "local")
        self.assertEqual(r.returncode, 1)
        self.assertTrue((wt / "novo.txt").exists())
        self.assertIn("feat/w", self.fx.local_branches())

    def test_prunable_fora_do_plano_recusa_o_prune(self):
        """O prune leva todo prunable; com um fora do plano, não roda, e a branch presa fica."""
        self.merged("feat/p")
        shutil.rmtree(self.fx.worktree("wt-p", "feat/p"))
        plan = self.analyze()
        self.merged("feat/q")
        shutil.rmtree(self.fx.worktree("wt-q", "feat/q"))
        r = self.apply("--plan", plan, "--scope", "local")
        self.assertEqual(r.returncode, 1)
        self.assertIn("fora do plano", r.stdout)
        self.assertIn("feat/p", self.fx.local_branches())

    def test_lease_recusa_so_a_branch_que_mudou(self):
        """Sem --atomic: a lease velha recusa uma branch e a outra sai no mesmo push."""
        tip_a = self.merged("feat/a")
        self.merged("feat/b")
        with mock.patch.dict(os.environ, self.fx.env()):
            result, _tail = apply_plan.push_deletions(
                self.fx.clone, "origin", [("feat/a", tip_a), ("feat/b", "1" * 40)])
        self.assertEqual(result["feat/a"], (True, "[deleted]"))
        self.assertFalse(result["feat/b"][0])
        self.assertIn("stale info", result["feat/b"][1])
        self.assertEqual(self.fx.remote_branches() & {"feat/a", "feat/b"}, {"feat/b"})

    def test_remota_que_andou_e_recusada_e_as_outras_saem(self):
        """O commit de outra pessoa depois do plano: aquela fica, as outras saem."""
        self.merged("feat/a")
        self.merged("feat/b")
        plan = self.analyze()
        self.fx.remote_commit("feat/b")
        r = self.apply("--plan", plan, "--scope", "remote")
        self.assertEqual(r.returncode, 1)
        self.assertEqual(self.fx.remote_branches() & {"feat/a", "feat/b"}, {"feat/b"})
        self.assertIn("recusado: branch remota feat/b", r.stdout)

    def test_pre_push_que_recusa(self):
        """O pre-push roda e manda; o relatório traz o que ele disse, e nada sai."""
        self.merged("feat/a")
        plan = self.analyze()
        hook = self.fx.clone / ".git" / "hooks" / "pre-push"
        hook.write_text("#!/bin/sh\necho bloqueado-pelo-hook >&2\nexit 1\n")
        hook.chmod(0o755)
        r = self.apply("--plan", plan, "--scope", "remote")
        self.assertEqual(r.returncode, 1)
        self.assertIn("o push não rodou", r.stdout)
        self.assertIn("bloqueado-pelo-hook", r.stdout)
        self.assertIn("feat/a", self.fx.remote_branches())

    def test_dry_run_nao_muda_nada(self):
        """O --dry-run verifica tudo e diz o que faria, sem apagar nada."""
        self.merged("feat/a")
        self.merged("feat/w")
        self.fx.worktree("wt-w", "feat/w")
        plan = self.analyze()
        before = (snapshot(self.fx.clone), self.fx.remote_branches())
        for scope in ("local", "remote"):
            r = self.apply("--plan", plan, "--scope", scope, "--dry-run")
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("faria: ", r.stdout)
        self.assertEqual((snapshot(self.fx.clone), self.fx.remote_branches()), before)

    def test_only_apaga_so_o_aprovado(self):
        """O usuário aprovou 1 dos 2: o --only apaga esse, e o outro fica no plano e no repo."""
        self.merged("feat/a")
        self.merged("feat/b")
        plan = self.analyze()
        r = self.apply("--plan", plan, "--scope", "local", "--only", "feat/a")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertNotIn("feat/a", self.fx.local_branches())
        self.assertIn("feat/b", self.fx.local_branches())
        self.assertIn("fora do --only: 1 item(s) deste escopo ficam", r.stdout)
        r = self.apply("--plan", plan, "--scope", "remote", "--only", "feat/a")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertNotIn("feat/a", self.fx.remote_branches())
        self.assertIn("feat/b", self.fx.remote_branches())

    def test_only_que_nao_casa_e_uso_invalido(self):
        """Nome que não é delete no escopo sai com rc 2 e nada muda, em vez do "nada a apagar" com rc 0."""
        self.merged("feat/a")
        plan = self.analyze()
        before = (snapshot(self.fx.clone), self.fx.remote_branches())
        r = self.apply("--plan", plan, "--scope", "local", "--only", "feat/a", "--only", "branch feat/a")
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn("'branch feat/a'", r.stderr)
        self.assertIn("feat/a", r.stderr.split("aceita:", 1)[-1])
        self.assertEqual((snapshot(self.fx.clone), self.fx.remote_branches()), before)

    def test_only_no_dry_run_mostra_so_o_aprovado(self):
        """O --dry-run com --only diz que faria só o escolhido."""
        self.merged("feat/a")
        self.merged("feat/b")
        plan = self.analyze()
        r = self.apply("--plan", plan, "--scope", "local", "--only", "feat/b", "--dry-run")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("faria: branch local feat/b", r.stdout)
        self.assertNotIn("feat/a", r.stdout.replace("fora do --only", ""))
        self.assertIn("feat/a", self.fx.local_branches())

    def test_plano_vazio(self):
        """Sem nada a apagar, sai 0 e diz isso (Review Focus 4)."""
        plan = self.analyze()
        r = self.apply("--plan", plan, "--scope", "local")
        self.assertEqual(r.returncode, 0)
        self.assertIn("nada a apagar neste escopo", r.stdout)

    def test_nome_com_acento_ida_e_volta(self):
        """feat/ação sai local e remota (Review Focus 1)."""
        self.merged("feat/ação")
        plan = self.analyze()
        self.assertEqual(self.apply("--plan", plan, "--scope", "local").returncode, 0)
        self.assertEqual(self.apply("--plan", plan, "--scope", "remote").returncode, 0)
        self.assertNotIn("feat/ação", self.fx.local_branches())
        self.assertNotIn("feat/ação", self.fx.remote_branches())

    def test_symlink_ignorado_sai_e_o_destino_fica(self):
        """O git worktree remove apaga o link, não o destino (magic_tutor, 2026-10-26)."""
        self.merged("feat/w")
        wt = self.fx.worktree("wt-w", "feat/w")
        venv = self.root / "venv-do-checkout"
        (venv / "bin").mkdir(parents=True)
        (venv / "bin" / "python").write_text("#!/bin/sh\n", encoding="utf-8")
        with open(self.fx.clone / ".git" / "info" / "exclude", "a", encoding="utf-8") as f:
            f.write(".venv\n")
        (wt / ".venv").symlink_to(venv)
        plan = self.analyze()
        r = self.apply("--plan", plan, "--scope", "local")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertFalse(wt.exists())
        self.assertTrue((venv / "bin" / "python").is_file())

    @unittest.skipUnless(os.path.isdir("/proc/self"), "sem /proc: a varredura de processos não roda")
    def test_processo_que_entrou_depois_do_plano_segura_o_worktree(self):
        """A sessão abriu no worktree depois do plano: o apply recusa e o worktree fica."""
        self.merged("feat/w")
        wt = self.fx.worktree("wt-w", "feat/w")
        plan = self.analyze()
        proc = subprocess.Popen(["sleep", "60"], cwd=wt)
        try:
            r = self.apply("--plan", plan, "--scope", "local")
        finally:
            proc.kill()
            proc.wait()
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn(f"pid {proc.pid}", r.stdout)
        self.assertTrue(wt.exists())


if __name__ == "__main__":
    unittest.main()
