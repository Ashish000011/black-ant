// Builds black-ant-physics-deck.pptx: 11 main slides and 5 hidden backup slides, joined by a clickable map.
// Every number comes from fig/deck_data.json, which figures.py writes from results/ and config.yaml.
// Run after figures.py: cd docs/physics && npm ci && node build_deck.mjs
import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";
import pptxgen from "pptxgenjs";
import React from "react";
import ReactDOMServer from "react-dom/server";
import sharp from "sharp";
import * as Fa from "react-icons/fa6";

const require = createRequire(import.meta.url);
const here = path.dirname(fileURLToPath(import.meta.url));
const D = JSON.parse(fs.readFileSync(path.join(here, "fig", "deck_data.json"), "utf8"));
const OUT = path.join(here, "black-ant-physics-deck.pptx");

// ------------------------------------------------------------------ theme
const THEME = {
  name: "Black Ant physics",
  headFontFace: "Cambria",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "0E1726", lt1: "FFFFFF", dk2: "1D2B45", lt2: "F1F3F6",
    accent1: "E8A317", accent2: "2A78D6", accent3: "EB6834", accent4: "15936A", accent5: "6250D6", accent6: "5B6B85",
    hlink: "2A78D6", folHlink: "6250D6",
  },
};
const HEX = THEME.colors;
const MUTED = "5F6B7A";          // secondary ink on white (hex-only options)
const SOFT = "AEB9CC";           // secondary ink on the dark slides
const GRID = "E3E6EB";

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";     // 13.333 x 7.5 in
pres.title = "Towing Earth to 2.7 AU: the physics";
pres.author = "Team Black Ant";
pres.company = "Team Black Ant";
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
// pptxgenjs registers links only on text runs, images and plain shapes; a text shape's own link (a whole clickable
// tile) gets no relationship. Register it here, the way pptxgenjs numbers its own (getNewRelId).
const addSlide = pres.addSlide.bind(pres);
pres.addSlide = (opts) => {
  const slide = addSlide(opts);
  const addText = slide.addText.bind(slide);
  slide.addText = (text, o = {}) => {
    if (o.hyperlink && !o.hyperlink._rId) {
      const rId = slide._rels.length + slide._relsChart.length + slide._relsMedia.length + 1;
      slide._rels.push({ type: "hyperlink", data: o.hyperlink.slide ? "slide" : "dummy", rId,
        Target: o.hyperlink.slide ? String(o.hyperlink.slide) : o.hyperlink.url });
      o.hyperlink._rId = rId;
    }
    return addText(text, o);
  };
  return slide;
};
const C = pres.SchemeColor;
const SH = pres.ShapeType;

// Slide numbers, fixed so links can point forward.
const S = { title: 1, map: 2, problem: 3, idea: 4, physics: 5, enablers: 6, journey: 7, honest: 8, safe: 9, whatif: 10,
  verdict: 11, e1: 12, e2: 13, e3: 14, stress: 15, longterm: 16 };

// pptxgenjs writes Office's stock palette into the theme; put ours there so scheme colours resolve to it.
async function applyTheme(file, theme) {
  const JSZip = require(require.resolve("jszip", { paths: [require.resolve("pptxgenjs")] }));
  const zip = await JSZip.loadAsync(fs.readFileSync(file));
  const part = "ppt/theme/theme1.xml";
  const slots = ["dk1", "lt1", "dk2", "lt2", "accent1", "accent2", "accent3", "accent4", "accent5", "accent6", "hlink", "folHlink"];
  const scheme = `<a:clrScheme name="${theme.name}">` +
    slots.map((k) => `<a:${k}><a:srgbClr val="${theme.colors[k]}"/></a:${k}>`).join("") + "</a:clrScheme>";
  const xml = (await zip.file(part).async("string")).replace(/<a:clrScheme\b[\s\S]*?<\/a:clrScheme>/, () => scheme)
    .replace(/(<a:(?:theme|fontScheme)\b[^>]*?\bname=")[^"]*"/g, (_, head) => `${head}${theme.name}"`);
  if (!xml.includes(scheme)) throw new Error("theme1.xml has no colour scheme to replace");
  zip.file(part, xml);
  for (const name of Object.keys(zip.files).filter((n) => n.endsWith(".xml"))) {
    const bad = (await zip.file(name).async("string")).match(/<a:srgbClr val="((?![0-9A-Fa-f]{6}")[^"]*)"/);
    if (bad) throw new Error(`${name}: colour "${bad[1]}" is not hex (a scheme colour in a hex-only option)`);
  }
  fs.writeFileSync(file, await zip.generateAsync({ type: "nodebuffer", compression: "DEFLATE" }));
}

// ------------------------------------------------------------------ helpers
const SUP = { "0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴", "5": "⁵", "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹", "-": "⁻" };
// (Unicode superscripts are used only inside chart titles, where text runs cannot be styled.)
const sup = (s) => String(s).split("").map((c) => SUP[c] ?? c).join("");
// 9.27e25 -> "9.27×10²⁵" (Unicode superscripts: for labels inside charts, where runs cannot be styled)
function sciU(x, digits = 2) {
  const [m, e] = x.toExponential(digits).split("e");
  return `${m}×10${sup(Number(e))}`;
}
// 9.27e25 -> "9.27×10^{25}" for rich()
function sci(x, digits = 2) {
  const [m, e] = x.toExponential(digits).split("e");
  return `${m}×10^{${Number(e)}}`;
}
const fmt = (x, d = 0) => x.toLocaleString("en-US", { minimumFractionDigits: d, maximumFractionDigits: d });

// "a_{E} = 6.5×10^{-8}" -> text runs with real sub/superscripts. opts apply to every run.
function rich(str, opts = {}) {
  const runs = [];
  for (const part of String(str).split(/(\^\{[^}]*\}|_\{[^}]*\})/)) {
    if (!part) continue;
    if (part.startsWith("^{")) runs.push({ text: part.slice(2, -1).replace(/-/g, "−"), options: { ...opts, superscript: true } });
    else if (part.startsWith("_{")) runs.push({ text: part.slice(2, -1).replace(/-/g, "−"), options: { ...opts, subscript: true } });
    else runs.push({ text: part, options: { ...opts } });
  }
  return runs;
}
// Paragraphs: [[string, opts], ...] -> runs with line breaks between paragraphs.
function paras(list) {
  const out = [];
  list.forEach(([str, opts], i) => {
    const runs = rich(str, opts);
    if (i < list.length - 1) runs[runs.length - 1].options.breakLine = true;
    out.push(...runs);
  });
  return out;
}

const iconCache = {};
async function icon(name, color) {
  const key = `${name}-${color}`;
  if (!iconCache[key]) {
    const svg = ReactDOMServer.renderToStaticMarkup(React.createElement(Fa[name], { color: `#${color}`, size: 256 }));
    const png = await sharp(Buffer.from(svg)).png().toBuffer();
    iconCache[key] = "image/png;base64," + png.toString("base64");
  }
  return iconCache[key];
}

// An icon in a coloured circle; optional link to a slide.
async function badge(slide, name, x, y, d, fill, link) {
  const opts = { x, y, w: d, h: d, fill: { color: fill }, line: { color: fill }, objectName: `badge ${name}` };
  if (link) opts.hyperlink = { slide: link, tooltip: "Open" };
  slide.addShape(SH.ellipse, opts);
  const img = { data: await icon(name, "FFFFFF"), x: x + d * 0.24, y: y + d * 0.24, w: d * 0.52, h: d * 0.52,
    objectName: `icon ${name}` };
  if (link) img.hyperlink = { slide: link, tooltip: "Open" };
  slide.addImage(img);
}

async function mapButton(slide, dark = false) {
  slide.addText("Map", {
    shape: SH.roundRect, rectRadius: 0.21, x: 11.85, y: 0.42, w: 1.0, h: 0.42, align: "right", valign: "middle",
    fontSize: 12, bold: true, color: dark ? C.background1 : C.text1, fill: { color: dark ? HEX.dk2 : HEX.lt2 },
    line: { color: dark ? HEX.dk2 : HEX.lt2 }, margin: [0, 12, 0, 0], hyperlink: { slide: S.map, tooltip: "Back to the map" },
    objectName: "Map button",
  });
  slide.addImage({ data: await icon("FaMap", dark ? "FFFFFF" : HEX.dk1), x: 12.0, y: 0.52, w: 0.22, h: 0.22,
    hyperlink: { slide: S.map, tooltip: "Back to the map" }, objectName: "Map icon" });
}

async function backButton(slide, target, label) {
  slide.addText(`Back to ${label}`, {
    shape: SH.roundRect, rectRadius: 0.21, x: 8.55, y: 0.42, w: 3.15, h: 0.42, align: "right", valign: "middle",
    fontSize: 12, bold: true, color: C.background1, fill: { color: HEX.dk1 }, line: { color: HEX.dk1 },
    margin: [0, 12, 0, 0], hyperlink: { slide: target, tooltip: `Back to ${label}` }, objectName: "Back button",
  });
  slide.addImage({ data: await icon("FaArrowLeft", "FFFFFF"), x: 8.72, y: 0.52, w: 0.22, h: 0.22,
    hyperlink: { slide: target, tooltip: `Back to ${label}` }, objectName: "Back icon" });
}

