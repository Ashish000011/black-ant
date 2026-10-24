// Coupled run of the Earth tow.
// Each tow is a real asteroid body. A controller sets the beam force that holds it on its spot,
// the beam's power and mirror angle are derived from that force, and a ledger books every push:
// the asteroid, the station's recoil and the bounced light.
//
// Usage: node coupled_run.mjs [years] [dtDays] [--no-mars-tow] [--quiet]
// Writes out/summary.json and out/run.json (one frame per 10 years).

import { mkdirSync, writeFileSync } from "node:fs";

const G = 6.674e-11, C_LIGHT = 2.99792458e8, AU = 1.495978707e11, DAY = 86400, YR = 3.15576e7;
const GM_SUN = 1.32712440018e20;

const maxYears = Number(process.argv[2] ?? 10000);
const dt = Number(process.argv[3] ?? 0.5) * DAY;
const marsTow = !process.argv.includes("--no-mars-tow");
const quiet = process.argv.includes("--quiet");

// Bodies: circular, flat orbits at their J2000 mean longitudes. Earth carries the Moon's mass.
const PLANETS = [
  { name: "venus", m: 4.8675e24, a: 0.72333, L: 181.97973 },
  { name: "earth", m: 5.9722e24 + 7.342e22, a: 1.0, L: 100.46435 },
  { name: "mars", m: 6.4171e23, a: 1.52368, L: 355.45332 },
  { name: "jupiter", m: 1.89813e27, a: 5.2026, L: 34.39644 },
  { name: "saturn", m: 5.6834e26, a: 9.55491, L: 49.95424 },
];
const SUN = 0, EARTH = 2, MARS = 3, JUPITER = 4;
// Tows: the asteroid's mass sets the target's acceleration (G x mass / distance^2); the beam must
// hold the asteroid against the target's pull. Mars gets the same acceleration as Earth.
const TOWS = [
  { name: "earth-tow", target: EARTH, mass: 3.97e20, d: 6.371e8, stopAU: 2.7, maxP: 8.5e25 },
  ...(marsTow ? [{ name: "mars-tow", target: MARS, mass: 3.97e20 * (1.0e8 / 6.371e8) ** 2, d: 1.0e8, stopAU: 3.1, maxP: 1.5e25 }] : []),
];
// Each tow's power cap (maxP) keeps the total under the E1 limit even while a tow recovers from a pause.
const BEAM_LIMIT_W = 1.0e26; // enabler E1: total beam power
const BEAM_CLEARANCE_M = 4.2e8; // beams stay 420,000 km from Earth, beyond the Moon's farthest point (406,700 km)
const ROUTE_ANGLES_DEG = [0, 5, -5, 10, -10, 15, -15, 20, -20, 30, -30]; // how far off the Sun line the light may arrive

const names = ["sun", ...PLANETS.map((p) => p.name), ...TOWS.map((t) => t.name)];
const N = names.length;
TOWS.forEach((t, i) => { t.idx = 1 + PLANETS.length + i; t.active = true; t.beam = { fx: 0, fy: 0, P: 0, inx: 0, iny: 0, outx: 0, outy: 0 }; t.blocked = 0; t.paused = 0; t.capped = 0; t.rerouted = 0; });

const m = new Float64Array(N), x = new Float64Array(N), y = new Float64Array(N);
const vx = new Float64Array(N), vy = new Float64Array(N), ax = new Float64Array(N), ay = new Float64Array(N);
m[SUN] = GM_SUN / G;
PLANETS.forEach((p, i) => {
  const k = i + 1, L = (p.L * Math.PI) / 180, r = p.a * AU, v = Math.sqrt((G * (m[SUN] + p.m)) / r);
  m[k] = p.m; x[k] = r * Math.cos(L); y[k] = r * Math.sin(L);
  vx[k] = -v * Math.sin(L); vy[k] = v * Math.cos(L);
});

