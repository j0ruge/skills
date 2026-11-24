"""retrofit-watch, modo autônomo: o pedido do Stop hook e o registro das retros autônomas.

O `cmd_stop` de retrofit_watch.py importa este módulo só com `mode` diferente de `manual` na config;
o `cmd_pending` (o aviso de startup) o importa sempre. Ele roda dentro do hook (10 s): nenhuma chamada
de rede, nenhum git, nenhum subagente.

Arquivos, todos em <dados> (o CLAUDE_PLUGIN_DATA), fora de qualquer repo:
  auto/<id>/pedido.json   o hook grava ao pedir a retro autônoma
  auto/<id>/licoes.json   o agente da sessão grava as lições da retro
  autonomo.jsonl          o registro: uma linha por lote ou por lição sem ramo
A trava do registro é o `_lock` de retrofit_watch.py, que serve no Unix e no Windows.
"""
import json
import os
import re
import sys
import tempfile
import time
from pathlib import Path

import retrofit_watch as rw

AUTO_DIR = "auto"
REGISTRY = "autonomo.jsonl"
REGISTRY_LOCK = "autonomo.lock"
AUTO_OPEN_TTL = 6 * 3600
# A regra contra a autoaprovação (decisão O9), igual no texto do hook e na referência do fluxo.
OWNER_WORD_RULE = "Nunca rode `approve`, `--publico-add` nem `--add` sem a palavra do dono nesta conversa."

SAFE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
HERE = Path(__file__).resolve().parent
REFERENCE = HERE.parent / "references" / "modo-autonomo.md"
CRITERIA = HERE.parent / "references" / "criteria.md"
SCRIPT = HERE / "retrofit_watch.py"

# Motivos de uma entrada ficar no modo manual, na ordem em que why_manual os confere.
REASONS = ("modo", "kit-ou-lean", "lista-manual", "permissao", "entrypoint", "sem-loja", "teto")
# Os motivos que a linha ao dono explica. Os outros não ganham acréscimo: são o modo manual de
# sempre (o `modo`, a lista `manual`, o kit ou a skill lean) ou uma sessão que não é a interativa.
REASON_TEXT = {
    "permissao": "o modo autônomo só vale com o modo de permissão bypassPermissions",
    "sem-loja": "falta na config a chave store com o clone de trabalho da loja",
    "teto": "o teto de retrofits autônomos da sessão (auto_limits) foi atingido",
}
# Os motivos de nome da porta (rw_gate): só o dono os resolve, ensinando o portão (O7). Moram aqui porque
# o `approve` também os lê (Final-F1).
NAME_REASONS = ("nome-privado", "termo-nao-publico")


class Malformed(Exception):
    """Nome de retro ou de lote fora do formato seguro, ou arquivo do fluxo fora do formato."""


def new_id(session_id, now=None):
    """`AAAAMMDD-HHMMSS-<8 caracteres seguros da sessão>`, com a hora em UTC."""
    now = time.time() if now is None else now
    safe = re.sub(r"[^A-Za-z0-9]", "", session_id or "")[:8] or "sessao"
    return time.strftime("%Y%m%d-%H%M%S", time.gmtime(now)) + "-" + safe


def _safe(name, what):
    # fullmatch, não match: o `$` do Python também casa antes de uma quebra de linha final.
    if not isinstance(name, str) or not SAFE_NAME.fullmatch(name):
        raise Malformed(f"{what} fora do formato seguro: {name!r}")
    return name


def retro_dir(ctx, rid):
    return ctx.data_dir / AUTO_DIR / _safe(rid, "id")


def lote_dir(ctx, rid, lote):
    return retro_dir(ctx, rid) / _safe(lote, "lote")


# --- registro ----------------------------------------------------------------------------------

def read_registry(ctx):
    """As linhas de autonomo.jsonl. Linha ilegível, ou que não é objeto, é pulada.

    Cada linha se decodifica sozinha: o registro só cresce, e uma linha com um caractere de vários
    bytes cortado no meio (gravação interrompida) derrubaria a leitura do arquivo inteiro."""
    try:
        lines = (ctx.data_dir / REGISTRY).read_bytes().split(b"\n")
    except OSError:
        return []
    out = []
    for line in lines:
        if not line.strip():
            continue
        try:
            item = json.loads(line.decode("utf-8"))
        except ValueError:  # inclui o UnicodeDecodeError
            continue
        if isinstance(item, dict):
            out.append(item)
    return out


