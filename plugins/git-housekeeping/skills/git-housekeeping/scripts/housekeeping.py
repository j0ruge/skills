"""Fatos de um repo git e as regras de limpeza do git-housekeeping.

O analyze.py monta o plano com estas funções, e o apply_plan.py as chama de novo, item a item, antes
de apagar: o plano diz o que pode sair, e a prova é refeita na hora. Fora o `git fetch` do
load_facts, que não apaga ref nenhuma, nada aqui escreve no repo.
"""
from __future__ import annotations

import fnmatch
import json
import os
import re
import shutil
import subprocess
from dataclasses import asdict, dataclass, field, replace
from datetime import datetime
from pathlib import Path

PLAN_VERSION = 1
# Destino de merge ou de deploy: nunca saem, mesmo mergeadas.
LONG_LIVED = ("main", "master", "develop", "staging", "production", "release/*")
# O gh pagina até aqui. PR mergeado além do limite só deixa de provar (a falha segura); PR aberto
# além dele esconderia uma proteção, e por isso o gh passa a contar como indisponível.
PR_LIMIT = 1000
PR_FIELDS = "number,headRefName,headRefOid,baseRefName,isCrossRepository"
KIND_PT = {"worktree": "worktree", "local-branch": "branch local",
           "remote-branch": "branch remota", "remote-tracking": "ref remote-tracking"}


class GitError(RuntimeError):
    """Comando git, ou o remoto, que falhou; as CLIs transformam isso em rc 2."""


def run_git(repo, *args: str) -> subprocess.CompletedProcess:
    """`git -C repo ...` sem optional locks: o `git status` não reescreve o index."""
    return subprocess.run(["git", "--no-optional-locks", "-C", str(repo), *args],
                          capture_output=True, text=True, encoding="utf-8",
                          errors="surrogateescape")


def git(repo, *args: str) -> str:
    """O stdout de run_git; rc ≠ 0 vira GitError com o stderr."""
    proc = run_git(repo, *args)
    if proc.returncode != 0:
        raise GitError(f"git {' '.join(args)}: {proc.stderr.strip()}")
    return proc.stdout


@dataclass
class PullRequest:
    """O que o gh diz de um PR: só os campos que provam merge ou protegem branch."""
    number: int
    head: str
    head_oid: str
    base: str
    cross_repo: bool


@dataclass
class LocalBranch:
    """Branch local, com o upstream já resolvido para o remoto e o nome da branch lá."""
    name: str
    sha: str
    upstream_remote: str
    upstream_name: str


@dataclass
class Worktree:
    """Um bloco do `git worktree list --porcelain`; `branch` vazio quando o HEAD está destacado."""
    path: str
    head: str
    branch: str
    main: bool = False
    locked: bool = False
    prunable: bool = False


@dataclass
class Item:
    """Uma linha do plano: o que é, a decisão (delete, keep, unproven), o porquê e a prova."""
    kind: str
    name: str
    sha: str
    decision: str
    reason: str
    evidence: str = ""
    scope: str = "local"
    branch: str = ""
    action: str = ""
    kb: int = 0
    ignored: list = field(default_factory=list)
    author: str = ""


@dataclass
class Facts:
    """Tudo o que as regras leem, juntado uma vez por load_facts."""
    repo: str
    common_dir: str
    remote: str
    default: str
    default_sha: str
    first_parent: set
    remote_heads: dict
    tracking: dict
    local: list
    worktrees: list
    current_path: str
    protect_patterns: list
    workflow_branches: list
    merged_prs: list
    open_prs: list
    gh_available: bool
    gh_reason: str
    offline: bool
    cwd: str = ""
    busy: dict = field(default_factory=dict)


_SLUG = re.compile(r"^(?:https://(?:[^@/]+@)?github\.com/|ssh://git@github\.com/|git@github\.com:)"
                   r"([^/]+)/([^/]+?)(?:\.git)?/?$")


def github_slug(url: str) -> str:
    """owner/repo de uma URL do github.com, ou "" para qualquer outro host."""
    m = _SLUG.match(url.strip())
    return f"{m.group(1)}/{m.group(2)}" if m else ""


