---
missao: 20261125-retrofit-watch-atribuicao
fase: REVIEW
rodada: 36
status: done
sessao: 01a22075-7931-7460-860e-666014a69138
data: 2026-11-28 01:47
gate: "Em 4eeac3c82d6f9b674b54df6c134a81aface89270, árvore limpa antes da revisão. TEST_CMD isolado rc 0 (154 testes da loja, 3 pulados, 141 do hook, versão 0.4.1). Os 25 Checks, incluindo F1, e quatro testes de release passaram. A sonda nova retornou rc 1 nas quatro variantes com externa anterior. Code Quality (Zen), Error Handling e Test Coverage seguem abaixo de A. Documentation subiu a A. R24 pending e gate REVIEW não aprovado."
reviewed_head: 4eeac3c82d6f9b674b54df6c134a81aface89270
---

# Review — rodada r36 — Atribuição da retrofit-watch por mensagem

## TL;DR

R23 corrigiu as quatro retomadas da r35 em que a externa era posterior. A ordem inversa expôs uma regressão no mesmo caminho: a externa comprovadamente anterior passou a encerrar a atribuição.
A suíte, os 25 Checks concluídos e os quatro testes de release passaram. O cenário novo falhou em quatro retomadas com estado gravado pela 0.4.0 real.
A nota geral é B. O único achado virou `R24 pending`, sem alteração de código nesta rodada.

## Nota da rodada

Fluxo Codex de `/codereview:codereview base=3371edd9d10b2a970900d1be34ef29a0f55857c4`
até `4eeac3c82d6f9b674b54df6c134a81aface89270`, na branch `fix/retrofit-watch-atribuicao-mesma-mensagem`.
Sete commits. Nove arquivos analisados: um módulo Python, seu teste direto e sete documentos. O delta
analisado tem 353 adições e 21 remoções, excluindo o diário conforme o escopo. A QA de F1 distingue
vínculo válido, ausente e vazio em dois Stops. O achado desta rodada envolve um prefixo real da 0.4.0
e a ordem entre a chamada externa e todos os candidatos, sem repetir o defeito de F1.

### Secrets Detection

| Achados | Scanners | Arquivos | Linhas adicionadas | Status |
|---|---|---|---|---|
| 0 | regex e gitleaks | 9 | 353 | PASS |

Sem erro de scanner. O delta não muda permissões, destinos de dados nem dependências de produção.

### Qualidade, cobertura e sincronização

| Área | Evidência |
|---|---|
| Zen e integridade | Uma guarda identifica o metadado rejeitado compatível com o dono salvo. O estado agregado descarta a precedência do ID externo até quando a ordem de todas as chamadas a confirma. |
| Tipos e segurança | A chave do dono só é lida de um dicionário. `Scanner.skill_path` acrescenta um sinal interno de sucesso, consumido pelo replay. O chamador normal continua ignorando o retorno. |
| Desempenho | Não há nova leitura do prefixo nem novo registro persistido. A mudança limpa o conjunto já limitado da interseção. Os Checks de memória e de limite continuaram verdes. |
| Cobertura | `WITH_TESTS` em 1 de 1 módulos alterados. A regressão adicionada testa posições do metadado ignorado e o controle por outro dono, mas não a precedência comprovada do ID externo com o mesmo dono possível. |
| Sincronização | Os três grupos de documentação foram revisados. A receita histórica de r34 lê o blob publicado e reprova com blob ausente ou código vazio. O handoff situa as medidas de Exec no commit de R23. |

### Código morto e limpeza

Bucket A em linha. O único contrato interno alterado foi o retorno de `skill_path`. A busca
`rg -n 'skill_path\(' --glob '*.py' plugins/retrofit-watch/skills/retrofit-watch` confirmou o chamador
normal e a nova checagem no replay. O teste novo foi descoberto e executado. Nenhum símbolo do delta
ficou órfão. Bucket B fora do escopo.

### Overall Grade

