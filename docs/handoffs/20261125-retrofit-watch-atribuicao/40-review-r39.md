---
missao: 20261125-retrofit-watch-atribuicao
fase: REVIEW
rodada: 39
status: done
sessao: 01a220aa-c40e-7e32-8869-a813f2e11053
data: 2026-11-28 02:45
gate: "Em 7a9d42cca8c5d525c13034b8528b151e25c848f7, árvore limpa antes da revisão. TEST_CMD isolado rc 0 (154 testes da loja, 3 pulados, 144 do hook, versão 0.4.1). Passaram os 28 Checks, a jornada F1, a sonda adicional e os quatro testes de release. R26 confirmado em 0bd4efa. Seis critérios técnicos em A, Documentation e Overall em B. Nenhum incremento pendente. A rodada atende ao piso de REVIEW."
reviewed_head: 7a9d42cca8c5d525c13034b8528b151e25c848f7
---

# Review — rodada r39 — Atribuição da retrofit-watch por mensagem

## TL;DR

R26 preserva a ordem já provada quando o registro de mensagens enche. A sonda da 0.4.0, os 28 Checks e a suíte passaram.
Uma frase do handoff troca o alvo da retro. Foi registrada no backlog, sem incremento.
Seis critérios técnicos em A. Documentation e Overall em B. A rodada atende ao piso de REVIEW.

## Nota da rodada

Fluxo Codex de `/codereview:codereview base=a7903595adc9ed755a731a815d4e1221ee0a7021` até
`7a9d42cca8c5d525c13034b8528b151e25c848f7`, na branch `fix/retrofit-watch-atribuicao-mesma-mensagem`
com base configurada `main`. Seis commits. O escopo de conteúdo tem dez arquivos (+376/−26),
com um módulo Python, seu teste direto e oito documentos. O diário append-only ficou fora da leitura
e do pré-scan. O módulo e o teste foram lidos no entorno dos hunks. Não houve interface renomeada.
A QA de `08f09a1` já especifica o silêncio em dois Stops para vínculo válido, ausente e vazio
após carga posterior. Esta rodada repetiu essa jornada sem registrar o achado de QA de novo.

### Secrets Detection

| Achados | Scanners | Arquivos | Linhas adicionadas | Status |
|---|---|---|---|---|
| 0 | regex e gitleaks | 10 | 376 | PASS |

Sem erros de scanner. O comando de pré-scan está nas evidências. O delta não muda permissões,
destinos, I/O ou o estado persistido.

### Qualidade, cobertura e sincronização

| Área | Evidência |
|---|---|
| Ordem e integridade | As primeiras posições permanecem estáveis depois do teto de mensagens. Uma chamada sem posição não vira prova e o reuso do ID de chamada continua invalidando a posição. |
| Tipos e erros | Só um ID textual válido entra no novo ramo de admissão. Nos controles negativos a atribuição fechou sem erro, com o offset no fim e os créditos legados preservados. |
| Desempenho | Uma passagem pelo prefixo. Após 64 mensagens, não há inserções novas no índice de mensagens. Os tetos separados de IDs de chamada e bytes continuam ativos. |
| Testes | `WITH_TESTS` em 1 de 1 módulos. O novo teste de Stop cobre seis cenários em dois cortes. A sonda independente também cobre chamadas feitas depois do limite com posições provadas antes por texto. |
| Documentação | README, guia e CHANGELOG concordam com a regra. O resumo de EXEC identifica a carga externa antiga como alvo da retro, mas a saída nomeia a monitorada. |

### Código morto e limpeza

Bucket A em linha. As buscas por `message_positions`, `call_positions`, `position_bytes` e
`_bound_positions` nos arquivos Python do delta mostram os consumidores do índice e dos limites.
O unittest executou a regressão nova nominalmente. Nenhum órfão. Bucket B fora do escopo.

### Overall Grade

| Criterion | Grade | Rationale |
|-----------|-------|-----------|
| Code Quality (Zen) | A | O limite de admissão agora preserva posições já registradas sem mudar o descarte por excesso de chamadas ou bytes. |
| Type Safety | A | Só IDs textuais válidos e ainda não registrados recebem posição. ID sem posição ou reaproveitado não vira prova de aposentadoria. |
| Error Handling | A | Nos dois cortes, uma externa posterior ou sem ordem demonstrada fechou a atribuição sem erro nem perda de crédito legado. |
| Security | A | Regex e gitleaks passaram sem achados ou erros. O delta não altera acesso, destinos de dados ou permissões. |
| Performance | A | Ainda há uma passagem pelo prefixo, com até 64 posições de mensagem e os tetos de chamadas e bytes mantidos. Não há campos persistidos novos. |
| Test Coverage | A | A regressão durável exercita seis variantes em dois cortes. Passaram a sonda com a 0.4.0, a jornada de QA, os 28 Checks e a suíte. |
| Documentation | B | O resumo de EXEC confunde o metadado externo antigo com a skill que recebe a retro. Guia, CHANGELOG e Check executável distinguem os dois. |
| **Overall** | **B** | R26 corrigiu os dois silêncios comprovados, sem novo defeito funcional reproduzido. Resta um desvio de prosa registrado no backlog. |

