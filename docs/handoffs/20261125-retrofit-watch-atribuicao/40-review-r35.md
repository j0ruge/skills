---
missao: 20261125-retrofit-watch-atribuicao
fase: REVIEW
rodada: 35
status: done
sessao: 01a22065-1c18-7780-842c-5099a5e2f24c
data: 2026-11-28 01:30
gate: "Em 3371edd9d10b2a970900d1be34ef29a0f55857c4, antes de editar, árvore limpa e TEST_CMD com Git isolado rc 0 (154 testes da loja, 3 pulados, e 140 do hook, versão 0.4.1). 24 de 24 Checks, F1 e quatro testes de release passaram. A sonda nova voltou rc 1 em dois cenários, com e sem corte na migração. Platô frente à r34 em Code Quality (Zen), Error Handling, Test Coverage, Documentation e Overall. R23 pending e gate REVIEW não aprovado."
reviewed_head: 3371edd9d10b2a970900d1be34ef29a0f55857c4
---

# Review — rodada r35 — Atribuição da retrofit-watch por mensagem

## TL;DR

O R22 fechou os dois achados funcionais de r34 e as quatro receitas documentais voltaram a falhar quando devem.
Uma nova regressão reproduzida com a 0.4.0 real virou R23. A retomada pode creditar trabalho mesmo após uma externa de mensagem posterior.
A suíte e os 24 Checks anteriores passaram. O achado de reprodução documental ficou no backlog. A nota geral é B e houve platô.

## Nota da rodada

Fluxo Codex da skill `/codereview:codereview base=880640757cfd70a1a06aecf75c952aa4e0b184a8` até `3371edd9d10b2a970900d1be34ef29a0f55857c4`, com Python e `unittest`.
Seis commits e dez arquivos analisados, com 467 linhas adicionadas e 25 removidas. Escopo de código em
`retrofit_watch.py` e `test_retrofit_watch.py`. A documentação do delta inclui
`20-handoff-exec.md`, `40-review-r24.md` a `40-review-r27.md`, `40-review-r34.md`,
`checkpoint.md` e `TODO.md`. O diário não integra a análise. Não houve mudança de interface pública.

### Secrets Detection

| Achados | Scanners | Arquivos | Linhas adicionadas | Status |
|---|---|---|---|---|
| 0 | regex e gitleaks | 10 | 467 | PASS |

Nenhum erro de scanner. O delta não muda autorização nem introduz dependências de produção.

### Qualidade, cobertura e sincronização

| Área | Evidência |
|---|---|
| Zen e integridade | O reaproveitamento de IDs é revogado no caminho de chamadas. A prova comum de precedência não considera o metadado compatível barrado no caminho de metadados. |
| Tipos e segurança | O ID de chamada chega ao replay como string validada ou nulo. O novo acesso ao valor de classificação exige um dicionário antes de ler a chave. |
| Desempenho | A leitura continua com os mesmos limites. A prova comum é limitada pelo registro de IDs aposentados. O conjunto de caminhos replica as chaves já salvas, uma vez na migração. |
| Cobertura | `WITH_TESTS` em 1 de 1 módulos mudados. O teste direto tem duas novas regressões e a sonda de R22 usa a 0.4.0 real. Falta o metadado que a 0.4.0 lê depois de pular duas cargas compatíveis, mas que o replay rejeita. |
| Sincronização | As quatro receitas reparadas retornaram as contagens exatas com Git de fixture e falharam nos dois controles negativos. A receita nova da r34 não distingue o commit do código e o commit que contém o relatório. |

### Código morto e limpeza

Bucket A em linha. `ReplayScanner` usa os novos estados da prova em `_watch`, `skill_path` e no retorno da função.
As duas regressões chamam `save_legacy_owner` e são descobertas pela suíte. Sem símbolo novo sem uso ou chamador removido.
Bucket B fora do delta.

### Overall Grade

| Criterion | Grade | Rationale |
|-----------|-------|-----------|
| Code Quality (Zen) | B | A interseção de IDs considera só as atribuições aceitas pelo replay, embora a 0.4.0 também possa ter aceitado metadado barrado pelo scanner novo. |
| Type Safety | A | Os estados novos usam IDs validados, conjuntos de chaves e guarda de dicionário antes de inspecionar a classificação. |
| Error Handling | B | A migração aceita uma prova incompleta, ignora uma externa posterior e emite retro indevida em quatro execuções com estado legado válido. |
| Security | A | O pré-scan encontrou zero segredos e zero erros, sem mudança nas permissões ou na exposição de dados. |
| Performance | A | Não há releitura adicional do transcript, e os novos conjuntos são limitados pelos IDs retidos e caminhos em cache. Os Checks de memória e limite passaram. |
| Test Coverage | B | Os 24 Checks continuam verdes, mas não cobrem a seleção legada feita só por metadado que o replay posterior rejeita. |
| Documentation | B | As quatro receitas de pré-scan foram reparadas, mas a sonda de r34 é referenciada a partir de um SHA em que seu arquivo não existe. |
| **Overall** | **B** | R22 resolveu os casos de r34, mas introduziu falso positivo na retomada da 0.4.0. |

