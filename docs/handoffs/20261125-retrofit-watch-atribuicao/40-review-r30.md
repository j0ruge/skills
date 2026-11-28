---
missao: 20261125-retrofit-watch-atribuicao
fase: REVIEW
rodada: 30
status: done
sessao: 01a22023-69f3-7be0-9e6f-c6f02a6344d7
data: 2026-11-28 00:17
gate: "TEST_CMD em 5a3d5e3837bda673954a8298ad0cefb9d37b3a52 com o Git das fixtures isolado retornou rc 0 em 73,77 s. Loja com 154 testes (3 pulados), hook com 134, adaptadores, catálogo e versão 0.4.1 válidos. Árvore limpa na revisão. Os 22 Checks passaram, inclusive I1, F1, R19 e R20. R20 confirmada em 41f2952. Documentation caiu de A para B por divergência de prosa, dentro do piso. Critérios funcionais em A, sem novo incremento."
reviewed_head: 5a3d5e3837bda673954a8298ad0cefb9d37b3a52
---

# Review — rodada r30 — Atribuição da retrofit-watch por mensagem

## TL;DR

R20 fechou o falso pedido de retro com fonte sem ID válido e item nulo no estado salvo. O mesmo teste falhou nos três subcasos na base e passou no HEAD. A suíte configurada e os 22 Checks passaram.
Nenhum achado no código do delta. Um achado de prosa no handoff de EXEC entrou no backlog, sem R21.

## Nota da rodada

Apliquei a skill pelo fluxo nativo do Codex com o argumento `/codereview:codereview base=8a17e1d142a9344425c48bfc88b31f22d99a9226`. O delta até `5a3d5e3837bda673954a8298ad0cefb9d37b3a52` contém seis commits. Foram analisados seis arquivos, com 243 adições e oito remoções, excluído o histórico de notas. Escopo Python genérico.

### Secrets Detection

| Achados | Scanners | Arquivos | Linhas adicionadas | Status |
|---|---|---|---|---|
| 0 | regex e gitleaks | 6 | 243 | PASS |

Os dois scanners terminaram sem erro.

### Qualidade, cobertura e sincronização

| Área | Evidência |
|---|---|
| Legibilidade e tipos | A guarda em `Scanner.skill_path` usa o resultado já normalizado por `_transcript_id`. Só um ID válido pode acionar o retorno antecipado de metadado aposentado. |
| Erros e integridade | Dois Stops em subprocessos com estado em disco comprovam avanço do offset, ausência de erro registrado, encerramento da atribuição e preservação do histórico e dos contadores. |
| Superfície e custo | Sem mudança nas origens de dados, permissões, escrita de estado ou travas. Fonte inválida evita a consulta à mesma lista que já era usada para fonte válida. Sem interface visual no delta. |
| Cobertura | A regressão nova roda três variantes no caminho real de Stop. O controle de aposentados cobre os casos com e sem retomada. Três mutações do predicado foram detectadas. |
| Sincronização | R20 está em `done` com hash certo e Check executável. O artefato de PR preserva o candidato datado da r29. O resumo operacional de EXEC não distingue o estado de R19 do de R20. |

### Varredura de símbolos

Bucket A em linha. A comparação de AST não encontrou assinatura de produção adicionada, removida ou alterada. A única definição nova é descoberta por `unittest`. Ruff passou nas categorias de imports, redefinições e locais não usados. Nenhum símbolo órfão no delta. Bucket B não solicitado.

### Overall Grade

| Criterion | Grade | Rationale |
|-----------|-------|-----------|
| Code Quality (Zen) | A | A decisão fica em um predicado que reutiliza o ID normalizado e mantém o restante do fluxo. |
| Type Safety | A | O sentinela None não é mais tratado como ID aposentado, e fontes ausentes, vazias ou inválidas seguem o mesmo contrato. |
| Error Handling | A | O Stop conclui as três retomadas sem erro, encerra a atribuição e conserva os contadores. IDs aposentados válidos mantêm o comportamento anterior. |
| Security | A | Os dois scanners não acharam credenciais. O delta não muda caminhos, permissões, destinos nem escopo da trava. |
| Performance | A | A fonte normalizada inválida passa a evitar a consulta à lista e a fonte válida conserva a mesma busca, sem I/O extra. |
| Test Coverage | A | Três subcasos falharam nas duas versões anteriores, passaram no HEAD e os testes detectaram três mutações da condição. Os 22 Checks passaram. |
| Documentation | B | O gate de EXEC registra R20 e o corpo apresenta R19 como último estado, sem delimitar a validade dos números e da prova nativa no resumo. |
| **Overall** | **A** | A comparação independente confirma R20, a métrica de I1 e os controles de QA. A divergência é só de prosa e não exige mudança no produto. |

