"""Octo-Earth, the brief's reference concept, audited with the same physics as our own machine.

    uv run python -m sim.scenarios.octo          # prints the audit and writes results/octo_earth.json

Two questions, answered with numbers:

1. Can currents in the arms push Earth? Earth's field comes from currents in Earth's own core. The force of the
   core's field on the arms' circuits and the force of the arms' field on the core are worked out separately
   (Biot-Savart fields, I dl x B forces) and they add up to zero: the arms only push on Earth's core, and nothing
   moves the pair. In a uniform outside field a closed circuit feels no net force at all. Only arms with no return
   path seem to push, and they are impossible (the charge would have nowhere to go); even then the push is a
   billionth of what moving Earth needs.
2. Can the arms hold themselves up? Standing, an arm's weight crushes its base and the column buckles; held out
   level, its weight bends it at the root. Both for eight materials, at the demo's default tube.
"""

import argparse
import json
import math

import numpy as np

from ..checks.structure import cantilever
from ..config import ROOT, load_config
from ..em import MU0, loop_force

GM_EARTH = 3.986004418e14
R_EARTH = 6.371e6
M_EARTH = 5.9722e24
OMEGA = 7.2921159e-5           # Earth's spin, rad/s
G_SURFACE = 9.81
GREENHILL = 7.837              # a column under its own weight buckles once q L^3 / (E I) reaches this
OUR_TOW_ACCELERATION = 6.53e-8  # m/s^2: what our asteroid gives Earth; the journey takes about 8,760 years


def segments_field(current: float, a, b, points, chunk: int = 128) -> np.ndarray:
    """Exact Biot-Savart field (T) at each of `points` from all the straight pieces a[k] -> b[k] (the same current
    in each), as in sim/em.segment_field, for many pieces and points at once."""
    a, b, points = (np.asarray(x, float) for x in (a, b, points))
    dl = b - a
    out = np.empty_like(points)
    for s in range(0, len(points), chunk):
        p = points[s:s + chunk, None, :]
        r1, r2 = p - a, p - b
        c = np.cross(dl, r1)
        along = ((r1 / np.linalg.norm(r1, axis=-1, keepdims=True) - r2 / np.linalg.norm(r2, axis=-1, keepdims=True))
                 * dl).sum(-1)
        out[s:s + chunk] = (c * (along / (c * c).sum(-1))[..., None]).sum(axis=1)
    return MU0 * current / (4 * math.pi) * out


def circuit_force(current: float, a, b, field_at) -> np.ndarray:
    """Net force I sum(dl x B) on the pieces a[k] -> b[k], with B from `field_at(points)`, integrated along each
    piece by three-point Gauss-Legendre quadrature."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    x, w = np.polynomial.legendre.leggauss(3)
    dl = b - a
    pts = a[:, None, :] + ((x + 1) / 2)[None, :, None] * dl[:, None, :]
    field = field_at(pts.reshape(-1, 3)).reshape(pts.shape)
    return current * (np.cross(dl[:, None, :], field) * (w / 2)[None, :, None]).sum(axis=(0, 1))


def polyline(corners, piece: float) -> np.ndarray:
    """Points along a closed path through `corners`, no piece longer than `piece` (m)."""
    out = []
    for p, q in zip(corners, corners[1:] + corners[:1]):
        n = max(1, math.ceil(np.linalg.norm(q - p) / piece))
        out += [p + (q - p) * k / n for k in range(n)]
    return np.array(out)


def arm_circuit(cfg: dict, k: int) -> np.ndarray:
    """Arm k's closed circuit: out along the arm, across the tip, back along the return conductor, across the root."""
    phi = 2 * math.pi * k / cfg["arms"]
    out_dir, side = np.array([math.cos(phi), math.sin(phi), 0.0]), np.array([-math.sin(phi), math.cos(phi), 0.0])
    el = math.radians(cfg["elevation_deg"])
    along = math.cos(el) * out_dir + math.sin(el) * np.array([0.0, 0.0, 1.0])
    root, half = R_EARTH * out_dir, cfg["go_return_spacing_km"] * 1e3 / 2 * side
    tip = root + cfg["length_km"] * 1e3 * along
    return polyline([root + half, tip + half, tip - half, root - half], cfg["segment_km"] * 1e3)


