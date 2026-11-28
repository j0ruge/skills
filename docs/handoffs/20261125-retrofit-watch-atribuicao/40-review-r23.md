---
missao: 20261125-retrofit-watch-atribuicao
fase: REVIEW
rodada: 23
status: done
sessao: 01a21fb1-826e-7231-9475-1f7b5212ebc4
data: 2026-11-27 22:13
gate: 'Em c2c0c8c394eccfbde1e91039306886f7955844dd, árvore inicial limpa. env -u GIT_DIR -u GIT_WORK_TREE PYTHONDONTWRITEBYTECODE=1 bash -c ''source .sdd/config.sh && eval "$TEST_CMD"'' → rc 0. Adaptadores e catálogo válidos, 154 testes da loja (3 pulados), 119 do hook e versão 0.4.1 validada. Os 15 Checks anteriores igualaram o stdout esperado e retornaram rc 0. A sonda de R14 reproduziu três divergências em leitura contínua e retomada e retornou rc 1 com --expect. Regressão ante r22 em Code Quality (Zen), Error Handling, Test Coverage, Documentation e Overall. R14 pendente.'
reviewed_head: c2c0c8c394eccfbde1e91039306886f7955844dd
---

# Review — rodada r23 — Atribuição da retrofit-watch por mensagem

## TL;DR

R13 e os 15 Checks existentes passaram. A r23 confirmou três desvios de atribuição no Stop real,
em leitura contínua e retomada, reunidos no R14. Um achado apenas documental foi para o backlog.
Nota geral B. Nenhum código foi alterado nesta revisão.

## Nota da rodada

`/codereview:codereview base=a07e588acf0f9d03445797a1ebd431ed5265cb1d` limitou a revisão ao delta até
`c2c0c8c394eccfbde1e91039306886f7955844dd`. Sete commits. Excluído o conteúdo do diário append-only,
o recorte tem 21 arquivos, 469 adições e 50 remoções. Um módulo Python alterado, dois arquivos de
teste e 18 documentos. QA e r22 foram usados como controles. A r22 não deixou achados pendentes.

### Secrets Detection

| Ocorrências | Scanners | Arquivos | Linhas adicionadas | Status |
|---|---|---|---|---|
| 0 | regex e gitleaks | 21 | 469 | PASS |

O pré-scan não registrou erros e seus totais conferem com o `git diff --numstat` do mesmo recorte.

### Qualidade, cobertura e sincronização

- O módulo `retrofit_watch.py` tem cobertura atualizada em `test_retrofit_watch.py` e na
  jornada `e2e/test_retrofit_watch_stop.py` (1 de 1 arquivo de produção).
- Cinco testes dirigidos de R13 passaram. Cada mutação isolada falhou, com um teste executado e
  erro de asserção: desabilitar o encerramento por erro, ignorar a lista de IDs aposentados,
  não importar a lista no replay, apagar todo slash ao começar uma chamada e retirar a guarda
  de tipo do texto de `isMeta`. O total de 30 mutações é evidência do EXEC, não desta rodada.
- I1 imprimiu `1 0 1 0 0 1`. F1 executou um teste com três variantes e manteve silêncio
  após confirmar crédito anterior e encerramento. R13 imprimiu os seis pares esperados.
  As três provas nativas não foram repetidas. O TEST_CMD as pula e o EXEC registrou que o
  Bubblewrap não chegou a criar o namespace.
- Guia de atribuição e SKILL descrevem os controles de R13. A redação exclusiva no changelog
  contradiz um desses controles. Adaptadores, catálogo e versão 0.4.1 passaram na suíte.

### Varredura de símbolos

Bucket A em linha. Nenhuma assinatura mudou e nenhuma chamada ou importação ficou órfã.
O campo novo é escrito, lido, limpo e importado pelo mesmo hook e exercitado nas fixtures.
Bucket B não solicitado.

### Overall Grade

