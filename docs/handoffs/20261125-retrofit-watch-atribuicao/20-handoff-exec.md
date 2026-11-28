---
missao: 20261125-retrofit-watch-atribuicao
fase: EXEC
status: done
sessao: 01a22008-97b9-7ad1-aa29-23211304c9cb
data: 2026-11-27 23:46
gate: 'TEST_CMD em 41f2952 com GIT_DIR e GIT_WORK_TREE removidos retornou rc 0. Loja com 154 testes (3 pulados) e hook com 134. As três provas nativas, a jornada F1 e os controles de R19 e R20 passaram.'
---

# Handoff — EXEC — Atribuição da retrofit-watch por mensagem

> Escrito no fim de cada fase. A próxima fase é uma **sessão nova sem memória**: se algo que ela
> precisa saber não está aqui (ou nos artefatos linkados), está perdido.

## TL;DR

R20 exige um ID válido antes de ignorar metadado externo por aposentadoria.
R19 continua protegendo a transição com dados salvos malformados.
O TEST_CMD, os 22 Checks, F1 e os controles de R19 e R20 passaram.
As três provas nativas passaram no host Linux. A QA começa por R20, R19 e F1.

## Estado do repo

- **Branch** `fix/retrofit-watch-atribuicao-mesma-mensagem`, ligada ao PR #13.
- O incremento mais recente é R20 em `41f2952`. R19 em `bdf75fa` mediu 133 testes do hook.
- O `TEST_CMD` de `.sdd/config.sh` foi executado para R20 com `GIT_DIR` e `GIT_WORK_TREE` removidos. Retornou rc 0 com 154 testes da loja (3 pulados) e 134 do hook. Adaptadores, catálogo e versão 0.4.1 foram validados.
- A suíte `test_auto_docs.ReleaseTest` passou com quatro testes. As três provas de distribuição nativa passaram separadamente no host Linux, fora do sandbox.
- A r30 confirmou rc 0 e a saída esperada dos 22 Checks. F1 manteve `linked=silêncio missing=silêncio empty=silêncio`.

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

### Retorno da revisão — rodada r8

- `8b861d2` — conserva a evidência sem origem quando a segunda chamada reutiliza o ID de uma
  pendência com dono. A poda aposenta o dono que saiu da janela e mantém a marca enquanto a
  mensagem ativa não muda. Os limites de 64 mensagens e 1.024 IDs não mudaram.
- `8b861d2` — na 0.4.0 de `fe38d1f`, `skill_path` gravava `classify_path` em `classified` e chamava
  `_watch(None)` para o resultado nulo. `kit` gravava a chave `kit:<nome>` no mesmo cache, mas
  só chamava `_watch` para resultado não nulo. A migração usa a distinção e mantém a flag
  explícita do estado atual.
- `8b861d2` — Red em `2166607` com três pedidos indevidos na sonda e quatro falhas nos subcasos
  dos dois testes novos. Green com a 0.4.0 real, controles positivos e negativos e onze
  degradações detectadas em cópia temporária. O controle sem mutação passou antes e depois
  com grupo de processos próprio, 25 s e 512 MiB de memória virtual.

### Retorno da revisão — rodada r9

- `8fa5c7d` — consulta uma vez o prefixo da sessão 0.4.0, até o offset salvo, e reutiliza a
  correlação do scanner em estado isolado. Importa apenas o encerramento e os vínculos
  confirmados sem substituir a atribuição gravada ou alterar a janela. O Stop seguinte lê
  só o delta, mesmo quando o metadado ainda não chegou no primeiro Stop.
- `8fa5c7d` — mantém a evidência persistida se não conseguir ler ou validar o prefixo. Se o
  arquivo estiver menor que o offset, não recua para recontar o histórico.
- Red em `adbf954`: a chamada local posterior ficou em silêncio e a confirmação local mais
  antiga pediu retro quando a externa não tinha metadado. O primeiro lote de testes também
  acusou a falta da leitura única e o recuo em arquivo encurtado.
- Green em `8fa5c7d`: os cortes da 0.4.0 real persistiram o mesmo estado antes do delta.
  A confirmação local posterior à externa pediu retro de `codereview`. A anterior ficou em
  silêncio com ou sem metadado externo. O controle sem externa e a carga nova pediram retro.
  Os testes permanentes verificam a leitura única, o offset, a atribuição gravada, os
  contadores, os pedidos pendentes e os resultados já registrados.
