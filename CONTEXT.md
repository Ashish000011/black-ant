# CONTEXT.md: the project in one file, for AI models and new teammates

**Read this first, every prompt.** It replaces re-reading the chat history. Update it with notable changes only (a
feature, a result, a decision, an important prompt), in the same PR as the change, so PRs do not all collide on
this file: touch the sections concerned (Status, Decisions, Active work) and add one line to the Log at the bottom.
Keep entries short: what changed, where, and what is left. Numbers here are copied from `results/` and
`config.yaml`; if they differ, those files win. Machine-specific setup (local paths, accounts) does not belong here.

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

**Why not the brief's Octo-Earth:** forces between arms and Earth are internal whatever the arms' shape (net 3.4e-13
of each force). Curled over the planet as the company's demo draws it, a 12,000 km arm breaks at its root past 5 km
(steel) or 637 km (nanotube); standing straight up it would buckle past 471 km or 1,444 km. Audited in
`sim/scenarios/octo.py` (the demo's curled arm, from `config.yaml` `octo_earth`), test X8.

- Repo: `github.com/Ashish000011/black-ant`. Nobody pushes to `main`: branch, PR, Ashish reviews and merges.
- Team: Ashish Bharti (lead), Madhukar Verma, Akhil Semwal, Sushmit Sukla, Prabhanshu Kerketa. Who did what is in
  `docs/contributions.md`, by the work each actually did.

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

**Half-step convergence check (done):** with half-day steps Earth arrives in year 8,730 at 2.70 AU (1-day run: 8,758
at 2.7006), Mars parks in 5,170 at 3.6415 AU (1-day run: 5,168 at 3.6408), and the ledger closes to 2.3e-16. These
numbers go into the docs on `main`.

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
| `sim/` | Python model (uv, Python 3.12, numpy, rebound, pyyaml). `integrator.py` gravity and steppers; `forces.py` tow and beam; `ledger.py` momentum; `habitability.py` sunlight, mirrors, climate; `night.py` moonlight and Moon reflectors; `checks/` safety and structures every 100 days; `scenarios/` journey (`tow.py`), moon, longterm, parking, outage, crossing, octo, swap (Plan S study), small_asteroids (rocks under 1 km, #30); `viewer_data.py` turns `results/` into `viewer/public/data/` |
| `results/` | The final run's outputs. `run.json` has one frame per 10 years with positions of **only Earth, Mars, Jupiter and the Earth tow asteroid** |
| `viewer/` | 3D test bench (Vite 6, Three.js 0.170, plain JS). **Replays saved runs; the official numbers are not computed in the browser.** Published to GitHub Pages from `main` (`.github/workflows/pages.yml`). `src/main.js` wiring and keys; `src/scene.js` 3D views incl. top view and close-ups, `noStage` fallback without WebGL; `src/studio.js` Blender-style panels (Scene tab, Model, Data, the million-years explainer); `src/estimates.js` values derived from the run (year length, Sun size, tides, light time) and the Moon reflectors (port of `night.py`); `src/bodies.js` positions of every body (run or Kepler); `src/panels.js` the nine results tabs; `src/data.js` loading and interpolation |
| `viewer/scripts/video.mjs` | Renders the demo video through `?capture` mode and `window.bench` (run, view, tab, time, scale, orbit, caption, frame). **Keep that API working.** |
| `docs/` | problem, approach, enablers, report (technical report), status, risk register, qa, rules, momentum record, contributions |
| `tests/` | Official benchmarks, extra checks, safety and structure checks, Moon, night |

Commands:

```bash
uv sync                                   # set up
uv run python -m sim.benchmarks           # ten official benchmarks, ~12 s
uv run pytest -m "not slow" -v            # quick tests (run on every PR)
uv run python -m sim.scenarios.tow --out results   # full journey, about 1.5 hours
uv run python -m sim.scenarios.swap       # Plan S: Earth-Mars crossing, 12 starts (a few minutes)
uv run python -m sim.scenarios.small_asteroids   # rocks under 1 km at 2.7 AU (#30), a second
uv run python -m sim.viewer_data          # results/ -> viewer/public/data/
cd viewer && npm ci && npm run dev        # test bench locally
```

## 5. Deliverables (guide section 9)

| Deliverable | Status |
| --- | --- |
| Source code with README | Done |
| Runnable simulation + 3D test bench | Done; Blender-style test bench in PR #23 |
| Technical report (8 pages max) | Drafted (`docs/report.md`); needs PDF export |
| Conservation and momentum record | Done (`docs/momentum-record.md`) |
| Demo video (3 min max) | Done, captions on screen (`media/black-ant-demo.mp4`, 2 min 20 s); re-rendered with the Blender-style test bench and again with #27's Octo-Earth view |
| Pitch deck (7 min) | Drafted, 13 slides (shared deck, ask Ashish) |
| Half-step convergence check | Done (numbers in section 2) |
| Still open | Each member checks their section of `docs/contributions.md` (#17) |

## 6. Known limits and gotchas

- The test bench replays the saved run. The only numbers it computes outside the run are the Moon reflectors
  (marked ≈, formulas of `sim/night.py`). Any other change needs `config.yaml` changed and a re-run of about an hour
  and a half.
- Bodies other than Earth, Mars, Jupiter and the tow asteroid are placed by two-body Kepler orbits from their J2000
  elements (approximate, perturbations ignored).
- The climate model is zero-dimensional (yearly global mean). It has no day and night; night heating figures are
  separate estimates.
- The Moon-reflector area is conservative: `night.py` compares the overhead full-Moon figure (0.25 lux) with light
  averaged over the whole night hemisphere, so the area comes out up to 2x too big.
- Past 3.28 AU lie Jupiter's 2:1 resonance and Mars's parking orbit (3.64 AU): orbits there are not safe.
- Vite 6 needs Node 18 or newer; CI uses Node 22.
- The climate run counts the sunlight optics face on. Design (#39): a refracting ring near L1 (100 g/m2) gives 97%
  of today's sunlight inside E3 at 95% transmission; below 89.3% of today's sunlight the climate model freezes. E3's
  bound is read as covering sunlight optics; fallback (mirrors only): the sunlight-held ring at 120 deg (#32).
  The tow mirror's scattered light is bounded by no enabler (needs s < 3.4e-11 for dark nights).

## 7. Active work

**Branch `claude/contextualization-blender-gui-1e303d`, PR #23 (github.com/Ashish000011/black-ant/pull/23).** It
replaces PR #22, which was closed unmerged on 25 Oct. Ashish approved #23 on 25 Oct and asked for review fixes on
the branch before merging (done 25 Oct, see Log). The branch starts from `b101f2f`; `main` has since gained only a
contribution log, a status update and README lines that do not overlap, so it merges cleanly.

1. CONTEXT.md (this file) + `CLAUDE.md` pointer. Done.
2. Blender-style GUI replacing `viewer/index.html`. Done:
   - Top bar: name left, view tabs (Solar system, Earth tow, Mars tow, Octo-Earth), live **mission line** in the
     middle ("Year X · Earth a → 2.7 AU · N years to go"), **A− / A+ text size** (80-150%, remembered), scale,
     Model/Data toggles, theme. Text size scales font sizes, panel widths and fixed heights via `--ui-zoom` (CSS
     `zoom` overflowed full-width bars, so it is not used). The bar wraps rather than overflowing.
   - Top-left **Scene** tab: every body's r, ecliptic longitude, source (run or Kepler); Moon, tow asteroids,
     sunlight satellites and Moon reflector counts under Earth/Mars. Click a planet to centre on it; click the Moon,
     a tow asteroid or the reflectors to open the Earth or Mars tow view centred on it, the camera following it
     (`Stage.focusClose`).
   - Left **Model** panel: experiments R, A-I; Time (speed + meters: journey, Earth/Mars orbit progress, E1 beam,
     E3 mirror area, year length); Concept and enablers (open by default). No sliders (removed 25 Oct, P7).
   - Experiment I opens a large **explainer card over the Data panel**: why a million years, how it is tested,
     moved vs real Earth table, flags, chaos copies, what it cannot prove (inner planets chaotic, ~5 Myr, Laskar 1989).
   - Right **Data** panel: Constants, Initial Earth (year 0), Now against year 0 (24 factors incl. year length,
     seasons, Sun size, tides, light time, moonlight, impacts), Results and checks (all nine original tabs).
   - Bottom-right **Top view** button: orthographic, every orbit a circle, Inner / All orbits zoom. Keys: Space, T,
     N, 7, Home. Timeline with editable year and markers.
   - Works without WebGL (panels only) and at phone width (panels stack under the viewport).
3. Moon reflectors at fixed defaults. Done: `sim/night.py`, `tests/test_night.py` (5 tests), `config.yaml` `night`.
   At 2.7 AU: natural full Moon 0.034 lux (13.7% of today); 3,335 km2 of panels restore 0.25 lux (conservative, see
   6); one panel lights a ~1,325 km patch; whole near side (9.5e6 km2) gives at most 6.6 W/m2 on the night side,
   0.31 K global mean. Reflectors only work from first to last quarter (cos(phase/2), 45% monthly mean), so the
   lunar cycle is kept.

Checked: 40 quick tests pass; `npm run build` passes; headless Chromium (SwiftShader software WebGL) screenshots of
every view, no console errors; `?capture` bench API works; Kepler placement matches the run's Earth/Jupiter at
year 0 to 6e-7 AU. A browser without WebGL shows the panels only, so 3D checks need a headless Chromium.

### Plan S study (25 Oct): swap Earth and Mars instead of pushing Mars out

`sim/scenarios/swap.py` (outputs in `out/swap_*.json`, which git ignores). Mars towed IN to Earth's old orbit (1 AU)
while Earth goes out to 2.7 AU. Tows modelled as their pull on the planet (G m / d^2 toward the spot; Mars's spot
45 deg behind-and-out); REBOUND IAS15, real J2000 planets.
- By hand: Mars needs 5.66 km/s (out to 3.64: 8.52), ~3,900 years at the normal pull, no Jupiter 2:1 crossing.
  But the orbits MUST cross: sizes meet ~year 1,940 at ~1.22 AU.
- Plain crossing, tows kept on (48 runs: Mars eccentric/round x normal/4x-sprint, 12 starts each): every run passes
  inside the 0.05 AU limit (2 to 99 times); closest 0.0018-0.0447 AU; 10 of 48 within 1 million km, 2 of 48 inside
  the Moon's distance. No collisions, crossing always completes, Earth e stays <= 0.026. NOT safe.
- End state (Earth 2.7, Mars 1.0), a million years, 5 runs (`--longterm`): stable. Earth as in the design (a
  2.698-2.702, e <= 0.056, tilt 22.4-27.0); Mars a +-0.0005, e <= 0.095 (round start) or 0.166 (as today);
  Earth-Mars orbit gap 1.39-1.46 AU (design 0.55). Close passes only Earth vs big asteroids, as in the design.
- Gravity handover (Janus-Epimetheus, `--handover`): tows off, 0.0007-0.003 AU apart, 180 deg apart: they swap in
  130-240 years and never come within 0.37 AU. Restarting the tows at normal pull: re-swaps 7 times, passes at
  45,000-90,000 km (near collision). Restarting with Mars x4, Earth x0.56: one clean swap, closest 0.026 AU.
- Verdict: the end state is better than the design's; the crossing is the problem. Only a staged handover with a
  sprint comes near safe (0.026 AU, under the 0.05 AU rule), and its approach leg (arriving 180 deg apart, nearly
  level, round orbits) is untested and needs a phase-targeting controller plus inward-tow code in the full model.
  Recommendation: keep the design for the final; use Plan S as a studied alternative (Q&A).

## 8. Decisions (with the reason)

| Date | Decision | Why |
| --- | --- | --- |
| 25 Oct | The test bench replays the saved run; only the Moon reflectors are computed in the browser, marked ≈ | A full run takes about 1.5 hours; the page must stay static for GitHub Pages |
| 25 Oct | New GUI replaces the old layout; all nine result tabs and `?capture` kept | One page to maintain; the demo video script depends on the API |
| 25 Oct | Moon reflectors fit inside E3's mirror bound (no new enabler) | Enablers frozen after the mid-point |
| 25 Oct | Night feature shows both light (lux) and heating | User's choice |
| 25 Oct | Defaults: one sunlight satellite = 10,000 km2; one Moon reflector panel = 1 km2 (in `config.yaml`, `night`) | Counts need a unit size |
| 25 Oct | Moon / tow asteroid rows open the tow close-up (not drawn in the solar-system view) | In that view Earth is drawn 260x, so they would sit inside it |
| 25 Oct | Model panel keeps experiments, time meters, concept and enablers only; reflector numbers stay at fixed defaults (satellites follow the run, Moon reflectors restore today's full Moon) | User: no need for the sliders |
| 25 Oct | CONTEXT.md is updated for notable changes only, in the same PR; no machine-specific setup in it | Ashish's review: every PR editing it would conflict, and local paths or accounts would mislead other machines |
| 25 Oct | Octo-Earth drawn and audited as the company's demo draws it (experiment R: 24 jointed segments curling 72° round the globe to a claw 4,600 km up, alternate arms north and south), ring on the equator; its labels give both the curled arm's failure and the standing arm's buckling | Akhil (#27): the demo is what the company expects, "this or closest to it"; the curled arm fails sooner than the standing one buckles |
| 25 Oct | Rocks under 1 km (#30): rates as low / central / high with JWST's slope errors and the 1 km population's together; a whole-sky fleet of NEO Surveyor-class telescopes rated at 280 uJy; Grün's 1 AU dust flux unscaled; rocks 2,000 kg/m3 (1,200 to 3,300) | Akhil's choices (the recommended options); each errs toward more hits, later sightings and more wear |
| 25 Oct | E1 answers small rocks by pushing them whole (light they absorb, spot as wide as the tow mirror), never by breaking them | Inside E1's declared role; no fragments, no debris; 2% of its spare power |
| 25 Oct | Space debris from the mirror fleet handled by thin rip-stop film, E3 recycling and placement away from today's satellites | Akhil asked; hits make holes and vapour, not fragments |
| 25 Oct | Sunlight mirrors (#32): lead with the simple ring that keeps nights dark (20% over E3, said plainly), then the sunlight-held ring at 120 deg as the way back inside E3; tow-mirror scatter an open risk with both limits | Akhil's choices; a limit of our own design counts for honesty |
| 25 Oct | Sunlight optics (#39): adopt a refracting ring near L1 (option D); the sunlight-held ring at 120 deg (C) is the fallback if E3 is read as mirrors only. Film 100 g/m2; tow-mirror rock totals over the belt years, the whole tow as upper bound | Ashish's decision (#39); film weight and counting are Akhil's choices: light film is pushed far past L1 |

## 9. Important prompts (condensed)

- **25 Oct, P1:** Make a contextualization file for the whole project; always read it instead of the full chat and
  keep adding to it. Build a Blender-like GUI (panels as in 7.2). Fix the night "lumens" issue with scalable Moon
  reflectors. Ask questions before implementing and explain what else could be an issue.
- **25 Oct, P2:** Before committing, open a server and check the current state of the test bench.
- **25 Oct, P3:** Keep a git timeline of each feature, with commit messages that use the prompt's own context, and
  commit to the branch for Ashish.
- **25 Oct, P4:** Redo the commits from the user's own GitHub account.
- **25 Oct, P5:** Open a new PR to main from that account with the same description, saying it replaces #22.
- **25 Oct, P6:** Instead of moving Mars out, swap Earth and Mars so Mars takes a stable inner orbit; run
  simulations and calculations to find out if it is viable (see Plan S study in 7).
- **25 Oct, P7:** GUI fixes: Moon and tow asteroid "not working" in the solar system view; remove the target-orbit,
  sunlight-satellite and Moon-reflector sections from the Model panel (keep concept and enablers); A-/A+ text size
  left of Visualisation; a big explainer popup when "A million years later" is pressed; replace "Earth tow test
  bench" with something interesting in the middle of the top bar. Also: report when running simulations finish.
- **25 Oct, P8:** Show the Earth-Mars swap results; is it feasible? (Answered with a chart: no, not for the final.)
- **25 Oct, P9:** Commit it all now, with messages saying what is implemented.
- **25 Oct, P10:** Ashish approved PR #23 with review comments: work on them, and start new sessions for the next PRs.
- **25 Oct, P11 (Akhil, #27):** Make the Octo-Earth view match the company's demo (octo-earth-simulator.vercel.app),
  "this or closest to it"; labels show both the curled and the standing numbers; ring on the equator; report figure
  and a new column in its table.
- **25 Oct, P12 (Akhil, #30):** Re-render the demo video here, and work on Ashish's new issue: small asteroids at
  2.7 AU (impacts, infrared survey, E1's response, mirror wear, Mars and the Moons). Also: with so many satellites
  and mirrors, won't there be space debris, and how is it handled efficiently?

## 10. What can be delivered next

After PR #23 merges, one PR each (Ashish's list):
1. `docs/qa.md` and `docs/risk-register.md`: "Why not swap Earth and Mars?" (Plan S) and "What about night light?"
   (0.034 lux at 2.7 AU; ~3,335 km2 of Moon reflectors restore 0.25 lux; they cannot carry the climate).
2. Re-render the demo video with the new layout (`viewer/scripts/video.mjs`); `media/` shows the old page.
3. Each member's own section in `docs/contributions.md` (#17), in their own words.

Ideas, not started:
- Re-run the journey with Moon reflectors inside the official checks (needs `sim/checks/safety.py` + a 1.5-hour run).
- Save Venus, Saturn, Uranus, Neptune and the big asteroids in `run.json` frames, so the viewer shows their true
  simulated positions instead of Kepler estimates.
- A day/night (two-box) climate model so night temperature is computed rather than estimated.
- Mention Moon reflectors in `docs/approach.md` and `docs/report.md` if the team adopts them.
- Decide whether hidden panels (T / N) should be remembered between visits (they are now, in localStorage), so a
  returning viewer never sees an empty page.

## Log

- 25 Oct: Read the whole project; created CONTEXT.md and CLAUDE.md. Asked 4 questions (night fix: both light and
  heat; sliders: live estimates; GUI replaces old page; which clone to work in).
- 25 Oct: Added `sim/night.py` + tests + `config.yaml` `night`; `viewer_data.py` exports constants, planets, small
  bodies, night settings into `config.json`. Rebuilt the viewer as a Blender-style GUI (index.html, style.css,
  main.js, new studio.js, estimates.js, bodies.js; scene.js gains top view, all bodies, reflector visuals, WebGL
  fallback). README updated. Verified (see 7).
- 25 Oct: Checked the running test bench. Corrected the journey's run time to about 1.5 hours (as `main` now says).
  Committed one feature per commit, messages quoting the request. Opened PR #22.
- 25 Oct: Rewrote the branch's commits under the author's own account; PR #22 had already been closed unmerged
  (label `invalid`, no comment). Opened PR #23 from that account ("Replaces #22").
- 25 Oct: Plan S study (swap Earth and Mars): `sim/scenarios/swap.py`, 48 crossing runs, 5 million-year runs,
  14 handover runs. End state stable; crossing unsafe unless staged.
- 25 Oct: P7 test bench fixes (Model panel slimmed, close-ups for Moon/tow asteroids, mission line, text size,
  million-years explainer). Committed with the Plan S study and pushed to PR #23.
- 25 Oct: Ashish approved PR #23 with fixes requested. Done on the branch: machine-specific lines and the account
  instructions removed from this file, stale slider mentions fixed, prompts in date order, half-step check marked
  done, `swap.py` reads its 0.05 AU limit from `config.yaml` and its docstring names `--longterm`, README lists
  `swap.py`, the top bar wraps at phone width, `night.py` says its reflector area is conservative, CLAUDE.md asks
  for updates on notable changes only. Next PRs (section 10) started in their own sessions.
- 25 Oct: Demo video re-rendered with the Blender-style test bench (own PR, merges after #23): `video.mjs` turns the
  Earth tow and Octo-Earth cameras so panels and caption hide nothing, and scrolls the Data panel to each shot's tab.
- 25 Oct: Team by name. `docs/contributions.md` rewritten by name and by the work each member actually did
  (Claude Code noted as a tool, not a member); "Member N" labels replaced by names in the risk register and
  enablers, and dropped from code comments. Organiser questions and `docs/video-script.md` removed from the public
  docs; the six winning conditions vs ten thresholds/benchmarks made explicit in `docs/problem.md`; report figures
  re-taken from the new test bench. Akhil assigned the Octo-Earth reference view (#27).
- 25 Oct: Octo-Earth reference view (#27, Akhil). Studied the company's demo (its own code): experiment R's arm is 24
  jointed segments leaving at 36.1° and bending 7.13° down per joint (less toward the tip) to a claw 72° round the
  globe, 4,600 km up. `config.yaml` `octo_earth` and `octo.py` now model that arm (`arm_path`, `curled_root`): net
  force 3.4e-13 (was 3.7e-12 for straight arms); curled it breaks at its root past 5 km (steel), 637 km (nanotube),
  safety factor 0.012 at 12,000 km. Test X8 checks the shape, the net force and the curled failure. `scene.js` draws
  the ring band, the jointed arms with collars and three-fingered claws; report figure, table and docs updated.
  Demo video re-rendered (all 3,500 frames) with the new Octo-Earth shot and caption.
- 25 Oct: Small asteroids at 2.7 AU (#30, Akhil): `sim/scenarios/small_asteroids.py` post-processes the run's belt
  passes with JWST's size distribution (`config.yaml` `small_asteroids`, sources there). Parked, undefended: 20 m and
  up about 8 a year (1 to 40), 100 m once per 9 years; seen 10 to 15 days out (20 m) by NEO Surveyor-class telescopes;
  E1 pushes each with 1.6e23 W for a day (2% of its spare). Wear: E3 replaces 570 km2 of sunlight mirror a year;
  debris 5,700 t of film a year, mostly vapour. Moon, Mars, Phobos, Deimos: craters only. Kirkwood gaps: 0.75 to 1.05
  of the encounters at 2.7 AU. Tests in `tests/test_small_asteroids.py`. Stacked on PR #29.
- 25 Oct: #29 and #31 approved and merged, but #31 merged into #29's branch, not `main`; re-landed as PR #34. Q&A for
  #33 (Akhil): stellar engines (Shkadov, Caplan 2019), where E1's power comes from, DE-STAR (Lubin et al.), light
  pressure in flight (IKAROS, LightSail 2, Starshot), with sources; the #29 and #31 review follow-ups (why steel
  fails curled sooner than level; "pushes it aside or vaporises it"). New PRs target `main` only.
- 25 Oct: Sunlight mirrors (#32, Akhil): `sim/scenarios/mirrors.py`, `tests/test_mirrors.py`, `config.yaml` `mirrors`.
  Ring orbiting 200,000 km out in the plane facing the Sun, spots aimed at daylit ground: 1.2e9 km2 (20% over E3);
  capped at 1e9 Earth freezes (238 K). Sunlight-held ring at 120 deg on 1 um film: 9.8e8 km2, 711,000 km out. Tow
  mirror: 1,466 K red disc the Moon's size in the night sky, 0.24 lux at full power; scatter must stay under 3.4e-11.
  Satellites' panels get 13.6%. Q&A, risk register, report sentence. Stacked on #35 (and #34); PR targets `main`.
- 25 Oct: Report references (#36, Akhil): 42 checked references with [n] in the text, related work (Lu & Love 2005;
  Korycansky et al. 2001: a 1e19 kg body every ~6,000 years for ~1e6 passes at ~1e4 km, Moon likely lost, "extremely
  risky"), Limits of the model brought up to date (#30, #32). Checking caught the belt mass: Pitjeva & Pitjev 2018 give
  4.008e-4 Earth masses (2.394e21 kg), not 12.4e-10 solar masses; fixed in `config.yaml`, small-asteroid results
  re-run (Mars break-up 370 belt masses). The NEO Surveyor sensitivity source is the EU-ESA NEO size workshop, Nov 2024.
- 25 Oct: Sunlight optics (#39, Akhil): option D in `sim/scenarios/mirrors.py`. Sunlight's push sets how far past
  L1 the ring sits (2.5 g/m2: 48%, only 38% of the light lands; 100 g/m2: 0.9%, 82%). Inside E3: 97.3% of today's
  sunlight, 286 K at T 0.95; 281.7 K at 0.90; freezes at 0.85 (cliff 89.3%). Tow mirrors: 62 rocks >= 20 m over the
  belt years (196 whole tow), beam vaporises a 1 m rock in 3-6 ms, 7.3% spare power. Q&A, register, report, enablers.
- 25 Oct: Report trimmed to 8 pages (A4, 10.5 pt, references in two columns at 8 pt; 150 words of spare room): Summary states the L1 optics outcome (97%, 286 K); Octo-Earth table cut to four materials; one Sunlight optics paragraph; E3 limit reads sunlight optics; Limits adds the 13-month seasons and that the 1.4% tilt re-aim must come out of E3 with the L1 ring; Ceres leaving in one chaos copy stated.