def core_loop(cfg: dict, sides: int = 720) -> tuple[np.ndarray, float]:
    """Earth's field as a current loop at the centre with Earth's dipole moment (pointing south, as Earth's does)."""
    r = cfg["core_loop_radius_km"] * 1e3
    t = np.linspace(0, 2 * math.pi, sides, endpoint=False)
    pts = np.stack((r * np.cos(t), -r * np.sin(t), np.zeros_like(t)), axis=1)
    return pts, cfg["earth_dipole_a_m2"] / (math.pi * r * r)


def net_force(cfg: dict, arms: list[int]) -> dict:
    """Force of the core's field on the arms, of the arms' field on the core, and their sum."""
    circuits = [arm_circuit(cfg, k) for k in arms]
    a = np.concatenate(circuits)
    b = np.concatenate([np.roll(c, -1, axis=0) for c in circuits])
    core, core_i = core_loop(cfg)
    core_b = np.roll(core, -1, axis=0)
    i = cfg["current_a"]
    on_arms = circuit_force(i, a, b, lambda p: segments_field(core_i, core, core_b, p))
    on_core = circuit_force(core_i, core, core_b, lambda p: segments_field(i, a, b, p))
    total = on_arms + on_core
    return {"arms": [k + 1 for k in arms], "on_arms_n": on_arms.tolist(), "on_core_n": on_core.tolist(),
            "sum_n": total.tolist(), "sum_over_force": float(np.linalg.norm(total) / max(np.linalg.norm(on_arms), 1e-300)),
            "field_at_root_t": float(np.linalg.norm(segments_field(core_i, core, core_b, a[:1])[0]))}


def outside_field(cfg: dict) -> dict:
    """Closed arm circuits in the demo's uniform 0.5 nT outside field, and the same arms with no return path."""
    field = np.array(cfg["interplanetary_field_t"], float)
    i, length = cfg["current_a"], cfg["length_km"] * 1e3
    closed = sum(loop_force(i, arm_circuit(cfg, k), field) for k in range(cfg["arms"]))
    one_way = []
    for k in range(cfg["arms"]):
        c = arm_circuit(cfg, k)
        tip = c[np.argmax(np.linalg.norm(c, axis=1))]
        one_way.append(i * np.cross(tip - c[0], field))
    open_force = np.sum(one_way, axis=0)
    # The same open arms in Earth's own field near the surface (the biggest push they could seem to give).
    surface = 3.1e-5
    open_earth = cfg["arms"] * i * length * surface
    return {"closed_circuits_n": float(np.linalg.norm(closed)), "scale_i_l_b_n": float(i * length * np.linalg.norm(field)),
            "open_arms_n": float(np.linalg.norm(open_force)), "open_arms_in_earth_field_n": open_earth,
            "open_arms_earth_acceleration": open_earth / M_EARTH,
            "years_needed_at_that_push": 8758 * OUR_TOW_ACCELERATION / (open_earth / M_EARTH)}


def column_stress(density: float, length: float) -> float:
    """Base stress (Pa) of a straight tower of even cross-section standing on the equator, spinning with Earth."""
    top = R_EARTH + length
    return density * (GM_EARTH * (1 / R_EARTH - 1 / top) - OMEGA ** 2 * (top ** 2 - R_EARTH ** 2) / 2)


GEO_HEIGHT = (GM_EARTH / OMEGA ** 2) ** (1 / 3) - R_EARTH   # a standing tower's base stress peaks at this height


def longest(stress_at, allowed: float, top: float) -> float | None:
    """Longest arm (m) whose stress stays at or under `allowed`, by bisection up to `top`, where the stress is
    largest; None if even `top` is within it."""
    lo, hi = 0.0, top
    if stress_at(hi) <= allowed:
        return None
    for _ in range(80):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if stress_at(mid) <= allowed else (lo, mid)
    return lo


def km_or_none(m: float | None) -> float | None:
    return None if m is None else m / 1e3


