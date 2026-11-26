---
missao: 20261125-retrofit-watch-atribuicao
fase: REVIEW
rodada: 3
status: done
sessao: 01a2159b-e632-7222-9f44-8e3432faae90
data: 2026-11-25 23:14
gate: "env -u GIT_DIR -u GIT_WORK_TREE PYTHONDONTWRITEBYTECODE=1 bash -c 'source .sdd/config.sh && eval \"$TEST_CMD\"' em 87b9dc4, árvore inicial limpa, rc 0. Adaptadores e catálogo válidos, 154 testes da loja (3 pulados), 78 testes do hook e versão 0.4.1 validada. I1, F1, R1 e R2 verdes. Performance subiu de B para A com o fix 485e6c0. Code Quality (Zen), Error Handling e Test Coverage continuam B. R3 pending por dois achados reproduzidos."
reviewed_head: 87b9dc48b263695ed13aab32a400d748373c32a2
---

# Review — rodada r3 — Preservar a atribuição da retrofit-watch por mensagem

## TL;DR

R2 passou no delta de `485e6c0`. As seis ordens devolveram `graphify` e 1.000 tentativas falhas deixaram zero vínculos.
Dois casos ainda emitem a retro errada em leitura contínua e retomada. Ambos entram em `R3`. Um caso anterior ao delta vai ao backlog.
A nota geral é B. Performance melhorou de B para A. Nenhum código ou teste foi alterado.

## Escopo e medidas

Rodada DELTA pela skill `codereview:codereview base=b020b425ed8a967c4cc9c40a542a54968006dd7f`, até
`87b9dc48b263695ed13aab32a400d748373c32a2`. Três commits e nove caminhos no inventário. O único commit que tocou o hook e seus testes foi
`485e6c006cd8156767b09618e2f276316f2c2668`. Foram analisados o script, o teste de Stop e seis documentos do delta.
`checkpoint-notas.md` ficou fora da leitura e da varredura. O handoff de QA foi usado como controle histórico de F1.

### Detecção de segredos

| Resultado | Arquivos no escopo | Linhas adicionadas | Ferramentas | Erros |
|---|---:|---:|---|---:|
| PASS, 0 achados | 8 | 374 | `regex`, `gitleaks` | 0 |

### Verificações em `87b9dc4`

| Medida | Resultado |
|---|---|
| `env -u GIT_DIR -u GIT_WORK_TREE PYTHONDONTWRITEBYTECODE=1 bash -c 'source .sdd/config.sh && eval "$TEST_CMD"'` | rc 0. Adaptadores e catálogo válidos. Loja com 154 testes e 3 pulados. Hook com 78 testes sem falhas. Validador confirmou 0.4.1. |
| Células I1 e F1 de `checkpoint.md` | I1 devolveu `1 0 1 0 0 1`. F1 executou um teste de terminal com silêncio nas três variantes e repetiu o vetor de I1. |
| Célula R1 de `checkpoint.md` | A sonda deu as 12 saídas esperadas e o grupo de quatro testes terminou em `regressoes=4`. |
| Célula R2 de `checkpoint.md`, também com `plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py --medir --reuso` | Seis alvos `graphify`. Em 10, 100 e 1.000 erros, zero vínculos e 239, 240 e 241 bytes de estado. |
| Cinco testes de Stop ligados ao delta, com o script de cada revisão em subprocesso | Os cinco passaram em `87b9dc4`. Em `b020b42`, houve sete falhas de asserção nos cinco testes, sem erros de infraestrutura. |
| `env -u GIT_DIR -u GIT_WORK_TREE PYTHONDONTWRITEBYTECODE=1 bash /home/joruge/repos/sdd_agents/tests/check-checkpoint.sh --red docs/handoffs/20261125-retrofit-watch-atribuicao/checkpoint.md --only R3` | rc 0 do validador. Um Check pendente executado e confirmado em Red pelas seis variantes. |

### Cobertura, documentação e código morto

O script alterado tem três testes novos e um controle ampliado. Sete mutações independentes, só em cópias temporárias,
derrubaram os sensores de ordenação léxica, descarte de vínculos posteriores, retenção de vínculos antigos, ID de
resultado sem validação, perda da marca de consumo, ausência de limpeza de falha e restauração do atalho anterior do
Stop. O delta não removeu asserções. As duas lacunas novas aparecem na sonda desta rodada, mesmo com a suíte verde.

