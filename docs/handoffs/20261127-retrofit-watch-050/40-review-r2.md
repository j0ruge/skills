---
missao: 20261127-retrofit-watch-050
fase: REVIEW
rodada: 2
status: done
sessao: 01a2212e-ccd1-7001-8307-fa62b5540598
data: 2026-11-28 05:11
gate: "Em 66a88d82156a0759c0f32a844d3549bffeae376f, env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp PYTHONDONTWRITEBYTECODE=1 bash -c 'source .sdd/config.sh; eval \"$TEST_CMD\"' → rc 0, adaptadores e catálogo válidos, 154 testes da loja (3 pulados), 144 do Stop e versões validadas. git status --porcelain → vazio na árvore revisada. env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B docs/handoffs/20261127-retrofit-watch-050/sonda-qa.py → rc 0. env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp PYTHONDONTWRITEBYTECODE=1 python3 scripts/anonymity-gate.py --camada1 --base 1f1b0083efbb3bf753559432ca03ba2df4d5c048 → rc 1 com duas sinalizações sintéticas novas. R4 e R5 pendentes. Code Quality (Zen), Error Handling, Security e Test Coverage abaixo de A, com melhora em Security e Overall frente à r1."
reviewed_head: 66a88d82156a0759c0f32a844d3549bffeae376f
---

# Review — rodada r2 — Retrofit de skills locais com ensaio antes do push autônomo

## TL;DR

Revisei o delta de `1f1b008` até `66a88d8` com o handoff da QA em mãos.
R1–R3 passaram nos sensores anteriores. Confirmei quatro achados, três em R4–R5 e um no backlog.
A jornada e o TEST_CMD passaram, mas a identidade ainda confunde caminhos e a camada 1 do delta saiu vermelha.

## Nota da rodada

### Overall Grade

| Criterion | Grade | Rationale |
|-----------|-------|-----------|
| Code Quality (Zen) | B | O delta fecha a exclusão indevida do patch e separa os avisos, mas a identidade reduz o caminho Git ao slug e reaproveita o endereço de transporte como endereço da API. |
| Type Safety | A | Os leitores exigem um identificador hexadecimal nos pedidos e lotes privados, preservam o full legado e verificam o tipo dos campos exibidos no aviso. |
| Error Handling | B | Setup e registros inválidos têm respostas observáveis, mas o avanço ainda pode registrar sucesso sobre outro ramo e a porta não conclui o status na variante SSH medida. |
| Security | B | O patch de lista e o host distinto passaram nas regressões, mas caminhos distintos no mesmo host ainda colidem fora de um serviço com equivalência garantida. Sem segredo literal no delta. |
| Performance | A | O teste offline confirmou startup em menos de 1 s e fetch destacado. A checagem extra de ramo ocorre no processo de avanço. |
| Test Coverage | B | Passaram 126 regressões e a sonda. Faltam sensores para caminhos distintos no mesmo host, status via SSH com porta própria e a última janela do merge. |
| Documentation | B | O contrato do clone e os avisos acompanham R1–R3, mas o caminho de auditoria privada da r1 continua inconsistente e a promessa de preservação do ramo tem um limite. |
| **Overall** | **B** | Os consertos têm commits e sensores verdes, mas ainda há colisão de identidade, falha de status e camada 1 vermelha no delta. |

## Achados da rodada

