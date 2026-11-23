// Regra: toda cor e todo tracejado de um diagrama Mermaid têm explicação na figcaption.
// Mermaid já desenhado (sem o código no texto) falha.
// Lê o código do Mermaid sem rede (o diagrama fica como texto). Um estilo entra no diagrama por quatro caminhos:
//   - "classDef nome ..." usada por "class X nome" ou por "A:::nome" (uma classDef pode nomear várias: "a,b");
//   - "classDef default ...", que vale para todo nó sem classe e por isso conta sempre como usada;
//   - "style X ...", direto num nó;
//   - "linkStyle N ...", direto numa seta (aqui só o tracejado importa).
// Em cada figure.diagrama com pre.mermaid:
//   - cada fill de uma classe usada ou de um style pede, na figcaption, o nome que GUIA_TEXTOS.cores dá a ele;
//   - stroke-dasharray numa classe usada, num style ou num linkStyle, ou seta pontilhada (-.-> ou -.-), pede
//     palavraTracejado na figcaption;
//   - fill que não está em GUIA_TEXTOS.cores também falha (a cor ganha um nome lá);
//   - fill branco (#fff, #ffffff) não pede nome.
// O nome pode trazer alternativas separadas por "|". SVG feito à mão fica de fora: o rótulo está no desenho.
// Página sem Mermaid passa e diz isso.
// Uso: NODE_PATH=<bancada>/pw/node_modules node cor-sem-legenda.js <página.html>...
const { chromium } = require('playwright');
const path = require('path');
const { pathToFileURL } = require('url');
(async () => {
  const paginas = process.argv.slice(2);
  if (!paginas.length) { console.error('uso: cor-sem-legenda.js <página.html>...'); process.exit(2); }
  const b = await chromium.launch();
  let falhas = 0;
  for (const pagina of paginas) {
    const p = await b.newPage();
    // Sem rede: o Mermaid não desenha, e o texto do bloco continua sendo o código.
    await p.route(u => u.protocol !== 'file:', r => r.abort());
    await p.goto(pathToFileURL(path.resolve(pagina)).href, { waitUntil: 'domcontentloaded' });
    const T = await p.evaluate(() => window.GUIA_TEXTOS || {});
    const figuras = await p.$$eval('figure.diagrama', fs => fs.filter(f => f.querySelector('pre.mermaid')).map(f => ({
      mermaid: f.querySelector('pre.mermaid').textContent,
      desenhado: !!f.querySelector('pre.mermaid > svg'),
      legenda: ((f.querySelector('figcaption') || {}).textContent || '').toLowerCase()
    })));
    const cores = {};
    Object.keys(T.cores || {}).forEach(k => { cores[k.toLowerCase()] = String(T.cores[k]).toLowerCase(); });
    const tracejado = String(T.palavraTracejado || '').toLowerCase();
    const BRANCO = ['#fff', '#ffffff'];
    const problemas = [];
    figuras.forEach((f, i) => {
      if (f.desenhado) { problemas.push(`figura ${i + 1}: o Mermaid desenhou sem rede; o código não está mais no texto`); return; }
      const pede = new Set();
      const defs = {};
      for (const m of f.mermaid.matchAll(/^\s*classDef\s+([\w,]+)\s+([^\n]+)/gm)) m[1].split(',').forEach(n => { defs[n] = m[2]; });
      const usadas = new Set();
      if ('default' in defs) usadas.add('default');
      for (const m of f.mermaid.matchAll(/^\s*class\s+[\w,]+\s+(\w+)/gm)) usadas.add(m[1]);
      for (const m of f.mermaid.matchAll(/:::(\w+)/g)) usadas.add(m[1]);
      let temTraco = /-\.->|-\.-/.test(f.mermaid);
      for (const m of f.mermaid.matchAll(/^\s*linkStyle\s+\S+\s+([^\n]+)/gm)) if (/stroke-dasharray/.test(m[1])) temTraco = true;
      // Cada estilo que pinta um nó: o das classes usadas e o de cada linha "style X ...".
      const estilos = Array.from(usadas, c => defs[c] || '');
      for (const m of f.mermaid.matchAll(/^\s*style\s+\S+\s+([^\n]+)/gm)) estilos.push(m[1]);
      for (const d of estilos) {
        const fill = (d.match(/fill:\s*(#[0-9a-fA-F]{3,6})/) || [])[1];
        if (fill) {
          const k = fill.toLowerCase();
          if (k in cores) pede.add(cores[k]);
          else if (!BRANCO.includes(k)) pede.add('cor desconhecida ' + k);
        }
        if (/stroke-dasharray/.test(d)) temTraco = true;
      }
      if (temTraco) pede.add('\u0000tracejado');
      const faltam = [];
      for (const w of pede) {
        if (w.startsWith('cor desconhecida')) { faltam.push(w); continue; }
        const palavras = w === '\u0000tracejado' ? [tracejado] : w.split('|');
        if (!palavras.some(x => x && f.legenda.includes(x.trim()))) faltam.push(w === '\u0000tracejado' ? `o tracejado (${tracejado || 'palavraTracejado ausente'})` : w);
      }
      if (faltam.length) problemas.push(`figura ${i + 1}: a legenda não diz ${faltam.join(', ')}`);
    });
    const ok = problemas.length === 0;
    if (!ok) falhas++;
    console.log(`${ok ? 'PASS' : 'FAIL'} ${path.basename(pagina)}: ${figuras.length ? figuras.length + ' figuras Mermaid' : 'sem Mermaid'}${ok ? '' : ' -> ' + problemas.join('; ')}`);
    await p.close();
  }
  await b.close();
  process.exit(falhas ? 1 : 0);
})().catch(e => { console.log('FAIL erro do sensor: ' + String((e && e.message) || e).split('\n')[0]); process.exit(1); });
