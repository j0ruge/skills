---
missao: 20261125-retrofit-watch-atribuicao
fase: REVIEW
rodada: 18
status: done
sessao: 01a21f0c-996c-7070-babe-0d8c06f23691
data: 2026-11-27 19:13
gate: 'Em b466c6c111a3093da6aa033f84d75428ab0a206a, árvore inicial limpa. env -u GIT_DIR -u GIT_WORK_TREE PYTHONDONTWRITEBYTECODE=1 bash -c ''source .sdd/config.sh && eval "$TEST_CMD"'' retornou rc 0. Adaptadores e catálogo válidos, 154 testes da loja (3 pulados por configuração), 114 testes do hook e retrofit-watch 0.4.1 validada. Os 14 Checks retornaram rc 0 e o stdout esperado. Nenhum incremento pendente. Documentation permanece em B pelo pré-scan manual, dentro da tolerância do gate. Sem regressão nos critérios estritos.'
reviewed_head: b466c6c111a3093da6aa033f84d75428ab0a206a
---

# Review — rodada r18 — Atribuição da retrofit-watch por mensagem

Delta de `1b7d8831271e9d4e7f818060abd228beb21e8413` até `b466c6c111a3093da6aa033f84d75428ab0a206a`, com quatro commits. Seis registros
analisados. O diário append-only aparece na lista de caminhos, mas seu conteúdo
não faz parte da análise. Nenhum arquivo de produção, teste ou configuração mudou.

## TL;DR

A suíte e os 14 Checks passaram. Os dois cenários da r17 foram corrigidos.
Marcar Markdown como binário ainda faz o pré-scan manual retornar sucesso com zero linhas.
O caso fica no item existente do backlog. Documentation B, demais notas A, sem R13.

## Nota da rodada

### Secrets Detection

**Status PASS.** Regex e gitleaks analisaram seis arquivos e 207 linhas adicionadas,
sem ocorrências nem erros. O total coincide com o `--numstat` no mesmo recorte.
A varredura da rodada forçou a saída de texto para os seis registros e não leu o diário.

### Código, cobertura e sincronização

As 14 linhas de incrementos são idênticas às da base. Cada Check foi executado
com rc e stdout inteiro conferidos. As regressões exercitam o hook e a retomada
pelo estado em disco. A suíte descobriu 154 testes da loja, três pulados por
configuração, e 114 do hook. Não houve smoke no host Claude Code ou no Windows.
Não houve alteração no esquema do estado, nas travas, na versão ou no escopo dos testes.

### Varredura de símbolos

Bucket A em linha. O delta não introduziu nem deixou órfão símbolo produtivo e
não renomeou interface. As variáveis introduzidas nas receitas são locais e usadas.
Bucket B não solicitado.

### Overall Grade

| Criterion | Grade | Rationale |
|-----------|-------|-----------|
| Code Quality (Zen) | A | As alterações são de registros e comandos manuais. Nenhum caminho produtivo ou Check mudou. |
| Type Safety | A | Nenhuma assinatura, dependência ou chave persistida mudou no recorte. |
| Error Handling | A | F1 e R12 confirmaram silêncio após o encerramento e os controles de nova carga e slash continuaram funcionando. |
| Security | A | O pré-scan independente contabilizou todas as 207 linhas do recorte analisado e não detectou credenciais. O desvio é de receitas manuais históricas. |
| Performance | A | Nenhum caminho produtivo novo. Os Checks de retomada e migração R10–R12 passaram. |
| Test Coverage | A | Os 14 Checks e toda a suíte configurada passaram, com os três pulos de distribuição já configurados. |
| Documentation | B | Os casos da r17 foram corrigidos, mas o pré-scan manual ainda aceita zero linhas quando o Git classifica Markdown como binário. |
| **Overall** | **A** | Sem regressão funcional. A limitação reproduzida pertence à documentação e está no backlog. |

## Achados da rodada

| # | Severidade | Achado | Onde |
|---|---|---|---|
| 1 | MEDIUM | O diff nativo ainda respeita `-diff` nos atributos Git. Com Markdown classificado como binário, a receita sai com rc 0, zero linhas adicionadas analisadas e nenhum erro. Isso deixa incompleta a resolução integral anotada no backlog. | `40-review-r14.md:37`, `40-review-r15.md:119` e `TODO.md:280` |

A diferença foi medida com atributos temporários, sem alterar a configuração
do checkout. O scanner reconheceu 9 arquivos na r14 e 3 na r15, mas não leu
linhas de nenhum deles. Forçar apenas `--text` no mesmo comando restaurou
382 e 175 linhas, respectivamente. O desvio afeta a receita manual, não o hook
nem o pré-scan desta rodada.

## Incrementos de conserto (R<n>)

Nenhum. I1, F1 e R1 a R12 continuam em `done`.

## O que virou incremento

Nenhum nesta rodada.

- I1, fechado em `682cd3d`, repetiu `1 0 1 0 0 1`. F1, fechado em `c704301`,
  ficou em silêncio nas variantes `linked`, `missing` e `empty`.
- R12, fechado em `d77e6a1`, ficou em silêncio no limite, acima dele e após
  outro Stop. Carga nova e slash explícito pediram `graphify`. A regressão durável
  executou um teste.

