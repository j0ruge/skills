#!/usr/bin/env python3
"""Testes do scripts/repetidos.py (só biblioteca padrão).

Rodar a partir do diretório da skill:
    python3 tests/test_repetidos.py

Cada teste monta uma skill num diretório temporário e roda o script como
subprocesso, com `--json`, para provar o contrato que a refatoração usa: o que o
script aponta como repetido é o que pode sair do SKILL.md.
"""
import json
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
SCRIPT = SKILL_DIR / "scripts" / "repetidos.py"

FRASE = ("Não canalize o pull para o tail numa cadeia com e-comercial duplo, porque o "
         "pipeline sai com o status do último comando.")


def montar(skill_md: str, references: dict[str, str] | None = None) -> Path:
    raiz = Path(tempfile.mkdtemp())
    (raiz / "SKILL.md").write_text(textwrap.dedent(skill_md), encoding="utf-8")
    if references is not None:
        (raiz / "references").mkdir()
        for nome, texto in references.items():
            (raiz / "references" / nome).write_text(textwrap.dedent(texto), encoding="utf-8")
    return raiz


def rodar(raiz: Path) -> tuple[int, dict]:
    proc = subprocess.run([sys.executable, str(SCRIPT), str(raiz), "--json"],
                          capture_output=True, text=True)
    return proc.returncode, (json.loads(proc.stdout) if proc.stdout.strip() else {})


class TestRepetidos(unittest.TestCase):
    def test_bloco_inteiro_numa_reference(self):
        raiz = montar("""\
            # S
            ```bash
            git fetch origin -q
            git rev-list --count HEAD
            ```
            """, {"start.md": """\
            ## A8
            ```bash
            git fetch origin -q
            git rev-list --count HEAD
            ```
            """})
        rc, saida = rodar(raiz)
        self.assertEqual(rc, 0)
        (bloco,) = saida["blocos"]
        self.assertEqual((bloco["tipo"], bloco["reference"], bloco["linha"]),
                         ("INTEIRO", "references/start.md", 2))

    def test_bloco_com_toda_linha_coberta_fora_de_ordem(self):
        # A reference tem um comentário no meio: não é contíguo, e cada linha está lá.
        raiz = montar("""\
            ```bash
            git checkout main
            git pull origin main
            ```
            """, {"start.md": """\
            ```bash
            git checkout main
            # poka-yoke
            git pull origin main
            ```
            """})
        _, saida = rodar(raiz)
        (bloco,) = saida["blocos"]
        self.assertEqual((bloco["tipo"], bloco["cobertas"], bloco["total"]), ("COBERTO", 2, 2))

    def test_bloco_indentado_dentro_de_item_de_lista(self):
        # Caso real (ticket 1.9.0): o bloco mora num passo numerado, com a cerca indentada.
        raiz = montar("""\
            8. **Criar branch:**

               ```bash
               git fetch origin -q
               ```
            """, {"start.md": """\
            ```bash
            git fetch origin -q
            ```
            """})
        _, saida = rodar(raiz)
        (bloco,) = saida["blocos"]
        self.assertEqual((bloco["tipo"], bloco["linha"]), ("INTEIRO", 3))

    def test_frase_que_a_reference_ja_tem(self):
        raiz = montar(f"# S\n\n{FRASE}\n", {"start.md": f"## A8\n\n{FRASE}\n"})
        _, saida = rodar(raiz)
        (frase,) = saida["frases"]
        self.assertEqual(frase["reference"], "references/start.md")

    def test_frase_repetida_no_proprio_skill_md(self):
        raiz = montar(f"# S\n\n{FRASE}\n\n## Armadilhas\n\n{FRASE}\n", {})
        _, saida = rodar(raiz)
        (repetida,) = saida["repetidas"]
        self.assertEqual(repetida["linhas"], [3, 7])

    def test_nada_repetido_sai_zero_e_vazio(self):
        raiz = montar("# S\n\nTexto que só existe aqui e em mais lugar nenhum desta skill.\n",
                      {"start.md": "## A\n\nOutro texto.\n"})
        rc, saida = rodar(raiz)
        self.assertEqual((rc, saida["blocos"], saida["frases"], saida["repetidas"]),
                         (0, [], [], []))

    def test_sem_skill_md_e_erro_de_uso(self):
        proc = subprocess.run([sys.executable, str(SCRIPT), tempfile.mkdtemp(), "--json"],
                              capture_output=True, text=True)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("SKILL.md", proc.stderr)


if __name__ == "__main__":
    unittest.main()
