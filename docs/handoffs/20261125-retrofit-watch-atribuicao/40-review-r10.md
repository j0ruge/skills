---
missao: 20261125-retrofit-watch-atribuicao
fase: REVIEW
rodada: 10
status: done
sessao: 01a21eb2-3922-76a2-a7b0-872ddfd5da1a
data: 2026-11-27 17:38
gate: "Em 8d2910945c9041d670e9e13a69df8cf7d7010d9f, árvore limpa. env -u GIT_DIR -u GIT_WORK_TREE PYTHONDONTWRITEBYTECODE=1 bash -c 'source .sdd/config.sh && eval \"$TEST_CMD\"' → rc 0, 154 testes da loja (3 pulados), 107 do hook, adaptadores, catálogo e versão 0.4.1 válidos. Comparação de rc e stdout dos Checks em checkpoint.md → 9/11, com R1–R9 verdes. I1 e F1 deram rc 0, mas 1 0 1 0 1 1 em vez de 1 0 1 0 0 1. A sonda R10 desta rodada deu rc 1 com --expect. Regressão de Performance, A para B, com Code Quality (Zen), Error Handling e Test Coverage ainda em B."
reviewed_head: 8d2910945c9041d670e9e13a69df8cf7d7010d9f
---

# Review — rodada r10 — Atribuição da retrofit-watch por mensagem

Escopo completo de `7e623fe62fa09473a8d2ebfd49b75099fe2c2bcc...8d2910945c9041d670e9e13a69df8cf7d7010d9f`
sobre `origin/main`, após a integração em `a37aad4`. O diff tem 26 caminhos, com 1 módulo Python,
2 testes, 2 manifestos e 21 documentos. As notas de execução ficaram fora da leitura e do pré-scan
por instrução da fase. QA já cobriu a reabertura pelo metadado atrasado em F1.

## TL;DR

A suíte e R1–R9 passaram. I1 e F1 imprimiram 1 no quinto caso, onde o plano exige 0.
O hook perdeu um slash que atravessou a migração, aceitou reuso de ID falho sem origem e
não concluiu a migração do prefixo grande sob o teto da sonda. Os quatro achados sanáveis
foram para R10. Nota B, com regressão em Performance. Nenhum código alterado.

## Nota da rodada

### Secrets Detection

**Status: PASS.** Zero ocorrências e zero erros em `regex` e `gitleaks`. Os pré-scans das
versões 2.27.38 e 2.30.2, sobre o mesmo diff com a exclusão indicada acima, contaram
25 arquivos e 4.562 linhas adicionadas. A mudança não introduz comando de rede nem destino de
escrita. O replay usa o mesmo classificador e a mesma trava por sessão do Stop.

### Cobertura, sincronização e varredura

- **WITH_TESTS, 1/1 módulo.** `test_retrofit_watch.py` executa o hook filho com transcript
  e estado reais da fixture. `e2e/test_retrofit_watch_stop.py` mediu as três variantes de
  BUG-01 sem reabertura. O sensor de leitura em `test_retrofit_watch.py:665` exige hoje o
  `read(offset)` integral. Deve passar a provar uma só travessia, sem exigir uma alocação.
- **Tipos e dados.** A fronteira para IDs converte ausentes e inválidos para `None` e
  distingue ausência de uma chamada ambígua. O achado de ID é perda de histórico, não
  confusão de representação. As sondas verificaram JSON legado e atual, offset, alvo e contadores.
  Não há verificador estático Python configurado no diff.
- **Sincronização.** Manifesto, catálogo Claude, README, versão do SKILL e CHANGELOG concordam
  em 0.4.1. A afirmação do CHANGELOG sobre IDs falhos não vale para o corte do achado 2.
  Os checks de catálogo Codex e de versões passaram. Não houve teste em Claude Code ou Windows.
