---
missao: 20261127-retrofit-watch-050
fase: REVIEW
rodada: 10
status: done
sessao: 01a221f0-fe11-73f0-a510-ad7224007024
data: 2026-11-28 08:42
gate: "Em 7f1d9375598e55d8570d962420669e6abcdafc6a, env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp/review-r10.jJFbXK PYTHONDONTWRITEBYTECODE=1 bash -c 'source .sdd/config.sh; eval \"$TEST_CMD\"' → rc 0. Adaptadores, catálogo e versões válidos, 154 testes da loja com três pulos nativos configurados e 144 do Stop sem pulos. Árvore limpa durante a medição. O gate de REVIEW não passou. Error Handling e Test Coverage continuam em B, com R16 pendente. Documentation subiu de B para A com bfbb9f8."
reviewed_head: 7f1d9375598e55d8570d962420669e6abcdafc6a
---

# Review — rodada r10 — Retrofit de skills locais com ensaio antes do push autônomo

## TL;DR

R15 fechou os dois casos da r9. A suíte configurada, 149 regressões dirigidas e a jornada de QA passaram.
O delta ainda libera um clone cuja main resolve para outro ramo e chama HEAD ilegível de ramo errado.
Os dois casos reproduzidos viraram R16. Nota geral B, com Error Handling e Test Coverage em B.
Documentation subiu de B para A após a correção do guia.

## Nota da rodada

Escopo `base=aab91a606994ce33601fba4043d24847fa16829f` até `7f1d9375598e55d8570d962420669e6abcdafc6a`. O delta tem um arquivo
de produto, `rw_store.py`, um de testes, `test_lean_live.py`, e sete documentos, incluindo
os registros da missão. O arquivo de notas de execução foi excluído da leitura e da
pré-varredura. `30-handoff-qa.md` orientou a repetição da jornada.

### Secrets Detection

| Arquivo | Linha | Tipo | Severidade |
|---|---|---|---|
| Nenhum | — | — | — |

PASS. Regex e Gitleaks examinaram 329 linhas adicionadas em nove arquivos do
delta e não reportaram erros de varredura.

### Cobertura, documentação e código morto

No SHA `7f1d9375598e55d8570d962420669e6abcdafc6a`, com árvore limpa antes de gravar a revisão:

| Prova | Comando | Resultado |
|---|---|---|
| Clone dedicado e startup | `env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -m unittest -v test_lean_live` | rc 0, 55 testes sem pulos. Inclui R15, remoção do marcador, trava e startup offline. |
| Elegibilidade, lote, porta e contratos | `env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -m unittest test_lean_auto test_lean_batch test_lean_gate test_auto_docs` | rc 0, 94 testes sem pulos. |
| Jornada de QA | `env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B docs/handoffs/20261127-retrofit-watch-050/sonda-qa.py` | rc 0. Ensaio preservou o bare, emenda invalidou a aprovação, publicação alinhou bare, status, registro e clone. Janela, revert e confirmação manual também passaram. |

`live_clone` continua leve e `_live_fetch` conserva a assinatura usada na
preparação e na porta. A exceção nova tem lançamento e captura ativos. Não há
símbolo ou importação órfã no delta. A busca fora do delta ficou restrita ao
contrato de chamada existente. Sem superfície visual alterada.
A distribuição nativa não foi reexecutada nesta sessão. O handoff de EXEC
registra as três provas nativas e a camada 1 no host Linux em `42042d1`, via
`ad65cf9`. Não se inferiu cobertura nativa dos três pulos locais.

### Overall Grade

| Criterion | Grade | Rationale |
|-----------|-------|-----------|
| Code Quality (Zen) | A | O predicado comum concentra a leitura curta e a exceção específica mantém explícita a recusa da busca. |
| Type Safety | A | O predicado só retorna booleano, a identificação conserva Path ou None e LiveBranchError continua sendo uma StoreError para os chamadores. |
| Error Handling | B | O setup libera uma cópia cujo ramo efetivo é outro, e o avanço confunde falha de leitura de HEAD com troca de ramo. |
| Security | A | A pré-varredura não encontrou credenciais. Os controles preservaram a origem e nenhuma das duas falhas provocou avanço no ramo errado. |
| Performance | A | A leitura de elegibilidade continua limitada a 64 bytes, sem subprocesso Git adicional, e a regressão de startup offline passou. |
| Test Coverage | B | Os dois casos da r9 ficaram verdes, mas as 149 regressões dirigidas não detectam a referência efetiva errada no setup nem a falha de leitura no segundo exame. |
| Documentation | A | O guia distingue arquivo simbólico e commit resolvido após bfbb9f8. README, guia e CHANGELOG apresentam o contrato de referência direta e descrevem o resultado da troca detectada antes do fetch. |
| **Overall** | **B** | O conserto de R15 e a correção editorial têm evidência, mas as duas falhas do delta exigem R16. |

