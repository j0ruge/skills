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

## Contrato ilegível

Se nesta sessão um `Read` dentro de `{SKILL_DIR}` foi negado, inclusive o desta referência, o
agente também não vai ler o próprio contrato. Ele então revisa sem as passadas ou para pedindo uma
permissão que ninguém concede, e volta sem o marcador. Nesse caso, e só nele, os dois
prompts de lançamento (por arquivo e varredura) ganham uma linha no fim, e nada além dela:
`If Read is denied on {SKILL_DIR}, read those files with cat through Bash.`

Medido em fases REVIEW do `sdd run`:

- de 2026-10-19 a 2026-10-25, 94 de 176 agentes tiveram o `Read` negado; nas fases seguintes, com a
  pasta já liberada pelo kit, nenhum;
- com a linha, voltaram com `END_OF_FILE_REVIEW` 10 de 11 (2026-10-21) e 4 de 4 numa relançada
  (2026-10-24).

Ali a causa era do kit, que passou a liberar a pasta. A linha vale para qualquer sessão cujo `Read`
não alcança o cache de plugins.

## Teste de contrato numa revisão `full`

O `SKILL.md` só manda um arquivo TESTS a agente no foco de qualidade de teste (6.12). Numa revisão
`full`, então, nenhum agente lê os testes, e o 6.11, que vale sempre, não chega a eles. Quem fica
descoberto é o teste de contrato: ele lê pelo caminho arquivos do repositório (doc, config, script
lido como texto) e é o único sensor deles. O agente do módulo que ele importa revisa o módulo, e não
o teste.

Numa revisão `full`, cada TESTS mudado que lê arquivo do repositório pelo caminho vai a um agente,
no mesmo lote da fase B, com a categoria `TESTS (contract)`, o prompt de lançamento sem mudança e
até 3 arquivos por agente. Ache-os com
`grep -lE 'readFileSync|readFile\(|existsSync|readdirSync|glob'` sobre os TESTS mudados, num
script em bash: o zsh aborta o glob que não casa.

Esse grep só conhece JavaScript. Em teste Python, ou shell que embute Python, acrescente
`|open\(|read_text\(|safe_load`. O resultado é uma lista de candidatos, e não a lista final: o
padrão também casa a leitura de um arquivo temporário que o próprio teste criou. Fique com os que
leem um caminho do repositório (a role, o playbook, o `defaults`), e só esses vão a agente.

Medido em 2026-11-11 (codereview 2.27.36, revisão `full` de 62 arquivos de um monorepo TypeScript):

- a rodada 1 lançou 15 agentes por arquivo, e nenhum recebeu um dos 4 TESTS mudados;
- um deles era o contrato de rótulos de duas páginas de manual. Ele pulava calado, com
  `.filter(existsSync)`, a página que faltasse, e o piso de vacuidade só cobria a outra;
- o achado (MEDIUM, sensor cego) veio do agente do plano, que leu o teste para conferir a frase "o
  contrato cobre os dois arquivos". O agente do módulo que o teste importa leu 4 arquivos e não o
  citou;
- dos 4 TESTS, 3 leem arquivo pelo caminho, e o grep acima acha esses 3 e só eles: a regra custaria
  1 agente.

Medido em 2026-11-12 (codereview 2.27.38, revisão `full` de 78 arquivos de um repositório de
playbooks, com testes em shell e Python): dos 22 TESTS mudados, o grep de JavaScript achou 3 e o
grep estendido achou 13. Entre esses 13 estavam os que carregam as tasks de uma role com
`safe_load(open(…))` e conferem o texto delas, que nenhum agente por arquivo tinha recebido.

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