## Achados da rodada

| # | Severidade | Achado | Onde |
|---|---|---|---|
| 1 | MEDIUM | A migração aposenta o ID de uma externa posterior quando o replay rejeita o metadado da única carga monitorada efetivamente lida pela 0.4.0. A externa é ignorada e o Stop pede retro indevidamente. | `plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py:871–893,926–930` |
| 2 | LOW | O comando de r34 extrai a sonda de um relatório ausente no SHA indicado. Na ausência do arquivo, `sed` falha e o interpretador recebe código vazio e retorna rc 0. | `docs/handoffs/20261125-retrofit-watch-atribuicao/40-review-r34.md:122` |

No achado 1, um Stop ativo da 0.4.0 avança sobre duas invocações qualificadas de `codereview` sem lê-las.
O Stop normal seguinte ativa `codereview` pelo metadado de uma invocação anterior, sem qualificador no nome.
A chamada externa pertence à mensagem seguinte à dessa invocação e só entrega seu metadado depois da atualização.
O replay aceita as duas cargas que o Stop ativo pulou e rejeita o metadado da carga realmente observada porque seu ID já foi aposentado.
Assim, `common_retired` só prova que a externa é anterior às duas cargas que foram puladas. A guarda de
`skill_path` revoga `proved_owner`, mas não revê `common_retired`.

A falha muda o pedido e o crédito futuro, sem corromper estado nem impedir o avanço de Stop. A sonda verifica
offset, ausência de `errors.log` e preservação do histórico anterior no caminho esperado de silêncio.

## Incrementos de conserto (R<n>)

| R<n> | Achado | Check escrito no checkpoint |
|---|---|---|
| R23 | Achado 1 | Sonda com `--expect`, jornada F1 e uma regressão durável nomeada. Exige silêncio nas quatro retomadas e mantém o controle que pede retro. |

~~~text
| R23 | Não aposentar a chamada externa quando o replay ignora uma carga que a 0.4.0 pôde aceitar como dona (r35, achado 1) | `probe=$(sed -n '/^~~~python$/,/^~~~$/{ /^~~~/!p; }' docs/handoffs/20261125-retrofit-watch-atribuicao/40-review-r35.md) && test -n "$probe" && env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -c "$probe" --expect && env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B e2e/test_retrofit_watch_stop.py && if o=$(env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -m unittest -q test_retrofit_watch.StopTest.test_legacy_replay_preserves_external_after_ignored_owner 2>&1); then [[ "$o" == *"Ran 1 test"* && "$o" == *"OK"* ]] && printf 'regressao=1\n'; else printf '%s\n' "$o" >&2; exit 1; fi` → `novo=silêncio:0,silêncio:0 repetido=silêncio:0,silêncio:0 controle=codereview:1,codereview:1 linked=silêncio missing=silêncio empty=silêncio regressao=1` | pending | — |
~~~

## O que virou incremento

- O achado 1 virou `R23`. O Check exige silêncio para a externa posterior com caminho novo ou repetido, com ou sem Stop extra antes do metadado. A externa anterior a todos os donos compatíveis continua sendo ignorada. Nenhum código foi alterado nesta rodada.
- `R22` foi executado em `1863fc2`. O Check passou e confirmou `older_unique=codereview older_same=codereview older_later=codereview older_monitored=codereview between=silêncio observed_new_path=codereview`, F1 verde e duas regressões duráveis. A mesma sonda no código da base mostrou as quatro saídas erradas de r34.
- A limitação das quatro receitas de pré-scan também fechou em `1863fc2`. O reteste com Git de fixture confirmou as quatro contagens e as falhas por SHA ou contagem inválidos.

## O que foi refutado

