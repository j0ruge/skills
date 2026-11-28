---
missao: 20261125-retrofit-watch-atribuicao
fase: REVIEW
rodada: 25
status: done
sessao: 01a21fd1-e1fa-7be2-b02a-e393370df730
data: 2026-11-27 22:47
gate: 'Em 4794fd4d63d95bb1911540da725720f58ac5ef9e, árvore inicial limpa. env -u GIT_DIR -u GIT_WORK_TREE PYTHONDONTWRITEBYTECODE=1 bash -c ''source .sdd/config.sh && eval "$TEST_CMD"'' → rc 0. Adaptadores e catálogo válidos, 154 testes da loja (3 pulados), 126 do hook, versão 0.4.1 validada. Os 17 Checks existentes devolveram rc 0 e stdout esperado. A sonda de R16 ficou vermelha. Type Safety subiu de B para A. Code Quality (Zen), Error Handling e Test Coverage seguem em B. O gate não passou.'
reviewed_head: 4794fd4d63d95bb1911540da725720f58ac5ef9e
---

# Review — rodada r25 — Atribuição da retrofit-watch por mensagem

## TL;DR

R15 fechou os dois achados funcionais de r24 em `1dd3224`. A r25 reproduziu uma regressão no
limite da janela de correlação. Uma chamada nova da monitorada falha, mas o Stop pede retro
como se ela tivesse carregado. R16 registra o caso. Nota geral B, sem mudanças de código.

## Nota da rodada

A skill `/codereview:codereview` foi aplicada com
`base=9ddaaab25ab27f0e7f6b0230738e1c5cb517b903` até `4794fd4d63d95bb1911540da725720f58ac5ef9e`.
Seis commits, dez arquivos no recorte efetivamente lido, 452 linhas adicionadas e 22 removidas.
O diário append-only foi excluído da leitura e da varredura. O recorte contém um módulo, seu
teste e oito documentos. O handoff de QA orientou a repetição da F1, que continuou silenciosa nas
três variantes. A análise foi em linha.

### Secrets Detection

| Ocorrências | Scanners | Arquivos | Linhas adicionadas | Status |
|---|---|---|---|---|
| 0 | regex e gitleaks | 10 | 452 | PASS |

Sem erros no pré-scan. O delta não muda permissões, leitura sob trava ou gravação atômica.
Não alterou a interface do hook. A validação da origem tem no máximo dois IDs e o teste de
presença no mapa não amplia a janela nem o custo de replay.

### Cobertura e sincronização

| Código | Sensor | Resultado |
|---|---|---|
| `retrofit_watch.py` | `test_retrofit_watch.py`, dois testes novos em R15 | 1 de 1 módulo com testes atualizados. Controle verde e quatro mutações pontuais em cópia descartável ficaram vermelhas. |
| Limite da janela e falha própria | Sonda de R16 com subprocessos do Stop e estado real | Os testes de R15 cobrem erro único e ID disputado com janela disponível. O teste de estouro não combina o limite com erro da carga nova. |
| Regra pública | Guia, README, CHANGELOG e SKILL | A prosa separa ID de chamada de ID de mensagem e não pede reativação da janela. O comportamento que diverge da regra de falha própria é o achado funcional 1. |

### Varredura de símbolos

Bucket A em linha. O Python não ganhou nem perdeu símbolos de produção. Os dois métodos novos
são descobertos e executados pelo `unittest`. Nenhum símbolo órfão. Bucket B não solicitado.

### Overall Grade

| Criterion | Grade | Rationale |
|-----------|-------|-----------|
| Code Quality (Zen) | B | A presença no mapa de mensagens virou condição para provar a identidade da chamada, embora o mapa possa estar desativado sem disputa observada. |
| Type Safety | A | A abertura valida tipo, tamanho e os dois IDs da origem antes de indexar. A sonda com origem truncada, numérica ou em objeto retomou sem erro. |
| Error Handling | B | Depois de cada um dos dois limites, o erro da própria carga deixa crédito aberto e produz um pedido indevido. |
| Security | A | O pré-scan não encontrou credenciais e o delta não muda a fronteira de acesso ao estado nem a sincronização. |
| Performance | A | O delta valida dois IDs e consulta o mapa existente, sem ampliar a janela de correlação. |
| Test Coverage | B | As duas regressões de R15 e os 17 Checks passaram, mas nenhum combinava o estouro com a falha da chamada nova. |
| Documentation | A | Guia, SKILL, README e CHANGELOG distinguem falha própria de ID disputado e não prometem correlacionar mensagens além da janela. |
| **Overall** | **B** | R15 fechou os dois achados anteriores e Type Safety subiu. R16 fica pendente por uma regressão funcional reproduzida nos dois limites. |

