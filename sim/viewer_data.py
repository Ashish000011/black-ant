"""Data for the 3D viewer, built from results/ so the page computes nothing and every number comes from the model.

    uv run python -m sim.viewer_data       # writes viewer/public/data/*.json

The viewer (viewer/) plays these files. Earth-safety values per frame are worked out here with the same
functions the journey uses (sim/habitability.py), replaying the sunlight-mirror build schedule on the saved frames.
"""

import json

import numpy as np

from .benchmarks import ALL as BENCHMARKS
from .bodies import state_from_elements
from .checks.structure import structure_checks
from . import habitability as hab, night
from .config import ROOT, load_config
from .constants import AU, C_LIGHT, G, GM_SUN, M_SUN, YEAR
from .habitability import (SOLAR_CONSTANT, Mirrors, absorbed_flux, day_length_rate, hill_share, jeans_lambda,
                           liquid_water_share, magnetopause_re, mean_temperature, thrust_over_moon_pull)

RESULTS = ROOT / "results"
OUT = ROOT / "viewer" / "public" / "data"


def load(name: str):
    return json.loads((RESULTS / name).read_text(encoding="utf-8"))


def orbit_line(p: dict, points: int = 180) -> list:
    """Points around a planet's J2000 orbit (AU), for drawing."""
    out = []
    for k in range(points + 1):
        q = dict(p, mean_longitude_deg=p["perihelion_longitude_deg"] + 360.0 * k / points)
        r, _ = state_from_elements(q, GM_SUN)
        out.append([round(float(c) / AU, 5) for c in r])
    return out


def journey(cfg: dict) -> dict:
    run = load("run.json")
    h = cfg["habitability"]
    tow = next(t for t in cfg["tows"] if t["name"] == "earth-tow")
    mirrors = Mirrors(h)
    t_prev, lod, year_prev = 288.0, 0.0, 0.0
    frames = []
    for f in run["frames"]:
        a, e = f["earth_orbit_au"], f["earth_eccentricity"]
        mirrors.update(f["t"], a, e)
        share = mirrors.sunlight_share(a, e)
        temp = mean_temperature(share * SOLAR_CONSTANT, t_prev)
        t_prev = temp
        active = f["earth_tow_active"]
        tow_m = float(np.linalg.norm(np.subtract(f["pos"]["asteroid"], f["pos"]["earth"]))) * AU
        if active:  # the same running sum as sim/checks/safety.py, at the frames' coarser spacing
            lod += day_length_rate(tow["asteroid_mass_kg"], tow_m) * (f["t"] - year_prev) * 3.15576e7
        year_prev = f["t"]
        frames.append({
            "t": f["t"], "pos": f["pos"], "earth_a": a, "earth_e": e, "mars_a": f["mars_orbit_au"],
            "beam_w": f["beam_power_w"], "tow_active": active, "tow_km": round(tow_m / 1e3) if active else None,
            "flags": f["flags"], "energy_error": f["energy_error"], "momentum_error": f["momentum_error"],
            "safety": {"temperature_k": round(temp, 3), "sunlight_share": round(share, 5),
                       "mirror_area_km2": round(mirrors.area_km2), "liquid_water_share": round(liquid_water_share(temp), 4),
                       "absorbed_w_m2": round(absorbed_flux(share * SOLAR_CONSTANT, temp), 2),
                       "surface_pressure_kpa": h["surface_pressure_kpa"],
                       "jeans_lambda_n2": round(jeans_lambda(share), 1),
                       "magnetopause_re": round(magnetopause_re(a, h["magnetopause_today_re"]), 3),
                       "day_length_change_s": lod,
                       "moon_hill_share": round(hill_share(a, h["earth_mass_with_moon_kg"]), 4),
                       "thrust_over_moon_pull": round(thrust_over_moon_pull(tow["asteroid_mass_kg"], tow_m), 5)
                       if active else 0.0}})
    planets = {p["name"]: orbit_line(p) for p in cfg["planets"]}
    belt = {"inner_au": cfg["belt_sample"]["a_au"][0], "outer_au": cfg["belt_sample"]["a_au"][1]}
    return {"frame_every_years": run["meta"]["frame_every_years"], "frames": frames, "orbits": planets, "belt": belt,
            "tows": [{k: t[k] for k in ("name", "target", "asteroid_mass_kg", "distance_km", "stop_au", "max_beam_w")}
                     for t in cfg["tows"]]}


