"""Small asteroids at 2.7 AU (issue #30): how often rocks under 1 km would hit, how early an infrared survey sees
them, what E1 spends pushing each aside, what dust and rocks do to the mirrors and cables (and the debris that makes),
and what the belt does to Mars, its moons and our Moon.

    uv run python -m sim.scenarios.small_asteroids     # a second or two; writes results/small_asteroids.json

Post-processing only, no re-run: the journey tracked 1,000 real belt orbits and scaled their close passes to the
belt's asteroids over 1 km (`belt` in results/summary.json). Smaller rocks follow JWST's size distribution, a power
law with a break at about 100 m (config.yaml `small_asteroids`), so the rate of hits by rocks over D is the 1 km rate
times N(>D) / N(>1 km). Each number comes as low, central and high, every low end taken at once.
"""

import argparse
import json
import math

import numpy as np

from .. import night
from ..belt import R_EARTH, V_ESCAPE_EARTH
from ..config import ROOT, load_config
from ..constants import AU, C_LIGHT, DAY, G, GM_SUN, YEAR
from ..habitability import SOLAR_CONSTANT

CASES = ("low", "central", "high")
H, K_B, SIGMA = 6.62607015e-34, 1.380649e-23, 5.670374e-8
JANSKY = 1e-26                                  # W m^-2 Hz^-1
MEGATON = 4.184e15                              # J
L_SUN = SOLAR_CONSTANT * 4 * math.pi * AU ** 2  # W


def count_ratio(d_m: float, cfg: dict, k: int = 1) -> float:
    """N(>d) / N(>1 km) for case k (0 low, 1 central, 2 high): slope q_above above the break, q_below under it."""
    qa, qb, brk = cfg["slope_above_break"][k], cfg["slope_below_break"][k], cfg["break_m"]
    if d_m >= brk:
        return (d_m / 1000.0) ** -qa
    return (brk / 1000.0) ** -qa * (d_m / brk) ** -qb


def impact_rates(cfg: dict, belt: dict, run_population: float) -> dict:
    """Years per impact on Earth by rocks of each size and up, crossing the belt and parked at 2.7 AU, with no
    defence: the run's 1 km rate, rescaled for the belt's population and down the size distribution."""
    out = {}
    for phase, key in (("crossing", "crossing"), ("parked", "parked_at_target")):
        per_km = belt[key]["years_per_impact"]
        out[phase] = {"years": belt[key]["years"], "sample_encounters": belt[key]["sample_encounters"]}
        for d in cfg["sizes_m"]:
            years = [per_km * run_population / cfg["population_over_1km"][k] / count_ratio(d, cfg, k) for k in range(3)]
            out[phase][f"{d}m"] = {"years_per_impact": dict(zip(CASES, years)),   # keyed by rate: "low" = fewest hits
                                   "per_year": dict(zip(CASES, [1 / y for y in years]))}
    return out


def impact_energy(cfg: dict, v_enc: float) -> dict:
    """Mass and impact energy of each size at Earth: the encounter speed sharpened by Earth's pull."""
    v = math.hypot(v_enc, V_ESCAPE_EARTH)
    out = {"impact_speed_km_s": v / 1e3}
    for d in cfg["sizes_m"]:
        mass = [math.pi / 6 * d ** 3 * rho for rho in cfg["density_kg_m3"]]
        out[f"{d}m"] = {"mass_kg": dict(zip(CASES, mass)),
                        "energy_mt": dict(zip(CASES, [0.5 * m * v * v / MEGATON for m in mass]))}
    return out


def planck_nu(lam: float, temp: np.ndarray) -> np.ndarray:
    nu = C_LIGHT / lam
    return 2 * H * nu ** 3 / C_LIGHT ** 2 / np.expm1(H * nu / (K_B * temp))


