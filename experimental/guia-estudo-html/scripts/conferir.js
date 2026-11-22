// Confere cada página do curso a 1280 e a 390 px: diagramas desenhados, nenhum erro do Mermaid, console limpo,
// sem rolagem lateral da página e quiz que responde ao toque. Grava uma captura de cada página e largura.
// Uso: NODE_PATH=<bancada>/pw/node_modules node conferir.js <saída> <página.html>...
// Uma linha por página e largura: "OK" ou "FALHA", com o detalhe. Sai 0 se tudo passou, 1 se algo falhou, 2 sem argumento.
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const { pathToFileURL } = require('url');

(async () => {
  const [saida, ...arquivos] = process.argv.slice(2);
  if (!saida || arquivos.length === 0) {
    console.error('uso: node conferir.js <saída> <página.html>...');
    process.exit(2);
  }
  fs.mkdirSync(saida, { recursive: true });
  const browser = await chromium.launch();
  let falhas = 0;
  for (const arq of arquivos) {
    for (const largura of [1280, 390]) {
      const page = await browser.newPage({ viewport: { width: largura, height: 900 } });
      const erros = [];
      page.on('console', m => { if (m.type() === 'error') erros.push(m.text()); });
      page.on('pageerror', e => erros.push(String(e)));
      await page.goto(pathToFileURL(path.resolve(arq)).href, { waitUntil: 'networkidle' });
      // Espera o Mermaid desenhar todos os blocos; sem rede, ou com erro, segue e o resultado acusa.
      await page.waitForFunction(() => {
        const blocos = document.querySelectorAll('pre.mermaid');
        return Array.from(blocos).every(b => b.querySelector('svg'));
      }, null, { timeout: 15000 }).catch(() => {});
      await page.waitForTimeout(500);
      const r = await page.evaluate(() => {
        const blocos = Array.from(document.querySelectorAll('pre.mermaid'));
        return {
          blocos: blocos.length,
          feitos: blocos.filter(b => b.querySelector('svg')).length,
          erroMermaid: blocos.filter(b => /Syntax error|Parse error|Unsupported markdown/i.test(b.textContent)).length,
          perguntas: document.querySelectorAll('.pergunta').length,
          rolagem: document.documentElement.scrollWidth - window.innerWidth
        };
      });
      // Quiz: toca a primeira opção de cada pergunta e confere o estado que o quiz.js grava.
      let quizOk = true;
      for (const p of await page.$$('.pergunta')) {
        const b = await p.$('button.opcao');
        if (!b) { quizOk = false; continue; }
        await b.click();
        const resultado = await p.getAttribute('data-resultado');
        const retorno = await p.$eval('.retorno', e => e.textContent.trim()).catch(() => '');
        if (!['certo', 'errado'].includes(resultado) || !retorno) quizOk = false;
      }
      const nome = path.basename(arq, '.html') + '-' + largura + '.png';
      await page.screenshot({ path: path.join(saida, nome), fullPage: true });
      const ok = r.blocos === r.feitos && r.erroMermaid === 0 && erros.length === 0 && r.rolagem <= 0 && quizOk;
      if (!ok) falhas++;
      console.log(`${ok ? 'OK   ' : 'FALHA'} ${path.basename(arq)} @${largura}: diagramas ${r.feitos}/${r.blocos}, erro mermaid ${r.erroMermaid}, perguntas ${r.perguntas}, quiz ${quizOk ? 'ok' : 'FALHA'}, rolagem ${r.rolagem}px, console ${erros.length}${erros.length ? ' -> ' + erros.slice(0, 3).join(' | ') : ''}`);
      await page.close();
    }
  }
  await browser.close();
  process.exit(falhas ? 1 : 0);
})();
