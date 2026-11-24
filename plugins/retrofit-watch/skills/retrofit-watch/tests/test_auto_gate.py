"""Testes da porta de publicação (rw_gate.py): as 25 guardas de `rg.GUARDS`, o `hold` e o `publish`.

Rodar: python3 plugins/retrofit-watch/skills/retrofit-watch/tests/test_auto_gate.py
Cada teste parte de `clean_retrofit`: um retrofit limpo do `demo`, com veredito, selo e anonimato.json,
na loja fixture da Tarefa 6 (um `origin` `--bare` e um clone, sob o diretório temporário), e sabota uma
coisa. Toda chamada de `refuse` confere depois que o `origin/main` não mudou. O `publish` recebe os
efeitos da fixture (`FixtureEffects`): o push real, só para o `origin` da fixture, e uma cópia do plugin
no cache do HOME fixture no lugar do `claude plugin update`. Nenhum teste toca a rede, o `claude` real
ou um `origin` real. Todo nome inventado se monta em tempo de execução: um literal faria a camada 1
reprovar o próprio ramo.
"""
import contextlib
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tarfile
import threading
import time
import unittest
import warnings
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import fixture_store as fs  # noqa: E402
from test_retrofit_watch import SCRIPT, HookHarness, skill_typed, tool  # noqa: E402
import retrofit_watch as rw  # noqa: E402
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


class GateHarness:
    """A loja fixture e os auxiliares dos testes da porta. Quem herda é também um TestCase."""

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


