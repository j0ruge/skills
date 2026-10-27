"""Seções derivadas: o que na página não é Bloco de arquivo (intro, tabela de Ambientes, CI/CD e Como
rodar). Saem da config, dos workflows e dos nomes do gh, e o sync as refaz quando uma dessas entradas
muda, sem tocar nas Seções de ambiente."""
import copy
import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from support import (CANARIO, MAQUINA, QUANDO, QUANDO_ISO, config_exemplo, config_so_development, criar_arvore,
                     criar_repo, eds, fixture)
from test_ci import RESPOSTAS_GH, GhFalso
from test_hook import AGORA, DestinoEspiao
from test_kb import KbFalso, config_kb, permissoes

CI_A = "<h3>Workflows</h3>\n<p>versão A</p>"
CI_B = "<h3>Workflows</h3>\n<p>versão B</p>"


def bloco(texto):
    return eds.bloco_de_arquivo(texto, sincronizado_em=QUANDO, commit="abc1234")


def com_ids(pagina):
    """O que o BookStack faz ao guardar: id em cada bloco e entidades onde o html tinha caractere."""
    n = iter(range(1, 1000))
    for tag in ("<h2>", "<h3>", "<p>", "<table>", "<pre>"):
        while tag in pagina:
            pagina = pagina.replace(tag, f'{tag[:-1]} id="bkmrk-{next(n)}">', 1)
    return pagina.replace("—", "&mdash;")


class PartesDaPagina(unittest.TestCase):
    def setUp(self):
        self.cfg = config_exemplo()
        self.blocos = {"development": {".env": bloco("A=1\n")}, "staging": {"infra/staging/.env": bloco("S=1\n")}}
        self.pagina = eds.pagina_de_ambientes(self.cfg, self.blocos, ci_cd=CI_A)

    def test_parte_antes_das_secoes_de_ambiente_e_a_partir_da_ci_cd(self):
        prefixo, secoes, sufixo = eds.partes_da_pagina(self.pagina)
        self.assertEqual(prefixo + secoes + sufixo, self.pagina)
        self.assertTrue(secoes.startswith("<h2>[development]</h2>"))
        self.assertIn("<h3>infra/staging/.env</h3>", secoes)
        self.assertTrue(sufixo.startswith("<h2>CI/CD</h2>"))
        self.assertIn("<h2>Ambientes</h2>", prefixo)
        self.assertNotIn("[development]", prefixo)

    def test_headings_com_id_do_bookstack(self):
        prefixo, secoes, sufixo = eds.partes_da_pagina(com_ids(self.pagina))
        self.assertTrue(secoes.startswith('<h2 id="bkmrk-'))
        self.assertTrue(sufixo.startswith('<h2 id="bkmrk-'))
        self.assertIn(">CI/CD</h2>", sufixo.split("\n", 1)[0])

    def test_sem_secoes_de_ambiente(self):
        cfg = config_so_development()
        cfg["environments"] = {"development": cfg["environments"]["development"]}
        pagina = eds.pagina_de_ambientes(cfg, {}, ci_cd=CI_A).replace("<h2>[development]</h2>\n", "")
        _, secoes, sufixo = eds.partes_da_pagina(pagina)
        self.assertEqual(secoes, "")
        self.assertTrue(sufixo.startswith("<h2>CI/CD</h2>"))

    def test_pagina_fora_do_template_e_erro(self):
        for quebrada in (self.pagina.replace("<h2>CI/CD</h2>", "<h2>Integração</h2>"),
                         self.pagina.replace("<h2>Ambientes</h2>", ""),
                         self.pagina + "<h2>CI/CD</h2>"):
            with self.subTest(quebrada[-40:]), self.assertRaises(eds.ErroEnvDocs):
                eds.partes_da_pagina(quebrada)

    def test_pagina_com_as_secoes_dadas(self):
        _, secoes, _ = eds.partes_da_pagina(com_ids(self.pagina))
        nova = eds.pagina_de_ambientes(self.cfg, {}, ci_cd=CI_B, secoes=secoes)
        self.assertEqual(eds.partes_da_pagina(nova)[1], secoes)
        self.assertIn("versão B", nova)


