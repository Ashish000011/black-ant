"""Runs every check we have and writes one results PDF, out/verify/black-ant-verification.pdf:

1. the ten official benchmarks (participant guide, section 6);
2. the test suite (pytest: the benchmarks with changed inputs, our checks X1 to X9, safety, structures, the studies);
3. a fresh run of the engine, checked against the official run: the same orbits, the momentum ledger closed,
   every Earth-safety threshold held;
4. the Moon test: the Moon stays with Earth at the start, middle and end of the journey;
5. to 7. the Octo-Earth audit and the small-asteroid and sunlight-optics studies, re-run and compared with results/;
8. the six winning conditions, read from the final run in results/.

    uv run python scripts/verify.py               # about 4 minutes
    uv run python scripts/verify.py --full        # also the slow tests
    uv run python scripts/verify.py --years 500   # a longer fresh engine run (default 200 years, about 90 s)
"""

import argparse
import datetime
import html
import json
import os
import pathlib
import platform
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

from browser import print_pdf

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
OUT = ROOT / "out" / "verify"
PDF = OUT / "black-ant-verification.pdf"
RESULTS = ROOT / "results"


class Section:
    def __init__(self, title: str, what: str):
        self.title, self.what = title, what
        self.ok, self.seconds, self.summary, self.body = False, 0.0, "", ""


