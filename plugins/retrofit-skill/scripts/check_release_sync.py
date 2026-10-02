#!/usr/bin/env python3
"""Confere, no modo completo, que plugin.json, marketplace.json, SKILL.md e README contam a mesma história.

Imprime os VALORES encontrados em vez de só booleanos: um cheque que imprime o que achou deixa o
erro visível mesmo quando a comparação está errada. Rode na raiz do marketplace.
Motivo de cada detalhe: references/armadilhas-medidas.md, seção "Cheque dos quatro lugares".
"""
import argparse, glob, io, json, re, sys


def linha_do_plugin(linha, nome):
    """Diz se uma linha de tabela do README pertence ao plugin `nome` (primeira célula)."""
    if not linha.startswith('|'):
        return False
    celula = linha.split('|')[1].strip()
    celula = re.sub(r'^\[|\]\(#[^)]*\)$', '', celula).strip().strip('*')
    return celula == nome


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('nome', help='nome do plugin, igual a plugins/<nome>/')
    nome = p.parse_args().nome
    try:
        pj = json.load(open(f'plugins/{nome}/.claude-plugin/plugin.json'))
        mk = {x['name']: x for x in json.load(open('.claude-plugin/marketplace.json'))['plugins']}[nome]
    except (OSError, KeyError) as e:
        sys.exit(f'não achei o plugin {nome!r} ({e}); rode na raiz do marketplace')
    rd = io.open('README.md', encoding='utf-8').read()
    print('description plugin.json == marketplace.json:', pj['description'] == mk['description'])
    print('versão plugin.json / marketplace.json:', pj['version'], '/', mk['version'])
    print('tamanho:', len(pj['description']), '(cap 500)')
    skills = sorted(glob.glob(f'plugins/{nome}/skills/*/SKILL.md'))
    if not skills:
        print('plugin só de comandos — o canônico é o plugin.json, não há SKILL.md')
    for sp in skills:
        sk = io.open(sp, encoding='utf-8').read()
        d = re.search(r'^description:\s*(.*?)(?=\n[A-Za-z0-9_-]+:|\n---)', sk, re.S | re.M).group(1).strip().strip('"')
        print(f'{sp}: igual ao plugin.json?', d == pj['description'], '| len', len(d))
    linhas = [l for l in rd.split('\n') if linha_do_plugin(l, nome)]
    vers = [l.split('|')[2].strip() for l in linhas if l.split('|')[2].strip() not in ('✓', '—')]
    print('versão na linha do README:', vers, '— esperado:', [pj['version']], f'({len(linhas)} linhas)')


if __name__ == '__main__':
    main()
