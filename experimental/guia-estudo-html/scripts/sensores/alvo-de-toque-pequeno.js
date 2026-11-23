// Regra: a 390 x 844, com toque, cada alvo abaixo tem 44 x 44 px ou mais:
//   - os links do rodapé (nav.rodape a);
//   - os atalhos do topo (.atalhos a) e os links para o glossário (a.no-glossario);
//   - as opções do quiz (.pergunta button.opcao) e os summary dos details;
//   - os links para âncora num parágrafo com três ou mais deles.
// O sensor abre todo <details> antes de medir: um link dentro de caixa fechada mede 0 x 0 e acusaria um defeito
// que a pessoa não vê. Cada summary também tem de manter o display de lista: com outro display o triângulo de
// abrir some (flex, grid, block), e a caixa deixa de parecer que abre.
// Exceção a "um sensor por defeito" (qa.md, seção 1): o sensor mede dois defeitos na mesma passada pelos summary.
// Cada um tem o seu caso no sabotar.py. O marcador se mede só pelo display: um summary em list-item com
// list-style: none ou ::marker vazio também perde o triângulo, e passa aqui.
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
      document.querySelectorAll('details').forEach(d => { d.open = true; });
      const alvos = new Set(document.querySelectorAll('nav.rodape a, .atalhos a, a.no-glossario, .pergunta button.opcao, details > summary'));
      document.querySelectorAll('p').forEach(par => {
        const ancoras = Array.from(par.children).filter(a => a.matches('a[href^="#"]'));
        if (ancoras.length >= 3) ancoras.forEach(a => alvos.add(a));
      });
      return Array.from(alvos).map(a => {
        const q = a.getBoundingClientRect();
        const semMarcador = a.matches('summary') && getComputedStyle(a).display !== 'list-item';
        return { t: a.textContent.trim().slice(0, 24), w: Math.round(q.width), h: Math.round(q.height), semMarcador };
      });
    });
    const pequenos = r.filter(a => a.w < MINIMO || a.h < MINIMO);
    const semMarcador = r.filter(a => a.semMarcador);
    const ok = pequenos.length === 0 && semMarcador.length === 0;
    if (!ok) falhas++;
    const menorH = r.length ? Math.min(...r.map(a => a.h)) : null;
    console.log(`${ok ? 'PASS' : 'FAIL'} ${path.basename(pagina)}: ${r.length ? `${r.length} alvos, menor altura ${menorH} px` : 'sem alvos'}${ok ? '' : ' -> ' + [
      ...pequenos.slice(0, 6).map(a => `"${a.t}" ${a.w}x${a.h}`).concat(pequenos.length > 6 ? [`(+${pequenos.length - 6})`] : []),
      ...semMarcador.slice(0, 6).map(a => `summary sem marcador de abrir: "${a.t}"`)
    ].join('; ')}`);
    await p.close();
  }
  await b.close();
  process.exit(falhas ? 1 : 0);
})().catch(e => { console.log('FAIL erro do sensor: ' + String((e && e.message) || e).split('\n')[0]); process.exit(1); });
