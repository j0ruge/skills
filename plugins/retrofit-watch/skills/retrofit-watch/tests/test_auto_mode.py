"""Testes do modo autônomo do retrofit-watch: a config, o pedido.json e o texto do Stop hook.

Rodar: python3 plugins/retrofit-watch/skills/retrofit-watch/tests/test_auto_mode.py
Usa o mesmo HOME fixture e o mesmo arnês de test_retrofit_watch.py. Nenhum teste toca a rede,
o `claude` real ou um `origin` real.
"""
import json
import shutil
import sys
import time
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from test_retrofit_watch import (  # noqa: E402
    SCRIPT, WINDOWS_STDIO, HookHarness, World, commit_all, init_repo, make_skill, skill_typed,
    skill_via_tool, tool, with_entrypoint)

sys.path.insert(0, str(SCRIPT.parent))
import retrofit_watch as rw  # noqa: E402
import rw_auto  # noqa: E402

REFERENCE = SCRIPT.parents[1] / "references" / "modo-autonomo.md"
# Frase que o texto manual de hoje tem e o autônomo não pode ter: ela no texto autônomo é a
# entrada autônoma caindo também no texto manual.
MANUAL_ONLY = "termine perguntando se deve executar a ação indicada"
BYPASS = "bypassPermissions"


def batch_line(rid, plugin, session="s1", licoes=(1,)):
    return {"ts": 1, "sessao": session, "id": rid, "lote": plugin, "plugin": plugin,
            "item": f"{rid}/{plugin}", "licoes": list(licoes), "resultado": "publicado"}


