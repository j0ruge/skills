# Roteiro da aula

Este arquivo fixa os blocos de uma aula, a ordem deles e a regra de ensino de cada um. A coluna "Fonte" aponta para a seção do `evidencia.md` ou para a skill `teach`. Um bloco sem fonte sai do roteiro.

## 1. Os blocos, em ordem

| # | Bloco | Marcação | Fonte |
|---|---|---|---|
| 1 | Objetivo da aula, escrito como a pergunta que a pessoa tenta responder | `div.caixa.objetivo` | `evidencia.md` 5.3 |
| 2 | "Antes de ler, tente responder": pré-teste. Errar é esperado | `details.lembrar` | `evidencia.md` seção 3, regra 6; seção 1, linha "Pré-teste" |
| 3 | Revisão da aula anterior, a partir da aula 2 | `details.lembrar` | `evidencia.md` seção 3, regras 3 e 10 |
| 4 | Seções. Uma ideia em cada, com o diagrama junto do texto e o rótulo dentro da figura | `figure.diagrama` | `evidencia.md` seção 3, regras 4 e 11 |
| 4a | Termo novo: definição, exemplo do material e contraexemplo, juntos | `div.caixa.termo` | `evidencia.md` seção 3, regra 9 |
| 4b | "Por quê?" e "e se fosse diferente?" | `div.caixa.ideia` | `evidencia.md` seção 3, regra 7 |
| 4c | Exemplo resolvido: completo, depois parcial, depois sozinho | `div.caixa.exemplo-resolvido` e `div.caixa.exemplo-inventado` | `evidencia.md` seção 3, regra 8 |
| 4d | Analogia | `div.caixa.analogia` | `evidencia.md` 5.1 |
| 5 | "Lembre sem olhar" e "explique a um colega" | `details.lembrar` | `evidencia.md` seção 3, regras 1 e 5 |
| 6 | Quiz com retorno imediato e o porquê | `div.quiz` | `evidencia.md` seção 3, regras 1 e 2 |
| 7 | Aplique agora: uma tarefa ligada ao uso real | `div.caixa.aplique` | `evidencia.md` 5.4 |
| 8 | Para ler na fonte: a fonte primária mais confiável | `div.caixa.na-fonte` | skill `teach` |
| 9 | Convite a perguntar ao agente | `div.caixa.pergunte` | skill `teach` |

Os blocos de aviso `cuidado` e `nao-confunda` não têm lugar fixo. Entram onde o texto precisa deles (seção 3 deste arquivo).

## 2. Regra de cada bloco

### 1. Objetivo
- Escreva o objetivo como uma pergunta que a pessoa tenta responder antes de ler. O objetivo e o bloco 2 formam um par: o objetivo diz o que se busca, o pré-teste deixa tentar.
- O apoio é modesto. A evidência é mista e antiga, com um estudo recente (`evidencia.md` 5.3).
- Dê o retorno do pré-teste, como manda a regra 2. O resultado contrário de um só estudo fica como aviso.

### 2. Antes de ler
- Uma pergunta antes do conceito novo. Diga que errar é esperado.
- A resposta certa vem depois, dentro da aula.

### 3. Revisão da aula anterior
- Entra a partir da aula 2. Leva duas ou três perguntas de aulas de dois a quatro dias antes.
- Misture aulas e peça para distinguir conceitos parecidos.
- A pergunta errada volta na aula seguinte, até a pessoa acertar.

### 4. Seções
- Uma ideia por seção. Se a seção pede dois títulos, são duas seções.
- O diagrama fica junto do texto. O rótulo vai dentro da figura. Cor e seta marcam só o caminho principal.
- O texto diz tudo o que o diagrama diz (`linguagem-simples.md`).

### 4a. Termo novo
- A caixa traz três partes: definição, exemplo do material e contraexemplo.
- O termo é explicado na primeira menção, antes de qualquer frase que o use.

### 4b. Por quê
- Cada decisão do material recebe um "por quê?" curto. Se couber, recebe também "e se fosse diferente?".

