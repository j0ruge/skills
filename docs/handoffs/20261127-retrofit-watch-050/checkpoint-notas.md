# Notas de execução — Skills locais da lista

> **Append-only.** Uma linha por evento; nunca reescreva o arquivo, nunca o releia inteiro.
>
> Este arquivo nasceu em `20260904-a-dieta-de-contexto`, separado do `checkpoint.md` por medição:
> as notas eram **69% daquele arquivo** (67 166 B de 97 865 B em `20260901-o-revisor-so-acha`), e
> aquele arquivo era **44,7% de tudo que a missão releu** — 160 leituras, 1 114 571 B. Enquanto
> tabela e notas dividiam o arquivo havia um piso mecânico: em sessão headless o `Edit` exige um
> `Read` prévio, então toda sessão que atualizasse a tabela pagava o arquivo inteiro. Separadas,
> escrever nota é `>>` e custa **zero leitura**.
>
> O prompt de boot **inlina as últimas 10 notas** (`BOOT_NOTES_TAIL` no `bin/sdd`) e manda
> explicitamente **não abrir este arquivo**. Se você precisa de uma nota mais antiga, ela é
> história — e história se lê no `git log`, não no boot de toda sessão.

## Notas de execução

> Uma linha por evento relevante: bloqueio, decisão tomada, desvio do plano com justificativa.
> É o que a próxima sessão lê para não repetir um erro que já custou caro.


> **Toda vez que um humano precisou entrar na linha** — um `sdd retry`, um conserto à mão, um
> `BLOCKED` assumido — sai uma linha com o marcador `intervention:`. É a **narrativa** do que o
> humano fez. O **número** de intervenções o `sdd autonomy --by-mission` lê do ledger, em
> `launch(es)` (`run_id` distintos — cada `sdd run`/`sdd retry`), e imprime estas notas ao lado
> como `intervention note(s)`. Medido em 2026-08-28: a missão de três lançamentos tinha zero
> notas — o contador não pode depender de alguém lembrar de escrever; a narrativa, sim, e é a
> única fonte que diz o que o humano *fez*.
>
> ⚠️ O marcador é **inglês e minúsculo**, como `pending`/`done`/`blocked`: é contrato, não prosa.
> O texto depois dos dois-pontos vai no idioma do `OUTPUT_LANG`, como o resto deste arquivo.
> Só conta quando abre a linha — `intervention` no meio de uma frase é prosa e não é contado.
>
> Desde 2026-09-03 o **runner escreve a linha sozinho** quando é ele quem recebe a mão do humano —
> `sdd run --phase X`, `sdd retry`, `--budget-override` — **e só na volta que abre sessão** (uma
> volta parada antes dela, por PLAN, carimbo, teto ou no-work, não grava nota), e a commita sozinha,
> na hora, para a árvore chegar limpa ao gate da fase seguinte. A linha escrita à mão continua valendo para o que
> o runner não vê: conserto manual, `BLOCKED` assumido. Fase feita à mão tem comando:
> `sdd note-manual <missão> <FASE>` escreve a nota e a linha `manual` do ledger, que não gradua
> nada — escrita só aqui, a fase não existe para o ledger. `sdd approve` não
> escreve nenhuma: aprovar o plano é o gate humano desenhado, não uma entrada na linha. A nota
> diz o que o runner **sabe** ("forçada pela CLI"), nunca quem estava na CLI: outro agente com
> shell entra pela mesma porta, e o runner não distingue — medido em 2026-09-03.
>
> O exemplo abaixo mora **dentro** desta citação de propósito: o `>` quebra o casamento com
> `^[[:space:]]*-`, e sem ele o exemplo era contado verbatim — todo checkpoint recém-instanciado
> nascia devendo uma intervenção fantasma ao instrumento que mede autonomia. Copie a forma para
> fora da citação ao registrar uma intervenção de verdade.
>
> - intervention: <o que o humano teve de fazer> — <fase> — <custo, se houver>


