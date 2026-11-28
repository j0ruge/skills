"""O clone em uso segue a main sem tocar o checkout de desenvolvimento."""
import json
import subprocess
import sys
import unittest

from fixture_private import PrivateWorld, SLUG
import rw_store as store


class LiveTest(unittest.TestCase):
    def setUp(self):
        self.w = PrivateWorld()
        self.addCleanup(self.w.cleanup)
        self.ctx = self.w.ctx()
        self.w.data.mkdir(exist_ok=True)

    def cli(self, *args):
        script = store.rw_auto.rw.__file__
        return subprocess.run([sys.executable, script, *args], env=dict(
            self.w.env, CLAUDE_PLUGIN_DATA=str(self.w.data)), capture_output=True, text=True)

    def test_setup_clones_main_with_worktree_lock(self):
        w = self.w
        w.assert_fixture_origin(w.live)
        w.git(w.remote, "branch", "outro", "main")
        w.git(w.remote, "symbolic-ref", "HEAD", "refs/heads/outro")
        w.live.rename(w.live.with_name("anterior"))
        result = self.cli("live-setup", SLUG, "--url", str(w.remote))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(str(w.live), result.stdout)
        self.assertEqual(store.live_clone(self.ctx, SLUG), w.live)
        self.assertEqual(w.git(w.live, "branch", "--show-current"), "main")
        self.assertEqual(w.git(w.live, "config", "extensions.worktreeConfig"), "true")
        head = w.git(w.live, "rev-parse", "HEAD")
        w.git(w.live, "config", "--local", "core.hooksPath", ".githooks")
        with self.assertRaises(subprocess.CalledProcessError) as denied:
            w.git(w.live, "commit", "--allow-empty", "-m", "Bloqueado")
        self.assertIn("worktree do lote", denied.exception.stderr)
        self.assertEqual(w.git(w.live, "rev-parse", "HEAD"), head)
        batch = w.tmp / "lote"
        w.git(w.live, "worktree", "add", "-qb", "lote", str(batch))
        self.assertEqual(w.git(batch, "config", "core.hooksPath"), ".githooks")
        w.git(batch, "commit", "--allow-empty", "-qm", "Commit no lote")
        w.assert_fixture_origin(w.live)
        self.assertEqual(w.git(batch, "remote", "get-url", "--push", "origin"), str(w.remote))
        w.git(batch, "push", "-q", "origin", "HEAD:refs/heads/lote")
        self.assertEqual(json.loads(w.gate_log.read_text().splitlines()[-1])["head"],
                         w.git(batch, "rev-parse", "HEAD"))

    def test_setup_preserves_existing_destination_and_rejects_wrong_slug_or_url(self):
        w = self.w
        (w.live / "estado").write_text("preservar")
        w.config(owners=["fixture", "other"], lean_auto=[SLUG, "other/kb-libs"])
        for slug in (SLUG, "other/kb-libs"):
            url = w.remote if slug == SLUG else w.remote.parents[1] / "other/kb-libs.git"
            with self.subTest(slug=slug), self.assertRaisesRegex(store.StoreError, "destino já existe"):
                store.live_setup(w.ctx(), slug, str(url))
        for slug in ("fixture/..", "fixture/fora"):
            with self.subTest(slug=slug), self.assertRaisesRegex(store.StoreError, "destino autorizado"):
                store.live_setup(w.ctx(), slug, str(w.remote.parent / "fora.git"))
        self.assertEqual((w.live / "estado").read_text(), "preservar")
        w.live.rename(w.live.with_name("anterior"))
        with self.assertRaises(store.StoreError):
            store.live_setup(w.ctx(), SLUG, str(w.origin))
        self.assertFalse(w.live.exists())

    def test_setup_refuses_target_symlink_even_if_dangling(self):
        w = self.w
        w.live.rename(w.live.with_name("anterior"))
        outside = w.tmp / "ausente"
        w.live.symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(store.StoreError, "destino"):
            store.live_setup(self.ctx, SLUG, str(w.remote))
        self.assertEqual(w.live.readlink(), outside)
        self.assertFalse(outside.exists())

    def test_advance_fast_forwards_ignoring_only_ignored_files_and_records_result(self):
        w = self.w
        head = w.git(w.live, "rev-parse", "HEAD")
        (w.live / ".git/info/exclude").write_text("estado\n")
        (w.live / "estado").write_text("preservar")
        new = w.commit_on_origin({"README.md": "nova revisão"}, "Avança o bare")
        result = self.cli("live-advance")
        self.assertEqual(result.returncode, 0, result.stderr)
        record = json.loads((w.data / "live/kb-libs.json").read_text())
        self.assertEqual(set(record), {"repo", "resultado", "antes", "depois", "detalhe", "ts"})
        self.assertEqual((record["repo"], record["resultado"], record["antes"], record["depois"]),
                         (SLUG, "ok", head, new))
        self.assertIsInstance(record["ts"], int)
        self.assertEqual(w.git(w.live, "rev-parse", "HEAD"), new)
        self.assertEqual((w.live / "estado").read_text(), "preservar")

    def test_advance_leaves_wrong_branch_dirty_tree_and_divergence_alone(self):
        w = self.w
        head = w.git(w.live, "rev-parse", "HEAD")
        w.commit_on_origin({"README.md": "nova revisão"}, "Avança o bare")
        w.git(w.live, "switch", "-qc", "outro")
        self.assertEqual(store.live_advance(self.ctx, SLUG)["resultado"], "fora-da-main")
        self.assertEqual(w.git(w.live, "rev-parse", "HEAD"), head)
        w.git(w.live, "switch", "-q", "main")
        (w.live / "estado").write_text("preservar")
        self.assertEqual(store.live_advance(self.ctx, SLUG)["resultado"], "suja")
        self.assertEqual(w.git(w.live, "rev-parse", "HEAD"), head)
        self.assertEqual(w.git(w.live, "rev-parse", "origin/main"), head)
        (w.live / "estado").unlink()
        w.git(w.live, "commit", "--allow-empty", "-qm", "Diverge")
        divergent = w.git(w.live, "rev-parse", "HEAD")
        result = store.live_advance(self.ctx, SLUG)
        self.assertEqual((result["resultado"], result["antes"], result["depois"]),
                         ("erro", divergent, divergent))
        self.assertEqual(w.git(w.live, "rev-parse", "HEAD"), divergent)

    def test_advance_refuses_ahead_head_and_preserves_ignored_data_on_conflict(self):
        w = self.w
        head = w.git(w.live, "rev-parse", "HEAD")
        w.git(w.live, "commit", "--allow-empty", "-qm", "Commit só no clone")
        ahead = w.git(w.live, "rev-parse", "HEAD")
        self.assertEqual(store.live_advance(self.ctx, SLUG)["resultado"], "erro")
        self.assertEqual(w.git(w.live, "rev-parse", "HEAD"), ahead)
        w.git(w.live, "reset", "--hard", head)
        (w.live / ".git/info/exclude").write_text("estado\n")
        (w.live / "estado").write_text("preservar")
        w.commit_on_origin({"estado": "versão rastreada"}, "Toca o arquivo ignorado local")
        self.assertEqual(store.live_advance(self.ctx, SLUG)["resultado"], "erro")
        self.assertEqual((w.live / "estado").read_text(), "preservar")
        self.assertEqual(w.git(w.live, "rev-parse", "HEAD"), head)

    def test_advance_rejects_swapped_origin_before_fetch(self):
        w = self.w
        head = w.git(w.live, "rev-parse", "HEAD")
        w.git(w.live, "remote", "set-url", "origin", str(w.origin))
        self.assertIsNone(store.live_clone(self.ctx, SLUG))
        self.assertEqual(store.live_advance(self.ctx, SLUG)["resultado"], "erro")
        self.assertEqual(w.git(w.live, "rev-parse", "origin/main"), head)

    def test_advance_rejects_effective_origin_rewritten_to_another_repo(self):
        w = self.w
        before = w.git(w.live, "rev-parse", "origin/main")
        w.git(w.live, "config", f"url.{w.origin}.insteadOf", str(w.remote))
        self.assertEqual(store.live_clone(self.ctx, SLUG), w.live)
        record = store.live_advance(self.ctx, SLUG)
        self.assertEqual(record["resultado"], "erro")
        self.assertIn("origin do clone dedicado", record["detalhe"])
        self.assertEqual(w.git(w.live, "rev-parse", "origin/main"), before)
