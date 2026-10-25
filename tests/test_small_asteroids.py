"""Small asteroids at 2.7 AU (sim/scenarios/small_asteroids.py, issue #30): the size scaling, the thermal model, and
the Kirkwood-gap check against real orbits."""

import json
import math

from sim.config import ROOT, load_config
from sim.scenarios import small_asteroids as sa

CFG = load_config()
SUMMARY = json.loads((ROOT / "results" / "summary.json").read_text(encoding="utf-8"))


def test_rates_scale_down_the_size_distribution():
    """The >=20 m rate is the >=1 km rate times the count ratio the slopes give: 10^q_above (1 km to the 100 m
    break) times 5^q_below (100 m to 20 m), for each of low, central and high; the 1 km rate is the run's own."""
    s = CFG["small_asteroids"]
    run = CFG["belt_sample"]["real_population_over_1km"]
    r = sa.impact_rates(s, SUMMARY["belt"], run)
    for phase, key in (("crossing", "crossing"), ("parked", "parked_at_target")):
        assert math.isclose(r[phase]["1000m"]["years_per_impact"]["central"], SUMMARY["belt"][key]["years_per_impact"])
        for k, case in enumerate(sa.CASES):
            ratio = 10 ** s["slope_above_break"][k] * 5 ** s["slope_below_break"][k]
            one_km = r[phase]["1000m"]["per_year"][case]
            assert math.isclose(r[phase]["20m"]["per_year"][case], one_km * ratio, rel_tol=1e-12)
    assert r["parked"]["20m"]["per_year"]["low"] < r["parked"]["20m"]["per_year"]["central"] < r["parked"]["20m"]["per_year"]["high"]


def test_thermal_flux_matches_rayleigh_jeans():
    """At long wavelengths NEATM's flux has a closed form: eps R^2 / delta^2 (2 k nu^2 / c^2) 2 pi T_ss / 2.25 (the
    day side at T_ss cos^(1/4)); and the survey's reach grows in step with the rock's size."""
    s = dict(CFG["small_asteroids"], phase_deg=0)
    lam, d, delta, eta = 0.1, 100.0, 1e9, 1.2   # 10 cm: h nu / k T is 6e-4, so Planck is Rayleigh-Jeans to 0.03%
    t_ss = ((1 - 0.39 * s["albedo"]) * sa.SOLAR_CONSTANT / 2.7 ** 2 / (eta * s["emissivity"] * sa.SIGMA)) ** 0.25
    nu = sa.C_LIGHT / lam
    by_hand = s["emissivity"] * (d / 2) ** 2 / delta ** 2 * 2 * sa.K_B * nu ** 2 / sa.C_LIGHT ** 2 * 2 * math.pi * t_ss / 2.25
    assert math.isclose(sa.neatm_jy(d, delta, 2.7, eta, s, lam=lam), by_hand / sa.JANSKY, rel_tol=1e-3)
    assert math.isclose(sa.seen_from_m(100, eta, s, 2.7), 5 * sa.seen_from_m(20, eta, s, 2.7), rel_tol=1e-9)


def test_kirkwood_gaps_are_gaps_in_orbit_size_not_in_space():
    """In the 20,000 real orbits the gaps hold far fewer orbit sizes than 2.7 AU, but Earth parked there would still
    meet most of the asteroids it meets at 2.7 AU: those that cross a gap come from elsewhere."""
    k = sa.kirkwood(CFG["small_asteroids"], CFG)
    for au in ("2.50", "2.82"):
        assert k[au]["orbit_sizes_vs_2.70"] < 0.3
        assert 0.6 < k[au]["encounters_vs_2.70"] < 1.4
