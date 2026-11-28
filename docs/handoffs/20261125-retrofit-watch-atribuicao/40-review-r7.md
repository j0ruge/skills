---
missao: 20261125-retrofit-watch-atribuicao
fase: REVIEW
rodada: 7
status: done
sessao: 01a21df2-5346-7262-b682-5aaa52d7b7de
data: 2026-11-27 14:07
gate: "Não passou. Em 6f190e3, env -u GIT_DIR -u GIT_WORK_TREE PYTHONDONTWRITEBYTECODE=1 bash -c 'source .sdd/config.sh && eval \"$TEST_CMD\"' → rc 0, 154 testes da loja (3 pulados), 96 do hook, adaptadores e catálogo válidos e versão 0.4.1 confirmada. Oito Checks concluídos com rc 0 e árvore limpa antes da revisão. A sonda R7 saiu com rc 1 em cinco subcasos. Platô em Code Quality (Zen), Error Handling e Test Coverage, todos B como em r6."
reviewed_head: 6f190e3907f80eb39fb9cc79d35822e8efcc930b
---

# Review — rodada r7 — Atribuição da retrofit-watch por mensagem

## TL;DR

A revisão completa repetiu oito Checks, a suíte e seis variantes temporárias de R6.
Dois defeitos viraram R7. A retomada de estado já encerrado na 0.4.0 volta a pedir retro.
A colisão de um ID pendente sem origem pode apagar a prova de reuso. Nenhum código foi alterado.
Nota geral B, com as mesmas letras de r6. O gate não passou.

## Nota da rodada

**Escopo.** Revisão completa com `codereview:codereview` para Python e `unittest`.
Base `origin/main` em `fe38d1f`, segundo pai de `624de6b`, até `6f190e3`.
A `main` local ainda apontava para `e45db9e`. Usá-la incluiria oito arquivos de
`html-presentation` já incorporados na base. A comparação do primeiro pai com o merge
retornou zero alterações no código e nos testes da retrofit-watch. O diff da missão tem
23 arquivos, 3.210 adições e 23 remoções. Dois registros foram excluídos da leitura integral
conforme a instrução da fase. O Check de R6 executou apenas o bloco da sonda, como pede o checkpoint.

### 🛑 Secrets Detection

| Detector | Arquivos | Linhas adicionadas | Achados |
|---|---:|---:|---:|
| regex e gitleaks | 21 | 2.766 | 0 |

Estado `PASS` no escopo autorizado. O diff entregue ao scanner usou as duas exclusões acima
e retornou `errors=[]`. A correlação não acrescenta comandos de shell, rede ou destinos de escrita.
O estado continua sendo lido e salvo sob a trava existente, com substituição atômica.

### Princípios Zen e revisão técnica

A regra compartilhada de atribuição cobre nome e caminho. A perda do encerramento na migração e
a perda de evidência na poda contrariam a decisão conservadora do plano. As entradas de
`message.id`, `tool_use.id` e `sourceToolUseID` são validadas antes da consulta. Nenhum Red
depende de tipo inválido, erro de leitura ou exceção do hook. As duas reproduções consomem o
transcript inteiro. Não há alteração de interface visual ou contrato HTTP nesta missão.

### Test Coverage

| Arquivo ou sensor | Status | Evidência em `6f190e3` |
|---|---|---|
| `retrofit_watch.py` | WITH_TESTS | `test_retrofit_watch.py` importa o módulo, executa o hook em subprocesso e confere o estado em disco. |
| `e2e/test_retrofit_watch_stop.py` | PASS | Check F1, dois Stops por variante. Metadado antigo com origem válida, ausente ou vazia permaneceu em silêncio. |
| I1, F1 e R1–R6 | PASS | As oito células de `checkpoint.md` saíram com rc 0 e a saída esperada. I1 retornou `1 0 1 0 0 1`. R6 confirmou `marca_apos_confirmacao=1` e `regressao=1`. |
| Limites e retenção | PASS | Com o Check R2 e `--medir`, 10, 100 e 1.000 falhas independentes deixaram zero vínculos e estados de 325, 326 e 327 bytes, respectivamente. Os testes de limites de mensagens e de IDs passaram no hook. |
| Mutação seletiva de R6 | PASS | Seis variantes em cópias temporárias, cada uma com os dois testes de R5 e R6. Todas deram falha de asserção, sem erro de teste. |
| Sonda R7 | FAIL | Cinco divergências com offset completo e sem `errors.log`, fora da suíte atual. |