def neatm_jy(d_m: float, delta_m: float, r_au: float, eta: float, cfg: dict, lam: float | None = None) -> float:
    """Thermal flux (Jy) of a rock of diameter d at distance delta, r_au from the Sun, by NEATM (Harris 1998): the
    day side at T_ss cos^(1/4) of the angle from the Sun, seen face on, then dimmed for phase."""
    lam = lam or cfg["survey_wavelength_um"] * 1e-6
    eps, bond = cfg["emissivity"], 0.39 * cfg["albedo"]
    t_ss = ((1 - bond) * SOLAR_CONSTANT / r_au ** 2 / (eta * eps * SIGMA)) ** 0.25
    n = 2000
    th = (np.arange(n) + 0.5) * (math.pi / 2) / n
    disc = np.sum(planck_nu(lam, t_ss * np.cos(th) ** 0.25) * 2 * math.pi * np.cos(th) * np.sin(th)) * (math.pi / 2) / n
    face_on = eps * (d_m / 2) ** 2 / delta_m ** 2 * disc / JANSKY
    return face_on * 10 ** (-0.4 * cfg["phase_mag_per_deg"] * cfg["phase_deg"])


def seen_from_m(d_m: float, eta: float, cfg: dict, r_au: float) -> float:
    """How far out the survey sees the rock: flux falls as 1/distance^2 down to the survey's limit."""
    return math.sqrt(neatm_jy(d_m, 1.0, r_au, eta, cfg) / cfg["survey_limit_jy"])


def e1_response(cfg: dict, full: dict, v_enc: float, r_au: float, beam_max_w: float) -> dict:
    """For each size: how far out it is seen, the warning, the push E1 gives it before it is within the beam
    clearance, and that push's share of E1 (spot as wide as the Earth tow's mirror)."""
    clear = full["beam"]["earth_clearance_km"] * 1e3
    off_sun = math.radians(max(abs(a) for a in full["beam"]["route_angles_deg"]))
    engage_beyond = clear / math.sin(off_sun)  # light up to 30 deg off the Sun line reaches any rock this far out
    capture = R_EARTH * math.sqrt(1 + (V_ESCAPE_EARTH / v_enc) ** 2)
    miss = cfg["miss_capture_radii"] * capture
    spot = 2 * full["structures"]["earth-tow"]["mirror_radius_km"] * 1e3
    e1 = full["beam"]["total_limit_w"]
    push = cfg["push_days"] * DAY
    out = {"capture_radius_km": capture / 1e3, "miss_km": miss / 1e3, "engage_beyond_km": engage_beyond / 1e3,
           "beam_spot_km": spot / 1e3, "e1_spare_w": e1 - beam_max_w}   # E1's headroom at the tows' busiest
    for d in cfg["sizes_m"]:
        mass = math.pi / 6 * d ** 3 * cfg["density_kg_m3"][1]
        rows = {}
        for case, eta in zip(("worst", "central", "best"), cfg["beaming_eta"]):
            seen = seen_from_m(d, eta, cfg, r_au)
            to_earth = seen / v_enc
            lead = to_earth - cfg["confirm_days"] * DAY - push / 2   # push's middle, before arrival
            dv = miss / lead
            absorbed = mass * dv / push * C_LIGHT                    # P/c of light it absorbs
            beam = absorbed * (spot / d) ** 2
            end_km = (seen - v_enc * (cfg["confirm_days"] * DAY + push)) / 1e3
            rows[case] = {"seen_km": seen / 1e3, "warning_days": to_earth / DAY, "push_ends_km": end_km,
                          "in_time": end_km * 1e3 >= engage_beyond, "speed_change_m_s": dv,
                          "absorbed_w": absorbed, "beam_w": beam, "share_of_e1": beam / e1,
                          "share_of_spare": beam / (e1 - beam_max_w),
                          "beam_seconds_of_e1": beam * push / e1}
        vap = [mass * j for j in cfg["vaporise_j_per_kg"]]    # absorbed; the beam is (spot / d)^2 times more
        rows["vaporise_j"] = dict(zip(CASES, vap))
        rows["vaporise_seconds_of_e1"] = dict(zip(CASES, [v * (spot / d) ** 2 / e1 for v in vap]))
        out[f"{d}m"] = rows
    return out