| Criterion | Grade | Rationale |
|-----------|-------|-----------|
| Code Quality (Zen) | B | A decisão descarta a prova por ID ao encontrar um dono possível, sem distinguir se a externa é anterior a esse dono. |
| Type Safety | A | A guarda verifica o tipo da classificação antes de consultar sua chave e só o replay consome o novo retorno booleano ou nulo. |
| Error Handling | B | Em quatro retomadas válidas o Stop avança sem erro, mas fecha a atribuição e omite a retro mesmo com a externa comprovadamente anterior. |
| Security | A | O pré-scan não encontrou segredos e o delta não introduz permissões, destinos ou tratamento de credenciais. |
| Performance | A | A leitura segue limitada como antes, sem nova passagem ou crescimento de estado. Os controles de limite e memória passaram. |
| Test Coverage | B | A suíte detecta o falso positivo da r35, mas ficou verde diante do falso negativo que surge ao inverter apenas a ordem das chamadas. |
| Documentation | A | A reprodução histórica de r34 passou com o blob publicado e falhou nos dois controles negativos. O handoff identifica o SHA e as limitações das medições. |
| **Overall** | **B** | O falso positivo da r35 foi corrigido, mas a perda de atribuição com externa anterior impede aprovar este delta. |

## Achados da rodada

| # | Severidade | Achado | Onde |
|---|---|---|---|
| 1 | MEDIUM | O replay limpa a interseção inteira quando rejeita metadado de um possível dono. Assim perde a prova de antiguidade de uma externa anterior a todos os candidatos e o Stop deixa de pedir retro. | `plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py:875–898,931–935` |

A 0.4.0 lê as chamadas sem qualificador da externa e do dono que será salvo. Um Stop ativo avança
sobre duas cargas qualificadas de `codereview` sem processá-las. O Stop seguinte da 0.4.0 lê só o
metadado do dono original, guarda seu caminho no cache e credita trabalho a ele. Já o replay lê as
duas cargas ignoradas e aposenta os IDs das chamadas anteriores. Quando chega ao metadado do dono
original, rejeita seu ID. A nova guarda limpa `common_retired` mesmo quando o ID externo tem origem
inequívoca anterior à chamada original e também às duas cargas ignoradas.

A sonda muda apenas a posição das duas chamadas iniciais. No cenário anterior, qualquer um dos
três candidatos é posterior à externa. Não é necessário eleger um dono para preservar o ID externo.
Ao inverter a posição, a externa passa a ser posterior ao dono original, e silenciar é correto.
O efeito observado é perda do crédito do trabalho novo e do pedido de retro. O offset avança
normalmente, o histórico anterior permanece e nenhum `errors.log` é criado.

## Incrementos de conserto (R<n>)

| R<n> | Achado | Check escrito no checkpoint |
|---|---|---|
| R24 | Achado 1 | Sonda com `--expect`, jornada F1 e regressão durável nomeada. Exige pedido nas quatro retomadas com externa anterior e silêncio nas quatro com externa posterior. |

## O que virou incremento

~~~text
| R24 | Conservar a aposentadoria da externa comprovadamente anterior ao possível dono rejeitado no replay (r36, achado 1) | `probe=$(sed -n '/^~~~python$/,/^~~~$/{ /^~~~/!p; }' docs/handoffs/20261125-retrofit-watch-atribuicao/40-review-r36.md) && test -n "$probe" && env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -c "$probe" --expect && env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B e2e/test_retrofit_watch_stop.py && if o=$(env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -m unittest -q test_retrofit_watch.StopTest.test_legacy_replay_keeps_older_external_with_ignored_owner 2>&1); then [[ "$o" == *"Ran 1 test"* && "$o" == *"OK"* ]] && printf 'regressao=1\n'; else printf '%s\n' "$o" >&2; exit 1; fi` → `anterior=codereview:1,codereview:1,codereview:1,codereview:1 posterior=silêncio:0,silêncio:0,silêncio:0,silêncio:0 linked=silêncio missing=silêncio empty=silêncio regressao=1` | pending | — |
~~~

- O achado 1 virou `R24`. O Check cruza caminho repetido ou distinto com metadado no Stop da migração ou no seguinte. Exige conservar só a aposentadoria comprovada, sem voltar a ignorar externa posterior.
- `R23` foi fechado em `f82e1d5`. A célula confirmou `novo=silêncio:0,silêncio:0 repetido=silêncio:0,silêncio:0 controle=codereview:1,codereview:1`, F1 verde e uma regressão durável. A sonda nova confirma separadamente o silêncio nos quatro controles com externa posterior.
- A receita histórica de r34 também foi corrigida em `f82e1d5`. O reteste confirmou rc 0 com o blob publicado, rc 128 com blob ausente e rc 1 sem código. Não foi registrada nova pendência para esse item.

