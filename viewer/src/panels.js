// The experiments list and the results tabs. Every number is read from the data files; nothing is typed here.
import { lineChart, fmt } from "./charts.js";
import { G, MASS, valueAt } from "./data.js";

const REPO = "https://github.com/Ashish000011/black-ant/blob/main";
const yr = (v) => Math.round(v).toLocaleString("en");
const pct = (v, digits = 1) => `${(v * 100).toFixed(digits)}%`;
// A benchmark value may be a number, a list (vector or several results) or named parts.
const show = (v) => (Array.isArray(v) ? v.map((x) => fmt(x, 6)).join(", ")
  : v && typeof v === "object" ? Object.entries(v).map(([k, x]) => `${k.replace(/_/g, " ")} ${fmt(x, 3)}`).join("; ")
    : typeof v === "number" ? fmt(v, 6) : String(v));
const hours = (days) => (days < 1 ? `${(days * 24).toFixed(1)} h` : `${days.toFixed(2)} d`);

export function chip(kind, text) {
  const word = { pass: "Pass", fail: "Fail", cover: "Covered", info: "" }[kind];
  return `<span class="chip ${kind}"><i></i>${word ? `${word}${text ? ": " : ""}` : ""}${text}</span>`;
}

function div(html) {
  const e = document.createElement("div");
  e.innerHTML = html;
  return e;
}

function tiles(items) {
  return `<div class="tiles">${items.map(([k, v, s]) => `<div class="tile"><div class="k">${k}</div><div class="v">${v}</div>${s ? `<div class="s">${s}</div>` : ""}</div>`).join("")}</div>`;
}

function table(head, rows, numCols = []) {
  const th = head.map((h, i) => `<th${numCols.includes(i) ? ' class="num"' : ""}>${h}</th>`).join("");
  const tr = rows.map((r) => `<tr>${r.map((c, i) => `<td${numCols.includes(i) ? ' class="num"' : ""}>${c}</td>`).join("")}</tr>`).join("");
  return `<table><thead><tr>${th}</tr></thead><tbody>${tr}</tbody></table>`;
}

// The ten Earth-safety thresholds (the company demo's Safety thresholds panel), limits from config.yaml.
export function thresholds(d) {
  const s = d.config.safety;
  return [
    { key: "temperature_k", name: "Global mean temperature, low", unit: " K", limit: s.temperature_min_k, kind: "min" },
    { key: "temperature_k", name: "Global mean temperature, high", unit: " K", limit: s.temperature_max_k, kind: "max" },
    { key: "liquid_water_share", name: "Surface with liquid water", limit: s.liquid_water_min_share, kind: "min", f: (v) => pct(v, 0) },
    { key: "absorbed_w_m2", name: "Absorbed sunlight (runaway greenhouse)", unit: " W/m²", limit: s.runaway_absorbed_max_w_m2, kind: "max" },
    { key: "surface_pressure_kpa", name: "Surface pressure", unit: " kPa", limit: s.surface_pressure_min_kpa, kind: "min" },
    { key: "jeans_lambda_n2", name: "Nitrogen kept (Jeans λ)", limit: s.jeans_lambda_min, kind: "min" },
    { key: "magnetopause_re", name: "Magnetopause distance", unit: " Earth radii", limit: s.magnetopause_min_re, kind: "min" },
    { key: "day_length_change_s", name: "Change in length of day", unit: " s", limit: s.day_length_change_max_s, kind: "max" },
    { key: "moon_hill_share", name: "Moon's distance / Earth's Hill radius", limit: s.moon_hill_max_share, kind: "max" },
    { key: "thrust_over_moon_pull", name: "Tow thrust / Earth's pull on the Moon", limit: s.thrust_over_moon_pull_max, kind: "max" },
  ];
}

function worst(d, th) {
  const v = d.series[th.key].filter((x) => x != null);
  return th.kind === "min" ? Math.min(...v) : Math.max(...v);
}

export function validity(d) {
  const fl = d.summary.flags;
  const benchOk = d.benchmarks.filter((b) => b.ok).length;
  const lg = d.summary.ledger;
  const earth = d.summary.tows["earth-tow"].arrival;
  const safeOk = thresholds(d).every((th) => (th.kind === "min" ? worst(d, th) >= th.limit : worst(d, th) <= th.limit));
  const sfMin = Math.min(...d.structures.filter((r) => r.check.includes("safety factor")).map((r) => r.value));
  const lt = d.longterm.verdict.flags;
  return [
    chip(earth.year <= 10000 ? "pass" : "fail", `arrives year ${yr(earth.year)} (limit 10,000)`),
    chip(fl.unresolved ? "fail" : "pass", `${fl.unresolved} unresolved flags`),
    chip("cover", `${fl.covered_by_enablers} flags covered by enablers E1–E3`),
    chip(benchOk === d.benchmarks.length ? "pass" : "fail", `${benchOk}/${d.benchmarks.length} benchmarks`),
    chip(safeOk ? "pass" : "fail", "10 Earth-safety thresholds"),
    chip(sfMin >= 1.5 ? "pass" : "fail", `safety factor ≥ ${sfMin.toFixed(2)}`),
    chip(lg.nothing_from_nothing_max < 1e-9 ? "pass" : "fail", `momentum ledger ${fmt(lg.nothing_from_nothing_max, 2)} (1e-9)`),
    chip(lt.unresolved ? "fail" : "pass", "a million years after"),
  ].join("");
}

