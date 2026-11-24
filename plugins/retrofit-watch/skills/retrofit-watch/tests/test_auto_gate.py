"""Testes das recusas da porta de publicação (rw_gate.py): as 21 guardas de `refuse` e o `hold`.

Rodar: python3 plugins/retrofit-watch/skills/retrofit-watch/tests/test_auto_gate.py
Cada teste parte de `clean_retrofit`: um retrofit limpo do `demo`, com veredito, selo e anonimato.json,
na loja fixture da Tarefa 6 (um `origin` `--bare` e um clone, sob o diretório temporário), e sabota uma
coisa. Toda chamada da porta confere depois que o `origin/main` não mudou. Nenhum teste toca a rede,
o `claude` real ou um `origin` real. Todo nome inventado se monta em tempo de execução: um literal
faria a camada 1 reprovar o próprio ramo.
"""
import json
import os
import shutil
import sys
import time
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import fixture_store as fs  # noqa: E402
import rw_auto  # noqa: E402  (o test_retrofit_watch, importado pela fixture, põe scripts/ no path)
import rw_gate as rg  # noqa: E402
import rw_store  # noqa: E402

DOC = fs.PLUGINS["demo"]
APPROVED_NOTE = "{}: substituido pela aprovacao do dono"


def invented(tag):
    """Um nome que não existe em lugar nenhum, montado aqui."""
    return "zq" + tag + "vorn"


def camel(tag):
    """Um nome com cara de identificador (CamelCase): candidato da camada 2."""
    return "Zq" + tag.capitalize() + "Vorn"


def append(path, text):
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(text)


def failing_test(name="DemoBreak"):
    return ("import unittest\n\n\n"
            f"class {name}Test(unittest.TestCase):\n"
            "    def test_breaks(self):\n"
            "        self.fail('quebrado de proposito')\n")


