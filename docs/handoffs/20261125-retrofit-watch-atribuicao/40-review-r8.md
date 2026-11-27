---
missao: 20261125-retrofit-watch-atribuicao
fase: REVIEW
rodada: 8
status: done
sessao: 01a21e03-4b3b-7fe0-9e3e-1baf2a762978
data: 2026-11-27 14:24
gate: "Não passou. Em 90837f5, env -u GIT_DIR -u GIT_WORK_TREE PYTHONDONTWRITEBYTECODE=1 bash -c 'source .sdd/config.sh && eval \"$TEST_CMD\"' → rc 0. Loja com 154 testes (3 pulados) e hook com 98. Adaptadores, catálogo e versão 0.4.1 válidos. Nove Checks com rc 0 e árvore limpa antes dos artefatos. A sonda R8 saiu com rc 1 em três jornadas. Platô em Code Quality (Zen), Error Handling e Test Coverage, todos B como em r7."
reviewed_head: 90837f5c1ce78c70721b2578b2451533f5385a6d
---

# Review — rodada r8 — Atribuição da retrofit-watch por mensagem

## TL;DR

R7 passou nos nove Checks, inclusive com estado gravado pelo hook 0.4.0 real.
Dois defeitos ainda no delta viraram R8. Uma colisão inversa perde a marca do ID, e a retomada
da 0.4.0 reabre o crédito após carga externa quando ainda não havia skill monitorada no histórico.
A suíte passou. Nota geral B e platô em três critérios estritos. Nenhum código foi alterado.

## Nota da rodada

**Escopo.** `codereview:codereview base=6f190e3907f80eb39fb9cc79d35822e8efcc930b`,
Python e `unittest`, branch `fix/retrofit-watch-atribuicao-mesma-mensagem` sobre `main`.
O delta até `90837f5` tem um arquivo de código, um de testes e sete registros/documentos
(+521/−18). O arquivo de notas foi excluído da revisão de conteúdo. A QA já exercitou F1
com a monitorada reconhecida antes do encerramento. O novo caso atravessa a atualização antes da
primeira confirmação por caminho, com `skills={}` no corte.

### 🛑 Secrets Detection

Estado `PASS`. Regex e gitleaks analisaram oito arquivos e 505 linhas adicionadas no escopo
autorizado, sem achados e com `errors=[]`. O delta não abre um destino de escrita, rede ou shell
no hook. Leitura e gravação continuam sob a trava existente, com substituição atômica.

### Princípios Zen e revisão técnica

A migração agora preserva `attribution_closed` explícito e infere o encerramento em estados
legados com histórico. Ela ainda confunde histórico vazio com ausência de encerramento. A fusão
do histórico do ID retém a falta de origem no primeiro participante, mas não no segundo. Os dois
desvios são de decisão, não de exceção ou tipo inválido. Não há alteração visual nem de API.

### Test Coverage

| Sensor | Status | Evidência em `90837f5` |
|---|---|---|
| `retrofit_watch.py` | WITH_TESTS | `test_retrofit_watch.py` foi alterado e chama o hook em subprocessos. Os dois testes novos conferem offset, erros e contadores. |
| I1, F1, R1–R7 | PASS | Nove células de `checkpoint.md` executadas na raiz, uma por Bash, com Git isolado para as fixtures. Cada rc foi 0 e cada saída coincidiu com a célula, normalizado o espaço. I1 deu `1 0 1 0 0 1`, F1 deu os três silêncios e R7 terminou em `regressoes=2`. |
| R7 com a 0.4.0 real | PASS | Sonda de r7 com `--expect --legado`, usando o script exportado de `fe38d1f`. Todos os vetores de R7 coincidiram com o Check. |
| Limites e retenção | PASS | Os testes de teto da suíte passaram. A sonda de R2 com `--medir` no hook corrente imprimiu `[(10, 0, 325), (100, 0, 326), (1000, 0, 327)]` no formato tentativas, vínculos e bytes. |
| Sonda R8 | FAIL | Três falsos pedidos em oito jornadas. Os cinco controles deram o resultado esperado. Todos os Stops conferiram offset completo e ausência de `errors.log`. |

