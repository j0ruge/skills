#!/usr/bin/env python3
"""O que o SKILL.md repete: das references dele, ou de si mesmo.

É a prova antes de remover (Passo 2 da skill-refactoring): só sai do SKILL.md o
que este script aponta. Somente leitura, só biblioteca padrão.

    python3 scripts/repetidos.py <dir-da-skill>          # relatório
    python3 scripts/repetidos.py <dir-da-skill> --json   # para outro script

Três achados, com o espaço em branco normalizado:
  BLOCO     bloco de código do SKILL.md que uma reference traz INTEIRO (contíguo)
            ou COBERTO (toda linha está na mesma reference, com algo no meio);
  FRASE     frase do texto corrido, de --min caracteres ou mais, que uma reference
            já tem igual;
  REPETIDA  frase de --min caracteres ou mais que aparece duas vezes no SKILL.md.

Bloco PARCIAL (só algumas linhas na reference) não é achado: o resto ainda mora
só no SKILL.md. Sai 0 com ou sem achado; 2 é uso errado (sem SKILL.md).
"""
import argparse
import json
import re
import sys
from pathlib import Path

# A cerca pode vir indentada: o bloco de um passo numerado mora dentro do item da lista.
BLOCO = re.compile(r"^[ \t]*```[^\n]*\n(.*?)^[ \t]*```", re.S | re.M)


def _norm(texto: str) -> str:
    return " ".join(texto.split())


def _linha(texto: str, posicao: int) -> int:
    return texto.count("\n", 0, posicao) + 1


def _frases(texto: str, minimo: int) -> list[tuple[int, str]]:
    """As frases do texto corrido (fora de bloco de código), com a linha de cada."""
    sem_blocos = BLOCO.sub(lambda m: "\n" * m.group(0).count("\n"), texto)
    achadas = []
    for m in re.finditer(r"[^\n.;:!?]+(?:[.;:!?](?=\s|$)|$)", sem_blocos, re.M):
        frase = _norm(m.group(0)).strip("*_|>- ")
        if len(frase) >= minimo:
            achadas.append((_linha(sem_blocos, m.start()), frase))
    return achadas


def analisar(dir_skill: Path, minimo: int) -> dict:
    skill = (dir_skill / "SKILL.md").read_text(encoding="utf-8")
    refs = {f"references/{p.name}": p.read_text(encoding="utf-8")
            for p in sorted((dir_skill / "references").glob("*.md"))}
    refs_norm = {nome: _norm(texto) for nome, texto in refs.items()}
    refs_linhas = {nome: {_norm(l) for l in texto.splitlines() if _norm(l)}
                   for nome, texto in refs.items()}

    blocos = []
    for m in BLOCO.finditer(skill):
        corpo = m.group(1)
        linhas = [_norm(l) for l in corpo.splitlines() if _norm(l)]
        if not linhas:
            continue
        inteiro = next((n for n, t in refs_norm.items() if _norm(corpo) in t), None)
        if inteiro:
            blocos.append({"tipo": "INTEIRO", "linha": _linha(skill, m.start()),
                           "chars": len(corpo), "reference": inteiro})
            continue
        for nome, conjunto in refs_linhas.items():
            cobertas = sum(1 for l in linhas if l in conjunto)
            if cobertas == len(linhas):
                blocos.append({"tipo": "COBERTO", "linha": _linha(skill, m.start()),
                               "chars": len(corpo), "reference": nome,
                               "cobertas": cobertas, "total": len(linhas)})
                break

    frases, vistas, repetidas = [], {}, []
    for linha, frase in _frases(skill, minimo):
        onde = next((n for n, t in refs_norm.items() if frase in t), None)
        if onde:
            frases.append({"linha": linha, "reference": onde, "frase": frase})
        if frase in vistas:
            repetidas.append({"linhas": [vistas[frase], linha], "frase": frase})
        else:
            vistas[frase] = linha
    return {"blocos": blocos, "frases": frases, "repetidas": repetidas}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("dir_skill", type=Path, help="diretório da skill (com o SKILL.md)")
    parser.add_argument("--min", type=int, default=80,
                        help="tamanho mínimo da frase comparada (padrão 80 caracteres)")
    parser.add_argument("--json", action="store_true", help="saída em JSON")
    args = parser.parse_args()
    if not (args.dir_skill / "SKILL.md").is_file():
        print(f"{args.dir_skill}: sem SKILL.md", file=sys.stderr)
        return 2
    resultado = analisar(args.dir_skill, args.min)
    if args.json:
        print(json.dumps(resultado, ensure_ascii=False, indent=2))
        return 0
    for b in resultado["blocos"]:
        extra = f" ({b['cobertas']}/{b['total']} linhas)" if b["tipo"] == "COBERTO" else ""
        print(f"BLOCO     L{b['linha']:<4} {b['chars']:5d} chars  {b['tipo']}{extra} em {b['reference']}")
    for f in resultado["frases"]:
        print(f"FRASE     L{f['linha']:<4} em {f['reference']}: {f['frase'][:90]}")
    for r in resultado["repetidas"]:
        print(f"REPETIDA  L{r['linhas'][0]} e L{r['linhas'][1]}: {r['frase'][:90]}")
    if not any(resultado.values()):
        print("nada repetido: o que sair do SKILL.md precisa de outra prova (Estratégia B)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
