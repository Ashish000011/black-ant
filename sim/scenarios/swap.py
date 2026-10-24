"""Plan S: swap Earth and Mars instead of pushing Mars out past the belt.

Mars is towed inward to Earth's old orbit while Earth is towed out to 2.7 AU, so the two orbits must cross once.
This tests that crossing from many starting points: how close does Mars come to Earth, does the crossing finish,
and what orbits are left? (The finished orbits' million-year stability is the parking scan's job.)

Each tow is modelled by the pull it puts on its planet, G m / d^2 toward its asteroid's spot, which is what the held
asteroid delivers (sim/forces.py keeps it within 1% of the spot). Earth's spot is the design's, 45 deg between
ahead and away from the Sun. Mars's is 45 deg between behind and away from the Sun: its pull slows Mars, so the
orbit shrinks, and the light holding the asteroid still arrives from the Sun's side. The beams and controller are
not simulated here. REBOUND's IAS15 (adaptive steps, exact through close passes) follows the Sun and Venus to
Neptune from their J2000 orbits.

Run from the project root (one run per CPU core):
    uv run python -m sim.scenarios.swap                         # 12 starting points of Mars along its orbit
    uv run python -m sim.scenarios.swap --mars-e 0.02           # Mars's orbit made nearly round first
    uv run python -m sim.scenarios.swap --sprint 4 --ease 0.56  # Mars's tow 4x across the crossing, Earth's eased
"""

import argparse
import copy
import json
import math
import time
from concurrent.futures import ProcessPoolExecutor

import rebound

from ..bodies import move_to_barycentre, start_planets
from ..config import ROOT, load_config
from ..constants import AU, G, YEAR

RADII_M = {"earth": 6.371e6, "mars": 3.3895e6}
CLOSE_AU = 0.05            # config.yaml safety.mars_min_distance_au: the closest Mars may come to Earth


def elements(p, s, mu):
    """Heliocentric orbit size (AU) and eccentricity of particle p around s."""
    rx, ry, rz = p.x - s.x, p.y - s.y, p.z - s.z
    vx, vy, vz = p.vx - s.vx, p.vy - s.vy, p.vz - s.vz
    r = math.sqrt(rx * rx + ry * ry + rz * rz)
    v2 = vx * vx + vy * vy + vz * vz
    rv = rx * vx + ry * vy + rz * vz
    a = 1.0 / (2.0 / r - v2 / mu)
    ex, ey, ez = ((v2 - mu / r) * rx - rv * vx) / mu, ((v2 - mu / r) * ry - rv * vy) / mu, ((v2 - mu / r) * rz - rv * vz) / mu
    return a / AU, math.sqrt(ex * ex + ey * ey + ez * ez)


def pull(p, s, sign, acc):
    """Add a tow's pull on planet p: acc (m/s^2) toward (out + sign * ahead) / sqrt 2 in its orbit plane."""
    rx, ry, rz = p.x - s.x, p.y - s.y, p.z - s.z
    vx, vy, vz = p.vx - s.vx, p.vy - s.vy, p.vz - s.vz
    r = math.sqrt(rx * rx + ry * ry + rz * rz)
    ox, oy, oz = rx / r, ry / r, rz / r
    hx, hy, hz = ry * vz - rz * vy, rz * vx - rx * vz, rx * vy - ry * vx
    h = math.sqrt(hx * hx + hy * hy + hz * hz)
    nx, ny, nz = hx / h, hy / h, hz / h
    tx, ty, tz = ny * oz - nz * oy, nz * ox - nx * oz, nx * oy - ny * ox  # ahead
    k = acc * math.sqrt(0.5)
    p.ax += k * (ox + sign * tx)
    p.ay += k * (oy + sign * ty)
    p.az += k * (oz + sign * tz)


