---
missao: 20261125-retrofit-watch-atribuicao
fase: REVIEW
rodada: 24
status: done
sessao: 01a21fc3-b1cf-7551-9261-ad25e618b219
data: 2026-11-27 22:33
gate: 'Em 9ddaaab25ab27f0e7f6b0230738e1c5cb517b903, árvore inicial limpa. env -u GIT_DIR -u GIT_WORK_TREE PYTHONDONTWRITEBYTECODE=1 bash -c ''source .sdd/config.sh && eval "$TEST_CMD"'' → rc 0. Adaptadores e catálogo válidos, 154 testes da loja (3 pulados), 124 do hook e versão 0.4.1 validada. 16 Checks com rc 0 e stdout esperado, incluindo R14 e F1. A sonda nova deixa R15 pendente. Type Safety regrediu de A para B. Code Quality (Zen), Error Handling, Test Coverage e Overall continuam em B.'
reviewed_head: 9ddaaab25ab27f0e7f6b0230738e1c5cb517b903
---

# Review — rodada r24 — Atribuição da retrofit-watch por mensagem

## TL;DR

As três correções funcionais de r23 estão comprovadas em `5459e8c`. A r24 reproduziu
duas regressões novas no Stop, bateladas em R15. A ordem do slash em um estado intermediário
ficou no backlog. Nota geral B. Nenhum código foi alterado nesta revisão.

## Nota da rodada

`/codereview:codereview base=c2c0c8c394eccfbde1e91039306886f7955844dd` limitou a análise ao
delta até `9ddaaab25ab27f0e7f6b0230738e1c5cb517b903`. Seis commits, 12 arquivos, 530 adições
e 49 remoções, sem consultar o diário append-only (33 adições excluídas pela estatística de paths).
Um módulo Python, um teste Python e dez documentos. O handoff de QA de `08f09a1` embasou o controle
de F1. O código e os testes são idênticos aos de `5459e8c`.

### Secrets Detection

| Ocorrências | Scanners | Arquivos | Linhas adicionadas | Status |
|---|---|---|---|---|
| 0 | regex e gitleaks | 12 | 530 | PASS |

O pré-scan não registrou erros. Nenhuma mudança na fronteira de permissões. A leitura e gravação
do estado por sessão continuam sob a mesma trava, com substituição atômica. A corrida entre
tamanho e leitura do prefixo não foi introduzida neste delta. A lista de IDs anterior ao slash
copia apenas os IDs da janela já limitada. O replay mantém o limite por registro. O Stop não
adiciona nem modifica interface visual.

### Cobertura e sincronização

| Código | Sensor | Resultado |
|---|---|---|
| `retrofit_watch.py` | Cinco novos métodos de `StopTest`, Checks de I1 e R14, jornada F1 | 1 de 1 módulo com testes atualizados. Os 5 métodos passaram e os 16 Checks reproduziram o stdout esperado. |
| `State.__enter__` e resultado de chamada | Sonda nova de R15, com estado real | As duas regressões não são cobertas pela suíte atual. |

A release continua em 0.4.1. O CHANGELOG não apresenta mais o ID aposentado como única prova.
O guia e a SKILL descrevem a regra pretendida de precedência do slash e encerramento por erro
da própria chamada. O falso encerramento medido é funcional, não uma licença para mudar essa regra.
As três provas nativas continuaram puladas pela configuração.

### Varredura de símbolos

Bucket A em linha. `_skill_origin`, `invocation` e `_watch` têm chamadas correspondentes à nova
assinatura. `current_call` e `slash_prior_calls` são gravados, consultados e testados. Nenhum
símbolo órfão no delta. Bucket B não solicitado.

### Overall Grade

| Criterion | Grade | Rationale |
|-----------|-------|-----------|
| Code Quality (Zen) | B | O fluxo separa ID de origem, mas a colisão detectada ainda vira prova para fechar a carga ativa. |
| Type Safety | B | O novo default pressupõe uma origem indexável com segundo elemento, antes de validar a forma do JSON persistido. |
| Error Handling | B | Uma falha de ID disputado corta o crédito e três formatos de origem inválida travam o avanço do Stop. |
| Security | A | Regex e gitleaks sem achados no recorte e nenhuma mudança na trava ou nas permissões do estado local. |
| Performance | A | A lista nova é uma fotografia dos IDs pendentes já limitados. O replay mantém o teto por registro. |
| Test Coverage | B | Os cinco testes novos e os 16 Checks passaram, mas não distinguem a falha de ID disputado nem a sessão que deixa de avançar com origem inválida. |
| Documentation | A | CHANGELOG, guia e SKILL descrevem a regra pretendida, sem a exclusividade que a r23 refutou. |
| **Overall** | **B** | R14 passou nos três pontos de r23. Duas regressões do delta foram reproduzidas, com R15 pendente. |

