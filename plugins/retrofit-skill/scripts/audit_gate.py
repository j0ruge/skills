#!/usr/bin/env python3
"""Compara o baseline com a auditoria depois da edição e lista o que o retrofit precisa responder.

Lê <B>/antes.json, <B>/depois.json (saídas do audit_skill_quality.py com --claims) e <B>/diff.txt
(git diff -U0 da skill). Imprime uma linha por item:
  NOVO / dívida / SUMIU  achados ERRO/AVISO novos, antigos e desaparecidos
  LER                    linhas acrescentadas e removidas por arquivo
  CLAIM                  afirmações com número/data caídas em linha nova
Como responder a cada tipo está no comando, seção "Gate da auditoria".
"""
import argparse, json, re


def ler(b, nome):
    """Devolve o primeiro bloco de skill do JSON da auditoria."""
    return json.load(open(f'{b}/{nome}.json'))['skills'][0]


def linhas_do_diff(caminho):
    """Lê os cabeçalhos @@ de um diff -U0 e devolve (linhas novas por arquivo, removidas por arquivo)."""
    novas, removidas, arq, velho = {}, {}, None, None
    for l in open(caminho, encoding='utf-8'):
        if l.startswith('--- '):
            velho = l[6:].strip() if l.startswith('--- a/') else None
        elif l.startswith('+++ '):
            arq = l[6:].strip() if l.startswith('+++ b/') else velho
        elif l.startswith('@@') and arq:
            m = re.search(r'-\d+(?:,(\d+))? \+(\d+)(?:,(\d+))?', l)
            rem, ini, n = int(m.group(1) or 1), int(m.group(2)), int(m.group(3) or 1)
            novas.setdefault(arq, set()).update(range(ini, ini + n))
            removidas[arq] = removidas.get(arq, 0) + rem
    return novas, removidas


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('B', help='diretório com antes.json, depois.json e diff.txt')
    b = p.parse_args().B
    antes, depois = ler(b, 'antes'), ler(b, 'depois')
    chave = lambda f: (f['level'], f['id'], f['msg'])
    grave = lambda f: f['level'] in ('ERRO', 'AVISO')
    velhos = {chave(f) for f in antes['findings'] if grave(f)}
    atuais = {chave(f) for f in depois['findings'] if grave(f)}
    for k in sorted(atuais):
        print('NOVO     ' if k not in velhos else 'dívida   ', *k)
    for k in sorted(velhos - atuais):
        print('SUMIU    ', *k)
    novas, removidas = linhas_do_diff(f'{b}/diff.txt')
    for a in sorted(set(novas) | set(removidas)):
        print('LER      ', a, f'+{len(novas.get(a, ()))} -{removidas.get(a, 0)} linha(s)')
    for c in depois.get('claims', []):
        if any(a.endswith(c['file']) and c['line'] in ls for a, ls in novas.items()):
            print('CLAIM    ', f"{c['file']}:{c['line']}", c['kind'], '|', c['text'][:90])


if __name__ == '__main__':
    main()