@fs.requires_store
class GateTest(GateHarness, unittest.TestCase):
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

    def test_hidden_index_flags_refuse(self):
        # Final-F2: um arquivo com `--assume-unchanged` ou `--skip-worktree` some do `status --porcelain`, e
        # a porta rodaria o portão e as listas do disco. A guarda 2 lê o `ls-files -v` e nomeia o caminho.
        rel = "scripts/public-names.txt"
        for flag in ("--assume-unchanged", "--skip-worktree"):
            with self.subTest(flag=flag):
                rid, wt = self.clean_retrofit()
                self.w.git(wt, "update-index", flag, rel)
                append(wt / rel, invented("oculto") + "\n")
                self.assertEqual(self.w.git(wt, "status", "--porcelain", "--untracked-files=all"), "")
                got = self.assertRefuses(rid, "arvore-suja")
                self.assertIn(rel, got[1])

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
            args = [str(a) for a in call.args[0]]
            # Item 11: o git que fala com o `origin` (e a sonda do `core.sshCommand`, no mesmo ambiente) lê a
            # config de sistema; todos os outros, não.
            remote = "fetch" in args or "push" in args or "core.sshCommand" in args
            with self.subTest(cmd=call.args[0]):
                self.assertNotIn("GIT_DIR", env)
                self.assertEqual(env.get("GIT_CONFIG_NOSYSTEM"), None if remote else "1")
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

    # --- guarda 5b: o que as camadas não leem (item 12) ----------------------------------------

    def test_content_the_layers_cannot_read_is_held(self):
        # C4 e C5: as camadas leem o diff como UTF-8 com `replace`. Um blob com NUL, fora do UTF-8, um link
        # ou um `.gitattributes` as cegam, e o nome colhido passaria: a porta segura com `escopo`.
        name = invented("colh")
        harvested = self.w.tmp / "repos" / name
        harvested.mkdir(parents=True)
        self.w.git(harvested, "init", "-q")
        folder = Path(DOC).parent.as_posix()
        cases = {
            "NUL": (folder + "/nota.md", ("- Linha um.\n" + chr(0) + "- Linha dois.\n").encode("utf-8")),
            "UTF-16": (folder + "/nota.md", ("- Veja o " + name + " antes.\n").encode("utf-16")),
            "Latin-1": (folder + "/nota.md", ("- Configura" + chr(0xE7) + chr(0xE3) + "o.\n").encode("latin-1")),
            "atributo": ("plugins/demo/.gitattributes", ("*.md filter=" + "x\n").encode("utf-8")),
            "link": (folder + "/atalho.md", None),
        }
        for label, (rel, body) in cases.items():
            with self.subTest(label=label):
                def edit(wt, rel=rel, body=body):
                    if body is None:
                        os.symlink("SKILL.md", wt / rel)
                    else:
                        (wt / rel).write_bytes(body)
                if body is None:
                    probe = self.w.tmp / "probe-link"
                    try:
                        os.symlink("alvo", probe)
                    except (OSError, NotImplementedError):
                        self.skipTest("sem permissao de link simbolico")
                    probe.unlink()
                rid, wt = self.clean_retrofit(edit=edit)
                got = self.assertRefuses(rid, "escopo")
                self.assertIn(rel, got[1])

    def test_attributes_under_another_spelling_are_held(self):
        # Final-F6 (C5): no NTFS e no APFS estes nomes abrem como `.gitattributes`, e chegam assim aos
        # clones da loja: a caixa, o ponto do fim e o nome curto 8.3. Qualquer um segura com `escopo`.
        cases = {
            "caixa": "plugins/demo/.Git" + "Attributes",
            "ponto": "plugins/demo/.gitattributes" + ".",
            "curto": "plugins/demo/GIT" + "ATT~1",
        }
        for label, rel in cases.items():
            with self.subTest(label=label):
                rid, wt = self.clean_retrofit(edit=lambda wt, rel=rel: (wt / rel).write_text("*.md text\n",
                                                                                          encoding="utf-8"))
                got = self.assertRefuses(rid, "escopo")
                self.assertIn(rel + " (.gitattributes)", got[1])

    def test_attributes_removed_by_the_branch_are_held(self):
        # Final-F3 (C5): o `.gitattributes` conta também quando o ramo o tira. Ele não está no `p.head`, e
        # a guarda não pode depender do `ls-tree` dele.
        rel = "plugins/demo/.gitattributes"

        def seed(root):
            (root / rel).write_text("*.md text\n", encoding="utf-8")
        self.push_origin(seed, "chore(demo): atributos")
        rid, wt = self.clean_retrofit(edit=lambda wt: (wt / rel).unlink())
        p = rg._Porta(self.ctx(), rid, "demo", [])
        self.assertIsNone(rg._g_rebase(p))
        self.assertIn(rel, p.names())
        self.assertNotIn(rel, self.w.git(wt, "ls-tree", "-r", "--name-only", "HEAD").splitlines())
        got = self.assertRefuses(rid, "escopo")
        self.assertIn(rel + " (.gitattributes)", got[1])

    def test_plain_text_passes_the_content_guard(self):
        # Um arquivo novo com acento no nome e no conteúdo, em UTF-8, e um arquivo do plugin que o lote tira:
        # o apagado não tem blob, e a guarda o pula.
        old = "plugins/demo/notas-velhas.md"

        def seed(root):
            (root / old).write_text("- Uma nota velha.\n", encoding="utf-8")
        self.push_origin(seed, "docs(demo): uma nota velha")
        rel = Path(DOC).parent.as_posix() + "/nota-t" + chr(0xE9) + "cnica.md"

        def edit(wt):
            (wt / rel).write_text("- Configura" + chr(0xE7) + chr(0xE3) + "o medida.\n", encoding="utf-8")
            (wt / old).unlink()
        rid, wt = self.clean_retrofit(edit=edit)
        p = rg._Porta(self.ctx(), rid, "demo", [])
        self.assertIsNone(rg._g_rebase(p))
        self.assertIn(rel, p.names())
        self.assertIn(old, p.names())
        self.assertIsNone(rg._g_opaque(p))
        got = self.refuse(rid)
        self.assertTrue(got is None or got[0] != "escopo", got)

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

    def test_a_piece_of_a_cited_name_is_not_cited(self):
        # Item 13: a forma do termo novo é igual à de um trecho citado, nunca um pedaço dela. A recusa cita o
        # nome inteiro; a lista de públicos ganha só a primeira metade, e a guarda 5 segura.
        name = invented("metade")
        half = name[:len(name) // 2]
        rid, wt = self.clean_retrofit(edit=lambda wt: append(wt / "scripts/public-names.txt", half + "\n"))
        rg.hold(self.ctx(), rid, "demo", "nome-privado", f'nota.md:1: colheita "{name}"')
        self.approve(rid, "demo", "nome-privado")
        got = self.assertRefuses(rid, "escopo")
        self.assertIn(half, got[1])
        self.assertIn("nao citou", got[1])

    def test_an_entry_without_letters_is_not_cited(self):
        # Item 13: um termo sem letra tem a forma vazia, e a forma vazia nunca conta como citada. A recusa cita
        # `"..."` e a lista ganha `...`: a guarda 5 segura, embora a letra seja igual.
        rid, wt = self.clean_retrofit(edit=lambda wt: append(wt / "scripts/public-names.txt", "...\n"))
        rg.hold(self.ctx(), rid, "demo", "nome-privado", 'nota.md:1: colheita "..."')
        self.approve(rid, "demo", "nome-privado")
        got = self.assertRefuses(rid, "escopo")
        self.assertIn("nao citou", got[1])
        self.assertIn("...", got[1])

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

    def test_generated_with_line_refuses(self):
        # Item 2: o CLAUDE.md da loja recusa a linha de rodapé do Claude Code; montada aqui, nunca literal.
        footer = "Gene" + "rated with [Claude " + "Code](https://claude.com/claude-code)"
        for line in (footer, footer.lower()):
            with self.subTest(line=line):
                rid, wt = self.clean_retrofit(message="fix(demo): v1.0.1\n\n" + line)
                got = self.assertRefuses(rid, "coautoria")
                self.assertIn("Gene" + "rated with", got[1])
        rid, wt = self.clean_retrofit(message="fix(demo): v1.0.1\n\nA lição foi " + "gene" + "rated with care.")
        self.assertIsNone(self.refuse(rid))

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

    # --- guarda 7b: a versão sobe --------------------------------------------------------------

    def bump_origin(self, version):
        """O `demo` do `origin` vai a `version` nos quatro lugares, sem lição nova."""
        def edit(root):
            self.w.retrofit(root, files={}, version=version, trailer=None)
        other = self.w.other
        self.w.git(other, "fetch", "-q", "origin")
        self.w.git(other, "reset", "-q", "--hard", "origin/main")
        edit(other)
        self.w.git(other, "push", "-q", "origin", "HEAD:main")
        self.base = self.w.origin_main()

    def test_same_or_lower_version_refuses(self):
        # Final-F5: com a versão de antes, o `claude plugin update` não traz nada, e o lote fica atrás.
        for version in (fs.VERSION, "0.9.0"):
            with self.subTest(version=version):
                rid, wt = self.clean_retrofit(version=version)
                got = self.assertRefuses(rid, "sem-bump")
                self.assertIn(fs.VERSION, got[1])
                # A aprovação do dono não substitui o `sem-bump`.
                self.approve(rid, "demo", "sem-bump", "teto")
                self.assertRefuses(rid, "sem-bump")

    def test_version_compares_by_number(self):
        # Final-F5: `1.10.0` sobe sobre `1.9.0`; comparados como texto, não subiria.
        self.bump_origin("1.9.0")
        rid, wt = self.clean_retrofit(version="1.10.0")
        self.assertIsNone(self.refuse(rid))

    def test_new_plugin_passes_the_bump_guard(self):
        # Final-F5: um plugin sem plugin.json no `origin/main` é novo, e não tem versão de antes.
        rid, wt = self.clean_retrofit()
        porta = rg._Porta(self.ctx(), rid, "demo", [])
        real = rg._manifest_version
        with mock.patch.object(rg, "_manifest_version",
                               side_effect=lambda p, ref: rg.ABSENT if ref == rw_store.BASE_REF else real(p, ref)):
            self.assertIsNone(rg._g_bump(porta))
        self.assertIsNone(rg._g_bump(porta))
        self.assertEqual(real(porta, rw_store.BASE_REF), fs.VERSION)

    def test_new_plugin_passes_the_bump_guard_through_show(self):
        # Item 16b, rodada 1: sem mock; o `origin/main` não tem o plugin.json do demo, e o `_show` real dá None.
        rid, wt = self.clean_retrofit()
        manifest = "plugins/demo/.claude-plugin/plugin.json"
        self.push_origin(lambda root: (Path(root) / manifest).unlink(), "chore: demo sem plugin.json")
        self.w.git(wt, "fetch", "-q", "origin")
        porta = rg._Porta(self.ctx(), rid, "demo", [])
        try:
            self.assertIsNone(rg._show(porta, rw_store.BASE_REF, manifest))
            self.assertIs(rg._manifest_version(porta, rw_store.BASE_REF), rg.ABSENT)
            self.assertIsNone(rg._g_bump(porta))
            self.assertIsNotNone(rg._show(porta, "HEAD", manifest))
        finally:
            porta.close()

    def test_git_failure_is_not_a_new_plugin(self):
        # Item 16b: um git que falha ao ler o plugin.json do origin/main não é "plugin novo": é `interno`.
        rid, wt = self.clean_retrofit()
        manifest = "plugins/demo/.claude-plugin/plugin.json"
        real = rw_store.run

        def broken(cmd, *args, **kwargs):
            words = [str(c) for c in cmd]
            if (("ls-tree" in words or "show" in words) and any(manifest in w for w in words)
                    and any(rw_store.BASE_REF in w for w in words)):
                return 128, "fatal: falha de proposito"
            return real(cmd, *args, **kwargs)

        with mock.patch.object(rw_store, "run", side_effect=broken):
            got = self.assertRefuses(rid, "interno")
        self.assertIn("128", got[1])

    # --- guardas 8 a 10: veredito e lições -----------------------------------------------------

    def test_missing_verdict_refuses(self):
        rid, wt = self.clean_retrofit()
        path = rw_auto.retro_dir(self.ctx(), rid) / "veredito.json"
        path.unlink()
        self.assertRefuses(rid, "sem-veredito")
        path.write_text("{}", encoding="utf-8")
        self.assertRefuses(rid, "sem-veredito")

    def test_gate_refuses_a_verdict_of_another_retro(self):
        # Item 7: o veredito.json de outra retro, com todo parecer `procede`, casaria as lições pelo
        # número. O `id` dele não é o da retro: a guarda 8 segura com `sem-veredito`.
        rid, wt = self.clean_retrofit()
        other = self.w.retro([{}], [{}])
        source = rw_auto.retro_dir(self.ctx(), other) / "veredito.json"
        self.assertEqual([p["procede"] for p in json.loads(source.read_text(encoding="utf-8"))["licoes"]],
                         ["procede"])
        shutil.copyfile(source, rw_auto.retro_dir(self.ctx(), rid) / "veredito.json")
        got = self.assertRefuses(rid, "sem-veredito")
        self.assertIn("outra retro", got[1])

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

    def test_auto_lote_that_changes_a_description_refuses(self):
        # Final-F6: a guarda 10b compara a `description` do origin/main e do HEAD nos lugares que o
        # check_release_sync.py confere, com ou sem a flag `muda_description` das lições.
        old = fs._description("demo")
        new = old.replace("Demo skill", "Demo skill, agora outra,")
        places = {"plugins/demo/skills/demo/SKILL.md": "SKILL.md",
                  "plugins/demo/.claude-plugin/plugin.json": "plugin.json",
                  ".claude-plugin/marketplace.json": "marketplace.json"}
        # Cada lugar sozinho, e os três juntos: assim o validate-versions.py passa, e só esta guarda segura.
        cases = [[rel] for rel in places] + [list(places)]
        for rels in cases:
            with self.subTest(rels=rels):
                def edit(wt, rels=rels):
                    for rel in rels:
                        path = wt / rel
                        text = path.read_text(encoding="utf-8")
                        self.assertEqual(text.count(old), 1, rel)
                        path.write_text(text.replace(old, new), encoding="utf-8")
                rid, wt = self.clean_retrofit(edit=edit)
                got = self.assertRefuses(rid, "muda-description")
                for rel in rels:
                    self.assertIn(places[rel], got[1])
                # O motivo continua substituível: com a aprovação, a porta passa desta guarda.
                self.approve(rid, "demo", "muda-description")
                again = self.refuse(rid)
                self.assertTrue(again is None or again[0] != "muda-description", again)

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

    def test_compound_name_written_in_prose_refuses(self):
        # Final-F4: o nome colhido com `-`, `_`, `.` ou CamelCase, escrito em prosa com espaço e em outra
        # caixa. As partes têm 3 letras: só a frase das duas pega o texto, nunca uma palavra sozinha.
        a, b = "zq" + "f", "zq" + "b"
        cases = {f"{a}-{b}": f"{a.capitalize()} {b.capitalize()}",
                 f"{a}_{b}": f"{a} {b}",
                 a.capitalize() + b.capitalize(): f"{a} {b}",
                 f"{a}.{b}": f"{a.capitalize()} {b.capitalize()}"}
        for harvested, prose in cases.items():
            with self.subTest(harvested=harvested):
                source = self.w.tmp / "privados.txt"
                source.write_text(harvested + "\n", encoding="utf-8")
                self.config(private_sources=[str(source)])
                rid, wt = self.clean_retrofit(edit=lambda wt, prose=prose: append(wt / DOC, f"- Como o {prose} faz.\n"))
                got = self.assertRefuses(rid, "nome-privado")
                self.assertIn("colheita", got[1])

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

    def test_gate_reports_a_shrunk_harvest_as_internal(self):
        # Item 8 (C8): uma fonte da colheita que existe e não lê segura o lote com `interno`, nunca uma
        # camada 1 "limpa" com menos nomes.
        rid, wt = self.clean_retrofit()
        folder = self.w.tmp / "fonte-pasta"
        folder.mkdir()
        self.config(private_sources=[str(folder)])
        got = self.assertRefuses(rid, "interno")
        self.assertIn(str(folder), got[1])

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

    def test_zero_tests_refuse(self):
        # Item 4 (C6): no Python 3.11, o `discover` que não acha teste sai 0; zero testes é `testes`.
        skill_tests = "plugins/demo/skills/demo/tests"
        rid, wt = self.clean_retrofit()
        real = rw_store.run
        for fake in ("Ran 0 tests in 0.000s\n\nOK\n", ""):
            with self.subTest(fake=fake):
                def empty(cmd, *args, **kwargs):
                    words = [str(c) for c in cmd]
                    if "discover" in words and skill_tests in words:
                        return 0, fake
                    return real(cmd, *args, **kwargs)

                with mock.patch.object(rw_store, "run", side_effect=empty):
                    got = self.assertRefuses(rid, "testes")
                self.assertIn("nenhum teste rodou", got[1])
                self.assertIn(skill_tests, got[1])

    def test_printed_ran_line_does_not_count(self):
        # Item 4, rodada 1: o `print` de um teste com a forma do resumo não decide a contagem; vale o do unittest.
        rel = "plugins/demo/skills/demo/tests/test_printed.py"
        fake = "Ran 0 " + "tests in 0.000s"
        source = (f"import unittest\n\nprint({fake!r})\n\n\n"
                  "class PrintedTest(unittest.TestCase):\n"
                  "    def test_ok(self):\n"
                  "        self.assertTrue(True)\n")
        rid, wt = self.clean_retrofit(edit=lambda wt: (wt / rel).write_text(source, encoding="utf-8"))
        self.assertIsNone(self.refuse(rid))

    def test_emptied_test_file_refuses(self):
        # Item 4: o commit que esvazia o arquivo de teste reprova em qualquer versão (3.12: rc 5; 3.11: zero).
        rel = "plugins/demo/skills/demo/tests/test_demo.py"
        rid, wt = self.clean_retrofit(edit=lambda wt: (wt / rel).write_text("import unittest\n", encoding="utf-8"))
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

        def ignored(wt):
            # A pasta sai do HEAD, mas fica no disco, ignorada por um `.gitignore` do plugin: não conta.
            self.w.git(wt, "rm", "-q", "-r", "--cached", skill_tests)
            (wt / "plugins/demo/.gitignore").write_text("skills/demo/tests/\n", encoding="utf-8")

        rid, wt = self.clean_retrofit(edit=ignored)
        self.assertTrue((wt / skill_tests).is_dir())
        self.assertEqual(self.w.git(wt, "ls-tree", "--name-only", "HEAD", "--", skill_tests).strip(), "")
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
                guards = contextlib.nullcontext()
                if edit is hidden_claim:
                    # Item 12 (C5): o `.gitattributes` já segura com `escopo` antes. Sem a guarda 5b, o
                    # `--text` da guarda da auditoria continua a defesa de trás.
                    self.assertRefuses(rid, "escopo")
                    guards = mock.patch.object(rg, "GUARDS", tuple(g for g in rg.GUARDS if g[1] is not rg._g_opaque))
                with guards:
                    got = self.assertRefuses(rid, "fase-de-auditoria")
                    self.assertTrue(got[1].startswith(phase + ":"), got[1])
                    self.seal(rid, fases=[phase])
                    self.assertIsNone(self.refuse(rid))

    def test_diff_keeps_accented_names_for_the_audit_gate(self):
        # N1: no ambiente neutro, o git põe entre aspas um caminho fora do ASCII, e o `linhas_do_diff` só lê
        # `+++ b/`. O diff da porta sai sem aspas, e as linhas novas do arquivo com acento contam.
        rel = "plugins/demo/skills/demo/nota-t" + chr(0xE9) + "cnica.md"

        def accented(wt):
            (wt / rel).write_text("# Nota\n\n- Medido em 2026-11-01: 120 ms por chamada.\n", encoding="utf-8")

        rid, wt = self.clean_retrofit(edit=accented)
        text = rg._Porta(self.ctx(), rid, "demo", []).diff("plugins/demo/skills/demo")
        self.assertIn("+++ b/" + rel, text.splitlines())
        spec = importlib.util.spec_from_file_location("audit_gate_n1", wt / rg.AUDIT_GATE)
        gate = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(gate)
        diff = self.w.data / "n1-diff.txt"
        diff.write_text(text, encoding="utf-8")
        with warnings.catch_warnings():  # o `linhas_do_diff` não fecha o arquivo que lê
            warnings.simplefilter("ignore", ResourceWarning)
            novas, _ = gate.linhas_do_diff(diff)
        self.assertEqual(novas.get(rel), {1, 2, 3})

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

    # --- item 1: a porta roda a loja de uma cópia do commit -------------------------------------
    # Cada caso planta um arquivo ignorado no worktree, que o `git status` não mostra; nenhum chega às guardas.

    def assertQuiet(self, wt):
        self.assertEqual(self.w.git(wt, "status", "--porcelain", "--untracked-files=all"), "")

    def test_planted_bytecode_does_not_blind_layer1(self):
        self.config(harvest_roots=[str(self.w.tmp / "vazio")])
        name = self.w.proj.name
        rid, wt = self.clean_retrofit(edit=lambda wt: append(wt / DOC, f"- Como no {name}.\n"))
        pyc = self.w.plant_blind_name_check(wt)
        self.assertTrue(pyc.is_file() and pyc.is_relative_to(wt), pyc)
        self.assertQuiet(wt)
        with mock.patch.dict(os.environ):
            os.environ.pop("PYTHONPYCACHEPREFIX", None)  # o executor grava o bytecode no worktree
            got = self.assertRefuses(rid, "nome-privado")
        self.assertIn(name, got[1])

    def test_planted_module_does_not_pass_the_versions_guard(self):
        def back_to_old(wt):
            path = wt / ".claude-plugin/marketplace.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            for entry in data["plugins"]:
                if entry["name"] == "demo":
                    entry["version"] = fs.VERSION
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            self.amend(wt)
        rid, wt = self.clean_retrofit(after=back_to_old)
        self.w.ignore(wt, "/scripts/json.py")
        (wt / "scripts/json.py").write_text("raise SystemExit(0)\n", encoding="utf-8")
        self.assertQuiet(wt)
        self.assertRefuses(rid, "validate-versions")

    def test_planted_module_does_not_pass_the_audit(self):
        rid, wt = self.clean_retrofit(edit=self.extra_field)
        planted = (wt / fs.AUDITOR).parent / "json.py"
        self.w.ignore(wt, "/" + planted.relative_to(wt).as_posix())
        planted.write_text("print('{\"skills\": [{\"findings\": [], \"claims\": []}]}')\nraise SystemExit(0)\n",
                           encoding="utf-8")
        self.assertQuiet(wt)
        got = self.assertRefuses(rid, "auditoria")
        self.assertIn("NOVO", got[1])

    def test_tests_come_from_the_commit(self):
        rid, wt = self.clean_retrofit()
        planted = wt / "plugins/demo/skills/demo/tests/test_ignorado.py"
        self.w.ignore(wt, "/" + planted.relative_to(wt).as_posix())
        planted.write_text(failing_test("Ignorado"), encoding="utf-8")
        self.assertQuiet(wt)
        self.assertIsNone(self.refuse(rid))

    def test_gate_passes_with_the_executor_bytecode(self):
        rid, wt = self.clean_retrofit()
        env = {k: v for k, v in self.w.env.items() if k not in ("PYTHONDONTWRITEBYTECODE", "PYTHONPYCACHEPREFIX")}
        proc = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "plugins/demo/skills/demo/tests",
                               "-p", "test_*.py"], cwd=str(wt), capture_output=True, env=env, encoding="utf-8",
                              errors="replace")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertTrue(list(wt.glob("plugins/**/__pycache__")))
        self.assertQuiet(wt)
        # A porta fica viva depois do `refuse`: sem isso, o coletor do CPython fecharia o gerador da cópia e
        # a pasta sairia sem o `finally` do `_check`.
        kept = []

        class Kept(rg._Porta):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                kept.append(self)

        with mock.patch.object(rg, "_Porta", Kept):
            self.assertIsNone(self.refuse(rid))
            self.assertEqual(len(kept), 1)
            self.assertEqual([x.name for x in self.w.data.iterdir() if x.name.startswith(".porta-")], [])

    @contextlib.contextmanager
    def owner_attributes(self, text):
        """O arquivo global de atributos do dono (`~/.config/git/attributes`) com `text`, pelo HOME e pelo
        XDG_CONFIG_HOME do ambiente: o git do ambiente neutro o leria sem o `core.attributesFile`."""
        owner = self.w.tmp / "dono"
        (owner / ".config/git").mkdir(parents=True, exist_ok=True)
        (owner / ".config/git/attributes").write_text(text, encoding="utf-8")
        with mock.patch.dict(os.environ, HOME=str(owner), XDG_CONFIG_HOME=str(owner / ".config")):
            yield

    def test_owner_attributes_do_not_drop_a_test_from_the_copy(self):
        rel = "plugins/demo/skills/demo/tests/test_quebra.py"
        rid, wt = self.clean_retrofit(edit=lambda wt: (wt / rel).write_text(failing_test("Quebra"), encoding="utf-8"))
        with self.owner_attributes("test_quebra.py export-ignore\n"):
            got = self.assertRefuses(rid, "testes")
        self.assertIn("test_quebra", got[1])

    def test_owner_attributes_do_not_drop_the_base_of_the_audit(self):
        # A dívida antiga do origin/main não reprova; sem o SKILL.md na base, ela pareceria nova.
        self.push_origin(self.extra_field, "chore: campo fora da spec")
        rid, wt = self.clean_retrofit()
        notes = []
        with self.owner_attributes("SKILL.md export-ignore\n"):
            self.assertIsNone(self.refuse(rid, notes=notes))
        self.assertEqual(notes, [])

    def test_planted_module_does_not_pass_the_audit_gate(self):
        rid, wt = self.clean_retrofit(edit=self.extra_field)
        planted = (wt / fs.AUDIT_GATE).parent / "json.py"
        self.w.ignore(wt, "/" + planted.relative_to(wt).as_posix())
        planted.write_text("raise SystemExit(0)\n", encoding="utf-8")
        self.assertQuiet(wt)
        got = self.assertRefuses(rid, "auditoria")
        self.assertIn("NOVO", got[1])

    def test_ignored_skill_does_not_reach_the_audit(self):
        rid, wt = self.clean_retrofit()
        planted = wt / "plugins/demo/skills/fantasma/SKILL.md"
        self.w.ignore(wt, "/plugins/demo/skills/fantasma/")
        planted.parent.mkdir(parents=True)
        planted.write_text((wt / DOC).read_text(encoding="utf-8").replace("license: MIT\n",
                                                                          "license: MIT\ncampo-extra: x\n", 1),
                           encoding="utf-8")
        self.assertQuiet(wt)
        notes = []
        self.assertIsNone(self.refuse(rid, notes=notes))
        self.assertEqual(notes, [])

    def test_ignored_auditor_on_disk_is_still_missing(self):
        self.push_origin(lambda root: (Path(root) / fs.AUDITOR).unlink(), "chore: auditor ausente")
        rid, wt = self.clean_retrofit()
        self.w.ignore(wt, "/" + fs.AUDITOR)
        (wt / fs.AUDITOR).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(fs.STORE_ROOT / fs.AUDITOR, wt / fs.AUDITOR)
        self.assertQuiet(wt)
        got = self.assertRefuses(rid, "auditoria")
        self.assertIn("ausente", got[1])

    def test_skill_md_read_by_the_audit_is_the_commit(self):
        # O SKILL.md do disco cresce depois que o auditor o leu: o teto se mede no do commit.
        rid, wt = self.clean_retrofit()
        real = rg._audit_json

        def growing(p, skill):
            got = real(p, skill)
            append(wt / DOC, "- Linha de preenchimento.\n" * (rg.SKILL_MAX_LINES + 10))
            return got

        with mock.patch.object(rg, "_audit_json", side_effect=growing):
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