- Remover toda a importação de IDs aposentados da migração ambígua não serve. O cenário `controle` da sonda usa uma externa realmente anterior a ambas as cargas. O HEAD pede `codereview` nas duas modalidades. A base, sem a importação, silencia em ambas.
- A regressão não exige divergência de cache ou snapshot escrito à mão. Com um caminho repetido, a 0.4.0 grava o mesmo caminho que consta do replay. Com um caminho novo, ela grava apenas o caminho que de fato viu. Ambos reproduzem o mesmo falso positivo com estado real.
- As quatro receitas de pré-scan de r24–r27 não ficam verdes com revisão ou contagem errada no código revisado. As reexecuções devolveram rc 128 e rc 1, respectivamente.

## Achados fora de escopo

- Achado 2 registrado em `TODO.md` sob Documentação da loja. A comparação separa o SHA do código do SHA em que a sonda foi publicada. É um problema de receita histórica, sem incremento funcional.

## Pendências / Decisions for a Human

As letras da r34 se repetiram. Code Quality (Zen), Error Handling e Test Coverage seguem B.
Documentation e Overall também continuam B. O resultado de `1863fc2` fechou os casos anteriores,
mas não removeu o bloqueio funcional. Registro o platô no gate e encerro esta rodada com `R23` pendente.
A decisão de prosseguir após o platô cabe ao mantenedor. O `verified_head` de `50-pr.md`
é anterior ao candidato revisado. Nenhuma ação foi feita no PR.

## Evidências reproduzíveis

Medições na raiz em `3371edd9d10b2a970900d1be34ef29a0f55857c4`, salvo os controles que carregam um blob histórico.

- `env -u GIT_DIR -u GIT_WORK_TREE PYTHONDONTWRITEBYTECODE=1 bash -c 'source .sdd/config.sh && eval "$TEST_CMD"'` → rc 0. Adaptadores e catálogo válidos. Loja com 154 testes, três pulados, em 8,980 s. Hook com 140 testes em 57,971 s. Validação da versão 0.4.1 passou. As três provas nativas puladas não foram repetidas.
- As 24 células `done` do checkpoint (I1, F1 e R1–R22) foram executadas individualmente com `bash -c "$check"` e sem `GIT_DIR` e `GIT_WORK_TREE`. Todos os comandos retornaram rc 0 e o stdout esperado, normalizando só espaços. `git merge-base --is-ancestor "$hash" HEAD` confirmou os 24 hashes. A série levou 70,11 s. I1 voltou `1 0 1 0 0 1` e F1 voltou `linked=silêncio missing=silêncio empty=silêncio`.
- `env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -m unittest -q test_auto_docs.ReleaseTest` → quatro testes, rc 0.
- Sob `pipefail`, `git -P diff 880640757cfd70a1a06aecf75c952aa4e0b184a8...HEAD --unified=0 -- . ':(exclude)docs/handoffs/20261125-retrofit-watch-atribuicao/checkpoint-notas.md' | bash /home/joruge/.agents/skills/codereview/scripts/scan_secrets.sh` → 10 arquivos, 467 linhas, zero segredos e zero erros.
- Executei os blocos Bash de pré-scan em r24–r27 com `GIT_DIR` e `GIT_WORK_TREE` apontando para uma fixture nova de `git init`. Os quatro deram rc 0, com 530, 452, 327 e 428 linhas. Com o primeiro SHA trocado por 40 zeros deram rc 128. Somando um à contagem exigida no `jq` deram rc 1.
- `git cat-file -e '880640757cfd70a1a06aecf75c952aa4e0b184a8:docs/handoffs/20261125-retrofit-watch-atribuicao/40-review-r34.md'` → rc 128. O mesmo comando com `846925a`, commit que criou o relatório, → rc 0. Em diretório temporário sem esse relatório, o comando literal produziu erro de leitura no `sed` e rc 0 no Python. Com o relatório extraído de `846925a` e o hook da base em `--script`, a sonda executou os seis casos, incluindo os quatro desvios registrados em r34.

### Sonda de R23

Extraia a sonda deste relatório na raiz que contém o arquivo. Para repetir a observação da base sem mover o checkout,
salve apenas o módulo Python com `git show 880640757cfd70a1a06aecf75c952aa4e0b184a8:plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py > "$arquivo"`
em um diretório temporário e use `--script "$arquivo"` no lugar de `--expect`. A sonda carrega a 0.4.0 de `7e623fe`
para gravar os snapshots de verdade.

~~~bash
probe=$(sed -n '/^~~~python$/,/^~~~$/{ /^~~~/!p; }' docs/handoffs/20261125-retrofit-watch-atribuicao/40-review-r35.md) && test -n "$probe" && env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -c "$probe" --expect
~~~

O primeiro resultado de cada par vem de migração e metadado no mesmo Stop. O segundo vem de migração em um Stop e metadado no seguinte.
O dígito indica se o ID externo ficou aposentado depois da retomada.

