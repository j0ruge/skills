"""O sensor de nomes privados: limpo na árvore real, vermelho quando sabotado, e sem texto puro na lista.

Este arquivo é varrido como qualquer outro: o nome real da lista só aparece montado em tempo de execução,
e os casos usam um nome inventado, com hash calculado aqui.
"""
import contextlib
import importlib.util
import io
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

RAIZ = Path(__file__).resolve().parents[1]
SCRIPT = RAIZ / 'scripts/check-private-names.py'
_spec = importlib.util.spec_from_file_location('check_private_names', SCRIPT)
cpn = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cpn)

# Apelido antigo, já público no próprio histórico: prova que a lista real está ligada, sem revelar nada dela.
CANARIO = 'portal' + '_app'


class Base(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name)
        self.hashes = {cpn.resumo('cafe_tutor'), cpn.resumo('cafe tutor'), cpn.resumo('xy9')}

    def achar(self, texto, nome='doc.md'):
        (self.dir / nome).parent.mkdir(parents=True, exist_ok=True)
        (self.dir / nome).write_text(texto, encoding='utf-8')
        return cpn.varrer(self.dir, self.hashes)


class ArvoreReal(Base):
    def test_a_arvore_esta_limpa(self):
        self.assertEqual(cpn.varrer(RAIZ, cpn.carregar()), [])

    def test_a_lista_real_esta_ligada(self):
        (self.dir / 'doc.md').write_text(f'no {CANARIO} em 2026\n', encoding='utf-8')
        self.assertEqual(cpn.varrer(self.dir, cpn.carregar()), [('doc.md', 1, CANARIO)])

    def test_a_lista_so_tem_hashes(self):
        linhas = cpn.LISTA.read_text(encoding='utf-8').splitlines()
        dados = [l for l in linhas if not l.startswith('#')]
        self.assertGreater(len(dados), 20)
        self.assertEqual(dados, sorted(set(dados)))
        for linha in dados:
            self.assertRegex(linha, r'^[0-9a-f]{64}$')


class Grafias(Base):
    def test_separador_e_caixa_nao_escondem(self):
        for grafia in ('cafe_tutor', 'cafe-tutor', 'cafe.tutor', 'CafeTutor', 'CAFE_TUTOR', 'cafetutor'):
            with self.subTest(grafia=grafia):
                self.assertTrue(self.achar(f'medido no `{grafia}` em 2026\n'), grafia)

    def test_prefixo_e_sufixo_nao_escondem(self):
        for grafia in ('cafe_tutor-p1', '../cafe_tutor-PRC-65', '~/repos/cafe_tutor/.env', 'dono/cafe_tutor#104', '@cafe-tutor/shared'):
            with self.subTest(grafia=grafia):
                self.assertTrue(self.achar(f'em {grafia}, depois\n'), grafia)

    def test_forma_com_espaco_so_vale_se_listada(self):
        self.assertTrue(self.achar('o Cafe Tutor abriu\n'))
        self.hashes = {cpn.resumo('cafe_tutor')}
        self.assertEqual(self.achar('o Cafe Tutor abriu\n'), [])

    def test_pedaco_de_outra_palavra_nao_e_achado(self):
        for texto in ('cafetutorial', 'cafe_tutorial', 'tutor', 'cafe', 'meu cafe, tutor', 'xy90', 'axy9', 'cafe  tutor'):
            with self.subTest(texto=texto):
                self.assertEqual(self.achar(texto + '\n'), [])

    def test_palavra_curta_inteira_e_achado(self):
        self.assertEqual(self.achar('rodou no XY9 ontem\n'), [('doc.md', 1, 'xy9')])


