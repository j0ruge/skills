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
from unittest import mock
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
# As variáveis que apontam outro repo: um hook do git as exporta, e com elas `git -C <dir>` age no repo delas.
GIT_LOCATION = ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY",
                "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_COMMON_DIR")


def git_env():
    """O ambiente do git da fixture, lido do ambiente de agora: sem as variáveis de localização, sem a
    config global (o `~/.gitconfig` real e a do XDG) e sem a de sistema."""
    env = {k: v for k, v in os.environ.items() if k not in GIT_LOCATION and not k.startswith("GIT_CONFIG")}
    env.update(GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t",
               GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull)
    return env


GIT_ENV = git_env()


def git(cwd, *args):
    subprocess.run(["git", "-C", str(cwd), *args], check=True, capture_output=True, env=git_env())


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
        init_repo(self.proj, "https://github.com/chewiesoft/app-interno.git")
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


def identified_load(name, path, message_id, call_id):
    call, result, meta = skill_via_tool(name, path)
    call["message"]["id"] = message_id
    call["message"]["content"][0]["id"] = call_id
    result["message"]["content"][0]["tool_use_id"] = call_id
    meta["sourceToolUseID"] = call_id
    return call, result, meta


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


def with_entrypoint(group, entrypoint):
    """Os registros reais trazem de onde a sessão veio: `cli` (interativa) ou `sdk-cli` (`claude -p`)."""
    return [dict(entry, entrypoint=entrypoint) for entry in group]


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

    def test_owner_outside_the_defaults_needs_the_config(self):
        repo = self.w.tmp / "repos/app-de-outra-org"
        init_repo(repo, "https://github.com/outra-org/app.git")
        skill = make_skill(repo / ".claude/skills", "do-cliente")
        commit_all(repo)
        self.assertIsNone(self.classify(skill))
        cfg_path = self.w.home / ".claude/retrofit-watch.json"
        cfg_path.write_text(json.dumps({"owners": ["outra-org"]}))
        try:
            ctx = self.w.ctx()
            self.assertEqual(rw.classify_path(str(skill), ctx)["mode"], "lean")
            self.assertIsNone(rw.classify_path(str(self.w.graphify), ctx))  # owners substitui a lista padrão
        finally:
            cfg_path.unlink()

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


class HookHarness:
    """Escreve o transcript, roda o hook num subprocesso e lê o contexto devolvido. Quem herda
    cria `self.w` (um World) no próprio setUp."""

    def write(self, *groups, compact=False):
        with open(self.w.transcript, "a", encoding="utf-8") as fh:
            for group in groups:
                for entry in group:
                    fh.write(json.dumps(entry, separators=(",", ":") if compact else None) + "\n")

    def run_hook(self, sub="stop", last="Feito.", active=False, env=None, raw=None, mode="default",
                 script=SCRIPT):
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
        proc = subprocess.run([sys.executable, str(script), sub], input=payload.encode("utf-8"),
                              capture_output=True, env=full_env, timeout=20)
        self.assertEqual(proc.returncode, 0, proc.stderr.decode("utf-8", "replace"))
        out = proc.stdout.decode("utf-8").strip()
        return json.loads(out) if out else None

    def context_of(self, out):
        self.assertIsNotNone(out, "esperava um pedido de retro")
        return out["hookSpecificOutput"]["additionalContext"]


