# Changelog — html-presentation

Versioned history of the plugin (mirrors `plugin.json`). The per-session record lives in
`skills/html-presentation/CHANGELOG.md`.

## [1.10.1] — 2026-11-27

### A variante larga com condição, e testes do build

- **A condição.** A armadilha *Empty stage* do `SKILL.md` mandava "add `.wide`" sem ressalva, e o registro da 1.10.0
  diz que o efeito depende da fonte. Agora ela diz "Try `.wide`; the shot decides", com o mesmo tamanho, porque o
  `SKILL.md` está a 2 caracteres do teto de 20 mil. A tabela de tipos do `layout-and-type.md` leva o detalhe: a fonte
  decide quantas linhas o título ocupa, e a variante fica só quando a captura mostra menos linhas.
- **A contagem.** O título do caso tem 83 caracteres, não "cerca de 84": a revisão da retro recontou, e o registro
  da 1.10.0 foi corrigido nos dois CHANGELOGs.
- **Os testes.** O plugin não tinha pasta de testes, e a porta da `retrofit-watch` registrou isso ao publicar a
  1.10.0. `tests/test_build.py` roda o `build.py` sobre uma cópia do template, só com a biblioteca padrão: o template
  passa, gera o roteiro e traz a variante larga; seis portões reprovam (orçamento de tempo, recurso externo, lâmina
  sem nota, asset ausente, dica sem verbete, outro deck na mesma pasta); e um recurso externo dentro de comentário
  passa. Cada portão foi provado por uma mutação no `build.py` ou no template, e as 8 mutações reprovaram a suíte.

## [1.10.0] — 2026-11-27

### Variante larga do título no template

- **O caso.** Um título-afirmação novo, de 83 caracteres, quebrou em 3 linhas sob o
  `.head .t-title{max-width:30ch}` do template. A captura mostrou o título em ~60 % da largura e a metade direita do
  palco vazia. O `check-fit` aprovou, porque mede caixa fora do lugar, e não linhas de título. Cada deck reinventava
  uma variante larga.
- **A mudança.** O `deck-template.html` traz `.head .t-title.wide{max-width:none}`. A tabela de tipos do
  `layout-and-type.md` manda `class="t-title wide"` para título de uma linha e para a afirmação que quebra em 3
  linhas no `30ch`. A armadilha *Empty stage* do `SKILL.md` aponta para a variante.
- **O limite.** O efeito depende da fonte: com a fonte do deck, o mesmo título deu 3 linhas no `30ch` e 2 no `none`;
  com a fonte padrão do template, 3 nos dois casos. Quem decide é a captura.

## [1.9.0] — 2026-11-26

### O `check-fit` mede o número de página do PDF

- **O caso.** No deck da defesa de TCC, a capa ganhou um quarto metadado, a banca examinadora, e a linha de crédito
  desceu para uma segunda linha, alinhada à direita. Na impressão, o `.slide::after` põe o número "01 / 19" em
  `right:128px; bottom:52px`, no mesmo canto. A captura, o `check-fit` nos quatro tamanhos e o `check-presenter`
  ficaram verdes. Só a página 1 do PDF, aberta a olho, mostrou o número sobre o crédito.
- **A passada nova.** Depois das quatro medidas de tela, o `check-fit.mjs` mede uma vez em `print`, a 1920×1080. O
  pseudo-elemento não tem caixa própria: uma sonda copia o estilo calculado do `::after` e o texto dele, e um `Range`
  mede os glifos. Assim o número desenhado sobre a lâmina inteira (`inset:0`, alinhado embaixo à direita) também
  mede certo. Só texto conta: foto ou fundo sob o número é escolha de desenho, e texto sob ele é defeito. A lâmina
  com texto sob o número reprova (saída 1). Um deck sem número na impressão aparece na saída como "nenhum número de
  página na impressão" e não reprova.
- **A prova.** O deck da defesa ficou verde, com o número medido nas 19 lâminas. Uma cópia com o crédito à direita
  reprovou a lâmina 1 (`div.credit`). Uma cópia com `inset:0` no número da capa deu o mesmo par, verde e vermelho.
  Uma cópia sem a regra do `::after` mediu 0 lâminas e disse isso, sem "livre". O template da skill passou, com o
  número medido nas 8 lâminas.
- O `SKILL.md` muda em duas frases, a do passo 6 e a da tabela de arquivos, porque está a 19,9 mil caracteres. O
  caso fica no cabeçalho do script.

## [1.8.0] — 2026-11-26

### Zoom por clique no template; o `check-presenter` tira os testes de clique de cima das fotos