function card(slide, x, y, w, h, fill = HEX.lt2, name = "card", link) {
  const o = { x, y, w, h, rectRadius: 0.12, fill: { color: fill }, line: { color: fill }, objectName: name };
  if (link) o.hyperlink = { slide: link, tooltip: "Open the details" };
  slide.addShape(SH.roundRect, o);
}

function source(slide, text, dark = false) {
  slide.addText(rich(text), { x: 0.6, y: 6.7, w: 10.6, h: 0.3, fontSize: 10, color: dark ? SOFT : MUTED, margin: 0,
    isTextBox: true, objectName: "source" });
}

// A straight arrow from (x1,y1) to (x2,y2).
function arrow(slide, x1, y1, x2, y2, color, width = 2.5, head = true, dash) {
  const line = { color, width };
  if (head) line.endArrowType = "triangle";
  if (dash) line.dashType = dash;
  slide.addShape(SH.line, { x: Math.min(x1, x2), y: Math.min(y1, y2), w: Math.max(Math.abs(x2 - x1), 0.001),
    h: Math.max(Math.abs(y2 - y1), 0.001), flipH: x2 < x1, flipV: y2 < y1, line, objectName: "arrow" });
}

function chartBase(extra = {}) {
  return {
    catAxisLabelColor: MUTED, valAxisLabelColor: MUTED, catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt",
    catAxisLabelFontSize: 11, valAxisLabelFontSize: 11, valGridLine: { color: GRID, size: 0.75 },
    catGridLine: { style: "none" }, catAxisLineShow: true, catAxisLineColor: "C9CED6", valAxisLineShow: false,
    showLegend: false, legendFontFace: "+mn-lt", legendFontSize: 11, legendColor: MUTED,
    titleFontFace: "+mn-lt", titleColor: HEX.dk1, titleFontSize: 13, dataLabelFontFace: "+mn-lt",
    dataLabelFontSize: 11, dataLabelColor: HEX.dk1, valAxisTitleFontFace: "+mn-lt", valAxisTitleColor: MUTED,
    valAxisTitleFontSize: 11, catAxisTitleFontFace: "+mn-lt", catAxisTitleColor: MUTED, catAxisTitleFontSize: 11,
    ...extra,
  };
}

function title(slide, text) {
  slide.addText(rich(text), { placeholder: "title" });
}

// ------------------------------------------------------------------ layouts
pres.defineSlideMaster({
  title: "DARK", background: { color: HEX.dk1 },
  objects: [{ placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.35, w: 10.9, h: 0.95, fontSize: 36,
    bold: true, color: C.background1, valign: "middle", align: "left", margin: 0 }, text: "" } }],
});
pres.defineSlideMaster({
  title: "CONTENT", background: { color: HEX.lt1 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.35, w: 10.9, h: 0.95, fontSize: 36, bold: true,
      color: C.text1, valign: "middle", align: "left", margin: 0 }, text: "" } },
    { text: { text: "Black Ant · towing Earth to 2.7 AU", options: { x: 0.6, y: 7.05, w: 6, h: 0.3, fontSize: 10,
      color: MUTED, margin: 0 } } },
  ],
  slideNumber: { x: 12.25, y: 7.05, w: 0.6, h: 0.3, fontSize: 10, color: MUTED, align: "right" },
});
pres.defineSlideMaster({
  title: "BACKUP", background: { color: "F6F7F9" },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.35, w: 7.8, h: 0.95, fontSize: 34, bold: true,
      color: C.text1, valign: "middle", align: "left", margin: 0 }, text: "" } },
    { text: { text: "Backup slide · skipped in the slideshow; reached by clicking", options: { x: 0.6, y: 7.05, w: 7,
      h: 0.3, fontSize: 10, color: MUTED, margin: 0 } } },
  ],
  slideNumber: { x: 12.25, y: 7.05, w: 0.6, h: 0.3, fontSize: 10, color: MUTED, align: "right" },
});

// ------------------------------------------------------------------ numbers used on several slides
const sm = D.summary;
const arr = sm.tows["earth-tow"].arrival;
const marsArr = sm.tows["mars-tow"].arrival;
const dv = D.derived;
const lg = sm.ledger;
const cl = sm.climate;
const en = D.enablers;
const lt = D.longterm;
const l1 = D.optics.l1.by_transmission["0.95"];
const eYear = fmt(Math.round(arr.year));
const mYear = fmt(Math.round(marsArr.year));
const beamPct = Math.round((sm.total_beam_max_w / en.e1_beam_limit_w) * 100);

// ================================================================== 1 Title
{
  pres.addSection({ title: "Main talk" });
  const s = pres.addSlide({ masterName: "DARK", sectionTitle: "Main talk" });
  // orbit motif on the right: today's orbit and the target, the Sun at the centre
  const cx = 13.6, cy = 3.75;
  for (const [r, col] of [[1.55, "2B3B5E"], [4.2, "2B3B5E"]]) {
    s.addShape(SH.ellipse, { x: cx - r, y: cy - r, w: 2 * r, h: 2 * r, fill: { type: "none" }, line: { color: col, width: 1.25 },
      objectName: "orbit" });
  }
  s.addShape(SH.ellipse, { x: cx - 0.5, y: cy - 0.5, w: 1.0, h: 1.0, fill: { color: HEX.accent1 }, line: { color: HEX.accent1 },
    objectName: "Sun" });
  s.addShape(SH.ellipse, { x: cx - 1.55 * 0.87 - 0.13, y: cy - 1.55 * 0.5 - 0.13, w: 0.26, h: 0.26,
    fill: { color: HEX.accent2 }, line: { color: HEX.accent2 }, objectName: "Earth today" });
  s.addShape(SH.ellipse, { x: cx - 4.2 * 0.6 - 0.15, y: cy - 4.2 * 0.8 - 0.15, w: 0.3, h: 0.3,
    fill: { color: HEX.accent2 }, line: { color: HEX.accent2 }, objectName: "Earth at 2.7 AU" });
  s.addText("TransfiNITTe 2026 · Team Black Ant", { x: 0.6, y: 0.75, w: 8, h: 0.4, fontSize: 14, bold: true,
    color: C.accent1, margin: 0, isTextBox: true, charSpacing: 2 });
  s.addText("Towing Earth to 2.7 AU", { x: 0.6, y: 1.2, w: 9.5, h: 0.95, fontSize: 48, bold: true, fontFace: "Cambria",
    color: C.background1, margin: 0, valign: "middle", isTextBox: true });
  s.addText("A gravity tractor held by light: the physics that makes it work", { x: 0.6, y: 2.2, w: 9.4, h: 0.6,
    fontSize: 22, color: "CADCFC", margin: 0, isTextBox: true });
  const tiles = [
    [`Year ${eYear}`, `Earth reaches ${arr.a_au} AU (limit: year 10,000)`],
    ["0", `unresolved flags; ${sm.flags.covered_by_enablers} covered by our enablers E1–E3`],
    [sci(lg.nothing_from_nothing_max, 1), "momentum ledger closure (limit 10^{-9})"],
  ];
  tiles.forEach(([big, small], i) => {
    const x = 0.6 + i * 3.15;
    s.addShape(SH.roundRect, { x, y: 3.25, w: 2.95, h: 1.75, rectRadius: 0.12, fill: { color: HEX.dk2 }, line: { color: HEX.dk2 },
      objectName: `title stat ${i + 1}` });
    s.addText(rich(big, { fontSize: 34, bold: true, color: C.accent1, fontFace: "Cambria" }), { x: x + 0.25, y: 3.4, w: 2.5,
      h: 0.75, margin: 0, valign: "middle", isTextBox: true });
    s.addText(rich(small, { fontSize: 13, color: C.background1 }), { x: x + 0.25, y: 4.15, w: 2.5, h: 0.75, margin: 0,
      valign: "top", isTextBox: true });
  });
  s.addText("Ashish Bharti · Madhukar Verma · Akhil Semwal · Sushmit Sukla · Prabhanshu Kerketa", { x: 0.6, y: 5.75,
    w: 9, h: 0.35, fontSize: 13, color: SOFT, margin: 0, isTextBox: true });
  s.addText("Open the map", { shape: SH.roundRect, rectRadius: 0.25, x: 0.6, y: 6.3, w: 2.4, h: 0.5, fontSize: 14, bold: true,
    color: C.text1, fill: { color: HEX.accent1 }, line: { color: HEX.accent1 }, align: "center", valign: "middle",
    hyperlink: { slide: S.map, tooltip: "Go to the map" }, objectName: "Open the map" });
  s.addNotes(`Our brief: move Earth from 1 AU to about 2.7 AU in under 10,000 years without harming it. Our answer is a gravity tractor: an asteroid whose gravity pulls Earth, held in place by focused light. In our full N-body simulation Earth arrives in year ${eYear}, every force is booked with its reaction, and no flag is left unresolved. Click "Open the map" to navigate; every slide has a Map button to come back.`);
}