| # | Severidade | Achado | Onde |
|---|---|---|---|
| 1 | HIGH | O vínculo usa o slug em minúsculas também como caminho efetivo. Dois caminhos com caixa distinta no mesmo host geram o mesmo `origin_id` e passam pela elegibilidade, mesmo quando o serviço não garante que sejam o mesmo repositório. | `plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py:327` |
| 2 | MEDIUM | Para origem SSH com porta própria, a publicação passa a porta de transporte ao `gh api --hostname`. Quando a API atende pela porta HTTPS usual, o lote fica publicado no bare, mas sem `local/ci` e com rc 4. | `plugins/retrofit-watch/skills/retrofit-watch/scripts/rw_gate.py:1415` |
| 3 | MEDIUM | A nova guarda fecha a janela durante o fetch, mas não durante a verificação de ancestralidade. Uma troca de ramo limpo nesse intervalo ainda resulta em avanço do ramo incorreto e registro `ok`. | `plugins/retrofit-watch/skills/retrofit-watch/scripts/rw_store.py:1039` |
| 4 | LOW | As duas URLs SSH sintéticas adicionadas pela regressão de R2 são lidas como endereços pela camada 1 e tornam vermelho o delta. Nenhuma é credencial. | `plugins/retrofit-watch/skills/retrofit-watch/tests/test_lean_auto.py:87` e linha 88 |

### Reprodução dos achados

As sondas em Python rodaram em `66a88d82156a0759c0f32a844d3549bffeae376f` com `env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -` e fixtures descartáveis. Nenhuma fez chamada a serviço externo.

1. Em `PrivateWorld`, configurei duas URLs HTTPS sintéticas do mesmo host com caminhos que diferem somente na caixa do basename. O `git remote get-url origin` preservou os dois caminhos, mas `origin_identity` e `origin_id` retornaram valores iguais. A classificação seguida de `why_manual` devolveu `None`. A prova terminou na elegibilidade, sem fetch nem push. A caixa não implica repositórios diferentes no GitHub, mas o parser aceita outros hosts sem conhecer essa política.
2. Em `GateTest`, o push para o bare local foi real. Depois dele, forneci ao consumidor de status a identidade resultante do parser para um remoto SSH de fixture na porta 2222. O dublê de `gh` aceitaria o host da API sem essa porta e capturou o argumento com a porta SSH. O retorno foi `publicado`, `status-falhou`, rc 4, com o SHA esperado no bare. `gh api --help` identifica `--hostname` como o endereço da API do GitHub. Não medi a disponibilidade de um serviço externo.
3. Em `PrivateWorld`, intercalei uma troca de ramo local após o `merge-base --is-ancestor` real, antes do merge. As referências do Git confirmaram `resultado=ok`, `main_no_inicio=True` e `ramo_local_no_remoto=True`. O sensor existente troca de ramo durante o fetch e continua verde. O handoff do EXEC já delimitava essa janela menor.
4. Em `66a88d82156a0759c0f32a844d3549bffeae376f`, `env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp PYTHONDONTWRITEBYTECODE=1 python3 scripts/anonymity-gate.py --camada1 --base 1f1b0083efbb3bf753559432ca03ba2df4d5c048` saiu 1, com dois achados sintéticos nas linhas 87–88. A saída não sinalizou nenhum outro arquivo do delta. A varredura de credenciais em separado saiu limpa.

## Incrementos de conserto (R<n>)

| R<n> | Achado | Check escrito no checkpoint |
|---|---|---|
| R4 | 1 | Dois testes exigem identidade distinta e inelegibilidade quando a equivalência entre caminhos não está garantida. A sonda repete a rota autorizada. |
| R5 | 2 e 4 | Um teste captura o status no host da API usando origem SSH com porta própria. A camada 1 do delta precisa voltar a rc 0 e a sonda repete a rota privada. |

```text
| R4 | Distinguir caminhos diferentes em origens do mesmo servidor quando o serviço não garante equivalência | `(env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -m unittest test_lean_auto.LeanAutoTest.test_same_host_distinct_repo_paths_stay_manual test_lean_gate.GateTest.test_distinct_repo_paths_have_distinct_origin_ids >/dev/null && env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B docs/handoffs/20261127-retrofit-watch-050/sonda-qa.py >/dev/null); echo $?` → `0` | pending | — |
| R5 | Separar a porta SSH da API de status e manter verdes as formas sintéticas da camada 1 | `(env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -m unittest test_lean_gate.GateTest.test_private_status_uses_api_host_not_ssh_port >/dev/null && env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp PYTHONDONTWRITEBYTECODE=1 python3 scripts/anonymity-gate.py --camada1 --base 1f1b0083efbb3bf753559432ca03ba2df4d5c048 >/dev/null && env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B docs/handoffs/20261127-retrofit-watch-050/sonda-qa.py >/dev/null); echo $?` → `0` | pending | — |
```