// A tow's spot: distance d from its target, 45 degrees between "ahead" and "away from the Sun".
function spot(t) {
  const j = t.target;
  const rx = x[j] - x[SUN], ry = y[j] - y[SUN], rvx = vx[j] - vx[SUN], rvy = vy[j] - vy[SUN];
  const r = Math.hypot(rx, ry), hx = rx / r, hy = ry / r, tx = -hy, ty = hx;
  const w = (rx * rvy - ry * rvx) / (r * r), k = t.d * Math.SQRT1_2;
  return {
    px: x[j] + k * (hx + tx), py: y[j] + k * (hy + ty),
    vx: vx[j] + k * w * (tx - hx), vy: vy[j] + k * w * (ty - hy),
    ax: ax[j] - k * w * w * (hx + tx), ay: ay[j] - k * w * w * (hy + ty),
  };
}
for (const t of TOWS) { const s = spot(t); m[t.idx] = t.mass; x[t.idx] = s.px; y[t.idx] = s.py; vx[t.idx] = s.vx; vy[t.idx] = s.vy; }

// Move to the barycentre so the total momentum starts at zero.
{
  let M = 0, cx = 0, cy = 0, px = 0, py = 0;
  for (let i = 0; i < N; i++) { M += m[i]; cx += m[i] * x[i]; cy += m[i] * y[i]; px += m[i] * vx[i]; py += m[i] * vy[i]; }
  for (let i = 0; i < N; i++) { x[i] -= cx / M; y[i] -= cy / M; vx[i] -= px / M; vy[i] -= py / M; }
}

function gravity() {
  ax.fill(0); ay.fill(0);
  for (let i = 0; i < N; i++) for (let j = i + 1; j < N; j++) {
    if (m[i] === 0 && m[j] === 0) continue;
    const dx = x[j] - x[i], dy = y[j] - y[i], r2 = dx * dx + dy * dy, inv = 1 / (r2 * Math.sqrt(r2));
    const fi = G * m[j] * inv, fj = G * m[i] * inv;
    ax[i] += fi * dx; ay[i] += fi * dy; ax[j] -= fj * dx; ay[j] -= fj * dy;
  }
}

// Controller: feed-forward to follow the spot, plus a gentle correction for drift.
// Light arrives travelling straight out from the Sun; a mirror bouncing it to direction "out"
// pushes with (P/c)(in - out). The power that gives force f is P = |f|^2 c / (2 in.f), which
// needs in.f > 0: light from the Sun can never push an asteroid back toward the Sun.
const WC = (2 * Math.PI) / (10 * DAY), KP = WC * WC, KD = 2 * WC;
function beamForces() {
  for (const t of TOWS) {
    const b = t.beam, a = t.idx;
    if (!t.active) { b.fx = b.fy = b.P = 0; continue; }
    const s = spot(t);
    const fx0 = m[a] * (s.ax - ax[a] + KP * (s.px - x[a]) + KD * (s.vx - vx[a]));
    const fy0 = m[a] * (s.ay - ay[a] + KP * (s.py - y[a]) + KD * (s.vy - vy[a]));
    const rx = x[a] - x[SUN], ry = y[a] - y[SUN], r = Math.hypot(rx, ry), hx = rx / r, hy = ry / r;
    // Normally the light comes straight out from the Sun. If that beam would pass too close to
    // Earth, collectors slightly off the line fire instead, so the light arrives at an angle.
    let chosen = null;
    for (const deg of ROUTE_ANGLES_DEG) {
      const c = Math.cos((deg * Math.PI) / 180), sn = Math.sin((deg * Math.PI) / 180);
      const inx = hx * c - hy * sn, iny = hx * sn + hy * c;
      let fx = fx0, fy = fy0, along = inx * fx + iny * fy;
      if (along <= 1e-6 * Math.hypot(fx, fy)) continue; // light can't pull the asteroid toward its source
      let P = ((fx * fx + fy * fy) * C_LIGHT) / (2 * along), capped = false;
      if (P > t.maxP) { const k = t.maxP / P; fx *= k; fy *= k; P = t.maxP; capped = true; } // power scales with force
      const outx = inx - (fx * C_LIGHT) / P, outy = iny - (fy * C_LIGHT) / P, ol = Math.hypot(outx, outy);
      // Safety rule: no beam passes closer to Earth than just beyond the Moon's farthest point.
      const clearIn = rayDist(x[EARTH], y[EARTH], x[a], y[a], -inx, -iny, r);
      const clearOut = rayDist(x[EARTH], y[EARTH], x[a], y[a], outx / ol, outy / ol);
      if (Math.min(clearIn, clearOut) < BEAM_CLEARANCE_M) continue;
      chosen = { fx, fy, P, inx, iny, outx, outy, deg, capped };
      break;
    }
    if (!chosen) { t.paused++; b.fx = b.fy = b.P = 0; continue; }
    if (chosen.deg !== 0) t.rerouted++;
    if (chosen.capped) t.capped++;
    Object.assign(b, chosen);
  }
}

