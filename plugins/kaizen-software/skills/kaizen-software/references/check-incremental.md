# Check incremental com baseline fixa

Use quando o critério de sucesso for não introduzir regressão em um artefato
que já contém dívida. Não é uma auditoria global nem uma baseline móvel calculada
da própria população: a referência é um estado anterior identificado e preservado.

## Receita

1. Antes de editar, registre a revisão ou snapshot anterior, comando, versão e
   opções do checker, escopo e achados. Preserve a saída, não apenas sua contagem.
2. Rode o mesmo checker depois, incluindo os arquivos novos. Se versão, opções
   ou escopo mudarem, reconstrua a medição anterior a partir da revisão original;
   não use a árvore já editada como baseline. Sem base reproduzível, declare
   comparação inconclusiva em vez de assumir ausência de regressão.
3. Compare a identidade estável dos achados: regra, arquivo e evidência.
   Número de linha pode mudar sem mudar o defeito. Compare severidade como
   atributo ordenado: redução não é regressão, aumento é agravamento. Preserve
   multiplicidade e confira as contagens por limiar de severidade; contagens
   totais ou um conjunto que descarte repetições podem esconder regressões.
4. Classifique: **novo/agravado** bloqueia o incremento; **dívida anterior** fica
   registrada, sem autorizar correção fora do escopo; **desaparecido** exige
   explicação, pois apagar a evidência ou reduzir a cobertura também apaga alertas.
5. Confira o delta com controle bom e sabotado: dívida inalterada não vira
   regressão; um defeito acrescentado ou agravado precisa reprovar. Um defeito
   antigo desaparecer e outro nascer mantém a contagem, mas continua reprovando.
6. Relate o resultado incremental e a dívida separadamente, com comando e saída.
   Não chame a auditoria de limpa enquanto houver achados antigos. Checks de
   segurança, critérios de aceitação e gates absolutos continuam exigindo seus
   resultados próprios; a baseline não os desliga nem concede exceção.

Se o escopo da tarefa incluir reparar a dívida, confira também a remoção efetiva
da causa e sua regressão. Classificá-la como antiga não cumpre esse objetivo.

## Exemplo executável em memória

Os achados abaixo são sintéticos. Cada tupla contém regra, arquivo, evidência
estável e severidade. A identidade não inclui a severidade. O exemplo compara
contagens por identidade e por limiar ordenado para não confundir redução com
agravamento. Execute com `python3 -B`, sem arquivo, rede ou código do projeto:

```python
from collections import Counter

LEVELS = {"info": 0, "warning": 1, "error": 2}
legacy = ("invalid_link", "docs/guide.md", "old-missing-target", "warning")
fresh = ("invalid_link", "docs/guide.md", "new-missing-target", "warning")
raised = (*legacy[:3], "error")
lowered = (*legacy[:3], "info")
baseline = [legacy]
before = Counter(row[:3] for row in baseline)


def compare(after):
    current = Counter(row[:3] for row in after)
    identities = set(before) | set(current)

    def count_at_least(rows, identity, threshold):
        return sum(row[:3] == identity and LEVELS[row[3]] >= threshold for row in rows)

    regression = any(
        count_at_least(after, identity, threshold)
        > count_at_least(baseline, identity, threshold)
        for identity in identities for threshold in LEVELS.values())
    return {"regression": regression, "introduced": current - before,
            "debt": current & before, "disappeared": before - current}


unchanged = compare([legacy])
assert not unchanged["regression"]
assert not unchanged["introduced"]
assert unchanged["debt"] == before
assert not unchanged["disappeared"]

assert compare([legacy, fresh])["regression"]
assert compare([legacy, fresh])["introduced"] == Counter([fresh[:3]])
assert compare([legacy, legacy])["regression"]
assert compare([legacy, legacy])["introduced"] == before
assert compare([fresh])["regression"]
assert compare([fresh])["disappeared"] == before
assert compare([raised])["regression"]
assert not compare([raised])["introduced"]
assert not compare([lowered])["regression"]
assert compare([lowered])["debt"] == before
assert compare([])["disappeared"] == before
print("Delta conferido: identidade, multiplicidade e severidade preservadas.")
```

O campo `regression` bloqueia o incremento. `introduced` conta ocorrências novas
por identidade; `debt` pode incluir achado cuja severidade diminuiu. Registre
reduções e explique os desaparecidos separadamente. O exemplo não aprova gates
absolutos nem substitui o checker real, que também precisa provar ter aberto o
artefato novo.
