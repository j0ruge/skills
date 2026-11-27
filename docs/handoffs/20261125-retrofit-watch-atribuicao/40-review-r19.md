---
missao: 20261125-retrofit-watch-atribuicao
fase: REVIEW
rodada: 19
status: done
sessao: 01a21f18-773f-72b3-b640-0bd2b611ed82
data: 2026-11-27 19:24
gate: 'Em 739d48510f66dd56b2f9cadc78ecb36e5977ff4a, árvore inicial limpa. env -u GIT_DIR -u GIT_WORK_TREE PYTHONDONTWRITEBYTECODE=1 bash -c ''source .sdd/config.sh && eval "$TEST_CMD"'' retornou rc 0. Adaptadores e catálogo válidos, 154 testes da loja (3 pulados), 114 testes do hook e versão 0.4.1 validada. Os 14 Checks retornaram rc 0 e o stdout esperado. Documentation permanece B pela propagação de falha da receita histórica da r15. Demais critérios A e nenhum incremento pendente.'
reviewed_head: 739d48510f66dd56b2f9cadc78ecb36e5977ff4a
---

# Review — rodada r19 — Atribuição da retrofit-watch por mensagem

Delta de `b466c6c111a3093da6aa033f84d75428ab0a206a` até `739d48510f66dd56b2f9cadc78ecb36e5977ff4a`, com cinco commits. Foram analisados seis registros. O diário append-only consta na lista de caminhos, mas está fora do parecer.

## TL;DR

A suíte e os 14 Checks passaram. O diff textual corrigiu o caso de Markdown binário.
O bloco completo da r15 ainda devolve rc 0 quando o pré-scan rejeita a contagem.
O falso verde fica no item já aberto do backlog. Documentation B, demais notas A, sem R13.

## Nota da rodada

### Secrets Detection

**Status PASS.** Regex e gitleaks analisaram seis arquivos e 205 linhas adicionadas,
sem ocorrências nem erros. A contagem coincide com o diff textual do recorte
analisado. O diário append-only ficou fora da varredura usada para a nota.

### Código, cobertura e sincronização

Não houve mudança em produção, configuração, esquema de estado, dependências
ou testes. As 14 linhas de incrementos são idênticas às da base. Conferi o rc
e o stdout inteiro de cada Check, normalizando espaços. F1 repetiu a jornada da
QA em dois Stops. R10–R12 repetiram as sondas de retomada e migração.
A suíte descobriu 154 testes da loja, com três pulos configurados, e 114 testes
do hook sem falhas. Não houve smoke no host Claude Code ou no Windows.

A ficha do PR registra `f203d0c` como o commit verificado na abertura. A comparação
Git local com o HEAD desta rodada mostrou apenas diferenças em registros e no
backlog. Esta rodada não consultou o estado remoto nem alterou o PR.

### Varredura de símbolos

Bucket A em linha. O delta não introduziu nem deixou órfão símbolo produtivo.
As variáveis acrescentadas às receitas são locais e usadas. Nenhuma interface
foi renomeada. Bucket B não solicitado.

### Overall Grade

| Criterion | Grade | Rationale |
|-----------|-------|-----------|
| Code Quality (Zen) | A | O delta altera somente registros e receitas manuais, sem mudança nas 14 células de Check. |
| Type Safety | A | O recorte não muda tipos, assinaturas, dependências nem o formato do estado persistido. |
| Error Handling | A | F1 e R12 confirmaram o encerramento conservador e os controles de carga nova e slash. A falha de propagação está na receita manual histórica. |
| Security | A | O pré-scan independente leu as 205 linhas do recorte analisado, sem credenciais ou erros, e nenhum controle produtivo mudou. |
| Performance | A | Nenhum caminho de execução mudou. As verificações de retomada e migração R10–R12 passaram. |
| Test Coverage | A | A suíte configurada passou e os 14 Checks confirmaram tanto o rc quanto o resultado completo. |
| Documentation | B | O diff textual fechou o caso binário, mas o bloco completo da r15 ainda termina com sucesso quando a verificação de contagem falha. |
| **Overall** | **A** | Sem regressão funcional no delta. O falso verde reproduzido se limita à receita manual histórica. |

## Achados da rodada

| # | Severidade | Achado | Onde |
|---|---|---|---|
| 1 | MEDIUM | O `set -e` do pré-scan vale apenas no subshell. Se a contagem for rejeitada, o bloco completo da r15 continua sem JSON até o teste de release e termina com rc 0 quando ele passa. | `40-review-r15.md:117–126` |

Em Bash e Zsh sem `errexit` no shell externo, o negativo saiu com rc 0 e sem JSON,
e as duas validações do kit e os quatro testes de release passaram depois da
rejeição. O mesmo negativo no subshell isolado, ou no bloco completo com
`errexit` externo, saiu com rc 1. A receita completa da r14 já propaga a falha,
pois o subshell é seu último comando.

## Incrementos de conserto (R<n>)

Nenhum. I1, F1 e R1 a R12 continuam em `done`.

## O que virou incremento

Nenhum nesta rodada.

- I1, fechado em `682cd3d`, voltou a imprimir `1 0 1 0 0 1`. F1, fechado em
  `c704301`, ficou em silêncio nas três variantes do segundo Stop verificadas pela QA.
