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
  caminho   /home/<u>, /Users/<u>, <letra>:\\Users\\<u>, /mnt/<x>/<pasta>; isento o segmento que começa
            com <, $, % ou {
  segredo   os prefixos de credencial do criteria.md, e sequência alfanumérica de 32 ou mais com letra e
            dígito (hexadecimal de 40 passa: é sha de commit)

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
import re
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
    re.compile(r'(?<![A-Za-z])[A-Za-z]:\\Users\\' + _SEGMENTO),
    re.compile(r'(?<![\w.])/mnt/[^/\s]+/' + _SEGMENTO),
]
PLACEHOLDER = ('<', '$', '%', '{')
_FRONTEIRA = r'(?<![A-Za-z0-9_-])'
PREFIXOS = re.compile(_FRONTEIRA + r'(?:sk-|ghp_|xox[bpars]-|AKIA)[A-Za-z0-9_-]{8,}')
CABECALHO_HTTP = re.compile(_FRONTEIRA + r'(?:Bearer|Basic) (\S{16,})')
LONGA = re.compile(r'(?<![A-Za-z0-9])[A-Za-z0-9]{32,}(?![A-Za-z0-9])')
SHA_DE_COMMIT = re.compile(r'[0-9a-fA-F]{40}')


def carregar_publicos(lista=PUBLICOS):
    """As formas normalizadas da lista de públicos. Arquivo ausente dá conjunto vazio: sem lista, nada é isento."""
    try:
        linhas = Path(lista).read_text(encoding='utf-8').splitlines()
    except FileNotFoundError:
        return set()
    return {cpn.chave(l.strip()) for l in linhas if l.strip() and not l.strip().startswith('#')}


def _git(repo, *args):
    return subprocess.run(['git', '-C', str(repo), *args], capture_output=True, check=True).stdout.decode('utf-8', 'replace')


def linhas_novas(repo, base):
    """[(onde, linha, texto)]: as linhas acrescentadas desde a base, o caminho de cada arquivo novo e as mensagens."""
    novas = []
    for rel in _git(repo, '-c', 'core.quotePath=false', 'diff', '--no-renames', '--name-only',
                    '--diff-filter=A', '-z', f'{base}...HEAD').split('\0'):
        if rel:
            novas.append((rel, 0, rel))
    onde, numero = None, 0
    diff = _git(repo, '-c', 'core.quotePath=false', 'diff', '-U0', '--no-renames', '--no-color', f'{base}...HEAD')
    for linha in diff.split('\n'):
        if linha.startswith('diff --git '):
            onde = None
        elif linha.startswith('+++ '):
            alvo = linha[4:]
            onde = alvo[2:] if alvo.startswith('b/') else None
        elif linha.startswith('@@'):
            m = re.match(r'@@ -\S+ \+(\d+)', linha)
            numero = int(m.group(1)) if m else 0
        elif linha.startswith('+') and onde is not None:
            novas.append((onde, numero, linha[1:]))
            numero += 1
    for mensagem in _git(repo, 'log', '-z', '--format=%B', f'{base}..HEAD').split('\0'):
        for i, texto in enumerate(mensagem.splitlines(), start=1):
            novas.append((MENSAGEM, i, texto))
    return novas


def _segredos(texto):
    """Os trechos com forma de segredo. Uma sequência longa dentro de um prefixo já achado não conta de novo."""
    achados = [m.span() for m in PREFIXOS.finditer(texto)]
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
    for m in EMAIL.finditer(texto):
        if cpn.chave(m.group()) not in publicos:
            achados.append(('email', m.group()))
    for padrao in CAMINHOS:
        for m in padrao.finditer(texto):
            segmento = m.group(1)
            if segmento.startswith(PLACEHOLDER) or cpn.chave(segmento) in publicos:
                continue
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
        extras = set().union(*(_ler_extra(a) for a in args.extra)) if args.extra else set()
    except (OSError, ValueError) as exc:
        print(f'lista inutilizavel: {exc}')
        return 2
    try:
        achados = camada1(args.repo, args.base, extras=extras, hashes=hashes)
    except subprocess.CalledProcessError as exc:
        print(f'git falhou: {exc.stderr.decode("utf-8", "replace").strip()}')
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
