"""Where the sunlight mirrors sit (issue #32): the area they really need, how much of their light reaches the night
side, what Earth sees of them and of the tow mirror, and what happens to our satellites.

    uv run python -m sim.scenarios.mirrors     # a second; writes results/mirrors.json

The run's climate (`habitability.Mirrors`) counts every square metre of sunlight mirror as catching sunlight face on
and sending all of it to Earth. That is only true for a mirror right behind Earth, whose light then lands on the
night side (and which sits in Earth's shadow). A mirror at angle phi from the Sun, seen from Earth, catches sunlight
at an incidence whose cosine is sin(phi / 2); if its light covers Earth's disc, a share (1 - cos phi) / 2 of it lands
on the night side. A mirror near enough can instead aim its spot (the Sun's apparent size times its distance) at the
daylit ground it sees. The design (#39) is a ring of refracting film near the Sun-Earth L1 point instead, which bends
sunlight onto Earth from the Sun's own direction; the sunlight-held ring at 120 degrees is the fallback. Also here: how
the tow mirrors are protected from rocks (from `results/small_asteroids.json`). Post-processing only: the area comes
from the run (`results/summary.json`).
"""

import argparse
import json
import math

import numpy as np

from .. import night
from ..config import ROOT, load_config
from ..constants import AU, C_LIGHT, GM_SUN, YEAR
from ..habitability import SIGMA, SOLAR_CONSTANT, liquid_water_share, mean_temperature

GM_EARTH = 3.986004418e14
R_EARTH = 6.371e6
H, K_B = 6.62607015e-34, 1.380649e-23


def incidence(phi: float) -> float:
    """Cosine of the angle at which sunlight meets a mirror that sends it to Earth from phi (rad) off the Sun."""
    return math.sin(phi / 2)


def night_share(phi: float) -> float:
    """Share of a mirror's light that lands on Earth's night side when it covers Earth's whole disc."""
    return (1 - math.cos(phi)) / 2


def light_push(cfg: dict, full: dict, film_um: float, phi: float, r_au: float) -> float:
    """Sunlight's push on a mirror per kg (m/s^2) while it sends light to Earth from phi: (1 + R) S cos^2(i) / (c sigma)."""
    sigma = film_um * 1e-6 * full["enablers"]["e2_density_kg_m3"]
    reflect = full["habitability"]["mirror_reflectivity"]
    return (1 + reflect) * SOLAR_CONSTANT / r_au ** 2 * incidence(phi) ** 2 / (C_LIGHT * sigma)


def hover(cfg: dict, full: dict, film_um: float, phi: float, r_au: float) -> dict:
    """A mirror held at phi > 90 deg by sunlight. Along the Sun line, the push (a_L sin(phi/2) away from the Sun)
    balances Earth's pull (-g cos phi): that sets its distance. Across it, what is left of Earth's pull keeps it
    circling the Sun-Earth line (it must point inward)."""
    a_l = light_push(cfg, full, film_um, phi, r_au)
    g = a_l * math.sin(phi / 2) / -math.cos(phi)
    d = math.sqrt(GM_EARTH / g)
    inward = g * math.sin(phi) - a_l * math.cos(phi / 2)
    n_sun = 2 * math.pi / (r_au ** 1.5 * YEAR)
    return {"distance_km": d / 1e3, "light_m_s2": a_l, "earth_pull_m_s2": g, "inward_m_s2": inward,
            "circling_days": 2 * math.pi / math.sqrt(inward / (d * math.sin(phi))) / 86400,
            "solar_tide_over_pull": 3 * n_sun ** 2 * d / g}


def ring_points(phi: float, d: float, n: int = 3600) -> np.ndarray:
    """A ring of mirrors at phi from the Sun, distance d (m). Frame: x toward the Sun, y ahead along the orbit, z up."""
    u = np.linspace(0, 2 * math.pi, n, endpoint=False)
    return np.stack((np.full(n, d * math.cos(phi)), d * math.sin(phi) * np.cos(u), d * math.sin(phi) * np.sin(u)), axis=1)


