"""Isolamento da origem privada e contrato do pre-push da fixture."""
import json
import subprocess
import unittest

from fixture_private import PrivateWorld, SLUG


class FixturePrivateTest(unittest.TestCase):
    def setUp(self):
        self.w = PrivateWorld()
        self.addCleanup(self.w.cleanup)

    def test_isolated_origins(self):
        w = self.w
        for clone in (w.dev, w.live, w.store, w.other):
            w.assert_fixture_origin(clone)
        self.assertTrue(w.git(w.dev, "remote", "get-url", "origin").endswith(f"{SLUG}.git"))
        w.git(w.dev, "remote", "set-url", "--push", "origin", str(w.origin))
        with self.assertRaises(AssertionError):
            w.assert_fixture_origin(w.dev)

    def test_prepush_accepts_and_refuses(self):
        w = self.w
        store_head = w.origin_main()
        before = w.git(w.remote, "rev-parse", "main")
        accepted = w.commit_on_origin({"note.md": "um"}, "primeira nota")
        self.assertNotEqual(accepted, before)
        self.assertEqual(w.git(w.remote, "rev-parse", "main"), accepted)
        with self.assertRaises(subprocess.CalledProcessError) as error:
            w.commit_on_origin({"note.md": "dois"}, "segunda nota", gate_rc=2)
        self.assertIn("gate: 2 passo", error.exception.stderr)
        self.assertEqual(w.git(w.remote, "rev-parse", "main"), accepted)
        self.assertEqual(w.origin_main(), store_head)
        passed, failed = [json.loads(line) for line in w.gate_log.read_text().splitlines()][-2:]
        self.assertEqual(passed, {
            "args": ["origin", str(w.remote)], "head": accepted, "rc": 0,
            "stdin": f"HEAD {accepted} refs/heads/main {before}\n",
        })
        self.assertEqual(failed["head"], w.git(w.dev, "rev-parse", "HEAD"))
        self.assertEqual(failed["rc"], 2)