// ================================================================== 2 Map
{
  const s = pres.addSlide({ masterName: "DARK", sectionTitle: "Main talk" });
  title(s, "Map of the talk");
  s.addText("Click a tile to jump there. Every slide has a Map button to come back; cards marked “details” open backup slides.",
    { x: 0.6, y: 1.25, w: 11.5, h: 0.4, fontSize: 14, color: SOFT, margin: 0, isTextBox: true });
  const tiles = [
    ["FaBan", "The problem", "Arms on Earth can't push it", S.problem, HEX.accent3],
    ["FaLightbulb", "The idea", "An asteroid held by light", S.idea, HEX.accent1],
    ["FaSquareRootVariable", "The physics", "Three equations, by hand", S.physics, HEX.accent2],
    ["FaBolt", "The enablers", "E1, E2, E3 and sources", S.enablers, HEX.accent1],
    ["FaRoute", "The journey", `${eYear} years, Mars first`, S.journey, HEX.accent2],
    ["FaScaleBalanced", "Honest physics", "Every push booked", S.honest, HEX.accent5],
    ["FaShieldHalved", "Earth stays safe", "Ten thresholds, all held", S.safe, HEX.accent4],
    ["FaFlask", "What if…?", "Tests that shaped it", S.whatif, HEX.accent3],
    ["FaListCheck", "Verdict and limits", "What holds, what we assume", S.verdict, HEX.accent6],
  ];
  for (let i = 0; i < tiles.length; i++) {
    const [ic, head, line, link, col] = tiles[i];
    const x = 0.6 + (i % 3) * 4.1, y = 1.95 + Math.floor(i / 3) * 1.68;
    s.addText([
      { text: `${i + 1}  ${head}`, options: { fontSize: 18, bold: true, color: C.background1, breakLine: true } },
      { text: line, options: { fontSize: 13, color: "CADCFC" } },
    ], { shape: SH.roundRect, rectRadius: 0.12, x, y, w: 3.85, h: 1.45, fill: { color: HEX.dk2 }, line: { color: HEX.dk2 },
      margin: [76, 10, 0, 0], valign: "middle", hyperlink: { slide: link, tooltip: `Go to: ${head}` }, objectName: `tile ${head}` });
    await badge(s, ic, x + 0.25, y + 0.42, 0.62, col, link);
  }
  s.addNotes("This is the hub. In a live talk go through 1 to 9 in order; in Q&A click straight to what was asked. The enabler and what-if cards open hidden backup slides with the details and sources.");
}

// ================================================================== 3 The problem
{
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Main talk" });
  title(s, "You can't push a planet from inside");
  await mapButton(s);
  const pts = [
    ["FaRightLeft", "Newton's third law", `Arms rooted on Earth push Earth, and Earth pushes back. In our audit the core's ${sci(D.octo.net_force_n, 2)} N push on the arms and the arms' push on the core cancel to ${sci(D.octo.net_share, 1)}.`, HEX.accent3],
    ["FaTriangleExclamation", "The arms can't hold themselves up", `Curled as the company's demo draws it, a ${fmt(D.octo.arm_km)} km arm breaks at its root past ${fmt(D.octo.materials[0].curled_km)} km in steel and ${fmt(D.octo.materials[2].curled_km)} km in ideal nanotube.`, HEX.accent3],
    ["FaEarthAmericas", "So the force must come from outside", "Another body's gravity is a real outside force, and nothing has to touch Earth.", HEX.accent2],
  ];
  for (let i = 0; i < pts.length; i++) {
    const y = 1.55 + i * 1.65;
    await badge(s, pts[i][0], 0.6, y + 0.05, 0.62, pts[i][3]);
    s.addText(paras([[pts[i][1], { fontSize: 18, bold: true, color: C.text1 }], [pts[i][2], { fontSize: 14, color: C.text1 }]]),
      { x: 1.45, y, w: 4.95, h: 1.5, margin: 0, valign: "top", isTextBox: true, paraSpaceAfter: 4 });
  }
  const m = D.octo.materials;
  const names = ["Steel S355", "CFRP", "Nanotube (ideal)", "Graphene (ideal)", "Demo's arm"];
  s.addChart(pres.ChartType.bar, [
    { name: "Longest curled arm at safety factor 1.5", labels: names, values: [...m.map((x) => Math.round(x.curled_km)), null] },
    { name: "Arm the demo draws", labels: names, values: [null, null, null, null, D.octo.arm_km] },
  ], chartBase({ x: 6.75, y: 1.45, w: 6.0, h: 5.1, barDir: "col", barGrouping: "stacked", chartColors: [HEX.accent6, HEX.accent3],
    valAxisLogScaleBase: 10, valAxisMinVal: 1, valAxisMaxVal: 100000, showValue: true, dataLabelPosition: "inEnd",
    dataLabelFormatCode: "#,##0", dataLabelColor: "FFFFFF", showTitle: true, title: "Longest arm that holds, curled (km, log scale)",
    valAxisLabelFormatCode: "#,##0", barGapWidthPct: 45, showLegend: true, legendPos: "b" }));
  source(s, "Source: results/octo_earth.json (sim/scenarios/octo.py; test X8). Standing straight up, arms buckle past 471 km (steel) or 1,444 km (nanotube).");
  s.addNotes("The brief's reference concept, Octo-Earth, puts arms on Earth. But forces between the arms and Earth are internal: they cancel, so Earth's centre of mass cannot move. We checked it with the same physics as our own machine: the two pushes cancel to 3 parts in 10 trillion. The arms also break under their own weight long before 12,000 km. So the push has to come from outside Earth.");
}

// ================================================================== 4 The idea
{
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Main talk" });
  title(s, "The idea: a gravity tractor held by light");
  await mapButton(s);
  card(s, 0.6, 1.45, 7.5, 5.15, "F6F7F9", "diagram panel");
  // diagram: Sun far left, Earth moving up, asteroid at 45 deg between ahead and away from the Sun
  const E = [3.0, 5.45], A = [4.85, 3.6], M = [5.75, 2.7];
  s.addShape(SH.ellipse, { x: 0.75, y: 2.15, w: 1.1, h: 1.1, fill: { color: HEX.accent1 }, line: { color: HEX.accent1 }, objectName: "Sun" });
  s.addText("Sun (far away)", { x: 0.7, y: 3.3, w: 1.6, h: 0.3, fontSize: 11, color: MUTED, margin: 0, isTextBox: true });
  arrow(s, 1.95, M[1], M[0] - 0.05, M[1], HEX.accent1, 6);                       // light in
  s.addText(rich("light in (E1)", { fontSize: 13, bold: true, color: "8A5D00" }), { x: 2.1, y: 2.25, w: 2.2, h: 0.35, margin: 0, isTextBox: true });
  arrow(s, M[0], M[1] + 0.05, M[0], 6.35, HEX.accent1, 6);                       // light out
  s.addText(rich("light out", { fontSize: 13, bold: true, color: "8A5D00" }), { x: M[0] + 0.15, y: 5.7, w: 1.4, h: 0.35, margin: 0, isTextBox: true });
  s.addShape(SH.line, { x: M[0] - 0.42, y: M[1] - 0.42, w: 0.84, h: 0.84, line: { color: HEX.dk1, width: 7 }, objectName: "mirror" });
  s.addText("mirror (E2)", { x: M[0] + 0.45, y: M[1] - 0.05, w: 1.5, h: 0.32, fontSize: 13, bold: true, color: C.text1, margin: 0, isTextBox: true });
  arrow(s, M[0] + 0.15, M[1] - 0.15, M[0] + 0.7, M[1] - 0.7, "8A5D00", 3.5);      // light's push
  s.addText("push", { x: M[0] + 0.75, y: M[1] - 1.0, w: 0.8, h: 0.3, fontSize: 12, color: "8A5D00", margin: 0, isTextBox: true });
  arrow(s, A[0] + 0.15, A[1] - 0.15, M[0] - 0.12, M[1] + 0.12, "8C96A6", 1.5, false); // cables
  s.addShape(SH.ellipse, { x: A[0] - 0.25, y: A[1] - 0.25, w: 0.5, h: 0.5, fill: { color: "6B7280" }, line: { color: "6B7280" }, objectName: "asteroid" });
  s.addText(rich("asteroid (E3), 3.97×10^{20} kg", { fontSize: 13, bold: true, color: C.text1 }), { x: A[0] + 0.35, y: A[1] - 0.05, w: 2.6, h: 0.6, margin: 0, isTextBox: true });
  arrow(s, E[0], E[1], A[0] - 0.2, A[1] + 0.2, "8C96A6", 1.25, false, "dash");   // separation
  s.addText("637,100 km", { x: 2.95, y: 4.25, w: 1.3, h: 0.3, fontSize: 12, color: MUTED, margin: 0, isTextBox: true, rotate: -45 });
  arrow(s, E[0] + 0.22, E[1] - 0.22, E[0] + 0.85, E[1] - 0.85, HEX.accent2, 4);   // pull on Earth
  s.addText("pull", { x: E[0] + 0.85, y: E[1] - 0.6, w: 0.7, h: 0.3, fontSize: 13, bold: true, color: C.accent2, margin: 0, isTextBox: true });
  arrow(s, E[0], E[1] - 0.3, E[0], E[1] - 1.2, HEX.dk1, 1.75);                   // orbital motion
  s.addText("orbit", { x: E[0] - 0.85, y: E[1] - 1.05, w: 0.75, h: 0.3, fontSize: 12, color: MUTED, margin: 0, align: "right", isTextBox: true });
  s.addShape(SH.ellipse, { x: E[0] - 0.3, y: E[1] - 0.3, w: 0.6, h: 0.6, fill: { color: HEX.accent2 }, line: { color: HEX.accent2 }, objectName: "Earth" });
  s.addText("Earth", { x: E[0] - 0.6, y: E[1] + 0.35, w: 1.2, h: 0.3, fontSize: 13, bold: true, color: C.text1, align: "center", margin: 0, isTextBox: true });
  s.addText("Not to scale", { x: 0.8, y: 6.2, w: 2, h: 0.3, fontSize: 11, color: MUTED, margin: 0, isTextBox: true });
  const stats = [
    [sci(3.97e20), "kg asteroid, between Vesta and Ceres in mass"],
    ["637,100 km", "from Earth, 45° between ahead and away from the Sun"],
    [`${sci(dv.pull_n)} N`, "pull on Earth: the only new force on the planet"],
    [`${sci(dv.p_45deg_w, 1)} W`, "of focused light hold the asteroid on its spot"],
  ];
  stats.forEach(([big, small], i) => {
    const y = 1.5 + i * 1.28;
    s.addText(rich(big, { fontSize: 26, bold: true, color: C.text1, fontFace: "Cambria" }), { x: 8.45, y, w: 4.3, h: 0.55, margin: 0, isTextBox: true });
    s.addText(small, { x: 8.45, y: y + 0.55, w: 4.3, h: 0.6, fontSize: 14, color: C.text1, margin: 0, valign: "top", isTextBox: true });
  });
  source(s, `Source: config.yaml (tows); results/summary.json. Mars is towed first, to 3.64 AU, by a second tow of 1.56×10^{20} kg at 400,000 km.`);
  s.addNotes("An asteroid four times ten to the twenty kilograms sits 637,100 km from Earth. Its gravity pulls Earth forward and outward; Earth's orbit widens a little every lap. Earth pulls back on the asteroid, so a mirror tied to it is pushed by focused light from stations on the Sun's side. Light can only push, so the asteroid sits at 45 degrees, where the beam can hold it without ever passing near Earth.");
}

