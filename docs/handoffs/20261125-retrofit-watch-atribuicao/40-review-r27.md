---
missao: 20261125-retrofit-watch-atribuicao
fase: REVIEW
rodada: 27
status: done
sessao: 01a21fed-f10f-7123-934d-503854ab08d9
data: 2026-11-27 23:20
gate: "Em 5260a1a69942652c432adbc30e47ae9e8a8741bc, árvore inicial limpa. env -u GIT_DIR -u GIT_WORK_TREE PYTHONDONTWRITEBYTECODE=1 bash -c 'source .sdd/config.sh && eval \"$TEST_CMD\"' retornou rc 0. Adaptadores e catálogo válidos, 154 testes da loja (3 pulados), 129 do hook, versão 0.4.1 validada. Os 19 Checks concluídos passaram, incluindo I1, F1, R16 e R17. As duas sondas novas deram rc 1 e R18 ficou pendente. Type Safety caiu de A para B. Code Quality (Zen), Error Handling e Test Coverage permanecem em B. O gate não passou."
reviewed_head: 5260a1a69942652c432adbc30e47ae9e8a8741bc
---

# Review — rodada r27 — Atribuição da retrofit-watch por mensagem

## TL;DR

R17 fechou o reuso já observado após o limite. A r27 reproduziu dois problemas no delta: um ID observado antes ou na transição ainda pode encerrar o crédito errado, e um valor inválido no registro novo impede o avanço de Stop. Os dois achados estão no R18. Nota geral B, com regressão em Type Safety.

## Nota da rodada

Apliquei `/codereview:codereview base=c883c7b35b0192f7b532265807dcc4e485883778` até `5260a1a69942652c432adbc30e47ae9e8a8741bc`. Sete commits, dez arquivos, 428 adições e 26 remoções. O recorte tem um módulo Python, um arquivo de testes e oito documentos. O diário append-only ficou fora da leitura. A QA delimitou F1 e o contrato original de retomada.

### Secrets Detection

| Ocorrências | Scanners | Arquivos | Linhas adicionadas | Status |
|---|---|---|---|---|
| 0 | regex e gitleaks | 10 | 428 | PASS |

Sem erros no pré-scan. O delta não altera permissões, sincronização, destinos de leitura ou gravação, nem a interface visual.

### Qualidade, cobertura e sincronização

| Área | Evidência |
|---|---|
| Módulo Python | Um de um com teste revisado. Os dois testes novos cobrem reuso após a perda, saturação, reconstruções aceitas e rejeitadas e metadados sem prova. |
| Tratamento de erro | O mesmo ID antes ou na transição ainda provoca 12 encerramentos indevidos. Um campo persistido com tipo errado interrompe dois Stops seguidos em cada uma de duas variantes. |
| Custo | Um dicionário com teto de 1.024 entradas em estado produzido pelo hook. A consulta por chamada não adiciona leitura ou varredura do prefixo normal. O cenário de fronteira conserva as quatro coleções de mensagem vazias. |
| Documentação | README, guia, CHANGELOG e SKILL descrevem o registro pós-limite sem lhe atribuir valor de prova para metadados. O handoff de EXEC explicita que não se reconstroem IDs descartados. As revisões documentais não encontraram outro desvio. |

### Varredura de símbolos

Bucket A em linha. A comparação de declarações por AST não encontrou adição ou remoção de funções, classes ou importações no módulo. Os dois métodos novos de teste foram descobertos pela suíte, e o auxiliar local é chamado pelos cenários de limite. Nenhum símbolo órfão no delta. Bucket B não solicitado.

### Overall Grade

