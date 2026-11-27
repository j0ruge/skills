---
missao: 20261125-retrofit-watch-atribuicao
fase: REVIEW
rodada: 20
status: done
sessao: 01a21f30-07d3-76d1-84f3-331d03656e71
data: 2026-11-27 19:51
gate: 'Em e32b365158e8c555d99c503e94332c8a7d0b0fe2, árvore inicial limpa. env -u GIT_DIR -u GIT_WORK_TREE PYTHONDONTWRITEBYTECODE=1 bash -c ''source .sdd/config.sh && eval "$TEST_CMD"'' retornou rc 0. Adaptadores e catálogo válidos, 154 testes da loja (3 pulados), 114 do hook e versão 0.4.1 validada. Os 14 Checks confirmaram rc 0 e stdout esperado. Documentation permanece B pelo escopo da variável na reprodução histórica. Critérios estritos A, sem incremento pendente.'
reviewed_head: e32b365158e8c555d99c503e94332c8a7d0b0fe2
---

# Review — rodada r20 — Atribuição da retrofit-watch por mensagem

Delta de `739d48510f66dd56b2f9cadc78ecb36e5977ff4a` até `e32b365158e8c555d99c503e94332c8a7d0b0fe2`. Quatro commits e quatro arquivos analisados. O diário append-only consta apenas na lista de caminhos e ficou fora do parecer.

## TL;DR

O bloco completo da r15 agora interrompe a execução quando o pré-scan rejeita a contagem.
A reprodução manual seguinte perdeu o caminho do kit. O achado documental foi reproduzido e registrado no backlog.
Suíte e 14 Checks verdes. Documentation B, demais critérios A, sem R13.

## Nota da rodada

### Secrets Detection

| Ocorrências | Scanners | Arquivos | Linhas adicionadas | Status |
|---|---|---|---|---|
| 0 | regex e gitleaks | 4 | 197 | PASS |

Os totais do pré-scan coincidem com o diff textual, sem erros. O diário append-only ficou excluído.

### Qualidade, cobertura e sincronização

Nenhum arquivo de produção, teste, configuração ou interface pública mudou. O delta cobre
a receita de verificação da r15, o registro histórico da r19, o item de backlog e a data do
checkpoint. As 14 linhas de incrementos são idênticas às da base e retornaram rc 0 com o
stdout esperado. O teste de release da receita válida executou quatro testes. Não houve
smoke no host Claude Code nem no Windows.

### Varredura de símbolos

Bucket A em linha. Nenhum símbolo produtivo foi introduzido ou ficou órfão. As variáveis
criadas na receita têm uso local. A perda da definição acima de um uso na prosa está no
achado 1. Nenhuma interface renomeada. Bucket B não solicitado.

### Overall Grade

| Criterion | Grade | Rationale |
|-----------|-------|-----------|
| Code Quality (Zen) | A | O delta não muda código produtivo nem as 14 células de Check. O subshell estrito concentra a verificação manual. |
| Type Safety | A | O delta não altera assinaturas, tipos, dependências ou o formato de estado do hook. |
| Error Handling | A | O bloco principal termina na primeira falha em Bash e Zsh. F1 e R12 confirmam o encerramento conservador no hook. |
| Security | A | Regex e gitleaks verificaram as 197 linhas adicionadas dos quatro arquivos do recorte, sem ocorrências nem erros. |
| Performance | A | Nenhum caminho produtivo foi modificado. R10 a R12 passaram nas sondas de retomada e migração. |
| Test Coverage | A | Os 14 Checks mantiveram o resultado esperado e a suíte rodou 154 testes da loja e 114 do hook, com três pulos configurados. |
| Documentation | B | A reprodução isolada do limite de linhas do backlog usa uma variável agora local ao subshell anterior e falha após um bloco válido. |
| **Overall** | **A** | Não houve regressão funcional. O único achado reproduzido afeta uma instrução histórica fora dos gates. |

## Achados da rodada

| # | Severidade | Achado | Onde |
|---|---|---|---|
| 1 | LOW | O conserto tornou `SDD_KIT` local ao subshell. A instrução seguinte usa a variável no shell externo e tenta executar `/tests/check-todo.sh` mesmo após o bloco de verificação passar. | `40-review-r15.md:122,132` |

Atribuição ausente no ambiente inicial e ambos os trechos executados no mesmo shell.
Bash e Zsh retornaram rc 0 na base e rc 127 no HEAD. O bloco principal ainda analisou
175 linhas e executou os quatro testes de release. Quando a resolução do kit é repetida
na sonda externa, o validador volta a medir o que a r15 descreve. Seis linhas dão rc 0,
nove dão rc 1 com `9 content lines, cap is 8` e oito dão rc 0.

## Incrementos de conserto (R<n>)

Nenhum. O achado é da reprodução documental da r15, fora dos Checks e da jornada de Stop. I1, F1 e R1 a R12 continuam em `done`.

## O que virou incremento

Nenhum nesta rodada.

- I1, fechado em `682cd3d`, voltou a imprimir `1 0 1 0 0 1`. F1, fechado em
  `c704301`, repetiu o silêncio nas três variantes do segundo Stop, como na QA.
