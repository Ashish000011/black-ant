"""Results built straight from results/, so no number is typed by hand.

    uv run python -m sim.report              # prints the README's results table
    uv run python -m sim.report --readme     # also writes it into README.md between the results markers
    uv run python -m sim.report --momentum   # writes docs/momentum-record.md (a required deliverable)
"""

import argparse
import json
import re

from .config import ROOT

START, END = "<!-- results:start -->", "<!-- results:end -->"


def table(folder=ROOT / "results") -> str:
    s = json.loads((folder / "summary.json").read_text(encoding="utf-8"))
    lt = json.loads((folder / "longterm.json").read_text(encoding="utf-8"))
    m, base, verdict = lt["moved"], lt.get("baseline"), lt.get("verdict", {})
    earth, mars = s["tows"]["earth-tow"]["arrival"], s["tows"]["mars-tow"]["arrival"]
    fl, b = s["flags"], s.get("belt")
    covered = sorted({f["covered_by"] for f in fl["flags"] if f["covered_by"]})
    rows = [
        ("Earth arrives", f"year {earth['year']:,.0f} at {earth['a_au']} AU (limit: year 10,000); eccentricity "
                          f"{earth['eccentricity']}, orbit tilt {earth['tilt_deg']} deg"),
        ("Mars parks", f"year {mars['year']:,.0f} at {mars['a_au']} AU"),
        ("Closest Earth-Mars pass", f"{s['mars_closest']['au']} AU (limit 0.05)"),
        ("Closest big asteroid during the journey",
         ", ".join(f"{k} {v} AU" for k, v in s["big_asteroids_closest_au"].items()) + " (limit 0.02)"),
        ("Most beam power", f"{s['total_beam_max_w']:.3g} W (E1 limit 1e26)"),
        ("Ledger (the guide's form)", f"bodies' momentum change matches the applied impulse to "
                   f"{s['ledger']['integrator_honest_max']:.1e} of it; applied impulse plus its partners: "
                   f"{s['ledger']['nothing_from_nothing_max']:.1e} (limit 1e-9); beam work matches energy gained to "
                   f"{s['ledger']['work_mismatch_share']:.3%}"),
        ("Flags during the journey", f"{fl['unresolved']} unresolved; {fl['covered_by_enablers']} covered by "
                                     f"{', '.join(covered) or 'none'}"),
    ]
    c = s.get("climate")
    if c:
        rows.append(("Climate, computed along the journey", f"temperature {c['temperature_k'][0]:.1f} to "
                     f"{c['temperature_k'][1]:.1f} K (limit 288 +/- 2); sunlight {c['sunlight_share'][0]:.3f} to "
                     f"{c['sunlight_share'][1]:.3f} of today's; mirrors up to {c['mirror_area_km2'][1]:.3g} km2 (E3 limit 1e9); "
                     f"magnetopause {c['magnetopause_re'][0]:.1f} to {c['magnetopause_re'][1]:.1f} Earth radii; the Moon at "
                     f"{c['moon_hill_share'][1]:.2f} to {c['moon_hill_share'][0]:.3f} of Earth's Hill radius"))
    if b:
        rows.append(("Asteroid impacts (1 km and up), without E1's nudges",
                     f"one per {b['crossing']['years_per_impact']:,.0f} years crossing the belt, one per "
                     f"{b['parked_at_target']['years_per_impact']:,.0f} years parked; natural: one per 500,000"))
    r = m["ranges"]
    rows += [
        ("A million years after arrival: Earth", f"orbit {r['earth']['a'][0]:.3f} to {r['earth']['a'][1]:.3f} AU; "
         f"eccentricity up to {r['earth']['e'][1]:.3f}" + (f" (real Earth: up to {base['ranges']['earth']['e'][1]:.3f})" if base else "")),
        ("A million years after arrival: Mars", f"orbit {r['mars']['a'][0]:.3f} to {r['mars']['a'][1]:.3f} AU; "
         f"smallest gap to Earth's orbit {m['earth_mars_orbit_gap_min_au']:.3f} AU"),
        ("Earth's axial tilt", f"{m['axial_tilt_deg'][0]:.1f} to {m['axial_tilt_deg'][1]:.1f} deg"
         + (f" (real Earth: {base['axial_tilt_deg'][0]:.1f} to {base['axial_tilt_deg'][1]:.1f})" if base else "")),
    ]
    if verdict.get("seasons"):
        rows.append(("Sunlight the mirrors re-aim to keep today's seasons",
                     f"{verdict['seasons']['sunlight_to_reaim']:.1%} of Earth's sunlight (mirrors supply "
                     f"{verdict['seasons']['mirror_supplied_share']:.0%})"))
    if verdict.get("big_asteroid_nudges"):
        n = verdict["big_asteroid_nudges"]
        rows.append(("Big-asteroid passes near Earth", f"{n['passes']} in a million years; each nudged with at most "
                     f"{n['longest_beam_hours']:.1f} hours of a {n['beam_w']:.0e} W beam, {n['warning_years']} years ahead"))
    if verdict.get("flags"):
        vf = verdict["flags"]
        rows.append(("Flags after a million years", f"{vf['unresolved']} unresolved; {vf['covered_by_enablers']} covered by enablers"))
    thrown = [t["body"] for t in m.get("thrown_out", [])]
    rows.append(("Bodies thrown out in a million years", ", ".join(thrown) if thrown else "none"))
    out = ["| | |", "| --- | --- |"] + [f"| {k} | {v} |" for k, v in rows]
    return "\n".join(out)


