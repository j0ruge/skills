"""Regras das pastas de rascunho (~/.wt): o que cada entrada guarda e se aquilo tem outra cópia.

O scratch_scan.py monta o plano com estas funções, e o scratch_apply.py as chama de novo antes de
mover. A prova aqui é outra que a das branches: não há merge para provar, e sim que nada se perde.
Uma entrada sai quando tudo o que guarda tem outra cópia (no histórico de um --repo, byte a byte num
destino dado, no remoto de um clone) ou se recria; fica quando algo vivo a cita, quando é recente ou
quando um processo está dentro. Nada aqui escreve: o `gh api` e o git só leem.
"""
from __future__ import annotations

import filecmp
import glob
import hashlib
import json
import os
import re
import stat
import subprocess
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

import housekeeping as hk

PLAN_VERSION = 1
# A quarentena fica na própria raiz: o mv é um rename no mesmo disco, e o `desfazer` é outro.
LIXEIRA = ".housekeeping-lixeira"
RECENTE_DIAS = 7
# O nome solto só conta como citação a partir deste tamanho; abaixo, só pelo caminho (`.wt/<nome>`),
# porque um nome curto (`api-sonda`) casaria com prosa comum.
NOME_MINIMO = 12
TEXTO = (".md", ".txt", ".json", ".yaml", ".yml", ".toml")
TETO_TEXTO = 2 * 1024 * 1024
# Acima disto o arquivo não é conferido contra o histórico dos --repo: fica sem prova.
TETO_HASH = 32 * 1024 * 1024
TETO_MENSAGEM = 64 * 1024
# Fora de um repo, build/ e dist/ não provam que se recriam: nenhum .gitignore nem projeto os declara.
SO_NO_REPO = {"build", "dist", "htmlcov", ".coverage"}
# E o node_modules só se recria igual com o lockfile ao lado. Em 2026-11-17, o de um bundle extraído
# para estudo (102,8 MB, 14985 arquivos) tinha package.json e nenhum lockfile.
LOCKFILES = ("package-lock.json", "npm-shrinkwrap.json", "yarn.lock", "pnpm-lock.yaml", "bun.lock", "bun.lockb")
# O que o retrofit-skill grava no `mktemp -d`: a saída do auditor e o diff do gate.
BASELINE = {"antes.json", "depois.json", "diff.txt"}
SAEM = ("delete", "review")
_SHA = re.compile(r"(?<![0-9A-Za-z])([0-9a-f]{7,40})(?![0-9A-Za-z])")
_REF_URL = re.compile(r"github\.com/([\w.-]+/[\w.-]+)/(?:pull|issues)/(\d+)")
_REF_SLUG = re.compile(r"(?<![\w/.-])([\w.-]+/[\w.-]+)#(\d+)\b")
_REF_NUM = re.compile(r"(?<![\w&/#])#(\d{1,6})\b|\bPRs?\s+(\d{1,6})\b")
_HANDOFF = re.compile(r"^handoff-(.+?)-\d{4}-\d{2}-\d{2}")


class ScratchError(RuntimeError):
    """Uso inválido (raiz, plano, --repo, --igual); as CLIs transformam isso em rc 2."""


@dataclass
class Item:
    """Uma entrada da raiz (`entry`) ou um pedaço dela que sai sozinho (`sub`), com a decisão."""
    name: str
    kind: str
    type: str
    decision: str
    reason: str
    proof: str = ""
    evidence: list = field(default_factory=list)
    files: int = 0
    kb: int = 0
    size: int = 0
    newest: float = 0.0


@dataclass
class Repo:
    """Um --repo: o caminho, a default do remoto (`origin/HEAD`) e o owner/repo do GitHub."""
    path: str
    ref: str
    sha: str
    slug: str


def _commit(repo, ref: str) -> str:
    return hk.run_git(repo, "rev-parse", "--verify", "-q", f"{ref}^{{commit}}").stdout.strip()


def load_repo(path) -> Repo:
    """O --repo pelo topo dele e a default do remoto: o `origin/HEAD`, ou a branch que o remoto
    anuncia (`ls-remote`), ou o HEAD local em último caso (o relatório mostra qual). Em 2026-11-17,
    dois dos quatro clones não tinham `origin/HEAD`, e o HEAD de um deles estava 269 commits atrás do
    `origin/main` (`git rev-list --count HEAD..origin/main`)."""
    try:
        top = hk.git(path, "rev-parse", "--show-toplevel").strip()
    except (hk.GitError, OSError) as e:
        raise ScratchError(f"--repo {path} não é um repo git ({e})") from e
    ref, sha = "origin/HEAD", _commit(top, "refs/remotes/origin/HEAD")
    if not sha:
        try:
            branch = hk._remote_default(top, "origin")
            ref, sha = f"origin/{branch}", _commit(top, f"refs/remotes/origin/{branch}")
        except hk.GitError:
            sha = ""
    if not sha:
        ref, sha = "HEAD", _commit(top, "HEAD")
    url = hk.run_git(top, "config", "--get", "remote.origin.url").stdout.strip()
    return Repo(top, ref, sha, hk.github_slug(url))


