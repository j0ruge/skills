---
missao: 20261125-retrofit-watch-atribuicao
fase: REVIEW
rodada: 13
status: done
sessao: 01a21ee2-de2f-7952-93f7-f0835316ac1f
data: 2026-11-27 18:29
gate: 'Em 91a7b7d5b6b0f58abfcbcb569ba423d2088d6790, com árvore limpa, env -u GIT_DIR -u GIT_WORK_TREE PYTHONDONTWRITEBYTECODE=1 bash -c ''source .sdd/config.sh && eval "$TEST_CMD"'' → rc 0. Adaptadores e catálogo válidos, 154 testes da loja (3 pulados), 114 do hook e versão 0.4.1 válida. 14/14 Checks com rc 0 e stdout esperado. A sonda de R12 falhou na base e passou no HEAD. Gate de revisão atendido pelas notas desta rodada.'
reviewed_head: 91a7b7d5b6b0f58abfcbcb569ba423d2088d6790
---

# Review — rodada r13 — Atribuição da retrofit-watch por mensagem

Revisão do delta de `a07b8fdd1ef790aaa9ae268dab8d25243877fc0a` a
`91a7b7d5b6b0f58abfcbcb569ba423d2088d6790` na branch
`fix/retrofit-watch-atribuicao-mesma-mensagem`. Seis commits, um módulo Python,
um arquivo de testes e sete caminhos de documentação ou execução. A QA em
`08f09a1` cobriu o BUG-01. O Check de F1 voltou a exercitar os três controles
em dois Stops.

## TL;DR

R12 fechou em `d77e6a1`. O falso pedido de retro foi reproduzido na base e ficou em silêncio no HEAD, com avanço do offset.
Cargas novas com vínculo, slash explícito e atribuição já ativa continuaram funcionando.
A suíte, os 14 Checks e quatro mutações independentes confirmaram o resultado.
Nota A em todos os critérios. Nenhum novo incremento e nenhum código alterado.

## Nota da rodada

### Secrets Detection

**Status: PASS no escopo lido.** O pré-scan `regex` e `gitleaks` leu oito caminhos
e 394 linhas adicionadas, sem ocorrências ou erros. O nono caminho é o registro
append-only de execução, excluído da leitura pelo protocolo da missão.

~~~bash
git diff a07b8fdd1ef790aaa9ae268dab8d25243877fc0a...HEAD --unified=0 -- . ':(exclude)docs/handoffs/20261125-retrofit-watch-atribuicao/checkpoint-notas.md' | bash /home/joruge/.agents/skills/codereview/scripts/scan_secrets.sh
~~~

### Zen, erros e integridade de estado

A decisão usa o encerramento que existia antes do replay para distinguir o
estado persistido da proteção provisória. Retornos antecipados deixam o
fallback no estado real, sem importar vínculos parciais. Uma leitura completa
e compatível ainda pode substituí-lo. O delta não muda chaves do JSON, código de
trava, permissões, caminhos de escrita nem o contrato de saída do hook.

### Cobertura e documentação

| Módulo | Estado | Evidência |
|---|---|---|
| `retrofit_watch.py` | WITH_TESTS | `test_retrofit_watch.py` ganhou sete variantes de R12. A jornada de terminal usa a 0.4.0 real, arquivos de estado e subprocessos. |

README, CHANGELOG e SKILL descrevem o descarte da reconstrução parcial e o
silêncio sem vínculo quando não há atribuição ativa. A validação de versões e
o teste de release confirmaram a 0.4.1. Sem mudança de interface, dependências
ou distribuição. A função interna de reconstrução já documenta no corpo por
que compara o replay com a atribuição gravada.

### Varredura de símbolos

Bucket A sem órfãos. `was_closed` é lido na inicialização e na validação do
replay. O teste novo é descoberto pelo `unittest` e nomeado no Check de R12.
Nenhuma interface foi renomeada. Bucket B não varrido.