- **Zoom por clique.** Na defesa de TCC, o autor experimentou a fileira de fotos da 1.7.3 e a reprovou: a foto abria
  quando o mouse passava, a foto aberta trocava pela de baixo, e o clique ao lado dela trocava a lâmina. Um QA de
  usabilidade, feito por um agente independente, achou mais dois defeitos. A foto fechava quando o mouse passava da
  borda por ~150 ms, e a volta caía na miniatura de baixo, que abria. A curva `cubic-bezier(.16,1,.3,1)` punha metade
  de um caminho de 637 px em ~36 ms. Espera, margem e tolerância ao tremor resolveram os casos do QA, mas o autor
  ficou só com o clique ("total controle"). O template troca o `.zoom:hover` (escala no lugar) pela moldura
  `div.zoom`. O clique abre, e a foto viaja por `transform` até o centro do palco, com 1000 px de altura. A capa
  `::after` cobre o palco com o cursor `zoom-out`, e o clique só fecha. O motor ganha o bloco "Fotos com zoom", o
  `fecharZoom()` em `show()` e a guarda no clique da moldura, da `.zoom-row` e de `figure:has(.zoom)`.
- **A prova.** No deck da defesa, um sensor do projeto com 17 verificações ficou verde nas lâminas 3 e 4. Cada uma
  das 14 cópias sabotadas, uma por mecanismo, ficou vermelha. Num deck de teste feito do template novo, as três fotos
  abriram a 0,0 px do centro, com 1000 px de altura.
- **Falso alarme no `check-presenter`.** Os testes de clique usavam a lâmina 3, e no deck da defesa ela tem fotos no
  centro. As duas verificações de clique falharam sem defeito no motor. Agora os testes avançam até uma lâmina com os
  dois pontos livres de foto. Sem esse pulo, o deck de teste repete as duas falhas. Três verificações novas cobrem o
  zoom por clique: o clique abre sem trocar a lâmina, o clique só fecha, e a troca de lâmina fecha. Uma cópia sem a
  guarda do clique reprova as três. Um deck sem `div.zoom` dá "pulado", inclusive o zoom antigo em `img.zoom`.
- `references/layout-and-type.md`: as entradas *Zoom on hover* e *Zoom to the center* viram *Zoom on click*. Saem
  duas lições que valiam só para o zoom sob o mouse, que o template não tem mais. Uma é a do rodapé (escala no lugar,
  21/11). A outra é a da foto que piscava (`:hover` na foto, 26/11). As notas do PDF e do `build.py` passam para a
  entrada nova, com a migração de um deck antigo.
- O `SKILL.md` muda só na tabela de arquivos ("click zoom"), porque está a 19,9 mil caracteres.

## [1.7.3] — 2026-11-26

### Fileira de fotos que vão ao centro do palco, sem piscar; a fileira que esticava as imagens

- **Zoom ao centro.** A entrada *Zoom on hover* amplia a imagem no lugar, a partir de um ponto fixo. Numa fileira de
  três figuras, esse ponto empurra as das pontas para fora do palco. A `references/layout-and-type.md` ganha a
  variante: uma moldura guarda o tamanho de repouso, e no `:hover` dela a foto ganha `position:fixed` no centro, com
  `pointer-events:none`. Dentro do `#stage` escalado, o `fixed` se mede no palco. Na defesa de TCC, um sensor
  Playwright mediu 0 px do centro a cada 50 ms durante 500 ms. Com o `:hover` na própria foto, 4 a 6 de 11 amostras
  voltaram pequenas: a foto saía de baixo do cursor e piscava. Com a ampliação no lugar, a foto da ponta esquerda ficou
  a 637 px do centro.
- **Fileira de figuras esticada.** No mesmo deck, as três imagens saíram de 9 % a 20 % mais largas e encostadas, com o
  `build.py` e o `check-fit.mjs` verdes. A captura mostrou o defeito. Uma linha que cobre as três colunas `auto`
  alarga as colunas, e o `figure` em coluna flexível estica a moldura por cima do `aspect-ratio`. A reference diz
  as três regras que resolveram.
- Só a reference muda: o template e os scripts ficam como estão. A classe no template e um sensor em `scripts/`
  ficam para quando forem provados ali.

## [1.7.2] — 2026-11-22

### Uma pasta `--out` por deck: o build recusa o roteiro de outro deck; a lâmina privada fora do pacote de revisão

