# Notas de execução — Atribuição da retrofit-watch por mensagem

> **Append-only.** Uma linha por evento.

## Notas de execução

- 2026-11-25 22:14 · `I1` · TDD confirmado no Stop. Sonda de `0 0 0 0 0 1` para `1 0 1 0 0 1`. A suíte rodou sem GIT_DIR/GIT_WORK_TREE herdados do Git privado do runner, conforme o handoff.
- 2026-11-25 22:21 · `F1` · BUG-01 confirmado em dois Stops. Com sourceToolUseID ausente ou vazio, o metadado atrasado reabriu a atribuição. Teste vermelho e correção em pending no checkpoint.
- 2026-11-25 22:25 ·  · BUG-01 corrigido em . Dois Stops ficaram em silêncio com ID válido, ausente ou vazio. A sonda de I1 manteve  e a suíte passou com 71 testes da retrofit-watch.
- 2026-11-25 22:25 · `F1` · BUG-01 corrigido em `c704301`. Dois Stops ficaram em silêncio com ID válido, ausente ou vazio. A sonda de I1 manteve `1 0 1 0 0 1` e a suíte passou com 71 testes da retrofit-watch.
- 2026-11-25 22:29 · `F1` · QA repetiu BUG-01 em `13e2b7a`: dois Stops silenciosos nas três variantes. O sensor falhou com ID ausente e vazio em `bf0dae7`. Sonda `1 0 1 0 0 1`, controles de slash e legado e suíte configurada passaram. Handoff reescrito para REVIEW.
- 2026-11-25 22:38 · `R1` · r1 com quatro achados de atribuição reproduzidos, reunidos em R1. F1, sonda de I1 e TEST_CMD passaram. Dois achados de prosa foram ao backlog, sem alteração no código.
- 2026-11-25 22:52 · `R1` · R1 sabotage: parâmetro de preservação ignorado → test_pending_slash_survives_older_external_metadata
- 2026-11-25 22:52 · `R1` · R1 sabotage: aposentadoria repetida na mesma mensagem → test_reused_consumed_call_id_stops_attribution
- 2026-11-25 22:52 · `R1` · R1 sabotage: mensagem reconhecida não persistida → test_reused_consumed_call_id_stops_attribution
- 2026-11-25 22:52 · `R1` · R1 sabotage: mapa anterior mantido → test_late_monitored_metadata_does_not_reopen_attribution
- 2026-11-25 22:52 · `R1` · R1 sabotage: filtro de aposentadoria não aplicado → test_late_monitored_metadata_does_not_reopen_attribution
- 2026-11-25 22:52 · `R1` · R1 sabotage: slash preservado inclusive no encerramento explícito → test_pending_slash_survives_older_external_metadata
- 2026-11-25 22:52 · `R1` · R1 sabotage: limpeza de slash restaurada incondicionalmente → test_pending_slash_survives_older_external_metadata
- 2026-11-25 22:52 · `R1` · R1 sabotage: sentinela sobrescreve mensagem reconhecida → test_reused_consumed_call_id_stops_attribution
- 2026-11-25 22:52 · `R1` · R1 sabotage: remoção da sentinela de chamada vista → test_failed_unknown_skill_keeps_pending_monitored_call
- 2026-11-25 22:52 · `R1` · R1 sabotage: limpeza por tentativa posterior recolocada → test_failed_unknown_skill_keeps_pending_monitored_call, test_same_message_with_two_skill_blocks_before_metadata
- 2026-11-25 22:52 · `R1` · R1 sabotage: mensagem marcada na tentativa recolocada → test_late_monitored_metadata_does_not_reopen_attribution
- 2026-11-25 22:52 · `R1` · R1 sabotage: perde distinção de ID ausente → test_pending_slash_survives_older_external_metadata, test_typed_slash_can_start_new_attribution_after_external_skill
- 2026-11-25 22:52 · `R1` · R1 sabotage: ID desconhecido aceito após tentativa → test_failed_unknown_skill_keeps_pending_monitored_call
- 2026-11-25 22:52 · `R1` · R1 sabotage: fallback anterior para ID legado recolocado → test_legacy_closed_attribution_ignores_unknown_source
- 2026-11-25 22:52 · `R1` · R1 sabotage: pop anterior de ID consumido recolocado → test_reused_consumed_call_id_stops_attribution
- 2026-11-25 22:52 · `R1` · R1 sabotage: chamada anterior sem preservar slash recolocada → test_pending_slash_survives_older_external_metadata
- 2026-11-25 22:52 · `R1` · R1 sabotage: inserção de marca para origem desconhecida → test_legacy_closed_attribution_ignores_unknown_source
- 2026-11-25 22:52 · `R1` · R1 sabotage: marca de consumo removida → test_reused_consumed_call_id_stops_attribution
- 2026-11-25 22:52 · `R1` · Quatro regressões passaram de vermelho a verde em `eb44360`. As 18 degradações foram detectadas com grupo próprio, 20 s e 512 MiB. I1 manteve `1 0 1 0 0 1`, F1 ficou em silêncio nas três variantes e a suíte passou com 75 testes do hook.
2026-11-25 22:59 · `R2` · r2 confirmou descarte de vínculo posterior e crescimento do estado por tentativas falhas. Sonda em leitura contínua e retomada registrada no checkpoint.
