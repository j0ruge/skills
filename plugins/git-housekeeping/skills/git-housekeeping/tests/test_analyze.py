"""A CLI analyze.py: plano fora do repo, relatório, erros com rc 2 e a varredura que só lê."""
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ANALYZE = HERE.parent / "scripts" / "analyze.py"
sys.path.insert(0, str(HERE))
from fixture import Fixture, snapshot  # noqa: E402


def run(fx, *args):
    """Roda o analyze.py como o agente rodaria, no ambiente da fixture."""
    return subprocess.run([sys.executable, str(ANALYZE), *map(str, args)], capture_output=True,
                          text=True, encoding="utf-8", env=fx.env())


class AnalyzeCliTest(unittest.TestCase):
    """Um repo por teste: o analyze não pode depender do que o anterior deixou."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.fx = Fixture(self.root / "fx")
        self.plan = self.root / "scratch" / "plano.json"

    def tearDown(self):
        self.tmp.cleanup()

    def test_relatorio_e_plano(self):
        """O plano é gravado fora do repo e o relatório traz os três grupos e o disco."""
        self.fx.branch("feat/a"); self.fx.merge("feat/a", pr=False)
        self.fx.branch("wip/b", push=False)
        r = run(self.fx, "--repo", self.fx.clone, "--plan", self.plan)
        self.assertEqual(r.returncode, 0, r.stderr)
        plan = json.loads(self.plan.read_text(encoding="utf-8"))
        self.assertEqual(plan["version"], 1)
        self.assertEqual(plan["default_branch"], "main")
        decisions = {(i["kind"], i["name"]): i["decision"] for i in plan["items"]}
        self.assertEqual(decisions[("local-branch", "feat/a")], "delete")
        self.assertEqual(decisions[("local-branch", "wip/b")], "keep")
        for part in ("SAI (", "NÃO PROVADO", "FICA (", "DISCO", "branches e refs: ~0", str(self.plan)):
            self.assertIn(part, r.stdout)

    def test_nada_a_limpar(self):
        """Repo só com a main: o relatório diz isso em vez de uma lista vazia muda (Review Focus 4)."""
        r = run(self.fx, "--repo", self.fx.clone, "--plan", self.plan)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Nada a limpar.", r.stdout)

    def test_plano_dentro_do_repo_recusado(self):
        """O plano dentro da árvore a sujaria e faria o pre-push recusar o próximo push."""
        inside = self.fx.clone / "plano.json"
        r = run(self.fx, "--repo", self.fx.clone, "--plan", inside)
        self.assertEqual(r.returncode, 2)
        self.assertIn("não pode ficar dentro", r.stderr)
        self.assertFalse(inside.exists())

    def test_plano_dentro_de_outro_worktree_recusado(self):
        """Um worktree ligado também é árvore do repo: sujá-lo o seguraria na próxima análise."""
        self.fx.branch("feat/w"); self.fx.merge("feat/w", pr=False)
        wt = self.fx.worktree("wt-w", "feat/w")
        r = run(self.fx, "--repo", self.fx.clone, "--plan", wt / "plano.json")
        self.assertEqual(r.returncode, 2)
        self.assertIn("não pode ficar dentro", r.stderr)
        self.assertFalse((wt / "plano.json").exists())

    def test_remoto_que_nao_responde(self):
        """Sem remoto não há prova: rc 2 e nenhum plano, em vez de um plano com dado velho."""
        self.fx.git(self.fx.clone, "config", "remote.origin.url", str(self.root / "nao-existe.git"))
        r = run(self.fx, "--repo", self.fx.clone, "--plan", self.plan)
        self.assertEqual(r.returncode, 2)
        self.assertIn("não respondeu", r.stderr)
        self.assertFalse(self.plan.exists())

    def test_nome_com_acento(self):
        """O nome com acento e barra chega intacto ao plano (Review Focus 1)."""
        self.fx.branch("feat/ação"); self.fx.merge("feat/ação", pr=False)
        r = run(self.fx, "--repo", self.fx.clone, "--plan", self.plan)
        self.assertEqual(r.returncode, 0, r.stderr)
        names = {i["name"] for i in json.loads(self.plan.read_text(encoding="utf-8"))["items"]}
        self.assertIn("feat/ação", names)
        self.assertIn("feat/ação", r.stdout)

    def test_symlink_ignorado_sai_marcado_como_link(self):
        """O .venv do worktree aponta para o do checkout: o relatório diz que só o link sai."""
        self.fx.branch("feat/w"); self.fx.merge("feat/w", pr=False)
        wt = self.fx.worktree("wt-w", "feat/w")
        venv = self.root / "venv-do-checkout"
        venv.mkdir()
        with open(self.fx.clone / ".git" / "info" / "exclude", "a", encoding="utf-8") as f:
            f.write(".venv\n")
        (wt / ".venv").symlink_to(venv)
        r = run(self.fx, "--repo", self.fx.clone, "--plan", self.plan)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn(f".venv → {venv} (link: só o link sai)", r.stdout)
        item = next(i for i in json.loads(self.plan.read_text(encoding="utf-8"))["items"]
                    if i["kind"] == "worktree")
        self.assertEqual(item["decision"], "delete")
        self.assertEqual(item["links"], {".venv": str(venv)})

    @unittest.skipUnless(os.path.isdir("/proc/self"), "sem /proc: a varredura de processos não roda")
    def test_worktree_com_processo_dentro_fica(self):
        """Outra sessão aberta no worktree: ele fica, e o motivo traz o pid."""
        self.fx.branch("feat/w"); self.fx.merge("feat/w", pr=False)
        wt = self.fx.worktree("wt-w", "feat/w")
        proc = subprocess.Popen(["sleep", "60"], cwd=wt)
        try:
            r = run(self.fx, "--repo", self.fx.clone, "--plan", self.plan)
        finally:
            proc.kill()
            proc.wait()
        self.assertEqual(r.returncode, 0, r.stderr)
        item = next(i for i in json.loads(self.plan.read_text(encoding="utf-8"))["items"]
                    if i["kind"] == "worktree")
        self.assertEqual(item["decision"], "keep")
        self.assertIn(f"pid {proc.pid}", item["reason"])
        self.assertIn("diretório atual neste worktree", item["reason"])


class CabecalhoTest(unittest.TestCase):
    """O que o relatório não conseguiu conferir aparece no cabeçalho, em vez de sumir calado."""

    def test_sem_proc_o_cabecalho_avisa(self):
        sys.path.insert(0, str(HERE.parent / "scripts"))
        import analyze  # noqa: E402
        plan = {"repo": "/r", "remote": "origin", "default_branch": "main", "gh_available": True,
                "gh_reason": "", "procs_checked": False, "items": [],
                "disk": {"git_kb": 0, "worktrees_kb": 0}}
        self.assertIn("processos nos worktrees: não conferido (sem /proc)", analyze.render(plan))
        self.assertNotIn("processos nos worktrees", analyze.render(dict(plan, procs_checked=True)))


class VarreduraTest(unittest.TestCase):
    """A varredura promete só ler: refs, worktrees e index ficam idênticos (Review Focus 5)."""

    def test_varredura_so_le_e_so_mostra_repos(self):
        """Dois repos, uma pasta comum e uma pasta de worktree ligado: só os repos aparecem."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repos = root / "repos"
            a = Fixture(root / "fx-a", clone=repos / "alfa")
            a.branch("feat/1"); a.merge("feat/1", pr=False)
            a.branch("feat/2"); a.merge("feat/2", pr=False)
            a.git(a.clone, "worktree", "add", "-q", str(repos / "alfa-wt"), "feat/2")   # .git arquivo
            # mtime velho num arquivo rastreado: um `git status` com optional locks reescreveria o
            # index desse worktree (o stat mudou, o conteúdo não), e a foto pegaria isso.
            old = time.time() - 3600
            os.utime(repos / "alfa-wt" / ".gitignore", (old, old))
            b = Fixture(root / "fx-b", clone=repos / "beta")
            (repos / "anotacoes").mkdir()
            before = {name: snapshot(repos / name) for name in ("alfa", "beta")}
            r = run(a, "--scan", repos)
            self.assertEqual(r.returncode, 0, r.stderr)
            after = {name: snapshot(repos / name) for name in ("alfa", "beta")}
            self.assertEqual(before, after)
            lines = [line for line in r.stdout.splitlines() if ":" in line and not line.startswith("Varredura")]
            self.assertEqual([line.split(":")[0] for line in lines], ["alfa", "beta"])
            self.assertIn("sairiam 2 local(is)", r.stdout)
            self.assertIn("squash não foi contado", r.stdout)


if __name__ == "__main__":
    unittest.main()