## O que foi refutado

- O comparador externo do achado 1 da r17 deixou de cegar as receitas em `261bff5`.
  Com o mesmo comparador e com cor forçada e prefixos desligados, a base rendeu
  zero linhas nas duas receitas. No HEAD, a r14 voltou a 9 arquivos e 382 linhas,
  e a r15 a 3 arquivos e 175 linhas. O controle com conversor de texto também
  voltou às contagens nativas no HEAD. Isso confirma o conserto parcial.
- O achado 2 da r17 foi fechado em `261bff5`. O bloco da r16 em `2086fc6`
  saiu com rc 1. No HEAD, a referência histórica `24b801c` fez o mesmo bloco
  executar as quatro varreduras com rc 0, na ordem `(3, 175), (3, 0), (0, 0), (3, 175)`
  em arquivos e linhas. O bloco do comparador na r17 também continua reproduzível
  porque lê as receitas do blob anterior à correção.

## Achados fora de escopo

- O achado 1 foi incorporado ao item “Pré-scan manual da revisão pode passar sem
  analisar linhas”, em `TODO.md`. O item agora distingue o conserto confirmado
  do caso ainda aberto. Não há item duplicado nem nova entrada de `RECURRED`
  para o mesmo par de projeto e missão, conforme a gramática do backlog.

## Pendências / Decisions for a Human

Nenhuma decisão técnica nova. Documentation ficou em B e todas as outras letras
permaneceram em A. Esse patamar atende ao gate e encerra o ciclo sem incremento.
A base do PR é `main`, conforme `.sdd/config.sh`. O merge cabe ao mantenedor.

## Evidências reproduzíveis

Execute da raiz. A suíte e os Checks foram executados em `b466c6c111a3093da6aa033f84d75428ab0a206a`.
O comando da suíte está no campo `gate`. Para cada linha da tabela de `checkpoint.md`,
copie para `check` o comando entre crases, à esquerda de `→` na célula `Check (comando → esperado)`.
Execute-o com `env -u GIT_DIR -u GIT_WORK_TREE PYTHONDONTWRITEBYTECODE=1 bash -c "$check"`
e compare todo o stdout após normalizar espaços, exigindo rc 0.

~~~bash
(
  set -euo pipefail
  unset GIT_DIR GIT_WORK_TREE
  mission=docs/handoffs/20261125-retrofit-watch-atribuicao
  base=1b7d8831271e9d4e7f818060abd228beb21e8413
  reviewed=b466c6c111a3093da6aa033f84d75428ab0a206a
  exclude=":(exclude)$mission/checkpoint-notas.md"
  git -c diff.noprefix=false -P diff --text --numstat "$base...$reviewed" -- . "$exclude"
  git -c diff.noprefix=false -P diff --text --no-color --src-prefix=a/ --dst-prefix=b/ \
    --no-ext-diff --no-textconv --unified=0 "$base...$reviewed" -- . "$exclude" |
    bash "$HOME/.agents/skills/codereview/scripts/scan_secrets.sh"
)
~~~

O achado 1 pode ser repetido sem modificar a configuração do repositório.
O primeiro JSON de cada par traz zero linhas sem erro. O segundo usa
`--text` como controle e volta à contagem nativa. Todos saem com rc 0.

~~~bash
(
  set -euo pipefail
  unset GIT_DIR GIT_WORK_TREE
  mission=docs/handoffs/20261125-retrofit-watch-atribuicao
  reviewed=b466c6c111a3093da6aa033f84d75428ab0a206a
  fixture=$(mktemp -d)
  trap 'rm -rf -- "$fixture"' EXIT
  printf '*.md -diff\n' > "$fixture/attributes"
  export GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=core.attributesFile
  export GIT_CONFIG_VALUE_0="$fixture/attributes"
  for round in 14 15; do
    git show "$reviewed:$mission/40-review-r$round.md" |
      sed -n 's/^  \(git -c diff.noprefix=false .*scan_secrets\.sh"\)$/\1/p' > "$fixture/recipe"
    test "$(wc -l < "$fixture/recipe")" -eq 1
    bash -o pipefail "$fixture/recipe"
    sed 's/ -P diff / -P diff --text /' "$fixture/recipe" > "$fixture/control"
    bash -o pipefail "$fixture/control"
  done
)
~~~

Para repetir os casos anteriores, execute os segundos blocos Bash de
`40-review-r16.md` e `40-review-r17.md` no HEAD revisado. O bloco da r16 em
`2086fc6` é o negativo. O da r17 compara a receita anterior com as opções nativas.

### Recommended Actions

**Must Fix (CRITICAL)**

_Nenhum._

**Should Fix (HIGH)**

_Nenhum._

**Consider Fixing (MEDIUM/LOW)**

- Na triagem do pré-scan manual, conferir os totais do scanner contra a entrada
  esperada no recorte. Para as duas receitas de Markdown, forçar diff textual.

### Cost footprint

_Codereview 2.27.38 no caminho solicitado para o Codex. O cache do Claude registrava 2.30.2 e não foi usado. Dois agentes gpt-6.1-terra, seis leituras integrais e 12–13 chamadas por agente, sem relançamentos. Varredura de símbolos em linha. Custo monetário não medido._
