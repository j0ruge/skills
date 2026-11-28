"""Elegibilidade e formato do pedido de uma sessão com origens mistas."""
import json
import unittest
from unittest import mock

import test_retrofit_watch as watch
from fixture_private import PrivateWorld, SLUG
import rw_auto as auto
import rw_store as store

rw = watch.rw
PAYLOAD = {"permission_mode": "bypassPermissions", "session_id": "fixture"}


class OriginTest(unittest.TestCase):
    def test_only_supported_origin_shapes(self):
        for url in ("https://github.com/Fixture/KB-libs.git", "git@github.com:Fixture/KB-libs.git",
                    "ssh://git@github.com/fixture/kb-libs", "/tmp/remotes/fixture/kb-libs.git"):
            with self.subTest(url=url):
                self.assertEqual(rw.origin_slug(url), SLUG)
        for url in ("kb-libs", "https://github.com/kb-libs", "https://github.com/a/b/c",
                    "http://github.com/a/b", "https://github.com/../kb-libs",
                    "https://github.com/a/b?x=y", "/tmp/a/../b.git", "file:///tmp/a/b.git"):
            with self.subTest(url=url):
                self.assertIsNone(rw.origin_slug(url))


class LeanAutoTest(unittest.TestCase):
    def setUp(self):
        self.w = PrivateWorld()
        self.addCleanup(self.w.cleanup)
        self.entry = rw.classify_path(self.w.skill, self.w.ctx())
        self.full = rw.classify_path(self.w.store / "plugins/demo/skills/demo", self.w.ctx())

    def reason(self, *, entry=None, payload=PAYLOAD, entrypoint="cli"):
        return auto.why_manual(self.w.ctx(), payload, self.entry if entry is None else entry, [], entrypoint)

    def test_only_owned_tracked_local_skills_can_enter(self):
        self.assertEqual(self.entry["origin"], SLUG)
        self.assertEqual(self.entry["repo"], str(self.w.dev))
        self.w.config(owners=["fixture", "chewiesoft"])
        with mock.patch.object(store, "run_bytes", side_effect=AssertionError("git desnecessário")):
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
        self.assertFalse(auto.in_request(ctx, with_collision, lesson))
        path = auto.retro_dir(ctx, pedido["id"]) / "pedido.json"
        self.assertEqual(auto.load_pedido(path), pedido)
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
