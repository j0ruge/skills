#!/usr/bin/env python3
"""Confere, no modo completo, que plugin.json, marketplace.json, SKILL.md e README contam a mesma história.

Imprime os VALORES encontrados em vez de só booleanos: um cheque que imprime o que achou deixa o
erro visível mesmo quando a comparação está errada. Rode na raiz do marketplace.
Motivo de cada detalhe: references/armadilhas-medidas.md, seção "Cheque dos quatro lugares".
Plugin com codex em platforms: a seção "Plugin que também vai para o Codex" (§10).
"""
import argparse, glob, io, json, re, subprocess, sys

# Pastas que a coluna "N arquivos de scripts/referências/templates/assets" do
# docs/codex/compatibility.md conta; codex-skills/ é derivado e fica de fora (§10).
RECURSOS = ('/scripts/', '/references/', '/templates/', '/assets/')


def linha_do_plugin(linha, nome):
    """Diz se uma linha de tabela do README pertence ao plugin `nome` (primeira célula)."""
    if not linha.startswith('|'):
        return False
    celula = linha.split('|')[1].strip()
    celula = re.sub(r'^\[|\]\(#[^)]*\)$', '', celula).strip().strip('*')
    return celula == nome


def codex(nome, versao):
    """Catálogo Codex, linha do compatibility.md e smoke de um plugin com codex em platforms."""
    try:
        catalogo = [x['name'] for x in json.load(open('.agents/plugins/marketplace.json'))['plugins']]
        print('no catálogo Codex (.agents/plugins/marketplace.json):', nome in catalogo)
    except (OSError, KeyError, ValueError) as e:
        print('catálogo Codex: não li .agents/plugins/marketplace.json:', e)
    arquivos = subprocess.run(['git', 'ls-files', '--cached', '--others', '--exclude-standard',
                               f'plugins/{nome}'], capture_output=True, text=True, check=True).stdout.split()
    medido = sum(1 for f in arquivos if any(d in f for d in RECURSOS) and '/codex-skills/' not in f)
    linhas = [l for l in io.open('docs/codex/compatibility.md', encoding='utf-8') if l.startswith(f'| {nome} |')]
    for l in linhas:
        n = re.search(r'(\d+) arquivos', l)
        print('compatibility.md:', l.split('|')[2].strip(), '| recursos na linha / medidos:',
              n.group(1) if n else '?', '/', medido)
    if not linhas:
        print('compatibility.md: sem linha para', nome, f'(medidos: {medido})')
    smokes = [r.get('version') for r in json.load(open('docs/codex/smokes.json'))['results']
              if r.get('plugin') == nome]
    print('smoke em docs/codex/smokes.json:', smokes, '— versão do plugin:', versao)


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
    plat = pj.get('platforms'), mk.get('platforms')
    print('platforms plugin.json / marketplace.json:', plat[0], '/', plat[1], '| iguais:', plat[0] == plat[1])
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
    if 'codex' in (plat[0] or []) + (plat[1] or []):
        codex(nome, pj['version'])


if __name__ == '__main__':
    main()
