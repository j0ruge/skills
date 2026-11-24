"""retrofit-watch, modo autônomo: a colheita dos nomes privados, o worktree do lote e o selo do executor.

Roda fora do hook, pelos verbos `harvest`, `prepare` e `seal` de retrofit_watch.py. Chama o git e o
portão de anonimização da loja (`scripts/anonymity-gate.py`); nunca faz push.

  colheita   os nomes locais que não podem ir à loja pública, fora de qualquer repo e com permissão
             0o600: o verbo `harvest` grava <dados>/colheita.txt; a camada 1 grava a de cada chamada
             num arquivo só dela, passado por `--extra` e removido depois
  prepare    `git fetch origin` no clone da loja e um worktree ligado novo do `origin/main`, num ramo
             que sai do id e do lote; grava <dados>/auto/<id>/<lote>/retrofit.json
  seal       o selo do executor: completa o retrofit.json, grava termos-novos.json e roda a camada 1

Todo git daqui roda sem as variáveis de localização herdadas (um hook do git exporta GIT_DIR) e com o
HOME do Context: o `~` resolve pelo ctx.home, nunca pelo HOME real. Os erros são StoreError; a saída do
portão fora do formato também, nunca uma lista vazia (falha fechada).
"""
import hashlib
import json
import os
import re
import socket
import subprocess
import sys
from pathlib import Path

import rw_auto

RUN_TIMEOUT = 900
MIN_WORD = 4
PHASES = {"claim-check", "self-containment", "refactoring"}

HARVEST_FILE = "colheita.txt"
HARVEST_DEPTH = 2
GATE = Path("scripts") / "anonymity-gate.py"
BASE_REF = "origin/main"
# As duas listas do portão: mudam só com a aprovação do dono, e o patch (D20) não as conta.
LIST_FILES = ("scripts/public-names.txt", "scripts/private-names.sha256")
REDO_REASON = "rebase"
# As variáveis que apontam outro repo: com elas, `git -C <dir>` age no repo delas.
GIT_LOCATION = ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY",
                "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_COMMON_DIR")
# As que trocam a config lida ou a saída do diff. As GIT_CONFIG* saem todas (GIT_CONFIG_GLOBAL,
# GIT_CONFIG_SYSTEM, GIT_CONFIG_PARAMETERS, GIT_CONFIG_COUNT...); o XDG_CONFIG_HOME também, para o git
# ler a config global do HOME do Context.
GIT_OVERRIDES = ("XDG_CONFIG_HOME", "GIT_DIFF_OPTS", "GIT_EXTERNAL_DIFF")
GATE_FINDING = re.compile(r'.+:[0-9]+: (lista|colheita|email|caminho|segredo) ".*"')
GATE_CLEAN = "ok: camada 1 limpa"
TERM_KEYS = frozenset({"termo", "onde", "contexto"})


class StoreError(Exception):
    """A loja, o git ou o portão não deixaram o passo terminar. A mensagem diz por quê."""


# --- processos ---------------------------------------------------------------------------------

def run(cmd, cwd=None, timeout=RUN_TIMEOUT, env=None):
    """(rc, saída) do comando, com stdout e stderr juntos e decodificados sem erro. Nunca levanta:
    o tempo esgotado dá rc 124; o comando que não chegou a rodar (binário ausente, outro OSError ao
    lançar, um NUL num argumento ou no cwd) dá rc 127."""
    rc, raw = run_bytes(cmd, cwd=cwd, timeout=timeout, env=env)
    return rc, _decode(raw)


