---
missao: 20261125-retrofit-watch-atribuicao
fase: REVIEW
rodada: 6
status: done
sessao: 01a21d60-6d4b-7563-af7b-bdeac6a6470c
data: 2026-11-27 11:27
gate: 'Em 6f245e10c22f03364face08b649c7d223689fd54, árvore inicial limpa. env -u GIT_DIR -u GIT_WORK_TREE PYTHONDONTWRITEBYTECODE=1 bash -c ''source .sdd/config.sh && eval "$TEST_CMD"'' → rc 0. 154 testes da loja (3 pulados), 95 do hook e versão 0.4.1 validada. Sete Checks concluídos verdes. R6 reproduziu dois pedidos de retro indevidos e o ID sem marca após confirmação. Gate não passou. Platô em Code Quality (Zen), Error Handling e Test Coverage (B). Documentation e Overall seguem B.'
reviewed_head: 6f245e10c22f03364face08b649c7d223689fd54
---

# Review — rodada r6 — Preservar a atribuição da retrofit-watch por mensagem

## TL;DR

`c52f09c` fechou R5. A suíte e os sete Checks concluídos passaram.
O delta perde a marca de colisão quando a mensagem que reutilizou o ID é confirmada. O Stop pede
retro indevidamente em leitura contínua e retomada. O achado virou R6.
Nota geral B, com as mesmas letras de r5. Gate não passou. Nenhum código ou teste foi alterado.

## Escopo e medidas

`codereview:codereview base=669d93d795411275d6608cf5ccc56f975663e152` até `6f245e10c22f03364face08b649c7d223689fd54`.
Cinco commits e nove caminhos no inventário. O diário append-only ficou fora da leitura e da
varredura. No escopo restante, um script com suíte atualizada e seis arquivos Markdown. Quatro
arquivos de prosa, 19 unidades, passaram pelo verificador. A revisão anterior e o checkpoint
entraram no fluxo inline por conterem a sonda e os Checks executáveis. O handoff de QA de
`08f09a1` documenta F1, não uma QA após R5. Sua jornada foi repetida no Check de F1.

### Detecção de segredos

~~~json
{"findings":[],"scanners":["regex","gitleaks"],"errors":[],"scanned":{"files":8,"added_lines":354}}
~~~

Status PASS nos oito caminhos autorizados, sem achados. Não há interface gráfica neste delta.

### Sensores repetidos no HEAD revisado

| Sensor | Resultado |
|---|---|
| `env -u GIT_DIR -u GIT_WORK_TREE PYTHONDONTWRITEBYTECODE=1 bash -c 'source .sdd/config.sh && eval "$TEST_CMD"'` | rc 0, adaptadores e catálogo válidos, 154 testes da loja (3 pulados) e 95 do hook. Validador confirmou a 0.4.1. |
| Sete células de `checkpoint.md`, em Bash com Git isolado e igualdade da saída integral após normalizar espaços | Sete rc 0, I1, F1 e R1–R5 com as saídas contratuais. F1 executou os três fluxos de dois Stops. |
| Sonda R5 e teste `StopTest.test_unowned_consumed_id_survives_intermediate_collision`, usando o hook do HEAD e o exportado da base | HEAD com os 16 subcasos verdes. O blob da base é igual ao de `c8ddc39` e reprovou quatro subcasos. Na sonda, a base divergiu em três valores. |
| Dez controles direcionados de Stop, `test_correlation_overflow_persists_conservative_fallback` e `test_auto_docs.ReleaseTest.test_the_four_places_agree_at_0_4_0_or_later` | 12 testes, todos verdes. Legado, IDs inválidos, descarte, pendência concorrente, dois tetos e consistência das fontes de versão. |
| Sonda de R2 com o script atual e `--medir` | `[(10, 0, 325), (100, 0, 326), (1000, 0, 327)]`. Zero vínculos e os bytes indicados por lote. |
| `ruff check --no-cache --select F401,F811,F821,F841 plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py plugins/retrofit-watch/skills/retrofit-watch/tests/test_retrofit_watch.py` | rc 0. Nenhum import, nome ou variável local inválidos nas regras verificadas. Sem símbolo novo sem uso e sem mudança de nome de interface. Dívida anterior não varrida. |

As cinco mutações foram aplicadas uma de cada vez sobre o hook do HEAD em diretório temporário.
Os testes abaixo continuaram usando o mesmo transcript e o mesmo estado em disco que no Green.
Os erros de teste das duas últimas linhas foram `KeyError: 'toolu_a'` na inspeção da marca ausente,
não falhas do subprocesso do hook.