// ================================================================== 5 The physics
{
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Main talk" });
  title(s, "The physics in three equations");
  await mapButton(s);
  const cards = [
    ["FaEarthAmericas", "Gravity pulls Earth", "F = G M_{E} m_{a} / d^{2}",
      `M_{E} = 6.05×10^{24} kg, m_{a} = 3.97×10^{20} kg, d = 637,100 km`, `F = ${sci(dv.pull_n)} N`, `Earth's acceleration ${sci(dv.accel_m_s2)} m/s^{2}`, HEX.accent2],
    ["FaSun", "Light holds the asteroid", "F = (P/c)(n_{in} − n_{out})",
      "Light turned through 90° pushes with √2·P/c (n = the light's direction)", `P = F c / √2 = ${sci(dv.p_45deg_w, 1)} W`,
      `A head-on bounce would need ${sci(dv.p_min_w, 1)} W but cannot keep the beam clear of Earth`, HEX.accent1],
    ["FaRoute", "The orbit grows (Gauss)", "da/dt = 2a^{2} (v·f) / μ",
      "A constant along-orbit pull, from 1 AU to 2.7 AU", `${fmt(Math.round(dv.gauss_years))} years by hand`,
      `${eYear} simulated: the tow eases off for Mars and trims Earth's orbit on arrival`, HEX.accent5],
  ];
  for (let i = 0; i < 3; i++) {
    const [ic, head, eq, given, result, note, col] = cards[i];
    const x = 0.6 + i * 4.1;
    card(s, x, 1.5, 3.85, 3.95, HEX.lt2, `equation card ${i + 1}`);
    await badge(s, ic, x + 0.25, 1.72, 0.55, col);
    s.addText(head, { x: x + 0.95, y: 1.72, w: 2.75, h: 0.55, fontSize: 17, bold: true, color: C.text1, valign: "middle", margin: 0, isTextBox: true });
    s.addText(rich(eq, { fontSize: 21, fontFace: "Cambria", italic: true, color: C.text1 }), { x: x + 0.25, y: 2.45, w: 3.4, h: 0.6, margin: 0, valign: "middle", isTextBox: true });
    s.addText(rich(given, { fontSize: 13, color: MUTED }), { x: x + 0.25, y: 3.1, w: 3.4, h: 0.75, margin: 0, valign: "top", isTextBox: true });
    s.addText(rich(result, { fontSize: 20, bold: true, color: C.text1, fontFace: "Cambria" }), { x: x + 0.25, y: 3.9, w: 3.4, h: 0.5, margin: 0, valign: "middle", isTextBox: true });
    s.addText(rich(note, { fontSize: 13, color: C.text1 }), { x: x + 0.25, y: 4.45, w: 3.4, h: 0.85, margin: 0, valign: "top", isTextBox: true });
  }
  const strips = [
    ["Energy check.", `Earth's orbit needs ${sci(dv.energy_j)} J. The beams did ${sci(lg.beam_work_j, 4)} J of work and the bodies gained ${sci(lg.bodies_energy_gain_j, 4)} J (Mars included): a 0.007% match.`],
    ["Why 10^{26} W?", `Light carries only P/c of momentum. The work it does is the energy it loses to Doppler shift off the moving mirror: about v/c ≈ 10^{-4} of the light.`],
  ];
  strips.forEach(([h, t], i) => {
    const x = 0.6 + i * 6.15;
    card(s, x, 5.65, 5.95, 1.0, "FDF3DC", `strip ${i + 1}`);
    s.addText([...rich(h + " ", { fontSize: 13, bold: true, color: C.text1 }), ...rich(t, { fontSize: 13, color: C.text1 })],
      { x: x + 0.2, y: 5.7, w: 5.6, h: 0.9, margin: 0, valign: "middle", isTextBox: true });
  });
  s.addNotes(`Three pieces of ordinary physics carry the design. Newton's gravity gives the pull, about 4 times ten to the 17 newtons. Radiation pressure tells us how much light holds the asteroid: about 8.4 times ten to the 25 watts. Gauss's equation turns the pull into orbit growth: about 8,000 years by hand, ${eYear} in the full simulation. The energy books balance to 0.007 percent.`);
}

