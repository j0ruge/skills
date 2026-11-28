---
missao: 20261125-retrofit-watch-atribuicao
fase: REVIEW
rodada: 1
status: done
sessao: 01a21579-7203-7cb1-b48d-c253ebd1f664
data: 2026-11-25 22:38
gate: "TEST_CMD em 08f09a1 com Git isolado e árvore inicialmente limpa devolveu rc 0. Loja: 154 testes e 3 pulados. Hook: 71 testes. F1 e vetor I1 verdes. Quatro falhas reproduzidas ficam no lote R1 pending. Code Quality, Error Handling e Test Coverage não passaram."
reviewed_head: 08f09a14c68b54b05cfe9f1d5c2f988eee32e8af
---

# Review — rodada r1 — Atribuição da retrofit-watch por mensagem

## TL;DR

A revisão completa confirmou quatro defeitos de atribuição e registrou o lote `R1` como `pending`.
A sonda de I1 manteve `1 0 1 0 0 1`, F1 ficou em silêncio e a suíte configurada passou.
Nota geral B. Dois achados de documentação foram ao backlog, sem alteração em código ou testes.

## Escopo e medidas

Rodada FULL de `e45db9e…08f09a1` contra `main`, com 8 commits e 16 caminhos no inventário. Foram analisados o hook, seus dois arquivos de teste, os dois manifestos e a documentação modificada. O conteúdo de `checkpoint-notas.md` não foi aberto e `30-handoff-qa.md` entrou somente pelo resumo, boot inlinado e histórico Git, conforme o mandato. O último commit do handoff de QA (`08f09a1`) descende de `c704301`.

### Detecção de segredos

| Resultado | Arquivos | Linhas adicionadas | Ferramentas | Erros |
|---|---:|---:|---|---:|
| PASS, 0 achados | 14 | 556 | `regex`, `gitleaks` | 0 |

A varredura de linhas adicionadas respeitou as duas exclusões de leitura acima. O inventário e os hashes de commit abrangem os 16 caminhos.

### Verificações em `08f09a1`

| Medida | Resultado |
|---|---|
| `source .sdd/config.sh && env -u GIT_DIR -u GIT_WORK_TREE PYTHONDONTWRITEBYTECODE=1 bash -c "$TEST_CMD"` | rc 0. Adaptadores e catálogo válidos, loja com 154 testes e 3 pulados, módulo com 71 testes, validador confirmou 0.4.1. |
| Check completo de `F1` em `checkpoint.md` | rc 0. Jornada de 1 teste com 3 variantes silenciosas no segundo Stop e sonda de I1 `1 0 1 0 0 1`. |
| `env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -m unittest test_auto_docs.ReleaseTest.test_the_four_places_agree_at_0_4_0_or_later` | 1 teste, rc 0. Manifesto, catálogo, README, metadado da skill e CHANGELOG em 0.4.1. |
| `env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -m unittest -v test_retrofit_watch.StopTest.test_typed_slash_can_start_new_attribution_after_external_skill test_retrofit_watch.StopTest.test_legacy_state_resumes_at_offset_and_keeps_history test_retrofit_watch.StopTest.test_shared_call_id_is_not_proof_of_same_message test_retrofit_watch.StopTest.test_same_message_skill_name_keeps_attribution_before_metadata test_retrofit_watch.StopTest.test_path_can_exclude_the_same_call_recognized_by_plugin_name` | 5 testes, rc 0. Os controles de slash, retomada, ID duplicado ainda pendente, classificação pelo nome e exclusão via caminho seguem verdes. |

O hook alterado tem testes atualizados (1 de 1 arquivo de produção). A trava e a escrita atômica do estado não mudaram. A varredura de símbolos não encontrou código morto introduzido ou órfão, e não fez o inventário de dívida preexistente. A reprodução usa o hook em subprocesso e estado real em disco, com transcript sintético. Não houve smoke em instalação Claude Code ou Windows.

## Nota da rodada

### Overall Grade

| Criterion | Grade | Rationale |
|-----------|-------|-----------|
| Code Quality (Zen) | B | A correlação confunde tentativa com carga e esquece IDs já observados. Os quatro efeitos na atribuição foram reproduzidos. |
| Type Safety | A | O delta valida o tipo de IDs do transcript antes de usá-los como chaves e mantém os tipos existentes no JSON da 0.4.0. Os erros observados são de origem e ordenação. |
| Error Handling | B | O fallback legado trata ID sem correspondência como carga nova depois do encerramento. Uma tentativa de carga que falha também invalida um vínculo ainda necessário. |
| Security | A | A varredura do delta permitido não encontrou segredos. A mudança não abre novos destinos de escrita, executáveis ou superfícies de rede. |
| Performance | A | A leitura continua incremental, com classificação por caminho em cache e consulta direta dos vínculos. O delta não acrescenta processos externos à correlação. |
| Test Coverage | B | O arquivo alterado tem regressões na suíte, mas F1 e os testes novos não exercitam as quatro ordens ou condições reproduzidas nesta rodada. |
| Documentation | B | A versão 0.4.1 está sincronizada, mas o registro da missão apresenta o Red histórico como se fosse o estado atual e há uma âncora deslocada. |
| **Overall** | **B** | A métrica original e a jornada de QA passam. Quatro casos de borda contrariam o contrato e voltam à execução em um lote com sensores próprios. |