# --- a porta que publica (Tarefa 9) --------------------------------------------------------------

def a_real_remote():
    # Montado em tempo de execução: um literal de URL faria o portão do ramo reprovar este arquivo.
    return "https" + "://" + "example" + ".invalid/" + "loja.git"


def bump_config(path):
    """Muda um byte da cópia: um `\\n` a mais no fim."""
    append(path, "\n")


class FixtureEffects(rg.Effects):
    """Os efeitos da porta na loja fixture. O `push` é o real, depois do `assert_fixture_origin`. A
    instalação copia o plugin do commit publicado (`git archive` do `main` do `origin`, nunca o worktree)
    para o cache do HOME fixture, com um `.in_use` como o do Claude Code; `after_copy(pasta)` mexe na
    cópia. Cada chamada fica em `calls`. `push` e `raises` trocam o resultado: uma tupla é devolvida,
    uma exceção é levantada."""

    def __init__(self, world, push=None, install=None, raises=None, after_copy=None, during_push=None):
        super().__init__(world.ctx())
        self.w, self.calls = world, []
        self.push_result, self.install_result, self.raises = push, install, raises
        self.after_copy, self.during_push = after_copy, during_push

    def push(self, worktree, sha):
        self.calls.append("push")
        if self.during_push:
            self.during_push(worktree)
        if isinstance(self.push_result, BaseException):
            raise self.push_result
        if self.push_result is not None:
            return self.push_result
        self.w.assert_fixture_origin(worktree)
        return super().push(worktree, sha)

    def refresh_install(self, plugin):
        self.calls.append("refresh_install")
        if self.raises is not None:
            raise self.raises
        if self.install_result is not None:
            return self.install_result
        manifest = json.loads(self.w.git(self.w.origin, "show", f"main:plugins/{plugin}/.claude-plugin/plugin.json"))
        dest = self.w.home / ".claude/plugins/cache" / rw.MARKETPLACE / plugin / manifest["version"]
        raw = subprocess.run(["git", "-C", str(self.w.origin), "archive", "--format=tar", f"main:plugins/{plugin}"],
                             capture_output=True, env=self.w.env, check=True).stdout
        dest.mkdir(parents=True, exist_ok=True)
        with tarfile.open(fileobj=io.BytesIO(raw)) as tar:
            tar.extractall(dest, filter="data")
        # Como o cache real (medido, T9-r1-inuse): uma pasta `.in_use` com um arquivo por PID.
        (dest / ".in_use").mkdir(exist_ok=True)
        (dest / ".in_use" / "1243").write_text("", encoding="utf-8")
        if self.after_copy:
            self.after_copy(dest)
        return True, "copiado"

    def cache_matches(self, ctx, worktree, plugin, versao):
        self.calls.append("cache_matches")
        return super().cache_matches(ctx, worktree, plugin, versao)


class ExitCodeTest(unittest.TestCase):
    def test_exit_code_of_each_line(self):
        cases = [({"resultado": "publicado", "instalacao": "ok"}, 0),
                 ({"resultado": "publicado", "instalacao": "nao-instalado"}, 0),
                 ({"resultado": "publicado", "instalacao": "update"}, 4),
                 ({"resultado": "publicado", "instalacao": "cache-difere"}, 4),
                 ({"resultado": "publicado", "instalacao": "pendente"}, 4),
                 ({"resultado": "segurado", "instalacao": None}, 1),
                 ({"resultado": "erro", "instalacao": None}, 3),
                 ({"resultado": "outro", "instalacao": "ok"}, 3)]
        for line, rc in cases:
            with self.subTest(line=line):
                self.assertEqual(rg.exit_code(line), rc)