- **Roteiro sobrescrito.** O `build.py` grava sempre `<out>/roteiro-de-fala.md`, qualquer que seja o `--name`. A
  1.7.0 registrou isso como "Not fixed here". Na defesa de TCC, a versão 2 do deck foi construída no mesmo `dist/`
  da versão 1 e sobrescreveu o roteiro rastreado dela (sha256 `c52105…` para `972bb8…`); o da versão 2 ficou como
  estava. Agora o cabeçalho do roteiro diz de qual fonte ele veio, e o build sai 1, sem gravar nada, quando o roteiro
  da pasta veio de outra fonte, ou não tem essa linha e a pasta tem outro deck construído. Seis casos no
  interpretador, com o `rc` escrito antes, e o caso real numa cópia: rc 1, roteiro intacto.
- **Lâmina com imagem que o agente não pode abrir.** A lâmina 3 do mesmo deck tem uma tela real tarjada. O pacote de
  revisão manda passar todas as capturas, e a `grade-1.png` e a `laptop-1280.png` mostram essa lâmina. A
  `references/review.md` diz agora como nomear no pacote as capturas proibidas. O `shoot.sh` não muda: o PDF
  precisa de todas as lâminas.

## [1.7.1] — 2026-11-22

### O modo escuro automático do Chrome não recolore o deck; cor de texto medida em cada superfície

As duas lições vieram do QA de um guia de estudo em HTML feito para a mesma defesa de TCC, com o mesmo `DESIGN.md`
(UVA) do deck. Nenhuma das duas apareceu no deck da defesa. O template tinha as duas brechas.

- **Modo escuro automático.** O "Auto Dark Mode for Web Contents" do Chrome repinta uma página que não declara
  esquema de cor. No guia, ele deixou os rótulos Mermaid com 1,06:1. No template, medido com Playwright e
  `--blink-settings=forceDarkModeEnabled=true`, a luminância média das lâminas 1 a 4 caiu de 236–244 para 35–43.
  Com `color-scheme:only light` no `:root`, as quatro ficaram iguais ao modo normal. A janela do apresentador, escura
  de propósito, mediu o mesmo nos dois modos, com e sem a linha.
- **Cor de texto em cada superfície.** O comentário dos tokens mandava medir `--brand-strong` contra texto branco. O
  template usa esse token também como cor de texto (destaque do gráfico e do ranking). No guia, o magenta da marca
  `#e60073` deu 4,55:1 no branco, 4,25:1 no `#f7f7f7` e 3,85:1 na caixa rosa `#fde6f1`. A saída foi um token de
  texto mais escuro (`#c80064`, de 4,88 a 5,77:1), e as formas ficaram com a cor da marca.

Arquivos:
- `assets/deck-template.html`: `color-scheme:only light` no `:root` e duas linhas no comentário dos tokens.
- `references/layout-and-type.md`: seção *Text color on every surface*.
- `references/engine.md`: linha *Auto dark* na tabela de comportamento. Um deck anterior à 1.7.1 precisa da linha
  portada.
- O `SKILL.md` só muda a versão: ele tem 19.843 caracteres, perto do teto de 20 mil.

Dívida anotada, sem conserto aqui: o F1 da `skill-quality-audit` (as references citadas sem dizer quando ler) e as 28
afirmações do D1 já estavam no baseline.

## [1.7.0] — 2026-11-21

### Componente novo: imagem que cresce com o mouse (`.zoom`)

No deck de uma defesa de TCC (21/11/2026), a lâmina mostrava uma tela real de 895 × 560 px, e a banca não lia os
textos dela do fundo da sala. O autor pediu que a foto crescesse com o mouse sobre ela. O efeito foi escrito à mão no
deck; a primeira escala (1.7) entrou 41 px no rodapé, e só a medição da caixa mostrou, porque o `check-fit.mjs` e o
`shoot.sh` olham a lâmina em repouso.

- `assets/deck-template.html`: classe `.zoom`, com a escala em `--zoom` (padrão 1.5) e o ponto fixo em
  `--zoom-origin`. O resto da lâmina escurece. A impressão não muda.
- `references/layout-and-type.md`: entrada *Zoom on hover*, com a medição da caixa ampliada, o limite dos dois
  sensores, o PDF com a imagem pequena e o aviso de que o `build.py` embute a imagem no `dist/`.
- O `SKILL.md` só muda a versão: está a menos de 200 caracteres do teto de 20 mil.
- Prova: no template, uma imagem com `.zoom` medida antes, durante e depois do mouse.
- Dívida anotada, sem conserto aqui: o `build.py` grava sempre `roteiro-de-fala.md`, e um segundo deck na mesma
  pasta `dist/` sobrescreve o roteiro do primeiro.

