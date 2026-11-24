"""retrofit-watch, modo autônomo: a colheita dos nomes privados, o worktree do lote e o selo do executor.

Roda fora do hook, pelos verbos `harvest`, `prepare` e `seal` de retrofit_watch.py. Chama o git e o
portão de anonimização da loja (`scripts/anonymity-gate.py`); nunca faz push. A exceção é o `criterion`,
que o aviso de startup (`cmd_pending`) chama dentro do hook: só lê, sem rede.

  colheita   os nomes locais que não podem ir à loja pública, fora de qualquer repo e com permissão
             0o600: o verbo `harvest` grava <dados>/colheita.txt; a camada 1 grava a de cada chamada
             num arquivo só dela, passado por `--extra` e removido depois
  prepare    `git fetch origin` no clone da loja e um worktree ligado novo do `origin/main`, num ramo
             que sai do id e do lote; grava <dados>/auto/<id>/<lote>/retrofit.json
  seal       o selo do executor: completa o retrofit.json, grava termos-novos.json e roda a camada 1,
             com o portão de uma cópia do commit selado (`clean_tree`), nunca o do disco do worktree
  criterion  o critério da v2 para o aviso de startup, lido do `origin/main` local, sem `fetch` e com o
             teto de 3 s por chamada ao git; o cache fica em <dados>/criterio.json

Todo git daqui roda sem as variáveis de localização herdadas (um hook do git exporta GIT_DIR) e com o
HOME do Context: o `~` resolve pelo ctx.home, nunca pelo HOME real. Os erros são StoreError; a saída do
portão fora do formato também, nunca uma lista vazia (falha fechada).
"""
import contextlib
import hashlib
import importlib.util
import io
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tarfile
import tempfile
import time
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


BATCH_SSH = "ssh -o BatchMode=yes"


def network_env(env, worktree):
    """O ambiente de um git que fala com o `origin` a partir de `worktree`: nunca espera credencial no
    terminal, nem a senha da chave SSH (T9-ssh). O `ssh -o BatchMode=yes` só entra quando o dono não
    escolheu o ssh: sem GIT_SSH_COMMAND, sem GIT_SSH e sem `core.sshCommand` na config que este mesmo
    ambiente lê no worktree (T9-ssh2). A variável venceria as duas outras escolhas. A porta e o fetch do
    `prepare` usam este mesmo ambiente (Final-F8)."""
    env = dict(env, GIT_TERMINAL_PROMPT="0")
    if "GIT_SSH_COMMAND" in env or "GIT_SSH" in env:
        return env
    rc, out = run(["git", "-C", str(worktree), "config", "--get", "core.sshCommand"], env=env)
    if rc == 0 and out.strip():
        return env
    env["GIT_SSH_COMMAND"] = BATCH_SSH
    return env


def remote_env(ctx, worktree):
    """O único ambiente de um git que fala com o `origin`: o fetch do `prepare`, a guarda do fetch, o
    fetch do `_publish` e o push. Lê a config de sistema (item 11): no Git for Windows o `credential.helper`
    padrão mora nela, e sem ela um `origin` HTTPS daria `fetch` em todo lote. As outras guardas seguem
    com `nosystem=True`."""
    return network_env(git_env(home=ctx.home), worktree)


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

# O que separa as partes de um nome além do espaço (Final-F4): `-`, `_`, `.` e a fronteira do CamelCase
# (`FooBar`, e `HTTPServer` entre `HTTP` e `Server`).
PART_SEPARATORS = re.compile(r"[\s_.-]+")
CAMEL_BOUNDARY = re.compile(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])")


def _parts(term):
    """As partes de um nome. Um e-mail só se parte no espaço: o `.` do domínio não é parte de nome, e a
    parte local entra na colheita sozinha."""
    if "@" in term:
        return term.split()
    return [part for chunk in PART_SEPARATORS.split(term) for part in CAMEL_BOUNDARY.split(chunk) if part]


