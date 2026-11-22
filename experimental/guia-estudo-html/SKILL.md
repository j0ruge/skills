---
name: guia-estudo-html
description: "Monta e testa um curso de estudo em HTML estático, de qualquer assunto. Triggers — guia de estudo, curso HTML, aula HTML, roteiro de aula, quiz, testar guia, lição, teach"
---

# guia-estudo-html

Monta um curso de estudo em HTML estático e o testa com sensores Playwright. O curso tem índice, aulas, glossário e páginas de consulta. Cada aula segue um roteiro de ensino com fonte, em linguagem simples. O kit traz quiz e diagramas que resistem a rede lenta, celular e escuro forçado.

**Estado do método: estrutura conferida, aprendizado ainda não medido.** Os sensores provam que os blocos existem e que a página funciona. Ninguém mediu se alguém aprendeu pelo curso. A skill fica em `experimental/` até o primeiro curso de outro projeto registrar isso (ver `CHANGELOG.md`).

Esta skill não decide o que ensinar (isso é da `teach`) e não faz deck de palestra (isso é da `html-presentation`).

## Fluxo

Missão, planejar, escrever, montar, testar, entregar. Faça um passo por vez.

### 1. Missão

Leia o `MISSION.md` da pasta do curso. Se não existe, pergunte à pessoa as três linhas (por que aprender, o que fazer com isso, até quando) e grave. Não exija a `teach`. O formato está em `references/roteiro-da-aula.md`, seção 5.

### 2. Planejar

1. Liste as aulas, uma ideia grande em cada. Nomeie o arquivo `lessons/000N-<slug>.html`.
2. Para cada bloco do roteiro, confira a fonte em `references/evidencia.md`. Bloco sem fonte primária conferida não entra.
3. Defina o tempo de cada aula. O sensor confere que o tempo prometido bate com o tamanho.

### 3. Escrever

Escreva cada aula pelo `references/roteiro-da-aula.md` (os blocos, a ordem e a regra de cada um) e pelo `references/linguagem-simples.md` (um termo novo por vez, texto que diz tudo o que o diagrama diz, número com fonte e localização). Use só a marcação de `references/marcacao.md`: classes e atributos `data-*`, sem ler o texto visível.

### 4. Montar

Copie `assets/curso-modelo/` para a pasta do curso. Ela traz `assets/curso-modelo/index.html`, duas aulas (`assets/curso-modelo/lessons/0001-o-que-cada-uma-diz.html` e `assets/curso-modelo/lessons/0002-quando-a-media-engana.html`), o glossário (`assets/curso-modelo/reference/glossario.html`) e o kit em `assets/curso-modelo/assets/` (`textos.js`, `estudo.css`, `assets/curso-modelo/assets/diagramas.js` e `assets/curso-modelo/assets/quiz.js`). Troque o conteúdo e deixe o kit como está.

- As frases da interface ficam só em `assets/curso-modelo/assets/textos.js`. Para outra língua, troque esse arquivo.
- Os scripts vão no fim do `body`, nesta ordem: `textos.js`, `diagramas.js`, `quiz.js`. Toda página com quiz ou `details` carrega o `quiz.js`.
- Para as cores do projeto, troque os tokens de `:root` em `assets/curso-modelo/assets/estudo.css`. Cada cor de marca usada como texto tem um token mais escuro, medido em 4,5:1.
- Não numere rótulos do Mermaid com "1. ".

### 5. Testar

```bash
bash scripts/preparar.sh <bancada nova>                      # Playwright 1.58.0 e Chromium; uma vez
bash scripts/rodar-tudo.sh <bancada> <pasta do curso>        # conferir.js e os 17 sensores
python3 scripts/sabotar.py <pasta do curso> <pasta nova> --bancada <bancada>
```

- A bancada, as capturas e as cópias sabotadas ficam fora de qualquer repositório e fora do `/tmp`.
- `rodar-tudo.sh` grava cada execução em `<bancada>/execucoes/<data-hora>-<pid>/`. Duas execuções ao mesmo tempo não se pisam. Sai 1 se algo falhar, e 2 se a bancada ou o curso não existem.
- `sabotar.py` desfaz cada correção numa cópia. Todo sensor tem de falhar na sua cópia (MORTO). Sensor VIVO não prova nada.
- Um sensor por defeito, sempre provado por sabotagem. O método de QA, o modelo de bug e a revisão de conteúdo por aula estão em `references/qa.md`.
- Confira cada DOI de um arquivo de fontes com `python3 scripts/conferir-dois.py <arquivo.md>`.

### 6. Entregar

1. Rode `rodar-tudo.sh` de novo: tudo em rc 0.
2. Gere o PDF de leitura no celular das páginas de consulta: `NODE_PATH=<bancada>/pw/node_modules node scripts/gerar-pdf.js <pasta de saída> <página.html>...`. A página é A5, com os `details` abertos. O PDF fica fora do git.
3. Termine o relatório de QA com "Verificação humana necessária": o que a pessoa confere sobre o aprendizado e como (`references/qa.md`, seção 7).

## Aula por chat

Quando o agente ensina pelo chat, com o curso aberto, valem as regras de `references/roteiro-da-aula.md`, seção 6:

1. Corrija logo após cada resposta: diga o certo e o porquê.
2. Abra a aula com duas ou três perguntas de dois a quatro dias antes. A errada volta até ser acertada.
3. Avance com cerca de 80 % de acerto. Abaixo disso, divida o passo.
4. Nunca pergunte "ficou claro?". Peça que a pessoa explique com as palavras dela.

## Armadilhas

Cada uma tem medida e correção em `references/construcao.md`.

- Rede pendurada trava a página mais que rede ausente: o Mermaid entra por `async`, e a fonte da web não bloqueia.
- O `useMaxWidth` do Mermaid leva o texto a 5 a 10 px no celular: o desenho rola dentro do quadro.
- Por `file://`, o Voltar zera a página: o estado vai para o `sessionStorage`.
- O escuro forçado muda só a pintura e deixa o estilo computado igual: meça o contraste nos pixels.
- Cor de marca como texto falha em 4,5:1: use o token de texto.
- Quiz sem marca e sem borda depende só da cor: use `✓`, `✗` e bordas.
- Link de 19 a 26 px de altura erra o toque: 44 px, e seletor por contagem de links.
- `npx playwright install chromium` apaga browsers do cache compartilhado: use `PLAYWRIGHT_SKIP_BROWSER_GC=1`.
- Curso em pasta com espaço ou acento: os scripts abrem a página por `pathToFileURL`.

## Referências

| Arquivo | Leia quando |
|---|---|
| `references/roteiro-da-aula.md` | for escrever uma aula, ou ensinar pelo chat |
| `references/linguagem-simples.md` | for escrever ou revisar o texto de uma aula |
| `references/evidencia.md` | alguém perguntar por que um bloco existe, ou for propor bloco novo |
| `references/marcacao.md` | for escrever uma página ou um sensor novo |
| `references/construcao.md` | for mudar o kit ou pôr um recurso novo numa página |
| `references/qa.md` | for testar o curso, abrir um bug ou revisar o conteúdo |