- **Varredura de símbolos, Bucket A.** Zero órfãos novos confirmados. Os auxiliares de
  correlação são chamados por `Scanner`, o leitor de compatibilidade por `cmd_stop`, e os
  pontos de entrada são registrados em `hooks.json`. Os testes têm descoberta por nome e F1
  tem ponto de entrada próprio. Bucket B preexistente fora desta rodada.

### Overall Grade

| Criterion | Grade | Rationale |
|-----------|-------|-----------|
| Code Quality (Zen) | B | O replay recupera a ordem, mas deixa de reaproveitar o slash explícito ainda pendente e perde a marca de falha sem origem. |
| Type Safety | A | IDs ausentes, válidos e ambíguos e estados da 0.4.0 e da 0.4.1 foram exercitados sem erro de tipo. |
| Error Handling | B | O Stop não credita o slash migrado, credita trabalho depois de um reuso ambíguo e retorna 0 sem concluir a migração quando o prefixo excede a memória da sonda. |
| Security | A | Duas varreduras sem segredos nem erros. A mudança não abre rede, novos comandos nem novos destinos persistentes. |
| Performance | B | Sem bytes novos, o pico passou de 16.096 para 148.456 KiB com um prefixo de cerca de 64 MiB. O replay falhou com um prefixo de cerca de 160 MiB sob teto de 256 MiB. |
| Test Coverage | B | Os 107 testes do hook passam, mas não guardam os cortes dos achados 1–3. As duas células que verificam o vetor da missão divergem no quinto caso. |
| Documentation | B | A versão está sincronizada, mas a garantia publicada sobre IDs falhos não se cumpre na falta de origem. O achado de âncoras é só de forma. |
| **Overall** | **B** | R9 fechou seus cortes, mas a revisão completa encontrou outras falhas de retomada, correlação e medição. |

## Achados da rodada

| # | Severidade | Achado | Onde |
|---|---|---|---|
| 1 | MEDIUM | Após uma externa, o slash local digitado no prefixo perde a atribuição quando só seu metadado chega no Stop que migra. Sem troca de versão, ambos os hooks pedem retro de `graphify`. | `retrofit_watch.py:812` e `:696` |
| 2 | MEDIUM | O erro descarta a pendência de ID sem mensagem e não deixa marca. Reusar esse ID numa externa na mensagem ativa passa como vínculo novo e credita retro indevida, tanto em leitura contínua quanto na retomada. ID falho com origem conhecida e ID novo são controles independentes. | `retrofit_watch.py:704` e `:708`, `CHANGELOG.md:17` |
| 3 | MEDIUM | A primeira retomada carrega o prefixo todo e o duplica no `split`, sob a trava. Sem delta, sob teto de 256 MiB, o hook de saída 0 registra `MemoryError` e deixa o estado legado por migrar. | `retrofit_watch.py:780`, `:785`, `:796` e `:1013` |
| 4 | MEDIUM | I1 e F1 ficam vermelhos pela saída, apesar de rc 0. O quinto caso fabrica o estado sem chaves novas, mas conserva IDs recuperáveis no transcript. Não é um teste válido do fallback sem evidência depois de `cf17ddd`. | `checkpoint.md:10`, `:11` e `01-plano.md:87` |
| 5 | LOW | As referências de três itens do backlog abrem linhas vizinhas, não a definição ou a expressão citada. Todas ainda passam a tolerância do linter. | `TODO.md:91`, `:208` e `:214` |

O achado 2 confirma a divergência de comportamento em `plugins/retrofit-watch/CHANGELOG.md`.
Corrigir o comportamento cobre a garantia publicada, sem criar incremento só de redação.

## Incrementos de conserto (R<n>)

| R<n> | Achado | Check escrito no checkpoint |
|---|---|---|
| R10 | Achados 1–4, em lote. | Sonda de subprocessos com a 0.4.0 real, controles positivo e negativo, teste de memória limitada e comparação integral dos Checks I1/F1, seguida por três regressões duráveis descobertas por nome. |

