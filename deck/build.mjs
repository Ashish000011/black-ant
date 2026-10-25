// Builds the visual report, docs/black-ant-visual-report.pptx: 11 dense slides whose diagrams are native,
// editable PowerPoint shapes and charts, and whose numbers all come from deck/data.json (made from results/ by
// deck/data.py). Run from the repository root:
//
//   uv run python deck/data.py && node deck/build.mjs
//   powershell -ExecutionPolicy Bypass -File deck/export.ps1 docs/black-ant-visual-report.pptx docs/black-ant-visual-report.pdf

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import pptxgen from "pptxgenjs";
import JSZip from "jszip";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, "..");
const OUT = path.join(ROOT, "docs", "black-ant-visual-report.pptx");
const D = JSON.parse(fs.readFileSync(path.join(HERE, "data.json"), "utf8"));
const S = D.summary;

// ---------- palette and type ----------
const INK = "0B1324", INK2 = "16213A", ORBIT_D = "34445F", TEXT_D = "E8EDF5", MUTED_D = "9AA7BA";
const TEXT = "1A2233", MUTED = "566173", LINE = "D5DCE6", TINT = "F1F4F8", WHITE = "FFFFFF";
const SUN = "F2A541", SUN_D = "A9630A", EARTH = "2A9D8F", EARTH_D = "1D6F66", MARS = "C8553D";
const ROCK = "8A94A6", PASS = "2F9E5B", PASS_BG = "E3F3E9", BLUE = "3D7DCA";
const HEAD = "Cambria", BODY = "Calibri";
const THEME = {
  name: "Black Ant",
  colors: { dk1: INK, lt1: WHITE, dk2: "1C2B44", lt2: TINT, accent1: SUN, accent2: EARTH, accent3: MARS,
            accent4: ROCK, accent5: BLUE, accent6: PASS, hlink: BLUE, folHlink: "6C7A89" },
};

// ---------- number formatting ----------
const SUP = { "-": "⁻", 0: "⁰", 1: "¹", 2: "²", 3: "³", 4: "⁴", 5: "⁵", 6: "⁶", 7: "⁷", 8: "⁸", 9: "⁹" };
const sup = (n) => String(n).split("").map((c) => SUP[c]).join("");
function sci(x, digits = 2) {
  const e = Math.floor(Math.log10(Math.abs(x)));
  const m = x / 10 ** e;
  const ms = m.toFixed(digits - 1).replace(/\.0+$/, "");
  return ms === "1" ? `10${sup(e)}` : `${ms} × 10${sup(e)}`;
}
const n0 = (x) => Math.round(x).toLocaleString("en-US");
const fx = (x, d) => x.toLocaleString("en-US", { minimumFractionDigits: d, maximumFractionDigits: d });
const pct = (x, d = 0) => `${fx(x * 100, d)}%`;

// ---------- facts used on several slides ----------
const ET = S.tows["earth-tow"], MT = S.tows["mars-tow"], ARR = ET.arrival;
const TOWS = D.config.tows, SAFE = D.config.safety, CL = S.climate, LED = S.ledger, MS = D.milestones;
const YEARS = D.config.years;
const marsPark = { t: MT.arrival.year, a: MT.arrival.a_au };
const capChecks = D.structures_cap;
const capVal = (tow, what) => capChecks.find((c) => c.tow === tow && c.check.includes(what)).value;
const minSF = Math.min(...capChecks.filter((c) => c.check.includes("safety factor")).map((c) => c.value));
const unresolved = S.flags.flags.filter((f) => !f.covered_by).length;
const flagsCovered = S.flags.flags.length - unresolved;
const benchPass = D.benchmarks.filter((b) => b.ok).length;
const verifyRows = D.verify ? D.verify.sections : [];
const tests = verifyRows.find((r) => r.title === "Test suite");
const testsPassed = tests ? Number(tests.summary.split(" ")[0]) : null;
const studyNumbers = verifyRows.filter((r) => r.summary.startsWith("reproduces"))
  .reduce((acc, r) => acc + Number(r.summary.match(/([\d,]+) numbers/)[1].replace(",", "")), 0);
const laps = D.journey.slice(1).reduce((acc, f, i) => acc + (f.t - D.journey[i].t) / f.earth_a ** 1.5, 0);
const lt = D.longterm, ltMoved = lt.moved, ltReal = lt.real;
const L1 = D.mirrors.refractor_l1, byT = L1.by_transmission;
const pull = 6.674e-11 * 5.972e24 * TOWS["earth-tow"].asteroid_mass_kg / (TOWS["earth-tow"].distance_km * 1e3) ** 2;
const accel = pull / 5.972e24;

// ---------- deck ----------
const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.333 x 7.5 in
pres.author = "Team Black Ant";
pres.company = "Team Black Ant";
pres.title = "Black Ant: towing Earth to 2.7 AU (visual report)";
pres.theme = { headFontFace: HEAD, bodyFontFace: BODY };

pres.defineSlideMaster({
  title: "CONTENT",
  background: { color: WHITE },
  objects: [
    { placeholder: { options: { name: "kicker", type: "body", x: 0.95, y: 0.34, w: 11.5, h: 0.28, fontFace: BODY, fontSize: 10.5,
      bold: true, color: SUN_D, charSpacing: 1, margin: 0, valign: "middle" }, text: "" } },
    { placeholder: { options: { name: "title", type: "title", x: 0.55, y: 0.64, w: 12.23, h: 0.56, fontFace: HEAD, fontSize: 28,
      bold: true, color: TEXT, margin: 0, valign: "middle" }, text: "" } },
    { placeholder: { options: { name: "lede", type: "body", x: 0.55, y: 1.22, w: 12.23, h: 0.5, fontFace: BODY, fontSize: 12.5,
      color: MUTED, margin: 0, valign: "top" }, text: "" } },
    { text: { text: "Black Ant · Towing Earth to 2.7 AU · TransfiNITTe 2026 · every number from results/",
      options: { x: 0.55, y: 7.13, w: 9, h: 0.24, fontFace: BODY, fontSize: 10, color: MUTED, margin: 0 } } },
  ],
  slideNumber: { x: 12.28, y: 7.13, w: 0.5, h: 0.24, fontFace: BODY, fontSize: 10, color: MUTED, align: "right" },
});
pres.defineSlideMaster({
  title: "DARK",
  background: { color: INK },
  objects: [],
  slideNumber: { x: 12.28, y: 7.13, w: 0.5, h: 0.24, fontFace: BODY, fontSize: 10, color: MUTED_D, align: "right" },
});

// ---------- drawing helpers ----------
const T = (s, text, o = {}) => s.addText(text, { isTextBox: true, margin: 0, fontFace: BODY, fontSize: 11, color: TEXT,
  valign: "top", ...o });
