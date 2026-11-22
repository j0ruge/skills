// Regra: um desenho que rola dentro do quadro diz como rolar com o aparelho que se tem na mão, e o caminho
// da dica funciona.
//   - A 1366 x 768, com mouse: a dica contém palavraMouse, e Shift com a roda rola o quadro, não a página.
//   - A 390 x 844, com toque: a dica existe em cada quadro que rola.
// Quadro = o pai do SVG do desenho; "rola" = tem texto fora da vista. Página sem desenho que rola passa.
// Precisa de rede para o Mermaid; se ele não desenhar em 20 s, a página falha com o motivo.
// Uso: NODE_PATH=<bancada>/pw/node_modules node desenho-cortado-no-notebook.js <página.html>...
const { chromium } = require('playwright');
const path = require('path');
const { pathToFileURL } = require('url');
const esperar = p => p.waitForFunction(() => Array.from(document.querySelectorAll('pre.mermaid'))
  .every(x => x.querySelector('svg')), null, { timeout: 20000 }).then(() => true, () => false);
// Marca cada quadro que rola com data-sensor-rola e devolve a dica de cada um.
const quadros = p => p.evaluate(() => {
  const saida = [];
  Array.from(document.querySelectorAll('figure.diagrama')).forEach((f, i) => {
    const svg = Array.from(f.querySelectorAll('svg')).find(s => !s.parentElement.closest('svg'));
    if (!svg) return;
    const q = svg.parentElement;
    if (q.scrollWidth - q.clientWidth <= 1) return;
    q.setAttribute('data-sensor-rola', String(i));
    const d = f.querySelector('.dica-rolagem');
    saida.push({ i, dica: d ? d.textContent : '', escondido: q.scrollWidth - q.clientWidth });
  });
  return saida;
});
(async () => {
  const paginas = process.argv.slice(2);
  if (!paginas.length) { console.error('uso: desenho-cortado-no-notebook.js <página.html>...'); process.exit(2); }
  const b = await chromium.launch();
  let falhas = 0;
  for (const pagina of paginas) {
    const url = pathToFileURL(path.resolve(pagina)).href;
    const achados = [];
    const resumo = [];
    // Notebook: mouse, sem toque.
    const c1 = await b.newContext({ viewport: { width: 1366, height: 768 } });
    const p1 = await c1.newPage();
    await p1.goto(url, { waitUntil: 'networkidle' });
    const temMermaid = await p1.$('pre.mermaid');
    if (temMermaid && !(await esperar(p1))) achados.push('o Mermaid não desenhou em 20 s (sem rede?)');
    await p1.waitForTimeout(500);
    const palavraMouse = await p1.evaluate(() => (window.GUIA_TEXTOS || {}).palavraMouse || '');
    const q1 = await quadros(p1);
    for (const q of q1) {
      if (!palavraMouse || !q.dica.toLowerCase().includes(palavraMouse.toLowerCase())) {
        achados.push(`1366, figura ${q.i + 1}: ${q.escondido} px fora da vista, e a dica não fala do mouse ("${q.dica}")`);
      }
      const quadro = await p1.$(`[data-sensor-rola="${q.i}"]`);
      await quadro.evaluate(e => { e.scrollLeft = 0; e.scrollIntoView({ block: 'center' }); });
      await p1.waitForTimeout(200);
      const bb = await quadro.boundingBox();
      await p1.mouse.move(bb.x + bb.width / 2, bb.y + bb.height / 2);
      await p1.keyboard.down('Shift'); await p1.mouse.wheel(0, 300); await p1.keyboard.up('Shift');
      await p1.waitForTimeout(400);
      const r = await quadro.evaluate(e => ({ sl: Math.round(e.scrollLeft), sx: window.scrollX }));
      if (r.sl <= 0) achados.push(`1366, figura ${q.i + 1}: Shift com a roda não rolou o quadro`);
      if (r.sx !== 0) achados.push(`1366, figura ${q.i + 1}: Shift com a roda rolou a página de lado`);
      resumo.push(`1366 fig ${q.i + 1}: ${q.escondido} px fora, Shift+roda ${r.sl} px`);
    }
    await c1.close();
    // Celular: toque.
    const c2 = await b.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true });
    const p2 = await c2.newPage();
    await p2.goto(url, { waitUntil: 'networkidle' });
    if (await p2.$('pre.mermaid')) await esperar(p2);
    await p2.waitForTimeout(500);
    const q2 = await quadros(p2);
    for (const q of q2) if (!q.dica.trim()) achados.push(`390, figura ${q.i + 1}: o quadro rola e não tem dica`);
    resumo.push(`390: ${q2.length} rolam`);
    await c2.close();
    const ok = achados.length === 0;
    if (!ok) falhas++;
    console.log(`${ok ? 'PASS' : 'FAIL'} ${path.basename(pagina)}: ${q1.length ? resumo.join('; ') : 'nenhum desenho rola a 1366; ' + resumo.join('; ')}${ok ? '' : ' -> ' + achados.join('; ')}`);
  }
  await b.close();
  process.exit(falhas ? 1 : 0);
})();
