#!/usr/bin/env node
// Regression check for the deck engine: presenter window, shared timer, key hint and focus click.
//
// Usage: node check-presenter.mjs dist/<name>.html [--headed]
//
// Drives Chrome through Playwright (local or global install) on the built deck, at 1366×657 (a 1366×768
// laptop minus the browser frame), and exits 1 when a check fails. Each check is a failure seen in a real
// rehearsal (Manutenção Proativa deck, 16/10/2026). The activation click is simulated with a window
// `focus` event: Playwright emulates focus, so the page never sees the real one (references/engine.md).
import { createRequire } from 'node:module';
import { execSync } from 'node:child_process';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const file = process.argv[2];
if (!file) { console.error('uso: node check-presenter.mjs dist/<deck>.html [--headed]'); process.exit(2); }
let pw;
try { pw = createRequire(import.meta.url)('playwright'); } catch {
  try { pw = createRequire(execSync('npm root -g').toString().trim() + '/')('playwright'); } catch {
    console.error('check-presenter: precisa do Playwright (npm i -g playwright)'); process.exit(2);
  }
}
const headless = !process.argv.includes('--headed');
const browser = await pw.chromium.launch({ channel: 'chrome', headless }).catch(() => pw.chromium.launch({ headless }));
const ctx = await browser.newContext({ viewport: { width: 1366, height: 657 } });
const sleep = ms => new Promise(r => setTimeout(r, ms));
const url = pathToFileURL(resolve(file)).href;
let failed = 0;
const errors = [];
ctx.on('page', p => p.on('pageerror', e => errors.push(e.message)));
const check = (name, ok, got) => { if (!ok) failed++; console.log(`${ok ? 'ok     ' : 'FALHOU '} ${name}${ok ? '' : ` (${got})`}`); };

const page = await ctx.newPage();
await page.goto(url + '#2'); await sleep(600);
const N = await page.evaluate(() => document.querySelectorAll('.slide').length);
const deckIdx = () => page.evaluate(() => +location.hash.slice(1));
const deckClock = () => page.evaluate(() => (document.getElementById('notesPanel').textContent.match(/decorrido\s*(\d\d:\d\d)/) || [])[1]);
const popIdx = p => p.evaluate(() => +document.getElementById('ptitle').textContent.slice(0, 2));
const popClock = p => p.evaluate(() => document.getElementById('pclock').textContent);
const secs = s => +s.slice(0, 2) * 60 + +s.slice(3);
await page.keyboard.press('n');
let [pop] = await Promise.all([page.waitForEvent('popup'), page.keyboard.press('p')]); await sleep(800);

await sleep(3200); await page.keyboard.press('r'); await sleep(300);
let a = await popClock(pop), b = await deckClock();
check('R no deck zera as duas janelas', a === '00:00' && b === '00:00', `popup ${a}, deck ${b}`);

await sleep(3200); await pop.keyboard.press('r'); await sleep(300);
a = await popClock(pop); b = await deckClock();
check('R no popup zera as duas janelas', a === '00:00' && b === '00:00', `popup ${a}, deck ${b}`);

await sleep(3200); await pop.close();
[pop] = await Promise.all([page.waitForEvent('popup'), page.keyboard.press('p')]); await sleep(800);
a = await popClock(pop); b = await deckClock();
check('popup reaberto mostra o tempo já falado', secs(a) >= 3 && Math.abs(secs(a) - secs(b)) <= 1, `popup ${a}, deck ${b}`);

if (N >= 4) {
  await page.reload(); await page.waitForLoadState('load'); await sleep(1500);
  await page.keyboard.press('n'); await sleep(300);
  b = await deckClock();
  check('F5 no deck mantém o tempo', secs(b) >= 3, `deck ${b}`);
  await page.keyboard.press('ArrowRight'); await sleep(400);
  const d = await deckIdx(), p = await popIdx(pop);
  check('F5 no deck: o popup acompanha o deck', d === p, `deck ${d}, popup ${p}`);
  await pop.keyboard.press('ArrowRight'); await sleep(400);
  const d2 = await deckIdx();
  check('F5 no deck: o popup avança uma lâmina, sem salto', d2 === d + 1, `deck ${d} → ${d2}`);
  await sleep(2200);
  check('F5 no deck: a sincronia se mantém', (await deckIdx()) === (await popIdx(pop)), 'divergiu depois de 2 s');
  await page.keyboard.press('ArrowLeft'); await page.keyboard.press('ArrowLeft'); await sleep(400);
} else console.log(`pulado  F5 no deck (o deck tem ${N} lâminas; o teste precisa de 4)`);
await page.keyboard.press('n');

const hint = () => page.evaluate(() => +getComputedStyle(document.getElementById('help')).opacity);
const wiggle = async () => { await page.mouse.move(683, 330); await sleep(80); await page.mouse.move(690, 335); await sleep(400); };
// with the presenter window open the deck is being shown: a shared window would carry the hint to the audience
await wiggle(); const h0 = await hint();
check('dica de teclas não aparece com a janela P aberta', h0 === 0, `opacidade ${h0}`);
await pop.close(); await sleep(300);
await wiggle(); const h1 = await hint(); await sleep(3600); const h2 = await hint();
check('sem a janela P, a dica aparece com o mouse e some parada', h1 > 0.5 && h2 === 0, `opacidade ${h1} → ${h2}`);

// clicks start mid-deck: on the cover a click that goes back changes nothing and would pass by accident
await page.keyboard.press('Home'); await page.keyboard.press('ArrowRight'); await page.keyboard.press('ArrowRight'); await sleep(300);
const box = await page.evaluate(() => { const r = document.getElementById('stage').getBoundingClientRect(); return [r.left, r.top, r.width, r.height]; });
// each click is measured from where it starts: a wrong move by one check must not make the next one pass
const click = async (name, x, y, delta, before = () => {}) => {
  const from = await deckIdx(); await before();
  await page.mouse.click(x, y); await sleep(300);
  const to = await deckIdx();
  check(name, to === from + delta, `lâmina ${from} → ${to}`);
  if (to !== from) await page.keyboard.press(to > from ? 'ArrowLeft' : 'ArrowRight');
  await sleep(500);
};
const cx = box[0] + box[2] / 2, cy = box[1] + box[3] / 2;
if (box[0] > 20) await click('clique na faixa fora do palco não navega', box[0] / 2, cy, 0);
else console.log('pulado  clique fora do palco (o palco ocupa a largura toda)');
await click('clique que só traz a janela à frente não navega', cx, cy, 0, () => page.evaluate(() => dispatchEvent(new FocusEvent('focus'))));
await click('clique comum no palco ainda avança', cx, cy, 1);
await click('clique no terço esquerdo do palco volta', box[0] + box[2] / 6, cy, -1);

check('nenhum erro de script nas duas janelas', !errors.length, errors.slice(0, 3).join(' | '));
await browser.close();
console.log(failed ? `${failed} verificação(ões) falharam` : 'motor ok');
process.exit(failed ? 1 : 0);
