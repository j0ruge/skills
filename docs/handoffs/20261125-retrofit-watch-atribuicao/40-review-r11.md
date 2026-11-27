---
missao: 20261125-retrofit-watch-atribuicao
fase: REVIEW
rodada: 11
status: done
sessao: 01a21ec6-4be5-7d02-8dd4-70f0f19d6fc5
data: 2026-11-27 17:58
gate: "Em 5506df4dd27b2bda8f19b0f47424a6cf0c3192a4, árvore limpa. env -u GIT_DIR -u GIT_WORK_TREE PYTHONDONTWRITEBYTECODE=1 bash -c 'source .sdd/config.sh && eval \"$TEST_CMD\"' → rc 0, 154 testes da loja (3 pulados), 111 do hook, adaptadores, catálogo e versão 0.4.1 válidos. Checks já fechados → 12/12 com rc 0 e stdout igual. Sonda R11 com --expect → rc 1. Platô em Code Quality (Zen), Error Handling, Performance e Test Coverage, todos em B. Os controles de R10 melhoraram, mas os novos cortes permanecem vermelhos."
reviewed_head: 5506df4dd27b2bda8f19b0f47424a6cf0c3192a4
---

# Review — rodada r11 — Atribuição da retrofit-watch por mensagem

Delta fixado por **codereview** com o argumento
`base=8d2910945c9041d670e9e13a69df8cf7d7010d9f` e HEAD `5506df4dd27b2bda8f19b0f47424a6cf0c3192a4`. Seis commits, dez caminhos.
Excluindo o diário por ordem da fase, o escopo analisado tem sete documentos, um módulo Python e
um arquivo de testes, com +599/−45. Seis documentos passaram por verificação de 95 unidades
editadas. O plano voltou à análise completa do delta porque contém a sonda executada por I1.
O fechamento de QA de `08f09a1` cobre BUG-01. Nesta rodada F1 repetiu a jornada de terminal.

## TL;DR

A suíte e os 12 Checks passaram, inclusive os quatro cortes originais de R10.
A primeira atribuição ainda apaga uma marca de ID falho sem origem e permite retro indevida.
Um registro de 96 MiB no prefixo ainda aborta a migração sob 256 MiB e impede a retro do delta.
Os dois achados viraram R11. Nota B, em platô. Nenhum código alterado.

## Nota da rodada

### Secrets Detection

**Status: PASS.** Os pré-scans 2.27.38 e 2.30.2 devolveram 0 ocorrências e 0 erros em
`regex` e `gitleaks`, com 9 caminhos e 599 linhas adicionadas em cada um.

### Zen, cobertura e sincronização

- **Zen e integridade.** As duas lacunas estão na fronteira do estado e da leitura. O novo
  registro de ID sem origem funciona depois de iniciada a atribuição, mas some na primeira
  confirmação. A leitura linha a linha evita materializar o prefixo inteiro, mas o limite
  por chamada a `readline` ainda é o restante do prefixo.
- **WITH_TESTS, 1/1 módulo.** O arquivo de testes alterado importa o módulo e roda o hook
  em subprocessos com estado real. Cinco provas independentes em cópias temporárias
  reagiram a retirar o slash recuperado, a marca sem origem, a checagem de tamanho, a
  rejeição de evidência parcial ou a leitura incremental. Cada controle rodou um teste
  com rc 0 e cada variante rodou um teste com falha de asserção.
- **Documentação.** A prova de release rodou 1 teste e retornou 0. README e CHANGELOG
  acompanham a leitura linha a linha e a recuperação do slash. A afirmação sobre a janela
  de IDs falhos precisa cobrir o corte do achado 1.
- **Varredura de símbolos, Bucket A.** Nenhum órfão confirmado. `_retire_skill_call`
  tem dois chamadores, `recover_legacy_correlation` tem o Stop como chamador, e os
  testes novos são descobertos. A busca pela grafia antiga `consumed=True` não
  encontrou consumidor restante. Bucket B fora do delta.

### Overall Grade

