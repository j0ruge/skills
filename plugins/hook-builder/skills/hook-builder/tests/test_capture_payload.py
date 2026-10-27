"""O probe: o que ele grava, com que permissão, o que esconde e como recusa uso inválido."""
import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
CAPTURE = HERE.parent / "scripts" / "capture_payload.py"


def run(*args, stdin="", env=None):
    return subprocess.run([sys.executable, str(CAPTURE), *map(str, args)], input=stdin,
                          capture_output=True, text=True, env=env)


class CaptureTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.out = Path(self.tmp.name) / "out"

    def tearDown(self):
        self.tmp.cleanup()

    def capture(self, payload, extra_env=None):
        env = {k: v for k, v in os.environ.items() if not k.startswith(("CLAUDE", "CODEX", "PLUGIN_"))}
        env.update(extra_env or {})
        result = run("--capture", self.out, stdin=payload, env=env)
        self.assertEqual((result.returncode, result.stdout), (0, ""))
        return result

    def test_files_are_private(self):
        self.capture(json.dumps({"hook_event_name": "Stop"}))
        self.assertEqual(stat.S_IMODE(self.out.stat().st_mode), 0o700)
        files = sorted(self.out.iterdir())
        self.assertEqual([f.name.split("-")[0] for f in files], ["env", "stdin"])
        for f in files:
            self.assertEqual(stat.S_IMODE(f.stat().st_mode), 0o600, f.name)

    def test_sensitive_names_are_redacted(self):
        canary = "canario-7f3a"
        names = ["CODEX_AUTH_JSON", "PLUGIN_DB_PASSWD", "CLAUDE_X_CREDENTIALS", "CODEX_COOKIE",
                 "PLUGIN_PRIVATE_PEM", "CLAUDE_API_KEY", "CODEX_PASSPHRASE"]
        self.capture(json.dumps({"hook_event_name": "Stop"}),
                     {**{name: canary for name in names}, "CODEX_HOME": "/visivel"})
        env_text = next(self.out.glob("env-*")).read_text()
        self.assertNotIn(canary, env_text)
        self.assertIn("CODEX_HOME=/visivel", env_text)

    def test_event_name_cannot_leave_the_directory(self):
        self.capture(json.dumps({"hook_event_name": "../../fora"}))
        self.assertEqual(len(list(self.out.iterdir())), 2)
        self.assertFalse((Path(self.tmp.name).parent / "fora").exists())

    def test_failure_goes_to_stderr_not_silence(self):
        blocker = Path(self.tmp.name) / "arquivo"
        blocker.write_text("x")
        result = run("--capture", blocker / "sub", stdin="{}")
        self.assertEqual((result.returncode, result.stdout), (0, ""))
        self.assertIn("captura falhou", result.stderr)

    def test_print_config_option_without_value_is_usage_error(self):
        for args in (["--host"], ["--matcher"], ["--matcher", "--host", "codex"]):
            with self.subTest(args=args):
                self.assertEqual(run("--print-config", "Stop", self.out, *args).returncode, 2)

    def test_codex_config_is_shell_form(self):
        config = json.loads(run("--print-config", "Stop", self.out, "--host", "codex").stdout)
        handler = config["hooks"]["Stop"][0]["hooks"][0]
        self.assertNotIn("args", handler)
        self.assertIn("--capture", handler["command"])
        self.assertEqual(set(config), {"description", "hooks"})


if __name__ == "__main__":
    unittest.main()
