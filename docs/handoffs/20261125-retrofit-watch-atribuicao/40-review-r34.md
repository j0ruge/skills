---
missao: 20261125-retrofit-watch-atribuicao
fase: REVIEW
rodada: 34
status: done
sessao: 01a2204e-5ecf-76e2-ab57-c1c4102eb365
data: 2026-11-28 01:07
gate: "Em 880640757cfd70a1a06aecf75c952aa4e0b184a8 com árvore limpa, TEST_CMD com Git isolado retornou rc 0 (154 testes da loja, 3 pulados, 138 do hook e versão 0.4.1). Os 23 Checks concluídos, F1 e quatro testes de release passaram. A sonda nova saiu com rc 1. A nota regrediu em Code Quality (Zen), Error Handling, Test Coverage, Documentation e Overall frente à r33. R22 permanece pending."
reviewed_head: 880640757cfd70a1a06aecf75c952aa4e0b184a8
---

# Review — rodada r34 — Atribuição da retrofit-watch por mensagem

## TL;DR

R21 fechou os quatro cenários relatados na revisão externa. A suíte e os 23 Checks anteriores passaram.
Com estado gravado pela 0.4.0, a guarda de ambiguidade ainda faz o Stop perder a retro de `codereview` ou pedi-la para `ticket`.
Dois achados funcionais viraram R22. Uma limitação das receitas históricas foi para o backlog.
A nota geral é B. Os critérios estritos abaixo de A mantêm o gate vermelho.

## Nota da rodada

Fluxo Codex da skill `/codereview:codereview base=4c065758d4d7be1680208e67c3a322aeb86aaac9`, até `880640757cfd70a1a06aecf75c952aa4e0b184a8`.
O delta tem oito commits, um módulo Python, sua suíte com quatro testes novos e 14 documentos.
O diário append-only ficou fora do escopo de leitura. Nos 15 arquivos analisados, foram 459 linhas adicionadas e 40 removidas.
Python, `unittest`, scanner da skill e jornada de terminal F1. Não houve alteração de interface pública ou grafia a procurar fora do delta.

### Secrets Detection

| Achados | Scanners | Arquivos | Linhas adicionadas | Status |
|---|---|---|---|---|
| 0 | regex e gitleaks | 15 | 459 | PASS |

Nenhum erro de scanner. O delta não altera autorização, dependências nem o armazenamento dos pedidos.

### Qualidade, cobertura e sincronização

| Área | Evidência |
|---|---|
| Legibilidade e simplicidade | As guardas de texto tratam apenas strings e o modo de replay é explícito. O retorno global de ambiguidade mistura a identidade do dono com outras evidências que podem ser independentes. |
| Comportamento e integridade | Houve silêncio com metadado externo comprovadamente antigo, pedido indevido para `ticket` com metadado monitorado antigo e silêncio após uma carga confirmada no cache legado. Em todos os casos a sonda verificou o offset e a ausência de `errors.log`. |
| Segurança e desempenho | O prefixo continua limitado pelo offset e pelo teto por registro. A coleta adicional retém um par de IDs e uma flag, sem nova leitura ou subprocesso por evento. |
| Cobertura | O módulo tem cobertura direta em `test_retrofit_watch.py` e indireta nas sondas e em F1. O R21 cobre dois donos, mas o caso não põe metadado antigo antes de ambos nem traz um caminho posterior comprovado pelo estado. |
| Sincronização | r14, r15 e r19 foram repetidas com Git roteado para uma fixture. O caminho de scanner de r24–r27 funciona no repo correto, mas não verifica se o Git entregou o diff. |

### Código morto e limpeza

Bucket A em linha. O scanner de replay é instanciado, a flag é lida em `skill_path` e as quatro regressões são descobertas pela suíte.
Nenhuma remoção de símbolo, importação ou chamador. Bucket B fora do delta.

### Overall Grade

| Criterion | Grade | Rationale |
|-----------|-------|-----------|
| Code Quality (Zen) | B | A guarda única de ambiguidade descarta provas independentes de qual chamada era a dona. |
| Type Safety | A | O delta distingue texto string dos outros tipos JSON e trata o histórico de slash de tipo inválido como campo ausente. |
| Error Handling | B | A retomada com estado válido da 0.4.0 pode perder o alvo correto ou atribuir o trabalho a outra skill. |
| Security | A | Regex e gitleaks retornaram zero achados e zero erros, sem mudança na autorização ou na fronteira de confiança. |
| Performance | A | O delta mantém os limites de leitura e correlação e acumula apenas um candidato de tamanho constante por replay. |
| Test Coverage | B | Os 23 Checks anteriores passaram, mas não detectaram as quatro saídas incorretas da sonda nova em estados criados pela 0.4.0 real. |
| Documentation | B | As receitas históricas de r24–r27 usam caminho portátil, mas em uma fixture sem os SHAs retornam rc 0 e analisam zero linhas. |
| **Overall** | **B** | R21 fecha os cenários originais, mas a regressão na atribuição legada impede aprovar esta rodada. |