def expand(term):
    """O termo; com 2 ou mais partes (separadas por espaço, `-`, `_`, `.` ou CamelCase), também cada par
    de partes vizinhas (`a b` e `a_b`), cada parte com MIN_WORD letras ou mais e a frase das partes unidas
    por espaço, por `-`, por `_` e sem separador. A camada 1 casa a frase sem diferença de caixa: o repo
    `foo-bar` pega "Foo Bar" na prosa (Final-F4). Termo em branco dá o conjunto vazio."""
    term = term.strip() if isinstance(term, str) else ""
    if not term:
        return set()
    out = {term}
    words = _parts(term)
    if len(words) >= 2:
        for a, b in zip(words, words[1:]):
            out.update({f"{a} {b}", f"{a}_{b}"})
        out.update(w for w in words if len(w) >= MIN_WORD)
        out.update(joint.join(words) for joint in (" ", "-", "_", ""))
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


def _gone(path):
    """True só quando `path` não existe mais (ou um pedaço dele não é pasta). Outro OSError, como o
    EACCES, é StoreError com o caminho (C8): a pasta que existe e não lê nunca passa por ausente."""
    try:
        os.stat(path)
    except (FileNotFoundError, NotADirectoryError):
        return True
    except OSError as exc:
        raise StoreError(f"colheita: a pasta {path} nao le: {exc}") from exc
    return False


def _origin_of(repo, env):
    """Os termos do `origin` de `repo`. Sem remoto `origin` (rc 2) é nada, e o clone que sumiu depois de
    achado também (T5-r1); outro rc é StoreError (C8): a colheita nunca encolhe em silêncio."""
    rc, out = run(["git", "-C", str(repo), "remote", "get-url", "origin"], env=env)
    if rc == 0:
        return origin_terms(out)
    if rc == 2 or _gone(repo):
        return []
    raise StoreError(f"colheita: o origin de {repo} nao le: git saiu {rc}: {out.strip()[:500]}")


def _repos(root, depth=HARVEST_DEPTH):
    """Cada pasta com `.git` sob `root`, da profundidade 1 até `depth`. Raiz ausente, raiz que é arquivo
    e pasta que sumiu no meio não são erro; a pasta que existe e não lê é StoreError (C8)."""
    found, level = [], [Path(root)]
    for _ in range(depth):
        nxt = []
        for folder in level:
            try:
                children = sorted(p for p in folder.iterdir() if p.name != ".git" and p.is_dir())
            except (FileNotFoundError, NotADirectoryError):
                continue
            except OSError as exc:
                raise StoreError(f"colheita: a pasta {folder} nao le: {exc}") from exc
            for child in children:
                # Não o `exists()`: no 3.12 ele relança o EACCES cru, e no 3.13 pode dar False (T5-r1).
                if not _gone(child / ".git"):
                    found.append(child)
                nxt.append(child)
        level = nxt
    return found


def _git_config(key, env, cwd):
    # Sem --global: com o ~/.gitconfig presente, o --global não lê o ~/.config/git/config.
    # Chave ausente (rc 1) é vazio; outro rc (config ilegível) é StoreError (C8).
    rc, out = run(["git", "-C", str(cwd), "config", "--get", key], env=env)
    if rc == 0:
        return out.strip()
    if rc == 1:
        return ""
    raise StoreError(f"colheita: git config {key} nao le: git saiu {rc}: {out.strip()[:500]}")


def _source_lines(path):
    """As linhas da fonte privada. Fonte ausente é nada; a que existe e não lê é StoreError (C8)."""
    try:
        text = Path(path).read_bytes().decode("utf-8", "replace")
    except FileNotFoundError:
        return []
    except OSError as exc:
        raise StoreError(f"colheita: a fonte privada {path} nao le: {exc}") from exc
    return [line.strip() for line in text.splitlines() if line.strip() and not line.strip().startswith("#")]


