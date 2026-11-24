#!/usr/bin/env python3
"""Analisa uma pasta de rascunho (~/.wt) e diz o que sairia dela, sem mover nada.

`scratch_scan.py --root ~/.wt --repo <repo>... --plan <fora da raiz>/plano.json` classifica cada
entrada da raiz em SAI, SAI SE A LEITURA CONFIRMAR (handoff), NÃO PROVADO e FICA, grava o plano e
imprime o relatório. As citações vêm dos --repo (o origin/HEAD e a cópia de trabalho), do CLAUDE.md,
dos planos e das memórias do Claude Code em ~/.claude, dos --cite e do texto das entradas que ficam.
rc 0 ok; 2 uso inválido (raiz, plano dentro da raiz, --repo que não é repo, --igual).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import housekeeping as hk  # noqa: E402
import scratch  # noqa: E402

GROUPS = (("delete", "SAI"), ("review", "SAI SE A LEITURA CONFIRMAR"),
          ("unproven", "NÃO PROVADO (fica)"), ("keep", "FICA"))


def mb(kb: int) -> str:
    """KiB em MB com uma casa; abaixo de 1 MB, em KB."""
    return f"{kb / 1024:.1f} MB" if kb >= 1024 else f"{kb} KB"


def _tipo(i: dict) -> str:
    return "sub" if i["kind"] == "sub" else ("pasta" if i["type"] == "dir" else "arquivo")


def _fontes(cites: list) -> str:
    """As citações extras numa linha: as pastas de memória do Claude Code viram uma contagem."""
    home = str(Path.home())
    mem = [c for c in cites if Path(c).name == "memory" and Path(c).parent.parent.name == "projects"]
    out = [c.replace(home, "~", 1) for c in cites if c not in mem]
    if mem:
        out.append(f"{len(mem)} pasta(s) de memória (~/.claude/projects/*/memory)")
    return ", ".join(out) or "nenhuma fonte extra"


def render(plan: dict) -> str:
    """O relatório: cabeçalho, os quatro grupos com o motivo de cada item, e o disco."""
    repos = ", ".join(f"{os.path.basename(r['path'])} ({r['ref']})" for r in plan["repos"]) or "nenhum"
    lines = [f"pastas de rascunho: {plan['root']} (recente: até {plan['recent_days']} dia(s); "
             f"repos: {repos}; prova por PR: {plan['gh']})"]
    for path, refs in sorted(plan.get("sem_fetch", {}).items()):
        lines.append(f"aviso: {os.path.basename(path)}: o remoto andou depois do último fetch "
                     f"({', '.join(refs)}), e essas refs não provam cópia; rode git -C {path} fetch "
                     "e o scan de novo")
    if not plan["procs_checked"]:
        lines.append("processos nas pastas: não conferido (sem /proc)")
    lines.append(f"citações lidas também em: {_fontes(plan['cites'])}")
    lines.append("")
    for decision, title in GROUPS:
        group = [i for i in plan["items"] if i["decision"] == decision]
        lines.append(f"{title} ({len(group)}, {mb(sum(i['kb'] for i in group))})")
        for i in group:
            lines.append(f"  {_tipo(i):<7} {i['name']}  ({i['files']} arquivo(s), {mb(i['kb'])})  "
                         f"{i['reason']}")
            ev = i["evidence"]
            if decision == "review" and ev:
                mais = f" e mais {len(ev) - 12}" if len(ev) > 12 else ""
                lines.append(f"          evidência: {', '.join(ev[:12])}{mais}")
        lines.append("")
    out = sum(i["kb"] for i in plan["items"] if i["decision"] == "delete")
    review = sum(i["kb"] for i in plan["items"] if i["decision"] == "review")
    lines += ["DISCO",
              f"  sai agora: {mb(out)}; se a leitura confirmar: {mb(review)}",
              f"  o que sai vai para {os.path.join(plan['root'], scratch.LIXEIRA)}: o disco só libera "
              "com scratch_apply.py --purge"]
    return "\n".join(lines)


def _igual(pares: list, root: str) -> dict:
    """`ORIGEM=DESTINO` → {origem real dentro da raiz: destino real}; o inválido vira ScratchError."""
    out = {}
    for par in pares:
        origem, sep, destino = par.partition("=")
        if not sep or not origem or not destino:
            raise scratch.ScratchError(f"--igual espera ORIGEM=DESTINO, veio {par!r}")
        origem = os.path.realpath(os.path.join(root, origem))
        if not hk._inside(origem, root) or not os.path.exists(origem):
            raise scratch.ScratchError(f"--igual: {origem} não existe dentro da raiz {root}")
        if not os.path.isdir(destino):
            raise scratch.ScratchError(f"--igual: o destino {destino} não é uma pasta")
        out[origem] = os.path.realpath(destino)
    return out


def main(argv=None) -> int:
    """Lê os argumentos, valida a raiz e o plano, classifica e devolve o rc."""
    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    ap.add_argument("--root", required=True, help="a pasta de rascunho (ex.: ~/.wt)")
    ap.add_argument("--repo", action="append", default=[], help="repo cujo histórico prova e cita (repetível)")
    ap.add_argument("--cite", action="append", default=[], help="arquivo ou pasta de texto que cita (repetível)")
    ap.add_argument("--sem-citas-padrao", action="store_true",
                    help="não ler ~/.claude/CLAUDE.md, ~/.claude/plans nem as memórias")
    ap.add_argument("--igual", action="append", default=[], metavar="ORIGEM=DESTINO",
                    help="a ORIGEM (relativa à raiz) sai se cada arquivo tem cópia igual no DESTINO")
    ap.add_argument("--recent-days", type=float, default=scratch.RECENTE_DIAS)
    ap.add_argument("--plan", required=True, help="onde gravar o plano JSON, fora da raiz")
    args = ap.parse_args(argv)
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(errors="replace")
    root = os.path.realpath(os.path.expanduser(args.root))
    plan_path = Path(args.plan).resolve()
    try:
        if not os.path.isdir(root):
            raise scratch.ScratchError(f"a raiz {root} não é uma pasta")
        if root in ("/", os.path.realpath(Path.home())):
            raise scratch.ScratchError(f"a raiz {root} é a casa toda: aponte para a pasta de rascunho")
        if hk._inside(plan_path, root):
            raise scratch.ScratchError(f"o plano não pode ficar dentro da raiz ({root}): viraria uma entrada")
        repos = [scratch.load_repo(r) for r in args.repo]
        igual = _igual(args.igual, root)
    except scratch.ScratchError as e:
        print(f"erro: {e}", file=sys.stderr)
        return 2
    cites = ([] if args.sem_citas_padrao else scratch.default_cites(Path.home())) + args.cite
    plan = scratch.scan(root, repos, cites, igual, args.recent_days, hk.proc_cwds(), time.time())
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(render(plan))
    print(f"\nplano: {plan_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