## Achados da rodada

| # | Severidade | Achado | Onde |
|---|---|---|---|
| 1 | MEDIUM | Um erro com ID disputado encerra a monitorada como se fosse comprovadamente da chamada ativa. | `plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py:765` e `plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py:797` |
| 2 | MEDIUM | Uma origem salva inválida impede qualquer progresso em um Stop que não precisa dela. | `plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py:429` |
| 3 | LOW | O estado intermediário sem ordem gravada trata um slash anterior como mais recente. | `plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py:430` |

1. A primeira tentativa, irrelevante, e a carga monitorada reconhecida pelo nome usam o
   mesmo ID. Outra pendência mantém a colisão na janela. `_skill_origin` detecta a ambiguidade,
   mas o novo `current_call` registra o mesmo ID e o erro da primeira tentativa fecha a
   segunda. Com o mesmo transcript, a base pediu `codereview` e o HEAD silenciou, tanto no
   fluxo contínuo quanto em dois Stops. Com dois IDs distintos a monitorada continua pedindo
   retro. Quando o erro é do ID único da carga ativa, o Stop deve silenciar nos dois cortes
   mesmo que falte `message.id`.
2. Ao abrir um objeto de estado válido com `current_origin` igual a uma lista de um elemento,
   um inteiro ou um objeto sem a posição esperada, a nova expressão em `setdefault` falha antes
   de ler seis chamadas de trabalho bem-sucedidas. O processo retorna rc 0, mas o offset fica
   parado e `errors.log` recebe, respectivamente, `IndexError`, `TypeError` e `KeyError`.
   No mesmo ensaio a base avança e emite a retro, sem usar a origem. O controle com origem
   intacta avança nos dois SHAs. A perda é do Stop inteiro, não só da correlação opcional.
3. Ao retomar arquivo criado por `c2c0c8c`, com slash digitado antes da chamada externa e
   metadados ainda por chegar, os IDs pendentes são assumidos como anteriores ao slash.
   A confirmação posterior não o expira e a saída indevida pede `graphify`. O corte com
   estado escrito pela 0.4.0 de `fe38d1f` funciona: silêncio para o slash anterior e
   `graphify` para o posterior. A métrica não promete migração de snapshots intermediários
   da branch. O caso vai ao backlog, sem exigir ampliar o replay nesta entrega.

## Incrementos de conserto (R<n>)

| R<n> | Achado | Check escrito no checkpoint |
|---|---|---|
| R15 | Achados 1–2 | `env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -c "$(sed -n '/^~~~python$/,/^~~~$/{ /^~~~/!p; }' docs/handoffs/20261125-retrofit-watch-atribuicao/40-review-r24.md)" --expect && env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B e2e/test_retrofit_watch_stop.py && if o=$(env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -m unittest -q test_retrofit_watch.StopTest.test_ambiguous_call_failure_does_not_close_attribution test_retrofit_watch.StopTest.test_malformed_saved_origin_does_not_break_stop 2>&1); then [[ "$o" == *"Ran 2 tests"* && "$o" == *"OK" ]] && printf 'regressoes=2\n'; else printf '%s\n' "$o" >&2; exit 1; fi` → `active=silêncio:1,silêncio:1 missing_message=silêncio:1,silêncio:1 different=codereview:1,codereview:1 reused=codereview:1,codereview:1 intact=codereview:1:0 short=codereview:1:0 numeric=codereview:1:0 braced=codereview:1:0 linked=silêncio missing=silêncio empty=silêncio regressoes=2` |

## O que virou incremento

- R15 agrupa os achados médios 1–2. A sonda deve exigir a retro para o ID em disputa
  e para o estado recuperável, sem perder o silêncio após erro da chamada única. As
  duas regressões duráveis e a jornada de F1 também precisam passar.
- R14 (r23, achados 1–3) foi fechado pelo executor em `5459e8c`. O Check reproduziu os
  nove pares esperados e a jornada F1. A falha própria sem `message.id` silenciou,
  a colisão sem origem não virou ID aposentado e o slash anterior não reabriu
  a atribuição. Todos os cinco testes novos passaram. O caso com erro de outro ID
  em r23 tinha IDs distintos e não cobre o achado 1.
- R23, achado 4, foi resolvido em `5459e8c`. A entrada agora distingue vínculo
  confirmado da mesma mensagem de ID aposentado. O controle
  `externa_da_mesma_mensagem=codereview:1,codereview:1` comprova a primeira via.

## O que foi refutado

- A regra de aposentadoria não passou a descartar todo metadado antigo. O Check de R14
  mediu `aposentadoria_ambigua=silêncio:1:0,silêncio:1:0` e
  `aposentadoria_conhecida=codereview:1:1,codereview:1:1`. O terceiro campo confirma
  quais IDs realmente chegaram à lista.
