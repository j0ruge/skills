---
missao: 20261125-retrofit-watch-atribuicao
fase: EXEC
status: done
sessao: 01a220a1-44a3-7a93-940a-1f737c7d8d97
data: 2026-11-28 02:35
gate: "Em 0bd4efa, `env -u GIT_DIR -u GIT_WORK_TREE PYTHONDONTWRITEBYTECODE=1 bash -c 'source .sdd/config.sh && eval \"$TEST_CMD\"'` retornou rc 0. Loja com 154 testes (3 pulados), hook com 144, adaptadores, catálogo e versão 0.4.1 válidos. As 28 células de Check de checkpoint.md executadas com Bash tiveram rc 0 e stdout esperado, incluindo R23, R24, R25, R26 e F1. Os quatro testes de test_auto_docs.ReleaseTest passaram."
---

# Handoff — EXEC — Atribuição da retrofit-watch por mensagem

> Escrito no fim de cada fase. A próxima fase é uma **sessão nova sem memória**: se algo que ela
> precisa saber não está aqui (ou nos artefatos linkados), está perdido.

## TL;DR

R26 preserva a ordem já comprovada na retomada da 0.4.0 quando texto sem carga preenche o registro.
Nos dois cortes, o metadado externo comprovadamente antigo fica sem efeito e a retro continua atribuída a `codereview`.
Quando a externa é posterior, o Stop fica em silêncio.
Passaram a suíte isolada, os 28 Checks, F1 e quatro testes de release.
A QA começa por R26 e repete R25, R24 e R23. As três provas nativas passaram no host Linux em `5c54699`.

## Estado do repo

- **Branch** `fix/retrofit-watch-atribuicao-mesma-mensagem`, ligada ao PR #13.
- O incremento mais recente é R26 em `0bd4efa`. A versão continua 0.4.1.
- A suíte isolada de R26 passou com 154 testes da loja (3 pulados) e 144 do hook.
  As 28 células de Check tiveram rc 0 e stdout esperado. Os quatro testes de release passaram.
- A suíte isolada de R25 passou com 154 testes da loja (3 pulados) e 143 do hook.
  As 27 células de Check tiveram rc 0 e stdout esperado. Os quatro testes de release passaram.
- A suíte isolada de R24 passou com 154 testes da loja (3 pulados) e 142 do hook.
  Os 26 Checks tiveram rc 0 e stdout esperado. Os quatro testes de release passaram.
- A suíte isolada de R23 validou 154 testes da loja (3 pulados), 141 do hook, adaptadores,
  catálogo e versões. Os 25 Checks tiveram rc 0 e stdout esperado.
- A suíte isolada de R22 validou 154 testes da loja (3 pulados), 140 do hook, adaptadores,
  catálogo e versões. Os 24 Checks tiveram rc 0 e stdout esperado.
- O `TEST_CMD` isolado em R21 retornou rc 0 com 154 testes da loja (3 pulados) e 138 do hook. Os 23 Checks compararam o stdout completo. F1 confirmou `linked=silêncio missing=silêncio empty=silêncio`.
- R20 em `41f2952` mediu 134 testes do hook. R19 em `bdf75fa` mediu 133.
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

### R21 — Retorno da revisão externa do PR #13

- `e5c249d` — corrige os quatro casos de Stop em [plano-r21.md](plano-r21.md).
  Histórico de slash malformado usa a mesma regra do campo ausente. Metadado externo
  sem vínculo encerra a atribuição, mas preserva o slash no delta. O replay mantém o
  controle legado de slash já consumido. Campos `text` não string não interrompem a
  leitura do delta ou do prefixo. A 0.4.0 pode ter avançado o offset sem varrer o
  delta. Com dois donos compatíveis, o replay mantém a atribuição e os contadores
  persistidos sem importar correlação. Um dono único continua recuperável.
- `e5c249d` — isola o Git nas receitas de r14, r15 e r19 e usa o caminho do scanner
  relativo ao diretório pessoal em r24–r27. Em uma fixture Git sem os SHAs
  históricos, a receita antiga falhou e a corrigida passou. r14 e r15 repetiram
  382 e 175 linhas em Bash e Zsh. r19 manteve os controles negativos com e sem
  `errexit`. r24–r27 repetiram os pré-scans de 530, 452, 327 e 428 linhas.