### Overall Grade

| Criterion | Grade | Rationale |
|-----------|-------|-----------|
| Code Quality (Zen) | A | O replay separa a evidência persistida do fechamento provisório e preserva os controles de atribuição. |
| Type Safety | A | O delta reutiliza estados booleanos e a comparação explícita com None, sem mudar o formato JSON. |
| Error Handling | A | O fallback persiste sem creditar metadado antigo ou importar estado parcial após leitura incompleta. |
| Security | A | Pré-scan limpo no escopo lido. O delta não amplia acesso ao transcript nem muda a trava ou a escrita do estado. |
| Performance | A | A célula R11 voltou a avançar após um registro de 96 MiB sob teto de 256 MiB. R12 acrescenta apenas decisões escalares. |
| Test Coverage | A | A suíte e os 14 Checks passaram. As duas regressões selecionadas detectaram quatro mutações independentes. |
| Documentation | A | README, CHANGELOG e SKILL descrevem o fallback medido. Receitas e notas da rodada foram conferidas no seu escopo. |
| **Overall** | **A** | R12 impede o falso pedido na migração e não altera os controles positivos. Nenhum novo defeito confirmado. |

## Achados da rodada

Nenhum achado confirmado no delta.

## Incrementos de conserto (R<n>)

Nenhum. Os 14 incrementos permanecem em `done`.

## O que virou incremento

R12 foi fechado pelo executor em `d77e6a1`. Na base, o metadado de
`graphify` sem vínculo disponível acima de 2 MiB gerou a retro indevida,
com ou sem o Stop intermediário. No HEAD, os dois casos ficaram em silêncio
e o offset chegou ao fim. No limite exato manteve o silêncio. Acima dele,
a carga com vínculo novo e o slash explícito pediram `graphify`.
A regressão executou um teste com sete variantes e rc 0.

## O que foi refutado

- **A receita do handoff teria aspas escapadas que impedem executar
  `TEST_CMD`.** A leitura byte a byte de `20-handoff-exec.md:7`, `:27`
  e `:260` encontrou zero pares de barra invertida e aspas duplas. O
  comando da linha 27 é idêntico ao executado nesta rodada com rc 0. Na
  linha 7, aspas simples duplicadas pertencem à representação YAML e
  não passam ao Bash como parte da receita.
- **O fallback bloquearia toda atribuição após uma leitura incompleta.**
  R12 manteve o pedido para carga com vínculo novo e slash explícito.
  Uma jornada adicional com estado gravado pela 0.4.0 e registro acima
  do teto manteve `codereview` ativo entre Stops e pediu retro para o
  trabalho posterior. Uma leitura válida sem externa também permitiu
  confirmar a chamada pendente na regressão permanente.
- **Os testes poderiam passar com a proteção desativada.** Quatro
  mutações isoladas deram rc 1 por falha de asserção. As mesmas duas
  regressões passaram antes e depois, com dois testes por execução.

## Achados fora de escopo

Nenhum achado novo para o backlog. Não foram reabertos os itens já
registrados de âncoras e preservação de saídas históricas.

## Pendências / Decisions for a Human

Nenhuma decisão de produto ou de implementação nova. O merge continua a
cargo do mantenedor. Em relação a r12, Code Quality (Zen), Error Handling e
Test Coverage subiram de B para A com a correção `d77e6a1`. Documentation e
Overall também subiram de B para A. Os demais critérios ficaram em A.
Não houve platô ou regressão.

## Evidências reproduzíveis

Todos os retestes do checkout rodaram no `reviewed_head`, com `GIT_DIR`
e `GIT_WORK_TREE` removidos nas jornadas. O comando completo da suíte está no
campo `gate`. Cada célula `done` de `checkpoint.md` foi executada da raiz
com `bash -c`, usando o comando literal da célula. Os 14 retornaram rc 0
e todo o stdout bateu com o esperado após normalizar apenas espaços em branco.
I1 deu `1 0 1 0 0 1` e F1 manteve o silêncio para ID válido, ausente e vazio.