| Criterion | Grade | Rationale |
|-----------|-------|-----------|
| Code Quality (Zen) | B | A marca criada por R10 ainda some no primeiro reconhecimento de uma monitorada. |
| Type Safety | A | Os cortes exercitam ID ausente e válido, estado JSON legado e leitura binária sem divergência de tipos. |
| Error Handling | B | O Stop sob teto retorna 0 e registra MemoryError, mas não processa o delta nem salva a migração. |
| Security | A | Dois pré-scans sem ocorrências ou erros. O replay usa o mesmo transcript e mantém a trava e os destinos de escrita. |
| Performance | B | 160 MiB de linhas curtas migraram sob 256 MiB, mas trocar parte delas por um único registro de 96 MiB bloqueou a retomada. |
| Test Coverage | B | Os 12 Checks e cinco provas de sensibilidade passaram. A suíte ainda não cobre a perda da marca antes da primeira atribuição nem um registro grande. |
| Documentation | B | A versão e os vetores estão sincronizados, mas a garantia sobre a janela de IDs falhos precisa distinguir a primeira atribuição. |
| **Overall** | **B** | R10 passou nos cortes originais. Duas variantes confirmadas ainda quebram correlação ou retomada. |

## Achados da rodada

| # | Severidade | Achado | Onde |
|---|---|---|---|
| 1 | MEDIUM | O ID falho sem origem recebe marca, mas a primeira confirmação de uma monitorada a apaga. A externa que reaproveita o ID na mensagem dessa monitorada é aceita como correlacionada. O trabalho seguinte pede retro indevida em leitura contínua e após Stops. | `retrofit_watch.py:704–709` e `:512–530` |
| 2 | MEDIUM | Um único registro JSONL grande ainda pode esgotar a memória na leitura e decodificação do prefixo. O Stop volta com rc 0, o estado fica idêntico ao legado, o offset não avança e a retro do delta não sai. | `retrofit_watch.py:790–805` e `test_retrofit_watch.py:625–641` |

No achado 1, o corte adicional está no comportamento alterado por R10. A marca `[]`
ambígua existe após o erro, mas é descartada na transição de nenhuma mensagem confirmada para
a primeira. Essa transição não prova que o erro sem `message.id` veio de outra mensagem.
O Check conserva o controle com ID novo e não pede reter a marca ao avançar de uma mensagem
confirmada para outra, comportamento já testado em R10.

No achado 2, com o mesmo teto de 256 MiB e cerca de 160 MiB de prefixo, só mudar a distribuição
do tamanho dos registros altera o resultado no HEAD. O prefixo contém um registro `system`
válido com 96 MiB de texto e linhas curtas de 4 KiB. A 0.4.0 processa o delta em ambos os
casos. O Check permite o fallback conservador quando um registro inviabiliza a reconstrução,
sem travar o delta nem importar evidência parcial.

## Incrementos de conserto (R<n>)

| R<n> | Achado | Check escrito no checkpoint |
|---|---|---|
| R11 | Achados 1–2, em lote. | `env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -c "$(sed -n '/^~~~python$/,/^~~~$/{ /^~~~/!p; }' docs/handoffs/20261125-retrofit-watch-atribuicao/40-review-r11.md)" --expect && if o=$(env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -m unittest -q test_retrofit_watch.StopTest.test_failed_unowned_call_id_survives_first_attribution test_retrofit_watch.StopTest.test_legacy_replay_recovers_after_oversized_line 2>&1); then [[ "$o" == *"Ran 2 tests"* && "$o" == *"OK" ]] && printf 'regressoes=2\n'; else printf '%s\n' "$o" >&2; exit 1; fi` → `continua_novo=codereview continua_reuso=silêncio retomada_novo=codereview marca_novo=1,1 retomada_reuso=silêncio marca_reuso=1,1 linhas_curtas=graphify,graphify linha_longa=graphify,graphify regressoes=2` |

## O que virou incremento