def refs_do_remoto(repo):
    """(vivas, sem_fetch), ou None se o remoto não responde. `vivas` são as refs remote-tracking do
    `origin` (ou do primeiro remoto) cuja branch existe no remoto agora (`ls-remote`) com a ponta
    igual, ou à frente, da local. A ref de uma branch apagada no remoto não é cópia: o próximo
    `fetch --prune` a leva, e o que só ela alcança vai junto. É o mesmo caso do "único ponteiro
    local" do fluxo das branches. `sem_fetch` são as que também não provam porque a ponta remota
    não está no repo: o remoto andou depois do último fetch, e sem o commit não há como saber se
    ele avançou ou reescreveu. Elas são ditas, nunca contadas: em 2026-11-24 outra sessão empurrou
    entre o fetch e o scan, a única ref viva do repo caiu calada, e 551 arquivos que estavam no
    histórico saíram sem prova."""
    remotes = hk.run_git(repo, "remote").stdout.split()
    if not remotes:
        return None
    name = "origin" if "origin" in remotes else remotes[0]
    ls = hk.run_git(repo, "ls-remote", "--heads", name)
    if ls.returncode:
        return None
    heads = {}
    for line in ls.stdout.splitlines():
        sha, _, ref = line.partition("\t")
        heads[ref.removeprefix("refs/heads/")] = sha
    prefix = f"refs/remotes/{name}/"
    vivas, sem_fetch = [], []
    for ref in hk.run_git(repo, "for-each-ref", "--format=%(refname)", prefix).stdout.split():
        remote_tip = heads.get(ref.removeprefix(prefix))
        tip = _commit(repo, ref)
        if not (remote_tip and tip):
            continue
        if tip == remote_tip:
            vivas.append(ref)
        elif not hk.has_commit(repo, remote_tip):
            sem_fetch.append(ref)
        elif hk.is_ancestor(repo, tip, remote_tip):
            vivas.append(ref)
    return vivas, sem_fetch


def refs_vivas(repo):
    """As refs vivas de `refs_do_remoto`, ou None se o remoto não responde."""
    r = refs_do_remoto(repo)
    return None if r is None else r[0]


def nomes_curtos(refs) -> str:
    """`refs/remotes/origin/main` → `origin/main`, separados por vírgula."""
    return ", ".join(r.removeprefix("refs/remotes/") for r in refs)


def conta(path) -> tuple:
    """(arquivos, KiB em disco, bytes, mtime mais novo) sem seguir symlink; o mtime inclui as pastas."""
    st = os.lstat(path)
    newest = st.st_mtime
    if not stat.S_ISDIR(st.st_mode):
        return 1, _disco(st) // 1024, st.st_size, newest
    files = blocks = size = 0
    for top, dirs, names in os.walk(path):
        for name in dirs:
            try:
                newest = max(newest, os.lstat(os.path.join(top, name)).st_mtime)
            except OSError:
                continue
        for name in names:
            try:
                s = os.lstat(os.path.join(top, name))
            except OSError:
                continue
            files, blocks, size = files + 1, blocks + _disco(s), size + s.st_size
            newest = max(newest, s.st_mtime)
    return files, blocks // 1024, size, newest


def _disco(st) -> int:
    blocks = getattr(st, "st_blocks", None)
    return blocks * 512 if blocks is not None else st.st_size


def processo_dentro(path, procs) -> str:
    """O primeiro processo com o diretório atual dentro de `path`, como `pid (comando)`, ou ""."""
    real = os.path.realpath(path)
    for pid, (cwd, cmd) in sorted((procs or {}).items()):
        if cwd == real or cwd.startswith(real + os.sep):
            return f"{pid} ({cmd[:60]})"
    return ""


def regen_solto(path) -> bool:
    """Pasta que se recria, fora de um repo: a regra da `hk.regeneravel` menos o build/ e o dist/,
    e o node_modules só com um lockfile na pasta-mãe."""
    path = os.path.normpath(path)
    name = os.path.basename(path)
    if name in SO_NO_REPO:
        return False
    if name == "node_modules":
        return any(os.path.isfile(os.path.join(os.path.dirname(path), f)) for f in LOCKFILES)
    return hk.regeneravel(path)


