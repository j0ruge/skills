---
missao: 20261125-retrofit-watch-atribuicao
fase: REVIEW
rodada: 26
status: done
sessao: 01a21fdf-0e17-7f13-9287-19ced5f528c5
data: 2026-11-27 23:02
gate: 'Em c883c7b35b0192f7b532265807dcc4e485883778, árvore inicial limpa. env -u GIT_DIR -u GIT_WORK_TREE PYTHONDONTWRITEBYTECODE=1 bash -c ''source .sdd/config.sh && eval "$TEST_CMD"'' → rc 0. Adaptadores e catálogo válidos, 154 testes da loja (3 pulados), 127 do hook, versão 0.4.1 validada. Os 18 Checks existentes passaram, incluindo R16 e F1. A sonda nova reproduziu seis encerramentos indevidos e R17 ficou pendente. Code Quality (Zen), Error Handling e Test Coverage continuam em B, no mesmo patamar de r25. O gate não passou.'
reviewed_head: c883c7b35b0192f7b532265807dcc4e485883778
---

# Review — rodada r26 — Atribuição da retrofit-watch por mensagem

## TL;DR

R16 fechou a perda de vínculo da falha própria após os dois limites. A r26 encontrou a regressão inversa
quando uma chamada anterior, já observada depois do limite, usa o mesmo ID que a carga monitorada.
Seu erro encerra o crédito da monitorada mesmo após o sucesso dela. R17 registra o caso.
Nota geral B, sem alterações em código.

## Nota da rodada

Apliquei `/codereview:codereview base=4794fd4d63d95bb1911540da725720f58ac5ef9e` até `c883c7b35b0192f7b532265807dcc4e485883778`.
O recorte contém seis commits e nove arquivos analisados, com 327 adições e 22 remoções.
Um módulo Python e seus testes, quatro documentos do produto e três artefatos da missão.
O diário append-only fica fora do recorte. A revisão do módulo e o sweep foram em linha.
O handoff de QA delimitou o reteste da F1, que permaneceu silenciosa nas três variantes.

### Secrets Detection

| Ocorrências | Scanners | Arquivos | Linhas adicionadas | Status |
|---|---|---|---|---|
| 0 | regex e gitleaks | 9 | 327 | PASS |

Sem erros no pré-scan. O delta não muda os caminhos de leitura, as permissões, a trava ou a gravação do estado.
Não há consulta nova a arquivos externos nem alteração na interface do Stop. Sem interface visual no recorte.

### Qualidade, cobertura e sincronização

| Área | Sensor | Resultado |
|---|---|---|
| Módulo `retrofit_watch.py` | `test_retrofit_watch.py` importa o módulo e chama o hook em subprocesso | Um de um módulo com teste atualizado. A regressão durável de R16 passou e cobre os dois limites, erro próprio, erro alheio com ID distinto e repetição do ID depois de abrir o crédito. |
| Tratamento de erro e integridade | Sonda R17 com transcript e estado reais em disco | A repetição na ordem inversa fecha indevidamente o crédito em seis subcasos. O Stop avança o offset até o fim e não deixa `errors.log`, mas persiste `attribution_closed=true` e não emite a retro. |
| Custo e tipos | Condição alterada e estado persistido da sonda | A comparação usa IDs textuais já validados. Não há nova leitura, repetição de prefixo ou ampliação das coleções de correlação. Em todos os cenários depois do limite, a origem por mensagem ficou nula e as quatro coleções permaneceram vazias. |
| Regra pública | README, guia, CHANGELOG e SKILL | Os textos distinguem o vínculo direto com a própria chamada da prova de mesma mensagem. A divergência em ID repetido é funcional. A versão 0.4.1 e os vínculos entre os documentos permanecem válidos. |

### Varredura de símbolos

Bucket A em linha. O código não ganhou nem perdeu funções, importações ou chaves de interface.
O único método de teste adicionado foi descoberto pelo `unittest` e executado isoladamente. Nenhum símbolo
órfão no delta. Bucket B não solicitado.

### Overall Grade