| Mutação em `_skill_origin` | Teste que detectou | Resultado |
|---|---|---|
| Trocar `if history.get(call_id) != []:` por `if True:` | `test_unowned_consumed_id_survives_intermediate_collision` | 4 falhas |
| Tirar `*owners,` da tupla que reúne os donos | Mesmo teste de R5 | 4 falhas |
| Trocar `calls.pop(call_id, None)` por `calls.get(call_id)` | `test_duplicate_pending_id_does_not_select_either_message` | 2 falhas |
| Trocar `message_id` por `None` no último argumento da tupla de donos | Teste de ID pendente duplicado e `test_ambiguous_id_survives_retirement_of_one_owner` | 1 falha e 1 erro |
| Trocar a atribuição `history[call_id] = [owner for owner in owners if owner]` por `pass` | Os mesmos dois testes | 2 erros |

A repetição confirma o total atual de cinco degradações detectadas, sem certificar os tetos usados
no ensaio histórico nem recontar as mutações de outras rodadas.

## Nota da rodada

A nota separa o fechamento de R5 da regressão introduzida no mesmo commit.
O laço não avança porque os critérios estritos abaixo de A são os mesmos de r5.

### Overall Grade

| Criterion | Grade | Rationale |
|-----------|-------|-----------|
| Code Quality (Zen) | B | A lista vazia conserva o consumo sem origem, mas o ramo de colisão deixa de registrar a mensagem conhecida que também reutilizou o ID. |
| Type Safety | A | Os testes de IDs inválidos e de retomada com estado antigo e intermediário passaram. A divergência é de associação, não de tipo ou de leitura do JSON. |
| Error Handling | B | A confirmação de uma mensagem ainda retida esquece a sua colisão e o próximo reuso passa indevidamente por origem confiável. |
| Security | A | O delta não altera comandos, permissões, travas ou destinos de escrita. Dois detectores não encontraram segredos no escopo autorizado. |
| Performance | A | Três lotes de até 1.000 falhas isoladas deixaram zero vínculos. O controle concorrente e o teste dos dois limites de correlação passaram. |
| Test Coverage | B | Os 95 testes do hook e os sete Checks passaram. Os casos novos de R5 não confirmam a mensagem que colidiu, e não detectam R6. |
| Documentation | B | README e CHANGELOG delimitam R5 à mensagem ativa inalterada. O handoff não distingue poda intacta de mudança dos IDs descartados ao confirmar outra mensagem. |
| **Overall** | **B** | R5 foi fechado com prova no Stop, mas ainda há um pedido indevido de retro introduzido pelo delta. |

## Achados da rodada

| # | Severidade | Achado | Onde |
|---|---|---|---|
| 1 | MEDIUM, atribuição | O ID consumido sem origem colide com uma tentativa da mensagem posterior que continua retida por outra chamada pendente. Ao confirmar essa mensagem, a marca some e a externa que reutiliza o ID parece ter origem confiável na mensagem ativa. | `plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py:659–665` e `:503–523` |

Com `msg_a` ativa e `toolu_s: []` no histórico, `msg_b` tem uma chamada pendente com ID novo.
Outra tentativa de `msg_b` colide com `toolu_s`. Na base, o histórico passa a registrar `["msg_b"]`.
Em `c52f09c`, a guarda conserva `[]` e não registra `msg_b`. A confirmação da chamada de ID novo
mantém `msg_b` na janela, mas apaga a lista vazia. A carga externa de `msg_b` reaproveita `toolu_s`
e preserva `codereview` no HEAD. A base não aceita esse vínculo. Foi a própria mensagem que colidiu
que ficou ativa, portanto não é o caso de reuso após descartar todos os donos, já no backlog.

### Sonda de R6

A primeira parte do Check executa o bloco Python abaixo com `--expect`. Sem essa opção, a sonda
imprime o observado. Para comparar com a base, exporte
`git show 669d93d795411275d6608cf5ccc56f975663e152:plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py`
para um arquivo temporário e passe seu caminho como argumento da sonda.
O mesmo transcript foi executado com o hook real, em processo separado e com estado em disco.

| Medida | Base `669d93d` | HEAD `6f245e1` |
|---|---|---|
| `continua_novo` | `codereview` | `codereview` |
| `continua_reuso` | `silêncio` | `codereview` |
| `retomada_novo` | `codereview` | `codereview` |
| `marca_apos_confirmacao` | `1` | `0` |
| `retomada_reuso` | `silêncio` | `codereview` |

