// Regra: a 390 x 844, com toque, cada alvo abaixo tem 44 x 44 px ou mais:
//   - os links do rodapé (nav.rodape a);
//   - os atalhos do topo (.atalhos a) e os links para o glossário (a.no-glossario);
//   - as opções do quiz (.pergunta button.opcao) e os summary dos details;
//   - os links para âncora num parágrafo com três ou mais deles.
// Página sem nenhum desses alvos passa e diz isso.
// Uso: NODE_PATH=<bancada>/pw/node_modules node alvo-de-toque-pequeno.js <página.html>...
const { chromium } = require('playwright');
const path = require('path');
const { pathToFileURL } = require('url');
const MINIMO = 44;
(async () => {
  const paginas = process.argv.slice(2);
  if (!paginas.length) { console.error('uso: alvo-de-toque-pequeno.js <página.html>...'); process.exit(2); }
  const b = await chromium.launch();
  let falhas = 0;
  for (const pagina of paginas) {
    const p = await b.newPage({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true });
    await p.route(u => u.protocol !== 'file:', r => r.abort());
    await p.goto(pathToFileURL(path.resolve(pagina)).href, { waitUntil: 'domcontentloaded' });
    await p.waitForTimeout(300);
    const r = await p.evaluate(() => {
      const alvos = new Set(document.querySelectorAll('nav.rodape a, .atalhos a, a.no-glossario, .pergunta button.opcao, details > summary'));
      document.querySelectorAll('p').forEach(par => {
        const ancoras = Array.from(par.children).filter(a => a.matches('a[href^="#"]'));
        if (ancoras.length >= 3) ancoras.forEach(a => alvos.add(a));
      });
      return Array.from(alvos).map(a => {
        const q = a.getBoundingClientRect();
        return { t: a.textContent.trim().slice(0, 24), w: Math.round(q.width), h: Math.round(q.height) };
      });
    });
    const pequenos = r.filter(a => a.w < MINIMO || a.h < MINIMO);
    const ok = pequenos.length === 0;
    if (!ok) falhas++;
    const menorH = r.length ? Math.min(...r.map(a => a.h)) : null;
    console.log(`${ok ? 'PASS' : 'FAIL'} ${path.basename(pagina)}: ${r.length ? `${r.length} alvos, menor altura ${menorH} px` : 'sem alvos'}${ok ? '' : ' -> ' + pequenos.slice(0, 6).map(a => `"${a.t}" ${a.w}x${a.h}`).join('; ') + (pequenos.length > 6 ? ` (+${pequenos.length - 6})` : '')}`);
    await p.close();
  }
  await b.close();
  process.exit(falhas ? 1 : 0);
})();