## Achados da rodada

| # | Severidade | Achado | Onde |
|---|---|---|---|
| 1 | MEDIUM | Com duas cargas compatíveis, a retomada perde a prova de que o mesmo ID precede qualquer dono possível. O metadado antigo silencia `codereview` se for externo e pede retro para `ticket` se for monitorado. | `plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py:897–910` |
| 2 | MEDIUM | O replay trata como concorrentes duas cargas mesmo quando a 0.4.0 registrou um caminho novo exclusivo da segunda. A externa vinculada à mensagem dessa segunda carga encerra indevidamente o crédito. | `plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py:862–868,897–906` |
| 3 | LOW | As receitas históricas de r24–r27 aceitam rc 0 com diff vazio quando o Git herdado não contém os SHAs. O scanner recebe zero linhas. | `40-review-r24.md:159`, `40-review-r25.md:134`, `40-review-r26.md:170`, `40-review-r27.md:99` |

No achado 1, a 0.4.0 escaneia a primeira carga. Um Stop ativo avança sobre a segunda sem ler seu delta. A chamada cujo metadado atrasa aparece antes de ambas. Sua posição é comprovada sem eleger uma das duas cargas, na mesma mensagem ou em mensagens distintas.

No achado 2, o caminho da segunda skill não existe no cache antes da segunda carga e aparece no cache salvo pelo Stop normal da 0.4.0. Os contadores e `current` continuam com a mesma chave de plugin, mas o caminho exclusivo comprova que o metadado da segunda chamada foi lido. Em seguida, a externa chega vinculada à mesma mensagem da segunda carga e deveria preservar a monitorada.

O impacto exige retomada de uma sessão legada nessas condições. Os efeitos são perda ou troca do pedido de retro, não perda dos contadores persistidos ou falha no avanço do offset. Por isso os dois achados funcionais são MEDIUM.

## Incrementos de conserto (R<n>)

| R<n> | Achado | Check escrito no checkpoint |
|---|---|---|
| R22 | Achados 1–2 em lote | Sonda desta rodada com `--expect`, jornada F1 e duas regressões duráveis nomeadas na célula. O Check exige `regressoes=2`. |

Linha adicionada ao checkpoint.

~~~text
| R22 | Conservar a prova comum de ID obsoleto e usar o caminho novo confirmado pela 0.4.0 para distinguir o dono (r34, achados 1–2) | `env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -c "$(sed -n '/^~~~python$/,/^~~~$/{ /^~~~/!p; }' docs/handoffs/20261125-retrofit-watch-atribuicao/40-review-r34.md)" --expect && env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B e2e/test_retrofit_watch_stop.py && if o=$(env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -m unittest -q test_retrofit_watch.StopTest.test_legacy_replay_preserves_provably_older_metadata test_retrofit_watch.StopTest.test_legacy_replay_recovers_owner_proven_by_new_path 2>&1); then [[ "$o" == *"Ran 2 tests"* && "$o" == *"OK" ]] && printf 'regressoes=2\n'; else printf '%s\n' "$o" >&2; exit 1; fi` → `older_unique=codereview older_same=codereview older_later=codereview older_monitored=codereview between=silêncio observed_new_path=codereview linked=silêncio missing=silêncio empty=silêncio regressoes=2` | pending | — |
~~~

## O que virou incremento

- Os achados 1–2 viraram `R22`. O Check exige `codereview` para o metadado antigo comprovado sem escolher um dono ambíguo. A externa intercalada continua silenciosa. O caminho novo registrado pela 0.4.0 permite identificar a segunda chamada. Nenhum código foi alterado nesta rodada.
- `R21` foi executado em `e5c249d`. A célula passou com `slash_list=graphify slash_unlinked=graphify null_replay=codereview skipped_owner=codereview`. O caso de dono único com erro próprio permaneceu silencioso dentro da mesma sonda.
- A r33 não deixou achado funcional aberto. `R20` continua fechado em `41f2952` com `fonte_sem_id=ok`. O achado documental da r32 permanece fechado em `02fe0ac` e não volta como incremento.