_BRANCHES = re.compile(r"^(\s*)branches\s*:\s*(.*?)\s*(?:#.*)?$")


def _unquote(s: str) -> str:
    """Tira espaço e aspas de um item de lista YAML."""
    return s.strip().strip("'\"")


def parse_workflow_branches(text: str) -> list:
    """Os padrões de toda lista `branches:` de um workflow, sem parser YAML.

    Heurística de propósito: protege qualquer nome citado em `branches:` (push, pull_request, o que
    for). Proteger demais deixa a branch no lugar; proteger de menos pode derrubar um deploy.
    """
    out = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        m = _BRANCHES.match(lines[i])
        i += 1
        if not m:
            continue
        indent, rest = len(m.group(1)), m.group(2)
        if rest.startswith("["):
            out += [_unquote(x) for x in rest.strip("[]").split(",") if x.strip()]
            continue
        if rest:
            out.append(_unquote(rest))
            continue
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                i += 1
                continue
            if not stripped.startswith("-") or len(line) - len(line.lstrip()) < indent:
                break
            out.append(_unquote(stripped[1:].split(" #")[0]))
            i += 1
    return [p for p in out if p and not p.startswith("!")]


def parse_worktrees(porcelain: str) -> list:
    """Os blocos do `git worktree list --porcelain`; o primeiro é o worktree principal."""
    out = []
    for block in porcelain.strip().split("\n\n"):
        if not block.strip():
            continue
        wt = Worktree(path="", head="", branch="")
        for line in block.splitlines():
            key, _, value = line.partition(" ")
            if key == "worktree":
                wt.path = value
            elif key == "HEAD":
                wt.head = value
            elif key == "branch":
                wt.branch = value.removeprefix("refs/heads/")
            elif key == "locked":
                wt.locked = True
            elif key == "prunable":
                wt.prunable = True
        out.append(wt)
    if out:
        out[0].main = True
    return out


def parse_push_porcelain(stdout: str) -> dict:
    """ref remota → (apagada?, resumo do git), a partir do `git push --porcelain`.

    Apagada: `-\\t:refs/heads/b\\t[deleted]`. Recusada: `!\\t(delete):refs/heads/b\\t[rejected] (stale info)`.
    """
    out = {}
    for line in stdout.splitlines():
        parts = line.split("\t")
        if len(parts) < 3 or ":" not in parts[1]:
            continue
        out[parts[1].split(":", 1)[1]] = (parts[0] == "-", parts[2].strip())
    return out


def same_path(a, b) -> bool:
    """Dois caminhos são o mesmo lugar (o git e o tempfile podem divergir por symlink)."""
    return os.path.realpath(str(a)) == os.path.realpath(str(b))


def _inside(path, folder) -> bool:
    """`path` está dentro de `folder` (ou é ele), comparando por realpath."""
    return Path(os.path.realpath(str(path))).is_relative_to(os.path.realpath(str(folder)))


# Marcadores de operação parada no gitdir do worktree: apagar o worktree perderia a operação.
_BUSY = (("rebase-merge", "rebase"), ("rebase-apply", "rebase"), ("BISECT_LOG", "bisect"),
         ("MERGE_HEAD", "merge"), ("CHERRY_PICK_HEAD", "cherry-pick"), ("REVERT_HEAD", "revert"))


def _busy(path) -> tuple:
    """(operação, branch que ela vai atualizar) parada no worktree, ou ("", "")."""
    try:
        gitdir = Path(git(path, "rev-parse", "--absolute-git-dir").strip())
    except GitError:
        return "", ""
    for marker, op in _BUSY:
        if (gitdir / marker).exists():
            head = gitdir / marker / "head-name"
            branch = head.read_text(encoding="utf-8").strip() if head.is_file() else ""
            return op, branch.removeprefix("refs/heads/")
    return "", ""


def worktrees(repo) -> list:
    """Os worktrees do repo, o principal primeiro."""
    return parse_worktrees(git(repo, "worktree", "list", "--porcelain"))


def is_ancestor(repo, a: str, b: str) -> bool:
    """`a` está contido em `b`."""
    return run_git(repo, "merge-base", "--is-ancestor", a, b).returncode == 0


