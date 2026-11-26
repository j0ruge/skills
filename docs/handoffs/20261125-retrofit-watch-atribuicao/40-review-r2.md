---
missao: 20261125-retrofit-watch-atribuicao
fase: REVIEW
rodada: 2
status: done
sessao: 01a2158e-1e04-72c3-a71b-d314eefe8316
data: 2026-11-25 22:59
gate: "TEST_CMD em b020b42, árvore inicialmente limpa e Git isolado, rc 0. Adaptadores e catálogo válidos, 154 testes da loja (3 pulados), 75 do hook, versão 0.4.1. I1, F1 e os quatro testes de R1 verdes. R2 pending por duas falhas reproduzidas. Code Quality (Zen), Error Handling e Test Coverage continuam B. Performance caiu de A para B pelo crescimento do estado. O laço de revisão para nesta regressão."
reviewed_head: b020b425ed8a967c4cc9c40a542a54968006dd7f
---

# Review — rodada r2 — Atribuição da retrofit-watch por mensagem

## TL;DR

Os quatro casos de R1 passaram no delta de `eb44360`. I1 e F1 também passaram.
A revisão encontrou duas regressões novas. A confirmação antiga pode descartar o vínculo mais novo e tentativas já falhas incham o estado.
As duas entram em `R2`. A nota geral é B e Performance caiu de A para B. Nenhum código ou teste foi alterado nesta rodada.

## Escopo e medidas

Rodada DELTA da skill `codereview:codereview base=08f09a14c68b54b05cfe9f1d5c2f988eee32e8af`, até `b020b425ed8a967c4cc9c40a542a54968006dd7f`. Três commits, oito caminhos no inventário. `eb44360` é o único commit que tocou o plugin. Um script de produção, um arquivo de testes e cinco artefatos de documentação foram analisados. `checkpoint-notas.md` ficou fora da leitura e da varredura de conteúdo. O handoff de QA serviu de controle anterior para F1, sem ampliar a inspeção de código além do delta.

### Detecção de segredos

| Resultado | Arquivos | Linhas adicionadas | Ferramentas | Erros |
|---|---:|---:|---|---:|
| PASS, 0 achados | 7 | 362 | `regex`, `gitleaks` | 0 |

### Verificações em `b020b42`

| Medida | Resultado |
|---|---|
| `env -u GIT_DIR -u GIT_WORK_TREE PYTHONDONTWRITEBYTECODE=1 bash -c 'source .sdd/config.sh && eval "$TEST_CMD"'` | rc 0. Adaptadores e catálogo válidos, 154 testes da loja (3 pulados), 75 testes do hook e validador de versões com 0.4.1. |
| Check de F1 em `checkpoint.md` | rc 0. Um teste, três variantes silenciosas. A sonda de I1 devolveu `1 0 1 0 0 1`. |
| Sonda e grupo de testes do Check de R1 em `checkpoint.md` | rc 0. Todas as 12 saídas intermediárias esperadas e quatro testes nomeados. |
| `env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -m unittest -q test_auto_docs.ReleaseTest.test_the_four_places_agree_at_0_4_0_or_later` | rc 0, 1 teste de release. |
| `bash /home/joruge/repos/sdd_agents/tests/check-todo.sh --check TODO.md --allow-empty --baseline main` | Na árvore inicial, rc 0, nenhuma violação nova e uma herdada. |
| `bash /home/joruge/repos/sdd_agents/tests/check-checkpoint.sh --red docs/handoffs/20261125-retrofit-watch-atribuicao/checkpoint.md --only R2` | rc 0. Um Check executado. O validador confirmou o Red pelos dois alvos indevidos e pelo crescimento previsto. |

### Cobertura, documentação e código morto

O único arquivo de produção tem testes atualizados. A atribuição e a leitura incremental foram exercitadas com subprocessos, estado em disco e transcript sintético, sem abertura do Claude Code ou teste em Windows. A trava e a escrita atômica não mudaram. Confirmação de carga e descarte de vínculo agora dividem a decisão dentro de `_watch`, onde a ordem dos eventos importa. O novo parâmetro do método tem um chamador que passa o argumento e quatro que mantêm o default. A busca pela interface anterior não encontrou chamada incompatível, nem símbolo introduzido ou órfão no delta. A varredura de código morto preexistente não foi feita. A verificação delegada leu 21 unidades de prosa em três arquivos. Os checks e o relatório histórico com código foram analisados em linha.


## Nota da rodada

### Overall Grade