def ray_gap(points: np.ndarray, start: np.ndarray, direction: np.ndarray) -> float:
    """Closest distance (m) from any of `points` to the half-line from `start` along `direction` (unit)."""
    rel = points - start
    along = np.clip(rel @ direction, 0.0, None)
    return float(np.min(np.linalg.norm(rel - along[:, None] * direction, axis=1)))


def beam_rays(cfg: dict, full: dict) -> list[tuple[np.ndarray, np.ndarray, np.ndarray]]:
    """The Earth tow's beam: light arriving up to the route angles off the Sun line (in the orbit plane and across
    it), reflected by the tow mirror whose face points along the asteroid's bearing (its push holds the asteroid
    off Earth). Only routes whose light keeps the clearance from Earth are kept, as in the run."""
    bearing = math.radians(cfg["tow_bearing_deg"])
    dist = full["tows"][0]["distance_km"] * 1e3
    normal = np.array([math.cos(bearing), math.sin(bearing), 0.0])
    tow = dist * normal
    clear = full["beam"]["earth_clearance_km"] * 1e3
    rays = []
    for a in full["beam"]["route_angles_deg"]:
        t = math.radians(a)
        for come in (np.array([-math.cos(t), -math.sin(t), 0.0]), np.array([-math.cos(t), 0.0, -math.sin(t)])):
            out = come - 2 * np.dot(come, normal) * normal
            back_in = ray_gap(np.zeros((1, 3)), tow, -come)   # the incoming light, traced back from the mirror
            leave = ray_gap(np.zeros((1, 3)), tow, out)
            if min(back_in, leave) >= clear:
                rays.append((tow, -come, out))
    return rays


def clearances(cfg: dict, full: dict, phi: float, d: float, rays) -> dict:
    """How far a ring at (phi, d) stays from the beam (minus the tow mirror's radius), the tow asteroid and the
    Moon's and the satellites' orbits."""
    pts = ring_points(phi, d)
    mirror_r = full["structures"]["earth-tow"]["mirror_radius_km"] * 1e3
    beam = min(min(ray_gap(pts, s, back), ray_gap(pts, s, out)) for s, back, out in rays) - mirror_r
    tow = rays[0][0]
    return {"beam_gap_km": beam / 1e3, "tow_gap_km": (float(np.min(np.linalg.norm(pts - tow, axis=1))) - mirror_r) / 1e3,
            "above_geostationary_km": d / 1e3 - cfg["geostationary_km"],
            "from_moon_orbit_km": min(abs(d / 1e3 - cfg["moon_perigee_km"]), abs(d / 1e3 - cfg["moon_apogee_km"]))
            if not cfg["moon_perigee_km"] <= d / 1e3 <= cfg["moon_apogee_km"] else 0.0,
            "clear": bool(beam > 0 and not cfg["moon_perigee_km"] <= d / 1e3 <= cfg["moon_apogee_km"]
                          and d / 1e3 > cfg["geostationary_km"])}


def planck_lux_per_w(t_k: float, lo_um: float, hi_um: float, n: int = 4000) -> float:
    """Lux per W/m^2 of a blackbody at temperature t: 683 lm/W times the eye's sensitivity (a Gaussian fit to the
    CIE photopic curve, 1.019 exp(-285.4 (lambda - 0.559)^2), lambda in um), over the visible range."""
    lam = np.linspace(lo_um, hi_um, n) * 1e-6
    b = 2 * H * C_LIGHT ** 2 / lam ** 5 / np.expm1(H * C_LIGHT / (lam * K_B * t_k))
    eye = 1.019 * np.exp(-285.4 * (lam * 1e6 - 0.559) ** 2)
    return 683.0 * float(np.sum(b * eye) * (lam[1] - lam[0]) * math.pi / (SIGMA * t_k ** 4))


def climate_cliff(lo: float = 0.5, hi: float = 1.0) -> float:
    """Lowest share of today's sunlight at which the climate model stays on its warm branch (below it, ice wins)."""
    for _ in range(50):
        mid = (lo + hi) / 2
        lo, hi = (lo, mid) if mean_temperature(mid * SOLAR_CONSTANT) > 270.0 else (mid, hi)
    return hi