def _session_project(cwd, env):
    """O nome e o `origin` do repo do projeto da sessão (spec 5.6). O `cwd` que sumiu, ou que não fica em
    repo nenhum, é nada. Com o `rev-parse` fora do rc 0 e um `.git` no `cwd` ou num pai (o `_gone`, o
    critério da Tarefa 5, sem ler a mensagem do git, que pode vir traduzida), é StoreError com o caminho
    (C8): um `gitfile` quebrado, um `safe.directory` só na config de sistema ou uma config ilegível nunca
    tiram o projeto da colheita em silêncio (Final-F1)."""
    rc, top = run(["git", "-C", str(cwd), "rev-parse", "--show-toplevel"], env=env)
    if rc == 0 and top.strip():
        root = Path(top.strip())
        return [root.name] + _origin_of(root, env)
    # Um caminho com NUL não existe em sistema nenhum (o `os.stat` levantaria ValueError).
    if "\0" in str(cwd):
        return []
    start = Path(os.path.abspath(cwd))
    if _gone(start):
        return []
    for folder in [start, *start.parents]:
        if not _gone(folder / ".git"):
            raise StoreError(f"colheita: o projeto da sessao em {folder} nao le: git saiu {rc}: "
                             f"{top.strip()[:500]}")
    return []


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
        raw += _session_project(cwd, env)
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
    path = _harvest_dir(ctx) / HARVEST_FILE
    _atomic_write(path, _harvest_bytes(ctx, cwd))
    return path


def _harvest_dir(ctx):
    """A pasta de dados, real; StoreError quando ela fica dentro de um repo git."""
    data = Path(os.path.realpath(ctx.data_dir))
    if _inside_repo(data):
        raise StoreError(f"a pasta de dados esta dentro de um repo git: {data}. A colheita fica fora de repo.")
    return data


def _harvest_bytes(ctx, cwd):
    """A colheita serializada: um termo por linha, em ordem, em UTF-8."""
    return "".join(t + "\n" for t in sorted(harvest(ctx, cwd))).encode("utf-8")


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
    _git(["fetch", "origin"], store, remote_env(ctx, store), "fetch")
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


def patch_id(worktree, base=BASE_REF, message=None):
    """O sha256 do que o ramo muda (D20 e M13), sobre os bytes de `git diff -U0 --no-renames
    origin/main...HEAD` sem os dois arquivos de lista: as linhas `+` e `-` (os nomes de arquivo vêm nas
    `+++` e `---`), as de PATCH_HEADERS, e a mensagem de cada commit. O rebase não o muda; mudar
    conteúdo, nome, modo ou mensagem muda. `base` troca o `origin/main` (a porta mede o commit já
    publicado contra `HEAD^`); `message`, em bytes, troca a mensagem lida do log."""
    env = git_env(neutral=True)
    exclude = [f":(exclude){f}" for f in LIST_FILES]
    diff = _git_bytes(["-c", "core.quotePath=false", "diff", "-U0", "--no-renames", "--text", "--no-ext-diff",
                       "--no-textconv", "--src-prefix=a/", "--dst-prefix=b/", "--no-color", "--no-relative",
                       f"{base}...HEAD", "--", ".", *exclude], worktree, env, "patch")
    if message is None:
        message = _git_bytes(["log", "--format=%B", f"{base}..HEAD"], worktree, env, "patch")
    digest = hashlib.sha256()
    for line in diff.split(b"\n"):
        if line.startswith((b"+", b"-")) or line.startswith(PATCH_HEADERS):
            digest.update(line + b"\n")
    digest.update(b"\0" + message)
    return digest.hexdigest()


def _gate(tools, worktree, *args):
    """O portão de `tools` (a cópia do commit, `clean_tree`) sobre o git de `worktree`, sem gravar bytecode
    na cópia. O portão do disco do worktree nunca roda: um `.pyc` ou um `.py` ignorado ali trocaria um
    módulo dele (item 1)."""
    gate = Path(tools) / GATE
    return run([sys.executable, gate, *args, "--base", BASE_REF, "--repo", worktree], cwd=worktree,
               env=dict(git_env(neutral=True), PYTHONDONTWRITEBYTECODE="1"))


def untar(raw, dest):
    """Extrai o tar `raw` (bytes) em `dest`. O filtro `data` recusa link, caminho absoluto e `..`; o
    Python sem ele levanta TypeError, que sobe (D25)."""
    with tarfile.open(fileobj=io.BytesIO(raw)) as tar:
        tar.extractall(dest, filter="data")
    return Path(dest)


TREE_PREFIX = ".porta-"
# O `git archive` lê os atributos de fora da árvore (o arquivo global do dono, `~/.config/git/attributes`,
# e o de sistema) mesmo sem config nenhuma: um `export-ignore` ali tiraria um teste da cópia, e um
# `export-subst` mudaria o conteúdo. Os dois saem; vale o `.gitattributes` da árvore (C5), e também o
# `info/attributes` do `.git` comum: quem escreve dentro do `.git/` já controla o git da porta (C2).
ARCHIVE = ("-c", f"core.attributesFile={os.devnull}", "archive", "--format=tar")


