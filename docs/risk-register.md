# Black Ant risk register

Every way the Earth tow could fail, how we check it, and what we did about it. Status words: **Holds** (checked,
passes), **Fixed** (failed, countered, re-checked), **Covered (E1/E2/E3)** (relies on a declared enabler, with
numbers), **Open**, **Ask organisers**. Numbers come from `results/` (the final run of 24 October) unless stated.
Rules: the participant guide (Planetary Propulsion Hackathon); see `docs/problem.md` and `docs/enablers.md`.

## Rules and scope

| Risk | Why it matters | How we check | Counter | Status | Owner |
| --- | --- | --- | --- | --- | --- |
| The rulebook's safety appendix (the thresholds) is still not published | "Every threshold in the rulebook appendix" is a winning condition | Every limit sits in `config.yaml` with its source | Ask; when the numbers come, change them there and re-run (journey about 70 minutes) | Ask organisers | Member 5 (#9) |
| Team size: the guide says 2 to 4 members; we are 5 | Could affect eligibility | - | Ask today | Ask organisers | Ashish (#14) |
| Enablers are fixed at the mid-point check-in | They cannot change afterwards | `docs/enablers.md`; every use is a flag naming its enabler | Three enablers, each bounded and matched to an allowed kind; E1 no longer claims to cancel its own recoil (it is booked) | Ready to declare | Member 3 (#4) |
| "Fewer and smaller enablers score higher" | Scientific honesty is 15 marks | - | Each has a stated bound and a reason; we do not claim the energy bonus | Holds | Member 3 |
| The official benchmarks | Validation is 20 marks; judges may change inputs | `uv run python -m sim.benchmarks`; runs on every pull request | All ten pass; inputs can be changed from the command line | Holds | Member 5 (#10) |
| The 10,000-year deadline | A winning condition | Arrival year is a flag | Earth arrives in year 8,699 | Holds | Ashish |
| "About 2.7 AU" | Exact target and tolerance | Million-year runs | Earth's orbit stays 2.699 to 2.703 AU | Holds | Ashish |
| Moving Mars may be questioned | The brief protects Earth and life | Journey without Mars's tow | Without it Earth passes Mars at about 33,000 km; Mars has no known life | Ask organisers | Ashish |
| Deliverables | Report (8 pages at most), momentum record, video (3 minutes), deck (7 minutes) | Issues #11, #15, #16 | - | Open | Member 5, Ashish |

## The tow machine

| Risk | Why it matters | How we check | Counter | Status | Owner |
| --- | --- | --- | --- | --- | --- |
| **Beam outage: the asteroid falls toward Earth** | A lost asteroid passes about 15,000 km from Earth, tides about 90 times the Moon's | `sim/scenarios/outage.py`, worst phase (Mars's tow also running) | Shared E1 budget, structures sized for full power, E1 as independent stations. Holds through: full blackout 15 hours; half the stations down 1.25 days; a quarter down 2.8 days (was 3 hours) | Fixed, with a requirement: no single fault over a quarter of E1, faults answered within 12 hours | Member 3 |
| Mars tow outage | Its asteroid would fall onto Mars | Same test, Mars's tow | Full blackout 13 hours; half the stations 1.8 days; a quarter down: holds. During its 4x sprint (a few decades) the asteroid is closer, so a blackout must be answered faster (not yet measured) | Open (sprint case) | Member 3 |
| Too little spare power | Steady need 8.37e25 W against an old cap of 8.5e25 W | Outage runs | Shared budget: 9% spare while Mars tows, 19% after, about a third during Mars's sprint (Earth's tow eases off) | Fixed | Ashish |
| Structures too weak at full power | Recovery after a fault needs full power | `test_structures_hold_at_the_most_the_beam_can_push` | Earth tow sized for 1e26 W (cables 10.5 km2, anchor 10,500 km2, mirror radius 2,600 km); Mars tow for 4e25 W (4.2 km2, 4,200 km2, 1,650 km) | Fixed | Member 3 (#5) |
| Beam passes near Earth or the Moon | 1e26 W of light must not cross the Earth-Moon system | Every check: at least 420,000 km from Earth | Light arrives up to 30 degrees off the Sun line when needed | Holds | Ashish |
| Asteroid drifts off its spot | Large drift is how a loss starts | Under 1% of its distance, every check | 10-day controller; trim and sprint motion fed forward and ramped | Holds | Ashish |
| **Forces not booked with their reactions** | A winning condition; the guide's ledger check | `ledger.checks`, exact fractions | Bodies' momentum change equals the applied impulse to 1.9e-21 of it; applied impulse plus its partners to 4.7e-16 (limit 1e-9). Was 1.2e-8 before the stepper kept its rounding | Fixed | Ashish (#16) |
| Tow mirror waste heat at Earth | Extra heating | Under 0.5% of sunlight | About 0.24% | Holds | Member 2 |

## Earth's safety

| Risk | Why it matters | How we check | Counter | Status | Owner |
| --- | --- | --- | --- | --- | --- |
| The tow pulls the Moon away | The guide: "simulate the Moon and check it stays bound" | 50-year Earth-Moon-asteroid-Sun runs at start, middle, end; the Moon's share of Earth's Hill sphere every check | Distance changes under 0.05%; the Moon sits at 0.26 of the Hill radius today and 0.095 at 2.7 AU (more tightly held) | Holds | Member 2 |
| **Climate: the guide forbids assuming it** | Without help Earth would reach about 155 K (equilibrium) | `sim/habitability.py`: mirrors built in 25-year batches, sunlight and temperature from the energy balance | Sunlight within about 1% of today's; temperature within about 0.6 K of 288 K (final numbers: `results/summary.json`, climate). Mirrors up to 8.6e8 km2 (E3 limit 1e9) | Covered (E3) | Member 2 (#1) |
| Liquid water | Oceans must not freeze | Mean temperature above 273 K, every check | Held | Holds | Member 2 |
| Air | The guide asks for it | Not yet a computed check | Escape speed unchanged; colder and weaker solar wind mean slower escape; Member 2 adds the check | Open | Member 2 (#1) |
| Magnetic shielding | Solar wind and radiation | Magnetopause distance every check | Grows from 10 to 13.9 Earth radii as the solar wind weakens | Holds | Member 2 |
| **Asteroid impacts in the belt** | 2.7 AU is inside the main belt | 1,000 test asteroids on real orbits (JPL Small-Body Database), scaled to 1.2 million over 1 km | Without defence: one 1 km impact per about 130 years while crossing and 70 once parked (natural: one per 500,000). E1 nudges each one heading for Earth: 5 cm/s ten years ahead, about 1e14 W for a day | Covered (E1), said up front | Member 2 (#2) |
| **Big asteroids pass near Earth** | Ceres, Pallas, Vesta, Hygiea cross or touch the new orbit; today: none within 0.01 AU in a million years | Million-year runs log every pass; journey checks 0.02 AU | Journey: closest 0.068 AU (Vesta). Million years: 7 to 48 passes within 0.01 AU (three copies); each nudged 50 years ahead with at most 1.1 hours of a 1e25 W beam | Covered (E1) | Member 2 (#2) |
| **Axial tilt (seasons)** | At 2.7 AU Earth's axis turns at about 35 arcsec a year, near the 26 arcsec a year at which Jupiter and Saturn tip every orbit (s6) | `sim/spin.py` on the real spin axis from today; X9 reproduces today's 22.1 to 24.5 degrees | Plane trim onto the forced plane: swing 21.7 to 26.1 degrees (2.0 times today's; untrimmed 15 to 28). The rest: the sunlight mirrors re-aim about 1.4% of the light to keep today's seasons (the real Earth's own swing moves 0.7%) | Fixed in part; rest Covered (E3) | Ashish, Member 2 |
| Eccentricity: sunlight swinging through the year | Untrimmed, Earth drifts to 0.09 at 2.7 AU | Million-year runs | Shape trim onto the forced 0.03: at most 0.059 over a million years (real Earth 0.051; limit 0.07) | Fixed | Ashish |

## Orbits and other bodies

| Risk | Why it matters | How we check | Counter | Status | Owner |
| --- | --- | --- | --- | --- | --- |
| Earth meets Mars on the way | Earth crosses Mars's old orbit | Journey with and without Mars's tow | Mars moves first; closest 0.37 AU | Fixed | Ashish |
| **Mars's parking orbit** | At 3.0 and 3.1 AU Jupiter throws Mars onto Earth-crossing orbits; at 3.4 AU, next to Earth's new 7:5 resonance, it drifts until the orbits cross | Parking scans (`results/parking_scan*.json`) | Park at 3.64 AU, between every resonance with Jupiter and with Earth; gap to Earth's orbit at least 0.39 AU over a million years | Fixed | Ashish |
| **Jupiter's 2:1 resonance catches Mars on the way** | At the normal pull it caught Mars in 6 of 8 trials | `sim/scenarios/crossing.py` (`results/crossing.json`) | Mars's tow sprints at 4 times the pull across 3.0 to 3.5 AU while Earth's tow eases off: caught 0 of 8 at 3.3 and at 4.9 times; in the final run Mars parked at 3.6405 AU in year 5,147 | Fixed | Ashish |
| Jupiter | Earth ends 2.5 AU from it | Closest pass; million years | Earth's orbit holds 2.699 to 2.703 AU | Holds | Ashish |
| Chaos: one million-year run could be luck | Planetary systems are chaotic | Three copies, Earth moved 1 km two ways (`results/longterm_chaos_copies.json`) | All three: 0 unresolved flags, near-identical ranges | Holds | Ashish |
| Big asteroids thrown out | Shows the moved Earth and Mars stir the belt | Million-year runs log escapes | Ceres and Hygiea are thrown out of the solar system within a million years in the main copy (Hygiea in one other); harmless to Earth, and fewer big asteroids to nudge | Holds | Ashish |

## Code and validation

| Risk | Why it matters | How we check | Counter | Status | Owner |
| --- | --- | --- | --- | --- | --- |
| Official benchmarks fail with changed inputs | Judges may change them | `sim/benchmarks.py` takes inputs from the command line | All ten pass; Member 5 tries changed inputs | Open (to try) | Member 5 (#10) |
| Step size | "Halve the time step and show the answer does not change" | Journey at 1 day and 0.5 day | Earth arrives in year 8,542.6 against 8,549.3, orbit 2.7005 against 2.7004 AU. Mars's crossing is chaotic at either step, which is why it now sprints | Holds | Ashish |
| Integrator wrong | Everything rests on it | Official benchmarks 4 to 8; X6 against REBOUND | Pass | Holds | Member 5 |
| Tilt model wrong | The seasons finding rests on it | X9: real solar system, 50,000 years | 22.5 to 24.0 degrees (known 22.1 to 24.5) | Holds | Member 5 |
| Belt sample unlike the real belt | Our first sample was too cold | Compared with 20,000 real orbits | Sample drawn from real orbits | Fixed | Member 2 |
| A climate bug | The mirror schedule's 100-day growth estimate overbuilt mirrors (sunlight up to 11% high) | Final-run flags | Growth estimated over whole 25-year batches; replayed on the final trajectory: within 0.9% and 0.6 K | Fixed | Ashish |
| Runs are slow | Journey about 70 minutes with the exact ledger and the belt | Timings in logs | Start long runs early; `--no-belt` saves about 15 minutes | Open | Ashish |

## Decisions and questions

**Decided from the runs:** Mars parks at 3.64 AU and sprints across Jupiter's 2:1 resonance while Earth's tow eases
off; Earth arrives on the orbit shape and plane Jupiter forces at 2.7 AU (arrival trim); the stepper keeps its
rounding so the ledger meets the guide's form; the climate is computed from a mirror build schedule.

**For the organisers:** (1) Where is the rulebook's safety appendix? (2) Is a team of 5 allowed? (3) May we move
Mars? (4) Does asteroid defence count within a declared enabler? (5) Is there a limit on axial tilt or seasons?
