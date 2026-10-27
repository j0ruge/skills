"""Varredura: quais .env* entram (include/exclude, exclude padrão, outro checkout, symlink) e o hash."""
import os
import tempfile
import unittest
from pathlib import Path

from support import criar_arvore, eds

INCLUDE = ["**/.env", "**/.env.*"]


class Varredura(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.raiz = Path(self.tmp.name) / "repo"
        criar_arvore(self.raiz, {
            ".env": "A=1\n",
            ".env.example": "A=\n",
            ".env.local": "A=2\n",
            ".envrc": "export X=1\n",
            ".env-docs.json": "{}\n",
            "README.md": "x\n",
            "packages/api/.env": "B=1\n",
            "packages/web/.env.example": "C=\n",
            "tests/fixtures/.env": "F=1\n",
            "node_modules/x/.env": "N=1\n",
            "packages/web/node_modules/y/.env.local": "N=2\n",
            "dist/.env": "D=1\n",
            "graphify-out/.env": "G=1\n",
            "test-results/.env": "T=1\n",
            "playwright-report/.env": "P=1\n",
            ".claude/worktrees/w1/.env": "W=1\n",
            ".worktrees/w2/.env": "W=2\n",
            ".git/.env": "R=1\n",
            # Outro checkout aninhado (worktree, submódulo, clone): tem o próprio .git.
            "outro/.git": "gitdir: /em/outro/lugar\n",
            "outro/.env": "O=1\n",
        })

    def tearDown(self):
        self.tmp.cleanup()

    def test_inclui_env_example_e_exclui_node_modules(self):
        achados = eds.varredura(self.raiz, INCLUDE, ["**/fixtures/**"])
        self.assertEqual(achados, [".env", ".env.example", ".env.local",
                                   "packages/api/.env", "packages/web/.env.example"])

    def test_exclude_padrao_vale_sem_exclude_na_config(self):
        achados = eds.varredura(self.raiz, INCLUDE, [])
        self.assertIn("tests/fixtures/.env", achados)
        for fora in ("node_modules/x/.env", "packages/web/node_modules/y/.env.local", "dist/.env",
                     "graphify-out/.env", "test-results/.env", "playwright-report/.env",
                     ".claude/worktrees/w1/.env", ".worktrees/w2/.env", ".git/.env", "outro/.env"):
            with self.subTest(fora=fora):
                self.assertNotIn(fora, achados)

    def test_include_largo_nunca_pega_a_propria_config(self):
        achados = eds.varredura(self.raiz, ["**/.env*"], [])
        self.assertNotIn(".env-docs.json", achados)
        # `.env*` pega `.envrc`, que não é arquivo de env: por isso o exemplo usa dois padrões.
        self.assertIn(".envrc", achados)

    def test_caminhos_relativos_com_barra_e_ordenados(self):
        achados = eds.varredura(self.raiz, INCLUDE, [])
        self.assertEqual(achados, sorted(achados))
        for caminho in achados:
            self.assertFalse(caminho.startswith(("/", "./")), caminho)
            self.assertNotIn("\\", caminho)

    def test_symlink_entra_so_se_o_alvo_estiver_dentro_da_raiz(self):
        fora = Path(self.tmp.name) / "fora.env"
        fora.write_text("FORA=1\n", encoding="utf-8")
        (self.raiz / "packages/link").mkdir(parents=True)
        os.symlink(self.raiz / ".env", self.raiz / "packages/link/.env")
        os.symlink(fora, self.raiz / "packages/link/.env.local")
        achados = eds.varredura(self.raiz, INCLUDE, [])
        self.assertIn("packages/link/.env", achados)
        self.assertNotIn("packages/link/.env.local", achados)


class CasaPadrao(unittest.TestCase):
    def test_glob(self):
        casos = [
            (".env", ["**/.env"], True),
            ("a/b/.env", ["**/.env"], True),
            ("a/.envx", ["**/.env"], False),
            ("a/.env", [".env*"], False),
            ("a/.env.local", ["a/.env.*"], True),
            ("a/b/.env.local", ["a/*/.env.local"], True),
            ("a/b/c/.env.local", ["a/*/.env.local"], False),
            ("a/.env1", ["a/.env?"], True),
            ("a/.enva", ["a/.env[0-9]"], False),
            ("node_modules/x/.env", ["**/node_modules/**"], True),
            ("a.env", ["**/.env"], False),
        ]
        for caminho, padroes, esperado in casos:
            with self.subTest(caminho=caminho, padroes=padroes):
                self.assertIs(eds.casa_padrao(caminho, padroes), esperado)


class Hash(unittest.TestCase):
    def test_vetores_conhecidos(self):
        self.assertEqual(eds.hash_sha256(b""),
                         "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")
        self.assertEqual(eds.hash_sha256(b"abc"),
                         "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")

    def test_hash_e_dos_bytes_lidos_do_disco(self):
        with tempfile.TemporaryDirectory() as tmp:
            criar_arvore(tmp, {".env": b"A=1\r\n", "b/.env": b"A=1\n"})
            lidos = eds.ler_arquivos(tmp, [".env", "b/.env"])
        self.assertEqual(lidos, {".env": b"A=1\r\n", "b/.env": b"A=1\n"})
        self.assertNotEqual(eds.hash_sha256(lidos[".env"]), eds.hash_sha256(lidos["b/.env"]))


if __name__ == "__main__":
    unittest.main()