def balance_distance(beta: float, r_au: float) -> float:
    """Distance (m) from Earth toward the Sun where a sheet pushed by sunlight (beta: the push over the Sun's pull)
    holds still in Hill's approximation: the Sun's tide 3 n^2 x equals Earth's pull plus the push. beta = 0 is L1."""
    gm_sun_a2 = GM_SUN / (r_au * AU) ** 2
    n2 = GM_SUN / (r_au * AU) ** 3
    lo, hi = (GM_EARTH / (3 * n2)) ** (1 / 3), 20 * (GM_EARTH / (3 * n2)) ** (1 / 3)
    for _ in range(200):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if 3 * n2 * mid - GM_EARTH / mid ** 2 - beta * gm_sun_a2 < 0 else (lo, mid)
    return lo


def landing_share(image_radius: float) -> float:
    """Share of a Sun's image (radius m) centred on Earth that Earth's disc catches."""
    return min(1.0, (R_EARTH / image_radius) ** 2)


def refractor(cfg: dict, full: dict, need: float, sun: float, rays, r_au: float) -> dict:
    """Option D for each transmission T: where the ring balances, how much light lands, the area that gives today's
    sunlight against E3, Earth's sunlight and climate when held to E3's area, the ring's size and look, how it is
    kept in place, and how far the tow beams pass from it."""
    rf = cfg["refractor"]
    sigma = rf["areal_density_g_m2"] / 1e3
    limit = full["enablers"]["e3_mirror_area_limit_km2"]
    disc = math.pi * (R_EARTH / 1e3) ** 2
    per_area = SOLAR_CONSTANT * AU ** 2 / (C_LIGHT * GM_SUN)     # kg/m^2: L / (4 pi c GM_sun)
    n = math.sqrt(GM_SUN / (r_au * AU) ** 3)
    unstable = n * math.sqrt(1 + 2 * math.sqrt(7))                      # growth rate at a collinear point (Hill)
    steer = rf["control_reflectivity"] * 2 * SOLAR_CONSTANT / r_au ** 2 / (C_LIGHT * sigma)
    need_steer = unstable ** 2 * rf["hold_km"] * 1e3
    l1 = balance_distance(0.0, r_au)
    mirror_r = full["structures"]["earth-tow"]["mirror_radius_km"] * 1e3
    out = {"l1_km": l1 / 1e3, "areal_density_g_m2": rf["areal_density_g_m2"], "mass_kg": limit * 1e6 * sigma,
           "unstable_efold_days": 1 / unstable / 86400, "steering_needed_m_s2": need_steer, "steering_available_m_s2": steer,
           "climate_cliff_sunlight": climate_cliff(), "by_transmission": {}}
    for t in rf["transmission"]:
        beta = (1 - t) * 2 * per_area / sigma
        d = balance_distance(beta, r_au)
        image = d * sun / 2
        land = landing_share(image)
        area = need * disc / (t * land)
        share = (1 + min(1.0, limit / area) * need) / (1 + need)
        temp = mean_temperature(share * SOLAR_CONSTANT)
        r_in = R_EARTH + image                                   # inside this, light partly reaches Earth anyway
        r_out = math.sqrt(min(area, limit) * 1e6 / math.pi + r_in ** 2)
        gap = math.inf
        for start, back, _ in rays:                              # incoming light, traced back toward the Sun
            if back[0] <= 0:
                continue
            p = start + (d - start[0]) / back[0] * back
            r = math.hypot(p[1], p[2])
            gap = min(gap, r_in - mirror_r - r if r < r_in else r - r_out - mirror_r if r > r_out else -1.0)
        out["by_transmission"][f"{t:.2f}"] = {
            "beta": beta, "distance_km": d / 1e3, "past_l1": d / l1 - 1, "image_km": 2 * image / 1e3, "lands": land,
            "area_km2": area, "area_vs_e3": area / limit, "sunlight_vs_today_at_e3": share, "temperature_k": temp,
            "liquid_water": liquid_water_share(temp), "warm": share > out["climate_cliff_sunlight"],
            "ring_km": [r_in / 1e3, r_out / 1e3], "bend_deg": math.degrees(r_out / d),
            "halo_deg": [math.degrees(r_in / d), math.degrees(r_out / d)], "beam_gap_km": gap / 1e3}
    return out


