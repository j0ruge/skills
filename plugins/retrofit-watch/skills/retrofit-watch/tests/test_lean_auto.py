"""Elegibilidade e formato do pedido de uma sessão com origens mistas."""
import json
import shlex
import subprocess
import unittest
from unittest import mock

import test_retrofit_watch as watch
from fixture_private import PASTA, PrivateWorld, SKILL, SLUG
import rw_auto as auto
import rw_store as store

rw = watch.rw
PAYLOAD = {"permission_mode": "bypassPermissions", "session_id": "fixture"}


class OriginTest(unittest.TestCase):
    def test_only_supported_origin_shapes(self):
        for url in ("https://github.com/Fixture/KB-libs.git", "git@localhost:Fixture/KB-libs.git",
                    "ssh://git@localhost/fixture/kb-libs", "/tmp/remotes/fixture/kb-libs.git"):
            with self.subTest(url=url):
                self.assertEqual(rw.origin_slug(url), SLUG)
        for url in ("kb-libs", "https://github.com/kb-libs", "https://github.com/a/b/c",
                    "http://github.com/a/b", "https://github.com/../kb-libs",
                    "https://github.com:0/a/b", "ssh://github.com:65536/a/b",
                    "https://github.com%2Fother.example/a/b", None,
                    "https://github.com/a/b?x=y", "/tmp/a/../b.git", "file:///tmp/a/b.git"):
            with self.subTest(url=url):
                self.assertIsNone(rw.origin_slug(url))