A suíte configurada foi `env -u GIT_DIR -u GIT_WORK_TREE PYTHONDONTWRITEBYTECODE=1 bash -c 'source .sdd/config.sh && eval "$TEST_CMD"'`. Saiu com rc 0 em `6f190e3`. A loja rodou 154
testes com três pulados por configuração. O hook rodou 96 sem falhas. A validação de versões
confirmou a 0.4.1 e apresentou três avisos de outras skills, sem falhar o gate de versão. A rodada
não fez smoke de Claude Code, Windows ou distribuição nativa. As jornadas locais usam transcript
sintético e estado em disco.

### Sincronia da documentação

README, catálogo Claude, manifesto, SKILL e primeira entrada do CHANGELOG concordam na 0.4.1.
`env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -m unittest -v test_auto_docs.ReleaseTest.test_the_four_places_agree_at_0_4_0_or_later`
em `6f190e3` rodou um teste com rc 0. Nenhuma superfície pública nova ficou sem docstring.
O comando literal do plano ainda herda o Git do runner. A rastreabilidade das medições antigas
permanece no item já aberto do backlog, sem invalidar as medições repetidas nesta rodada.

### 🧹 Dead Code & Cleanup

A varredura inline de símbolos introduzidos ou órfãos encontrou zero candidatos confirmados.
Os seis auxiliares novos de correlação e os dois tetos têm chamadores ou consumidores.
A mudança na assinatura de `skill_path` atualiza seu único chamador. Os dois arquivos de teste
estão ligados pela fixture de Stop. Código morto preexistente não foi varrido.

### Overall Grade

| Criterion | Grade | Rationale |
|-----------|-------|-----------|
| Code Quality (Zen) | B | A migração confunde ausência de marca nova com ausência de encerramento. A junção de evidências confunde pendência sem origem com ausência de pendência. |
| Type Safety | A | IDs externos são validados e os formatos de estado exercitados retomaram e avançaram até o fim. Os Reds usam tipos aceitos e decorrem da interpretação do estado. |
| Error Handling | B | A retomada sem prova e o reuso ambíguo deveriam encerrar o crédito futuro. Em cinco subcasos, ambos acabaram emitindo um pedido indevido. |
| Security | A | Regex e gitleaks não encontraram segredos nas 2.766 linhas autorizadas. A mudança preserva a trava e não introduz comandos externos nem novos caminhos de escrita. |
| Performance | A | Os dois limites foram exercitados. De 10 a 1.000 falhas independentes, a lista de vínculos ficou vazia e o estado variou só dois bytes. |
| Test Coverage | B | Os 96 testes do hook, seis variantes temporárias e oito Checks confirmam as garantias já medidas. A suíte não vê os dois percursos reproduzidos em R7. |
| Documentation | B | A versão está sincronizada. A receita antiga de suíte omite o isolamento do Git, e parte das medidas históricas continua sem saída preservada no handoff. |
| **Overall** | **B** | R6 fechou com mudança funcional e sensores, mas dois outros falsos pedidos permanecem. As letras repetem r6. |

O gate para no mesmo conjunto de notas. `cd55517` fecha o cenário de r6 e tem mudança real
no hook. Ainda assim, a rodada não autoriza nova passagem automática pela revisão.

## Achados da rodada

| # | Severidade | Achado | Onde |
|---|---|---|---|
| 1 | MEDIUM | Retomar um estado 0.4.0 já encerrado permite que o primeiro metadado atrasado da monitorada reabra a atribuição. | `plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py:424`, `plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py:682` |
| 2 | MEDIUM | Colisão com chamada ainda pendente e sem origem pode perder a marca de ambiguidade ao podar a tentativa de outra mensagem. | `plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py:661` |
| 3 | MEDIUM | A receita histórica de suíte no plano herda as variáveis do Git do runner. Achado de documentação, sem mudança do hook. | `docs/handoffs/20261125-retrofit-watch-atribuicao/01-plano.md:121` |

