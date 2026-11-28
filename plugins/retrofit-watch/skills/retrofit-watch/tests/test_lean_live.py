"""O clone em uso segue a main sem tocar o checkout de desenvolvimento."""
import json
import os
import shlex
import shutil
import time
import subprocess
import sys
import unittest
from unittest import mock

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

    def test_setup_refuses_same_slug_rewrite_before_clone(self):
        w = self.w
        w.live.rename(w.live.with_name("anterior"))
        url = f"https://other.example/{SLUG}.git"
        w.git(w.live.parent, "config", "--file", str(w.home / ".gitconfig"),
              f"url.{url}.insteadOf", str(w.remote))
        run = store.run

        def no_clone(command, **kw):
            self.assertNotIn("clone", command)
            return run(command, **kw)

        with mock.patch.object(store, "run", side_effect=no_clone):
            with self.assertRaisesRegex(store.StoreError, "URL efetiva"):
                store.live_setup(self.ctx, SLUG, str(w.remote))
        self.assertFalse(w.live.exists())

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
        run = store.run

        def no_fetch(command, **kw):
            self.assertNotIn("fetch", command)
            return run(command, **kw)

        for url in (str(w.origin), f"https://other.example/{SLUG}.git"):
            with self.subTest(url=url), mock.patch.object(store, "run", side_effect=no_fetch):
                key = f"url.{url}.insteadOf"
                w.git(w.live, "config", key, str(w.remote))
                try:
                    self.assertEqual(store.live_clone(self.ctx, SLUG), w.live)
                    record = store.live_advance(self.ctx, SLUG)
                    self.assertEqual(record["resultado"], "erro")
                    self.assertIn("origin do clone dedicado", record["detalhe"])
                    self.assertEqual(w.git(w.live, "rev-parse", "origin/main"), before)
                finally:
                    w.git(w.live, "config", "--unset", key)
        extra = w.tmp / "include-origin"
        w.git(w.live, "config", "--file", str(extra), "remote.origin.url", str(w.origin))
        w.git(w.live, "config", "include.path", str(extra))
        self.assertEqual(w.git(w.live, "remote", "get-url", "--all", "origin").splitlines(),
                         [str(w.remote), str(w.origin)])
        with mock.patch.object(store, "run", side_effect=no_fetch):
            record = store.live_advance(self.ctx, SLUG)
        self.assertEqual(record["resultado"], "erro")
        self.assertIn("origin do clone dedicado", record["detalhe"])


class StartupTest(unittest.TestCase):
    def setUp(self):
        self.w = PrivateWorld()
        self.addCleanup(self.w.cleanup)
        self.ctx = self.w.ctx()
        attended = mock.patch.dict("os.environ", RETROFIT_WATCH="force")
        attended.start()
        self.addCleanup(attended.stop)

    def test_spawn_is_detached_and_does_not_wait(self):
        with mock.patch.object(subprocess, "Popen") as launch, mock.patch.object(store, "lean_window"):
            start = time.monotonic()
            store.rw_auto.rw.cmd_pending({}, self.ctx)
            self.assertLess(time.monotonic() - start, 1)
        calls = [call for call in launch.call_args_list if call.args[0][-1] == "live-advance"]
        self.assertEqual(len(calls), 1)
        opts = calls[0].kwargs
        for key in ("stdin", "stdout", "stderr"):
            self.assertEqual(opts[key], subprocess.DEVNULL)
        self.assertEqual(opts["env"]["CLAUDE_PLUGIN_DATA"], str(self.ctx.data_dir))
        self.assertTrue(opts["creationflags"] & subprocess.DETACHED_PROCESS if os.name == "nt"
                        else opts["start_new_session"])
        launch.return_value.wait.assert_not_called()

    def test_no_list_does_not_spawn(self):
        self.w.config(lean_auto=[])
        with mock.patch.object(subprocess, "Popen") as launch:
            self.assertFalse(store.spawn_live_advance(self.w.ctx()))
        launch.assert_not_called()

    def test_offline_advance_is_in_child_and_reported_on_next_startup(self):
        w = self.w
        guard = w.tmp / "liberar"
        wrapper = w.bindir / "git"
        real = shlex.quote(shutil.which("git"))
        wrapper.write_text('#!/bin/sh\n'
                           'for arg in "$@"; do\n'
                           '  if [ "$arg" = fetch ]; then\n'
                           f'    for i in 1 2 3 4 5 6 7 8 9 10; do\n'
                           f'      [ -f {shlex.quote(str(guard))} ] && break\n'
                           '      sleep 0.2\n'
                           '    done\n'
                           '    exit 1\n'
                           '  fi\n'
                           'done\n'
                           f'exec {real} "$@"\n')
        wrapper.chmod(0o755)
        rw = store.rw_auto.rw
        original = subprocess.Popen
        child = []

        def track(cmd, *args, **kwargs):
            proc = original(cmd, *args, **kwargs)
            if cmd[-1] == "live-advance":
                child.append(proc)
                self.addCleanup(proc.wait, timeout=5)
            return proc

        with mock.patch.dict(os.environ, PATH=f"{w.bindir}{os.pathsep}{os.environ['PATH']}"), \
                mock.patch.object(subprocess, "Popen", side_effect=track):
            start = time.monotonic()
            rw.cmd_pending({}, self.ctx)
            self.assertLess(time.monotonic() - start, 1)
        self.assertEqual(len(child), 1)
        self.assertIsNone(child[0].poll())
        guard.touch()
        self.assertEqual(child[0].wait(timeout=5), 1)
        with mock.patch.object(store, "spawn_live_advance", return_value=True):
            notice = rw.cmd_pending({}, self.ctx)
        self.assertIsNotNone(notice, "o startup precisa mostrar a falha gravada no avanço")
        self.assertIn(f"avanço de {SLUG} falhou:", notice["systemMessage"])

    def test_notice_once_per_transition(self):
        modes = [("auto-dry", None), ("auto", None), ("auto", None),
                 ("auto-dry", "2026-11-27"), ("auto-dry", "2026-11-27")]
        with mock.patch.object(store, "lean_mode_state", side_effect=modes):
            notice = store.rw_auto.lean_mode_notice
            self.assertIsNone(notice(self.ctx))
            self.assertIn("fora do ensaio", notice(self.ctx))
            self.assertIsNone(notice(self.ctx))
            self.assertIn("de volta ao ensaio (revert de 2026-11-27)", notice(self.ctx))
            self.assertIsNone(notice(self.ctx))
