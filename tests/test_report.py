"""The technical report (issue #15: "every number matches results/") and the pitch documents (issue #11).

Each check takes a number from results/ (or from the model, for numbers the run does not save), writes it the way
the documents do, and looks for it. Re-run the journey and a number that moved fails here until the text follows.
Run: uv run pytest tests/test_report.py
"""

import json
import math
import re
import shutil
import subprocess

import pytest

from sim.checks.structure import structure_checks
from sim.config import ROOT, load_config
from sim.constants import AU, C_LIGHT, G, GM_SUN, YEAR
from sim.habitability import day_length_rate

CFG = load_config()
RESULTS = ROOT / "results"
DOCS = ROOT / "docs"
S = json.loads((RESULTS / "summary.json").read_text(encoding="utf-8"))
LT = json.loads((RESULTS / "longterm.json").read_text(encoding="utf-8"))
OCTO = json.loads((RESULTS / "octo_earth.json").read_text(encoding="utf-8"))
OUTAGE = {o["name"]: o for o in json.loads((RESULTS / "outage.json").read_text(encoding="utf-8"))}
CROSSING = json.loads((RESULTS / "crossing.json").read_text(encoding="utf-8"))["variants"]
CHAOS = json.loads((RESULTS / "longterm_chaos_copies.json").read_text(encoding="utf-8"))["copies"]
EARTH, MARS = S["tows"]["earth-tow"], S["tows"]["mars-tow"]
TOW = {t["name"]: t for t in CFG["tows"]}
PLANET = {p["name"]: p for p in CFG["planets"]}


def text(name: str) -> str:
    """A document as one line, without quote marks at line starts and with "x 10^" written as "× 10^"."""
    doc = re.sub(r"^> ", "", (DOCS / name).read_text(encoding="utf-8"), flags=re.M)
    return re.sub(r"\s+", " ", doc).replace(" x 10^", " × 10^")


def sci(x: float, digits: int = 2) -> str:
    """3.97e20 -> '3.97 × 10^20', as the documents write it."""
    mantissa, exponent = f"{x:.{digits - 1}e}".split("e")
    return f"{mantissa} × 10^{int(exponent)}"


def days(d: float) -> str:
    """An outage as the report writes it: hours under a day; quarter days exactly, others to a tenth."""
    if d < 1:
        return f"{d * 24:.1f}".removesuffix(".0") + " hours"
    return (f"{d:g}" if (4 * d).is_integer() else f"{d:.1f}") + " days"


def structures(tow: str, power: float) -> dict:
    """The structure checks at a beam power, sized as the report says: the most a beam can push, 2P/c, with the
    asteroid at the closest it comes to its planet (Mars's sprints in to 200,000 km)."""
    t = TOW[tow]
    closest = min(t["distance_km"], t.get("sprint", {}).get("distance_km", math.inf))
    out = structure_checks(CFG, tow, 2 * power / C_LIGHT, power, t["asteroid_mass_kg"], closest * 1e3,
                           PLANET[t["target"]]["mass_kg"])
    return {r["check"].split(": ", 1)[1]: r["value"] for r in out}