def clone_limpo(path) -> tuple:
    """(True, de onde) para o clone sem nada que só exista nele: árvore limpa (o ignorado, só o
    regenerável), sem stash, e o HEAD e as branches contidos nas refs do remoto."""
    top = hk.run_git(path, "rev-parse", "--show-toplevel")
    if top.returncode or not hk.same_path(top.stdout.strip(), path):
        return False, "o .git não abre como repo"
    remotes = hk.run_git(path, "remote").stdout.split()
    if not remotes:
        return False, "sem remoto"
    st = hk.run_git(path, "status", "--porcelain", "--untracked-files=all", "--ignored")
    if st.returncode:
        return False, "o git status falhou"
    sujo = [ln[3:] for ln in st.stdout.splitlines()
            if not (ln.startswith("!! ") and hk.regeneravel(os.path.join(path, ln[3:].rstrip("/"))))]
    if sujo:
        return False, f"árvore suja ({len(sujo)}: {', '.join(sujo[:3])})"
    if hk.run_git(path, "rev-parse", "-q", "--verify", "refs/stash").returncode == 0:
        return False, "tem stash"
    remoto = refs_do_remoto(path)
    if remoto is None:
        return False, "o remoto não respondeu (ls-remote)"
    vivas, sem_fetch = remoto
    andou = (f"o remoto andou depois do último fetch do clone ({nomes_curtos(sem_fetch)}): "
             "git fetch nele") if sem_fetch else ""
    if not vivas:
        return False, andou or "nenhuma branch do clone existe mais no remoto"
    fora = hk.run_git(path, "rev-list", "--count", "HEAD", "--branches", "--not", *vivas)
    if fora.returncode or fora.stdout.strip() != "0":
        return False, (f"{fora.stdout.strip() or '?'} commit(s) fora das branches que o remoto tem"
                       + (f"; {andou}" if andou else ""))
    url = hk.run_git(path, "config", "--get", f"remote.{remotes[0]}.url").stdout.strip()
    return True, f"tudo o que tem está no remoto ({url})"


def compara(src, dst) -> tuple:
    """(arquivos de `src`, os que não têm cópia igual byte a byte em `dst` no mesmo caminho)."""
    total, faltam = 0, []
    for top, _dirs, names in os.walk(src):
        for name in names:
            path = os.path.join(top, name)
            total += 1
            if os.path.islink(path):
                continue
            other = os.path.join(dst, os.path.relpath(path, src))
            if not (os.path.isfile(other) and not os.path.islink(other)
                    and os.path.getsize(other) == os.path.getsize(path)
                    and filecmp.cmp(path, other, shallow=False)):
                faltam.append(path)
    return total, faltam


