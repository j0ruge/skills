"""Cada regra da spec § 2 num repo de fixture, classificado uma vez (é só leitura)."""
import os
import shutil
import subprocess
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


class ClassificacaoTest(unittest.TestCase):
    """Um repo com todos os casos; cada teste lê a decisão de um deles."""

    @classmethod
    def setUpClass(cls):
        """Monta os casos na ordem em que um repo real os acumularia."""
        cls.tmp = tempfile.TemporaryDirectory()
        fx = cls.fx = Fixture(Path(cls.tmp.name))
        fx.workflow("on:\n  push:\n    branches:\n      - deploy/prod\n")
        fx.branch("feat/merge-commit"); fx.merge("feat/merge-commit", pr=False)
        fx.branch("feat/squash-ok"); fx.merge("feat/squash-ok", how="squash")
        fx.branch("feat/squash-moved"); fx.merge("feat/squash-moved", how="squash")
        fx.git(fx.clone, "switch", "-q", "feat/squash-moved")
        fx.commit("ajuste depois do merge"); fx.git(fx.clone, "push", "-q")
        fx.git(fx.clone, "switch", "-q", "main")
        fx.branch("staging", commits=0)
        fx.branch("feat/on-staging"); fx.merge("feat/on-staging", into="staging", how="squash")
        tip = fx.branch("feat/fork"); fx.add_pr("merged", "feat/fork", tip, cross=True)
        fx.branch("feat/never-used", commits=0)
        fx.branch("wip/local-only", push=False)
        fx.branch("feat/gone-merged"); fx.merge("feat/gone-merged", pr=False)
        fx.delete_on_remote("feat/gone-merged")
        fx.branch("feat/gone-unmerged"); fx.delete_on_remote("feat/gone-unmerged")
        fx.branch("feat/orphan-tracking"); fx.git(fx.clone, "branch", "-q", "-D", "feat/orphan-tracking")
        fx.delete_on_remote("feat/orphan-tracking")
        fx.branch("deploy/prod"); fx.merge("deploy/prod", pr=False)
        fx.branch("keep/me"); fx.merge("keep/me", pr=False)
        fx.git(fx.clone, "config", "--add", "housekeeping.protect", "keep/*")
        tip = fx.branch("feat/open-head"); fx.merge("feat/open-head", pr=False)
        fx.add_pr("open", "feat/open-head", tip)
        fx.branch("feat/open-base"); fx.merge("feat/open-base", pr=False)
        fx.add_pr("open", "feat/outra", "0" * 40, base="feat/open-base")
        fx.branch("feat/wt-clean"); fx.merge("feat/wt-clean", pr=False)
        wt = fx.worktree("wt-clean", "feat/wt-clean")
        (wt / "node_modules" / "pkg").mkdir(parents=True)
        (wt / "node_modules" / "pkg" / "index.js").write_text("x" * 8192)
        (wt / ".env.local").write_text("SEGREDO=nao-imprima\n")
        fx.branch("feat/wt-dirty"); fx.merge("feat/wt-dirty", pr=False)
        (fx.worktree("wt-dirty", "feat/wt-dirty") / "rascunho.txt").write_text("wip")
        fx.branch("feat/wt-locked"); fx.merge("feat/wt-locked", pr=False)
        fx.worktree("wt-locked", "feat/wt-locked")
        fx.git(fx.clone, "worktree", "lock", str(fx.base / "wt-locked"))
        fx.branch("feat/wt-gone"); fx.merge("feat/wt-gone", pr=False)
        shutil.rmtree(fx.worktree("wt-gone", "feat/wt-gone"))
        fx.worktree("wt-detached", detach="main~1")
        fx.branch("wip/wt-unmerged"); fx.worktree("wt-unmerged", "wip/wt-unmerged")
        with mock.patch.dict(os.environ, fx.env()):
            cls.facts = hk.load_facts(fx.clone)
            cls.items = hk.classify(cls.facts)

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

    def assertDecision(self, kind, name, decision, evidence=None, reason=None):
        """Decisão, evidência e um trecho do motivo de um item."""
        i = self.item(kind, name)
        self.assertEqual(i.decision, decision, i.reason)
        if evidence is not None:
            self.assertEqual(i.evidence, evidence)
        if reason is not None:
            self.assertIn(reason, i.reason)

    def test_merge_commit_sai_local_e_remota(self):
        """O merge commit põe a ponta fora da cadeia de primeiro pai: a prova não precisa de PR."""
        self.assertDecision("local-branch", "feat/merge-commit", "delete", "merge-commit")
        self.assertDecision("remote-branch", "feat/merge-commit", "delete", "merge-commit")

    def test_squash_com_a_ponta_do_pr_sai(self):
        """No squash a ancestralidade falha; o PR mergeado na main com a mesma ponta prova."""
        i = self.item("remote-branch", "feat/squash-ok")
        self.assertEqual(i.decision, "delete", i.reason)
        self.assertTrue(i.evidence.startswith("pr#"), i.evidence)

    def test_squash_com_commit_depois_do_merge_nao_provado(self):
        """O commit depois do merge não está na main: apagar o perderia."""
        for kind in ("remote-branch", "local-branch"):
            self.assertDecision(kind, "feat/squash-moved", "unproven", reason="1 commit(s) depois")

    def test_squash_na_staging_nao_provado(self):
        """Só a default conta como integração (decisão do usuário no brainstorming)."""
        self.assertDecision("remote-branch", "feat/on-staging", "unproven",
                            reason="na staging, não na main")

    def test_pr_de_fork_nao_prova(self):
        """Um fork pode ter branch com o mesmo nome; o PR dele não diz nada sobre a nossa."""
        self.assertDecision("remote-branch", "feat/fork", "keep", reason="não mergeada")

    def test_ponta_que_e_commit_da_main_sem_pr_nao_provado(self):
        """Branch criada e nunca usada é indistinguível de fast-forward sem PR: fica."""
        self.assertDecision("remote-branch", "feat/never-used", "unproven", reason="nunca usada")
        self.assertDecision("local-branch", "feat/never-used", "unproven", reason="nunca usada")

    def test_branch_so_local_fica(self):
        """Sem upstream e sem merge, é trabalho que só existe aqui."""
        self.assertDecision("local-branch", "wip/local-only", "keep", reason="trabalho só local")

    def test_upstream_que_sumiu(self):
        """O auto-delete do GitHub apaga a remota: a local mergeada sai, a não mergeada fica."""
        self.assertDecision("local-branch", "feat/gone-merged", "delete", "merge-commit")
        self.assertDecision("local-branch", "feat/gone-unmerged", "keep",
                            reason="os commits só existem aqui")
        self.assertNotIn(("remote-branch", "feat/gone-merged"),
                         {(i.kind, i.name) for i in self.items})

    def test_refs_remote_tracking_velhas(self):
        """A velha sai quando a ponta está salva; a que é o único ponteiro fica."""
        self.assertDecision("remote-tracking", "feat/gone-merged", "delete")
        self.assertDecision("remote-tracking", "feat/gone-unmerged", "delete")
        self.assertDecision("remote-tracking", "feat/orphan-tracking", "unproven",
                            reason="único ponteiro")

    def test_protecoes(self):
        """Cada proteção da spec § 2.3 vence a prova de merge."""
        for name, part in (("main", "branch default"), ("staging", "vida longa"),
                           ("deploy/prod", "workflow"), ("keep/me", "housekeeping.protect"),
                           ("feat/open-head", "head do PR aberto"),
                           ("feat/open-base", "base do PR aberto")):
            with self.subTest(name=name):
                self.assertDecision("remote-branch", name, "keep", reason=part)
        self.assertDecision("local-branch", "main", "keep", reason="worktree principal")

    def test_worktree_limpo_e_mergeado_sai_com_os_ignorados(self):
        """O remove apaga os ignorados com rc 0 (medido): o plano os lista pelo nome."""
        i = self.item("worktree", "wt-clean")
        self.assertEqual((i.decision, i.action), ("delete", "remove"), i.reason)
        self.assertIn(".env.local", i.ignored)
        self.assertIn("node_modules/", i.ignored)
        self.assertGreater(i.kb, 0)
        self.assertDecision("local-branch", "feat/wt-clean", "delete")

    def test_worktree_sujo_fica_e_segura_a_branch(self):
        """Arquivo não rastreado é trabalho: o worktree fica, e a branch dele também."""
        self.assertDecision("worktree", "wt-dirty", "keep", reason="não rastreado")
        self.assertDecision("local-branch", "feat/wt-dirty", "keep", reason="em uso no worktree")

    def test_worktree_travado_fica(self):
        """`git worktree lock` é o usuário dizendo que esse fica."""
        self.assertDecision("worktree", "wt-locked", "keep", reason="travado")

    def test_worktree_sem_pasta_sai_por_prune(self):
        """A pasta sumiu: sobra só o registro, e a branch sai depois do prune."""
        i = self.item("worktree", "wt-gone")
        self.assertEqual((i.decision, i.action), ("delete", "prune"), i.reason)
        self.assertDecision("local-branch", "feat/wt-gone", "delete")

    def test_worktree_destacado_dentro_da_main_sai(self):
        """Sem branch, o commit segue alcançável pela main: não há o que perder."""
        i = self.item("worktree", "wt-detached")
        self.assertEqual((i.decision, i.action), ("delete", "remove"), i.reason)

    def test_worktree_em_branch_que_fica_fica(self):
        """O worktree segue a decisão da branch dele."""
        self.assertDecision("worktree", "wt-unmerged", "keep", reason="que fica")

    def test_o_conteudo_do_env_nunca_e_lido(self):
        """O plano tem o nome do .env.local, nunca o que está dentro."""
        self.assertNotIn("nao-imprima", repr(self.items))


