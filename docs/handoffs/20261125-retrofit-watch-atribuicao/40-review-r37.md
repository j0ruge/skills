---
missao: 20261125-retrofit-watch-atribuicao
fase: REVIEW
rodada: 37
status: done
sessao: 01a22085-f637-7062-b6f3-c0744b55afb5
data: 2026-11-28 02:06
gate: "Em 2c4c45d8cc5cecd5b32265b024d5a09f1aec3964, árvore limpa antes da revisão. TEST_CMD isolado rc 0 (154 testes da loja, 3 pulados, 142 do hook, versão 0.4.1), 26 Checks verdes e quatro testes de release verdes. A sonda adicional retornou rc 1 com quatro vereditos invertidos. R25 pending. Gate REVIEW não aprovado. Code Quality (Zen), Error Handling e Test Coverage permanecem em B. Documentation caiu de A para B."
reviewed_head: 2c4c45d8cc5cecd5b32265b024d5a09f1aec3964
---

# Review — rodada r37 — Atribuição da retrofit-watch por mensagem

## TL;DR

R24 encerra o achado da r36. As oito retomadas originais, os 26 Checks concluídos e a suíte passaram.
A sonda da r37 reproduziu quatro vereditos invertidos quando a primeira linha de um message.id contém texto.
O defeito virou `R25 pending`. Uma divergência no inventário de EXEC foi registrada no backlog. Nota geral B, sem mudança de código.

## Nota da rodada

Fluxo Codex de `/codereview:codereview base=4eeac3c82d6f9b674b54df6c134a81aface89270` até
`2c4c45d8cc5cecd5b32265b024d5a09f1aec3964`, na branch `fix/retrofit-watch-atribuicao-mesma-mensagem`.
Nove arquivos no delta analisado com +383/−20. Um módulo Python, seu teste direto e sete documentos.
O diário não entrou na leitura nem no pré-scan. A QA de F1 já cobre vínculo válido, ausente e vazio
em dois Stops. A sonda desta rodada trata a ordem das mensagens no prefixo legado, um caso diferente.

### Secrets Detection

| Achados | Scanners | Arquivos | Linhas adicionadas | Status |
|---|---|---|---|---|
| 0 | regex e gitleaks | 9 | 383 | PASS |

Nenhum erro dos scanners. O diff não acrescenta fluxo de dados externo nem código com privilégio novo.

### Qualidade, cobertura e sincronização

| Área | Evidência |
|---|---|
| Integridade e ordem | A comparação estrita de R24 distingue mensagens com posição comprovada, mas a posição vem da primeira chamada Skill válida e ignora blocos anteriores da mesma mensagem. |
| Tipos e erros | `_transcript_id` filtra ID ausente, inválido ou vazio. Reuso mantém a posição da chamada indefinida. A falha observada é de atribuição, sem exceção ou erro de leitura. |
| Desempenho | Sem releitura do prefixo ou novo campo persistente. O estado temporário permanece limitado, e os três tetos foram retestados em isolamento. |
| Testes | `WITH_TESTS` em 1 de 1 módulos. A regressão nova testa uma chamada Skill como testemunha anterior, não um bloco de texto com o mesmo message.id. |
| Documentação | README, guia de atribuição e CHANGELOG apontam à mesma regra de precedência. O inventário do handoff não acompanha o próprio boot de R24. |

### Código morto e limpeza

Bucket A em linha. `rg -n 'message_positions|call_positions|position_bytes|test_legacy_replay_keeps_older_external_with_ignored_owner' plugins/retrofit-watch/skills/retrofit-watch/{scripts,tests}` mostrou consumo das três variáveis na função e o teste foi descoberto no unittest. Nenhum símbolo órfão no delta. Bucket B fora do escopo.

### Overall Grade

| Criterion | Grade | Rationale |
|-----------|-------|-----------|
| Code Quality (Zen) | B | O registro novo usa a primeira chamada Skill com ID válido como início da mensagem. Isso inverte a decisão em mensagens fragmentadas. |
| Type Safety | A | O registro valida IDs antes de usá-los como chaves. Metadado sem posição ou de ID repetido não entra como prova de ordem. |
| Error Handling | B | A leitura termina sem erro e avança o offset, mas pode pedir retro após carga posterior ou omitir retro com externa anterior. |
| Security | A | O pré-scan cobriu os nove arquivos em escopo sem segredos. O delta não muda permissões, destinos nem credenciais. |
| Performance | A | A ordem é coletada na passagem existente. Os tetos de mensagens, chamadas e bytes têm controles independentes que falharam quando removidos. |
| Test Coverage | B | A regressão de R24 detectou as oito mutações repetidas, mas não cobria a primeira ocorrência de um message.id em bloco de texto. |
| Documentation | B | O inventário de EXEC ainda termina em R23 apesar de o Check de R24 já existir. O boot informa corretamente como reproduzi-lo. |
| **Overall** | **B** | R24 fecha os oito casos da r36, mas quatro retomadas novas ainda decidem a atribuição na direção contrária à ordem das mensagens. |