`env -u GIT_DIR -u GIT_WORK_TREE PYTHONDONTWRITEBYTECODE=1 bash -c 'source .sdd/config.sh && eval "$TEST_CMD"'`
em `90837f5` saiu com rc 0. A loja rodou 154 testes, com três pulados por configuração, e o hook
rodou 98 sem falhas. A validação aprovou a 0.4.1 com três avisos de outras skills, sem falha.
Não houve smoke no host Claude Code, no Windows ou de distribuição nativa.

### Sincronia da documentação

`env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -m unittest -q test_auto_docs.ReleaseTest.test_the_four_places_agree_at_0_4_0_or_later`
rodou um teste em `90837f5`, com rc 0. Manifesto, catálogo, SKILL, README e CHANGELOG concordam
na 0.4.1. O CHANGELOG explicita a condição de haver histórico na migração. A formulação mais
ampla do README ainda não se verifica no caso legado de R8. O verificador de `TODO.md` acusou
duas âncoras deslocadas no CHANGELOG, já cobertas pelo item posicional aberto.

### 🧹 Dead Code & Cleanup

Nenhum símbolo introduzido ou órfão na varredura inline do delta. O novo local `unowned`
alimenta a decisão de retenção, a chave `attribution_closed` tem escritores e leitor, e os dois
novos métodos são descobertos por `unittest`. A varredura não inclui dívida preexistente.

### Overall Grade

| Criterion | Grade | Rationale |
|-----------|-------|-----------|
| Code Quality (Zen) | B | A junção trata de forma assimétrica as duas chamadas da colisão. A migração usa histórico vazio como ausência de encerramento. |
| Type Safety | A | Os casos exercitam um JSON produzido pela versão anterior, ID ausente e IDs válidos. A união e a migração preservam os tipos esperados no delta. |
| Error Handling | B | A decisão conservadora deixa passar três falsos pedidos mesmo sem erro de leitura, sem perda de offset e sem mudança da mensagem ativa no caso de colisão. |
| Security | A | Regex e gitleaks voltaram sem achados. Nenhum novo comando externo, acesso à rede ou destino de escrita foi introduzido no hook. |
| Performance | A | Os tetos passaram e 10 a 1.000 falhas independentes deixaram zero vínculos e só dois bytes de variação. O delta acrescenta apenas consultas locais aos mapas existentes. |
| Test Coverage | B | A suíte e os nove Checks confirmam R7, mas a sonda reproduz três falsos pedidos nos dois percursos que os testes ainda não cobrem. |
| Documentation | B | A versão está sincronizada, mas duas âncoras ultrapassaram a tolerância do verificador e a descrição ampla da retomada ainda tem um contraexemplo. |
| **Overall** | **B** | O commit funcional de R7 fechou os cenários anteriores. As letras se repetem com novas lacunas confirmadas nas mesmas áreas. |

O gate não passou. As letras são as mesmas de r7. A execução de R7 teve correção funcional, mas
o platô não justifica abrir outra rodada automática de revisão.

## Achados da rodada

| # | Severidade | Achado | Onde |
|---|---|---|---|
| 1 | MEDIUM | Se a segunda chamada de uma colisão vem sem `message.id`, a poda pode apagar a ambiguidade e permitir falso vínculo com a mensagem ativa. | `plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py:664–670` |
| 2 | MEDIUM | A migração não reconhece um encerramento da 0.4.0 com histórico vazio, mesmo após confirmar carga externa posterior à chamada monitorada. | `plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py:427` |
| 3 | LOW | As três linhas novas no CHANGELOG deslocaram duas âncoras do backlog para fora da tolerância. É a recorrência do item de âncoras, sem mudança do hook. | `plugins/retrofit-watch/CHANGELOG.md:93`, `TODO.md:175`, `TODO.md:202` |

