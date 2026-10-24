"""After arrival: does the moved solar system stay as we left it?

Starts from out/end_state.json (the journey's final positions and velocities; the tow asteroids are
already gone) and runs REBOUND's MERCURIUS integrator, which hands close encounters to a
high-accuracy method. The same run of the real, unmoved solar system from J2000 is the yardstick:
anything the moved system does that the real one also does is natural, not our doing.

Every sample_years it records each planet's orbit; it logs every pass closer than encounter_au
between any two bodies, and stops if a body is thrown out. Earth's axial tilt is then followed on top
of its recorded orbit plane: the Sun and Moon pull on Earth's equatorial bulge and turn the spin axis
around the orbit's pole. At 2.7 AU the Sun's share of that pull drops about 20 times, so the axis turns
more slowly; if that rate lands on one of the orbit plane's own wobble rates, the tilt can swing wildly
(as Mars's does). The real solar system run should give back today's 22.1-24.5 degree cycle.

Run from the project root (after the journey has written out/end_state.json):
    uv run python -m sim.scenarios.longterm                    # settings from config.yaml (1 million years)
    uv run python -m sim.scenarios.longterm --years 10000      # a quick look
    uv run python -m sim.scenarios.longterm --only moved       # skip the baseline
"""

import argparse
import json
import math
import time
from pathlib import Path

import numpy as np

from ..bodies import add_state_bodies, move_to_barycentre, start_planets
from ..config import ROOT, load_config
from ..constants import AU, DAY, G, YEAR
from ..flags import Flags, check
from ..checks.safety import nudge_hours
from ..spin import follow_spin, seasons_shift

TRACKED = ("venus", "earth", "mars", "jupiter", "saturn", "ceres", "vesta", "pallas", "hygiea")
PLANETS = ("sun", "venus", "earth", "mars", "jupiter", "saturn", "uranus", "neptune")


