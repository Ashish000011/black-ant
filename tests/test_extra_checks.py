"""Our own extra checks X1 to X8 (the official ten benchmarks are in test_official_benchmarks.py).

Run all:            uv run pytest -v
Skip the slow ones: uv run pytest -v -m "not slow"
Each test prints the value it measured, so it can be quoted on a slide (add -s to see prints).
"""

import math

import numpy as np
import pytest

from sim.bodies import circular_planets, move_to_barycentre, orbit_elements, real_planets
from sim.config import load_config
from sim.constants import AU, DAY, G, GM_SUN, M_SUN, YEAR
from sim.integrator import energy, gravity, leapfrog
from sim.scenarios.tow import run

CFG = load_config()
EARTH_MASS = 6.04562e24


def sun_and_earth():
    system = circular_planets([{"name": "earth", "mass_kg": EARTH_MASS, "a_au": 1.0, "mean_longitude_deg": 0.0}])
    move_to_barycentre(system)
    return system


def test_config_numbers_are_numbers():
    assert isinstance(CFG["tows"][0]["asteroid_mass_kg"], float)
    assert isinstance(CFG["planets"][0]["mass_kg"], float)


def test_real_orbits_match_their_elements():
    """Positions built from JPL's elements give back the same orbit size, eccentricity and tilt."""
    system = real_planets(CFG["planets"])
    for p in CFG["planets"]:
        o = orbit_elements(system, system.index(p["name"]))
        assert abs(o["a"] / p["a_au"] - 1) < 1e-5, p["name"]
        assert abs(o["e"] - p["e"]) < 1e-5, p["name"]
        assert abs(o["i"] - abs(p["i_deg"])) < 1e-4, p["name"]


def test_x1_period_matches_kepler():
    """X1: Sun and Earth on a circular orbit for 100 years; period within 0.001% of Kepler's law.
    Uses tenth-of-a-day steps: the period error grows with the square of the step (2.5e-5 at half a day)."""
    system = sun_and_earth()
    dt, years = 0.1 * DAY, 100
    angle = {"last": 0.0, "total": 0.0}

    def track(_, pos, __):
        a = math.atan2(pos[1, 1] - pos[0, 1], pos[1, 0] - pos[0, 0])
        angle["total"] += (a - angle["last"] + math.pi) % (2 * math.pi) - math.pi
        angle["last"] = a

    leapfrog(system.m, system.pos, system.vel, dt, round(years * YEAR / dt), track)
    measured = years * YEAR / (angle["total"] / (2 * math.pi))
    kepler = 2 * math.pi * math.sqrt(AU ** 3 / (G * (M_SUN + EARTH_MASS)))
    error = abs(measured / kepler - 1)
    print(f"X1 period error {error:.2e}")
    assert error < 1e-5


@pytest.mark.slow
def test_x2_energy_steady_for_1000_years():
    """X2: Sun and five planets on their real orbits for 1,000 years; energy error below 1 part in a
    million, no steady drift."""
    system = real_planets(CFG["planets"])
    move_to_barycentre(system)
    e0 = energy(system.m, system.pos, system.vel)
    errors = []

    def track(step, pos, vel):
        if step % 2000 == 0:
            errors.append(abs(energy(system.m, pos, vel) / e0 - 1))

    dt = 0.5 * DAY
    leapfrog(system.m, system.pos, system.vel, dt, round(1000 * YEAR / dt), track)
    half = len(errors) // 2
    print(f"X2 energy error max {max(errors):.2e}")
    assert max(errors) < 1e-6
    assert max(errors[half:]) < 2 * max(errors[:half]) + 1e-12  # no steady drift


def test_x3_momentum_with_ledger():
    """X3: the guide's ledger check on a 20-year tow run: the bodies' momentum change equals the applied impulse,
    and the applied impulse plus its partners (station recoil, bounced light) is zero, each to 1e-9 of it."""
    summary, _, _ = run(years=20, belt=False)
    lg = summary["ledger"]
    print(f"X3 integrator honest {lg['integrator_honest_max']:.1e}; nothing from nothing {lg['nothing_from_nothing_max']:.1e}")
    assert lg["integrator_honest_max"] < 1e-9
    assert lg["nothing_from_nothing_max"] < 1e-9


