# Conferir um `--fix --write` antes do commit

O `--fix` é determinístico, mas uma migração de formato apaga itens, troca o preâmbulo e muda os
headings. Três coisas escapam dos gates dele e só aparecem no commit seguinte, ou nunca. Rode as
três antes de commitar o `--write`, na branch da migração.

Os três casos foram medidos no `lighthouse_project` em 2026-10-16: 139 violações iniciais, 20 itens
marcados apagados pelo `AUTO` e 57 casos `MANUAL`.

## 1. A quebra de linha não mudou nenhuma palavra

O `AUTO` promete quebrar em 120 colunas "sem mudar uma palavra", e o título em negrito só acrescenta
`**`. Prove na seção aberta, palavra por palavra, contra a versão commitada:

```bash
norm() { awk '/^<!-- sdd:open -->$/{f=1;next} /^## /{f=0} f' | tr -d '*' | tr -s ' \n' '\n'; }
diff <(git show HEAD:TODO.md | norm) <(norm < TODO.md) | grep -c '^[<>]'    # tem de dar 0
```

⚠️ **Ancore o marcador na linha inteira (`^…$`).** O preâmbulo da semente atual cita
`<!-- sdd:open -->` entre crases, ao explicar o esqueleto. O recorte por `/<!-- sdd:open -->/`
começa nesse parágrafo, e a comparação acusa 364 linhas de diferença onde há 0 (medido na
migração do `lighthouse_project`, 2026-10-16). Desde a 2.6.0 o
`AUTO` também apaga item aberto já resolvido (`--fix` diz quantos): as palavras dele saem como `<`,
e só elas podem sair. Confira que cada `<` pertence a um desses itens.

## 2. Um item apagado pode carregar um plano condicional

O `AUTO` apaga o item cujo `RESOLVED by` já está na branch padrão, e só olha o hash. O texto pode
guardar uma contingência que não vive em outro lugar. No caso medido, o item do `a7755bc` dizia: "é
PREMISSA da decisão 6 da Direção: se ela a recusar, `git revert a7755bc` e este item volta". O
plano sobreviveu porque também estava em `docs/roadmap/amep.md`.

Antes do `--write`, liste o hash de cada item que sai com uma condicional no corpo. A condicional
costuma estar numa linha de continuação, então o filtro lê o bloco inteiro, não só a primeira
linha (que, no caso medido, deu 7 acertos de ruído e nenhum do `a7755bc`):

```bash
python3 $S --fix | awk '/^-- \[/{b=$0; next} /^-  /{b=b"\n"$0; if (tolower($0) ~ /premissa|revert|volta a/) \
  {print b; b=""}; next} {b=""}' | grep -oE 'RESOLVED by `[0-9a-f]{7,}`' | sort -u
git grep -n <hash> -- ':!TODO.md'      # para cada hash: a contingência tem outro dono?
```

Sem outro dono, o plano vira uma linha na seção decidida, citando o hash e a condição, no mesmo
commit.

## 3. Um sensor do repositório que lia os headings antigos fica cego

A migração troca `## Open`/`## Resolved` pelos marcadores. Um teste do próprio repositório que
procurava esses headings não reprova: ele para de ver. No caso medido, o `docs.test.ts` (o teste
"nenhuma dívida está na seção errada do TODO") continuou verde com uma caixa aberta plantada na
seção decidida.

```bash
git grep -nE '## Resolved|## Open\b|Closed is DELETED' -- ':!TODO.md' ':!docs/handoffs'
```

Cada acerto que é sensor passa a ler os marcadores (`<!-- sdd:open -->`, `<!-- sdd:decided -->`,
linha inteira) e é visto vermelho por sabotagem antes do commit: uma caixa aberta na seção
decidida, uma caixa marcada na aberta e o marcador apagado.
