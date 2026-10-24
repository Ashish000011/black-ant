"""The journey: Earth (and Mars, ahead of it) towed outward by light-pushed asteroids.

Every check step runs the safety, structure and orbit checks and records flags; the run ends with a
belt-impact estimate and saves the final state for the long-term stability run.

Run from the project root:
    uv run python -m sim.scenarios.tow                       # settings from config.yaml
    uv run python -m sim.scenarios.tow --years 200            # a short run
    uv run python -m sim.scenarios.tow --orbits circular      # flat circular starting orbits
    uv run python -m sim.scenarios.tow --no-mars-tow          # see why Mars must move first
"""

import argparse
import math
import time

import numpy as np

from ..belt import BeltSample
from ..bodies import System, add_state_bodies, move_to_barycentre, orbit_elements, start_planets
from ..checks.safety import nudge_hours, safety_checks
from ..checks.structure import structure_checks
from ..config import load_config
from ..constants import AU, C_LIGHT, DAY, YEAR
from ..export import write_outputs
from ..flags import Flags, check
from ..forces import Beam, Tow, beam_for, ray_distance, spot
from ..integrator import energy, gravity
from ..ledger import Ledger
from ..secular import Trim
from ..spin import TODAY_AXIS, follow_spin, orbit_pole

REAL_WORLD_POWER_W = 2e13  # all of humanity's power use today, roughly; anything above needs E1


def build(cfg: dict, mars_tow: bool = True, orbits: str | None = None) -> tuple[System, list[Tow], list[int]]:
    """Planets on their starting orbits, the big asteroids, and one tow asteroid on its spot for each tow."""
    system = start_planets(cfg["planets"], orbits or cfg["run"]["start_orbits"])
    small = add_state_bodies(system, cfg.get("small_bodies", [])) if (orbits or cfg["run"]["start_orbits"]) == "real" else []
    no_acc = np.zeros_like(system.pos)
    tows = []
    for t in cfg["tows"]:
        if t["target"] == "mars" and not mars_tow:
            continue
        target = system.index(t["target"])
        distance = t["distance_km"] * 1e3
        p, v, _ = spot(system.pos, system.vel, no_acc, 0, target, distance)
        idx = system.add(t["name"], t["asteroid_mass_kg"], p, v)
        tows.append(Tow(t["name"], target, idx, t["asteroid_mass_kg"], distance, t["stop_au"], t["max_beam_w"]))
    move_to_barycentre(system)
    return system, tows, small