def test_x4_hohmann_transfer():
    """X4: Hohmann transfer from 1 to 2.7 AU; speed change within 0.1% of 11.00 km/s, and the
    simulated transfer really reaches 2.7 AU."""
    r1, r2 = AU, 2.7 * AU
    v1, v2 = math.sqrt(GM_SUN / r1), math.sqrt(GM_SUN / r2)
    a_t = (r1 + r2) / 2
    vp, va = math.sqrt(GM_SUN * (2 / r1 - 1 / a_t)), math.sqrt(GM_SUN * (2 / r2 - 1 / a_t))
    dv = (vp - v1) + (v2 - va)
    print(f"X4 Hohmann speed change {dv / 1e3:.3f} km/s")
    assert abs(dv / 11.0e3 - 1) < 1e-3
    # Simulate the transfer: a massless test body starting at 1 AU with the first burn already applied.
    m = np.array([M_SUN, 0.0])
    pos = np.array([[0.0, 0.0], [r1, 0.0]])
    vel = np.array([[0.0, 0.0], [0.0, vp]])
    half_period = math.pi * math.sqrt(a_t ** 3 / GM_SUN)
    dt = 0.05 * DAY
    leapfrog(m, pos, vel, dt, round(half_period / dt))
    reached = math.hypot(*(pos[1] - pos[0]))
    print(f"X4 transfer reached {reached / AU:.5f} AU")
    assert abs(reached / r2 - 1) < 1e-3


def test_x5_steady_push_arrival_time():
    """X5: a steady push along the orbit; arrival time at 2.7 AU within 1% of mass x 11.66 km/s / push.
    The push is scaled up so the test takes seconds; the physics is the same gentle spiral."""
    accel = 1.2e-5  # m/s^2, still 500 times weaker than the Sun's pull at 1 AU
    dv = math.sqrt(GM_SUN / AU) - math.sqrt(GM_SUN / (2.7 * AU))
    predicted = dv / accel
    pos, vel = np.array([AU, 0.0]), np.array([0.0, math.sqrt(GM_SUN / AU)])
    dt, t = 0.25 * DAY, 0.0

    def acc(p, v):
        r = np.hypot(*p)
        return -GM_SUN * p / r ** 3 + accel * v / np.hypot(*v)

    a = acc(pos, vel)
    while True:
        vel = vel + a * dt / 2
        pos = pos + vel * dt
        a = acc(pos, vel)
        vel = vel + a * dt / 2
        t += dt
        r, v2 = np.hypot(*pos), float(vel @ vel)
        if 1 / (2 / r - v2 / GM_SUN) >= 2.7 * AU:
            break
    error = abs(t / predicted - 1)
    print(f"X5 arrival time error {error:.2%}")
    assert error < 0.01


@pytest.mark.slow
def test_x6_matches_rebound():
    """X6: our stepper against REBOUND's high-accuracy IAS15, Sun and five planets on their real
    orbits for 100 years; Earth's orbit size agrees within 1e-6 AU."""
    rebound = pytest.importorskip("rebound")
    ours = real_planets(CFG["planets"])
    move_to_barycentre(ours)
    sim = rebound.Simulation()
    sim.G = G
    for k in range(len(ours.m)):
        sim.add(m=float(ours.m[k]), x=float(ours.pos[k, 0]), y=float(ours.pos[k, 1]), z=float(ours.pos[k, 2]),
                vx=float(ours.vel[k, 0]), vy=float(ours.vel[k, 1]), vz=float(ours.vel[k, 2]))
    sim.integrator = "ias15"
    years, dt = 100, 0.1 * DAY
    sim.integrate(years * YEAR)
    leapfrog(ours.m, ours.pos, ours.vel, dt, round(years * YEAR / dt))
    earth = ours.index("earth")
    ref = real_planets(CFG["planets"])  # same names and masses; fill in REBOUND's final state
    for k, p in enumerate(sim.particles):
        ref.pos[k] = (p.x, p.y, p.z)
        ref.vel[k] = (p.vx, p.vy, p.vz)
    a_ours, a_ref = orbit_elements(ours, earth)["a"], orbit_elements(ref, earth)["a"]
    print(f"X6 Earth orbit size ours {a_ours:.9f} AU, REBOUND {a_ref:.9f} AU")
    assert abs(a_ours - a_ref) < 1e-6