def materials(cfg: dict, sf_min: float) -> list[dict]:
    d, t = cfg["outer_diameter_km"] * 1e3, cfg["wall_km"] * 1e3
    area = math.pi / 4 * (d ** 2 - (d - 2 * t) ** 2)
    inertia = math.pi / 64 * (d ** 4 - (d - 2 * t) ** 4)
    out = []
    for m in cfg["materials"]:
        q = m["density"] * G_SURFACE * area
        top_g = GM_EARTH / (R_EARTH + cfg["length_km"] * 1e3) ** 2   # the weakest gravity along a standing arm

        def bend(length, m=m, q=q):  # root stress of the arm held out level near the ground
            moment, _ = cantilever(q, length, m["e_pa"], inertia, segments=200)
            return moment * (d / 2) / inertia

        allowed = m["strength_pa"] / sf_min
        rows = []
        for km in cfg["lengths_km"]:
            L = km * 1e3
            rows.append({"length_km": km, "standing_base_stress_pa": column_stress(m["density"], L),
                         "standing_sf": m["strength_pa"] / column_stress(m["density"], L),
                         "level_root_stress_pa": bend(L), "level_sf": m["strength_pa"] / bend(L)})
        out.append({**{k: m[k] for k in ("name", "density", "strength_pa", "e_pa", "source")},
                    "lengths": rows,
                    "standing_longest_km": km_or_none(longest(lambda L: column_stress(m["density"], L), allowed, GEO_HEIGHT)),
                    "buckling_length_km": (GREENHILL * m["e_pa"] * inertia / q) ** (1 / 3) / 1e3,
                    "buckling_length_weakest_gravity_km": (GREENHILL * m["e_pa"] * inertia / (q * top_g / G_SURFACE)) ** (1 / 3) / 1e3,
                    "level_longest_km": km_or_none(longest(bend, allowed, top=2e7))})
    return out


def run(cfg: dict | None = None) -> dict:
    cfg = cfg or load_config()
    o = cfg["octo_earth"]
    sf_min = cfg["safety"]["structural_safety_factor_min"]
    return {"arm": {k: o[k] for k in ("arms", "length_km", "outer_diameter_km", "wall_km", "elevation_deg", "current_a",
                                      "go_return_spacing_km")},
            "net_force_all_arms": net_force(o, list(range(o["arms"]))),
            "net_force_one_arm": net_force(o, [0]),
            "outside_field": outside_field(o),
            "materials": materials(o, sf_min), "safety_factor_min": sf_min}


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit the Octo-Earth reference concept.")
    parser.add_argument("--out", default=str(ROOT / "results" / "octo_earth.json"))
    args = parser.parse_args()
    r = run()
    for key in ("net_force_all_arms", "net_force_one_arm"):
        n = r[key]
        print(f"Arms {n['arms']}: force on the arms {np.linalg.norm(n['on_arms_n']):.3e} N, on Earth's core "
              f"{np.linalg.norm(n['on_core_n']):.3e} N, sum {np.linalg.norm(n['sum_n']):.2e} N "
              f"({n['sum_over_force']:.1e} of the force)")
    f = r["outside_field"]
    print(f"0.5 nT outside field: closed circuits {f['closed_circuits_n']:.2e} N (I L B = {f['scale_i_l_b_n']:.2e} N); "
          f"open arms {f['open_arms_n']:.2e} N")
    print(f"Open arms in Earth's field, at best {f['open_arms_in_earth_field_n']:.2e} N: Earth would take "
          f"{f['years_needed_at_that_push']:.1e} years")
    print(f"\nAt safety factor {r['safety_factor_min']}, the demo's tube ({r['arm']['outer_diameter_km']} km across, "
          f"{r['arm']['wall_km']} km walls):")
    print(f"{'Material':48} {'stand 12,000 km SF':>18} {'longest standing':>17} {'buckles past':>13} {'level 12,000 km SF':>19} {'longest level':>14}")
    for m in r["materials"]:
        last = m["lengths"][-1]
        stand = "no limit" if m["standing_longest_km"] is None else f"{m['standing_longest_km']:,.0f} km"
        print(f"{m['name']:48} {last['standing_sf']:18.2e} {stand:>17} {m['buckling_length_km']:10,.0f} km "
              f"{last['level_sf']:19.2e} {m['level_longest_km']:11,.0f} km")
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(r, fh, indent=1)
    print(f"\nWrote {args.out}")


if __name__ == "__main__":
    main()