def _ler(path) -> str:
    try:
        if os.path.getsize(path) > TETO_TEXTO:
            return ""
        with open(path, encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError:
        return ""


def _norm_msg(text: str) -> str:
    return "\n".join(line.rstrip() for line in text.strip().splitlines())


def _lista(xs, k=2) -> str:
    xs = list(xs)
    return ", ".join(xs[:k]) + (f" e mais {len(xs) - k}" if len(xs) > k else "")


def default_cites(home) -> list:
    """As citações do Claude Code que existirem: o CLAUDE.md do usuário, os planos e as memórias."""
    home = Path(home)
    found = [home / ".claude" / "CLAUDE.md", home / ".claude" / "plans",
             *map(Path, sorted(glob.glob(str(home / ".claude" / "projects" / "*" / "memory"))))]
    return [str(p) for p in found if p.exists()]


class Busca:
    """Onde cada nome da raiz é citado: pelo caminho (`<raiz>/<nome>`), ou solto se for longo."""

    def __init__(self, root, names):
        self.root, self.names = root, set(names)
        rootname = os.path.basename(root)
        self._path = re.compile(re.escape(rootname) + r"/([^\s/'\"`)\]>*,;:|<(]+)")
        longos = sorted((n for n in names if len(n) >= NOME_MINIMO), key=len, reverse=True)
        self._solto = (re.compile(r"(?<![\w.-])(" + "|".join(map(re.escape, longos)) + r")(?![\w-]|\.\w)")
                       if longos else None)
        self._fixos = [f"{rootname}/{n}" for n in names] + longos

    def achar(self, text: str) -> set:
        hits = {m.group(1).rstrip(".") for m in self._path.finditer(text)} & self.names
        if self._solto:
            hits.update(m.group(1) for m in self._solto.finditer(text))
        return hits

    def _grep(self, repo, sha=None):
        """(caminho, texto) dos arquivos do repo com algum nome: na árvore de `sha`, ou na cópia de
        trabalho (rastreados e não rastreados que o .gitignore não esconde)."""
        if not self._fixos:
            return
        # Os padrões vão pelo stdin (`-f -`): centenas de nomes estourariam a linha de comando.
        args = ["git", "--no-optional-locks", "-C", str(repo), "grep", "-I", "-l", "-z", "-F", "-f", "-"]
        args += [sha, "--"] if sha else ["--untracked", "--"]
        out = subprocess.run(args, input="\n".join(self._fixos) + "\n", capture_output=True, text=True,
                             encoding="utf-8", errors="surrogateescape").stdout
        for path in filter(None, out.split("\0")):
            if sha:
                yield path.split(":", 1)[1], hk.run_git(repo, "show", path).stdout
            else:
                yield path, _ler(os.path.join(repo, path))

    def fontes(self, repos, cites) -> dict:
        """{nome: [onde]} nas fontes de fora da raiz: os --repo (o origin/HEAD e a cópia de trabalho)
        e as citações (arquivos ou pastas de texto)."""
        out = defaultdict(list)
        for r in repos:
            label = os.path.basename(r.path)
            for path, text in self._grep(r.path, r.sha):
                for n in self.achar(text):
                    out[n].append(f"{label}@{r.ref}:{path}")
            for path, text in self._grep(r.path):
                for n in self.achar(text):
                    out[n].append(f"{label}:{path}")
        for c in cites:
            for f in _textos(c):
                for n in self.achar(_ler(f)):
                    out[n].append(f.replace(str(Path.home()), "~", 1))
        return out

    def entradas(self, names) -> dict:
        """{nome: [onde]} no texto das entradas `names` da raiz; a entrada não cita a si mesma."""
        out = defaultdict(list)
        for e in names:
            p = os.path.join(self.root, e)
            if os.path.islink(p):
                continue
            if os.path.exists(os.path.join(p, ".git")):
                found = ((os.path.join(e, path), text) for path, text in self._grep(p))
            else:
                found = ((os.path.relpath(f, self.root), _ler(f)) for f in _textos(p))
            for where, text in found:
                for n in self.achar(text) - {e}:
                    out[n].append(where)
        return out


def _textos(path):
    """Os arquivos de texto (`TEXTO`) de um arquivo ou pasta, sem entrar em .git nem em regenerável."""
    if os.path.isfile(path):
        yield path
        return
    for top, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if d not in (".git", LIXEIRA) and not regen_solto(os.path.join(top, d))]
        for f in files:
            if f.endswith(TEXTO):
                yield os.path.join(top, f)


@dataclass
class Partilha:
    """O conteúdo de uma pasta separado: sem prova (`resto`), o que sai sozinho (`subs`), o que
    bloqueia (clone sujo, worktree) e quantos arquivos se provaram, por motivo."""
    resto: list = field(default_factory=list)
    subs: list = field(default_factory=list)
    bloqueios: list = field(default_factory=list)
    notas: list = field(default_factory=list)
    provados: Counter = field(default_factory=Counter)


