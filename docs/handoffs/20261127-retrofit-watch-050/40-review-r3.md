---
missao: 20261127-retrofit-watch-050
fase: REVIEW
rodada: 3
status: done
sessao: 01a22142-6717-7c23-be6f-781e3e18473c
data: 2026-11-28 05:32
gate: "Em 9432d56e18bf1734199ce0c8ac3bc5aac7ae3b8f, env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp PYTHONDONTWRITEBYTECODE=1 bash -c 'source .sdd/config.sh; eval \"$TEST_CMD\"' → rc 0, adaptadores e catálogo válidos, 154 testes da loja com 3 pulados, 144 do Stop e versões validadas. git status --porcelain=v1 vazio na árvore analisada. env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B docs/handoffs/20261127-retrofit-watch-050/sonda-qa.py → rc 0. TMPDIR=/tmp PYTHONDONTWRITEBYTECODE=1 python3 scripts/anonymity-gate.py --camada1 --base 1f1b0083efbb3bf753559432ca03ba2df4d5c048 → rc 0 no Git delegado. R6 e R7 pendentes. Platô frente à r2 em Code Quality (Zen), Error Handling, Security e Test Coverage."
reviewed_head: 9432d56e18bf1734199ce0c8ac3bc5aac7ae3b8f
---

# Review — rodada r3 — Retrofit de skills locais com ensaio antes do push autônomo

## TL;DR

R4 separou caixa, sufixo e barra final. R5 corrigiu o argumento SSH e limpou a camada 1 desde a base da r2.
O Git ainda distingue destinos SSH que a autorização iguala, e o `gh` real recusa a porta HTTPS que o dublê aceitou.
R6 e R7 ficam pendentes. As suítes e a jornada passaram, mas a nota continua B nos mesmos critérios técnicos.

## Nota da rodada

### Overall Grade

| Criterion | Grade | Rationale |
|-----------|-------|-----------|
| Code Quality (Zen) | B | A chave da lista agora se separa da grafia do caminho, mas a identidade ainda perde a semântica do transporte. A chamada de status também mistura porta HTTPS e hostname do cliente. |
| Type Safety | A | As variantes exercitadas preservam a forma da identidade e o contrato hexadecimal. Os quatro Python do delta foram importados e executados pelos testes, sem erro de construção. |
| Error Handling | B | A correção SSH e o registro pós-push funcionam na fixture, mas um argumento HTTPS que o cliente nunca aceita ainda é descoberto só depois de mover o bare. |
| Security | B | Caminhos com grafias diferentes deixaram de colidir e a varredura não encontrou credenciais. Dois destinos SSH com SHAs distintos ainda compartilham a autorização de origem. |
| Performance | A | O parser continua local e a seleção do endereço usa apenas a URL já lida. A regressão de startup offline passou, sem incluir rede no processo do hook. |
| Test Coverage | B | Os 130 testes e a jornada passaram, mas um teste trata equivalência não comprovada como sucesso e o dublê HTTPS aceita um argumento recusado pelo cliente real. |
| Documentation | B | A documentação acompanha a separação de caixa e a porta SSH, mas os comandos de evidência têm aspas literais e a garantia de status HTTPS ainda não se sustenta. |
| **Overall** | **B** | Há consertos reais em R4 e R5, mas o vínculo de destino e a compatibilidade do status ainda têm falhas reproduzidas. |

## Achados da rodada

| # | Severidade | Achado | Onde |
|---|---|---|---|
| 1 | HIGH | A identidade do mesmo servidor iguala SCP relativo e URI SSH de caminho absoluto. A troca passa na elegibilidade e na guarda da porta mesmo quando o Git encontra outro repositório. | `plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py:329` |
| 2 | MEDIUM | A seleção atual mantém a porta HTTPS em `--hostname`, que o GitHub CLI rejeita. O bare pode avançar sem `local/ci`, com rc 4, apesar do teste verde. | `plugins/retrofit-watch/skills/retrofit-watch/scripts/rw_gate.py:1419` |
| 3 | LOW | Trechos copiáveis dos handoffs usam escapes próprios de YAML no shell. O comando do scanner recebe aspas no caminho e o da suíte falha antes de executá-la. | `docs/handoffs/20261127-retrofit-watch-050/20-handoff-exec.md:87` e `docs/handoffs/20261127-retrofit-watch-050/40-review-r2.md:98` |

### Reprodução dos achados