## Achados da rodada

| # | Severidade | Achado | Onde |
|---|---|---|---|
| 1 | MEDIUM | A prova de antiguidade confunde a primeira chamada Skill com a primeira ocorrência de sua mensagem. Uma externa posterior pode ficar aposentada, e uma anterior pode encerrar a atribuição. | `plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py:870–886,899–910` |
| 2 | LOW | A tabela de artefatos de EXEC ainda diz que o checkpoint termina em R23, embora suas instruções mandem repetir R24 e as 26 células. | `docs/handoffs/20261125-retrofit-watch-atribuicao/20-handoff-exec.md:358` |

A sonda escreve o prefixo com a 0.4.0 real. Um Stop ativo avança sobre duas cargas qualificadas
sem lê-las. Depois, o hook antigo salva a monitorada ao processar um metadado que só ele aceita.
A sonda intercala dois message.id válidos e muda o tipo do primeiro bloco de um deles de Skill
para texto, sem alterar as duas chamadas nem seus vínculos. `message_positions` só é preenchido
em `_skill_origin` quando há ID de chamada. Em consequência, com texto a posição depende da
primeira chamada `Skill`, não da primeira linha da mensagem. No caso `texto_dono` isso aposenta
uma externa posterior. No caso `texto_externa` descarta a prova de antiguidade de uma externa anterior.
O plano permite que uma mensagem venha em mais de um registro e distingue a mensagem que originou a carga.

O achado 2 é só de prosa. A linha é anterior ao delta, mas o novo R24 deixa a contagem
desatualizada nesta rodada. O próprio fluxo do boot funciona e R24 está concluído.

## Incrementos de conserto (R<n>)

| R<n> | Achado | Check escrito no checkpoint |
|---|---|---|
| R25 | Achado 1 | Sonda com `--expect`, jornada F1 e a regressão durável nomeada. Exige silêncio com externa posterior e retro com externa anterior nos dois cortes. |

## O que virou incremento

~~~text
| R25 | Comparar a ordem legada pela primeira ocorrência da mensagem, inclusive em blocos de texto (r37, achado 1) | `probe=$(sed -n '/^~~~python$/,/^~~~$/{ /^~~~/!p; }' docs/handoffs/20261125-retrofit-watch-atribuicao/40-review-r37.md) && test -n "$probe" && env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -c "$probe" --expect && env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B e2e/test_retrofit_watch_stop.py && if o=$(env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -m unittest -q test_retrofit_watch.StopTest.test_legacy_replay_orders_messages_from_first_assistant_block 2>&1); then [[ "$o" == *"Ran 1 test"* && "$o" == *"OK"* ]] && printf 'regressao=1\n'; else printf '%s\n' "$o" >&2; exit 1; fi` → `texto_dono=silêncio:0,silêncio:0 texto_externa=codoreview:1,codereview:1 skill_dono=silêncio:0,silêncio:0 skill_externa=codoreview:1,codoreview:1 sem_bloco=codoreview:1,codoreview:1 linked=silêncio missing=silêncio empty=silêncio regressao=1` | pending | — |
~~~

- O achado 1 virou `R25`. O Check conserva os controles com Skill como primeiro bloco e com nenhuma
  linha anterior, além dos cenários que começam por texto e da jornada de F1.
- R24 foi fechado em `51a8a73`. A célula executou a sonda da r36, a regressão durável e F1.
  As quatro externas anteriores pediram retro e as quatro posteriores ficaram em silêncio.

## O que foi refutado

- A regressão da r36 não continua aberta. Os oito cenários do próprio Check de R24 passaram,
  incluindo os cortes em que o metadado chega no Stop seguinte. O novo defeito só apareceu ao
  variar o primeiro bloco da mensagem.
