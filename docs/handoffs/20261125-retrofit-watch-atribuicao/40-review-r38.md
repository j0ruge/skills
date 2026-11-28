---
missao: 20261125-retrofit-watch-atribuicao
fase: REVIEW
rodada: 38
status: done
sessao: 01a22099-717c-7612-8902-305c9629fdbb
data: 2026-11-28 02:27
gate: "Em a7903595adc9ed755a731a815d4e1221ee0a7021, árvore limpa antes da revisão. TEST_CMD isolado rc 0 (154 testes da loja, 3 pulados, 143 do hook, versão 0.4.1), 27 Checks verdes e quatro testes de release verdes. A sonda R26 retornou rc 1 em HEAD e rc 0 na base, com dois pedidos de retro suprimidos em HEAD. R26 pending. Gate REVIEW não aprovado. Platô em Code Quality (Zen), Error Handling e Test Coverage (B)."
reviewed_head: a7903595adc9ed755a731a815d4e1221ee0a7021
---

# Review — rodada r38 — Atribuição da retrofit-watch por mensagem

## TL;DR

R25 corrigiu os quatro vereditos invertidos da r37. A suíte e os 27 Checks passaram.
Uma nova regressão aparece na retomada quando texto sem carga ultrapassa o teto de 64 mensagens. Ela virou R26.
Uma divergência de prosa foi para o backlog. Nota geral B, sem alteração de código.

## Nota da rodada

Fluxo Codex de `/codereview:codereview base=2c4c45d8cc5cecd5b32265b024d5a09f1aec3964`
até `a7903595adc9ed755a731a815d4e1221ee0a7021`, na branch `fix/retrofit-watch-atribuicao-mesma-mensagem`.
Nove arquivos em escopo, com +427/−25, entre um módulo Python, seu teste direto e sete documentos.
O diário foi excluído da leitura, do diff de conteúdo e do pré-scan. A QA em `08f09a1` cobre
vínculo válido, ausente e vazio em dois Stops. A rodada repetiu essa jornada e examinou o limite
do registro de posições introduzido para blocos de texto.

### Secrets Detection

| Achados | Scanners | Arquivos | Linhas adicionadas | Status |
|---|---|---|---|---|
| 0 | regex e gitleaks | 9 | 427 | PASS |

Sem erros dos scanners. O delta não altera permissões, destinos de dados ou credenciais.

### Qualidade, cobertura e sincronização

| Área | Evidência |
|---|---|
| Integridade e ordem | A primeira linha de texto agora fixa a posição correta, mas mensagens sem chamada descartam posições de chamadas já observadas ao atingir o teto. |
| Tipos e erros | A entrada valida o objeto e o ID antes de usar o dicionário. No caso de R26, o Stop termina normalmente, avança o offset e não grava erro, mas fica indevidamente em silêncio. |
| Desempenho | Continua uma passagem pelo prefixo, sem campo persistente novo. Os tetos de mensagens, chamadas e bytes limitam as tabelas temporárias. |
| Testes | `WITH_TESTS` em 1 de 1 módulos. A regressão de R25 tem 11 cenários parametrizados em dois cortes. O ramo `message_limit` exige não aposentar e termina antes de exercitar a emissão de retro. |
| Documentação | README, guia e CHANGELOG concordam sobre a primeira ocorrência da mensagem. O inventário de EXEC aponta para a tabela canônica. A cópia histórica da célula em r37 tem grafias divergentes. |

### Código morto e limpeza

Bucket A em linha. `rg -n 'message_positions|call_positions|position_bytes|_bound_positions|test_legacy_replay_orders_messages_from_first_assistant_block'`
nos dois arquivos Python do delta mostrou que as tabelas e o método auxiliar têm consumidores, e o
unittest descobriu a regressão de R25. Sem símbolo órfão. Bucket B fora do escopo.

### Overall Grade