| R11 | Preservar a ambiguidade de ID falho na primeira atribuição e completar a retomada com registro grande no prefixo (r11, achados 1–2) | `env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -c "$(sed -n '/^~~~python$/,/^~~~$/{ /^~~~/!p; }' docs/handoffs/20261125-retrofit-watch-atribuicao/40-review-r11.md)" --expect && if o=$(env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -m unittest -q test_retrofit_watch.StopTest.test_failed_unowned_call_id_survives_first_attribution test_retrofit_watch.StopTest.test_legacy_replay_recovers_after_oversized_line 2>&1); then [[ "$o" == *"Ran 2 tests"* && "$o" == *"OK" ]] && printf 'regressoes=2\n'; else printf '%s\n' "$o" >&2; exit 1; fi` → `continua_novo=codereview continua_reuso=silêncio retomada_novo=codereview marca_novo=1,1 retomada_reuso=silêncio marca_reuso=1,1 linhas_curtas=graphify,graphify linha_longa=graphify,graphify regressoes=2` | pending | — |

R10 foi fechado por `e65902c` nos cortes originais. Em `5506df4`, a troca real
0.4.0 → 0.4.1 recuperou o slash de `graphify` e ignorou o alheio. I1 e F1 voltaram ao vetor
aprovado. IDs falhos reaproveitados depois da ativação ficaram em silêncio. IDs novos
continuaram positivos. O prefixo de linhas curtas migrou sob o teto e as três regressões
nomeadas em R10 passaram. R9 também manteve suas quatro saídas e o teste de origem ativa.

## O que foi refutado

- **O quinto caso ficou verde por mudar a saída esperada.** Não mudou. I1 e F1 retornaram
  `1 0 1 0 0 1`, e o Check R10 validou o contrato das duas células, o caso sem vínculo
  em silêncio e o controle com prova válida pedindo retro de `codereview`.
- **Migrar prefixos grandes continua falhando independentemente do formato.** O Check R10
  e a sonda nova migraram 160 MiB com linhas curtas sob 256 MiB. No Red anterior, o
  módulo de `df6407a` também falhou nesse formato. O achado remanescente exige um
  registro individual grande e não invalida a melhora medida nos prefixos de linhas curtas.
- **Os resultados Red e Green do handoff contradizem o delta.** A revisão repetiu os
  Checks fechados, reproduziu o contraste de memória com o módulo anterior e executou cinco
  controles negativos. Não reatribuiu ao HEAD os RSS e tempos históricos de r10, nem declarou
  reproduzidas as 33 variações de EXEC. A ausência das saídas brutas nas fontes dos
  verificadores é uma lacuna de registro, não evidência de um resultado falso.

## Achados fora de escopo

- A precisão das três âncoras permanece no item que veio de r10, sem um incremento novo.
- As saídas brutas históricas de RSS, pré-scans, varredura e mutações não foram anexadas
  aos verificadores. O item **Medições históricas da atribuição sem saída preservada** do
  `TODO.md` já registra essa dívida. O modelo do backlog não duplica o registro da
  mesma missão que abriu o item.

## Pendências / Decisions for a Human

As letras repetiram r10. `Code Quality (Zen)`, `Error Handling`, `Performance`
e `Test Coverage` seguem em B. A regra de platô encerra esta revisão, sem aprovar o
gate. R11 deixa os cortes reproduzidos para EXEC. Não há decisão de produto para
reproduzi-los nem mudança de escopo necessária.

## Evidências reproduzíveis

A suíte foi executada uma vez em `5506df4`, com árvore limpa.

~~~bash
env -u GIT_DIR -u GIT_WORK_TREE PYTHONDONTWRITEBYTECODE=1 bash -c 'source .sdd/config.sh && eval "$TEST_CMD"'
~~~

Retornou rc 0. A loja rodou 154 testes com três pulos configurados. O hook rodou 111
testes. Adaptadores, catálogo e versões passaram. As 12 células já fechadas foram
executadas em `bash -c`, com Git isolado e comparação de rc e stdout completo,
normalizando só espaços em branco. Todas igualaram as saídas do checkpoint.
Não houve execução em Claude Code ou Windows.

