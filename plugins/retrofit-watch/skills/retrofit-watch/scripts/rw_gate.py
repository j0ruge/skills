"""retrofit-watch, modo autônomo: as recusas da porta de publicação (spec 5.7).

A porta (`publish <id> <lote>`) chama `refuse` antes de publicar e `hold` quando uma guarda reprova.
Nada daqui faz push: as guardas só leem o worktree do lote, o rebaseiam sobre o `origin/main` e rodam
as portas da loja (testes, `validate-versions.py`, auditoria, camada 1 do portão de anonimização).

O worktree e o ramo saem do `<id>`, do `<lote>` e da `tentativa` (D9), nunca dos campos `worktree` e
`ramo` do retrofit.json. Os arquivos do fluxo se leem das pastas do Context (C4): `pedido.json`,
`licoes.json` e `veredito.json` da pasta da retro; `retrofit.json`, `anonimato.json` e `aprovado.json`
da pasta do lote. Todo git roda pelo `rw_store.git_env` (C5): sem as variáveis de localização herdadas
e com o HOME do Context.
"""
import json
import os
import re
import sys
import tarfile
import tempfile
from pathlib import Path

import rw_auto
import rw_store

# Os motivos que a aprovação do dono substitui (spec 5.7, itens 1, 7, 8, 10 e 11; D19).
OVERRIDABLE = ("sem-veredito", "nao-publicavel", "muda-description", "regra-repetida", "diff-alem-das-licoes",
               "teto", "auto-dry")
# Os que viram linha `erro`, não `segurado`: a porta não chegou a decidir.
ERRORS = ("fetch", "push", "trava", "interno")
GATE_REASONS = ("escopo", "arvore-suja", "rebase", "coautoria", "sem-marca", "sem-veredito", "fora-do-pedido",
                "nao-publicavel", "muda-description", "nome-privado", "sem-anonimato", "revisao-desatualizada",
                "termo-nao-publico", "regra-repetida", "diff-alem-das-licoes", "testes", "validate-versions",
                "auditoria", "fase-de-auditoria", "teto", "auto-dry") + ERRORS
# Os motivos de nome: só o dono os resolve, ensinando o portão (O7). A aprovação com um deles libera a
# mudança das listas na guarda 5 (C2), nunca a recusa por nome.
NAME_REASONS = ("nome-privado", "termo-nao-publico")

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
DESCRIPTION_SUFFIX = "__description"
DETAIL_MAX = 1500


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
        self.retro = rw_auto.retro_dir(ctx, rid)
        self.retrofit = _retrofit(ctx, rid, lote)
        tentativa = self.retrofit["tentativa"]
        self.worktree = rw_store.worktree_path(ctx, rid, lote, tentativa)
        self.branch = rw_store.branch_name(rid, lote, tentativa)
        self.env = rw_store.git_env(home=ctx.home, nosystem=True)
        self.neutral = rw_store.git_env(neutral=True)
        path = self.folder / "aprovado.json"
        self.approval = None
        if path.exists():
            self.approval = list(rw_auto._fields(rw_auto._read_json(path), rw_auto.APROVADO_SPEC,
                                                 str(path))["motivos"])
        self.skipped = set(self.approval or ()) & set(OVERRIDABLE)

    def git(self, *args, what="porta"):
        return rw_store._git(list(args), self.worktree, self.env, what)

    def names(self, *extra):
        """Os caminhos que o ramo muda, sem renomeação (o nome velho e o novo aparecem os dois)."""
        out = rw_store._git(["-c", "core.quotePath=false", "diff", "--name-only", "-z", "--no-renames", *extra,
                             f"{rw_store.BASE_REF}...HEAD"], self.worktree, self.neutral, "porta")
        return [p for p in out.split("\0") if p]

    def diff(self, *paths):
        return rw_store._git(["diff", "-U0", "--no-color", "--no-ext-diff", "--no-textconv", "--src-prefix=a/",
                              "--dst-prefix=b/", f"{rw_store.BASE_REF}...HEAD", "--", *paths],
                             self.worktree, self.neutral, "porta")

    def pedido(self):
        return rw_auto.load_pedido(self.retro / "pedido.json")


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


