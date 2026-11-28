---
missao: 20261127-retrofit-watch-050
fase: REVIEW
rodada: 6
status: done
sessao: 01a22190-0dc0-7ec0-8d8c-1f818acd940e
data: 2026-11-28 06:57
gate: "Em 21d8e02e03767382b5a97c86e0d55b426906dce0, `env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp PYTHONDONTWRITEBYTECODE=1 bash -c 'source .sdd/config.sh; eval \"$TEST_CMD\"'` → rc 0, adaptadores e catálogo válidos, 154 testes da loja (3 pulados), 144 do Stop e versões validadas. Árvore inicial limpa. Cinco regressões nomeadas de R11, 156 regressões dirigidas e jornada de QA verdes. Gate de notas não passou. Error Handling e Test Coverage ficaram em B como na r5 (platô de notas). R12 está pending."
reviewed_head: 21d8e02e03767382b5a97c86e0d55b426906dce0
---

# Review — rodada r6 — Retrofit de skills locais com ensaio antes do push autônomo


## TL;DR

R11 passou nos cinco casos do Check e a jornada de QA passou.
O setup ainda libera a cópia se o caminho efetivo da trava termina em espaço ou se o ramo
muda durante a validação sem troca de diretório. Os dois casos reproduzidos formam R12.
Nota geral B. Error Handling e Test Coverage ficaram no mesmo patamar da r5.

## Nota da rodada

Usei `codereview:codereview base=b99115b126352d02a6fa5a3a64fc8d44ca0d2e68` sobre
`21d8e02e03767382b5a97c86e0d55b426906dce0`, com o handoff de QA e as pendências da r5. Foram seis commits e
dez arquivos analisados no delta (+569 / −27), sendo um módulo Python, um arquivo de testes
e oito documentos. `checkpoint-notas.md` ficou fora da leitura, da classificação e do pré-scan.
A nota de Documentation cobre somente as 105 unidades atribuídas à verificação de prosa.

### Secrets Detection

**Status**: `PASS`. Regex e gitleaks verificaram 569 linhas adicionadas em dez arquivos.
Nenhum achado e nenhum erro no JSON do pré-scan.

### Qualidade, segurança e desempenho

A extração dos auxiliares deixa explícita a separação entre validação de Git e identidade física.
No POSIX, o descritor impede que a remoção do marcador siga um novo `.git` no mesmo caminho.
As duas falhas desta rodada estão nos dados que a validação aceita antes dessa remoção.
Nenhuma sonda de r6 usou publicação ou credencial real. A jornada em bares locais confirmou
a retenção quando exigida e a convergência entre bare, status capturado e clone após publicar.
O teste offline, incluído na suíte dirigida, continua a exigir retorno do startup em menos de 1 s.
Não há interface visual no delta.

### Test Coverage

| Produção | Sensor | Resultado |
|---|---|---|
| `rw_store.py` | `test_lean_live.py::LiveTest` | R11 cobre substituição e desaparecimento do checkout e do `.git`, origem, ramo e trava alterados antes da retomada e preservação de arquivos. Ainda não cobre o caminho de hooks com espaço final nem a troca de ramo durante a validação. |

Provas em `21d8e02e03767382b5a97c86e0d55b426906dce0`:

- `env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp PYTHONDONTWRITEBYTECODE=1 bash -c 'source .sdd/config.sh; eval "$TEST_CMD"'` → rc 0. Loja com 154 testes, três pulados por distribuição nativa. Stop com 144
  testes, sem pulos. Adaptadores, catálogo e versões válidos, incluindo watch 0.5.0 e skill 0.12.0.
- `env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests:plugins/retrofit-skill/tests python3 -B -m unittest test_fixture_private test_lean_auto test_lean_window test_lean_live test_lean_batch test_lean_gate test_auto_docs test_modo_autonomo` → 156 testes, sem falhas nem pulos. A execução nomeada dos cinco casos da célula R11
  também deu rc 0, em 1,801 s.
- `env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B docs/handoffs/20261127-retrofit-watch-050/sonda-qa.py` → rc 0. O ensaio preservou o bare em `583c2bd89242`. Nova aprovação após emenda
  convergiu em `a2b12d71e206`. A janela cumprida publicou em `af314dd9d33e` sem aprovação.
  O revert voltou a reter em `3bcf0bc431b7`. Na rota manual, só a confirmação levou bare, status
  capturado e clone a `734e13376b01`. A rota não testa uma decisão de modelo nem uma API real.
- Em cópia descartável, `python3 -B -m unittest test_lean_live.LiveTest` passou 34 casos sem pulos.
  A retirada isolada de quatro guardas fez falhar os casos nomeados de origem declarada, ramo,
  escopo worktree e bytes do hook. Sem a comparação do descritor em `_finish_live_setup`, o mesmo
  conjunto acusou a falta do marcador do substituto na subprova de abertura
  (`FileNotFoundError` ao ler o arquivo) e, em cascata, a recusa por destino existente na subprova
  de remoção. Nenhuma variante falhou ao compilar ou importar.

### Documentation Sync

