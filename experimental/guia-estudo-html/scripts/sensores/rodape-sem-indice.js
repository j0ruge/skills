// Regra: o rodapé de cada aula (nav.rodape) tem a anterior, o índice e a próxima.
//   - a primeira aula não tem `anterior`; as outras têm, e ela aponta para a aula N-1;
//   - `indice` aponta para ../index.html;
//   - `proxima` aponta para a aula N+1; na última aula, aponta para o índice.
// O número N vem do nome do arquivo (000N-...); a última aula é a de maior número na mesma pasta.
// Página que não é aula (sem 000N- no nome) passa e diz isso.
// Uso: NODE_PATH=<bancada>/pw/node_modules node rodape-sem-indice.js <aula.html>...
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');
const { pathToFileURL } = require('url');
(async () => {
  const paginas = process.argv.slice(2);
  if (!paginas.length) { console.error('uso: rodape-sem-indice.js <aula.html>...'); process.exit(2); }
  const b = await chromium.launch();
  let falhas = 0;
  for (const pagina of paginas) {
    const abs = path.resolve(pagina);
    const nome = path.basename(abs);
    const m = nome.match(/^(\d{4})-/);
    if (!m) { console.log(`PASS ${nome}: não é aula`); continue; }
    const n = parseInt(m[1], 10);
    const irmas = fs.readdirSync(path.dirname(abs)).map(f => (f.match(/^(\d{4})-.*\.html$/) || [])[1]).filter(Boolean).map(Number);
    const ultima = Math.max(...irmas);
    const p = await b.newPage({ viewport: { width: 390, height: 844 } });
    await p.route(u => u.protocol !== 'file:', r => r.abort());
    await p.goto(pathToFileURL(abs).href, { waitUntil: 'domcontentloaded' });
    const h = await p.evaluate(() => {
      const href = k => { const a = document.querySelector(`nav.rodape a[data-rodape="${k}"]`); return a ? a.getAttribute('href') : null; };
      return { anterior: href('anterior'), indice: href('indice'), proxima: href('proxima') };
    });
    const alvo = href => (href === null ? null : path.resolve(path.dirname(abs), href.split('#')[0]));
    const indiceAbs = path.resolve(path.dirname(abs), '..', 'index.html');
    const dessa = k => { const pad = String(k).padStart(4, '0'); return a => a !== null && path.dirname(a) === path.dirname(abs) && path.basename(a).startsWith(pad + '-'); };
    const achados = [];
    if (alvo(h.indice) !== indiceAbs) achados.push(h.indice === null ? 'sem o link do índice' : `o índice aponta para ${h.indice}`);
    if (n === 1) { if (h.anterior !== null) achados.push('a primeira aula tem "anterior"'); }
    else if (!dessa(n - 1)(alvo(h.anterior))) achados.push(h.anterior === null ? 'sem o link da anterior' : `a anterior aponta para ${h.anterior}`);
    if (n === ultima) { if (alvo(h.proxima) !== indiceAbs) achados.push(h.proxima === null ? 'a última aula sem "proxima"' : `a última aula leva a ${h.proxima}, não ao índice`); }
    else if (!dessa(n + 1)(alvo(h.proxima))) achados.push(h.proxima === null ? 'sem o link da próxima' : `a próxima aponta para ${h.proxima}`);
    const ok = achados.length === 0;
    if (!ok) falhas++;
    console.log(`${ok ? 'PASS' : 'FAIL'} ${nome}: aula ${n} de ${ultima} [${h.anterior ?? '-'} | ${h.indice ?? '-'} | ${h.proxima ?? '-'}]${ok ? '' : ' -> ' + achados.join('; ')}`);
    await p.close();
  }
  await b.close();
  process.exit(falhas ? 1 : 0);
})().catch(e => { console.log('FAIL erro do sensor: ' + String((e && e.message) || e).split('\n')[0]); process.exit(1); });
