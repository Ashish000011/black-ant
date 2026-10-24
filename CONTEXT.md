# CONTEXT.md: the project in one file, for AI models and new teammates

**Read this first, every prompt.** It replaces re-reading the chat history. After finishing any task, update the
sections it touches (Status, Decisions, Active work) and add one line to the Log at the bottom. Keep entries short:
what changed, where, and what is left. Numbers here are copied from `results/` and `config.yaml`; if they differ,
those files win.

---

## 1. What this project is

**Black Ant**: a hackathon entry for Black Ant Robotics at TransfiNITTe 2026 (Planetary Propulsion Hackathon,
24 to 26 October 2026; mid-point check-in 24 Oct, final 26 Oct). The brief: simulate a machine that moves Earth from
1 AU to about 2.7 AU without harming the planet or life on it.

**Our concept:** a *gravity tractor held by light*. A 3.97e20 kg asteroid sits 637,100 km from Earth, 45 degrees
between "ahead" and "away from the Sun". Its gravity pulls Earth (3.95e17 N; 2.8e17 N along the orbit) and a beam of
focused light on a mirror tied to the asteroid holds it in place. Mars is towed first, to 3.64 AU, by a second tow.
Sunlight mirrors (E3) keep Earth at today's sunlight and 288 K. On the last stretch (from 2.0 AU) the tow steers
Earth onto the orbit shape and plane Jupiter forces at 2.7 AU (the "arrival trim").

**Why not the brief's Octo-Earth:** forces between arms and Earth are internal (net 3.7e-12 of each force), and a
12,000 km arm buckles past 471 km (steel) or 1,444 km (nanotube). Audited in `sim/scenarios/octo.py`, test X8.

- Repo: `github.com/Ashish000011/black-ant`. Nobody pushes to `main`: branch, PR, Ashish reviews and merges.
- Team roles (GitHub issue labels): member-1 physics, member-2 safety, member-3 structures and enablers,
  member-4 3D viewer, member-5 validation and pitch.
- Two local clones exist (`~/Desktop/pipelin-two/black-ant` and `~/Desktop/madhukarverma/black-ant`), same remote.
  Work goes in **pipelin-two** (decided 25 Oct).

## 2. The six winning conditions and where we stand (final run, 24 Oct)