| Material | Resultado |
|---|---|
| README, contrato do clone, changelog e referência do modo autônomo | Descrevem a intenção de R11. A distância entre o contrato e as duas reproduções foi atribuída ao código em R12. |
| Handoff de EXEC, checkpoint e r5 | As três saídas específicas pedidas na r5 agora constam no handoff. Algumas medições citadas nesta rodada ainda não têm a saída completa preservada no delta. |

### Código morto

`ruff check --no-cache --select F401,F821,F841 plugins/retrofit-watch/skills/retrofit-watch/{scripts/rw_store.py,tests/test_lean_live.py}`
→ rc 0. Os novos auxiliares têm chamadas no setup, e o literal da trava é usado na escrita e na
conferência. Sem símbolo introduzido ou tornado órfão no delta. Varredura de legado fora desta rodada.
O sensor de backlog confirmou 42 âncoras, nenhuma fora do alvo. A camada 1 passou contra `origin/main`.

### Overall Grade

| Criterion | Grade | Rationale |
|-----------|-------|-----------|
| Code Quality (Zen) | A | A validação da configuração e a remoção ancorada do marcador têm responsabilidades separadas. |
| Type Safety | A | A identidade usa pares de dispositivo e inode, o marcador é comparado em bytes e não houve nomes ou imports inválidos no lint. |
| Error Handling | B | A retomada pode dar sucesso com o hook inativo ou com o ramo trocado no mesmo diretório. |
| Security | A | O pré-scan não encontrou credenciais e a jornada mostrou as retenções esperadas sem efeitos fora dos bares de fixture. |
| Performance | A | A validação nova roda no setup explícito. O teste offline manteve o startup independente do fetch. |
| Test Coverage | B | R11 e a jornada passaram, mas os dois estados incorretos reproduzidos ainda não têm regressões permanentes. |
| Documentation | B | As saídas pedidas na r5 foram incorporadas. Outras medições históricas no delta têm exemplos ou resumos sem a saída completa. |
| **Overall** | **B** | R11 corrigiu casos concretos em fb134ce. Os dois casos novos impedem o aceite técnico e ficam em R12. |

As letras são as mesmas da r5. Error Handling e Test Coverage continuam em B, apesar
dos casos de R11 comprovadamente fechados. O platô está registrado no gate e a rodada
não dá aceite técnico nem inicia outra revisão nesta sessão.

## Achados da rodada

| # | Severidade | Achado | Onde |
|---|---|---|---|
| 1 | MEDIUM | A validação remove espaço significativo de `core.hooksPath`. Aceita como ativa uma trava que o Git procura em outro diretório. O clone sai da pendência e aceita commit na `main`. | `plugins/retrofit-watch/skills/retrofit-watch/scripts/rw_store.py:1022` |
| 2 | LOW | O ramo pode mudar no mesmo checkout depois da conferência e antes de remover o marcador. A identidade de ambos os diretórios permanece válida e o setup libera uma cópia fora da `main`. | `plugins/retrofit-watch/skills/retrofit-watch/scripts/rw_store.py:1058` |
| 3 | MEDIUM | O caminho alternativo do Windows detecta a troca, mas pode apagar o marcador do clone substituto antes de devolver a falha. É a limitação já registrada pelo EXEC. | `plugins/retrofit-watch/skills/retrofit-watch/scripts/rw_store.py:999` |
| 4 | LOW | A contagem total das mutações de R11 e outras medições históricas aparecem como relato. O delta não preserva a saída completa para conferi-las. | `docs/handoffs/20261127-retrofit-watch-050/20-handoff-exec.md:119` |

### Reprodução

As sondas de caracterização usaram Git 2.43.0 e `PrivateWorld` de `test_lean_live`
em `21d8e02e03767382b5a97c86e0d55b426906dce0`. Em cada caso, a preparação
`LiveTest._leave_pending_setup()` deixou a cópia pendente por uma recusa real de origem,
encerrou a interferência na origem e manteve o clone e o marcador.

1. Na cópia pendente, gravei `core.hooksPath` com `git config --worktree` para o nome
   absoluto de `.git/rw-live-hooks` mais um espaço final e confirmei que esse outro diretório
   não existia. A saída real de `git config --show-scope --type=path --get core.hooksPath`
   preservou o espaço antes da quebra. `live-setup` devolveu rc 0, o marcador sumiu e
   `live_clone` aceitou a cópia. Um `git commit --allow-empty` avançou o HEAD da `main`.
   O teste atual muda o caminho para `.githooks`, que não se confunde com o caminho esperado.
2. Na retentativa, executei o `_live_remote` real e, antes de devolver o resultado,
   usei `git switch -qc rascunho` no mesmo checkout. `live_setup` retornou o destino,
   o marcador sumiu e a cópia ficou elegível em `rascunho`, com o mesmo SHA de HEAD.
   A prova existente troca para `rascunho` **antes** de chamar o setup. O caso novo
   exige que o operador tenha alterado o clone dedicado no intervalo da validação.
