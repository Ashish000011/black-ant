// What the panels say about Earth at any year: the saved run's values, plus a few derived from them (year length,
// the Sun's size, tides, light time) and the Moon reflectors, which are not in the run. The reflectors use the
// formulas of sim/night.py with the constants the Python model exports (config.json, "constants"); the page marks
// them with ≈.
import { valueAt } from "./data.js";

export function makeModel(d) {
  const k = d.config.constants, hab = d.config.habitability, night = d.config.night;
  const rho = hab.mirror_reflectivity;
  const R = k.earth_radius_m;
  const discKm2 = (Math.PI * R * R) / 1e6;
  const nightM2 = 2 * Math.PI * R * R;

  const mir2 = (a, e = 0) => 1 / (a * a * Math.sqrt(1 - e * e));
  const vCirc = (a) => Math.sqrt(k.gm_sun / (a * k.au_m));
  // Sunlight mirrors (E3): each square metre near Earth catches Earth's sunlight and sends `rho` of it on.
  const mirrorPart = (areaKm2) => { const x = (rho * areaKm2) / discKm2; return x / (1 + x); };

  // Moon reflectors at full Moon (sim/night.py): flat mirrors on the near side, their light spread over the night side.
  const naturalLux = (a, e = 0) => night.full_moon_lux_today * mir2(a, e);
  const reflectorW = (areaKm2, a, e = 0) => areaKm2 * 1e6 * k.solar_constant * mir2(a, e) * rho;
  const reflectorLux = (areaKm2, a, e = 0) => (reflectorW(areaKm2, a, e) / nightM2) * night.sunlight_lm_per_w;
  // The area that brings full-Moon light back to today's.
  const moonAreaFor = (lux, a, e = 0) => Math.max(0, lux - naturalLux(a, e)) / reflectorLux(1, a, e);

  // Everything the panels show about Earth at year t. moonKm2: the Moon reflectors' area (default: enough for
  // today's full Moon).
  function state(t, moonKm2 = null) {
    const a = valueAt(d, "earth_a", t), e = valueAt(d, "earth_e", t);
    const sunArea = valueAt(d, "mirror_area_km2", t);
    const moonArea = moonKm2 ?? moonAreaFor(night.full_moon_lux_today, a, e);
    const yearDays = (2 * Math.PI * Math.sqrt((a * k.au_m) ** 3 / k.gm_sun)) / 86400;
    const mm = d.config.moon;
    const siderealMonth = (2 * Math.PI * Math.sqrt((mm.a_km * 1e3) ** 3 / (k.G * (mm.earth_mass_kg + mm.mass_kg)))) / 86400;
    const share = valueAt(d, "sunlight_share", t);
    const m = d.milestones, belt = d.summary.belt;
    const impactEvery = t >= m.earthArrives ? belt.parked_at_target.years_per_impact
      : m.beltEntry != null && t >= m.beltEntry ? belt.crossing.years_per_impact : d.config.safety.natural_1km_impact_interval_years;
    return {
      a, e, speed: vCirc(a) / 1e3, yearDays, seasonDays: yearDays / 4,
      synodic: 1 / (1 / siderealMonth - 1 / yearDays),
      direct: mir2(a, e), share, sunArea, mirrorPart: mirrorPart(sunArea), sunSats: sunArea / night.sunlight_satellite_unit_km2,
      temp: valueAt(d, "temperature_k", t), water: valueAt(d, "liquid_water_share", t), absorbed: valueAt(d, "absorbed_w_m2", t),
      sunDeg: night.sun_diameter_1au_deg / a, dayLux: share * k.solar_constant * night.sunlight_lm_per_w,
      swing: ((1 + e) / (1 - e)) ** 2 - 1, lightMin: (a * k.au_m) / k.c / 60,
      tide: (k.m_sun / (a * k.au_m) ** 3) / (mm.mass_kg / (mm.a_km * 1e3) ** 3),
      moonArea, moonPanels: moonArea / night.moon_reflector_unit_km2,
      naturalLux: naturalLux(a, e), reflectorLux: reflectorLux(moonArea, a, e), heating: reflectorW(moonArea, a, e) / nightM2,
      e3Total: sunArea + moonArea,
      magnetopause: valueAt(d, "magnetopause_re", t), hill: valueAt(d, "moon_hill_share", t),
      jeans: valueAt(d, "jeans_lambda_n2", t), lod: valueAt(d, "day_length_change_s", t), impactEvery,
    };
  }

  return { state };
}