def one(job: dict) -> dict:
    cfg = load_config()
    planets = copy.deepcopy(cfg["planets"])
    for p in planets:
        if p["name"] == "mars":
            p["mean_longitude_deg"] += job["phase"]
            if job["mars_e"] is not None:
                p["e"] = job["mars_e"]
    system = start_planets(planets, "real")
    move_to_barycentre(system)
    sim = rebound.Simulation()
    sim.G = G
    sim.integrator = "ias15"
    for m, r, v in zip(system.m, system.pos, system.vel):
        sim.add(m=float(m), x=float(r[0]), y=float(r[1]), z=float(r[2]), vx=float(v[0]), vy=float(v[1]), vz=float(v[2]))
    names = system.names
    iS, iE, iM = names.index("sun"), names.index("earth"), names.index("mars")
    ps = sim.particles
    muE, muM = G * (ps[iS].m + ps[iE].m), G * (ps[iS].m + ps[iM].m)
    tow = {t["target"]: t for t in cfg["tows"]}
    accE = G * tow["earth"]["asteroid_mass_kg"] / (tow["earth"]["distance_km"] * 1e3) ** 2
    accM = G * tow["mars"]["asteroid_mass_kg"] / (tow["mars"]["distance_km"] * 1e3) ** 2
    touch = RADII_M["earth"] + RADII_M["mars"]
    st = {"earth_on": True, "mars_on": True, "boost": False, "dmin": math.inf, "tmin": 0.0, "inside": False, "passes": [],
          "hit": None}

    def forces(_):
        s, e, m = ps[iS], ps[iE], ps[iM]
        if st["earth_on"]:
            pull(e, s, +1, accE * (job["ease"] if st["boost"] else 1.0))
        if st["mars_on"]:
            pull(m, s, -1, accM * (job["sprint"] if st["boost"] else 1.0))
        d = math.sqrt((e.x - m.x) ** 2 + (e.y - m.y) ** 2 + (e.z - m.z) ** 2)
        if d < st["dmin"]:
            st["dmin"], st["tmin"] = d, sim.t
        if d < CLOSE_AU * AU and not st["inside"]:
            st["inside"] = True
            st["passes"].append({"year": round(sim.t / YEAR, 1), "au": d / AU})
        elif st["inside"]:
            if d < st["passes"][-1]["au"] * AU:
                st["passes"][-1].update(year=round(sim.t / YEAR, 1), au=d / AU)
            if d > 1.2 * CLOSE_AU * AU:
                st["inside"] = False
        if d < touch and st["hit"] is None:
            st["hit"] = round(sim.t / YEAR, 2)

    sim.additional_forces = forces
    sim.force_is_velocity_dependent = 1
    started = time.time()
    samples, crossed, mars_arrived, earth_e_after = [], None, None, 0.0
    t_end, step = job["years"] * YEAR, job["sample_years"] * YEAR
    a_at_min = None
    while sim.t < t_end:
        sim.integrate(sim.t + step, exact_finish_time=0)
        aE, eE = elements(ps[iE], ps[iS], muE)
        aM, eM = elements(ps[iM], ps[iS], muM)
        samples.append([round(sim.t / YEAR, 1), round(aE, 4), round(eE, 4), round(aM, 4), round(eM, 4)])
        if abs(st["tmin"] - sim.t) <= step:
            a_at_min = (round(aE, 3), round(aM, 3))
        st["boost"] = st["mars_on"] and abs(aM - aE) < job["zone_au"]
        if crossed is None and aE > aM:
            crossed = {"year": round(sim.t / YEAR, 1), "au": round(aE, 3)}
        if crossed:
            earth_e_after = max(earth_e_after, eE)
        if st["mars_on"] and aM <= job["mars_target"]:
            st["mars_on"] = False
            mars_arrived = {"year": round(sim.t / YEAR, 1), "a_au": round(aM, 4), "e": round(eM, 4)}
        if st["hit"] is not None:
            break
        if not st["mars_on"] and crossed and aE - aM > 0.5:
            break
    last = samples[-1]
    return {**job, "crossed": crossed, "mars_arrived": mars_arrived, "closest_au": round(st["dmin"] / AU, 5),
            "closest_year": round(st["tmin"] / YEAR, 1), "a_at_closest": a_at_min, "collision_year": st["hit"],
            "passes_within_0p05_au": [{"year": p["year"], "au": round(p["au"], 5)} for p in st["passes"]],
            "earth_e_max_after_crossing": round(earth_e_after, 4), "end": {"year": last[0], "earth_a": last[1],
            "earth_e": last[2], "mars_a": last[3], "mars_e": last[4]}, "samples": samples[::4],
            "run_seconds": round(time.time() - started)}