## Achados da rodada

| # | Severidade | Achado | Onde |
|---|---|---|---|
| 1 | MEDIUM | Um ID não vazio sem vínculo em estado legado reabre a atribuição encerrada. | `plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py:612` |
| 2 | MEDIUM | Um ID de chamada reutilizado após consumo volta a valer como prova de mesma mensagem. | `plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py:594`, `plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py:613` |
| 3 | MEDIUM | Metadado externo atrasado apaga um slash explícito mais novo que ainda aguarda seu caminho. | `plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py:492`, `plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py:618` |
| 4 | MEDIUM | Uma tentativa posterior de chamar uma skill desconhecida, sem carga, invalida o vínculo pendente de uma monitorada. | `plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py:595`, `plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py:614` |
| 5 | MEDIUM | O documento de missão chama o Red histórico de estado do HEAD e inclui aprovação já registrada entre as pendências. | `docs/handoffs/20261125-retrofit-watch-atribuicao/00-missao.md:76` |
| 6 | LOW | A entrada 0.4.1 desloca para fora da tolerância a âncora de uma pendência da 0.4.0. | `TODO.md:174`, `plugins/retrofit-watch/CHANGELOG.md:78` |

**#1.** O primeiro Stop leu as duas chamadas com a 0.4.0 e persistiu `current=null`. O Stop com 0.4.1 leu primeiro o metadado externo, que encerrou a atribuição, e só depois o metadado antigo da monitorada. Com `sourceToolUseID=toolu_1` e nenhum mapa capaz de resolvê-lo, saiu `codereview` e `reviews` passou de 0 a 1. A mesma sequência com estado atual e os controles legado com ID ausente ou vazio ficaram em silêncio. O problema não é o offset ou o contador legado, e sim o tratamento do ID desconhecido quando `skill_message` ainda é `None`.

**#2.** A primeira externa da mesma mensagem usou `toolu_2` e seu metadado foi consumido no primeiro Stop. Uma segunda externa diferente veio em outro registro da mesma mensagem e reutilizou `toolu_2`. A verificação de duplicidade só vê o mapa de pendências e aceita esse ID como novo. Tanto o controle com `toolu_3` quanto o caso ambíguo emitiram `codereview`. Só o distinto deveria preservar. O caso existente de ID compartilhado antes do consumo não detecta essa variante.

**#3.** Após uma externa posterior encerrar a atribuição por nome, o usuário digitou `/graphify`. A confirmação por caminho da externa anterior chegou entre a linha do slash e o metadado de `graphify`. O segundo Stop limpou `pending_slash` e o terceiro ficou silencioso. Sem a confirmação atrasada da externa, o terceiro Stop emitiu `graphify`. A perda é da carga explícita mais nova, não do crédito já acumulado.

**#4.** `Skill("coderabbit-pr")` sem prefixo de plugin depende do caminho para ser classificada. A chamada pendia entre Stops. Uma tentativa em outra mensagem chamou `nao-instalada` e retornou erro sem metadado de carga. Ela não foi reconhecida como externa, mas a troca de `skill_message` descartou o vínculo anterior mesmo assim. Com trabalho após o metadado válido da monitorada, o controle emitiu `codereview` e o caso com tentativa falha ficou silencioso. A validade do vínculo anterior não deveria depender de uma tentativa que não carregou outra skill.

**#5.** A aprovação consta no frontmatter e em `aceite-do-plano.md:3`. A sonda vermelha era de `e45db9e`, enquanto I1 está `done` em `682cd3d` e o Check passou em `08f09a1`. É deriva de prosa, sem efeito no sensor.

**#6.** A inserção de 12 linhas deslocou a ocorrência de `push` da linha 66 para a 78. `bash /home/joruge/repos/sdd_agents/tests/check-todo.sh --check TODO.md --allow-empty` reportou a âncora fora do alvo. Com `--baseline main` o linter retornou 0 e classificou a violação como herdada porque o item já existia. A pendência antiga é sobre o texto de release, não sobre o deslocamento da referência.

### Sonda da rodada

