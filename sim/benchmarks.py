"""The ten official benchmarks (participant guide, section 6), each with inputs judges can change.

    uv run python -m sim.benchmarks                  # run all ten, print measured against expected
    uv run python -m sim.benchmarks 4 --set e=0.5 --set periods=20
    uv run python -m sim.benchmarks 8 --set push=2e-8

Each function returns a dict: what was measured, what was expected, the tolerance, and whether it passed.
tests/test_official_benchmarks.py runs them all on every pull request.
"""

import argparse
import math

import numpy as np

from .bodies import move_to_barycentre, real_planets, start_planets
from .checks.structure import cantilever
from .config import load_config
from .constants import AU, DAY, G, GM_SUN, YEAR
from .em import MU0, loop_force, wire_field, wire_force
from .habitability import equilibrium_temperature, sunlight
from .integrator import energy, gravity, leapfrog, yoshida4

M_SUN = GM_SUN / G


def result(name, measured, expected, tolerance, ok, unit="", note=""):
    return {"name": name, "measured": measured, "expected": expected, "tolerance": tolerance, "ok": bool(ok),
            "unit": unit, "note": note}


def b1(current=10.0, length=(2.0, 0.0, 0.0), field=(0.0, 0.5, 0.0), pieces=1000):
    """Wire, I = 10 A, L = 2 m along x, B = 0.5 T along y: 10 N along +z.
    Measured: dF = I dl x B added up over the wire's pieces. Expected: F = I L x B."""
    ends = np.outer(np.linspace(0, 1, pieces + 1), np.asarray(length, float))
    f = sum(wire_force(current, ends[k + 1] - ends[k], field) for k in range(pieces))
    expected = wire_force(current, length, field)
    err = np.linalg.norm(f - expected) / np.linalg.norm(expected)
    return result("Wire in a field", [round(float(x), 12) for x in f], expected.tolist(), "1e-9 relative", err <= 1e-9, "N")


def b2(current=10.0, radius=1.0, field=(0.3, -0.2, 0.5), sides=1000):
    """Closed loop in a uniform field: net force 0, to 1e-9 of I L B."""
    t = np.linspace(0, 2 * np.pi, sides, endpoint=False)
    points = np.stack((radius * np.cos(t), radius * np.sin(t), np.zeros_like(t)), axis=1)
    f = loop_force(current, points, field)
    scale = current * 2 * np.pi * radius * np.linalg.norm(field)
    return result("Closed loop, uniform field", float(np.linalg.norm(f) / scale), 0.0, "1e-9 of I L B",
                  np.linalg.norm(f) <= 1e-9 * scale, "of I L B")


def b3(current=1000.0, distance=1.0, half_length=1e6):
    """Long straight wire, 1 kA, field at 1 m: mu0 I / (2 pi r) = 2.000e-4 T, to 1e-6."""
    b = wire_field(current, [(-half_length, 0, 0), (half_length, 0, 0)], (0, distance, 0))
    expected = MU0 * current / (2 * np.pi * distance)
    return result("Long wire field", float(np.linalg.norm(b)), expected, "1e-6 relative",
                  abs(np.linalg.norm(b) / expected - 1) <= 1e-6, "T")


def b4(a_au=1.0, e=0.3, periods=10, steps_per_period=None):
    """Kepler orbit, a = 1 AU, e = 0.3, 10 periods: back to the start within 1e-6 a; energy within 1e-9."""
    # The step that matters is the one at pericentre, where the orbit turns fastest: its timescale goes as
    # (1 - e)^1.5, so a more eccentric orbit gets proportionally more steps (2,000 per orbit at e = 0.3).
    steps_per_period = int(steps_per_period or max(2000, math.ceil(2000 * (0.7 / (1 - e)) ** 1.5)))
    a = a_au * AU
    rp = a * (1 - e)
    vp = math.sqrt(GM_SUN * (1 + e) / rp)
    m = np.array([M_SUN, 0.0])
    pos = np.array([[0.0, 0, 0], [rp, 0, 0]])
    vel = np.array([[0.0, 0, 0], [0, vp, 0]])
    period = 2 * math.pi * math.sqrt(a ** 3 / GM_SUN)
    e0 = 0.5 * vp ** 2 - GM_SUN / rp
    worst = [0.0]

    def watch(_, p, v):
        r, u = np.linalg.norm(p[1] - p[0]), np.linalg.norm(v[1] - v[0])
        worst[0] = max(worst[0], abs((0.5 * u * u - GM_SUN / r - e0) / e0))

    yoshida4(m, pos, vel, period / steps_per_period, periods * steps_per_period, watch)
    miss = float(np.linalg.norm(pos[1] - pos[0] - [rp, 0, 0]) / a)
    return result("Kepler orbit back to start", {"position_over_a": float(f"{miss:.3g}"), "energy": float(f"{worst[0]:.3g}")}, 0.0,
                  "1e-6 a; energy 1e-9", miss <= 1e-6 and worst[0] <= 1e-9,
                  note=f"Yoshida 4th order, {steps_per_period} steps per orbit")


