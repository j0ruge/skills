---
missao: 20261125-retrofit-watch-atribuicao
fase: REVIEW
rodada: 9
status: done
sessao: 01a21e13-411d-7fb2-96c9-5e833c2d2329
data: 2026-11-27 14:43
gate: "Não passou. Em 15a36e9, env -u GIT_DIR -u GIT_WORK_TREE PYTHONDONTWRITEBYTECODE=1 bash -c 'source .sdd/config.sh && eval \"$TEST_CMD\"' → rc 0. Loja com 154 testes (3 pulados), hook com 100, adaptadores e catálogo válidos e versão 0.4.1 confirmada. Árvore limpa antes dos artefatos e dez Checks com rc 0 e saída exata. Platô em Code Quality (Zen), Error Handling e Test Coverage, todos B como em r8. A sonda com a 0.4.0 reproduziu uma perda de crédito introduzida no delta e um falso pedido herdado no corte sem metadado externo."
reviewed_head: 15a36e9877b1328669fa18d2b9dfb7541269ac24
---

# Review — rodada r9 — Atribuição da retrofit-watch por mensagem

## TL;DR

R8 fechou os dois defeitos reproduzidos em r8. Os dez Checks e a suíte passaram.
Na troca real de 0.4.0 para 0.4.1, a ordem entre a carga externa e a chamada local pendente
não sobrevive no estado legado. Uma ordem perdeu a retro no delta. Sem metadado externo,
a ordem inversa ainda pede retro indevidamente. A limitação foi para o backlog.
Nota geral B, platô em três critérios estritos. Nenhum código alterado.

## Nota da rodada

**Escopo.** `codereview:codereview base=90837f5c1ce78c70721b2578b2451533f5385a6d` até
`15a36e9877b1328669fa18d2b9dfb7541269ac24`, branch
`fix/retrofit-watch-atribuicao-mesma-mensagem` sobre `main`. Sete commits, nove arquivos no
escopo de conteúdo (+480/−26), um de código, um de teste e sete de prosa. O histórico de
notas foi excluído. A verificação de prosa cobriu 103 unidades editadas em sete arquivos.
A QA já cobre o encerramento com monitorada reconhecida antes da externa, nas três formas
de origem de F1. A lacuna abaixo usa `skills={}` no estado real da versão anterior.

### 🛑 Secrets Detection

| Status | Scanners | Escopo | Achados | Erros |
|---|---|---|---|---|
| PASS | Regex e gitleaks | Nove arquivos e 480 linhas adicionadas | 0 | 0 |

O delta não acrescenta comando externo, acesso à rede nem destino de escrita em produção.

### Princípios Zen e revisão técnica

A colisão agora incorpora a origem ausente de qualquer participante antes da poda. A
retomada preserva uma flag explícita do formato atual. Para o legado, a classificação nula
de caminho prova que houve encerramento, mas não diz quando ele ocorreu. A comparação com o
formato atual isola o efeito dessa falta de ordem. A migração não muda o tipo dos campos
gravados, e a leitura e a substituição do estado continuam sob a trava da sessão.

### Test Coverage

| Sensor | Status | Evidência |
|---|---|---|
| I1, F1 e R1–R8 | PASS | Dez células de `checkpoint.md` em `15a36e9`, cada uma em Bash, rc 0 e saída padrão esperada após normalização de espaço. I1 deu `1 0 1 0 0 1`. O teste de F1 escreveu seu resumo normal no stderr. |
| R8, Red e Green | PASS | A sonda executada com o script de `90837f5` saiu com rc 1, três pedidos indevidos e duas marcas ausentes. Os dois testes permanentes desta rodada de execução, contra a mesma base, rodaram com quatro subcasos vermelhos. Em `15a36e9`, a sonda e os dois testes deram rc 0. |
| R7 com a 0.4.0 real | PASS | A sonda r7 com `--expect --legado` e o script exportado de `fe38d1f` deu rc 0 e repetiu os vetores de silêncio e controles positivos. |
| Retenção | PASS | A sonda em `40-review-r2.md` com `--medir`, no script de `90837f5` e no de `15a36e9`, imprimiu em ambos `[(10, 0, 325), (100, 0, 326), (1000, 0, 327)]`. |
| Ordem no corte legado | FAIL | Doze jornadas com Stops em subprocessos. Um pedido legítimo sumiu no delta e um pedido indevido sem metadado externo no corte já existia na base. Todos os Stops tiveram offset completo e nenhum `errors.log`. |

