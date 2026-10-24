// Live estimates behind the sliders: the formulas of sim/habitability.py and sim/night.py with the constants the
// Python model exports (config.json, "constants"), and the tow's spiral time. The saved run stays the official
// result; the page marks every number from here with ≈.
import { valueAt } from "./data.js";

const DEG = Math.PI / 180;

export function makeModel(d) {
  const k = d.config.constants, hab = d.config.habitability, night = d.config.night;
  const rho = hab.mirror_reflectivity;
  const R = k.earth_radius_m;
  const discKm2 = (Math.PI * R * R) / 1e6;
  const nightM2 = 2 * Math.PI * R * R;
  const earthMass = hab.earth_mass_with_moon_kg;
  const marsMass = d.config.planets.find((p) => p.name === "mars").mass_kg;
  const earthTow = d.config.tows.find((t) => t.target === "earth");
  const marsTow = d.config.tows.find((t) => t.target === "mars");

  // Climate (sim/habitability.py)
  const mir2 = (a, e = 0) => 1 / (a * a * Math.sqrt(1 - e * e));
  const albedoAt = (t) => (t >= k.warm_k ? k.warm_albedo : t <= k.ice_k ? k.ice_albedo
    : k.ice_albedo + ((k.warm_albedo - k.ice_albedo) * (t - k.ice_k)) / (k.warm_k - k.ice_k));
  function temperature(flux, start = k.today_mean_k) {
    let t = start;
    for (let i = 0; i < 500; i++) {
      const next = Math.pow((flux * (1 - albedoAt(t))) / (4 * k.emissivity * k.sigma), 0.25);
      if (Math.abs(next - t) < 1e-9) break;
      t = 0.5 * (t + next);
    }
    return t;
  }
  const absorbed = (flux, t) => (flux / 4) * (1 - albedoAt(t));
  function liquidWater(t) {
    const p2 = (273.15 - t) / k.latitude_t2_k;
    const x2 = (2 * p2 + 1) / 3;
    return Math.min(1, Math.max(0, Math.sqrt(Math.max(x2, 0))));
  }

  // Sunlight mirrors (E3): each square metre near Earth catches Earth's sunlight and sends `rho` of it on.
  const sunAreaNeeded = (a, e = 0) => (Math.max(0, 1 / mir2(a, e) - 1) * discKm2) / rho;
  const sunShare = (a, e, areaKm2) => mir2(a, e) * (1 + (rho * areaKm2) / discKm2);
  const mirrorPart = (areaKm2) => { const x = (rho * areaKm2) / discKm2; return x / (1 + x); };

  // Night light and Moon reflectors (sim/night.py)
  const phaseFactor = (deg) => (deg < 90 ? Math.cos((deg * DEG) / 2) : 0);
  const naturalLux = (a, e = 0) => night.full_moon_lux_today * mir2(a, e);
  const reflectorW = (areaKm2, a, e = 0, phase = 0) => areaKm2 * 1e6 * k.solar_constant * mir2(a, e) * rho * phaseFactor(phase);
  const reflectorLux = (areaKm2, a, e = 0, phase = 0) => (reflectorW(areaKm2, a, e, phase) / nightM2) * night.sunlight_lm_per_w;
  const moonAreaFor = (lux, a, e = 0) => Math.max(0, lux - naturalLux(a, e)) / reflectorLux(1, a, e);
  const nearSideKm2 = Math.PI * night.moon_radius_km ** 2;
  const spotKm = (a) => (d.config.moon.a_km * night.sun_diameter_1au_deg * DEG) / a;
  const nightHeating = (areaKm2, a, e = 0) => reflectorW(areaKm2, a, e) / nightM2;
  function warmingK(areaKm2, a, e, share) {
    const base = share * k.solar_constant;
    const extra = (reflectorW(areaKm2, a, e) * k.month_mean) / (Math.PI * R * R);
    const t0 = temperature(base);
    return temperature(base + extra, t0) - t0;
  }

  // The tow: pull G M m / d^2, the along-orbit share at 45 deg, and the light it takes, P = f c / (2 cos 45 deg).
  const pull = (massKg, distKm, target = earthMass) => (k.G * target * massKg) / (distKm * 1e3) ** 2;
  const beamW = (force) => force * k.c * Math.SQRT1_2;
  const vCirc = (a) => Math.sqrt(k.gm_sun / (a * k.au_m));
  // A slow spiral under a steady along-orbit push takes (v_start - v_end) / push.
  const spiralYears = (a0, a1, acc) => Math.abs(vCirc(a0) - vCirc(a1)) / acc / k.year_s;
  const a0 = d.series.earth_a[0];
  const arrival = d.summary.tows["earth-tow"].arrival;
  const accDesign = (pull(earthTow.asteroid_mass_kg, earthTow.distance_km) * Math.SQRT1_2) / earthMass;
  // The saved run against the ideal spiral: Earth's tow eases off while Mars sprints and the arrival trim weakens it.
  const calib = arrival.year / spiralYears(a0, arrival.a_au, accDesign);
  const marsBeam = beamW(pull(marsTow.asteroid_mass_kg, marsTow.distance_km, marsMass));

  function tow(w) {
    const F = pull(w.massKg, w.distKm), acc = (F * Math.SQRT1_2) / earthMass;
    const ideal = spiralYears(a0, w.target, acc);
    return { force: F, acc, beam: beamW(F), marsBeam, total: beamW(F) + marsBeam, ideal, years: ideal * calib,
      dv: Math.abs(vCirc(a0) - vCirc(w.target)) };
  }

  function warnings(a) {
    const out = [];
    const mars = d.config.planets.find((p) => p.name === "mars");
    const peri = mars.a_au * (1 - mars.e);
    const belt = d.journey.belt, res = d.parking.resonances_au, park = marsTow.stop_au;
    if (a < a0) out.push(["fail", "Inward: Earth would get more sunlight, and E3 can only add light, not shade it"]);
    if (a > peri - 0.05) out.push(["cover", `Crosses Mars's orbit (perihelion ${peri.toFixed(2)} AU): Mars must be towed out first`]);
    if (a >= belt.inner_au && a <= belt.outer_au) out.push(["cover", `Inside the asteroid belt (${belt.inner_au}–${belt.outer_au} AU): E1 must nudge asteroids`]);
    for (const [name, r] of Object.entries(res)) {
      if (Math.abs(a - r) < (name === "2:1" || name === "3:1" ? 0.08 : 0.015)) out.push([name === "2:1" || name === "3:1" ? "fail" : "info", `Next to Jupiter's ${name} resonance at ${r} AU`]);
    }
    if (Math.abs(a - park) < 0.35) out.push(["fail", `Too close to Mars's parking orbit (${park} AU)`]);
    if (a > park) out.push(["fail", "Beyond Mars's parking orbit: Mars would have to go even farther"]);
    return out;
  }

  // Everything the panels show about Earth at year t, with the what-if settings `w`.
  function state(t, w) {
    const a = valueAt(d, "earth_a", t), e = valueAt(d, "earth_e", t);
    const runSun = w.sunMode === "run";
    const sunArea = runSun ? valueAt(d, "mirror_area_km2", t) : w.sunSats * night.sunlight_satellite_unit_km2;
    const share = runSun ? valueAt(d, "sunlight_share", t) : sunShare(a, e, sunArea);
    const temp = runSun ? valueAt(d, "temperature_k", t) : temperature(share * k.solar_constant);
    const moonArea = w.moonMode === "auto" ? moonAreaFor(night.full_moon_lux_today, a, e) : w.moonPanels * night.moon_reflector_unit_km2;
    const yearDays = (2 * Math.PI * Math.sqrt((a * k.au_m) ** 3 / k.gm_sun)) / 86400;
    const mm = d.config.moon;
    const siderealMonth = (2 * Math.PI * Math.sqrt((mm.a_km * 1e3) ** 3 / (k.G * (mm.earth_mass_kg + mm.mass_kg)))) / 86400;
    const tide = (k.m_sun / (a * k.au_m) ** 3) / (mm.mass_kg / (mm.a_km * 1e3) ** 3);
    const m = d.milestones, belt = d.summary.belt;
    const impactEvery = t >= m.earthArrives ? belt.parked_at_target.years_per_impact
      : m.beltEntry != null && t >= m.beltEntry ? belt.crossing.years_per_impact : d.config.safety.natural_1km_impact_interval_years;
    return {
      a, e, speed: vCirc(a) / 1e3, yearDays, seasonDays: yearDays / 4,
      synodic: 1 / (1 / siderealMonth - 1 / yearDays),
      direct: mir2(a, e), share, sunArea, sunEst: !runSun, mirrorPart: mirrorPart(sunArea),
      sunSats: sunArea / night.sunlight_satellite_unit_km2, sunNeeded: sunAreaNeeded(a, e),
      temp, water: runSun ? valueAt(d, "liquid_water_share", t) : liquidWater(temp),
      absorbed: runSun ? valueAt(d, "absorbed_w_m2", t) : absorbed(share * k.solar_constant, temp),
      sunDeg: night.sun_diameter_1au_deg / a, dayLux: share * k.solar_constant * night.sunlight_lm_per_w,
      swing: ((1 + e) / (1 - e)) ** 2 - 1, tide, lightMin: (a * k.au_m) / k.c / 60,
      moonArea, moonPanels: moonArea / night.moon_reflector_unit_km2, moonEst: true,
      naturalLux: naturalLux(a, e), reflectorLux: reflectorLux(moonArea, a, e),
      phaseLux: reflectorLux(moonArea, a, e, w.phaseDeg ?? 0), monthLux: reflectorLux(moonArea, a, e) * k.month_mean,
      heating: nightHeating(moonArea, a, e), warming: warmingK(moonArea, a, e, share), moonW: reflectorW(moonArea, a, e),
      nearShare: moonArea / nearSideKm2, e3Total: sunArea + moonArea,
      magnetopause: valueAt(d, "magnetopause_re", t), hill: valueAt(d, "moon_hill_share", t),
      jeans: valueAt(d, "jeans_lambda_n2", t), lod: valueAt(d, "day_length_change_s", t), impactEvery,
    };
  }

  return {
    rho, discKm2, nearSideKm2, calib, a0, temperature, absorbed, liquidWater, sunAreaNeeded, sunShare, naturalLux,
    reflectorLux, moonAreaFor, spotKm, nightHeating, warmingK, tow, warnings, state, mir2,
    todayAbsorbed: absorbed(k.solar_constant, k.today_mean_k),
  };
}