**1.** A 0.4.0 processa a chamada monitorada e a carga externa posterior, inclusive o metadado
externo, antes da atualização. Salva `current=null`, com histórico de `codereview` e sem
`attribution_closed`. O primeiro evento da retomada na 0.4.1 é o metadado atrasado da monitorada.
Com origem válida sem mapa, ausente ou vazia, o Stop indevidamente pede retro e sobe `reviews`
de 0 para 1. Quando o primeiro Stop roda na 0.4.1, os três casos ficam em silêncio. Um slash
explícito ou uma carga nova vinculada ainda consegue atribuir o trabalho a `graphify`.
O cenário de R1 também usa estado legado, mas só encerra com o metadado externo **depois** da
atualização. Isso preenche a marca nova e mascara a perda reproduzida aqui.

**2.** Com `codereview` ativa na mensagem `msg_1`, uma chamada ainda não confirmada usa um ID
válido sem `message.id`. A chamada está no mapa com valor nulo. Outra tentativa de `msg_2`
reusa esse ID e sai da janela por não ter outro vínculo. A combinação filtra o valor nulo
da pendência original como se a pendência nunca tivesse existido. A mensagem ativa não muda.
Quando a externa de `msg_1` reutiliza o ID, ele passa como novo, o trabalho continua atribuído
a `codereview` e o Stop pede retro. O resultado foi igual em leitura contínua e com o estado
gravado antes e depois da colisão. ID novo preserva `codereview` e a variante com dono
conhecido na mensagem ativa rejeita o reuso. O caso não depende de ampliar a janela,
nem de fazer R5 ou R6 perder a marca de um ID **já consumido**.

**3.** Em dois repositórios temporários, `git -C <fixture> rev-parse --show-toplevel`
devolveu o diretório apontado por `GIT_WORK_TREE` quando as duas variáveis estavam definidas.
Removê-las devolveu a raiz da fixture. Isso confirma o mecanismo descrito em
`20-handoff-exec.md:136`, sem reexecutar a suíte contra o Git do runner. O Check do
checkpoint e o comando do handoff de execução já usam isolamento. A divergência está na
receita do plano, não no código ou na configuração do plugin.

## Incrementos de conserto (R<n>)

| R<n> | Achado | Check escrito no checkpoint |
|---|---|---|
| R7 | Achados 1 e 2, um lote MEDIUM. | Sonda desta rodada com `--expect` e dois testes de Stop com contagem obrigatória. |

Da raiz, a sonda abaixo, em `6f190e3`, saiu com rc 1. Por padrão, ela regrava o
JSON com as chaves da 0.4.0 a partir do mesmo corte. Para conferir com o hook anterior real,
exporte `git archive fe38d1f plugins/retrofit-watch` para um diretório temporário e passe
`--legado` com o caminho do script exportado, depois de `--expect`. As cinco divergências
foram reproduzidas com o estado efetivamente gravado pela 0.4.0 e com a fixture reduzida.
O `check-checkpoint.sh --check` validou as nove linhas. Em `--red`, o kit confirmou
que R7 imprime o vetor observado e diverge do esperado.

~~~bash
env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -c "$(sed -n '/^~~~python$/,/^~~~$/{ /^~~~/!p; }' docs/handoffs/20261125-retrofit-watch-atribuicao/40-review-r7.md)" --expect
~~~

Saída observada, com a contagem de revisões de `codereview` após cada caso.

~~~text
legado_linked=codereview:1 legado_missing=codereview:1 legado_empty=codereview:1
atual_linked=silêncio:0 atual_missing=silêncio:0 atual_empty=silêncio:0
legado_slash=graphify:0 legado_nova=graphify:0
continua_novo=codereview:1 continua_reuso=codereview:1 continua_dono=silêncio:0
retomada_novo=codereview:1 retomada_reuso=codereview:1 retomada_dono=silêncio:0
divergências: legado_linked, legado_missing, legado_empty, continua_reuso, retomada_reuso
~~~

~~~python
import argparse
import json

from test_retrofit_watch import StopTest, identified_load, skill_typed, tool

parser = argparse.ArgumentParser()
parser.add_argument("--expect", action="store_true")
parser.add_argument("--legado")
args = parser.parse_args()
failures = []


def stop(test, script=None):
    output = test.run_hook(script=script) if script else test.run_hook()
    path = test.w.data / "sessions/s1.json"
    state = json.loads(path.read_text(encoding="utf-8"))
    assert state["offset"] == test.w.transcript.stat().st_size
    assert not (test.w.data / "errors.log").exists()
    if output is None:
        return "silêncio", state
    text = output["hookSpecificOutput"]["additionalContext"]
    targets = [name for name in ("codereview", "graphify")
               if f"/retrofit-skill:retrofit-skill {name}`" in text]
    assert len(targets) == 1, text
    return targets[0], state