def run(cfg: dict | None = None, years: float | None = None, dt_days: float | None = None,
        mars_tow: bool = True, orbits: str | None = None, after_arrival_years: float = 200,
        belt: bool = True, outage: tuple[float, float, float] | None = None,
        progress: bool = False) -> tuple[dict, list[dict], dict]:
    """Step the whole journey. Returns (summary, frames, end_state).
    outage: (start year, days, share of power left, tow name) for one tow's beam, to test a failure."""
    cfg = cfg or load_config()
    orbits = orbits or cfg["run"]["start_orbits"]
    years = cfg["run"]["years"] if years is None else years
    dt = (dt_days or cfg["run"]["dt_days"]) * DAY
    check_every = cfg["run"]["check_every_steps"]
    frame_every = max(1, round(cfg["run"]["frame_every_years"] * YEAR / dt))
    wc = 2 * math.pi / (cfg["controller"]["correction_period_days"] * DAY)
    kp, kd = wc * wc, 2 * wc
    clearance = cfg["beam"]["earth_clearance_km"] * 1e3
    routes = [(d, math.cos(math.radians(d)), math.sin(math.radians(d))) for d in cfg["beam"]["route_angles_deg"]]
    limit = cfg["beam"]["total_limit_w"]
    s_cfg, arrival_cfg = cfg["safety"], cfg["arrival"]

    system, tows, small = build(cfg, mars_tow, orbits)
    m, pos, vel = system.m, system.pos, system.vel
    sun, earth, mars, jupiter, saturn = (system.index(n) for n in ("sun", "earth", "mars", "jupiter", "saturn"))
    ledger, flags = Ledger(), Flags()
    beam_acc = np.zeros_like(pos)  # each asteroid's acceleration from its beam
    sample: BeltSample | None = None
    sample_acc = None
    clock = {"yr": 0.0}
    trims = {}  # tow name -> its arrival trim; Mars's settings override the shared ones
    at = cfg.get("arrival_trim", {})
    if at.get("enabled"):
        for tow in tows:
            own = at.get(tow.name, {})
            if tow.name == "earth-tow" or own:
                base = {k: v for k, v in at.items() if not isinstance(v, dict)}
                trims[tow.name] = Trim({**base, **own}, tow.distance)
    outage_end = outage[0] + outage[1] * DAY / YEAR if outage else 0.0

    def set_beams(acc):
        # Plain Python lists make the many small calculations below much faster than NumPy scalars.
        p_list, v_list, a_list, m_list = pos.tolist(), vel.tolist(), acc.tolist(), m.tolist()
        beam_acc.fill(0.0)
        used = 0.0
        for tow in reversed(tows):  # Mars first: the Earth tow may use whatever of E1's budget Mars isn't using
            cap = (limit - used) * (1 - 1e-12)  # a hair inside, so rounding never tips the total over
            if outage and tow.name == outage[3] and outage[0] <= clock["yr"] < outage_end:
                cap = min(cap, tow.max_beam_w) * outage[2]  # stations lost: a share of what this tow could have
            if not tow.active or cap <= 0:
                tow.beam = Beam()
                continue
            beam, capped = beam_for(tow, m_list, p_list, v_list, a_list, sun, earth, kp, kd, clearance, routes, cap)
            if beam is None:
                tow.no_route_steps += 1
                tow.beam = Beam()
                continue
            tow.rerouted_steps += beam.route_deg != 0
            tow.capped_steps += capped
            tow.beam = beam
            used += beam.power
            beam_acc[tow.asteroid] = np.array(beam.force) / m[tow.asteroid]

    def kick(acc, h):
        total = acc + beam_acc
        v_rows, t_rows = None, None
        for tow in tows:
            if tow.active and tow.beam.power > 0:  # book the beam's work at the asteroid's mid-kick velocity
                if v_rows is None:
                    v_rows, t_rows = vel.tolist(), total.tolist()
                va, ta = v_rows[tow.asteroid], t_rows[tow.asteroid]
                ledger.book_beam(tow.beam, (va[0] + 0.5 * ta[0] * h, va[1] + 0.5 * ta[1] * h, va[2] + 0.5 * ta[2] * h), h)
        np.add(vel, total * h, out=vel)

    def send_away(tow):
        """A finished tow's asteroid is sent away: it leaves the run, and the ledger keeps what it carried."""
        a = tow.asteroid
        before = energy(m, pos, vel)
        for i in range(3):
            ledger.departed[i] += float(m[a] * vel[a, i])
        m[a] = 0.0
        tow.active, tow.beam = False, Beam()
        ledger.departed_energy += before - energy(m, pos, vel)

    def dist(i, j):
        return float(np.linalg.norm(pos[i] - pos[j]))

    # Places where the design relies on an enabler: allowed flags, recorded up front.
    covers = cfg["enablers"]["covers"]
    flags.note(f"Tow mirrors and cables. {covers['E2']}", cfg["enablers"]["e2_absorbed_fraction"], "absorbed share", "E2")
    flags.note(f"Asteroids and mirrors in place. {covers['E3']}", sum(t.mass for t in tows), "kg of asteroids", "E3")

    acc = gravity(m, pos)
    set_beams(acc)
    e0 = energy(m, pos, vel)
    p0 = ledger.total_momentum(m, vel)
    stats = {t.name: {"beam_min_w": math.inf, "beam_max_w": 0.0, "mirror_angle_min_deg": 180.0,
                      "mirror_angle_max_deg": 0.0, "spot_error_max_km": 0.0, "beam_clearance_min_km": math.inf,
                      "target_distance_km": [math.inf, 0.0],
                      "arrival": None} for t in tows}
    no_route_seen = {t.name: 0 for t in tows}
    total_beam_max = 0.0
    mars_min, mars_min_year, mars_window = math.inf, 0.0, math.inf
    small_min = {system.names[i]: math.inf for i in small}
    small_window, small_window_body = math.inf, None
    nudges = []  # big-asteroid passes inside the limit, and E1's cost to push each one outside
    jupiter_min = math.inf
    energy_err_max = momentum_err_max = 0.0
    last = {"gain": 0.0}
    frames = []
    steps = round(years * YEAR / dt)
    started = time.time()

    for n in range(steps + 1):
        yr = n * dt / YEAR
        if belt and sample is None and yr >= cfg["belt_sample"]["start_year"]:
            sample = BeltSample(cfg["belt_sample"], pos[sun].copy(), vel[sun].copy(), yr)
            sample_acc = sample.accel(m, pos)
        if n % check_every == 0:
            results, total = [], 0.0
            for tow in tows:
                if tow.name in trims and tow.active:
                    trims[tow.name].update(m, pos, vel, sun, tow.target, jupiter, saturn)
            earth_orbit = orbit_elements(system, earth, sun)
            for tow in tows:
                if not tow.active:
                    continue
                st, b, a = stats[tow.name], tow.beam, tow.asteroid
                total += b.power
                sp, _, _ = spot(pos, vel, acc, sun, tow.target, tow.distance, tow.shape)
                err = float(np.linalg.norm(pos[a] - np.array(sp)))
                d_target = dist(a, tow.target) / 1e3
                st["target_distance_km"] = [min(st["target_distance_km"][0], d_target), max(st["target_distance_km"][1], d_target)]
                if yr > 1:
                    st["spot_error_max_km"] = max(st["spot_error_max_km"], err / 1e3)
                    results.append(check(f"{tow.name}: asteroid off its spot", err / tow.distance,
                                         s_cfg["spot_error_max_fraction"], "max", "share of its distance"))
                if tow.no_route_steps > no_route_seen[tow.name]:
                    results.append(check(f"{tow.name}: no allowed beam could hold the asteroid", 1, 0, "max", "steps"))
                    no_route_seen[tow.name] = tow.no_route_steps
                f_len = 0.0
                if b.power > 0:
                    f = np.array(b.force)
                    f_len = float(np.linalg.norm(f))
                    angle = math.degrees(math.acos(float(np.dot(b.incoming, f)) / f_len))
                    st["mirror_angle_min_deg"] = min(st["mirror_angle_min_deg"], angle)
                    st["mirror_angle_max_deg"] = max(st["mirror_angle_max_deg"], angle)
                    st["beam_min_w"] = min(st["beam_min_w"], b.power)
                    st["beam_max_w"] = max(st["beam_max_w"], b.power)
                    ap, ep = tuple(pos[a].tolist()), tuple(pos[earth].tolist())
                    back = tuple(-x for x in b.incoming)
                    clear = min(ray_distance(ep, ap, back, dist(a, sun)), ray_distance(ep, ap, b.outgoing))
                    st["beam_clearance_min_km"] = min(st["beam_clearance_min_km"], clear / 1e3)
                    results.append(check(f"{tow.name}: beam passes near Earth", clear / 1e3,
                                         cfg["beam"]["earth_clearance_km"], "min", "km"))
                results += structure_checks(cfg, tow.name, f_len, b.power, tow.mass, tow.distance, float(m[tow.target]))
                orb = orbit_elements(system, tow.target, sun)
                if orb["a"] >= tow.stop_au:
                    st["arrival"] = {"year": round(yr, 1), "a_au": round(orb["a"], 4), "eccentricity": round(orb["e"], 4),
                                     "tilt_deg": round(orb["i"], 3), "speed_km_s": round(orb["v"] / 1e3, 2)}
                    if tow.name in trims:
                        st["arrival"]["free_eccentricity"] = round(trims[tow.name].free_e, 4)
                        st["arrival"]["free_tilt_deg"] = round(trims[tow.name].free_tilt, 3)
                    send_away(tow)
            earth_tow = tows[0]
            results += safety_checks(cfg, earth_orbit["a"], earth_tow.mass if earth_tow.active else None,
                                     earth_tow.distance, earth_tow.beam.power if earth_tow.active else 0.0)
            total_beam_max = max(total_beam_max, total)
            results.append(check("Total beam power within E1's limit", total, limit, "max", "W"))
            results.append(check("Closest Earth to Mars", mars_window / AU, s_cfg["mars_min_distance_au"], "min", "AU"))
            if small:
                limit_m = s_cfg["big_asteroid_min_distance_au"] * AU
                covered = None
                if small_window < limit_m:  # E1 nudges it decades ahead so it passes outside the limit
                    hours = nudge_hours(float(m[small_window_body]), limit_m - small_window, cfg["longterm"]["nudge"])
                    nudges.append({"year": round(yr, 1), "body": system.names[small_window_body],
                                   "au": round(small_window / AU, 4), "beam_hours": round(hours, 3)})
                    covered = "E1" if hours <= cfg["longterm"]["nudge"]["max_hours"] else None
                results.append(check("Closest Earth to a big asteroid", small_window / AU,
                                     s_cfg["big_asteroid_min_distance_au"], "min", "AU", covered_by=covered))
            results.append(check("Earth's eccentricity", earth_orbit["e"], arrival_cfg["max_eccentricity"], "max"))
            gain = energy(m, pos, vel) - e0 + ledger.departed_energy
            last["gain"] = gain
            e_err = abs(gain - ledger.work) / abs(e0)
            p_err = float(np.linalg.norm(ledger.total_momentum(m, vel) - p0))
            scale = float((m * np.linalg.norm(vel, axis=1)).sum())
            if yr > 1:
                energy_err_max = max(energy_err_max, e_err)
                results.append(check("Energy ledger error", e_err, s_cfg["energy_error_max_of_total"], "max", "share of total"))
            momentum_err_max = max(momentum_err_max, p_err / scale)
            results.append(check("Momentum ledger error", p_err / scale, s_cfg["momentum_error_max"], "max", "share"))
            failed = [r["check"] for r in results if flags.record(r, yr)]
            mars_window = small_window = math.inf
            jupiter_min = min(jupiter_min, dist(earth, jupiter) / AU)
            if n % frame_every < check_every:
                frames.append(frame(system, tows, yr, e_err, p_err / scale, failed))
            if not earth_tow.active and yr > stats[earth_tow.name]["arrival"]["year"] + after_arrival_years:
                break
            if progress and n % (check_every * 500) == 0:
                print(f"  year {yr:7.0f}  Earth at {earth_orbit['a']:.3f} AU  ({time.time() - started:.0f} s)")
        d_mars = dist(earth, mars)
        mars_window = min(mars_window, d_mars)
        if d_mars < mars_min:
            mars_min, mars_min_year = d_mars, yr
        if small:
            d_small = np.linalg.norm(pos[small] - pos[earth], axis=1)
            k_min = int(d_small.argmin())
            if d_small[k_min] < small_window:
                small_window, small_window_body = float(d_small[k_min]), small[k_min]
            for k, i in enumerate(small):
                small_min[system.names[i]] = min(small_min[system.names[i]], float(d_small[k]))
        clock["yr"] = (n + 1) * dt / YEAR
        kick(acc, dt / 2)
        if sample is not None:
            sample.vel += sample_acc * (dt / 2)
            earth_before, sample_before = pos[earth].copy(), sample.pos.copy()
            sample.pos += sample.vel * dt
        np.add(pos, vel * dt, out=pos)
        acc = gravity(m, pos)
        for tow in tows:
            if tow.name in trims and tow.active:
                trims[tow.name].apply(tow, pos, sun, tow.target)
        set_beams(acc)
        if sample is not None:
            sample_acc = sample.accel(m, pos)
            sample.track(earth_before, pos[earth], sample_before, dt, yr)
            sample.vel += sample_acc * (dt / 2)
        kick(acc, dt / 2)

    # End-of-run checks: beam power beyond any real source, arrival, and the asteroid belt.
    if total_beam_max > REAL_WORLD_POWER_W:
        flags.note(f"Beam power far above all of humanity's ({REAL_WORLD_POWER_W:.0e} W). {covers['E1']}",
                   total_beam_max, "W", "E1")
    arrival = stats[tows[0].name]["arrival"]
    flags.record(check("Earth reaches its target within 10,000 years", arrival["year"] if arrival else math.inf,
                       arrival_cfg["max_years"], "max", "years"), yr)
    belt_summary = None
    if sample is not None:
        belt_summary = sample.summary(yr, s_cfg["natural_1km_impact_interval_years"], arrival["year"] if arrival else None)
        # Above Earth's natural rate, E1's beams nudge any asteroid found heading for Earth: 5 cm/s given ten years
        # ahead moves a 1 km asteroid's arrival by about 3 x 0.05 m/s x 10 years = 47,000 km, over seven Earth radii.
        rock = 2500 * 4 / 3 * math.pi * 500.0 ** 3
        belt_summary["deflection"] = {"asteroid_kg": rock, "speed_change_m_s": 0.05, "beam_days": 1,
                                      "beam_power_w": rock * 0.05 * C_LIGHT / (2 * DAY), "warning_years": 10}
        natural = 1.0 / s_cfg["natural_1km_impact_interval_years"]
        for label, part in (("crossing the belt", belt_summary["crossing"]), ("parked at the target", belt_summary["parked_at_target"])):
            if part["years"] > 0:
                times = part["expected_impacts"] / (part["years"] * natural)
                flags.record(check(f"Expected 1 km impacts {label}, against Earth's natural rate", times, 1.0, "max",
                                   "times natural", covered_by="E1" if times > 1.0 else None), yr)

    # Earth's spin axis, from where it points today, turned by the Sun and Moon along the journey's orbit.
    tilts, spin_axis = follow_spin([f["t"] for f in frames], [f["earth_pole"] for f in frames],
                                   [f["earth_orbit_au"] for f in frames], [f["earth_eccentricity"] for f in frames],
                                   cfg["spin"], TODAY_AXIS)
    end_e, end_m = orbit_elements(system, earth, sun), orbit_elements(system, mars, sun)
    keep = m > 0
    end_state = {"year": round(yr, 1), "names": [nm for nm, k in zip(system.names, keep) if k],
                 "mass_kg": m[keep].tolist(), "pos_m": pos[keep].tolist(), "vel_m_s": vel[keep].tolist(),
                 "spin_axis": spin_axis}
    summary = {
        "settings": {"years": years, "dt_days": dt / DAY, "mars_tow": mars_tow, "start_orbits": orbits,
                     "bodies": system.names, "frame_every_years": cfg["run"]["frame_every_years"], "beam_limit_w": limit,
                     "belt_sample": belt,
                     "model": ("real tilted, oval orbits from J2000.0 positions" if orbits == "real"
                               else "flat circular starting orbits at J2000 mean longitudes") + "; Earth carries the Moon's mass",
                     "tows": [{"name": t.name, "asteroid_mass_kg": t.mass, "distance_km": t.distance / 1e3,
                               "stop_au": t.stop_au} for t in tows]},
        "flags": flags.summary(),
        "tows": {t.name: {**stats[t.name], "days_without_allowed_beam": round(t.no_route_steps * dt / 2 / DAY, 1),
                          "days_rerouted": round(t.rerouted_steps * dt / 2 / DAY, 1),
                          "days_power_capped": round(t.capped_steps * dt / 2 / DAY, 1)} for t in tows},
        "arrival_trim": {name: {"beta_mean": t.beta_sum / max(t.updates, 1), "free_eccentricity_end": t.free_e,
                                "free_tilt_end_deg": t.free_tilt} for name, t in trims.items()},
        "axial_tilt_journey_deg": [round(min(tilts), 3), round(max(tilts), 3)] if tilts else None,
        "total_beam_max_w": total_beam_max,
        "station_recoil_max_n": total_beam_max / C_LIGHT,
        "mars_closest": {"au": round(mars_min / AU, 5), "year": round(mars_min_year, 1)},
        "jupiter_closest_au": round(jupiter_min, 3),
        "big_asteroids_closest_au": {k: round(v / AU, 4) for k, v in small_min.items()},
        "big_asteroid_nudges": nudges,
        "belt": belt_summary,
        "end": {"year": round(yr, 1),
                "earth": {"a_au": round(end_e["a"], 4), "eccentricity": round(end_e["e"], 4), "tilt_deg": round(end_e["i"], 3)},
                "mars": {"a_au": round(end_m["a"], 4), "eccentricity": round(end_m["e"], 4), "tilt_deg": round(end_m["i"], 3)}},
        "ledger": {"energy_error_max_of_total": energy_err_max, "beam_work_j": ledger.work,
                   "bodies_energy_gain_j": last["gain"],
                   "work_mismatch_share": abs(last["gain"] - ledger.work) / max(ledger.work, 1.0),
                   "momentum_error_max": momentum_err_max},
        "run_seconds": round(time.time() - started, 1),
    }
    return summary, frames, end_state


