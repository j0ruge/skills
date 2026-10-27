"""O lint_hooks.py pelos dois hosts: forma, guarda de Stop, opções e o --host both sem eco."""
import json
import os
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

    def test_malformed_structure_is_an_error_in_every_host(self):
        stop = lambda handler: {"hooks": {"Stop": [{"hooks": [handler]}]}}  # noqa: E731
        cases = {
            "hooks lista": ({"hooks": []}, "precisa ser um objeto"),
            "evento objeto": ({"hooks": {"Stop": {}}}, "lista de grupos"),
            "grupo texto": ({"hooks": {"Stop": ["x"]}}, "grupo precisa ser um objeto"),
            "grupo sem hooks": ({"hooks": {"Stop": [{"matcher": ""}]}}, "falta a lista 'hooks'"),
            "hooks vazio": ({"hooks": {"Stop": [{"hooks": []}]}}, "falta a lista 'hooks'"),
            "command número": (stop({"type": "command", "command": 123}), "command precisa ser texto"),
            "sem command": (stop({"type": "command"}), "exige o campo 'command'"),
        }
        for name, (data, fragment) in cases.items():
            for host in ("codex", "claude", "both"):
                with self.subTest(name, host=host):
                    result = run(self.config(data), "--host", host)
                    self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                    self.assertEqual(result.stdout.count(fragment), 1, result.stdout)
                    self.assertNotIn("Traceback", result.stderr)

    def test_args_not_a_list_does_not_crash(self):
        data = {"hooks": {"Stop": [{"hooks": [{"type": "command", "command": "x", "args": 5}]}]}}
        for host in ("claude", "codex"):
            with self.subTest(host=host):
                result = run(self.config(data), "--host", host)
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertNotIn("Traceback", result.stderr)
                self.assertIn("args", result.stdout)

    def test_unchecked_stop_guard_is_a_warning(self):
        data = {"hooks": {"Stop": [{"hooks": [
            {"type": "command", "command": 'python3 "${CLAUDE_PLUGIN_ROOT}/scripts/nao-existe.py"'}]}]}}
        for name, fragment in (("solto.json", "só resolve"), ("p/hooks/hooks.json", "não existe")):
            with self.subTest(name):
                result = run(self.config(data, name), "--host", "both")
                self.assertEqual(result.returncode, 0, result.stdout)
                lines = [line for line in result.stdout.splitlines() if fragment in line]
                self.assertEqual(len(lines), 1, result.stdout)
                self.assertTrue(lines[0].startswith("AVISO"), lines[0])

    def test_plugin_directory_is_unchecked_not_missing(self):
        command = 'cd "${CLAUDE_PLUGIN_ROOT}/scripts" && python3 stop.py; true'
        result = run(self.plugin(command, guard=True), "--host", "both")
        self.assertNotIn("não existe", result.stdout)
        self.assertIn("cita só diretório", result.stdout)

    def test_placeholder_list_is_split(self):
        command = ('PYTHONPATH="${CLAUDE_PLUGIN_ROOT}/scripts:${PLUGIN_ROOT}" '
                   'python3 "${CLAUDE_PLUGIN_ROOT}/scripts/stop.py"')
        result = run(self.plugin(command, guard=True), "--host", "both")
        self.assertIn("0 erro(s), 0 aviso(s)", result.stdout)

    @unittest.skipIf(os.geteuid() == 0, "root lê arquivo 000")
    def test_unreadable_stop_script_is_a_warning(self):
        path = self.plugin('python3 "${CLAUDE_PLUGIN_ROOT}/scripts/stop.py"')
        script = self.dir / "p" / "scripts" / "stop.py"
        script.chmod(0)
        self.assertIn("não li stop.py", run(path, "--host", "codex").stdout)

    def test_non_object_json_is_an_error(self):
        for data in (None, 3, []):
            with self.subTest(data=data):
                result = run(self.config(data))
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertNotIn("Traceback", result.stderr)
                self.assertIn("precisa ser um objeto JSON", result.stdout)
        hooks = self.config({"hooks": {}})
        manifest = self.config([], "plugin.json")
        result = run(hooks, "--plugin-json", manifest)
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("plugin.json: precisa ser um objeto JSON", result.stdout)

    def test_codex_warns_on_claude_only_fields(self):
        data = {"hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [
            {"type": "command", "command": 'x "$CLAUDE_PLUGIN_OPTION_TOKEN"', "once": True}]}]}}
        result = run(self.config(data), "--host", "codex")
        self.assertIn("'once'", result.stdout)
        self.assertIn("CLAUDE_PLUGIN_OPTION_", result.stdout)
        both = run(self.config(data), "--host", "both").stdout
        self.assertEqual(both.count("'once'"), 1, both)

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
