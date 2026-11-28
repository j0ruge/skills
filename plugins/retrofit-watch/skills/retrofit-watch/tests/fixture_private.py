"""Repo privado sintético com origem isolada e pre-push observável."""
import json
from pathlib import Path

from fixture_store import StoreWorld
from test_retrofit_watch import make_skill

SLUG = "fixture/kb-libs"
SKILL = "kb-demo"
PASTA = f".claude/skills/{SKILL}"

GATE_STUB = """import json
import os
import subprocess
import sys

rc = int(os.environ.get("RW_FAKE_GATE_RC", "0"))
head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
entry = {"args": sys.argv[1:], "stdin": sys.stdin.read(), "head": head, "rc": rc}
if log := os.environ.get("RW_FAKE_GATE_LOG"):
    with open(log, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry) + "\\n")
print(f"gate: {rc} passo(s) reprovado(s)", file=sys.stderr)
sys.exit(rc)
"""


class PrivateWorld(StoreWorld):
    def __init__(self):
        super().__init__()
        self.remote = self.tmp / "remotes" / f"{SLUG}.git"
        self.remote.parent.mkdir(parents=True)
        self.dev = self.home / "repos/kb-libs"
        self.live = self.home / ".local/share/skills-live/kb-libs"
        self.gate_log = self.tmp / "private-gate.jsonl"
        self.env["RW_FAKE_GATE_LOG"] = str(self.gate_log)

        self.git(self.tmp, "init", "-q", "--bare", str(self.remote))
        self.git(self.remote, "symbolic-ref", "HEAD", "refs/heads/main")
        self.git(self.tmp, "clone", "-q", str(self.remote), str(self.dev))
        self.skill = make_skill(self.dev / ".claude/skills", SKILL)
        (self.skill / "CHANGELOG.md").write_text("# Histórico\n", encoding="utf-8")
        hooks = self.dev / ".githooks"
        hooks.mkdir()
        prepush = hooks / "pre-push"
        prepush.write_text('#!/bin/sh\nexec python3 scripts/gate_stub.py "$@"\n', encoding="utf-8")
        prepush.chmod(0o755)
        (self.dev / "scripts").mkdir()
        (self.dev / "scripts/gate_stub.py").write_text(GATE_STUB, encoding="utf-8")
        self.git(self.dev, "add", "-A")
        self.git(self.dev, "commit", "-qm", "Semeia skill da fixture privada")
        self.assert_fixture_origin(self.dev)
        self.git(self.dev, "push", "-qu", "origin", "HEAD:main")
        self.git(self.dev, "config", "core.hooksPath", ".githooks")
        self.git(self.tmp, "clone", "-q", str(self.remote), str(self.live))
        self.git(self.live, "config", "core.hooksPath", ".githooks")
        self.config()

    def config(self, **extra):
        cfg = {"mode": "auto", "owners": ["fixture"], "store": str(self.store), "lean_auto": [SLUG]}
        (self.home / ".claude/retrofit-watch.json").write_text(json.dumps(cfg | extra), encoding="utf-8")

    def assert_fixture_origin(self, path):
        super().assert_fixture_origin(path)
        path = Path(path).resolve()
        expected = self.remote if path in (self.dev, self.live) else self.origin
        for flag in ([], ["--push"]):
            url = self.git(path, "remote", "get-url", *flag, "origin")
            if Path(url).resolve() != expected:
                raise AssertionError(f"{path}: origin de outra fixture: {url}")

    def commit_on_origin(self, files, message, date=None, gate_rc=0):
        self.assert_fixture_origin(self.dev)
        self.git(self.dev, "fetch", "-q", "origin")
        self.git(self.dev, "reset", "-q", "--hard", "origin/main")
        for rel, body in files.items():
            target = (self.dev / rel).resolve()
            if not target.is_relative_to(self.dev):
                raise ValueError(rel)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(body, encoding="utf-8")
        self.git(self.dev, "add", "-A")
        env = dict(self.env)
        if date is not None:
            env.update(GIT_AUTHOR_DATE=date, GIT_COMMITTER_DATE=date)
        self.git(self.dev, "commit", "-qm", message, env=env)
        self.git(self.dev, "push", "-q", "origin", "HEAD:main", env=dict(env, RW_FAKE_GATE_RC=str(gate_rc)))
        return self.git(self.dev, "rev-parse", "HEAD")