## O que virou incremento

- Achado 1 → `R4`. A identidade de publicação deve distinguir o caminho efetivo da chave normalizada da lista, ou recusar quando não puder comprovar equivalência.
- Achados 2 e 4 → `R5`. Um Check cobre a seleção do host de status, a camada 1 sem omitir os casos SSH e a jornada com bare, registro, status capturado e clone.
- `R1` em `fe68792` — `test_private_patch_includes_store_list_paths` passou. A sonda preservou o bare na emenda e exigiu nova aprovação.
- `R2` em `bc8a164` — os testes de hosts distintos passaram na classificação e na porta antes do fetch. O achado 1 é uma variante no mesmo host e o achado 2 é do status pós-push.
- `R3` em `30d619b` — passaram os quatro Checks de setup, troca durante fetch, basenames e registro inválido. A janela após a nova checagem, achado 3, tem outro ponto de sincronização.
- Nenhum destes consertos foi escrito nesta rodada de revisão.

## O que foi refutado

- O formato novo quebraria um upgrade da 0.4.1. O campo extra é exigido só nas variantes privadas introduzidas pela 0.5.0 e o plano exige compatibilidade com registros full antigos, não migração de estado privado pré-release. `test_mixed_request_and_legacy_full` passou. Um pedido lean de uma candidata antiga não equivale a um formato full distribuído.
- O fallback do status de bare obrigaria uma instalação real a ter API em localhost. A missão limita bare absoluto a fixture e o dublê de `gh` da sonda validou essa rota. Não há serviço externo nessa variante. O achado 2 trata de transporte SSH documentado, não do fallback de teste.
- O README tornaria obrigatória a aprovação mesmo com a janela cumprida. As linhas 476–479 partem do ensaio e as linhas 483–485 explicitam a publicação sem aprovação em `auto`. A sonda publicou em `auto` sem `approve` e voltou ao ensaio após revert.
- Os dois alertas novos da camada 1 seriam vazamento de credenciais. A inspeção de `test_lean_auto.py:83–101` mostrou apenas endereços sintéticos da classificação, sem senha, token ou acesso. Isso explica a diferença entre os scanners, mas não deixa a camada 1 verde.
- A busca pela grafia anterior encontrou `origin_slug` ainda em testes do contrato do slug e o caminho antigo de registro em planos históricos. As referências operacionais alteradas já usam o caminho com dono.

## Achados fora de escopo

- Achado 3 → `TODO.md`, **O avanço pode mover outro ramo depois da última conferência**. A correção completa precisa tornar a condição verificável na atualização do ramo. Uma terceira leitura apenas reduz outra vez a janela. O setup e a guarda contra troca durante fetch ficam comprovados em R3.
- A referência de auditoria privada da r1 continua no item **O executor privado herda caminhos de auditoria da loja no worktree errado**. As linhas da variante de execução não mudaram neste delta. Não há item duplicado.
- As sinalizações anteriores a este delta continuam no item **A camada 1 sinaliza evidência sintética da entrega local**. O achado 4 cobre somente as duas linhas novas de R2. Esta rodada não repetiu a comparação completa com `origin/main`.

## Pendências / Decisions for a Human

Nenhuma decisão nova de produto. A distribuição nativa continua sem comprovação neste host. A QA e a r1 registraram as três falhas antes da instalação por falta de namespace no Bubblewrap. Esta rodada não repetiu a distribuição nativa nem fez publicação real.

## Evidência e escopo da codereview

