"""retrofit-watch, modo autônomo: a porta de publicação (spec 5.7).

A porta (`publish <id> <lote>`) chama `refuse` antes de publicar e `hold` quando uma guarda reprova.
As guardas não fazem push: só leem o worktree do lote, o rebaseiam sobre o `origin/main` e rodam as
portas da loja (testes, `validate-versions.py`, auditoria, camada 1 do portão de anonimização). O push
e a instalação moram no `Effects`, que só o `publish` chama, depois de `refuse` passar (D22, D25).

O worktree e o ramo saem do `<id>`, do `<lote>` e da `tentativa` (D9), nunca dos campos `worktree` e
`ramo` do retrofit.json. Os arquivos do fluxo se leem das pastas do Context (C4): `pedido.json`,
`licoes.json` e `veredito.json` da pasta da retro; `retrofit.json`, `anonimato.json` e `aprovado.json`
da pasta do lote. Todo git roda pelo `rw_store.git_env` (C5): sem as variáveis de localização herdadas
e com o HOME do Context.
"""
import json
import os
import re
import shutil
import sys
import tarfile
import tempfile
import time
from pathlib import Path

import retrofit_watch as rw
import rw_auto
import rw_store

# Os motivos que a aprovação do dono substitui (spec 5.7, itens 1, 7, 8, 10 e 11; D19).
OVERRIDABLE = ("sem-veredito", "nao-publicavel", "muda-description", "regra-repetida", "diff-alem-das-licoes",
               "teto", "auto-dry")
# Os que viram linha `erro`, não `segurado`: a porta não chegou a decidir.
ERRORS = ("fetch", "push", "trava", "interno")
GATE_REASONS = ("escopo", "arvore-suja", "rebase", "coautoria", "sem-marca", "sem-bump", "sem-veredito",
                "fora-do-pedido", "nao-publicavel", "muda-description", "nome-privado", "sem-anonimato", "revisao-desatualizada",
                "termo-nao-publico", "regra-repetida", "diff-alem-das-licoes", "testes", "validate-versions",
                "auditoria", "fase-de-auditoria", "teto", "auto-dry") + ERRORS
# Os motivos de nome: só o dono os resolve, ensinando o portão (O7). A aprovação com um deles libera a
# mudança das listas na guarda 5 (C2), nunca a recusa por nome.
NAME_REASONS = rw_auto.NAME_REASONS

# O que um retrofit pode tocar: a pasta do plugin do lote e os arquivos da loja que listam a versão.
SCOPE = ("plugins/<plugin>/", ".claude-plugin/marketplace.json", "README.md", ".agents/plugins/marketplace.json",
         "docs/codex/compatibility.md", "docs/codex/smokes.json")
# As duas listas do portão: mudam só com a aprovação do dono por nome (C2).
OWNER_ONLY = ("scripts/private-names.sha256", "scripts/public-names.txt")
PUBLIC_LIST, PRIVATE_LIST = "scripts/public-names.txt", "scripts/private-names.sha256"

SKILL_MAX_LINES = 400
SKILL_MAX_CHARS = 16000
AUDITOR = Path("plugins/skill-quality-audit/skills/skill-quality-audit/scripts/audit_skill_quality.py")
AUDIT_GATE = Path("plugins/retrofit-skill/scripts/audit_gate.py")
AUDIT_FLAGS = ("--format", "json", "--claims", "--desc-budget", "0", "--external", "off")
MARKER = "Retrofit-Mode"
CO_AUTHOR = re.compile(r"(?im)^[ \t]*co-authored-by[ \t]*:")
FRONTMATTER_VERSION = re.compile(r"\s*version\s*:.*")
VERSION_FORM = re.compile(r"([0-9]+)\.([0-9]+)\.([0-9]+)")
# A `description` do frontmatter de um SKILL.md, como o check_release_sync.py do retrofit-skill a lê.
SKILL_DESCRIPTION = re.compile(r"^description:\s*(.*?)(?=\n[A-Za-z0-9_-]+:|\n---)", re.S | re.M)
DESCRIPTION_SUFFIX = "__description"
DETAIL_MAX = 1500

# A porta que publica (D22, D25).
PUBLISH_LOCK = "publish.lock"
PUBLISH_LOCK_WAIT = 900
APPROVED = "autonomous-approved"
BATCH_SSH = rw_store.BATCH_SSH
# O `instalacao` da linha `publicado` que dá rc 0; os outros (`update`, `cache-difere`) dão rc 4.
INSTALLED = ("ok", "nao-instalado")
# O que a cópia instalada e o worktree têm e não conta na comparação (M7): a marca de uso do Claude
# Code e o bytecode.
CACHE_SKIP_DIRS = (".in_use", "__pycache__")
CACHE_SKIP_SUFFIX = ".pyc"
SHA_SHORT = 7


def _lote_kind(lote):
    """(plugin, tipo) pelo nome do lote (D2): `<plugin>` é `auto`, `<plugin>__description` é `description`."""
    rw_auto._safe(lote, "lote")
    if lote.endswith(DESCRIPTION_SUFFIX) and len(lote) > len(DESCRIPTION_SUFFIX):
        return lote[:-len(DESCRIPTION_SUFFIX)], "description"
    return lote, "auto"


def _retrofit(ctx, rid, lote):
    """O retrofit.json do lote, conferido contra o `<id>` e o `<lote>`. Ausente, inválido ou de outro
    lote é Malformed: a porta não sabe o que publicar, e não grava linha."""
    plugin, tipo = _lote_kind(lote)
    path = rw_auto.lote_dir(ctx, rid, lote) / "retrofit.json"
    retrofit = rw_auto.load_retrofit(path)
    got = (retrofit["id"], retrofit["lote"], retrofit["plugin"], retrofit["tipo"])
    if got != (rid, lote, plugin, tipo):
        raise rw_auto.Malformed(f"{path}: e de {got}, nao de {(rid, lote, plugin, tipo)}")
    return retrofit


def _short(text):
    text = str(text).strip()
    return text if len(text) <= DETAIL_MAX else text[:DETAIL_MAX] + " [...]"


