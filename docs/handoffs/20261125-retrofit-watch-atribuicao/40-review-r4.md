---
missao: 20261125-retrofit-watch-atribuicao
fase: REVIEW
rodada: 4
status: done
sessao: 01a215c9-b884-7402-8ca9-c9f98f079706
data: 2026-11-26 00:04
gate: "`env -u GIT_DIR -u GIT_WORK_TREE PYTHONDONTWRITEBYTECODE=1 bash -c 'source .sdd/config.sh && eval \"$TEST_CMD\"'` em e405af12e689defb6987857ead4473faffd3a8e5, árvore inicial limpa, rc 0. Adaptadores e catálogo válidos, 154 testes da loja (3 pulados), 83 do hook e versão 0.4.1 confirmada. I1, F1, R1, R2 e R3 verdes. R4 pendente com quatro divergências reproduzidas. Gate não passou. Platô em Code Quality (Zen), Error Handling e Test Coverage, todos B. Documentation e Overall permaneceram B e são tolerados pelo gate."
reviewed_head: e405af12e689defb6987857ead4473faffd3a8e5
---

# Review — rodada r4 — Preservar a atribuição da retrofit-watch por mensagem

## TL;DR

O fix `43c2d49` fechou as seis reproduções de R3. Os cinco Checks e a suíte passaram.
Duas variantes novas para a revisão ainda pedem retro da skill errada, em leitura contínua e retomada. Ambas já falham na base e passam pelos trechos alterados em R3. Foram reunidas no Check de R4.
Nota geral B, com as mesmas letras de r3. O gate não passa. Um achado só de prosa foi ao backlog. Nenhum código ou teste foi alterado.

## Escopo e medidas

Rodada DELTA de `codereview:codereview base=87b9dc48b263695ed13aab32a400d748373c32a2` até `e405af12e689defb6987857ead4473faffd3a8e5`.
Seis commits e dez caminhos no inventário. Nove caminhos analisados, incluindo um script e seu arquivo de testes.
O diário append-only ficou fora da leitura e da varredura. O handoff de QA foi usado como controle de F1.
A verificação de prosa cobriu 106 unidades em sete arquivos. O script e os testes foram lidos no delta, com o contexto local de cada trecho.

### Detecção de segredos

| Resultado | Arquivos | Linhas adicionadas | Ferramentas | Erros |
|---|---:|---:|---|---:|
| PASS, 0 achados | 9 | 470 | `regex`, `gitleaks` | 0 |

### Verificações em `e405af1`

| Sensor | Resultado |
|---|---|
| `env -u GIT_DIR -u GIT_WORK_TREE PYTHONDONTWRITEBYTECODE=1 bash -c 'source .sdd/config.sh && eval "$TEST_CMD"'` | rc 0. Adaptadores e catálogo válidos. Loja com 154 testes, 3 pulados. Hook com 83 testes sem falhas. Validador confirmou a 0.4.1. |
| Checks de `checkpoint.md` | Cinco comandos com rc 0 e saídas iguais às esperadas. I1 deu `1 0 1 0 0 1`. F1 ficou em silêncio nas três variantes. R1 deu `regressoes=4`. R2 deu seis alvos `graphify` e `falhas=estavel`. Os seis pares de R3 conferiram. |
| Check de R2 com `plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py --medir --reuso` como argumentos da sonda | Após 10, 100 e 1.000 falhas em mensagens distintas, ficaram 0 vínculos e 291, 292 e 293 bytes na execução desta rodada. |
| `env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -m unittest test_auto_docs.ReleaseTest.test_the_four_places_agree_at_0_4_0_or_later` | 1 teste, rc 0. |
| Sonda de R3 com o script exportado de `87b9dc4` | Seis divergências nas mesmas variantes descritas em r3. Mesmo script em `f382fa2`. |
| Sonda de R4 abaixo, com o script do HEAD e com o de `87b9dc4` | Quatro divergências em ambos os scripts. Offset confirmado no fim do transcript, sem `errors.log`. |

### Qualidade do código, tipos e cobertura

A ordem foi separada dos vínculos e a limpeza agora distingue falha, consumo e troca de mensagem.
A lista de ordem e o mapa divergem quando um último vínculo é removido cedo demais.
Os IDs continuam validados antes das consultas e os formatos suportados de estado anterior passam pelos controles de retomada.
O delta não altera a trava da sessão, o arquivo gravado por substituição atômica ou a fronteira de acesso.
Não há interface gráfica neste delta. Não houve smoke no Claude Code nem no Windows.