- O erro não é de chegada tardia do metadado nem de ID reutilizado. Os dois cortes discordaram
  da regra do mesmo modo, com IDs únicos. Ao substituir só o bloco inicial de texto por uma
  chamada Skill com ID próprio, os quatro vereditos voltaram ao esperado.
- A sugestão de devolver a âncora de delegação ao handoff não comprova uma lacuna recorrente.
  `00-missao.md:34` contém a seção e a condição vigentes, e `20-handoff-exec.md:485–487`
  repete a condição e remete à fonte. `657165d` mudou apenas a âncora para a fonte.
  O achado de r31 já está marcado `RESOLVED by b6b1d3c` e não foi duplicado.

## Achados fora de escopo

- Achado 2 registrado em `TODO.md`, na seção de itens abertos (`2026-11-28`).
  Não gera R<n>.

## Pendências / Decisions for a Human

A tabela não melhorou em relação à r36. Code Quality (Zen), Error Handling e Test Coverage
permaneceram em B e Documentation caiu de A para B. O gate segue não aprovado e a revisão
para neste ponto para o responsável decidir se prossegue com R25. O `verified_head` de `50-pr.md`
continua anterior a este candidato. Nenhuma ação foi tomada no PR.

## Evidências reproduzíveis

Medições na raiz em `2c4c45d8cc5cecd5b32265b024d5a09f1aec3964`, salvo a comparação com a base.

- `env -u GIT_DIR -u GIT_WORK_TREE PYTHONDONTWRITEBYTECODE=1 bash -c 'source .sdd/config.sh && eval "$TEST_CMD"'`
  retornou rc 0. Loja com 154 testes em 8,911 s, três pulados. Hook com 142 em 60,372 s.
  Adaptadores, catálogo e versões passaram, com retrofit-watch 0.4.1. As três provas nativas não foram repetidas.
- Foram executadas as 26 células `done` do `checkpoint.md` (I1, F1 e R1–R24) com
  `env -u GIT_DIR -u GIT_WORK_TREE PYTHONDONTWRITEBYTECODE=1 bash -c "$check"`, uma por vez.
  Em 74,57 s, todas retornaram rc 0 e todo stdout esperado, normalizando só espaços.
  `git merge-base --is-ancestor "$hash" HEAD` confirmou os 26 hashes. I1 deu `1 0 1 0 0 1`
  e F1 deu `linked=silêncio missing=silêncio empty=silêncio` mais o vetor de I1.
- `env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -m unittest -q test_auto_docs.ReleaseTest`
  retornou rc 0 com quatro testes.
- Sob `pipefail`, `git -P diff 4eeac3c82d6f9b674b54df6c134a81aface89270...HEAD --unified=0 -- . ':(exclude)docs/handoffs/20261125-retrofit-watch-atribuicao/checkpoint-notas.md' | bash /home/joruge/.agents/skills/codereview/scripts/scan_secrets.sh`
  retornou nove arquivos, 383 adições, zero achados e zero erros.
- Repeti `test_retrofit_watch.StopTest.test_legacy_replay_keeps_older_external_with_ignored_owner`
  em cópias temporárias com `timeout -k 2 25` e `ulimit -v 524288`. O controle executou um teste e
  passou. Oito mutações independentes falharam por asserção no mesmo teste. Elas trocaram a primeira
  posição pela última, aceitaram ID repetido, aceitaram igualdade, mantiveram a interseção sem posição,
  reiniciaram a interseção e retiraram cada um dos três tetos. Nenhum timeout ou erro de importação.
- `git blame -L 358,358 HEAD -- docs/handoffs/20261125-retrofit-watch-atribuicao/20-handoff-exec.md`
  identificou a linha antiga do inventário em `af4923b3`. O boot atual manda ler R24 e executar 26 Checks.

### Sonda de R25

Cada célula abaixo resume os dois cortes, com metadado externo no Stop da migração e no Stop
seguinte, nessa ordem. `:1` indica que o ID externo ficou aposentado. As duas chamadas continuam
com ID único e distinto. `checked_stop` mede offset e ausência de `errors.log` em cada chamada.

| Primeiro bloco | Base `4eeac3c`, ambos os cortes | HEAD, ambos os cortes | Esperado, ambos os cortes |
|---|---|---|---|
| Texto da mensagem do dono | `silêncio:0` | `codoreview:1` | `silêncio:0` |
| Texto da mensagem externa | `silêncio:0` | `silêncio:0` | `codoreview:1` |
| Skill da mensagem do dono | `silêncio:0` | `silêncio:0` | `silêncio:0` |
| Skill da mensagem externa | `silêncio:0` | `codoreview:1` | `codoreview:1` |
| Sem bloco anterior. Externa vem primeiro. | `silêncio:0` | `codoreview:1` | `codoreview:1` |