A decisão de atribuição é local e sequencial sob a trava do estado. O delta não mudou a trava, a gravação atômica nem o
caminho de saída. A leitura analisou os tipos do resultado e os pontos de consulta do mapa. A varredura inline não
encontrou símbolo novo sem uso nem órfão no delta. A única assinatura alterada foi o helper de testes
`HookHarness.write`, com um argumento opcional. A busca da grafia anterior encontrou só a definição removida.
Não houve varredura de dívida anterior, smoke no Claude Code nem teste em Windows.

## Nota da rodada

### Overall Grade

| Criterion | Grade | Rationale |
|-----------|-------|-----------|
| Code Quality (Zen) | B | O primeiro vínculo ainda presente no mapa passa por primeira ocorrência da mensagem. Remoção por erro ou consumo muda a ordem e pode deixar codereview no lugar de graphify. |
| Type Safety | A | IDs do resultado são validados antes da consulta. O mutante sem validação falhou com ID em lista, e o formato legado passou nos controles de retomada. |
| Error Handling | B | A limpeza da tentativa falha evita acumular o vínculo, mas permite que um ID repetido na mensagem ativa volte a valer como prova de origem. |
| Security | A | A varredura não encontrou segredos e o delta não introduz comando, acesso a rede, destino de escrita ou mudança de permissões. |
| Performance | A | O crescimento de 527 para 29.239 bytes na base caiu para 239 a 241 bytes no mesmo percurso de 10 a 1.000 falhas, com zero vínculos retidos. |
| Test Coverage | B | Os cinco testes direcionados passaram e os sete mutantes foram detectados. A suíte não protege a ordem após a perda do primeiro vínculo nem o reuso do ID de uma falha. |
| Documentation | B | A versão 0.4.1 está sincronizada e as medidas do delta conferem. Persistem a ambiguidade sobre o Red histórico da missão e a referência deslocada no backlog. |
| **Overall** | **B** | R2 fechou as reproduções anteriores, mas ainda há atribuição ao alvo errado em duas classes reproduzidas nesta rodada. |

## Achados da rodada

| # | Severidade | Achado | Onde |
|---|---|---|---|
| 1 | MEDIUM | A primeira ocorrência remanescente de uma mensagem no mapa muda depois da remoção ou do consumo de um vínculo e pode inverter a precedência. | `plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py:486`–`489` |
| 2 | MEDIUM | O resultado de erro apaga a evidência de que o ID já foi visto na mensagem ativa. Se uma carga externa reutiliza o ID, o hook trata a origem como confiável e preserva a monitorada indevidamente. | `plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py:686`–`690` |

**Achado 1.** A sonda alterna os registros de chamada de `msg_1`, `msg_2` e novamente `msg_1`, com IDs
distintos por chamada. A primeira entrada de `msg_1` é removida por falha ou marcada como consumida. O mapa restante
faz `msg_2` parecer anterior a `msg_1`. No caso de erro, confirmar `msg_1` descarta a vinculação nova antes de
`graphify` confirmar. No caso de consumo, confirmar `msg_2` mantém indevidamente o vínculo velho, e o metadado tardio
de `msg_1` reassume a atribuição. O controle sem remoção por erro e o controle com chamadas de `msg_1` adjacentes
emitem `graphify`. Na base, o caso de consumo intercalado emitia `graphify`; o de erro já emitia `codereview`, mas
também no controle sem erro, por descartar todas as outras mensagens. A perda de precedência após o consumo é regressão
do delta e a rota por erro expõe o mesmo defeito da ordem nova.

**Achado 2.** Na mesma `msg_1`, a monitorada carrega e outra chamada falha sem metadado. A externa em seguida tem o
mesmo ID da tentativa falha ou, no controle, um ID novo. O ID novo preserva `codereview` como esperado. O ID repetido
também preserva `codereview` no HEAD, mas resulta em silêncio na base. O caso não depende de reter todos os IDs entre
mensagens. O achado 3 da r2, que tratava de um ID consumido em outra mensagem, continua distinto.

### Sonda de R3

Rode a célula de R3 a partir da raiz. Cada par imprime controle, variante. Os cenários usam subprocessos do hook e
releem o estado em disco. Cada Stop exige offset no fim do transcript e ausência de erro interno. Em `87b9dc4` a saída
foi:

~~~text
ordem_erro_continua=graphify,codereview
ordem_erro_retomada=graphify,codereview
ordem_consumo_continua=graphify,codereview
ordem_consumo_retomada=graphify,codereview
reuso_apos_erro_continua=codereview,codereview
reuso_apos_erro_retomada=codereview,codereview
~~~