A sonda abaixo troca apenas o binário de migração para a base do delta
na segunda execução. A opção `--base` original de r12 aponta para a
base daquela rodada, não para a base de r13.

~~~bash
p=docs/handoffs/20261125-retrofit-watch-atribuicao/40-review-r12.md
s=plugins/retrofit-watch/skills/retrofit-watch
probe=$(sed -n '/^~~~python$/,/^~~~$/{ /^~~~/!p; }' "$p")
env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH="$s/tests" python3 -B -c "$probe" --expect
probe_r13=${probe/5506df4dd27b2bda8f19b0f47424a6cf0c3192a4/a07b8fdd1ef790aaa9ae268dab8d25243877fc0a}
env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH="$s/tests" python3 -B -c "$probe_r13" --expect --base
env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH="$s/tests" python3 -B -m unittest test_auto_docs.ReleaseTest.test_the_four_places_agree_at_0_4_0_or_later
~~~

| Execução | rc | No limite | Acima, atrasado | Acima, após Stop | Acima, carga nova | Acima, slash |
|---|---|---|---|---|---|---|
| Base do delta | 1 | silêncio | graphify | graphify | graphify | graphify |
| HEAD revisado | 0 | silêncio | silêncio | silêncio | graphify | graphify |

O teste de release executou um caso e retornou rc 0. A jornada adicional
com JSON inválido no prefixo, salvo pela 0.4.0, confirmou o mesmo fallback
após um Stop sem trabalho. No HEAD, metadados atrasados com ID e sem ID
ficaram em silêncio. Na base, os dois pediram `graphify`. Carga nova e slash
pediram `graphify` nas duas versões. O offset avançou em todas as variantes.
Os Stops de migração usaram teto de 256 MiB.

As mutações foram feitas só em uma cópia descartável do módulo e do teste,
com os diretórios `scripts/` e `tests/` lado a lado. O comando foi executado
em grupo de processos próprio, com teto de 256 MiB e timeout de 20 s.

~~~bash
env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH=tests python3 -B -m unittest -q test_retrofit_watch.StopTest.test_legacy_oversized_replay_does_not_reopen_from_delayed_metadata test_retrofit_watch.StopTest.test_legacy_pending_call_order
~~~

| Alteração isolada na cópia | rc | Subcasos que falharam |
|---|---|---|
| Remover a atribuição do fallback | 1 | `delayed`, `resumed` |
| Forçar fechamento também com atribuição ativa | 1 | `active` |
| Retirar a proteção do encerramento persistido na comparação | 1 | `cache_only` |
| Comparar o fechamento provisório em vez do persistido | 1 | `no_external`, `alone` |
| Controles antes e depois, sem mutação | 0 | Nenhum |

Não houve smoke no host Claude Code nem no Windows. A suíte da loja manteve
os três pulos configurados para distribuição nativa.

## Boot da próxima fase

Não há R13 nem retorno a EXEC por achado desta rodada. Validar o checkpoint
e este relatório no gate externo. Para repetir a evidência de atribuição,
partir do Check de R12 e do relato de QA referente a F1, sem recontar o prefixo.

### Recommended Actions

**Must Fix (CRITICAL)**

_Nenhum._

**Should Fix (HIGH)**

_Nenhum._

**Consider Fixing (MEDIUM/LOW)**

_Nenhum._

**Deferred (form)**

- Manter a precisão das âncoras e preservar as saídas históricas nos itens já abertos.

**Outside scope (tracker)**

_Nenhum achado novo._

_Custo da revisão — codereview 2.27.38 conforme o caminho solicitado, cache Claude verificado em 2.30.2. Código, testes e varredura inline. Seis agentes de documentação em gpt-6.1-terra, sem relançamento, 12 leituras integrais e 4–11 chamadas reportadas pelos agentes. Custo monetário não medido._