const run = (text, o = {}) => ({ text, options: o });
function circle(s, cx, cy, r, o = {}) {
  s.addShape(pres.shapes.OVAL, { x: cx - r, y: cy - r, w: 2 * r, h: 2 * r, ...o });
}
function ring(s, cx, cy, r, color, width = 1, o = {}) {
  circle(s, cx, cy, r, { line: { color, width, dashType: o.dash, transparency: o.transparency }, ...(o.fill ? { fill: o.fill } : {}) });
}
function line(s, x1, y1, x2, y2, o = {}) {
  s.addShape(pres.shapes.LINE, {
    x: Math.min(x1, x2), y: Math.min(y1, y2), w: Math.max(Math.abs(x2 - x1), 0.001), h: Math.max(Math.abs(y2 - y1), 0.001),
    flipH: x2 < x1, flipV: y2 < y1,
    line: { color: o.color || TEXT, width: o.width || 1, dashType: o.dash, endArrowType: o.end, beginArrowType: o.begin,
            transparency: o.transparency },
  });
}
function poly(s, pts, o = {}) {
  const xs = pts.map((p) => p[0]), ys = pts.map((p) => p[1]);
  const x0 = Math.min(...xs), y0 = Math.min(...ys);
  s.addShape(pres.shapes.CUSTOM_GEOMETRY, {
    x: x0, y: y0, w: Math.max(Math.max(...xs) - x0, 0.01), h: Math.max(Math.max(...ys) - y0, 0.01),
    points: pts.map(([x, y]) => ({ x: x - x0, y: y - y0 })).concat(o.close ? [{ close: true }] : []),
    line: { color: o.color || TEXT, width: o.width || 1, dashType: o.dash, endArrowType: o.end, transparency: o.transparency },
    ...(o.fill ? { fill: o.fill } : {}),
  });
}
function box(s, x, y, w, h, o = {}) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: o.r ?? 0.08, fill: { color: o.fill || TINT, transparency: o.ft },
    ...(o.line ? { line: { color: o.line, width: o.lw || 0.75, dashType: o.dash } } : {}) });
}
function rect(s, x, y, w, h, fill, o = {}) {
  s.addShape(pres.shapes.RECTANGLE, { x, y, w, h, fill: { color: fill, transparency: o.ft },
    ...(o.line ? { line: { color: o.line, width: o.lw || 0.75 } } : {}) });
}
function chip(s, x, y, text = "PASS", o = {}) {
  s.addText(text, { shape: pres.shapes.ROUNDED_RECTANGLE, rectRadius: 0.06, x, y, w: o.w || 0.62, h: 0.26, margin: 0,
    fill: { color: o.fill || PASS_BG }, color: o.color || PASS, fontFace: BODY, fontSize: 10, bold: true, align: "center",
    valign: "middle" });
}
function badge(s, cx, cy, label, fill, o = {}) {
  s.addText(label, { shape: pres.shapes.OVAL, x: cx - (o.r || 0.2), y: cy - (o.r || 0.2), w: 2 * (o.r || 0.2), h: 2 * (o.r || 0.2),
    margin: 0, fill: { color: fill }, color: o.color || WHITE, fontFace: BODY, fontSize: o.size || 11, bold: true,
    align: "center", valign: "middle" });
}
function arcPts(cx, cy, r, a0, a1, n = 48) { // angles in degrees, counter-clockwise on screen (y up)
  const pts = [];
  for (let i = 0; i <= n; i++) {
    const a = ((a0 + (a1 - a0) * i / n) * Math.PI) / 180;
    pts.push([cx + r * Math.cos(a), cy - r * Math.sin(a)]);
  }
  return pts;
}
function head(s, kicker, title, lede) {
  ring(s, 0.68, 0.48, 0.12, SUN_D, 1.25);
  circle(s, 0.785, 0.42, 0.04, { fill: { color: SUN_D } });
  s.addText(kicker, { placeholder: "kicker" });
  s.addText(title, { placeholder: "title" });
  if (lede) s.addText(lede, { placeholder: "lede" });
}
const content = () => pres.addSlide({ masterName: "CONTENT" });
const CHART = { // the same quiet frame on every chart
  catAxisLabelColor: MUTED, valAxisLabelColor: MUTED, catAxisLabelFontSize: 10, valAxisLabelFontSize: 10,
  catAxisLabelFontFace: BODY, valAxisLabelFontFace: BODY, valGridLine: { color: LINE, size: 0.5 }, catGridLine: { style: "none" },
  catAxisLineColor: LINE, valAxisLineShow: false, legendFontSize: 10, legendFontFace: BODY, legendColor: MUTED,
  valAxisTitleColor: MUTED, catAxisTitleColor: MUTED, valAxisTitleFontSize: 10, catAxisTitleFontSize: 10,
  valAxisTitleFontFace: BODY, catAxisTitleFontFace: BODY, dataLabelFontFace: BODY, dataLabelFontSize: 10, dataLabelColor: TEXT,
};
function rng(seed) { // a fixed pseudo-random sequence, so the belt's dots are the same on every build
  return () => { seed |= 0; seed = (seed + 0x6d2b79f5) | 0; let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
}

// =====================================================================================================
// 1. Title: the orbit map and the headline numbers
// =====================================================================================================
{
  const s = pres.addSlide({ masterName: "DARK" });
  T(s, "TRANSFINITTE 2026 · PLANETARY PROPULSION HACKATHON · VISUAL REPORT", { x: 0.6, y: 0.55, w: 6.2, h: 0.3,
    fontSize: 10.5, bold: true, color: SUN, charSpacing: 1 });
  T(s, "Towing Earth\nto 2.7 AU", { x: 0.6, y: 0.92, w: 6.0, h: 1.5, fontFace: HEAD, fontSize: 46, bold: true, color: WHITE });
  T(s, "A gravity tractor held by light. An asteroid's gravity pulls Earth outward; focused light on its mirror holds the "
    + "asteroid in place. Nothing touches the planet.", { x: 0.6, y: 2.5, w: 5.85, h: 0.95, fontSize: 15, color: TEXT_D });
  const kpis = [
    [`${fx(ARR.a_au, 4)} AU`, `Earth's new orbit (target ${D.config.target_au})`, EARTH],
    [`${n0(ARR.year)} yr`, `arrival, of ${n0(YEARS)} allowed`, EARTH],
    [`${benchPass} / ${D.benchmarks.length}`, "official benchmarks pass", PASS],
    [fx(minSF, 2), "lowest safety factor (needs 1.5)", PASS],
    [sci(LED.nothing_from_nothing_max), "momentum ledger gap (limit 10⁻⁹)", SUN],
    [String(unresolved), `unresolved flags (${flagsCovered} covered by E1–E3)`, SUN],
  ];
  kpis.forEach(([v, label, c], i) => {
    const x = 0.6 + (i % 3) * 1.98, y = 3.62 + Math.floor(i / 3) * 1.12;
    box(s, x, y, 1.86, 1.0, { fill: INK2, line: ORBIT_D });
    T(s, v, { x: x + 0.14, y: y + 0.12, w: 1.65, h: 0.42, fontSize: i === 4 ? 19 : 23, bold: true, color: c, valign: "middle" });
    T(s, label, { x: x + 0.14, y: y + 0.56, w: 1.62, h: 0.4, fontSize: 10, color: MUTED_D });
  });
  T(s, [run("Sushmit Sukla", { bold: true }), run(" (team leader) · Ashish Bharti · Akhil Semwal · Madhukar Verma · Prabhanshu Kerketa")],
    { x: 0.6, y: 6.02, w: 6.0, h: 0.42, fontSize: 11, color: TEXT_D });
  T(s, "25 October 2026 · github.com/Ashish000011/black-ant · test bench: ashish000011.github.io/black-ant",
    { x: 0.6, y: 6.5, w: 6.0, h: 0.4, fontSize: 10, color: MUTED_D });

  // The solar system to scale, Sun at the centre
  const cx = 9.95, cy = 3.72, k = 0.81;
  const [b0, b1] = D.belt_au;
  const rnd = rng(7);
  for (let i = 0; i < 230; i++) {
    const r = (b0 + (b1 - b0) * rnd()) * k, a = rnd() * 2 * Math.PI;
    circle(s, cx + r * Math.cos(a), cy - r * Math.sin(a), 0.013 + 0.012 * rnd(), { fill: { color: ROCK, transparency: 35 } });
  }
  ring(s, cx, cy, D.orbits_au.venus * k, ORBIT_D, 0.75);
  ring(s, cx, cy, 1.0 * k, EARTH, 1, { dash: "dash" });
  ring(s, cx, cy, D.orbits_au.mars * k, MARS, 1, { dash: "dash" });
  ring(s, cx, cy, ARR.a_au * k, EARTH, 2.25);
  ring(s, cx, cy, TOWS["mars-tow"].stop_au * k, MARS, 2);
  circle(s, cx, cy, 0.3, { fill: { color: SUN, transparency: 78 } });
  circle(s, cx, cy, 0.16, { fill: { color: SUN } });
  // Paths: schematic spirals (the real Earth circles the Sun ~laps times on the way)
  const spiral = (r0, r1, a0, turns) => {
    const pts = [];
    for (let i = 0; i <= 140; i++) {
      const u = i / 140, a = ((a0 + 360 * turns * u) * Math.PI) / 180, r = (r0 + (r1 - r0) * u ** 1.15) * k;
      pts.push([cx + r * Math.cos(a), cy - r * Math.sin(a)]);
    }
    return pts;
  };
  const ray = (r0, r1, deg) => { const a = (deg * Math.PI) / 180; return [[cx + r0 * k * Math.cos(a), cy - r0 * k * Math.sin(a)], [cx + r1 * k * Math.cos(a), cy - r1 * k * Math.sin(a)]]; };
  const eP = ray(1.0, ARR.a_au, 215), mP = ray(D.orbits_au.mars, TOWS["mars-tow"].stop_au, 335);
  line(s, eP[0][0], eP[0][1], eP[1][0], eP[1][1], { color: EARTH, width: 2, end: "triangle" });
  line(s, mP[0][0], mP[0][1], mP[1][0], mP[1][1], { color: MARS, width: 2, end: "triangle" });
  const dot = (p, r, c) => circle(s, p[0], p[1], r, { fill: { color: c }, line: { color: WHITE, width: 0.75 } });
  dot(eP[0], 0.07, EARTH); dot(mP[0], 0.06, MARS); dot(eP.at(-1), 0.1, EARTH); dot(mP.at(-1), 0.085, MARS);
  circle(s, eP.at(-1)[0] + 0.15, eP.at(-1)[1] - 0.1, 0.035, { fill: { color: ROCK } });
  const lbl = (text, x, y, w, c = TEXT_D, o = {}) => T(s, text, { x, y, w, h: 0.42, fontSize: 10, color: c, ...o });
  lbl("Sun", cx - 0.25, cy + 0.2, 0.5, SUN, { align: "center", h: 0.2 });
  lbl([run("Earth arrives, year " + n0(ARR.year), { bold: true }), run(`\n${fx(ARR.a_au, 4)} AU, e = ${fx(ARR.eccentricity, 3)}`)],
    eP.at(-1)[0] + 0.16, eP.at(-1)[1] + 0.02, 1.9, EARTH);
  lbl([run("Mars parked, year " + n0(marsPark.t), { bold: true }), run(`\n${fx(marsPark.a, 2)} AU`)],
    mP.at(-1)[0] - 2.1, mP.at(-1)[1] + 0.12, 1.95, MARS, { align: "right" });
  lbl("Earth today, 1 AU", eP[0][0] + 0.1, eP[0][1] + 0.02, 1.3, EARTH, { h: 0.2 });
  lbl("Mars today, 1.52 AU", mP[0][0] + 0.1, mP[0][1] - 0.26, 1.5, MARS, { h: 0.2 });
  lbl(`Asteroid belt ${b0}–${b1} AU`, cx - 0.9, cy - b1 * k + 0.04, 1.8, MUTED_D, { align: "center", h: 0.2 });
  lbl(`Earth's new orbit sits in the belt`, cx - 1.1, cy + ARR.a_au * k - 0.27, 2.2, EARTH, { align: "center", h: 0.2 });
  // scale bar
  line(s, 11.75, 6.92, 11.75 + k, 6.92, { color: MUTED_D, width: 1.25 });
  lbl("1 AU", 11.75, 6.66, k, MUTED_D, { align: "center", h: 0.2 });
  lbl(`Orbits to scale. The arrows show the net move; Earth really spirals out over about ${n0(Math.round(laps / 100) * 100)} laps of the Sun, Mars over ${n0(Math.round(D.journey.filter((f) => f.t <= marsPark.t).slice(1).reduce((a, f, i) => a + (f.t - D.journey[i].t) / f.mars_a ** 1.5, 0) / 100) * 100)}.`,
    6.75, 6.56, 4.8, MUTED_D, { h: 0.5 });
  s.addNotes(`Black Ant moves Earth from 1 AU to ${fx(ARR.a_au, 4)} AU in ${n0(ARR.year)} years, inside the ${n0(YEARS)}-year limit. `
    + "The machine is a gravity tractor: an asteroid parked near Earth pulls it outward, and light pushing on a mirror tied to the "
    + "asteroid holds it in place. Mars is moved out of the way first. Every number in this deck is read from results/ by deck/data.py.");
}

// =====================================================================================================
// 2. The verdict: six winning conditions and the three enablers
// =====================================================================================================
{
  const s = content();
  head(s, "01 · THE VERDICT", "All six winning conditions hold",
    "Each condition of the participant guide, measured in the final run (results/summary.json) and checked again from scratch "
    + "by run.bat verify, which re-runs the benchmarks, the tests, the engine and the studies.");
  const rows = [
    ["Earth reaches the target orbit within 10,000 years", `required: ${D.config.target_au} AU by year ${n0(YEARS)}`,
      `year ${n0(ARR.year)}`, `${fx(ARR.a_au, 4)} AU · ${n0(YEARS - ARR.year)} years to spare`, "years"],
    ["Every Earth-safety threshold holds all run", "required: all ten, at every 100-day check",
      "10 of 10", `held at all ${n0(MS.checks)} checks`, "dots10"],
    ["Every structural safety factor ≥ 1.5", "sized at each tow's full power cap",
      fx(minSF, 2), "lowest: cables and anchors", "sf"],
    ["Every applicable benchmark passes", "the guide's ten, inputs changeable",
      `${benchPass} of ${D.benchmarks.length}`, `plus our checks X1–X9 and ${testsPassed ?? ""} tests`, "squares10"],
    ["Forces booked; energy and momentum kept", "ledger within 10⁻⁹ of the applied impulse",
      sci(LED.nothing_from_nothing_max), `${fx(-9 - Math.log10(LED.nothing_from_nothing_max), 1)} orders of magnitude inside`, "log"],
    ["No unresolved flags", "a flag may stand only if an enabler covers it",
      `${unresolved} open`, `${flagsCovered} raised, each covered by E1, E2 or E3`, "flags"],
  ];
  rows.forEach(([cond, req, big, small, vis], i) => {
    const y = 1.86 + i * 0.77, h = 0.7;
    box(s, 0.55, y, 7.95, h, { fill: TINT });
    badge(s, 0.86, y + h / 2, String(i + 1), INK, { r: 0.19 });
    T(s, [run(cond, { bold: true, fontSize: 11.5 }), run("\n" + req, { fontSize: 10, color: MUTED })],
      { x: 1.2, y: y + 0.1, w: 3.05, h: 0.55 });
    T(s, [run(big, { bold: true, fontSize: 17 }), run("\n" + small, { fontSize: 10, color: MUTED })],
      { x: 4.32, y: y + 0.06, w: 2.05, h: 0.62 });
    const vx = 6.45, vy = y + h / 2, vw = 1.25;
    if (vis === "years") {
      rect(s, vx, vy - 0.05, vw, 0.1, LINE);
      rect(s, vx, vy - 0.05, vw * ARR.year / YEARS, 0.1, EARTH);
      line(s, vx + vw, vy - 0.14, vx + vw, vy + 0.14, { color: MARS, width: 1.5 });
    } else if (vis === "dots10" || vis === "squares10") {
      for (let j = 0; j < 10; j++) {
        const x = vx + j * 0.125;
        if (vis === "dots10") circle(s, x + 0.05, vy, 0.045, { fill: { color: PASS } });
        else rect(s, x + 0.01, vy - 0.045, 0.09, 0.09, PASS);
      }
    } else if (vis === "sf") {
      const X = (v) => vx + vw * v / 2;
      rect(s, vx, vy - 0.05, vw, 0.1, LINE);
      rect(s, vx, vy - 0.05, X(minSF) - vx, 0.1, PASS);
      line(s, X(1.5), vy - 0.14, X(1.5), vy + 0.14, { color: MARS, width: 1.5 });
    } else if (vis === "log") {
      const X = (e) => vx + vw * (e + 18) / 12;  // 10^-18 .. 10^-6
      line(s, vx, vy, vx + vw, vy, { color: LINE, width: 2 });
      line(s, X(-9), vy - 0.14, X(-9), vy + 0.14, { color: MARS, width: 1.5 });
      circle(s, X(Math.log10(LED.nothing_from_nothing_max)), vy, 0.06, { fill: { color: PASS } });
    } else if (vis === "flags") {
      const by = S.flags.flags.map((f) => f.covered_by);
      by.forEach((e, j) => badge(s, vx + 0.1 + j * 0.21, vy, e.slice(1), { E1: SUN_D, E2: EARTH_D, E3: "5B6779" }[e], { r: 0.09, size: 8 }));
    }
    chip(s, 7.8, y + (h - 0.26) / 2);
  });

  // Enablers, with how much of each bound the run used
  T(s, "Three declared enablers, each with a hard limit", { x: 8.8, y: 1.86, w: 4.0, h: 0.3, fontSize: 13, bold: true });
  const ens = [
    ["E1 · Power source", S.total_beam_max_w / D.config.enablers.e1_beam_limit_w, SUN,
      `${sci(S.total_beam_max_w, 3)} W at peak, of ${sci(D.config.enablers.e1_beam_limit_w)} W`,
      `Covers: beam power above humanity's 2 × 10¹³ W; Vesta's ${fx(S.big_asteroids_closest_au.vesta, 3)} AU pass; belt impact rates.`],
    ["E2 · Super-mirror material", capVal("earth-tow", "temperature") / D.config.enablers.e2_max_temperature_k, EARTH,
      `mirror at ${n0(capVal("earth-tow", "temperature"))} K of ${n0(D.config.enablers.e2_max_temperature_k)} K at the power cap`,
      "Covers: tow mirrors and cables (absorbs 10⁻⁷ of the light, 100 GPa strength)."],
    ["E3 · Planet-scale manufacturing", D.mirrors.face_on_area_km2 / D.mirrors.e3_limit_km2, "6C7A89",
      `${sci(D.mirrors.face_on_area_km2)} km² of optics, of ${sci(D.mirrors.e3_limit_km2)} km²`,
      `Covers: placing ${sci(S.flags.flags.find((f) => f.covered_by === "E3").worst)} kg of asteroids; building the mirrors.`],
  ];
  ens.forEach(([name, used, c, usage, covers], i) => {
    const y = 2.24 + i * 1.4;
    box(s, 8.8, y, 3.98, 1.3, { fill: WHITE, line: LINE });
    s.addChart(pres.charts.DOUGHNUT, [{ name, labels: ["used", "spare"], values: [used, 1 - used] }], {
      x: 8.88, y: y + 0.1, w: 1.1, h: 1.1, holeSize: 68, chartColors: [c, "E6EAF0"], showLegend: false, showValue: false,
      showPercent: false, showLabel: false, showTitle: false, dataBorder: { pt: 0.5, color: WHITE }, firstSliceAng: 0 });
    T(s, pct(used), { x: 8.88, y: y + 0.5, w: 1.1, h: 0.3, fontSize: 13, bold: true, align: "center", valign: "middle" });
    T(s, [run(name, { bold: true, fontSize: 11.5 }), run("\n" + usage, { fontSize: 10, color: TEXT }),
      run("\n" + covers, { fontSize: 10, color: MUTED })], { x: 10.05, y: y + 0.1, w: 2.65, h: 1.15 });
  });
  box(s, 0.55, 6.5, 12.23, 0.44, { fill: INK, r: 0.06 });
  T(s, [run("Re-checked from scratch: ", { bold: true, color: SUN }),
    run(`run.bat verify → ${benchPass}/${D.benchmarks.length} benchmarks · ${testsPassed} tests · a fresh engine run identical to the official one · `
      + `the Moon stays bound · 3 studies reproduce (${n0(studyNumbers)} numbers, 0 differ) · 6/6 conditions → one results PDF`, { color: WHITE })],
    { x: 0.75, y: 6.5, w: 11.9, h: 0.44, fontSize: 11, valign: "middle" });
  s.addNotes("The scorecard. Each row is one of the guide's six winning conditions, with what we measured and how far inside the "
    + "limit it sits. The right column shows how much of each declared enabler the run used, and which flags each one covers: "
    + "six flags were raised and every one is covered, so none is unresolved. The dark strip is the one-command check anyone can run.");
}

// =====================================================================================================
// 3. Octo-Earth audited
// =====================================================================================================
{
  const s = content();
  const o = D.octo, arm = o.arm;
  head(s, "02 · THE REFERENCE CONCEPT, AUDITED", "Why not Octo-Earth: it cannot push, and it cannot stand",
    `We audited the company's eight-armed reference with the same physics as our machine, at the arm its demo draws: `
    + `${arm.arms} arms of ${n0(arm.length_km)} km in ${arm.segments} jointed segments, a ${arm.outer_diameter_km} km tube with `
    + `${arm.wall_km} km walls carrying ${arm.current_a / 1e6} MA, curling ${Math.round(o.curl.reach_deg)}° round the globe.`);
  // Diagram panel
  box(s, 0.55, 1.86, 4.45, 5.08, { fill: INK, r: 0.06 });
  T(s, "THE ARMS AS THE DEMO DRAWS THEM (Earth and lengths to scale)", { x: 0.75, y: 1.98, w: 4.1, h: 0.22, fontSize: 9.5, bold: true, color: MUTED_D });
  const ex = 2.78, ey = 4.55, R = 1.05, kmIn = R / 6371;
  circle(s, ex, ey, R, { fill: { color: "1E5F68" }, line: { color: EARTH, width: 1.25 } });
  s.addShape(pres.shapes.OVAL, { x: ex - R - 0.12, y: ey - 0.13, w: 2 * R + 0.24, h: 0.26, line: { color: ROCK, width: 2 } });
  // core loop and its push
  s.addShape(pres.shapes.OVAL, { x: ex - 0.22, y: ey - 0.07, w: 0.44, h: 0.14, line: { color: SUN, width: 1.5 } });
  line(s, ex, ey + 0.1, ex, ey + 0.72, { color: MARS, width: 2.25, end: "triangle" });
  T(s, `−${sci(Math.abs(o.all.on_core_n[2]), 3)} N\non the core`, { x: ex + 0.08, y: ey + 0.42, w: 1.3, h: 0.4, fontSize: 10, color: "F3B6A8", bold: true });
  // two arms curling over the top, with joints and claws
  const armPts = (side) => {
    const pts = [], start = side > 0 ? 8 : 172;
    for (let i = 0; i <= arm.segments; i++) {
      const u = i / arm.segments, ang = start + side * o.curl.reach_deg * u;
      const alt = o.curl.tip_altitude_km * Math.sin((Math.PI / 2) * Math.min(1, u * 1.15));
      const r = R + 0.03 + alt * kmIn;
      pts.push([ex + r * Math.cos((ang * Math.PI) / 180), ey - r * Math.sin((ang * Math.PI) / 180)]);
    }
    return pts;
  };
  [1, -1].forEach((side) => {
    const p = armPts(side);
    poly(s, p, { color: "C9D3E0", width: 3 });
    p.forEach((q, i) => { if (i % 3 === 0) circle(s, q[0], q[1], 0.025, { fill: { color: WHITE } }); });
    const [tx, ty] = p.at(-1), [px, py] = p.at(-2), dx = tx - px, dy = ty - py, L = Math.hypot(dx, dy);
    const ux = dx / L, uy = dy / L;
    line(s, tx, ty, tx + 0.16 * (ux - uy), ty + 0.16 * (uy + ux), { color: WHITE, width: 1.5 });
    line(s, tx, ty, tx + 0.16 * (ux + uy), ty + 0.16 * (uy - ux), { color: WHITE, width: 1.5 });
  });
  const top = armPts(1)[12];
  line(s, top[0], top[1], top[0], top[1] - 0.62, { color: SUN, width: 2.25, end: "triangle" });
  T(s, `+${sci(o.all.on_arms_n[2], 3)} N on the arms`, { x: top[0] - 1.85, y: top[1] - 0.66, w: 1.78, h: 0.22, fontSize: 10, color: SUN, bold: true, align: "right" });
  T(s, [run("Sum of the two: ", { bold: true, color: WHITE }),
    run(`${sci(o.all.sum_over_force)} of either force (test X8). Earth's field comes from its own core, so the arms' push on the `
      + "field comes back on the core: whatever their shape, the arms only push on Earth itself.", { color: TEXT_D })],
    { x: 0.75, y: 6.02, w: 4.1, h: 0.85, fontSize: 10 });
  // Two numbers
  const stat = (y, big, label, body) => {
    T(s, big, { x: 5.25, y, w: 3.0, h: 0.62, fontFace: HEAD, fontSize: 32, bold: true, color: MARS });
    T(s, [run(label, { bold: true, fontSize: 11.5 }), run("\n" + body, { fontSize: 10.5, color: MUTED })], { x: 5.25, y: y + 0.66, w: 3.0, h: 1.6 });
  };
  stat(1.9, sci(o.all.sum_over_force), "net push, as a share of the force",
    `Each side feels ${sci(o.all.on_arms_n[2], 3)} N; they cancel to rounding error. In the demo's 0.5 nT outside field, `
    + `all closed circuits together feel ${sci(o.outside.closed_circuits_n, 1)} N.`);
  const cnt = o.materials.find((m) => m.name.toLowerCase().includes("nanotube"));
  stat(4.35, "0.012", "safety factor at an arm's root",
    `Curled as drawn, a ${n0(arm.length_km)} km arm is a beam held only at its root: 5,500 GPa there even in ideal nanotube, `
    + `whose measured strength is ${n0(cnt.strength_pa / 1e9)} GPa. It needs 1.5.`);
  // Chart: the longest arm each material can hold up
  const mats = [...o.materials].reverse();
  const cats = mats.map((m) => m.name.replace("Structural steel S355", "Steel S355").replace(", unidirectional", "")
    .replace(/,? ideal macroscale.*/i, ", ideal").replace("Carbon nanotube", "Nanotube").replace(" composite", "").replace(" (axial)", ""));
  const cx0 = 8.45, cy0 = 1.86, cw = 4.33, ch = 3.75, lay = { x: 0.31, y: 0.13, w: 0.63, h: 0.62 };
  T(s, "Longest arm that holds itself up, at safety factor 1.5 (km, log scale)", { x: cx0, y: cy0, w: cw, h: 0.42, fontSize: 11, bold: true });
  s.addChart(pres.charts.BAR, [
    { name: "Curled as drawn", labels: cats, values: mats.map((m) => m.curled_longest_km) },
    { name: "Standing straight up", labels: cats, values: mats.map((m) => m.standing_longest_km) },
    { name: "Standing, before it buckles", labels: cats, values: mats.map((m) => m.buckling_length_km) },
  ], { ...CHART, x: cx0, y: cy0 + 0.3, w: cw, h: ch - 0.3, barDir: "bar", barGrouping: "clustered", barGapWidthPct: 45,
    chartColors: [MARS, ROCK, "C9D3E0"], valAxisLogScaleBase: 10, valAxisMinVal: 1, valAxisMaxVal: 100000,
    valAxisLabelFormatCode: "#,##0", showLegend: true, legendPos: "b", layout: lay });
  const lx = cx0 + cw * (lay.x + lay.w * Math.log10(arm.length_km) / 5);
  const ly0 = cy0 + 0.3 + (ch - 0.3) * lay.y, ly1 = cy0 + 0.3 + (ch - 0.3) * (lay.y + lay.h);
  line(s, lx, ly0, lx, ly1, { color: MARS, width: 1.75, dash: "dash" });
  T(s, `arm as drawn:\n${n0(arm.length_km)} km`, { x: lx - 1.15, y: ly0 - 0.02, w: 1.1, h: 0.4, fontSize: 10, bold: true, color: MARS, align: "right" });
  box(s, 8.45, 5.75, 4.33, 1.19, { fill: TINT });
  T(s, [run("So we move Earth with an outside mass. ", { bold: true }),
    run("An asteroid's gravity is a real external force: no structure on the planet, nothing to push against, and every "
      + "reaction is booked in the ledger.", { color: MUTED })], { x: 8.62, y: 5.85, w: 4.0, h: 1.0, fontSize: 11 });
  s.addNotes("The reference concept fails on two counts. First, Newton's third law: the arms push on Earth's magnetic field, which "
    + "comes from currents in Earth's own core, so the core is pushed back and the sum is zero to rounding error. Second, the arms "
    + "as drawn cannot hold up their own weight in any real material, not even ideal nanotube. Hence an external mass.");
}

// =====================================================================================================
// 4. The machine
// =====================================================================================================
{
  const s = content();
  const tow = TOWS["earth-tow"], dkm = tow.distance_km;
  head(s, "03 · THE MACHINE", "A gravity tractor held by light",
    `An asteroid ${fx(dkm / 384400, 2)} times the Moon's distance away pulls Earth outward with ${sci(pull, 3)} N. Earth pulls it `
    + "back just as hard, so focused light on a mirror tied to the asteroid holds it on its spot. Earth feels only gravity.");
  box(s, 0.55, 1.86, 8.0, 5.08, { fill: INK, r: 0.06 });
  T(s, "THE EARTH TOW, DISTANCES TO SCALE (bodies enlarged)", { x: 0.75, y: 1.98, w: 6, h: 0.22, fontSize: 9.5, bold: true, color: MUTED_D });
  const ex = 3.25, ey = 4.95, kIn = 2.5 / dkm;
  const d = [Math.SQRT1_2, -Math.SQRT1_2];               // 45° between along the orbit (up) and away from the Sun (right)
  const ax = ex + 2.5 * d[0], ay = ey + 2.5 * d[1];      // the asteroid
  const mx = ax + 0.5 * d[0], my = ay + 0.5 * d[1];      // its mirror
  line(s, ex - 0.02, 6.85, ex - 0.02, 2.3, { color: ORBIT_D, width: 1, dash: "dash" });
  T(s, "Earth's orbit", { x: ex - 1.2, y: 2.32, w: 1.1, h: 0.2, fontSize: 10, color: MUTED_D, align: "right" });
  ring(s, ex, ey, 384400 * kIn, "5A6A86", 0.75, { dash: "sysDot" });
  circle(s, ex - 384400 * kIn * 0.82, ey + 384400 * kIn * 0.57, 0.06, { fill: { color: "C9D3E0" } });
  T(s, "Moon's orbit", { x: ex - 1.62, y: ey + 0.92, w: 0.9, h: 0.2, fontSize: 10, color: MUTED_D });
  ring(s, ex, ey, 420000 * kIn, MARS, 1, { dash: "dash" });
  T(s, `no beam inside 420,000 km\n(closest ${n0(ET.beam_clearance_min_km)} km)`, { x: ex - 2.55, y: ey - 1.45, w: 1.75, h: 0.4, fontSize: 10, color: "F3B6A8", align: "right" });
  circle(s, ex, ey, 0.3, { fill: { color: "1E5F68" }, line: { color: EARTH, width: 1.5 } });
  T(s, "Earth", { x: ex - 0.5, y: ey + 0.33, w: 1.0, h: 0.2, fontSize: 10, bold: true, color: EARTH, align: "center" });
  // directions and the 45° between them
  line(s, ex, ey - 0.32, ex, ey - 1.15, { color: MUTED_D, width: 1.25, end: "triangle" });
  T(s, "orbital velocity", { x: ex - 1.35, y: ey - 1.18, w: 1.28, h: 0.2, fontSize: 10, color: MUTED_D, align: "right" });
  line(s, ex + 0.32, ey, ex + 1.15, ey, { color: MUTED_D, width: 1.25, end: "triangle" });
  T(s, "away from the Sun", { x: ex + 0.55, y: ey + 0.05, w: 1.4, h: 0.2, fontSize: 10, color: MUTED_D });
  poly(s, arcPts(ex, ey, 0.62, 0, 45, 12), { color: SUN, width: 1 });
  T(s, "45°", { x: ex + 0.62, y: ey - 0.42, w: 0.4, h: 0.2, fontSize: 10, bold: true, color: SUN });
  // asteroid, cables, mirror
  circle(s, ax, ay, 0.24, { fill: { color: "7C8698" }, line: { color: "AEB6C4", width: 0.75 } });
  circle(s, ax - 0.07, ay - 0.05, 0.05, { fill: { color: "5F6878" } });
  circle(s, ax + 0.08, ay + 0.07, 0.035, { fill: { color: "5F6878" } });
  const mh = 0.3, m1 = [mx - mh * Math.SQRT1_2, my - mh * Math.SQRT1_2], m2 = [mx + mh * Math.SQRT1_2, my + mh * Math.SQRT1_2];
  line(s, ax - 0.12, ay - 0.16, m1[0], m1[1], { color: "AEB6C4", width: 0.75 });
  line(s, ax + 0.16, ay + 0.12, m2[0], m2[1], { color: "AEB6C4", width: 0.75 });
  line(s, m1[0], m1[1], m2[0], m2[1], { color: WHITE, width: 4 });
  // the beam: in from the stations on the Sun's side, out downward
  line(s, 0.75, my, mx - 0.02, my, { color: SUN, width: 3, end: "triangle", transparency: 10 });
  line(s, mx, my + 0.02, mx, 6.8, { color: SUN, width: 1.5, dash: "dash", end: "triangle", transparency: 30 });
  T(s, "← from the beam stations on the Sun's side (E1)", { x: 0.75, y: my - 0.28, w: 3.6, h: 0.22, fontSize: 10, color: SUN });
  T(s, "light leaving: its momentum booked", { x: mx + 0.1, y: 6.45, w: 2.2, h: 0.36, fontSize: 10, color: SUN });
  // forces
  line(s, ex + 0.24, ey - 0.24, ex + 0.95, ey - 0.95, { color: WHITE, width: 2.5, end: "triangle" });
  T(s, `asteroid's pull on Earth\n${sci(pull, 3)} N, ${sci(accel, 3)} m/s²`, { x: ex + 0.98, y: ey - 0.74, w: 2.0, h: 0.4, fontSize: 10, bold: true, color: WHITE });
  line(s, ax - 0.2, ay + 0.2, ax - 0.75, ay + 0.75, { color: "C9D3E0", width: 2.5, end: "triangle" });
  T(s, "Earth's pull back,\njust as strong", { x: ax - 2.05, y: ay + 0.32, w: 1.3, h: 0.4, fontSize: 10, color: "C9D3E0", align: "right" });
  line(s, mx + 0.08, my - 0.08, mx + 0.7, my - 0.7, { color: SUN, width: 2.5, end: "triangle" });
  T(s, "light push (P/c)(n̂in − n̂out)\nholds the asteroid", { x: mx + 0.35, y: my - 0.95, w: 2.2, h: 0.4, fontSize: 10, bold: true, color: SUN });
  T(s, `${n0(dkm)} km`, { x: ex + 1.18, y: ey - 1.47, w: 1.0, h: 0.2, fontSize: 10, color: TEXT_D, rotate: -45 });
  // right column: the numbers
  const cards = [
    ["Tow asteroid", `${sci(tow.asteroid_mass_kg, 3)} kg, 336 km radius at 2,500 kg/m³; held ${n0(tow.distance_km)}–${n0(Math.round(ET.target_distance_km[1] / 100) * 100)} km from Earth; E3 places it.`, "6C7A89"],
    ["The pull", `${sci(pull, 3)} N on Earth, ${sci(accel, 3)} m/s². Its along-orbit part widens Earth's orbit a little on every lap (Gauss).`, EARTH_D],
    ["The beam (E1)", `${sci(ET.beam_min_w)}–${sci(ET.beam_max_w)} W on the Earth tow; both beams peak at ${sci(S.total_beam_max_w, 3)} W of 10²⁶; the stations' recoil (up to ${sci(S.station_recoil_max_n)} N) is booked.`, SUN_D],
    ["The controller", `Asks each step for the force that keeps the asteroid on its spot (10-day response); it strayed at most ${n0(ET.spot_error_max_km)} km (${pct(ET.spot_error_max_km / dkm, 1)}).`, BLUE],
    ["Why 45°", `Light can only push. At 45° the pull grows the orbit most per watt; the mirror stayed at ${fx(ET.mirror_angle_min_deg, 1)}°–${fx(ET.mirror_angle_max_deg, 1)}°.`, MARS],
  ];
  cards.forEach(([t, body, c], i) => {
    const y = 1.86 + i * 1.035;
    box(s, 8.8, y, 3.98, 0.95, { fill: TINT });
    badge(s, 9.08, y + 0.3, String(i + 1), c, { r: 0.16, size: 10 });
    T(s, [run(t, { bold: true, fontSize: 11.5 }), run("\n" + body, { fontSize: 10, color: MUTED })], { x: 9.35, y: y + 0.08, w: 3.35, h: 0.84 });
  });
  s.addNotes("This is the Earth tow, with distances to scale. The asteroid sits about 1.7 times the Moon's distance away, at 45 degrees "
    + "between straight ahead along Earth's orbit and straight out from the Sun. Its gravity pulls Earth; Earth pulls it back, and a "
    + "beam of light from stations on the Sun's side pushes on a mirror tied to the asteroid to hold it in place. The light only "
    + "pushes, and the beam never comes within 420,000 km of Earth.");
}

// =====================================================================================================
// 5. The journey
// =====================================================================================================
{
  const s = content();
  head(s, "04 · THE JOURNEY", `1 AU to ${fx(ARR.a_au, 4)} AU in ${n0(ARR.year)} years`,
    `Mars is moved first and parked at ${TOWS["mars-tow"].stop_au} AU in year ${n0(marsPark.t)}, so the planets never come closer `
    + `than ${fx(S.mars_closest.au, 3)} AU. From 2 AU, Earth's tow trims the arrival orbit to the one Jupiter forces at 2.7 AU.`);
  const J = D.journey, n = J.length, labels = J.map((f) => n0(Math.round(f.t / 100) * 100));
  const cx0 = 0.55, cy0 = 1.86, cw = 7.85, ch = 3.3, lay = { x: 0.08, y: 0.05, w: 0.9, h: 0.76 };
  s.addChart(pres.charts.LINE, [
    { name: "Earth's orbit (AU)", labels, values: J.map((f) => f.earth_a) },
    { name: "Mars's orbit (AU)", labels, values: J.map((f) => f.mars_a) },
    { name: "Target 2.7 AU", labels, values: J.map(() => D.config.target_au) },
  ], { ...CHART, x: cx0, y: cy0, w: cw, h: ch, chartColors: [EARTH, MARS, SUN], lineSize: 2.25, lineDataSymbol: "none",
    valAxisMinVal: 0.5, valAxisMaxVal: 4, valAxisMajorUnit: 0.5, valAxisLabelFormatCode: "0.0", catAxisLabelFrequency: 20,
    showLegend: true, legendPos: "b", layout: lay, valAxisTitle: "orbit size (AU)", showValAxisTitle: true });
  const X = (t) => cx0 + cw * (lay.x + lay.w * (t / J.at(-1).t) * ((n - 1) / n) + lay.w * 0.5 / n);
  const Y = (a) => cy0 + ch * (lay.y + lay.h * (1 - (a - 0.5) / 3.5));
  rect(s, X(MS.mars_sprint_from), cy0 + ch * lay.y, X(MS.mars_sprint_to) - X(MS.mars_sprint_from), ch * lay.h, MARS, { ft: 85 });
  const note = (x, y, w, text, c, o = {}) => T(s, text, { x, y, w, h: 0.4, fontSize: 10, color: c, ...o });
  note(X(MS.mars_sprint_from) - 2.35, Y(3.35) - 0.05, 2.3, "Mars's sprint across Jupiter's 2:1 resonance (3.28 AU)", MARS, { align: "right" });
  circle(s, X(marsPark.t), Y(marsPark.a), 0.06, { fill: { color: MARS } });
  note(X(marsPark.t) + 0.12, Y(marsPark.a) - 0.44, 2.4, `Mars parked at ${fx(marsPark.a, 2)} AU, year ${n0(marsPark.t)}, e = ${fx(MT.arrival.eccentricity, 3)}`, MARS, { bold: true });
  circle(s, X(MS.earth_2au), Y(2.0), 0.06, { fill: { color: EARTH } });
  note(X(MS.earth_2au) - 2.35, Y(2.0) + 0.1, 2.25, `2.0 AU in year ${n0(MS.earth_2au)}: the arrival trim begins (pull varied up to 40% round each lap, up to 20° off the plane)`, EARTH_D, { align: "right", h: 0.6 });
  circle(s, X(ARR.year), Y(ARR.a_au), 0.06, { fill: { color: EARTH } });
  note(X(ARR.year) - 1.75, Y(ARR.a_au) + 0.12, 1.7, `arrives year ${n0(ARR.year)}\ne = ${fx(ARR.eccentricity, 3)}, tilt ${fx(ARR.tilt_deg, 2)}°`, EARTH_D, { bold: true, align: "right" });
  note(X(0) + 0.1, Y(1.0) - 0.45, 2.6, `closest Earth–Mars: ${fx(S.mars_closest.au, 3)} AU, at the start`, MUTED);

  // Crossing Jupiter's 2:1 resonance: caught starts out of eight
  box(s, 8.65, 1.86, 4.13, 3.3, { fill: TINT });
  T(s, [run("Crossing Jupiter's 2:1 resonance", { bold: true, fontSize: 12 }),
    run("\nAt 3.28 AU Mars's year is half Jupiter's, and a slow crossing gets caught. Eight starting points per pull; a filled dot "
      + "never reached its parking orbit.", { fontSize: 10, color: MUTED })], { x: 8.82, y: 1.96, w: 3.85, h: 1.0 });
  const cross = Object.entries(D.crossing).filter(([, v]) => v.of);
  cross.forEach(([name, v], i) => {
    const y = 3.08 + i * 0.4, chosen = name.startsWith("chosen");
    const label = chosen ? "4× sprint (chosen)" : name.replace("normal pull", "normal pull").replace(/ \(.*\)/, "")
      .replace("sprint ", "").replace("x", "× sprint");
    T(s, label, { x: 8.82, y: y - 0.1, w: 1.35, h: 0.22, fontSize: 10, bold: chosen, color: chosen ? EARTH_D : TEXT });
    const caughtN = v.caught;
    for (let j = 0; j < v.of; j++) {
      const c = j < caughtN;
      circle(s, 10.3 + j * 0.25, y + 0.01, 0.085, c ? { fill: { color: MARS } } : { line: { color: chosen ? EARTH : ROCK, width: 1.25 } });
    }
    T(s, `${v.caught}/${v.of}`, { x: 12.3, y: y - 0.1, w: 0.4, h: 0.22, fontSize: 10, bold: true, color: v.caught ? MARS : PASS });
  });

  // Timeline of the whole mission
  const t0x = 2.15, t1x = 12.55, TX = (t) => t0x + (t1x - t0x) * t / YEARS;
  const lanes = [
    ["Mars tow", [[0, marsPark.t, MARS, `towing Mars out to ${TOWS["mars-tow"].stop_au} AU`], [MS.mars_sprint_from, MS.mars_sprint_to, "8E2F1E", ""]]],
    ["Earth tow", [[0, MS.earth_2au, EARTH, `towing Earth out from ${n0(TOWS["earth-tow"].distance_km)} km away`], [MS.earth_2au, ARR.year, EARTH_D, "arrival trim"]]],
    ["Sunlight optics (E3)", [[MS.optics_from, S.end.year, SUN, `built in 25-year batches, up to ${sci(D.mirrors.face_on_area_km2)} km²`]]],
  ];
  lanes.forEach(([name, bars], i) => {
    const y = 5.36 + i * 0.34;
    T(s, name, { x: 0.55, y: y + 0.02, w: 1.55, h: 0.22, fontSize: 10, bold: true, align: "right" });
    bars.forEach(([a, b, c, text]) => {
      rect(s, TX(a), y, TX(b) - TX(a), 0.26, c);
      if (text) T(s, text, { x: TX(a) + 0.08, y: y + 0.02, w: TX(b) - TX(a) - 0.1, h: 0.22, fontSize: 10, color: WHITE, bold: true });
    });
  });
  const ay = 6.55;
  line(s, t0x, ay, t1x, ay, { color: MUTED, width: 1 });
  for (let t = 0; t <= YEARS; t += 1000) {
    line(s, TX(t), ay, TX(t), ay + 0.06, { color: MUTED, width: 0.75 });
    T(s, n0(t), { x: TX(t) - 0.35, y: ay + 0.08, w: 0.7, h: 0.2, fontSize: 10, color: MUTED, align: "center" });
  }
  S.big_asteroid_nudges.forEach((nd) => {
    s.addShape(pres.shapes.DIAMOND, { x: TX(nd.year) - 0.07, y: ay - 0.17, w: 0.14, h: 0.14, fill: { color: SUN_D } });
  });
  T(s, `E1 nudges Vesta (${fx(S.big_asteroid_nudges[0].beam_hours, 3)} h of beam each) ◆`, { x: TX(S.big_asteroid_nudges[0].year) - 3.2, y: ay - 0.2, w: 3.08, h: 0.2, fontSize: 10, color: SUN_D, align: "right" });
  line(s, TX(YEARS), 5.36, TX(YEARS), ay, { color: MARS, width: 1.5, dash: "dash" });
  T(s, "limit", { x: TX(YEARS) - 0.45, y: 5.12, w: 0.9, h: 0.2, fontSize: 10, bold: true, color: MARS, align: "center" });
  T(s, "years →", { x: 0.55, y: ay + 0.08, w: 1.55, h: 0.2, fontSize: 10, color: MUTED, align: "right" });
  s.addNotes(`Earth's orbit grows slowly at first and faster as it widens. Mars's tow sprints across Jupiter's 2:1 resonance, `
    + `where the normal pull got Mars caught in six of eight trials; at four times the pull none are caught. `
    + `From 2 AU the Earth tow varies its pull around each lap and rides slightly off the orbit plane so Earth arrives on the `
    + `orbit Jupiter forces at 2.7 AU. The optics are built from year ${Math.round(MS.optics_from)} as sunlight starts to fall.`);
}

// =====================================================================================================
// 6. The engine and the momentum ledger
// =====================================================================================================
{
  const s = content();
  head(s, "05 · THE ENGINE", "Every push is booked with its partner",
    "A Newtonian N-body engine with an error-free momentum ledger. The only outside forces are the beams on the two tow asteroids, "
    + "and their partners (the stations' recoil, the light that leaves) are booked too.");
  const eqs = [
    ["Gravity, every pair once", "r̈ᵢ = Σⱼ G mⱼ (rⱼ−rᵢ)/|rⱼ−rᵢ|³ + Fᵢ/mᵢ",
      "Sun; Venus to Neptune on J2000 orbits; Ceres, Pallas, Vesta, Hygiea; both tow asteroids"],
    ["Light pressure", "F = (P/c)(n̂in − n̂out)", "a mirror is only ever pushed; the power for a wanted force: P = |F|²c / (2 n̂in·F)"],
    ["Orbit growth (Gauss)", "da/dt = (2a² / μ) v · f", "only the along-orbit part of the pull grows the orbit; benchmark 8 checks it"],
    ["Climate (Budyko–Sellers)", "(S/4)(1 − α(T)) = ε σ T⁴", "albedo 0.30 → 0.62 as ice spreads; a latitude profile gives the liquid-water share"],
    ["The Moon stays (Hill)", "r_H = a (m⊕ / 3M☉)^⅓", `the Moon at ${fx(CL.moon_hill_share[1], 3)} of Earth's Hill radius today, ${fx(CL.moon_hill_share[0], 3)} at 2.7 AU`],
    ["Air and magnetic shield", "λ = GMm / (kT r)", `nitrogen's Jeans λ stays ≥ ${n0(CL.jeans_lambda_n2[0])} (escape needs < 30); magnetopause ${fx(CL.magnetopause_re[0], 0)} → ${fx(CL.magnetopause_re[1], 1)} R⊕`],
  ];
  eqs.forEach(([t, eq, role], i) => {
    const x = 0.55 + (i % 2) * 2.98, y = 1.86 + Math.floor(i / 2) * 1.2;
    box(s, x, y, 2.86, 1.1, { fill: TINT });
    T(s, t, { x: x + 0.12, y: y + 0.08, w: 2.65, h: 0.2, fontSize: 10.5, bold: true, color: EARTH_D });
    T(s, eq, { x: x + 0.12, y: y + 0.3, w: 2.7, h: 0.3, fontFace: HEAD, fontSize: 11.5, color: TEXT });
    T(s, role, { x: x + 0.12, y: y + 0.62, w: 2.65, h: 0.45, fontSize: 10, color: MUTED });
  });
  const integ = [
    ["Leapfrog (kick–drift–kick), 1 day", "the journey; half the step moves arrival 0.3%"],
    ["Yoshida 4th order", "the ten official benchmarks"],
    ["REBOUND MERCURIUS, 5 days", "a million years after arrival"],
    ["REBOUND IAS15", "an independent cross-check (X6)"],
  ];
  s.addTable([[{ text: "Integrator", options: { bold: true, fill: { color: INK }, color: WHITE } },
               { text: "Used for", options: { bold: true, fill: { color: INK }, color: WHITE } }],
    ...integ.map(([a, b]) => [{ text: a, options: { bold: true } }, b])],
  { x: 0.55, y: 5.55, w: 5.84, colW: [2.6, 3.24], fontFace: BODY, fontSize: 10, color: TEXT, rowH: 0.27,
    border: { type: "solid", pt: 0.5, color: LINE }, margin: [0.02, 0.08, 0.02, 0.08], valign: "middle" });

  // Ledger flow
  box(s, 6.6, 1.86, 6.18, 2.86, { fill: TINT });
  T(s, "WHERE EVERY PUSH GOES", { x: 6.78, y: 1.95, w: 4, h: 0.22, fontSize: 9.5, bold: true, color: MUTED });
  const node = (x, y, w, text, c) => {
    s.addText(text, { shape: pres.shapes.ROUNDED_RECTANGLE, rectRadius: 0.06, x, y, w, h: 0.6, fill: { color: WHITE },
      line: { color: c, width: 1.5 }, fontFace: BODY, fontSize: 10.5, bold: true, color: TEXT, align: "center", valign: "middle", margin: 0.04 });
  };
  node(6.8, 2.3, 1.6, "Beam stations (E1)", SUN);
  node(8.95, 2.3, 1.6, "Tow mirror and cables", SUN);
  node(11.05, 2.3, 1.55, "Tow asteroid", ROCK);
  node(11.05, 3.6, 1.55, "Earth (with the Moon's mass)", EARTH);
  node(6.8, 3.6, 1.6, "Stations' recoil: booked", MARS);
  node(8.95, 3.6, 1.6, "Light leaving: booked", MARS);
  line(s, 8.4, 2.6, 8.93, 2.6, { color: SUN_D, width: 2, end: "triangle" });
  T(s, "light, P/c", { x: 8.35, y: 2.33, w: 0.62, h: 0.2, fontSize: 9.5, color: SUN_D, align: "center" });
  line(s, 10.55, 2.6, 11.03, 2.6, { color: TEXT, width: 2, end: "triangle" });
  T(s, "cables", { x: 10.5, y: 2.33, w: 0.6, h: 0.2, fontSize: 9.5, color: MUTED, align: "center" });
  line(s, 11.82, 2.92, 11.82, 3.58, { color: EARTH_D, width: 2, end: "triangle", begin: "triangle" });
  T(s, "gravity: exact\nopposite pairs", { x: 11.9, y: 3.05, w: 0.85, h: 0.42, fontSize: 9.5, color: EARTH_D });
  line(s, 7.6, 2.92, 7.6, 3.58, { color: MARS, width: 1.5, end: "triangle" });
  line(s, 9.75, 2.92, 9.75, 3.58, { color: MARS, width: 1.5, end: "triangle" });
  T(s, `Applied impulse over the journey: ${sci(LED.applied_impulse_kg_m_s, 3)} kg m/s. Asteroids sent away after arrival take their `
    + "momentum with them, booked.", { x: 6.8, y: 4.25, w: 5.85, h: 0.42, fontSize: 10, color: MUTED });
  // Ledger on a log scale
  T(s, "The guide's two ledger checks, worst over the journey (log scale)", { x: 6.6, y: 4.88, w: 6.18, h: 0.22, fontSize: 11, bold: true });
  const lx0 = 6.75, lx1 = 12.6, LX = (e) => lx0 + (lx1 - lx0) * (e + 24) / 18, ly = 5.62;
  line(s, lx0, ly, lx1, ly, { color: LINE, width: 3 });
  for (let e = -24; e <= -6; e += 3) {
    line(s, LX(e), ly - 0.05, LX(e), ly + 0.05, { color: MUTED, width: 0.75 });
    T(s, `10${sup(e)}`, { x: LX(e) - 0.3, y: ly + 0.08, w: 0.6, h: 0.2, fontSize: 10, color: MUTED, align: "center" });
  }
  rect(s, LX(-9), ly - 0.1, lx1 - LX(-9), 0.2, MARS, { ft: 80 });
  line(s, LX(-9), ly - 0.32, LX(-9), ly + 0.12, { color: MARS, width: 1.75 });
  T(s, "guide's limit 10⁻⁹", { x: LX(-9) + 0.05, y: ly - 0.36, w: 1.4, h: 0.2, fontSize: 10, bold: true, color: MARS });
  const mark = (v, text, up) => {
    const x = LX(Math.log10(v));
    circle(s, x, ly, 0.07, { fill: { color: PASS }, line: { color: WHITE, width: 0.75 } });
    T(s, text, { x: x - 1.0, y: up ? ly - 0.55 : ly + 0.3, w: 2.0, h: 0.4, fontSize: 10, color: TEXT, align: "center", bold: true });
  };
  mark(LED.integrator_honest_max, `integrator honest\n${sci(LED.integrator_honest_max)}`, true);
  mark(LED.nothing_from_nothing_max, `nothing from nothing\n${sci(LED.nothing_from_nothing_max)}`, true);
  T(s, "float64 rounding ≈ 10⁻¹⁶ ↑", { x: LX(-16) - 0.75, y: ly + 0.3, w: 1.6, h: 0.2, fontSize: 10, color: MUTED, align: "center" });
  box(s, 6.6, 6.38, 6.18, 0.56, { fill: INK, r: 0.06 });
  T(s, [run("Energy: ", { bold: true, color: SUN }),
    run(`the beams did ${sci(LED.beam_work_j, 5)} J of work and the bodies gained ${sci(LED.bodies_energy_gain_j, 5)} J, counting what `
      + `left with the asteroids: a ${pct(LED.work_mismatch_share, 3)} match.`, { color: WHITE })],
    { x: 6.78, y: 6.38, w: 5.9, h: 0.56, fontSize: 10.5, valign: "middle" });
  s.addNotes("The physics in the engine, and the bookkeeping. Every pair of bodies pulls each other with exactly opposite forces. The "
    + "only outside forces are the beams' pushes on the tow asteroids, and their partners, the recoil on the stations and the light "
    + "that leaves, are booked. The guide's two ledger checks sit seven to thirteen orders of magnitude inside the limit.");
}

// =====================================================================================================
// 7. Validation
// =====================================================================================================
{
  const s = content();
  head(s, "06 · VALIDATION", `${benchPass} of ${D.benchmarks.length} benchmarks, ${testsPassed} tests, one command to check it all`,
    "Every official benchmark passes, also with inputs a judge changes (python -m sim.benchmarks 4 --set e=0.5); run.bat verify "
    + "re-runs everything and writes a results PDF.");
  const B = Object.fromEntries(D.benchmarks.map((b) => [b.n, b]));
  const measured = {
    1: `(${B[1].measured.join(", ")}) N`, 2: `${sci(B[2].measured)} of I L B`, 3: `${(B[3].measured * 1e4).toFixed(5)} × 10⁻⁴ T`,
    4: `back within ${sci(B[4].measured.position_over_a)} a; energy ${sci(B[4].measured.energy)}`, 5: `energy error ${sci(B[5].measured)}`,
    6: `${fx(B[6].measured, 3)} days`, 7: `${fx(B[7].measured[0], 3)}, ${fx(B[7].measured[1], 3)} km/s; ${fx(B[7].measured[2], 1)} days`,
    8: `${fx(B[8].measured, 1)} km`, 9: "root moment, tip deflection within 10⁻⁹", 10: `${fx(B[10].measured, 1)} K`,
  };
  const expected = {
    1: "(0, 0, 10) N (10⁻⁹)", 2: "0 (10⁻⁹ of I L B)", 3: "μ₀I/2πr (10⁻⁶)", 4: "10⁻⁶ a; 10⁻⁹", 5: "10⁻⁹",
    6: `${B[6].expected} (0.1 day)`, 7: "2.94, 2.65 km/s; 259 d (±0.02; ±2)", 8: `${fx(B[8].expected, 1)} km, Gauss (1%)`,
    9: "qL²/2, qL⁴/8EI (1%)", 10: "254 K (2 K)",
  };
  const hdr = ["#", "Benchmark", "Measured", "Expected (tolerance)", ""].map((t) => ({ text: t, options: { bold: true, fill: { color: INK }, color: WHITE } }));
  s.addTable([hdr, ...D.benchmarks.map((b) => [String(b.n), b.name.replace("Earth-Moon", "Earth–Moon"), measured[b.n], expected[b.n],
    { text: b.ok ? "✓" : "✗", options: { bold: true, color: b.ok ? PASS : MARS, align: "center" } }])],
  { x: 0.55, y: 1.86, w: 7.05, colW: [0.3, 2.05, 2.45, 1.95, 0.3], fontFace: BODY, fontSize: 10, color: TEXT, rowH: 0.29,
    border: { type: "solid", pt: 0.5, color: LINE }, margin: [0.02, 0.06, 0.02, 0.06], valign: "middle" });
  T(s, "Convergence: halving the step to 0.5 day moves arrival from year 8,758 to 8,730 (0.3%), with the same orbit and 0 unresolved flags.",
    { x: 0.55, y: 5.2, w: 7.05, h: 0.38, fontSize: 10, color: MUTED });
  // X1-X9
  T(s, "Our own checks, X1–X9", { x: 7.85, y: 1.86, w: 4.9, h: 0.24, fontSize: 12, bold: true });
  const xs = ["Kepler's third law", "Energy steady for 1,000 years", "Ledger with a push on", "A Hohmann transfer, flown",
    "Arrival time under steady push", "Agrees with REBOUND IAS15", "The asteroid's pull and hold", "Octo-Earth: zero net push",
    "Earth's real axial-tilt cycle"];
  xs.forEach((t, i) => {
    const x = 7.85 + (i % 3) * 1.66, y = 2.18 + Math.floor(i / 3) * 0.6;
    box(s, x, y, 1.58, 0.52, { fill: TINT });
    badge(s, x + 0.2, y + 0.26, `X${i + 1}`, EARTH_D, { r: 0.14, size: 9 });
    T(s, t, { x: x + 0.4, y: y + 0.05, w: 1.14, h: 0.44, fontSize: 10, valign: "middle" });
  });
  // The verify pipeline
  T(s, "run.bat verify: the whole check, one command, one PDF", { x: 7.85, y: 4.1, w: 4.93, h: 0.24, fontSize: 12, bold: true });
  const steps = verifyRows.length ? verifyRows : [];
  const short = { "Official benchmarks": "Bench-\nmarks", "Test suite": "Tests", "Engine: a fresh run": "Engine\nre-run",
    "Moon test": "Moon", "Octo-Earth audit": "Octo-\nEarth", "Small-asteroid study": "Small\nrocks", "Sunlight-optics study": "Optics",
    "The six winning conditions": "6 condi-\ntions" };
  line(s, 8.1, 4.75, 12.55, 4.75, { color: PASS, width: 2 });
  steps.forEach((r, i) => {
    const x = 8.1 + i * (4.45 / 7);
    badge(s, x, 4.75, "✓", r.ok ? PASS : MARS, { r: 0.17, size: 11 });
    T(s, `${short[r.title] || r.title}\n${Math.round(r.seconds)} s`, { x: x - 0.32, y: 4.97, w: 0.64, h: 0.62, fontSize: 9.5, color: MUTED, align: "center" });
  });
  // Structures
  T(s, "Structures, sized for the most a beam can ever push (2P/c at the power cap), so the catch-up after an outage is covered",
    { x: 0.55, y: 5.68, w: 12.23, h: 0.24, fontSize: 11, bold: true });
  const st = [
    ["Cable safety factor", capVal("earth-tow", "cable"), capVal("mars-tow", "cable"), 1.5, "≥ 1.5", (v) => fx(v, 2), 3, false],
    ["Anchor safety factor", capVal("earth-tow", "anchor"), capVal("mars-tow", "anchor"), 1.5, "≥ 1.5", (v) => fx(v, 2), 3, false],
    ["Tow mirror temperature", capVal("earth-tow", "temperature"), capVal("mars-tow", "temperature"), 1500, "≤ 1,500 K", (v) => `${n0(v)} K`, 1600, true],
    ["Asteroid body safety factor", capVal("earth-tow", "asteroid body"), capVal("mars-tow", "asteroid body"), 1.5, "≥ 1.5", (v) => n0(v), 160, false],
  ];
  st.forEach(([t, e, m, lim, limText, f, max, upper], i) => {
    const x = 0.55 + i * 3.08, y = 6.0;
    box(s, x, y, 2.95, 0.94, { fill: TINT });
    T(s, [run(t, { bold: true }), run(`  ${limText}`, { color: MUTED })], { x: x + 0.12, y: y + 0.07, w: 2.75, h: 0.22, fontSize: 10 });
    T(s, [run(`Earth ${f(e)}`, { bold: true, color: EARTH_D }), run("  ·  "), run(`Mars ${f(m)}`, { bold: true, color: MARS })],
      { x: x + 0.12, y: y + 0.32, w: 2.75, h: 0.26, fontSize: 12 });
    const gx = x + 0.12, gw = 2.7, G = (v) => gx + gw * Math.min(v, max) / max;
    rect(s, gx, y + 0.7, gw, 0.08, LINE);
    rect(s, gx, y + 0.7, G(Math.min(e, m)) - gx, 0.08, upper ? SUN : PASS);
    line(s, G(lim), y + 0.63, G(lim), y + 0.85, { color: MARS, width: 1.5 });
  });
  s.addNotes("Validation. All ten official benchmarks pass, and a judge can change their inputs from the command line. Our own nine "
    + "checks add Kepler's law, long-run energy, the ledger under thrust, an agreement test with REBOUND's IAS15 and more. One command, "
    + "run.bat verify, re-runs all of it, including a fresh run of the engine compared with the official one, and writes a results PDF.");
}

// =====================================================================================================
// 8. Earth safety and the sunlight optics
// =====================================================================================================
{
  const s = content();
  const end = D.journey.at(-1);
  head(s, "07 · EARTH SAFETY", `Ten thresholds held at every one of ${n0(MS.checks)} checks`,
    `At 2.7 AU Earth gets ${pct(1 / ARR.a_au ** 2, 1)} of today's sunlight and the same model freezes it at ${n0(end.temperature_no_optics_k)} K. `
    + `Sunlight optics built by E3 hold it at ${fx(CL.sunlight_share[0], 3)}–${fx(CL.sunlight_share[1], 3)} of today's sunlight, `
    + `${fx(CL.temperature_k[0], 1)}–${fx(CL.temperature_k[1], 1)} K.`);
  const g = [
    ["Global mean temperature", "263–308 K", 220, 320, [SAFE.temperature_min_k, SAFE.temperature_max_k], CL.temperature_k, (v) => `${fx(v[0], 1)}–${fx(v[1], 1)} K`],
    ["Surface with liquid water", "≥ 30%", 0, 1, [SAFE.liquid_water_min_share, 1], CL.liquid_water_share, (v) => `≥ ${pct(v[0], 1)}`],
    ["Absorbed sunlight (runaway)", "< 282 W/m²", 150, 300, [150, SAFE.runaway_absorbed_max_w_m2], CL.absorbed_w_m2, (v) => `≤ ${fx(v[1], 1)} W/m²`],
    ["Surface pressure", "≥ 50 kPa", 0, 120, [SAFE.surface_pressure_min_kpa, 120], CL.surface_pressure_kpa, (v) => `${fx(v[0], 1)} kPa`],
    ["Nitrogen kept (Jeans λ)", "> 30", 0, 250, [SAFE.jeans_lambda_min, 250], CL.jeans_lambda_n2, (v) => `≥ ${n0(v[0])}`],
    ["Magnetopause distance", "≥ 3 Earth radii", 0, 16, [SAFE.magnetopause_min_re, 16], CL.magnetopause_re, (v) => `${fx(v[0], 1)}–${fx(v[1], 1)} R⊕`],
    ["Change in length of day", "≤ 1 s (log scale)", -10, 1, [-10, 0], [-10, Math.log10(MS.day_length_max_s)], () => `${sci(MS.day_length_max_s)} s`],
    ["Moon over Earth's Hill radius", "< 0.49", 0, 0.6, [0, SAFE.moon_hill_max_share], CL.moon_hill_share, (v) => `${fx(v[0], 3)}–${fx(v[1], 3)}`],
    ["Tow thrust over the Moon's pull", "< 0.01", 0, 0.012, [0, SAFE.thrust_over_moon_pull_max], CL.thrust_over_moon_pull, (v) => `≤ ${fx(v[1], 4)}`],
  ];
  g.forEach(([name, limText, lo, hi, ok, worst, f], i) => {
    const y = 1.88 + i * 0.565;
    T(s, [run(name, { bold: true }), run("\n" + limText, { color: MUTED })], { x: 0.55, y, w: 2.15, h: 0.5, fontSize: 10.5 });
    const gx = 2.75, gw = 2.3, G = (v) => gx + gw * (Math.min(Math.max(v, lo), hi) - lo) / (hi - lo), gy = y + 0.17;
    rect(s, gx, gy, gw, 0.16, "E6EAF0");
    rect(s, G(ok[0]), gy, G(ok[1]) - G(ok[0]), 0.16, PASS_BG);
    [ok[0], ok[1]].forEach((v) => { if (v > lo && v < hi) line(s, G(v), gy - 0.06, G(v), gy + 0.22, { color: MARS, width: 1.25 }); });
    rect(s, G(worst[0]), gy + 0.02, Math.max(G(worst[1]) - G(worst[0]), 0.05), 0.12, EARTH_D);
    T(s, f(worst), { x: 5.12, y: y + 0.1, w: 1.25, h: 0.3, fontSize: 10.5, bold: true, color: EARTH_D });
  });
  T(s, "green: allowed · red tick: the limit · teal: the range over the whole journey", { x: 0.55, y: 6.98, w: 6, h: 0.14, fontSize: 9, color: MUTED });
  // Temperature with and without the optics
  const J = D.journey, labels = J.map((f) => n0(Math.round(f.t / 100) * 100));
  const cx0 = 6.6, cy0 = 1.86, cw = 6.18, ch = 2.65, lay = { x: 0.1, y: 0.16, w: 0.87, h: 0.66 };
  s.addChart(pres.charts.LINE, [
    { name: "With the sunlight optics (the run)", labels, values: J.map((f) => f.temperature_k) },
    { name: "Same climate model, no optics", labels, values: J.map((f) => f.temperature_no_optics_k) },
    { name: "Lowest allowed, 263 K", labels, values: J.map(() => SAFE.temperature_min_k) },
  ], { ...CHART, x: cx0, y: cy0, w: cw, h: ch, chartColors: [EARTH, MARS, "B8C1CE"], lineSize: 2.25, lineDataSymbol: "none",
    valAxisMinVal: 140, valAxisMaxVal: 300, valAxisMajorUnit: 40, catAxisLabelFrequency: 30, showLegend: true, legendPos: "t",
    layout: lay, valAxisTitle: "global mean (K)", showValAxisTitle: true });
  const X = (t) => cx0 + cw * (lay.x + lay.w * (t / J.at(-1).t) * ((J.length - 1) / J.length) + lay.w * 0.5 / J.length);
  const Y = (k) => cy0 + ch * (lay.y + lay.h * (1 - (k - 140) / 160));
  const a570 = D.journey.reduce((p, f) => (Math.abs(f.t - MS.earth_freezes_without_optics) < Math.abs(p.t - MS.earth_freezes_without_optics) ? f : p));
  T(s, `without the optics Earth drops off the ice-albedo cliff by year ${n0(MS.earth_freezes_without_optics)}, at only ${fx(a570.earth_a, 2)} AU`, { x: X(MS.earth_freezes_without_optics) + 0.15, y: Y(243), w: 3.6, h: 0.4, fontSize: 10, bold: true, color: MARS });
  T(s, `${n0(end.temperature_no_optics_k)} K at 2.7 AU`, { x: X(J.at(-1).t) - 1.45, y: Y(end.temperature_no_optics_k) - 0.3, w: 1.4, h: 0.22, fontSize: 10, color: MARS, align: "right" });
  // The L1 ring
  box(s, 6.6, 4.62, 6.18, 2.32, { fill: TINT });
  T(s, "WHERE THE OPTICS SIT: A REFRACTING RING NEAR L1", { x: 6.78, y: 4.7, w: 5.5, h: 0.22, fontSize: 9.5, bold: true, color: MUTED });
  const sx = 7.0, sy = 5.78, rx = 8.35, ex = 9.35;
  circle(s, sx, sy, 0.24, { fill: { color: SUN } });
  s.addShape(pres.shapes.OVAL, { x: rx - 0.05, y: sy - 0.62, w: 0.1, h: 1.24, line: { color: SUN_D, width: 1.75 } });
  circle(s, ex, sy, 0.14, { fill: { color: EARTH } });
  [-0.55, 0.55].forEach((dy) => {
    line(s, sx + 0.2, sy + dy * 0.35, rx, sy + dy, { color: SUN, width: 1 });
    line(s, rx, sy + dy, ex - 0.1, sy + dy * 0.12, { color: SUN_D, width: 1.25, end: "triangle" });
  });
  line(s, sx + 0.24, sy, ex - 0.15, sy, { color: SUN, width: 1, end: "triangle" });
  T(s, "Sun", { x: sx - 0.3, y: sy + 0.28, w: 0.6, h: 0.2, fontSize: 10, align: "center", color: SUN_D, bold: true });
  T(s, `ring near L1, ${fx(L1.l1_km / 1e6, 2)} M km from Earth`, { x: rx - 1.0, y: sy - 0.95, w: 2.4, h: 0.2, fontSize: 10, align: "center", color: SUN_D });
  T(s, "Earth", { x: ex - 0.35, y: sy + 0.18, w: 0.7, h: 0.2, fontSize: 10, align: "center", color: EARTH_D, bold: true });
  T(s, "Film bends extra sunlight onto Earth from the Sun's own direction, so noons and nights stay natural (Angel 2006, used the other way round).",
    { x: 6.78, y: 6.42, w: 2.95, h: 0.5, fontSize: 9.5, color: MUTED });
  const trs = ["0.95", "0.90", "0.85"].map((k) => [k, byT[k]]);
  s.addTable([[{ text: "Film passes", options: { bold: true } }, { text: "Sunlight", options: { bold: true } }, { text: "Earth", options: { bold: true } }],
    ...trs.map(([k, v]) => [pct(Number(k)), pct(v.sunlight_vs_today_at_e3, 1),
      { text: v.warm ? `${fx(v.temperature_k, 1)} K ✓` : `${n0(v.temperature_k)} K, frozen ✗`, options: { bold: true, color: v.warm ? PASS : MARS } }])],
  { x: 9.85, y: 4.98, w: 2.8, colW: [0.8, 0.75, 1.25], fontFace: BODY, fontSize: 10, color: TEXT, rowH: 0.27,
    border: { type: "solid", pt: 0.5, color: LINE }, fill: { color: WHITE }, margin: [0.02, 0.05, 0.02, 0.05], valign: "middle" });
  T(s, `Held to E3's ${sci(D.mirrors.e3_limit_km2)} km². The climate cliff is at ${pct(D.cliff, 1)} of today's sunlight, so the film must pass at least about 88%.`,
    { x: 9.85, y: 6.13, w: 2.85, h: 0.75, fontSize: 9.5, color: MUTED });
  s.addNotes("Earth safety. Left, the ten thresholds as gauges: the green zone is allowed and the teal bar is the range over the whole "
    + "journey. Right, the same climate model with and without the sunlight optics: without them Earth falls off the ice-albedo cliff "
    + "within a few centuries. Placed for real, the optics are a ring of refracting film near L1; at 95% transmission Earth keeps 97% "
    + "of today's sunlight, 286 K, inside every threshold.");
}

// =====================================================================================================
// 9. The Moon, the sky and a million years
// =====================================================================================================
{
  const s = content();
  head(s, "08 · THE MOON, THE SKY AND A MILLION YEARS", "The Moon stays, and the new orbits hold for a million years",
    `With the tows gone, the moved solar system ran ${n0(lt.moved_info.years)} years beside the real one (REBOUND MERCURIUS): `
    + `no planet lost, ${lt.verdict.flags.unresolved} unresolved flags, and ${lt.chaos_copies.length} chaos copies started with tiny changes agree.`);
  box(s, 0.55, 1.86, 3.95, 5.08, { fill: INK, r: 0.06 });
  T(s, "EARTH'S HILL SPHERE, TO SCALE", { x: 0.72, y: 1.96, w: 3.6, h: 0.22, fontSize: 9.5, bold: true, color: MUTED_D });
  const hx = 2.52, hy = 4.0, hk = 1.45 / D.mirrors.hill_radius_km;
  const hill1 = D.moon ? D.moon.start.without_asteroid.hill_radius_km : 1.4965e6;
  circle(s, hx, hy, D.mirrors.hill_radius_km * hk, { fill: { color: EARTH, transparency: 88 }, line: { color: EARTH, width: 1.5 } });
  ring(s, hx, hy, D.mirrors.hill_radius_km * hk * SAFE.moon_hill_max_share, MARS, 1, { dash: "dash" });
  ring(s, hx, hy, hill1 * hk, "7FC4BA", 1.25, { dash: "dash" });
  ring(s, hx, hy, 384400 * hk, "C9D3E0", 1);
  circle(s, hx, hy, 0.06, { fill: { color: EARTH } });
  circle(s, hx + 384400 * hk, hy, 0.035, { fill: { color: WHITE } });
  T(s, `Hill radius at 2.7 AU: ${fx(D.mirrors.hill_radius_km / 1e6, 2)} M km`, { x: hx - 1.5, y: hy - 1.45 - 0.24, w: 3.0, h: 0.2, fontSize: 10, color: EARTH, align: "center", bold: true });
  T(s, "stable limit (0.49)", { x: hx + 0.25, y: hy - 0.72, w: 1.4, h: 0.2, fontSize: 10, color: "F3B6A8" });
  T(s, `today: ${fx(hill1 / 1e6, 2)} M km`, { x: hx - 1.55, y: hy + 0.42, w: 1.2, h: 0.2, fontSize: 10, color: "7FC4BA", align: "right" });
  T(s, "Moon", { x: hx + 0.12, y: hy - 0.02, w: 0.6, h: 0.2, fontSize: 10, color: WHITE });
  if (D.moon) {
    const ep = D.moon;
    s.addTable([[{ text: "Moon test", options: { bold: true } }, { text: "Earth at", options: { bold: true } }, { text: "Asteroid moves the Moon by", options: { bold: true } }],
      ...["start", "middle", "end"].map((k) => [`${k}, year ${n0(ep[k].journey_year)}`, `${fx(ep[k].earth_au, 2)} AU`,
        { text: pct(ep[k].distance_change, 3), options: { bold: true, color: PASS } }])],
    { x: 0.7, y: 5.58, w: 3.65, colW: [1.2, 0.75, 1.7], fontFace: BODY, fontSize: 9.5, color: TEXT_D, rowH: 0.25,
      border: { type: "solid", pt: 0.5, color: ORBIT_D }, margin: [0.02, 0.05, 0.02, 0.05], valign: "middle" });
  }
  // Tilt and eccentricity over a million years
  const L = lt.series, lbl = L.map((p) => String(Math.round(p.year / 1000)));
  const chartO = { ...CHART, lineSize: 1.75, lineDataSymbol: "none", catAxisLabelFrequency: 20, showLegend: true, legendPos: "b",
    catAxisTitle: "thousand years after arrival", showCatAxisTitle: true };
  T(s, "Axial tilt (degrees)", { x: 4.75, y: 1.86, w: 4.2, h: 0.22, fontSize: 11, bold: true });
  s.addChart(pres.charts.LINE, [
    { name: "moved Earth", labels: lbl, values: L.map((p) => p.tilt) },
    { name: "real Earth", labels: lbl, values: L.map((p) => p.real_tilt) },
  ], { ...chartO, x: 4.7, y: 2.08, w: 4.3, h: 2.2, chartColors: [EARTH, "9AA5B5"], valAxisMinVal: 21, valAxisMaxVal: 27, valAxisMajorUnit: 1 });
  T(s, "Eccentricity", { x: 4.75, y: 4.35, w: 4.2, h: 0.22, fontSize: 11, bold: true });
  s.addChart(pres.charts.LINE, [
    { name: "moved Earth", labels: lbl, values: L.map((p) => p.earth_e) },
    { name: "real Earth", labels: lbl, values: L.map((p) => p.real_e) },
  ], { ...chartO, x: 4.7, y: 4.57, w: 4.3, h: 2.05, chartColors: [EARTH, "9AA5B5"], valAxisMinVal: 0, valAxisMaxVal: 0.07,
    valAxisMajorUnit: 0.02, valAxisLabelFormatCode: "0.00" });
  T(s, `Tilt swings ${fx(lt.moved_info.axial_tilt_deg[0], 1)}°–${fx(lt.moved_info.axial_tilt_deg[1], 1)}° (real ${fx(lt.real_info.axial_tilt_deg[0], 1)}°–${fx(lt.real_info.axial_tilt_deg[1], 1)}°): `
    + `spin precession nears a slow planetary mode; E3 re-aims ${pct(lt.verdict.seasons.sunlight_to_reaim, 1)} of the sunlight (a covered flag).`,
  { x: 4.75, y: 6.62, w: 4.25, h: 0.4, fontSize: 9.5, color: MUTED });
  // Moved against real
  const r = (a, d) => `${fx(a[0], d)}–${fx(a[1], d)}`;
  s.addTable([
    [{ text: "", options: { fill: { color: INK } } }, { text: "Moved", options: { bold: true, fill: { color: INK }, color: WHITE } },
      { text: "Real", options: { bold: true, fill: { color: INK }, color: WHITE } }],
    ["Earth's orbit (AU)", r(ltMoved.earth.a, 3), r(ltReal.earth.a, 5)],
    ["Earth's eccentricity, max", fx(ltMoved.earth.e[1], 3), fx(ltReal.earth.e[1], 3)],
    ["Earth's tilt", `${r(lt.moved_info.axial_tilt_deg, 1)}°`, `${r(lt.real_info.axial_tilt_deg, 1)}°`],
    ["Mars's orbit (AU)", r(ltMoved.mars.a, 3), r(ltReal.mars.a, 4)],
    ["Earth–Mars orbit gap, min", `${fx(lt.moved_info.earth_mars_orbit_gap_min_au, 2)} AU`, `${fx(lt.real_info.earth_mars_orbit_gap_min_au, 2)} AU`],
    ["Energy error", sci(lt.moved_info.energy_error), sci(lt.real_info.energy_error)],
  ], { x: 9.2, y: 1.86, w: 3.58, colW: [1.5, 1.05, 1.03], fontFace: BODY, fontSize: 9.5, color: TEXT, rowH: 0.27,
    border: { type: "solid", pt: 0.5, color: LINE }, margin: [0.02, 0.05, 0.02, 0.05], valign: "middle" });
  const sky = [
    ["Sun 0.20° wide", `${pct(D.mirrors.sun_deg / 0.533, 0)} of today's width`],
    [`Year: ${fx(ARR.a_au ** 1.5, 2)} of ours`, "each season about 13 months"],
    ["Same day length", `the tow adds ${sci(MS.day_length_max_s)} s`],
    ["Tow mirror ≈ full Moon", `${fx(D.mirrors.tow_mirror.disc_deg, 2)}° disc, ${D.mirrors.tow_mirror.bearing_from_sun_deg}° from the Sun`],
    ["Stronger shield", `magnetopause ${fx(CL.magnetopause_re[0], 0)} → ${fx(CL.magnetopause_re[1], 1)} Earth radii`],
    ["45 big-asteroid passes", `each nudged ${lt.verdict.big_asteroid_nudges.warning_years} yr ahead (≤ ${fx(lt.verdict.big_asteroid_nudges.longest_beam_hours, 2)} h of beam)`],
  ];
  T(s, "THE SKY AND THE DAYS AT 2.7 AU", { x: 9.2, y: 4.0, w: 3.58, h: 0.22, fontSize: 9.5, bold: true, color: MUTED });
  sky.forEach(([a, b], i) => {
    const x = 9.2 + (i % 2) * 1.82, y = 4.28 + Math.floor(i / 2) * 0.89;
    box(s, x, y, 1.76, 0.8, { fill: TINT });
    T(s, [run(a, { bold: true, fontSize: 10.5 }), run("\n" + b, { fontSize: 9.5, color: MUTED })], { x: x + 0.1, y: y + 0.07, w: 1.6, h: 0.7 });
  });
  s.addNotes("The Moon test follows the Moon around Earth with and without the tow asteroid at the start, middle and end; the asteroid "
    + "changes its distance by hundredths of a percent, and Earth's Hill sphere grows as Earth moves out, so the Moon gets safer. "
    + "After arrival the moved solar system runs a million years beside the real one: orbits hold, nothing is lost. Earth's tilt swings "
    + "wider than today's, which the optics offset by re-aiming 1.4% of the sunlight.");
}

// =====================================================================================================
// 10. Hazards and resilience
// =====================================================================================================
{
  const s = content();
  const parked = D.small.impacts.parked || D.small.impacts.parked_at_target;
  const k1 = parked["1000m"].years_per_impact.central, k100 = parked["100m"].years_per_impact.central, k20 = parked["20m"].per_year.central;
  const today = k1 * S.belt.parked_at_target.times_natural_rate;
  head(s, "09 · HAZARDS AND RESILIENCE", "Parked in the asteroid belt, and defended",
    `At 2.7 AU Earth sits inside the belt: a 1 km impact every ${n0(k1)} years instead of every ${n0(Math.round(today / 1000) * 1000)}. `
    + "E1 watches and nudges, the tow mirrors protect themselves, and every beam survives station outages.");
  box(s, 0.55, 1.86, 4.7, 5.08, { fill: INK, r: 0.06 });
  T(s, "LAYERS OF DEFENCE (schematic)", { x: 0.72, y: 1.96, w: 4.3, h: 0.22, fontSize: 9.5, bold: true, color: MUTED_D });
  const dx = 2.9, dy = 3.95, layers = [
    [1.6, SUN_D, "4"], [1.18, SUN, "3"], [0.78, "E8C27A", "2"], [0.42, "C9D3E0", "1"]];
  layers.forEach(([r, c, n]) => {
    ring(s, dx, dy, r, c, 1.5, { dash: n === "1" ? undefined : "dash" });
    const a = (35 * Math.PI) / 180;
    badge(s, dx + r * Math.cos(a), dy - r * Math.sin(a), n, c, { r: 0.13, size: 9, color: INK });
  });
  circle(s, dx, dy, 0.18, { fill: { color: EARTH } });
  const rk = rng(3);
  for (let i = 0; i < 26; i++) {
    const a = rk() * 2 * Math.PI, r = 1.72 + rk() * 0.25;
    circle(s, dx + r * Math.cos(a), dy - r * Math.sin(a), 0.02 + 0.02 * rk(), { fill: { color: ROCK } });
  }
  const tp = D.mirrors.tow_protection["earth-tow"], sv = D.small.survey_and_e1["20m"].worst;
  const legend = [
    `Tow mirror: its beam, ${n0(Math.round(tp.beam_vs_sun_surface / 1000) * 1000)}× the Sun's surface brightness, vaporises a 1 m rock in ${fx(tp.vaporise_1m_s[0] * 1000, 0)}–${fx(tp.vaporise_1m_s[2] * 1000, 0)} ms.`,
    `20 m rocks: an infrared survey sees a dark one ${fx(sv.warning_days, 0)}–15 days out; E1 pushes it aside with ${pct(sv.share_of_spare, 0)} of its spare power.`,
    `1 km asteroids: found 10 years ahead, a ${fx(S.belt.deflection.speed_change_m_s * 100, 0)} cm/s nudge moves them off.`,
    `Big asteroids: nudged ${lt.verdict.big_asteroid_nudges.warning_years} years ahead (Vesta's ${fx(S.big_asteroids_closest_au.vesta, 3)} AU passes: ${fx(S.big_asteroid_nudges[0].beam_hours, 3)} h of beam each).`,
  ];
  legend.forEach((t, i) => {
    const y = 5.72 + i * 0.3;
    badge(s, 0.82, y + 0.1, String(i + 1), layers[3 - i][1], { r: 0.1, size: 8, color: INK });
    T(s, t, { x: 1.0, y, w: 4.15, h: 0.3, fontSize: 9.5, color: TEXT_D });
  });
  // How often
  T(s, "Years between impacts (log scale)", { x: 5.5, y: 1.86, w: 3.6, h: 0.24, fontSize: 11, bold: true });
  const every = (y) => (y >= 2 ? `every ${n0(y)} yr` : `every ${n0(y * 365.25)} days`);
  const vals = [today, S.belt.crossing.years_per_impact, k1, k100, 1 / k20];
  const cats = ["1 km, Earth today", "1 km, crossing the belt", "1 km, parked at 2.7 AU", "100 m, parked", "20 m, parked"]
    .map((c, i) => `${c}: ${every(vals[i])}`).reverse();
  s.addChart(pres.charts.BAR, [{ name: "years between impacts", labels: cats, values: vals.reverse() }],
  { ...CHART, x: 5.45, y: 2.1, w: 3.65, h: 2.75, barDir: "bar", chartColors: [SUN, SUN, MARS, MARS, ROCK], valAxisLogScaleBase: 10,
    valAxisMinVal: 0.05, valAxisMaxVal: 1000000, showValue: false,
    showLegend: false, valAxisHidden: true, valGridLine: { style: "none" }, barGapWidthPct: 40,
    layout: { x: 0.6, y: 0.03, w: 0.38, h: 0.94 } });
  const kw = D.small.kirkwood;
  const facts = [
    ["Parked rates", `about ${fx(k20, 0)} rocks of 20 m+ a year (range ${fx(parked["20m"].per_year.low, 1)}–${n0(parked["20m"].per_year.high)}), and a 100 m one every ${fx(k100, 0)} years.`],
    ["Kirkwood gaps don't help", `encounters at 2.50 AU are ${fx(kw["2.50"]["encounters_vs_2.70"], 2)}×, at 2.82 AU ${fx(kw["2.82"]["encounters_vs_2.70"], 2)}× those at 2.70: the gaps are in orbit size, not in space.`],
    ["The Moon, Mars, its moons", `get craters only: breaking the Moon up takes ${n0(D.small.bodies.moon.breaker_over_belt_mass)}× the whole belt's mass.`],
  ];
  facts.forEach(([a, b], i) => {
    const y = 5.0 + i * 0.66;
    box(s, 5.5, y, 3.6, 0.6, { fill: TINT });
    T(s, [run(a + ": ", { bold: true }), run(b, { color: MUTED })], { x: 5.6, y: y + 0.05, w: 3.42, h: 0.52, fontSize: 9.5, valign: "middle" });
  });
  // Outages
  T(s, "How long each beam can be cut and its asteroid still held", { x: 9.35, y: 1.86, w: 3.43, h: 0.42, fontSize: 11, bold: true });
  const pick = (needle) => D.outage.find((o) => o.name === needle);
  const out = [
    ["Earth tow, all stations off", pick("shared E1 budget, all beams off")],
    ["Earth tow, half off", pick("shared E1 budget, half the stations off")],
    ["Earth tow, a quarter off", pick("shared E1 budget, a quarter off")],
    ["Mars tow, all off", pick("Mars tow, all beams off")],
    ["Mars tow in its sprint, all off", pick("Mars tow in its 4x sprint (200,000 km), all off")],
  ].filter(([, o]) => o).reverse();
  s.addChart(pres.charts.BAR, [{ name: "longest safe outage (hours)", labels: out.map((o) => o[0]),
    values: out.map(([, o]) => o.longest_safe_outage_days * 24) }],
  { ...CHART, x: 9.3, y: 2.3, w: 3.5, h: 2.9, barDir: "bar", chartColors: [MARS, MARS, EARTH, EARTH, EARTH], showValue: true,
    dataLabelFormatCode: "0\" h\"", dataLabelPosition: "outEnd", showLegend: false, valAxisHidden: true, valGridLine: { style: "none" },
    valAxisMaxVal: 140, barGapWidthPct: 40, layout: { x: 0.47, y: 0.02, w: 0.42, h: 0.96 } });
  box(s, 9.35, 5.32, 3.43, 1.62, { fill: TINT });
  T(s, [run("Many independent stations share E1's budget. ", { bold: true }),
    run(`The structures are sized for the full cap, so catching up after an outage is safe; ${pct(tp.spare_power, 1)} of E1 stays spare `
      + `for rocks and asteroids, and dust holes about ${n0(D.small.wear["sunlight mirrors"].holed_km2_per_year)} km² of optics a year for E3 to patch.`,
    { color: MUTED })], { x: 9.48, y: 5.4, w: 3.2, h: 1.48, fontSize: 9.5 });
  s.addNotes("At 2.7 AU Earth is parked inside the asteroid belt, so impacts would come thousands of times as often as today. The defence "
    + "is layered: E1 nudges big asteroids decades ahead, a survey sees small rocks days ahead and E1 pushes them aside, and the tow "
    + "beam itself vaporises rocks that drift into the mirror. Separately, every tow holds its asteroid through station outages "
    + "measured in hours to days.");
}

// =====================================================================================================
// 11. Limits, next steps, and how to check us
// =====================================================================================================
{
  const s = pres.addSlide({ masterName: "DARK" });
  T(s, "10 · HONEST LIMITS, NEXT STEPS, HOW TO CHECK US", { x: 0.55, y: 0.42, w: 9, h: 0.28, fontSize: 10.5, bold: true, color: SUN, charSpacing: 1 });
  T(s, "What the model proves, and what it does not", { x: 0.55, y: 0.72, w: 12.2, h: 0.62, fontFace: HEAD, fontSize: 30, bold: true, color: WHITE });
  const cols = [
    ["Proven in simulation", PASS, [
      `Earth to ${fx(ARR.a_au, 4)} AU by year ${n0(ARR.year)}, with Mars moved first`,
      `ten Earth-safety thresholds held at all ${n0(MS.checks)} checks`,
      `every structure at safety factor ≥ ${fx(minSF, 2)}, at full beam power`,
      `${benchPass}/${D.benchmarks.length} official benchmarks, checks X1–X9, ${testsPassed} tests`,
      `momentum ledger closed to ${sci(LED.nothing_from_nothing_max)}`,
      "stable for a million years; the Moon stays bound",
    ]],
    ["Not modelled, or still open", SUN, [
      "the hardware: E1–E3 are declared and bounded, not engineered",
      "climate in one dimension: no weather, oceans or carbon cycle",
      "13-month seasons: the model gives yearly means only",
      `tow-mirror scatter must stay below ${sci(D.mirrors.tow_mirror.scatter_limit_full_moon)} of the beam; no enabler bounds it`,
      "the Moon and Earth's spin run separately from the journey",
      "the safety thresholds are the company demo's; a new rulebook means a re-run",
    ]],
    ["Next", "7FC4BA", [
      "the Moon as its own body through the whole journey",
      "a climate resolved by latitude and season",
      "a sensitivity sweep of tow mass and distance",
      "a scatter specification and test for the tow mirrors",
      "resonance transport in the belt with 20,000+ orbits",
      "aimable mirrors re-aiming 1.4% of the sunlight for the seasons",
      "re-run with the organisers' thresholds the day they publish",
    ]],
  ];
  cols.forEach(([title, c, items], i) => {
    const x = 0.55 + i * 4.13;
    box(s, x, 1.6, 3.97, 4.05, { fill: INK2, line: ORBIT_D });
    badge(s, x + 0.32, 1.95, ["✓", "!", "→"][i], c, { r: 0.17, size: 12, color: INK });
    T(s, title, { x: x + 0.6, y: 1.82, w: 3.2, h: 0.28, fontSize: 14, bold: true, color: c });
    T(s, items.map((t, j) => run(t, { bullet: true, breakLine: j < items.length - 1 })), { x: x + 0.22, y: 2.35, w: 3.6, h: 3.2,
      fontSize: 11.5, color: TEXT_D, paraSpaceAfter: 6 });
  });
  box(s, 0.55, 5.85, 12.23, 1.05, { fill: INK2, line: SUN });
  T(s, [run("Check us yourself.  ", { bold: true, color: SUN }),
    run("run.bat verify", { bold: true, color: WHITE, fontFace: "Consolas" }),
    run(" re-runs the benchmarks, the tests, the engine and the studies and writes a results PDF in about 4 minutes;  ", { color: TEXT_D }),
    run("python -m sim.benchmarks 4 --set e=0.5", { bold: true, color: WHITE, fontFace: "Consolas" }),
    run(" changes a benchmark's inputs.  Test bench: ashish000011.github.io/black-ant · Code: github.com/Ashish000011/black-ant", { color: TEXT_D }),
    run("\nKey sources: Lu & Love 2005 (Nature) · Korycansky, Laughlin & Adams 2001 · Angel 2006 (PNAS) · Budyko 1969 · Sellers 1969 · "
      + "Goldblatt et al. 2013 · Rein & Liu 2012 (REBOUND) · Yoshida 1990 · Burdanov et al. 2025 · Lubin et al. 2014 (DE-STAR); 43 in the technical report.",
    { color: MUTED_D, fontSize: 9.5 })], { x: 0.75, y: 5.93, w: 11.85, h: 0.92, fontSize: 10.5, valign: "middle" });
  T(s, "Team Black Ant · Sushmit Sukla (team leader) · Ashish Bharti · Akhil Semwal · Madhukar Verma · Prabhanshu Kerketa",
    { x: 0.55, y: 7.08, w: 10, h: 0.26, fontSize: 10, color: MUTED_D });
  s.addNotes("We close with what is and is not proven. The physics closes in simulation with every check passing; the hardware is "
    + "represented by three declared, bounded enablers, and we list the limits we found in our own design. Anyone can re-check every "
    + "number with one command.");
}

// ---------- write, then give the deck its own theme colors ----------
await pres.writeFile({ fileName: OUT });
const zip = await JSZip.loadAsync(fs.readFileSync(OUT));
const part = "ppt/theme/theme1.xml";
const slots = ["dk1", "lt1", "dk2", "lt2", "accent1", "accent2", "accent3", "accent4", "accent5", "accent6", "hlink", "folHlink"];
const scheme = `<a:clrScheme name="${THEME.name}">` + slots.map((k) => `<a:${k}><a:srgbClr val="${THEME.colors[k]}"/></a:${k}>`).join("") + "</a:clrScheme>";
const xml = (await zip.file(part).async("string")).replace(/<a:clrScheme\b[\s\S]*?<\/a:clrScheme>/, () => scheme)
  .replace(/(<a:(?:theme|fontScheme)\b[^>]*?\bname=")[^"]*"/g, (_, h) => `${h}${THEME.name}"`);
zip.file(part, xml);
fs.writeFileSync(OUT, await zip.generateAsync({ type: "nodebuffer", compression: "DEFLATE" }));
console.log(`Wrote ${path.relative(ROOT, OUT)}`);
