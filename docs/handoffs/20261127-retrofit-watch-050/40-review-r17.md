---
missao: 20261127-retrofit-watch-050
fase: REVIEW
rodada: 17
status: done
sessao: codex-revisao-estatica-r17
data: 2026-11-28 16:09
gate: "Revisão independente estática de f1bbf79f4c5bb5a54d1edacc433e3a092f77f878 a 8df070f1fc00c4b8d31a611c9a72ce061a5c3c32. Nota geral B. O encerramento forçado preserva a pendência, a falha na liberação preserva o OID observado e o TODO descreve a ref explícita. A limpeza ainda pode esconder a causa primária de um erro ordinário."
reviewed_head: 8df070f1fc00c4b8d31a611c9a72ce061a5c3c32
---

# Review — rodada r17 — Evidência e desfecho do avanço

## Achados da r16

- O encerramento forçado durante a preparação agora produz `LiveAdvanceUncertain` antes da escrita e preserva a pendência. O stdout da transação e o stderr local ficam separados. Uma nova tentativa encontra a pendência antes do fetch. O teste confere o encerramento, os arquivos de evidência, a ref intacta e a recusa da próxima tentativa. `rw_store.py:1239`, `:1273`, `:1391` e `:1434`. `test_lean_live.py:1111`.
- A liberação da trava do índice agora ocorre antes do descarte da evidência. Se a ref já avançou, uma falha de liberação conserva a pasta e registra o OID observado. Se a causa já tiver sido classificada como inconclusiva, o diagnóstico da liberação é acrescido à mensagem anterior. `rw_store.py:1397`, `:1402` e `:1444`. `test_lean_live.py:1141`.
- O TODO registra o P2 como resolvido por `a5a2302`, com âncora na transação de `refs/heads/main`. A revisão confirmou o OID anterior esperado e o HEAD temporário destacado no caminho de materialização. A recuperação manual e a validação nativa da plataforma continuam delimitadas em seus registros. `TODO.md:275`, `rw_store.py:1245` e `:1331`.

## Achado remanescente

- **Baixo — uma falha de limpeza ainda pode substituir a causa primária.** Em `rw_store.py:1402`, a falha de `unlink` agrega a mensagem primária apenas se a exceção já for `LiveAdvanceUncertain`. Quando a preparação recusa ou a instalação do índice falha com rollback verificado, a exceção ordinária pode ser substituída pelo diagnóstico de remoção da trava. A falha em `rmtree` também descarta a causa que já estava sendo propagada. O registro usa o texto da exceção final, embora a causa anterior exista no encadeamento interno. O OID observado continua preservado nos caminhos com pendência. Acrescentar a causa primária existente ao detalhe das duas falhas de limpeza, mantendo o OID e o destino da evidência. Cobrir a combinação de um erro ordinário com uma falha de limpeza. `rw_store.py:1394`, `:1405`, `:1414` e `:1444`.

## Evidência e alcance

O implementador registrou dois Reds em `f1bbf79` e Green em `8df070f`. O primeiro controle usa um processo simulado para testar o encerramento forçado. O segundo confirma uma falha de remoção após avanço bem-sucedido, com o OID novo e o índice anterior ainda observáveis. As outras evidências registradas incluem 191 regressões dirigidas, 27 casos de avanço, TEST_CMD com 154 testes da loja e três pulos configurados mais 144 testes do Stop, QA em bare local, três provas nativas no Linux, camada 1 e forma e âncoras do TODO. A leitura do teste de liberação confirmou que o avanço principal é bem-sucedido antes da falha de limpeza. A combinação com uma causa primária ordinária fica fora dessa prova.

A suíte ampla de R22 registrou 634 testes e a única falha preexistente de atribuição da segunda skill full. A ampla de R23 estava em execução na revisão. A análise foi estática e considerou a evidência existente em Linux com Git 2.43 e repositórios de fixture. A recuperação de estado inconclusivo exige inspeção manual de ref, travas, índice e arquivos. A validação nativa desse avanço em Windows permanece pendente. A inspeção manual do delta de produto não identificou credenciais literais.

### Overall Grade

| Criterion | Grade | Rationale |
|---|---|---|
| Code Quality (Zen) | A | A liberação antecede o descarte e os estados observados governam a retenção das evidências. |
| Type Safety | A | A transação conserva os OIDs como dados do Git e permite representar OID inconclusivo no registro. |
| Error Handling | B | A limpeza pode ocultar um erro ordinário anterior. Acrescentar a causa primária às mensagens de unlink e rmtree e conservar o OID observado. |
| Security | A | A atualização real segue com ref e OID anterior explícitos. O diagnóstico bruto da transação fica na pendência local. |
| Performance | A | O delta mantém os prazos da transação e acrescenta apenas a gravação local do diagnóstico no avanço fora do Stop. |
| Test Coverage | B | Os dois Reds distinguem os consertos. Falta comprovar que uma falha de limpeza mantém uma causa primária já existente. Cobrir o erro combinado. |
| Documentation | A | O TODO referencia o mecanismo atual e o guia indica a evidência preservada e as verificações antes da retomada. |
| **Overall** | **B** | A pendência e o OID observado são preservados nos novos casos. A aceitação do delta ainda requer manter a causa primária quando a própria limpeza falhar. |
