---
missao: 20261125-retrofit-watch-atribuicao
fase: REVIEW
rodada: 29
status: done
sessao: 01a2200e-edfc-76f2-91bd-741d3eecefa2
data: 2026-11-27 23:55
gate: "TEST_CMD em 8a17e1d142a9344425c48bfc88b31f22d99a9226 retornou rc 0 em 68,42 s. Loja com 154 testes (3 pulados), hook com 133, adaptadores, catálogo e versão 0.4.1 válidos. Árvore limpa na revisão. Os 21 Checks passaram. R19 fechada em bdf75fa. Todos os critérios em A no delta, sem novos incrementos. Um achado reproduzido na base foi registrado no backlog."
reviewed_head: 8a17e1d142a9344425c48bfc88b31f22d99a9226
---

# Review — rodada r29 — Atribuição da retrofit-watch por mensagem

## TL;DR

R19 fechou a falha de retomada da r28. A sonda antiga e a regressão permanente distinguiram a base do HEAD.
A suíte configurada e os 21 Checks passaram. Nenhum achado no delta exige novo incremento.
Uma falha anterior ao delta, com item `null` antes da transição, foi reproduzida e entrou no backlog. Nota A no delta.

## Nota da rodada

Apliquei `/codereview:codereview base=0bb2e84c8076fcf91609acf414deabeeff48eec0` pelo fluxo nativo do Codex. O diff até `8a17e1d142a9344425c48bfc88b31f22d99a9226` contém sete commits. Revisei nove arquivos, com 331 linhas adicionadas e 20 removidas. O histórico de notas foi excluído da leitura e da varredura. Escopo Python genérico, com um módulo de produção, seu teste e sete registros ou documentos.

### Secrets Detection

| Achados | Scanners | Arquivos | Linhas adicionadas | Status |
|---|---|---|---|---|
| 0 | regex e gitleaks | 9 | 331 | PASS |

Os dois scanners retornaram sem erro.

### Qualidade, cobertura e sincronização

| Área | Evidência |
|---|---|
| Legibilidade e simplicidade | A validação da lista fica no carregamento e a do ID reutiliza `_transcript_id` ao montar o snapshot. A ordem de retenção e o caminho de atribuição não mudam. |
| Erros e tipos | A sonda da r28 deixou de gerar `TypeError` com objetos e listas misturados ao ID válido. A regressão também confere campos ausentes, nulos, em mapa ou texto e itens escalares inválidos. |
| Custo e superfície | A inspeção dos IDs ocorre só ao cruzar o limite. O código conserva o recorte de 2.049 chaves e não acrescenta leitura do prefixo, subprocesso, I/O ou travas. Não há interface visual no delta. |
| Cobertura | `test_retrofit_watch.py` importa o módulo e executa o caminho alterado em subprocessos reais com arquivos de estado. Um teste com oito subcasos passa no HEAD e falha nos seis subcasos inválidos com o script da base. R18 e F1 continuam verdes. |
| Sincronização | README, guia e CHANGELOG descrevem a tolerância na transição. O guia também descreve o valor vazio para um campo salvo que não seja lista. As três âncoras alteradas no backlog conferem com o módulo. Os quatro testes de release passaram. |

### Varredura de símbolos

Bucket A em linha. A comparação das ASTs da base e do HEAD não encontrou assinatura de função ou classe adicionada, removida ou alterada. O teste novo foi descoberto por `unittest`. Ruff não encontrou imports, redefinições ou variáveis locais ociosos nas categorias verificadas. Nenhum símbolo órfão no delta. Bucket B não solicitado.

### Overall Grade

