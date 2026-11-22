// Regra: com o escuro forçado do Chromium (--blink-settings=forceDarkModeEnabled=true e colorScheme dark),
// o texto de cada rótulo Mermaid tem contraste de 3:1 ou mais contra o fundo da própria caixa, medido nos
// pixels da tela (o escuro forçado age na pintura; o estilo computado não muda).
// Fundo = mediana da luminância da área do rótulo; texto = o pixel mais distante dela.
// Cada rótulo vem à vista antes da captura, porque o desenho largo rola dentro do quadro.
// O fundo da página tem de sair escuro: é a prova de que o escuro forçado pegou.
// Página sem Mermaid passa e diz isso. Precisa de rede para o Mermaid.
// Uso: NODE_PATH=<bancada>/pw/node_modules node mermaid-ilegivel-no-escuro-forcado.js <página.html>...
const { chromium } = require('playwright');
const { PNG } = require('playwright-core/lib/utilsBundle');
const path = require('path');
const { pathToFileURL } = require('url');
const MINIMO = 3;
const lum = (r, g, b) => { const f = c => { c /= 255; return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4); }; return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b); };
(async () => {
  const paginas = process.argv.slice(2);
  if (!paginas.length) { console.error('uso: mermaid-ilegivel-no-escuro-forcado.js <página.html>...'); process.exit(2); }
  const b = await chromium.launch({ args: ['--blink-settings=forceDarkModeEnabled=true'] });
  let falhas = 0;
  for (const pagina of paginas) {
    const ctx = await b.newContext({ viewport: { width: 1366, height: 768 }, colorScheme: 'dark' });
    const p = await ctx.newPage();
    await p.goto(pathToFileURL(path.resolve(pagina)).href, { waitUntil: 'networkidle' });
    const blocos = await p.$$eval('pre.mermaid', x => x.length);
    const desenhou = await p.waitForFunction(() => Array.from(document.querySelectorAll('pre.mermaid'))
      .every(x => x.querySelector('svg')), null, { timeout: 20000 }).then(() => true, () => false);
    await p.waitForTimeout(500);
    const achados = [];
    let pior = 99, qual = '', rotulos = 0;
    if (blocos) {
      const topo = PNG.sync.read(await p.screenshot({ clip: { x: 0, y: 0, width: 8, height: 8 } }));
      if (lum(topo.data[0], topo.data[1], topo.data[2]) > 0.2) achados.push('o escuro forçado não pegou: o fundo da página saiu claro');
      const folhas = await p.$$('pre.mermaid svg foreignObject span, pre.mermaid svg foreignObject div, pre.mermaid svg foreignObject p, pre.mermaid svg text, pre.mermaid svg tspan');
      for (const e of folhas) {
        const c = await e.evaluate(el => {
          if (!el.textContent.trim() || el.querySelector('span, div, p, tspan')) return null;
          el.scrollIntoView({ block: 'center', inline: 'center' });
          const r = el.getBoundingClientRect();
          return { x: r.left, y: r.top, w: r.width, h: r.height, t: el.textContent.trim().slice(0, 30) };
        });
        if (!c || c.w <= 4 || c.h <= 4) continue;
        const img = PNG.sync.read(await p.screenshot({ clip: { x: c.x, y: c.y, width: c.w, height: c.h } }));
        const ls = [];
        for (let k = 0; k < img.width * img.height; k++) ls.push(lum(img.data[4 * k], img.data[4 * k + 1], img.data[4 * k + 2]));
        if (!ls.length) continue;
        rotulos++;
        const fundo = ls.slice().sort((a, z) => a - z)[Math.floor(ls.length / 2)];
        let texto = fundo; for (const l of ls) if (Math.abs(l - fundo) > Math.abs(texto - fundo)) texto = l;
        const cr = (Math.max(texto, fundo) + 0.05) / (Math.min(texto, fundo) + 0.05);
        if (cr < pior) { pior = cr; qual = c.t; }
      }
      if (!desenhou) achados.push('o Mermaid não desenhou em 20 s (sem rede?)');
      if (desenhou && !rotulos) achados.push('nenhum rótulo medido (todos menores que 4 px ou sem texto)');
      if (pior < MINIMO) achados.push(`rótulo "${qual}" com contraste ${pior.toFixed(2)}:1`);
    }
    const ok = achados.length === 0;
    if (!ok) falhas++;
    console.log(`${ok ? 'PASS' : 'FAIL'} ${path.basename(pagina)}: ${blocos ? `${rotulos} rótulos, pior contraste ${pior.toFixed(2)}:1` : 'sem Mermaid'}${ok ? '' : ' -> ' + achados.join('; ')}`);
    await ctx.close();
  }
  await b.close();
  process.exit(falhas ? 1 : 0);
})();
