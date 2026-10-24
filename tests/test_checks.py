"""Checks, flags, the belt estimate and the axial-tilt model. Run: uv run pytest tests/test_checks.py"""

import math

import numpy as np
import pytest

from sim.belt import R_EARTH, V_ESCAPE_EARTH, BeltSample
from sim.checks.structure import structure_checks
from sim.config import load_config
from sim.constants import AU, C_LIGHT
from sim.flags import Flags, check

CFG = load_config()


def test_flags_keep_failures_and_name_the_enabler():
    flags = Flags()
    assert not flags.record(check("fine", 1.0, 2.0, "max"), 1.0)
    assert flags.record(check("too close", 0.01, 0.05, "min", "AU"), 10.0)
    assert flags.record(check("too close", 0.02, 0.05, "min", "AU"), 20.0)
    flags.note("uses E1", 5e25, "W", "E1")
    s = flags.summary()
    assert s["unresolved"] == 1 and s["covered_by_enablers"] == 1
    worst = next(f for f in s["flags"] if f["check"] == "too close")
    assert worst["worst"] == 0.01 and worst["times"] == 2 and worst["first_year"] == 10.0 and worst["last_year"] == 20.0


@pytest.mark.parametrize("tow", ["earth-tow", "mars-tow"])
def test_structures_hold_at_the_most_the_beam_can_push(tow):
    """At its power cap, a perfect mirror pushes at most 2P/c; every structure keeps a 1.5 safety factor."""
    t = next(x for x in CFG["tows"] if x["name"] == tow)
    target = next(p for p in CFG["planets"] if p["name"] == t["target"])
    power = t["max_beam_w"]
    results = structure_checks(CFG, tow, 2 * power / C_LIGHT, power, t["asteroid_mass_kg"], t["distance_km"] * 1e3,
                               target["mass_kg"])
    failed = [(r["check"], r["value"]) for r in results if not r["ok"]]
    assert not failed, failed


def test_belt_encounter_turns_into_a_hit_chance():
    """One pass within x at speed v counts R^2 (1 + (v_esc/v)^2) / x^2, scaled up to the real belt."""
    cfg = {**CFG["belt_sample"], "count": 10}
    sample = BeltSample(cfg, np.zeros(3), np.zeros(3), 0.0)
    v = 5000.0
    sample.encounters = [(1.0, 1e9, v)]
    x = cfg["close_pass_au"] * AU
    expected = R_EARTH ** 2 * (1 + (V_ESCAPE_EARTH / v) ** 2) / x ** 2 * cfg["real_population_over_1km"] / 10
    s = sample.summary(100.0, 500000, None)
    assert math.isclose(s["expected_real_impacts_over_1km"], expected, rel_tol=1e-12)


@pytest.mark.slow
def test_x9_real_earth_axial_tilt_cycle():
    """X9: our tilt model on the real solar system gives back Earth's known 41,000-year tilt cycle,
    which over the last million years stayed between about 22.1 and 24.5 degrees."""
    from sim.scenarios.longterm import baseline_state, run_one
    r = run_one(baseline_state(CFG), 50000, CFG, "real", progress=False)
    lo, hi = r["axial_tilt_deg"]
    print(f"X9 tilt {lo:.2f}-{hi:.2f} deg over 50,000 years")
    assert 21.9 < lo < 23.0 and 23.9 < hi < 24.7