| Criterion | Grade | Rationale |
|-----------|-------|-----------|
| Code Quality (Zen) | B | O mesmo teto descarta o índice de novas mensagens e as posições já conhecidas de chamadas válidas. Só o segundo descarte inverteu os dois vereditos novos. |
| Type Safety | A | A entrada filtra objetos e IDs inválidos. Não usa posições ausentes ou de chamadas repetidas como prova de ordem. |
| Error Handling | B | O fallback por teto mantém o arquivo íntegro, mas em uma retomada válida suprimiu a retro apesar de a ordem estar provada antes de o teto ser atingido. |
| Security | A | Sem segredos em regex e gitleaks. A alteração não abre novas entradas, saídas ou permissões. |
| Performance | A | O replay continua em uma passagem e não aumenta o estado persistido. As tabelas são limitadas em mensagens, chamadas e bytes. |
| Test Coverage | B | R25 cobre o erro original e o acionamento do teto, mas o teste passa exigindo descartar uma prova já conhecida e não mede a saída do Stop nesse ramo. |
| Documentation | B | A célula canônica funciona, mas copiar a expectativa histórica de r37 produz uma comparação falsa por grafia. |
| **Overall** | **B** | R25 foi verificado no commit de EXEC. Uma nova regressão nos dois cortes impede aprovar a retomada no teto. |

## Achados da rodada

| # | Severidade | Achado | Onde |
|---|---|---|---|
| 1 | MEDIUM | Texto de mensagens distintas invalida as posições já registradas de duas chamadas Skill anteriores ao teto. Metadado externo comprovadamente antigo encerra a atribuição e suprime a retro. | `plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py:870–899` |
| 2 | LOW | A célula histórica de R25 em r37 mistura `codoreview` com `codereview`. O Check canônico já está certo. | `docs/handoffs/20261125-retrofit-watch-atribuicao/40-review-r37.md:91` |

No achado 1, as duas posições vêm de chamadas com IDs válidos e distintos, e o texto não
reutiliza nenhum deles. O replay vê quatro mensagens com chamadas Skill. Com 60 IDs só de
texto, ainda tem as posições. Ao chegar a 61, `_bound_positions` põe as duas tabelas em
`None`. Quando chega o metadado do dono, não consegue mais demonstrar que a externa é
anterior. Na base, a mesma entrada preserva a retro. O fallback documentado continua
necessário para identidade ou ordem não comprovadas. Aqui, a prova já existia antes do
teto e a entrada que o excede não pode alterá-la.

O achado 2 foi rebaixado de MEDIUM para LOW. O comando da cópia histórica funciona e a
sonda retorna exclusivamente `codereview` nos casos positivos. Só o stdout **esperado**
da linha histórica diverge do medido. O checkpoint e o boot da fase apontam para a
versão executável que passou, então não há incremento de código.

## Incrementos de conserto (R<n>)

| R<n> | Achado | Check escrito no checkpoint |
|---|---|---|
| R26 | Achado 1 | Sonda com a 0.4.0 real e `--expect`, jornada F1 e regressão durável nomeada. Exige preservar a antiga e manter silêncio com externa posterior, sem retirar os limites. |

## O que virou incremento

~~~text
| R26 | Preservar a ordem já comprovada quando texto sem chamada excede o teto do replay legado (r38, achado 1) | `probe=$(sed -n '/^~~~python$/,/^~~~$/{ /^~~~/!p; }' docs/handoffs/20261125-retrofit-watch-atribuicao/40-review-r38.md) && test -n "$probe" && env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -c "$probe" --expect && env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B e2e/test_retrofit_watch_stop.py && if o=$(env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -m unittest -q test_retrofit_watch.StopTest.test_legacy_replay_keeps_proven_order_after_text_limit 2>&1); then [[ "$o" == *"Ran 1 test"* && "$o" == *"OK"* ]] && printf 'regressao=1\n'; else printf '%s\n' "$o" >&2; exit 1; fi` → `sem_texto=codereview:1,codereview:1 no_teto=codereview:1,codereview:1 acima_do_teto=codereview:1,codereview:1 texto_repetido=codereview:1,codereview:1 externa_posterior=silêncio:0,silêncio:0 linked=silêncio missing=silêncio empty=silêncio regressao=1` | pending | — |
~~~

- O achado 1 virou R26. O Check exige manter a ordem já confirmada quando o teto é atingido por texto.
  A regressão durável precisa cobrir o limite sem tratar mensagem desconhecida ou ID reutilizado como prova.
- R25 foi fechado em `149086f`. Seu Check passou com os cinco pares esperados, incluindo as quatro
  retomadas antes invertidas, a regressão durável e F1. R23 e R24 também passaram.
