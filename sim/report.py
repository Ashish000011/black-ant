"""The results table for the README, built straight from results/ so no number is typed by hand.

    uv run python -m sim.report            # prints the table
    uv run python -m sim.report --readme   # also writes it into README.md between the results markers
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Results table from results/.")
    parser.add_argument("--readme", action="store_true", help="write it into README.md")
    args = parser.parse_args()
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