| Criterion | Grade | Rationale |
|-----------|-------|-----------|
| Code Quality (Zen) | B | A aposentadoria transforma origem ambígua em prova e o slash anterior sobrevive a uma carga externa posterior. |
| Type Safety | A | As alterações no leitor validam dicionários e texto antes de ler caminhos. IDs malformados continuam passando pelo normalizador e estado anterior recebe o campo opcional. |
| Error Handling | B | Sem message.id, um resultado de erro da própria chamada deixa a atribuição aberta e o Stop pede retro com o trabalho posterior. |
| Security | A | Regex e gitleaks sem ocorrências ou erros no recorte de 21 arquivos. A mudança de estado continua sob a trava existente. |
| Performance | A | A retenção nova tem teto separado de 1.024 IDs, com controle de expulsão e limpeza. O replay mantém o limite por registro. |
| Test Coverage | B | Os 15 Checks existentes passam e cinco mutações isoladas foram detectadas, mas nenhuma prova permanente distingue as três variantes confirmadas nesta rodada. |
| Documentation | B | O changelog descreve a aposentadoria como exceção exclusiva e contradiz o controle reproduzido de metadado atrasado da mesma mensagem. |
| **Overall** | **B** | R13 passou nos casos anunciados, mas três desvios de atribuição persistem nos dois cortes do Stop. R14 ficou pendente. |

## Achados da rodada

| # | Severidade | Achado | Onde |
|---|---|---|---|
| 1 | MEDIUM | A falha da própria chamada não encerra crédito se o ID da chamada existe mas falta `message.id`. | `plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py:781` |
| 2 | MEDIUM | ID com dono desconhecido vira prova de antiguidade após dois avanços e protege indevidamente a monitorada. | `plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py:521` |
| 3 | MEDIUM | O caminho de um slash anterior reabre a atribuição mesmo depois de confirmada a carga externa posterior. | `plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py:661` e `plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py:716` |
| 4 | LOW | A nota de release descreve ID aposentado como condição exclusiva para preservar diante de metadado externo atrasado. | `plugins/retrofit-watch/CHANGELOG.md:19` |

1. O resultado de erro traz o mesmo `tool_use_id` que a chamada reconhecida pelo nome.
   Sem `message.id`, `current_origin` fica nulo e a comparação nova nem é feita, apesar de
   o ID de chamada ainda existir. O trabalho posterior pediu `codereview` nos dois cortes.
   Com o mesmo ID de mensagem preenchido ficou em silêncio. Sucesso sem `message.id` e erro
   de outro ID continuaram pedindo `codereview`.
2. Uma pendência sem mensagem e uma chamada de mensagem conhecida compartilham o ID.
   Enquanto outro vínculo mantém o dono conhecido na janela, o primeiro avanço retira a marca
   sem origem do histórico e sobra só o dono conhecido. No avanço seguinte, o delta expõe
   essa perda ao registrar o ID como comprovadamente aposentado. O metadado externo
   sem origem foi ignorado, e o Stop pediu `codereview`. No controle só com o dono conhecido,
   esse pedido está correto. Na base, ambas as variantes ficavam em silêncio.
3. O slash digitado antecede uma carga externa reconhecida pelo caminho de uma chamada
   vinculada. A chamada deixa de apagar o slash e a confirmação pelo caminho preserva-o.
   Chegando depois da externa, o caminho sem ID do slash antigo reabre a atribuição e
   pede `graphify`. Na base só o slash digitado **depois** da confirmação externa pedia retro.
   Esse controle positivo continua válido, assim como o slash que atravessa tentativa irrelevante.
4. Mesmo com o metadado externo em outro Stop, o vínculo da mesma mensagem manteve
   `codereview` sem aposentar o ID. A exclusividade em “só deixam” contradiz também as
   linhas 7–9 do próprio changelog.

## Incrementos de conserto (R<n>)

| R<n> | Achado | Check escrito no checkpoint |
|---|---|---|
| R14 | Achados 1–3 | `env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -c "$(sed -n '/^~~~python$/,/^~~~$/{ /^~~~/!p; }' docs/handoffs/20261125-retrofit-watch-atribuicao/40-review-r23.md)" --expect && env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B e2e/test_retrofit_watch_stop.py` → `falha_sem_mensagem=silêncio:1,silêncio:1 falha_com_mensagem=silêncio:1,silêncio:1 sucesso_sem_mensagem=codereview:1,codereview:1 falha_outro_id=codereview:1,codereview:1 aposentadoria_ambigua=silêncio:1:0,silêncio:1:0 aposentadoria_conhecida=codereview:1:1,codereview:1:1 slash_anterior=silêncio:1,silêncio:1 slash_posterior=graphify:1,graphify:1 externa_da_mesma_mensagem=codereview:1,codereview:1 linked=silêncio missing=silêncio empty=silêncio` |