def frame(system: System, tows: list[Tow], yr: float, e_err: float, p_err: float, failed: list[str]) -> dict:
    """One saved moment of the run, in the format the viewer reads (positions [x, y, z] relative to the Sun, AU)."""
    sun, earth, mars, jupiter = (system.index(n) for n in ("sun", "earth", "mars", "jupiter"))

    def rel(i):
        return [round(float(c), 6) for c in (system.pos[i] - system.pos[sun]) / AU]

    oe, om = orbit_elements(system, earth, sun), orbit_elements(system, mars, sun)
    return {"t": round(yr, 1), "pos": {"earth": rel(earth), "mars": rel(mars), "jupiter": rel(jupiter),
                                       "asteroid": rel(tows[0].asteroid)},
            "earth_orbit_au": round(oe["a"], 5), "earth_eccentricity": round(oe["e"], 5),
            "earth_pole": [round(c, 8) for c in orbit_pole(system.pos[earth], system.vel[earth], system.pos[sun], system.vel[sun])],
            "mars_orbit_au": round(om["a"], 5),
            "beam_power_w": sum(t.beam.power for t in tows if t.active),
            "energy_error": e_err, "momentum_error": p_err, "earth_tow_active": tows[0].active, "flags": failed}


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Earth tow journey.")
    parser.add_argument("--years", type=float, help="stop after this many years (default: config.yaml)")
    parser.add_argument("--dt-days", type=float, help="step size in days (default: config.yaml)")
    parser.add_argument("--orbits", choices=["real", "circular"], help="starting orbits (default: config.yaml)")
    parser.add_argument("--no-mars-tow", action="store_true", help="leave Mars where it is")
    parser.add_argument("--no-belt", action="store_true", help="skip the asteroid-belt sample (faster)")
    parser.add_argument("--mars-stop-au", type=float, help="where Mars's tow stops (default: config.yaml)")
    parser.add_argument("--out", help="output folder (default: out/)")
    args = parser.parse_args()
    cfg = load_config()
    if args.mars_stop_au:
        next(t for t in cfg["tows"] if t["target"] == "mars")["stop_au"] = args.mars_stop_au
    summary, frames, end_state = run(cfg, years=args.years, dt_days=args.dt_days, mars_tow=not args.no_mars_tow,
                                     orbits=args.orbits, belt=not args.no_belt, progress=True)
    out = write_outputs(summary, frames, args.out, end_state)
    print(f"Starting orbits: {summary['settings']['start_orbits']}")
    for name, t in summary["tows"].items():
        arrival = t["arrival"]
        print(f"{name}: " + (f"arrived year {arrival['year']}, orbit {arrival['a_au']} AU, eccentricity {arrival['eccentricity']}, "
                             f"tilt {arrival['tilt_deg']} deg" if arrival else "did not arrive"))
    print(f"Closest Earth to Mars: {summary['mars_closest']['au']} AU in year {summary['mars_closest']['year']}")
    if summary["big_asteroids_closest_au"]:
        print("Closest Earth to big asteroids (AU): " + ", ".join(f"{k} {v}" for k, v in summary["big_asteroids_closest_au"].items()))
    if summary["belt"]:
        b = summary["belt"]
        print(f"Belt sample: {b['sample_encounters']} passes within {b['close_pass_au']} AU by {b['sample_size']} test asteroids "
              f"over {b['years_tracked']} years; closest {b['sample_closest_au']} AU")
        for label, part in (("crossing", b["crossing"]), ("parked", b["parked_at_target"])):
            print(f"  {label}: {part['years']} years, {part['sample_encounters']} passes, "
                  f"one 1 km impact per {part['years_per_impact']:.3g} years expected (natural: one per 500,000)")
    fl = summary["flags"]
    print(f"Flags: {fl['unresolved']} unresolved, {fl['covered_by_enablers']} covered by enablers")
    for f in fl["flags"]:
        print(f"  [{f['covered_by'] or 'UNRESOLVED'}] {f['check']}: worst {f['worst']:.4g} {f['unit']} "
              f"(limit {f['limit']:.4g}), years {f['first_year']}-{f['last_year']}, {f['times']} checks")
    print(f"Ledger: momentum error {summary['ledger']['momentum_error_max']:.1e}, "
          f"work mismatch {summary['ledger']['work_mismatch_share']:.3%}")
    print(f"Wrote {out / 'summary.json'}, {out / 'run.json'} and {out / 'end_state.json'} in {summary['run_seconds']} s")


if __name__ == "__main__":
    main()