## O que foi refutado

- Restaurar a interseção anterior sem distinguir o dono ignorado desfaria R23. Com o hook de `3371edd`, a sonda nova em modo de observação emitiu `codereview:1` nas quatro retomadas em que a externa deveria encerrar a atribuição.
- Escolher outro caminho ou exigir uma retomada adicional não evita o falso negativo. A sonda produziu `silêncio:0` com os dois caminhos e nos dois cortes de Stop, mantendo os créditos legados.
- A receita de r34 não passa mais com comando vazio. Substituir o blob por `HEAD:README.md` manteve a leitura Git válida, mas retornou rc 1 pelo teste de código não vazio.

## Achados fora de escopo

Nenhum achado novo.

## Pendências / Decisions for a Human

Nenhuma decisão nova. As notas de código, erro e cobertura seguem B. Documentation subiu a A
com a correção da receita em `f82e1d5`, então a tabela não repete todas as letras da r35. O gate
ainda não fecha e `R24` volta à execução em TDD. O `verified_head` de `50-pr.md` é anterior ao
candidato revisado. Não houve ação no PR.

## Evidências reproduzíveis

Medições na raiz em `4eeac3c82d6f9b674b54df6c134a81aface89270`, salvo a comparação explícita com o blob histórico.

- `env -u GIT_DIR -u GIT_WORK_TREE PYTHONDONTWRITEBYTECODE=1 bash -c 'source .sdd/config.sh && eval "$TEST_CMD"'` → rc 0. Adaptadores e catálogo válidos. Loja com 154 testes, 3 pulados, em 9,167 s. Hook com 141 testes em 58,720 s. Validação de versões confirmou a 0.4.1. Não foram repetidas as três provas nativas puladas.
- As 25 células concluídas de `checkpoint.md` (I1, F1 e R1–R23) foram executadas individualmente com `env -u GIT_DIR -u GIT_WORK_TREE bash -c "$check"`. Resultado 25/25 em 69,46 s, comparando rc e todo o stdout, com normalização só de espaços. `git merge-base --is-ancestor "$hash" HEAD` confirmou os 25 hashes. I1 devolveu `1 0 1 0 0 1` e F1 devolveu `linked=silêncio missing=silêncio empty=silêncio` mais o vetor de I1.
- `env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -m unittest -q test_auto_docs.ReleaseTest` → quatro testes, rc 0.
- Sob `pipefail`, `git -P diff 3371edd9d10b2a970900d1be34ef29a0f55857c4...HEAD --unified=0 -- . ':(exclude)docs/handoffs/20261125-retrofit-watch-atribuicao/checkpoint-notas.md' | bash /home/joruge/.agents/skills/codereview/scripts/scan_secrets.sh` → nove arquivos, 353 adições, zero achados e zero erros.
- O bloco Bash da sonda de r34 foi extraído com `sed -n '/^~~~bash$/, /^~~~$/{ /^~~~/!p; }' docs/handoffs/20261125-retrofit-watch-atribuicao/40-review-r34.md`. Executado com `bash -c "$recipe"`, retornou rc 0 com o blob do relatório. Substituir o SHA por 40 zeros retornou rc 128. Trocar o blob por `HEAD:README.md` retornou rc 1.

### Sonda de R24

A 0.4.0 real é carregada de `7e623fe` para gravar o estado, e `checked_stop` verifica em cada chamada o offset e a ausência de `errors.log`.
Os quatro resultados de cada grupo correspondem, em ordem, a caminho repetido e caminho distinto, cada um sem e com um Stop separado para migrar. Em cada par, o primeiro caso não tem esse Stop separado. O sufixo `:1` indica que o ID externo ficou aposentado. O `:0` indica ausência no registro.

~~~bash
probe=$(sed -n '/^~~~python$/,/^~~~$/{ /^~~~/!p; }' docs/handoffs/20261125-retrofit-watch-atribuicao/40-review-r36.md) &&
  test -n "$probe" &&
  env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -c "$probe" --expect
~~~

O Check retornou rc 1 na asserção final. Para a comparação com a base, extraia
`git show 3371edd9d10b2a970900d1be34ef29a0f55857c4:plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py > "$arquivo"`
e use `--script "$arquivo"` no lugar de `--expect`. Essa execução devolveu rc 0 em modo de observação.

