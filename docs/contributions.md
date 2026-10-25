# Who built what

The guide: "Careers offers are based on individual contribution, so keep a short log of who built what. Every
member should be able to explain the code and the physics."

**Team leader: Sushmit Sukla.** Members: Ashish Bharti, Akhil Semwal, Madhukar Verma and Prabhanshu Kerketa.

Each section lists what that person actually did, with the pull request where there is one; the sections follow
the amount of work in the git history. The git history and the pull requests are the record behind every line
(commit and line counts are from `main` on 25 October: `git log`, and `git blame` over each folder). Members: check
your own section and add anything missing, in your own words.

## Ashish Bharti

Led the technical work day to day: the concept, the simulation and its results, the first test bench, the report,
the tooling, and the team's tasks and reviews. 57 commits on `main` (35 of his own and 22 merges of teammates' pull
requests), and the largest share of every part of the code: 3,254 of the 4,475 lines in `sim/` (73%), 326 of the
535 lines of tests, 1,571 of the 2,934 lines of the test bench's code, and 869 of the 1,167 lines in `docs/`.

**Concept and design decisions**
- The gravity tractor held in place by light, instead of the reference Octo-Earth: a 3.97 × 10^20 kg asteroid
  637,100 km from Earth, at 45° between along its orbit and away from the Sun, held on its spot by focused light on
  a mirror tied to it; nothing touches Earth.
- Mars moved out first and parked at 3.64 AU, between the strong resonances; the tow's sprint across Jupiter's 2:1
  resonance; the arrival trim from 2 AU that lands Earth on the orbit Jupiter forces at 2.7 AU; sunlight optics built
  in 25-year batches.
- The three declared enablers, each with a hard limit in `config.yaml` and every flag naming its enabler
  (`docs/enablers.md`, which he owns); E1's station recoil is booked, not cancelled.
