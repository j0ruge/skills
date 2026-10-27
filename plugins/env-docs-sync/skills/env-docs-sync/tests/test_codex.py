"""`install --codex`: o trust do hook gravado no config.toml do Codex, conferido contra o próprio Codex.

A fixture `codex-hooks-list-dourado.json` é um pacote sintético instalado pelo `codex plugin add` no
codex-cli 0.164.0, com o `currentHash` que o `hooks/list` do app-server devolveu para cada hook. O
pacote força os casos que mudam o hash: ordem por bytes, lixo que o Codex ignora, nome não ASCII,
`async`, `statusMessage`, `commandWindows`, matcher no Stop (que o Codex descarta), timeout 0 e
ausente. Os testes da CLI usam o pacote real deste plugin, copiado para um CODEX_HOME de mentira, e
um canário no config.toml que não pode aparecer em nenhuma saída.
"""
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path

from support import CANARIO, FIXTURES, PLUGIN, SCRIPT, criar_arvore, eds

DOURADO = json.loads((FIXTURES / "codex-hooks-list-dourado.json").read_text(encoding="utf-8"))
LIXO = ("__pycache__/m.cpython-312.pyc", "sub/x.pyc", ".venv/lib/y.txt", "pkg.egg-info/PKG-INFO")
ID = "env-docs-sync@chewiesoft-marketplace"
H1, H2, C = "sha256:" + "1" * 64, "sha256:" + "2" * 64, "sha256:" + "c" * 64


def _hooks(eventos):
    return json.dumps({"hooks": eventos})


