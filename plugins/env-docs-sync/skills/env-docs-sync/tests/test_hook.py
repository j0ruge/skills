"""Entrada do hook: payloads reais dos dois hosts, filtro do Checkout da verdade, Varredura, estado e canário.

Os payloads em `fixtures/` foram capturados no Claude Code 2.1.309 e no codex-cli 0.164.0 (2026-10-27)
e anonimizados; o teste troca a raiz anonimizada pela raiz de um repo git real criado no setUp.
"""
import io
import json
import os
import socket
import stat
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from support import (CANARIO, MAQUINA, PLUGIN, comando_do_hook, config_so_development, criar_repo, eds,
                     fixture, git)

AGORA = datetime(2026, 10, 27, 15, 0, tzinfo=timezone(timedelta(hours=-3)))


class DestinoEspiao(eds.DestinoDiretorio):
    """DestinoDiretorio que registra as chamadas e pode falhar na n-ésima escrita."""

    def __init__(self, pasta, falhar_em=None):
        super().__init__(pasta)
        self.escritas, self.falhar_em = [], falhar_em

    def escrever(self, op):
        if self.falhar_em is not None and len(self.escritas) == self.falhar_em:
            raise eds.ErroEnvDocs(f"destino recusou {op.caminho}")
        super().escrever(op)
        self.escritas.append((op.ambiente, op.acao, op.caminho))


