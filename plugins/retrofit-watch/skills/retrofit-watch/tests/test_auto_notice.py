"""Testes do aviso de startup do modo autônomo (Tarefa 10): segurados, órfãos, instalação atrás e o
critério da v2, medido no `origin/main` local (D14, D15).

Rodar: python3 plugins/retrofit-watch/skills/retrofit-watch/tests/test_auto_notice.py
Os commits autônomos nascem no `origin` da loja fixture (`advance_origin`), com o trailer na mensagem e
a data pedida, e chegam ao `origin/main` local por um `fetch` do teste: o startup nunca busca. Todo nome
inventado se monta em tempo de execução: um literal faria a camada 1 reprovar o próprio ramo.
"""
import contextlib
import importlib.util
import json
import os
import sys
import time
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import fixture_store as fs  # noqa: E402
from test_retrofit_watch import UNATTENDED, HookHarness, World, skill_via_tool, tool  # noqa: E402
import retrofit_watch as rw  # noqa: E402
import rw_auto  # noqa: E402  (o test_retrofit_watch põe scripts/ no path)
import rw_store  # noqa: E402
from test_auto_formats import lesson  # noqa: E402

# O aviso de hoje, gravado antes da Tarefa 10 com uma retro adiada do `codereview` na fila.
TODAY = ("retrofit-watch: 1 retro pendente de sessões headless (codereview) — "
         "/retrofit-watch:retrofit-watch pendentes")
DAY = 86400
NOTE = "plugins/demo/skills/demo/references/nota-{}.md"


def invented(tag):
    """Um nome que não existe em lugar nenhum, montado aqui."""
    return "zq" + tag + "vorn"


def phrase(result):
    return (f"{result['publicados']} retrofits autônomos, {result['revertidos']} revertidos, "
            f"{result['vazados']} nomes vazados desde {result['desde']} — o kit pode entrar "
            "(ver a spec do modo autônomo)")


