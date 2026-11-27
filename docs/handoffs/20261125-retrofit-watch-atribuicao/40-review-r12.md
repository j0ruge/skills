---
missao: 20261125-retrofit-watch-atribuicao
fase: REVIEW
rodada: 12
status: done
sessao: 01a21ed5-a00e-78a1-a3c7-23248939d6a4
data: 2026-11-27 18:13
gate: 'Em a07b8fdd1ef790aaa9ae268dab8d25243877fc0a, com árvore limpa, env -u GIT_DIR -u GIT_WORK_TREE PYTHONDONTWRITEBYTECODE=1 bash -c ''source .sdd/config.sh && eval "$TEST_CMD"'' → rc 0; 154 testes da loja (3 pulados), 113 do hook, adaptadores, catálogo e versões válidos. 13/13 Checks fechados bateram rc e stdout. A sonda de R12 saiu com rc 1 por reabertura indevida após o limite. Gate não passou em Code Quality (Zen), Error Handling e Test Coverage. Performance subiu de B para A.'
reviewed_head: a07b8fdd1ef790aaa9ae268dab8d25243877fc0a
---

# Review — rodada r12 — Atribuição da retrofit-watch por mensagem

Delta de `5506df4dd27b2bda8f19b0f47424a6cf0c3192a4` a
`a07b8fdd1ef790aaa9ae268dab8d25243877fc0a`, na branch
`fix/retrofit-watch-atribuicao-mesma-mensagem`. Um módulo Python, um arquivo de testes
e sete registros de documentação ou execução. A QA em `08f09a1` cobriu o
BUG-01 e o Check F1 voltou a exercitá-lo. O achado novo está no caminho de migração
alterado em `fb5e489`, não no fluxo que a QA já especificou.

## TL;DR

A suíte e os 13 Checks passaram. R11 fechou os dois casos anteriores.
Um registro de 2 MiB + 1 byte faz a retomada aceitar metadado atrasado e pedir retro indevida.
A base do delta rejeita o mesmo metadado sob o mesmo teto. R12 registra a regressão.
Nota geral B. Performance subiu para A. Nenhum código foi alterado.

## Nota da rodada

### Secrets Detection

**Status: PASS.** Pré-scan `regex` e `gitleaks` retornou 0 ocorrências e 0 erros.
O delta tem 9 caminhos e 500 linhas adicionadas. O comando usado foi
`git diff 5506df4dd27b2bda8f19b0f47424a6cf0c3192a4...HEAD --unified=0 | bash /home/joruge/.agents/skills/codereview/scripts/scan_secrets.sh`.

### Zen, cobertura e sincronização

- **Estado e erro.** O descarte de evidência parcial está correto. O problema é
  deixar o estado legado indistinguível de uma sessão sem encerramento quando a
  reconstrução termina no novo limite.
- **WITH_TESTS, 1/1 módulo.** `test_retrofit_watch.py` importa o módulo, mede a
  alocação e usa subprocessos com transcript e estado em disco. O caso novo
  é um par negativo e positivo no mesmo limite, com uma segunda variante após
  persistir a migração.
- **Documentação.** README, CHANGELOG e SKILL descrevem o teto e o avanço da
  primeira confirmação. A validação da versão 0.4.1 e o teste de release
  passaram. As duas ressalvas de sintaxe sugeridas no handoff foram refutadas
  pelos bytes das receitas.
- **Varredura de símbolos, Bucket A.** A constante nova é lida no limite de
  `readline`, a variável `previous` é consumida na poda e os dois métodos de teste
  são descobertos. Nenhuma interface foi renomeada. Nenhum órfão no delta.
  Bucket B fora de escopo.

### Overall Grade

| Criterion | Grade | Rationale |
|-----------|-------|-----------|
| Code Quality (Zen) | B | A primeira confirmação preserva a marca sem origem, mas o novo ramo de limite perde o encerramento legado que dependia da ordem. |
| Type Safety | A | Os cortes com estado legado, linhas binárias e IDs válidos ou ausentes funcionaram sem divergência de tipos. |
| Error Handling | B | Acima do limite, o fallback consome o delta, mas aceita um metadado antigo como se fosse carga nova. |
| Security | A | Pré-scan sem ocorrências ou erros. O delta não muda caminhos de saída, trava ou permissões do estado. |
| Performance | A | A célula R11 avançou o offset com 96 MiB em um registro sob teto de 256 MiB. A regressão durável também passou com pico abaixo de 6 MiB. |
| Test Coverage | B | As duas regressões de R11 passaram, mas a prova de registro grande usa slash fresco e não detecta reabertura por metadado atrasado. |
| Documentation | B | O limite e a versão estão documentados e verificados. A garantia contra metadado atrasado ainda não vale na retomada acima do limite. |
| **Overall** | **B** | R11 corrigiu a pressão de memória e a perda da marca. Uma regressão funcional na retomada ainda exige R12. |

