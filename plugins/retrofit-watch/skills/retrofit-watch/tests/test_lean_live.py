"""O clone em uso segue a main sem tocar o checkout de desenvolvimento."""
import errno
import io
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

    def test_setup_retry_after_clone_failure(self):
        w = self.w
        previous = w.live.with_name("anterior")
        w.live.rename(previous)
        (previous / "estado").write_text("preservar")
        w.git(w.remote, "branch", "-m", "main", "outro")
        with self.assertRaisesRegex(store.StoreError, "clone .* falhou"):
            store.live_setup(self.ctx, SLUG, str(w.remote))
        w.git(w.remote, "branch", "-m", "outro", "main")
        self.assertEqual(store.live_setup(self.ctx, SLUG, str(w.remote)), w.live)
        self.assertEqual((previous / "estado").read_text(), "preservar")

    def test_setup_retry_after_lock_failure(self):
        w = self.w
        w.live.rename(w.live.with_name("anterior"))
        git = store._git

        for error in (store.StoreError, OSError):
            def fail_lock(args, *rest):
                if "extensions.worktreeConfig" in args:
                    raise error("trava falhou")
                return git(args, *rest)

            with self.subTest(error=error), mock.patch.object(store, "_git", side_effect=fail_lock):
                with self.assertRaisesRegex(error, "trava falhou"):
                    store.live_setup(self.ctx, SLUG, str(w.remote))
                self.assertFalse(w.live.exists())
        self.assertEqual(store.live_setup(self.ctx, SLUG, str(w.remote)), w.live)

    def test_setup_waits_for_the_lock_before_exposing_the_clone(self):
        w = self.w
        w.live.rename(w.live.with_name("anterior"))
        git = store._git

        def observe_lock(args, *rest):
            if "extensions.worktreeConfig" in args:
                self.assertIsNone(store.live_clone(self.ctx, SLUG))
            return git(args, *rest)

        with mock.patch.object(store, "_git", side_effect=observe_lock):
            self.assertEqual(store.live_setup(self.ctx, SLUG, str(w.remote)), w.live)
        self.assertEqual(store.live_clone(self.ctx, SLUG), w.live)

    def test_setup_preserves_a_destination_created_while_cloning(self):
        w = self.w
        w.live.rename(w.live.with_name("anterior"))
        git = store._git
        note = w.live / "nota-local"

        def interrupt_lock(args, *rest):
            if "extensions.worktreeConfig" in args:
                w.live.mkdir(exist_ok=True)
                note.write_text("preservar", encoding="utf-8")
                raise store.StoreError("trava interrompida")
            return git(args, *rest)

        with mock.patch.object(store, "_git", side_effect=interrupt_lock):
            with self.assertRaisesRegex(store.StoreError, "trava interrompida"):
                store.live_setup(self.ctx, SLUG, str(w.remote))
        self.assertTrue(note.is_file())
        self.assertEqual(note.read_text(encoding="utf-8"), "preservar")

    def test_setup_does_not_replace_concurrent_empty_destination(self):
        w = self.w
        w.live.rename(w.live.with_name("anterior"))
        install = store._install_live_clone
        created = []

        def create_before_install(checkout, path):
            path.mkdir()
            created.append(path.stat())
            return install(checkout, path)

        with mock.patch.object(store, "_install_live_clone", side_effect=create_before_install):
            with self.assertRaisesRegex(store.StoreError, "destino já existe"):
                store.live_setup(self.ctx, SLUG, str(w.remote))
        self.assertEqual(len(created), 1)
        self.assertTrue(os.path.samestat(created[0], w.live.stat()))
        self.assertEqual(list(w.live.iterdir()), [])

    def _final_origin_rewrite(self):
        w = self.w
        w.live.rename(w.live.with_name("anterior"))
        config = w.home / "destino.gitconfig"
        w.git(w.tmp, "config", "--file", str(config), f"url.{w.origin}.insteadOf", str(w.remote))
        key = f'includeIf.gitdir:{w.live / ".git"}.path'
        w.git(w.tmp, "config", "--global", key, str(config))
        return key

    def test_setup_checks_effective_origin_at_the_final_path(self):
        self._final_origin_rewrite()
        with self.assertRaisesRegex(store.StoreError, "origin do clone dedicado"):
            store.live_setup(self.ctx, SLUG, str(self.w.remote))
        self.assertIsNone(store.live_clone(self.ctx, SLUG))

    def test_setup_retries_after_final_origin_validation_failure(self):
        w = self.w
        key = self._final_origin_rewrite()
        live_remote = store._live_remote

        def observe_pending(ctx, slug, path, expected):
            if path == w.live:
                self.assertIsNone(store.live_clone(ctx, slug))
            return live_remote(ctx, slug, path, expected)

        with mock.patch.object(store, "_live_remote", side_effect=observe_pending):
            with self.assertRaisesRegex(store.StoreError, "origin do clone dedicado"):
                store.live_setup(self.ctx, SLUG, str(w.remote))
        self.assertIsNone(store.live_clone(self.ctx, SLUG))
        w.git(w.tmp, "config", "--global", "--unset", key)
        self.assertEqual(store.live_setup(self.ctx, SLUG, str(w.remote)), w.live)
        self.assertEqual(store.live_clone(self.ctx, SLUG), w.live)
        w.assert_fixture_origin(w.live)

    def test_setup_retry_keeps_files_after_final_origin_rejection(self):
        w = self.w
        key = self._final_origin_rewrite()
        check_remote = store._live_remote
        note = w.live / "nota-local"

        def add_note_during_validation(ctx, slug, path, expected):
            if path == w.live:
                note.write_text("preservar", encoding="utf-8")
            return check_remote(ctx, slug, path, expected)

        with mock.patch.object(store, "_live_remote", side_effect=add_note_during_validation):
            with self.assertRaisesRegex(store.StoreError, "origin do clone dedicado"):
                store.live_setup(self.ctx, SLUG, str(w.remote))
        self.assertTrue(note.is_file(), "a recusa da origem apagou o arquivo criado durante a validação")
        self.assertIsNone(store.live_clone(self.ctx, SLUG))
        installed = w.live.stat()
        other = w.tmp / "outra-origem" / f"{SLUG}.git"
        with self.assertRaisesRegex(store.StoreError, "destino já existe"):
            store.live_setup(self.ctx, SLUG, str(other))
        w.git(w.tmp, "config", "--global", "--unset", key)
        self.assertEqual(store.live_setup(self.ctx, SLUG, str(w.remote)), w.live)
        self.assertTrue(os.path.samestat(installed, w.live.stat()))
        self.assertEqual(note.read_text(encoding="utf-8"), "preservar")
        self.assertEqual(store.live_clone(self.ctx, SLUG), w.live)

    def test_setup_does_not_finalize_missing_or_replaced_destination(self):
        w = self.w
        w.live.rename(w.live.with_name("anterior"))
        live_remote = store._live_remote
        pending = w.live / ".git" / store.LIVE_SETUP_PENDING

        for change in ("ausente", "outro-clone", "outro-gitdir"):
            moved = w.live.with_name(change)
            seen = []

            def move_after_validation(ctx, slug, path, expected):
                env = live_remote(ctx, slug, path, expected)
                if path == w.live:
                    source = path / ".git" if change == "outro-gitdir" else path
                    seen.append((source.stat(), pending.read_bytes()))
                    source.rename(moved)
                    if change != "ausente":
                        replacement = path / ".git" if change == "outro-gitdir" else path
                        shutil.copytree(moved, replacement)
                return env

            with self.subTest(change=change):
                with mock.patch.object(store, "_live_remote", side_effect=move_after_validation):
                    with self.assertRaisesRegex(store.StoreError, "destino.*mudou"):
                        store.live_setup(self.ctx, SLUG, str(w.remote))
                original_marker = moved / ("" if change == "outro-gitdir" else ".git") / pending.name
                original, contents = seen[0]
                self.assertTrue(os.path.samestat(original, moved.stat()))
                self.assertEqual(original_marker.read_bytes(), contents)
                self.assertIsNone(store.live_clone(self.ctx, SLUG))
                if change == "ausente":
                    self.assertFalse(w.live.exists())
                else:
                    replaced = w.live / ".git" if change == "outro-gitdir" else w.live
                    self.assertFalse(os.path.samestat(original, replaced.stat()))
                    self.assertEqual(pending.read_bytes(), contents)
            if w.live.exists():
                w.live.rename(w.live.with_name(change + "-substituto"))

    def _leave_pending_setup(self):
        w = self.w
        key = self._final_origin_rewrite()
        with self.assertRaisesRegex(store.StoreError, "origin do clone dedicado"):
            store.live_setup(self.ctx, SLUG, str(w.remote))
        w.git(w.tmp, "config", "--global", "--unset", key)
        return w.live / ".git" / store.LIVE_SETUP_PENDING

    def test_setup_retry_refuses_clone_replaced_after_pending_check(self):
        w = self.w
        pending = self._leave_pending_setup()
        moved = w.live.with_name("deslocado")
        contents = pending.read_bytes()
        check = store._pending_live_setup

        def replace_after_check(*args):
            matches = check(*args)
            self.assertTrue(matches)
            w.live.rename(moved)
            shutil.copytree(moved, w.live)
            return matches

        with mock.patch.object(store, "_pending_live_setup", side_effect=replace_after_check):
            with self.assertRaisesRegex(store.StoreError, "destino.*mudou"):
                store.live_setup(self.ctx, SLUG, str(w.remote))
        self.assertEqual(pending.read_bytes(), contents)
        self.assertFalse(os.path.samestat(w.live.stat(), moved.stat()))

    def test_setup_refuses_clone_replaced_just_after_install(self):
        w = self.w
        w.live.rename(w.live.with_name("anterior"))
        moved = w.live.with_name("deslocado")
        install = store._install_live_clone

        def replace_after_install(checkout, path):
            install(checkout, path)
            path.rename(moved)
            shutil.copytree(moved, path, ignore=shutil.ignore_patterns(".git"))
            (moved / ".git").rename(path / ".git")

        with mock.patch.object(store, "_install_live_clone", side_effect=replace_after_install):
            with self.assertRaisesRegex(store.StoreError, "destino.*mudou"):
                store.live_setup(self.ctx, SLUG, str(w.remote))
        marker = ".git/" + store.LIVE_SETUP_PENDING
        self.assertTrue((w.live / marker).is_file())
        self.assertFalse(os.path.samestat(w.live.stat(), moved.stat()))

    def test_setup_does_not_accept_disappearing_marker(self):
        w = self.w
        pending = self._leave_pending_setup()
        live_remote = store._live_remote

        def remove_after_validation(*args):
            env = live_remote(*args)
            pending.unlink()
            return env

        with mock.patch.object(store, "_live_remote", side_effect=remove_after_validation):
            with self.assertRaises(FileNotFoundError):
                store.live_setup(self.ctx, SLUG, str(w.remote))

    @unittest.skipIf(os.name == "nt", "Remoção por descritor de diretório no POSIX")
    def test_setup_leaves_replacement_pending_at_marker_removal(self):
        w = self.w
        pending = self._leave_pending_setup()
        contents = pending.read_bytes()
        open_dir, unlink = os.open, os.unlink

        for boundary in ("abertura", "remoção"):
            moved = w.live.with_name(boundary)
            descriptors = []

            def replace():
                w.live.rename(moved)
                shutil.copytree(moved, w.live)

            def open_after_swap(path, *args, **kwargs):
                if boundary == "abertura" and path == pending.parent:
                    replace()
                fd = open_dir(path, *args, **kwargs)
                if path == pending.parent:
                    descriptors.append(fd)
                return fd

            def unlink_after_swap(path, *args, **kwargs):
                if boundary == "remoção" and path in (pending, pending.name):
                    replace()
                return unlink(path, *args, **kwargs)

            with self.subTest(boundary=boundary), \
                    mock.patch.object(os, "open", side_effect=open_after_swap), \
                    mock.patch.object(os, "unlink", side_effect=unlink_after_swap):
                with self.assertRaisesRegex(store.StoreError, "destino.*mudou"):
                    store.live_setup(self.ctx, SLUG, str(w.remote))
                self.assertFalse(os.path.samestat(w.live.stat(), moved.stat()))
                self.assertEqual(pending.read_bytes(), contents)
                if boundary == "abertura":
                    self.assertEqual((moved / ".git" / pending.name).read_bytes(), contents)
                self.assertEqual(len(descriptors), 1)
                with self.assertRaises(OSError):
                    os.fstat(descriptors[0])

    def test_setup_path_removal_fallback_requires_marker(self):
        pending = self._leave_pending_setup()
        path = self.w.live
        identity = store._live_setup_identity(path)
        origin_id = pending.read_bytes()
        with mock.patch.object(store.os, "name", "nt"):
            store._finish_live_setup(path, pending, identity, origin_id)
            with self.assertRaises(FileNotFoundError):
                store._finish_live_setup(path, pending, identity, origin_id)
        self.assertEqual(store.live_clone(self.ctx, SLUG), path)

    @unittest.skipIf(os.name == "nt", "Abertura de diretório sem seguir links no POSIX")
    def test_setup_does_not_follow_gitdir_link_at_marker_removal(self):
        pending = self._leave_pending_setup()
        moved = self.w.live.with_name("gitdir-deslocado")
        contents = pending.read_bytes()
        open_dir = os.open

        def open_after_link(path, *args, **kwargs):
            if path == pending.parent:
                pending.parent.rename(moved)
                pending.parent.symlink_to(moved, target_is_directory=True)
            return open_dir(path, *args, **kwargs)

        with mock.patch.object(os, "open", side_effect=open_after_link):
            with self.assertRaises(OSError):
                store.live_setup(self.ctx, SLUG, str(self.w.remote))
        self.assertEqual((moved / pending.name).read_bytes(), contents)

    def test_setup_retry_requires_declared_and_effective_origin(self):
        w = self.w
        pending = self._leave_pending_setup()
        previous = pending.read_bytes()
        alias = f"https://alias.example/{SLUG}.git"
        w.git(w.live, "remote", "set-url", "origin", alias)
        w.git(w.tmp, "config", "--global", f"url.{w.remote}.insteadOf", alias)
        self.assertEqual(w.git(w.live, "remote", "get-url", "origin"), str(w.remote))

        refused = self.cli("live-setup", SLUG, "--url", str(w.remote))
        self.assertEqual(refused.returncode, 1, refused.stdout)
        self.assertIn("origem declarada", refused.stderr)
        self.assertEqual(pending.read_bytes(), previous)
        self.assertIsNone(store.live_clone(self.ctx, SLUG))
        w.git(w.live, "remote", "set-url", "origin", str(w.remote))
        self.assertEqual(store.live_setup(self.ctx, SLUG, str(w.remote)), w.live)
        self.assertEqual(store.live_clone(self.ctx, SLUG, origin=store.rw_auto.rw.origin_identity(str(w.remote))),
                         w.live)

    def test_setup_retry_does_not_finalize_wrong_branch(self):
        w = self.w
        pending = self._leave_pending_setup()
        w.git(w.live, "switch", "-qc", "rascunho")
        note = w.live / "nota-local"
        note.write_text("preservar", encoding="utf-8")
        head = w.git(w.live, "rev-parse", "HEAD")

        refused = self.cli("live-setup", SLUG, "--url", str(w.remote))
        self.assertEqual(refused.returncode, 1, refused.stdout)
        self.assertIn("main", refused.stderr)
        self.assertEqual(w.git(w.live, "branch", "--show-current"), "rascunho")
        self.assertEqual(w.git(w.live, "rev-parse", "HEAD"), head)
        self.assertEqual(note.read_text(encoding="utf-8"), "preservar")
        self.assertTrue(pending.is_file())
        self.assertIsNone(store.live_clone(self.ctx, SLUG))
        w.git(w.live, "switch", "-q", "main")
        self.assertEqual(store.live_setup(self.ctx, SLUG, str(w.remote)), w.live)

    def test_setup_and_eligibility_agree_on_symbolic_main(self):
        w = self.w
        pending = self._leave_pending_setup()
        marker = pending.read_bytes()
        head = w.git(w.live, "rev-parse", "HEAD")
        w.git(w.live, "symbolic-ref", "refs/heads/atalho", "refs/heads/main")
        w.git(w.live, "symbolic-ref", "HEAD", "refs/heads/atalho")
        self.assertEqual(w.git(w.live, "symbolic-ref", "HEAD"), "refs/heads/main")
        self.assertIsNone(store.live_clone(self.ctx, SLUG))

        with self.assertRaisesRegex(store.StoreError, "HEAD.*diretamente.*main"):
            store.live_setup(self.ctx, SLUG, str(w.remote))
        self.assertEqual(pending.read_bytes(), marker)
        self.assertIsNone(store.live_clone(self.ctx, SLUG))
        self.assertEqual(w.git(w.live, "rev-parse", "HEAD"), head)
        self.assertEqual(w.git(w.live, "symbolic-ref", "--no-recurse", "HEAD"), "refs/heads/atalho")

        w.git(w.live, "symbolic-ref", "HEAD", "refs/heads/main")
        self.assertEqual(store.live_setup(self.ctx, SLUG, str(w.remote)), w.live)
        self.assertFalse(pending.exists())
        self.assertEqual(store.live_clone(self.ctx, SLUG), w.live)
        self.assertEqual(store.live_advance(self.ctx, SLUG)["resultado"], "ok")

    def test_setup_rejects_main_resolving_to_other_branch(self):
        w = self.w
        pending = self._leave_pending_setup()
        marker = pending.read_bytes()
        head_file = pending.with_name("HEAD")
        head_bytes = head_file.read_bytes()
        head = w.git(w.live, "rev-parse", "HEAD")
        w.git(w.live, "branch", "rascunho")
        main_ref = pending.parent / "refs/heads/main"

        def assert_refused():
            self.assertEqual(head_file.read_bytes(), head_bytes)
            self.assertEqual(w.git(w.live, "symbolic-ref", "HEAD"), "refs/heads/rascunho")
            with self.assertRaisesRegex(store.StoreError, "fora da main"):
                store.live_setup(self.ctx, SLUG, str(w.remote))
            self.assertEqual(pending.read_bytes(), marker)
            self.assertIsNone(store.live_clone(self.ctx, SLUG))
            # O ramo também impede a elegibilidade quando o marcador deixa de estar visível.
            pending.unlink()
            try:
                self.assertIsNone(store.live_clone(self.ctx, SLUG))
            finally:
                pending.write_bytes(marker)

        w.git(w.live, "symbolic-ref", "refs/heads/main", "refs/heads/rascunho")
        assert_refused()
        if os.name != "nt":
            main_ref.unlink()
            main_ref.symlink_to("refs/heads/rascunho")
            assert_refused()
        main_ref.unlink()
        w.git(w.live, "update-ref", "refs/heads/main", head)
        w.git(w.live, "pack-refs", "--all")
        self.assertFalse(main_ref.exists())
        self.assertEqual(store.live_setup(self.ctx, SLUG, str(w.remote)), w.live)
        self.assertFalse(pending.exists())
        self.assertEqual(store.live_clone(self.ctx, SLUG), w.live)
        self.assertEqual(store.live_advance(self.ctx, SLUG)["resultado"], "ok")

    def test_setup_keeps_pending_when_main_redirects_during_validation(self):
        w = self.w
        pending = self._leave_pending_setup()
        marker = pending.read_bytes()
        head_file = pending.with_name("HEAD")
        head_bytes = head_file.read_bytes()
        main_ref = pending.parent / "refs/heads/main"
        direct_ref = main_ref.read_bytes()
        local = w.live / "estado-local.txt"
        local.write_bytes(b"preservar")
        w.git(w.live, "branch", "rascunho")
        read_git = store._git
        unlink = os.unlink

        def redirect():
            w.git(w.live, "symbolic-ref", "refs/heads/main", "refs/heads/rascunho")

        def redirect_during_hooks(args, cwd, env, label):
            if args[-1] == "core.hooksPath":
                redirect()
            return read_git(args, cwd, env, label)

        observed = []

        def redirect_at_removal(name, *args, **kwargs):
            if name in (pending, pending.name):
                if moment == "remoção":
                    redirect()
                unlink(name, *args, **kwargs)
                observed.append(store.live_clone(self.ctx, SLUG))
                return
            return unlink(name, *args, **kwargs)

        for moment in ("trava", "remoção"):
            with self.subTest(moment=moment):
                git = redirect_during_hooks if moment == "trava" else read_git
                try:
                    with mock.patch.object(store, "_git", side_effect=git), \
                            mock.patch.object(os, "unlink", side_effect=redirect_at_removal), \
                            self.assertRaisesRegex(store.StoreError, "ramo.*mudou"):
                        store.live_setup(self.ctx, SLUG, str(w.remote))
                    self.assertEqual(pending.read_bytes(), marker)
                    self.assertEqual(local.read_bytes(), b"preservar")
                    self.assertEqual(head_file.read_bytes(), head_bytes)
                    self.assertEqual(w.git(w.live, "symbolic-ref", "HEAD"), "refs/heads/rascunho")
                    self.assertIsNone(store.live_clone(self.ctx, SLUG))
                finally:
                    main_ref.write_bytes(direct_ref)
                    if not pending.exists():
                        pending.write_bytes(marker)
        self.assertEqual(observed, [None])
        self.assertEqual(store.live_setup(self.ctx, SLUG, str(w.remote)), w.live)
        self.assertFalse(pending.exists())
        self.assertEqual(local.read_bytes(), b"preservar")

    def test_setup_and_advance_accept_packed_main_with_empty_loose_dir(self):
        w = self.w
        pending = self._leave_pending_setup()
        head = w.git(w.live, "rev-parse", "--verify", "HEAD")
        w.git(w.live, "pack-refs", "--all")
        main_ref = pending.parent / "refs/heads/main"
        if os.name != "nt":
            main_ref.symlink_to("refs/heads/rascunho")
            with self.assertRaisesRegex(store.StoreError, "fora da main"):
                store.live_setup(self.ctx, SLUG, str(w.remote))
            self.assertTrue(pending.exists())
            main_ref.unlink()
        main_ref.mkdir()
        self.assertEqual(w.git(w.live, "rev-parse", "--verify", "HEAD"), head)
        self.assertEqual(store.live_setup(self.ctx, SLUG, str(w.remote)), w.live)
        self.assertFalse(pending.exists())
        self.assertEqual(store.live_clone(self.ctx, SLUG), w.live)
        new_head = w.commit_on_origin({"README.md": "nova revisão"}, "Avança o bare")
        record = store.live_advance(self.ctx, SLUG)
        self.assertEqual((record["resultado"], record["antes"], record["depois"]), ("ok", head, new_head))
        self.assertEqual(w.git(w.live, "rev-parse", "HEAD"), new_head)

    def test_live_main_ref_checks_packed_ref_after_loose_file_disappears(self):
        w = self.w
        main_ref = w.live / ".git" / "refs" / "heads" / "main"
        loose_stat = main_ref.lstat()
        w.git(w.live, "pack-refs", "--all")
        self.assertFalse(main_ref.exists())

        lstat = type(main_ref).lstat

        def previous_stat(path):
            if path == main_ref:
                return loose_stat
            return lstat(path)

        with mock.patch.object(type(main_ref), "lstat", previous_stat):
            self.assertTrue(store._live_main_ref(w.live))

    def test_setup_finalization_rechecks_identity_after_reading_main(self):
        w = self.w
        pending = self._leave_pending_setup()
        origin_id = pending.read_bytes()
        identity = store._live_setup_identity(w.live)
        head = identity[2]
        changed = (*identity[:2], (*head[:-1], head[-1] + 1))

        with mock.patch.object(store, "_live_setup_identity", side_effect=[identity, changed]), \
                mock.patch.object(store, "_live_main_ref", return_value=True), \
                self.assertRaisesRegex(store.StoreError, "ramo.*mudou"):
            store._verify_live_setup_finalization(w.live, pending, identity, origin_id)

        self.assertEqual(pending.read_bytes(), origin_id)

    def test_setup_rejects_missing_main_ref(self):
        w = self.w
        pending = self._leave_pending_setup()
        marker = pending.read_bytes()
        w.git(w.live, "branch", "main-extra")
        w.git(w.live, "pack-refs", "--all")
        w.git(w.live, "update-ref", "-d", "refs/heads/main")
        packed = pending.parent / "packed-refs"
        self.assertIn(b" refs/heads/main-extra\n", packed.read_bytes())
        self.assertEqual(w.git(w.live, "symbolic-ref", "HEAD"), "refs/heads/main")
        self.assertNotEqual(subprocess.run(
            ["git", "rev-parse", "--verify", "HEAD"], cwd=w.live, env=w.env,
            capture_output=True).returncode, 0)
        for state in ("outras refs empacotadas", "ref solta sem SHA",
                      "ref empacotada sem SHA", "sem tabela empacotada"):
            with self.subTest(state=state):
                main_ref = pending.parent / "refs/heads/main"
                if state == "ref solta sem SHA":
                    main_ref.write_bytes(b"sem-sha\n")
                elif state == "ref empacotada sem SHA":
                    with packed.open("ab") as refs:
                        refs.write(b"sem-sha refs/heads/main\n")
                elif state == "sem tabela empacotada":
                    packed.unlink()
                try:
                    if state != "ref empacotada sem SHA":
                        reason = "main do clone ilegível" if state == "ref solta sem SHA" else "fora da main"
                        with self.assertRaisesRegex(store.StoreError, reason):
                            store.live_setup(self.ctx, SLUG, str(w.remote))
                    self.assertEqual(pending.read_bytes(), marker)
                    pending.unlink()
                    self.assertIsNone(store.live_clone(self.ctx, SLUG))
                finally:
                    pending.write_bytes(marker)
                    main_ref.unlink(missing_ok=True)

    def test_live_clone_accepts_whitespace_in_loose_ref_when_git_resolves_it(self):
        w = self.w
        ref = w.live / ".git" / "refs/heads/main"
        before = w.git(w.live, "rev-parse", "--verify", "HEAD")
        ref.write_bytes(ref.read_bytes().rstrip() + b" \n")

        self.assertEqual(w.git(w.live, "rev-parse", "--verify", "HEAD"), before)
        self.assertEqual(store.live_clone(self.ctx, SLUG), w.live)

    def test_live_main_confirms_head_after_git_ref_query(self):
        path = self.w.live
        head = path / ".git" / "HEAD"
        states = iter((b"ref: refs/heads/main\n", b"ref: refs/heads/rascunho\n"))
        open_path = type(head).open

        def read_head(current, *args, **kwargs):
            if current == head:
                return io.BytesIO(next(states))
            return open_path(current, *args, **kwargs)

        with mock.patch.object(type(head), "open", read_head):
            self.assertFalse(store._live_main(path))

    def test_setup_finalization_distinguishes_unavailable_main_ref(self):
        path = self.w.live
        pending = self._leave_pending_setup()
        origin_id = pending.read_bytes()
        identity = store._live_setup_identity(path)

        with mock.patch.object(store, "_live_main_ref", return_value=None):
            with self.assertRaisesRegex(store.StoreError, "main do clone ilegível"):
                store._finish_live_setup(path, pending, identity, origin_id)
            self.assertEqual(pending.read_bytes(), origin_id)

            pending.unlink()
            with self.assertRaisesRegex(store.StoreError, "main do clone ilegível"):
                store._verify_live_setup_finalization(path, pending, identity, origin_id)
            self.assertEqual(pending.read_bytes(), origin_id)

    def test_live_main_accepts_sha256_loose_and_packed_refs(self):
        w = self.w
        repo = w.tmp / "sha256"
        w.git(w.tmp, "init", "-q", "--object-format=sha256", "-b", "main", str(repo))
        w.git(repo, "commit", "--allow-empty", "-qm", "Cria a main em SHA-256")
        self.assertEqual(w.git(repo, "rev-parse", "--show-object-format"), "sha256")
        self.assertTrue(store._live_main(repo))
        w.git(repo, "pack-refs", "--all")
        self.assertFalse((repo / ".git" / "refs/heads/main").exists())
        self.assertTrue(store._live_main(repo))

    def test_setup_retry_does_not_finalize_branch_changed_during_validation(self):
        w = self.w
        pending = self._leave_pending_setup()
        content = pending.read_bytes()
        check_origin = store._live_remote

        def switch_after_origin_check(ctx, slug, path, expected):
            env = check_origin(ctx, slug, path, expected)
            w.git(path, "switch", "-qc", "rascunho")
            return env

        with mock.patch.object(store, "_live_remote", side_effect=switch_after_origin_check):
            with self.assertRaisesRegex(store.StoreError, "fora da main"):
                store.live_setup(self.ctx, SLUG, str(w.remote))
        self.assertEqual(pending.read_bytes(), content)
        self.assertIsNone(store.live_clone(self.ctx, SLUG))
        w.git(w.live, "switch", "-q", "main")
        self.assertEqual(store.live_setup(self.ctx, SLUG, str(w.remote)), w.live)

    def test_setup_retry_rejects_hooks_path_with_trailing_space(self):
        w = self.w
        pending = self._leave_pending_setup()
        hooks_path = str(pending.parent / "rw-live-hooks")
        w.git(w.live, "config", "--worktree", "core.hooksPath", hooks_path + " ")
        with self.assertRaisesRegex(store.StoreError, "trava de commit"):
            store.live_setup(self.ctx, SLUG, str(w.remote))
        self.assertTrue(pending.is_file())
        self.assertIsNone(store.live_clone(self.ctx, SLUG))
        w.git(w.live, "config", "--worktree", "--unset", "core.hooksPath")
        self.assertEqual(store.live_setup(self.ctx, SLUG, str(w.remote)), w.live)

    def test_setup_does_not_finalize_branch_changed_while_reading_hooks(self):
        w = self.w
        pending = self._leave_pending_setup()
        read_git = store._git

        def switch_before_hooks(args, cwd, env, label):
            if args[0] == "config" and args[-1] == "core.hooksPath":
                w.git(cwd, "switch", "-qc", "rascunho")
            return read_git(args, cwd, env, label)

        with mock.patch.object(store, "_git", side_effect=switch_before_hooks):
            with self.assertRaisesRegex(store.StoreError, "ramo.*mudou"):
                store.live_setup(self.ctx, SLUG, str(w.remote))
        self.assertTrue(pending.is_file())
        self.assertIsNone(store.live_clone(self.ctx, SLUG))

    def test_setup_does_not_finalize_origin_verified_on_another_branch(self):
        w = self.w
        pending = self._leave_pending_setup()
        w.git(w.live, "switch", "-qc", "rascunho")
        config = w.home / "main.gitconfig"
        w.git(w.tmp, "config", "--file", str(config), f"url.{w.origin}.insteadOf", str(w.remote))
        key = "includeIf.onbranch:main.path"
        w.git(w.tmp, "config", "--global", key, str(config))
        check_origin = store._live_remote

        def switch_after_origin_check(ctx, slug, path, expected):
            env = check_origin(ctx, slug, path, expected)
            w.git(path, "switch", "-q", "main")
            return env

        with mock.patch.object(store, "_live_remote", side_effect=switch_after_origin_check):
            with self.assertRaisesRegex(store.StoreError, "ramo.*mudou"):
                store.live_setup(self.ctx, SLUG, str(w.remote))
        self.assertTrue(pending.is_file())
        self.assertIsNone(store.live_clone(self.ctx, SLUG))
        w.git(w.tmp, "config", "--global", "--unset", key)
        self.assertEqual(store.live_setup(self.ctx, SLUG, str(w.remote)), w.live)

    @unittest.skipIf(os.name == "nt", "Remoção por descritor de diretório no POSIX")
    def test_setup_keeps_pending_if_branch_changes_at_marker_removal(self):
        w = self.w
        pending = self._leave_pending_setup()
        expected = pending.read_bytes()
        unlink = os.unlink

        def switch_at_removal(name, *args, **kwargs):
            if name == pending.name and kwargs.get("dir_fd") is not None:
                w.git(w.live, "switch", "-qc", "rascunho")
            return unlink(name, *args, **kwargs)

        with mock.patch.object(os, "unlink", side_effect=switch_at_removal):
            with self.assertRaises(store.StoreError):
                store.live_setup(self.ctx, SLUG, str(w.remote))
        self.assertTrue(pending.is_file())
        self.assertEqual(pending.read_bytes(), expected)
        self.assertIsNone(store.live_clone(self.ctx, SLUG))

    def test_setup_stays_ineligible_during_branch_change_at_marker_removal(self):
        w = self.w
        pending = self._leave_pending_setup()
        expected = pending.read_bytes()
        observed = []
        unlink = os.unlink

        def observe_removal(name, *args, **kwargs):
            if name not in (pending, pending.name):
                return unlink(name, *args, **kwargs)
            w.git(w.live, "switch", "-qc", "rascunho")
            unlink(name, *args, **kwargs)
            observed.append((pending.exists(), store.live_clone(self.ctx, SLUG)))

        self.assertIsNone(store.live_clone(self.ctx, SLUG))
        with mock.patch.object(os, "unlink", side_effect=observe_removal):
            with self.assertRaisesRegex(store.StoreError, "ramo.*mudou"):
                store.live_setup(self.ctx, SLUG, str(w.remote))
        self.assertEqual(pending.read_bytes(), expected)
        self.assertIsNone(store.live_clone(self.ctx, SLUG))
        self.assertEqual(observed, [(False, None)])
        w.git(w.live, "switch", "-q", "main")
        self.assertEqual(store.live_setup(self.ctx, SLUG, str(w.remote)), w.live)
        self.assertEqual(store.live_clone(self.ctx, SLUG), w.live)

    def test_setup_rejects_hook_change_during_branch_validation(self):
        w = self.w
        pending = self._leave_pending_setup()
        expected = pending.read_bytes()
        empty_hooks = w.tmp / "hooks-vazios"
        empty_hooks.mkdir()
        read_main = store._live_main
        read_git = store._git

        def change_hook_on_branch_query(path):
            w.git(path, "config", "--worktree", "core.hooksPath", str(empty_hooks))
            return read_main(path)

        with mock.patch.object(store, "_live_main", side_effect=change_hook_on_branch_query):
            with self.assertRaisesRegex(store.StoreError, "trava de commit"):
                store.live_setup(self.ctx, SLUG, str(w.remote))
        self.assertEqual(w.git(w.live, "config", "--get", "core.hooksPath"), str(empty_hooks))
        self.assertEqual(pending.read_bytes(), expected)
        self.assertIsNone(store.live_clone(self.ctx, SLUG))
        w.git(w.live, "config", "--worktree", "--unset", "core.hooksPath")
        checked_hooks = False

        def track_hook_verification(args, cwd, env, label):
            nonlocal checked_hooks
            result = read_git(args, cwd, env, label)
            if args[-1] == "core.hooksPath":
                checked_hooks = True
            return result

        def change_hook_only_after_verification(path):
            if checked_hooks:
                w.git(path, "config", "--worktree", "core.hooksPath", str(empty_hooks))
            return read_main(path)

        with mock.patch.object(store, "_git", side_effect=track_hook_verification), \
                mock.patch.object(store, "_live_main", side_effect=change_hook_only_after_verification):
            self.assertEqual(store.live_setup(self.ctx, SLUG, str(w.remote)), w.live)
        hook_dir = pending.parent / "rw-live-hooks"
        self.assertEqual(w.git(w.live, "config", "--get", "core.hooksPath"), str(hook_dir))
        self.assertEqual(store.live_clone(self.ctx, SLUG), w.live)

    def test_live_clone_requires_readable_main(self):
        head = self.w.live / ".git" / "HEAD"
        head.write_bytes(b"ref: refs/heads/main\r\n")
        self.assertEqual(store.live_clone(self.ctx, SLUG), self.w.live)
        open_path = type(head).open

        def unreadable(path, *args, **kwargs):
            if path == head:
                raise PermissionError("HEAD ilegível")
            return open_path(path, *args, **kwargs)

        with mock.patch.object(type(head), "open", unreadable):
            self.assertIsNone(store.live_clone(self.ctx, SLUG))
            with self.assertRaisesRegex(store.StoreError, "sem clone dedicado"):
                store._private_clone(self.ctx, SLUG)

    def test_setup_retry_requires_effective_worktree_lock(self):
        w = self.w
        pending = self._leave_pending_setup()
        config = pending.with_name("rw-live.config")
        hidden = config.with_suffix(".oculta")
        hook = pending.parent / "rw-live-hooks" / "pre-commit"
        original = hook.read_bytes()
        contents = pending.read_bytes()
        note = w.live / "nota-local"
        note.write_text("preservar", encoding="utf-8")

        def assert_refused():
            refused = self.cli("live-setup", SLUG, "--url", str(w.remote))
            try:
                self.assertEqual(refused.returncode, 1, refused.stdout)
                self.assertIn("trava", refused.stderr)
                self.assertEqual(pending.read_bytes(), contents)
                self.assertIsNone(store.live_clone(self.ctx, SLUG))
                self.assertEqual(note.read_text(encoding="utf-8"), "preservar")
            finally:
                if not pending.is_file():
                    pending.write_bytes(contents)

        with self.subTest(lock="inclusão ausente"):
            config.rename(hidden)
            try:
                assert_refused()
            finally:
                hidden.rename(config)
        with self.subTest(lock="caminho incorreto"):
            w.git(w.live, "config", "--worktree", "core.hooksPath", ".githooks")
            try:
                assert_refused()
            finally:
                w.git(w.live, "config", "--worktree", "--unset", "core.hooksPath")
        with self.subTest(lock="escopo comum"):
            config.rename(hidden)
            w.git(w.live, "config", "--local", "core.hooksPath", str(hook.parent))
            try:
                assert_refused()
            finally:
                w.git(w.live, "config", "--local", "--unset", "core.hooksPath")
                hidden.rename(config)
        with self.subTest(lock="hook permissivo"):
            hook.write_bytes(b"#!/bin/sh\nexit 0\n")
            try:
                assert_refused()
            finally:
                hook.write_bytes(original)
        with self.subTest(lock="hook ausente"):
            hook.rename(hidden)
            try:
                assert_refused()
            finally:
                hidden.rename(hook)
        with self.subTest(lock="diretório no lugar do hook"):
            hook.rename(hidden)
            hook.mkdir()
            try:
                assert_refused()
            finally:
                hook.rmdir()
                hidden.rename(hook)
        if os.name != "nt":
            with self.subTest(lock="hook sem execução"):
                hook.chmod(0o644)
                try:
                    assert_refused()
                finally:
                    hook.chmod(0o755)
        self.assertEqual(store.live_setup(self.ctx, SLUG, str(w.remote)), w.live)
        with self.assertRaises(subprocess.CalledProcessError) as denied:
            w.git(w.live, "commit", "--allow-empty", "-m", "Bloqueado")
        self.assertIn("worktree do lote", denied.exception.stderr)
        self.assertEqual(note.read_text(encoding="utf-8"), "preservar")

    def test_setup_preserves_replacement_on_final_validation_failure(self):
        w = self.w
        w.live.rename(w.live.with_name("anterior"))
        live_remote = store._live_remote
        note = w.live / "nota-local"

        def replace_before_failure(ctx, slug, path, expected):
            if path == w.live:
                path.rename(path.with_name("deslocado"))
                path.mkdir()
                note.write_text("preservar", encoding="utf-8")
                raise store.StoreError("origem recusada após a troca")
            return live_remote(ctx, slug, path, expected)

        with mock.patch.object(store, "_live_remote", side_effect=replace_before_failure):
            with self.assertRaisesRegex(store.StoreError, "origem recusada após a troca"):
                store.live_setup(self.ctx, SLUG, str(w.remote))
        self.assertEqual(note.read_text(encoding="utf-8"), "preservar")

    def test_setup_reports_install_error_without_leaving_destination(self):
        w = self.w
        w.live.rename(w.live.with_name("anterior"))
        error = OSError(errno.EOPNOTSUPP, "sem suporte no sistema de arquivos")
        with mock.patch.object(store, "_install_live_clone", side_effect=error):
            with self.assertRaisesRegex(store.StoreError, "instalação do clone.*sem suporte"):
                store.live_setup(self.ctx, SLUG, str(w.remote))
        self.assertFalse(w.live.exists())
        self.assertEqual(store.live_setup(self.ctx, SLUG, str(w.remote)), w.live)

    def test_setup_retries_after_pending_marker_removal_fails(self):
        w = self.w
        w.live.rename(w.live.with_name("anterior"))
        marker = w.live / ".git" / store.LIVE_SETUP_PENDING
        unlink = os.unlink

        def fail_final_unlink(path, *args, **kwargs):
            if path in (marker, marker.name):
                self.assertIsNone(store.live_clone(self.ctx, SLUG))
                raise PermissionError("marcador ocupado")
            return unlink(path, *args, **kwargs)

        with mock.patch.object(os, "unlink", new=fail_final_unlink):
            with self.assertRaisesRegex(PermissionError, "marcador ocupado"):
                store.live_setup(self.ctx, SLUG, str(w.remote))
        self.assertEqual(store.live_setup(self.ctx, SLUG, str(w.remote)), w.live)
        self.assertEqual(store.live_clone(self.ctx, SLUG), w.live)

    def test_setup_keeps_original_error_when_installed_path_disappears(self):
        w = self.w
        w.live.rename(w.live.with_name("anterior"))
        live_remote = store._live_remote

        def move_before_failure(ctx, slug, path, expected):
            if path == w.live:
                path.rename(path.with_name("deslocado"))
                raise store.StoreError("origem recusada após a mudança")
            return live_remote(ctx, slug, path, expected)

        with mock.patch.object(store, "_live_remote", side_effect=move_before_failure):
            with self.assertRaisesRegex(store.StoreError, "origem recusada após a mudança"):
                store.live_setup(self.ctx, SLUG, str(w.remote))
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
        w.git(w.live, "tag", "main")
        (w.live / ".git/info/exclude").write_text("estado\n")
        (w.live / "estado").write_text("preservar")
        new = w.commit_on_origin({"README.md": "nova revisão"}, "Avança o bare")
        result = self.cli("live-advance")
        self.assertEqual(result.returncode, 0, result.stderr)
        record = json.loads((w.data / f"live/{SLUG}.json").read_text())
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

    def test_advance_reports_branch_change_before_fetch(self):
        w = self.w
        head = w.git(w.live, "rev-parse", "HEAD")
        remote_head = w.git(w.live, "rev-parse", "origin/main")
        w.commit_on_origin({"README.md": "nova revisão"}, "Avança o bare")
        obstruction = store._live_obstruction
        run = store.run
        switched = False

        def switch_after_inspection(path, env):
            nonlocal switched
            result = obstruction(path, env)
            if not switched and result is None:
                w.git(path, "switch", "-qc", "rascunho")
                switched = True
            return result

        with mock.patch.object(store, "_live_obstruction", side_effect=switch_after_inspection), \
                mock.patch.object(store, "run", wraps=run) as commands:
            record = store.live_advance(self.ctx, SLUG)

        self.assertTrue(switched)
        self.assertFalse(any("fetch" in call.args[0] for call in commands.call_args_list))
        self.assertEqual((record["resultado"], record["detalhe"]),
                         ("fora-da-main", "cópia em uso fora da main"))
        self.assertEqual((record["antes"], record["depois"]), (head, head))
        self.assertEqual(json.loads((w.data / f"live/{SLUG}.json").read_text()), record)
        self.assertEqual(w.git(w.live, "branch", "--show-current"), "rascunho")
        for ref in ("HEAD", "main", "rascunho"):
            self.assertEqual(w.git(w.live, "rev-parse", ref), head)
        self.assertEqual(w.git(w.live, "rev-parse", "origin/main"), remote_head)

        # Os outros chamadores tratam a recusa da busca como StoreError.
        with self.assertRaisesRegex(store.StoreError, "fora da main"):
            store._live_fetch(self.ctx, SLUG, w.live)

    def test_advance_reports_unreadable_head_before_fetch(self):
        w = self.w
        head = w.git(w.live, "rev-parse", "HEAD")
        remote_head = w.git(w.live, "rev-parse", "origin/main")
        w.commit_on_origin({"README.md": "nova revisão"}, "Avança o bare")
        head_file = w.live / ".git" / "HEAD"
        head_bytes = head_file.read_bytes()
        open_path = type(head_file).open
        obstruction = store._live_obstruction
        read_failed = False
        inspected = False

        def after_inspection(path, env):
            nonlocal inspected
            result = obstruction(path, env)
            inspected = result is None
            return result

        def unreadable(path, *args, **kwargs):
            nonlocal read_failed
            if inspected and path == head_file:
                read_failed = True
                raise PermissionError("falha de leitura simulada")
            return open_path(path, *args, **kwargs)

        with mock.patch.object(store, "_live_obstruction", side_effect=after_inspection), \
                mock.patch.object(type(head_file), "open", unreadable), \
                mock.patch.object(store, "run", wraps=store.run) as commands:
            record = store.live_advance(self.ctx, SLUG)

        self.assertTrue(read_failed)
        self.assertFalse(any("fetch" in call.args[0] for call in commands.call_args_list))
        self.assertEqual((record["resultado"], record["detalhe"]), ("erro", "HEAD do clone ilegível"))
        self.assertEqual((record["antes"], record["depois"]), (head, head))
        self.assertEqual(json.loads((w.data / f"live/{SLUG}.json").read_text()), record)
        self.assertEqual(head_file.read_bytes(), head_bytes)
        self.assertEqual(w.git(w.live, "symbolic-ref", "HEAD"), "refs/heads/main")
        self.assertEqual(w.git(w.live, "rev-parse", "origin/main"), remote_head)

    def test_advance_reports_unreadable_main_ref_separately(self):
        w = self.w
        head = w.git(w.live, "rev-parse", "HEAD")
        remote_head = w.git(w.live, "rev-parse", "origin/main")
        w.commit_on_origin({"README.md": "nova revisão"}, "Avança o bare")
        head_file = w.live / ".git" / "HEAD"
        head_bytes = head_file.read_bytes()
        run = store.run
        for response in ((128, "ref ilegível"), (0, "warning: ignoring broken ref")):
            with self.subTest(response=response):
                def unreadable(args, *rest, **kwargs):
                    if "for-each-ref" in args:
                        return response
                    return run(args, *rest, **kwargs)

                with mock.patch.object(store, "run", side_effect=unreadable) as commands:
                    record = store.live_advance(self.ctx, SLUG)

                self.assertTrue(any("for-each-ref" in call.args[0] for call in commands.call_args_list))
                self.assertFalse(any("fetch" in call.args[0] for call in commands.call_args_list))
                self.assertEqual((record["resultado"], record["detalhe"]),
                                 ("erro", "refs/heads/main do clone ilegível"))
                self.assertEqual((record["antes"], record["depois"]), (head, head))
                self.assertEqual(json.loads((w.data / f"live/{SLUG}.json").read_text()), record)
                self.assertEqual(w.git(w.live, "rev-parse", "HEAD"), head)
                self.assertEqual(w.git(w.live, "rev-parse", "origin/main"), remote_head)

    def test_advance_revalidates_clone_identity_before_fetch(self):
        w = self.w
        obstruction = store._live_obstruction

        def replace_origin_after_inspection(path, env):
            result = obstruction(path, env)
            if result is None:
                w.git(path, "remote", "set-url", "origin", str(w.origin))
            return result

        with mock.patch.object(store, "_live_obstruction", side_effect=replace_origin_after_inspection):
            record = store.live_advance(self.ctx, SLUG)
        self.assertEqual((record["resultado"], record["detalhe"]),
                         ("erro", f"sem clone dedicado: {SLUG}"))

    def test_advance_does_not_merge_after_branch_switch_during_fetch(self):
        w = self.w
        head = w.git(w.live, "rev-parse", "HEAD")
        new = w.commit_on_origin({"README.md": "nova revisão"}, "Avança o bare")
        fetch = store._live_fetch

        def fetch_then_switch(*args, **kwargs):
            fetch(*args, **kwargs)
            w.git(w.live, "switch", "-qc", "ramo-do-dono")

        with mock.patch.object(store, "_live_fetch", side_effect=fetch_then_switch):
            record = store.live_advance(self.ctx, SLUG)
        self.assertEqual(record["resultado"], "fora-da-main")
        self.assertEqual((record["antes"], record["depois"]), (head, head))
        self.assertEqual(w.git(w.live, "rev-parse", "origin/main"), new)
        self.assertEqual(w.git(w.live, "branch", "--show-current"), "ramo-do-dono")
        for branch in ("main", "ramo-do-dono"):
            self.assertEqual(w.git(w.live, "rev-parse", branch), head)

    def test_advance_does_not_merge_when_tree_becomes_dirty_during_fetch(self):
        w = self.w
        head = w.git(w.live, "rev-parse", "HEAD")
        new = w.commit_on_origin({"README.md": "nova revisão"}, "Avança o bare")
        fetch = store._live_fetch

        def fetch_then_edit(*args, **kwargs):
            fetch(*args, **kwargs)
            (w.live / "estado").write_text("preservar")

        with mock.patch.object(store, "_live_fetch", side_effect=fetch_then_edit):
            record = store.live_advance(self.ctx, SLUG)
        self.assertEqual(record["resultado"], "suja")
        self.assertEqual(w.git(w.live, "rev-parse", "origin/main"), new)
        self.assertEqual(w.git(w.live, "rev-parse", "HEAD"), head)
        self.assertEqual((w.live / "estado").read_text(), "preservar")

    def test_advance_reports_unreadable_branch_without_fetch(self):
        run = store.run

        def branch_error(command, **kw):
            if "symbolic-ref" in command:
                return 128, ""
            return run(command, **kw)

        with mock.patch.object(store, "run", side_effect=branch_error), \
                mock.patch.object(store, "_live_fetch") as fetch:
            record = store.live_advance(self.ctx, SLUG)
        fetch.assert_not_called()
        self.assertEqual((record["resultado"], record["detalhe"]),
                         ("erro", "branch do clone ilegível (git saiu 128)"))

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