Para comparar, exporte o script com `git show b020b425ed8a967c4cc9c40a542a54968006dd7f:plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py`
para um arquivo temporário e passe esse caminho como argumento adicional ao comando da célula. A opção
`--backlog` executa apenas a reprodução fora do escopo, com o script indicado ou com o HEAD por padrão.

~~~python
import argparse
import json
import re
from pathlib import Path

from test_retrofit_watch import SCRIPT, StopTest, skill_via_tool, tool


def load(name, path, message, call_id):
    call, result, meta = skill_via_tool(name, path)
    call["message"]["id"] = message
    call["message"]["content"][0]["id"] = call_id
    result["message"]["content"][0]["tool_use_id"] = call_id
    meta["sourceToolUseID"] = call_id
    return call, result, meta


def stop(test, script):
    out = test.run_hook(script=script)
    state = json.loads((test.w.data / "sessions/s1.json").read_bytes())
    assert state["offset"] == test.w.transcript.stat().st_size
    assert not (test.w.data / "errors.log").exists()
    if out is None:
        return "silêncio"
    target, = re.findall(r"`/retrofit-skill:retrofit-skill ([^`]+)`", test.context_of(out))
    return target


def order_after_error(test, script, resume, failed):
    first = load("coderabbit-pr", test.w.mkt_skill, "msg_1", "toolu_a")
    newer = load("graphify", test.w.graphify, "msg_2", "toolu_b")
    second = load("coderabbit-pr", test.w.mkt_skill, "msg_1", "toolu_c")
    if failed:
        first[1]["message"]["content"][0].update(is_error=True, content="Skill não carregou")
    test.write(first[:1], newer[:2], second[:2], first[1:2], compact=True)
    if resume:
        assert stop(test, script) == "silêncio"
    test.write(second[2:], newer[2:])
    if not failed:
        test.write(first[2:])
    test.write(tool(error=True))
    return stop(test, script)


def order_after_consumption(test, script, resume, interleaved):
    first = load("coderabbit-pr", test.w.mkt_skill, "msg_1", "toolu_a")
    newer = load("graphify", test.w.graphify, "msg_2", "toolu_b")
    second = load("coderabbit-pr", test.w.mkt_skill, "msg_1", "toolu_c")
    test.write(first)
    groups = (newer[:2], second[:2]) if interleaved else (second[:2], newer[:2])
    test.write(*groups, compact=True)
    if resume:
        assert stop(test, script) == "silêncio"
    test.write(newer[2:], second[2:], tool(error=True))
    return stop(test, script)


def reuse_after_error(test, script, resume, duplicate):
    monitored = load("codoreview:coderabbit-pr", test.w.mkt_skill, "msg_1", "toolu_a")
    failed = load("nao-instalada", test.w.other_skill, "msg_1", "toolu_b")
    failed[1]["message"]["content"][0].update(is_error=True, content="Unknown skill: nao-instalada")
    external = load("superpowers:brainstorming", test.w.other_skill, "msg_1",
                    "toolu_b" if duplicate else "toolu_c")
    test.write(monitored, failed[:2], compact=True)
    if resume:
        assert stop(test, script) == "silêncio"
    test.write(external, tool(error=True))
    return stop(test, script)


def late_external(test, script, resume, late):
    older = load("brainstorming", test.w.other_skill, "msg_1", "toolu_a")
    newer = load("graphify", test.w.graphify, "msg_2", "toolu_b")
    test.write(older[:2], newer, compact=True)
    if resume:
        assert stop(test, script) == "silêncio"
    if late:
        test.write(older[2:])
    test.write(tool(error=True))
    return stop(test, script)


def measure(scenario, script, resume, variant):
    test = StopTest()
    test.setUp()
    try:
        return scenario(test, script, resume, variant)
    finally:
        test.tearDown()


parser = argparse.ArgumentParser()
parser.add_argument("script", type=Path, nargs="?", default=SCRIPT)
parser.add_argument("--backlog", action="store_true")
args = parser.parse_args()
scenarios = [("ordem_erro", order_after_error), ("ordem_consumo", order_after_consumption),
             ("reuso_apos_erro", reuse_after_error)]
if args.backlog:
    scenarios = [("externa_atrasada", late_external)]
for label, scenario in scenarios:
    for mode, resume in (("continua", False), ("retomada", True)):
        targets = [measure(scenario, args.script, resume, case) for case in (False, True)]
        print(f"{label}_{mode}={','.join(targets)}")
~~~

