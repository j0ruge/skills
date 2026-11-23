// Regra: com o teclado, o contorno de foco das opções do quiz tem 2 px ou mais e contraste de 3:1 ou mais
// contra o fundo ao lado, nos dois modos: o claro e o escuro forçado do Chromium
// (--blink-settings=forceDarkModeEnabled=true e colorScheme dark). O escuro forçado age na pintura, e o
// estilo computado não muda; por isso o contraste se mede nos pixels: a área da opção com 8 px de margem,
// capturada com foco e sem foco. O que muda fora da caixa da opção é o anel; o fundo é a mediana do que não muda.
// Contraste = o pixel do anel mais distante do fundo, contra o fundo.
// Antes de medir, a pergunta 1 é respondida errada, para que a certa e a errada também recebam o foco.
// Mede todas as opções da pergunta 1, pelo Tab desde o topo. Página sem quiz passa e diz isso.
// Uso: NODE_PATH=<bancada>/pw/node_modules node foco-sem-contraste.js <página.html>...
const { chromium } = require('playwright');
const { PNG } = require('playwright-core/lib/utilsBundle');
const path = require('path');
const { pathToFileURL } = require('url');
const MINIMO = 3;
const M = 8;
const lum = (r, g, b) => { const f = c => { c /= 255; return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4); }; return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b); };

async function anel(p) {
  const q = await p.evaluate(() => { const e = document.activeElement; e.scrollIntoView({ block: 'center' }); const r = e.getBoundingClientRect(); return { x: r.left, y: r.top, w: r.width, h: r.height }; });
  await p.waitForTimeout(60);
  const clip = { x: Math.max(0, q.x - M), y: Math.max(0, q.y - M), width: q.w + 2 * M, height: q.h + 2 * M };
  const com = PNG.sync.read(await p.screenshot({ clip }));
  const alvo = await p.evaluateHandle(() => document.activeElement);
  await p.evaluate(() => document.activeElement.blur());
  await p.waitForTimeout(60);
  const sem = PNG.sync.read(await p.screenshot({ clip }));
  await alvo.evaluate(e => e.focus({ focusVisible: true }));
  const ring = [], fundo = [];
  for (let y = 0; y < com.height; y++) for (let x = 0; x < com.width; x++) {
    if (x >= M + 2 && x < com.width - M - 2 && y >= M + 2 && y < com.height - M - 2) continue;
    const k = 4 * (y * com.width + x);
    const a = lum(com.data[k], com.data[k + 1], com.data[k + 2]);
    const s = lum(sem.data[k], sem.data[k + 1], sem.data[k + 2]);
    if (Math.abs(a - s) > 0.02) ring.push(a); else fundo.push(s);
  }
  if (!ring.length) return null;
  fundo.sort((a, z) => a - z);
  const f = fundo.length ? fundo[Math.floor(fundo.length / 2)] : 1;
  let m = ring[0]; for (const v of ring) if (Math.abs(v - f) > Math.abs(m - f)) m = v;
  return +((Math.max(m, f) + 0.05) / (Math.min(m, f) + 0.05)).toFixed(2);
}

(async () => {
  const paginas = process.argv.slice(2);
  if (!paginas.length) { console.error('uso: foco-sem-contraste.js <página.html>...'); process.exit(2); }
  let falhas = 0;
  for (const modo of ['claro', 'escuro']) {
    const b = await chromium.launch(modo === 'claro' ? {} : { args: ['--blink-settings=forceDarkModeEnabled=true'] });
    for (const pagina of paginas) {
      const nome = path.basename(pagina);
      const ctx = await b.newContext({ viewport: { width: 1366, height: 768 }, colorScheme: modo === 'claro' ? 'light' : 'dark' });
      const p = await ctx.newPage();
      await p.route(u => u.protocol !== 'file:', r => r.abort());
      await p.goto(pathToFileURL(path.resolve(pagina)).href, { waitUntil: 'domcontentloaded' });
      await p.waitForTimeout(300);
      const per = await p.$('.pergunta');
      if (!per) {
        console.log(`PASS ${nome} [${modo}]: sem quiz`);
        await ctx.close();
        continue;
      }
      const achados = [];
      // Prova de que o modo pegou: o fundo pintado da página sai claro no claro e escuro no escuro forçado.
      const topo = PNG.sync.read(await p.screenshot({ clip: { x: 0, y: 0, width: 8, height: 8 } }));
      const lp = lum(topo.data[0], topo.data[1], topo.data[2]);
      if (modo === 'escuro' && lp > 0.2) achados.push('o escuro forçado não pegou: o fundo da página saiu claro');
      if (modo === 'claro' && lp < 0.5) achados.push('o fundo da página saiu escuro no modo claro');
      // Responde a pergunta 1 errada e volta o ponto de partida do Tab ao topo.
      const ops = await per.$$('button.opcao');
      const nOpcoes = ops.length;
      const certa = parseInt(await per.getAttribute('data-certa'), 10);
      await ops[certa === 1 ? Math.min(1, nOpcoes - 1) : 0].click();
      await p.evaluate(() => { document.activeElement.blur(); window.scrollTo(0, 0); });
      await p.mouse.click(3, 3);
      const medidas = [];
      for (let k = 0; k < 400 && medidas.length < nOpcoes; k++) {
        await p.keyboard.press('Tab');
        const m = await p.evaluate(() => {
          const e = document.activeElement;
          if (!e || !e.matches('.pergunta button.opcao') || e.closest('.pergunta') !== document.querySelector('.pergunta')) return null;
          const s = getComputedStyle(e);
          return { estilo: s.outlineStyle, largura: parseFloat(s.outlineWidth), cor: s.outlineColor, visivel: e.matches(':focus-visible'),
            tipo: e.classList.contains('certa') ? 'certa' : e.classList.contains('errada') ? 'errada' : 'neutra' };
        });
        if (m) { m.cr = await anel(p); medidas.push(m); }
      }
      if (!medidas.length) achados.push('nenhuma opção do quiz recebeu foco pelo Tab');
      medidas.forEach((m, i) => {
        if (!m.visivel) achados.push(`opção ${i + 1}: sem :focus-visible`);
        if (m.estilo === 'none' || m.largura < 2) achados.push(`opção ${i + 1}: contorno ${m.estilo} ${m.largura}px`);
        if (m.cr === null) achados.push(`opção ${i + 1} (${m.tipo}): nenhum anel nos pixels`);
        else if (m.cr < MINIMO) achados.push(`opção ${i + 1} (${m.tipo}): contraste ${m.cr}:1 (${m.cor})`);
      });
      const ok = achados.length === 0;
      if (!ok) falhas++;
      const tipos = medidas.map(m => m.tipo[0]).join('');
      console.log(`${ok ? 'PASS' : 'FAIL'} ${nome} [${modo}]: ${medidas.map(m => m.cr + ':1').join(', ') || '-'} (${tipos})${ok ? '' : ' -> ' + achados.join('; ')}`);
      await ctx.close();
    }
    await b.close();
  }
  process.exit(falhas ? 1 : 0);
})().catch(e => { console.log('FAIL erro do sensor: ' + String((e && e.message) || e).split('\n')[0]); process.exit(1); });
