# Lições de construção

Cada lição vem de um defeito medido num guia de estudo de 9 aulas de outro projeto. A medida fica escrita aqui, para a skill não depender desse guia. Os números foram observados em 2026-11-22, com Playwright 1.58.0 e Chromium headless; o `scripts/rodar-tudo.sh` os refaz num curso novo. O kit em `assets/curso-modelo/` já aplica todas. Leia este arquivo antes de mudar o kit ou de pôr um recurso novo numa página.

## 1. Rede pendurada é pior que rede ausente

- **Defeito:** sem rede alguma, o navegador recusa o host na hora e a página funciona. Com a rede que não responde (Wi-Fi de hotel antes do login, sinal que cai), o Mermaid síncrono e a folha de fonte bloqueante deixavam a aula em branco e o quiz mudo.
- **Medida:** com o CDN do Mermaid e os hosts de fonte sem resposta, a primeira pintura levava 15.084 ms. Com Slow 3G, o quiz respondia ao primeiro toque só aos 14.970 ms. Na cópia sabotada, o carregamento estourava 30.000 ms.
- **Regra:** o Mermaid entra por `<script async>` que o próprio `diagramas.js` insere, e o desenho acontece no `onload`. A fonte da web, se houver, entra com `media="print" onload="this.media='all'"`. O kit usa fontes do sistema por padrão.
- **Depois:** primeira pintura aos 120 ms, quiz aos 356 ms em Slow 3G. O sensor `rede-pendurada.js` pendura todo host externo e exige primeira pintura em 3 s e quiz respondendo em 2 s.

## 2. O `useMaxWidth` do Mermaid leva o texto a 5 a 10 px no celular

- **Defeito:** o Mermaid encolhe o SVG até caber na largura do quadro. A 390 px, o texto das caixas ficava entre 5 e 10 px, um terço do texto do corpo.
- **Medida:** na cópia sabotada, menor texto de 7,7 px e de 6,1 px em duas aulas.
- **Regra:** o `diagramas.js` mede o menor texto de cada desenho, Mermaid ou SVG feito à mão. Abaixo de 11 px, o desenho recebe uma largura mínima que leva esse texto a 12 px, e rola de lado dentro do quadro. A conta se refaz quando a janela muda de largura. A legenda fica fora da área que rola.
- **Depois:** menor texto de 11,0 a 12,0 px, e a página rola 0 px de lado.
- **Efeito colateral medido:** a 1366 px, dois desenhos também passaram a rolar (92 px e 255 px escondidos), e a dica antiga mandava arrastar, o que o mouse não faz: o arrasto seleciona texto. A dica diz agora que o toque arrasta e que o mouse usa Shift com a roda. O sensor `desenho-cortado-no-notebook.js` confere as duas dicas e que Shift com a roda rola o quadro.

## 3. Por `file://`, o Chromium não tem cache de voltar

- **Defeito:** o Voltar e o recarregar montam a página de novo, do zero. A pessoa respondia duas perguntas e abria três caixas, tocava o rodapé, voltava, e o placar dizia "0 de 0" com as caixas fechadas. A segunda tentativa passava a contar como primeira.
- **Medida:** antes, placar "1 de 2" e três caixas abertas; depois do Voltar, "0 de 0" e `000`.
- **Regra:** o `quiz.js` grava no `sessionStorage`, na chave `'guia:' + location.pathname`, a primeira tentativa, a última opção marcada e as caixas `details` abertas. Aba nova recomeça do zero: é assim que se refaz o quiz no dia seguinte. Sem `sessionStorage`, a página funciona sem guardar. Nada sai do navegador.
- **Toda página com `details` carrega o `quiz.js`,** mesmo sem quiz. Uma página de perguntas com 40 caixas e sem o script perdia as cinco caixas abertas e a rolagem (7.268 para 5.052 px). Com o script, 7.268 para 7.268 px.
- **Sensores:** `quiz-zera-ao-voltar.js` (Voltar, recarregar, aba nova) e `caixas-fecham-ao-voltar.js` (sai por um link dentro de uma caixa e volta).

## 4. O escuro forçado do Chrome muda só a pintura

- **Defeito 1:** com o escuro forçado, o navegador clareia o texto dos rótulos Mermaid e deixa claro o fundo das caixas. O texto fica claro sobre claro, a 1,06:1.
- **Regra 1:** o quadro do desenho tem `color-scheme: only light`. Ele fica como um cartão claro, e o resto da página escurece. Depois, o pior rótulo ficou em 4,97:1. O sensor é `mermaid-ilegivel-no-escuro-forcado.js`.
- **Defeito 2:** o anel de foco de cor escura media 9:1 no estilo computado, mas só 2,03:1 no escuro forçado, porque o navegador escurece o fundo da pergunta e não muda o contorno.
- **Regra 2:** meça o contraste nos pixels da captura. Um sensor que lê `getComputedStyle` passa em silêncio, porque o estilo computado não muda. O anel de foco usa uma cor de luminância entre a do branco e a do fundo escuro: 4,55:1 no claro e 4,11:1 no escuro forçado, medidos nos pixels. Sensor: `foco-sem-contraste.js`, com as duas passadas.
- **Como ligar o modo:** `--blink-settings=forceDarkModeEnabled=true` no Chromium, com `colorScheme: dark` no contexto. Só `prefers-color-scheme: dark` não força nada.

## 5. A cor da marca usada como texto precisa de um token mais escuro

