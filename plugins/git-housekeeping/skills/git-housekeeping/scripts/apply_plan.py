#!/usr/bin/env python3
"""Apaga só o que o plano do analyze.py marca como `delete`, e só depois de provar cada item de novo.

`apply_plan.py --plan <arquivo> --scope local|remote [--dry-run]`. O plano é a lista do que pode
sair, não a prova: cada item é reclassificado com os fatos de agora, e o que mudou é recusado. Uma
recusa nunca é contornada com outro comando (-D, --force, --no-verify): vai para o relatório.
rc 0 tudo feito; 1 algum item recusado ou falhou; 2 plano ou uso inválido.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import housekeeping as hk  # noqa: E402


class Run:
    """As linhas do relatório, os comandos de desfazer e se algo foi recusado."""

    def __init__(self, dry: bool):
        self.dry, self.failed, self.lines, self.undo = dry, False, [], []

    def done(self, label: str, undo: str = "") -> None:
        """Item apagado (ou que seria, no --dry-run), com o comando que o traz de volta."""
        self.lines.append(("faria: " if self.dry else "apagado: ") + label)
        if undo and not self.dry:
            self.undo.append(undo)

    def refuse(self, label: str, why: str) -> None:
        """Item que não saiu, com o motivo; o rc passa a 1."""
        self.failed = True
        self.lines.append(f"recusado: {label}: {why}")


def label(item: hk.Item, remote: str) -> str:
    """Tipo e nome do item, em PT-BR, como o relatório do analyze mostra."""
    name = f"{remote}/{item.name}" if item.kind == "remote-tracking" else item.name
    return f"{hk.KIND_PT[item.kind]} {name}"


def push_deletions(repo, remote: str, pairs: list) -> tuple:
    """Apaga as branches do remoto num push só, cada uma com a lease do sha do plano.

    Sem --atomic: a branch que andou é recusada sozinha (`stale info`) e as outras saem. Devolve
    {branch: (apagada, resumo)} e o fim do stderr, que explica o push que nem rodou (pre-push).
    """
    leases = [f"--force-with-lease=refs/heads/{b}:{sha}" for b, sha in pairs]
    refs = [f":refs/heads/{b}" for b, _ in pairs]
    proc = hk.run_git(repo, "push", "--porcelain", *leases, remote, *refs)
    by_ref = hk.parse_push_porcelain(proc.stdout)
    result = {b: by_ref.get(f"refs/heads/{b}", (False, "")) for b, _ in pairs}
    return result, " | ".join(proc.stderr.strip().splitlines()[-3:])


def apply_local(facts: hk.Facts, items: list, run: Run) -> None:
    """Worktrees (remove, depois prune), branches locais e refs remote-tracking, nesta ordem."""
    repo, remote = facts.repo, facts.remote
    gone = set()
    for i in (x for x in items if x.kind == "worktree" and x.action == "remove"):
        if run.dry:
            gone.add(i.name)
            run.done(label(i, remote))
            continue
        proc = hk.run_git(repo, "worktree", "remove", i.name)
        if proc.returncode:
            run.refuse(label(i, remote), proc.stderr.strip())
            continue
        gone.add(i.name)
        run.done(label(i, remote), f"git worktree add {i.name} {i.branch or i.sha}  (os ignorados não voltam)")
    prunes = [x for x in items if x.kind == "worktree" and x.action == "prune"]
    if prunes:
        planned = {i.name for i in prunes}
        extra = sorted(w.path for w in hk.worktrees(repo) if w.prunable and w.path not in planned)
        if extra:
            for i in prunes:
                run.refuse(label(i, remote), f"há worktree prunable fora do plano ({', '.join(extra)}); "
                                             "rode o analyze de novo")
        elif run.dry or hk.run_git(repo, "worktree", "prune").returncode == 0:
            for i in prunes:
                gone.add(i.name)
                run.done(label(i, remote) + " (prune)")
        else:
            for i in prunes:
                run.refuse(label(i, remote), "git worktree prune falhou")
    in_use = {w.branch: w.path for w in hk.worktrees(repo) if w.branch and w.path not in gone}
    for i in (x for x in items if x.kind == "local-branch"):
        if i.name in in_use:
            run.refuse(label(i, remote), f"em uso no worktree {in_use[i.name]}")
            continue
        if run.dry:
            run.done(label(i, remote))
            continue
        proc = hk.run_git(repo, "update-ref", "-d", f"refs/heads/{i.name}", i.sha)
        if proc.returncode:
            run.refuse(label(i, remote), proc.stderr.strip())
            continue
        hk.run_git(repo, "config", "--remove-section", f"branch.{i.name}")
        run.done(f"{label(i, remote)} ({i.sha[:7]})", f"git branch {i.name} {i.sha}")
    for i in (x for x in items if x.kind == "remote-tracking"):
        ref = f"refs/remotes/{remote}/{i.name}"
        if run.dry:
            run.done(label(i, remote))
            continue
        proc = hk.run_git(repo, "update-ref", "-d", ref, i.sha)
        if proc.returncode:
            run.refuse(label(i, remote), proc.stderr.strip())
        else:
            run.done(label(i, remote), f"git update-ref {ref} {i.sha}")


def apply_remote(facts: hk.Facts, items: list, run: Run) -> None:
    """As branches do remoto, num push com uma lease por item; o pre-push roda e manda."""
    if not items:
        return
    if run.dry:
        for i in items:
            run.done(label(i, facts.remote))
        return
    result, tail = push_deletions(facts.repo, facts.remote, [(i.name, i.sha) for i in items])
    for i in items:
        ok, summary = result[i.name]
        if ok:
            run.done(f"{label(i, facts.remote)} ({i.sha[:7]})",
                     f"git push {facts.remote} {i.sha}:refs/heads/{i.name}")
        elif summary:
            run.refuse(label(i, facts.remote), summary)
        else:
            run.refuse(label(i, facts.remote), f"o push não rodou (pre-push ou remoto recusou): {tail}")


def recheck(plan: dict, scope: str, now: dict, run: Run) -> list:
    """Os itens `delete` do escopo que ainda são `delete`, com o mesmo sha e a mesma ação."""
    ok = []
    for raw in plan["items"]:
        if raw["decision"] != "delete" or raw["scope"] != scope:
            continue
        item = hk.Item(**raw)
        cur = now.get((item.kind, item.name))
        if cur is None:
            run.refuse(label(item, plan["remote"]), "não existe mais")
        elif cur.decision != "delete":
            run.refuse(label(item, plan["remote"]), f"agora é {cur.decision}: {cur.reason}")
        elif cur.sha != item.sha:
            run.refuse(label(item, plan["remote"]),
                       f"a ponta mudou: no plano {item.sha[:7]}, agora {cur.sha[:7]}")
        elif cur.action != item.action:
            run.refuse(label(item, plan["remote"]), f"a ação mudou: no plano {item.action}, agora {cur.action}")
        elif set(cur.ignored) - set(item.ignored):
            # O usuário confirmou vendo a lista do plano; o que apareceu depois ele não viu.
            novos = ", ".join(sorted(set(cur.ignored) - set(item.ignored)))
            run.refuse(label(item, plan["remote"]), f"ignorados novos desde o plano ({novos}); "
                                                    "rode o analyze de novo")
        else:
            ok.append(item)
    return ok


def main(argv=None) -> int:
    """Valida o plano, reclassifica com os fatos de agora e apaga o que passou."""
    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    ap.add_argument("--plan", required=True)
    ap.add_argument("--scope", required=True, choices=("local", "remote"))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    for stream in (sys.stdout, sys.stderr):   # nome de branch com acento num console cp1252
        stream.reconfigure(errors="replace")
    try:
        plan = json.loads(Path(args.plan).read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        print(f"erro: plano ilegível: {e}", file=sys.stderr)
        return 2
    if plan.get("version") != hk.PLAN_VERSION:
        print(f"erro: plano versão {plan.get('version')!r}; este script lê a {hk.PLAN_VERSION}",
              file=sys.stderr)
        return 2
    fields = set(hk.Item.__dataclass_fields__)
    if any(set(raw) != fields for raw in plan.get("items", [])):
        print("erro: o plano tem item com campos que o analyze.py não gera", file=sys.stderr)
        return 2
    # O escopo segue o tipo: um item local trocado para "remote" apagaria a remota de mesmo nome
    # sem que a remota tivesse sido classificada.
    if any(raw["scope"] != ("remote" if raw["kind"] == "remote-branch" else "local")
           for raw in plan["items"]):
        print("erro: o plano tem item com escopo trocado (o escopo segue o tipo do item)",
              file=sys.stderr)
        return 2
    try:
        common = hk.git(plan["repo"], "rev-parse", "--path-format=absolute", "--git-common-dir").strip()
        if not hk.same_path(common, plan["git_common_dir"]):
            print(f"erro: o plano é de outro repo ({plan['git_common_dir']}, e não {common})",
                  file=sys.stderr)
            return 2
        facts = hk.load_facts(plan["repo"], plan["remote"])
        now = {(i.kind, i.name): i for i in hk.classify(facts)}
    except hk.GitError as e:
        print(f"erro: {e}", file=sys.stderr)
        return 2
    run = Run(args.dry_run)
    items = recheck(plan, args.scope, now, run)
    (apply_local if args.scope == "local" else apply_remote)(facts, items, run)
    print("\n".join(run.lines) or "nada a apagar neste escopo")
    # Do último apagado ao primeiro: o worktree só volta depois que a branch dele voltou.
    for line in reversed(run.undo):
        print(f"desfazer: {line}")
    return 1 if run.failed else 0


if __name__ == "__main__":
    sys.exit(main())
