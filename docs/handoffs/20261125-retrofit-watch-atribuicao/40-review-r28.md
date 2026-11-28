---
missao: 20261125-retrofit-watch-atribuicao
fase: REVIEW
rodada: 28
status: done
sessao: 01a22000-f10c-7172-90d2-7a86a0341a1a
data: 2026-11-27 23:40
gate: "TEST_CMD em 0bb2e84c8076fcf91609acf414deabeeff48eec0 deu rc 0 em 61,04 s. Loja 154 testes (3 pulados), hook 132, adaptadores, catálogo e versão 0.4.1 válidos. Árvore limpa antes da revisão. Os 20 Checks concluídos passaram. R19 reproduz regressão de retomada no HEAD, ausente na base. Type Safety, Error Handling e Test Coverage em B."
reviewed_head: 0bb2e84c8076fcf91609acf414deabeeff48eec0
---

# Review — rodada r28 — Atribuição da retrofit-watch por mensagem

## TL;DR

O delta `5260a1a…0bb2e84` fecha os dois achados de R18. A suíte e os 20 Checks concluídos passaram.
Reproduzi uma regressão nova de retomada com estado JSON válido e um item aposentado inválido. Ela virou R19.
A nota geral é B. Nenhum código foi alterado nesta rodada.

## Nota da rodada

Executei `/codereview:codereview base=5260a1a69942652c432adbc30e47ae9e8a8741bc` no fluxo nativo do Codex. O argumento delimitou o delta até `0bb2e84c8076fcf91609acf414deabeeff48eec0`. São seis commits e nove arquivos analisados, com 444 linhas adicionadas e 33 removidas. As notas históricas ficaram fora da leitura e da contagem.

### Secrets Detection

| Achados | Scanners | Arquivos | Linhas adicionadas | Status |
|---|---|---|---|---|
| 0 | regex e gitleaks | 9 | 444 | PASS |

Nenhum erro do pré-scan.

### Qualidade, cobertura e sincronização

| Área | Evidência |
|---|---|
| Legibilidade e simplicidade | Um mapa separado para a transição e outro para observações posteriores. O fluxo não restaura correlação por mensagem. |
| Erros e tipos | O default por tipo cobre os dois mapas. A conversão nova de chaves falha com dois tipos de elemento inválido no histórico de aposentados. |
| Custo e superfície | Sem mudança de subprocesso, acesso, travas, interface visual ou leitura de rede. O caminho normal mantém consulta por ID e não relê o prefixo. |
| Cobertura | Um módulo Python alterado, com três regressões descobertas e executadas. Também executei a especificação F1 do QA. |
| Prosa | O guia e a documentação de release acompanham a separação dos registros. Os fatos do handoff confrontados com as sondas e os Checks nesta rodada passaram. As 14 mutações permanecem evidência de EXEC, sem reexecução pela REVIEW. |

### Varredura de símbolos

Bucket A em linha. AST não mostrou função ou classe adicionada ou removida no módulo. Os três métodos novos são descobertos por `unittest`, e o campo `overflow_skill_calls` é inicializado, consultado e importado na reconstrução legada. Ruff passou com `F401,F811,F841` nos dois arquivos Python. Nenhum símbolo órfão no delta e Bucket B não solicitado.

### Overall Grade

| Criterion | Grade | Rationale |
|-----------|-------|-----------|
| Code Quality (Zen) | A | O snapshot separado protege os IDs ainda retidos e a reconstrução comprovada. As duas sondas da r27 fecharam com o commit funcional de R18. |
| Type Safety | B | O novo snapshot presume que os elementos do campo opcional de aposentados podem ser usados como chaves do dicionário, sem validar os itens carregados do JSON. |
| Error Handling | B | Um objeto ou uma lista entre os aposentados faz dois Stops repetirem TypeError, sem avançar o offset. A base consome o delta nas duas variantes. |
| Security | A | O pré-scan não encontrou credenciais. O delta não muda destinos, permissões, travas ou fronteiras de acesso. |
| Performance | A | O snapshot criado pelo hook tem teto de 2.049 entradas e é feito na transição. A consulta por ID não acrescenta replay aos Stops normais. |
| Test Coverage | B | Os três testes novos passam e cobrem a janela, a reconstrução e os registros diretos inválidos. Nenhum deles insere um valor que não pode ser chave de dicionário entre os aposentados ao construir o snapshot. |
| Documentation | A | Guia, nota de versão, README e skill distinguem os dois registros e não os tratam como prova de origem de metadados. |
| **Overall** | **B** | R18 fecha os casos da r27, mas resta uma regressão delimitada de retomada em estado opcional malformado. |

## Achados da rodada