class _Porta:
    """O que as guardas leem de um lote. O worktree e o ramo saem do id, do lote e da tentativa."""

    def __init__(self, ctx, rid, lote, notes):
        self.ctx, self.rid, self.lote, self.notes = ctx, rid, lote, notes
        self.plugin, self.tipo = _lote_kind(lote)
        self.folder = rw_auto.lote_dir(ctx, rid, lote)
        self.retrofit = _retrofit(ctx, rid, lote)
        tentativa = self.retrofit["tentativa"]
        self.worktree = rw_store.worktree_path(ctx, rid, lote, tentativa)
        self.branch = rw_store.branch_name(rid, lote, tentativa)
        self.env = rw_store.git_env(home=ctx.home, nosystem=True)
        self.neutral = rw_store.git_env(neutral=True)
        path = self.folder / "aprovado.json"
        self.approval = None
        if path.exists():
            self.approval = list(rw_auto.load_aprovado(path)["motivos"])
        self.skipped = set(self.approval or ()) & set(OVERRIDABLE)
        # O sha que as guardas conferem: a guarda do rebase o grava; antes dela, None (item 10).
        self.head = None

    def git(self, *args, what="porta"):
        return rw_store._git(list(args), self.worktree, self.env, what)

    def names(self, *extra):
        """Os caminhos que o ramo muda, sem renomeação (o nome velho e o novo aparecem os dois)."""
        out = rw_store._git(["-c", "core.quotePath=false", "diff", "--name-only", "-z", "--no-renames", *extra,
                             f"{rw_store.BASE_REF}...HEAD"], self.worktree, self.neutral, "porta")
        return [p for p in out.split("\0") if p]

    def diff(self, *paths):
        """O diff -U0 do ramo, lido como o patch_id lê: `--text`, sem diff externo nem textconv e no ambiente
        neutro. Um `.gitattributes` do ramo com `binary` não esconde linha nova (T8-r1-text), e um nome com
        acento sai sem aspas, como o `+++ b/` que o `linhas_do_diff` lê (N1)."""
        return rw_store._git(["-c", "core.quotePath=false", "diff", "-U0", "--text", "--no-color", "--no-ext-diff", "--no-textconv", "--src-prefix=a/",
                              "--dst-prefix=b/", f"{rw_store.BASE_REF}...HEAD", "--", *paths],
                             self.worktree, self.neutral, "porta")

    def pedido(self):
        return rw_auto.retro_pedido(self.ctx, self.rid)


def _added_lines(diff):
    return [line[1:].strip() for line in diff.splitlines() if line.startswith("+") and not line.startswith("+++")]


def _removed_lines(diff):
    return [line[1:].strip() for line in diff.splitlines() if line.startswith("-") and not line.startswith("---")]


def _entries(lines):
    return [line for line in lines if line and not line.startswith("#")]


# --- as guardas, na ordem da porta --------------------------------------------------------------
# Cada uma devolve (motivo, detalhe) ou None.

def _g_place(p):
    """1. O worktree derivado não é o clone da loja, existe como raiz de um repo e está no ramo
    derivado, que não é o `main`."""
    store = Path(os.path.realpath(rw_store.store_clone(p.ctx)))
    real = Path(os.path.realpath(p.worktree))
    if real == store:
        return "escopo", f"o worktree do lote e o clone da loja: {p.worktree}"
    rc, top = rw_store.run(["git", "-C", real, "rev-parse", "--show-toplevel"], env=p.env)
    if rc != 0 or Path(os.path.realpath(top.strip())) != real:
        return "escopo", f"{p.worktree} nao existe ou nao e a raiz de um worktree git"
    current = p.git("branch", "--show-current").strip()
    if p.branch == "main" or current == "main":
        return "escopo", "o ramo do lote e o main"
    if current != p.branch:
        return "escopo", f"o worktree esta no ramo {current!r}, nao em {p.branch!r}"
    return None


def _hidden(p):
    """Os caminhos do índice com `assume-unchanged` (letra minúscula no `ls-files -v`) ou `skip-worktree`
    (`S`): o `status --porcelain` não mostra a mudança deles, e a porta roda o portão e as listas do disco
    (Final-F2)."""
    out = p.git("-c", "core.quotePath=false", "ls-files", "-v", "-z")
    found = []
    for entry in out.split("\0"):
        tag, _, path = entry.partition(" ")
        if path and (tag.islower() or tag == "S"):
            found.append(path)
    return found


def _g_clean(p):
    """2. A árvore do worktree está limpa, e nenhum arquivo do índice esconde a mudança dele do status."""
    out = p.git("status", "--porcelain", "--untracked-files=all")
    if out.strip():
        return "arvore-suja", _short(out)
    hidden = _hidden(p)
    if hidden:
        return "arvore-suja", _short("assume-unchanged ou skip-worktree no indice: " + ", ".join(hidden))
    return None


# O ambiente de rede mora no rw_store: o fetch do `prepare`, a guarda 3, o fetch do `_publish` e o push usam
# o mesmo, o `remote_env` (Final-F8, item 11).
network_env = rw_store.network_env


def _g_fetch(p):
    """3. `git fetch origin`, sem nunca esperar credencial no terminal. Falha é `fetch`, nunca "em dia"."""
    rc, out = rw_store.run(["git", "-C", p.worktree, "fetch", "origin"], env=rw_store.remote_env(p.ctx, p.worktree))
    return ("fetch", _short(f"git fetch origin saiu {rc}: {out}")) if rc != 0 else None


def _g_rebase(p):
    """4. Rebase sobre o `origin/main` (D7). Com conflito, `git rebase --abort`: o ramo fica como estava."""
    rc, out = rw_store.run(["git", "-C", p.worktree, "rebase", rw_store.BASE_REF], env=p.env)
    if rc == 0:
        p.head = p.git("rev-parse", "HEAD").strip()
        return None
    rw_store.run(["git", "-C", p.worktree, "rebase", "--abort"], env=p.env)
    return "rebase", _short(f"git rebase {rw_store.BASE_REF} saiu {rc}: {out}")


def _in_scope(path, plugin):
    folder, files = SCOPE[0].replace("<plugin>", plugin), SCOPE[1:]
    return path.startswith(folder) or path in files


def _last_name_hold(p):
    """O `detalhe` da última linha `segurado` do lote por um motivo de nome, ou None."""
    item = f"{p.rid}/{p.lote}"
    last = None
    for line in rw_auto.read_registry(p.ctx):
        if line.get("item") == item and line.get("resultado") == "segurado" and line.get("motivo") in NAME_REASONS:
            last = line
    return None if last is None else str(last.get("detalhe") or "")


def _g_scope(p):
    """5. Um commit só, cada caminho no SCOPE; as listas do portão só com a aprovação do dono por nome (C2)."""
    count = p.git("rev-list", "--count", f"{rw_store.BASE_REF}..HEAD").strip()
    if count != "1":
        return "escopo", f"o ramo tem {count} commit(s) acima do {rw_store.BASE_REF}; a porta publica um so"
    paths = p.names()
    outside = [x for x in paths if x not in OWNER_ONLY and not _in_scope(x, p.plugin)]
    if outside:
        return "escopo", _short("fora do escopo do lote: " + ", ".join(outside))
    if not [x for x in paths if x in OWNER_ONLY]:
        return None
    if not set(p.approval or ()) & set(NAME_REASONS):
        return "escopo", "as listas do portao so mudam com a aprovacao do dono por nome-privado ou termo-nao-publico"
    detail = _last_name_hold(p)
    if detail is None:
        return "escopo", f"as listas do portao mudaram sem linha `segurado` por nome de {p.rid}/{p.lote}"
    uncited = [t for t in _entries(_added_lines(p.diff(PUBLIC_LIST))) if f'"{t}"' not in detail]
    if uncited:
        return "escopo", _short("termos novos na lista de publicos que a recusa nao citou: " + ", ".join(uncited))
    if _entries(_removed_lines(p.diff(PRIVATE_LIST))):
        return "escopo", "o commit tira hash da lista de privados: so o dono faz isso, a mao"
    return None


