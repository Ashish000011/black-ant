"""Night light at 2.7 AU: how much moonlight is lost, what Moon reflectors can give back, and what they cannot."""

import math

from sim import night
from sim.config import load_config

CFG = load_config()
NIGHT = CFG["night"]
RHO = CFG["habitability"]["mirror_reflectivity"]


def test_moonlight_falls_as_the_inverse_square():
    assert math.isclose(night.natural_full_moon_lux(NIGHT, 2.7) / NIGHT["full_moon_lux_today"], 1 / 2.7 ** 2)


def test_restoring_full_moon_light_fits_well_inside_e3():
    """About 3,300 km^2 of reflectors gives back today's full Moon at 2.7 AU; E3 has 1.5e8 km^2 spare."""
    area = night.area_for_full_moon_lux(NIGHT, NIGHT["full_moon_lux_today"], 2.7, 0.0, RHO)
    print(f"Moon reflectors to restore full-Moon light at 2.7 AU: {area:,.0f} km2")
    assert 2000 < area < 5000
    total = night.natural_full_moon_lux(NIGHT, 2.7) + night.reflector_lux(NIGHT, area, 2.7, 0.0, RHO)
    assert math.isclose(total, NIGHT["full_moon_lux_today"], rel_tol=1e-9)
    assert area < 0.01 * (CFG["enablers"]["e3_mirror_area_limit_km2"] - 8.5e8)


def test_moon_reflectors_cannot_carry_the_climate():
    """Even the Moon's whole near side, mirrored, sends under 10 W/m2 to the night side and warms Earth under 1 K."""
    full = night.near_side_km2(NIGHT)
    w = night.night_heating_w_m2(full, 2.7, 0.0, RHO)
    k = night.warming_k(full, 2.7, 0.0, 1.0, RHO)
    print(f"Whole near side: {w:.2f} W/m2 on the night side, {k:.2f} K global mean")
    assert 1 < w < 10
    assert 0 < k < 1


def test_month_mean_matches_the_phase_rule():
    n = 100000
    mean = sum(night.phase_factor(180 * (i + 0.5) / n) for i in range(n)) / n
    assert math.isclose(mean, night.MONTH_MEAN, rel_tol=1e-4)
    assert night.phase_factor(120) == 0.0


def test_one_reflector_lights_a_spot_about_1300_km_wide():
    assert 1250 < night.spot_km(NIGHT, 2.7) < 1400
