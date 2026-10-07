#!/usr/bin/env python3
"""Converte o resumo em markdown do `/ticket close` em ADF para o REST do Jira.

Fallback do close step 5 quando não há MCP atlassian (o MCP converte sozinho).
Roda a varredura de marks e estrutura de `references/templates.md` antes de
gravar: ADF malformado volta do Jira como 400 sem dizer o nó.

Uso:
    python3 md2adf.py resumo.md comment.json          # {"body": <doc>}, para POST .../comment
    python3 md2adf.py resumo.md descricao.json --doc  # só o <doc>, para o campo description

Markdown aceito (os nós da tabela ADF do templates.md): títulos `#`..`######`,
parágrafos (linhas seguidas viram um parágrafo), listas `- `/`* ` e `1. `/`1) `
`**negrito**`, `` `code` ``, `[texto](url)`, bloco de código com ``` e linha `---`.
Itálico e tabela não: saem como texto. Duas construções são recusadas porque
chegariam erradas ao Jira (medido em 07/10/2026, no fechamento do SBM-6): lista
aninhada, que virava um nível só, e crase dentro de negrito, que aparecia literal.

Saída: rc 0 gravou; rc 1 a varredura reprovou ou o markdown tem construção
recusada (nada gravado); rc 2 uso inválido.
Só stdlib.
"""
import json
import re
import sys

VALIDAS = {'strong', 'em', 'code', 'link', 'strike', 'underline'}
INLINE = re.compile(r'(\*\*[^*]+\*\*|`[^`]+`|\[[^\]]+\]\([^)\s]+\))')
BULLET = re.compile(r'\s*[-*] (.*)')
ORDERED = re.compile(r'\s*\d+[.)] (.*)')
HEADING = re.compile(r'(#{1,6}) (.*)')
FENCE = re.compile(r'\s*```(.*)')
ANINHADO = re.compile(r'\s+([-*]|\d+[.)]) ')


def inline(s):
    out = []
    for tok in INLINE.split(s):
        if not tok:
            continue
        if tok.startswith('**') and tok.endswith('**') and len(tok) > 4:
            out.append({'type': 'text', 'text': tok[2:-2], 'marks': [{'type': 'strong'}]})
        elif tok.startswith('`') and tok.endswith('`') and len(tok) > 2:
            out.append({'type': 'text', 'text': tok[1:-1], 'marks': [{'type': 'code'}]})
        elif tok.startswith('[') and tok.endswith(')') and '](' in tok:
            texto, href = tok[1:-1].split('](', 1)
            out.append({'type': 'text', 'text': texto,
                        'marks': [{'type': 'link', 'attrs': {'href': href}}]})
        else:
            out.append({'type': 'text', 'text': tok})
    return out


def convert(md):
    content, lista, par = [], None, []
    linhas = md.replace('\r\n', '\n').split('\n')

    def fecha_par():
        if par:
            content.append({'type': 'paragraph', 'content': inline(' '.join(par))})
            par.clear()

    i = 0
    while i < len(linhas):
        line = linhas[i]
        i += 1
        fence = FENCE.match(line)
        if fence:
            fecha_par()
            lista = None
            corpo = []
            while i < len(linhas) and not FENCE.match(linhas[i]):
                corpo.append(linhas[i])
                i += 1
            i += 1  # pula o ``` de fechamento
            no = {'type': 'codeBlock', 'content': [{'type': 'text', 'text': '\n'.join(corpo)}]}
            if fence.group(1).strip():
                no['attrs'] = {'language': fence.group(1).strip()}
            if not corpo:
                no.pop('content')
            content.append(no)
            continue
        for regex, tipo in ((BULLET, 'bulletList'), (ORDERED, 'orderedList')):
            m = regex.match(line)
            if m:
                break
        else:
            m = None
        if m:
            fecha_par()
            if lista is None or lista['type'] != tipo:
                lista = {'type': tipo, 'content': []}
                content.append(lista)
            lista['content'].append({'type': 'listItem', 'content': [
                {'type': 'paragraph', 'content': inline(m.group(1))}]})
            continue
        if not line.strip():
            fecha_par()
            lista = None
            continue
        if lista is not None and line.startswith(' '):
            # continuação do item de lista anterior
            p = lista['content'][-1]['content'][0]
            p['content'] = inline(_texto(p['content']) + ' ' + line.strip())
            continue
        lista = None
        h = HEADING.match(line)
        if h:
            fecha_par()
            content.append({'type': 'heading', 'attrs': {'level': len(h.group(1))},
                            'content': inline(h.group(2))})
        elif line.strip() == '---':
            fecha_par()
            content.append({'type': 'rule'})
        else:
            par.append(line.strip())
    fecha_par()
    return {'version': 1, 'type': 'doc', 'content': content}