Para o achado 1, manter os controles de comando divergente e de encerramento anterior. Para o 2,
não ampliar a janela nem retirar os tetos para preservar a ambiguidade. Para o 3, manter a leitura
única e o offset, inclusive quando falta prefixo. Para o 4, conservar o vetor aprovado e exercer
de fato o caso sem correlação. O controle correlacionado da sonda valida que a mudança do sensor
não retira a recuperação legítima.

## O que virou incremento

- | R10 | Preservar o slash e a ambiguidade de ID, limitar a memória da retomada e restaurar o sensor sem vínculo (r10, achados 1–4) | `PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -c "$(sed -n '/^~~~python$/,/^~~~$/{ /^~~~/!p; }' docs/handoffs/20261125-retrofit-watch-atribuicao/40-review-r10.md)" --expect && if o=$(env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -m unittest -q test_retrofit_watch.StopTest.test_legacy_migration_preserves_split_typed_slash test_retrofit_watch.StopTest.test_failed_unowned_call_id_cannot_prove_same_message test_retrofit_watch.StopTest.test_legacy_replay_reads_prefix_with_bounded_memory 2>&1); then [[ "$o" == *"Ran 3 tests"* && "$o" == *"OK" ]] && printf 'regressoes=3\n'; else printf '%s\n' "$o" >&2; exit 1; fi` → `slash_040=graphify slash_041=graphify slash_migrado=graphify slash_alheio=silêncio sem_vinculo=silêncio com_vinculo=codereview falha_sem_origem=silêncio,silêncio falha_com_origem=silêncio,silêncio falha_id_novo=codereview,codereview prefixo_040=ok prefixo_041=ok checks_i1_f1=2 regressoes=3` | pending | — |

- R9 fechado por `8fa5c7d` e `cf17ddd`. O Check em `8d29109` retornou silêncio para
  pendência anterior à externa e `codereview` para a posterior, mesmo com estados legados
  idênticos. Sem externa o controle pediu retro, e sem metadado externo o caso anterior ficou
  em silêncio. O teste de origem ativa rodou e passou. R1–R8 também igualaram as saídas previstas.

## O que foi refutado

- **O quinto caso prova que o fallback sem vínculo regrediu.** A mesma sonda I1 imprimiu
  `1 0 1 0 0 1` com o módulo de `8fa5c7d` e `1 0 1 0 1 1` com o de `8d29109`.
  Removendo apenas `message.id` e `sourceToolUseID` da variante legada, em cópia temporária
  da sonda, `8d29109` voltou a `1 0 1 0 0 1`. Na troca real de binários da sonda abaixo,
  uma externa por caminho sem ID de mensagem também encerra, e a mesma externa com vínculo
  confirmado preserva a retro. A falha é do sensor, não autorização para mudar a métrica.
- **O Check R9 passa mesmo com as quatro linhas ausentes.** Só o rc do comando pode passar.
  `sed -n '/^legado_atual .* meta=/p' <<< ""` retorna 0 sem imprimir nada. Com o teste de origem
  verde, isso deixaria apenas `origem_ativa=1`, que não iguala o esperado. O leitor de
  `--red` em `tests/check-checkpoint.sh` compara o stdout completo, e nossa verificação também.
  O `gate_EXEC` não executa as células. No HEAD, nenhuma linha de R9 faltou.
- **As três âncoras são inválidas.** Os símbolos reais estão nas linhas 539, 650 e 689, a 7,
  7 e 1 linhas respectivamente das referências. A regra do backlog aceita até 10 linhas.
  Ficou só a melhoria de precisão, sem efeito na nota.

## Achados fora de escopo

- O achado 5 foi registrado em `TODO.md` na seção de revisão da atribuição. Não muda a suíte nem vira R.

## Pendências / Decisions for a Human