class ProvaSemGhTest(unittest.TestCase):
    """Sem gh, o merge commit ainda prova; o squash não."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.fx = Fixture(Path(self.tmp.name))
        self.fx.branch("feat/a"); self.fx.merge("feat/a", how="squash")
        self.fx.branch("feat/b"); self.fx.merge("feat/b", pr=False)

    def tearDown(self):
        self.tmp.cleanup()

    def classify(self, env, kind="remote-branch"):
        """Classifica com o ambiente dado; devolve (facts, {nome: item}) do tipo pedido."""
        with mock.patch.dict(os.environ, env):
            facts = hk.load_facts(self.fx.clone)
            items = hk.classify(facts)
        return facts, {i.name: i for i in items if i.kind == kind}

    def test_gh_ausente(self):
        """gh fora do PATH: o motivo diz isso, e o squash vira não provado."""
        facts, items = self.classify(self.fx.env(gh=False))
        self.assertFalse(facts.gh_available)
        self.assertEqual(facts.gh_reason, "gh não instalado")
        self.assertEqual(items["feat/a"].decision, "unproven")
        self.assertIn("squash merge não pode ser provado", items["feat/a"].reason)

    def test_sem_gh_a_remota_nao_sai_mesmo_mergeada(self):
        """Sem gh não se sabe de PR aberto, e apagar a remota fecharia o PR: só a local sai."""
        _facts, remote = self.classify(self.fx.env(gh=False))
        self.assertEqual(remote["feat/b"].decision, "unproven")
        self.assertIn("PR aberto não pode ser conferido", remote["feat/b"].reason)
        _facts, local = self.classify(self.fx.env(gh=False), kind="local-branch")
        self.assertEqual(local["feat/b"].decision, "delete")

    def test_gh_que_falha(self):
        """gh sem login ou sem rede é o mesmo que gh ausente, com o erro no motivo."""
        facts, items = self.classify(self.fx.env(FAKE_GH_FAIL="1"))
        self.assertFalse(facts.gh_available)
        self.assertTrue(facts.gh_reason.startswith("gh falhou"), facts.gh_reason)
        self.assertEqual(items["feat/a"].decision, "unproven")


class WorktreeAtualTest(unittest.TestCase):
    """Rodar a análise de dentro de um worktree ligado o protege (Review Focus 2)."""

    def test_worktree_atual_e_a_branch_dele_ficam(self):
        """Apagar o worktree onde o usuário está tiraria o chão do shell dele."""
        with tempfile.TemporaryDirectory() as tmp:
            fx = Fixture(Path(tmp))
            fx.branch("feat/x"); fx.merge("feat/x", pr=False)
            wt = fx.worktree("wt-x", "feat/x")
            with mock.patch.dict(os.environ, fx.env()):
                items = hk.classify(hk.load_facts(wt))
            by = {(i.kind, i.name): i for i in items}
            wt_item = next(i for i in items if i.kind == "worktree")
            self.assertEqual(wt_item.decision, "keep")
            self.assertIn("onde a análise roda", wt_item.reason)
            self.assertEqual(by[("local-branch", "feat/x")].decision, "keep")
            self.assertIn("worktree atual", by[("local-branch", "feat/x")].reason)


class ConfigHostilTest(unittest.TestCase):
    """A config legítima do usuário não pode mudar o que sai: a fixture isola a global, e por isso
    estes testes põem a config no próprio clone (achados C1 e C2 da revisão final)."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.fx = Fixture(Path(self.tmp.name))

    def tearDown(self):
        self.tmp.cleanup()

    def classify(self, repo=None):
        """Classifica no ambiente da fixture; devolve {(tipo, nome): item}."""
        with mock.patch.dict(os.environ, self.fx.env()):
            return {(i.kind, i.name): i for i in hk.classify(hk.load_facts(repo or self.fx.clone))}

    def test_fetch_prune_da_config_nao_apaga_o_unico_ponteiro_nem_tag(self):
        """Com fetch.prune e fetch.pruneTags, um fetch comum apagaria a ref órfã e a tag local."""
        fx = self.fx
        fx.branch("feat/colega")
        fx.git(fx.clone, "branch", "-q", "-D", "feat/colega")
        fx.delete_on_remote("feat/colega")
        fx.git(fx.clone, "tag", "-a", "minha-tag-local", "-m", "só aqui")
        fx.git(fx.clone, "config", "fetch.prune", "true")
        fx.git(fx.clone, "config", "fetch.pruneTags", "true")
        items = self.classify()
        self.assertEqual(items[("remote-tracking", "feat/colega")].decision, "unproven")
        refs = fx.git(fx.clone, "for-each-ref", "--format=%(refname)")
        self.assertIn("refs/remotes/origin/feat/colega", refs)
        self.assertIn("refs/tags/minha-tag-local", refs)

    def test_show_untracked_no_nao_esconde_arquivo_nem_ignorado(self):
        """Com status.showUntrackedFiles=no, o status padrão não vê o não rastreado nem lista o .env."""
        fx = self.fx
        fx.git(fx.clone, "config", "status.showUntrackedFiles", "no")
        fx.branch("feat/u"); fx.merge("feat/u", pr=False)
        wt_u = fx.worktree("wt-u", "feat/u")
        (wt_u / "rascunho-importante.md").write_text("não commitado")
        fx.branch("feat/e"); fx.merge("feat/e", pr=False)
        wt_e = fx.worktree("wt-e", "feat/e")
        (wt_e / ".env.local").write_text("X=1\n")
        items = self.classify()
        by_path = {os.path.realpath(i.name): i for (k, _n), i in items.items() if k == "worktree"}
        self.assertEqual(by_path[os.path.realpath(wt_u)].decision, "keep")
        self.assertIn(".env.local", by_path[os.path.realpath(wt_e)].ignored)