def _texto(nos):
    """Reconstrói o markdown inline de um parágrafo, para somar a linha de continuação."""
    partes = []
    for n in nos:
        marks = [m['type'] for m in n.get('marks', [])]
        t = n['text']
        if 'strong' in marks:
            t = f'**{t}**'
        elif 'code' in marks:
            t = f'`{t}`'
        elif 'link' in marks:
            t = f"[{t}]({n['marks'][0]['attrs']['href']})"
        partes.append(t)
    return ''.join(partes)


def recusas(md, doc):
    """Construções que o conversor entregaria erradas ao Jira: lista aninhada (o ADF sairia num
    nível só) e crase dentro de negrito (a crase apareceria literal)."""
    erros, dentro = [], False
    for n, line in enumerate(md.replace('\r\n', '\n').split('\n'), 1):
        if FENCE.match(line):
            dentro = not dentro
        elif not dentro and ANINHADO.match(line):
            erros.append(f'linha {n}: lista aninhada sairia num nível só; '
                         'use um parágrafo em negrito por grupo, cada um com a sua lista')

    def textos(no):
        if isinstance(no, dict):
            if no.get('type') == 'text':
                yield no
            for c in no.get('content', []) or []:
                yield from textos(c)

    for t in textos(doc):
        if '`' in t['text'] and any(m.get('type') == 'strong' for m in t.get('marks', [])):
            erros.append(f"negrito com crase ({t['text']!r}): a crase sairia literal; "
                         'tire a crase ou o negrito')
    return erros


def varredura(doc):
    """A varredura de marks e estrutura do templates.md §Antes de postar."""
    ruim_marks, ruim_estrutura = [], []

    def check(n, caminho='root'):
        if isinstance(n, dict):
            for m in n.get('marks', []) or []:
                if not isinstance(m, dict) or m.get('type') not in VALIDAS:
                    ruim_marks.append((caminho, m))
            for i, c in enumerate(n.get('content', []) or []):
                if not isinstance(c, dict) or 'type' not in c:
                    ruim_estrutura.append((f'{caminho}.content[{i}]', repr(c)[:60]))
                else:
                    check(c, f"{caminho}.{c.get('type')}")
        elif isinstance(n, list):
            for i, c in enumerate(n):
                check(c, f'{caminho}[{i}]')

    check(doc)
    return ruim_marks, ruim_estrutura


def main(argv):
    args = [a for a in argv if a != '--doc']
    if len(args) != 2:
        print(__doc__.strip().split('\n\n')[1], file=sys.stderr)
        return 2
    with open(args[0], encoding='utf-8') as f:
        md = f.read()
    doc = convert(md)
    erros = recusas(md, doc)
    if erros:
        print('\n'.join(erros), file=sys.stderr)
        return 1
    ruim_marks, ruim_estrutura = varredura(doc)
    if ruim_marks or ruim_estrutura:
        print(f'marks invalidas: {ruim_marks}', file=sys.stderr)
        print(f'content com item que nao e no: {ruim_estrutura}', file=sys.stderr)
        return 1
    payload = doc if '--doc' in argv else {'body': doc}
    with open(args[1], 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False)
    print(f"ok: {len(doc['content'])} blocos -> {args[1]}")
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
