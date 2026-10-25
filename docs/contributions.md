# Who built what

The guide: "Careers offers are based on individual contribution, so keep a short log of who built what. Every
member should be able to explain the code and the physics."

Each section lists what that person actually did, with the pull request where there is one. The git history and
the pull requests are the record behind every line. Members: check your own section and add anything missing, in
your own words.

## Ashish Bharti (team lead)

- **Concept and approach:** the gravity tractor held in place by light, Mars moved out of the way first, sunlight
  mirrors to keep Earth at today's sunlight, and the three declared enablers.
- **The model and its results:** the simulation in `sim/` (gravity and the steppers, the tows and their beams, the
  momentum ledger, climate and Earth-safety checks, structures, the ten official benchmarks), the final journey in
  `results/`, the million-year runs and the Octo-Earth audit ([#18](https://github.com/Ashish000011/black-ant/pull/18),
  [#19](https://github.com/Ashish000011/black-ant/pull/19)).
- **The first 3D test bench**, the technical report, the risk register and the docs (#18, #19); the half-step
  convergence check ([#24](https://github.com/Ashish000011/black-ant/pull/24)).
- **Running the team:** the task issues (#1 to #17), reviews and merges.

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

## Sushmit Sukla

- Started this contribution log, and pointed the status page and README to the new deliverables
  ([#21](https://github.com/Ashish000011/black-ant/pull/21)).

## Prabhanshu Kerketa

- The technical report as a PDF with every number checked against `results/`, the pitch talk track, the Q&A with
  who answers what, a voiceover tool and the submission checklist
  ([#20](https://github.com/Ashish000011/black-ant/pull/20); to be resubmitted with the review's fixes).

## Tools

We used Claude Code, an AI coding assistant, throughout. Commits it helped write carry a "Co-Authored-By: Claude"
line. Every member should still be able to explain the code and the physics behind their part.
