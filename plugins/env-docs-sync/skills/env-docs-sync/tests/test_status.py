"""`status`: o hash do bloco relido no destino contra o hash do arquivo, sem valor na saída.

K2: a sonda tem caso sabotado. Um byte trocado, no arquivo ou no bloco, tem que dar `diverge` e rc != 0;
uma sonda que só sabe dizer `ok` não prova nada.
"""
import json
import tempfile
import unittest
from pathlib import Path

from support import CANARIO, QUANDO_ISO, config_so_development, criar_arvore, eds, rodar_cli


class Status(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.raiz, self.estado, self.destino = base / "repo", base / "estado.json", base / "destino"
        criar_arvore(self.raiz, {".env": f"DB_PASSWORD={CANARIO}\nURL=http://localhost\n",
                                 "packages/api/.env.local": "PORT=3000\n"})
        (self.raiz / ".env-docs.json").write_text(json.dumps(config_so_development()), encoding="utf-8")
        r = rodar_cli("sync", "--root", self.raiz, "--state", self.estado, "--now", QUANDO_ISO,
                      "--commit", "abc1234", "--to-dir", self.destino)
        self.assertEqual(r.returncode, 0, r.stderr)

    def tearDown(self):
        self.tmp.cleanup()

    def status(self, rc):
        r = rodar_cli("status", "--root", self.raiz, "--to-dir", self.destino)
        self.assertEqual(r.returncode, rc, r.stdout + r.stderr)
        self.assertNotIn(CANARIO, r.stdout + r.stderr)
        return r.stdout.splitlines()

    def test_tudo_ok_sai_0(self):
        linhas = self.status(0)
        self.assertIn("ok\tdevelopment\t.env", linhas)
        self.assertIn("ok\tdevelopment\tpackages/api/.env.local", linhas)
        self.assertIn("2 ok, 0 diverge, 0 ausente", linhas[-1])

    def test_sabotado_um_byte_no_arquivo_local_diverge(self):
        arquivo = self.raiz / ".env"
        dados = bytearray(arquivo.read_bytes())
        dados[-2] ^= 0x01
        arquivo.write_bytes(bytes(dados))
        linhas = self.status(3)
        self.assertIn("diverge\tdevelopment\t.env", linhas)
        self.assertIn("ok\tdevelopment\tpackages/api/.env.local", linhas)

    def test_sabotado_um_byte_no_bloco_do_destino_diverge(self):
        bloco = self.destino / "development" / "packages" / "api" / ".env.local.html"
        bloco.write_text(bloco.read_text(encoding="utf-8").replace("PORT=3000", "PORT=3001"), encoding="utf-8")
        self.assertIn("diverge\tdevelopment\tpackages/api/.env.local", self.status(3))

    def test_bloco_que_falta_no_destino_e_ausente(self):
        (self.destino / "development" / ".env.html").unlink()
        self.assertIn("ausente\tdevelopment\t.env", self.status(3))

    def test_bloco_sem_pre_e_diverge(self):
        (self.destino / "development" / ".env.html").write_text("<p>só texto</p>", encoding="utf-8")
        self.assertIn("diverge\tdevelopment\t.env", self.status(3))

    def test_funcao_pura(self):
        destino = eds.DestinoDiretorio(self.destino)
        atuais = {"development": {".env": (self.raiz / ".env").read_bytes(), "novo/.env": b"A=1\n"}}
        self.assertEqual(eds.status_dos_arquivos(atuais, destino),
                         [("development", ".env", "ok"), ("development", "novo/.env", "ausente")])

    def test_sem_to_dir_usa_o_backend_da_config_e_falha_sem_vazar(self):
        r = rodar_cli("status", "--root", self.raiz)
        self.assertNotEqual(r.returncode, 0)
        self.assertNotIn(CANARIO, r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()