def moved_state(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def baseline_state(cfg: dict) -> dict:
    """The real solar system at J2000, same bodies as the journey, nothing moved."""
    system = start_planets(cfg["planets"], "real")
    add_state_bodies(system, cfg.get("small_bodies", []))
    move_to_barycentre(system)
    return {"year": 0.0, "names": system.names, "mass_kg": system.m.tolist(),
            "pos_m": system.pos.tolist(), "vel_m_s": system.vel.tolist()}


def make_sim(state: dict, dt_days: float):
    import rebound
    sim = rebound.Simulation()
    sim.G = G
    for name, mass, p, v in zip(state["names"], state["mass_kg"], state["pos_m"], state["vel_m_s"]):
        sim.add(m=mass, x=p[0], y=p[1], z=p[2], vx=v[0], vy=v[1], vz=v[2])
    sim.move_to_com()
    sim.integrator = "mercurius"
    sim.dt = dt_days * DAY
    return sim


def orbits(sim, names: list[str]) -> dict:
    sun = sim.particles[0]
    out = {}
    for k, name in enumerate(names):
        if name in TRACKED:
            o = sim.particles[k].orbit(primary=sun)
            out[name] = (o.a / AU, o.e, math.degrees(o.inc), o.inc, o.Omega)
    return out


def run_one(state: dict, years: float, cfg: dict, label: str, progress: bool = True) -> dict:
    lt = cfg["longterm"]
    sim = make_sim(state, lt["dt_days"])
    names = list(state["names"])
    sample = lt["sample_years"] * YEAR
    encounter = lt["encounter_au"] * AU
    sim.exit_min_distance = encounter
    sim.exit_max_distance = lt["escape_au"] * AU
    e0 = sim.energy()
    series = {n: {"a": [], "e": [], "i": []} for n in names if n in TRACKED}
    earth_pole = []  # Earth's orbit pole (unit vector, ecliptic J2000) at each sample
    times, gaps, ratio = [], [], []
    encounters = []
    thrown_out = []
    stopped = None
    started = time.time()
    t_end = years * YEAR
    t_next = 0.0
    while sim.t < t_end and stopped is None:
        try:
            sim.integrate(min(t_next, t_end), exact_finish_time=0)
        except Exception as err:  # rebound raises Encounter or Escape
            kind = type(err).__name__
            if kind == "Encounter":
                d, pair = closest_pair(sim, names)
                encounters.append({"year": round(sim.t / YEAR, 1), "bodies": pair, "au": round(d / AU, 5)})
                sim.exit_min_distance = 0.0  # let the pass finish, then watch again
                sim.integrate(sim.t + lt["encounter_pause_years"] * YEAR, exact_finish_time=0)
                sim.exit_min_distance = encounter
                continue
            if kind == "Escape":
                far = int(np.argmax([q.x * q.x + q.y * q.y + q.z * q.z for q in sim.particles]))
                thrown_out.append({"year": round(sim.t / YEAR, 1), "body": names[far]})
                if names[far] in PLANETS:
                    stopped = {"year": round(sim.t / YEAR, 1), "why": f"{names[far]} thrown out"}
                    break
                sim.remove(far)
                names.pop(far)
                continue
            stopped = {"year": round(sim.t / YEAR, 1), "why": kind}
            break
        if sim.t >= t_next - 1.0:
            orb = orbits(sim, names)
            times.append(round(sim.t / YEAR))
            for n, (a, e, i, _, _) in orb.items():
                series[n]["a"].append(round(a, 5))
                series[n]["e"].append(round(e, 5))
                series[n]["i"].append(round(i, 4))
            ea, ee, _, inc, node = orb["earth"]
            ma, me = orb["mars"][:2]
            earth_pole.append([math.sin(inc) * math.sin(node), -math.sin(inc) * math.cos(node), math.cos(inc)])
            gaps.append(round(ma * (1 - me) - ea * (1 + ee) if ma > ea else ea * (1 - ee) - ma * (1 + me), 5))
            ratio.append(round((orb["jupiter"][0] / ma) ** 1.5, 5))
            t_next += sample
            if progress and len(times) % max(1, round(len(range(0, int(years), int(lt["sample_years"]))) / 10)) == 0:
                print(f"  {label}: year {sim.t / YEAR:9.0f}  Earth a {ea:.4f} e {ee:.4f}  Mars a {ma:.4f} e {me:.4f}  "
                      f"({time.time() - started:.0f} s)", flush=True)
    energy_error = abs((sim.energy() - e0) / e0)
    ranges = {n: {k: [min(v), max(v)] for k, v in s.items() if v} for n, s in series.items()}
    tilt, _ = follow_spin(times, earth_pole, series["earth"]["a"], series["earth"]["e"], cfg["spin"],
                          state.get("spin_axis"))
    return {"label": label, "start_year": state["year"], "years": round(sim.t / YEAR), "stopped": stopped,
            "thrown_out": thrown_out,
            "energy_error": energy_error, "encounters": encounters, "ranges": ranges,
            "earth_mars_orbit_gap_min_au": min(gaps) if gaps else None,
            "jupiter_mars_period_ratio": [min(ratio), max(ratio)] if ratio else None,
            "axial_tilt_deg": [round(min(tilt), 3), round(max(tilt), 3)] if tilt else None,
            "series": {"year": times, "orbits": series, "earth_mars_gap_au": gaps, "jupiter_mars_period_ratio": ratio,
                       "axial_tilt_deg": [round(x, 3) for x in tilt],
                       "earth_pole": [[round(c, 7) for c in v] for v in earth_pole]},
            "run_seconds": round(time.time() - started, 1)}


def closest_pair(sim, names: list[str]) -> tuple[float, list[str]]:
    p = np.array([[q.x, q.y, q.z] for q in sim.particles])
    d = np.linalg.norm(p[:, None, :] - p[None, :, :], axis=2)
    np.fill_diagonal(d, np.inf)
    i, j = np.unravel_index(np.argmin(d), d.shape)
    return float(d[i, j]), [names[i], names[j]]


def judge(moved: dict, base: dict | None, cfg: dict) -> dict:
    """Checks on the moved system; limits from config.yaml, with the real solar system alongside."""
    lt, s = cfg["longterm"], cfg["safety"]
    flags = Flags()
    yr = moved["years"]
    flags.record(check("Run finished without a planet thrown out", 0 if moved["stopped"] is None else 1, 0, "max"), yr)
    flags.record(check("Energy error over the run", moved["energy_error"], lt["energy_error_max"], "max"), yr)
    r = moved["ranges"]
    target = cfg["arrival"]["target_au"]
    flags.record(check("Earth's orbit size drift from the target", max(abs(a - target) for a in r["earth"]["a"]) / target,
                       lt["earth_a_drift_max_fraction"], "max", "share"), yr)
    flags.record(check("Earth's highest eccentricity", r["earth"]["e"][1], lt["earth_max_eccentricity"], "max"), yr)
    flags.record(check("Smallest gap between Earth's and Mars's orbits", moved["earth_mars_orbit_gap_min_au"],
                       s["mars_min_distance_au"], "min", "AU"), yr)
    near_earth = [e for e in moved["encounters"] if "earth" in e["bodies"]]
    # E1 nudges each one decades ahead so it passes outside the encounter distance.
    nd = lt["nudge"]
    masses = {b["name"]: b["mass_kg"] for b in cfg.get("small_bodies", [])}
    hours = []
    for e in near_earth:
        other = next(b for b in e["bodies"] if b != "earth")
        hours.append(nudge_hours(masses.get(other, 0.0), (lt["encounter_au"] - e["au"]) * AU, nd))
    flags.record(check("Passes near Earth closer than the encounter distance", len(near_earth), 0, "max", "passes",
                       covered_by="E1" if near_earth and max(hours) <= nd["max_hours"] else None), yr)
    out = {}
    if moved["axial_tilt_deg"] and base and base.get("axial_tilt_deg"):
        lo, hi = base["axial_tilt_deg"]
        m_lo, m_hi = moved["axial_tilt_deg"]
        today = cfg["spin"]["tilt_today_deg"]
        # Tilt only moves sunlight between latitudes and seasons. The sunlight mirrors (E3) already supply
        # 1 - 1/a^2 of Earth's sunlight at a AU, so they can re-aim that much to give today's seasons back.
        need = max(seasons_shift(m_lo, today), seasons_shift(m_hi, today))
        natural = max(seasons_shift(lo, today), seasons_shift(hi, today))
        mirrors = 1 - 1 / target ** 2
        swing = (m_hi - m_lo) / (hi - lo)
        flags.record(check("Axial tilt swing compared with the real Earth's", swing, lt["tilt_swing_max_times_natural"],
                           "max", "times the real swing",
                           covered_by="E3" if swing > lt["tilt_swing_max_times_natural"] and need <= mirrors else None), yr)
        flags.record(check("Sunlight the mirrors must re-aim to keep today's seasons", need, mirrors, "max",
                           "share of Earth's sunlight"), yr)
        out["seasons"] = {"tilt_deg": moved["axial_tilt_deg"], "real_tilt_deg": base["axial_tilt_deg"],
                          "sunlight_to_reaim": need, "real_earth_own_shift": natural, "mirror_supplied_share": mirrors}
    out["big_asteroid_nudges"] = {"passes": len(near_earth), "warning_years": nd["warning_years"], "beam_w": nd["beam_w"],
                                  "longest_beam_hours": max(hours) if hours else 0.0}
    out["flags"] = flags.summary()
    if base:
        out["compared_with_real_solar_system"] = {
            n: {"moved": moved["ranges"].get(n), "real": base["ranges"].get(n)} for n in ("earth", "mars", "jupiter", "venus")}
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Long-term stability after arrival.")
    parser.add_argument("--years", type=float, help="length of each run (default: config.yaml)")
    parser.add_argument("--only", choices=["moved", "baseline"], help="run just one of the two")
    parser.add_argument("--state", default=str(ROOT / "out" / "end_state.json"), help="journey end state")
    parser.add_argument("--out", help="output file (default: out/longterm.json, or out/longterm_baseline.json)")
    parser.add_argument("--perturb-m", type=float, default=0.0,
                        help="move Earth this far in a random direction first: a chaos check (same result = robust)")
    parser.add_argument("--seed", type=int, default=0, help="direction of the --perturb-m move")
    args = parser.parse_args()
    cfg = load_config()
    years = args.years or cfg["longterm"]["years"]
    baseline_file = ROOT / "out" / "longterm_baseline.json"
    out = args.out or (baseline_file if args.only == "baseline" else ROOT / "out" / "longterm.json")
    result = {"settings": {"years": years, **cfg["longterm"]}}
    if args.only != "baseline":
        state = moved_state(Path(args.state))
        if args.perturb_m:
            k = state["names"].index("earth")
            u = np.random.default_rng(args.seed).normal(size=3)
            state["pos_m"][k] = (np.array(state["pos_m"][k]) + args.perturb_m * u / np.linalg.norm(u)).tolist()
            result["settings"]["perturb_m"], result["settings"]["seed"] = args.perturb_m, args.seed
        result["moved"] = run_one(state, years, cfg, "moved")
    if args.only != "moved":
        result["baseline"] = run_one(baseline_state(cfg), years, cfg, "real")
    elif baseline_file.exists():  # a baseline run earlier with --only baseline
        earlier = json.loads(baseline_file.read_text(encoding="utf-8"))["baseline"]
        if earlier["years"] >= years:
            result["baseline"] = earlier
    if "moved" in result:
        result["verdict"] = judge(result["moved"], result.get("baseline"), cfg)
    Path(out).write_text(json.dumps(result), encoding="utf-8")
    for key in ("moved", "baseline"):
        if key in result:
            r = result[key]
            print(f"{r['label']}: {r['years']} years in {r['run_seconds']} s, energy error {r['energy_error']:.1e}, "
                  f"stopped: {r['stopped']}")
            for n in ("venus", "earth", "mars", "jupiter"):
                rr = r["ranges"][n]
                print(f"  {n:8s} a {rr['a'][0]:.4f}-{rr['a'][1]:.4f} AU   e {rr['e'][0]:.4f}-{rr['e'][1]:.4f}   "
                      f"tilt {rr['i'][0]:.2f}-{rr['i'][1]:.2f} deg")
            print(f"  Earth's axial tilt {r['axial_tilt_deg']} deg")
            print(f"  Earth-Mars orbit gap min {r['earth_mars_orbit_gap_min_au']} AU; Jupiter/Mars period ratio "
                  f"{r['jupiter_mars_period_ratio']}; close passes logged: {len(r['encounters'])}")
            for e in r["encounters"][:10]:
                print(f"    year {e['year']}: {e['bodies'][0]}-{e['bodies'][1]} at {e['au']} AU")
    if "verdict" in result:
        fl = result["verdict"]["flags"]
        print(f"Flags: {fl['unresolved']} unresolved")
        for f in fl["flags"]:
            print(f"  [{f['covered_by'] or 'UNRESOLVED'}] {f['check']}: worst {f['worst']:.4g} (limit {f['limit']:.4g})")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