class DerivadasConferem(unittest.TestCase):
    def setUp(self):
        self.cfg = config_exemplo()
        self.blocos = {"development": {".env": bloco("A=1\n")}}

    def pagina(self, cfg=None, blocos=None, ci_cd=CI_A):
        return eds.pagina_de_ambientes(cfg or self.cfg, self.blocos if blocos is None else blocos, ci_cd=ci_cd)

    def test_ids_entidades_e_espaco_entre_tags_nao_contam(self):
        self.assertTrue(eds.derivadas_conferem(com_ids(self.pagina()).replace(">\n<", ">\n\n<"), self.pagina()))

    def test_secoes_de_ambiente_nao_contam(self):
        self.assertTrue(eds.derivadas_conferem(self.pagina(), self.pagina(blocos={})))

    def test_ci_cd_tabela_e_como_rodar_contam(self):
        outra = copy.deepcopy(self.cfg)
        outra["environments"]["staging"]["domain"] = "outro.example.com"
        mais_um = copy.deepcopy(self.cfg)
        mais_um["run"].append({"label": "lint", "command": "npm run lint"})
        papeis = copy.deepcopy(self.cfg)
        papeis["doc"]["allowed_roles"] = ["Admin"]
        for nova in (self.pagina(ci_cd=CI_B), self.pagina(cfg=outra), self.pagina(cfg=mais_um), self.pagina(cfg=papeis)):
            with self.subTest():
                self.assertFalse(eds.derivadas_conferem(self.pagina(), nova))

    def test_pagina_fora_do_template_nao_confere(self):
        self.assertFalse(eds.derivadas_conferem("<p>outra coisa</p>", self.pagina()))