def _message(p):
    return p.git("log", "-1", "--format=%B")


def _g_coauthor(p):
    """6. Sem `Co-authored-by` na mensagem."""
    return ("coautoria", "o commit tem Co-authored-by") if CO_AUTHOR.search(_message(p)) else None


def _g_marker(p):
    """7. O trailer `Retrofit-Mode` é `autonomous`; com aprovado.json, também `autonomous-approved`."""
    out = p.git("log", "-1", f"--format=%(trailers:key={MARKER},valueonly)")
    values = [v.strip() for v in out.splitlines() if v.strip()]
    allowed = {"autonomous"} | ({"autonomous-approved"} if p.approval is not None else set())
    if len(values) != 1 or values[0] not in allowed:
        return "sem-marca", f"{MARKER} esperado {sorted(allowed)}, achado {values}"
    return None


def _show(p, ref, path):
    """O texto de `path` na árvore de `ref`, ou None quando ele não está lá."""
    rc, out = rw_store.run(["git", "-C", p.worktree, "show", f"{ref}:{path}"], env=p.neutral)
    return out if rc == 0 else None


ABSENT = object()


def _manifest_version(p, ref):
    """A `version` do plugin.json do plugin em `ref`: ABSENT sem o arquivo, None com ele ilegível."""
    text = _show(p, ref, f"plugins/{p.plugin}/.claude-plugin/plugin.json")
    if text is None:
        return ABSENT
    try:
        data = json.loads(text)
    except ValueError:
        return None
    version = data.get("version") if isinstance(data, dict) else None
    return version if isinstance(version, str) else None


def _version_parts(version):
    m = VERSION_FORM.fullmatch(version) if isinstance(version, str) else None
    return tuple(int(x) for x in m.groups()) if m else None


def _g_bump(p):
    """7b. A versão do plugin.json no HEAD é maior que a do `origin/main`, por número (Final-F5). Sem ela,
    o `claude plugin update` não traz nada, e o lote fica atrás. Um plugin novo, sem plugin.json no
    `origin/main`, passa."""
    base = _manifest_version(p, rw_store.BASE_REF)
    if base is ABSENT:
        return None
    head = _manifest_version(p, "HEAD")
    shown = "ausente" if head is ABSENT else head
    bt, ht = _version_parts(base), _version_parts(head)
    if bt is None or ht is None:
        return "sem-bump", f"versao fora de X.Y.Z: {base!r} no {rw_store.BASE_REF}, {shown!r} no HEAD"
    if ht <= bt:
        return "sem-bump", f"a versao do plugin.json nao sobe: {base} no {rw_store.BASE_REF}, {head} no HEAD"
    return None


def _veredito(p):
    return rw_auto.retro_veredito(p.ctx, p.rid)


def _g_verdict(p):
    """8. O veredito.json existe e é válido."""
    try:
        _veredito(p)
    except rw_auto.Malformed as exc:
        return "sem-veredito", _short(exc)
    return None


def _lessons(p):
    """As lições do retrofit.json, de licoes.json: [(n, lição ou None)]."""
    licoes = rw_auto.retro_licoes(p.ctx, p.rid)
    return [(n, licoes.get(str(n))) for n in p.retrofit["licoes"]]


def _g_request(p):
    """9. Cada lição é do plugin do lote e cabe no pedido, com a config de agora (D24)."""
    pedido = p.pedido()
    for n, licao in _lessons(p):
        if licao is None:
            return "fora-do-pedido", f"a licao {n} nao esta no licoes.json"
        if licao["plugin"] != p.plugin:
            return "fora-do-pedido", f"a licao {n} e do plugin {licao['plugin']}, nao do lote {p.lote}"
        if not rw_auto.in_request(p.ctx, pedido, licao):
            return "fora-do-pedido", f"a licao {n} ({licao['plugin']}/{licao['skill']}) nao cabe no pedido"
    return None


def _g_publishable(p):
    """10a. Cada lição classifica como `publicar` (no lote `description`, como `ramo-pronto`)."""
    try:
        veredito = _veredito(p)
    except rw_auto.Malformed:
        # Com `sem-veredito` aprovado, a guarda 8 foi pulada: sem veredito, cada lição classifica como
        # `segurar/sem-veredito`, e a porta segura com `nao-publicavel`, que o dono pode aprovar (I1).
        if "sem-veredito" not in p.skipped:
            raise
        veredito = {}
    wanted = "publicar" if p.tipo == "auto" else "ramo-pronto"
    for n, licao in _lessons(p):
        destino, motivo = rw_auto.classify(licao, veredito.get(str(n)))
        if destino != wanted:
            return "nao-publicavel", f"a licao {n} classifica como {destino} ({motivo})"
    return None


def _json_at(p, ref, path):
    text = _show(p, ref, path)
    if text is None:
        return None
    try:
        return json.loads(text)
    except ValueError:
        return ILLEGIBLE


ILLEGIBLE = "<ilegivel>"


def _descriptions(p, ref):
    """{lugar: description} do plugin em `ref`, nos lugares que o check_release_sync.py confere: o
    plugin.json, o bloco do marketplace.json e o frontmatter de cada SKILL.md do plugin. Arquivo ausente
    não entra; ilegível entra como ILLEGIBLE."""
    out = {}
    manifest = _json_at(p, ref, f"plugins/{p.plugin}/.claude-plugin/plugin.json")
    if manifest is not None:
        out["plugin.json"] = manifest.get("description") if isinstance(manifest, dict) else ILLEGIBLE
    catalog = _json_at(p, ref, ".claude-plugin/marketplace.json")
    if isinstance(catalog, dict) and isinstance(catalog.get("plugins"), list):
        blocks = [e for e in catalog["plugins"] if isinstance(e, dict) and e.get("name") == p.plugin]
        if blocks:
            out["marketplace.json"] = [e.get("description") for e in blocks]
    elif catalog is not None:
        out["marketplace.json"] = ILLEGIBLE
    listing = rw_store._git(["ls-tree", "-r", "-z", "--name-only", ref, "--", f"plugins/{p.plugin}/skills"],
                            p.worktree, p.neutral, "description")
    skill_md = re.compile(rf"plugins/{re.escape(p.plugin)}/skills/[^/]+/SKILL\.md")
    for path in sorted(x for x in listing.split("\0") if skill_md.fullmatch(x)):
        m = SKILL_DESCRIPTION.search(_show(p, ref, path) or "")
        out[path] = m.group(1).strip().strip('"') if m else ILLEGIBLE
    return out


def _g_description(p):
    """10b. O lote `description` não sai sozinho (D12): fica o ramo pronto. Num lote `auto`, a
    `description` do HEAD é a do `origin/main` em cada lugar, com ou sem a flag `muda_description` das
    lições (Final-F6)."""
    if p.tipo == "description":
        return "muda-description", f"ramo pronto: {p.branch}"
    before, after = _descriptions(p, rw_store.BASE_REF), _descriptions(p, "HEAD")
    changed = sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k))
    if changed:
        return "muda-description", _short("o lote auto muda a description em: " + ", ".join(changed))
    return None


