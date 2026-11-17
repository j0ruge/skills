#!/usr/bin/env python3
"""Mede o cache de prompt do Claude Code pelos transcritos locais (`~/.claude/projects/**/*.jsonl`). Só leitura.

Por modelo: quanto da entrada veio do cache. Por tipo de conversa (principal ou subagente): o TTL das escritas, as
quedas de cache pela causa e o tamanho do contexto por pedido. No fim, a conta que diz se o TTL de 1h compensa.

O formato do transcrito não é documentado: sem nenhuma resposta com `message.usage`, o script falha e diz o que
esperava, em vez de imprimir zeros.

Saída: 0 com o relatório; 2 sem transcritos, com a pasta errada ou com o formato inesperado.
"""
import argparse
import json
import statistics
import sys
import time
from datetime import datetime
from pathlib import Path

MIN_PREFIX = 20_000   # prefixo menor que isto não conta como queda: a reescrita é barata e o ruído é grande
MISS_RATIO = 0.5      # queda: o pedido leu do cache menos que esta fração do prefixo do pedido anterior
CAUSES = ('idle_over_1h', 'idle_5m_to_1h', 'model_switch', 'prefix_changed')
LABELS = {'idle_over_1h': 'pausa de mais de 1h', 'idle_5m_to_1h': 'pausa entre 5 min e 1h',
          'model_switch': 'troca de modelo', 'prefix_changed': 'sem pausa: o prefixo mudou'}
KINDS = {'main': 'conversa principal', 'sub': 'subagentes'}


class UnexpectedFormat(Exception):
    """Os arquivos têm linhas, mas nenhuma é uma resposta com `message.usage`."""


def _seconds(stamp):
    """O `timestamp` ISO do transcrito em segundos; None se faltar ou não for ISO."""
    try:
        return datetime.fromisoformat(stamp.replace('Z', '+00:00')).timestamp()
    except (AttributeError, ValueError):
        return None


def _is_sub(path):
    """Transcrito de subagente: fica numa pasta `subagents` ou se chama `agent-*.jsonl`."""
    return 'subagents' in path.parts or path.name.startswith('agent-')


def ttl_threshold(write_5m=1.25, write_1h=2.0, read=0.1):
    """Fração das escritas de 5 min que precisa ser reescrita depois de pausa de 5 min a 1h para o TTL de 1h empatar.

    Hoje: W escritos a `write_5m`. Com 1h: os R reescritos viram leitura e o resto custa `write_1h`.
    Empata quando write_1h * (W - R) + read * R = write_5m * W, isto é, R / W = (write_1h - write_5m) / (write_1h - read).
    """
    return (write_1h - write_5m) / (write_1h - read)


def ttl_verdict(written_5m, rewritten, write_5m=1.25, write_1h=2.0, read=0.1):
    """Se passar as escritas de 5 min para 1h sai mais barato, com os números da conta."""
    threshold = ttl_threshold(write_5m, write_1h, read)
    share = rewritten / written_5m if written_5m else 0.0
    return {'written_5m': written_5m, 'rewritten': rewritten, 'share': share, 'threshold': threshold,
            'worth_1h': written_5m > 0 and share > threshold}