def run_bytes(cmd, cwd=None, timeout=RUN_TIMEOUT, env=None):
    """O `run` com a saída em bytes, sem decodificar: o patch (D20) se calcula sobre os bytes, porque
    dois bytes diferentes fora do UTF-8 viram o mesmo U+FFFD na decodificação."""
    try:
        proc = subprocess.run([str(c) for c in cmd], cwd=None if cwd is None else str(cwd), env=env,
                              stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                              timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        return 124, exc.output or b""
    except (OSError, ValueError) as exc:  # ValueError: o subprocess recusa um NUL no argumento ou no cwd
        return 127, str(exc).encode("utf-8", "replace")
    return proc.returncode, proc.stdout or b""


def _decode(raw):
    return (raw or b"").decode("utf-8", "replace")


def git_env(home=None, nosystem=False, neutral=False):
    """O ambiente de um git daqui: sem as variáveis de localização e de config herdadas.

    `home` vira o HOME (a config global lida é a do Context). `nosystem` tira a config de sistema.
    `neutral` não lê config nenhuma: o diff do patch e o portão não podem mudar com a config local."""
    env = {k: v for k, v in os.environ.items()
           if k not in GIT_LOCATION and k not in GIT_OVERRIDES and not k.startswith("GIT_CONFIG")}
    if home is not None:
        env["HOME"] = str(home)
    if nosystem or neutral:
        env["GIT_CONFIG_NOSYSTEM"] = "1"
    if neutral:
        env["GIT_CONFIG_GLOBAL"] = os.devnull
    return env


def _git(args, cwd, env, what):
    """A saída do git em `cwd`, ou StoreError com o comando e a saída."""
    rc, out = run(["git", "-C", str(cwd), *args], env=env)
    if rc != 0:
        raise StoreError(f"{what}: git {' '.join(args)} saiu {rc}: {out.strip()[:500]}")
    return out


def store_clone(ctx):
    """O clone de trabalho da loja. O Context já conferiu o `.git` e o marketplace.json."""
    if ctx.store is None:
        raise StoreError("sem loja: falta na config a chave store com o clone de trabalho da loja, "
                         "ou ela nao aponta um clone com o marketplace da loja")
    return ctx.store


# --- colheita ----------------------------------------------------------------------------------

def expand(term):
    """O termo; com 2 ou mais palavras, também cada par de palavras vizinhas (`a b` e `a_b`) e cada
    palavra com MIN_WORD letras ou mais. Termo em branco dá o conjunto vazio."""
    term = term.strip() if isinstance(term, str) else ""
    if not term:
        return set()
    out = {term}
    words = term.split()
    if len(words) >= 2:
        for a, b in zip(words, words[1:]):
            out.update({f"{a} {b}", f"{a}_{b}"})
        out.update(w for w in words if len(w) >= MIN_WORD)
    return out


def origin_terms(url):
    """O nome do repo de uma URL de `origin` e, quando ela tem host, o dono (cada pasta antes do nome).
    Caminho local e `file://` não têm host: a pasta acima do repo não é dono (M22)."""
    url = (url or "").strip()
    host, path = "", url
    full = re.fullmatch(r"([A-Za-z][A-Za-z0-9+.-]*)://([^/]*)(.*)", url)
    scp = re.fullmatch(r"(?:[^@/\\]+@)?([^:/\\]+):(.+)", url)
    if full:
        scheme, authority, path = full.groups()
        host = "" if scheme.lower() == "file" else authority
    elif scp and len(scp.group(1)) > 1:  # `x:` de uma letra é unidade do Windows, não host
        host, path = scp.groups()
    parts = [p for p in re.split(r"[/\\]+", path) if p]
    if not parts:
        return []
    name = parts[-1][:-4] if parts[-1].endswith(".git") else parts[-1]
    owners = parts[:-1] if host else []
    return [t for t in owners + [name] if t]


def _origin_of(repo, env):
    rc, out = run(["git", "-C", str(repo), "remote", "get-url", "origin"], env=env)
    return origin_terms(out) if rc == 0 else []


def _repos(root, depth=HARVEST_DEPTH):
    """Cada pasta com `.git` sob `root`, da profundidade 1 até `depth`. Raiz ausente não é erro."""
    found, level = [], [Path(root)]
    for _ in range(depth):
        nxt = []
        for folder in level:
            try:
                children = sorted(p for p in folder.iterdir() if p.name != ".git" and p.is_dir())
            except OSError:
                continue
            for child in children:
                if (child / ".git").exists():
                    found.append(child)
                nxt.append(child)
        level = nxt
    return found


def _git_config(key, env, cwd):
    # Sem --global: com o ~/.gitconfig presente, o --global não lê o ~/.config/git/config.
    rc, out = run(["git", "-C", str(cwd), "config", "--get", key], env=env)
    return out.strip() if rc == 0 else ""


def _source_lines(path):
    try:
        text = Path(path).read_bytes().decode("utf-8", "replace")
    except OSError:
        return []
    return [line.strip() for line in text.splitlines() if line.strip() and not line.strip().startswith("#")]


def harvest(ctx, cwd=None):
    """Os nomes locais, já passados pelo `expand` (spec 5.6 e O5)."""
    env = git_env(home=ctx.home, nosystem=True)
    raw = [ctx.home.name]
    for root in ctx.harvest_roots:
        for repo in _repos(root):
            raw.append(repo.name)
            raw += _origin_of(repo, env)
    name = _git_config("user.name", env, ctx.home)
    email = _git_config("user.email", env, ctx.home)
    raw += [name, email, email.partition("@")[0] if "@" in email else ""]
    host = socket.gethostname()
    raw += [host, host.split(".")[0]]
    for source in ctx.private_sources:
        raw += _source_lines(source)
    if cwd is not None:
        rc, top = run(["git", "-C", str(cwd), "rev-parse", "--show-toplevel"], env=env)
        if rc == 0 and top.strip():
            root = Path(top.strip())
            raw += [root.name] + _origin_of(root, env)
    terms = set()
    for item in raw:
        for line in str(item).splitlines():
            terms |= expand(line)
    return terms


def _inside_repo(path):
    return any((p / ".git").exists() for p in [Path(path), *Path(path).parents])


def write_harvest(ctx, cwd=None):
    """Grava a colheita em <dados>/colheita.txt, um termo por linha, com permissão 0o600. Recusa a
    pasta de dados dentro de um repo: a colheita nunca grava nome em repo."""
    data = Path(os.path.realpath(ctx.data_dir))
    if _inside_repo(data):
        raise StoreError(f"a pasta de dados esta dentro de um repo git: {data}. A colheita fica fora de repo.")
    path = data / HARVEST_FILE
    _atomic_write(path, "".join(t + "\n" for t in sorted(harvest(ctx, cwd))).encode("utf-8"))
    return path


def _atomic_write(path, body):
    """Grava `body` num temporário novo (O_EXCL, 0o600) da mesma pasta e o põe no lugar de `path` com
    os.replace. Quem lê o arquivo antigo (um portão rodado à mão com `--extra`) nunca o vê truncado
    ou pela metade, e o arquivo antigo com outra permissão nunca recebe os nomes novos. O temporário
    de uma falha sai no `finally`: não fica arquivo com nomes colhidos para trás."""
    path = Path(path)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.{os.urandom(6).hex()}.tmp")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    done = False
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(body)
        os.replace(tmp, path)
        done = True
    finally:
        if not done:
            try:
                os.unlink(tmp)
            except OSError:
                pass


# --- o worktree do lote ------------------------------------------------------------------------

def _suffix(tentativa):
    if not isinstance(tentativa, int) or isinstance(tentativa, bool) or tentativa < 1:
        raise StoreError(f"tentativa fora do dominio: {tentativa!r}")
    return "" if tentativa == 1 else f"-r{tentativa}"


def worktree_path(ctx, rid, lote, tentativa=1):
    rw_auto._safe(rid, "id")
    rw_auto._safe(lote, "lote")
    return ctx.home / ".wt" / f"retrofit-auto-{lote}-{rid}{_suffix(tentativa)}"


def branch_name(rid, lote, tentativa=1):
    rw_auto._safe(rid, "id")
    rw_auto._safe(lote, "lote")
    return f"retrofit-auto/{lote}-{rid}{_suffix(tentativa)}"


def _lote_of_triage(ctx, rid, lote):
    for item in rw_auto.triage(ctx, rid)["lotes"]:
        if item["lote"] == lote:
            return item
    raise StoreError(f"{rid}/{lote} nao e um lote da triagem da retro {rid}")


def _last_line(ctx, rid, lote):
    return rw_auto.last_lines(rw_auto.read_registry(ctx)).get(f"{rid}/{lote}")


def prepare(ctx, rid, lote, redo=False):
    """O worktree ligado do lote, do `origin/main` recém-buscado, e o retrofit.json dele.

    Chamado de novo, devolve o retrofit.json que já existe. `redo` abre a tentativa seguinte só
    quando a última linha do lote é `segurado` por `rebase` (D23); a anterior fica no lugar. Com a
    tentativa atual ainda sem selo, o `redo` devolve a atual: rodar duas vezes não abre duas."""
    store = store_clone(ctx)
    found = _lote_of_triage(ctx, rid, lote)
    path = rw_auto.lote_dir(ctx, rid, lote) / "retrofit.json"
    tentativa = 1
    if redo:
        last = _last_line(ctx, rid, lote)
        if not last or last.get("resultado") != "segurado" or last.get("motivo") != REDO_REASON:
            raise StoreError(f"--redo so vale quando a ultima linha de {rid}/{lote} e `segurado` por "
                             f"`{REDO_REASON}`")
        if not path.exists():
            raise StoreError(f"--redo sem retrofit.json de {rid}/{lote}: rode prepare sem --redo")
        current = rw_auto.load_retrofit(path)
        if current["commit"] is None:
            return current
        tentativa = current["tentativa"] + 1
        # Nada é apagado (D23): o retrofit.json da tentativa anterior fica como retrofit-r<n>.json.
        _atomic_write(path.with_name(f"retrofit-r{current['tentativa']}.json"), path.read_bytes())
    elif path.exists():
        return rw_auto.load_retrofit(path)
    worktree = worktree_path(ctx, rid, lote, tentativa)
    branch = branch_name(rid, lote, tentativa)
    env = git_env(home=ctx.home)
    _git(["fetch", "origin"], store, env, "fetch")
    worktree.parent.mkdir(parents=True, exist_ok=True)
    _git(["worktree", "add", "-q", "-b", branch, str(worktree), BASE_REF], store, env, "worktree")
    base = _git(["rev-parse", "HEAD"], worktree, env, "base").strip()
    retrofit = {"id": rid, "lote": lote, "plugin": found["plugin"], "tipo": found["tipo"], "tentativa": tentativa,
                "worktree": str(worktree), "ramo": branch, "base": base, "licoes": list(found["licoes"]),
                "fases": None, "commit": None, "versao": None, "patch": None}
    rw_auto._fields(retrofit, rw_auto.RETROFIT_SPEC, "retrofit.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    rw_auto._write_json(path, retrofit)
    return retrofit


# --- o selo ------------------------------------------------------------------------------------

# As linhas do diff que o patch conta além das `+` e `-`: o cabeçalho que nomeia o arquivo e o modo.
# Um arquivo vazio novo ou apagado e uma troca só de modo não têm linha `+`/`-`: só estas os nomeiam.
# O rebase não as muda. Ficam fora os `@@` (números de linha) e o `index ` (os shas dos blobs).
PATCH_HEADERS = (b"diff --git ", b"new file mode ", b"deleted file mode ", b"old mode ", b"new mode ")


def _git_bytes(args, cwd, env, what):
    rc, out = run_bytes(["git", "-C", str(cwd), *args], env=env)
    if rc != 0:
        raise StoreError(f"{what}: git {' '.join(args)} saiu {rc}: {_decode(out).strip()[:500]}")
    return out


def patch_id(worktree):
    """O sha256 do que o ramo muda (D20 e M13), sobre os bytes de `git diff -U0 --no-renames
    origin/main...HEAD` sem os dois arquivos de lista: as linhas `+` e `-` (os nomes de arquivo vêm nas
    `+++` e `---`), as de PATCH_HEADERS, e a mensagem de cada commit. O rebase não o muda; mudar
    conteúdo, nome, modo ou mensagem muda."""
    env = git_env(neutral=True)
    exclude = [f":(exclude){f}" for f in LIST_FILES]
    diff = _git_bytes(["-c", "core.quotePath=false", "diff", "-U0", "--no-renames", "--text", "--no-ext-diff",
                       "--no-textconv", "--src-prefix=a/", "--dst-prefix=b/", "--no-color", "--no-relative",
                       f"{BASE_REF}...HEAD", "--", ".", *exclude], worktree, env, "patch")
    message = _git_bytes(["log", "--format=%B", f"{BASE_REF}..HEAD"], worktree, env, "patch")
    digest = hashlib.sha256()
    for line in diff.split(b"\n"):
        if line.startswith((b"+", b"-")) or line.startswith(PATCH_HEADERS):
            digest.update(line + b"\n")
    digest.update(b"\0" + message)
    return digest.hexdigest()


def _gate(worktree, *args):
    gate = Path(worktree) / GATE
    return run([sys.executable, gate, *args, "--base", BASE_REF, "--repo", worktree], cwd=worktree,
               env=git_env(neutral=True))


def _private_harvest(ctx, cwd):
    """A colheita de uma chamada só, num arquivo novo dela (O_EXCL, 0o600) na pasta de dados. Duas
    retros ao mesmo tempo, com `cwd` diferentes, nunca leem a colheita uma da outra (T7-race): o
    colheita.txt partilhado fica para o verbo `harvest`. Quem chama remove o arquivo."""
    data = Path(os.path.realpath(ctx.data_dir))
    if _inside_repo(data):
        raise StoreError(f"a pasta de dados esta dentro de um repo git: {data}. A colheita fica fora de repo.")
    data.mkdir(parents=True, exist_ok=True)
    path = data / f".colheita-{os.getpid()}-{os.urandom(6).hex()}.txt"
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write("".join(t + "\n" for t in sorted(harvest(ctx, cwd))).encode("utf-8"))
    except BaseException:
        _unlink(path)
        raise
    return path


def _unlink(path):
    try:
        os.unlink(path)
    except OSError:
        pass


def layer1(ctx, rid, worktree):
    """Os achados da camada 1 no que o ramo acrescenta, com a colheita feita agora (com o `cwd` do
    pedido.json), num arquivo só desta chamada. Saída do portão fora do formato é StoreError, nunca
    "nada achado" (C1)."""
    pedido = rw_auto.load_pedido(rw_auto.retro_dir(ctx, rid) / "pedido.json")
    extra = _private_harvest(ctx, pedido["cwd"])
    try:
        rc, out = _gate(worktree, "--camada1", "--extra", extra)
    finally:
        _unlink(extra)
    lines = [line for line in out.splitlines() if line.strip()]
    findings = [line for line in lines if GATE_FINDING.fullmatch(line)]
    if rc == 0 and lines == [GATE_CLEAN]:
        return []
    if rc == 1 and findings and lines == findings + [f"{len(findings)} achado(s) na camada 1"]:
        return findings
    raise StoreError(f"camada 1 inutilizavel: o portao saiu {rc} com: {out.strip()[:500]}")


def new_terms(worktree):
    """Os termos novos do ramo para a camada 2: [{termo, onde, contexto}]. Portão fora de rc 0 ou JSON
    fora do formato é StoreError (C1)."""
    rc, out = _gate(worktree, "--termos")
    if rc != 0:
        raise StoreError(f"termos novos: o portao saiu {rc} com: {out.strip()[:500]}")
    try:
        terms = json.loads(out)
    except ValueError:
        raise StoreError(f"termos novos: saida do portao nao e JSON: {out.strip()[:500]}") from None
    if not isinstance(terms, list) or not all(
            isinstance(t, dict) and set(t) == TERM_KEYS and all(isinstance(v, str) for v in t.values())
            for t in terms):
        raise StoreError(f"termos novos: saida do portao fora do formato: {out.strip()[:500]}")
    return terms


def _lessons(raw, allowed, where):
    out = []
    for item in raw:
        text = str(item).strip()
        if not re.fullmatch(r"[1-9][0-9]*", text):
            raise StoreError(f"licao fora do formato (um numero): {text!r}")
        if int(text) not in allowed:
            raise StoreError(f"a licao {text} nao e do lote {where}: as dele sao {sorted(allowed)}")
        if int(text) not in out:
            out.append(int(text))
    if not out:
        raise StoreError("--licoes sem nenhuma licao")
    return out


def _version(worktree, plugin):
    path = Path(worktree) / "plugins" / plugin / ".claude-plugin" / "plugin.json"
    try:
        version = json.loads(path.read_bytes().decode("utf-8")).get("version")
    except (OSError, ValueError, AttributeError) as exc:
        raise StoreError(f"versao ilegivel em {path}: {exc}") from None
    if not isinstance(version, str) or not version.strip():
        raise StoreError(f"{path} sem `version`")
    return version


def seal(ctx, rid, lote, licoes, fases):
    """O selo do executor. Confere as lições contra o lote da triagem e as fases contra PHASES antes
    de gravar qualquer coisa; completa o retrofit.json; grava termos-novos.json no diretório do lote
    (C4); roda a camada 1. Cada lição do lote fora de `licoes` ganha linha `segurado` por
    `executor-recusou` (C9). Devolve {commit, versao, patch, termos, camada1}."""
    found = _lote_of_triage(ctx, rid, lote)
    chosen = _lessons(licoes, set(found["licoes"]), f"{rid}/{lote}")
    phases = []
    for phase in fases:
        if phase not in PHASES:
            raise StoreError(f"fase fora de {', '.join(sorted(PHASES))}: {phase!r}")
        if phase not in phases:
            phases.append(phase)
    folder = rw_auto.lote_dir(ctx, rid, lote)
    retrofit = rw_auto.load_retrofit(folder / "retrofit.json")
    worktree = worktree_path(ctx, rid, lote, retrofit["tentativa"])
    env = git_env(neutral=True)
    count = _git(["rev-list", "--count", f"{BASE_REF}..HEAD"], worktree, env, "selo").strip()
    if count in ("", "0"):
        raise StoreError(f"o ramo de {rid}/{lote} nao tem commit acima do {BASE_REF}")
    commit = _git(["rev-parse", "HEAD"], worktree, env, "selo").strip()
    versao = _version(worktree, retrofit["plugin"])
    patch = patch_id(worktree)
    termos = new_terms(worktree)
    camada1 = layer1(ctx, rid, worktree)
    rw_auto._write_json(folder / "termos-novos.json", {"patch": patch, "termos": termos})
    retrofit.update(licoes=chosen, fases=phases, commit=commit, versao=versao, patch=patch)
    rw_auto._write_json(folder / "retrofit.json", retrofit)
    open_items = rw_auto.last_lines(rw_auto.read_registry(ctx))
    for n in found["licoes"]:
        item = f"{rid}/{found['plugin']}#{n}"
        last = open_items.get(item)
        if n not in chosen and not (last and last.get("resultado") == "segurado"
                                    and last.get("motivo") == "executor-recusou"):
            rw_auto.hold_item(ctx, rid, item, "executor-recusou", f"fora do selo de {rid}/{lote}")
    return {"commit": commit, "versao": versao, "patch": patch, "termos": termos, "camada1": camada1}


# --- linha de comando --------------------------------------------------------------------------

USAGE = {
    "prepare": "prepare <id> <lote> [--redo]",
    "seal": "seal <id> <lote> --licoes L1,L2 [--fases a,b]",
    "harvest": "harvest",
}


def _ascii(text):
    return str(text).encode("ascii", "backslashreplace").decode("ascii")


def _split(value):
    return [v for v in value.split(",") if v.strip()]


def _parse(verb, args):
    """(posicionais, opções) ou None quando o uso está errado."""
    flags = {"prepare": {"--redo": False}, "seal": {"--licoes": True, "--fases": True}, "harvest": {}}[verb]
    positional, options, i = [], {}, 0
    while i < len(args):
        arg = args[i]
        if arg in flags:
            if arg in options:
                return None
            if flags[arg]:
                if i + 1 >= len(args):
                    return None
                options[arg] = args[i + 1]
                i += 2
                continue
            options[arg] = True
        elif arg.startswith("--"):
            return None
        else:
            positional.append(arg)
        i += 1
    wanted = 0 if verb == "harvest" else 2
    if len(positional) != wanted or (verb == "seal" and "--licoes" not in options):
        return None
    return positional, options


def cli(verb, args, ctx):
    """rc 0 certo; 1 recusado (achado da camada 1 no `seal`); 2 uso, StoreError, arquivo do fluxo fora
    do formato ou OSError, com a mensagem em ASCII no stderr e sem traceback."""
    parsed = _parse(verb, args)
    if parsed is None:
        sys.stderr.write(f"retrofit-watch: uso: retrofit_watch.py {USAGE[verb]}\n")
        return 2
    positional, options = parsed
    try:
        if verb == "prepare":
            result = prepare(ctx, *positional, redo=bool(options.get("--redo")))
        elif verb == "seal":
            result = seal(ctx, *positional, _split(options["--licoes"]), _split(options.get("--fases", "")))
        else:
            path = write_harvest(ctx)
            result = {"termos": len(path.read_text(encoding="utf-8").splitlines()), "arquivo": str(path)}
    except (StoreError, rw_auto.Malformed, OSError) as exc:
        sys.stderr.write(_ascii(f"retrofit-watch: {exc}") + "\n")
        return 2
    sys.stdout.write(json.dumps(result, indent=2) + "\n")
    return 1 if verb == "seal" and result["camada1"] else 0