def _cpn():
    spec = importlib.util.spec_from_file_location("cpn_dos_testes", fs.STORE_ROOT / "scripts/check-private-names.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class NoticeHarness(HookHarness):
    """A loja fixture, o registro e o aviso de startup chamado no mesmo processo."""

    def setUp(self):
        self.w = fs.StoreWorld()
        self.w.data.mkdir(exist_ok=True)
        self.t0 = int(time.time()) - 30 * DAY
        self.count = 0

    def tearDown(self):
        self.w.cleanup()

    def ctx(self):
        return self.w.ctx()

    def line(self, rid, item, resultado, plugin="demo", **over):
        entry = rw_auto._line("s1", rid, item, plugin, [1], resultado, over.pop("motivo", None),
                              lote=over.pop("lote", None))
        entry.update(over)
        return rw_auto.append_registry(self.ctx(), entry)

    def pending(self, now=None):
        """O `systemMessage` do startup, numa sessão assistida; `now` fixa o relógio do aviso."""
        clock = mock.patch("time.time", return_value=now) if now is not None else contextlib.nullcontext()
        with mock.patch.dict(os.environ, {"CLAUDE_CODE_SESSION_ATTENDED": "1"}), clock:
            os.environ.pop("RETROFIT_WATCH", None)
            out = rw.cmd_pending({}, self.ctx())
        return out["systemMessage"] if out else None

    def commit(self, message, ts, files=None):
        """Um commit no `origin` com a data `ts` (epoch)."""
        self.count += 1
        files = files or {f"plugins/demo/notas/outro-{self.count}.md": f"nota {self.count}\n"}
        return self.w.advance_origin(files, message, date=f"@{int(ts)} +0000")

    def autos(self, n, trailer="autonomous", start=None):
        """`n` commits com o trailer, o primeiro em `start` (padrão `self.t0`) e os outros um minuto
        depois de cada anterior. Cada um toca uma nota própria. Devolve os shas."""
        start = self.t0 if start is None else start
        shas = []
        for i in range(n):
            self.count += 1
            shas.append(self.w.advance_origin({NOTE.format(self.count): f"nota {self.count}\n"},
                                              f"fix(demo): nota {self.count}\n\nRetrofit-Mode: {trailer}\n",
                                              date=f"@{start + 60 * i} +0000"))
        return shas

    def fetch(self):
        self.w.git(self.w.store, "fetch", "-q", "origin")

    def criterion(self, now):
        return rw_store.criterion(self.ctx(), now=now)

    def queue_one(self):
        HookHarness.write(self, skill_via_tool("codereview:coderabbit-pr", self.w.mkt_skill), tool(error=True))
        self.run_hook(env=UNATTENDED)

    def errors(self):
        path = self.w.data / "errors.log"
        return path.read_text(encoding="utf-8") if path.exists() else ""


class TodayTest(HookHarness, unittest.TestCase):
    def setUp(self):
        self.w = World()

    def tearDown(self):
        self.w.cleanup()

    def test_startup_without_auto_data_is_unchanged(self):
        self.write(skill_via_tool("codereview:coderabbit-pr", self.w.mkt_skill), tool(error=True))
        self.run_hook(env=UNATTENDED)
        out = self.run_hook("pending")
        self.assertEqual(out, {"systemMessage": TODAY})
        self.assertFalse((self.w.data / "errors.log").exists())


@fs.requires_store
class RegistryNoticeTest(NoticeHarness, unittest.TestCase):
    def test_held_retrofit_is_announced_with_its_branch(self):
        self.line("x1", "x1/demo", "segurado", motivo="testes", lote="demo", ramo="retrofit-auto/demo-x1")
        self.line("y1", "y1/demo2", "segurado", plugin="demo2", motivo="testes", lote="demo2",
                  ramo="retrofit-auto/demo2-y1")
        self.line("y1", "y1/demo2", "descartado", plugin="demo2", motivo="descartado-pelo-dono", lote="demo2")
        self.line("z1", "z1/demo#1", "descartado", motivo="coberta")
        self.assertEqual(self.pending(), "retrofit-watch: 1 retrofit segurado (demo: retrofit-auto/demo-x1) — "
                                         "/retrofit-watch:retrofit-watch segurados")
        # Uma lição segurada não tem ramo: o aviso a nomeia pelo item.
        self.line("z2", "z2/demo#2", "segurado", motivo="sem-correcao")
        self.assertIn("2 retrofits segurados (demo: retrofit-auto/demo-x1, demo: z2/demo#2)", self.pending())

    def test_held_lote_without_branch_in_its_line_reads_the_retrofit_json(self):
        """I2: a linha do `hold_item` por `executor-falhou` sai sem ramo; o ramo vem do retrofit.json."""
        rid = self.w.retro([{}], [{}])
        retrofit = rw_store.prepare(self.ctx(), rid, "demo")
        line = rw_auto.hold_item(self.ctx(), rid, f"{rid}/demo", "executor-falhou")
        self.assertIsNone(line["ramo"])
        self.assertEqual(self.pending(), f"retrofit-watch: 1 retrofit segurado (demo: {retrofit['ramo']}) — "
                                         "/retrofit-watch:retrofit-watch segurados")
        # Sem retrofit.json (o lote não chegou ao prepare), o aviso nomeia o item.
        (rw_auto.lote_dir(self.ctx(), rid, "demo") / "retrofit.json").unlink()
        self.assertIn(f"(demo: {rid}/demo)", self.pending())
        # Uma linha com o id fora do formato seguro não aponta pasta nenhuma: o aviso nomeia o item.
        self.line("..", "../demo", "segurado", motivo="testes", lote="demo")
        self.assertIn("demo: ../demo)", self.pending())

    def test_install_behind_is_announced(self):
        self.line("a1", "a1/demo", "publicado", lote="demo", instalacao="update")
        self.line("b1", "b1/demo2", "publicado", plugin="demo2", lote="demo2", instalacao="ok")
        self.line("d1", "d1/demo2", "publicado", plugin="demo2", lote="demo2", instalacao="pendente")
        self.line("d1", "d1/demo2", "publicado", plugin="demo2", lote="demo2", instalacao="nao-instalado")
        # T10-lição: a linha `publicado` de uma lição trazida de volta não tem `instalacao`.
        self.line("a1", "a1/demo#2", "publicado", lote="demo")
        got = rw_auto.install_behind(self.ctx())
        self.assertEqual([e["item"] for e in got], ["a1/demo"])
        self.assertEqual(self.pending(), "retrofit-watch: 1 plugin com a cópia instalada atrás da última publicação "
                                         "(demo)")
        for state in ("pendente", "cache-difere"):
            self.line("e1", "e1/demo2", "publicado", plugin="demo2", lote="demo2", instalacao=state)
            self.assertEqual([e["item"] for e in rw_auto.install_behind(self.ctx())], ["a1/demo", "e1/demo2"], state)

    def test_a_newer_publication_of_the_plugin_replaces_the_one_behind(self):
        # Final-F3: o aviso conta só a última publicação de cada plugin. O lote A atrás e o lote B do mesmo
        # plugin em dia: o plugin sai do aviso; o `publish` de A de novo daria `cache-difere` para sempre.
        clock = [self.t0]

        def at(rid, state):
            clock[0] += 60
            with mock.patch("time.time", return_value=clock[0]):
                self.line(rid, f"{rid}/demo", "publicado", lote="demo", instalacao=state)
        at("a1", "pendente")
        at("a1", "update")
        self.assertEqual([e["item"] for e in rw_auto.install_behind(self.ctx())], ["a1/demo"])
        at("b1", "pendente")
        at("b1", "ok")
        self.assertEqual(rw_auto.install_behind(self.ctx()), [])
        self.assertIsNone(self.pending())
        # Rodar o `publish` de A de novo não traz A de volta: B continua a última publicação do plugin.
        at("a1", "cache-difere")
        self.assertEqual(rw_auto.install_behind(self.ctx()), [])
        # A e B atrás: o plugin aparece uma vez, pelo lote B.
        at("c1", "pendente")
        at("c1", "update")
        at("d1", "pendente")
        at("d1", "cache-difere")
        got = rw_auto.install_behind(self.ctx())
        self.assertEqual([e["item"] for e in got], ["d1/demo"])
        self.assertEqual(self.pending(), "retrofit-watch: 1 plugin com a cópia instalada atrás da última "
                                         "publicação (demo)")

    def test_a_failing_segment_keeps_the_queue_notice(self):
        self.queue_one()
        self.line("x1", "x1/demo", "segurado", motivo="testes", lote="demo", ramo="retrofit-auto/demo-x1")
        held = "1 retrofit segurado (demo: retrofit-auto/demo-x1) — /retrofit-watch:retrofit-watch segurados"
        self.assertEqual(self.pending(), f"{TODAY} · {held}")
        for target in ((rw_auto, "held"), (rw_auto, "orphans"), (rw_auto, "install_behind"),
                       (rw_store, "criterion")):
            with self.subTest(target=target[1]), mock.patch.object(*target, side_effect=RuntimeError(target[1])):
                self.assertEqual(self.pending(), TODAY if target[1] == "held" else f"{TODAY} · {held}")
                self.assertIn(f"RuntimeError: {target[1]}", self.errors())


@fs.requires_store
class OrphanTest(NoticeHarness, unittest.TestCase):
    def test_orphan_lote_is_announced_after_an_hour(self):
        rid = self.w.retro([{}], [{}])
        retrofit = rw_store.prepare(self.ctx(), rid, "demo")
        ts = rw_auto.load_pedido(rw_auto.retro_dir(self.ctx(), rid) / "pedido.json")["ts"]
        self.assertEqual(rw_auto.orphans(self.ctx(), now=ts + 600), [])
        self.assertEqual(rw_auto.orphans(self.ctx(), now=ts + rw_auto.ORPHAN_AGE - 1), [])
        self.assertEqual(len(rw_auto.orphans(self.ctx(), now=ts + rw_auto.ORPHAN_AGE)), 1, "1 h em ponto já é órfão")
        [got] = rw_auto.orphans(self.ctx(), now=ts + 2 * 3600)
        self.assertEqual((got["tipo"], got["id"], got["lote"], got["ramo"]), ("lote", rid, "demo", retrofit["ramo"]))
        # T10-órfão: a linha de uma lição que leva o `lote` não é a linha do lote.
        self.line(rid, f"{rid}/demo#1", "publicado", lote="demo")
        [got] = rw_auto.orphans(self.ctx(), now=ts + 2 * 3600)
        self.assertEqual(got["tipo"], "lote")
        self.assertIsNone(self.pending(now=ts + 600))
        self.assertEqual(self.pending(now=ts + 2 * 3600),
                         f"retrofit-watch: 1 retrofit autônomo sem registro de fim ({retrofit['ramo']})")
        # retrofit.json ilegível: o órfão continua, nomeado pelo id.
        path = rw_auto.lote_dir(self.ctx(), rid, "demo") / "retrofit.json"
        good = path.read_bytes()
        path.write_text("{", encoding="utf-8")
        [got] = rw_auto.orphans(self.ctx(), now=ts + 2 * 3600)
        self.assertEqual((got["tipo"], got["ramo"]), ("lote", None))
        self.assertEqual(self.pending(now=ts + 2 * 3600), f"retrofit-watch: 1 retrofit autônomo sem registro de fim ({rid})")
        path.write_bytes(good)
        self.line(rid, f"{rid}/demo", "publicado", lote="demo", instalacao="ok")
        self.assertEqual(rw_auto.orphans(self.ctx(), now=ts + 2 * 3600), [])

    def test_orphan_lessons_are_announced_after_an_hour(self):
        rid = self.w.retro([{}, {}], None)
        folder = rw_auto.retro_dir(self.ctx(), rid)
        ts = rw_auto.load_pedido(folder / "pedido.json")["ts"]
        self.line(rid, f"{rid}/demo#1", "descartado", motivo="coberta")
        self.assertEqual(rw_auto.orphans(self.ctx(), now=ts + 600), [])
        [got] = rw_auto.orphans(self.ctx(), now=ts + 2 * 3600)
        self.assertEqual((got["tipo"], got["id"], got["lote"], got["ramo"]), ("licoes", rid, None, None))
        (folder / "licoes.json").write_text("{", encoding="utf-8")
        [got] = rw_auto.orphans(self.ctx(), now=ts + 2 * 3600)
        self.assertEqual((got["tipo"], got["id"]), ("licoes", rid))
        # pedido.json ilegível: a idade sai da hora da pasta.
        pedido = (folder / "pedido.json").read_bytes()
        (folder / "pedido.json").write_text("{", encoding="utf-8")
        os.utime(folder, (ts, ts))
        [got] = rw_auto.orphans(self.ctx(), now=ts + 2 * 3600)
        self.assertEqual(got["id"], rid)
        self.assertEqual(rw_auto.orphans(self.ctx(), now=ts + 600), [])
        # Uma pasta fora do formato seguro (um temporário) não é uma retro.
        odd = folder.parent / ".tmp-x"
        odd.mkdir()
        (odd / "licoes.json").write_text("{", encoding="utf-8")
        os.utime(odd, (ts, ts))
        self.assertEqual([o["id"] for o in rw_auto.orphans(self.ctx(), now=ts + 2 * 3600)], [rid])
        (folder / "pedido.json").write_bytes(pedido)
        # Com a linha da segunda lição, o fluxo fechou: nada é órfão.
        rw_auto._write_json(folder / "licoes.json", {"id": rid, "licoes": [lesson(1, "demo"), lesson(2, "demo")]})
        self.line(rid, f"{rid}/demo#2", "descartado", motivo="coberta", licoes=[2])
        self.assertEqual(rw_auto.orphans(self.ctx(), now=ts + 2 * 3600), [])


    def test_discard_retro_closes_lessons_without_a_verdict(self):
        """Item 14: o revisor falhou (sem veredito.json) e a retro ficaria órfã para sempre."""
        rid = self.w.retro([{}, {}], None)
        ts = rw_auto.retro_pedido(self.ctx(), rid)["ts"]
        self.line(rid, f"{rid}/demo#1", "descartado", motivo="coberta")
        self.assertEqual([o["id"] for o in rw_auto.orphans(self.ctx(), now=ts + 2 * 3600)], [rid])
        before = len(rw_auto.read_registry(self.ctx()))
        got = rw_auto.discard_retro(self.ctx(), rid)
        self.assertEqual([(e["item"], e["licoes"], e["resultado"], e["motivo"], e["sessao"], e["plugin"]) for e in got],
                         [(f"{rid}/demo#2", [2], "descartado", "descartado-pelo-dono", "s1", "demo")])
        self.assertEqual(rw_auto.read_registry(self.ctx())[before:], got)
        self.assertEqual(rw_auto.orphans(self.ctx(), now=ts + 2 * 3600), [])
        self.assertEqual(rw_auto.held(self.ctx()), [])

    def test_discard_retro_closes_an_unreadable_lessons_file(self):
        rid = self.w.retro([{}, {}], None)
        folder = rw_auto.retro_dir(self.ctx(), rid)
        ts = rw_auto.retro_pedido(self.ctx(), rid)["ts"]
        (folder / "licoes.json").write_text("{", encoding="utf-8")
        self.line("x1", "x1/demo", "publicado", lote="demo")
        used = rw_auto.used(rw_auto.read_registry(self.ctx()), "s1")
        self.assertEqual([o["id"] for o in rw_auto.orphans(self.ctx(), now=ts + 2 * 3600)], [rid])
        got = rw_auto.discard_retro(self.ctx(), rid, "resolvido-manual")
        self.assertEqual([(e["item"], e["resultado"], e["motivo"], e["sessao"]) for e in got],
                         [(f"{rid}#retro", "descartado", "resolvido-manual", "s1")])
        self.assertEqual(rw_auto.RETRO_ITEM.format(rid=rid), f"{rid}#retro")
        self.assertEqual(rw_auto.orphans(self.ctx(), now=ts + 2 * 3600), [])
        self.assertEqual(rw_auto.used(rw_auto.read_registry(self.ctx()), "s1"), used,
                         "a linha da retro não é um retrofit da sessão")
        # De novo: a retro já está fechada, e nada é gravado.
        before = rw_auto.read_registry(self.ctx())
        with self.assertRaises(rw_auto.Malformed) as caught:
            rw_auto.discard_retro(self.ctx(), rid)
        self.assertIn("nada sem registro de fim", str(caught.exception))
        self.assertEqual(rw_auto.read_registry(self.ctx()), before)
        # pedido.json ilegível: a linha sai com `sessao` null.
        rid2 = self.w.retro([{}], None)
        folder2 = rw_auto.retro_dir(self.ctx(), rid2)
        (folder2 / "licoes.json").write_text("{", encoding="utf-8")
        (folder2 / "pedido.json").write_text("{", encoding="utf-8")
        [got] = rw_auto.discard_retro(self.ctx(), rid2)
        self.assertEqual((got["item"], got["sessao"]), (f"{rid2}#retro", None))

    def test_discard_retro_closes_a_lote_without_a_line(self):
        rid = self.w.retro([{}], [{}])
        retrofit = rw_store.prepare(self.ctx(), rid, "demo")
        ts = rw_auto.retro_pedido(self.ctx(), rid)["ts"]
        [orphan] = rw_auto.orphans(self.ctx(), now=ts + 2 * 3600)
        self.assertEqual(orphan["tipo"], "lote")
        # Um segundo lote, já segurado: tem linha, e o `discard --retro` não o toca.
        other = rw_auto.lote_dir(self.ctx(), rid, "demo__description")
        other.mkdir()
        (other / "retrofit.json").write_bytes((rw_auto.lote_dir(self.ctx(), rid, "demo") / "retrofit.json").read_bytes())
        self.line(rid, f"{rid}/demo__description", "segurado", motivo="testes", lote="demo__description")
        held = rw_auto.held(self.ctx())
        got = rw_auto.discard_retro(self.ctx(), rid)
        self.assertEqual([(e["item"], e["lote"], e["plugin"], e["licoes"], e["resultado"]) for e in got],
                         [(f"{rid}/demo", "demo", "demo", retrofit["licoes"], "descartado")])
        self.assertEqual(rw_auto.held(self.ctx()), held, "o lote segurado continua em aberto")
        self.assertEqual(rw_auto.orphans(self.ctx(), now=ts + 2 * 3600), [])

    def test_discard_retro_takes_the_plugin_from_the_retrofit_json(self):
        # Final-F2: um plugin com `__` no nome. O `plugin` da linha é o do retrofit.json do lote, nunca o
        # pedaço do nome antes do primeiro `__`; com o retrofit.json ilegível, sai do nome pela regra da
        # porta (o sufixo `__description`).
        rid = self.w.retro([{}], [{}])
        rw_store.prepare(self.ctx(), rid, "demo")
        self.line(rid, f"{rid}/demo", "segurado", motivo="testes", lote="demo")
        plugin = "ab__cd"
        good = json.loads((rw_auto.lote_dir(self.ctx(), rid, "demo") / "retrofit.json").read_text(encoding="utf-8"))
        folder = rw_auto.lote_dir(self.ctx(), rid, plugin)
        folder.mkdir()
        rw_auto._write_json(folder / "retrofit.json", dict(good, lote=plugin, plugin=plugin, licoes=[3]))
        broken = rw_auto.lote_dir(self.ctx(), rid, plugin + "__description")
        broken.mkdir()
        (broken / "retrofit.json").write_text("{", encoding="utf-8")
        got = rw_auto.discard_retro(self.ctx(), rid)
        self.assertEqual([(e["lote"], e["plugin"], e["licoes"]) for e in got],
                         [(plugin, plugin, [3]), (plugin + "__description", plugin, [])])

    def test_discard_retro_refuses_when_nothing_is_open(self):
        rid = self.w.retro([{}, {}], None)
        self.line(rid, f"{rid}/demo#1", "descartado", motivo="coberta")
        self.line(rid, f"{rid}/demo#2", "segurado", motivo="sem-veredito", licoes=[2])
        before = rw_auto.read_registry(self.ctx())
        cases = {"nada sem registro de fim": (rid, "descartado-pelo-dono"),
                 "não tem pasta": ("20261101-000000-ausente", "descartado-pelo-dono"),
                 "'teto'": (self.w.retro([{}], None), "teto")}
        for needle, (who, motivo) in cases.items():
            with self.subTest(needle):
                with self.assertRaises(rw_auto.Malformed) as caught:
                    rw_auto.discard_retro(self.ctx(), who, motivo)
                self.assertIn(needle, str(caught.exception))
                self.assertEqual(rw_auto.read_registry(self.ctx()), before)
        # A lição segurada continua em aberto: sai pelo `discard <id> <item>`.
        self.assertEqual([e["item"] for e in rw_auto.held(self.ctx())], [f"{rid}/demo#2"])

    def test_orphans_read_the_registry_once(self):
        """I1: nada é apagado, e toda retro fechada continua com o seu licoes.json. O registro se lê uma
        vez só por chamada, não uma vez por retro antiga (o startup tem 10 s)."""
        old = int(time.time()) - 2 * DAY
        root = self.w.data / rw_auto.AUTO_DIR
        for i in range(50):
            rid = f"20261101-000000-r{i:03d}"
            (root / rid).mkdir(parents=True)
            rw_auto._write_json(root / rid / "licoes.json", {"id": rid, "licoes": [lesson(1, "demo"), lesson(2, "demo")]})
            os.utime(root / rid, (old, old))
            self.line(rid, f"{rid}/demo#1", "descartado", motivo="coberta")
            if i % 2:
                self.line(rid, f"{rid}/demo#2", "descartado", motivo="coberta", licoes=[2])
        with mock.patch.object(rw_auto, "read_registry", wraps=rw_auto.read_registry) as spy:
            got = rw_auto.orphans(self.ctx())
        self.assertEqual(spy.call_count, 1)
        self.assertEqual([o["id"] for o in got], [f"20261101-000000-r{i:03d}" for i in range(0, 50, 2)])


@fs.requires_store
class CriterionTest(NoticeHarness, unittest.TestCase):
    def test_criterion_needs_ten_and_fourteen_days(self):
        self.assertIsNone(rw_store.criterion(rw.Context(home=self.w.tmp / "sem-loja", data_dir=self.w.data)))
        self.autos(9)
        self.fetch()
        got = self.criterion(self.t0 + 20 * DAY)
        self.assertEqual((got["publicados"], got["dias"], got["cumprido"]), (9, 20, False))
        self.assertIsNone(got["vazados"], "vazados só se calcula com os dois pisos passados")
        self.autos(1, start=self.t0 + 600)
        self.fetch()
        got = self.criterion(self.t0 + 13 * DAY + 30)
        self.assertEqual((got["publicados"], got["dias"], got["cumprido"]), (10, 13, False))
        self.assertIsNone(got["vazados"])
        got = self.criterion(self.t0 + 14 * DAY + 30)
        self.assertEqual(got, {"publicados": rw_store.V2_MIN_PUBLISHED, "dias": rw_store.V2_MIN_DAYS,
                               "revertidos": 0, "vazados": 0, "desde": time.strftime("%Y-%m-%d", time.gmtime(self.t0)),
                               "cumprido": True})
        self.assertEqual(rw_store.criterion_notice(self.ctx(), now=self.t0 + 14 * DAY + 30),
                         f"10 retrofits autônomos, 0 revertidos, 0 nomes vazados desde {got['desde']} — o kit pode "
                         "entrar (ver a spec do modo autônomo)")
        self.assertIsNone(rw_store.criterion_notice(self.ctx(), now=self.t0 + 13 * DAY + 30))

    def test_criterion_counts_commits_not_registry_lines(self):
        base = self.w.git(self.w.store, "rev-parse", "origin/main")
        self.autos(10)
        self.fetch()
        self.assertEqual(rw_auto.read_registry(self.ctx()), [])
        self.assertEqual(self.criterion(self.t0 + 15 * DAY)["publicados"], 10, "o registro vazio não zera a conta")
        # Um origin/main local sem os commits e 10 linhas `publicado` no registro: a conta é zero.
        self.w.git(self.w.store, "update-ref", "refs/remotes/origin/main", base)
        for i in range(10):
            self.line(f"r{i}", f"r{i}/demo", "publicado", lote="demo", instalacao="ok", commit="0" * 40)
        self.assertEqual(self.criterion(self.t0 + 15 * DAY)["publicados"], 0)

    def test_approved_commits_do_not_count(self):
        self.autos(9)
        self.autos(3, trailer="autonomous-approved", start=self.t0 + 3600)
        self.autos(1, trailer="autonomous-later", start=self.t0 + 7200)
        self.commit("fix(demo): dois trailers\n\nRetrofit-Mode: autonomous\nRetrofit-Mode: autonomous\n", self.t0 + 9000)
        self.fetch()
        self.assertEqual(self.criterion(self.t0 + 15 * DAY)["publicados"], 9)

    def test_a_revert_on_origin_main_blocks_the_criterion(self):
        shas = self.autos(10)
        base = self.w.git(self.w.store, "rev-list", "--max-parents=0", "origin/main")
        self.commit(f"Revert \"feat: loja fixture\"\n\nThis reverts commit {base}.\n", self.t0 + 3600)
        self.fetch()
        got = self.criterion(self.t0 + 15 * DAY)
        self.assertEqual((got["revertidos"], got["cumprido"]), (0, True), "reverter commit não autônomo não conta")
        self.commit(f"Revert \"fix(demo): nota 3\"\n\nThis reverts commit {shas[2]}.\n", self.t0 + 7200)
        self.fetch()
        got = self.criterion(self.t0 + 15 * DAY)
        self.assertEqual((got["publicados"], got["revertidos"], got["cumprido"]), (10, 1, False))
        self.assertEqual(got["vazados"], 0)

    def test_a_leaked_name_in_a_touched_file_blocks_the_criterion(self):
        self.autos(10)
        name = invented("vaza")
        listed = (self.w.other / "scripts/private-names.sha256").read_text(encoding="utf-8")
        listed += _cpn().resumo(name) + "\n"
        # O nome num arquivo que nenhum commit autônomo tocou não conta.
        self.commit("chore: um nome na lista", self.t0 + 3600,
                    {"scripts/private-names.sha256": listed, "plugins/demo2/notas.md": f"de {name}\n"})
        self.fetch()
        got = self.criterion(self.t0 + 15 * DAY)
        self.assertEqual((got["vazados"], got["cumprido"]), (0, True))
        self.commit("docs(demo): nota", self.t0 + 7200, {NOTE.format(1): f"nota de {name}\n"})
        self.fetch()
        got = self.criterion(self.t0 + 15 * DAY)
        self.assertEqual((got["vazados"], got["cumprido"]), (1, False))
        # O worktree do clone da loja não mudou: o nome só está no origin/main.
        self.assertFalse((self.w.store / NOTE.format(1)).exists())

    def test_a_leaked_name_in_a_touched_symlink_counts(self):
        """O blob de um link simbólico é o caminho do alvo, e o sensor o lê."""
        self.autos(10)
        name = invented("elo")
        listed = (self.w.other / "scripts/private-names.sha256").read_text(encoding="utf-8")
        self.commit("chore: um nome na lista", self.t0 + 3600,
                    {"scripts/private-names.sha256": listed + _cpn().resumo(name) + "\n"})
        other = self.w.other
        self.w.git(other, "fetch", "-q", "origin")
        self.w.git(other, "reset", "-q", "--hard", "origin/main")
        try:
            os.symlink(f"{name}.md", other / "plugins/demo/atalho")
        except (OSError, NotImplementedError) as exc:
            self.skipTest(f"sem link simbólico aqui: {exc}")
        self.w.git(other, "add", "-A")
        date = f"@{self.t0 + 7200} +0000"
        self.w.git(other, "commit", "-q", "-m", "fix(demo): atalho\n\nRetrofit-Mode: autonomous\n",
                   env=dict(self.w.env, GIT_AUTHOR_DATE=date, GIT_COMMITTER_DATE=date))
        self.w.git(other, "push", "-q", "origin", "HEAD:main")
        self.fetch()
        got = self.criterion(self.t0 + 15 * DAY)
        self.assertEqual((got["publicados"], got["vazados"], got["cumprido"]), (11, 1, False))

    def test_startup_makes_no_fetch(self):
        now = int(time.time())
        self.autos(10, start=now - 15 * DAY)
        self.fetch()
        self.w.git(self.w.store, "remote", "set-url", "origin", str(self.w.tmp / "nao-existe.git"))
        with mock.patch.object(rw_store, "run_bytes", wraps=rw_store.run_bytes) as spy:
            expected = "retrofit-watch: " + phrase(self.criterion(now))
        self.assertFalse([c for c in spy.call_args_list if "fetch" in map(str, c.args[0])])
        out = self.run_hook("pending")
        self.assertEqual(out, {"systemMessage": expected})
        self.assertEqual(self.errors(), "")

    def test_criterion_is_cached_by_origin_main_sha(self):
        self.autos(10)
        self.fetch()

        def logs(spy):
            return [c for c in spy.call_args_list if "log" in map(str, c.args[0])]

        with mock.patch.object(rw_store, "run_bytes", wraps=rw_store.run_bytes) as spy:
            first = self.criterion(self.t0 + 13 * DAY + 30)
            self.assertEqual(len(logs(spy)), 1)
            cache = json.loads((self.w.data / "criterio.json").read_text(encoding="utf-8"))
            self.assertEqual(cache["sha"], self.w.git(self.w.store, "rev-parse", "origin/main"))
            # M1: o mesmo sha um dia depois muda `dias` e `cumprido`, sem ler o log de novo.
            second = self.criterion(self.t0 + 14 * DAY + 30)
            self.assertEqual(len(logs(spy)), 1)
            self.assertEqual((first["dias"], first["cumprido"]), (13, False))
            self.assertEqual((second["dias"], second["cumprido"]), (14, True))
            self.autos(1, start=self.t0 + 3600)
            self.fetch()
            third = self.criterion(self.t0 + 14 * DAY + 30)
            self.assertEqual(len(logs(spy)), 2)
            self.assertEqual(third["publicados"], 11)
            # O startup tem 10 s: toda chamada ao git do critério leva o teto de 3 s.
            calls = [c for c in spy.call_args_list if "git" in map(str, c.args[0])]
            self.assertTrue(calls)
            self.assertTrue(all(c.kwargs.get("timeout") == rw_store.STARTUP_TIMEOUT == 3 for c in calls), calls)
            # Cache ilegível ou de outro formato se refaz, sem exceção.
            head = self.w.git(self.w.store, "rev-parse", "origin/main")
            whole = {"sha": head, "commits": [], "revertidos": 0, "vazados": None}
            for broken in ("{", json.dumps([1]), json.dumps({"sha": head}), json.dumps(dict(whole, mais=1)),
                           json.dumps(dict(whole, commits="x")), json.dumps(dict(whole, commits=[["a", "1", "d"]])),
                           json.dumps(dict(whole, revertidos=-1)), json.dumps(dict(whole, vazados="0"))):
                (self.w.data / "criterio.json").write_text(broken, encoding="utf-8")
                self.assertEqual(self.criterion(self.t0 + 14 * DAY + 30), third)

    def test_criterion_timeout_is_cached_by_sha(self):
        """C9: o `git log` que estoura os 3 s grava {sha, estouro}; o mesmo sha não paga o teto de novo
        por 24 h, e o `origin/main` que anda mede de novo."""
        self.autos(10)
        self.fetch()
        real = rw_store.run_bytes
        state = {"slow": True}

        def slow_log(cmd, *args, **kwargs):
            if state["slow"] and "log" in map(str, cmd):
                return 124, b""
            return real(cmd, *args, **kwargs)

        def logs(spy):
            return [c for c in spy.call_args_list if "log" in map(str, c.args[0])]

        now = self.t0 + 15 * DAY
        head = self.w.git(self.w.store, "rev-parse", "origin/main")
        with mock.patch.object(rw_store, "run_bytes", side_effect=slow_log) as spy:
            with self.assertRaises(rw_store.StartupTimeout):
                self.criterion(now)
            cache = json.loads((self.w.data / "criterio.json").read_text(encoding="utf-8"))
            self.assertEqual(cache, {"sha": head, "estouro": now})
            self.assertEqual(len(logs(spy)), 1)
            # O mesmo sha, no mesmo instante e 60 s depois: None, sem `git log`.
            self.assertIsNone(self.criterion(now))
            self.assertIsNone(self.criterion(now + 60))
            self.assertEqual(len(logs(spy)), 1, "o cache negativo não poupou o git log")
            # Pelo aviso de startup: a linha sai sem o segmento do critério, e o errors.log não cresce.
            self.queue_one()
            before = self.errors()
            self.assertEqual(self.pending(now=now + 120), TODAY)
            self.assertEqual(self.errors(), before)
            self.assertEqual(len(logs(spy)), 1)
            # 24 h e 1 s depois do estouro: o critério mede de novo.
            later = now + rw_store.CRITERION_RETRY + 1
            self.assertEqual(rw_store.CRITERION_RETRY, 86400)
            with self.assertRaises(rw_store.StartupTimeout):
                self.criterion(later)
            self.assertEqual(len(logs(spy)), 2, "o prazo de 24 h não reabriu a medida")
            # O origin/main anda, sem estouro: o dicionário do critério.
            state["slow"] = False
            self.autos(1, start=self.t0 + 3600)
            self.fetch()
            got = self.criterion(later + 60)
            self.assertEqual(len(logs(spy)), 3)
            # A forma do estouro quebrada mede de novo, sem exceção: chama o git log e devolve o dicionário.
            # Final-F7: o estouro gravado no futuro (o relógio que voltou) também, e não cala o critério.
            head = self.w.git(self.w.store, "rev-parse", "origin/main")
            for n, broken in enumerate(({"sha": head, "estouro": "x"}, {"sha": head, "estouro": None},
                                        {"sha": head, "estouro": later, "mais": 1},
                                        {"sha": head, "estouro": later + 3600}), start=4):
                with self.subTest(broken=broken):
                    (self.w.data / "criterio.json").write_text(json.dumps(broken), encoding="utf-8")
                    self.assertEqual(self.criterion(later + 60), got)
                    self.assertEqual(len(logs(spy)), n)
        self.assertEqual((got["publicados"], got["cumprido"]), (11, True), "o sha novo não mediu de novo")


if __name__ == "__main__":
    unittest.main()
