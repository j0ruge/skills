"""Janela v2 para repos privados, medida apenas pelos refs locais."""
from datetime import datetime, timezone
import unittest
from unittest import mock

from fixture_private import PrivateWorld, SLUG
import rw_store as store

DAY = 86400
T0 = 1_760_000_000
MARK = "\n\nRetrofit-Mode: autonomous"


def iso(ts):
    return datetime.fromtimestamp(ts, timezone.utc).isoformat()


class LeanWindowTest(unittest.TestCase):
    def setUp(self):
        self.w = PrivateWorld()
        self.addCleanup(self.w.cleanup)
        self.ctx = self.w.ctx()
        self.n = 0

    def publish(self, count, at=T0):
        w = self.w
        for _ in range(count):
            self.n += 1
            sha = w.advance_origin({"docs/proof.md": f"prova {self.n}\n"}, f"Publica {self.n}{MARK}", iso(at))
        w.git(w.store, "fetch", "-q", "origin")
        return sha

    def window(self, days):
        return store.lean_window(self.ctx, T0 + days * DAY)

    def test_floors_modes_and_no_fetch(self):
        self.assertIsNone(store.lean_window(type(self.ctx)(home=self.w.tmp / "ausente")))
        self.assertEqual(store.lean_mode(self.ctx, T0), "auto-dry")
        self.publish(9)
        self.assertFalse(self.window(14)["cumprido"])
        self.publish(1)
        self.assertFalse(self.window(14 - 1 / DAY)["cumprido"])
        with mock.patch.object(store, "_startup_git", wraps=store._startup_git) as git:
            self.assertTrue(self.window(14)["cumprido"])
            self.assertFalse(any("fetch" in call.args[1] for call in git.call_args_list))
        with mock.patch.object(store, "_leaks", side_effect=AssertionError("cache ignorado")):
            self.assertEqual(store.lean_mode(self.ctx, T0 + 14 * DAY), "auto")
        for mode in ("auto-dry", "manual"):
            self.w.config(mode=mode)
            with mock.patch.object(store, "lean_window", side_effect=AssertionError("janela desnecessária")):
                self.assertEqual(store.lean_mode(self.w.ctx()), mode)

    def test_store_revert_resets_then_window_recovers(self):
        sha = self.publish(10)
        self.assertTrue(self.window(14)["cumprido"])
        revert = self.w.advance_origin({"docs/proof.md": "reversão\n"}, f"Reverte\n\nThis reverts commit {sha}.",
                                       iso(T0 + 15 * DAY))
        self.publish(10, T0 + 16 * DAY)
        got = self.window(28)
        self.assertEqual((got["publicados"], got["dias"], got["ultimo_revert"]),
                         (10, 13, T0 + 15 * DAY), revert)
        self.assertFalse(got["cumprido"])
        self.assertTrue(self.window(29)["cumprido"])
        self.assertFalse(store.criterion(self.ctx, T0 + 29 * DAY)["cumprido"])

    def test_private_publishes_do_not_count_and_revert_resets(self):
        w = self.w
        self.publish(9)
        sha = w.commit_on_origin({"note.md": "privado"}, f"Publica{MARK}", date=iso(T0))
        w.git(w.live, "fetch", "-q", "origin")
        self.assertEqual(self.window(13)["publicados"], 9)
        self.publish(1)
        self.assertTrue(self.window(14)["cumprido"])
        w.commit_on_origin({"note.md": "reverte"}, f"Reverte\n\nThis reverts commit {sha[:12]}.",
                           date=iso(T0 + 15 * DAY))
        self.assertTrue(self.window(16)["cumprido"], "o bare não é consultado sem fetch")
        w.git(w.live, "fetch", "-q", "origin")
        self.assertEqual(self.window(16)["ultimo_revert"], T0 + 15 * DAY)
        self.assertEqual(self.window(16)["publicados"], 0)
        self.assertFalse(self.window(16)["cumprido"])

    def test_unreadable_other_history_invalidates_positive_cache(self):
        w = self.w
        parent = w.git(w.remote, "rev-parse", "main")
        w.commit_on_origin({"note.md": "histórico"}, "Nota")
        other_origin = w.remote.parent / "other.git"
        w.git(w.tmp, "clone", "-q", "--bare", str(w.remote), str(other_origin))
        other = w.live.parent / "other"
        w.git(w.tmp, "clone", "-q", str(other_origin), str(other))
        w.config(lean_auto=[SLUG, "fixture/other"])
        self.ctx = w.ctx()
        self.publish(10)
        local_main = "refs/remotes/origin/main"
        self.assertTrue(self.window(14)["cumprido"])
        head = w.git(other, "rev-parse", local_main)
        (other / ".git/objects" / parent[:2] / parent[2:]).unlink()
        self.assertEqual(w.git(other, "rev-parse", f"{local_main}^{{commit}}"), head)
        self.assertEqual(store.lean_mode(self.ctx, T0 + 14 * DAY), "auto-dry")
        w.git(other, "update-ref", "-d", local_main)
        self.assertEqual(store.lean_mode(self.ctx, T0 + 14 * DAY), "auto-dry")

    def test_leak_forces_dry(self):
        self.publish(10)
        name = "xq" + "7zeta"
        private_list = self.w.other / store.PRIVATE_LIST
        digest = store._load_name_check(private_list.parent).resumo(name)
        self.w.advance_origin({store.PRIVATE_LIST: private_list.read_text() + digest + "\n",
                               "docs/proof.md": f"nota de {name}\n"}, "Nota", iso(T0 + 1))
        self.w.git(self.w.store, "fetch", "-q", "origin")
        self.assertEqual(self.window(14)["vazados"], 1)
        self.assertEqual(store.lean_mode(self.ctx, T0 + 14 * DAY), "auto-dry")