A nota de **Performance** caiu de A para B em relação a r9. Pela regra de movimento, não
inicio outra revisão nesta sessão. R10 registra o trabalho sanável sem dispensar a regressão.
Nenhuma mudança de política é necessária para repetir as provas.

## Evidências reproduzíveis

A suíte de `8d29109` foi executada uma vez, com árvore limpa.

```bash
env -u GIT_DIR -u GIT_WORK_TREE PYTHONDONTWRITEBYTECODE=1 bash -c 'source .sdd/config.sh && eval "$TEST_CMD"'
```

Saiu 0. Loja com 154 testes e três pulos configurados. Hook com 107 testes verdes.
Adaptadores, catálogo e versões passaram. Os avisos não bloqueantes foram de outros plugins.

Comparei o rc e o stdout completo das onze células, normalizando só o espaço em branco.
I1 e F1 deram rc 0, mas vetor `1 0 1 0 1 1`. F1 também imprimiu `linked=silêncio`,
`missing=silêncio` e `empty=silêncio`. Os nove Checks R1–R9 deram rc 0 com as saídas previstas.

A sonda nova roda da raiz em Linux. Extrai a versão 0.4.0 de `fe38d1f` do Git da missão,
isola Git e HOME nos subprocessos e não toca no estado do host. Sem `--expect`, imprime a
medição. Com `--expect`, exige igualdade de todos os controles.

```bash
PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -c "$(sed -n '/^~~~python$/,/^~~~$/{ /^~~~/!p; }' docs/handoffs/20261125-retrofit-watch-atribuicao/40-review-r10.md)" --expect
```

Resultado em `8d29109`, rc 1 com `--expect`:

```text
slash_040=graphify slash_041=graphify slash_migrado=silêncio slash_alheio=silêncio sem_vinculo=silêncio com_vinculo=codereview falha_sem_origem=codereview,codereview falha_com_origem=silêncio,silêncio falha_id_novo=codereview,codereview prefixo_040=ok prefixo_041=MemoryError checks_i1_f1=0
```

A amostra complementar de RSS usou `/usr/bin/time -f '%M %e' python3 <hook> stop`
após `baseline` da 0.4.0, sem delta, com registros de assistente de cerca de 4 KiB.
Em cerca de 16 MiB, mediu 16.140 KiB e 0,04 s no 0.4.0 contra 49.284 KiB e 1,15 s no HEAD.
Em cerca de 64 MiB, mediu 16.096 KiB e 0,03 s contra 148.456 KiB e 4,43 s.
São medidas locais, não uma estimativa de frequência em produção. A asserção do Check
usa o teto de memória controlado, não os tempos de parede.

~~~python
import json
import os
import re
import resource
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from test_retrofit_watch import SCRIPT, HookHarness, World, identified_load, skill_typed, tool

for key in ("GIT_DIR", "GIT_WORK_TREE"):
    os.environ.pop(key, None)
legacy_code = subprocess.check_output([
    "git", "show",
    "fe38d1f:plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py",
])


class Journey(HookHarness, TestCase):
    def measure(self, first, second, cut, *, matched=True, proof=True):
        self.w = w = World()
        try:
            our = identified_load("codereview:coderabbit-pr", w.mkt_skill, "m1", "u1")
            if cut == "skill":
                other = identified_load("brainstorming", w.other_skill, "m1", "u2")
                if not proof:
                    other[0]["message"].pop("id")
                prefix, delta = (our, other[:2]), (other[2:],)
            else:
                other = identified_load("superpowers:brainstorming", w.other_skill, "m2", "u2")
                direct = skill_typed("graphify" if matched else "outra-skill", w.graphify)
                prefix, delta = (our, other, direct[:1]), (direct[1:],)
            self.write(*prefix, compact=True)
            assert self.run_hook(script=first) is None
            state_path = w.data / "sessions/s1.json"
            before = json.loads(state_path.read_bytes())
            assert before["offset"] == w.transcript.stat().st_size
            self.write(*delta, tool(error=True), compact=True)
            out = self.run_hook(script=second)
            after = json.loads(state_path.read_bytes())
            assert after["offset"] == w.transcript.stat().st_size
            assert not (w.data / "errors.log").exists()
            target = "silêncio" if out is None else re.search(
                r"/retrofit-skill:retrofit-skill ([a-z-]+)", self.context_of(out)
            ).group(1)
            if cut == "slash":
                assert after["skills"]["full:codereview"] == before["skills"]["full:codereview"]
            if out is None:
                assert after["current"] is None
            else:
                active = after["skills"][after["current"]]
                assert active["arg"] == target
                assert (active["work"], active["friction"], active["reviews"]) == (0, 0, 1)
            return target
        finally:
            w.cleanup()