- O achado de prosa da r37 foi encerrado em `149086f`. O inventário do handoff aponta agora
  para a tabela canônica sem repetir o intervalo, e o backlog já registra o encerramento.

## O que foi refutado

- R25 não deixou abertos os quatro vereditos da r37. Sem texto que ultrapasse o teto, os controles
  de R25 distinguem corretamente a primeira ocorrência do dono e da externa.
- Não é o volume de linhas que reproduz R26. Com 61 blocos usando um único ID adicional, sai
  `codereview:1,codereview:1`. Só 61 IDs distintos acrescentados às quatro mensagens com carga
  mudaram o veredito. Inverter as chamadas continuou produzindo silêncio, também acima do teto.
- O teto não está sem sensor. Retirar só a comparação de `MAX_SKILL_MESSAGES` de
  `recover_legacy_correlation` em memória produziu duas falhas de asserção no subcaso
  `message_limit` da regressão de R25. O sensor exige o descarte atual de uma posição que
  a sonda nova prova ser útil. Remover o teto inteiro não é a correção indicada.
- A grafia histórica não torna o Check de R25 vermelho. A expectativa canônica da célula
  em `checkpoint.md` coincide com seu stdout completo.

## Achados fora de escopo

- Achado 2 registrado na seção aberta do backlog nesta rodada. É só de prosa, sem R<n>.

## Pendências / Decisions for a Human

A r38 tem as mesmas notas da r37. Code Quality (Zen), Error Handling e Test Coverage
permanecem em B, embora o caso anterior tenha sido corrigido. Este é um platô. O gate
segue reprovado e a revisão termina aqui para o responsável decidir se prossegue com R26.
O `verified_head` de `50-pr.md` é anterior ao candidato. Nenhuma ação foi tomada no PR.

## Evidências reproduzíveis

- Em `a7903595adc9ed755a731a815d4e1221ee0a7021`, a árvore estava limpa. O comando
  `env -u GIT_DIR -u GIT_WORK_TREE PYTHONDONTWRITEBYTECODE=1 bash -c 'source .sdd/config.sh && eval "$TEST_CMD"'`
  retornou rc 0. Loja com 154 testes em 9,468 s, três pulados. Hook com 143 em 66,330 s.
  Adaptadores, catálogo e versão 0.4.1 passaram. As três provas nativas não foram repetidas.
- No mesmo HEAD, executei as 27 células `done` de `checkpoint.md` uma a uma com
  `env -u GIT_DIR -u GIT_WORK_TREE PYTHONDONTWRITEBYTECODE=1 bash -c "$check"`. Todas retornaram
  rc 0 e stdout completo esperado, normalizados apenas espaços. `git merge-base --is-ancestor "$hash" HEAD`
  confirmou os 27 hashes. I1 deu `1 0 1 0 0 1`. F1 deu `linked=silêncio missing=silêncio empty=silêncio` e o vetor de I1.
- No mesmo HEAD, `env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -m unittest -q test_auto_docs.ReleaseTest`
  retornou rc 0 com quatro testes.
- Sob `pipefail`, `git -P diff 2c4c45d8cc5cecd5b32265b024d5a09f1aec3964...HEAD --unified=0 -- . ':(exclude)docs/handoffs/20261125-retrofit-watch-atribuicao/checkpoint-notas.md' | bash /home/joruge/.agents/skills/codereview/scripts/scan_secrets.sh`
  retornou zero achados e zero erros em nove arquivos.

### Sonda de R26

A 0.4.0 real grava a atribuição legada em disco. As cinco variantes medem o Stop da
migração e o Stop seguinte, nessa ordem. O sufixo indica se o ID externo foi aposentado.
`checked_stop` mede o offset e a ausência de `errors.log` em cada chamada.

| Variante | Base `2c4c45d`, em ambos os cortes | HEAD, em ambos os cortes | Esperado |
|---|---|---|---|
| Externa anterior, sem texto | `codereview:1` | `codereview:1` | `codereview:1` |
| Externa anterior, 60 IDs de texto distintos | `codereview:1` | `codereview:1` | `codereview:1` |
| Externa anterior, 61 IDs de texto distintos | `codereview:1` | `silêncio:0` | `codereview:1` |
| Externa anterior, 61 blocos com o mesmo ID | `codereview:1` | `codereview:1` | `codereview:1` |
| Externa posterior, 61 IDs de texto distintos | `silêncio:0` | `silêncio:0` | `silêncio:0` |