- A retomada suportada da 0.4.0 não perde genericamente a precedência do slash.
  Com o estado real de `fe38d1f`, a externa posterior silenciou e o slash mais novo
  pediu `graphify`. O desvio confirmado se limita ao snapshot intermediário sem essa ordem.
- O problema de estado inválido não foi provocado por um `tool_result` de erro.
  O ensaio usa seis chamadas bem-sucedidas e passa com a origem intacta. Assim isola
  a nova leitura durante a abertura de estado da leitura antiga no ramo de erro.

## Achados fora de escopo

- Achado 3 registrado na seção aberta de `TODO.md` (2026-11-27). Não altera R15
  nem reabre o item sobre migração da 0.4.0, que a sonda do Stop real confirmou.

## Pendências / Decisions for a Human

O incremento anterior teve conserto real em `5459e8c`, mas a rodada não passa.
Documentation subiu de B para A e Type Safety caiu de A para B. Code Quality (Zen),
Error Handling, Test Coverage e Overall permaneceram em B. A revisão para neste delta
com R15 registrado. Decidir a continuidade depois da regressão e integrar o PR cabe ao mantenedor.

## Evidências reproduzíveis

- No HEAD revisado, execute a sonda abaixo com `--expect`. A saída tem
  `reused=silêncio:1,silêncio:1` e `short=silêncio:0:1 numeric=silêncio:0:1 braced=silêncio:0:1`.
  O rc é 1. Para os pares, a ordem é contínua e retomada. Para as variantes de
  origem, os dígitos indicam offset no fim e presença de `errors.log`, nessa ordem.
- Para a comparação extraia o hook da base e da 0.4.0 em uma pasta temporária:
  `git show c2c0c8c394eccfbde1e91039306886f7955844dd:plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py`
  e `git show fe38d1f:plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py`. Com `--script "$base"` e sem `--expect`, a
  base imprime `reused=codereview:1,codereview:1` e `short`, `numeric` e `braced`
  iguais a `codereview:1:0`. Com `--old-script "$base"` e o hook atual para o segundo
  Stop, a sonda imprime `older=graphify:1 newer=graphify:1`. Com
  `--old-script "$legado"`, imprime `older=silêncio:1 newer=graphify:1`.
  O dígito nesses dois controles confirma o consumo do slash.
- Para repetir o pré-scan, em Bash, use
  `git -c diff.noprefix=false -P diff c2c0c8c394eccfbde1e91039306886f7955844dd...9ddaaab25ab27f0e7f6b0230738e1c5cb517b903 --unified=0 -- . ':(exclude)**/checkpoint-notas.md' | bash "$HOME/.agents/skills/codereview/scripts/scan_secrets.sh"`.
- Os 16 Checks da rodada são I1, F1 e R1–R14. Da raiz, execute em Bash cada comando
  antes de `→` nas células do checkpoint em `9ddaaab25ab27f0e7f6b0230738e1c5cb517b903`, com o ambiente
  Git do runner. Exija rc 0 e igualdade do stdout após normalizar só espaços em
  branco. A execução de F1 dentro de R14 produziu um teste com as três variantes.
- O comando da sonda é `env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -c "$(sed -n '/^~~~python$/,/^~~~$/{ /^~~~/!p; }' docs/handoffs/20261125-retrofit-watch-atribuicao/40-review-r24.md)"`. Para repetir os cinco testes novos
  em `9ddaaab25ab27f0e7f6b0230738e1c5cb517b903`, use:

~~~bash
env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -m unittest -v \
  test_retrofit_watch.StopTest.test_active_call_failure_without_message_origin \
  test_retrofit_watch.StopTest.test_retirement_requires_known_origin_after_multiple_advances \
  test_retrofit_watch.StopTest.test_confirmed_external_call_expires_only_older_slash \
  test_retrofit_watch.StopTest.test_resumed_attribution_recovers_call_identity_from_old_state \
  test_retrofit_watch.StopTest.test_resumed_slash_keeps_prior_call_order_from_old_state
~~~

### Sonda de R15

~~~python
import argparse
import json
from pathlib import Path

from test_retrofit_watch import SCRIPT, StopTest, identified_load, skill_typed, tool


def target(test, output):
    if output is None:
        return "silêncio"
    text = test.context_of(output)
    for name in ("codereview", "graphify"):
        if f"`/retrofit-skill:retrofit-skill {name}`" in text:
            return name
    raise ValueError(text)