def failed_id(*, origin, reused, split):
    j = Journey()
    j.w = w = World()
    try:
        ours = identified_load("codereview:coderabbit-pr", w.mkt_skill, "m1", "u1")
        failed = identified_load("desconhecida", w.other_skill, "m1", "u2")
        if not origin:
            del failed[0]["message"]["id"]
        failed[1]["message"]["content"][0]["is_error"] = True
        other = identified_load("superpowers:brainstorming", w.other_skill, "m1", "u2" if reused else "u3")
        j.write(ours, failed[:2], compact=True)
        state = w.data / "sessions/s1.json"
        if split:
            assert j.run_hook(mode="plan") is None
            before = json.loads(state.read_bytes())
            assert before["offset"] == w.transcript.stat().st_size
            assert before["current"] == "full:codereview"
        j.write(other, tool(error=True), compact=True)
        out = j.run_hook()
        after = json.loads(state.read_bytes())
        assert after["offset"] == w.transcript.stat().st_size
        assert not (w.data / "errors.log").exists()
        skill = after["skills"]["full:codereview"]
        if out is None:
            assert after["current"] is None
            # Só o resultado falho anterior à externa pode contar como atrito.
            assert (skill["work"], skill["friction"], skill["reviews"]) == (0, 1, 0)
            return "silêncio"
        assert "/retrofit-skill:retrofit-skill codereview" in j.context_of(out)
        assert skill["reviews"] == 1
        return "codereview"
    finally:
        w.cleanup()


def vector_checks():
    checkpoint = Path("docs/handoffs/20261125-retrofit-watch-atribuicao/checkpoint.md")
    contract = {
        "I1": "1 0 1 0 0 1",
        "F1": "linked=silêncio missing=silêncio empty=silêncio 1 0 1 0 0 1",
    }
    result = {}
    for line in checkpoint.read_text(encoding="utf-8").splitlines():
        cells = line.split("|")
        if len(cells) != 7 or cells[1].strip() not in contract:
            continue
        label, check = cells[1].strip(), cells[3].strip()
        match = re.fullmatch(r"`(.*)` → `([^`]*)`", check)
        assert match and match[2].split() == contract[label].split(), check
        proc = subprocess.run(["bash", "-c", match[1]], text=True, capture_output=True, timeout=55)
        result[label] = proc.returncode == 0 and proc.stdout.split() == match[2].split()
        if not result[label]:
            print(f"{label}: rc={proc.returncode} stdout={proc.stdout.strip()!r}", file=sys.stderr)
    assert result.keys() == contract.keys()
    return sum(result.values())