## Achados da rodada

| # | Severidade | Achado | Onde |
|---|---|---|---|
| 1 | MEDIUM | Após esgotar a janela, um erro da própria carga explícita nova mantém o crédito e gera pedido de retro indevido. | `plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py:767` |

Com 65 mensagens distintas pendentes ou 1.025 IDs pendentes na mesma mensagem, a janela já
está desativada quando a chamada de ID novo chega. `_skill_origin` não a registra no mapa.
O novo teste de presença descarta o ID antes de `invocation`, que ainda ativa a monitorada
pelo nome. Quando chega o erro com esse mesmo ID, falta `current_call` para fechar o crédito.
Em leitura contínua e em dois Stops, a base silenciou e gravou o encerramento. O HEAD pediu
`codereview`, persistiu a atribuição aberta e registrou uma revisão. Sem `message.id`, o
resultado indevido se repete. A correção deve distinguir janela desativada de disputa observada
sem reabilitar a correlação por mensagem nem guardar um histórico ilimitado.

## Incrementos de conserto (R<n>)

| R<n> | Achado | Check escrito no checkpoint |
|---|---|---|
| R16 | 1 | `env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -c "$(sed -n '/^~~~python$/,/^~~~$/{ /^~~~/!p; }' docs/handoffs/20261125-retrofit-watch-atribuicao/40-review-r25.md)" --expect && env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B e2e/test_retrofit_watch_stop.py && if o=$(env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -m unittest -q test_retrofit_watch.StopTest.test_active_skill_failure_after_correlation_overflow 2>&1); then [[ "$o" == *"Ran 1 test"* && "$o" == *"OK" ]] && printf 'regressao=1\n'; else printf '%s\n' "$o" >&2; exit 1; fi` → `at_limit=silêncio:1:0,silêncio:1:0 after_limit=silêncio:1:0,silêncio:1:0 no_message=silêncio:1:0,silêncio:1:0 after_id_limit=silêncio:1:0,silêncio:1:0 success=codereview:0:1,codereview:0:1 reused=codereview:0:1,codereview:0:1 linked=silêncio missing=silêncio empty=silêncio regressao=1` |

## O que virou incremento

- Achado 1 → R16. Exige silêncio e encerramento na falha própria, com controle de sucesso,
  reuso observado, retomada e os dois limites reais. O Check também exige a F1 e um teste durável.
- R15 (r24, achados 1–2) foi fechado em `1dd3224`. A sonda confirmou silêncio para a falha
  própria com ou sem ID da mensagem, retro para os IDs distinto e disputado, e avanço do
  offset sem `errors.log` nas origens inválidas. Passaram os dois testes duráveis e a F1.

## O que foi refutado

- A falha não ocorre simplesmente porque há muitas mensagens. Com 64 pendências, a chamada
  monitorada é reconhecida e poda as anteriores. A janela fica ativa e ambos os SHAs silenciam
  após o erro. Sem erro, ambos os SHAs emitem a retro mesmo com a janela esgotada.
- Reverter a verificação de disputa não satisfaz R16. Com reuso observado depois de abrir a
  carga, a base fechava indevidamente o crédito e o HEAD o preserva. Na janela ativa, retirar
  a restrição ao ID disputado ou a revogação do ID fez o teste de R15 falhar.

## Achados fora de escopo

Nenhum achado novo. O snapshot intermediário sem ordem do slash permanece no item de
`TODO.md` já registrado pela r24. R15 não tocou a regra de precedência nem ampliou a migração.

## Pendências / Decisions for a Human

Nenhuma pendência nova. A melhora em Type Safety veio de conserto real. O gate continua abaixo
de A em três critérios técnicos e R16 está pendente para EXEC. A integração do PR continua com
o mantenedor.

## Evidências reproduzíveis

- Em `4794fd4d63d95bb1911540da725720f58ac5ef9e`, da raiz, execute os comandos de I1, F1 e
  R1–R15 antes de `→` no checkpoint em Bash. Cada célula saiu com rc 0 e stdout esperado após
  normalizar apenas espaços em branco. I1 imprimiu `1 0 1 0 0 1` e F1 retornou
  `linked=silêncio missing=silêncio empty=silêncio`. A suíte do campo `gate` é a da configuração,
  isolada das variáveis do Git privado conforme a QA. As três provas nativas ficaram puladas.
