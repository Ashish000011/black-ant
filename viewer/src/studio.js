// The Blender-style panels: the Scene tab (where every body is), the Model panel (sliders, time meters, what-if
// estimates, experiments) and the Data panel (constants, Earth at the start, now against then, every result).
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
const est = (s) => `<span class="est" title="Live estimate, not from the saved run">≈</span>${s}`;
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

function seg(options, value, onPick) {
  const el = html(`<div class="seg full">${options.map(([k, label]) => `<button data-k="${k}">${label}</button>`).join("")}</div>`);
  const mark = (k) => el.querySelectorAll("button").forEach((b) => b.classList.toggle("on", b.dataset.k === k));
  el.querySelectorAll("button").forEach((b) => (b.onclick = () => { mark(b.dataset.k); onPick(b.dataset.k); }));
  mark(value);
  return el;
}

// ------------------------------------------------------------------ Scene tab (top left)
export function outliner(d, bodies, { focus }) {
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
  const child = (id, name, icon) => `<tr class="ol-row d1 sub" data-id="${id}"><td><i class="dot ${icon}"></i>${name}</td><td class="num" colspan="3" data-k="v"></td></tr>`;
  const planets = bodies.filter((b) => b.kind !== "asteroid"), rocks = bodies.filter((b) => b.kind === "asteroid");
  root.innerHTML = `<table class="ol-t"><thead><tr><th>Body</th><th class="num">r, AU</th><th class="num">λ, °</th><th>From</th></tr></thead><tbody>
    ${planets.map((b) => row(b) + (b.id === "earth" ? child("moon", "Moon", "moon") + child("earth-tow", "Tow asteroid", "rock") + child("sun-mirrors", "Sunlight mirrors (E3)", "mirror") + child("moon-reflectors", "Moon reflectors", "mirror") : "")
      + (b.id === "mars" ? child("mars-tow", "Tow asteroid", "rock") : "")).join("")}
    <tr class="ol-group"><td colspan="4">Big asteroids</td></tr>${rocks.map((b) => row(b)).join("")}
    </tbody></table><p class="note">Click a body to centre the view on it. λ: ecliptic longitude. "Kepler": not saved in the run, placed on its J2000 orbit.</p>`;
  const cells = {};
  root.querySelectorAll(".ol-row").forEach((tr) => {
    cells[tr.dataset.id] = tr;
    if (bodies.some((b) => b.id === tr.dataset.id)) {
      tr.onclick = () => focus(tr.dataset.id);
      tr.onkeydown = (e) => { if (e.key === "Enter") focus(tr.dataset.id); };
    }
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
    set("sun-mirrors", `${s.sunEst ? "≈" : ""}${yr(s.sunSats)} satellites · ${fmt(s.sunArea, 3)} km²`);
    set("moon-reflectors", `≈${yr(s.moonPanels)} panels · ${fmt(s.moonArea, 3)} km²`);
  }
  return { el, update, open };
}

// ------------------------------------------------------------------ Model panel (left)
export function modelPanel(d, model, ctx) {
  const { whatIf: w, exps, speeds, state } = ctx;
  const night = d.config.night, en = d.config.enablers, end = d.milestones.end;
  const earthTow = d.config.tows.find((t) => t.target === "earth");
  const S0 = d.config.constants.solar_constant;
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
    m.mirrors.set(s.e3Total / en.e3_mirror_area_limit_km2, `${s.sunEst || s.moonArea ? "≈" : ""}${fmt(s.e3Total, 3)} km²`);
    m.year.set(s.yearDays / yearAtTarget, `${(s.yearDays / 365.25).toFixed(2)} of today's years`);
  });
  ctx.setSpeedUI = (i) => speed.set(i);

  // Target orbit: what-if estimates
  const tgt = slider({ label: "Target orbit", min: 1.0, max: 3.6, step: 0.01, value: w.target, format: (v) => `${v.toFixed(2)} AU`,
    onInput: (v) => { w.target = v; ctx.onChange(); } });
  const mass = slider({ label: "Tow asteroid mass", min: 0.5, max: en.e3_asteroid_limit_kg / 1e20, step: 0.01, value: w.massKg / 1e20,
    format: (v) => `${v.toFixed(2)}e20 kg`, onInput: (v) => { w.massKg = v * 1e20; ctx.onChange(); } });
  const dist = slider({ label: "Tow distance", min: 450, max: 1000, step: 0.1, value: w.distKm / 1e3,
    format: (v) => `${yr(v * 1e3)} km`, onInput: (v) => { w.distKm = v * 1e3; ctx.onChange(); } });
  const tgtOut = html(`<div></div>`), tgtWarn = html(`<div class="warns"></div>`);
  const reset = html(`<button class="wide">Back to the run's design</button>`);
  reset.onclick = () => {
    Object.assign(w, { target: d.config.arrival.target_au, massKg: earthTow.asteroid_mass_kg, distKm: earthTow.distance_km });
    tgt.set(w.target); mass.set(w.massKg / 1e20); dist.set(w.distKm / 1e3);
    ctx.onChange();
  };
  const arr = d.summary.tows["earth-tow"].arrival;
  panels.push(subpanel("target", "Target orbit <span class='est-tag'>≈ estimate</span>", [tgt, mass, dist, tgtOut, tgtWarn, reset,
    html(`<p class="note">A steady push along the orbit takes (speed at the start − speed at the target) / push. The saved run reached ${arr.a_au} AU in year
      ${yr(arr.year)}, ×${model.calib.toFixed(2)} the ideal (its tow eases off while Mars sprints, and the arrival trim weakens it), so estimates are
      scaled by that. An official answer needs config.yaml changed and the journey re-run (about an hour and a half).</p>`)]));
  updaters.push(() => {
    const r = model.tow(w);
    const finish = r.years;
    const sunNeed = model.sunAreaNeeded(w.target);
    const moonNeed = model.moonAreaFor(night.full_moon_lux_today, w.target);
    const beamOk = r.total <= en.e1_beam_limit_w;
    tgtOut.innerHTML = kv([
      ["Pull on Earth", est(`${fmt(r.force, 3)} N`)],
      ["Push along the orbit", est(`${fmt(r.acc, 3)} m/s²`)],
      ["Speed change needed", est(`${(r.dv / 1e3).toFixed(2)} km/s`)],
      ["Beam power, with Mars's tow", est(`${fmt(r.total, 3)} W ${chip(beamOk ? "pass" : "fail", beamOk ? "" : "over E1")}`)],
      ["Arrives", est(`year ${yr(finish)} ${chip(finish <= d.config.arrival.max_years ? "pass" : "fail", "")}`)],
      ["Sunlight there, without mirrors", est(pct(1 / w.target ** 2))],
      ["Sunlight mirrors needed there", est(`${fmt(sunNeed, 3)} km² · ${yr(sunNeed / night.sunlight_satellite_unit_km2)} satellites`)],
      ["Moon reflectors for today's full Moon", est(`${fmt(moonNeed, 3)} km² · ${yr(moonNeed / night.moon_reflector_unit_km2)} panels`)],
    ]);
    const warns = model.warnings(w.target);
    if (sunNeed + moonNeed > en.e3_mirror_area_limit_km2) warns.push(["fail", "Mirrors needed exceed E3's 1e9 km²"]);
    if (w.distKm < d.config.beam.earth_clearance_km) warns.push(["fail", "Tow inside the beams' 420,000 km clearance"]);
    tgtWarn.innerHTML = warns.length ? warns.map(([k, text]) => chip(k, text)).join("") : chip("pass", "No known hazard at this orbit");
  });

  // Sunlight mirrors (E3)
  const satMax = en.e3_mirror_area_limit_km2 / night.sunlight_satellite_unit_km2;
  const sats = slider({ label: "Satellites", min: 0, max: satMax, step: 100, value: w.sunSats, format: (v) => yr(v),
    onInput: (v) => { w.sunSats = v; if (w.sunMode !== "manual") { w.sunMode = "manual"; sunSeg.querySelectorAll("button").forEach((b) => b.classList.toggle("on", b.dataset.k === "manual")); } ctx.onChange(); } });
  const sunSeg = seg([["run", "Follow the run"], ["manual", "Set my own"]], w.sunMode, (k) => { w.sunMode = k; ctx.onChange(); });
  const sunOut = html(`<div></div>`);
  panels.push(subpanel("sun-mirrors", "Sunlight reflector satellites (E3)", [sunSeg, sats, sunOut,
    html(`<p class="note">One satellite = ${yr(night.sunlight_satellite_unit_km2)} km² of mirror (config.yaml, night). They sit near Earth and reflect
      ${pct(model.rho, 0)} of the sunlight they catch onto it. "Follow the run" replays the journey's 25-year build schedule.</p>`)]));
  updaters.push((t, s) => {
    if (w.sunMode === "run") sats.set(Math.round(s.sunSats / 100) * 100);
    const tag = (x) => (s.sunEst ? est(x) : x);
    sunOut.innerHTML = kv([
      ["Now", tag(`${yr(s.sunSats)} satellites · ${fmt(s.sunArea, 3)} km²`)],
      ["Needed now for today's sunlight", est(`${yr(s.sunNeeded / night.sunlight_satellite_unit_km2)} satellites`)],
      ["Sunlight against today", tag(pct(s.share))],
      ["Global mean temperature", tag(`${s.temp.toFixed(1)} K ${chip(s.temp >= d.config.safety.temperature_min_k && s.temp <= d.config.safety.temperature_max_k ? "pass" : "fail", "")}`)],
      ["Surface with liquid water", tag(pct(s.water, 0))],
      ["Absorbed sunlight", tag(`${s.absorbed.toFixed(0)} W/m² ${chip(s.absorbed <= d.config.safety.runaway_absorbed_max_w_m2 ? "pass" : "fail", "")}`)],
      ["Earth's light from mirrors", tag(pct(s.mirrorPart, 0))],
    ]);
  });

  // Moon reflectors (night light and heat)
  const cap = model.nearSideKm2 / night.moon_reflector_unit_km2;
  const logMax = Math.log10(cap);
  const panelsS = slider({ label: "Moon reflector panels", min: 0, max: 1000, step: 1, value: w.moonPanels,
    toValue: (p) => (p <= 0 ? 0 : Math.round(10 ** ((p / 1000) * logMax))), fromValue: (n) => (n <= 0 ? 0 : (1000 * Math.log10(Math.max(1, n))) / logMax),
    format: (n) => yr(n), onInput: (n) => { w.moonPanels = n; if (w.moonMode !== "manual") { w.moonMode = "manual"; moonSeg.querySelectorAll("button").forEach((b) => b.classList.toggle("on", b.dataset.k === "manual")); } ctx.onChange(); } });
  const moonSeg = seg([["auto", "Restore today's full Moon"], ["manual", "Set my own"]], w.moonMode, (k) => { w.moonMode = k; ctx.onChange(); });
  const phase = slider({ label: "Moon phase angle", min: 0, max: 180, step: 1, value: w.phaseDeg,
    format: (v) => `${v}° ${v < 20 ? "(full)" : v < 80 ? "(gibbous)" : v <= 100 ? "(quarter)" : v < 160 ? "(crescent)" : "(new)"}`,
    onInput: (v) => { w.phaseDeg = v; ctx.onChange(); } });
  const moonOut = html(`<div></div>`), moonVerdict = html(`<div class="verdict small"></div>`);
  panels.push(subpanel("moon-reflectors", "Moon reflectors: night light <span class='est-tag'>≈ estimate</span>", [moonSeg, panelsS, phase, moonOut, moonVerdict,
    html(`<p class="note">Flat mirrors on the Moon's near side, one panel = ${night.moon_reflector_unit_km2} km², counted against E3's 1e9 km² of mirrors
      (no new enabler). They are lit only from first to last quarter, around full Moon, when the Moon is over Earth's night side, so they keep
      the monthly cycle: cos(phase/2) of their full-Moon light, ${pct(d.config.constants.month_mean, 0)} over a month. Model: sim/night.py.</p>`)]));
  updaters.push((t, s) => {
    if (w.moonMode === "auto") panelsS.set(s.moonPanels);
    const fullTotal = s.naturalLux + s.reflectorLux;
    const today = night.full_moon_lux_today;
    moonOut.innerHTML = kv([
      ["Panels now", est(`${yr(s.moonPanels)} · ${fmt(s.moonArea, 3)} km² · ${pct(s.nearShare, s.nearShare < 0.01 ? 3 : 1)} of the near side`)],
      ["Full Moon, natural", est(`${fmt(s.naturalLux, 3)} lux (${pct(s.naturalLux / today, 0)} of today)`)],
      ["Full Moon, with reflectors", est(`${fmt(fullTotal, 3)} lux ${chip(fullTotal >= today * 0.98 ? "pass" : "cover", fullTotal >= today * 0.98 ? "today's" : "dimmer")}`)],
      [`Reflectors at ${w.phaseDeg}°`, est(`${fmt(s.phaseLux, 3)} lux`)],
      ["Reflectors, monthly mean", est(`${fmt(s.monthLux, 3)} lux`)],
      ["Patch one panel lights", est(`${yr(model.spotKm(s.a))} km across`)],
      ["Light sent at full Moon", est(`${fmt(s.moonW, 3)} W`)],
      ["Night-side heating, full Moon", est(`${fmt(s.heating, 3)} W/m² (${fmt((100 * s.heating) / model.todayAbsorbed, 2)}% of the ${model.todayAbsorbed.toFixed(0)} W/m² absorbed by day)`)],
      ["Global warming, monthly mean", est(`${fmt(s.warming, 2)} K`)],
      ["All mirrors against E3", est(`${fmt(s.e3Total, 3)} / 1e9 km² ${chip(s.e3Total <= en.e3_mirror_area_limit_km2 ? "pass" : "fail", "")}`)],
    ]);
    const maxW = model.nightHeating(model.nearSideKm2, s.a, s.e);
    moonVerdict.innerHTML = `<b>Light, yes; heat, no.</b> Even the whole near side mirrored would send ${maxW.toFixed(1)} W/m² to the night side at full Moon here
      (${pct(maxW / model.todayAbsorbed, 1)} of what Earth absorbs by day). The sunlight satellites keep the temperature; Moon reflectors only give back the night's light.`;
    if (s.nearShare > 1) moonVerdict.innerHTML += ` ${chip("fail", "more than the near side can hold")}`;
  });

  // Concept and enablers
  panels.push(subpanel("concept", "Concept and enablers", html(`<div><p>A ${fmt(earthTow.asteroid_mass_kg, 3)} kg asteroid sits ${yr(earthTow.distance_km)} km from Earth,
    45° between "ahead" and "away from the Sun". Its gravity pulls Earth outward along its orbit; Earth pulls back on it with the same force, and beams
    from stations far sunward push on a mirror tied to the asteroid to hold it in place. Nothing touches Earth. Mars is moved first, to ${marsPark} AU.</p>
    <ul class="enablers">${Object.entries(en.covers).map(([k, v]) => `<li><b>${k}</b>: ${v}</li>`).join("")}</ul></div>`), false));

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
  ["Sunlight with mirrors", (s) => s.share, (v) => pct(v), "d", (s) => s.sunEst],
  ["Earth's light from mirrors", (s) => s.mirrorPart, (v) => pct(v, 0), "d", (s) => s.sunEst],
  ["Daylight, outside the air", (s) => s.dayLux, (v) => `${fmt(v, 3)} lux`, "x", (s) => s.sunEst],
  ["Sunlight swing, perihelion / aphelion", (s) => s.swing, (v) => pct(v), "d"],
  ["Global mean temperature", (s) => s.temp, (v) => `${v.toFixed(1)} K`, "d", (s) => s.sunEst],
  ["Surface with liquid water", (s) => s.water, (v) => pct(v, 0), "d", (s) => s.sunEst],
  ["Absorbed sunlight", (s) => s.absorbed, (v) => `${v.toFixed(0)} W/m²`, "d", (s) => s.sunEst],
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
  const s0 = model.state(0, { sunMode: "run", moonMode: "manual", moonPanels: 0, phaseDeg: 0 });
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
    <p class="note">≈ marks live estimates (your slider settings, or a model outside the saved run). Everything else is the saved run, between its frames 10 years apart.</p></div>`);
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
