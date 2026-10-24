"""Earth-safety checks, run at every check step. Member 2 owns and extends these.

Each returns a check() result; limits come from config.yaml (safety and enablers sections).
"""

import math

from ..constants import C_LIGHT, G, YEAR
from ..flags import check
from ..habitability import SOLAR_CONSTANT, hill_share, magnetopause_re, mean_temperature

R_EARTH = 6.371e6
MOON_MASS = 7.342e22
MOON_DISTANCE = 3.844e8
SOLAR_CONSTANT = 1361.0                                # W/m^2 at 1 AU
EARTH_SUNLIGHT_W = SOLAR_CONSTANT * math.pi * R_EARTH ** 2  # all sunlight Earth catches today (mirrors keep it)


def safety_checks(cfg: dict, earth_au: float, tow_mass: float | None, tow_distance: float | None,
                  beam_power: float, earth_e: float = 0.0167, mirrors=None, climate: dict | None = None) -> list[dict]:
    """Earth's safety at one moment. With `mirrors` (habitability.Mirrors, already updated), sunlight and
    temperature are computed from the mirrors actually built; `climate` collects the values for the summary."""
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
    temperature = mean_temperature(share * SOLAR_CONSTANT * (1.0 + heat))
    h = cfg["habitability"]
    shield = magnetopause_re(earth_au, h["magnetopause_today_re"])
    hill = hill_share(earth_au, h["earth_mass_with_moon_kg"])
    results += [
        check("Sunlight mirrors built, within E3's limit", area, en["e3_mirror_area_limit_km2"], "max", "km2"),
        check("Sunlight reaching Earth", abs(share - 1.0), s["sunlight_fraction"]["tolerance"], "max", "away from today's"),
        check("Average temperature away from 288 K", abs(temperature - s["temperature_k"]["target"]),
              s["temperature_k"]["tolerance"], "max", "K"),
        check("Liquid water: mean temperature above freezing", temperature, 273.15, "min", "K"),
        check("Magnetic shielding no weaker than today's", shield, 0.99 * h["magnetopause_today_re"], "min", "Earth radii"),
        check("The Moon inside Earth's Hill sphere", hill, h["moon_hill_max_share"], "max", "of the Hill radius"),
    ]
    if climate is not None:
        for key, value in (("temperature_k", temperature), ("sunlight_share", share), ("mirror_area_km2", area),
                           ("magnetopause_re", shield), ("moon_hill_share", hill)):
            lo, hi = climate.get(key, (value, value))
            climate[key] = (min(lo, value), max(hi, value))
    return results


def nudge_hours(mass_kg: float, push_m: float, nudge: dict) -> float:
    """Hours of E1's beam to move a body's pass by push_m, nudged nudge["warning_years"] ahead. A speed
    change dv given t ahead moves the pass about 3 dv t along the orbit; light pushes with up to 2P/c."""
    dv = push_m / (3 * nudge["warning_years"] * YEAR)
    return mass_kg * dv / (2 * nudge["beam_w"] / C_LIGHT) / 3600
