// Needs playwright-core and Chrome: npm i --no-save playwright-core@1.49.1, then node scripts/video.mjs http://localhost:5173/ frames
// Without Chrome it uses Playwright's own Chromium (npx playwright-core install chromium-headless-shell).
// Renders the demo video frame by frame from the test bench in ?capture mode: node video.mjs <url> <frames dir>
import { chromium } from "playwright-core";
import { mkdirSync } from "node:fs";

const [,, base, dir, only] = process.argv;
const FPS = 25;
mkdirSync(dir, { recursive: true });

// Scrolls the floating Data panel to the section holding an element: "validity" (Results and checks, with the tabs)
// or "cmp-now" (Now against year 0).
const data = (id) => `{ const s = document.getElementById("${id}").closest(".bp"), box = s.closest(".fp-b");
  box.scrollTop += s.getBoundingClientRect().top - box.getBoundingClientRect().top - 4; }`;

// Each shot: seconds, what to set up, and per-frame changes (u runs 0 to 1 over the shot). Each view keeps its
// camera between shots, so the Earth tow and Octo-Earth shots set their own start angle. The Earth tow view stays
// 0 to 35 degrees from its first pose, turned the negative way: there the tow, the forces and their labels are clear
// of the floating panels and the caption, and do not crowd one another.
const shots = [
  { s: 10, setup: `bench.run('B'); bench.view('system'); bench.tab('Summary'); bench.time(0); ${data("validity")}`,
    each: (u) => `bench.orbit(0.12)`, caption: () => "Black Ant: towing Earth from 1 AU to 2.7 AU with a gravity tractor held in place by light" },
  { s: 20, setup: `bench.run('C'); bench.tab('Forces & momentum'); bench.time(1200); ${data("validity")}`,
    each: (u) => `bench.orbit(-0.05)`,
    caption: (u) => u < 0.5 ? "A 3.97 × 10²⁰ kg asteroid 637,100 km away pulls Earth with 3.95 × 10¹⁷ N"
      : "Earth pulls it back; light on its mirror holds it in place. No beam comes within 420,000 km of Earth" },
  { s: 40, setup: `bench.run('B'); bench.view('system'); bench.tab('Summary'); bench.time(0); ${data("cmp-now")}`,
    each: (u) => `bench.time(${8949} * ${u}); bench.orbit(0.05)`,
    caption: (u) => u < 0.38 ? "Mars is towed out first, and sprints across Jupiter’s 2:1 resonance"
      : u < 0.75 ? "Mars parks at 3.64 AU in year 5,168; then Earth crosses the asteroid belt"
        : "Earth arrives at 2.7006 AU in year 8,758, inside the 10,000-year limit" },
  { s: 15, setup: `bench.run('F'); bench.time(8000); bench.orbit(10); ${data("validity")}`, each: () => "bench.orbit(-0.05)",
    caption: () => "All ten Earth-safety thresholds hold: 288 K, liquid water on 82% of the surface, the Moon well inside Earth’s Hill sphere" },
  { s: 15, setup: `bench.run('C'); bench.tab('Forces & momentum'); bench.time(4000); bench.orbit(28.75); ${data("validity")}`,
    each: () => "bench.orbit(-0.05)",
    caption: () => "Every force booked with its reaction: the momentum ledger closes to 5.6 × 10⁻¹⁶ (limit 10⁻⁹)" },
  { s: 15, setup: `bench.run('I'); ${data("validity")}`, each: () => "bench.orbit(0.1)",
    caption: () => "A million years later the new orbits stay put, and nothing is thrown out" },
  { s: 15, setup: `bench.run('R'); bench.orbit(25); ${data("validity")}`, each: () => "bench.orbit(-0.24)",
    caption: () => "Octo-Earth, audited: its push lands on Earth’s own core (net 3.7 × 10⁻¹²), and a 12,000 km arm buckles past 471 km" },
  { s: 10, setup: `bench.run('A'); ${data("validity")}`, each: () => "bench.orbit(0.1)",
    caption: () => "All ten official benchmarks pass · github.com/Ashish000011/black-ant" },
];

// WebGL in software (SwiftShader), so it renders on machines without a GPU too.
const args = ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"];
const browser = await chromium.launch({ channel: "chrome", args }).catch(() => chromium.launch({ args }));
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
const errors = [];
page.on("pageerror", (e) => errors.push(e.message));
await page.goto(`${base}?capture=1`);
await page.waitForFunction(() => window.bench);
let n = 0;
const t0 = Date.now();
for (const [k, shot] of shots.entries()) {
  if (only && String(k) !== only) { n += shot.s * FPS; continue; }
  await page.evaluate(shot.setup);
  const frames = shot.s * FPS;
  for (let f = 0; f < frames; f++) {
    const u = f / (frames - 1);
    await page.evaluate(`${shot.each(u)}; bench.caption(${JSON.stringify(shot.caption(u))}); bench.frame(${n * 1000 / FPS})`);
    await page.screenshot({ path: `${dir}/${String(n).padStart(5, "0")}.jpg`, type: "jpeg", quality: 90 });
    n++;
  }
  console.log(`shot ${k} done: ${n} frames, ${((Date.now() - t0) / 1000).toFixed(0)} s`);
}
console.log(JSON.stringify({ frames: n, errors }));
await browser.close();
