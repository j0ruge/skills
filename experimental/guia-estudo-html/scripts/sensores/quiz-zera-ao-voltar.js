// Regra: o estado do quiz vive na aba (sessionStorage). Em cada página com quiz, a 390 x 844 com toque:
//   1. abre as três primeiras caixas <details>, toca a opção 2 da pergunta 1 e a opção 3 da pergunta 2 (a
//      última opção que houver, se faltar uma), e guarda o placar, as caixas abertas e as marcas;
//   2. toca o primeiro link do rodapé e volta com o Voltar: tudo igual;
//   3. recarrega a página: tudo igual;
//   4. abre a mesma página numa aba nova: recomeça do zero (placar e marcas iguais aos do começo).
// O placar se compara com ele mesmo (antes, depois, no começo), nunca com a frase. Página sem quiz passa.
// Uso: NODE_PATH=<bancada>/pw/node_modules node quiz-zera-ao-voltar.js <página.html>...
const { chromium } = require('playwright');
const path = require('path');
const { pathToFileURL } = require('url');
const retrato = p => p.evaluate(() => ({
  placar: (document.querySelector('.placar') || {}).textContent || '',
  abertos: Array.from(document.querySelectorAll('details')).map(d => d.open ? 1 : 0).join(''),
  marcas: Array.from(document.querySelectorAll('.pergunta')).map(q =>
    Array.from(q.querySelectorAll('button.opcao')).map(b => b.classList.contains('certa') ? 'C' : b.classList.contains('errada') ? 'E' : '-').join('')).join(' '),
  retornos: Array.from(document.querySelectorAll('.pergunta .retorno')).map(r => r.textContent.length).join(',')
}));
const igual = (a, z) => JSON.stringify(a) === JSON.stringify(z);
(async () => {
  const paginas = process.argv.slice(2);
  if (!paginas.length) { console.error('uso: quiz-zera-ao-voltar.js <página.html>...'); process.exit(2); }
  const b = await chromium.launch();
  let falhas = 0;
  for (const pagina of paginas) {
    const url = pathToFileURL(path.resolve(pagina)).href;
    const ctx = await b.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true });
    await ctx.route(u => u.protocol !== 'file:', r => r.abort());
    const p = await ctx.newPage();
    await p.goto(url, { waitUntil: 'load' });
    await p.waitForTimeout(300);
    const perg = await p.$$('.pergunta');
    if (!perg.length) {
      console.log(`PASS ${path.basename(pagina)}: sem quiz`);
      await ctx.close();
      continue;
    }
    const achados = [];
    const zero0 = await retrato(p);
    const det = await p.$$('details > summary');
    for (const s of det.slice(0, 3)) { await s.scrollIntoViewIfNeeded(); await s.tap(); }
    const alvos = [1, 2];
    for (let k = 0; k < Math.min(2, perg.length); k++) {
      const ops = await perg[k].$$('button.opcao');
      await perg[k].scrollIntoViewIfNeeded();
      await ops[Math.min(alvos[k], ops.length - 1)].tap();
    }
    const antes = await retrato(p);
    if (antes.placar === zero0.placar) achados.push(`o placar não mudou depois das respostas: "${antes.placar}"`);
    const link = await p.$('nav.rodape a');
    if (!link) achados.push('sem link no rodapé');
    else {
      await link.scrollIntoViewIfNeeded();
      await Promise.all([p.waitForNavigation({ waitUntil: 'load' }), link.tap()]);
      await p.goBack({ waitUntil: 'load' });
      await p.waitForTimeout(300);
      const volta = await retrato(p);
      if (!igual(volta, antes)) achados.push(`depois do Voltar: placar "${volta.placar}", caixas ${volta.abertos} (antes "${antes.placar}", ${antes.abertos})`);
    }
    await p.reload({ waitUntil: 'load' });
    await p.waitForTimeout(300);
    const recarga = await retrato(p);
    if (!igual(recarga, antes)) achados.push(`depois de recarregar: placar "${recarga.placar}", caixas ${recarga.abertos}`);
    const nova = await ctx.newPage();
    await nova.goto(url, { waitUntil: 'load' });
    await nova.waitForTimeout(300);
    const zero = await retrato(nova);
    if (zero.placar !== zero0.placar || /[CE]/.test(zero.marcas)) achados.push(`aba nova não recomeçou: "${zero.placar}"`);
    const ok = achados.length === 0;
    if (!ok) falhas++;
    console.log(`${ok ? 'PASS' : 'FAIL'} ${path.basename(pagina)}: antes "${antes.placar}", ${antes.abertos.replace(/0/g, '').length} caixas abertas${ok ? '' : ' -> ' + achados.join('; ')}`);
    await ctx.close();
  }
  await b.close();
  process.exit(falhas ? 1 : 0);
})().catch(e => { console.log('FAIL erro do sensor: ' + String((e && e.message) || e).split('\n')[0]); process.exit(1); });