def grun_flux(m_g: np.ndarray) -> np.ndarray:
    """Grun et al. 1985 interplanetary meteoroid flux at 1 AU: grains over m grams per m^2 per second."""
    return ((2.2e3 * m_g ** 0.306 + 15.0) ** -4.38 + 1.3e-9 * (m_g + 1e11 * m_g ** 2 + 1e27 * m_g ** 4) ** -0.36
            + 1.3e-16 * (m_g + 1e6 * m_g ** 2) ** -0.85)


def dust_holes(cfg: dict) -> dict:
    """Per square metre of one face per year: area holed and grains hitting, 1e-18 to 100 g."""
    m = np.logspace(-18, 2, 4001)
    hits = -np.diff(grun_flux(m)) * YEAR
    mid = np.sqrt(m[1:] * m[:-1])
    size = (6 * mid * 1e-3 / (math.pi * cfg["grain_density_kg_m3"])) ** (1 / 3)
    hole = math.pi / 4 * (cfg["hole_over_grain"] * size) ** 2
    return {"area_fraction_per_year": float(np.sum(hits * hole)), "grains_per_m2_year": float(np.sum(hits)),
            "hits_per_m2_year": hits, "hole_side_m": cfg["hole_over_grain"] * size}


def rock_flux(belt: dict, run_population: float) -> dict:
    """Rocks over 1 km crossing each square metre per year (no gravity focusing on a mirror)."""
    x = belt["close_pass_au"] * AU
    scale = run_population / belt["sample_size"]
    return {phase: belt[key]["sample_encounters"] * scale / (math.pi * x * x) / belt[key]["years"]
            for phase, key in (("crossing", "crossing"), ("parked", "parked_at_target"))}


def wear(cfg: dict, full: dict, summary: dict, belt: dict, run_population: float) -> dict:
    """Dust and rocks on each surface: area holed per year (what E3 must replace), rocks of 1 m and 20 m and up per
    year, and the film knocked off as debris. Rocks come from every direction: a flat sheet in space meets them over
    half its area on average, one lying on the Moon over a quarter."""
    dust = dust_holes(cfg)
    flux_1km = rock_flux(belt, run_population)["crossing"]       # the busier of the two
    film = cfg["film_um"] * 1e-6 * full["enablers"]["e2_density_kg_m3"]   # kg/m^2
    sunlight = max(summary["climate"]["mirror_area_km2"]) if "climate" in summary else 0.0
    moon = night.area_for_full_moon_lux(full["night"], full["night"]["full_moon_lux_today"], full["arrival"]["target_au"])
    surfaces = {"sunlight mirrors": (sunlight, 2), "Moon reflectors": (moon, 1)}
    for tow in ("earth-tow", "mars-tow"):
        r = full["structures"][tow]["mirror_radius_km"]
        surfaces[f"{tow} mirror"] = (math.pi * r * r, 2)
    out = {"dust_area_fraction_per_face_year": dust["area_fraction_per_year"],
           "dust_grains_per_m2_year": dust["grains_per_m2_year"], "film_kg_m2": film}
    for name, (km2, faces) in surfaces.items():
        a = km2 * 1e6
        holed = dust["area_fraction_per_year"] * faces * a
        out[name] = {"area_km2": km2, "faces": faces, "holed_km2_per_year": holed / 1e6,
                     "holed_fraction_per_year": holed / a,
                     "rocks_1m_per_year": flux_1km * count_ratio(1.0, cfg) * a * faces / 4,
                     "rocks_20m_per_year": flux_1km * count_ratio(20.0, cfg) * a * faces / 4,
                     "film_debris_kg_per_year": holed * film if "mirror" in name else None}
    # Tow cables: one round bundle of the design cross-section, as long as the mirror's radius. Each grain digs a
    # hemispherical crater as wide as its hole; the share of the cable's volume dug out is also what a typical
    # cross-section loses.
    for tow in ("earth-tow", "mars-tow"):
        s = full["structures"][tow]
        cross = s["cable_cross_section_km2"] * 1e6
        width = math.sqrt(4 * cross / math.pi)
        side = width * s["mirror_radius_km"] * 1e3 * cfg["cable_length_over_mirror_radius"]
        dug = float(np.sum(dust["hits_per_m2_year"] * math.pi / 12 * dust["hole_side_m"] ** 3)) * width / cross
        out[f"{tow} cable"] = {"width_km": width / 1e3, "side_km2": side / 1e6, "volume_dug_per_year": dug,
                               "rocks_1m_per_year": flux_1km * count_ratio(1.0, cfg) * side,
                               "rocks_as_wide_per_year": flux_1km * count_ratio(width, cfg) * side}
    return out