class Contexto:
    """O que a análise consulta mais de uma vez: os --repo, os processos, o gh e o histórico."""

    def __init__(self, root, repos, igual, recent_days, procs, now, cites=None):
        self.root, self.repos, self.recent_days, self.procs, self.now = root, repos, recent_days, procs, now
        self.igual = {os.path.realpath(k): v for k, v in (igual or {}).items()}
        self.cites = cites or {}
        self._blobs, self._msgs, self._issues, self._shas, self._refs = {}, {}, {}, {}, {}
        self._sem_fetch = {}
        self.gh_ok, self.gh_erro = False, ""

    def refs(self, r: Repo) -> list:
        """As refs que provam cópia no repo: as vivas no remoto; sem resposta do remoto, só a
        default (`origin/...`); sem default no remoto, nenhuma."""
        if r.path not in self._refs:
            remoto = refs_do_remoto(r.path)
            vivas, self._sem_fetch[r.path] = remoto if remoto is not None else (None, [])
            self._refs[r.path] = (vivas if vivas is not None
                                  else [r.sha] if r.sha and r.ref.startswith("origin/") else [])
        return self._refs[r.path]

    def sem_fetch(self) -> dict:
        """As refs que não provam porque o remoto andou depois do último fetch, por repo."""
        for r in self.repos:
            self.refs(r)
        return {p: [ref.removeprefix("refs/remotes/") for ref in refs]
                for p, refs in self._sem_fetch.items() if refs}

    def blobs(self, r: Repo) -> set:
        if r.path not in self._blobs:
            refs = self.refs(r)
            out = hk.run_git(r.path, "rev-list", "--objects", *refs).stdout if refs else ""
            self._blobs[r.path] = {line[:40] for line in out.splitlines()}
        return self._blobs[r.path]

    def mensagens(self, r: Repo) -> set:
        if r.path not in self._msgs:
            refs = self.refs(r)
            out = hk.run_git(r.path, "log", "--format=%B%x00", *refs, "--").stdout if refs else ""
            self._msgs[r.path] = {_norm_msg(m) for m in out.split("\0") if m.strip()}
        return self._msgs[r.path]

    def prova_arquivo(self, path) -> str:
        """Por que o arquivo tem outra cópia (`no histórico de X`, `mensagem de commit de X`,
        `vazio`, `link`), ou "" sem prova."""
        try:
            st = os.lstat(path)
        except OSError:
            return ""
        if stat.S_ISLNK(st.st_mode):
            return "link (só o link sai)"
        if not stat.S_ISREG(st.st_mode):
            return ""
        if st.st_size == 0:
            return "vazio"
        if st.st_size > TETO_HASH:
            return ""
        try:
            data = Path(path).read_bytes()
        except OSError:
            return ""
        oid = hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()
        for r in self.repos:
            if oid in self.blobs(r):
                return f"no histórico de {os.path.basename(r.path)}"
        if len(data) <= TETO_MENSAGEM:
            msg = _norm_msg(data.decode("utf-8", "replace"))
            for r in self.repos:
                if msg and msg in self.mensagens(r):
                    return f"mensagem de commit de {os.path.basename(r.path)}"
        return ""

    def sha(self, short: str) -> tuple:
        """("default"|"fora", repo) para o sha que existe num --repo, ou ("ausente", None)."""
        if short not in self._shas:
            self._shas[short] = ("ausente", None)
            for r in self.repos:
                full = hk.run_git(r.path, "rev-parse", "--verify", "-q", f"{short}^{{commit}}").stdout.strip()
                if full:
                    self._shas[short] = ("default" if r.sha and hk.is_ancestor(r.path, full, r.sha)
                                         else "fora", r)
                    break
        return self._shas[short]

    def issues(self, slug: str):
        """{número: (é PR, estado, mergeado)} do repo pelo `gh api`, ou None sem gh (o motivo fica em
        `gh_erro`)."""
        if slug not in self._issues:
            try:
                proc = subprocess.run(["gh", "api", "--paginate", f"repos/{slug}/issues?state=all&per_page=100"],
                                      capture_output=True, text=True, encoding="utf-8")
            except OSError as e:
                proc = subprocess.CompletedProcess([], 127, "", f"gh não roda: {e}")
            if proc.returncode:
                self.gh_erro = (proc.stderr.strip().splitlines() or ["gh falhou"])[-1]
                self._issues[slug] = None
            else:
                self.gh_ok = True
                self._issues[slug] = {
                    i["number"]: ("pull_request" in i, i.get("state"),
                                  bool((i.get("pull_request") or {}).get("merged_at")))
                    for i in _json_concat(proc.stdout)}
        return self._issues[slug]


def _json_concat(text: str) -> list:
    """As páginas do `gh api --paginate`, que vêm como arrays JSON emendados."""
    dec, i, out = json.JSONDecoder(), 0, []
    while i < len(text):
        if text[i].isspace():
            i += 1
            continue
        obj, i = dec.raw_decode(text, i)
        out.extend(obj if isinstance(obj, list) else [obj])
    return out


def partilha(ctx: Contexto, path, provar=True) -> Partilha:
    """Separa o conteúdo da pasta. Sem `provar`, só acha o que sai sozinho (não confere arquivo)."""
    part = Partilha()

    def igual(d) -> bool:
        dest = ctx.igual.get(os.path.realpath(d))
        if not dest:
            return False
        total, faltam = compara(d, dest)
        rel = os.path.relpath(d, ctx.root)
        if faltam:
            part.notas.append(f"{len(faltam)} de {total} arquivos de {rel} sem cópia igual em {dest}")
            part.resto += [(os.path.relpath(f, ctx.root), os.path.getsize(f)) for f in faltam]
        elif d == path:
            part.provados[f"igual em {dest}"] += total
        else:
            part.subs.append((rel, "igual", f"{total} arquivos iguais byte a byte em {dest}"))
        return True

    def separa(d) -> bool:
        rel = os.path.relpath(d, ctx.root)
        if os.path.islink(d):
            part.provados["link (só o link sai)"] += 1
        elif regen_solto(d):
            tipo = "venv" if os.path.isfile(os.path.join(d, "pyvenv.cfg")) else os.path.basename(d)
            part.subs.append((rel, "regen", f"regenerável ({tipo})"))
        elif os.path.isdir(os.path.join(d, ".git")):
            ok, why = clone_limpo(d)
            if ok:
                part.subs.append((rel, "clone", f"clone limpo: {why}"))
            else:
                part.bloqueios.append(f"clone {rel}: {why}")
        elif os.path.exists(os.path.join(d, ".git")):
            part.bloqueios.append(f"worktree git em {rel}")
        else:
            return igual(d)
        return True

    if igual(path):
        return part
    for top, dirs, names in os.walk(path):
        dirs[:] = [d for d in dirs if not separa(os.path.join(top, d))]
        for name in names if provar else ():
            f = os.path.join(top, name)
            why = ctx.prova_arquivo(f)
            if why:
                part.provados[why] += 1
            else:
                part.resto.append((os.path.relpath(f, ctx.root), os.lstat(f).st_size))
    return part


