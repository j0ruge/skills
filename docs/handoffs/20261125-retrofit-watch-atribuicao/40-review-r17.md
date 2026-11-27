---
missao: 20261125-retrofit-watch-atribuicao
fase: REVIEW
rodada: 17
status: done
sessao: 01a21f05-c0a9-7512-9c08-060d27e5e8b2
data: 2026-11-27 19:05
gate: "Em 1b7d8831271e9d4e7f818060abd228beb21e8413, árvore limpa no início da revisão. env -u GIT_DIR -u GIT_WORK_TREE PYTHONDONTWRITEBYTECODE=1 bash -c 'source .sdd/config.sh && eval \"$TEST_CMD\"' retornou rc 0. Adaptadores e catálogo válidos, 154 testes da loja (3 pulados), 114 testes do hook e versão 0.4.1 validada. Os 14 Checks do checkpoint retornaram rc 0 e stdout esperado. Nenhum incremento pendente. Documentation permaneceu em B pelos desvios das receitas manuais, dentro da tolerância do gate. Sem regressão nos critérios estritos."
reviewed_head: 1b7d8831271e9d4e7f818060abd228beb21e8413
---

# Review — rodada r17 — Atribuição da retrofit-watch por mensagem

Delta de `0389ae5f350996de0d8f81b05194fcc4b9fb5abc` até `1b7d8831271e9d4e7f818060abd228beb21e8413` na branch `fix/retrofit-watch-atribuicao-mesma-mensagem`. Quatro commits, cinco registros revisados e duas linhas acrescentadas ao diário, fora da análise de conteúdo. Nenhum arquivo de produção, teste ou configuração mudou.

## TL;DR

A suíte configurada e os 14 Checks passaram. O delta alterou apenas registros.
A correção protege o pré-scan manual de cor e prefixos, mas um comparador externo ainda faz a receita retornar sucesso sem analisar o diff. O controle negativo da r16 também parou de localizar a receita original.
Os dois achados ficam no backlog. Nota B em Documentation e A nos demais critérios. Nenhum R13.

## Nota da rodada

### Secrets Detection

**Status PASS.** Regex e gitleaks analisaram cinco arquivos e 218 linhas
adicionadas, de acordo com a contagem de `git diff --numstat` no recorte.
Zero ocorrências e zero erros. A varredura usada para a nota excluiu o diário
append-only e desativou cor, comparadores externos e filtros de texto.

### Código, cobertura e sincronização

As 14 linhas da tabela de incrementos são idênticas às da base. Cada Check
foi executado uma vez, com rc e stdout conferidos. A suíte descobriu 154 testes
da loja, com três pulos configurados, e 114 do hook. O delta não alterou
esquema, tipos, dependências, travas nem caminhos de execução. Não houve
smoke no host Claude Code ou no Windows.

### Varredura de símbolos

Bucket A em linha. Nenhum símbolo produtivo introduzido ou órfão, nenhuma
interface renomeada. As variáveis e comandos mudados nas receitas são locais.
Bucket B não solicitado.

### Overall Grade

| Criterion | Grade | Rationale |
|-----------|-------|-----------|
| Code Quality (Zen) | A | O delta não alterou código de produção e manteve intactos os comandos dos 14 Checks. |
| Type Safety | A | Nenhuma assinatura, dependência ou chave do estado de sessão mudou no delta. |
| Error Handling | A | F1 ficou em silêncio nas três variantes. R12 preservou o encerramento na retomada sem impedir carga nova ou slash explícito. |
| Security | A | A varredura do delta conferiu entrada de 218 linhas, sem ocorrências nem erros. A limitação reproduzida está nas receitas manuais históricas. |
| Performance | A | Nenhum caminho de execução mudou e os Checks de migração R10–R12 passaram. |
| Test Coverage | A | Os 14 Checks e a suíte configurada passaram, com 154 testes da loja, três pulos configurados e 114 testes do hook. |
| Documentation | B | O pré-scan manual ainda pode retornar sucesso sem ler o diff. O controle negativo da r16 deixou de localizar a receita que pretende repetir. |
| **Overall** | **A** | As verificações funcionais passaram e os dois desvios se limitam a receitas manuais da revisão. |

## Achados da rodada

| # | Severidade | Achado | Onde |
|---|---|---|---|
| 1 | MEDIUM | Um comparador externo pode devolver texto que não é um patch. A receita retorna rc 0, zero arquivos, zero linhas e nenhum erro. A resolução anotada no backlog cobre cor e prefixos, mas não esse caso. | `40-review-r14.md:37`, `40-review-r15.md:119`, `TODO.md:277–282` |
| 2 | LOW | O controle negativo da r16 lê a receita atual da r15. A expressão de extração não reconhece a linha alterada em `3b8ef98`. O bloco aborta em `test -n` antes de rodar o scanner. | `40-review-r16.md:152–153` |

O achado 1 é do sensor manual, não do hook nem do gate configurado. O
comparador devolveu texto não vazio com rc 0, de modo que `pipefail` não ajuda
nesse caso. O comparador sem saída também deu rc 0, mas o scanner nesse caso
preencheu `errors` com `empty input`. No achado 2, trocar apenas a origem da
receita pelo blob histórico reproduziu as quatro varreduras da r16.

## Incrementos de conserto (R<n>)

Nenhum. I1, F1 e R1 a R12 continuam em `done`.

## O que virou incremento

Nenhum nesta rodada.

- F1, fechado em `c704301`, confirmou silêncio nas variantes `linked`, `missing`
  e `empty`. I1 manteve `1 0 1 0 0 1`.