def has_commit(repo, sha: str) -> bool:
    """O commit existe neste clone (uma ponta remota pode não ter vindo no fetch)."""
    return run_git(repo, "cat-file", "-e", f"{sha}^{{commit}}").returncode == 0


def dir_kb(path) -> int:
    """KiB ocupados por uma pasta, sem seguir symlink: o que o `du -sk` diria, sem depender dele."""
    total = 0
    for root, _dirs, files in os.walk(path):
        for name in files:
            try:
                st = os.lstat(os.path.join(root, name))
            except OSError:
                continue
            blocks = getattr(st, "st_blocks", None)
            total += blocks * 512 if blocks is not None else st.st_size
    return total // 1024


def git_kb(repo) -> int:
    """KiB dos objetos do repo (soltos e empacotados), pelo `git count-objects -v`."""
    values = dict(line.split(": ", 1) for line in git(repo, "count-objects", "-v").splitlines())
    return int(values.get("size", 0)) + int(values.get("size-pack", 0))


def _refs(repo, prefix: str) -> dict:
    """nome (sem o prefixo) → sha das refs sob `prefix`."""
    out = {}
    for line in git(repo, "for-each-ref", "--format=%(refname)%00%(objectname)", prefix).splitlines():
        ref, sha = line.split("\0")
        out[ref.removeprefix(prefix)] = sha
    return out


def _local_branches(repo) -> list:
    """As branches locais com o upstream (remoto e nome lá), lidos da configuração."""
    fmt = "%(refname)%00%(objectname)%00%(upstream:remotename)%00%(upstream:remoteref)"
    out = []
    for line in git(repo, "for-each-ref", f"--format={fmt}", "refs/heads/").splitlines():
        ref, sha, up_remote, up_ref = line.split("\0")
        out.append(LocalBranch(ref.removeprefix("refs/heads/"), sha, up_remote,
                               up_ref.removeprefix("refs/heads/")))
    return out


def _remote_default(repo, remote: str) -> str:
    """A branch default que o remoto anuncia no HEAD."""
    for line in git(repo, "ls-remote", "--symref", remote, "HEAD").splitlines():
        if line.startswith("ref: "):
            return line[5:].split("\t")[0].removeprefix("refs/heads/")
    raise GitError(f"o remoto {remote} não diz qual é a branch default (HEAD)")


def _ls_remote_heads(repo, remote: str) -> dict:
    """nome → sha das branches que existem agora no remoto (a fonte fresca)."""
    out = {}
    for line in git(repo, "ls-remote", "--heads", remote).splitlines():
        sha, ref = line.split("\t")
        out[ref.removeprefix("refs/heads/")] = sha
    return out


def _workflow_branches(repo, ref: str) -> list:
    """Os padrões de `branches:` dos workflows da default (lidos do commit, e não da árvore)."""
    proc = run_git(repo, "ls-tree", "--name-only", f"{ref}:.github/workflows")
    out = []
    for name in proc.stdout.split() if proc.returncode == 0 else []:
        if name.endswith((".yml", ".yaml")):
            out += parse_workflow_branches(git(repo, "show", f"{ref}:.github/workflows/{name}"))
    return out


def load_prs(repo, remote: str) -> tuple:
    """(mergeados, abertos, gh_available, motivo) do repo no GitHub, pelo gh."""
    if shutil.which("gh") is None:
        return [], [], False, "gh não instalado"
    # A URL crua: o `git remote get-url` aplicaria o insteadOf (medido no git 2.43).
    url = run_git(repo, "config", "--get", f"remote.{remote}.url").stdout.strip()
    slug = github_slug(url)
    if not slug:
        return [], [], False, "o remoto não está no github.com"
    lists = {}
    for state in ("merged", "open"):
        proc = subprocess.run(["gh", "pr", "list", "-R", slug, "--state", state,
                               "--limit", str(PR_LIMIT), "--json", PR_FIELDS],
                              capture_output=True, text=True, encoding="utf-8")
        if proc.returncode != 0:
            return [], [], False, f"gh falhou: {proc.stderr.strip()[:200]}"
        lists[state] = [PullRequest(p["number"], p["headRefName"], p["headRefOid"],
                                    p["baseRefName"], bool(p["isCrossRepository"]))
                        for p in json.loads(proc.stdout or "[]")]
    if len(lists["open"]) >= PR_LIMIT:
        return [], [], False, f"{PR_LIMIT}+ PRs abertos: a proteção por PR aberto ficaria incompleta"
    return lists["merged"], lists["open"], True, ""