def archive_env():
    """O ambiente neutro do `git archive`, sem o arquivo de atributos de sistema."""
    return dict(git_env(neutral=True), GIT_ATTR_NOSYSTEM="1")


@contextlib.contextmanager
def clean_tree(ctx, worktree, ref):
    """A árvore de `ref`, tirada com `git archive` (ambiente neutro) numa pasta temporária nova sob
    <dados>, que sai no fim (item 1, C1). Ela não tem arquivo ignorado, bytecode nem `.git`: o que a
    porta e o selo rodam da loja sai daqui. Falha do git ou da extração é StoreError."""
    data = Path(ctx.data_dir)
    data.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(dir=data, prefix=TREE_PREFIX))
    try:
        raw = _git_bytes([*ARCHIVE, ref], worktree, archive_env(), "arvore limpa")
        tree = tmp / "arvore"
        try:
            untar(raw, tree)
        except (tarfile.TarError, OSError) as exc:
            raise StoreError(f"arvore limpa: a extracao de {ref} falhou: {exc}") from None
        yield tree
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _private_harvest(ctx, cwd):
    """A colheita de uma chamada só, num arquivo novo dela (O_EXCL, 0o600) na pasta de dados. Duas
    retros ao mesmo tempo, com `cwd` diferentes, nunca leem a colheita uma da outra (T7-race): o
    colheita.txt partilhado fica para o verbo `harvest`. Quem chama remove o arquivo."""
    data = _harvest_dir(ctx)
    data.mkdir(parents=True, exist_ok=True)
    path = data / f".colheita-{os.getpid()}-{os.urandom(6).hex()}.txt"
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(_harvest_bytes(ctx, cwd))
    except BaseException:
        _unlink(path)
        raise
    return path


def _unlink(path):
    try:
        os.unlink(path)
    except OSError:
        pass


def layer1(ctx, rid, worktree, tools):
    """Os achados da camada 1 no que o ramo de `worktree` acrescenta, pelo portão de `tools` (a cópia do
    commit), com a colheita feita agora (com o `cwd` do pedido.json), num arquivo só desta chamada. Saída
    do portão fora do formato é StoreError, nunca "nada achado" (C1)."""
    pedido = rw_auto.retro_pedido(ctx, rid)
    extra = _private_harvest(ctx, pedido["cwd"])
    try:
        rc, out = _gate(tools, worktree, "--camada1", "--extra", extra)
    finally:
        _unlink(extra)
    lines = [line for line in out.splitlines() if line.strip()]
    findings = [line for line in lines if GATE_FINDING.fullmatch(line)]
    if rc == 0 and lines == [GATE_CLEAN]:
        return []
    if rc == 1 and findings and lines == findings + [f"{len(findings)} achado(s) na camada 1"]:
        return findings
    raise StoreError(f"camada 1 inutilizavel: o portao saiu {rc} com: {out.strip()[:500]}")


def new_terms(worktree, tools):
    """Os termos novos do ramo para a camada 2: [{termo, onde, contexto}], pelo portão de `tools` (a cópia
    do commit). Portão fora de rc 0 ou JSON fora do formato é StoreError (C1)."""
    rc, out = _gate(tools, worktree, "--termos")
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
    with clean_tree(ctx, worktree, commit) as tools:
        termos = new_terms(worktree, tools)
        camada1 = layer1(ctx, rid, worktree, tools)
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


# --- o critério da v2 ---------------------------------------------------------------------------
# Spec 5.9 e D15: a conta sai dos commits do `origin/main` LOCAL, nunca do registro, e sem `fetch` (o
# startup tem 10 s). O `origin/main` local anda quando a porta busca.