def test_call(case, resumed, script):
    test = StopTest()
    test.setUp()
    try:
        ours, _ = test.identified_loads("msg_2")
        other_id = "toolu_1" if case == "reused" else "toolu_other"
        prior = identified_load("irrelevante", test.w.other_skill, "msg_old", other_id)
        if case == "missing_message":
            ours[0]["message"].pop("id")
        error = (ours if case in ("active", "missing_message") else prior)[1:2]
        error[0]["message"]["content"][0]["is_error"] = True
        if case in ("reused", "different"):
            sentinel = identified_load("irrelevante", test.w.other_skill, "msg_keep", "toolu_keep")
            test.write(prior[:1], sentinel[:1], compact=True)
        test.write(ours[:1], compact=True)
        if resumed:
            out, state = test.checked_stop(script=script, mode="plan")
            assert out is None and state["current"] == "full:codereview", state
            if case == "reused":
                assert other_id in state["skill_call_history"] and state["current_origin"] is None, state
        test.write(error, tool(error=True), compact=True)
        out, after = test.checked_stop(script=script)
        skill = after["skills"]["full:codereview"]
        expected_history = target(test, out) == "codereview"
        if expected_history:
            invariant = after["current"] == "full:codereview" and not after["attribution_closed"]
            invariant &= skill["reviews"] == 1
        else:
            invariant = after["current"] is None and after["attribution_closed"]
            invariant &= (skill["work"], skill["friction"], skill["reviews"]) == (0, 0, 0)
        return f"{target(test, out)}:{int(invariant)}"
    finally:
        test.tearDown()


def test_origin(origin, script):
    test = StopTest()
    test.setUp()
    try:
        ours, _ = test.identified_loads("msg_2")
        test.write(ours, compact=True)
        _, state = test.checked_stop(script=script, mode="plan")
        state.pop("current_call", None)
        if origin != "intact":
            state["current_origin"] = {"short": ["msg_1"], "numeric": 42, "braced": {"message": "msg_1"}}[origin]
        path = test.w.data / "sessions/s1.json"
        path.write_text(json.dumps(state), encoding="utf-8")
        test.write(*(tool() for _ in range(6)), compact=True)
        out = test.run_hook(script=script)
        after = json.loads(path.read_bytes())
        errors = test.w.data / "errors.log"
        return f"{target(test, out)}:{int(after['offset'] == test.w.transcript.stat().st_size)}:{int(errors.exists())}"
    finally:
        test.tearDown()


def test_slash(case, old_script, script):
    test = StopTest()
    test.setUp()
    try:
        ours, external = test.identified_loads("msg_2")
        slash = skill_typed("graphify", test.w.graphify)
        external[0]["message"]["content"][0]["input"]["skill"] = "brainstorming"
        groups = (slash[:1], external[:2]) if case == "older" else (external[:2], slash[:1])
        test.write(ours, *groups, compact=True)
        if old_script:
            out, state = test.checked_stop(script=old_script, mode="plan")
            assert out is None and state["current"] == "full:codereview"
        test.write(external[2:], slash[1:], tool(error=True), compact=True)
        out, state = test.checked_stop(script=script)
        return f"{target(test, out)}:{int(state['pending_slash'] is None)}"
    finally:
        test.tearDown()


parser = argparse.ArgumentParser()
parser.add_argument("--script", type=Path, default=SCRIPT)
parser.add_argument("--old-script", type=Path)
parser.add_argument("--expect", action="store_true")
args = parser.parse_args()
expected = {
    "active": "silêncio:1,silêncio:1",
    "missing_message": "silêncio:1,silêncio:1",
    "different": "codereview:1,codereview:1",
    "reused": "codereview:1,codereview:1",
    "intact": "codereview:1:0",
    "short": "codereview:1:0",
    "numeric": "codereview:1:0",
    "braced": "codereview:1:0",
}
observed = {
    case: ",".join(test_call(case, resumed, args.script) for resumed in (False, True))
    for case in ("active", "missing_message", "different", "reused")
}
observed.update({case: test_origin(case, args.script) for case in ("intact", "short", "numeric", "braced")})
for case, result in observed.items():
    print(f"{case}={result}")
if not args.expect:
    for case in ("older", "newer"):
        print(f"{case}={test_slash(case, args.old_script, args.script)}")
elif observed != expected:
    raise SystemExit(1)
~~~

### Recommended Actions

**Must Fix (CRITICAL)**

_Nenhum._

**Should Fix (HIGH)**

_Nenhum._

**Consider Fixing (MEDIUM/LOW)**

- Fechar R15 preservando a distinção entre ID único e ID disputado e retomando
  o trabalho mesmo quando a origem opcional não puder ser usada.
- Triar compatibilidade do snapshot intermediário sem estender a promessa da 0.4.0.

### Cost footprint

_Codereview 2.27.38 do caminho solicitado, sem usar o cache Claude 2.30.2. Dois agentes
gpt-6.1-terra na documentação, 28 chamadas e cinco leituras integrais informadas.
Diffs recuperados quando truncados, com código Python e Bucket A em linha.
Nenhum relançamento. Custo monetário não medido._
