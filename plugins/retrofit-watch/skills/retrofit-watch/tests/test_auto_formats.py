"""Testes do modo autônomo do retrofit-watch: os formatos dos arquivos do fluxo, a triagem das
lições e os verbos do registro (`triage`, `held`, `hold`, `approve`, `discard`).

Rodar: python3 plugins/retrofit-watch/skills/retrofit-watch/tests/test_auto_formats.py
Só pastas temporárias: nenhum teste toca a rede, o git, o `claude` real ou um `origin` real.
"""
import copy
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
import rw_auto  # noqa: E402

# O stdio do Python no Windows quando o Claude Code chama o script por pipe; reproduz em qualquer SO.
WINDOWS_STDIO = {"PYTHONIOENCODING": "cp1252"}
# Um caractere fora do cp1252 (a seta), montado em tempo de execução: `é` e `ç` existem no cp1252.
ARROW = chr(0x2192)


def lesson(n, plugin="alfa", skill=None, **over):
    """Uma lição publicável; `over` muda um campo."""
    data = {"n": n, "plugin": plugin, "skill": skill or plugin, "tipo": "pitfall",
            "evidencia": {"texto": "o comando saiu 1", "transcript": "sessao.jsonl", "entrada": "u1"},
            "padrao": "o passo pulava a conferência", "resolveu": "conferir antes", "muda_description": False}
    data.update(over)
    return data


def parecer(n, **over):
    """Um parecer que deixa a lição publicável; `over` muda um campo."""
    data = {"n": n, "evidencia_confere": True, "coberta": None, "generica": True, "procede": "procede",
            "basta_o_transcript": None, "nao_capturar": None, "nota": ""}
    data.update(over)
    return data


def pedido(rid, *plugins, skills=None):
    skills = skills or {}
    return {"id": rid, "sessao": "s1", "ts": 1, "transcript": "sessao.jsonl", "cwd": "projeto", "modo": "auto",
            "skills": [{"key": f"full:{p}", "plugin": p, "label": p, "skills": list(skills.get(p, []))}
                       for p in plugins]}


def retrofit(rid="r1", lote="alfa"):
    return {"id": rid, "lote": lote, "plugin": "alfa", "tipo": "auto", "tentativa": 1, "worktree": "wt",
            "ramo": "retrofit-auto/alfa-r1", "base": "abc", "licoes": [1], "fases": None, "commit": None,
            "versao": None, "patch": None}


def anonimato():
    return {"patch": "abc", "termos": [{"termo": "palavra", "veredito": "publico", "nota": ""}],
            "regra_repetida": None, "fora_das_licoes": None}


def line(rid, item, resultado, motivo, plugin="alfa", detalhe="", licoes=(1,)):
    lote = None if "#" in item else item.split("/", 1)[1]
    return {"ts": 1, "sessao": "s1", "id": rid, "lote": lote, "plugin": plugin, "item": item,
            "licoes": list(licoes), "resultado": resultado, "motivo": motivo, "detalhe": detalhe,
            "commit": None, "ramo": None, "worktree": None, "versao": None, "aprovado": None, "instalacao": None}


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(os.path.realpath(tempfile.mkdtemp(prefix="rw-formats-")))
        self.home = self.tmp / "home"
        (self.home / ".claude").mkdir(parents=True)
        self.data = self.tmp / "data"
        self.data.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def ctx(self):
        return rw.Context(home=self.home, data_dir=self.data)

    def config(self, **keys):
        (self.home / ".claude/retrofit-watch.json").write_text(json.dumps(keys))

    def retro(self, rid, lessons, pareceres, plugins=None, skills=None, folder=None):
        folder = folder or self.data / "auto" / rid
        folder.mkdir(parents=True, exist_ok=True)
        plugins = plugins or sorted({les["plugin"] for les in lessons})
        (folder / "pedido.json").write_text(json.dumps(pedido(rid, *plugins, skills=skills)))
        (folder / "licoes.json").write_text(json.dumps({"id": rid, "licoes": lessons}))
        (folder / "veredito.json").write_text(json.dumps({"id": rid, "base": "abc", "licoes": pareceres}))
        return folder

    def registry_lines(self):
        path = self.data / rw_auto.REGISTRY
        if not path.exists():
            return []
        return [json.loads(raw) for raw in path.read_text(encoding="utf-8").splitlines() if raw.strip()]

    def add_lines(self, *lines):
        with open(self.data / rw_auto.REGISTRY, "a", encoding="utf-8") as fh:
            for item in lines:
                fh.write(json.dumps(item, ensure_ascii=False) + "\n")

    def cli(self, *args, env=None, data=True):
        full_env = dict(os.environ, HOME=str(self.home), PYTHONDONTWRITEBYTECODE="1")
        full_env.pop("CLAUDE_PLUGIN_DATA", None)
        full_env.pop("RETROFIT_WATCH", None)
        if data:
            full_env["CLAUDE_PLUGIN_DATA"] = str(self.data)
        full_env.update(env or {})
        return subprocess.run([sys.executable, str(SCRIPT), *args], input=b"", capture_output=True,
                              env=full_env, timeout=20)

    def assert_refused(self, proc, *needles):
        err = proc.stderr.decode("utf-8", "replace")
        self.assertEqual(proc.returncode, 2, err)
        self.assertNotIn("Traceback", err)
        for needle in needles:
            self.assertIn(needle, err)