- Em cópias temporárias, 38 de 40 execuções mutantes ficaram vermelhas. As outras duas
  ficaram vermelhas após ampliar as sondas e repetir. Os controles sem mutações passaram
  com grupo de processos próprio, 18 s e 512 MiB de memória virtual, antes e após restaurar
  a cópia. Cada resultado, com código de saída e nome da sonda, está nas notas de execução.
  A assinatura de `read_delta` é coberta pelo recuo normal e pela proteção do legado.
  Alterar só o padrão do parâmetro não muda o outro chamador, que sempre usa offset zero.

### Retorno da revisão — rodada r10

- `e65902c` — lê o prefixo uma vez, em linhas limitadas pelo offset salvo, e só importa
  evidência de um prefixo validado. Preserva o slash digitado ainda pendente quando a
  reconstrução confirma a atribuição e o cache. Offset, histórico e contadores não são recontados.
- `e65902c` — registra IDs falhos sem origem na janela já existente. Um reuso não comprova
  que a nova carga veio da mesma mensagem. O controle com ID novo conserva a atribuição.
- `e65902c` — restaura o quinto caso de I1 e F1 sem um `message.id` externo válido.
  O caso correlacionado continua positivo. Não muda nenhuma saída esperada.
- Red em `df6407a`: slash migrado em silêncio, ID falho sem origem creditava `codereview`
  nos dois cortes, prefixo de 160 MiB registrava `MemoryError` sob 256 MiB e I1/F1 davam
  `1 0 1 0 1 1`. Os três testes permanentes falharam antes da mudança de produção.
- Green em `e65902c`: a troca real de binários recuperou o slash correto, manteve silêncio
  para o comando alheio e para reuso de ID falho, e migrou o prefixo de 160 MiB sob 256 MiB.
  As três regressões nomeadas e o teste adicional de leitura interrompida passaram.
  Os 12 Checks igualaram todo o stdout esperado, além de retornarem rc 0.
- Sabotagem final em cópia temporária: 32 de 33 variações detectadas. A assinatura antiga com
  um parâmetro opcional sem uso é equivalente. Os controles rodaram antes e após as mutações
  com grupo de processos próprio, teto de 14 s e 512 MiB de memória virtual.

### Retorno da revisão — rodada r11

- `fb5e489` — mantém a marca sem origem até haver avanço entre mensagens confirmadas.
  Reuso do ID falho fica em silêncio, mas ID novo da mesma mensagem ainda pede retro.
- `fb5e489` — limita a leitura de cada registro na migração a 2 MiB. Se o registro
  não couber, descarta toda a reconstrução e aplica o trecho novo ao estado salvo.
- Red em `8984d38`: a marca passou de `1` a `0` após a primeira confirmação. O
  reuso pediu `codereview` e o registro de 96 MiB deixou o offset parado sob 256 MiB.
  As duas regressões falharam antes da correção.
- Green em `fb5e489`: os dois binários pediram `graphify` e avançaram o offset nos dois
  perfis de prefixo sob 256 MiB. A regressão confere que contadores e histórico não são
  recontados e que vínculos parciais não chegam ao estado.
- Sabotagem em cópia temporária: 16 de 16 variações detectadas. Os controles passaram
  antes e depois, com grupos de processos próprios, teto de 12 s e 512 MiB de memória
  virtual. As notas registram o sensor de cada variação.

- **Suíte:** `env -u GIT_DIR -u GIT_WORK_TREE PYTHONDONTWRITEBYTECODE=1 bash -c 'source .sdd/config.sh && eval "$TEST_CMD"'` em `fb5e489` → rc 0. Loja com 154 testes (3 pulados). Hook com 113 testes. Adaptadores e catálogo válidos. Versão 0.4.1 confirmada.
- **E2E:** os 13 Checks de `checkpoint.md` passaram em `fb5e489`, incluindo F1 e as trocas de versão em R9–R11.

### Retorno da revisão — rodada r12

- `d77e6a1` — quando não há atribuição ativa, a migração parte do encerramento conservador.
  Só uma reconstrução completa e compatível pode substituir esse estado. A proteção não
  importa vínculos parciais e persiste mesmo se o primeiro Stop não tiver trabalho elegível.