## Achados da rodada

| # | Severidade | Achado | Onde |
|---|---|---|---|
| 1 | LOW | O TL;DR diz que os dois cortes pedem retro para a externa antiga. O metadado externo é ignorado e o comando pede retro para `codereview`, a monitorada. | `docs/handoffs/20261125-retrofit-watch-atribuicao/20-handoff-exec.md:18` |

No Check de R26, acima do teto, a sonda devolveu `codereview:1,codereview:1`. Ela
exige o comando completo para `codereview` no `additionalContext`. O sufixo `1`
confirma a aposentadoria do ID externo e não identifica o alvo da retro. É um erro no
resumo, sem alteração no comportamento ou no Check.

## Incrementos de conserto (R<n>)

Nenhum. O único achado novo é de prosa e foi para o backlog. O checkpoint segue com 28 linhas
`done` e nenhuma `pending`.

## O que virou incremento

- Nenhum achado virou incremento nesta rodada.
- R26 da r38 foi fechado em `0bd4efa`. Repeti a sonda que gravou o estado com a 0.4.0.
  Nos dois cortes acima do teto, o alvo voltou a ser `codereview`. A externa posterior
  continuou em silêncio. F1 e a regressão nominal do Check passaram.
- O achado de grafia da r38 está marcado `RESOLVED by 0bd4efa` no backlog. O diff da
  expectativa histórica em r37 altera só as grafias divergentes. O Check canônico de R25
  continua com o stdout esperado.

## O que foi refutado

- **Uma chamada registrada só depois do teto invalida a ordem.** Com a ordem fixada antes
  do teto por dois blocos de texto, as duas chamadas puderam ocorrer depois do teto.
  A sonda adicional preservou a retro apenas quando o texto da externa era primeiro.
  Inverter o texto ou omitir o marcador da externa manteve o silêncio.
- **A r38 apresenta duas grafias idênticas.** A linha 71 contém literalmente
  `codoreview` e `codereview`. O diff histórico de r37 mostra a primeira sendo
  substituída pela segunda. Não há divergência nova para registrar.
- **A âncora de R24 indica que a omissão ocorreu no checkpoint.** O item resolvido
  aponta para a linha canônica que comprova R24 e conserva a fonte histórica em r37.
  O inventário de EXEC remete à tabela canônica. O Check de R24 passou. Não há nova
  omissão nem perda da fonte histórica.

## Achados fora de escopo

- Achado 1, “Resumo de EXEC confunde o alvo da retro na retomada legada”, registrado na
  seção aberta de `TODO.md`. Sem alteração de código.

## Pendências / Decisions for a Human

Nenhuma decisão nova. Code Quality (Zen), Error Handling e Test Coverage subiram de B
para A, com `0bd4efa` e os sensores reproduzidos. Os dois critérios de prosa permanecem
em B, dentro do piso. O `verified_head` de `50-pr.md` é histórico e não certifica
o candidato desta rodada. Nenhuma ação foi tomada no PR.

## Evidências reproduzíveis

Todas as medidas abaixo usaram `7a9d42cca8c5d525c13034b8528b151e25c848f7` como candidato, com árvore limpa antes da revisão.

- `env -u GIT_DIR -u GIT_WORK_TREE PYTHONDONTWRITEBYTECODE=1 bash -c 'source .sdd/config.sh && eval "$TEST_CMD"'`
  retornou rc 0. Adaptadores e catálogo válidos. Loja com 154 testes em 8,982 s, três
  pulados. Hook com 144 em 63,050 s. Versão 0.4.1 validada. As três provas nativas
  são os casos pulados pelo comando configurado.
- Executei cada célula `done` em `checkpoint.md` com
  `env -u GIT_DIR -u GIT_WORK_TREE PYTHONDONTWRITEBYTECODE=1 bash -c "$check"`,
  com `check` igual ao comando completo da célula. As 28 retornaram rc 0 e stdout
  canônico após normalizar espaços. `git merge-base --is-ancestor "$hash" HEAD`
  passou para os 28 hashes. I1 retornou `1 0 1 0 0 1`. F1 retornou
  `linked=silêncio missing=silêncio empty=silêncio` e o vetor de I1.
- `env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -m unittest -q test_retrofit_watch.StopTest.test_legacy_replay_keeps_older_external_with_ignored_owner test_retrofit_watch.StopTest.test_legacy_replay_orders_messages_from_first_assistant_block test_retrofit_watch.StopTest.test_legacy_replay_keeps_proven_order_after_text_limit test_auto_docs.ReleaseTest`
  retornou rc 0 e sete testes, incluindo os quatro de release.
- Sob `pipefail`, `git -P diff a7903595adc9ed755a731a815d4e1221ee0a7021...HEAD --unified=0 -- . ':(exclude)docs/handoffs/20261125-retrofit-watch-atribuicao/checkpoint-notas.md' | bash /home/joruge/.agents/skills/codereview/scripts/scan_secrets.sh`
  retornou zero achados, zero erros e dez arquivos escaneados.

