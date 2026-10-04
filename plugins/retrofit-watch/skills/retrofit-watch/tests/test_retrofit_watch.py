"""Testes do retrofit-watch: classificação de dono da skill e regra de disparo do Stop hook.

Rodar: python3 -m unittest plugins/retrofit-watch/tests/test_retrofit_watch.py
Monta um HOME fixture com cache de marketplace, clone do marketplace, repos git de projeto e de
terceiro, e transcripts JSONL sintéticos no formato real (2.1.283). Só biblioteca padrão + git.
Rode também no Windows, com o `python3` do PATH (o mesmo do hooks.json): é só lá que aparecem a
falta do fcntl e o path com `\\`.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE.parent / "scripts" / "retrofit_watch.py"
sys.path.insert(0, str(SCRIPT.parent))
import retrofit_watch as rw  # noqa: E402

UNATTENDED = {"CLAUDE_CODE_SESSION_ATTENDED": "0", "CLAUDE_CODE_ENTRYPOINT": "sdk-cli"}
# O stdio do Python no Windows quando o Claude Code chama o hook por pipe; reproduz em qualquer SO.
WINDOWS_STDIO = {"PYTHONIOENCODING": "cp1252:surrogateescape"}
# No Windows, o `shutil.which` só acha binário com extensão do PATHEXT.
EXE = ".cmd" if os.name == "nt" else ""
GIT_ENV = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t",
               GIT_COMMITTER_EMAIL="t@t", GIT_CONFIG_NOSYSTEM="1")


def git(cwd, *args):
    subprocess.run(["git", "-C", str(cwd), *args], check=True, capture_output=True, env=GIT_ENV)


def make_skill(parent, name):
    d = Path(parent) / name
    d.mkdir(parents=True, exist_ok=True)
    (d / "SKILL.md").write_text(f"---\nname: {name}\ndescription: t\n---\n# {name}\n")
    return d


def init_repo(path, origin):
    path.mkdir(parents=True, exist_ok=True)
    git(path, "init", "-q")
    git(path, "remote", "add", "origin", origin)


def commit_all(path):
    git(path, "add", "-A")
    git(path, "commit", "-q", "-m", "fixture")


class World:
    """HOME fixture com todas as origens de skill que o hook precisa distinguir."""

    def __init__(self):
        self.tmp = Path(os.path.realpath(tempfile.mkdtemp(prefix="rw-test-")))
        self.home = self.tmp / "home"
        self.data = self.tmp / "data"
        cache = self.home / ".claude/plugins/cache"
        self.mkt_skill = make_skill(cache / "chewiesoft-marketplace/codereview/2.0.0/skills", "coderabbit-pr")
        self.mkt_quality = make_skill(cache / "chewiesoft-marketplace/skill-quality-audit/0.4.0/skills",
                                      "skill-claim-check")
        self.other_skill = make_skill(cache / "claude-plugins-official/superpowers/6.4.1/skills", "brainstorming")
        (self.home / ".claude/plugins/installed_plugins.json").write_text(json.dumps({"version": 2, "plugins": {
            "codereview@chewiesoft-marketplace": [{"installPath": str(cache / "chewiesoft-marketplace/codereview/2.0.0")}],
            "dev-script@chewiesoft-marketplace": [{"installPath": str(cache / "chewiesoft-marketplace/dev-script/1.0.0")}],
            "superpowers@claude-plugins-official": [{"installPath": str(cache / "claude-plugins-official/superpowers/6.4.1")}],
        }}))
        # clone do marketplace (symlink em ~/.claude/skills, --plugin-dir, worktree)
        self.repo = self.tmp / "repos/skills"
        init_repo(self.repo, "https://github.com/j0ruge/skills.git")
        (self.repo / ".claude-plugin").mkdir()
        (self.repo / ".claude-plugin/marketplace.json").write_text(json.dumps({"name": "chewiesoft-marketplace"}))
        self.ticket = make_skill(self.repo / "plugins/ticket/skills", "ticket")
        self.watch_skill = make_skill(self.repo / "plugins/retrofit-watch/skills", "retrofit-watch")
        commit_all(self.repo)
        (self.home / ".claude/skills").mkdir(parents=True)
        os.symlink(self.ticket, self.home / ".claude/skills/ticket")
        # repo de projeto nosso (modo lean)
        self.proj = self.tmp / "repos/app-interno"
        init_repo(self.proj, "https://github.com/JRC-Brasil/app-interno.git")
        (self.proj / ".gitignore").write_text(".claude/skills/local-only/\n")
        self.graphify = make_skill(self.proj / ".claude/skills", "graphify")
        self.local_only = make_skill(self.proj / ".claude/skills", "local-only")
        self.locked = make_skill(self.proj / ".claude/skills", "grill-with-docs")
        self.agents_skill = make_skill(self.proj / ".agents/skills", "self-learning")
        (self.proj / "skills-lock.json").write_text(json.dumps({"version": 1, "skills": {"grill-with-docs": {}}}))
        commit_all(self.proj)
        # terceiro com git próprio, skill fora do git, Hermes
        self.napkin = self.home / ".claude/skills/napkin"
        init_repo(self.napkin, "https://github.com/blader/napkin.git")
        (self.napkin / "SKILL.md").write_text("---\nname: napkin\ndescription: t\n---\n")
        commit_all(self.napkin)
        self.unversioned = make_skill(self.home / ".claude/skills", "qa-execution")
        self.hermes = make_skill(self.home / ".hermes/skills/autonomous-ai-agents", "hermes-agent")
        # kit nosso (o sdd): binário no PATH por symlink, como o ~/.hermes/bin/sdd
        self.kit_repo = self.tmp / "repos/sdd_agents"
        init_repo(self.kit_repo, "https://github.com/j0ruge/sdd_agents.git")
        (self.kit_repo / "bin").mkdir()
        (self.kit_repo / f"bin/sdd{EXE}").write_text("#!/bin/sh\n")
        (self.kit_repo / f"bin/sdd{EXE}").chmod(0o755)
        (self.kit_repo / "TODO.md").write_text("# TODO\n")
        commit_all(self.kit_repo)
        self.bindir = self.tmp / "bin"
        self.bindir.mkdir()
        os.symlink(self.kit_repo / f"bin/sdd{EXE}", self.bindir / f"sdd{EXE}")
        # kit de terceiro, com o mesmo formato
        third = self.tmp / "repos/outro-kit"
        init_repo(third, "https://github.com/alguem/outro-kit.git")
        (third / f"otk{EXE}").write_text("#!/bin/sh\n")
        (third / f"otk{EXE}").chmod(0o755)
        commit_all(third)
        os.symlink(third / f"otk{EXE}", self.bindir / f"otk{EXE}")
        self.transcript = self.tmp / "session.jsonl"
        self.transcript.write_text("")

    def ctx(self):
        return rw.Context(home=self.home, data_dir=self.data)

    def cleanup(self):
        shutil.rmtree(self.tmp, ignore_errors=True)


# --- construtores de linhas de transcript (formato observado na 2.1.283) ---------------------

def skill_via_tool(skill_name, path):
    return [
        {"type": "assistant", "message": {"role": "assistant", "content": [
            {"type": "tool_use", "id": "toolu_s", "name": "Skill", "input": {"skill": skill_name}}]}},
        {"type": "user", "message": {"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": "toolu_s", "content": f"Launching skill: {skill_name}"}]}},
        {"type": "user", "isMeta": True, "sourceToolUseID": "toolu_s", "message": {"role": "user", "content": [
            {"type": "text", "text": f"Base directory for this skill: {path}\n\n# corpo"}]}},
    ]


def skill_typed(command, path=None, args=""):
    lines = [{"type": "user", "message": {"role": "user", "content":
              f"<command-message>{command}</command-message>\n<command-name>/{command}</command-name>"
              + (f"\n<command-args>{args}</command-args>" if args else "")}}]
    if path:
        lines.append({"type": "user", "isMeta": True, "message": {"role": "user", "content": [
            {"type": "text", "text": f"Base directory for this skill: {path}\n\n# corpo"}]}})
    return lines


def tool(name="Bash", error=False):
    return [
        {"type": "assistant", "message": {"role": "assistant", "content": [
            {"type": "tool_use", "id": "toolu_t", "name": name, "input": {}}]}},
        {"type": "user", "message": {"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": "toolu_t", "content": "x", "is_error": error}]}},
    ]


def tool_with(name, tool_input, error=False):
    """Chamada de ferramenta com input (Agent, Bash, Edit), no formato do transcript."""
    return [
        {"type": "assistant", "message": {"role": "assistant", "content": [
            {"type": "tool_use", "id": "toolu_i", "name": name, "input": tool_input}]}},
        {"type": "user", "message": {"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": "toolu_i", "content": "x", "is_error": error}]}},
    ]


def prompt(text):
    return [{"type": "user", "message": {"role": "user", "content": text}}]


def assistant_text(text):
    return [{"type": "assistant", "message": {"role": "assistant", "content": [{"type": "text", "text": text}]}}]


def quoted_base_dir(path):
    """A frase citada dentro de um tool_result não é carga de skill."""
    return [{"type": "user", "message": {"role": "user", "content": [
        {"type": "tool_result", "tool_use_id": "toolu_q", "content": f"Base directory for this skill: {path}"}]}}]


class ClassifyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.w = World()
        cls.ctx = cls.w.ctx()

    @classmethod
    def tearDownClass(cls):
        cls.w.cleanup()

    def classify(self, path):
        return rw.classify_path(str(path), self.ctx)

    def test_marketplace_cache_is_full_with_plugin_name_as_argument(self):
        got = self.classify(self.w.mkt_skill)
        self.assertEqual((got["mode"], got["arg"]), ("full", "codereview"))

    def test_symlink_into_marketplace_clone_is_full(self):
        got = self.classify(self.w.home / ".claude/skills/ticket")
        self.assertEqual((got["mode"], got["arg"]), ("full", "ticket"))

    def test_plugin_dir_or_worktree_of_marketplace_clone_is_full(self):
        wt = self.w.tmp / "wt-skills"
        git(self.w.repo, "worktree", "add", "-q", str(wt))
        got = self.classify(wt / "plugins/ticket/skills/ticket")
        self.assertEqual((got["mode"], got["arg"]), ("full", "ticket"))

    def test_tracked_project_skill_of_our_org_is_lean(self):
        got = self.classify(self.w.graphify)
        self.assertEqual((got["mode"], got["arg"], got["repo"]), ("lean", "graphify", str(self.w.proj)))

    def test_project_worktree_is_lean_in_the_worktree(self):
        wt = self.w.tmp / "wt-sq"
        git(self.w.proj, "worktree", "add", "-q", str(wt))
        got = self.classify(wt / ".claude/skills/graphify")
        self.assertEqual((got["mode"], got["repo"]), ("lean", str(wt)))

    def test_ignored(self):
        cases = {
            "gitignored": self.w.local_only,
            "skills-lock": self.w.locked,
            ".agents/skills": self.w.agents_skill,
            "third-party origin": self.w.napkin,
            "outside git": self.w.unversioned,
            "hermes": self.w.hermes,
            "other marketplace": self.w.other_skill,
            "excluded plugin": self.w.mkt_quality,
            "excluded self": self.w.watch_skill,
        }
        for label, path in cases.items():
            with self.subTest(label):
                self.assertIsNone(self.classify(path))

    def test_config_include_and_exclude(self):
        cfg_path = self.w.home / ".claude/retrofit-watch.json"
        cfg_path.write_text(json.dumps({"include": ["qa-execution"], "exclude": ["codereview"]}))
        try:
            ctx = self.w.ctx()
            self.assertEqual(rw.classify_path(str(self.w.unversioned), ctx)["mode"], "lean")
            self.assertIsNone(rw.classify_path(str(self.w.mkt_skill), ctx))
        finally:
            cfg_path.unlink()

    def test_plugin_name_lookup_for_commands_only_plugins(self):
        self.assertEqual(rw.classify_plugin("dev-script", self.ctx)["arg"], "dev-script")
        self.assertIsNone(rw.classify_plugin("superpowers", self.ctx))
        self.assertIsNone(rw.classify_plugin("retrofit-skill", self.ctx))


class StopTest(unittest.TestCase):
    def setUp(self):
        self.w = World()

    def tearDown(self):
        self.w.cleanup()

    def write(self, *groups):
        with open(self.w.transcript, "a", encoding="utf-8") as fh:
            for group in groups:
                for entry in group:
                    fh.write(json.dumps(entry) + "\n")

    def run_hook(self, sub="stop", last="Feito.", active=False, env=None, raw=None, mode="default"):
        payload = raw if raw is not None else json.dumps({
            "session_id": "s1", "transcript_path": str(self.w.transcript), "cwd": str(self.w.proj),
            "hook_event_name": "Stop" if sub == "stop" else "SessionStart", "permission_mode": mode,
            "stop_hook_active": active, "last_assistant_message": last, "source": "resume"},
            ensure_ascii=False)
        full_env = dict(os.environ, HOME=str(self.w.home), CLAUDE_PLUGIN_DATA=str(self.w.data),
                        CLAUDE_CODE_SESSION_ATTENDED="1", CLAUDE_CODE_ENTRYPOINT="cli",
                        PATH=f"{self.w.bindir}{os.pathsep}{os.environ.get('PATH', '')}")
        full_env.pop("RETROFIT_WATCH", None)
        full_env.update(env or {})
        # O Claude Code manda o JSON em UTF-8 cru (JSON.stringify não escapa acento) em qualquer SO;
        # `text=True` usaria a página de código local.
        proc = subprocess.run([sys.executable, str(SCRIPT), sub], input=payload.encode("utf-8"),
                              capture_output=True, env=full_env, timeout=20)
        self.assertEqual(proc.returncode, 0, proc.stderr.decode("utf-8", "replace"))
        out = proc.stdout.decode("utf-8").strip()
        return json.loads(out) if out else None

    def context_of(self, out):
        self.assertIsNotNone(out, "esperava um pedido de retro")
        return out["hookSpecificOutput"]["additionalContext"]

    def test_real_work_fires_once_with_retrofit_command(self):
        self.write(skill_via_tool("codereview:coderabbit-pr", self.w.mkt_skill), *[tool()] * 6)
        out = self.run_hook()
        text = self.context_of(out)
        self.assertEqual(out["hookSpecificOutput"]["hookEventName"], "Stop")
        self.assertIn("/retrofit-skill:retrofit-skill codereview", text)
        self.assertIn("sem lições novas", text)
        self.assertLess(len(text), 900)
        self.assertIn("systemMessage", out)
        self.assertIsNone(self.run_hook(), "não repete sem trabalho novo")

    def test_little_work_does_not_fire(self):
        self.write(skill_via_tool("codereview:coderabbit-pr", self.w.mkt_skill), tool(), tool())
        self.assertIsNone(self.run_hook())

    def test_one_error_and_one_call_fires(self):
        self.write(skill_via_tool("codereview:coderabbit-pr", self.w.mkt_skill), tool(error=True))
        self.assertIsNotNone(self.run_hook())

    def test_typed_slash_skill_is_seen(self):
        self.write(skill_typed("graphify", self.w.graphify), tool(error=True))
        text = self.context_of(self.run_hook())
        self.assertIn("/retrofit-skill:retrofit-skill graphify", text)
        self.assertIn("lean", text)

    def test_commands_only_plugin_is_seen_by_name(self):
        self.write(skill_typed("dev-script:dev-script"), tool(error=True))
        self.assertIn("dev-script", self.context_of(self.run_hook()))

    def test_waiting_for_user_defers_then_fires(self):
        self.write(skill_via_tool("codereview:coderabbit-pr", self.w.mkt_skill), tool(error=True))
        self.assertIsNone(self.run_hook(last="Qual das duas opções você prefere?"))
        self.write(prompt("a primeira"), tool())
        self.assertIsNotNone(self.run_hook(last="Pronto."))

    def test_ask_user_question_last_defers(self):
        self.write(skill_via_tool("codereview:coderabbit-pr", self.w.mkt_skill), tool(error=True),
                   tool("AskUserQuestion"))
        self.assertIsNone(self.run_hook())

    def test_plan_mode_defers(self):
        self.write(skill_via_tool("codereview:coderabbit-pr", self.w.mkt_skill), *[tool()] * 6)
        self.assertIsNone(self.run_hook(mode="plan"))

    def test_stop_hook_active_is_silent_and_records_metric(self):
        self.write(skill_via_tool("codereview:coderabbit-pr", self.w.mkt_skill), *[tool()] * 6)
        self.assertIsNotNone(self.run_hook())
        self.write(tool(), tool(), tool(), tool(), tool(), tool())
        self.assertIsNone(self.run_hook(active=True, last="retro codereview: sem lições novas"))
        metrics = (self.w.data / "metrics.jsonl").read_text().strip().splitlines()
        self.assertEqual(json.loads(metrics[-1])["outcome"], "none")
        self.assertIsNone(self.run_hook(), "o que aconteceu durante a retro não conta como trabalho")

    def test_second_review_needs_two_frictions_and_cap_is_two(self):
        self.write(skill_via_tool("codereview:coderabbit-pr", self.w.mkt_skill), *[tool()] * 6)
        self.assertIsNotNone(self.run_hook())
        self.write(tool(error=True))
        self.assertIsNone(self.run_hook())
        self.write(tool(error=True))
        self.assertIsNotNone(self.run_hook())
        self.write(tool(error=True), tool(error=True), *[tool()] * 6)
        self.assertIsNone(self.run_hook(), "teto de 2 revisões por skill por sessão")

    def test_two_skills_in_one_turn_give_one_request(self):
        self.write(skill_via_tool("codereview:coderabbit-pr", self.w.mkt_skill), tool(error=True),
                   skill_typed("graphify", self.w.graphify), tool(error=True))
        text = self.context_of(self.run_hook())
        self.assertIn("codereview", text)
        self.assertIn("graphify", text)

    def test_third_party_skill_after_ours_stops_attribution(self):
        self.write(skill_via_tool("codereview:coderabbit-pr", self.w.mkt_skill),
                   skill_via_tool("superpowers:brainstorming", self.w.other_skill), *[tool(error=True)] * 3)
        self.assertIsNone(self.run_hook())

    def test_quoted_base_directory_is_not_a_skill_load(self):
        self.write(quoted_base_dir(self.w.mkt_skill), *[tool(error=True)] * 3)
        self.assertIsNone(self.run_hook())

    def test_user_correction_and_interrupt_count_as_friction(self):
        self.write(skill_via_tool("codereview:coderabbit-pr", self.w.mkt_skill), tool(),
                   prompt("não, errado: use o outro arquivo"))
        self.assertIsNotNone(self.run_hook())

    def test_assistant_narrating_a_deviation_counts_as_friction(self):
        """A instrução da skill estava errada e o Claude contornou sem erro de ferramenta."""
        self.write(skill_via_tool("codereview:coderabbit-pr", self.w.mkt_skill), tool(),
                   assistant_text("File not in the expected location — searching the rest of the repo."))
        self.assertIsNotNone(self.run_hook())
        self.write(skill_typed("graphify", self.w.graphify), tool(),
                   assistant_text("O arquivo config/x.yaml não existe; usei conf/app.yaml em vez dele."))
        self.assertIn("graphify", self.context_of(self.run_hook()))

    def test_ordinary_narration_is_not_friction(self):
        self.write(skill_via_tool("codereview:coderabbit-pr", self.w.mkt_skill), tool(),
                   assistant_text("Rodei os testes e todos passaram."))
        self.assertIsNone(self.run_hook())

    def test_retrofit_run_suppresses_target(self):
        self.write(skill_via_tool("codereview:coderabbit-pr", self.w.mkt_skill), tool(error=True),
                   skill_typed("retrofit-skill:retrofit-skill", args="codereview"))
        self.assertIsNone(self.run_hook())

    def test_fork_baseline_ignores_copied_history(self):
        self.write(skill_via_tool("codereview:coderabbit-pr", self.w.mkt_skill), *[tool(error=True)] * 3)
        self.assertIsNone(self.run_hook(sub="baseline"))
        self.assertIsNone(self.run_hook())

    def test_partial_last_line_is_left_for_later(self):
        self.write(skill_via_tool("codereview:coderabbit-pr", self.w.mkt_skill))
        with open(self.w.transcript, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(tool(error=True)[0])[:30])
        self.assertIsNone(self.run_hook())
        with open(self.w.transcript, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(tool(error=True)[0])[30:] + "\n")
            fh.write(json.dumps(tool(error=True)[1]) + "\n")
        self.assertIsNotNone(self.run_hook())

    def kit_config(self, kits):
        (self.w.home / ".claude").mkdir(parents=True, exist_ok=True)
        (self.w.home / ".claude/retrofit-watch.json").write_text(json.dumps({"kits": kits}))

    def test_kit_command_typed_is_seen_and_points_to_the_kit_todo(self):
        """/sdd-plan não tem `:` nem Base directory: o prefixo do kit é o que o reconhece."""
        self.write(skill_typed("sdd-plan", args="tema"), *[tool()] * 5)
        text = self.context_of(self.run_hook())
        self.assertIn("kit sdd", text)
        self.assertIn(str(self.w.kit_repo / "TODO.md"), text)
        self.assertNotIn("/retrofit-skill", text)

    def test_kit_subagent_is_seen(self):
        """Agent com subagent_type `sdd-*` vigia o kit; um erro depois dele é atrito do kit."""
        self.write(tool_with("Agent", {"subagent_type": "sdd-planner", "prompt": "p"}), tool(error=True))
        self.assertIn("kit sdd", self.context_of(self.run_hook()))

    def test_kit_cli_in_bash_is_seen_but_not_as_an_argument(self):
        """`cd x && sdd run` e `echo y | sdd approve` são o kit; `grep sdd arquivo` não é."""
        self.write(*[tool_with("Bash", {"command": "grep -n sdd TODO.md"})] * 6)
        self.assertIsNone(self.run_hook())
        self.write(tool_with("Bash", {"command": "cd /r && sdd run m"}),
                   tool_with("Bash", {"command": "echo y | sdd approve m"}), *[tool()] * 4)
        self.assertIn("kit sdd", self.context_of(self.run_hook()))

    def test_writing_the_kit_todo_suppresses_the_next_retro(self):
        """O registro no TODO.md do kit é o retrofit dele: o atrito seguinte não pede outra retro."""
        self.write(skill_typed("sdd-plan"), tool(error=True))
        self.context_of(self.run_hook())
        self.write(tool_with("Edit", {"file_path": str(self.w.kit_repo / "TODO.md")}),
                   tool(error=True), tool(error=True), tool(error=True))
        self.assertIsNone(self.run_hook())

    def test_third_party_kit_and_disabled_kits_are_ignored(self):
        """Binário de repo de terceiro não vira kit; `kits: []` desliga o sdd."""
        self.kit_config(["otk"])
        self.write(skill_typed("otk-plan"), *[tool()] * 6)
        self.assertIsNone(self.run_hook())
        self.kit_config([])
        self.write(skill_typed("sdd-plan"), *[tool()] * 6)
        self.assertIsNone(self.run_hook())

    def test_kill_switch_and_force(self):
        self.write(skill_via_tool("codereview:coderabbit-pr", self.w.mkt_skill), *[tool(error=True)] * 3)
        self.assertIsNone(self.run_hook(env=dict(UNATTENDED, RETROFIT_WATCH="off")))
        self.assertFalse(self.queue_path().exists(), "off não grava nem a fila")
        self.assertIsNotNone(self.run_hook(env={"CLAUDE_CODE_SESSION_ATTENDED": "0", "RETROFIT_WATCH": "force"}))

    # --- sessão desassistida: fila fora do repo, nada devolvido à sessão -----------------------

    def queue_path(self):
        return self.w.data / "queue.jsonl"

    def queued(self):
        if not self.queue_path().exists():
            return []
        return [json.loads(line) for line in self.queue_path().read_text().splitlines() if line.strip()]

    def cli(self, *args, env=None):
        full_env = dict(os.environ, HOME=str(self.w.home), CLAUDE_PLUGIN_DATA=str(self.w.data))
        full_env.update(env or {})
        proc = subprocess.run([sys.executable, str(SCRIPT), *args], input="", capture_output=True,
                              text=True, env=full_env, timeout=20)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return proc.stdout

    def test_unattended_queues_and_says_nothing_to_the_session(self):
        self.write(skill_via_tool("codereview:coderabbit-pr", self.w.mkt_skill), tool(error=True))
        out = self.run_hook(last="Segredo do assistente: não grave isto.",
                            env=dict(UNATTENDED, GIT_REFLOG_ACTION="sdd:REVIEW:ab12cd34"))
        self.assertIsNone(out, "uma fase headless não pode ganhar turno nem aviso")
        [item] = self.queued()
        self.assertEqual(item["session"], "s1")
        self.assertEqual(item["transcript"], str(self.w.transcript))
        self.assertEqual(item["phase"], "sdd:REVIEW:ab12cd34")
        self.assertEqual(item["cwd"], str(self.w.proj))
        [skill] = item["skills"]
        self.assertEqual((skill["arg"], skill["mode"], skill["friction"]), ("codereview", "full", 1))
        self.assertNotIn("Segredo", self.queue_path().read_text(), "texto do assistente nunca é gravado")
        self.assertIsNone(self.run_hook(env=UNATTENDED))
        self.assertEqual(len(self.queued()), 1, "sem trabalho novo, nada novo na fila")

    def test_unattended_queue_needs_friction(self):
        self.write(skill_via_tool("codereview:coderabbit-pr", self.w.mkt_skill), *[tool()] * 8)
        self.assertIsNone(self.run_hook(env=UNATTENDED))
        self.assertEqual(self.queued(), [], "trabalho sem atrito não vira retro adiada")

    def test_unattended_does_not_wait_for_an_answer(self):
        self.write(skill_via_tool("codereview:coderabbit-pr", self.w.mkt_skill), tool(error=True))
        self.assertIsNone(self.run_hook(last="Rodo isto agora?", env=UNATTENDED))
        self.assertEqual(len(self.queued()), 1, "ninguém vai responder a pergunta da fase headless")

    def test_unattended_off_in_config_restores_silence(self):
        (self.w.home / ".claude/retrofit-watch.json").write_text(json.dumps({"unattended": "off"}))
        self.write(skill_via_tool("codereview:coderabbit-pr", self.w.mkt_skill), tool(error=True))
        self.assertIsNone(self.run_hook(env=UNATTENDED))
        self.assertFalse(self.queue_path().exists())

    def test_pending_notice_only_in_attended_sessions(self):
        self.assertIsNone(self.run_hook("pending"), "fila vazia: nada a dizer")
        self.write(skill_via_tool("codereview:coderabbit-pr", self.w.mkt_skill), tool(error=True))
        self.run_hook(env=UNATTENDED)
        self.assertIsNone(self.run_hook("pending", env=UNATTENDED), "a fase headless seguinte não ouve o aviso")
        out = self.run_hook("pending")
        self.assertIn("1 retro", out["systemMessage"])
        self.assertIn("/retrofit-watch:retrofit-watch pendentes", out["systemMessage"])
        self.assertNotIn("hookSpecificOutput", out, "o aviso é para o humano, não entra no contexto")

    def test_queue_lists_and_drains_by_id(self):
        self.write(skill_via_tool("codereview:coderabbit-pr", self.w.mkt_skill), tool(error=True))
        self.run_hook(env=UNATTENDED)
        [listed] = json.loads(self.cli("queue"))
        self.assertTrue(listed["transcript_exists"])
        self.cli("queue", "--done", listed["id"])
        self.assertEqual(json.loads(self.cli("queue")), [])
        self.assertIsNone(self.run_hook("pending"))

    def test_hooks_json_wires_pending_on_startup(self):
        hooks = json.loads((SCRIPT.parents[3] / "hooks/hooks.json").read_text())["hooks"]
        startup = [h for group in hooks["SessionStart"] if "startup" in group.get("matcher", "")
                   for h in group["hooks"]]
        self.assertTrue(any(h["args"][-1] == "pending" for h in startup))

    def test_windows_codepage_stdout_still_delivers_the_retro(self):
        """O `→` do pedido não existe em cp1252: o erro ia para o errors.log e a retro sumia já contada."""
        self.write(skill_via_tool("codereview:coderabbit-pr", self.w.mkt_skill), *[tool()] * 6)
        text = self.context_of(self.run_hook(env=WINDOWS_STDIO))
        self.assertIn("→ `/retrofit-skill:retrofit-skill codereview`", text)
        self.assertFalse((self.w.data / "errors.log").exists())

    def test_windows_codepage_stdin_reads_the_payload_as_utf8(self):
        """Lido em cp1252, `sem lições novas` chegava `sem liÃ§Ãµes novas` e a métrica marcava lição."""
        self.write(skill_via_tool("codereview:coderabbit-pr", self.w.mkt_skill), *[tool()] * 6)
        self.assertIsNotNone(self.run_hook())
        self.run_hook(active=True, last="retro codereview: sem lições novas", env=WINDOWS_STDIO)
        metrics = (self.w.data / "metrics.jsonl").read_text(encoding="utf-8").strip().splitlines()
        self.assertEqual(json.loads(metrics[-1])["outcome"], "none")

    def test_broken_input_never_breaks_the_session(self):
        self.assertIsNone(self.run_hook(raw="{not json"))
        self.assertIsNone(self.run_hook(raw=json.dumps({"session_id": "s2", "transcript_path": "/nope.jsonl",
                                                        "hook_event_name": "Stop"})))

    def test_fast_path_without_skills_keeps_no_heavy_state(self):
        self.write(*[tool(error=True)] * 5)
        self.assertIsNone(self.run_hook())
        state = json.loads((self.w.data / "sessions/s1.json").read_text())
        self.assertEqual(state["skills"], {})
        self.assertEqual(state["offset"], self.w.transcript.stat().st_size)


if __name__ == "__main__":
    unittest.main()
