// The Blender-style panels: the Scene tab (where every body is), the Model panel (experiments, time meters, the
// concept and enablers) and the Data panel (constants, Earth at the start, now against then, every result).
// Numbers marked ≈ are live estimates (estimates.js); the rest are read from the saved run.
import { fmt } from "./charts.js";
import { longitude } from "./bodies.js";
import { towActive, towLocalAt, valueAt } from "./data.js";
import { chip } from "./panels.js";

export const store = {
  get(k, fallback) { try { return localStorage.getItem(k) ?? fallback; } catch { return fallback; } },
  set(k, v) { try { localStorage.setItem(k, v); } catch { /* private window: keep defaults */ } },
};

const yr = (v) => Math.round(v).toLocaleString("en");
const pct = (v, digits = 1) => `${(v * 100).toFixed(digits)}%`;
const html = (s) => { const t = document.createElement("template"); t.innerHTML = s.trim(); return t.content.firstElementChild; };
const kv = (rows) => `<table class="kv"><tbody>${rows.map(([k, v]) => `<tr><td>${k}</td><td class="num">${v}</td></tr>`).join("")}</tbody></table>`;

// A collapsible panel, as Blender's: a header with a disclosure triangle; its open state is remembered.
export function subpanel(id, title, body, open = true) {
  const saved = store.get(`panel:${id}`, null);
  const isOpen = saved == null ? open : saved === "1";
  const el = html(`<div class="bp${isOpen ? "" : " closed"}"><button class="bp-h" aria-expanded="${isOpen}"><span class="tri" aria-hidden="true"></span>${title}</button><div class="bp-b"></div></div>`);
  const head = el.firstElementChild;
  head.onclick = () => {
    const nowOpen = el.classList.toggle("closed") === false;
    head.setAttribute("aria-expanded", nowOpen);
    store.set(`panel:${id}`, nowOpen ? "1" : "0");
  };
  el.lastElementChild.append(...[body].flat());
  return el;
}

// A slider drawn as Blender's: name and value on a filled bar. `toValue` / `fromValue` map the bar to the value
// (identity, or a log scale).
export function slider({ label, min = 0, max = 1000, step = 1, value, format, onInput, toValue = (x) => x, fromValue = (x) => x }) {
  const el = html(`<label class="bslider"><span class="fill"></span><span class="txt"><span class="k">${label}</span><span class="v"></span></span>
    <input type="range" min="${min}" max="${max}" step="${step}" aria-label="${label}"></label>`);
  const input = el.querySelector("input"), fill = el.querySelector(".fill"), v = el.querySelector(".v");
  // Show the value itself, not the bar's rounded position (a log slider's steps are coarse).
  const show = (val) => {
    fill.style.width = `${((Number(input.value) - min) / (max - min)) * 100}%`;
    v.textContent = format(val);
  };
  input.oninput = () => { const val = toValue(Number(input.value)); show(val); onInput(val); };
  el.set = (val) => { input.value = String(fromValue(val)); show(val); };
  el.set(value);
  return el;
}

// A meter: a label, a value and a bar. Against a limit it turns amber past 90% and red past 100%; a progress
// meter stays blue.
export function meter(label, limit = true) {
  const el = html(`<div class="meter"><div class="mk"><span>${label}</span><span class="mv"></span></div><div class="bar"><i></i></div></div>`);
  const bar = el.querySelector("i"), mv = el.querySelector(".mv");
  el.set = (frac, text) => {
    const f = Math.max(0, Math.min(1, frac));
    bar.style.width = `${f * 100}%`;
    bar.className = !limit ? "" : frac > 1 ? "over" : frac > 0.9 ? "near" : "";
    mv.innerHTML = text;
  };
  return el;
}

