#!/usr/bin/env python3
"""Portão de anonimização, camada 1: reprova nome, e-mail, caminho com usuário e segredo no que um ramo acrescenta.

A camada 1 é mecânica e não hesita. Ela olha só o que é novo: as linhas acrescentadas do diff, o caminho
de cada arquivo novo (linha 0) e as mensagens dos commits. A árvore inteira tem palavra comum que
coincide com nome local (Files, Users, System); o que é novo não tem desculpa.

Tipos de achado:
  lista     forma candidata cujo hash está em scripts/private-names.sha256
  colheita  forma candidata igual a um termo de --extra (um por linha, # comenta); quem quebra o termo
            em pedaços é a colheita, não este script
  email     endereço com @ e domínio com ponto
  caminho   /home/<u>, /Users/<u>, <letra>:\\Users\\<u> (sem caixa, com a barra escapada ou não),
            /mnt/<x>/<pasta>; isento o segmento que começa com <, $, % ou {
  segredo   os prefixos de credencial do criteria.md, connection string com usuário e senha antes do @,
            e sequência alfanumérica de 32 ou mais com letra e dígito (hexadecimal de 40 passa: é sha
            de commit)

A lista de públicos (scripts/public-names.txt) isenta lista, colheita, email e o segmento de caminho.
Nunca isenta segredo. O arquivo private-names.sha256 é isento só de segredo, porque é feito de hashes.

Uso (da raiz ou de qualquer pasta):
  python3 scripts/anonymity-gate.py --camada1 --base REF [--repo DIR] [--extra ARQUIVO]
      rc 0 limpa, 1 com achados, 2 uso ou lista inutilizável
  python3 scripts/anonymity-gate.py --publico-add NOME     rc 1 se o nome está na lista de hashes
  python3 scripts/anonymity-gate.py --publico-remove NOME  rc 1 se o nome não está nos públicos
"""
import argparse
import importlib.util
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

_spec = importlib.util.spec_from_file_location('check_private_names',
                                               Path(__file__).with_name('check-private-names.py'))
cpn = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cpn)

PUBLICOS = Path(__file__).with_name('public-names.txt')
CABECALHO_PUBLICOS = ('# Nomes publicos, em texto puro: isentam a camada 1 (nunca de segredo). '
                      'Para mudar: python3 scripts/anonymity-gate.py --publico-add|--publico-remove NOME\n')
MENSAGEM = '<mensagem>'
ISENTO_DE_SEGREDO = 'scripts/private-names.sha256'

EMAIL = re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+')
_SEGMENTO = r'([^/\\\s"\'`)\]]+)'
CAMINHOS = [
    re.compile(r'(?<![\w.])/home/' + _SEGMENTO),
    re.compile(r'(?<![\w.])/Users/' + _SEGMENTO),
    re.compile(r'(?<![A-Za-z])[A-Za-z]:\\+[Uu][Ss][Ee][Rr][Ss]\\+' + _SEGMENTO),
    re.compile(r'(?<![A-Za-z])[A-Za-z]:/+[Uu][Ss][Ee][Rr][Ss]/+' + _SEGMENTO),
    re.compile(r'(?<![\w.])/mnt/[^/\s]+/' + _SEGMENTO),
]
PLACEHOLDER = ('<', '$', '%', '{')
_FRONTEIRA = r'(?<![A-Za-z0-9_-])'
PREFIXOS = re.compile(_FRONTEIRA + r'(?:sk-|ghp_|xox[bpars]-|AKIA)[A-Za-z0-9_-]{8,}')
CABECALHO_HTTP = re.compile(_FRONTEIRA + r'(?:Bearer|Basic) (\S{16,})')
# Qualquer esquema, sem lista e sem caixa (HTTPS, ftp, git+ssh, o postgresql de jdbc:postgresql, sufixo de
# driver), seguido de usuário e senha antes do @. O usuário pode ser vazio, só a senha entre os dois-pontos
# e o @ (a forma usual do redis). Grupo 1: usuário; grupo 2: senha.
CONEXAO = re.compile(r'(?<![A-Za-z0-9+.-])[A-Za-z][A-Za-z0-9+.-]*://([^\s/:@]*):([^\s/@]+)@')
# Senha de modelo, nas formas estreitas: <...>, ${...}, {...}, $NOME em maiúsculas e %NOME%. Uma senha que só
# começa com $ ou % (%21abc, $x7Kp) é literal.
SENHA_MODELO = re.compile(r'<[^>]*>|\$\{[^}]*\}|\{[^}]*\}|\$[A-Z_][A-Z0-9_]*|%[A-Za-z_][A-Za-z0-9_]*%')
LONGA = re.compile(r'(?<![A-Za-z0-9])[A-Za-z0-9]{32,}(?![A-Za-z0-9])')
SHA_DE_COMMIT = re.compile(r'[0-9a-fA-F]{40}')


