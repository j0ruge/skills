---
missao: 20261127-retrofit-watch-050
fase: REVIEW
rodada: 5
status: done
sessao: 01a22176-a7bf-7640-bb40-85f50a485317
data: 2026-11-28 06:30
gate: "Em b99115b126352d02a6fa5a3a64fc8d44ca0d2e68, `env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp PYTHONDONTWRITEBYTECODE=1 bash -c 'source .sdd/config.sh; eval \"$TEST_CMD\"'` → rc 0, adaptadores e catálogo válidos, 154 testes da loja (3 pulados), 144 do Stop e versões validadas. Árvore inicial limpa. Jornada da QA e 146 regressões dirigidas verdes. Gate de notas não passou em Error Handling e Test Coverage. R11 está pending."
reviewed_head: b99115b126352d02a6fa5a3a64fc8d44ca0d2e68
---

# Review — rodada r5 — Retrofit de skills locais com ensaio antes do push autônomo

## TL;DR

R9 e R10 passaram nos casos que motivaram as correções. A jornada de QA também passou.
Reproduzi três achados na finalização do setup. O comando pode devolver um destino ausente
ou liberar um substituto. Na retentativa, também aceita origem declarada incompatível,
ramo errado ou trava incompleta. Os achados de código formam R11. Nota geral B.

## Nota da rodada

Usei `codereview:codereview base=eaf78b0011ea61f00a745b3cfe922b6b2061cebe` sobre `b99115b126352d02a6fa5a3a64fc8d44ca0d2e68`, com o handoff de QA e as pendências da r4. Foram 10 commits e 15 caminhos no delta. O conteúdo de `checkpoint-notas.md` ficou fora da leitura conforme o boot. Os dois arquivos de produção e a varredura de código morto foram revisados inline. Os verificadores leram 102 unidades alteradas de 10 arquivos de prosa. A nota de Documentation avalia somente essas unidades.

### Secrets Detection

`PASS`. O pré-scan com regex e gitleaks leu os 14 arquivos incluídos, com 443 linhas adicionadas, zero achados e zero erros. A revisão do código e das fixtures não acrescentou credenciais.

### Qualidade, segurança e desempenho

A instalação exclusiva substitui a separação entre checar existência e renomear. Os achados se concentram em outra etapa, a promoção do clone de pendente para pronto. A inconsistência da origem declarada reproduzida é recusada no avanço antes de fetch, e nenhuma sonda publicou fora do bare. O teste offline confirma que o startup retorna em menos de 1 s sem esperar o fetch. Sem superfície de interface gráfica no delta.

### Test Coverage

| Produção | Sensor no delta | Resultado |
|---|---|---|
| `rw_store.py` | `test_lean_live.py` | Movimento exclusivo, perda de arquivos na recusa, retomada, origem final e trava no setup inicial cobertos. Os casos de R11 ainda não são cobertos. |
| `retrofit_watch.py` | `test_lean_live.py::StartupTest` | A falha de lançamento aparece com registro anterior `ok`, sem suprimir outro aviso. Avanço offline continua separado. |

Os dois arquivos de produção têm testes atualizados. Provas em `b99115b126352d02a6fa5a3a64fc8d44ca0d2e68`:

- `env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp PYTHONDONTWRITEBYTECODE=1 bash -c 'source .sdd/config.sh; eval "$TEST_CMD"'` → rc 0. Loja com 154 testes, três pulados. Stop com 144, sem falhas. A validação das versões inclui watch 0.5.0 e skill 0.12.0.
- `env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests:plugins/retrofit-skill/tests python3 -B -m unittest test_fixture_private test_lean_auto test_lean_window test_lean_live test_lean_batch test_lean_gate test_auto_docs test_modo_autonomo` → 146 testes, sem falhas nem pulos.
- `env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B docs/handoffs/20261127-retrofit-watch-050/sonda-qa.py` → rc 0. O ensaio não moveu o bare. A emenda reteve o push até nova aprovação. A janela cumprida publicou sem aprovação e o revert restaurou o ensaio. Na rota confirmada de fixture, bare, status capturado e clone convergiram. A sonda não mede a decisão de um modelo nem consulta uma API real.
- Oito provas dirigidas do setup e startup passaram, incluindo os dublês de macOS e Windows e o teste offline. A distribuição nativa no host consta do handoff de EXEC e não foi repetida nesta rodada.

### Documentation Sync

A receita de status manual em `plugins/retrofit-skill/references/modo-autonomo.md` e o teste de contrato agora especificam hostname sem porta e URL absoluta para HTTPS com porta própria. O contrato do clone, o README e as referências descrevem preservação e retomada. Os desvios reproduzidos desse contrato foram atribuídos ao código. Parte das medições históricas ficou sem saída preservada nos artefatos revisados.

### Código morto