| # | Severidade | Achado | Onde |
|---|---|---|---|
| 1 | MEDIUM | Um item inválido na lista persistida de IDs aposentados impede o Stop de cruzar o limite de correlação e retomar a sessão. | `plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py:558–559` |

O novo `dict.fromkeys` recebe, além das chaves de dois mapas, todos os itens da lista aposentada. Na sonda, um Stop anterior deixou a monitorada ativa e um ID válido aposentado. Antes do próximo Stop, acrescentei um objeto ou uma lista à lista aposentada no arquivo de sessão. O JSON continuou válido. A chamada seguinte excedeu o limite real de 64 mensagens. No HEAD, ambas as variantes levantaram `TypeError` em dois Stops, ficaram sem retro e repetiram o mesmo offset. A base avançou, marcou a perda da janela e emitiu retro nas duas variantes. Sem o item inválido, o HEAD também avançou e preservou no snapshot o ID aposentado válido.

O efeito exige estado local malformado e a transição da janela. As fixtures normais não produzem esse elemento. A gravidade é MEDIUM por esse alcance, mas a sessão que o encontra fica presa até mudar o estado ou o código.

## Incrementos de conserto (R<n>)

| R<n> | Achado | Check escrito no checkpoint |
|---|---|---|
| R19 | 1 | `env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -c "$(sed -n '/^~~~python$/,/^~~~$/{ /^~~~/!p; }' docs/handoffs/20261125-retrofit-watch-atribuicao/40-review-r28.md)" --expect && env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B e2e/test_retrofit_watch_stop.py && if o=$(env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -m unittest -q test_retrofit_watch.StopTest.test_invalid_retired_id_does_not_break_correlation_overflow 2>&1); then [[ "$o" == *"Ran 1 test"* && "$o" == *"OK" ]] && printf 'regressao=1\n'; else printf '%s\n' "$o" >&2; exit 1; fi` → `valid=codereview:1:1:0 invalid_object=codereview:1:1:0 invalid_list=codereview:1:1:0 linked=silêncio missing=silêncio empty=silêncio regressao=1` |

## O que virou incremento

- A linha escrita no checkpoint foi

  ~~~text
  | R19 | Retomar Stop quando a janela se perde com um ID aposentado malformado, sem descartar IDs válidos (r28, achado 1) | `env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -c "$(sed -n '/^~~~python$/,/^~~~$/{ /^~~~/!p; }' docs/handoffs/20261125-retrofit-watch-atribuicao/40-review-r28.md)" --expect && env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B e2e/test_retrofit_watch_stop.py && if o=$(env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -m unittest -q test_retrofit_watch.StopTest.test_invalid_retired_id_does_not_break_correlation_overflow 2>&1); then [[ "$o" == *"Ran 1 test"* && "$o" == *"OK" ]] && printf 'regressao=1\n'; else printf '%s\n' "$o" >&2; exit 1; fi` → `valid=codereview:1:1:0 invalid_object=codereview:1:1:0 invalid_list=codereview:1:1:0 linked=silêncio missing=silêncio empty=silêncio regressao=1` | pending | — |
  ~~~

- Os achados 1 e 2 da r27 foram fechados por `7b1da02`. O Check de R18 passa integralmente no HEAD da revisão. Os 12 cenários de reuso ainda retido preservam a retro, os três controles de falha própria fecham a atribuição e os quatro casos de retomada avançam sem erro. O terceiro teste do incremento também confirma o teto da transição e exclui o ID já descartado na ordem de chegada.

## O que foi refutado

- A correção não desativa toda prova de erro próprio após o limite. A sonda da r27 voltou `own_error=silêncio:1:0` nos três cortes, enquanto `different=codereview:0:1` nos mesmos cortes.
- O default novo não resolve a escrita apagando toda a atribuição. Os quatro casos da r27 voltaram `codereview:1:0`, com offset no fim e nenhum `TypeError`. A falha nova exige um elemento inválido em `retired_skill_calls`, não um dos dois mapas inválidos da r27.
- Os dois sintomas da r27 não são regressões abertas. O Check de R18 e as três regressões permanentes passaram no mesmo HEAD revisado. A jornada F1 continuou silenciosa com ID válido, ausente e vazio.
- O encerramento com ID aposentado reutilizado pela própria chamada que dispara o limite não é introduzido pelo snapshot. A variante sem atingir o limite fecha indevidamente do mesmo modo, em ambos os commits. A causa vem antes da transição e já está no item de reuso da seção seguinte. O controle com ID novo e falha própria produz o mesmo silêncio, mas nesse controle o encerramento é esperado.

## Achados fora de escopo