class Dourado(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.raiz = Path(self.tmp.name) / "pacote"
        criar_arvore(self.raiz, DOURADO["arquivos"])

    def tearDown(self):
        self.tmp.cleanup()

    def test_impressao_do_pacote_igual_a_do_codex(self):
        self.assertEqual(eds.impressao_do_pacote(self.raiz), DOURADO["conteudo"])

    def test_declaracoes_iguais_as_do_codex_e_na_ordem_dele(self):
        self.assertEqual(eds.hooks_do_pacote(self.raiz, DOURADO["plugin_id"]),
                         list(DOURADO["declaracoes"].items()))

    def test_o_lixo_que_o_codex_ignora_nao_muda_a_impressao(self):
        for rel in LIXO:
            (self.raiz / rel).unlink()
        self.assertEqual(eds.impressao_do_pacote(self.raiz), DOURADO["conteudo"])

    def test_um_byte_trocado_muda_a_impressao(self):
        (self.raiz / "a" / "b.txt").write_bytes(b"y")
        self.assertNotEqual(eds.impressao_do_pacote(self.raiz), DOURADO["conteudo"])

    def test_arquivo_vazio_criado_muda_a_impressao(self):
        (self.raiz / "novo.txt").write_bytes(b"")
        self.assertNotEqual(eds.impressao_do_pacote(self.raiz), DOURADO["conteudo"])

    def test_symlink_no_pacote_e_recusado(self):
        # O Codex falha a impressão de um pacote com symlink e pula os hooks do plugin.
        os.symlink(self.raiz / "B.txt", self.raiz / "atalho")
        with self.assertRaisesRegex(eds.ErroEnvDocs, "symlink"):
            eds.impressao_do_pacote(self.raiz)


class FormaDoHook(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.raiz = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_o_hooks_json_deste_plugin_passa_e_da_as_quatro_chaves(self):
        chaves = [chave for chave, _ in eds.hooks_do_pacote(PLUGIN, ID)]
        self.assertEqual(chaves, [f"{ID}:hooks/hooks.json:post_tool_use:0:0",
                                  f"{ID}:hooks/hooks.json:post_tool_use:1:0",
                                  f"{ID}:hooks/hooks.json:session_start:0:0",
                                  f"{ID}:hooks/hooks.json:stop:0:0"])

    def test_forma_que_o_hash_nao_modela_e_recusada(self):
        comando = {"type": "command", "command": "true"}
        casos = {
            "mcp_tool": {"Stop": [{"hooks": [{"type": "mcp_tool", "server": "s", "tool": "t"}]}]},
            "prompt": {"Stop": [{"hooks": [{"type": "prompt"}]}]},
            "additionalContextLimit": {"SessionStart": [{"hooks": [{**comando, "additionalContextLimit": 10}]}]},
            "campo novo no handler": {"Stop": [{"hooks": [{**comando, "novo": 1}]}]},
            "campo novo no grupo": {"Stop": [{"novo": 1, "hooks": [comando]}]},
            "evento só do Claude": {"PostToolUseFailure": [{"hooks": [comando]}]},
            "command vazio": {"Stop": [{"hooks": [{"type": "command", "command": "  "}]}]},
            "timeout não inteiro": {"Stop": [{"hooks": [{**comando, "timeout": 1.5}]}]},
        }
        for nome, eventos in casos.items():
            with self.subTest(nome):
                criar_arvore(self.raiz, {"hooks/hooks.json": _hooks(eventos)})
                with self.assertRaisesRegex(eds.ErroEnvDocs, "forma"):
                    eds.hooks_do_pacote(self.raiz, "p@m")

    def test_hooks_json_ausente_ou_ilegivel_e_recusado(self):
        with self.assertRaisesRegex(eds.ErroEnvDocs, "hooks.json"):
            eds.hooks_do_pacote(self.raiz, "p@m")
        criar_arvore(self.raiz, {"hooks/hooks.json": "{"})
        with self.assertRaisesRegex(eds.ErroEnvDocs, "hooks.json"):
            eds.hooks_do_pacote(self.raiz, "p@m")


def _instalar(codex_home, *, loja="chewiesoft-marketplace", versao="0.1.0", config=True, ligado=True):
    destino = Path(codex_home) / "plugins" / "cache" / loja / "env-docs-sync" / versao
    shutil.copytree(PLUGIN, destino, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    if config:
        arquivo = Path(codex_home) / "config.toml"
        texto = arquivo.read_text(encoding="utf-8") if arquivo.exists() else 'model = "m"\n'
        texto += f'\n[plugins."env-docs-sync@{loja}"]\nenabled = {"true" if ligado else "false"}\n'
        arquivo.write_text(texto, encoding="utf-8")
    return destino


class PluginNoCodex(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name) / "codex-home"
        self.home.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def achar(self):
        config = tomllib.loads((self.home / "config.toml").read_text(encoding="utf-8")) \
            if (self.home / "config.toml").exists() else {}
        return eds.plugin_no_codex(self.home, config, "env-docs-sync")

    def test_acha_o_plugin_instalado(self):
        raiz = _instalar(self.home)
        achado = self.achar()
        self.assertEqual((achado.plugin_id, achado.versao, achado.raiz, achado.ligado), (ID, "0.1.0", raiz, True))

    def test_desligado_no_config(self):
        _instalar(self.home, ligado=False)
        self.assertFalse(self.achar().ligado)

    def test_sem_o_pacote_no_cache_nao_esta_instalado(self):
        (self.home / "config.toml").write_text('model = "m"\n', encoding="utf-8")
        with self.assertRaisesRegex(eds.ErroEnvDocs, "não está instalado"):
            self.achar()

    def test_pacote_no_cache_sem_o_plugin_no_config_nao_esta_instalado(self):
        _instalar(self.home, config=False)
        (self.home / "config.toml").write_text('model = "m"\n', encoding="utf-8")
        with self.assertRaisesRegex(eds.ErroEnvDocs, "não está instalado"):
            self.achar()

    def test_duas_lojas_e_ambiguo(self):
        _instalar(self.home)
        _instalar(self.home, loja="outra-loja")
        with self.assertRaisesRegex(eds.ErroEnvDocs, "mais de uma loja"):
            self.achar()

    def test_duas_versoes_e_ambiguo(self):
        _instalar(self.home)
        _instalar(self.home, versao="0.0.9", config=False)
        with self.assertRaisesRegex(eds.ErroEnvDocs, "mais de uma versão"):
            self.achar()


class EditarTrust(unittest.TestCase):
    D = {"p@m:hooks/hooks.json:post_tool_use:0:0": {"trusted_hash": H1, "trusted_content_hash": C},
         "p@m:hooks/hooks.json:stop:0:0": {"trusted_hash": H2, "trusted_content_hash": C}}

    def estado(self, texto):
        return tomllib.loads(texto)["hooks"]["state"]

    def test_acrescenta_as_tabelas_no_fim_e_preserva_o_resto(self):
        texto = '# config pessoal\nmodel = "m"  # comentário\n\n[plugins."p@m"]\nenabled = true\n'
        novo = eds.editar_trust(texto, self.D)
        self.assertEqual(novo, texto + (
            '\n[hooks.state."p@m:hooks/hooks.json:post_tool_use:0:0"]\n'
            f'trusted_hash = "{H1}"\ntrusted_content_hash = "{C}"\n'
            '\n[hooks.state."p@m:hooks/hooks.json:stop:0:0"]\n'
            f'trusted_hash = "{H2}"\ntrusted_content_hash = "{C}"\n'))
        self.assertEqual(self.estado(novo), self.D)

    def test_texto_sem_newline_no_fim(self):
        novo = eds.editar_trust('model = "m"', self.D)
        self.assertTrue(novo.startswith('model = "m"\n\n[hooks.state."'))
        self.assertEqual(self.estado(novo), self.D)

    def test_troca_no_lugar_mantem_enabled_e_acrescenta_o_campo_que_falta(self):
        texto = ('[hooks.state."p@m:hooks/hooks.json:stop:0:0"]\nenabled = false\n'
                 'trusted_hash = "sha256:velho"\n\n[outra]\nx = 1\n')
        novo = eds.editar_trust(texto, self.D)
        self.assertTrue(novo.startswith(
            '[hooks.state."p@m:hooks/hooks.json:stop:0:0"]\nenabled = false\n'
            f'trusted_hash = "{H2}"\ntrusted_content_hash = "{C}"\n\n[outra]\nx = 1\n'))
        estado = self.estado(novo)
        self.assertEqual(estado["p@m:hooks/hooks.json:stop:0:0"],
                         {"enabled": False, "trusted_hash": H2, "trusted_content_hash": C})
        self.assertEqual(tomllib.loads(novo)["outra"], {"x": 1})

    def test_ja_confiado_devolve_o_mesmo_texto(self):
        texto = eds.editar_trust('model = "m"\n', self.D)
        self.assertEqual(eds.editar_trust(texto, self.D), texto)

    def test_forma_do_config_que_a_edicao_nao_cobre_e_recusada(self):
        casos = {
            "inline sob [hooks.state]": '[hooks.state]\n"p@m:hooks/hooks.json:stop:0:0" = { trusted_hash = "x" }\n',
            "chave pontuada sob [hooks]": '[hooks]\nstate."p@m:hooks/hooks.json:stop:0:0".trusted_hash = "x"\n',
        }
        for nome, texto in casos.items():
            with self.subTest(nome):
                with self.assertRaisesRegex(eds.ErroEnvDocs, "config.toml"):
                    eds.editar_trust(texto, self.D)

    def test_config_invalido_e_recusado(self):
        with self.assertRaisesRegex(eds.ErroEnvDocs, "config.toml"):
            eds.editar_trust("model = \n", self.D)

    def test_valor_fora_do_formato_de_hash_e_recusado(self):
        with self.assertRaisesRegex(eds.ErroEnvDocs, "hash"):
            eds.editar_trust("", {"p@m:hooks/hooks.json:stop:0:0": {"trusted_hash": 'x"\n[y]'}})

    def test_mantem_o_crlf(self):
        novo = eds.editar_trust('model = "m"\r\n', self.D)
        self.assertNotIn("\n", novo.replace("\r\n", ""))
        self.assertEqual(self.estado(novo), self.D)


class InstallCli(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.home, self.bin = base / "codex-home", base / "bin"
        self.home.mkdir()
        self.bin.mkdir()
        self.config = self.home / "config.toml"
        self.config.write_text(f'model = "m"\n\n[mcp_servers.x.env]\nTOKEN = "{CANARIO}"\n', encoding="utf-8")
        self.raiz = _instalar(self.home)
        self.config.chmod(0o600)
        self.original = self.config.read_bytes()
        self.codex_falso("codex-cli 0.164.0")

    def tearDown(self):
        self.tmp.cleanup()

    def codex_falso(self, versao):
        falso = self.bin / "codex"
        falso.write_text(f"#!/bin/sh\necho '{versao}'\n", encoding="utf-8")
        falso.chmod(0o755)

    def cli(self, *args, rc, home=True, path=None):
        env = {"HOME": str(self.tmp.name), "PATH": path or f"{self.bin}:/usr/bin:/bin", "LANG": "C.UTF-8"}
        argv = [sys.executable, "-B", str(SCRIPT), "install", *args]
        if home:
            argv += ["--codex-home", str(self.home)]
        r = subprocess.run(argv, capture_output=True, text=True, env=env)
        self.assertEqual(r.returncode, rc, r.stdout + r.stderr)
        self.assertNotIn(CANARIO, r.stdout + r.stderr)
        return r

    def desejado(self):
        conteudo = eds.impressao_do_pacote(self.raiz)
        return {chave: {"trusted_hash": decl, "trusted_content_hash": conteudo}
                for chave, decl in eds.hooks_do_pacote(self.raiz, ID)}

    def copias(self):
        return sorted(p.name for p in self.home.iterdir() if p.name.startswith("config.toml."))

    def test_dry_run_mostra_exatamente_o_que_entra_e_nao_grava(self):
        r = self.cli("--codex", rc=4)
        esperado = eds.editar_trust(self.original.decode(), self.desejado())
        acrescimo = esperado[len(self.original.decode()):]
        mais = [linha[1:] for linha in r.stdout.splitlines() if linha.startswith("+") and not linha.startswith("+++")]
        self.assertEqual("\n".join(mais) + "\n", acrescimo)
        self.assertEqual(self.config.read_bytes(), self.original)
        self.assertEqual(self.copias(), [])
        self.assertIn(ID, r.stdout)

    def test_apply_grava_com_copia_e_e_idempotente(self):
        r = self.cli("--codex", "--apply", rc=0)
        self.assertEqual(self.config.read_text(encoding="utf-8"),
                         eds.editar_trust(self.original.decode(), self.desejado()))
        self.assertEqual(stat.S_IMODE(self.config.stat().st_mode), 0o600)
        copias = self.copias()
        self.assertEqual(len(copias), 1)
        copia = self.home / copias[0]
        self.assertEqual(copia.read_bytes(), self.original)
        self.assertEqual(stat.S_IMODE(copia.stat().st_mode), 0o600)
        self.assertIn(copias[0], r.stdout)
        gravado = self.config.read_bytes()
        r = self.cli("--codex", "--apply", rc=0)
        self.assertIn("nada a mudar", r.stdout)
        self.assertEqual(self.config.read_bytes(), gravado)
        self.assertEqual(self.copias(), copias)

    def test_conteudo_do_pacote_mudou_troca_so_os_hashes(self):
        self.cli("--codex", "--apply", rc=0)
        (self.raiz / "CHANGELOG.md").write_text("mudou\n", encoding="utf-8")
        self.cli("--codex", "--apply", rc=0)
        estado = tomllib.loads(self.config.read_text(encoding="utf-8"))["hooks"]["state"]
        self.assertEqual(estado, self.desejado())
        self.assertEqual(len(self.copias()), 2)

    def test_plugin_nao_instalado_recusa_sem_tocar_o_config(self):
        shutil.rmtree(self.home / "plugins")
        r = self.cli("--codex", "--apply", rc=1)
        self.assertIn("não está instalado", r.stderr)
        self.assertEqual(self.config.read_bytes(), self.original)
        self.assertEqual(self.copias(), [])

    def test_modo_do_config_e_mantido(self):
        self.config.chmod(0o640)
        self.cli("--codex", "--apply", rc=0)
        self.assertEqual(stat.S_IMODE(self.config.stat().st_mode), 0o640)

    def test_config_que_e_symlink_continua_symlink(self):
        real = Path(self.tmp.name) / "dotfiles" / "codex.toml"
        real.parent.mkdir()
        real.write_bytes(self.original)
        self.config.unlink()
        self.config.symlink_to(real)
        self.cli("--codex", "--apply", rc=0)
        self.assertTrue(self.config.is_symlink())
        self.assertEqual(tomllib.loads(real.read_text(encoding="utf-8"))["hooks"]["state"], self.desejado())

    def test_config_que_muda_entre_o_plano_e_a_gravacao_nao_e_sobrescrito(self):
        plano = eds.planejar_instalacao(self.home)
        self.config.write_text(self.original.decode() + '\n[outra]\nx = 1\n', encoding="utf-8")
        mudado = self.config.read_bytes()
        with self.assertRaisesRegex(eds.ErroEnvDocs, "mudou"):
            eds.aplicar_instalacao(plano)
        self.assertEqual(self.config.read_bytes(), mudado)

    def test_diff_omite_linha_que_nao_e_do_trust(self):
        antes = f'TOKEN = "{CANARIO}"\n'
        depois = f'TOKEN = "{CANARIO}x"\n\n[hooks.state."p@m:hooks/hooks.json:stop:0:0"]\ntrusted_hash = "{H1}"\n'
        linhas = eds.linhas_da_mudanca(antes, depois, "config.toml")
        self.assertNotIn(CANARIO, "\n".join(linhas))
        self.assertIn(f'+trusted_hash = "{H1}"', linhas)
        self.assertIn('+[hooks.state."p@m:hooks/hooks.json:stop:0:0"]', linhas)

    def test_install_sem_codex_e_uso_errado(self):
        self.cli(rc=2)

    def test_codex_home_vem_do_ambiente(self):
        env = {"HOME": str(self.tmp.name), "PATH": f"{self.bin}:/usr/bin:/bin", "CODEX_HOME": str(self.home)}
        r = subprocess.run([sys.executable, "-B", str(SCRIPT), "install", "--codex"],
                           capture_output=True, text=True, env=env)
        self.assertEqual(r.returncode, 4, r.stderr)
        self.assertIn(str(self.config), r.stdout)

    def test_avisa_quando_o_codex_nao_e_a_versao_medida(self):
        r = self.cli("--codex", rc=4)
        self.assertNotIn("aviso", r.stderr)
        self.codex_falso("codex-cli 0.166.0")
        r = self.cli("--codex", rc=4)
        self.assertIn("0.166.0", r.stderr)
        for versao in eds.CODEX_MEDIDOS:
            self.assertIn(versao, r.stderr)
        r = self.cli("--codex", rc=4, path="/nada")
        self.assertIn("aviso", r.stderr)

    def test_versao_conferida_pelo_oraculo_nao_avisa(self):
        # o 0.165.0 entrou pelo tests/oraculo_codex.py (9/9 iguais à fixture), não pela leitura do código
        self.assertEqual(eds.CODEX_MEDIDOS, ("0.164.0", "0.165.0"))
        for versao in eds.CODEX_MEDIDOS:
            self.codex_falso(f"codex-cli {versao}")
            r = self.cli("--codex", rc=4)
            self.assertNotIn("aviso", r.stderr, versao)


if __name__ == "__main__":
    unittest.main()