Execute a sonda nova da raiz. Ela usa somente fixtures temporárias e extrai a 0.4.0
de `fe38d1f`. Sem `--expect`, imprime a medição. Com a opção, exige o resultado de R11.

~~~bash
env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -c "$(sed -n '/^~~~python$/,/^~~~$/{ /^~~~/!p; }' docs/handoffs/20261125-retrofit-watch-atribuicao/40-review-r11.md)" --expect
~~~

Resultado no HEAD revisado, rc 1 com `--expect`:

~~~text
continua_novo=codereview continua_reuso=codereview retomada_novo=codereview marca_novo=1,0 retomada_reuso=codereview marca_reuso=1,0 linhas_curtas=graphify,graphify linha_longa=graphify,MemoryError
~~~

Em `marca_novo` e `marca_reuso`, o primeiro bit observa a marca antes da primeira
ativação e o segundo após a ativação. `linhas_curtas` e `linha_longa` mostram 0.4.0
antes de 0.4.1. No ramo `MemoryError`, o Stop saiu 0, sem stdout ou stderr, o log registrou
a exceção e o JSON legado ficou inteiro e igual ao anterior, inclusive o offset.

~~~python
import json
import os
import resource
import subprocess
import sys
from pathlib import Path
from shutil import copyfile
from tempfile import TemporaryDirectory
from unittest import TestCase

from test_retrofit_watch import HookHarness, SCRIPT, World, identified_load, skill_typed, tool


class Jornada(HookHarness, TestCase):
    pass


def target(journey, output, name):
    if output is None:
        return "silêncio"
    assert f"\x60/retrofit-skill:retrofit-skill {name}\x60" in journey.context_of(output)
    return name


def before_activation(reused, split):
    j = Jornada()
    j.w = w = World()
    try:
        failed = identified_load("nao-instalada", w.other_skill, "m1", "u2")
        del failed[0]["message"]["id"]
        failed[1]["message"]["content"][0]["is_error"] = True
        ours = identified_load("codereview:coderabbit-pr", w.mkt_skill, "m1", "u1")
        external = identified_load("superpowers:brainstorming", w.other_skill, "m1", "u2" if reused else "u3")
        state = w.data / "sessions/s1.json"

        def snapshot():
            saved = json.loads(state.read_bytes())
            assert saved["offset"] == w.transcript.stat().st_size
            assert not (w.data / "errors.log").exists()
            return saved

        j.write(failed[:2], compact=True)
        marks = []
        if split:
            assert j.run_hook(mode="plan") is None
            pre = snapshot()
            assert pre["current"] is None
            marks.append(pre["skill_call_history"].get("u2") == [])
        j.write(ours, compact=True)
        if split:
            assert j.run_hook(mode="plan") is None
            active = snapshot()
            assert active["current"] == "full:codereview"
            marks.append(active["skill_call_history"].get("u2") == [])
        j.write(external, tool(error=True), compact=True)
        observed = target(j, j.run_hook(), "codereview")
        saved = snapshot()
        skill = saved["skills"]["full:codereview"]
        assert (skill["work"], skill["friction"], skill["reviews"]) == (0, 0, int(observed == "codereview"))
        assert saved["current"] == ("full:codereview" if observed == "codereview" else None)
        return observed, marks
    finally:
        w.cleanup()


def cap():
    ceiling = 256 * 1024 * 1024
    resource.setrlimit(resource.RLIMIT_AS, (ceiling, ceiling))


