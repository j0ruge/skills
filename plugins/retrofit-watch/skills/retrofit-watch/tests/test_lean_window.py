"""Janela v2 para repos privados, medida apenas pelos refs locais."""
from datetime import datetime, timezone
import json
import unittest
from unittest import mock

from fixture_private import PrivateWorld, SLUG
from fixture_store import requires_store
import rw_store as store

DAY = 86400
T0 = 1_760_000_000
MARK = "\n\nRetrofit-Mode: autonomous"


def iso(ts):
    return datetime.fromtimestamp(ts, timezone.utc).isoformat()


@requires_store
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
        with mock.patch.object(store, "run_bytes", wraps=store.run_bytes) as git:
            self.assertTrue(self.window(14)["cumprido"])
            calls = [call for call in git.call_args_list if call.args[0][0] == "git"]
            self.assertTrue(any("for-each-ref" in call.args[0] for call in calls))
            self.assertTrue(all(call.kwargs["env"]["GIT_ALLOW_PROTOCOL"] == "" for call in calls))
            self.assertFalse(any("fetch" in call.args[0] for call in calls))
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

    def test_store_window_follows_ancestry_within_one_second(self):
        sha = self.publish(3)
        self.w.advance_origin({"docs/proof.md": "reversão\n"}, f"Reverte\n\nThis reverts commit {sha}.",
                              iso(T0))
        self.publish(10)
        got = self.window(14)
        self.assertEqual(got["publicados"], 10)
        self.assertTrue(got["cumprido"])

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

        self.publish(10, T0 + 16 * DAY)
        self.assertEqual(self.window(30)["publicados"], 0)
        self.assertEqual(store.lean_mode(self.ctx, T0 + 30 * DAY), "auto-dry")

    def test_private_revert_with_shared_history_allows_a_new_window(self):
        w = self.w
        self.publish(3)
        sha = w.commit_on_origin({"note.md": "privado"}, f"Publica{MARK}", date=iso(T0))
        w.commit_on_origin({"note.md": "reverte"}, f"Reverte\n\nThis reverts commit {sha}.",
                           date=iso(T0 + DAY))
        w.git(w.live, "fetch", "-q", "origin")
        w.git(w.other, "fetch", "-q", str(w.remote), "main")
        w.git(w.other, "merge", "-q", "--allow-unrelated-histories", "--no-edit", "FETCH_HEAD")
        w.git(w.other, "push", "-q", "origin", "HEAD:main")
        self.publish(10, T0 + 2 * DAY)
        self.assertEqual(self.window(15)["publicados"], 10)
        self.assertTrue(self.window(15)["cumprido"])

    def test_incomplete_scan_requires_rehearsal(self):
        self.publish(10)
        git = store._startup_git

        def incomplete_archive(repo, args, *rest, **kwargs):
            if "archive" in args:
                args = [arg for arg in args if arg != "docs/proof.md"]
            return git(repo, args, *rest, **kwargs)

        with mock.patch.object(store, "_startup_git", side_effect=incomplete_archive):
            self.assertEqual(store.lean_mode(self.ctx, T0 + 14 * DAY), "auto-dry")
        self.assertFalse((self.ctx.data_dir / store.LEAN_WINDOW_FILE).exists())
        self.assertTrue(self.window(14)["cumprido"])

    def test_legacy_scan_cache_is_recomputed(self):
        self.publish(10)
        self.ctx.data_dir.mkdir(parents=True, exist_ok=True)
        heads = {key: self.w.git(repo, "rev-parse", store.BASE_REF)
                 for key, repo in (("store", self.w.store), (SLUG, self.w.live))}
        cache = self.ctx.data_dir / store.LEAN_WINDOW_FILE
        cache.write_text(json.dumps({"heads": heads, "vazados": 0}), encoding="utf-8")
        with mock.patch.object(store, "_leaks", wraps=store._leaks) as scan:
            self.assertTrue(self.window(14)["cumprido"])
            scan.assert_called_once()

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