| Criterion | Grade | Rationale |
|-----------|-------|-----------|
| Code Quality (Zen) | A | O filtro reutiliza a regra já usada para reconhecer IDs e mantém a ordem de retenção no mesmo ponto da transição. |
| Type Safety | A | O leitor normaliza o campo que não for lista e o snapshot recebe apenas IDs válidos dessa lista. Objetos, listas e escalares inválidos não entram no snapshot. |
| Error Handling | A | Os casos que travavam na base agora avançam o offset sem erro e mantêm a atribuição. Os controles intacto e de campo ausente continuam funcionando. |
| Security | A | O pré-scan passou e o delta não muda origens de dados, permissões, destinos nem travas. |
| Performance | A | Nas janelas produzidas pelo hook, validação ocorre uma vez na transição e o teto de 2.049 chaves foi verificado. O Stop normal não ganha replay. |
| Test Coverage | A | O teste novo tem seis subcasos vermelhos na base e oito verdes no HEAD, com asserções sobre offset, histórico, contadores e emissão. Os 21 Checks passaram. |
| Documentation | A | As notas públicas especificam a tolerância no snapshot. O handoff e o checkpoint apontam para o hash da correção e os sensores que foram repetidos. |
| **Overall** | **A** | O commit funcional fecha R19 com evidência comparativa. A falha reproduzida fora do delta foi registrada separadamente e não pede outro ciclo desta missão. |

## Achados da rodada

Nenhum achado no delta.

| # | Severidade | Achado | Onde |
|---|---|---|---|
| 1 | MEDIUM | Fora do delta. Antes da transição, um item `null` nos aposentados faz o hook ignorar metadado externo sem ID e pedir retro para a monitorada anterior. | `plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py:720` |

## Incrementos de conserto (R<n>)

Nenhum incremento novo. O achado 1 tem a mesma reprodução na base e no HEAD, antes de chegar à transição corrigida.

## O que virou incremento

- Achado 1 da r28 → R19, fechado pelo executor em `bdf75fa`. Repeti o Check de R19, o teste permanente e a comparação com a base. Os três casos da sonda histórica deram `codereview:1:1:0` no HEAD. A verificação de offset, o histórico de IDs e os contadores também passaram no teste novo.
- Os controles de R18 e a jornada F1 de QA permaneceram verdes. F1 retornou `linked=silêncio missing=silêncio empty=silêncio`.

## O que foi refutado

- A falha de retomada da r28 não continua aberta. Na base, objetos e listas na lista persistida deram `silêncio:0:0:2` em dois Stops. No HEAD, os dois deram `codereview:1:1:0` e conservaram o ID aposentado válido.
- A validação não descarta o registro inteiro por causa de um item inválido nem aumenta o teto. O teste de R19 exige igualdade do conjunto do snapshot no caso misto. O teste de R18 mantém o limite e exclui um ID já descartado.
- R19 não introduziu a supressão indevida por `null` antes da transição. A sonda abaixo obteve o mesmo falso pedido na base e no HEAD, sem cruzar o limite. Com a lista intacta ou um ID válido não aposentado, a externa encerrou a atribuição nos dois.
- O reuso de ID aposentado descrito na r28 não foi alterado por R19. A sonda `--retired-reuse` produziu as mesmas três saídas na base e no HEAD. O item de reuso já aberto nasceu nesta missão e não ganha duplicata nem nova recorrência da própria origem.

## Achados fora de escopo

O achado 1 foi registrado no `TODO.md` sob **Item nulo nos aposentados oculta metadado externo sem ID**. Em `skill_path`, `_transcript_id` devolve `None` para a fonte ausente e a busca pelo ID aposentado encontra o item `null`. O retorno antecipado confunde ausência de ID com prova de obsolescência. A leitura e a decisão em `skill_path` não mudaram no delta. É um defeito distinto do reuso de um ID válido já registrado no backlog.

## Pendências / Decisions for a Human

Nenhuma decisão nova. Type Safety, Error Handling e Test Coverage passaram de B para A com a mudança funcional em `bdf75fa`. Nenhum critério regrediu. Não houve ação no PR.

## Evidências reproduzíveis

Comandos executados no HEAD `8a17e1d142a9344425c48bfc88b31f22d99a9226`, salvo a comparação nomeada com a base.