- R12, fechado em `d77e6a1`, ficou em silêncio para metadado atrasado no limite,
  acima dele e após novo Stop. Carga nova e slash explícito pediram `graphify`.

## O que foi refutado

- O falso verde da r19 não persiste. Em Bash e Zsh, o mesmo controle com contagem
  esperada alterada para `-1` deu rc 0 na base, sem JSON e com quatro testes de release.
  Em `26feade` a execução inteira passou a usar o subshell estrito. No HEAD, o controle
  retornou rc 1, sem JSON e sem executar o release.
- A receita atual deu rc 0 e analisou 175 linhas em cada shell, inclusive com Markdown
  marcado como binário, cor forçada, sem prefixos por configuração e comparador externo
  configurado em conjunto. O comparador temporário não foi chamado.
- Uma falha na leitura Git antes do pré-scan deu rc 128 e não alcançou o release.
  Um filtro de release inexistente, após o pré-scan válido, deu rc 1 nos dois shells.
- O linter e o achado do marcador da r15 continuam verificáveis com o caminho do kit
  definido no shell externo. A regressão só impede que o leitor chegue ao linter.

## Achados fora de escopo

- A reprodução que perdeu `SDD_KIT` foi registrada em `TODO.md` na seção
  “Documentação da loja” (2026-11-27). Afeta a demonstração do limite de linhas,
  não o pré-scan já corrigido no item vizinho.

## Pendências / Decisions for a Human

Nenhuma decisão técnica nova. As letras ficaram iguais às da r19. O patamar B
em Documentation é tolerado pelo gate e os critérios estritos ficaram em A.
O merge continua com o mantenedor.

## Evidências reproduzíveis

- Suíte no HEAD revisado com o comando do campo `gate`. Para os 14 Checks, leia cada
  célula de `checkpoint.md` e execute `env -u GIT_DIR -u GIT_WORK_TREE PYTHONDONTWRITEBYTECODE=1 bash -c "$check"`,
  sendo `check` o comando à esquerda da seta. Compare o rc e o stdout inteiro,
  normalizando só espaços. A estrutura também foi verificada pelos validadores
  `check-checkpoint.sh --check docs/handoffs/20261125-retrofit-watch-atribuicao/checkpoint.md`
  e `check-todo.sh --check TODO.md --allow-empty` do kit.
- Pré-scan do recorte com `git -c diff.noprefix=false -P diff --text --no-ext-diff --no-textconv --no-color --src-prefix=a/ --dst-prefix=b/ 739d48510f66dd56b2f9cadc78ecb36e5977ff4a...e32b365158e8c555d99c503e94332c8a7d0b0fe2 --unified=0 -- . ':(exclude)docs/handoffs/20261125-retrofit-watch-atribuicao/checkpoint-notas.md' | bash "$HOME/.agents/skills/codereview/scripts/scan_secrets.sh"`.
  A mesma seleção de caminhos com `--numstat` confirmou as 197 adições.
- Receitas em cópias temporárias. Faça `git show "$rev:docs/handoffs/20261125-retrofit-watch-atribuicao/40-review-r15.md"`
  para cada ponta do recorte e extraia o primeiro bloco cercado de Bash. Rode o arquivo
  com Bash e Zsh, ambos sem `errexit` externo. Para a rejeição, troque só `== 175` por
  `== -1` na condição do `jq`. Para os controles adicionais no HEAD, use atributos
  temporários `*.md -diff`, `color.ui=always`, `diff.noprefix=true` e um
  `GIT_EXTERNAL_DIFF` que registra se foi chamado. Separadamente, troque o primeiro
  caminho no `git show` ou o nome da classe de release por um inexistente.
- Para o achado 1, use a amostra de seis linhas descrita na r15 com o item “A fonte do
  incidente da atribuição leva à reprodução sintética” em
  `git show 11ae63baa9d93c2236f04c651fd5900d5ba1151a:TODO.md`.
  Adapte a âncora para `TODO.md:1`, em um `TODO.md` temporário com os dois marcadores.
  Anexe ao arquivo que executa o bloco o comando de reprodução da r15 no blob
  `e32b365:docs/handoffs/20261125-retrofit-watch-atribuicao/40-review-r15.md`
  que consulta `$SDD_KIT/tests/check-todo.sh`. Rode com `env -u SDD_KIT fixture="$fixture" bash "$receita"`
  e repita com `zsh`. Para o controle, execute apenas esse comando depois de copiar para
  o mesmo shell a definição de `SDD_KIT` da receita e repita nas amostras de seis,
  nove e oito linhas. Nenhuma cópia temporária foi versionada.

### Recommended Actions

**Must Fix (CRITICAL)**

_Nenhum._

**Should Fix (HIGH)**

_Nenhum._

**Consider Fixing (MEDIUM/LOW)**

- Na triagem documental, resolver o caminho do kit na própria instrução que usa a amostra
  do backlog. Manter a propagação de falha do bloco anterior.

### Cost footprint

_Codereview 2.27.38 do caminho pedido, independente do cache Claude 2.30.2.
Dois agentes gpt-6.1-terra, quatro leituras integrais informadas e 6 a 14 chamadas por agente,
sem relançamentos. Passada de símbolos em linha. Custo monetário não medido._