- 2026-11-28 03:32 · `I1` · TDD em `d929f44`: o Red reproduziu `kit-ou-lean` na primeira guarda elegível e a ausência da janela v2. O Check passou com 12 testes em `TMPDIR=/tmp`, sem `GIT_DIR` e `GIT_WORK_TREE`. O controle íntegro sob grupo isolado, 25 s e 512 MiB por processo passou. As 22 mutações em cópias temporárias falharam nas asserções-alvo.
- 2026-11-28 03:32 · `I1` · `TEST_CMD` passou com o mesmo ambiente isolado: 154 testes da loja (3 pulados pela configuração), 144 do Stop, adaptadores, catálogo e versões válidos. Os 60 testes direcionados de I1, formatos e critério público passaram. A suíte da retrofit-skill passou com 9 testes. O TODO ficou com 58 âncoras válidas.
- 2026-11-28 03:32 · `I1` · A suíte completa da watch (499 testes) ficou vermelha. `/var/tmp` é somente leitura e o `/tmp/.git` vazio faz a colheita de fixture recusar `/tmp`. O controle que ignorou o marcador só no processo de teste deixou 7 falhas e 2 erros, todos reproduzidos em `6d72029`. A segunda skill full ausente no estado já falhava na base sem esse controle e foi registrada no TODO.
- 2026-11-28 03:32 · `I1` · kit: o ambiente do EXEC exportou `GIT_DIR` e `GIT_WORK_TREE` da cópia privada. O primeiro `TEST_CMD` redirecionou operações das fixtures para essa cópia. Removi apenas a ref `base` e a sequência que a rodada criou, conferindo o reflog e a igualdade da árvore com `6d72029`. Repetir as suítes com as variáveis de localização desarmadas. O Check aprovado com `/var/tmp` permanece intacto para o runner externo.
- 2026-11-28 03:45 ·  · TDD em . O Red expôs comandos ausentes e a rejeição de  nas lições. O Check exato passou com 16 testes, incluindo trava só no clone principal, pre-push herdado, recusa de colisão e selo. O controle íntegro passou sob grupo isolado, 25 s e 512 MiB por processo. As 24 mutações em cópia descartável ficaram vermelhas nas sondas direcionadas.
- 2026-11-28 03:45 ·  ·  verde com , sem  e : 154 testes de loja (3 pulados pela configuração), 144 do Stop, adaptadores, catálogo e versões válidos. Também passaram 97 testes direcionados da watch e 9 da retrofit-skill. TODO com 58 âncoras válidas e camada 1 do incremento limpa.
- 2026-11-28 03:45 ·  · A suíte completa da watch sob controle que ignora só  no processo de teste manteve as mesmas 7 falhas em 510 testes da candidata e 499 da base . Subprocessos continuam vendo o marcador e a falha de atribuição full já estava aberta no TODO, com recorrência registrada. O Check externo conserva .
- 2026-11-28 03:46 · `I2` · Registro canônico de I2, que substitui as três linhas anteriores truncadas na formatação. Em `785c388`, o Red reproduziu os comandos ausentes e a rejeição de `repo`. O Check com `TMPDIR=/var/tmp` passou com 16 testes. O controle íntegro em grupo isolado, 25 s e 512 MiB por processo passou e todas as 24 mutações em cópia descartável falharam nas sondas. O `TEST_CMD` passou com `TMPDIR=/tmp`, sem `GIT_DIR` nem `GIT_WORK_TREE`, com 154 testes da loja (3 pulados), 144 do Stop e adaptadores, catálogo e versões válidos. Passaram 97 testes direcionados da watch e 9 da retrofit-skill. A suíte completa sob controle que ignora só `/tmp/.git` no processo principal manteve as mesmas 7 falhas em 510 testes da candidata e 499 da base `aa93d81`. Os subprocessos ainda veem o marcador. A atribuição full já registrada ganhou recorrência no TODO, que ficou com 58 âncoras válidas. A camada 1 do incremento passou.
- 2026-11-28 04:05 · `I3` · Em `ff7025b`, o Red reproduziu a falta da porta privada, do startup e dos contratos de revisão. O Check com `TMPDIR=/var/tmp` passou com 41 testes e a rodada dirigida final com 147. O controle íntegro passou em grupo isolado, com 45 s e 512 MiB por processo. As 42 mutações em cópia descartável ficaram vermelhas nas sondas. A fixture confirmou ensaio com bare intacto, aprovação vinculada ao patch, mesmo SHA no bare, no `local/ci` e no clone, retorno ao ensaio após revert e retro manual com e sem o sim. O `TEST_CMD` passou com `TMPDIR=/tmp`, sem `GIT_DIR` nem `GIT_WORK_TREE`, com 154 testes da loja (3 pulados), 144 do Stop e adaptadores, catálogo e versões válidos. A retrofit-skill passou com 11 testes. A suíte ampla, sob controle que ignora `/tmp/.git` só no processo do teste, teve as mesmas 7 falhas e 2 erros em 549 testes da candidata e 515 da base `5fc94c1`. A atribuição full ganhou recorrência no TODO, com 58 âncoras válidas. A camada 1 do incremento passou.
- 2026-11-28 04:15 · `I4` · Em `04a1a77`, o Red acusou as duas versões anteriores e o Check imprimiu `0.5.0 0.12.0`. Controle íntegro e 17 mutações em cópia isolada sob 10 s e 512 MiB por processo. TEST_CMD rc 0 (154 da loja, 3 pulados, e 144 do Stop), 44 contratos, 11 da retrofit-skill, sincronização e validação Claude com avisos. A ampla mais o Stop isolado mantiveram as mesmas 7 falhas e 2 erros em 555 testes da candidata e 554 da base `d28e095` sob controle de `/tmp/.git`. A distribuição nativa foi bloqueada por Bubblewrap. Camada 1 limpa no incremento e com três sinalizações anteriores na branch. TODO com 60 âncoras, incluindo recorrência da atribuição full.
- 2026-11-28 04:24 · `QA` · Jornada privada no bare em 8ff2681 e Stop da 0.4.1 verdes. Os quatro Checks e o TEST_CMD passaram em aba5090. A suíte ampla repetiu as mesmas 5 falhas e 176 erros de 6d72029 neste ambiente. Bubblewrap bloqueou as três provas nativas e a camada 1 da branch manteve as três sinalizações já registradas no TODO. Sem regressão nova nem incremento de fix.
- 2026-11-28 04:34 ·  · REVIEW r1, achado 1. Emenda em caminho excluído do digest privado reutilizou a revisão e o approve e chegou ao bare de fixture.
- 2026-11-28 04:34 ·  · REVIEW r1, achado 2. Classificação e porta aceitaram origens de servidores diferentes com o mesmo slug, inclusive com reescrita efetiva.
- 2026-11-28 04:34 ·  · REVIEW r1, achados 3–6. Reprodução de troca de ramo durante fetch, setup residual, colisão de registros e JSON inválido silencioso.
- 2026-11-28 04:34 · Registro canônico de REVIEW r1, em complemento às três linhas anteriores sem ID. `R1` veio do achado 1 (emenda fora do digest), `R2` do achado 2 (origens homônimas) e `R3` dos achados 3–6 (ramo, setup e avisos).
- 2026-11-28 04:41 · `R1` · R1 sabotage: Modo privado por padrão → test_patch_id_survives_a_rebase_and_changes_with_content
- 2026-11-28 04:41 · `R1` · R1 sabotage: Exclusões da loja também no privado → test_private_patch_includes_store_list_paths
- 2026-11-28 04:41 · `R1` · R1 sabotage: Exclusões removidas também do full → test_patch_id_survives_a_rebase_and_changes_with_content
- 2026-11-28 04:41 · `R1` · R1 sabotage: Selo sem modo privado → test_private_patch_includes_store_list_paths
- 2026-11-28 04:41 · `R1` · R1 sabotage: Selo full no modo privado → test_patch_id_survives_a_rebase_and_changes_with_content
- 2026-11-28 04:41 · `R1` · R1 sabotage: Aprovação privada com digest full → test_private_patch_includes_store_list_paths
- 2026-11-28 04:41 · `R1` · R1 sabotage: Comparação da base invertida na conferência final → test_private_patch_includes_store_list_paths
- 2026-11-28 04:41 · `R1` · R1 sabotage: Conferência final com digest full → test_private_patch_includes_store_list_paths
- 2026-11-28 04:41 · `R1` · R1 sabotage: Linha anterior da conferência final recolocada → test_private_patch_includes_store_list_paths
- 2026-11-28 04:41 · `R1` · Em `fe68792`, o Red na base `8a70707` não detectava a emenda em caminho de lista. O Check passou e conservou o bare. A sonda repetiu ensaio, nova aprovação, publicação, avanço e revert. Passaram 45 testes direcionados, o contrato documental e o TEST_CMD (154 da loja, 3 pulados, 144 do Stop, adaptadores, catálogo e versões). Controle íntegro e 9 mutações de código em cópia descartável, sob grupo próprio, 25 s e 512 MiB por processo. A montagem da fixture e suas asserções são os próprios sensores, sem sensor funcional separado para cada linha. A prosa foi conferida no contexto e nas referências ao patch. A camada 1 do incremento passou e o TODO tem 61 âncoras válidas.