def load_facts(repo, remote: str = "origin", offline: bool = False) -> Facts:
    """Junta os fatos de um repo. Online: fetch (sem prune), ls-remote e gh. Offline: só o local."""
    top = git(repo, "rev-parse", "--show-toplevel").strip()
    common = git(repo, "rev-parse", "--path-format=absolute", "--git-common-dir").strip()
    if remote not in git(repo, "remote").split():
        raise GitError(f"o repo não tem o remoto {remote!r}")
    if not offline:
        # Sem estes flags, o fetch obedece fetch.prune / fetch.pruneTags da config do usuário e
        # apaga em silêncio a ref órfã (o único ponteiro) e as tags locais.
        fetch = run_git(repo, "fetch", "--no-prune", "--no-prune-tags", "--no-auto-maintenance",
                        "--quiet", remote)
        if fetch.returncode != 0:
            raise GitError(f"o remoto {remote} não respondeu ao fetch: {fetch.stderr.strip()}")
    tracking = _refs(repo, f"refs/remotes/{remote}/")
    tracking.pop("HEAD", None)
    if offline:
        head = run_git(repo, "symbolic-ref", "--quiet", f"refs/remotes/{remote}/HEAD").stdout.strip()
        default = head.removeprefix(f"refs/remotes/{remote}/")
        if not default:
            raise GitError(f"sem refs/remotes/{remote}/HEAD: rode git remote set-head {remote} --auto")
        remote_heads = dict(tracking)
        merged, opened, gh_ok, gh_reason = [], [], False, "varredura sem rede"
    else:
        default = _remote_default(repo, remote)
        remote_heads = _ls_remote_heads(repo, remote)
        merged, opened, gh_ok, gh_reason = load_prs(repo, remote)
    if default not in remote_heads:
        raise GitError(f"a branch default {default!r} não está no remoto {remote}")
    default_sha = remote_heads[default]
    patterns = run_git(repo, "config", "--get-all", "housekeeping.protect").stdout.split()
    wts = worktrees(repo)
    busy = {}
    for wt in wts:
        if not wt.prunable and os.path.isdir(wt.path):
            op, branch = _busy(wt.path)
            if op:
                busy[wt.path] = (op, branch)
    return Facts(
        repo=top, common_dir=common, remote=remote, default=default, default_sha=default_sha,
        first_parent=set(git(repo, "rev-list", "--first-parent", default_sha).split()),
        remote_heads=remote_heads, tracking=tracking, local=_local_branches(repo),
        worktrees=wts, current_path=top, protect_patterns=patterns,
        workflow_branches=_workflow_branches(repo, default_sha), merged_prs=merged,
        open_prs=opened, gh_available=gh_ok, gh_reason=gh_reason, offline=offline,
        cwd=os.path.realpath(os.getcwd()), busy=busy,
    )


def _ahead(repo, base: str, tip: str) -> str:
    """Quantos commits a ponta tem além da ponta do PR."""
    if has_commit(repo, base) and is_ancestor(repo, base, tip):
        return f"{git(repo, 'rev-list', '--count', f'{base}..{tip}').strip()} commit(s) depois"
    return "a ponta não descende da do PR"