- As quatro regressões ficaram vermelhas antes da correção. Vinte e uma mutações
  do código final morreram depois de um controle verde com grupo próprio,
  timeout de 20 s e memória virtual de 512 MiB. Os resultados individuais estão
  nas notas de execução.

### R22 — Retorno da revisão r34

- `1863fc2` — na migração da 0.4.0, conserva apenas os IDs que o replay comprova
  anteriores a todos os donos compatíveis. Não importa origem ou janela ambíguas.
  Reuso, evidência anterior perdida e dono sem origem não autorizam suprimir metadados.
- `1863fc2` — aceita o metadado vinculado de um caminho exclusivo registrado no cache
  legado. Outra carga compatível ou metadado posterior que a 0.4.0 poderia aceitar
  revoga essa prova. Não muda os contadores, o offset nem os limites da leitura.
- `1863fc2` — as receitas de r24–r27 isolam o Git, propagam erro do diff e exigem
  530, 452, 327 e 428 linhas, respectivamente. Com Git de fixture, as contagens
  passaram. Com revisão inválida deram rc 128 e com contagem divergente, rc 1.
- Antes da mudança, as duas regressões deram quatro falhas. Um controle adicional
  ficou vermelho antes da revogação por metadado posterior. As 31 degradações
  do código final foram testadas em cópia temporária após controle verde, com
  grupo próprio, timeout de 25 s e memória virtual de 512 MiB. Consulte as notas
  de execução para o resultado de cada degradação.

### R23 — Retorno da revisão r35

- `f82e1d5` — um metadado compatível rejeitado no replay revoga a prova de
  antiguidade e mantém vazia a interseção que se basearia só nas outras cargas.
  Sem prova, a externa posterior encerra o crédito futuro sem apagar o anterior.
- `f82e1d5` — a receita histórica de r34 lê o relatório de `846925a`.
  A receita retornou rc 0 no hook corrigido, rc 1 no hook revisado, rc 128 com blob
  ausente e rc 1 com extração vazia.
- A regressão durável falhou em quatro posições antes da correção. A sonda de
  r35 reproduziu quatro pedidos indevidos com estado gravado pela 0.4.0 real.
  No código corrigido, os quatro casos silenciam e os dois controles de R23
  ainda emitem o pedido. As 12 degradações do código deixaram testes vermelhos
  em cópia temporária com grupo próprio, 25 s e memória virtual de 512 MiB.

### Retorno da revisão — rodada r36

- `51a8a73` — trata o metadado rejeitado compatível com a 0.4.0 como candidato na interseção.
  Recupera sua posição por ID único e pela ordem das mensagens na mesma leitura do prefixo.
  Sem posição comprovada dentro dos limites, não importa a aposentadoria desses IDs.
- `51a8a73` — adiciona a regressão durável, incluindo ID reutilizado ou inválido, mesma mensagem,
  mensagens intercaladas e os três tetos do registro temporário. No Red, a sonda real mostrou
  silêncio nas quatro variantes anteriores. Em Green, todas pediram retro e os quatro
  controles posteriores ficaram em silêncio. Foram detectadas 31 degradações em cópias
  temporárias com grupo próprio, timeout de 25 s e 512 MiB de memória virtual.

### R25 — Retorno da revisão r37

- `149086f` — registra a primeira ocorrência de um `message.id` válido do assistente antes
  de filtrar blocos. Só uma chamada Skill com ID válido ganha vínculo com a posição.
  O replay mantém os limites de mensagens, chamadas e bytes, sem alterar o estado persistido.
