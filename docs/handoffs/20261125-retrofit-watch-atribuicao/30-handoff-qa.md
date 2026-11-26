---
missao: 20261125-retrofit-watch-atribuicao
fase: QA
status: done
sessao: 01a2156b-d459-7933-b1ed-77adb979bd95
data: 2026-11-25 22:21
gate: Em `42cfe55`, `PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -c "$(sed -n '/^~~~python$/,/^~~~$/{ /^~~~/!p; }' "${L1_PLAN:-docs/handoffs/20261125-retrofit-watch-atribuicao/01-plano.md}")"` → `1 0 1 0 0 1`. Em `42cfe55`, `env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -m unittest -v test_retrofit_watch.StopTest.test_third_party_skill_in_same_message_keeps_attribution test_retrofit_watch.StopTest.test_third_party_skill_in_later_message_stops_attribution test_retrofit_watch.StopTest.test_third_party_skill_in_same_message_keeps_attribution_after_resume test_retrofit_watch.StopTest.test_third_party_skill_in_later_message_stops_attribution_after_resume test_retrofit_watch.StopTest.test_legacy_state_resumes_at_offset_and_keeps_history test_retrofit_watch.StopTest.test_real_work_fires_once_with_retrofit_command test_retrofit_watch.StopTest.test_path_can_exclude_the_same_call_recognized_by_plugin_name test_retrofit_watch.StopTest.test_late_monitored_metadata_does_not_override_external_slash_skill test_retrofit_watch.StopTest.test_late_monitored_metadata_does_not_reopen_attribution` → 9 testes OK de Stop em subprocessos com estado em disco. Em `42cfe55`, `env -u GIT_DIR -u GIT_WORK_TREE PYTHONDONTWRITEBYTECODE=1 bash -c 'source .sdd/config.sh && eval "$TEST_CMD"'` → loja Ran 154 tests, OK (skipped=3), plugin Ran 68 tests, OK, adaptadores, catálogo e validador OK. Em `d3484a5`, `env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B e2e/test_retrofit_watch_stop.py` → rc 1, `linked=silêncio`, `missing=saída`, `empty=saída`. Nos dois casos sem vínculo o segundo Stop emitiu `/retrofit-skill:retrofit-skill codereview` indevidamente. F1 está pending.
---

# Handoff — QA — Atribuição da retrofit-watch por mensagem

> Escrito no fim de cada fase. A próxima fase é uma **sessão nova sem memória**: se algo que ela
> precisa saber não está aqui (ou nos artefatos linkados), está perdido.

## TL;DR

A QA percorreu nove jornadas de Stop. A sonda de I1 retornou `1 0 1 0 0 1` e a suíte configurada passou.
Um achado virou um teste ponta a ponta de terminal e o incremento `F1`, ainda `pending`. Nenhuma decisão precisou ser escalada ao humano.
No segundo Stop, um metadado atrasado sem `sourceToolUseID` ou com o campo vazio reabre indevidamente a atribuição encerrada por carga externa posterior.
A execução deve fechar `F1`. A QA então repete o caso e reescreve este handoff antes da revisão.

## Estado do repo

- **Branch:** `fix/retrofit-watch-atribuicao-mesma-mensagem`, sem upstream configurado.
- **Último commit antes deste handoff:** `d3484a5` `test(retrofit-watch): registrar a reabertura indevida pelo metadado atrasado`.
- **Working tree:** limpa após o commit do teste e do checkpoint.
- **Suíte:** `TEST_CMD` verde em `42cfe55`. A loja reportou 154 testes, com 3 pulados, e a retrofit-watch reportou 68 testes aprovados. O catálogo e o validador confirmaram a 0.4.1.
- **E2E:** sem `E2E_CMD` e sem `APP_URL`. A jornada no terminal em `e2e/test_retrofit_watch_stop.py` confirmou `BUG-01` em `d3484a5`.

## O que foi feito

- `42cfe55` — Em leitura contínua e retomada, a mesma mensagem manteve `codereview` e a mensagem posterior encerrou a atribuição. Nos casos com corte, o primeiro Stop foi silencioso e gravou o offset no fim do trecho, com o vínculo externo pendente. O segundo consumiu o vínculo e só pediu retro no caso da mesma mensagem.
- `42cfe55` — Ao retomar o estado 0.4.0 sem vínculo, o Stop ficou em silêncio, avançou o offset de 996 a 1565 bytes no fixture e preservou `work=3`, `friction=1`, `reviews=1` e o histórico. A monitorada sozinha pediu retro. A exclusão pelo caminho da própria chamada e o slash externo mantiveram o silêncio.
- `d3484a5` — `BUG-01` confirmado. Carregar a monitorada sem seu metadado, completar a externa de outra mensagem e chamar Stop encerra a atribuição. Acrescentar o metadado atrasado da monitorada sem `sourceToolUseID` (ou com o campo vazio), seguido de trabalho com erro, faz o segundo Stop pedir retro. Com o ID preservado, o segundo Stop fica em silêncio.
- `d3484a5` — Em `Scanner.skill_path` (`retrofit_watch.py:600–611`), uma origem ausente ou vazia vira `None` e chega a `_watch` como nova atribuição. O controle com ID preservado cai no ramo que descarta o vínculo obsoleto. O teste falhou nas duas variantes sem vínculo, com 2 falhas de asserção, e o Check de `F1` foi validado em vermelho.

## Artefatos

| Arquivo | O que contém |
|---|---|
| `e2e/test_retrofit_watch_stop.py` | Teste ponta a ponta do Stop que registra `BUG-01`, com subprocessos, transcript e estado em disco. |
| `docs/handoffs/20261125-retrofit-watch-atribuicao/checkpoint.md` | `F1` em `pending`, com teste de regressão e nova execução da sonda de I1. |

## Boot da próxima fase

Antes do REVIEW, o executor deve ler `docs/handoffs/20261125-retrofit-watch-atribuicao/checkpoint.md` e seguir o Check de `F1`. A correção deve manter o Stop silencioso após o metadado atrasado sem vínculo, sem afetar a carga legítima por slash ou a retomada 0.4.0. Incorpore a cobertura de `BUG-01` à suíte descoberta por `TEST_CMD` e preserve a reprodução ponta a ponta do checkpoint.

Depois de `F1` concluído, a QA deve repetir o caso em dois Stops, a sonda de I1 e a suíte e registrar os resultados aqui. Para iniciar a revisão, confirmar que este handoff é posterior ao commit de `F1` e comparar `git diff main...HEAD` com a regra de origem de `01-plano.md`.

## Pendências / Decisions for a Human

Nenhuma decisão humana surgiu na QA. O merge continua reservado ao mantenedor, conforme o aceite do plano.

## Riscos e não-feitos

- A correção de produção de `F1` não foi feita nesta sessão.
- A validação usou o hook real com transcripts sintéticos, sem iniciar o Claude Code. As três provas de distribuição nativa do Codex ficaram de fora pelo `TEST_CMD` configurado.

## Achados fora de escopo

Nenhum achado fora do escopo confirmado nesta QA.
