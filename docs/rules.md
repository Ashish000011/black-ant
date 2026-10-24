# The rules we work to, and where each is met

From the participant guide (Planetary Propulsion Simulation Hackathon, 24 to 26 October 2026). The guide says the
rulebook wins where the two differ; the rulebook's safety appendix has not reached us, so the ten Earth-safety
thresholds come from the company's reference demo (see the last section).

## Winning conditions (all required)

| Condition | Where we meet it |
| --- | --- |
| Earth reaches its target orbit within 10,000 simulated years | `sim/scenarios/tow.py`; arrival in `results/summary.json` |
| Every threshold in the rulebook appendix holds for the whole run | `sim/checks/safety.py`, every 100 days; thresholds in `config.yaml` |
| Every structural safety factor at least 1.5 | `sim/checks/structure.py`, every 100 days, sized for the power cap |
| Every applicable benchmark passes | `sim/benchmarks.py`, `tests/test_official_benchmarks.py` |
| Every force booked with its reaction; energy and momentum conserved | `sim/ledger.py`; `docs/momentum-record.md` |
| No unresolved flags (only flags caused by declared enablers) | `sim/flags.py`; `flags` in `results/summary.json` |

## Enablers (guide section 7)

- Up to three, declared in writing at the mid-point check-in; they cannot change afterwards. Ours: `docs/enablers.md`.
- Each must be bounded and labelled. Ours are, with limits in `config.yaml` (`enablers`): a power source up to
  10^26 W with its waste heat radiated (E1); a mirror material (E2); placing asteroids and building mirrors (E3,
  which includes the guide's "access to an asteroid of stated mass").
- Never allowed, and not used: reactionless thrust, breaking a conservation law, switching off gravity, inertia or
  Earth's field, assuming the outcome (our climate is modelled, not held constant), ignoring a load.
- Fewer and smaller enablers score higher. The energy bonus needs no hypothetical energy source; we do not claim it.

## The guide's common mistakes, and our answer to each

| Mistake | Our answer |
| --- | --- |
| Counting a force on the arms as thrust | Our push is gravity from a body outside Earth; Octo-Earth's arms audited in `sim/scenarios/octo.py` (test X8) |
| Open circuits; pushing on "the field" | The audit models closed circuits and Earth's field as currents in its core |
| 32-bit physics | 64-bit throughout, plus error-free sums in the momentum ledger |
| One time step for everything | 1-day steps for orbits; the controller is checked against the step every 100 days |
| Ignoring the Moon | `sim/scenarios/moon.py` follows the Moon itself; its Hill-sphere share is checked along the journey |
| Unlabelled visual scaling | The test bench labels visualisation and true scale on screen, with the factors |
| Hard-coded or tuned results | Every number comes from the running model, written to `results/`; tables are generated |
| No convergence check | The journey run at half the step (0.5 days): arrival moves 28 years in 8,758 (0.3%), same orbit, 0 unresolved flags |

## Deliverables (guide section 9)

| Deliverable | Ours |
| --- | --- |
| Source code, README with setup, run, test | This repository |
| Runnable simulation | The Python model, and the test bench on GitHub Pages (`viewer/`) |
| Technical report, at most 8 pages | Drafted as a shared document; exported to PDF for submission |
| Conservation and momentum record | `docs/momentum-record.md` |
| Demo video, at most 3 minutes | 2 minutes 20 seconds; script in `docs/video-script.md` |
| Pitch deck: 7 minutes, then 5 of questions | Deck drafted; answers in `docs/qa.md` |

Judging: physical correctness 30, validation and numerical rigour 20, scientific honesty 15, depth 15,
visualisation and usability 10, presentation and questions 10, energy bonus up to 10 more.

## Questions for the organisers

1. The rulebook's safety appendix: are its thresholds the ten in the company's demo? If not, which numbers?
2. Is a team of five confirmed in writing? (The guide says 2 to 4; we were told 5 is allowed.)
3. Does "access to an asteroid of stated mass" cover two asteroids (one for Earth, one for Mars) under one enabler?
4. Is a web link to the test bench enough as the runnable simulation, or must we also demo from a laptop?