Da raiz, rode `env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -c "$(sed -n '/^~~~python$/,/^~~~$/{ /^~~~/!p; }' docs/handoffs/20261125-retrofit-watch-atribuicao/40-review-r1.md)"` em `08f09a1`. A saída reproduzida está abaixo. Para conferir a origem do estado legado com a versão anterior real, extraia `env -u GIT_DIR -u GIT_WORK_TREE git show e45db9ecd846af4ddf7ae8003c190ea07e078b3e:plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py` para um arquivo temporário e passe o caminho como argumento ao Python após o código. O Red também se reproduz com as chaves legadas preparadas pela própria sonda, sem depender do Git histórico.

~~~text
atual linked silêncio reviews=0
atual missing silêncio reviews=0
atual empty silêncio reviews=0
legado linked codereview reviews=1
legado missing silêncio reviews=0
legado empty silêncio reviews=0
distinto codereview
duplicado codereview
slash_controle graphify
slash_intercalado silêncio
carga_por_caminho codereview
tentativa_sem_carga silêncio
~~~

~~~python
import json
import sys
from contextlib import contextmanager
from pathlib import Path

import test_retrofit_watch as f

@contextmanager
def journey():
    test = f.StopTest()
    test.w = f.World()
    try:
        yield test
    finally:
        test.w.cleanup()

def append(test, *groups):
    with test.w.transcript.open("a", encoding="utf-8") as stream:
        for group in groups:
            for row in group:
                stream.write(json.dumps(row, separators=(",", ":")) + "\n")

def stop(test, script=f.SCRIPT):
    result = test.run_hook(script=script)
    saved = json.loads((test.w.data / "sessions/s1.json").read_text(encoding="utf-8"))
    assert saved["offset"] == test.w.transcript.stat().st_size
    if result is None:
        return "silêncio", saved
    text = test.context_of(result)
    targets = [name for name in ("codereview", "graphify")
               if f"/retrofit-skill:retrofit-skill {name}" in text]
    assert len(targets) == 1, text
    return targets[0], saved

baseline = Path(sys.argv[1]) if len(sys.argv) > 1 else None

for legacy in (False, True):
    for source in ("linked", "missing", "empty"):
        with journey() as test:
            monitored, external = test.identified_loads("msg_2")
            if source == "missing":
                monitored[2].pop("sourceToolUseID")
            if source == "empty":
                monitored[2]["sourceToolUseID"] = ""
            append(test, monitored[:2], external[:2])
            first, before = stop(test, baseline if legacy and baseline else f.SCRIPT)
            assert first == "silêncio" and before["current"] is None
            assert before["skills"]["full:codereview"]["work"] == 0
            if legacy and baseline is None:
                old = {k: before[k] for k in ("offset", "skills", "current", "classified", "pending", "done")}
                (test.w.data / "sessions/s1.json").write_text(json.dumps(old), encoding="utf-8")
            if legacy and baseline:
                assert "skill_message" not in before
            append(test, external[2:], monitored[2:], f.tool(error=True))
            second, after = stop(test)
            print(f"{'legado' if legacy else 'atual'} {source} {second} reviews={after['skills']['full:codereview']['reviews']}")

for duplicate in (False, True):
    with journey() as test:
        monitored, external = test.identified_loads()
        append(test, monitored, external)
        first, before = stop(test)
        assert first == "silêncio" and before["current"] == "full:codereview"
        new_skill = f.make_skill(test.w.other_skill.parent, "writing-plans")
        new_external = f.skill_via_tool("superpowers:writing-plans", new_skill)
        call_id = "toolu_2" if duplicate else "toolu_3"
        new_external[0]["message"]["id"] = "msg_1"
        new_external[0]["message"]["content"][0]["id"] = call_id
        new_external[1]["message"]["content"][0]["tool_use_id"] = call_id
        new_external[2]["sourceToolUseID"] = call_id
        append(test, new_external, f.tool(error=True))
        second, _ = stop(test)
        print(f"{'duplicado' if duplicate else 'distinto'} {second}")

for late_external in (False, True):
    with journey() as test:
        monitored, external = test.identified_loads("msg_2")
        slash = f.skill_typed("graphify", test.w.graphify)
        append(test, monitored, external[:2])
        first, before = stop(test)
        assert first == "silêncio" and before["current"] is None
        append(test, slash[:1], *([external[2:]] if late_external else []))
        middle, _ = stop(test)
        assert middle == "silêncio"
        append(test, slash[1:], f.tool(error=True))
        second, _ = stop(test)
        print(f"{'slash_intercalado' if late_external else 'slash_controle'} {second}")

for failed_attempt in (False, True):
    with journey() as test:
        monitored, _ = test.identified_loads()
        monitored[0]["message"]["content"][0]["input"]["skill"] = "coderabbit-pr"
        missing = f.skill_via_tool("nao-instalada", test.w.other_skill)
        missing[0]["message"]["id"] = "msg_2"
        missing[1]["message"]["content"][0].update(content="Unknown skill: nao-instalada", is_error=True)
        append(test, monitored[:2], *([missing[:2]] if failed_attempt else []))
        first, before = stop(test)
        assert first == "silêncio" and before["current"] is None
        append(test, monitored[2:], f.tool(error=True))
        second, _ = stop(test)
        print(f"{'tentativa_sem_carga' if failed_attempt else 'carga_por_caminho'} {second}")
