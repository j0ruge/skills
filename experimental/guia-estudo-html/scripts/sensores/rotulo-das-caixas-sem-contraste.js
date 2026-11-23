// Regra: dentro de .caixa, todo span.rotulo e todo texto de ::before tem contraste de 4,5:1 ou mais contra o
// fundo do primeiro ancestral com cor de fundo (o próprio elemento conta). Mede pelo estilo computado, no
// tema claro, a 1280 px. Página sem caixa passa e diz isso.
// Uso: NODE_PATH=<bancada>/pw/node_modules node rotulo-das-caixas-sem-contraste.js <página.html>...
const { chromium } = require('playwright');
const path = require('path');
const { pathToFileURL } = require('url');
const MINIMO = 4.5;
(async () => {
  const paginas = process.argv.slice(2);
  if (!paginas.length) { console.error('uso: rotulo-das-caixas-sem-contraste.js <página.html>...'); process.exit(2); }
  const b = await chromium.launch();
  let falhas = 0;
  for (const pagina of paginas) {
    const p = await b.newPage({ viewport: { width: 1280, height: 900 } });
    await p.route(u => u.protocol !== 'file:', r => r.abort());
    await p.goto(pathToFileURL(path.resolve(pagina)).href, { waitUntil: 'load' });
    const r = await p.evaluate(() => {
      const rgb = s => (s.match(/[\d.]+/g) || []).map(Number);
      // Mesma fórmula e mesmo limite (0.03928) dos outros três sensores de contraste.
      const lum = c => { const v = c.slice(0, 3).map(x => { x /= 255; return x <= 0.03928 ? x / 12.92 : Math.pow((x + 0.055) / 1.055, 2.4); });
        return 0.2126 * v[0] + 0.7152 * v[1] + 0.0722 * v[2]; };
      const fundo = el => { for (let e = el; e; e = e.parentElement) { const c = rgb(getComputedStyle(e).backgroundColor);
        if (c.length === 3 || (c.length === 4 && c[3] > 0)) return c; } return [255, 255, 255]; };
      const razao = (cor, fu) => { const [a, z] = [lum(cor), lum(fu)].sort((x, y) => y - x); return (a + 0.05) / (z + 0.05); };
      const medidas = [];
      document.querySelectorAll('.caixa').forEach((caixa, i) => {
        const todos = [caixa, ...caixa.querySelectorAll('*')];
        todos.forEach(e => {
          if (e.matches('span.rotulo')) {
            const cor = rgb(getComputedStyle(e).color), fu = fundo(e);
            medidas.push({ onde: `caixa ${i + 1}, rótulo "${e.textContent.trim().slice(0, 24)}"`, razao: razao(cor, fu), cor: cor.join(','), fundo: fu.slice(0, 3).join(',') });
          }
          const antes = getComputedStyle(e, '::before');
          const c = antes.content;
          if (c && c !== 'none' && c !== 'normal' && c.replace(/^["']|["']$/g, '').trim()) {
            const cor = rgb(antes.color), fu = fundo(e);
            medidas.push({ onde: `caixa ${i + 1}, ::before de ${e.tagName.toLowerCase()}`, razao: razao(cor, fu), cor: cor.join(','), fundo: fu.slice(0, 3).join(',') });
          }
        });
      });
      return medidas;
    });
    const ruins = r.filter(x => x.razao < MINIMO);
    const pior = r.length ? Math.min(...r.map(x => x.razao)).toFixed(2) : '-';
    if (ruins.length) {
      falhas += 1;
      console.log(`FAIL ${path.basename(pagina)}: ${r.length} textos, ${ruins.length} abaixo de 4,5:1, pior ${pior}:1 -> ${ruins.slice(0, 3).map(x => `${x.onde} (cor ${x.cor} sobre ${x.fundo})`).join('; ')}`);
    } else {
      console.log(`PASS ${path.basename(pagina)}: ${r.length ? `${r.length} textos, pior ${pior}:1` : 'sem caixa com rótulo'}`);
    }
    await p.close();
  }
  await b.close();
  process.exit(falhas ? 1 : 0);
})().catch(e => { console.log('FAIL erro do sensor: ' + String((e && e.message) || e).split('\n')[0]); process.exit(1); });