### 4c. Exemplo resolvido
- Para um procedimento, mostre três versões: completa, parcial e sozinho.
- Tire o apoio quando a pessoa acertar.
- O exemplo inventado leva a marca `exemplo-inventado` e nunca repete um número real no mesmo papel.
- O exemplo resolvido vale para iniciantes. Quem já domina o assunto perde o efeito (`evidencia.md` seção 1, linha "Exemplo resolvido"). Se o curso é para quem domina, corte o passo a passo.

### 4d. Analogia
A regra segue o que as fontes sustentam (`evidencia.md` 5.1):
1. Use a analogia para ajudar o iniciante a inferir e a entender a ideia geral.
2. Dê também a definição literal. A analogia sozinha custou acertos nos detalhes.
3. Prefira duas analogias ou dois casos, com a pergunta "o que os dois têm em comum?". Dê o princípio depois da comparação.

Uma frase ficou fora de propósito: "diga onde a analogia deixa de valer". Nenhuma fonte lida a sustenta, e o `evidencia.md` 5.1 registra isso. O roteiro não a cobra como regra. O autor da aula pode escrevê-la como cuidado próprio.

### 5. Lembre sem olhar e explique a um colega
- No fim da seção, uma pergunta aberta. A resposta fica dentro de `details`.
- "Explique a um colega" pede que a pessoa explique com as próprias palavras, sem notas.
- Não proponha reler.

### 6. Quiz
- O retorno vem logo após o toque: o certo e o porquê.
- O porquê da opção certa leva fonte e localização.
- As opções têm o mesmo número de palavras. A certa muda de posição de pergunta para pergunta.
- Nunca pergunte "ficou claro?". O quiz exige uma resposta.

### 7. Aplique agora
- A tarefa pede que a pessoa use o conteúdo numa situação dela e diga como ele se liga à situação.
- Inclui uma pergunta nova, de aplicação, que não repete o exemplo da aula.
- A tarefa é curta. Nenhuma fonte lida mede quanto tempo ela deve durar (`evidencia.md` 5.4).
- A situação vem da missão (seção 5 deste arquivo).

### 8. Para ler na fonte
- Aponte a fonte primária mais confiável do tema, com a seção a ler. A regra vem da skill `teach`.

### 9. Convite a perguntar ao agente
- Feche com um convite a perguntar. A regra vem da skill `teach`.

## 3. Cuidado e "não confunda"

- `cuidado` avisa de um erro comum. `nao-confunda` separa dois sentidos do mesmo termo, ou dois termos parecidos.
- Todo termo com dois sentidos no curso ganha uma caixa `nao-confunda` no lugar onde o segundo sentido aparece.

## 4. Pausas e foco: fora da aula

Pausas não são bloco. O `evidencia.md` 5.2 manda o destino:
- Corte a aula com perguntas de recuperação (blocos 2, 5 e 6). Elas fixam e mantêm o foco.
- Nenhum limite em minutos entra na skill. Nenhuma fonte o sustenta. O autor do curso escolhe a duração, e o sensor de tempo só confere que o tempo prometido bate com o tamanho da aula.
- O plano de estudo do índice pode sugerir um intervalo sem tela depois de uma aula. O apoio é fraco e de laboratório. A frase sai como sugestão, sem número de ganho.

## 5. Missão

Os blocos 1 e 7 dependem da missão. Use este formato curto no `MISSION.md` da pasta do curso:

```
# Missão
Por que quero aprender:
O que vou fazer com isso:
Até quando:
```

1. Se a pasta tem um `MISSION.md` (o da `teach`), leia-o.
2. Se não tem, pergunte à pessoa as três linhas acima e grave a resposta nesse formato.
3. Não exija a `teach`.

## 6. Aula por chat

Estas regras valem quando o agente ensina pelo chat, com o curso aberto. Ficam fora do fluxo de construção. Vêm do `evidencia.md`, seção 3.

1. Corrija logo após cada resposta: diga o certo e o porquê (regra 2).
2. Abra a aula com duas ou três perguntas de dois a quatro dias antes. A errada volta até ser acertada (regra 3).
3. Avance com cerca de 80 % de acerto. Abaixo disso, divida o passo (regra 4).
4. Nunca pergunte "ficou claro?". Peça que a pessoa explique com as palavras dela (regra 5).

## 7. Páginas de consulta

O roteiro vale também para glossário, números e perguntas, no que couber: termo com definição e exemplo, e fonte em cada número.