def report_facts() -> list[tuple[str, str]]:
    """(what, the text the report must contain), every number from results/ or the model."""
    ea, ma, led, cl, belt = EARTH["arrival"], MARS["arrival"], S["ledger"], S["climate"], S["belt"]
    lo = {k: v[0] for k, v in cl.items()}
    hi = {k: v[1] for k, v in cl.items()}
    et, mt = TOW["earth-tow"], TOW["mars-tow"]
    d = et["distance_km"] * 1e3
    m_earth = CFG["habitability"]["earth_mass_with_moon_kg"]
    radius = (3 * et["asteroid_mass_kg"] / (4 * math.pi * CFG["structures"]["earth-tow"]["asteroid_density_kg_m3"])) ** (1 / 3)
    lod = day_length_rate(et["asteroid_mass_kg"], d) * ea["year"] * YEAR  # tow at its closest the whole way
    cap = {tow: structures(tow, TOW[tow]["max_beam_w"]) for tow in TOW}
    used = structures("earth-tow", EARTH["beam_max_w"])
    sf_min = min(v for c in cap.values() for k, v in c.items() if "safety factor" in k)
    flags = S["flags"]
    e3 = next(f for f in flags["flags"] if f["covered_by"] == "E3")
    vesta_minutes = max(n["beam_hours"] for n in S["big_asteroid_nudges"]) * 60
    m, base, verdict = LT["moved"], LT["baseline"], LT["verdict"]
    mr, br = m["ranges"], base["ranges"]
    nudges = verdict["big_asteroid_nudges"]
    arms = OCTO["net_force_all_arms"]
    outside = OCTO["outside_field"]
    steel = next(x for x in OCTO["materials"] if x["name"].startswith("Structural steel"))
    nanotube = next(x for x in OCTO["materials"] if x["name"].startswith("Carbon nanotube"))
    longest_arm = OCTO["arm"]["length_km"]
    facts = [
        ("arrival", f"{ea['a_au']} AU in year {ea['year']:,.0f}"),
        ("arrival eccentricity", f"eccentricity of {ea['eccentricity']:.3f}"),
        ("arrival tilt and speed", f"tilt of {ea['tilt_deg']:.2f}° to today's ecliptic, moving at {ea['speed_km_s']:.1f} km/s"),
        ("free eccentricity", f"free eccentricity left is {ea['free_eccentricity']}"),
        ("Mars parks", f"{ma['a_au']:.2f} AU in year {ma['year']:,.0f}"),
        ("Mars parks, exact", f"{ma['a_au']:.3f} AU in year {ma['year']:,.0f}"),
        ("Mars ahead of Earth", f"{round(ea['year'] - ma['year'], -2):,.0f} years before Earth"),
        ("closest Earth-Mars pass", f"closest pass is {S['mars_closest']['au']:.2f} AU"),
        ("closest Earth-Mars pass, exact", f"({S['mars_closest']['au']:.3f} AU"),
        ("flags", f"{flags['unresolved']} unresolved; {flags['covered_by_enablers']} caused by enablers"),
        ("Earth's asteroid", f"{sci(et['asteroid_mass_kg'], 3)} kg asteroid ({radius / 1e3:.0f} km in radius at "
                             f"{CFG['structures']['earth-tow']['asteroid_density_kg_m3']:,} kg/m³) sits {et['distance_km']:,} km"),
        ("its pull", f"{sci(G * m_earth * et['asteroid_mass_kg'] / d ** 2, 3)} N, an acceleration of "
                     f"{sci(G * et['asteroid_mass_kg'] / d ** 2, 3)} m/s²"),
        ("beam clearance", f"within {CFG['beam']['earth_clearance_km']:,} km of Earth"),
        ("closest beam", f"The closest any beam came was {EARTH['beam_clearance_min_km']:,.0f} km"),
        ("Earth tow power", f"{EARTH['beam_min_w'] / 1e25:.1f} to {sci(EARTH['beam_max_w'])} W"),
        ("spot error", f"{EARTH['spot_error_max_km']:,.0f} km ({EARTH['spot_error_max_km'] / et['distance_km']:.1%})"),
        ("Mars's asteroid", f"{sci(mt['asteroid_mass_kg'], 3)} kg asteroid {mt['distance_km']:,} km from Mars"),
        ("crossing, normal pull", f"caught in {CROSSING['normal pull']['caught']} of {CROSSING['normal pull']['of']}"),
        ("Mars's sprint", f"{mt['sprint']['distance_km']:,} km for "
                          f"{(mt['distance_km'] / mt['sprint']['distance_km']) ** 2:.0f}× the pull (caught in "
                          f"{CROSSING['chosen: sprint 4x with the asteroid at 400,000 km (to 200,000 km)']['caught']} of 8)"),
        ("Earth eases out", f"{et['sprint']['distance_km']:,} km"),
        ("most beam power", f"{sci(S['total_beam_max_w'], 3)} W"),
        ("sunlight", f"{lo['sunlight_share']:.3f} to {hi['sunlight_share']:.3f} of today's sunlight"),
        ("mirror area", f"{sci(hi['mirror_area_km2'])} km²"),
        ("asteroids placed (E3)", f"{sci(e3['worst'])} kg of asteroids"),
        ("Vesta", f"Vesta, {S['big_asteroids_closest_au']['vesta']:.3f} AU, nudged with {vesta_minutes:.0f} minutes"),
        ("lowest safety factor", f"lowest structural safety factor is {sf_min:.2f}"),
        ("structures at the cap: cables", f"| Cable safety factor (E2 material, 100 GPa) | "
                                          f"{cap['earth-tow']['cable safety factor']:.2f} | {cap['mars-tow']['cable safety factor']:.2f} |"),
        ("structures at the cap: anchors", f"| {cap['earth-tow']['anchor safety factor']:.2f} | "
                                           f"{cap['mars-tow']['anchor safety factor']:.2f} | at least 1.5 |"),
        ("structures at the cap: mirrors", f"| {cap['earth-tow']['tow mirror temperature']:,.0f} K | "
                                           f"{cap['mars-tow']['tow mirror temperature']:,.0f} K |"),
        ("structures at the cap: asteroid bodies", f"| {cap['earth-tow']['asteroid body safety factor']:.0f} | "
                                                   f"{cap['mars-tow']['asteroid body safety factor']:.0f} |"),
        ("structures at the most power used", f"safety factor of {used['cable safety factor']:.2f} and the mirrors run "
                                              f"at about {round(used['tow mirror temperature'], -1):,.0f} K"),
        ("ledger: integrator honest", f"| {sci(led['integrator_honest_max'])} | {sci(led['integrator_honest_end'])} |"),
        ("ledger: nothing from nothing", f"| {sci(led['nothing_from_nothing_max'])} | {sci(led['nothing_from_nothing_end'])} |"),
        ("ledger in the summary", f"momentum ledger closes to {sci(led['nothing_from_nothing_max'])}"),
        ("applied impulse", f"{sci(led['applied_impulse_kg_m_s'], 3)} kg m/s"),
        ("beam work", f"{sci(led['beam_work_j'], 5)} J of work, and the bodies gained {sci(led['bodies_energy_gain_j'], 5)} J"),
        ("work against energy", f"they match to {led['work_mismatch_share']:.3%}"),
        ("energy gap", f"{sci(led['energy_error_max_of_total'])} of the system's total energy"),
        ("real solar system's energy", f"{sci(base['energy_error'])} over a million years"),
        ("temperature", f"{lo['temperature_k']:.1f} to {hi['temperature_k']:.1f} K"),
        ("liquid water", f"at least {lo['liquid_water_share']:.0%}"),
        ("absorbed sunlight", f"at most {hi['absorbed_w_m2']:.1f} W/m²"),
        ("surface pressure", f"{lo['surface_pressure_kpa']:.1f} kPa"),
        ("Jeans lambda", f"at least {lo['jeans_lambda_n2']:.0f}"),
        ("magnetopause", f"at least {lo['magnetopause_re']:.1f} Earth radii"),
        ("magnetopause grows", f"from {lo['magnetopause_re']:.0f} to {hi['magnetopause_re']:.1f} Earth radii"),
        ("day length", f"about {sci(lod)} s"),
        ("the Moon's Hill share", f"at most {hi['moon_hill_share']:.3f}"),
        ("the Moon grows safer", f"from {hi['moon_hill_share']:.3f} to {lo['moon_hill_share']:.3f}"),
        ("thrust on the Moon", f"at most {hi['thrust_over_moon_pull']:.4f}"),
        ("two hundred years on", f"Earth sits at {S['end']['earth']['a_au']:.3f} AU with an eccentricity of "
                                 f"{S['end']['earth']['eccentricity']:.3f}"),
        ("belt: impacts", f"once every {belt['crossing']['years_per_impact']:,.0f} years while crossing the belt and once "
                          f"every {belt['parked_at_target']['years_per_impact']:,.0f} years parked"),
        ("belt: sample", f"{belt['sample_size']:,} real belt orbits (JPL Small-Body Database) for {belt['years_tracked']:,} "
                         f"years and scaled their {belt['sample_encounters']:,} close passes"),
        ("belt: population", f"{CFG['belt_sample']['real_population_over_1km'] / 1e6:.1f} million asteroids over 1 km"),
        ("belt: nudge", f"found {belt['deflection']['warning_years']} years ahead, it is nudged "
                        f"{belt['deflection']['speed_change_m_s'] * 100:.0f} cm/s aside by a "
                        f"{sci(belt['deflection']['beam_power_w'])} W beam for one day"),
        ("long run: Earth's orbit", f"| {mr['earth']['a'][0]:.3f} to {mr['earth']['a'][1]:.3f} AU | "
                                    f"{br['earth']['a'][0]:.5f} to {br['earth']['a'][1]:.5f} AU |"),
        ("long run: Earth's eccentricity", f"| {mr['earth']['e'][1]:.3f} | {br['earth']['e'][1]:.3f} |"),
        ("long run: axial tilt", f"| {m['axial_tilt_deg'][0]:.1f}° to {m['axial_tilt_deg'][1]:.1f}° | "
                                 f"{base['axial_tilt_deg'][0]:.1f}° to {base['axial_tilt_deg'][1]:.1f}° |"),
        ("long run: Mars's orbit", f"| {mr['mars']['a'][0]:.3f} to {mr['mars']['a'][1]:.3f} AU | "
                                   f"{br['mars']['a'][0]:.4f} to {br['mars']['a'][1]:.4f} AU |"),
        ("long run: orbit gap", f"never comes within {m['earth_mars_orbit_gap_min_au']:.2f} AU"),
        ("long run: flags", f"there were {verdict['flags']['unresolved']} unresolved flags. "
                            f"{['No', 'One', 'Two', 'Three'][len(CHAOS)]} chaos copies"),
        ("long run: big-asteroid passes", f"{nudges['passes']} big-asteroid passes"),
        ("long run: their nudges", f"at most {nudges['longest_beam_hours']:.1f} hours of a "
                                   f"10^{math.log10(nudges['beam_w']):.0f} W beam"),
        ("long run: seasons", f"re-aim {verdict['seasons']['sunlight_to_reaim']:.1%} of Earth's sunlight"),
        ("Octo-Earth: force on the arms", f"({sci(abs(arms['on_arms_n'][2]), 3)} N)"),
        ("Octo-Earth: they cancel", f"cancel to {sci(arms['sum_over_force'])} of each other"),
        ("Octo-Earth: uniform field", f"feel 10^{math.floor(math.log10(outside['closed_circuits_n']))} N against an I L B of "
                                      f"{outside['scale_i_l_b_n']:,.0f} N"),
        ("Octo-Earth: open arms", f"at most {sci(outside['open_arms_in_earth_field_n'], 1)} N"),
        ("Octo-Earth: years", f"about 10^{round(math.log10(outside['years_needed_at_that_push']))} years"),
        ("Octo-Earth: steel base", f"puts {steel['lengths'][-1]['standing_base_stress_pa'] / 1e9:.0f} GPa on its base"),
        ("Octo-Earth: nanotube", f"reaches only a safety factor of {nanotube['lengths'][-1]['standing_sf']:.1f}"),
        ("Octo-Earth: Greenhill", f"buckles (Greenhill's limit) past {nanotube['buckling_length_km']:,.0f} km"),
        ("Octo-Earth: arm length", f"each {longest_arm:,} km long"),
        ("journey run time", f"# the full journey with every check, about an hour"
                             f"{' and a half' if 1.25 < S['run_seconds'] / 3600 < 1.75 else ''}"),
    ]
    facts += [(f"Octo-Earth: {x['name']}", f"| {x['standing_longest_km']:,.0f} km | {x['buckling_length_km']:,.0f} km | "
                                          f"{x['level_longest_km']:,.0f} km |")
              for x in OCTO["materials"] if not x["name"].startswith(("Titanium", "Aluminium", "Aramid"))]
    rows = {"Earth tow, all stations off": "shared E1 budget, all beams off",
            "Earth tow, half the stations off": "shared E1 budget, half the stations off",
            "Earth tow, a quarter off": "shared E1 budget, a quarter off",
            "Mars tow, all stations off": "Mars tow, all beams off",
            "Mars tow during its sprint, all off": "Mars tow in its 4x sprint (200,000 km), all off",
            "Earth tow during Mars's sprint, all off": "Earth tow during Mars's sprint (850,000 km), all off"}
    facts += [(f"outage: {row}", f"| {row} | {days(OUTAGE[name]['longest_safe_outage_days'])} |") for row, name in rows.items()]
    half, quarter = OUTAGE["Mars tow, half the stations off"], OUTAGE["Mars tow, a quarter off"]
    assert half["first_unsafe_days"] is None and quarter["first_unsafe_days"] is None
    facts.append(("outage: Mars tow, half or a quarter off",
                  f"more than {days(max(half['longest_safe_outage_days'], quarter['longest_safe_outage_days']))}"))
    return facts


