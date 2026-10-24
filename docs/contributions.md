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
- Next: a realistic Octo-Earth reference view in the test bench
  ([#27](https://github.com/Ashish000011/black-ant/issues/27)).

## Madhukar Verma

- **`CONTEXT.md` and `CLAUDE.md`:** the whole project in one file, for new teammates and AI assistants
  ([#23](https://github.com/Ashish000011/black-ant/pull/23)).
- **The Blender-style test bench:** floating Scene, Model and Data panels, the top view, close-ups of the Moon and
  the tow asteroids, the mission line, text size, the million-years explainer and the phone layout (#23).
- **Moon reflectors for night light** (`sim/night.py` and its tests): how much moonlight is left at 2.7 AU and the
  mirror area that brings it back (#23).
- **Plan S study:** swapping Earth and Mars instead of pushing Mars out (`sim/scenarios/swap.py`) (#23).
- Q&A and risk register for the swap, night light and where the tow asteroid comes from
  ([#25](https://github.com/Ashish000011/black-ant/pull/25), in review).

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
