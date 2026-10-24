# Questions the judges may ask, and our answers

Five minutes of questions follow the pitch. Each question has a one-line answer to say first and, under it, more
if they ask. The member named answers first, but everyone should be able to give every answer: the guide says
"Every member should be able to explain the code and the physics." Every number comes from `results/`
(`tests/test_report.py` checks them); say where it comes from if asked.

Who: **Ashish** (physics core), **Member 2** (safety and environment), **Member 3** (structures and enablers),
**Member 4** (3D test bench), **Member 5** (validation and pitch).

## The concept

**1. Is the asteroid's pull really an outside force?** *(Ashish)*
Yes: the asteroid is a separate body outside Earth, and every push in the system is booked with its partner.
More: its gravity pulls Earth with 3.95 × 10^17 N and Earth pulls it back just as hard. Light on its mirror
balances that pull, and the light's partners, the stations' recoil and the light that leaves, are in the ledger.

**2. Why doesn't the asteroid fall onto Earth?** *(Ashish)*
The beam holds it on its spot: it never strayed more than 2,715 km (0.4%) from it.
More: a controller with a 10-day response asks for exactly the force the spot needs. If every station goes dark
at once, the Earth tow still recovers after 15 hours; with half the stations up, after 1.25 days.

**3. Where does a 4 × 10^20 kg asteroid come from?** *(Member 3)*
Placing it is our enabler E3, planet-scale space manufacturing, bounded at 4 × 10^20 kg per asteroid.
More: ours is 3.97 × 10^20 kg; for scale, Vesta is 2.6 × 10^20 kg and Ceres 9.4 × 10^20 kg. Mars's tow uses
1.56 × 10^20 kg.

**4. Why move Mars?** *(Ashish)*
Earth's path from 1 to 2.7 AU crosses Mars's orbit, so Mars goes first, to 3.64 AU in year 5,168.
More: 3.64 AU sits between the resonances with Jupiter and with Earth. Crossing Jupiter's 2:1 resonance at the
normal pull, Mars was caught in 6 of 8 trials; its tow sprints across instead (caught in 0 of 8). The two planets
are never closer than 0.37 AU, an ordinary opposition at the start.

**5. Why 45 degrees, ahead and out?** *(Ashish)*
Light can only push, so the beam comes from the Sun's side, and at 45 degrees the pull along Earth's orbit per
watt of light is largest.
More: the asteroid sits 637,100 km from Earth at 45 degrees between straight ahead along the orbit and straight
out from the Sun; light may arrive up to 30 degrees off the Sun line to keep clear of Earth.

## Power and energy

**6. 10^26 W is a quarter of the Sun's output. Isn't that absurd?** *(Member 3)*
It is our biggest assumption, declared as enabler E1 with a hard limit of 10^26 W; the run peaked at
9.27 × 10^25 W.
More: light carries little momentum for its energy (1.41 P/c with our 45 degree bounce), so holding a
3.95 × 10^17 N load takes about 8.4 × 10^25 W, while the planets gain only 1.8 × 10^33 J of orbital energy over
8,758 years (6.5 × 10^21 W on average). We do not claim the energy bonus.

**7. Where does the beam's waste heat go?** *(Member 3)*
The mirror absorbs 10^-7 of the light and radiates it from both faces: 1,466 K at the power cap, under E2's
1,500 K.
More: the stations radiate their own waste heat; E1 is declared that way.

**8. Could the beam hit Earth?** *(Member 2)*
No beam may pass within 420,000 km of Earth, beyond the Moon's farthest point; the closest any came was
448,909 km.
More: light may arrive up to 30 degrees off the Sun line, which is how the beam keeps clear.

## Earth, the Moon and the belt

**9. Does Earth freeze at 2.7 AU?** *(Member 2)*
Not with the sunlight mirrors (E3): the temperature stays between 287.8 and 288.8 K the whole way.
More: without them our climate model gives 150 K and no liquid water, as the company's demo does. The mirrors,
built in 25-year batches up to 8.5 × 10^8 km², keep Earth's sunlight between 0.995 and 1.010 of today's.

**10. Does the Moon stay with Earth?** *(Member 2)*
Yes: the Moon sits at 0.256 of Earth's Hill radius at the start and 0.095 at 2.7 AU (limit 0.49).
More: the Hill sphere grows as Earth moves out. The tow's pull is at most 0.0020 of Earth's pull on the Moon
(limit 0.01). The Moon test (`sim/scenarios/moon.py`) follows the Moon itself at the start, middle and end.

