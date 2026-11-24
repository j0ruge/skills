"""A loja fixture: um `origin` `--bare` e um clone, os dois sob o diretório temporário.

Nenhum teste toca a loja real nem a rede. A `StoreWorld` herda o HOME fixture do `World` e monta, a
partir das cópias dos scripts da loja real, uma loja pequena que passa nas portas reais:

- `demo` e `demo2` (com skill) e `demo-cmd` (só de comandos), todos na 1.0.0, com `plugin.json`,
  `CHANGELOG.md`, testes, bloco no `marketplace.json` e linha no README;
- na raiz, os `scripts/` da loja, o auditor da `skill-quality-audit` (sem o `SKILL.md` dele), o
  `audit_gate.py` do `retrofit-skill` e um `tests/test_root.py` mínimo. Sem `install.py`: as
  verificações 5 e 8 do `validate-versions.py` se pulam sem ele. O catálogo Codex sai vazio;
- em cada arquivo que os plugins dividem, uma linha intacta entre os blocos de dois plugins, para
  que os lotes de dois plugins não editem linhas vizinhas e se rebaseiem sem conflito.

Todo comando git da fixture roda com `self.env`: sem as variáveis de localização do git herdadas do
ambiente e com o HOME fixture, para nunca ler o `.gitconfig` real.
"""
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import time
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from test_retrofit_watch import GIT_ENV, World  # noqa: E402
import rw_auto  # noqa: E402  (o test_retrofit_watch põe scripts/ no path)
import rw_store  # noqa: E402

AUDITOR = "plugins/skill-quality-audit/skills/skill-quality-audit/scripts/audit_skill_quality.py"
AUDIT_GATE = "plugins/retrofit-skill/scripts/audit_gate.py"
CATALOG = ".agents/plugins/marketplace.json"
# Nome -> o arquivo que guarda o `metadata.version` do plugin (o SKILL.md ou o comando).
PLUGINS = {
    "demo": "plugins/demo/skills/demo/SKILL.md",
    "demo-cmd": "plugins/demo-cmd/commands/demo-cmd.md",
    "demo2": "plugins/demo2/skills/demo2/SKILL.md",
}
VERSION = "1.0.0"
# Do GIT_ENV do test_retrofit_watch, só o que não vem do ambiente: o autor e o git sem config de sistema.
GIT_IDENTITY = ("GIT_AUTHOR_NAME", "GIT_AUTHOR_EMAIL", "GIT_COMMITTER_NAME", "GIT_COMMITTER_EMAIL",
                "GIT_CONFIG_NOSYSTEM")
LESSON_LINE = "- Releia o arquivo gerado antes do commit.\n"


def find_store_root(start=HERE):
    """A raiz da loja acima de `start`, ou None (a cópia instalada no cache não traz os scripts)."""
    for parent in Path(start).resolve().parents:
        if (parent / "scripts/validate-versions.py").is_file() and (parent / ".claude-plugin/marketplace.json").is_file():
            return parent
    return None


STORE_ROOT = find_store_root()
HAS_YAML = importlib.util.find_spec("yaml") is not None


def store_skip_reason(root, has_yaml):
    """Por que pular um teste que monta a loja fixture, ou None."""
    if root is None:
        return "cópia instalada: a raiz da loja não está acima deste arquivo"
    if not has_yaml:
        return "falta o PyYAML, que o validate-versions.py exige"
    return None


def requires_store(test):
    reason = store_skip_reason(STORE_ROOT, HAS_YAML)
    return unittest.skip(reason)(test) if reason else test