def handover(job: dict) -> dict:
    """A swap by gravity alone, as Saturn's moons Janus and Epimetheus do: both tows off, Earth on job["a"] AU and
    Mars job["da"] AU farther out, both with eccentricity job["e"], Mars half an orbit ahead (opposite Earth).
    Co-orbital (horseshoe) dynamics should turn them round before they meet, swapping their orbit sizes."""
    cfg = load_config()
    planets = copy.deepcopy(cfg["planets"])
    earth = next(p for p in planets if p["name"] == "earth")
    mars = next(p for p in planets if p["name"] == "mars")
    earth.update(a_au=job["a"], e=job["e"])
    mars.update(a_au=job["a"] + job["da"], e=job["e"], perihelion_longitude_deg=earth["perihelion_longitude_deg"],
                mean_longitude_deg=earth["mean_longitude_deg"] + job["ahead_deg"])
    if job["flat"]:
        mars.update(i_deg=earth["i_deg"], node_longitude_deg=earth["node_longitude_deg"])
    system = start_planets(planets, "real")
    move_to_barycentre(system)
    sim = rebound.Simulation()
    sim.G = G
    sim.integrator = "ias15"
    for m, r, v in zip(system.m, system.pos, system.vel):
        sim.add(m=float(m), x=float(r[0]), y=float(r[1]), z=float(r[2]), vx=float(v[0]), vy=float(v[1]), vz=float(v[2]))
    iS, iE, iM = (system.names.index(n) for n in ("sun", "earth", "mars"))
    ps = sim.particles
    muE, muM = G * (ps[iS].m + ps[iE].m), G * (ps[iS].m + ps[iM].m)
    # job["retow"]: once Earth is the outer one, switch the tows back on (Mars's pull times `sprint`, Earth's times
    # `ease`) until the orbit sizes are 0.15 AU apart, and record how close they come while separating.
    tow = {t["target"]: t for t in cfg["tows"]}
    accE = G * tow["earth"]["asteroid_mass_kg"] / (tow["earth"]["distance_km"] * 1e3) ** 2
    accM = G * tow["mars"]["asteroid_mass_kg"] / (tow["mars"]["distance_km"] * 1e3) ** 2
    st = {"on": False, "dmin": math.inf}

    def forces(_):
        s, e, m = ps[iS], ps[iE], ps[iM]
        pull(e, s, +1, accE * job.get("ease", 1.0))
        pull(m, s, -1, accM * job.get("sprint", 1.0))
        st["dmin"] = min(st["dmin"], math.sqrt((e.x - m.x) ** 2 + (e.y - m.y) ** 2 + (e.z - m.z) ** 2))

    dmin, swaps, side, e_max, retow = math.inf, [], None, 0.0, None
    t = 0.0
    while t < job["years"] * YEAR:
        t += 0.05 * YEAR
        sim.integrate(t, exact_finish_time=0)
        e, m = ps[iE], ps[iM]
        dmin = min(dmin, math.sqrt((e.x - m.x) ** 2 + (e.y - m.y) ** 2 + (e.z - m.z) ** 2))
        aE, eE = elements(e, ps[iS], muE)
        aM, _ = elements(m, ps[iS], muM)
        e_max = max(e_max, eE)
        now = aE > aM
        if side is not None and now != side:
            swaps.append(round(sim.t / YEAR, 1))
        side = now
        if job.get("retow") and now and not st["on"] and swaps:
            st["on"] = True
            sim.additional_forces = forces
            sim.force_is_velocity_dependent = 1
            retow = {"year": round(sim.t / YEAR, 1)}
        if st["on"] and aE - aM > 0.15:
            retow.update(done_year=round(sim.t / YEAR, 1), closest_while_separating_au=round(min(st["dmin"], dmin) / AU, 4))
            break
    return {**job, "closest_au": round(dmin / AU, 4), "swaps_years": swaps[:6], "swap_count": len(swaps),
            "earth_e_max": round(e_max, 4), "retow": retow}


def parked_jobs(years: float) -> list:
    """The swapped end state for the parking scan: Earth as the arrival trim leaves it (as parking_scan3), Mars on
    Earth's old orbit, eccentric as today or made round, from two starting points; and Mars stopped at 1.25 AU,
    just past the crossing."""
    earth = {"earth_a": 2.7, "earth_e": 0.03, "earth_peri": "jupiter", "earth_i": 1.1349, "earth_node": 92.92}
    jobs = [{**earth, "name": f"Mars {a:.2f}, e {e}, phase {ph}", "mars_a": a, "mars_e": e, "mars_phase": ph}
            for a, e, ph in ((1.0, 0.0934, 0), (1.0, 0.0934, 120), (1.0, 0.02, 0), (1.0, 0.02, 120), (1.25, 0.05, 0))]
    return [(job, years) for job in jobs]