1. Em `PrivateWorld`, `git ls-remote` real com um dublê SSH local passou `fixture/kb-libs.git` para SCP e `/fixture/kb-libs.git` para a URI. Cada forma consultou um bare distinto e devolveu um SHA de `main` diferente, `0f841f45afc9` e `ede24dcad09d`. Mesmo assim, ambas produziram o mesmo `origin_id` e `why_manual` devolveu `None`. Em `GateTest`, a guarda `_private_origin` também aceitou a troca de origem de SCP para URI no worktree do lote, com a identidade original e as duas URLs Git efetivas apontando para a URI. A sonda parou na guarda, sem push para o destino alternativo.
2. Repeti o cenário de `GateTest.assert_private_status_target`, com push real para bare local e troca sintética para uma origem HTTPS na porta 8443 somente no passo de status. Substituí a aceitação do dublê pelo `gh` 2.85.0 real em ambiente isolado. A execução devolveu `error parsing --hostname: invalid hostname` e rc 1 antes de tentar uma conexão. A porta devolveu `publicado`, `status-falhou`, rc 4 e o bare continha o SHA esperado. No controle, hostname sem porta e endpoint HTTPS absoluto na porta 8443 passaram do parser e o cliente tentou a porta 8443. O sandbox recusou o socket. A prova mede os argumentos e o destino selecionado, não a aceitação pela API.
3. Com `TEST_CMD` sintético que imprimiu `sensor-verde`, a forma literal do Markdown produziu `command not found`. Com aspas de shell sem barras, imprimiu a sentinela. Um `printf` com o argumento de `--repo` mostrou aspas literais na forma publicada e nenhuma na forma corrigida. Os escapes nos campos YAML, que são decodificados antes de ler o comando, não fazem parte do achado.

## Incrementos de conserto (R<n>)

| R<n> | Achado | Check escrito no checkpoint |
|---|---|---|
| R6 | 1 | Duas regressões exigem inelegibilidade e recusa antes do fetch para destino não equivalente. A jornada repete o caminho autorizado. |
| R7 | 2 | A regressão exige argumentos aceitos pelo cliente para HTTPS, sem perder a porta efetiva, e mantém a prova SSH e a jornada. |

```text
| R6 | Distinguir destinos Git por transporte e forma do caminho onde não há equivalência comprovada | `(env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -m unittest test_lean_auto.LeanAutoTest.test_unverified_transport_equivalence_stays_manual test_lean_gate.GateTest.test_changed_transport_target_holds_before_fetch >/dev/null && env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B docs/handoffs/20261127-retrofit-watch-050/sonda-qa.py >/dev/null); echo $?` → `0` | pending | — |
| R7 | Usar uma chamada válida ao gh para status com porta HTTPS explícita | `(env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -m unittest test_lean_gate.GateTest.test_private_status_custom_https_port_uses_valid_cli_arguments test_lean_gate.GateTest.test_private_status_uses_api_host_not_ssh_port >/dev/null && env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B docs/handoffs/20261127-retrofit-watch-050/sonda-qa.py >/dev/null); echo $?` → `0` | pending | — |
```

## O que virou incremento

- Achado 1 → `R6`. A regressão deve medir o destino Git efetivo e exigir que a autorização recuse a equivalência que não consegue comprovar. O teste atual de mesmo slug com outro host também espera, para loopback, igualdade entre HTTPS e duas formas SSH. Rever esse controle sem perder a prova positiva do GitHub público.
- Achado 2 → `R7`. Não basta retirar a porta HTTPS ou continuar aceitando qualquer sequência no dublê. A chamada deve preservar o destino da API em formato válido para o cliente, sem redirecionar para a porta padrão. A expectativa de `test_private_status_keeps_custom_https_port` precisa acompanhar o contrato real medido.
- `R4` em `4f9d3cb` — os testes de grafia do caminho e a sonda passaram. Remover a distinção do caminho em memória fez quatro subcasos do teste de elegibilidade falharem. O achado 1 é sobre o significado de caminhos com a mesma grafia, não sobre a reabertura dos casos de caixa e sufixo.
- `R5` em `def54f4` — o teste SSH, a jornada e a camada 1 desde `1f1b008` passaram. Repassar a porta SSH fez a regressão nova falhar. Remover também a porta HTTPS derrubou o controle atual, que prova o argumento produzido, mas não a compatibilidade com o cliente. O achado 2 deixa esse limite explícito.
- Esta rodada não alterou fonte, testes ou documentação de produto.

## O que foi refutado

- R4 não deixou a caixa, o sufixo e a barra final colidirem no caso original. `test_same_host_distinct_repo_paths_stay_manual` e `test_distinct_repo_paths_have_distinct_origin_ids` passaram no controle íntegro. A contraprova que retirou o caminho foi detectada.
- R5 não quebrou a variante SSH de porta própria nem introduziu um segredo. `test_private_status_uses_api_host_not_ssh_port`, a camada 1 com base `1f1b008` e a varredura de segredos do delta saíram verdes. A reprodução HTTPS falha por uma regra do cliente, sem uma requisição real.
- Não se deve concluir que todo uso de aspas escapadas é incorreto. O problema foi reproduzido nas receitas Markdown copiáveis. Os campos de frontmatter precisam dos escapes para representar aspas dentro de uma string YAML.

## Achados fora de escopo