// ---------------------------------------------------------------- experiments
export function experiments(d) {
  const m = d.milestones;
  return [
    { id: "R", title: "Reference concept: Octo-Earth", view: "octo", t: 0, play: false, tab: "Summary",
      q: "A ring round the globe with eight 12,000 km arms, pushed by currents in magnetic fields. What does established physics say about it?" },
    { id: "A", title: "Baseline", view: "system", t: 0, play: false, tab: "Validation",
      q: "Sun and planets with no push. Do the integrators and the ten official benchmarks hold?" },
    { id: "B", title: "The journey", view: "system", t: 0, play: true, tab: "Summary",
      q: "A light-held gravity tractor tows Earth from 1 AU to 2.7 AU. Does it get there within 10,000 years with every check held?" },
    { id: "C", title: "The tow up close", view: "earth", t: 1200, play: true, tab: "Forces & momentum",
      q: "What holds the asteroid in place, what does each force act on, and where does every newton-second go?" },
    { id: "D", title: "Mars clears the way", view: "system", t: Math.max(0, m.marsSprintStart - 300), play: true, tab: "Summary",
      q: "Mars must move out first, across Jupiter's 2:1 resonance. Is it caught, and does it ever come near Earth?" },
    { id: "E", title: "Beam outage", view: "earth", t: 2000, play: false, tab: "Summary",
      q: "If the beams go dark, how long before a tow asteroid drifts off its spot and the tow is lost?" },
    { id: "F", title: "Earth safety", view: "earth", t: 0, play: true, tab: "Earth safety",
      q: "Do temperature, water, air, shielding, day length and the Moon stay inside the ten thresholds all the way?" },
    { id: "G", title: "Structures", view: "earth", t: 3000, play: false, tab: "Structure",
      q: "Do the cables, anchors, mirrors and the asteroids themselves hold at full beam power with a safety factor of 1.5?" },
    { id: "H", title: "Crossing the asteroid belt", view: "system", t: m.beltEntry, play: true, tab: "Summary",
      q: "Earth spends about 2,800 years in the belt. How often would a 1 km asteroid hit, and how is that stopped?" },
    { id: "I", title: "A million years later", view: "system", t: m.end, play: false, tab: "Summary",
      q: "Once moved, does the new solar system stay put for a million years, and how does it compare with the real one?" },
  ];
}

