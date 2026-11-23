// Regra: com a rede externa sem resposta, a página pinta e o quiz responde logo.
// Todo pedido que não é file: fica pendurado (nunca responde). Passa se o domcontentloaded e a primeira
// pintura vêm em até 3 s e, havendo quiz, se o retorno aparece em até 2 s depois.
// Uso: NODE_PATH=<bancada>/pw/node_modules node rede-pendurada.js <página.html>...
const { chromium } = require('playwright');
const path = require('path');
const { pathToFileURL } = require('url');
(async () => {
  const paginas = process.argv.slice(2);
  if (!paginas.length) { console.error('uso: rede-pendurada.js <página.html>...'); process.exit(2); }
  const b = await chromium.launch();
  let falhas = 0;
  for (const pagina of paginas) {
    const nome = path.basename(pagina);
    const p = await b.newPage({ viewport: { width: 390, height: 800 } });
    // Pendura: só o file: segue; o resto nunca responde.
    await p.route(u => u.protocol !== 'file:', () => {});
    const t0 = Date.now();
    let linha;
    try {
      await p.goto(pathToFileURL(path.resolve(pagina)).href, { waitUntil: 'domcontentloaded', timeout: 3000 });
      const tDom = Date.now() - t0;
      // Folha de estilo bloqueante deixa a página em branco: por isso se espera a primeira pintura.
      const pintou = await p.waitForFunction(
        () => performance.getEntriesByName('first-contentful-paint').length > 0,
        null, { timeout: 3000 }).then(() => true, () => false);
      const temQuiz = await p.$('.pergunta button.opcao');
      if (!pintou) {
        linha = `FAIL ${nome}: sem primeira pintura em 3 s, dom=${tDom}ms`;
        falhas += 1;
      } else if (!temQuiz) {
        linha = `PASS ${nome}: dom=${tDom}ms, sem quiz`;
      } else {
        await p.click('.pergunta button.opcao', { timeout: 2000 });
        const ok = await p.waitForFunction(() => {
          const r = document.querySelector('.pergunta .retorno');
          return r && r.textContent.trim().length > 0;
        }, null, { timeout: 2000 }).then(() => true, () => false);
        linha = `${ok ? 'PASS' : 'FAIL'} ${nome}: dom=${tDom}ms, quiz=${Date.now() - t0}ms${ok ? '' : ' (retorno não veio em 2 s)'}`;
        if (!ok) falhas += 1;
      }
    } catch (e) {
      linha = `FAIL ${nome}: ${e.name || 'erro'} em ${Date.now() - t0}ms`;
      falhas += 1;
    }
    console.log(linha);
    await p.close();
  }
  await b.close();
  process.exit(falhas ? 1 : 0);
})().catch(e => { console.log('FAIL erro do sensor: ' + String((e && e.message) || e).split('\n')[0]); process.exit(1); });