- Chose the L1 refracting ring for the sunlight optics, with the sunlight-held ring at 120° as the fallback
  ([#39](https://github.com/Ashish000011/black-ant/issues/39)).
- Asked the questions that became studies: where the mirrors sit and what protects them when a rock hits
  ([#32](https://github.com/Ashish000011/black-ant/issues/32), #39); our satellites, and whether the mirrors can be
  seen from Earth (#32); what the move does to rain, the air and the view from Earth (Q&A); and the Moon (the Moon
  test).

**The simulation (`sim/`) and its results**
- The N-body engine: every pair's pull computed once and applied as exact opposites; a 1-day leapfrog for the
  journey, Yoshida fourth order for the benchmarks, REBOUND's MERCURIUS for a million years and an IAS15
  cross-check; the planets on their real J2000 orbits and the four biggest asteroids.
- The tows: light pressure on the mirrors, the controller that holds each asteroid on its spot, the beam keep-out
  round Earth and the power caps; the momentum ledger with error-free sums (it closes to 5.6 × 10^-16) and the
  energy check.
- Earth's safety: the climate model with ice-albedo feedback and the ten thresholds checked every 100 days; the
  structures at the power cap; the flags.
- The what-if runs: the asteroid belt with 1,000 real orbits, beam outages, the parking scans, the crossing of
  Jupiter's 2:1 resonance, the run without the Mars tow, a million years beside the real solar system with chaos
  copies, the Moon test, the first Octo-Earth audit, and the half-step convergence check
  ([#24](https://github.com/Ashish000011/black-ant/pull/24)).
- The ten official benchmarks, with inputs a judge can change, and our checks X1 to X9
  ([#18](https://github.com/Ashish000011/black-ant/pull/18), [#19](https://github.com/Ashish000011/black-ant/pull/19)).
- The final run in `results/`: Earth at 2.7006 AU in year 8,758, with every winning condition met.

**Test bench, video and documents**
- The first 3D test bench, replaying `results/` and published on GitHub Pages (#18, #19), and the scale bar in every
  view ([#43](https://github.com/Ashish000011/black-ant/pull/43)).
- The explainer video with captions ([#42](https://github.com/Ashish000011/black-ant/pull/42)).
- The technical report ([#15](https://github.com/Ashish000011/black-ant/issues/15)), trimmed to 8 pages with the L1
  result ([#41](https://github.com/Ashish000011/black-ant/pull/41)) and built to PDF by a script (#42); the risk
  register, the momentum record, the rules, the Q&A, the status page and the enablers.

**Verification and tooling**
- The quick tests on every pull request, and the protected `main` that needs a review.
- `run.bat`, one menu for setting up and running everything (#42), and `scripts/verify.py`: one command runs every
  check and writes a results PDF ([#44](https://github.com/Ashish000011/black-ant/pull/44)).

**Running the team's work**
- The task issues #1 to #17, and the six research issues behind Akhil's studies
  ([#27](https://github.com/Ashish000011/black-ant/issues/27), [#30](https://github.com/Ashish000011/black-ant/issues/30),
  #32, [#33](https://github.com/Ashish000011/black-ant/issues/33), [#36](https://github.com/Ashish000011/black-ant/issues/36),
  #39).
- Reviewed and merged the teammates' pull requests (#23, #25, #26, #29, #34, #35, #37, #38, #40) with merge commits,
  so each keeps his own commits; reviewed #45.
- The team by name and this contribution log by the work each did
  ([#28](https://github.com/Ashish000011/black-ant/pull/28)).

## Akhil Semwal

- **Research and verification:** the research behind the concept, and checking the physics and the numbers.
- Raised the idea of parking Earth in a Kirkwood gap to dodge asteroids. The check showed the gaps are gaps in
  orbit size, not in space, so Earth stays at 2.7 AU.
- **The Octo-Earth reference view** ([#27](https://github.com/Ashish000011/black-ant/issues/27)): studied the
  company's demo and redrew our Octo-Earth to match it (a ring on the equator, eight 12,000 km arms of 24 jointed
  segments curling over the planet to gripper claws). The audit (`sim/scenarios/octo.py`, test X8) now models that
  curled arm: the net force is still zero, and curled, an arm breaks at its root past 5 km in steel and 637 km in
  ideal nanotube, sooner than it would buckle standing up.
- **Small asteroids at 2.7 AU** ([#30](https://github.com/Ashish000011/black-ant/issues/30)): rocks under 1 km
  (`sim/scenarios/small_asteroids.py`): impacts by size from JWST's size distribution, how early an infrared survey
  sees them, E1's push, dust wear on the mirrors and cables, the debris it makes, Mars and the Moons, and why a
  Kirkwood gap does not help.
- **Moving things with light, with sources** ([#33](https://github.com/Ashish000011/black-ant/issues/33)): Q&A on
  stellar engines (Shkadov, Caplan 2019), where E1's 10^26 W comes from, DE-STAR laser deflection (Lubin et al.), and
  light pressure in flight (IKAROS, LightSail 2, Breakthrough Starshot).
- **Where the sunlight mirrors sit** ([#32](https://github.com/Ashish000011/black-ant/issues/32)):
  `sim/scenarios/mirrors.py` found a limit of our own design: keeping nights dark needs 20% more mirror than E3's
  bound, unless a ring is held by sunlight on 1 um film. Also the tow mirror's glow and scattered light, what Earth
  sees of the mirrors, and our satellites.
- **The report's references and related work** ([#36](https://github.com/Ashish000011/black-ant/issues/36)): 42
  checked references cited in the text, a related-work paragraph (Lu & Love 2005; Korycansky, Laughlin & Adams 2001,
  read in full) and an up-to-date "Limits of the model". The check caught our belt mass, now Pitjeva & Pitjev's own
  value.
- **Sunlight optics at L1, and the tow mirrors' protection** ([#39](https://github.com/Ashish000011/black-ant/issues/39)):
  put the refracting ring near L1 in the model, found the film must be heavy (100 g/m^2) to sit near L1 and pass at
  least about 88% of the light, and worked out the rocks and dust on the tow mirrors and the layers that protect them.

## Madhukar Verma

- **`CONTEXT.md` and `CLAUDE.md`:** the whole project in one file, for new teammates and AI assistants
  ([#23](https://github.com/Ashish000011/black-ant/pull/23)).
- **The Blender-style test bench:** floating Scene, Model and Data panels, the top view, close-ups of the Moon and
  the tow asteroids, the mission line, text size, the million-years explainer and the phone layout (#23).
- **Moon reflectors for night light** (`sim/night.py` and its tests): how much moonlight is left at 2.7 AU and the
  mirror area that brings it back (#23).
- **Plan S study:** swapping Earth and Mars instead of pushing Mars out (`sim/scenarios/swap.py`) (#23).
- Q&A and risk register for the swap, night light and where the tow asteroid comes from
  ([#25](https://github.com/Ashish000011/black-ant/pull/25)).
- **The demo video re-rendered** with the new test bench, with each shot framed around the floating panels
  ([#26](https://github.com/Ashish000011/black-ant/pull/26)).

## Prabhanshu Kerketa

- **The physics paper and the physics deck** ([#45](https://github.com/Ashish000011/black-ant/pull/45)): a 7-page
  paper laid out like a journal preprint (10 figures drawn from `results/`, 6 tables, 9 equations, 50 references),
  and an 11-slide clickable deck with 5 backup slides and speaker notes, both rebuilt by scripts in `docs/physics/`.
- The technical report as a PDF with every number checked against `results/`, the pitch talk track, the Q&A with
  who answers what, a voiceover tool and the submission checklist
  ([#20](https://github.com/Ashish000011/black-ant/pull/20); closed, its parts to be resubmitted).

## Sushmit Sukla (team leader)

- Team leader.
- Started this contribution log, and pointed the status page and README to the new deliverables
  ([#21](https://github.com/Ashish000011/black-ant/pull/21)).

## Tools

We used Claude Code, an AI coding assistant, throughout; it is a tool, not a team member. Commits it helped write
carry a "Co-Authored-By: Claude" line (73 on `main`), and each is credited above to the member who directed that
work. Every member should still be able to explain the code and the physics behind their part.