class StopTest(HookHarness, unittest.TestCase):
    def setUp(self):
        self.w = World()

    def tearDown(self):
        self.w.cleanup()

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

    def identified_loads(self, other_message="msg_1"):
        return [identified_load(*args) for args in (
            ("codereview:coderabbit-pr", self.w.mkt_skill, "msg_1", "toolu_1"),
            ("superpowers:brainstorming", self.w.other_skill, other_message, "toolu_2"),
        )]

    def assert_codereview_retro(self):
        self.assertIn("/retrofit-skill:retrofit-skill codereview", self.context_of(self.run_hook()))

    def test_third_party_skill_in_same_message_keeps_attribution(self):
        self.write(*self.identified_loads(), tool(error=True))
        self.assert_codereview_retro()

    def test_third_party_skill_in_later_message_stops_attribution(self):
        self.write(*self.identified_loads("msg_2"), tool(error=True))
        self.assertIsNone(self.run_hook())

    def test_third_party_skill_in_same_message_keeps_attribution_after_resume(self):
        ours, other = self.identified_loads()
        self.write(ours, other[:2])
        self.assertIsNone(self.run_hook())
        self.write(other[2:], tool(error=True))
        self.assert_codereview_retro()

    def test_third_party_skill_in_later_message_stops_attribution_after_resume(self):
        ours, other = self.identified_loads("msg_2")
        self.write(ours, other[:2])
        self.assertIsNone(self.run_hook())
        self.write(other[2:], tool(error=True))
        self.assertIsNone(self.run_hook())

    def test_same_message_with_two_skill_blocks_before_metadata(self):
        (our_call, our_result, our_meta), (other_call, other_result, other_meta) = self.identified_loads()
        # A monitorada só é reconhecida pelo caminho, depois de ambas as chamadas.
        our_call["message"]["content"][0]["input"]["skill"] = "coderabbit-pr"
        our_call["message"]["content"].extend(other_call["message"]["content"])
        self.write([our_call, our_result, other_result, our_meta, other_meta], tool(error=True))
        self.assert_codereview_retro()

    def assert_late_monitored_metadata_does_not_reopen_attribution(self, source):
        ours, other = self.identified_loads("msg_2")
        if source is None:
            del ours[2]["sourceToolUseID"]
        else:
            ours[2]["sourceToolUseID"] = source
        self.write(ours[:2], other)
        self.assertIsNone(self.run_hook())
        self.write(ours[2:], tool(error=True))
        self.assertIsNone(self.run_hook())

    def test_late_monitored_metadata_does_not_reopen_attribution(self):
        self.assert_late_monitored_metadata_does_not_reopen_attribution("toolu_1")

    def test_late_monitored_metadata_without_source_does_not_reopen_attribution(self):
        self.assert_late_monitored_metadata_does_not_reopen_attribution(None)

    def test_late_monitored_metadata_with_empty_source_does_not_reopen_attribution(self):
        self.assert_late_monitored_metadata_does_not_reopen_attribution("")

    def test_typed_slash_can_start_new_attribution_after_external_skill(self):
        ours, other = self.identified_loads("msg_2")
        slash = skill_typed("graphify", self.w.graphify)
        del ours[2]["sourceToolUseID"]
        self.write(ours[:2], other, slash[:1])
        self.assertIsNone(self.run_hook())
        self.write(ours[2:], tool(error=True))
        self.assertIsNone(self.run_hook())
        self.write(slash[1:], tool(error=True))
        text = self.context_of(self.run_hook())
        self.assertIn("/retrofit-skill:retrofit-skill graphify", text)

    def test_late_monitored_metadata_does_not_override_external_slash_skill(self):
        ours, _ = self.identified_loads()
        self.write(ours[:2], skill_typed("brainstorming", self.w.other_skill))
        self.assertIsNone(self.run_hook())
        self.write(ours[2:], tool(error=True))
        self.assertIsNone(self.run_hook())

    def test_missing_source_stops_attribution(self):
        ours, other = self.identified_loads()
        other[2].pop("sourceToolUseID")
        self.write(ours, other, tool(error=True))
        self.assertIsNone(self.run_hook())

    def test_unknown_source_stops_attribution(self):
        ours, other = self.identified_loads()
        other[2]["sourceToolUseID"] = "toolu_unknown"
        self.write(ours, other, tool(error=True))
        self.assertIsNone(self.run_hook())

    def test_shared_call_id_is_not_proof_of_same_message(self):
        ours, other = self.identified_loads()
        other[0]["message"]["content"][0]["id"] = "toolu_1"
        other[1]["message"]["content"][0]["tool_use_id"] = "toolu_1"
        other[2]["sourceToolUseID"] = "toolu_1"
        self.write(ours[:1], other, tool(error=True))
        self.assertIsNone(self.run_hook())

    def test_same_message_skill_name_keeps_attribution_before_metadata(self):
        ours, other = self.identified_loads()
        self.write(ours, other[:2], tool(error=True))
        self.assert_codereview_retro()

    def test_path_can_exclude_the_same_call_recognized_by_plugin_name(self):
        cfg = self.w.home / ".claude/retrofit-watch.json"
        cfg.write_text(json.dumps({"exclude": ["coderabbit-pr"]}), encoding="utf-8")
        ours, _ = self.identified_loads()
        self.write(ours, tool(error=True))
        self.assertIsNone(self.run_hook())

    def test_legacy_state_resumes_at_offset_and_keeps_history(self):
        ours, other = self.identified_loads()
        self.write(ours, other[:2])
        state_path = self.w.data / "sessions/s1.json"
        state_path.parent.mkdir(parents=True)
        info = rw.classify_plugin("codereview", self.w.ctx())
        key = info["key"]
        legacy = dict(offset=self.w.transcript.stat().st_size, current=key,
                      skills={key: dict(info, reviews=1, work=3, friction=1)},
                      classified={}, pending=[], done=["full:ticket"])
        state_path.write_text(json.dumps(legacy), encoding="utf-8")
        self.write(other[2:], tool(error=True))
        self.assertIsNone(self.run_hook())
        saved = json.loads(state_path.read_text(encoding="utf-8"))
        self.assertEqual(saved["offset"], self.w.transcript.stat().st_size)
        self.assertIsNone(saved["current"])
        for field in ("skills", "pending", "done"):
            self.assertEqual(saved[field], legacy[field])

    def test_legacy_migration_recovers_active_message_origin(self):
        for message, keeps_attribution in (("msg_1", True), ("msg_2", False)):
            with self.subTest(message=message), self.sub_world() as world:
                ours, other = self.identified_loads(message)
                self.write(ours, compact=True)
                info = rw.classify_plugin("codereview", world.ctx())
                state = dict(offset=world.transcript.stat().st_size, current=info["key"],
                             classified={str(world.mkt_skill): info},
                             skills={info["key"]: dict(info, reviews=0, work=0, friction=0)})
                path = world.data / "sessions/s1.json"
                path.parent.mkdir(parents=True)
                path.write_text(json.dumps(state), encoding="utf-8")
                self.write(other, tool(error=True), compact=True)

                out, saved = self.checked_stop()

                if keeps_attribution:
                    self.assertIn("`/retrofit-skill:retrofit-skill codereview`", self.context_of(out))
                    self.assertEqual(saved["current_origin"], ["msg_1", "toolu_1"])
                else:
                    self.assertIsNone(out)
                    self.assertIsNone(saved["current"])

    def test_legacy_pending_call_order(self):
        cuts = {}
        for scenario in ("late", "new", "alone", "name_only", "fresh", "cache_only",
                         "bad_line", "scalar", "partial"):
            with self.subTest(scenario=scenario), self.sub_world() as world:
                local = identified_load("coderabbit-pr", world.mkt_skill, "msg_local", "toolu_local")
                other = identified_load("superpowers:brainstorming", world.other_skill,
                                        "msg_other", "toolu_other")
                confirmed = scenario not in ("alone", "name_only")
                external = other if confirmed and scenario != "cache_only" else (
                    other[:2] if scenario == "name_only" else ())
                invalid = {"bad_line": b'{"type":\n', "scalar": b"null\n", "partial": b"{}"}
                groups = (external, local[:2]) if scenario in ("new", *invalid) else (local[:2], external)
                self.write(*groups, tool(), compact=True)
                if scenario in invalid:
                    with world.transcript.open("ab") as fh:
                        fh.write(invalid[scenario])
                before = dict(offset=world.transcript.stat().st_size, current=None, skills={},
                              classified={str(world.other_skill): None} if confirmed else {},
                              pending=[], done=[])
                path = world.data / "sessions/s1.json"
                path.parent.mkdir(parents=True)
                path.write_text(json.dumps(before), encoding="utf-8")
                if scenario == "partial":
                    with world.transcript.open("ab") as fh:
                        fh.write(b"\n")
                if scenario in ("late", "new"):
                    cuts[scenario] = dict(before, classified={"external": None})
                if scenario == "fresh":
                    local = identified_load("coderabbit-pr", world.mkt_skill, "msg_fresh", "toolu_fresh")
                    self.write(local[:2], compact=True)
                self.write(local[2:], tool(error=True), compact=True)
                out, saved = self.checked_stop()
                if scenario in ("new", "alone", "fresh"):
                    self.assertIn("`/retrofit-skill:retrofit-skill codereview`", self.context_of(out))
                    entry = saved["skills"]["full:codereview"]
                    self.assertEqual(tuple(entry[k] for k in ("work", "friction", "reviews")), (0, 0, 1))
                else:
                    self.assertIsNone(out)
                    self.assertEqual(saved["skills"], {})
                    self.assertTrue(saved["attribution_closed"])
                if scenario in invalid or scenario == "cache_only":
                    self.assertEqual(saved["skill_calls"], {})
                    self.assertEqual(saved["skill_message_order"], [])
                    self.assertEqual(saved["skill_call_history"], {})
        self.assertEqual(cuts["late"], cuts["new"])

    def test_legacy_prefix_read_once_without_recounting(self):
        local = identified_load("codereview:coderabbit-pr", self.w.mkt_skill, "msg_local", "toolu_local")
        delayed = identified_load("graphify", self.w.graphify, "msg_delayed", "toolu_delayed")
        self.write(skill_typed("dev-script:dev-script"),
                   skill_typed("retrofit-skill:retrofit-skill", args="dev-script"),
                   local, tool(error=True), delayed[:2], compact=True)
        offset = self.w.transcript.stat().st_size
        info = rw.classify_plugin("codereview", self.w.ctx())
        legacy = dict(offset=offset, current=info["key"],
                      skills={info["key"]: dict(info, reviews=1, work=2, friction=1)},
                      classified={}, pending=[info["label"]], done=["full:ticket"], entrypoint="cli")
        path = self.w.data / "sessions/s1.json"
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps(legacy), encoding="utf-8")
        payload = dict(session_id="s1", transcript_path=str(self.w.transcript), last_assistant_message="Feito.")
        reads = []
        historical_bumps = []
        bump = rw.Scanner._bump

        def track_bump(scanner, field):
            historical_bumps.append((field, scanner.silent))
            bump(scanner, field)

        def track_open(path, mode):
            actual = open(path, mode)
            stream = mock.MagicMock(wraps=actual)

            def track_read(*args):
                start = stream.tell()
                value = actual.read(*args)
                reads.append((start, len(value)))
                return value

            stream.read.side_effect = track_read
            stream.__enter__.return_value = stream
            stream.__exit__.side_effect = actual.__exit__
            return stream

        with self.w.transcript.open("ab") as fh:
            fh.write(b" ")
        with mock.patch.dict(os.environ, RETROFIT_WATCH="force"), mock.patch.object(
                rw, "open", side_effect=track_open, create=True):
            with mock.patch.object(rw.Scanner, "_bump", track_bump):
                self.assertIsNone(rw.cmd_stop(payload, self.w.ctx()))
            self.assertEqual(historical_bumps, [("work", True), ("friction", True)])
            saved = json.loads(path.read_bytes())
            for field, value in legacy.items():
                self.assertEqual(saved[field], value, field)
            self.assertFalse((self.w.data / "metrics.jsonl").exists())
            self.assertEqual(saved["skill_calls"].get("toolu_delayed"), "msg_delayed")
            self.assertEqual(saved["skill_message"], "msg_local")
            self.assertEqual(saved["skill_message_order"], ["msg_local", "msg_delayed"])
            self.assertEqual(saved["skill_call_history"], {"toolu_local": ["msg_local"]})
            self.write(delayed[2:], tool(error=True), compact=True)
            out = rw.cmd_stop(payload, self.w.ctx())
            self.assertEqual([read for read in reads if read[0] < offset], [(0, offset)])
            reads.clear()
            rw.cmd_stop(dict(payload, session_id="new"), self.w.ctx())
            self.assertEqual(reads, [(0, self.w.transcript.stat().st_size)])
        self.assertIn("`/retrofit-skill:retrofit-skill graphify`", self.context_of(out))
        saved = json.loads(path.read_bytes())
        self.assertEqual(saved["offset"], self.w.transcript.stat().st_size)
        self.assertEqual(saved["skills"][info["key"]], legacy["skills"][info["key"]])
        self.assertEqual(saved["done"], legacy["done"])

    def test_legacy_truncated_transcript_does_not_rewind(self):
        ours, other = self.identified_loads("msg_2")
        local = identified_load("coderabbit-pr", self.w.mkt_skill, "msg_local", "toolu_local")
        self.write(ours, tool(error=True), other, local[:2], compact=True)
        offset = self.w.transcript.stat().st_size + 30
        path = self.w.data / "sessions/s1.json"
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps(dict(offset=offset, current=None, skills={},
                                        classified={str(self.w.other_skill): None})), encoding="utf-8")
        for _ in range(2):
            self.assertIsNone(self.run_hook())
            saved = json.loads(path.read_bytes())
            self.assertEqual(saved["offset"], offset)
            self.assertEqual(saved["skills"], {})
            self.assertTrue(saved["attribution_closed"])
            self.assertEqual(saved["skill_calls"], {})
        with self.w.transcript.open("ab") as fh:
            fh.write(b" " * 29 + b"\n")
        self.write(ours, tool(error=True), compact=True)
        out, saved = self.checked_stop()
        self.assertIn("`/retrofit-skill:retrofit-skill codereview`", self.context_of(out))
        self.assertNotIn("legacy_prefix_truncated", saved)

    def test_legacy_missing_prefix_uses_saved_classification(self):
        local = identified_load("coderabbit-pr", self.w.mkt_skill, "msg_local", "toolu_local")
        self.write(local[:2], compact=True)
        offset = self.w.transcript.stat().st_size
        path = self.w.data / "sessions/s1.json"
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps(dict(offset=offset, current=None, skills={},
                                        classified={str(self.w.other_skill): None})), encoding="utf-8")
        self.write(local[2:], tool(error=True), compact=True)
        payload = dict(session_id="s1", transcript_path=str(self.w.transcript), last_assistant_message="Feito.")
        def fail_first_open(path, mode):
            if path == str(self.w.transcript) and mode == "rb":
                rw.open.side_effect = open
                raise OSError("prefixo indisponível")
            return open(path, mode)

        with mock.patch.dict(os.environ, RETROFIT_WATCH="force"), mock.patch.object(
                rw, "open", side_effect=fail_first_open, create=True):
            self.assertIsNone(rw.cmd_stop(payload, self.w.ctx()))
        saved = json.loads(path.read_bytes())
        self.assertTrue(saved["attribution_closed"])
        self.assertEqual(saved["skills"], {})
        self.assertEqual(saved["offset"], self.w.transcript.stat().st_size)

    def test_legacy_replay_does_not_replace_saved_current(self):
        for scenario in ("closed", "pending"):
            with self.subTest(scenario=scenario), self.sub_world() as world:
                ours, other = self.identified_loads("msg_2")
                local = identified_load("graphify", world.graphify, "msg_local", "toolu_local")
                groups = (ours, other[:2]) if scenario == "closed" else (local[:2],)
                self.write(*groups, compact=True)
                info = rw.classify_plugin("codereview", world.ctx())
                legacy = dict(offset=world.transcript.stat().st_size, current=info["key"],
                              skills={info["key"]: dict(info, reviews=1, work=2, friction=1)})
                path = world.data / "sessions/s1.json"
                path.parent.mkdir(parents=True)
                path.write_text(json.dumps(legacy), encoding="utf-8")
                out, saved = self.checked_stop()
                self.assertIsNone(out)
                for field, value in legacy.items():
                    self.assertEqual(saved[field], value)
                self.assertFalse(saved["attribution_closed"])
                self.assertEqual(saved["skill_calls"], {})

    def test_legacy_replay_respects_correlation_ceiling(self):
        _, other = self.identified_loads("msg_2")
        local = identified_load("coderabbit-pr", self.w.mkt_skill, "msg_local", "toolu_local")
        self.write(other, local[:2], compact=True)
        path = self.w.data / "sessions/s1.json"
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps(dict(offset=self.w.transcript.stat().st_size, current=None,
                                        classified={str(self.w.other_skill): None})), encoding="utf-8")
        self.write(local[2:], tool(error=True), compact=True)
        payload = dict(session_id="s1", transcript_path=str(self.w.transcript), last_assistant_message="Feito.")
        with mock.patch.dict(os.environ, RETROFIT_WATCH="force"), mock.patch.object(rw, "MAX_SKILL_MESSAGES", 1):
            self.assertIsNone(rw.cmd_stop(payload, self.w.ctx()))
        saved = json.loads(path.read_bytes())
        self.assertTrue(saved["skill_correlation_lost"])
        self.assertEqual(saved["skill_calls"], {})
        self.assertEqual(saved["skills"], {})

    def test_legacy_closed_attribution_ignores_unknown_source(self):
        ours, other = self.identified_loads("msg_2")
        self.write(ours[:2], other[:2])
        state_path = self.w.data / "sessions/s1.json"
        state_path.parent.mkdir(parents=True)
        info = rw.classify_plugin("codereview", self.w.ctx())
        key = info["key"]
        legacy = dict(offset=self.w.transcript.stat().st_size, current=None,
                      skills={key: dict(info, reviews=0, work=0, friction=0)},
                      classified={}, pending=[], done=[])
        state_path.write_text(json.dumps(legacy), encoding="utf-8")
        self.write(other[2:], ours[2:], tool(error=True))
        self.assertIsNone(self.run_hook())
        saved = json.loads(state_path.read_text(encoding="utf-8"))
        self.assertEqual(saved["skills"], legacy["skills"])
        self.assertEqual(saved["offset"], self.w.transcript.stat().st_size)
        self.assertEqual(saved["skill_calls"], {})

    def test_legacy_closed_before_upgrade_ignores_delayed_metadata(self):
        for scenario in ("linked", "missing", "empty", "modern", "modern_empty", "slash", "new",
                         "no_history", "history_only", "active"):
            with self.subTest(scenario=scenario), self.sub_world() as world:
                ours, external = self.identified_loads("msg_2")
                key = "full:codereview"
                groups = (ours[:2],) if scenario == "active" else (ours[:2], external, tool())
                if scenario == "no_history":
                    groups = (tool(),)
                elif scenario == "history_only":
                    groups = (ours[:2], external[:2], tool())
                elif scenario == "modern_empty":
                    groups = (external,)
                self.write(*groups, compact=True)
                out, before = self.checked_stop()
                self.assertIsNone(out)
                self.assertEqual(before["current"], key if scenario == "active" else None)
                if scenario == "history_only":
                    self.assertEqual(before["classified"], {})
                if scenario in ("no_history", "modern_empty"):
                    self.assertEqual(before["skills"], {})
                else:
                    self.assertEqual(tuple(before["skills"][key][field]
                                           for field in ("work", "friction", "reviews")), (0, 0, 0))
                if scenario not in ("modern", "modern_empty"):
                    fields = ("created", "offset", "skills", "current", "classified",
                              "pending", "done", "entrypoint")
                    saved = {field: before[field] for field in fields if field in before}
                    (world.data / "sessions/s1.json").write_text(json.dumps(saved), encoding="utf-8")
                    self.assertNotIn("attribution_closed",
                                     json.loads((world.data / "sessions/s1.json").read_bytes()))
                if scenario in ("missing", "modern", "modern_empty", "slash", "no_history"):
                    del ours[2]["sourceToolUseID"]
                elif scenario == "empty":
                    ours[2]["sourceToolUseID"] = ""
                if scenario != "active":
                    self.write(ours[2:])
                if scenario == "slash":
                    self.write(skill_typed("graphify", world.graphify))
                elif scenario == "new":
                    self.write(identified_load("graphify", world.graphify, "msg_3", "toolu_3"))
                self.write(tool(error=True))
                out, after = self.checked_stop()
                if scenario in ("slash", "new", "no_history", "active"):
                    target = "graphify" if scenario in ("slash", "new") else "codereview"
                    self.assertIn(f"`/retrofit-skill:retrofit-skill {target}`", self.context_of(out))
                    self.assertFalse(after["attribution_closed"])
                else:
                    self.assertIsNone(out)
                    self.assertIsNone(after["current"])
                    self.assertTrue(after["attribution_closed"])
                if scenario == "modern_empty":
                    self.assertEqual(after["skills"], {})
                elif scenario not in ("no_history", "active"):
                    self.assertEqual(tuple(after["skills"][key][field]
                                           for field in ("work", "friction", "reviews")), (0, 0, 0))

    def test_reused_consumed_call_id_stops_attribution(self):
        self.write(*self.identified_loads())
        self.assertIsNone(self.run_hook())
        # Um resultado atrasado não apaga a marca de consumo.
        _, other = self.identified_loads()
        other[1]["message"]["content"][0]["is_error"] = True
        self.write(other[1:2])
        self.assertIsNone(self.run_hook())
        state_path = self.w.data / "sessions/s1.json"
        saved = json.loads(state_path.read_text(encoding="utf-8"))
        self.assertEqual(saved["skill_message"], "msg_1")
        self.assertEqual(saved["skill_calls"], {})
        self.assertEqual(saved["skill_call_history"], {"toolu_1": ["msg_1"], "toolu_2": ["msg_1"]})
        path = make_skill(self.w.other_skill.parent, "writing-plans")
        call, result, meta = skill_via_tool("superpowers:writing-plans", path)
        call["message"]["id"] = "msg_1"
        call["message"]["content"][0]["id"] = "toolu_2"
        result["message"]["content"][0]["tool_use_id"] = "toolu_2"
        meta["sourceToolUseID"] = "toolu_2"
        self.write([call, result, meta], tool(error=True))
        self.assertIsNone(self.run_hook())

    def test_pending_slash_survives_older_external_metadata(self):
        ours, other = self.identified_loads("msg_2")
        slash = skill_typed("graphify", self.w.graphify)
        self.write(ours, other[:2])
        self.assertIsNone(self.run_hook())
        self.write(slash[:1], other[2:])
        self.assertIsNone(self.run_hook())
        self.write(slash[1:], tool(error=True))
        self.assertIn("/retrofit-skill:retrofit-skill graphify", self.context_of(self.run_hook()))
        self.write(skill_typed("retrofit-skill:retrofit-skill", args="graphify"))
        self.assertIsNone(self.run_hook())
        saved = json.loads((self.w.data / "sessions/s1.json").read_text(encoding="utf-8"))
        self.assertIsNone(saved["pending_slash"])

    def test_failed_unknown_skill_keeps_pending_monitored_call(self):
        ours, _ = self.identified_loads()
        ours[0]["message"]["content"][0]["input"]["skill"] = "coderabbit-pr"
        call, result, _ = skill_via_tool("nao-instalada", self.w.other_skill)
        call["message"]["id"] = "msg_2"
        result["message"]["content"][0].update(content="Unknown skill: nao-instalada", is_error=True)
        # Sem metadado ou histórico, o Stop procura o marcador no formato compacto do Claude.
        self.w.transcript.write_text(
            "".join(json.dumps(row, separators=(",", ":")) + "\n" for row in (*ours[:2], call, result)),
            encoding="utf-8",
        )
        self.assertIsNone(self.run_hook())
        unmatched = dict(ours[2], sourceToolUseID="toolu_unmatched")
        self.write([unmatched], tool(error=True))
        self.assertIsNone(self.run_hook())
        self.write(ours[2:], tool(error=True))
        self.assert_codereview_retro()

    def test_newer_skill_metadata_wins_regardless_of_confirmation_order(self):
        for resume in (False, True):
            for order in ("sem", "antes", "depois"):
                world = World()
                self.addCleanup(world.cleanup)
                with self.subTest(resume=resume, order=order), mock.patch.object(self, "w", world):
                    older, newer = self.identified_loads("msg_2")
                    # O ID é opaco, não ordenável.
                    older[0]["message"]["id"] = "msg_z"
                    newer[0]["message"]["id"] = "msg_a"
                    older[0]["message"]["content"][0]["input"]["skill"] = "coderabbit-pr"
                    newer[0]["message"]["content"][0]["input"]["skill"] = "graphify"
                    newer[2]["message"]["content"][0]["text"] = f"{rw.BASE_PREFIX}{world.graphify}"
                    self.write(older[:2], newer[:2])
                    if order != "sem":
                        self.write(older[2:] if order == "antes" else newer[2:])
                    if resume:
                        self.assertIsNone(self.run_hook())
                    self.write(older[2:] if order == "depois" else newer[2:], tool(error=True))
                    context = self.context_of(self.run_hook())
                    self.assertIn("/retrofit-skill:retrofit-skill graphify", context)
                    self.assertNotIn("/retrofit-skill:retrofit-skill codereview", context)

    def test_new_skill_retires_older_consumed_and_unlinked_calls(self):
        older, newer = self.identified_loads("msg_2")
        newer[0]["message"]["content"][0]["input"]["skill"] = "graphify"
        newer[2]["message"]["content"][0]["text"] = f"{rw.BASE_PREFIX}{self.w.graphify}"
        call, result, meta = skill_via_tool("coderabbit-pr", self.w.mkt_skill)
        call["message"]["id"] = "msg_1"
        unlinked = skill_via_tool("nao-instalada", self.w.other_skill)
        unlinked[0]["message"]["content"][0]["id"] = "toolu_no_message"
        self.write(older[:2], newer[:2], [call, result, meta], unlinked[:1], newer[2:])
        self.assertIsNone(self.run_hook())
        saved = json.loads((self.w.data / "sessions/s1.json").read_bytes())
        self.assertEqual(saved["skill_calls"], {})
        self.assertEqual(saved["skill_call_history"], {"toolu_2": ["msg_2"]})

    def assert_graphify_retro(self):
        context = self.context_of(self.run_hook())
        self.assertIn("`/retrofit-skill:retrofit-skill graphify`", context)
        self.assertNotIn("`/retrofit-skill:retrofit-skill codereview`", context)

    def interleaved_skill_loads(self):
        return (identified_load("coderabbit-pr", self.w.mkt_skill, "msg_z", "toolu_a"),
                identified_load("graphify", self.w.graphify, "msg_a", "toolu_b"),
                identified_load("coderabbit-pr", self.w.mkt_skill, "msg_z", "toolu_c"))

    def test_message_order_survives_failed_call(self):
        for resume in (False, True):
            for failed in (False, True):
                world = World()
                self.addCleanup(world.cleanup)
                with self.subTest(resume=resume, failed=failed), mock.patch.object(self, "w", world):
                    first, newer, second = self.interleaved_skill_loads()
                    first[1]["message"]["content"][0]["is_error"] = failed
                    self.write(first[:1], newer[:2], second[:2], first[1:2], compact=True)
                    if resume:
                        self.assertIsNone(self.run_hook())
                    self.write(second[2:], newer[2:])
                    if not failed:
                        self.write(first[2:])
                    self.write(tool(error=True))
                    self.assert_graphify_retro()

    def test_message_order_survives_consumed_call(self):
        for resume in (False, True):
            for interleaved in (False, True):
                world = World()
                self.addCleanup(world.cleanup)
                with self.subTest(resume=resume, interleaved=interleaved), mock.patch.object(self, "w", world):
                    first, newer, second = self.interleaved_skill_loads()
                    self.write(first)
                    groups = (newer, second) if interleaved else (second, newer)
                    self.write(*(group[:2] for group in groups), compact=True)
                    if resume:
                        self.assertIsNone(self.run_hook())
                    self.write(newer[2:], second[2:], tool(error=True))
                    self.assert_graphify_retro()

    def test_failed_call_id_cannot_prove_same_message(self):
        for resume in (False, True):
            for duplicate in (False, True):
                world = World()
                self.addCleanup(world.cleanup)
                with self.subTest(resume=resume, duplicate=duplicate), mock.patch.object(self, "w", world):
                    monitored, external = self.identified_loads()
                    failed_id = "toolu_2" if duplicate else "toolu_f"
                    call, result, _ = identified_load("nao-instalada", world.other_skill, "msg_1", failed_id)
                    result["message"]["content"][0]["is_error"] = True
                    self.write(monitored, [call, result], compact=True)
                    if resume:
                        self.assertIsNone(self.run_hook())
                    # Mede a decisão pelo nome antes de a confirmação por caminho poder interferir.
                    self.write(external[:2], tool(error=True))
                    if duplicate:
                        self.assertIsNone(self.run_hook())
                        self.assertFalse((world.data / "errors.log").exists())
                    else:
                        self.assert_codereview_retro()

    def checked_stop(self, **kwargs):
        out = self.run_hook(**kwargs)
        self.assertFalse((self.w.data / "errors.log").exists())
        saved = json.loads((self.w.data / "sessions/s1.json").read_bytes())
        self.assertEqual(saved["offset"], self.w.transcript.stat().st_size)
        return out, saved

    def test_message_order_survives_last_failed_call(self):
        for cut in (None, 0, 1, 2):
            for failed in (False, True):
                with self.subTest(cut=cut, failed=failed), self.sub_world():
                    first, newer, retry = self.interleaved_skill_loads()
                    first[1]["message"]["content"][0]["is_error"] = failed
                    self.write(first[:1], newer[:2], compact=True)
                    for index, rows in enumerate((first[1:2], retry[:2] + newer[2:], retry[2:])):
                        if cut == index:
                            out, saved = self.checked_stop()
                            self.assertIsNone(out)
                            if cut == 1:
                                self.assertEqual(saved["skill_message_order"], ["msg_z", "msg_a"])
                        self.write(rows, compact=True)
                    self.write(tool(error=True))
                    out, _ = self.checked_stop()
                    context = self.context_of(out)
                    self.assertIn("`/retrofit-skill:retrofit-skill graphify`", context)
                    self.assertNotIn("`/retrofit-skill:retrofit-skill codereview`", context)

    def sub_world(self):
        world = World()
        self.addCleanup(world.cleanup)
        return mock.patch.object(self, "w", world)

    def test_failed_call_before_activation_cannot_prove_same_message(self):
        for cut in (None, 0, 1, 2):
            for duplicate in (False, True):
                with self.subTest(cut=cut, duplicate=duplicate), self.sub_world() as world:
                    fail = identified_load("nao-instalada", world.other_skill, "msg_z", "toolu_f")
                    fail[1]["message"]["content"][0]["is_error"] = True
                    monitored = identified_load("coderabbit-pr", world.mkt_skill, "msg_z", "toolu_m")
                    external = identified_load("superpowers:brainstorming", world.other_skill,
                                               "msg_z", "toolu_f" if duplicate else "toolu_n")
                    self.write(fail[:1], monitored[:2], compact=True)
                    for index, rows in enumerate((fail[1:2], monitored[2:], external)):
                        if cut == index:
                            self.assertIsNone(self.checked_stop()[0])
                        self.write(rows, compact=True)
                    self.write(tool(error=True))
                    out, saved = self.checked_stop()
                    if duplicate:
                        self.assertIsNone(out)
                        self.assertIsNone(saved["current"])
                    else:
                        self.assertIn("`/retrofit-skill:retrofit-skill codereview`", self.context_of(out))

    def test_distinct_failed_messages_do_not_accumulate_behind_pending_call(self):
        pending = identified_load("graphify", self.w.graphify, "msg_z", "toolu_pending")
        self.write(pending[:2], compact=True)
        self.assertIsNone(self.checked_stop()[0])
        for start, end in ((0, 10), (10, 100), (100, 1000)):
            for index in range(start, end):
                fail = identified_load("nao-instalada", self.w.other_skill, f"msg_{index}", f"toolu_{index}")
                fail[1]["message"]["content"][0]["is_error"] = True
                self.write(fail[:2], compact=True)
            out, saved = self.checked_stop()
            self.assertIsNone(out)
            self.assertEqual(saved["skill_calls"], {"toolu_pending": "msg_z"})
            self.assertEqual(saved["skill_message_order"], ["msg_z"])
            self.assertFalse(saved.get("skill_call_history"))
            self.assertFalse(saved.get("skill_correlation_lost"))
        self.write(pending[2:], tool(error=True))
        self.assert_graphify_retro()

    def test_duplicate_pending_id_does_not_select_either_message(self):
        for cut in (False, True):
            with self.subTest(cut=cut), self.sub_world() as world:
                first, newer, retry = self.interleaved_skill_loads()
                other = identified_load("graphify", world.graphify, "msg_a", "toolu_a")
                self.write(first[:2], newer[:2], retry[:2], other[:2], compact=True)
                if cut:
                    out, saved = self.checked_stop()
                    self.assertIsNone(out)
                    self.assertNotIn("toolu_a", saved["skill_calls"])
                    self.assertEqual(saved["skill_call_history"]["toolu_a"], ["msg_z", "msg_a"])
                self.write(retry[2:], other[2:], tool(error=True))
                out, _ = self.checked_stop()
                context = self.context_of(out)
                self.assertIn("`/retrofit-skill:retrofit-skill codereview`", context)
                self.assertNotIn("`/retrofit-skill:retrofit-skill graphify`", context)

    def test_ambiguous_id_survives_retirement_of_one_owner(self):
        first, later, retry = self.interleaved_skill_loads()
        duplicate = identified_load("graphify", self.w.graphify, "msg_a", "toolu_a")
        latest = identified_load("coderabbit-pr", self.w.mkt_skill, "msg_a", "toolu_d")
        self.write(first[:1], later[:1], retry[:1], duplicate[:1], latest, compact=True)
        out, saved = self.checked_stop()
        self.assertIsNone(out)
        self.assertEqual(saved["skill_call_history"]["toolu_a"], ["msg_a"])
        self.assertEqual(saved["skill_message_order"], ["msg_a"])
        self.write(duplicate[2:], tool(error=True))
        self.assert_codereview_retro()

    def test_intermediate_state_recovers_failed_and_unowned_ids(self):
        for old_id in ("toolu_old_failed", "toolu_old_unowned"):
            with self.subTest(old_id=old_id), self.sub_world() as world:
                ours, _ = self.identified_loads()
                self.write(ours)
                out, old = self.checked_stop()
                self.assertIsNone(out)
                old.pop("skill_call_history")
                old["failed_skill_calls"] = ["toolu_old_failed"]
                old["skill_calls"]["toolu_old_unowned"] = False
                path = world.data / "sessions/s1.json"
                path.write_text(json.dumps(old), encoding="utf-8")
                out, saved = self.checked_stop()
                self.assertIsNone(out)
                self.assertEqual(saved["skill_call_history"],
                                 {"toolu_old_failed": ["msg_1"], "toolu_old_unowned": []})
                self.assertEqual(saved["skill_calls"], {})
                self.write(identified_load("superpowers:brainstorming", world.other_skill, "msg_1", old_id),
                           tool(error=True))
                out, saved = self.checked_stop()
                self.assertIsNone(out)
                self.assertIsNone(saved["current"])

    def test_correlation_overflow_persists_conservative_fallback(self):
        for limit in ("MAX_SKILL_MESSAGES", "MAX_SKILL_CALL_IDS"):
            with self.subTest(limit=limit), self.sub_world() as world:
                script = world.tmp / "limited.py"
                source = SCRIPT.read_text(encoding="utf-8")
                script.write_text(source.replace(f"{limit} = " + ("64" if limit.endswith("MESSAGES") else "1024"),
                                                 f"{limit} = 2"), encoding="utf-8")
                ours, external = self.identified_loads()
                first = identified_load("graphify", world.graphify, "msg_z", "toolu_a")
                second = identified_load("graphify", world.graphify,
                                         "msg_y" if limit.endswith("MESSAGES") else "msg_z", "toolu_b")
                self.write(ours, first[:2], compact=True)
                out, saved = self.checked_stop(script=script)
                self.assertIsNone(out)
                self.assertFalse(saved.get("skill_correlation_lost"))
                self.write(second[:2], compact=True)
                out, saved = self.checked_stop(script=script)
                self.assertIsNone(out)
                self.assertTrue(saved.get("skill_correlation_lost"))
                self.assertIsNone(saved["current_origin"])
                self.assertEqual(saved["skill_calls"], {})
                self.assertEqual(saved["skill_message_order"], [])
                self.assertEqual(saved["skill_call_history"], {})
                fresh = identified_load("graphify", world.graphify, "msg_fresh", "toolu_fresh")
                unlinked = dict(second[2], sourceToolUseID=None)
                self.write(fresh[:2], [unlinked], compact=True)
                out, saved = self.checked_stop()
                self.assertIsNone(out)
                self.assertEqual(saved["current"], "full:codereview")
                self.assertEqual(saved["skill_calls"], {})
                self.assertEqual(saved["skill_message_order"], [])
                self.write(external, second[2:], tool(error=True))
                out, saved = self.checked_stop()
                self.assertIsNone(out)
                self.assertTrue(saved["skill_correlation_lost"])
                self.assertEqual(saved["skills"]["full:codereview"]["work"], 0)
                self.write(skill_typed("graphify", world.graphify), tool(error=True))
                self.assert_graphify_retro()

    def test_oversized_saved_correlation_is_disabled_before_metadata(self):
        first, later, retry = self.interleaved_skill_loads()
        self.write(first[:1], later[:1], retry[:1], compact=True)
        self.assertIsNone(self.checked_stop()[0])
        script = self.w.tmp / "limited.py"
        source = SCRIPT.read_text(encoding="utf-8")
        script.write_text(source.replace("MAX_SKILL_CALL_IDS = 1024", "MAX_SKILL_CALL_IDS = 2"),
                          encoding="utf-8")
        self.write(later[2:], tool(error=True))
        out, saved = self.checked_stop(script=script)
        self.assertIsNone(out)
        self.assertTrue(saved["skill_correlation_lost"])
        self.assertEqual(saved["skill_calls"], {})

    def test_consumed_unlinked_call_keeps_id_without_inventing_message(self):
        anonymous = skill_via_tool("codereview:coderabbit-pr", self.w.mkt_skill)
        self.write(anonymous[:2], compact=True)
        out, saved = self.checked_stop()
        self.assertIsNone(out)
        self.assertEqual(saved["current"], "full:codereview")
        self.assertIsNone(saved["current_origin"])
        self.assertEqual(saved["skill_message_order"], [])
        self.write(anonymous[2:])
        out, saved = self.checked_stop()
        self.assertIsNone(out)
        self.assertEqual(saved["skill_call_history"], {"toolu_s": []})
        self.assertEqual(saved["skill_calls"], {})
        self.assertEqual(saved["skill_message_order"], [])

    def test_unowned_consumed_id_survives_intermediate_collision(self):
        for cuts in ((), ("before",), ("after",), ("before", "after")):
            for scenario in ("new", "reused", "interleaved", "owned_interleaved", "retained_then_pruned"):
                with self.subTest(cuts=cuts, scenario=scenario), self.sub_world() as world:
                    name = "codereview:coderabbit-pr"
                    active = identified_load(name, world.mkt_skill, "msg_a", "toolu_active")
                    if scenario == "owned_interleaved":
                        consumed = identified_load(name, world.mkt_skill, "msg_a", "toolu_s")
                        owners = ["msg_a"]
                    else:
                        consumed = skill_via_tool(name, world.mkt_skill)
                        owners = []
                    refresh = identified_load(name, world.mkt_skill, "msg_a", "toolu_refresh")
                    self.write(active, consumed, refresh, compact=True)

                    if "before" in cuts:
                        out, saved = self.checked_stop()
                        self.assertIsNone(out)
                        self.assertEqual(saved["skill_call_history"]["toolu_s"], owners)

                    if scenario == "retained_then_pruned":
                        pending = identified_load("nao-instalada", world.other_skill, "msg_b", "toolu_pending")
                        self.write(pending[:1], compact=True)
                    if scenario in ("interleaved", "owned_interleaved", "retained_then_pruned"):
                        collision = identified_load("nao-instalada", world.other_skill, "msg_b", "toolu_s")
                        self.write(collision[:1], compact=True)
                    if scenario == "retained_then_pruned":
                        pending[1]["message"]["content"][0]["is_error"] = True
                        self.write(pending[1:2], compact=True)
                    if "after" in cuts:
                        out, saved = self.checked_stop()
                        self.assertIsNone(out)
                        self.assertEqual(saved["current_origin"], ["msg_a", "toolu_refresh"])
                        self.assertEqual(saved["skill_message_order"], ["msg_a"])
                        self.assertEqual(saved["skill_call_history"].get("toolu_s"), owners)

                    call_id = "toolu_new" if scenario == "new" else "toolu_s"
                    external = identified_load("superpowers:brainstorming", world.other_skill, "msg_a", call_id)
                    self.write(external, tool(error=True), compact=True)
                    out, saved = self.checked_stop()
                    skill = saved["skills"]["full:codereview"]
                    if scenario == "new":
                        self.assertIn("`/retrofit-skill:retrofit-skill codereview`", self.context_of(out))
                        self.assertEqual(skill["reviews"], 1)
                    else:
                        self.assertIsNone(out)
                        self.assertIsNone(saved["current"])
                        # Só o erro da pendência anterior à externa pode contar como atrito.
                        friction = int(scenario == "retained_then_pruned")
                        self.assertEqual((skill["work"], skill["friction"], skill["reviews"]), (0, friction, 0))

    def test_unowned_collision_survives_confirmation_of_live_owner(self):
        for resume in (False, True):
            for duplicate in (False, True):
                with self.subTest(resume=resume, duplicate=duplicate), self.sub_world() as world:
                    name = "codereview:coderabbit-pr"
                    active = identified_load(name, world.mkt_skill, "msg_a", "toolu_active")
                    consumed = skill_via_tool(name, world.mkt_skill)
                    refresh = identified_load(name, world.mkt_skill, "msg_a", "toolu_refresh")
                    pending = identified_load("coderabbit-pr", world.mkt_skill, "msg_b", "toolu_pending")
                    collision = identified_load("nao-instalada", world.other_skill, "msg_b", "toolu_s")
                    self.write(active, consumed, refresh, compact=True)
                    if resume:
                        out, saved = self.checked_stop()
                        self.assertIsNone(out)
                        self.assertEqual(saved["skill_call_history"]["toolu_s"], [])

                    self.write(pending[:2], collision[:1], compact=True)
                    if resume:
                        out, saved = self.checked_stop()
                        self.assertIsNone(out)
                        self.assertEqual(saved["skill_message_order"], ["msg_a", "msg_b"])
                        self.assertEqual(saved["skill_calls"], {"toolu_pending": "msg_b"})
                        self.assertEqual(saved["skill_call_history"].get("toolu_s"), [None, "msg_b"])

                    self.write(collision[:1], compact=True)
                    if resume:
                        out, saved = self.checked_stop()
                        self.assertIsNone(out)
                        self.assertEqual(saved["skill_call_history"].get("toolu_s"), [None, "msg_b"])

                    self.write(pending[2:], compact=True)
                    if resume:
                        out, saved = self.checked_stop()
                        self.assertIsNone(out)
                        self.assertFalse(saved["skill_correlation_lost"])
                        self.assertEqual(saved["current_origin"], ["msg_b", "toolu_pending"])
                        self.assertEqual(saved["skill_message_order"], ["msg_b"])
                        self.assertEqual(saved["skill_call_history"].get("toolu_s"), ["msg_b"])

                    call_id = "toolu_s" if duplicate else "toolu_new"
                    external = identified_load("superpowers:brainstorming", world.other_skill, "msg_b", call_id)
                    self.write(external, tool(error=True), compact=True)
                    out, saved = self.checked_stop()
                    skill = saved["skills"]["full:codereview"]
                    if duplicate:
                        self.assertIsNone(out)
                        self.assertIsNone(saved["current"])
                        self.assertEqual((skill["work"], skill["friction"], skill["reviews"]), (0, 0, 0))
                    else:
                        self.assertIn("`/retrofit-skill:retrofit-skill codereview`", self.context_of(out))
                        self.assertEqual(skill["reviews"], 1)
                        later = identified_load(name, world.mkt_skill, "msg_c", "toolu_later")
                        self.write(later, compact=True)
                        out, saved = self.checked_stop()
                        self.assertIsNone(out)
                        self.assertEqual(saved["skill_call_history"], {"toolu_later": ["msg_c"]})

    def test_unowned_pending_collision_survives_pruning(self):
        for resume in (False, True):
            for scenario in ("new", "unowned", "owned", "consumed"):
                with self.subTest(resume=resume, scenario=scenario), self.sub_world() as world:
                    ours, _ = self.identified_loads()
                    call_id = "toolu_original"
                    owner = "msg_1" if scenario in ("owned", "consumed") else None
                    if scenario == "consumed":
                        original = identified_load("codereview:coderabbit-pr", world.mkt_skill,
                                                   owner, call_id)
                        active_origin = ["msg_1", call_id]
                    else:
                        original = identified_load("graphify", world.graphify, owner, call_id)[:2]
                        active_origin = ["msg_1", ours[0]["message"]["content"][0]["id"]]
                    self.write(ours, original, compact=True)
                    if resume:
                        out, before = self.checked_stop()
                        self.assertIsNone(out)
                        self.assertEqual(before["current_origin"], active_origin)
                        if scenario == "consumed":
                            self.assertNotIn(call_id, before["skill_calls"])
                            self.assertEqual(before["skill_call_history"][call_id], ["msg_1"])
                        else:
                            self.assertIn(call_id, before["skill_calls"])
                            self.assertEqual(before["skill_calls"][call_id], owner)

                    collision = identified_load("nao-instalada", world.other_skill, "msg_2", call_id)
                    self.write(collision[:2], compact=True)
                    if resume:
                        out, middle = self.checked_stop()
                        self.assertIsNone(out)
                        self.assertEqual(middle["current_origin"], active_origin)
                        self.assertEqual(middle["skill_message_order"], ["msg_1"])
                        self.assertFalse(middle["skill_correlation_lost"])
                        self.assertNotIn(call_id, middle["skill_calls"])
                        if scenario != "new":
                            self.assertEqual(middle["skill_call_history"].get(call_id),
                                             [owner] if owner else [])

                    external = identified_load("superpowers:brainstorming", world.other_skill,
                                               "msg_1", "toolu_new" if scenario == "new" else call_id)
                    self.write(external, tool(error=True), compact=True)
                    out, after = self.checked_stop()
                    skill = after["skills"]["full:codereview"]
                    if scenario == "new":
                        self.assertIn("`/retrofit-skill:retrofit-skill codereview`", self.context_of(out))
                        self.assertEqual(skill["reviews"], 1)
                    else:
                        self.assertIsNone(out)
                        self.assertIsNone(after["current"])
                        self.assertEqual((skill["work"], skill["friction"], skill["reviews"]), (0, 0, 0))

    def test_unowned_collision_after_owned_pending_survives_pruning(self):
        for resume in (False, True):
            for reused in (False, True):
                with self.subTest(resume=resume, reused=reused), self.sub_world() as world:
                    ours, _ = self.identified_loads()
                    call_id = "toolu_collision"
                    original = identified_load("graphify", world.other_skill, "msg_2", call_id)
                    collision = identified_load("graphify", world.other_skill, None, call_id)
                    del collision[0]["message"]["id"]
                    self.write(ours, original[:2], compact=True)
                    if resume:
                        out, before = self.checked_stop()
                        self.assertIsNone(out)
                        self.assertEqual(before["skill_calls"][call_id], "msg_2")
                        self.assertEqual(before["skill_message_order"], ["msg_1", "msg_2"])

                    self.write(collision[:2], compact=True)
                    if resume:
                        out, middle = self.checked_stop()
                        self.assertIsNone(out)
                        self.assertEqual(middle["current_origin"], before["current_origin"])
                        self.assertEqual(middle["skill_message_order"], ["msg_1"])
                        self.assertFalse(middle["skill_correlation_lost"])
                        self.assertNotIn(call_id, middle["skill_calls"])
                        self.assertEqual(middle["skill_call_history"].get(call_id), [])

                    external = identified_load("superpowers:brainstorming", world.other_skill,
                                               "msg_1", call_id if reused else "toolu_fresh")
                    self.write(external, tool(error=True), compact=True)
                    out, after = self.checked_stop()
                    skill = after["skills"]["full:codereview"]
                    if reused:
                        self.assertIsNone(out)
                        self.assertIsNone(after["current"])
                    else:
                        self.assertIn("`/retrofit-skill:retrofit-skill codereview`", self.context_of(out))
                    self.assertEqual((skill["work"], skill["friction"], skill["reviews"]),
                                     (0, 0, 0 if reused else 1))

    def test_legacy_external_without_history_ignores_delayed_metadata(self):
        for scenario in ("external", "no_external", "kit_cache", "modern", "modern_call", "new"):
            with self.subTest(scenario=scenario), self.sub_world() as world:
                pending = identified_load("coderabbit-pr", world.mkt_skill, "msg_1", "toolu_pending")
                external = identified_load("superpowers:brainstorming", world.other_skill,
                                           "msg_2", "toolu_other")
                closed = scenario in ("external", "modern", "modern_call", "new")
                external_rows = external[:2] if scenario == "modern_call" else external if closed else ()
                self.write(pending[:2], external_rows, tool(), compact=True)
                out, before = self.checked_stop()
                self.assertIsNone(out)
                self.assertIsNone(before["current"])
                self.assertEqual(before["skills"], {})
                cached = closed and scenario != "modern_call"
                self.assertEqual(before["classified"], {str(world.other_skill): None} if cached else {})
                if scenario not in ("modern", "modern_call"):
                    fields = ("created", "offset", "skills", "current", "classified",
                              "pending", "done", "entrypoint")
                    legacy = {field: before[field] for field in fields if field in before}
                    if scenario == "kit_cache":
                        legacy["classified"]["kit:sdd"] = None
                    (world.data / "sessions/s1.json").write_text(json.dumps(legacy), encoding="utf-8")
                if scenario == "new":
                    self.write(identified_load("codereview:coderabbit-pr", world.mkt_skill,
                                               "msg_3", "toolu_new"))
                else:
                    self.write(pending[2:])
                self.write(tool(error=True))
                out, after = self.checked_stop()
                silent = closed and scenario != "new"
                if silent:
                    self.assertIsNone(out)
                    self.assertIsNone(after["current"])
                    self.assertEqual(after["skills"], {})
                else:
                    self.assertIn("`/retrofit-skill:retrofit-skill codereview`", self.context_of(out))
                    skill = after["skills"]["full:codereview"]
                    self.assertEqual((skill["work"], skill["friction"], skill["reviews"]), (0, 0, 1))
                self.assertEqual(after["attribution_closed"], silent)

    def test_invalid_call_id_cannot_establish_message_position(self):
        for value in (None, "id com espaços", []):
            with self.subTest(value=value), self.sub_world() as world:
                call, _, _ = identified_load("graphify", world.graphify, "msg_z", value)
                self.write([call], compact=True)
                out, saved = self.checked_stop()
                self.assertIsNone(out)
                self.assertEqual(saved["skill_calls"], {})
                self.assertEqual(saved["skill_message_order"], [])

    def test_ambiguous_calls_without_pending_peer_are_pruned(self):
        first, later, _ = self.interleaved_skill_loads()
        later[0]["message"]["content"][0]["id"] = "toolu_a"
        self.write(first[:1], later[:1], compact=True)
        out, saved = self.checked_stop()
        self.assertIsNone(out)
        self.assertEqual(saved["skill_calls"], {})
        self.assertEqual(saved["skill_message_order"], [])
        self.assertEqual(saved["skill_call_history"], {})

    def test_old_state_recovers_order_from_pending_calls(self):
        first, newer, second = self.interleaved_skill_loads()
        self.write(first, newer[:2], second[:2], compact=True)
        self.assertIsNone(self.run_hook())
        path = self.w.data / "sessions/s1.json"
        saved = json.loads(path.read_bytes())
        saved.pop("skill_message_order", None)
        path.write_text(json.dumps(saved), encoding="utf-8")
        self.write(newer[2:], second[2:], tool(error=True))
        self.assert_graphify_retro()

    def test_failed_ids_retire_with_their_active_message(self):
        for linked in (True, False):
            world = World()
            self.addCleanup(world.cleanup)
            with self.subTest(linked=linked), mock.patch.object(self, "w", world):
                older, _, _ = self.interleaved_skill_loads()
                call, result, _ = identified_load("nao-instalada", world.other_skill, "msg_z", "toolu_f")
                result["message"]["content"][0]["is_error"] = True
                self.write(older, [call, result])
                self.assertIsNone(self.run_hook())
                path = world.data / "sessions/s1.json"
                before = json.loads(path.read_bytes())
                self.assertEqual(before["skill_call_history"]["toolu_f"], ["msg_z"])
                self.assertNotIn("toolu_f", before["skill_calls"])
                newer = identified_load("graphify", world.graphify, "msg_a", "toolu_new")
                self.write(newer if linked else skill_typed("brainstorming", world.other_skill))
                self.assertIsNone(self.run_hook())
                after = json.loads(path.read_bytes())
                self.assertNotIn("toolu_f", after["skill_call_history"])
                self.assertEqual(after["skill_message_order"], ["msg_a"] if linked else [])
                if linked:
                    # Fora da janela, a falha antiga não invalida o ID da nova carga.
                    self.write(identified_load("graphify", world.graphify, "msg_a", "toolu_f"),
                               tool(error=True))
                    self.assert_graphify_retro()

    def test_failed_skill_calls_do_not_accumulate_in_saved_state(self):
        path = self.w.data / "sessions/s1.json"
        sizes = []
        for start, end in ((0, 10), (10, 100), (100, 1000)):
            for index in range(start, end):
                call, result, _ = skill_via_tool("nao-instalada", self.w.other_skill)
                call_id = f"toolu_f{index:05}"
                call["message"]["id"] = f"msg_{index:05}"
                call["message"]["content"][0]["id"] = call_id
                result["message"]["content"][0].update(
                    tool_use_id=call_id, content="Unknown skill: nao-instalada", is_error=True)
                self.write([call], compact=True)
                if index == 0:
                    self.assertIsNone(self.run_hook())
                    self.assertIn(call_id, json.loads(path.read_bytes())["skill_calls"])
                self.write([result])
                if index == 0:
                    _, malformed = tool(error=True)
                    malformed["message"]["content"][0]["tool_use_id"] = []
                    self.write([malformed])
                    self.assertIsNone(self.run_hook())
                    with self.subTest(tentativas=1):
                        self.assertNotIn(call_id, json.loads(path.read_bytes())["skill_calls"])
                        self.assertFalse((self.w.data / "errors.log").exists())
            self.assertIsNone(self.run_hook())
            state = path.read_bytes()
            with self.subTest(tentativas=end):
                saved = json.loads(state)
                self.assertEqual(saved["skill_calls"], {})
                self.assertEqual(saved["skill_message_order"], [])
                self.assertEqual(saved["skill_call_history"], {})
            sizes.append(len(state))
        self.assertLessEqual(max(sizes) - min(sizes), 1024)

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

    def kit_worktree(self):
        wt = self.w.tmp / "repos/sdd_agents-missao"
        git(self.w.kit_repo, "worktree", "add", "-q", "-b", "missao", str(wt))
        return wt

    def test_kit_retro_names_the_linked_worktrees(self):
        """Missão do kit roda num worktree ligado, e a sessão do lote 6 tinha o cwd no checkout
        principal: o pedido nomeia o TODO.md de cada worktree. Sem worktree, nada muda."""
        self.write(skill_typed("sdd-plan"), tool(error=True))
        self.assertNotIn("worktree", self.context_of(self.run_hook()))
        wt = self.kit_worktree()
        self.write(skill_typed("sdd-plan"), tool(error=True), tool(error=True))
        text = self.context_of(self.run_hook())
        self.assertIn(str(self.w.kit_repo / "TODO.md"), text)
        self.assertIn(str(wt / "TODO.md"), text)
        self.assertIn("KIT-TOUCHED", text)

    def test_writing_the_todo_of_a_kit_worktree_suppresses_the_next_retro(self):
        """O registro no TODO.md de um worktree ligado do kit também é o retrofit dele."""
        wt = self.kit_worktree()
        self.write(skill_typed("sdd-plan"), tool(error=True))
        self.context_of(self.run_hook())
        self.write(tool_with("Edit", {"file_path": str(wt / "TODO.md")}),
                   tool(error=True), tool(error=True), tool(error=True))
        self.assertIsNone(self.run_hook())

    def test_writing_the_todo_of_another_repo_does_not_suppress_the_kit_retro(self):
        """Controle negativo: TODO.md de outro repo nosso não é o do kit, e a retro volta."""
        self.kit_worktree()
        self.write(skill_typed("sdd-plan"), tool(error=True))
        self.context_of(self.run_hook())
        self.write(tool_with("Edit", {"file_path": str(self.w.proj / "TODO.md")}),
                   tool(error=True), tool(error=True), tool(error=True))
        self.assertIn("kit sdd", self.context_of(self.run_hook()))

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

    def cli_raw(self, *args, data=True):
        """O `queue` como você o roda à mão: sem CLAUDE_PLUGIN_DATA, que só o hook recebe."""
        full_env = dict(os.environ, HOME=str(self.w.home))
        full_env.pop("CLAUDE_PLUGIN_DATA", None)
        if data:
            full_env["CLAUDE_PLUGIN_DATA"] = str(self.w.data)
        return subprocess.run([sys.executable, str(SCRIPT), *args], input="", capture_output=True,
                              text=True, env=full_env, timeout=20)

    def test_queue_by_hand_finds_the_plugin_data_dir(self):
        """Sem a variável, o `queue` lia `data/retrofit-watch`, que não existe, e respondia `[]` (2026-11-02)."""
        real = self.w.home / ".claude/plugins/data/retrofit-watch-chewiesoft-marketplace"
        real.mkdir(parents=True)
        (real / "queue.jsonl").write_text(json.dumps({"id": "s9:1", "session": "s9", "skills": []}) + "\n")
        proc = self.cli_raw("queue", data=False)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual([item["id"] for item in json.loads(proc.stdout)], ["s9:1"])
        proc = self.cli_raw("queue", "--done", "s9:1", data=False)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual((real / "queue.jsonl").read_text(), "", "o --done tira da fila de verdade")

    def test_queue_without_data_dir_fails_loudly_and_creates_nothing(self):
        base = self.w.home / ".claude/plugins/data"
        for args in (("queue",), ("queue", "--done", "s9:1")):
            proc = self.cli_raw(*args, data=False)
            self.assertEqual(proc.returncode, 1, f"{args}: uma fila vazia inventada esconde a de verdade")
            self.assertEqual(proc.stdout, "")
            self.assertIn("não existe", proc.stderr)
        self.assertFalse((base / "retrofit-watch").exists(), "o --done não cria a pasta errada")

    def test_queue_with_two_data_dirs_refuses_to_guess(self):
        for name in ("retrofit-watch-loja-a", "retrofit-watch-loja-b"):
            (self.w.home / ".claude/plugins/data" / name).mkdir(parents=True)
        proc = self.cli_raw("queue", data=False)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("loja-a", proc.stderr)
        self.assertIn("loja-b", proc.stderr)

    def test_queue_done_with_unknown_id_says_so(self):
        self.write(skill_via_tool("codereview:coderabbit-pr", self.w.mkt_skill), tool(error=True))
        self.run_hook(env=UNATTENDED)
        proc = self.cli_raw("queue", "--done", "nao-existe:1")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("nao-existe:1", proc.stderr)
        self.assertEqual(len(self.queued()), 1, "a entrada de verdade fica")

    def test_interactive_transcript_wins_over_unattended_env(self):
        """Oito sessões interativas (`cli` no transcript) foram para a fila e nunca tiveram a retro ao vivo."""
        self.write(with_entrypoint(skill_via_tool("codereview:coderabbit-pr", self.w.mkt_skill), "cli"),
                   with_entrypoint(tool(error=True), "cli"))
        self.assertIn("codereview", self.context_of(self.run_hook(env=UNATTENDED)))
        self.assertEqual(self.queued(), [], "sessão interativa não vai para a fila")
        (self.w.home / ".claude/retrofit-watch.json").write_text(json.dumps({"unattended": "off"}))
        self.write(with_entrypoint(tool(error=True), "cli"), with_entrypoint(tool(error=True), "cli"))
        self.assertIsNotNone(self.run_hook(env=UNATTENDED), "o off da config cala a desassistida, não esta")

    def test_headless_transcript_still_queues_and_records_the_gate(self):
        self.write(with_entrypoint(skill_via_tool("codereview:coderabbit-pr", self.w.mkt_skill), "sdk-cli"),
                   with_entrypoint(tool(error=True), "sdk-cli"))
        self.assertIsNone(self.run_hook(env=UNATTENDED))
        [item] = self.queued()
        self.assertEqual(item["gate"], {"attended_env": "0", "entrypoint_env": "sdk-cli",
                                        "entrypoint_transcript": "sdk-cli"})

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