- **Defeito:** uma cor boa para linha, ponto e barra (mínimo de 3:1 para forma) falha como texto (mínimo de 4,5:1). A cor de marca usada nos rótulos dos gráficos ficou em 4,25:1 sobre o cinza do quadro. O rótulo das caixas coloridas ficou entre 3,85:1 e 4,13:1.
- **Medida:** com um token de texto mais escuro, 5,39:1 sobre o quadro, e de 4,88:1 a 5,23:1 sobre as três caixas, 5,77:1 no branco. O foco amarelo da marca original chegava a 1,47:1 sobre o branco, e o mínimo do indicador é 3:1.
- **Regra:** o `estudo.css` tem um token de texto para cada cor de marca (`--marca-texto`, `--destaque-texto`, `--acento-texto`), medido em 4,5:1 sobre cada superfície em que o texto aparece. A cor da marca fica para forma e borda. Texto de SVG feito à mão usa o `fill` escuro, e a forma mantém o dela.
- **Sensores:** `texto-dos-graficos-sem-contraste.js` (contraste do `fill` contra a forma sob o texto) e `rotulo-das-caixas-sem-contraste.js` (estilo computado, tema claro; o escuro forçado se mede à parte, como na seção 4).

## 6. Quiz acessível: marcas, borda e alvos de 44 px

- **Defeito 1, cor como único sinal:** a opção certa e a errada diferiam só em verde e vermelho. Sem enxergar cor, as duas ficavam iguais, e o retorno em texto não nomeava a certa. Leitor de tela também não sabia qual botão era o certo.
- **Regra 1:** o `quiz.js` escreve a marca na opção certa e na escolha errada (`span.marca`, com `✓` e `✗` de `textos.js`), a certa leva borda dupla e a errada, borda tracejada. O retorno de um erro termina nomeando a certa. A `.pergunta` recebe `data-resultado`. Sensor: `quiz-certa-so-pela-cor.js`.
- **Defeito 2, retorno repetido:** o retorno de um erro saía "Ainda não. Não. …" em 21 de 40 opções erradas, porque a explicação começava por "Não.". Regra: o `quiz.js` tira do começo da explicação a palavra de `negacoes`. O texto da aula não muda. Sensor: `retorno-repete-negacao.js`.
- **Defeito 3, alvo de toque:** atalhos de um algarismo tinham cerca de 10 por 24 px, a 15 px do vizinho. O rodapé tinha 24 px de altura, e links de lista tinham 19 px.
- **Defeito 4, triângulo do `summary`:** o `details.lembrar summary` usava `display: flex` para centrar o texto, e o `flex` tira o marcador de abrir (medido no Chromium 1.58.0: o texto começa em 0 px da borda do conteúdo, e em 18 px com `display: list-item`). Regra: todo `summary` fica em `list-item`, e os 44 px vêm de `min-height` com `box-sizing: border-box`. Sensor: `alvo-de-toque-pequeno.js` lê o `display` de cada `summary`.
- **Regra 3:** `min-height: 44px` e `inline-flex` no rodapé, nos atalhos e no link do glossário. No celular, todo parágrafo ou item de lista com três links ou mais vira uma linha de botões de 44 por 44 px (`li:has(> a ~ a ~ a) > a`). Uma correção por seletor com nome deixa de fora o link que não casa com o nome: o primeiro conserto não pegou a lista do índice nem o item com três links para outras páginas. Sensores: `alvo-de-toque-pequeno.js` e `links-vizinhos-pequenos.js`.

## 7. O PDF do celular

- **Decisão:** no celular, a pessoa lê um PDF das páginas de consulta, com as caixas abertas e os diagramas desenhados. O PDF se gera de novo a cada mudança dessas páginas, pelo `gerar-pdf.js`. Ele fica fora do git.
- **Regra:** página A5, para o texto ficar grande na tela. O `gerar-pdf.js` abre todos os `details` depois do carregamento, zera o `min-width` do SVG (no papel não há rolagem, e o desenho volta a caber) e esconde a dica de rolagem.
- **Medida:** a saída traz `diagramas 0, caixas fechadas 0` por página e sai 1 se alguma caixa ficou fechada. Uma página de perguntas com 40 caixas deu 20 páginas A5. O script precisa de rede para o Mermaid.

## 8. Rótulo do Mermaid que começa por "1. " vira lista

- **Defeito:** um rótulo de caixa que começa por `1. ` é lido como lista markdown, e o desenho mostra "Unsupported markdown". Apareceu ao montar o curso-modelo.
- **Regra:** não numere rótulos do Mermaid com "N. ". Tire a numeração, ou escreva "Passo 1" no lugar. O `conferir.js` acusa o erro do Mermaid em cada página.

## 9. A instalação do Chromium apaga o cache dos outros projetos

- **Defeito:** `npx playwright install chromium` (Playwright 1.58.0) apaga do cache compartilhado `~/.cache/ms-playwright` os browsers que nenhuma instalação aponta, a menos que `PLAYWRIGHT_SKIP_BROWSER_GC=1` esteja no ambiente (`_validateInstallationCache`, em `playwright-core/lib/server/registry/index.js`, linha 1030).
- **Medida:** na máquina de teste, ela apagou `chromium-1140` e `ffmpeg-1010`, usados por outros projetos.
- **Regra:** o `preparar.sh` exporta `PLAYWRIGHT_SKIP_BROWSER_GC=1` na linha do `playwright install`. Se você instalar o Chromium à mão, ponha a variável antes.
- **Como reconferir:** `grep -n SKIP_BROWSER_GC scripts/preparar.sh` mostra a variável na linha do `playwright install`. Na versão instalada, `grep -n _validateInstallationCache <bancada>/pw/node_modules/playwright-core/lib/server/registry/index.js` mostra a função que apaga. A linha 1030 vale para a 1.58.0; com outra versão, o número muda.