## Achados da rodada

| # | Severidade | Achado | Onde |
|---|---|---|---|
| 1 | MEDIUM | O setup retira o marcador e libera a cópia quando HEAD aponta para `refs/heads/main`, mas essa ref é simbólica e resolve para outro ramo. O avanço então recusa o clone que o setup acabou de liberar. | `plugins/retrofit-watch/skills/retrofit-watch/scripts/rw_store.py:1065` |
| 2 | LOW | Se a leitura de HEAD falhar na revalidação pré-fetch, o avanço grava `fora-da-main` mesmo quando a cópia continua na main. | `plugins/retrofit-watch/skills/retrofit-watch/scripts/rw_store.py:953`, `plugins/retrofit-watch/skills/retrofit-watch/scripts/rw_store.py:1152` e `plugins/retrofit-watch/skills/retrofit-watch/scripts/rw_store.py:1192` |

**Reprodução com Git 2.43.0.** As sondas usaram `LiveTest` com bares locais e
não alteraram a árvore da missão. O contraste carregou o módulo gravado com
`git show aab91a606994ce33601fba4043d24847fa16829f:plugins/retrofit-watch/skills/retrofit-watch/scripts/rw_store.py > /tmp/review-r10.jJFbXK/rw_store_base.py`.
Para cada sonda abaixo, rode `env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp/review-r10.jJFbXK PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests REVIEW_BASE=0 python3 -B /tmp/review-r10.jJFbXK/<sonda>` no HEAD.
Repita com `REVIEW_BASE=1` para usar o módulo da base.

1. `symref.py`. Em clone pendente com a trava instalada, torne `refs/heads/main`
   simbólica para `refs/heads/rascunho` com o próprio Git. Os bytes de `.git/HEAD`
   não mudam. `git symbolic-ref --no-recurse HEAD` devolve `refs/heads/main`,
   e `git symbolic-ref HEAD` devolve `refs/heads/rascunho`. Na base, um teste
   passou, rc 0. O setup recusou o ramo, preservou o marcador e retomou após
   restaurar `main` como ref direta. No HEAD, um teste falhou, rc 1. O setup
   concluiu, retirou o marcador e `live_clone` passou a aceitar a cópia, mas
   `live_advance` registrou `fora-da-main`.
2. `head-io.py`. Após a inspeção inicial bem-sucedida, retire apenas a
   permissão de leitura de `.git/HEAD`. A sonda confirmou `PermissionError`.
   Após restaurar a permissão, os bytes e o ramo efetivo eram os mesmos.
   Nenhuma versão buscou ou moveu `origin/main`. No HEAD, um teste falhou,
   rc 1, com `fora-da-main` e `cópia em uso fora da main`. Na base o teste
   também ficou vermelho, mas no detalhe genérico `sem clone dedicado` do
   registro `erro`. A regressão desta rodada é afirmar que o ramo mudou
   quando a leitura falhou. A mensagem da base não é o resultado esperado.

Logs em `/tmp/review-r10.jJFbXK/`, incluindo
`symref-directed-0.log`, `symref-directed-1.log`, `head-io-final.log`,
`head-io-1.log`, `r15-base.log`, `test-cmd.log`, `clone.log`,
`related.log` e `qa.log`.

## Incrementos de conserto (R<n>)