Em HEAD, a sonda com `--expect` retorna rc 1 na comparação final e imprime o vetor acima.
Para repetir, execute os três primeiros termos do Check de R25. Para observar a base, extraia
o hook com `git show 4eeac3c82d6f9b674b54df6c134a81aface89270:plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py > "$arquivo"`
e use `--script "$arquivo"` no lugar de `--expect`. Esse modo retornou rc 0 e cinco pares de silêncio.
Os transcripts são sintéticos. A gravação da 0.4.0, a migração e a leitura do estado rodam em disco.

~~~python
import argparse
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from test_retrofit_watch import SCRIPT, StopTest, assistant_text, identified_load, tool

parser = argparse.ArgumentParser()
parser.add_argument("--script", type=Path, default=SCRIPT)
parser.add_argument("--expect", action="store_true")
args = parser.parse_args()


def measure(marker_origin, marker_kind, split, legacy):
    test = StopTest()
    test.setUp()
    try:
        w = test.w
        owner = identified_load("coderabbit-pr", w.mkt_skill, "msg_owner", "toolu_owner")
        external = identified_load("brainstorming", w.other_skill, "msg_external", "toolu_external")
        if marker_origin:
            origin = f"msg_{marker_origin}"
            if marker_kind == "text":
                marker = assistant_text("Vou conferir a mudança.")[0]
                marker["message"]["id"] = origin
            else:
                marker = identified_load("brainstorming", w.other_skill, origin, "toolu_marker")[0]
            test.write([marker], compact=True)
        # A ordem das duas primeiras chamadas Skill é oposta à primeira ocorrência
        # da mensagem quando o primeiro bloco é texto do outro message.id.
        order = (owner, external) if marker_origin == "external" else (external, owner)
        test.write([load[0] for load in order], [load[1] for load in order], compact=True)
        out, initial = test.checked_stop(script=legacy)
        assert out is None and initial["current"] is None and initial["classified"] == {}

        for index in range(2):
            test.write(identified_load("codereview:coderabbit-pr", w.mkt_skill,
                                       f"msg_skip_{index}", f"toolu_skip_{index}"), compact=True)
        out, skipped = test.checked_stop(script=legacy, active=True)
        assert out is None and skipped["current"] is None and skipped["classified"] == {}
        assert skipped["offset"] > initial["offset"]

        test.write(owner[2:], tool(), compact=True)
        out, saved = test.checked_stop(script=legacy)
        key = "full:codereview"
        credits = saved["skills"][key]
        assert out is None and saved["current"] == key and "skill_calls" not in saved
        assert set(saved["classified"]) == {str(w.mkt_skill)}
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
groups = {"texto_dono": ("owner", "text"), "texto_externa": ("external", "text"),
          "skill_dono": ("owner", "skill"), "skill_externa": ("external", "skill"),
          "sem_bloco": (None, None)}
with TemporaryDirectory() as tmp:
    legacy = Path(tmp) / "legacy.py"
    legacy.write_bytes(subprocess.check_output(["git", "show", f"7e623fe:{hook}"]))
    measured = {case: ",".join(measure(origin, kind, split, legacy) for split in (False, True))
                for case, (origin, kind) in groups.items()}
print(" ".join(f"{case}={outputs}" for case, outputs in measured.items()))
if args.expect:
    expected = {case: ",".join([output] * 2) for case, output in
                zip(groups, ("silêncio:0", "codereview:1", "silêncio:0", "codereview:1", "codereview:1"))}
    assert measured == expected, measured
~~~

### Recommended Actions

**Must Fix (CRITICAL)**

_Nenhuma._

**Should Fix (HIGH)**

_Nenhuma._

**Consider Fixing (MEDIUM/LOW)**

- Executar R25 em TDD e manter os controles de R23, R24 e F1. Atualizar o inventário de EXEC em triagem.

### Cost footprint

_Skill 2.27.38 do caminho solicitado, distinta do cache Claude 2.30.2. Três agentes gpt-6.1-terra para sete documentos, com 9–16 chamadas e oito leituras integrais declaradas. Código, teste, Bucket A e reproduções em linha. Custo monetário não medido._
