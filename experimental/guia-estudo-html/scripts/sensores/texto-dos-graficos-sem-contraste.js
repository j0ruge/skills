// Regra: todo texto de SVG feito à mão (dentro de figure.diagrama, fora do Mermaid) tem contraste de 4,5:1
// ou mais contra o que está atrás dele, inclusive os rótulos em negrito.
// Cor do texto: o fill computado. Fundo: a forma do mesmo SVG sob o centro do texto (elementsFromPoint),
// misturada pela opacidade sobre o fundo do quadro; sem forma, o fundo do quadro.
// O quadro do desenho fica claro também no escuro forçado (color-scheme: only light), então basta o claro.
// Página sem SVG feito à mão passa e diz isso.
// Uso: NODE_PATH=<bancada>/pw/node_modules node texto-dos-graficos-sem-contraste.js <página.html>...
const { chromium } = require('playwright');
const path = require('path');
const { pathToFileURL } = require('url');
const MINIMO = 4.5;
(async () => {
  const paginas = process.argv.slice(2);
  if (!paginas.length) { console.error('uso: texto-dos-graficos-sem-contraste.js <página.html>...'); process.exit(2); }
  const b = await chromium.launch();
  let falhas = 0;
  for (const pagina of paginas) {
    const p = await b.newPage({ viewport: { width: 1366, height: 768 } });
    await p.route(u => u.protocol !== 'file:', r => r.abort());
    await p.goto(pathToFileURL(path.resolve(pagina)).href, { waitUntil: 'load' });
    await p.waitForTimeout(300);
    const r = await p.evaluate((MINIMO) => {
      const rgb = s => (s.match(/[\d.]+/g) || []).map(Number);
      const lum = ([r, g, b]) => { const f = c => { c /= 255; return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4); }; return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b); };
      const mistura = (cima, alfa, baixo) => cima.map((c, k) => alfa * c + (1 - alfa) * baixo[k]);
      const hex = c => '#' + c.map(v => Math.round(v).toString(16).padStart(2, '0')).join('');
      const svgs = Array.from(document.querySelectorAll('figure.diagrama svg')).filter(s => !s.closest('pre.mermaid') && !s.parentElement.closest('svg'));
      const achados = [];
      let textos = 0, pior = 99, qual = '';
      svgs.forEach((svg, i) => {
        let a = svg.parentElement, quadro = [255, 255, 255];
        while (a) { const v = rgb(getComputedStyle(a).backgroundColor); if (v.length >= 3 && !(v.length === 4 && v[3] === 0)) { quadro = v.slice(0, 3); break; } a = a.parentElement; }
        svg.querySelectorAll('text, tspan').forEach(t => {
          if (!t.textContent.trim() || t.querySelector('tspan')) return;
          const s = getComputedStyle(t);
          if (s.fill === 'none' || s.visibility === 'hidden') return;
          t.scrollIntoView({ block: 'center', inline: 'center' });
          const q = t.getBoundingClientRect();
          if (!q.width || !q.height) return;
          let fundo = quadro;
          const sob = document.elementsFromPoint(q.left + q.width / 2, q.top + q.height / 2)
            .find(e => e !== t && !e.closest('text') && svg.contains(e) && e !== svg && /^(rect|circle|ellipse|polygon|path)$/.test(e.tagName));
          if (sob) {
            const fs = getComputedStyle(sob);
            if (fs.fill !== 'none') {
              const alfa = parseFloat(fs.fillOpacity) * parseFloat(fs.opacity);
              fundo = mistura(rgb(fs.fill).slice(0, 3), alfa, quadro);
            }
          }
          const cor = mistura(rgb(s.fill).slice(0, 3), parseFloat(s.fillOpacity) * parseFloat(s.opacity), fundo);
          const l1 = lum(cor), l2 = lum(fundo);
          const cr = (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);
          textos++;
          if (cr < pior) { pior = cr; qual = t.textContent.trim().slice(0, 30); }
          if (cr < MINIMO) achados.push(`desenho ${i + 1}, "${t.textContent.trim().slice(0, 30)}" ${hex(cor)} contra ${hex(fundo)}: ${cr.toFixed(2)}:1`);
        });
      });
      return { svgs: svgs.length, textos, pior, qual, achados };
    }, MINIMO);
    if (r.svgs && !r.textos) r.achados.push('nenhum texto medido nos SVG');
    const ok = r.achados.length === 0;
    if (!ok) falhas++;
    console.log(`${ok ? 'PASS' : 'FAIL'} ${path.basename(pagina)}: ${r.svgs ? `${r.svgs} gráficos, ${r.textos} textos, pior ${r.pior.toFixed(2)}:1 ("${r.qual}")` : 'sem gráfico em SVG feito à mão'}${ok ? '' : ' -> ' + r.achados.slice(0, 5).join('; ') + (r.achados.length > 5 ? ` (+${r.achados.length - 5})` : '')}`);
    await p.close();
  }
  await b.close();
  process.exit(falhas ? 1 : 0);
})().catch(e => { console.log('FAIL erro do sensor: ' + String((e && e.message) || e).split('\n')[0]); process.exit(1); });
