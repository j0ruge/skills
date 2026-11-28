---
missao: 20261127-retrofit-watch-050
fase: REVIEW
rodada: 19
status: done
sessao: codex-revisao-estatica-r19
data: 2026-11-28 16:38
gate: "Revisão independente estática de 4e57bd124f0c5009e3a9f77a221e26e44e208039 a 340888ce8d7a98a3739dcaf1eec569334291b005. A execução literal nesse SHA registrou 155 testes da loja, três pulos e uma falha entre 144 testes do Stop. 210 dirigidos, QA em bare, três provas nativas Linux, camada 1 e TODO verdes. Nota geral B, com ajustes de compatibilidade e de verificação do hook."
reviewed_head: 340888ce8d7a98a3739dcaf1eec569334291b005
---

# Review — rodada r19 — Evidência do lote privado e publicação

## Achados

- **Médio — o helper Git quebrou a cópia isolada do Stop.** O _TEST_CMD_ falhou em `test_oversized_saved_correlation_is_disabled_before_metadata`. O teste carrega uma cópia autônoma de `retrofit_watch.py`, e a nova importação de `rw_store` em `_git` deixa o processo sem esse módulo. O cenário de correlação excedida perde sua passagem pelo evento seguinte. Manter o ambiente Git no módulo de entrada e permitir que `rw_store` o reutilize. Conferir a suíte literal no próximo SHA. `retrofit_watch.py:251` e `test_retrofit_watch.py:2546`.
- **Médio — um caminho Git fora de UTF-8 pode interromper o Stop inteiro.** A descoberta do caminho exato pede saída de índice terminada em NUL, com o nome em bytes, mas a camada de subprocesso usa decodificação de texto estrita. A exceção pode chegar à varredura antes de `valid_skill_path` classificar a evidência. Uma entrada incompatível pode impedir o processamento das outras entradas da sessão. Ler e comparar o registro do índice em bytes, ou tratar a falha de decodificação na fronteira e encaminhar a skill para o fluxo manual. `retrofit_watch.py:251`, `:426` e `:1315`, `rw_auto.py:520`.
- **Médio — o scanner privado exige uma versão que a loja local pode ainda não ter.** O selo e a porta usam o scanner extraído de `origin/main` do clone local da loja. A chamada privada exige `--private` e `--head`, adicionados neste delta. O fluxo privado não atualiza essa ref e a fixture carrega a versão corrente do scanner desde a inicialização. Um plugin atualizado com a loja local ainda na versão anterior recebe erro genérico de camada 1 no selo e na publicação. Manter a recusa e apresentar um diagnóstico acionável de incompatibilidade. Documentar a atualização exigida da loja antes de usar o fluxo privado. `rw_store.py:623` e `:727`, `rw_gate.py:147`, `scripts/anonymity-gate.py:432` e `fixture_store.py:163`.
- **Médio — a identidade do pre-push é conferida antes de iniciar o processo que o executa.** A porta valida o digest antes de chamar Git. O wrapper confirma URL e refs, mas executa o caminho atual do hook sem vincular a execução ao conteúdo que passou no ensaio. O teste cobre mudança anterior à chamada de push. Amarrar o executável que o wrapper usa à identidade ensaiada no ponto de execução, preservando o hook, seus argumentos, o worktree e as guardas existentes. Ajustar a garantia do guia à verificação efetiva. `rw_gate.py:983`, `:1129` e `:1153`, `docs/retrofit-watch/clone-dedicado.md:81`.

## Contratos conferidos

O Stop reconfere o checkout e a origem no orçamento compartilhado. O pedido grava a identidade e o caminho literal, e o preparo e a porta exigem um `SKILL.md` regular nesse caminho exato. Pedidos privados antigos sem caminho são encaminhados para nova evidência ou resolução manual. O selo e a porta usam o par de commits fixado, e o parecer de diff é carregado uma vez na passagem privada. O patch privado considera as posições dos hunks e as listas da loja. A aprovação só se aplica ao patch registrado e o scanner privado inclui essas listas sem a exceção do fluxo full. `rw_auto.py:183`, `rw_store.py:416`, `:525` e `:623`, `rw_gate.py:268` e `:927`.

A janela só conta publicações cuja ordem após os reverts pode ser comprovada por ancestria. Um revert independente conserva o ensaio, conforme o guia. A prova de varredura confere presença e OID dos blobs exportados, lista de entradas do scanner e identidade do cache. O lote de avanços continua após uma falha individual. Os Checks I1–I4 desarmam as variáveis de localização do Git herdadas do runner. O status privado usa a última linha do pre-push real quando disponível, inclusive em retomada, com mensagem própria se a saída não puder ser recuperada. `rw_store.py:813`, `:1523`, `:1543` e `:1653`, `rw_gate.py:1164` e `:1458`, `checkpoint.md:10`.

## Evidência e alcance

O implementador confirmou no SHA `340888c` 210 testes dirigidos, QA em bare, três provas nativas Linux, camada 1 e TODO verdes. A execução literal do TEST_CMD nesse SHA passou os 155 testes da loja, com três pulos, e registrou uma falha entre 144 testes do Stop. Modo instalação e check privado também tiveram evidência nos controles informados. A revisão usou leitura estática e resultados existentes. A inspeção manual do delta de produto não identificou credenciais literais. A evidência de publicação e retomada usa Linux e repositórios de fixture.

### Overall Grade

| Criterion | Grade | Rationale |
|---|---|---|
| Code Quality (Zen) | B | A importação nova rompe o ponto de entrada autônomo. Manter o helper de ambiente no módulo de entrada e reaproveitá-lo no restante do produto. |
| Type Safety | B | A saída do índice em bytes passa por um decodificador de texto estrito. Preservar os bytes até a validação ou tratar a falha como evidência manual. |
| Error Handling | B | A loja local antiga retorna falha genérica da camada 1. Identificar a incompatibilidade e encaminhar a atualização da ferramenta confiável. |
| Security | B | A verificação do hook antecede o processo que abre o executável. Vincular a execução à identidade ensaiada no wrapper. |
| Performance | A | As consultas do Stop e da janela compartilham prazo e a validação de blobs ocorre no fluxo que exige prova completa. |
| Test Coverage | B | A suíte literal contém uma falha. Revalidar o Stop no próximo SHA e cobrir a recusa de scanner incompatível e a verificação efetiva do hook. |
| Documentation | B | Alinhar a garantia do hook ao ponto de verificação e registrar a versão mínima exigida da loja local. |
| **Overall** | **B** | Os contratos centrais têm evidência dirigida, mas o Stop literal e os pontos de compatibilidade e identificação do hook exigem os ajustes descritos. |