def counters(state):
    entry = state["skills"]["full:codereview"]
    return tuple(entry[key] for key in ("work", "friction", "reviews"))


def legacy(source, recovery=None, modern=False):
    test = StopTest()
    test.setUp()
    try:
        ours, external = test.identified_loads("msg_2")
        test.write(ours[:2], external, tool(), compact=True)
        state_path = test.w.data / "sessions/s1.json"
        if args.legado and not modern:
            out, before = stop(test, args.legado)
        else:
            # Campos do JSON que a 0.4.0 grava nesse corte, sem a marca introduzida no patch.
            out, before = stop(test)
            if not modern:
                old_fields = ("created", "offset", "skills", "current", "classified",
                              "pending", "done", "entrypoint")
                before = {key: before[key] for key in old_fields if key in before}
                state_path.write_text(json.dumps(before), encoding="utf-8")
        assert out == "silêncio" and before["current"] is None
        assert ("attribution_closed" in before) == modern
        assert counters(before) == (0, 0, 0)
        if source == "missing":
            del ours[2]["sourceToolUseID"]
        elif source == "empty":
            ours[2]["sourceToolUseID"] = ""
        test.write(ours[2:])
        if recovery == "slash":
            test.write(skill_typed("graphify", test.w.graphify))
        elif recovery == "nova":
            test.write(identified_load("graphify", test.w.graphify, "msg_3", "toolu_3"))
        test.write(tool(error=True))
        out, after = stop(test)
        label = ("atual" if modern else "legado") + "_" + (recovery or source)
        expected = "graphify" if recovery else "silêncio"
        if out != expected or counters(after) != counters(before) or (
                recovery is None and after["current"] is not None):
            failures.append(label)
        return f"{label}={out}:{counters(after)[2]}"
    finally:
        test.tearDown()


def collision(reuse, resume, owner=None):
    test = StopTest()
    test.setUp()
    try:
        ours, _ = test.identified_loads()
        original = identified_load("graphify", test.w.graphify, owner, "toolu_unowned")
        colliding = identified_load("nao-instalada", test.w.other_skill, "msg_2", "toolu_unowned")
        external = identified_load("superpowers:brainstorming", test.w.other_skill, "msg_1",
                                   "toolu_unowned" if reuse else "toolu_new")
        test.write(ours, original[:2])
        if resume:
            out, before = stop(test)
            assert out == "silêncio"
            assert "toolu_unowned" in before["skill_calls"]
            assert before["skill_calls"]["toolu_unowned"] == owner
        test.write(colliding[:2])
        if resume:
            out, middle = stop(test)
            assert out == "silêncio" and middle["skill_message_order"] == ["msg_1"]
            assert not middle["skill_correlation_lost"]
        test.write(external, tool(error=True))
        out, after = stop(test)
        label = ("retomada" if resume else "continua") + "_" + (
            "dono" if owner else "reuso" if reuse else "novo")
        expected = "silêncio" if reuse else "codereview"
        if out != expected or (reuse and (
                counters(after) != (0, 0, 0) or after["current"] is not None)):
            failures.append(label)
        return f"{label}={out}:{counters(after)[2]}"
    finally:
        test.tearDown()


print(*(legacy(source) for source in ("linked", "missing", "empty")))
print(*(legacy(source, modern=True) for source in ("linked", "missing", "empty")))
print(*(legacy("missing", recovery) for recovery in ("slash", "nova")))
for resume in (False, True):
    print(collision(False, resume), collision(True, resume), collision(True, resume, "msg_1"))
if args.expect and failures:
    raise SystemExit("divergências: " + ", ".join(failures))
~~~

## O que virou incremento

- **R7** — dois achados confirmados, ainda em `pending`. O Check exige silêncio e nenhum
  crédito nos dois falsos positivos, preserva o pedido para ID novo, o controle de dono
  conhecido, o encerramento em estado atual e a reativação por slash ou chamada nova.
- **R6** — fechado em `cd55517`. O Check R6 passou com `marca_apos_confirmacao=1` e
  `regressao=1`. Os testes de R5 e R6 detectaram seis degradações independentes em cópias
  temporárias. Subcasos vermelhos por variante: 10 ao perder a marca sem origem na poda, 3 ao
  não retirá-la no avanço, 3 ao omitir a mensagem que colidiu, 10 ao ignorar a marca vazia,
  2 ao ignorar a marca mista e 10 ao gravar só os donos conhecidos.