@fs.requires_store
class GateTest(unittest.TestCase):
    def setUp(self):
        self.w = fs.StoreWorld()
        self.w.data.mkdir(exist_ok=True)
        self.config()
        # O rebase sobre commits novos regrava o commit: o git precisa de um autor na config do HOME.
        self.identity(invented("autor"))
        self.base = self.w.origin_main()

    def tearDown(self):
        self.w.cleanup()

    # --- auxiliares ----------------------------------------------------------------------------

    def config(self, **keys):
        data = {"mode": "auto", "store": str(self.w.store), "harvest_roots": [str(self.w.tmp / "repos")]}
        data.update(keys)
        (self.w.home / ".claude/retrofit-watch.json").write_text(json.dumps(data), encoding="utf-8")

    def ctx(self):
        return self.w.ctx()

    def identity(self, name):
        email = invented("mail") + "@" + "example" + ".invalid"
        (self.w.home / ".gitconfig").write_text(f"[user]\n\tname = {name}\n\temail = {email}\n", encoding="utf-8")

    def folder(self, rid, lote="demo"):
        return rw_auto.lote_dir(self.ctx(), rid, lote)

    def read(self, rid, name, lote="demo"):
        return json.loads((self.folder(rid, lote) / name).read_text(encoding="utf-8"))

    def write(self, rid, name, data, lote="demo"):
        (self.folder(rid, lote) / name).write_text(json.dumps(data), encoding="utf-8")

    def push_origin(self, edit, message):
        """Um commit no `origin` vindo do outro clone, feito por `edit(raiz)`; atualiza `self.base`."""
        other = self.w.other
        self.w.git(other, "fetch", "-q", "origin")
        self.w.git(other, "reset", "-q", "--hard", "origin/main")
        edit(other)
        self.w.git(other, "add", "-A")
        self.w.git(other, "commit", "-q", "-m", message)
        self.w.git(other, "push", "-q", "origin", "HEAD:main")
        self.base = self.w.origin_main()

    def amend(self, wt, *args):
        self.w.git(wt, "add", "-A")
        self.w.git(wt, "commit", "-q", "--amend", *(args or ("--no-edit",)))

    def clean_retrofit(self, licoes=({},), skills=("demo",), lote="demo", edit=None, after=None, fases=(),
                       review=None, **commit):
        """(rid, worktree) de um retrofit limpo: retro, prepare, `edit(wt)` antes do commit, o commit da
        fixture, `after(wt)` depois dele, o selo e a segunda passada do revisor (`review`)."""
        rid = self.w.retro(list(licoes), [{} for _ in licoes], skills=skills)
        got = rw_store.prepare(self.ctx(), rid, lote)
        wt = Path(got["worktree"])
        if edit:
            edit(wt)
        self.w.retrofit(wt, plugin=got["plugin"], **commit)
        if after:
            after(wt)
        self.seal(rid, lote, fases, **(review or {}))
        return rid, wt

    def seal(self, rid, lote="demo", fases=(), **review):
        retrofit = rw_auto.load_retrofit(self.folder(rid, lote) / "retrofit.json")
        rw_store.seal(self.ctx(), rid, lote, [str(n) for n in retrofit["licoes"]], list(fases))
        self.review(rid, lote, **review)

    def review(self, rid, lote="demo", doubt=None, **over):
        """O anonimato.json da segunda passada: cada termo do selo `publico`, menos os que contêm
        `doubt` (`duvida`); `over` troca campos."""
        terms = self.read(rid, "termos-novos.json", lote)
        verdicts = [{"termo": t["termo"], "veredito": "duvida" if doubt and doubt in t["termo"] else "publico",
                     "nota": ""} for t in terms["termos"]]
        data = {"patch": terms["patch"], "termos": verdicts, "regra_repetida": None, "fora_das_licoes": None}
        data.update(over)
        self.write(rid, "anonimato.json", data, lote)

    def approve(self, rid, lote, *motivos):
        self.write(rid, "aprovado.json", {"id": rid, "lote": lote, "ts": int(time.time()), "motivos": list(motivos)},
                   lote)

    def refuse(self, rid, lote="demo", notes=None):
        got = rg.refuse(self.ctx(), rid, lote, [] if notes is None else notes)
        self.assertEqual(self.w.origin_main(), self.base, "a porta mexeu no origin/main")
        return got

    def assertRefuses(self, rid, motivo, lote="demo"):
        got = self.refuse(rid, lote)
        self.assertIsNotNone(got, f"esperava {motivo}")
        self.assertEqual(got[0], motivo, got)
        self.assertIsInstance(got[1], str)
        return got

    def other_lines(self, n, plugin="demo", prefix="outro"):
        """`n` linhas de lote de outros ids, na sessão do pedido."""
        for i in range(n):
            rid = f"{prefix}{i}"
            rw_auto.append_registry(self.ctx(), rw_auto._line("s1", rid, f"{rid}/{plugin}", plugin, [1], "publicado",
                                                              None, lote=plugin))

    def add_private_name(self, name):
        def edit(root):
            proc = self.w.run_script(root, "scripts/check-private-names.py", "--add", name)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.push_origin(edit, "chore: um nome na lista de privados")

    # --- o caso limpo --------------------------------------------------------------------------

    def test_clean_retrofit_passes_every_guard(self):
        rid, wt = self.clean_retrofit()
        notes = []
        # M7: sem o PYTHONDONTWRITEBYTECODE do ambiente, os testes da porta não gravam bytecode.
        with mock.patch.dict(os.environ):
            os.environ.pop("PYTHONDONTWRITEBYTECODE", None)
            self.assertIsNone(self.refuse(rid, notes=notes))
        self.assertEqual(notes, [])
        # C3: o retrofit da fixture muda a versão do metadata e passa sem a fase claim-check.
        self.assertEqual(self.read(rid, "retrofit.json")["fases"], [])
        self.assertEqual(self.w.git(wt, "status", "--porcelain", "--untracked-files=all"), "")
        self.assertEqual(list(wt.glob("plugins/**/__pycache__")) + list(wt.glob("tests/__pycache__")), [])
        self.assertEqual(rw_auto.read_registry(self.ctx()), [])

    # --- guarda 1: o lugar ---------------------------------------------------------------------

    def test_retrofit_json_cannot_point_the_gate_elsewhere(self):
        rid, wt = self.clean_retrofit()
        data = self.read(rid, "retrofit.json")
        data.update(worktree=str(self.w.store), ramo="main")
        self.write(rid, "retrofit.json", data)
        before = self.w.shared_state()
        self.assertIsNone(self.refuse(rid))
        self.assertEqual(self.w.shared_state(), before)

    def test_the_store_clone_and_main_are_refused(self):
        rid, wt = self.clean_retrofit()
        branch = rw_store.branch_name(rid, "demo")
        link = self.w.tmp / "link-para-o-clone"
        os.symlink(self.w.store, link)
        # O clone no ramo do lote, limpo: só a recusa do clone segura.
        self.w.git(self.w.store, "checkout", "-q", "--ignore-other-worktrees", branch)
        with mock.patch.object(rw_store, "worktree_path", return_value=link):
            got = self.assertRefuses(rid, "escopo")
        self.assertIn("clone da loja", got[1])
        self.w.git(self.w.store, "checkout", "-q", "main")
        rid2, wt2 = self.clean_retrofit()
        # O worktree no `main`, com o commit do lote: só a recusa do `main` segura.
        self.w.git(wt2, "checkout", "-q", "--ignore-other-worktrees", "-B", "main")
        with mock.patch.object(rw_store, "branch_name", return_value="main"):
            got = self.assertRefuses(rid2, "escopo")
        self.assertIn("main", got[1])

    def test_worktree_missing_or_not_a_root_refuses(self):
        rid, wt = self.clean_retrofit()
        with mock.patch.object(rw_store, "worktree_path", return_value=wt / "plugins"):
            got = self.assertRefuses(rid, "escopo")
        self.assertIn("raiz", got[1])
        wt.rename(wt.with_name(wt.name + "-movido"))
        got = self.assertRefuses(rid, "escopo")
        self.assertIn("nao existe", got[1])

    def test_branch_other_than_the_lote_refuses(self):
        rid, wt = self.clean_retrofit()
        self.w.git(wt, "checkout", "-q", "-b", "outro-ramo")
        got = self.assertRefuses(rid, "escopo")
        self.assertIn("outro-ramo", got[1])

    # --- guardas 2 a 4: árvore, fetch e rebase -------------------------------------------------

    def test_dirty_worktree_refuses(self):
        rid, wt = self.clean_retrofit()
        (wt / "solto.txt").write_text("sem commit\n", encoding="utf-8")
        self.assertRefuses(rid, "arvore-suja")

    def test_unreachable_origin_is_an_error_not_a_pass(self):
        rid, wt = self.clean_retrofit()
        self.w.git(wt, "remote", "set-url", "origin", str(self.w.tmp / "nao-existe.git"))
        got = self.assertRefuses(rid, "fetch")
        line = rg.hold(self.ctx(), rid, "demo", *got)
        self.assertEqual((line["resultado"], line["motivo"]), ("erro", "fetch"))
        self.assertEqual(rw_auto.read_registry(self.ctx())[-1]["resultado"], "erro")

    def test_git_of_the_gate_ignores_the_inherited_environment(self):
        # T8-fetch: o fetch nunca espera credencial no terminal. C5: nenhum git da porta obedece a um
        # GIT_DIR herdado nem lê a config de fora do HOME do Context.
        rid, wt = self.clean_retrofit()
        trap = self.w.tmp / "trap-repo"
        trap.mkdir()
        self.w.git(trap, "init", "-q")
        traps = {"GIT_DIR": str(trap / ".git"), "GIT_WORK_TREE": str(trap), "GIT_TERMINAL_PROMPT": "1"}
        with mock.patch.dict(os.environ, traps):
            with mock.patch.object(rw_store, "run", wraps=rw_store.run) as spy:
                self.assertIsNone(self.refuse(rid))
        calls = [c for c in spy.call_args_list if str(c.args[0][0]) == "git"]
        fetches = [c for c in calls if "fetch" in [str(a) for a in c.args[0]]]
        self.assertTrue(fetches)
        for call in fetches:
            self.assertEqual(call.kwargs["env"]["GIT_TERMINAL_PROMPT"], "0")
        for call in calls:
            env = call.kwargs["env"]
            with self.subTest(cmd=call.args[0]):
                self.assertNotIn("GIT_DIR", env)
                self.assertEqual(env["GIT_CONFIG_NOSYSTEM"], "1")
                self.assertTrue(env.get("HOME") == str(self.w.home) or env.get("GIT_CONFIG_GLOBAL") == os.devnull)
        self.assertEqual(self.w.git(trap, "rev-list", "--all"), "")

    def test_rebase_conflict_refuses_and_leaves_the_branch_intact(self):
        rid, wt = self.clean_retrofit()
        head = self.w.git(wt, "rev-parse", "HEAD")
        text = (self.w.store / DOC).read_text(encoding="utf-8")
        self.w.advance_origin({DOC: text + "- Outra regra no mesmo lugar.\n"}, "docs: outra regra")
        self.base = self.w.origin_main()
        self.assertRefuses(rid, "rebase")
        self.assertEqual(self.w.git(wt, "rev-parse", "HEAD"), head)
        self.assertEqual(self.w.git(wt, "branch", "--show-current"), rw_store.branch_name(rid, "demo"))
        for name in ("rebase-merge", "rebase-apply"):
            with self.subTest(name=name):
                self.assertFalse((wt / self.w.git(wt, "rev-parse", "--git-path", name)).exists())
        self.assertEqual(self.w.git(wt, "status", "--porcelain"), "")

    def test_rebase_over_unrelated_commits_passes(self):
        rid, wt = self.clean_retrofit()
        new = self.w.advance_origin({"notas.md": "Uma nota.\n"}, "docs: nota")
        self.base = new
        self.assertIsNone(self.refuse(rid))
        self.assertEqual(self.w.git(wt, "rev-parse", "HEAD^"), new)

    # --- guarda 5: escopo e as listas do portão ------------------------------------------------

    def test_two_commits_refuse(self):
        rid, wt = self.clean_retrofit()
        append(wt / "plugins/demo/CHANGELOG.md", "- Mais uma.\n")
        self.w.git(wt, "commit", "-q", "-a", "-m", "fix(demo): mais", "--trailer", "Retrofit-Mode: autonomous")
        got = self.assertRefuses(rid, "escopo")
        self.assertIn("2 commit", got[1])

    def test_path_outside_scope_refuses(self):
        # T7-I3: o commit que muda o próprio portão também é escopo, antes de a camada 1 rodar.
        for rel in ("scripts/check-private-names.py", "scripts/anonymity-gate.py", "plugins/demo2/CHANGELOG.md"):
            with self.subTest(rel=rel):
                rid, wt = self.clean_retrofit(edit=lambda wt, rel=rel: append(wt / rel, "\n# fora do escopo\n"))
                got = self.assertRefuses(rid, "escopo")
                self.assertIn(rel, got[1])

    def test_list_files_need_owner_approval(self):
        term = invented("pub")
        rid, wt = self.clean_retrofit(edit=lambda wt: append(wt / "scripts/public-names.txt", term + "\n"))
        ctx = self.ctx()
        self.assertRefuses(rid, "escopo")
        # C2: aprovação por nome sem linha `segurado` por nome.
        self.approve(rid, "demo", "nome-privado")
        self.assertRefuses(rid, "escopo")
        # C2: a linha cita o termo, mas a aprovação é só de outro motivo.
        rg.hold(ctx, rid, "demo", "nome-privado", f'nota.md:1: colheita "{term}"')
        self.approve(rid, "demo", "teto")
        self.assertRefuses(rid, "escopo")
        # C2: a aprovação é por nome, mas a última linha por nome não cita o termo novo da lista.
        self.approve(rid, "demo", "nome-privado")
        rg.hold(ctx, rid, "demo", "nome-privado", f'nota.md:1: colheita "{invented("outro")}"')
        got = self.assertRefuses(rid, "escopo")
        self.assertIn(term, got[1])
        rg.hold(ctx, rid, "demo", "termo-nao-publico", f'"{term}": duvida')
        self.assertIsNone(self.refuse(rid))

    def test_private_list_needs_a_name_hold_and_only_grows(self):
        def add_a_hash(wt):
            proc = self.w.run_script(wt, "scripts/check-private-names.py", "--add", invented("novo"))
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        rid, wt = self.clean_retrofit(edit=add_a_hash)
        self.approve(rid, "demo", "nome-privado")
        got = self.assertRefuses(rid, "escopo")
        self.assertIn("sem linha", got[1])
        rg.hold(self.ctx(), rid, "demo", "nome-privado", f'nota.md:1: colheita "{invented("x")}"')
        self.assertIsNone(self.refuse(rid))

        def drop_a_hash(wt):
            path = wt / "scripts/private-names.sha256"
            lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
            path.write_text("".join(lines[:-1]), encoding="utf-8")
        rid, wt = self.clean_retrofit(edit=drop_a_hash)
        self.approve(rid, "demo", "nome-privado")
        rg.hold(self.ctx(), rid, "demo", "nome-privado", f'nota.md:1: colheita "{invented("x")}"')
        got = self.assertRefuses(rid, "escopo")
        self.assertIn("privados", got[1])

    # --- guardas 6 e 7: o commit ---------------------------------------------------------------

    def test_co_authored_by_refuses(self):
        rid, wt = self.clean_retrofit(message="fix(demo): v1.0.1\n\nCo-Authored-By: " + "x <x" + "@" + "x.dev>")
        self.assertEqual(rg.refuse(self.ctx(), rid, "demo", [])[0], "coautoria")
        self.assertEqual(self.w.origin_main(), self.base)

    def test_commit_without_marker_refuses(self):
        rid, wt = self.clean_retrofit(trailer=None)
        self.assertRefuses(rid, "sem-marca")
        rid2, wt2 = self.clean_retrofit(trailer="Retrofit-Mode: autonomous-approved")
        self.assertRefuses(rid2, "sem-marca")
        self.approve(rid2, "demo", "teto")
        self.assertIsNone(self.refuse(rid2))
        # Dois valores do trailer, os dois permitidos: a marca tem de ser uma só (T8-r1-mut).
        rid3, wt3 = self.clean_retrofit(trailer=None, message="fix(demo): v1.0.1\n\nRetrofit-Mode: autonomous\n"
                                                              "Retrofit-Mode: autonomous")
        self.assertEqual(self.w.git(wt3, "log", "-1", "--format=%(trailers:key=Retrofit-Mode,valueonly)").split(),
                         ["autonomous", "autonomous"])
        self.assertRefuses(rid3, "sem-marca")

    # --- guardas 8 a 10: veredito e lições -----------------------------------------------------

    def test_missing_verdict_refuses(self):
        rid, wt = self.clean_retrofit()
        path = rw_auto.retro_dir(self.ctx(), rid) / "veredito.json"
        path.unlink()
        self.assertRefuses(rid, "sem-veredito")
        path.write_text("{}", encoding="utf-8")
        self.assertRefuses(rid, "sem-veredito")

    def test_approved_missing_verdict_holds_as_not_publishable(self):
        # I1: com `sem-veredito` aprovado e o veredito ainda ilegível, a porta segura com `nao-publicavel`
        # (que o dono pode aprovar), nunca levanta.
        rid, wt = self.clean_retrofit()
        path = rw_auto.retro_dir(self.ctx(), rid) / "veredito.json"
        for content in (None, "{}"):
            with self.subTest(content=content):
                if content is None:
                    path.unlink(missing_ok=True)
                else:
                    path.write_text(content, encoding="utf-8")
                self.approve(rid, "demo", "sem-veredito")
                got = self.assertRefuses(rid, "nao-publicavel")
                self.assertIn("sem-veredito", got[1])
                self.approve(rid, "demo", "sem-veredito", "nao-publicavel")
                self.assertIsNone(self.refuse(rid))
        # Sem a aprovação, o veredito ilegível continua `sem-veredito` na guarda 8.
        (self.folder(rid) / "aprovado.json").unlink()
        self.assertRefuses(rid, "sem-veredito")

    def test_lesson_outside_the_request_refuses_at_the_gate(self):
        # Uma lição de um plugin que o pedido não trouxe.
        rid, wt = self.clean_retrofit(licoes=({}, {"plugin": "demo2"}))
        data = self.read(rid, "retrofit.json")
        self.assertEqual(data["licoes"], [1])
        self.write(rid, "retrofit.json", dict(data, licoes=[1, 2]))
        self.assertRefuses(rid, "fora-do-pedido")
        # Uma lição que não está no licoes.json.
        self.write(rid, "retrofit.json", dict(data, licoes=[1, 9]))
        self.assertRefuses(rid, "fora-do-pedido")
        # O plugin posto no `exclude` depois da triagem.
        self.write(rid, "retrofit.json", data)
        self.config(exclude=["demo"])
        self.assertRefuses(rid, "fora-do-pedido")
        # Uma lição do pedido, mas de outro plugin, no retrofit.json deste lote.
        self.config()
        rid, wt = self.clean_retrofit(licoes=({}, {"plugin": "demo2"}), skills=("demo", "demo2"))
        data = self.read(rid, "retrofit.json")
        self.write(rid, "retrofit.json", dict(data, licoes=[1, 2]))
        got = self.assertRefuses(rid, "fora-do-pedido")
        self.assertIn("demo2", got[1])

    def test_lesson_not_publishable_refuses(self):
        rid, wt = self.clean_retrofit()
        path = rw_auto.retro_dir(self.ctx(), rid) / "licoes.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["licoes"][0]["resolveu"] = None
        path.write_text(json.dumps(data), encoding="utf-8")
        got = self.assertRefuses(rid, "nao-publicavel")
        self.assertIn("sem-correcao", got[1])

    def test_description_lote_is_held_as_ready_branch(self):
        lote = "demo__description"
        rid, wt = self.clean_retrofit(licoes=({"muda_description": True},), lote=lote)
        got = self.assertRefuses(rid, "muda-description", lote=lote)
        line = rg.hold(self.ctx(), rid, lote, *got)
        self.assertEqual((line["resultado"], line["motivo"], line["item"], line["lote"], line["plugin"],
                          line["licoes"], line["sessao"]),
                         ("segurado", "muda-description", f"{rid}/{lote}", lote, "demo", [1], "s1"))
        self.assertEqual((line["ramo"], line["worktree"], line["commit"]),
                         (rw_store.branch_name(rid, lote), str(wt), self.w.git(wt, "rev-parse", "HEAD")))
        self.assertEqual(rw_auto.read_registry(self.ctx())[-1], line)

    # --- guarda 11: a camada 1 -----------------------------------------------------------------

    def test_private_name_in_diff_refuses(self):
        name = invented("priv")
        self.add_private_name(name)
        rid, wt = self.clean_retrofit(edit=lambda wt: append(wt / DOC, f"- Veja o {name} antes.\n"))
        got = self.assertRefuses(rid, "nome-privado")
        self.assertIn("lista", got[1])

    def test_three_word_name_in_the_commit_message_refuses(self):
        words = [invented("um"), invented("dois"), invented("tres")]
        self.identity(" ".join(words))
        rid, wt = self.clean_retrofit(message=f"fix(demo): {words[0]} {words[1]} v1.0.1")
        self.assertRefuses(rid, "nome-privado")

    def test_session_project_name_in_diff_refuses(self):
        self.config(harvest_roots=[str(self.w.tmp / "vazio")])
        name = self.w.proj.name
        rid, wt = self.clean_retrofit(edit=lambda wt: append(wt / DOC, f"- Como no {name}.\n"))
        got = self.assertRefuses(rid, "nome-privado")
        self.assertIn(name, got[1])

    def test_layer1_and_terms_errors_are_internal_not_clean(self):
        # C1 e T8-exc: um StoreError de uma guarda é `interno` (linha `erro`), nunca uma lista vazia.
        rid, wt = self.clean_retrofit()
        for target in ("layer1", "new_terms", "patch_id"):
            with self.subTest(target=target):
                boom = rw_store.StoreError(f"{target} inutilizavel")
                with mock.patch.object(rw_store, target, side_effect=boom):
                    got = self.assertRefuses(rid, "interno")
                self.assertIn(target, got[1])
        line = rg.hold(self.ctx(), rid, "demo", *got)
        self.assertEqual((line["resultado"], line["motivo"]), ("erro", "interno"))
        # Exceção que não é StoreError sobe: a porta (Tarefa 9) a transforma em linha `erro`.
        with mock.patch.object(rw_store, "layer1", side_effect=RuntimeError("outra")):
            with self.assertRaises(RuntimeError):
                rg.refuse(self.ctx(), rid, "demo", [])
        self.assertEqual(self.w.origin_main(), self.base)

    # --- guardas 12 a 16: a segunda passada do revisor -----------------------------------------

    def test_missing_anonimato_refuses(self):
        rid, wt = self.clean_retrofit()
        path = self.folder(rid) / "anonimato.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        path.unlink()
        self.assertRefuses(rid, "sem-anonimato")
        data.pop("fora_das_licoes")
        path.write_text(json.dumps(data), encoding="utf-8")
        self.assertRefuses(rid, "sem-anonimato")

    def test_review_of_an_older_diff_refuses(self):
        rid, wt = self.clean_retrofit()
        doc = wt / DOC
        doc.write_text(doc.read_text(encoding="utf-8").replace(fs.LESSON_LINE, "- Releia antes do commit.\n"),
                       encoding="utf-8")
        self.amend(wt)
        self.assertRefuses(rid, "revisao-desatualizada")

    def test_term_in_doubt_refuses(self):
        word = camel("duvida")
        rid, wt = self.clean_retrofit(edit=lambda wt: append(wt / DOC, f"- Veja o {word}.\n"),
                                      review={"doubt": word})
        self.assertTrue([t for t in self.read(rid, "anonimato.json")["termos"] if t["veredito"] == "duvida"])
        got = self.assertRefuses(rid, "termo-nao-publico")
        self.assertIn(word, got[1])

    def test_term_only_in_the_message_refuses(self):
        # Ruling T8-M13: o patch inclui a mensagem, então o revisor aprovou o patch novo, mas listou só
        # os termos antigos; o termos-novos.json fica o velho.
        rid, wt = self.clean_retrofit()
        word = camel("mensagem")
        self.amend(wt, "-m", f"fix(demo): v1.0.1 com {word}", "--trailer", "Retrofit-Mode: autonomous")
        data = self.read(rid, "anonimato.json")
        data["patch"] = rw_store.patch_id(wt)
        self.write(rid, "anonimato.json", data)
        got = self.assertRefuses(rid, "termo-nao-publico")
        self.assertIn(word, got[1])

    def test_repeated_rule_refuses(self):
        rid, wt = self.clean_retrofit(review={"regra_repetida": "SKILL.md:12 ja diz isto"})
        got = self.assertRefuses(rid, "regra-repetida")
        self.assertIn("SKILL.md:12", got[1])

    def test_diff_beyond_the_lessons_refuses(self):
        rid, wt = self.clean_retrofit(review={"fora_das_licoes": "CHANGELOG.md:3 fala de outra coisa"})
        self.assertRefuses(rid, "diff-alem-das-licoes")

    # --- guardas 17 e 18: testes e versões -----------------------------------------------------

    def test_failing_plugin_test_refuses(self):
        rel = "plugins/demo/skills/demo/tests/test_demo.py"
        rid, wt = self.clean_retrofit(edit=lambda wt: (wt / rel).write_text(failing_test(), encoding="utf-8"))
        got = self.assertRefuses(rid, "testes")
        self.assertIn("plugins/demo/skills/demo/tests", got[1])

    def test_failing_root_test_refuses(self):
        self.push_origin(lambda root: (root / "tests/test_root.py").write_text(failing_test("Root"), encoding="utf-8"),
                         "test: raiz quebrada")
        rid, wt = self.clean_retrofit()
        got = self.assertRefuses(rid, "testes")
        self.assertTrue(got[1].startswith("tests "), got[1])

    def test_removing_the_plugin_tests_refuses(self):
        # I2: o ramo que tira uma pasta de testes do origin/main reprova, também quando sobra outra.
        skill_tests = "plugins/demo/skills/demo/tests"
        rid, wt = self.clean_retrofit(edit=lambda wt: self.w.git(wt, "rm", "-q", "-r", skill_tests))
        got = self.assertRefuses(rid, "testes")
        self.assertIn(skill_tests, got[1])
        self.push_origin(lambda root: (Path(root) / "plugins/demo/tests").mkdir() or
                         (Path(root) / "plugins/demo/tests/test_extra.py").write_text(
                             "import unittest\n\n\nclass ExtraTest(unittest.TestCase):\n"
                             "    def test_ok(self):\n        self.assertTrue(True)\n", encoding="utf-8"),
                         "test: segunda pasta de testes")
        rid, wt = self.clean_retrofit(edit=lambda wt: self.w.git(wt, "rm", "-q", "-r", "plugins/demo/tests"))
        got = self.assertRefuses(rid, "testes")
        self.assertIn("plugins/demo/tests", got[1])

    def test_plugin_without_tests_passes_with_a_note(self):
        # A nota vale só para o plugin cuja base no origin/main também não tem pasta de testes.
        self.push_origin(lambda root: shutil.rmtree(Path(root) / "plugins/demo/skills/demo/tests"),
                         "test: demo sem testes")
        rid, wt = self.clean_retrofit()
        notes = []
        self.assertIsNone(self.refuse(rid, notes=notes))
        self.assertEqual(notes, ["testes: plugin demo sem pasta de testes"])

    def test_version_out_of_sync_refuses(self):
        def back_to_old(wt):
            path = wt / ".claude-plugin/marketplace.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            for entry in data["plugins"]:
                if entry["name"] == "demo":
                    entry["version"] = fs.VERSION
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            self.amend(wt)
        rid, wt = self.clean_retrofit(after=back_to_old)
        self.assertRefuses(rid, "validate-versions")

    # --- guarda 19: a auditoria ----------------------------------------------------------------

    @staticmethod
    def extra_field(root):
        doc = Path(root) / DOC
        doc.write_text(doc.read_text(encoding="utf-8").replace("license: MIT\n", "license: MIT\ncampo-extra: x\n", 1),
                       encoding="utf-8")

    def test_new_audit_finding_refuses(self):
        rid, wt = self.clean_retrofit(edit=self.extra_field)
        got = self.assertRefuses(rid, "auditoria")
        self.assertIn("NOVO", got[1])

    def test_old_audit_debt_does_not_refuse(self):
        self.push_origin(self.extra_field, "chore: campo fora da spec")
        rid, wt = self.clean_retrofit()
        self.assertIsNone(self.refuse(rid))

    def test_missing_auditor_refuses(self):
        stub = ("import json\nprint(json.dumps({'skills': [{'findings': [], 'claims': []}]}))\n"
                "raise SystemExit(2)\n")
        cases = {
            "auditor ausente": (lambda root: (Path(root) / fs.AUDITOR).unlink(), "ausente"),
            "comparador ausente": (lambda root: (Path(root) / fs.AUDIT_GATE).unlink(), "ausente"),
            "auditor rc 2": (lambda root: (Path(root) / fs.AUDITOR).write_text(stub, encoding="utf-8"), "saiu 2"),
            "auditor sem JSON": (lambda root: (Path(root) / fs.AUDITOR).write_text("print('nada')\n", encoding="utf-8"),
                                 "fora do formato"),
            "comparador rc 1": (lambda root: (Path(root) / fs.AUDIT_GATE).write_text("raise SystemExit(1)\n",
                                                                                     encoding="utf-8"), "saiu 1"),
        }

        def restore(root):
            for rel in (fs.AUDITOR, fs.AUDIT_GATE):
                shutil.copy2(fs.STORE_ROOT / rel, Path(root) / rel)

        for what, (edit, needle) in cases.items():
            with self.subTest(what):
                self.push_origin(edit, f"chore: {what}")
                rid, wt = self.clean_retrofit()
                got = self.assertRefuses(rid, "auditoria")
                self.assertIn(needle, got[1])
                self.push_origin(restore, "chore: auditor de volta")

    def test_plugin_without_skill_md_skips_the_audit_with_a_note(self):
        rid, wt = self.clean_retrofit(skills=("demo-cmd",), lote="demo-cmd")
        notes = []
        self.assertIsNone(self.refuse(rid, "demo-cmd", notes))
        self.assertEqual(notes, ["auditoria: plugin sem SKILL.md"])

    def test_missing_audit_phase_refuses(self):
        refs = "plugins/demo/skills/demo/references/nota.md"

        def claim(wt):
            append(wt / DOC, "- Medido em 2026-11-01: 120 ms por chamada.\n")

        def reference(wt):
            (wt / refs).parent.mkdir(parents=True, exist_ok=True)
            (wt / refs).write_text("# Nota\n\nUma nota de apoio.\n", encoding="utf-8")
            append(wt / DOC, "- Detalhes em `references/nota.md`.\n")

        def hidden_claim(wt):
            # T8-r1-text: um `.gitattributes` do ramo com `binary` não esconde a linha nova do diff.
            (wt / "plugins/demo/skills/demo/.gitattributes").write_text("*.md binary\n", encoding="utf-8")
            claim(wt)

        for phase, edit, after in (("claim-check", claim, None), ("claim-check", hidden_claim, None),
                                   ("self-containment", reference, None),
                                   ("refactoring", None, lambda wt: self.size_doc(wt, lines=rg.SKILL_MAX_LINES + 1)),
                                   ("refactoring", None, lambda wt: self.size_doc(wt, chars=rg.SKILL_MAX_CHARS + 1))):
            with self.subTest(phase=phase, edit=edit, after=after):
                rid, wt = self.clean_retrofit(edit=edit, after=after)
                got = self.assertRefuses(rid, "fase-de-auditoria")
                self.assertTrue(got[1].startswith(phase + ":"), got[1])
                self.seal(rid, fases=[phase])
                self.assertIsNone(self.refuse(rid))

    def size_doc(self, wt, lines=None, chars=None):
        """Leva o SKILL.md do commit a exatamente `lines` linhas ou `chars` caracteres (com menos de
        SKILL_MAX_LINES linhas) e emenda o commit."""
        doc = wt / DOC
        text = doc.read_text(encoding="utf-8")
        if lines is not None:
            text += "- Linha de preenchimento.\n" * (lines - len(text.splitlines()))
        else:
            filler = "- " + "texto de preenchimento sem numero " * 3 + "\n"
            while len(text) + len(filler) < chars - 10:
                text += filler
            rest = chars - len(text)
            text += "- " + "x" * (rest - 3) + "\n"
        doc.write_text(text, encoding="utf-8")
        self.amend(wt)
        text = doc.read_text(encoding="utf-8")
        if lines is not None:
            self.assertEqual(len(text.splitlines()), lines)
        else:
            self.assertEqual(len(text), chars)
            self.assertLess(len(text.splitlines()), rg.SKILL_MAX_LINES)

    def test_skill_md_at_the_cap_needs_no_refactoring(self):
        # S1: no teto (400 linhas, 16000 caracteres) a fase não se exige; uma a mais, sim (o teste acima).
        for size in ({"lines": rg.SKILL_MAX_LINES}, {"chars": rg.SKILL_MAX_CHARS}):
            with self.subTest(size=size):
                rid, wt = self.clean_retrofit(after=lambda wt, size=size: self.size_doc(wt, **size))
                self.assertIsNone(self.refuse(rid))

    def test_skill_md_already_over_the_cap_needs_no_refactoring(self):
        # C3: o gatilho é cruzar o teto; o SKILL.md que já passava dele no origin/main e cresce não exige a fase.
        self.push_origin(lambda root: append(Path(root) / DOC, "- Linha de preenchimento.\n" * (rg.SKILL_MAX_LINES + 10)),
                         "docs: SKILL.md grande")
        rid, wt = self.clean_retrofit()
        self.assertGreater(len((wt / DOC).read_text(encoding="utf-8").splitlines()), rg.SKILL_MAX_LINES)
        self.assertIsNone(self.refuse(rid))

    # --- guardas 20 e 21: teto e auto-dry ------------------------------------------------------

    def test_caps_refuse(self):
        rid, wt = self.clean_retrofit()
        registry = self.w.data / rw_auto.REGISTRY
        # As linhas deste lote não contam: uma do demo de outro id e uma deste.
        self.other_lines(1)
        rg.hold(self.ctx(), rid, "demo", "testes", "antes")
        self.assertIsNone(self.refuse(rid))
        registry.unlink()
        self.other_lines(2)
        got = self.assertRefuses(rid, "teto")
        self.assertIn("2 de 2 do plugin", got[1])
        registry.unlink()
        for plugin in ("demo2", "demo-cmd", "outro-plugin"):
            self.other_lines(1, plugin=plugin, prefix=f"id-{plugin}-")
        got = self.assertRefuses(rid, "teto")
        self.assertIn("3 de 3 da sessao", got[1])
        self.config(auto_limits={"per_skill": 3, "per_session": 4})
        self.assertIsNone(self.refuse(rid))

    def test_auto_dry_refuses_last(self):
        self.config(mode="auto-dry")
        rid, wt = self.clean_retrofit()
        self.assertRefuses(rid, "auto-dry")
        rel = "plugins/demo/skills/demo/tests/test_demo.py"
        rid2, wt2 = self.clean_retrofit(edit=lambda wt: (wt / rel).write_text(failing_test(), encoding="utf-8"))
        self.assertRefuses(rid2, "testes")

    # --- a aprovação do dono -------------------------------------------------------------------

    def test_approval_replaces_only_the_reasons_it_lists(self):
        lote = "demo__description"
        rel = "plugins/demo/skills/demo/tests/test_demo.py"
        rid, wt = self.clean_retrofit(licoes=({"muda_description": True},), lote=lote,
                                      edit=lambda wt: (wt / rel).write_text(failing_test(), encoding="utf-8"))
        self.approve(rid, lote, "muda-description")
        self.assertRefuses(rid, "testes", lote=lote)
        rid2, wt2 = self.clean_retrofit(licoes=({"muda_description": True},), lote=lote)
        self.other_lines(2)
        self.assertRefuses(rid2, "muda-description", lote=lote)
        self.approve(rid2, lote, "muda-description", "teto")
        notes = []
        self.assertIsNone(self.refuse(rid2, lote, notes))
        self.assertEqual(notes, [APPROVED_NOTE.format("muda-description"), APPROVED_NOTE.format("teto")])

    def test_approval_never_replaces_a_name_refusal(self):
        name = invented("aprov")
        self.add_private_name(name)
        word = camel("termo")
        cases = {
            "nome-privado": {"edit": lambda wt: append(wt / DOC, f"- Veja o {name}.\n")},
            "termo-nao-publico": {"edit": lambda wt: append(wt / DOC, f"- Veja o {word}.\n"),
                                  "review": {"doubt": word}},
            "sem-anonimato": {},
        }
        for motivo, spec in cases.items():
            with self.subTest(motivo=motivo):
                rid, wt = self.clean_retrofit(**spec)
                if motivo == "sem-anonimato":
                    (self.folder(rid) / "anonimato.json").unlink()
                self.approve(rid, "demo", "nome-privado", "termo-nao-publico", "sem-anonimato")
                self.assertRefuses(rid, motivo)

    # --- retrofit.json e hold ------------------------------------------------------------------

    def test_retrofit_json_missing_or_of_another_lote_is_malformed(self):
        rid = self.w.retro([{}], [{}])
        with self.assertRaises(rw_auto.Malformed):
            rg.refuse(self.ctx(), rid, "demo", [])
        with self.assertRaises(rw_auto.Malformed):
            rg.hold(self.ctx(), rid, "demo", "testes", "")
        rid, wt = self.clean_retrofit()
        data = self.read(rid, "retrofit.json")
        for key, value in (("plugin", "demo2"), ("lote", "demo2"), ("id", "outro-id"), ("tipo", "description")):
            with self.subTest(key=key):
                self.write(rid, "retrofit.json", dict(data, **{key: value}))
                with self.assertRaises(rw_auto.Malformed):
                    rg.refuse(self.ctx(), rid, "demo", [])
        self.assertEqual(rw_auto.read_registry(self.ctx()), [])
        self.assertEqual(self.w.origin_main(), self.base)

    def test_hold_takes_only_the_gate_reasons(self):
        rid, wt = self.clean_retrofit()
        ctx = self.ctx()
        with self.assertRaises(rw_auto.Malformed):
            rg.hold(ctx, rid, "demo", "executor-falhou", "")
        with self.assertRaises(rw_auto.Malformed):
            rw_auto.hold_item(ctx, rid, f"{rid}/demo", "testes")
        line = rg.hold(ctx, rid, "demo", "testes", "um teste quebrou")
        self.assertEqual((line["resultado"], line["detalhe"]), ("segurado", "um teste quebrou"))
        self.assertEqual(set(line), set(rw_auto._line("s", "i", "x", "p", [1], "segurado", "m")) | {"ts"})
        for motivo in rg.ERRORS:
            with self.subTest(motivo=motivo):
                self.assertEqual(rg.hold(ctx, rid, "demo", motivo, "")["resultado"], "erro")
        self.assertEqual(set(rg.OVERRIDABLE) - set(rg.GATE_REASONS), set())
        self.assertEqual(set(rg.ERRORS) - set(rg.GATE_REASONS), set())
        self.assertEqual(self.w.origin_main(), self.base)


if __name__ == "__main__":
    unittest.main()
