---
missao: 20261127-retrofit-watch-050
fase: REVIEW
rodada: 8
status: done
sessao: 01a221cc-56c6-77a0-ac23-6c77398c7587
data: 2026-11-28 08:01
gate: "Em 5419786e6a7124ac03ff6188ae66b25347c19c58, env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp/review-r8.jt0X0V PYTHONDONTWRITEBYTECODE=1 bash -c 'source .sdd/config.sh && eval \"$TEST_CMD\"' → rc 0, com adaptadores e catálogo válidos, 154 testes da loja (3 pulados), 144 do Stop e validação de versões. Árvore limpa durante a medição. Gate de REVIEW não passou. Error Handling e Test Coverage permanecem em B; Documentation caiu de A para B por uma promessa ambígua. R14 pendente."
reviewed_head: 5419786e6a7124ac03ff6188ae66b25347c19c58
---

# Review — rodada r8 — Retrofit de skills locais com ensaio antes do push autônomo

## TL;DR

R13 fechou as duas reproduções da r7 e a suíte passou. A r8 confirmou duas falhas na liberação do clone que viraram R14.
Uma leitura intermediária ainda aceita a cópia fora da `main`. Uma edição concorrente da trava pode deixar um sucesso sem hook efetivo.
Nota geral B. As notas estritas não subiram. Uma precisão editorial sobre `HEAD` foi para o backlog.

## Nota da rodada

Revisão delta de `31121ec9c32753fef955eda376d18e2c26d828b4` a `5419786e6a7124ac03ff6188ae66b25347c19c58`, na branch `feat/retrofit-watch-050-loja`. Seis commits, oito arquivos no resumo de Git, +229/−34. A análise direta cobriu sete arquivos (um Python de produto, um de testes e cinco documentos). Não abri as notas de checkpoint, cuja cauda veio do runner. O conteúdo de produto em `plugins/` é idêntico ao de `ea37315` (`git diff --quiet ea37315 HEAD -- plugins` → rc 0). A amostra de QA usa apenas bares locais e HOME isolado.

### Secrets Detection

| Arquivo | Linha | Tipo | Severidade |
|---|---|---|---|

**PASS** no delta analisado. Regex e gitleaks leram 227 linhas adicionadas nos sete arquivos do escopo direto, sem achados ou erros.

### Qualidade, segurança e desempenho

O delta separa a identificação física do clone da versão do arquivo simbólico `.git/HEAD`. A remoção POSIX continua ancorada no descritor e os testes de substituição do checkout e do `.git` passaram. A comparação nova não é uma transação que inclua a publicação da elegibilidade ou a vigência da configuração do hook. As reproduções são inconsistências locais do setup. Não mostram publicação incorreta, acesso externo ou vazamento. O custo adicional está no setup explícito. O teste de startup offline passou na execução dirigida. Não há interface gráfica, mudança de esquema ou dependência nova no delta.

### Test Coverage

| Verificação | Evidência |
|---|---|
| TEST_CMD no HEAD | Comando integral no campo `gate`. Adaptadores, catálogo e versões passaram. Loja 154 testes, três provas nativas puladas por configuração do sandbox, Stop 144 testes sem pulos. |
| Setup e controles | Com `GIT_DIR` e `GIT_WORK_TREE` desarmados, `TMPDIR` isolado sob `/tmp` e `PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests`, `python3 -B -m unittest -v test_lean_live` passou 49/49 em 13,450 s. Inclui os três testes de R13, os controles de R10/R12 e startup offline. |
| Jornada de QA no HEAD | No mesmo tipo de ambiente, `python3 -B docs/handoffs/20261127-retrofit-watch-050/sonda-qa.py` → rc 0. A sonda reteve o bare no ensaio e após emendar o patch, e alinhou bare, `local/ci` capturado, registro e clone após nova aprovação. Também passou janela cumprida, reset por revert e os controles manuais com e sem confirmação. |
| Red independente de R14 | Dois casos executados, dois vermelhos comportamentais. O primeiro observou o caminho da cópia em vez de `None` durante a liberação. O segundo não recebeu `StoreError`. Mais detalhes nos achados. |
| Escopo das provas | Sem execução nativa Windows ou macOS, sem serviço iniciado e sem adoção privada. A distribuição Linux está documentada pelo executor em `ea37315`, não foi reexecutada nesta sessão. |

### Documentation Sync

O handoff do executor já lista os 17 Checks e orienta começar por R12 e R13. A nota sobre a mudança de `HEAD` no guia do clone é mais ampla do que a assinatura do arquivo simbólico consegue mostrar. Esse ajuste editorial não exige fazer o setup rejeitar toda mudança de SHA na `main`.

