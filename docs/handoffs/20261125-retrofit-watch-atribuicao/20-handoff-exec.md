---
missao: 20261125-retrofit-watch-atribuicao
fase: EXEC
status: done
sessao: 01a215a2-a00f-7ed3-9254-4df0c29dc18b
data: 2026-11-25 23:22
gate: 'env -u GIT_DIR -u GIT_WORK_TREE PYTHONDONTWRITEBYTECODE=1 bash -c ''source .sdd/config.sh && eval "$TEST_CMD"'' em 43c2d49 → rc 0. Loja: 154 testes, 3 pulados. Retrofit-watch: 83 testes. Adaptadores e catálogo válidos. Versão 0.4.1 confirmada. As cinco células de Check passaram.'
---

# Handoff — EXEC — Atribuição da retrofit-watch por mensagem

> Escrito no fim de cada fase. A próxima fase é uma **sessão nova sem memória**: se algo que ela
> precisa saber não está aqui (ou nos artefatos linkados), está perdido.

## TL;DR

R3 preservou a ordem entre mensagens quando uma chamada falha ou é consumida.
Reusar o ID de uma falha da mensagem ativa não preserva mais a atribuição indevida.
A suíte e os cinco Checks passaram. R2 reteve zero vínculos após 1.000 falhas. QA deve repetir as jornadas abaixo.

## Estado do repo

- **Branch:** `fix/retrofit-watch-atribuicao-mesma-mensagem`, em Git isolado pelo runner.
- **Último commit do incremento:** `43c2d49` — preservar a ordem das mensagens e rejeitar IDs falhos.
- **Working tree:** limpo após o commit deste registro.
- **Suíte:** `env -u GIT_DIR -u GIT_WORK_TREE PYTHONDONTWRITEBYTECODE=1 bash -c 'source .sdd/config.sh && eval "$TEST_CMD"'` em `43c2d49` → rc 0. Loja: 154 testes, 3 pulados. Retrofit-watch: 83 testes. Adaptadores e catálogo válidos. Versão 0.4.1 confirmada.
- **E2E:** as cinco células de `checkpoint.md` passaram em `43c2d49`, incluindo a jornada de F1.
- **Release:** `env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -m unittest test_auto_docs.ReleaseTest.test_the_four_places_agree_at_0_4_0_or_later` em `43c2d49` → 1 teste, rc 0.

## O que foi feito

- `682cd3d` — unificou a decisão de atribuição por nome e caminho, com vínculo entre `message.id`, o ID de `tool_use` e `sourceToolUseID`. O estado conserva a origem atual e os vínculos ainda pendentes da mensagem de carga. Metadados obsoletos não reativam a monitorada quando o vínculo correspondente foi descartado.
- `682cd3d` — adicionou 13 testes de regressão e sincronizou manifesto, catálogo Claude, README, SKILL.md e CHANGELOG para 0.4.1.
- No Red, os dois positivos canônicos não emitiram a retro, o caso com blocos agrupados também ficou em silêncio e o metadado atrasado reabriu indevidamente a atribuição.

### Retorno da QA — BUG-01

- `c704301` — persistiu o encerramento entre Stops. Metadado da monitorada sem ID válido não reabre a atribuição encerrada. A confirmação por chamada vinculada e a carga explícita por slash continuam disponíveis. O formato 0.4.0 conserva o fallback e o histórico.
- `c704301` — incorporou à suíte de Stop os casos com ID ausente e vazio e o controle por slash, com metadado atrasado de outra skill intercalado. Em `bf0dae7` com os testes novos e sem a correção, os três falharam por emitirem retro de `codereview`. O caso com ID preservado e o controle da 0.4.0 já passavam. A reprodução de terminal da QA foi preservada.

### Retorno da revisão — rodada r1

- `eb44360` — impede a reabertura com ID desconhecido após encerramento legado e mantém uma marca dos IDs já consumidos enquanto o vínculo ainda é relevante.
- `eb44360` — preserva o slash mais novo ao receber metadado externo atrasado e mantém o vínculo pendente quando uma tentativa posterior não resulta em carga reconhecida.
- `eb44360` — adiciona quatro regressões. As quatro falharam em `1a07661` com os testes novos e sem a correção. Foram detectadas 18 degradações sob grupo de processos próprio, timeout de 20 s e memória virtual de 512 MiB. O arquivo original foi restaurado após cada degradação.

### Retorno da revisão — rodada r2

- `485e6c0` — ao confirmar uma carga, a limpeza retira os vínculos antigos e mantém os das mensagens posteriores. Metadado atrasado da monitorada antiga não reassume a atribuição.
- `485e6c0` — resultado de erro retira só o vínculo da tentativa correspondente, inclusive quando chega em outro Stop sem carga reconhecida. A marca dos IDs consumidos continua protegida.
- `485e6c0` — três testes de Stop novos e um controle ampliado. Antes da correção, dois subcasos pediram retro para `codereview`, e o estado cresceu 28.712 bytes entre 10 e 1.000 falhas. Após a correção, a sonda mediu zero vínculos e estados de 239, 240 e 241 bytes. Foram detectadas 13 degradações com grupo próprio, timeout de 20 s e 512 MiB de memória virtual. A variante equivalente de acesso direto não mudou nenhuma saída.