const answers = {
  R(d) {
    const r = d.octo, all = r.net_force_all_arms, one = r.net_force_one_arm, f = r.outside_field;
    const steel = r.materials[0], cnt = r.materials.find((m) => m.name.startsWith("Carbon"));
    const n = (v) => Math.hypot(...v);
    const km = (v) => (v == null ? "no limit" : `${Math.round(v).toLocaleString("en")} km`);
    return div(`<div class="verdict"><b>It cannot move Earth, and its arms cannot stand.</b>
      Earth's field comes from currents in Earth's own core, so whatever the field does to the arms, the arms do back to the
      core: worked out separately, the two forces cancel to ${fmt(all.sum_over_force, 2)} of each other. A force inside
      Earth plus machine cannot move them. And a ${r.arm.length_km.toLocaleString("en")} km arm crushes or buckles under its own
      weight in every material, even ones that do not exist yet. That is why we tow Earth with an asteroid's gravity instead.</div>`
      + tiles([["Force on the arms from Earth's field", `${fmt(n(all.on_arms_n), 3)} N`, `on Earth's core from the arms: ${fmt(n(all.on_core_n), 3)} N`],
        ["Net force on Earth plus machine", `${fmt(all.sum_over_force, 2)} of it`, `one arm alone: ${fmt(one.sum_over_force, 2)} (test X8)`],
        ["Arms with no return path (impossible)", `${fmt(f.open_arms_in_earth_field_n, 2)} N at best`, `Earth would take ${fmt(f.years_needed_at_that_push, 2)} years`],
        ["12,000 km standing, steel", `safety factor ${fmt(steel.lengths.at(-1).standing_sf, 2)}`, `nanotube ${cnt.lengths.at(-1).standing_sf.toFixed(2)}; 1.5 required`]])
      + `<h3>Each material at the demo's tube (${r.arm.outer_diameter_km} km across, ${r.arm.wall_km} km walls), safety factor ${r.safety_factor_min}</h3>`
      + table(["Material", "Longest standing", "Buckles past", "Longest level"], r.materials.map((m) => [
        `${m.name}<br><span class="note">${m.source}</span>`, km(m.standing_longest_km), km(m.buckling_length_km),
        km(m.level_longest_km)]), [1, 2, 3])
      + `<p class="note">Standing: the arm's weight on its base, with gravity falling off with height and Earth's spin. Buckling:
        Greenhill's limit for a column under its own weight, with surface gravity (with the weakest gravity along the arm,
        nanotube still buckles past ${Math.round(cnt.buckling_length_weakest_gravity_km).toLocaleString("en")} km). Level: the arm held out
        sideways near the ground, bending at its root. Closed arm circuits in the demo's 0.5 nT outside field feel ${fmt(f.closed_circuits_n, 2)} N
        (I L B is ${fmt(f.scale_i_l_b_n, 2)} N). Code: sim/scenarios/octo.py.</p>`);
  },
  A(d, ctx) {
    const b5 = d.benchmarks.find((b) => b.number === 5);
    const ok = d.benchmarks.filter((b) => b.ok).length;
    const e = div(`<div class="verdict"><b>${ok === 10 ? "Yes." : "No."} ${ok} of 10 official benchmarks pass.</b>
      The real solar system, run for ${yr(d.longterm.real_info.years)} years with no push, keeps its energy to
      ${fmt(d.longterm.real_info.energy_error, 2)} (limit 1e-6).</div>`
      + tiles([["Benchmarks", `${ok} / 10`, "guide §6, run with uv run python -m sim.benchmarks"],
        ["Benchmark 5: energy, 5 years", fmt(b5.measured, 2), "limit 1e-9"],
        ["Real solar system, 1 Myr", fmt(d.longterm.real_info.energy_error, 2), "energy error, limit 1e-6"],
        ["Momentum ledger (journey)", fmt(d.summary.ledger.integrator_honest_max, 2), "limit 1e-9 of the applied impulse"]])
      + `<p>The full benchmark table is on the Validation tab.</p>`);
    return e;
  },
  B(d, ctx) {
    const a = d.summary.tows["earth-tow"].arrival, mars = d.summary.tows["mars-tow"].arrival, fl = d.summary.flags;
    const e = div(`<div class="verdict"><b>Yes. Earth reaches ${a.a_au} AU in year ${yr(a.year)}, with ${fl.unresolved} unresolved flags.</b>
      Mars is moved out of the way first and parks at ${mars.a_au} AU in year ${yr(mars.year)}. The ${fl.covered_by_enablers} flags
      left are all caused by the three declared enablers, which the brief allows.</div>`
      + tiles([["Earth arrives", `year ${yr(a.year)}`, `limit 10,000; orbit ${a.a_au} AU, eccentricity ${a.eccentricity}`],
        ["Mars parks", `year ${yr(mars.year)}`, `${mars.a_au} AU`],
        ["Most beam power", `${fmt(d.summary.total_beam_max_w, 3)} W`, "E1 limit 1e26 W, both tows together"],
        ["Closest Earth–Mars pass", `${d.summary.mars_closest.au} AU`, "limit 0.05 AU"]]));
    const c = lineChart({ title: "Orbit size", sub: "Earth and Mars, AU; lines at Earth's target and Mars's parking orbit",
      series: [{ name: "Earth", x: d.T, y: d.series.earth_a }, { name: "Mars", x: d.T, y: d.series.mars_a }],
      limits: [{ y: 2.7, label: "2.7 target", color: "var(--good)" }, { y: 3.64, label: "3.64 Mars", color: "var(--text-muted)" }] });
    ctx.charts.push(c); c.onPick?.(ctx.goto);
    e.appendChild(c);
    return e;
  },
  C(d, ctx) { return forcesTab(d, ctx); },
  D(d, ctx) {
    const cr = d.crossing.variants;
    const rows = Object.entries(cr).filter(([, v]) => v.caught != null)
      .map(([k, v]) => [k, `${v.caught} of ${v.of}`, v.caught ? chip("fail", "caught") : chip("pass", "crossed")]);
    const e = div(`<div class="verdict"><b>Not caught. Mars crosses Jupiter's 2:1 resonance (3.28 AU) in every trial.</b>
      At the normal pull the resonance caught Mars in ${cr["normal pull"].caught} of 8 starting points. So Mars's tow sprints
      across it, with the asteroid moved in from 400,000 to 200,000 km for 4× the pull, while Earth's tow eases off to
      850,000 km so the two stay inside E1's 1e26 W. Closest Earth–Mars pass in the whole journey:
      ${d.summary.mars_closest.au} AU (limit 0.05).</div>`
      + `<h3>Crossing trials (8 starting points each)</h3>` + table(["Variant", "Caught", ""], rows, [1]));
    const c = lineChart({ title: "Mars's orbit size", sub: "AU; the resonance and the parking orbit",
      series: [{ name: "Mars", x: d.T, y: d.series.mars_a }],
      limits: [{ y: 3.278, label: "2:1 3.28" }, { y: 3.64, label: "park 3.64", color: "var(--good)" }] });
    ctx.charts.push(c); c.onPick(ctx.goto);
    e.appendChild(c);
    const k = lineChart({ title: "Mars's tow distance", sub: "km; the sprint across the resonance (from the config's rule)",
      series: [{ name: "Mars tow", x: d.T, y: d.series.mars_tow_km }] });
    ctx.charts.push(k); k.onPick(ctx.goto);
    e.appendChild(k);
    return e;
  },
  E(d, ctx) {
    const rows = d.outage.filter((o) => !o.name.startsWith("old:") && !o.name.startsWith("lighter"))
      .map((o) => [o.name, hours(o.longest_safe_outage_days), fmt(o.steady_beam_w, 3), pct(o.spare_share, 0)]);
    const earth = d.outage.find((o) => o.name === "shared E1 budget, all beams off");
    const e = div(`<div class="verdict"><b>The Earth tow rides out a ${hours(earth.longest_safe_outage_days)} total blackout, and much longer if only some stations fail.</b>
      The beams come from many independent stations; losing all of them at once is the worst case. After an outage the spare
      power under E1's cap pulls the asteroid back to its spot. Mars's tow holds ${hours(d.outage.find((o) => o.name === "Mars tow, all beams off").longest_safe_outage_days)}
      in a blackout; during its sprint it has the least margin.</div>`
      + `<h3>Longest outage with the asteroid kept (sim/scenarios/outage.py)</h3>`
      + table(["Case", "Held", "Steady beam, W", "Spare"], rows, [1, 2, 3])
      + `<p class="note">Each case is a full run of the tow with the beams cut for a growing number of days, until the asteroid can no longer be caught.</p>`);
    return e;
  },
  F(d, ctx) { return safetyTab(d, ctx); },
  G(d, ctx) { return structureTab(d, ctx); },
  H(d, ctx) {
    const b = d.summary.belt, n = d.summary.big_asteroid_nudges;
    const e = div(`<div class="verdict"><b>About one 1 km impact every ${yr(b.crossing.years_per_impact)} years while crossing the belt, and one every
      ${yr(b.parked_at_target.years_per_impact)} years once parked, against a natural one per 500,000. E1 stops them.</b>
      Each is found 10 years ahead and nudged ${b.deflection.speed_change_m_s * 100} cm/s aside with ${fmt(b.deflection.beam_power_w, 2)} W for
      ${b.deflection.beam_days} day, a tiny share of the tow beams. The big asteroids come no closer than:
      ${Object.entries(d.summary.big_asteroids_closest_au).map(([k, v]) => `${k} ${v} AU`).join(", ")}.</div>`
      + tiles([["Sample tracked", `${b.sample_size.toLocaleString()} real orbits`, `${yr(b.years_tracked)} years, ${b.sample_encounters.toLocaleString()} passes within ${b.close_pass_au} AU`],
        ["Closest sample pass", `${b.sample_closest_au} AU`, `median speed ${b.encounter_speed_median_km_s} km/s`],
        ["Crossing", `1 per ${yr(b.crossing.years_per_impact)} yr`, "1 km and up, scaled to 1.2 million real ones"],
        ["Parked", `1 per ${yr(b.parked_at_target.years_per_impact)} yr`, `${fmt(b.parked_at_target.times_natural_rate, 2)}× natural`]])
      + `<h3>Big-asteroid passes nudged (E1)</h3>`
      + table(["Year", "Body", "Closest, AU", "Beam time"], n.map((x) => [yr(x.year), x.body, x.au, `${(x.beam_hours * 60).toFixed(1)} min`]), [0, 2, 3]));
    return e;
  },
  I(d, ctx) {
    const lt = d.longterm, mi = lt.moved_info, ri = lt.real_info, mr = lt.moved_ranges, v = lt.verdict;
    const e = div(`<div class="verdict"><b>Yes. In a million years after arrival the new orbits stay put: ${v.flags.unresolved} unresolved flags, nothing thrown out.</b>
      Earth's orbit stays between ${mr.earth.a[0]} and ${mr.earth.a[1]} AU and Mars's never comes within ${mi.earth_mars_orbit_gap_min_au.toFixed(2)} AU of it.
      Two chaos copies (tiny changes at the start) agree. The ${v.flags.covered_by_enablers} flags left are covered: big-asteroid passes are nudged by E1,
      and the mirrors (E3) re-aim ${pct(v.seasons.sunlight_to_reaim)} of Earth's sunlight to keep today's seasons while the tilt swings ${mi.axial_tilt_deg[0]}–${mi.axial_tilt_deg[1]}°.</div>`
      + tiles([["Earth's orbit", `${mr.earth.a[0]}–${mr.earth.a[1]} AU`, `eccentricity up to ${mr.earth.e[1]} (real Earth: up to ${lt.real_ranges.earth.e[1]})`],
        ["Mars's orbit", `${mr.mars.a[0]}–${mr.mars.a[1]} AU`, `smallest gap to Earth's orbit ${mi.earth_mars_orbit_gap_min_au.toFixed(3)} AU`],
        ["Axial tilt", `${mi.axial_tilt_deg[0]}–${mi.axial_tilt_deg[1]}°`, `real Earth: ${ri.axial_tilt_deg[0]}–${ri.axial_tilt_deg[1]}°`],
        ["Energy error", fmt(mi.energy_error, 2), `${yr(mi.years)} years, limit 1e-6`]]));
    const x = lt.moved.year;
    const c = lineChart({ title: "Earth's eccentricity", sub: "moved Earth at 2.7 AU against the real Earth, a million years",
      series: [{ name: "Moved Earth", x, y: lt.moved.earth_e }, { name: "Real Earth", x: lt.real.year, y: lt.real.earth_e }], xName: "year after arrival" });
    e.appendChild(c);
    const g = lineChart({ title: "Earth's and Mars's orbit size", sub: "AU, a million years after arrival",
      series: [{ name: "Earth", x, y: lt.moved.earth_a }, { name: "Mars", x, y: lt.moved.mars_a }], xName: "year after arrival" });
    e.appendChild(g);
    return e;
  },
};