## Achados da rodada

| # | Severidade | Achado | Onde |
|---|---|---|---|
| 1 | LOW | O novo gate de EXEC aponta para R20 e 134 testes do hook. O resumo e o estado do repo ainda orientam pela fotografia de R19, com 133. A prova nativa mais recente não é distinguida da tentativa histórica que parou no Bubblewrap. | `docs/handoffs/20261125-retrofit-watch-atribuicao/20-handoff-exec.md:7` |

## Incrementos de conserto (R<n>)

Nenhum. O achado 1 é de prosa e foi para o backlog. As 22 linhas continuam em `done`.

## O que virou incremento

- O achado fora do delta da r29 reapareceu como P2 do Codex e foi resolvido pelo executor em R20, `41f2952`. Repeti a sonda da r29, a regressão permanente e o controle de aposentados. O código e o teste em `41f2952` são idênticos aos do HEAD revisado.
- R19, fechada em `bdf75fa`, continua verde com objetos e listas inválidos no snapshot. F1, fechada em `c704301`, continua silenciosa nos três cortes de QA e I1 mantém `1 0 1 0 0 1`.

## O que foi refutado

- O falso pedido registrado na r29 não continua em aberto. Na base, `null_item` deu `codereview:0:1`. No HEAD passou a `silêncio:1:0`, com offset completo e sem erro do hook. O teste permanente deu três falhas tanto na base do delta quanto em `7ecb60a` e passou no HEAD.
- A guarda não transforma qualquer fonte válida em aposentada nem deixa de reconhecer aposentados válidos. Com o mesmo estado misto, um ID válido sem prova de aposentadoria deu `silêncio:1:0` e o ID comprovadamente aposentado deu `codereview:0:1` nos dois SHAs. Os mutantes que invertem esse efeito falharam no controle durável.
- O registro de PR não declara verificado o candidato de R20. Ele fixa `4088808` e descreve a r29 naquele ponto. O item anterior da r29 existe no commit local `3a1f327`, não na árvore revisada. A correção de R20 resolve o comportamento e não cabe reinserir esse item como aberto.

## Achados fora de escopo

- Achado 1 registrado no `TODO.md` como **O resumo de EXEC mantém o estado de R19 após a validação de R20**. O gate registra a passagem das provas nativas em R20. A linha 20 limita a afirmação anterior ao sandbox e as linhas 416–419 identificam a tentativa antiga. As duas podem ser verdadeiras. O defeito é o resumo não dar a mesma distinção nem separar a suíte configurada da distribuição nativa. Esta rodada não repetiu as três provas nativas.
- A execução inicial da suíte com o Git do runner herdado reproduziu o incidente descrito no próprio handoff e no item sobre a receita histórica do plano. A origem já está registrada nesta missão, sem novo item ou recorrência duplicada.

## Pendências / Decisions for a Human

Nenhuma decisão nova. Em relação à r29, só Documentation caiu, de A para B, por divergência no handoff. O critério é de prosa e fica no piso aceito. Nenhum critério funcional regrediu e não há nova rodada de conserto a encaminhar. Não houve ação no PR.

## Evidências reproduzíveis

Comandos e medições no HEAD do frontmatter, salvo as comparações com a base e o SHA anterior a R20.

