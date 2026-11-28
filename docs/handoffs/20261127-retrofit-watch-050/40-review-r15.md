---
missao: 20261127-retrofit-watch-050
fase: REVIEW
rodada: 15
status: done
sessao: codex-revisao-estatica-r15
data: 2026-11-28 15:55
gate: "Revisão independente estática de 4f649989c2a3c08cd0cfa79d286dafd990dbd61c a a5a230248776d2e20cf2161be5b75d7d2be51206. Nota geral C. A atualização explícita da main está presente. Permanecem falhas na recuperação após materialização parcial, na interoperabilidade da preparação e no registro do resultado da transação."
reviewed_head: a5a230248776d2e20cf2161be5b75d7d2be51206
---

# Review — rodada r15 — Avanço explícito da main

O delta fixa `refs/heads/main`, verifica o OID anterior, prepara a transação antes da materialização e respeita uma trava de índice já existente. A confirmação da ref e a recuperação precisam refletir o estado real do checkout em caso de falha.

## Achados

- **Alto — uma falha do Git após alterar arquivos pula a recuperação.** Em `rw_store.py:1283`, `applied` só se torna verdadeiro depois de o merge retornar sucesso, embora o merge opere sobre o worktree real. No Git 2.43, os arquivos são aplicados antes da gravação do índice e da atualização do HEAD temporário. Uma falha na gravação do índice temporário ou uma recusa do hook sobre a ref temporária pode ocorrer com os arquivos já alterados. O código aborta a transação de `main`, solta a trava do índice e descarta o estado temporário. Uma nova tentativa pode encontrar a cópia suja com o índice e a ref anteriores. A correção mínima registra a tentativa de materialização antes de chamá-la e trata o erro como estado inconclusivo até conferir ref, índice e arquivos. Recuperar automaticamente apenas quando a identidade e o estado necessário à restauração forem verificáveis. Em interrupção ou falha de I/O no worktree, conservar arquivos e evidências, registrar a pendência e segurar o avanço automático até inspeção. A restauração sem prova pode sobrescrever uma edição do dono. [Ordem da atualização no Git 2.43](https://github.com/git/git/blob/v2.43.0/merge.c#L81-L100) · [Atualização da ref depois do checkout](https://github.com/git/git/blob/v2.43.0/builtin/merge.c#L1481-L1489)
- **Médio — o Git temporário muda a configuração efetiva usada no worktree real.** Em `rw_store.py:1262`, copiar `config.worktree` para outro `GIT_DIR` altera as condições `includeIf.gitdir` e `onbranch`. A configuração específica do clone dedicado é selecionada pelo caminho exato em `rw_store.py:1182`. O merge temporário pode, assim, chamar hooks da configuração comum destinados aos worktrees de lote. O checkout de recuperação também pode chamar `post-checkout`. Para sparse checkout, a preparação muda o caminho de `info/sparse-checkout` sem levar o arquivo de padrões. Preservar a configuração efetiva relevante, os metadados por worktree e os hooks de validação autorizados. Recusar antes da materialização quando a equivalência necessária não puder ser estabelecida. [Includes condicionais](https://git-scm.com/docs/git-config/2.43.0#_conditional_includes) · [Sparse checkout](https://git-scm.com/docs/git-read-tree/2.43.0#_sparse_checkout) · [Hooks de checkout e merge](https://git-scm.com/docs/githooks/2.43.0)
- **Médio — falha de confirmação esconde o resultado efetivo e pode impedir a retomada.** Em `rw_store.py:1228`, o stderr da transação é descartado. Em `rw_store.py:1298`, uma falha após o envio de `commit` pode encontrar `main` já no alvo com o índice instalado e ainda relançar o erro. O registro então conserva `depois=antes` em `rw_store.py:1354`. O Git chama o hook `committed` depois de atualizar as refs, portanto uma espera esgotada pode ocorrer depois de efetivar o avanço. Se o processo ainda estiver em preparação, encerrá-lo à força também pode deixar travas em disco e tornar a tentativa seguinte inconclusiva. Distinguir preparação recusada, confirmação inconclusiva e avanço confirmado. Conservar diagnóstico Git sanitizado e registrar o estado observado depois da operação. Manter informação suficiente para identificar travas e estado da tentativa, sem remover travas de terceiros. [Estados do hook de transação](https://git-scm.com/docs/githooks/2.43.0#_reference_transaction)

## Evidência e alcance

Os resultados do implementador em `checkpoint-notas.md:426` registram 184 testes dirigidos, TEST_CMD com 154 testes da loja e três pulos configurados, 144 testes do Stop, QA em bares locais, três provas de distribuição Linux e camada 1 verdes. A recusa da preparação da ref ficou vermelha na base e verde no candidato. As asserções novas também cobrem uma trava de índice existente, rollback após erro ao instalar o índice, índice dividido legível e preservação de um ramo vizinho e de arquivo ignorado. A recusa ocorre antes da materialização e a falha de instalação ocorre depois de um merge bem-sucedido. Os dois casos deixam em aberto o erro durante a materialização e a confirmação inconclusiva. Os testes estão em `test_lean_live.py:1017`, `:1072`, `:1089`, `:1110` e `:1132`.

A análise consistiu em leitura do delta, do código e da evidência já registrada. A inspeção manual do delta de produto não identificou literais de credenciais. A evidência dinâmica é de Linux e repositórios de fixture. A execução nativa deste avanço em Windows e o estado após uma interrupção abrupta permanecem fora da evidência.

### Overall Grade

| Criterion | Grade | Rationale |
|---|---|---|
| Code Quality (Zen) | B | Os estados `applied` e `installed` não representam a materialização iniciada nem a confirmação inconclusiva. Registrar essas fases antes de cada efeito. |
| Type Safety | A | O delta conserva objetos Path e usa OIDs completos lidos do Git na operação de ref explícita. |
| Error Handling | C | Um erro durante a escrita pode deixar arquivos divergentes, e um erro de confirmação pode ocultar avanço já efetivado. Recuperar sob prova, conservar pendência no estado inconclusivo e reconciliar o resultado observado. |
| Security | A | A transação tem destino e OID anterior explícitos. A validação de origem permanece antes da busca e o delta revisado não contém literal de credencial identificado. |
| Performance | A | O avanço roda fora do Stop e a preparação e a confirmação da ref têm esperas limitadas. |
| Test Coverage | B | Os controles exercitam recusa antes da materialização e falha depois do merge. Falta evidência para erro iniciado durante a materialização e resultado inconclusivo do commit. Acrescentar cobertura de erros normais nessas fases. |
| Documentation | A | O guia registra a ref nomeada, a proteção do índice e os arquivos ignorados. As notas delimitam o backend de arquivos e a plataforma aferida. |
| **Overall** | **C** | A ref alvo é explícita, mas falta preservar e identificar o estado do checkout diante de erros normais. Corrigir a recuperação, a configuração efetiva e o registro antes de aceitar o delta. |