## O que virou incremento

- R14 reúne os achados 1–3 da r23. O Check exige os nove pares corretos com o hook real
  e a jornada F1. O executor deixa regressões permanentes para os três casos nos dois cortes, preservando
  os controles positivos e o histórico já creditado. Nenhum conserto nesta rodada.
- A r22 estava fechada sem pendências. O R13 de `fcbd6cb`, aberto após a revisão externa,
  passou no Check original e nas cinco regressões duráveis. Os novos casos não anulam
  essas provas e delimitam onde elas deixam de valer.

## O que foi refutado

- A falha não encerra indiscriminadamente outra atribuição. Com erro de outro ID, os dois
  cortes pediram `codereview`. O controle `independent` do teste de R13 ainda pediu `graphify`
  pela chamada pendente independente.
- O descarte de metadado não ficou geral. ID antigo com dono conhecido preservou a monitorada
  na sonda, enquanto os controles `unknown`, `reused`, `evicted` e `reset` da suíte
  continuaram encerrando. Isso não refuta a promoção do ID ambíguo do achado 2.
- Bloco inválido não impede o caminho válido nem faz replay parcial importar a lista.
  Os dois testes passaram no original e ficaram vermelhos quando as defesas respectivas
  foram removidas isoladamente em cópias temporárias.

## Achados fora de escopo

- Achado 4, só de prosa, registrado em `TODO.md` na seção aberta (2026-11-27).
  Não virou incremento. O caso anterior de reuso geral de ID depois de sair da janela
  continua no backlog e não é o novo caso de promoção indevida à lista de aposentados.

## Pendências / Decisions for a Human

A r22 tinha A em todos os critérios. Regrediram Code Quality (Zen), Error Handling, Test Coverage,
Documentation e Overall. A revisão para neste delta com as notas reais e o R14 registrado.
A decisão de avançar após a regressão e a integração do PR continuam com o mantenedor.

## Evidências reproduzíveis

- Execute `env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -c "$(sed -n '/^~~~python$/,/^~~~$/{ /^~~~/!p; }' docs/handoffs/20261125-retrofit-watch-atribuicao/40-review-r23.md)"` da raiz no HEAD revisado. O bloco roda Stop em subprocessos
  com estado em disco e verifica avanço do offset e ausência de `errors.log`.
  O primeiro valor de cada par é contínuo, o segundo é retomado. O primeiro dígito
  confirma o estado final e, nas duas linhas de aposentadoria, o segundo mostra se
  o ID entrou na lista. Com `--expect`, a sonda devolveu rc 1 neste HEAD.
- Para comparar a base, grave `env -u GIT_DIR -u GIT_WORK_TREE git show a07e588acf0f9d03445797a1ebd431ed5265cb1d:plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py`
  em arquivo temporário e acrescente `--script "$arquivo"` ao comando acima.
  Na base, a falha com `message.id` pediu `codereview`, o ID de dono conhecido
  não tinha proteção e o slash anterior à externa ficou em silêncio, nos dois cortes.
- No HEAD revisado, `env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B e2e/test_retrofit_watch_stop.py` executou um teste com os três controles de F1.
  Para repetir os 15 Checks existentes, execute em Bash cada comando da célula anterior a `→`.
  Exija rc 0 e compare todo o stdout normalizando apenas espaços em branco.
- Para repetir o pré-scan no mesmo intervalo, execute a sequência abaixo em Bash.

~~~bash
set -o pipefail
git -c diff.noprefix=false -P diff a07e588acf0f9d03445797a1ebd431ed5265cb1d...c2c0c8c394eccfbde1e91039306886f7955844dd --unified=0 -- .   ':(exclude)docs/handoffs/20261125-retrofit-watch-atribuicao/checkpoint-notas.md' |
  bash "$HOME/.agents/skills/codereview/scripts/scan_secrets.sh"
~~~

### Sonda de R14

~~~python
import argparse
import re
from pathlib import Path

from test_retrofit_watch import SCRIPT, StopTest, identified_load, skill_typed, tool