## [1.6.3] — 2026-11-20

### `check-fit.mjs` reprova a linha de fonte que entra na margem esquerda

A `.src` é ancorada à direita (`right:128px`) e cresce para a esquerda numa linha só. Com texto longo ela entra no
`padding` esquerdo da lâmina e continua dentro da caixa da lâmina, então o cheque "fora da lâmina" não a vê. No deck
de uma defesa de TCC (20/11/2026), duas correções do revisor puseram frases na `.src` das lâminas 8 e 10; a linha
começou em x = 80 no palco de 1920, com margem de 128, e o `check-fit` respondeu "encaixe ok: 17 lâminas em 4
tamanhos". Só a captura mostrou.

- `scripts/check-fit.mjs`: compara a borda esquerda da `.src` com o `padding-left` da lâmina, na escala do palco, e
  reprova com `fonte na margem esquerda`. Lâmina sem `padding` não é medida.
- `SKILL.md`: meia frase no gotcha *Source line under the content*.
- Prova: o deck com a `.src` longa falha nos quatro tamanhos; o deck corrigido e o template passam; com a
  comparação desligada o deck defeituoso volta a passar (mutante morto pelo caso).

## [1.6.2] — 2026-11-20

### A identidade do deck se pergunta no brief, e sem `DESIGN.md` ela se deriva do site

Só documentação muda: `SKILL.md` (quatro frases) e `references/layout-and-type.md` (uma seção). O comportamento
dos scripts e do template não muda.

- Brief: um `DESIGN.md` de uma organização numa fala dada em outra pede a pergunta de qual identidade governa,
  mesmo quando o usuário citou o arquivo. Por quê: num deck de defesa de TCC, o `DESIGN.md` era da empresa do
  autor e o logo do rodapé era da universidade; o usuário pediu a troca com o deck pronto.
- Seção nova *Identity without a DESIGN.md*: derivar do logo e do CSS do site, olhar a captura antes de escolher
  superfícies, trocar a fonte licenciada por uma livre de mesmo modelo, medir os pares e registrar a origem. Por
  quê: o primeiro `DESIGN.md`, feito só da contagem de cores, deu um deck que não lembrava o site, e a capa foi
  refeita depois da captura.
- Passo 6: a versão do Playwright sai do build que o erro de lançamento nomeia (1.58.0 usa o 1208, conferido no
  `browsers.json` do pacote em 20/11/2026). Por quê: o primeiro palpite, 1.57.0, pediu o build 1200.
- Gotcha da impressão: capa em campo de cor precisa da mesma regra de duas classes da capa com foto.

## [1.6.1] — 2026-11-18

### A foto da capa se mede, o diagrama da fonte se redesenha, e a ideia visual do original fica

Só `references/layout-and-type.md` muda. O `SKILL.md` está a 19.210 chars, perto do teto, e a reference é lida
ao compor as lâminas. O comportamento dos scripts e do template não muda.

- Componente *Photo*: a foto da capa é paisagem, com pelo menos a largura do palco (1920 px), em tela cheia e com
  o véu sobre a lâmina inteira. Por quê: num deck de plano de negócios, uma foto retrato de 426×945 px esticada
  numa faixa de 680×1080 px, com o véu até 48% dela, mostrou riscos no fade, e o usuário reprovou a capa. As
  capas que ele apontou como boas, de dois decks anteriores, usam foto paisagem de 1920 px com véu inteiro.
- Componente novo *Source diagram*: organograma ou fluxo que vem como imagem dentro do deck de origem é
  redesenhado em HTML. Por quê: no mesmo deck, o organograma de 1600×1062 px, mostrado a 1232 px de largura, deixou
  os nomes ilegíveis, e o usuário reprovou a lâmina.
- Seção nova *Redesigning someone else's slide*: nomear a ideia visual da lâmina de origem e mantê-la. Por quê:
  a seta em curva ascendente da origem virou uma linha reta com pontos, e o usuário achou a lâmina menos
  interessante que a original.

As três falhas foram observadas em 18/11/2026, na revisão do deck pelo usuário. A correção da capa tem os dois
decks anteriores como prova. As do diagrama e da ideia visual foram planejadas e ainda não capturadas: a
confirmar na execução do plano daquele deck.

A mesma revisão pediu para tirar o azul de um gráfico. O componente *Chart* já dizia "one series, one hue" e
destacar só a barra que importa; nada mudou ali.

## [1.6.0] — 2026-11-10

### O rodapé some na lâmina escura, e o PDF de uma parte com as notas