class ClassifyTest(Base):
    def test_classification_table(self):
        rows = [
            ("sem-veredito", {}, None, ("segurar", "sem-veredito")),
            ("coberta", {}, {"coberta": "SKILL.md:12"}, ("descartar", "coberta")),
            ("do-projeto", {}, {"generica": False}, ("descartar", "do-projeto")),
            ("nao-procede", {}, {"procede": "nao-procede"}, ("descartar", "nao-procede")),
            ("sem-evidencia", {}, {"evidencia_confere": False}, ("descartar", "sem-evidencia")),
            ("nao-capturar", {}, {"nao_capturar": "erro transitório"}, ("descartar", "nao-capturar")),
            ("nao-reproduzivel", {}, {"procede": "nao-reproduzivel"}, ("segurar", "nao-reproduzivel")),
            ("nao-reproduzivel com transcript", {}, {"procede": "nao-reproduzivel", "basta_o_transcript": "o erro está literal"},
             ("publicar", None)),
            ("sem-correcao", {"resolveu": None}, {}, ("segurar", "sem-correcao")),
            ("muda-description", {"muda_description": True}, {}, ("ramo-pronto", "muda-description")),
            ("publicavel", {}, {}, ("publicar", None)),
        ]
        for label, lesson_over, parecer_over, expected in rows:
            with self.subTest(label):
                opinion = None if parecer_over is None else parecer(1, **parecer_over)
                self.assertEqual(rw_auto.classify(lesson(1, **lesson_over), opinion), expected)

    def test_covered_wins_over_description(self):
        self.assertEqual(rw_auto.classify(lesson(1, muda_description=True), parecer(1, coberta="SKILL.md:3")),
                         ("descartar", "coberta"))
        # O3: o descarte vence o que seguraria ou mandaria ao ramo pronto.
        discards = {"coberta": {"coberta": "SKILL.md:3"}, "do-projeto": {"generica": False},
                    "nao-procede": {"procede": "nao-procede"}, "sem-evidencia": {"evidencia_confere": False},
                    "nao-capturar": {"nao_capturar": "narrativa de tarefa única"}}
        for reason, over in discards.items():
            for label, lesson_over in (("sem correção", {"resolveu": None}), ("description", {"muda_description": True})):
                with self.subTest(reason=reason, other=label):
                    self.assertEqual(rw_auto.classify(lesson(1, **lesson_over), parecer(1, **over)),
                                     ("descartar", reason))


