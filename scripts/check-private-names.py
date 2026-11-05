#!/usr/bin/env python3
"""Reprova nome privado em qualquer arquivo da loja: repositório, empresa ou pessoa que não é pública.

A loja é pública, e as lições nascem de sessões em projetos reais: sem um sensor, o nome volta a cada
retrofit. A regra: se o nome não é necessário, ele sai; se a frase depende dele, entra um termo
genérico (um projeto, outro repo, <repo>). Data, número de PR e hash ficam, porque são a evidência.

A lista guarda hashes, não nomes: em texto puro, ela publicaria o que protege. Hash não é cofre, pois
confirma um palpite e quebra nome curto, mas não entrega a lista a quem só lê a árvore.

O nome é comparado por palavras, sem caixa e sem separador: a mesma entrada pega as grafias com _, - e .,
com prefixo e sufixo, e nunca um pedaço de outra palavra. A forma com espaço só vale se estiver na lista.

Uso (da raiz ou de qualquer pasta):
  python3 scripts/check-private-names.py                varre a loja; rc 0 limpa, 1 com achados, 2 sem lista
  python3 scripts/check-private-names.py --add NOME     acrescenta o nome à lista
  python3 scripts/check-private-names.py --remove NOME  tira o nome da lista (coincidência com palavra comum)
"""
import functools
import hashlib
import re
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
LISTA = Path(__file__).with_name('private-names.sha256')
SAL = b'chewiesoft-marketplace/private-names/v1:'
CABECALHO = '# Hashes, nao nomes. Para mudar: python3 scripts/check-private-names.py --add|--remove NOME\n'
PALAVRA = re.compile(r'[^\W_]+')
SEPARADORES = {'_', '-', '.'}
MAX_PARTES = 6
PULAR = {'.git', '__pycache__', 'node_modules'}
REGRA = ('se o nome nao e necessario, tire; se a frase depende dele, use um termo generico '
         '(um projeto, outro repo, <repo>). Coincidencia com palavra comum: --remove NOME')


def chave(nome):
    """Forma normalizada do nome: 'Foo_Bar' e 'foo-bar' dão 'foobar'; com espaço, é a forma de prosa, 'foo bar'."""
    palavras = PALAVRA.findall(nome.lower())
    return ' '.join(palavras) if ' ' in nome.strip() else ''.join(palavras)


@functools.lru_cache(maxsize=None)
def _resumo(texto):
    return hashlib.sha256(SAL + texto.encode('utf-8')).hexdigest()


def resumo(nome):
    """O hash que a lista guarda para este nome."""
    return _resumo(chave(nome))


def carregar(lista=LISTA):
    """Lê a lista e devolve os hashes. Lista ausente ou vazia é erro: um sensor sem lista aprovaria tudo."""
    linhas = [l.strip() for l in Path(lista).read_text(encoding='utf-8').splitlines()]
    hashes = {l for l in linhas if l and not l.startswith('#')}
    invalidas = [h for h in hashes if not re.fullmatch(r'[0-9a-f]{64}', h)]
    if invalidas:
        raise ValueError(f'{lista}: {len(invalidas)} linha(s) fora do formato de hash')
    if not hashes:
        raise ValueError(f'{lista}: lista vazia')
    return hashes


def candidatos(linha):
    """Cada palavra e cada sequência ligada por _, - ou ., e cada par ligado por um espaço: (trecho, forma normalizada)."""
    baixa = linha.lower()
    palavras = list(PALAVRA.finditer(baixa))
    for i, atual in enumerate(palavras):
        junto = atual.group()
        yield junto, junto
        for j in range(i + 1, min(i + MAX_PARTES, len(palavras))):
            if baixa[palavras[j - 1].end():palavras[j].start()] not in SEPARADORES:
                break
            junto += palavras[j].group()
            yield baixa[atual.start():palavras[j].end()], junto
        if i + 1 < len(palavras) and baixa[atual.end():palavras[i + 1].start()] == ' ':
            yield baixa[atual.start():palavras[i + 1].end()], f'{atual.group()} {palavras[i + 1].group()}'


def arquivos(raiz):
    """Os arquivos da árvore: num checkout, o que o git rastreia ou rastrearia; fora dele, tudo menos o que é gerado."""
    raiz = Path(raiz)
    if (raiz / '.git').exists():
        saida = subprocess.run(['git', '-C', str(raiz), 'ls-files', '-c', '-o', '--exclude-standard', '-z'],
                               capture_output=True, check=True).stdout
        return [r for r in saida.decode('utf-8', 'surrogateescape').split('\0') if r]
    return [p.relative_to(raiz).as_posix() for p in sorted(raiz.rglob('*'))
            if p.is_file() and not PULAR & set(p.relative_to(raiz).parts)]


def varrer(raiz, hashes):
    """[(caminho relativo, linha, trecho)] de cada ocorrência; a linha 0 é o próprio caminho. Binário só tem o caminho varrido."""
    achados = []
    for rel in arquivos(raiz):
        try:
            dados = (Path(raiz) / rel).read_bytes()
        except OSError:
            continue
        linhas = [(0, rel)]
        if b'\0' not in dados:
            linhas += list(enumerate(dados.decode('utf-8', 'replace').splitlines(), start=1))
        for numero, linha in linhas:
            for trecho, forma in candidatos(linha):
                if _resumo(forma) in hashes:
                    achados.append((rel, numero, trecho))
    return achados


def _mudar(argumento, nome, lista=LISTA):
    hashes = set(carregar(lista)) if Path(lista).is_file() else set()
    alvo = resumo(nome)
    if argumento == '--add':
        hashes.add(alvo)
    elif alvo in hashes:
        hashes.remove(alvo)
    else:
        print('esse nome nao esta na lista')
        return 1
    Path(lista).write_text(CABECALHO + ''.join(h + '\n' for h in sorted(hashes)), encoding='utf-8', newline='\n')
    print(f'{len(hashes)} nomes na lista')
    return 0


def main(argv=None):
    """Varre a loja, ou muda a lista com --add e --remove."""
    argv = sys.argv[1:] if argv is None else argv
    if argv and argv[0] in ('--add', '--remove'):
        if len(argv) != 2:
            print(__doc__)
            return 2
        return _mudar(argv[0], argv[1])
    if argv:
        print(__doc__)
        return 2
    try:
        hashes = carregar()
    except (OSError, ValueError) as exc:
        print(f'lista de nomes privados inutilizavel: {exc}')
        return 2
    achados = varrer(RAIZ, hashes)
    for rel, numero, trecho in achados:
        print(f'{rel}:{numero}: nome privado "{ascii(trecho)[1:-1]}"')
    if achados:
        print(f'\n{len(achados)} achado(s). {REGRA}')
        return 1
    print(f'ok: nenhum dos {len(hashes)} nomes na arvore')
    return 0


if __name__ == '__main__':
    sys.exit(main())