O script tem cinco testes de Stop novos e um controle ampliado. O grupo direcionado de sete testes passou no HEAD.
Doze mutações independentes no script temporário foram detectadas pelos testes do grupo. Foram testadas separadamente a migração vazia,
o descarte de ordem anterior, a limpeza de ordem sem origem, as duas limpezas de IDs falhos, o reuso aceito, o bloqueio além da
mensagem ativa, a repetição de posição, a remoção de vínculo, a retenção da evidência de falha e as duas variantes de aposentadoria
da ordem após erro. Os novos percursos de R4 continuam fora da suíte permanente.

### Código morto e documentação

A varredura inline do delta não encontrou símbolo novo sem uso nem órfão. Os auxiliares novos são usados pelos testes.
`ruff check --no-cache --select F401,F811,F841 plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py plugins/retrofit-watch/skills/retrofit-watch/tests/test_retrofit_watch.py` retornou rc 0.
A busca de dívida preexistente não foi executada. A versão 0.4.1 está sincronizada.
Os dois registros de prosa de r1 estão resolvidos em `9e79cb6`. O linter do backlog aceitou as âncoras.
O achado 3 desta rodada distingue se a outra chamada pendente é da mesma mensagem.

## Nota da rodada

### Overall Grade

| Criterion | Grade | Rationale |
|-----------|-------|-----------|
| Code Quality (Zen) | B | A ordem ficou independente do mapa só enquanto a posição é retida. O último erro da mensagem ainda pode colocá-la depois de uma mensagem posterior. |
| Type Safety | A | IDs não textuais são descartados antes da consulta e os estados legados suportados retomam. A mutação que elimina a reconstrução de ordem falhou no teste de migração. |
| Error Handling | B | Uma falha anterior ao reconhecimento da própria mensagem perde a marca do ID e o reuso volta a valer como prova. |
| Security | A | O delta não altera comandos executados, permissões ou destinos de escrita. Varredura por dois detectores com zero achados. |
| Performance | A | Após 1.000 falhas em mensagens distintas não houve vínculos retidos. O estado oscilou só dois bytes entre os três lotes. |
| Test Coverage | B | Os 83 testes passaram e as doze mutações direcionadas foram detectadas. Os quatro percursos de R4 ainda devolvem o alvo incorreto com a suíte verde. |
| Documentation | B | O handoff omite que a chamada pendente precisa pertencer à mesma mensagem para sustentar a garantia de R3. O caso registrado no backlog reproduz a diferença. |
| **Overall** | **B** | As seis reproduções de R3 passaram, mas dois casos de atribuição indevida continuam nos caminhos alterados. As letras não avançaram nesta rodada. |

## Achados da rodada

| # | Severidade | Achado | Onde |
|---|---|---|---|
| 1 | MEDIUM | Quando o último vínculo da mensagem mais antiga falha, ela perde posição mesmo com outra mensagem pendente. Uma carga da primeira mensagem que chega em seguida entra no fim e pode reassumir a atribuição. | `plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py:708`–`709` e `:621`–`623` |
| 2 | MEDIUM | Um ID falho ainda é aceito como novo quando a falha ocorreu antes da mesma mensagem se tornar ativa, mesmo se outra chamada dela já estava pendente. | `plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py:704`–`709` e `:611`–`612` |
| 3 | LOW, prosa | A garantia do handoff fala em qualquer chamada pendente. Na reprodução do achado 1 existe uma pendência, mas em outra mensagem, e ela não protege a ordem. | `docs/handoffs/20261125-retrofit-watch-atribuicao/20-handoff-exec.md:55` |

No achado 1, a primeira chamada é de `msg_a`. A chamada de `msg_b` já está pendente quando a primeira falha.
Outra carga de `msg_a`, com ID novo, chega antes do metadado de `msg_b`. Quando os metadados chegam na ordem
`msg_b`, `msg_a`, a retro deve ser de `graphify`, a carga posterior pela ordem da mensagem. No controle, o resultado
da primeira chamada não é erro e `graphify` vence. Na variante falha, o hook troca para `codereview`.