// ================================================================== 6 Enablers
{
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Main talk" });
  title(s, "Three enablers, each with a hard limit");
  await mapButton(s);
  const used = {
    e1: sm.total_beam_max_w / en.e1_beam_limit_w,
    e2: dv.mirror_k_at_cap / en.e2_max_temperature_k,
    e3: sm.climate.mirror_area_km2[1] / en.e3_mirror_area_limit_km2,
  };
  const cards = [
    ["E1", "Focused light", HEX.accent1, S.e1, "Power source of a stated wattage (guide §7)", "≤ 10^{26} W in total",
      used.e1, `peak ${sci(sm.total_beam_max_w)} W`, "Light pressure has flown: IKAROS, LightSail 2. Laser sails (Starshot) and laser asteroid defence (DE-STAR) are planned."],
    ["E2", "Super-mirror material", HEX.accent6, S.e2, "Ideal nanotube or graphene, 50–130 GPa (guide §7)", "100 GPa · absorbs 10^{-7} · ≤ 1,500 K",
      used.e2, `mirror ${fmt(dv.mirror_k_at_cap)} K at full power`, "Strongest nanotube measured: 63 GPa (Yu 2000); graphene 130 GPa (Lee 2008). LIGO's mirror coatings absorb under 10^{-6}."],
    ["E3", "Planet-scale manufacturing", HEX.accent5, S.e3, "Asteroid of stated mass; built at the start (guide §7)", "asteroids ≤ 4×10^{20} kg each · optics ≤ 10^{9} km^{2}",
      used.e3, `optics ${sci(sm.climate.mirror_area_km2[1], 1)} km^{2}`, "Tow asteroids are Vesta-class bodies. The sunlight optics follow Angel's L1 sunshade (PNAS 2006), used the other way round."],
  ];
  for (let i = 0; i < 3; i++) {
    const [tag, name, col, link, kind, bound, share, usedTxt, basis] = cards[i];
    const x = 0.6 + i * 4.1;
    card(s, x, 1.5, 3.85, 4.75, HEX.lt2, `${tag} card`, link);
    s.addText(tag, { shape: SH.ellipse, x: x + 0.25, y: 1.72, w: 0.7, h: 0.7, fill: { color: col }, line: { color: col },
      fontSize: 18, bold: true, color: C.background1, align: "center", valign: "middle", margin: 0, hyperlink: { slide: link, tooltip: "Open the details" } });
    s.addText(name, { x: x + 1.1, y: 1.72, w: 2.6, h: 0.7, fontSize: 17, bold: true, color: C.text1, valign: "middle", margin: 0,
      isTextBox: true });
    s.addText(paras([["Allowed as", { fontSize: 12, bold: true, color: MUTED }], [kind, { fontSize: 13, color: C.text1 }]]),
      { x: x + 0.25, y: 2.6, w: 3.4, h: 0.8, margin: 0, valign: "top", isTextBox: true });
    s.addText(paras([["Bound", { fontSize: 12, bold: true, color: MUTED }], [bound, { fontSize: 14, bold: true, color: C.text1 }]]),
      { x: x + 0.25, y: 3.4, w: 3.4, h: 0.75, margin: 0, valign: "top", isTextBox: true });
    // meter: share of the bound the run used
    s.addShape(SH.roundRect, { x: x + 0.25, y: 4.25, w: 3.35, h: 0.2, rectRadius: 0.1, fill: { color: "D9DEE5" }, line: { color: "D9DEE5" }, objectName: `${tag} meter` });
    s.addShape(SH.roundRect, { x: x + 0.25, y: 4.25, w: 3.35 * share, h: 0.2, rectRadius: 0.1, fill: { color: col }, line: { color: col }, objectName: `${tag} meter fill` });
    s.addText(rich(`Used: ${usedTxt} (${Math.round(share * 100)}% of the bound)`, { fontSize: 12, color: C.text1 }),
      { x: x + 0.25, y: 4.5, w: 3.4, h: 0.35, margin: 0, isTextBox: true });
    s.addText(rich(basis, { fontSize: 12, color: C.text1 }), { x: x + 0.25, y: 4.9, w: 3.4, h: 0.9, margin: 0, valign: "top", isTextBox: true });
    s.addText("Details →", { x: x + 2.35, y: 5.83, w: 1.3, h: 0.32, fontSize: 13, bold: true, color: C.accent2, align: "right", margin: 0,
      hyperlink: { slide: link, tooltip: "Open the details" } });
  }
  s.addText(rich(`Declared at the mid-point and frozen since. None creates energy or momentum: E1's recoil and bounced light are booked. Every flag that relies on an enabler names it (${sm.flags.covered_by_enablers} during the journey, ${lt.verdict.flags.covered_by_enablers} in the million years after).`, { fontSize: 13, color: C.text1 }),
    { x: 0.6, y: 6.35, w: 12.2, h: 0.6, margin: 0, valign: "middle", isTextBox: true });
  s.addNotes("The brief allows three hypothetical enablers, each bounded by a number. E1 is the big one: up to ten to the 26 watts of focused light, a quarter of the Sun's output. The physics of pushing with light has flown on IKAROS and LightSail 2; the scale is what we assume. E2 is a mirror material inside the guide's nanotube-graphene range. E3 places the asteroids and builds the optics. Each card opens a detail slide with sources.");
}

// ================================================================== 7 Journey
{
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Main talk" });
  title(s, `The journey: ${eYear} years, Mars first`);
  await mapButton(s);
  const J = D.journey;
  const years = J.year.map((_, i) => String(i * 100));
  s.addChart(pres.ChartType.line, [
    { name: "Mars", labels: years, values: J.mars_au },
    { name: "Earth", labels: years, values: J.earth_au },
  ], chartBase({ x: 0.6, y: 1.45, w: 8.1, h: 5.15, chartColors: [HEX.accent3, HEX.accent2], lineSize: 3, lineDataSymbol: "none",
    valAxisMinVal: 0.5, valAxisMaxVal: 4.0, valAxisMajorUnit: 0.5, valAxisLabelFormatCode: "0.0", catAxisLabelFrequency: 10, catAxisLabelRotate: 0,
    showTitle: true, title: "Orbit size (AU) against year of the journey", showLegend: true, legendPos: "t",
    catAxisTitle: "year", showCatAxisTitle: false }));
  const kpis = [
    [`Year ${mYear}`, `Mars parks at ${marsArr.a_au} AU, past Jupiter's 2:1 resonance`, HEX.accent3],
    [`Year ${eYear}`, `Earth arrives at ${arr.a_au} AU, eccentricity ${arr.eccentricity}`, HEX.accent2],
    [`${sm.mars_closest.au.toFixed(3)} AU`, "closest Earth–Mars pass (limit 0.05 AU)", HEX.accent4],
    [`${sci(sm.total_beam_max_w)} W`, `peak beam power: ${beamPct}% of E1's bound`, HEX.accent1],
  ];
  kpis.forEach(([big, small, col], i) => {
    const y = 1.5 + i * 1.3;
    card(s, 9.0, y, 3.75, 1.15, HEX.lt2, `journey stat ${i + 1}`);
    s.addShape(SH.ellipse, { x: 9.2, y: y + 0.22, w: 0.22, h: 0.22, fill: { color: col }, line: { color: col }, objectName: "key dot" });
    s.addText(rich(big, { fontSize: 20, bold: true, color: C.text1, fontFace: "Cambria" }), { x: 9.55, y: y + 0.08, w: 3.1, h: 0.45, margin: 0, isTextBox: true });
    s.addText(small, { x: 9.55, y: y + 0.52, w: 3.1, h: 0.58, fontSize: 12, color: C.text1, margin: 0, valign: "top", isTextBox: true });
  });
  source(s, "Source: results/run.json (one frame per 10 years; plotted every 100) and results/summary.json.");
  s.addNotes(`Mars sits across Earth's path, so a second tow moves it first. It sprints across Jupiter's 2:1 resonance at 3.28 AU, where a slow crossing gets caught, and parks at 3.64 AU in year ${mYear}. Earth's orbit widens faster as it goes, and it arrives at 2.7006 AU in year ${eYear}, with 1,242 years to spare.`);
}

// ================================================================== 8 Honest physics
{
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Main talk" });
  title(s, "Honest physics: every push is booked");
  await mapButton(s);
  const labels = ["Bodies' momentum vs applied impulse", "Impulse + recoil + light + departed", "The guide's limit"];
  s.addChart(pres.ChartType.bar, [
    { name: "Our run (worst)", labels, values: [lg.integrator_honest_max, lg.nothing_from_nothing_max, null] },
    { name: "Limit", labels, values: [null, null, 1e-9] },
  ], chartBase({ x: 0.6, y: 1.45, w: 7.0, h: 5.15, barDir: "col", barGrouping: "stacked", chartColors: [HEX.accent5, HEX.accent6],
    valAxisLogScaleBase: 10, valAxisMinVal: 1e-24, valAxisMaxVal: 1e-6, valAxisLabelFormatCode: "0E+0", showValue: true,
    dataLabelPosition: "inEnd", dataLabelFormatCode: "0.0E+0", dataLabelColor: "FFFFFF", showTitle: true,
    title: "Ledger error, share of the applied impulse (log scale: shorter is better)", barGapWidthPct: 50,
    catAxisLabelFontSize: 11 }));
  const st = [
    ["10 / 10", "official benchmarks pass, also with changed inputs (Kepler, Hohmann, Biot–Savart, energy balance…)"],
    ["0.007%", "beams' work against the bodies' energy gain over the whole journey"],
    ["8,730 vs " + eYear, "arrival year with half-day steps: the result has converged (0.3%)"],
  ];
  st.forEach(([big, small], i) => {
    const y = 1.5 + i * 1.6;
    card(s, 7.95, y, 4.8, 1.4, HEX.lt2, `honest stat ${i + 1}`);
    s.addText(big, { x: 8.2, y: y + 0.12, w: 4.4, h: 0.55, fontSize: 26, bold: true, fontFace: "Cambria", color: C.text1, margin: 0, isTextBox: true });
    s.addText(small, { x: 8.2, y: y + 0.68, w: 4.4, h: 0.65, fontSize: 13, color: C.text1, margin: 0, valign: "top", isTextBox: true });
  });
  source(s, "Source: results/summary.json (ledger); sim/benchmarks.py. Gravity acts in exact pairs; the beams' partners are the stations' recoil, the bounced light and the departing asteroids.");
  s.addNotes("The brief asks that every force be booked with its reaction. The only outside pushes are the beams on the two tow asteroids; their partners are the stations' recoil and the light that bounces away. Everything adds to zero to about 6 parts in ten to the 16, seven orders of magnitude inside the limit. All ten official benchmarks pass, and halving the time step moves arrival by only 0.3 percent.");
}

