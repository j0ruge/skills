---
missao: 20261127-retrofit-watch-050
fase: REVIEW
rodada: 20
status: done
sessao: codex-revisao-estatica-r20
data: 2026-11-28 16:41
gate: "Revisão independente estática de 340888ce8d7a98a3739dcaf1eec569334291b005 a 63c093bd2cf2a52e6bbd75f101988f60158ea96f. No SHA exato, 212 dirigidos, TEST_CMD rc 0 (155 loja com 3 pulos e 144 Stop), QA, três provas de distribuição Linux, anonimização e âncoras do TODO passaram segundo o implementador. Nota geral B. Restam o isolamento do verificador de digest e a preservação do diagnóstico da camada 1 privada."
reviewed_head: 63c093bd2cf2a52e6bbd75f101988f60158ea96f
---

# Review — rodada r20 — Stop autônomo e validação do pre-push

## Achados da r19

- O ambiente Git foi movido para o script autônomo. `rw_store` reutiliza a mesma função e `_git` do script carrega suas dependências sem importar `rw_store`. O teste de correlação antes vermelho passou no Stop. `retrofit_watch.py:257` e `:270`, `rw_store.py:94`.
- A saída do Git agora é decodificada com UTF-8 e `surrogateescape`. A validação rejeita o caminho com surrogate para o pedido privado, mantendo a entrada no fluxo manual. O teste POSIX seleciona um caminho que o índice rastreia e confirma o motivo manual. `retrofit_watch.py:277`, `rw_auto.py:520` e `test_lean_auto.py:47`.
- A seção de adoção agora manda sincronizar a loja local e indica as opções exigidas do scanner privado. A porta continua recusando a verificação quando esse scanner falha. Resta preservar a causa nos outros erros de retorno 2. `rw_store.py:601`, `test_lean_gate.py:175` e `docs/retrofit-watch/clone-dedicado.md:8`.
- O wrapper invocado pelo Git repete o digest antes de executar o hook e conserva as guardas de URL, refs e HEAD. O guia descreve os pontos de verificação e limita a garantia aos bytes conferidos. Resta isolar o intérprete auxiliar do ambiente de importação do worktree. `rw_gate.py:1142`, `:1149` e `:1162`, `docs/retrofit-watch/clone-dedicado.md:85`.

## Achados remanescentes

- **Médio — o verificador do digest depende dos imports do worktree.** A nova invocação de `python -c` ocorre no diretório do lote e herda o ambiente Python. O interpretador acrescenta o diretório atual à busca por módulos e pode resolver imports do verificador por módulos que não pertencem à biblioteca padrão. O resultado da checagem deixa de depender apenas do Python confiável e dos bytes do hook. Invocar o intérprete de verificação em modo isolado, mantendo o diretório e o ambiente esperados pelo pre-push original. `rw_gate.py:1149` e `:1171`. [Opções de linha de comando do Python](https://docs.python.org/3.12/using/cmdline.html#cmdoption-I)
- **Baixo — a dica de versão substitui causas operacionais da camada 1.** O retorno 2 também identifica lista inutilizável, falha de Git sobre o par de commits e erro de leitura no scanner atual. A nova guarda descarta a saída desses casos e deixa apenas a sugestão de conferir suporte às opções. Conservar uma causa curta e sanitizada para as falhas operacionais e apresentar a instrução de sincronizar quando cabível. O scanner continua recusando a verificação. `rw_store.py:609`, `:628` e `scripts/anonymity-gate.py:455` e `:466`.

## Evidência e alcance

O implementador confirmou seis provas focadas, 212 dirigidos, QA em bare local, três provas de distribuição Linux, anonimização e âncoras verdes em `63c093b`. O TEST_CMD do mesmo SHA retornou 0 com 155 testes da loja, três pulos configurados e os 144 testes do Stop verdes. A revisão usou leitura estática do delta e resultados existentes. A inspeção manual do delta de produto não identificou credenciais literais. A evidência dinâmica cobre Linux e repositórios de fixture.

### Overall Grade

| Criterion | Grade | Rationale |
|---|---|---|
| Code Quality (Zen) | A | O módulo de entrada possui a lógica de ambiente e `rw_store` reaproveita a função. |
| Type Safety | A | A decodificação preserva os bytes não representáveis e o contrato de caminho privado encaminha a entrada para manual. |
| Error Handling | B | O retorno 2 da camada 1 perde causas operacionais distintas. Preservar o diagnóstico sanitizado e manter a dica de versão. |
| Security | B | O verificador de digest usa o caminho de imports do lote. Isolar o intérprete auxiliar antes da verificação. |
| Performance | A | A consulta Git do Stop mantém seu prazo. O novo cálculo ocorre na publicação e lê o executável do hook. |
| Test Coverage | B | A suíte literal está verde e a fronteira de codificação tem teste. Cobrir o isolamento do verificador e preservar a distinção de erro operacional no scanner privado. |
| Documentation | A | O guia explicita a atualização da loja e os pontos em que o hook é conferido. |
| **Overall** | **B** | Os ajustes centrais estão medidos. Isolar o verificador e preservar a causa do retorno 2 antes de aceitar o delta. |
