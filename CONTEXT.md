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

**Branch `claude/contextualization-blender-gui-1e303d` (pipelin-two worktree). Built and checked 25 Oct;
committed one feature per commit as madhukarverma. PR #22 (opened from sushmitnitt) was closed unmerged by
Ashish on 25 Oct 01:25 IST with the label `invalid` and no comment. PR #23
(github.com/Ashish000011/black-ant/pull/23), opened from madhukarverma, replaces it and awaits Ashish's review.** The branch starts from `b101f2f`;
`main` has since gained only a contribution log, a status update and README lines that do not overlap, so it
merges cleanly.

1. CONTEXT.md (this file) + `CLAUDE.md` pointer. Done.
2. Blender-style GUI replacing `viewer/index.html`. Done:
   - Top bar with view tabs (Solar system, Earth tow, Mars tow, Octo-Earth), scale, Model/Data toggles, theme.
   - Top-left **Scene** tab: every body's r, ecliptic longitude, source (run or Kepler); Moon, tow asteroids,
     sunlight satellites and Moon reflector counts under Earth/Mars; click a body to centre on it.
   - Left **Model** panel: experiments R, A-I; Time (speed + meters: journey, Earth/Mars orbit progress, E1 beam,
     E3 mirror area, year length); Concept and enablers (open by default). The target-orbit, sunlight-satellite and
     Moon-reflector sliders were removed on 25 Oct (P7); reflector numbers stay at fixed defaults elsewhere.
   - Top bar: name left, live **mission line** in the middle ("Year X · Earth a → 2.7 AU · N years to go"),
     **A− / A+ text size** (80-150%, remembered) left of Visualisation. Text size scales font sizes, panel widths
     and fixed heights via `--ui-zoom` (CSS `zoom` overflowed full-width bars, so it is not used).
   - Scene tab: clicking the Moon, a tow asteroid or the reflectors opens the Earth or Mars tow view centred on it,
     and the camera follows it (`Stage.focusClose`).
   - Experiment I opens a large **explainer card over the Data panel**: why a million years, how it is tested,
     moved vs real Earth table, flags, chaos copies, what it cannot prove (inner planets chaotic, ~5 Myr, Laskar 1989).
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

### Plan S study (25 Oct): swap Earth and Mars instead of pushing Mars out

`sim/scenarios/swap.py` (committed 25 Oct; outputs in `out/swap_*.json`, which git ignores). Mars towed IN to Earth's old orbit (1 AU)
while Earth goes out to 2.7 AU. Tows modelled as their pull on the planet (G m / d^2 toward the spot; Mars's spot
45 deg behind-and-out); REBOUND IAS15, real J2000 planets.
- By hand: Mars needs 5.66 km/s (out to 3.64: 8.52), ~3,900 years at the normal pull, no Jupiter 2:1 crossing.
  But the orbits MUST cross: sizes meet ~year 1,940 at ~1.22 AU.
- Plain crossing, tows kept on (48 runs: Mars eccentric/round x normal/4x-sprint, 12 starts each): every run passes
  inside the 0.05 AU limit (2 to 99 times); closest 0.0018-0.0447 AU; 10 of 48 within 1 million km, 2 of 48 inside
  the Moon's distance. No collisions, crossing always completes, Earth e stays <= 0.026. NOT safe.
- End state (Earth 2.7, Mars 1.0), a million years, 5 runs: stable. Earth as in the design (a 2.698-2.702, e <= 0.056,
  tilt 22.4-27.0); Mars a +-0.0005, e <= 0.095 (round start) or 0.166 (as today); Earth-Mars orbit gap 1.39-1.46 AU
  (design 0.55). Close passes only Earth vs big asteroids, as in the design.
- Gravity handover (Janus-Epimetheus): tows off, 0.0007-0.003 AU apart, 180 deg apart: they swap in 130-240 years
  and never come within 0.37 AU. Restarting the tows at normal pull: re-swaps 7 times, passes at 45,000-90,000 km
  (near collision). Restarting with Mars x4, Earth x0.56: one clean swap, closest 0.026 AU (3.9 million km).
- Verdict: the end state is better than the design's; the crossing is the problem. Only a staged handover with a
  sprint comes near safe (0.026 AU, under the 0.05 AU rule), and its approach leg (arriving 180 deg apart, nearly
  level, round orbits) is untested and needs a phase-targeting controller plus inward-tow code in the full model.
  Recommendation: keep the design for the final; use Plan S as a studied alternative (Q&A).

## 8. Decisions (with the reason)