def carregar_publicos(lista=PUBLICOS):
    """As formas normalizadas da lista de públicos. Arquivo ausente dá conjunto vazio: sem lista, nada é isento."""
    try:
        linhas = Path(lista).read_text(encoding='utf-8').splitlines()
    except FileNotFoundError:
        return set()
    return {cpn.chave(l.strip()) for l in linhas if l.strip() and not l.strip().startswith('#')}


# Variáveis que mudam o que o git lê: GIT_DIFF_OPTS passa por cima do -U0, e as de repositório (que um hook
# do git herda) passam por cima do -C repo.
AMBIENTE_FORA = frozenset({'GIT_DIFF_OPTS', 'GIT_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE', 'GIT_OBJECT_DIRECTORY',
                           'GIT_ALTERNATE_OBJECT_DIRECTORIES', 'GIT_COMMON_DIR'})


def _git(repo, *args):
    git = shutil.which('git')
    if git is None:
        raise FileNotFoundError('git nao encontrado no PATH')
    env = {k: v for k, v in os.environ.items() if k not in AMBIENTE_FORA}
    return subprocess.run([git, '-C', str(repo), *args], capture_output=True, check=True,
                          env=env).stdout.decode('utf-8', 'replace')


def _dizer(texto):
    """Imprime em ASCII: o stdout do Windows é cp1252, e uma mensagem de erro com acento não pode derrubar o portão."""
    print(texto.encode('ascii', 'backslashreplace').decode('ascii'))


_ESCAPES = {'a': 7, 'b': 8, 't': 9, 'n': 10, 'v': 11, 'f': 12, 'r': 13, '"': 34, '\\': 92}


def _descitar(citado):
    """O nome que o git escreveu entre aspas, no estilo C (\\t, \\", \\303...), de volta ao texto."""
    corpo, saida, i = citado[1:-1], bytearray(), 0
    while i < len(corpo):
        c = corpo[i]
        if c != '\\':
            saida += c.encode('utf-8')
            i += 1
        elif corpo[i + 1:i + 2] in _ESCAPES:
            saida.append(_ESCAPES[corpo[i + 1]])
            i += 2
        elif re.fullmatch(r'[0-7]{3}', corpo[i + 1:i + 4]):
            saida.append(int(corpo[i + 1:i + 4], 8))
            i += 4
        else:
            raise ValueError(citado)
    return saida.decode('utf-8', 'replace')


def _destino(alvo):
    """O caminho de um cabeçalho '+++'. Nome citado ou estranho nunca faz a linha ser pulada: só /dev/null é pulado."""
    if alvo == '/dev/null':
        return None
    if alvo.startswith('"') and alvo.endswith('"') and len(alvo) > 1:
        try:
            alvo = _descitar(alvo)
        except (ValueError, IndexError):
            return alvo
    else:
        alvo = alvo.rstrip('\t')  # o git põe um tab depois de nome com espaço
    return alvo[2:] if alvo.startswith('b/') else alvo