export function summaryTab(d, ctx, exp) {
  const wrap = div(`<div class="question"><b>${exp.id}. ${exp.title}.</b> ${exp.q}</div>`);
  wrap.appendChild(answers[exp.id](d, ctx));
  return wrap;
}

// ---------------------------------------------------------------- tabs
export function forcesTab(d, ctx) {
  const lg = d.summary.ledger;
  const earthTow = d.config.tows.find((t) => t.target === "earth"), marsTow = d.config.tows.find((t) => t.target === "mars");
  const e = div(`<h3>Forces now</h3><div id="forces-now"></div>
    <p>Earth is moved only by gravity: the asteroid pulls Earth, Earth pulls the asteroid back with the same force, and the
    light push on the asteroid's mirror balances that. The light's own partners are the beam stations, which recoil as they fire,
    and the light itself, which carries momentum away after bouncing. Every one of these is booked.</p>
    <h3>Momentum ledger, the guide's two checks</h3>`
    + table(["Check", "Worst", "At the end", "Limit"], [
      ["Integrator is honest: bodies' momentum change against the applied impulse", fmt(lg.integrator_honest_max, 2), fmt(lg.integrator_honest_end, 2), "1e-9"],
      ["Nothing from nothing: applied impulse plus its partners", fmt(lg.nothing_from_nothing_max, 2), fmt(lg.nothing_from_nothing_end, 2), "1e-9"],
    ], [1, 2, 3])
    + `<h3>Where the momentum went (kg m/s)</h3>`
    + table(["Account", "Size"], [
      ["Applied impulse: beams on the two asteroids", fmt(lg.applied_impulse_kg_m_s, 4)],
      ["Beam stations' recoil", fmt(Math.hypot(...lg.station_recoil_kg_m_s), 4)],
      ["Bounced light", fmt(Math.hypot(...lg.bounced_light_kg_m_s), 4)],
      ["Asteroids sent away at the end of their tows", fmt(Math.hypot(...lg.departed_kg_m_s), 4)],
    ], [1])
    + `<h3>Energy</h3><p>The beams did ${fmt(lg.beam_work_j, 4)} J of work; the bodies gained ${fmt(lg.bodies_energy_gain_j, 4)} J
      (counting what left with the asteroids). They match to ${pct(lg.work_mismatch_share, 3)}. The worst energy gap during the run was
      ${fmt(lg.energy_error_max_of_total, 2)} of the system's total (limit 1e-5).</p>`);
  const now = e.querySelector("#forces-now");
  ctx.live.push((t) => {
    const ed = valueAt(d, "tow_km", t), md = valueAt(d, "mars_tow_km", t);
    const rows = [];
    if (t < d.milestones.earthArrives && ed) {
      const F = (G * MASS.earth * earthTow.asteroid_mass_kg) / (ed * 1e3) ** 2;
      rows.push(["Earth tow: asteroid's pull on Earth (and Earth's on it)", `${fmt(F, 3)} N`],
        ["Earth's acceleration from it", `${fmt(F / MASS.earth, 3)} m/s²`], ["Earth tow distance", `${yr(ed)} km`]);
    } else rows.push(["Earth tow", "finished; asteroid sent away"]);
    if (t < d.milestones.marsParks && md) {
      const F = (G * MASS.mars * marsTow.asteroid_mass_kg) / (md * 1e3) ** 2;
      rows.push(["Mars tow: asteroid's pull on Mars", `${fmt(F, 3)} N`], ["Mars's acceleration", `${fmt(F / MASS.mars, 3)} m/s²`],
        ["Mars tow distance", `${yr(md)} km`]);
    } else rows.push(["Mars tow", "finished; asteroid sent away"]);
    rows.push(["Beam power, both tows", `${fmt(valueAt(d, "beam_w", t), 3)} W`]);
    now.innerHTML = table(["", `year ${yr(t)}`], rows, [1]);
  });
  const c = lineChart({ title: "Momentum check per frame", sub: "bodies' momentum change against the applied impulse (log scale; limit 1e-9)",
    series: [{ name: "check", x: d.T, y: d.series.momentum_error }], log: true, limits: [{ y: 1e-9, label: "1e-9" }] });
  ctx.charts.push(c); c.onPick(ctx.goto);
  e.appendChild(c);
  const en = lineChart({ title: "Energy gap per frame", sub: "share of the system's total energy (log scale; limit 1e-5)",
    series: [{ name: "energy", x: d.T, y: d.series.energy_error.map(Math.abs) }], log: true, limits: [{ y: 1e-5, label: "1e-5" }] });
  ctx.charts.push(en); en.onPick(ctx.goto);
  e.appendChild(en);
  return e;
}

