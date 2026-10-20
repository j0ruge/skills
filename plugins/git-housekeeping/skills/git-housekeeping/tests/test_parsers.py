"""Testes das funções puras do housekeeping: nenhuma toca em repo."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import housekeeping as hk  # noqa: E402


class GithubSlugTest(unittest.TestCase):
    """O owner/repo do gh sai da URL crua do remoto; o que não é GitHub não tem prova por PR."""

    def test_formas_do_github(self):
        """Toda forma comum de URL do GitHub dá o mesmo owner/repo."""
        for url in ("https://github.com/acme/demo.git", "https://github.com/acme/demo",
                    "https://github.com/acme/demo/", "https://user@github.com/acme/demo.git",
                    "git@github.com:acme/demo.git", "ssh://git@github.com/acme/demo.git"):
            with self.subTest(url=url):
                self.assertEqual(hk.github_slug(url), "acme/demo")

    def test_fora_do_github(self):
        """GitLab, caminho local e URL vazia não dão slug: a prova por PR fica ausente, e não errada."""
        for url in ("https://gitlab.com/acme/demo.git", "/srv/git/demo.git", ""):
            with self.subTest(url=url):
                self.assertEqual(hk.github_slug(url), "")


class WorkflowBranchesTest(unittest.TestCase):
    """Toda lista `branches:` protege; a heurística erra para o lado de proteger demais."""

    def test_lista_em_bloco_e_inline(self):
        """Lista em bloco, inline, com aspas e com comentário: todos os nomes saem."""
        text = (
            "on:\n"
            "  push:\n"
            "    branches:\n"
            "      - deploy/prod   # produção\n"
            "      - 'release/**'\n"
            "  pull_request:\n"
            "    branches: [main, \"staging\"]\n"
            "jobs: {}\n"
        )
        self.assertEqual(hk.parse_workflow_branches(text),
                         ["deploy/prod", "release/**", "main", "staging"])

    def test_negacao_e_outras_chaves_ficam_fora(self):
        """`!padrão`, `branches-ignore:` e `tags:` não viram proteção."""
        text = ("on:\n  push:\n    branches:\n      - main\n      - '!main-old'\n"
                "    branches-ignore: [wip/*]\n    tags: [v*]\n")
        self.assertEqual(hk.parse_workflow_branches(text), ["main"])

    def test_item_na_mesma_indentacao_da_chave(self):
        """YAML aceita a lista na mesma coluna da chave; a próxima chave encerra a lista."""
        text = "on:\n  push:\n    branches:\n    - hotfix/*\n    paths: [src/**]\n"
        self.assertEqual(hk.parse_workflow_branches(text), ["hotfix/*"])


class WorktreePorcelainTest(unittest.TestCase):
    """O `git worktree list --porcelain` vira Worktree, com o principal marcado."""

    def test_blocos(self):
        """Principal, travado, prunable e destacado saem cada um com a sua marca."""
        text = ("worktree /r\nHEAD aaa\nbranch refs/heads/main\n\n"
                "worktree /w1\nHEAD bbb\nbranch refs/heads/feat/x\nlocked\n\n"
                "worktree /w2\nHEAD ccc\nbranch refs/heads/feat/y\n"
                "prunable gitdir file points to non-existent location\n\n"
                "worktree /w3\nHEAD ddd\ndetached\n\n")
        wts = hk.parse_worktrees(text)
        self.assertEqual([w.path for w in wts], ["/r", "/w1", "/w2", "/w3"])
        self.assertTrue(wts[0].main)
        self.assertEqual(wts[0].branch, "main")
        self.assertTrue(wts[1].locked)
        self.assertTrue(wts[2].prunable)
        self.assertEqual((wts[3].branch, wts[3].head), ("", "ddd"))


class PushPorcelainTest(unittest.TestCase):
    """O resultado de cada ref do `git push --porcelain`, no formato medido no git 2.43."""

    def test_apagada_e_recusada(self):
        """`-` é apagada; `!` é recusada, com o resumo do git (stale info é a lease)."""
        out = ("To /srv/remote.git\n"
               "-\t:refs/heads/b1\t[deleted]\n"
               "!\t(delete):refs/heads/b2\t[rejected] (stale info)\n"
               "Done\n")
        self.assertEqual(hk.parse_push_porcelain(out), {
            "refs/heads/b1": (True, "[deleted]"),
            "refs/heads/b2": (False, "[rejected] (stale info)"),
        })

    def test_push_que_nem_rodou(self):
        """O pre-push que recusa não deixa linha de ref nenhuma."""
        self.assertEqual(hk.parse_push_porcelain(""), {})


if __name__ == "__main__":
    unittest.main()
