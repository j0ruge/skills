---
missao: 20261127-retrofit-watch-050
fase: REVIEW
rodada: 7
status: done
sessao: codex-review-skills-r7
data: 2026-11-28 07:39
gate: "Em 31121ec9c32753fef955eda376d18e2c26d828b4, a revisão independente do Codex confirmou os 46 testes do clone e a jornada de QA. TEST_CMD e os 16 checks passaram na árvore de produto 39490d1. Dois falsos sucessos do setup reproduzidos receberam o incremento R13. Nota geral B."
reviewed_head: 31121ec9c32753fef955eda376d18e2c26d828b4
---

# Review — rodada r7 — Retrofit de skills locais

A prova de R12 fecha o caso do espaço final no caminho da trava e a troca de `main` para outro ramo durante a consulta de origem. **Nota geral B.** Ainda há dois falsos sucessos no setup. A ordem nova pode validar em `rascunho` uma origem efetiva que não vale em `main`. Também é possível trocar de ramo depois de `symbolic-ref`, enquanto o setup ainda verifica a trava.

- Repositório `j0ruge/skills`, branch `feat/retrofit-watch-050-loja`, checkout `/home/joruge/.wt/skills-sdd-loja-v050`.
- HEAD revisado `31121ec9c32753fef955eda376d18e2c26d828b4`. Base da r6 `21d8e02e03767382b5a97c86e0d55b426906dce0`.
- Delta de três commits, seis arquivos, +256/−10. O produto e os testes são idênticos ao ancestral `39490d17b420bc0d5ff016ce92337059416c329e`. Entre os dois SHAs mudam somente o handoff de EXEC, o checkpoint e as notas do checkpoint.

### Secrets Detection

| Arquivo | Linha | Tipo | Severidade |
|---|---|---|---|

**Status** `PASS`. Regex e gitleaks leram as 256 linhas adicionadas nos seis arquivos e devolveram zero achados e zero erros. Em execução independente no HEAD, `anonymity-gate.py --camada1 --base origin/main` devolveu `ok: camada 1 limpa`, usando a ref local.

### Achados acionáveis

| # | Severidade | Evidência no HEAD | Achado e ação |
|---|---|---|---|
| 1 | MEDIUM | `rw_store.py:1058–1062`, `1095–1099` e `1103–1108` | **O setup pode validar a origem efetiva no ramo errado e liberar a cópia em `main`.** Configuração Git condicional ao ramo pode reescrever a URL. A nova ordem consulta a origem antes de exigir `main`. Se o operador trocar para `main` nesse intervalo, a origem declarada e a trava passam, mas a origem efetiva validada já não vale. O marcador some, a cópia fica elegível e a próxima guarda recusa antes do fetch. Exigir `main` também antes da validação de origem e adicionar a regressão com configuração por ramo. |
| 2 | LOW | `rw_store.py:1019–1026` e `1061–1062`, `test_lean_live.py:421–438` | **Uma troca de ramo durante a leitura da trava ainda finaliza o setup fora da `main`.** A nova regressão injeta a troca no retorno de `_live_remote`, antes da leitura de `HEAD`. Durante `git config`, depois de ler `HEAD`, a mesma troca conserva a identidade física e passa. Faça a última verificação de ramo depois da inspeção da trava, imediatamente antes da finalização ancorada, e cubra essa fronteira. Isso reduz a janela medida, sem tornar atômica a coordenação com Git externo. |
| 3 | LOW | `20-handoff-exec.md:132,138,145–146`, `checkpoint.md:25` | O handoff anuncia 16 Checks, mas a tabela de artefatos ainda diz 14 e o primeiro boot de QA manda começar em R11. Corrigir para 16 e apontar primeiro para R12 e suas duas regressões, preservando R11 como controle. |

As referências `rw_store.py` e `test_lean_live.py` apontam, respectivamente, para `plugins/retrofit-watch/skills/retrofit-watch/scripts/rw_store.py` e `plugins/retrofit-watch/skills/retrofit-watch/tests/test_lean_live.py`. Os dois documentos citados ficam em `docs/handoffs/20261127-retrofit-watch-050/`.

