---
missao: 20261127-retrofit-watch-050
fase: REVIEW
rodada: 11
status: done
sessao: 01a22204-340d-7401-b23c-6f6a03cddab8
data: 2026-11-28 09:06
gate: "Em 6e1bc9f507f7dc857bc6d8ca763c386bb8329f6a, `env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp/review-r11.oQktbf GIT_CEILING_DIRECTORIES=/tmp PYTHONDONTWRITEBYTECODE=1 bash -c '. .sdd/config.sh && eval \"$TEST_CMD\"'` → rc 0 com adaptadores, catálogo e versões válidos, 154 testes da loja (três pulos nativos configurados) e 144 do Stop sem pulos. Árvore limpa durante os testes. Saída em /tmp/review-r11.oQktbf/test-cmd.log. Gate de REVIEW não passou. Error Handling e Test Coverage permanecem em B (platô nos critérios estritos). Documentation caiu de A para B pela evidência não localizada da suíte ampla no host. R17 pendente. Parada da revisão autônoma para decisão humana."
reviewed_head: 6e1bc9f507f7dc857bc6d8ca763c386bb8329f6a
---

# Review — rodada r11 — Retrofit de skills locais com ensaio antes do push autônomo

## TL;DR

R16 fechou os dois casos da r10. O TEST_CMD, 169 regressões dirigidas e a jornada de QA passaram.
Quatro casos reproduzidos na validação da main viraram R17. Não houve alteração de código nesta revisão.
Nota geral B. Error Handling e Test Coverage ficaram em B. Documentation caiu de A para B.
O platô nos critérios estritos e a regressão editorial pedem decisão humana antes de outra rodada automática.

## Nota da rodada

Delta da skill `base=7f1d9375598e55d8570d962420669e6abcdafc6a` até `6e1bc9f507f7dc857bc6d8ca763c386bb8329f6a` na branch `feat/retrofit-watch-050-loja`.
Escopo de análise com um arquivo de produto, um de testes e sete de documentação. As notas de execução não
fazem parte da análise nem da varredura contabilizada. O handoff de QA orientou a jornada repetida.

### Secrets Detection

| Arquivo | Linha | Tipo | Severidade |
|---|---|---|---|
| Nenhum | — | — | — |

`PASS`. Regex e Gitleaks analisaram nove arquivos e 306 linhas adicionadas, sem erro.
A saída está em `/tmp/review-r11.oQktbf/secrets.json`.

### Cobertura, documentação e código morto

Os comandos desta seção rodaram em `6e1bc9f507f7dc857bc6d8ca763c386bb8329f6a`, com árvore limpa.

| Prova | Comando | Resultado |
|---|---|---|
| Suíte do runner | `env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp/review-r11.oQktbf GIT_CEILING_DIRECTORIES=/tmp PYTHONDONTWRITEBYTECODE=1 bash -c '. .sdd/config.sh && eval "$TEST_CMD"'` | rc 0, 154 testes da loja com três pulos nativos e 144 do Stop sem pulos. |
| Regressões dirigidas | `env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp/review-r11.oQktbf PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests:plugins/retrofit-skill/tests python3 -B -m unittest test_fixture_private test_lean_auto test_lean_window test_lean_live test_lean_batch test_lean_gate test_auto_docs test_modo_autonomo` | rc 0, 169 testes sem pulos. |
| Jornada de QA | `env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp/review-r11.oQktbf PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B docs/handoffs/20261127-retrofit-watch-050/sonda-qa.py` | rc 0. Ensaio, invalidação por emenda, aprovação, janela, revert e confirmação manual preservaram ou alinharam o bare, o registro, o status e o clone conforme a etapa. |
| Contraprovas de R16 | `env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp/review-r11.oQktbf PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B /tmp/review-r11.oQktbf/contraprovas.py integro` | Três controles verdes, dois Reds na base e quatro mutantes detectados. Os modos são `integro`, `base`, `ignorar-simbolica`, `aceitar-link`, `io-como-ramo` e `ignorar-ramo`. |

Saídas em `/tmp/review-r11.oQktbf/`, incluindo `test-cmd.log`, `directed.log`, `qa.log` e `contraprova-*.log`.
O mapa de cobertura liga `rw_store.py` a `test_lean_live.py`. A sintaxe dos dois arquivos
foi analisada pelo AST. A varredura de órfãos ficou no delta e nas referências ao contrato
existente de `_live_fetch`, sem símbolo ou importação órfã. Não houve mudança de interface visual.