class TriageTest(Base):
    def test_unconfirmed_evidence_and_do_not_capture_are_discarded(self):
        self.retro("r1", [lesson(1), lesson(2)],
                   [parecer(1, evidencia_confere=False), parecer(2, nao_capturar="falha de ambiente")])
        got = rw_auto.triage(self.ctx(), "r1")
        self.assertEqual(got["lotes"], [])
        self.assertEqual([(d["item"], d["motivo"]) for d in got["descartar"]],
                         [("r1/alfa#1", "sem-evidencia"), ("r1/alfa#2", "nao-capturar")])
        lines = self.registry_lines()
        self.assertEqual([(x["item"], x["resultado"], x["motivo"]) for x in lines],
                         [("r1/alfa#1", "descartado", "sem-evidencia"), ("r1/alfa#2", "descartado", "nao-capturar")])
        self.assertEqual(lines[1]["detalhe"], "falha de ambiente")
        self.assertEqual(rw_auto.held(self.ctx()), [])

    def test_lesson_outside_the_request_is_held(self):
        self.config(manual=["skill-manual", "plugin-manual"], exclude=["skill-excluida"])
        lessons = [
            lesson(1, plugin="fora"),                                   # o plugin não está no pedido
            lesson(2, plugin="retrofit-skill", skill="outra"),          # sempre excluído
            lesson(3, plugin="gama", skill="skill-manual"),             # a skill está em `manual`
            lesson(4, plugin="plugin-manual", skill="outra"),           # o plugin está em `manual`
            lesson(5, plugin="gama", skill="skill-excluida"),           # a skill está no `exclude`
            lesson(6, plugin="delta", skill="outra"),                   # o pedido lista as skills e não esta
            lesson(7, plugin="delta", skill="listada"),                 # controle: listada
            lesson(8, plugin="gama", skill="qualquer"),                 # controle: pedido sem lista de skills
        ]
        self.retro("r1", lessons, [parecer(n) for n in range(1, 9)],
                   plugins=["retrofit-skill", "gama", "plugin-manual", "delta"], skills={"delta": ["listada"]})
        got = rw_auto.triage(self.ctx(), "r1")
        held = {d["item"]: d["motivo"] for d in got["segurar"]}
        expected = {f"r1/{p}#{n}": "fora-do-pedido" for n, p in
                    ((1, "fora"), (2, "retrofit-skill"), (3, "gama"), (4, "plugin-manual"), (5, "gama"), (6, "delta"))}
        self.assertEqual(held, expected)
        self.assertEqual([(lote["lote"], lote["licoes"]) for lote in got["lotes"]], [("delta", [7]), ("gama", [8])])

    def test_in_request_reads_the_request_entry(self):
        ctx = self.ctx()
        request = pedido("r1", "alfa", "beta", skills={"beta": ["um"]})
        self.assertTrue(rw_auto.in_request(ctx, request, lesson(1)))
        self.assertTrue(rw_auto.in_request(ctx, request, lesson(1, plugin="beta", skill="um")))
        self.assertFalse(rw_auto.in_request(ctx, request, lesson(1, plugin="beta", skill="dois")))
        self.assertFalse(rw_auto.in_request(ctx, request, lesson(1, plugin="gama")))

    def test_triage_splits_lotes_and_orders_auto_first(self):
        lessons = [lesson(1, plugin="alfa", muda_description=True), lesson(2, plugin="beta"),
                   lesson(3, plugin="alfa"), lesson(4, plugin="alfa")]
        self.retro("r1", lessons, [parecer(n) for n in range(1, 5)])
        got = rw_auto.triage(self.ctx(), "r1")
        self.assertEqual(got["lotes"], [
            {"lote": "alfa", "plugin": "alfa", "tipo": "auto", "licoes": [3, 4]},
            {"lote": "beta", "plugin": "beta", "tipo": "auto", "licoes": [2]},
            {"lote": "alfa__description", "plugin": "alfa", "tipo": "description", "licoes": [1]},
        ])
        self.assertEqual(self.registry_lines(), [], "lição de lote não ganha linha na triagem")

    def test_triage_writes_held_and_discarded_lines_once(self):
        self.retro("r1", [lesson(1, resolveu=None), lesson(2)], [parecer(1), parecer(2, coberta="SKILL.md:9")])
        first = rw_auto.triage(self.ctx(), "r1")
        second = rw_auto.triage(self.ctx(), "r1")
        self.assertEqual(first, second)
        lines = self.registry_lines()
        self.assertEqual([(x["item"], x["resultado"], x["motivo"]) for x in lines],
                         [("r1/alfa#1", "segurado", "sem-correcao"), ("r1/alfa#2", "descartado", "coberta")])
        self.assertEqual(lines[1]["detalhe"], "SKILL.md:9")
        self.assertEqual((lines[0]["sessao"], lines[0]["id"], lines[0]["licoes"], lines[0]["lote"]), ("s1", "r1", [1], None))
        self.assertEqual(set(lines[0]), set(line("r1", "r1/alfa#1", "segurado", "x")))

    def test_lesson_missing_from_verdict_is_held(self):
        self.retro("r1", [lesson(1), lesson(2)], [parecer(1)])
        got = rw_auto.triage(self.ctx(), "r1")
        self.assertEqual([(d["item"], d["motivo"]) for d in got["segurar"]], [("r1/alfa#2", "sem-veredito")])
        self.assertEqual(got["lotes"], [{"lote": "alfa", "plugin": "alfa", "tipo": "auto", "licoes": [1]}])

    def test_triage_refuses_a_file_of_another_retro(self):
        # Item 7: cada arquivo da pasta da retro leva o `id` dela. O `id` de outra retro válida num só
        # arquivo é Malformed, antes de gravar linha; senão um veredito alheio casaria lições pelo número.
        self.retro("r2", [lesson(1), lesson(2, resolveu=None)], [parecer(1), parecer(2)])
        for name in ("pedido.json", "licoes.json", "veredito.json"):
            with self.subTest(arquivo=name):
                # Cada subteste parte do registro vazio: o mutante de um leitor não reprova os outros.
                (self.data / rw_auto.REGISTRY).unlink(missing_ok=True)
                folder = self.retro("r1", [lesson(1), lesson(2, resolveu=None)], [parecer(1), parecer(2)])
                data = json.loads((folder / name).read_text(encoding="utf-8"))
                data["id"] = "r2"
                (folder / name).write_text(json.dumps(data), encoding="utf-8")
                with self.assertRaises(rw_auto.Malformed) as caught:
                    rw_auto.triage(self.ctx(), "r1")
                self.assertIn("outra retro", str(caught.exception))
                self.assertIn(name, str(caught.exception))
                self.assertEqual(self.registry_lines(), [])
                self.assert_refused(self.cli("triage", "r1"), "outra retro")
                self.assertEqual(self.registry_lines(), [])

    def test_flow_finished_refuses_lessons_of_another_retro(self):
        """T3-c1: o licoes.json de outra retro não fecha o fluxo, nem com linha para cada número dele."""
        folder = self.retro("r1", [lesson(1)], [parecer(1)])
        self.add_lines(line("r1", "r1/alfa#1", "descartado", "coberta"))
        self.assertTrue(rw_auto.flow_finished(self.ctx(), {"id": "r1"}))
        (folder / "licoes.json").write_text(json.dumps({"id": "r2", "licoes": [lesson(1)]}))
        self.assertFalse(rw_auto.flow_finished(self.ctx(), {"id": "r1"}))

    def test_triage_flow_closes_the_request(self):
        self.retro("r1", [lesson(1, resolveu=None)], [parecer(1)])
        rw_auto.triage(self.ctx(), "r1")
        self.assertTrue(rw_auto.flow_finished(self.ctx(), {"id": "r1"}))