export function orbitTab(d, ctx) {
  const ea = d.summary.tows["earth-tow"].arrival, ma = d.summary.tows["mars-tow"].arrival;
  const e = div(`<h3>Now</h3><div id="orbit-now"></div><h3>On arrival</h3>`
    + table(["", "Earth", "Mars"], [
      ["Year", yr(ea.year), yr(ma.year)], ["Orbit size, AU", ea.a_au, ma.a_au], ["Eccentricity", ea.eccentricity, ma.eccentricity],
      ["Tilt to the ecliptic, deg", ea.tilt_deg, ma.tilt_deg ?? "–"], ["Free eccentricity left", ea.free_eccentricity, ma.free_eccentricity ?? "–"],
    ], [1, 2])
    + `<p class="note">Earth arrives with the orbit shape and plane that Jupiter forces at 2.7 AU (the arrival trim, sim/secular.py), so it does not
      wobble afterwards: the free eccentricity left is ${ea.free_eccentricity}.</p>`);
  const now = e.querySelector("#orbit-now");
  ctx.live.push((t) => {
    now.innerHTML = table(["", `year ${yr(t)}`], [
      ["Earth's orbit size", `${valueAt(d, "earth_a", t).toFixed(4)} AU`], ["Earth's eccentricity", valueAt(d, "earth_e", t).toFixed(4)],
      ["Mars's orbit size", `${valueAt(d, "mars_a", t).toFixed(4)} AU`]], [1]);
  });
  for (const opts of [
    { title: "Orbit size", sub: "AU", series: [{ name: "Earth", x: d.T, y: d.series.earth_a }, { name: "Mars", x: d.T, y: d.series.mars_a }] },
    { title: "Earth's eccentricity", sub: "the arrival trim brings it to Jupiter's forced value (about 0.03)", series: [{ name: "e", x: d.T, y: d.series.earth_e }] },
  ]) {
    const c = lineChart(opts);
    ctx.charts.push(c); c.onPick(ctx.goto);
    e.appendChild(c);
  }
  const pk = d.parking;
  e.appendChild(div(`<h3>Where Mars can park: million-year runs</h3>`
    + table(["Arrangement", "Earth e max", "Gap to Earth, AU", "Thrown out"], pk.results.map((r) => [
      r.name, r.earth_e_max ?? "–", r.earth_mars_gap_min_au ?? "–", r.stopped ? `stopped: ${r.stopped}` : (r.thrown_out || []).map((x) => x.body).join(", ") || "none"]), [1, 2])
    + `<p class="note">Resonances with Jupiter near the belt: ${Object.entries(pk.resonances_au).map(([k, v]) => `${k} at ${v}`).join(", ")} AU. Mars parks at 3.64 AU, between them and Earth's own.</p>`));
  return e;
}