- R12, fechado em `d77e6a1`, voltou a ficar em silêncio no limite, acima dele e após
  outro Stop. Carga nova e slash explícito pediram `graphify`.

## O que foi refutado

- O caso exato da r18 está fechado em `f41ad63`. Com `*.md -diff` em um arquivo
  temporário de atributos, as receitas antigas do blob revisado na r18 retornaram
  rc 0 com zero linhas. No HEAD, as receitas da r14 e r15 voltaram a analisar
  9 arquivos e 382 linhas, e 3 arquivos e 175 linhas, respectivamente, em Bash e Zsh.
- A hipótese de que exigir a contagem fecha todo falso verde da receita é refutada
  pelo achado 1. A condição do `jq` rejeita a contagem no subshell, mas o bloco
  copiado por inteiro não propaga a falha em um shell sem `errexit`.

## Achados fora de escopo

- O achado 1 foi registrado no item existente “Pré-scan manual da revisão pode
  passar sem analisar linhas”, em `TODO.md`. O item distingue a correção comprovada
  do caso restante. Não há duplicata nem nova entrada de `RECURRED` para o mesmo
  par de projeto e missão.

## Pendências / Decisions for a Human

Nenhuma decisão técnica nova. As letras permaneceram iguais às da r18.
`Documentation` está no patamar B tolerado pelo gate e os critérios estritos
ficaram em A. A revisão para sem incremento pendente. Integrar o PR cabe ao
mantenedor.

## Evidências reproduzíveis

Execute da raiz. A suíte e os Checks rodaram em `739d48510f66dd56b2f9cadc78ecb36e5977ff4a`.
O comando exato da suíte está no campo `gate`. Para os Checks, execute cada célula
de `checkpoint.md` com `env -u GIT_DIR -u GIT_WORK_TREE PYTHONDONTWRITEBYTECODE=1 bash -c "$check"`
e confira rc 0 e o stdout inteiro após normalizar espaços. A checagem estrutural
do kit confirmou 14 linhas válidas no checkpoint.

O controle negativo histórico é o segundo bloco Bash de `40-review-r18.md`.
Para repetir os controles desta rodada, extraia o primeiro bloco Bash de cada
relatório no commit revisado. A sonda muda somente a contagem esperada no
`jq` para `-1` em cópias temporárias, de modo que a rejeição seja determinística.
Nenhum checkout ou arquivo versionado é alterado.

~~~python
import os
from pathlib import Path
import re
import subprocess
import tempfile

mission = "docs/handoffs/20261125-retrofit-watch-atribuicao"
reviewed = "739d48510f66dd56b2f9cadc78ecb36e5977ff4a"
with tempfile.TemporaryDirectory() as directory:
    temporary = Path(directory)
    attributes = temporary / "attributes"
    attributes.write_text("*.md -diff\n")
    for round_, expected in [(14, 382), (15, 175)]:
        blob = subprocess.check_output(
            ["git", "show", f"{reviewed}:{mission}/40-review-r{round_}.md"], text=True
        )
        recipe = blob.split("~~~bash\n", 1)[1].split("\n~~~", 1)[0]
        original = temporary / "original"
        original.write_text(recipe)
        negative = temporary / "negative"
        rejected, edits = re.subn(
            r"(?m)^(  jq -e '\.scanned\.added_lines == )\d+", r"\g<1>-1", recipe
        )
        assert edits == 1
        negative.write_text(rejected)
        for shell in ("bash", "zsh"):
            env = dict(os.environ, GIT_CONFIG_COUNT="1", GIT_CONFIG_KEY_0="core.attributesFile",
                       GIT_CONFIG_VALUE_0=str(attributes))
            binary = subprocess.run([shell, str(original)], env=env, capture_output=True, text=True)
            plain = subprocess.run([shell, str(negative)], capture_output=True, text=True)
            strict = subprocess.run([shell, "-e", str(negative)], capture_output=True, text=True)
            assert binary.returncode == 0 and f'"added_lines": {expected}' in binary.stdout
            assert plain.returncode == (0 if round_ == 15 else 1)
            assert '"added_lines"' not in plain.stdout and strict.returncode == 1
            if round_ == 15:
                assert "Ran 4 tests" in plain.stderr and plain.stderr.rstrip().endswith("OK")
                assert "Ran 4 tests" not in strict.stderr
            print(shell, f"r{round_}", f"binário={expected}",
                  f"rejeitado={plain.returncode}", f"rejeitado_errexit={strict.returncode}")
~~~

### Recommended Actions

**Must Fix (CRITICAL)**

_Nenhum._

**Should Fix (HIGH)**

_Nenhum._

**Consider Fixing (MEDIUM/LOW)**

- Na triagem do item do pré-scan manual, fazer a falha da contagem terminar o
  bloco inteiro da r15 ou registrar explicitamente o resultado e impedir que
  o teste de release dê um veredito de sucesso ao pré-scan.

### Cost footprint

_Codereview 2.27.38, no caminho pedido para o Codex. O cache do Claude registrava
2.30.2 e não foi usado. Dois agentes gpt-6.1-terra, seis leituras integrais e
2–18 chamadas informadas por agente, sem relançamentos. Bucket A em linha.
Custo monetário não medido._