| Criterion | Grade | Rationale |
|-----------|-------|-----------|
| Code Quality (Zen) | B | A condição usa um ID diferente do ativo como sinal de ID novo após o limite. Isso não exclui disputa observada antes de abrir o crédito. |
| Type Safety | A | A chamada e o resultado passam pela validação de ID antes de comparação ou consulta. Não há novos formatos, coerções ou indexações de origem. |
| Error Handling | B | Um erro da chamada anterior encerra o crédito da carga bem-sucedida em seis cenários, sem erro de execução do hook. |
| Security | A | O pré-scan não encontrou credenciais e o delta não altera acesso a arquivos, permissões nem sincronização. |
| Performance | A | A decisão acrescenta só comparação e consulta ao estado existente. As coleções de correlação permanecem vazias após os dois limites. |
| Test Coverage | B | A regressão durável de R16 passa, mas o teste de reuso só repete o ID depois de abrir o crédito e não cobre a ordem em que o ID já vinha de outra chamada. |
| Documentation | A | Os textos mantêm a distinção entre erro próprio e correlação de mensagem. A regra documentada identificou a divergência funcional. |
| **Overall** | **B** | R16 corrigiu a falha própria. A regressão de erro alheio no mesmo ponto mantém três critérios técnicos no patamar anterior. |

## Achados da rodada

| # | Severidade | Achado | Onde |
|---|---|---|---|
| 1 | MEDIUM | Depois do limite, o erro de uma chamada anterior encerra o crédito de uma carga bem-sucedida que reutilizou seu ID. | `plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py:768–774` |

Depois de esgotar a janela, chegam duas chamadas de Skill em mensagens distintas. A primeira não
abre atribuição. A segunda é a monitorada e traz o mesmo ID. Como a janela já está desativada,
`_skill_origin` não registra a primeira chamada. A condição alterada aceita o ID na segunda
porque ele é diferente de `current_call`, que ainda é nulo. Mesmo após o sucesso da monitorada,
o erro tardio da chamada anterior coincide com `current_call` e encerra o crédito futuro.

Na base, nos seis casos ambíguos, o Stop emitiu a retro de `codereview`. No HEAD, todos ficaram
em silêncio, com zero revisões e atribuição encerrada. O problema ocorre com ambos os limites,
sem corte e com corte antes ou depois da segunda chamada. O pedido perdido é de uma única
atribuição e exige um transcript com ID repetido após o estouro. Não houve crash nem perda de
histórico persistido. Por isso o achado é MEDIUM.

## Incrementos de conserto (R<n>)

| R<n> | Achado | Check escrito no checkpoint |
|---|---|---|
| R17 | 1 | `env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -c "$(sed -n '/^~~~python$/,/^~~~$/{ /^~~~/!p; }' docs/handoffs/20261125-retrofit-watch-atribuicao/40-review-r26.md)" --expect && env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B e2e/test_retrofit_watch_stop.py && if o=$(env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -m unittest -q test_retrofit_watch.StopTest.test_prior_reused_call_does_not_close_after_correlation_overflow 2>&1); then [[ "$o" == *"Ran 1 test"* && "$o" == *"OK" ]] && printf 'regressao=1\n'; else printf '%s\n' "$o" >&2; exit 1; fi` → `antes_mensagens=codereview:0:1,codereview:0:1,codereview:0:1 antes_ids=codereview:0:1,codereview:0:1,codereview:0:1 depois=codereview:0:1,codereview:0:1,codereview:0:1 distinto=codereview:0:1,codereview:0:1,codereview:0:1 proprio=silêncio:1:0,silêncio:1:0,silêncio:1:0 linked=silêncio missing=silêncio empty=silêncio regressao=1` |

## O que virou incremento

- Achado 1 → R17. Exige preservar a monitorada quando o erro não identifica univocamente a carga ativa.
  Cobre o reuso já observado depois de ambos os limites, seguido de sucesso da monitorada e erro tardio
  da outra chamada. Mantém os controles de ID distinto, reuso posterior e falha própria, sem reativar
  a correlação de mensagens nem ampliar seus tetos. O Check inclui F1 e um teste de regressão durável.
- R16 (r25, achado 1) fechado em `fcdea17`. A célula de R16 passou integralmente no HEAD.
  A falha própria ficou silenciosa após ambos os limites e na ausência de ID de mensagem.
  Sucesso, erro de outra chamada com ID distinto e reuso que ocorre depois da abertura mantiveram a retro.

