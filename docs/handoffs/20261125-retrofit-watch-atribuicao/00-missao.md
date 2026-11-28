---
missao: 20261125-retrofit-watch-atribuicao
titulo: Preservar o pedido de retro da skill monitorada quando uma externa carrega na mesma mensagem
data: 2026-11-25
versao: 0.4.1
branch: fix/retrofit-watch-atribuicao-mesma-mensagem
aprovacao: humano-2026-11-25
adr: none
ddd: n/a
qa:
kaizen_log:
campaign: 20261125-loja-skills
lot: L1
---

# Missão — Preservar a atribuição da retrofit-watch na mesma mensagem

## Problema (Gemba)

Na issue `j0ruge/skills#12`, o trabalho feito após duas cargas perde o vínculo com a skill monitorada. No HEAD `e45db9e`, reproduzimos o defeito com os construtores de transcript do plugin. Após carregar `codereview:coderabbit-pr`, carregar `superpowers:brainstorming` e executar uma ferramenta com erro, `cmd_stop` ficou em silêncio tanto com o mesmo `message.id` quanto com IDs distintos. A monitorada sozinha, com o mesmo trabalho, recebeu o pedido de retro. A retomada entre a chamada externa e sua linha `isMeta` reproduziu os dois silêncios. O Check e os limites da medição estão em `01-plano.md`.

## Métrica

Em leitura contínua e em duas chamadas de Stop, a saída deve conter `/retrofit-skill:retrofit-skill codereview` quando as duas cargas forem da mesma mensagem. A saída deve ser vazia quando a externa vier de mensagem posterior. Na retomada de estado antigo sem correlação, a carga externa também deve encerrar a atribuição. A monitorada sozinha deve continuar recebendo o pedido. Vetor observado `0 0 0 0 0 1`. Esperado `1 0 1 0 0 1`, na ordem definida no plano.

## Resultado esperado

O hook reconhece a mensagem que originou cada carga e atribui o trabalho posterior à monitorada quando o vínculo é confiável. A carga externa de outra mensagem encerra a atribuição para trabalho futuro. Uma sessão iniciada com a 0.4.0 pode continuar a partir do offset salvo, com seus contadores e histórico. A correção sai como patch 0.4.1 do plugin Claude.

## Fora de escopo

A issue #11 e o projeto 0.5.0 seguem em seu próprio fluxo. O L1 exclui mudanças de modo autônomo, publicação, fila, critérios de elegibilidade, catálogo Codex, instalador e refatorações gerais.

## Campanha e delegação