~~~

## Incrementos de conserto (R<n>)

| R<n> | Achado | Check escrito no checkpoint |
|---|---|---|
| R1 | #1–#4, lote de correlação e encerramento | Quatro testes nomeados em `StopTest` e a sonda de terminal acima, com a saída esperada registrada no `checkpoint.md`. |

## O que virou incremento

- | R1 | Corrigir os achados de atribuição 1–4 da rodada r1, preservando os controles de I1 e F1 | `env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -c "$(sed -n '/^~~~python$/,/^~~~$/{ /^~~~/!p; }' docs/handoffs/20261125-retrofit-watch-atribuicao/40-review-r1.md)" && if o=$(env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -m unittest -q test_retrofit_watch.StopTest.test_legacy_closed_attribution_ignores_unknown_source test_retrofit_watch.StopTest.test_reused_consumed_call_id_stops_attribution test_retrofit_watch.StopTest.test_pending_slash_survives_older_external_metadata test_retrofit_watch.StopTest.test_failed_unknown_skill_keeps_pending_monitored_call 2>&1); then [[ "$o" == *"Ran 4 tests"* && "$o" == *"OK" ]] && printf 'regressoes=4\n'; else printf '%s\n' "$o" >&2; exit 1; fi` → `atual linked silêncio reviews=0 atual missing silêncio reviews=0 atual empty silêncio reviews=0 legado linked silêncio reviews=0 legado missing silêncio reviews=0 legado empty silêncio reviews=0 distinto codereview duplicado silêncio slash_controle graphify slash_intercalado graphify carga_por_caminho codereview tentativa_sem_carga codereview regressoes=4` | pending | — |

O validador do kit, com `--red docs/handoffs/20261125-retrofit-watch-atribuicao/checkpoint.md --only R1`, confirmou Red pelos quatro resultados divergentes da sonda. O lote exige silêncio sem novo crédito nos casos #1 e #2 e o alvo correto nos casos #3 e #4. Não há rodada anterior nem correção feita nesta sessão.

## O que foi refutado

- **O handoff EXEC quebraria o comando com aspas escapadas.** Nas linhas 26 e 55, o bloco Markdown contém aspas sem barra. A extração por `shlex.split` resultou em `source .sdd/config.sh && eval "$TEST_CMD"` e `bash -n` aceitou. A barra aparece no escalar YAML em aspas da linha 7 para representar o mesmo texto, não no comando do boot.
- **A âncora de `_watch` em `TODO.md:91` é inválida.** A linha indicada está em branco, mas o símbolo está na linha seguinte (`481`), dentro da tolerância de dez linhas do kit. O linter apontou só a outra âncora, a do CHANGELOG.
- **O BUG-01 já coberto pela QA continua vermelho com estado atual.** O Check de F1 repetiu os três silêncios. Na sonda adicional, mudar apenas de estado legado para atual manteve `reviews=0` e silêncio com o mesmo ID. O achado #1 restringe-se à retomada sem o mapa, em vez de repetir F1.
- **A tarefa que já tinha crédito o perde quando `current` é limpo.** O controle legado permanente passa e compara `skills`, `pending` e `done` pelos valores do JSON decodificado. O encerramento atinge o crédito futuro, não apaga esse histórico.

## Achados fora de escopo

- #5 — `TODO.md`, item “O registro da missão mistura a medição histórica com o estado atual”.
- #6 — `TODO.md`, item “A publicação do patch desloca uma âncora do backlog da retrofit-watch”.

## Pendências / Decisions for a Human

Nenhuma.

### Recommended Actions

- **CRITICAL** — nenhum.
- **HIGH** — nenhum.
- **MEDIUM** — fechar o lote `R1` em TDD. Distinguir ID desconhecido de ID resolvido, preservar a marca de duplicidade pelo tempo relevante, separar a confirmação atrasada de uma carga antiga do slash mais novo e invalidar vínculos só diante de um encerramento reconhecido.
- **MEDIUM/LOW de documentação** — manter os itens no backlog, sem reabrir a execução por prosa.

_Custo da revisão: `codereview` 2.27.38 no caminho solicitado, comparada à versão instalada 2.30.2. As mudanças de roteamento da versão instalada valem para delta, não para esta rodada FULL. Seis revisores por arquivo/grupo com `gpt-6.1-terra`, 13 leituras integrais e 2–11 chamadas por agente conforme seus retornos. Código, reprodução e varredura de código morto em linha. Sem medição de custo monetário._
