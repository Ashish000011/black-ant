// Builds black-ant-physics-paper.pdf from paper.html: numbers figures, tables, equations and references,
// typesets the TeX with KaTeX, then prints A4 with headless Chromium (playwright-core).
// Run after figures.py: cd docs/physics && npm ci && node build_paper.mjs
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import katex from "katex";
import { chromium } from "playwright-core";

const here = path.dirname(fileURLToPath(import.meta.url));
let html = fs.readFileSync(path.join(here, "paper.html"), "utf8");

// Figures and tables: number in order, put "Figure n." / "Table n." at the start of each caption.
const labels = {};
let nFig = 0, nTab = 0, nEq = 0;
html = html.replace(/<figure([^>]*?)data-label="([^"]+)"([^>]*)>([\s\S]*?)<figcaption>/g, (m, a, label, b, body) => {
  labels[label] = ++nFig;
  return `<figure${a}id="${label}"${b}>${body}<figcaption><b>Figure ${nFig}.</b> `;
});
html = html.replace(/<div class="table([^"]*)" data-label="([^"]+)">\s*<div class="tcap">/g, (m, cls, label) => {
  labels[label] = ++nTab;
  return `<div class="table${cls}" id="${label}"><div class="tcap"><b>Table ${nTab}.</b> `;
});

// Wide figures and tables sit between two-column blocks (column-span inside a multi-page multicol is unreliable
// in Chromium's print layout).
html = html.replace('<main class="cols">', '<main><div class="cols">').replace("</main>", "</div></main>");
html = html.replace(/(<figure class="wide"[\s\S]*?<\/figure>|<div class="table wide"[\s\S]*?<\/table><\/div>)/g,
  '</div>$1<div class="cols">');

// Display equations: $$ ... \label{eq:x} $$ get \tag{n}.
html = html.replace(/\$\$([\s\S]+?)\$\$/g, (m, tex) => {
  const lab = tex.match(/\\label\{([^}]+)\}/);
  if (lab) {
    labels[lab[1]] = ++nEq;
    tex = tex.replace(lab[0], `\\tag{${nEq}}`);
  }
  return katex.renderToString(tex.trim(), { displayMode: true, throwOnError: true, strict: "ignore" });
});
html = html.replace(/\$([^$\n]+?)\$/g, (m, tex) => katex.renderToString(tex, { throwOnError: true, strict: "ignore" }));

html = html.replace(/\\ref\{([^}]+)\}/g, (m, label) => {
  if (!(label in labels)) throw new Error(`unknown label ${label}`);
  return String(labels[label]);
});

// References: number by first citation; drop any never cited; compress runs (3,4,5 -> 3-5).
const refItems = {};
html = html.replace(/<li data-key="([^"]+)">([\s\S]*?)<\/li>/g, (m, key, body) => {
  refItems[key] = body.trim();
  return "";
});
const order = [];
html = html.replace(/\\cite\{([^}]+)\}/g, (m, keys) => {
  const nums = keys.split(",").map((k) => k.trim()).map((k) => {
    if (!(k in refItems)) throw new Error(`unknown reference ${k}`);
    if (!order.includes(k)) order.push(k);
    return order.indexOf(k) + 1;
  }).sort((x, y) => x - y);
  const parts = [];
  for (let i = 0; i < nums.length; i++) {
    let j = i;
    while (j + 1 < nums.length && nums[j + 1] === nums[j] + 1) j++;
    parts.push(j - i >= 2 ? `${nums[i]}–${nums[j]}` : nums.slice(i, j + 1).join(","));
    i = j;
  }
  return `<span class="cite">[${parts.join(",")}]</span>`;
});
const unused = Object.keys(refItems).filter((k) => !order.includes(k));
if (unused.length) console.warn("references never cited (left out):", unused.join(", "));
html = html.replace("<!--REFERENCES-->", `<ol>${order.map((k) => `<li>${refItems[k]}</li>`).join("\n")}</ol>`);

const built = path.join(here, "paper.built.html");
fs.writeFileSync(built, html);

const browser = await chromium.launch();
const page = await browser.newPage();
await page.goto(pathToFileURL(built).href, { waitUntil: "networkidle" });
await page.evaluate(() => document.fonts.ready);
const head = (left, right) => `<div style="font-family: serif; font-size: 6.5pt; color: #666; width: 100%;
  padding: 0 13.5mm; display: flex; justify-content: space-between;"><span>${left}</span><span>${right}</span></div>`;
const out = path.join(here, "black-ant-physics-paper.pdf");
await page.pdf({
  path: out, format: "A4", printBackground: true, preferCSSPageSize: true, displayHeaderFooter: true,
  headerTemplate: head("Black Ant · Towing Earth to 2.7 AU with a light-held gravity tractor",
    "TransfiNITTe 2026 · technical preprint, not peer reviewed"),
  footerTemplate: head("", `<span class="pageNumber"></span> / <span class="totalPages"></span>`),
});
await browser.close();
console.log(`wrote ${path.relative(process.cwd(), out)}: ${nFig} figures, ${nTab} tables, ${nEq} equations, ${order.length} references`);
