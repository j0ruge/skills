---
missao: 20261125-retrofit-watch-atribuicao
fase: REVIEW
rodada: 5
status: done
sessao: 01a21d3e-8e44-7e80-92c2-3dba6af4e5bb
data: 2026-11-27 10:51
gate: 'Em 669d93d795411275d6608cf5ccc56f975663e152, árvore inicial limpa. env -u GIT_DIR -u GIT_WORK_TREE PYTHONDONTWRITEBYTECODE=1 bash -c ''source .sdd/config.sh && eval "$TEST_CMD"'' → rc 0. Adaptadores e catálogo válidos, 154 testes da loja (3 pulados), 94 testes do hook e versão 0.4.1 validada. I1, F1 e R1–R4 passaram com as saídas previstas no checkpoint. R5 reproduziu dois pedidos indevidos e a perda da marca no estado. Gate não passou. Platô em Code Quality (Zen), Error Handling e Test Coverage (B). Documentation e Overall ficaram B, tolerados pelo gate.'
reviewed_head: 669d93d795411275d6608cf5ccc56f975663e152
---

# Review — rodada r5 — Preservar a atribuição da retrofit-watch por mensagem

## TL;DR

`893c9c6` fechou as quatro divergências de R4. Os seis Checks e a suíte passaram.
O delta introduziu perda da marca de ID consumido sem origem, com retro indevida em dois modos de Stop.
Nota geral B, com as mesmas letras de r4. Gate não passou. Um achado funcional virou R5 e uma pendência
de prosa foi ao backlog. Nenhum código ou teste foi alterado.

## Escopo e medidas

Rodada DELTA de `codereview:codereview base=e405af12e689defb6987857ead4473faffd3a8e5` até `669d93d795411275d6608cf5ccc56f975663e152`.
Oito commits e 11 caminhos no inventário. O diário append-only não foi lido nem varrido.
Os dez caminhos restantes são oito de prosa, um script e seu teste. A verificação de prosa leu as
150 unidades alteradas. O script e o teste foram analisados inline no delta. O handoff de QA em
`08f09a1` documenta F1, não uma rodada de QA posterior a R4. F1 foi reexecutado nesta rodada.

### Detecção de segredos

~~~json
{"findings":[],"scanners":["regex","gitleaks"],"errors":[],"scanned":{"files":10,"added_lines":654}}
~~~

Status PASS no escopo analisado, sem achados. O delta não muda comandos executados, permissões, travas
ou destinos de escrita do hook. Não há interface gráfica neste delta.

### Verificações no HEAD revisado

| Sensor | Resultado |
|---|---|
| `env -u GIT_DIR -u GIT_WORK_TREE PYTHONDONTWRITEBYTECODE=1 bash -c 'source .sdd/config.sh && eval "$TEST_CMD"'` | rc 0. Adaptadores e catálogo válidos. Loja com 154 testes, 3 pulados. Hook com 94 testes sem falhas. Versão 0.4.1 confirmada. |
| Seis comandos de `checkpoint.md`, com Git isolado e comparação da saída integral com espaços normalizados | Seis rc 0. I1 deu `1 0 1 0 0 1`. F1 ficou em silêncio nos três casos. R1 deu `regressoes=4`. R2 deu seis alvos `graphify` e `falhas=estavel`. Todos os pares de R3 e R4 conferiram. |
| Sonda de R4 com o script exportado de `e405af1` e de `893c9c6` | A base teve quatro divergências. No fix, os pares de ordem deram `graphify,graphify` e os de reuso `codereview,silêncio`. O arquivo do hook em `893c9c6` é idêntico ao do HEAD. |
| Check R2 com `plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py --medir` | Após 10, 100 e 1.000 falhas em mensagens distintas, 0 vínculos e 325, 326, 327 bytes. Com a sonda apontada para scripts de `e405af1` e `762f440`, 0 vínculos e 292, 293, 294 bytes nesta execução. |
| Oito testes direcionados de `StopTest` e `ReleaseTest` | 8 testes, rc 0. Cobriram os dois casos de R4, falhas isoladas e com pendência antiga, saturação, migração e consistência da versão. |
| Duas mutações independentes em cópias temporárias do script | Inverter a ponta consultada para a poda da ordem e impedir o registro de IDs de falhas produziram quatro falhas de asserção cada, em `test_message_order_survives_last_failed_call` e `test_failed_call_before_activation_cannot_prove_same_message`. |
| `ruff check --no-cache --select F401,F811,F821,F841 plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py plugins/retrofit-watch/skills/retrofit-watch/tests/test_retrofit_watch.py` | rc 0. Nenhum erro de nome, import ou variável local nas regras rodadas. |