V2_MIN_PUBLISHED = 10
V2_MIN_DAYS = 14
DAY = 86400
STARTUP_TIMEOUT = 3
CRITERION_FILE = "criterio.json"
# C9: o estouro do teto fica em cache por sha do `origin/main`, por 24 h; depois o critério mede de novo.
CRITERION_RETRY = 86400
MARKER = "Retrofit-Mode"
AUTONOMOUS = "autonomous"
REVERTS = re.compile(r"This reverts commit ([0-9a-f]{7,40})")
NAME_CHECK = "scripts/check-private-names.py"
PRIVATE_LIST = LIST_FILES[1]
# Um registro por commit (0x1e), os campos separados por 0x1f, os valores do trailer por 0x1d.
LOG_FORMAT = f"%H%x1f%ct%x1f%cs%x1f%(trailers:key={MARKER},valueonly,separator=%x1d)%x1f%B%x1e"


class StartupTimeout(StoreError):
    """O git do critério estourou o teto do startup (rc 124)."""


def _startup_git(store, args, what):
    """A saída em bytes do git da loja, com o teto do startup, sem config nenhuma; StartupTimeout com rc 124,
    StoreError com outro rc != 0."""
    rc, out = run_bytes(["git", "--literal-pathspecs", "-C", str(store), *args], timeout=STARTUP_TIMEOUT,
                        env=git_env(neutral=True))
    if rc == 124:
        raise StartupTimeout(f"{what}: git {' '.join(args[:2])} passou de {STARTUP_TIMEOUT} s")
    if rc != 0:
        raise StoreError(f"{what}: git {' '.join(args[:2])} saiu {rc}: {_decode(out).strip()[:500]}")
    return out


def _autonomous(store, head):
    """([[sha, ts, data], ...] dos commits com o trailer exatamente `autonomous`, revertidos): os commits
    do `head` que trazem `This reverts commit <sha>` de um deles."""
    out = _decode(_startup_git(store, ["log", f"--format={LOG_FORMAT}", head], "criterio"))
    records = []
    for record in out.split("\x1e"):
        fields = record.lstrip("\n").split("\x1f", 4)
        if len(fields) == 5:
            records.append(fields)
    commits = []
    for sha, ts, date, trailers, _ in records:
        if [v.strip() for v in trailers.split("\x1d") if v.strip()] == [AUTONOMOUS]:
            commits.append([sha, int(ts), date])
    shas = [c[0] for c in commits]
    reverted = sum(1 for *_, body in records
                   if any(s.startswith(m) for m in REVERTS.findall(body) for s in shas))
    return commits, reverted


def _load_name_check(folder):
    spec = importlib.util.spec_from_file_location("rw_check_private_names", Path(folder) / Path(NAME_CHECK).name)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _leaks(store, head, shas):
    """Os achados do sensor de nomes (o `varrer` do check-private-names.py, com a lista de hashes, os dois
    do `head`) nos arquivos que os commits `shas` tocaram, como estão no `head`. Os arquivos saem do
    `git archive` para uma pasta temporária, que o `varrer` lê sem o git (ela não tem `.git`)."""
    names = _decode(_startup_git(store, ["-c", "core.quotePath=false", "show", "--name-only", "--no-renames",
                                         "--format=", "-z", *shas], "criterio"))
    touched = sorted({n.lstrip("\n") for n in names.split("\0")} - {""})
    present = []
    if touched:
        listed = _decode(_startup_git(store, ["ls-tree", "-r", "-z", "--name-only", head, "--", *touched],
                                      "criterio"))
        present = [n for n in listed.split("\0") if n]
    raw = _startup_git(store, ["archive", "--format=tar", head, "--", NAME_CHECK, PRIVATE_LIST, *present],
                       "criterio")
    wanted = set(present)
    with tempfile.TemporaryDirectory(prefix="rw-criterio-") as tmp:
        tree, tool = Path(tmp) / "arvore", Path(tmp) / "sensor"
        tree.mkdir()
        tool.mkdir()
        with tarfile.open(fileobj=io.BytesIO(raw)) as tar:
            for member in tar:
                if member.name in wanted:
                    target = tree / member.name
                elif member.name == NAME_CHECK:
                    target = tool / Path(NAME_CHECK).name
                elif member.name == PRIVATE_LIST:
                    target = tool / Path(PRIVATE_LIST).name
                else:
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                # O blob de um link simbólico é o caminho do alvo: o sensor lê esse texto, como o `git show`.
                target.write_bytes(member.linkname.encode("utf-8", "surrogateescape") if member.issym()
                                   else tar.extractfile(member).read())
        check = _load_name_check(tool)
        return len(check.varrer(tree, check.carregar(tool / Path(PRIVATE_LIST).name)))