| Criterion | Grade | Rationale |
|-----------|-------|-----------|
| Code Quality (Zen) | B | A limpeza nova trata a confirmação de uma chamada mais antiga como razão para descartar uma chamada posterior já conhecida. A retro saiu para o alvo errado em leitura contínua e retomada. |
| Type Safety | A | Os IDs continuam validados como strings antes da consulta. O delta conserva os campos legados e nenhum dos Reds depende de tipo inválido ou exceção. |
| Error Handling | B | O encerramento legado ficou correto, mas um resultado de erro explícito não aposenta o vínculo que o delta passa a reter. |
| Security | A | A varredura do delta analisável não encontrou segredos. O hook não ganha destino de escrita, execução de comando ou rede com esta mudança. |
| Performance | B | Sem nenhuma carga reconhecida, 10, 100 e 1.000 tentativas falhas deixaram 10, 100 e 1.000 vínculos no JSON que o Stop lê e regrava. A base mantinha um. |
| Test Coverage | B | Os quatro testes novos saem de Red para Green e sete mutações seletivas foram detectadas. A suíte continua verde nos dois casos novos reproduzidos fora dela. |
| Documentation | B | Release em 0.4.1 e evidência executável coerente para os Checks antigos. A missão ainda usa o HEAD para descrever o Red histórico e a referência antiga do backlog segue deslocada. |
| **Overall** | **B** | O conserto de R1 é real, mas o delta pode atribuir trabalho à skill errada e reter tentativas encerradas durante a sessão. |

## Achados da rodada

| # | Severidade | Achado | Onde |
|---|---|---|---|
| 1 | MEDIUM | Ao confirmar a carga mais antiga, a limpeza descarta o vínculo de uma carga posterior que ainda aguarda confirmação por caminho. | `plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py:483`–`486` |
| 2 | MEDIUM | Tentativas que retornam erro e nunca carregam uma skill ficam no mapa persistido. O estado cresce enquanto nenhuma carga reconhecida interrompe a sequência. | `plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py:601`–`606` |
| 3 | LOW | Reaproveitar um ID de chamada de outra mensagem ainda pode valer como prova de mesma mensagem. É uma limitação anterior, fora de R2. | `plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py:600` |

**#1.** Dois `Skill` sem prefixo, `coderabbit-pr` em `msg_1` e `graphify` em `msg_2`, têm IDs distintos e resultados de sucesso. Ambos os registros de chamada e resultado chegam antes dos metadados. Ao ler primeiro o metadado de `msg_1`, `_watch` retém somente vínculos daquela mensagem. O `sourceToolUseID` de `msg_2` vira desconhecido, sua confirmação é ignorada e um Bash com erro após as duas cargas dispara `codereview`. Sem o metadado antigo, ou com ele depois da confirmação de `graphify`, sai `graphify`. Em `08f09a1`, `graphify` saiu nas seis combinações. O teste deve preservar a confirmação nova sem permitir que uma confirmação velha, lida por último, reassuma a atribuição.

**#2.** A sonda em três Stops registrou `(tentativas, vínculos, bytes)` de `(10, 10, 527)`, `(100, 100, 3138)` e `(1000, 1000, 29239)` em `b020b42`. Em `08f09a1`, mediu `(10, 1, 275)`, `(100, 1, 276)` e `(1000, 1, 277)`. Os Stops leram até o fim do transcript e ficaram em silêncio em ambas as versões. Cada chamada era para uma skill inexistente, em mensagem própria, com `tool_result.is_error=true` e sem metadado. O aumento é de estado, não de tempo de produção medido. Distinguir a tentativa com erro confirmado da chamada que ainda pode produzir metadado preserva o positivo de R1.

**#3.** Em três Stops, a sonda consumiu `toolu_a` em `msg_1`, carregou a monitorada via `toolu_b` em `msg_2` e intercalou uma externa em `msg_2`. Tanto o controle com `toolu_c` quanto a versão com `toolu_a` emitiram `codereview` em `08f09a1` e `b020b42`. O teste de R1 permanece válido para reutilização ainda na mensagem ativa. O caso entre mensagens depende da regra de duplicidade já existente e fica no backlog, sem expandir a correção ou prometer retenção global de IDs.

### Sonda de R2

Da raiz, rode o Check de R2 em `checkpoint.md`. Cada trio mostra os controles sem metadado antigo, com o metadado antigo antes da confirmação nova e com ele depois. A última linha mede a variação do JSON de estado nos três Stops sem cargas. A tolerância de 1 KiB exclui o crescimento observado, sem exigir um formato específico de JSON.