def longterm() -> dict:
    lt = load("longterm.json")
    real = lt.get("baseline") or load("longterm_real_solar_system.json")["baseline"]

    def thin(run, every=10):
        s = run["series"]
        o = s["orbits"]
        idx = range(0, len(s["year"]), every)
        return {"year": [s["year"][i] for i in idx],
                "earth_a": [o["earth"]["a"][i] for i in idx], "earth_e": [o["earth"]["e"][i] for i in idx],
                "mars_a": [o["mars"]["a"][i] for i in idx], "mars_e": [o["mars"]["e"][i] for i in idx],
                "tilt_deg": [s["axial_tilt_deg"][i] for i in idx] if s.get("axial_tilt_deg") else []}

    chaos = load("longterm_chaos_copies.json")
    def info(run):
        return {k: run.get(k) for k in ("years", "energy_error", "earth_mars_orbit_gap_min_au", "axial_tilt_deg")}

    return {"moved": thin(lt["moved"]), "real": thin(real), "verdict": lt.get("verdict"),
            "moved_info": info(lt["moved"]), "real_info": info(real),
            "moved_ranges": lt["moved"]["ranges"], "real_ranges": real["ranges"],
            "encounters": lt["moved"]["encounters"], "thrown_out": lt["moved"]["thrown_out"],
            "chaos_copies": [{"seed": c["seed"], "verdict_flags": c["verdict"]["flags"]["unresolved"],
                              "earth_e_max": c["ranges"]["earth"]["e"][1], "gap_min_au": c["earth_mars_orbit_gap_min_au"],
                              "tilt_deg": c["axial_tilt_deg"]} for c in chaos["copies"]]}


def structures(cfg: dict, summary: dict) -> list:
    """Every structural check for each tow, at the most its beam used on the journey and at its power cap, with the
    beam pushing 2P/c (a perfect mirror, light straight back) and the asteroid at its closest to the target."""
    masses = {p["name"]: p["mass_kg"] for p in cfg["planets"]}
    out = []
    for t in cfg["tows"]:
        used = summary["tows"][t["name"]]["beam_max_w"]
        closest = min(summary["tows"][t["name"]]["target_distance_km"]) * 1e3
        for case, power in (("most used on the journey", used), ("power cap", t["max_beam_w"])):
            for r in structure_checks(cfg, t["name"], 2 * power / C_LIGHT, power, t["asteroid_mass_kg"], closest,
                                      masses[t["target"]]):
                out.append({"tow": t["name"], "case": case, "beam_w": power, **r})
    return out


def benchmarks() -> list:
    out = []
    for n, fn in BENCHMARKS.items():
        r = fn()
        out.append({"number": n, **{k: r[k] for k in ("name", "measured", "expected", "tolerance", "ok", "unit", "note")},
                    "doc": (fn.__doc__ or "").strip().splitlines()[0]})
    return out


def constants() -> dict:
    """The model's own constants, so the test bench's live estimates use exactly the numbers the Python model does."""
    return {"G": G, "c": C_LIGHT, "au_m": AU, "year_s": YEAR, "gm_sun": GM_SUN, "m_sun": M_SUN,
            "solar_constant": SOLAR_CONSTANT, "sigma": hab.SIGMA, "today_mean_k": hab.TODAY_MEAN_K,
            "warm_albedo": hab.WARM_ALBEDO, "ice_albedo": hab.ICE_ALBEDO, "warm_k": hab.WARM_K, "ice_k": hab.ICE_K,
            "emissivity": hab.EMISSIVITY, "latitude_t2_k": hab.LATITUDE_T2_K, "runaway_w_m2": hab.RUNAWAY_W_M2,
            "earth_radius_m": night.EARTH_RADIUS_M, "month_mean": night.MONTH_MEAN}


def main() -> None:
    cfg = load_config()
    OUT.mkdir(parents=True, exist_ok=True)
    s = load("summary.json")
    files = {
        "journey.json": journey(cfg),
        "summary.json": {k: s[k] for k in ("flags", "tows", "climate", "total_beam_max_w", "mars_closest",
                                           "big_asteroids_closest_au", "big_asteroid_nudges", "belt", "end", "ledger",
                                           "arrival_trim", "axial_tilt_journey_deg") if k in s},
        "longterm.json": longterm(),
        "benchmarks.json": benchmarks(),
        "crossing.json": load("crossing.json"),
        "outage.json": load("outage.json"),
        "parking.json": load("parking_scan3.json"),
        "structures.json": structures(cfg, s),
        "octo.json": load("octo_earth.json"),
        "config.json": {"safety": cfg["safety"], "enablers": cfg["enablers"], "structures": cfg["structures"],
                        "tows": cfg["tows"], "beam": cfg["beam"], "habitability": cfg["habitability"],
                        "night": cfg["night"], "moon": cfg["moon"], "arrival": cfg["arrival"],
                        "planets": cfg["planets"], "small_bodies": cfg["small_bodies"], "constants": constants()},
    }
    for name, data in files.items():
        (OUT / name).write_text(json.dumps(data, separators=(",", ":"), default=float), encoding="utf-8")
        print(f"wrote viewer/public/data/{name} ({(OUT / name).stat().st_size / 1e3:.0f} kB)")


if __name__ == "__main__":
    main()
