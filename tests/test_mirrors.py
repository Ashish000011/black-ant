"""Sunlight mirror geometry (sim/scenarios/mirrors.py, issue #32): the incidence factor and the night-side share
from first principles, and the light-held ring's balance."""

import math

import numpy as np

from sim.config import load_config
from sim.scenarios import mirrors as mr

CFG = load_config()


def test_incidence_is_sin_half_phi():
    """A mirror at phi from the Sun sends sunlight (travelling along -s) to Earth (along -m): its normal bisects the
    two, and the light meets it at an angle whose cosine is sin(phi / 2)."""
    s = np.array([1.0, 0.0, 0.0])
    for deg in (30, 70.53, 90, 120, 150, 178):
        phi = math.radians(deg)
        m = np.array([math.cos(phi), math.sin(phi), 0.0])
        come, leave = -s, -m
        normal = (come - leave) / np.linalg.norm(come - leave)
        assert math.isclose(abs(np.dot(come, normal)), mr.incidence(phi), rel_tol=1e-12)
        assert math.isclose(abs(np.dot(leave, normal)), mr.incidence(phi), rel_tol=1e-12)   # angle in = angle out


def test_night_share_matches_the_lit_disc():
    """Light from direction m covering Earth's disc: the share falling on ground where the Sun is down equals
    (1 - cos phi) / 2 (sampled over the disc as seen from the mirror)."""
    n = 801
    x, y = np.meshgrid(np.linspace(-1, 1, n), np.linspace(-1, 1, n))
    inside = x * x + y * y < 1
    x, y = x[inside], y[inside]
    z = np.sqrt(1 - x * x - y * y)                       # toward the mirror
    for deg in (45, 90, 120, 160):
        phi = math.radians(deg)
        # Frame with the mirror on +z; the Sun at phi from it, in the x-z plane.
        sun = np.array([math.sin(phi), 0.0, math.cos(phi)])
        dark = (x * sun[0] + z * sun[2]) < 0
        assert abs(dark.mean() - mr.night_share(phi)) < 0.003


def test_light_held_ring_balances():
    """At the distance the script finds, sunlight's push and Earth's pull cancel along the Sun line, and what is
    left points inward, keeping the mirror circling the Sun-Earth line."""
    full = CFG
    phi = math.radians(full["mirrors"]["light_ring"]["phi_deg"])
    h = mr.hover(full["mirrors"], full, 1.0, phi, full["arrival"]["target_au"])
    d = h["distance_km"] * 1e3
    s, m = np.array([1.0, 0.0, 0.0]), np.array([math.cos(phi), math.sin(phi), 0.0])
    push = h["light_m_s2"] * (m - s) / np.linalg.norm(m - s)          # along in - out: away from the light's source
    pull = -mr.GM_EARTH / d ** 2 * m
    total = push + pull
    assert abs(total[0]) < 1e-12 * mr.GM_EARTH / d ** 2
    assert total[1] < 0 and math.isclose(-total[1], h["inward_m_s2"], rel_tol=1e-9)