**Caracterização independente.** Git 2.43.0, `PrivateWorld` e cópia pendente produzida pela recusa real usada em `LiveTest._leave_pending_setup`. `GIT_DIR` e `GIT_WORK_TREE` desarmados e cada `TMPDIR` isolado sob `/var/tmp`. Os dublês sincronizam a troca, mas as consultas e os comandos de troca de ramo são do Git real.

- Achado 1. `includeIf.onbranch:main.path` aplicou a reescrita de URL só em `main`. A origem correta foi consultada em `rascunho`. Um `git switch main` antes do retorno da guarda deixou o setup retornar o destino, sem marcador, com cópia elegível, origem declarada correta e origem efetiva errada. A mesma guarda, chamada de novo em `main`, recusou. Contra o módulo da base r6 lido com `git show`, a mesma sonda recusou antes da consulta de origem, com marcador presente e cópia inelegível. Nenhum fetch ou push para a origem desviada foi tentado.
- Achado 2. Um `git switch -qc rascunho` imediatamente antes do `git config --show-scope` de validação deixou o setup retornar o destino, sem marcador e elegível em `rascunho`. Os inodes do checkout e do `.git`, bem como o SHA de `HEAD`, permaneceram iguais. Não é a corrida do avanço nem a troca de diretório do Windows.
- Controle do achado 1 da r6. Com um espaço final em `core.hooksPath`, o CLI devolveu rc 1 e erro de trava, preservou os bytes do marcador e manteve a cópia inelegível. Retirado o override, a mesma chamada devolveu rc 0 e o hook real bloqueou `git commit --allow-empty` com a mensagem esperada, sem mover `HEAD`.

### Qualidade, segurança e desempenho

O delta conserva a separação entre a identidade física e as consultas ao Git. Remover só o delimitador final evita a perda do espaço significativo. Os falsos sucessos reproduzidos nesta rodada decorrem da coordenação entre condições lidas em momentos diferentes, não de exceção engolida ou quebra na rota POSIX ancorada. A guarda de fetch ainda recusa a origem reescrita no caso observado. Não se mediu vazamento, publicação incorreta ou acesso externo. O custo adicional no caminho alterado é uma comparação da identidade em setup explícito. O teste de startup offline passou na execução independente de `test_lean_live`.

### Test Coverage

| Verificação | Prova |
|---|---|
| Red e Green de R12 | `r12-red.log:5,13,23` mostra duas falhas por ausência de `StoreError`. `r12-matrix.log:136–143` mostra R12 rc 0 e as três regressões da célula, incluindo a preservação de arquivos de R10. A jornada de QA da célula também passou novamente no HEAD. |
| Testes do clone e jornada repetidos no HEAD | `test_lean_live` passou 46/46 em 11,950 s, incluindo as regressões novas em `test_lean_live.py:421,440`. A sonda de QA passou retenção, emenda e nova aprovação, janela, revert e a rota manual com e sem confirmação. Comparou bare de fixture, `local/ci` capturado, registro e clone. |
| Suíte e matriz em `39490d1` | `r12-full.log:5–12` mostra 154 testes da loja com três pulos e 144 do Stop sem falhas. Adaptadores, catálogo e versões passaram no TEST_CMD. `r12-matrix.log` registra rc 0 para I1–I4 e R1–R12. `r12-targeted.log:3–5` registra 158 testes sem falhas. |
| Provas separadas em `39490d1` | `r12-stop.log` mostra a regressão de atribuição verde e silêncio nos três controles. `r12-qa.log` mostra a progressão completa em bare de fixture. `r12-native.log` registra três testes verdes com Codex CLI 0.172.0 e o SHA de produto nos três registros. `r12-privacidade.log` registra camada 1 limpa. |
| Fronteiras que a matriz não mede | A regressão de R12 cobre a troca na saída da validação da origem, não a troca durante a conferência da trava. Não há caso com reescrita efetiva dependente do ramo na suíte de setup. As duas caracterizações acima confirmam os resultados que faltam à matriz. |

