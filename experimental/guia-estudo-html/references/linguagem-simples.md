# Linguagem simples e conteúdo

Estas regras se conferem na página. Cada uma leva a medida que a originou: a condição que provou o defeito e o que resolveu. O assunto do guia de origem não entra aqui.

## 1. Um termo novo por vez, explicado na primeira menção
- **Defeito medido:** uma frase de abertura usava um termo que nenhuma aula definia antes. Outros apareciam só numa opção de quiz ou num diagrama, antes da caixa que os define.
- **Regra:** leia a página na ordem em que a pessoa lê. Todo termo tem definição antes do primeiro uso, inclusive em título, diagrama e opção de quiz.
- **Medida:** o termo tem uma glosa curta no primeiro uso e uma caixa `termo` (definição, exemplo, contraexemplo) e um verbete no glossário com o mesmo `id`.

## 2. Uma ideia por seção
- **Defeito medido:** frases curtas, mas seções com duas ideias. Um parágrafo apresentava dois termos novos. A pessoa cansada saía com a segunda e perdia a primeira.
- **Regra:** a seção que pede dois títulos vira duas seções. O parágrafo com dois termos vira dois parágrafos, um termo em cada. A lista de três termos vira uma tabela com a coluna "o que decide", uma linha por termo.
- **Medida:** frase de ensino com até 30 palavras. Um título, uma ideia.

## 3. Frases curtas, voz ativa
- Uma ideia por frase. Quem age aparece no sujeito. Sem advérbio de enchimento.

## 4. O texto diz tudo o que o diagrama diz
- **Defeito medido:** sem rede, o diagrama não desenha e vira código. Em quatro de dezessete diagramas, uma parte só existia no desenho. Três legendas falavam de uma cor que, sem o desenho, não existia.
- **Regra:** o texto vizinho substitui o diagrama. Toda lista, divisão ou sequência do desenho aparece também em texto. A legenda nomeia o que a cor marca, não só a cor.
- **Medida:** abra a página sem rede. Cada informação do diagrama se acha no texto.

## 5. Um termo com dois sentidos ganha uma caixa "Não confunda"
- **Defeito medido (duas vezes):** a mesma palavra tinha um sentido numa aula e outro numa aula seguinte, sem aviso. Numa delas, uma linha usava o termo antes da linha que o define.
- **Regra:** use o nome completo da medida, não o nome curto da coluna da tabela. Na primeira vez que o segundo sentido aparece, ponha uma caixa `nao-confunda` que aponta o primeiro, diz como falar de cada um e liga ao verbete do glossário.
- **Medida:** procure cada termo do glossário nas aulas. Dois sentidos exigem a caixa.

## 6. Toda cor e todo tracejado têm legenda
- **Defeito medido:** seis diagramas usavam cor ou linha tracejada sem explicar. O sensor achou mais oito, ao todo catorze figuras.
- **Regra:** cada cor usada no código do diagrama aparece na legenda, com o que ela marca. Cada tracejado também. Com uma cor só, a palavra "destaque" basta.
- **Medida:** o sensor lê o código do diagrama sem rede. Cada `classDef` usada pede o nome da cor na legenda, e o tracejado pede o termo "tracejad".

## 7. Todo número tem fonte e localização
- Todo número leva `span.n` e a fonte com a localização (`span.fonte`).
- **Defeito medido:** uma frase de síntese juntava quatro números de uma frase da fonte que quebra de página. A marca citou a página vizinha. O valor estava certo.
- **Regra:** para a frase que junta números, cite as duas páginas, ou a faixa.
- **Deslocamento de página:** quando a fonte é um PDF, a página do PDF não é a impressa. Confira o deslocamento em dois pontos distantes antes de usá-lo. O guia de origem achou "página do PDF menos 1".

## 8. O exemplo inventado vem marcado, e o porquê confere com a conta
- **Defeito medido (duas vezes):** um exemplo inventado repetia o valor de uma medida real, ao lado de outro resultado. A pessoa decorava o número visto por último. Depois da correção, a frase do porquê sobrou da tabela antiga e atribuía o efeito inteiro a uma causa que respondia por parte dele.
- **Regra:** nenhum número inventado repete um número real no mesmo papel. A frase do porquê diz só o que a conta mostra.
- **Medida:** refaça a conta do exemplo, passo a passo, e compare cada número com o da frase.

## 9. O porquê da opção certa do quiz tem fonte
- **Defeito medido:** uma pergunta, entre vinte, tinha o porquê da certa sem seção e sem página. As outras dezenove tinham as duas.
- **Regra:** o `data-explica` da certa termina com a fonte e a localização.
- **Medida:** conte as opções certas. Todas têm a marca.

## 10. Simplificar tira qualificador: confira contra a fonte
- **Defeito medido:** três frases de fala eram mais largas que a fonte. "Dois modelos" virou "a origem". "Oito das nove de classe" virou "as discordâncias". O exemplo de um estudo virou regra geral. A conferência comparava números e ordem, não o alcance.
- **Regra:** depois de simplificar, compare o alcance da frase com a fonte citada: quantos casos, quais, em que condição. Frase que junta duas fontes se confere contra as duas.
- **Procura:** depois de corrigir uma frase, procure a mesma frase nas outras páginas. Uma resposta escrita só a partir da introdução deixou de fora um limite que a fonte declara em outra seção.

## 11. Quiz: opções com o mesmo número de palavras
- As três ou quatro opções de uma pergunta têm o mesmo número de palavras. A certa muda de posição de pergunta para pergunta.
- Uma opção mais longa denuncia a certa.

## 12. O tempo que a aula promete bate com o tamanho dela
- **Defeito medido:** o índice prometia "de 10 a 15 minutos". Os cabeçalhos diziam 10, 15, 20 e 20. O volume de texto pedia perto do dobro. O plano de um dia passava de uma hora.
- **Regra:** declare a conta no índice. Leitura a 130 palavras por minuto (parâmetro `palavrasPorMinuto`), mais um minuto por "lembre sem olhar" e meio minuto por pergunta, arredondado para cima de cinco em cinco.
- **Medida:** o `data-minutos` do cabeçalho de cada aula é igual ao do índice e à estimativa do sensor. A skill não impõe limite de duração (`evidencia.md` 5.2). Ela só confere a consistência.
