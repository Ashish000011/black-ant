// Loads the files sim/viewer_data.py writes and derives what the page plays: time series, milestones and
// smooth positions between the saved frames (one every 10 years).

const FILES = ["journey", "summary", "longterm", "benchmarks", "crossing", "outage", "parking", "structures", "config"];

export const AU_KM = 1.495978707e8;
export const G = 6.674e-11;
export const MASS = { earth: 6.04562e24, mars: 6.4171e23 };

export async function loadData() {
  const entries = await Promise.all(FILES.map(async (name) => {
    const res = await fetch(`./data/${name}.json`);
    if (!res.ok) throw new Error(`data/${name}.json: ${res.status}`);
    return [name, await res.json()];
  }));
  const d = Object.fromEntries(entries);
  derive(d);
  return d;
}

function firstTime(T, values, test) {
  const i = values.findIndex(test);
  return i < 0 ? null : T[i];
}

function derive(d) {
  const F = d.journey.frames;
  const T = F.map((f) => f.t);
  const s = {
    year: T,
    earth_a: F.map((f) => f.earth_a),
    earth_e: F.map((f) => f.earth_e),
    mars_a: F.map((f) => f.mars_a),
    beam_w: F.map((f) => f.beam_w),
    tow_km: F.map((f) => f.tow_km),
    energy_error: F.map((f) => f.energy_error),
    momentum_error: F.map((f) => f.momentum_error),
  };
  for (const k of Object.keys(F[0].safety)) s[k] = F.map((f) => f.safety[k]);

  const tows = d.summary.tows;
  const marsParks = tows["mars-tow"].arrival.year;
  const earthArrives = tows["earth-tow"].arrival.year;
  const marsSprint = sprintDistances(d, T, s.mars_a, marsParks);
  s.mars_tow_km = marsSprint;
  d.series = s;
  d.T = T;
  d.milestones = {
    start: 0,
    marsCrosses21: firstTime(T, s.mars_a, (a) => a >= 3.278),
    marsSprintStart: firstTime(T, s.mars_a, (a) => a >= 3.0),
    marsParks,
    beltEntry: firstTime(T, s.earth_a, (a) => a >= 2.1),
    earthArrives,
    end: T[T.length - 1],
  };
  d.tracks = {
    earth: track(F.map((f) => f.pos.earth), s.earth_a, T),
    mars: track(F.map((f) => f.pos.mars), s.mars_a, T),
    jupiter: track(F.map((f) => f.pos.jupiter), F.map(() => 5.2029), T),
  };
  d.towLocal = F.map((f) => toLocal(f.pos.earth, f.pos.asteroid));
}

// Mars's tow distance is not saved per frame; it follows the config rule: 400,000 km, moving to 200,000 km
// while Mars is between 3.0 and 3.5 AU, at the configured ramp (2,000 km per 100-day check).
function sprintDistances(d, T, marsA, parks) {
  const tow = d.config.tows.find((t) => t.name === "mars-tow");
  const rate = tow.sprint.ramp_km_per_check / (100 / 365.25);
  let dist = tow.distance_km;
  return T.map((t, i) => {
    if (t >= parks) return null;
    const goal = marsA[i] >= tow.sprint.from_au && marsA[i] < tow.sprint.to_au ? tow.sprint.distance_km : tow.distance_km;
    const dt = i ? T[i] - T[i - 1] : 0;
    const step = Math.min(Math.abs(goal - dist), rate * dt);
    dist += Math.sign(goal - dist) * step;
    return dist;
  });
}

// Polar track of a body with the angle unwrapped: between two frames 10 years apart the body makes many turns,
// so the turn count comes from Kepler's third law (P = a^1.5 years) and the frames themselves stay exact.
function track(pos, a, T) {
  const r = pos.map((p) => Math.hypot(p[0], p[1]));
  const th = pos.map((p) => Math.atan2(p[1], p[0]));
  const z = pos.map((p) => p[2]);
  const ang = [th[0]];
  for (let i = 1; i < pos.length; i++) {
    const dt = T[i] - T[i - 1];
    const turns = dt / Math.pow((a[i] + a[i - 1]) / 2, 1.5);
    let dth = th[i] - th[i - 1];
    dth = ((dth % (2 * Math.PI)) + 2 * Math.PI) % (2 * Math.PI);
    const k = Math.round(turns - dth / (2 * Math.PI));
    ang.push(ang[i - 1] + dth + 2 * Math.PI * Math.max(0, k));
  }
  return { r, ang, z, T, a };
}

export function frameIndex(T, t) {
  if (t <= T[0]) return [0, 0];
  if (t >= T[T.length - 1]) return [T.length - 2, 1];
  let lo = 0, hi = T.length - 1;
  while (hi - lo > 1) {
    const mid = (lo + hi) >> 1;
    if (T[mid] <= t) lo = mid; else hi = mid;
  }
  return [lo, (t - T[lo]) / (T[lo + 1] - T[lo])];
}

export function lerp(a, b, u) { return a + (b - a) * u; }

export function valueAt(d, key, t) {
  const [i, u] = frameIndex(d.T, t);
  const v = d.series[key];
  if (v[i] == null || v[i + 1] == null) return u < 0.5 ? v[i] : v[i + 1];
  return lerp(v[i], v[i + 1], u);
}

// Heliocentric ecliptic position (AU) of a body at year t.
export function positionAt(trk, t) {
  const [i, u] = frameIndex(trk.T, t);
  const r = lerp(trk.r[i], trk.r[i + 1], u);
  const ang = lerp(trk.ang[i], trk.ang[i + 1], u);
  return [r * Math.cos(ang), r * Math.sin(ang), lerp(trk.z[i], trk.z[i + 1], u)];
}

// A vector from Earth in Earth's own frame: [away from the Sun, ahead along the orbit, up], in km.
export function toLocal(earth, other) {
  const rel = other.map((c, k) => (c - earth[k]) * AU_KM);
  const rl = Math.hypot(earth[0], earth[1]);
  const out = [earth[0] / rl, earth[1] / rl];
  const ahead = [-out[1], out[0]];
  return [rel[0] * out[0] + rel[1] * out[1], rel[0] * ahead[0] + rel[1] * ahead[1], rel[2]];
}

export function towLocalAt(d, t) {
  const [i, u] = frameIndex(d.T, t);
  const a = d.towLocal[i], b = d.towLocal[i + 1];
  return [lerp(a[0], b[0], u), lerp(a[1], b[1], u), lerp(a[2], b[2], u)];
}

export function towActive(d, t, tow) {
  return tow === "earth" ? t < d.milestones.earthArrives : t < d.milestones.marsParks;
}