REPORT_FACTS = report_facts()


@pytest.mark.parametrize("what, expected", REPORT_FACTS, ids=[w for w, _ in REPORT_FACTS])
def test_report_number_matches_results(what, expected):
    assert expected in text("report.md"), f"docs/report.md should say: {expected}"


def test_report_says_what_the_million_year_runs_threw_out():
    """The main run throws nothing out; a chaos copy may lose a big asteroid, and the report must say which."""
    report = text("report.md")
    assert LT["moved"]["thrown_out"] == [] and "Nothing was thrown out" in report
    lost = [x for c in CHAOS for x in c["thrown_out"]]
    assert not {x["body"] for x in lost} & set(PLANET) and "no planet is thrown out" in report
    for x in lost:
        assert f"{x['body'].capitalize()} is thrown out of the solar system after {round(x['year'], -3):,.0f} years" in report
    for body in ("earth", "mars"):  # "the same ranges for Earth and Mars to 0.001 AU"
        for copy in CHAOS:
            assert max(abs(a - b) for a, b in zip(copy["ranges"][body]["a"], LT["moved"]["ranges"][body]["a"])) < 1e-3
    assert "same ranges for Earth and Mars to 0.001 AU" in report


def test_report_benchmark_table_matches_the_benchmarks():
    """The validation table's measured column, from the ten official benchmarks run now (a few seconds). Benchmark
    2 is round-off, which differs between machines, so the report gives it to one figure."""
    from sim.benchmarks import ALL

    r = {n: ALL[n]() for n in ALL}
    assert all(x["ok"] for x in r.values())
    b4 = r[4]["measured"]
    rows = [
        f"| 1 | Wire in a field, I L × B summed over 1,000 pieces | ({', '.join(f'{x:g}' for x in r[1]['measured'])}) N |",
        f"| {sci(r[2]['measured'], 1)} of I L B |",
        f"| {sci(r[3]['measured'], 6)} T |",
        f"back within {sci(b4['position_over_a'])} a; energy {sci(b4['energy'], 3)} |",
        f"energy error {sci(r[5]['measured'])} |",
        f"| {r[6]['measured']:.3f} days |",
        f"| {r[7]['measured'][0]:.3f} and {r[7]['measured'][1]:.3f} km/s; {r[7]['measured'][2]:.1f} days |",
        f"| {r[8]['measured']:,.1f} km | {r[8]['expected']:,.1f} km from Gauss (1%) |",
        f"| {r[10]['measured']:.1f} K |",
    ]
    missing = [row for row in rows if row not in text("report.md")]
    assert not missing, missing