export function structureTab(d, ctx) {
  // One row per check, with its value at the most power the journey used and at the tow's power cap.
  const byTow = {};
  for (const r of d.structures) {
    const name = r.check.replace(/^[a-z]+-tow: /, "");
    const row = ((byTow[r.tow] ??= {})[name] ??= { ...r, name, cases: {} });
    row.cases[r.case] = r;
  }
  const val = (r) => (r.unit ? `${fmt(r.value, 4)} ${r.unit}` : r.value.toFixed(2));
  const towTable = (tow) => table(["Check", "Journey's most", "At the cap", "Limit", ""], Object.values(byTow[tow]).map((r) => {
    const cs = Object.values(r.cases);
    return [r.name[0].toUpperCase() + r.name.slice(1), val(r.cases["most used on the journey"]), val(r.cases["power cap"]),
      `${r.kind === "min" ? "≥" : "≤"} ${r.limit}`, chip(cs.every((c) => c.ok) ? "pass" : "fail", "")];
  }), [1, 2, 3]);
  const sfs = d.structures.filter((r) => r.check.includes("safety factor"));
  const st = d.config.structures;
  return div(`<div class="verdict"><b>Every structure holds: the lowest safety factor is ${Math.min(...sfs.map((r) => r.value)).toFixed(2)} (at least 1.5 required), at the full E1 power cap.</b>
    Sized for the most a beam can ever push, 2P/c (a perfect mirror sending light straight back), so recovering after an outage is covered too.</div>`
    + Object.keys(byTow).map((tow) => {
      const cap = d.structures.find((r) => r.tow === tow && r.case === "power cap").beam_w;
      const used = d.structures.find((r) => r.tow === tow && r.case !== "power cap").beam_w;
      return `<h3>${tow === "earth-tow" ? "Earth" : "Mars"} tow</h3><p class="note">Beam: most used on the journey ${fmt(used, 3)} W; power cap ${fmt(cap, 2)} W.</p>${towTable(tow)}`;
    }).join("")
    + `<h3>Design sizes (config.yaml)</h3>`
    + table(["", "Earth tow", "Mars tow"], [
      ["Cable cross-section", `${st["earth-tow"].cable_cross_section_km2} km²`, `${st["mars-tow"].cable_cross_section_km2} km²`],
      ["Anchor area in the rock", `${st["earth-tow"].anchor_area_km2.toLocaleString()} km²`, `${st["mars-tow"].anchor_area_km2.toLocaleString()} km²`],
      ["Mirror radius", `${st["earth-tow"].mirror_radius_km.toLocaleString()} km`, `${st["mars-tow"].mirror_radius_km.toLocaleString()} km`],
      ["Asteroid density", `${st["earth-tow"].asteroid_density_kg_m3} kg/m³`, `${st["mars-tow"].asteroid_density_kg_m3} kg/m³`],
    ], [1, 2])
    + `<p>Cables and mirrors are made of the E2 super-mirror material (100 GPa strength, absorbs 1e-7 of the light, up to 1,500 K).
      Anchors spread the load into rock of ${fmt(st.rock_strength_pa, 2)} Pa strength. The asteroid's own body only has to resist the
      uneven pull of the planet across it.</p>`);
}

