"""Testes da loja do modo autônomo (rw_store.py): a colheita, o worktree do lote (`prepare`) e o selo
do executor (`seal`), com a camada 1 do portão de anonimização.

Rodar: python3 plugins/retrofit-watch/skills/retrofit-watch/tests/test_auto_store.py
A loja é a fixture da Tarefa 6 (um `origin` `--bare` e um clone, sob o diretório temporário). Nenhum
teste toca a rede, o `claude` real ou um `origin` real. Todo nome inventado se monta em tempo de
execução: um literal faria a camada 1 reprovar o próprio ramo.
"""
import contextlib
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import fixture_store as fs  # noqa: E402
import retrofit_watch as rw  # noqa: E402  (o test_retrofit_watch, importado pela fixture, põe scripts/ no path)
import rw_auto  # noqa: E402
import rw_store  # noqa: E402

SCRIPT = HERE.parent / "scripts" / "retrofit_watch.py"


def invented(tag):
    """Um nome que não existe em lugar nenhum, montado aqui."""
    return "zq" + tag + "vorn"


def remote(owner, name):
    return "https" + "://" + "example" + ".invalid/" + owner + "/" + name + ".git"


def tgit(env, cwd, *args):
    proc = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, env=env, encoding="utf-8",
                          errors="replace")
    if proc.returncode:
        raise subprocess.CalledProcessError(proc.returncode, args, proc.stdout, proc.stderr)
    return proc.stdout.strip()


def make_repo(env, path, origin=None):
    path.mkdir(parents=True, exist_ok=True)
    tgit(env, path, "init", "-q")
    if origin:
        tgit(env, path, "remote", "add", "origin", origin)
    return path


class RunAndNamesTest(unittest.TestCase):
    def test_run_reports_timeout_and_missing_binary(self):
        start = time.time()
        rc, _ = rw_store.run([sys.executable, "-c", "import time; time.sleep(30)"], timeout=1)
        self.assertEqual(rc, 124)
        self.assertLess(time.time() - start, 20)
        rc, out = rw_store.run([invented("bin") + "-nao-existe"])
        self.assertEqual(rc, 127)
        self.assertTrue(out)
        rc, out = rw_store.run([sys.executable, "-c", "import sys; print('x'); sys.stderr.write('y'); sys.exit(3)"])
        self.assertEqual((rc, out.split()), (3, ["x", "y"]))

    def test_run_never_raises_on_a_nul(self):
        # Ruling T7-r1a: o subprocess recusa um NUL com ValueError; o `run` o lê como "não rodou", rc 127.
        nul = chr(0)
        for kwargs in ({"cmd": [sys.executable, "-c", "pass", "a" + nul + "b"]},
                       {"cmd": [sys.executable, "-c", "pass"], "cwd": "x" + nul + "y"}):
            with self.subTest(kwargs=kwargs):
                rc, out = rw_store.run(**kwargs)
                self.assertEqual(rc, 127)
                self.assertTrue(out)
        ctx = rw.Context(home=tempfile.gettempdir(), data_dir=tempfile.gettempdir())
        self.assertIsInstance(rw_store.harvest(ctx, cwd="proj" + nul), set)

    def test_expand_breaks_a_long_name(self):
        a, b = invented("alfa"), invented("beta")
        term = f"{a} de {b}"
        self.assertEqual(rw_store.expand(term),
                         {term, f"{a} de", f"{a}_de", f"de {b}", f"de_{b}", a, b,
                          f"{a}-de-{b}", f"{a}_de_{b}", f"{a}de{b}"})
        self.assertEqual(rw_store.expand(f"  {a}  "), {a})
        self.assertEqual(rw_store.expand("   "), set())

    def test_expand_breaks_a_compound_name(self):
        # Final-F4: um nome de repo quase nunca tem espaço. O `-`, o `_`, o `.` e a fronteira do CamelCase
        # também separam as partes, com a mesma política das palavras de um nome com espaço.
        a, b = invented("alfa"), invented("beta")
        forms = {f"{a} {b}", f"{a}_{b}", f"{a}-{b}", f"{a}{b}", a, b}
        for term in (f"{a}-{b}", f"{a}_{b}", f"{a}.{b}"):
            with self.subTest(term=term):
                self.assertEqual(rw_store.expand(term), forms | {term})
        camel_term = a.capitalize() + b.capitalize()
        self.assertEqual(rw_store.expand(camel_term),
                         {camel_term, f"{a.capitalize()} {b.capitalize()}", f"{a.capitalize()}_{b.capitalize()}",
                          f"{a.capitalize()}-{b.capitalize()}", a.capitalize(), b.capitalize()})
        # Uma parte curta (menos de MIN_WORD letras) não vira termo sozinha, como no nome com espaço.
        short = rw_store.expand(f"{a}-de")
        self.assertIn(f"{a} de", short)
        self.assertNotIn("de", short)
        # Um e-mail não se parte no `.` do domínio: a parte local já entra pela colheita, sozinha.
        email = a + "@" + "example" + ".invalid"
        self.assertEqual(rw_store.expand(email), {email})

    def test_worktree_and_branch_names_come_from_the_id_and_lote(self):
        ctx = rw.Context(home=tempfile.gettempdir(), data_dir=tempfile.gettempdir())
        self.assertEqual(rw_store.worktree_path(ctx, "r1", "demo"), ctx.home / ".wt/retrofit-auto-demo-r1")
        self.assertEqual(rw_store.worktree_path(ctx, "r1", "demo", 3), ctx.home / ".wt/retrofit-auto-demo-r1-r3")
        self.assertEqual(rw_store.branch_name("r1", "demo"), "retrofit-auto/demo-r1")
        self.assertEqual(rw_store.branch_name("r1", "demo", 2), "retrofit-auto/demo-r1-r2")
        for bad in (0, -1, True, "2"):
            with self.subTest(tentativa=bad):
                with self.assertRaises(rw_store.StoreError):
                    rw_store.branch_name("r1", "demo", bad)
        with self.assertRaises(rw_auto.Malformed):
            rw_store.worktree_path(ctx, "r1", "../x")

    def test_origin_terms_give_an_owner_only_with_a_host(self):
        owner, name = invented("dono"), invented("nome")
        user = invented("usu")
        cases = {
            remote(owner, name): [owner, name],
            "https" + "://" + user + ":" + "x" + "@" + "example.invalid/" + owner + "/" + name: [owner, name],
            "ssh" + "://" + "git" + "@" + "example.invalid:22/" + owner + "/" + name + ".git": [owner, name],
            "git" + "@" + "example.invalid:" + owner + "/" + name + ".git": [owner, name],
            "/srv/" + owner + "/" + name + ".git": [name],
            "file" + "://" + "/srv/" + owner + "/" + name: [name],
            "file" + "://" + "localhost/srv/" + owner + "/" + name: [name],
            "C:" + "\\" + "srv" + "\\" + owner + "\\" + name: [name],
            "": [],
        }
        for url, expected in cases.items():
            with self.subTest(url=url):
                self.assertEqual(rw_store.origin_terms(url), expected)


class HarvestTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(os.path.realpath(tempfile.mkdtemp(prefix="rw-store-")))
        self.home = self.tmp / invented("usr")
        (self.home / ".claude").mkdir(parents=True)
        self.data = self.tmp / "data"
        self.data.mkdir()
        self.roots = self.tmp / "repos"
        self.env = fs._clean_env(self.home)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def config(self, **keys):
        keys.setdefault("harvest_roots", [str(self.roots)])
        (self.home / ".claude/retrofit-watch.json").write_text(json.dumps(keys), encoding="utf-8")

    def ctx(self):
        return rw.Context(home=self.home, data_dir=self.data)

    def gitconfig(self, folder, name=None, email=None):
        lines = ["[user]\n"]
        if name:
            lines.append(f"\tname = {name}\n")
        if email:
            lines.append(f"\temail = {email}\n")
        folder.mkdir(parents=True, exist_ok=True)
        (folder / ".gitconfig").write_text("".join(lines), encoding="utf-8")

    def cli(self, *args):
        env = dict(self.env, CLAUDE_PLUGIN_DATA=str(self.data))
        return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, env=env, timeout=60,
                              encoding="utf-8", errors="replace")

    def test_harvest_collects_every_source(self):
        n = {k: invented(k) for k in ("ra", "rb", "own", "rem", "own2", "rem2", "plain", "nm", "sob", "mail",
                                     "pa", "pb", "cmt")}
        make_repo(self.env, self.roots / n["ra"], remote(n["own"], n["rem"]))
        make_repo(self.env, self.roots / "grupo" / n["rb"],
                  "git" + "@" + "example.invalid:" + n["own2"] + "/" + n["rem2"] + ".git")
        (self.roots / n["plain"]).mkdir(parents=True)
        user_name = f"{n['nm']} De {n['sob']}"
        email = n["mail"] + "@" + "example.invalid"
        self.gitconfig(self.home, user_name)
        # O e-mail fica na config global do XDG (~/.config/git/config), ao lado do ~/.gitconfig.
        (self.home / ".config/git").mkdir(parents=True)
        (self.home / ".config/git/config").write_text(f"[user]\n\temail = {email}\n", encoding="utf-8")
        private = self.tmp / "privados.txt"
        private.write_text(f"{n['pa']}\n\n# {n['cmt']}\n  {n['pb']}  \n", encoding="utf-8")
        self.config(private_sources=[str(private), str(self.tmp / "nao-existe.txt")])
        got = rw_store.harvest(self.ctx())
        expected = {n["ra"], n["rb"], n["own"], n["rem"], n["own2"], n["rem2"], user_name, n["nm"], n["sob"],
                    f"{n['nm']} De", f"{n['nm']}_De", email, n["mail"], self.home.name, socket.gethostname(),
                    socket.gethostname().split(".")[0], n["pa"], n["pb"]}
        self.assertEqual(expected - got, set())
        for absent in (n["plain"], "grupo", n["cmt"], f"# {n['cmt']}", "De"):
            with self.subTest(absent=absent):
                self.assertNotIn(absent, got)

    def test_harvest_includes_the_session_project(self):
        proj, owner, name = invented("proj"), invented("pown"), invented("prem")
        root = make_repo(self.env, self.tmp / "fora" / proj, remote(owner, name))
        (root / "src").mkdir()
        self.config()
        with_cwd = rw_store.harvest(self.ctx(), cwd=root / "src")
        self.assertEqual({proj, owner, name} - with_cwd, set())
        self.assertNotIn("src", with_cwd)
        without = rw_store.harvest(self.ctx())
        self.assertEqual({proj, owner, name} & without, set())
        # Um cwd que não é repo, ou que não existe, não derruba a colheita.
        self.assertIn(self.home.name, rw_store.harvest(self.ctx(), cwd=self.tmp / "nao-existe"))

    def test_harvest_reads_the_project_path_from_stdout_only(self):
        # CR-r1 #4: com `core.fsyncObjectFiles` na config do repo, o git 2.43 sai 0 no `rev-parse` e põe um
        # aviso no stderr. O caminho é só o stdout: o nome e os termos do `origin` entram na colheita.
        proj, owner, name = invented("wproj"), invented("wown"), invented("wrem")
        root = make_repo(self.env, self.tmp / "fora" / proj, remote(owner, name))
        tgit(self.env, root, "config", "core.fsyncObjectFiles", "true")
        self.config()
        got = rw_store.harvest(self.ctx(), cwd=root)
        self.assertEqual({proj, owner, name} - got, set())
        real_run = rw_store.run
        # CR-r2 #1: nem todo git avisa (o Git for Windows 2.56 não avisa). O `run` falso põe o aviso na saída
        # sempre que a chamada não tira o stderr, como o git 2.43: o caso não depende do git da máquina.
        with self.subTest("aviso no stderr, com o run falso"):
            def warns(cmd, *args, **kwargs):
                if "--show-toplevel" in cmd:
                    if kwargs.get("stderr") is subprocess.DEVNULL:
                        return 0, str(root) + "\n"
                    return 0, "warning: " + invented("aviso") + "\n" + str(root) + "\n"
                return real_run(cmd, *args, **kwargs)

            with mock.patch.object(rw_store, "run", warns):
                got = rw_store.harvest(self.ctx(), cwd=root)
            self.assertEqual({proj, owner, name} - got, set())
        # Um stdout de rc 0 que não é uma pasta absoluta é StoreError, nunca um nome a menos: o caminho
        # relativo (o `.` é pasta para quem roda) e a pasta que não existe.
        for label, out in (("relativo", "."), ("ausente", str(self.tmp / "nao-existe" / proj))):
            with self.subTest(label):
                def fake(cmd, *args, out=out, **kwargs):
                    if "--show-toplevel" in cmd:
                        return 0, out + "\n"
                    return real_run(cmd, *args, **kwargs)

                with mock.patch.object(rw_store, "run", fake):
                    with self.assertRaises(rw_store.StoreError) as caught:
                        rw_store.harvest(self.ctx(), cwd=root)
                self.assertIn("nao deu uma pasta", str(caught.exception))

    def test_harvest_reads_a_symlinked_cwd_by_its_physical_path(self):
        # CR-r1 #2: o git sobe pelo caminho físico do `cwd` (o `-C` faz `chdir`). A busca do `.git` também:
        # um link fora de repo para um projeto que não lê é StoreError, e um link dentro de um repo bom para
        # uma pasta fora de repo não é erro.
        probe = self.tmp / "probe-link"
        try:
            os.symlink(str(self.tmp), probe)
        except (OSError, NotImplementedError):
            self.skipTest("sem permissao de link simbolico")
        probe.unlink()
        broken = self.tmp / "fora" / invented("lkq")
        (broken / "src").mkdir(parents=True)
        (broken / ".git").write_text("gitdir: " + str(self.tmp / "sumiu" / "mais") + "\n", encoding="utf-8")
        loose = self.tmp / "soltos"
        loose.mkdir()
        good = make_repo(self.env, self.tmp / "bom" / invented("lkb"))
        plain = self.tmp / "sem-repo" / "alvo"
        plain.mkdir(parents=True)
        self.config()
        with self.subTest("link fora de repo para o projeto que nao le"):
            link = loose / "para-o-projeto"
            os.symlink(str(broken / "src"), link)
            with self.assertRaises(rw_store.StoreError) as caught:
                rw_store.harvest(self.ctx(), cwd=link)
            self.assertIn(str(broken), str(caught.exception))
        with self.subTest("link dentro do repo bom para uma pasta fora de repo"):
            link = good / "para-fora"
            os.symlink(str(plain), link)
            self.assertIn(self.home.name, rw_store.harvest(self.ctx(), cwd=link))

    def test_harvest_refuses_a_session_project_that_does_not_read(self):
        # Final-F1 (C8): o projeto da sessão tem `.git`, mas o `rev-parse` falha (um `gitfile` que aponta
        # para uma pasta que sumiu): StoreError com o caminho, nunca uma colheita sem o nome do projeto.
        proj = invented("gfq")
        root = self.tmp / "fora" / proj
        (root / "src").mkdir(parents=True)
        (root / ".git").write_text("gitdir: " + str(self.tmp / "sumiu" / "mais") + "\n", encoding="utf-8")
        self.config()
        for cwd in (root, root / "src"):
            with self.subTest(cwd=cwd.name):
                with self.assertRaises(rw_store.StoreError) as caught:
                    rw_store.harvest(self.ctx(), cwd=cwd)
                self.assertIn(str(root), str(caught.exception))
        # CR-r2 #2: a mensagem do git sai de uma segunda chamada, com o stderr junto (a primeira o tira).
        # O teste confere as chamadas, e não o texto do git, que pode vir traduzido.
        with self.subTest("a segunda chamada traz o stderr"):
            real_run = rw_store.run
            calls = []

            def records(cmd, *args, **kwargs):
                if "--show-toplevel" in cmd:
                    calls.append(kwargs.get("stderr", subprocess.STDOUT))
                return real_run(cmd, *args, **kwargs)

            with mock.patch.object(rw_store, "run", records):
                with self.assertRaises(rw_store.StoreError):
                    rw_store.harvest(self.ctx(), cwd=root)
            self.assertEqual(len(calls), 2, calls)
            self.assertIs(calls[0], subprocess.DEVNULL)
            self.assertIsNot(calls[1], subprocess.DEVNULL)
        # A pasta sem `.git` em lugar nenhum acima dela continua sem erro.
        plain = self.tmp / "sem-repo" / "sub"
        plain.mkdir(parents=True)
        self.assertIn(self.home.name, rw_store.harvest(self.ctx(), cwd=plain))
        # O cwd que sumiu, dentro de um repo que lê, também: o `rev-parse` sai fora do rc 0 só porque a
        # pasta não existe.
        good = make_repo(self.env, self.tmp / "bom" / invented("gfb"))
        self.assertIn(self.home.name, rw_store.harvest(self.ctx(), cwd=good / "sumiu"))

    def test_harvest_respects_depth_and_survives_bad_roots(self):
        deep, two = invented("deep"), invented("two")
        make_repo(self.env, self.roots / "a" / "b" / deep)
        make_repo(self.env, self.roots / "a" / two)
        not_a_dir = self.tmp / "arquivo"
        not_a_dir.write_text("x", encoding="utf-8")
        self.config(harvest_roots=[str(self.tmp / "nao-existe"), str(not_a_dir), str(self.roots)])
        got = rw_store.harvest(self.ctx())
        self.assertIn(two, got)
        self.assertNotIn(deep, got)

    def test_harvest_fails_closed_on_an_unreadable_source(self):
        # Item 8 (C8): uma fonte que existe e não lê é StoreError com a fonte; nunca uma colheita menor.
        make_repo(self.env, self.roots / invented("fa"), remote(invented("fown"), invented("frem")))
        locked = self.roots / "grupo"
        make_repo(self.env, locked / invented("fb"))
        self.gitconfig(self.home, invented("fnm"))
        real_iterdir, real_run = Path.iterdir, rw_store.run

        def iterdir(path):
            if path == locked:
                raise PermissionError(13, "Permission denied", str(path))
            return real_iterdir(path)

        def failing(*words):
            def fake(cmd, *args, **kwargs):
                if all(w in cmd for w in words):
                    return 128, "fatal: " + invented("quebrado")
                return real_run(cmd, *args, **kwargs)
            return fake

        folder = self.tmp / "fonte-pasta"
        folder.mkdir()
        cases = {
            "private_sources": ({"private_sources": [str(folder)]}, None, str(folder)),
            "iterdir": ({}, mock.patch.object(Path, "iterdir", iterdir), str(locked)),
            "origin": ({}, mock.patch.object(rw_store, "run", failing("remote", "get-url")), "origin"),
            "config": ({}, mock.patch.object(rw_store, "run", failing("config", "user.name")), "user.name"),
        }
        for source, (keys, patch, named) in cases.items():
            with self.subTest(source=source):
                self.config(**keys)
                with patch or contextlib.nullcontext():
                    with self.assertRaises(rw_store.StoreError) as caught:
                        rw_store.harvest(self.ctx())
                self.assertIn(named, str(caught.exception))

    def test_harvest_skips_what_is_absent(self):
        # Item 8 (C8): o que não existe continua sem erro: o repo sem `origin` (rc 2), a chave ausente da
        # config (rc 1), a fonte privada ausente e a pasta que sumiu no meio da varredura.
        bare, ra, own, rem, nm = (invented(k) for k in ("sem", "ab", "aown", "arem", "anm"))
        make_repo(self.env, self.roots / bare)
        make_repo(self.env, self.roots / ra, remote(own, rem))
        gone = self.roots / "sumiu"
        gone.mkdir(parents=True)
        self.gitconfig(self.home, nm)  # sem user.email
        self.config(private_sources=[str(self.tmp / "nao-existe.txt")])
        real_iterdir = Path.iterdir

        def iterdir(path):
            if path == gone:
                raise FileNotFoundError(2, "No such file or directory", str(path))
            return real_iterdir(path)

        with mock.patch.object(Path, "iterdir", iterdir):
            got = rw_store.harvest(self.ctx())
        self.assertEqual({bare, ra, own, rem, nm, self.home.name} - got, set())

    def test_harvest_skips_a_clone_deleted_mid_scan(self):
        # T5-r1-focus: o clone que some entre o `_repos` (ou o `rev-parse` do projeto) e o `_origin_of`
        # é ausência, não leitura que falhou. O git sai 128 nele; a colheita segue com os outros nomes.
        keep, kown, krem = invented("kp"), invented("kown"), invented("krem")
        make_repo(self.env, self.roots / keep, remote(kown, krem))
        nm = invented("dnm")
        self.gitconfig(self.home, nm)
        self.config()
        real_run = rw_store.run
        for where in ("raiz", "projeto"):
            with self.subTest(where=where):
                base = self.roots if where == "raiz" else self.tmp / "fora"
                doomed = make_repo(self.env, base / invented("dd" + where), remote(invented("down"), invented("drem")))
                cwd = doomed if where == "projeto" else None

                def fake(cmd, *args, doomed=doomed, **kwargs):
                    if "get-url" in cmd and str(doomed) in cmd:
                        shutil.rmtree(doomed)
                    return real_run(cmd, *args, **kwargs)

                with mock.patch.object(rw_store, "run", fake):
                    got = rw_store.harvest(self.ctx(), cwd=cwd)
                self.assertFalse(doomed.exists())
                self.assertEqual({keep, kown, krem, nm, self.home.name} - got, set())

    @unittest.skipIf(os.name == "nt" or (hasattr(os, "geteuid") and os.geteuid() == 0),
                     "chmod 000 não barra o root nem vale no Windows")
    def test_harvest_refuses_a_folder_without_permission(self):
        # T5-r1: a pasta `chmod 000` sob a raiz. No Python 3.12 o `exists()` do `.git` relança o EACCES
        # cru; no 3.13 pode dar False e o repo sumiria. Os dois casos têm de ser StoreError com a pasta.
        make_repo(self.env, self.roots / invented("ok"))
        # Na última profundidade: ali ninguém faz `iterdir` da pasta, e só a conferência do `.git` a vê.
        locked = self.roots / "grupo" / invented("tranc")
        locked.mkdir(parents=True)
        self.config()
        os.chmod(locked, 0)
        try:
            with self.assertRaises(rw_store.StoreError) as caught:
                rw_store.harvest(self.ctx())
        finally:
            os.chmod(locked, 0o700)
        self.assertIn(str(locked), str(caught.exception))

    def test_harvest_origin_without_host_gives_no_owner(self):
        parent, name, other = invented("parent"), invented("lrem"), invented("lrem2")
        make_repo(self.env, self.roots / invented("ca"), str(self.tmp / parent / (name + ".git")))
        make_repo(self.env, self.roots / invented("cb"), "file" + "://" + str(self.tmp / parent / other))
        self.config()
        got = rw_store.harvest(self.ctx())
        self.assertEqual({name, other} - got, set())
        self.assertNotIn(parent, got)

    def test_harvest_git_ignores_inherited_location_and_config(self):
        # Ruling C5: o git da colheita lê o HOME do Context e nada que o ambiente herdado aponte.
        good = invented("good")
        self.gitconfig(self.home, good)
        repo_name, owner, name = invented("rr"), invented("rown"), invented("rname")
        make_repo(self.env, self.roots / repo_name, remote(owner, name))
        trap = {k: invented("trap" + k) for k in ("dir", "home", "global", "xdg", "orig", "count")}
        trap_repo = make_repo(self.env, self.tmp / "trap-repo", remote(trap["orig"], trap["orig"]))
        trap_home = self.tmp / "trap-home"
        self.gitconfig(trap_home, trap["home"])
        trap_global = self.tmp / "trap-global"
        self.gitconfig(trap_global, trap["global"])
        trap_xdg = self.tmp / "trap-xdg"
        (trap_xdg / "git").mkdir(parents=True)
        (trap_xdg / "git/config").write_text(f"[user]\n\temail = {trap['xdg']}@x.invalid\n", encoding="utf-8")
        self.config()
        traps = {"GIT_DIR": str(trap_repo / ".git"), "GIT_WORK_TREE": str(trap_repo), "HOME": str(trap_home),
                 "GIT_CONFIG_GLOBAL": str(trap_global / ".gitconfig"), "XDG_CONFIG_HOME": str(trap_xdg),
                 "GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "user.name", "GIT_CONFIG_VALUE_0": trap["count"]}
        with mock.patch.dict(os.environ, traps):
            with mock.patch.object(rw_store, "run", wraps=rw_store.run) as spy:
                got = rw_store.harvest(self.ctx())
        self.assertEqual({good, repo_name, owner, name} - got, set())
        for value in trap.values():
            with self.subTest(trap=value):
                self.assertFalse([t for t in got if value in t])
        for call in spy.call_args_list:
            env = call.kwargs["env"]
            self.assertEqual((env["HOME"], env["GIT_CONFIG_NOSYSTEM"]), (str(self.home), "1"))

    def test_write_harvest_is_private_and_outside_repos(self):
        name = invented("wh")
        make_repo(self.env, self.roots / name)
        self.config()
        old = self.data / rw_store.HARVEST_FILE
        old.write_text("velho\n", encoding="utf-8")
        old.chmod(0o644)
        path = rw_store.write_harvest(self.ctx())
        self.assertEqual(path, old)
        self.assertIn(name, path.read_text(encoding="utf-8").splitlines())
        self.assertNotIn("velho", path.read_text(encoding="utf-8"))
        if os.name != "nt":
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
        inside = make_repo(self.env, self.tmp / "um-repo") / "dados"
        inside.mkdir()
        with self.assertRaises(rw_store.StoreError) as caught:
            rw_store.write_harvest(rw.Context(home=self.home, data_dir=inside))
        self.assertIn("dentro de um repo", str(caught.exception))
        self.assertFalse((inside / rw_store.HARVEST_FILE).exists())

    def test_write_harvest_replaces_the_file_and_leaves_no_temp(self):
        # Achado I2: quem já abriu o arquivo antigo (o portão de outro lote) lê o antigo inteiro, nunca
        # um arquivo truncado; uma falha no meio não deixa temporário com nomes.
        name = invented("atom")
        make_repo(self.env, self.roots / name)
        self.config()
        path = self.data / rw_store.HARVEST_FILE
        old = "".join(invented(f"old{i}") + "\n" for i in range(50))
        path.write_text(old, encoding="utf-8")
        if os.name != "nt":  # no Windows, o os.replace sobre um arquivo aberto dá PermissionError
            with open(path, encoding="utf-8") as reader:
                rw_store.write_harvest(self.ctx())
                self.assertEqual(reader.read(), old)
        else:
            rw_store.write_harvest(self.ctx())
        self.assertIn(name, path.read_text(encoding="utf-8").splitlines())
        before = path.read_text(encoding="utf-8")
        with mock.patch.object(rw_store.os, "replace", side_effect=OSError("disco cheio")):
            with self.assertRaises(OSError):
                rw_store.write_harvest(self.ctx())
        self.assertEqual(path.read_text(encoding="utf-8"), before)
        self.assertEqual(sorted(p.name for p in self.data.iterdir()), [rw_store.HARVEST_FILE])

    def test_harvest_cli_prints_no_name(self):
        names = [invented("cli1"), invented("cli2")]
        for name in names:
            make_repo(self.env, self.roots / name)
        self.config()
        proc = self.cli("harvest")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        out = json.loads(proc.stdout)
        self.assertEqual(set(out), {"termos", "arquivo"})
        for name in names + [self.home.name]:
            self.assertNotIn(name, proc.stdout)
        path = Path(out["arquivo"])
        self.assertEqual(path, self.data / rw_store.HARVEST_FILE)
        self.assertEqual(out["termos"], len(path.read_text(encoding="utf-8").splitlines()))
        self.assertTrue(set(names) <= set(path.read_text(encoding="utf-8").splitlines()))
        self.assertFalse(any((p / ".git").exists() for p in [path.parent, *path.parents]))

    def test_cli_maps_store_and_os_errors_to_rc_2_in_ascii(self):
        # Ruling T7-rc: StoreError, Malformed e OSError dão rc 2, sem traceback, com o stderr em ASCII.
        self.config()
        cases = {
            "StoreError": ("prepare", "r1", "demo"),
            "Malformed": ("seal", "r" + chr(0xE9), "demo", "--licoes", "1"),
            "uso": ("seal", "r1", "demo"),
        }
        for what, args in cases.items():
            with self.subTest(what):
                proc = self.cli(*args)
                self.assertEqual(proc.returncode, 2, proc.stderr)
                self.assertNotIn("Traceback", proc.stderr)
                self.assertTrue(proc.stderr.isascii(), proc.stderr)
                self.assertEqual(proc.stdout, "")
        (self.data / rw_store.HARVEST_FILE).mkdir()
        proc = self.cli("harvest")
        self.assertEqual(proc.returncode, 2, proc.stderr)
        self.assertNotIn("Traceback", proc.stderr)
        self.assertIn(rw_store.HARVEST_FILE, proc.stderr)


@fs.requires_store
class StoreTest(unittest.TestCase):
    def setUp(self):
        self.w = fs.StoreWorld()
        self.w.data.mkdir(exist_ok=True)
        self.config()

    def tearDown(self):
        self.w.cleanup()

    def config(self, **keys):
        data = {"mode": "auto", "store": str(self.w.store), "harvest_roots": [str(self.w.tmp / "repos")]}
        data.update(keys)
        (self.w.home / ".claude/retrofit-watch.json").write_text(json.dumps(data), encoding="utf-8")

    def ctx(self):
        return self.w.ctx()

    def cli(self, *args):
        env = dict(self.w.env, CLAUDE_PLUGIN_DATA=str(self.w.data))
        return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, env=env, timeout=300,
                              encoding="utf-8", errors="replace")

    def retrofit_json(self, rid, lote="demo"):
        return json.loads((rw_auto.lote_dir(self.ctx(), rid, lote) / "retrofit.json").read_text(encoding="utf-8"))

    def prepared(self, licoes=({},), pareceres=None):
        rid = self.w.retro(list(licoes), list(pareceres or [{} for _ in licoes]))
        return rid, rw_store.prepare(self.ctx(), rid, "demo")

    def assert_rc2(self, proc, *needles):
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertNotIn("Traceback", proc.stderr)
        for needle in needles:
            self.assertIn(needle, proc.stderr)

    # --- prepare -------------------------------------------------------------------------------

    def test_prepare_creates_a_linked_worktree_from_origin_main(self):
        rid = self.w.retro([{}], [{}])
        new = self.w.advance_origin({"notas.md": "nota\n"}, "docs: nota")
        got = rw_store.prepare(self.ctx(), rid, "demo")
        wt = rw_store.worktree_path(self.ctx(), rid, "demo")
        self.assertEqual((got["worktree"], got["ramo"], got["base"], got["tentativa"]),
                         (str(wt), rw_store.branch_name(rid, "demo"), new, 1))
        self.assertEqual((got["plugin"], got["tipo"], got["licoes"], got["fases"], got["commit"], got["versao"],
                          got["patch"]), ("demo", "auto", [1], None, None, None, None))
        self.assertEqual(set(got), rw_auto.RETROFIT_KEYS)
        self.assertEqual(self.w.git(wt, "branch", "--show-current"), rw_store.branch_name(rid, "demo"))
        common = self.w.git(wt, "rev-parse", "--path-format=absolute", "--git-common-dir")
        self.assertEqual(Path(common), self.w.store / ".git")
        self.assertEqual(self.retrofit_json(rid), got)
        self.assertEqual(rw_auto.load_retrofit(rw_auto.lote_dir(self.ctx(), rid, "demo") / "retrofit.json"), got)

    def test_prepare_leaves_the_shared_checkout_untouched(self):
        rid = self.w.retro([{}], [{}])
        (self.w.store / "sujo.txt").write_text("sujo\n", encoding="utf-8")
        before = self.w.shared_state()
        rw_store.prepare(self.ctx(), rid, "demo")
        self.assertEqual(self.w.shared_state(), before)

    def test_prepare_is_idempotent(self):
        rid, first = self.prepared()
        second = rw_store.prepare(self.ctx(), rid, "demo")
        self.assertEqual(first, second)
        listed = self.w.git(self.w.store, "worktree", "list", "--porcelain")
        self.assertEqual(listed.count("worktree "), 2)

    def test_prepare_refuses_a_lote_outside_the_triage(self):
        rid = self.w.retro([{}], [{}])
        with self.assertRaises(rw_store.StoreError) as caught:
            rw_store.prepare(self.ctx(), rid, "demo2")
        self.assertIn("nao e um lote da triagem", str(caught.exception))
        self.assertFalse(rw_store.worktree_path(self.ctx(), rid, "demo2").exists())

    def test_store_missing_is_an_error_with_the_reason(self):
        rid = self.w.retro([{}], [{}])
        for store in (None, str(self.w.tmp / "nao-e-loja")):
            with self.subTest(store=store):
                self.config(store=store)
                with self.assertRaises(rw_store.StoreError) as caught:
                    rw_store.store_clone(self.ctx())
                self.assertIn("store", str(caught.exception))
                self.assert_rc2(self.cli("prepare", rid, "demo"), "sem loja")
        self.assertFalse((rw_auto.lote_dir(self.ctx(), rid, "demo") / "retrofit.json").exists())

    def test_redo_opens_the_next_attempt_only_after_a_rebase_hold(self):
        rid, first = self.prepared()
        ctx = self.ctx()
        self.assert_rc2(self.cli("prepare", rid, "demo", "--redo"), "rebase")
        wt1 = Path(first["worktree"])
        self.w.retrofit(wt1)
        sealed = rw_store.seal(ctx, rid, "demo", ["1"], [])

        def hold(motivo):
            rw_auto.append_registry(ctx, rw_auto._line("s1", rid, f"{rid}/demo", "demo", [1], "segurado", motivo,
                                                       lote="demo"))
        hold("executor-falhou")
        self.assert_rc2(self.cli("prepare", rid, "demo", "--redo"), "rebase")
        hold("rebase")
        proc = self.cli("prepare", rid, "demo", "--redo")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        second = json.loads(proc.stdout)
        self.assertEqual((second["tentativa"], second["worktree"], second["ramo"], second["commit"]),
                         (2, str(rw_store.worktree_path(ctx, rid, "demo", 2)), rw_store.branch_name(rid, "demo", 2),
                          None))
        self.assertTrue(second["worktree"].endswith("-r2") and second["ramo"].endswith("-r2"))
        self.assertTrue(wt1.is_dir())
        # Ruling T7-r1c: o retrofit.json da tentativa 1, já selado, fica como retrofit-r1.json.
        folder = rw_auto.lote_dir(ctx, rid, "demo")
        kept = rw_auto.load_retrofit(folder / "retrofit-r1.json")
        self.assertEqual((kept["tentativa"], kept["ramo"], kept["commit"]), (1, first["ramo"], sealed["commit"]))
        self.assertEqual((kept["patch"], kept["versao"], kept["licoes"], kept["fases"]),
                         (sealed["patch"], sealed["versao"], [1], []))
        self.assertEqual(self.retrofit_json(rid), second)
        self.w.git(self.w.store, "rev-parse", "--verify", "-q", first["ramo"])
        self.w.git(self.w.store, "rev-parse", "--verify", "-q", second["ramo"])
        # Sem selo na tentativa 2, um segundo --redo devolve a mesma, e o prepare sem --redo também.
        self.assertEqual(rw_store.prepare(ctx, rid, "demo", redo=True), second)
        self.assertEqual(rw_store.prepare(ctx, rid, "demo"), second)
        self.assertFalse(rw_store.worktree_path(ctx, rid, "demo", 3).exists())

    def test_prepare_fetch_runs_in_batch_mode(self):
        # Final-F8: o fetch do `prepare` usa o ambiente de rede da porta (T9-ssh e T9-ssh2): nunca espera
        # credencial nem a senha da chave no terminal, e o GIT_SSH_COMMAND do dono fica.
        own = "ssh -o " + "IdentitiesOnly=yes"
        for inherited in (None, own):
            with self.subTest(inherited=inherited):
                rid = self.w.retro([{}], [{}])
                with mock.patch.dict(os.environ):
                    os.environ.pop("GIT_SSH_COMMAND", None)
                    os.environ.pop("GIT_SSH", None)
                    os.environ["GIT_TERMINAL_PROMPT"] = "1"
                    if inherited:
                        os.environ["GIT_SSH_COMMAND"] = inherited
                    with mock.patch.object(rw_store, "run", wraps=rw_store.run) as spy:
                        rw_store.prepare(self.ctx(), rid, "demo")
                fetches = [c for c in spy.call_args_list if "fetch" in [str(a) for a in c.args[0]]]
                self.assertEqual(len(fetches), 1, fetches)
                env = fetches[0].kwargs["env"]
                self.assertEqual(env["GIT_TERMINAL_PROMPT"], "0")
                self.assertEqual(env.get("GIT_SSH_COMMAND"), fs.expected_ssh(self.ctx().home, inherited))

    def test_prepare_and_gate_share_the_remote_env(self):
        # Item 11: o fetch do `prepare` e o da porta usam um só ambiente, o rw_store.remote_env.
        rid = self.w.retro([{}], [{}])
        ctx = self.ctx()
        with mock.patch.object(rw_store, "run", wraps=rw_store.run) as spy:
            rw_store.prepare(ctx, rid, "demo")
        fetches = [c for c in spy.call_args_list if "fetch" in [str(a) for a in c.args[0]]]
        self.assertEqual(len(fetches), 1, fetches)
        store = rw_store.store_clone(ctx)
        # assertTrue, não assertEqual: a mensagem do assertEqual imprimiria o ambiente de quem roda.
        self.assertTrue(fetches[0].kwargs["env"] == rw_store.remote_env(ctx, store))
        self.assertFalse("GIT_CONFIG_NOSYSTEM" in fetches[0].kwargs["env"])

    def test_inherited_git_location_and_config_do_not_redirect_prepare_or_seal(self):
        # Um hook do git exporta GIT_DIR; o HOME real tem a config de quem roda. Nenhum dos dois conta.
        trap_repo = self.w.tmp / "trap-repo"
        trap_repo.mkdir()
        self.w.git(trap_repo, "init", "-q")
        trap_home = self.w.tmp / "trap-home"
        hooks = trap_home / "hooks"
        hooks.mkdir(parents=True)
        marker = self.w.tmp / "hook-rodou"
        (hooks / "post-checkout").write_text(f"#!/bin/sh\ntouch '{marker}'\n", encoding="utf-8")
        (hooks / "post-checkout").chmod(0o755)
        (trap_home / ".gitconfig").write_text(f"[core]\n\thooksPath = {hooks}\n[i18n]\n\tlogOutputEncoding = ISO-8859-1\n",
                                              encoding="utf-8")
        rid = self.w.retro([{}], [{}])
        traps = {"GIT_DIR": str(trap_repo / ".git"), "GIT_WORK_TREE": str(trap_repo), "HOME": str(trap_home)}
        with mock.patch.dict(os.environ, traps):
            got = rw_store.prepare(self.ctx(), rid, "demo")
        self.assertFalse(marker.exists(), "o prepare leu a config do HOME herdado")
        wt = Path(got["worktree"])
        self.w.retrofit(wt, message="fix(demo): li" + chr(0xE7) + chr(0xE3) + "o")
        clean = rw_store.patch_id(wt)
        with mock.patch.dict(os.environ, traps):
            self.assertEqual(rw_store.patch_id(wt), clean)
            sealed = rw_store.seal(self.ctx(), rid, "demo", ["1"], [])
        self.assertEqual(sealed["commit"], self.w.git(wt, "rev-parse", "HEAD"))
        self.assertEqual(self.w.git(trap_repo, "rev-list", "--all"), "")

    # --- patch ---------------------------------------------------------------------------------

    def test_patch_id_survives_a_rebase_and_changes_with_content(self):
        rid, got = self.prepared()
        wt = Path(got["worktree"])
        self.w.retrofit(wt)
        first = rw_store.patch_id(wt)
        readme = (self.w.store / "README.md").read_text(encoding="utf-8")
        self.w.advance_origin({"README.md": readme.replace("# Loja fixture\n", "# Loja fixture\n\nUma nota.\n", 1)},
                              "docs: nota no README")
        self.w.git(wt, "fetch", "-q", "origin")
        self.w.git(wt, "rebase", "-q", "origin/main")
        self.assertEqual(rw_store.patch_id(wt), first, "o rebase mudou o patch")
        doc = wt / fs.PLUGINS["demo"]
        doc.write_text(doc.read_text(encoding="utf-8").replace(fs.LESSON_LINE, "- Releia o arquivo antes.\n"),
                       encoding="utf-8")
        self.w.git(wt, "commit", "-q", "-a", "--amend", "--no-edit")
        amended = rw_store.patch_id(wt)
        self.assertNotEqual(amended, first, "uma emenda de conteúdo não mudou o patch")
        for rel in rw_store.LIST_FILES:
            with open(wt / rel, "a", encoding="utf-8") as fh:
                fh.write("# linha nova\n")
        self.w.git(wt, "commit", "-q", "-a", "--amend", "--no-edit")
        self.assertEqual(rw_store.patch_id(wt), amended, "os arquivos de lista entraram no patch")
        self.w.git(wt, "commit", "-q", "--amend", "-m", "fix(demo): outra mensagem")
        self.assertNotEqual(rw_store.patch_id(wt), amended, "a mensagem do commit ficou fora do patch")

    def test_patch_id_binds_names_modes_and_raw_bytes(self):
        # Achados I1 e M2: um arquivo vazio novo e uma troca só de modo não têm linha `+`/`-`; dois bytes
        # diferentes fora do UTF-8 viram o mesmo U+FFFD se o diff for decodificado antes do hash.
        rid, got = self.prepared()
        wt = Path(got["worktree"])
        self.w.retrofit(wt)

        def amend():
            self.w.git(wt, "add", "-A")
            self.w.git(wt, "commit", "-q", "--amend", "--no-edit")
            return rw_store.patch_id(wt)

        base = rw_store.patch_id(wt)
        empty = wt / "plugins/demo/skills/demo/references" / (invented("vazio") + ".md")
        empty.parent.mkdir(parents=True)
        empty.write_bytes(b"")
        with_empty = amend()
        self.assertNotEqual(with_empty, base, "um arquivo vazio novo não mudou o patch")
        # Só o cabeçalho `diff --git` nomeia o arquivo vazio: renomeá-lo tem de mudar o patch.
        self.w.git(wt, "mv", str(empty), str(empty.with_name(invented("outro") + ".md")))
        renamed = amend()
        self.assertNotEqual(renamed, with_empty, "renomear um arquivo vazio não mudou o patch")
        self.w.git(wt, "mv", str(empty.with_name(invented("outro") + ".md")), str(empty))
        self.assertEqual(amend(), with_empty)
        if os.name != "nt":
            (wt / fs.PLUGINS["demo"]).chmod(0o755)
            with_mode = amend()
            self.assertNotEqual(with_mode, with_empty, "uma troca só de modo não mudou o patch")
            for rel in rw_store.LIST_FILES:
                (wt / rel).chmod(0o755)
            self.assertEqual(amend(), with_mode, "o modo de um arquivo de lista entrou no patch")
        raw = wt / "plugins/demo/skills/demo/references/bytes.txt"
        patches = []
        for byte in (0xFE, 0xFF):
            raw.write_bytes(b"antes " + bytes([byte]) + b" depois\n")
            patches.append(amend())
        self.assertNotEqual(patches[0], patches[1], "dois bytes fora do UTF-8 deram o mesmo patch")

    # --- camada 1 e termos ---------------------------------------------------------------------

    def layer1(self, rid, wt, ctx=None):
        """A camada 1 do commit de `wt`, com o portão da cópia dele (item 1), como o selo a roda."""
        with rw_store.clean_tree(self.ctx(), wt, "HEAD") as tools:
            return rw_store.layer1(ctx or self.ctx(), rid, wt, tools)

    def test_layer1_harvests_again_on_every_call(self):
        rid, got = self.prepared()
        wt = Path(got["worktree"])
        stale = self.w.data / rw_store.HARVEST_FILE
        stale.write_text("", encoding="utf-8")
        name = self.w.proj.name
        rel = "plugins/demo/skills/demo/references/nota.md"
        self.w.retrofit(wt, files={rel: f"Veja o {name} antes.\n"})
        found = self.layer1(rid, wt)
        self.assertTrue([f for f in found if f.startswith(f"{rel}:1: colheita")], found)
        # Ruling T7-race: a colheita da chamada é um arquivo só dela, removido depois; o partilhado fica.
        self.assertEqual(stale.read_text(encoding="utf-8"), "")
        self.assertEqual(sorted(p.name for p in self.w.data.iterdir() if "colheita" in p.name),
                         [rw_store.HARVEST_FILE])

    def test_layer1_reads_only_its_own_harvest(self):
        # Ruling T7-race: outra retro, com outro `cwd`, grava a colheita partilhada entre a colheita
        # desta chamada e o portão; o portão desta chamada lê a colheita dela, com o projeto da sessão.
        rid, got = self.prepared()
        wt = Path(got["worktree"])
        self.config(harvest_roots=[str(self.w.tmp / "vazio")])
        name = self.w.proj.name
        rel = "plugins/demo/skills/demo/references/nota.md"
        self.w.retrofit(wt, files={rel: f"Veja o {name} antes.\n"})
        shared = self.w.data / rw_store.HARVEST_FILE
        real_gate = rw_store._gate
        seen = []

        def racing_gate(tools, worktree, *args):
            shared.write_text("", encoding="utf-8")  # a outra retro, sem o projeto desta sessão
            extra = Path(args[args.index("--extra") + 1])
            seen.append((extra, extra.exists(), extra.stat().st_mode & 0o777 if os.name != "nt" else 0o600))
            return real_gate(tools, worktree, *args)

        with mock.patch.object(rw_store, "_gate", side_effect=racing_gate):
            found = self.layer1(rid, wt)
        self.assertTrue([f for f in found if f.startswith(f"{rel}:1: colheita")], found)
        (extra, existed, mode), = seen
        self.assertNotEqual(extra, shared)
        self.assertEqual((existed, mode, extra.parent), (True, 0o600, Path(os.path.realpath(self.w.data))))
        self.assertFalse(extra.exists(), "a colheita da chamada ficou para trás")

    def test_layer1_harvest_stays_outside_repos_and_leaves_nothing(self):
        rid, got = self.prepared()
        wt = Path(got["worktree"])
        self.w.retrofit(wt)
        # Uma falha no meio da colheita não deixa arquivo com nomes para trás.
        with mock.patch.object(rw_store, "harvest", side_effect=OSError("disco cheio")):
            with self.assertRaises(OSError):
                self.layer1(rid, wt)
        self.assertEqual([p.name for p in self.w.data.iterdir() if p.name.startswith(".colheita")], [])
        # A pasta de dados dentro de um repo: a colheita não grava nome em repo.
        inside = make_repo(self.w.env, self.w.tmp / "um-repo") / "dados"
        inside.mkdir()
        (inside / rw_auto.AUTO_DIR).symlink_to(self.w.data / rw_auto.AUTO_DIR)
        with self.assertRaises(rw_store.StoreError) as caught:
            self.layer1(rid, wt, rw.Context(home=self.w.home, data_dir=inside))
        self.assertIn("dentro de um repo", str(caught.exception))
        self.assertEqual(sorted(p.name for p in inside.iterdir()), [rw_auto.AUTO_DIR])

    def gate_stub(self, camada1, termos, root=None):
        """Um portão falso, que responde `camada1` e `termos`, em `root` (padrão: uma pasta do teste, fora
        do worktree). Devolve `root`, que se passa como `tools`."""
        root = Path(root or self.w.tmp / "portao-falso")
        (root / "scripts").mkdir(parents=True, exist_ok=True)
        (root / "scripts/stub.json").write_text(json.dumps({"camada1": camada1, "termos": termos}), encoding="utf-8")
        (root / rw_store.GATE).write_text(
            "import json, sys\nfrom pathlib import Path\n"
            "spec = json.loads((Path(__file__).parent / 'stub.json').read_text())\n"
            "rc, out = spec['termos' if '--termos' in sys.argv else 'camada1']\n"
            "sys.stdout.write(out)\nsys.exit(rc)\n", encoding="utf-8")
        return root

    def commit_gate_stub(self, wt, camada1, termos):
        """O portão falso no commit do ramo: o selo roda o portão da cópia do commit (item 1)."""
        self.gate_stub(camada1, termos, root=wt)
        self.w.git(wt, "add", "-A")
        self.w.git(wt, "commit", "-q", "--amend", "--no-edit")

    def test_layer1_and_new_terms_fail_closed_on_bad_gate_output(self):
        # Ruling C1: rc fora de {0, 1}, rc 0 com achado, rc 1 sem achado e JSON fora do formato são
        # StoreError, nunca uma lista vazia.
        rid, got = self.prepared()
        wt = Path(got["worktree"])
        self.w.retrofit(wt)
        ctx = self.ctx()
        finding = 'a.md:3: colheita "x"'
        good_terms = [0, json.dumps([{"termo": "x", "onde": "a.md:1", "contexto": "c"}])]
        tools = self.gate_stub([0, "ok: camada 1 limpa\n"], good_terms)
        self.assertEqual(rw_store.layer1(ctx, rid, wt, tools), [])
        self.assertEqual(rw_store.new_terms(wt, tools), json.loads(good_terms[1]))
        self.gate_stub([1, f"{finding}\n\n1 achado(s) na camada 1\n"], good_terms)
        self.assertEqual(rw_store.layer1(ctx, rid, wt, tools), [finding])
        bad_layer1 = {
            "rc 2": [2, "git falhou\n"],
            "rc 124": [124, ""],
            "rc 0 com achado": [0, f"{finding}\n\n1 achado(s) na camada 1\n"],
            "rc 0 vazio": [0, ""],
            "rc 1 sem achado": [1, "\n0 achado(s) na camada 1\n"],
            "rc 1 com lixo": [1, f"lixo\n{finding}\n\n2 achado(s) na camada 1\n"],
            "rc 1 sem resumo": [1, f"{finding}\n"],
        }
        for what, spec in bad_layer1.items():
            with self.subTest(camada1=what):
                self.gate_stub(spec, good_terms)
                with self.assertRaises(rw_store.StoreError) as caught:
                    rw_store.layer1(ctx, rid, wt, tools)
                self.assertIn("camada 1 inutilizavel", str(caught.exception))
        bad_terms = {
            "rc 2": [2, "[]"],
            "rc 1": [1, "[]"],
            "nao json": [0, "lista"],
            "nao lista": [0, "{}"],
            "chave faltando": [0, json.dumps([{"termo": "x"}])],
            "chave a mais": [0, json.dumps([{"termo": "x", "onde": "a", "contexto": "c", "outra": "d"}])],
            "valor nao texto": [0, json.dumps([{"termo": 1, "onde": "a", "contexto": "c"}])],
            "item nao objeto": [0, json.dumps(["x"])],
            "item lista": [0, json.dumps([["termo", "onde", "contexto"]])],
        }
        for what, spec in bad_terms.items():
            with self.subTest(termos=what):
                self.gate_stub([0, "ok: camada 1 limpa\n"], spec)
                with self.assertRaises(rw_store.StoreError) as caught:
                    rw_store.new_terms(wt, tools)
                self.assertIn("termos novos", str(caught.exception))
        # Pela CLI, o portão quebrado é rc 2 (erro), não rc 1 (recusa), e o selo não grava nada.
        self.commit_gate_stub(wt, [2, "git falhou\n"], good_terms)
        self.assert_rc2(self.cli("seal", rid, "demo", "--licoes", "1"), "camada 1 inutilizavel")
        self.commit_gate_stub(wt, [0, "ok: camada 1 limpa\n"], [2, ""])
        self.assert_rc2(self.cli("seal", rid, "demo", "--licoes", "1"), "termos novos")
        self.assertIsNone(self.retrofit_json(rid)["commit"])
        self.assertFalse((rw_auto.lote_dir(ctx, rid, "demo") / "termos-novos.json").exists())

    # --- a cópia do commit (item 1) -----------------------------------------------------------

    def test_clean_tree_is_the_commit_and_leaves_nothing(self):
        rid, got = self.prepared()
        wt = Path(got["worktree"])
        sha = self.w.retrofit(wt)
        (wt / "solto.txt").write_text("fora do commit\n", encoding="utf-8")
        data = self.w.tmp / ("dados com espa" + chr(0xE7) + "o")
        ctx = rw.Context(home=self.w.home, data_dir=data)
        listed = sorted(self.w.git(wt, "ls-tree", "-r", "--name-only", sha).splitlines())
        with rw_store.clean_tree(ctx, wt, sha) as tree:
            self.assertTrue(Path(tree).is_relative_to(data))
            self.assertEqual(sorted(p.relative_to(tree).as_posix() for p in Path(tree).rglob("*") if p.is_file()),
                             listed)
            self.assertFalse((Path(tree) / "solto.txt").exists())
            self.assertEqual((Path(tree) / fs.PLUGINS["demo"]).read_bytes(), (wt / fs.PLUGINS["demo"]).read_bytes())
        self.assertFalse(Path(tree).exists())
        self.assertEqual(list(data.iterdir()), [])
        with self.assertRaises(rw_store.StoreError) as caught:
            with rw_store.clean_tree(ctx, wt, "0" * 40):
                pass
        self.assertIn("arvore limpa", str(caught.exception))
        self.assertEqual(list(data.iterdir()), [])

    def test_seal_runs_the_gate_from_the_commit(self):
        rid, got = self.prepared()
        wt = Path(got["worktree"])
        name = self.w.proj.name
        rel = "plugins/demo/skills/demo/references/nota.md"
        self.w.retrofit(wt, files={rel: f"Veja o {name} antes.\n"})
        pyc = self.w.plant_blind_name_check(wt)
        self.assertTrue(pyc.is_file() and pyc.is_relative_to(wt), pyc)
        self.assertEqual(self.w.git(wt, "status", "--porcelain", "--untracked-files=all"), "")
        with mock.patch.dict(os.environ):
            os.environ.pop("PYTHONPYCACHEPREFIX", None)  # o executor grava o bytecode no worktree
            out = rw_store.seal(self.ctx(), rid, "demo", ["1"], [])
        self.assertTrue([f for f in out["camada1"] if f.startswith(f"{rel}:1: colheita")], out["camada1"])

    # --- seal ----------------------------------------------------------------------------------

    def test_seal_writes_terms_patch_and_reports_layer1(self):
        rid, got = self.prepared()
        wt = Path(got["worktree"])
        name = invented("selo")
        make_repo(self.w.env, self.w.tmp / "repos" / name)
        rel = "plugins/demo/skills/demo/references/nota.md"
        self.w.retrofit(wt, files={rel: f"Primeira linha.\nO {name} sabe.\n"})
        proc = self.cli("seal", rid, "demo", "--licoes", "1")
        self.assertEqual(proc.returncode, 1, proc.stderr)
        out = json.loads(proc.stdout)
        self.assertEqual(set(out), {"commit", "versao", "patch", "termos", "camada1"})
        self.assertTrue([f for f in out["camada1"] if f.startswith(f"{rel}:2: colheita") and name in f], out)
        terms = json.loads((rw_auto.lote_dir(self.ctx(), rid, "demo") / "termos-novos.json").read_text(encoding="utf-8"))
        self.assertEqual(set(terms), {"patch", "termos"})
        self.assertEqual(terms["patch"], rw_store.patch_id(wt))
        self.assertEqual(terms["termos"], out["termos"])
        self.assertIn(rel, [t["termo"] for t in terms["termos"]])  # o caminho novo é candidato da camada 2
        self.assertEqual(self.retrofit_json(rid)["patch"], terms["patch"])

    def test_seal_fills_retrofit_json_and_exits_0_when_clean(self):
        rid, got = self.prepared()
        wt = Path(got["worktree"])
        sha = self.w.retrofit(wt)
        proc = self.cli("seal", rid, "demo", "--licoes", "1,1", "--fases", "claim-check,refactoring")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        out = json.loads(proc.stdout)
        self.assertEqual((out["commit"], out["versao"], out["camada1"]), (sha, "1.0.1", []))
        saved = rw_auto.load_retrofit(rw_auto.lote_dir(self.ctx(), rid, "demo") / "retrofit.json")
        self.assertEqual((saved["licoes"], saved["fases"], saved["commit"], saved["versao"], saved["patch"]),
                         ([1], ["claim-check", "refactoring"], sha, "1.0.1", rw_store.patch_id(wt)))
        self.assertEqual({k: saved[k] for k in ("worktree", "ramo", "base", "tentativa")},
                         {k: got[k] for k in ("worktree", "ramo", "base", "tentativa")})

    def test_seal_holds_the_lessons_left_out(self):
        # Ruling C9: a lição do lote fora de --licoes ganha linha `segurado` por `executor-recusou`.
        rid, got = self.prepared(licoes=({}, {}))
        self.assertEqual(got["licoes"], [1, 2])
        self.w.retrofit(Path(got["worktree"]))
        for _ in range(2):
            rw_store.seal(self.ctx(), rid, "demo", ["1"], [])
        lines = [x for x in rw_auto.read_registry(self.ctx()) if x.get("item") == f"{rid}/demo#2"]
        self.assertEqual(len(lines), 1, lines)
        self.assertEqual((lines[0]["resultado"], lines[0]["motivo"], lines[0]["licoes"], lines[0]["lote"]),
                         ("segurado", "executor-recusou", [2], "demo"))
        self.assertFalse([x for x in rw_auto.read_registry(self.ctx()) if x.get("item") == f"{rid}/demo#1"])
        self.assertEqual(self.retrofit_json(rid)["licoes"], [1])

    def test_seal_refuses_a_lesson_from_another_lote(self):
        rid, got = self.prepared(licoes=({}, {"muda_description": True}))
        self.w.retrofit(Path(got["worktree"]))
        self.assert_rc2(self.cli("seal", rid, "demo", "--licoes", "2"), "nao e do lote")
        self.assertIsNone(self.retrofit_json(rid)["commit"])
        self.assertEqual([x for x in rw_auto.read_registry(self.ctx()) if x.get("motivo") == "executor-recusou"], [])

    def test_seal_refuses_an_unknown_phase(self):
        rid, got = self.prepared()
        self.w.retrofit(Path(got["worktree"]))
        self.assert_rc2(self.cli("seal", rid, "demo", "--licoes", "1", "--fases", "claim-check,revisao-geral"),
                        "revisao-geral")
        self.assertIsNone(self.retrofit_json(rid)["commit"])

    def test_seal_refuses_bad_lessons_an_empty_branch_and_a_missing_version(self):
        rid, got = self.prepared()
        wt = Path(got["worktree"])
        ctx = self.ctx()
        with self.assertRaises(rw_store.StoreError) as caught:
            rw_store.seal(ctx, rid, "demo", ["1"], [])
        self.assertIn("nao tem commit", str(caught.exception))
        self.w.retrofit(wt)
        for licoes, needle in ((["x"], "fora do formato"), (["0"], "fora do formato"), ([], "sem nenhuma")):
            with self.subTest(licoes=licoes):
                with self.assertRaises(rw_store.StoreError) as caught:
                    rw_store.seal(ctx, rid, "demo", licoes, [])
                self.assertIn(needle, str(caught.exception))
        self.assert_rc2(self.cli("seal", rid, "demo", "--licoes", ","), "sem nenhuma")
        (wt / "plugins/demo/.claude-plugin/plugin.json").write_text("{}", encoding="utf-8")
        with self.assertRaises(rw_store.StoreError) as caught:
            rw_store.seal(ctx, rid, "demo", ["1"], [])
        self.assertIn("sem `version`", str(caught.exception))
        self.assertIsNone(self.retrofit_json(rid)["commit"])


if __name__ == "__main__":
    unittest.main()