## O que foi refutado

- Remover o retorno antecipado por completo não é uma correção válida. Na base, `between` escolheu a segunda carga que a 0.4.0 pulou e emitiu `codereview`. No HEAD, esse controle ficou corretamente em silêncio porque a chamada externa pode ser posterior ao dono gravado.
- Não foi observado que o novo replay apagasse o crédito persistido antes do metadado tardio. Nos casos que ficaram silenciosos ou pediram `ticket`, a entrada de `codereview` manteve o trabalho e os contadores originais. O desvio está na atribuição do trabalho seguinte.
- O caminho relativo ao diretório pessoal não quebrou o scanner. Com Git isolado, as quatro receitas históricas devolveram suas contagens. A falha mede o status do pipeline com o Git errado, não ausência da instalação.

## Achados fora de escopo

- O achado 3 foi registrado em `TODO.md`, seção Documentação da loja. É uma limitação das receitas históricas de r24–r27, não da suíte configurada ou da varredura desta rodada. O item anterior de r14–r15 permanece resolvido para aquelas receitas. R14 e R15 foram reexecutadas com Git de fixture e acharam 382 e 175 linhas.

## Pendências / Decisions for a Human

A r33 tinha oito notas A. Code Quality (Zen), Error Handling, Test Coverage, Documentation e Overall regrediram. O R22 está registrado e o gate não fecha neste HEAD. A decisão de prosseguir após a regressão cabe ao mantenedor. O `verified_head` de `50-pr.md` é anterior a R21 e não certifica este candidato. Nenhuma ação no PR foi realizada.

## Evidências reproduzíveis

Comandos na raiz em `880640757cfd70a1a06aecf75c952aa4e0b184a8`, exceto o controle com a base.

- `env -u GIT_DIR -u GIT_WORK_TREE PYTHONDONTWRITEBYTECODE=1 bash -c 'source .sdd/config.sh && eval "$TEST_CMD"'` → rc 0. Loja com 154 testes, três pulados, em 9,284 s. Hook com 138 testes em 58,164 s. Adaptadores, catálogo e versão 0.4.1 validados.
- Comparei o stdout completo das 23 células marcadas `done` em Bash, com `GIT_DIR` e `GIT_WORK_TREE` removidos, e confirmei cada hash como ancestral do HEAD com `git merge-base --is-ancestor`. Os 23 passaram em 63,23 s. I1 deu `1 0 1 0 0 1`. F1 acrescentou `linked=silêncio missing=silêncio empty=silêncio` ao mesmo vetor.
- `env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -m unittest -q test_auto_docs.ReleaseTest` → quatro testes, rc 0. As três provas nativas puladas no comando configurado não foram repetidas nesta rodada.
- `git -P diff 4c065758d4d7be1680208e67c3a322aeb86aaac9...HEAD --unified=0 -- . ':(exclude)docs/handoffs/20261125-retrofit-watch-atribuicao/checkpoint-notas.md' | bash /home/joruge/.agents/skills/codereview/scripts/scan_secrets.sh` → 15 arquivos e 459 linhas, sem segredos ou erros. Execute com `pipefail`.
- No cenário documental, execute em Bash os comandos textuais de r24–r27. Primeiro, remova as duas variáveis Git. As contagens devem ser 530, 452, 327 e 428. Depois, aponte `GIT_DIR` para o `.git` de uma pasta temporária criada com `git init` e `GIT_WORK_TREE` para essa pasta. As quatro receitas retornaram rc 0 com zero linhas e a mensagem de revisão inválida no stderr. As mesmas quatro sob `bash -o pipefail` retornaram rc 128. Os blocos corrigidos de r14, r15 e r19 também foram executados com a fixture. r19 manteve as quatro linhas de controle em Bash e Zsh.

### Sonda de R22

`env -u GIT_DIR -u GIT_WORK_TREE PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -c "$(sed -n '/^~~~python$/,/^~~~$/{ /^~~~/!p; }' docs/handoffs/20261125-retrofit-watch-atribuicao/40-review-r34.md)" --expect` → rc 1 no HEAD revisado. O modo de observação, sem `--expect`, imprime as saídas mesmo quando divergentes. A sonda usa o blob real de `7e623fe` para gravar o estado legado. Para comparar o hook de retomada com a base, extraia `git show 4c065758d4d7be1680208e67c3a322aeb86aaac9:plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py` para um arquivo temporário e use `--script` apontando para esse arquivo, sem `--expect`. A sonda verifica o progresso de todos os Stops e os contadores em disco.