class OndeASessaoEstaTest(unittest.TestCase):
    """O worktree que contém o cwd do processo fica, mesmo com --repo apontando para outro (I3)."""

    def test_worktree_do_cwd_fica(self):
        """A sessão roda num worktree ligado e passa o checkout principal: a pasta dela não sai."""
        with tempfile.TemporaryDirectory() as tmp:
            fx = Fixture(Path(tmp))
            fx.branch("feat/s"); fx.merge("feat/s", pr=False)
            wt = fx.worktree("wt-sessao", "feat/s")
            old = os.getcwd()
            try:
                os.chdir(wt)
                with mock.patch.dict(os.environ, fx.env()):
                    items = hk.classify(hk.load_facts(fx.clone))
            finally:
                os.chdir(old)
            wt_item = next(i for i in items if i.kind == "worktree")
            self.assertEqual(wt_item.decision, "keep", wt_item.reason)
            self.assertIn("onde a sessão está", wt_item.reason)
            local = next(i for i in items if i.kind == "local-branch" and i.name == "feat/s")
            self.assertEqual(local.decision, "keep", local.reason)


class OperacaoEmAndamentoTest(unittest.TestCase):
    """Rebase parado num worktree: o worktree e a branch que está sendo rebaseada ficam (I4)."""

    def test_rebase_parado_segura_worktree_e_branch(self):
        """No `edit` o HEAD fica destacado num commit da main; apagar perderia o rebase em curso."""
        with tempfile.TemporaryDirectory() as tmp:
            fx = Fixture(Path(tmp))
            fx.branch("feat/r", commits=2); fx.merge("feat/r", pr=False)
            wt = fx.worktree("wt-r", "feat/r")
            env = {**fx.env(), "GIT_SEQUENCE_EDITOR": "sed -i 's/^pick/edit/'"}
            subprocess.run(["git", "-C", str(wt), "rebase", "-q", "-i", "HEAD~1"], env=env,
                           capture_output=True, text=True, check=True)
            with mock.patch.dict(os.environ, fx.env()):
                items = hk.classify(hk.load_facts(fx.clone))
            wt_item = next(i for i in items if i.kind == "worktree")
            self.assertEqual(wt_item.decision, "keep", wt_item.reason)
            self.assertIn("rebase", wt_item.reason)
            local = next(i for i in items if i.kind == "local-branch" and i.name == "feat/r")
            self.assertEqual(local.decision, "keep", local.reason)


class DestacadoForaDaMainTest(unittest.TestCase):
    """O HEAD destacado com commit fora de qualquer branch é a única cópia desse commit (I5)."""

    def test_destacado_com_commit_proprio_fica(self):
        """Commit feito em HEAD destacado não está em branch nenhuma: o worktree fica."""
        with tempfile.TemporaryDirectory() as tmp:
            fx = Fixture(Path(tmp))
            wt = fx.worktree("wt-solto", detach="main")
            fx.commit("experimento solto", cwd=wt)
            with mock.patch.dict(os.environ, fx.env()):
                items = hk.classify(hk.load_facts(fx.clone))
            wt_item = next(i for i in items if i.kind == "worktree")
            self.assertEqual(wt_item.decision, "keep", wt_item.reason)
            self.assertIn("fora da main", wt_item.reason)


if __name__ == "__main__":
    unittest.main()
