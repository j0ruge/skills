---
missao: 20261127-retrofit-watch-050
fase: REVIEW
rodada: 9
status: done
sessao: 01a221de-3c9c-7d93-81e3-50ce2dc17c0f
data: 2026-11-28 08:20
gate: "Em aab91a606994ce33601fba4043d24847fa16829f, env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp PYTHONDONTWRITEBYTECODE=1 bash -c 'source .sdd/config.sh; eval \"$TEST_CMD\"' → rc 0. Adaptadores, catálogo e versões válidos. 154 testes da loja, três nativos pulados pela configuração, e 144 do Stop sem pulos. Árvore limpa durante a medição. O gate de REVIEW não passou. Error Handling e Test Coverage permaneceram em B após R14. Platô frente à r8, com R15 pendente e decisão de continuidade para o humano."
reviewed_head: aab91a606994ce33601fba4043d24847fa16829f
---

# Review — rodada r9 — Retrofit de skills locais com ensaio antes do push autônomo

## TL;DR

R14 fechou os dois casos da r8. A suíte configurada, 118 regressões dirigidas e a jornada de QA passaram.
A r9 confirmou dois problemas no delta. O setup pode liberar uma cópia que depois se declara ausente,
e o avanço pode informar clone ausente quando o ramo muda antes da busca. Ambos viraram R15.
Nota geral B. Error Handling e Test Coverage continuam em B. O platô deixa a continuidade para decisão humana.

## Nota da rodada

Escopo `base=5419786e6a7124ac03ff6188ae66b25347c19c58`, até `aab91a606994ce33601fba4043d24847fa16829f`. O delta traz seis documentos revisados,
um arquivo de produto (`rw_store.py`), seu teste alterado (`test_lean_live.py`)
e as notas de execução, excluídas da leitura conforme o boot. O commit de produto
que fecha R14 é `680d355`. A jornada de `30-handoff-qa.md` serviu de controle.

### Secrets Detection

| Arquivo | Linha | Tipo | Severidade |
|---|---|---|---|
| Nenhum | — | — | — |

PASS. Varredura do delta permitido com regex e Gitleaks, oito arquivos e 264 linhas
adicionadas, sem achados nem erros. Os casos desta revisão usaram remotos bare locais.

### Qualidade, segurança e desempenho

O argumento nomeado ficou restrito às chamadas que precisam distinguir identificação
de elegibilidade. A consulta da trava fica no setup explícito. A leitura de elegibilidade
continua sem subprocesso e lê no máximo 64 bytes adicionais. A prova de startup com rede
indisponível passou. Não houve nova escrita em refs nem publicação nos dois Reds.

### Test Coverage

| Verificação | Evidência |
|---|---|
| TEST_CMD no HEAD | Comando no campo `gate`. 154 testes da loja (3 pulados) e 144 do Stop. |
| Regressões dirigidas no HEAD | `env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -m unittest test_lean_live test_lean_auto test_lean_batch test_lean_gate test_lean_window` → 118/118, sem pulos, em 51,662 s. |
| R14 na base e no HEAD | `controle-r14.py` executou as três provas nomeadas no Check. Duas falharam pelas asserções esperadas na base e a prova de restauração de R13 passou. No HEAD, 3/3 passaram. |
| Jornada de QA no HEAD | `env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B docs/handoffs/20261127-retrofit-watch-050/sonda-qa.py` → rc 0. Ensaio e emenda preservaram o bare. A nova aprovação alinhou bare, status capturado, registro e clone. Janela cumprida, reset por revert e publicação manual com e sem confirmação também passaram. |
| Dois Reds novos no HEAD | `red-r15.py` executou exatamente dois casos, ambos vermelhos por asserção de comportamento. |
| Plataformas | Sem prova nativa Windows ou macOS. A distribuição Linux consta no handoff do executor em `0ce205b`, com execução no host em `66dd118`. Não foi repetida nesta rodada. |

### Documentation Sync

A descrição de elegibilidade durante a liberação corresponde aos casos de R14.
O guia ainda usa `HEAD` com alcance maior que o demonstrado. A precisão editorial
já consta no backlog. O diagnóstico de avanço prometido no handoff continua correto
quando o ramo já estava errado na primeira consulta, mas não no intercalamento do achado 2.

### Código morto

Varredura do delta sem arquivo, importação ou símbolo órfão. A busca dos chamadores de
`live_clone` e `_private_clone` não encontrou incompatibilidade na forma de chamada.
A varredura de código preexistente ficou fora do escopo.