// ================================================================== 9 Earth stays safe
{
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Main talk" });
  title(s, "Earth stays safe the whole way");
  await mapButton(s);
  const T = [
    ["Mean temperature", `${cl.temperature_k[0].toFixed(1)}–${cl.temperature_k[1].toFixed(1)} K`, "263–308 K"],
    ["Liquid-water area", `≥ ${Math.round(cl.liquid_water_share[0] * 100)}%`, "≥ 30%"],
    ["Absorbed sunlight", `≤ ${cl.absorbed_w_m2[1].toFixed(1)} W/m^{2}`, "< 282 W/m^{2}"],
    ["Surface pressure", `${cl.surface_pressure_kpa[0].toFixed(1)} kPa`, "≥ 50 kPa"],
    ["Air kept (N_{2} Jeans λ)", `≥ ${Math.floor(cl.jeans_lambda_n2[0])}`, "> 30"],
    ["Magnetic shield", `≥ ${cl.magnetopause_re[0].toFixed(1)} R_{E}`, "≥ 3 R_{E}"],
    ["Day length change", "< 10^{-6} s", "≤ 1 s"],
    ["Moon / Hill radius", `≤ ${cl.moon_hill_share[1].toFixed(3)}`, "< 0.49"],
    ["Thrust / pull on Moon", `≤ ${cl.thrust_over_moon_pull[1].toFixed(4)}`, "< 0.01"],
  ];
  for (let i = 0; i < T.length; i++) {
    const x = 0.6 + (i % 3) * 2.5, y = 1.5 + Math.floor(i / 3) * 1.72;
    card(s, x, y, 2.35, 1.57, HEX.lt2, `threshold ${i + 1}`);
    s.addImage({ data: await icon("FaCircleCheck", HEX.accent4), x: x + 1.93, y: y + 0.15, w: 0.27, h: 0.27, objectName: "check" });
    s.addText(rich(T[i][0], { fontSize: 13, bold: true, color: C.text1 }), { x: x + 0.18, y: y + 0.12, w: 1.75, h: 0.4, margin: 0, isTextBox: true });
    s.addText(rich(T[i][1], { fontSize: 18, bold: true, color: C.text1, fontFace: "Cambria" }), { x: x + 0.18, y: y + 0.55, w: 2.05, h: 0.5, margin: 0, isTextBox: true });
    s.addText(rich(`limit ${T[i][2]}`, { fontSize: 12, color: MUTED }), { x: x + 0.18, y: y + 1.08, w: 2.05, h: 0.35, margin: 0, isTextBox: true });
  }
  card(s, 8.25, 1.5, 4.5, 4.97, "FDF3DC", "climate card");
  s.addText("Sunlight at 2.7 AU", { x: 8.5, y: 1.7, w: 4.0, h: 0.45, fontSize: 18, bold: true, color: C.text1, margin: 0, isTextBox: true });
  const steps = [
    ["13.7%", "of today's sunlight reaches Earth at 2.7 AU"],
    ["150 K", "frozen, no liquid water, without help"],
    [`${cl.temperature_k[0].toFixed(1)}–${cl.temperature_k[1].toFixed(1)} K`, `with E3's sunlight optics, up to ${sci(cl.mirror_area_km2[1], 1)} km^{2}, counted face on`],
    [`${Math.round(l1.sunlight_vs_today_at_e3 * 100)}%, ${Math.round(l1.temperature_k)} K`, "placed for real: a refracting ring near L1, held to E3's bound"],
  ];
  steps.forEach(([big, small], i) => {
    const y = 2.25 + i * 1.03;
    s.addText(rich(big, { fontSize: 20, bold: true, color: C.text1, fontFace: "Cambria" }), { x: 8.5, y, w: 4.0, h: 0.42, margin: 0, isTextBox: true });
    s.addText(rich(small, { fontSize: 12, color: C.text1 }), { x: 8.5, y: y + 0.42, w: 4.0, h: 0.55, margin: 0, valign: "top", isTextBox: true });
  });
  source(s, "Source: results/summary.json (climate), results/mirrors.json; thresholds from the company's reference demo. Checked every 100 days.");
  s.addNotes("The ten thresholds come from the company's reference demo, checked every 100 simulated days. The hard one is sunlight: at 2.7 AU Earth gets 13.7 percent of today's light and freezes at 150 K. E3's sunlight optics make up the difference. Counted face on, Earth stays at 288 K. Placed realistically as a refracting ring near L1, they give 97 percent of today's sunlight and 286 K, still inside every threshold.");
}

// ================================================================== 10 What if
{
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Main talk" });
  title(s, "What if…? The tests that shaped the design");
  await mapButton(s);
  const sp = D.small.parked;
  const W = [
    ["FaMeteor", "No Mars tow?", "Earth passes Mars at about 33,000 km.", "Tow Mars out first, to 3.64 AU.", S.stress, HEX.accent3],
    ["FaArrowsRotate", "Cross Jupiter's 2:1 slowly?", "Mars was caught in 6 of 8 trials.", "Sprint at 4× the pull: caught 0 of 8.", S.stress, HEX.accent3],
    ["FaPowerOff", "Beams go dark?", "The first design lost its asteroid after 3 hours.", `Shared power, many stations: safe ${Math.round(D.outage_hours["shared E1 budget, all beams off"])} h with every station off.`, S.stress, HEX.accent1],
    ["FaRightLeft", "Swap Earth and Mars?", "The orbits must cross: 48 of 48 runs passed inside 0.05 AU.", "Rejected; kept as a studied Plan S.", S.stress, HEX.accent6],
    ["FaSatellite", "Rocks at 2.7 AU?", `A 20 m rock about ${Math.round(1 / sp["20m"].years_per_impact.central)} times a year; 1 km once per ${Math.round(sp["1000m"].years_per_impact.central)} years.`, "Infrared survey, then E1 pushes each away with 2% of its spare power.", S.stress, HEX.accent5],
    ["FaHourglassHalf", "A million years later?", `Nothing is thrown out; Earth stays at ${lt.verdict.compared_with_real_solar_system.earth.moved.a[0].toFixed(3)}–${lt.verdict.compared_with_real_solar_system.earth.moved.a[1].toFixed(3)} AU.`, `Tilt swings ${lt.verdict.seasons.tilt_deg[0].toFixed(1)}°–${lt.verdict.seasons.tilt_deg[1].toFixed(1)}°: E3 re-aims 1.4% of the sunlight.`, S.longterm, HEX.accent2],
  ];
  for (let i = 0; i < W.length; i++) {
    const [ic, q, found, fix, link, col] = W[i];
    const x = 0.6 + (i % 3) * 4.1, y = 1.5 + Math.floor(i / 3) * 2.6;
    card(s, x, y, 3.85, 2.42, HEX.lt2, `what-if ${i + 1}`, link);
    await badge(s, ic, x + 0.22, y + 0.2, 0.55, col, link);
    s.addText(q, { x: x + 0.9, y: y + 0.2, w: 2.8, h: 0.55, fontSize: 16, bold: true, color: C.text1, valign: "middle", margin: 0,
      isTextBox: true });
    s.addText(paras([[found, { fontSize: 13, color: C.text1 }], [fix, { fontSize: 13, bold: true, color: C.text1 }]]),
      { x: x + 0.22, y: y + 0.88, w: 3.45, h: 1.15, margin: 0, valign: "top", isTextBox: true, paraSpaceAfter: 5 });
    s.addText("Details →", { x: x + 2.4, y: y + 2.02, w: 1.3, h: 0.3, fontSize: 12, bold: true, color: C.accent2, align: "right", margin: 0,
      hyperlink: { slide: link, tooltip: "Open the details" } });
  }
  source(s, "Source: results/crossing.json, outage.json, small_asteroids.json, longterm.json; sim/scenarios/swap.py (Plan S).");
  s.addNotes("Most of what makes the journey safe came from tests that failed. Without the Mars tow, Earth nearly hits Mars. A slow crossing of Jupiter's 2:1 resonance traps Mars. Our first beam design lost its asteroid after a three-hour blackout. Swapping Earth and Mars needs their orbits to cross, which never stayed safe. Each card opens the evidence.");
}