def append_registry(ctx, line):
    """Acrescenta uma linha ao registro, com `ts`, sob a trava. Devolve a linha gravada."""
    ctx.data_dir.mkdir(parents=True, exist_ok=True)
    written = dict(line, ts=int(time.time()))
    lock = rw._lock(ctx.data_dir / REGISTRY_LOCK)
    try:
        with open(ctx.data_dir / REGISTRY, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(written, ensure_ascii=False) + "\n")
    finally:
        rw._unlock(lock)
    return written


def _is_batch(line):
    item = line.get("item")
    return isinstance(item, str) and bool(item) and "#" not in item


def used(registry, session, plugin=None, skip=None):
    """Retrofits autônomos da sessão: pares `(id, plugin)` distintos das linhas de lote (item sem
    `#`). Os dois lotes de um plugin numa retro (`<plugin>` e `<plugin>__description`) são um só.
    `plugin` conta só os daquele plugin; `skip` deixa de fora as linhas de um id."""
    pairs = set()
    for line in registry:
        if not isinstance(line, dict) or line.get("sessao") != session or not _is_batch(line):
            continue
        if plugin is not None and line.get("plugin") != plugin:
            continue
        if skip is not None and line.get("id") == skip:
            continue
        pairs.add((line.get("id"), line.get("plugin")))
    return len(pairs)


# --- decisão -----------------------------------------------------------------------------------

def why_manual(ctx, payload, entry, registry, entrypoint):
    """Por que a entrada fica no modo manual, ou None quando o modo autônomo vale para ela."""
    if ctx.mode == "manual":
        return "modo"
    if entry.get("mode") != "full":
        return "kit-ou-lean"
    manual = ctx.manual
    if entry.get("arg") in manual or any(s in manual for s in entry.get("skills") or []):
        return "lista-manual"
    if payload.get("permission_mode") != "bypassPermissions":
        return "permissao"
    # O ambiente não decide: a fase headless de um `sdd run` herda CLAUDE_CODE_ENTRYPOINT=cli da
    # sessão que a lançou, e o transcript dela diz `sdk-cli` (spec 5.10, medido em 2026-11-23).
    if entrypoint != "cli":
        return "entrypoint"
    if ctx.store is None:
        return "sem-loja"
    limits = ctx.auto_limits
    session = payload.get("session_id") or "unknown"
    if (used(registry, session, plugin=entry.get("arg")) >= limits["per_skill"]
            or used(registry, session) >= limits["per_session"]):
        return "teto"
    return None


def split(ctx, payload, entries, entrypoint):
    """Separa as entradas prontas: (autônomas, manuais, motivos por extenso das manuais).

    As autônomas do mesmo Stop entram no teto umas das outras: cada uma conta como um retrofit
    da sessão para a seguinte, senão quatro entradas prontas de uma vez passariam do teto de 3."""
    registry = read_registry(ctx)
    session = payload.get("session_id") or "unknown"
    planned, auto, manual, reasons = [], [], [], []
    for entry in entries:
        why = why_manual(ctx, payload, entry, registry + planned, entrypoint)
        if why is None:
            auto.append(entry)
            planned.append({"sessao": session, "id": None, "plugin": entry.get("arg"),
                            "item": f"pedido/{entry.get('arg')}"})
            continue
        manual.append(entry)
        text = REASON_TEXT.get(why)
        if text and text not in reasons:
            reasons.append(text)
    return auto, manual, reasons


# --- pedido ------------------------------------------------------------------------------------

def _write_json(path, data):
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".tmp-")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def open_request(ctx, payload, entries):
    """Grava <dados>/auto/<id>/pedido.json e o devolve. O id não repete: com a pasta já ocupada
    (dois pedidos no mesmo segundo), avança um segundo."""
    session = payload.get("session_id") or "unknown"
    now = time.time()
    (ctx.data_dir / AUTO_DIR).mkdir(parents=True, exist_ok=True)
    while True:
        rid = new_id(session, now)
        folder = retro_dir(ctx, rid)
        try:
            folder.mkdir()
            break
        except FileExistsError:
            now += 1
    pedido = {
        "id": rid,
        "sessao": session,
        "ts": int(time.time()),
        "transcript": payload.get("transcript_path"),
        "cwd": payload.get("cwd") or os.getcwd(),
        "modo": ctx.mode,
        "skills": [{"key": e["key"], "plugin": e["arg"], "label": e["label"], "skills": list(e.get("skills") or [])}
                   for e in entries],
    }
    _write_json(folder / "pedido.json", pedido)
    return pedido