def linhas_novas(repo, base):
    """[(onde, linha, texto)]: as linhas acrescentadas desde a base, o caminho de cada arquivo novo e as mensagens."""
    novas = []
    for rel in _git(repo, '-c', 'core.quotePath=false', 'diff', '--no-renames', '--no-relative', '--name-only',
                    '--diff-filter=A', '-z', f'{base}...HEAD').split('\0'):
        if rel:
            novas.append((rel, 0, rel))
    onde, numero, em_cabecalho = None, 0, False
    # quotePath=false de propósito, como defesa em profundidade: o _destino já desfaz o nome citado.
    # As outras flags tiram do alcance do ramo e do ambiente o que muda a saída: atributo (-diff, binary,
    # textconv), diff externo, prefixo, cor, diff.relative e diff.interHunkContext (linha de contexto entre
    # hunks não conta no número da linha).
    diff = _git(repo, '-c', 'core.quotePath=false', 'diff', '-U0', '--no-renames', '--text', '--no-ext-diff',
                '--no-textconv', '--src-prefix=a/', '--dst-prefix=b/', '--no-color', '--no-relative',
                '--inter-hunk-context=0',
                f'{base}...HEAD')
    for linha in diff.split('\n'):
        if linha.startswith('diff --git '):
            onde, em_cabecalho = None, True
        elif em_cabecalho and linha.startswith('+++ '):
            onde = _destino(linha[4:])
        elif linha.startswith('@@'):
            em_cabecalho = False
            m = re.match(r'@@ -\S+ \+(\d+)', linha)
            numero = int(m.group(1)) if m else 0
        elif linha.startswith('+') and onde is not None:
            novas.append((onde, numero, linha[1:]))
            numero += 1
    for mensagem in _git(repo, 'log', '-z', '--format=%B', f'{base}..HEAD').split('\0'):
        for i, texto in enumerate(mensagem.splitlines(), start=1):
            novas.append((MENSAGEM, i, texto))
    return novas


def _conexoes(texto):
    """[(span, isenta)] de cada connection string com credencial. É isenta a de modelo (SENHA_MODELO).

    Só a senha decide: um usuário de modelo com a senha literal (<usuario>:hunter2@) continua achado.
    """
    return [(m.span(), bool(SENHA_MODELO.fullmatch(m.group(2)))) for m in CONEXAO.finditer(texto)]


def _segredos(texto):
    """Os trechos com forma de segredo. Uma sequência longa dentro de um prefixo já achado não conta de novo."""
    achados = [m.span() for m in PREFIXOS.finditer(texto)]
    achados += [span for span, isenta in _conexoes(texto) if not isenta]
    for m in CABECALHO_HTTP.finditer(texto):
        if re.search(r'[0-9]', m.group(1)):
            achados.append(m.span())
    for m in LONGA.finditer(texto):
        trecho = m.group()
        if not (re.search(r'[A-Za-z]', trecho) and re.search(r'[0-9]', trecho)):
            continue
        if len(trecho) == 40 and SHA_DE_COMMIT.fullmatch(trecho):
            continue
        if any(a <= m.start() < b for a, b in achados):
            continue
        achados.append(m.span())
    return [texto[a:b] for a, b in sorted(achados)]


def _achados_da_linha(onde, texto, hashes, extras, publicos):
    achados = []
    for trecho, forma in cpn.candidatos(texto):
        if forma in publicos:
            continue
        if cpn._resumo(forma) in hashes:
            achados.append(('lista', trecho))
        elif forma in extras:
            achados.append(('colheita', trecho))
    # O '$SENHA@host.com' de um modelo de conexão não é endereço: o modelo vira espaço antes de buscar o e-mail,
    # e um endereço real logo depois dele continua inteiro.
    sem_modelos = texto
    for (a, b), isenta in _conexoes(texto):
        if isenta:
            sem_modelos = sem_modelos[:a] + ' ' * (b - a) + sem_modelos[b:]
    for m in EMAIL.finditer(sem_modelos):
        if cpn.chave(m.group()) not in publicos:
            achados.append(('email', m.group()))
    vistos = []
    for padrao in CAMINHOS:
        for m in padrao.finditer(texto):
            segmento = m.group(1)
            if segmento.startswith(PLACEHOLDER) or cpn.chave(segmento) in publicos:
                continue
            if any(a < m.end() and m.start() < b for a, b in vistos):
                continue  # C:/Users/<u> casa com duas formas: um achado só
            vistos.append(m.span())
            achados.append(('caminho', m.group()))
    if onde != ISENTO_DE_SEGREDO:
        achados += [('segredo', s) for s in _segredos(texto)]
    return achados