// ------------------------------------------------------------------ Scene tab (top left)
export function outliner(d, bodies, { focus, closeUp }) {
  const el = html(`<div><button class="fp-h" aria-expanded="true"><span class="tri" aria-hidden="true"></span>Scene<span class="fp-sub" id="ol-year"></span></button><div class="fp-b ol"></div></div>`);
  const root = el.querySelector(".ol"), head = el.querySelector(".fp-h");
  const open = store.get("panel:outliner", "1") === "1";
  head.setAttribute("aria-expanded", open);
  head.onclick = () => {
    const sec = el.parentElement;
    const nowOpen = sec.classList.toggle("closed") === false;
    head.setAttribute("aria-expanded", nowOpen);
    store.set("panel:outliner", nowOpen ? "1" : "0");
  };
  const hex = (c) => `#${c.toString(16).padStart(6, "0")}`;
  const row = (b, depth = 0) => `<tr class="ol-row d${depth}" data-id="${b.id}" tabindex="0"><td><i class="dot ${b.kind}" style="background:${hex(b.color)}"></i>${b.name}</td>
    <td class="num" data-k="r"></td><td class="num" data-k="lon"></td><td><span class="src ${b.source}">${b.source === "kepler" ? "Kepler" : b.source}</span></td></tr>`;
  const child = (id, name, icon) => `<tr class="ol-row d1 sub" data-id="${id}" tabindex="0" title="Open it up close"><td><i class="dot ${icon}"></i>${name}</td><td class="num" colspan="3" data-k="v"></td></tr>`;
  const planets = bodies.filter((b) => b.kind !== "asteroid"), rocks = bodies.filter((b) => b.kind === "asteroid");
  root.innerHTML = `<table class="ol-t"><thead><tr><th>Body</th><th class="num">r, AU</th><th class="num">λ, °</th><th>From</th></tr></thead><tbody>
    ${planets.map((b) => row(b) + (b.id === "earth" ? child("moon", "Moon", "moon") + child("earth-tow", "Tow asteroid", "rock") + child("sun-mirrors", "Sunlight mirrors (E3)", "mirror") + child("moon-reflectors", "Moon reflectors", "mirror") : "")
      + (b.id === "mars" ? child("mars-tow", "Tow asteroid", "rock") : "")).join("")}
    <tr class="ol-group"><td colspan="4">Big asteroids</td></tr>${rocks.map((b) => row(b)).join("")}
    </tbody></table><p class="note">Click a planet to centre the solar system on it; click the Moon, a tow asteroid or the reflectors to see them up close.
    λ: ecliptic longitude. "Kepler": not saved in the run, placed on its J2000 orbit.</p>`;
  const cells = {};
  root.querySelectorAll(".ol-row").forEach((tr) => {
    cells[tr.dataset.id] = tr;
    const go = bodies.some((b) => b.id === tr.dataset.id) ? focus : closeUp;
    tr.onclick = () => go(tr.dataset.id);
    tr.onkeydown = (e) => { if (e.key === "Enter") go(tr.dataset.id); };
  });
  const marsTow = d.config.tows.find((t) => t.target === "mars");
  function update(t, s) {
    el.querySelector("#ol-year").textContent = `year ${yr(t)}`;
    for (const b of bodies) {
      const p = b.pos(t), tr = cells[b.id];
      tr.querySelector('[data-k="r"]').textContent = Math.hypot(...p).toFixed(3);
      tr.querySelector('[data-k="lon"]').textContent = b.id === "sun" ? "–" : longitude(p).toFixed(1);
      tr.title = `x ${p[0].toFixed(4)}, y ${p[1].toFixed(4)}, z ${p[2].toFixed(4)} AU (heliocentric ecliptic, J2000)`;
    }
    const set = (id, text) => (cells[id].querySelector('[data-k="v"]').innerHTML = text);
    set("moon", `${yr(d.config.moon.a_km)} km from Earth`);
    set("earth-tow", towActive(d, t, "earth") ? `${yr(Math.hypot(...towLocalAt(d, t)))} km from Earth` : "sent away");
    set("mars-tow", towActive(d, t, "mars") ? `${yr(valueAt(d, "mars_tow_km", t))} km from Mars` : "sent away");
    set("sun-mirrors", `${yr(s.sunSats)} satellites · ${fmt(s.sunArea, 3)} km²`);
    set("moon-reflectors", `≈${yr(s.moonPanels)} panels · ${fmt(s.moonArea, 3)} km²`);
  }
  return { el, update, open };
}