| Criterion | Grade | Rationale |
|-----------|-------|-----------|
| Code Quality (Zen) | B | A ausência no registro pós-limite é aceita como novidade mesmo quando o ID estava retido na transição. |
| Type Safety | B | O novo campo JSON tem default para ausência, mas não valida o tipo antes da busca e da escrita por chave. |
| Error Handling | B | Um erro alheio encerra o crédito em 12 cenários e os dois formatos inválidos repetem a falha sem avançar o offset. |
| Security | A | O pré-scan não encontrou credenciais e o delta não alterou superfície de acesso, travas ou permissões. |
| Performance | A | A consulta direta é limitada pelo teto de IDs, sem releitura do prefixo normal ou crescimento da janela de mensagens. |
| Test Coverage | B | R17 e os controles de limite passam, mas não cobrem o ID ainda retido na transição nem a retomada com tipo inválido no registro novo. |
| Documentation | A | Os documentos descrevem o limite e o handoff registra a perda do histórico descartado. Nenhum achado exclusivamente de prosa foi confirmado. |
| **Overall** | **B** | R17 fecha o cenário da r26. Dois achados de execução permanecem e um critério técnico regrediu. |

## Achados da rodada

| # | Severidade | Achado | Onde |
|---|---|---|---|
| 1 | MEDIUM | Perder a janela faz um ID ainda retido parecer novo. O erro tardio da primeira chamada encerra o crédito da monitorada bem-sucedida. | `plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py:768–775` |
| 2 | MEDIUM | Um registro direto malformado no JSON da sessão impede o Stop de processar qualquer delta que contenha outra chamada de Skill. | `plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py:423–428,770–774` |

**1. ID que cruza o limite.** Uma chamada alheia precede a perda da janela ou é a chamada que a dispara. Nas duas ordens seu ID ainda fazia parte da janela que acaba de ser descartada. Depois, a monitorada reutiliza o ID e tem sucesso. O resultado de erro atrasado da chamada alheia é tratado como erro próprio, fecha `current` e deixa zero revisões. A sonda reproduziu isso com os limites reais de mensagens e IDs, em leitura contínua e com corte de Stop antes ou depois da perda. A base também falha nesses 12 casos. O delta melhora o reuso pós-limite, mas seu novo predicado de ID novo ainda perdeu a evidência que existia na transição. O Check pede apenas os IDs ainda retidos naquele momento, não o histórico inteiro já podado.

**2. Tipo do registro persistido.** Depois de um Stop confirmar a perda de correlação, a sonda troca apenas `uncorrelated_skill_calls` no arquivo de sessão por `null` ou `[]`. O arquivo continua sendo um JSON válido. Em `null`, a busca `call_id not in seen` levanta `TypeError`. Em `[]`, a atribuição `seen[call_id] = True` levanta `TypeError`. O processo retorna 0, mas não salva o offset e registra a exceção em `errors.log`. O Stop seguinte repete a falha no mesmo ponto. Ausência da chave e objeto vazio passam no HEAD. A base ignora esse novo campo, segue até o fim e emite a retro nas duas variantes. O impacto é restrito à sessão com estado local inválido, mas impede sua retomada de forma persistente.

## Incrementos de conserto (R<n>)

| R<n> | Achado | Check escrito no checkpoint |
|---|---|---|
| R18 | 1 e 2 | `env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -c "$(sed -n '/^~~~python$/,/^~~~$/{ /^~~~/!p; }' docs/handoffs/20261125-retrofit-watch-atribuicao/40-review-r27.md)" --expect --group window && env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -c "$(sed -n '/^~~~python$/,/^~~~$/{ /^~~~/!p; }' docs/handoffs/20261125-retrofit-watch-atribuicao/40-review-r27.md)" --expect --group state && env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B e2e/test_retrofit_watch_stop.py && if o=$(env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -m unittest -q test_retrofit_watch.StopTest.test_reused_call_across_correlation_overflow_does_not_close_attribution test_retrofit_watch.StopTest.test_invalid_direct_call_history_does_not_break_stop 2>&1); then [[ "$o" == *"Ran 2 tests"* && "$o" == *"OK" ]] && printf 'regressoes=2\n'; else printf '%s\n' "$o" >&2; exit 1; fi` → `before_messages=codereview:0:1,codereview:0:1,codereview:0:1 before_ids=codereview:0:1,codereview:0:1,codereview:0:1 trigger_messages=codereview:0:1,codereview:0:1,codereview:0:1 trigger_ids=codereview:0:1,codereview:0:1,codereview:0:1 after=codereview:0:1,codereview:0:1,codereview:0:1 different=codereview:0:1,codereview:0:1,codereview:0:1 own_error=silêncio:1:0,silêncio:1:0,silêncio:1:0 missing=codereview:1:0 object=codereview:1:0 null=codereview:1:0 list=codereview:1:0 linked=silêncio missing=silêncio empty=silêncio regressoes=2` |