Com `--expect`, a base saiu com rc 0 e o HEAD com rc 1 após imprimir os cinco valores. Cada Stop
verificou offset completo e ausência de `errors.log`. Antes da confirmação, ambos os scripts ainda
guardavam o ID e a pendência de `msg_b`. Depois, `msg_b` seguia na janela em ambos, sem saturação.
Só a base encerrou o crédito futuro no caso ambíguo. A segunda parte do Check exige o teste durável
que será escrito em EXEC e não é alcançada no Red atual.

~~~python
from argparse import ArgumentParser
from pathlib import Path

from test_retrofit_watch import SCRIPT, StopTest, identified_load, skill_via_tool, tool


def measure(script, cuts, duplicate):
    results = []
    test = StopTest()
    test.setUp()
    try:
        path = test.w.mkt_skill
        name = "codereview:coderabbit-pr"
        active = identified_load(name, path, "msg_a", "toolu_active")
        anonymous = skill_via_tool(name, path)
        refresh = identified_load(name, path, "msg_a", "toolu_refresh")
        pending = identified_load("coderabbit-pr", path, "msg_b", "toolu_pending")
        collision = identified_load("nao-instalada", test.w.other_skill, "msg_b", "toolu_s")
        external = identified_load("superpowers:brainstorming", test.w.other_skill, "msg_b",
                                   "toolu_s" if duplicate else "toolu_new")
        test.write(active, anonymous, refresh, pending[:2], collision[:1], compact=True)
        if cuts:
            out, saved = test.checked_stop(script=script)
            assert out is None and saved["current_origin"] == ["msg_a", "toolu_refresh"]
            assert not saved["skill_correlation_lost"]
            assert saved["skill_message_order"] == ["msg_a", "msg_b"]
            assert saved["skill_calls"] == {"toolu_pending": "msg_b"}
            assert "toolu_s" in saved["skill_call_history"]
        test.write(pending[2:], compact=True)
        if cuts:
            out, saved = test.checked_stop(script=script)
            assert out is None and saved["current_origin"] == ["msg_b", "toolu_pending"]
            assert not saved["skill_correlation_lost"]
            assert saved["skill_message_order"] == ["msg_b"]
            if duplicate:
                results.append(f"marca_apos_confirmacao={int('toolu_s' in saved['skill_call_history'])}")
        test.write(external, tool(error=True), compact=True)
        out, saved = test.checked_stop(script=script)
        target = "silêncio"
        skill = saved["skills"]["full:codereview"]
        if out is not None:
            assert "`/retrofit-skill:retrofit-skill codereview`" in test.context_of(out), out
            assert saved["current"] == "full:codereview" and skill["reviews"] == 1
            target = "codereview"
        else:
            assert saved["current"] is None
            assert (skill["work"], skill["friction"], skill["reviews"]) == (0, 0, 0)
        mode = "retomada" if cuts else "continua"
        case = "reuso" if duplicate else "novo"
        return [*results, f"{mode}_{case}={target}"]
    finally:
        test.tearDown()


parser = ArgumentParser()
parser.add_argument("script", type=Path, default=SCRIPT, nargs="?")
parser.add_argument("--expect", action="store_true")
args = parser.parse_args()
results = [result for cuts in (False, True) for duplicate in (False, True)
           for result in measure(args.script, cuts, duplicate)]
print("\n".join(results))
expected = ["continua_novo=codereview", "continua_reuso=silêncio", "retomada_novo=codereview",
            "marca_apos_confirmacao=1", "retomada_reuso=silêncio"]
if args.expect and results != expected:
    parser.exit(1, "A jornada de R6 divergiu do resultado esperado.\n")
~~~

## Incrementos de conserto (R<n>)

| R<n> | Achado | Check escrito no checkpoint |
|---|---|---|
| R6 | Achado 1, colisão esquecida na confirmação da própria mensagem que reutilizou o ID | A jornada deve manter a marca após a confirmação e ficar em silêncio no reuso nos dois modos. O controle de ID novo ainda pede retro. Além da jornada, a célula exige um teste de regressão executado e verde. |

## O que virou incremento

| ID | Incremento | Check (comando → esperado) | Status | Commit |
|---|---|---|---|---|
| R6 | Impedir que a confirmação de uma mensagem ainda retida apague a ambiguidade do ID com que ela colidiu (r6, achado 1) | `env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -c "$(sed -n '/^~~~python$/,/^~~~$/{ /^~~~/!p; }' docs/handoffs/20261125-retrofit-watch-atribuicao/40-review-r6.md)" --expect && if o=$(env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -m unittest -q test_retrofit_watch.StopTest.test_unowned_collision_survives_confirmation_of_live_owner 2>&1); then [[ "$o" == *"Ran 1 test"* && "$o" == *"OK" ]] && printf 'regressao=1\n'; else printf '%s\n' "$o" >&2; exit 1; fi` → `continua_novo=codereview continua_reuso=silêncio retomada_novo=codereview marca_apos_confirmacao=1 retomada_reuso=silêncio regressao=1` | pending | — |

