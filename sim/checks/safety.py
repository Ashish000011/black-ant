"""Earth-safety checks, run at every check step. Member 2 owns and extends these.

Each returns a check() result; limits come from config.yaml (safety and enablers sections).
"""

import math

from ..constants import C_LIGHT, G, YEAR
from ..flags import check

R_EARTH = 6.371e6
MOON_MASS = 7.342e22
MOON_DISTANCE = 3.844e8
SOLAR_CONSTANT = 1361.0                                # W/m^2 at 1 AU
EARTH_SUNLIGHT_W = SOLAR_CONSTANT * math.pi * R_EARTH ** 2  # all sunlight Earth catches today (mirrors keep it)


def safety_checks(cfg: dict, earth_au: float, tow_mass: float | None, tow_distance: float | None,
                  beam_power: float) -> list[dict]:
    s, en = cfg["safety"], cfg["enablers"]
    mirror_km2 = math.pi * R_EARTH ** 2 * max(earth_au ** 2 - 1.0, 0.0) / 1e6
    results = [check("Sunlight mirrors needed, within E3's limit", mirror_km2, en["e3_mirror_area_limit_km2"], "max", "km2")]
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
    # Mirrors keep sunlight at today's level; the tow mirror's waste heat is the only extra.
    temperature = s["temperature_k"]["target"] * (1.0 + heat) ** 0.25
    results.append(check("Average temperature away from 288 K", abs(temperature - s["temperature_k"]["target"]),
                         s["temperature_k"]["tolerance"], "max", "K"))
    return results


def nudge_hours(mass_kg: float, push_m: float, nudge: dict) -> float:
    """Hours of E1's beam to move a body's pass by push_m, nudged nudge["warning_years"] ahead. A speed
    change dv given t ahead moves the pass about 3 dv t along the orbit; light pushes with up to 2P/c."""
    dv = push_m / (3 * nudge["warning_years"] * YEAR)
    return mass_kg * dv / (2 * nudge["beam_w"] / C_LIGHT) / 3600