// Ledger accounts (momentum in kg m/s, energy in J).
const led = { stationPx: 0, stationPy: 0, lightPx: 0, lightPy: 0, departedPx: 0, departedPy: 0, work: 0, departedE: 0 };
function kick(h) {
  for (let i = 0; i < N; i++) { vx[i] += ax[i] * h; vy[i] += ay[i] * h; }
  for (const t of TOWS) {
    const b = t.beam, a = t.idx;
    if (!t.active || b.P === 0) continue;
    const dvx = (b.fx / m[a]) * h, dvy = (b.fy / m[a]) * h;
    led.work += (b.fx * (vx[a] + 0.5 * dvx) + b.fy * (vy[a] + 0.5 * dvy)) * h;
    vx[a] += dvx; vy[a] += dvy;
    const k = (b.P / C_LIGHT) * h;
    led.stationPx -= k * b.inx; led.stationPy -= k * b.iny; // station recoil when it fires
    led.lightPx += k * b.outx; led.lightPy += k * b.outy; // momentum carried off by the bounced light
  }
}
function energy() {
  let E = 0;
  for (let i = 0; i < N; i++) {
    if (m[i] === 0) continue;
    E += 0.5 * m[i] * (vx[i] * vx[i] + vy[i] * vy[i]);
    for (let j = i + 1; j < N; j++) if (m[j] !== 0) E -= (G * m[i] * m[j]) / Math.hypot(x[j] - x[i], y[j] - y[i]);
  }
  return E;
}
function momentum() {
  let px = led.stationPx + led.lightPx + led.departedPx, py = led.stationPy + led.lightPy + led.departedPy, scale = 0;
  for (let i = 0; i < N; i++) { px += m[i] * vx[i]; py += m[i] * vy[i]; scale += m[i] * Math.hypot(vx[i], vy[i]); }
  return { err: Math.hypot(px, py), scale };
}
function orbit(j) {
  const rx = x[j] - x[SUN], ry = y[j] - y[SUN], wx = vx[j] - vx[SUN], wy = vy[j] - vy[SUN];
  const mu = G * (m[SUN] + m[j]), r = Math.hypot(rx, ry), v2 = wx * wx + wy * wy;
  const a = 1 / (2 / r - v2 / mu), rv = rx * wx + ry * wy;
  const ex = ((v2 - mu / r) * rx - rv * wx) / mu, ey = ((v2 - mu / r) * ry - rv * wy) / mu;
  return { a: a / AU, e: Math.hypot(ex, ey), r: r / AU, v: Math.sqrt(v2) };
}
// The asteroid of a finished tow is sent away; we take it out of the run and book what it carried.
function sendAway(t) {
  const a = t.idx, Eb = energy();
  led.departedPx += m[a] * vx[a]; led.departedPy += m[a] * vy[a];
  m[a] = 0; t.active = false; t.beam.P = 0;
  led.departedE += Eb - energy();
}
// Closest distance from point q to the ray starting at o along unit u (optionally capped in length).
function rayDist(qx, qy, ox, oy, ux, uy, maxLen = Infinity) {
  const s = Math.max(0, Math.min(maxLen, (qx - ox) * ux + (qy - oy) * uy));
  return Math.hypot(qx - ox - s * ux, qy - oy - s * uy);
}