def momentum_record(folder=ROOT / "results") -> str:
    """The conservation and momentum record: baseline drift, and the full ledger of the propulsion run."""
    from .benchmarks import b5
    s = json.loads((folder / "summary.json").read_text(encoding="utf-8"))
    lg = s["ledger"]
    real = json.loads((folder / "longterm_real_solar_system.json").read_text(encoding="utf-8"))["baseline"]
    lt = json.loads((folder / "longterm.json").read_text(encoding="utf-8"))["moved"]
    bench5 = b5()

    def vec(v):
        return "(" + ", ".join(f"{x:.4e}" for x in v) + ")"

    station, light, departed = lg["station_recoil_kg_m_s"], lg["bounced_light_kg_m_s"], lg["departed_kg_m_s"]
    partners = [a + b for a, b in zip(station, light)]
    lines = [
        "# Conservation and momentum record",
        "",
        "Generated from `results/` by `uv run python -m sim.report --momentum`. Every number comes from the running model.",
        "",
        "## Baseline drift (no push)",
        "",
        "| Run | Energy error | Limit |",
        "| --- | --- | --- |",
        f"| Official benchmark 5: Sun, Mercury to Neptune, 5 years, Yoshida fourth order, 0.25-day steps | {bench5['measured']:.2e} | 1e-9 |",
        f"| The real solar system for {real['years']:,} years (REBOUND MERCURIUS, 5-day steps) | {real['energy_error']:.2e} | 1e-6 |",
        f"| The moved solar system for {lt['years']:,} years after arrival | {lt['energy_error']:.2e} | 1e-6 |",
        "",
        "## The propulsion run's momentum ledger",
        "",
        "Earth is pulled only by gravity. The only outside forces in the run are the beams' pushes on the two tow asteroids",
        "(the applied impulse). Their partners are the beam stations, which recoil as they fire, and the light, which carries",
        "momentum away after bouncing. Gravity between bodies is applied in exactly opposite pairs. Asteroids sent away at",
        "the end of their tows take their momentum with them.",
        "",
        "| Account | Impulse, kg m/s (x, y, z; J2000 ecliptic) |",
        "| --- | --- |",
        f"| Applied impulse (beams on asteroids) | magnitude {lg['applied_impulse_kg_m_s']:.4e} |",
        f"| Beam stations' recoil | {vec(station)} |",
        f"| Bounced light | {vec(light)} |",
        f"| Station recoil plus bounced light | {vec(partners)} |",
        f"| Asteroids sent away | {vec(departed)} |",
        "",
        "| The guide's check | Worst during the run | At the end | Limit |",
        "| --- | --- | --- | --- |",
        f"| Integrator is honest: bodies' momentum change against the applied impulse | {lg['integrator_honest_max']:.1e} | "
        f"{lg['integrator_honest_end']:.1e} | 1e-9 of the applied impulse |",
        f"| Nothing from nothing: applied impulse plus its partners | {lg['nothing_from_nothing_max']:.1e} | "
        f"{lg['nothing_from_nothing_end']:.1e} | 1e-9 of the applied impulse |",
        "",
        "The stepper keeps every rounding error (sim/ledger.py): each pair's gravity forces are exact negatives bit for bit, "
        "and every push is added with an error-free sum, so momentum is conserved to the precision of the arithmetic itself.",
        "",
        "## Energy",
        "",
        f"The beams did {lg['beam_work_j']:.4e} J of work on the bodies; the bodies gained {lg['bodies_energy_gain_j']:.4e} J "
        f"(counting what left with the asteroids sent away). They match to {lg['work_mismatch_share']:.3%}. The worst gap "
        f"between the two during the run was {lg['energy_error_max_of_total']:.1e} of the system's total energy (limit 1e-5).",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Results built from results/.")
    parser.add_argument("--readme", action="store_true", help="write the results table into README.md")
    parser.add_argument("--momentum", action="store_true", help="write docs/momentum-record.md")
    args = parser.parse_args()
    if args.momentum:
        (ROOT / "docs" / "momentum-record.md").write_text(momentum_record(), encoding="utf-8")
        print("Wrote docs/momentum-record.md")
        return
    t = table()
    print(t)
    if args.readme:
        path = ROOT / "README.md"
        text = path.read_text(encoding="utf-8")
        block = f"{START}\n{t}\n{END}"
        if START in text:
            text = re.sub(re.escape(START) + ".*?" + re.escape(END), lambda _: block, text, flags=re.S)
        else:
            text = text.replace("RESULTS_TABLE", block)
        path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