## O que foi refutado

- A janela esgotada não invalida todo erro próprio. O controle `proprio` preservou o silêncio e o
  encerramento no HEAD nas três disposições, enquanto voltar ao tratamento da base produziu
  três pedidos indevidos. Reverter R16 não satisfaz R17.
- O erro não encerra a atribuição só por vir de uma chamada anterior. Com ID distinto
  (`distinto`), o HEAD emitiu `codereview:0:1` nos três cortes. Também emitiu retro quando o
  ID foi repetido depois de abrir o crédito (`depois`). Os seis casos vermelhos exigem a
  ordem inversa com o mesmo ID.

## Achados fora de escopo

Nenhum achado novo fora do escopo. Não houve alteração em `TODO.md`.

## Pendências / Decisions for a Human

A rodada corrigiu zero arquivos de código. As notas técnicas repetem as da r25 apesar do conserto
real em `fcdea17`. A revisão para neste patamar e deixa R17 no checkpoint, com a reprodução para
a decisão sobre a próxima rodada. A integração do PR continua com o mantenedor.

## Evidências reproduzíveis

- Rode a suíte da configuração no HEAD revisado com
  `env -u GIT_DIR -u GIT_WORK_TREE PYTHONDONTWRITEBYTECODE=1 bash -c 'source .sdd/config.sh && eval "$TEST_CMD"'`. RC 0, 154 testes da loja com três pulados e 127 do hook.
  Adaptadores, catálogo e versão 0.4.1 passaram. Não houve execução no host Claude Code nem nova prova
  nativa. Os avisos do validador são de outros plugins fora do delta.
- Em `c883c7b35b0192f7b532265807dcc4e485883778`, rode em Bash cada comando já concluído (I1, F1 e R1–R16) antes de
  `→` no checkpoint, com `GIT_DIR` e `GIT_WORK_TREE` removidos para proteger o Git privado.
  Compare RC e stdout normalizando apenas espaços. Os 18 Checks passaram. I1 voltou
  `1 0 1 0 0 1` e a F1 voltou `linked=silêncio missing=silêncio empty=silêncio`.
- Para a checagem dirigida, `env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -m unittest -q test_retrofit_watch.StopTest.test_active_skill_failure_after_correlation_overflow test_retrofit_watch.StopTest.test_ambiguous_call_failure_does_not_close_attribution test_auto_docs.ReleaseTest`
  executou seis testes e saiu com RC 0 no mesmo HEAD.
- Rode o primeiro comando da célula R17 até `--expect` no HEAD. RC 1. Para comparar, extraia
  `git show 4794fd4d63d95bb1911540da725720f58ac5ef9e:plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py`
  para um arquivo Python temporário. Rode a sonda com `--script "$arquivo"` no lugar de
  `--expect`. RC 0 em modo de observação. Em cada linha, a ordem é leitura contínua, corte
  antes da carga monitorada e corte depois dela. Os campos são alvo, atribuição encerrada e
  revisões. O harness verifica offset completo e ausência de `errors.log` em cada Stop.

**HEAD observado**

~~~text
antes_mensagens=silêncio:1:0,silêncio:1:0,silêncio:1:0
antes_ids=silêncio:1:0,silêncio:1:0,silêncio:1:0
depois=codereview:0:1,codereview:0:1,codereview:0:1
distinto=codereview:0:1,codereview:0:1,codereview:0:1
proprio=silêncio:1:0,silêncio:1:0,silêncio:1:0
~~~

**Base observada**

~~~text
antes_mensagens=codereview:0:1,codereview:0:1,codereview:0:1
antes_ids=codereview:0:1,codereview:0:1,codereview:0:1
depois=codereview:0:1,codereview:0:1,codereview:0:1
distinto=codereview:0:1,codereview:0:1,codereview:0:1
proprio=codereview:0:1,codereview:0:1,codereview:0:1
~~~

**Esperado**

~~~text
antes_mensagens=codereview:0:1,codereview:0:1,codereview:0:1
antes_ids=codereview:0:1,codereview:0:1,codereview:0:1
depois=codereview:0:1,codereview:0:1,codereview:0:1
distinto=codereview:0:1,codereview:0:1,codereview:0:1
proprio=silêncio:1:0,silêncio:1:0,silêncio:1:0
~~~