| Condition | Result |
| --- | --- |
| Earth reaches target within 10,000 years | Year 8,758 at 2.7006 AU, e 0.0331, tilt 1.294 deg |
| Earth stays safe (ten thresholds from the company's reference demo) | All ten hold: 287.8 to 288.8 K, liquid water at least 82%, etc. |
| Structures at safety factor 1.5 or more | Lowest 1.57 |
| Benchmarks pass | All ten official ones; extra checks X1 to X9 |
| Every force booked; energy and momentum conserved | Ledger closes to 5.6e-16 (limit 1e-9); beam work matches energy gained to 0.007% |
| No unresolved flags | 0 unresolved; 6 covered by enablers E1 to E3 |

Also: Mars parks year 5,168 at 3.6408 AU; closest Earth-Mars pass 0.373 AU; most beam power 9.27e25 W (E1 cap 1e26);
mirrors up to 8.5e8 km2 (E3 cap 1e9). A million years after arrival: Earth 2.698 to 2.702 AU, nothing thrown out.

## 3. Enablers (frozen since the mid-point check-in: **no new ones, no changes**)

| | Provides | Bound |
| --- | --- | --- |
| E1 | Focused light for both tows; nudges dangerous asteroids | 1e26 W total; many independent stations |
| E2 | Super-mirror material for tow mirrors and cables | 100 GPa, absorbs 1e-7, 2,000 kg/m3, 1,500 K |
| E3 | Places the two asteroids; builds tow mirrors and **sunlight mirrors** | Asteroids 4e20 kg each; mirrors 1e9 km2 total |

Anything new (e.g. Moon reflectors) must fit inside an existing bound. Moon reflectors count against E3's 1e9 km2.

## 4. Map of the code

| Path | Holds |
| --- | --- |
| `config.yaml` | Every setting and limit, with sources. **Numbers live here only.** |
| `sim/` | Python model (uv, Python 3.12, numpy, rebound, pyyaml). `integrator.py` gravity and steppers; `forces.py` tow and beam; `ledger.py` momentum; `habitability.py` sunlight, mirrors, climate; `night.py` moonlight and Moon reflectors; `checks/` safety and structures every 100 days; `scenarios/` journey (`tow.py`), moon, longterm, parking, outage, crossing, octo; `viewer_data.py` turns `results/` into `viewer/public/data/` |
| `results/` | The final run's outputs. `run.json` has one frame per 10 years with positions of **only Earth, Mars, Jupiter and the Earth tow asteroid** |
| `viewer/` | 3D test bench (Vite 6, Three.js 0.170, plain JS). **Replays saved runs; the official numbers are not computed in the browser.** Published to GitHub Pages from `main` (`.github/workflows/pages.yml`). `src/main.js` wiring and keys; `src/scene.js` 3D views incl. top view, `noStage` fallback without WebGL; `src/studio.js` Blender-style panels (Scene tab, Model, Data); `src/estimates.js` live what-if maths (ports of habitability.py + night.py + tow spiral); `src/bodies.js` positions of every body (run or Kepler); `src/panels.js` the nine results tabs; `src/data.js` loading and interpolation |
| `viewer/scripts/video.mjs` | Renders the demo video through `?capture` mode and `window.bench` (run, view, tab, time, scale, orbit, caption, frame). **Keep that API working.** |
| `docs/` | problem, approach, enablers, report (technical report), status, risk register, qa, rules, video script, momentum record |
| `tests/` | Official benchmarks, extra checks, safety and structure checks, Moon, night |

Commands:

```bash
uv sync                                   # set up
uv run python -m sim.benchmarks           # ten official benchmarks, ~12 s
uv run pytest -m "not slow" -v            # quick tests (run on every PR)
uv run python -m sim.scenarios.tow --out results   # full journey, about 1.5 hours
uv run python -m sim.viewer_data          # results/ -> viewer/public/data/
cd viewer && npm ci && npm run dev        # test bench locally
```

## 5. Deliverables (guide section 9)

| Deliverable | Status |
| --- | --- |
| Source code with README | Done |
| Runnable simulation + 3D test bench | Done; GUI being redesigned (see 7) |
| Technical report (8 pages max) | Drafted (`docs/report.md`); needs PDF export |
| Conservation and momentum record | Done (`docs/momentum-record.md`) |
| Demo video (3 min max) | Done, needs voiceover (`media/black-ant-demo.mp4`) |
| Pitch deck (7 min) | Drafted, 13 slides (shared deck, ask Ashish) |
| Still open | Half-step convergence check (running); contribution log (#17); questions to organisers (`docs/rules.md`) |

## 6. Known limits and gotchas

- The viewer's sliders give **estimates** (browser maths ported from `sim/habitability.py` and `sim/night.py`);
  the saved 2.7 AU run stays the official result. A target-orbit change needs a re-run of about an hour and a half to be official.
- Bodies other than Earth, Mars, Jupiter and the tow asteroid are placed by two-body Kepler orbits from their J2000
  elements (approximate, perturbations ignored).
- The climate model is zero-dimensional (yearly global mean). It has no day and night; night heating figures are
  separate estimates.
- Past 3.28 AU lie Jupiter's 2:1 resonance and Mars's parking orbit (3.64 AU): targets there are not safe.
- Node 18 locally (Vite 6 works); CI uses Node 22.

## 7. Active work

**Branch `claude/contextualization-blender-gui-1e303d` (pipelin-two worktree). Built and checked 25 Oct; not yet
committed or reviewed by the team.**

1. CONTEXT.md (this file) + `CLAUDE.md` pointer. Done.
2. Blender-style GUI replacing `viewer/index.html`. Done:
   - Top bar with view tabs (Solar system, Earth tow, Mars tow, Octo-Earth), scale, Model/Data toggles, theme.
   - Top-left **Scene** tab: every body's r, ecliptic longitude, source (run or Kepler); Moon, tow asteroids,
     sunlight satellites and Moon reflector counts under Earth/Mars; click a body to centre on it.
   - Left **Model** panel: experiments R, A-I; Time (speed + meters: journey, Earth/Mars orbit progress, E1 beam,
     E3 mirror area, year length); Target orbit (target AU, tow mass, tow distance; time to arrive, beam power, mirrors
     needed, hazard chips); Sunlight reflector satellites (follow the run or set a count); Moon reflectors.
   - Right **Data** panel: Constants, Initial Earth (year 0), Now against year 0 (24 factors incl. year length,
     seasons, Sun size, tides, light time, moonlight, impacts), Results and checks (all nine original tabs).
   - Bottom-right **Top view** button: orthographic, every orbit a circle, Inner / All orbits zoom; what-if target
     drawn as a light-blue dashed circle. Keys: Space, T, N, 7, Home. Timeline with editable year and markers.
   - Works without WebGL (panels only) and at phone width (panels stack under the viewport).
3. Moon reflectors, scalable. Done: `sim/night.py`, `tests/test_night.py` (5 tests), `config.yaml` `night`.
   At 2.7 AU: natural full Moon 0.034 lux (13.7% of today); 3,335 km2 of panels restore 0.25 lux; one panel lights a
   ~1,325 km patch; whole near side (9.5e6 km2) gives at most 6.6 W/m2 on the night side, 0.31 K global mean.
   Reflectors only work from first to last quarter (cos(phase/2), 45% monthly mean), so the lunar cycle is kept.

Checked: 40 quick tests pass; `npm run build` passes; headless Chromium (SwiftShader) screenshots of every view,
no console errors; `?capture` bench API works; Kepler placement matches the run's Earth/Jupiter at year 0 to 6e-7 AU.
The built-in browser pane has no WebGL, so 3D checks need headless Chromium (Playwright in the scratchpad).

## 8. Decisions (with the reason)

| Date | Decision | Why |
| --- | --- | --- |
| 25 Oct | Sliders give live estimates, clearly labelled; the saved run stays official | A full run takes about 1.5 hours; the page must stay static for GitHub Pages |
| 25 Oct | New GUI replaces the old layout; all nine result tabs and `?capture` kept | One page to maintain; the demo video script depends on the API |
| 25 Oct | Moon reflectors fit inside E3's mirror bound (no new enabler) | Enablers frozen after the mid-point |
| 25 Oct | Night feature shows both light (lux) and heating | User's choice |
| 25 Oct | Defaults: one sunlight satellite = 10,000 km2; one Moon reflector panel = 1 km2 (in `config.yaml`, `night`) | Counts need a unit size |
| 25 Oct | Work only in the pipelin-two clone | Both clones share one GitHub repo |

## 9. Important prompts (condensed)

- **25 Oct, P1:** Make a contextualization file for the whole project; always read it instead of the full chat and
  keep adding to it. Build a Blender-like GUI (panels as in 7.2). Fix the night "lumens" issue with scalable Moon
  reflectors. Ask questions before implementing and explain what else could be an issue.

## 10. What can be delivered next (ideas, not started)

- Re-run the journey with Moon reflectors inside the official checks (needs `sim/checks/safety.py` + a 1.5-hour run).
- Save Venus, Saturn, Uranus, Neptune and the big asteroids in `run.json` frames, so the viewer shows their true
  simulated positions instead of Kepler estimates.
- A day/night (two-box) climate model so night temperature is computed rather than estimated.
- Mention Moon reflectors in `docs/approach.md`, `docs/report.md` and the risk register if the team adopts them.
- Re-render the demo video (`viewer/scripts/video.mjs`) so it shows the new layout.
- Commit, push and open a PR from the branch (Ashish reviews; Pages deploys from `main`).

## Log

- 25 Oct: Read the whole project; created CONTEXT.md and CLAUDE.md. Asked 4 questions (night fix: both light and
  heat; sliders: live estimates; GUI replaces old page; work in pipelin-two only).
- 25 Oct: Added `sim/night.py` + tests + `config.yaml` `night`; `viewer_data.py` exports constants, planets, small
  bodies, night settings into `config.json`. Rebuilt the viewer as a Blender-style GUI (index.html, style.css,
  main.js, new studio.js, estimates.js, bodies.js; scene.js gains top view, all bodies, reflector visuals, WebGL
  fallback). README updated. Verified (see 7). Nothing committed yet.