def debris(cfg: dict, full: dict, worn: dict) -> dict:
    """Where the mirrors' debris goes: sunlight's push on a loose flake of film and on a vapour droplet, against the
    Sun's pull (beta). Above 0.5 a grain leaves the solar system."""
    per_area = L_SUN / (4 * math.pi * C_LIGHT * GM_SUN)          # kg/m^2: beta = (1 + R) per_area / sigma
    reflect = full["habitability"]["mirror_reflectivity"]
    rho = full["enablers"]["e2_density_kg_m3"]
    fleet = worn["sunlight mirrors"]["area_km2"] / full["night"]["sunlight_satellite_unit_km2"]
    return {"sunlight_satellites": fleet, "film_kg_per_year": worn["sunlight mirrors"]["film_debris_kg_per_year"],
            "flake_beta_face_on": (1 + reflect) * per_area / worn["film_kg_m2"],
            "droplet_escapes_below_um": 0.75 * per_area / (rho * 0.5) * 1e6}


def bodies(cfg: dict, full: dict, rates: dict, v_enc: float) -> dict:
    """Mars, Phobos, Deimos and the Moon against Earth: impact rates scaled by size and gravity focusing at the same
    encounter speed, and the rock it would take to break each one up."""
    b = cfg["bodies"]
    gm_earth = V_ESCAPE_EARTH ** 2 * R_EARTH / 2
    gm = {"earth": gm_earth, **{k: G * v["mass_kg"] for k, v in b.items()}}
    earth_focus = 1 + (V_ESCAPE_EARTH / v_enc) ** 2
    parked_1km = rates["parked"]["1000m"]["years_per_impact"]["central"]
    q = cfg["slope_above_break"][1]
    rho_rock = cfg["density_kg_m3"][1]
    out = {}
    for name, body in b.items():
        r = body["radius_km"] * 1e3
        v_esc = math.sqrt(2 * gm[name] / r)
        v_local, well = v_enc, 1.0
        if "around" in body:   # its parent's pull concentrates and speeds up the passing rocks
            v_parent = math.sqrt(2 * gm[body["around"]] / (body["orbit_km"] * 1e3))
            well, v_local = 1 + (v_parent / v_enc) ** 2, math.hypot(v_enc, v_parent)
        focus = 1 + (v_esc / v_local) ** 2
        share = (r / R_EARTH) ** 2 * well * focus / earth_focus
        v_hit = math.hypot(v_local, v_esc)
        mass = body["mass_kg"]
        if mass < 1e20:   # a small moon: Benz & Asphaug's threshold, in cgs
            ba = cfg["benz_asphaug"]
            density = mass / (4 / 3 * math.pi * r ** 3)
            r_cm = r * 100
            q_star = (ba["q0"] * r_cm ** ba["a"] + ba["b_coeff"] * density / 1e3 * r_cm ** ba["b"]) * 1e-4   # J/kg
        else:             # a big body: Stewart & Leinhardt's, combined radius at 1,000 kg/m^3
            r_c1 = (3 * mass / (4 * math.pi * 1000.0)) ** (1 / 3)
            q_star = cfg["leinhardt_c_star"] * 0.8 * math.pi * 1000.0 * G * r_c1 ** 2
        breaker = 2 * q_star * mass / v_hit ** 2           # a small rock's mass, all its energy counted
        breaker_d = (6 * breaker / (math.pi * rho_rock)) ** (1 / 3)
        binding = 3 * G * mass ** 2 / (5 * r)
        row = {"rate_vs_earth": share, "impact_speed_km_s": v_hit / 1e3,
               "years_per_20m": rates["parked"]["20m"]["years_per_impact"]["central"] / share,
               "years_per_1km": parked_1km / share,
               "disruption_j_per_kg": q_star, "breaker_kg": breaker, "breaker_over_belt_mass": breaker / cfg["belt_mass_kg"],
               "binding_over_belt_mass": 2 * binding / v_hit ** 2 / cfg["belt_mass_kg"]}
        if breaker_d < 1e6:
            row["breaker_km"] = breaker_d / 1e3
            row["years_per_breaker"] = parked_1km / share / (breaker_d / 1000.0) ** -q
        out[name] = row
    return out


