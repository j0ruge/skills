---
missao: 20261125-retrofit-watch-atribuicao
fase: REVIEW
rodada: 21
status: done
sessao: 01a21f37-1547-7a30-88fb-74d923dc02a7
data: 2026-11-27 19:58
gate: 'Em 757396c8f6db5130ee6bc9d4233ceea878ea94a4, árvore inicial limpa. env -u GIT_DIR -u GIT_WORK_TREE PYTHONDONTWRITEBYTECODE=1 bash -c ''source .sdd/config.sh && eval "$TEST_CMD"'' retornou rc 0. Adaptadores e catálogo válidos, 154 testes da loja (3 pulados), 114 do hook e versão 0.4.1 validada. Os 14 Checks retornaram rc 0 e stdout esperado. Documentation permanece B pela origem implícita da amostra histórica. Critérios estritos e Overall em A, sem incremento pendente.'
reviewed_head: 757396c8f6db5130ee6bc9d4233ceea878ea94a4
---

# Review — rodada r21 — Atribuição da retrofit-watch por mensagem

## TL;DR

A r21 confirmou o conserto em `41a6ca5`. A sonda isolada funciona em Bash e Zsh sem `SDD_KIT`.
O único achado novo é documental. A r15 não fixa a versão da amostra e o item atual deixa passar o controle negativo.
A suíte e os 14 Checks passaram. Documentation B, demais critérios A, nenhum incremento novo.

## Nota da rodada

### Secrets Detection

| Ocorrências | Scanners | Arquivos | Linhas adicionadas | Status |
|---|---|---|---|---|
| 0 | regex e gitleaks | 4 | 177 | PASS |

O resultado não trouxe erros e conferiu com o `--numstat` dos mesmos quatro caminhos.

### Qualidade, cobertura e sincronização

O argumento `base=e32b365158e8c555d99c503e94332c8a7d0b0fe2` limitou a revisão até
`757396c8f6db5130ee6bc9d4233ceea878ea94a4`. Foram quatro commits. O quinto caminho
alterado é o diário append-only, excluído sem leitura. O delta analisado compreende
`TODO.md`, `40-review-r15.md`, `40-review-r20.md` e `checkpoint.md`.
Nenhum módulo produtivo, configuração ou teste mudou. A receita revisada é manual.
As 14 células de Check são idênticas às da base e foram executadas com comparação do
stdout integral. A QA já registrou a jornada de Stop em `30-handoff-qa.md`. A r21
repetiu I1 e F1 pelo checkpoint. Os três testes de distribuição nativa continuam
pulados por configuração. Não houve smoke no host Claude Code ou no Windows.

### Varredura de símbolos

Bucket A em linha. Nenhuma interface ou símbolo produtivo introduzido, renomeado
ou órfão. `SDD_KIT` no novo subshell é consumida pelo validador e `fixture`
continua sendo fornecida na chamada. Bucket B não solicitado.

### Overall Grade

| Criterion | Grade | Rationale |
|-----------|-------|-----------|
| Code Quality (Zen) | A | Sem alterações no hook ou nas células de Check. A sonda manual que mudou é autocontida em Bash e Zsh. |
| Type Safety | A | O recorte não altera assinaturas, tipos, configuração ou o formato serializado do estado. |
| Error Handling | A | A sonda propagou a rejeição do linter e o bloco principal bloqueou a execução no pré-scan inválido nos dois shells. |
| Security | A | Regex e gitleaks examinaram 177 linhas adicionadas em quatro arquivos, sem ocorrências ou erros. |
| Performance | A | Nenhum caminho produtivo mudou e os Checks de migração R10 a R12 mantiveram os resultados esperados. |
| Test Coverage | A | Os 14 Checks e a suíte de 154 testes da loja e 114 do hook passaram. Três pulos de distribuição estavam configurados. |
| Documentation | B | A r15 resolve o caminho do kit, mas a amostra atual não produz a rejeição histórica que a receita anuncia. |
| **Overall** | **A** | Sem regressão funcional no delta. O único achado afeta a preparação da amostra manual e foi registrado no backlog. |

## Achados da rodada

| # | Severidade | Achado | Onde |
|---|---|---|---|
| 1 | LOW | A receita não identifica o blob do item a copiar. Com o backlog atual, acrescentar as três linhas indicadas produz uma amostra de oito linhas que o linter aceita, sem o diagnóstico esperado de nove linhas. | `40-review-r15.md:129–145` |

O marcador já está no corpo do item atual. Copiei esse item para um backlog
temporário, ajustei a âncora para `TODO.md:1` e rodei o bloco da r15 sem
`SDD_KIT`. Em Bash e Zsh, a amostra inicial tinha cinco linhas e retornou
rc 0. Depois das três inserções ficou com oito e continuou em rc 0. Com o
item histórico de seis linhas, cuja origem a r20 indica, obtive rc 0, 1 e 0
para seis, nove e oito linhas nos dois shells. A falha está na escolha da
amostra, não no limite do linter nem na resolução do kit.

## Incrementos de conserto (R<n>)

Nenhum. I1, F1 e R1 a R12 continuam em `done`. O achado 1 é da prosa
de uma reprodução manual e não muda a jornada nem os Checks do checkpoint.

## O que virou incremento

Nenhum nesta rodada.