def test_report_pdf_is_current_and_within_the_page_limit():
    """docs/report.pdf is what gets submitted: at most 8 pages, and made from the report as it is now."""
    from pypdf import PdfReader

    from sim.report_pdf import MAX_PAGES, report_hash

    pdf = PdfReader(DOCS / "report.pdf")
    assert len(pdf.pages) <= MAX_PAGES
    made_from = pdf.metadata["/Subject"].split()[-1]
    assert made_from == report_hash(DOCS / "report.md"), \
        "docs/report.pdf is older than docs/report.md: run uv run python -m sim.report_pdf"


# The pitch documents (issue #11): the Q&A sheet, the pitch's talk track and the demo video's voiceover.

def pitch_numbers() -> dict[str, str]:
    """Numbers the Q&A sheet, the pitch and the voiceover quote, written as they write them."""
    ea, led, cl, belt, lt = EARTH["arrival"], S["ledger"], S["climate"], S["belt"], LT["moved"]
    lo = {k: v[0] for k, v in cl.items()}
    hi = {k: v[1] for k, v in cl.items()}
    et = TOW["earth-tow"]
    d, m = et["distance_km"] * 1e3, et["asteroid_mass_kg"]
    m_earth = CFG["habitability"]["earth_mass_with_moon_kg"]
    pull = G * m_earth * m / d ** 2
    accel = G * m / d ** 2
    v_start, v_end = math.sqrt(GM_SUN / AU), math.sqrt(GM_SUN / (ea["a_au"] * AU))
    spiral_years = (v_start - v_end) / (accel * math.cos(math.radians(45))) / YEAR
    tide = (m / d ** 3) / (CFG["moon"]["mass_kg"] / (CFG["moon"]["a_km"] * 1e3) ** 3)
    old_outage = OUTAGE["old: own cap 8.5e25 W, all beams off"]["longest_safe_outage_days"]
    return {
        "pull": f"{sci(pull, 3)} N",
        "acceleration": f"{sci(accel, 3)} m/s²",
        "along the orbit": f"{sci(accel * math.cos(math.radians(45)))} of it along the orbit",
        "Earth's energy": f"{sci(GM_SUN * m_earth / 2 * (1 / AU - 1 / (ea['a_au'] * AU)))} J of orbital energy",
        "spiral": f"{(v_start - v_end) / 1e3:.1f} km/s",
        "spiral years": f"about {round(spiral_years, -3):,.0f} years. The run takes {ea['year']:,.0f}",
        "power to hold": f"about {sci(pull * C_LIGHT / math.sqrt(2))} W",
        "planets' energy": f"{sci(led['bodies_energy_gain_j'])} J of orbital energy over {ea['year']:,.0f} years "
                           f"({sci(led['bodies_energy_gain_j'] / (ea['year'] * YEAR))} W on average)",
        "asteroid": f"{sci(m, 3)} kg",
        "distance": f"{et['distance_km']:,} km",
        "E3 bound": f"{sci(CFG['enablers']['e3_asteroid_limit_kg'], 1)} kg per asteroid",
        "Mars parks": f"{MARS['arrival']['a_au']:.2f} AU in year {MARS['arrival']['year']:,.0f}",
        "arrival": f"{ea['a_au']} AU in year {ea['year']:,.0f}",
        "closest Mars": f"{S['mars_closest']['au']:.2f} AU",
        "beam peak": f"{sci(S['total_beam_max_w'], 3)} W",
        "clearance": f"{CFG['beam']['earth_clearance_km']:,} km",
        "closest beam": f"{EARTH['beam_clearance_min_km']:,.0f} km",
        "spot": f"{EARTH['spot_error_max_km']:,.0f} km ({EARTH['spot_error_max_km'] / et['distance_km']:.1%})",
        "blackout": days(OUTAGE["shared E1 budget, all beams off"]["longest_safe_outage_days"]),
        "half stations": days(OUTAGE["shared E1 budget, half the stations off"]["longest_safe_outage_days"]),
        "old outage": f"{old_outage * 24:.0f}-hour beam outage",
        "new blackout": f"{OUTAGE['shared E1 budget, all beams off']['longest_safe_outage_days'] * 24:.0f}-hour blackout",
        "normal pull caught": f"caught in {CROSSING['normal pull']['caught']} of {CROSSING['normal pull']['of']}",
        "sprint caught": f"caught in {CROSSING['chosen: sprint 4x with the asteroid at 400,000 km (to 200,000 km)']['caught']} of 8",
        "mirror temperature": f"{structures('earth-tow', et['max_beam_w'])['tow mirror temperature']:,.0f} K",
        "temperature": f"{lo['temperature_k']:.1f} and {hi['temperature_k']:.1f} K",
        "sunlight": f"{lo['sunlight_share']:.3f} and {hi['sunlight_share']:.3f}",
        "mirror area": f"{sci(hi['mirror_area_km2'])} km²",
        "liquid water": f"at least {lo['liquid_water_share']:.0%}",
        "Moon start and end": f"{hi['moon_hill_share']:.3f} of Earth's Hill radius at the start and {lo['moon_hill_share']:.3f}",
        "Moon at most": f"at most {hi['moon_hill_share']:.3f}",
        "thrust on the Moon": f"at most {hi['thrust_over_moon_pull']:.4f}",
        "day length": f"about {sci(day_length_rate(m, d) * ea['year'] * YEAR)} s",
        "tide": f"{tide:.2%} of the Moon's",
        "tilt": f"{lt['axial_tilt_deg'][0]:.1f} to {lt['axial_tilt_deg'][1]:.1f} degrees",
        "real tilt": f"(today {LT['baseline']['axial_tilt_deg'][0]:.1f} to {LT['baseline']['axial_tilt_deg'][1]:.1f})",
        "re-aim": f"{LT['verdict']['seasons']['sunlight_to_reaim']:.1%} of Earth's sunlight",
        "crossing impacts": f"once every {belt['crossing']['years_per_impact']:,.0f} years",
        "parked impacts": f"once every {belt['parked_at_target']['years_per_impact']:,.0f} years",
        "nudge": f"{belt['deflection']['speed_change_m_s'] * 100:.0f} cm/s",
        "nudge beam": f"{sci(belt['deflection']['beam_power_w'])} W beam for a day",
        "belt sample": f"{belt['sample_size']:,} real belt orbits",
        "Vesta": f"Vesta comes closest ({S['big_asteroids_closest_au']['vesta']:.3f} AU)",
        "Vesta's nudge": f"{max(n['beam_hours'] for n in S['big_asteroid_nudges']) * 60:.0f} minutes of beam",
        "lowest safety factor": f"at least {min(v for t in TOW for k, v in structures(t, TOW[t]['max_beam_w']).items() if 'safety factor' in k):.2f}",
        "asteroid body": f"safety factor of {structures('earth-tow', et['max_beam_w'])['asteroid body safety factor']:.0f}",
        "ledger checks": f"{sci(led['integrator_honest_max'])} and {sci(led['nothing_from_nothing_max'])}",
        "ledger": sci(led["nothing_from_nothing_max"]),
        "work against energy": f"{led['work_mismatch_share']:.3%}",
        "Octo-Earth cancels": f"cancel to {sci(OCTO['net_force_all_arms']['sum_over_force'])}",
        "Octo-Earth arms": f"{OCTO['materials'][0]['buckling_length_km']:,.0f} km in steel and "
                           f"{next(x for x in OCTO['materials'] if x['name'].startswith('Carbon'))['buckling_length_km']:,.0f} km in ideal nanotube",
        "long run Earth": f"{lt['ranges']['earth']['a'][0]:.3f} and {lt['ranges']['earth']['a'][1]:.3f} AU",
        "journey run time": "about an hour and a half" if 1.25 < S["run_seconds"] / 3600 < 1.75 else "(re-time the run)",
    }


