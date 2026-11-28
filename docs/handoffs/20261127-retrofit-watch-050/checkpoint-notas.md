# Notas de execução — Skills locais da lista

> **Append-only.** Uma linha por evento; nunca reescreva o arquivo, nunca o releia inteiro.
>
> Este arquivo nasceu em `20260904-a-dieta-de-contexto`, separado do `checkpoint.md` por medição:
> as notas eram **69% daquele arquivo** (67 166 B de 97 865 B em `20260901-o-revisor-so-acha`), e
> aquele arquivo era **44,7% de tudo que a missão releu** — 160 leituras, 1 114 571 B. Enquanto
> tabela e notas dividiam o arquivo havia um piso mecânico: em sessão headless o `Edit` exige um
> `Read` prévio, então toda sessão que atualizasse a tabela pagava o arquivo inteiro. Separadas,
> escrever nota é `>>` e custa **zero leitura**.
>
> O prompt de boot **inlina as últimas 10 notas** (`BOOT_NOTES_TAIL` no `bin/sdd`) e manda
> explicitamente **não abrir este arquivo**. Se você precisa de uma nota mais antiga, ela é
> história — e história se lê no `git log`, não no boot de toda sessão.

## Notas de execução

> Uma linha por evento relevante: bloqueio, decisão tomada, desvio do plano com justificativa.
> É o que a próxima sessão lê para não repetir um erro que já custou caro.


> **Toda vez que um humano precisou entrar na linha** — um `sdd retry`, um conserto à mão, um
> `BLOCKED` assumido — sai uma linha com o marcador `intervention:`. É a **narrativa** do que o
> humano fez. O **número** de intervenções o `sdd autonomy --by-mission` lê do ledger, em
> `launch(es)` (`run_id` distintos — cada `sdd run`/`sdd retry`), e imprime estas notas ao lado
> como `intervention note(s)`. Medido em 2026-08-28: a missão de três lançamentos tinha zero
> notas — o contador não pode depender de alguém lembrar de escrever; a narrativa, sim, e é a
> única fonte que diz o que o humano *fez*.
>
> ⚠️ O marcador é **inglês e minúsculo**, como `pending`/`done`/`blocked`: é contrato, não prosa.
> O texto depois dos dois-pontos vai no idioma do `OUTPUT_LANG`, como o resto deste arquivo.
> Só conta quando abre a linha — `intervention` no meio de uma frase é prosa e não é contado.
>
> Desde 2026-09-03 o **runner escreve a linha sozinho** quando é ele quem recebe a mão do humano —
> `sdd run --phase X`, `sdd retry`, `--budget-override` — **e só na volta que abre sessão** (uma
> volta parada antes dela, por PLAN, carimbo, teto ou no-work, não grava nota), e a commita sozinha,
> na hora, para a árvore chegar limpa ao gate da fase seguinte. A linha escrita à mão continua valendo para o que
> o runner não vê: conserto manual, `BLOCKED` assumido. Fase feita à mão tem comando:
> `sdd note-manual <missão> <FASE>` escreve a nota e a linha `manual` do ledger, que não gradua
> nada — escrita só aqui, a fase não existe para o ledger. `sdd approve` não
> escreve nenhuma: aprovar o plano é o gate humano desenhado, não uma entrada na linha. A nota
> diz o que o runner **sabe** ("forçada pela CLI"), nunca quem estava na CLI: outro agente com
> shell entra pela mesma porta, e o runner não distingue — medido em 2026-09-03.
>
> O exemplo abaixo mora **dentro** desta citação de propósito: o `>` quebra o casamento com
> `^[[:space:]]*-`, e sem ele o exemplo era contado verbatim — todo checkpoint recém-instanciado
> nascia devendo uma intervenção fantasma ao instrumento que mede autonomia. Copie a forma para
> fora da citação ao registrar uma intervenção de verdade.
>
> - intervention: <o que o humano teve de fazer> — <fase> — <custo, se houver>


- 2026-11-28 03:32 · `I1` · TDD em `d929f44`: o Red reproduziu `kit-ou-lean` na primeira guarda elegível e a ausência da janela v2. O Check passou com 12 testes em `TMPDIR=/tmp`, sem `GIT_DIR` e `GIT_WORK_TREE`. O controle íntegro sob grupo isolado, 25 s e 512 MiB por processo passou. As 22 mutações em cópias temporárias falharam nas asserções-alvo.
- 2026-11-28 03:32 · `I1` · `TEST_CMD` passou com o mesmo ambiente isolado: 154 testes da loja (3 pulados pela configuração), 144 do Stop, adaptadores, catálogo e versões válidos. Os 60 testes direcionados de I1, formatos e critério público passaram. A suíte da retrofit-skill passou com 9 testes. O TODO ficou com 58 âncoras válidas.
- 2026-11-28 03:32 · `I1` · A suíte completa da watch (499 testes) ficou vermelha. `/var/tmp` é somente leitura e o `/tmp/.git` vazio faz a colheita de fixture recusar `/tmp`. O controle que ignorou o marcador só no processo de teste deixou 7 falhas e 2 erros, todos reproduzidos em `6d72029`. A segunda skill full ausente no estado já falhava na base sem esse controle e foi registrada no TODO.
- 2026-11-28 03:32 · `I1` · kit: o ambiente do EXEC exportou `GIT_DIR` e `GIT_WORK_TREE` da cópia privada. O primeiro `TEST_CMD` redirecionou operações das fixtures para essa cópia. Removi apenas a ref `base` e a sequência que a rodada criou, conferindo o reflog e a igualdade da árvore com `6d72029`. Repetir as suítes com as variáveis de localização desarmadas. O Check aprovado com `/var/tmp` permanece intacto para o runner externo.