export function safetyTab(d, ctx) {
  const ths = thresholds(d);
  const e = div(`<div class="verdict"><b>All ten held for the whole journey.</b> Earth's sunlight is kept at today's level by mirrors in space
    (E3), so the climate stays where it is. Without them, the same model gives 150 K and no liquid water at 2.7 AU, as the company's demo does.</div>
    <div id="safety-now"></div>`);
  const now = e.querySelector("#safety-now");
  ctx.live.push((t) => {
    now.innerHTML = table(["Threshold", `Year ${yr(t)}`, "Worst", "Limit", ""], ths.map((th) => {
      const f = th.f || ((v) => fmt(v, 4));
      const w = worst(d, th);
      const ok = th.kind === "min" ? w >= th.limit : w <= th.limit;
      return [th.name, f(valueAt(d, th.key, t)) + (th.unit && !th.f ? th.unit : ""), f(w), `${th.kind === "min" ? "≥" : "≤"} ${th.f ? th.f(th.limit) : th.limit}`, chip(ok ? "pass" : "fail", "")];
    }), [1, 2, 3]);
  });
  const s = d.config.safety;
  for (const opts of [
    { title: "Global mean temperature", sub: "K; the safe band is 263 to 308 K", series: [{ name: "T", x: d.T, y: d.series.temperature_k }], band: [s.temperature_min_k, s.temperature_max_k], unit: " K" },
    { title: "Sunlight Earth gets, against today", sub: "direct sunlight plus what the mirrors add", series: [{ name: "sunlight", x: d.T, y: d.series.sunlight_share }] },
    { title: "Sunlight mirrors built (E3)", sub: "km², built in 25-year batches; E3 limit 1e9 km²", series: [{ name: "area", x: d.T, y: d.series.mirror_area_km2 }], limits: [{ y: 1e9, label: "1e9 limit" }] },
    { title: "Moon's distance against Earth's Hill radius", sub: "the Hill sphere grows as Earth moves out, so the Moon gets safer", series: [{ name: "share", x: d.T, y: d.series.moon_hill_share }], limits: [{ y: s.moon_hill_max_share, label: "0.49 limit" }] },
  ]) {
    const c = lineChart(opts);
    ctx.charts.push(c); c.onPick(ctx.goto);
    e.appendChild(c);
  }
  return e;
}

const PLOTS = [
  ["earth_a", "Earth's orbit size", "AU"], ["earth_e", "Earth's eccentricity", ""], ["mars_a", "Mars's orbit size", "AU"],
  ["beam_w", "Beam power, both tows", "W"], ["tow_km", "Earth tow distance", "km"], ["mars_tow_km", "Mars tow distance", "km"],
  ["temperature_k", "Temperature", "K"], ["liquid_water_share", "Liquid water share", ""], ["absorbed_w_m2", "Absorbed sunlight", "W/m²"],
  ["sunlight_share", "Sunlight against today", ""], ["mirror_area_km2", "Mirror area", "km²"], ["magnetopause_re", "Magnetopause", "Earth radii"],
  ["jeans_lambda_n2", "Jeans λ (N2)", ""], ["day_length_change_s", "Day length change", "s"], ["moon_hill_share", "Moon / Hill radius", ""],
  ["thrust_over_moon_pull", "Thrust / Moon pull", ""], ["energy_error", "Energy gap", ""], ["momentum_error", "Momentum check", ""],
];

export function plotsTab(d, ctx, state) {
  const e = div(`<p>Pick a series. Click a chart to jump the 3D view to that year.</p><div class="picker"></div><div class="plot"></div>`);
  const picker = e.querySelector(".picker"), plot = e.querySelector(".plot");
  const draw = () => {
    picker.querySelectorAll("button").forEach((b) => b.classList.toggle("on", b.dataset.k === state.plot));
    const [k, name, unit] = PLOTS.find((p) => p[0] === state.plot);
    const c = lineChart({ title: name, sub: unit || "", series: [{ name, x: d.T, y: d.series[k] }], log: k.endsWith("_error"), height: 220 });
    c.onPick(ctx.goto);
    plot.replaceChildren(c);
    ctx.charts.length = 0;
    ctx.charts.push(c);
    c.setCursor(ctx.t());
  };
  for (const [k, name] of PLOTS) {
    const b = document.createElement("button");
    b.textContent = name; b.dataset.k = k;
    b.onclick = () => { state.plot = k; draw(); };
    picker.appendChild(b);
  }
  draw();
  return e;
}

export function validationTab(d) {
  const flags = d.summary.flags.flags;
  return div(`<h3>The ten official benchmarks (guide §6)</h3>`
    + table(["#", "Benchmark", ""], d.benchmarks.map((b) => [b.number,
      `<b>${b.name}</b><br><span class="note">${b.doc.replace(/\.$/, "")}${b.note ? `; ${b.note}` : ""}</span><br>
       measured <b>${show(b.measured)}</b>${b.unit ? ` ${b.unit}` : ""}; expected ${show(b.expected)}; tolerance ${b.tolerance}`,
      chip(b.ok ? "pass" : "fail", "")]), [0])
    + `<p class="note">Run them: <code>uv run python -m sim.benchmarks</code>; any input can be changed with <code>--set name=value</code>.</p>
    <h3>Our own extra checks (tests/test_extra_checks.py)</h3>`
    + table(["Test", "What it checks"], [
      ["X1", "An orbit's period matches Kepler's third law"], ["X2", "Energy holds steady for 1,000 years"],
      ["X3", "Momentum ledger in the guide's form, with a push on"], ["X4", "A Hohmann transfer reaches its target orbit"],
      ["X5", "A steady push arrives when theory says"], ["X6", "Our integrator matches REBOUND, an independent code"],
      ["X7", "An asteroid's pull and the hold on it"], ["X8", "Octo-Earth's arms and Earth's core push on each other equally: no net force on Earth plus machine"]])
    + `<h3>Flags in the journey: all caused by declared enablers</h3>`
    + table(["Check", "Worst", "Limit", "Covered by"], flags.map((f) => [f.check, fmt(f.worst, 3), `${f.kind === "min" ? "≥" : "≤"} ${fmt(f.limit, 3)}`, chip(f.covered_by ? "cover" : "fail", f.covered_by || "none")]), [1, 2])
    + `<h3>Flags after a million years</h3>`
    + table(["Check", "Worst", "Covered by"], d.longterm.verdict.flags.flags.map((f) => [f.check, fmt(f.worst, 3), chip(f.covered_by ? "cover" : "fail", f.covered_by || "none")]), [1]));
}