O teste de reuso de um ID aposentado antes e durante a transição é mais uma manifestação do item aberto **ID de chamada reaproveitado entre mensagens passa por vínculo novo** em `TODO.md`. O ID da primeira chamada já estava na lista aposentada. `_skill_origin`, sem mudança no delta, retira o ID dessa lista e o aceita como vínculo novo. Um erro atrasado da chamada anterior então fecha a monitorada. Reproduzi na base e no HEAD, em leitura contínua e em dois Stops. Não é novo R<n>. O item já foi registrado nesta mesma missão e o molde não duplica recorrências da própria missão de origem.

## Pendências / Decisions for a Human

Nenhuma decisão nova. Code Quality (Zen) subiu de B para A com o conserto em `7b1da02`. Não houve queda de nota. Type Safety, Error Handling e Test Coverage continuam em B pelo achado de retomada. R19 fica pendente para EXEC. Não houve ação no PR.

## Evidências reproduzíveis

Comandos executados no HEAD `0bb2e84c8076fcf91609acf414deabeeff48eec0`, salvo onde a base é indicada.

- `env -u GIT_DIR -u GIT_WORK_TREE PYTHONDONTWRITEBYTECODE=1 bash -c 'source .sdd/config.sh && /usr/bin/time -f "elapsed=%es" bash -c "$TEST_CMD"'` deu rc 0 em 61,04 s. Adaptadores, catálogo e versão 0.4.1 válidos. A loja executou 154 testes com três pulados, e o hook 132 sem falhas. As três provas nativas e o host Claude Code não foram exercitados.
- Executei em Bash as 20 células `done` de `checkpoint.md`, sem `GIT_DIR` e `GIT_WORK_TREE`. Comparei cada rc e stdout com o esperado, sem distinguir espaços entre tokens. Todos passaram. I1 retornou `1 0 1 0 0 1` e F1 `linked=silêncio missing=silêncio empty=silêncio`.
- As três regressões de R18 passaram com `env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -m unittest -v test_retrofit_watch.StopTest.test_reused_call_across_correlation_overflow_does_not_close_attribution test_retrofit_watch.StopTest.test_transition_history_keeps_retained_ids_only_and_stays_bounded test_retrofit_watch.StopTest.test_invalid_direct_call_history_does_not_break_stop`. O mesmo ambiente com `python3 -B -m unittest -q test_auto_docs.ReleaseTest` executou quatro testes e deu rc 0.
- A parte inicial do Check de R19, `env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -c "$(sed -n '/^~~~python$/,/^~~~$/{ /^~~~/!p; }' docs/handoffs/20261125-retrofit-watch-atribuicao/40-review-r28.md)" --expect`, deu rc 1 no HEAD. Para comparar, extraia o script em Bash com `git show 5260a1a69942652c432adbc30e47ae9e8a8741bc:plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py > "$arquivo"`, onde `$arquivo` é um caminho novo sob `mktemp -d`. Use a mesma sonda com `--expect --script "$arquivo"`. Na base deu rc 0, com `valid=codereview:1:1:0 invalid_object=codereview:1:1:0 invalid_list=codereview:1:1:0`.
- Rode a mesma sonda com `--retired-reuse`, e depois com `--retired-reuse --script "$arquivo"`. A saída é idêntica nas duas revisões. Cada par mede leitura contínua e dois Stops. Cada valor indica alvo da retro, encerramento e perda da janela.
- Para o pré-scan, executei `git -P diff 5260a1a69942652c432adbc30e47ae9e8a8741bc...0bb2e84c8076fcf91609acf414deabeeff48eec0 --unified=0 -- . ':(exclude)**/checkpoint-notas.md' | bash /home/joruge/.agents/skills/codereview/scripts/scan_secrets.sh`. Scanners regex e gitleaks retornaram zero achados e zero erros.

Na sonda de R19, os campos medem alvo, offset no fim, perda persistida da janela e número de `TypeError` em até dois Stops. A sonda também exige que um snapshot existente após a transição conserve o ID aposentado válido.

~~~text
HEAD  valid=codereview:1:1:0 invalid_object=silêncio:0:0:2 invalid_list=silêncio:0:0:2
base  valid=codereview:1:1:0 invalid_object=codereview:1:1:0 invalid_list=codereview:1:1:0
~~~

~~~text
before=silêncio:1:0,silêncio:1:0
trigger=silêncio:1:1,silêncio:1:1
fresh=silêncio:1:1,silêncio:1:1
~~~

### Sonda de R19 e controle do reuso fora do delta

~~~python
import argparse
import json
from pathlib import Path

from test_retrofit_watch import SCRIPT, StopTest, identified_load, rw, tool


def fail(load):
    result = load[1]
    result["message"]["content"][0]["is_error"] = True
    return [result]


def verdict(test, out, state):
    if out:
        assert "`/retrofit-skill:retrofit-skill codereview`" in test.context_of(out), out
    return "codereview" if out else "silêncio"