## Incrementos de conserto (R<n>)

| R<n> | Achado | Check escrito no checkpoint |
|---|---|---|
| R3 | Achados 1–2, precedência e ambiguidade após limpeza | Os quatro pares de ordem devem emitir `graphify,graphify`. Nos dois pares de reuso, o controle deve emitir `codereview` e a repetição deve ficar em silêncio. |

## O que virou incremento

| ID | Incremento | Check (comando → esperado) | Status | Commit |
|---|---|---|---|---|
| R3 | Preservar a ordem das mensagens após remover vínculos e rejeitar o reuso do ID de uma chamada falha na mensagem ativa (r3, achados 1–2) | `env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -c "$(sed -n '/^~~~python$/,/^~~~$/{ /^~~~/!p; }' docs/handoffs/20261125-retrofit-watch-atribuicao/40-review-r3.md)"` → `ordem_erro_continua=graphify,graphify ordem_erro_retomada=graphify,graphify ordem_consumo_continua=graphify,graphify ordem_consumo_retomada=graphify,graphify reuso_apos_erro_continua=codereview,silêncio reuso_apos_erro_retomada=codereview,silêncio` | pending | — |

- `R2`, achados 1–2 de r2, fechado em `485e6c0`. A sonda antes/depois deu seis alvos corretos no HEAD e zero
  vínculos após os três lotes de falhas, contra 10, 100 e 1.000 vínculos na base. I1, F1 e R1 continuaram verdes.
- `R3` requer regressões permanentes de Stop para as duas classes, em leitura contínua e retomada. Preservar o
  Check de R2, incluindo a estabilidade do estado, e os de I1, F1 e R1.

## O que foi refutado

- **R2 só teria deslocado os Reds.** A sonda de r2 em `b020b42` repetiu os dois alvos errados e o crescimento até
  29.239 bytes. Em `87b9dc4`, deu seis alvos `graphify` e no máximo 241 bytes. Os mutantes de ordenação, filtro e
  limpeza falharam individualmente nos testes atuais.
- **A limpeza de erros apagaria também a marca já consumida.** O teste ampliado passou com resultado atrasado para
  ID consumido. Remover a guarda `is not False` na cópia temporária derrubou esse teste. O achado 2 trata da perda
  de um ID que ainda não havia sido consumido por metadado.
- **A correção teria fechado o reuso entre mensagens de r2.** Repetir `--reuso` na sonda de R2 devolveu
  `codereview` para IDs distintos e repetidos em ambos os commits. A limitação continua no mesmo item do backlog.

## Achados fora de escopo

- **LOW — Metadado externo antigo encerra a atribuição de uma carga posterior**, em `plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py:622`–`633`. A
  sonda `--backlog` deu `graphify,silêncio` no HEAD e na base, com e sem retomada. No controle a chamada externa de
  `msg_1` já aparece, mas seu metadado não chega. A variante acrescenta esse metadado depois de `graphify` em
  `msg_2`. O fallback anterior ao delta trata o ID aposentado como ausência de vínculo e aplica a limpeza conservadora.
  Registrado em `TODO.md`. Não entra em R3.
- O reuso de ID consumido entre mensagens e os dois achados de prosa de r1 permanecem nos itens existentes.
  A mesma missão não ganha outra linha de recorrência.

## Pendências / Decisions for a Human

Nenhuma. O gate ainda não passa, mas a melhora de Performance de B para A veio do fix `485e6c0` e nenhuma letra
caiu. O laço segue com R3.

## Boot da próxima fase

Leia R3 no checkpoint e rode a sonda em Red antes de editar. Os controles distinguem erro de consumo e ID novo de ID
reaproveitado. Feche o incremento em TDD e repita os cinco Checks, inclusive o crescimento de estado de R2.

### Recommended Actions

**Must Fix (CRITICAL)**

_Nenhum._

**Should Fix (HIGH)**

_Nenhum._

**Consider Fixing (MEDIUM/LOW)**

- Executar R3. Distinguir a ordem de uma mensagem da ordem atual dos seus vínculos, e a remoção do vínculo da
  decisão de confiar num ID reaproveitado.
- Manter no backlog o caso de metadado externo obsoleto e os itens históricos.

_Custo da revisão: skill solicitada 2.27.38, registro do plugin instalado 2.30.2. Código, testes e varredura em linha.
Dois agentes de documentação gpt-6.1-terra, seis documentos, respostas completas e 2 a 11 chamadas informadas.
Sete mutações independentes em cópias temporárias. Custo monetário não medido._