def py(*args: str) -> tuple[int, str, float]:
    """Runs `python <args>` in the project folder: exit code, its output, seconds."""
    t0 = time.time()
    p = subprocess.run([sys.executable, *args], cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    return p.returncode, p.stdout + p.stderr, time.time() - t0


def short(v) -> str:
    if isinstance(v, bool):
        return str(v)
    if isinstance(v, float):
        return f"{v:.6g}"
    if isinstance(v, list):
        return "[" + ", ".join(short(x) for x in v) + "]"
    if isinstance(v, dict):
        return ", ".join(f"{k} {short(x)}" for k, x in v.items())
    return str(v)


def chip(ok: bool) -> str:
    return '<span class="pass">PASS</span>' if ok else '<span class="fail">FAIL</span>'


def table(head: list[str], rows: list[list]) -> str:
    th = "".join(f"<th>{html.escape(h)}</th>" for h in head)
    tr = "".join("<tr>" + "".join(f"<td>{c if isinstance(c, str) and c.startswith('<span') else html.escape(str(c))}</td>"
                                  for c in r) + "</tr>" for r in rows)
    return f"<table><tr>{th}</tr>{tr}</table>"


def log_tail(text: str, n: int = 12) -> str:
    lines = [ln.replace(str(ROOT), ".") for ln in text.strip().splitlines() if ln.strip()][-n:]
    return f"<pre>{html.escape(chr(10).join(lines))}</pre>"


def is_num(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def biggest(v) -> float:
    """The largest size of a number or a list of numbers (0 for anything else)."""
    if is_num(v):
        return abs(v)
    return max((abs(x) for x in v if is_num(x)), default=0.0) if isinstance(v, list) else 0.0


def deep_compare(a, b, path: str = "", scale: float = 0.0) -> tuple[int, list[str]]:
    """Numbers agree to 1e-9 of the largest quantity of the same unit beside them (a vector's components against
    the vector, `sum_n` against `on_arms_n`), so rounding left over when big forces cancel is not a difference;
    everything else must match exactly. Returns (numbers compared, differences)."""
    if isinstance(a, dict) and isinstance(b, dict):
        unit = lambda k: k.rsplit("_", 1)[-1]
        sizes: dict[str, float] = {}
        for k, v in b.items():
            sizes[unit(k)] = max(sizes.get(unit(k), 0.0), biggest(v))
        n, diffs = 0, [f"{path}.{k}: only in one" for k in set(a) ^ set(b)]
        for k in set(a) & set(b):
            m, d = deep_compare(a[k], b[k], f"{path}.{k}", sizes[unit(k)])
            n, diffs = n + m, diffs + d
        return n, diffs
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            return 0, [f"{path}: {len(a)} items against {len(b)}"]
        n, diffs = 0, []
        for i, (x, y) in enumerate(zip(a, b)):
            m, d = deep_compare(x, y, f"{path}[{i}]", max(scale, biggest(b)))
            n, diffs = n + m, diffs + d
        return n, diffs
    if is_num(a) and is_num(b):
        same = a == b or abs(a - b) <= max(1e-12, 1e-9 * max(abs(a), abs(b), scale))
        return 1, [] if same else [f"{path}: {a!r} against {b!r}"]
    return 0, [] if a == b else [f"{path}: {a!r} against {b!r}"]


def safety_rows(climate: dict, safety: dict) -> list[tuple[str, str, str, bool]]:
    """The ten Earth-safety thresholds against a run's worst values: (threshold, worst, limit, held)."""
    lo, hi = lambda k: climate[k][0], lambda k: climate[k][1]
    t = climate["temperature_k"]
    return [
        ("Global mean temperature", f"{t[0]:.1f} to {t[1]:.1f} K", f"{safety['temperature_min_k']} to {safety['temperature_max_k']} K",
         safety["temperature_min_k"] <= t[0] and t[1] <= safety["temperature_max_k"]),
        ("Surface with liquid water", f"at least {lo('liquid_water_share'):.1%}", f"at least {safety['liquid_water_min_share']:.0%}",
         lo("liquid_water_share") >= safety["liquid_water_min_share"]),
        ("Absorbed sunlight (runaway greenhouse)", f"at most {hi('absorbed_w_m2'):.1f} W/m2", f"under {safety['runaway_absorbed_max_w_m2']} W/m2",
         hi("absorbed_w_m2") < safety["runaway_absorbed_max_w_m2"]),
        ("Surface pressure", f"at least {lo('surface_pressure_kpa'):.1f} kPa", f"at least {safety['surface_pressure_min_kpa']} kPa",
         lo("surface_pressure_kpa") >= safety["surface_pressure_min_kpa"]),
        ("Nitrogen kept (Jeans lambda)", f"at least {lo('jeans_lambda_n2'):.0f}", f"over {safety['jeans_lambda_min']}",
         lo("jeans_lambda_n2") > safety["jeans_lambda_min"]),
        ("Magnetopause distance", f"at least {lo('magnetopause_re'):.1f} Earth radii", f"at least {safety['magnetopause_min_re']}",
         lo("magnetopause_re") >= safety["magnetopause_min_re"]),
        ("Change in length of day", f"{hi('day_length_change_s'):.2g} s", f"at most {safety['day_length_change_max_s']} s",
         hi("day_length_change_s") <= safety["day_length_change_max_s"]),
        ("Moon over Earth's Hill radius", f"at most {hi('moon_hill_share'):.3f}", f"under {safety['moon_hill_max_share']}",
         hi("moon_hill_share") < safety["moon_hill_max_share"]),
        ("Tow thrust over Earth's pull on the Moon", f"at most {hi('thrust_over_moon_pull'):.4f}", f"under {safety['thrust_over_moon_pull_max']}",
         hi("thrust_over_moon_pull") < safety["thrust_over_moon_pull_max"]),
    ]


def benchmarks(_args) -> Section:
    from sim.benchmarks import ALL
    s = Section("Official benchmarks", "The ten benchmarks of the participant guide (section 6), each against its expected value and tolerance.")
    rows, oks = [], []
    for n, fn in ALL.items():
        r = fn()
        oks.append(r["ok"])
        rows.append([n, r["name"], short(r["measured"]), short(r["expected"]), r["tolerance"], chip(r["ok"])])
    s.ok, s.summary = all(oks), f"{sum(oks)} of {len(oks)} pass"
    s.body = table(["#", "Benchmark", "Measured", "Expected", "Tolerance", ""], rows)
    return s


def tests(args) -> Section:
    s = Section("Test suite", "pytest: the official benchmarks also with changed inputs, our checks X1 to X9, the safety and "
                "structure checks, and the studies' own tests." + ("" if args.full else " Slow tests left out (add --full)."))
    junit = OUT / "junit.xml"
    code, out, _ = py("-m", "pytest", "-q", "-p", "no:cacheprovider", f"--junitxml={junit}", *([] if args.full else ["-m", "not slow"]))
    root = ET.parse(junit).getroot()
    cases = list(root.iter("testcase"))
    files: dict[str, list] = {}
    failures = []
    for c in cases:
        f = c.get("classname", "").split(".")[1] if "." in c.get("classname", "") else c.get("classname", "")
        state = "failed" if c.find("failure") is not None or c.find("error") is not None else "skipped" if c.find("skipped") is not None else "passed"
        files.setdefault(f, []).append((state, float(c.get("time", 0))))
        if state == "failed":
            el = c.find("failure") if c.find("failure") is not None else c.find("error")
            failures.append([f"{f}::{c.get('name')}", (el.get("message") or "")[:200]])
    count = lambda st: sum(1 for v in files.values() for x in v if x[0] == st)
    s.ok = code == 0 and count("failed") == 0 and len(cases) > 0
    s.summary = f"{count('passed')} passed, {count('failed')} failed" + (f", {count('skipped')} skipped" if count("skipped") else "")
    rows = [[f, sum(1 for x in v if x[0] == "passed"), sum(1 for x in v if x[0] == "failed"), f"{sum(x[1] for x in v):.1f} s"]
            for f, v in sorted(files.items())]
    s.body = table(["Test file", "Passed", "Failed", "Time"], rows)
    if failures:
        s.body += "<h3>Failures</h3>" + table(["Test", "Message"], failures)
    return s


def engine(args) -> Section:
    from sim.config import load_config
    s = Section("Engine: a fresh run", f"The journey engine run again from J2000 for {args.years:g} years (without the belt's test "
                "asteroids, which are massless and move nothing), checked against the official run in results/.")
    out = OUT / "journey"
    code, log, _ = py("-m", "sim.scenarios.tow", "--no-belt", "--years", f"{args.years:g}", "--out", str(out))
    if code:
        s.summary, s.body = "the run failed", log_tail(log, 30)
        return s
    summ = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    fresh = json.loads((out / "run.json").read_text(encoding="utf-8"))["frames"][-1]
    official = min(json.loads((RESULTS / "run.json").read_text(encoding="utf-8"))["frames"], key=lambda f: abs(f["t"] - fresh["t"]))
    led, cfg = summ["ledger"], load_config()
    d_pos = max(abs(a - b) for body in ("earth", "mars", "jupiter") for a, b in zip(fresh["pos"][body], official["pos"][body]))
    unresolved = [f["check"] for f in summ["flags"]["flags"] if f["covered_by"] is None and not f["check"].startswith("Earth reaches")]
    same = "identical" if d_pos == 0 else f"within {d_pos:.1e} AU"
    checks = [
        ("Same orbits as the official run", f"year {fresh['t']:g}: Earth {fresh['earth_orbit_au']} AU (official {official['earth_orbit_au']}); "
         f"positions of Earth, Mars, Jupiter {same}", "within 1e-5 AU (the saved rounding)", official["t"] == fresh["t"] and d_pos <= 1e-5),
        ("Integrator is honest: bodies' momentum change against the applied impulse", f"{led['integrator_honest_max']:.1e}", "under 1e-9",
         led["integrator_honest_max"] <= 1e-9),
        ("Nothing from nothing: applied impulse plus its partners", f"{led['nothing_from_nothing_max']:.1e}", "under 1e-9",
         led["nothing_from_nothing_max"] <= 1e-9),
        ("Energy kept", f"worst gap {led['energy_error_max_of_total']:.1e} of the total", "reported", True),
        ("Unresolved flags (besides arrival, not reached in a short run)", f"{len(unresolved)}", "0", not unresolved),
    ]
    rows = [[n, v, lim, chip(ok)] for n, v, lim, ok in checks]
    rows += [[n, v, lim, chip(ok)] for n, v, lim, ok in safety_rows(summ["climate"], cfg["safety"])]
    s.ok = all(r[3] == chip(True) for r in rows)
    s.summary = f"same orbits as the official run ({same}); ledger {led['nothing_from_nothing_max']:.1e}; all safety thresholds held"
    s.body = table(["Check", "Fresh run", "Limit", ""], rows) + log_tail(log, 4)
    return s


def moon(_args) -> Section:
    s = Section("Moon test", "The Moon followed around Earth for 50 years at the start, middle and end of the journey, with and "
                "without the tow asteroid: does it stay bound?")
    code, log, _ = py("-m", "sim.scenarios.moon")
    data = json.loads((ROOT / "out" / "moon_runs_x1.json").read_text(encoding="utf-8"))
    rows = []
    for name, e in data["epochs"].items():
        w, b = e["with_asteroid"], e["without_asteroid"]
        rows.append([name, e["journey_year"], f"{e['earth_au']:.3f} AU", f"{b['closest_km']:,.0f} to {b['farthest_km']:,.0f} km",
                     f"{w['closest_km']:,.0f} to {w['farthest_km']:,.0f} km", f"{e['distance_change']:.3%}", chip(e["ok"])])
    s.ok = code == 0 and all(e["ok"] for e in data["epochs"].values())
    s.summary = "the Moon stays: distance changes " + ", ".join(f"{e['distance_change']:.3%}" for e in data["epochs"].values())
    s.body = table(["When", "Year", "Earth", "Moon without the asteroid", "With it", "Change", ""], rows)
    return s


def rerun(title: str, what: str, module: str, saved: str) -> Section:
    s = Section(title, what)
    target = OUT / saved
    code, log, _ = py("-m", module, "--out", str(target))
    if code:
        s.summary, s.body = "the run failed", log_tail(log, 30)
        return s
    n, diffs = deep_compare(json.loads(target.read_text(encoding="utf-8")), json.loads((RESULTS / saved).read_text(encoding="utf-8")))
    s.ok = not diffs and n > 0
    s.summary = f"reproduces results/{saved}: {n:,} numbers compared, {len(diffs)} differ"
    s.body = log_tail(log, 10) + (table(["Differences (first 20)"], [[d] for d in diffs[:20]]) if diffs else "")
    return s


def octo(_args) -> Section:
    return rerun("Octo-Earth audit", "The reference concept audited: the arms' push cancels against Earth's core, and the arms "
                 "cannot hold themselves up. Re-run and compared with the saved result.", "sim.scenarios.octo", "octo_earth.json")


def small(_args) -> Section:
    return rerun("Small-asteroid study", "Rocks under 1 km at 2.7 AU, the infrared survey, E1's answer, wear, the Moons and the "
                 "Kirkwood gaps. Re-run and compared with the saved result.", "sim.scenarios.small_asteroids", "small_asteroids.json")


def optics(_args) -> Section:
    return rerun("Sunlight-optics study", "Where the sunlight optics sit, the L1 refracting ring against E3, the tow mirror seen "
                 "from Earth, and the tow mirrors' protection. Re-run and compared with the saved result.", "sim.scenarios.mirrors", "mirrors.json")


def winning(_args, bench: Section) -> Section:
    from sim.config import load_config
    from sim.viewer_data import structures
    s = Section("The six winning conditions", "Read from the final run in results/ (Earth to 2.7 AU with every check, 8,758 years).")
    cfg, summ = load_config(), json.loads((RESULTS / "summary.json").read_text(encoding="utf-8"))
    arr, years = summ["tows"]["earth-tow"]["arrival"], summ["settings"]["years"]
    safety = safety_rows(summ["climate"], cfg["safety"])
    struct = [c for c in structures(cfg, summ) if c["case"] == "power cap"]
    sf = min(c["value"] for c in struct if "safety factor" in c["check"])
    led = summ["ledger"]
    unresolved = [f for f in summ["flags"]["flags"] if f["covered_by"] is None]
    rows = [
        ["Earth reaches its target orbit within 10,000 years", f"year {arr['year']:,} at {arr['a_au']} AU",
         f"{cfg['arrival']['target_au']} AU by year {years:,}", arr["year"] <= years and arr["a_au"] >= cfg["arrival"]["target_au"]],
        ["Every Earth-safety threshold holds for the whole run", f"{sum(r[3] for r in safety)} of {len(safety)} checks held "
         "(ten thresholds: temperature has two)", "all", all(r[3] for r in safety)],
        ["Every structural safety factor at least 1.5", f"lowest {sf:.2f} at the power cap; tow mirrors at most "
         f"{max(c['value'] for c in struct if 'temperature' in c['check']):,.0f} K", "1.5; 1,500 K", all(c["ok"] for c in struct)],
        ["Every applicable benchmark passes", bench.summary, "10 of 10", bench.ok],
        ["Every force booked; energy and momentum conserved", f"ledger {led['nothing_from_nothing_max']:.1e} and "
         f"{led['integrator_honest_max']:.1e}; beam work matches energy gained to {led['work_mismatch_share']:.3%}", "under 1e-9",
         led["nothing_from_nothing_max"] <= 1e-9 and led["integrator_honest_max"] <= 1e-9],
        ["No unresolved flags", f"{len(unresolved)} unresolved; {len(summ['flags']['flags']) - len(unresolved)} covered by E1 to E3",
         "0 unresolved", not unresolved],
    ]
    s.ok = all(r[3] for r in rows)
    s.summary = f"{sum(r[3] for r in rows)} of 6 hold"
    s.body = (table(["Condition", "Final run", "Required", ""], [[*r[:3], chip(r[3])] for r in rows])
              + "<h3>The ten Earth-safety thresholds, worst over the journey</h3>"
              + table(["Threshold", "Worst", "Limit", ""], [[*r[:3], chip(r[3])] for r in safety]))
    return s


def git_version() -> str:
    try:
        rev = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
        dirty = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
        return f"{rev}{' with local changes' if dirty else ''}" if rev else "not a git checkout"
    except OSError:
        return "git not found"


def bars(sections: list[Section]) -> str:
    """Seconds per section, as a bar chart."""
    w, row = 480, 18
    top = max(s.seconds for s in sections) or 1
    items = "".join(
        f'<text x="0" y="{i * row + 12}" font-size="9">{html.escape(s.title)}</text>'
        f'<rect x="170" y="{i * row + 3}" width="{max(1, (w - 230) * s.seconds / top):.1f}" height="11" fill="{"#2f9e5b" if s.ok else "#d0453b"}"/>'
        f'<text x="{176 + (w - 230) * s.seconds / top:.1f}" y="{i * row + 12}" font-size="9">{s.seconds:.0f} s</text>'
        for i, s in enumerate(sections))
    return f'<svg width="{w}" height="{len(sections) * row + 4}" font-family="Segoe UI, Arial">{items}</svg>'


CSS = """@page{size:A4;margin:14mm 14mm}body{font:9.5pt/1.4 'Segoe UI',Arial,sans-serif;color:#111}
h1{font-size:18pt;margin:0}h2{font-size:12pt;margin:14pt 0 3pt;border-bottom:1px solid #ccc;padding-bottom:2pt}h3{font-size:10pt;margin:8pt 0 3pt}
.meta{color:#555;margin:2pt 0 8pt}.verdict{font-size:14pt;font-weight:700;padding:6pt 10pt;border-radius:5pt;margin:6pt 0;display:inline-block}
.ok{background:#e3f3e8;color:#17663a}.bad{background:#fbe5e3;color:#a12a20}
table{border-collapse:collapse;width:100%;margin:4pt 0;font-size:8.5pt}td,th{border:1px solid #ccc;padding:2pt 4pt;text-align:left;vertical-align:top}
th{background:#f2f2f2}.pass{color:#17663a;font-weight:700}.fail{color:#a12a20;font-weight:700}
pre{background:#f6f6f6;font-size:7.5pt;padding:4pt;white-space:pre-wrap;margin:4pt 0}.what{color:#444;margin:2pt 0 4pt}
section{break-inside:avoid-page}"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Run every check and write the verification PDF.")
    parser.add_argument("--full", action="store_true", help="also run the slow tests")
    parser.add_argument("--years", type=float, default=200, help="length of the fresh engine run (default 200 years)")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    started = time.time()
    steps = [benchmarks, tests, engine, moon, octo, small, optics]
    sections: list[Section] = []
    for i, step in enumerate(steps + [None], 1):
        name = step.__name__ if step else "winning"
        print(f"[{i}/{len(steps) + 1}] {name} ...", flush=True)
        t0 = time.time()
        try:
            sec = step(args) if step else winning(args, sections[0])
        except Exception as e:  # a crashed step is a failed step, and the report still gets written
            sec = Section(name, "This step stopped with an error.")
            sec.summary, sec.body = f"error: {e}", f"<pre>{html.escape(repr(e))}</pre>"
        sec.seconds = time.time() - t0
        sections.append(sec)
        print(f"      {'PASS' if sec.ok else 'FAIL'}  {sec.summary}  ({sec.seconds:.0f} s)", flush=True)
    ok = all(s.ok for s in sections)
    stamp = datetime.datetime.now().strftime("%d %B %Y, %H:%M")
    head = (f"<h1>Black Ant: verification report</h1><div class='meta'>{stamp} · code {html.escape(git_version())} · Python "
            f"{platform.python_version()} on {html.escape(platform.system())} · {time.time() - started:.0f} s in all</div>"
            f"<div class='verdict {'ok' if ok else 'bad'}'>{'Everything passes' if ok else 'Something failed: see below'}</div>")
    summary = table(["", "What it checks", "Result", "Time"], [[f"{s.title} {chip(s.ok)}", s.what, s.summary, f"{s.seconds:.0f} s"]
                                                              for s in sections])
    summary = summary.replace("&lt;span class=&quot;pass&quot;&gt;PASS&lt;/span&gt;", chip(True)).replace(
        "&lt;span class=&quot;fail&quot;&gt;FAIL&lt;/span&gt;", chip(False))
    body = "".join(f"<section><h2>{i}. {html.escape(s.title)} {chip(s.ok)}</h2><p class='what'>{html.escape(s.what)}</p>"
                   f"<p><b>{html.escape(s.summary)}</b></p>{s.body}</section>" for i, s in enumerate(sections, 1))
    page = OUT / "verification.html"
    page.write_text(f"<!doctype html><meta charset=utf-8><title>Black Ant verification</title><style>{CSS}</style>"
                    f"{head}<h2>Summary</h2>{summary}{bars(sections)}{body}", encoding="utf-8")
    (OUT / "verification.json").write_text(json.dumps({"ok": ok, "when": stamp, "code": git_version(), "sections": [
        {"title": s.title, "ok": s.ok, "summary": s.summary, "seconds": round(s.seconds, 1)} for s in sections]}, indent=1), encoding="utf-8")
    print_pdf(page, PDF)
    print(f"\n{'Everything passes' if ok else 'Something FAILED'}. Results: {PDF.relative_to(ROOT)}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
