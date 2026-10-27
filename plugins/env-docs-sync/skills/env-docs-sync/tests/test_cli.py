"""CLI mínima, ponta a ponta num repo sintético, com o canário: ele chega ao destino e a nenhum outro lugar."""
import json
import stat
import tempfile
import unittest
from pathlib import Path

from support import CANARIO, QUANDO_ISO, config_exemplo, criar_arvore, eds, rodar_cli


class Cli(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.raiz, self.estado, self.destino = base / "repo", base / "dados" / "estado.json", base / "destino"
        criar_arvore(self.raiz, {
            ".env": f"DB_PASSWORD={CANARIO}_a\nAPI_URL=https://api.example.com\n",
            "packages/api/.env.example": "DB_PASSWORD=\n",
            "node_modules/x/.env": f"DB_PASSWORD={CANARIO}_nm\n",
        })
        (self.raiz / ".env-docs.json").write_text(json.dumps(config_exemplo()), encoding="utf-8")
        self.saidas = []

    def tearDown(self):
        self.tmp.cleanup()

    def cli(self, *args, rc=0):
        resultado = rodar_cli(*args)
        self.saidas.append(resultado.stdout + resultado.stderr)
        self.assertEqual(resultado.returncode, rc, resultado.stderr)
        return resultado

    def comum(self):
        return ["--root", self.raiz, "--state", self.estado]

    def sync(self, rc=0):
        return self.cli("sync", *self.comum(), "--now", QUANDO_ISO, "--commit", "abc1234",
                        "--to-dir", self.destino, rc=rc)

    def test_validate_ok_e_config_quebrada_sai_2(self):
        saida = self.cli("validate", "--root", self.raiz).stdout
        self.assertIn("page_id=4242", saida)
        cfg = config_exemplo()
        del cfg["doc"]["page_id"]
        (self.raiz / ".env-docs.json").write_text(json.dumps(cfg), encoding="utf-8")
        erro = self.cli("validate", "--root", self.raiz, rc=2).stderr
        self.assertIn("config.doc.page_id: campo obrigatório ausente", erro)

    def test_scan_lista_caminhos_e_hash_curto(self):
        linhas = self.cli("scan", "--root", self.raiz).stdout.splitlines()
        sha = eds.hash_sha256((self.raiz / ".env").read_bytes())[:12]
        self.assertIn(f"development\t.env\tsha256:{sha}", linhas)
        self.assertIn("2 arquivo(s)", linhas[-1])

    def test_plan_sync_e_plan_de_novo_fica_vazio(self):
        plano = self.cli("plan", *self.comum()).stdout
        self.assertIn("development criar .env ", plano)
        self.assertIn("development criar packages/api/.env.example ", plano)
        self.sync()
        self.assertIn("nada a sincronizar", self.cli("plan", *self.comum()).stdout)
        self.assertIn("nada a sincronizar", self.sync().stdout)

    def test_sync_grava_estado_0600_e_bloco_no_destino(self):
        self.sync()
        self.assertEqual(stat.S_IMODE(self.estado.stat().st_mode), 0o600)
        bloco = (self.destino / "development" / ".env.html").read_text(encoding="utf-8")
        self.assertEqual(eds.conteudo_do_bloco(bloco), (self.raiz / ".env").read_text(encoding="utf-8"))
        self.assertEqual(stat.S_IMODE((self.destino / "development" / ".env.html").stat().st_mode), 0o600)

    def test_canario_nunca_em_stdout_stderr_nem_estado(self):
        self.cli("validate", "--root", self.raiz)
        self.cli("scan", "--root", self.raiz)
        self.cli("plan", *self.comum())
        self.sync()
        (self.raiz / ".env").write_text(f"DB_PASSWORD={CANARIO}_b\n", encoding="utf-8")
        self.cli("plan", *self.comum())
        self.sync()
        (self.raiz / ".env").unlink()
        self.sync()
        pagina = Path(self.tmp.name) / "pagina.html"
        self.cli("render-page", "--root", self.raiz, "--now", QUANDO_ISO, "--commit", "abc1234", "--out", pagina)
        for saida in self.saidas:
            self.assertNotIn(CANARIO, saida)
        self.assertNotIn(CANARIO, self.estado.read_text(encoding="utf-8"))
        # Controle positivo: o canário existe e chega aos destinos; o teste enxergaria um vazamento.
        bloco = (self.destino / "development" / ".env.html").read_text(encoding="utf-8")
        self.assertIn(f"{CANARIO}_b", bloco)
        self.assertIn("ausente desde 2026-10-27", bloco)
        self.assertNotIn(CANARIO, pagina.read_text(encoding="utf-8"))  # o .env já foi apagado
        self.assertNotIn(f"{CANARIO}_nm", "".join(p.read_text(encoding="utf-8")
                                                  for p in self.destino.rglob("*.html")))

    def test_render_page_grava_0600_com_o_canario_so_no_arquivo(self):
        pagina = Path(self.tmp.name) / "saida" / "pagina.html"
        saida = self.cli("render-page", "--root", self.raiz, "--now", QUANDO_ISO, "--commit", "abc1234",
                         "--out", pagina).stdout
        self.assertIn("1 ambiente(s) com blocos, 2 bloco(s)", saida)
        self.assertNotIn(CANARIO, saida)
        self.assertEqual(stat.S_IMODE(pagina.stat().st_mode), 0o600)
        self.assertIn(f"{CANARIO}_a", pagina.read_text(encoding="utf-8"))

    def test_arquivo_nao_utf8_falha_sem_vazar(self):
        (self.raiz / ".env.bin").write_bytes(f"TOKEN={CANARIO}_x".encode() + b"\xff\n")
        resultado = self.sync(rc=1)
        self.assertIn(".env.bin", resultado.stderr)
        for saida in self.saidas:
            self.assertNotIn(CANARIO, saida)
        self.assertFalse(self.estado.exists(), "falha no planejamento não grava estado")

    def test_ambientes_remotos_ficam_de_fora_nesta_versao(self):
        saida = self.sync().stdout
        self.assertIn("ignorados nesta versão: staging, production", saida)


if __name__ == "__main__":
    unittest.main()
