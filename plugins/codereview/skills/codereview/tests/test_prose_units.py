#!/usr/bin/env python3
"""Testes do scripts/prose_units.py (só biblioteca padrão).

Rodar a partir do diretório da skill:
    python3 tests/test_prose_units.py

A rodada de verificação lê, em volta de cada linha mudada, a unidade de prosa inteira (o
parágrafo, o item de lista com as continuações, a linha da tabela, o bloco de comentário), e não
o arquivo todo. Os testes de unidade usam um documento fixo; os de linhas mudadas, de tipo do
arquivo e do CLI, um repositório git descartável com um commit base e um commit head.
"""
import json
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

    def tipo(self, caminho: str) -> str:
        return prose_units.file_kind(self.repo, self.base, self.head, caminho)

    def rodar_cli_rc(self, *opcoes: str) -> int:
        """rc do CLI com o --repo, o --base e o --head do teste; `opcoes` troca algum deles.

        Guarda a saída em self.saida e o stderr em self.erro.
        """
        argumentos = {"--repo": str(self.repo), "--base": self.base, "--head": self.head}
        argumentos.update(zip(opcoes[::2], opcoes[1::2]))
        comando = [sys.executable, str(SCRIPT)]
        for nome, valor in argumentos.items():
            comando += [nome, valor]
        out = subprocess.run(comando, capture_output=True, text=True, encoding="utf-8")
        self.saida, self.erro = out.stdout, out.stderr
        return out.returncode

    def rodar_cli(self) -> dict:
        self.assertEqual(self.rodar_cli_rc(), 0, self.erro)
        return json.loads(self.saida)


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


CS = "class A {\n    /// <summary>\n    /// texto\n    /// </summary>\n    void M() {}\n}\n"
PY = 'def f():\n    """\n    texto antigo\n    """\n    return 1\n'
MD = "# Título\n\nPrimeira frase do parágrafo\nsegunda linha do parágrafo.\n\nOutro parágrafo.\n"


class TestComentarioETipo(RepoTemporario):
    def test_bloco_de_comentario_inteiro(self):
        linhas = ["class A {", "    /// <summary>", "    /// texto", "    /// </summary>", "    void M() {}", "}"]
        self.assertEqual(prose_units.comment_units(linhas, [3], "A.cs"), [(2, 4)])

    def test_diff_so_de_comentario_e_doc_only(self):
        # head troca só a linha "/// texto"
        self.base = self.gravar({"A.cs": CS})
        self.head = self.gravar({"A.cs": CS.replace("/// texto", "/// outro texto")})
        self.assertEqual(self.tipo("A.cs"), "DOC_ONLY")

    def test_diff_com_uma_linha_de_codigo_e_code(self):
        # head troca o comentário e também "void M() {}"
        self.base = self.gravar({"A.cs": CS})
        self.head = self.gravar({"A.cs": CS.replace("/// texto", "/// outro texto")
                                 .replace("void M() {}", "void M() { N(); }")})
        self.assertEqual(self.tipo("A.cs"), "CODE")

    def test_docstring_de_python_cai_em_code(self):
        # head troca só o texto dentro de aspas triplas
        self.base = self.gravar({"m.py": PY})
        self.head = self.gravar({"m.py": PY.replace("texto antigo", "texto novo")})
        self.assertEqual(self.tipo("m.py"), "CODE")

    def test_markdown_e_docs(self):
        self.base = self.gravar({"doc.md": MD})
        self.head = self.gravar({"doc.md": MD.replace("Outro", "Mais um")})
        self.assertEqual(self.tipo("doc.md"), "DOCS")

    def test_identificadores_das_linhas_novas(self):
        linhas = ["o `Foo.Bar` chama o `X` e o `Foo.Bar` de novo", "velha `Baz.Qux`"]
        self.assertEqual(prose_units.identifiers(linhas, [1]), ["Foo.Bar"])


class TestSaida(RepoTemporario):
    def test_json_de_um_intervalo_misto(self):
        # head: doc.md com a linha 4 trocada, A.cs com código trocado, velho.md apagado
        self.base = self.gravar({"doc.md": MD, "A.cs": CS, "velho.md": "texto velho\n"})
        git(self.repo, "rm", "-q", "velho.md")
        self.head = self.gravar({"doc.md": MD.replace("segunda linha", "outra linha"),
                                 "A.cs": CS.replace("void M() {}", "void M() { N(); }")})
        saida = self.rodar_cli()
        por = {f["path"]: f for f in saida["files"]}
        self.assertEqual(por["doc.md"]["units"], [{"start": 3, "end": 4, "changed": [4]}])
        self.assertEqual((por["A.cs"]["kind"], por["A.cs"]["units"]), ("CODE", []))
        self.assertEqual((por["velho.md"]["status"], por["velho.md"]["units"]), ("D", []))
        self.assertEqual(saida["totals"], {"prose_files": 1, "code_files": 1, "units": 1, "unit_lines": 2})

    def test_arquivo_renomeado_sai_pelo_caminho_novo(self):
        # head: git mv a.md b.md e troca uma linha
        self.base = self.gravar({"a.md": MD})
        git(self.repo, "mv", "a.md", "b.md")
        self.head = self.gravar({"b.md": MD.replace("Outro", "Mais um")})
        self.assertIn("b.md", {f["path"] for f in self.rodar_cli()["files"]})

    def test_sha_inexistente_sai_com_rc_2(self):
        self.base = self.gravar({"doc.md": MD})
        self.head = self.gravar({"doc.md": MD.replace("Outro", "Mais um")})
        self.assertEqual(self.rodar_cli_rc("--base", "0" * 40), 2)
        self.assertIn("0" * 40, self.erro)


if __name__ == "__main__":
    unittest.main()
