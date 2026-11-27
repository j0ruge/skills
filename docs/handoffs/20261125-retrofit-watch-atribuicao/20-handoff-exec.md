---
missao: 20261125-retrofit-watch-atribuicao
fase: EXEC
status: done
sessao: 01a21dfc-0d15-76d1-9462-b7c2f9b68576
data: 2026-11-27 14:16
gate: 'env -u GIT_DIR -u GIT_WORK_TREE PYTHONDONTWRITEBYTECODE=1 bash -c ''source .sdd/config.sh && eval "$TEST_CMD"'' em 830629b → rc 0. Loja com 154 testes (3 pulados). Hook com 98 testes. Adaptadores e catálogo válidos. Versão 0.4.1 confirmada. Os nove Checks de checkpoint.md passaram.'
---

# Handoff — EXEC — Atribuição da retrofit-watch por mensagem

> Escrito no fim de cada fase. A próxima fase é uma **sessão nova sem memória**: se algo que ela
> precisa saber não está aqui (ou nos artefatos linkados), está perdido.

## TL;DR

R7 conserva o encerramento gravado na 0.4.0 e a marca de colisão de um ID pendente sem origem.
O metadado atrasado e o ID reutilizado ficam em silêncio, sem crédito futuro.
O slash explícito, a carga nova e o ID novo continuam atribuindo o trabalho.
O TEST_CMD e os nove Checks passaram. QA deve repetir as duas jornadas de R7.

## Estado do repo

- **Branch:** `fix/retrofit-watch-atribuicao-mesma-mensagem`, em Git isolado pelo runner.
- **Último commit do incremento:** `830629b` — preservar o encerramento e a colisão na retomada.
- **Working tree:** limpo após o commit deste registro.
- **Suíte:** `env -u GIT_DIR -u GIT_WORK_TREE PYTHONDONTWRITEBYTECODE=1 bash -c 'source .sdd/config.sh && eval "$TEST_CMD"'` em `830629b` → rc 0. Loja com 154 testes (3 pulados). Hook com 98 testes. Adaptadores e catálogo válidos. Versão 0.4.1 confirmada.
- **E2E:** os nove Checks de `checkpoint.md` passaram em `830629b`, incluindo a jornada de terminal de F1.
- **Release:** `env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -m unittest test_auto_docs.ReleaseTest.test_the_four_places_agree_at_0_4_0_or_later` em `830629b` → 1 teste, rc 0.

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

- `43c2d49` — persistiu a ordem de chegada separada dos vínculos consumidos ou removidos por erro. No R3, outra chamada pendente na mesma mensagem preservava sua posição ao perder um vínculo.
- `43c2d49` — descarta o vínculo falho e mantém seu ID separado somente na mensagem ativa. Reusar o mesmo ID nessa mensagem não prova a origem. O estado anterior reconstrói a ordem a partir da mensagem ativa e dos vínculos disponíveis.
- `43c2d49` — cinco testes de Stop adicionados e o controle de crescimento ampliado. Em `f382fa2`, a sonda de R3 e os três testes do Red reproduziram as seis divergências. Após o fix, 25 degradações foram detectadas em cópias temporárias, com grupo próprio, timeout de 20 s e 512 MiB de memória virtual.

### Retorno da revisão — rodada r4

- `893c9c6` — preserva a ordem de uma mensagem sem vínculos enquanto outra posterior aguarda confirmação. O histórico de IDs inválidos acompanha as mensagens retidas, inclusive antes da primeira carga reconhecida.
- `893c9c6` — separa pendências de IDs falhos, consumidos ou ambíguos. A janela tem teto de 64 mensagens e 1.024 IDs retidos. Acima do teto, o Stop persiste a perda de precisão na sessão e mantém os contadores e as invocações explícitas.
- `893c9c6` — adiciona 11 testes de Stop. Em `b3e9117` sem a correção, a sonda de R4 mostrou as quatro divergências e os dois testes principais falharam em oito subcasos. Em Green, foram detectadas 58 degradações em cópias temporárias com grupo próprio, teto de 25 s e 512 MiB de memória virtual.
- `893c9c6` — nos lotes de 10, 100 e 1.000 falhas em mensagens distintas, o estado reteve zero registros sem pendência e somente a chamada antiga no cenário concorrente. O metadado dessa chamada ainda gerou retro de `graphify`.

### Retorno da revisão — rodada r5

- `c52f09c` — conserva a marca sem dono ao colidir com uma tentativa posterior. A poda continua retirando
  a posição da tentativa sem vínculo. A janela, os tetos e o descarte ao avançar a mensagem ativa não mudaram.