- `149086f` — acrescenta a regressão durável nos dois cortes. Ela verifica primeira linha de
  texto ou vazia, registros sem origem válida, ID atrelado a outra ferramenta e os casos em
  que mensagens sem carga esgotam o registro. A [sonda de r37](40-review-r37.md#sonda-de-r25)
  reproduziu quatro vereditos invertidos no Red com a 0.4.0 real. No Green, os quatro foram
  corrigidos e os controles sem texto inicial passaram. R23, R24 e F1 permaneceram verdes.
- Foram detectadas 25 degradações em cópias temporárias com grupo próprio, timeout de 25 s
  e teto de memória virtual de 512 MiB. Quatro reposições equivalentes não mudaram o resultado.
  A célula R25 usa a grafia `codereview` nos resultados positivos, conforme a sonda.

### R26 — Retorno da revisão r38

- `0bd4efa` — mantém as 64 posições já comprovadas no replay, sem atribuir ordem a mensagens
  novas depois do teto. O reuso de ID ainda invalida sua prova de ordem. Os tetos de
  chamadas e bytes e o estado persistido não mudam.
- `0bd4efa` — acrescenta uma regressão em dois cortes para a última posição, origem
  desconhecida, externa posterior e reuso de ID. Na [sonda com a 0.4.0 real](40-review-r38.md#sonda-de-r26),
  o Red silenciou os dois cortes acima do teto. No Green, ambos pediram retro e a externa
  posterior ficou em silêncio. A cópia histórica da expectativa de R25 foi alinhada ao stdout.
- Sete degradações foram detectadas em cópias temporárias com grupo próprio, timeout
  de 25 s e 512 MiB de memória virtual. Uma reposição isolada foi equivalente, pois o
  índice de mensagens já não passa do teto.

## Artefatos

| Arquivo | O que contém |
|---|---|
| `checkpoint.md` | Tabela canônica dos incrementos, com as sondas executáveis e os hashes das correções. |
| `40-review-r38.md` | Sonda de R26 com a 0.4.0 real. |
| `40-review-r37.md` | Sonda de R25 com a 0.4.0 real. |
| `checkpoint-notas.md` | Evidência de execução, isolamento do Git e resultados individuais das mutações. |
| `plugins/retrofit-watch/skills/retrofit-watch/tests/test_retrofit_watch.py` | Regressões de Stop com persistência em disco. |
| `e2e/test_retrofit_watch_stop.py` | Jornada de BUG-01 em dois Stops com transcript e estado em disco. |
| `TODO.md` | Registra as correções da issue #12, da ordem legada e do inventário de EXEC até o merge. |

## Boot da próxima fase

Leia `checkpoint.md` e rode as 28 células de Check da raiz, comparando o stdout completo de cada célula com o esperado. Para cada comando da tabela, use `env -u GIT_DIR -u GIT_WORK_TREE PYTHONDONTWRITEBYTECODE=1 bash -c "$check"`. Use Python 3, Git e um diretório temporário gravável. As jornadas criam transcript e estado próprios, sem iniciar o Claude Code.

- Comece pela célula de R26 e pela [sonda de r38](40-review-r38.md#sonda-de-r26).
  Confira os dois cortes usando o estado gravado pela 0.4.0. Uma externa comprovadamente
  anterior deve pedir retro mesmo com texto acima do teto. Com externa posterior ou ordem
  não comprovada, o Stop deve ficar em silêncio. A célula inclui a regressão durável e F1.

- Em seguida, rode a célula de R25 com a [sonda de r37](40-review-r37.md#sonda-de-r25).
  Compare os dois cortes. Se o primeiro registro for texto da mensagem do dono, a externa
  posterior encerra a atribuição. Se o texto for da mensagem externa, a retro é preservada.
  Repita os três grupos de controle, a regressão durável e F1, todos cobertos pela célula.

- Em seguida, rode a célula de R24 com a [sonda de r36](40-review-r36.md#sonda-de-r24).
  A 0.4.0 real grava o estado no fixture. O Stop deve pedir retro quando a externa for
  comprovadamente anterior a todos os candidatos, e ficar em silêncio na ordem inversa.
  Confira caminho repetido ou distinto e metadado no Stop de migração ou no seguinte.

- Em seguida, rode a célula de R23. A [sonda de r35](40-review-r35.md#sonda-de-r23)
  grava o estado com a 0.4.0 real. Exija silêncio e crédito preservado com caminho
  novo ou repetido, tanto no Stop que migra como no Stop seguinte. A externa
  comprovadamente anterior continua sem fechar a atribuição no controle.

- Em seguida, rode a célula de R22. A sonda de [r34](40-review-r34.md#sonda-de-r22) usa o blob
  da 0.4.0 para gravar o estado em disco. Exija `codereview` para os IDs comprovadamente
  antigos e para o caminho confirmado, e silêncio para a externa intercalada. Repita
  F1 e os controles de R21. Confira as quatro receitas com Git de fixture e os dois
  controles negativos antes de reutilizar resultados de pré-scan.

- Depois, rode a célula de R21. A sonda usa a 0.4.0 do Git e deve retornar
  `slash_list=graphify slash_unlinked=graphify null_replay=codereview skipped_owner=codereview`.
  Confirme também o silêncio no controle de erro próprio com dono único. Repita
  R14 para slash posterior comprovado, R20 para externo sem fonte válida e F1 para
  metadado atrasado. Execute a suíte da raiz com:

  ~~~bash
  env -u GIT_DIR -u GIT_WORK_TREE PYTHONDONTWRITEBYTECODE=1 bash -c 'source .sdd/config.sh && eval "$TEST_CMD"'
  ~~~

- Repita R20, R19 e F1. R20 exercita fonte ausente, vazia e inválida. A célula R19 extrai a sonda de `40-review-r28.md` com
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
Para repetir os quatro testes de release, rode `env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -m unittest -q test_auto_docs.ReleaseTest`.

## Pendências / Decisions for a Human

- Sob a delegação full da loja, o merge do PR #13 exige termos vigentes, orçamento
  disponível, permissão do ato e `pr-ready` no mesmo SHA que o worker vai integrar.
  O registro da ampliação está na [missão](00-missao.md#campanha-e-delegação).

## Riscos e não-feitos

- R22 a R26 não repetiram as três provas nativas de distribuição. O comando configurado as pula
  neste sandbox. As provas de R20 no host são históricas. Não houve smoke manual do Claude Code.
- Blocos de texto de mensagens distintas ocupam o registro de posições do replay. Ao preencher
  o teto de mensagens, só as posições já registradas podem servir de prova. Se exceder
  o teto de chamadas ou de bytes do registro, a prova de ordem é descartada.
- A evidência de cache é conservadora. Caminho repetido, cache divergente ou outra carga
  compatível posterior não permitem escolher o dono. O hook segue a regra de encerramento
  quando falta prova diante de uma externa.

- As três provas nativas de R21 retornaram rc 1 antes de executar o CLI, pois o
  Bubblewrap não pôde criar um namespace no sandbox. Para repetir no host Linux
  fora do sandbox, na raiz do checkout com R21, execute
  `env -u GIT_DIR -u GIT_WORK_TREE -u SKILLS_SKIP_NATIVE_DISTRIBUTION python3 -B -m unittest discover -s tests -p test_codex_distribution.py -v`.
  O resultado verde de R20 é histórico e não substitui essa execução.
- R21 não publica a 0.4.1, não atua nas conversas do PR e não tenta integrar a branch.

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

- kit: em R25, `bin/sdd-codex:468` voltou a expor `GIT_DIR` e `GIT_WORK_TREE` às fixtures da loja
  na primeira execução literal de TEST_CMD. A suíte foi interrompida. O reflog e o checkout
  confirmaram a ponta inicial `9599cad` e a árvore e o índice intactos. Só a ponta, a
  referência das fixtures e a identidade Git contaminada foram restauradas no espelho
  privado. A suíte isolada passou antes e depois da correção. Nenhuma alteração foi feita no kit.

- kit: em R21, `bin/sdd-codex:468` voltou a deixar o Git privado chegar às
  fixtures de TEST_CMD. O reflog e a árvore idêntica confirmaram a ponta inicial
  `b2f6de8`. Somente a ponta, a referência e a configuração contaminadas do
  espelho privado foram restauradas. A suíte isolada passou antes e depois.
  Nenhuma alteração foi feita no kit.

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
