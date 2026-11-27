#!/usr/bin/env node
// Layout check for the built deck: fails when a slide leaves the window, clips text, runs under its source line,
// enters the footer, has a source line that grew into the left margin, or puts text under the PDF page number.
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
//
// Then once more in print, where the footer is gone and .slide::after prints the page number at the bottom right.
// Why: in the TCC deck (26/11/2026) the cover gained a fourth metadata item, and its credit line moved to a second
// row, right-aligned, under "01 / 19" in the PDF. The shot and the four screen sizes were green; only page 1 of the
// PDF showed it. Only text counts here: a photo or a tint under the number is a design choice, text under it is not.
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
  // The source line is anchored right and grows to the left, on one line: a long one enters the slide's left padding
  // and still sits inside the slide's box, so the edge check below does not see it.
  const padLeft = parseFloat(getComputedStyle(slide).paddingLeft) * (box.width / (slide.offsetWidth || box.width));
  const label = (el) => `${el.tagName.toLowerCase()}.${el.className?.baseVal ?? el.className}`.slice(0, 60);
  const bad = new Set();
  if (srcEl && padLeft > 0 && srcEl.getBoundingClientRect().left < box.left + padLeft - 1) bad.add(`fonte na margem esquerda: ${label(srcEl)}`);
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

/** Runs in the page under print media. For each slide, finds visible text whose glyphs cross the page number of
 *  .slide::after. A pseudo-element has no box to read: a probe takes its computed style and its text, and a Range
 *  measures the glyphs, so a number drawn over the whole slide (inset:0, aligned bottom-right) still measures right. */
function measurePrint() {
  const label = (el) => `${el.tagName.toLowerCase()}.${el.className?.baseVal ?? el.className}`.slice(0, 60);
  const cross = (a, b) => a.left < b.right - 1 && b.left < a.right - 1 && a.top < b.bottom - 1 && b.top < a.bottom - 1;
  const out = { measured: 0, without: [], bad: [] };
  [...document.querySelectorAll('section.slide')].forEach((slide, i) => {
    const ps = getComputedStyle(slide, '::after');
    const c = ps.content || '';
    const attr = c.match(/^attr\(\s*([\w-]+)\s*\)$/);
    const text = attr ? slide.getAttribute(attr[1]) || '' : /^".*"$/.test(c) ? c.slice(1, -1) : '';
    if (ps.display === 'none' || !text.trim()) { out.without.push(i + 1); return; }
    const probe = document.createElement('span');
    for (let k = 0; k < ps.length; k++) if (ps[k] !== 'content') probe.style.setProperty(ps[k], ps.getPropertyValue(ps[k]));
    probe.textContent = text;
    slide.appendChild(probe);
    const range = document.createRange();
    range.selectNodeContents(probe);
    const num = range.getBoundingClientRect();
    probe.remove();
    if (!num.width || !num.height) { out.without.push(i + 1); return; }
    out.measured++;
    const under = new Set();
    const walk = document.createTreeWalker(slide, NodeFilter.SHOW_TEXT);
    for (let t = walk.nextNode(); t; t = walk.nextNode()) {
      const el = t.parentElement;
      if (!t.textContent.trim() || el.closest('aside.notes')) continue;
      let seen = true;
      for (let a = el; a && a !== slide.parentElement; a = a.parentElement) {
        const cs = getComputedStyle(a);
        if (cs.display === 'none' || cs.visibility === 'hidden' || Number(cs.opacity) === 0) { seen = false; break; }
      }
      if (!seen) continue;
      const r = document.createRange();
      r.selectNodeContents(t);
      if ([...r.getClientRects()].some((q) => q.width && q.height && cross(q, num))) under.add(label(el));
    }
    if (under.size) out.bad.push({ n: i + 1, numero: text.trim().slice(-12), sob_o_numero: [...under].slice(0, 5) });
  });
  return out;
}

/** Measures the PDF page numbers once, in print media at the page size. Returns how many slides failed. */
async function measurePrintPass(nav, url) {
  const ctx = await nav.newContext({ viewport: { width: 1920, height: 1080 }, reducedMotion: 'reduce' });
  const page = await ctx.newPage();
  await page.goto(url);
  await page.emulateMedia({ media: 'print' });
  await page.evaluate(async () => { void document.body.offsetHeight; await document.fonts.ready; });
  await page.waitForTimeout(250);
  const m = await page.evaluate(measurePrint);
  await ctx.close();
  const without = m.without.length ? (m.measured ? m.without.join(', ') : 'todas') : 'nenhuma';
  console.log(`impressão (PDF): número de página medido em ${m.measured} lâminas; sem número: ${without}; reprovadas: ${m.bad.length ? JSON.stringify(m.bad) : 'nenhuma'}`);
  return m;
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
    const print = await measurePrintPass(nav, url);
    failed += print.bad.length;
    // A deck without a page number in print is reported, not failed: zero numbers measured never reads as "ok" for them.
    const pdf = print.measured ? `número do PDF livre em ${print.measured}` : 'nenhum número de página na impressão (data-print?)';
    console.log(failed ? `FALHOU: ${failed} reprovação(ões) em ${deck.steps.length} lâminas` : `encaixe ok: ${deck.steps.length} lâminas em ${SIZES.length} tamanhos; ${pdf}`);
    process.exitCode = failed ? 1 : 0;
  }
} catch (e) {
  console.error(`check-fit: ${e.message}`);
  process.exitCode = 2;
} finally {
  await nav.close();
}