def _cached(ctx, head):
    """O cache do `head`, ou None (ausente, ilegível, de outro sha ou fora do formato)."""
    try:
        data = json.loads((ctx.data_dir / CRITERION_FILE).read_bytes().decode("utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict) or set(data) != {"sha", "commits", "revertidos", "vazados"} or data["sha"] != head:
        return None
    commits, reverted, leaks = data["commits"], data["revertidos"], data["vazados"]
    if not (isinstance(commits, list) and all(
            isinstance(c, list) and len(c) == 3 and isinstance(c[0], str) and rw_auto._int(c[1])
            and isinstance(c[2], str) for c in commits)):
        return None
    if not rw_auto._int(reverted) or not (leaks is None or rw_auto._int(leaks)):
        return None
    return data


def _timed_out(ctx, head, now):
    """True quando <dados>/criterio.json é o estouro do `head`, {sha, estouro}, com menos de 24 h. O
    instante no futuro (o relógio que voltou, a edição à mão) conta como expirado: sem o limite de
    baixo, ele nunca venceria (Final-F7)."""
    try:
        data = json.loads((ctx.data_dir / CRITERION_FILE).read_bytes().decode("utf-8"))
    except (OSError, ValueError):
        return False
    if not isinstance(data, dict) or set(data) != {"sha", "estouro"} or data["sha"] != head:
        return False
    when = data["estouro"]
    if not isinstance(when, (int, float)):
        return False
    return 0 <= now - when < CRITERION_RETRY


def criterion(ctx, now=None):
    """O critério da v2 (spec 5.9): {publicados, dias, revertidos, vazados, desde, cumprido}, ou None sem
    loja. `vazados` é None até os dois pisos passarem. O cache, em <dados>/criterio.json por sha do
    `origin/main`, guarda os commits e o que sai deles; `dias` e `cumprido` se refazem a cada chamada,
    contra `now` (M1). O `git log` ou o `_leaks` que estoura o teto grava {sha, estouro} e deixa o
    StartupTimeout subir; com essa forma do mesmo sha e menos de 24 h, devolve None sem chamar o git log
    (C9). O estouro do `rev-parse` não grava nada: ainda não há sha."""
    store = ctx.store
    if store is None:
        return None
    now = time.time() if now is None else now
    head = _decode(_startup_git(store, ["rev-parse", "--verify", f"{BASE_REF}^{{commit}}"], "criterio")).strip()
    if _timed_out(ctx, head, now):
        return None
    data = _cached(ctx, head)
    changed = data is None
    try:
        if changed:
            commits, reverted = _autonomous(store, head)
            data = {"sha": head, "commits": commits, "revertidos": reverted, "vazados": None}
        commits = data["commits"]
        first = min(commits, key=lambda c: c[1]) if commits else None
        days = max(0, int((now - first[1]) // DAY)) if first else 0
        floors = len(commits) >= V2_MIN_PUBLISHED and days >= V2_MIN_DAYS
        if floors and data["vazados"] is None:
            data["vazados"] = _leaks(store, head, [c[0] for c in commits])
            changed = True
    except StartupTimeout:
        ctx.data_dir.mkdir(parents=True, exist_ok=True)
        rw_auto._write_json(ctx.data_dir / CRITERION_FILE, {"sha": head, "estouro": now})
        raise
    if changed:
        ctx.data_dir.mkdir(parents=True, exist_ok=True)
        rw_auto._write_json(ctx.data_dir / CRITERION_FILE, data)
    return {"publicados": len(commits), "dias": days, "revertidos": data["revertidos"], "vazados": data["vazados"],
            "desde": first[2] if first else None,
            "cumprido": floors and data["revertidos"] == 0 and data["vazados"] == 0}


def criterion_notice(ctx, now=None):
    """A frase do critério cumprido (spec 5.9), com os números medidos; None quando não se cumpre."""
    got = criterion(ctx, now)
    if not got or not got["cumprido"]:
        return None
    return (f"{got['publicados']} retrofits autônomos, {got['revertidos']} revertidos, {got['vazados']} nomes "
            f"vazados desde {got['desde']} — o kit pode entrar (ver a spec do modo autônomo)")


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