def tow_protection(cfg: dict, full: dict, summary: dict) -> dict:
    """Rocks and dust on each tow mirror and its cables, over its years in the belt (Earth's: the years the run measured
    the belt's rate over; Mars's: from its orbit passing belt_inner_au) and, as an upper bound, the belt's rate over the
    whole tow, and the layers that protect it: its own beam, the survey and E1, patching, spare power,
    the cables' margin and the outage study."""
    from .small_asteroids import count_ratio
    small = json.loads((ROOT / "results" / "small_asteroids.json").read_text(encoding="utf-8"))
    frames = json.loads((ROOT / "results" / "run.json").read_text(encoding="utf-8"))["frames"]
    outage = {c["name"]: c["longest_safe_outage_days"] for c in json.loads((ROOT / "results" / "outage.json").read_text(encoding="utf-8"))}
    sa = full["small_asteroids"]
    v = small["encounter_speed_km_s"] * 1e3
    rho = sa["density_kg_m3"][1]
    out = {}
    for tow_cfg in full["tows"]:
        name, planet = tow_cfg["name"], tow_cfg["target"]
        arrive = summary["tows"][name]["arrival"]["year"]
        if planet == "earth":   # the years over which the run measured the belt's rate
            belt = summary["belt"]["crossing"]["years"]
        else:
            belt = arrive - next(f["t"] for f in frames if f["mars_orbit_au"] >= cfg["belt_inner_au"])
        years = {"belt": belt, "whole_tow": arrive}
        mirror, cable = small["wear"][f"{name} mirror"], small["wear"][f"{name} cable"]
        rocks = {f"{d}m": {"per_year": mirror["rocks_1m_per_year"] * count_ratio(d, sa) / count_ratio(1.0, sa)} for d in cfg["tow_rock_sizes_m"]}
        for r in rocks.values():
            r.update({f"over_{k}": r["per_year"] * y for k, y in years.items()})
        r_m = full["structures"][name]["mirror_radius_km"] * 1e3
        intensity = tow_cfg["max_beam_w"] / (math.pi * r_m ** 2)
        one_m = math.pi / 6 * rho
        cable_10 = cable["rocks_1m_per_year"] * count_ratio(10.0, sa) / count_ratio(1.0, sa)
        cap = tow_cfg["max_beam_w"]
        cable_sf = full["enablers"]["e2_strength_pa"] * full["structures"][name]["cable_cross_section_km2"] * 1e6 / (2 * cap / C_LIGHT)
        peak = summary["total_beam_max_w"] if planet == "earth" else summary["tows"][name]["beam_max_w"]
        limit = full["beam"]["total_limit_w"] if planet == "earth" else cap
        prefix = "shared E1 budget" if planet == "earth" else "Mars tow"
        out[name] = {"years": years, "rocks": rocks, "dust_holed_per_year": mirror["holed_fraction_per_year"],
                     "dust_unrepaired": {k: mirror["holed_fraction_per_year"] * y for k, y in years.items()},
                     "patch_km2_per_year": mirror["holed_km2_per_year"],
                     "cable_rocks_10m": {k: cable_10 * y for k, y in years.items()},
                     "rock_10m_kt": 0.5 * math.pi / 6 * 1000 * rho * v * v / 4.184e12,
                     "beam_w_m2": intensity, "beam_vs_sun_surface": intensity / (SIGMA * cfg["sun_surface_k"] ** 4),
                     "vaporise_1m_s": [one_m * j / (intensity * math.pi * 0.25) for j in sa["vaporise_j_per_kg"]],
                     "spare_power": 1 - peak / limit, "cable_sf_at_cap": cable_sf, "cable_loss_allowed": 1 - full["safety"]["structural_safety_factor_min"] / cable_sf,
                     "outage_all_off_days": outage[f"{prefix}, all beams off"],
                     "outage_half_off_days": outage[f"{prefix}, half the stations off"]}
    out["survey_warning_days"] = {d: small["survey_and_e1"][d]["worst"]["warning_days"] for d in ("20m", "100m")}
    return out


