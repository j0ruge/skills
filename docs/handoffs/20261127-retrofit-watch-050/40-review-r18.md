---
missao: 20261127-retrofit-watch-050
fase: REVIEW
rodada: 18
status: done
sessao: codex-revisao-estatica-r18
data: 2026-11-28 16:11
gate: "Revisão independente estática de 8df070f1fc00c4b8d31a611c9a72ce061a5c3c32 a 4e57bd124f0c5009e3a9f77a221e26e44e208039. O achado da r17 foi tratado em 4d2a22f. O delta posterior muda dois documentos e tem 44 contratos verdes. Nota geral A."
reviewed_head: 4e57bd124f0c5009e3a9f77a221e26e44e208039
---

# Review — rodada r18 — Preservação da causa durante a limpeza

## Achado da r17

A liberação da trava do índice e o descarte da pasta de evidência passam por um único tratador. Qualquer causa primária em trânsito entra no detalhe antes da mensagem da etapa de limpeza que falhou. A liberação continua antes do descarte. Quando a pasta já foi criada, a falha aponta para a pendência e o resultado carrega o OID observado. Sem pasta criada, o erro conserva as duas causas no registro de avanço. O caso previamente inconclusivo mantém a mensagem e o OID que já apontavam para a pendência. `rw_store.py:1391`, `:1401` e `:1443`.

A nova regressão começa com uma falha ordinária de instalação do índice. Após a restauração, a falha de remoção da evidência exige as duas causas no registro e comprova o OID inicial, o índice anterior preservado, a trava liberada e a árvore limpa. O implementador registrou Red em `8df070f` e Green em `4d2a22f`. O controle anterior da falha de `unlink` depois de um avanço continua cobrindo a preservação do novo OID e da pasta. A composição da causa para `unlink` foi conferida por leitura do tratador compartilhado. `test_lean_live.py:1141` e `:1266`.

Entre `4d2a22f` e `4e57bd1`, o runbook do clone documenta a ref explícita, a inspeção de `.git/rw-live-advance` e a resolução da pendência antes de repetir `publish`. A rotina de publicação retoma os efeitos do lote publicado e o avanço recusa proceder enquanto a pendência existir. O checklist editorial vincula o P2 à atualização nomeada e mantém os limites de Windows e adoção real. O diff desse intervalo tem dois arquivos de prosa e as árvores de produto e testes são idênticas. `docs/retrofit-watch/clone-dedicado.md:38` e `:87`, `45-docs.md:15`, `rw_gate.py:1391` e `rw_store.py:1433`.

A revisão estática não identificou novo achado acionável no delta.

## Evidência e alcance

O implementador registrou 28 casos de avanço e 192 regressões dirigidas verdes em `4d2a22f`, além de TEST_CMD com 154 testes da loja incluindo três pulos configurados e 144 testes do Stop, QA em bare local, camada 1, TODO e três provas de distribuição Linux. O implementador registrou 44 contratos verdes de documentação e modo autônomo depois do delta exclusivamente documental em `4e57bd1`. A revisão usou leitura do delta e dos resultados existentes. A inspeção manual do delta de produto não identificou credenciais literais.

A evidência de avanço vem de Linux com Git 2.43 e repositórios de fixture. Após estado inconclusivo, a retomada continua condicionada à inspeção manual de ref, travas, índice e arquivos. A execução nativa do avanço no Windows permanece fora da evidência.

### Overall Grade

| Criterion | Grade | Rationale |
|---|---|---|
| Code Quality (Zen) | A | Um tratador identifica a etapa de limpeza e reaproveita a composição do diagnóstico. |
| Type Safety | A | O OID observado chega ao erro de avanço no mesmo formato e a etapa de limpeza tem rótulo explícito. |
| Error Handling | A | A causa primária é agregada tanto na liberação da trava quanto no descarte da pasta. O OID e a pendência seguem disponíveis conforme o estado verificado. |
| Security | A | A atualização explícita da ref e a guarda de origem permanecem nas mesmas funções, e o delta se limita ao tratamento local de erros. |
| Performance | A | O delta conserva a ordem e o número de operações de limpeza e não acrescenta subprocessos. |
| Test Coverage | A | A regressão de erro combinado tem Red e Green. O controle de unlink e os 28 casos de avanço mantêm a evidência dos outros caminhos. |
| Documentation | A | O runbook exige resolver a pendência antes de repetir publish. O checklist e os 44 contratos sustentam o delta documental. |
| **Overall** | **A** | O único achado aberto da r17 foi tratado no código medido. O delta documental alinha a retomada ao fluxo verificado. |
