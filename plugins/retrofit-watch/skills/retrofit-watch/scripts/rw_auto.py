"""retrofit-watch, modo autônomo: o pedido do Stop hook e o registro das retros autônomas.

Só o `cmd_stop` de retrofit_watch.py importa este módulo, e só com `mode` diferente de `manual`
na config. Ele roda dentro do hook (10 s): nenhuma chamada de rede, nenhum git, nenhum subagente.

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


class Malformed(Exception):
    """Nome de retro ou de lote fora do formato seguro, ou arquivo do fluxo fora do formato."""


def new_id(session_id, now=None):
    """`AAAAMMDD-HHMMSS-<8 caracteres seguros da sessão>`, com a hora em UTC."""
    now = time.time() if now is None else now
    safe = re.sub(r"[^A-Za-z0-9]", "", session_id or "")[:8] or "sessao"
    return time.strftime("%Y%m%d-%H%M%S", time.gmtime(now)) + "-" + safe


def _safe(name, what):
    if not isinstance(name, str) or not SAFE_NAME.match(name):
        raise Malformed(f"{what} fora do formato seguro: {name!r}")
    return name


def retro_dir(ctx, rid):
    return ctx.data_dir / AUTO_DIR / _safe(rid, "id")


def lote_dir(ctx, rid, lote):
    return retro_dir(ctx, rid) / _safe(lote, "lote")


# --- registro ----------------------------------------------------------------------------------

def read_registry(ctx):
    """As linhas de autonomo.jsonl. Linha ilegível, ou que não é objeto, é pulada."""
    try:
        lines = (ctx.data_dir / REGISTRY).read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    out = []
    for line in lines:
        try:
            item = json.loads(line)
        except ValueError:
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


def flow_finished(ctx, pedido):
    """O fluxo acabou quando licoes.json falta (a retro respondeu "sem lições novas"), ou quando
    toda lição dele tem linha no registro com o id do pedido. licoes.json ilegível ou fora do
    formato deixa o fluxo aberto, até o TTL: devolve False, sem exceção."""
    try:
        path = retro_dir(ctx, pedido["id"]) / "licoes.json"
        if not path.exists():
            return True
        numbers = _lesson_numbers(path)
    except (OSError, ValueError, KeyError, TypeError, Malformed):
        return False
    seen = set()
    for line in read_registry(ctx):
        if line.get("id") == pedido["id"] and isinstance(line.get("licoes"), list):
            seen.update(n for n in line["licoes"] if isinstance(n, (int, str)))
    return numbers <= seen