def audit(files, write_5m=1.25, write_1h=2.0, read=0.1):
    """Lê os transcritos e devolve o relatório como dicionário (o `--json` o imprime como está)."""
    seen, lines, models = set(), 0, {}
    writes = {k: {'5m': 0, '1h': 0} for k in KINDS}
    context = {k: [] for k in KINDS}
    misses = {}
    rewritten_5m = {k: 0 for k in KINDS}
    for path in files:
        path = Path(path)
        previous = None
        with open(path, encoding='utf-8', errors='replace') as handle:
            for raw in handle:
                if not raw.strip():
                    continue
                lines += 1
                try:
                    record = json.loads(raw)
                except ValueError:
                    continue
                message = record.get('message') if isinstance(record, dict) else None
                usage = message.get('usage') if isinstance(message, dict) else None
                if record.get('type') != 'assistant' or not isinstance(usage, dict):
                    continue
                ident = message.get('id')
                if ident is not None and ident in seen:  # o transcrito repete a resposta a cada bloco de conteúdo
                    continue
                seen.add(ident)
                kind = 'sub' if _is_sub(path) or record.get('isSidechain') else 'main'
                fresh = usage.get('input_tokens') or 0
                got = usage.get('cache_read_input_tokens') or 0
                put = usage.get('cache_creation_input_tokens') or 0
                creation = usage.get('cache_creation') or {}
                put_5m = creation.get('ephemeral_5m_input_tokens') or 0
                put_1h = creation.get('ephemeral_1h_input_tokens') or 0
                model = message.get('model') or '?'
                row = models.setdefault(model, {'requests': 0, 'input': 0, 'read': 0, 'write': 0, 'output': 0})
                row['requests'] += 1
                row['input'] += fresh
                row['read'] += got
                row['write'] += put
                row['output'] += usage.get('output_tokens') or 0
                writes[kind]['5m'] += put_5m
                writes[kind]['1h'] += put_1h
                total = fresh + got + put
                context[kind].append(total)
                when = _seconds(record.get('timestamp'))
                if previous and when is not None and previous[0] is not None \
                        and previous[2] > MIN_PREFIX and got < MISS_RATIO * previous[2]:
                    gap = when - previous[0]
                    if model != previous[1]:
                        cause = 'model_switch'
                    elif gap > 3600:
                        cause = 'idle_over_1h'
                    elif gap > 300:
                        cause = 'idle_5m_to_1h'
                    else:
                        cause = 'prefix_changed'
                    slot = misses.setdefault((kind, cause), [0, 0])
                    slot[0] += 1
                    slot[1] += put
                    if cause == 'idle_5m_to_1h':
                        rewritten_5m[kind] += put_5m
                previous = (when, model, total)
    if not seen:
        raise UnexpectedFormat(
            f'{lines} linha(s) em {len(files)} arquivo(s), nenhuma com type == "assistant" e message.usage; '
            'esperado: uma linha JSON por evento, a resposta com message.id, message.model e message.usage '
            '(input_tokens, cache_read_input_tokens, cache_creation_input_tokens). O formato do transcrito mudou?')
    for row in models.values():
        entered = row['input'] + row['read'] + row['write']
        row['read_pct'] = 100 * row['read'] / entered if entered else 0.0
    sizes = {}
    for kind, values in context.items():
        values.sort()
        sizes[kind] = {'requests': len(values), 'median': int(statistics.median(values)) if values else 0,
                       'p90': values[min(len(values) - 1, int(len(values) * 0.9))] if values else 0,
                       'max': values[-1] if values else 0, 'sum': sum(values)}
    return {'files': len(files), 'models': models, 'writes': writes, 'context': sizes,
            'misses': [{'kind': k, 'cause': c, 'events': misses[k, c][0], 'rewritten': misses[k, c][1]}
                       for k in KINDS for c in CAUSES if (k, c) in misses],
            'ttl': {k: ttl_verdict(writes[k]['5m'], rewritten_5m[k], write_5m, write_1h, read) for k in KINDS},
            'multipliers': {'write_5m': write_5m, 'write_1h': write_1h, 'read': read}}


def _m(tokens):
    """Tokens em milhões, com uma casa."""
    return f'{tokens / 1e6:.1f}M'


def _n(tokens):
    """Tokens com ponto de milhar."""
    return f'{tokens:,}'.replace(',', '.')