// ---- Run ----
gravity(); beamForces();
const E0 = energy();
const stats = {
  totalBeamMaxW: 0, overLimitChecks: 0, marsMin: Infinity, marsMinYear: 0, jupiterMinAU: Infinity, energyErrMax: 0, momErrMax: 0,
  tows: Object.fromEntries(TOWS.map((t) => [t.name, { beamMinW: Infinity, beamMaxW: 0, angleMinDeg: 180, angleMaxDeg: 0, spotErrMaxKm: 0, clearEarthInKm: Infinity, clearEarthOutKm: Infinity, arrival: null }])),
};
const frames = [];
const steps = Math.round((maxYears * YR) / dt), CHECK = 200, FRAME = Math.round((10 * YR) / dt);
const t0 = Date.now();
let lastE = { dE: 0, err: 0 };
for (let n = 0; n <= steps; n++) {
  const yrs = (n * dt) / YR;
  if (n % CHECK === 0) {
    let total = 0;
    for (const t of TOWS) {
      if (!t.active) continue;
      const st = stats.tows[t.name], b = t.beam, a = t.idx, s = spot(t);
      total += b.P;
      if (yrs > 1) st.spotErrMaxKm = Math.max(st.spotErrMaxKm, Math.hypot(s.px - x[a], s.py - y[a]) / 1e3);
      if (b.P > 0) {
        const ang = (Math.acos((b.inx * b.fx + b.iny * b.fy) / Math.hypot(b.fx, b.fy)) * 180) / Math.PI;
        st.angleMinDeg = Math.min(st.angleMinDeg, ang); st.angleMaxDeg = Math.max(st.angleMaxDeg, ang);
        st.beamMinW = Math.min(st.beamMinW, b.P); st.beamMaxW = Math.max(st.beamMaxW, b.P);
        const ol = Math.hypot(b.outx, b.outy), rSA = Math.hypot(x[a] - x[SUN], y[a] - y[SUN]);
        st.clearEarthOutKm = Math.min(st.clearEarthOutKm, rayDist(x[EARTH], y[EARTH], x[a], y[a], b.outx / ol, b.outy / ol) / 1e3);
        st.clearEarthInKm = Math.min(st.clearEarthInKm, rayDist(x[EARTH], y[EARTH], x[a], y[a], -b.inx, -b.iny, rSA) / 1e3);
      }
      const orb = orbit(t.target);
      if (orb.a >= t.stopAU) {
        st.arrival = { year: +yrs.toFixed(1), a: +orb.a.toFixed(4), e: +orb.e.toFixed(4), speedKms: +(orb.v / 1000).toFixed(2) };
        sendAway(t);
      }
    }
    stats.totalBeamMaxW = Math.max(stats.totalBeamMaxW, total);
    if (total > BEAM_LIMIT_W) stats.overLimitChecks++;
    const dE = energy() - E0 + led.departedE, err = Math.abs(dE - led.work) / Math.abs(E0);
    lastE = { dE, err };
    if (yrs > 1) stats.energyErrMax = Math.max(stats.energyErrMax, err);
    const mom = momentum(); stats.momErrMax = Math.max(stats.momErrMax, mom.err / mom.scale);
    stats.jupiterMinAU = Math.min(stats.jupiterMinAU, Math.hypot(x[EARTH] - x[JUPITER], y[EARTH] - y[JUPITER]) / AU);
    if (n % FRAME < CHECK) {
      const rel = (i) => [+((x[i] - x[SUN]) / AU).toFixed(6), +((y[i] - y[SUN]) / AU).toFixed(6)];
      const oe = orbit(EARTH), om = orbit(MARS);
      frames.push({ t: +yrs.toFixed(1), pos: { earth: rel(EARTH), mars: rel(MARS), jupiter: rel(JUPITER), asteroid: rel(TOWS[0].idx) },
        earth_orbit_au: +oe.a.toFixed(5), earth_eccentricity: +oe.e.toFixed(5), mars_orbit_au: +om.a.toFixed(5),
        beam_power_w: TOWS.reduce((s, t) => s + (t.active ? t.beam.P : 0), 0), energy_error: err, momentum_error: mom.err / mom.scale,
        earth_tow_active: TOWS[0].active });
    }
    if (!TOWS[0].active && yrs > stats.tows["earth-tow"].arrival.year + 200) break; // 200 years after arrival
  }
  const dm = Math.hypot(x[EARTH] - x[MARS], y[EARTH] - y[MARS]);
  if (dm < stats.marsMin) { stats.marsMin = dm; stats.marsMinYear = yrs; }
  // Leapfrog: kick, drift, kick.
  kick(dt / 2);
  for (let i = 0; i < N; i++) { x[i] += vx[i] * dt; y[i] += vy[i] * dt; }
  gravity(); beamForces();
  kick(dt / 2);
}