class FixtureGitEnvTest(unittest.TestCase):
    """O git do `World` não obedece a um GIT_DIR herdado (dentro de um hook do git ele agiria no repo
    real) nem lê a config global ou de sistema de quem roda os testes."""

    def test_world_ignores_an_inherited_git_dir_and_the_real_config(self):
        trap = Path(os.path.realpath(tempfile.mkdtemp(prefix="rw-trap-")))
        self.addCleanup(shutil.rmtree, trap, True)
        subprocess.run(["git", "init", "-q", str(trap / "repo")], check=True, capture_output=True,
                       env=dict(git_env(), HOME=str(trap)))
        marker = trap / "hook-rodou"
        hooks = trap / "hooks"
        hooks.mkdir()
        (hooks / "pre-commit").write_text(f"#!/bin/sh\ntouch '{marker}'\nexit 1\n")
        (hooks / "pre-commit").chmod(0o755)
        config = f"[core]\n\thooksPath = {hooks}\n"
        (trap / ".gitconfig").write_text(config)
        (trap / "global").write_text(config)
        traps = {"GIT_DIR": str(trap / "repo/.git"), "GIT_WORK_TREE": str(trap / "repo"),
                 "GIT_INDEX_FILE": str(trap / "index"), "HOME": str(trap), "GIT_CONFIG_GLOBAL": str(trap / "global"),
                 "GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "core.hooksPath", "GIT_CONFIG_VALUE_0": str(hooks)}
        with mock.patch.dict(os.environ, traps):
            world = World()
        self.addCleanup(world.cleanup)
        self.assertFalse(marker.exists(), "o git da fixture leu a config global herdada")
        log = subprocess.run(["git", "-C", str(world.proj), "log", "--format=%an"], capture_output=True,
                             text=True, env=git_env())
        self.assertEqual(log.stdout.split(), ["t"])
        heads = subprocess.run(["git", "--git-dir", str(trap / "repo/.git"), "rev-list", "--all"],
                               capture_output=True, text=True, env=git_env())
        self.assertEqual(heads.stdout, "", "um commit da fixture foi parar no repo do GIT_DIR herdado")
        self.assertFalse((trap / "index").exists())


if __name__ == "__main__":
    unittest.main()