class LeanAutoTest(watch.HookHarness, unittest.TestCase):
    def setUp(self):
        self.w = PrivateWorld()
        self.addCleanup(self.w.cleanup)
        self.entry = rw.classify_path(self.w.skill, self.w.ctx())
        self.full = rw.classify_path(self.w.store / "plugins/demo/skills/demo", self.w.ctx())

    def reason(self, *, entry=None, payload=PAYLOAD, entrypoint="cli"):
        return auto.why_manual(self.w.ctx(), payload, self.entry if entry is None else entry, [], entrypoint)

    def test_origin_recheck_uses_the_evidence_checkout_despite_inherited_git_locations(self):
        with mock.patch.dict("os.environ", GIT_DIR=str(self.w.store / ".git"), GIT_WORK_TREE=str(self.w.store)):
            self.assertIsNone(self.reason())

    def test_stop_dispatch_uses_the_evidence_checkout_identity(self):
        w = self.w
        for session in ("original", "reescrito", "legado"):
            with self.subTest(session=session):
                w.transcript.write_text("")
                w.git(w.dev, "remote", "set-url", "origin", str(w.remote))
                self.write(watch.with_entrypoint(watch.skill_via_tool(SKILL, w.skill), "cli"), watch.tool())
                payload = {"session_id": session, "transcript_path": str(w.transcript),
                           "last_assistant_message": "Feito.", "permission_mode": "bypassPermissions"}
                env = {"GIT_ALLOW_PROTOCOL": ""}
                self.assertIsNone(self.run_hook(raw=json.dumps(payload), env=env))
                if session == "reescrito":
                    w.git(w.dev, "remote", "set-url", "origin", f"https://example.invalid/{SLUG}.git")
                if session == "legado":
                    state_file = w.data / "sessions" / f"{session}.json"
                    state = json.loads(state_file.read_text())
                    for entry in (*state["classified"].values(), *state["skills"].values()):
                        entry.pop("skill_path", None)
                    state_file.write_text(json.dumps(state))
                self.write(*[watch.tool()] * 5)
                output = self.context_of(self.run_hook(raw=json.dumps(payload), env=env))
                if session == "original":
                    self.assertIn("6 chamadas", output)
                    self.assertIn("[modo autônomo:", output)
                else:
                    self.assertNotIn("[modo autônomo:", output)
                    self.assertIn("/retrofit-skill:retrofit-skill", output)

        requests = list((w.data / auto.AUTO_DIR).glob("*/pedido.json"))
        self.assertEqual(len(requests), 1)
        self.assertEqual(auto.load_pedido(requests[0])["skills"][0]["skill_path"], f"{PASTA}/SKILL.md")

    def test_only_owned_tracked_local_skills_can_enter(self):
        self.assertEqual(self.entry["origin"], SLUG)
        self.assertEqual(self.entry["repo"], str(self.w.dev))
        self.w.config(owners=["fixture", "chewiesoft"])
        self.assertIsNone(self.reason())
        ctx = self.w.ctx()
        self.assertIsNone(rw.classify_path(self.w.local_only, ctx))
        self.assertIsNone(rw.classify_path(self.w.locked, ctx))
        self.assertIsNone(rw.classify_path(self.w.napkin, ctx))
        self.assertIsNone(rw.classify_path(self.w.agents_skill, ctx))
        self.w.config(include=[self.w.local_only.name], lean_auto=["chewiesoft/app-interno"],
                      owners=["fixture", "chewiesoft"])
        forced = rw.classify_path(self.w.local_only, self.w.ctx())
        self.assertEqual(self.reason(entry=forced), "kit-ou-lean")
        self.w.config(owners=["other"])
        self.assertEqual(self.reason(), "kit-ou-lean")

    def test_split_shares_the_local_ref_budget_across_entries(self):
        self.w.config(mode="auto")
        ctx = self.w.ctx()
        second = dict(self.entry, key="segunda-skill", arg="segunda-skill")
        now = [100.0]
        deadline = now[0] + store.STARTUP_TIMEOUT

        def resolve(*args, **kwargs):
            self.assertIn("for-each-ref", args[0])
            self.assertEqual(kwargs["timeout"], store.STARTUP_TIMEOUT)
            self.assertEqual(kwargs["env"]["GIT_ALLOW_PROTOCOL"], "")
            now[0] += store.STARTUP_TIMEOUT + 1
            return 0, "refs/heads/main\0\0commit\n"

        with mock.patch.object(auto.time, "monotonic", side_effect=lambda: now[0]), \
                mock.patch.object(store, "run", side_effect=resolve) as git:
            automatic, manual, _ = auto.split(ctx, PAYLOAD, [self.entry, second], "cli", deadline=deadline)
            pedido = auto.open_request(ctx, PAYLOAD, automatic, deadline=deadline)

        self.assertEqual(automatic, [self.entry])
        self.assertEqual(manual, [second])
        self.assertEqual(pedido["skills"][0]["modo"], "auto-dry")
        self.assertEqual(git.call_count, 1)

    def test_precedence(self):
        w = self.w
        w.config(mode="manual", lean_auto=[])
        self.assertEqual(self.reason(), "modo")
        w.config(lean_auto=[])
        self.assertEqual(self.reason(), "kit-ou-lean")
        w.config(manual=[self.entry["arg"]], store=None)
        self.assertEqual(self.reason(payload={}, entrypoint="sdk-cli"), "lista-manual")
        w.config(store=None)
        self.assertEqual(self.reason(payload={}, entrypoint="sdk-cli"), "permissao")
        self.assertEqual(self.reason(entrypoint="sdk-cli"), "entrypoint")
        self.assertEqual(self.reason(), "sem-loja")
        w.config(auto_limits={"per_skill": 0})
        self.assertEqual(self.reason(), "teto")
        w.git(w.live, "remote", "set-url", "origin", str(w.origin))
        self.assertEqual(self.reason(), "sem-clone")
        self.assertEqual(self.reason(entry=dict(self.entry, mode="kit")), "kit-ou-lean")
        w.config(live_dir="~/.hermes/clones")
        self.assertIsNone(self.w.ctx().live_dir)
        self.assertEqual(self.reason(), "sem-clone")
        w.config(live_dir=str(w.tmp / "ausente"), store=None)
        self.assertEqual(self.reason(), "sem-loja")
        w.config(live_dir=str(w.tmp / "ausente"))
        self.assertEqual(self.reason(), "sem-clone")

    def test_same_slug_on_another_host_stays_manual(self):
        w = self.w
        w.git(w.live, "remote", "set-url", "origin", f"https://localhost/{SLUG}.git")
        for url, reason in (
            (f"https://localhost/{SLUG}.git", None),
            (f"https://other.example/{SLUG}.git", "sem-clone"),
            (f"https://localhost:8443/{SLUG}.git", "sem-clone"),
        ):
            with self.subTest(url=url):
                w.git(w.dev, "remote", "set-url", "origin", url)
                entry = rw.classify_path(w.skill, w.ctx())
                self.assertEqual(entry["origin"], SLUG)
                self.assertEqual(self.reason(entry=entry), reason)
        w.git(w.live, "remote", "set-url", "origin", str(w.remote))
        other_bare = w.tmp / "outro" / f"{SLUG}.git"
        w.git(w.dev, "remote", "set-url", "origin", str(other_bare))
        self.assertEqual(self.reason(entry=rw.classify_path(w.skill, w.ctx())), "sem-clone")
        self.assertEqual(self.reason(entry=dict(self.entry, origin_identity=None)), "origem-da-skill")

    def test_unverified_transport_equivalence_stays_manual(self):
        w = self.w
        scp = f"git@localhost:{SLUG}.git"
        ssh = f"ssh://git@localhost/{SLUG}.git"
        https = f"https://localhost/{SLUG}.git"
        probe = w.tmp / "ssh-probe"
        probe.write_text('#!/bin/sh\nfor arg do last=$arg; done\nprintf "%s\\n" "$last" >&2\nexit 1\n')
        probe.chmod(0o755)
        env = dict(w.env, GIT_SSH_COMMAND=shlex.quote(str(probe)), GIT_SSH_VARIANT="ssh")
        for url, path in ((scp, f"{SLUG}.git"), (ssh, f"/{SLUG}.git")):
            w.git(w.dev, "remote", "set-url", "origin", url)
            with self.assertRaises(subprocess.CalledProcessError) as call:
                w.git(w.dev, "ls-remote", "origin", env=env)
            self.assertIn(f"git-upload-pack '{path}'", call.exception.stderr.splitlines())

        for authorized, actual, reason in (
            (scp, scp, None),
            (scp, ssh, "sem-clone"),
            (https, scp, "sem-clone"),
            (https, ssh, "sem-clone"),
            (ssh, ssh.replace("git@", "other@"), "sem-clone"),
            (ssh, ssh.replace("localhost/", "localhost:22/"), "sem-clone"),
            (f"https://github.com/{SLUG}", "github.com:Fixture/KB-libs.git", None),
            (f"https://github.com/{SLUG}", f"ssh://github.com/{SLUG}.git", None),
        ):
            with self.subTest(authorized=authorized, actual=actual):
                w.git(w.live, "remote", "set-url", "origin", authorized)
                w.git(w.dev, "remote", "set-url", "origin", actual)
                entry = rw.classify_path(w.skill, w.ctx())
                self.assertEqual(entry["origin"], SLUG)
                self.assertEqual(self.reason(entry=entry), reason)

    def test_same_host_distinct_repo_paths_stay_manual(self):
        w = self.w
        base = "https://localhost"
        w.git(w.live, "remote", "set-url", "origin", f"{base}/{SLUG}.git")
        for path, reason in ((f"{SLUG}.git", None), ("fixture/KB-libs.git", "sem-clone"),
                             ("Fixture/kb-libs.git", "sem-clone"), (SLUG, "sem-clone"),
                             (f"{SLUG}.git/", "sem-clone")):
            with self.subTest(path=path):
                w.git(w.dev, "remote", "set-url", "origin", f"{base}/{path}")
                entry = rw.classify_path(w.skill, w.ctx())
                self.assertEqual(entry["origin"], SLUG)
                self.assertEqual(self.reason(entry=entry), reason)

    def test_mixed_request_and_legacy_full(self):
        ctx = self.w.ctx()
        pedido = auto.open_request(ctx, PAYLOAD, [self.full, self.entry])
        self.assertEqual(pedido["modo"], "auto")
        full, lean = pedido["skills"]
        self.assertEqual((full["repo"], full["modo"]), (None, "auto"))
        self.assertEqual((lean["repo"], lean["modo"]), (SLUG, "auto-dry"))
        self.assertFalse(auto.in_request(ctx, pedido, {"plugin": lean["plugin"], "skill": lean["plugin"]}))
        lesson = {"plugin": full["plugin"], "skill": full["plugin"]}
        self.assertTrue(auto.in_request(ctx, pedido, lesson))
        with_collision = dict(pedido, skills=[full, dict(lean, plugin=full["plugin"])])
        self.assertTrue(auto.in_request(ctx, with_collision, lesson))
        path = auto.retro_dir(ctx, pedido["id"]) / "pedido.json"
        self.assertEqual(auto.load_pedido(path), pedido)
        self.assertEqual(lean["origin_id"], rw.origin_id(self.entry["origin_identity"]))
        saved = lean.pop("origin_id")
        path.write_text(json.dumps(pedido))
        with self.assertRaises(auto.Malformed):
            auto.load_pedido(path)
        lean["origin_id"] = saved
        lean["repo"] = "fixture/../kb-libs"
        path.write_text(json.dumps(pedido))
        with self.assertRaises(auto.Malformed):
            auto.load_pedido(path)
        for key in ("repo", "modo"):
            del full[key]
        pedido["skills"] = [full]
        path.write_text(json.dumps(pedido))
        self.assertEqual(auto.load_pedido(path), pedido)

    def test_default_config(self):
        ctx = self.w.ctx()
        self.assertEqual(ctx.live_dir, self.w.home / ".local/share/skills-live")
        self.w.config(lean_auto=None)
        self.assertEqual(self.w.ctx().lean_auto, frozenset())
        self.w.config(lean_auto=["FIXTURE/KB-LIBS", "fixture/..", "other/kb-libs", 42])
        self.assertEqual(self.w.ctx().lean_auto, frozenset({SLUG}))
        self.w.config(live_dir="~/protegido/clone", deny_roots=["~/protegido"])
        self.assertIsNone(self.w.ctx().live_dir)
