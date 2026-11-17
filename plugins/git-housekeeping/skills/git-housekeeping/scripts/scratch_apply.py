#!/usr/bin/env python3
"""Move para a quarentena só o que o plano do scratch_scan.py deixa sair, provando cada item de novo.

`scratch_apply.py --plan <arquivo> [--only <nome>]... [--dry-run]` move os itens `delete` (e, com
`--only`, os `review` nomeados, depois da leitura) para `<raiz>/.housekeeping-lixeira/<data>/itens/`,
com um `desfazer:` por item. Antes de mover, reconfere: o caminho dentro da raiz sem link no meio, o
tipo, o conteúdo (arquivos, bytes, mtime), o processo dentro, a citação nova e, no clone, a limpeza.
`scratch_apply.py --purge --root <raiz> --older-than <dias> [--dry-run]` apaga os lotes da quarentena
mais velhos que isso: é o único passo sem volta.
rc 0 tudo feito; 1 algum item recusado; 2 plano ou uso inválido (`--only` fora do que pode sair).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import housekeeping as hk  # noqa: E402
import scratch  # noqa: E402
from scratch_scan import mb  # noqa: E402

LOTE = re.compile(r"^(\d{8}-\d{6})(?:-\d+)?$")


def _recusa(plan: dict, raw: dict, procs, citadas: dict) -> str:
    """O motivo de não mover o item agora, ou "" se a prova do plano ainda vale."""
    root = plan["root"]
    path = os.path.join(root, raw["name"])
    if not os.path.lexists(path):
        return "não existe mais"
    if os.path.islink(path) or os.path.realpath(path) != os.path.normpath(path):
        return "o caminho virou link (ou passa por um)"
    if os.path.isdir(path) != (raw["type"] == "dir"):
        return f"o tipo mudou: no plano {raw['type']}, agora {'dir' if os.path.isdir(path) else 'file'}"
    files, _kb, size, newest = scratch.conta(path)
    if (files, size, newest) != (raw["files"], raw["size"], raw["newest"]):
        return (f"mudou desde o plano (arquivos {raw['files']}→{files}, bytes {raw['size']}→{size}"
                f"{', mtime mais novo' if newest != raw['newest'] else ''}); rode o scan de novo")
    who = scratch.processo_dentro(path, procs)
    if who:
        return f"processo com o diretório aqui dentro: {who}"
    if raw["proof"] == "clone":
        ok, why = scratch.clone_limpo(path)
        if not ok:
            return f"o clone deixou de estar limpo: {why}"
    if raw["proof"] == "regen" and not scratch.regen_solto(path):
        return "deixou de ser regenerável"
    if raw["proof"] == "igual":
        dest = plan["igual"].get(os.path.realpath(path))
        if not dest or scratch.compara(path, dest)[1]:
            return "deixou de ter cópia igual no destino"
    return citadas.get(raw["name"], "")


def _citadas(plan: dict, items: list, repos: list) -> dict:
    """{entrada que vai sair: por que fica agora}: citada nas mesmas fontes do scan ou no texto das
    entradas que ficam, ou o handoff que é a única descrição de uma pasta que fica."""
    root = plan["root"]
    names = [i["name"] for i in items if i["kind"] == "entry"]
    if not names:
        return {}
    todas = [n for n in scratch.listar(root) if n != scratch.LIXEIRA]
    staying = [n for n in todas if n not in names]
    handoffs = [i["name"] for i in items if i["kind"] == "entry" and i["proof"] == "handoff"]
    descritas = {x: onde for x, onde in scratch.Busca(root, todas).entradas(handoffs).items() if x in staying}
    busca = scratch.Busca(root, names + list(descritas))
    hits = busca.fontes(repos, plan["cites"])
    for n, onde in busca.entradas(staying).items():
        hits.setdefault(n, []).extend(onde)
    out = {n: f"citada agora em {', '.join(hits[n][:2])}" for n in names if hits.get(n)}
    for x, onde in descritas.items():
        if not hits.get(x):
            for h in {w.split(os.sep)[0] for w in onde}:
                out.setdefault(h, f"é a única descrição de {x}, que fica")
    return out


def _lote(root: str) -> Path:
    base = Path(root) / scratch.LIXEIRA
    stamp = time.strftime("%Y%m%d-%H%M%S")
    lote, k = base / stamp, 2
    while lote.exists():
        lote, k = base / f"{stamp}-{k}", k + 1
    return lote


def _valida(plan: dict) -> str:
    if plan.get("version") != scratch.PLAN_VERSION or plan.get("tool") != "scratch":
        return f"plano versão {plan.get('version')!r} de {plan.get('tool')!r}; este script lê o do scratch_scan.py"
    fields = set(scratch.Item.__dataclass_fields__)
    for raw in plan.get("items", []):
        if set(raw) != fields:
            return "o plano tem item com campos que o scratch_scan.py não gera"
        parts = Path(raw["name"]).parts
        if os.path.isabs(raw["name"]) or ".." in parts or not parts or raw["kind"] not in ("entry", "sub"):
            return f"item inválido no plano: {raw['name']!r}"
    if not os.path.isdir(plan.get("root", "")):
        return f"a raiz do plano não existe: {plan.get('root')!r}"
    return ""


def apply(args) -> int:
    """Seleciona, reconfere e move; imprime o que fez e os `desfazer:`."""
    try:
        plan = json.loads(Path(args.plan).read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        print(f"erro: plano ilegível: {e}", file=sys.stderr)
        return 2
    err = _valida(plan)
    if err:
        print(f"erro: {err}", file=sys.stderr)
        return 2
    only = [n.rstrip("/") for n in args.only]
    podem = {raw["name"]: raw for raw in plan["items"] if raw["decision"] in scratch.SAEM}
    fora = [n for n in only if n not in podem]
    if fora:
        print(f"erro: --only fora do que pode sair: {', '.join(map(repr, fora))}; o plano aceita: "
              f"{', '.join(sorted(podem)) or 'nenhum'}", file=sys.stderr)
        return 2
    chosen = ([podem[n] for n in only] if only
              else [raw for raw in plan["items"] if raw["decision"] == "delete"])
    try:
        repos = [scratch.load_repo(r["path"]) for r in plan["repos"]]
    except scratch.ScratchError as e:
        print(f"erro: {e}", file=sys.stderr)
        return 2
    procs = hk.proc_cwds()
    citadas = _citadas(plan, chosen, repos)
    lote, lines, undo, failed, moved_kb = _lote(plan["root"]), [], [], False, 0
    feitos = []
    for raw in chosen:
        why = _recusa(plan, raw, procs, citadas)
        if why:
            failed = True
            lines.append(f"recusado: {raw['name']}: {why}")
            continue
        src, dest = Path(plan["root"]) / raw["name"], lote / "itens" / raw["name"]
        if args.dry_run:
            lines.append(f"faria: {raw['name']} → {dest}")
            continue
        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            os.rename(src, dest)
        except OSError as e:
            failed = True
            lines.append(f"recusado: {raw['name']}: o mv falhou ({e})")
            continue
        moved_kb += raw["kb"]
        feitos.append({"name": raw["name"], "origem": str(src), "destino": str(dest), "motivo": raw["reason"]})
        lines.append(f"movido: {raw['name']} → {dest}")
        undo.append(f"mv -n -T {shlex.quote(str(dest))} {shlex.quote(str(src))}")
    if feitos:
        (lote / "lote.json").write_text(json.dumps({"plano": str(Path(args.plan).resolve()), "itens": feitos},
                                                   ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("\n".join(lines) or "nada a mover")
    if not only:
        review = sum(1 for raw in plan["items"] if raw["decision"] == "review")
        if review:
            print(f"esperando a leitura: {review} handoff(s); depois de ler, passe cada um com --only")
    if feitos:
        print(f"na quarentena: {mb(moved_kb)} em {lote}; o disco só libera com "
              f"--purge --root {shlex.quote(plan['root'])} --older-than <dias>")
    for line in reversed(undo):
        print(f"desfazer: {line}")
    return 1 if failed else 0


def purge(args) -> int:
    """Apaga os lotes da quarentena mais velhos que `--older-than` dias (pelo nome do lote)."""
    root = os.path.realpath(os.path.expanduser(args.root))
    lix = os.path.join(root, scratch.LIXEIRA)
    if os.path.islink(lix):
        print(f"erro: {lix} é um link; a quarentena tem de ser uma pasta da raiz", file=sys.stderr)
        return 2
    if not os.path.isdir(lix):
        print("nada na quarentena")
        return 0
    now = time.time()
    for name in sorted(os.listdir(lix)):
        path = os.path.join(lix, name)
        m = LOTE.match(name)
        if not m or os.path.islink(path) or not os.path.isdir(path):
            print(f"fica: {name} (não é um lote desta skill)")
            continue
        idade = (now - time.mktime(time.strptime(m.group(1), "%Y%m%d-%H%M%S"))) / 86400
        files, kb, _size, _newest = scratch.conta(path)
        desc = f"lote {name} ({idade:.0f} dia(s), {files} arquivo(s), {mb(kb)})"
        if idade < args.older_than:
            print(f"fica: {desc}")
        elif args.dry_run:
            print(f"faria: apagar {desc}")
        else:
            shutil.rmtree(path)
            print(f"apagado: {desc}")
    if not args.dry_run and not os.listdir(lix):
        os.rmdir(lix)
    return 0


def main(argv=None) -> int:
    """Lê os argumentos e roda o apply ou o purge."""
    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    ap.add_argument("--plan")
    ap.add_argument("--only", action="append", default=[], metavar="NOME",
                    help="move só este item do plano (repetível), pelo nome do relatório")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--purge", action="store_true", help="apaga os lotes velhos da quarentena")
    ap.add_argument("--root", help="a raiz, com --purge")
    ap.add_argument("--older-than", type=float, help="idade mínima do lote, em dias, com --purge")
    args = ap.parse_args(argv)
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(errors="replace")
    if args.purge:
        if not args.root or args.older_than is None or args.plan or args.only:
            ap.error("--purge pede --root e --older-than, sem --plan nem --only")
        return purge(args)
    if not args.plan:
        ap.error("--plan é obrigatório (ou --purge)")
    return apply(args)


if __name__ == "__main__":
    sys.exit(main())