| Caso | Base em observação | HEAD revisado | Esperado |
|---|---|---|---|
| `older_unique` | codereview | codereview | codereview |
| `older_same` | codereview | silêncio | codereview sem escolher chamada |
| `older_later` | codereview | silêncio | codereview sem escolher chamada |
| `older_monitored` | codereview | ticket | codereview sem escolher chamada |
| `between` | codereview | silêncio | silêncio por falta de prova |
| `observed_new_path` | codereview | silêncio | codereview com a chamada do caminho confirmado |

~~~python
import argparse
import json
import re
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

from test_retrofit_watch import SCRIPT, StopTest, identified_load, make_skill, tool

parser = argparse.ArgumentParser()
parser.add_argument("--expect", action="store_true")
parser.add_argument("--script", type=Path, default=SCRIPT)
args = parser.parse_args()


def run(case, legacy):
    t = StopTest()
    t.setUp()
    try:
        w = t.w
        old = case.startswith("older")
        new_path = case == "observed_new_path"
        first = identified_load("codereview:coderabbit-pr", w.mkt_skill, "msg_1", "toolu_1")
        second_msg = "msg_1" if case == "older_same" else "msg_2"
        second_path = make_skill(w.mkt_skill.parent, "codereview") if new_path else w.mkt_skill
        second_name = f"codereview:{second_path.name}"
        second = identified_load(second_name, second_path, second_msg, "toolu_2")
        name, path = ("ticket", w.ticket) if case == "older_monitored" else ("brainstorming", w.other_skill)
        late = identified_load(name, path, "msg_old" if old else second_msg, "toolu_late")

        if old:
            t.write(late[:2], compact=True)
        t.write(first, tool(), compact=True)
        out, before = t.checked_stop(script=legacy)
        assert out is None and "skill_calls" not in before
        assert str(second_path) not in before["classified"] if new_path else True
        if case == "between":
            t.write(late[:2], compact=True)
        if case != "older_unique":
            t.write(second, compact=True)
            out, before = t.checked_stop(script=legacy, active=not new_path)
            assert out is None and "skill_calls" not in before

        key = "full:codereview"
        assert before["current"] == key and before["skills"][key]["work"] == 1
        if new_path:
            assert before["classified"][str(second_path)]["key"] == key
            assert "codereview" in before["skills"][key]["skills"]
        t.write(late if new_path else late[2:], tool(error=True), compact=True)
        out, after = t.checked_stop(script=args.script)
        targets = re.findall(r"`/retrofit-skill:retrofit-skill ([a-z-]+)`", t.context_of(out)) if out else []
        assert len(targets) == int(out is not None), targets
        target = targets[0] if targets else "silêncio"
        assert after["skills"][key]["reviews"] == int(target == "codereview")
        if target != "codereview":
            assert after["skills"][key] == before["skills"][key]
        return target, after["attribution_closed"], after["current_origin"], after["current_call"]
    finally:
        t.tearDown()


name = "plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py"
cases = ("older_unique", "older_same", "older_later", "older_monitored", "between", "observed_new_path")
with TemporaryDirectory() as tmp:
    legacy = Path(tmp) / "legacy.py"
    legacy.write_bytes(subprocess.check_output(["git", "show", f"7e623fe:{name}"]))
    results = {case: run(case, legacy) for case in cases}

print(" ".join(f"{case}={results[case][0]}" for case in cases))
if args.expect:
    assert results["older_unique"] == ("codereview", False, ["msg_1", "toolu_1"], "toolu_1"), results
    for case in ("older_same", "older_later", "older_monitored"):
        assert results[case] == ("codereview", False, None, None), results
    assert results["between"] == ("silêncio", True, None, None), results
    assert results["observed_new_path"] == ("codereview", False, ["msg_2", "toolu_2"], "toolu_2"), results
~~~

### Recommended Actions

**Must Fix (CRITICAL)**

_Nenhuma._

**Should Fix (HIGH)**

_Nenhuma._

**Consider Fixing (MEDIUM/LOW)**

- Executar `R22` em TDD com as duas regressões e o controle intercalado.
- Tratar o achado documental na triagem do backlog, sem incremento funcional.

### Cost footprint

_Skill 2.27.38 do caminho solicitado. Cache Claude 2.30.2 identificado e não usado. Código, testes e Bucket A em linha. Três agentes gpt-6.1-terra concluíram 13 análises documentais, sem relançamento. Custo monetário não medido._
