"""How often does Jupiter's 2:1 resonance (3.28 AU) catch Mars as its tow pulls it across?

Mars starts at 2.95 AU from several points along its orbit, and only Mars's tow runs (Earth is far inside at
that time). Each variant is a different pull across the resonance. A caught Mars never reaches its parking
orbit. This is why Mars's tow sprints across 3.0-3.5 AU (config.yaml, tows).

Run from the project root (about 15 minutes; one run per CPU core):
    uv run python -m sim.scenarios.crossing
"""

import copy
import json
from concurrent.futures import ProcessPoolExecutor

from ..config import ROOT, load_config
from .tow import run


def one(args: tuple) -> dict:
    variant, phase = args
    cfg = load_config()
    c = cfg["crossing"]
    mars = next(t for t in cfg["tows"] if t["name"] == "mars-tow")
    mars.pop("sprint", None)
    sprint = c["variants"][variant]
    if sprint:
        mars["sprint"] = copy.deepcopy(sprint)
    cfg["tows"] = [mars]  # only Mars's tow
    for p in cfg["planets"]:
        if p["name"] == "mars":
            p.update(a_au=c["start_a_au"], e=c["start_e"])
            p["mean_longitude_deg"] += phase
    s, frames, _ = run(cfg, years=c["years"], belt=False)
    t = s["tows"]["mars-tow"]
    return {"variant": variant, "phase": phase, "arrival": t["arrival"],
            "mars_a_max": max(f["mars_orbit_au"] for f in frames), "beam_max_w": t["beam_max_w"],
            "spot_error_max_km": t["spot_error_max_km"]}


def main() -> None:
    c = load_config()["crossing"]
    jobs = [(v, ph) for v in c["variants"] for ph in range(0, 360, 360 // c["phases"])]
    with ProcessPoolExecutor(c["workers"]) as pool:
        out = list(pool.map(one, jobs))
    (ROOT / "out").mkdir(exist_ok=True)
    (ROOT / "out" / "crossing.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    for v in c["variants"]:
        rows = [r for r in out if r["variant"] == v]
        caught = [r["phase"] for r in rows if r["arrival"] is None]
        print(f"{v}: caught {len(caught)} of {len(rows)}; most beam power {max(r['beam_max_w'] for r in rows):.3g} W")
        for r in rows:
            a = r["arrival"]
            print(f"   start {r['phase']:3d} deg: " + (f"arrived year {a['year']}, eccentricity {a['eccentricity']}" if a
                                                    else f"CAUGHT (orbit stuck near {r['mars_a_max']:.3f} AU)"))
    print("Wrote out/crossing.json")


if __name__ == "__main__":
    main()
