"""Testes do template e dos portões do `build.py` da html-presentation.

Rodar, da raiz da loja: python3 -m unittest discover -s plugins/html-presentation/tests -p 'test_*.py'
Só a biblioteca padrão e o interpretador que roda o teste: nada de rede, navegador ou Playwright. O
`check-fit` e o `check-presenter` pedem o Chromium e ficam fora daqui.

Cada teste roda o `build.py` de verdade, num subprocesso, sobre uma cópia do `assets/deck-template.html` numa
pasta temporária. O teste de portão muda uma coisa só na cópia e espera o `BUILD REPROVADO` daquele portão.
"""
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent / "skills" / "html-presentation"
TEMPLATE = SKILL / "assets" / "deck-template.html"
BUILD = SKILL / "scripts" / "build.py"
COMMENT = re.compile(r"/\*.*?\*/|<!--.*?-->", re.S)
NOTE = re.compile(r'<aside class="notes" data-t="(\d+)">.*?</aside>', re.S)


def _sem_comentario(texto):
    return COMMENT.sub("", texto)


def _soma_das_notas(texto):
    return sum(int(m.group(1)) for m in NOTE.finditer(texto))


def _uma_vez(texto, velho, novo):
    if texto.count(velho) != 1:
        raise AssertionError(f"{velho!r} aparece {texto.count(velho)} vezes no template")
    return texto.replace(velho, novo)


class TemplateEBuild(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="html-presentation-")
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)
        self.fonte = TEMPLATE.read_text(encoding="utf-8")
        # Minutos que cabem as notas e os 30 s de perguntas, como o build.py confere.
        self.minutos = (_soma_das_notas(self.fonte) + 30 + 59) // 60

    def build(self, texto, *extra, nome="deck.html", out="dist"):
        src = self.tmp / nome
        src.write_text(texto, encoding="utf-8")
        r = subprocess.run([sys.executable, str(BUILD), str(src), "--out", str(self.tmp / out), *extra],
                           capture_output=True, text=True, encoding="utf-8", cwd=self.tmp)
        return r.returncode, r.stdout + r.stderr

    def reprova(self, texto, trecho, *extra):
        rc, saida = self.build(texto, "--duration", str(self.minutos), *extra)
        self.assertEqual(rc, 1, saida)
        self.assertIn("BUILD REPROVADO", saida)
        self.assertIn(trecho, saida)
        self.assertFalse((self.tmp / "dist" / "deck.html").exists(), "o build reprovado não grava o deck")

    # O template

    def test_template_traz_o_titulo_estreito_e_a_variante_larga(self):
        css = _sem_comentario(self.fonte)
        self.assertIn(".head .t-title{max-width:30ch}", css)
        self.assertIn(".head .t-title.wide{max-width:none}", css)

    def test_template_passa_no_build_e_gera_o_roteiro(self):
        rc, saida = self.build(self.fonte, "--duration", str(self.minutos))
        self.assertEqual(rc, 0, saida)
        deck = (self.tmp / "dist" / "deck.html").read_text(encoding="utf-8")
        roteiro = (self.tmp / "dist" / "roteiro-de-fala.md").read_text(encoding="utf-8")
        laminas = len(NOTE.findall(self.fonte))
        self.assertGreater(laminas, 0)
        self.assertIn(f"{laminas} lâminas", saida)
        self.assertEqual(len(re.findall(r"^## \d{2} · ", roteiro, re.M)), laminas)
        self.assertIsNone(re.search(r'(?:src|href)="https?://', _sem_comentario(deck)), "o deck pronto não chama a rede")

    # Os portões

    def test_orcamento_acima_do_tempo_reprova(self):
        notas = _soma_das_notas(self.fonte)
        apertado = (notas + 29) / 60  # 1 s abaixo do que as notas pedem com os 30 s de perguntas
        rc, saida = self.build(self.fonte, "--duration", f"{apertado:.6f}")
        self.assertEqual(rc, 1, saida)
        self.assertIn("para perguntas", saida)

    def test_recurso_externo_reprova(self):
        texto = _uma_vez(self.fonte, "</body>", '<script src="https://example.com/x.js"></script>\n</body>')
        self.reprova(texto, "recurso externo")

    def test_recurso_externo_dentro_de_comentario_passa(self):
        texto = _uma_vez(self.fonte, "</body>", '<!-- <script src="https://example.com/x.js"></script> -->\n</body>')
        rc, saida = self.build(texto, "--duration", str(self.minutos))
        self.assertEqual(rc, 0, saida)

    def test_lamina_sem_nota_reprova(self):
        primeira = NOTE.search(self.fonte).group(0)
        self.reprova(_uma_vez(self.fonte, primeira, ""), 'sem <aside class="notes" data-t>')

    def test_asset_ausente_reprova(self):
        texto = _uma_vez(self.fonte, "</body>", '<img src="assets/nao-existe.png" alt="">\n</body>')
        self.reprova(texto, "asset não encontrado: assets/nao-existe.png")

    def test_dica_sem_verbete_reprova(self):
        texto = _uma_vez(self.fonte, "</body>", '<span data-g="chave-sem-verbete">x</span>\n</body>')
        self.reprova(texto, "dica sem verbete no #glossario")

    def test_segundo_deck_na_mesma_pasta_reprova(self):
        rc, saida = self.build(self.fonte, "--duration", str(self.minutos))
        self.assertEqual(rc, 0, saida)
        rc, saida = self.build(self.fonte, "--duration", str(self.minutos), nome="outro.html")
        self.assertEqual(rc, 1, saida)
        self.assertIn("é de outro deck", saida)
        self.assertFalse((self.tmp / "dist" / "outro.html").exists())


if __name__ == "__main__":
    unittest.main()