def _g_clean(p):
    """2. A árvore do worktree está limpa."""
    out = p.git("status", "--porcelain", "--untracked-files=all")
    return ("arvore-suja", _short(out)) if out.strip() else None


def _g_fetch(p):
    """3. `git fetch origin`, sem nunca esperar credencial no terminal. Falha é `fetch`, nunca "em dia"."""
    env = dict(p.env, GIT_TERMINAL_PROMPT="0")
    rc, out = rw_store.run(["git", "-C", p.worktree, "fetch", "origin"], env=env)
    return ("fetch", _short(f"git fetch origin saiu {rc}: {out}")) if rc != 0 else None


def _g_rebase(p):
    """4. Rebase sobre o `origin/main` (D7). Com conflito, `git rebase --abort`: o ramo fica como estava."""
    rc, out = rw_store.run(["git", "-C", p.worktree, "rebase", rw_store.BASE_REF], env=p.env)
    if rc == 0:
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


def _veredito(p):
    return rw_auto.load_veredito(p.retro / "veredito.json")


def _g_verdict(p):
    """8. O veredito.json existe e é válido."""
    try:
        _veredito(p)
    except rw_auto.Malformed as exc:
        return "sem-veredito", _short(exc)
    return None


def _lessons(p):
    """As lições do retrofit.json, de licoes.json: [(n, lição ou None)]."""
    licoes = rw_auto.load_licoes(p.retro / "licoes.json")
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
    veredito = _veredito(p)
    wanted = "publicar" if p.tipo == "auto" else "ramo-pronto"
    for n, licao in _lessons(p):
        destino, motivo = rw_auto.classify(licao, veredito.get(str(n)))
        if destino != wanted:
            return "nao-publicavel", f"a licao {n} classifica como {destino} ({motivo})"
    return None


def _g_description(p):
    """10b. O lote `description` não sai sozinho (D12): fica o ramo pronto."""
    if p.tipo == "description":
        return "muda-description", f"ramo pronto: {p.branch}"
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


def _test_dirs(p):
    base = p.worktree / "plugins" / p.plugin
    dirs = [base / "tests"] + sorted(base.glob("skills/*/tests"))
    return [d for d in dirs if d.is_dir()]


def _g_tests(p):
    """17. Os testes do plugin e a suíte da raiz (D11), sem gravar bytecode no worktree (M7)."""
    env = dict(p.env, PYTHONDONTWRITEBYTECODE="1")
    dirs = _test_dirs(p)
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


def _g_dry(p):
    """21. O `auto-dry` faz tudo menos publicar: vem por último, para dizer se o resto passaria."""
    return ("auto-dry", "mode auto-dry: nada se publica") if p.ctx.mode == "auto-dry" else None


GUARDS = (
    ("escopo", _g_place),
    ("arvore-suja", _g_clean),
    ("fetch", _g_fetch),
    ("rebase", _g_rebase),
    ("escopo", _g_scope),
    ("coautoria", _g_coauthor),
    ("sem-marca", _g_marker),
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
    ("auto-dry", _g_dry),
)


def refuse(ctx, rid, lote, notes):
    """(motivo, detalhe) da primeira guarda que reprova, ou None quando o lote pode subir.

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
                return found
    except rw_store.StoreError as exc:
        return "interno", _short(exc)
    return None


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
    session = rw_auto.load_pedido(rw_auto.retro_dir(ctx, rid) / "pedido.json")["sessao"]
    resultado = "erro" if motivo in ERRORS else "segurado"
    return rw_auto._hold(ctx, session, rid, f"{rid}/{lote}", plugin, list(retrofit["licoes"]), resultado, motivo,
                         detalhe, lote, commit=_head(worktree) or retrofit["commit"], ramo=branch,
                         worktree=str(worktree))