- `env -u GIT_DIR -u GIT_WORK_TREE PYTHONDONTWRITEBYTECODE=1 bash -c 'source .sdd/config.sh && /usr/bin/time -f "elapsed=%es" bash -c "$TEST_CMD"'` → rc 0 em 68,42 s. Adaptadores, catálogo e versão 0.4.1 válidos. Loja com 154 testes e três pulados por configuração. Hook com 133 testes, todos verdes. O validador emitiu avisos não bloqueantes em três plugins fora do delta. Distribuição nativa e host Claude Code não foram exercitados.
- Executei em Bash os comandos das 21 células `done` de `checkpoint.md`, sem `GIT_DIR` e `GIT_WORK_TREE` e com `PYTHONDONTWRITEBYTECODE=1`. Todos retornaram rc 0 e stdout igual à célula esperada, comparado por tokens. I1 deu `1 0 1 0 0 1` e a jornada F1 confirmou os três silêncios no segundo Stop com offset completo.
- `env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -m unittest -q test_auto_docs.ReleaseTest` → quatro testes, rc 0.
- `ruff check --no-cache --select F401,F811,F841 plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py plugins/retrofit-watch/skills/retrofit-watch/tests/test_retrofit_watch.py` → rc 0.
- `git -P diff 0bb2e84c8076fcf91609acf414deabeeff48eec0...8a17e1d142a9344425c48bfc88b31f22d99a9226 --unified=0 -- . ':(exclude)**/checkpoint-notas.md' | bash /home/joruge/.agents/skills/codereview/scripts/scan_secrets.sh` → zero achados, zero erros, nove arquivos e 331 adições.
- `bash /home/joruge/repos/sdd_agents/tests/check-checkpoint.sh --check docs/handoffs/20261125-retrofit-watch-atribuicao/checkpoint.md` confirmou 21 linhas e nenhum Check cego. O backlog foi validado com `bash /home/joruge/repos/sdd_agents/tests/check-todo.sh --check TODO.md --baseline 8a17e1d142a9344425c48bfc88b31f22d99a9226`.

Para reproduzir a comparação de R19 sem trocar o checkout, exporte o módulo da base e rode a sonda da r28. A segunda chamada, sem `--expect`, exibe a divergência da base. Trocar `--expect` por `--retired-reuse` nos comandos da sonda compara o achado anterior de reuso. Nos dois SHAs, `before=silêncio:1:0,silêncio:1:0`, `trigger=silêncio:1:1,silêncio:1:1` e `fresh=silêncio:1:1,silêncio:1:1`.

~~~bash
tmp=$(mktemp -d)
base=0bb2e84c8076fcf91609acf414deabeeff48eec0
script=plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py
git show "$base:$script" > "$tmp/base.py"
export PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests
probe=$(sed -n '/^~~~python$/,/^~~~$/{ /^~~~/!p; }' docs/handoffs/20261125-retrofit-watch-atribuicao/40-review-r28.md)
env -u GIT_DIR -u GIT_WORK_TREE python3 -B -c "$probe" --expect
env -u GIT_DIR -u GIT_WORK_TREE python3 -B -c "$probe" --script "$tmp/base.py"
~~~

~~~text
HEAD  valid=codereview:1:1:0 invalid_object=codereview:1:1:0 invalid_list=codereview:1:1:0
base  valid=codereview:1:1:0 invalid_object=silêncio:0:0:2 invalid_list=silêncio:0:0:2
~~~

Repeti o teste permanente de R19 com o script da base, conservando o mesmo teste do HEAD. Foram um teste e seis falhas de subcasos, sem erro no executor de testes. `intact` e `missing` não falharam.