def _sub_items(ctx: Contexto, part: Partilha) -> list:
    out = []
    for rel, proof, why in part.subs:
        files, kb, size, newest = conta(os.path.join(ctx.root, rel))
        out.append(Item(rel, "sub", "dir", "delete", why, proof, [], files, kb, size, newest))
    return out


def _sem_prova(part: Partilha, o_que="arquivo(s)") -> str:
    motivos = part.bloqueios + part.notas
    if part.resto and not part.notas:
        kb = sum(s for _, s in part.resto) // 1024
        motivos.append(f"{len(part.resto)} {o_que} sem prova de outra cópia ({kb} KB): "
                       f"{_lista((n for n, _ in part.resto), 5)}")
    return "; ".join(motivos)


def _resumo(part: Partilha) -> str:
    bits = [f"{n} {why}" for why, n in sorted(part.provados.items())]
    bits += [f"{rel} ({why})" for rel, _, why in part.subs]
    return "; ".join(bits) or "nada dentro"


def baseline(ctx: Contexto, path) -> tuple:
    """(decisão, motivo, evidência) do baseline do retrofit-skill: sai quando o diff do gate está
    no histórico de um --repo, porque o diff.txt pode ser a única cópia de uma edição não publicada."""
    diff = os.path.join(path, "diff.txt")
    if not os.path.isfile(diff):
        return "delete", "baseline de retrofit sem diff.txt: só a saída do auditor, que se refaz", []
    text = _ler(diff)
    paths = re.findall(r"^diff --git a/(\S+) b/", text, re.M)
    linhas = sorted({ln[1:].strip() for ln in text.splitlines()
                     if ln.startswith("+") and not ln.startswith("+++") and len(ln[1:].strip()) >= 20},
                    key=len, reverse=True)[:6]
    if not linhas:
        return "delete", "baseline de retrofit sem linha acrescentada no diff: nada a perder", []
    for r in ctx.repos:
        refs = ctx.refs(r)
        if not paths or not refs or not hk.run_git(r.path, "log", "-1", "--format=%h", *refs, "--",
                                                   paths[0]).stdout.strip():
            continue
        achou = [h for h in (hk.run_git(r.path, "log", "-1", "--format=%h", f"-S{ln}", *refs, "--",
                                        *paths).stdout.strip() for ln in linhas) if h]
        name = os.path.basename(r.path)
        if len(achou) == len(linhas):
            return ("delete", f"o diff do retrofit está no histórico de {name} "
                              f"({len(linhas)}/{len(linhas)} linhas; {achou[0]})", achou)
        return "unproven", f"só {len(achou)} de {len(linhas)} linhas do diff estão no histórico de {name}", achou
    return "unproven", f"nenhum --repo tem os arquivos do diff ({paths[0] if paths else 'sem caminho'})", []


def _repo_do_handoff(ctx: Contexto, name: str):
    m = _HANDOFF.match(name)
    if not m:
        return None
    key = m.group(1).lower().replace("_", "-")
    hits = []
    for r in ctx.repos:
        nomes = {os.path.basename(p).lower().replace("_", "-") for p in (r.path, os.path.dirname(r.path))}
        if key in nomes or any(key.startswith(n + "-") for n in nomes):
            hits.append(r)
    return hits[0] if len(hits) == 1 else None


