---
missao: 20261127-retrofit-watch-050
fase: REVIEW
rodada: 21
status: done
sessao: codex-revisao-estatica-r21
data: 2026-11-28 16:44
gate: "Revisão independente estática de 63c093bd2cf2a52e6bbd75f101988f60158ea96f a f56d7a3fae360d67fe3e1ac78e2c167a3c83d36c. Os dois achados da r20 foram tratados. No SHA exato, duas provas do delta, 212 dirigidos, TEST_CMD rc 0, QA em bare, três provas nativas Linux, TODO, camada 1 e check-private-names verdes segundo o implementador. Nota geral A no delta."
reviewed_head: f56d7a3fae360d67fe3e1ac78e2c167a3c83d36c
---

# Review — rodada r21 — Verificador isolado e diagnóstico da camada 1

## Achados da r20

- **Isolamento do verificador de digest.** O wrapper invoca o próprio interpretador em modo isolado com `-I`. O diretório atual, os módulos do usuário e variáveis `PYTHON*` ficam fora do ambiente de importação do verificador. A opção se aplica ao auxiliar de hash. O hook original preserva os argumentos, o worktree e a entrada conferida pelo wrapper. O teste lê o wrapper entregue ao Git, verifica a opção e segue pela publicação em bare da fixture. `rw_gate.py:1149` e `:1162`, `test_lean_gate.py:262` e `:275`. [Modo isolado do Python](https://docs.python.org/3.12/using/cmdline.html#cmdoption-I)
- **Diagnóstico da camada 1 privada.** Com retorno 2, a porta agora mantém o código e a saída do scanner, normalizada para uma linha e limitada a 350 caracteres. A mensagem também conserva a orientação para conferir a compatibilidade do scanner do `origin/main` local. A verificação continua recusada. O teste exige a causa e a orientação na mesma ocorrência de `StoreError`. `rw_store.py:609` e `test_lean_gate.py:175`.

A revisão estática não identificou novo achado material no delta. A alteração em `TODO.md` atualiza a âncora de `_startup_git` para a definição no candidato.

## Evidência e alcance

O implementador confirmou em `f56d7a3` as duas provas do delta, 212 testes dirigidos e TEST_CMD com código 0. A suíte da loja executou 155 testes com três pulos configurados e o Stop executou 144 testes verdes. Também passaram a jornada em bare local, as três provas separadas de distribuição no Linux, a forma e as âncoras do TODO, a camada 1 e o `check-private-names`. A suíte ampla do SHA ainda estava em execução ao fechar o parecer.

A revisão usou leitura estática e resultados existentes. A inspeção manual do delta de produto não identificou credenciais literais. As provas de execução abrangem Linux e repositórios de fixture.

### Overall Grade

| Criterion | Grade | Rationale |
|---|---|---|
| Code Quality (Zen) | A | O wrapper recebe a opção no ponto de invocação e a camada 1 mantém o tratamento de erro no caminho existente. |
| Type Safety | A | A saída registrada permanece texto e os parâmetros do digest continuam passados como argumentos separados. |
| Error Handling | A | O retorno 2 conserva a causa operacional limitada e a instrução de compatibilidade, com recusa da verificação. |
| Security | A | O intérprete do digest fica isolado do ambiente de importação do worktree. As guardas e a invocação do pre-push original foram preservadas. |
| Performance | A | O delta mantém o número de subprocessos e o prazo da publicação. |
| Test Coverage | A | Os dois tratamentos têm provas no candidato e o TEST_CMD literal passou no mesmo SHA. |
| Documentation | A | A orientação de sincronização segue coerente com o diagnóstico e a âncora alterada aponta para a função atual. |
| **Overall** | **A** | Os dois achados da r20 estão tratados no delta, com evidência dirigida e suíte literal verdes no SHA revisado. |