## Achados da rodada

| # | Severidade | Achado | Onde |
|---|---|---|---|
| 1 | MEDIUM | O retorno ao atingir o limite de leitura reabre a atribuição depois de uma externa posterior que a 0.4.0 observou só pelo nome. O efeito persiste se houver um Stop entre a migração e o metadado atrasado. | `retrofit_watch.py:794–800` |

Na sonda, a 0.4.0 lê a chamada de `graphify` ainda sem caminho e a chamada
externa posterior, também sem caminho. Persiste `current=null`, `skills={}`
e `classified={}`, além do offset correto. Com o registro completo de 2 MiB,
o replay reconhece o encerramento. Com exatamente mais um byte, o retorno em
`recover_legacy_correlation` mantém só os defaults do estado salvo. Na ausência
de mensagem conhecida ou indicação de encerramento, `skill_path` trata o
`sourceToolUseID` atrasado como falta de origem compatível com a carga e
atribui o trabalho novo a `graphify`. O Stop emite a retro e registra uma review
indevida. Não há erro no log e o offset avança. O mesmo ocorre em outro Stop
depois que a migração já foi salva.

O controle da base aceita o mesmo prefixo acima do limite sob 256 MiB e mantém
silêncio. Na versão revisada, uma carga realmente iniciada no delta e um slash
explícito ainda emitem `graphify`. O sensor novo deve preservar esses dois
controles, sem importar vínculos parciais nem desfazer o limite de memória.

## Incrementos de conserto (R<n>)

| R<n> | Achado | Check escrito no checkpoint |
|---|---|---|
| R12 | Achado 1 | `env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -c "$(sed -n '/^~~~python$/,/^~~~$/{ /^~~~/!p; }' docs/handoffs/20261125-retrofit-watch-atribuicao/40-review-r12.md)" --expect && if o=$(env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -m unittest -q test_retrofit_watch.StopTest.test_legacy_oversized_replay_does_not_reopen_from_delayed_metadata 2>&1); then [[ "$o" == *"Ran 1 test"* && "$o" == *"OK" ]] && printf 'regressao=1\n'; else printf '%s\n' "$o" >&2; exit 1; fi` → `at_limit=silêncio above_delayed=silêncio above_delayed_resumed=silêncio above_fresh=graphify above_slash=graphify regressao=1` |

## O que virou incremento

| R12 | Impedir a reabertura por metadado atrasado quando a migração descarta um registro grande (r12, achado 1) | `env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -c "$(sed -n '/^~~~python$/,/^~~~$/{ /^~~~/!p; }' docs/handoffs/20261125-retrofit-watch-atribuicao/40-review-r12.md)" --expect && if o=$(env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -m unittest -q test_retrofit_watch.StopTest.test_legacy_oversized_replay_does_not_reopen_from_delayed_metadata 2>&1); then [[ "$o" == *"Ran 1 test"* && "$o" == *"OK" ]] && printf 'regressao=1\n'; else printf '%s\n' "$o" >&2; exit 1; fi` → `at_limit=silêncio above_delayed=silêncio above_delayed_resumed=silêncio above_fresh=graphify above_slash=graphify regressao=1` | pending | — |

R11 foi fechado em `fb5e489` para os dois casos registrados em r11. A célula
confirmou `marca_novo=1,1` e `marca_reuso=1,1`, manteve silêncio para ID
reaproveitado e pediu `codereview` para ID novo. Os quatro Stops de comparação
0.4.0 → 0.4.1 pediram `graphify` e avançaram o offset nos dois perfis de
prefixo sob teto de 256 MiB. As duas regressões duráveis rodaram com rc 0.
R10 repetiu o controle de avanço entre mensagens confirmadas e as sondas sem
vínculo, com vínculo e slash alheio. F1 e I1 voltaram ao vetor aprovado.