Os logs `r12-*.log` foram conferidos em `/tmp/skills-sdd-l2.oHhti50i/`. A suíte ampla e os três testes nativos foram conferidos pelos logs do ancestral de produto, não reexecutados nesta rodada. QA usa fixture local e não demonstra adoção externa ou compatibilidade em Windows nativo.

### Documentation Sync

O contrato de `docs/retrofit-watch/clone-dedicado.md:11–17` exige que a origem efetiva corresponda no clone em `main`, com trava ativa, antes da liberação. A divergência reproduzida pertence ao código. O handoff atual registra o SHA de produto e as provas da r7 que vieram de R12. Resta atualizar a contagem e o ponto de partida de QA no achado 3. A prova histórica de mutações da r6 continua separada da evidência atual.

### Código morto

Sem símbolo novo ou tornado órfão no delta. Os auxiliares reordenados têm chamadas no mesmo módulo e as regressões são descobertas por unittest. `ruff check --no-cache --select F401,F821,F841` passou nos dois arquivos Python alterados. A varredura de legado não faz parte desta rodada.

### Conciliação com a r6 e o backlog

- R6 #1, espaço final, fechado no caso reproduzido. R6 #2, troca no mesmo checkout, fechado na fronteira agora exercitada pelo teste de R12. O achado 2 atual demonstra que a garantia mais ampla ainda não vale durante a verificação da trava.
- R6 #3 permanece no `TODO.md:275–280`. A rota Windows que remove o marcador por caminho está inalterada. Os três testes de distribuição no host Linux não são prova nativa do Windows.
- R6 #4 permanece no `TODO.md:206–212`. O handoff preserva os exemplos, mas não a saída completa da contagem histórica de 33 mutações em R11. Isso não invalida os resultados atuais de R12 nem foi reclassificado como novo.
- A corrida após a última conferência do **avanço** permanece no `TODO.md:268–273`. Na versão atual está entre `rw_store.py:1138` e `1139`, fora do delta de produto. Não a confundi com o achado 2, que ocorre no **setup**.

### Overall Grade

| Criterion | Grade | Rationale |
|-----------|-------|-----------|
| Code Quality (Zen) | A | O delta é pequeno e conserva a separação entre validação Git, identidade física e remoção ancorada. |
| Type Safety | A | Os valores alterados mantêm os contratos de caminho, identidade e marcador, e o lint dirigido ficou limpo. |
| Error Handling | B | Dois intercalamentos reproduzidos removem o marcador e reportam sucesso quando a validação deveria recusar a liberação. |
| Security | A | Pré-scan e anonimização passaram, e a guarda seguinte recusou a origem errada antes de qualquer fetch no caso medido. |
| Performance | A | A conferência adicional roda no setup explícito, e o teste independente de startup offline passou. |
| Test Coverage | B | R12, controles e jornada passaram, mas os testes permanentes não cobrem os dois falsos sucessos reproduzidos. |
| Documentation | A | As medições atuais são conferíveis e o contrato permanece claro, com uma inconsistência editorial localizada no handoff. |
| **Overall** | **B** | R12 melhora os dois casos previstos, mas não dá aceite a um setup que ainda libera a cópia com invariantes inconsistentes. |

### Ações recomendadas

**Corrigir obrigatoriamente (CRITICAL)**

_Nenhuma._

**Corrigir com prioridade (HIGH)**

_Nenhuma._

**Corrigir ou considerar (MEDIUM/LOW)**

- Na próxima correção do setup, cobrir a origem condicional ao ramo e a troca durante a leitura da trava. Exigir recusa, preservação dos bytes do marcador, inelegibilidade e retomada após corrigir o estado. Não estender a correção à corrida de `live-advance` nem à rota nativa do Windows sem escopo próprio.
- Atualizar a contagem e o boot de QA do handoff. Manter o backlog histórico sem duplicar itens.

_Cost footprint: codereview v2.27.38 da cópia local indicada, seis arquivos no delta, análise e varredura inline, zero agentes adicionais. Sem edição do checkout ou interação com GitHub._