- `c52f09c` — adiciona uma regressão com 16 casos. Em `c8ddc39`, com o teste novo e sem o ajuste do hook,
  os quatro casos de colisão sem dono falharam. Em Green, todo Stop avançou o offset até o fim do
  transcript sem gerar `errors.log`. A variante ambígua não creditou trabalho, atrito ou retro.
- `c52f09c` — a sonda R5 confirmou `marca_apos_disputa=1` e silêncio após a colisão nos dois modos.
  O controle de ID novo pediu retro de `codereview`. Cinco degradações foram detectadas, com
  grupo de processos próprio, timeout de 25 s e teto de 512 MiB de memória virtual por processo.

### Retorno da revisão — rodada r6

- `cd55517` — mantém separadas a marca de consumo sem origem e a lista de mensagens que colidiram
  com o ID. Podar uma tentativa não apaga a marca sem origem. Avançar a mensagem ativa aposenta
  a marca sem origem e os donos fora da janela, mas preserva os donos ainda retidos.
- `cd55517` — a sonda e o teste de Stop reproduziram o pedido indevido no Red em `274d877`.
  Em Green, o reuso ficou em silêncio, sem crédito futuro. ID novo ainda pede retro de
  `codereview`. Cada Stop conferiu offset completo e ausência de `errors.log`.
- `cd55517` — duas retomadas leram estado gravado por `274d877` antes da colisão, uma para ID novo
  e outra para reuso. O controle de R5 cobre também a poda da mensagem que ainda estava na janela.
  Dezoito degradações foram detectadas em cópias temporárias, em grupo próprio, com timeout de
  25 s e teto de 512 MiB de memória virtual por processo.

### Retorno da revisão — rodada r7

- `830629b` — infere o encerramento da 0.4.0 só se há histórico e nenhuma skill ativa.
  O encerramento explícito do estado atual é preservado. A sessão sem histórico, o slash
  explícito e a carga nova vinculada continuam podendo iniciar outra atribuição.
- `830629b` — distingue uma pendência sem origem de um ID ausente. A colisão mantém sua marca
  quando a tentativa intermediária é podada sem trocar a mensagem ativa. Os controles de ID
  novo e de dono conhecido continuam independentes.
- `830629b` — em `9081588`, a sonda R7 e os dois testes novos em Red apontaram cinco divergências.
  No Green, a sonda também passou com o estado gravado pelo hook real de `fe38d1f` (0.4.0),
  usando a opção `--legado` de `40-review-r7.md`. Os testes de Stop conferem o offset completo,
  a ausência de `errors.log` e trabalho, atrito e revisões sem incremento nos casos negativos.
- `830629b` — onze degradações detectadas pelos quatro testes de Stop de R5, R6 e R7, em cópias
  temporárias com grupo próprio, teto de 25 s e 512 MiB de memória virtual. O controle sem
  mutação passou antes e depois. Cada degradação e seu sensor constam em `checkpoint-notas.md`.

## Artefatos

| Arquivo | O que contém |
|---|---|
| `checkpoint.md` | I1, F1 e R1–R7 com as sondas executáveis e os hashes das correções. |
| `checkpoint-notas.md` | Evidência de execução e isolamento do Git na suíte. |
| `plugins/retrofit-watch/skills/retrofit-watch/tests/test_retrofit_watch.py` | Regressões de Stop com persistência em disco. |
| `e2e/test_retrofit_watch_stop.py` | Jornada de BUG-01 em dois Stops com transcript e estado em disco. |
| `TODO.md` | Issue #12 marcada `RESOLVED by 682cd3d` até o merge. |

## Boot da próxima fase

Leia `checkpoint.md` e rode as nove células de Check da raiz. Use Python 3, Git e um diretório temporário gravável. As jornadas criam transcript e estado próprios, sem iniciar o Claude Code.

- I1 deve imprimir `1 0 1 0 0 1`. F1 deve ficar em silêncio nas três variantes e R1 deve terminar em `regressoes=4`.
- R2 deve emitir `graphify` nas seis combinações e terminar em `falhas=estavel`. Acrescente `plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py --medir` para conferir os lotes. Em `43c2d49` foram 0 vínculos e 292, 293 e 294 bytes após 10, 100 e 1.000 tentativas.
- R3 deve emitir `graphify,graphify` nos quatro pares de ordem, tanto após erro quanto após consumo. Nos dois pares de reuso, o ID novo deve preservar `codereview` e o reaproveitado deve ficar em silêncio.
- R4 deve emitir `graphify,graphify` nos pares de ordem e `codereview,silêncio` nos pares de reuso, tanto em leitura contínua quanto em retomada. Os testes permanentes também interrompem antes e depois do erro e entre as confirmações.