def main() -> None:
    ap = argparse.ArgumentParser(description="Earth out, Mars in: test the crossing.")
    ap.add_argument("--longterm", type=float, default=None, help="instead: run the swapped end state this many years")
    ap.add_argument("--handover", type=float, default=None, help="instead: test a tows-off swap for this many years")
    ap.add_argument("--mars-target", type=float, default=1.0, help="Mars's final orbit, AU (Earth's old one: 1.0)")
    ap.add_argument("--mars-e", type=float, default=None, help="Mars's starting eccentricity (default: today's)")
    ap.add_argument("--phases", type=int, default=12, help="starting points of Mars along its orbit")
    ap.add_argument("--sprint", type=float, default=1.0, help="Mars's pull, times normal, while the orbits are close")
    ap.add_argument("--ease", type=float, default=1.0, help="Earth's pull, times normal, meanwhile (E1's budget)")
    ap.add_argument("--zone", type=float, default=0.25, help="'close': orbit sizes within this many AU")
    ap.add_argument("--years", type=float, default=6000)
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--label", default="")
    args = ap.parse_args()
    if args.handover:
        jobs = [{"a": 1.2, "da": da, "e": e, "ahead_deg": 180.0, "flat": flat, "years": args.handover}
                for da in (0.0007, 0.0015, 0.003) for e in (0.001, 0.005, 0.02) for flat in (True,)]
        jobs += [{"a": 1.2, "da": 0.0015, "e": 0.001, "ahead_deg": 180.0, "flat": False, "years": args.handover}]
        # Then separate them: normal tows, and Mars sprinting with Earth eased (inside E1's 1e26 W)
        jobs += [{"a": 1.2, "da": 0.0015, "e": e, "ahead_deg": 180.0, "flat": True, "years": args.handover, "retow": True,
                  "sprint": sp, "ease": es} for e in (0.001, 0.02) for sp, es in ((1.0, 1.0), (4.0, 0.56))]
        with ProcessPoolExecutor(args.workers) as pool:
            res = list(pool.map(handover, jobs))
        (ROOT / "out").mkdir(exist_ok=True)
        (ROOT / "out" / "swap_handover.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
        for r in res:
            tail = (f"; tows back on in year {r['retow']['year']} (Mars x{r['sprint']}, Earth x{r['ease']}): closest while "
                    f"separating {r['retow'].get('closest_while_separating_au')} AU, 0.15 AU apart by year "
                    f"{r['retow'].get('done_year')}") if r.get("retow") else ""
            print(f"gap {r['da']:.4f} AU, e {r['e']:.3f}, {'same plane' if r['flat'] else 'Mars tilted as today'}: closest "
                  f"{r['closest_au']:.4f} AU; orbit sizes swapped {r['swap_count']} times (first at years "
                  f"{r['swaps_years']}); Earth e max {r['earth_e_max']}{tail}")
        return
    if args.longterm:
        from .parking import one as parked
        with ProcessPoolExecutor(args.workers) as pool:
            res = list(pool.map(parked, parked_jobs(args.longterm)))
        (ROOT / "out").mkdir(exist_ok=True)
        (ROOT / "out" / "swap_longterm.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
        for r in res:
            if "error" in r:
                print(f"{r['name']}: FAILED {r['error']}")
                continue
            near = [e for e in r["encounters"] if "earth" in e["bodies"] or "mars" in e["bodies"]]
            print(f"{r['name']:28s} | {r['years']:,.0f} yr | Earth a {r['earth_a_range']} e max {r['earth_e_max']} | "
                  f"Mars a {r['mars_a_range']} e max {r['mars_e_max']} | gap {r['earth_mars_gap_min_au']} | "
                  f"tilt {r['axial_tilt_deg']} | passes near Earth/Mars {len(near)} | thrown {[t['body'] for t in r['thrown_out']]}"
                  f" | stopped {r['stopped']}")
        print("Wrote out/swap_longterm.json")
        return
    jobs = [{"phase": k * 360 / args.phases, "mars_target": args.mars_target, "mars_e": args.mars_e, "sprint": args.sprint,
             "ease": args.ease, "zone_au": args.zone, "years": args.years, "sample_years": 5} for k in range(args.phases)]
    with ProcessPoolExecutor(args.workers) as pool:
        out = list(pool.map(one, jobs))
    (ROOT / "out").mkdir(exist_ok=True)
    path = ROOT / "out" / f"swap{('_' + args.label) if args.label else ''}.json"
    path.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"Mars in to {args.mars_target} AU, Mars e {args.mars_e or 'as today'}, sprint x{args.sprint}, Earth x{args.ease}")
    for r in out:
        c, m = r["crossed"], r["mars_arrived"]
        print(f"  start +{r['phase']:5.1f} deg: closest {r['closest_au']:.4f} AU in year {r['closest_year']:7.1f} "
              f"(a {r['a_at_closest']}); passes < {CLOSE_AU} AU: {len(r['passes_within_0p05_au']):3d}; "
              + (f"crossed year {c['year']} at {c['au']} AU; " if c else "NOT crossed; ")
              + (f"Mars at {m['a_au']} AU year {m['year']}; " if m else "Mars not arrived; ")
              + f"Earth e max after {r['earth_e_max_after_crossing']}; "
              + (f"COLLISION year {r['collision_year']}; " if r["collision_year"] else "")
              + f"{r['run_seconds']} s")
    safe = [r for r in out if r["closest_au"] >= CLOSE_AU and r["crossed"]]
    print(f"Safe (never within {CLOSE_AU} AU, crossing done): {len(safe)} of {len(out)}. Wrote {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