Verificação de prosa restrita às 88 unidades editadas em sete documentos. README e guias descrevem
o clone dedicado e a ref direta. Os casos em que o código não cumpre esse contrato estão na tabela de achados.
A suíte ampla e a distribuição nativa não foram repetidas nesta rodada. O handoff de EXEC
registra a distribuição nativa de R16 em `c83293c` e a comparação da suíte ampla no sandbox.
Esses registros não substituem a saída da execução histórica da suíte ampla no host sobre R15.

### Overall Grade

| Criterion | Grade | Rationale |
|-----------|-------|-----------|
| Code Quality (Zen) | A | A guarda compartilhada concentra o contrato e o delta não deixou importação ou símbolo órfão. |
| Type Safety | A | Os caminhos continuam usando Path, e o avanço distingue explicitamente None dos dois booleanos. |
| Error Handling | B | O setup pode finalizar com main ausente ou redirecionada, recusa uma main empacotada válida e o avanço pode atribuir ao HEAD um erro de leitura da ref. |
| Security | A | A pré-varredura ficou limpa. As sondas não mudaram a origem autorizada. O avanço preservou as refs no erro de leitura. |
| Performance | A | O caminho de elegibilidade segue sem subprocesso novo, com uma inspeção local de metadados e leituras de até 64 e 4 bytes. |
| Test Coverage | B | Os testes de R16 distinguiram a base e quatro mutantes, mas não acusaram os casos confirmados de R17. |
| Documentation | B | Nos trechos editados, as provas de R16 conferem. A afirmação de falha única no host sobre R15 não traz acesso à saída que a comprova. |
| **Overall** | **B** | R16 resolveu os dois casos verificados na r10. Os quatro casos reproduzidos mantêm o gate vermelho. |

## Achados da rodada

| # | Severidade | Achado | Onde |
|---|---|---|---|
| 1 | MEDIUM | Se a main passa a redirecionar depois da guarda e durante a validação da trava, o setup retorna sucesso e remove a pendência sem detectar a troca. Restaurar a ref não permite retomar pelo comando. | `plugins/retrofit-watch/skills/retrofit-watch/scripts/rw_store.py:956`, `:1031`, `:1077` |
| 2 | MEDIUM | Um diretório vazio no caminho da ref solta encobre, para a guarda, uma main empacotada que o Git resolve normalmente. O setup recusa o clone que a base conseguia configurar e avançar. | `plugins/retrofit-watch/skills/retrofit-watch/scripts/rw_store.py:959` |
| 3 | MEDIUM | A ausência da ref solta é tratada como êxito mesmo se a main não existir na tabela empacotada. O setup conclui e a elegibilidade aceita a cópia, mas o avanço falha ao resolver HEAD. | `plugins/retrofit-watch/skills/retrofit-watch/scripts/rw_store.py:963` |
| 4 | LOW | A falha de leitura de `refs/heads/main` na revalidação pré-fetch é registrada como HEAD ilegível quando `.git/HEAD` segue legível. O comando recusa a busca, mas aponta o arquivo errado. | `plugins/retrofit-watch/skills/retrofit-watch/scripts/rw_store.py:961`, `:1165` |
| 5 | MEDIUM | O handoff afirma falha única na execução histórica da suíte ampla no host de R15, sem apontar a saída desse ambiente. O resultado equivalente do sandbox não comprova a contagem do host. Somente prosa e rastreabilidade. | `docs/handoffs/20261127-retrofit-watch-050/20-handoff-exec.md:158` |

**Reprodução com Git 2.43.0 e bares locais.** Execute em `6e1bc9f507f7dc857bc6d8ca763c386bb8329f6a` o comando
`env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp/review-r11.oQktbf PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests REVIEW_BASE=0 python3 -B /tmp/review-r11.oQktbf/ref-main.py -v MainRefProbe.test_main_redirect_during_setup MainRefProbe.test_git_accepts_packed_main_with_empty_loose_dir MainRefProbe.test_setup_rejects_main_missing_from_both_backends MainRefProbe.test_advance_ref_read_error_is_reported_without_fetch`.
O contraste `REVIEW_BASE=1` carrega apenas o arquivo de produto de `7f1d9375598e55d8570d962420669e6abcdafc6a`,
extraído por `git show 7f1d9375598e55d8570d962420669e6abcdafc6a:plugins/retrofit-watch/skills/retrofit-watch/scripts/rw_store.py`. As alterações ocorreram só nas fixtures.