### Overall Grade

| Criterion | Grade | Rationale |
|-----------|-------|-----------|
| Code Quality (Zen) | A | A leitura é limitada, o descritor fecha no contexto e a exceção de identificação tem uma chamada explícita. |
| Type Safety | A | O argumento opcional é booleano e nomeado. O caminho continua sendo Path ou None na leitura e Path ou erro na operação. |
| Error Handling | B | O setup confirma uma cópia que a leitura seguinte não reconhece, e uma troca de ramo antes da busca produz um diagnóstico de clone ausente. |
| Security | A | Varredura sem credenciais. Nos casos medidos, não houve escrita no ramo incorreto nem publicação fora do destino previsto. |
| Performance | A | A elegibilidade faz uma leitura curta sem Git adicional e o teste de startup offline passou. |
| Test Coverage | B | R14 passou contra dois Reds da base, mas as 118 regressões não cobrem as duas falhas de contrato reproduzidas nesta rodada. |
| Documentation | B | A prosa do guia ainda não limita a garantia de mudança de HEAD ao estado simbólico observado. |
| **Overall** | **B** | R14 fecha os dois casos anteriores. Os dois Reds do delta mantêm os critérios estritos abaixo do aceite. |

## Achados da rodada

| # | Severidade | Achado | Onde |
|---|---|---|---|
| 1 | MEDIUM | O setup libera a cópia cuja referência simbólica resolve para a `main`, mas a elegibilidade lê apenas o formato direto de `HEAD`. O setup informa sucesso, remove a pendência e a cópia não é reconhecida nem avança. | `plugins/retrofit-watch/skills/retrofit-watch/scripts/rw_store.py:957`, `plugins/retrofit-watch/skills/retrofit-watch/scripts/rw_store.py:1058` |
| 2 | LOW | Uma troca de ramo depois da primeira inspeção e antes da busca conserva o HEAD, mas grava `erro` e `sem clone dedicado` para a cópia que acabou de identificar. | `plugins/retrofit-watch/skills/retrofit-watch/scripts/rw_store.py:433`, `plugins/retrofit-watch/skills/retrofit-watch/scripts/rw_store.py:1170` |
| 3 | LOW | O guia ainda não distingue o arquivo simbólico do SHA resolvido de `HEAD`. É o mesmo item editorial da r8, sem alteração do requisito de produto. | `docs/retrofit-watch/clone-dedicado.md:17` |

**Reprodução e controles.** Usei Git 2.43.0 e `LiveTest` em `PrivateWorld`. Os
comandos abaixo usam o HEAD desta rodada. Para o contraste, gravei o módulo de
`git show 5419786e6a7124ac03ff6188ae66b25347c19c58:plugins/retrofit-watch/skills/retrofit-watch/scripts/rw_store.py` em `/tmp/review-r9.nMHJfa/rw_store-base.py` e carreguei
esse módulo em novo processo, com `REVIEW_BASE_SOURCE` apontando para a cópia.
Não troquei a árvore da missão.

1. Na retomada, uma referência simbólica criada pelo próprio Git apontava indiretamente
   para `main`. `git symbolic-ref -q HEAD` devolveu `refs/heads/main` e a trava veio do
   worktree. O setup retornou o destino e removeu o marcador. No HEAD,
   `live_clone` devolveu `None` e `live_advance` registrou `erro` com `sem clone dedicado`.
   A base reconheceu o mesmo estado e o avanço retornou `ok`. Com o formato canônico
   de `HEAD`, o controle ficou elegível nas duas versões.
2. A sonda disparou um `git switch` local para `rascunho` após a inspeção inicial
   bem-sucedida de `live-advance`, antes da busca. O HEAD e a ref local `origin/main`
   ficaram intactos. A segunda identificação, que agora exige a `main` por padrão,
   registrou `erro` em vez de `fora-da-main`. Na base, a busca atualizou a ref local
   `origin/main`, a segunda inspeção identificou o ramo incorreto e não houve merge.
   O diagnóstico deve voltar sem reintroduzir a busca no cenário medido.
3. A leitura independente do guia confirmou que a frase continua no presente e
   sem a distinção já medida pela r8. Não se propõe uma nova trava para alterações
   do SHA na mesma `main`.

