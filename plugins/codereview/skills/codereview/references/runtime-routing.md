# Roteamento nativo e coleta dos resultados

Leia antes de delegar as fases B/B2 e ao receber cada resultado.

## Seleção do modelo

| Ambiente observado | Ferramenta nativa | `REVIEW_MODEL` |
|---|---|---|
| Codex com `collaboration.spawn_agent` | `spawn_agent` | `gpt-6.1-terra` |
| Claude Code com `Agent` | `Agent` | `sonnet` |

Uma escolha explícita do usuário prevalece. No Codex, use `fork_turns="none"`,
`model="gpt-6.1-terra"` e `reasoning_effort="medium"`; inclua o contrato completo
no prompt da skill. Lance até o limite de agentes ativos do ambiente; uma vaga
liberada recebe o próximo grupo. O modelo principal faz a fase C.

Confira os nomes aceitos na ferramenta disponível antes do lançamento. Se o
modelo escolhido não estiver disponível, informe a limitação e execute inline
com o modelo principal. Não abra outro CLI para contornar o roteamento. Não
omita `model` numa delegação para herdar silenciosamente o modelo principal.
Registre no Cost footprint o modelo usado, inclusive fallback e relançamentos.
Esta adaptação do fluxo não declara compatibilidade dos demais comandos do plugin.

## Coleta sem perda

Mantenha um registro por tarefa: `{id, model, base, head, files, raw_result,
complete, failure}`. Capture cada resposta integral antes de imprimir resumos.
Use o armazenamento em memória do orquestrador; a revisão continua sem escrever
arquivos no repositório. Cada tarefa tem sua própria resposta: não concatene
JSONs, mensagens ou blocos de agentes antes de validar sua origem.

Ao receber um resultado, confira:

1. O ID corresponde à tarefa, à base, ao HEAD congelado e aos arquivos enviados.
2. O transporte não indica truncamento, saída omitida ou limite excedido.
3. A mensagem final termina em `END_OF_FILE_REVIEW` ou
   `END_OF_DEAD_CODE_SWEEP`, conforme o contrato, e contém os contadores.

Um JSON válido ou um marcador encontrado dentro de um lote não prova que todas
as respostas chegaram inteiras. Se a leitura do lote foi cortada, recupere cada
resposta pelo seu ID com orçamento suficiente, guardando-a antes de mostrar
apenas metadados ao modelo principal. Confirme a quantidade de respostas contra
a quantidade de tarefas, sem confundir dois resultados fundidos com um só.

Se a recuperação integral não existir, relance somente a tarefa afetada, com a
mesma base e o mesmo HEAD. Conte a tentativa extra. Se o HEAD mudou, reporte o
escopo antigo como incompleto e inicie a revisão do novo delta separadamente.
Falha persistente fica como análise parcial, com os achados recuperados e o
motivo; não vira resultado limpo nem aprovação por ausência de achados.
