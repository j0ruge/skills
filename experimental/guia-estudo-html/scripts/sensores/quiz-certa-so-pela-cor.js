// Regra: depois de um erro no quiz, a opção certa se reconhece sem cor. Em cada pergunta, toca uma opção
// errada e confere:
//   1. a certa traz marcaCerta no texto do botão e a errada traz marcaSua (as duas vêm do textos.js);
//   2. a borda da certa e a da errada diferem em algo além da cor (estilo, espessura ou sombra);
//   3. o retorno, que o leitor de tela anuncia, traz o texto da opção certa;
//   4. a .pergunta recebe data-resultado="errado".
// Página sem quiz passa e diz isso.
// Uso: NODE_PATH=<bancada>/pw/node_modules node quiz-certa-so-pela-cor.js <página.html>...
const { chromium } = require('playwright');
const path = require('path');
const { pathToFileURL } = require('url');
(async () => {
  const paginas = process.argv.slice(2);
  if (!paginas.length) { console.error('uso: quiz-certa-so-pela-cor.js <página.html>...'); process.exit(2); }
  const b = await chromium.launch();
  let falhas = 0;
  for (const pagina of paginas) {
    const p = await b.newPage({ viewport: { width: 1366, height: 768 } });
    await p.route(u => u.protocol !== 'file:', r => r.abort());
    await p.goto(pathToFileURL(path.resolve(pagina)).href, { waitUntil: 'domcontentloaded' });
    await p.waitForTimeout(300);
    const T = await p.evaluate(() => window.GUIA_TEXTOS || {});
    const achados = [];
    const perguntas = await p.$$('.pergunta');
    for (let q = 0; q < perguntas.length; q++) {
      const per = perguntas[q];
      const certa = parseInt(await per.getAttribute('data-certa'), 10);
      const bs = await per.$$('button.opcao');
      const textos = await Promise.all(bs.map(x => x.evaluate(e => e.textContent.replace(/\s+/g, ' ').trim())));
      const iErrada = certa === 1 ? 1 : 0;
      if (!bs[iErrada]) { achados.push(`P${q + 1}: sem opção errada para tocar`); continue; }
      await bs[iErrada].click();
      const r = await per.evaluate((el, a) => {
        const bs = el.querySelectorAll('button.opcao');
        const c = bs[a.certa - 1], e = bs[a.iErrada];
        const sc = getComputedStyle(c), se = getComputedStyle(e);
        const forma = s => [s.borderTopStyle, s.borderTopWidth, s.boxShadow].join('|');
        return {
          certaTexto: c.innerText,
          erradaTexto: e.innerText,
          formaDifere: forma(sc) !== forma(se),
          resultado: el.getAttribute('data-resultado'),
          retorno: (el.querySelector('.retorno') || {}).textContent || ''
        };
      }, { certa, iErrada });
      const alvo = textos[certa - 1].replace(/[.;:]+$/, '');
      if (!T.marcaCerta || !r.certaTexto.includes(T.marcaCerta)) achados.push(`P${q + 1}: a certa não tem a marca`);
      if (!T.marcaSua || !r.erradaTexto.includes(T.marcaSua)) achados.push(`P${q + 1}: a errada não tem a marca`);
      if (!r.formaDifere) achados.push(`P${q + 1}: certa e errada só diferem na cor da borda`);
      if (!r.retorno.includes(alvo)) achados.push(`P${q + 1}: o retorno não nomeia a certa`);
      if (r.resultado !== 'errado') achados.push(`P${q + 1}: data-resultado é "${r.resultado}", esperado "errado"`);
    }
    const ok = achados.length === 0;
    if (!ok) falhas++;
    console.log(`${ok ? 'PASS' : 'FAIL'} ${path.basename(pagina)}: ${perguntas.length ? perguntas.length + ' perguntas' : 'sem quiz'}${ok ? '' : ' -> ' + achados.slice(0, 4).join('; ') + (achados.length > 4 ? ` (+${achados.length - 4})` : '')}`);
    await p.close();
  }
  await b.close();
  process.exit(falhas ? 1 : 0);
})();
