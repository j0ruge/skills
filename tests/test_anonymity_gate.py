"""A camada 1 do portão de anonimização: acha nome, e-mail, caminho com usuário e segredo nas linhas novas.

Este arquivo é varrido como qualquer outro, e a camada 1 roda sobre o próprio ramo: todo texto de
sabotagem (nome inventado, e-mail, caminho com usuário, forma de segredo) é montado em tempo de execução.
"""
import hashlib
import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import unittest.mock

RAIZ = Path(__file__).resolve().parents[1]
SCRIPT = RAIZ / 'scripts/anonymity-gate.py'
_spec = importlib.util.spec_from_file_location('anonymity_gate', SCRIPT)
ag = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ag)
cpn = ag.cpn

NOME = 'xq' + '7zeta'
BARRA = '\\'
EMAIL = 'fulano' + '@' + 'exemplo' + '.org'


def _ambiente():
    env = dict(os.environ)
    env.update({'GIT_CONFIG_GLOBAL': os.devnull, 'GIT_CONFIG_NOSYSTEM': '1',
                'GIT_AUTHOR_NAME': 't', 'GIT_AUTHOR_EMAIL': 't',
                'GIT_COMMITTER_NAME': 't', 'GIT_COMMITTER_EMAIL': 't'})
    return env


class Base(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name)
        self.repo = self.dir / 'repo'
        self.repo.mkdir()
        self.env = _ambiente()
        self.git('init', '-q')
        self.hashes = {cpn.resumo(NOME)}
        self._base = False

    def git(self, *args):
        return subprocess.run(['git', '-C', str(self.repo), *args], check=True, capture_output=True, env=self.env)

    def _gravar(self, arquivos):
        for nome, texto in arquivos.items():
            caminho = self.repo / nome
            caminho.parent.mkdir(parents=True, exist_ok=True)
            caminho.write_text(texto, encoding='utf-8')
        self.git('add', '-A')

    def base(self, arquivos=None):
        self._gravar(arquivos or {})
        self.git('commit', '-q', '--allow-empty', '-m', 'base')
        self.git('branch', 'base')
        self._base = True

    def commit(self, arquivos, mensagem='novo'):
        if not self._base:
            self.base()
        self._gravar(arquivos)
        self.git('commit', '-q', '--allow-empty', '-m', mensagem)

    def camada1(self, **kw):
        kw.setdefault('hashes', self.hashes)
        kw.setdefault('publicos', set())
        return ag.camada1(self.repo, 'base', **kw)

    def tipos(self, **kw):
        return [(a[0], a[2]) for a in self.camada1(**kw)]


class Nomes(Base):
    def test_nome_da_lista_em_linha_nova_e_achado(self):
        self.base({'doc.md': 'um\n'})
        self.commit({'doc.md': f'um\ndois\nmedido no {NOME}\n'})
        self.assertEqual(self.camada1(), [('doc.md', 3, 'lista', NOME)])

    def test_nome_da_colheita_na_mensagem_do_commit_e_achado(self):
        nome = 'cafe' + '_tutor'
        self.commit({'doc.md': 'limpo\n'}, mensagem=f'fix: medido no {nome}')
        achados = ag.camada1(self.repo, 'base', extras={nome}, hashes=self.hashes, publicos=set())
        self.assertEqual([(a[0], a[2]) for a in achados], [('<mensagem>', 'colheita')])

    def test_par_com_espaco_da_colheita_e_achado(self):
        self.base({'doc.md': 'um\n'})
        self.commit({'doc.md': 'um\no Aaa Bbb abriu\n'})
        self.assertEqual(self.tipos(extras={'aaa bbb'}), [('doc.md', 'colheita')])

    def test_linha_antiga_nao_e_achado(self):
        self.base({'doc.md': f'no {NOME}\num\n'})
        self.commit({'doc.md': f'no {NOME}\ndois\n'})
        self.assertEqual(self.camada1(), [])

    def test_caminho_de_arquivo_novo_e_varrido(self):
        rel = f'notas/{NOME}.md'
        self.commit({rel: 'limpo\n'})
        self.assertEqual(self.camada1(), [(rel, 0, 'lista', NOME)])

    def test_arquivo_de_nome_com_acento_e_varrido(self):
        rel = 'notas/doc-a' + 'ção' + '.md'
        self.base({'doc.md': 'um\n'})
        self.commit({rel: f'um\nfale com {EMAIL}\n'})
        self.assertEqual([a[:3] for a in self.camada1()], [(rel, 2, 'email')])

    @unittest.skipIf(os.name == 'nt', 'o Windows nao aceita tab nem aspas em nome de arquivo')
    def test_arquivo_de_nome_citado_pelo_git_e_varrido(self):
        for rel in ('doc' + '\t' + 'x.md', 'doc' + '"' + 'x.md', 'doc' + ' ' + 'x.md'):
            with self.subTest(rel=rel):
                self.setUp()
                self.base({'outro.md': 'um\n'})
                self.commit({rel: f'um\nfale com {EMAIL}\n'})
                self.assertEqual([a[:3] for a in self.camada1()], [(rel, 2, 'email')])

    def test_publico_isenta_nome_e_nunca_segredo(self):
        segredo = 'gh' + 'p_' + 'a1b2c3d4e5f6'
        self.base({'doc.md': 'um\n'})
        self.commit({'doc.md': f'um\nno {NOME}, cafe' + '_tutor\n'})
        publicos = {cpn.chave(NOME), cpn.chave('cafe' + '_tutor')}
        self.assertEqual(self.camada1(extras={'cafe' + '_tutor'}, publicos=publicos), [])
        self.commit({'doc.md': f'um\nchave {segredo}\n'})
        self.assertEqual(self.tipos(publicos={cpn.chave(segredo), cpn.chave(segredo[4:])}), [('doc.md', 'segredo')])


