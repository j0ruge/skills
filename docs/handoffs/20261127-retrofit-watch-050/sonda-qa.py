"""Sonda de QA da CLI com dois bares locais e captura do status por um dublê de gh."""

import json
import os
from pathlib import Path
import subprocess
import sys

from fixture_private import PASTA, SKILL, SLUG, PrivateWorld
import rw_auto as auto
from test_lean_window import MARK, T0, iso
import test_retrofit_watch as watch

def read(path):
    return json.loads(path.read_text(encoding="utf-8"))

def write(path, data):
    path.write_text(json.dumps(data), encoding="utf-8")

def journey(w):
    status = w.tmp / "status.jsonl"
    gh = w.bindir / "gh"
    gh.write_text(f"#!{sys.executable}\n"
                  "import json, os, sys\n"
                  "with open(os.environ['QA_STATUS_LOG'], 'a', encoding='utf-8') as fh:\n"
                  "    print(json.dumps(sys.argv[1:]), file=fh)\n")
    gh.chmod(0o755)
    env = dict(w.env, CLAUDE_PLUGIN_DATA=str(w.data),
               CLAUDE_CODE_SESSION_ATTENDED="1", CLAUDE_CODE_ENTRYPOINT="cli",
               QA_STATUS_LOG=str(status), PATH=f"{w.bindir}{os.pathsep}{os.environ['PATH']}",
               GIT_ALLOW_PROTOCOL="file")
    w.data.mkdir(exist_ok=True)
    def cli(*args, rc=0, payload=None):
        p = subprocess.run([sys.executable, str(watch.SCRIPT), *args], env=env, cwd=w.dev,
                           input=json.dumps(payload) if payload else "", capture_output=True,
                           text=True, timeout=30)
        assert p.returncode == rc, (args, rc, p.returncode, p.stdout, p.stderr)
        if args[0] == "publish":
            raw, phrase = p.stdout.rstrip().rsplit("\n", 1)
            assert phrase, p.stdout
            return json.loads(raw)
        return json.loads(p.stdout)

    def head():
        return w.git(w.remote, "rev-parse", "refs/heads/main")
    def assert_status(sha):
        args = json.loads(status.read_text().splitlines()[-1])
        assert args[:4] == ["api", "-X", "POST", f"repos/{SLUG}/statuses/{sha}"], args
        assert "state=success" in args and "context=local/ci" in args, args
    def snapshot():
        return tuple(w.git(w.dev, *args) for args in [
            ("show-ref",), ("status", "--porcelain"), ("worktree", "list", "--porcelain")
        ])

    w.live.rename(w.live.with_name("anterior"))
    cli("live-setup", SLUG, "--url", str(w.remote))
    w.assert_fixture_origin(w.live)
    w.git(w.live, "config", "--local", "core.hooksPath", ".githooks")
    w.git(w.dev, "switch", "-qc", "trabalho-do-dono")
    (w.dev / "rascunho.txt").write_text("Em andamento\n")
    dev_before = snapshot()
    baseline = head()
    day = subprocess.check_output(["date", "+%Y-%m-%d %H:%M"], text=True).split()[0]
    original = {str(p): (w.skill / p).read_text() for p in ("SKILL.md", "CHANGELOG.md")}

    def prepare(session, mode):
        tx = w.tmp / f"{session}.jsonl"
        records = watch.with_entrypoint(watch.skill_via_tool(SKILL, w.skill), "cli") + sum(
            [watch.tool(error=(i == 0)) for i in range(6)], [])
        tx.write_text("".join(json.dumps(e) + "\n" for e in records))
        out = cli("stop", payload={"session_id": session, "transcript_path": str(tx),
                                  "cwd": str(w.dev), "hook_event_name": "Stop",
                                  "permission_mode": "bypassPermissions", "stop_hook_active": False,
                                  "last_assistant_message": "Feito."})
        assert f"repo {SLUG}, modo {mode}" in out["hookSpecificOutput"]["additionalContext"], out
        rid = read(w.data / f"sessions/{session}.json")["auto_open"]["id"]
        folder = auto.retro_dir(w.ctx(), rid)
        requests = read(folder / "pedido.json")["skills"]
        assert [(s["repo"], s["plugin"], s["modo"]) for s in requests] == [(SLUG, SKILL, mode)]
        write(folder / "licoes.json", {"id": rid, "licoes": [
            {"n": 1, "repo": SLUG, "plugin": SKILL, "skill": SKILL, "tipo": "pitfall",
             "evidencia": {"texto": "o comando falhou", "transcript": str(tx), "entrada": "1"},
             "padrao": "conferir a saída", "resolveu": "a releitura resolveu", "muda_description": False}]})
        write(folder / "veredito.json", {"id": rid, "base": head(), "licoes": [
            {"n": 1, "evidencia_confere": True, "coberta": None, "generica": True,
             "procede": "procede", "basta_o_transcript": None, "nao_capturar": None, "nota": ""}]})
        plan = cli("triage", rid)
        assert [(b["repo"], b["lote"]) for b in plan["lotes"]] == [(SLUG, SKILL)], plan
        prepared = cli("prepare", rid, SKILL)
        assert (prepared["repo"], prepared["pasta"], prepared["base"]) == (SLUG, PASTA, head()), prepared
        wt = Path(prepared["worktree"])
        assert w.git(wt, "remote", "get-url", "--push", "origin") == str(w.remote)
        assert w.git(wt, "rev-parse", "--path-format=absolute", "--git-common-dir") == str(w.live / ".git")
        with (wt / PASTA / "SKILL.md").open("a", encoding="utf-8") as fh:
            fh.write(f"\nConfira o resultado antes de seguir ({session}).\n")
        with (wt / PASTA / "CHANGELOG.md").open("a", encoding="utf-8") as fh:
            fh.write(f"\n## {day}\n\n- Registra procedimento de verificação.\n")
        w.git(wt, "commit", "-qam", "Documenta uma verificação", "-m", "Retrofit-Mode: autonomous")
        return rid, wt

    def seal(rid):
        signed = cli("seal", rid, SKILL, "--licoes", "1")
        folder = auto.lote_dir(w.ctx(), rid, SKILL)
        write(folder / "diff.json", {"patch": signed["patch"], "regra_repetida": None,
                                      "fora_das_licoes": None})
        return signed["patch"]

    def held(rid, reason, remote):
        out = cli("publish", rid, SKILL, rc=1)
        assert (out["resultado"], out["motivo"], out["repo"], head()) == (
            "segurado", reason, SLUG, remote), out
        if reason == "auto-dry":
            assert "gate: 0 passo(s)" in out["detalhe"], out
        return out

    def published(rid, wt):
        sha = w.git(wt, "rev-parse", "HEAD")
        out = cli("publish", rid, SKILL)
        assert (out["resultado"], out["commit"], head(), w.git(w.live, "rev-parse", "HEAD")) == (
            "publicado", sha, sha, sha), out
        assert_status(sha)
        registry = [row for row in auto.read_registry(w.ctx()) if row.get("id") == rid]
        assert (registry[-1]["resultado"], registry[-1]["commit"], registry[-1]["repo"]) == (
            "publicado", sha, SLUG), registry
        logs = [json.loads(line) for line in w.gate_log.read_text().splitlines()]
        assert logs[-2] == logs[-1] and logs[-1]["head"] == sha, logs[-2:]
        return sha

    rid, wt = prepare("ensaio", "auto-dry")
    print("Stop -> pedido -> triagem -> preparação no clone dedicado", flush=True)
    patch = seal(rid)
    held(rid, "auto-dry", baseline)
    first = json.loads(w.gate_log.read_text().splitlines()[-1])
    start = w.git(wt, "rev-parse", "HEAD")
    assert first["stdin"] == f"HEAD {start} refs/heads/main {baseline}\n", first
    assert not status.exists()
    print(f"Ensaio verde, retenção auto-dry, bare preservado {baseline[:12]}", flush=True)
    assert cli("approve", rid, SKILL)["patch"] == patch
    assert head() == baseline
    with (wt / PASTA / "SKILL.md").open("a", encoding="utf-8") as fh:
        fh.write("\nRegistre a divergência antes de repetir a verificação.\n")
    w.git(wt, "commit", "-qa", "--amend", "--no-edit")
    held(rid, "revisao-desatualizada", baseline)
    new_patch = seal(rid)
    assert new_patch != patch
    held(rid, "auto-dry", baseline)
    assert cli("approve", rid, SKILL)["patch"] == new_patch
    assert head() == baseline
    manual_approval = published(rid, wt)
    print(f"Emenda reteve o bare, nova aprovação publicou {manual_approval[:12]} no bare, local/ci, registro e clone",
          flush=True)
    assert snapshot() == dev_before

    for n in range(10):
        w.advance_origin({"docs/teste.md": f"prova {n}\n"}, f"Publica {n}{MARK}", iso(T0))
    w.git(w.store, "fetch", "origin")
    rid, wt = prepare("janela", "auto")
    seal(rid)
    autonomous = published(rid, wt)
    print(f"Janela cumprida, sem approve, bare, local/ci, registro e clone em {autonomous[:12]}", flush=True)
    assert snapshot() == dev_before

    revert_wt = w.tmp / "revert-fixture"
    w.git(w.live, "worktree", "add", "-qb", "revert-fixture", str(revert_wt), "origin/main")
    assert w.git(revert_wt, "remote", "get-url", "--push", "origin") == str(w.remote)
    w.git(revert_wt, "revert", "--no-edit", autonomous)
    w.git(revert_wt, "push", "--no-follow-tags", "origin", "HEAD:main")
    reverted = head()
    cli("live-advance", SLUG)
    rid, _ = prepare("apos-revert", "auto-dry")
    seal(rid)
    held(rid, "auto-dry", reverted)
    print(f"Revert reiniciou janela, ensaio reteve bare em {reverted[:12]}", flush=True)

    manual_wt = w.tmp / "manual-fixture"
    w.git(w.live, "worktree", "add", "-qb", "manual-fixture", str(manual_wt), "origin/main")
    assert w.git(manual_wt, "remote", "get-url", "--push", "origin") == str(w.remote)
    path = manual_wt / PASTA / "SKILL.md"
    path.write_text(original["SKILL.md"] + "\nRegistre a verificação manual.\n")
    with (manual_wt / PASTA / "CHANGELOG.md").open("a", encoding="utf-8") as fh:
        fh.write(f"\n## {day}\n\n- Registra lição manual.\n")
    prior_log = w.gate_log.read_bytes()
    prior_status = status.read_bytes()
    assert head() == w.git(w.live, "rev-parse", "HEAD") == reverted
    assert w.gate_log.read_bytes() == prior_log and status.read_bytes() == prior_status
    print(f"Manual sem confirmação conservou bare e clone em {reverted[:12]}", flush=True)
    w.git(manual_wt, "commit", "-qam", "Registra lição manual")
    w.git(manual_wt, "push", "--no-follow-tags", "origin", "HEAD:main")
    manual = head()
    assert manual != reverted
    gate = json.loads(w.gate_log.read_text().splitlines()[-1])
    assert (gate["head"], gate["rc"]) == (manual, 0), gate
    subprocess.run(["gh", "api", "-X", "POST", f"repos/{SLUG}/statuses/{manual}",
                    "-f", "state=success", "-f", "context=local/ci", "-f", "description=gate verde"],
                   env=env, check=True, timeout=10)
    assert_status(manual)
    cli("live-advance", SLUG)
    assert manual == w.git(w.live, "rev-parse", "HEAD")
    assert snapshot() == dev_before
    print(f"Manual confirmado passou no pre-push e alinhou bare, local/ci e clone em {manual[:12]}", flush=True)

w = PrivateWorld()
try:
    journey(w)
finally:
    w.cleanup()
