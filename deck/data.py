"""Collects every number and series the deck shows from results/ (and the climate model), into deck/data.json,
so no number on a slide is typed by hand (README, "How we work": numbers on slides come from results/).

    uv run python deck/data.py
"""

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sim import habitability as hab  # noqa: E402
from sim.benchmarks import ALL  # noqa: E402
from sim.config import load_config  # noqa: E402
from sim.viewer_data import structures  # noqa: E402

RESULTS = ROOT / "results"


def load(path: pathlib.Path):
    return json.loads(path.read_text(encoding="utf-8"))


def every(rows: list, n: int) -> list:
    """Every n-th row, always keeping the last."""
    out = rows[::n]
    return out if out[-1] is rows[-1] else out + [rows[-1]]


def climate_curve() -> list[dict]:
    """Global mean temperature against sunlight (share of today's), followed down from today's warm climate:
    the warm branch ends at the cliff, where ice runs away."""
    rows, t = [], hab.TODAY_MEAN_K
    for i in range(0, 61):
        share = 1.10 - i * 0.005
        t = hab.mean_temperature(share * hab.SOLAR_CONSTANT, start_k=t)
        rows.append({"share": round(share, 3), "k": round(t, 2)})
    return rows


def main() -> None:
    cfg, s = load_config(), load(RESULTS / "summary.json")
    run = load(ROOT / "viewer" / "public" / "data" / "journey.json")
    frames = run["frames"]
    longterm = load(ROOT / "viewer" / "public" / "data" / "longterm.json")
    mirrors, small = load(RESULTS / "mirrors.json"), load(RESULTS / "small_asteroids.json")
    octo, outage, crossing = load(RESULTS / "octo_earth.json"), load(RESULTS / "outage.json"), load(RESULTS / "crossing.json")
    moon_path = ROOT / "out" / "moon_runs_x1.json"
    moon = load(moon_path) if moon_path.exists() else None
    verify_path = ROOT / "out" / "verify" / "verification.json"
    verify = load(verify_path) if verify_path.exists() else None

    # The same climate model without the sunlight optics, followed along the journey from today's 288 K.
    bare, t_k = {}, hab.TODAY_MEAN_K
    for f in frames:
        t_k = hab.mean_temperature(hab.sunlight(f["earth_a"]), start_k=t_k)
        bare[f["t"]] = round(t_k, 2)
    journey = [{"t": f["t"], "earth_a": f["earth_a"], "mars_a": f["mars_a"], "beam_w": f["beam_w"], "tow_km": f["tow_km"],
                "temperature_no_optics_k": bare[f["t"]],
                **{k: f["safety"][k] for k in ("temperature_k", "sunlight_share", "mirror_area_km2", "liquid_water_share",
                                               "magnetopause_re", "moon_hill_share", "absorbed_w_m2")}}
               for f in every(frames, 5)]
    first = lambda test: next((f["t"] for f in frames if test(f)), None)
    milestones = {"earth_2au": first(lambda f: f["earth_a"] >= 2.0), "mars_sprint_from": first(lambda f: f["mars_a"] >= 3.0),
                  "mars_sprint_to": first(lambda f: f["mars_a"] >= 3.5), "optics_from": first(lambda f: f["safety"]["mirror_area_km2"] > 0),
                  "earth_freezes_without_optics": next((t for t, k in bare.items() if k < 263), None),
                  "day_length_max_s": max(f["safety"]["day_length_change_s"] for f in frames),
                  "checks": round(frames[-1]["t"] * 365.25 / (cfg["run"]["check_every_steps"] * cfg["run"]["dt_days"]))}
    lt = longterm["moved"]
    long_series = [{"year": lt["year"][i], "earth_a": lt["earth_a"][i], "earth_e": lt["earth_e"][i], "tilt": lt["tilt_deg"][i],
                    "real_tilt": longterm["real"]["tilt_deg"][i], "real_e": longterm["real"]["earth_e"][i]}
                   for i in range(0, len(lt["year"]), 10)]
    bench = [{"n": n, **{k: v for k, v in fn().items() if k in ("name", "ok", "unit", "measured", "expected", "tolerance")}} for n, fn in ALL.items()]
    cap = [c for c in structures(cfg, s) if c["case"] == "power cap"]
    tow_cfg = {t["name"]: t for t in cfg["tows"]}

    data = {
        "config": {"safety": cfg["safety"], "target_au": cfg["arrival"]["target_au"], "years": s["settings"]["years"],
                   "tows": tow_cfg, "enablers": cfg.get("enablers")},
        "summary": {k: s[k] for k in ("tows", "arrival_trim", "axial_tilt_journey_deg", "climate", "total_beam_max_w",
                                      "station_recoil_max_n", "mars_closest", "jupiter_closest_au", "big_asteroids_closest_au",
                                      "big_asteroid_nudges", "belt", "end", "ledger", "flags")},
        "journey": journey,
        "milestones": milestones,
        "orbits_au": {k: round(sum(sum(c * c for c in p) ** 0.5 for p in v) / len(v), 4) for k, v in run["orbits"].items()},
        "belt_au": [run["belt"]["inner_au"], run["belt"]["outer_au"]],
        "longterm": {"series": long_series, "moved": longterm["moved_ranges"], "real": longterm["real_ranges"],
                     "verdict": longterm["verdict"], "moved_info": longterm["moved_info"], "real_info": longterm["real_info"],
                     "chaos_copies": longterm["chaos_copies"], "thrown_out": longterm["thrown_out"]},
        "climate_curve": climate_curve(),
        "cliff": mirrors["refractor_l1"]["climate_cliff_sunlight"],
        "mirrors": {k: mirrors[k] for k in ("face_on_area_km2", "e3_limit_km2", "sun_deg", "hill_radius_km", "tow_mirror",
                                            "satellites", "refractor_l1", "tow_protection", "light_ring", "sky")},
        "small": {k: small[k] for k in ("count_vs_1km", "impacts", "survey_and_e1", "wear", "bodies", "kirkwood", "energy")},
        "octo": {"arm": octo["arm"], "curl": octo["curl"], "all": octo["net_force_all_arms"], "one": octo["net_force_one_arm"],
                 "outside": octo["outside_field"], "materials": [{k: m[k] for k in ("name", "strength_pa", "density",
                 "curled_longest_km", "standing_longest_km", "buckling_length_km")} for m in octo["materials"]]},
        "outage": [{k: o[k] for k in ("name", "longest_safe_outage_days") if k in o} for o in outage],
        "crossing": crossing["variants"],
        "benchmarks": bench,
        "structures_cap": cap,
        "moon": moon["epochs"] if moon else None,
        "verify": verify,
    }
    out = ROOT / "deck" / "data.json"
    out.write_text(json.dumps(data, indent=1, default=float), encoding="utf-8")
    print(f"Wrote {out.relative_to(ROOT)}: {len(journey)} journey frames, {len(long_series)} million-year points")


if __name__ == "__main__":
    main()