def auto_text(ctx, pedido, entries):
    """O bloco do pedido autônomo para o Claude. Nomeia os caminhos absolutos que o fluxo usa."""
    labels = ", ".join(e["label"] for e in entries)
    label = entries[0]["label"] if len(entries) == 1 else "<skill>"
    skills = "; ".join(f"`{e['label']}` ({e['work']} chamadas, {e['friction']} sinais de atrito)" for e in entries)
    lessons = retro_dir(ctx, pedido["id"]) / "licoes.json"
    limit = ctx.auto_limits["per_session"]
    before = used(read_registry(ctx), pedido["sessao"], skip=pedido["id"])
    left = max(0, limit - before - len(pedido["skills"]))
    return (
        f"[modo autônomo: {labels}] retrofit-watch: nesta sessão trabalhou {skills}. A retro destas skills "
        f"é no modo autônomo (pedido {pedido['id']}, modo {pedido['modo']}): não pergunte nada ao dono "
        f"sobre elas. Leia antes `{REFERENCE}` e siga o fluxo dele. Faça a retro pelas seções 1 a 4 de "
        f"`{CRITERIA}`: só lições desta sessão, cada uma com a evidência e o padrão de falha. Se nenhuma "
        f"houver, responda só \"retro {label}: sem lições novas\" e não grave nada. Se houver, grave as "
        f"lições em `{lessons}`, no formato da referência, e rode os verbos do fluxo com "
        f"`\"{sys.executable}\" \"{SCRIPT}\"`. Não rode o /retrofit-skill nesta sessão e não cite valores "
        f"de segredo. {OWNER_WORD_RULE} Este pedido usa {len(pedido['skills'])} dos {limit} retrofits "
        f"autônomos da sessão; depois dele, restam {left}."
    )


def auto_message(pedido, entries):
    """A linha ao dono do pedido autônomo."""
    names = ", ".join(e["label"] for e in entries)
    return f"retrofit-watch: retro de {names} pedida ao Claude, modo autônomo ({pedido['id']})"


# --- fluxo aberto ------------------------------------------------------------------------------

def flow_open(st):
    """O pedido autônomo do estado está aberto? Aberto há AUTO_OPEN_TTL ou mais, ele sai do
    estado e o hook volta a contar (D13)."""
    current = st.get("auto_open")
    if not isinstance(current, dict):
        st.pop("auto_open", None)
        return False
    ts = current.get("ts")
    if isinstance(ts, (int, float)) and time.time() - ts < AUTO_OPEN_TTL:
        return True
    st.pop("auto_open", None)
    return False


def _lesson_numbers(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("licoes"), list):
        raise Malformed("licoes.json sem a lista `licoes`")
    numbers = set()
    for lesson in data["licoes"]:
        if not isinstance(lesson, dict) or "n" not in lesson:
            raise Malformed("lição sem `n`")
        numbers.add(lesson["n"])
    return numbers


def flow_finished(ctx, pedido, registry=None):
    """O fluxo acabou quando licoes.json falta (a retro respondeu "sem lições novas"), ou quando
    toda lição dele tem linha no registro com o id do pedido. licoes.json ilegível ou fora do
    formato deixa o fluxo aberto, até o TTL: devolve False, sem exceção. `registry` são as linhas já
    lidas: o `orphans` confere centenas de retros com uma leitura só do registro (T10-r1, I1)."""
    try:
        path = retro_dir(ctx, pedido["id"]) / "licoes.json"
        if not path.exists():
            return True
        numbers = _lesson_numbers(path)
    except (OSError, ValueError, KeyError, TypeError, Malformed):
        return False
    seen = set()
    for line in read_registry(ctx) if registry is None else registry:
        if line.get("id") == pedido["id"] and isinstance(line.get("licoes"), list):
            seen.update(n for n in line["licoes"] if isinstance(n, (int, str)))
    return numbers <= seen


# --- formatos ----------------------------------------------------------------------------------
# Um validador por campo. A chave a mais, a chave faltando e o valor fora do domínio são Malformed,
# com o arquivo e o campo na mensagem: o arquivo vem de um agente, e um campo errado lido como
# "vazio" publicaria a lição errada.

def _any(value):
    return True


def _int(value):
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _count(value):
    return _int(value) and value >= 1