- Red em `4837f6e`: a sonda com `--expect` retornou rc 1 com
  `at_limit=silêncio above_delayed=graphify above_delayed_resumed=graphify above_fresh=graphify above_slash=graphify`.
  A regressão falhou em `delayed` e `resumed`. Os controles passaram.
- Green em `d77e6a1`: a célula R12 retornou
  `at_limit=silêncio above_delayed=silêncio above_delayed_resumed=silêncio above_fresh=graphify above_slash=graphify regressao=1`.
  O offset chegou ao fim em todos os cenários. A regressão também confirma que a leitura
  completa sem externa ainda autoriza a carga pendente e que uma atribuição ativa é preservada.
- Cinco mutações detectadas, com controles verdes antes e depois. Cada execução usou grupo
  próprio de processos, timeout de 20 s e teto de 256 MiB de memória virtual.

### Retorno da revisão externa — R13 do PR #13

- `fcbd6cb` — invalida só a atribuição da chamada ativa que falhou, sem apagar vínculos independentes. Registra IDs aposentados com teto de 1.024, retira o ID ao ser reutilizado e mantém o tratamento conservador sem prova. Preserva o slash explícito em tentativa irrelevante e processa blocos válidos de `isMeta` no delta e na recuperação legada.
- `fcbd6cb` — fixa a revisão legada na r1, isola o roteamento Git nas receitas históricas, explicita a origem de `check` na r18 e resolve o caminho do kit no boot de DOCS. As saídas e os campos de evidência histórica foram preservados.
- F1 creditou uma chamada de trabalho a `full:codereview` no primeiro Stop e gravou o encerramento. O segundo permaneceu em silêncio nas três variantes.
- Cinco testes novos exercitam persistência, controles negativos, reuso, teto, falha, slash e migração completa ou parcial. Das mutações dirigidas ao código e à jornada F1, 30 derrubaram seu sensor sob timeout de 25 s e teto de 256 MiB por processo. Os detalhes estão nas notas.

### Retorno da revisão — rodada r23

- `5459e8c` — salva o ID da chamada ativa à parte da origem da mensagem. O erro da própria
  chamada encerra apenas o crédito futuro. Sucesso e erro de outro ID preservam a atribuição.
- `5459e8c` — conserva a marca sem origem enquanto houver donos conhecidos retidos. Só a
  antiguidade comprovada autoriza ignorar metadado externo. Registra as chamadas anteriores
  ao slash para que a confirmação tardia preserve o slash mais novo e só expire o anterior.
- `5459e8c` — cinco regressões duráveis, incluindo retomada legada e replay parcial. No Red,
  em `c82a249`, a sonda reproduziu retro indevida para falha sem mensagem, ID ambíguo e slash
  anterior. Com os testes de execução escritos e o hook antigo, 12 subcasos falharam.
  No Green, os 16 Checks passaram sem alterar os resultados esperados.
- `5459e8c` — corrige a exclusividade do changelog e move a remoção de `GIT_DIR` e `GIT_WORK_TREE`
  para antes do primeiro Git nas receitas de r9 e r10. Com essas duas variáveis apontando para
  um repositório temporário estranho à loja, antes ambas falharam no objeto `fe38d1f`. Depois,
  ambas retornaram rc 0 e o Check de cada rodada manteve a saída esperada.
- 28 mutações detectadas em cópias temporárias, com controle sem mutação verde no mesmo grupo
  isolado, timeout de 25 s e teto de 384 MiB de memória virtual por processo. As notas registram o
  sensor de cada mutação. A normalização do ID foi movida, não suprimida. Repeti-la no ponto antigo
  seria idempotente, mas retirar a validação do ponto novo ficou vermelho com um ID inválido.

### Retorno da revisão — rodada r24

- `1dd3224` — só associa erro à carga ativa quando o ID da chamada foi vinculado sem disputa.
  Uma chamada que repete o ID invalida essa prova, mesmo que a monitorada tenha sido
  reconhecida antes da colisão. Um erro com ID único ainda encerra o crédito, mesmo sem
  ID da mensagem. Colisão de outro ID não invalida a chamada ativa.
