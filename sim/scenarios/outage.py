"""Beam outage: the Earth tow's asteroid only stays put because its beam holds it against Earth's pull.
If the beam stops, the asteroid starts falling toward Earth. As it falls, Earth's pull grows, and
once that pull is more than the beam's spare power can answer, the asteroid is lost and falls
through the Moon's orbit. Rough rule: longest safe outage = spare power share x sqrt(distance / pull),
about 9 days x the spare share for our tow.

For each design in config.yaml (asteroid mass, power cap, share of power left during the outage)
this searches for the longest outage after which the asteroid is still held: outside the Moon's
orbit, with an allowed beam. Flags raised while recovering (structures, drift off the spot) are listed
separately: they show what must be sized for recovery, not a lost asteroid. Mars's tow runs alongside,
so the Earth tow has only what is left of E1's budget: the tightest phase of the journey.

Run from the project root:
    uv run python -m sim.scenarios.outage                     # search every design in config.yaml
    uv run python -m sim.scenarios.outage --days 0.1 0.25     # just these outages, current design
"""

import argparse
import copy
import json
from concurrent.futures import ProcessPoolExecutor

from ..config import ROOT, load_config
from .tow import run


def trial(cfg: dict, days: float, power_left: float = 0.0, tow: str = "earth-tow") -> dict:
    o = cfg["outage"]
    s, _, _ = run(cfg, years=o["start_year"] + o["watch_years"], dt_days=o["dt_days"], mars_tow=True,
                  belt=False, outage=(o["start_year"], days, power_left, tow))
    t = s["tows"][tow]
    closest = t["target_distance_km"][0]
    flags = [f["check"] for f in s["flags"]["flags"] if f["covered_by"] is None and not f["check"].startswith("Earth reaches")]
    # Earth's tow must stay beyond the Moon's orbit; Mars's must not fall onto Mars (radius 3,390 km)
    floor = cfg["beam"]["earth_clearance_km"] if tow == "earth-tow" else cfg["outage"]["mars_floor_km"]
    held = closest >= floor and not any("no allowed beam" in f for f in flags)
    return {"days": days, "closest_km": round(closest), "beam_max_w": t["beam_max_w"],
            "mars_beam_max_w": s["tows"]["mars-tow"]["beam_max_w"],
            "days_power_capped": t["days_power_capped"], "unresolved_flags": flags, "safe": held,
            "clean": held and not flags}


def design_cfg(design: dict) -> dict:
    cfg = load_config()
    cfg["run"]["check_every_steps"] = 1  # watch every step: an outage plays out over days
    tow = next(t for t in cfg["tows"] if t["name"] == "earth-tow")
    tow["asteroid_mass_kg"] = design.get("earth_mass_kg", tow["asteroid_mass_kg"])
    tow["max_beam_w"] = design.get("earth_max_beam_w", tow["max_beam_w"])
    return cfg


def longest_safe(design: dict) -> dict:
    """Bisect for the longest safe outage, to outage.resolution_days."""
    cfg = design_cfg(design)
    o = cfg["outage"]
    left = design.get("power_left", 0.0)
    which = design.get("tow", "earth-tow")
    steady = trial(cfg, 0.0, 0.0, which)
    lo, hi = 0.0, o["search_max_days"]
    tried = [steady]
    top = trial(cfg, hi, left, which)
    tried.append(top)
    if top["safe"]:
        lo = hi
    while hi - lo > o["resolution_days"] and not top["safe"]:
        mid = round((lo + hi) / 2, 3)
        r = trial(cfg, mid, left, which)
        tried.append(r)
        lo, hi = (mid, hi) if r["safe"] else (lo, mid)
    tow = next(t for t in cfg["tows"] if t["name"] == which)
    if which == "earth-tow":
        spare = min(tow["max_beam_w"], cfg["beam"]["total_limit_w"] - steady["mars_beam_max_w"]) / steady["beam_max_w"] - 1
    else:
        spare = tow["max_beam_w"] / steady["beam_max_w"] - 1
    clean = [r["days"] for r in tried if r["clean"]]
    return {**design, "asteroid_mass_kg": tow["asteroid_mass_kg"], "max_beam_w": tow["max_beam_w"],
            "steady_beam_w": steady["beam_max_w"], "spare_share": spare,
            "longest_safe_outage_days": lo, "first_unsafe_days": None if top["safe"] else hi,
            "longest_clean_outage_days": max(clean) if clean else 0.0,
            "trials": sorted(tried, key=lambda r: r["days"])}


def main() -> None:
    parser = argparse.ArgumentParser(description="Test Earth tow beam outages.")
    parser.add_argument("--days", type=float, nargs="+", help="just run these outage lengths on the current design")
    args = parser.parse_args()
    if args.days:
        cfg = design_cfg({})
        for days in args.days:
            r = trial(cfg, days, 0.0)
            print(f"beam off {days:5.2f} days: closest {r['closest_km']:>9,} km, {'safe' if r['safe'] else 'LOST'}; "
                  f"flags: {r['unresolved_flags'] or 'none'}", flush=True)
        return
    designs = copy.deepcopy(load_config()["outage"]["designs"])
    with ProcessPoolExecutor(max_workers=len(designs)) as pool:
        results = list(pool.map(longest_safe, designs))
    (ROOT / "out" / "outage.json").write_text(json.dumps(results, indent=1), encoding="utf-8")
    print(f"{'design':44s} {'asteroid kg':>11} {'cap W':>8} {'steady W':>9} {'spare':>6} | held through | lost at | no flags through")
    for r in results:
        lost = "-" if r["first_unsafe_days"] is None else f"{r['first_unsafe_days']:.2f} d"
        print(f"{r['name']:44s} {r['asteroid_mass_kg']:11.3g} {r['max_beam_w']:8.2g} {r['steady_beam_w']:9.3g} "
              f"{r['spare_share']:6.1%} | {r['longest_safe_outage_days']:9.2f} d | {lost:>7} | {r['longest_clean_outage_days']:.2f} d")
    print("Wrote out/outage.json")


if __name__ == "__main__":
    main()