def _text(value):
    return isinstance(value, str) and bool(value.strip())


def _opt_text(value):
    return value is None or _text(value)


def _opt_str(value):
    return value is None or isinstance(value, str)


def _flag(value):
    return isinstance(value, bool)


def _safe_text(value):
    return isinstance(value, str) and SAFE_NAME.fullmatch(value) is not None


def _one_of(*values):
    return lambda value: value in values


def _list(value):
    return isinstance(value, list)


def _text_list(value):
    return isinstance(value, list) and all(_text(v) for v in value)


def _opt_text_list(value):
    return value is None or _text_list(value)


def _counts(value):
    return isinstance(value, list) and bool(value) and all(_count(v) for v in value)


LOCATION = re.compile(r".+:[1-9][0-9]*")


def _opt_location(value):
    """`coberta`: null, ou `arquivo:linha`."""
    return value is None or (isinstance(value, str) and LOCATION.fullmatch(value) is not None)


PROCEDE = ("procede", "nao-procede", "nao-reproduzivel")
# Um dict como valor é o validador de um objeto aninhado; uma lista de objetos se confere no load_*.
PEDIDO_SPEC = {
    "id": _safe_text,
    "sessao": _text,
    "ts": _int,
    "transcript": _opt_text,
    "cwd": _text,
    "modo": _one_of("auto", "auto-dry"),
    "skills": _list,
}
PEDIDO_SKILL_SPEC = {
    "key": _text,
    "plugin": _safe_text,
    "label": _text,
    "skills": _text_list,
}
LICOES_SPEC = {
    "id": _safe_text,
    "licoes": _list,
}
EVIDENCIA_SPEC = {
    "texto": _text,
    "transcript": _text,
    "entrada": _text,
}
LICAO_SPEC = {
    "n": _count,
    "plugin": _safe_text,
    "skill": _safe_text,
    "tipo": _one_of("pitfall", "melhoria"),
    "evidencia": EVIDENCIA_SPEC,
    "padrao": _text,
    "resolveu": _opt_text,
    "muda_description": _flag,
}
VEREDITO_SPEC = {
    "id": _safe_text,
    "base": _text,
    "licoes": _list,
}
PARECER_SPEC = {
    "n": _count,
    "evidencia_confere": _flag,
    "coberta": _opt_location,
    "generica": _flag,
    "procede": _one_of(*PROCEDE),
    "basta_o_transcript": _opt_text,
    "nao_capturar": _opt_text,
    "nota": _opt_str,
}
# `fases`, `commit`, `versao` e `patch` ficam null do `prepare` ao `seal` (Tarefa 7).
RETROFIT_SPEC = {
    "id": _safe_text,
    "lote": _safe_text,
    "plugin": _safe_text,
    "tipo": _one_of("auto", "description"),
    "tentativa": _count,
    "worktree": _text,
    "ramo": _text,
    "base": _text,
    "licoes": _counts,
    "fases": _opt_text_list,
    "commit": _opt_text,
    "versao": _opt_text,
    "patch": _opt_text,
}
ANONIMATO_SPEC = {
    "patch": _text,
    "termos": _list,
    "regra_repetida": _opt_text,
    "fora_das_licoes": _opt_text,
}
TERMO_SPEC = {
    "termo": _text,
    "veredito": _one_of("publico", "privado", "duvida"),
    "nota": _opt_str,
}
APROVADO_SPEC = {
    "id": _safe_text,
    "lote": _safe_text,
    "ts": _int,
    "motivos": _text_list,
}

LICAO_KEYS = frozenset(LICAO_SPEC)
EVIDENCIA_KEYS = frozenset(EVIDENCIA_SPEC)
PARECER_KEYS = frozenset(PARECER_SPEC)
TERMO_KEYS = frozenset(TERMO_SPEC)
ANONIMATO_KEYS = frozenset(ANONIMATO_SPEC)
RETROFIT_KEYS = frozenset(RETROFIT_SPEC)

# Os motivos da triagem: os que descartam e os que seguram (seção Formatos e motivos do plano).
DISCARD_REASONS = ("coberta", "do-projeto", "nao-procede", "sem-evidencia", "nao-capturar")
HOLD_REASONS = ("sem-veredito", "fora-do-pedido", "nao-reproduzivel", "sem-correcao")
LESSON_REASONS = DISCARD_REASONS + HOLD_REASONS
OWNER_REASONS = ("descartado-pelo-dono", "resolvido-manual")
AGENT_REASONS = ("executor-falhou", "executor-recusou")