- A chamada equivalente a `/codereview:codereview base=1f1b0083efbb3bf753559432ca03ba2df4d5c048` limitou o review a `1f1b0083efbb3bf753559432ca03ba2df4d5c048...66a88d82156a0759c0f32a844d3549bffeae376f`. O Git listou sete commits e 20 arquivos. A análise leu quatro módulos de produção, seis arquivos de teste ou sonda e nove Markdown. O diário de execução não foi aberto.
- **Secrets Detection — PASS.** Nesse intervalo, `git -P diff 1f1b0083efbb3bf753559432ca03ba2df4d5c048...HEAD --unified=0 -- . ':(exclude)docs/handoffs/20261127-retrofit-watch-050/checkpoint-notas.md' | bash /home/joruge/.agents/skills/codereview/scripts/scan_secrets.sh` retornou 19 arquivos, 780 linhas acrescentadas, zero achados e zero erros em `regex` e `gitleaks`. A camada 1 é o sensor distinto do achado 4.
- **Cobertura.** Em `66a88d82156a0759c0f32a844d3549bffeae376f`, `env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests:plugins/retrofit-skill/tests python3 -B -m unittest -v test_fixture_private test_lean_auto test_lean_window test_lean_live test_lean_batch test_lean_gate test_auto_docs test_modo_autonomo` saiu 0 com 126 testes. A classificação, o pedido, a porta e o clone tiveram testes nas quatro unidades Python alteradas. Os cinco casos de Review Focus rodaram nessa seleção, incluindo startup offline, pre-push ausente, emenda, colisão de nomes e obstruções no avanço.
- **Jornada.** Em `66a88d82156a0759c0f32a844d3549bffeae376f`, `env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B docs/handoffs/20261127-retrofit-watch-050/sonda-qa.py` saiu 0. O ensaio preservou `beb79f2abd49`, a nova aprovação alinhou os quatro efeitos em `349b946ecf99`, auto publicou `4a4e91174c66`, o revert reteve em `455b902ce2ef` e a confirmação manual alinhou `049f5505da21`. Sem confirmação manual não houve mudança.
- **TEST_CMD.** Em `66a88d82156a0759c0f32a844d3549bffeae376f`, `env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp PYTHONDONTWRITEBYTECODE=1 bash -c 'source .sdd/config.sh; eval "$TEST_CMD"'` saiu 0. Adaptadores e catálogo válidos, 154 testes da loja com três pulados, 144 do Stop sem falhas e versões 0.5.0 e 0.12.0 validadas.
- **Documentação.** README, CHANGELOG e as referências alteradas descrevem a origem autorizada e os registros por dono e repo. A variante da auditoria da loja mantém a inconsistência anterior. O handoff da QA cobre o fluxo e o handoff do EXEC explicita a janela residual.
- **Dead Code & Cleanup.** A varredura por referências dos símbolos do delta não encontrou órfãos. Usou busca textual e não avaliou o estoque preexistente nem consumidores externos.
- **Movimento frente à r1.** Security e Overall subiram de C para B, com os três commits de conserto acima. Nenhuma nota caiu. O gate ainda não fecha.

### Recommended Actions

**Must Fix (CRITICAL)**

Nenhum.

**Should Fix (HIGH)**

- `R4` — separar identidade de publicação do slug de inscrição e preservar a equivalência somente onde ela é comprovada.

**Consider Fixing (MEDIUM/LOW)**

- `R5` — distinguir o endpoint de status do transporte SSH e conservar as provas de origem com fixtures compatíveis com a camada 1.
- **Backlog** — manter visível a corrida residual do avanço. A prova da adoção e a distribuição real ainda dependem dos ambientes já indicados pela QA.

_Custo da revisão — codereview 2.27.38, cópia indicada pela missão. O registro instalado aponta 2.30.2, com fluxo diferente para verificação documental. Dois lotes de código, dois de documentação e uma varredura em gpt-6.1-terra, com marcadores completos. As reproduções e a nota foram consolidadas na sessão principal._