Em `b020b42`, a saída foi:

~~~text
continua=graphify,codereview,graphify
retomada=graphify,codereview,graphify
falhas=cresce
~~~

Para repetir a comparação com `08f09a1`, extraia o script daquele commit com `git show 08f09a14c68b54b05cfe9f1d5c2f988eee32e8af:plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py` para um arquivo em um diretório temporário. Passe o caminho como argumento ao Python depois do código da sonda e acrescente `--medir` para ver as contagens e os bytes. Para também repetir o controle do achado 3, acrescente `--reuso`.

~~~python
import json
import sys
from contextlib import contextmanager
from pathlib import Path

import test_retrofit_watch as fixture


@contextmanager
def journey():
    test = fixture.StopTest()
    test.setUp()
    try:
        yield test
    finally:
        test.tearDown()


def load(name, path, message, call_id):
    call, result, meta = fixture.skill_via_tool(name, path)
    call["message"]["id"] = message
    call["message"]["content"][0]["id"] = call_id
    result["message"]["content"][0]["tool_use_id"] = call_id
    meta["sourceToolUseID"] = call_id
    return call, result, meta


def append(test, *groups):
    with test.w.transcript.open("a", encoding="utf-8") as stream:
        for group in groups:
            for row in group:
                stream.write(json.dumps(row, separators=(",", ":")) + "\n")


def stop(test, script):
    result = test.run_hook(script=script)
    state_path = test.w.data / "sessions/s1.json"
    data = json.loads(state_path.read_text(encoding="utf-8"))
    assert data["offset"] == test.w.transcript.stat().st_size
    if result is None:
        target = "silêncio"
    else:
        context = test.context_of(result)
        targets = [arg for arg in ("codereview", "graphify")
                   if f"/retrofit-skill:retrofit-skill {arg}`" in context]
        assert len(targets) == 1, context
        target = targets[0]
    return target, data, state_path.stat().st_size


def ordered(script, split, order):
    with journey() as test:
        older = load("coderabbit-pr", test.w.mkt_skill, "msg_1", "toolu_a")
        newer = load("graphify", test.w.graphify, "msg_2", "toolu_b")
        append(test, older[:2], newer[:2])
        if order != "sem":
            append(test, older[2:] if order == "antes" else newer[2:])
        if split:
            assert stop(test, script)[0] == "silêncio"
        last = older if order == "depois" else newer
        append(test, last[2:], fixture.tool(error=True))
        return stop(test, script)[0]


def failed_calls(script):
    with journey() as test:
        observations = []
        steps = (10, 100, 1000)
        for start, end in zip((0, *steps), steps):
            for index in range(start, end):
                call, result, _ = load("nao-instalada", test.w.other_skill,
                                       f"msg_{index:05}", f"toolu_f{index:05}")
                result["message"]["content"][0].update(
                    content="Unknown skill: nao-instalada", is_error=True)
                append(test, [call, result])
            target, state, size = stop(test, script)
            assert target == "silêncio" and not state["skills"]
            observations.append((end, len(state.get("skill_calls", {})), size))
        return observations


def duplicate(script, duplicate_id):
    with journey() as test:
        first = load("codereview:coderabbit-pr", test.w.mkt_skill, "msg_1", "toolu_a")
        second = load("codereview:coderabbit-pr", test.w.mkt_skill, "msg_2", "toolu_b")
        external = load("superpowers:brainstorming", test.w.other_skill, "msg_2",
                        "toolu_a" if duplicate_id else "toolu_c")
        for rows in (first, second):
            append(test, rows)
            out, _, _ = stop(test, script)
            assert out == "silêncio"
        append(test, external, fixture.tool(error=True))
        out, _, _ = stop(test, script)
        print(f"reuso_entre_mensagens={duplicate_id} alvo={out}")


script = Path(sys.argv[1]) if len(sys.argv) > 1 else fixture.SCRIPT
for split in (False, True):
    label = "retomada" if split else "continua"
    print(f"{label}=" + ",".join(ordered(script, split, order)
                                 for order in ("sem", "antes", "depois")))
observations = failed_calls(script)
sizes = [size for _, _, size in observations]
print("falhas=estavel" if max(sizes) - min(sizes) <= 1024 else "falhas=cresce")
if "--medir" in sys.argv:
    print(observations)
if "--reuso" in sys.argv:
    for reused in (False, True):
        duplicate(script, reused)
~~~

## Incrementos de conserto (R<n>)