def _fields(obj, spec, where):
    if not isinstance(obj, dict):
        raise Malformed(f"{where}: não é um objeto")
    for key in obj:
        if key not in spec:
            raise Malformed(f"{where}: chave a mais `{key}`")
    for key in spec:
        if key not in obj:
            raise Malformed(f"{where}: falta a chave `{key}`")
    for key, check in spec.items():
        if isinstance(check, dict):
            _fields(obj[key], check, f"{where}, `{key}`")
        elif not check(obj[key]):
            raise Malformed(f"{where}: `{key}` fora do domínio: {obj[key]!r}")
    return obj


def _items(obj, key, spec, where):
    """Confere cada objeto da lista `obj[key]` contra `spec`."""
    for i, item in enumerate(obj[key]):
        _fields(item, spec, f"{where}, `{key}`[{i}]")
    return obj[key]


def _read_json(path):
    """O JSON de `path`, em UTF-8 sem BOM. Ilegível, com BOM, com cerca de código ou fora do UTF-8
    é Malformed, nunca um traceback."""
    path = Path(path)
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise Malformed(f"{path}: ilegível ({exc.strerror or exc})") from None
    try:
        return json.loads(raw.decode("utf-8"))
    except ValueError as exc:  # inclui o UnicodeDecodeError e o BOM
        raise Malformed(f"{path}: não é JSON em UTF-8 sem BOM ({exc})") from None


def _by_number(entries, where):
    out = {}
    for entry in entries:
        key = str(entry["n"])
        if key in out:
            raise Malformed(f"{where}: `n` repetido: {entry['n']}")
        out[key] = entry
    return out


def load_pedido(path):
    data = _fields(_read_json(path), PEDIDO_SPEC, str(path))
    _items(data, "skills", PEDIDO_SKILL_SPEC, str(path))
    return data


def load_licoes(path):
    """As lições de licoes.json, por número (`"1"`, `"2"`...), na ordem do arquivo."""
    data = _fields(_read_json(path), LICOES_SPEC, str(path))
    return _by_number(_items(data, "licoes", LICAO_SPEC, str(path)), str(path))


def load_veredito(path):
    """Os pareceres de veredito.json, por número da lição."""
    data = _fields(_read_json(path), VEREDITO_SPEC, str(path))
    return _by_number(_items(data, "licoes", PARECER_SPEC, str(path)), str(path))


def load_retrofit(path):
    return _fields(_read_json(path), RETROFIT_SPEC, str(path))


def load_anonimato(path):
    data = _fields(_read_json(path), ANONIMATO_SPEC, str(path))
    _items(data, "termos", TERMO_SPEC, str(path))
    return data


def load_aprovado(path):
    return _fields(_read_json(path), APROVADO_SPEC, str(path))


# --- triagem -----------------------------------------------------------------------------------

def in_request(ctx, pedido, licao):
    """A lição cabe no pedido? O plugin tem de estar nele, e a skill na lista da entrada quando a
    entrada lista skills (spec 5.2). Plugin ou skill no `exclude` ou na lista `manual` da config
    de agora ficam fora, mesmo que a config tenha mudado depois do pedido."""
    plugin, skill = licao["plugin"], licao["skill"]
    entries = [e for e in pedido["skills"] if e["plugin"] == plugin]
    if not entries:
        return False
    excluded, manual = ctx.excluded, ctx.manual
    if plugin in excluded or skill in excluded or plugin in manual or skill in manual:
        return False
    listed = [s for e in entries for s in e["skills"]]
    return not listed or skill in listed


def classify(licao, parecer):
    """O destino da lição e o motivo: `publicar`, `ramo-pronto`, `segurar` ou `descartar`. Vale a
    primeira condição que casar; o descarte vem antes do que seguraria (decisão O3)."""
    if parecer is None:
        return "segurar", "sem-veredito"
    if parecer["coberta"] is not None:
        return "descartar", "coberta"
    if not parecer["generica"]:
        return "descartar", "do-projeto"
    if parecer["procede"] == "nao-procede":
        return "descartar", "nao-procede"
    if not parecer["evidencia_confere"]:
        return "descartar", "sem-evidencia"
    if parecer["nao_capturar"] is not None:
        return "descartar", "nao-capturar"
    if parecer["procede"] == "nao-reproduzivel" and parecer["basta_o_transcript"] is None:
        return "segurar", "nao-reproduzivel"
    if licao["resolveu"] is None:
        return "segurar", "sem-correcao"
    if licao["muda_description"]:
        return "ramo-pronto", "muda-description"
    return "publicar", None


