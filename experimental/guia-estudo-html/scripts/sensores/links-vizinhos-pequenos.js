// Regra: a 390 x 844, com toque, nenhum link pequeno fica ao lado de outro link, e as listas de links têm
// alvo folgado. Mede todo link visível:
//   - vizinho: link com menos de 44 px de altura não tem outro link a menos de 20 px, borda a borda;
//   - lista de links: numa lista em que todo item começa por um link, esse link tem 44 px de altura ou mais.
// Página sem nenhum desses casos passa, e a saída diz quantos links mediu.
// Uso: NODE_PATH=<bancada>/pw/node_modules node links-vizinhos-pequenos.js <página.html>...
const { chromium } = require('playwright');
const path = require('path');
const { pathToFileURL } = require('url');
const MINIMO = 44;
const PERTO = 20;
(async () => {
  const paginas = process.argv.slice(2);
  if (!paginas.length) { console.error('uso: links-vizinhos-pequenos.js <página.html>...'); process.exit(2); }
  const b = await chromium.launch();
  let falhas = 0;
  for (const pagina of paginas) {
    const p = await b.newPage({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true });
    await p.route(u => u.protocol !== 'file:', r => r.abort());
    await p.goto(pathToFileURL(path.resolve(pagina)).href, { waitUntil: 'load' });
    await p.waitForTimeout(300);
    const r = await p.evaluate(({ MINIMO, PERTO }) => {
      const links = Array.from(document.querySelectorAll('a[href]')).filter(a => a.getClientRects().length);
      const caixas = links.flatMap(a => Array.from(a.getClientRects()).map(q => ({ a, t: a.textContent.trim().slice(0, 20), x0: q.left, x1: q.right, y0: q.top + scrollY, y1: q.bottom + scrollY })));
      const achados = new Set();
      caixas.forEach((c, i) => caixas.forEach((z, j) => {
        if (j <= i || c.a === z.a) return;
        const dx = Math.max(0, Math.max(c.x0, z.x0) - Math.min(c.x1, z.x1));
        const dy = Math.max(0, Math.max(c.y0, z.y0) - Math.min(c.y1, z.y1));
        const d = Math.hypot(dx, dy);
        const pequeno = [c, z].filter(k => k.y1 - k.y0 < MINIMO);
        if (d < PERTO && pequeno.length) achados.add(`vizinho: "${c.t}" (${Math.round(c.y1 - c.y0)} px) a ${Math.round(d)} px de "${z.t}" (${Math.round(z.y1 - z.y0)} px)`);
      }));
      let emLista = 0;
      document.querySelectorAll('ul, ol').forEach(l => {
        const itens = Array.from(l.children).filter(x => x.tagName === 'LI');
        const abre = li => { const a = li.firstElementChild; return a && a.tagName === 'A' && !(li.firstChild.nodeType === 3 && li.firstChild.textContent.trim()) ? a : null; };
        if (!itens.length || !itens.every(abre)) return;
        itens.forEach(li => {
          emLista++;
          const h = Math.round(abre(li).getBoundingClientRect().height);
          if (h < MINIMO) achados.add(`lista de links: "${abre(li).textContent.trim().slice(0, 24)}" com ${h} px de altura`);
        });
      });
      return { n: links.length, emLista, achados: [...achados] };
    }, { MINIMO, PERTO });
    const ok = r.achados.length === 0;
    if (!ok) falhas++;
    console.log(`${ok ? 'PASS' : 'FAIL'} ${path.basename(pagina)}: ${r.n ? `${r.n} links, ${r.emLista} em lista de links` : 'sem links'}${ok ? '' : ' -> ' + r.achados.slice(0, 6).join('; ') + (r.achados.length > 6 ? ` (+${r.achados.length - 6})` : '')}`);
    await p.close();
  }
  await b.close();
  process.exit(falhas ? 1 : 0);
})().catch(e => { console.log('FAIL erro do sensor: ' + String((e && e.message) || e).split('\n')[0]); process.exit(1); });
