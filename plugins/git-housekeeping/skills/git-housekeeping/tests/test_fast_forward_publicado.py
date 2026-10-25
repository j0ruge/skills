"""A branch local criada de origin/main e publicada por push HEAD:main (a receita do retrofit-skill).

Medido em 2026-10-25 (j0ruge/skills): quatro branches retrofit-*, criadas com
`git worktree add -b X <wt> origin/main` e publicadas por `push origin HEAD:main`, ficaram como
"branch default do origin": a proteção olhava o nome da upstream (main). Sem upstream, cairiam em
"nunca usada, ou fast-forward sem PR". O reflog local separa os dois casos: a publicada tem commits
feitos nela, todos na main; a nunca usada só tem a criação.
"""
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))
sys.path.insert(0, str(HERE))
import housekeeping as hk  # noqa: E402
from fixture import Fixture  # noqa: E402


class FastForwardPublicadoTest(unittest.TestCase):
    """Os quatro jeitos de uma branch local apontar para um commit da main, classificados uma vez."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        fx = cls.fx = Fixture(Path(cls.tmp.name))
        fx.git(fx.clone, "fetch", "-q", "origin")
        publicado = fx.base / "wt-publicado"
        fx.git(fx.clone, "worktree", "add", "-q", "-b", "retrofit-a", str(publicado), "origin/main")
        fx.commit("retrofit-a: a lição", cwd=publicado)
        fx.git(publicado, "push", "-q", "origin", "HEAD:main")
        fx.git(fx.clone, "fetch", "-q", "origin")
        fx.git(fx.clone, "worktree", "add", "-q", "-b", "retrofit-b", str(fx.base / "wt-novo"), "origin/main")
        sem_upstream = fx.base / "wt-sem-upstream"
        fx.git(fx.clone, "worktree", "add", "-q", "--no-track", "-b", "retrofit-c", str(sem_upstream),
               "origin/main")
        fx.commit("retrofit-c: outra lição", cwd=sem_upstream)
        fx.git(sem_upstream, "push", "-q", "origin", "HEAD:main")
        fx.git(fx.clone, "fetch", "-q", "origin")
        fx.git(fx.clone, "branch", "-q", "--track", "apelido-da-main", "origin/main")
        abandonado = fx.base / "wt-abandonado"
        fx.git(fx.clone, "worktree", "add", "-q", "-b", "retrofit-e", str(abandonado), "origin/main")
        fx.commit("retrofit-e: trabalho que não foi publicado", cwd=abandonado)
        fx.git(abandonado, "reset", "-q", "--hard", "origin/main")
        with mock.patch.dict(os.environ, fx.env()):
            cls.items = hk.classify(hk.load_facts(fx.clone))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def item(self, kind, name):
        """O item pelo tipo e nome; worktree pelo nome da pasta, comparado por realpath."""
        for i in self.items:
            if i.kind != kind:
                continue
            if kind == "worktree" and hk.same_path(i.name, self.fx.base / name):
                return i
            if kind != "worktree" and i.name == name:
                return i
        self.fail(f"sem item {kind} {name}")

    def test_publicada_com_upstream_na_main_sai(self):
        """Os commits feitos na branch (reflog) estão todos na main: sai, e o worktree limpo junto."""
        i = self.item("local-branch", "retrofit-a")
        self.assertEqual(i.decision, "delete", i.reason)
        self.assertEqual(i.evidence, "reflog")
        wt = self.item("worktree", "wt-publicado")
        self.assertEqual(wt.decision, "delete", wt.reason)

    def test_publicada_sem_upstream_sai(self):
        i = self.item("local-branch", "retrofit-c")
        self.assertEqual(i.decision, "delete", i.reason)
        self.assertEqual(i.evidence, "reflog")

    def test_nunca_usada_com_upstream_na_main_nao_e_a_default(self):
        """Sem commit feito nela, fica como nunca usada, e não como se fosse a branch default."""
        for name in ("retrofit-b", "apelido-da-main"):
            i = self.item("local-branch", name)
            self.assertEqual(i.decision, "unproven", i.reason)
            self.assertIn("nunca usada", i.reason)
            self.assertNotIn("branch default", i.reason)

    def test_commit_abandonado_no_reflog_nao_prova(self):
        """A ponta voltou para a main, mas o reflog guarda um commit que não está nela: fica."""
        i = self.item("local-branch", "retrofit-e")
        self.assertEqual(i.decision, "unproven", i.reason)

    def test_a_main_fica(self):
        self.assertEqual(self.item("local-branch", "main").decision, "keep")


if __name__ == "__main__":
    unittest.main()
