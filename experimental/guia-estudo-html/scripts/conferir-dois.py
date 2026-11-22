#!/usr/bin/env python3
"""Confere cada DOI de um arquivo Markdown contra a API do Crossref.

Uso: python3 conferir-dois.py <arquivo.md>
Saida: uma linha por DOI, "OK <doi> <titulo>" ou "FALHA <doi> <motivo>".
rc 0 com todos OK, 1 com alguma FALHA, 2 sem argumento ou sem rede.
Nao envia e-mail nem dado pessoal; so o User-Agent fixo.
"""
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

DOI = re.compile(r'10\.\d{4,9}/[^\s;,)\]]+')
UA = 'guia-estudo-html/1'


def limpar(doi):
    return doi.rstrip('.*_`\'"')


def consultar(doi):
    url = 'https://api.crossref.org/works/' + urllib.parse.quote(doi, safe='/')
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)['message']


def main(argv):
    if len(argv) != 2:
        print('uso: conferir-dois.py <arquivo.md>', file=sys.stderr)
        return 2
    texto = Path(argv[1]).read_text(encoding='utf-8')
    dois = []
    for d in DOI.findall(texto):
        d = limpar(d)
        if d not in dois:
            dois.append(d)
    falhou = False
    for doi in dois:
        try:
            msg = consultar(doi)
            titulo = ' '.join(msg.get('title') or ['(sem titulo)'])
            print(f'OK {doi} {titulo}')
        except urllib.error.HTTPError as e:
            print(f'FALHA {doi} {e.code}')
            falhou = True
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            print(f'sem rede: {e}', file=sys.stderr)
            return 2
    return 1 if falhou else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