- Achado 3 registrado em `TODO.md`, item **As receitas dos handoffs preservam escapes indevidos ao copiar**. É prosa, sem incremento.
- Os itens abertos de corrida residual de avanço, auditoria privada e camada 1 da branch inteira permanecem no backlog. Não repeti uma varredura da branch inteira nem reabri achados fora do delta. A medição da camada 1 nesta rodada usa a mesma base do Check R5.

## Pendências / Decisions for a Human

O placar estacionou frente à r2. R6 e R7 documentam o trabalho restante para o EXEC. A revisão não inicia outra rodada neste contexto. A distribuição nativa e a adoção em repos reais continuam pendentes no ambiente indicado pela QA, sem medição nova nesta rodada.

## Evidência e escopo da codereview

- A chamada equivalente a `/codereview:codereview base=66a88d82156a0759c0f32a844d3549bffeae376f` analisou `66a88d82156a0759c0f32a844d3549bffeae376f...9432d56e18bf1734199ce0c8ac3bc5aac7ae3b8f`. O intervalo tem cinco commits e 14 caminhos. O diário de execução foi excluído do conteúdo analisado e da entrada do scanner. Os 13 arquivos restantes são dois módulos Python, dois testes e nove Markdown. Os dois commits de produto são `4f9d3cb` e `def54f4`. O handoff da QA orientou a repetição da jornada.
- **Secrets Detection — PASS.** `git -P diff 66a88d82156a0759c0f32a844d3549bffeae376f...HEAD --unified=0 -- . ':(exclude)docs/handoffs/20261127-retrofit-watch-050/checkpoint-notas.md' | bash /home/joruge/.agents/skills/codereview/scripts/scan_secrets.sh` escaneou 13 arquivos, 281 linhas adicionadas, zero achados e zero erros em `regex` e `gitleaks`.
- **TEST_CMD.** `env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp PYTHONDONTWRITEBYTECODE=1 bash -c 'source .sdd/config.sh; eval "$TEST_CMD"'` → rc 0. Loja com 154 testes e três pulados, Stop com 144 verdes, adaptadores e catálogo válidos e versões 0.5.0 e 0.12.0 validadas.
- **Cobertura.** `env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests:plugins/retrofit-skill/tests python3 -B -m unittest test_fixture_private test_lean_auto test_lean_window test_lean_live test_lean_batch test_lean_gate test_auto_docs test_modo_autonomo` → rc 0, 130 testes sem pulos. `retrofit_watch.py` tem cobertura direta nas duas suítes alteradas e `rw_gate.py` tem cobertura direta em `test_lean_gate.py`. Das três contraprovas independentes em memória, as três acusaram o defeito esperado, sem erro de importação ou skip. Foram 7 testes na contraprova R4 e 43 em cada variante de R5.
- **Jornada.** `env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B docs/handoffs/20261127-retrofit-watch-050/sonda-qa.py` → rc 0. Ensaio preservou `3b96dde72d05`, a nova aprovação alinhou bare, status capturado, registro e clone em `e8879a36d15d`, e a janela vigente publicou `16eadad44f6f` sem aprovação. Após revert, conservou `b294f46462b4`. A confirmação manual alinhou `475fa4a8c1da`, e sem confirmação o bare e o clone não mudaram.
- **Camada 1.** `TMPDIR=/tmp PYTHONDONTWRITEBYTECODE=1 python3 scripts/anonymity-gate.py --camada1 --base 1f1b0083efbb3bf753559432ca03ba2df4d5c048` → rc 0 com `HEAD` do Git delegado igual a `9432d56e18bf1734199ce0c8ac3bc5aac7ae3b8f`. A forma SSH do teste foi mantida com endereço sintético local. O scanner não foi alterado.
- **Documentação e código morto.** Foram conferidos README, CHANGELOG, contrato do clone, referências de publicação e artefatos do delta. A busca de referências à identidade e aos novos auxiliares não achou órfãos introduzidos pelo delta. O estoque preexistente e consumidores externos não foram varridos.
- **Movimento frente à r2.** Houve dois commits efetivos, mas as quatro notas técnicas abaixo de A não subiram. O limite da identidade SSH e a incompatibilidade HTTPS explicam o platô. Nenhuma nota foi rebaixada.

### Recommended Actions

**Must Fix (CRITICAL)**

Nenhum.

**Should Fix (HIGH)**

- `R6` — não reutilizar uma autorização entre destinos Git cuja equivalência não foi comprovada.

**Consider Fixing (MEDIUM/LOW)**

- `R7` — preservar o endereço HTTPS conferido sem formar um argumento que o cliente recusa.
- **Backlog** — corrigir as receitas copiáveis sem reescrever a evidência do que foi medido.

_Custo da revisão — codereview 2.27.38, cópia explicitamente indicada pela missão. O registro instalado aponta 2.30.2, que acrescenta fluxo documental próprio. Código e varredura inline, três agentes documentais gpt-6.1-terra com marcadores completos e 9–11 chamadas por agente. As reproduções, a calibragem e as notas foram consolidadas na sessão principal._