def kirkwood(cfg: dict, full: dict, v_enc_esc: float = V_ESCAPE_EARTH) -> dict:
    """Earth on a circular orbit at r meets the belt at a rate set by the asteroids whose orbits reach r (Opik): each
    one's share of time within the band round r, over sin i (how long it lingers near the ecliptic), times its speed
    past Earth and Earth's gravity focusing. Against the count of orbits whose size falls in the same band."""
    rows = json.loads((ROOT / full["belt_sample"]["orbits_file"]).read_text(encoding="utf-8"))["data"]
    a, e, inc = (np.array([float(r[c]) for r in rows]) for c in (1, 2, 3))
    h = cfg["kirkwood_band_au"]
    v_unit = math.sqrt(GM_SUN / AU)

    def anomaly(radius):   # mean anomaly (0 to pi) at which each orbit is at `radius`, clipped to its own range
        ecc = np.maximum(e, 1e-9)
        big_e = np.arccos(np.clip((1 - radius / a) / ecc, -1, 1))
        return big_e - e * np.sin(big_e)

    def rate(r):
        share = (anomaly(r + h) - anomaly(r - h)) / math.pi
        speed2 = (2 / r - 1 / a) + 1 / r - 2 * np.sqrt(a * (1 - e * e)) / r * np.cos(np.radians(inc)) / math.sqrt(r)
        u = np.sqrt(np.maximum(speed2, 1e-12)) * v_unit
        focus = 1 + (v_enc_esc / u) ** 2
        return float(np.sum(share * u * focus / np.maximum(np.sin(np.radians(inc)), math.sin(math.radians(0.5))))) / r ** 2

    base, base_count = rate(2.7), np.sum(np.abs(a - 2.7) < h)
    return {"orbits": len(a), "band_au": h,
            **{f"{r:.2f}": {"encounters_vs_2.70": rate(r) / base, "orbit_sizes_vs_2.70": float(np.sum(np.abs(a - r) < h) / base_count)}
               for r in cfg["kirkwood_au"]}}