// ------------------------------------------------------------------ Model panel (left)
export function modelPanel(d, ctx) {
  const { exps, speeds, state } = ctx;
  const en = d.config.enablers;
  const earthTow = d.config.tows.find((t) => t.target === "earth");
  const panels = [];
  const updaters = [];

  // Experiments
  const expBox = html(`<div class="exps"></div>`);
  for (const exp of exps) {
    const b = html(`<button class="exp-row" title="${exp.id}. ${exp.title}"><b>${exp.id}</b><span>${exp.title}</span></button>`);
    b.onclick = () => ctx.runExperiment(exp);
    exp.card = b;
    expBox.appendChild(b);
  }
  const expQ = html(`<p class="exp-q"></p>`);
  panels.push(subpanel("experiments", "Experiments R, A–I", [expBox, expQ]));

  // Time: playback speed and the meters
  const speed = slider({ label: "Playback speed", min: 0, max: speeds.length - 1, step: 1, value: state.speed,
    format: (i) => `${speeds[i]} yr/s`, onInput: (i) => ctx.setSpeed(i) });
  const m = {
    journey: meter("Journey (limit year 10,000)"), earth: meter("Earth's orbit", false), mars: meter("Mars's orbit", false),
    beam: meter("Beam power (E1, 1e26 W)"), mirrors: meter("Mirror area (E3, 1e9 km²)"), year: meter("Length of Earth's year", false),
  };
  panels.push(subpanel("time", "Time", [speed, ...Object.values(m)]));
  const a0 = d.series.earth_a[0], m0 = d.series.mars_a[0];
  const marsPark = d.config.tows.find((t) => t.target === "mars").stop_au;
  const yearAtTarget = Math.pow(d.config.arrival.target_au, 1.5) * 365.25;
  updaters.push((t, s) => {
    const left = d.milestones.earthArrives - t;
    m.journey.set(t / d.config.arrival.max_years, `year ${yr(t)}${left > 0 ? ` · ${yr(left)} to arrival` : " · arrived"}`);
    m.earth.set((s.a - a0) / (d.config.arrival.target_au - a0), `${s.a.toFixed(3)} → ${d.config.arrival.target_au} AU`);
    const ma = valueAt(d, "mars_a", t);
    m.mars.set((ma - m0) / (marsPark - m0), `${ma.toFixed(3)} → ${marsPark} AU`);
    const bw = valueAt(d, "beam_w", t);
    m.beam.set(bw / en.e1_beam_limit_w, `${fmt(bw, 3)} W`);
    m.mirrors.set(s.e3Total / en.e3_mirror_area_limit_km2, `${s.moonArea ? "≈" : ""}${fmt(s.e3Total, 3)} km²`);
    m.year.set(s.yearDays / yearAtTarget, `${(s.yearDays / 365.25).toFixed(2)} of today's years`);
  });
  ctx.setSpeedUI = (i) => speed.set(i);

  // Concept and enablers
  panels.push(subpanel("concept", "Concept and enablers", html(`<div><p>A ${fmt(earthTow.asteroid_mass_kg, 3)} kg asteroid sits ${yr(earthTow.distance_km)} km from Earth,
    45° between "ahead" and "away from the Sun". Its gravity pulls Earth outward along its orbit; Earth pulls back on it with the same force, and beams
    from stations far sunward push on a mirror tied to the asteroid to hold it in place. Nothing touches Earth. Mars is moved first, to ${marsPark} AU.</p>
    <ul class="enablers">${Object.entries(en.covers).map(([k, v]) => `<li><b>${k}</b>: ${v}</li>`).join("")}</ul></div>`)));

  const el = html(`<div><div class="fp-h static">Model</div><div class="fp-b"></div></div>`);
  el.lastElementChild.append(...panels);
  return {
    el,
    update(t, s) { for (const u of updaters) u(t, s); },
    markExperiment(exp) {
      exps.forEach((e) => e.card.classList.toggle("on", e === exp));
      expQ.innerHTML = exp ? `<b>${exp.id}. ${exp.title}.</b> ${exp.q}` : "";
    },
  };
}