def b5(years=5.0, dt_days=0.25):
    """Solar system, 5 years, no push: energy constant to 1e-9 (Sun, Mercury to Neptune)."""
    cfg = load_config()
    system = real_planets(cfg["planets"] + [cfg["benchmarks"]["mercury"]])
    move_to_barycentre(system)
    m, pos, vel = system.m, system.pos, system.vel
    e0 = energy(m, pos, vel)
    worst = [0.0]

    def watch(_, p, v):
        worst[0] = max(worst[0], abs(energy(m, p, v) / e0 - 1))

    yoshida4(m, pos, vel, dt_days * DAY, round(years * YEAR / (dt_days * DAY)), watch)
    return result("Solar system energy, no push", worst[0], 0.0, "1e-9", worst[0] <= 1e-9,
                  note=f"Yoshida 4th order, {dt_days}-day steps")


def b6(years=3.0, dt_days=0.25):
    """Earth-Moon barycentre's period around the Sun: 365.256 days, to 0.1 day."""
    cfg = load_config()
    system = start_planets(cfg["planets"], "real")
    move_to_barycentre(system)
    m, pos, vel = system.m, system.pos, system.vel
    sun, earth = system.index("sun"), system.index("earth")
    lon = [math.atan2(*(pos[earth] - pos[sun])[1::-1])]
    times = [0.0]

    def watch(k, p, _):
        times.append(k * dt_days)
        lon.append(math.atan2(*(p[earth] - p[sun])[1::-1]))

    yoshida4(m, pos, vel, dt_days * DAY, round(years * YEAR / (dt_days * DAY)), watch)
    turned = np.unwrap(lon) - lon[0]
    laps = np.arange(1, int(turned[-1] / (2 * np.pi)) + 1) * 2 * np.pi
    crossings = np.interp(laps, turned, times)
    period = float(np.diff(np.concatenate(([0.0], crossings))).mean())
    return result("Earth-Moon barycentre period", period, 365.256, "0.1 day", abs(period - 365.256) <= 0.1, "days",
                  note="mean of whole laps against the stars")


def b7(r1_au=1.0, r2_au=1.524, steps=20000):
    """Hohmann transfer 1 -> 1.524 AU: 2.94 + 2.65 km/s, about 259 days (0.02 km/s; 2 days)."""
    r1, r2 = r1_au * AU, r2_au * AU
    at = (r1 + r2) / 2
    dv1 = math.sqrt(GM_SUN / r1) * (math.sqrt(2 * r2 / (r1 + r2)) - 1)
    dv2 = math.sqrt(GM_SUN / r2) * (1 - math.sqrt(2 * r1 / (r1 + r2)))
    t_half = math.pi * math.sqrt(at ** 3 / GM_SUN)
    # Fly it: start on the circular orbit at r1, add dv1, and step until the farthest point.
    m = np.array([M_SUN, 0.0])
    pos = np.array([[0.0, 0, 0], [r1, 0, 0]])
    vel = np.array([[0.0, 0, 0], [0, math.sqrt(GM_SUN / r1) + dv1, 0]])
    dt = 1.2 * t_half / steps
    track = []
    leapfrog(m, pos, vel, dt, steps, lambda k, p, v: track.append((k * dt, np.linalg.norm(p[1] - p[0]))))
    t_far, r_far = max(track, key=lambda x: x[1])
    expected = (2.94, 2.65, 259.0)
    measured = (dv1 / 1e3, dv2 / 1e3, t_far / DAY)
    ok = abs(measured[0] - expected[0]) <= 0.02 and abs(measured[1] - expected[1]) <= 0.02 \
        and abs(measured[2] - expected[2]) <= 2 and abs(r_far / r2 - 1) < 1e-3
    return result("Hohmann transfer", [round(x, 4) for x in measured], list(expected), "0.02 km/s; 2 days", ok,
                  "km/s, km/s, days", note=f"flown: farthest point {r_far / AU:.4f} AU")