Para reproduzir, execute os três primeiros termos do Check de R26. Em HEAD, o comando
com `--expect` retornou rc 1 na asserção final. Com o módulo extraído da base via
`git show "2c4c45d8cc5cecd5b32265b024d5a09f1aec3964:$hook" > "$arquivo"` e
`--script "$arquivo" --expect`, retornou rc 0. Use como `hook` o caminho no bloco abaixo.
Os transcripts são sintéticos. Nenhuma execução reiniciou ou acessou uma sessão do usuário.

~~~python
import argparse
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from test_retrofit_watch import SCRIPT, StopTest, assistant_text, identified_load, rw, tool

parser = argparse.ArgumentParser()
parser.add_argument("--script", type=Path, default=SCRIPT)
parser.add_argument("--expect", action="store_true")
args = parser.parse_args()


def measure(text_count, distinct, older, split, legacy):
    test = StopTest()
    test.setUp()
    try:
        w = test.w
        owner = identified_load("coderabbit-pr", w.mkt_skill, "msg_owner", "toolu_owner")
        external = identified_load("brainstorming", w.other_skill, "msg_external", "toolu_external")
        order = (external, owner) if older else (owner, external)
        test.write([load[0] for load in order], [load[1] for load in order], compact=True)
        out, initial = test.checked_stop(script=legacy)
        assert out is None and initial["current"] is None and initial["classified"] == {}

        for index in range(2):
            test.write(identified_load("codereview:coderabbit-pr", w.mkt_skill,
                                       f"msg_skip_{index}", f"toolu_skip_{index}"), compact=True)
        out, skipped = test.checked_stop(script=legacy, active=True)
        assert out is None and skipped["current"] is None and skipped["classified"] == {}
        assert skipped["offset"] > initial["offset"]

        for index in range(text_count):
            row, = assistant_text("Continuando.")
            row["message"]["id"] = f"msg_text_{index if distinct else 0}"
            test.write([row], compact=True)
        test.write(owner[2:], tool(), compact=True)
        out, saved = test.checked_stop(script=legacy)
        key = "full:codereview"
        credits = saved["skills"][key]
        assert out is None and saved["current"] == key and "skill_calls" not in saved
        assert set(saved["classified"]) == {str(w.mkt_skill)}
        assert (credits["work"], credits["friction"], credits["reviews"]) == (1, 0, 0)

        if split:
            out, migrated = test.checked_stop(script=args.script)
            assert out is None and migrated["current"] == key
            assert migrated["skills"][key] == credits and migrated["offset"] == saved["offset"]
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
space = rw.MAX_SKILL_MESSAGES - 4
cases = {
    "sem_texto": (0, True, True),
    "no_teto": (space, True, True),
    "acima_do_teto": (space + 1, True, True),
    "texto_repetido": (space + 1, False, True),
    "externa_posterior": (space + 1, True, False),
}
with TemporaryDirectory() as tmp:
    legacy = Path(tmp) / "legacy.py"
    legacy.write_bytes(subprocess.check_output(["git", "show", f"7e623fe:{hook}"]))
    measured = {name: ",".join(measure(*case, split, legacy) for split in (False, True))
                for name, case in cases.items()}
print(" ".join(f"{name}={result}" for name, result in measured.items()))
if args.expect:
    expected = {name: ",".join([result] * 2) for name, result in
                zip(cases, ("codereview:1",) * 4 + ("silêncio:0",))}
    assert measured == expected, measured
~~~

### Recommended Actions

**Must Fix (CRITICAL)**

_Nenhuma._

**Should Fix (HIGH)**

_Nenhuma._

**Consider Fixing (MEDIUM/LOW)**

- Se o responsável decidir prosseguir, execute R26 em TDD e mantenha R23, R24, R25 e F1 verdes.
- Na triagem de prosa, alinhe ou remeta à expectativa canônica do Check de R25.

### Cost footprint

_Skill 2.27.38 do caminho solicitado, distinta do cache Claude 2.30.2. Três agentes gpt-6.1-terra para sete documentos, com 3–12 chamadas e sete leituras integrais declaradas. Módulo, teste direto, Bucket A e sondas em linha. Custo monetário não medido._