`ruff check --no-cache --select F401,F821,F841` nos quatro arquivos Python alterados passou. Os dois auxiliares novos e `ctypes` têm chamadas ou usos no fluxo revisto. Sem símbolos introduzidos ou órfãos a remover. Inventário preexistente fora da rodada.

### Overall Grade

| Criterion | Grade | Rationale |
|-----------|-------|-----------|
| Code Quality (Zen) | A | A movimentação exclusiva e o auxiliar de retomada separam instalação de validação, sem fallback que sobrescreva o destino. As falhas remanescentes estão na decisão de finalizar. |
| Type Safety | A | O marcador compara bytes ASCII de tamanho limitado. Os argumentos nativos, identificadores de origem e contratos persistidos passaram nas provas aplicáveis. |
| Error Handling | B | O setup pode retornar sucesso sem a cópia que validou, ou promover um clone pendente com invariantes incompletas. |
| Security | A | Pré-scan limpo e controles de origem e publicação verdes. O avanço recusa origem inconsistente antes do fetch. |
| Performance | A | O avanço segue destacado. A prova offline confirmou startup em menos de 1 s sem aguardar fetch. |
| Test Coverage | B | As 146 regressões, o TEST_CMD e a jornada passaram. Ainda faltam sensores de troca após validação e de retomada com origem, ramo ou trava alterados. |
| Documentation | B | A receita de status foi corrigida e o contrato do clone está expresso. Falta a saída preservada de parte das medições históricas do delta. |
| **Overall** | **B** | R9 e R10 moveram a revisão. Os defeitos reproduzidos de finalização impedem aprovação técnica e formam R11. |

Em relação à r4, Code Quality (Zen) sobe de B para A com a movimentação exclusiva de `c445ff7`.
Error Handling e Test Coverage continuam em B por casos novos, não por repetição dos achados fechados.
Nenhuma letra caiu.

## Achados da rodada

| # | Severidade | Achado | Onde |
|---|---|---|---|
| 1 | MEDIUM | A finalização resolve novamente o caminho depois da validação. Aceita um destino que sumiu e pode remover o marcador de outro clone que o substituiu. | `plugins/retrofit-watch/skills/retrofit-watch/scripts/rw_store.py:1008` |
| 2 | MEDIUM | A retomada compara a origem efetiva, mas pode dar sucesso com uma origem declarada diferente da original. O clone fica inelegível para a origem escolhida e já não pode ser retomado. | `plugins/retrofit-watch/skills/retrofit-watch/scripts/rw_store.py:1007` |
| 3 | MEDIUM | A retomada não reconfere a `main` nem a trava de commit instaladas antes da primeira validação. Pode entregar um clone que o avanço recusa ou uma `main` que aceita commits locais. | `plugins/retrofit-watch/skills/retrofit-watch/scripts/rw_store.py:990` |
| 4 | MEDIUM | Algumas medições históricas de PLAN, EXEC e r4 têm número e relato, sem a saída preservada junto do artefato. | `docs/handoffs/20261127-retrofit-watch-050/20-handoff-exec.md:80` |

### Reprodução

Cinco sondas de caracterização em `b99115b126352d02a6fa5a3a64fc8d44ca0d2e68`, executadas com `env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -` sobre a `PrivateWorld` de `test_lean_live`. As sondas deram rc 0 porque exigiram observar os resultados defeituosos. Não foram testes de aceite.

1. Fiz a chamada real de `_live_remote` conferir a origem e movi o destino antes de devolver seu resultado. Sem substituto, o setup retornou o caminho ausente. Com um segundo clone da mesma origem, marcador de mesmo conteúdo e inode diferente, o setup retirou o marcador do segundo clone e o tornou elegível. O marcador da cópia que de fato foi validada permaneceu intacto. As regressões existentes em `test_lean_live.py:214` e `:260` provocam uma **recusa** na validação, caso em que o unlink não é alcançado.
2. Usei o `includeIf.gitdir` de `_final_origin_rewrite` para deixar a instalação pendente e retirei a regra. Troquei o `remote.origin.url` por um alias sintético do mesmo slug e configurei `insteadOf` para apontar o alias ao bare original. A URL efetiva continuou correta. O retry pela URL original deu rc 0 e apagou o marcador. `live_clone(..., origin=original)` retornou `None`, `live-advance` registrou `erro` de origem e outro `live_setup` recusou o destino existente. Nenhum teste existente de retry separa a origem declarada da efetiva nessa etapa.
3. Após a mesma recusa inicial, em duas fixtures independentes, troquei para o ramo `rascunho` e, no outro caso, simulei uma trava incompleta movendo `.git/rw-live.config`. Corrigida a regra de origem, a CLI retornou rc 0 nos dois casos. No primeiro, `live-advance` registrou `fora-da-main`. No segundo, um `git commit --allow-empty` mudou o HEAD da `main`. O teste de setup inicial exige que esse commit seja recusado. O de retomada só verifica o mesmo inode, arquivos locais e elegibilidade depois de ajustar a regra.
4. As saídas que embasam o Red de planejamento e as 34 mutações de R9 não acompanham as linhas citadas. A r4 também registra medições por resumo, por exemplo a saída da sonda de QA. Isso limita a auditoria histórica, sem evidência de contagem incorreta. Repeti as verificações atuais indicadas acima, incluindo as 146 regressões. Não reabri o PLAN nem repeti as 34 mutações.