class Padroes(Base):
    def linha(self, texto):
        self.base({'doc.md': 'um\n'})
        self.commit({'doc.md': f'um\n{texto}\n'})
        return self.tipos()

    def test_email_e_achado(self):
        self.assertEqual(self.linha(f'fale com {EMAIL} amanha'), [('doc.md', 'email')])

    def test_email_logo_depois_de_modelo_de_conexao_e_achado(self):
        real = 'fulano.silva' + '@' + 'gmail' + '.com'
        self.assertEqual(self.linha('redis' + '://' + ':' + '$P' + '@' + real), [('doc.md', 'email')])

    def test_caminho_com_usuario_e_achado(self):
        usuario = 'ful' + 'ano'
        for forma in (f'/home/{usuario}/x', f'/Users/{usuario}/x',
                      f'C:{BARRA}Users{BARRA}{usuario}{BARRA}x', f'/mnt/d/{usuario}/x',
                      f'C:{BARRA * 2}Users{BARRA * 2}{usuario}{BARRA * 2}x',
                      f'c:{BARRA}users{BARRA}{usuario}{BARRA}x',
                      f'c:/users/{usuario}/x', f'C:/Users/{usuario}/x'):
            with self.subTest(forma=forma):
                self.setUp()
                self.assertEqual(self.linha(f'em {forma} rodou'), [('doc.md', 'caminho')])

    def test_placeholder_de_caminho_passa(self):
        for forma in ('/home/<u>/x', '/home/$USER/x', f'C:{BARRA}Users{BARRA}%USERNAME%', '/mnt/<x>/{pasta}'):
            with self.subTest(forma=forma):
                self.setUp()
                self.assertEqual(self.linha(f'em {forma} rodou'), [])

    def test_publico_isenta_o_segmento_do_caminho(self):
        usuario = 'ful' + 'ano'
        self.base({'doc.md': 'um\n'})
        self.commit({'doc.md': f'um\nem /home/{usuario}/x\n'})
        self.assertEqual(self.camada1(publicos={usuario}), [])

    def test_forma_de_segredo_e_achado(self):
        corpo = 'a1b2c3d4e5f6'
        letras_digitos = 'a1' * 16 + 'b'
        casos = ['sk' + '-' + corpo, 'gh' + 'p_' + corpo, 'xox' + 'b-' + corpo, 'xox' + 's-' + corpo,
                 'AK' + 'IA' + corpo.upper(), 'Bear' + 'er ' + corpo + 'ghij', 'Bas' + 'ic ' + corpo + 'ghij',
                 hashlib.sha256(b'x').hexdigest(), letras_digitos]
        casos += [f'{esquema}://' + 'usu' + ':' + 'senha9' + '@' + 'localhost:5432/db'
                  for esquema in ('postgres', 'mysql', 'mongodb', 'redis', 'amqp', 'https', 'postgresql',
                                  'git' + '+https', 'postgresql' + '+psycopg2', 'mysql' + '+pymysql',
                                  'mongodb' + '+srv', 'HTTPS', 'ftp', 'git' + '+ssh', 'jdbc:' + 'postgresql')]
        casos += ['postgres' + '://' + 'app' + ':' + '%21Real9pass' + '@' + 'localhost/db',
                  'postgres' + '://' + 'app' + ':' + '$x7Kp9qLm' + '@' + 'localhost/db',
                  'postgres' + '://' + 'app' + ':' + 'Real9' + '${X}' + '@' + 'localhost/db']
        casos += ['redis' + '://' + ':' + 'senha9' + '@' + 'localhost:6379',
                  'postgres' + '://' + '<usuario>' + ':' + 'senha9' + '@' + 'host/db',
                  'https' + '://' + 'user' + ':' + 'pass' + '@' + 'host']
        self.assertEqual(len(letras_digitos), 33)
        self.assertEqual(len(corpo + 'ghij'), 16)
        for caso in casos:
            with self.subTest(caso=caso):
                self.setUp()
                self.assertEqual(self.linha(f'valor {caso} fim'), [('doc.md', 'segredo')])

    def test_o_que_nao_e_segredo_passa(self):
        sha40 = hashlib.sha1(b'commit').hexdigest()
        self.assertRegex(sha40, r'[a-f]')
        self.assertRegex(sha40, r'[0-9]')
        casos = [sha40[:7], sha40, 'abcdef' * 6, 'Bear' + 'er ' + 'abcdef' * 6,
                 'docs/superpowers/plans/2026-11-23-' + 'retrofit-watch-modo-autonomo.md',
                 'Bas' + 'ic authentication', 'task' + '-planning', 'xxx-' + 'sk' + '-' + 'abcd1234efgh',
                 'ma' + 'sk' + '-' + 'abcd1234efgh',
                 'Bear' + 'er ' + 'a1b2c3d4e5f6g7h', '1' * 33, 'x' + 'Bear' + 'er ' + 'a1b2c3d4e5f6g7h8',
                 'postgres' + '://localhost/db', 'https' + '://example.com/x',
                 'postgres' + '://' + '<user>' + ':' + '<password>' + '@' + 'host/db',
                 'redis' + '://' + ':' + '${REDIS_PASSWORD}' + '@' + 'host',
                 'redis' + '://' + ':' + '$REDIS_PASSWORD' + '@' + 'db.exemplo.org:6379',
                 'postgres' + '://' + 'app' + ':' + '%DB_PASS%' + '@' + 'host/db',
                 'postgres' + '://' + 'app' + ':' + '{senha}' + '@' + 'host/db']
        self.assertEqual(len('a1b2c3d4e5f6g7h'), 15)
        for caso in casos:
            with self.subTest(caso=caso):
                self.setUp()
                self.assertEqual(self.linha(f'valor {caso} fim'), [])

    def test_a_lista_de_hashes_e_isenta_so_de_segredo(self):
        lista = 'scripts/private-names.sha256'
        self.base({lista: '# cabecalho\n'})
        self.commit({lista: f'# cabecalho\n{hashlib.sha256(b"y").hexdigest()}\n{EMAIL}\n'})
        self.assertEqual(self.tipos(), [(lista, 'email')])