1. A sonda redirecionou a main com `git symbolic-ref` na leitura de `core.hooksPath` após a primeira conferência.
   Os bytes de HEAD e o arquivo local ficaram intactos. O Git passou a resolver HEAD para `refs/heads/rascunho`.
   No delta, o setup retornou sucesso, o marcador sumiu, a elegibilidade recusou e, após restaurar a ref, o
   setup respondeu `destino já existe`. A base também removeu o marcador e, além disso, aceitou o clone.
   O delta reduziu o problema, mas sua nova guarda não acompanha a ref até a liberação.
2. Após `git pack-refs --all`, a sonda criou apenas um diretório vazio no caminho solto.
   `git symbolic-ref HEAD` devolveu `refs/heads/main`, e `git rev-parse --verify HEAD` devolveu
   o SHA empacotado. A candidata respondeu `fora da main`. Na base, o controle passou com um novo
   commit no bare e fast-forward até esse SHA. Trata-se de regressão do teste de tipo adicionado no delta,
   não de uma defesa contra uma ref simbólica.
3. Após `git update-ref -d refs/heads/main`, `git symbolic-ref HEAD` ainda devolveu o nome
   `refs/heads/main`, mas `git rev-parse --verify HEAD` falhou. Ambas as versões removeram o
   marcador, aceitaram a cópia e depois registraram `erro` no avanço. O caso fica no R17 porque o
   novo caminho de fallback adiciona uma decisão explícita de êxito sem constatar a ref empacotada.
4. A contraprova de permissão real usa
   `env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp/review-r11.oQktbf PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B /tmp/review-r11.oQktbf/permission-main.py -v MainPermission.test_ref_not_head`.
   Depois da inspeção bem-sucedida, restringiu só a leitura da ref solta. O teste confirmou
   `PermissionError` nessa ref e leu os mesmos bytes de `.git/HEAD`. Não houve fetch nem mudança no
   HEAD ou em `origin/main`. O único teste falhou pelo detalhe `HEAD do clone ilegível`, com `resultado=erro`.
5. A execução ampla de R16 no sandbox tem saída primária, com 5 falhas e 176 erros em ambas as árvores.
   O registro de R15 sobre o host em `fe7b6ea` só acrescenta a frase ao handoff. Não foi localizada uma
   saída primária para aquela afirmação. Isso não refuta o resultado do host e não exige mudança de código.

As saídas são `ref-main-0.log`, `ref-main-1.log`, `packed-controle.log` e `permission-main.log` em
`/tmp/review-r11.oQktbf/`. A primeira execução com quatro casos na candidata teve três falhas e um erro. Na base,
houve três falhas e o controle de main empacotada passou.

## Incrementos de conserto (R<n>)

| R<n> | Achado | Check escrito no checkpoint |
|---|---|---|
| R17 | Agrupa os achados 1–4. Preservar a pendência e os arquivos na troca da ref, aceitar a main empacotada que o Git resolve, recusar a main ausente e identificar erro de leitura da própria ref sem fetch nem avanço. | `(env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -m unittest test_lean_live.LiveTest.test_setup_keeps_pending_when_main_redirects_during_validation test_lean_live.LiveTest.test_setup_and_advance_accept_packed_main_with_empty_loose_dir test_lean_live.LiveTest.test_setup_rejects_missing_main_ref test_lean_live.LiveTest.test_advance_reports_unreadable_main_ref_separately >/dev/null && env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B docs/handoffs/20261127-retrofit-watch-050/sonda-qa.py >/dev/null); echo $?` → `0` |

Os quatro testes são sensores novos a escrever no EXEC. O Check exige os quatro e a jornada, sem
desfazer a recusa de uma main simbólica nem adicionar subprocesso ao caminho rápido de elegibilidade.

## O que virou incremento

- Achados 1–4 → `R17`. Nenhum código foi alterado nesta revisão.
- Achados 1 e 2 da r10 → resolvidos por `d0edd66` nos cenários daquela rodada. Os testes
  `test_setup_rejects_main_resolving_to_other_branch` e
  `test_advance_reports_unreadable_head_before_fetch` ficaram verdes na versão íntegra e vermelhos
  com o módulo de `7f1d9375598e55d8570d962420669e6abcdafc6a`. O controle de troca de ramo de R15 passou nas duas versões.
  Os quatro mutantes confirmaram os sensores de ref simbólica em arquivo, ref simbólica em link, I/O em
  HEAD e recusa de ramo errado. O achado 1 desta rodada muda a ref só depois da guarda, e o achado 4
  afeta a leitura da ref, não a leitura de HEAD.