- No mesmo HEAD, o controle dos dois métodos novos de `StopTest` deu rc 0 com dois testes.
  Separadamente, em cópia temporária, deixar passar ID disputado, não revogar o ID ao
  reaparecer, não validar os IDs da origem e não limpar a origem inválida produziram,
  respectivamente, 4, 2, 2 e 7 falhas de asserção nos testes de R15.
- A sonda abaixo usa o hook do HEAD por padrão. Rode o primeiro comando da célula R16 até
  `--expect`. O rc é 1 e `after_limit`, `no_message` e `after_id_limit` retornam
  `codereview:0:1,codereview:0:1`. Cada par é leitura contínua e retomada. Os campos são
  alvo emitido, estado de encerramento e total de revisões. O harness exige consumo completo
  do transcript e ausência de `errors.log`.
- Para comparar, extraia o hook da base com `git show 9ddaaab25ab27f0e7f6b0230738e1c5cb517b903:plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py > "$arquivo"`
  em pasta temporária. Rode o mesmo comando da sonda com `--script "$arquivo"` no lugar de
  `--expect`. A base imprime `silêncio:1:0,silêncio:1:0` nos três casos. Também silencia
  indevidamente em `reused`, o controle que não pode regredir com a correção.
- Para repetir o pré-scan, use `git -c diff.noprefix=false -P diff 9ddaaab25ab27f0e7f6b0230738e1c5cb517b903...4794fd4d63d95bb1911540da725720f58ac5ef9e --unified=0 -- . ':(exclude)**/checkpoint-notas.md' | bash "$HOME/.agents/skills/codereview/scripts/scan_secrets.sh"`.

### Sonda de R16

~~~python
import argparse
from pathlib import Path

from test_retrofit_watch import SCRIPT, StopTest, identified_load, rw, tool


def measure(case, resumed, script):
    test = StopTest()
    test.setUp()
    try:
        size = rw.MAX_SKILL_MESSAGES + int(case != "at_limit")
        if case == "after_id_limit":
            size = rw.MAX_SKILL_CALL_IDS + 1
        pending = [
            identified_load("irrelevante", test.w.other_skill, "msg_only" if case == "after_id_limit" else f"msg_{i}", f"toolu_other_{i}")[0]
            for i in range(size)
        ]
        call, result, _ = identified_load(
            "codereview:coderabbit-pr", test.w.mkt_skill, "msg_fresh", "toolu_fresh"
        )
        if case == "no_message":
            call["message"].pop("id")
        result["message"]["content"][0]["is_error"] = case != "success"
        test.write(pending, [call], compact=True)
        if resumed:
            out, state = test.checked_stop(script=script, mode="plan")
            assert out is None and state["current"] == "full:codereview", state
            assert state["skill_correlation_lost"] == (case != "at_limit"), case
            if case != "at_limit":
                assert not state["skill_calls"], case
        if case == "reused":
            duplicate, _, _ = identified_load(
                "irrelevante", test.w.other_skill, "msg_reused", "toolu_fresh"
            )
            test.write([duplicate], compact=True)
        test.write([result], tool(error=True), compact=True)
        out, state = test.checked_stop(script=script)
        assert state["skill_correlation_lost"] == (case != "at_limit"), case
        if case != "at_limit":
            assert not state["skill_calls"], case
        if out is not None:
            assert "`/retrofit-skill:retrofit-skill codereview`" in test.context_of(out), out
        entry = state["skills"]["full:codereview"]
        closed = state["attribution_closed"]
        if closed:
            assert state["current"] is None and entry["work"] == 0, state
        else:
            assert state["current"] == "full:codereview", state
        return f"{'codereview' if out else 'silêncio'}:{int(closed)}:{entry['reviews']}"
    finally:
        test.tearDown()


parser = argparse.ArgumentParser()
parser.add_argument("--script", type=Path, default=SCRIPT)
parser.add_argument("--expect", action="store_true")
args = parser.parse_args()
closed = "silêncio:1:0,silêncio:1:0"
open_attribution = "codereview:0:1,codereview:0:1"
expected = dict(at_limit=closed, after_limit=closed, no_message=closed, after_id_limit=closed,
                success=open_attribution, reused=open_attribution)
observed = {
    case: ",".join(measure(case, resumed, args.script) for resumed in (False, True))
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

- Fechar R16 sem relaxar o tratamento do ID disputado, reativar a janela ou ampliar seus limites.

### Cost footprint

_Codereview 2.27.38 do caminho solicitado. Cache Claude 2.30.2 identificado e não aplicado.
Python, documentação e Bucket A analisados em linha. Modelo de roteamento da skill indisponível.
Nenhum subagente nem relançamento. Custo monetário não medido._
