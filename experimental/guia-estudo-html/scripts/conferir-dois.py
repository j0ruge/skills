#!/usr/bin/env python3
"""Confere cada DOI de um arquivo Markdown contra a API do Crossref.

Uso: python3 conferir-dois.py <arquivo.md>
Saida: uma linha por DOI, "OK <doi> <titulo>" ou "FALHA <doi> <motivo>".
rc 0 com todos OK, 1 com alguma FALHA, 2 sem argumento, sem rede ou com o Crossref fora do ar
(429 e 5xx: o script tenta de novo uma vez, e depois sai 2, porque nao diz nada sobre o DOI).
Nao envia e-mail nem dado pessoal; so o User-Agent fixo.
"""
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

# O regex para no primeiro espaco, ';', ',', ')' ou ']'. Por isso um DOI com parenteses dentro, como o
# "10.1002/(SICI)..." de 1990, sai cortado em "10.1002/(SICI": nao ha suporte. Cole esse DOI a mao.
DOI = re.compile(r'10\.\d{4,9}/[^\s;,)\]]+')
UA = 'guia-estudo-html/1'
ESPERA = 3  # segundos antes da segunda tentativa


def limpar(doi):
    # Tira a pontuacao da prosa que o regex leva junto: "doi:10.x/y." ou "10.x/y:" ou "10.x/y-".
    return doi.rstrip('.:-*_`\'"')


def consultar(doi):
    url = 'https://api.crossref.org/works/' + urllib.parse.quote(doi, safe='/')
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    for tentativa in (1, 2):
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                return json.load(r)['message']
        except urllib.error.HTTPError as e:
            # 429 e 5xx dizem que o Crossref esta ocupado, nao que o DOI nao existe.
            if (e.code == 429 or e.code >= 500) and tentativa == 1:
                time.sleep(ESPERA)
                continue
            raise


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
            if e.code == 429 or e.code >= 500:
                print(f'Crossref indisponivel ({e.code}) em {doi}; o DOI nao foi conferido', file=sys.stderr)
                return 2
            print(f'FALHA {doi} {e.code}')
            falhou = True
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            print(f'sem rede: {e}', file=sys.stderr)
            return 2
    return 1 if falhou else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
