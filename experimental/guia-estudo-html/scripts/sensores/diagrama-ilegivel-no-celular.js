// Regra: a 390 x 844, o menor texto de cada desenho (Mermaid ou SVG feito à mão, dentro de figure.diagrama)
// tem 11 px ou mais na tela. Desenho mais largo que o quadro rola dentro do quadro, e a página não rola de lado.
// Precisa de rede para o Mermaid; se ele não desenhar em 20 s, a página falha com o motivo.
// Uso: NODE_PATH=<bancada>/pw/node_modules node diagrama-ilegivel-no-celular.js <página.html>...
const { chromium } = require('playwright');
const path = require('path');
const { pathToFileURL } = require('url');
const MINIMO = 11;
(async () => {
  const paginas = process.argv.slice(2);
  if (!paginas.length) { console.error('uso: diagrama-ilegivel-no-celular.js <página.html>...'); process.exit(2); }
  const b = await chromium.launch();
  let falhas = 0;
  for (const pagina of paginas) {
    const p = await b.newPage({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true });
    await p.goto(pathToFileURL(path.resolve(pagina)).href, { waitUntil: 'networkidle' });
    const desenhou = await p.waitForFunction(() => Array.from(document.querySelectorAll('pre.mermaid'))
      .every(x => x.querySelector('svg')), null, { timeout: 20000 }).then(() => true, () => false);
    await p.waitForTimeout(500);
    const r = await p.evaluate((MINIMO) => {
      const achados = [];
      let pior = 99;
      const svgs = Array.from(document.querySelectorAll('figure.diagrama svg')).filter(s => !s.parentElement.closest('svg'));
      let medidos = 0;
      svgs.forEach((svg, i) => {
        const vb = svg.viewBox && svg.viewBox.baseVal;
        if (!vb || !vb.width) return;
        medidos++;
        const rect = svg.getBoundingClientRect();
        const escala = rect.width / vb.width;
        let menor = 99;
        svg.querySelectorAll('foreignObject span, foreignObject div, foreignObject p, text, tspan').forEach(e => {
          if (!e.textContent.trim() || e.querySelector('span, div, p, tspan')) return;
          menor = Math.min(menor, parseFloat(getComputedStyle(e).fontSize) * escala);
        });
        pior = Math.min(pior, menor);
        if (menor < MINIMO) achados.push(`desenho ${i + 1}: menor texto ${menor.toFixed(1)} px`);
        // Mais largo que o quadro: um ancestral tem de rolar de lado.
        const fig = svg.closest('figure');
        const estilo = getComputedStyle(fig);
        const util = fig.clientWidth - parseFloat(estilo.paddingLeft) - parseFloat(estilo.paddingRight);
        if (rect.width > util + 1) {
          let a = svg.parentElement, rola = false;
          while (a && a !== document.body) {
            const ox = getComputedStyle(a).overflowX;
            if ((ox === 'auto' || ox === 'scroll') && a.scrollWidth > a.clientWidth) { rola = true; break; }
            a = a.parentElement;
          }
          if (!rola) achados.push(`desenho ${i + 1}: mais largo que o quadro e sem rolagem`);
        }
      });
      const paginaRola = document.documentElement.scrollWidth - window.innerWidth;
      if (paginaRola > 0) achados.push(`a página rola ${paginaRola} px de lado`);
      return { n: medidos, pior, achados };
    }, MINIMO);
    if (!desenhou) r.achados.push('o Mermaid não desenhou em 20 s (sem rede?)');
    const ok = r.achados.length === 0;
    if (!ok) falhas++;
    console.log(`${ok ? 'PASS' : 'FAIL'} ${path.basename(pagina)}: ${r.n ? `${r.n} desenhos, menor texto ${r.pior.toFixed(1)} px` : 'sem desenho'}${ok ? '' : ' -> ' + r.achados.join('; ')}`);
    await p.close();
  }
  await b.close();
  process.exit(falhas ? 1 : 0);
})();