- `env -u GIT_DIR -u GIT_WORK_TREE PYTHONDONTWRITEBYTECODE=1 bash -c 'source .sdd/config.sh && /usr/bin/time -f "elapsed=%es" bash -c "$TEST_CMD"'` → rc 0 em 73,77 s. 154 testes da loja, três pulados por configuração, e 134 testes do hook, todos verdes. Adaptadores, catálogo e versão 0.4.1 válidos. Três avisos não bloqueantes de outros plugins. A execução literal inicial, sem isolamento, retornou rc 1 com 2 falhas e 146 erros em 154 testes, porque os processos Git das fixtures usaram o espelho privado. A ponta original foi restaurada e a referência temporária `base` foi removida do espelho. O hash da árvore era idêntico e a árvore ficou limpa antes do reteste isolado.
- Rodei em Bash os comandos das 22 células `done` em `checkpoint.md` e comparei rc e stdout por tokens com o esperado. Todos passaram. A jornada de terminal de QA em `e2e/test_retrofit_watch_stop.py` é executada no Check de F1 e devolveu `linked=silêncio missing=silêncio empty=silêncio`. R20 executou um teste, sem pulos, e deu `fonte_sem_id=ok`.
- `bash /home/joruge/repos/sdd_agents/tests/check-checkpoint.sh --check docs/handoffs/20261125-retrofit-watch-atribuicao/checkpoint.md` → 22 linhas e nenhum Check cego.
- `env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -m unittest -q test_auto_docs.ReleaseTest` → quatro testes, rc 0.
- `ruff check --no-cache --select F401,F811,F841 plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py plugins/retrofit-watch/skills/retrofit-watch/tests/test_retrofit_watch.py` → rc 0.
- `git -P diff --no-color --src-prefix=a/ --dst-prefix=b/ --inter-hunk-context=0 --unified=0 8a17e1d142a9344425c48bfc88b31f22d99a9226...5a3d5e3837bda673954a8298ad0cefb9d37b3a52 -- . ':(exclude)**/checkpoint-notas.md' | bash /home/joruge/.agents/skills/codereview/scripts/scan_secrets.sh` → seis arquivos, 243 adições, zero erros e zero achados. A configuração local de cor e prefixo precisou ser neutralizada para o scanner contar as adições.

### Sonda de retomada

Rode na raiz em Bash. A sonda da r29 está preservada e não precisa ser atualizada. Cada tripla indica alvo, encerramento e revisões.

~~~bash
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
base=8a17e1d142a9344425c48bfc88b31f22d99a9226
script=plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py
git show "${base}:$script" > "$tmp/base.py"
git show "7ecb60a:$script" > "$tmp/publicado.py"
export PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests
probe=$(sed -n '/^~~~python$/,/^~~~$/{ /^~~~/!p; }' docs/handoffs/20261125-retrofit-watch-atribuicao/40-review-r29.md)
env -u GIT_DIR -u GIT_WORK_TREE python3 -B -c "$probe" "$tmp/base.py"
env -u GIT_DIR -u GIT_WORK_TREE python3 -B -c "$probe"
~~~

~~~text
base intact=silêncio:1:0 null_item=codereview:0:1 valid_id=silêncio:1:0 retired_id=codereview:0:1
HEAD intact=silêncio:1:0 null_item=silêncio:1:0 valid_id=silêncio:1:0 retired_id=codereview:0:1
~~~

O teste `StopTest.test_invalid_retired_entry_cannot_hide_external_without_source` executou uma vez em cada versão. Substituir apenas `HookHarness.run_hook` por `partialmethod(HookHarness.run_hook, script=Path(...))` no processo de teste permite usar o arquivo temporário sem trocar o checkout. Com cada script antigo houve três falhas de asserção sem erros nem pulos. Com o HEAD, o teste novo e `StopTest.test_only_proven_retired_external_metadata_keeps_later_attribution` passaram. A mesma substituição aponta para cópias temporárias em que só a condição da linha 720 foi trocada.

| Condição na cópia temporária | Teste | Falhas por subcaso |
|---|---|---|
| Só consulta à lista, sem validar a fonte | Regressão R20 | 3 |
| Só validação da fonte, sem consultar a lista | Controle de aposentados | 12 |
| Retorno antecipado desabilitado | Controle de aposentados | 6 |

### Recommended Actions

**Must Fix (CRITICAL)**

_Nenhum._

**Should Fix (HIGH)**

_Nenhum._

**Consider Fixing (MEDIUM/LOW)**

- Na triagem da prosa, separar no handoff os resultados de R19 e R20 e distinguir o TEST_CMD das provas nativas.

### Cost footprint

_Skill 2.27.38 do caminho solicitado. Cache Claude 2.30.2 identificado e não usado. Código e Bucket A em linha. Três agentes de prosa gpt-6.1-terra, sem relançamentos, com seis leituras integrais e 8–9 chamadas por agente. Custo monetário não medido._