def run(case, resumed, script):
    test = StopTest()
    test.setUp()
    try:
        w = test.w
        ours, external = test.identified_loads("msg_2")
        if case.startswith("falha_") or case == "sucesso_sem_mensagem":
            if case in ("falha_sem_mensagem", "sucesso_sem_mensagem"):
                del ours[0]["message"]["id"]
            if case != "sucesso_sem_mensagem":
                result = ours[1]["message"]["content"][0]
                result["is_error"] = True
                if case == "falha_outro_id":
                    result["tool_use_id"] = "toolu_other"
            before, after = ours[:1], ours[1:2]
        elif case.startswith("aposentadoria_"):
            a = identified_load("codereview:coderabbit-pr", w.mkt_skill, "ma", "ua")
            m = identified_load("graphify", w.graphify, "mm", "um")
            b = identified_load("graphify", w.graphify, "mb", "ub")
            known = identified_load("irrelevante", w.other_skill, "mb", "toolu_2")
            unknown = identified_load("irrelevante", w.other_skill, None, "toolu_2")
            before = a + m[:2] + (unknown[:2] if case.endswith("ambigua") else ()) + b[:2] + known[:2] + m[2:]
            source = unknown if case.endswith("ambigua") else known
            after = ours + source[2:]
        elif case.startswith("slash_"):
            direct = skill_typed("graphify", w.graphify)
            external[0]["message"]["content"][0]["input"]["skill"] = "brainstorming"
            before = [*direct[:1], *external] if case.endswith("anterior") else [*external, *direct[:1]]
            after = direct[1:]
        elif case == "externa_da_mesma_mensagem":
            external[0]["message"]["id"] = ours[0]["message"]["id"]
            before, after = ours + external[:2], external[2:]
        else:
            raise AssertionError(case)
        test.write(before, compact=True)
        if resumed:
            out, _ = test.checked_stop(script=script, mode="plan")
            assert out is None
        test.write(after, tool(error=True), compact=True)
        out, st = test.checked_stop(script=script)
        if out is None:
            target = "silêncio"
        else:
            target = re.search(r"/retrofit-skill:retrofit-skill ([a-z-]+)", test.context_of(out))[1]
        if target == "silêncio":
            invariant = st["current"] is None and st["attribution_closed"]
            invariant &= all(not any(entry[k] for k in ("work", "friction", "reviews"))
                             for entry in st["skills"].values())
        else:
            invariant = not st["attribution_closed"] and st["skills"][st["current"]]["arg"] == target
            invariant &= st["skills"][st["current"]]["reviews"] == 1
        if case.startswith("aposentadoria_"):
            retired = "toolu_2" in st.get("retired_skill_calls", [])
            return f"{target}:{int(invariant)}:{int(retired)}"
        return f"{target}:{int(invariant)}"
    finally:
        test.tearDown()


parser = argparse.ArgumentParser()
parser.add_argument("--expect", action="store_true")
parser.add_argument("--script", type=Path, default=SCRIPT)
args = parser.parse_args()
cases = {
    "falha_sem_mensagem": "silêncio:1",
    "falha_com_mensagem": "silêncio:1",
    "sucesso_sem_mensagem": "codereview:1",
    "falha_outro_id": "codereview:1",
    "aposentadoria_ambigua": "silêncio:1:0",
    "aposentadoria_conhecida": "codereview:1:1",
    "slash_anterior": "silêncio:1",
    "slash_posterior": "graphify:1",
    "externa_da_mesma_mensagem": "codereview:1",
}
ok = True
for case, expected in cases.items():
    result = [run(case, resumed, args.script) for resumed in (False, True)]
    print(f"{case}=" + ",".join(result))
    ok &= result == [expected, expected]
if args.expect and not ok:
    raise SystemExit(1)
~~~

### Recommended Actions

**Must Fix (CRITICAL)**

_Nenhum._

**Should Fix (HIGH)**

_Nenhum._

**Consider Fixing (MEDIUM/LOW)**

- Fechar R14 com os três controles negativos e positivos no Stop real.
- Corrigir a exclusividade no changelog quando o item documental for triado.

### Cost footprint

_Codereview 2.27.38 do caminho solicitado, sem uso do cache Claude. Dois agentes gpt-6.1-terra na documentação, 16 chamadas e nove leituras integrais informadas. Código Python e varredura de símbolos em linha, sem relançamentos. Custo monetário não medido._
