# Black Ant risk register

Every way the Earth tow could fail, how we check it, and what we did about it. Status words: **Holds** (checked,
passes), **Fixed** (failed, countered, re-checked), **Covered (E1/E2/E3)** (relies on a declared enabler, with
numbers), **Open**, **Ask organisers**. Numbers come from `results/` (the final run of 24 October) unless stated.
Rules: the participant guide (Planetary Propulsion Hackathon); see `docs/problem.md` and `docs/enablers.md`.

## Rules and scope

| Risk | Why it matters | How we check | Counter | Status | Owner |
| --- | --- | --- | --- | --- | --- |
| The rulebook's safety appendix (the thresholds) is still not published | "Every threshold in the rulebook appendix" is a winning condition | Every limit sits in `config.yaml` with its source | Adopted the ten thresholds of the company's reference demo (octo-earth-simulator.vercel.app), checked every 100 days; if the rulebook differs, change the numbers and re-run | Holds (ask to confirm) | Member 5 (#9) |
| Team size: the guide said 2 to 4 members; we are 5 | Could affect eligibility | Asked the organisers | Five members are allowed (the rule was added after the guide) | Holds | Ashish |
| Enablers are fixed at the mid-point check-in | They cannot change afterwards | `docs/enablers.md`; every use is a flag naming its enabler | Three enablers, each bounded and matched to an allowed kind; E1 no longer claims to cancel its own recoil (it is booked) | Ready to declare | Member 3 (#4) |
| "Fewer and smaller enablers score higher" | Scientific honesty is 15 marks | - | Each has a stated bound and a reason; we do not claim the energy bonus | Holds | Member 3 |
| The official benchmarks | Validation is 20 marks; judges may change inputs | `uv run python -m sim.benchmarks`; runs on every pull request | All ten pass; inputs can be changed from the command line | Holds | Member 5 (#10) |
| The 10,000-year deadline | A winning condition | Arrival year is a flag | Earth arrives in year 8,758 | Holds | Ashish |
| "About 2.7 AU" | Exact target and tolerance | Million-year runs | Earth's orbit stays 2.698 to 2.702 AU | Holds | Ashish |
| Moving Mars may be questioned | The brief protects Earth and life | Journey without Mars's tow | Without it Earth passes Mars at about 33,000 km; Mars has no known life | Ask organisers | Ashish |
| Deliverables | Report (8 pages at most), momentum record, video (3 minutes), deck (7 minutes) | Issues #11, #15, #16 | Report drafted (14 sections, two figures), `docs/momentum-record.md`, demo video (2 min 20 s), 13-slide deck, `docs/qa.md`, test bench (`viewer/`) | Drafted; review before submitting | Ashish |
| The reference concept left unexamined | Judges expect Octo-Earth judged with numbers, not dismissed | `sim/scenarios/octo.py`, test X8 | Core field on the arms and arms on the core cancel to 3.7e-12; closed circuits in a 0.5 nT field feel nothing; a 12,000 km arm buckles past 471 km (steel), 1,444 km (nanotube) | Holds | Ashish (#6, #12) |
| Visualisation and usability (10 marks) | Judges must see real against enlarged sizes, and every check | `viewer/`: 3D views, scale labels, ten experiments, nine results tabs | Built; published on GitHub Pages from `main` | Holds once merged | Ashish (#7, #8) |

## The tow machine

| Risk | Why it matters | How we check | Counter | Status | Owner |
| --- | --- | --- | --- | --- | --- |
| **Beam outage: the asteroid falls toward Earth** | A lost asteroid passes about 15,000 km from Earth, tides about 90 times the Moon's | `sim/scenarios/outage.py`, worst phase (Mars's tow also running) | Shared E1 budget, structures sized for full power, E1 as independent stations. Holds through: full blackout 15 hours; half the stations down 1.25 days; a quarter down 2.8 days (was 3 hours) | Fixed, with a requirement: no single fault over a quarter of E1, faults answered within 12 hours | Member 3 |
| Mars tow outage | Its asteroid would fall onto Mars | Same test, Mars's tow | Full blackout 4.75 days; half or a quarter of the stations down: 8+ days. During its 4x sprint (a few decades, asteroid at 200,000 km): full blackout 10.5 hours, half down 20 hours. Earth's tow, eased off meanwhile: 3.4 days | Fixed, with a requirement: during Mars's sprint, faults answered within 8 hours | Member 3 |
| Too little spare power | Steady need 8.37e25 W against an old cap of 8.5e25 W | Outage runs | Shared budget: 9% spare while Mars tows, 19% after, about a third during Mars's sprint (Earth's tow eases off) | Fixed | Ashish |
| Structures too weak at full power | Recovery after a fault needs full power | `test_structures_hold_at_the_most_the_beam_can_push` | Earth tow sized for 1e26 W (cables 10.5 km2, anchor 10,500 km2, mirror radius 2,600 km); Mars tow for 4e25 W (4.2 km2, 4,200 km2, 1,650 km); Mars's asteroid now 1.6e20 kg at 400,000 km | Fixed | Member 3 (#5) |
| Beam passes near Earth or the Moon | 1e26 W of light must not cross the Earth-Moon system | Every check: at least 420,000 km from Earth | Light arrives up to 30 degrees off the Sun line when needed | Holds | Ashish |
| Asteroid drifts off its spot | Large drift is how a loss starts | Under 1% of its distance, every check | 10-day controller; trim and sprint motion fed forward and ramped | Holds | Ashish |
| **Controller weaker than the pull's gradient** | A hovering asteroid is an unstable balance; at 100,000 km from Mars the pull's gradient worked on a 1.25-day timescale and the controller was only 0.62 times as strong (0.08 in the sprint), so Mars's asteroid held only through an exact model | New checks every 100 days: controller at least 3 times the gradient; step at least 3 times shorter than its timescale | Mars's asteroid 16 times heavier (1.6e20 kg) at 400,000 km, the same pull: 39 times the gradient (4.9 in the sprint), timescale 10 days (3.5 in the sprint). Earth's tow: 17 times, 6.5 days | Fixed | Ashish |
| **Forces not booked with their reactions** | A winning condition; the guide's ledger check | `ledger.checks`, exact fractions | Bodies' momentum change equals the applied impulse to 5.5e-22 of it; applied impulse plus its partners to 5.6e-16 (limit 1e-9). Was 1.2e-8 before the stepper kept its rounding | Fixed | Ashish (#16) |
| Tow mirror waste heat at Earth | Extra heating | Under 0.5% of sunlight | About 0.24% | Holds | Member 2 |

## Earth's safety

| Risk | Why it matters | How we check | Counter | Status | Owner |
| --- | --- | --- | --- | --- | --- |
| The tow pulls the Moon away | The guide: "simulate the Moon and check it stays bound" | 50-year Earth-Moon-asteroid-Sun runs at start, middle, end; the Moon's share of Earth's Hill sphere every check | Distance changes under 0.05%; the Moon sits at 0.26 of the Hill radius today and 0.095 at 2.7 AU (more tightly held) | Holds | Member 2 |
| **Climate: the guide forbids assuming it** | Without help Earth would reach 150 K with no liquid water (our model and the demo's agree) | `sim/habitability.py`: mirrors built in 25-year batches; energy balance with ice-albedo feedback; the demo's ten thresholds every 100 days | Sunlight 0.995 to 1.010 of today's; temperature 287.8 to 288.8 K over the whole journey. Mirrors up to 8.5e8 km2 (E3 limit 1e9) | Covered (E3) | Member 2 (#1) |
| Night sky about 7 times darker | The Moon moves with Earth: full-Moon light falls to 0.034 lux at 2.7 AU, 13.7% of today's 0.25; the sunlight mirrors aim at Earth, not the Moon | `sim/night.py`, `tests/test_night.py` (formulas, not in the saved run) | Moon reflectors inside E3: about 3,335 km2 of flat mirrors on the near side bring back 0.25 lux over the night side (E3 has 1.5e8 km2 spare; the area is up to about 2x conservative). Lit from first to last quarter only (45% over a month), so the monthly cycle stays. Even the whole near side (9.5e6 km2) gives at most 6.6 W/m2, 0.31 K: the sunlight mirrors carry the climate | Covered (E3), optional | Member 2 |
| Liquid water | At least 30% of the surface (the demo's threshold) | Share of the surface above 273 K from a latitude profile calibrated to today's 82% | Stays at about 81 to 83% | Holds | Member 2 |
| Air | Surface pressure at least 50 kPa; N2 kept (Jeans lambda over 30) | Jeans parameter every check, exosphere temperature scaling with sunlight | Nothing removes air; lambda stays near 195 (limit 30) | Holds | Member 2 (#1) |
| Day length | Changed by at most 1 s (the demo's threshold) | The tow asteroid's tidal torque on Earth, added up every check | About 2e-7 s over the whole journey: nothing touches Earth | Holds | Member 2 |
| Runaway greenhouse | Absorbed sunlight under 282 W/m2 | Every check | About 238 to 241 W/m2 | Holds | Member 2 |
| The tow outpulls the Moon's hold | Thrust under 0.01 of Earth's pull on the Moon | Every check | 0.0020 | Holds | Member 2 |
| Magnetic shielding | At least 3 Earth radii (the demo's threshold) | Magnetopause distance every check | Grows from 10 to 13.9 Earth radii as the solar wind weakens | Holds | Member 2 |
| **Asteroid impacts in the belt** | 2.7 AU is inside the main belt | 1,000 test asteroids on real orbits (JPL Small-Body Database), scaled to 1.2 million over 1 km | Without defence: one 1 km impact per about 127 years while crossing and 87 once parked (natural: one per 500,000). E1 nudges each one heading for Earth: 5 cm/s ten years ahead, about 1e14 W for a day | Covered (E1), said up front | Member 2 (#2) |
| **Big asteroids pass near Earth** | Ceres, Pallas, Vesta, Hygiea cross or touch the new orbit; today: none within 0.01 AU in a million years | Million-year runs log every pass; journey checks 0.02 AU | Journey: Vesta passes twice at 0.018 AU, inside our 0.02 AU limit; each nudged 50 years ahead with 0.06 hours of a 1e25 W beam. Million years: 23 to 45 passes within 0.01 AU (three copies), each nudged with at most 0.6 hours | Covered (E1) | Member 2 (#2) |
| **Axial tilt (seasons)** | At 2.7 AU Earth's axis turns at about 35 arcsec a year, near the 26 arcsec a year at which Jupiter and Saturn tip every orbit (s6) | `sim/spin.py` on the real spin axis from today; X9 reproduces today's 22.1 to 24.5 degrees | Plane trim onto the forced plane: swing 21.7 to 26.1 degrees (2.0 times today's; untrimmed 15 to 28). The rest: the sunlight mirrors re-aim about 1.4% of the light to keep today's seasons (the real Earth's own swing moves 0.7%) | Fixed in part; rest Covered (E3) | Ashish, Member 2 |
| Eccentricity: sunlight swinging through the year | Untrimmed, Earth drifts to 0.09 at 2.7 AU | Million-year runs | Shape trim onto the forced 0.03: at most 0.060 over a million years (real Earth 0.051; limit 0.07) | Fixed | Ashish |

## Orbits and other bodies

| Risk | Why it matters | How we check | Counter | Status | Owner |
| --- | --- | --- | --- | --- | --- |
| Earth meets Mars on the way | Earth crosses Mars's old orbit | Journey with and without Mars's tow | Mars moves first; closest 0.37 AU | Fixed | Ashish |
| **Mars's parking orbit** | At 3.0 and 3.1 AU Jupiter throws Mars onto Earth-crossing orbits; at 3.4 AU, next to Earth's new 7:5 resonance, it drifts until the orbits cross | Parking scans (`results/parking_scan*.json`) | Park at 3.64 AU, between every resonance with Jupiter and with Earth; gap to Earth's orbit at least 0.36 AU over a million years | Fixed | Ashish |
| **Jupiter's 2:1 resonance catches Mars on the way** | At the normal pull it caught Mars in 6 of 8 trials | `sim/scenarios/crossing.py` (`results/crossing.json`) | Mars's tow sprints at 4 times the pull across 3.0 to 3.5 AU while Earth's tow eases off: caught 0 of 8 at 3.3 and at 4.9 times, and 0 of 8 again with the asteroid at 400,000 km (sprinting to 200,000) | Fixed | Ashish |
| Swapping Earth and Mars left unexamined (Plan S) | Towing Mars in to 1 AU takes 5.66 km/s (out to 3.64 AU: 8.52) and never meets Jupiter's 2:1 resonance | `sim/scenarios/swap.py`: 48 crossing runs (Mars's orbit as today or round, normal pull or 4x, 12 starts each); the end state for a million years (5 runs); a swap by gravity (`--handover`) | The orbits must cross (about 1.22 AU, year 1,940): every run passes inside the 0.05 AU limit, 2 to 99 times, closest 0.0018 to 0.045 AU, 2 of 48 inside the Moon's distance; no collisions. End state stable, orbit gap 1.39 to 1.46 AU (design 0.55 set up the same way). The gravity handover holds 0.37 AU, but restarting the tows passes 45,000 to 90,000 km apart (0.026 AU with Mars's tow at 4x). Design kept | Studied, not adopted | Member 1 |
| Jupiter | Earth ends 2.5 AU from it | Closest pass; million years | Earth's orbit holds 2.698 to 2.702 AU | Holds | Ashish |
| Chaos: one million-year run could be luck | Planetary systems are chaotic | Three copies, Earth moved 1 km two ways (`results/longterm_chaos_copies.json`) | All three: 0 unresolved flags, near-identical ranges | Holds | Ashish |
| Big asteroids thrown out | Shows the moved Earth and Mars stir the belt | Million-year runs log escapes | Ceres is thrown out of the solar system in one of the three final copies (Ceres and Hygiea in earlier test runs); harmless to Earth, and fewer big asteroids to nudge | Holds | Ashish |

## Code and validation

| Risk | Why it matters | How we check | Counter | Status | Owner |
| --- | --- | --- | --- | --- | --- |
| Official benchmarks fail with changed inputs | Judges may change them | `sim/benchmarks.py` takes inputs from the command line; `tests/test_official_benchmarks.py` reruns 1-4 and 8-10 with changed inputs | Benchmark 4 failed at e = 0.7 (3e-6 a against 1e-6): its steps now scale with the pericentre's timescale, and it passes from e = 0 to 0.9. Benchmark 5 at coarser steps (0.5 days) misses 1e-9 (1.4e-9): the step is a method choice; at 0.25 days it passes for 5 and 20 years | Fixed | Ashish (#10) |
| Step size | "Halve the time step and show the answer does not change" | Journey at 1 day and 0.5 day | Earth arrives in year 8,542.6 against 8,549.3, orbit 2.7005 against 2.7004 AU (earlier design); the final design at 0.5 days is running. Mars's crossing is chaotic at either step, which is why it now sprints | Holds | Ashish |
| Integrator wrong | Everything rests on it | Official benchmarks 4 to 8; X6 against REBOUND | Pass | Holds | Member 5 |
| Tilt model wrong | The seasons finding rests on it | X9: real solar system, 50,000 years | 22.5 to 24.0 degrees (known 22.1 to 24.5) | Holds | Member 5 |
| Belt sample unlike the real belt | Our first sample was too cold | Compared with 20,000 real orbits | Sample drawn from real orbits | Fixed | Member 2 |
| A climate bug | The mirror schedule's 100-day growth estimate overbuilt mirrors (sunlight up to 11% high) | Final-run flags | Growth estimated over whole 25-year batches; final run: sunlight 0.995 to 1.010 of today's, temperature 287.8 to 288.8 K | Fixed | Ashish |
| Runs are slow | Journey about 70 minutes with the exact ledger and the belt | Timings in logs | Start long runs early; `--no-belt` saves about 15 minutes | Open | Ashish |

## Decisions and questions

**Decided from the runs:** Mars parks at 3.64 AU and sprints across Jupiter's 2:1 resonance while Earth's tow eases
off; Earth arrives on the orbit shape and plane Jupiter forces at 2.7 AU (arrival trim); the stepper keeps its
rounding so the ledger meets the guide's form; the climate is computed from a mirror build schedule.

**For the organisers:** (1) Are the reference demo's ten Earth-safety thresholds the rulebook appendix? (2) May we
move Mars? (3) Does asteroid defence count within a declared enabler? (4) Is there a limit on axial tilt or seasons?
Answered: a team of 5 is allowed.