class Arquivos(Base):
    def test_o_caminho_tambem_e_varrido(self):
        self.assertEqual(self.achar('limpo\n', nome='notas/cafe_tutor.md'), [('notas/cafe_tutor.md', 0, 'cafe_tutor')])

    def test_o_numero_da_linha_e_o_certo(self):
        self.assertEqual(self.achar('um\ndois\nno xy9\n'), [('doc.md', 3, 'xy9')])

    def test_binario_so_tem_o_caminho_varrido(self):
        (self.dir / 'foto.png').write_bytes(b'\x89PNG\0 cafe_tutor')
        self.assertEqual(cpn.varrer(self.dir, self.hashes), [])

    def test_utf8_invalido_nao_derruba(self):
        (self.dir / 'doc.md').write_bytes(b'no xy9 \xff\xfe\n')
        self.assertEqual(cpn.varrer(self.dir, self.hashes), [('doc.md', 1, 'xy9')])

    def test_ignorado_pelo_git_fica_de_fora(self):
        subprocess.run(['git', 'init', '-q', str(self.dir)], check=True)
        (self.dir / '.gitignore').write_text('local.md\n', encoding='utf-8')
        (self.dir / 'local.md').write_text('no xy9\n', encoding='utf-8')
        self.assertEqual(self.achar('no xy9\n'), [('doc.md', 1, 'xy9')])


class Lista(Base):
    def test_lista_vazia_ou_invalida_e_erro(self):
        arquivo = self.dir / 'lista'
        arquivo.write_text(cpn.CABECALHO, encoding='utf-8')
        with self.assertRaises(ValueError):
            cpn.carregar(arquivo)
        arquivo.write_text('nome em texto puro\n', encoding='utf-8')
        with self.assertRaises(ValueError):
            cpn.carregar(arquivo)

    def test_lista_ausente_e_erro_na_linha_de_comando(self):
        copia = self.dir / 'scripts'
        copia.mkdir()
        shutil.copy(SCRIPT, copia)
        r = subprocess.run([sys.executable, str(copia / SCRIPT.name)], capture_output=True, text=True)
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)

    def test_add_e_remove(self):
        lista = self.dir / 'lista'

        def mudar(argumento, nome):
            with contextlib.redirect_stdout(io.StringIO()):
                return cpn._mudar(argumento, nome, lista)

        self.assertEqual(mudar('--add', 'Cafe-Tutor'), 0)
        self.assertEqual(cpn.carregar(lista), {cpn.resumo('cafe_tutor')})
        self.assertNotIn('cafe', lista.read_text(encoding='utf-8').replace(cpn.CABECALHO, ''))
        self.assertEqual(mudar('--add', 'outro_nome'), 0)
        self.assertEqual(mudar('--remove', 'cafe_tutor'), 0)
        self.assertEqual(cpn.carregar(lista), {cpn.resumo('outro_nome')})
        self.assertEqual(mudar('--remove', 'cafe_tutor'), 1)


@unittest.skipUnless(importlib.util.find_spec('yaml'), 'o validate-versions exige PyYAML')
class LigadoAoValidate(Base):
    """O retrofit roda o validate-versions antes de todo commit: é ele que faz o sensor valer sem ninguém lembrar."""

    def rodar(self):
        (self.dir / 'scripts').mkdir(exist_ok=True)
        for nome in ('validate-versions.py', 'check-private-names.py', 'private-names.sha256', 'codex-marketplace.py', 'codex-adapters.py'):
            shutil.copy(RAIZ / 'scripts' / nome, self.dir / 'scripts')
        shutil.copy(RAIZ / 'install.py', self.dir)
        (self.dir / '.claude-plugin').mkdir(exist_ok=True)
        (self.dir / '.claude-plugin/marketplace.json').write_text('{"plugins": []}\n', encoding='utf-8')
        return subprocess.run([sys.executable, str(self.dir / 'scripts/validate-versions.py')], capture_output=True, text=True, encoding='utf-8', errors='replace')

    def test_o_validate_reprova_o_nome_e_diz_a_regra(self):
        (self.dir / 'doc.md').write_text(f'no {CANARIO} em 2026\n', encoding='utf-8')
        r = self.rodar()
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn('nome privado', r.stdout)
        self.assertIn('termo generico', r.stdout)

    def test_sem_o_nome_o_validate_nao_acusa(self):
        (self.dir / 'doc.md').write_text('limpo\n', encoding='utf-8')
        self.assertNotIn('nome privado', self.rodar().stdout)

    def test_sem_a_lista_o_validate_reprova(self):
        self.rodar()
        (self.dir / 'scripts/private-names.sha256').unlink()
        r = subprocess.run([sys.executable, str(self.dir / 'scripts/validate-versions.py')], capture_output=True, text=True, encoding='utf-8', errors='replace')
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn('nomes privados', r.stdout)


if __name__ == '__main__':
    unittest.main()
