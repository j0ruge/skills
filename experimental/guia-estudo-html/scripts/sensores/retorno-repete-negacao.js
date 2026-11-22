// Regra: toca cada opção errada de cada pergunta e confere que o retorno começa por GUIA_TEXTOS.aindaNao e
// que a palavra seguinte não repete a negação (não está em GUIA_TEXTOS.negacoes). Lê o texto do retorno
// só para comparar com o textos.js, nunca com uma frase escrita aqui.
// Página sem quiz passa e diz isso.
// Uso: NODE_PATH=<bancada>/pw/node_modules node retorno-repete-negacao.js <página.html>...
const { chromium } = require('playwright');
const path = require('path');
const { pathToFileURL } = require('url');
const limpa = s => s.toLowerCase().replace(/^[^\p{L}\p{N}]+|[^\p{L}\p{N}]+$/gu, '');
(async () => {
  const paginas = process.argv.slice(2);
  if (!paginas.length) { console.error('uso: retorno-repete-negacao.js <página.html>...'); process.exit(2); }
  const b = await chromium.launch();
  let falhas = 0;
  for (const pagina of paginas) {
    const p = await b.newPage({ viewport: { width: 1366, height: 768 } });
    await p.route(u => u.protocol !== 'file:', r => r.abort());
    await p.goto(pathToFileURL(path.resolve(pagina)).href, { waitUntil: 'domcontentloaded' });
    await p.waitForTimeout(300);
    const T = await p.evaluate(() => window.GUIA_TEXTOS || {});
    const negacoes = (T.negacoes || []).map(limpa);
    const achados = [];
    let erradas = 0;
    const perguntas = await p.$$('.pergunta');
    for (let q = 0; q < perguntas.length; q++) {
      const per = perguntas[q];
      const certa = parseInt(await per.getAttribute('data-certa'), 10);
      const bs = await per.$$('button.opcao');
      for (let i = 0; i < bs.length; i++) {
        if (i + 1 === certa) continue;
        erradas++;
        await bs[i].click();
        const t = (await per.$eval('.retorno', e => e.textContent)).trim();
        if (!T.aindaNao || !t.startsWith(T.aindaNao)) { achados.push(`P${q + 1} opção ${i + 1}: começa por "${t.slice(0, 20)}"`); continue; }
        const resto = t.slice(T.aindaNao.length).trim();
        const primeira = limpa((resto.split(/\s+/)[0]) || '');
        if (primeira && negacoes.includes(primeira)) achados.push(`P${q + 1} opção ${i + 1}: repete a negação "${resto.slice(0, 22)}…"`);
      }
    }
    if (erradas && !negacoes.length) achados.push('sem negacoes no GUIA_TEXTOS');
    const ok = achados.length === 0;
    if (!ok) falhas++;
    console.log(`${ok ? 'PASS' : 'FAIL'} ${path.basename(pagina)}: ${erradas ? erradas + ' opções erradas' : 'sem opção errada'}${ok ? '' : ', ' + achados.length + ' com defeito -> ' + achados.slice(0, 3).join('; ')}`);
    await p.close();
  }
  await b.close();
  process.exit(falhas ? 1 : 0);
})();