- `1dd3224` — valida tipo, comprimento e os dois IDs de `current_origin` antes de deduzir
  `current_call`. Descarta somente a origem inválida e retoma o trabalho a partir do
  offset gravado. Os testes preservam duas chamadas já creditadas e as somam às três novas.
- Treze subcasos falharam com o hook de `7811d0d` antes do conserto. Os dois testes de
  regressão ficaram verdes em `1dd3224`. Dez mutações foram detectadas em cópia temporária,
  após controle verde com grupo de processos isolado, timeout de 25 s e teto de 384 MiB
  de memória virtual por processo. Cada mutação tem seu sensor nas notas de execução.

### Retorno da revisão — rodada r25

- `fcdea17` — mantém o ID direto da nova chamada explícita após esgotar a janela. O erro próprio encerra
  o crédito futuro sem restaurar a origem ou os mapas. Na janela ativa, um ID disputado continua
  sem abrir esse vínculo, e repetir o ID da carga ativa após o limite ainda revoga o vínculo direto.
- `fcdea17` — atualiza guia, SKILL, README e CHANGELOG para distinguir identidade da chamada e prova de
  mesma mensagem. A regressão de Stop cobre 12 subcasos com estado em disco, incluindo os dois limites,
  a ausência de `message.id`, sucesso, erro de outro ID, reuso e metadado que não reativa a atribuição.
- `fcdea17` — no Red em `b3d009c`, a sonda da r25 acusou seis emissões indevidas e o teste durável falhou
  em nove subcasos. No Green, os 18 Checks passaram. Quatro mutações foram detectadas em cópia
  descartável, com grupo de processos próprio, timeout de 20 s e memória virtual de 512 MiB.

### Retorno da revisão — rodada r26

- `a19e5b5` — mantém um registro de até 1.024 IDs distintos vistos depois de perder a janela. Se o
  ID já apareceu, seu erro não encerra o crédito da nova carga. O registro persiste entre
  Stops, não reabre a janela e não dá validade ao metadado externo desconhecido.
- `a19e5b5` — acrescenta dois sensores duráveis para reuso nos dois limites, cortes de Stop,
  reconstrução válida e rejeitada, saturação do registro e vínculo direto da carga ativa.
  A sonda r26 reproduziu seis encerramentos indevidos no Red, e o teste durável reproduziu
  os seis e mais um na retomada de estado legado. No Green, os 19 Checks passaram. Quatorze
  mutações foram detectadas com grupo próprio, timeout de 25 s e memória virtual de 512 MiB.

### Retorno da revisão — rodada r27

- `7b1da02` — guarda até 2.049 IDs ainda retidos, incluindo o disparador da perda da janela
  e os aposentados que ainda estavam disponíveis. Mantém à parte o teto de 1.024 IDs
  distintos observados após o limite, como em R17. Nenhum dos dois registros comprova origem por mensagem. Tipos inválidos voltam vazios
  sem apagar o estado válido da sessão.
- `7b1da02` — acrescenta três testes permanentes. A sonda de janela falhou em 12 casos no Red
  e a de estado repetiu `TypeError` em dois formatos. No Green, os dois limites e os cortes de
  Stop, o histórico retido ou descartado, a reconstrução legada, o erro próprio e o alheio,
  o teto e a retomada com estado inválido passaram. As mutações rodaram em grupo separado
  com teto de 25 s e 512 MiB de memória virtual. Os resultados individuais estão nas notas.

### Retorno da revisão — rodada r28

- `bdf75fa` — normaliza o campo de aposentados quando não for lista e valida seus itens
  antes de montar o snapshot da transição. Conserva os IDs válidos sem aumentar o teto
  nem recuperar IDs já descartados.
- `bdf75fa` — acrescenta uma regressão de Stop com oito casos. No Red, a sonda repetiu
  `TypeError` sem avançar o offset com um objeto e uma lista entre os itens. O teste
  permanente falhou nas seis variantes inválidas. O estado intacto e o campo ausente
  passaram. No Green, a retomada preservou a atribuição e os contadores e avançou o
  offset. Cinco mutações foram detectadas com grupo próprio, timeout de 20 s e
  memória virtual de 512 MiB. Os resultados individuais estão nas notas.

## Artefatos