def measure(invalid_id, script):
    test = StopTest()
    test.setUp()
    try:
        old = identified_load("irrelevante", test.w.other_skill, "msg_old", "toolu_old")
        active = identified_load("codereview:coderabbit-pr", test.w.mkt_skill, "msg_active", "toolu_active")
        test.write(old[:1], active, compact=True)
        for i in range(rw.MAX_SKILL_MESSAGES - 1):
            pending = identified_load("irrelevante", test.w.other_skill, f"msg_{i}", f"toolu_{i}")
            test.write(pending[:1], compact=True)
        out, state = test.checked_stop(mode="plan", script=script)
        assert out is None and not state["skill_correlation_lost"]
        assert state["retired_skill_calls"] == ["toolu_old"], state["retired_skill_calls"]
        state_path = test.w.data / "sessions/s1.json"
        if invalid_id is not None:
            state["retired_skill_calls"].append(invalid_id)
            state_path.write_text(json.dumps(state), encoding="utf-8")
        trigger = identified_load("irrelevante", test.w.other_skill, "msg_trigger", "toolu_trigger")
        test.write(trigger[:1], tool(error=True), compact=True)
        out = test.run_hook(script=script)
        if out is None:
            # O segundo Stop mostra se a sessão tenta consumir o mesmo trecho outra vez.
            out = test.run_hook(script=script)
        state = json.loads(state_path.read_bytes())
        errors = test.w.data / "errors.log"
        count = errors.read_text(encoding="utf-8").count("TypeError: unhashable type") if errors.exists() else 0
        if "overflow_skill_calls" in state and state["skill_correlation_lost"]:
            assert "toolu_old" in state["overflow_skill_calls"], state["overflow_skill_calls"]
        return (f"{verdict(test, out, state)}:"
                f"{int(state['offset'] == test.w.transcript.stat().st_size)}:"
                f"{int(state['skill_correlation_lost'])}:{count}")
    finally:
        test.tearDown()


def trigger_reuse(kind, split, script):
    test = StopTest()
    test.setUp()
    try:
        old = identified_load("irrelevante", test.w.other_skill, "msg_old", "toolu_old")
        active = identified_load("codereview:coderabbit-pr", test.w.mkt_skill, "msg_same", "toolu_active")
        test.write(old[:1], active, compact=True)
        total = rw.MAX_SKILL_CALL_IDS - (2 if kind == "before" else 1)
        for i in range(total):
            pending = identified_load("irrelevante", test.w.other_skill, "msg_same", f"toolu_{i}")
            test.write(pending[:1], compact=True)
        if split:
            out, state = test.checked_stop(mode="plan", script=script)
            assert out is None and not state["skill_correlation_lost"]
            assert state["retired_skill_calls"] == ["toolu_old"]
        last_id = "toolu_fresh" if kind == "fresh" else "toolu_old"
        last = identified_load("codereview:coderabbit-pr", test.w.mkt_skill, "msg_same", last_id)
        test.write(last[:1], fail(last if kind == "fresh" else old), tool(error=True), compact=True)
        out, state = test.checked_stop(script=script)
        return f"{verdict(test, out, state)}:{int(state['attribution_closed'])}:{int(state['skill_correlation_lost'])}"
    finally:
        test.tearDown()


parser = argparse.ArgumentParser()
parser.add_argument("--script", type=Path, default=SCRIPT)
parser.add_argument("--expect", action="store_true")
parser.add_argument("--retired-reuse", action="store_true")
args = parser.parse_args()
if args.retired_reuse:
    for name in ("before", "trigger", "fresh"):
        print(f"{name}={','.join(trigger_reuse(name, split, args.script) for split in (False, True))}")
else:
    cases = (("valid", None), ("invalid_object", {"id": "toolu_invalido"}),
             ("invalid_list", ["toolu_invalido"]))
    observed = {name: measure(value, args.script) for name, value in cases}
    print(" ".join(f"{name}={verdict}" for name, verdict in observed.items()))
    if args.expect and any(verdict != "codereview:1:1:0" for verdict in observed.values()):
        raise SystemExit(1)
~~~

### Recommended Actions

**Must Fix (CRITICAL)**

_Nenhum._

**Should Fix (HIGH)**

_Nenhum._

**Consider Fixing (MEDIUM/LOW)**

- R19 — ignorar somente os itens aposentados que não são IDs válidos ao formar o snapshot. Preservar os itens válidos, o offset e a atribuição e confirmar a retomada no Check.

### Cost footprint

_Skill 2.27.38 do caminho solicitado, cache Claude 2.30.2 identificado e não usado. Código e Bucket A em linha. Dois agentes de prosa e um agente de teste de contrato, gpt-6.1-terra, sem relançamentos. Custo monetário não medido._