@fs.requires_store
class PublishTest(GateHarness, HookHarness, unittest.TestCase):
    # --- auxiliares ----------------------------------------------------------------------------

    def effects(self, **kw):
        return FixtureEffects(self.w, **kw)

    def publish(self, rid, effects, lote="demo"):
        line = rg.publish(self.ctx(), rid, lote, effects)
        return line, rg.exit_code(line)

    def lines(self, rid, lote="demo"):
        return [x for x in rw_auto.read_registry(self.ctx()) if x.get("item") == f"{rid}/{lote}"]

    def marker(self, repo=None, ref="main"):
        return self.w.git(repo or self.w.origin, "log", "-1", f"--format=%(trailers:key={rg.MARKER},valueonly)", ref)

    def head(self, wt):
        return self.w.git(wt, "rev-parse", "HEAD")

    def state(self):
        return json.loads((self.w.data / "sessions/s1.json").read_text(encoding="utf-8"))

    def cli(self, *args, effects):
        """O verbo `publish` da CLI, no processo, com `effects` no lugar dos efeitos reais."""
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(rg, "Effects", lambda ctx: effects):
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                rc = rw.cli(["publish", *args], self.ctx())
        return rc, out.getvalue(), err.getvalue()

    def install_demo(self, scope="user"):
        """Põe o `demo` da loja no installed_plugins.json do HOME fixture, no escopo `scope`."""
        path = self.w.home / ".claude/plugins/installed_plugins.json"
        data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"version": 2, "plugins": {}}
        data["plugins"][f"demo@{rw.MARKETPLACE}"] = [{"scope": scope, "installPath": str(self.w.tmp / "inst")}]
        path.write_text(json.dumps(data), encoding="utf-8")

    def two_lotes_of_demo(self):
        """Dois lotes do `demo` da mesma base: o primeiro publicado, o segundo segurado por `rebase`. O
        segundo traz outra lição no fim do SKILL.md: dois commits iguais no mesmo segundo teriam o mesmo
        sha, e o segundo já estaria publicado."""
        rid1, wt1 = self.clean_retrofit()
        rid2, wt2 = self.clean_retrofit(edit=lambda wt: append(wt / DOC, "- Outra regra.\n"))
        first, rc1 = self.publish(rid1, self.effects())
        fx = self.effects()
        second, rc2 = self.publish(rid2, fx)
        self.assertEqual((rc1, rc2), (0, 1), (first, second))
        self.assertEqual((second["resultado"], second["motivo"]), ("segurado", "rebase"))
        self.assertEqual(fx.calls, [])
        self.assertEqual(self.w.origin_main(), first["commit"])
        return rid2, wt2, first

    # --- o caminho limpo -----------------------------------------------------------------------

    def test_publish_pushes_exactly_the_reviewed_commit(self):
        rid, wt = self.clean_retrofit()
        fx = self.effects()
        line, rc = self.publish(rid, fx)
        self.assertEqual(rc, 0, line)
        self.assertEqual(self.w.origin_main(), self.head(wt))
        self.assertEqual(self.w.git(self.w.origin, "rev-list", "--count", f"{self.base}..main"), "1")
        self.assertEqual(self.marker(), "autonomous")
        self.assertEqual((line["resultado"], line["instalacao"], line["commit"], line["versao"], line["aprovado"]),
                         ("publicado", "ok", self.head(wt), "1.0.1", False))
        self.assertEqual((line["ramo"], line["worktree"]), (rw_store.branch_name(rid, "demo"), str(wt)))
        self.assertEqual(fx.calls, ["push", "refresh_install", "cache_matches"])
        self.assertEqual([(x["resultado"], x["instalacao"]) for x in self.lines(rid)],
                         [("publicado", "pendente"), ("publicado", "ok")])
        self.assertEqual(self.lines(rid)[-1], line)

    def test_shared_checkout_is_untouched_by_a_publication(self):
        before = self.w.shared_state()
        rid, wt = self.clean_retrofit()
        line, rc = self.publish(rid, self.effects())
        self.assertEqual(rc, 0, line)
        self.assertEqual(self.w.shared_state(), before)

    def test_published_skill_is_silenced_in_the_session_state(self):
        self.install_demo()
        rid, wt = self.clean_retrofit()
        line, rc = self.publish(rid, self.effects())
        self.assertEqual(rc, 0, line)
        self.assertIn("full:demo", self.state()["done"])
        # O `write` do GateHarness grava arquivos do lote; o do HookHarness, o transcript.
        HookHarness.write(self, skill_typed("demo:demo"), *[tool(error=True)] * 3)
        self.assertIsNone(self.run_hook())
        self.assertEqual(self.state()["skills"]["full:demo"]["reviews"], rw.MAX_REVIEWS)

    # --- recusa, push e instalação -------------------------------------------------------------

    def test_refused_retrofit_never_reaches_the_effects(self):
        rid, wt = self.clean_retrofit()
        (rw_auto.retro_dir(self.ctx(), rid) / "veredito.json").unlink()
        fx = self.effects()
        line, rc = self.publish(rid, fx)
        self.assertEqual((rc, line["resultado"], line["motivo"]), (1, "segurado", "sem-veredito"))
        self.assertEqual(fx.calls, [])
        self.assertEqual(self.w.origin_main(), self.base)

    def test_rejected_push_is_an_error_and_keeps_the_branch(self):
        rid, wt = self.clean_retrofit()
        fx = self.effects(push=(False, "recusado pelo remoto"))
        line, rc = self.publish(rid, fx)
        self.assertEqual((rc, line["resultado"], line["motivo"]), (3, "erro", "push"))
        self.assertIn("recusado pelo remoto", line["detalhe"])
        self.assertEqual(fx.calls, ["push"])
        branch = rw_store.branch_name(rid, "demo")
        self.assertEqual(self.w.git(self.w.store, "rev-parse", "--verify", f"refs/heads/{branch}"), self.head(wt))
        self.assertEqual([x["resultado"] for x in self.lines(rid)], ["erro"])
        self.assertEqual(self.w.origin_main(), self.base)

    def test_install_failure_after_push_is_still_published(self):
        rid, wt = self.clean_retrofit()
        line, rc = self.publish(rid, self.effects(install=(False, "o update saiu 1")))
        self.assertEqual(rc, 4)
        self.assertEqual([(x["resultado"], x["instalacao"]) for x in self.lines(rid)],
                         [("publicado", "pendente"), ("publicado", "update")])
        self.assertEqual(line["commit"], self.w.origin_main())
        self.assertIn("o update saiu 1", line["detalhe"])
        self.assertIn("full:demo", self.state()["done"])

    def test_cache_mismatch_is_recorded_in_the_install_field(self):
        rid, wt = self.clean_retrofit()
        line, rc = self.publish(rid, self.effects(after_copy=lambda d: bump_config(d / ".claude-plugin/plugin.json")))
        self.assertEqual((rc, line["instalacao"]), (4, "cache-difere"))
        self.assertIn("plugin.json", line["detalhe"])
        ctx = self.ctx()
        effects = rg.Effects(ctx)
        # Sem cópia da versão no cache: difere, nunca "igual".
        self.assertFalse(effects.cache_matches(ctx, wt, "demo", "9.9.9")[0])
        # A versão vira pasta: fora do formato seguro, nem se compara.
        with self.assertRaises(rw_auto.Malformed):
            effects.cache_matches(ctx, wt, "demo", "x/../1.0.1")

    def test_bytecode_and_in_use_are_not_a_cache_mismatch(self):
        # M7: o `__pycache__` do worktree (ignorado pelo git) e um `.pyc` solto na cópia não contam; o
        # `.in_use` da cópia também não.
        rid, wt = self.clean_retrofit()
        cache = wt / "plugins/demo/skills/demo/tests/__pycache__"
        cache.mkdir()
        (cache / "x.cpython-312.pyc").write_bytes(b"\0")
        # Um arquivo sem `.pyc` no `__pycache__`: a pasta inteira fica fora, não só o bytecode.
        (cache / "x.lock").write_bytes(b"")

        def stray(dest):
            (dest / "solto.pyc").write_bytes(b"\0")
        line, rc = self.publish(rid, self.effects(after_copy=stray))
        self.assertEqual((rc, line["instalacao"]), (0, "ok"), line)

    def test_plugin_not_installed_is_still_published(self):
        rid, wt = self.clean_retrofit()
        fx = self.effects(install=(True, "nao-instalado"))
        line, rc = self.publish(rid, fx)
        self.assertEqual((rc, line["resultado"], line["instalacao"]), (0, "publicado", "nao-instalado"))
        self.assertNotIn("cache_matches", fx.calls)

    # --- rodar de novo e as exceções -----------------------------------------------------------

    def test_rerun_after_push_redoes_only_the_install(self):
        rid, wt = self.clean_retrofit()
        first, rc = self.publish(rid, self.effects(install=(False, "falhou")))
        self.assertEqual(rc, 4)
        pushed = self.w.origin_main()
        (rw_auto.retro_dir(self.ctx(), rid) / "veredito.json").unlink()
        fx = self.effects()
        line, rc = self.publish(rid, fx)
        self.assertEqual((rc, line["resultado"], line["instalacao"], line["commit"]), (0, "publicado", "ok", pushed),
                         line)
        self.assertNotIn("push", fx.calls)
        self.assertEqual(self.w.origin_main(), pushed)
        self.assertEqual([x["instalacao"] for x in self.lines(rid)], ["pendente", "update", "ok"])

    def test_crash_after_push_is_recovered_by_a_rerun(self):
        # Ruling T9-crash: pela C10, a exceção depois da primeira linha `publicado` é `publicado` com
        # `instalacao: "update"` e rc 4, não `erro` e rc 3 como o brief escreveu.
        rid, wt = self.clean_retrofit()
        line, rc = self.publish(rid, self.effects(raises=RuntimeError("caiu no meio")))
        self.assertEqual((rc, line["resultado"], line["instalacao"]), (4, "publicado", "update"), line)
        self.assertIn("RuntimeError: caiu no meio", line["detalhe"])
        pushed = self.w.origin_main()
        self.assertEqual(pushed, self.head(wt))
        fx = self.effects()
        line, rc = self.publish(rid, fx)
        self.assertEqual((rc, line["instalacao"]), (0, "ok"), line)
        self.assertNotIn("push", fx.calls)
        self.assertEqual(self.w.origin_main(), pushed)

    def test_crash_before_the_first_published_line_is_an_internal_error(self):
        rid, wt = self.clean_retrofit()
        line, rc = self.publish(rid, self.effects(push=RuntimeError("o push caiu")))
        self.assertEqual((rc, line["resultado"], line["motivo"]), (3, "erro", "interno"))
        self.assertIn("RuntimeError: o push caiu", line["detalhe"])
        self.assertEqual([x["resultado"] for x in self.lines(rid)], ["erro"])
        self.assertEqual(self.w.origin_main(), self.base)

    def test_publish_without_a_retrofit_json_is_an_error_line(self):
        rid = self.w.retro([{}], [{}])
        fx = self.effects()
        line, rc = self.publish(rid, fx)
        self.assertEqual((rc, line["resultado"], line["motivo"]), (3, "erro", "interno"))
        self.assertIn("Malformed", line["detalhe"])
        self.assertEqual(rw_auto.read_registry(self.ctx())[-1], line)
        self.assertEqual(fx.calls, [])

    def test_gate_stops_on_lessons_of_another_retro(self):
        # Item 7: o licoes.json com o `id` de outra retro válida para a porta antes do push, com `interno`.
        rid, wt = self.clean_retrofit()
        other = self.w.retro([{}], [{}])
        path = rw_auto.retro_dir(self.ctx(), rid) / "licoes.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["id"] = other
        path.write_text(json.dumps(data), encoding="utf-8")
        fx = self.effects()
        line, rc = self.publish(rid, fx)
        self.assertEqual((rc, line["resultado"], line["motivo"]), (3, "erro", "interno"), line)
        self.assertIn("outra retro", line["detalhe"])
        self.assertEqual(fx.calls, [])
        self.assertEqual(self.w.origin_main(), self.base)

    def test_gate_stops_on_the_request_of_another_retro(self):
        # T3-m1: o pedido.json de outra retro válida, de outra sessão. A linha `erro` não leva a sessão dele.
        rid, wt = self.clean_retrofit()
        other = self.w.retro([{}], [{}])
        data = json.loads((rw_auto.retro_dir(self.ctx(), other) / "pedido.json").read_text(encoding="utf-8"))
        data["sessao"] = "s2"
        (rw_auto.retro_dir(self.ctx(), rid) / "pedido.json").write_text(json.dumps(data), encoding="utf-8")
        fx = self.effects()
        line, rc = self.publish(rid, fx)
        self.assertEqual((rc, line["resultado"], line["motivo"]), (3, "erro", "interno"), line)
        self.assertIsNone(line["sessao"], line)
        self.assertEqual(fx.calls, [])
        self.assertEqual(self.w.origin_main(), self.base)

    def test_unwritable_registry_never_raises(self):
        rid, wt = self.clean_retrofit()
        (rw_auto.retro_dir(self.ctx(), rid) / "veredito.json").unlink()
        # O registro vira pasta: nenhuma linha se grava.
        (self.w.data / rw_auto.REGISTRY).unlink(missing_ok=True)
        (self.w.data / rw_auto.REGISTRY).mkdir()
        fx = self.effects()
        line, rc = self.publish(rid, fx)
        self.assertEqual((rc, line["resultado"], line["motivo"]), (3, "erro", "interno"), line)
        self.assertIn("a linha completa falhou", line["detalhe"])
        self.assertEqual(fx.calls, [])
        self.assertEqual(self.w.origin_main(), self.base)

    def test_commit_pushed_without_a_line_is_recorded_on_rerun(self):
        # O push saiu e a porta caiu antes da linha: a próxima chamada grava a linha `publicado`, fecha a
        # retro da sessão e instala, sem push. O commit sobe por outro clone: só o fetch do passo 2 mostra
        # ao worktree que ele já está no `origin/main`.
        rid, wt = self.clean_retrofit()
        self.w.git(self.w.other, "fetch", "-q", str(wt), "HEAD")
        self.w.git(self.w.other, "push", "-q", "origin", "FETCH_HEAD:main")
        self.assertNotEqual(self.w.git(wt, "rev-parse", "origin/main"), self.head(wt))
        fx = self.effects()
        line, rc = self.publish(rid, fx)
        self.assertEqual((rc, line["instalacao"], line["commit"]), (0, "ok", self.head(wt)), line)
        self.assertNotIn("push", fx.calls)
        self.assertEqual([x["instalacao"] for x in self.lines(rid)], ["pendente", "ok"])
        self.assertIn("full:demo", self.state()["done"])
        self.assertIs(line["aprovado"], False)

    def test_approved_commit_pushed_without_a_line_is_recorded_as_approved(self):
        # I1 (c): na recuperação, o `aprovado` sai do trailer do commit publicado.
        rid, wt, lote = self.description_lote()
        rg._mark_approved(self.ctx(), wt, rw_store.git_env(home=self.w.home, nosystem=True), self.head(wt))
        self.w.git(self.w.other, "fetch", "-q", str(wt), "HEAD")
        self.w.git(self.w.other, "push", "-q", "origin", "FETCH_HEAD:main")
        fx = self.effects()
        line, rc = self.publish(rid, fx, lote)
        self.assertEqual((rc, line["commit"]), (0, self.head(wt)), line)
        self.assertNotIn("push", fx.calls)
        self.assertIs(line["aprovado"], True)
        self.assertEqual([x["aprovado"] for x in self.lines(rid, lote) if x["resultado"] == "publicado"], [True, True])

    def test_publish_without_anonimato_is_held_by_its_guard(self):
        # I1 (a): sem o anonimato.json não há patch selado; a porta passa pelo `refuse`, que segura.
        rid, wt = self.clean_retrofit()
        (self.folder(rid) / "anonimato.json").unlink()
        fx = self.effects()
        line, rc = self.publish(rid, fx)
        self.assertEqual((rc, line["resultado"], line["motivo"]), (1, "segurado", "sem-anonimato"), line)
        self.assertEqual(fx.calls, [])
        self.assertEqual(self.w.origin_main(), self.base)

    def test_rerun_finishes_the_close_that_a_crash_cut(self):
        # I2: o fecho (as lições trazidas de volta e o `mark_done`) cai depois da primeira linha `publicado`;
        # a nova chamada acha essa linha e roda o fecho de novo.
        rid = self.w.retro([{}, {}], [{}, {}])
        ctx = self.ctx()
        wt = Path(rw_store.prepare(ctx, rid, "demo")["worktree"])
        self.w.retrofit(wt)
        rw_store.seal(ctx, rid, "demo", ["1"], [])
        rw_store.seal(ctx, rid, "demo", ["1", "2"], [])
        self.review(rid)
        real = rg._finish
        with mock.patch.object(rg, "_finish", side_effect=RuntimeError("a trava do estado desistiu")):
            line, rc = self.publish(rid, self.effects())
        self.assertEqual((rc, line["resultado"], line["instalacao"]), (4, "publicado", "update"), line)
        self.assertEqual([x["item"] for x in rw_auto.held(ctx)], [f"{rid}/demo#2"])
        self.assertFalse((self.w.data / "sessions/s1.json").exists())
        self.assertIs(rg._finish, real)
        fx = self.effects()
        line, rc = self.publish(rid, fx)
        self.assertEqual((rc, line["instalacao"]), (0, "ok"), line)
        self.assertNotIn("push", fx.calls)
        self.assertEqual(rw_auto.held(ctx), [])
        self.assertIn("full:demo", self.state()["done"])

    def test_fresh_worktree_is_not_taken_as_published(self):
        # A base tem pai e o `sealed` é o patch dela: só a comparação com a `base` separa o worktree
        # recém-preparado de um lote publicado.
        self.w.advance_origin({"tests/antes.txt": "x\n"}, "chore: um commit antes da base")
        rid = self.w.retro([{}], [{}])
        got = rw_store.prepare(self.ctx(), rid, "demo")
        wt = Path(got["worktree"])
        sealed = rw_store.patch_id(wt, base="HEAD^")
        self.w.advance_origin({"tests/extra.txt": "x\n"}, "fix(demo2): v1.0.1\n\nRetrofit-Mode: autonomous")
        self.w.git(wt, "fetch", "-q", "origin")
        self.assertEqual(self.head(wt), got["base"])
        self.assertFalse(rg.already_published(wt, got, sealed))

    def test_published_lote_on_another_branch_goes_through_refuse(self):
        # T9-pub: o commit do lote está no `origin/main`, mas o worktree saiu do ramo do lote.
        rid, wt = self.clean_retrofit()
        self.w.git(self.w.other, "fetch", "-q", str(wt), "HEAD")
        self.w.git(self.w.other, "push", "-q", "origin", "FETCH_HEAD:main")
        self.w.git(wt, "fetch", "-q", "origin")
        retrofit = self.read(rid, "retrofit.json")
        sealed = self.read(rid, "anonimato.json")["patch"]
        self.assertTrue(rg.already_published(wt, retrofit, sealed))
        self.w.git(wt, "checkout", "-q", "-b", "outro-ramo")
        self.assertFalse(rg.already_published(wt, retrofit, sealed))
        fx = self.effects()
        line, rc = self.publish(rid, fx)
        self.assertEqual((rc, line["resultado"], line["motivo"]), (1, "segurado", "escopo"), line)
        self.assertIn("outro-ramo", line["detalhe"])
        self.assertEqual(fx.calls, [])

    def test_worktree_reset_to_origin_main_is_not_published(self):
        # T9-pub: no ramo do lote, levado por `reset --hard` a um commit do `origin/main` depois da base.
        rid, wt = self.clean_retrofit()
        moved = self.w.advance_origin({"tests/extra.txt": "x\n"}, "chore: outro commit no origin")
        self.w.git(wt, "fetch", "-q", "origin")
        self.w.git(wt, "reset", "-q", "--hard", "origin/main")
        self.assertEqual(self.head(wt), moved)
        retrofit = self.read(rid, "retrofit.json")
        self.assertFalse(rg.already_published(wt, retrofit, self.read(rid, "anonimato.json")["patch"]))
        fx = self.effects()
        line, rc = self.publish(rid, fx)
        self.assertEqual((rc, line["resultado"], line["motivo"]), (1, "segurado", "escopo"), line)
        self.assertEqual(fx.calls, [])
        self.assertEqual(self.w.origin_main(), moved)

    # --- a trava -------------------------------------------------------------------------------

    def test_lock_failure_is_an_error_line(self):
        rid, wt = self.clean_retrofit()
        real, seen = rw._lock, []

        def fake(path, timeout=None):
            if Path(path).name == rg.PUBLISH_LOCK:
                seen.append((Path(path), timeout))
                raise OSError("trava ocupada")
            return real(path, timeout)
        fx = self.effects()
        with mock.patch.object(rw, "_lock", fake):
            line, rc = self.publish(rid, fx)
        self.assertEqual(seen, [(self.w.data / rg.PUBLISH_LOCK, rg.PUBLISH_LOCK_WAIT)])
        self.assertEqual(rg.PUBLISH_LOCK_WAIT, 900)
        self.assertEqual((rc, line["resultado"], line["motivo"]), (3, "erro", "trava"))
        self.assertIn("trava ocupada", line["detalhe"])
        self.assertEqual(fx.calls, [])
        self.assertEqual(self.w.origin_main(), self.base)

    def wait_for(self, path, timeout):
        """Tenta a trava numa thread: (segundos até a resposta, "presa" ou "livre"), ou None se a
        thread passou de 5 s esperando."""
        got = []

        def attempt():
            start = time.monotonic()
            try:
                rw._unlock(rw._lock(path, timeout=timeout))
                got.append((time.monotonic() - start, "livre"))
            except OSError:
                got.append((time.monotonic() - start, "presa"))
        thread = threading.Thread(target=attempt, daemon=True)
        thread.start()
        thread.join(5)
        return got[0] if got else None

    @unittest.skipIf(rw.fcntl is None, "a trava de outro descritor no mesmo processo se mede onde há fcntl")
    def test_lock_wait_has_a_deadline(self):
        path = self.w.data / "espera.lock"
        held = rw._lock(path)
        try:
            got = self.wait_for(path, 1)
        finally:
            rw._unlock(held)
        self.assertIsNotNone(got, "a trava esperou sem prazo")
        self.assertEqual(got[1], "presa")
        self.assertGreaterEqual(got[0], 0.9)
        self.assertLess(got[0], 5)

    @unittest.skipIf(rw.fcntl is None, "a trava de outro descritor no mesmo processo se mede onde há fcntl")
    def test_zero_timeout_fails_at_once(self):
        # M18: `timeout=0` é "não espere", não "sem prazo".
        path = self.w.data / "espera.lock"
        held = rw._lock(path)
        try:
            got = self.wait_for(path, 0)
        finally:
            rw._unlock(held)
        self.assertIsNotNone(got, "timeout=0 esperou sem prazo")
        self.assertEqual(got[1], "presa")
        self.assertLess(got[0], 0.5)
        self.assertEqual(self.wait_for(path, 0)[1], "livre")

    @unittest.skipIf(rw.fcntl is None, "a trava de outro descritor no mesmo processo se mede onde há fcntl")
    def test_the_lock_is_held_during_the_push(self):
        rid, wt = self.clean_retrofit()
        tried = []

        def during(worktree):
            try:
                rw._unlock(rw._lock(self.w.data / rg.PUBLISH_LOCK, timeout=0))
                tried.append("livre")
            except OSError:
                tried.append("presa")
        line, rc = self.publish(rid, self.effects(during_push=during))
        self.assertEqual(rc, 0, line)
        self.assertEqual(tried, ["presa"])

    # --- duas portas, rebase e redo ------------------------------------------------------------

    def test_second_gate_rebases_over_the_first_publication(self):
        rid = self.w.retro([{}, {"plugin": "demo2"}], [{}, {}], skills=("demo", "demo2"))
        ctx = self.ctx()
        trees = {lote: Path(rw_store.prepare(ctx, rid, lote)["worktree"]) for lote in ("demo", "demo2")}

        # O lote do `demo` acrescenta uma linha no README acima da do `demo2`: o rebase do segundo desloca
        # os números de linha dele (os `@@`), e o patch não pode mudar por isso.
        readme = trees["demo"] / "README.md"
        lines = readme.read_text(encoding="utf-8").splitlines(keepends=True)
        at = next(i for i, x in enumerate(lines) if x.startswith("- **demo** "))
        lines.insert(at + 1, "  Uma nota do demo.\n")
        readme.write_text("".join(lines), encoding="utf-8")
        for lote in ("demo", "demo2"):
            self.w.retrofit(trees[lote], plugin=lote)
            self.seal(rid, lote)
        first, rc1 = self.publish(rid, self.effects(), "demo")
        # O rc 0 do segundo é a guarda 13 aceitando o anonimato.json da revisão de antes do rebase.
        second, rc2 = self.publish(rid, self.effects(), "demo2")
        self.assertEqual((rc1, rc2), (0, 0), (first, second))
        self.assertEqual(self.w.git(self.w.origin, "rev-list", f"{self.base}..main").split(),
                         [second["commit"], first["commit"]])
        catalog = json.loads(self.w.git(self.w.origin, "show", "main:.claude-plugin/marketplace.json"))
        self.assertEqual({e["name"]: e["version"] for e in catalog["plugins"]},
                         {"demo": "1.0.1", "demo-cmd": "1.0.0", "demo2": "1.0.1"})

    def test_second_lote_of_the_same_plugin_conflicts_and_is_held(self):
        self.two_lotes_of_demo()

    def test_a_rebase_hold_can_be_redone_and_published(self):
        rid, wt, first = self.two_lotes_of_demo()
        got = rw_store.prepare(self.ctx(), rid, "demo", redo=True)
        self.assertEqual(got["tentativa"], 2)
        wt2 = Path(got["worktree"])
        self.w.retrofit(wt2, plugin="demo", version="1.0.2")
        self.seal(rid)
        line, rc = self.publish(rid, self.effects())
        self.assertEqual((rc, line["resultado"], line["versao"]), (0, "publicado", "1.0.2"), line)
        self.assertEqual((line["commit"], line["ramo"]), (self.w.origin_main(), rw_store.branch_name(rid, "demo", 2)))
        old = rw_store.branch_name(rid, "demo")
        self.assertEqual(self.w.git(self.w.store, "rev-parse", "--verify", f"refs/heads/{old}"), self.head(wt))

    # --- a aprovação do dono -------------------------------------------------------------------

    def description_lote(self, **commit):
        lote = "demo__description"
        rid, wt = self.clean_retrofit(licoes=({"muda_description": True},), lote=lote, **commit)
        held, rc = self.publish(rid, self.effects(), lote)
        self.assertEqual((rc, held["motivo"]), (1, "muda-description"))
        rw_auto.approve(self.ctx(), rid, lote)
        return rid, wt, lote

    def test_owner_approval_publishes_with_the_approved_marker(self):
        rid, wt, lote = self.description_lote()
        tree = self.w.git(wt, "rev-parse", "HEAD^{tree}")
        line, rc = self.publish(rid, self.effects(), lote)
        self.assertEqual((rc, line["resultado"], line["aprovado"]), (0, "publicado", True), line)
        self.assertEqual(self.marker(), "autonomous-approved")
        self.assertEqual(self.w.git(self.w.origin, "rev-parse", "main^{tree}"), tree)
        self.assertEqual(self.w.git(self.w.origin, "rev-list", "--count", f"{self.base}..main"), "1")
        self.assertEqual(line["commit"], self.w.origin_main())
        # De novo: a emenda do trailer não tira o lote de "já publicado" (o revisor selou o de antes).
        fx = self.effects()
        again, rc = self.publish(rid, fx, lote)
        self.assertEqual((rc, again["resultado"], again["commit"]), (0, "publicado", line["commit"]), again)
        self.assertNotIn("push", fx.calls)

    # --- o ensino do portão com os verbos reais (Final-F1) ----------------------------------------

    def teach_public(self, wt, word):
        """A palavra "público" do dono: `--publico-add` no worktree e a emenda com a lista (passo 6)."""
        proc = self.w.run_script(wt, "scripts/anonymity-gate.py", "--publico-add", word)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.w.git(wt, "commit", "-q", "-a", "--amend", "--no-edit")

    def held_as(self, rid, motivo):
        line, rc = self.publish(rid, self.effects())
        self.assertEqual((rc, line["resultado"], line["motivo"]), (1, "segurado", motivo), line)

    def teaching(self, tag, publish_before_approve=False, without_review=False, missing_review=False):
        """Um termo em dúvida que o dono chama de público, com o `approve` e o `publish` de verdade."""
        word = camel(tag)
        rid, wt = self.clean_retrofit(edit=lambda wt: append(wt / DOC, f"- Veja o {word}.\n"),
                                      review={"doubt": word})
        ctx = self.ctx()
        if without_review:
            # O `sem-anonimato` aprovado antes da segunda passada: um `approve` a mais não estraga o par.
            (self.folder(rid) / "anonimato.json").unlink()
            self.held_as(rid, "sem-anonimato")
            rw_auto.approve(ctx, rid, "demo")
            self.review(rid, doubt=word)
        if missing_review:
            # O caminho do passo 6 (item 3): a segunda passada e a porta, sem `approve` até o par do dono.
            (self.folder(rid) / "anonimato.json").unlink()
            self.held_as(rid, "sem-anonimato")
            self.review(rid, doubt=word)
        self.held_as(rid, "termo-nao-publico")
        if missing_review:
            self.assertFalse((self.folder(rid) / "aprovado.json").exists(), "um `approve` veio antes do par")
        self.teach_public(wt, word)
        if publish_before_approve:
            self.held_as(rid, "escopo")
        rw_auto.approve(ctx, rid, "demo")
        line, rc = self.publish(rid, self.effects())
        self.assertEqual((rc, line["resultado"], line["aprovado"]), (0, "publicado", True), line)
        published = self.w.git(self.w.origin, "show", "main:scripts/public-names.txt").splitlines()
        self.assertIn(word, published)

    def test_teaching_the_gate_in_the_right_order_publishes(self):
        self.teaching("ordem")

    def test_teaching_the_gate_with_a_publish_before_the_approve_publishes(self):
        self.teaching("antes", publish_before_approve=True)

    def test_teaching_the_gate_after_a_missing_review_publishes(self):
        self.teaching("passada", publish_before_approve=True, without_review=True)

    def test_missing_review_path_publishes_without_an_early_approve(self):
        self.teaching("falta", missing_review=True)

    def test_teaching_a_harvested_name_with_capital_and_accent_publishes(self):
        # Item 13: a camada 1 cita o trecho com os escapes do `ascii()` (`\xe9`), e o dono escreve o nome
        # como ele é, com maiúscula e acento. A guarda 5 compara a forma, não a letra: o ensino publica.
        name = "Zq" + chr(0xE9) + "lvorn"
        harvested = self.w.tmp / "repos" / name
        harvested.mkdir(parents=True)
        self.w.git(harvested, "init", "-q")
        rid, wt = self.clean_retrofit(edit=lambda wt: append(wt / DOC, f"- Como no {name}.\n"))
        self.held_as(rid, "nome-privado")
        self.teach_public(wt, name)
        rw_auto.approve(self.ctx(), rid, "demo")
        line, rc = self.publish(rid, self.effects())
        self.assertEqual((rc, line["resultado"], line["aprovado"]), (0, "publicado", True), line)
        published = self.w.git(self.w.origin, "show", "main:scripts/public-names.txt").splitlines()
        self.assertIn(name, published)

    def test_amend_keeps_the_marker_before_another_trailer(self):
        # I3: com outro trailer depois do `Retrofit-Mode`, a emenda o troca no lugar; no fim, a nova chamada
        # do lote publicado não reconheceria o patch selado e cairia no `refuse`.
        other = "Refs: " + "pedido-1"
        rid, wt, lote = self.description_lote(trailer=None,
                                              message=f"fix(demo): v1.0.1\n\n{rg.MARKER}: autonomous\n{other}")
        line, rc = self.publish(rid, self.effects(), lote)
        self.assertEqual(rc, 0, line)
        body = self.w.git(self.w.origin, "log", "-1", "--format=%B", "main").splitlines()
        self.assertEqual(body[-2:], [f"{rg.MARKER}: {rg.APPROVED}", other])
        with mock.patch.object(rg, "_check", wraps=rg._check) as spy:
            again, rc = self.publish(rid, self.effects(), lote)
        self.assertEqual((rc, again["commit"]), (0, line["commit"]), again)
        spy.assert_not_called()

    def test_rejected_push_of_an_approved_lote_can_be_rerun(self):
        # O push recusado devolve o ramo ao commit revisado: a emenda do trailer muda o patch (D20), e sem
        # isso a próxima porta seguraria por `revisao-desatualizada`.
        rid, wt, lote = self.description_lote()
        reviewed = self.head(wt)
        line, rc = self.publish(rid, self.effects(push=(False, "recusado")), lote)
        self.assertEqual((rc, line["motivo"]), (3, "push"))
        self.assertEqual(self.head(wt), reviewed)
        self.assertEqual(self.marker(wt, "HEAD"), "autonomous")
        line, rc = self.publish(rid, self.effects(), lote)
        self.assertEqual((rc, line["aprovado"]), (0, True), line)
        self.assertEqual(self.marker(), "autonomous-approved")

    @unittest.skipIf(os.name == "nt", "os hooks do git do teste são scripts de shell")
    def test_amend_that_changes_the_tree_or_drops_the_marker_is_an_error(self):
        # Um hook do clone que reescreve um arquivo no commit, ou tira o trailer da mensagem, faz a emenda
        # publicar outra coisa: a porta para antes do push, com `interno`, e devolve o ramo ao revisado.
        hooks = self.w.store / ".git/hooks"
        cases = (("pre-commit", '#!/bin/sh\necho mais >> README.md\ngit add README.md\n', "arvore"),
                 ("commit-msg", '#!/bin/sh\nsed -i "/^Retrofit-Mode/d" "$1"\n', rg.MARKER))
        for hook, body, why in cases:
            with self.subTest(hook=hook):
                rid, wt, lote = self.description_lote()
                reviewed = self.head(wt)
                (hooks / hook).write_text(body, encoding="utf-8")
                (hooks / hook).chmod(0o755)
                try:
                    fx = self.effects()
                    line, rc = self.publish(rid, fx, lote)
                finally:
                    (hooks / hook).unlink()
                self.assertEqual((rc, line["resultado"], line["motivo"]), (3, "erro", "interno"), line)
                self.assertIn(why, line["detalhe"])
                self.assertEqual(fx.calls, [])
                self.assertEqual(self.head(wt), reviewed)
                self.assertEqual(self.w.origin_main(), self.base)

    def test_lesson_brought_back_by_a_second_seal_is_closed(self):
        # T9-seal: a lição que o primeiro selo segurou (`executor-recusou`) volta no segundo; publicado o
        # lote, ela ganha a linha que a fecha, e `held()` não a lista mais.
        rid = self.w.retro([{}, {}], [{}, {}])
        ctx = self.ctx()
        wt = Path(rw_store.prepare(ctx, rid, "demo")["worktree"])
        self.w.retrofit(wt)
        rw_store.seal(ctx, rid, "demo", ["1"], [])
        self.assertEqual([x["item"] for x in rw_auto.held(ctx)], [f"{rid}/demo#2"])
        rw_store.seal(ctx, rid, "demo", ["1", "2"], [])
        self.review(rid)
        line, rc = self.publish(rid, self.effects())
        self.assertEqual((rc, line["licoes"]), (0, [1, 2]), line)
        self.assertEqual(rw_auto.held(ctx), [])
        last = rw_auto.last_lines(rw_auto.read_registry(ctx))
        closing = last[f"{rid}/demo#2"]
        self.assertEqual((closing["resultado"], closing["commit"], closing["detalhe"], closing["licoes"]),
                         ("publicado", line["commit"], f"publicada no lote {rid}/demo", [2]))
        self.assertNotIn(f"{rid}/demo#1", last)

    # --- o ambiente do git de rede -------------------------------------------------------------

    def test_network_git_runs_in_batch_mode(self):
        # T9-ssh: o fetch e o push nunca pedem a senha da chave no terminal; o GIT_SSH_COMMAND do dono fica.
        own = "ssh -o " + "IdentitiesOnly=yes"
        for inherited, plugin in ((None, "demo"), (own, "demo2")):
            with self.subTest(inherited=inherited):
                rid, wt = self.clean_retrofit(licoes=({"plugin": plugin},), skills=(plugin,), lote=plugin)
                with mock.patch.dict(os.environ):
                    os.environ.pop("GIT_SSH_COMMAND", None)
                    os.environ.pop("GIT_SSH", None)
                    if inherited:
                        os.environ["GIT_SSH_COMMAND"] = inherited
                    with mock.patch.object(rw_store, "run", wraps=rw_store.run) as spy:
                        line, rc = self.publish(rid, self.effects(), plugin)
                self.assertEqual(rc, 0, line)
                calls = [c for c in spy.call_args_list if {"fetch", "push"} & {str(a) for a in c.args[0]}]
                verbs = [next(str(a) for a in c.args[0] if str(a) in ("fetch", "push")) for c in calls]
                self.assertEqual(verbs.count("push"), 1, verbs)
                self.assertGreaterEqual(verbs.count("fetch"), 2, verbs)
                for call in calls:
                    env = call.kwargs["env"]
                    self.assertEqual(env["GIT_TERMINAL_PROMPT"], "0")
                    self.assertEqual(env["GIT_SSH_COMMAND"], inherited or "ssh -o BatchMode=yes")

    def test_network_git_reads_the_system_config(self):
        # Item 11: no Git for Windows o `credential.helper` padrão mora na config de sistema. O fetch e o
        # push a leem (rw_store.remote_env); as outras guardas continuam sem ela.
        rid, wt = self.clean_retrofit()
        with mock.patch.object(rw_store, "run", wraps=rw_store.run) as spy:
            line, rc = self.publish(rid, self.effects())
        self.assertEqual(rc, 0, line)
        calls = [c for c in spy.call_args_list if {"fetch", "push"} & {str(a) for a in c.args[0]}]
        verbs = [next(str(a) for a in c.args[0] if str(a) in ("fetch", "push")) for c in calls]
        self.assertEqual(verbs.count("push"), 1, verbs)
        self.assertGreaterEqual(verbs.count("fetch"), 2, verbs)
        for call in calls:
            env = call.kwargs["env"]
            # Sem o assertNotIn: a mensagem dele imprimiria o ambiente inteiro de quem roda.
            self.assertFalse("GIT_CONFIG_NOSYSTEM" in env, call.args[0])
            self.assertEqual(env["GIT_TERMINAL_PROMPT"], "0")
            self.assertEqual(env["HOME"], str(self.ctx().home))
        rebases = [c for c in spy.call_args_list if "rebase" in [str(a) for a in c.args[0]]]
        self.assertTrue(rebases)
        for call in rebases:
            self.assertEqual(call.kwargs["env"]["GIT_CONFIG_NOSYSTEM"], "1")

    def test_network_env_keeps_the_owner_ssh(self):
        # T9-ssh2: GIT_SSH_COMMAND, GIT_SSH ou `core.sshCommand` do dono: nenhum BatchMode por cima.
        rid, wt = self.clean_retrofit()
        own = "ssh -o " + "IdentitiesOnly=yes"
        base = {k: v for k, v in rw_store.git_env(home=self.w.home, nosystem=True).items()
                if k not in ("GIT_SSH_COMMAND", "GIT_SSH")}
        self.assertEqual(rg.network_env(base, wt)["GIT_SSH_COMMAND"], "ssh -o BatchMode=yes")
        for label, env in (("GIT_SSH_COMMAND", dict(base, GIT_SSH_COMMAND=own)),
                           ("GIT_SSH", dict(base, GIT_SSH="/usr/bin/ssh"))):
            with self.subTest(label):
                got = rg.network_env(env, wt)
                self.assertEqual(got["GIT_TERMINAL_PROMPT"], "0")
                self.assertEqual(got.get("GIT_SSH_COMMAND"), env.get("GIT_SSH_COMMAND"))
        with self.subTest("core.sshCommand"):
            self.w.git(wt, "config", "core.sshCommand", own)
            got = rg.network_env(base, wt)
            self.assertEqual(got["GIT_TERMINAL_PROMPT"], "0")
            self.assertNotIn("GIT_SSH_COMMAND", got)
            # A config lida é a do ambiente do push: com o HOME do Context e no worktree.
            self.w.git(wt, "config", "--unset", "core.sshCommand")
            (self.w.home / ".gitconfig").write_text(
                (self.w.home / ".gitconfig").read_text(encoding="utf-8") + f"[core]\n\tsshCommand = {own}\n",
                encoding="utf-8")
            self.assertNotIn("GIT_SSH_COMMAND", rg.network_env(base, wt))

    def test_push_sends_the_checked_sha_not_the_head(self):
        # Final-F7: um commit novo no worktree depois do `refuse` não sobe; sobe o sha que a porta conferiu.
        rid, wt = self.clean_retrofit()
        checked = []

        def during(worktree):
            checked.append(self.head(worktree))
            # Fora da pasta do plugin: a cópia instalada continua igual, e o rc diz só o push.
            (Path(worktree) / "nota-nova.md").write_text("Uma linha que ninguem conferiu.\n", encoding="utf-8")
            self.amend(worktree)
        line, rc = self.publish(rid, self.effects(during_push=during))
        self.assertEqual(rc, 0, line)
        self.assertNotEqual(self.head(wt), checked[0])
        self.assertEqual((self.w.origin_main(), line["commit"]), (checked[0], checked[0]))

    # --- item 10: a porta publica o HEAD que ela conferiu ----------------------------------------

    def after_check(self, then):
        """Embrulha `rg._check`: depois dele, `then(head)` mexe no worktree (o commit "depois das guardas")."""
        original = rg._check

        def wrapped(ctx, rid, lote, notes):
            got = original(ctx, rid, lote, notes)
            then(got[1])
            return got
        return mock.patch.object(rg, "_check", side_effect=wrapped)

    def test_commit_made_during_the_guards_is_held(self):
        # Item 10: uma guarda a mais, antes de `_g_still`, emenda o commit do worktree no meio das guardas.
        rid, wt = self.clean_retrofit()

        def sabotage(p):
            append(Path(p.worktree) / DOC, "- Uma linha que a camada 1 nao leu.\n")
            self.amend(p.worktree)
            return None
        guards = list(rg.GUARDS)
        at = next(i for i, (_, guard) in enumerate(guards) if guard is rg._g_caps) + 1
        guards.insert(at, ("escopo", sabotage))
        fx = self.effects()
        with mock.patch.object(rg, "GUARDS", tuple(guards)):
            line, rc = self.publish(rid, fx)
        self.assertEqual((rc, line["resultado"], line["motivo"]), (1, "segurado", "arvore-suja"), line)
        self.assertIn("HEAD mudou", line["detalhe"])
        self.assertEqual(self.w.origin_main(), self.base)
        self.assertEqual(fx.calls, [])

    def test_plan_records_the_checked_sha(self):
        # Item 10: um commit novo no worktree depois do `_check` não entra na linha nem sobe.
        rid, wt = self.clean_retrofit()
        checked = []

        def then(head):
            checked.append(head)
            (wt / "nota-nova.md").write_text("Uma linha que ninguem conferiu.\n", encoding="utf-8")
            self.w.git(wt, "add", "-A")
            self.w.git(wt, "commit", "-q", "-m", "docs: depois das guardas")
        with self.after_check(then):
            line, rc = self.publish(rid, self.effects())
        self.assertEqual(rc, 0, line)
        self.assertNotEqual(self.head(wt), checked[0])
        self.assertEqual((line["commit"], self.w.origin_main()), (checked[0], checked[0]))

    def test_approval_amends_the_reviewed_message(self):
        # Item 10: depois do `_check`, a mensagem do HEAD ganha um nome; a emenda do trailer usa a revisada.
        rid, wt, lote = self.description_lote()
        name = invented("emenda")

        def then(head):
            message = self.w.git(wt, "log", "-1", "--format=%B")
            self.w.git(wt, "commit", "-q", "--amend", "-m", message + "\n" + name + "\n")
        with self.after_check(then):
            line, rc = self.publish(rid, self.effects(), lote)
        self.assertEqual(rc, 0, line)
        body = self.w.git(self.w.origin, "log", "-1", "--format=%B", "main")
        self.assertNotIn(name, body)
        self.assertEqual(self.marker(), rg.APPROVED)
        self.assertEqual(line["commit"], self.w.origin_main())

    def test_approval_refuses_a_commit_on_top(self):
        # Item 10: depois do `_check`, commits por cima do revisado que voltam à árvore dele. A emenda do
        # último tem a árvore certa e outro pai: `interno`, nada sobe e o ramo volta ao revisado. Um só
        # `commit --allow-empty` não chega à conferência do pai: o `commit --amend` dele sai 1 ("would make
        # it empty") antes, e o mutante sem a conferência sobreviveria.
        rid, wt, lote = self.description_lote()
        reviewed = []

        def then(head):
            reviewed.append(head)
            (wt / "nota-nova.md").write_text("Por cima do revisado.\n", encoding="utf-8")
            self.w.git(wt, "add", "-A")
            self.w.git(wt, "commit", "-q", "-m", "chore: por cima")
            self.w.git(wt, "rm", "-q", "nota-nova.md")
            self.w.git(wt, "commit", "-q", "-m", "chore: de volta a arvore revisada")
            self.assertEqual(self.w.git(wt, "rev-parse", "HEAD^{tree}"), self.w.git(wt, "rev-parse", f"{head}^{{tree}}"))
        fx = self.effects()
        with self.after_check(then):
            line, rc = self.publish(rid, fx, lote)
        self.assertEqual((rc, line["resultado"], line["motivo"]), (3, "erro", "interno"), line)
        self.assertIn("pai do commit revisado", line["detalhe"])
        self.assertEqual(self.w.origin_main(), self.base)
        self.assertEqual(self.head(wt), reviewed[0])
        self.assertEqual(fx.calls, [])

    def test_approval_refuses_a_tree_no_guard_read(self):
        # Item 10, rodada 1: depois do `_check`, uma emenda põe um arquivo novo e mantém o pai. A árvore de
        # referência é a do revisado, não a do HEAD de antes da emenda do trailer: `interno`, nada sobe.
        rid, wt, lote = self.description_lote()
        reviewed = []

        def then(head):
            reviewed.append(head)
            (wt / "nota-nova.md").write_text("Uma arvore que nenhuma guarda leu.\n", encoding="utf-8")
            self.amend(wt)
        fx = self.effects()
        with self.after_check(then):
            line, rc = self.publish(rid, fx, lote)
        self.assertEqual((rc, line["resultado"], line["motivo"]), (3, "erro", "interno"), line)
        self.assertIn("arvore", line["detalhe"])
        self.assertEqual(self.w.origin_main(), self.base)
        self.assertEqual(fx.calls, [])

    def test_approval_returns_the_sha_it_checked(self):
        # Item 10, rodada 1: um commit entra no worktree logo depois da primeira leitura do git que segue a
        # emenda do trailer. As conferências e o retorno usam o sha dessa leitura: sobe a emenda, e o
        # commit novo, que nenhuma conferência viu, fica de fora.
        rid, wt, lote = self.description_lote()
        tree = self.w.git(wt, "rev-parse", "HEAD^{tree}")
        original = rw_store._git
        state = {"amended": False, "done": False}

        def spy(args, cwd, env, what):
            out = original(args, cwd, env, what)
            if what == "aprovacao" and state["amended"] and not state["done"]:
                state["done"] = True
                (wt / "nota-nova.md").write_text("Entre as leituras da emenda.\n", encoding="utf-8")
                self.w.git(wt, "add", "-A")
                self.w.git(wt, "commit", "-q", "-m", "chore: entre as leituras")
            if what == "aprovacao" and "--amend" in args:
                state["amended"] = True
            return out
        with mock.patch.object(rw_store, "_git", side_effect=spy):
            line, rc = self.publish(rid, self.effects(), lote)
        self.assertTrue(state["done"])
        self.assertEqual(rc, 0, line)
        self.assertEqual(line["commit"], self.w.origin_main())
        self.assertEqual(self.w.git(self.w.origin, "rev-parse", "main^{tree}"), tree)
        self.assertEqual(self.marker(), rg.APPROVED)

    def test_push_never_follows_tags(self):
        # Final-F9: com `push.followTags` na config do dono, o push da porta não leva uma tag ao `origin`.
        rid, wt = self.clean_retrofit()
        self.w.git(wt, "config", "push.followTags", "true")
        self.w.git(wt, "tag", "-a", "-m", "uma tag local", "v-local")
        with mock.patch.object(rw_store, "run", wraps=rw_store.run) as spy:
            line, rc = self.publish(rid, self.effects())
        self.assertEqual(rc, 0, line)
        pushes = [[str(a) for a in c.args[0]] for c in spy.call_args_list if "push" in [str(a) for a in c.args[0]]]
        self.assertEqual(len(pushes), 1, pushes)
        self.assertIn("--no-follow-tags", pushes[0])
        self.assertEqual(self.w.git(self.w.origin, "tag", "--list"), "")

    def test_fixture_push_refuses_a_real_remote(self):
        rid, wt = self.clean_retrofit()
        self.w.git(wt, "remote", "set-url", "--push", "origin", a_real_remote())
        with mock.patch.object(rw_store, "run", wraps=rw_store.run) as spy:
            with self.assertRaises(AssertionError):
                self.effects().push(wt, self.head(wt))
            line, rc = self.publish(rid, self.effects())
        self.assertEqual([c for c in spy.call_args_list if "push" in [str(a) for a in c.args[0]]], [])
        self.assertEqual((rc, line["resultado"], line["motivo"]), (3, "erro", "interno"))
        self.assertIn("AssertionError", line["detalhe"])
        self.assertEqual(self.w.origin_main(), self.base)

    # --- os efeitos reais ----------------------------------------------------------------------

    def test_real_effects_without_claude_fail_closed(self):
        empty = self.w.tmp / "sem-claude"
        empty.mkdir()
        with mock.patch.dict(os.environ, {"PATH": str(empty)}):
            self.assertEqual(rg.Effects(self.ctx()).refresh_install("demo"), (False, "claude ausente"))

    @unittest.skipIf(os.name == "nt", "o claude falso é um script de shell")
    def test_real_effects_update_only_a_user_scope_install(self):
        bindir = self.w.tmp / "bin-claude"
        bindir.mkdir()
        log = self.w.tmp / "claude.log"
        fake = bindir / "claude"
        fake.write_text(f'#!/bin/sh\necho "$@" >> "{log}"\nexit "${{FAKE_RC:-0}}"\n', encoding="utf-8")
        fake.chmod(0o755)
        effects = rg.Effects(self.ctx())
        path = {"PATH": f"{bindir}{os.pathsep}{os.environ.get('PATH', '')}"}
        with mock.patch.dict(os.environ, path):
            # I1 (b): sem o installed_plugins.json no HOME, nada está instalado (rc 0, não 4).
            installed = self.w.home / ".claude/plugins/installed_plugins.json"
            original = installed.read_text(encoding="utf-8")
            installed.unlink()
            self.assertEqual(effects.refresh_install("demo"), (True, "nao-instalado"))
            installed.write_text(original, encoding="utf-8")  # o arquivo sem o `demo`
            self.assertEqual(effects.refresh_install("demo"), (True, "nao-instalado"))
            self.install_demo(scope="project")
            self.assertEqual(effects.refresh_install("demo"), (True, "nao-instalado"))
            self.assertFalse(log.exists())
            self.install_demo()
            ok, detail = effects.refresh_install("demo")
            self.assertTrue(ok, detail)
            self.assertNotEqual(detail, "nao-instalado")
            self.assertEqual(log.read_text(encoding="utf-8").splitlines(),
                             [f"plugin marketplace update {rw.MARKETPLACE}",
                              f"plugin update demo@{rw.MARKETPLACE} --scope user"])
            with mock.patch.dict(os.environ, {"FAKE_RC": "3"}):
                ok, detail = effects.refresh_install("demo")
        self.assertFalse(ok)
        self.assertIn("3", detail)

    # --- a linha de comando --------------------------------------------------------------------

    def test_cli_publish_prints_the_line_and_the_phrase(self):
        rid, wt = self.clean_retrofit()
        rc, out, err = self.cli(rid, "demo", effects=self.effects(install=(False, "sem rede")))
        self.assertEqual(rc, 4, err)
        sha = self.w.origin_main()
        lines = out.splitlines()
        self.assertEqual(lines[-1], f"retrofit-watch: demo v1.0.1 publicada sozinha ({sha[:7]}) \\u2014 "
                                    "c\\xf3pia instalada n\\xe3o atualizada: update")
        self.assertEqual(json.loads("\n".join(lines[:-1]))["instalacao"], "update")
        rc, out, err = self.cli(rid, "demo", effects=self.effects())
        self.assertEqual(rc, 0, err)
        self.assertEqual(out.splitlines()[-1], f"retrofit-watch: demo v1.0.1 publicada sozinha ({sha[:7]})")
        self.assertTrue(out.isascii())

    def test_cli_publish_in_auto_dry_never_calls_effects(self):
        rid, wt = self.clean_retrofit()
        self.config(mode="auto-dry")
        fx = self.effects()
        rc, out, err = self.cli(rid, "demo", effects=fx)
        self.assertEqual(rc, 1, err)
        self.assertEqual(fx.calls, [])
        self.assertEqual(self.w.origin_main(), self.base)
        lines = out.splitlines()
        self.assertEqual(lines[-1], f"retrofit-watch: demo segurada \\u2014 auto-dry (ramo {rw_store.branch_name(rid, 'demo')})")
        self.assertEqual(json.loads("\n".join(lines[:-1]))["motivo"], "auto-dry")

    def test_cli_publish_refuses_names_out_of_format(self):
        # T7-rc: <id> ou <lote> fora do formato é uso (rc 2), sem traceback e sem linha no registro.
        rid, wt = self.clean_retrofit()
        before = rw_auto.read_registry(self.ctx())
        fx = self.effects()
        for args in ((rid,), (rid, "demo", "x"), ("../" + rid, "demo"), (rid, "demo\n"), (rid, "-demo"),
                     (rid, "d" + chr(0xE9) + "mo")):
            with self.subTest(args=args):
                rc, out, err = self.cli(*args, effects=fx)
                self.assertEqual((rc, out), (2, ""), err)
                self.assertTrue(err.isascii(), err)
                self.assertIn("publish <id> <lote>", err)
                self.assertNotIn("Traceback", err)
        self.assertEqual(rw_auto.read_registry(self.ctx()), before)
        self.assertEqual(fx.calls, [])

    def test_cli_lines_are_ascii_on_cp1252(self):
        # M4: `→` não existe no cp1252; `é` e `ç` existem e deixariam vivo o `ensure_ascii=False`.
        arrow = chr(0x2192)
        rid, wt = self.clean_retrofit(review={"regra_repetida": f"SKILL.md:3 repete {arrow} a regra"})
        env = dict(self.w.env, CLAUDE_PLUGIN_DATA=str(self.w.data), PYTHONIOENCODING="cp1252")
        proc = subprocess.run([sys.executable, str(SCRIPT), "publish", rid, "demo"], capture_output=True, env=env,
                              timeout=600)
        self.assertEqual(proc.returncode, 1, proc.stderr.decode("utf-8", "replace"))
        self.assertTrue(proc.stdout.isascii(), proc.stdout)
        text = proc.stdout.decode("cp1252")
        lines = text.splitlines()
        self.assertIn("segurada", lines[-1])
        line = json.loads("\n".join(lines[:-1]))
        self.assertEqual((line["motivo"], line["detalhe"]), ("regra-repetida", f"SKILL.md:3 repete {arrow} a regra"))
        self.assertEqual(self.w.origin_main(), self.base)


if __name__ == "__main__":
    unittest.main()