// ------------------------------------------------------------------ Data panel (right)
const COMPARE = [
  // [factor, value(s), format(v), change: "x" ratio, "d" difference, or none, estimate?(s)]
  ["Orbit size", (s) => s.a, (v) => `${v.toFixed(3)} AU`, "x"],
  ["Eccentricity", (s) => s.e, (v) => v.toFixed(4), "d"],
  ["Orbital speed", (s) => s.speed, (v) => `${v.toFixed(1)} km/s`, "x"],
  ["Length of the year", (s) => s.yearDays, (v) => `${yr(v)} d`, "x"],
  ["Each season lasts", (s) => s.seasonDays / 30.44, (v) => `${v.toFixed(1)} months`, "x"],
  ["Full Moon to full Moon", (s) => s.synodic, (v) => `${v.toFixed(2)} d`, "d"],
  ["Sun's apparent size", (s) => s.sunDeg, (v) => `${v.toFixed(3)}°`, "x"],
  ["Direct sunlight", (s, S0) => s.direct * S0, (v) => `${v.toFixed(0)} W/m²`, "x"],
  ["Sunlight with mirrors", (s) => s.share, (v) => pct(v), "d"],
  ["Earth's light from mirrors", (s) => s.mirrorPart, (v) => pct(v, 0), "d"],
  ["Daylight, outside the air", (s) => s.dayLux, (v) => `${fmt(v, 3)} lux`, "x"],
  ["Sunlight swing, perihelion / aphelion", (s) => s.swing, (v) => pct(v), "d"],
  ["Global mean temperature", (s) => s.temp, (v) => `${v.toFixed(1)} K`, "d"],
  ["Surface with liquid water", (s) => s.water, (v) => pct(v, 0), "d"],
  ["Absorbed sunlight", (s) => s.absorbed, (v) => `${v.toFixed(0)} W/m²`, "d"],
  ["Full-Moon light", (s) => s.naturalLux + s.reflectorLux, (v) => `${fmt(v, 3)} lux`, "x", () => true],
  ["Night heating from Moon reflectors", (s) => s.heating, (v) => `${fmt(v, 2)} W/m²`, "d", () => true],
  ["Sun's tide against the Moon's", (s) => s.tide, (v) => v.toFixed(3), "x"],
  ["Sunlight travel time", (s) => s.lightMin, (v) => `${v.toFixed(1)} min`, "x"],
  ["Magnetopause", (s) => s.magnetopause, (v) => `${v.toFixed(1)} R⊕`, "x"],
  ["Moon / Earth's Hill radius", (s) => s.hill, (v) => v.toFixed(3), "x"],
  ["Nitrogen kept (Jeans λ)", (s) => s.jeans, (v) => v.toFixed(0), "x"],
  ["Change in length of day", (s) => s.lod, (v) => `${fmt(v, 2)} s`, "d"],
  ["1 km asteroid impacts (without E1's nudges)", (s) => 1 / s.impactEvery, (v) => `1 per ${fmt(1 / v, 3)} yr`, "x"],
];