# A ordem importa (T7-I3): a camada 1 e os termos rodam o anonymity-gate.py do worktree do lote. Só
# depois da guarda 5, que recusa commit no portão e nas listas sem a aprovação do dono, a porta pode
# confiar no que ele diz. Uma guarda de nome antes da 5 leria um portão que o próprio ramo afrouxou.

def _g_layer1(p):
    """11. A camada 1, rodada de novo sobre o diff final e a mensagem, com a colheita de agora."""
    found = rw_store.layer1(p.ctx, p.rid, p.worktree)
    return ("nome-privado", _short("; ".join(found))) if found else None


def _anonimato(p):
    return rw_auto.load_anonimato(p.folder / "anonimato.json")


def _g_anonimato(p):
    """12. O anonimato.json existe e é válido."""
    try:
        _anonimato(p)
    except rw_auto.Malformed as exc:
        return "sem-anonimato", _short(exc)
    return None


def _g_patch(p):
    """13. A segunda passada do revisor é do diff de agora (D20)."""
    patch = rw_store.patch_id(p.worktree)
    if _anonimato(p)["patch"] != patch:
        return "revisao-desatualizada", "o anonimato.json e de outro patch: o commit mudou depois da revisao"
    return None


def _g_terms(p):
    """14. Cada termo novo, recalculado agora (nunca o termos-novos.json), é `publico` na revisão."""
    verdicts = {t["termo"]: t["veredito"] for t in _anonimato(p)["termos"]}
    bad = [t["termo"] for t in rw_store.new_terms(p.worktree) if verdicts.get(t["termo"]) != "publico"]
    if bad:
        return "termo-nao-publico", _short("; ".join(f'"{t}": {verdicts.get(t, "sem veredito")}' for t in bad))
    return None


def _g_rule(p):
    """15. A mudança não repete nem contradiz regra já escrita (O2)."""
    text = _anonimato(p)["regra_repetida"]
    return ("regra-repetida", _short(text)) if text is not None else None


def _g_beyond(p):
    """16. O diff não faz mais do que as lições declaradas (O8)."""
    text = _anonimato(p)["fora_das_licoes"]
    return ("diff-alem-das-licoes", _short(text)) if text is not None else None


def _is_test_dir(path, plugin):
    return re.fullmatch(rf"plugins/{re.escape(plugin)}/(skills/[^/]+/)?tests", path) is not None


def _tree_test_dirs(p, ref):
    """As pastas de teste do plugin na árvore de `ref`, como caminhos relativos."""
    out = rw_store._git(["ls-tree", "-r", "-d", "-z", "--name-only", ref, "--", f"plugins/{p.plugin}"],
                        p.worktree, p.neutral, "testes")
    return sorted(x for x in out.split("\0") if x and _is_test_dir(x, p.plugin))


def _test_dirs(p):
    """(pastas de teste do plugin no HEAD, as do `origin/main`). As duas saem da árvore do git, nunca do disco:
    uma pasta ignorada ou fora do índice que sobra no worktree não conta como teste do ramo (I2)."""
    return _tree_test_dirs(p, "HEAD"), _tree_test_dirs(p, rw_store.BASE_REF)


def _g_tests(p):
    """17. Os testes do plugin e a suíte da raiz (D11), sem gravar bytecode no worktree (M7). Uma pasta de
    teste do `origin/main` que o ramo tira é `testes` (I2); a nota só vale para plugin que nunca teve teste."""
    env = dict(p.env, PYTHONDONTWRITEBYTECODE="1")
    here, base = _test_dirs(p)
    gone = [d for d in base if d not in here]
    if gone:
        return "testes", "o ramo tira pasta de testes do origin/main: " + ", ".join(gone)
    dirs = [p.worktree / d for d in here]
    if not dirs:
        p.notes.append(f"testes: plugin {p.plugin} sem pasta de testes")
    for folder in dirs + [p.worktree / "tests"]:
        rel = folder.relative_to(p.worktree).as_posix()
        rc, out = rw_store.run([sys.executable, "-m", "unittest", "discover", "-s", rel, "-p", "test_*.py"],
                               cwd=p.worktree, env=env)
        if rc != 0:
            return "testes", _short(f"{rel} saiu {rc}: {out[-1000:]}")
    return None


def _g_versions(p):
    """18. `validate-versions.py` rc 0."""
    rc, out = rw_store.run([sys.executable, p.worktree / "scripts" / "validate-versions.py"], cwd=p.worktree,
                           env=dict(p.env, PYTHONDONTWRITEBYTECODE="1"))
    return ("validate-versions", _short(f"saiu {rc}: {out[-1000:]}")) if rc != 0 else None