class Entradas(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.raiz = Path(self.tmp.name)
        criar_arvore(self.raiz, {".env": "A=1\n", ".github/workflows/cd.yml": "name: cd\n"})
        self.cfg = config_exemplo()

    def tearDown(self):
        self.tmp.cleanup()

    def entradas(self, cfg=None):
        return eds.entradas_derivadas(self.raiz, cfg or self.cfg)

    def test_mesmas_entradas_mesmo_hash(self):
        self.assertRegex(self.entradas(), r"^[0-9a-f]{64}$")
        self.assertEqual(self.entradas(), self.entradas())

    def test_workflow_mudado_novo_ou_apagado_muda_o_hash(self):
        antes = self.entradas()
        (self.raiz / ".github/workflows/cd.yml").write_text("name: cd2\n", encoding="utf-8")
        mudado = self.entradas()
        (self.raiz / ".github/workflows/ci.yaml").write_text("name: ci\n", encoding="utf-8")
        novo = self.entradas()
        (self.raiz / ".github/workflows/cd.yml").unlink()
        self.assertEqual(len({antes, mudado, novo, self.entradas()}), 4)

    def test_config_muda_o_hash_e_env_nao(self):
        antes = self.entradas()
        (self.raiz / ".env").write_text("A=2\n", encoding="utf-8")
        self.assertEqual(self.entradas(), antes)
        outra = copy.deepcopy(self.cfg)
        outra["run"] = []
        self.assertNotEqual(self.entradas(outra), antes)

    def test_sem_ci_nao_le_workflows(self):
        cfg = copy.deepcopy(self.cfg)
        cfg["ci"] = None
        antes = self.entradas(cfg)
        (self.raiz / ".github/workflows/cd.yml").write_text("name: outro\n", encoding="utf-8")
        self.assertEqual(self.entradas(cfg), antes)


class Devidas(unittest.TestCase):
    def setUp(self):
        self.cfg = config_exemplo()
        self.estado = eds.estado_vazio()
        self.estado["derived"] = {"inputs_sha256": "a" * 64, "sha256": "b" * 64, "checked_at": "2026-10-27T10:00:00-03:00"}

    def devidas(self, entradas="a" * 64, janela=False, agora=AGORA, cfg=None):
        return eds.derivadas_devidas(cfg or self.cfg, self.estado, entradas, agora, olhar_janela=janela)

    def test_estado_sem_derivadas(self):
        self.assertTrue(eds.derivadas_devidas(self.cfg, eds.estado_vazio(), "a" * 64, AGORA, olhar_janela=False))

    def test_entradas_mudaram(self):
        self.assertTrue(self.devidas(entradas="c" * 64))

    def test_mesmas_entradas_fora_da_janela(self):
        self.assertFalse(self.devidas())

    def test_janela_vencida_com_gh(self):
        self.assertTrue(self.devidas(janela=True, agora=AGORA + timedelta(days=1)))

    def test_janela_em_dia(self):
        self.assertFalse(self.devidas(janela=True, agora=datetime(2026, 10, 27, 11, 0, tzinfo=timezone(timedelta(hours=-3)))))

    def test_janela_vencida_sem_gh(self):
        cfg = copy.deepcopy(self.cfg)
        cfg["ci"]["secrets"] = None
        self.assertFalse(self.devidas(janela=True, agora=AGORA + timedelta(days=1), cfg=cfg))


class EstadoDasDerivadas(unittest.TestCase):
    def test_estado_aceita_so_hashes_e_carimbo(self):
        estado = eds.estado_vazio()
        estado["derived"] = {"inputs_sha256": "a" * 64, "sha256": "b" * 64, "checked_at": QUANDO_ISO}
        eds.validar_estado(estado)
        for ruim in ({**estado["derived"], "ci_cd": "<p>x</p>"}, {**estado["derived"], "sha256": "curto"},
                     {**estado["derived"], "checked_at": "ontem"}, {"sha256": "b" * 64}):
            with self.subTest(ruim=list(ruim)), self.assertRaises(eds.ErroDeEstado):
                eds.validar_estado({**estado, "derived": ruim})


class DestinoComDerivadas(DestinoEspiao):
    def __init__(self, pasta, falhar=False):
        super().__init__(pasta)
        self.derivadas, self.falhar = [], falhar

    def escrever_derivadas(self, config, ci_cd):
        if self.falhar:
            raise eds.ErroEnvDocs("destino recusou as seções derivadas")
        escreveu = super().escrever_derivadas(config, ci_cd)
        self.derivadas.append(escreveu)
        return escreveu


class HookComDerivadas(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.dados = base / "dados"
        self.raiz = criar_repo(base / "repo", {".env": f"P={CANARIO}\n",
                                               ".github/workflows/cd.yml": "name: cd\njobs:\n  d:\n    runs-on: x\n"},
                               config=config_so_development())
        self.destino = DestinoComDerivadas(base / "destino")
        self.gh = GhFalso({})

    def tearDown(self):
        self.tmp.cleanup()

    def hook(self, nome, agora=AGORA, **campos):
        ctx = eds.Contexto(hostname=lambda: MAQUINA, agora=lambda: agora, fabrica_destino=lambda c, r, x: self.destino,
                           pasta_de_estado=self.dados, ambiente={}, runner=self.gh)
        resposta = eds.executar_hook(json.dumps(fixture(nome, self.raiz, **campos)), ctx)
        self.assertNotIn(CANARIO, resposta.mensagem or "")
        return resposta

    def estado(self):
        return eds.carregar_estado(eds.arquivo_de_estado(self.raiz, self.dados))

    def gravar_config(self, cfg):
        (self.raiz / ".env-docs.json").write_text(json.dumps(cfg), encoding="utf-8")

    def test_primeiro_gatilho_escreve_as_derivadas_com_os_blocos(self):
        resposta = self.hook("claude-sessionstart.json")
        self.assertEqual(self.destino.derivadas, [True])
        self.assertIn("seções derivadas", resposta.mensagem)
        self.assertIn("<td>d</td><td>x</td>", self.destino.ler_derivadas())
        self.assertEqual(set(self.estado()["derived"]), {"inputs_sha256", "sha256", "checked_at"})

    def test_sem_mudanca_fica_calado(self):
        self.hook("claude-sessionstart.json")
        for nome in ("claude-stop.json", "codex-sessionstart.json"):
            self.assertIsNone(self.hook(nome).mensagem)
        self.assertEqual(self.destino.derivadas, [True])

    def test_workflow_editado_refaz_as_derivadas_pela_edicao(self):
        self.hook("claude-sessionstart.json")
        arquivo = self.raiz / ".github/workflows/cd.yml"
        arquivo.write_text("name: cd\njobs:\n  d:\n    runs-on: [self-hosted, novo]\n", encoding="utf-8")
        resposta = self.hook("claude-posttooluse-edit-env.json",
                             tool_input={"file_path": str(arquivo), "old_string": "x", "new_string": "y"})
        self.assertIn("seções derivadas", resposta.mensagem)
        self.assertIn("self-hosted, novo", self.destino.ler_derivadas())
        self.assertEqual(self.destino.escritas, [("development", "criar", ".env")], "os blocos ficam")

    def test_config_editada_refaz_as_derivadas_no_stop(self):
        self.hook("claude-sessionstart.json")
        cfg = config_so_development()
        cfg["run"].append({"label": "Lint", "command": "npm run lint"})
        self.gravar_config(cfg)
        self.assertIn("seções derivadas", self.hook("claude-stop.json").mensagem)
        self.assertIn("npm run lint", self.destino.ler_derivadas())

    def test_falha_nas_derivadas_avisa_e_nao_grava_o_estado_delas(self):
        self.destino.falhar = True
        resposta = self.hook("claude-sessionstart.json")
        self.assertIn("recusou as seções derivadas", resposta.mensagem)
        self.assertEqual(self.destino.escritas, [("development", "criar", ".env")], "os blocos seguem")
        self.assertNotIn("derived", self.estado())
        self.destino.falhar = False
        self.assertIn("seções derivadas", self.hook("claude-stop.json").mensagem, "o próximo gatilho tenta de novo")

    def test_bloco_que_falha_deixa_as_derivadas_para_depois(self):
        self.destino.falhar_em = 0
        resposta = self.hook("claude-sessionstart.json")
        self.assertEqual(self.destino.derivadas, [])
        self.assertNotIn("seções derivadas (Ambientes", resposta.mensagem)
        self.assertNotIn("derived", self.estado() if eds.arquivo_de_estado(self.raiz, self.dados).exists() else {})

    def test_yml_fora_da_pasta_de_workflows_nao_dispara(self):
        self.hook("claude-sessionstart.json")
        outro = self.raiz / "docs/exemplo.yml"
        outro.parent.mkdir()
        outro.write_text("name: x\n", encoding="utf-8")
        resposta = self.hook("claude-posttooluse-edit-env.json",
                             tool_input={"file_path": str(outro), "old_string": "x", "new_string": "y"})
        self.assertIsNone(resposta.mensagem)

    def test_filtro_da_edicao_conta_config_e_workflows_so_da_pasta_declarada(self):
        cfg = config_so_development()
        casos = {".env-docs.json": True, ".github/workflows/cd.yml": True, ".github/workflows/ci.yaml": True,
                 "docs/exemplo.yml": False, ".github/workflows/sub/x.yml": False, ".github/workflows/notas.md": False,
                 "app.txt": False}
        for rel, esperado in casos.items():
            with self.subTest(rel=rel):
                self.assertIs(eds._algum_vigiado(self.raiz, [self.raiz / rel], cfg), esperado)

    def com_gh(self):
        cfg = config_so_development()
        cfg["ci"]["secrets"], cfg["remote_check_every"] = "gh", "24h"
        self.gravar_config(cfg)
        self.gh = GhFalso(RESPOSTAS_GH)

    def test_gh_so_na_sessionstart_depois_da_janela(self):
        self.com_gh()
        self.hook("claude-sessionstart.json")
        self.assertIn("<code>SSH_KEY</code>", self.destino.ler_derivadas())
        chamadas = len(self.gh.chamadas)
        self.assertIsNone(self.hook("codex-sessionstart.json", agora=AGORA + timedelta(hours=1)).mensagem)
        self.assertIsNone(self.hook("claude-stop.json", agora=AGORA + timedelta(days=2)).mensagem)
        self.assertEqual(len(self.gh.chamadas), chamadas, "dentro da janela, e no Stop, o gh não roda")
        self.gh.respostas["secret list --env staging --json name"] = '[{"name": "NOVO"}]'
        resposta = self.hook("claude-sessionstart.json", agora=AGORA + timedelta(days=2))
        self.assertGreater(len(self.gh.chamadas), chamadas)
        self.assertIn("seções derivadas", resposta.mensagem)
        self.assertIn("<code>NOVO</code>", self.destino.ler_derivadas())

    def test_gh_sem_mudanca_carimba_sem_escrever(self):
        self.com_gh()
        self.hook("claude-sessionstart.json")
        antes = self.estado()["derived"]["checked_at"]
        self.assertIsNone(self.hook("claude-sessionstart.json", agora=AGORA + timedelta(days=2)).mensagem)
        self.assertEqual(self.destino.derivadas, [True])
        self.assertNotEqual(self.estado()["derived"]["checked_at"], antes)

    def test_gh_que_falha_avisa_e_nao_carimba(self):
        self.com_gh()
        self.hook("claude-sessionstart.json")
        antes = self.estado()["derived"]
        self.gh.rc["secret list --json name"] = 4
        resposta = self.hook("claude-sessionstart.json", agora=AGORA + timedelta(days=2))
        self.assertIn("gh secret list", resposta.mensagem)
        self.assertEqual(self.estado()["derived"], antes)


class DestinoKbDerivadas(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.cfg = config_kb()
        self.kb = KbFalso(Path(self.tmp.name), self.cfg)
        self.ctx = eds.Contexto(ambiente=self.kb.ambiente())
        self.destino = eds.DestinoKb(self.cfg, self.ctx, commit="abc1234")
        self.destino.escrever(eds.planejar(eds.estado_vazio(), {"development": {".env": f"P={CANARIO}\n".encode()}},
                                           sincronizado_em=QUANDO, commit="abc1234",
                                           ler_corpo=self.destino.ler_corpo)[0])

    def tearDown(self):
        self.tmp.cleanup()

    def test_pagina_igual_nao_chama_o_replace(self):
        ci_cd = eds.secao_ci_cd(self.cfg["ci"], [], None)
        antes = self.kb.ler()["revision_count"]
        self.assertTrue(eds.DestinoKb(self.cfg, self.ctx).conferir_derivadas(self.cfg, ci_cd))
        self.assertFalse(eds.DestinoKb(self.cfg, self.ctx).escrever_derivadas(self.cfg, ci_cd))
        self.assertEqual(self.kb.ler()["revision_count"], antes)
        self.assertFalse(any(a[:2] == ["page", "replace"] for a in self.kb.ler()["chamadas"]))

    def test_ci_cd_nova_troca_so_as_derivadas(self):
        antes = self.kb.ler()
        destino = eds.DestinoKb(self.cfg, self.ctx)
        self.assertFalse(destino.conferir_derivadas(self.cfg, CI_B))
        self.assertTrue(destino.escrever_derivadas(self.cfg, CI_B))
        depois = self.kb.ler()
        self.assertEqual(depois["revision_count"], antes["revision_count"] + 1)
        self.assertIn("versão B", depois["html"])
        self.assertIn(CANARIO, depois["html"])
        self.assertTrue(eds.bloco_confere(
            eds.Operacao("development", ".env", "trocar", eds.hash_sha256(f"P={CANARIO}\n".encode()), ""),
            eds.corpo_da_secao(depois["html"], "[development]", ".env")))
        (argv,) = [a for a in depois["chamadas"] if a[:2] == ["page", "replace"]]
        self.assertIn("--apply", argv)
        self.assertIn("--confirm=4242", argv)
        self.assertTrue(any(a.startswith("--changelog=env-docs-sync: seções derivadas") for a in argv))
        self.assertFalse(any(CANARIO in parte for a in depois["chamadas"] for parte in a), "valor nunca em argv")
        self.assertTrue(destino.conferir_derivadas(self.cfg, CI_B))

    def test_trava_recusa_antes_do_replace(self):
        self.kb.mudar(permissoes=permissoes(fallback_view=True))
        with self.assertRaises(eds.ErroDePermissao):
            eds.DestinoKb(self.cfg, self.ctx).escrever_derivadas(self.cfg, CI_B)
        self.assertFalse(any(a[:2] == ["page", "replace"] for a in self.kb.ler()["chamadas"]))

    def test_pagina_aberta_e_recusa_mesmo_com_as_derivadas_iguais(self):
        self.kb.mudar(permissoes=permissoes(fallback_view=True))
        with self.assertRaises(eds.ErroDePermissao):
            eds.DestinoKb(self.cfg, self.ctx).escrever_derivadas(self.cfg, eds.secao_ci_cd(self.cfg["ci"], [], None))

    def test_releitura_divergente_e_erro(self):
        self.kb.mudar(sabotar=True)
        with self.assertRaises(eds.ErroEnvDocs) as ctx:
            eds.DestinoKb(self.cfg, self.ctx).escrever_derivadas(self.cfg, CI_B)
        self.assertIn("releitura", str(ctx.exception))

    def test_pagina_fora_do_template_e_erro_sem_replace(self):
        estado = self.kb.ler()
        estado["html"] = "<p>página escrita à mão</p>"
        self.kb.gravar(estado)
        with self.assertRaises(eds.ErroEnvDocs):
            eds.DestinoKb(self.cfg, self.ctx).escrever_derivadas(self.cfg, CI_B)
        self.assertFalse(any(a[:2] == ["page", "replace"] for a in self.kb.ler()["chamadas"]))


class CliComDerivadas(unittest.TestCase):
    """`status`, `sync` e `migrate` pela CLI, com o kb falso."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.config = config_kb()
        self.raiz = criar_repo(base / "repo", {".env": f"P={CANARIO}\n"}, config=self.config)
        self.kb = KbFalso(base, self.config)
        self.estado = base / "estado.json"

    def tearDown(self):
        self.tmp.cleanup()

    def cli(self, *args, rc=0):
        r = subprocess.run([sys.executable, "-B", str(eds.__file__), *map(str, args)], capture_output=True,
                           text=True, env={**os.environ, **self.kb.ambiente()})
        self.assertEqual(r.returncode, rc, r.stdout + r.stderr)
        self.assertNotIn(CANARIO, r.stdout + r.stderr)
        return r

    def test_status_confere_as_derivadas(self):
        self.cli("sync", "--root", self.raiz, "--state", self.estado, "--now", QUANDO_ISO, "--commit", "abc1234")
        saida = self.cli("status", "--root", self.raiz).stdout
        self.assertIn("ok\tpágina\tseções derivadas", saida)
        self.assertIn("2 ok, 0 diverge", saida)
        self.config["run"].append({"label": "Lint", "command": "npm run lint"})
        (self.raiz / ".env-docs.json").write_text(json.dumps(self.config), encoding="utf-8")
        self.assertIn("diverge\tpágina\tseções derivadas", self.cli("status", "--root", self.raiz, rc=3).stdout)

    def test_sync_refaz_as_derivadas_quando_a_config_muda(self):
        self.cli("sync", "--root", self.raiz, "--state", self.estado, "--now", QUANDO_ISO, "--commit", "abc1234")
        self.config["run"].append({"label": "Lint", "command": "npm run lint"})
        (self.raiz / ".env-docs.json").write_text(json.dumps(self.config), encoding="utf-8")
        saida = self.cli("sync", "--root", self.raiz, "--state", self.estado, "--now", QUANDO_ISO,
                         "--commit", "abc1234").stdout
        self.assertIn("aplicado: seções derivadas", saida)
        self.assertIn("npm run lint", self.kb.ler()["html"])
        self.assertIn("nada a sincronizar", self.cli("sync", "--root", self.raiz, "--state", self.estado,
                                                     "--now", QUANDO_ISO, "--commit", "abc1234").stdout)

    def test_migrate_grava_as_derivadas_no_estado(self):
        self.cli("migrate", "--root", self.raiz, "--state", self.estado, "--now", QUANDO_ISO, "--commit", "abc1234",
                 "--apply")
        gravado = json.loads(self.estado.read_text(encoding="utf-8"))
        self.assertEqual(gravado["derived"]["inputs_sha256"], eds.entradas_derivadas(self.raiz, self.config))
        antes = self.kb.ler()["revision_count"]
        self.assertIn("nada a sincronizar", self.cli("sync", "--root", self.raiz, "--state", self.estado,
                                                     "--now", QUANDO_ISO, "--commit", "abc1234").stdout)
        self.assertEqual(self.kb.ler()["revision_count"], antes)


if __name__ == "__main__":
    unittest.main()