~~~bash
env -u GIT_DIR -u GIT_WORK_TREE python3 -B - "$tmp/base.py" <<'PY'
from functools import partialmethod
from pathlib import Path
import sys
import unittest
import test_retrofit_watch as t
t.HookHarness.run_hook = partialmethod(t.HookHarness.run_hook, script=Path(sys.argv[1]))
suite = unittest.defaultTestLoader.loadTestsFromName(
    "StopTest.test_invalid_retired_id_does_not_break_correlation_overflow", t)
assert suite.countTestCases() == 1
result = unittest.TextTestRunner(verbosity=2).run(suite)
assert result.testsRun == 1 and len(result.failures) == 6 and not result.errors
PY
~~~

### Sonda do achado fora do delta

Na mesma shell, extraia o bloco desta seção com `probe=$(sed -n '/^~~~python$/,/^~~~$/{ /^~~~/!p; }' docs/handoffs/20261125-retrofit-watch-atribuicao/40-review-r29.md)`. Rode `env -u GIT_DIR -u GIT_WORK_TREE python3 -B -c "$probe"` e depois repita com `"$tmp/base.py"` no fim. Ambas as execuções avançam o offset e retornam o vetor abaixo. Cada tripla indica alvo, encerramento e revisões. `intact` e `valid_id` medem o fechamento correto. `retired_id` comprova que ignorar metadado de ID realmente aposentado é esperado. Só `null_item` preserva crédito incorretamente.

~~~text
intact=silêncio:1:0 null_item=codereview:0:1 valid_id=silêncio:1:0 retired_id=codereview:0:1
~~~

~~~python
import json
import sys
from pathlib import Path

from test_retrofit_watch import SCRIPT, StopTest, identified_load, tool

def measure(case, script):
    test = StopTest()
    test.setUp()
    try:
        old = identified_load("irrelevante", test.w.other_skill, "msg_old", "toolu_old")
        ours = identified_load("codereview:coderabbit-pr", test.w.mkt_skill, "msg_active", "toolu_active")
        test.write(old[:1], ours, compact=True)
        out, state = test.checked_stop(script=script)
        assert out is None and not state["skill_correlation_lost"]
        assert state["retired_skill_calls"] == ["toolu_old"]
        assert state["current"] == "full:codereview"
        if case in ("null_item", "valid_id", "retired_id"):
            state["retired_skill_calls"].insert(0, None)
            (test.w.data / "sessions/s1.json").write_text(json.dumps(state), encoding="utf-8")
        meta = identified_load("superpowers:brainstorming", test.w.other_skill,
                               "msg_other", "toolu_external")[2]
        if case == "retired_id":
            meta["sourceToolUseID"] = "toolu_old"
        elif case != "valid_id":
            del meta["sourceToolUseID"]
        test.write([meta], tool(error=True), compact=True)
        out, state = test.checked_stop(script=script)
        entry = state["skills"]["full:codereview"]
        assert not state["skill_correlation_lost"]
        if out:
            assert "`/retrofit-skill:retrofit-skill codereview`" in test.context_of(out), out
        return f"{'codereview' if out else 'silêncio'}:{int(state['attribution_closed'])}:{entry['reviews']}"
    finally:
        test.tearDown()

script = Path(sys.argv[1]) if len(sys.argv) == 2 else SCRIPT
print(" ".join(f"{case}={measure(case, script)}" for case in ("intact", "null_item", "valid_id", "retired_id")))
~~~

### Recommended Actions

**Must Fix (CRITICAL)**

_Nenhum._

**Should Fix (HIGH)**

_Nenhum._

**Consider Fixing (MEDIUM/LOW)**

- Na triagem do backlog, verificar se a prova de obsolescência exige uma fonte válida antes de consultar os IDs aposentados. A sonda distingue o falso pedido do descarte legítimo.

### Cost footprint

_Skill 2.27.38 do caminho solicitado, cache Claude 2.30.2 identificado e não usado. Código e Bucket A em linha. Três agentes de prosa gpt-6.1-terra, sem relançamentos, com dez leituras integrais e 3–13 chamadas por agente. Custo monetário não medido._