| R<n> | Achado | Check escrito no checkpoint |
|---|---|---|
| R16 | Agrupa os achados 1 e 2. O setup recusa o ramo efetivo errado, preserva a pendência, mantém a cópia inelegível e retoma após normalizar a ref. A falha de leitura antes do fetch registra `erro` com detalhe de HEAD ilegível, preserva as refs e não busca. A jornada deve seguir verde. | `(env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -m unittest test_lean_live.LiveTest.test_setup_rejects_main_resolving_to_other_branch test_lean_live.LiveTest.test_advance_reports_unreadable_head_before_fetch >/dev/null && env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B docs/handoffs/20261127-retrofit-watch-050/sonda-qa.py >/dev/null); echo $?` → `0` |

## O que virou incremento

- Os dois achados reproduzidos no delta viraram `R16`. A ausência de subprocesso Git no
  caminho rápido de elegibilidade e o diagnóstico de ramo errado de R15 devem ser preservados.
- Os dois achados da r9 foram fechados em `4ea2ef0`. As regressões
  `test_setup_and_eligibility_agree_on_symbolic_main` e
  `test_advance_reports_branch_change_before_fetch` passaram no HEAD.
  `env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp/review-r10.jJFbXK PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B /tmp/review-r10.jJFbXK/r15-base.py`
  deu rc 1 com duas falhas em três testes ao carregar o módulo de `aab91a606994ce33601fba4043d24847fa16829f`.
  A base liberou o HEAD indireto, diagnosticou o ramo trocado como clone ausente
  e passou no controle de recusa da troca durante o setup.

```md
| R16 | Recusar no setup a main que resolve para outro ramo e distinguir HEAD ilegível no avanço | `(env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -m unittest test_lean_live.LiveTest.test_setup_rejects_main_resolving_to_other_branch test_lean_live.LiveTest.test_advance_reports_unreadable_head_before_fetch >/dev/null && env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B docs/handoffs/20261127-retrofit-watch-050/sonda-qa.py >/dev/null); echo $?` → `0` | pending | — |
```

## O que foi refutado

- «A referência indireta de HEAD para uma main efetiva continua aceita». No caso de
  R15, HEAD aponta para um atalho que resolve em main. O HEAD revisado recusou,
  preservou o marcador e concluiu após restaurar HEAD direto. O achado 1
  inverte a direção da indireção, que está em `refs/heads/main`.
- «O avanço agora busca mesmo ao detectar um ramo trocado». A regressão de
  R15 confirmou nenhum fetch e preservou as refs após a troca efetiva para
  `rascunho`. Já a sonda do achado 2 não mudou de ramo.
- «O teste de trava de R14 perdeu seu sensor ao trocar a consulta Git pela
  leitura direta». O teste adaptado passou com a troca de trava antes da
  verificação, registrou a recusa e confirmou a retomada com a trava restaurada.

## Achados fora de escopo

- Nenhum item novo. Permanecem no backlog a corrida depois da prova de
  ancestralidade e a remoção do marcador por caminho no Windows. A suíte ampla
  não foi repetida nesta rodada. O handoff de EXEC conserva a comparação em que os
  mesmos problemas de fixture apareceram na candidata e em `e184101`.
- A precisão editorial da r9 já tem resolução registrada por `bfbb9f8`.
  A alteração descreve o arquivo simbólico e ressalva que mudar de commit
  dentro da main pode deixar esse arquivo intacto.

## Pendências / Decisions for a Human

Nenhuma nova. O gate segue vermelho nos dois critérios estritos. Em relação à
r9, há melhora de Documentation, respaldada por `bfbb9f8`, sem queda de
outra letra. Não é platô de notas idênticas. A continuidade é EXEC para R16,
sem conserto na sessão de REVIEW.

### Ações recomendadas

**Corrigir obrigatoriamente (CRITICAL)**

Nenhuma.

**Corrigir com prioridade (HIGH)**

Nenhuma.

**Corrigir ou considerar (MEDIUM/LOW)**

- Cobrar no setup tanto HEAD direto quanto a confirmação do ramo efetivo, sem
  relaxar a validação de origem e trava. No avanço, distinguir a leitura
  malsucedida de uma troca de ramo observada e manter a recusa antes do fetch.

_Cost footprint: codereview v2.27.38 da cópia solicitada, instalação Claude registrada em 2.30.2.
Dois agentes gpt-6.1-terra leram sete documentos, duas chamadas cada. Código, testes e varredura
de órfãos no agente principal._