def _detail(motivo, parecer):
    """O texto do parecer que explica o motivo: o `arquivo:linha` da coberta, o item da lista do
    que não capturar; senão a nota do revisor."""
    if parecer is None:
        return ""
    if motivo == "coberta":
        return parecer["coberta"]
    if motivo == "nao-capturar":
        return parecer["nao_capturar"]
    return parecer["nota"] or ""


def _line(session, rid, item, plugin, licoes, resultado, motivo, detalhe="", lote=None):
    """Uma linha do registro sem o `ts`, com todas as chaves; as da porta ficam null."""
    return {"sessao": session, "id": rid, "lote": lote, "plugin": plugin, "item": item, "licoes": licoes,
            "resultado": resultado, "motivo": motivo, "detalhe": detalhe, "commit": None, "ramo": None,
            "worktree": None, "versao": None, "aprovado": None, "instalacao": None}


def _plan(ctx, rid):
    """A triagem sem gravar nada: (pedido, lotes, segurar, descartar)."""
    folder = retro_dir(ctx, rid)
    pedido = load_pedido(folder / "pedido.json")
    licoes = load_licoes(folder / "licoes.json")
    veredito = load_veredito(folder / "veredito.json")
    lotes, hold, drop = {}, [], []
    for key, licao in licoes.items():
        plugin, n = licao["plugin"], licao["n"]
        if not in_request(ctx, pedido, licao):
            destino, motivo, parecer = "segurar", "fora-do-pedido", None
        else:
            parecer = veredito.get(key)
            destino, motivo = classify(licao, parecer)
        if destino in ("publicar", "ramo-pronto"):
            tipo = "auto" if destino == "publicar" else "description"
            name = plugin if tipo == "auto" else f"{plugin}__description"
            lotes.setdefault(name, {"lote": name, "plugin": plugin, "tipo": tipo, "licoes": []})["licoes"].append(n)
            continue
        entry = {"item": f"{rid}/{plugin}#{n}", "plugin": plugin, "licoes": [n], "motivo": motivo,
                 "detalhe": _detail(motivo, parecer)}
        (hold if destino == "segurar" else drop).append(entry)
    ordered = sorted(lotes.values(), key=lambda lote: (lote["tipo"] != "auto", lote["plugin"]))
    return pedido, ordered, hold, drop


def _append_new(ctx, lines):
    """Acrescenta, sob uma trava só, as linhas cujo `item` ainda não tem linha no registro."""
    ctx.data_dir.mkdir(parents=True, exist_ok=True)
    lock = rw._lock(ctx.data_dir / REGISTRY_LOCK)
    try:
        seen = {entry.get("item") for entry in read_registry(ctx)}
        now = int(time.time())
        with open(ctx.data_dir / REGISTRY, "a", encoding="utf-8") as fh:
            for entry in lines:
                if entry["item"] not in seen:
                    fh.write(json.dumps(dict(entry, ts=now), ensure_ascii=False) + "\n")
    finally:
        rw._unlock(lock)


def triage(ctx, rid):
    """Os lotes da retro (os `auto` antes dos `description`) e as lições sem ramo. Grava uma linha
    `segurado` ou `descartado` por lição sem ramo; rodar de novo não repete linha."""
    pedido, lotes, hold, drop = _plan(ctx, rid)
    lines = [_line(pedido["sessao"], rid, e["item"], e["plugin"], e["licoes"], result, e["motivo"], e["detalhe"])
             for result, entries in (("segurado", hold), ("descartado", drop)) for e in entries]
    _append_new(ctx, lines)
    return {"lotes": lotes, "segurar": hold, "descartar": drop}


# --- verbos do registro ------------------------------------------------------------------------

def last_lines(registry):
    """A última linha de cada `item`."""
    out = {}
    for entry in registry:
        item = entry.get("item")
        if isinstance(item, str):
            out[item] = entry
    return out


def held(ctx):
    """Os itens em aberto: a última linha é `segurado` ou `erro`."""
    return [entry for entry in last_lines(read_registry(ctx)).values()
            if entry.get("resultado") in ("segurado", "erro")]