def run(cfg_all: dict | None = None, summary: dict | None = None) -> dict:
    full = cfg_all or load_config()
    cfg = full["small_asteroids"]
    summary = summary or json.loads((ROOT / "results" / "summary.json").read_text(encoding="utf-8"))
    belt = summary["belt"]
    v_enc = belt["encounter_speed_median_km_s"] * 1e3
    pop = full["belt_sample"]["real_population_over_1km"]
    r_au = full["arrival"]["target_au"]
    rates = impact_rates(cfg, belt, pop)
    worn = wear(cfg, full, summary, belt, pop)
    for k in list(worn):
        if isinstance(worn[k], dict):
            worn[k] = {kk: vv for kk, vv in worn[k].items() if vv is not None}
    return {"encounter_speed_km_s": v_enc / 1e3, "count_vs_1km": {f"{d}m": dict(zip(CASES, [count_ratio(d, cfg, k) for k in range(3)]))
                                                                for d in cfg["sizes_m"]},
            "impacts": rates, "energy": impact_energy(cfg, v_enc), "survey_and_e1": e1_response(cfg, full, v_enc, r_au, summary["total_beam_max_w"]),
            "wear": worn, "debris": debris(cfg, full, worn), "bodies": bodies(cfg, full, rates, v_enc),
            "kirkwood": kirkwood(cfg, full)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Small asteroids at 2.7 AU: impacts, survey, E1's answer, wear.")
    parser.add_argument("--out", default=str(ROOT / "results" / "small_asteroids.json"))
    args = parser.parse_args()
    r = run()
    print(f"Encounter speed {r['encounter_speed_km_s']:.2f} km/s; impact speed {r['energy']['impact_speed_km_s']:.2f} km/s")
    for phase in ("crossing", "parked"):
        for d, row in r["impacts"][phase].items():
            if isinstance(row, dict) and "years_per_impact" in row:
                y = row["years_per_impact"]
                print(f"{phase:8} >= {d:>5}: one hit per {y['central']:9.3g} years (fewest {y['low']:.3g}, most {y['high']:.3g})")
    for d in ("20m", "100m", "1000m"):
        en, s = r["energy"][d]["energy_mt"], r["survey_and_e1"][d]
        w = s["worst"]
        print(f"{d:>5}: {en['central']:.3g} Mt ({en['low']:.3g} to {en['high']:.3g}); seen {w['seen_km']:,.0f} km out "
              f"({w['warning_days']:.1f} days; best {s['best']['seen_km']:,.0f} km), push {w['speed_change_m_s']:.3g} m/s, "
              f"beam {w['beam_w']:.2e} W ({w['share_of_e1']:.1e} of E1) for a day, in time: {w['in_time']}")
    w = r["wear"]
    print(f"Dust holes {w['dust_area_fraction_per_face_year']:.2e} of each face a year")
    for name in ("sunlight mirrors", "earth-tow mirror", "mars-tow mirror", "Moon reflectors"):
        x = w[name]
        print(f"{name:17} {x['area_km2']:.3g} km2: {x['holed_km2_per_year']:.3g} km2 holed a year, "
              f"{x['rocks_1m_per_year']:.3g} rocks >= 1 m and {x['rocks_20m_per_year']:.3g} >= 20 m a year")
    for name in ("earth-tow cable", "mars-tow cable"):
        x = w[name]
        print(f"{name:17} {x['width_km']:.2f} km wide: {x['volume_dug_per_year']:.2e} of its volume dug out a year, "
              f"{x['rocks_1m_per_year']:.3g} rocks >= 1 m a year")
    d = r["debris"]
    print(f"Debris: {d['film_kg_per_year']:.3g} kg of film a year from {d['sunlight_satellites']:,.0f} satellites; "
          f"flake beta {d['flake_beta_face_on']:.2f}; droplets under {d['droplet_escapes_below_um']:.2f} um leave")
    for name, b in r["bodies"].items():
        extra = f", breaker {b['breaker_km']:.2f} km once per {b['years_per_breaker']:.2e} years" if "breaker_km" in b else ""
        print(f"{name:7} {b['rate_vs_earth']:.2e} of Earth's rate; >= 20 m once per {b['years_per_20m']:.3g} y; "
              f"break-up needs {b['breaker_over_belt_mass']:.2g} belt masses{extra}")
    for au, k in r["kirkwood"].items():
        if isinstance(k, dict):
            print(f"Kirkwood {au} AU: encounters {k['encounters_vs_2.70']:.2f} of 2.70 AU's; orbit sizes {k['orbit_sizes_vs_2.70']:.2f}")
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(r, fh, indent=1, default=float)
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