| Arquivo | O que contém |
|---|---|
| `checkpoint.md` | I1, F1 e R1–R20 com as sondas executáveis e os hashes das correções. |
| `checkpoint-notas.md` | Evidência de execução, isolamento do Git e resultados individuais das mutações de R9–R19. |
| `plugins/retrofit-watch/skills/retrofit-watch/tests/test_retrofit_watch.py` | Regressões de Stop com persistência em disco. |
| `e2e/test_retrofit_watch_stop.py` | Jornada de BUG-01 em dois Stops com transcript e estado em disco. |
| `TODO.md` | Issue #12 e ordem legada marcadas `RESOLVED by 682cd3d` e `RESOLVED by 8fa5c7d` até o merge. |

## Boot da próxima fase

Leia `checkpoint.md` e rode as 22 células de Check da raiz, comparando o stdout completo. Use Python 3, Git e um diretório temporário gravável. As jornadas criam transcript e estado próprios, sem iniciar o Claude Code.

- Comece por R20, R19 e F1. R20 exercita fonte ausente, vazia e inválida. A célula R19 extrai a sonda de `40-review-r28.md` com
  `--expect` e roda a regressão permanente. Confira a retro de `codereview`, o offset no
  fim e a perda da janela sem erro nos três casos da sonda. O teste permanente também
  confere o campo opcional ausente ou inválido, os IDs sobreviventes e os contadores.

- Repita R18 e F1. A célula R18 extrai a sonda de `40-review-r27.md` e executa
  `--expect --group window` e `--expect --group state`. Compare o crédito nos dois limites
  e três cortes, o silêncio para erro próprio novo e o avanço do offset após retomar
  um registro inválido. Depois, repita R15 a R17. A suíte também inclui
  `test_transition_history_keeps_retained_ids_only_and_stays_bounded`.

- Repita R17 e F1. O Check de R17 extrai a sonda de `40-review-r26.md` e usa `--expect`.
  Deve haver retro de `codereview` para ID em disputa ou alheio e silêncio para falha própria,
  em leitura contínua e com corte de Stop antes ou depois da carga. A suíte também testa
  o teto do registro direto e que sua presença não faz o hook ignorar metadado externo.

- Repita R16 e F1. A célula R16 extrai a sonda de `40-review-r25.md` com `--expect`.
  Compare silêncio e encerramento nos dois limites, inclusive em retomada e sem `message.id`.
  Sucesso e reuso observado na janela ativa devem pedir retro. A célula roda a jornada
  F1 e a regressão durável, que também verifica erro de outra chamada, reuso do ID ativo
  depois do limite e ausência de reativação pelo metadado tardio.

- Confira R15. A célula R15 extrai a sonda de `40-review-r24.md` com `--expect`.
  Confira silêncio para falha própria com e sem ID de mensagem, `codereview` para ID
  distinto ou disputado, e avanço sem `errors.log` com origem intacta, curta,
  numérica ou em objeto. A mesma célula roda a jornada de F1 e os dois testes duráveis.

- Repita R14 e F1. A célula R14 extrai a sonda de `40-review-r23.md` com `--expect`
  e executa a jornada de Stop. Compare os nove pares completos, com crédito e encerramento
  preservados em disco e com a distinção entre ID ambíguo e ID aposentado.
  Para repetir a checagem das receitas de r9 e r10, extraia os blocos Python como nas células
  do checkpoint e execute-os com `GIT_DIR` e `GIT_WORK_TREE` apontando para uma fixture Git.
  Os blocos devem consultar a história da loja e manter o stdout esperado quando a célula o filtra.

- Repita R13 e F1. R13 extrai a sonda de `plano-r13.md` e mede falha, sucesso, ID aposentado,
  ID desconhecido, slash e bloco inválido com e sem retomada. F1 deve provar que o primeiro Stop
  creditou o trabalho à monitorada e já salvou o encerramento. Execute `TEST_CMD` com
  `GIT_DIR` e `GIT_WORK_TREE` removidos da suíte para isolar os repositórios das fixtures.

- Em seguida, rode R12. A célula extrai a sonda de `40-review-r12.md`, roda a migração sob
  256 MiB e exige silêncio no limite e acima dele, inclusive após um Stop sem trabalho.
  Exija `graphify` para carga nova e slash explícito, avanço de offset e `regressao=1`.