QA = ["pull", "spot", "blackout", "half stations", "asteroid", "E3 bound", "Mars parks", "normal pull caught",
      "sprint caught", "closest Mars", "distance", "beam peak", "power to hold", "planets' energy", "mirror temperature",
      "clearance", "closest beam", "temperature", "mirror area", "sunlight", "Moon start and end", "thrust on the Moon",
      "day length", "tide", "tilt", "real tilt", "re-aim", "crossing impacts", "parked impacts", "nudge", "belt sample",
      "nudge beam", "Vesta", "Vesta's nudge", "lowest safety factor", "asteroid body", "ledger checks",
      "work against energy", "Octo-Earth cancels", "Octo-Earth arms", "journey run time"]
PITCH = ["asteroid", "distance", "Earth's energy", "spiral", "pull", "acceleration", "along the orbit", "spiral years",
         "power to hold", "beam peak", "clearance", "ledger", "Mars parks", "arrival", "sunlight", "temperature",
         "liquid water", "Moon at most", "thrust on the Moon", "day length", "long run Earth", "crossing impacts",
         "re-aim", "Octo-Earth cancels", "normal pull caught", "sprint caught", "old outage", "new blackout"]
VIDEO = ["distance", "clearance", "Mars parks", "arrival", "long run Earth"]
NUMBERS = pitch_numbers()