Linha registrada no checkpoint:

| R7 | Manter encerrada a atribuição já fechada na 0.4.0 e não reaproveitar ID sem origem após colisão e poda (r7, achados 1–2) | `env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -c "$(sed -n '/^~~~python$/,/^~~~$/{ /^~~~/!p; }' docs/handoffs/20261125-retrofit-watch-atribuicao/40-review-r7.md)" --expect && if o=$(env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -m unittest -q test_retrofit_watch.StopTest.test_legacy_closed_before_upgrade_ignores_delayed_metadata test_retrofit_watch.StopTest.test_unowned_pending_collision_survives_pruning 2>&1); then [[ "$o" == *"Ran 2 tests"* && "$o" == *"OK" ]] && printf 'regressoes=2\n'; else printf '%s\n' "$o" >&2; exit 1; fi` → `legado_linked=silêncio:0 legado_missing=silêncio:0 legado_empty=silêncio:0 atual_linked=silêncio:0 atual_missing=silêncio:0 atual_empty=silêncio:0 legado_slash=graphify:0 legado_nova=graphify:0 continua_novo=codereview:1 continua_reuso=silêncio:0 continua_dono=silêncio:0 retomada_novo=codereview:1 retomada_reuso=silêncio:0 retomada_dono=silêncio:0 regressoes=2` | pending | — |

## O que foi refutado

- O merge teria alterado a lógica ou as fixtures de Stop. A comparação com seu primeiro pai
  ficou vazia nos caminhos `plugins/retrofit-watch` e `e2e`. Os defeitos da rodada são
  reproduzíveis no código da missão.
- F1 ou R6 ainda estariam vermelhos nos seus próprios percursos. F1 retornou os três silêncios
  e R6 retornou o vetor esperado. Os Reds de R7 mudam o corte da atualização ou passam por
  uma pendência ainda não consumida.
- Cinco âncoras do backlog estariam fora do alvo. As linhas exatas mudaram, mas cada símbolo
  está na tolerância de dez linhas do kit. `check-todo.sh --check TODO.md` aprovou as
  36 entradas antes da atualização desta rodada.

## Achados fora de escopo

- O achado 3 foi registrado na seção aberta de `TODO.md`. É prosa histórica da missão.
  A evidência de execução usa a receita isolada já registrada no handoff.
- A janela de correlação não foi ampliada. O reuso após aposentadoria efetiva da mensagem e o
  metadado externo antigo permanecem em seus itens abertos de `TODO.md`. As medidas
  históricas sem saída preservada também já têm item. Não foram duplicados.

## Pendências / Decisions for a Human

O mantenedor decide se retoma a missão após o platô. R7 está registrado para a execução em TDD
caso haja retomada. O merge continua reservado ao mantenedor.

## Boot da próxima fase

Se o mantenedor retomar, execute a sonda de R7 em Red. Escreva os dois testes nomeados no
checkpoint, um para cada condição. Confirme o encerramento persistido antes da migração e
os cortes em disco antes e depois da colisão. Nos casos negativos, exija offset completo,
ausência de `errors.log` e nenhum incremento futuro de trabalho, atrito ou revisões.
Mantenha os controles positivos, a poda sem troca de mensagem ativa e os limites da janela.
Repita os oito Checks anteriores e o `TEST_CMD` com Git isolado.

### Recommended Actions

**Must Fix (CRITICAL)**

_Nenhum._

**Should Fix (HIGH)**

_Nenhum._

**Consider Fixing (MEDIUM/LOW)**

- Executar R7 em TDD se houver retomada. A nota geral B e o platô permanecem.
- Triar a receita histórica do plano e a rastreabilidade das medições nos itens do backlog.

**Deferred (form)**

_Nenhum._

_Custo da revisão: skill 2.30.2 instalada, chamada pela cópia 2.27.38. A instalada acrescenta a verificação de prosa por unidades e altera o fechamento de deltas, não aplicados neste full, além da nota de documentação separada. Quatro agentes gpt-6.1-terra por arquivo ou grupo, zero verificadores, varredura inline. Agentes leram 17 arquivos, com 2–4 chamadas informadas cada. Seis variantes temporárias. Custo monetário não medido. No Claude Code, `/reload-plugins` pode alinhar a cópia carregada à instalada._