- `assets/deck-template.html`: a lâmina com a classe `dark` (o fechamento sobre a foto) põe `dark-mode` no palco, e o
  rodapé some como na capa. Por quê: num deck de treinamento, o fechamento escuro com foto, que a skill recomenda,
  mostrou o logo, a linha de progresso e o número da página por cima da foto, porque o motor só escondia o rodapé na
  capa. Visto vermelho numa cópia da amostra com uma lâmina `.dark` (o `check-fit` não a listava em "sem rodapé") e
  verde depois ("sem rodapé: 1, 9"); `check-fit` e `check-presenter` verdes na amostra.
- `references/engine.md`, seção *One part with its notes*: a receita para dar a uma parte do deck um PDF com a nota
  embaixo de cada lâmina (`?part=N&notes` antes do motor, `@page` mais alto só nesse modo, `min-height` para nota longa
  virar página a mais), as três provas e a armadilha de a classe do `<body>` ser a do bloco, que deu um PDF de uma
  página em branco com saída 0. Por quê: o treinamento em que a parte 1 é repassada por outros pedia isso, e a skill
  não tinha como. O trecho de código foi rodado na amostra do template.
- `references/layout-and-type.md`, componente *Screenshot*: recortar a captura até a parte que a lâmina comenta.
  Por quê: a seção do formulário reduzida a uma coluna deixou a letra com 10 a 12 px no palco, medida na captura.
- `SKILL.md`: um gotcha e um item no passo 8, que apontam para o detalhe.

## [1.5.2] — 2026-11-05

### Apelidos de projeto saem do texto

Os apelidos de projeto da limpeza anterior saem do texto, também nas entradas antigas deste arquivo.
Onde a frase dependia do nome, ficou um termo genérico. As medições continuam valendo. O comportamento não muda.

## [1.5.1] — 2026-11-04

### Dados da empresa saem do texto

Nome da empresa, repositórios privados, hosts, e-mails, chaves de ticket, IDs de instância e marca da
instalação de origem viram substitutos fixos (`Acme`, `acme.example`, `QUO-…`), também nas
entradas antigas deste arquivo. As medições continuam valendo, sem identificar a origem. O comportamento não muda.

## [1.5.0] — 2026-11-03

### Added
- `scripts/check-fit.mjs`: fails when a slide leaves the window, clips text, runs under its source line or enters the
  footer, and exits 2 when it could not measure. Why: in the Portal deck a request that wrapped to 2 lines put the
  `.act` box 20 px into the footer with `build.py`, `shoot.sh`, `check-presenter` and the deck's secrecy check green.
  The deck's first sensor had two holes, reproduced in its code review: it answered "ok" on zero slides, and an SVG
  in the footer of slide 3 came out green. This version counts whatever paints and proves it reached each slide. Red
  on an SVG, an image and a box in the footer, on text outside the slide and on the real 2-line defect; 2 on zero slides
  and on a deck that ignores the hash; green on the Portal deck and on the template sample.
- `check-presenter.mjs`: four checks on the popup's keys and on a malformed message, each seen red on the 1.4.3
  template.

### Fixed
- Template: Enter and Space on a focused button belong to the button, and a mouse click on a popup button drops its
  focus. Why: on the 1.4.3 template, Enter on "Zerar cronômetro" advanced without resetting, and Space on "← Anterior"
  advanced. `:focus-visible` does not work here: the first attempt failed its own check, because the key press itself
  turns it on.
- Template: a message whose `deck` is not an integer is ignored. Why: `NaN` passed `typeof … === 'number'` and left
  the deck with no active slide and a script error. Seen only with a crafted message; the fix is one word.

### Not included
- The deck's pixel contrast sensor (457 texts): it caught no defect, and the gotchas here are real failures.
- The deck's `check-sigilo.sh` is not part of this skill, so its findings stay in that deck's review.

### Debt
- `docs/codex/smokes.json` still records the smoke of 1.4.0, as it has since 1.4.1. Not redone here.

## [1.4.3] — 2026-11-03

### Fixed
- `shoot.sh` measures the browser bar with a screenshot of a marker at the bottom of the viewport, the same mode as
  the captures, instead of `--dump-dom`. Why: from Chrome 153, `--dump-dom` still reports `innerHeight` 993 in a
  1920×1080 window, but `--screenshot` uses the whole window. Measured on 03/11/2026 with the probe page: Chrome 145
  captures 993 rows, 153 and 156 capture 1080. Compensating 87 px on 156 moved the stage 44 px down and cut the
  footer in every shot of the Portal deck, though the PDF was fine. With the new measure, the 27 slide shots
  and the 2 laptop shots of that deck are pixel-identical to Playwright shots at the exact viewport: the mean
  difference is 0.00, against 16.0 to 31.8 with the old `shoot.sh`. Without Pillow, `shoot.sh` keeps the
  `--dump-dom` measure.