`env -u GIT_DIR -u GIT_WORK_TREE PYTHONDONTWRITEBYTECODE=1 bash -c 'source .sdd/config.sh && eval "$TEST_CMD"'`
em `15a36e9` retornou rc 0. Foram 154 testes da loja, com três pulados pela configuração,
e 100 do hook sem falhas. Adaptadores, catálogo e 0.4.1 foram validados. Os três avisos de
versão ou de forma são de outras skills. Não houve smoke no host Claude Code ou no Windows.

### Sincronia da documentação

O teste `test_auto_docs.ReleaseTest.test_the_four_places_agree_at_0_4_0_or_later` executou
um teste com rc 0, com `PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests` e Git
isolado. O sensor `check-todo.sh --check TODO.md` em `15a36e9` confirmou 37 itens e todas
as âncoras no alvo. O commit `9f9a08c` reposicionou as duas âncoras do CHANGELOG e a de
código. A nota sobre âncoras no handoff EXEC continua histórica. A contagem histórica de
onze mutações foi reportada sem disponibilizar nesta fase as saídas individuais.

### 🧹 Dead Code & Cleanup

Varredura inline do delta, sem símbolo introduzido ou órfão. `attribution_closed` tem
leitura em `skill_path` e escrita na migração e em `_watch`. O tratamento de ausência
usa os mapas já consumidos pela poda. Os dois métodos novos são descobertos por
`unittest`. Dívida preexistente não varrida.

### Overall Grade

| Criterion | Grade | Rationale |
|-----------|-------|-----------|
| Code Quality (Zen) | B | A migração toma um caminho externo em cache como encerramento ainda vigente, sem informação de ordem para a carga local pendente. |
| Type Safety | A | O pareamento foi exercitado com JSON gravado pela 0.4.0, estado atual, caminho nulo e marcadores de origem conhecidos ou ausentes. |
| Error Handling | B | Os Stops avançam e não registram erro, mas a retomada anterior à confirmação pode perder uma retro legítima ou emitir uma indevida. |
| Security | A | A varredura de segredos não acusou achados e a mudança não abre comandos, rede ou novos destinos de escrita. |
| Performance | A | A consulta ao cache roda apenas na migração e a prova de 10 a 1.000 falhas manteve zero vínculos e só dois bytes de variação. |
| Test Coverage | B | R8 e os dez Checks passaram, mas a suíte não cruza o corte legado com a ordem invertida nem com a externa reconhecida só pelo nome. |
| Documentation | B | A versão e as âncoras passaram nos sensores, mas o handoff não preserva as saídas que permitiriam examinar as onze mutações históricas. |
| **Overall** | **B** | R8 foi fechado por um commit funcional, mas a retomada legada ainda viola o comportamento em dois cortes reproduzidos. |

As letras são as mesmas de r8. O fechamento de R8 é real, mas os critérios estritos
continuam no mesmo patamar. Esta rodada termina no platô sem outra execução automática.

## Achados da rodada

| # | Severidade | Achado | Onde |
|---|---|---|---|
| 1 | MEDIUM | Uma chamada local nova antes da atualização perde a retro se o legado só preservou a classificação de uma externa anterior. É regressão do delta. | `plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py:426–430` |
| 2 | MEDIUM | Se a 0.4.0 encerrou a atribuição pelo nome da externa e ainda não viu o caminho, a migração sem histórico ainda aceita metadado monitorado anterior. O falso pedido já existe na base. | `plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py:428–430` |
| 3 | LOW | O total de mutações detectadas no EXEC não vem com as saídas individuais disponíveis para revisão. É recorrência de evidência histórica, não falha funcional nova. | `docs/handoffs/20261125-retrofit-watch-atribuicao/20-handoff-exec.md:116–119` |

**1.** Quando a externa vem antes da chamada sem prefixo `coderabbit-pr`, a mesma confirmação
por caminho que aciona o pedido no formato atual fica em silêncio na migração. Na ordem inversa,
o silêncio é correto. As duas ordens deixam no legado o mesmo `offset=1187`, `current=null`,
`skills={}`, cache com o caminho externo nulo e listas `pending` e `done` vazias. A
comparação desconsidera apenas `created` e normaliza a raiz temporária. O mesmo metadado
local é entregue depois do corte nos dois casos.