- R5 deve emitir `codereview` para ID novo e silêncio nos casos de reuso, com e sem colisão,
  em leitura contínua e em retomada. Após a disputa, a sonda deve imprimir `marca_apos_disputa=1`.
  O teste permanente reabre o estado em disco antes e depois da colisão e verifica os contadores.

- R6 deve emitir `codereview` para ID novo e silêncio para reuso, em ambos os modos, além de
  `marca_apos_confirmacao=1` e `regressao=1`. A jornada confirma a mensagem depois da colisão
  e antes da externa. O teste permanente verifica também o descarte ao confirmar uma terceira mensagem.

- R7 deve deixar o metadado atrasado em silêncio ao retomar a 0.4.0 já encerrada, mesmo com
  origem preenchida, ausente ou vazia. Slash explícito e carga nova ainda pedem retro de
  `graphify`. Na colisão, o ID novo mantém `codereview` e o reuso fica em silêncio, com e sem
  retomada. Rode a célula R7 até `regressoes=2`. Para a leitura da 0.4.0 real, repita a sonda
  com `--legado` seguindo `40-review-r7.md`.

Rode `env -u GIT_DIR -u GIT_WORK_TREE PYTHONDONTWRITEBYTECODE=1 bash -c 'source .sdd/config.sh && eval "$TEST_CMD"'` e registre a repetição em `30-handoff-qa.md`.

## Pendências / Decisions for a Human

- O merge cabe ao mantenedor. A execução não publicou a versão nem abriu PR.

## Riscos e não-feitos

- Não houve smoke no host Claude Code ou no Windows. As jornadas foram medidas com transcripts sintéticos no formato do hook e persistência em disco.
- Os três testes de distribuição nativa seguem pulados pelo `TEST_CMD` no sandbox. Em um clone temporário de `893c9c6`, `env -u SKILLS_SKIP_NATIVE_DISTRIBUTION python3 -B -m unittest discover -s tests -p test_codex_distribution.py -v` retornou rc 1 nos três por não conseguir criar o namespace Bubblewrap. Nenhum chegou ao primeiro comando do CLI dentro do namespace. Repetir no host com suporte a Bubblewrap.
- O leitor aceita o formato anterior. Donos já omitidos por uma versão anterior não são
  reconstruídos a partir do transcript já consumido.
- Modo autônomo, fila e distribuição Codex ficaram fora do patch.

- A medida de crescimento cobre tentativas em mensagens distintas. IDs de mensagens já aposentadas não integram a janela de correlação. Ampliar o histórico continua fora do R4.

## Achados fora de escopo

- kit: `bin/sdd-codex:468` exporta `GIT_DIR` e `GIT_WORK_TREE` para o Git privado. Na primeira execução literal de `TEST_CMD`, fixtures Git da loja herdaram essas variáveis, geraram commits de teste no espelho privado e a suíte terminou com 2 falhas e 146 erros. O reflog e a árvore idêntica confirmaram a ponta anterior `7bd6eeb`, restaurada no espelho sem editar a árvore de trabalho. A repetição com as duas variáveis removidas passou antes e depois da correção. Isolar as variáveis no ambiente de testes que criam repositórios evita redirecionar `git -C`. Nenhuma mudança foi feita no kit.

- Os dois achados de documentação da rodada r1 permanecem nos itens já abertos em `TODO.md`. A frase apontada pela revisão de R4 foi precisada no registro histórico de R3 acima.

- O reuso de ID depois que a mensagem original sai da janela permanece no item já aberto em `TODO.md`.

- kit: em R2, a execução literal voltou a herdar o Git privado. O reflog e a comparação da árvore confirmaram o início em `0aa7b40`. A ponta e a referência temporária criada pelas fixtures foram restauradas no espelho. A suíte passou com as duas variáveis removidas, antes e depois da correção.

- O metadado externo obsoleto ainda pode encerrar uma carga posterior. O caso anterior a R3 permanece no item já aberto em `TODO.md`.

- kit: a execução literal em R3 voltou a contaminar o espelho Git privado com fixtures. O teste foi encerrado, o reflog e a árvore confirmaram a ponta inicial `f382fa2` e a referência temporária foi removida. As repetições isoladas de `TEST_CMD` passaram antes da correção e no commit final. A correção do ambiente do runner permanece fora da missão.

- A rastreabilidade das medições históricas permanece no item aberto de `TODO.md` apontado pela revisão r5.

- A receita histórica do plano que herda o Git privado continua no item aberto de `TODO.md`
  apontado por `40-review-r7.md`. Execute a receita isolada deste handoff.