// ================================================================== 11 Verdict
{
  const s = pres.addSlide({ masterName: "DARK", sectionTitle: "Main talk" });
  title(s, "Verdict: the physics closes");
  await mapButton(s, true);
  const checks = [
    `Target in year ${eYear} of 10,000 (${arr.a_au} AU)`,
    "Ten Earth-safety thresholds held at every check",
    "Every structure at a safety factor of 1.57 or more",
    "10 of 10 official benchmarks pass",
    `Ledger closes to ${sci(lg.nothing_from_nothing_max, 1)} (limit 10^{-9})`,
    `0 unresolved flags; ${sm.flags.covered_by_enablers} covered by E1–E3`,
  ];
  for (let i = 0; i < checks.length; i++) {
    const y = 1.55 + i * 0.78;
    s.addImage({ data: await icon("FaCircleCheck", "3FC995"), x: 0.6, y: y + 0.05, w: 0.38, h: 0.38, objectName: "check" });
    s.addText(rich(checks[i], { fontSize: 17, color: C.background1 }), { x: 1.15, y, w: 5.7, h: 0.5, margin: 0, valign: "middle", isTextBox: true });
  }
  s.addShape(SH.roundRect, { x: 7.2, y: 1.5, w: 5.55, h: 4.75, rectRadius: 0.12, fill: { color: HEX.dk2 }, line: { color: HEX.dk2 }, objectName: "limits card" });
  s.addText("What we assume, and what we don't claim", { x: 7.45, y: 1.68, w: 5.1, h: 0.45, fontSize: 17, bold: true, color: C.accent1, margin: 0, isTextBox: true });
  const lim = [
    "E1 is 26% of the Sun's output: our largest assumption, bounded and booked",
    "Climate is a global, yearly model: no weather, oceans or seasons (13 months long at 2.7 AU)",
    `The run counts the optics face on; placed at L1 they give ${Math.round(l1.sunlight_vs_today_at_e3 * 100)}% of today's sunlight (${Math.round(l1.temperature_k)} K)`,
    `The tow mirror's scattered light must stay below ${sciU(D.optics.tow_mirror.scatter_limit_full_moon, 1)}: no enabler bounds it`,
    "Our runs reach a million years; beyond a few million the inner solar system is chaotic",
  ];
  s.addText(lim.flatMap((t, i) => {
    const r = rich(t, { fontSize: 14, color: C.background1, bullet: true });
    if (i < lim.length - 1) r[r.length - 1].options.breakLine = true;
    return r;
  }), { x: 7.45, y: 2.25, w: 5.1, h: 3.85, margin: 0, valign: "top", isTextBox: true, paraSpaceAfter: 9 });
  s.addText([
    { text: "Code and runs: github.com/Ashish000011/black-ant", options: { hyperlink: { url: "https://github.com/Ashish000011/black-ant" }, color: "CADCFC", breakLine: true } },
    { text: "3D test bench: ashish000011.github.io/black-ant", options: { hyperlink: { url: "https://ashish000011.github.io/black-ant/" }, color: "CADCFC", breakLine: true } },
    { text: "Physics paper: docs/physics/black-ant-physics-paper.pdf", options: { color: SOFT } },
  ], { x: 0.6, y: 6.3, w: 9, h: 0.85, fontSize: 12, margin: 0, isTextBox: true });
  s.addNotes("All six winning conditions hold in our simulation. We're explicit about what we assume: E1's power, a global yearly climate model, and the realistic optics placement, which still keeps Earth at 286 K. One risk no enabler covers is the light the tow mirror scatters onto Earth's night side. Thank you; the map is one click away for questions.");
}

// ================================================================== backup slides (hidden)
pres.addSection({ title: "Backup" });

// ---- E1
{
  const s = pres.addSlide({ masterName: "BACKUP", sectionTitle: "Backup" });
  s.hidden = true;
  title(s, "E1 · Focused light, up to 10^{26} W");
  await backButton(s, S.enablers, "the enablers");
  await mapButton(s);
  const J = D.journey;
  const years = J.year.map((_, i) => String(i * 100));
  s.addChart(pres.ChartType.line, [
    { name: "Both beams together", labels: years, values: J.beam_w.map((w) => +(w / 1e25).toFixed(3)) },
    { name: "E1's bound", labels: years, values: years.map(() => en.e1_beam_limit_w / 1e25) },
  ], chartBase({ x: 0.6, y: 1.45, w: 6.6, h: 5.1, chartColors: [HEX.accent1, HEX.accent6], lineSize: 2.25, lineDataSymbol: "none",
    valAxisMinVal: 0, valAxisMaxVal: 12, valAxisMajorUnit: 2, catAxisLabelFrequency: 10, showTitle: true,
    title: "Beam power (×10²⁵ W) against year of the journey", showLegend: true, legendPos: "t" }));
  card(s, 7.5, 1.45, 5.25, 5.1, HEX.lt1, "E1 text card");
  s.addText(paras([
    ["What it does", { fontSize: 14, bold: true, color: C.text1 }],
    ["Lights both tow mirrors from the Sun's side; nudges dangerous asteroids (a 20 m rock: 2% of its spare power).", { fontSize: 13, color: C.text1 }],
    ["How it's built", { fontSize: 14, bold: true, color: C.text1 }],
    ["Many independent stations: no single fault takes out more than a quarter of the power, and a fault is answered within 12 hours.", { fontSize: 13, color: C.text1 }],
    ["Its reaction partners", { fontSize: 14, bold: true, color: C.text1 }],
    ["Each station's recoil and the bounced light are booked in the ledger. No energy bonus is claimed.", { fontSize: 13, color: C.text1 }],
    ["Precedents", { fontSize: 14, bold: true, color: C.text1 }],
    [`10^{26} W is ${Math.round(dv.e1_over_sun * 100)}% of the Sun's 3.83×10^{26} W (IAU 2015). IKAROS measured 1.12 mN of sunlight push (JAXA 2010); LightSail 2 flew on sunlight (2019). Starshot plans 100 GW lasers; DE-STAR proposes pushing asteroids with sunlight-powered lasers (Lubin et al. 2014). E1 is 10^{15} times Starshot: proven physics, assumed scale.`, { fontSize: 13, color: C.text1 }],
  ]), { x: 7.75, y: 1.6, w: 4.8, h: 4.85, margin: 0, valign: "top", isTextBox: true, paraSpaceAfter: 3 });
  s.addNotes("E1 is our largest assumption and we say so. The chart shows the run never exceeded the bound: the dips are the Earth tow easing off while Mars sprints, and the ripple near the end is the arrival trim. The physics of light pushing things has flown; the scale is what we assume.");
}

// ---- E2
{
  const s = pres.addSlide({ masterName: "BACKUP", sectionTitle: "Backup" });
  s.hidden = true;
  title(s, "E2 · Super-mirror material");
  await backButton(s, S.enablers, "the enablers");
  await mapButton(s);
  const m = D.octo.materials;
  const names = ["Steel S355", "CFRP", "Nanotube, measured", "E2", "Graphene, measured"];
  const vals = [m[0].strength_gpa, m[1].strength_gpa, m[2].strength_gpa, en.e2_strength_pa / 1e9, m[3].strength_gpa];
  s.addChart(pres.ChartType.bar, [
    { name: "Real materials", labels: names, values: vals.map((v, i) => (i === 3 ? null : +v.toFixed(3))) },
    { name: "E2 (declared)", labels: names, values: vals.map((v, i) => (i === 3 ? v : null)) },
  ], chartBase({ x: 0.6, y: 1.45, w: 6.6, h: 5.1, barDir: "col", barGrouping: "stacked", chartColors: [HEX.accent6, HEX.accent1],
    valAxisLogScaleBase: 10, valAxisMinVal: 0.1, valAxisMaxVal: 1000, valAxisLabelFormatCode: "#,##0.#", showValue: true,
    dataLabelPosition: "inEnd", dataLabelFormatCode: "#,##0.###", dataLabelColor: "FFFFFF", showTitle: true,
    title: "Tensile strength (GPa, log scale)", barGapWidthPct: 45, showLegend: true, legendPos: "b" }));
  card(s, 7.5, 1.45, 5.25, 5.1, HEX.lt1, "E2 text card");
  s.addText(paras([
    ["Bound", { fontSize: 14, bold: true, color: C.text1 }],
    ["100 GPa strength · absorbs 10^{-7} of the light · 2,000 kg/m^{3} · works up to 1,500 K.", { fontSize: 13, color: C.text1 }],
    ["What it does, and how close it runs", { fontSize: 14, bold: true, color: C.text1 }],
    [`Tow mirrors and cables, sized for the most a beam can push (2P/c at the power cap). Cable safety factor ${dv.cable_sf_at_cap.toFixed(2)} (needs 1.5); mirror ${fmt(dv.mirror_k_at_cap)} K (limit 1,500 K).`, { fontSize: 13, color: C.text1 }],
    ["T = (αP / 2εσπR^{2})^{1/4}: the absorbed share is radiated from both faces.", { fontSize: 13, color: C.text1, italic: true }],
    ["Precedents", { fontSize: 14, bold: true, color: C.text1 }],
    ["Strongest single nanotube measured: 63 GPa (Yu et al., Science 2000). Monolayer graphene: 130 GPa (Lee et al., Science 2008). The guide allows 50–130 GPa. LIGO's mirror coatings absorb under 10^{-6} (Pinard et al. 2017); E2 asks for ten times better.", { fontSize: 13, color: C.text1 }],
  ]), { x: 7.75, y: 1.6, w: 4.8, h: 4.85, margin: 0, valign: "top", isTextBox: true, paraSpaceAfter: 3 });
  s.addNotes("E2 sits between the strongest nanotube ever measured and monolayer graphene, inside the range the guide allows. At full power the cables keep a safety factor of 1.57 and the mirror runs at 1,466 K, just under its 1,500 K limit.");
}