@pytest.mark.parametrize("doc, what", [("qa.md", w) for w in QA] + [("pitch.md", w) for w in PITCH]
                         + [("video-script.md", w) for w in VIDEO])
def test_pitch_document_number_matches_results(doc, what):
    assert NUMBERS[what] in text(doc), f"docs/{doc} should say: {NUMBERS[what]}"


def test_qa_sheet_has_twenty_questions_each_with_a_one_line_answer_and_who_answers():
    """Issue #11: 20 likely questions, one-line answers, who answers each; every member answers some."""
    lines = (DOCS / "qa.md").read_text(encoding="utf-8").splitlines()
    heads = [(i, m) for i, line in enumerate(lines)
             if (m := re.fullmatch(r"\*\*(\d+)\. (.+\?)\*\* \*\((Ashish|Member [2-5])\)\*", line))]
    assert len(heads) >= 20
    assert [int(m.group(1)) for _, m in heads] == list(range(1, len(heads) + 1))
    assert {m.group(3) for _, m in heads} == {"Ashish", "Member 2", "Member 3", "Member 4", "Member 5"}
    for (i, m), (j, _) in zip(heads, heads[1:] + [(len(lines), None)]):
        block = lines[i + 1:j]
        more = next(k for k, line in enumerate(block) if line.startswith("More: "))
        answer = " ".join(block[:more])
        assert answer and len(answer) <= 200 and answer.count(". ") == 0, f"question {m.group(1)}: {answer}"