- O achado documental da r20 foi fechado em `41a6ca5`. Retestei os trechos
  extraídos de cada ponta. Em Bash e Zsh, o bloco principal seguido da sonda
  de seis linhas foi de rc 127 na base para rc 0 no HEAD, sem `SDD_KIT` externo.
- I1, entregue em `682cd3d`, manteve `1 0 1 0 0 1`. F1, fechado em
  `c704301`, manteve silêncio no segundo Stop com ID válido, ausente e vazio.
  R12, fechado em `d77e6a1`, manteve silêncio para metadado atrasado, inclusive
  após retomada, com os pedidos de `graphify` preservados para carga nova e slash.

## O que foi refutado

- A leitura de que `"$rev:docs/…"` na r20 quebraria em Zsh não se confirmou.
  Em Bash e Zsh o comando literal retornou rc 0 em `739d485` e `e32b365`.
  O stdout coincidiu byte a byte com `git show` de cada referência passada
  como argumento único, sem expansão pelo shell.
- O novo bloco não depende de exportar `SDD_KIT` no bloco anterior. Executado
  sozinho, distinguiu as três amostras históricas. A de nove linhas saiu com
  rc 1 e `9 content lines, cap is 8`.
- O conserto não reabriu o falso verde do pré-scan. O primeiro bloco permaneceu
  idêntico ao da base. Deu rc 0 com 175 linhas e quatro testes de release.
  Trocando apenas `== 175` por `== -1`, deu rc 1 sem imprimir o JSON do scan
  nem alcançar o teste de release nos dois shells.
- O total histórico da r20 não usa o delta atual. O `--numstat` no recorte
  `739d485...e32b365` devolveu 197 adições nos quatro arquivos esperados.

## Achados fora de escopo

- Achado 1 na seção “Documentação da loja” de `TODO.md` (2026-11-27). A direção
  é apontar a preparação da amostra para o blob já identificado na r20.

## Pendências / Decisions for a Human

Nenhuma decisão técnica nova. As letras da r20 e da r21 são iguais.
Documentation permanece em B, no piso tolerado pelo gate, por um achado
diferente do corrigido. Os critérios estritos continuam em A. A integração
continua com o mantenedor.

## Evidências reproduzíveis

- No HEAD revisado, execute da raiz o comando da suíte no campo `gate`.
  Para cada célula da tabela de `checkpoint.md`, isole o comando antes da
  seta e execute `env -u GIT_DIR -u GIT_WORK_TREE PYTHONDONTWRITEBYTECODE=1 bash -c "$check"`.
  Compare o rc e o stdout inteiro, normalizando só espaços. Os validadores do
  kit confirmaram as 14 linhas do checkpoint e as 45 entradas do backlog
  no HEAD revisado.
- Pré-scan da r21 na raiz, comparado com o `--numstat` do mesmo recorte.

~~~bash
(
  set -o pipefail
  git -c diff.noprefix=false -P diff --text --no-ext-diff --no-textconv --no-color --src-prefix=a/ --dst-prefix=b/ e32b365158e8c555d99c503e94332c8a7d0b0fe2...757396c8f6db5130ee6bc9d4233ceea878ea94a4 --unified=0 -- . ':(exclude)docs/handoffs/20261125-retrofit-watch-atribuicao/checkpoint-notas.md' |
    bash "$HOME/.agents/skills/codereview/scripts/scan_secrets.sh"
)
~~~

- Extraia a r15 com `git show` nas duas pontas do recorte. Concatene o primeiro
  bloco e o comando avulso da linha 132 na base, ou o primeiro e o segundo
  blocos no HEAD. Execute cada versão como arquivo, com
  `env -u SDD_KIT fixture="$fixture" bash "$receita"` e com `zsh`.
  Rode também o segundo bloco do HEAD sozinho para isolar a sonda.
- Em uma pasta temporária com `TODO.md` e os marcadores `sdd:open` e
  `sdd:decided`, use o item “A fonte do incidente da atribuição leva à
  reprodução sintética” vindo de `git show 11ae63baa9d93c2236f04c651fd5900d5ba1151a:TODO.md`.
  Troque a âncora local por `TODO.md:1`. Insira três linhas curtas antes da linha
  isolada do marcador para a amostra de nove e junte o marcador à terceira
  linha inserida para a de oito. Para reproduzir o achado 1, prepare uma cópia
  com o mesmo item de `git show 757396c8f6db5130ee6bc9d4233ceea878ea94a4:TODO.md`
  e repita a inserção antes do marcador, mantendo-o na última linha inserida.
  Essa cópia começa com cinco linhas e passa com oito.

### Recommended Actions

**Must Fix (CRITICAL)**

_Nenhum._

**Should Fix (HIGH)**

_Nenhum._

**Consider Fixing (MEDIUM/LOW)**

- Na triagem documental, fixar na r15 a versão do backlog que ainda tem o
  marcador em linha própria. O achado não exige novo ciclo de EXEC.

### Cost footprint

_Codereview 2.27.38 do caminho solicitado, distinto do plugin Claude 2.30.2
registrado. Três agentes gpt-6.1-terra, 17 chamadas e 13 leituras integrais
informadas no total. Sem relançamentos. Varredura de símbolos em linha.
Custo monetário não medido._