## O que foi refutado

- **R11 teria aspas escapadas que impedem copiar o Check.** A célula de
  `checkpoint.md:22` tem zero pares barra invertida e aspas. É idêntica byte a
  byte ao comando executado, com rc 0, stdout esperado e duas regressões
  executadas. Os dois `\n` pertencem aos formatos de `printf`.
- **A receita de suíte do handoff teria aspas literais no Bash.** Em
  `20-handoff-exec.md:27` e `:238` há zero pares barra e aspas na receita.
  As duas linhas contêm exatamente o comando executado nesta rodada com rc 0.
- **A retomada acima do limite ainda ficaria travada.** A regressão de 96 MiB
  avançou o offset em R11. Na sonda nova todos os offsets também chegaram ao
  fim do transcript, inclusive nas duas variantes com saída indevida. O defeito
  novo é atribuição incorreta, não falta de progresso.

## Achados fora de escopo

Nenhum achado novo para o backlog. Permanecem abertos os itens de âncoras e
de preservação das saídas históricas. Não foi feita uma nova medição das 16
mutações históricas de EXEC, e a recorrência na mesma missão não duplica o item.

## Pendências / Decisions for a Human

Nenhuma decisão de produto. Em relação a r11, `Performance` subiu de B para A
e os demais critérios não baixaram. Não houve platô. O gate ainda não passou
e R12 deixa o caso mínimo para EXEC.

## Evidências reproduzíveis

No HEAD revisado, o `TEST_CMD` rodou uma vez com o Git privado removido do
ambiente. A loja rodou 154 testes, com três pulos configurados. O hook rodou
113 testes sem falhas. O comando completo consta no campo `gate`.
O teste de release
`env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -m unittest test_auto_docs.ReleaseTest.test_the_four_places_agree_at_0_4_0_or_later`
rodou um teste com rc 0 no mesmo HEAD.

Os 13 comandos das linhas `done` de `checkpoint.md` rodaram da raiz em
`bash -c` com `GIT_DIR` e `GIT_WORK_TREE` removidos. O rc e o stdout
completo, normalizado só em espaços em branco, igualaram os valores de I1,
F1 e R1–R11. Não houve execução no host Claude Code nem no Windows.

Execute a sonda nova da raiz. Ela cria fixtures isoladas, roda o primeiro
Stop com a 0.4.0 de `fe38d1f` e limita os subprocessos de migração a 256 MiB.
`--base` troca só o binário da migração pelo da base do delta.

~~~bash
env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -c "$(sed -n '/^~~~python$/,/^~~~$/{ /^~~~/!p; }' docs/handoffs/20261125-retrofit-watch-atribuicao/40-review-r12.md)" --expect
env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -c "$(sed -n '/^~~~python$/,/^~~~$/{ /^~~~/!p; }' docs/handoffs/20261125-retrofit-watch-atribuicao/40-review-r12.md)" --expect --base
~~~

No HEAD revisado, rc 1.

~~~text
at_limit=silêncio above_delayed=graphify above_delayed_resumed=graphify above_fresh=graphify above_slash=graphify
~~~

Na base `5506df4dd27b2bda8f19b0f47424a6cf0c3192a4`, rc 0.

~~~text
at_limit=silêncio above_delayed=silêncio above_delayed_resumed=silêncio above_fresh=graphify above_slash=graphify
~~~

~~~python
import json
import resource
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, mock

from test_retrofit_watch import HookHarness, SCRIPT, World, identified_load, skill_typed, tool


class Journey(HookHarness, TestCase):
    pass


def cap():
    ceiling = 256 * 1024 * 1024
    resource.setrlimit(resource.RLIMIT_AS, (ceiling, ceiling))


