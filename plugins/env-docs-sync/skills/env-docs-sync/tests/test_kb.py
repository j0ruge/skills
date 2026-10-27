"""Adaptador kb, trava de permissão (D1/CA5) e migração, contra o kb falso de `kb_falso.py`.

O kb falso roda como processo de verdade (o runner padrão), com a página guardada num JSON. Os papéis
são fictícios; a forma do JSON (`role_permissions[].role.display_name`, `fallback_permissions`) é a da
API do BookStack lida no KB de staging em 2026-10-27.
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from support import (CANARIO, MAQUINA, QUANDO, QUANDO_ISO, TESTES, config_exemplo, config_so_development,
                     criar_repo, eds, fixture)
from test_hook import AGORA

KB_FALSO = TESTES / "kb_falso.py"
PERMITIDOS = ("platform-team", "Admin")


def permissoes(*, herdando=False, fallback_view=False, papeis=(("platform-team", True), ("Admin", True))):
    fallback = {"inheriting": herdando, "view": None if herdando else fallback_view,
                "create": None if herdando else False, "update": None if herdando else False,
                "delete": None if herdando else False}
    return {"owner": {"id": 1, "name": "dono", "slug": "dono"},
            "role_permissions": [{"role_id": i, "view": view, "create": False, "update": view, "delete": False,
                                  "role": {"id": i, "display_name": nome}} for i, (nome, view) in enumerate(papeis, 1)],
            "fallback_permissions": fallback}


def config_kb(base=None):
    cfg = base or config_so_development()
    cfg["doc"].update({"python": sys.executable, "cli": str(KB_FALSO), "target": "staging"})
    return cfg


class KbFalso:
    """A página do kb falso, num JSON em `pasta`. Começa no template, sem blocos."""

    def __init__(self, pasta, config, perms=None):
        self.caminho = Path(pasta) / "kb-falso.json"
        html = eds.pagina_de_ambientes(config, {})
        self.gravar({"id": config["doc"]["page_id"], "target": "staging", "html": html, "revision_count": 1,
                     "permissoes": perms or permissoes()})

    def ler(self):
        return json.loads(self.caminho.read_text(encoding="utf-8"))

    def gravar(self, estado):
        self.caminho.write_text(json.dumps(estado), encoding="utf-8")

    def mudar(self, **campos):
        estado = self.ler()
        estado.update(campos)
        self.gravar(estado)

    def comandos(self):
        return [" ".join(a for a in argv if not a.startswith("--"))[:40] for argv in self.ler().get("chamadas", [])]

    def ambiente(self, extra=None):
        return {"PATH": os.environ["PATH"], "HOME": str(self.caminho.parent), "KB_FALSO_ESTADO": str(self.caminho),
                **(extra or {})}


class RunnerEspiao:
    def __init__(self):
        self.chamadas = []

    def __call__(self, argv, *, env, timeout, entrada=None):
        self.chamadas.append((list(argv), entrada))
        return eds.rodar_comando(argv, env=env, timeout=timeout, entrada=entrada)


class Permissao(unittest.TestCase):
    def test_restrita_aos_papeis_permitidos_passa(self):
        self.assertEqual(eds.permissao_restrita(permissoes(), PERMITIDOS), [])
        so_um = permissoes(papeis=(("platform-team", True),))
        self.assertEqual(eds.permissao_restrita(so_um, PERMITIDOS), [])

    def test_papel_extra_sem_view_passa(self):
        perms = permissoes(papeis=(("platform-team", True), ("Viewer", False)))
        self.assertEqual(eds.permissao_restrita(perms, PERMITIDOS), [])

    def test_recusas(self):
        casos = {
            "herda": permissoes(herdando=True),
            "fallback": permissoes(fallback_view=True),
            "Viewer": permissoes(papeis=(("platform-team", True), ("Viewer", True))),
        }
        for trecho, perms in casos.items():
            with self.subTest(trecho):
                motivos = eds.permissao_restrita(perms, PERMITIDOS)
                self.assertTrue(motivos)
                self.assertIn(trecho, " ".join(motivos))

    def test_resposta_estranha_falha_fechado(self):
        sem_view = permissoes()
        sem_view["role_permissions"][0]["view"] = None
        sem_view["role_permissions"][0]["role"]["display_name"] = "Outro"
        sem_nome = permissoes()
        sem_nome["role_permissions"][0]["role"] = None
        for perms in ({}, {"role_permissions": []}, {"fallback_permissions": {"inheriting": False}},
                      {"fallback_permissions": {"inheriting": False, "view": False}, "role_permissions": "x"},
                      sem_view, sem_nome):
            with self.subTest(perms=str(perms)[:50]):
                self.assertTrue(eds.permissao_restrita(perms, PERMITIDOS))


PAGINA = ('<p id="bkmrk-1">intro</p>\n<h2 id="bkmrk-2">Ambientes</h2>\n<table id="bkmrk-3"></table>\n'
          '<h2 id="bkmrk-4">[development]</h2>\n'
          '<h3 id="bkmrk-5">.env</h3><pre id="bkmrk-6"><code class="language-bash">A=1&amp;2\n</code></pre>\n<p id="bkmrk-7">ⓘ dev</p>\n'
          '<h3 id="bkmrk-8">a&amp;b/.env</h3><pre id="bkmrk-9"><code class="language-bash">B=2\n</code></pre>\n'
          '<h2 id="bkmrk-10">[staging]</h2>\n'
          '<h3 id="bkmrk-11">.env</h3><pre id="bkmrk-12"><code class="language-bash">S=3\n</code></pre>\n'
          '<h4>nota</h4><p>dentro do bloco</p>\n'
          '<h2 id="bkmrk-13">CI/CD</h2><p>x</p>')


class CorpoDaSecao(unittest.TestCase):
    def test_mesmo_caminho_em_dois_ambientes(self):
        self.assertEqual(eds.conteudo_do_bloco(eds.corpo_da_secao(PAGINA, "[development]", ".env")), "A=1&2\n")
        corpo_stg = eds.corpo_da_secao(PAGINA, "[staging]", ".env")
        self.assertEqual(eds.conteudo_do_bloco(corpo_stg), "S=3\n")
        self.assertIn("dentro do bloco", corpo_stg, "h4 não fecha a seção do h3")
        self.assertNotIn("CI/CD", corpo_stg)

    def test_texto_do_heading_com_entidade_e_caminho_que_falta(self):
        self.assertEqual(eds.conteudo_do_bloco(eds.corpo_da_secao(PAGINA, "[development]", "a&b/.env")), "B=2\n")
        self.assertIsNone(eds.corpo_da_secao(PAGINA, "[development]", "b/.env"))
        self.assertIsNone(eds.corpo_da_secao(PAGINA, "[production]", ".env"))
        self.assertIsNone(eds.corpo_da_secao(PAGINA, "[staging]", "a&b/.env"), "não sai da faixa do h2")

    def test_ambiguidade_e_erro(self):
        dobrada = PAGINA.replace("<h3 id=\"bkmrk-8\">a&amp;b/.env</h3>", "<h3>.env</h3>")
        with self.assertRaises(eds.ErroEnvDocs):
            eds.corpo_da_secao(dobrada, "[development]", ".env")


class BaseKb(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.config = config_kb()
        self.kb = KbFalso(base, self.config)
        self.runner = RunnerEspiao()
        self.ctx = eds.Contexto(hostname=lambda: MAQUINA, agora=lambda: AGORA, pasta_de_estado=base / "dados",
                                ambiente=self.kb.ambiente(), runner=self.runner)
        self.destino = eds.DestinoKb(self.config, self.ctx, commit="abc1234def")

    def tearDown(self):
        self.tmp.cleanup()

    def op(self, acao, caminho=".env", conteudo=f"DB_PASSWORD={CANARIO}\n", ambiente="development"):
        dados = conteudo.encode()
        estado = eds.estado_vazio()
        if acao != "criar":
            estado["environments"][ambiente] = {caminho: {"sha256": "0" * 64, "synced_at": QUANDO_ISO}}
        atuais = {ambiente: {} if acao == "marcar_ausente" else {caminho: dados}}
        (op,) = eds.planejar(estado, atuais, sincronizado_em=QUANDO, commit="abc1234def" if ambiente == "development" else None,
                             ler_corpo=self.destino.ler_corpo)
        self.assertEqual(op.acao, acao)
        return op

    def argv_de(self, sub):
        return [argv for argv, _ in self.runner.chamadas if sub in " ".join(argv)]


class DestinoKbTestes(BaseKb):
    def test_criar_chama_section_set_com_stdin_create_e_changelog(self):
        op = self.op("criar")
        self.destino.escrever(op)
        (argv,) = self.argv_de("section-set")
        self.assertEqual(argv[:2], [sys.executable, str(KB_FALSO)])
        for parte in ("page", "section-set", "4242", "--heading=.env", "--under=[development]", "--create",
                      "--stdin", "--apply", "--changelog=env-docs-sync: [development] .env @ abc1234"):
            self.assertIn(parte, argv)
        self.assertEqual(argv[-2:], ["--target", "staging"])
        entrada = [e for a, e in self.runner.chamadas if "section-set" in a][0]
        self.assertEqual(entrada, op.corpo.encode("utf-8"))
        self.assertFalse(any(CANARIO in parte for a, _ in self.runner.chamadas for parte in a))
        self.assertEqual(eds.conteudo_do_bloco(self.destino.ler_corpo("development", ".env")),
                         f"DB_PASSWORD={CANARIO}\n")
        self.assertEqual(self.kb.ler()["changelogs"], ["env-docs-sync: [development] .env @ abc1234"])

    def test_trocar_recria_o_bloco_que_sumiu_da_pagina(self):
        self.destino.escrever(self.op("trocar"))
        self.assertIn("--create", self.argv_de("section-set")[0])
        self.assertIsNotNone(self.destino.ler_corpo("development", ".env"))

    def test_remoto_usa_o_sha_do_arquivo_no_changelog(self):
        cfg = config_kb(config_exemplo())
        pasta = Path(self.tmp.name) / "k2"
        pasta.mkdir()
        kb = KbFalso(pasta, cfg)
        destino = eds.DestinoKb(cfg, eds.Contexto(ambiente=kb.ambiente(), runner=self.runner), commit="abc1234")
        op = self.op("criar", caminho="infra/staging/.env", ambiente="staging")
        destino.escrever(op)
        self.assertEqual(kb.ler()["changelogs"], [f"env-docs-sync: [staging] infra/staging/.env @ sha256:{op.sha256[:12]}"])

    def test_marcar_ausente_mantem_o_bloco_e_confere_o_callout(self):
        self.destino.escrever(self.op("criar"))
        op = self.op("marcar_ausente")
        self.destino.escrever(op)
        corpo = self.destino.ler_corpo("development", ".env")
        self.assertIn("ausente desde", corpo)
        self.assertIn(CANARIO, corpo)

    def test_permissao_lida_uma_vez_e_antes_da_primeira_escrita(self):
        self.destino.escrever(self.op("criar"))
        self.destino.escrever(self.op("trocar", conteudo="X=2\n"))
        comandos = self.kb.comandos()
        self.assertEqual(sum(1 for c in comandos if c.startswith("content-permissions")), 1)
        self.assertLess(next(i for i, c in enumerate(comandos) if c.startswith("content-permissions")),
                        next(i for i, c in enumerate(comandos) if c.startswith("page section-set")))

    def test_trava_recusa_sem_escrever(self):
        casos = {"herda": permissoes(herdando=True), "fallback": permissoes(fallback_view=True),
                 "Viewer": permissoes(papeis=(("platform-team", True), ("Viewer", True)))}
        for trecho, perms in casos.items():
            with self.subTest(trecho):
                self.kb.mudar(permissoes=perms, chamadas=[])
                destino = eds.DestinoKb(self.config, self.ctx, commit="abc1234")
                with self.assertRaises(eds.ErroDePermissao) as erro:
                    destino.escrever(self.op("criar"))
                self.assertIn(trecho, str(erro.exception))
                self.assertNotIn("page section-set", " ".join(self.kb.comandos()))
                self.assertEqual(self.kb.ler()["revision_count"], 1)

    def test_erros_do_kb_viram_aviso_com_codigo_e_backup(self):
        casos = [(1, "api", "HTTP 500", "/snap/a.json", "pode ter ocorrido"), (2, "usage", "h2 não encontrado", None, "usage"),
                 (3, "integrity", "releitura: o corpo da seção não ficou", "/snap/b.json", "pode ter ocorrido")]
        for rc, code, message, backup, trecho in casos:
            with self.subTest(rc=rc):
                self.kb.mudar(falhar={"page section-set": [rc, code, message, backup]})
                with self.assertRaises(eds.ErroEnvDocs) as erro:
                    self.destino.escrever(self.op("criar"))
                texto = str(erro.exception)
                self.assertIn(f"rc {rc}", texto)
                self.assertIn(trecho, texto)
                self.assertNotIn(CANARIO, texto)

    def test_releitura_divergente_falha(self):
        self.kb.mudar(sabotar=True)
        with self.assertRaises(eds.ErroEnvDocs) as erro:
            self.destino.escrever(self.op("criar"))
        self.assertIn("releitura", str(erro.exception))
        self.assertNotIn(CANARIO, str(erro.exception))

    def test_sem_mudanca_nao_cria_revisao(self):
        op = self.op("criar")
        self.destino.escrever(op)
        revisoes = self.kb.ler()["revision_count"]
        self.destino.escrever(op)
        self.assertEqual(self.kb.ler()["revision_count"], revisoes)

    def test_conteudo_ja_na_pagina_nao_reescreve_nem_com_outro_horario(self):
        """Outro host (outro estado) ou estado perdido: o bloco já tem o hash, só a linha ⓘ mudaria."""
        self.destino.escrever(self.op("criar"))
        revisoes = self.kb.ler()["revision_count"]
        outro_host = eds.DestinoKb(self.config, self.ctx, commit="fedcba9")
        (op,) = eds.planejar(eds.estado_vazio(), {"development": {".env": f"DB_PASSWORD={CANARIO}\n".encode()}},
                             sincronizado_em=QUANDO.replace(hour=23), commit="fedcba9")
        self.assertIs(outro_host.escrever(op), False, "False = o destino já tinha o bloco")
        self.assertEqual(self.kb.ler()["revision_count"], revisoes)
        self.assertEqual(sum(1 for c in self.kb.comandos() if c.startswith("page section-set")), 1)

    def test_arquivo_que_volta_com_o_mesmo_conteudo_tira_o_callout(self):
        self.destino.escrever(self.op("criar"))
        self.destino.escrever(self.op("marcar_ausente"))
        revisoes = self.kb.ler()["revision_count"]
        self.destino.escrever(self.op("trocar"))
        self.assertEqual(self.kb.ler()["revision_count"], revisoes + 1)
        self.assertNotIn("ausente desde", self.destino.ler_corpo("development", ".env"))

    def test_kb_que_nao_roda_vira_erro_sem_eco(self):
        cfg = config_kb()
        cfg["doc"]["cli"] = str(Path(self.tmp.name) / "nao-existe.py")
        with self.assertRaises(eds.ErroEnvDocs) as erro:
            eds.DestinoKb(cfg, self.ctx).ler_corpo("development", ".env")
        self.assertIn("rc 2", str(erro.exception))
        cfg["doc"]["python"] = str(Path(self.tmp.name) / "nao-existe-python")
        with self.assertRaises(eds.ErroEnvDocs) as erro:
            eds.DestinoKb(cfg, self.ctx).ler_corpo("development", ".env")
        self.assertIn("não encontrado", str(erro.exception))

    def test_til_em_cli_e_python_expande_pelo_home_do_ambiente(self):
        cfg = config_kb()
        cfg["doc"]["cli"] = "~/kb.py"
        destino = eds.DestinoKb(cfg, eds.Contexto(ambiente={"HOME": "/casa/x"}))
        self.assertEqual(destino.base[1], "/casa/x/kb.py")


class HookComKb(BaseKb):
    def setUp(self):
        super().setUp()
        self.raiz = criar_repo(Path(self.tmp.name) / "repo", {".env": f"DB_PASSWORD={CANARIO}\n"}, config=self.config)

    def hook(self, nome="claude-posttooluse-edit-env.json"):
        return eds.executar_hook(json.dumps(fixture(nome, self.raiz)), self.ctx)

    def arquivo(self):
        return eds.arquivo_de_estado(self.raiz, self.ctx.pasta_de_estado)

    def test_fabrica_padrao_escreve_no_kb_e_grava_o_estado(self):
        resposta = self.hook()
        self.assertIn("atualizada", resposta.mensagem)
        self.assertTrue(self.arquivo().is_file())
        self.assertIn(CANARIO, self.kb.ler()["html"])
        self.assertNotIn(CANARIO, resposta.mensagem + self.arquivo().read_text(encoding="utf-8"))

    def test_pagina_aberta_recusa_avisa_e_nao_grava(self):
        self.kb.mudar(permissoes=permissoes(papeis=(("platform-team", True), ("Viewer", True))))
        resposta = self.hook()
        self.assertIn("Viewer", resposta.mensagem)
        self.assertIn("aviso", resposta.mensagem)
        self.assertFalse(self.arquivo().exists())
        self.assertEqual(self.kb.ler()["revision_count"], 1)
        self.assertNotIn("page section-set", " ".join(self.kb.comandos()))

    def test_segundo_host_com_estado_vazio_fica_calado_e_nao_cria_revisao(self):
        self.hook()
        revisoes = self.kb.ler()["revision_count"]
        outro = eds.Contexto(hostname=lambda: MAQUINA, agora=lambda: AGORA, runner=self.runner,
                             pasta_de_estado=Path(self.tmp.name) / "dados-outro-host", ambiente=self.kb.ambiente())
        resposta = eds.executar_hook(json.dumps(fixture("codex-stop.json", self.raiz)), outro)
        self.assertIsNone(resposta.mensagem)
        self.assertEqual(self.kb.ler()["revision_count"], revisoes)
        self.assertTrue(eds.arquivo_de_estado(self.raiz, Path(self.tmp.name) / "dados-outro-host").is_file(),
                        "o estado do outro host passa a refletir a página")

    def test_releitura_divergente_nao_grava_o_estado(self):
        self.kb.mudar(sabotar=True)
        resposta = self.hook()
        self.assertIn("releitura", resposta.mensagem)
        self.assertFalse(self.arquivo().exists())

    def test_estado_salvo_a_cada_operacao_aceita(self):
        (self.raiz / ".env.local").write_text("Y=1\n", encoding="utf-8")
        gravacoes = []
        original = eds.gravar_estado

        def espiao(caminho, estado):
            gravacoes.append(sorted(estado["environments"].get("development", {})))
            original(caminho, estado)
        eds.gravar_estado = espiao
        try:
            self.hook("claude-stop.json")
        finally:
            eds.gravar_estado = original
        self.assertEqual(gravacoes[:2], [[".env"], [".env", ".env.local"]])


class Cli(unittest.TestCase):
    """`sync`, `status` e `migrate` pelo backend kb de verdade (o kb falso como `doc.cli`)."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.config = config_kb()
        self.raiz = criar_repo(base / "repo", {".env": f"DB_PASSWORD={CANARIO}\n", "api/.env.local": "P=1\n"},
                               config=self.config)
        self.kb = KbFalso(base, self.config)
        self.estado = base / "estado.json"

    def tearDown(self):
        self.tmp.cleanup()

    def cli(self, *args, rc=0, extra=None):
        r = subprocess.run([sys.executable, "-B", str(eds.__file__), *map(str, args)], capture_output=True, text=True,
                           env={**os.environ, **self.kb.ambiente(extra)})
        self.assertEqual(r.returncode, rc, r.stdout + r.stderr)
        self.assertNotIn(CANARIO, r.stdout + r.stderr)
        return r

    def test_sync_e_status_pelo_kb(self):
        self.cli("sync", "--root", self.raiz, "--state", self.estado, "--now", QUANDO_ISO, "--commit", "abc1234")
        self.assertIn("ok\tdevelopment\t.env", self.cli("status", "--root", self.raiz).stdout)
        estado = self.kb.ler()
        estado["html"] = estado["html"].replace("P=1", "P=2")
        self.kb.gravar(estado)
        self.assertIn("diverge\tdevelopment\tapi/.env.local", self.cli("status", "--root", self.raiz, rc=3).stdout)

    def test_migrate_dry_run_nao_escreve_e_manda_o_html_pelo_stdin(self):
        r = self.cli("migrate", "--root", self.raiz, "--now", QUANDO_ISO, "--commit", "abc1234", rc=4)
        self.assertIn("dry-run", r.stdout)
        self.assertIn("lost", r.stdout)
        estado = self.kb.ler()
        self.assertEqual(estado["revision_count"], 1)
        (argv,) = [a for a in estado["chamadas"] if a[:2] == ["page", "replace"]]
        self.assertIn("--html=@-", argv)
        self.assertIn("--confirm=4242", argv)
        self.assertNotIn("--apply", argv)
        self.assertFalse(any(CANARIO in parte for a in estado["chamadas"] for parte in a))

    def test_migrate_apply_publica_a_pagina_e_grava_o_estado(self):
        r = self.cli("migrate", "--root", self.raiz, "--state", self.estado, "--now", QUANDO_ISO,
                     "--commit", "abc1234", "--apply")
        self.assertIn("revision_count", r.stdout)
        estado = self.kb.ler()
        self.assertEqual(estado["revision_count"], 2)
        self.assertIn(CANARIO, estado["html"])
        self.assertEqual(estado["changelogs"], ["env-docs-sync: migração ao template @ abc1234"])
        gravado = json.loads(self.estado.read_text(encoding="utf-8"))
        self.assertEqual(set(gravado["environments"]["development"]), {".env", "api/.env.local"})
        self.assertIn("nada a sincronizar", self.cli("sync", "--root", self.raiz, "--state", self.estado,
                                                     "--now", QUANDO_ISO, "--commit", "abc1234").stdout)
        self.assertIn("2 ok", self.cli("status", "--root", self.raiz).stdout)

    def test_migrate_passa_pela_mesma_trava(self):
        self.kb.mudar(permissoes=permissoes(fallback_view=True))
        r = self.cli("migrate", "--root", self.raiz, "--now", QUANDO_ISO, "--commit", "abc1234", "--apply", rc=1)
        self.assertIn("fallback", r.stderr)
        self.assertFalse(any(a[:2] == ["page", "replace"] for a in self.kb.ler()["chamadas"]))

    def test_migrate_com_remoto_que_falha_nao_publica(self):
        cfg = config_kb(config_exemplo())
        cfg["environments"]["development"]["machine"] = MAQUINA
        (self.raiz / ".env-docs.json").write_text(json.dumps(cfg), encoding="utf-8")
        falso = Path(self.tmp.name) / "bin"
        falso.mkdir()
        (falso / "ssh").write_text("#!/bin/sh\nexit 255\n", encoding="utf-8")
        (falso / "ssh").chmod(0o755)
        r = self.cli("migrate", "--root", self.raiz, "--now", QUANDO_ISO, "--commit", "abc1234", "--apply", rc=1,
                     extra={"PATH": f"{falso}:{os.environ['PATH']}", "EXAMPLE_SSH_PASSWORD": "x"})
        self.assertIn("staging", r.stderr)
        self.assertFalse(any(a[:2] == ["page", "replace"] for a in self.kb.ler().get("chamadas", [])))


if __name__ == "__main__":
    unittest.main()