**2.** Sem gravar o metadado da externa, a 0.4.0 já reconheceu o plugin instalado pelo nome,
mas persiste o cache vazio. Na troca de versão, a confirmação local atrasada produz
`codereview:0,0,1` tanto na base quanto no HEAD. O formato atual atravessa o mesmo corte em
silêncio, com `0,0,0`. A sessão legada sem externa ainda pede retro nos dois builds.

Da raiz, a receita a seguir consulta as versões no Git da revisão antes de isolar o Git
das fixtures. O resultado mostra alvo e contadores de trabalho, atrito e revisões, nessa
ordem. Os demais casos são controles, incluindo o fechamento de r8 com caminho confirmado.

~~~bash
PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -c "$(sed -n '/^~~~python$/,/^~~~$/{ /^~~~/!p; }' docs/handoffs/20261125-retrofit-watch-atribuicao/40-review-r9.md)"
~~~

| Corte | Legado → base `90837f5` | Legado → HEAD `15a36e9` | Atual → atual |
|---|---|---|---|
| Local antes da externa com caminho | codereview:0,0,1 | silêncio:0,0,0 | silêncio:0,0,0 |
| Local depois da externa com caminho | codereview:0,0,1 | silêncio:0,0,0 | codereview:0,0,1 |
| Local sem externa | codereview:0,0,1 | codereview:0,0,1 | codereview:0,0,1 |
| Local antes da externa só pelo nome | codereview:0,0,1 | codereview:0,0,1 | silêncio:0,0,0 |

~~~python
import os
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

from test_retrofit_watch import StopTest, identified_load, tool

p = "plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py"
scripts = {name: subprocess.check_output(["git", "-P", "show", f"{ref}:{p}"])
           for name, ref in (("old", "fe38d1f"), ("base", "90837f5"))}
for name in ("GIT_DIR", "GIT_WORK_TREE"):
    os.environ.pop(name, None)


def run(old, finish, order, external_meta):
    test = StopTest()
    test.setUp()
    try:
        w = test.w
        pending = identified_load("coderabbit-pr", w.mkt_skill, "msg_own", "toolu_own")
        external = identified_load("superpowers:brainstorming", w.other_skill, "msg_other", "toolu_other")
        external_rows = external if external_meta else external[:2]
        if order == "late":
            test.write(pending[:2], external_rows, tool(), compact=True)
        elif order == "new":
            test.write(external_rows, pending[:2], tool(), compact=True)
        else:
            test.write(pending[:2], tool(), compact=True)
        out, before = test.checked_stop(**({"script": old} if old else {}))
        assert out is None and before["current"] is None and before["skills"] == {}
        if old:
            assert "attribution_closed" not in before
            assert (str(w.other_skill) in before["classified"]) == (external_meta and order != "alone")
            before.pop("created")
            before["classified"] = {"external" if path == str(w.other_skill) else path: info
                                    for path, info in before["classified"].items()}
        test.write(pending[2:], tool(error=True), compact=True)
        out, after = test.checked_stop(**({"script": finish} if finish else {}))
        if out is not None:
            assert "`/retrofit-skill:retrofit-skill codereview`" in test.context_of(out)
        counts = after["skills"].get("full:codereview", {})
        result = "codereview" if out else "silêncio"
        return before, (result, tuple(counts.get(k, 0) for k in ("work", "friction", "reviews")))
    finally:
        test.tearDown()


with TemporaryDirectory(prefix="retrofit-r9-") as folder:
    dirpath = Path(folder)
    files = {}
    for name, source in scripts.items():
        files[name] = dirpath / f"{name}.py"
        files[name].write_bytes(source)

    for variant, old, finish in (("legado_base", files["old"], files["base"]),
                                 ("legado_atual", files["old"], None),
                                 ("moderno", None, None)):
        observations = {}
        for order, meta in (("late", True), ("new", True), ("alone", False), ("late", False)):
            state, (target, counts) = run(old, finish, order, meta)
            observations[(order, meta)] = state
            print(f"{variant} {order} meta={int(meta)} {target}:{','.join(map(str, counts))}")
        if old:
            assert observations[("late", True)] == observations[("new", True)]
            print(variant, "estado_igual_na_inversão", observations[("new", True)])