- R12, fechado em `d77e6a1`, confirmou silêncio no limite, acima dele e após
  outro Stop. Os controles de carga nova e slash emitiram `graphify`.
  A regressão durável executou um teste.

## O que foi refutado

- Os dois falsos verdes originais da r16 não persistem. Com `diff.noprefix=true`
  ou `color.diff=always`, as receitas novas restauraram 9 arquivos e 382 linhas
  na r14 e 3 arquivos e 175 linhas na r15. As antigas mediram zero linhas nas
  duas configurações. A proteção nova contra erro do produtor também funcionou.
  Com uma opção inválida no Git, a receita retornou rc 129.
- O erro de extração da r16 não invalida a medição histórica. A receita lida no
  blob de `0389ae5f` executou as quatro varreduras, na ordem
  `(3, 175), (3, 0), (0, 0), (3, 175)` em arquivos e linhas.

## Achados fora de escopo

- Achado 1 registrado no mesmo item de documentação de `TODO.md`. O marcador de
  resolução integral foi retirado. O corpo conserva o conserto parcial de
  `3b8ef98` e o caso faltante. Não há entrada nova de `RECURRED` porque a
  atribuição do item já é desta missão e deste projeto.
- Achado 2 registrado no item “Controle negativo da r16 perde a receita original”
  em `TODO.md`. O relatório histórico não foi editado.

## Pendências / Decisions for a Human

Nenhuma decisão técnica nova. Documentation permanece em B, as demais letras
são as mesmas da r16, e o gate aceita esse patamar. Parar o ciclo de REVIEW,
sem novo incremento. A base do PR é `main`, conforme `.sdd/config.sh`. O merge
continua a cargo do mantenedor.

## Evidências reproduzíveis

Execute da raiz no `reviewed_head`. As quantidades abaixo contam arquivos e
linhas adicionadas. O comando de `TEST_CMD` está no campo `gate`.

~~~bash
mission=docs/handoffs/20261125-retrofit-watch-atribuicao
base=0389ae5f350996de0d8f81b05194fcc4b9fb5abc
review_head=1b7d8831271e9d4e7f818060abd228beb21e8413
scanner=$HOME/.agents/skills/codereview/scripts/scan_secrets.sh
exclude=":(exclude)$mission/checkpoint-notas.md"
(
  set -o pipefail
  git -P diff --numstat "$base...$review_head" -- . "$exclude"
  git -c diff.noprefix=false -P diff --no-color --src-prefix=a/ --dst-prefix=b/ \
    --no-ext-diff --no-textconv --unified=0 "$base...$review_head" -- . "$exclude" \
    | bash "$scanner"
)
~~~

Para os Checks, execute cada comando da coluna em `checkpoint.md` com
`env -u GIT_DIR -u GIT_WORK_TREE PYTHONDONTWRITEBYTECODE=1 bash -c "$check"`
e exija rc 0 e todo o stdout esperado, comparado após normalizar espaços.

O achado 1 é reproduzível sem trocar a configuração do repositório. O
comparador temporário abaixo representa um visualizador que escreve texto
fora do formato de patch.

~~~bash
(
  set -euo pipefail
  mission=docs/handoffs/20261125-retrofit-watch-atribuicao
  fixture=$(mktemp -d)
  trap 'rm -rf -- "$fixture"' EXIT
  cat > "$fixture/compare" <<'SH'
#!/bin/sh
printf 'Comparação externa de dois arquivos\n'
SH
  chmod +x "$fixture/compare"
  for r in 14 15; do
    recipe=$(sed -n 's/^  \(git -c diff.noprefix=false .*scan_secrets\.sh"\)$/\1/p' \
      "$mission/40-review-r$r.md")
    test -n "$recipe"
    env GIT_EXTERNAL_DIFF="$fixture/compare" bash -o pipefail -c "$recipe"
    native=${recipe/" -P diff "/" -P diff --no-ext-diff --no-textconv "}
    env GIT_EXTERNAL_DIFF="$fixture/compare" bash -o pipefail -c "$native"
  done
)
~~~

As receitas publicadas retornam rc 0 e `(0, 0)`. O controle nativo retorna
`(9, 382)` na r14 e `(3, 175)` na r15. Para o achado 2, execute o bloco
“controle negativo” da seção “Evidências reproduzíveis” da r16 como publicado
e depois troque somente a origem da extração por esta linha no mesmo bloco.

~~~bash
recipe=$(git show "0389ae5f350996de0d8f81b05194fcc4b9fb5abc:${report}" \
  | sed -n '/^git -P diff .*scan_secrets\.sh"$/p')
~~~

O bloco original sai com rc 1 antes da primeira varredura. O controle
histórico sai com rc 0 e quatro resultados, na ordem registrada acima.

### Recommended Actions

**Must Fix (CRITICAL)**

_Nenhum._

**Should Fix (HIGH)**

_Nenhum._

**Consider Fixing (MEDIUM/LOW)**

- Na triagem da receita manual, desabilitar comparação externa e filtros de
  texto. Conferir o rc do produtor, a contagem de arquivos e as linhas
  adicionadas quando o diff as contiver.
- Na triagem do controle negativo, fixar o blob histórico da receita da r15.

### Cost footprint

_Codereview 2.27.38 do caminho solicitado no Codex. O cache registrado do Claude tem 2.30.2, com fluxo adicional de verificação, e não foi usado. Dois agentes gpt-6.1-terra, seis leituras integrais, 3–11 chamadas reportadas por agente, sem relançamentos. Varredura de símbolos em linha. Custo monetário não medido._
