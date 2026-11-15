# codereview: nota escrita para prosa e rodada de verificação

**Data:** 2026-11-15 · **Estado do desenho:** `draft` · **Implementação:** `not_started`

## Por quê

Levar a linha **Documentation** a A depois de um conserto de docs custa hoje várias rodadas, e
quase nenhum achado dessas rodadas é sobre o código. Cada conserto escreve prosa nova, e a rodada
seguinte manda agentes novos lerem os arquivos inteiros de novo.

Medido em 2026-11-15 (um motor de regras .NET, PR #30), depois que o pipeline do projeto já tinha
fechado a revisão dele:

| Rodada | Intervalo | Agentes | Achados | Documentation |
|---|---|---|---|---|
| r3 | 32 arquivos (13 só comentário, 19 docs), +549/−82 | 8 | 14 LOW | B |
| r4 | 13 arquivos, +37/−31 | 4 | 1 MEDIUM, 6 LOW | B |
| r5 | 7 arquivos, +15/−12 | 3 | 1 MEDIUM, 5 LOW | B |
| r6 | 4 arquivos | 1 | 2 LOW | A |

De onde vieram os achados:

1. **Conserto de uma frase que deixou o trecho incoerente.** Uma célula de tabela teve achado nas
   quatro rodadas. O MEDIUM da r5 nasceu do conserto da r4: a última frase de um bullet foi
   trocada, e a primeira seguia dizendo o contrário. Os dois LOW da r6 caíram em texto escrito
   pelo conserto da r5.
2. **Leitura nova do arquivo inteiro a cada rodada.** O MEDIUM da r4 estava numa linha que o
   agente da r3 leu, no mesmo arquivo, e não acusou. Cada rodada é uma amostra nova de um leitor
   imperfeito sobre um doc de centenas de linhas, então sempre aparece algo.
3. **A nota não tem critério escrito para prosa.** A escala diz "A: no máximo itens MEDIUM/LOW
   menores" (`references/report-template.md`, *Grading Scale*). Quem decide o que é "menor" é a
   sessão que monta o relatório. Na r3, 14 LOW deram B; na r6, 2 LOW deram A.
4. **Custo fixo por agente.** Cada agente lê `per-file-agent.md` e `detection-passes.md` (69 KB)
   antes do arquivo. Medido em 2026-11-01 (o mesmo projeto, PR #22): de 80 a 150 mil tokens por
   agente só de contrato e arquivo.

As seções *Docs this session wrote* e *Re-review rounds* do `references/configuration.md` já
somam 43 regras escritas (14 e 29, contadas em 2026-11-15 na 2.28.5), várias delas nascidas deste
mesmo problema, e as rodadas continuam. Por isso este
desenho muda a forma da rodada, e não acrescenta mais uma regra para a sessão lembrar.

## O que se quer

**Objetivos**

- G1. A letra da linha Documentation sai de um critério escrito: duas sessões diferentes dão a
  mesma letra para a mesma lista de achados.
- G2. A rodada depois de um conserto que só mexeu em prosa confere o conserto, e não relê os
  arquivos inteiros. Custa um agente pequeno, que não carrega os passes de detecção de código.
- G3. A contradição que um conserto cria dentro do próprio trecho é achada na rodada desse
  conserto porque o trecho inteiro está no escopo, e não por sorte da leitura.

**Fora do escopo**

- Rodada depois de conserto que mexe em código: continua como hoje (agente por arquivo e varredura).
- A primeira rodada sobre um doc: continua lendo o arquivo inteiro. Só ganha a marca de tipo (abaixo).
- O kit de pipeline e as regras do projeto revisado: são dois desenhos seguintes, separados.
- Aplicar consertos: a skill continua só de leitura.

**O que seria fracasso mesmo funcionando**

- Um A que esconde uma frase que afirma um comportamento falso do sistema.
- Um verificador que só confirma o que o conserto diz que fez.
- O `configuration.md` crescer mais uma página de regras para a sessão lembrar.

## Restrições

- O repositório é público: nenhum nome de projeto, empresa ou pessoa nos arquivos nem nos commits
  (`scripts/check-private-names.py`). Datas, números de PR e hashes ficam.
- Commits sem `Co-Authored-By` e sem "Generated with" (`CLAUDE.md`, *Git*).
- A regra *The agents never see the earlier reports* continua valendo: o verificador não recebe
  os achados anteriores.
- A regra do projeto medido continua atendida: a última rodada é feita por agente revisor e
  termina no head que vai para o PR.
- O contrato do verificador mora num arquivo próprio em `references/`, lido só por ele. O
  `SKILL.md` e o `configuration.md` ganham só o roteamento para ele.
- Entrega pelo fluxo de release do repositório: versão, `CHANGELOG.md`, `marketplace.json`,
  `README.md`, distribuição Codex, `scripts/validate-versions.py`.

## Caminhos considerados

- **A. Mais regras escritas** (consertar o trecho inteiro, estado do PR num lugar só, e assim por
  diante). Barato, mas depende de a sessão lembrar, e as 43 regras que já existem mostram que isso
  não segura as rodadas.
- **B. Mudar a forma da rodada de prosa** (este desenho): critério escrito para a nota e rodada de
  verificação com escopo calculado. **Escolhido pelo dono em 2026-11-15**, por atacar as quatro
  causas e valer para todo repositório que usa a skill.
- **C. Aceitar B na prosa**, como o kit de pipeline do projeto medido já faz. Custo zero, mas o
  dono quer A na Documentation.

Dentro do B, a primeira ideia era o verificador receber os achados anteriores e dizer se cada um
fechou. Foi descartada: ele passaria a confirmar em vez de revisar. Conferir se um achado fechou
passa a ser um passo novo e mecânico da Fase C (seção 3). Hoje a Fase C só lê o diff sobre as
linhas dos achados novos, para pegar pedido de desfazer o conserto.

## O desenho

### 1. Tipo do achado de prosa

Todo achado que entra na linha Documentation ganha um tipo, venha de um agente ou do passo 7 da
própria sessão (que é quem lê o doc que a sessão não escreveu). Entram nessa linha os achados do
6.5.1 e do 6.5.2 e os de legibilidade sobre comentário; o 6.5.3 (contrato em teste) fica na linha
de testes, sem tipo.

- **`behavior`**: a frase afirma um comportamento, valor, estado ou garantia do sistema que o
  código ou a evidência contradiz, e o achado cita o `arquivo:linha` que contradiz. Também é
  `behavior` a afirmação que o doc dá como medida ou como ausência sem a evidência que *Docs this
  session wrote* exige, e o achado nomeia a evidência que falta. Um comando dentro do doc que
  falha ao rodar é `behavior`.
- **`form`**: a frase é verdadeira, mas está mal escrita, incompleta ou aponta para o lugar menos
  exato. Exemplos: sujeito faltando, ponteiro para um arquivo que existe mas não é onde o item
  mora, lista de exemplos que parece completa, contagem redigida de modo ambíguo, docstring que
  falta com severidade LOW.

Na Fase C, um `behavior` sem a citação do que o contradiz, ou sem o nome da evidência que falta,
vira `form`. A severidade continua vindo
das regras do 6.5; o tipo não a muda.

### 2. Critério da linha Documentation

Substitui, só para essa linha, a leitura livre da escala:

| Letra | Condição |
|---|---|
| A | nenhum CRITICAL, HIGH ou MEDIUM de documentação, e nenhum achado `behavior` |
| B | algum MEDIUM de documentação, ou algum LOW `behavior` |
| C ou pior | algum HIGH ou CRITICAL de documentação, pela escala geral |

Achado `form` de severidade LOW não baixa a letra e não pede rodada. Ele vai para uma lista
"Adiados (forma)" nas Recommended Actions. A linha Overall segue a mesma regra: LOW `form` adiado
não a baixa. A série de rodadas termina na primeira rodada sem MEDIUM ou pior e sem `behavior`;
hoje ela só termina na rodada que não acha nada (`SKILL.md`, *Re-review the fix, not the branch*).

Achado `pre-existing` (linha mais velha que a branch) passa a ficar fora da letra também. Hoje ele
só fica fora da regra de parada. Continua listado, e o usuário decide onde ele vai.

Conferência contra o caso medido: r3 tinha 3 LOW `behavior`, e daria B; r4 e r5 tinham 1 MEDIUM
cada, e dariam B; r6 tinha 2 LOW `form` (um ponteiro e uma frase sem sujeito), e daria A. As
letras são as mesmas que a sessão deu, agora por critério.

### 3. Rodada de verificação

**Quando vale.** Numa re-rodada (`base=<head revisado>`), para todo arquivo do intervalo que é
DOCS ou `DOC_ONLY` (CODE cujo diff só muda comentário). O `report-template.md` define o
`DOC_ONLY`, mas hoje ele só é decidido na Fase C, para a tabela de cobertura; para rotear, passa a
ser calculado na Fase A, pelo mesmo script do escopo. Um arquivo com linha de código mudada segue
o fluxo de hoje. Num intervalo misto, cada arquivo vai pelo seu caminho.

A rodada de verificação exige a lista dos achados abertos da rodada anterior (número,
`arquivo:linha`, tipo e a afirmação), da conversa ou de um arquivo que a sessão indica. Sem essa
lista, como numa sessão nova sem o relatório, a re-rodada é a de hoje.

**Escopo calculado por script.** Um script novo em `scripts/` recebe o intervalo e imprime, para
cada hunk, a **unidade** que o contém: em Markdown, o parágrafo, o item de lista inteiro (com as
linhas de continuação) ou a linha da tabela; em código, o bloco de comentário inteiro. Imprime
também os identificadores entre crases das linhas `+`. O escopo do verificador é essa saída, e não
julgamento da sessão.

**O que o verificador faz.** Um agente (mais de um só quando as unidades passam de um teto de
tamanho que o construtor define e mede) lê um contrato curto, só dele, e para cada unidade:

1. lê a unidade inteira no head e confere se alguma frase contradiz outra da mesma unidade;
2. confere cada afirmação das linhas `+` contra o código ou a evidência, pelo passe 6.5;
3. procura, nos docs do projeto, outras frases com os identificadores das linhas `+` que o texto
   novo passou a contradizer.

Ele não lê o resto do arquivo atrás de achado novo. O que notar fora do escopo entra numa lista
"fora do escopo", com teto, que vai para o tracker do projeto. Dessa lista, só o `form` fica fora
da nota: um `behavior` com citação, em linha que a branch escreveu, conta como qualquer outro. O passe de
segredos continua rodando na Fase A, como em toda rodada.

**Fase C.** Passo novo: para cada achado aberto da rodada anterior, a sessão lê o diff sobre as
linhas dele. Ele fecha quando o diff tocou a unidade dele e o verificador não deu `behavior` nela.
Achado cujas linhas o diff não tocou continua aberto e conta na nota, a menos que um veredito
escrito o tenha dispensado. A nota sai do critério da seção 2.

**Limite declarado.** Drift antigo fora das unidades editadas não é procurado por re-rodada. Ele é
trabalho da primeira rodada sobre o arquivo e, no projeto medido, de um sensor na fase de docs do
pipeline (desenho seguinte). O MEDIUM da r4 do caso medido estava nesse limite: a rodada de
verificação não o acharia.

### 4. Como saber que funcionou

Repetição, só de leitura, sobre os quatro intervalos do caso medido, três execuções por
intervalo. Os intervalos são `e195f52...b87d5c7` (r3), `b87d5c7...e652c6d` (r4),
`e652c6d...5e65896` (r5) e `5e65896...786b348` (r6), num repositório privado que o dono indica ao
construtor. Só números, datas e hashes vão para os arquivos deste repositório.

- no intervalo da r5 (o conserto da r4), o verificador acha a contradição do bullet, o MEDIUM
  que a r5 achou, nas três execuções;
- nos intervalos da r4 e da r6, ele acha os achados que caíam dentro das unidades editadas;
- os tokens de cada rodada de verificação ficam medidos. Os das rodadas originais não foram
  gravados, então a comparação é contra uma execução do modo de hoje sobre o intervalo da r4.

Estimativa, não medição: o caso medido fecharia em três rodadas com cerca de 10 agentes, contra
quatro rodadas e 16, e os agentes das re-rodadas seriam menores.

## Fica com o construtor

- O nome do modo, e se ele é escolhido sozinho pelo conteúdo do intervalo ou pedido por argumento.
- A linguagem do script de unidades e os testes dele (o repositório já tem testes em Python).
- O teto de tamanho por verificador e o teto da lista "fora do escopo", ambos medidos.
- Onde o tipo do achado aparece no formato de saída do agente por arquivo.
- O número da versão e o texto do `CHANGELOG.md`.
- Quais regras de *Re-review rounds* ficam redundantes com o escopo calculado e podem sair.

## Depois deste desenho

1. O sensor de frases de trabalho futuro na fase de docs do kit de pipeline.
2. O estado do PR num lugar só, nas regras do projeto revisado, e a atualização da regra do dono
   sobre LOW de doc, que este critério muda: LOW `form` deixa de pedir rodada.