- Repita R11. A célula em `checkpoint.md` executa a sonda de `40-review-r11.md`
  e as duas regressões duráveis. Exija `marca_novo=1,1`, `marca_reuso=1,1`, silêncio
  no reuso e `codereview` para ID novo nos dois modos. Sob teto de 256 MiB, os quatro
  subprocessos das duas versões devem pedir `graphify` e avançar o offset, tanto no
  prefixo de linhas curtas quanto no de registro de 96 MiB. Depois confirme que o
  registro grande não trouxe consigo contadores ou vínculos do prefixo.

- Repita R10. A célula em `checkpoint.md` extrai a sonda de `40-review-r10.md`
  e a 0.4.0 de `fe38d1f`, roda os dois hooks em diretórios temporários e exige `prefixo_041=ok`,
  `checks_i1_f1=2` e `regressoes=3`. Confira também os controles de slash alheio, externa
  sem vínculo e ID novo. Não é preciso iniciar, parar ou reiniciar uma sessão real de Claude Code.

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

- R8 deve manter `codereview` com ID novo e ficar em silêncio com ID repetido, em leitura
  contínua e com estado em disco. A retomada deve mostrar `marca_apos_poda_novo=1` e
  `marca_apos_poda_reuso=1`. Para a 0.4.0 real, a sonda de `40-review-r8.md` extrai `fe38d1f`
  do Git local. O legado sem externa e a carga nova devem pedir retro, enquanto o metadado
  atrasado após externa deve ficar em silêncio tanto no legado quanto no estado atual.
  Na célula R8, exija `regressoes=2`. Os testes verificam offset completo, ausência de
  `errors.log` e contadores zerados nos casos negativos.

- R9 deve repetir as quatro jornadas do Check com a 0.4.0 de `fe38d1f`. Confira o silêncio
  nos dois cortes com a externa posterior e o pedido nos casos de carga local posterior
  e de sessão sem externa. Rode também os testes `test_legacy_*` via TEST_CMD para cobrir
  metadado no Stop seguinte, ausência de evidência, carga nova e preservação do estado.

Rode `env -u GIT_DIR -u GIT_WORK_TREE PYTHONDONTWRITEBYTECODE=1 bash -c 'source .sdd/config.sh && eval "$TEST_CMD"'` e registre a repetição em `30-handoff-qa.md`.

## Pendências / Decisions for a Human

- O merge do PR #13 segue a delegação full e a verificação do SHA pelo worker.

## Riscos e não-feitos

- R19 conserva os IDs válidos ainda retidos ao desligar a janela, mas não recupera os já descartados.
  O registro de IDs novos de R17 mantém o próprio teto. Quando ele enche, IDs novos deixam
  de provar erro próprio. Nenhum dos registros prova que duas cargas são da mesma mensagem.

- Um estado intermediário já salvo sem ID da chamada e sem origem de mensagem não prova qual
  chamada abriu a atribuição. Se não houver reconstrução legada, a comparação começa nas
  cargas observadas com o código novo. Ordem de slash não gravada não prova precedência.
- As medições de R14 e R15 não incluem as provas de distribuição nativa. R20 confirma
  as três provas no host Linux.

- Não houve smoke no host Claude Code ou no Windows. As jornadas foram medidas com transcripts sintéticos no formato do hook e persistência em disco.
- Os três testes de distribuição nativa seguem pulados pelo `TEST_CMD` no sandbox. Em um clone temporário de `893c9c6`, `env -u SKILLS_SKIP_NATIVE_DISTRIBUTION python3 -B -m unittest discover -s tests -p test_codex_distribution.py -v` retornou rc 1 nos três por não conseguir criar o namespace Bubblewrap. Nenhum chegou ao primeiro comando do CLI dentro do namespace. O R20 confirmou as três no host.
- A consulta ao trecho já consumido só vale na migração da 0.4.0. Se o trecho não
  estiver utilizável ou contradisser a atribuição gravada, prevalece a evidência persistida.
  O limite de 2 MiB por registro vale para a reconstrução do prefixo, não para um delta
  novo. Sem atribuição ativa, uma reconstrução não comprovada deixa a sessão em silêncio
  para metadado atrasado sem vínculo, até uma carga confirmada no trecho novo.
- Modo autônomo, fila e distribuição Codex ficaram fora do patch.