### Código morto

Nenhum símbolo órfão no delta. Os auxiliares novos têm chamadas locais, e a busca pela assinatura anterior de `_finish_live_setup` encontrou apenas declaração, chamada de produto e dois usos no teste já atualizados. `ruff check --no-cache --select F401,F821,F841` passou nos dois arquivos Python. Legado fora da varredura.

### Overall Grade

| Criterion | Grade | Rationale |
|-----------|-------|-----------|
| Code Quality (Zen) | A | A identidade física e a versão do arquivo simbólico são verificadas separadamente, com descritor fechado em todos os caminhos medidos. |
| Type Safety | A | Os formatos de identidade e os bytes do marcador são consistentes entre a instalação, a verificação e os chamadores atualizados. |
| Error Handling | B | A recusa pode ser precedida por elegibilidade observável, e uma trava alterada durante a validação pode resultar em sucesso. |
| Security | A | A varredura não apontou credenciais e a prova local não demonstrou acesso ou publicação fora da origem autorizada. |
| Performance | A | As novas leituras pertencem ao setup explícito e o controle de startup offline passou. |
| Test Coverage | B | Os 49 testes e a jornada passaram, mas os dois Reds independentes mostram lacunas na observação durante a liberação. |
| Documentation | B | O boot anterior foi corrigido, mas o guia deixa entender que toda mudança no SHA resolvido de HEAD é detectada. |
| **Overall** | **B** | R13 corrige os falsos sucessos anteriores nas fronteiras medidas, mas os dois achados de liberação ainda impedem o aceite técnico. |

## Achados da rodada

| # | Severidade | Achado | Onde |
|---|---|---|---|
| 1 | MEDIUM | A cópia fora da `main` fica transitoriamente elegível entre a remoção do marcador e a restauração posterior. O comando termina em erro, mas isso não desfaz a leitura feita no intervalo. | `plugins/retrofit-watch/skills/retrofit-watch/scripts/rw_store.py:1040` e `plugins/retrofit-watch/skills/retrofit-watch/tests/test_lean_live.py:499` |
| 2 | MEDIUM | A consulta de ramo foi movida para depois da validação da trava. Uma edição de configuração durante essa consulta libera o clone na `main` sem o hook efetivo e sem aviso. | `plugins/retrofit-watch/skills/retrofit-watch/scripts/rw_store.py:1051` e `plugins/retrofit-watch/skills/retrofit-watch/scripts/rw_store.py:1057` |
| 3 | LOW | O guia não distingue a mudança do ramo apontado por `.git/HEAD` de uma mudança de SHA no mesmo ramo. É um ajuste de prosa, sem requisito novo de bloquear atualizações de SHA. | `docs/retrofit-watch/clone-dedicado.md:16` |

**Reprodução e controles.** Usei `LiveTest._leave_pending_setup` e Git 2.43.0 em `PrivateWorld`. As interceptações só coordenaram operações locais reais. Para o controle da base, carreguei o mesmo módulo de `git show 31121ec9c32753fef955eda376d18e2c26d828b4:plugins/retrofit-watch/skills/retrofit-watch/scripts/rw_store.py` em processo separado, sem trocar a árvore.

- **1.** Na remoção do marcador por descritor, troquei o checkout de fixture para `rascunho` e fiz uma leitura de `live_clone` depois do unlink real, antes da verificação seguinte. Os pares `(marcador presente, elegível)` foram `(sim, não)`, `(não, sim)` e `(sim, não)`. O setup terminou com erro de ramo e restaurou os bytes. Na base, a mesma troca retornava sucesso e a cópia continuava elegível. A melhora de R13 é real, mas o teste novo observa só o último estado.
- **2.** Ao iniciar a consulta de ramo, alterei `core.hooksPath` do worktree de fixture para um diretório vazio. No HEAD a ordem medida foi trava, ramo. O setup devolveu o destino, na `main`, sem marcador e elegível, e o novo diretório efetivo não continha o hook. Na base a ordem foi ramo, trava. A mesma edição causou erro de trava, preservou os bytes do marcador e manteve a cópia inelegível.
- **3.** Com dois commits locais na fixture, um reset suave para o outro commit durante a validação mudou o resultado de `rev-parse HEAD`. A assinatura de `.git/HEAD` não mudou, o ramo continuou `main` e o setup retornou sucesso. Isso delimita a garantia implementada, sem provar que a origem ou a trava deixaram de valer.

