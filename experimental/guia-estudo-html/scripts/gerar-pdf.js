// Gera o PDF de leitura no celular das páginas do curso: caixas <details> abertas, diagramas desenhados,
// página A5 para o texto ficar grande na tela. No papel não há rolagem: o SVG volta a caber na largura
// (min-width zerado) e a dica de rolagem some.
// Uma linha por página: OK ou FAIL, com o número de caixas que ficaram fechadas. Sai 1 se alguma ficou.
// "Fechada" é a caixa sem o conteúdo à vista depois de aberta: um <details> escondido por CSS (display: none no
// conteúdo, ou numa caixa em volta) entra no PDF vazio, mesmo com open = true. Se o Mermaid não desenhar em 30 s,
// a página sai com FAIL e sem PDF, e o script segue para a próxima.
// Precisa de rede para o Mermaid. Uso: NODE_PATH=<bancada>/pw/node_modules node gerar-pdf.js <pasta de saída> <página.html>...
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const { pathToFileURL } = require('url');
(async () => {
  const [saida, ...paginas] = process.argv.slice(2);
  if (!saida || !paginas.length) { console.error('uso: gerar-pdf.js <pasta de saída> <página.html>...'); process.exit(2); }
  fs.mkdirSync(saida, { recursive: true });
  const b = await chromium.launch();
  let falhas = 0;
  for (const pagina of paginas) {
    const nome = path.basename(pagina, '.html');
    const p = await b.newPage({ viewport: { width: 520, height: 900 } });
    await p.goto(pathToFileURL(path.resolve(pagina)).href, { waitUntil: 'load' });
    const total = await p.$$eval('pre.mermaid', l => l.length);
    if (total) {
      const desenhou = await p.waitForFunction(n => document.querySelectorAll('pre.mermaid > svg').length === n, total, { timeout: 30000 }).then(() => true, () => false);
      if (!desenhou) {
        console.log(`FAIL ${nome}: o Mermaid não desenhou em 30 s (sem rede?); sem PDF`);
        falhas += 1;
        await p.close();
        continue;
      }
    }
    await p.evaluate(async () => {
      document.querySelectorAll('details').forEach(d => { d.open = true; });
      document.querySelectorAll('figure.diagrama svg').forEach(s => { s.style.minWidth = '0'; });
      document.querySelectorAll('.dica-rolagem').forEach(d => { d.style.display = 'none'; });
      await document.fonts.ready;
    });
    // Aberta de fato: open, e o primeiro filho que não é o summary está à vista (checkVisibility segue os ancestrais).
    const fechadas = await p.$$eval('details', l => l.filter(d => {
      if (!d.open) return true;
      const corpo = Array.from(d.children).find(c => c.tagName !== 'SUMMARY');
      return !!corpo && !corpo.checkVisibility();
    }).length);
    const arq = path.join(saida, nome + '.pdf');
    await p.pdf({ path: arq, format: 'A5', printBackground: true, margin: { top: '10mm', bottom: '10mm', left: '8mm', right: '8mm' } });
    console.log(`${fechadas ? 'FAIL' : 'OK'} ${arq}: diagramas ${total}, caixas fechadas ${fechadas}`);
    if (fechadas) falhas += 1;
    await p.close();
  }
  await b.close();
  process.exit(falhas ? 1 : 0);
})().catch(e => { console.log('FAIL erro do script: ' + String((e && e.message) || e).split('\n')[0]); process.exit(1); });