- R5, achado 1 de r5, fechado em `c52f09c`. Comparada à base, a sonda recuperou a marca e eliminou
  os dois pedidos indevidos com tentativa intermediária descartada. O teste permanente falhou em
  quatro subcasos com o script de `c8ddc39` e passou com o script de `c52f09c`. Os blobs do hook
  e do teste no HEAD são os mesmos do fix. R6 cobre a sequência distinta em que a mensagem
  intermediária fica retida e é confirmada.

## O que foi refutado

- **R5 ficou em aberto ou basta desfazer a guarda nova.** A sonda de r5 reproduziu na base
  `marca_apos_disputa=0` e dois pedidos indevidos. No HEAD mostrou `marca_apos_disputa=1` e silêncio
  em ambos. Remover a guarda em cópia temporária voltou a reprovar quatro subcasos do teste de R5.
- **R6 exige histórico de mensagens aposentadas.** A sonda mostrou `msg_b` pendente na colisão e
  confirmada antes do próximo reuso. A base já retém o vínculo nessa sequência. O controle
  `test_new_skill_retires_older_consumed_and_unlinked_calls` continuou verde.
- **As medições de R5 não são verificáveis sem a saída original.** O verificador apontou cinco
  lacunas no handoff. A repetição confirmou a suíte e os sete Checks, o teste de release, quatro
  falhas no Red, ausência de `errors.log` e avanço do offset nos casos de Green, o vetor da sonda
  e cinco degradações detectadas nas cópias temporárias. Não são as saídas originais de EXEC.
- **O sucesso de R5 demonstra que o descarte ao confirmar outra mensagem não mudou.**
  Em `20-handoff-exec.md:69` a afirmação vale para o procedimento de poda, que não foi editado,
  mas não para os IDs que ele descarta. O A/B de R6 mede a perda da marca apesar de `msg_b`
  continuar retida. A ressalva de escopo do README e do CHANGELOG, que falam de mensagem ativa
  inalterada, está correta.

## Achados fora de escopo

- O verificador pediu evidência da ausência de saídas históricas citada em `TODO.md:230`.
  Os artefatos autorizados trazem resumos das 58 degradações e da prova nativa em
  `20-handoff-exec.md:63` e `:109`, sem suas saídas originais anexadas. A revisão não afirma
  ausência no diário ou em logs que não leu. É a pendência já aberta pela mesma missão em r5,
  sem nova ocorrência no tracker.
- Os itens já registrados sobre mensagens aposentadas e metadado externo obsoleto continuam fora
  deste lote. Nenhum achado novo de prosa ou de código externo foi registrado.

## Pendências / Decisions for a Human

`Code Quality (Zen)`, `Error Handling` e `Test Coverage` ficaram em B, sem alta ou queda em
relação a r5. A revisão encerra no platô sem certificar o gate. O mantenedor decide se retoma pelo
R6. As três provas nativas continuam pendentes de um host com suporte ao namespace Bubblewrap.

## Boot da próxima fase

Se houver retomada, rode o Check R6 em Red e escreva
`StopTest.test_unowned_collision_survives_confirmation_of_live_owner` em TDD. Cubra a leitura
contínua e a retomada com estado em disco entre colisão e confirmação e antes da externa.
Exija offset completo, ausência de `errors.log` e nenhum crédito futuro no reuso. Mantenha os
controles de ID novo, da tentativa podada de R5, dos limites e do descarte dos donos aposentados.
Repita os sete Checks concluídos e o `TEST_CMD` com Git isolado.

### Recommended Actions

**Must Fix (CRITICAL)**

_Nenhum._

**Should Fix (HIGH)**

_Nenhum._

**Consider Fixing (MEDIUM/LOW)**

- Se a missão for retomada, execute R6 preservando as duas garantias de R5 e sem ampliar a janela.
- Triar a rastreabilidade histórica no item existente do backlog.

**Deferred (form)**

_Nenhum._

**Outside scope (tracker)**

_Nenhum item novo. O verificador declarou corte zero._

_Custo da revisão: skill instalada 2.30.2, chamada pela cópia 2.27.38. A instalada acrescenta o verificador de prosa, o fechamento por unidade e a nota de documentação separada. Um verificador gpt-6.1-terra, quatro arquivos, 19 unidades, 15 chamadas informadas. Zero agentes por arquivo. Código, sondas executáveis e varredura inline. Cinco mutações temporárias. Custo monetário não medido._