| Date | Decision | Why |
| --- | --- | --- |
| 25 Oct | Sliders give live estimates, clearly labelled; the saved run stays official | A full run takes about 1.5 hours; the page must stay static for GitHub Pages |
| 25 Oct | New GUI replaces the old layout; all nine result tabs and `?capture` kept | One page to maintain; the demo video script depends on the API |
| 25 Oct | Moon reflectors fit inside E3's mirror bound (no new enabler) | Enablers frozen after the mid-point |
| 25 Oct | Night feature shows both light (lux) and heating | User's choice |
| 25 Oct | Defaults: one sunlight satellite = 10,000 km2; one Moon reflector panel = 1 km2 (in `config.yaml`, `night`) | Counts need a unit size |
| 25 Oct | Work only in the pipelin-two clone | Both clones share one GitHub repo |
| 25 Oct | Moon / tow asteroid rows open the tow close-up (not drawn in the solar-system view) | In that view Earth is drawn 260x, so they would sit inside it |
| 25 Oct | Model panel keeps experiments, time meters, concept and enablers only; reflector numbers stay at fixed defaults (satellites follow the run, Moon reflectors restore today's full Moon) | User: no need for the sliders |
| 25 Oct | Commit as **madhukarverma** `<174335640+madhukarverma@users.noreply.github.com>` and push with that gh account: `git -c user.name=madhukarverma -c user.email=174335640+madhukarverma@users.noreply.github.com commit ...`, then `GH_TOKEN=$(gh auth token --user madhukarverma) git push` | The user's GitHub account; this clone's git config and gh's active account are sushmitnitt |

## 9. Important prompts (condensed)

- **25 Oct, P1:** Make a contextualization file for the whole project; always read it instead of the full chat and
  keep adding to it. Build a Blender-like GUI (panels as in 7.2). Fix the night "lumens" issue with scalable Moon
  reflectors. Ask questions before implementing and explain what else could be an issue.
- **25 Oct, P2:** Before committing, open a server and check the current state of the test bench.
- **25 Oct, P3:** Keep a git timeline of each feature, with commit messages that use the prompt's own context, and
  commit to the branch for Ashish.
- **25 Oct, P4:** Redo the commits from the user's own account, madhukarverma.
- **25 Oct, P5:** Open a new PR to main from madhukarverma with the same description, saying it replaces #22.
- **25 Oct, P7:** GUI fixes: Moon and tow asteroid "not working" in the solar system view; remove the target-orbit,
  sunlight-satellite and Moon-reflector sections from the Model panel (keep concept and enablers); A-/A+ text size
  left of Visualisation; a big explainer popup when "A million years later" is pressed; replace "Earth tow test
  bench" with something interesting in the middle of the top bar. Also: report when running simulations finish.
- **25 Oct, P8:** Show the Earth-Mars swap results; is it feasible? (Answered with a chart: no, not for the final.)
- **25 Oct, P9:** Commit it all now, with messages saying what is implemented.
- **25 Oct, P6:** Instead of moving Mars out, swap Earth and Mars so Mars takes a stable inner orbit; run
  simulations and calculations to find out if it is viable (see Plan S study in 7).

## 10. What can be delivered next (ideas, not started)

- Re-run the journey with Moon reflectors inside the official checks (needs `sim/checks/safety.py` + a 1.5-hour run).
- Save Venus, Saturn, Uranus, Neptune and the big asteroids in `run.json` frames, so the viewer shows their true
  simulated positions instead of Kepler estimates.
- A day/night (two-box) climate model so night temperature is computed rather than estimated.
- Mention Moon reflectors in `docs/approach.md`, `docs/report.md` and the risk register if the team adopts them.
- Re-render the demo video (`viewer/scripts/video.mjs`) so it shows the new layout.
- Ashish reviews PR #23 (it replaces #22); find out why #22 was marked invalid in case the same applies.
- Decide whether hidden panels (T / N) should be remembered between visits (they are now, in localStorage), so a
  returning viewer never sees an empty page.
- Add this work to `docs/contributions.md` (on `main` since PR #21) if the team wants it credited.

## Log

- 25 Oct: Read the whole project; created CONTEXT.md and CLAUDE.md. Asked 4 questions (night fix: both light and
  heat; sliders: live estimates; GUI replaces old page; work in pipelin-two only).
- 25 Oct: Added `sim/night.py` + tests + `config.yaml` `night`; `viewer_data.py` exports constants, planets, small
  bodies, night settings into `config.json`. Rebuilt the viewer as a Blender-style GUI (index.html, style.css,
  main.js, new studio.js, estimates.js, bodies.js; scene.js gains top view, all bodies, reflector visuals, WebGL
  fallback). README updated. Verified (see 7).
- 25 Oct: Checked the running test bench (the pane has no WebGL; panels had been remembered as hidden). Corrected
  the journey's run time to about 1.5 hours (as `main` now says). Committed one feature per commit, messages
  quoting the request: CONTEXT.md; Moon reflectors (sim/night.py); 3D bodies and top view; live estimates;
  Blender-style layout; README; this log. Pushed the branch for Ashish.
- 25 Oct: Opened PR #22 against `main` (ready for review, follows the repo's PR template).
- 25 Oct: Rewrote the branch's 8 commits as madhukarverma (author and committer; messages, contents and times
  unchanged) and force-pushed them to PR #22. PR #22 itself was opened by sushmitnitt.
- 25 Oct: Found PR #22 closed by Ashish (label `invalid`, no comment) a minute before the force-push.
- 25 Oct: Opened PR #23 from madhukarverma (ready for review, same description, "Replaces #22").
- 25 Oct: Plan S study (swap Earth and Mars): `sim/scenarios/swap.py`, 48 crossing runs, 5 million-year runs,
  14 handover runs. End state stable; crossing unsafe unless staged. Not committed.
- 25 Oct: P7 GUI fixes done (Model panel slimmed, close-ups for Moon/tow asteroids, mission line, text size,
  million-years explainer). Checked: build, headless Chromium shots, capture API, 40 quick tests. All simulations
  from the Plan S study had finished. Not committed.
- 25 Oct: Committed as madhukarverma on the PR #23 branch: the Plan S study (`sim/scenarios/swap.py`), the P7 test
  bench fixes (one commit listing each fix), and this log. Pushed to PR #23 as madhukarverma.