Saídas em `/tmp/review-r9.nMHJfa/delta-head.log`, `delta-base.log`,
`r14-head.log` e `r14-base.log` no mesmo diretório. Para reproduzir a caracterização,
rode `env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp/review-r9.nMHJfa PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B /tmp/review-r9.nMHJfa/sonda-delta.py`.
No mesmo ambiente, `python3 -B /tmp/review-r9.nMHJfa/red-r15.py` executou dois casos
e saiu com rc 1. O primeiro acusou sucesso sem elegibilidade. O segundo acusou
`erro` em vez de `fora-da-main`.

## Incrementos de conserto (R<n>)

| R<n> | Achado | Check escrito no checkpoint |
|---|---|---|
| R15 | Achados 1 e 2. Setup e elegibilidade concordam sobre a cópia com referência recursiva resolvida para main. Se não suportada, a recusa é explícita, preserva a pendência e permite retomar com HEAD canônico. O avanço relata o ramo trocado sem buscar nem mover refs. A jornada de QA deve passar. | `(env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -m unittest test_lean_live.LiveTest.test_setup_and_eligibility_agree_on_symbolic_main test_lean_live.LiveTest.test_advance_reports_branch_change_before_fetch >/dev/null && env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B docs/handoffs/20261127-retrofit-watch-050/sonda-qa.py >/dev/null); echo $?` → `0` |

## O que virou incremento

- Achados 1 e 2 da r9 viraram `R15`. O Check exige dois testes dirigidos e a jornada.
- Achados 1 e 2 da r8 foram fechados em `680d355`. Nas mesmas três provas, a base perdeu
  as asserções de inelegibilidade intermediária e recusa da trava, mas preservou o controle de R13.
  No HEAD, as três passaram.

```md
| R15 | Alinhar a liberação e a elegibilidade ao conferir o ramo e preservar o diagnóstico do avanço | `(env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -m unittest test_lean_live.LiveTest.test_setup_and_eligibility_agree_on_symbolic_main test_lean_live.LiveTest.test_advance_reports_branch_change_before_fetch >/dev/null && env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B docs/handoffs/20261127-retrofit-watch-050/sonda-qa.py >/dev/null); echo $?` → `0` | pending | — |
```

## O que foi refutado

- «R14 só restaura o marcador e continua aceitando o ramo errado na janela intermediária».
  A primeira regressão mediu o instante sem marcador. A base devolveu o caminho e o HEAD devolveu
  `None`. A pendência restaurada também passou no caso de controle.
- «A mudança da trava durante a consulta de ramo continua liberando o clone».
  A base não levantou `StoreError`. O HEAD recusou a trava alterada e retomou com a
  configuração restaurada, como exige a segunda regressão de R14.
- «O ramo já errado no início do avanço perdeu o diagnóstico». O caso
  `test_advance_leaves_wrong_branch_dirty_tree_and_divergence_alone` passou no HEAD
  e confirmou `fora-da-main`. O achado 2 exige a troca depois da primeira inspeção.

## Achados fora de escopo

- Achado 3 já registrado em `TODO.md`, seção **Clone dedicado da retrofit-watch**.
  É a mesma missão da primeira ocorrência. A gramática de recorrência não acrescenta
  outra ocorrência para a mesma missão. Nenhum item foi duplicado.
- A troca de destino na remoção do marcador no Windows e a corrida do avanço depois
  da prova de ancestralidade continuam no backlog. O achado 2 é anterior ao fetch e
  não alcançou a etapa de merge.

## Pendências / Decisions for a Human

As notas ficaram iguais às da r8. Error Handling e Test Coverage continuam em B
apesar do conserto demonstrado em `680d355`. O gate registra o platô e esta revisão
não inicia outra rodada. Cabe ao responsável decidir se encaminha R15 para EXEC.

### Ações recomendadas

**Corrigir obrigatoriamente (CRITICAL)**

Nenhuma.

**Corrigir com prioridade (HIGH)**

Nenhuma.

**Corrigir ou considerar (MEDIUM/LOW)**

- Em R15, cobrar coerência entre setup e elegibilidade sem relaxar a recusa de ramo errado
  nem trazer Git para a leitura rápida de elegibilidade. No avanço, distinguir a troca de ramo
  de um clone ausente, sem buscar nem tocar nas refs no caso reproduzido.
- Manter a precisão editorial sobre HEAD no backlog, sem nova rodada por prosa.

_Cost footprint: codereview v2.27.38 da cópia solicitada. O registro do Claude indica v2.30.2 e inclui roteamento de verificação de prosa ausente na cópia pedida. Dois agentes gpt-6.1-terra para seis documentos, com 3 e 10 chamadas informadas. Código, testes e varredura de órfãos analisados na sessão principal._