def handoff(ctx: Contexto, path, name, part: Partilha) -> tuple:
    """(decisão, motivo, evidência) do handoff. O script confere o mecânico (os shas na default, os
    PRs fechados, os anexos com outra cópia) e marca `review`: se as pendências foram cumpridas é
    leitura, e quem lê é o agente, antes de pedir a confirmação."""
    text = _ler(os.path.join(path, "HANDOFF.md"))
    part.resto = [(n, s) for n, s in part.resto if n != os.path.join(name, "HANDOFF.md")]
    problemas = [_sem_prova(part, "anexo(s)")] if (part.resto or part.bloqueios) else []
    provas, notas, tipos = [], [], Counter()
    # Todo token hexadecimal é conferido. O que mistura letra e dígito é um sha mesmo sem resolver;
    # o só de dígitos (`1719887`, 3,7% dos shas curtos) ou só de letras só conta se resolver como
    # commit: sem isso, `20261117` (uma data) seria um sha que não existe.
    for s in sorted(set(_SHA.findall(text))):
        st, r = ctx.sha(s)
        if st == "default":
            provas.append(f"{s} na default de {os.path.basename(r.path)}")
            tipos["sha(s) na default"] += 1
        elif st == "fora":
            problemas.append(f"sha {s} fora da default de {os.path.basename(r.path)}")
        elif re.search(r"[a-f]", s) and re.search(r"\d", s):
            problemas.append(f"sha {s} não existe em nenhum --repo")
    refs = {(slug, int(n)) for slug, n in _REF_URL.findall(text) + _REF_SLUG.findall(text)}
    dono = _repo_do_handoff(ctx, name)
    nums = {int(a or b) for a, b in _REF_NUM.findall(text)}
    if nums and not dono:
        problemas.append(f"o repo do handoff não está entre os --repo: {_lista(sorted(f'#{n}' for n in nums), 4)} "
                         "não se conferem")
    refs |= {(dono.slug, n) for n in nums} if dono else set()
    slugs = {r.slug for r in ctx.repos if r.slug}
    for slug, n in sorted(refs, key=lambda x: (x[0] or "", x[1])):
        if slug not in slugs:
            problemas.append(f"{slug}#{n}: repo fora dos --repo")
            continue
        info = ctx.issues(slug)
        if info is None:
            problemas.append(f"sem gh para conferir #{n} ({ctx.gh_erro})")
            continue
        if n not in info:
            continue
        is_pr, state, merged = info[n]
        if is_pr and state == "open":
            problemas.append(f"PR #{n} aberto")
            continue
        tipo, label = ((("PR(s) mergeado(s)", "PR mergeado") if merged
                        else ("PR(s) fechado(s) sem merge", "PR fechado sem merge")) if is_pr
                       else ("issue(s) aberta(s)", "issue aberta") if state == "open"
                       else ("issue(s) fechada(s)", "issue fechada"))
        (notas if state == "open" else provas).append(f"#{n} {label}")
        tipos[tipo] += 1
    if not provas and not problemas:
        problemas.append("sem sha nem PR que provem o merge")
    if problemas:
        return "unproven", "; ".join(problemas), provas + notas
    resumo = "; ".join(f"{n} {t}" for t, n in tipos.items() if t != "issue(s) aberta(s)")
    aberta = (f"; {tipos['issue(s) aberta(s)']} issue(s) aberta(s), o trabalho segue no tracker"
              if tipos["issue(s) aberta(s)"] else "")
    return ("review", f"provas mecânicas ok ({resumo}){aberta}; falta ler as pendências do HANDOFF.md",
            provas + notas)