### Sonda adicional de fronteira

A sonda usa a 0.4.0 de `7e623fe` para gravar o estado e compara a base do delta e o
candidato. Primeiro entram os textos que identificam as mensagens. A janela recebe
mais 64 textos distintos e só então entram as chamadas Skill, na mesma ordem física
nos três casos. Cada par mede a migração com o metadado externo já presente ou
acrescentado no Stop seguinte. A sonda verifica o alvo, o offset, os créditos e a
ausência de erros com `checked_stop`.

| Caso | Base do delta | Candidato |
|---|---|---|
| Texto da externa primeiro | silêncio, silêncio | codereview, codereview |
| Texto do dono primeiro | silêncio, silêncio | silêncio, silêncio |
| Externa sem posição admitida | silêncio, silêncio | silêncio, silêncio |

Os dois passos do comparativo retornaram rc 0. Para repetir no SHA candidato:

~~~bash
env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B - <<'PY'
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from test_retrofit_watch import SCRIPT, StopTest, assistant_text, identified_load, rw, tool

base = "a7903595adc9ed755a731a815d4e1221ee0a7021"
hook = "plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py"

def measure(case, cut, legacy, script):
    t = StopTest()
    t.setUp()
    try:
        w = t.w
        def mark(msg):
            row, = assistant_text("Bloco anterior à chamada.")
            row["message"]["id"] = msg
            t.write([row], compact=True)
        owner = identified_load("coderabbit-pr", w.mkt_skill, "owner", "toolu_owner")
        external = identified_load("brainstorming", w.other_skill, "external", "toolu_external")
        if case != "externa_sem_posição":
            for message in (("external", "owner") if case == "externa_primeira" else ("owner", "external")):
                mark(message)
        else:
            mark("owner")
        for index in range(rw.MAX_SKILL_MESSAGES):
            mark(f"fill_{index}")
        t.write(owner[:2], external[:2], compact=True)
        out, before = t.checked_stop(script=legacy)
        assert out is None and before["current"] is None
        for index in range(2):
            t.write(identified_load("codereview:coderabbit-pr", w.mkt_skill,
                                    f"skip_{index}", f"toolu_skip_{index}"), compact=True)
        out, skip = t.checked_stop(script=legacy, active=True)
        assert out is None and skip["current"] is None and skip["offset"] > before["offset"]
        t.write(owner[2:], tool(), compact=True)
        out, saved = t.checked_stop(script=legacy)
        assert out is None and "skill_calls" not in saved
        key = "full:codereview"
        credits = saved["skills"][key]
        assert saved["current"] == key and (credits["work"], credits["friction"], credits["reviews"]) == (1, 0, 0)
        if cut:
            out, migrated = t.checked_stop(script=script)
            assert out is None and migrated["current"] == key
            assert migrated["offset"] == saved["offset"] and migrated["skills"][key] == credits
        t.write(external[2:], tool(error=True), compact=True)
        out, after = t.checked_stop(script=script)
        retired = "toolu_external" in after["retired_skill_calls"]
        if out is None:
            assert after["attribution_closed"] and after["current"] is None and after["skills"][key] == credits
            assert not retired
            return "silêncio"
        assert "`/retrofit-skill:retrofit-skill codereview`" in t.context_of(out)
        assert retired and after["current"] == key and after["skills"][key]["reviews"] == 1
        return "codereview"
    finally:
        t.tearDown()

cases = ("externa_primeira", "dono_primeiro", "externa_sem_posição")
with TemporaryDirectory() as tmp:
    old, legacy = (Path(tmp) / name for name in ("base.py", "v040.py"))
    for path, sha in ((old, base), (legacy, "7e623fe")):
        path.write_bytes(subprocess.check_output(["git", "show", f"{sha}:{hook}"]))
    for version, script in (("base", old), ("HEAD", SCRIPT)):
        results = {k: tuple(measure(k, cut, legacy, script) for cut in (False, True)) for k in cases}
        print(version, " ".join(f"{k}={','.join(v)}" for k, v in results.items()), flush=True)
        expected = {k: (("codereview",)*2 if version == "HEAD" and k == "externa_primeira" else ("silêncio",)*2)
                    for k in cases}
        assert results == expected, results
PY
~~~

### Recommended Actions

**Must Fix (CRITICAL)**

_Nenhuma._

**Should Fix (HIGH)**

_Nenhuma._

**Consider Fixing (MEDIUM/LOW)**

- Corrigir na triagem de prosa o alvo descrito no TL;DR de EXEC, sem reabrir R26.

### Cost footprint

_Skill Codex 2.27.38 do caminho solicitado, distinta do cache Claude 2.30.2. Três agentes
gpt-6.1-terra para oito documentos, com 3, 9 e 10 chamadas declaradas. Módulo, teste direto,
Bucket A e reprodução em linha. Custo monetário não medido._