No achado 2, `msg_a` tem uma tentativa falha e outra carga monitorada previamente pendente, que passa a ser ativa pelo
metadado. O ID da falha já foi removido sem marca. Uma carga externa da mesma mensagem com ID novo deve preservar
`codereview`. Com ID reaproveitado, a origem é ambígua e a atribuição deveria encerrar. O HEAD emite `codereview` nos dois casos.

Os dois comportamentos também existem em `87b9dc4`. Não são regressões introduzidas por R3. São lacunas remanescentes
na remoção de ordem e na retenção de IDs, ambas modificadas em R3. O caso de reuso **entre** mensagens permanece fora de R4.

### Sonda de R4

Execute o comando da célula de R4 no checkpoint. Para comparar com a base, exporte
`git show 87b9dc48b263695ed13aab32a400d748373c32a2:plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py` para um script temporário e acrescente seu caminho como argumento.
O controle e a variante reportam os alvos nesta ordem. Os dois scripts devolveram o mesmo vetor.
O validador `env -u GIT_DIR -u GIT_WORK_TREE PYTHONDONTWRITEBYTECODE=1 bash /home/joruge/repos/sdd_agents/tests/check-checkpoint.sh --red docs/handoffs/20261125-retrofit-watch-atribuicao/checkpoint.md --only R4` confirmou o Red em `e405af1` com rc 0 e um Check pendente executado.

~~~text
ordem_ultimo_vinculo_continua=graphify,codereview
ordem_ultimo_vinculo_retomada=graphify,codereview
reuso_pre_ativacao_continua=codereview,codereview
reuso_pre_ativacao_retomada=codereview,codereview
~~~

~~~python
import argparse
import json
import re
from pathlib import Path
from test_retrofit_watch import SCRIPT, StopTest, identified_load, tool


def stop(test, script):
    out = test.run_hook(script=script)
    state = json.loads((test.w.data / "sessions/s1.json").read_bytes())
    assert state["offset"] == test.w.transcript.stat().st_size
    assert not (test.w.data / "errors.log").exists()
    if out is None:
        return "silêncio"
    targets = re.findall(r"`/retrofit-skill:retrofit-skill ([^`]+)`", test.context_of(out))
    return "+".join(targets)


def order(test, script, resume, failed):
    first = identified_load("coderabbit-pr", test.w.mkt_skill, "msg_a", "toolu_a")
    later = identified_load("graphify", test.w.graphify, "msg_b", "toolu_b")
    retry = identified_load("coderabbit-pr", test.w.mkt_skill, "msg_a", "toolu_c")
    first[1]["message"]["content"][0]["is_error"] = failed
    test.write(first[:1], later[:2], first[1:2], compact=True)
    if resume:
        assert stop(test, script) == "silêncio"
    test.write(retry[:2], later[2:], retry[2:], tool(error=True), compact=True)
    return stop(test, script)


def failed_before_activation(test, script, resume, duplicate):
    fail = identified_load("nao-instalada", test.w.other_skill, "msg_a", "toolu_a")
    monitored = identified_load("coderabbit-pr", test.w.mkt_skill, "msg_a", "toolu_b")
    external = identified_load("superpowers:brainstorming", test.w.other_skill,
                               "msg_a", "toolu_a" if duplicate else "toolu_c")
    fail[1]["message"]["content"][0]["is_error"] = True
    test.write(fail[:1], monitored[:2], fail[1:2], monitored[2:], compact=True)
    if resume:
        assert stop(test, script) == "silêncio"
    test.write(external, tool(error=True), compact=True)
    return stop(test, script)


def run(scenario, script, resume, variant):
    test = StopTest()
    test.setUp()
    try:
        return scenario(test, script, resume, variant)
    finally:
        test.tearDown()


parser = argparse.ArgumentParser()
parser.add_argument("script", type=Path, nargs="?", default=SCRIPT)
args = parser.parse_args()
for name, scenario in (("ordem_ultimo_vinculo", order), ("reuso_pre_ativacao", failed_before_activation)):
    for modo, resume in (("continua", False), ("retomada", True)):
        observed = [run(scenario, args.script, resume, variant) for variant in (False, True)]
        print(f"{name}_{modo}={','.join(observed)}")
~~~

## Incrementos de conserto (R<n>)

| R<n> | Achado | Check escrito no checkpoint |
|---|---|---|
| R4 | Achados 1–2, ordem após último vínculo e reuso antes da ativação | Os dois pares de ordem devem dar `graphify,graphify`. Os dois pares de reuso devem dar `codereview,silêncio`. Cada par cobre um controle e uma variante com falha de atribuição. |