class BaseHook(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.dados, self.pasta_destino = base / "dados", base / "destino"
        self.raiz = criar_repo(base / "repo", {".env": f"DB_PASSWORD={CANARIO}_a\nAPI_URL=http://localhost\n"},
                               config=config_so_development())
        self.fabricas = 0
        self.destino = DestinoEspiao(self.pasta_destino)
        self.saidas = []

    def tearDown(self):
        self.tmp.cleanup()

    def fabrica(self, config, raiz, ctx):
        self.fabricas += 1
        return self.destino

    def contexto(self, **troca):
        opcoes = dict(hostname=lambda: MAQUINA, agora=lambda: AGORA, fabrica_destino=self.fabrica,
                      pasta_de_estado=self.dados, ambiente={})
        opcoes.update(troca)
        return eds.Contexto(**opcoes)

    def hook(self, payload, **troca):
        texto = payload if isinstance(payload, str) else json.dumps(payload)
        resposta = eds.executar_hook(texto, self.contexto(**troca))
        self.saidas.append(eds.saida_do_hook(resposta) + "\n".join(resposta.log))
        return resposta

    def arquivo_de_estado(self, raiz=None):
        return eds.arquivo_de_estado(raiz or self.raiz, self.dados)

    def estado(self, raiz=None):
        return eds.carregar_estado(self.arquivo_de_estado(raiz))


class Gatilho(unittest.TestCase):
    """O que o hook extrai do payload: só caminho e comando, nunca o conteúdo."""

    def test_claude_edit_e_write_dao_o_file_path(self):
        for nome, rel in (("claude-posttooluse-edit-env.json", ".env"),
                          ("claude-posttooluse-write-env.json", ".env.local")):
            with self.subTest(nome):
                g = eds.ler_gatilho(fixture(nome, "/r"))
                self.assertEqual((g.evento, g.caminhos, g.comando), ("PostToolUse", (Path("/r") / rel,), None))

    def test_codex_apply_patch_da_os_caminhos_do_patch(self):
        for nome, rel in (("codex-posttooluse-apply_patch-update-env.json", ".env"),
                          ("codex-posttooluse-apply_patch-add-env.json", ".env.codex")):
            with self.subTest(nome):
                g = eds.ler_gatilho(fixture(nome, "/r"))
                self.assertEqual(g.caminhos, (Path("/r") / rel,))

    def test_patch_com_move_delete_e_caminho_relativo(self):
        patch = ("*** Begin Patch\n*** Update File: a/.env\n*** Move to: b/.env\n@@\n-X=1\n+X=2\n"
                 "*** Delete File: /abs/.env.old\n*** Add File: c d/.env\n+Y=1\n*** End Patch")
        self.assertEqual(eds.caminhos_do_patch(patch, Path("/r")),
                         [Path("/r/a/.env"), Path("/r/b/.env"), Path("/abs/.env.old"), Path("/r/c d/.env")])

    def test_bash_traz_o_comando_e_nenhum_caminho(self):
        for nome in ("claude-posttooluse-bash-ssh.json", "codex-posttooluse-bash-ssh.json"):
            with self.subTest(nome):
                g = eds.ler_gatilho(fixture(nome, "/r"))
                self.assertIsNone(g.caminhos)
                self.assertIn("staging.internal.example", g.comando)

    def test_stop_e_sessionstart_dos_dois_hosts(self):
        for nome, evento in (("claude-stop.json", "Stop"), ("codex-stop.json", "Stop"),
                             ("claude-sessionstart.json", "SessionStart"),
                             ("codex-sessionstart.json", "SessionStart")):
            with self.subTest(nome):
                g = eds.ler_gatilho(fixture(nome, "/r"))
                self.assertEqual((g.evento, g.caminhos, g.comando, g.cwd), (evento, None, None, Path("/r")))

    def test_stop_com_stop_hook_active_nao_e_gatilho(self):
        self.assertIsNone(eds.ler_gatilho(fixture("claude-stop-active.json", "/r")))
        self.assertIsNone(eds.ler_gatilho(fixture("codex-stop.json", "/r", stop_hook_active=True)))

    def test_payload_estranho_nao_e_gatilho(self):
        casos = [[], "x", {}, {"hook_event_name": "PostToolUse"},
                 fixture("claude-stop.json", "/r", cwd="relativo"),
                 fixture("claude-stop.json", "/r", hook_event_name="SessionEnd"),
                 fixture("claude-posttooluse-edit-env.json", "/r", tool_name="NotebookEdit"),
                 fixture("claude-posttooluse-edit-env.json", "/r", tool_input={"file_path": 3}),
                 fixture("codex-posttooluse-apply_patch-add-env.json", "/r", tool_input={"command": "sem marcador"})]
        for caso in casos:
            with self.subTest(caso=str(caso)[:60]):
                self.assertIsNone(eds.ler_gatilho(caso))


class Hook(BaseHook):
    def test_positivo_claude_edit_sincroniza_e_grava_estado_0600(self):
        resposta = self.hook(fixture("claude-posttooluse-edit-env.json", self.raiz))
        self.assertEqual(self.destino.escritas, [("development", "criar", ".env")])
        self.assertIn(".env", resposta.mensagem)
        self.assertIn("atualizada", resposta.mensagem)
        arquivo = self.arquivo_de_estado()
        self.assertEqual(stat.S_IMODE(arquivo.stat().st_mode), 0o600)
        sha = eds.hash_sha256((self.raiz / ".env").read_bytes())
        self.assertEqual(self.estado()["environments"]["development"][".env"]["sha256"], sha)

    def test_positivo_cada_host_e_cada_ferramenta(self):
        casos = [("claude-posttooluse-edit-env.json", ".env"), ("claude-posttooluse-write-env.json", ".env.local"),
                 ("codex-posttooluse-apply_patch-update-env.json", ".env"),
                 ("codex-posttooluse-apply_patch-add-env.json", ".env.codex")]
        for nome, rel in casos:
            with self.subTest(nome), tempfile.TemporaryDirectory() as tmp:
                raiz = criar_repo(Path(tmp) / "repo", {rel: f"X={CANARIO}\n"}, config=config_so_development())
                destino = DestinoEspiao(Path(tmp) / "destino")
                resposta = self.hook(fixture(nome, raiz), fabrica_destino=lambda c, r, x: destino,
                                     pasta_de_estado=Path(tmp) / "dados")
                self.assertEqual(destino.escritas, [("development", "criar", rel)])
                self.assertIn(rel, resposta.mensagem)

    def test_negativo_edicao_de_arquivo_que_nao_e_env_fica_calada(self):
        for nome in ("claude-posttooluse-edit-outro.json", "codex-posttooluse-apply_patch-outro.json"):
            with self.subTest(nome):
                resposta = self.hook(fixture(nome, self.raiz))
                self.assertIsNone(resposta.mensagem)
                self.assertEqual(self.fabricas, 0, "o destino nem é montado")
                self.assertFalse(self.arquivo_de_estado().exists())

    def test_bash_refaz_a_varredura_sem_interpretar_o_comando(self):
        self.hook(fixture("claude-sessionstart.json", self.raiz))
        (self.raiz / ".env").write_text("DB_PASSWORD=outro\n", encoding="utf-8")  # o `echo >>` do Bash
        resposta = self.hook(fixture("codex-posttooluse-bash-ssh.json", self.raiz,
                                     tool_input={"command": "true"}))
        self.assertEqual(self.destino.escritas[-1], ("development", "trocar", ".env"))
        self.assertIn(".env", resposta.mensagem)

    def test_stop_e_sessionstart_pegam_a_edicao_a_mao(self):
        for nome in ("claude-sessionstart.json", "codex-stop.json"):
            with self.subTest(nome):
                antes = len(self.destino.escritas)
                (self.raiz / ".env").write_text(f"DB_PASSWORD={CANARIO}_{nome}\n", encoding="utf-8")
                self.hook(fixture(nome, self.raiz))
                self.assertEqual(len(self.destino.escritas), antes + 1)

    def test_stop_hook_active_fica_calado_mesmo_com_mudanca(self):
        resposta = self.hook(fixture("claude-stop-active.json", self.raiz))
        self.assertIsNone(resposta.mensagem)
        self.assertEqual(self.fabricas, 0)

    def test_sem_mudanca_o_destino_nao_e_chamado(self):
        self.hook(fixture("claude-posttooluse-edit-env.json", self.raiz))
        self.assertEqual(self.fabricas, 1)
        for nome in ("claude-posttooluse-edit-env.json", "claude-stop.json", "codex-sessionstart.json"):
            resposta = self.hook(fixture(nome, self.raiz))
            self.assertIsNone(resposta.mensagem)
        self.assertEqual(self.fabricas, 1, "sem mudança de hash, o destino nem é montado")

    def test_arquivo_apagado_vira_ausente_e_o_bloco_fica(self):
        self.hook(fixture("claude-sessionstart.json", self.raiz))
        (self.raiz / ".env").unlink()
        resposta = self.hook(fixture("claude-stop.json", self.raiz))
        self.assertEqual(self.destino.escritas[-1], ("development", "marcar_ausente", ".env"))
        self.assertIn("ausente", resposta.mensagem)
        self.assertIn(CANARIO, self.destino.ler_corpo("development", ".env"))

    def test_config_ausente_fica_calado_e_destino_nao_e_chamado(self):
        (self.raiz / ".env-docs.json").unlink()
        for nome in ("claude-posttooluse-edit-env.json", "claude-stop.json", "codex-sessionstart.json"):
            self.assertIsNone(self.hook(fixture(nome, self.raiz)).mensagem)
        self.assertEqual(self.fabricas, 0)
        self.assertFalse(self.dados.exists(), "nem a pasta de estado nasce")

    def test_fora_de_repositorio_git_fica_calado(self):
        fora = Path(self.tmp.name) / "solto"
        fora.mkdir()
        (fora / ".env").write_text("X=1\n", encoding="utf-8")
        self.assertIsNone(self.hook(fixture("claude-stop.json", fora)).mensagem)
        self.assertEqual(self.fabricas, 0)

    def test_worktree_fica_calado(self):
        wt = Path(self.tmp.name) / "wt"
        git(self.raiz, "add", ".env-docs.json")
        git(self.raiz, "-c", "user.name=t", "-c", "user.email=t@example.invalid", "commit", "-q", "-m", "cfg")
        git(self.raiz, "worktree", "add", "-q", wt)
        (wt / ".env").write_text("DB_PASSWORD=do-worktree\n", encoding="utf-8")
        self.assertTrue((wt / ".env-docs.json").is_file(), "a config versionada chega ao worktree")
        for nome in ("claude-posttooluse-edit-env.json", "claude-stop.json", "codex-sessionstart.json"):
            self.assertIsNone(self.hook(fixture(nome, wt)).mensagem)
        self.assertEqual(self.fabricas, 0)
        # Controle: o checkout principal, com o mesmo payload, age.
        self.assertIsNotNone(self.hook(fixture("claude-stop.json", self.raiz)).mensagem)

    def test_subpasta_do_checkout_principal_nao_parece_worktree(self):
        sub = self.raiz / "packages" / "api"
        sub.mkdir(parents=True)
        self.assertTrue(eds.checkout_da_verdade(sub))
        resposta = self.hook(fixture("claude-stop.json", sub))
        self.assertIn(".env", resposta.mensagem)

    def test_outra_maquina_fica_calada(self):
        resposta = self.hook(fixture("claude-posttooluse-edit-env.json", self.raiz), hostname=lambda: "outra-maquina")
        self.assertIsNone(resposta.mensagem)
        self.assertEqual(self.fabricas, 0)

    def test_maquina_compara_sem_caixa_e_aceita_nome_curto(self):
        self.assertTrue(eds.maquina_confere("Estacao-Teste", "estacao-teste"))
        self.assertTrue(eds.maquina_confere("estacao-teste", "estacao-teste.lan.example"))
        self.assertFalse(eds.maquina_confere("estacao", "estacao-teste"))
        self.assertFalse(eds.maquina_confere("estacao-teste.lan", "estacao-teste.wan"))

    def test_edicao_em_outro_repo_usa_a_raiz_do_arquivo(self):
        outro = criar_repo(Path(self.tmp.name) / "outro", {})
        payload = fixture("claude-posttooluse-edit-env.json", self.raiz, cwd=str(outro))
        resposta = self.hook(payload)
        self.assertEqual(self.destino.escritas, [("development", "criar", ".env")])
        self.assertIn(".env", resposta.mensagem)

    def test_falha_do_destino_mantem_o_estado_intacto(self):
        self.hook(fixture("claude-sessionstart.json", self.raiz))
        antes = self.arquivo_de_estado().read_bytes()
        (self.raiz / ".env").write_text(f"DB_PASSWORD={CANARIO}_b\n", encoding="utf-8")
        self.destino.falhar_em = len(self.destino.escritas)
        resposta = self.hook(fixture("claude-stop.json", self.raiz))
        self.assertIn("aviso", resposta.mensagem)
        self.assertIn(".env", resposta.mensagem)
        self.assertEqual(self.arquivo_de_estado().read_bytes(), antes)

    def test_falha_no_meio_grava_so_o_que_o_destino_aceitou(self):
        (self.raiz / ".env.local").write_text("Y=1\n", encoding="utf-8")
        self.destino.falhar_em = 1
        resposta = self.hook(fixture("claude-stop.json", self.raiz))
        self.assertEqual(self.destino.escritas, [("development", "criar", ".env")])
        self.assertEqual(set(self.estado()["environments"]["development"]), {".env"})
        self.assertIn(".env.local", resposta.mensagem)
        # O próximo gatilho tenta o resto.
        self.destino.falhar_em = None
        self.hook(fixture("claude-stop.json", self.raiz))
        self.assertEqual(self.destino.escritas[-1], ("development", "criar", ".env.local"))

    def test_fabrica_que_falha_avisa_e_nao_grava(self):
        def quebrada(config, raiz, ctx):
            raise eds.ErroEnvDocs("adaptador kb ainda não implementado")
        resposta = self.hook(fixture("claude-stop.json", self.raiz), fabrica_destino=quebrada)
        self.assertIn("adaptador kb ainda não implementado", resposta.mensagem)
        self.assertIn(".env", resposta.mensagem)
        self.assertFalse(self.arquivo_de_estado().exists())

    def test_excecao_inesperada_sai_so_com_o_tipo(self):
        class Bomba(DestinoEspiao):
            def escrever(self, op):
                raise RuntimeError(f"vazou {op.corpo}")
        resposta = self.hook(fixture("claude-stop.json", self.raiz),
                             fabrica_destino=lambda c, r, x: Bomba(self.pasta_destino))
        self.assertIn("RuntimeError", resposta.mensagem)
        self.assertNotIn(CANARIO, resposta.mensagem)

    def test_config_invalida_avisa_sem_agir(self):
        (self.raiz / ".env-docs.json").write_text('{"doc": {}}', encoding="utf-8")
        resposta = self.hook(fixture("claude-stop.json", self.raiz))
        self.assertIn("config", resposta.mensagem)
        self.assertEqual(self.fabricas, 0)

    def test_estado_corrompido_avisa_sem_agir(self):
        arquivo = self.arquivo_de_estado()
        arquivo.parent.mkdir(parents=True)
        arquivo.write_text('{"version": 1, "environments": {}, "remote_checked_at": {}, "valor": "x"}', encoding="utf-8")
        resposta = self.hook(fixture("claude-stop.json", self.raiz))
        self.assertIn("estado", resposta.mensagem)
        self.assertEqual(self.fabricas, 0)

    def test_lock_ocupado_avisa_e_nao_escreve(self):
        trava = eds.trava_do_repo(self.raiz, self.dados)
        with trava:
            resposta = self.hook(fixture("claude-stop.json", self.raiz), espera_da_trava=0.2)
        self.assertIn("outro sync", resposta.mensagem)
        self.assertEqual(self.destino.escritas, [])
        self.assertFalse(self.arquivo_de_estado().exists())

    def test_estado_por_repo_com_chave_pelo_caminho(self):
        outro = criar_repo(Path(self.tmp.name) / "outro", {".env": "Z=1\n"}, config=config_so_development())
        self.hook(fixture("claude-stop.json", self.raiz))
        self.hook(fixture("claude-stop.json", outro))
        a, b = self.arquivo_de_estado(), self.arquivo_de_estado(outro)
        self.assertNotEqual(a, b)
        self.assertEqual(a.parent, b.parent)
        self.assertEqual(a.name, eds.hash_sha256(str(self.raiz.resolve()).encode()) + ".json")

    def test_canario_fora_de_mensagem_log_e_estado(self):
        envenenado = fixture("claude-posttooluse-edit-env.json", self.raiz)
        envenenado["tool_input"]["new_string"] = f"{CANARIO}_payload"
        envenenado["tool_response"]["originalFile"] = f"{CANARIO}_payload"
        self.hook(envenenado)
        (self.raiz / ".env").write_text(f"DB_PASSWORD={CANARIO}_c\n", encoding="utf-8")
        self.destino.falhar_em = len(self.destino.escritas)
        self.hook(fixture("claude-stop.json", self.raiz))
        self.destino.falhar_em = None
        self.hook(fixture("claude-stop.json", self.raiz))
        (self.raiz / ".env").unlink()
        self.hook(fixture("codex-sessionstart.json", self.raiz))
        for saida in self.saidas:
            self.assertNotIn(CANARIO, saida)
        self.assertNotIn(CANARIO, self.arquivo_de_estado().read_text(encoding="utf-8"))
        # Controle positivo: o canário chegou ao destino, então o teste enxergaria um vazamento.
        self.assertIn(f"{CANARIO}_c", self.destino.ler_corpo("development", ".env"))


class PastaDeEstado(unittest.TestCase):
    def test_ordem_de_resolucao(self):
        self.assertEqual(eds.pasta_de_estado({"CLAUDE_PLUGIN_DATA": "/c", "PLUGIN_DATA": "/p", "HOME": "/h"}), Path("/c"))
        self.assertEqual(eds.pasta_de_estado({"PLUGIN_DATA": "/p", "HOME": "/h"}), Path("/p"))
        self.assertEqual(eds.pasta_de_estado({"XDG_STATE_HOME": "/x", "HOME": "/h"}), Path("/x/env-docs-sync"))
        self.assertEqual(eds.pasta_de_estado({"HOME": "/h"}), Path("/h/.local/state/env-docs-sync"))

    def test_valor_vazio_ou_relativo_nao_conta(self):
        self.assertEqual(eds.pasta_de_estado({"CLAUDE_PLUGIN_DATA": "", "PLUGIN_DATA": "rel", "HOME": "/h"}),
                         Path("/h/.local/state/env-docs-sync"))


class ComandoReal(unittest.TestCase):
    """A string inteira do `command` do hooks.json, por `sh -c`, como os dois hosts rodam."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.dados = base / "dados"
        self.raiz = criar_repo(base / "repo", {".env": f"DB_PASSWORD={CANARIO}\n"},
                               config=config_so_development(socket.gethostname()))
        (self.comando,) = comando_do_hook()

    def tearDown(self):
        self.tmp.cleanup()

    def rodar(self, entrada, raiz_do_plugin=PLUGIN, dados=None):
        env = {"PATH": os.environ["PATH"], "HOME": self.tmp.name, "CLAUDE_PLUGIN_ROOT": str(raiz_do_plugin),
               "CLAUDE_PLUGIN_DATA": str(dados or self.dados)}
        texto = entrada if isinstance(entrada, str) else json.dumps(entrada)
        return subprocess.run(["sh", "-c", self.comando], input=texto, capture_output=True, text=True, env=env,
                              timeout=60)

    def test_todos_os_handlers_usam_o_mesmo_comando_com_guarda_de_script_ausente(self):
        self.assertIn('[ -f "$f" ]', self.comando)
        self.assertIn('"${CLAUDE_PLUGIN_ROOT}/skills/env-docs-sync/scripts/env_docs_sync.py"', self.comando)

    def test_script_ausente_sai_0(self):
        r = self.rodar(fixture("claude-stop.json", self.raiz), raiz_do_plugin=Path(self.tmp.name) / "nao-existe")
        self.assertEqual((r.returncode, r.stdout), (0, ""))
        self.assertIn("script ausente", r.stderr)

    def test_stdin_invalido_sai_0_sem_stdout(self):
        for entrada in ("", "não é json", "[1, 2]", "{}", '{"hook_event_name": "Stop"}'):
            with self.subTest(entrada=entrada):
                r = self.rodar(entrada)
                self.assertEqual((r.returncode, r.stdout), (0, ""))

    def test_positivo_pelo_comando_real_avisa_e_nao_grava(self):
        """Sem fábrica injetada vale o `doc.backend` da config; o destino não confirma, o estado não nasce."""
        r = self.rodar(fixture("claude-posttooluse-edit-env.json", self.raiz))
        self.assertEqual(r.returncode, 0, r.stderr)
        mensagem = json.loads(r.stdout)["systemMessage"]
        self.assertIn("aviso", mensagem)
        self.assertIn(".env", mensagem)
        self.assertFalse(eds.arquivo_de_estado(self.raiz, self.dados).exists())
        self.assertNotIn(CANARIO, r.stdout + r.stderr)

    def test_stop_hook_active_pelo_comando_real(self):
        r = self.rodar(fixture("claude-stop-active.json", self.raiz))
        self.assertEqual((r.returncode, r.stdout), (0, ""))

    def test_negativo_e_config_ausente_pelo_comando_real(self):
        r = self.rodar(fixture("codex-posttooluse-apply_patch-outro.json", self.raiz))
        self.assertEqual((r.returncode, r.stdout), (0, ""))
        (self.raiz / ".env-docs.json").unlink()
        r = self.rodar(fixture("claude-stop.json", self.raiz))
        self.assertEqual((r.returncode, r.stdout, r.stderr), (0, "", ""))


class HooksJson(unittest.TestCase):
    def test_forma_shell_eventos_e_timeout_inteiro(self):
        dados = json.loads((PLUGIN / "hooks" / "hooks.json").read_text(encoding="utf-8"))
        self.assertEqual(set(dados), {"description", "hooks"})
        self.assertEqual(set(dados["hooks"]), {"PostToolUse", "Stop", "SessionStart"})
        self.assertEqual([g.get("matcher") for g in dados["hooks"]["PostToolUse"]], ["Write|Edit", "Bash"])
        for grupos in dados["hooks"].values():
            for g in grupos:
                for h in g["hooks"]:
                    self.assertEqual(h["type"], "command")
                    self.assertNotIn("args", h)
                    self.assertNotIn("async", h)
                    self.assertIsInstance(h["timeout"], int)
        manifesto = json.loads((PLUGIN / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
        self.assertNotIn("hooks", manifesto)


if __name__ == "__main__":
    unittest.main()