- Para repetir o pré-scan, use
  `git -P diff 4794fd4d63d95bb1911540da725720f58ac5ef9e...c883c7b35b0192f7b532265807dcc4e485883778 --unified=0 -- . ':(exclude)**/checkpoint-notas.md' | bash "$HOME/.agents/skills/codereview/scripts/scan_secrets.sh"`.

### Sonda de R17

~~~python
import argparse
from pathlib import Path

from test_retrofit_watch import SCRIPT, StopTest, identified_load, rw, tool


def measure(case, cut, script):
    test = StopTest()
    test.setUp()
    try:
        id_limit = case == "antes_ids"
        cap = rw.MAX_SKILL_CALL_IDS if id_limit else rw.MAX_SKILL_MESSAGES
        pending = [
            identified_load("irrelevante", test.w.other_skill,
                            "msg_lote" if id_limit else f"msg_lote_{i}", f"toolu_lote_{i}")[0]
            for i in range(cap + 1)
        ]
        shared_id = "toolu_ativo"
        other_id = "toolu_alheio" if case == "distinto" else shared_id
        other = identified_load("irrelevante", test.w.other_skill, "msg_alheia", other_id)
        active = identified_load("codereview:coderabbit-pr", test.w.mkt_skill, "msg_ativa", shared_id)

        def prefix(expected_current):
            out, state = test.checked_stop(script=script, mode="plan")
            assert out is None and state["current"] == expected_current, state
            assert state["skill_correlation_lost"] and state["current_origin"] is None, state

        test.write(pending, compact=True)
        if case not in ("depois", "proprio"):
            test.write(other[:1], compact=True)
        if cut == "antes":
            prefix(None)
        test.write(active[:1], compact=True)
        if case == "depois":
            test.write(other[:1], compact=True)
        if cut == "depois":
            prefix("full:codereview")
        failed = active[1] if case == "proprio" else other[1]
        failed["message"]["content"][0]["is_error"] = True
        if case != "proprio":
            test.write(active[1:], compact=True)
        test.write([failed], tool(error=True), compact=True)
        out, state = test.checked_stop(script=script)
        assert state["skill_correlation_lost"] and state["current_origin"] is None, state
        assert not any(state[k] for k in ("skill_calls", "skill_call_history",
                                          "skill_message_order", "retired_skill_calls")), state
        credit = state["skills"]["full:codereview"]
        if out is not None:
            assert "`/retrofit-skill:retrofit-skill codereview`" in test.context_of(out), out
            assert state["current"] == "full:codereview" and state["pending"] == ["codereview"], state
        else:
            assert state["current"] is None and not state["pending"], state
        return f"{'codereview' if out else 'silêncio'}:{int(state['attribution_closed'])}:{credit['reviews']}"
    finally:
        test.tearDown()


parser = argparse.ArgumentParser()
parser.add_argument("--script", type=Path, default=SCRIPT)
parser.add_argument("--expect", action="store_true")
args = parser.parse_args()
opened = "codereview:0:1"
closed = "silêncio:1:0"
expected = {case: ",".join([closed if case == "proprio" else opened] * 3)
            for case in ("antes_mensagens", "antes_ids", "depois", "distinto", "proprio")}
observed = {
    case: ",".join(measure(case, cut, args.script) for cut in ("contínuo", "antes", "depois"))
    for case in expected
}
for case, result in observed.items():
    print(f"{case}={result}")
if args.expect and observed != expected:
    raise SystemExit(1)
~~~

### Recommended Actions

**Must Fix (CRITICAL)**

_Nenhum._

**Should Fix (HIGH)**

_Nenhum._

**Consider Fixing (MEDIUM/LOW)**

- Tratar o reuso já observado antes de abrir o crédito no modo sem janela, sem perder a identificação
  direta do erro próprio de R16 nem usar esse vínculo para correlacionar mensagens.

### Cost footprint

_Codereview 2.27.38 do caminho solicitado. Cache Claude 2.30.2 identificado e não usado.
Código, testes, Bucket A e consolidação em linha. Quatro revisões documentais com
`gpt-6.1-terra`, todas com marcador de conclusão. Nenhum relançamento. Custo monetário não medido._
