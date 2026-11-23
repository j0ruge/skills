// Regra: as caixas <details> abertas vivem na aba (sessionStorage). Em cada página com <details>, a
// 390 x 844 com toque:
//   1. abre as quatro primeiras caixas e a caixa que guarda o primeiro link para outra página;
//   2. toca esse link (sem ele, o primeiro link do rodapé) e volta com o Voltar;
//   3. as mesmas caixas têm de estar abertas, e o link de onde se saiu tem de estar na tela.
// Página sem <details> passa e diz isso.
// Uso: NODE_PATH=<bancada>/pw/node_modules node caixas-fecham-ao-voltar.js <página.html>...
const { chromium } = require('playwright');
const path = require('path');
const { pathToFileURL } = require('url');
const abertas = p => p.$$eval('details', ds => ds.map(d => (d.open ? 1 : 0)).join(''));
(async () => {
  const paginas = process.argv.slice(2);
  if (!paginas.length) { console.error('uso: caixas-fecham-ao-voltar.js <página.html>...'); process.exit(2); }
  const b = await chromium.launch();
  let falhas = 0;
  for (const pagina of paginas) {
    const nome = path.basename(pagina);
    const ctx = await b.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true });
    await ctx.route(u => u.protocol !== 'file:', r => r.abort());
    const p = await ctx.newPage();
    await p.goto(pathToFileURL(path.resolve(pagina)).href, { waitUntil: 'load' });
    await p.waitForTimeout(300);
    const total = await p.$$eval('details', ds => ds.length);
    if (!total) {
      console.log(`PASS ${nome}: sem caixas <details>`);
      await ctx.close();
      continue;
    }
    const achados = [];
    const sums = await p.$$('details > summary');
    for (const s of sums.slice(0, 4)) { await s.scrollIntoViewIfNeeded(); if (!(await s.evaluate(x => x.parentElement.open))) await s.tap(); }
    // O primeiro link para outra página dentro de uma caixa; sem ele, o primeiro do rodapé.
    let link = await p.evaluateHandle(() => Array.from(document.querySelectorAll('details a[href]'))
      .find(a => !a.closest('summary') && !a.getAttribute('href').startsWith('#') && a.target !== '_blank') || null);
    const deCaixa = !!(await link.jsonValue());
    if (deCaixa) {
      const s = await link.evaluateHandle(a => a.closest('details').querySelector('summary'));
      await s.asElement().scrollIntoViewIfNeeded();
      if (!(await s.evaluate(x => x.parentElement.open))) await s.asElement().tap();
    } else {
      link = await p.evaluateHandle(() => document.querySelector('nav.rodape a'));
      if (!(await link.jsonValue())) achados.push('sem link para sair da página');
    }
    const antes = await abertas(p);
    let ondeAntes = 0, ondeDepois = 0;
    if (!achados.length) {
      await link.evaluate(a => a.scrollIntoView({ block: 'center' }));
      await p.waitForTimeout(200);
      ondeAntes = await p.evaluate(() => Math.round(scrollY));
      const alvo = await link.evaluate(a => Array.from(document.querySelectorAll('a[href]')).indexOf(a));
      await Promise.all([p.waitForNavigation({ waitUntil: 'load' }), link.asElement().tap()]);
      await p.goBack({ waitUntil: 'load' });
      await p.waitForTimeout(500);
      const volta = await abertas(p);
      ondeDepois = await p.evaluate(() => Math.round(scrollY));
      const naTela = await p.evaluate(k => {
        const a = document.querySelectorAll('a[href]')[k];
        if (!a) return false;
        const r = a.getBoundingClientRect();
        // checkVisibility: o link dentro de caixa fechada tem caixa de layout, mas não aparece.
        return a.checkVisibility() && r.height > 0 && r.bottom > 0 && r.top < window.innerHeight;
      }, alvo);
      if (volta !== antes) achados.push(`depois do Voltar, ${volta.replace(/0/g, '').length} caixas abertas (antes ${antes.replace(/0/g, '').length})`);
      if (!naTela) achados.push(`o link de onde se saiu ficou fora da tela (rolagem ${ondeAntes} -> ${ondeDepois} px)`);
    }
    const ok = achados.length === 0;
    if (!ok) falhas++;
    console.log(`${ok ? 'PASS' : 'FAIL'} ${nome}: ${total} caixas, ${antes.replace(/0/g, '').length} abertas, saída por ${deCaixa ? 'link dentro de uma caixa' : 'rodapé'}, rolagem ${ondeAntes} -> ${ondeDepois} px${ok ? '' : ' -> ' + achados.join('; ')}`);
    await ctx.close();
  }
  await b.close();
  process.exit(falhas ? 1 : 0);
})().catch(e => { console.log('FAIL erro do sensor: ' + String((e && e.message) || e).split('\n')[0]); process.exit(1); });