**1.** Com `codereview` ativa em `msg_1`, uma chamada de `graphify` de `msg_2` aguarda a
confirmação por caminho. Uma segunda chamada sem `message.id` reutiliza seu ID. Só a pendência
original é consultada para `unowned`. Como ela tem dono, a segunda origem nula some da lista.
A poda tira `msg_2` e apaga a marca, sem trocar `msg_1`. O Stop seguinte, com uma externa de
`msg_1` que reutiliza o ID, pede retro de `codereview`. O resultado se repete em leitura
contínua e com estado em disco antes e depois da colisão. O ID fresco ainda pede a retro
correta. Este não é o reuso após trocar a mensagem ativa que já está adiado no backlog.

**2.** O nome local `coderabbit-pr` ainda aguarda confirmação do caminho. O hook real da 0.4.0
recebe a carga externa posterior, inclusive o metadado, e persiste `current=null`, `skills={}`
e a classificação nula do caminho externo antes da atualização. O primeiro registro do delta
novo é a confirmação atrasada da monitorada. A 0.4.1 pede retro mesmo sem prova de nova carga.
O mesmo corte gravado pelo hook atual permanece em silêncio. Um legado vazio sem passagem da
externa ainda aceita a confirmação, e uma chamada realmente nova após a migração ainda pede
retro. Isso separa ausência de encerramento de encerramento antes da primeira confirmação.

**3.** `bash /home/joruge/.wt/sdd-kit-8a56249/tests/check-todo.sh --check TODO.md` retornou
duas violações em `90837f5`. No base do delta, a ocorrência de `push` estava na linha 90,
oito linhas depois de ambas as referências à linha 82. Agora está na 93, onze depois.

## Incrementos de conserto (R<n>)

| R<n> | Achado | Check escrito no checkpoint |
|---|---|---|
| R8 | Achados 1 e 2, um lote MEDIUM. | Sonda de Stop desta rodada, estado da 0.4.0 real, controles positivos e dois testes de regressão com contagem obrigatória. |

Da raiz, a sonda abaixo em `90837f5` saiu com rc 1. O Git da revisão fornece o script legado
por `git show`. O script roda em diretório temporário e as fixtures recebem Git isolado.
A célula de R8 também exige dois testes permanentes, que ficam para a execução.
`check-checkpoint.sh --red` confirmou R8 como a única célula pendente e vermelha.

~~~bash
PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -c "$(sed -n '/^~~~python$/,/^~~~$/{ /^~~~/!p; }' docs/handoffs/20261125-retrofit-watch-atribuicao/40-review-r8.md)" --expect
~~~

Saída normalizada por linhas. Cada trio é trabalho, atrito e revisões para `codereview`.

~~~text
continua_novo=codereview:0,0,1
continua_reuso=codereview:0,0,1
marca_apos_poda_novo=0
retomada_novo=codereview:0,0,1
marca_apos_poda_reuso=0
retomada_reuso=codereview:0,0,1
legado_sem_externa=codereview:0,0,1
atual_externa=silêncio:0,0,0
legado_carga_nova=codereview:0,0,1
legado_externa=codereview:0,0,1
divergências: continua_reuso, retomada_reuso, legado_externa
~~~

~~~python
import argparse
import os
from pathlib import Path
import subprocess
import tempfile

from test_retrofit_watch import StopTest, identified_load, tool


parser = argparse.ArgumentParser()
parser.add_argument("--expect", action="store_true")
args = parser.parse_args()
failures = []


def target(test, out, expected):
    if out is None:
        return "silêncio"
    assert f"`/retrofit-skill:retrofit-skill {expected}`" in test.context_of(out), out
    return expected


def counts(state, key):
    entry = state["skills"].get(key, {})
    return tuple(entry.get(field, 0) for field in ("work", "friction", "reviews"))


def verify(label, test, out, state, expected, key):
    result = target(test, out, key.split(":", 1)[1])
    work, friction, reviews = counts(state, key)
    print(f"{label}={result}:{work},{friction},{reviews}")
    if expected != result or (expected == "silêncio" and
                              (state["current"] is not None or (work, friction, reviews) != (0, 0, 0))):
        failures.append(label)