- Template: `.item .chip{align-self:flex-start}`. Why: in the item's flex column a status chip stretched to the
  full width of the column (Portal deck, slide 2).
- `SKILL.md` "Deliver": the cover page carries only `01 / TT`, not the classification, because the engine adds no
  prefix on slide 1. The template's cover credit placeholder now asks for the classification.

### Added
- Gotcha "Cover title over its metadata": the cover places its blocks at fixed `top` values, and a hero title
  that gains a line runs over the line and the metadata.
- `references/layout-and-type.md`: "Generated diagram" (a legend written outside it restates its semantics; the
  Archify decline is also dashed) and "Photo" (license, credit, and the record in `material/`).
- The gotcha on the builder's review now says a design critique does not replace the independent review (5 factual
  errors after two rounds and an impeccable critique, Portal deck).

## [1.4.2] — 2026-11-03

### Fixed
- `check-presenter.mjs` reads the N panel clock from the first `<span>` of the bar instead of the word "decorrido".
  Why: the Portal deck is in English, and the template with only that word translated crashed the check with
  `TypeError: Cannot read properties of undefined (reading 'slice')`; the original template passed. Both pass now,
  and a bar without the elapsed span fails the three clock checks instead of crashing.
- `SKILL.md` metadata version was still `1.4.0` after the 1.4.1 release; it now follows `plugin.json`.

### Added
- Gotcha "Deck in another language": the engine strings ship in Portuguese; translate at least the key hint and the
  tip label, which the audience sees.

## [1.4.1] — 2026-10-22

Distribuição individual no catálogo Codex após instalação isolada, descoberta e smoke seguro de entrada dos workflows. Conteúdo canônico compartilhado com Claude Code/Cursor. Requisitos e limites em `docs/codex/compatibility.md` na raiz do marketplace.

## [1.4.0] — 2026-10-19

### Added
- Hover tips in the template. `data-tip="…"` shows a translation (label in `data-tip-label`); `data-g="key"` shows
  the entry `<p id="g-key">` of a hidden `#glossario` block, so one definition serves every slide that names the
  term. The box lives inside the stage (it scales with it and is clamped to it), uses the deck's own tokens
  (`--dark`, `--dark-fg`, `--dark-accent`, a dotted `--fg3` underline), closes on every slide change, hides the key
  hint while open, and disappears in print. Why: in the Farel deck the presenter's questions after reading the
  slides (who Beza was, what a colophon is, what the French titles mean) became 20 glossary entries, and the slides stayed as
  clean as before; translations of a 10-line poem were shown line by line during the talk.
- `build.py` fails on a `data-g` with no glossary entry (the box would open empty) and warns on an entry nothing
  uses. Comments don't count: the template's CSS comment cites an example key.
- `check-presenter.mjs`: on a deck with tips, the first tip must open with text inside the stage and close when the
  mouse leaves (prints "pulado" otherwise).
- `references/layout-and-type.md` (when to use a tip, and when not: nothing essential only in a tip, the PDF hides
  it) and `references/engine.md` (contract and behavior).

### Fixed
- The "occasional timeout" on the reopened popup that 1.3.1 left open is a race in `check-presenter`: `P` pressed
  right after `close()` reached the window still closing, and no popup opened. The Farel deck failed 3 of 3 runs,
  also with the tip code removed, and passed 18/18 with 300 ms of wait; the check now waits.

## [1.3.1] — 2026-10-19

### Fixed
- The stage fills the screenshots. In `--headless=new`, `--window-size` is the outer window and 87 px go to the
  browser bar (a 1920×1080 window gave a 1920×993 viewport on Chromium 130 and 145), so every shot showed the stage
  at ~0.92 with dark bands. `shoot.sh` measures the real viewport once, opens each window that much taller and crops
  the PNG back (Pillow or ImageMagick; one warning without either). On the template sample and the Farel deck the
  dark border went from 100% to 0% in every slide and laptop shot.
- `shoot.sh` finds Playwright's newer Chromium builds, which live in `chrome-linux64/`; the `chrome-linux/` glob only
  found `chromium-1140`.
- Reduced motion turns off every transition, not only the `.enter` animation. `shoot.sh` captures with
  `--force-prefers-reduced-motion`, and "[CONCLUSÃO]" was shot mid-fade over "[PARTE 3]": the text pixels in its
  strip went from 402 to 0 with the transition off.
