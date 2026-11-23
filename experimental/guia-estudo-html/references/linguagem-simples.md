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
- **Medida:** a frase de ensino tem até 30 palavras (regra 2). O advérbio de enchimento não se mede na página: quem confere é a revisão de conteúdo (`qa.md`, seção 6), sem sensor. Esta regra não nasceu de um defeito medido.

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
- **Regra:** cada cor usada no código do diagrama, ou no estilo inline de uma figura em HTML, aparece na legenda, com o que ela marca. Cada tracejado também. Com uma cor só, a palavra "destaque" basta.
- **Medida:** o sensor `cor-sem-legenda.js` lê o código do diagrama sem rede. O `fill` de cada `classDef` usada, da `classDef default` e de cada `style` pede o nome da cor na legenda, em hex ou por nome (`red`). O `stroke` pede nome quando é a cor de uma seta (`linkStyle`) ou a única cor do estilo: sem `fill`, ou com `fill` branco ou `none`. Num nó com `fill` de cor, o `stroke` é a borda e a legenda do `fill` a cobre. O tracejado pede o termo "tracejad", venha ele de uma classe, de um `style`, de um `linkStyle` ou da seta `-.->`.
- **Fora do sensor:** figura em HTML ou SVG feito à mão, com cor inline (`style="fill:#e0006e"`), segue a mesma regra, mas nenhum sensor a lê. Quem confere é a revisão de conteúdo (`qa.md`, seção 6).

## 7. Todo número tem fonte e localização
- Todo número no corpo da aula, numa caixa, numa legenda ou num diagrama leva `span.n` e a fonte com a localização (`span.fonte`). A analogia que usa número inventado também leva a marca "exemplo inventado" (regra 8).
- Pré-teste e enunciado de quiz repetem números de um exemplo que já tem a fonte. Neles o `span.n` e a fonte não entram, e a opção certa leva a fonte no `data-explica` (regra 9).
- **Medida:** em cada caixa, `details`, figura ou parágrafo solto com `span.n`, procure um `span.fonte` no mesmo bloco. O pré-teste e os enunciados ficam de fora.
- **Defeito medido:** uma frase de síntese juntava quatro números de uma frase da fonte que quebra de página. A marca citou a página vizinha. O valor estava certo.
- **Regra:** para a frase que junta números, cite as duas páginas, ou a faixa.
- **Deslocamento de página:** quando a fonte é um PDF, a página do PDF não é a impressa. Confira o deslocamento em dois pontos distantes antes de usá-lo. O guia de origem achou "página do PDF menos 1".

## 8. O exemplo inventado vem marcado, e o porquê confere com a conta
- **Defeito medido (duas vezes):** um exemplo inventado repetia o valor de uma medida real, ao lado de outro resultado. A pessoa decorava o número visto por último. Depois da correção, a frase do porquê ainda atribuía o efeito inteiro a uma causa que respondia por parte dele.
- **Regra:** nenhum número inventado repete um número real no mesmo papel. A frase do porquê diz só o que a conta mostra.
- **Medida:** refaça a conta do exemplo, passo a passo, e compare cada número com o da frase.

## 9. O porquê da opção certa do quiz tem fonte
- **Defeito medido:** uma pergunta, entre vinte, tinha o porquê da certa sem seção e sem página. As outras dezenove tinham as duas.
- **Regra:** o `data-explica` da certa termina com a fonte e a localização.
- **Medida:** conte as opções certas. Todas têm a marca.

## 10. Simplificar tira qualificador: confira contra a fonte
- **Defeito medido:** três frases eram mais largas que a fonte. Duas trocavam a parte pelo todo, como "dois dos três métodos" que vira "os métodos". A terceira fazia do exemplo de um estudo uma regra geral. A conferência comparava números e ordem, e o alcance ficou sem conferir.
- **Regra:** depois de simplificar, compare o alcance da frase com a fonte citada: quantos casos, quais, em que condição. Frase que junta duas fontes se confere contra as duas.
- **Procura:** depois de corrigir uma frase, procure a mesma frase nas outras páginas. Uma resposta escrita só a partir da introdução deixou de fora um limite que a fonte declara em outra seção.

## 11. Quiz: opções com o mesmo tamanho, e a certa fora do topo
- **Defeito medido:** no curso-modelo, uma pergunta tinha opções de 4, 4 e 5 palavras, e a certa era a mais longa. Em outra, as três opções tinham 3 palavras, e a certa era a mais longa em caracteres.
- **Regra:** as opções de uma pergunta têm o mesmo número de palavras. A diferença de uma palavra passa, se a certa não for a mais longa. A certa nunca é a única mais longa, nem em palavras nem em caracteres. Ela muda de posição de pergunta para pergunta.
- **Medida:** conte palavras e caracteres das opções de cada pergunta, na ordem em que a página as mostra. Uma opção mais longa denuncia a certa.

## 12. O tempo que a aula promete bate com o tamanho dela
- **Defeito medido:** o índice prometia "de 10 a 15 minutos". Os cabeçalhos diziam 10, 15, 20 e 20. O volume de texto pedia perto do dobro. O plano de um dia passava de uma hora.
- **Regra:** declare a conta no índice. Leitura a 130 palavras por minuto (parâmetro `palavrasPorMinuto`), mais um minuto por "lembre sem olhar" e meio minuto por pergunta, arredondado para cima de cinco em cinco.
- **Medida:** o `data-minutos` do cabeçalho de cada aula é igual ao do índice e à estimativa do sensor. A skill não impõe limite de duração (`evidencia.md` 5.2). Ela só confere a consistência.