export function dataPanel(d, model) {
  const k = d.config.constants, en = d.config.enablers, night = d.config.night, hab = d.config.habitability, moon = d.config.moon;
  const tows = d.config.tows;
  const constants = kv([
    ["Gravitational constant G", `${k.G} m³/kg/s²`], ["Speed of light c", `${fmt(k.c, 9)} m/s`], ["Stefan–Boltzmann σ", `${fmt(k.sigma, 6)} W/m²/K⁴`],
    ["Astronomical unit", `${fmt(k.au_m, 10)} m`], ["Julian year", `${fmt(k.year_s, 6)} s`], ["Sun's GM", `${fmt(k.gm_sun, 12)} m³/s²`],
    ["Sun's mass", `${fmt(k.m_sun, 5)} kg`], ["Sunlight at 1 AU (solar constant)", `${k.solar_constant} W/m²`],
    ["Sunlight's luminous efficacy", `${night.sunlight_lm_per_w} lm/W`], ["Full Moon today", `${night.full_moon_lux_today} lux`],
    ["Earth with the Moon, mass", `${fmt(hab.earth_mass_with_moon_kg, 6)} kg`], ["Earth's radius", `${yr(k.earth_radius_m / 1e3)} km`],
    ["Moon's mass", `${fmt(moon.mass_kg, 4)} kg`], ["Moon's distance", `${yr(moon.a_km)} km`], ["Moon's radius", `${night.moon_radius_km} km`],
    ["Earth's albedo (warm / icy)", `${k.warm_albedo} / ${k.ice_albedo}`], ["Effective emissivity (288 K today)", k.emissivity.toFixed(4)],
    ["Mirror reflectivity", hab.mirror_reflectivity],
    ...tows.map((t) => [`${t.target === "earth" ? "Earth" : "Mars"} tow asteroid`, `${fmt(t.asteroid_mass_kg, 3)} kg at ${yr(t.distance_km)} km`]),
    ["E1 beam power", `${fmt(en.e1_beam_limit_w, 2)} W`], ["E2 strength / absorbs", `${fmt(en.e2_strength_pa, 2)} Pa / ${fmt(en.e2_absorbed_fraction, 1)}`],
    ["E3 asteroids / mirrors", `${fmt(en.e3_asteroid_limit_kg, 2)} kg / ${fmt(en.e3_mirror_area_limit_km2, 2)} km²`],
    ["Sunlight satellite / Moon panel", `${yr(night.sunlight_satellite_unit_km2)} km² / ${night.moon_reflector_unit_km2} km²`],
    ["Structural safety factor, at least", d.config.safety.structural_safety_factor_min],
  ]);
  const s0 = model.state(0, 0);
  const initial = kv([
    ["Orbit", `${s0.a.toFixed(5)} AU, e ${s0.e.toFixed(4)}`], ["Orbital speed", `${s0.speed.toFixed(2)} km/s`],
    ["Year", `${s0.yearDays.toFixed(2)} days`], ["Sunlight", `${(s0.direct * k.solar_constant).toFixed(0)} W/m²`],
    ["Global mean temperature", `${s0.temp.toFixed(1)} K`], ["Surface with liquid water", pct(s0.water, 0)],
    ["Absorbed sunlight", `${s0.absorbed.toFixed(0)} W/m²`], ["Surface pressure", `${hab.surface_pressure_kpa} kPa`],
    ["Magnetopause", `${s0.magnetopause.toFixed(1)} Earth radii`], ["Moon / Earth's Hill radius", s0.hill.toFixed(3)],
    ["Full Moon", `${fmt(s0.naturalLux, 3)} lux`], ["Sun's tide against the Moon's", s0.tide.toFixed(3)],
    ["1 km asteroid impacts", `1 per ${yr(s0.impactEvery)} years`],
  ]);
  const cmp = html(`<div><table class="cmp"><thead><tr><th>Factor</th><th class="num">Year 0</th><th class="num" id="cmp-now">Now</th><th class="num">Change</th></tr></thead><tbody></tbody></table>
    <p class="note">≈ marks the Moon reflectors (sim/night.py), which are not in the saved run; they restore today's full Moon. Everything else is the saved run, between its frames 10 years apart.</p></div>`);
  const tbody = cmp.querySelector("tbody");
  tbody.innerHTML = COMPARE.map(([name]) => `<tr><td>${name}</td><td class="num"></td><td class="num"></td><td class="num"></td></tr>`).join("");
  const trs = [...tbody.children];
  COMPARE.forEach(([, v, f], i) => (trs[i].children[1].textContent = f(v(s0, k.solar_constant))));

  const results = html(`<div><div id="validity" class="validity"></div><nav class="tabs" id="tabs" role="tablist"></nav><div id="panel" class="panel"></div></div>`);
  const el = html(`<div><div class="fp-h static">Data</div><div class="fp-b"></div></div>`);
  el.lastElementChild.append(
    subpanel("constants", "Constants", html(`<div>${constants}<p class="note">From config.yaml and the Python model (sim/constants.py, sim/habitability.py).</p></div>`), false),
    subpanel("initial", "Initial Earth (year 0)", html(`<div>${initial}</div>`)),
    subpanel("compare", "Now against year 0", cmp),
    subpanel("results", "Results and checks", results),
  );
  function update(t, s) {
    cmp.querySelector("#cmp-now").textContent = `Year ${yr(t)}`;
    COMPARE.forEach(([, v, f, ch, isEst], i) => {
      const a = v(s0, k.solar_constant), b = v(s, k.solar_constant);
      const mark = isEst?.(s) ? "≈" : "";
      trs[i].children[2].textContent = mark + f(b);
      let c = "";
      if (ch === "x" && a) c = `×${fmt(b / a, 3)}`;
      else if (ch === "d") { const dv = b - a; c = Math.abs(dv) < 1e-12 ? "0" : `${dv > 0 ? "+" : "−"}${f(Math.abs(dv)).replace(/^[+-]/, "")}`; }
      trs[i].children[3].textContent = c;
    });
  }
  return { el, update };
}