~~~

## Incrementos de conserto (R<n>)

Nenhum novo incremento. Os achados 1 e 2 foram agrupados no backlog. Os dois estados
idênticos exigem recuperar ordem e identidade anteriores ao offset para dar resultados
diferentes. Trocar apenas a condição do cache restauraria o falso pedido que R8 fechou.
O achado 3 é de documentação e não abre execução.

## O que virou incremento

- **R8**, fechado em `8b861d2`. A colisão inversa preservou as duas marcas após a poda e
  ficou em silêncio com ID repetido em leitura contínua e em disco. A 0.4.0 real com
  confirmação externa preservou o encerramento. ID fresco, legado sem externa e carga nova
  após a migração pediram retro. A célula deu `regressoes=2`.
- **Âncoras de r8**, corrigidas por `9f9a08c`. O verificador atual não reproduziu os dois desvios.

## O que foi refutado

- O achado de aspas escapadas no handoff EXEC não se sustenta no arquivo. As linhas 27 e
  162 contêm `eval "$TEST_CMD"` sem barras invertidas. O comando literal passou na suíte,
  com 154 e 100 testes. O frontmatter YAML usa aspas simples duplicadas apenas para
  representar as aspas de `bash -c`.
- A falta da saída bruta histórica não torna incorretos os valores de retenção e Red de r8.
  Com o hook de `90837f5` em diretório temporário, a sonda de retenção reproduziu 325, 326 e
  327 bytes e zero vínculos. A sonda R8 reproduziu exatamente três pedidos indevidos, e os
  dois testes novos reproduziram quatro subcasos vermelhos. Esses retestes não provam a
  execução histórica das onze mutações. O registro disso permanece no backlog.
- A poda de R8 não descartou todas as origens conhecidas nem aceitou toda chamada externa.
  A célula de R8 distinguiu ID novo e reutilizado, antes e depois da retomada. O Stop
  negativo confirmou a mensagem ativa intacta no corte e os três contadores zerados no fim.

## Achados fora de escopo

- Achados 1 e 2 → `TODO.md` › Revisão da atribuição da retrofit-watch › “A migração perde
  a ordem de cargas anteriores ao offset”. Recuperar essa ordem demandaria estender a
  leitura do legado ou definir um comportamento explícito para estados indistinguíveis.
- Achado 3 → item existente “Medições históricas da atribuição sem saída preservada”.
  A falta de saídas da varredura histórica e da lista de símbolos também é desse item.
  A varredura desta rodada foi refeita, mas não valida a execução de r8. A origem é a
  mesma missão e a gramática de `RECURRED` não a duplica.

## Pendências / Decisions for a Human

O mantenedor decide se aceita a política conservadora da migração ou autoriza recuperar
a ordem de chamadas anteriores ao offset salvo, incluindo o caso sem caminho externo.
O merge continua com o mantenedor.

## Boot da próxima fase

Os dez Checks existentes continuam em `done`. Se o mantenedor autorizar ampliar a migração,
rode primeiro a sonda desta rodada e conserve os controles de `40-review-r8.md`. Fixe o
contrato para a ausência de evidência antes de mudar o leitor legado. Rode a suíte do campo
`gate` com Git isolado. Não retire a inferência por caminho sem preservar o silêncio no
controle com a externa posterior.

### Recommended Actions

**Must Fix (CRITICAL)**

_Nenhum._

**Should Fix (HIGH)**

_Nenhum._

**Consider Fixing (MEDIUM/LOW)**

- Triar o par de cortes legados junto, com o controle de sessão sem externa. Não alterar a
  janela de correlação para corrigir uma limitação do estado da 0.4.0.
- Preservar a saída individual de mutações em execuções futuras.

**Deferred (form)**

_Nenhum._

**Outside scope (tracker)**

- O verificador não retornou itens fora das unidades analisadas e não cortou itens de forma.

_Custo da revisão — skill 2.27.38 indicada pela fase, verificação de prosa e segundo pré-scan
pela instalação 2.30.2. Três agentes por arquivo e um verificador, todos gpt-6.1-terra.
Os agentes por arquivo reportaram dez arquivos lidos integralmente e 2–12 chamadas por
agente. O verificador reportou 103 unidades e 12 chamadas. Código, testes e símbolos
analisados inline. Custo monetário não medido._