### Cobertura e documentação

`retrofit_watch.py` tem sua suíte atualizada em `test_retrofit_watch.py`, um de um arquivo de produção.
Os testes cobrem consumo sem dono, colisão com dois donos conhecidos e retomada de estado. Não
combinam a marca sem dono com a colisão seguida da poda, sequência de R5.
README, CHANGELOG e SKILL descrevem a 0.4.1, e os dois últimos registram o limite e o fallback.
A garantia histórica de R3 foi delimitada no handoff. As três provas de distribuição nativa
permaneceram puladas por configuração. Não houve smoke no Claude Code nem no Windows.

### Código morto

Varredura inline de referências nos dois arquivos Python do delta, com Ruff. Os auxiliares
e constantes novos têm consumidores no scanner ou nos testes. O nome de dados aposentado
`failed_skill_calls` é lido pela migração e usado em uma fixture legada. Nenhum símbolo novo órfão.
Dívida preexistente não varrida.

## Nota da rodada

### Overall Grade

| Criterion | Grade | Rationale |
|-----------|-------|-----------|
| Code Quality (Zen) | B | Fundir a marca de consumo sem origem com os donos conhecidos faz a primeira depender do descarte da outra mensagem. |
| Type Safety | A | IDs inválidos foram rejeitados nos testes, e os formatos de estado antigo e intermediário retomaram sem inventar uma origem na leitura do JSON. |
| Error Handling | B | A sequência de IDs ambíguos volta indevidamente a habilitar a exceção de mesma mensagem, mesmo sem troca da mensagem ativa. |
| Security | A | O delta não muda permissões, comandos nem destinos de escrita. Dois detectores varreram o escopo permitido sem achados. |
| Performance | A | Os lotes de 10, 100 e 1.000 falhas deixaram zero vínculos sem pendência e só a chamada esperada com pendência. Os dois limites foram exercitados. |
| Test Coverage | B | Os 94 testes do hook e os seis Checks passaram, mas não detectam os dois pedidos indevidos reproduzidos em R5. |
| Documentation | B | A rodada confirmou as medidas atuais e o fechamento de R4, mas resultados históricos de mutações e provas nativas não têm saída preservada nas evidências revisadas. |
| **Overall** | **B** | O fix fechou as duas lacunas de R4, mas o delta introduziu uma regressão em que o hook sugere retro quando deveria ficar em silêncio. |

## Achados da rodada

| # | Severidade | Achado | Onde |
|---|---|---|---|
| 1 | MEDIUM, atribuição | Um ID consumido sem `message.id` perde a marca ao colidir numa tentativa intermediária sem carga. O próximo uso do ID na mensagem que continua ativa comprova incorretamente a origem de uma externa. | `plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py:660–663` e `:518–523` |
| 2 | LOW, prosa | Totais históricos de mutações e resultados nativos sem saída preservada nas evidências da revisão. A lacuna reduz a auditabilidade, mas não demonstra falha de código ou de gate. | `docs/handoffs/20261125-retrofit-watch-atribuicao/20-handoff-exec.md:63` e `:94`, `docs/handoffs/20261125-retrofit-watch-atribuicao/40-review-r4.md:53` |

No achado 1, `msg_a` já está ativa. Uma chamada monitorada sem `message.id` consome `toolu_s`, e outra
carga identificada de `msg_a` confirma a atribuição de `codereview`. A marca de `toolu_s` fica sem dono
(`[]`). Uma tentativa de `msg_b` sem carga reaproveita o ID. A colisão substitui a marca sem dono por
`["msg_b"]`, e a poda imediatamente retira `msg_b` e a marca. `msg_a` nunca foi aposentada, não há
confirmação de outra mensagem e nenhum teto é atingido. Quando uma externa da própria `msg_a` volta
a usar `toolu_s`, o scanner toma o ID por novo, mantém o crédito e pede a retro de `codereview`.
A base rejeita a origem ambígua. O ID novo e o reuso direto sem a tentativa intermediária se
comportam como previsto nos dois scripts. Não é o reuso após confirmar outra mensagem, já no backlog.