| Caso | Base observada (cada uma das 4) | HEAD observado (cada uma das 4) | Esperado (cada uma das 4) |
|---|---|---|---|
| Externa anterior à chamada original | `codereview:1` | `silêncio:0` | `codereview:1` |
| Externa posterior à chamada original | `codereview:1` | `silêncio:0` | `silêncio:0` |

~~~python
import argparse
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from test_retrofit_watch import SCRIPT, StopTest, identified_load, make_skill, tool

parser = argparse.ArgumentParser()
parser.add_argument("--script", type=Path, default=SCRIPT)
parser.add_argument("--expect", action="store_true")
args = parser.parse_args()

def measure(older, distinct_path, split, legacy):
    test = StopTest()
    test.setUp()
    try:
        world = test.w
        path = make_skill(world.mkt_skill.parent, "codereview") if distinct_path else world.mkt_skill
        original = identified_load(path.name, path, "msg_a", "toolu_original")
        external = identified_load("brainstorming", world.other_skill, "msg_z", "toolu_external")
        for load in ((external, original) if older else (original, external)):
            test.write(load[:2], compact=True)
        out, initial = test.checked_stop(script=legacy)
        assert out is None and initial["current"] is None and initial["classified"] == {}

        for suffix in ("1", "2"):
            test.write(identified_load("codereview:coderabbit-pr", world.mkt_skill,
                                       f"msg_skip_{suffix}", f"toolu_skip_{suffix}"), compact=True)
        out, skipped = test.checked_stop(script=legacy, active=True)
        assert out is None and skipped["current"] is None and skipped["classified"] == {}
        assert skipped["offset"] > initial["offset"]

        test.write(original[2:], tool(), compact=True)
        out, saved = test.checked_stop(script=legacy)
        key = "full:codereview"
        credits = saved["skills"][key]
        assert out is None and saved["current"] == key and "skill_calls" not in saved
        assert set(saved["classified"]) == {str(path)}
        assert (credits["work"], credits["friction"], credits["reviews"]) == (1, 0, 0)

        if split:
            out, migrated = test.checked_stop(script=args.script)
            assert out is None and migrated["current"] == key and migrated["skills"][key] == credits
            assert migrated["offset"] == saved["offset"]
        test.write(external[2:], tool(error=True), compact=True)
        out, after = test.checked_stop(script=args.script)
        retired = int("toolu_external" in after["retired_skill_calls"])
        if out is None:
            assert after["current"] is None and after["attribution_closed"]
            assert after["skills"][key] == credits
            return f"silêncio:{retired}"
        assert "`/retrofit-skill:retrofit-skill codereview`" in test.context_of(out)
        assert after["current"] == key and not after["attribution_closed"]
        assert after["skills"][key]["reviews"] == 1
        return f"codereview:{retired}"
    finally:
        test.tearDown()

hook = "plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py"
with TemporaryDirectory() as tmp:
    legacy = Path(tmp) / "legacy.py"
    legacy.write_bytes(subprocess.check_output(["git", "show", f"7e623fe:{hook}"]))
    measured = {case: ",".join(measure(older, distinct, split, legacy)
                               for distinct in (False, True) for split in (False, True))
                for case, older in (("anterior", True), ("posterior", False))}
print(" ".join(f"{case}={outputs}" for case, outputs in measured.items()))
if args.expect:
    assert measured == {
        "anterior": ",".join(["codereview:1"] * 4),
        "posterior": ",".join(["silêncio:0"] * 4),
    }, measured
~~~

### Recommended Actions

**Must Fix (CRITICAL)**

_Nenhuma._

**Should Fix (HIGH)**

_Nenhuma._

**Consider Fixing (MEDIUM/LOW)**

- Executar `R24` em TDD. Preservar a antiguidade quando comprovada para todos os candidatos, sem reintroduzir o falso positivo de R23.

### Cost footprint

_Skill 2.27.38 do caminho solicitado, separada do cache Claude 2.30.2. Três agentes gpt-6.1-terra para sete documentos, com 10–11 chamadas declaradas e seis leituras integrais reportadas. Módulo, teste, Bucket A e reproduções em linha. Custo monetário não medido._