| Caso | Base em observação | HEAD em observação | Esperado |
|---|---|---|---|
| `novo` | silêncio:0,silêncio:0 | codereview:1,codereview:1 | silêncio:0,silêncio:0 |
| `repetido` | silêncio:0,silêncio:0 | codereview:1,codereview:1 | silêncio:0,silêncio:0 |
| `controle` | silêncio:0,silêncio:0 | codereview:1,codereview:1 | codereview:1,codereview:1 |

O comando com `--expect` retornou rc 1 no HEAD. Em modo de observação as seis execuções terminaram normalmente.

~~~python
import argparse
import re
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from test_retrofit_watch import SCRIPT, StopTest, identified_load, make_skill, tool

p = argparse.ArgumentParser()
p.add_argument("--script", type=Path, default=SCRIPT)
p.add_argument("--expect", action="store_true")
args = p.parse_args()

def run(case, split, legacy):
    t = StopTest()
    t.setUp()
    try:
        w = t.w
        alt = make_skill(w.mkt_skill.parent, "codereview") if case == "novo" else w.mkt_skill
        original = identified_load(alt.name, alt, "msg_original", "toolu_original")
        externa = identified_load("brainstorming", w.other_skill, "msg_externa", "toolu_externa")
        a = identified_load("codereview:coderabbit-pr", w.mkt_skill, "msg_a", "toolu_a")
        b = identified_load("codereview:coderabbit-pr", w.mkt_skill, "msg_b", "toolu_b")
        if case != "controle":
            t.write(original[:2], compact=True)
        t.write(externa[:2], compact=True)
        if case != "controle":
            out, before_skip = t.checked_stop(script=legacy)
            assert out is None and before_skip["current"] is None and before_skip["classified"] == {}
        t.write(a, b, compact=True)
        if case != "controle":
            out, skipped = t.checked_stop(script=legacy, active=True)
            assert out is None and skipped["current"] is None and skipped["classified"] == {}
        if case != "controle":
            t.write(original[2:], compact=True)
        t.write(tool(), compact=True)
        out, before = t.checked_stop(script=legacy)
        key = "full:codereview"
        assert out is None and "skill_calls" not in before and before["current"] == key
        assert before["skills"][key]["work"] == 1
        assert set(before["classified"]) == {str(alt)}
        if split:
            out, migrated = t.checked_stop(script=args.script)
            assert out is None and migrated["current"] == key
            assert migrated["skills"] == before["skills"]
        t.write(externa[2:], tool(error=True), compact=True)
        out, after = t.checked_stop(script=args.script)
        targets = re.findall(r"\x60/retrofit-skill:retrofit-skill ([a-z-]+)\x60", t.context_of(out)) if out else []
        assert len(targets) == bool(out), targets
        target = targets[0] if targets else "silêncio"
        assert after["skills"][key]["reviews"] == int(bool(out))
        assert bool(after["attribution_closed"]) == (out is None)
        if out is None:
            assert after["current"] is None
            assert after["skills"][key] == before["skills"][key]
        return f"{target}:{int('toolu_externa' in after['retired_skill_calls'])}"
    finally:
        t.tearDown()

cases = ("novo", "repetido", "controle")
hook = "plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py"
with TemporaryDirectory() as tmp:
    legacy = Path(tmp) / "legacy.py"
    legacy.write_bytes(subprocess.check_output(["git", "show", f"7e623fe:{hook}"]))
    observed = {case: ",".join(run(case, split, legacy) for split in (False, True)) for case in cases}
print(" ".join(f"{k}={v}" for k, v in observed.items()))
if args.expect:
    assert observed == {
        "novo": "silêncio:0,silêncio:0",
        "repetido": "silêncio:0,silêncio:0",
        "controle": "codereview:1,codereview:1",
    }, observed
~~~

### Recommended Actions

**Must Fix (CRITICAL)**

_Nenhuma._

**Should Fix (HIGH)**

_Nenhuma._

**Consider Fixing (MEDIUM/LOW)**

- Executar `R23` em TDD se a missão continuar, mantendo os controles de R22.
- Na triagem documental, separar os SHAs do relatório e do módulo usado para repetir a evidência de r34.

### Cost footprint

_Skill 2.27.38 do caminho solicitado. Cache Claude 2.30.2 identificado e não usado. Três agentes gpt-6.1-terra em sete documentos, com 6–9 chamadas cada. Código, testes, sweep do Bucket A e reproduções em linha. Custo monetário não medido._