def merge_proof(facts: Facts, remote_name: str, tip: str) -> tuple:
    """(decisão, motivo, evidência) da prova de que a ponta já está na default (spec § 2.2)."""
    d, repo = facts.default, facts.repo
    if not has_commit(repo, tip):
        return "unproven", "o commit da ponta não está neste clone", ""
    in_default = is_ancestor(repo, tip, facts.default_sha)
    if in_default and tip not in facts.first_parent:
        return "delete", f"mergeada na {d} por merge commit", "merge-commit"
    prs = [p for p in facts.merged_prs if p.head == remote_name and not p.cross_repo]
    for p in prs:
        if p.base == d and p.head_oid == tip:
            return "delete", f"PR #{p.number} mergeado na {d} com esta ponta", f"pr#{p.number}"
    if in_default:
        return "unproven", f"a ponta é um commit da {d}: branch nunca usada, ou fast-forward sem PR", ""
    on_default = [p for p in prs if p.base == d]
    if on_default:
        p = on_default[0]
        return ("unproven", f"PR #{p.number} mergeado, mas a ponta andou depois do merge: "
                f"{_ahead(repo, p.head_oid, tip)}", "")
    if prs:
        return "unproven", f"PR #{prs[0].number} mergeado na {prs[0].base}, não na {d}", ""
    if not facts.gh_available:
        return "unproven", f"sem prova por PR ({facts.gh_reason}): um squash merge não pode ser provado", ""
    return "keep", "não mergeada", ""


def protection(facts: Facts, *names: str) -> str:
    """Por que a branch fica mesmo mergeada (spec § 2.3), ou "" quando nada a protege."""
    for name in dict.fromkeys(n for n in names if n):
        if name == facts.default:
            return f"branch default do {facts.remote}"
        for pat in LONG_LIVED:
            if fnmatch.fnmatchcase(name, pat):
                return f"branch de vida longa ({pat})"
        for pat in facts.protect_patterns:
            if fnmatch.fnmatchcase(name, pat):
                return f"protegida por housekeeping.protect ({pat})"
        for pat in facts.workflow_branches:
            if fnmatch.fnmatchcase(name, pat):
                return f"citada em branches: de um workflow ({pat})"
        for p in facts.open_prs:
            if p.head == name and not p.cross_repo:
                return f"head do PR aberto #{p.number}"
            if p.base == name:
                return f"base do PR aberto #{p.number}"
    return ""


def _classify_local_base(facts: Facts, b: LocalBranch) -> Item:
    """A decisão de uma branch local sem contar os worktrees ligados (eles entram em classify)."""
    on_remote = b.upstream_name if b.upstream_remote == facts.remote else ""
    remote_name = on_remote or b.name

    def item(decision, reason, evidence=""):
        return Item("local-branch", b.name, b.sha, decision, reason, evidence)

    for wt in facts.worktrees:
        if wt.branch == b.name and (wt.main or same_path(wt.path, facts.current_path)):
            where = "principal" if wt.main else "atual"
            return item("keep", f"em uso no worktree {where} ({wt.path})")
    for path, (op, branch) in facts.busy.items():
        if branch == b.name:
            return item("keep", f"um {op} em andamento no worktree {path} usa esta branch")
    reason = protection(facts, b.name, remote_name)
    if reason:
        return item("keep", reason)
    decision, reason, evidence = merge_proof(facts, remote_name, b.sha)
    if decision == "keep" and not b.upstream_remote:
        reason = "não mergeada: trabalho só local"
    if decision != "delete" and on_remote and on_remote not in facts.remote_heads:
        reason += "; a branch sumiu do remoto"
        if decision == "keep":
            reason += ", e os commits só existem aqui"
    return item(decision, reason, evidence)


def _classify_worktree(facts: Facts, wt: Worktree, base: dict) -> Item:
    """A decisão de um worktree ligado (spec § 2.6); o principal nunca chega aqui."""
    def item(decision, reason, action=""):
        return Item("worktree", wt.path, wt.head, decision, reason, branch=wt.branch, action=action)

    if same_path(wt.path, facts.current_path):
        return item("keep", "é o worktree onde a análise roda")
    if wt.prunable:
        return item("delete", "a pasta do worktree não existe mais", "prune")
    if wt.locked:
        return item("keep", "travado (git worktree lock)")
    if facts.cwd and _inside(facts.cwd, wt.path):
        return item("keep", "é o worktree onde a sessão está (o diretório atual)")
    op, rebasing = facts.busy.get(wt.path, ("", ""))
    if op:
        out = item("keep", f"{op} em andamento neste worktree")
        out.branch = rebasing or wt.branch
        return out
    try:
        # Flags explícitos: status.showUntrackedFiles=no esconderia o arquivo não rastreado.
        dirty = git(wt.path, "status", "--porcelain", "--untracked-files=normal",
                    "--ignore-submodules=none").strip()
    except GitError as e:
        return item("keep", f"não deu para ler o estado do worktree: {e}")
    if dirty:
        return item("keep", "tem alteração ou arquivo não rastreado")
    if wt.branch:
        b = base.get(wt.branch)
        if b is None or b.decision != "delete":
            return item("keep", f"está na branch {wt.branch}, que fica" + (f": {b.reason}" if b else ""))
        out = item("delete", f"a branch {wt.branch} sai: {b.reason}", "remove")
    elif is_ancestor(facts.repo, wt.head, facts.default_sha):
        out = item("delete", f"HEAD destacado, já contido na {facts.default}", "remove")
    else:
        return item("keep", f"HEAD destacado fora da {facts.default}")
    out.kb = dir_kb(wt.path)
    listing = git(wt.path, "status", "--porcelain", "-z", "--ignored",
                  "--untracked-files=normal").split("\0")
    out.ignored = [entry[3:] for entry in listing if entry.startswith("!! ")]
    return out


