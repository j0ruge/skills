// Regra dos diagramas: todo desenho é legível em qualquer largura, e a página nunca rola de lado por causa dele.
//   <script src="../assets/textos.js"></script> <script src="../assets/diagramas.js"></script>
// Os Mermaid vêm do jsDelivr (versão 11.4.1) por async: o texto e o quiz funcionam enquanto a rede
// demora, e também quando ela falha. Sem rede, o desenho aparece como texto. O texto ao lado de cada
// diagrama diz o mesmo, de propósito: a página continua legível sem ele.
//
// Tamanho legível: cada desenho, Mermaid ou SVG feito à mão dentro de <figure class="diagrama">, cabe
// primeiro na largura do quadro. Se assim o menor texto fica abaixo de LIMITE px na tela, o desenho
// recebe uma largura mínima que leva esse texto a MENOR_TEXTO px. Então ele rola de lado dentro do
// próprio quadro, com uma dica acima dele (p.dica-rolagem), e a página não rola. A conta se refaz
// quando a janela muda de largura. Um desenho muito largo rola também no notebook.
// As cores do tema Mermaid vêm dos tokens do estudo.css, lidos na hora; a frase da dica vem do textos.js.
(function () {
  'use strict';

  var T = window.GUIA_TEXTOS;
  if (!T) {
    console.error('GUIA_TEXTOS ausente: carregue assets/textos.js antes do diagramas.js.');
    return;
  }

  var URL_MERMAID = 'https://cdn.jsdelivr.net/npm/mermaid@11.4.1/dist/mermaid.min.js';
  var LIMITE = 11;
  var MENOR_TEXTO = 12;
  var DICA = T.dicaRolagem;
  var desenhos = [];   // { svg, quadro, largura do viewBox, menor fonte }

  // Menor fonte do desenho, em unidades do viewBox (o px de dentro do SVG).
  function menorFonte(svg) {
    var folhas = svg.querySelectorAll('foreignObject span, foreignObject div, foreignObject p, text, tspan');
    var menor = 0;
    for (var k = 0; k < folhas.length; k++) {
      var e = folhas[k];
      if (!e.textContent.trim() || e.querySelector('span, div, p, tspan')) continue;
      var f = parseFloat(window.getComputedStyle(e).fontSize);
      if (f > 0 && (!menor || f < menor)) menor = f;
    }
    return menor;
  }

  function atualizarRolagem(quadro) {
    var rola = quadro.scrollWidth > quadro.clientWidth + 1;
    var dica = quadro.previousElementSibling;
    var temDica = dica && dica.classList.contains('dica-rolagem');
    quadro.classList.toggle('rola', rola);
    if (rola) {
      quadro.setAttribute('tabindex', '0');
      quadro.setAttribute('role', 'region');
      quadro.setAttribute('aria-label', DICA);
      if (!temDica) {
        dica = document.createElement('p');
        dica.className = 'dica-rolagem';
        dica.setAttribute('aria-hidden', 'true');
        dica.textContent = DICA;
        quadro.parentNode.insertBefore(dica, quadro);
      }
    } else {
      quadro.removeAttribute('tabindex');
      quadro.removeAttribute('role');
      quadro.removeAttribute('aria-label');
      if (temDica) dica.parentNode.removeChild(dica);
    }
  }

  // Mede o desenho já encaixado no quadro e, se o menor texto fica abaixo de LIMITE, dá a largura mínima.
  function ajustar(d) {
    d.svg.style.minWidth = '';
    if (d.largura && d.fonte) {
      var naTela = d.fonte * d.svg.getBoundingClientRect().width / d.largura;
      if (naTela < LIMITE) d.svg.style.minWidth = Math.floor(d.largura * MENOR_TEXTO / d.fonte) + 'px';
    }
    atualizarRolagem(d.quadro);
  }

  // Põe o desenho num quadro que rola (o <pre> do Mermaid, ou um <div> criado em volta do SVG feito
  // à mão) e faz o primeiro ajuste.
  function tornarLegivel(svg) {
    for (var k = 0; k < desenhos.length; k++) if (desenhos[k].svg === svg) return;
    var vb = svg.viewBox && svg.viewBox.baseVal;
    var quadro = svg.parentNode;
    if (quadro.tagName !== 'PRE' && !quadro.classList.contains('rolagem')) {
      var envoltorio = document.createElement('div');
      envoltorio.className = 'rolagem';
      quadro.insertBefore(envoltorio, svg);
      envoltorio.appendChild(svg);
      quadro = envoltorio;
    }
    var d = { svg: svg, quadro: quadro, largura: vb ? vb.width : 0, fonte: menorFonte(svg) };
    desenhos.push(d);
    ajustar(d);
  }

  var agendado = false;
  window.addEventListener('resize', function () {
    if (agendado) return;
    agendado = true;
    window.requestAnimationFrame(function () {
      agendado = false;
      desenhos.forEach(ajustar);
    });
  });

  // SVG feito à mão: já está na página.
  Array.prototype.slice.call(document.querySelectorAll('figure.diagrama > svg[viewBox]')).forEach(tornarLegivel);

  if (!document.querySelector('.mermaid')) return;

  // Lê um token de cor do estudo.css; usa o padrão se a folha não o define.
  function token(nome, padrao) {
    var v = window.getComputedStyle(document.documentElement).getPropertyValue(nome).trim();
    return v || padrao;
  }

  function desenhar() {
    if (typeof window.mermaid === 'undefined') return;
    window.mermaid.initialize({
      startOnLoad: false,
      theme: 'base',
      securityLevel: 'strict',
      fontFamily: token('--sans', 'sans-serif'),
      flowchart: { htmlLabels: true, curve: 'basis', useMaxWidth: true },
      themeVariables: {
        primaryColor: token('--marca-fundo', '#e2f0f1'),
        primaryBorderColor: token('--marca', '#0f7480'),
        primaryTextColor: token('--texto', '#2b2b2b'),
        secondaryColor: token('--destaque-fundo', '#fdf3d3'),
        tertiaryColor: token('--verde-fundo', '#e4f2e8'),
        lineColor: token('--marca-texto', '#0a5560'),
        fontSize: '16px'
      }
    });
    var feito = window.mermaid.run({ querySelector: '.mermaid' });
    var depois = function () {
      Array.prototype.slice.call(document.querySelectorAll('figure.diagrama pre.mermaid > svg')).forEach(tornarLegivel);
    };
    if (feito && typeof feito.then === 'function') feito.then(depois, depois);
    else depois();
  }

  if (typeof window.mermaid !== 'undefined') { desenhar(); return; }
  var s = document.createElement('script');
  s.src = URL_MERMAID;
  s.async = true;
  s.onload = desenhar;
  document.head.appendChild(s);
})();
