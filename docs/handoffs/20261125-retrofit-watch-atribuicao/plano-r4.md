# Plano do R4 — Preservar a evidência de atribuição até seu descarte seguro

**Objetivo.** Fechar os dois casos reproduzidos na [revisão r4](40-review-r4.md) e manter a correção 0.4.1 da issue [j0ruge/skills#12](https://github.com/j0ruge/skills/issues/12).

**Arquitetura.** Registrar separadamente a posição da mensagem, a situação de cada ID de chamada e a atribuição vigente. Todos os eventos da mesma mensagem consultam a mesma posição enquanto ela participa da decisão.

**Base e escopo.** `762f440`, branch `fix/retrofit-watch-atribuicao-mesma-mensagem`. Python, estado JSON por sessão, fixtures `StopTest` e validadores do kit. R4 é o único incremento pendente. Esta revisão do plano complementa o [plano original](01-plano.md) e preserva as decisões aprovadas.

**Aceite.** Em 27/11/2026, o mantenedor autorizou no Codex a implementação do R4 e uma rodada de revisão após a correção.

## O que os dois casos têm em comum

No Check de R4, os controles mantêm o alvo correto. As variantes falham tanto em leitura contínua quanto na retomada entre Stops. A mesma perda foi observada no JSON do Stop, logo após o `tool_result` com erro:

| Caso | Estado observado depois da falha | Evidência que precisa sobreviver |
|---|---|---|
| Mensagem A observada antes de B, com uma chamada B ainda pendente | `skill_message_order` passou de `[msg_a, msg_b]` para `[msg_b]` | A posição inicial de A enquanto B ainda disputa a atribuição. Uma nova chamada de A usa aquela posição. |
| Chamada A falha antes de outra chamada da mesma mensagem ser reconhecida | A chamada desapareceu de `skill_calls` e `failed_skill_calls` ficou vazio | O ID falho pertence à mensagem em que foi visto, ainda que ela não seja a ativa. Reutilizá-lo não prova a origem. |

O [checkpoint](checkpoint.md) reproduz a troca indevida de `graphify` por `codereview` no primeiro caso e a preservação indevida de `codereview` no segundo. O ramo de erro em `Scanner.entry` reúne as duas perdas em `retrofit_watch.py:700–709`.

Controle medido em `762f440`: 10, 100 e 1.000 falhas em mensagens distintas, com uma chamada anterior pendente. Só essa chamada ficou no mapa e seu metadado ainda atribuiu a retro a `graphify`. O JSON mediu 331 bytes no início e 332, 333 e 334 nos três lotes. O número de vínculos, e não o tamanho exato do JSON com offset, é o critério a preservar.

## Abordagem escolhida

Um ajuste apenas no ramo de erro resolveria as duas entradas do Check, mas ainda deixaria o descarte de evidência espalhado por `_watch`, `_skill_origin` e `skill_path`. Reconstituir a ordem relendo o transcript tem mais custo e muda o contrato de leitura incremental. O R4 mantém a leitura pelo offset e explicita o ciclo de vida da correlação que o hook já persiste.

### O que o estado precisa representar

| Dado | Regra |
|---|---|
| Posição da mensagem | Atribuir uma posição crescente ao primeiro `Skill` identificado da mensagem na janela vigente. Não alterar a posição se uma chamada falhar ou for consumida. `message.id` é opaco e serve só para igualdade. |
| Chamada identificada | Associar o par `message.id` e `tool_use.id` a um estado: pendente, consumido, falho ou ambíguo. Sucesso em `tool_result` deixa o vínculo disponível para o metadado. Erro muda o estado para falho, sem permitir que seu metadado confirme a origem. Consumido, falho e ambíguo são evidência contra reuso, nunca vínculos válidos. |
| Origem da atribuição | Preservar o par da carga que atribuiu o trabalho. Só uma origem comprovada pode aplicar a exceção de mesma mensagem. Comparar com a posição da última carga reconhecida antes de aceitar metadados atrasados. |
| Metadado | `sourceToolUseID` precisa identificar uma única chamada ainda válida. Se houver IDs iguais entre registros retidos, ausência, tipo inválido ou vínculo expirado, manter o tratamento conservador existente. Manter distintos o caso da própria carga excluída pelo caminho e o de uma carga externa separada na mesma mensagem. |

Reconhecimento pelo nome, identidade pelo caminho, comandos de barra e contagem de trabalho continuam nos pontos atuais do scanner. A ordenação é usada apenas quando a origem é comprovada. Resultado de erro mantém a contagem de atrito, sem representar por si uma nova carga.

### Descarte e recuperação

1. **Manter enquanto pode afetar uma decisão.** Conservar a mensagem reconhecida vigente, as mensagens com vínculos pendentes e a posição de uma mensagem vazia mais antiga enquanto existir uma mensagem posterior pendente que ainda possa estabelecer precedência. Reter os IDs falhos e consumidos das mensagens conservadas. Uma sequência de erros isolados em mensagens novas não deve acumular registros só porque existe uma pendência mais antiga.
2. **Aposentar ao fechar a disputa.** Confirmar uma mensagem posterior retira posições e vínculos anteriores. Os metadados atrasados de vínculos aposentados seguem a política sem prova de origem. Quando uma tentativa falha e sua mensagem não é ativa, não contém pendência e não há disputa posterior em curso, descartar seu registro. O R4 cobre as mensagens ainda relevantes nessa janela. O reuso do mesmo ID entre mensagens já aposentadas continua na pendência separada do `TODO.md`.
3. **Limitar o histórico retido.** Proposta para manter o hook leve: após descartar o que já pode ser aposentado, limitar a correlação a 64 mensagens e 1.024 IDs retidos por sessão. Se a janela exceder qualquer limite, registrar no estado da sessão que a correlação perdeu precisão e aplicar a política conservadora até abrir outra sessão. Preservar contadores e o comportamento das invocações explícitas. Evitar que uma expulsão parcial transforme um ID esquecido em prova de origem. Os limites são internos ao scanner, sem nova opção de configuração.
4. **Retomar sem inventar dados.** Preservar `offset`, `skills`, `current`, histórico e contadores do estado 0.4.0. Para estados intermediários que já trazem mensagens e IDs, aproveitar a ordem registrada e reconstruir apenas o que as chaves existentes comprovam. Um ID ambíguo sem mensagem conhecida pode negar correlação, sem confirmar uma carga. Manter o caminho rápido do Stop capaz de tratar um erro quando a chamada correspondente veio em outro delta.

## R4 — Testes, correção e evidência

**Arquivos.** `plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py`, `plugins/retrofit-watch/skills/retrofit-watch/tests/test_retrofit_watch.py` e handoffs da missão. Sincronizar apenas as referências de comportamento da 0.4.1 que ficarem imprecisas, mantendo o catálogo e a versão atuais.

- [ ] Repetir o Red do R4 com o Check existente. Acrescentar os dois casos à suíte de Stop com estado em disco. Cobrir leitura contínua e cortes logo antes do erro, logo depois dele e entre as confirmações concorrentes. No teste de ordem, usar IDs opacos que não reflitam a ordem lexical. No teste de reuso, um ID novo preserva `codereview`, e a repetição do ID falho encerra a atribuição.
- [ ] Fixar os controles de descarte antes da correção. Repetir as 1.000 falhas em mensagens distintas em duas condições: sem pendências e com uma chamada antiga ainda pendente. Exigir que o número de registros retidos não cresça com essas tentativas e que a chamada antiga continue consumível. Cobrir a saturação com limites menores injetados no teste, verificando a retomada conservadora após reler o JSON. Usar duas mensagens ainda retidas que anunciam o mesmo ID para provar que o metadado não escolhe um vínculo por acaso.
- [ ] Atualizar o ciclo de vida em `State`, na associação de `Skill`, no tratamento de `is_error`, no consumo pelo caminho e na decisão de atribuição. Usar uma única regra de descarte compartilhada entre esses eventos. Manter os controles de IDs já consumidos, slash explícito, metadado antigo e offsets da 0.4.0.
- [ ] Exigir o Green do R4 nas quatro linhas abaixo. Repetir I1, F1, R1, R2 e R3 com os comandos registrados no checkpoint e comparar os resultados antes de fechar R4. Rodar a suíte da `retrofit-watch`, o teste de terminal de F1 e o preflight Codex. Rodar no host as três provas nativas de distribuição. Corrigir a frase do handoff que descrevia qualquer pendência como evidência de precedência. Registrar o hash real de R4 e o resultado no handoff.

```text
ordem_ultimo_vinculo_continua=graphify,graphify
ordem_ultimo_vinculo_retomada=graphify,graphify
reuso_pre_ativacao_continua=codereview,silêncio
reuso_pre_ativacao_retomada=codereview,silêncio
```

No Red de `762f440`, os dois pares de ordem imprimiram `graphify,codereview` e os dois pares de reuso imprimiram `codereview,codereview`. O mesmo resultado foi confirmado em `02e0331` pelo `check-checkpoint.sh --red` antes da retomada. As condições de merge estão na [missão](00-missao.md#campanha-e-delegação).