## O que virou incremento

- Achados 1 e 2 → R18, um lote com Check para a transição dos dois limites e outro para o tipo persistido. Exige retro para a monitorada nos reusos ambíguos, silêncio para a falha própria nova, offset completo e ausência de erro interno após retomar estado inválido. A jornada F1 e duas regressões permanentes fazem parte da célula.
- R17 (r26, achado 1) foi fechado em `a19e5b5`. O Check de R17 passou integralmente em `5260a1a`, com retro nos seis casos de reuso já observado após os limites e silêncio nos três casos de falha própria. A suíte executou os dois novos métodos de regressão, inclusive a reconstrução legada e o teto do registro.

## O que foi refutado

- A perda da janela não torna toda falha própria indistinguível. `own_error` fechou corretamente nos três cortes, e `different` preservou a retro com um ID alheio distinto. O reparo não deve desativar o vínculo direto em bloco.
- O problema de fronteira não foi introduzido por R17. A base também fecha indevidamente os 12 casos. O controle `after` prova o conserto real de R17, pois passa de silêncio na base para retro no HEAD em cada corte.
- A mera ausência da chave nova não trava a atualização. O controle `missing` emitiu a retro e avançou o offset na base e no HEAD. A regressão de tipo exige o campo presente com valor inválido.
- O registro direto não dá origem comprovada a metadados. O caso `external_meta` da regressão de limite passou e a jornada F1 manteve as três variantes silenciosas.

## Achados fora de escopo

Nenhum achado novo fora do escopo. O backlog não foi alterado.

## Pendências / Decisions for a Human

R17 fechou com um commit funcional, mas Code Quality (Zen), Error Handling e Test Coverage permanecem em B. Type Safety caiu de A para B. A revisão para pela regressão e deixa R18 pendente para a decisão do mantenedor. Esta rodada não alterou código nem executou ações no PR.

## Evidências reproduzíveis

- Em `5260a1a69942652c432adbc30e47ae9e8a8741bc`, executei `env -u GIT_DIR -u GIT_WORK_TREE PYTHONDONTWRITEBYTECODE=1 bash -c 'source .sdd/config.sh && eval "$TEST_CMD"'`. RC 0, adaptadores, catálogo e versão 0.4.1 válidos, 154 testes da loja (três pulados) e 129 do hook. Não repeti as provas nativas nem executei no host Claude Code.
- No mesmo HEAD, executei em Bash cada célula concluída (I1, F1 e R1–R17), com `GIT_DIR` e `GIT_WORK_TREE` removidos. RC 0 e stdout esperado nos 19 Checks, normalizando apenas espaços entre os tokens. I1 voltou `1 0 1 0 0 1` e F1, `linked=silêncio missing=silêncio empty=silêncio`.
- Os primeiros dois comandos de R18 usam as opções `--group window` e `--group state`. Cada um retornou rc 1 no HEAD. Compare com a base extraindo `git show c883c7b35b0192f7b532265807dcc4e485883778:plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py` para um arquivo Python temporário e substituindo `--expect --group ...` por `--script "$arquivo"` na primeira chamada da sonda. A base em modo de observação retornou rc 0, que não significa que o comportamento seja o esperado.
- Na sonda de janela, a ordem da saída é leitura contínua, corte antes do estouro e corte entre o estouro e a monitorada. Cada campo mede alvo, encerramento e revisões. Na sonda de estado, cada campo mede alvo, offset no fim e número de `TypeError` em até dois Stops.
- Para repetir o pré-scan, use `git -P diff c883c7b35b0192f7b532265807dcc4e485883778...5260a1a69942652c432adbc30e47ae9e8a8741bc --unified=0 -- . ':(exclude)**/checkpoint-notas.md' | bash /home/joruge/.agents/skills/codereview/scripts/scan_secrets.sh`.

