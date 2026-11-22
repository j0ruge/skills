# Contrato de marcação

Este arquivo é a interface entre o kit (`assets/`) e os sensores. Eles leem só as classes e os atributos `data-*` daqui, nunca o texto visível. Assim um curso em outra língua passa nos mesmos sensores. As frases da interface ficam só em `assets/textos.js`.

## 1. Tabela do contrato

| Elemento | Marcação |
|---|---|
| Pastas | `index.html`, `lessons/000N-<slug>.html`, `reference/<slug>.html`, `assets/{textos.js,estudo.css,diagramas.js,quiz.js}` |
| Scripts, no fim do `body`, nesta ordem | `textos.js`, `diagramas.js`, `quiz.js`. O `quiz.js` vai em toda página com quiz ou `details` |
| Textos | `window.GUIA_TEXTOS = { idioma, palavrasPorMinuto, certo, aindaNao, negacoes, marcaCerta, marcaSua, placar, aCerta, dicaRolagem, palavraMouse, palavraTracejado, cores }`. `placar` tem `{acertos}`, `{respondidas}` e `{total}`. `cores` mapeia hex minúsculo para o nome da cor. Valores PT-BR de origem: `130`, `'Certo.'`, `'Ainda não.'`, `['Não']`, `'✓ certa'`, `'✗ sua resposta'`, a dica de `diagramas.js` de origem, `'roda'`, `'tracejad'` |
| Cabeçalho da aula | `header.topo > h1`, logo depois `p.atalhos` com `a[data-atalho="indice"]` e `a[data-atalho="glossario"][target="_blank"]`; em `p.meta`, um elemento `[data-minutos="N"]` |
| Índice | cada aula em `li[data-aula="N"]`, com o link para `lessons/000N-...` e um `[data-minutos="N"]` |
| Caixas | `div.caixa`, com um modificador: `ideia`, `cuidado`, `nao-confunda`, `termo`, `exemplo-resolvido`, `exemplo-inventado`, e os blocos que a pesquisa manteve: `objetivo`, `analogia`, `aplique`, `na-fonte`, `pergunte`; rótulo em `span.rotulo` |
| Lembrar | `details.lembrar > summary`: pré-teste, revisão da aula anterior, "lembre sem olhar" |
| Fonte e número | `span.fonte` (fonte e localização), `span.n` (número) |
| Figura | `figure.diagrama` com `pre.mermaid` ou `svg`, e `figcaption`; o quadro que rola recebe `.dica-rolagem` |
| Quiz | `p.placar`; `div.quiz > div.pergunta[data-certa="k"]` com `p.enunciado`, `div.opcoes > button.opcao[data-explica]` e `p.retorno[aria-live="polite"]`. Depois do toque, o `quiz.js` põe `data-resultado="certo"` ou `"errado"` na `.pergunta`, a classe `certa` ou `errada` no botão e um `span.marca` |
| Rodapé | `nav.rodape > a[data-rodape="anterior"]`, `a[data-rodape="indice"]`, `a[data-rodape="proxima"]` |
| Glossário | `a.no-glossario[target="_blank"]` com `href` para `glossario.html#<id>`; cada verbete do glossário tem esse `id` |
| Estado | `sessionStorage`, chave `'guia:' + location.pathname` |

## 2. Os blocos da aula e a classe de cada um

Na ordem do `roteiro-da-aula.md`:

| # | Bloco | Classe |
|---|---|---|
| 1 | Objetivo | `div.caixa.objetivo` |
| 2 | Antes de ler | `details.lembrar` |
| 3 | Revisão da aula anterior | `details.lembrar` |
| 4 | Seção com diagrama | `figure.diagrama` |
| 4a | Termo novo | `div.caixa.termo` |
| 4b | Por quê, e se fosse diferente | `div.caixa.ideia` |
| 4c | Exemplo resolvido, exemplo inventado | `div.caixa.exemplo-resolvido`, `div.caixa.exemplo-inventado` |
| 4d | Analogia | `div.caixa.analogia` |
| 5 | Lembre sem olhar, explique a um colega | `details.lembrar` |
| 6 | Quiz | `div.quiz` |
| 7 | Aplique agora | `div.caixa.aplique` |
| 8 | Para ler na fonte | `div.caixa.na-fonte` |
| 9 | Convite a perguntar | `div.caixa.pergunte` |

Os modificadores `cuidado` e `nao-confunda` ficam fora da ordem. Entram onde o texto pede.

## 3. Interface comum dos sensores

```
NODE_PATH=<bancada>/pw/node_modules node <sensor>.js <página.html>...
```

- Uma linha por página: `PASS <arquivo>: <detalhe>` ou `FAIL <arquivo>: <detalhe>`.
- Sai 0 se tudo passou, 1 se algo falhou, 2 sem argumento.
- Página sem a coisa medida sai `PASS ... sem <coisa>` e rc 0, nunca com exceção.

## 4. Regras do contrato

- O tempo prometido vem de `[data-minutos]`, não da frase "cerca de N minutos".
- O sensor do retorno do quiz lê o estado do botão e o `data-resultado`, não a palavra "Ainda não".
- As palavras por minuto da conta de tempo vêm de `palavrasPorMinuto`, com 130 como padrão para PT-BR. Só o PT-BR fica testado.
- Página que esqueceu o `textos.js`: o `quiz.js` e o `diagramas.js` escrevem `GUIA_TEXTOS ausente` no console.
