"""Bloco de arquivo: o corpo exato, o escape, a volta (corpo → conteúdo) e o callout de ausente."""
import unittest
from datetime import date

from support import QUANDO, eds

PRE = '<pre><code class="language-bash">'


class BlocoDeArquivo(unittest.TestCase):
    def test_corpo_exato_com_escape(self):
        corpo = eds.bloco_de_arquivo(b'A=<b>&"x"\n', sincronizado_em=QUANDO, commit="abc1234def5678")
        self.assertEqual(corpo, PRE + 'A=&lt;b&gt;&amp;"x"\n</code></pre>\n'
                                '<p>ⓘ sincronizado em 2026-10-27 14:05 · commit abc1234</p>')

    def test_sem_commit_nao_tem_trecho_de_commit(self):
        corpo = eds.bloco_de_arquivo("A=1\n", sincronizado_em=QUANDO, commit=None)
        self.assertTrue(corpo.endswith("<p>ⓘ sincronizado em 2026-10-27 14:05</p>"))
        self.assertNotIn("commit", corpo)

    def test_commit_invalido_e_erro(self):
        for ruim in ("xyz", "--help", "ABC1234", "abc", ""):
            with self.subTest(ruim=ruim), self.assertRaises(eds.ErroEnvDocs):
                eds.bloco_de_arquivo("A=1\n", sincronizado_em=QUANDO, commit=ruim)

    def test_conteudo_que_nao_e_utf8_e_erro(self):
        with self.assertRaises(eds.ErroEnvDocs):
            eds.bloco_de_arquivo(b"A=\xff\xfe\n", sincronizado_em=QUANDO, commit=None)

    def test_ida_e_volta(self):
        textos = ["A=1\n", "P=a<b>&amp;c\n", "X=\"$HOME\" 'q'\n", "ç=ã → ✓\n", "", "\ncomeça com quebra\n",
                  "sem quebra no fim", "A=1\r\nB=2\r\n", "</code></pre><script>x</script>\n"]
        for texto in textos:
            with self.subTest(texto=texto):
                corpo = eds.bloco_de_arquivo(texto, sincronizado_em=QUANDO, commit="abc1234")
                self.assertEqual(eds.conteudo_do_bloco(corpo), texto)

    def test_volta_tolera_os_ids_que_o_bookstack_acrescenta(self):
        corpo = eds.bloco_de_arquivo("A=<1>\n", sincronizado_em=QUANDO, commit="abc1234")
        relido = corpo.replace("<pre>", '<pre id="bkmrk-a%3D1">').replace("<p>", '<p id="bkmrk-sinc">')
        self.assertEqual(eds.conteudo_do_bloco(relido), "A=<1>\n")

    def test_corpo_sem_bloco_fechado(self):
        for corpo in ("<p>sem bloco</p>", "<pre>sem code</pre>", '<pre><code class="language-bash">A=1'):
            with self.subTest(corpo=corpo):
                self.assertIsNone(eds.conteudo_do_bloco(corpo))


class Ausente(unittest.TestCase):
    def setUp(self):
        self.corpo = eds.bloco_de_arquivo("A=1\n", sincronizado_em=QUANDO, commit="abc1234")

    def test_callout(self):
        callout = eds.callout_ausente(date(2026, 10, 27))
        self.assertTrue(callout.startswith('<p class="callout danger">ausente desde 2026-10-27'), callout)
        self.assertTrue(callout.endswith("</p>"))

    def test_mantem_o_bloco(self):
        marcado = eds.marcar_ausente(self.corpo, date(2026, 10, 27))
        self.assertEqual(marcado, eds.callout_ausente(date(2026, 10, 27)) + "\n" + self.corpo)
        self.assertEqual(eds.conteudo_do_bloco(marcado), "A=1\n")

    def test_nao_duplica_o_callout(self):
        uma = eds.marcar_ausente(self.corpo, date(2026, 10, 1))
        relida = uma.replace('<p class="callout danger">', '<p id="bkmrk-ausente" class="callout danger">')
        duas = eds.marcar_ausente(relida, date(2026, 10, 27))
        self.assertEqual(duas.count("ausente desde"), 1)
        self.assertIn("ausente desde 2026-10-27", duas)
        self.assertEqual(eds.conteudo_do_bloco(duas), "A=1\n")

    def test_sem_corpo_anterior_fica_so_o_callout(self):
        self.assertEqual(eds.marcar_ausente(None, date(2026, 10, 27)), eds.callout_ausente(date(2026, 10, 27)))


if __name__ == "__main__":
    unittest.main()