def b8(push=1e-8, years=1.0, dt_days=0.1):
    """Push of 1e-8 m/s^2 along the velocity for a year: the orbit grows by about 3,170 km (1%)."""
    a0 = AU
    m = np.array([M_SUN, 0.0])
    pos = np.array([[0.0, 0, 0], [a0, 0, 0]])
    vel = np.array([[0.0, 0, 0], [0, math.sqrt(GM_SUN / a0), 0]])

    def along(p, v):
        out = np.zeros_like(v)
        u = v[1] - v[0]
        out[1] = push * u / np.linalg.norm(u)
        return out

    def size(p, v):
        r, u = np.linalg.norm(p[1] - p[0]), np.linalg.norm(v[1] - v[0])
        return 1 / (2 / r - u * u / GM_SUN)

    start = size(pos, vel)
    leapfrog(m, pos, vel, dt_days * DAY, round(years * YEAR / (dt_days * DAY)), push=along)
    grown = (size(pos, vel) - start) / 1e3
    expected = 2 * push * years * YEAR / math.sqrt(GM_SUN / a0 ** 3) / 1e3  # Gauss: da/dt = 2 push / n
    return result("Push along velocity, orbit growth", grown, expected, "1%", abs(grown / expected - 1) <= 0.01, "km",
                  note="Gauss's equation da/dt = 2 a^2 v.push / mu")


def b9(density=7850.0, area=0.01, length=10.0, e_mod=200e9, inertia=1e-4, g=9.81):
    """Cantilever under its own weight: root moment q L^2 / 2 and tip deflection q L^4 / (8 E I), to 1%."""
    q = density * area * g
    moment, tip = cantilever(q, length, e_mod, inertia)
    exp_m, exp_d = q * length ** 2 / 2, q * length ** 4 / (8 * e_mod * inertia)
    return result("Cantilever under self-weight", [moment, tip], [exp_m, exp_d], "1%",
                  abs(moment / exp_m - 1) <= 0.01 and abs(tip / exp_d - 1) <= 0.01, "N m, m")


def b10(r_au=1.0, albedo=0.306):
    """Equilibrium temperature at 1 AU, albedo 0.306: about 254 K, to 2 K."""
    t = equilibrium_temperature(sunlight(r_au), albedo)
    return result("Equilibrium temperature", t, 254.0, "2 K", abs(t - 254.0) <= 2.0, "K")


ALL = {1: b1, 2: b2, 3: b3, 4: b4, 5: b5, 6: b6, 7: b7, 8: b8, 9: b9, 10: b10}


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the official benchmarks.")
    parser.add_argument("which", nargs="*", type=int, help="benchmark numbers (default: all)")
    parser.add_argument("--set", action="append", default=[], help="change an input, e.g. --set e=0.5")
    args = parser.parse_args()
    params = {}
    for kv in args.set:
        k, v = kv.split("=", 1)
        params[k] = eval(v, {"__builtins__": {}})  # numbers or tuples typed by a judge
    print(f"{'#':>2}  {'benchmark':34s} {'measured':>40s}  {'expected':>28s}  {'tolerance':>18s}  result")
    passed = []
    for n in args.which or ALL:
        fn = ALL[n]
        r = fn(**{k: v for k, v in params.items() if k in fn.__code__.co_varnames})
        passed.append(r["ok"])
        meas = r["measured"] if isinstance(r["measured"], (list, dict)) else f"{r['measured']:.6g}"
        exp = r["expected"] if isinstance(r["expected"], list) else f"{r['expected']:.6g}"
        print(f"{n:>2}  {r['name']:34s} {str(meas):>40s}  {str(exp):>28s}  {r['tolerance']:>18s}  "
              f"{'PASS' if r['ok'] else 'FAIL'} {r['unit']} {r['note']}")
    noun = "official benchmark passes" if len(passed) == 1 else "official benchmarks pass"
    print(f"\n{sum(passed)} of {len(passed)} {noun}." + ("" if all(passed) else " Some FAIL: see above."))
    if not all(passed):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