class FormatTest(Base):
    def write(self, name, data, rid="r1"):
        folder = self.data / "auto" / rid
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / name
        path.write_bytes(data if isinstance(data, bytes) else json.dumps(data).encode("utf-8"))
        return path

    def assert_malformed(self, loader, path, *needles):
        with self.assertRaises(rw_auto.Malformed) as caught:
            loader(path)
        for needle in needles:
            self.assertIn(needle, str(caught.exception))

    def test_malformed_verdict_is_a_refusal_not_a_traceback(self):
        good = {"id": "r1", "base": "abc", "licoes": [parecer(1)]}
        extra = copy.deepcopy(good)
        extra["licoes"][0]["opiniao"] = "x"
        domain = copy.deepcopy(good)
        domain["licoes"][0]["procede"] = "talvez"
        raw = json.dumps(good).encode("utf-8")
        cases = {
            "chave a mais": (json.dumps(extra).encode(), "`opiniao`"),
            "procede fora do domínio": (json.dumps(domain).encode(), "`procede`"),
            "BOM": (b"\xef\xbb\xbf" + raw, "JSON"),
            "cerca de código": (b"```json\n" + raw + b"\n```\n", "JSON"),
            "lista no lugar de objeto": (json.dumps([parecer(1)]).encode(), "objeto"),
            "bytes fora do UTF-8": (b'{"id": "r1\xff"}', "JSON"),
        }
        for label, (data, needle) in cases.items():
            with self.subTest(label):
                path = self.write("veredito.json", data)
                self.assert_malformed(rw_auto.load_veredito, path, "veredito.json", needle)
        self.retro("r1", [lesson(1)], [parecer(1)])
        self.write("veredito.json", json.dumps(domain).encode())
        self.assert_refused(self.cli("triage", "r1"), "veredito.json", "`procede`")
        self.assertEqual(self.registry_lines(), [])

    def test_missing_file_is_malformed(self):
        self.assert_malformed(rw_auto.load_veredito, self.data / "auto/r1/veredito.json", "veredito.json")

    def test_anonimato_without_the_judgement_keys_is_malformed(self):
        for key in ("regra_repetida", "fora_das_licoes", "patch"):
            with self.subTest(key):
                data = anonimato()
                del data[key]
                self.assert_malformed(rw_auto.load_anonimato, self.write("anonimato.json", data), f"`{key}`")
        self.assertEqual(rw_auto.load_anonimato(self.write("anonimato.json", anonimato())), anonimato())

    def test_load_retrofit_accepts_null_until_seal(self):
        data = retrofit()
        self.assertEqual(rw_auto.load_retrofit(self.write("retrofit.json", data)), data)
        sealed = dict(data, fases=["fase-1"], commit="abc", versao="1.2.3", patch="def")
        self.assertEqual(rw_auto.load_retrofit(self.write("retrofit.json", sealed)), sealed)
        for key in ("commit", "versao", "patch", "fases"):
            with self.subTest(key):
                missing = retrofit()
                del missing[key]
                self.assert_malformed(rw_auto.load_retrofit, self.write("retrofit.json", missing), f"`{key}`")

    def test_extra_and_missing_keys_are_malformed_in_every_file(self):
        files = {
            "pedido.json": (rw_auto.load_pedido, pedido("r1", "alfa")),
            "licoes.json": (rw_auto.load_licoes, {"id": "r1", "licoes": [lesson(1)]}),
            "veredito.json": (rw_auto.load_veredito, {"id": "r1", "base": "abc", "licoes": [parecer(1)]}),
            "retrofit.json": (rw_auto.load_retrofit, retrofit()),
            "anonimato.json": (rw_auto.load_anonimato, anonimato()),
        }
        for name, (loader, data) in files.items():
            with self.subTest(name, case="válido"):
                loader(self.write(name, data))
            with self.subTest(name, case="chave a mais"):
                self.assert_malformed(loader, self.write(name, dict(data, sobra=1)), name, "`sobra`")
            with self.subTest(name, case="chave faltando"):
                missing = dict(data)
                key = sorted(missing)[0]
                del missing[key]
                self.assert_malformed(loader, self.write(name, missing), name, f"`{key}`")

    def test_nested_extra_and_missing_keys_are_malformed(self):
        cases = [
            ("licoes.json", rw_auto.load_licoes, {"id": "r1", "licoes": [dict(lesson(1), sobra=1)]}, "`sobra`"),
            ("licoes.json", rw_auto.load_licoes, {"id": "r1", "licoes": [{k: v for k, v in lesson(1).items() if k != "padrao"}]}, "`padrao`"),
            ("licoes.json", rw_auto.load_licoes, {"id": "r1", "licoes": [dict(lesson(1), evidencia={"texto": "x", "transcript": "t"})]}, "`entrada`"),
            ("veredito.json", rw_auto.load_veredito, {"id": "r1", "base": "a", "licoes": [{k: v for k, v in parecer(1).items() if k != "nota"}]}, "`nota`"),
            ("anonimato.json", rw_auto.load_anonimato, dict(anonimato(), termos=[{"termo": "x", "veredito": "publico"}]), "`nota`"),
            ("pedido.json", rw_auto.load_pedido, dict(pedido("r1"), skills=[{"key": "k", "plugin": "alfa", "label": "l"}]), "`skills`"),
        ]
        for name, loader, data, needle in cases:
            with self.subTest(name, needle=needle):
                self.assert_malformed(loader, self.write(name, data), name, needle)

    def test_each_field_out_of_domain_is_malformed(self):
        """Um valor fora do domínio por campo, para cada campo de cada arquivo."""
        def at(data, path, value):
            data = copy.deepcopy(data)
            target = data
            for step in path[:-1]:
                target = target[step]
            target[path[-1]] = value
            return data

        files = {
            "pedido.json": (rw_auto.load_pedido, pedido("r1", "alfa"), [
                (("id",), "../x"), (("sessao",), ""), (("ts",), "agora"), (("ts",), True), (("ts",), -1),
                (("transcript",), 5), (("cwd",), None), (("modo",), "manual"), (("skills",), {}),
                (("skills", 0), "alfa"), (("skills", 0), ["key", "plugin", "label", "skills"]), (("skills", 0, "key"), ""), (("skills", 0, "plugin"), "../x"),
                (("skills", 0, "label"), 5), (("skills", 0, "skills"), "um"), (("skills", 0, "skills"), [""])]),
            "licoes.json": (rw_auto.load_licoes, {"id": "r1", "licoes": [lesson(1)]}, [
                (("id",), "a b"), (("licoes",), {}), (("licoes", 0), "lição"),
                (("licoes", 0, "n"), 0), (("licoes", 0, "n"), True), (("licoes", 0, "n"), "1"),
                (("licoes", 0, "plugin"), "a/b"), (("licoes", 0, "skill"), ""), (("licoes", 0, "tipo"), "outro"),
                (("licoes", 0, "evidencia"), "texto solto"), (("licoes", 0, "evidencia", "texto"), "  "),
                (("licoes", 0, "evidencia", "transcript"), None), (("licoes", 0, "evidencia", "entrada"), 7),
                (("licoes", 0, "padrao"), ""), (("licoes", 0, "resolveu"), ""), (("licoes", 0, "muda_description"), "sim")]),
            "veredito.json": (rw_auto.load_veredito, {"id": "r1", "base": "abc", "licoes": [parecer(1)]}, [
                (("id",), "../x"), (("base",), ""), (("licoes",), {}), (("licoes", 0), []),
                (("licoes", 0, "n"), -2), (("licoes", 0, "evidencia_confere"), 1), (("licoes", 0, "coberta"), "SKILL.md"),
                (("licoes", 0, "coberta"), ":3"), (("licoes", 0, "coberta"), "SKILL.md:0"),
                (("licoes", 0, "coberta"), "SKILL.md:3 e mais"),
                (("licoes", 0, "generica"), None), (("licoes", 0, "procede"), "sim"),
                (("licoes", 0, "basta_o_transcript"), True), (("licoes", 0, "nao_capturar"), ""),
                (("licoes", 0, "nota"), 3)]),
            "retrofit.json": (rw_auto.load_retrofit, retrofit(), [
                (("id",), "../x"), (("lote",), "a#1"), (("plugin",), ""), (("plugin",), 7), (("tipo",), "manual"),
                (("tentativa",), 0), (("tentativa",), True), (("worktree",), ""), (("ramo",), None),
                (("base",), 3), (("licoes",), []), (("licoes",), [0]), (("fases",), "fase-1"), (("fases",), [""]),
                (("commit",), ""), (("versao",), 1), (("patch",), "")]),
            "anonimato.json": (rw_auto.load_anonimato, anonimato(), [
                (("patch",), None), (("termos",), {}), (("termos", 0), "palavra"),
                (("termos", 0, "termo"), ""), (("termos", 0, "veredito"), "talvez"), (("termos", 0, "nota"), 1),
                (("regra_repetida",), ""), (("fora_das_licoes",), False)]),
        }
        for name, (loader, good, bad) in files.items():
            loader(self.write(name, good))
            for path, value in bad:
                with self.subTest(name, field=path, value=value):
                    field = next(step for step in reversed(path) if isinstance(step, str))
                    self.assert_malformed(loader, self.write(name, at(good, path, value)), name, f"`{field}`")

    def test_repeated_lesson_number_is_malformed(self):
        self.assert_malformed(rw_auto.load_licoes, self.write("licoes.json", {"id": "r1", "licoes": [lesson(1), lesson(1)]}),
                              "licoes.json", "`n`")
        self.assert_malformed(rw_auto.load_veredito,
                              self.write("veredito.json", {"id": "r1", "base": "a", "licoes": [parecer(2), parecer(2)]}),
                              "veredito.json", "`n`")

    def test_loaders_return_lessons_by_number(self):
        lessons = rw_auto.load_licoes(self.write("licoes.json", {"id": "r1", "licoes": [lesson(2), lesson(1)]}))
        self.assertEqual(list(lessons), ["2", "1"])
        self.assertEqual(lessons["1"], lesson(1))
        opinions = rw_auto.load_veredito(self.write("veredito.json", {"id": "r1", "base": "a", "licoes": [parecer(1)]}))
        self.assertEqual(opinions, {"1": parecer(1)})

    def test_pedido_written_by_the_hook_loads(self):
        self.config(mode="auto")
        entries = [{"key": "full:alfa", "arg": "alfa", "label": "alfa", "skills": ["um"]}]
        written = rw_auto.open_request(self.ctx(), {"session_id": "s1", "cwd": "projeto"}, entries)
        loaded = rw_auto.load_pedido(rw_auto.retro_dir(self.ctx(), written["id"]) / "pedido.json")
        self.assertEqual(loaded, written)
        self.assertIsNone(loaded["transcript"])

    def test_reason_sets(self):
        self.assertEqual(set(rw_auto.LESSON_REASONS), {"coberta", "do-projeto", "nao-procede", "sem-evidencia",
                                                       "nao-capturar", "sem-veredito", "fora-do-pedido",
                                                       "nao-reproduzivel", "sem-correcao"})
        self.assertEqual(rw_auto.OWNER_REASONS, ("descartado-pelo-dono", "resolvido-manual"))
        self.assertEqual(rw_auto.AGENT_REASONS, ("executor-falhou", "executor-recusou"))
        self.assertEqual(rw_auto.RETROFIT_KEYS, {"id", "lote", "plugin", "tipo", "tentativa", "worktree", "ramo",
                                                 "base", "licoes", "fases", "commit", "versao", "patch"})
        self.assertEqual(rw_auto.ANONIMATO_KEYS, {"patch", "termos", "regra_repetida", "fora_das_licoes"})