No piloto, o teto do L1 era `plan`, com aprovação e merge reservados ao mantenedor.
Em 27/11, o mantenedor autorizou delegação `full` para a campanha da loja, registrada
no checkout operacional em `f25cc8f`. Cada ato usa os termos vigentes da campanha.
Para o merge, o worker confere orçamento, permissão e `pr-ready` no SHA do PR e
usa esse SHA no merge. [Procedimento do kit](https://github.com/j0ruge/sdd_agents/blob/main/commands/sdd-worker.md#merge)

## Gate PLAN-AUTO

| # | Critério | Status | Evidência |
|---|---|---|---|
| a | Grill sem perguntas abertas não endereçadas | ✅ | Retomada e versão decididas abaixo. Aprovação e merge têm dono. |
| b | Checklist kaizen e DDD | ✅ | K1–K8 endereçados. DDD `n/a` justificado. |
| c | Autocontenção | ✅ | Os três rascunhos identificam a raiz, fixtures, corte do transcript, código da sonda, resultado por caso, arquivos de versão e comando da suíte. A sonda foi executada com esses dados. |
| d | Cada Check vermelho no HEAD pelo `--red` do kit | ✅ | O `--red` executado no worktree em `e45db9e` confirmou I1 vermelha, imprimindo `0 0 0 0 0 1` diante de `1 0 1 0 0 1`. |
| e | Versão confirmada | ✅ | O worker seguiu a opção recomendada de 0.4.1 sob a delegação do L1. `JIRA_ENABLED=false`. |
| f | ADR decidido | ✅ | `none`. A mudança é local e reversível. A correlação usa identificadores que o transcript já fornece. |

## Checklist kaizen (`kaizen-software`)

| # | Item | Status | Nota |
|---|---|---|---|
| K1 | Gemba | ✅ | Stop executado em seis cenários com transcript sintético e estado em memória. |
| K2 | Problema com métrica | ✅ | O pedido para o alvo correto e o silêncio são observáveis na saída do hook. |
| K3 | Desperdícios cortados | ✅ | Um defeito, um patch, sem incorporar o projeto 0.5.0. |
| K4 | Fatiamento | ✅ | Um incremento reúne reprodução, correção, regressão e versão coerente. |
| K5 | Check por artefato | ✅ | A sonda lê `hookSpecificOutput.additionalContext` e distingue ausência completa de saída. |
| K6 | Jidoka | ✅ | Resultado divergente, perda de estado ou falha da suíte interrompem a entrega. |
| K7 | SDCA | ✅ | Os testes permanentes entram em `test_retrofit_watch.py`, já descoberto pelo `TEST_CMD`. |
| K8 | Registro no KAIZEN_LOG | ✅ | Prevista na fase DOCS uma entrada curta com o ID da missão, o antes/depois medido e o teste que ficou. |

## Checklist DDD (`ddd`) — condicional

`n/a — sem toque de domínio`. O patch corrige a associação interna entre registros de uma carga. Preserva os conceitos de skill, trabalho, atrito e pedido de retro e o contrato público do hook.

## Decisões do grill (não re-litigar)

O worker respondeu às duas perguntas pela delegação assinada do L1, seguindo as opções recomendadas.

1. Pergunta registrada pelo relay
   - question: Medi o pedido de retro do \`codereview\` na saída de \`cmd\_stop\`, usando os fixtures do plugin e estado em memória. Com o mesmo trabalho após as cargas, o pedido apareceu com a monitorada sozinha e sumiu nos dois casos com a externa. A correção deve mudar apenas o resultado em que as duas cargas têm o mesmo \`message.id\`.&#10;&#10;O Check do L1 deve cobrir também o caso em que o hook salva o estado entre a chamada \`Skill\` e a chegada da linha \`isMeta\` com o diretório da skill?&#10;&#10;A (recomendada) — Sim. Testar a leitura contínua e a retomada em duas chamadas do hook. Na retomada, preservar a atribuição quando \`sourceToolUseID\` ligar a carga à mesma mensagem. Com estado antigo sem essa correlação, manter o encerramento conservador.&#10;&#10;B — Testar o par e a mensagem posterior em uma única leitura. Na retomada, manter o encerramento conservador mesmo quando a correlação estava disponível antes de salvar o estado.
   - answer: (other: A (recomendada) — Sim. Testar a leitura contínua e a retomada em duas chamadas do hook. Na retomada, preservar a atribuição quando \`sourceToolUseID\` ligar a carga à mesma mensagem. Com estado antigo sem essa correlação, manter o encerramento conservador.)

2. Pergunta registrada pelo relay
   - question: Medi também a retomada em duas chamadas de \`cmd\_stop\`, com o estado serializado em JSON em memória entre elas. Hoje, o pedido de retro some tanto com o mesmo \`message.id\` quanto com IDs distintos. O controle com a monitorada sozinha emitiu o pedido esperado.&#10;&#10;Qual versão deve identificar a correção da issue #12?&#10;&#10;A (recomendada) — 0.4.1. É o próximo patch após a 0.4.0 registrada na loja e mantém a 0.5.0 reservada ao trabalho da issue #11.&#10;&#10;B — Outra versão de patch da série 0.4.x. Indique o número que o mantenedor reservou para esta correção.
   - answer: (other: A (recomendada) — 0.4.1. É o próximo patch após a 0.4.0 registrada na loja e mantém a 0.5.0 reservada ao trabalho da issue #11.)

## Pendências para o humano

I1 estava vermelha em `e45db9e` antes da correção e passou em `682cd3d`. O mantenedor aprovou o plano em 25/11/2026. O merge do futuro PR para `main` é a decisão pendente do mantenedor.