def avaliar(ctx: Contexto, name: str) -> list:
    """A entrada da raiz e, se ela fica, os pedaços dela que saem sozinhos."""
    p = os.path.join(ctx.root, name)
    st = os.lstat(p)
    is_dir = stat.S_ISDIR(st.st_mode)
    files, kb, size, newest = conta(p)

    def item(decision, reason, proof="", evidence=()):
        return Item(name, "entry", "dir" if is_dir else "file", decision, reason, proof,
                    list(evidence), files, kb, size, newest)

    if name == LIXEIRA:
        return [item("keep", "a quarentena desta limpeza: esvazie com scratch_apply.py --purge")]
    if stat.S_ISLNK(st.st_mode):
        return [item("keep", f"link para {os.readlink(p)}: só o link é desta raiz")]
    if any(hk.same_path(r.path, p) or hk._inside(r.path, p) for r in ctx.repos):
        return [item("keep", "é (ou contém) um dos --repo")]
    if is_dir and os.path.isfile(os.path.join(p, ".git")):
        return [item("keep", "worktree git: quem cuida dele é o fluxo das branches (analyze.py)")]
    who = processo_dentro(p, ctx.procs)
    if who:
        return [item("keep", f"processo com o diretório aqui dentro: {who}")]
    idade = (ctx.now - newest) / 86400
    if idade < ctx.recent_days:
        return [item("keep", f"recente: mexida há {idade:.1f} dia(s) (janela de {ctx.recent_days})")]
    onde = ctx.cites.get(name)
    if onde:
        return [item("keep", f"citada em {_lista(onde)}", evidence=onde)] + subs_de(ctx, name)
    if not is_dir:
        why = ctx.prova_arquivo(p)
        if why:
            return [item("delete", f"arquivo {why}", "arquivo")]
        return [item("unproven", "arquivo sem prova de outra cópia (nem no histórico dos --repo, "
                                 "nem mensagem de commit)")]
    if os.path.isdir(os.path.join(p, ".git")):
        ok, why = clone_limpo(p)
        return [item("delete" if ok else "unproven", f"clone{' limpo' if ok else ''}: {why}", "clone")]
    if files == 0:
        return [item("delete", "pasta vazia", "vazia")]
    tops = set(os.listdir(p))
    if "antes.json" in tops and tops <= BASELINE and all(os.path.isfile(os.path.join(p, t)) for t in tops):
        decision, reason, ev = baseline(ctx, p)
        return [item(decision, reason, "baseline", ev)]
    part = partilha(ctx, p)
    if "HANDOFF.md" in tops:
        decision, reason, ev = handoff(ctx, p, name, part)
        return [item(decision, reason, "handoff", ev)] + (_sub_items(ctx, part) if decision == "unproven" else [])
    if part.resto or part.bloqueios:
        return [item("unproven", _sem_prova(part))] + _sub_items(ctx, part)
    return [item("delete", f"tudo tem outra cópia ou se recria: {_resumo(part)}", "partilha")]


def subs_de(ctx: Contexto, name: str) -> list:
    """Os pedaços que saem sozinhos de uma entrada que fica (regenerável, clone limpo, cópia igual)."""
    p = os.path.join(ctx.root, name)
    if not os.path.isdir(p) or os.path.islink(p) or os.path.isfile(os.path.join(p, ".git")):
        return []
    return _sub_items(ctx, partilha(ctx, p, provar=False))


def listar(root) -> list:
    """As entradas da raiz, em ordem."""
    return sorted(os.listdir(root))


def scan(root, repos, cites, igual=None, recent_days=RECENTE_DIAS, procs=None, now=None) -> dict:
    """O plano da raiz: cada entrada classificada, a cadeia das citações resolvida até parar."""
    root = os.path.realpath(root)
    ctx = Contexto(root, repos, igual, recent_days, procs, now)
    names = [n for n in listar(root) if n != LIXEIRA]
    busca = Busca(root, names)
    ctx.cites = busca.fontes(repos, cites)
    items = [i for n in listar(root) for i in avaliar(ctx, n)]
    by = {i.name: i for i in items if i.kind == "entry"}

    def fica(n, reason, onde):
        it = by[n]
        it.decision, it.reason, it.evidence = "keep", reason, list(onde)
        items.extend(subs_de(ctx, n))
        novas.append(n)

    # Quem cita cada entrada: as fontes de fora e, rodada a rodada, as entradas que ficam.
    citers = defaultdict(set, {n: set(onde) for n, onde in ctx.cites.items()})
    novas = [n for n, i in by.items() if i.decision not in SAEM and n != LIXEIRA]
    while novas:
        while novas:
            hits, novas = busca.entradas(novas), []
            for n, onde in sorted(hits.items()):
                citers[n].update(w.split(os.sep)[0] for w in onde)
                if by[n].decision in SAEM:
                    fica(n, f"citada por quem fica: {_lista(onde)}", onde)
        # O handoff que é a única descrição de uma pasta que fica, fica com ela: sem ele, ninguém
        # sabe mais o que a pasta guarda.
        handoffs = [n for n, i in by.items() if i.decision in SAEM and i.proof == "handoff"]
        for cited, onde in sorted(busca.entradas(handoffs).items()):
            if by[cited].decision in SAEM or citers[cited]:
                continue
            for h in sorted({w.split(os.sep)[0] for w in onde}):
                if by[h].decision in SAEM:
                    fica(h, f"é a única descrição de {cited}, que fica", [f"{h} cita {cited}"])
    gh = "sim" if ctx.gh_ok else (f"não ({ctx.gh_erro})" if ctx.gh_erro else "não usado")
    return {"version": PLAN_VERSION, "tool": "scratch", "root": root, "created": now,
            "recent_days": recent_days, "repos": [r.__dict__ for r in repos], "sem_fetch": ctx.sem_fetch(),
            "cites": list(cites),
            "igual": {k: v for k, v in ctx.igual.items()}, "gh": gh, "procs_checked": procs is not None,
            "items": [i.__dict__ for i in items]}
