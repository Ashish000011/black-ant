"""Night light after the move: moonlight, and Moon reflectors that bring it back.

The Moon goes wherever Earth goes, so at r AU it gets 1/r^2 of today's sunlight and full-Moon light on Earth falls the
same way: 13.7% of today's at 2.7 AU. The sunlight mirrors (enabler E3) aim at Earth, not at the Moon. Moon
reflectors are flat mirrors on the Moon's near side, built under E3's mirror bound, that send sunlight to Earth's
night side. Three limits follow from geometry:

- A flat mirror sends back a cone as wide as the Sun looks from it (0.533 deg / r), so from the Moon each one lights
  a spot about 1,300 km across at 2.7 AU. Many mirrors aimed at different spots light the whole night side.
- The near side faces Earth all month but is in daylight only from first to last quarter, the half of the month
  around full Moon, which is also when the Moon is over Earth's night side. A mirror tilted halfway between the Sun
  and Earth catches cos(phase / 2) of what it catches at full Moon; over a month that averages 2 sin(45 deg) / pi.
- The near side's disc is 9.5e6 km^2. Covering all of it caps what the Moon can send at about 1.7e15 W at 2.7 AU,
  6.6 W/m^2 over the night side against the ~240 W/m^2 Earth absorbs from the Sun. Moon reflectors can light the
  night; they cannot carry the climate. The sunlight mirrors do that.

The test bench (viewer/src/estimates.js) uses the same formulas for its live sliders. None of this is in the saved
journey run.
"""

import math

from .habitability import SOLAR_CONSTANT, mean_inverse_r2, mean_temperature

EARTH_RADIUS_M = 6.371e6
NIGHT_SIDE_M2 = 2 * math.pi * EARTH_RADIUS_M ** 2
# Monthly mean of cos(phase / 2) over phases 0 to 180 deg, the mirror lit only below 90 deg: (2 / pi) sin(pi / 4).
MONTH_MEAN = 2 * math.sin(math.pi / 4) / math.pi


def phase_factor(phase_deg: float) -> float:
    """What a near-side reflector sends, against full Moon (phase 0): zero once its site is in the lunar night."""
    return math.cos(math.radians(phase_deg) / 2) if phase_deg < 90 else 0.0


def natural_full_moon_lux(cfg: dict, a_au: float, e: float = 0.0) -> float:
    """Full-Moon light on Earth (lux), yearly mean: today's, scaled by the sunlight the Moon gets."""
    return cfg["full_moon_lux_today"] * mean_inverse_r2(a_au, e)


def reflector_power_w(area_km2: float, a_au: float, e: float = 0.0, reflectivity: float = 0.95,
                      phase_deg: float = 0.0) -> float:
    """Sunlight (W) Moon reflectors of this area send to Earth at this phase."""
    return area_km2 * 1e6 * SOLAR_CONSTANT * mean_inverse_r2(a_au, e) * reflectivity * phase_factor(phase_deg)


def reflector_lux(cfg: dict, area_km2: float, a_au: float, e: float = 0.0, reflectivity: float = 0.95,
                  phase_deg: float = 0.0) -> float:
    """Light (lux) the reflectors add, spread evenly over Earth's night side."""
    return reflector_power_w(area_km2, a_au, e, reflectivity, phase_deg) / NIGHT_SIDE_M2 * cfg["sunlight_lm_per_w"]


def area_for_full_moon_lux(cfg: dict, target_lux: float, a_au: float, e: float = 0.0,
                           reflectivity: float = 0.95) -> float:
    """Reflector area (km^2) that brings full-Moon light on the night side up to `target_lux`."""
    missing = max(0.0, target_lux - natural_full_moon_lux(cfg, a_au, e))
    per_km2 = reflector_lux(cfg, 1.0, a_au, e, reflectivity)
    return missing / per_km2


def near_side_km2(cfg: dict) -> float:
    """The Moon's disc as seen from Earth: the most flat reflectors facing Earth can cover."""
    return math.pi * cfg["moon_radius_km"] ** 2


def spot_km(cfg: dict, a_au: float, moon_distance_km: float = 384400.0) -> float:
    """Width of the patch one flat reflector lights on Earth: the Sun's apparent size times the distance."""
    return moon_distance_km * math.radians(cfg["sun_diameter_1au_deg"]) / a_au


def night_heating_w_m2(area_km2: float, a_au: float, e: float = 0.0, reflectivity: float = 0.95) -> float:
    """Sunlight arriving on the night side from the reflectors at full Moon (W/m^2 over the night hemisphere)."""
    return reflector_power_w(area_km2, a_au, e, reflectivity) / NIGHT_SIDE_M2


def warming_k(area_km2: float, a_au: float, e: float, sunlight_share: float, reflectivity: float = 0.95,
              start_k: float = 288.0) -> float:
    """Global mean warming (K) from the reflectors' monthly mean light, through the journey's own climate model:
    their power is added to the sunlight across Earth's disc."""
    base = sunlight_share * SOLAR_CONSTANT
    extra = reflector_power_w(area_km2, a_au, e, reflectivity) * MONTH_MEAN / (math.pi * EARTH_RADIUS_M ** 2)
    t0 = mean_temperature(base, start_k)
    return mean_temperature(base + extra, t0) - t0