class InstallTest(unittest.TestCase):
    def test_windows_uses_native_rename(self):
        checkout = mock.Mock()
        with mock.patch.object(os, "name", "nt"), mock.patch.object(store.ctypes, "CDLL") as libc:
            store._install_live_clone(checkout, "destino")
        checkout.rename.assert_called_once_with("destino")
        libc.assert_not_called()

    def test_mac_os_requests_exclusive_rename(self):
        libc = mock.Mock(spec=["renamex_np"])
        libc.renamex_np.return_value = 0
        with mock.patch.object(os, "name", "posix"), mock.patch.object(sys, "platform", "darwin"), \
                mock.patch.object(store.ctypes, "CDLL", return_value=libc) as load:
            store._install_live_clone("cópia", "destino")
        load.assert_called_once_with(None, use_errno=True)
        libc.renamex_np.assert_called_once_with(os.fsencode("cópia"), os.fsencode("destino"), 4)

    def test_missing_exclusive_rename_has_no_overwrite_fallback(self):
        for platform in ("linux", "darwin", "outro"):
            with self.subTest(platform=platform), mock.patch.object(os, "name", "posix"), \
                    mock.patch.object(sys, "platform", platform), \
                    mock.patch.object(store.ctypes, "CDLL", return_value=object()):
                with self.assertRaisesRegex(store.StoreError, "não suportada"):
                    store._install_live_clone("cópia", "destino")


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

    def test_spawn_failure_warns_even_with_prior_ok(self):
        rw = store.rw_auto.rw
        record = store.live_advance(self.ctx, SLUG)
        self.assertEqual(record["resultado"], "ok")
        path = self.w.data / f"live/{SLUG}.json"
        prior = path.read_bytes()
        segments = ((None, "queue_notice"), ("rw_auto", "live_notice"))
        for other in (None, "fila de sessões headless"):
            with self.subTest(queue=other), mock.patch.object(rw, "NOTICES", segments), \
                    mock.patch.object(rw, "queue_notice", return_value=other), \
                    mock.patch.object(subprocess, "Popen", side_effect=OSError("falha no lançamento")):
                notice = rw.cmd_pending({}, self.ctx)
                self.assertIsNotNone(notice)
                self.assertIn("não foi possível iniciar o avanço dos clones", notice["systemMessage"])
                if other:
                    self.assertIn(other, notice["systemMessage"])
        self.assertEqual(path.read_bytes(), prior)
        self.assertIn("falha no lançamento", (self.w.data / "errors.log").read_text(encoding="utf-8"))

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

    def test_advance_records_same_basename_without_losing_notice(self):
        w = self.w
        other = "other/kb-libs"
        w.config(owners=["fixture", "other"], lean_auto=[SLUG, other])
        ctx = w.ctx()
        w.git(w.live, "switch", "-qc", "outro")
        for repo, expected in ((SLUG, "fora-da-main"), (other, "erro")):
            self.assertEqual(store.live_advance(ctx, repo)["resultado"], expected)
        notice = store.rw_auto.live_notice(ctx)
        self.assertIn(f"avanço de {SLUG} falhou: cópia em uso fora da main", notice)
        self.assertIn(f"avanço de {other} falhou:", notice)
        for repo in (SLUG, other):
            path = w.data / f"live/{repo}.json"
            self.assertEqual(json.loads(path.read_text())["repo"], repo)

    def test_present_invalid_advance_record_reports_error(self):
        notice = store.rw_auto.live_notice
        self.assertIsNone(notice(self.ctx))
        path = self.w.data / f"live/{SLUG}.json"
        path.parent.mkdir(parents=True)
        for invalid in (b"{", b"\xff", b"[]", b"{}",
                        b'{"repo":"other/kb-libs","resultado":"ok","detalhe":""}',
                        json.dumps(dict(repo=SLUG, resultado="invalido", detalhe="")).encode(),
                        json.dumps(dict(repo=SLUG, resultado="erro", detalhe=42)).encode()):
            with self.subTest(invalid=invalid):
                path.write_bytes(invalid)
                self.assertEqual(notice(self.ctx), f"avanço de {SLUG} falhou: registro de avanço inválido")
        path.write_text(json.dumps(dict(repo=SLUG, resultado="ok", detalhe="")))
        self.assertIsNone(notice(self.ctx))
        path.write_text(json.dumps(dict(repo=SLUG, resultado="erro", detalhe="")))
        self.assertEqual(notice(self.ctx), f"avanço de {SLUG} falhou: erro")
        path.unlink()
        path.mkdir()
        self.assertEqual(notice(self.ctx), f"avanço de {SLUG} falhou: registro de avanço inválido")