// ---- E3
{
  const s = pres.addSlide({ masterName: "BACKUP", sectionTitle: "Backup" });
  s.hidden = true;
  title(s, "E3 · Planet-scale manufacturing");
  await backButton(s, S.enablers, "the enablers");
  await mapButton(s);
  const M = D.masses_1e20;
  const order = ["Hygiea", "Mars tow", "Pallas", "Vesta", "Earth tow", "Ceres"];
  s.addChart(pres.ChartType.bar, [
    { name: "Real asteroids", labels: order, values: order.map((k) => (k.includes("tow") ? null : +M[k].toFixed(2))) },
    { name: "Our tow asteroids (E3)", labels: order, values: order.map((k) => (k.includes("tow") ? +M[k].toFixed(2) : null)) },
  ], chartBase({ x: 0.6, y: 1.45, w: 6.6, h: 5.1, barDir: "col", barGrouping: "stacked", chartColors: [HEX.accent6, HEX.accent5],
    valAxisMinVal: 0, valAxisMaxVal: 10, valAxisMajorUnit: 2, showValue: true, dataLabelPosition: "inEnd",
    dataLabelFormatCode: "0.00", dataLabelColor: "FFFFFF", showTitle: true,
    title: `Mass (×10²⁰ kg); E3's bound is ${M["E3 bound"]}×10²⁰ kg each`, barGapWidthPct: 45, showLegend: true, legendPos: "b" }));
  card(s, 7.5, 1.45, 5.25, 5.1, HEX.lt1, "E3 text card");
  s.addText(paras([
    ["What it places and builds", { fontSize: 14, bold: true, color: C.text1 }],
    [`Two tow asteroids (${sci(5.53e20)} kg in all), the tow mirrors, cables and anchors, and the sunlight optics: up to 10^{9} km^{2}; the run used ${sci(sm.climate.mirror_area_km2[1], 1)} km^{2} counted face on.`, { fontSize: 13, color: C.text1 }],
    ["Placed for real", { fontSize: 14, bold: true, color: C.text1 }],
    [`A ring of refracting film near the Sun–Earth L1 point bends extra sunlight onto Earth, so noon and night stay natural. Held to E3's bound it gives ${(l1.sunlight_vs_today_at_e3 * 100).toFixed(1)}% of today's sunlight and ${l1.temperature_k.toFixed(0)} K at 95% transmission. At 100 g/m^{2} it weighs 10^{14} kg.`, { fontSize: 13, color: C.text1 }],
    ["Precedents", { fontSize: 14, bold: true, color: C.text1 }],
    ["Angel's L1 sunshade (PNAS 2006), used the other way round. Vesta's mass from Dawn (Russell et al., Science 2012). Fallback if E3 means mirrors only: a ring held 120° from the Sun by sunlight.", { fontSize: 13, color: C.text1 }],
  ]), { x: 7.75, y: 1.6, w: 4.8, h: 4.85, margin: 0, valign: "top", isTextBox: true, paraSpaceAfter: 3 });
  s.addNotes("E3 puts two Vesta-class asteroids in place and builds the optics. The Earth tow asteroid is about 1.5 times Vesta's mass and well under Ceres. The realistic optics design is Angel's famous L1 sunshade turned around: instead of shading Earth, it bends extra sunlight onto it.");
}

// ---- Stress tests
{
  const s = pres.addSlide({ masterName: "BACKUP", sectionTitle: "Backup" });
  s.hidden = true;
  title(s, "What broke, and the fix");
  await backButton(s, S.whatif, "What if…?");
  await mapButton(s);
  const cr = D.crossing;
  const crLabels = ["Normal pull", "1.56× pull", "3.3× pull", "4× (chosen)", "4.9× pull"];
  const crVals = [cr[0].caught, cr[1].caught, cr[2].caught, cr[4].caught, cr[3].caught];
  s.addChart(pres.ChartType.bar, [{ name: "Caught by Jupiter (of 8 starts)", labels: crLabels, values: crVals }],
    chartBase({ x: 0.6, y: 1.45, w: 5.9, h: 3.7, barDir: "col", chartColors: [HEX.accent3], valAxisMinVal: 0, valAxisMaxVal: 8,
      valAxisMajorUnit: 2, showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0", showTitle: true,
      title: "Mars across Jupiter's 2:1 resonance: trials caught (of 8)", barGapWidthPct: 60 }));
  const O = D.outage_hours;
  const oLabels = ["First design, all off", "Every station off", "Half off", "A quarter off", "Mars tow, all off"];
  const oVals = [O["old: own cap 8.5e25 W, all beams off"], O["shared E1 budget, all beams off"], O["shared E1 budget, half the stations off"],
    O["shared E1 budget, a quarter off"], O["Mars tow, all beams off"]].map((v) => Math.round(v));
  s.addChart(pres.ChartType.bar, [{ name: "Longest safe outage (hours)", labels: oLabels, values: oVals }],
    chartBase({ x: 6.85, y: 1.45, w: 5.9, h: 3.7, barDir: "col", chartColors: [HEX.accent1], valAxisMinVal: 0, valAxisMaxVal: 125,
      valAxisMajorUnit: 25, showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0", showTitle: true,
      title: "Beam outage the tow survives (hours); E1 answers a fault within 12 h", barGapWidthPct: 60, catAxisLabelFontSize: 10 }));
  const notes = [
    ["No Mars tow", "Earth passes Mars at about 33,000 km. Mars goes first, to 3.64 AU, between the resonances with Jupiter and with the moved Earth."],
    ["Swap Earth and Mars (Plan S)", "Cheaper for Mars (5.66 vs 8.52 km/s), but the orbits must cross: in 48 of 48 runs the planets came inside 0.05 AU, twice inside the Moon's distance. Not adopted."],
  ];
  notes.forEach(([h, t], i) => {
    const x = 0.6 + i * 6.25;
    card(s, x, 5.35, 5.9, 1.25, HEX.lt1, `stress note ${i + 1}`);
    s.addText([...rich(h + ". ", { fontSize: 13, bold: true, color: C.text1 }), ...rich(t, { fontSize: 13, color: C.text1 })],
      { x: x + 0.2, y: 5.42, w: 5.5, h: 1.1, margin: 0, valign: "middle", isTextBox: true });
  });
  s.addNotes("Two charts carry the stress tests. Crossing Jupiter's 2:1 resonance slowly, Mars got trapped six times out of eight; at four times the pull, never. And after giving the beams a shared power budget and many independent stations, the Earth tow survives 15 hours with every station dark, against 3 hours for the first design.");
}

// ---- A million years
{
  const s = pres.addSlide({ masterName: "BACKUP", sectionTitle: "Backup" });
  s.hidden = true;
  title(s, "A million years after arrival");
  await backButton(s, S.whatif, "What if…?");
  await mapButton(s);
  const kyr = lt.kyr.map((k) => String(Math.round(k)));
  s.addChart(pres.ChartType.line, [
    { name: "Moved Earth (2.7 AU)", labels: kyr, values: lt.tilt_moved },
    { name: "Real Earth (1 AU)", labels: kyr, values: lt.tilt_real },
  ], chartBase({ x: 0.6, y: 1.45, w: 7.4, h: 5.1, chartColors: [HEX.accent2, HEX.accent6], lineSize: 2, lineDataSymbol: "none",
    valAxisMinVal: 21, valAxisMaxVal: 27, valAxisMajorUnit: 1, catAxisLabelFrequency: 10, showTitle: true,
    title: "Earth's axial tilt (degrees) over 1,000 thousand years", showLegend: true, legendPos: "t" }));
  const cmp = lt.verdict.compared_with_real_solar_system;
  const st = [
    [`${cmp.earth.moved.a[0].toFixed(3)}–${cmp.earth.moved.a[1].toFixed(3)} AU`, "Earth's orbit size: it stays put"],
    [`e ≤ ${cmp.earth.moved.e[1].toFixed(3)}`, `Earth's eccentricity (the real Earth: ≤ ${cmp.earth.real.e[1].toFixed(3)})`],
    [`${lt.earth_mars_gap_min_au.toFixed(3)} AU`, "closest the Mars and Earth orbits come; nothing thrown out"],
    [`${lt.verdict.big_asteroid_nudges.passes} passes`, `of big asteroids within 0.01 AU, each nudged by ≤ ${lt.verdict.big_asteroid_nudges.longest_beam_hours.toFixed(1)} h of a 10^{25} W beam`],
  ];
  st.forEach(([big, small], i) => {
    const y = 1.5 + i * 1.27;
    card(s, 8.3, y, 4.45, 1.12, HEX.lt1, `long stat ${i + 1}`);
    s.addText(rich(big, { fontSize: 20, bold: true, color: C.text1, fontFace: "Cambria" }), { x: 8.5, y: y + 0.08, w: 4.1, h: 0.45, margin: 0, isTextBox: true });
    s.addText(rich(small, { fontSize: 12, color: C.text1 }), { x: 8.5, y: y + 0.52, w: 4.1, h: 0.55, margin: 0, valign: "top", isTextBox: true });
  });
  s.addNotes("With the tows gone, we ran the moved solar system for a million years beside the real one. Earth's orbit stays within 0.002 AU of 2.7. The tilt swings wider than today's, because at 2.7 AU Earth's spin precession nearly matches a slow Jupiter-Saturn mode; keeping today's seasons means re-aiming 1.4 percent of the sunlight with E3's optics.");
}

await pres.writeFile({ fileName: OUT });
await applyTheme(OUT, THEME);
console.log(`wrote ${path.relative(process.cwd(), OUT)}`);