def test_pitch_parts_fill_seven_minutes_and_fit_their_time():
    """The guide's five parts, 7 minutes in all; each part's words fit at 150 a minute, leaving room to click."""
    from sim.voiceover import spoken_words

    doc = (DOCS / "pitch.md").read_text(encoding="utf-8")
    parts = re.split(r"^## (\d)\. .+ \((\d+):(\d\d), (Ashish|Member [2-5])\)$", doc, flags=re.M)[1:]
    seconds = []
    for number, minutes, secs, who, body in zip(*[iter(parts)] * 5):
        said = " ".join(re.findall(r"^> (.*)$", body, flags=re.M) + re.findall(r"^\| [^|]+ \| ([^|]+) \|$", body, flags=re.M)[1:])
        seconds.append(60 * int(minutes) + int(secs))
        assert said, f"part {number} has nothing to say"
        assert spoken_words(said) <= 150 * seconds[-1] / 60, f"part {number}: {spoken_words(said)} words"
    assert len(seconds) == 5 and sum(seconds) == 7 * 60


def test_voiceover_fits_each_shot_and_the_captions_are_current():
    from sim.voiceover import CAPTIONS, MAX_SECONDS, WORDS_PER_MINUTE, captions, shots, video_seconds

    measured = video_seconds()
    all_shots = shots(video_seconds=measured)
    assert all_shots[0]["start"] == 0 and all_shots[-1]["end"] <= MAX_SECONDS
    if measured is not None:  # the script's stated length is the video's
        assert shots()[-1]["end"] == pytest.approx(measured, abs=0.5)
    slow = [(s["shot"], round(s["words_per_minute"])) for s in all_shots if s["words_per_minute"] > WORDS_PER_MINUTE]
    assert not slow, f"voiceover too long for its shot: {slow}"
    assert CAPTIONS.read_text(encoding="utf-8") == captions(all_shots), "run: uv run python -m sim.voiceover"


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="needs ffmpeg")
def test_adding_a_voice_keeps_the_video_and_adds_sound_and_captions(tmp_path):
    from sim.voiceover import VIDEO, add_voice, video_seconds

    voice = tmp_path / "voice.wav"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-f", "lavfi", "-i", "sine=frequency=220:duration=3", str(voice)],
                   check=True)
    out = add_voice(voice, out=tmp_path / "voiced.mp4")
    probe = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type", "-of", "csv=p=0", str(out)],
                           check=True, capture_output=True, text=True).stdout.split()
    assert probe == ["video", "audio", "subtitle"]
    assert video_seconds(out) == pytest.approx(video_seconds(VIDEO), abs=0.1)
