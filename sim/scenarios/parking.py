"""Where can Earth and Mars park? A quick scan of finished arrangements.

Instead of re-running the whole journey for each choice, this places Earth and Mars straight onto
their final orbits (every other body where it really was at J2000) and runs each arrangement through
REBOUND, recording how far the orbits wander. Used to choose Mars's parking orbit and to test Plan B
choices; the full journey then confirms the winner. Arrangements run side by side, one per CPU core.

Run from the project root:
    uv run python -m sim.scenarios.parking                              # config.yaml's list
    uv run python -m sim.scenarios.parking --mars 3.0 3.4 --years 1e6
"""

import argparse
import copy
import json
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from ..bodies import add_state_bodies, move_to_barycentre, start_planets
from ..config import ROOT, load_config
from .longterm import run_one

# Jupiter's strongest resonances near the parking zone: (inner:outer periods, distance in AU)
RESONANCES = {"3:1": 2.50, "8:3": 2.71, "5:2": 2.82, "7:3": 2.96, "9:4": 3.03, "2:1": 3.28}


def parked_state(cfg: dict, job: dict) -> dict:
    """job: earth_a, mars_a, and optionally earth_e, mars_e, and earth_peri / mars_peri ("jupiter" lines the
    perihelion up with Jupiter's, where Jupiter's pull settles an inner orbit's eccentricity)."""
    p = cfg["parking"]
    planets = copy.deepcopy(cfg["planets"])
    jupiter_peri = next(b for b in planets if b["name"] == "jupiter")["perihelion_longitude_deg"]
    for body in planets:
        for name in ("earth", "mars"):
            if body["name"] != name:
                continue
            body.update(a_au=job[f"{name}_a"], e=job.get(f"{name}_e", p[f"{name}_e"]))
            if name == "earth":
                body["i_deg"] = job.get("earth_i", p["earth_i_deg"])
                if "earth_node" in job:
                    body["node_longitude_deg"] = job["earth_node"]
            body["mean_longitude_deg"] += job.get(f"{name}_phase", 0.0)  # start elsewhere along the orbit
            peri = job.get(f"{name}_peri")
            if peri is not None:
                new = jupiter_peri if peri == "jupiter" else float(peri)
                # keep the planet where it is along its orbit: shift the mean longitude with the perihelion
                body["mean_longitude_deg"] += new - body["perihelion_longitude_deg"]
                body["perihelion_longitude_deg"] = new
    system = start_planets(planets, "real")
    add_state_bodies(system, cfg.get("small_bodies", []))
    move_to_barycentre(system)
    return {"year": 0.0, "names": system.names, "mass_kg": system.m.tolist(),
            "pos_m": system.pos.tolist(), "vel_m_s": system.vel.tolist()}


def one(args: tuple) -> dict:
    job, years = args
    try:
        return _one(job, years)
    except Exception as err:  # one failed arrangement must not lose the others
        return {**job, "error": f"{type(err).__name__}: {err}"}


def _one(job: dict, years: float) -> dict:
    cfg = load_config()
    r = run_one(parked_state(cfg, job), years, cfg, job.get("name", ""), progress=False)
    rg = r["ranges"]
    return {**job, "years": r["years"], "stopped": r["stopped"], "thrown_out": r["thrown_out"],
            "axial_tilt_deg": r["axial_tilt_deg"],
            "energy_error": r["energy_error"],
            "earth_a_range": rg["earth"]["a"], "earth_e_max": rg["earth"]["e"][1],
            "mars_a_range": rg["mars"]["a"], "mars_e_max": rg["mars"]["e"][1],
            "earth_mars_gap_min_au": r["earth_mars_orbit_gap_min_au"],
            "jupiter_mars_period_ratio": r["jupiter_mars_period_ratio"],
            "encounters": r["encounters"], "run_seconds": r["run_seconds"]}


def main() -> None:
    parser = argparse.ArgumentParser(description="Scan parking orbits for Earth and Mars.")
    parser.add_argument("--earth", type=float, nargs="+", help="Earth orbit sizes, AU (default: config.yaml)")
    parser.add_argument("--mars", type=float, nargs="+", help="Mars orbit sizes, AU (default: config.yaml)")
    parser.add_argument("--years", type=float, help="length of each run (default: config.yaml)")
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--out", default=str(ROOT / "out" / "parking.json"))
    args = parser.parse_args()
    cfg = load_config()
    p = cfg["parking"]
    years = args.years or p["years"]
    if args.earth or args.mars:
        jobs = [{"name": f"earth {e} mars {m}", "earth_a": e, "mars_a": m}
                for e in (args.earth or [2.7]) for m in (args.mars or [3.1])]
    else:
        jobs = p["arrangements"]
    jobs = [(job, years) for job in jobs]
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        results = list(pool.map(one, jobs))
    Path(args.out).write_text(json.dumps({"years": years, "resonances_au": RESONANCES, "results": results}, indent=1),
                              encoding="utf-8")
    print(f"{'arrangement':34s} | {'Earth a range':>15} {'e max':>7} | {'Mars a range':>15} {'e max':>7} | "
          f"{'gap min':>7} | near Earth | tilt | thrown out | stopped")
    for r in results:
        if "error" in r:
            print(f"{r.get('name', ''):34s} | FAILED: {r['error']}")
            continue
        near = [e for e in r["encounters"] if "earth" in e["bodies"]]
        closest = f"{len(near)}, {min(e['au'] for e in near):.4f} AU" if near else "0"
        print(f"{r.get('name', ''):34s} | {r['earth_a_range'][0]:.4f}-{r['earth_a_range'][1]:.4f} "
              f"{r['earth_e_max']:7.4f} | {r['mars_a_range'][0]:.4f}-{r['mars_a_range'][1]:.4f} {r['mars_e_max']:7.4f} | "
              f"{r['earth_mars_gap_min_au']:7.4f} | {closest} | {r['axial_tilt_deg']} | "
              f"{[t['body'] for t in r['thrown_out']]} | {r['stopped']}")
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