## O que virou incremento

| ID | Incremento | Check (comando → esperado) | Status | Commit |
|---|---|---|---|---|
| R4 | Preservar a precedência após a falha do último vínculo e a ambiguidade do ID falho antes do reconhecimento (r4, achados 1–2) | `env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -c "$(sed -n '/^~~~python$/,/^~~~$/{ /^~~~/!p; }' docs/handoffs/20261125-retrofit-watch-atribuicao/40-review-r4.md)"` → `ordem_ultimo_vinculo_continua=graphify,graphify ordem_ultimo_vinculo_retomada=graphify,graphify reuso_pre_ativacao_continua=codoreview,silêncio reuso_pre_ativacao_retomada=codoreview,silêncio` | pending | — |

- R3, achados 1–2 de r3, fechado em `43c2d49`. A sonda independente reproduziu as seis divergências na base e devolveu os seis pares esperados no HEAD.
- R4 não pede histórico global de chamadas falhas. Pede preservar as duas decisões quando ainda há uma carga concorrente pendente. Manter os cinco Checks existentes, em especial o descarte de falhas isoladas de R2.

## O que foi refutado

- **R3 não mudou as seis reproduções de r3.** A mesma sonda, com a mesma fixture, dá quatro pares de ordem corretos e dois pares de reuso corretos no HEAD. A base falha em uma variante de cada par.
- **A separação da ordem teria reintroduzido a retenção de vínculos falhos isolados.** A medição de R2 deu zero vínculos em cada lote. O teste permanente também exige ordem e lista de falhas vazias.
- **O verde de I1 em `682cd3d` não tinha comprovação direta nesta revisão.** A sonda do plano, com script e fixture extraídos desse commit para um diretório temporário, retornou `1 0 1 0 0 1`. Os agentes também apontaram ausência de logs históricos de outras medições. As reexecuções do HEAD comprovam esta rodada e não substituem aqueles logs. Os totais históricos de mutações não foram recontados e não há evidência de que estejam incorretos.

## Achados fora de escopo

- Achado 3, só de prosa, registrado em [TODO.md](../../../TODO.md) na seção aberta. Não vira incremento.
- Os itens já abertos sobre metadado externo obsoleto e reuso entre mensagens não são novos achados. A sonda de R3 com `--backlog` voltou a dar `graphify,silêncio` no HEAD e na base, nos dois modos. O controle de R2 com `--reuso` manteve `codereview` nos dois casos.

## Pendências / Decisions for a Human

A nota não avançou em relação a r3. `Code Quality (Zen)`, `Error Handling` e `Test Coverage` continuam B,
apesar do fix real `43c2d49`. A revisão encerra neste platô, sem atestar o gate. R4 fica registrado em `pending`
com o Red reproduzido. Cabe ao mantenedor decidir se a missão deve retomar pelo incremento ou rever o limite
de correlação. Nenhuma mudança foi feita no código, no gate ou no limite de rodadas.

## Boot da próxima fase

Se houver retomada, execute o Check R4 em Red a partir do checkpoint. Cubra os dois percursos em Stop com transcript
e estado em disco, sem usar silêncio por erro interno como acerto. Depois repita os cinco Checks anteriores e o `TEST_CMD`
com Git isolado. Não amplie o histórico para IDs de mensagens aposentadas sem nova decisão.

### Recommended Actions

**Must Fix (CRITICAL)**

_Nenhum._

**Should Fix (HIGH)**

_Nenhum._

**Consider Fixing (MEDIUM/LOW)**

- Se o mantenedor decidir retomar, executar R4 sem reintroduzir a retenção de falhas isoladas.
- Precisar o alcance da garantia no handoff apenas pela triagem do backlog.

**Deferred (form)**

_Nenhum._

**Outside scope (tracker)**

_Nenhum apontamento adicional dos verificadores fora das unidades editadas._

_Custo da revisão: skill 2.30.2 instalada, solicitada pela cópia 2.27.38. A versão instalada acrescenta a classificação de prosa, a verificação e o fechamento por unidade, além de separar a nota de documentação. Dois verificadores gpt-6.1-terra, 106 unidades, 14 e 81 chamadas informadas. Zero agentes por arquivo, código e varredura inline, doze mutações temporárias. Custo monetário não medido._