### Sonda de R5

O comando da célula R5 lê o bloco Python deste relatório. Para comparar com a base ou o fix, exporte
`git show e405af1:plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py` ou `git show 893c9c6:plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py` para um script temporário e acrescente
o caminho dele como argumento. No HEAD e em `893c9c6` a sonda saiu com rc 0 e mostrou

~~~text
continua_novo=codereview
continua_repetido=silêncio
continua_intercalada=codereview
retomada_novo=codereview
retomada_repetido=silêncio
marca_apos_disputa=0
retomada_intercalada=codereview
~~~

Em `e405af1`, a mesma sonda, com o script exportado e as mesmas fixtures, devolveu

~~~text
continua_novo=codereview
continua_repetido=silêncio
continua_intercalada=silêncio
retomada_novo=codereview
retomada_repetido=silêncio
marca_apos_disputa=1
retomada_intercalada=silêncio
~~~

A sonda usa subprocessos reais do hook e exige avanço do offset até o fim do transcript e ausência de
`errors.log` em todos os Stops. No caso retomado, mede a marca após a colisão.
O Red é a divergência de saída, não o rc da sonda.

~~~python
from argparse import ArgumentParser
import json
from pathlib import Path
import re

from test_retrofit_watch import SCRIPT, StopTest, identified_load, skill_via_tool, tool


def stop(test, script):
    out = test.run_hook(script=script)
    state = json.loads((test.w.data / "sessions/s1.json").read_bytes())
    assert state["offset"] == test.w.transcript.stat().st_size
    assert not (test.w.data / "errors.log").exists()
    targets = re.findall(r"\x60/retrofit-skill:retrofit-skill ([^\x60]+)\x60", test.context_of(out)) if out else []
    assert out is None or targets, out
    return "+".join(targets) if targets else "silêncio", state


def measure(script, resume, scenario):
    test = StopTest()
    test.setUp()
    try:
        path = test.w.mkt_skill
        active = identified_load("codereview:coderabbit-pr", path, "msg_a", "toolu_a")
        anonymous = skill_via_tool("codereview:coderabbit-pr", path)
        refresh = identified_load("codereview:coderabbit-pr", path, "msg_a", "toolu_again")
        test.write(active, anonymous, refresh, compact=True)
        if resume:
            target, state = stop(test, script)
            assert target == "silêncio" and state["current_origin"] == ["msg_a", "toolu_again"]
            known = state.get("skill_call_history", state.get("skill_calls"))
            assert "toolu_s" in known
        if scenario == "intercalada":
            collision = identified_load("nao-instalada", test.w.other_skill, "msg_b", "toolu_s")
            test.write(collision[:1], compact=True)
            if resume:
                target, state = stop(test, script)
                assert target == "silêncio" and state["current_origin"] == ["msg_a", "toolu_again"]
                known = state.get("skill_call_history", state.get("skill_calls"))
                print(f"marca_apos_disputa={int('toolu_s' in known)}")
        external = identified_load("superpowers:brainstorming", test.w.other_skill, "msg_a",
                                   "toolu_new" if scenario == "novo" else "toolu_s")
        test.write(external, tool(error=True), compact=True)
        target, state = stop(test, script)
        print(f"{'retomada' if resume else 'continua'}_{scenario}={target}")
    finally:
        test.tearDown()


parser = ArgumentParser()
parser.add_argument("script", type=Path, default=SCRIPT, nargs="?")
args = parser.parse_args()
for resume in (False, True):
    for scenario in ("novo", "repetido", "intercalada"):
        measure(args.script, resume, scenario)
~~~

## Incrementos de conserto (R<n>)

| R<n> | Achado | Check escrito no checkpoint |
|---|---|---|
| R5 | Achado 1, marca de consumo sem origem apagada por colisão e poda | O Stop deve ficar em silêncio nas duas variantes com colisão intermediária, com marca persistida igual a 1 na retomada. O controle de ID novo deve pedir retro de `codereview`. |

## O que virou incremento