class AutoStopTest(HookHarness, unittest.TestCase):
    def setUp(self):
        self.w = World()

    def tearDown(self):
        self.w.cleanup()

    # --- ajudantes ----------------------------------------------------------------------------

    def config(self, **keys):
        (self.w.home / ".claude/retrofit-watch.json").write_text(json.dumps(keys))

    def work(self, n=6):
        self.write(with_entrypoint(skill_via_tool("codereview:coderabbit-pr", self.w.mkt_skill), "cli"),
                   *[tool()] * n)

    def auto_on(self, **extra):
        self.config(mode="auto", store=str(self.w.repo), **extra)

    def state(self):
        return json.loads((self.w.data / "sessions/s1.json").read_text())

    def save_state(self, data):
        (self.w.data / "sessions/s1.json").write_text(json.dumps(data))

    def pedidos(self):
        return sorted((self.w.data / "auto").glob("*/pedido.json"))

    def lessons(self, rid, raw):
        path = self.w.data / "auto" / rid / "licoes.json"
        path.write_text(raw if isinstance(raw, str) else json.dumps(raw))

    def two_lessons(self, rid):
        self.lessons(rid, {"id": rid, "licoes": [{"n": 1, "plugin": "codereview"},
                                                 {"n": 2, "plugin": "codereview"}]})

    def registry(self, *lines):
        with open(self.w.data / rw_auto.REGISTRY, "a", encoding="utf-8") as fh:
            for line in lines:
                fh.write(json.dumps(line) + "\n")

    def today(self, work=6, friction=0, key="full:codereview"):
        """A saída de hoje para a entrada, montada pelo build_output sem os argumentos novos."""
        entry = dict(self.state()["skills"][key], work=work, friction=friction, reviews=0)
        return rw.build_output([entry])

    def payload(self, mode=BYPASS):
        return {"session_id": "s1", "permission_mode": mode, "cwd": str(self.w.proj)}

    def open_auto_request(self):
        self.auto_on()
        self.work()
        out = self.run_hook(mode=BYPASS)
        self.assertIsNotNone(out)
        rid = self.state()["auto_open"]["id"]
        return out, rid

    # --- o padrão e a config --------------------------------------------------------------------

    def test_default_mode_is_manual_and_text_is_unchanged(self):
        self.work()
        out = self.run_hook(mode=BYPASS)
        self.assertIn("/retrofit-skill:retrofit-skill codereview", self.context_of(out))
        self.assertEqual(out, self.today())
        self.assertFalse((self.w.data / "auto").exists())

    def test_invalid_mode_is_manual(self):
        self.config(mode="sempre", store=str(self.w.repo))
        self.work()
        out = self.run_hook(mode=BYPASS)
        self.assertIn("/retrofit-skill:retrofit-skill codereview", self.context_of(out))
        self.assertEqual(out, self.today())
        self.assertFalse((self.w.data / "auto").exists())

    def test_auto_needs_cli_entrypoint(self):
        self.auto_on()
        self.write(with_entrypoint(skill_via_tool("codereview:coderabbit-pr", self.w.mkt_skill), "sdk-cli"),
                   *[tool()] * 6)
        out = self.run_hook(mode=BYPASS, env={"CLAUDE_CODE_SESSION_ATTENDED": "1"})
        self.assertFalse((self.w.data / "auto").exists())
        st = self.state()
        entry = st["skills"]["full:codereview"]
        self.assertEqual(rw_auto.why_manual(self.w.ctx(), self.payload(), entry, [], st.get("entrypoint")),
                         "entrypoint")
        self.assertEqual(out, self.today())

    def test_auto_without_entrypoint_is_manual(self):
        self.auto_on()
        self.write(skill_via_tool("codereview:coderabbit-pr", self.w.mkt_skill), *[tool()] * 6)
        out = self.run_hook(mode=BYPASS)
        self.assertFalse((self.w.data / "auto").exists())
        st = self.state()
        self.assertNotIn("entrypoint", st)
        entry = st["skills"]["full:codereview"]
        self.assertEqual(rw_auto.why_manual(self.w.ctx(), self.payload(), entry, [], st.get("entrypoint")),
                         "entrypoint")
        self.assertEqual(out, self.today())

    def test_auto_needs_bypass_permissions(self):
        self.auto_on()
        self.work()
        out = self.run_hook(mode="default")
        today = self.today()
        self.assertEqual(self.context_of(out), today["hookSpecificOutput"]["additionalContext"])
        self.assertTrue(out["systemMessage"].startswith(today["systemMessage"] + " — modo manual: "))
        self.assertIn(BYPASS, out["systemMessage"])
        self.assertFalse((self.w.data / "auto").exists())

    # --- o pedido autônomo ----------------------------------------------------------------------

    def test_auto_request_names_absolute_paths_and_writes_pedido(self):
        self.config(mode="auto", store=str(self.w.repo))
        self.work()
        out = self.run_hook(mode=BYPASS)
        pedido = next((self.w.data / "auto").glob("*/pedido.json"))
        text = self.context_of(out)
        self.assertIn(str(pedido.parent / "licoes.json"), text)
        self.assertIn(str(REFERENCE), text)
        self.assertIn(str(SCRIPT), text)
        self.assertIn("seções 1 a 4", text)
        self.assertIn(str(SCRIPT.parents[1] / "references" / "criteria.md"), text)
        self.assertIn("retro codereview: sem lições novas", text)
        self.assertIn("não pergunte nada ao dono", text)
        self.assertIn("Não rode o /retrofit-skill nesta sessão", text)
        self.assertIn("não cite valores de segredo", text)
        self.assertIn(rw_auto.OWNER_WORD_RULE, text)
        self.assertIn("restam 2", text)
        self.assertNotIn(MANUAL_ONLY, text)
        data = json.loads(pedido.read_text())
        self.assertEqual(data["skills"][0]["plugin"], "codereview")
        self.assertEqual(data["cwd"], str(self.w.proj))
        self.assertEqual((data["sessao"], data["modo"], data["transcript"]), ("s1", "auto", str(self.w.transcript)))
        self.assertEqual(data["skills"][0]["skills"], ["coderabbit-pr"])
        self.assertEqual(data["id"], pedido.parent.name)
        self.assertEqual(out["systemMessage"],
                         f"retrofit-watch: retro de codereview pedida ao Claude, modo autônomo ({data['id']})")
        self.assertEqual(self.state()["auto_open"]["id"], data["id"])

    def test_manual_list_kit_and_lean_stay_manual(self):
        """Stop misto: dois blocos rotulados, e cada instrução fica com a lista das suas skills."""
        self.auto_on(manual=["dev-script"])
        cli = lambda group: with_entrypoint(group, "cli")  # noqa: E731
        self.write(cli(skill_via_tool("codereview:coderabbit-pr", self.w.mkt_skill)), tool(error=True),
                   skill_typed("graphify", self.w.graphify), tool(error=True),
                   skill_typed("sdd-plan"), tool(error=True),
                   skill_typed("dev-script:dev-script"), tool(error=True))
        out = self.run_hook(mode=BYPASS)
        [pedido] = self.pedidos()
        self.assertEqual([s["plugin"] for s in json.loads(pedido.read_text())["skills"]], ["codereview"])
        text = self.context_of(out)
        cut = text.index("[modo autônomo:")
        manual, auto = text[:cut], text[cut:]
        self.assertTrue(manual.startswith("[modo manual: "))
        for name in ("graphify", "kit sdd", "dev-script"):
            self.assertIn(name, manual)
            self.assertNotIn(name, auto)
        self.assertIn(MANUAL_ONLY, manual)
        self.assertIn("/retrofit-skill:retrofit-skill graphify", manual)
        self.assertNotIn("codereview", manual)
        self.assertIn("codereview", auto)
        self.assertIn("não pergunte nada ao dono", auto)
        self.assertNotIn("não pergunte nada ao dono", manual)
        self.assertNotIn(MANUAL_ONLY, auto)
        self.assertIn("modo autônomo", out["systemMessage"])
        self.assertIn("(RETROFIT_WATCH=off desliga)", out["systemMessage"])

    def test_second_skill_of_the_same_plugin_is_recorded(self):
        second = make_skill(self.w.mkt_skill.parent, "pr-review")
        self.auto_on(manual=["pr-review"])
        self.write(with_entrypoint(skill_via_tool("codereview:coderabbit-pr", self.w.mkt_skill), "cli"),
                   skill_via_tool("codereview:pr-review", second), *[tool()] * 6)
        out = self.run_hook(mode=BYPASS)
        entry = self.state()["skills"]["full:codereview"]
        self.assertEqual(entry["skills"], ["coderabbit-pr", "pr-review"])
        self.assertEqual(rw_auto.why_manual(self.w.ctx(), self.payload(), entry, [], "cli"), "lista-manual")
        self.assertEqual(out, self.today())
        self.assertFalse((self.w.data / "auto").exists())

    def test_auto_dry_is_requested_like_auto(self):
        self.config(mode="auto-dry", store=str(self.w.repo))
        self.work()
        self.assertIsNotNone(self.run_hook(mode=BYPASS))
        [pedido] = self.pedidos()
        self.assertEqual(json.loads(pedido.read_text())["modo"], "auto-dry")

    def test_store_missing_or_not_the_marketplace_is_manual(self):
        self.config(mode="auto")
        self.work()
        out = self.run_hook(mode=BYPASS)
        self.assertIn("— modo manual: ", out["systemMessage"])
        self.assertIn("store", out["systemMessage"])
        self.assertFalse((self.w.data / "auto").exists())
        other = self.w.tmp / "repos/outra-loja"
        init_repo(other, "https://github.com/alguem/outra-loja.git")
        (other / ".claude-plugin").mkdir()
        (other / ".claude-plugin/marketplace.json").write_text(json.dumps({"name": "outra-loja"}))
        commit_all(other)
        self.config(mode="auto", store=str(other))
        ctx = self.w.ctx()
        self.assertIsNone(ctx.store)
        entry = self.state()["skills"]["full:codereview"]
        self.assertEqual(rw_auto.why_manual(ctx, self.payload(), entry, [], "cli"), "sem-loja")
        self.write(tool(error=True), tool(error=True))
        out = self.run_hook(mode=BYPASS)
        self.assertIn("/retrofit-skill:retrofit-skill codereview", self.context_of(out))
        self.assertIn("store", out["systemMessage"])
        self.assertFalse((self.w.data / "auto").exists())

    def test_session_cap_reached_asks_manually(self):
        self.auto_on()
        self.w.data.mkdir(parents=True, exist_ok=True)
        self.registry(batch_line("r1", "ticket"), batch_line("r2", "dev-script"), batch_line("r3", "outro"))
        self.work()
        out = self.run_hook(mode=BYPASS)
        self.assertIn("/retrofit-skill:retrofit-skill codereview", self.context_of(out))
        self.assertIn("teto", out["systemMessage"])
        self.assertFalse((self.w.data / "auto").exists())
        entry = self.state()["skills"]["full:codereview"]
        registry = rw_auto.read_registry(self.w.ctx())
        self.assertEqual(rw_auto.why_manual(self.w.ctx(), self.payload(), entry, registry, "cli"), "teto")
        two_of_this_plugin = [batch_line("r1", "codereview"), batch_line("r2", "codereview")]
        self.assertEqual(rw_auto.why_manual(self.w.ctx(), self.payload(), entry, two_of_this_plugin, "cli"),
                         "teto")
        self.assertIsNone(rw_auto.why_manual(self.w.ctx(), self.payload(), entry, two_of_this_plugin[:1], "cli"))

    def test_cap_counts_the_entries_of_the_same_request(self):
        """Com 2 retrofits na sessão e duas entradas no mesmo Stop, só uma cabe no teto de 3."""
        self.auto_on()
        self.w.data.mkdir(parents=True, exist_ok=True)
        self.registry(batch_line("r1", "ticket"), batch_line("r2", "outro"))
        self.write(with_entrypoint(skill_via_tool("codereview:coderabbit-pr", self.w.mkt_skill), "cli"),
                   tool(error=True), skill_typed("dev-script:dev-script"), tool(error=True))
        out = self.run_hook(mode=BYPASS)
        [pedido] = self.pedidos()
        self.assertEqual([s["plugin"] for s in json.loads(pedido.read_text())["skills"]], ["codereview"])
        self.assertIn("[modo manual: dev-script]", self.context_of(out))
        self.assertIn("teto", out["systemMessage"])

    # --- o fluxo aberto -----------------------------------------------------------------------

    def test_flow_in_progress_counts_no_work_or_friction(self):
        _, rid = self.open_auto_request()
        self.two_lessons(rid)
        self.write(*[tool(error=True)] * 6)
        self.assertIsNone(self.run_hook(mode=BYPASS))
        entry = self.state()["skills"]["full:codereview"]
        self.assertEqual((entry["work"], entry["friction"]), (0, 0))
        self.assertIn("auto_open", self.state())

    def test_open_flow_silences_a_lean_skill_too(self):
        _, rid = self.open_auto_request()
        self.two_lessons(rid)
        self.write(skill_typed("graphify", self.w.graphify), *[tool(error=True)] * 3)
        self.assertIsNone(self.run_hook(mode=BYPASS))
        lean = [e for e in self.state()["skills"].values() if e["mode"] == "lean"]
        self.assertEqual([(e["work"], e["friction"]) for e in lean], [(0, 0)])

    def test_no_second_request_while_a_flow_is_open(self):
        _, rid = self.open_auto_request()
        self.two_lessons(rid)
        st = self.state()
        st["skills"]["full:dev-script"] = {"key": "full:dev-script", "mode": "full", "arg": "dev-script",
                                           "label": "dev-script", "repo": None, "skills": [],
                                           "reviews": 0, "work": 6, "friction": 1}
        self.save_state(st)
        self.assertTrue(rw.eligible(st["skills"]["full:dev-script"]))
        self.assertIsNone(self.run_hook(mode=BYPASS))
        self.assertEqual(len(self.pedidos()), 1)

    def test_flow_without_lessons_closes_at_the_continuation_stop(self):
        self.open_auto_request()
        self.assertIsNone(self.run_hook(mode=BYPASS, active=True, last="retro codereview: sem lições novas"))
        self.assertNotIn("auto_open", self.state())

    def test_unreadable_lessons_keep_the_flow_open(self):
        _, rid = self.open_auto_request()
        self.lessons(rid, "{quebrado")
        self.assertIsNone(self.run_hook(mode=BYPASS, active=True))
        self.assertIn("auto_open", self.state())
        self.lessons(rid, "[]")
        self.write(tool(error=True), tool(error=True))
        self.assertIsNone(self.run_hook(mode=BYPASS))
        self.assertIn("auto_open", self.state())
        self.assertFalse((self.w.data / "errors.log").exists())

    def test_flow_closes_when_every_lesson_has_a_line(self):
        _, rid = self.open_auto_request()
        self.two_lessons(rid)
        self.registry(batch_line(rid, "codereview", licoes=(1, 2)))
        self.write(tool(error=True), tool(error=True))
        self.assertIsNone(self.run_hook(mode=BYPASS), "o segundo Stop fecha o fluxo e não conta o trecho")
        self.assertNotIn("auto_open", self.state())
        self.write(tool(error=True), tool(error=True))
        out = self.run_hook(mode=BYPASS)
        self.assertIn("modo autônomo", out["systemMessage"])
        self.assertEqual(len(self.pedidos()), 2)

    def test_stale_open_flow_expires(self):
        _, rid = self.open_auto_request()
        self.two_lessons(rid)
        st = self.state()
        st["auto_open"]["ts"] = time.time() - 7 * 3600
        self.save_state(st)
        self.write(tool(error=True))
        self.assertIsNone(self.run_hook(mode=BYPASS))
        st = self.state()
        self.assertNotIn("auto_open", st)
        self.assertEqual(st["skills"]["full:codereview"]["friction"], 1)

    # --- falha, codificação, fonte -------------------------------------------------------------

    def test_auto_failure_falls_back_to_manual(self):
        copy = self.w.tmp / "copia/scripts"
        copy.mkdir(parents=True)
        shutil.copy(SCRIPT, copy / SCRIPT.name)
        (copy / "rw_auto.py").write_text("raise RuntimeError('rw_auto quebrado de propósito')\n")
        self.auto_on()
        self.work()
        out = self.run_hook(mode=BYPASS, script=copy / SCRIPT.name)
        self.assertIn("/retrofit-skill:retrofit-skill codereview", self.context_of(out))
        self.assertEqual(out, self.today())
        log = (self.w.data / "errors.log").read_text().splitlines()
        self.assertEqual(len(log), 1)
        self.assertIn("rw_auto quebrado", log[0])

    def test_auto_text_stays_ascii_on_cp1252_stdout(self):
        self.auto_on()
        self.work()
        out = self.run_hook(mode=BYPASS, env=WINDOWS_STDIO)
        self.assertIn(rw_auto.OWNER_WORD_RULE, self.context_of(out))
        self.assertFalse((self.w.data / "errors.log").exists())

    def test_new_modules_do_not_import_fcntl(self):
        sources = sorted(SCRIPT.parent.glob("rw_*.py"))
        self.assertTrue(sources)
        for path in sources:
            with self.subTest(path.name):
                self.assertNotIn("fcntl", path.read_text(encoding="utf-8"))


