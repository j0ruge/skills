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
- 2026-11-28 04:53 · `R2` · R2 sabotage: Importação do digest removida → test_mixed_request_and_legacy_full
- 2026-11-28 04:53 · `R2` · R2 sabotage: Entrada lean volta a guardar só o slug → test_mixed_request_and_legacy_full
- 2026-11-28 04:53 · `R2` · R2 sabotage: Slug por sessão volta a carregar a identidade inteira → test_mixed_request_and_legacy_full
- 2026-11-28 04:53 · `R2` · R2 sabotage: Autoridade aceita escapes na URL → test_only_supported_origin_shapes
- 2026-11-28 04:53 · `R2` · R2 sabotage: URL HTTPS e SSH deixa de ser reconhecida → test_same_slug_on_another_host_stays_manual
- 2026-11-28 04:53 · `R2` · R2 sabotage: Forma SCP deixa de ser reconhecida → test_same_slug_on_another_host_stays_manual
- 2026-11-28 04:53 · `R2` · R2 sabotage: Inicialização do bare removida → test_only_supported_origin_shapes
- 2026-11-28 04:53 · `R2` · R2 sabotage: Autoridade HTTPS e SSH descartada → test_same_slug_on_another_host_stays_manual
- 2026-11-28 04:53 · `R2` · R2 sabotage: Porta explícita desconsiderada → test_only_supported_origin_shapes
- 2026-11-28 04:53 · `R2` · R2 sabotage: Porta interpretada como padrão → test_only_supported_origin_shapes
- 2026-11-28 04:53 · `R2` · R2 sabotage: Portas fora do intervalo aceitas → test_only_supported_origin_shapes
- 2026-11-28 04:53 · `R2` · R2 sabotage: Porta padrão tratada como alternativa → test_same_slug_on_another_host_stays_manual
- 2026-11-28 04:53 · `R2` · R2 sabotage: Porta não padrão removida da identidade → test_same_slug_on_another_host_stays_manual
- 2026-11-28 04:53 · `R2` · R2 sabotage: Ramo SCP desabilitado → test_same_slug_on_another_host_stays_manual
- 2026-11-28 04:53 · `R2` · R2 sabotage: Autoridade SCP descartada → test_same_slug_on_another_host_stays_manual
- 2026-11-28 04:53 · `R2` · R2 sabotage: Bare volta a ser identificado pelo slug → test_same_slug_on_another_host_stays_manual
- 2026-11-28 04:53 · `R2` · R2 sabotage: Servidor diferencia maiúsculas → test_same_slug_on_another_host_stays_manual
- 2026-11-28 04:53 · `R2` · R2 sabotage: Validação do slug omitida no retorno → test_only_supported_origin_shapes
- 2026-11-28 04:53 · `R2` · R2 sabotage: Projeção de slug retorna a identidade inteira → test_only_supported_origin_shapes
- 2026-11-28 04:53 · `R2` · R2 sabotage: Digest não varia com a origem → test_prepare_rejects_same_slug_changed_after_request
- 2026-11-28 04:53 · `R2` · R2 sabotage: Origem do checkout volta a ser reduzida na leitura → test_mixed_request_and_legacy_full
- 2026-11-28 04:53 · `R2` · R2 sabotage: Filtro de dono removido → test_only_owned_tracked_local_skills_can_enter
- 2026-11-28 04:53 · `R2` · R2 sabotage: Origem diferente aceita na elegibilidade → test_same_slug_on_another_host_stays_manual
- 2026-11-28 04:53 · `R2` · R2 sabotage: Entrada sem identidade aceita como legada → test_same_slug_on_another_host_stays_manual
- 2026-11-28 04:53 · `R2` · R2 sabotage: Leitura da identidade volta a ler o slug → test_only_owned_tracked_local_skills_can_enter
- 2026-11-28 04:53 · `R2` · R2 sabotage: Origem gravada também em pedido full → test_mixed_request_and_legacy_full
- 2026-11-28 04:53 · `R2` · R2 sabotage: Origem não gravada no pedido → test_mixed_request_and_legacy_full
- 2026-11-28 04:53 · `R2` · R2 sabotage: Esquema privado não exige o digest no pedido → test_mixed_request_and_legacy_full
- 2026-11-28 04:53 · `R2` · R2 sabotage: Leitor não distingue pedido privado → test_mixed_request_and_legacy_full
- 2026-11-28 04:53 · `R2` · R2 sabotage: Leitor usa esquema pleno para pedido privado → test_mixed_request_and_legacy_full
- 2026-11-28 04:53 · `R2` · R2 sabotage: Esquema do lote volta a recusar origem → test_prepare_uses_only_live_clone_and_latest_remote_base
- 2026-11-28 04:53 · `R2` · R2 sabotage: Preparação ignora o pedido durante seleção da origem → test_prepare_rejects_same_slug_changed_after_request
- 2026-11-28 04:53 · `R2` · R2 sabotage: Seleção do pedido usa outro plugin → test_prepare_uses_only_live_clone_and_latest_remote_base
- 2026-11-28 04:53 · `R2` · R2 sabotage: Origens ambíguas aceitas na preparação → test_prepare_rejects_same_slug_changed_after_request
- 2026-11-28 04:53 · `R2` · R2 sabotage: Digest do pedido não é copiado ao lote → test_prepare_uses_only_live_clone_and_latest_remote_base
- 2026-11-28 04:53 · `R2` · R2 sabotage: Fetch de preparação volta a ignorar o vínculo → test_prepare_rejects_same_slug_changed_after_request
- 2026-11-28 04:53 · `R2` · R2 sabotage: Lote não registra a origem do pedido → test_prepare_uses_only_live_clone_and_latest_remote_base
- 2026-11-28 04:53 · `R2` · R2 sabotage: Identidade configurada reduzida ao slug → test_only_owned_tracked_local_skills_can_enter
- 2026-11-28 04:53 · `R2` · R2 sabotage: Clone de outro dono aceito → test_prepare_rejects_swapped_clone_missing_skill_and_symlink
- 2026-11-28 04:53 · `R2` · R2 sabotage: Clone com slug homônimo aceito → test_same_slug_on_another_host_stays_manual
- 2026-11-28 04:53 · `R2` · R2 sabotage: URL inválida aceita no setup → test_setup_preserves_existing_destination_and_rejects_wrong_slug_or_url
- 2026-11-28 04:53 · `R2` · R2 sabotage: Setup não resolve a URL de clone antes de chamar o Git → test_setup_refuses_same_slug_rewrite_before_clone
- 2026-11-28 04:53 · `R2` · R2 sabotage: Setup aceita a URL reescrita → test_setup_refuses_same_slug_rewrite_before_clone
- 2026-11-28 04:53 · `R2` · R2 sabotage: Setup não recusa reescrita → test_setup_refuses_same_slug_rewrite_before_clone
- 2026-11-28 04:53 · `R2` · R2 sabotage: Reserva vazia retida após recusar URL → test_setup_refuses_same_slug_rewrite_before_clone
- 2026-11-28 04:53 · `R2` · R2 sabotage: Validação pós-clone perde a referência declarada → test_setup_clones_main_with_worktree_lock
- 2026-11-28 04:53 · `R2` · R2 sabotage: Fetch confere apenas o slug efetivo → test_advance_rejects_effective_origin_rewritten_to_another_repo
- 2026-11-28 04:53 · `R2` · R2 sabotage: Remoto de fetch deixa de ser conferido → test_advance_rejects_effective_origin_rewritten_to_another_repo
- 2026-11-28 04:53 · `R2` · R2 sabotage: Fetch ignora a origem declarada no clone → test_fetch_rechecks_the_pinned_origin
- 2026-11-28 04:53 · `R2` · R2 sabotage: Fetch depois do pedido ignora origem trocada → test_prepare_rejects_same_slug_changed_after_request
- 2026-11-28 04:53 · `R2` · R2 sabotage: Fetch não interrompe em origem configurada trocada → test_prepare_rejects_same_slug_changed_after_request
- 2026-11-28 04:53 · `R2` · R2 sabotage: Avanço não repassa o digest → test_origin_change_after_push_cannot_redirect_status_or_advance
- 2026-11-28 04:53 · `R2` · R2 sabotage: Fetch privado volta a projetar apenas o slug → test_push_runs_hook_again_and_keeps_failure
- 2026-11-28 04:53 · `R2` · R2 sabotage: Selo de origem substituído por comparação de slug → test_same_slug_effective_origin_mismatch_holds_before_fetch
- 2026-11-28 04:53 · `R2` · R2 sabotage: Diferença de pushurl não bloqueia → test_origin_mismatch_holds_without_gate
- 2026-11-28 04:53 · `R2` · R2 sabotage: Origem validada não é retornada → test_push_runs_hook_again_and_keeps_failure
- 2026-11-28 04:53 · `R2` · R2 sabotage: Fetch da porta perde o digest do lote → test_fetch_rechecks_the_pinned_origin
- 2026-11-28 04:53 · `R2` · R2 sabotage: URL capturada antes do npm volta a valer para o ensaio → test_npm_precedes_the_effective_hook
- 2026-11-28 04:53 · `R2` · R2 sabotage: npm executa sem validar o destino → test_npm_precedes_the_effective_hook
- 2026-11-28 04:53 · `R2` · R2 sabotage: Destino depois do npm não é verificado → test_npm_precedes_the_effective_hook
- 2026-11-28 04:53 · `R2` · R2 sabotage: Push privado não desestrutura a origem validada → test_push_runs_hook_again_and_keeps_failure
- 2026-11-28 04:53 · `R2` · R2 sabotage: Status volta a receber só o slug → test_status_selects_the_host_even_with_another_gh_default
- 2026-11-28 04:53 · `R2` · R2 sabotage: gh volta a escolher o servidor por padrão → test_status_selects_the_host_even_with_another_gh_default
- 2026-11-28 04:53 · `R2` · R2 sabotage: Status não reconfere o servidor antes de postar → test_origin_change_after_push_cannot_redirect_status_or_advance
- 2026-11-28 04:53 · `R2` · R2 sabotage: Status usa servidor fixo em vez do servidor validado → test_dry_then_approval_and_idempotent_retry
- 2026-11-28 04:53 · `R2` · R2 sabotage: Avanço pós-publicação perde o digest do lote → test_origin_change_after_push_cannot_redirect_status_or_advance
- 2026-11-28 04:53 · `R2` · R2 sabotage: Tipo e formato do digest não são validados → test_private_formats_reject_invalid_slug_and_paths
- 2026-11-28 04:53 · `R2` · R2 sabotage: Guarda de slug volta a aceitar o primeiro fetch entre vários → test_advance_rejects_effective_origin_rewritten_to_another_repo
- 2026-11-28 04:53 · `R2` · Em `bc8a164`, o Red na base `2b30962` aceitou servidores homônimos na classificação e chegou ao fetch na porta com origin reescrito. O Check passou e a sonda repetiu ensaio, aprovação, publicação, status e avanço em dois bares locais; nenhum repo real foi acionado. Passaram 78 testes direcionados com o contrato documental e o TEST_CMD (154 da loja, 3 pulados, 144 do Stop, adaptadores, catálogo e versões). Controle íntegro e 68 mutações em cópias descartáveis, com grupo próprio, 30 s e 512 MiB por processo. Linhas estruturais de declaração, formatação e transposição foram cobertas pelo comportamento do bloco, sem sensor independente por linha. Prosa conferida nas referências e no contrato do clone. Camada 1 limpa e 61 âncoras válidas. R3 permanece pendente.
- 2026-11-28 05:02 · `R3` · R3 sabotage: Setup pula a criação do clone → test_setup_clones_main_with_worktree_lock
- 2026-11-28 05:02 · `R3` · R3 sabotage: Setup oculta a falha depois da limpeza → test_setup_retry_after_clone_failure
- 2026-11-28 05:02 · `R3` · R3 sabotage: Setup não compara a origem efetiva → test_setup_refuses_same_slug_rewrite_before_clone
- 2026-11-28 05:02 · `R3` · R3 sabotage: Detalhe de ramo ilegível se perde → test_advance_reports_unreadable_branch_without_fetch
- 2026-11-28 05:02 · `R3` · R3 sabotage: Árvore suja recebe resultado de ramo errado → test_advance_does_not_merge_when_tree_becomes_dirty_during_fetch
- 2026-11-28 05:02 · `R3` · R3 sabotage: Avanço não reconfere o ramo após o fetch → test_advance_does_not_merge_after_branch_switch_during_fetch
- 2026-11-28 05:02 · `R3` · R3 sabotage: Avanço limpo deixa de entrar no bloco do merge → test_advance_fast_forwards_ignoring_only_ignored_files_and_records_result
- 2026-11-28 05:02 · `R3` · R3 sabotage: Leitor e escritor perdem o dono no caminho → test_advance_records_same_basename_without_losing_notice
- 2026-11-28 05:02 · `R3` · R3 sabotage: Startup não capta JSON inválido → test_present_invalid_advance_record_reports_error
- 2026-11-28 05:02 · `R3` · R3 sabotage: Leitor aceita resultado fora do contrato → test_present_invalid_advance_record_reports_error
- 2026-11-28 05:02 · `R3` · R3 sabotage: Registro com falha deixa de produzir aviso → test_advance_records_same_basename_without_losing_notice
- 2026-11-28 05:02 · `R3` · R3 sabotage: Setup volta a limpar só falhas do Git → test_setup_retry_after_lock_failure
- 2026-11-28 05:02 · `R3` · R3 sabotage: Setup não devolve o caminho que criou → test_setup_retry_after_clone_failure
- 2026-11-28 05:02 · `R3` · R3 sabotage: Setup não recusa a URL efetiva divergente → test_setup_refuses_same_slug_rewrite_before_clone
- 2026-11-28 05:02 · `R3` · R3 sabotage: Ramo errado passa pela guarda → test_advance_does_not_merge_after_branch_switch_during_fetch
- 2026-11-28 05:02 · `R3` · R3 sabotage: Árvore limpa sempre parece obstruída → test_advance_fast_forwards_ignoring_only_ignored_files_and_records_result
- 2026-11-28 05:02 · `R3` · R3 sabotage: Avanço não reconfere a árvore após o fetch → test_advance_does_not_merge_when_tree_becomes_dirty_during_fetch
- 2026-11-28 05:02 · `R3` · R3 sabotage: Escrita volta a usar apenas o nome do clone → test_advance_records_same_basename_without_losing_notice
- 2026-11-28 05:02 · `R3` · R3 sabotage: Startup volta a ler os registros por basename → test_advance_records_same_basename_without_losing_notice
- 2026-11-28 05:02 · `R3` · R3 sabotage: Startup volta a silenciar registro ilegível → test_present_invalid_advance_record_reports_error
- 2026-11-28 05:02 · `R3` · R3 sabotage: Leitor aceita detalhe de tipo incorreto → test_present_invalid_advance_record_reports_error
- 2026-11-28 05:02 · `R3` · R3 sabotage: Aviso válido perde o detalhe específico → test_advance_records_same_basename_without_losing_notice
- 2026-11-28 05:02 · `R3` · R3 sabotage: Setup volta a deixar o destino reservado → test_setup_retry_after_clone_failure
- 2026-11-28 05:02 · `R3` · R3 sabotage: Validação da URL ignora o HOME autorizado → test_setup_refuses_same_slug_rewrite_before_clone
- 2026-11-28 05:02 · `R3` · R3 sabotage: Avanço volta a usar referência abreviada → test_advance_fast_forwards_ignoring_only_ignored_files_and_records_result
- 2026-11-28 05:02 · `R3` · R3 sabotage: Ramo errado recebe resultado de árvore suja → test_advance_does_not_merge_after_branch_switch_during_fetch
- 2026-11-28 05:02 · `R3` · R3 sabotage: Avanço não checa a cópia antes de buscar → test_advance_leaves_wrong_branch_dirty_tree_and_divergence_alone
- 2026-11-28 05:02 · `R3` · R3 sabotage: Merge deixa de respeitar obstrução → test_advance_does_not_merge_after_branch_switch_during_fetch
- 2026-11-28 05:02 · `R3` · R3 sabotage: Escrita não cria a pasta do dono → test_advance_fast_forwards_ignoring_only_ignored_files_and_records_result
- 2026-11-28 05:02 · `R3` · R3 sabotage: Startup trata ausência como registro inválido → test_present_invalid_advance_record_reports_error
- 2026-11-28 05:02 · `R3` · R3 sabotage: Leitor não exige objeto JSON → test_present_invalid_advance_record_reports_error
- 2026-11-28 05:02 · `R3` · R3 sabotage: Registro inválido não produz aviso → test_present_invalid_advance_record_reports_error
- 2026-11-28 05:02 · `R3` · R3 sabotage: Aviso de falha perde alternativa para detalhe vazio → test_present_invalid_advance_record_reports_error
- 2026-11-28 05:02 · `R3` · R3 sabotage: Setup volta a limpar só diretórios vazios → test_setup_retry_after_lock_failure
- 2026-11-28 05:02 · `R3` · R3 sabotage: Validação da URL deixa de consultar o Git → test_setup_refuses_same_slug_rewrite_before_clone
- 2026-11-28 05:02 · `R3` · R3 sabotage: Falha ao ler ramo não vira erro → test_advance_reports_unreadable_branch_without_fetch
- 2026-11-28 05:02 · `R3` · R3 sabotage: Árvore suja passa pela guarda → test_advance_does_not_merge_when_tree_becomes_dirty_during_fetch
- 2026-11-28 05:02 · `R3` · R3 sabotage: Fetch ignora obstrução inicial → test_advance_leaves_wrong_branch_dirty_tree_and_divergence_alone
- 2026-11-28 05:02 · `R3` · R3 sabotage: Registro perde a condição que impediu o merge → test_advance_does_not_merge_after_branch_switch_during_fetch
- 2026-11-28 05:02 · `R3` · R3 sabotage: Avanço não grava o resultado → test_advance_fast_forwards_ignoring_only_ignored_files_and_records_result
- 2026-11-28 05:02 · `R3` · R3 sabotage: Startup não capta arquivo ilegível → test_present_invalid_advance_record_reports_error
- 2026-11-28 05:02 · `R3` · R3 sabotage: Leitor aceita registro que pertence a outro repo → test_present_invalid_advance_record_reports_error
- 2026-11-28 05:02 · `R3` · R3 sabotage: Registro com sucesso produz aviso → test_present_invalid_advance_record_reports_error
- 2026-11-28 05:02 · `R3` · Em `30d619b`, Red em `5c6c947` reproduziu destino abandonado, ramo movido, colisão de avisos e registro inválido silencioso. Check R3 e sonda local verdes. O TEST_CMD passou com 154 testes da loja (3 pulados), 144 do Stop, adaptadores, catálogo e versões. Controle íntegro com 20 testes e 43 mutações detectadas em cópias descartáveis, sob grupo próprio, 30 s e 512 MiB por processo. Declarações, formatação e o retorno sem efeito no fim da função extraída foram cobertos pelo comportamento do bloco, sem sensor independente. Texto conferido no README, no CHANGELOG e nas referências do clone. Camada 1 limpa para R3 e 61 âncoras válidas. Nenhum repo real acionado.
- 2026-11-28 05:02 · `R3` · O primeiro TEST_CMD herdou o diretório Git do runner. A comparação de árvores confirmou que os 139 commits base eram vazios. O ramo foi recomposto sobre `5c6c947` com a mesma árvore de produto, e só a referência base criada pela fixture foi removida. A repetição desarmou as variáveis Git. A camada 1 da branch ainda sinaliza a impressão digital pública e quatro URLs de fixture anteriores a R3, já cobertas pelo item aberto da mesma missão.
- 2026-11-28 05:11 ·  · Achado 1 da r2: caminhos distintos no mesmo servidor colidem na identidade; o Check exige separação e a jornada autorizada verde.
- 2026-11-28 05:11 ·  · Achados 2 e 4 da r2: a porta SSH chegou ao status e duas URLs sintéticas reprovaram a camada 1; o Check inclui status, camada 1 e jornada.
- 2026-11-28 05:11 · `R4` · Rótulo da nota anterior de r2: o achado 1 exige separar a identidade de caminhos diferentes e preservar a jornada autorizada.
- 2026-11-28 05:11 · `R5` · Rótulo da nota anterior de r2: os achados 2 e 4 exigem o host correto do status, camada 1 verde e repetição da jornada.