| R<n> | Achado | Check escrito no checkpoint |
|---|---|---|
| R2 | #1 e #2, ciclo de vida dos vínculos | Seis variações em Stop real devem emitir `graphify`. Após 10, 100 e 1.000 erros, sem carga ou retro, o estado não deve crescer proporcionalmente às tentativas. |

## O que virou incremento

| R2 | Preservar vínculos de cargas posteriores e aposentar tentativas que falharam (r2, achados 1–2) | `env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -c "$(sed -n '/^~~~python$/,/^~~~$/{ /^~~~/!p; }' docs/handoffs/20261125-retrofit-watch-atribuicao/40-review-r2.md)"` → `continua=graphify,graphify,graphify retomada=graphify,graphify,graphify falhas=estavel` | pending | — |

- `R1` — fechado em `eb44360` para os quatro cenários de r1. A sonda da rodada anterior devolveu todas as linhas esperadas, com silêncio no legado e na chamada duplicada, `graphify` no slash intercalado e `codereview` após a tentativa sem carga. Os quatro testes do delta falharam por asserção com o script de `08f09a1` em cópia temporária e passaram no HEAD.
- `R2` — o executor deve incorporar duas regressões à suíte de Stop, uma para a ordem de confirmação em leitura contínua e retomada e outra para o crescimento por chamadas que já falharam. Preservar os Checks de I1, F1 e R1. Esta revisão apenas reproduziu e registrou os achados.

## O que foi refutado

- **R1 teria apenas deslocado os Reds, com os quatro testes já verdes na base.** Os quatro falharam por asserção com o script da base e passaram com o do HEAD. Remover isoladamente a guarda de legado encerrado, a marca de consumo, o `get` não destrutivo, a preservação do slash, o adiamento da limpeza, a marca de tentativa observada ou a aposentadoria de vínculos obsoletos derrubou o sensor escolhido em 7 de 7 variantes temporárias. A última mutação derrubou o controle de F1 com ID vinculado. Simplesmente deixar de limpar o mapa não serve como correção de R2.
- **A falta de uma saída salva torna inválidos o gate e o teste de release do EXEC.** O template exige comando inteiro e hash, não um arquivo de saída. O handoff os fornece. O reteste da suíte e o de release passaram em `b020b42`, sem alteração no plugin desde `eb44360`. Isso corrobora o resultado, sem alegar nova execução da suíte naquele hash histórico.
- **A contagem de quatro Reds e 18 mutações precisa de um log adicional no repositório.** A evidência da execução sobre as 18 está na nota inline do boot. O reteste independente executou os quatro Reds em `08f09a1` com os testes atuais e mediu sete mutações próprias. Não recontou as 18 da execução. A ausência de um arquivo de saída adicional não contradiz o handoff nem viola seu template.

## Achados fora de escopo

- #3 — `TODO.md`, item “ID de chamada reaproveitado entre mensagens passa por vínculo novo”. O defeito já existe no base e a regra de duplicidade que o admite não mudou.
- r1 #5 e #6 — continuam nos dois itens existentes de `TODO.md`. A frase de `00-missao.md` e a referência a `CHANGELOG.md:66` não foram corrigidas neste delta. A fonte é a mesma missão e não ganha nova entrada de recorrência.

## Pendências / Decisions for a Human

O critério de parada do laço foi atingido pela queda de Performance, embora os quatro casos de R1 tenham sido corrigidos. R2 registra o caminho de conserto e esta sessão não abre outra rodada nem força aprovação. A retomada da revisão após essa regressão fica para decisão do mantenedor.

### Recommended Actions

**Must Fix (CRITICAL)**

_Nenhum._

**Should Fix (HIGH)**

_Nenhum._

**Consider Fixing (MEDIUM/LOW)**

- Executar R2 em TDD. Separar confirmações antigas e novas e aposentar apenas tentativas comprovadamente falhas, mantendo os controles de I1, F1 e R1.
- Manter o caso de reuso entre mensagens no backlog, com controle negativo e positivo em qualquer solução posterior.

**Deferred (form)**

- Manter em backlog os dois itens de documentação de r1.

**Outside scope (tracker)**

- R1 #5 e #6 e r2 #3 estão vinculados na seção de escopo. O verificador não cortou outras unidades.

_Custo da revisão: skill solicitada 2.27.38, com passos divergentes de delta e verificação da instalada 2.30.2. Código, testes, reprodução e varredura em linha. Uma verificadora `gpt-6.1-terra`, 21 unidades, 11 chamadas informadas, retorno completo. Sete mutações próprias em cópias temporárias. Custo monetário não medido._