- R13 mantém até 1.024 IDs aposentados à parte da janela ativa. Quando a prova sai do limite,
  se perde ou o ID é reutilizado, o hook volta às regras normais de correlação. Um ID reaproveitado
  após sair da janela ainda pode se parecer com um vínculo novo, conforme o item aberto no backlog.
- As três provas nativas foram tentadas nesta sessão no HEAD inicial `824db1f` com
  `env -u GIT_DIR -u GIT_WORK_TREE -u SKILLS_SKIP_NATIVE_DISTRIBUTION python3 -B -m unittest discover -s tests -p test_codex_distribution.py`.
  As três pararam em `bwrap: No permissions to create new namespace`, antes de executar o CLI
  dentro do namespace. O R20 confirmou as três no host.

## Achados fora de escopo

- O snapshot intermediário que perde a ordem do slash continua no item aberto de `TODO.md`.
  R15 não ampliou a migração para esse formato.
- kit: A primeira execução literal de `TEST_CMD` em R15 reproduziu a herança de
  `GIT_DIR` e `GIT_WORK_TREE` já registrada abaixo. O reflog e a árvore idêntica
  confirmaram a ponta inicial `7811d0d`. Foram revertidas somente as referências
  afetadas no espelho privado da sessão, sem editar a árvore de trabalho. A suíte
  isolada passou antes e depois da correção.

- kit: `bin/sdd-codex:468` exporta `GIT_DIR` e `GIT_WORK_TREE` para o Git privado. Na primeira execução literal de `TEST_CMD`, fixtures Git da loja herdaram essas variáveis, geraram commits de teste no espelho privado e a suíte terminou com 2 falhas e 146 erros. O reflog e a árvore idêntica confirmaram a ponta anterior `7bd6eeb`, restaurada no espelho sem editar a árvore de trabalho. A repetição com as duas variáveis removidas passou antes e depois da correção. Isolar as variáveis no ambiente de testes que criam repositórios evita redirecionar `git -C`. Nenhuma mudança foi feita no kit.

- Os dois achados de documentação da rodada r1 permanecem nos itens já abertos em `TODO.md`. A frase apontada pela revisão de R4 foi precisada no registro histórico de R3 acima.

- O reuso de ID depois que a mensagem original sai da janela permanece no item já aberto em `TODO.md`.

- kit: em R2, a execução literal voltou a herdar o Git privado. O reflog e a comparação da árvore confirmaram o início em `0aa7b40`. A ponta e a referência temporária criada pelas fixtures foram restauradas no espelho. A suíte passou com as duas variáveis removidas, antes e depois da correção.

- O caso de metadado externo obsoleto registrado em R3 foi resolvido em `fcbd6cb`. O histórico
  permanece no mesmo item de `TODO.md` até o merge.
- kit: a primeira execução literal da suíte em R13 repetiu o problema de roteamento Git já
  registrado acima. O reflog e a comparação de árvores confirmaram a ponta inicial `824db1f`.
  A ponta e a referência temporária foram restauradas no espelho privado. A suíte isolada voltou
  a verde antes da edição. O kit não foi alterado.

- kit: a execução literal em R3 voltou a contaminar o espelho Git privado com fixtures. O teste foi encerrado, o reflog e a árvore confirmaram a ponta inicial `f382fa2` e a referência temporária foi removida. As repetições isoladas de `TEST_CMD` passaram antes da correção e no commit final. A correção do ambiente do runner permanece fora da missão.

- A rastreabilidade das medições históricas permanece no item aberto de `TODO.md` apontado pela revisão r5.

- A receita histórica do plano que herda o Git privado continua no item aberto de `TODO.md`
  apontado por `40-review-r7.md`. Execute a receita isolada deste handoff.

- As duas âncoras do CHANGELOG apontadas em R8 foram reposicionadas em `9f9a08c`.
  A recorrência histórica permanece no item já aberto, sem duplicata.

### Retorno da revisão externa do Codex — R20

O [P2](https://github.com/j0ruge/skills/pull/13#discussion_r4725187745) foi reproduzido no SHA publicado. O commit `41f2952` exige um ID válido antes de consultar os aposentados. O teste novo falhou nos três controles antes da correção e passou com fonte ausente, vazia ou inválida. A prova com fonte aposentada válida, a jornada de Stop e o R19 continuaram verdes. O achado preexistente da r29 foi assim tratado no próprio PR.
