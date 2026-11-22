// Regra: o verbete fica a uma ação da aula, sem sair dela. Em cada aula (arquivo 000N-...):
//   1. `p.atalhos` vem logo depois do h1, com a[data-atalho="indice"] e a[data-atalho="glossario"] que abre
//      em outra aba (target="_blank");
//   2. todo a.no-glossario abre em outra aba e aponta para um id que existe na página do href;
//   3. clicar no primeiro a.no-glossario abre o verbete numa aba nova, e a aula fica no mesmo ponto.
// Página que não é aula (sem 000N- no nome) passa e diz isso.
// Uso: NODE_PATH=<bancada>/pw/node_modules node glossario-longe-da-aula.js <aula.html>...
const { chromium } = require('playwright');
const path = require('path');
const { pathToFileURL } = require('url');
(async () => {
  const paginas = process.argv.slice(2);
  if (!paginas.length) { console.error('uso: glossario-longe-da-aula.js <aula.html>...'); process.exit(2); }
  const b = await chromium.launch();
  const ctx = await b.newContext({ viewport: { width: 1366, height: 768 } });
  await ctx.route(u => u.protocol !== 'file:', r => r.abort());
  let falhas = 0;
  const ids = {};
  // Ids de uma página (cache por arquivo).
  async function idsDe(arq) {
    if (ids[arq]) return ids[arq];
    const g = await ctx.newPage();
    try {
      await g.goto(pathToFileURL(arq).href, { waitUntil: 'domcontentloaded' });
      ids[arq] = new Set(await g.$$eval('[id]', es => es.map(e => e.id)));
    } catch (e) { ids[arq] = new Set(); }
    await g.close();
    return ids[arq];
  }
  for (const pagina of paginas) {
    const abs = path.resolve(pagina);
    const nome = path.basename(abs);
    if (!/^\d{4}-/.test(nome)) { console.log(`PASS ${nome}: não é aula`); continue; }
    const p = await ctx.newPage();
    await p.goto(pathToFileURL(abs).href, { waitUntil: 'domcontentloaded' });
    const problemas = [];
    const r = await p.evaluate(() => {
      const h1 = document.querySelector('h1');
      const at = h1 && h1.nextElementSibling;
      const ok = at && at.matches('p.atalhos');
      const el = k => { const a = ok ? at.querySelector(`a[data-atalho="${k}"]`) : null; return a ? { href: a.getAttribute('href'), alvo: a.getAttribute('target') } : null; };
      const links = Array.from(document.querySelectorAll('a.no-glossario')).map(a => ({ href: a.getAttribute('href') || '', alvo: a.getAttribute('target') }));
      return { atalhos: !!ok, indice: el('indice'), glossario: el('glossario'), links };
    });
    if (!r.atalhos) problemas.push('sem p.atalhos logo depois do h1');
    else {
      if (!r.indice) problemas.push('atalhos sem o índice');
      if (!r.glossario) problemas.push('atalhos sem o glossário');
      else if (r.glossario.alvo !== '_blank') problemas.push('o glossário dos atalhos abre na mesma aba');
    }
    for (const l of r.links) {
      const [arq, id] = l.href.split('#');
      if (l.alvo !== '_blank') problemas.push(`${l.href} abre na mesma aba`);
      const existe = arq ? (await idsDe(path.resolve(path.dirname(abs), arq))).has(id || '') : false;
      if (!existe) problemas.push(`#${id || ''} não existe em ${arq || '(sem arquivo)'}`);
    }
    // A jornada: clicar e conferir que a aula não saiu do lugar.
    const primeiro = await p.$('a.no-glossario');
    if (primeiro) {
      await primeiro.scrollIntoViewIfNeeded();
      const y0 = await p.evaluate(() => window.scrollY);
      const [aba] = await Promise.all([ctx.waitForEvent('page', { timeout: 5000 }).catch(() => null), primeiro.click()]);
      if (!aba) problemas.push('o link não abriu aba nova');
      else {
        await aba.waitForLoadState('domcontentloaded');
        if (!/#/.test(aba.url())) problemas.push(`a aba nova abriu ${aba.url()}`);
        await aba.close();
      }
      const y1 = await p.evaluate(() => window.scrollY);
      if (p.url() !== pathToFileURL(abs).href || Math.abs(y1 - y0) > 2) problemas.push(`a aula mudou: rolagem ${y0} -> ${y1}`);
    }
    const ok = problemas.length === 0;
    if (!ok) falhas++;
    console.log(`${ok ? 'PASS' : 'FAIL'} ${nome}: ${r.links.length} links para o glossário${ok ? '' : ' -> ' + problemas.join('; ')}`);
    await p.close();
  }
  await b.close();
  process.exit(falhas ? 1 : 0);
})();