```md
| R17 | Validar a main efetiva até a liberação, aceitar a ref empacotada válida e diagnosticar a ref inacessível | `(env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -m unittest test_lean_live.LiveTest.test_setup_keeps_pending_when_main_redirects_during_validation test_lean_live.LiveTest.test_setup_and_advance_accept_packed_main_with_empty_loose_dir test_lean_live.LiveTest.test_setup_rejects_missing_main_ref test_lean_live.LiveTest.test_advance_reports_unreadable_main_ref_separately >/dev/null && env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B docs/handoffs/20261127-retrofit-watch-050/sonda-qa.py >/dev/null); echo $?` → `0` | pending | — |
```

## O que foi refutado

- A ref simbólica já presente deixaria o clone elegível → refutado pelos controles de R16, inclusive
  sem o marcador e com a variante de link simbólico. O Red de r11 mede a troca posterior à conferência.
- O avanço buscaria apesar de erro de leitura de HEAD ou classificaria a ocorrência como ramo errado
  → refutado por R16. O erro da ref solta também conserva as refs, mas identifica o arquivo errado.
- Toda ausência de ref solta indicaria main quebrada → refutado pelo controle empacotado de R16.
  Um empacotamento válido, uma main ausente e um diretório solto vazio têm resultados Git distintos.
- Faltariam evidências das medições em r10 → refutado para segredos, as duas contagens e a ausência de
  fetch. O evento 19 de `REVIEW-20261128-083611-fce3cbf8.stream.jsonl` contém o JSON da varredura.
  `clone.log` e `related.log` em `/tmp/review-r10.jJFbXK/` registram 55 e 94 testes sem pulos.
  A sonda `head-io.py` verifica ausência de fetch e identidade de refs antes das asserções que falharam
  em `head-io-final.log` e `head-io-1.log`. Quanto a órfãos, o diff e as referências remanescentes
  confirmam que o contrato de chamada continua em uso. Não é necessário um log só para declarar zero.
- Faltariam evidências das 169 regressões e dos dois controles de oito provas em R16 → refutado
  pelas saídas dos eventos 60, 70, 78, 81 e 102 de `EXEC-20261128-084445-30fd19f2.stream.jsonl`.
  Esta rodada repetiu as 169 regressões. A falta de saída do host de R15 permanece separada.

## Achados fora de escopo

- O achado 5 de prosa pertence ao item aberto «Medições históricas da atribuição sem saída preservada»
  no `TODO.md`. A recorrência desta missão já existe na linha `RECURRED`, sem duplicação nem incremento.
- Continuam no backlog a corrida depois da prova de ancestralidade, a remoção do marcador por caminho
  no Windows e a falha preexistente da segunda skill full. Não foram reabertas nesta revisão do delta.

## Pendências / Decisions for a Human

Decidir se vale autorizar outra rodada após o R17. O conserto de R16 tem evidência independente,
mas Error Handling e Test Coverage continuam em B e Documentation caiu de A para B em relação à r10.
Esse é o ponto de parada do ciclo autônomo. R17 registra o trabalho reproduzido para uma retomada
autorizada. O resultado histórico do host não altera o estado de `TEST_CMD` nesta revisão.

### Ações recomendadas

**Corrigir obrigatoriamente (CRITICAL)**

Nenhuma.

**Corrigir com prioridade (HIGH)**

Nenhuma.

**Corrigir ou considerar (MEDIUM/LOW)**

Se houver retomada, fechar R17 com as quatro regressões em Git local e repetir a jornada de QA.
Na triagem do backlog editorial, ligar o resultado histórico à saída do host ou qualificá-lo como relato.

**Adiado por forma**

Nenhum item novo.

_Cost footprint: codereview 2.27.38 na cópia solicitada, 2.30.2 no fluxo instalado de verificação por unidades. Três verificadores gpt-6.1-terra, 9–72 chamadas informadas por agente. Um arquivo de produto e um de testes avaliados no agente principal, com varredura de órfãos inline._