# --- o aviso de startup ------------------------------------------------------------------------
# Os segmentos que o `cmd_pending` de retrofit_watch.py junta numa linha só ao dono. Cada um devolve o
# texto, ou None quando não há o que dizer; o `cmd_pending` roda cada um no seu `try` (M11).

ORPHAN_AGE = 3600
# A última linha `publicado` de um lote com a cópia instalada ainda atrás do commit (D22, C10).
BEHIND = ("pendente", "update", "cache-difere")


def _started(folder):
    """O instante do pedido da retro: o `ts` do pedido.json; ilegível, a hora da pasta."""
    try:
        return load_pedido(folder / "pedido.json")["ts"]
    except Malformed:
        return folder.stat().st_mtime


def _ramo(path):
    try:
        return load_retrofit(path)["ramo"]
    except Malformed:
        return None


def orphans(ctx, now=None):
    """Os fluxos autônomos sem registro de fim, com o pedido de ORPHAN_AGE s ou mais (D14). Um lote com
    retrofit.json e sem linha própria (`item == <id>/<lote>`; a linha de uma lição que leva o `lote` não
    conta), ou, numa retro sem lote órfão, licoes.json com lição sem linha (o `flow_finished`, que conta
    o licoes.json ilegível como aberto). Cada item: {tipo, id, lote, ramo}."""
    now = time.time() if now is None else now
    try:
        folders = sorted(p for p in (ctx.data_dir / AUTO_DIR).iterdir() if p.is_dir() and SAFE_NAME.fullmatch(p.name))
    except OSError:
        return []
    # Uma leitura só do registro, agrupada por id: o startup tem 10 s, e nada é apagado, então toda
    # retro fechada continua aqui com o seu licoes.json (T10-r1, I1).
    registry = read_registry(ctx)
    last = last_lines(registry)
    by_id = {}
    for line in registry:
        by_id.setdefault(line.get("id"), []).append(line)
    out = []
    for folder in folders:
        rid = folder.name
        if now - _started(folder) < ORPHAN_AGE:
            continue
        lotes = [{"tipo": "lote", "id": rid, "lote": sub.name, "ramo": _ramo(sub / "retrofit.json")}
                 for sub in sorted(folder.iterdir())
                 if sub.is_dir() and SAFE_NAME.fullmatch(sub.name) and (sub / "retrofit.json").exists()
                 and f"{rid}/{sub.name}" not in last]
        if lotes:
            out += lotes
        elif (folder / "licoes.json").exists() and not flow_finished(ctx, {"id": rid}, by_id.get(rid, [])):
            out.append({"tipo": "licoes", "id": rid, "lote": None, "ramo": None})
    return out


def install_behind(ctx):
    """Os itens cuja última linha é `publicado` com `instalacao` em BEHIND. A linha de uma lição trazida
    de volta (T9) não tem `instalacao` e fica fora."""
    return [entry for entry in last_lines(read_registry(ctx)).values()
            if entry.get("resultado") == "publicado" and entry.get("instalacao") in BEHIND]


def _amount(n, one, many):
    return f"{n} {one if n == 1 else many}"


def _held_branch(ctx, line):
    """O ramo de um item segurado: o da linha; sem ele, num lote (a linha do `hold_item` por
    `executor-falhou` sai sem ramo), o do retrofit.json do lote, se o `prepare` já o criou (T10-r1, I2)."""
    if line.get("ramo"):
        return line["ramo"]
    if not _is_batch(line):
        return None
    try:
        return _ramo(lote_dir(ctx, line.get("id"), line["item"].partition("/")[2]) / "retrofit.json")
    except Malformed:
        return None


def held_notice(ctx):
    items = held(ctx)
    if not items:
        return None
    names = ", ".join(f"{e.get('plugin')}: {_held_branch(ctx, e) or e.get('item')}" for e in items)
    return (f"{_amount(len(items), 'retrofit segurado', 'retrofits segurados')} ({names}) — "
            "/retrofit-watch:retrofit-watch segurados")


def orphan_notice(ctx):
    items = orphans(ctx)
    if not items:
        return None
    names = ", ".join(o["ramo"] or o["id"] for o in items)
    return (f"{_amount(len(items), 'retrofit autônomo', 'retrofits autônomos')} sem registro de fim "
            f"({names})")


def behind_notice(ctx):
    items = install_behind(ctx)
    if not items:
        return None
    names = ", ".join(str(e.get("plugin")) for e in items)
    return f"{_amount(len(items), 'publicado', 'publicados')} com a cópia instalada atrás ({names})"