def replay(root, legacy, long_line):
    transcript = root / "transcript.jsonl"
    head, tail = b'{"type":"system","text":"', b'"}\n'
    slab = b"x" * (1024 * 1024)
    short = head + slab[:4096 - len(head) - len(tail)] + tail
    with transcript.open("wb") as stream:
        if long_line:
            stream.write(head)
            for _ in range(96):
                stream.write(slab)
            stream.write(tail)
        for _ in range((64 if long_line else 160) * 256):
            stream.write(short)
    offset = transcript.stat().st_size
    results = []
    for script in (legacy, SCRIPT):
        j = Jornada()
        j.w = w = World()
        try:
            # Cada binário recebe o mesmo prefixo e o mesmo corte legado, em estado próprio.
            copyfile(transcript, w.transcript)
            payload = json.dumps(dict(session_id="s1", transcript_path=str(w.transcript), cwd=str(w.proj))).encode()
            env = dict(os.environ, HOME=str(w.home), CLAUDE_PLUGIN_DATA=str(w.data), RETROFIT_WATCH="force")
            subprocess.run([sys.executable, str(legacy), "baseline"], input=payload, env=env,
                           capture_output=True, check=True, timeout=15)
            state = w.data / "sessions/s1.json"
            before = json.loads(state.read_bytes())
            assert before["offset"] == offset and "skill_calls" not in before
            j.write(skill_typed("graphify", w.graphify), tool(error=True), compact=True)
            stop = subprocess.run([sys.executable, str(script), "stop"], input=payload, env=env,
                                  capture_output=True, timeout=18, preexec_fn=cap)
            assert stop.returncode == 0 and not stop.stderr
            saved = json.loads(state.read_bytes())
            log = w.data / "errors.log"
            if log.exists():
                assert not stop.stdout and saved == before
                assert "MemoryError:" in log.read_text(), log.read_text()
                results.append("MemoryError")
                continue
            out = json.loads(stop.stdout) if stop.stdout else None
            assert saved["offset"] == w.transcript.stat().st_size
            assert ("skill_calls" in saved) == (script == SCRIPT)
            results.append(target(j, out, "graphify"))
        finally:
            w.cleanup()
    return ",".join(results)


with TemporaryDirectory(prefix="sdd-r11-") as tmp:
    root = Path(tmp)
    legacy = root / "legacy.py"
    legacy.write_bytes(subprocess.check_output([
        "git", "show", "fe38d1f:plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py",
    ]))
    results = {}
    for split, mode in ((False, "continua"), (True, "retomada")):
        for reused, variant in ((False, "novo"), (True, "reuso")):
            observed, marks = before_activation(reused, split)
            results[f"{mode}_{variant}"] = observed
            if split:
                results[f"marca_{variant}"] = ",".join(str(int(mark)) for mark in marks)
    results["linhas_curtas"] = replay(root, legacy, False)
    results["linha_longa"] = replay(root, legacy, True)

print(" ".join(f"{key}={value}" for key, value in results.items()))
expected = {
    "continua_novo": "codereview", "continua_reuso": "silêncio",
    "retomada_novo": "codereview", "marca_novo": "1,1",
    "retomada_reuso": "silêncio", "marca_reuso": "1,1",
    "linhas_curtas": "graphify,graphify", "linha_longa": "graphify,graphify",
}
if "--expect" in sys.argv:
    raise SystemExit(results != expected)
~~~

## Boot da próxima fase

Repetir a célula de R11 para ver o Red, com atenção ao desaparecimento da marca e ao
offset que não avança. Escrever primeiro as duas regressões duráveis. Manter os controles
de ID novo, avanço de uma mensagem já confirmada, slash alheio e prefixo de linhas curtas.
Se o registro grande impedir a reconstrução, processar o delta com o fallback conservador,
sem crédito duplicado nem correlação parcial. Repetir I1, F1, R9, R10 e `TEST_CMD`.

### Recommended Actions

**Must Fix (CRITICAL)**

_Nenhum._

**Should Fix (HIGH)**

_Nenhum._

**Consider Fixing (MEDIUM/LOW)**

- Fechar R11 com os dois sensores duráveis e a jornada em subprocessos sob teto de memória.

**Deferred (form)**

- Manter a precisão das âncoras e a preservação de saídas históricas nos itens já abertos.

**Outside scope (tracker)**

_Nenhum achado novo._

_Custo da revisão — codereview 2.27.38 solicitada e 2.30.2 instalada usada para a verificação de prosa, com pré-scan de ambas. Dois verificadores e um agente por arquivo em gpt-6.1-terra, sem relançamento, com 4–85 chamadas informadas. Código, testes e varredura de símbolos inline. Custo monetário não medido._