As duas primeiras caracterizações e o controle da base estão em `/tmp/review-r8.jt0X0V/sonda-delta.py`, com as saídas em `delta-head.log` e `delta-base.log` no mesmo diretório. Com a mesma variável `PYTHONPATH` da suíte dirigida, `env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp/review-r8.jt0X0V PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B /tmp/review-r8.jt0X0V/red-r14.py` executou os dois Reds e saiu com rc 1 por duas falhas de asserção.

## Incrementos de conserto (R<n>)

| R<n> | Achado | Check escrito no checkpoint |
|---|---|---|
| R14 | Achados 1 e 2 em lote. O caso 1 precisa observar a inelegibilidade durante a liberação, além da recusa e dos bytes ao final. O caso 2 precisa acusar a alteração da trava, manter a pendência e permitir a retomada depois de restaurar a configuração. | `(env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -m unittest test_lean_live.LiveTest.test_setup_stays_ineligible_during_branch_change_at_marker_removal test_lean_live.LiveTest.test_setup_rejects_hook_change_during_branch_validation test_lean_live.LiveTest.test_setup_keeps_pending_if_branch_changes_at_marker_removal >/dev/null && env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B docs/handoffs/20261127-retrofit-watch-050/sonda-qa.py >/dev/null); echo $?` → `0` |

## O que virou incremento

- R14 foi anexado ao checkpoint com a linha abaixo. O Check exige os dois testes novos, o controle de restauração de R13 e a jornada de QA.
- R7, achados 1 e 2, tratados em `8fbee04` e fechados em `ea37315`. As regressões de origem validada em outro ramo, troca durante a leitura dos hooks e estado final após troca na remoção passaram no HEAD.
- R7, achado 3, não voltou. A tabela já registra 17 Checks e o boot de QA começa em R12 e R13. As mudanças estão em `1341fee` e `3ff90c3`.

```md
| R14 | Manter o clone inelegível até confirmar ramo e trava na liberação | `(env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -m unittest test_lean_live.LiveTest.test_setup_stays_ineligible_during_branch_change_at_marker_removal test_lean_live.LiveTest.test_setup_rejects_hook_change_during_branch_validation test_lean_live.LiveTest.test_setup_keeps_pending_if_branch_changes_at_marker_removal >/dev/null && env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B docs/handoffs/20261127-retrofit-watch-050/sonda-qa.py >/dev/null); echo $?` → `0` | pending | — |
```

## O que foi refutado

- «R13 não mudou o resultado da troca na remoção». A base retornou sucesso e não refez o marcador. No HEAD o setup devolveu erro, restaurou os bytes e voltou a negar elegibilidade. O achado 1 mede o que fica visível antes dessa restauração.
- «A configuração condicional ao ramo da r7 ainda libera o clone». A regressão correspondente trocou de `rascunho` para `main` após a consulta de origem, recebeu erro, manteve a pendência e conseguiu retomar após retirar a configuração condicional.
- «Uma mudança de SHA na mesma `main` exige um Red de código». A fixture mudou o SHA sem mudar o ramo, a origem ou a trava. O contrato desta missão exige o ramo correto e a trava ativa. O alcance da frase no guia é a pendência editorial do achado 3.

## Achados fora de escopo

- Achado 3 registrado em `TODO.md`, seção **Clone dedicado da retrofit-watch**, em 2026-11-28. É uma precisão editorial, sem incremento novo.
- A troca de destino na remoção por caminho no Windows e a corrida de `live-advance` após a prova de ancestralidade já estão no backlog. Não houve reprodução nova desses dois itens nesta rodada.

## Pendências / Decisions for a Human

Error Handling e Test Coverage ficaram no mesmo B da r7 e Documentation caiu de A para B. O gate registra o platô dos critérios estritos e a regressão de prosa. A revisão não dá aceite nem inicia outra rodada. Cabe decidir a continuidade com R14 já registrado para EXEC. A adoção em repos privados continua fora da missão.

### Ações recomendadas

**Corrigir obrigatoriamente (CRITICAL)**

Nenhuma.

**Corrigir com prioridade (HIGH)**

Nenhuma.

**Corrigir ou considerar (MEDIUM/LOW)**

- Em R14, verificar a elegibilidade dentro do intercalamento e a trava efetiva antes de devolver sucesso. Preservar o controle íntegro e a retomada.
- No backlog, explicitar que a guarda compara o arquivo simbólico e não o SHA resolvido da `main`.

_Cost footprint da revisão: codereview v2.27.38 da cópia pedida. A instalação do Claude registra v2.30.2. Um arquivo de produto, análise e varredura inline, zero subagentes. O modelo de delegação previsto pela skill não estava disponível._