def _version_lines(text):
    """Os números das linhas `version:` do frontmatter (a do topo e a aninhada em `metadata:`)."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return set()
    out = set()
    for i, line in enumerate(lines[1:], start=2):
        if line.strip() == "---":
            break
        if FRONTMATTER_VERSION.fullmatch(line):
            out.add(i)
    return out


def _read_text(path):
    try:
        return Path(path).read_bytes().decode("utf-8", "replace")
    except OSError:
        return None


def _crosses(before, after):
    """O SKILL.md passa do teto agora (antes <= teto < depois), em linhas ou em caracteres (C3)."""
    def size(text):
        return (len(text.splitlines()), len(text)) if text else (0, 0)
    (bl, bc), (al, ac) = size(before), size(after)
    return bl <= SKILL_MAX_LINES < al or bc <= SKILL_MAX_CHARS < ac


def _audit_json(p, skill):
    """A saída JSON do auditor para `skill`, ou (motivo, detalhe) quando ele não deu resultado."""
    rc, out = rw_store.run([sys.executable, p.worktree / AUDITOR, skill, *AUDIT_FLAGS], cwd=p.worktree,
                           env=dict(p.env, PYTHONDONTWRITEBYTECODE="1"))
    if rc not in (0, 1):
        return None, ("auditoria", _short(f"o auditor saiu {rc} em {skill}: {out[-500:]}"))
    try:
        data = json.loads(out)
        data["skills"][0]["findings"]
    except (ValueError, KeyError, IndexError, TypeError):
        return None, ("auditoria", _short(f"saida do auditor fora do formato em {skill}: {out[-500:]}"))
    return data, None


def _extract_base(p, dest):
    raw = rw_store._git_bytes(["archive", "--format=tar", rw_store.BASE_REF, f"plugins/{p.plugin}"], p.worktree,
                              p.neutral, "auditoria")
    tar_path = dest / "base.tar"
    tar_path.write_bytes(raw)
    # O filtro `data` recusa link, caminho absoluto e `..`; o Python sem ele levanta TypeError (D25).
    with tarfile.open(tar_path) as tar:
        tar.extractall(dest / "base", filter="data")
    return dest / "base"


def _g_audit(p):
    """19. O gate da auditoria do /retrofit-skill, rodado pela porta (D10), e as fases que a mudança
    exige no selo (D21)."""
    skills = sorted(md.parent for md in (p.worktree / "plugins" / p.plugin).glob("skills/*/SKILL.md"))
    if not skills:
        p.notes.append("auditoria: plugin sem SKILL.md")
        return None
    missing = [str(x) for x in (AUDITOR, AUDIT_GATE) if not (p.worktree / x).is_file()]
    if missing:
        return "auditoria", "ausente no worktree: " + ", ".join(missing)
    touched, added = set(p.names()), p.names("--diff-filter=A")
    claims, grows = [], []
    p.ctx.data_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=p.ctx.data_dir, prefix=".porta-") as tmp:
        tmp = Path(tmp)
        base = _extract_base(p, tmp)
        for i, skill in enumerate(skills):
            rel = skill.relative_to(p.worktree).as_posix()
            box = tmp / f"skill-{i}"
            box.mkdir()
            before_md = base / rel / "SKILL.md"
            if before_md.is_file():
                antes, bad = _audit_json(p, base / rel)
                if bad:
                    return bad
            else:  # skill nova: sem dívida antiga
                antes = {"skills": [{"findings": [], "claims": []}]}
            depois, bad = _audit_json(p, skill)
            if bad:
                return bad
            (box / "antes.json").write_text(json.dumps(antes), encoding="utf-8")
            (box / "depois.json").write_text(json.dumps(depois), encoding="utf-8")
            (box / "diff.txt").write_text(p.diff(rel), encoding="utf-8")
            rc, out = rw_store.run([sys.executable, p.worktree / AUDIT_GATE, box], cwd=p.worktree,
                                   env=dict(p.env, PYTHONDONTWRITEBYTECODE="1"))
            if rc != 0:
                return "auditoria", _short(f"o audit_gate.py saiu {rc} em {rel}: {out[-500:]}")
            lines = out.splitlines()
            novo = [line for line in lines if line.startswith("NOVO")]
            if novo:
                return "auditoria", _short(f"{rel}: " + "; ".join(novo))
            after_text = _read_text(skill / "SKILL.md") or ""
            versions = _version_lines(after_text)
            for line in lines:
                if not line.startswith("CLAIM"):
                    continue
                parts = line.split(None, 2)
                where, _, number = (parts[1] if len(parts) > 1 else "").rpartition(":")
                # A versão do frontmatter muda em todo retrofit; o audit_gate.py sempre a acusa (C3).
                if where == "SKILL.md" and number.isdigit() and int(number) in versions:
                    continue
                claims.append(f"{rel}: {line}")
            if f"{rel}/SKILL.md" in touched and _crosses(_read_text(before_md), after_text):
                grows.append(f"{rel}/SKILL.md")
    asset = re.compile(rf"plugins/{re.escape(p.plugin)}/skills/[^/]+/(references|scripts|assets)/.+")
    created = [x for x in added if asset.fullmatch(x)]
    phases = set(p.retrofit["fases"] or ())
    for phase, why in (("claim-check", claims), ("self-containment", created), ("refactoring", grows)):
        if why and phase not in phases:
            return "fase-de-auditoria", _short(f"{phase}: " + "; ".join(why))
    return None


def _g_caps(p):
    """20. O teto da sessão (spec 5.10), por plugin (M12), sem contar este lote."""
    session = p.pedido()["sessao"]
    others = [line for line in rw_auto.read_registry(p.ctx)
              if not (line.get("id") == p.rid and line.get("plugin") == p.plugin)]
    limits = p.ctx.auto_limits
    per_skill = rw_auto.used(others, session, plugin=p.plugin)
    per_session = rw_auto.used(others, session)
    if per_skill >= limits["per_skill"] or per_session >= limits["per_session"]:
        return "teto", (f"{per_skill} de {limits['per_skill']} do plugin e {per_session} de "
                        f"{limits['per_session']} da sessao ja usados")
    return None


def _g_still(p):
    """21. O HEAD é o que a guarda do rebase gravou: um commit feito no worktree durante as guardas não sobe
    sem elas (item 10, C3). Um HEAD que sai e volta ao mesmo sha passa: o que sobe é esse sha."""
    now = p.git("rev-parse", "HEAD").strip()
    if now != p.head:
        return "arvore-suja", f"o HEAD mudou durante as guardas: {p.head} -> {now}"
    return None


def _g_dry(p):
    """22. O `auto-dry` faz tudo menos publicar: vem por último, para dizer se o resto passaria."""
    return ("auto-dry", "mode auto-dry: nada se publica") if p.ctx.mode == "auto-dry" else None


GUARDS = (
    ("escopo", _g_place),
    ("arvore-suja", _g_clean),
    ("fetch", _g_fetch),
    ("rebase", _g_rebase),
    ("escopo", _g_scope),
    ("coautoria", _g_coauthor),
    ("sem-marca", _g_marker),
    ("sem-bump", _g_bump),
    ("sem-veredito", _g_verdict),
    ("fora-do-pedido", _g_request),
    ("nao-publicavel", _g_publishable),
    ("muda-description", _g_description),
    ("nome-privado", _g_layer1),
    ("sem-anonimato", _g_anonimato),
    ("revisao-desatualizada", _g_patch),
    ("termo-nao-publico", _g_terms),
    ("regra-repetida", _g_rule),
    ("diff-alem-das-licoes", _g_beyond),
    ("testes", _g_tests),
    ("validate-versions", _g_versions),
    ("auditoria", _g_audit),
    ("teto", _g_caps),
    ("arvore-suja", _g_still),
    ("auto-dry", _g_dry),
)


def refuse(ctx, rid, lote, notes):
    """(motivo, detalhe) da primeira guarda que reprova, ou None quando o lote pode subir (o `_check`)."""
    return _check(ctx, rid, lote, notes)[0]


def _check(ctx, rid, lote, notes):
    """(recusa, head): a recusa é (motivo, detalhe) da primeira guarda que reprova, ou None quando o lote
    pode subir; o head é o sha que as guardas conferiram (`_Porta.head`), o único que a porta publica.

    Com aprovado.json, pula a guarda cujo motivo está nos `motivos` dele e em OVERRIDABLE; o que a
    porta pulou entra em `notes`. retrofit.json ausente ou inválido é Malformed. Um StoreError de uma
    guarda é `interno` (a 3 e a 4 dão `fetch` e `rebase` por conta própria): erro de git nunca passa
    por aprovação. Outra exceção sobe (D25)."""
    p = _Porta(ctx, rid, lote, notes)
    try:
        for motivo, guard in GUARDS:
            if motivo in p.skipped:
                notes.append(f"{motivo}: substituido pela aprovacao do dono")
                continue
            found = guard(p)
            if found is not None:
                return found, p.head
    except rw_store.StoreError as exc:
        return ("interno", _short(exc)), p.head
    return None, p.head


def _head(worktree):
    if not Path(worktree).is_dir():
        return None
    rc, out = rw_store.run(["git", "-C", worktree, "rev-parse", "HEAD"], env=rw_store.git_env(neutral=True))
    return out.strip() if rc == 0 else None


def hold(ctx, rid, lote, motivo, detalhe):
    """Grava a linha `segurado` do lote, ou `erro` quando o motivo está em ERRORS, e a devolve. A linha
    leva o ramo, o worktree e o commit derivados (o lote `description` registra o ramo pronto)."""
    if motivo not in GATE_REASONS:
        raise rw_auto.Malformed(f"motivo fora dos da porta: {motivo!r}")
    plugin, _ = _lote_kind(lote)
    retrofit = _retrofit(ctx, rid, lote)
    worktree = rw_store.worktree_path(ctx, rid, lote, retrofit["tentativa"])
    branch = rw_store.branch_name(rid, lote, retrofit["tentativa"])
    session = rw_auto.retro_pedido(ctx, rid)["sessao"]
    resultado = "erro" if motivo in ERRORS else "segurado"
    return rw_auto._hold(ctx, session, rid, f"{rid}/{lote}", plugin, list(retrofit["licoes"]), resultado, motivo,
                         detalhe, lote, commit=_head(worktree) or retrofit["commit"], ramo=branch,
                         worktree=str(worktree))


# --- a porta que publica (D22, D25) -------------------------------------------------------------

def _files(root):
    """{caminho relativo: bytes} dos arquivos sob `root`, fora o `.in_use` e o bytecode (M7)."""
    out = {}
    for folder, dirs, names in os.walk(root):
        dirs[:] = [d for d in dirs if d not in CACHE_SKIP_DIRS]
        for name in names:
            if name in CACHE_SKIP_DIRS or name.endswith(CACHE_SKIP_SUFFIX):
                continue
            path = Path(folder) / name
            out[path.relative_to(root).as_posix()] = path.read_bytes()
    return out


class Effects:
    """O que a porta faz fora do worktree: o push e a cópia instalada. Os testes usam um `FixtureEffects`,
    que herda o `push` real e só empurra para o `origin` da fixture. Todo `~` resolve pelo `ctx.home` (C5):
    o installed_plugins.json e o cache lidos são os do Context."""

    def __init__(self, ctx):
        self.ctx = ctx

    def push(self, worktree, sha):
        """`git push --no-follow-tags origin <sha>:refs/heads/main`, sem força, sem esperar senha no
        terminal: (True, saída) ou (False, por quê). Sobe o `sha` que a porta conferiu, nunca o HEAD do
        worktree na hora do push (Final-F7); um `push.followTags` do dono não leva tag (Final-F9)."""
        env = rw_store.remote_env(self.ctx, worktree)
        ref = f"{sha}:refs/heads/main"
        rc, out = rw_store.run(["git", "-C", worktree, "push", "--no-follow-tags", "origin", ref], env=env)
        if rc != 0:
            return False, _short(f"git push origin {ref} saiu {rc}: {out}")
        return True, _short(out)

    def _user_install(self, plugin):
        """O plugin da loja está instalado no escopo `user` (D18)? Malformed com o arquivo ilegível."""
        path = self.ctx.home / ".claude/plugins/installed_plugins.json"
        if not path.exists():
            return False
        data = rw_auto._read_json(path)
        entries = data.get("plugins") if isinstance(data, dict) else None
        if not isinstance(entries, dict):
            raise rw_auto.Malformed(f"{path}: sem o objeto `plugins`")
        found = entries.get(f"{plugin}@{rw.MARKETPLACE}")
        return isinstance(found, list) and any(isinstance(e, dict) and e.get("scope") == "user" for e in found)

    def refresh_install(self, plugin):
        """`claude plugin marketplace update <loja>` e `claude plugin update <plugin>@<loja> --scope user`.
        Sem o `claude` no PATH, (False, "claude ausente"); plugin fora do escopo `user`, (True,
        "nao-instalado"), sem chamar nada."""
        exe = shutil.which("claude")
        if not exe:
            return False, "claude ausente"
        try:
            if not self._user_install(plugin):
                return True, "nao-instalado"
        except rw_auto.Malformed as exc:
            return False, _short(exc)
        env = dict(os.environ, HOME=str(self.ctx.home))
        for args in (("plugin", "marketplace", "update", rw.MARKETPLACE),
                     ("plugin", "update", f"{plugin}@{rw.MARKETPLACE}", "--scope", "user")):
            rc, out = rw_store.run([exe, *args], env=env)
            if rc != 0:
                return False, _short(f"claude {' '.join(args)} saiu {rc}: {out}")
        return True, "atualizado"

    def cache_matches(self, ctx, worktree, plugin, versao):
        """A cópia instalada (`~/.claude/plugins/cache/<loja>/<plugin>/<versao>`) tem os mesmos arquivos,
        com os mesmos bytes, que `plugins/<plugin>` do worktree, fora o `.in_use` e o bytecode (M7). A
        versão e o plugin viram pasta: fora do formato seguro, Malformed."""
        rw_auto._safe(plugin, "plugin")
        rw_auto._safe(versao, "versao")
        cache = ctx.home / ".claude/plugins/cache" / rw.MARKETPLACE / plugin / versao
        if not cache.is_dir():
            return False, f"sem copia instalada em {cache}"
        here, there = _files(Path(worktree) / "plugins" / plugin), _files(cache)
        differ = sorted(set(here) ^ set(there)) + sorted(k for k in set(here) & set(there) if here[k] != there[k])
        if differ:
            return False, _short("a copia instalada difere em: " + ", ".join(differ))
        return True, f"copia instalada igual: {cache}"


def _sealed_patch(ctx, rid, lote):
    """O `patch` da segunda passada do revisor (anonimato.json), ou None sem ela."""
    try:
        return rw_auto.load_anonimato(rw_auto.lote_dir(ctx, rid, lote) / "anonimato.json")["patch"]
    except rw_auto.Malformed:
        return None


def _published_patches(worktree, env):
    """O patch do commit do HEAD contra o pai dele: com a mensagem dele e, quando o trailer é o da
    aprovação, também com o trailer de antes da emenda da porta (o revisor selou esse)."""
    message = rw_store._git_bytes(["log", "--format=%B", "HEAD^..HEAD"], worktree, env, "porta")
    found = {rw_store.patch_id(worktree, base="HEAD^")}
    approved, reviewed = f"{MARKER}: {APPROVED}".encode(), f"{MARKER}: autonomous".encode()
    if message.count(approved) == 1:
        found.add(rw_store.patch_id(worktree, base="HEAD^", message=message.replace(approved, reviewed)))
    return found


def already_published(worktree, retrofit, sealed):
    """O commit do lote já está no `origin/main`? Vale quando as quatro coisas valem (T9-pub):
    - o HEAD está no ramo do lote (o do id, do lote e da tentativa, nunca o `ramo` do retrofit.json);
    - o HEAD não é a `base` do retrofit.json (o worktree recém-preparado é ancestral de qualquer
      `origin/main` novo);
    - o HEAD é ancestral do `origin/main`;
    - o patch do commit do HEAD é o `sealed`, o da revisão: um worktree levado a outro commit do
      `origin/main` (por `reset --hard`) está no ramo e é ancestral, mas não é o lote."""
    if not Path(worktree).is_dir() or not sealed:
        return False
    env = rw_store.git_env(neutral=True)
    branch = rw_store.branch_name(retrofit["id"], retrofit["lote"], retrofit["tentativa"])
    rc, current = rw_store.run(["git", "-C", worktree, "branch", "--show-current"], env=env)
    if rc != 0 or current.strip() != branch:
        return False
    rc, head = rw_store.run(["git", "-C", worktree, "rev-parse", "HEAD"], env=env)
    head = head.strip()
    if rc != 0 or not head or head == retrofit["base"]:
        return False
    rc, _ = rw_store.run(["git", "-C", worktree, "merge-base", "--is-ancestor", head, rw_store.BASE_REF], env=env)
    if rc != 0:
        return False
    try:
        return sealed in _published_patches(worktree, env)
    except rw_store.StoreError:  # sem pai (raiz), por exemplo: não é o commit de um lote
        return False


def mark_done(ctx, session, key):
    """A retro da skill acabou (D6): no estado da sessão, sob a trava dele, a chave entra em `done` e a
    entrada dela fica com `reviews = MAX_REVIEWS`. O Stop hook não a pede de novo."""
    with rw.State(ctx, session) as state:
        st = state.data
        if key not in st["done"]:
            st["done"].append(key)
        entry = st["skills"].get(key)
        if isinstance(entry, dict):
            entry["reviews"] = rw.MAX_REVIEWS
        state.save()


def _record(ctx, line):
    """Grava a linha e a devolve; sem conseguir gravar, devolve a linha não gravada. Nunca levanta."""
    try:
        return rw_auto.append_registry(ctx, line)
    except Exception:  # noqa: BLE001 — o publish nunca levanta (D25)
        return dict(line, ts=int(time.time()))


def _error(ctx, rid, lote, motivo, detalhe):
    """A linha `erro` do lote pelo `hold`. Sem o retrofit.json ou o pedido.json para montá-la, grava uma
    linha mínima com o porquê no `detalhe`. Nunca levanta."""
    try:
        return hold(ctx, rid, lote, motivo, detalhe)
    except Exception as exc:  # noqa: BLE001
        detalhe = _short(f"{detalhe}; a linha completa falhou: {type(exc).__name__}: {exc}")
    session = None
    try:
        session = rw_auto.retro_pedido(ctx, rid)["sessao"]
    except Exception:  # noqa: BLE001
        pass
    lote_text = str(lote)
    plugin = lote_text[:-len(DESCRIPTION_SUFFIX)] if lote_text.endswith(DESCRIPTION_SUFFIX) else lote_text
    return _record(ctx, rw_auto._line(session, rid, f"{rid}/{lote}", plugin, [], "erro", motivo, detalhe, lote=lote))


def _mark_approved(ctx, worktree, env, reviewed):
    """Troca o trailer por `Retrofit-Mode: autonomous-approved` com `commit --amend` e devolve o sha novo.
    A mensagem vem do commit `reviewed`, o que as guardas conferiram, nunca do HEAD (item 10). Depois da
    emenda, a árvore do HEAD é a de `reviewed`, o pai dele é o pai de `reviewed` e o trailer sai com um
    valor só; outra coisa é StoreError."""
    def git(*args):
        return rw_store._git(list(args), worktree, env, "aprovacao")
    tree = git("rev-parse", f"{reviewed}^{{tree}}").strip()
    parent = git("rev-parse", f"{reviewed}^").strip()
    message = git("log", "-1", "--format=%B", reviewed)
    fd, tmp = tempfile.mkstemp(dir=ctx.data_dir, prefix=".mensagem-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as fh:
            fh.write(message)
        # `--where after`: o trailer fica no lugar; no fim, a troca de volta de `_published_patches` não
        # daria a mensagem que o revisor selou (I3).
        git("interpret-trailers", "--in-place", "--where", "after", "--if-exists", "replace", "--trailer",
            f"{MARKER}: {APPROVED}", tmp)
        git("commit", "-q", "--amend", "-F", tmp)
    finally:
        os.unlink(tmp)
    # O HEAD se lê uma vez: as três conferências e o retorno são do mesmo sha. Um commit no worktree
    # entre duas leituras não sobe sem conferência (item 10, rodada 1).
    new = git("rev-parse", "HEAD").strip()
    if git("rev-parse", f"{new}^{{tree}}").strip() != tree:
        raise rw_store.StoreError("aprovacao: a emenda do trailer mudou a arvore do commit")
    if git("rev-parse", f"{new}^").strip() != parent:
        raise rw_store.StoreError("aprovacao: o commit emendado nao tem o pai do commit revisado")
    values = [v.strip() for v in git("log", "-1", f"--format=%(trailers:key={MARKER},valueonly)", new).splitlines()
              if v.strip()]
    if values != [APPROVED]:
        raise rw_store.StoreError(f"aprovacao: {MARKER} depois da emenda: {values}")
    return new


def _plan(ctx, rid, lote, retrofit, worktree, aprovado, detalhe, commit):
    """A linha `publicado` (`instalacao: "pendente"`) e as chaves da sessão a marcar feitas, montadas antes
    do push: depois dele só se grava. O `commit` é o sha conferido, do parâmetro (item 10); ele se acerta
    depois da emenda do trailer."""
    plugin, _ = _lote_kind(lote)
    pedido = rw_auto.retro_pedido(ctx, rid)
    line = rw_auto._line(pedido["sessao"], rid, f"{rid}/{lote}", plugin, list(retrofit["licoes"]), "publicado",
                         None, _short(detalhe), lote=lote)
    line.update(commit=commit, ramo=rw_store.branch_name(rid, lote, retrofit["tentativa"]),
                worktree=str(worktree), versao=rw_store._version(worktree, plugin), aprovado=aprovado,
                instalacao="pendente")
    return line, [e["key"] for e in pedido["skills"] if e["plugin"] == plugin]


def _close(ctx, line):
    """Depois da linha `publicado` do lote: fecha cada lição dele que um selo segurou por
    `executor-recusou` e outro trouxe de volta (T9-seal). Rodar de novo não repete linha."""
    last = rw_auto.last_lines(rw_auto.read_registry(ctx))
    for n in line["licoes"]:
        item = f"{line['id']}/{line['plugin']}#{n}"
        held_line = last.get(item)
        if held_line and held_line.get("resultado") == "segurado" and held_line.get("motivo") == "executor-recusou":
            closing = rw_auto._line(line["sessao"], line["id"], item, line["plugin"], [n], "publicado", None,
                                    f"publicada no lote {line['id']}/{line['lote']}", lote=line["lote"])
            closing.update(commit=line["commit"])
            rw_auto.append_registry(ctx, closing)


def _finish(ctx, line, keys):
    """O fecho do lote publicado: as lições trazidas de volta (`_close`) e a retro feita na sessão (D6).
    Os dois são idempotentes; a porta os roda em toda chamada sobre um lote publicado (T9-r1-up)."""
    _close(ctx, line)
    for key in keys:
        mark_done(ctx, line["sessao"], key)


def _previous(ctx, rid, lote, commit):
    """A última linha `publicado` do lote com este `commit`, ou None."""
    found = None
    for line in rw_auto.read_registry(ctx):
        if line.get("item") == f"{rid}/{lote}" and line.get("resultado") == "publicado" and line.get("commit") == commit:
            found = line
    return found


def _approved_marker(worktree, env):
    out = rw_store._git(["log", "-1", f"--format=%(trailers:key={MARKER},valueonly)"], worktree, env, "porta")
    return [v.strip() for v in out.splitlines() if v.strip()] == [APPROVED]


def _publish(ctx, rid, lote, effects, done):
    plugin, _ = _lote_kind(lote)
    retrofit = _retrofit(ctx, rid, lote)
    worktree = rw_store.worktree_path(ctx, rid, lote, retrofit["tentativa"])
    env = rw_store.git_env(home=ctx.home, nosystem=True)
    if worktree.is_dir():
        # 2. Uma falha deste fetch não se registra aqui: a guarda 3 busca de novo e a grava como `fetch`.
        rw_store.run(["git", "-C", worktree, "fetch", "origin"], env=rw_store.remote_env(ctx, worktree))
    if already_published(worktree, retrofit, _sealed_patch(ctx, rid, lote)):
        # Refaz só a instalação (D22). Sem linha `publicado` deste commit (a porta caiu entre o push e a
        # linha), grava a que faltou. O fecho roda sempre: a chamada de antes pode ter caído no meio dele.
        planned, keys = _plan(ctx, rid, lote, retrofit, worktree, _approved_marker(worktree, env),
                              "o commit ja estava no origin/main", _head(worktree))
        line = _previous(ctx, rid, lote, planned["commit"])
        if line is None:
            line = rw_auto.append_registry(ctx, planned)
        done["line"] = line
        _finish(ctx, line, keys)
    else:
        notes = []
        found, head = _check(ctx, rid, lote, notes)
        if found is not None:
            return hold(ctx, rid, lote, *found)
        approved = (rw_auto.lote_dir(ctx, rid, lote) / "aprovado.json").exists()
        line, keys = _plan(ctx, rid, lote, retrofit, worktree, approved, "; ".join(notes), head)
        reviewed, pushed = head, False
        try:
            if approved:
                line["commit"] = _mark_approved(ctx, worktree, env, reviewed)
            # O sha conferido: o HEAD que as guardas leram (`_Porta.head`, que o `_g_still` confere no fim
            # delas) ou a emenda dele, que só troca a mensagem. Um commit novo no worktree depois disso não
            # sobe (Final-F7, item 10).
            pushed, detail = effects.push(worktree, line["commit"])
        finally:
            # A emenda muda o patch (D20): um push que não saiu devolve o ramo ao commit revisado.
            if approved and not pushed:
                rw_store._git(["reset", "-q", "--soft", reviewed], worktree, env, "porta")
        if not pushed:
            return hold(ctx, rid, lote, "push", detail)
        done["line"] = rw_auto.append_registry(ctx, line)
        _finish(ctx, done["line"], keys)
    line = done["line"]
    ok, detail = effects.refresh_install(plugin)
    if not ok:
        instalacao = "update"
    elif detail == "nao-instalado":
        instalacao = "nao-instalado"
    else:
        same, detail = effects.cache_matches(ctx, worktree, plugin, line["versao"])
        instalacao = "ok" if same else "cache-difere"
    return rw_auto.append_registry(ctx, dict(line, instalacao=instalacao, detalhe=_short(detail)))


def publish(ctx, rid, lote, effects):
    """A porta: publica o lote e devolve a última linha gravada no registro. Nunca levanta (D25).

    1. Prende <dados>/publish.lock por até PUBLISH_LOCK_WAIT s até o fim; sem ela, linha `erro`, `trava`.
    2. `git fetch origin`. Com o commit já no `origin/main` (`already_published`), pula para o passo 6.
    3. `_check`; com recusa, `hold` e fim. O sha que sobe é o que as guardas conferiram (item 10).
    4. Com aprovado.json, o trailer vira `Retrofit-Mode: autonomous-approved` (`commit --amend`).
    5. `effects.push`. Falha: linha `erro`, `push`. Certo: linha `publicado` com `instalacao: "pendente"`,
       o fecho das lições trazidas de volta e `mark_done` na sessão do pedido.json.
    6. `effects.refresh_install` e, com o plugin instalado, `effects.cache_matches`: uma segunda linha
       `publicado` com `instalacao` `ok`, `nao-instalado`, `update` ou `cache-difere`.
    7. Exceção antes da primeira linha `publicado`: linha `erro`, `interno`, com o tipo e a mensagem. Depois
       dela, outra linha `publicado` com `instalacao: "update"` (C10): o commit já está no `origin/main`."""
    done = {}
    try:
        path = ctx.data_dir / PUBLISH_LOCK
        try:
            ctx.data_dir.mkdir(parents=True, exist_ok=True)
            lock = rw._lock(path, PUBLISH_LOCK_WAIT)
        except OSError as exc:
            return _error(ctx, rid, lote, "trava", _short(f"{path}: {exc}"))
        try:
            return _publish(ctx, rid, lote, effects, done)
        finally:
            rw._unlock(lock)
    except Exception as exc:  # noqa: BLE001 — D25: toda exceção vira linha
        detail = _short(f"{type(exc).__name__}: {exc}")
        if "line" in done:
            return _record(ctx, dict(done["line"], instalacao="update", detalhe=detail))
        return _error(ctx, rid, lote, "interno", detail)


def exit_code(line):
    """rc da porta pela linha: 0 publicado e instalado (ou não instalado); 4 publicado com a instalação
    falha; 1 segurado; 3 erro."""
    resultado = line.get("resultado")
    if resultado == "publicado":
        return 0 if line.get("instalacao") in INSTALLED else 4
    return 1 if resultado == "segurado" else 3


def phrase(line):
    """A linha ao dono (spec 5.1), em ASCII com escape."""
    plugin = line.get("plugin")
    if line.get("resultado") == "publicado":
        sha = str(line.get("commit") or "")[:SHA_SHORT]
        text = f"retrofit-watch: {plugin} v{line.get('versao')} publicada sozinha ({sha})"
        if exit_code(line) == 4:
            text += f" — cópia instalada não atualizada: {line.get('instalacao')}"
    else:
        text = f"retrofit-watch: {plugin} segurada — {line.get('motivo')} (ramo {line.get('ramo')})"
    return rw_store._ascii(text)


USAGE = "publish <id> <lote>"


def cli(args, ctx):
    """O verbo `publish <id> <lote>`: a linha em JSON e, na última linha do stdout, a frase ao dono, tudo
    em ASCII (o stdout do Windows é cp1252). rc pelo `exit_code`; 2, sem gravar linha, com a aridade
    errada ou o `<id>` ou o `<lote>` fora do formato seguro."""
    if len(args) != 2 or not all(rw_auto.SAFE_NAME.fullmatch(a) for a in args):
        sys.stderr.write(rw_store._ascii(f"retrofit-watch: uso: retrofit_watch.py {USAGE}, com o id e o lote no "
                                         f"formato seguro; recebido {args!r}") + "\n")
        return 2
    line = publish(ctx, args[0], args[1], Effects(ctx))
    sys.stdout.write(json.dumps(line, indent=2) + "\n" + phrase(line) + "\n")
    return exit_code(line)