def collision(resume, original_owner, second_owner, reused):
    test = StopTest()
    test.setUp()
    try:
        ours, _ = test.identified_loads()
        call_id = "toolu_collision"
        first = identified_load("graphify", test.w.other_skill, original_owner, call_id)
        second = identified_load("graphify", test.w.other_skill, second_owner, call_id)
        external = identified_load("superpowers:brainstorming", test.w.other_skill,
                                   "msg_1", call_id if reused else "toolu_fresh")
        del second[0]["message"]["id"]
        test.write(ours, first[:2], compact=True)
        if resume:
            out, before = test.checked_stop()
            assert out is None and before["skill_calls"][call_id] == original_owner
            assert before["skill_message_order"] == ["msg_1", "msg_2"]
        test.write(second[:2], compact=True)
        if resume:
            out, middle = test.checked_stop()
            assert out is None and middle["skill_message_order"] == ["msg_1"]
            assert middle["current_origin"] == before["current_origin"]
            assert not middle["skill_correlation_lost"] and call_id not in middle["skill_calls"]
            print(f"marca_apos_poda_{'reuso' if reused else 'novo'}="
                  f"{int(call_id in middle['skill_call_history'])}")
        test.write(external, tool(error=True), compact=True)
        out, after = test.checked_stop()
        verify(("retomada_" if resume else "continua_") + ("reuso" if reused else "novo"),
               test, out, after, "silêncio" if reused else "codereview", "full:codereview")
    finally:
        test.tearDown()


def legacy(legacy_script, current_format, external, new):
    test = StopTest()
    test.setUp()
    try:
        pending = identified_load("coderabbit-pr", test.w.mkt_skill, "msg_1", "toolu_pending")
        later = identified_load("superpowers:brainstorming", test.w.other_skill, "msg_2", "toolu_other")
        test.write(pending[:2], later if external else (), tool(), compact=True)
        if current_format:
            out, before = test.checked_stop()
        else:
            out, before = test.checked_stop(script=legacy_script)
        assert out is None and before["skills"] == {} and before["current"] is None
        external_path = str(test.w.other_skill)
        assert (external_path in before["classified"]) == external
        if external:
            assert before["classified"][external_path] is None
        if current_format:
            assert before["attribution_closed"] == external
        else:
            assert "attribution_closed" not in before
        if new:
            test.write(identified_load("codereview:coderabbit-pr", test.w.mkt_skill, "msg_3", "toolu_new"))
        else:
            test.write(pending[2:])
        test.write(tool(error=True))
        out, after = test.checked_stop()
        label = "atual_externa" if current_format else ("legado_carga_nova" if new else
                "legado_externa" if external else "legado_sem_externa")
        verify(label, test, out, after, "silêncio" if external and not new else "codereview",
               "full:codereview")
    finally:
        test.tearDown()



# Leia o histórico no Git da revisão antes de isolar o Git usado pelas fixtures.
old_path = "plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py"
old_source = subprocess.check_output(["git", "-P", "show", "fe38d1f:" + old_path])
for key in ("GIT_DIR", "GIT_WORK_TREE"):
    os.environ.pop(key, None)
for resume in (False, True):
    for reused in (False, True):
        collision(resume, "msg_2", None, reused)
with tempfile.TemporaryDirectory(prefix="retrofit-r8-") as folder:
    script = Path(folder) / "retrofit_watch.py"
    script.write_bytes(old_source)
    for current_format, external, new in ((False, False, False), (True, True, False),
                                          (False, True, True), (False, True, False)):
        legacy(script, current_format, external, new)

if args.expect and failures:
    raise SystemExit("divergências: " + ", ".join(failures))
~~~

## O que virou incremento

- **R8** — os dois defeitos viraram um incremento `pending`. A célula exige silêncio
  com trabalho, atrito e revisões em zero, a marca após a poda e os controles com ID novo,
  legado sem externa, estado atual e carga nova.
- **R7** — fechado em `830629b`. O Check e os dois testes de Stop passaram. Com a 0.4.0 real,
  a migração preservou o encerramento com histórico nas três origens. A colisão com a pendência
  originalmente sem origem ficou em silêncio, com ou sem retomada.

Linha registrada no checkpoint:

| R8 | Preservar a colisão com ID sem origem na ordem inversa e o encerramento legado sem histórico de monitorada (r8, achados 1–2) | `PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -c "$(sed -n '/^~~~python$/,/^~~~$/{ /^~~~/!p; }' docs/handoffs/20261125-retrofit-watch-atribuicao/40-review-r8.md)" --expect && if o=$(env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -m unittest -q test_retrofit_watch.StopTest.test_unowned_collision_after_owned_pending_survives_pruning test_retrofit_watch.StopTest.test_legacy_external_without_history_ignores_delayed_metadata 2>&1); then [[ "$o" == *"Ran 2 tests"* && "$o" == *"OK" ]] && printf 'regressoes=2\n'; else printf '%s\n' "$o" >&2; exit 1; fi` → `continua_novo=codereview:0,0,1 continua_reuso=silêncio:0,0,0 marca_apos_poda_novo=1 retomada_novo=codereview:0,0,1 marca_apos_poda_reuso=1 retomada_reuso=silêncio:0,0,0 legado_sem_externa=codereview:0,0,1 atual_externa=silêncio:0,0,0 legado_carga_nova=codereview:0,0,1 legado_externa=silêncio:0,0,0 regressoes=2` | pending | — |

## O que foi refutado

- A receita literal de R7 teria barras antes das aspas e quebraria ao copiar. Os trechos de
  `40-review-r7.md:60` e `40-review-r7.md:289` contêm aspas normais. Os escapes aparecem no
  valor YAML de `gate:`, não nos comandos em Markdown. A célula de R7 e o `TEST_CMD` literal
  foram repetidos com rc 0.
- O Check de F1 já cobriria o estado vazio legado. No F1, a monitorada é reconhecida antes
  da carga externa e o estado atual guarda o encerramento. R8 confirma `skills={}` antes da
  nova leitura e repete a mesma jornada com a marca do formato atual como controle.
- A correção de R7 teria quebrado o ID fresco ou a confirmação sem história. Tanto o ID
  novo antes e depois de retomada quanto o legado sem passagem da externa pediram a retro correta.

## Achados fora de escopo

- A posição das âncoras pertence ao item aberto “A publicação do patch desloca uma âncora do
  backlog da retrofit-watch” em `TODO.md`. O desvio reapareceu na mesma missão. A gramática de
  `RECURRED` admite uma entrada por projeto e missão e não repete a origem do item. Sem duplicata.
- A receita histórica sem isolamento do Git, os registros de métricas anteriores, o reuso
  após troca de mensagem ativa e o caso de metadado externo obsoleto continuam em itens
  existentes de `TODO.md`. Não se abriu incremento de prosa nem se ampliou a janela.

## Pendências / Decisions for a Human

O mantenedor decide se retoma a execução de R8 após o platô. O merge continua reservado ao
mantenedor.

## Boot da próxima fase

Se houver retomada, execute a sonda de R8 em Red e escreva os dois testes nomeados no
checkpoint. Passe também o controle da 0.4.0 sem externa e o da carga nova. Na colisão,
confirme em disco a origem conhecida antes da disputa, a mensagem ativa inalterada e a marca
retida após a poda. Em todos os Stops, exija offset completo e ausência de `errors.log`.
Nos casos negativos, exija silêncio e os três contadores em zero. Repita os nove Checks
anteriores e o `TEST_CMD` com Git isolado.

### Recommended Actions

**Must Fix (CRITICAL)**

_Nenhum._

**Should Fix (HIGH)**

_Nenhum._

**Consider Fixing (MEDIUM/LOW)**

- Executar R8 em TDD se o mantenedor retomar. Preservar os cinco controles da sonda e os limites da janela.
- Triar a posição das âncoras de `TODO.md` junto do item aberto que já acompanha o deslocamento.

**Deferred (form)**

_Nenhum._

_Custo da revisão: skill 2.27.38 indicada pela fase, registro de instalação 2.30.2. Três agentes
gpt-6.1-terra em documentação, zero verificadores, código e varredura inline. Agentes reportaram
cinco arquivos lidos integralmente e 2–6 chamadas cada. Oito jornadas R8 em duas formas de sonda,
além de nove Checks, execução da suíte e controle de versão. Custo monetário não medido._