3. Em Linux, selecionei somente o ramo `nt` de `rw_store` com dublê. Logo antes do
   `Path.unlink`, movi o clone pendente e coloquei no destino uma cópia com os mesmos
   bytes de marcador. A chamada recusou por troca de identidade, mas o marcador no
   substituto desapareceu e ele ficou elegível. A cópia movida manteve seu marcador.
   O dublê mede a ordem das operações, não o comportamento de handles no Windows nativo.
4. O trecho de R11 preserva cinco exemplos de contraprova, não a linha de total. A r5
   também relata pré-scan sem achados, ausência de publicação externa e busca sem
   ocorrência, sem preservar todas as saídas correspondentes. Não há evidência de
   que os resultados relatados estejam errados. Esta rodada repetiu cinco contraprovas,
   o pré-scan do seu próprio delta e a jornada em fixture, sem extrapolar para o histórico.

## Incrementos de conserto (R<n>)

| R<n> | Achado | Check escrito no checkpoint |
|---|---|---|
| R12 | 1 e 2 | Duas regressões nomeadas de retomada, preservação de arquivos de R10 e repetição da jornada de QA. |

## O que virou incremento

```text
| R12 | Conferir o caminho exato da trava e não liberar o clone se o ramo mudar durante a validação | `(env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -m unittest test_lean_live.LiveTest.test_setup_retry_rejects_hooks_path_with_trailing_space test_lean_live.LiveTest.test_setup_retry_does_not_finalize_branch_changed_during_validation test_lean_live.LiveTest.test_setup_retry_keeps_files_after_final_origin_rejection >/dev/null && env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B docs/handoffs/20261127-retrofit-watch-050/sonda-qa.py >/dev/null); echo $?` → `0` | pending | — |
```

- R11 fechado em `fb134ce` para o conjunto exercitado no Linux. Passaram a recusa de
  destino removido ou substituído, origem declarada divergente, ramo não main já na
  entrada e trava estática incompleta. O teste de R10 manteve o mesmo inode e arquivo
  após corrigir a configuração. O Subteste POSIX de abertura e remoção confirma que
  o marcador do substituto permanece.
- O achado de prosa da r5 sobre as três saídas históricas específicas foi atendido em
  `fb28160`. O handoff agora mostra o Red de planejamento, os dois controles e o
  total das 34 mutações de R9 e a jornada da r4.

## O que foi refutado

- **A receita do TEST_CMD contém escapes que impedem a execução.** Conferi
  `20-handoff-exec.md:26` e `40-review-r5.md:42` pelo texto e comparei com os respectivos
  campos `gate` decodificados por PyYAML. Os dois têm `eval "$TEST_CMD"`, sem barras.
  Os escapes visíveis no frontmatter são de YAML. A mesma receita executada em r6 deu rc 0.
- **A verificação POSIX ainda segue uma troca de `.git` na abertura.** O controle de 34
  casos passou. Só ao retirar a comparação do descritor a contraprova perdeu o marcador
  do substituto. A falha do achado 2 conserva os dois diretórios e muda apenas o ramo.
- **Um caminho errado de hooks já é coberto em qualquer forma.** O sensor com `.githooks`
  detecta um caminho claramente diferente. A sonda com espaço final comprovou um caso
  em que a leitura do setup e o diretório usado pelo Git divergem.

## Achados fora de escopo

- O achado 3 continua no item “A remoção do marcador do setup no Windows ainda depende do caminho”
  de `TODO.md`. Exige prova nativa e uma remoção ancorada. O item já nasceu nesta missão.
- O achado 4 fica no item “Medições históricas da atribuição sem saída preservada”
  de `TODO.md`, que já traz a recorrência desta missão. A gramática do backlog não
  duplica a mesma missão.
- A corrida do avanço depois da prova de ancestralidade não foi revisada de novo.
  Seu código não entrou no delta. O achado 2 ocorre na finalização do setup.

## Pendências / Decisions for a Human

O platô de Error Handling e Test Coverage fica visível no gate. Não há decisão nova
de desenho para as regressões de R12. A validação em Windows nativo e a adoção privada
continuam fora das provas desta rodada.

## Boot da próxima fase

Se o ciclo seguir para EXEC, comece pelo Red de R12 em `checkpoint.md`. Faça o Git real
preservar o espaço final do caminho de hooks e confira rc, marcador e bloqueio de commit
na variante íntegra. Na prova de ramo, altere o mesmo checkout depois da validação de
origem. Exija recusa, preservação do marcador e dos arquivos e nenhuma troca de ramo
pelo setup. Preserve R10 e os controles de identidade de R11. Repita a jornada de QA.

### Ações recomendadas

- **Críticas e de alta prioridade** — Nenhuma.
- **Corrigir no EXEC** — R12.
- **Manter no backlog** — Prova nativa do Windows e preservação das saídas históricas.

_Cost footprint: versão local 2.27.38 conferida, instruções e ferramentas do cache instalado
2.30.2 para escopo e verificação de prosa. Código e varredura inline, um verificador
gpt-6.1-terra, sem relançamento, 105 unidades lidas em oito arquivos. A próxima
invocação pode recarregar os plugins para alinhar a cópia inicial ao cache instalado._