def run_journey(legacy, script, size, scenario, split=False):
    j = Journey()
    j.w = w = World()
    try:
        delayed = identified_load("graphify", w.graphify, "msg_local", "toolu_local")
        external = identified_load("superpowers:brainstorming", w.other_skill, "msg_later", "toolu_later")
        j.write(delayed[:2], external[:2], compact=True)
        head, tail = b'{"type":"system","text":"', b'"}\n'
        with w.transcript.open("ab") as fh:
            fh.write(head + b"x" * (size - len(head) - len(tail)) + tail)
        assert j.run_hook(script=legacy, env={"RETROFIT_WATCH": "force"}) is None
        state = w.data / "sessions/s1.json"
        before = json.loads(state.read_bytes())
        assert before["offset"] == w.transcript.stat().st_size
        assert before["current"] is None and before["skills"] == {} and before["classified"] == {}
        assert "skill_calls" not in before
        rows = {"delayed": delayed[2:],
                "fresh": identified_load("graphify", w.graphify, "msg_fresh", "toolu_fresh"),
                "slash": skill_typed("graphify", w.graphify)}
        run = subprocess.run

        def limited(*args, **kwargs):
            return run(*args, **kwargs, preexec_fn=cap)

        with mock.patch.object(subprocess, "run", side_effect=limited):
            if split:
                j.write([{"type": "system", "text": "pausa"}], compact=True)
                assert j.run_hook(script=script, env={"RETROFIT_WATCH": "force"}) is None
                inter = json.loads(state.read_bytes())
                assert inter["offset"] == w.transcript.stat().st_size
                assert inter["current"] is None and inter["skills"] == {} and "skill_calls" in inter
            j.write(rows[scenario], tool(error=True), compact=True)
            out = j.run_hook(script=script, env={"RETROFIT_WATCH": "force"})
        saved = json.loads(state.read_bytes())
        assert saved["offset"] == w.transcript.stat().st_size
        assert not (w.data / "errors.log").exists()
        if out is None:
            assert saved["current"] is None and saved["skills"] == {}
            return "silêncio"
        assert "`/retrofit-skill:retrofit-skill graphify`" in j.context_of(out)
        assert saved["skills"][saved["current"]]["reviews"] == 1
        return "graphify"
    finally:
        w.cleanup()


with TemporaryDirectory(prefix="sdd-r12-") as tmp:
    legacy = Path(tmp) / "legacy.py"
    legacy.write_bytes(subprocess.check_output(["git", "show", f"fe38d1f:{SCRIPT.relative_to(Path.cwd())}"]))
    script = SCRIPT
    if "--base" in sys.argv:
        script = Path(tmp) / "base.py"
        script.write_bytes(subprocess.check_output([
            "git", "show", f"5506df4dd27b2bda8f19b0f47424a6cf0c3192a4:{SCRIPT.relative_to(Path.cwd())}",
        ]))
    limit = 2 * 1024 * 1024
    observed = {
        "at_limit": run_journey(legacy, script, limit, "delayed"),
        "above_delayed": run_journey(legacy, script, limit + 1, "delayed"),
        "above_delayed_resumed": run_journey(legacy, script, limit + 1, "delayed", split=True),
        "above_fresh": run_journey(legacy, script, limit + 1, "fresh"),
        "above_slash": run_journey(legacy, script, limit + 1, "slash"),
    }
print(" ".join(f"{name}={value}" for name, value in observed.items()))
if "--expect" in sys.argv:
    expected = {
        "at_limit": "silêncio", "above_delayed": "silêncio",
        "above_delayed_resumed": "silêncio", "above_fresh": "graphify", "above_slash": "graphify",
    }
    raise SystemExit(observed != expected)
~~~

## Boot da próxima fase

Começar pela sonda acima com `--expect` para ver o Red, inclusive quando o
Stop que grava a migração não recebe trabalho elegível. Escrever primeiro a
regressão durável nomeada em R12. Manter os controles no limite, de carga nova
e de slash explícito. Repetir I1, F1, R9, R10, R11 e o `TEST_CMD`, sem
recontar o prefixo nem retomar a leitura ilimitada do registro.

### Recommended Actions

**Must Fix (CRITICAL)**

_Nenhum._

**Should Fix (HIGH)**

_Nenhum._

**Consider Fixing (MEDIUM/LOW)**

- Fechar R12 com silêncio para metadado atrasado não comprovado e avanço do
  offset, sem bloquear cargas novas no delta.

**Deferred (form)**

- Manter a precisão das âncoras e preservar saídas históricas nos itens abertos.

**Outside scope (tracker)**

_Nenhum achado novo._

_Custo da revisão — codereview 2.27.38, código e varredura inline, três agentes de
documentação em gpt-6.1-terra, sem relançamento. Agentes reportaram 16 leituras
integrais e 7–13 chamadas cada. O orquestrador fez 27 chamadas de shell na
análise. Custo monetário não medido._