class AutoUnitTest(unittest.TestCase):
    def setUp(self):
        self.w = World()

    def tearDown(self):
        self.w.cleanup()

    def config(self, **keys):
        (self.w.home / ".claude/retrofit-watch.json").write_text(json.dumps(keys))

    def test_config_defaults_and_tilde_resolve_by_ctx_home(self):
        ctx = self.w.ctx()
        self.assertEqual(ctx.mode, "manual")
        self.assertEqual(ctx.manual, set())
        self.assertEqual(ctx.auto_limits, {"per_skill": 2, "per_session": 3})
        self.assertEqual(ctx.harvest_roots, [self.w.home / "repos"])
        self.assertEqual(ctx.private_sources, [])
        self.assertIsNone(ctx.store)
        link = self.w.home / "loja"
        link.symlink_to(self.w.repo)
        self.config(mode="auto-dry", manual=["graphify", 3], auto_limits={"per_session": 1, "x": 9},
                    harvest_roots=["~/src", "/abs/x"], private_sources=["~/lista.txt"], store="~/loja")
        ctx = self.w.ctx()
        self.assertEqual(ctx.mode, "auto-dry")
        self.assertEqual(ctx.manual, {"graphify"})
        self.assertEqual(ctx.auto_limits, {"per_skill": 2, "per_session": 1})
        self.assertEqual(ctx.harvest_roots, [self.w.home / "src", Path("/abs/x")])
        self.assertEqual(ctx.private_sources, [self.w.home / "lista.txt"])
        self.assertEqual(ctx.store, link)

    def test_store_needs_git_and_the_marketplace_name(self):
        bare = self.w.tmp / "sem-git"
        (bare / ".claude-plugin").mkdir(parents=True)
        (bare / ".claude-plugin/marketplace.json").write_text(json.dumps({"name": rw.MARKETPLACE}))
        for path in (bare, self.w.proj, self.w.tmp / "nao-existe"):
            with self.subTest(str(path.name)):
                self.config(mode="auto", store=str(path))
                self.assertIsNone(self.w.ctx().store)
        self.config(mode="auto", store=str(self.w.repo))
        self.assertEqual(self.w.ctx().store, self.w.repo)

    def test_new_id_is_dated_and_safe(self):
        self.assertEqual(rw_auto.new_id("ab-cd/ef.1234567890", now=0), "19700101-000000-abcdef12")
        self.assertRegex(rw_auto.new_id("../..", now=0), r"^19700101-000000-[A-Za-z0-9]+$")

    def test_retro_and_lote_dirs_refuse_unsafe_names(self):
        ctx = self.w.ctx()
        self.assertEqual(rw_auto.retro_dir(ctx, "r1"), self.w.data / "auto/r1")
        self.assertEqual(rw_auto.lote_dir(ctx, "r1", "codereview__description"),
                         self.w.data / "auto/r1/codereview__description")
        for bad in ("", "..", "../x", "a/b", ".oculto", "-x", "a b", "a\\b"):
            with self.subTest(bad):
                with self.assertRaises(rw_auto.Malformed):
                    rw_auto.retro_dir(ctx, bad)
                with self.assertRaises(rw_auto.Malformed):
                    rw_auto.lote_dir(ctx, "r1", bad)

    def test_registry_skips_unreadable_lines_and_stamps_ts(self):
        ctx = self.w.ctx()
        self.assertEqual(rw_auto.read_registry(ctx), [])
        written = rw_auto.append_registry(ctx, {"id": "r1", "item": "r1/codereview"})
        self.assertIsInstance(written["ts"], int)
        with open(self.w.data / rw_auto.REGISTRY, "a", encoding="utf-8") as fh:
            fh.write("{quebrado\n[1, 2]\n")
        second = rw_auto.append_registry(ctx, {"id": "r2"})
        self.assertEqual(rw_auto.read_registry(ctx), [written, second])

    def test_used_counts_distinct_batch_pairs_of_the_session(self):
        registry = [
            batch_line("r1", "codereview"),
            dict(batch_line("r1", "codereview"), lote="codereview__description",
                 item="r1/codereview__description"),
            dict(batch_line("r1", "codereview"), item="r1/codereview#3"),
            dict(batch_line("r2", "ticket"), item="r2/ticket#1"),
            batch_line("r3", "codereview", session="outra"),
            batch_line("r4", "ticket"),
        ]
        self.assertEqual(rw_auto.used(registry, "s1"), 2)
        self.assertEqual(rw_auto.used(registry, "s1", plugin="codereview"), 1)
        self.assertEqual(rw_auto.used(registry, "s1", skip="r1"), 1)
        self.assertEqual(rw_auto.used(registry, "outra"), 1)

    def test_why_manual_reasons_in_order(self):
        self.config(mode="auto", store=str(self.w.repo), manual=["ticket"])
        ctx = self.w.ctx()
        full = {"key": "full:codereview", "mode": "full", "arg": "codereview", "label": "codereview"}
        lean = {"key": "lean:x:graphify", "mode": "lean", "arg": "graphify", "label": "graphify"}
        listed = dict(full, arg="ticket", key="full:ticket")
        payload = {"session_id": "s1", "permission_mode": BYPASS}
        self.assertIsNone(rw_auto.why_manual(ctx, payload, full, [], "cli"), "estado antigo sem `skills`")
        self.assertEqual(rw_auto.why_manual(ctx, dict(payload, permission_mode="default"), lean, [], "x"),
                         "kit-ou-lean")
        self.assertEqual(rw_auto.why_manual(ctx, dict(payload, permission_mode="default"), listed, [], "x"),
                         "lista-manual")
        self.assertEqual(rw_auto.why_manual(ctx, dict(payload, permission_mode="default"), full, [], "x"),
                         "permissao")
        self.assertEqual(rw_auto.why_manual(ctx, payload, full, [], "sdk-cli"), "entrypoint")
        self.config(mode="auto")
        self.assertEqual(rw_auto.why_manual(self.w.ctx(), payload, full, [], "cli"), "sem-loja")
        self.config(store=str(self.w.repo))
        self.assertEqual(rw_auto.why_manual(self.w.ctx(), payload, lean, [], "cli"), "modo")

    def test_flow_finished_reads_lessons_against_the_registry(self):
        ctx = self.w.ctx()
        pedido = {"id": "r1"}
        self.assertTrue(rw_auto.flow_finished(ctx, pedido), "sem licoes.json o fluxo acabou")
        path = self.w.data / "auto/r1/licoes.json"
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps({"id": "r1", "licoes": [{"n": 1}, {"n": 2}]}))
        self.assertFalse(rw_auto.flow_finished(ctx, pedido))
        rw_auto.append_registry(ctx, {"id": "r1", "item": "r1/codereview#1", "licoes": [1]})
        rw_auto.append_registry(ctx, {"id": "r9", "item": "r9/codereview", "licoes": [2]})
        self.assertFalse(rw_auto.flow_finished(ctx, pedido), "a linha de outro id não conta")
        rw_auto.append_registry(ctx, {"id": "r1", "item": "r1/codereview", "licoes": [2]})
        self.assertTrue(rw_auto.flow_finished(ctx, pedido))
        for raw in ("{quebrado", "[]", '{"licoes": {}}', '{"licoes": [{"x": 1}]}', '{"licoes": [3]}'):
            with self.subTest(raw):
                path.write_text(raw)
                self.assertFalse(rw_auto.flow_finished(ctx, pedido))


if __name__ == "__main__":
    unittest.main()
