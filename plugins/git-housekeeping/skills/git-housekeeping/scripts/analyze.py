#!/usr/bin/env python3
"""Analisa um repo (ou varre uma pasta de repos) e diz o que a limpeza tiraria, sem apagar nada.

Um repo: `analyze.py --repo . --remote origin --plan <fora do repo>/plano.json` faz fetch (sem
prune), consulta o remoto e o gh, grava o plano e imprime o relatório. Varredura:
`analyze.py --scan ~/repos` não usa rede nem grava plano, e imprime uma linha por repo.
rc 0 ok; 2 uso inválido, remoto que não responde ou repo inválido.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import housekeeping as hk  # noqa: E402

GROUPS = (("delete", "SAI"), ("unproven", "NÃO PROVADO (fica)"), ("keep", "FICA"))


def mb(kb: int) -> str:
    """KiB em MB com uma casa, como o relatório mostra."""
    return f"{kb / 1024:.1f} MB"


def _label(plan: dict, item: dict) -> str:
    """O nome que o usuário reconhece: a ref remote-tracking leva o remoto na frente."""
    return f"{plan['remote']}/{item['name']}" if item["kind"] == "remote-tracking" else item["name"]


def render(plan: dict) -> str:
    """O relatório em texto: cabeçalho, os três grupos com o motivo de cada item, e o disco."""
    gh = "sim" if plan["gh_available"] else f"não ({plan['gh_reason']})"
    lines = [f"git-housekeeping: {plan['repo']} (remoto {plan['remote']}, default "
             f"{plan['default_branch']}, prova por PR: {gh})", ""]
    if not any(i["decision"] == "delete" for i in plan["items"]):
        lines += ["Nada a limpar.", ""]
    for decision, title in GROUPS:
        group = [i for i in plan["items"] if i["decision"] == decision]
        lines.append(f"{title} ({len(group)})")
        for i in group:
            line = f"  {hk.KIND_PT[i['kind']]:<19} {_label(plan, i)}  {i['sha'][:7]}  {i['reason']}"
            if i["author"]:
                line += f"  [último commit: {i['author']}]"
            if i["kind"] == "worktree" and decision == "delete" and i["action"] == "remove":
                names = [("⚠ " if Path(x.rstrip("/")).name.startswith(".env") else "") + x
                         for x in i["ignored"]]
                line += f"  [{mb(i['kb'])}; ignorados que vão junto: {', '.join(names) or 'nenhum'}]"
            lines.append(line)
        lines.append("")
    disk = plan["disk"]
    lines += ["DISCO",
              f"  .git: {mb(disk['git_kb'])}; worktrees que saem: {mb(disk['worktrees_kb'])}",
              "  branches e refs: ~0. A ref tem bytes; os objetos só saem com gc, depois que o reflog expira."]
    return "\n".join(lines)


def scan(root) -> str:
    """Uma linha por repo da pasta: sem rede, só o merge commit como prova, nada gravado."""
    rows = []
    for child in sorted(Path(root).iterdir()):
        if not (child / ".git").is_dir():
            continue
        try:
            items = hk.classify(hk.load_facts(child, "origin", offline=True))
        except hk.GitError as e:
            rows.append(f"{child.name}: não analisado ({e})")
            continue
        out = [i for i in items if i.decision == "delete"]
        fetch_head = child / ".git" / "FETCH_HEAD"
        when = (datetime.fromtimestamp(fetch_head.stat().st_mtime).strftime("%Y-%m-%d")
                if fetch_head.exists() else "nunca")

        def count(kind: str) -> int:
            return sum(1 for i in out if i.kind == kind)

        kb = sum(i.kb for i in out if i.kind == "worktree")
        rows.append(f"{child.name}: último fetch {when}; sairiam {count('local-branch')} local(is), "
                    f"{count('remote-branch')} remota(s), {count('worktree')} worktree(s), {mb(kb)}")
    rows += ["", "Varredura sem rede: só o merge commit conta como prova (squash não foi contado), "
                 "e as remotas vêm do último fetch de cada repo."]
    return "\n".join(rows)


def _inside_repo(plan_path: Path, repo) -> str:
    """O worktree do repo que contém o caminho do plano, ou ""."""
    for wt in hk.worktrees(repo):
        if plan_path.is_relative_to(Path(wt.path).resolve()):
            return wt.path
    return ""


def main(argv=None) -> int:
    """Lê os argumentos, roda a análise ou a varredura e devolve o rc."""
    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--repo", help="repo a analisar (gera plano)")
    mode.add_argument("--scan", help="pasta de repos a varrer (só lê)")
    ap.add_argument("--remote", default="origin")
    ap.add_argument("--plan", help="onde gravar o plano JSON, fora do repo")
    args = ap.parse_args(argv)
    for stream in (sys.stdout, sys.stderr):   # nome de branch com acento num console cp1252
        stream.reconfigure(errors="replace")
    if args.scan:
        print(scan(args.scan))
        return 0
    if not args.plan:
        ap.error("--plan é obrigatório com --repo")
    plan_path = Path(args.plan).resolve()
    try:
        holder = _inside_repo(plan_path, args.repo)
        if holder:
            print(f"erro: o plano não pode ficar dentro do repo ({holder}): sujaria a árvore e o "
                  "pre-push recusaria o próximo push", file=sys.stderr)
            return 2
        plan = hk.build_plan(hk.load_facts(args.repo, args.remote))
    except hk.GitError as e:
        print(f"erro: {e}", file=sys.stderr)
        return 2
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(render(plan))
    print(f"\nplano: {plan_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