class DiffBlindado(Base):
    """Nem uma linha de conteúdo, nem o ramo (atributo), nem o ambiente ou a config mudam o que a camada 1 lê."""

    def config(self, *pares):
        for chave, valor in pares:
            self.git('config', chave, valor)

    def test_linha_de_conteudo_com_mais_mais_nao_vira_cabecalho(self):
        token = 'a1' * 21
        for primeira, segunda, esperado in (
                ('++ ' + '/dev/null', f'fale com {EMAIL}', [('doc.md', 3, 'email')]),
                ('++ ' + 'b/scripts/private-names.sha256', f'valor {token}', [('doc.md', 3, 'segredo')]),
                ('++ ' + EMAIL, 'limpo', [('doc.md', 2, 'email')])):
            with self.subTest(primeira=primeira):
                self.setUp()
                self.base({'doc.md': 'um\n'})
                self.commit({'doc.md': f'um\n{primeira}\n{segunda}\n'})
                self.assertEqual([a[:3] for a in self.camada1()], esperado)

    def test_atributo_do_ramo_nao_cega(self):
        for atributo in ('*.md -diff', '*.md binary'):
            with self.subTest(atributo=atributo):
                self.setUp()
                self.base({'doc.md': 'um\n'})
                self.commit({'.gitattributes': atributo + '\n', 'doc.md': f'um\nfale com {EMAIL}\n'})
                self.assertEqual([a[:3] for a in self.camada1()], [('doc.md', 2, 'email')])

    def test_textconv_nao_cega(self):
        self.config(('diff.conv.textconv', 'true'))
        self.base({'doc.md': 'um\n'})
        self.commit({'.gitattributes': '*.md diff=conv\n', 'doc.md': f'um\nfale com {EMAIL}\n'})
        self.assertEqual([a[:3] for a in self.camada1()], [('doc.md', 2, 'email')])

    def test_diff_externo_nao_cega(self):
        self.base({'doc.md': 'um\n'})
        self.commit({'doc.md': f'um\nfale com {EMAIL}\n'})
        self.config(('diff.external', 'true'))
        self.assertEqual([a[:3] for a in self.camada1()], [('doc.md', 2, 'email')])
        self.git('config', '--unset', 'diff.external')
        self.env['GIT_EXTERNAL_DIFF'] = 'true'
        r = subprocess.run([sys.executable, str(SCRIPT), '--camada1', '--base', 'base', '--repo', str(self.repo)],
                           capture_output=True, text=True, encoding='utf-8', errors='replace', env=self.env)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn('doc.md:2: email "', r.stdout)

    def test_prefixo_da_config_nao_muda_o_caminho(self):
        self.config(('diff.noprefix', 'true'))
        self.base({'outro.md': 'um\n'})
        self.commit({'b/doc.md': f'fale com {EMAIL}\n'})
        self.assertEqual([a[:3] for a in self.camada1()], [('b/doc.md', 1, 'email')])

    def test_cor_da_config_nao_cega(self):
        self.config(('color.diff', 'always'), ('color.ui', 'always'))
        self.base({'doc.md': 'um\n'})
        self.commit({'doc.md': f'um\nfale com {EMAIL}\n'})
        self.assertEqual([a[:3] for a in self.camada1()], [('doc.md', 2, 'email')])

    def _duas_mudancas_longe(self):
        self.base({'doc.md': 'a\nb\nc\nd\ne\n'})
        self.commit({'doc.md': f'x\nb\nc\nd\nfale com {EMAIL}\n'})

    def test_inter_hunk_context_da_config_nao_muda_a_linha(self):
        self.config(('diff.interHunkContext', '5'))
        self._duas_mudancas_longe()
        self.assertEqual([a[:3] for a in self.camada1()], [('doc.md', 5, 'email')])

    def test_git_diff_opts_do_ambiente_nao_muda_a_linha(self):
        self._duas_mudancas_longe()
        with unittest.mock.patch.dict(os.environ, {'GIT_DIFF_OPTS': '-u5'}):
            self.assertEqual([a[:3] for a in self.camada1()], [('doc.md', 5, 'email')])

    def test_repositorio_do_ambiente_nao_desvia_o_repo(self):
        self.base({'doc.md': 'um\n'})
        self.commit({'doc.md': f'um\nfale com {EMAIL}\n'})
        limpo = self.dir / 'limpo'
        limpo.mkdir()
        subprocess.run(['git', '-C', str(limpo), 'init', '-q'], check=True, env=self.env)
        subprocess.run(['git', '-C', str(limpo), 'commit', '-q', '--allow-empty', '-m', 'base'], check=True, env=self.env)
        subprocess.run(['git', '-C', str(limpo), 'branch', 'base'], check=True, env=self.env)
        desvio = {'GIT_DIR': str(limpo / '.git'), 'GIT_WORK_TREE': str(limpo)}
        with unittest.mock.patch.dict(os.environ, desvio):
            self.assertEqual([a[:3] for a in self.camada1()], [('doc.md', 2, 'email')])

    def test_diff_relative_da_config_nao_cega(self):
        self.config(('diff.relative', 'true'))
        rel = f'notas/{NOME}.md'
        self.base({'sub/um.md': 'um\n'})
        self.commit({rel: f'fale com {EMAIL}\n'})
        achados = ag.camada1(self.repo / 'sub', 'base', hashes=self.hashes, publicos=set())
        self.assertEqual([a[:3] for a in achados], [(rel, 0, 'lista'), (rel, 1, 'email')])