const oE = orbit(EARTH), oM = orbit(MARS);
const summary = {
  settings: { years: maxYears, dtDays: dt / DAY, marsTow, bodies: names, beamLimitW: BEAM_LIMIT_W,
    controller: "feed-forward plus 10-day correction", model: "flat circular orbits at J2000 longitudes; Earth carries the Moon's mass",
    tows: TOWS.map((t) => ({ name: t.name, asteroidMassKg: t.mass, distanceKm: t.d / 1e3, stopAU: t.stopAU })) },
  tows: Object.fromEntries(TOWS.map((t) => [t.name, { ...stats.tows[t.name], beamOffDays: +(t.paused * dt / 2 / DAY).toFixed(1), reroutedDays: +(t.rerouted * dt / 2 / DAY).toFixed(1), powerCappedDays: +(t.capped * dt / 2 / DAY).toFixed(1) }])),
  totalBeamMaxW: stats.totalBeamMaxW, overLimitChecks: stats.overLimitChecks,
  stationRecoilMaxN: stats.totalBeamMaxW / C_LIGHT,
  marsClosestAU: { distance: +(stats.marsMin / AU).toFixed(5), year: +stats.marsMinYear.toFixed(1) },
  jupiterClosestAU: +stats.jupiterMinAU.toFixed(3),
  endState: { year: +((frames.at(-1) ?? { t: 0 }).t), earth: { a: +oE.a.toFixed(4), e: +oE.e.toFixed(4) }, mars: { a: +oM.a.toFixed(4), e: +oM.e.toFixed(4) } },
  ledger: { energyErrorMaxOfTotal: stats.energyErrMax, workJ: led.work, bodiesEnergyGainJ: lastE.dE,
    workMismatchShare: Math.abs(lastE.dE - led.work) / Math.max(led.work, 1), momentumErrorMax: stats.momErrMax },
  runSeconds: (Date.now() - t0) / 1000,
};
if (quiet) { console.log(JSON.stringify({ tows: summary.tows, marsClosestAU: summary.marsClosestAU, endState: summary.endState })); process.exit(0); }
mkdirSync(new URL("./out/", import.meta.url), { recursive: true });
writeFileSync(new URL("./out/summary.json", import.meta.url), JSON.stringify(summary, null, 2));
writeFileSync(new URL("./out/run.json", import.meta.url), JSON.stringify({ meta: { scenario: "tow", frame_every_years: 10, distance_unit: "AU", mars_tow: marsTow }, frames }));
console.log(JSON.stringify(summary, null, 2));
