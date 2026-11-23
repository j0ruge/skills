// Regra: o tempo que a aula promete bate com o tamanho dela.
// Em cada aula (arquivo 000N-...): o [data-minutos] do cabeçalho (em .meta) é igual ao do item
// li[data-aula="N"] do ../index.html, e fica a até 5 min da estimativa
//   palavras ÷ palavrasPorMinuto + 1 min por details.lembrar + 0,5 min por pergunta.
// As palavras são o texto do <main> com os <details> abertos, sem o código Mermaid e sem os SVG.
// palavrasPorMinuto vem do GUIA_TEXTOS (130 se faltar). Página que não é aula passa e diz isso.
// Uso: NODE_PATH=<bancada>/pw/node_modules node tempo-das-aulas.js <aula.html>...
const { chromium } = require('playwright');
const path = require('path');
const { pathToFileURL } = require('url');
const TOLERANCIA = 5;
(async () => {
  const paginas = process.argv.slice(2);
  if (!paginas.length) { console.error('uso: tempo-das-aulas.js <aula.html>...'); process.exit(2); }
  const b = await chromium.launch();
  let falhas = 0;
  const indices = {};
  for (const pagina of paginas) {
    const abs = path.resolve(pagina);
    const nome = path.basename(abs);
    const m = nome.match(/^(\d{4})-/);
    if (!m) { console.log(`PASS ${nome}: não é aula`); continue; }
    const n = parseInt(m[1], 10);
    const p = await b.newPage();
    await p.route(u => u.protocol !== 'file:', r => r.abort());
    await p.goto(pathToFileURL(abs).href, { waitUntil: 'domcontentloaded' });
    const r = await p.evaluate(() => {
      document.querySelectorAll('details').forEach(d => { d.open = true; });
      const main = document.querySelector('main') || document.body;
      const c = main.cloneNode(true);
      c.querySelectorAll('pre.mermaid, svg').forEach(e => e.remove());
      document.body.appendChild(c);
      const palavras = (c.innerText.match(/\S+/g) || []).length;
      c.remove();
      const el = document.querySelector('.meta [data-minutos]');
      const ppm = (window.GUIA_TEXTOS || {}).palavrasPorMinuto || 130;
      return {
        palavras, ppm,
        lembrar: document.querySelectorAll('details.lembrar').length,
        perguntas: document.querySelectorAll('.pergunta').length,
        cabecalho: el ? parseInt(el.getAttribute('data-minutos'), 10) : null
      };
    });
    const est = r.palavras / r.ppm + r.lembrar + r.perguntas * 0.5;
    const indice = path.resolve(path.dirname(abs), '..', 'index.html');
    if (!(indice in indices)) {
      const pi = await b.newPage();
      await pi.route(u => u.protocol !== 'file:', q => q.abort());
      try {
        await pi.goto(pathToFileURL(indice).href, { waitUntil: 'domcontentloaded' });
        indices[indice] = await pi.evaluate(() => Array.from(document.querySelectorAll('li[data-aula]')).map(li => {
          const e = li.querySelector('[data-minutos]');
          return { aula: parseInt(li.getAttribute('data-aula'), 10), minutos: e ? parseInt(e.getAttribute('data-minutos'), 10) : null };
        }));
      } catch (e) { indices[indice] = []; }
      await pi.close();
    }
    const item = indices[indice].find(i => i.aula === n);
    const noIndice = item ? item.minutos : null;
    const cab = r.cabecalho;
    const motivos = [];
    if (cab === null || Number.isNaN(cab)) motivos.push('o cabeçalho não tem número em .meta [data-minutos]');
    if (noIndice === null || Number.isNaN(noIndice)) motivos.push(`o índice não tem número no li[data-aula="${n}"]`);
    if (motivos.length === 0) {
      if (cab !== noIndice) motivos.push(`o cabeçalho (${cab}) e o índice (${noIndice}) diferem`);
      if (Math.abs(cab - est) > TOLERANCIA) motivos.push(`o cabeçalho diz ${cab} min e a conta dá ${est.toFixed(1)} (tolerância ${TOLERANCIA})`);
    }
    const ok = motivos.length === 0;
    if (!ok) falhas++;
    console.log(`${ok ? 'PASS' : 'FAIL'} ${nome}: estimativa ${est.toFixed(1)} min (${r.palavras} palavras, ${r.lembrar} lembrar, ${r.perguntas} perguntas); cabeçalho ${cab ?? 'sem número'}; índice ${noIndice ?? 'sem número'}${ok ? '' : ' -> ' + motivos.join('; ')}`);
    await p.close();
  }
  await b.close();
  process.exit(falhas ? 1 : 0);
})().catch(e => { console.log('FAIL erro do sensor: ' + String((e && e.message) || e).split('\n')[0]); process.exit(1); });