def _clean_env(home):
    """O ambiente do git e dos scripts da fixture: sem GIT_DIR, GIT_WORK_TREE, GIT_INDEX_FILE nem
    outra variável do git herdada (um hook de pré-commit as exporta), sem o CLAUDE_PLUGIN_DATA herdado
    (o script o lê, e ele apontaria a pasta de dados real) e com o HOME fixture."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_") and k != "CLAUDE_PLUGIN_DATA"}
    env.update({k: GIT_ENV[k] for k in GIT_IDENTITY})
    env.update(HOME=str(home), XDG_CONFIG_HOME=str(Path(home) / ".config"), PYTHONDONTWRITEBYTECODE="1")
    return env


def expected_ssh(home, inherited):
    """O GIT_SSH_COMMAND que o `network_env` deixa no git de rede, com a config de sistema de quem roda
    (Final-F4). O Git for Windows grava `core.sshCommand` nela quando a instalação escolhe "Use external
    OpenSSH", e o `network_env` lê essa config (resposta 3 do dono): com o valor lá, ele não põe o
    BatchMode e a variável fica ausente. O teste lê a config com o mesmo ambiente do código."""
    if inherited:
        return inherited
    rc, out = rw_store.run(["git", "config", "--system", "--get", "core.sshCommand"],
                           env=rw_store.git_env(home=home))
    return None if rc == 0 and out.strip() else rw_store.BATCH_SSH


def _description(plugin):
    kind = "command" if PLUGINS[plugin].endswith(f"commands/{plugin}.md") else "skill"
    return f"Demo {kind} of the fixture store ({plugin}). Triggers — {plugin}, fixture."


def _dump(data):
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"


def _replace_once(path, old, new):
    text = path.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise ValueError(f"{path}: esperava `{old.strip()}` uma vez, achou {text.count(old)}")
    path.write_text(text.replace(old, new), encoding="utf-8")


class StoreWorld(World):
    """O `World` com uma loja de verdade: `origin` (bare), `store` (o clone que faz o papel do
    checkout compartilhado) e `other` (o outro clone, de onde `advance_origin` empurra)."""

    def __init__(self):
        super().__init__()
        self.env = _clean_env(self.home)
        self.origin = self.tmp / "origin.git"
        self.other = self.tmp / "other"
        self.store = self.tmp / "store"
        self.git(self.tmp, "init", "-q", "--bare", str(self.origin))
        self.git(self.origin, "symbolic-ref", "HEAD", "refs/heads/main")
        self.other.mkdir()
        self.git(self.other, "init", "-q")
        self.git(self.other, "symbolic-ref", "HEAD", "refs/heads/main")
        self._seed(self.other)
        self.git(self.other, "add", "-A")
        self.git(self.other, "commit", "-q", "-m", "feat: loja fixture")
        self.git(self.other, "remote", "add", "origin", str(self.origin))
        self.git(self.other, "push", "-q", "-u", "origin", "main")
        self.git(self.tmp, "clone", "-q", str(self.origin), str(self.store))
        # O `World.repo` nasce com a URL real da loja como `origin`: nenhum push pode chegar lá.
        self.git(self.repo, "remote", "set-url", "origin", str(self.origin))
        config = self.home / ".claude/retrofit-watch.json"
        config.write_text(json.dumps({"mode": "auto", "store": str(self.store)}), encoding="utf-8")

    # --- git e scripts -------------------------------------------------------------------------

    def git(self, cwd, *args, env=None, strip=True):
        """Roda o git no ambiente limpo e devolve a saída sem o branco das pontas; com `strip=False`, só
        sem a quebra de linha do fim. Erro levanta."""
        proc = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, env=env or self.env,
                              encoding="utf-8", errors="replace")
        if proc.returncode:
            raise subprocess.CalledProcessError(proc.returncode, ["git", *args], proc.stdout, proc.stderr)
        return proc.stdout.strip() if strip else proc.stdout.removesuffix("\n")

    def run_script(self, repo, script, *args):
        """Um script Python da árvore `repo`, com `repo` como cwd. Devolve o CompletedProcess."""
        return subprocess.run([sys.executable, str(Path(repo) / script), *args], cwd=str(repo),
                              capture_output=True, env=self.env, encoding="utf-8", errors="replace")

    def run_tests(self, repo, tests):
        """`unittest discover` numa pasta de testes da árvore `repo`."""
        return subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", tests, "-p", "test_*.py"],
                              cwd=str(repo), capture_output=True, env=self.env, encoding="utf-8",
                              errors="replace")

    # --- a árvore inicial ----------------------------------------------------------------------

    def _seed(self, root):
        for source in sorted((STORE_ROOT / "scripts").iterdir()):
            if source.is_file():
                (root / "scripts").mkdir(exist_ok=True)
                shutil.copy2(source, root / "scripts" / source.name)
        for rel in (AUDITOR, AUDIT_GATE):
            (root / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(STORE_ROOT / rel, root / rel)
        (root / ".gitignore").write_text("__pycache__/\n", encoding="utf-8")
        (root / "tests").mkdir()
        (root / "tests/test_root.py").write_text(
            "import json\nimport unittest\nfrom pathlib import Path\n\n"
            "ROOT = Path(__file__).resolve().parents[1]\n\n\n"
            "class RootTest(unittest.TestCase):\n"
            "    def test_marketplace_lists_the_plugins(self):\n"
            "        data = json.loads((ROOT / '.claude-plugin/marketplace.json').read_text(encoding='utf-8'))\n"
            "        self.assertTrue(data['plugins'])\n", encoding="utf-8")
        entries, lines = [], []
        for plugin in PLUGINS:
            self._seed_plugin(root, plugin)
            entries.append({"name": plugin, "source": f"./plugins/{plugin}", "version": VERSION,
                            "description": _description(plugin), "category": "development",
                            "platforms": ["claude-code"]})
            lines.append(f"- **{plugin}** {VERSION} — {_description(plugin)}\n")
        (root / ".claude-plugin").mkdir()
        (root / ".claude-plugin/marketplace.json").write_text(_dump({
            "name": "chewiesoft-marketplace", "owner": {"name": "Chewiesoft"},
            "metadata": {"description": "Loja fixture dos testes.", "version": "0.1.0"},
            "plugins": entries}), encoding="utf-8")
        # Uma linha em branco entre as linhas de dois plugins: duas edições nunca são vizinhas.
        (root / "README.md").write_text("# Loja fixture\n\n## Plugins\n\n" + "\n".join(lines), encoding="utf-8")
        proc = self.run_script(root, "scripts/codex-marketplace.py", "--write", "--root", str(root))
        if proc.returncode:
            raise RuntimeError(f"catálogo Codex da fixture: {proc.stderr}")

    def _seed_plugin(self, root, plugin):
        base = root / "plugins" / plugin
        doc = root / PLUGINS[plugin]
        doc.parent.mkdir(parents=True)
        (base / ".claude-plugin").mkdir()
        manifest = {"name": plugin, "description": _description(plugin), "author": {"name": "Chewiesoft"},
                    "version": VERSION, "category": "development", "platforms": ["claude-code"]}
        if doc.name == "SKILL.md":
            manifest["skills"] = "./skills"
            doc.write_text(f'---\nname: {plugin}\ndescription: "{_description(plugin)}"\nlicense: MIT\n'
                           f'metadata:\n  version: "{VERSION}"\n---\n\n# {plugin}\n\n'
                           f"Uma skill de exemplo da loja fixture.\n\n## Armadilhas\n\n"
                           f"- Confira a saída antes de seguir.\n", encoding="utf-8")
            tests = doc.parent / "tests"
        else:
            manifest["commands"] = "./commands"
            doc.write_text(f"---\ndescription: {_description(plugin)}\nmetadata:\n  version: {VERSION}\n---\n\n"
                           f"# {plugin}\n\nUm comando de exemplo da loja fixture.\n", encoding="utf-8")
            tests = base / "tests"
        (base / ".claude-plugin/plugin.json").write_text(_dump(manifest), encoding="utf-8")
        (base / "CHANGELOG.md").write_text(f"# Changelog — {plugin}\n\n## [{VERSION}] — 2026-11-01\n\n"
                                           "- Primeira versão.\n", encoding="utf-8")
        tests.mkdir()
        module = plugin.replace("-", "_")
        (tests / f"test_{module}.py").write_text(
            "import unittest\nfrom pathlib import Path\n\n"
            f"DOC = Path(__file__).resolve().parents[1] / {Path(os.path.relpath(doc, tests.parent)).as_posix()!r}\n\n\n"
            f"class {module.title().replace('_', '')}Test(unittest.TestCase):\n"
            "    def test_doc_has_its_version(self):\n"
            "        self.assertIn('version:', DOC.read_text(encoding='utf-8'))\n", encoding="utf-8")

    # --- auxiliares dos testes -----------------------------------------------------------------

    def worktree(self, branch, base="origin/main"):
        """Um worktree do `store` num ramo novo, sob o diretório temporário."""
        path = self.tmp / "wt" / branch
        path.parent.mkdir(exist_ok=True)
        self.git(self.store, "worktree", "add", "-q", "-b", branch, str(path), base)
        return path

    def retrofit(self, wt, plugin="demo", files=None, message=None, version="1.0.1",
                 trailer="Retrofit-Mode: autonomous"):
        """Um commit de retrofit completo no worktree: a lição (`files`, ou uma linha nova no
        SKILL.md ou no comando), `plugin.json`, `metadata.version`, `CHANGELOG`, `marketplace.json`
        e README. Devolve o sha."""
        wt = Path(wt)
        manifest_path = wt / "plugins" / plugin / ".claude-plugin/plugin.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        old = manifest["version"]
        doc = wt / PLUGINS[plugin]
        if files is None:
            with open(doc, "a", encoding="utf-8") as fh:
                fh.write(LESSON_LINE)
        for rel, text in (files or {}).items():
            (wt / rel).parent.mkdir(parents=True, exist_ok=True)
            (wt / rel).write_text(text, encoding="utf-8")
        manifest["version"] = version
        manifest_path.write_text(_dump(manifest), encoding="utf-8")
        quote = '"' if doc.name == "SKILL.md" else ""
        _replace_once(doc, f"\n  version: {quote}{old}{quote}\n", f"\n  version: {quote}{version}{quote}\n")
        changelog = wt / "plugins" / plugin / "CHANGELOG.md"
        _replace_once(changelog, f"# Changelog — {plugin}\n\n",
                      f"# Changelog — {plugin}\n\n## [{version}] — {time.strftime('%Y-%m-%d')}\n\n"
                      "- Lição da sessão.\n\n")
        catalog_path = wt / ".claude-plugin/marketplace.json"
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        for entry in catalog["plugins"]:
            if entry["name"] == plugin:
                entry["version"] = version
        catalog_path.write_text(_dump(catalog), encoding="utf-8")
        _replace_once(wt / "README.md", f"- **{plugin}** {old} ", f"- **{plugin}** {version} ")
        self.git(wt, "add", "-A")
        extra = ["--trailer", trailer] if trailer else []
        self.git(wt, "commit", "-q", "-m", message or f"fix({plugin}): v{version}", *extra)
        return self.git(wt, "rev-parse", "HEAD")

    def ignore(self, wt, pattern):
        """Ignora `pattern` pela linha nova no `info/exclude` do repo de `wt` (o comum aos worktrees)."""
        path = Path(self.git(wt, "rev-parse", "--path-format=absolute", "--git-path", "info/exclude"))
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(pattern + "\n")

    def plant_blind_name_check(self, wt):
        """Um `.pyc` do `check-private-names.py` de `wt` com o `candidatos` vazio, no caminho do
        `cache_from_source` sem `PYTHONPYCACHEPREFIX` (o `__pycache__/` do worktree, como no executor), que o
        import do portão lê sem conferir a fonte (UNCHECKED_HASH). O `__pycache__/` é ignorado pelo
        `.gitignore` da loja. Quem chama tira o PYTHONPYCACHEPREFIX do ambiente do portão. Devolve o caminho."""
        import py_compile
        import tempfile
        source = Path(wt) / "scripts" / "check-private-names.py"
        prefix, sys.pycache_prefix = sys.pycache_prefix, None
        try:
            target = Path(importlib.util.cache_from_source(str(source)))
        finally:
            sys.pycache_prefix = prefix
        blind = source.read_text(encoding="utf-8") + "\n\ndef candidatos(linha):\n    return iter(())\n"
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / source.name
            src.write_text(blind, encoding="utf-8")
            py_compile.compile(str(src), cfile=str(target), dfile=str(source), doraise=True,
                               invalidation_mode=py_compile.PycInvalidationMode.UNCHECKED_HASH)
        return target

    def advance_origin(self, files, message, date=None):
        """Um commit no `origin` vindo de outro clone (o `other`). `date` (ISO) fixa a data."""
        self.git(self.other, "fetch", "-q", "origin")
        self.git(self.other, "reset", "-q", "--hard", "origin/main")
        for rel, text in files.items():
            (self.other / rel).parent.mkdir(parents=True, exist_ok=True)
            (self.other / rel).write_text(text, encoding="utf-8")
        self.git(self.other, "add", "-A")
        env = dict(self.env, GIT_AUTHOR_DATE=date, GIT_COMMITTER_DATE=date) if date else None
        self.git(self.other, "commit", "-q", "-m", message, env=env)
        self.git(self.other, "push", "-q", "origin", "HEAD:main")
        return self.git(self.other, "rev-parse", "HEAD")

    def origin_main(self):
        return self.git(self.origin, "rev-parse", "main")

    def shared_state(self):
        """(HEAD, ramo atual, `status --porcelain`) do clone compartilhado. O status perde só a quebra de
        linha do fim: a coluna da esquerda (o índice) começa com espaço quando só a árvore mudou."""
        return (self.git(self.store, "rev-parse", "HEAD"), self.git(self.store, "branch", "--show-current"),
                self.git(self.store, "status", "--porcelain", strip=False))

    def assert_fixture_origin(self, path):
        """AssertionError quando o `origin` do repo em `path`, de busca ou de push, não está sob o
        diretório temporário. O `push` da fixture chama isto antes de empurrar."""
        for args in (("remote", "get-url", "origin"), ("remote", "get-url", "--push", "origin")):
            try:
                url = self.git(path, *args)
            except subprocess.CalledProcessError:
                raise AssertionError(f"{path}: sem origin") from None
            if not os.path.isabs(url) or not Path(os.path.realpath(url)).is_relative_to(self.tmp):
                raise AssertionError(f"{path}: origin fora da fixture: {url}")

    def retro(self, licoes, pareceres, skills=("demo",)):
        """Grava `pedido.json`, `licoes.json` e `veredito.json` de uma retro e devolve o `id`. Cada
        lição e cada parecer é um dict parcial sobre um padrão que a triagem publica; `n` segue a
        ordem. Um lote por plugin (D2): `skills` são os plugins do pedido. `pareceres=None` não
        grava o `veredito.json`."""
        ctx = self.ctx()
        (ctx.data_dir / rw_auto.AUTO_DIR).mkdir(parents=True, exist_ok=True)
        now = time.time()
        while True:
            rid = rw_auto.new_id("s1", now)
            folder = rw_auto.retro_dir(ctx, rid)
            try:
                folder.mkdir()
                break
            except FileExistsError:
                now += 1
        pedido = {"id": rid, "sessao": "s1", "ts": int(now), "transcript": str(self.transcript),
                  "cwd": str(self.proj), "modo": "auto",
                  "skills": [{"key": f"full:{p}", "plugin": p, "label": p,
                              "skills": [p] if PLUGINS[p].endswith("SKILL.md") else []} for p in skills]}
        rows = []
        for n, over in enumerate(licoes, start=1):
            plugin = over.get("plugin", skills[0])
            rows.append({"n": n, "plugin": plugin, "skill": plugin, "tipo": "pitfall",
                         "evidencia": {"texto": "o comando falhou", "transcript": str(self.transcript),
                                       "entrada": "1"},
                         "padrao": "conferir a saída", "resolveu": "a releitura resolveu",
                         "muda_description": False, **over})
        (folder / "pedido.json").write_text(_dump(pedido), encoding="utf-8")
        (folder / "licoes.json").write_text(_dump({"id": rid, "licoes": rows}), encoding="utf-8")
        if pareceres is not None:
            verdicts = [{"n": n, "evidencia_confere": True, "coberta": None, "generica": True,
                         "procede": "procede", "basta_o_transcript": None, "nao_capturar": None,
                         "nota": "", **over} for n, over in enumerate(pareceres, start=1)]
            (folder / "veredito.json").write_text(_dump({"id": rid, "base": self.origin_main(),
                                                         "licoes": verdicts}), encoding="utf-8")
        return rid