**11. Does the asteroid's tide slow Earth's spin?** *(Member 2)*
Barely: it lengthens the day by about 2.1 × 10^-7 s over the whole journey (limit 1 s).
More: tide goes as mass over distance cubed, so the asteroid's is 0.12% of the Moon's.

**12. What happens to the seasons?** *(Member 2)*
Earth's axial tilt would swing 21.7 to 26.1 degrees over a million years (today 22.2 to 24.4), so the sunlight
mirrors re-aim 1.4% of Earth's sunlight to keep today's seasons.
More: at 2.7 AU Earth's spin precession runs close to a slow mode of the planets' orbits, which widens the swing;
the arrival trim already narrowed it from 15 to 28 degrees.

**13. Isn't 2.7 AU inside the asteroid belt?** *(Member 2)*
Yes: crossing it, Earth would meet a 1 km asteroid about once every 127 years, so E1 nudges each one 5 cm/s
aside, ten years ahead.
More: parked at 2.7 AU it is once every 87 years, against once per 500,000 today (from 1,000 real belt orbits,
JPL). Each nudge is a 1.1 × 10^14 W beam for a day. Of the big asteroids, Vesta comes closest (0.018 AU), and is
nudged with 3 minutes of beam.

**14. Do the structures hold?** *(Member 3)*
Yes: every structure keeps a safety factor of at least 1.57 at the full power cap (required 1.5).
More: cables and anchors are sized for the most a beam can ever push, 2P/c at the cap, so recovering after an
outage is covered. The cables are E2 material (100 GPa); the asteroid itself has a safety factor of 120 against
the planet's uneven pull across it.

## Numerics and honesty

**15. How do you know the result is not tuned?** *(Member 5)*
Every number comes from the running model, is written to `results/`, and a test checks each number in the report
against those files.
More: the README table and the momentum record are generated from `results/`. The ten benchmarks run as tests on
every pull request, and any input can be changed live: `uv run python -m sim.benchmarks 4 --set e=0.5`.

**16. Does the answer change with the step size?** *(Member 5)*
Barely: halving the step to half a day, the final design reaches each orbit size within 3 to 10 years of the
1-day run, so far up to year 8,556 (29 years at 2.5 AU, within the logs' sampling).
More: on an earlier version of the design the full half-step run moved arrival by 7 years in about 8,550. Give the
final design's number if its run has finished (`docs/status.md`).

**17. How is momentum conserved so exactly?** *(Ashish)*
Each pair's gravity is computed once and applied as exact negatives, and every push is added with an error-free
compensated sum.
More: the guide's two checks close to 5.5 × 10^-22 and 5.6 × 10^-16 of the applied impulse (limit 10^-9); the
beams' work matches the energy gained to 0.007%.

**18. Why not Octo-Earth?** *(Member 3)*
Its arms push on Earth's field, whose source is Earth's own core: the two forces cancel to 3.7 × 10^-12, so Earth
does not move.
More: and the arms cannot stand: a 12,000 km arm buckles under its own weight past 471 km in steel and
1,444 km in ideal nanotube.

**19. What would break your design?** *(Member 5)*
The power (E1) and building at planet scale (E3); physically, the closest calls were Jupiter's 2:1 resonance, a
long beam outage and 1 km asteroids in the belt.
More: each has a counter with a number: Mars's sprint (caught in 0 of 8), a 15-hour total blackout as the margin,
and E1's nudges (one 1 km asteroid every 127 years without them).

**20. What would you test next?** *(Member 5)*
The Moon as its own body inside the journey, a latitude-resolved climate, and a sweep of tow mass and distance.
More: also the rulebook's safety thresholds once the organisers publish them: a number change in `config.yaml`
and a re-run.

## The code

**21. Is the 3D test bench the real result, or an animation?** *(Member 4)*
It replays the model's saved runs (`results/run.json`); it computes nothing itself, and every check beside the
view comes from `results/`.
More: sizes are drawn larger so they can be seen, with the factors printed on screen, and a True scale switch
shows real sizes. It is at [ashish000011.github.io/black-ant](https://ashish000011.github.io/black-ant/).

**22. Can we run it?** *(Member 5)*
Yes: `uv sync`, then `uv run python -m sim.benchmarks` (about 12 seconds) and `uv run pytest -m "not slow"`
(about a minute).
More: the full journey takes about an hour and a half (`uv run python -m sim.scenarios.tow --out results`); the
test bench replays the saved runs in the browser.
