"""`init`: a `.env-docs.json` inicial sai da Varredura e do hostname; o que só a pessoa sabe fica null.

O null é de propósito: o `validate` recusa cada campo null com o caminho JSON, e a lista de erros vira
a lista do que preencher. Um texto "a preencher" passaria no `validate` e viraria aviso no hook.
"""
import json
import socket
import tempfile
import unittest
from pathlib import Path

from support import CANARIO, criar_arvore, eds, rodar_cli

A_PREENCHER = ("config.doc.cli", "config.doc.python", "config.doc.target", "config.doc.page_id",
               "config.doc.allowed_roles", "config.environments.development.server",
               "config.environments.development.domain")


class Init(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.raiz = Path(self.tmp.name) / "repo"
        criar_arvore(self.raiz, {
            ".env": f"DB_PASSWORD={CANARIO}\n",
            "packages/api/.env.example": "DB_PASSWORD=\n",
            "node_modules/x/.env": f"X={CANARIO}\n",
            ".envrc": "use flake\n",
        })
        self.arquivo = self.raiz / ".env-docs.json"

    def tearDown(self):
        self.tmp.cleanup()

    def test_config_inicial_da_varredura_e_do_hostname(self):
        config = eds.config_inicial(self.raiz, "estacao-x")
        dev = config["environments"]["development"]
        self.assertEqual(dev["machine"], "estacao-x")
        self.assertEqual(dev["where"], "checkout principal: raiz, packages/api")
        self.assertEqual(dev["source_of_truth"], "checkout principal em estacao-x")
        self.assertEqual(config["include"], ["**/.env", "**/.env.*"])
        self.assertIsNone(config["doc"]["page_id"])

    def test_preenchidos_os_nulls_a_config_vale(self):
        config = eds.config_inicial(self.raiz, "estacao-x")
        config["doc"].update(cli="~/kb.py", python="python3", target="staging", page_id=7, allowed_roles=["Admin"])
        config["environments"]["development"].update(server="estacao-x", domain="localhost")
        eds.validar_config(config)

    def test_cli_grava_e_o_validate_lista_o_que_falta(self):
        r = rodar_cli("init", "--root", self.raiz)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn(CANARIO, r.stdout + r.stderr)
        self.assertIn(".env", r.stdout)
        self.assertIn("packages/api/.env.example", r.stdout)
        self.assertNotIn("node_modules", r.stdout)
        for campo in A_PREENCHER:
            self.assertIn(campo, r.stdout)
        config = json.loads(self.arquivo.read_text(encoding="utf-8"))
        self.assertEqual(config["environments"]["development"]["machine"], socket.gethostname())
        v = rodar_cli("validate", "--root", self.raiz)
        self.assertEqual(v.returncode, 2)
        self.assertEqual(sorted(l.split(":")[1].strip() for l in v.stderr.splitlines()), sorted(A_PREENCHER))

    def test_nao_sobrescreve_a_config_que_existe(self):
        self.arquivo.write_text("{}\n", encoding="utf-8")
        r = rodar_cli("init", "--root", self.raiz)
        self.assertEqual(r.returncode, 1)
        self.assertIn("já existe", r.stderr)
        self.assertEqual(self.arquivo.read_text(encoding="utf-8"), "{}\n")


if __name__ == "__main__":
    unittest.main()