def _classify_tracking(facts: Facts, name: str, sha: str) -> Item:
    """Ref remote-tracking cuja branch sumiu do remoto (spec § 2.5)."""
    saved = is_ancestor(facts.repo, sha, facts.default_sha) or bool(
        git(facts.repo, "for-each-ref", "--contains", sha, "--format=%(refname)", "refs/heads/").strip())
    if saved:
        return Item("remote-tracking", name, sha, "delete", "a branch não existe mais no remoto")
    return Item("remote-tracking", name, sha, "unproven",
                "o remoto apagou a branch, e esta ref é o único ponteiro local para esses commits")


def _classify_remote(facts: Facts, name: str, sha: str) -> Item:
    """A decisão de uma branch do remoto, com o autor do último commit para a 2ª confirmação."""
    author = git(facts.repo, "log", "-1", "--format=%an", sha).strip() if has_commit(facts.repo, sha) else ""
    reason = protection(facts, name)
    decision, evidence = "keep", ""
    if not reason:
        decision, reason, evidence = merge_proof(facts, name, sha)
    if decision == "delete" and not facts.gh_available and not facts.offline:
        # Sem gh não há como saber de PR aberto, e apagar a remota fecharia o PR.
        decision, evidence = "unproven", ""
        reason = (f"{reason}, mas o PR aberto não pode ser conferido ({facts.gh_reason}): "
                  "apagar a remota fecharia um PR que esteja aberto")
    return Item("remote-branch", name, sha, decision, reason, evidence, scope="remote", author=author)


def classify(facts: Facts) -> list:
    """O plano inteiro: worktrees ligados, branches locais, refs remote-tracking e branches remotas."""
    base = {b.name: _classify_local_base(facts, b) for b in facts.local}
    linked = [wt for wt in facts.worktrees if not wt.main]
    wt_items = [_classify_worktree(facts, wt, base) for wt in linked]
    items = list(wt_items)
    for b in facts.local:
        item = base[b.name]
        holder = next((i for i in wt_items if i.branch == b.name), None)
        if item.decision == "delete" and holder is not None and holder.decision != "delete":
            item = replace(item, decision="keep", reason=f"em uso no worktree {holder.name}, que fica",
                           evidence="")
        items.append(item)
    for name, sha in sorted(facts.tracking.items()):
        if name not in facts.remote_heads:
            items.append(_classify_tracking(facts, name, sha))
    for name, sha in sorted(facts.remote_heads.items()):
        items.append(_classify_remote(facts, name, sha))
    return items


def build_plan(facts: Facts) -> dict:
    """O plano JSON (spec § 3.2): os fatos de identidade do repo e todos os itens classificados."""
    items = classify(facts)
    return {
        "version": PLAN_VERSION, "repo": facts.repo, "git_common_dir": facts.common_dir,
        "remote": facts.remote, "default_branch": facts.default,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "gh_available": facts.gh_available, "gh_reason": facts.gh_reason,
        "items": [asdict(i) for i in items],
        "disk": {"git_kb": git_kb(facts.repo),
                 "worktrees_kb": sum(i.kb for i in items if i.decision == "delete")},
    }