class ListasReais(unittest.TestCase):
    def test_as_listas_reais_nao_se_cruzam(self):
        publicos = ag.carregar_publicos()
        hashes = cpn.carregar()
        self.assertGreaterEqual(len(publicos), 5)
        self.assertIn('j0ruge', publicos)
        self.assertEqual({p for p in publicos if cpn._resumo(p) in hashes}, set())

    def test_lista_de_publicos_ausente_e_vazia(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(ag.carregar_publicos(Path(tmp) / 'nada.txt'), set())


class LinhaDeComando(Base):
    def rodar(self, *args, script=SCRIPT):
        return subprocess.run([sys.executable, str(script), *args], capture_output=True, text=True,
                              encoding='utf-8', errors='replace', env=self.env)

    def copia(self, com_lista, nome='copia'):
        pasta = self.dir / nome / 'scripts'
        pasta.mkdir(parents=True)
        for nome in ('anonymity-gate.py', 'check-private-names.py'):
            shutil.copy(RAIZ / 'scripts' / nome, pasta)
        if com_lista:
            (pasta / 'private-names.sha256').write_text(cpn.CABECALHO + cpn.resumo(NOME) + '\n', encoding='utf-8')
        return pasta

    def test_linha_de_comando(self):
        self.base({'doc.md': 'um\n'})
        self.commit({'doc.md': 'um\nlimpo\n'})
        r = self.rodar('--camada1', '--base', 'base', '--repo', str(self.repo))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.commit({'doc.md': f'um\nlimpo\n{EMAIL}\n'})
        r = self.rodar('--camada1', '--base', 'base', '--repo', str(self.repo))
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn('doc.md:3: email "', r.stdout)
        pasta = self.copia(com_lista=False)
        r = self.rodar('--camada1', '--base', 'base', '--repo', str(self.repo), script=pasta / 'anonymity-gate.py')
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn('lista inutilizavel', r.stdout)

    def test_sem_git_sai_2_com_mensagem(self):
        self.commit({'doc.md': 'limpo\n'})
        vazio = self.dir / 'sem-git'
        vazio.mkdir()
        self.env['PATH'] = str(vazio)
        r = self.rodar('--camada1', '--base', 'base', '--repo', str(self.repo))
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn('git nao encontrado', r.stdout)
        self.assertNotIn('Traceback', r.stderr)

    def test_publicos_fora_de_utf8_sai_2_com_mensagem(self):
        self.commit({'doc.md': 'limpo\n'})
        pasta = self.copia(com_lista=True)
        (pasta / 'public-names.txt').write_bytes(b'nome \xe7\xe3o\n')
        r = self.rodar('--camada1', '--base', 'base', '--repo', str(self.repo), script=pasta / 'anonymity-gate.py')
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn('lista inutilizavel', r.stdout)
        self.assertNotIn('Traceback', r.stderr)

    def test_mensagem_de_erro_e_ascii(self):
        self.commit({'doc.md': 'limpo\n'})
        pasta = self.copia(com_lista=False, nome='cópia')
        r = self.rodar('--camada1', '--base', 'base', '--repo', str(self.repo), script=pasta / 'anonymity-gate.py')
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn('lista inutilizavel', r.stdout)
        self.assertTrue(r.stdout.isascii(), r.stdout)

    def test_extra_da_linha_de_comando(self):
        nome = 'cafe' + '_tutor'
        extra = self.dir / 'extra.txt'
        extra.write_text(f'# colheita\n\n{nome}\n', encoding='utf-8')
        self.commit({'doc.md': f'no {nome}\n'})
        r = self.rodar('--camada1', '--base', 'base', '--repo', str(self.repo), '--extra', str(extra))
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn(f'doc.md:1: colheita "{nome}"', r.stdout)

    def test_publico_add_recusa_nome_privado(self):
        pasta = self.copia(com_lista=True)
        publicos = pasta / 'public-names.txt'
        publicos.write_text(ag.CABECALHO_PUBLICOS + 'j0ruge\n', encoding='utf-8')
        antes = publicos.read_bytes()
        r = self.rodar('--publico-add', NOME.upper(), script=pasta / 'anonymity-gate.py')
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertEqual(publicos.read_bytes(), antes)
        r = self.rodar('--publico-add', 'outro' + '-nome', script=pasta / 'anonymity-gate.py')
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn('outro' + '-nome', publicos.read_text(encoding='utf-8').splitlines())
        r = self.rodar('--publico-remove', 'Outro' + '_Nome', script=pasta / 'anonymity-gate.py')
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(publicos.read_bytes(), antes)


if __name__ == '__main__':
    unittest.main()
