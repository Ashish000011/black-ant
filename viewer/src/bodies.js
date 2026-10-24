// Where every major body is at year t. Earth, Mars and Jupiter come from the saved run. The run does not save the
// others, so Venus, Saturn, Uranus, Neptune and the big asteroids follow two-body Kepler orbits from their J2000
// values in config.yaml, ignoring the planets' pulls: their orbits are right, their place along them drifts over
// thousands of years.
import { positionAt, valueAt } from "./data.js";

const DEG = Math.PI / 180;
const DAYS_PER_YEAR = 365.25;
const TWO_PI = 2 * Math.PI;

const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
const norm = (a) => Math.hypot(...a);
const clamp1 = (x) => Math.max(-1, Math.min(1, x));

// The Sun's GM in AU^3/day^2, from the model's own constants.
export const muAuDay = (k) => (k.gm_sun * 86400 ** 2) / k.au_m ** 3;

// Orbital elements (the same names as config.yaml's planets) from a position (AU) and velocity (AU/day).
export function elementsFromState(r, v, mu) {
  const rn = norm(r), v2 = dot(v, v), rv = dot(r, v);
  const h = cross(r, v), hn = norm(h);
  const ev = r.map((x, i) => ((v2 - mu / rn) * x - rv * v[i]) / mu);
  const e = norm(ev);
  const a = 1 / (2 / rn - v2 / mu);
  const node = Math.atan2(h[0], -h[1]);
  const nodeDir = [Math.cos(node), Math.sin(node), 0];
  let w = Math.acos(clamp1(dot(nodeDir, ev) / e));
  if (ev[2] < 0) w = TWO_PI - w;
  let nu = Math.acos(clamp1(dot(ev, r) / (e * rn)));
  if (rv < 0) nu = TWO_PI - nu;
  const E = 2 * Math.atan(Math.sqrt((1 - e) / (1 + e)) * Math.tan(nu / 2));
  const M = E - e * Math.sin(E);
  return {
    a_au: a, e, i_deg: Math.acos(clamp1(h[2] / hn)) / DEG, node_longitude_deg: node / DEG,
    perihelion_longitude_deg: (node + w) / DEG, mean_longitude_deg: (node + w + M) / DEG,
  };
}

// Heliocentric ecliptic position (AU) `years` after J2000, following JPL's "Approximate Positions of the Planets".
export function keplerPosition(el, years, mu) {
  const a = el.a_au, e = el.e;
  const n = Math.sqrt(mu / a ** 3) * DAYS_PER_YEAR;
  const varpi = el.perihelion_longitude_deg * DEG, node = el.node_longitude_deg * DEG, inc = el.i_deg * DEG;
  const w = varpi - node;
  const M = ((el.mean_longitude_deg * DEG + n * years - varpi) % TWO_PI + TWO_PI) % TWO_PI;
  let E = M + e * Math.sin(M);
  for (let k = 0; k < 30; k++) {
    const dE = (E - e * Math.sin(E) - M) / (1 - e * Math.cos(E));
    E -= dE;
    if (Math.abs(dE) < 1e-12) break;
  }
  const xp = a * (Math.cos(E) - e), yp = a * Math.sqrt(1 - e * e) * Math.sin(E);
  const cw = Math.cos(w), sw = Math.sin(w), cO = Math.cos(node), sO = Math.sin(node), ci = Math.cos(inc), si = Math.sin(inc);
  return [
    (cw * cO - sw * sO * ci) * xp + (-sw * cO - cw * sO * ci) * yp,
    (cw * sO + sw * cO * ci) * xp + (-sw * sO + cw * cO * ci) * yp,
    sw * si * xp + cw * si * yp,
  ];
}

const COLORS = {
  sun: 0xffd27a, venus: 0xe6c27a, earth: 0x3987e5, mars: 0xd95926, jupiter: 0xc9a77c, saturn: 0xd8c48f,
  uranus: 0x8fd3d8, neptune: 0x5b7fe0,
};

// Every body the page shows: { id, name, kind, source ("run" or "kepler"), color, pos(t), orbitA(t) }.
export function allBodies(d) {
  const k = d.config.constants, mu = muAuDay(k);
  const cap = (s) => s[0].toUpperCase() + s.slice(1);
  const list = [{ id: "sun", name: "Sun", kind: "star", source: "fixed", color: COLORS.sun, pos: () => [0, 0, 0], orbitA: () => 0 }];
  for (const p of d.config.planets) {
    const base = { id: p.name, name: cap(p.name), kind: "planet", color: COLORS[p.name] ?? 0xaaaaaa };
    if (d.tracks[p.name]) {
      const key = `${p.name}_a`;
      list.push({ ...base, source: "run", pos: (t) => positionAt(d.tracks[p.name], t),
        orbitA: (t) => (d.series[key] ? valueAt(d, key, t) : p.a_au) });
    } else {
      const m = mu * (1 + p.mass_kg / k.m_sun);
      list.push({ ...base, source: "kepler", pos: (t) => keplerPosition(p, t, m), orbitA: () => p.a_au });
    }
  }
  for (const s of d.config.small_bodies) {
    const el = elementsFromState(s.pos_au, s.vel_au_per_day, mu);
    list.push({ id: s.name, name: cap(s.name), kind: "asteroid", source: "kepler", color: 0xa8a59c, el,
      pos: (t) => keplerPosition(el, t, mu), orbitA: () => el.a_au });
  }
  return list;
}

// Ecliptic longitude (deg, 0 to 360) of a heliocentric position.
export const longitude = (p) => ((Math.atan2(p[1], p[0]) / DEG) % 360 + 360) % 360;
