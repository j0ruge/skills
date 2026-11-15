#!/usr/bin/env python3
"""Testes do scripts/prose_units.py (só biblioteca padrão).

Rodar a partir do diretório da skill:
    python3 tests/test_prose_units.py

A rodada de verificação lê, em volta de cada linha mudada, a unidade de prosa inteira (o
parágrafo, o item de lista com as continuações, a linha da tabela), e não o arquivo todo. Os
testes de unidade usam um documento fixo; os de linhas mudadas, um repositório git descartável
com um commit base e um commit head.
"""
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
SCRIPT = SKILL_DIR / "scripts" / "prose_units.py"
sys.path.insert(0, str(SCRIPT.parent))
import prose_units  # noqa: E402


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True,
                          capture_output=True, text=True).stdout


class RepoTemporario(unittest.TestCase):
    """Repo descartável; cada teste grava o commit base e o commit head e lê o diff entre eles."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="test-prose-units-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.repo = self.tmp / "repo"
        self.repo.mkdir()
        git(self.repo, "init", "-q", "-b", "main")
        git(self.repo, "config", "user.email", "teste@example.com")
        git(self.repo, "config", "user.name", "teste")
        self.base = self.head = None

    def gravar(self, arquivos: dict[str, str]) -> str:
        """Escreve os arquivos, faz o commit de tudo o que está na árvore e devolve o sha."""
        for nome, texto in arquivos.items():
            caminho = self.repo / nome
            caminho.parent.mkdir(parents=True, exist_ok=True)
            caminho.write_text(texto, encoding="utf-8")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-qm", "commit")
        return git(self.repo, "rev-parse", "HEAD").strip()

    def mudadas(self) -> dict:
        return prose_units.changed_lines(self.repo, self.base, self.head)


class TestUnidadesMarkdown(unittest.TestCase):
    DOC = [
        "# Título",                      # 1
        "",                              # 2
        "Primeira frase do parágrafo",   # 3
        "segunda linha do parágrafo.",   # 4
        "",                              # 5
        "- item um, começo",             # 6
        "  continuação do item um",      # 7
        "  - sub-item",                  # 8
        "- item dois",                   # 9
        "",                              # 10
        "| a | b |",                     # 11
        "| c | d |",                     # 12
        "",                              # 13
        "```",                           # 14
        "codigo",                        # 15
        "```",                           # 16
    ]

    def test_paragrafo_inteiro(self):
        self.assertEqual(prose_units.markdown_units(self.DOC, [4]), [(3, 4)])

    def test_continuacao_devolve_o_item_desde_o_marcador_com_o_sub_item(self):
        self.assertEqual(prose_units.markdown_units(self.DOC, [7]), [(6, 8)])

    def test_alvo_no_sub_item_devolve_so_o_sub_item(self):
        self.assertEqual(prose_units.markdown_units(self.DOC, [8]), [(8, 8)])

    def test_linha_de_tabela_e_a_propria_linha(self):
        self.assertEqual(prose_units.markdown_units(self.DOC, [12]), [(12, 12)])

    def test_bloco_cercado_inteiro(self):
        self.assertEqual(prose_units.markdown_units(self.DOC, [15]), [(14, 16)])

    def test_titulo_sozinho(self):
        self.assertEqual(prose_units.markdown_units(self.DOC, [1]), [(1, 1)])

    def test_dois_alvos_na_mesma_unidade_saem_uma_vez(self):
        self.assertEqual(prose_units.markdown_units(self.DOC, [3, 4]), [(3, 4)])

    def test_linha_em_branco_cai_na_unidade_anterior(self):
        self.assertEqual(prose_units.markdown_units(self.DOC, [5]), [(3, 4)])


class TestLinhasMudadas(RepoTemporario):
    def test_linha_acrescentada(self):
        # base: 3 linhas; head: troca a linha 2
        self.base = self.gravar({"doc.md": "um\ndois\ntrês\n"})
        self.head = self.gravar({"doc.md": "um\nDOIS\ntrês\n"})
        self.assertEqual(self.mudadas()["doc.md"]["added"], [2])

    def test_hunk_que_so_apaga_registra_onde_cortou(self):
        # base: linhas 1..5; head: sem a linha 3
        self.base = self.gravar({"doc.md": "1\n2\n3\n4\n5\n"})
        self.head = self.gravar({"doc.md": "1\n2\n4\n5\n"})
        m = self.mudadas()["doc.md"]
        self.assertEqual((m["added"], m["removed_at"]), ([], [3]))

    def test_cr_solto_numa_linha_nao_abre_arquivo_fantasma(self):
        # base: linhas 1..10; head: troca a linha 2 por uma com CR solto antes de um `diff --git`, e a 10.
        # Lido em modo texto, o CR virava quebra de linha e o hunk da linha 10 ia para o arquivo fantasma.
        linhas = [str(n) for n in range(1, 11)]
        self.base = self.gravar({"doc.md": "\n".join(linhas) + "\n"})
        linhas[1] = "DOIS\rdiff --git a/fantasma.md b/fantasma.md"
        linhas[9] = "DEZ"
        self.head = self.gravar({"doc.md": "\n".join(linhas) + "\n"})
        self.assertEqual(self.mudadas(), {"doc.md": {"added": [2, 10], "removed_at": [], "status": "M"}})


if __name__ == "__main__":
    unittest.main()