- Footer labels are measured after the first slide is shown and again on `document.fonts.ready`, as a project deck
  already did. Before, the page number was still empty (line 1366 px wide instead of 1281) and a self-hosted font
  still loading (fallback widths 117 px instead of 105–109).

### Added
- `check-presenter.mjs`: two checks in a tab with reduced motion, as `shoot.sh` opens the deck: no transition still
  running, and the hidden footer labels are the colliding ones. Red on the 1.3.0 template (the transition check on
  the sample; both on a test deck whose first section label sits 11 px from the next), green on 1.3.1 (16 checks on
  the sample, that test deck and a self-hosted-font variant).

### Why
The debt 1.3.0 left open. Its diagnosis was half right: the overlap seen on the sample was a transition caught
mid-way, not the font; the font and the page number were real but latent errors, since the sample's labels collide
by a wide margin.

### Known debt (not changed here)
- `check-presenter.mjs` sometimes times out waiting for the reopened popup: 1 run in 3 on the Farel deck, with the
  1.3.0 check as well. Rerun once before reading it as a regression.
- Existing decks keep their own engine: the Farel deck fails the new reduced-motion check (75 elements still
  transition) until the rule is ported.

## [1.3.0] — 2026-10-19

### Added
- Reveal by clicks: `data-steps="N"` on a `<section>` and `data-step="1..N"` on its blocks. Arrows, click, swipe
  and the popup's buttons reveal the next step before changing slide; going back lands fully revealed. Messages
  carry `{deck, step, t0, gen}` and the popup shows "etapa s/N". Unrevealed blocks get `.later` (transparent,
  space kept); the PDF prints every step revealed. The hash stays `#N`, because `check-presenter.mjs` reads it;
  `#N.s` opens on a step, for screenshots.
- `check-presenter.mjs`: three step checks when the deck has `data-steps` ("pulado" otherwise). Red on the 1.2.1
  engine (3 failures), green on 1.3.0 (17 checks) on the template and on the Farel deck. Its error and header
  explain a local Playwright with `NODE_PATH`.
- `shoot.sh` on WSL without Chrome, `pdfinfo` or ImageMagick: Playwright's cached Chromium, a `/Type /Page`
  count, and Pillow contact sheets (or a warning). Before, the sheets the inspection step asks for vanished
  without a word. Checked with the default PATH: 8 slides, 8 pages, 2 sheets.
- `SKILL.md`: a requirements file that does not fit the subject (another course's guidelines, a second
  `DESIGN.md`) means ask which governs; with the `impeccable` skill, the direction contract goes in its surface
  brief, not in a comment that `build.py` ships to `dist/`.

### Why
A 10-minute HE II seminar deck on Guilherme Farel (19/10/2026), presented over Zoom. Its key moment, an acrostic
hidden in the 1535 Olivétan Bible colophon, needed a two-step reveal the template did not have. The prompt carried
the wrong course's guidelines and a package `DESIGN.md` the user overruled. Playwright was not installed globally,
and WSL had no Chrome, `pdfinfo` or `montage`.

### Known debt (not changed here)
- On the template's own sample, the footer labels "[PARTE 3]" and "[CONCLUSÃO]" still overlap: the `.tight`
  measure runs before the font loads. A project deck already re-measures on `document.fonts.ready`.
- Headless screenshots show the stage at ~0.93 with dark bands (the headless window reserves height). Not yet
  measured; the reviewer packet should say so.

## [1.2.1] — 2026-10-16

### Fixed
- The key hint never shows while the presenter window is open. On 1.2.0 it faded 2.5 s after the mouse
  stopped, but a mouse crossing the deck on its way to the popup still flashed it to the audience of a shared
  window. Without the popup (rehearsal) it behaves as before. `check-presenter.mjs` gained the check (red on
  1.2.0, green on 1.2.1) and now has 14.

### Why
The residue the 1.2.0 QA retest left open on the Manutenção Proativa deck (REP-929): the user chose "hide the hint
while the presenter window is open" over "only on the cover" and "accept".

## [1.2.0] — 2026-10-16