def test_x7_asteroid_pull_and_hold():
    """X7: the asteroid's pull on Earth equals G x asteroid mass / distance^2, and the tow holds the
    asteroid on its spot (within 0.1% of its distance) over 20 years."""
    tow = CFG["tows"][0]
    d, mass = tow["distance_km"] * 1e3, tow["asteroid_mass_kg"]
    acc = gravity(np.array([EARTH_MASS, mass]), np.array([[0.0, 0.0], [d, 0.0]]))
    expected = G * mass / d ** 2
    assert abs(acc[0, 0] / expected - 1) < 1e-12
    summary, _, _ = run(years=20, belt=False)
    held = summary["tows"]["earth-tow"]["spot_error_max_km"]
    print(f"X7 Earth's tow acceleration {expected:.3e} m/s^2; asteroid held within {held:.0f} km")
    assert held < 0.001 * d / 1e3


def test_x8_octo_earth_net_push_is_zero():
    """X8: Octo-Earth's arms, curled over the planet as the demo draws them and energised in Earth's own field, push
    on Earth's core exactly as hard as the core's field pushes on them, so Earth plus machine gets no net force; in a
    uniform outside field closed circuits feel none."""
    from sim.scenarios.octo import curl_shape, net_force, outside_field
    o = dict(CFG["octo_earth"], segment_km=200)
    c = curl_shape(o)                                         # the demo's shape: the claw 72 deg away, 4,600 km up
    assert abs(c["reach_deg"] - 72) < 0.05 and abs(c["tip_altitude_km"] - 4600) < 5 and c["lowest_joint_km"] > 200
    for arms in ([0], list(range(o["arms"]))):
        n = net_force(o, arms)
        print(f"X8 arms {n['arms']}: on the arms {np.linalg.norm(n['on_arms_n']):.3e} N, sum {n['sum_over_force']:.1e} of it")
        assert np.linalg.norm(n["on_arms_n"]) > 1e5          # a real force on the arms...
        assert n["sum_over_force"] < 1e-9                     # ...and its exact partner on Earth's core
    f = outside_field(o)
    assert f["closed_circuits_n"] < 1e-9 * f["scale_i_l_b_n"]


def test_x8_octo_earth_curled_arm_breaks_at_its_root():
    """X8: curled over the planet as drawn, an arm is a beam held only at its root, and its weight breaks it there long
    before 12,000 km in every material, sooner than the same arm standing straight up would buckle. A short arm, still
    nearly straight, matches the textbook tilted cantilever: weight along it over the area, plus q L^2 cos(e) / 2
    bending over the section modulus."""
    import math
    from sim.scenarios.octo import arm_path, curled_root, materials
    o = CFG["octo_earth"]
    for m in materials(o, CFG["safety"]["structural_safety_factor_min"]):
        print(f"X8 {m['name']}: curled 12,000 km SF {m['lengths'][-1]['curled_sf']:.2e}, holds up to "
              f"{m['curled_longest_km']:,.0f} km; standing it buckles past {m['buckling_length_km']:,.0f} km")
        assert m["lengths"][-1]["curled_sf"] < 0.02
        assert m["curled_longest_km"] < m["buckling_length_km"]
        assert m["curled_bending_share"] > 0.95 and m["curled_push_over_euler"] > 100   # it bends; it would buckle too
    nodes, _ = arm_path(o, 0)
    up, along = nodes[0] / np.linalg.norm(nodes[0]), (nodes[1] - nodes[0]) / np.linalg.norm(nodes[1] - nodes[0])
    e = math.asin(np.dot(along, up))                          # the root's elevation above its own horizon
    d, t, L = o["outer_diameter_km"] * 1e3, o["wall_km"] * 1e3, 50e3
    area, inertia = math.pi / 4 * (d ** 2 - (d - 2 * t) ** 2), math.pi / 64 * (d ** 4 - (d - 2 * t) ** 4)
    steel = o["materials"][0]
    q = steel["density"] * 9.81 * area
    by_hand = q * L * math.sin(e) / area + q * L ** 2 * math.cos(e) / 2 * (d / 2) / inertia
    assert abs(curled_root(o, steel, L)["stress_pa"] / by_hand - 1) < 0.02
