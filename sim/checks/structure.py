"""Structural checks for each tow, run at every check step.

Safety factor = strength / stress, and the brief requires at least 1.5 for every structure.
Design sizes come from config.yaml (structures section); material limits from the enablers section.
"""

import math

from ..constants import G
from ..flags import check

SIGMA = 5.670374e-8


def structure_checks(cfg: dict, tow_name: str, beam_force_n: float, beam_power_w: float,
                     asteroid_mass: float, distance: float, target_mass: float) -> list[dict]:
    design, en = cfg["structures"][tow_name], cfg["enablers"]
    sf_min = cfg["safety"]["structural_safety_factor_min"]
    rock = cfg["structures"]["rock_strength_pa"]
    results = []
    if beam_force_n > 0:
        cable_sf = en["e2_strength_pa"] * design["cable_cross_section_km2"] * 1e6 / beam_force_n
        anchor_sf = rock * design["anchor_area_km2"] * 1e6 / beam_force_n
        area = math.pi * (design["mirror_radius_km"] * 1e3) ** 2
        absorbed = beam_power_w * en["e2_absorbed_fraction"]
        mirror_t = (absorbed / (2 * en["e2_emissivity"] * SIGMA * area)) ** 0.25  # both faces radiate
        results += [
            check(f"{tow_name}: cable safety factor", cable_sf, sf_min, "min"),
            check(f"{tow_name}: anchor safety factor", anchor_sf, sf_min, "min"),
            check(f"{tow_name}: tow mirror temperature", mirror_t, en["e2_max_temperature_k"], "max", "K"),
        ]
    # The target's pull acts on every kilogram of the asteroid; the uneven part is about density x g x radius.
    radius = (3 * asteroid_mass / (4 * math.pi * design["asteroid_density_kg_m3"])) ** (1 / 3)
    stress = design["asteroid_density_kg_m3"] * (G * target_mass / distance ** 2) * radius
    results.append(check(f"{tow_name}: asteroid body safety factor", rock / stress, sf_min, "min"))
    return results


def cantilever(q: float, length: float, e_mod: float, inertia: float, segments: int = 2000) -> tuple[float, float]:
    """Root bending moment (N m) and tip deflection (m) of a cantilever under a load q (N/m: its own weight, a
    number or a function of distance from the root), worked out numerically with the trapezoid rule: shear is the
    load integrated in from the free tip, moment is the shear integrated in from the tip, and slope and deflection
    are the curvature M / (E I) integrated out from the clamped root, twice.
    For a uniform load the formulas are M = q L^2 / 2 and deflection = q L^4 / (8 E I)."""
    import numpy as np
    x = np.linspace(0.0, length, segments + 1)
    h = length / segments
    load = np.asarray(q(x) if callable(q) else np.full_like(x, q), float)

    def from_tip(f):
        return np.concatenate((np.cumsum(((f[1:] + f[:-1]) / 2)[::-1])[::-1] * h, [0.0]))

    shear = from_tip(load)
    moment = from_tip(shear)
    curvature = moment / (e_mod * inertia)
    slope = np.concatenate(([0.0], np.cumsum((curvature[1:] + curvature[:-1]) / 2) * h))
    deflection = np.concatenate(([0.0], np.cumsum((slope[1:] + slope[:-1]) / 2) * h))
    return float(moment[0]), float(deflection[-1])