// ------------------------------------------------------------------ Experiment I's explainer (over the Data panel)
// What a million years after arrival proves about the moved solar system's stability, and what it cannot.
export function millionYears(d) {
  const lt = d.longterm, mi = lt.moved_info, ri = lt.real_info, mr = lt.moved_ranges, rr = lt.real_ranges, v = lt.verdict;
  const near = lt.encounters.filter((e) => e.bodies.includes("earth"));
  const span = (r, digits) => `${r[0].toFixed(digits)}–${r[1].toFixed(digits)}`;
  const drift = (100 * (mr.earth.a[1] - mr.earth.a[0])) / 2 / ((mr.earth.a[0] + mr.earth.a[1]) / 2);
  const copies = lt.chaos_copies.map((c) => `copy ${c.seed}: ${c.verdict_flags} unresolved flags, eccentricity up to ${c.earth_e_max}, `
    + `orbit gap to Mars ${c.gap_min_au.toFixed(3)} AU`).join("; ");
  return html(`<div class="explainer-card" role="dialog" aria-label="A million years later: what it means">
    <div class="ex-h"><b>A million years later: what this test means</b><button data-close aria-label="Close">×</button></div>
    <div class="ex-b">
      <p class="ex-lead">Moving Earth is only half the job; it has to stay. Once the tows are switched off and their asteroids sent away,
        nothing holds Earth at ${d.config.arrival.target_au} AU but gravity: the Sun, Jupiter and the other planets. This experiment asks
        whether that new arrangement is stable, or slowly comes apart.</p>
      <h4>How it is tested</h4>
      <ul>
        <li>The solar system as the journey leaves it runs for ${yr(mi.years)} years in REBOUND (MERCURIUS: 5-day steps, small steps in any close pass).</li>
        <li>The <b>real</b> solar system runs for the same ${yr(ri.years)} years with the same code. That is the yardstick: whatever today's Earth does
          anyway is not a danger the move created.</li>
        <li>Two chaos copies start with tiny changes. If they told a different story, the verdict would be luck.</li>
        <li>Energy is kept to ${fmt(mi.energy_error, 2)} of the total (real run ${fmt(ri.energy_error, 2)}): any drift is physics, not rounding.</li>
      </ul>
      <h4>What "stable" means here, and the result</h4>
      <table><thead><tr><th>Check</th><th class="num">Moved Earth</th><th class="num">Real Earth</th></tr></thead><tbody>
        <tr><td>Orbit size, AU</td><td class="num">${span(mr.earth.a, 4)} (±${drift.toFixed(2)}%)</td><td class="num">${span(rr.earth.a, 4)}</td></tr>
        <tr><td>Eccentricity (how oval: the yearly swing in sunlight)</td><td class="num">up to ${mr.earth.e[1]}</td><td class="num">up to ${rr.earth.e[1]}</td></tr>
        <tr><td>Axial tilt (the seasons), degrees</td><td class="num">${span(mi.axial_tilt_deg, 1)}</td><td class="num">${span(ri.axial_tilt_deg, 1)}</td></tr>
        <tr><td>Smallest gap between Earth's and Mars's orbits</td><td class="num">${mi.earth_mars_orbit_gap_min_au.toFixed(2)} AU</td><td class="num">${ri.earth_mars_orbit_gap_min_au.toFixed(2)} AU</td></tr>
        <tr><td>Bodies thrown out of the solar system</td><td class="num">${lt.thrown_out.length ? lt.thrown_out.map((x) => x.body).join(", ") : "none"}</td><td class="num"></td></tr>
        <tr><td>Big asteroids passing within 0.01 AU of Earth</td><td class="num">${near.length}, each nudged aside by E1</td><td class="num"></td></tr>
      </tbody></table>
      <div class="ex-chips">${chip(v.flags.unresolved ? "fail" : "pass", `${v.flags.unresolved} unresolved flags`)}
        ${v.flags.flags.map((f) => chip("cover", `${f.check}: ${f.covered_by}`)).join(" ")}</div>
      <p>Chaos copies agree: ${copies}.</p>
      <h4>What it does not prove</h4>
      <p>The inner planets' orbits are chaotic: tiny differences grow about e-fold every 5 million years (Laskar 1989). A million years rules
        out the quick ways a moved planet fails (caught in a resonance, close encounters, thrown out), but no run can forecast billions of years
        exactly, for the moved Earth or the real one. That is why the moved Earth is judged against the real one over the same span.</p>
      <div class="ex-foot"><button class="primary" data-close>Got it</button></div>
    </div>
  </div>`);
}

