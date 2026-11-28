# Atribuição de trabalho no Stop da retrofit-watch

A partir da 0.4.1, carregar uma skill externa junto da monitorada na mesma
mensagem do assistente mantém o trabalho seguinte atribuído à monitorada quando
o hook consegue comprovar o vínculo. Isso vale também quando a chamada `Skill`
e o metadado com o diretório chegam em Stops diferentes. O patch se aplica ao
hook Claude Code da loja, não à adaptação local para Codex.

## Quando a atribuição muda

O hook usa `message.id` para reconhecer a mensagem e o ID da chamada para ligar
o metadado à carga por `sourceToolUseID`. Estar no mesmo turno ou perto no
transcript não basta. A classificação pelo diretório também pode excluir a
própria carga que o hook reconheceu primeiro pelo nome.

| O que o Stop reconhece | Efeito no trabalho posterior |
|---|---|
| Uma carga externa distinta e uma monitorada na mesma mensagem, com vínculo confiável | Mantém a monitorada. |
| Uma carga externa posterior ou sem prova de que veio da mesma mensagem | Encerra a atribuição. O trabalho já creditado permanece registrado. |
| Resultado de erro ligado sem ambiguidade à chamada que abriu a atribuição ativa | Encerra a atribuição sem apagar os outros vínculos pendentes. Não exige `message.id`. Um ID disputado não encerra a atribuição. |
| Metadado externo com ID comprovadamente aposentado por uma mensagem posterior | Não altera a atribuição. ID desconhecido ou fora da janela mantém o tratamento conservador. |
| Metadado atrasado da monitorada sem vínculo, depois do encerramento | Não reabre a atribuição. Uma carga nova com vínculo ou um slash explícito para a própria skill pode iniciá-la. |

Chamadas pendentes mantêm a ordem das mensagens mesmo se os metadados chegarem
fora de ordem. Dentro da janela retida, IDs falhos, consumidos ou ambíguos não
servem como prova para outra carga. Ao exceder 64 mensagens ou 1.024 IDs
retidos, o hook deixa de correlacionar mensagens nessa sessão. Isso não zera
contadores nem impede uma carga explícita. O ID direto da nova carga ainda pode
ligar seu próprio erro ao crédito aberto, sem comprovar que duas cargas vieram
da mesma mensagem. Na transição, o hook guarda até 2.049 IDs ainda retidos,
incluindo o que acionou o limite. IDs já descartados não voltam. Outro
registro guarda os primeiros 1.024 IDs distintos observados após o
limite. Reutilizar um ID de qualquer registro impede o vínculo direto.
Repetir o ID da carga ativa também revoga seu vínculo. Quando o registro de
chamadas novas se esgota, novos IDs deixam de provar erro próprio. Nenhum
desses registros valida metadados. Um registro opcional salvo com tipo
inválido volta vazio, sem zerar o offset, a atribuição ou os contadores.
O hook guarda à parte até 1.024 IDs aposentados dentro da janela.
Só entram nessa lista IDs com donos conhecidos e comprovadamente antigos. Ao
reaparecer numa chamada nova, um ID deixa de provar que o metadado é antigo.
Uma tentativa irrelevante não descarta o slash explícito enquanto aguarda o
caminho da skill. Uma carga externa que encerra a atribuição expira o slash
se a chamada externa for comprovadamente posterior. Um slash digitado depois
da chamada pode sobreviver ao metadado atrasado.

## Retomada da 0.4.0

O primeiro Stop que encontra estado legado com offset salvo tenta recuperar a
correlação lendo o trecho anterior a esse offset, linha por linha. Essa leitura
não reconta trabalho ou atrito, não gera pedidos de retro e não substitui a
atribuição ativa já salva. Quando o prefixo confirma o estado, o hook pode
recuperar também a origem ativa e um slash pendente.

Se a origem gravada tiver formato inválido, o Stop descarta essa origem, preserva
a atribuição e os contadores e continua a partir do offset salvo.

Se o prefixo não puder ser reconstruído, por exemplo porque um registro passa
de 2 MiB, nenhum vínculo parcial é importado. O Stop processa o trecho novo
a partir do offset salvo. Sem atribuição ativa, o metadado atrasado sem
vínculo continua sem abrir uma atribuição. A atribuição já ativa permanece
salva, e cargas novas com vínculo ou slash explícito continuam funcionando.

Os critérios de elegibilidade, os modos de retro e a fila não mudaram.
Veja as [notas da versão](../../plugins/retrofit-watch/CHANGELOG.md#041--2026-11-25)
e os [Checks de I1, F1 e R12](../handoffs/20261125-retrofit-watch-atribuicao/checkpoint.md).