### Retorno da revisão — rodada r3

- `43c2d49` — persistiu a ordem de chegada separada dos vínculos consumidos ou removidos por erro. Quando há outra chamada pendente, perder um vínculo não muda a precedência da mensagem.
- `43c2d49` — descarta o vínculo falho e mantém seu ID separado somente na mensagem ativa. Reusar o mesmo ID nessa mensagem não prova a origem. O estado anterior reconstrói a ordem a partir da mensagem ativa e dos vínculos disponíveis.
- `43c2d49` — cinco testes de Stop adicionados e o controle de crescimento ampliado. Em `f382fa2`, a sonda de R3 e os três testes do Red reproduziram as seis divergências. Após o fix, 25 degradações foram detectadas em cópias temporárias, com grupo próprio, timeout de 20 s e 512 MiB de memória virtual.

## Artefatos

| Arquivo | O que contém |
|---|---|
| `checkpoint.md` | I1, F1, R1, R2 e R3 com as sondas executáveis e os hashes das correções. |
| `checkpoint-notas.md` | Evidência de execução e isolamento do Git na suíte. |
| `plugins/retrofit-watch/skills/retrofit-watch/tests/test_retrofit_watch.py` | Regressões de Stop com persistência em disco. |
| `e2e/test_retrofit_watch_stop.py` | Jornada de BUG-01 em dois Stops com transcript e estado em disco. |
| `TODO.md` | Issue #12 marcada `RESOLVED by 682cd3d` até o merge. |

## Boot da próxima fase

Leia `checkpoint.md` e rode as cinco células de Check da raiz. Use Python 3, Git e um diretório temporário gravável. As jornadas criam transcript e estado próprios, sem iniciar o Claude Code.

- I1 deve imprimir `1 0 1 0 0 1`. F1 deve ficar em silêncio nas três variantes e R1 deve terminar em `regressoes=4`.
- R2 deve emitir `graphify` nas seis combinações e terminar em `falhas=estavel`. Acrescente `plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py --medir` para conferir os lotes. Em `43c2d49` foram 0 vínculos e 292, 293 e 294 bytes após 10, 100 e 1.000 tentativas.
- R3 deve emitir `graphify,graphify` nos quatro pares de ordem, tanto após erro quanto após consumo. Nos dois pares de reuso, o ID novo deve preservar `codereview` e o reaproveitado deve ficar em silêncio.

Rode `env -u GIT_DIR -u GIT_WORK_TREE PYTHONDONTWRITEBYTECODE=1 bash -c 'source .sdd/config.sh && eval "$TEST_CMD"'` e registre a repetição em `30-handoff-qa.md`. A retomada da revisão segue a decisão do mantenedor registrada em `40-review-r2.md`.

## Pendências / Decisions for a Human

- O merge e a decisão de retomar a revisão após a parada da rodada r2 cabem ao mantenedor. A execução não publicou a versão nem abriu PR.

## Riscos e não-feitos

- Não houve smoke no host Claude Code ou no Windows. As jornadas foram medidas com transcripts sintéticos no formato do hook e persistência em disco.
- Os três testes de distribuição nativa seguem pulados pelo `TEST_CMD` no sandbox. Modo autônomo, fila e distribuição Codex ficaram fora do patch.

- A medida de crescimento cobre tentativas em mensagens distintas. Os IDs falhos da mensagem ativa ficam no estado até a mudança de mensagem reconhecida ou o encerramento sem vínculo.

## Achados fora de escopo

- kit: `bin/sdd-codex:468` exporta `GIT_DIR` e `GIT_WORK_TREE` para o Git privado. Na primeira execução literal de `TEST_CMD`, fixtures Git da loja herdaram essas variáveis, geraram commits de teste no espelho privado e a suíte terminou com 2 falhas e 146 erros. O reflog e a árvore idêntica confirmaram a ponta anterior `7bd6eeb`, restaurada no espelho sem editar a árvore de trabalho. A repetição com as duas variáveis removidas passou antes e depois da correção. Isolar as variáveis no ambiente de testes que criam repositórios evita redirecionar `git -C`. Nenhuma mudança foi feita no kit.

- Os dois achados de documentação da rodada r1 permanecem nos itens já abertos em `TODO.md`.

- O achado r2 #3, reuso de ID entre mensagens, permanece no item já aberto em `TODO.md`.

- kit: em R2, a execução literal voltou a herdar o Git privado. O reflog e a comparação da árvore confirmaram o início em `0aa7b40`. A ponta e a referência temporária criada pelas fixtures foram restauradas no espelho. A suíte passou com as duas variáveis removidas, antes e depois da correção.

- O metadado externo obsoleto ainda pode encerrar uma carga posterior. O caso anterior a R3 permanece no item já aberto em `TODO.md`.

- kit: a execução literal em R3 voltou a contaminar o espelho Git privado com fixtures. O teste foi encerrado, o reflog e a árvore confirmaram a ponta inicial `f382fa2` e a referência temporária foi removida. As repetições isoladas de `TEST_CMD` passaram antes da correção e no commit final. A correção do ambiente do runner permanece fora da missão.
