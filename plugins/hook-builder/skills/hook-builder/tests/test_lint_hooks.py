"""O lint_hooks.py pelos dois hosts: forma, guarda de Stop, opções e o --host both sem eco."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
LINT = HERE.parent / "scripts" / "lint_hooks.py"
CAPTURE = HERE.parent / "scripts" / "capture_payload.py"


def run(*args):
    return subprocess.run([sys.executable, str(LINT), *map(str, args)],
                          capture_output=True, text=True)


class LintTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def config(self, data, name="hooks.json"):
        path = self.dir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data), encoding="utf-8")
        return path

    def plugin(self, command, event="Stop", guard=False):
        """Um plugin em <tmp>/p com hooks/hooks.json e um script de Stop."""
        (self.dir / "p" / "scripts").mkdir(parents=True)
        body = "import json, sys\n" + ("json.load(sys.stdin)['stop_hook_active']\n" if guard else "")
        (self.dir / "p" / "scripts" / "stop.py").write_text(body, encoding="utf-8")
        return self.config({"hooks": {event: [{"hooks": [{"type": "command", "command": command}]}]}},
                           "p/hooks/hooks.json")

    def test_codex_malformed_structure_is_an_error(self):
        cases = {
            "hooks lista": {"hooks": []},
            "evento objeto": {"hooks": {"Stop": {}}},
            "grupo texto": {"hooks": {"Stop": ["x"]}},
            "grupo sem hooks": {"hooks": {"Stop": [{"matcher": ""}]}},
            "hooks vazio": {"hooks": {"Stop": [{"hooks": []}]}},
        }
        for name, data in cases.items():
            for host in ("codex", "claude", "both"):
                with self.subTest(name, host=host):
                    result = run(self.config(data), "--host", host)
                    self.assertEqual(result.returncode, 1, result.stdout)
                    self.assertIn("ERRO", result.stdout)

    def test_codex_valid_shell_form_passes(self):
        command = 'python3 "${CLAUDE_PLUGIN_ROOT}/scripts/stop.py"'
        result = run(self.plugin(command, guard=True), "--host", "both")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("0 erro(s), 0 aviso(s)", result.stdout)

    def test_stop_guard_with_plugin_root_placeholder(self):
        result = run(self.plugin('python3 "${PLUGIN_ROOT}/scripts/stop.py"'), "--host", "codex")
        self.assertIn("stop_hook_active", result.stdout)

    def test_codex_subagent_stop_guard(self):
        path = self.plugin('python3 "${CLAUDE_PLUGIN_ROOT}/scripts/stop.py"', event="SubagentStop")
        self.assertIn("stop_hook_active", run(path, "--host", "codex").stdout)

    def test_both_does_not_echo_warnings(self):
        result = run(self.plugin("python3 ${CLAUDE_PLUGIN_ROOT}/scripts/stop.py"), "--host", "both")
        lines = [line for line in result.stdout.splitlines() if line.startswith(("ERRO", "AVISO"))]
        self.assertEqual(len(lines), len(set(lines)), result.stdout)
        self.assertEqual(sum("stop_hook_active" in line for line in lines), 1, result.stdout)
        self.assertEqual(sum("placeholder" in line for line in lines), 1, result.stdout)
        self.assertNotIn("forma exec", result.stdout)

    def test_option_without_value_is_usage_error(self):
        path = self.config({"hooks": {"Stop": [{"hooks": [{"type": "command", "command": "x"}]}]}})
        for args in (["--host"], ["--plugin-json"], ["--host", "--plugin-json", "x.json"]):
            with self.subTest(args=args):
                self.assertEqual(run(path, *args).returncode, 2)

    def test_codex_args_is_an_error(self):
        data = {"hooks": {"Stop": [{"hooks": [{"type": "command", "command": "python3",
                                               "args": ["hook.py"]}]}]}}
        result = run(self.config(data), "--host", "codex")
        self.assertEqual(result.returncode, 1)
        self.assertIn("'args'", result.stdout)

    def test_codex_probe_config_lints_clean(self):
        printed = subprocess.run([sys.executable, str(CAPTURE), "--print-config", "PostToolUse,Stop",
                                  str(self.dir / "out"), "--host", "codex"],
                                 capture_output=True, text=True, check=True).stdout
        result = run(self.config(json.loads(printed)), "--host", "codex")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("0 erro(s), 0 aviso(s)", result.stdout)


if __name__ == "__main__":
    unittest.main()