**HEAD observado**

~~~text
before_messages=silêncio:1:0,silêncio:1:0,silêncio:1:0
before_ids=silêncio:1:0,silêncio:1:0,silêncio:1:0
trigger_messages=silêncio:1:0,silêncio:1:0,silêncio:1:0
trigger_ids=silêncio:1:0,silêncio:1:0,silêncio:1:0
after=codereview:0:1,codereview:0:1,codereview:0:1
different=codereview:0:1,codereview:0:1,codereview:0:1
own_error=silêncio:1:0,silêncio:1:0,silêncio:1:0
missing=codereview:1:0
object=codereview:1:0
null=silêncio:0:2
list=silêncio:0:2
~~~

**Base observada**

~~~text
before_messages=silêncio:1:0,silêncio:1:0,silêncio:1:0
before_ids=silêncio:1:0,silêncio:1:0,silêncio:1:0
trigger_messages=silêncio:1:0,silêncio:1:0,silêncio:1:0
trigger_ids=silêncio:1:0,silêncio:1:0,silêncio:1:0
after=silêncio:1:0,silêncio:1:0,silêncio:1:0
different=codereview:0:1,codereview:0:1,codereview:0:1
own_error=silêncio:1:0,silêncio:1:0,silêncio:1:0
missing=codereview:1:0
object=codereview:1:0
null=codereview:1:0
list=codereview:1:0
~~~

### Sondas de R18

~~~python
import argparse
import json
from pathlib import Path

from test_retrofit_watch import SCRIPT, StopTest, identified_load, rw, tool


def measure(case, cut, script):
    test = StopTest()
    test.setUp()
    try:
        id_limit = case.endswith("_ids")
        cap = rw.MAX_SKILL_CALL_IDS if id_limit else rw.MAX_SKILL_MESSAGES
        pending = [
            identified_load("irrelevante", test.w.other_skill,
                            "msg_lote" if id_limit else f"msg_{i}", f"toolu_{i}")[0]
            for i in range(cap + 1)
        ]
        active_id = "toolu_ativo"
        other = identified_load("irrelevante", test.w.other_skill,
                                 "msg_lote" if id_limit else "msg_alheia",
                                 "toolu_distinto" if case == "different" else active_id)
        active = identified_load("codereview:coderabbit-pr", test.w.mkt_skill, "msg_ativa", active_id)
        if case.startswith("before_"):
            pending[0] = other[0]
        elif case.startswith("trigger_"):
            pending[-1] = other[0]
        elif case in ("after", "different"):
            pending.append(other[0])
        if cut == "before_limit":
            test.write(pending[:-1] if case.startswith("trigger_") else pending[:1], compact=True)
            out, state = test.checked_stop(mode="plan", script=script)
            assert out is None and not state["skill_correlation_lost"], state
            test.write(pending[-1:] if case.startswith("trigger_") else pending[1:], compact=True)
        else:
            test.write(pending, compact=True)
        if cut == "after_limit":
            out, state = test.checked_stop(mode="plan", script=script)
            assert out is None and state["skill_correlation_lost"] and state["current"] is None, state
        test.write(active[:1], compact=True)
        failed = active[1] if case == "own_error" else other[1]
        failed["message"]["content"][0]["is_error"] = True
        if case != "own_error":
            test.write(active[1:], compact=True)
        test.write([failed], tool(error=True), compact=True)
        out, state = test.checked_stop(script=script)
        assert state["skill_correlation_lost"] and state["current_origin"] is None, state
        assert not any(state[k] for k in ("skill_calls", "skill_call_history",
                                         "skill_message_order", "retired_skill_calls")), state
        if out:
            assert "`/retrofit-skill:retrofit-skill codereview`" in test.context_of(out), out
            assert state["current"] == "full:codereview" and state["pending"] == ["codereview"], state
        else:
            assert state["current"] is None and not state["pending"], state
        reviews = state["skills"]["full:codereview"]["reviews"]
        return f"{'codereview' if out else 'silêncio'}:{int(state['attribution_closed'])}:{reviews}"
    finally:
        test.tearDown()


