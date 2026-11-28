---
missao: 20261127-retrofit-watch-050
titulo: Permitir retrofit de skills locais com ensaio antes do push autônomo
data: 2026-11-27
versao: 0.5.0
branch: feat/retrofit-watch-050-loja
aprovacao: humano-2026-11-28
adr: docs/adr/0001-retrofit-lean-publicacao.md
ddd: aplicado
qa:
kaizen_log:
campaign: 20261125-loja-skills
lot: L2
---

# Missão — Retrofit de skills locais com ensaio antes do push autônomo

## Problema (Gemba)

Hoje, `why_manual` encaminha as skills locais para `kit-ou-lean`. A loja já tem pedido, triagem, worktree, selo, revisão, aprovação, registro e porta de publicação. A issue [j0ruge/skills#11](https://github.com/j0ruge/skills/issues/11) estende esse fluxo às skills de repos explicitamente listados. O problema da cópia em uso é independente da edição da skill. Se ela aponta para o checkout de desenvolvimento, segue a branch em que o dono está trabalhando. A spec de 25/11 documenta um caso em que a correção na `main` não chegaria ao usuário.

## Métrica

Em repos de fixture, um lote elegível percorre pedido → selo → revisão → porta. Antes do critério da v2, o gate aprovado deixa o lote `segurado` e o SHA do bare intacto até o `approve` do patch. Com o critério cumprido, o SHA publicado, o SHA do status `local/ci` e o HEAD do clone em uso coincidem. Um revert autônomo na loja ou em repo listado reinicia a janela. Os cinco casos do Review Focus têm prova de regressão. As suítes preservam a atribuição da 0.4.1 e os contratos do modo full.

## Resultado esperado

A `retrofit-watch` 0.5.0 reconhece o repo pelo `origin`, prepara um lote por skill e avança a cópia em uso com `--ff-only`. A `retrofit-skill` 0.12.0 registra a lição no CHANGELOG da skill local e respeita a aprovação manual quando aplicável. O checkout de desenvolvimento fica disponível ao dono durante todo o fluxo. A entrega da loja segue por PR do worker para `main`.

## Fora de escopo

- Setup e publicação reais nos repos privados, inscrição na config pessoal, medição do gate privado real, migração de estado, criação do clone real e troca dos links de Claude, Agents ou Hermes. Pertencem ao plano de adoção de cada repo privado.
- Autonomia do kit SDD, fila headless, Hermes, kits copiados de terceiros, repos de produto com deploy na `main`, skills fora da lista, pacotes do repo, tags e reescrita de histórico público.
- Alterar a política de autorização da porta pública da v1. A aprovação pública vinculada ao patch é um achado a registrar no TODO. A correção de atribuição pertence ao PR #13 de L1. L2 incorpora e testa seu resultado.

## Gate PLAN-AUTO

**Pré-condição de aprovação.** O worker confirma o PR #13 integrado em `j0ruge/skills:main`, atualiza a base de L2, comprova a presença da 0.4.1 e repete suas regressões. Confere o escopo atual da #11, as quatro linhas do checkpoint, o preflight e a delegação vigente. O SHA local de planejamento antecede essa integração.

| # | Critério | Status | Evidência |
|---|---|---|---|
| a | Grill sem perguntas abertas não endereçadas | ✅ | As duas escolhas recebidas estão abaixo. A adoção privada tem dono e fase próprios. |
| b | Kaizen e DDD cobertos no desenho | ✅ | K1–K8 e D1–D6 abaixo. |
| c | Autocontenção | ✅ | I1 identifica arquivos, fixture de origem, ambiente, contratos, casos, comando e resultado. |
| d | Checks vermelhos na base de aprovação | ✅ | No checkpoint materializado sobre `6329df5`, `--check` e `--red` retornaram rc 0 antes da aprovação. As quatro células deram `1`, `1`, `1`, `falhou`. |
| e | Versões | ✅ | Pedido do mantenedor fixa `retrofit-watch` 0.5.0 e `retrofit-skill` 0.12.0. `JIRA_ENABLED=false`. |
| f | ADR alocado | ✅ | A decisão proposta está vinculada em `docs/adr/0001-retrofit-lean-publicacao.md`. |

## Checklist kaizen (`kaizen-software`)

| # | Item | Status | Nota |
|---|---|---|---|
| K1 | Gemba | ✅ | Código, fixtures, config, revisões Git e células do checkpoint inspecionados. |
| K2 | Problema com métrica | ✅ | O SHA remoto, o registro do hook, o patch aprovado e o clone provam o efeito. |
| K3 | Desperdício | ✅ | Dez tarefas de origem agrupadas em quatro provas. Reuso de `StoreWorld`, `patch_id`, guardas e validadores. |
| K4 | Fatiamento | ✅ | Um commit de produto e um Check substantivo por incremento. |
| K5 | Check pelo artefato | ✅ | Os testes leem refs Git, arquivos, registro e chamadas externas capturadas. |
| K6 | Parada da linha | ✅ | Gate ausente ou vermelho segura o lote. Falha de regressão, de base ou de autorização para o worker. |
| K7 | Padronização | ✅ | Testes permanentes, referências dos dois plugins e contrato do revisor acompanham a mudança. |
| K8 | Registro | ✅ | I4 registra no `KAIZEN_LOG.md` a missão, as provas e a limitação da medição em fixture. |

## Checklist DDD (`ddd`) — condicional

| # | Decisão de domínio | Status | Invariante |
|---|---|---|---|
| D1 | Identidade da origem | ✅ | O slug normalizado identifica a entrada da lista. A origem efetiva distingue o destino Git e a pasta identifica a skill. |
| D2 | Unidade de trabalho | ✅ | Um lote reúne lições da mesma skill e origem. Colisão de nome produz retenção explícita. |
| D3 | Fronteira de escrita | ✅ | A edição pertence ao worktree do lote. A cópia em uso acompanha a `main`. |
| D4 | Autorização | ✅ | Aprovação privada vale para o patch revisto e apenas para motivos substituíveis. |
| D5 | Estado observado | ✅ | `segurado`, `publicado` e falha pós-push descrevem efeitos distintos. Uma falha de avanço preserva a evidência do push. |
| D6 | Contratos entre módulos | ✅ | Pedido, lição, retrofit, revisão e registro carregam a origem necessária. Leitura legada do fluxo full coberta por regressão. |

## Decisões do grill (não re-litigar)

1. Pergunta registrada pelo relay
   - question: A janela da v2 reinicia quando há um revert na loja ou em qualquer repo listado em lean\_auto. Se o histórico local de um desses repos estiver ilegível, como a porta deve tratar um lote de outro repo cujo clone está íntegro?&#10;&#10;A (recomendada) — Usar auto-dry enquanto a janela não puder ser comprovada. O lote passa pelo gate da fixture e fica pronto para aprovação manual do patch. Nenhum push ocorre sozinho.&#10;&#10;B — Segurar também a publicação manual desse lote até que todos os históricos possam ser lidos e a janela seja recalculada.
   - answer: (other: A (recomendada) — Usar auto-dry enquanto a janela não puder ser comprovada. O lote passa pelo gate da fixture e fica pronto para aprovação manual do patch. Nenhum push ocorre sozinho.)

2. Pergunta registrada pelo relay
   - question: No ensaio auto-dry, a spec de 25/11 manda rodar \`npm run gate\`. O plano de construção manda executar o pre-push com o mesmo SHA e a mesma referência de destino que o Git entregaria no push. Se o hook fizer verificações adicionais, os resultados podem divergir. Qual comportamento deve valer na issue #11?&#10;&#10;A (recomendada) — Executar o pre-push configurado no worktree da fixture, com os argumentos e a entrada que o Git entregaria, sem fazer push. Assim o dono vê o resultado do gate completo antes de aprovar o patch. No push aprovado, o Git executa o hook novamente.&#10;&#10;B — Conferir que o pre-push existe e é executável, mas rodar apenas \`npm run gate\` no ensaio. As verificações adicionais do hook rodam pela primeira vez no push aprovado e podem recusá-lo.
   - answer: (other: A (recomendada) — Executar o pre-push configurado no worktree da fixture, com os argumentos e a entrada que o Git entregaria, sem fazer push. Assim o dono vê o resultado do gate completo antes de aprovar o patch. No push aprovado, o Git executa o hook novamente.)

## Pendências para o humano

A adoção privada fica com o dono de cada repo. Antes de repontar links, ele decide o destino de arquivos ignorados ou não rastreados, transfere o estado para um local estável, verifica contagem e SHA-256 e só então autoriza a mudança. Nenhuma dessas operações integra o checkpoint da loja. O worker apresenta as duas decisões do grill no PR de L2.