def camada1(repo, base, extras=frozenset(), hashes=None, publicos=None):
    """[(onde, linha, tipo, trecho)] de cada achado nas linhas novas desde a base."""
    hashes = cpn.carregar() if hashes is None else hashes
    publicos = carregar_publicos() if publicos is None else publicos
    extras = {cpn.chave(e) for e in extras if cpn.chave(e)}
    achados = []
    for onde, numero, texto in linhas_novas(repo, base):
        for tipo, trecho in _achados_da_linha(onde, texto, hashes, extras, publicos):
            achados.append((onde, numero, tipo, trecho))
    return achados


def _ler_extra(arquivo):
    linhas = [l.strip() for l in Path(arquivo).read_text(encoding='utf-8').splitlines()]
    return {l for l in linhas if l and not l.startswith('#')}


def publico_mudar(argumento, nome, publicos=PUBLICOS, lista=cpn.LISTA):
    """Acrescenta ou tira um nome dos públicos. Um nome da lista de hashes nunca vira público por aqui."""
    alvo = cpn.chave(nome)
    caminho = Path(publicos)
    linhas = [l.strip() for l in caminho.read_text(encoding='utf-8').splitlines()] if caminho.is_file() else []
    nomes = [l for l in linhas if l and not l.startswith('#')]
    if argumento == '--publico-add':
        if cpn._resumo(alvo) in cpn.carregar(lista):
            print('esse nome esta na lista de nomes privados: tire-o de la antes, com check-private-names.py --remove')
            return 1
        if alvo not in {cpn.chave(n) for n in nomes}:
            nomes.append(nome.strip())
    else:
        restantes = [n for n in nomes if cpn.chave(n) != alvo]
        if len(restantes) == len(nomes):
            print('esse nome nao esta na lista de publicos')
            return 1
        nomes = restantes
    caminho.write_text(CABECALHO_PUBLICOS + ''.join(n + '\n' for n in sorted(nomes, key=str.lower)),
                       encoding='utf-8', newline='\n')
    print(f'{len(nomes)} nomes publicos')
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    modo = parser.add_mutually_exclusive_group(required=True)
    modo.add_argument('--camada1', action='store_true')
    modo.add_argument('--publico-add', metavar='NOME')
    modo.add_argument('--publico-remove', metavar='NOME')
    parser.add_argument('--base')
    parser.add_argument('--repo', default='.')
    parser.add_argument('--extra', action='append', default=[], metavar='ARQUIVO')
    args = parser.parse_args(argv)
    try:
        if args.publico_add is not None:
            return publico_mudar('--publico-add', args.publico_add)
        if args.publico_remove is not None:
            return publico_mudar('--publico-remove', args.publico_remove)
        if not args.base:
            parser.print_usage()
            print('--camada1 exige --base REF')
            return 2
        hashes = cpn.carregar()
        publicos = carregar_publicos()
        extras = set().union(*(_ler_extra(a) for a in args.extra)) if args.extra else set()
    except (OSError, ValueError) as exc:
        _dizer(f'lista inutilizavel: {exc}')
        return 2
    try:
        achados = camada1(args.repo, args.base, extras=extras, hashes=hashes, publicos=publicos)
    except subprocess.CalledProcessError as exc:
        _dizer(f'git falhou: {exc.stderr.decode("utf-8", "replace").strip()}')
        return 2
    except OSError as exc:
        _dizer(f'git inutilizavel: {exc}')
        return 2
    for onde, numero, tipo, trecho in achados:
        print(f'{ascii(onde)[1:-1]}:{numero}: {tipo} "{ascii(trecho)[1:-1]}"')
    if achados:
        print(f'\n{len(achados)} achado(s) na camada 1')
        return 1
    print('ok: camada 1 limpa')
    return 0


if __name__ == '__main__':
    sys.exit(main())