### Fixed
- Presenter window and deck share the clock. Messages carry `{deck, t0, gen}`: `R` in either window (or the
  popup's button) resets both, and a reopened popup or a reloaded deck keeps the time already spoken. Before,
  `R` reset only the window where it was pressed, and a reopened popup showed 00:00 minutes into the talk.
- A reloaded deck relinks the popup by itself. The popup sends a hello every second, and the deck answers
  once with its slide. Before, after an F5 the popup stopped following the deck, and the popup's arrows made
  the projector skip a slide.
- The key hint fades 2.5 s after the mouse stops, instead of staying while the mouse is over the page. In a
  call, the shared window showed it the whole time on a one-screen laptop.
- A click that only brings the deck window forward (within 400 ms of focus) and a click outside the stage
  no longer navigate; the left third is measured on the stage.

### Added
- `scripts/check-presenter.mjs`: Playwright regression check for the engine (13 checks). It failed 9 of
  them on the 1.1.1 engine and passes on 1.2.0, headless and headed.
- `build.py` warns, without failing, when a note read at 150 words per minute (`--wpm`) needs 5 s or more
  beyond its `data-t`; a number counts as two words and a date as three. On the four existing decks it flags
  only the slide that needed it.
- Gotchas: what a shared window shows in a call, the focus click, and engine fixes that must be ported by
  hand to each deck. `references/engine.md` documents the shared timer and the regression check.

### Why
A `/qa-execution` round on the Manutenção Proativa deck (REP-929, 16/10/2026) walked the presenter journeys in
persona and filed six findings against the template's engine and the build gate. Each fix was red before and
green after on the same check; the activation click was also measured with a real X11 click on plain Chrome,
since Playwright's focus emulation hides it.

## [1.1.1] — 2026-10-01

### Fixed
- Gotcha "Photo or dark slide lost in the PDF" now warns that print also takes `.slide::after` (the
  `data-print` footer). A cell-group deck drew its cover's dawn glow with `::after`; one combined print rule
  (`content:attr(data-print)` over the glow, `inset:0`) kept both, checked on page 1 of the PDF.

## [1.1.0] — 2026-09-30

### Added
- PowerPoint sources (step 2): `python-pptx` for text and speaker notes, `soffice` → PDF → MinerU for the
  layout. The PDF export drops the notes, and in the IACS E26/E27 deck they held a whole slide's talk.
- `references/layout-and-type.md`: an **Agenda** component whose minutes come from the `data-t` of each
  section, and a **References appendix** (citation standard such as ABNT NBR 6023:2018, reading slides after
  the close, each URL checked with `curl` before its "Acesso em").
- Gotchas: glyph missing from the self-hosted font (`≠ → ←`), photo or dark slide lost in the PDF (print
  rules repaint `.slide` and reuse `.slide::before`), the same image inlined once per `url()` (1.7 MB →
  569 KB with one `--photo` variable), and the `.src` line running under content that grows.

### Changed
- "Footer collisions" now says to keep section names to about 12 characters.
- The action block is for actions only; objectives and claims go in the lead or on a line with a brand bar.

### Why
Second real deck built with the skill: a 30-minute technical training on IACS UR E26/E27 from a PPTX
(25 slides, room + Meet + PDF). Every item above failed or was fixed during that session. The print-CSS
failure was reproduced without the fix before it was written down.

## [1.0.1] — 2026-09-30

### Fixed
- `plugin.json` no longer declares `"agents": "./agents"`. With that field, `claude plugin install` failed
  with `Validation errors: agents: Invalid input`; the `agents/` directory is discovered automatically,
  as in the official plugins (e.g. `coderabbit`). The template in this repo's `CLAUDE.md` still shows the
  field, which is where the mistake came from.

## [1.0.0] — 2026-09-30

### Added
- Skill `html-presentation`: workflow brief → source to Markdown → talk plan with a time budget per slide →
  design from the project's `DESIGN.md` → build → two inspection rounds → independent review → deliver
  (HTML, PDF, speaker script).
- `assets/deck-template.html`: 1920×1080 engine with the footer progress line by section, notes panel,
  presenter window with timer, print CSS with `classification · section · page`, and sample slides for
  each component.
- `scripts/build.py` (inline assets, generate the script from the notes, gates for offline, notes and time
  budget) and `scripts/shoot.sh` (screenshots with retry and reduced motion, laptop views, PDF page-count
  check, contact sheets).
- Agent `deck-reviewer`: a read-only independent review with a verdict and exact fixes.
- `evals/evals.json` + synthetic inputs: 2 cases (10-min training from a PDF, 8-min board report with a DESIGN.md). First iteration: with the skill 17/17 checks, without 12/17 (no speaker script in either run, no PDF in one).

### Why
Extracted from a real 15-minute training deck. Every gotcha in `SKILL.md` is a failure that happened while
building it: the stage clipped on laptops, faded headless captures, stale screenshots, presenter sync on
`file://`, footer collisions, and six material content losses that only the fresh reviewer caught.