## Incrementos de conserto (R<n>)

| R<n> | Achado | Check escrito no checkpoint |
|---|---|---|
| R11 | 1, 2 e 3 | Quatro regressões nomeadas, controle de preservação de arquivos de R10 e repetição da jornada de QA. |

## O que virou incremento

```text
| R11 | Finalizar somente o clone validado, na main, com origem consistente e trava efetiva | `(env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -m unittest test_lean_live.LiveTest.test_setup_does_not_finalize_missing_or_replaced_destination test_lean_live.LiveTest.test_setup_retry_requires_declared_and_effective_origin test_lean_live.LiveTest.test_setup_retry_does_not_finalize_wrong_branch test_lean_live.LiveTest.test_setup_retry_requires_effective_worktree_lock test_lean_live.LiveTest.test_setup_retry_keeps_files_after_final_origin_rejection >/dev/null && env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B docs/handoffs/20261127-retrofit-watch-050/sonda-qa.py >/dev/null); echo $?` → `0` | pending | — |
```

- R9 fechado em `c445ff7`. O destino vazio criado imediatamente antes da instalação manteve o inode. A primeira validação recusou a reescrita exclusiva do destino e o retry, após retirar a regra, funcionou. Falha no `Popen` gerou aviso com registro anterior `ok` e preservou o aviso da fila. A prova offline passou.
- R10 fechado em `1ca718d`. O teste preservou o inode e o arquivo criado durante a validação final, recusou a troca da origem pedida e retomou após retirar a regra. Os casos novos de R11 mudam condições que esse teste mantém constantes.
- O achado de prosa da r4 sobre a porta HTTPS foi resolvido em `84a0b0e`. O teste `test_manual_confirmation_and_publish_contract` passou nas regressões dirigidas e a busca pela receita antiga não encontrou ocorrência.

## O que foi refutado

- **Remover o clone pendente para evitar estados intermediários.** A regressão de R10 prova que há arquivos locais a preservar. Retirar a pendência só depois de conferir a mesma cópia é diferente de limpar o destino em caso de erro.
- **A concorrência ainda permite que a instalação inicial sobrescreva um diretório vazio.** O teste chama a movimentação real no Linux e compara o inode. O bug novo está após a validação final, no marcador, não no rename inicial.
- **A correção de origem precisa aceitar apenas a URL escrita literalmente no comando.** O contrato usa identidade de origem, não igualdade textual. A sonda usou duas identidades diferentes, com Git aplicando uma reescrita. Não há motivo para desfazer as equivalências já aceitas.
- **Ausência de saída histórica prova que as medições estavam erradas.** Não prova. A limitação verificável é de rastreabilidade. A contagem atual de 146 testes e a jornada foram repetidas com resultado verde.

## Achados fora de escopo

- A falta de saídas históricas do achado 4 foi registrada como recorrência em `TODO.md`, no item “Medições históricas da atribuição sem saída preservada”. Não gera incremento de prosa.
- A corrida do avanço depois da prova de ancestralidade continua no item “O avanço pode mover outro ramo depois da última conferência”. O delta só deslocou sua âncora. A corrida de R11 ocorre no setup.

## Pendências / Decisions for a Human

Nenhuma decisão nova. A adoção e a validação do gate nos repos reais permanecem com cada dono.

## Boot da próxima fase

Comece por R11 em `checkpoint.md`. No Red da corrida, mova ou troque o destino depois de
validar a origem de verdade. Compare a identidade do diretório e exija que o clone substituto
mantenha seu marcador. Na retomada, cubra separadamente origem declarada divergente,
ramo não `main` e trava incompleta. Exija falha explícita ou o clone pronto com os invariantes
comprovados, sem descartar arquivos do usuário nem trocar seu ramo silenciosamente.
Mantenha a prova de R10 e repita a jornada.

### Ações recomendadas

- **Correções críticas** — Nenhuma.
- **Correções de alta prioridade** — Nenhuma.
- **Corrigir no EXEC** — R11.
- **Prosa adiada** — Preservar saídas históricas, conforme a recorrência no backlog.

_Cost footprint: skill v2.30.2 do cache instalado após leitura da v2.27.38, uma tarefa de contrato e dois verificadores (gpt-6.1-terra), varredura inline, 3 leituras integrais reportadas pela tarefa de contrato, 102 unidades verificadas, 3–5 chamadas por agente._