def render(report, days):
    """O relatório em texto."""
    period = f'últimos {days:g} dia(s)' if days else 'todos os transcritos'
    out = [f'Cache de prompt do Claude Code: {report["files"]} transcrito(s), {period}', '',
           f'{"modelo":30} {"pedidos":>8} {"entrada":>9} {"escrito":>9} {"lido":>10} {"% lido":>7}']
    for model, row in sorted(report['models'].items(), key=lambda item: -(item[1]['read'] + item[1]['write'])):
        if not row['input'] + row['read'] + row['write']:
            continue  # resposta sintética do próprio Claude Code, sem tokens de entrada
        out.append(f'{model:30} {row["requests"]:8} {_m(row["input"]):>9} {_m(row["write"]):>9} '
                   f'{_m(row["read"]):>10} {row["read_pct"]:6.1f}%')
    out += ['', 'Escritas por TTL e tamanho do contexto por pedido:']
    for kind, label in KINDS.items():
        w, c = report['writes'][kind], report['context'][kind]
        out.append(f'  {label:20} 5 min {_m(w["5m"]):>8} | 1h {_m(w["1h"]):>8} | {c["requests"]} pedidos, '
                   f'mediana {_n(c["median"])} tokens, p90 {_n(c["p90"])}, máximo {_n(c["max"])}')
    out += ['', f'Quedas de cache (prefixo anterior acima de {MIN_PREFIX} tokens, menos de {MISS_RATIO:.0%} lido):']
    if not report['misses']:
        out.append('  nenhuma')
    for miss in report['misses']:
        out.append(f'  {KINDS[miss["kind"]]:20} {LABELS[miss["cause"]]:28} {miss["events"]:5} vez(es), '
                   f'{_m(miss["rewritten"])} reescritos')
    mult = report['multipliers']
    out += ['', f'TTL de 1h no lugar de 5 min (escrita {mult["write_5m"]:g}x e {mult["write_1h"]:g}x, leitura '
                f'{mult["read"]:g}x a entrada): compensa quando a reescrita depois de pausa de 5 min a 1h passa de '
                f'{report["ttl"]["main"]["threshold"]:.1%} do escrito em 5 min.']
    for kind, label in KINDS.items():
        verdict = report['ttl'][kind]
        if not verdict['written_5m']:
            out.append(f'  {label:20} nada escrito em 5 min: nada a mudar')
            continue
        out.append(f'  {label:20} {_m(verdict["rewritten"])} de {_m(verdict["written_5m"])} = {verdict["share"]:.1%}: '
                   + ('COMPENSA passar para 1h' if verdict['worth_1h'] else 'NÃO compensa; fique em 5 min'))
    return '\n'.join(out)


def main(argv=None):
    """Linha de comando."""
    parser = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    parser.add_argument('--projects-dir', default=str(Path.home() / '.claude' / 'projects'),
                        help='pasta dos transcritos (padrão: ~/.claude/projects)')
    parser.add_argument('--days', type=float, default=14,
                        help='só arquivos modificados nos últimos N dias; 0 lê todos (padrão: 14)')
    parser.add_argument('--json', action='store_true', help='imprime o relatório como JSON')
    parser.add_argument('--write-5m', type=float, default=1.25, help='multiplicador da escrita de 5 min (padrão: 1.25)')
    parser.add_argument('--write-1h', type=float, default=2.0, help='multiplicador da escrita de 1h (padrão: 2)')
    parser.add_argument('--read', type=float, default=0.1, help='multiplicador da leitura do cache (padrão: 0.1)')
    args = parser.parse_args(argv)
    root = Path(args.projects_dir).expanduser()
    if not root.is_dir():
        print(f'cache_audit: a pasta {root} não existe; passe --projects-dir <pasta dos transcritos>', file=sys.stderr)
        return 2
    cutoff = time.time() - args.days * 86400 if args.days else 0
    files = sorted(p for p in root.rglob('*.jsonl') if p.stat().st_mtime >= cutoff)
    if not files:
        print(f'cache_audit: nenhum .jsonl em {root} nos últimos {args.days:g} dia(s); tente --days 0',
              file=sys.stderr)
        return 2
    try:
        report = audit(files, args.write_5m, args.write_1h, args.read)
    except UnexpectedFormat as error:
        print(f'cache_audit: {error}', file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2) if args.json else render(report, args.days))
    return 0


if __name__ == '__main__':
    sys.exit(main())
