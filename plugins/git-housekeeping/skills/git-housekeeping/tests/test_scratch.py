"""As pastas de rascunho: scratch_scan.py prova cada entrada, scratch_apply.py só move o aprovado.

Cada regra veio de um caso medido em 2026-11-17, na limpeza de ~/.wt (CHANGELOG 0.8.0). A raiz dos
testes se chama `.wt`, como a do caso, para a citação pelo caminho (`.wt/<nome>`) valer.
"""
import json
import os
import shlex
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(HERE))
from fixture import Fixture  # noqa: E402

DIA = 86400


class ScratchCase(unittest.TestCase):
    """Uma raiz de rascunho, um repo com remoto e um HOME sem nada do usuário."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        self.fx = Fixture(self.base / "fx")
        self.root = self.base / ".wt"
        self.root.mkdir()
        self.home = self.base / "home"
        (self.home / ".claude").mkdir(parents=True)
        self.plan = self.base / "scratch" / "plano.json"

    def tearDown(self):
        self.tmp.cleanup()

    def env(self, **extra):
        """O ambiente da fixture com o HOME falso: as citações padrão vêm dele."""
        return self.fx.env(HOME=str(self.home), **extra)

    def mk(self, rel, text=None, data=None):
        """Arquivo (com texto ou bytes) ou pasta (sem os dois) dentro da raiz."""
        path = self.root / rel
        if text is None and data is None:
            path.mkdir(parents=True, exist_ok=True)
            return path
        path.parent.mkdir(parents=True, exist_ok=True)
        if data is not None:
            path.write_bytes(data)
        else:
            path.write_text(text, encoding="utf-8")
        return path

    def envelhecer(self, dias=30):
        """Tudo o que está na raiz fica com `dias` de idade (a regra do recente não o segura)."""
        t = time.time() - dias * DIA
        for top, dirs, files in os.walk(self.root):
            for name in dirs + files:
                os.utime(os.path.join(top, name), (t, t), follow_symlinks=False)

    def publicar(self, rel, text):
        """Um arquivo commitado e publicado na main do repo; devolve o sha."""
        path = self.fx.clone / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        self.fx.git(self.fx.clone, "add", "-A")
        self.fx.git(self.fx.clone, "commit", "-q", "-m", f"docs: {rel}")
        self.fx.git(self.fx.clone, "push", "-q", "origin", "main")
        return self.fx.git(self.fx.clone, "rev-parse", "HEAD")

    def scan(self, *extra, rc=0):
        """Roda o scratch_scan.py e devolve (stdout, plano)."""
        r = subprocess.run([sys.executable, str(SCRIPTS / "scratch_scan.py"), "--root", str(self.root),
                            "--repo", str(self.fx.clone), "--plan", str(self.plan), *map(str, extra)],
                           capture_output=True, text=True, encoding="utf-8", env=self.env())
        self.assertEqual(r.returncode, rc, r.stdout + r.stderr)
        plan = json.loads(self.plan.read_text(encoding="utf-8")) if rc == 0 else None
        return r.stdout + r.stderr, plan

    def apply(self, *args):
        """Roda o scratch_apply.py."""
        return subprocess.run([sys.executable, str(SCRIPTS / "scratch_apply.py"), *map(str, args)],
                              capture_output=True, text=True, encoding="utf-8", env=self.env())

    def item(self, plan, name):
        """O item do plano com esse nome."""
        found = [i for i in plan["items"] if i["name"] == name]
        self.assertEqual(len(found), 1, f"{name} não está no plano: {[i['name'] for i in plan['items']]}")
        return found[0]

    def decisao(self, plan, name):
        """A decisão do item."""
        return self.item(plan, name)["decision"]


class HandoffTest(ScratchCase):
    """O handoff: o script prova o mecânico e deixa a leitura das pendências para o agente."""

    NOME = "handoff-clone-2026-01-01-1"

    def handoff(self, texto, nome=NOME):
        return self.mk(f"{nome}/HANDOFF.md", texto)

    def test_sha_na_default_espera_a_leitura(self):
        sha = self.publicar("docs/a.md", "a\n")
        self.handoff(f"# Handoff\n\nFeito em `{sha[:7]}`.\n")
        self.envelhecer()
        out, plan = self.scan()
        self.assertEqual(self.decisao(plan, self.NOME), "review", out)
        self.assertIn("SAI SE A LEITURA CONFIRMAR", out)

    def test_sha_fora_da_default_fica(self):
        tip = self.fx.branch("feat/x")
        self.handoff(f"Ponta da feat/x: {tip[:9]}.\n")
        self.envelhecer()
        _, plan = self.scan()
        item = self.item(plan, self.NOME)
        self.assertEqual(item["decision"], "unproven")
        self.assertIn(tip[:9], item["reason"])

    def test_pr_aberto_fica_e_pr_mergeado_passa(self):
        sha = self.publicar("docs/a.md", "a\n")
        self.fx.add_issue(5, "open", pr=True)
        self.fx.add_issue(6, "closed", pr=True, merged=True)
        self.handoff(f"PR #6 mergeado ({sha[:7]}); o PR #5 segue aberto.\n")
        self.handoff(f"Só o PR #6 ({sha[:7]}).\n", nome="handoff-clone-2026-01-02-1")
        self.envelhecer()
        _, plan = self.scan()
        item = self.item(plan, self.NOME)
        self.assertEqual(item["decision"], "unproven")
        self.assertIn("#5", item["reason"])
        self.assertEqual(self.decisao(plan, "handoff-clone-2026-01-02-1"), "review")

    def test_sem_origin_head_a_default_vem_do_remoto(self):
        """O HEAD local atrás não pode servir de default: o sha publicado depois dele ficaria fora."""
        self.fx.git(self.fx.clone, "switch", "-q", "-c", "velha", "main")
        sha = self.publicar("docs/a.md", "a\n")   # publica a main a partir da branch velha
        self.fx.git(self.fx.clone, "push", "-q", "origin", "HEAD:main")
        self.fx.git(self.fx.clone, "reset", "-q", "--hard", "HEAD~1")
        self.fx.git(self.fx.clone, "remote", "set-head", "origin", "-d")
        self.handoff(f"Feito em `{sha[:7]}`.\n")
        self.envelhecer()
        out, plan = self.scan()
        self.assertEqual(plan["repos"][0]["ref"], "origin/main", out)
        self.assertEqual(self.decisao(plan, self.NOME), "review")

    def test_sha_so_de_digitos_conta_e_numero_nao(self):
        """O `1719887` é um sha; o `20261117` é uma data: o que não resolve como commit é ignorado."""
        for _ in range(400):
            self.fx.git(self.fx.clone, "switch", "-q", "-c", f"x{_}", "main")
            tip = self.fx.commit("um commit que não entra na main")
            self.fx.git(self.fx.clone, "switch", "-q", "main")
            if tip[:7].isdigit():
                break
        else:
            self.skipTest("nenhum sha só de dígitos em 400 commits")
        self.fx.git(self.fx.clone, "push", "-q", "origin", f"x{_}")
        sha = self.publicar("docs/a.md", "a\n")
        self.handoff(f"Feito em `{sha[:7]}`, em 20261117. Ponta: {tip[:7]}.\n")
        self.handoff(f"Feito em `{sha[:7]}`, em 20261117.\n", nome="handoff-clone-2026-01-02-1")
        self.envelhecer()
        _, plan = self.scan()
        item = self.item(plan, self.NOME)
        self.assertEqual(item["decision"], "unproven", item)
        self.assertIn(tip[:7], item["reason"])
        self.assertEqual(self.decisao(plan, "handoff-clone-2026-01-02-1"), "review")

    def test_sem_gh_o_pr_nao_se_prova(self):
        sha = self.publicar("docs/a.md", "a\n")
        self.handoff(f"PR #6 ({sha[:7]}).\n")
        self.envelhecer()
        r = subprocess.run([sys.executable, str(SCRIPTS / "scratch_scan.py"), "--root", str(self.root),
                            "--repo", str(self.fx.clone), "--plan", str(self.plan)],
                           capture_output=True, text=True, encoding="utf-8",
                           env=self.env(FAKE_GH_FAIL="1"))
        self.assertEqual(r.returncode, 0, r.stderr)
        plan = json.loads(self.plan.read_text(encoding="utf-8"))
        self.assertEqual(self.decisao(plan, self.NOME), "unproven")

    def test_sem_sha_nem_pr_fica(self):
        self.handoff("Continuar a missão amanhã.\n")
        self.envelhecer()
        _, plan = self.scan()
        self.assertEqual(self.decisao(plan, self.NOME), "unproven")

    def test_anexo_sem_copia_fica_e_anexo_no_historico_passa(self):
        sha = self.publicar("docs/plano.md", "o plano\n")
        self.handoff(f"Ver `{sha[:7]}`.\n")
        self.mk(f"{self.NOME}/plano.md", "o plano\n")
        outro = "handoff-clone-2026-01-03-1"
        self.handoff(f"Ver `{sha[:7]}`.\n", nome=outro)
        self.mk(f"{outro}/relatorio-do-perfil.md", "só existe aqui\n")
        self.envelhecer()
        _, plan = self.scan()
        self.assertEqual(self.decisao(plan, self.NOME), "review")
        item = self.item(plan, outro)
        self.assertEqual(item["decision"], "unproven")
        self.assertIn("relatorio-do-perfil.md", item["reason"])


class CitacaoTest(ScratchCase):
    """A pasta que um arquivo vivo cita fica, e o que fica cita também (a cadeia)."""

    def test_citada_por_arquivo_do_repo_fica(self):
        self.mk("untapped-estudo/NOTAS.md", "notas\n")
        self.publicar("TODO.md", "- ler ~/.wt/untapped-estudo/NOTAS.md\n")
        self.envelhecer()
        _, plan = self.scan()
        item = self.item(plan, "untapped-estudo")
        self.assertEqual(item["decision"], "keep")
        self.assertTrue(any("TODO.md" in e for e in item["evidence"]), item)

    def test_citada_pela_memoria_fica(self):
        memoria = self.home / ".claude" / "projects" / "-x" / "memory"
        memoria.mkdir(parents=True)
        (memoria / "nota.md").write_text("o log está em ~/.wt/sdd-logs-x\n", encoding="utf-8")
        self.mk("sdd-logs-x/run.log", "log\n")
        self.envelhecer()
        _, plan = self.scan()
        self.assertEqual(self.decisao(plan, "sdd-logs-x"), "keep")

    def test_cadeia_de_handoffs(self):
        sha = self.publicar("docs/a.md", "a\n")
        a, b, c = (f"handoff-clone-2026-01-0{k}-1" for k in (1, 2, 3))
        self.mk(f"{a}/HANDOFF.md", f"Feito em `{sha[:7]}`.\n")
        self.mk(f"{b}/HANDOFF.md", f"Continua o {a}. Feito em `{sha[:7]}`.\n")
        self.mk(f"{c}/HANDOFF.md", f"Feito em `{sha[:7]}`.\n")
        self.publicar("docs/roadmap.md", f"Handoff mais recente: ~/.wt/{b}\n")
        self.envelhecer()
        _, plan = self.scan()
        self.assertEqual(self.decisao(plan, b), "keep")
        self.assertEqual(self.decisao(plan, a), "keep", "o handoff que fica cita o A")
        self.assertEqual(self.decisao(plan, c), "review")

    def test_handoff_que_e_a_unica_descricao_de_quem_fica(self):
        sha = self.publicar("docs/a.md", "a\n")
        h1, h2 = "handoff-clone-2026-01-01-1", "handoff-clone-2026-01-02-1"
        self.mk(f"{h1}/HANDOFF.md", f"Feito em `{sha[:7]}`. Os dados brutos estão em ~/.wt/estudo-x.\n")
        self.mk(f"{h2}/HANDOFF.md", f"Feito em `{sha[:7]}`. Os dados brutos estão em ~/.wt/estudo-y.\n")
        self.mk("estudo-x/dados.csv", "só aqui\n")
        self.mk("estudo-y/dados.csv", "só aqui também\n")
        self.publicar("TODO.md", "- estudar ~/.wt/estudo-y\n")
        self.envelhecer()
        _, plan = self.scan()
        self.assertEqual(self.decisao(plan, "estudo-x"), "unproven")
        item = self.item(plan, h1)
        self.assertEqual(item["decision"], "keep")
        self.assertIn("única descrição de estudo-x", item["reason"])
        self.assertEqual(self.decisao(plan, h2), "review", "o TODO.md também descreve o estudo-y")

    def test_a_citacao_que_sai_nao_segura(self):
        sha = self.publicar("docs/a.md", "a\n")
        a, b = "handoff-clone-2026-01-01-1", "handoff-clone-2026-01-02-1"
        self.mk(f"{a}/HANDOFF.md", f"Feito em `{sha[:7]}`.\n")
        self.mk(f"{b}/HANDOFF.md", f"Continua o {a}. Feito em `{sha[:7]}`.\n")
        self.envelhecer()
        _, plan = self.scan()
        self.assertEqual(self.decisao(plan, a), "review")
        self.assertEqual(self.decisao(plan, b), "review")


class SeguraTest(ScratchCase):
    """O que fica sem olhar o conteúdo: recente, processo, link, worktree, repo dado, a quarentena."""

    def test_recente_fica(self):
        self.mk("rascunho/notas.txt", "x\n")
        self.envelhecer()
        self.mk("rascunho/hoje.txt", "y\n")
        _, plan = self.scan()
        self.assertEqual(self.decisao(plan, "rascunho"), "keep")
        self.assertIn("recente", self.item(plan, "rascunho")["reason"])

    def test_janela_do_recente(self):
        self.mk("vazia")
        self.envelhecer(dias=3)
        _, plan = self.scan("--recent-days", "2")
        self.assertEqual(self.decisao(plan, "vazia"), "delete")

    @unittest.skipUnless(Path("/proc/self").is_dir(), "sem /proc")
    def test_processo_dentro_fica(self):
        pasta = self.mk("em-uso")
        self.envelhecer()
        proc = subprocess.Popen(["sleep", "30"], cwd=pasta)
        try:
            _, plan = self.scan()
        finally:
            proc.kill()
            proc.wait()
        self.assertEqual(self.decisao(plan, "em-uso"), "keep")
        self.assertIn("processo", self.item(plan, "em-uso")["reason"])

    def test_link_worktree_e_repo_dado_ficam(self):
        (self.root / "atalho").symlink_to(self.fx.clone)
        self.fx.git(self.fx.clone, "worktree", "add", "-q", "--detach", str(self.root / "wt-x"), "main")
        self.envelhecer()
        _, plan = self.scan()
        self.assertEqual(self.decisao(plan, "atalho"), "keep")
        self.assertEqual(self.decisao(plan, "wt-x"), "keep")
        self.assertIn("worktree", self.item(plan, "wt-x")["reason"])

    def test_repo_dado_dentro_da_raiz_fica(self):
        meu = self.root / "meu-repo"
        self.fx.git(self.base, "clone", "-q", str(self.fx.bare), str(meu))
        self.envelhecer()
        _, plan = self.scan("--repo", meu)
        self.assertEqual(self.decisao(plan, "meu-repo"), "keep", "o clone limpo sairia, mas é um --repo")

    def test_repo_que_nao_e_repo_recusa(self):
        self.scan("--repo", self.base, rc=2)

    def test_raiz_home_recusa(self):
        r = subprocess.run([sys.executable, str(SCRIPTS / "scratch_scan.py"), "--root", str(self.home),
                            "--plan", str(self.plan)], capture_output=True, text=True,
                           encoding="utf-8", env=self.env())
        self.assertEqual(r.returncode, 2, r.stdout)

    def test_plano_dentro_da_raiz_recusa(self):
        r = subprocess.run([sys.executable, str(SCRIPTS / "scratch_scan.py"), "--root", str(self.root),
                            "--plan", str(self.root / "plano.json")], capture_output=True, text=True,
                           encoding="utf-8", env=self.env())
        self.assertEqual(r.returncode, 2, r.stdout)
        self.assertFalse((self.root / "plano.json").exists())


class ConteudoTest(ScratchCase):
    """A pasta sai quando tudo o que guarda tem outra cópia ou se recria."""

    def test_baseline_do_retrofit(self):
        linha = "Uma linha nova e bem distintiva do retrofit que foi publicada."
        sha = self.publicar("plugins/p/SKILL.md", f"# p\n{linha}\n")
        diff = (f"diff --git a/plugins/p/SKILL.md b/plugins/p/SKILL.md\n--- a/plugins/p/SKILL.md\n"
                f"+++ b/plugins/p/SKILL.md\n@@ -1 +1,2 @@\n+{linha}\n")
        self.mk("tmp.publicado/antes.json", "[]\n")
        self.mk("tmp.publicado/diff.txt", diff)
        self.mk("tmp.extra/antes.json", "[]\n")
        self.mk("tmp.extra/diff.txt", diff)
        self.mk("tmp.extra/aplicar.py", "print(1)\n")
        self.mk("tmp.perdido/antes.json", "[]\n")
        self.mk("tmp.perdido/diff.txt", diff.replace(linha, "Esta linha nunca entrou em commit nenhum, só no diff."))
        self.mk("tmp.sem-gate/antes.json", "[]\n")
        self.envelhecer()
        _, plan = self.scan()
        self.assertEqual(self.decisao(plan, "tmp.publicado"), "delete")
        self.assertIn(sha[:7], self.item(plan, "tmp.publicado")["reason"])
        self.assertEqual(self.decisao(plan, "tmp.extra"), "unproven")
        self.assertIn("aplicar.py", self.item(plan, "tmp.extra")["reason"])
        self.assertEqual(self.decisao(plan, "tmp.perdido"), "unproven")
        self.assertEqual(self.decisao(plan, "tmp.sem-gate"), "delete")

    def test_clone_aninhado(self):
        self.mk("estudo/notas.md", "só aqui\n")
        self.fx.git(self.base, "clone", "-q", str(self.fx.bare), str(self.root / "estudo" / "demo"))
        self.fx.git(self.base, "clone", "-q", str(self.fx.bare), str(self.root / "sujo" / "demo"))
        self.mk("sujo/demo/rascunho.txt", "não commitado\n")
        self.fx.git(self.base, "clone", "-q", str(self.fx.bare), str(self.root / "so-clone"))
        self.envelhecer()
        _, plan = self.scan()
        self.assertEqual(self.decisao(plan, "estudo"), "unproven")
        self.assertEqual(self.decisao(plan, "estudo/demo"), "delete")
        self.assertEqual(self.item(plan, "estudo/demo")["kind"], "sub")
        self.assertEqual(self.decisao(plan, "sujo"), "unproven")
        self.assertIn("sujo/demo", self.item(plan, "sujo")["reason"])
        self.assertFalse(any(i["name"] == "sujo/demo" for i in plan["items"]))
        self.assertEqual(self.decisao(plan, "so-clone"), "delete")

    def test_ref_de_branch_que_sumiu_do_remoto_nao_prova(self):
        """A ref remote-tracking velha não é cópia: um `fetch --prune` a leva, e o blob vai junto."""
        self.fx.git(self.fx.clone, "switch", "-q", "-c", "feat/sumiu", "main")
        (self.fx.clone / "so-na-branch.txt").write_text("só na branch que sumiu\n", encoding="utf-8")
        self.fx.git(self.fx.clone, "add", "-A")
        self.fx.git(self.fx.clone, "commit", "-q", "-m", "wip: só na branch")
        self.fx.git(self.fx.clone, "push", "-q", "-u", "origin", "feat/sumiu")
        self.fx.git(self.fx.clone, "switch", "-q", "main")
        aninhado = self.root / "estudo" / "c"
        self.fx.git(self.base, "clone", "-q", "-b", "feat/sumiu", str(self.fx.bare), str(aninhado))
        self.fx.delete_on_remote("feat/sumiu")
        self.mk("copia.txt", "só na branch que sumiu\n")
        self.envelhecer()
        _, plan = self.scan()
        self.assertEqual(self.decisao(plan, "copia.txt"), "unproven")
        self.assertEqual(self.decisao(plan, "estudo"), "unproven")
        self.assertFalse(any(i["name"] == "estudo/c" for i in plan["items"]))

    def empurrar_por_outra_copia(self, local):
        """Outra cópia empurra um commit para a main do remoto; devolve a ponta nova, que tem de ser
        diferente da `origin/main` de `local` (a testemunha de que o remoto andou depois do fetch)."""
        outro = self.base / "outro"
        if not outro.exists():
            self.fx.git(self.base, "clone", "-q", str(self.fx.bare), str(outro))
        ponta = self.fx.commit("empurrado por outra cópia", cwd=outro)
        self.fx.git(outro, "push", "-q", "origin", "main")
        self.assertNotEqual(ponta, self.fx.git(local, "rev-parse", "origin/main"))
        return ponta

    def test_remoto_a_frente_do_fetch_avisa_e_nao_prova(self):
        """A ref cuja ponta remota o repo não tem não prova cópia, e o cabeçalho a nomeia: em
        2026-11-24 ela caiu calada, e 551 arquivos que estavam no histórico saíram sem prova."""
        self.publicar("doc.md", "publicado na main\n")
        self.mk("copia.md", "publicado na main\n")
        self.envelhecer()
        out, plan = self.scan()
        self.assertEqual(self.decisao(plan, "copia.md"), "delete", out)
        self.assertNotIn("aviso:", out)
        self.assertFalse(plan.get("sem_fetch"))
        self.empurrar_por_outra_copia(self.fx.clone)
        out, plan = self.scan()
        self.assertEqual(self.decisao(plan, "copia.md"), "unproven", out)
        self.assertIn(f"aviso: {self.fx.clone.name}: o remoto andou depois do último fetch (origin/main)", out)
        self.assertEqual(list(plan.get("sem_fetch", {}).values()), [["origin/main"]])
        self.fx.git(self.fx.clone, "fetch", "-q", "origin")
        out, plan = self.scan()
        self.assertEqual(self.decisao(plan, "copia.md"), "delete", out)
        self.assertNotIn("aviso:", out)

    def test_clone_com_o_remoto_a_frente_pede_o_fetch(self):
        """O clone cuja branch andou no remoto depois do último fetch dele não diz que ela sumiu."""
        clone = self.root / "so-clone"
        self.fx.git(self.base, "clone", "-q", str(self.fx.bare), str(clone))
        self.empurrar_por_outra_copia(clone)
        self.envelhecer()
        _, plan = self.scan()
        item = self.item(plan, "so-clone")
        self.assertEqual(item["decision"], "unproven")
        self.assertIn("o remoto andou depois do último fetch do clone (origin/main): git fetch nele",
                      item["reason"])
        self.assertNotIn("nenhuma branch", item["reason"])
        self.fx.git(clone, "fetch", "-q", "origin")
        self.envelhecer()
        _, plan = self.scan()
        self.assertEqual(self.decisao(plan, "so-clone"), "delete")

    def test_regeneraveis(self):
        self.mk("ferramenta/.venv/pyvenv.cfg", "home = /usr\n")
        self.mk("ferramenta/__pycache__/a.pyc", data=b"\0pyc")
        self.mk("misto/.venv/pyvenv.cfg", "home = /usr\n")
        self.mk("misto/notas.md", "só aqui\n")
        self.mk("saida/build/relatorio.html", "<p>só aqui</p>\n")
        self.mk("bundle/package.json", "{}\n")
        self.mk("bundle/node_modules/lib/x.js", "// do app extraído\n")
        self.mk("app/package.json", "{}\n")
        self.mk("app/package-lock.json", "{}\n")
        self.mk("app/node_modules/lib/x.js", "// o npm ci refaz\n")
        self.envelhecer()
        _, plan = self.scan()
        self.assertEqual(self.decisao(plan, "ferramenta"), "delete")
        self.assertEqual(self.decisao(plan, "misto"), "unproven")
        self.assertEqual(self.decisao(plan, "misto/.venv"), "delete")
        self.assertEqual(self.decisao(plan, "saida"), "unproven", "build/ solto não prova que se recria")
        self.assertEqual(self.decisao(plan, "app/node_modules"), "delete")
        self.assertFalse(any(i["name"] == "bundle/node_modules" for i in plan["items"]),
                         "sem lockfile, o node_modules não se recria igual")

    def test_vazia_e_arquivos_soltos(self):
        self.fx.commit("feat: a mensagem que já está no log\n\ncorpo")
        self.fx.git(self.fx.clone, "push", "-q", "origin", "main")
        self.mk("vazia")
        self.mk("vazio.txt", "")
        # Os bytes diferem do arquivo que a fixture commitou (a linha a mais): só a mensagem prova.
        self.mk("msg-commit.txt", "feat: a mensagem que já está no log\n\ncorpo  \n\n")
        self.mk("rascunho.txt", "só existe aqui\n")
        self.envelhecer()
        _, plan = self.scan()
        self.assertEqual(self.decisao(plan, "vazia"), "delete")
        self.assertEqual(self.decisao(plan, "vazio.txt"), "delete")
        self.assertEqual(self.decisao(plan, "msg-commit.txt"), "delete")
        self.assertEqual(self.decisao(plan, "rascunho.txt"), "unproven")

    def test_igual_byte_a_byte(self):
        dest = self.base / "cache-oficial"
        (dest / "Content").mkdir(parents=True)
        (dest / "Content" / "a.bin").write_bytes(b"aaa")
        (dest / "Content" / "b.bin").write_bytes(b"bbb")
        self.mk("extracao/Content/a.bin", data=b"aaa")
        self.mk("extracao/Content/b.bin", data=b"bbb")
        self.mk("extracao2/Content/a.bin", data=b"aaa")
        self.mk("extracao2/Content/b.bin", data=b"outro")
        self.envelhecer()
        _, plan = self.scan("--igual", f"extracao={dest}", "--igual", f"extracao2={dest}")
        self.assertEqual(self.decisao(plan, "extracao"), "delete")
        item = self.item(plan, "extracao2")
        self.assertEqual(item["decision"], "unproven")
        self.assertIn("1 de 2", item["reason"])


class ApplyTest(ScratchCase):
    """O apply move para a quarentena só o aprovado, e prova de novo antes."""

    def lixeira(self):
        return self.root / ".housekeeping-lixeira"

    def test_move_para_a_quarentena_e_desfaz(self):
        self.mk("vazia")
        self.mk("misto/notas.md", "só aqui\n")
        self.mk("misto/.venv/pyvenv.cfg", "x\n")
        self.envelhecer()
        self.scan()
        r = self.apply("--plan", self.plan)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertFalse((self.root / "vazia").exists())
        self.assertFalse((self.root / "misto" / ".venv").exists())
        self.assertTrue((self.root / "misto" / "notas.md").exists())
        undo = [line.removeprefix("desfazer: ") for line in r.stdout.splitlines()
                if line.startswith("desfazer: ")]
        self.assertEqual(len(undo), 2, r.stdout)
        for cmd in undo:
            subprocess.run(shlex.split(cmd), check=True)
        self.assertTrue((self.root / "vazia").is_dir())
        self.assertTrue((self.root / "misto" / ".venv" / "pyvenv.cfg").is_file())
        _, plan = self.scan()
        self.assertEqual(self.decisao(plan, ".housekeeping-lixeira"), "keep")

    def test_dry_run_nao_move(self):
        self.mk("vazia")
        self.envelhecer()
        self.scan()
        r = self.apply("--plan", self.plan, "--dry-run")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("faria: ", r.stdout)
        self.assertTrue((self.root / "vazia").is_dir())
        self.assertFalse(self.lixeira().exists())

    def test_recusa_o_que_mudou(self):
        self.mk("vazia")
        self.envelhecer()
        self.scan()
        self.mk("vazia/novo.txt", "chegou depois\n")
        r = self.apply("--plan", self.plan)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("recusado: vazia", r.stdout)
        self.assertTrue((self.root / "vazia" / "novo.txt").exists())

    def test_recusa_o_tipo_trocado(self):
        self.mk("vazia")
        self.envelhecer()
        self.scan()
        (self.root / "vazia").rmdir()
        self.mk("vazia", "agora é arquivo\n")
        r = self.apply("--plan", self.plan)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertTrue((self.root / "vazia").is_file())

    def test_recusa_citacao_nova(self):
        self.mk("vazia")
        self.envelhecer()
        self.scan()
        self.publicar("TODO.md", "a pasta ~/.wt/vazia guarda o próximo passo\n")
        r = self.apply("--plan", self.plan)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("citada", r.stdout)
        self.assertTrue((self.root / "vazia").is_dir())

    def test_recusa_o_handoff_que_virou_a_unica_descricao(self):
        sha = self.publicar("docs/a.md", "a\n")
        nome = "handoff-clone-2026-01-01-1"
        self.mk(f"{nome}/HANDOFF.md", f"Feito em `{sha[:7]}`. Os dados estão em ~/.wt/estudo-y.\n")
        self.mk("estudo-y/dados.csv", "só aqui\n")
        self.publicar("TODO.md", "- estudar ~/.wt/estudo-y\n")
        self.envelhecer()
        _, plan = self.scan()
        self.assertEqual(self.decisao(plan, nome), "review")
        self.publicar("TODO.md", "- nada\n")
        r = self.apply("--plan", self.plan, "--only", nome)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("única descrição de estudo-y", r.stdout)
        self.assertTrue((self.root / nome).is_dir())

    def test_leitura_so_com_only(self):
        sha = self.publicar("docs/a.md", "a\n")
        nome = "handoff-clone-2026-01-01-1"
        self.mk(f"{nome}/HANDOFF.md", f"Feito em `{sha[:7]}`.\n")
        self.envelhecer()
        self.scan()
        r = self.apply("--plan", self.plan)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue((self.root / nome).is_dir(), "sem --only, o handoff não sai")
        r = self.apply("--plan", self.plan, "--only", nome)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertFalse((self.root / nome).exists())

    def test_only_fora_do_plano_rc2(self):
        self.mk("vazia")
        self.mk("rascunho.txt", "só aqui\n")
        self.envelhecer()
        self.scan()
        for nome in ("nao-existe", "rascunho.txt"):
            r = self.apply("--plan", self.plan, "--only", nome)
            self.assertEqual(r.returncode, 2, r.stdout)
        self.assertTrue((self.root / "vazia").is_dir())

    def test_purge(self):
        velho = self.lixeira() / "20200101-000000"
        novo = self.lixeira() / time.strftime("%Y%m%d-%H%M%S")
        (velho / "a").mkdir(parents=True)
        (novo / "b").mkdir(parents=True)
        r = self.apply("--purge", "--root", self.root, "--older-than", "7", "--dry-run")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue(velho.exists())
        r = self.apply("--purge", "--root", self.root, "--older-than", "7")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertFalse(velho.exists())
        self.assertTrue(novo.exists())


if __name__ == "__main__":
    unittest.main()
