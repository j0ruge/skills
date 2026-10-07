#!/usr/bin/env python3
"""Testes do scripts/md2adf.py (só biblioteca padrão).

Rodar a partir do diretório da skill:
    python3 tests/test_md2adf.py

O conversor é o fallback do close step 5 sem MCP. Até a 1.11.0 ele saía com rc 0
em duas construções que chegavam erradas ao Jira (medido em 07/10/2026, no
fechamento do SBM-6): lista aninhada virava um nível só, e crase dentro de
negrito aparecia literal. Agora as duas são recusadas com rc 1, sem gravar nada.
"""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
SCRIPT = SKILL_DIR / "scripts" / "md2adf.py"


class Md2Adf(unittest.TestCase):

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="test-md2adf-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def rodar(self, md: str):
        entrada, saida = self.tmp / "resumo.md", self.tmp / "comment.json"
        entrada.write_text(md, encoding="utf-8")
        proc = subprocess.run([sys.executable, str(SCRIPT), str(entrada), str(saida)],
                              capture_output=True, text=True)
        doc = json.loads(saida.read_text())["body"] if saida.exists() else None
        return proc.returncode, proc.stderr, doc

    def test_lista_aninhada_e_recusada_sem_gravar(self):
        rc, err, doc = self.rodar("- **0.3.0:**\n  - Domínio novo.\n  - Visual novo.\n- **0.3.1:** QA.\n")
        self.assertEqual(rc, 1)
        self.assertIsNone(doc)
        self.assertIn("linha 2", err)

    def test_lista_numerada_aninhada_tambem(self):
        rc, _, doc = self.rodar("1. Passo\n   1. Subpasso\n")
        self.assertEqual((rc, doc), (1, None))

    def test_crase_dentro_de_negrito_e_recusada(self):
        rc, err, doc = self.rodar("- **`--para`:** recusa o service@.\n")
        self.assertEqual(rc, 1)
        self.assertIsNone(doc)
        self.assertIn("--para", err)

    def test_grupo_em_negrito_com_lista_propria_passa(self):
        md = "**0.3.0:**\n\n- Domínio.\n- Visual.\n\n**0.3.1:** QA.\n\n- Atenção.\n"
        rc, _, doc = self.rodar(md)
        self.assertEqual(rc, 0)
        listas = [len(n["content"]) for n in doc["content"] if n["type"] == "bulletList"]
        self.assertEqual(listas, [2, 1])

    def test_continuacao_recuada_de_item_continua_valendo(self):
        rc, _, doc = self.rodar("- Primeira linha do item\n  que continua aqui.\n")
        self.assertEqual(rc, 0)
        texto = doc["content"][0]["content"][0]["content"][0]["content"][0]["text"]
        self.assertEqual(texto, "Primeira linha do item que continua aqui.")

    def test_lista_recuada_dentro_de_bloco_de_codigo_nao_e_aninhamento(self):
        rc, _, doc = self.rodar("```yaml\nitens:\n  - a\n  - b\n```\n")
        self.assertEqual(rc, 0)
        self.assertEqual(doc["content"][0]["type"], "codeBlock")

    def test_negrito_e_code_separados_continuam_valendo(self):
        rc, _, doc = self.rodar("**Opção:** use `--para`.\n")
        self.assertEqual(rc, 0)
        marks = [[m["type"] for m in n.get("marks", [])] for n in doc["content"][0]["content"]]
        self.assertIn(["strong"], marks)
        self.assertIn(["code"], marks)


if __name__ == "__main__":
    unittest.main()