class VerbTest(Base):
    def test_path_traversal_in_id_or_lote_is_refused(self):
        # Uma retro inteira e válida no lugar para onde o `../x` leva: só o padrão a recusa.
        self.retro("x", [lesson(1)], [parecer(1)], folder=self.data / "x")
        self.add_lines(line("r1", "r1/../x", "segurado", "teto"))
        ctx = self.ctx()
        for label, call in (("triage", lambda: rw_auto.triage(ctx, "../x")),
                            ("approve", lambda: rw_auto.approve(ctx, "r1", "../x"))):
            with self.subTest(label):
                with self.assertRaises(rw_auto.Malformed):
                    call()
        self.assertFalse((self.data / "auto/x").exists(), "nada gravado fora da pasta da retro")
        self.assert_refused(self.cli("approve", "r1", "../x"), "lote")

    def test_item_must_belong_to_the_id_and_have_a_safe_shape(self):
        self.retro("r1", [lesson(1)], [parecer(1)])
        self.retro("r2", [lesson(1)], [parecer(1)])
        # Cada item mal formado tem linha `segurado`: só a conferência do formato o recusa.
        items = ("r2/alfa", "r1/../x", "r1/alfa#x", "r1/alfa#0", "r1/", "r1", None)
        self.add_lines(*[dict(line("r1", "r1/alfa", "segurado", "teto"), item=item) for item in items])
        ctx = self.ctx()
        for item in items:
            with self.subTest(item):
                with self.assertRaises(rw_auto.Malformed) as caught:
                    rw_auto.discard(ctx, "r1", item)
                self.assertIn("item fora do formato", str(caught.exception))
                with self.assertRaises(rw_auto.Malformed):
                    rw_auto.hold_item(ctx, "r1", item, "executor-falhou")

    def test_held_lists_only_open_items(self):
        self.add_lines(line("r1", "r1/alfa#1", "segurado", "sem-correcao"),
                       line("r1", "r1/beta", "segurado", "teto", plugin="beta"),
                       line("r1", "r1/beta", "publicado", None, plugin="beta"),
                       line("r1", "r1/alfa#2", "descartado", "coberta"))
        self.assertEqual([x["item"] for x in rw_auto.held(self.ctx())], ["r1/alfa#1"])
        self.add_lines(line("r1", "r1/gama", "erro", "push", plugin="gama"))
        self.assertEqual([x["item"] for x in rw_auto.held(self.ctx())], ["r1/alfa#1", "r1/gama"])
        proc = self.cli("held")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual([x["item"] for x in json.loads(proc.stdout)], ["r1/alfa#1", "r1/gama"])

    def test_last_lines_keeps_the_last_line_of_each_item(self):
        registry = [{"item": "a", "resultado": "segurado"}, {"item": "b"}, {"item": "a", "resultado": "publicado"},
                    {"item": None}, {"sem": "item"}]
        self.assertEqual(rw_auto.last_lines(registry), {"a": registry[2], "b": registry[1]})

    def test_approve_needs_a_held_lote(self):
        self.retro("r1", [lesson(1)], [parecer(1)])
        self.add_lines(line("r1", "r1/alfa", "publicado", None), line("r1", "r1/beta#1", "segurado", "teto"))
        self.assert_refused(self.cli("approve", "r1", "alfa"), "segurado")
        self.assertFalse((self.data / "auto/r1/alfa/aprovado.json").exists())

    def test_approve_appends_each_reason(self):
        self.retro("r1", [lesson(1)], [parecer(1)])
        self.add_lines(line("r1", "r1/alfa", "segurado", "muda-description"))
        proc = self.cli("approve", "r1", "alfa")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(json.loads(proc.stdout)["motivos"], ["muda-description"])
        self.add_lines(line("r1", "r1/alfa", "segurado", "teto"))
        path = rw_auto.approve(self.ctx(), "r1", "alfa")
        self.assertEqual(path, self.data / "auto/r1/alfa/aprovado.json")
        rw_auto.approve(self.ctx(), "r1", "alfa")
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(data["motivos"], ["muda-description", "teto"], "sem repetir e sem sobrescrever")
        self.assertEqual(set(data), {"id", "lote", "ts", "motivos"})
        self.assertEqual((data["id"], data["lote"]), ("r1", "alfa"))

    def test_approve_refuses_a_malformed_approval_file(self):
        self.add_lines(line("r1", "r1/alfa", "segurado", "teto"))
        folder = self.data / "auto/r1/alfa"
        folder.mkdir(parents=True)
        good = {"id": "r1", "lote": "alfa", "ts": 1, "motivos": []}
        bad = [dict(good, motivos="teto"), dict(good, motivos=[""]), dict(good, id="../x"), dict(good, lote="a b"),
               dict(good, ts="agora"), dict(good, sobra=1)]
        for raw in [json.dumps(x) for x in bad] + ["[]", "{quebrado"]:
            with self.subTest(raw):
                (folder / "aprovado.json").write_text(raw)
                with self.assertRaises(rw_auto.Malformed) as caught:
                    rw_auto.approve(self.ctx(), "r1", "alfa")
                self.assertIn("aprovado.json", str(caught.exception))
                self.assertEqual((folder / "aprovado.json").read_text(), raw, "o arquivo ruim fica como estava")

    def test_discard_accepts_resolved_by_hand(self):
        self.add_lines(line("r1", "r1/alfa#1", "segurado", "sem-correcao"), line("r1", "r1/beta", "erro", "push", plugin="beta"))
        proc = self.cli("discard", "r1", "r1/alfa#1", "--motivo", "resolvido-manual")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        last = self.registry_lines()[-1]
        self.assertEqual((last["item"], last["resultado"], last["motivo"], last["licoes"], last["sessao"]),
                         ("r1/alfa#1", "descartado", "resolvido-manual", [1], "s1"))
        self.assertEqual(json.loads(proc.stdout)["motivo"], "resolvido-manual")
        before = len(self.registry_lines())
        self.assert_refused(self.cli("discard", "r1", "r1/beta", "--motivo", "porque-sim"), "porque-sim")
        self.assertEqual(len(self.registry_lines()), before)
        got = rw_auto.discard(self.ctx(), "r1", "r1/beta")
        self.assertEqual((got["resultado"], got["motivo"], got["lote"], got["plugin"]),
                         ("descartado", "descartado-pelo-dono", "beta", "beta"))
        self.assertEqual(rw_auto.held(self.ctx()), [])

    def test_cli_discard_retro(self):
        folder = self.retro("r1", [lesson(1), lesson(2)], [parecer(1), parecer(2)])
        (folder / "veredito.json").unlink()
        self.add_lines(line("r1", "r1/alfa#1", "descartado", "coberta"))
        proc = self.cli("discard", "r1", "--retro", "--motivo", "resolvido-manual", env=WINDOWS_STDIO)
        self.assertEqual(proc.returncode, 0, proc.stderr.decode("utf-8", "replace"))
        self.assertTrue(proc.stdout.isascii())
        [got] = json.loads(proc.stdout)
        self.assertEqual((got["item"], got["licoes"], got["resultado"], got["motivo"]),
                         ("r1/alfa#2", [2], "descartado", "resolvido-manual"))
        self.assertEqual(self.registry_lines()[-1], got)
        self.assert_refused(self.cli("discard", "r1", "--retro"), "r1")
        self.assertEqual(len(self.registry_lines()), 2)

    def test_discard_needs_an_open_item(self):
        self.add_lines(line("r1", "r1/alfa", "publicado", None))
        for item in ("r1/alfa", "r1/beta#1"):
            with self.subTest(item):
                with self.assertRaises(rw_auto.Malformed):
                    rw_auto.discard(self.ctx(), "r1", item)
        self.assertEqual(len(self.registry_lines()), 1)

    def test_hold_item_writes_a_held_line_for_a_lote_of_the_triage(self):
        self.retro("r1", [lesson(1), lesson(2, muda_description=True), lesson(3)], [parecer(n) for n in (1, 2, 3)])
        got = rw_auto.hold_item(self.ctx(), "r1", "r1/alfa", "executor-falhou", "o teste quebrou")
        self.assertEqual((got["item"], got["resultado"], got["motivo"], got["detalhe"], got["licoes"], got["lote"],
                          got["plugin"], got["sessao"]),
                         ("r1/alfa", "segurado", "executor-falhou", "o teste quebrou", [1, 3], "alfa", "alfa", "s1"))
        proc = self.cli("hold", "r1", "r1/alfa__description", "executor-recusou")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(json.loads(proc.stdout)["licoes"], [2])
        self.assertEqual([x["item"] for x in rw_auto.held(self.ctx())], ["r1/alfa", "r1/alfa__description"])

    def test_hold_item_takes_a_lesson_of_a_lote(self):
        # O selo (rw_store.seal) segura assim a lição do lote que o executor deixou fora (ruling C9).
        self.retro("r1", [lesson(1), lesson(2, muda_description=True), lesson(3)], [parecer(n) for n in (1, 2, 3)])
        got = rw_auto.hold_item(self.ctx(), "r1", "r1/alfa#3", "executor-recusou", "fora do selo")
        self.assertEqual((got["item"], got["licoes"], got["lote"], got["plugin"], got["motivo"]),
                         ("r1/alfa#3", [3], "alfa", "alfa", "executor-recusou"))
        self.assertEqual(rw_auto.hold_item(self.ctx(), "r1", "r1/alfa#2", "executor-recusou")["lote"],
                         "alfa__description")
        for item in ("r1/alfa#9", "r1/beta#1"):
            with self.subTest(item):
                with self.assertRaises(rw_auto.Malformed) as caught:
                    rw_auto.hold_item(self.ctx(), "r1", item, "executor-recusou")
                self.assertIn(item, str(caught.exception))
        self.assertEqual(len(self.registry_lines()), 2)

    def test_hold_refuses_an_unknown_reason_or_lote(self):
        self.retro("r1", [lesson(1)], [parecer(1)])
        with self.assertRaises(rw_auto.Malformed) as caught:
            rw_auto.hold_item(self.ctx(), "r1", "r1/alfa", "teto")
        self.assertIn("teto", str(caught.exception))
        with self.assertRaises(rw_auto.Malformed) as caught:
            rw_auto.hold_item(self.ctx(), "r1", "r1/beta", "executor-falhou")
        self.assertIn("r1/beta", str(caught.exception))
        self.assert_refused(self.cli("hold", "r1", "r1/alfa", "inventado"), "inventado")
        self.assertEqual(self.registry_lines(), [])

    def test_new_subcommands_refuse_a_missing_or_ambiguous_data_dir(self):
        shutil.rmtree(self.data)
        commands = (("triage", "r1"), ("held",), ("hold", "r1", "r1/alfa", "executor-falhou"),
                    ("approve", "r1", "alfa"), ("discard", "r1", "r1/alfa#1"))
        for args in commands:
            with self.subTest(args, case="ausente"):
                proc = self.cli(*args, data=False)
                self.assert_refused(proc, "a pasta de dados não existe")
                self.assertEqual(proc.stdout, b"")
        for name in ("retrofit-watch-loja-a", "retrofit-watch-loja-b"):
            (self.home / ".claude/plugins/data" / name).mkdir(parents=True)
        for args in commands:
            with self.subTest(args, case="ambígua"):
                self.assert_refused(self.cli(*args, data=False), "mais de uma pasta de dados", "loja-a", "loja-b")
        self.assertFalse((self.home / ".claude/plugins/data/retrofit-watch").exists())

    def test_cli_usage_errors_exit_2(self):
        for args in (("triage",), ("held", "a"), ("hold", "r1", "r1/alfa"), ("approve", "r1"),
                     ("discard", "r1", "r1/alfa#1", "--motivo"), ("discard", "r1", "r1/alfa#1", "--outro", "x"),
                     ("discard", "r1", "--retro", "--motivo"), ("discard", "r1", "--retro", "--outro", "x"),
                     ("discard", "r1", "--retro", "r1/alfa#1")):
            with self.subTest(args):
                self.assert_refused(self.cli(*args), "uso")

    def test_cli_output_is_valid_json_on_cp1252(self):
        detail = f"passo 1 {ARROW} passo 2, conferência"
        self.add_lines(line("r1", "r1/alfa#1", "segurado", "sem-correcao", detalhe=detail))
        proc = self.cli("held", env=WINDOWS_STDIO)
        self.assertEqual(proc.returncode, 0, proc.stderr.decode("utf-8", "replace"))
        self.assertTrue(proc.stdout.isascii(), "o stdout do Windows é cp1252: só ASCII, com \\uXXXX")
        self.assertEqual(json.loads(proc.stdout)[0]["detalhe"], detail)


if __name__ == "__main__":
    unittest.main()