def capped_prefix(root, legacy, target):
    p = root / "prefixo.jsonl"
    row = json.dumps({"type": "system", "message": {"content": [
        {"type": "text", "text": "x" * 4000},
    ]}}).encode() + b"\n"
    with p.open("wb") as fh:
        for _ in range(160 * 1024 * 1024 // len(row)):
            fh.write(row)
    with TemporaryDirectory(dir=root) as tmp:
        env = dict(os.environ, CLAUDE_PLUGIN_DATA=tmp, HOME=tmp, RETROFIT_WATCH="force")
        payload = json.dumps(dict(session_id="s1", transcript_path=str(p))).encode()
        subprocess.run([sys.executable, legacy, "baseline"], input=payload, env=env, check=True)
        state = Path(tmp, "sessions", "s1.json")
        offset = json.loads(state.read_bytes())["offset"]

        def cap():
            limit = 256 * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_AS, (limit, limit))

        proc = subprocess.run([sys.executable, target, "stop"], input=payload, env=env,
                              capture_output=True, timeout=10, preexec_fn=cap, check=True)
        saved = json.loads(state.read_bytes())
        assert offset == saved["offset"] == p.stat().st_size
        assert not proc.stdout and not proc.stderr
        errors = Path(tmp, "errors.log")
        error = errors.read_text().split()[1].rstrip(":") if errors.exists() else "ok"
        if error == "ok" and target != legacy:
            assert "skill_calls" in saved
        return error


with TemporaryDirectory(prefix="sdd-r10-") as tmp:
    root = Path(tmp)
    legacy = root / "legacy.py"
    legacy.write_bytes(legacy_code)
    result = {
        "slash_040": Journey().measure(legacy, legacy, "slash"),
        "slash_041": Journey().measure(SCRIPT, SCRIPT, "slash"),
        "slash_migrado": Journey().measure(legacy, SCRIPT, "slash"),
        "slash_alheio": Journey().measure(legacy, SCRIPT, "slash", matched=False),
        "sem_vinculo": Journey().measure(legacy, SCRIPT, "skill", proof=False),
        "com_vinculo": Journey().measure(legacy, SCRIPT, "skill", proof=True),
        "falha_sem_origem": ",".join(failed_id(origin=False, reused=True, split=split)
                                    for split in (False, True)),
        "falha_com_origem": ",".join(failed_id(origin=True, reused=True, split=split)
                                    for split in (False, True)),
        "falha_id_novo": ",".join(failed_id(origin=False, reused=False, split=split)
                                 for split in (False, True)),
        "prefixo_040": capped_prefix(root, legacy, legacy),
        "prefixo_041": capped_prefix(root, legacy, SCRIPT),
    }
result["checks_i1_f1"] = vector_checks()
print(" ".join(f"{label}={value}" for label, value in result.items()))
if "--expect" in sys.argv[1:]:
    assert result == dict(slash_040="graphify", slash_041="graphify", slash_migrado="graphify",
                          slash_alheio="silêncio", sem_vinculo="silêncio", com_vinculo="codereview",
                          falha_sem_origem="silêncio,silêncio", falha_com_origem="silêncio,silêncio",
                          falha_id_novo="codereview,codereview", prefixo_040="ok", prefixo_041="ok",
                          checks_i1_f1=2), result
~~~

## Boot da próxima fase

Repetir o Check R10 na árvore atual para ver o Red, mantendo o contrato de saída de I1/F1 e
os controles verdes de R9. Executar em TDD com as três regressões duráveis e repetir o
`TEST_CMD` com o Git isolado. Não editar os relatórios anteriores para fazê-los parecer medidos
no HEAD final.

### Recommended Actions

**Must Fix (CRITICAL)**

_Nenhum._

**Should Fix (HIGH)**

_Nenhum._

**Consider Fixing (MEDIUM/LOW)**

- Fechar R10 com os quatro sensores. O estado salvo, o histórico de créditos, a janela e o
  fallback conservador continuam no contrato.

**Deferred (form)**

- Reposicionar as três âncoras do achado 5 na próxima triagem do backlog.

_Custo da revisão — skill 2.27.38 indicada pela fase, instruções de prosa e segundo pré-scan da instalação 2.30.2. Quatro agentes por arquivo ou grupo, um relançamento por truncamento e zero verificadores, todos gpt-6.1-terra. Resultados completos para 20 arquivos, com 2–17 chamadas por tarefa concluída. Produção e varredura de símbolos inline. Custo monetário não medido._
