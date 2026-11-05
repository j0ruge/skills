#!/usr/bin/env node
// Layout check for the built deck: fails when a slide leaves the window, clips text, runs under its source line or
// enters the footer.
//
// Usage: node check-fit.mjs dist/<name>.html
// Exit:  0 everything fits · 1 a slide failed · 2 could not measure (no slides, no #stage or #footer, navigation that
//        did not reach the slide). A sensor that read nothing never says "ok".
//
// Why: build.py, shoot.sh and check-presenter do not measure fit. In the Portal deck (03/11/2026) a request that
// wrapped to 2 lines put the .act box 20 px inside the footer with all of them green. The footer sits inside the
// slide, so comparing content with the slide's edge does not see it.
//
// Each slide is measured fully revealed, its fullest state, at Full HD, on both laptops and on a laptop under a
// browser frame. Anything that paints counts against the footer: text, a background, a border, an image, an SVG.
import { createRequire } from 'node:module';
import { execSync } from 'node:child_process';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const SIZES = [[1920, 1080], [1366, 768], [1280, 720], [1366, 657]];

/** Runs in the page. Measures the active slide against the window, its own box, its source line and the footer. */
function measure() {
  const stage = document.getElementById('stage').getBoundingClientRect();
  const footer = document.getElementById('footer');
  const fs = getComputedStyle(footer);
  const footerOn = fs.display !== 'none' && fs.visibility !== 'hidden' && Number(fs.opacity) > 0;
  const footerTop = footer.getBoundingClientRect().top;
  const slide = document.querySelector('section.slide.active');
  const box = slide.getBoundingClientRect();
  const srcEl = slide.querySelector('.src');
  const srcBottom = srcEl ? srcEl.getBoundingClientRect().bottom : null;
  const label = (el) => `${el.tagName.toLowerCase()}.${el.className?.baseVal ?? el.className}`.slice(0, 60);
  const bad = new Set();
  let lowest = 0;
  let who = '';
  for (const el of slide.querySelectorAll('*')) {
    if (el.closest('aside.notes') || (el.closest('svg') && el.tagName.toLowerCase() !== 'svg')) continue;
    const cs = getComputedStyle(el);
    const r = el.getBoundingClientRect();
    if (cs.display === 'none' || cs.visibility === 'hidden' || Number(cs.opacity) === 0 || !r.width || !r.height) continue;
    const hasText = [...el.childNodes].some((c) => c.nodeType === Node.TEXT_NODE && c.textContent.trim());
    const anyText = Boolean(el.innerText?.trim());
    const hasBg = !/^(transparent|rgba\(\d+, \d+, \d+, 0\))$/.test(cs.backgroundColor) || cs.backgroundImage !== 'none';
    const hasBorder = ['Top', 'Right', 'Bottom', 'Left'].some((s) => parseFloat(cs[`border${s}Width`]) > 0 && cs[`border${s}Style`] !== 'none');
    const media = ['IMG', 'SVG', 'CANVAS', 'VIDEO', 'PICTURE'].includes(el.tagName.toUpperCase());
    if (r.right > box.right + 1 || r.bottom > box.bottom + 1 || r.left < box.left - 1 || r.top < box.top - 1) bad.add(`fora da lâmina: ${label(el)}`);
    if (anyText && ['hidden', 'clip'].includes(cs.overflowX) && el.scrollWidth > el.clientWidth + 1) bad.add(`cortado na largura: ${label(el)}`);
    if (anyText && ['hidden', 'clip'].includes(cs.overflowY) && el.scrollHeight > el.clientHeight + 1) bad.add(`cortado na altura: ${label(el)}`);
    if (anyText && srcBottom !== null && !el.closest('.src') && r.top >= srcBottom - 1) bad.add(`abaixo da fonte: ${label(el)}`);
    if ((hasText || hasBg || hasBorder || media) && r.bottom > lowest) { lowest = r.bottom; who = label(el); }
  }
  const scale = stage.width / 1920;
  return {
    index: [...document.querySelectorAll('section.slide')].indexOf(slide) + 1,
    at: slide.dataset.at ?? '0',
    inWindow: stage.left >= -1 && stage.top >= -1 && stage.right <= innerWidth + 1 && stage.bottom <= innerHeight + 1,
    gap: footerOn ? Math.round((footerTop - lowest) / scale) : null,
    who,
    bad: [...bad].slice(0, 5),
  };
}