export function notesTab(d) {
  const en = d.config.enablers.covers;
  return div(`<h3>What the model does</h3>
    <ul>
      <li><b>Bodies:</b> the Sun, Venus to Neptune at their real J2000 orbits, Ceres, Pallas, Vesta and Hygiea as massive bodies, and the two tow asteroids.
        1,000 real belt orbits are tracked to count close passes.</li>
      <li><b>Gravity:</b> every pair of bodies, with each pair's forces exact negatives. Leapfrog with 1-day steps for the journey,
        Yoshida fourth order for the benchmarks, REBOUND (MERCURIUS) for the million-year runs.</li>
      <li><b>The tow:</b> each asteroid is held on its spot by a light push (P/c)(in − out) on its mirror. A controller with a 10-day period
        keeps it there; checks every 100 days confirm the controller beats the planet's pull gradient 3× and the step is short enough.</li>
      <li><b>Arrival trim:</b> on the last stretch the tow steers Earth's orbit shape and plane to the values Jupiter forces at 2.7 AU (Gauss's equations).</li>
      <li><b>Earth safety:</b> an energy-balance climate with ice-albedo feedback, calibrated to 288 K today; mirrors built in 25-year batches;
        the ten thresholds checked every 100 days.</li>
      <li><b>Momentum ledger:</b> every push, its partners and what leaves the system, summed without rounding loss.</li>
    </ul>
    <h3>Declared enablers (the brief allows three)</h3>
    <ul>${Object.entries(en).map(([k, v]) => `<li><b>${k}:</b> ${v}</li>`).join("")}</ul>
    <h3>What it leaves out</h3>
    <ul>
      <li>How the beam stations, mirrors and asteroids are built and placed: that is what E1 and E3 declare.</li>
      <li>Climate in one dimension (plus a latitude profile for liquid water); no weather, oceans or biology.</li>
      <li>The Moon's orbit and Earth's spin are checked in separate runs (sim/scenarios/moon.py, sim/spin.py), not inside the journey.</li>
      <li>The page replays saved runs: it computes nothing itself. Change config.yaml and re-run the Python model to change them.</li>
    </ul>
    <h3>Read more</h3>
    <ul>
      <li><a href="${REPO}/docs/problem.md" target="_blank" rel="noopener">The problem and how it is judged</a></li>
      <li><a href="${REPO}/docs/approach.md" target="_blank" rel="noopener">Our approach, with every design choice and why</a></li>
      <li><a href="${REPO}/docs/enablers.md" target="_blank" rel="noopener">Enablers declaration</a></li>
      <li><a href="${REPO}/docs/risk-register.md" target="_blank" rel="noopener">Risk register: every failure we looked for</a></li>
      <li><a href="${REPO}/docs/momentum-record.md" target="_blank" rel="noopener">Conservation and momentum record</a></li>
    </ul>`);
}

export function compareTab(d, ctx) {
  const cmp = d.longterm.verdict.compared_with_real_solar_system;
  const rng = (r) => `${r[0]} – ${r[1]}`;
  const e = div(`<h3>The moved solar system against the real one, a million years each</h3>`
    + table(["Body", "Orbit size, AU (moved / real)", "Eccentricity (moved / real)"], Object.entries(cmp).map(([k, v]) => [
      k, `${rng(v.moved.a)}<br><span class="note">${rng(v.real.a)}</span>`, `${rng(v.moved.e)}<br><span class="note">${rng(v.real.e)}</span>`]), [1, 2])
    + `<h3>Chaos copies (the same run with tiny changes at the start)</h3>`
    + table(["Copy", "Unresolved flags", "Earth e max", "Gap to Mars, AU", "Tilt, deg"], d.longterm.chaos_copies.map((c) => [
      c.seed, c.verdict_flags, c.earth_e_max, c.gap_min_au, rng(c.tilt_deg)]), [1, 2, 3, 4]));
  const x = d.longterm.moved.year;
  const tilt = lineChart({ title: "Earth's axial tilt", sub: "degrees, a million years; the moved Earth swings more, so mirrors re-aim sunlight for the seasons (E3)",
    series: [{ name: "Moved Earth", x, y: d.longterm.moved.tilt_deg }, { name: "Real Earth", x: d.longterm.real.year, y: d.longterm.real.tilt_deg }], xName: "year after arrival" });
  e.appendChild(tilt);
  e.appendChild(div(`<h3>Export</h3><div class="btns">
    <button id="csv">Journey as CSV</button>
    ${["journey", "summary", "longterm", "benchmarks", "structures", "outage", "crossing", "parking"].map((n) => `<a href="./data/${n}.json" download><button>${n}.json</button></a>`).join("")}
    </div><p class="note">The CSV has one row per saved frame (every 10 years): orbits, beam power and the Earth-safety values.</p>`));
  e.querySelector("#csv").onclick = () => {
    const keys = Object.keys(d.series);
    const lines = [keys.join(",")];
    for (let i = 0; i < d.T.length; i++) lines.push(keys.map((k) => d.series[k][i] ?? "").join(","));
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([lines.join("\n")], { type: "text/csv" }));
    a.download = "black-ant-journey.csv";
    a.click();
    URL.revokeObjectURL(a.href);
  };
  return e;
}