def run(full: dict | None = None, summary: dict | None = None) -> dict:
    full = full or load_config()
    cfg = full["mirrors"]
    summary = summary or json.loads((ROOT / "results" / "summary.json").read_text(encoding="utf-8"))
    r_au = full["arrival"]["target_au"]
    reflect = full["habitability"]["mirror_reflectivity"]
    limit = full["enablers"]["e3_mirror_area_limit_km2"]
    disc = math.pi * (R_EARTH / 1e3) ** 2
    face_on = max(summary["climate"]["mirror_area_km2"])          # the run's area, counted face on
    extra = reflect * face_on / disc                              # mirror light in Earth-discs of direct sunlight
    sun = math.radians(full["night"]["sun_diameter_1au_deg"] / r_au)
    rays = beam_rays(cfg, full)

    scan = []
    for deg in cfg["phi_scan_deg"]:
        p = math.radians(deg)
        scan.append({"phi_deg": deg, "incidence": incidence(p), "night_share_if_flooding": night_share(p),
                     "area_km2": face_on / incidence(p), "area_day_side_flooding_km2": face_on / (incidence(p) * (1 - night_share(p)))
                     if night_share(p) < 1 else math.inf, "daylit_strip_km": R_EARTH / 1e3 * (math.pi - p)})

    # The simple ring: an orbit in the plane facing the Sun.
    sr = cfg["simple_ring"]
    p, d = math.radians(sr["phi_deg"]), sr["distance_km"] * 1e3
    v = math.sqrt(GM_EARTH / d)
    turn = 2 * math.pi / (r_au ** 1.5 * YEAR)                   # the Sun line turns once per Earth year at 2.7 AU
    capped = (1 + reflect * limit * incidence(p) / disc) / (1 + extra)   # today's sunlight with only E3's area
    t_capped = mean_temperature(capped * SOLAR_CONSTANT)
    simple = {"phi_deg": sr["phi_deg"], "distance_km": sr["distance_km"], "area_km2": face_on / incidence(p),
              "over_e3": face_on / incidence(p) / limit - 1, "spot_km": d * sun / 1e3,
              "spot_fill": d * sun / (R_EARTH * (math.pi - p)), "orbit_days": 2 * math.pi * d / v / 86400,
              "turning_m_s2": math.pi / 2 * turn * v,
              "sail_m_s2": {f"{f}um": light_push(cfg, full, f, math.pi, r_au) for f in cfg["film_um"]},
              "night_share": 0.0, "in_earth_shadow": False,
              "capped_at_e3": {"sunlight_vs_today": capped, "temperature_k": t_capped, "liquid_water": liquid_water_share(t_capped)},
              **clearances(cfg, full, p, d, rays)}
    simple["aimed"] = simple["spot_fill"] <= cfg["spot_fill_max"]

    # The light-held ring at 120 deg, for each film.
    lr = cfg["light_ring"]
    p = math.radians(lr["phi_deg"])
    light = {"phi_deg": lr["phi_deg"], "area_km2": face_on / incidence(p), "e3_margin": 1 - face_on / incidence(p) / limit,
             "daylit_strip_km": R_EARTH / 1e3 * (math.pi - p), "films": {}}
    for f in cfg["film_um"]:
        h = hover(cfg, full, f, p, r_au)
        dd = h["distance_km"] * 1e3
        row = {**h, "spot_km": dd * sun / 1e3, "spot_fill": dd * sun / (R_EARTH * (math.pi - p)), **clearances(cfg, full, p, dd, rays)}
        row["aimed"] = row["spot_fill"] <= cfg["spot_fill_max"]
        row["works"] = bool(row["aimed"] and row["clear"] and row["inward_m_s2"] > 0)
        light["films"][f"{f}um"] = row

    # What Earth sees. Mirrors lighting a site shine at R times the Sun's surface brightness, so together they cover
    # (their share of the site's light) / R of today's Sun disc. The rings' dark backs block A / d^2 of sky.
    mirror_light = extra / (1 + extra)
    sky = {"mirror_share_of_daylight": mirror_light, "lit_mirrors_vs_todays_sun_disc": mirror_light / reflect,
           "simple_ring": {"where": "a great circle 90 deg from the Sun", "band_deg": math.degrees(simple["area_km2"] / (2 * math.pi * simple["distance_km"]) / simple["distance_km"]),
                           "sky_share": simple["area_km2"] / (4 * math.pi * simple["distance_km"] ** 2)}}
    full_moon_w = full["night"]["full_moon_lux_today"] / full["night"]["sunlight_lm_per_w"]
    moon_at_r_w = night.natural_full_moon_lux(full["night"], r_au) / full["night"]["sunlight_lm_per_w"]
    fleet_w = simple["area_km2"] * 1e6 * SOLAR_CONSTANT / r_au ** 2 * incidence(math.radians(sr["phi_deg"]))
    per_s = fleet_w / (math.pi * (sr["distance_km"] * 1e3) ** 2)      # Lambertian scatter s, at its brightest
    sky["simple_ring"]["scatter_w_m2_per_s"] = per_s
    sky["simple_ring"]["scatter_under_2.7au_full_moon_if_s_below"] = moon_at_r_w / per_s

    # The tow mirror faces Earth: its glow, and the beam light it scatters rather than reflects.
    en, tow = full["enablers"], full["tows"][0]
    beam = full["beam"]["total_limit_w"]
    r_m, dist = full["structures"]["earth-tow"]["mirror_radius_km"] * 1e3, tow["distance_km"] * 1e3
    t_glow = (en["e2_absorbed_fraction"] * beam / (math.pi * r_m ** 2) / (2 * en["e2_emissivity"] * SIGMA)) ** 0.25
    glow = en["e2_emissivity"] * SIGMA * t_glow ** 4 * (r_m / dist) ** 2
    earth_sun_w = SOLAR_CONSTANT * math.pi * R_EARTH ** 2
    glow_heat = 2 * beam * en["e2_absorbed_fraction"] * R_EARTH ** 2 / (4 * dist ** 2) / earth_sun_w   # as safety.py
    k = beam / (math.pi * dist ** 2)                               # W/m^2 at Earth per unit Lambertian scatter
    heat_budget = full["safety"]["mirror_heat_max_fraction_of_sunlight"] - glow_heat
    lux = glow * planck_lux_per_w(t_glow, *cfg["visible_um"])

    def glow_lux(power):   # the same at the beam power the run actually used
        t = (en["e2_absorbed_fraction"] * power / (math.pi * r_m ** 2) / (2 * en["e2_emissivity"] * SIGMA)) ** 0.25
        return en["e2_emissivity"] * SIGMA * t ** 4 * (r_m / dist) ** 2 * planck_lux_per_w(t, *cfg["visible_um"])
    run_beam = summary["tows"]["earth-tow"]
    tow_mirror = {"temperature_k": t_glow, "disc_deg": math.degrees(2 * r_m / dist), "bearing_from_sun_deg": cfg["tow_bearing_deg"],
                  "glow_w_m2": glow, "glow_lux": lux, "glow_vs_full_moon": lux / full["night"]["full_moon_lux_today"],
                  "glow_vs_2.7au_full_moon": lux / night.natural_full_moon_lux(full["night"], r_au),
                  "glow_lux_run": [glow_lux(run_beam["beam_min_w"]), glow_lux(run_beam["beam_max_w"])],
                  "glow_heat_share": glow_heat, "scatter_w_m2_per_s": k,
                  "scatter_limit_full_moon": full_moon_w / k,
                  "scatter_limit_heat": heat_budget * earth_sun_w / (k * math.pi * R_EARTH ** 2),
                  "heat_share_at_1e-6": 1e-6 * k * math.pi * R_EARTH ** 2 / earth_sun_w,
                  "covered_by_enablers": "E2 bounds absorption (1e-7) only; E1 sets no wavelength: neither bounds scatter"}

    satellites = {"panel_sunlight_vs_today": 1 / (1 + extra), "inside_km": cfg["geostationary_km"]}
    design = refractor(cfg, full, extra, sun, rays, r_au)
    guard = tow_protection(cfg, full, summary)
    return {"face_on_area_km2": face_on, "e3_limit_km2": limit, "sun_deg": math.degrees(sun),
            "hill_radius_km": r_au * AU / 1e3 * (full["habitability"]["earth_mass_with_moon_kg"] / (3 * 1.98892e30)) ** (1 / 3),
            "earth_shadow_km": R_EARTH / 1e3 / (sun / 2),
            "scan": scan, "simple_ring": simple, "light_ring": light, "sky": sky, "tow_mirror": tow_mirror,
            "satellites": satellites, "full_moon_w_m2": full_moon_w, "full_moon_2.7au_w_m2": moon_at_r_w,
            "refractor_l1": design, "tow_protection": guard}


