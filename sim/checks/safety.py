"""Earth-safety checks, run at every check step.

Each returns a check() result; limits come from config.yaml (safety and enablers sections).
"""

import math

from ..constants import C_LIGHT, G, YEAR
from ..flags import check
from ..habitability import (SOLAR_CONSTANT, absorbed_flux, day_length_rate, hill_share, jeans_lambda,
                            liquid_water_share, magnetopause_re, mean_temperature, thrust_over_moon_pull)

R_EARTH = 6.371e6
MOON_MASS = 7.342e22
MOON_DISTANCE = 3.844e8
SOLAR_CONSTANT = 1361.0                                # W/m^2 at 1 AU
EARTH_SUNLIGHT_W = SOLAR_CONSTANT * math.pi * R_EARTH ** 2  # all sunlight Earth catches today (mirrors keep it)


def safety_checks(cfg: dict, earth_au: float, tow_mass: float | None, tow_distance: float | None,
                  beam_power: float, earth_e: float = 0.0167, mirrors=None, climate: dict | None = None,
                  year: float = 0.0) -> list[dict]:
    """Earth's safety at one moment: the ten indicators of the company's reference demo plus our own. With
    `mirrors` (habitability.Mirrors, already updated), sunlight comes from the mirrors actually built; `climate`
    keeps the climate's state between calls (temperature, day-length change) and the ranges for the summary."""
    s, en = cfg["safety"], cfg["enablers"]
    results = []
    heat = 0.0
    if tow_mass:
        # Worst case: the tow mirror's Earth-facing side sheds as much heat as its back (twice an even spread).
        heat = 2 * beam_power * en["e2_absorbed_fraction"] * R_EARTH ** 2 / (4 * tow_distance ** 2) / EARTH_SUNLIGHT_W
        tide = (tow_mass / tow_distance ** 3) / (MOON_MASS / MOON_DISTANCE ** 3)
        accel = G * tow_mass / tow_distance ** 2
        results += [
            check("Extra heat at Earth from the tow mirror", heat, s["mirror_heat_max_fraction_of_sunlight"], "max", "share of sunlight"),
            check("Tide from the tow asteroid", tide, s["asteroid_tide_max_fraction_of_moon"], "max", "share of the Moon's"),
            check("Earth's acceleration from the tow", accel, s["tow_acceleration_max_m_s2"], "max", "m/s2"),
        ]
    if mirrors is None:  # quick estimate only: sunlight held at today's level
        share = 1.0
        area = math.pi * R_EARTH ** 2 * max(earth_au ** 2 - 1.0, 0.0) / 1e6
    else:  # computed: direct sunlight plus what the mirrors built so far reflect onto Earth
        share = mirrors.sunlight_share(earth_au, earth_e)
        area = mirrors.area_km2
    state = climate if climate is not None else {}
    flux = share * SOLAR_CONSTANT * (1.0 + heat)
    temperature = mean_temperature(flux, state.get("_t_k", 288.0))
    state["_t_k"] = temperature
    if tow_mass:  # the tow asteroid's tide slows Earth's spin a little; it adds up over the journey
        state["_lod_s"] = state.get("_lod_s", 0.0) + day_length_rate(tow_mass, tow_distance) * \
            max(0.0, year - state.get("_year", year)) * 3.15576e7
    state["_year"] = year
    lod = state.get("_lod_s", 0.0)
    thrust = thrust_over_moon_pull(tow_mass, tow_distance) if tow_mass else 0.0
    h = cfg["habitability"]
    values = {"temperature_k": temperature, "sunlight_share": share, "mirror_area_km2": area,
              "liquid_water_share": liquid_water_share(temperature), "absorbed_w_m2": absorbed_flux(flux, temperature),
              "surface_pressure_kpa": h["surface_pressure_kpa"], "jeans_lambda_n2": jeans_lambda(share),
              "magnetopause_re": magnetopause_re(earth_au, h["magnetopause_today_re"]),
              "day_length_change_s": lod, "moon_hill_share": hill_share(earth_au, h["earth_mass_with_moon_kg"]),
              "thrust_over_moon_pull": thrust}
    results += [
        check("Sunlight mirrors built, within E3's limit", area, en["e3_mirror_area_limit_km2"], "max", "km2"),
        check("Global mean surface temperature above minimum", temperature, s["temperature_min_k"], "min", "K"),
        check("Global mean surface temperature below maximum", temperature, s["temperature_max_k"], "max", "K"),
        check("Surface area with liquid water", values["liquid_water_share"], s["liquid_water_min_share"], "min", "share"),
        check("Absorbed sunlight below the runaway-greenhouse limit", values["absorbed_w_m2"], s["runaway_absorbed_max_w_m2"],
              "max", "W/m2"),
        check("Surface pressure", values["surface_pressure_kpa"], s["surface_pressure_min_kpa"], "min", "kPa"),
        check("N2 retained (Jeans lambda)", values["jeans_lambda_n2"], s["jeans_lambda_min"], "min"),
        check("Magnetic shielding: magnetopause standoff", values["magnetopause_re"], s["magnetopause_min_re"], "min", "Earth radii"),
        check("Change in length of day", lod, s["day_length_change_max_s"], "max", "s"),
        check("Moon inside the stable part of Earth's Hill sphere", values["moon_hill_share"], s["moon_hill_max_share"],
              "max", "of the Hill radius"),
        check("Thrust small compared with Earth's pull on the Moon", thrust, s["thrust_over_moon_pull_max"], "max"),
    ]
    if climate is not None:
        for key, value in values.items():
            lo, hi = climate.get(key, (value, value))
            climate[key] = (min(lo, value), max(hi, value))
    return results


def nudge_hours(mass_kg: float, push_m: float, nudge: dict) -> float:
    """Hours of E1's beam to move a body's pass by push_m, nudged nudge["warning_years"] ahead. A speed
    change dv given t ahead moves the pass about 3 dv t along the orbit; light pushes with up to 2P/c."""
    dv = push_m / (3 * nudge["warning_years"] * YEAR)
    return mass_kg * dv / (2 * nudge["beam_w"] / C_LIGHT) / 3600