| ID | Incremento | Check (comando → esperado) | Status | Commit |
|---|---|---|---|---|
| R5 | Conservar a marca de consumo de ID sem origem quando uma tentativa intermediária colide e sai da janela (r5, achado 1) | `env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -c "$(sed -n '/^~~~python$/,/^~~~$/{ /^~~~/!p; }' docs/handoffs/20261125-retrofit-watch-atribuicao/40-review-r5.md)"` → `continua_novo=codereview continua_repetido=silêncio continua_intercalada=silêncio retomada_novo=codereview retomada_repetido=silêncio marca_apos_disputa=1 retomada_intercalada=silêncio` | pending | — |

- R4, achados 1 e 2 de r4, fechado em `893c9c6`. A comparação dos dois scripts confirmou as quatro diferenças
  entre o Red e o Green. Os cinco Checks anteriores continuaram verdes.
- R4, achado 3 só de prosa, fechado no handoff em `aa72f62`. A linha 55 delimita a garantia
  histórica de R3 à pendência da mesma mensagem. O registro de backlog já está marcado como resolvido.

## O que foi refutado

- **O fix não fecha os casos de R4.** O A/B reproduziu os quatro resultados incorretos em `e405af1`
  e os quatro pares previstos em `893c9c6`. Os dois sensores duráveis falharam sob mutações independentes.
- **O histórico voltaria a crescer com falhas isoladas.** O Check mediu zero vínculos em três lotes
  e os testes em disco confirmaram zero registros sem pendência e só a chamada antiga quando concorrente.
  A sonda repetida deu 292, 293 e 294 bytes na base, não os 291, 292 e 293 de r4. Isso não invalida
  a medida histórica nem prova os quatro tamanhos do cenário concorrente citados em `762f440`.
- **Não há evidência atual de uma varredura limpa.** A repetição desta rodada retornou dois detectores,
  zero achados e zero erros. Não substitui o resultado bruto da rodada r4.
- **A ausência de logs históricos pede correção funcional urgente.** Os verificadores apontaram falta
  de saída preservada para mutações de r4 e de EXEC, medidas de crescimento, a varredura de r4 e as provas
  nativas. As repetições confirmam crescimento estável, ordem e reuso nas condições medidas.
  As 12 e 58 mutações históricas não foram recontadas, nem se refez o ensaio nativo para contar comandos
  dentro do namespace. Ficou a pendência de rastreabilidade, sem elevação de severidade.

## Achados fora de escopo

- Achado 2, só de prosa, registrado em `TODO.md` na seção aberta em 2026-11-27. Sem incremento.
- Os itens já abertos sobre mensagens aposentadas e metadado externo obsoleto seguem fora deste lote.

## Pendências / Decisions for a Human

`Code Quality (Zen)`, `Error Handling` e `Test Coverage` continuam em B. A regressão é distinta
das lacunas fechadas em `893c9c6`, mas as letras não avançaram. A revisão encerra no platô,
sem certificar o gate. O mantenedor decide se retoma pelo R5. As três provas de distribuição nativa
continuam para um host com suporte ao namespace Bubblewrap.

## Boot da próxima fase

Se o mantenedor retomar a missão, execute o Check R5 em Red. Em TDD, cubra o transcript contínuo
e a retomada antes e depois da colisão com estado em disco. Exija ausência de `errors.log`,
offset completo e nenhum trabalho futuro creditado à monitorada na variante ambígua.
Mantenha o controle de ID novo e os controles de descarte e saturação de R4. Repita os seis Checks
anteriores e o `TEST_CMD` com Git isolado. Não amplie o histórico para mensagens aposentadas.

### Recommended Actions

**Must Fix (CRITICAL)**

_Nenhum._

**Should Fix (HIGH)**

_Nenhum._

**Consider Fixing (MEDIUM/LOW)**

- Se houver retomada, executar R5 sem ampliar a janela nem reintroduzir a retenção de falhas isoladas.
- Triar a rastreabilidade das medições no backlog.

**Deferred (form)**

_Nenhum._

**Outside scope (tracker)**

_Nenhum apontamento adicional dos verificadores fora das unidades editadas. Corte informado: zero._

_Custo da revisão: skill 2.30.2 instalada, chamada pela cópia 2.27.38. A instalada acrescenta a verificação de prosa, fechamento por unidade e nota de documentação separada. Dois verificadores gpt-6.1-terra, oito arquivos, 150 unidades, 98 e 22 chamadas informadas. Zero agentes por arquivo, código e varredura inline, duas mutações temporárias. Custo monetário não medido._