def measure_state(value, script):
    test = StopTest()
    test.setUp()
    try:
        for i in range(rw.MAX_SKILL_MESSAGES + 1):
            test.write(identified_load("irrelevante", test.w.other_skill,
                                        f"msg_{i}", f"toolu_{i}")[:1], compact=True)
        assert test.checked_stop(mode="plan", script=script)[0] is None
        path = test.w.data / "sessions/s1.json"
        state = json.loads(path.read_bytes())
        assert state["skill_correlation_lost"], state
        if value != "missing":
            state["uncorrelated_skill_calls"] = value
        else:
            state.pop("uncorrelated_skill_calls", None)
        path.write_text(json.dumps(state), encoding="utf-8")
        active = identified_load("codereview:coderabbit-pr", test.w.mkt_skill, "msg_ativa", "toolu_ativa")
        test.write(active, tool(error=True), compact=True)
        for _ in range(2):
            out = test.run_hook(script=script)
            if out:
                assert "`/retrofit-skill:retrofit-skill codereview`" in test.context_of(out), out
                break
        final = json.loads(path.read_bytes())
        errors = test.w.data / "errors.log"
        error_count = errors.read_text(encoding="utf-8").count("TypeError") if errors.exists() else 0
        return f"{'codereview' if out else 'silêncio'}:{int(final['offset'] == test.w.transcript.stat().st_size)}:{error_count}"
    finally:
        test.tearDown()


parser = argparse.ArgumentParser()
parser.add_argument("--script", type=Path, default=SCRIPT)
parser.add_argument("--group", choices=("all", "window", "state"), default="all")
parser.add_argument("--expect", action="store_true")
args = parser.parse_args()
cuts = ("continuous", "before_limit", "after_limit")
observed, expected = {}, {}
if args.group in ("all", "window"):
    for case in ("before_messages", "before_ids", "trigger_messages", "trigger_ids",
                 "after", "different", "own_error"):
        observed[case] = ",".join(measure(case, cut, args.script) for cut in cuts)
        expected[case] = ",".join(["silêncio:1:0" if case == "own_error" else "codereview:0:1"] * 3)
if args.group in ("all", "state"):
    for name, value in (("missing", "missing"), ("object", {}), ("null", None), ("list", [])):
        observed[name] = measure_state(value, args.script)
        expected[name] = "codereview:1:0"
for name, value in observed.items():
    print(f"{name}={value}")
if args.expect and observed != expected:
    raise SystemExit(1)
~~~

### Recommended Actions

**Must Fix (CRITICAL)**

_Nenhum._

**Should Fix (HIGH)**

_Nenhum._

**Consider Fixing (MEDIUM/LOW)**

- Conservar evidência limitada dos IDs ainda retidos quando a janela se perde, sem reativar a origem por mensagem ou impedir a detecção de uma falha própria nova.
- Normalizar um registro direto persistido com tipo inválido e retomar em modo conservador, sem perder contadores, histórico ou offset.

### Cost footprint

_Codereview 2.27.38 do caminho solicitado. Cache Claude 2.30.2 identificado e não usado. Código, testes e Bucket A em linha. Três agentes documentais gpt-6.1-terra, todos concluídos, sem relançamento. Custo monetário não medido._
