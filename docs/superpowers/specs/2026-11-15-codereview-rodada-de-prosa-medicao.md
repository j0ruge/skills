# codereview: medição da rodada de verificação

**Data:** 2026-11-15 · **Desenho:** `2026-11-15-codereview-rodada-de-prosa-design.md` · **Skill medida:** commit `f5c79e2` desta branch

Repetição, só de leitura, sobre os intervalos de quatro rodadas gravadas de um motor de regras
.NET (PR #30). Agentes no modelo `opus`. Cada verificador recebeu o prompt de lançamento do
`references/verification-round.md` por um arquivo, o que custa uma leitura a mais que o lançamento
real. Os tokens e a duração são os que a notificação de cada agente informa.

## O escopo que o script calcula

| Intervalo | Arquivos de prosa | Arquivos `CODE` | Unidades | Linhas de unidade |
|---|---|---|---|---|
| r3 `e195f52...b87d5c7` | 32 | 0 | 232 | 672 |
| r4 `b87d5c7...e652c6d` | 11 | 2 | 14 | 91 |
| r5 `e652c6d...5e65896` | 7 | 0 | 8 | 34 |
| r6 `5e65896...786b348` | 4 | 0 | 6 | 26 |

O `prose_units.py` saiu com rc 0 nos quatro. A r3 foi a primeira rodada sobre aqueles docs, que
o desenho mantém como rodada completa, e por isso não recebeu verificador. Na r4, dois arquivos
saíram `CODE`: um com uma mensagem de erro mudada e um com um comentário no fim de uma linha de
código.

## Os verificadores (três execuções por intervalo)

| Intervalo | Tokens por execução | Duração | Achados nas unidades | Fora do escopo |
|---|---|---|---|---|
| r4 | 141.054 · 137.984 · 153.066 | 264 a 283 s | 3 · 2 · 3 | 4 · 3 · 1 |
| r5 | 151.698 · 124.751 · 125.712 | 190 a 224 s | 2 · 1 · 3 | 5 · 5 · 3 |
| r6 | 134.681 · 135.363 · 144.256 | 244 a 284 s | 2 · 4 · 3 | 5 · 2 · 3 |

As nove execuções terminaram em `END_OF_VERIFICATION` e leram todas as unidades recebidas. Média:
138.729 tokens por verificador.

## Alvos: o que as rodadas originais tinham achado

| Alvo | Tipo | Achado em |
|---|---|---|
| r5: contradição dentro de um item de lista, criada pelo conserto da r4 (o MEDIUM da r5) | `behavior` | 3 de 3 |
| r6: ponteiro de uma regra para o arquivo errado | `form` | 2 de 3 |
| r6: frase sem sujeito | `form` | 2 de 3 |
| r4: célula de tabela que dizia "sem bloco" ao lado da forma nova, com bloco | `form` na rodada original | 0 de 3 |

O portão do plano (o alvo da r5 em 3 de 3, e menos de dois alvos pequenos falhando) passou.

Achados que as rodadas originais não tinham dado:

- r6, nas 3 execuções: uma frase da mesma célula de tabela que só vale sem bloco. Conferida no
  código pela sessão: com bloco, a função devolve a marca do `OverrideEvent`, e não o valor da
  condição. O head do PR ainda a carrega.
- r4, nas 3 execuções: uma frase que nomeia quatro leitores e diz "três lugares", com a relação
  entre os predicados invertida.
- Na lista "fora do escopo", pela busca dos identificadores: frases em outros cinco docs que o
  texto novo passou a contradizer. Nenhuma das quatro rodadas originais as tinha relatado.

## A comparação com o fluxo de hoje, no intervalo da r4

Os mesmos 11 arquivos de prosa, em 4 agentes por arquivo (grupos de até 3): 106.908, 111.847,
135.516 e 159.997 tokens, **514.268 no total**, de 75 a 213 s cada. O verificador único gastou em
média **144.035**: 3,6 vezes menos.

O fluxo de hoje achou o que o verificador não achou:

- 3 achados `behavior` em linhas fora das unidades, entre eles o MEDIUM da r4 original, numa
  linha 15 linhas abaixo de uma unidade editada, no mesmo arquivo;
- o alvo "sem bloco", desta vez como `behavior`, com a linha do código que o contradiz.

É o limite que o desenho declara, agora com número: a rodada de verificação custa 3,6 vezes
menos e não procura drift antigo fora dos trechos editados. Nesta medição, isso deixou de fora uma
frase falsa de severidade MEDIUM que uma releitura do arquivo inteiro achou.

## Limites desta medição

- Um projeto só, em português, com docs densos. Três execuções por intervalo.
- Os tokens das rodadas originais não foram gravados; a comparação é contra uma execução do fluxo
  de hoje sobre o intervalo da r4, só nos arquivos de prosa.
- Nas execuções em que o intervalo não termina no head do repositório, a busca de identificadores
  usou o commit do intervalo.