def main() -> None:
    parser = argparse.ArgumentParser(description="Where the sunlight mirrors sit, and what Earth sees.")
    parser.add_argument("--out", default=str(ROOT / "results" / "mirrors.json"))
    args = parser.parse_args()
    r = run()
    print(f"Face-on area {r['face_on_area_km2']:.3g} km2 (E3 {r['e3_limit_km2']:.0e}); Sun {r['sun_deg']:.3f} deg; "
          f"Earth's shadow reaches {r['earth_shadow_km']:,.0f} km; Hill radius {r['hill_radius_km']:,.0f} km")
    for s in r["scan"]:
        print(f"phi {s['phi_deg']:6.2f}: incidence {s['incidence']:.3f}, area {s['area_km2']:.3g} km2, night share if "
              f"flooding {s['night_share_if_flooding']:.2f}, day-side-only flooding {s['area_day_side_flooding_km2']:.3g} km2")
    s = r["simple_ring"]
    c = s["capped_at_e3"]
    print(f"Simple ring: {s['area_km2']:.3g} km2 ({100 * s['over_e3']:.0f}% over E3), spot {s['spot_km']:.0f} km "
          f"({s['spot_fill']:.2f} of the strip), orbit {s['orbit_days']:.1f} days, turning {s['turning_m_s2']:.2e} m/s2 "
          f"(sail {', '.join(f'{k} {v:.1e}' for k, v in s['sail_m_s2'].items())}); beam gap {s['beam_gap_km']:,.0f} km; "
          f"capped at E3: {c['sunlight_vs_today']:.3f} of today's sunlight, {c['temperature_k']:.0f} K, water {c['liquid_water']:.2f}")
    lr = r["light_ring"]
    print(f"Light-held ring at {lr['phi_deg']} deg: {lr['area_km2']:.3g} km2 ({100 * lr['e3_margin']:.1f}% under E3), strip {lr['daylit_strip_km']:,.0f} km")
    for f, x in lr["films"].items():
        print(f"  {f}: {x['distance_km']:,.0f} km, spot {x['spot_km']:,.0f} km ({x['spot_fill']:.2f}), beam gap {x['beam_gap_km']:,.0f} km, "
              f"tow gap {x['tow_gap_km']:,.0f} km, tide {x['solar_tide_over_pull']:.3f}, works {x['works']}")
    t = r["tow_mirror"]
    print(f"Tow mirror: {t['temperature_k']:.0f} K, {t['disc_deg']:.2f} deg, glow {t['glow_w_m2']:.2f} W/m2 "
          f"({t['glow_lux']:.3f} lux: {t['glow_vs_full_moon']:.2f} of today's full Moon, {t['glow_vs_2.7au_full_moon']:.1f}x the 2.7 AU one); "
          f"scatter limit {t['scatter_limit_full_moon']:.1e} "
          f"(full Moon), {t['scatter_limit_heat']:.1e} (heat); 1e-6 adds {100 * t['heat_share_at_1e-6']:.1f}% of sunlight")
    sk = r["sky"]
    print(f"Sky: lit mirrors cover {sk['lit_mirrors_vs_todays_sun_disc']:.2f} of today's Sun disc; ring band "
          f"{sk['simple_ring']['band_deg']:.2f} deg, {100 * sk['simple_ring']['sky_share']:.2f}% of the sky; scatter stays under "
          f"the 2.7 AU full Moon if s < {sk['simple_ring']['scatter_under_2.7au_full_moon_if_s_below']:.1e}")
    print(f"Satellites: solar panels get {r['satellites']['panel_sunlight_vs_today']:.3f} of today's sunlight")
    d = r["refractor_l1"]
    print(f"Refracting ring near L1 ({d['l1_km']:,.0f} km), {d['areal_density_g_m2']} g/m2, {d['mass_kg']:.1e} kg; climate cliff "
          f"{d['climate_cliff_sunlight']:.3f} of today's sunlight; unstable e-fold {d['unstable_efold_days']:.0f} days, steering "
          f"{d['steering_needed_m_s2']:.1e} needed vs {d['steering_available_m_s2']:.1e} m/s2")
    for t, x in d["by_transmission"].items():
        print(f"  T {t}: {x['distance_km']:,.0f} km ({100 * x['past_l1']:.1f}% past L1), image {x['image_km']:,.0f} km, lands {x['lands']:.3f}, "
              f"area {x['area_km2']:.3g} km2 ({x['area_vs_e3']:.2f}x E3); at E3 {x['sunlight_vs_today_at_e3']:.3f} of today -> "
              f"{x['temperature_k']:.1f} K, water {x['liquid_water']:.2f}; ring {x['ring_km'][0]:,.0f}-{x['ring_km'][1]:,.0f} km, "
              f"halo {x['halo_deg'][0]:.2f}-{x['halo_deg'][1]:.2f} deg; beam gap {x['beam_gap_km']:,.0f} km")
    for name, g in r["tow_protection"].items():
        if name == "survey_warning_days":
            continue
        rk = g["rocks"]
        print(f"{name}: {g['years']['belt']:,.0f} belt years (whole tow {g['years']['whole_tow']:,.0f}); per year >=1 m {rk['1m']['per_year']:.3g}; "
              f"in the belt >=20 m {rk['20m']['over_belt']:.3g}, >=100 m {rk['100m']['over_belt']:.3g}, >=1 km {rk['1000m']['over_belt']:.3g} "
              f"(whole tow {rk['20m']['over_whole_tow']:.3g} / {rk['100m']['over_whole_tow']:.3g} / {rk['1000m']['over_whole_tow']:.3g}); "
              f"dust unrepaired {100 * g['dust_unrepaired']['belt']:.2f}% ({100 * g['dust_unrepaired']['whole_tow']:.2f}%); "
              f"cable >=10 m {g['cable_rocks_10m']['belt']:.2f} ({g['cable_rocks_10m']['whole_tow']:.2f}), {g['rock_10m_kt']:.2f} kt; "
              f"beam {g['beam_w_m2']:.2e} W/m2 = {g['beam_vs_sun_surface']:,.0f}x Sun's surface, 1 m rock gone in "
              f"{g['vaporise_1m_s'][0]:.4f}-{g['vaporise_1m_s'][2]:.4f} s; patch {g['patch_km2_per_year']:.1f} km2/yr; spare power "
              f"{100 * g['spare_power']:.1f}%; cable SF {g['cable_sf_at_cap']:.2f} (may lose {100 * g['cable_loss_allowed']:.1f}%); outage "
              f"{g['outage_all_off_days']} d all off, {g['outage_half_off_days']} d half off")
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(r, fh, indent=1, default=float)
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