/** Opens slide n fully revealed. The engine reads the hash only on load, so a change of hash alone would not reach it. */
async function open(page, url, n, steps) {
  await page.goto('about:blank');
  await page.goto(`${url}#${n}.${steps}`);
  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(250);
}

/** Measures every slide at one window size. Returns how many failed; throws when navigation misses a slide. */
async function measureSize(nav, url, steps, [w, h]) {
  const ctx = await nav.newContext({ viewport: { width: w, height: h }, reducedMotion: 'reduce' });
  const page = await ctx.newPage();
  const failed = [];
  const noFooter = [];
  let smallest = Infinity;
  let where = 0;
  for (let n = 1; n <= steps.length; n++) {
    await open(page, url, n, steps[n - 1]);
    const m = await page.evaluate(measure);
    if (m.index !== n || String(m.at) !== String(steps[n - 1])) throw new Error(`a navegação não chegou à lâmina ${n}.${steps[n - 1]}: ativa ${m.index}, etapa ${m.at}`);
    if (m.gap === null) noFooter.push(n);
    else if (m.gap < smallest) { smallest = m.gap; where = n; }
    const inFooter = m.gap !== null && m.gap < 0;
    if (m.bad.length || !m.inWindow || inFooter) {
      failed.push({ n, ...(m.inWindow ? {} : { palco: 'fora da janela' }), ...(m.bad.length ? { caixas: m.bad } : {}), ...(inFooter ? { rodape: m.gap, quem: m.who } : {}) });
    }
  }
  await ctx.close();
  const gap = where ? `menor folga do rodapé ${smallest} px (lâmina ${where})` : 'nenhuma lâmina com rodapé';
  console.log(`${w}x${h}: ${gap}; sem rodapé: ${noFooter.join(', ') || 'nenhuma'}; reprovadas: ${failed.length ? JSON.stringify(failed) : 'nenhuma'}`);
  return failed.length;
}

const file = process.argv[2];
if (!file) { console.error('uso: node check-fit.mjs dist/<deck>.html'); process.exit(2); }
let pw;
try { pw = createRequire(import.meta.url)('playwright'); } catch {
  try { pw = createRequire(execSync('npm root -g').toString().trim() + '/')('playwright'); } catch {
    console.error('check-fit: precisa do Playwright (npm i -g playwright, ou npm i --prefix <pasta> playwright e NODE_PATH=<pasta>/node_modules)'); process.exit(2);
  }
}
const nav = await pw.chromium.launch({ channel: 'chrome' }).catch(() => pw.chromium.launch());
const url = pathToFileURL(resolve(file)).href;
try {
  const first = await nav.newPage({ viewport: { width: 1920, height: 1080 } });
  await first.goto(`${url}#1`);
  const deck = await first.evaluate(() => ({
    steps: [...document.querySelectorAll('section.slide')].map((s) => Number(s.dataset.steps || 0)),
    engine: Boolean(document.getElementById('stage') && document.getElementById('footer')),
  }));
  await first.close();
  if (!deck.steps.length || !deck.engine) {
    console.error(`check-fit: nada para medir em ${file}: ${deck.steps.length} section.slide; #stage e #footer ${deck.engine ? 'presentes' : 'ausentes'}`);
    process.exitCode = 2;
  } else {
    let failed = 0;
    for (const size of SIZES) failed += await measureSize(nav, url, deck.steps, size);
    console.log(failed ? `FALHOU: ${failed} reprovação(ões) em ${deck.steps.length} lâminas` : `encaixe ok: ${deck.steps.length} lâminas em ${SIZES.length} tamanhos`);
    process.exitCode = failed ? 1 : 0;
  }
} catch (e) {
  console.error(`check-fit: ${e.message}`);
  process.exitCode = 2;
} finally {
  await nav.close();
}