# O que vem depois de `<id>/` num item: `<lote>`, ou `<plugin>#<n>` na lição sem ramo.
ITEM_REST = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*(#[1-9][0-9]*)?")


def _item(rid, item):
    """Confere `item` contra o id: `<id>/<lote>` ou `<id>/<plugin>#<n>`."""
    _safe(rid, "id")
    prefix, _, rest = item.partition("/") if isinstance(item, str) else ("", "", "")
    if prefix != rid or ITEM_REST.fullmatch(rest) is None:
        raise Malformed(f"item fora do formato `{rid}/<lote>` ou `{rid}/<plugin>#<n>`: {item!r}")
    return item


def hold_item(ctx, rid, item, motivo, detalhe=""):
    """Linha `segurado` para um lote da triagem que o executor não levou até o fim, ou para uma
    lição de um lote (`<id>/<plugin>#<n>`) que o executor deixou fora do selo (rw_store.seal)."""
    _item(rid, item)
    if motivo not in AGENT_REASONS:
        raise Malformed(f"motivo fora de {', '.join(AGENT_REASONS)}: {motivo!r}")
    pedido, lotes, _, _ = _plan(ctx, rid)
    plugin, _, n = item.partition("/")[2].partition("#")
    if n:
        lote = next((x for x in lotes if x["plugin"] == plugin and int(n) in x["licoes"]), None)
        licoes = [int(n)]
    else:
        lote = next((x for x in lotes if f"{rid}/{x['lote']}" == item), None)
        licoes = lote["licoes"] if lote else None
    if lote is None:
        raise Malformed(f"{item} não é um lote, nem uma lição de um lote, da triagem da retro {rid}")
    return _hold(ctx, pedido["sessao"], rid, item, lote["plugin"], licoes, "segurado", motivo, detalhe, lote["lote"])


def _hold(ctx, session, rid, item, plugin, licoes, resultado, motivo, detalhe, lote, commit=None, ramo=None,
          worktree=None):
    """Grava e devolve a linha `segurado` (ou `erro`) de um item. Comum ao hold_item e ao hold da
    porta (rw_gate.hold), que preenche `commit`, `ramo` e `worktree`."""
    line = _line(session, rid, item, plugin, licoes, resultado, motivo, detalhe, lote=lote)
    line.update(commit=commit, ramo=ramo, worktree=worktree)
    return append_registry(ctx, line)


def approve(ctx, rid, lote):
    """Acrescenta a aprovado.json o motivo da última linha `segurado` do lote e, quando há uma, o da última
    recusa por nome (NAME_REASONS), sem repetir. Um `publish` entre a palavra do dono e o `approve` segura
    o lote com `escopo`: sem o motivo de nome, a guarda 5 nunca aceitaria a mudança das listas (Final-F1).
    O `detalhe` dessa recusa a porta lê da mesma linha do registro."""
    folder = lote_dir(ctx, rid, lote)
    item = f"{rid}/{lote}"
    reasons = [e.get("motivo") for e in read_registry(ctx) if e.get("item") == item and e.get("resultado") == "segurado"]
    if not reasons:
        raise Malformed(f"o lote {item} não tem linha `segurado` no registro")
    path = folder / "aprovado.json"
    motivos = []
    if path.exists():
        motivos = list(load_aprovado(path)["motivos"])
    names = [r for r in reasons if r in NAME_REASONS]
    for reason in [reasons[-1]] + names[-1:]:
        if reason not in motivos:
            motivos.append(reason)
    folder.mkdir(parents=True, exist_ok=True)
    _write_json(path, {"id": rid, "lote": lote, "ts": int(time.time()), "motivos": motivos})
    return path


def discard(ctx, rid, item, motivo="descartado-pelo-dono"):
    """Linha `descartado` para um item em aberto, pela palavra do dono."""
    _item(rid, item)
    if motivo not in OWNER_REASONS:
        raise Malformed(f"motivo fora de {', '.join(OWNER_REASONS)}: {motivo!r}")
    last = next((e for e in held(ctx) if e.get("item") == item), None)
    if last is None:
        raise Malformed(f"o item {item} não está em aberto (segurado ou erro) no registro")
    return append_registry(ctx, _line(last.get("sessao"), rid, item, last.get("plugin"), last.get("licoes"),
                                      "descartado", motivo, lote=last.get("lote")))
