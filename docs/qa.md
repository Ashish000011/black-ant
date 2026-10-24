# Questions the judges may ask, and our answers

Five minutes of questions follow the pitch. Every number here comes from `results/`; say where it comes
from if asked. Short answer first, then the detail if they want it.

## The concept

**Is the asteroid's pull really an outside force?**
Yes. The asteroid is not part of Earth. Its gravity pulls Earth (3.95 x 10^17 N) and Earth pulls it back with
the same force. That pull on the asteroid is balanced by light pushing on its mirror, and the light's partners
are the beam stations (they recoil) and the light itself (it carries momentum away). All of it is in the ledger.

**Why doesn't the asteroid fall onto Earth?**
The beam holds it on its spot. A controller with a 10-day response asks for exactly the force the spot needs;
the asteroid never strayed more than 2,715 km (0.4%) from it. If every station goes dark at once, the Earth tow
still recovers after 15 hours; with half the stations up, 1.25 days.

**Where does a 4 x 10^20 kg asteroid come from?**
That is enabler E3 (planet-scale space manufacturing). For scale: Vesta is 2.6 x 10^20 kg, Ceres 9.4 x 10^20 kg.
Mars's tow uses 1.56 x 10^20 kg.

**Why move Mars?**
Earth's path from 1 to 2.7 AU crosses Mars's orbit. Mars is towed first to 3.64 AU, between the resonances
with Jupiter and with Earth. The two planets are never closer than 0.37 AU (an ordinary opposition, at the start).

**Why 45 degrees, ahead and out?**
Light can only push. The beam comes from the Sun's side; at 45 degrees the pull along Earth's orbit per watt of
light is largest.

## Power and energy

**10^26 W is a quarter of the Sun's output. Isn't that absurd?**
It is our biggest assumption, declared as E1 and bounded by a hard limit in the code. Light carries little
momentum for its energy (F = 2P/c at best; 1.41 P/c with our 45 degree bounce), so holding a 3.95 x 10^17 N
load takes about 8.4 x 10^25 W, even though Earth itself only gains 1.8 x 10^33 J over 8,758 years
(6.5 x 10^21 W on average). We do not claim the energy bonus.

**Where does the beam's waste heat go?**
The mirror absorbs 10^-7 of the light (E2) and radiates it from both faces: 1,466 K at the power cap, under
E2's 1,500 K. The stations radiate their own waste heat; E1 is declared that way.

**Could the beam hit Earth?**
No beam comes within 420,000 km of Earth, beyond the Moon's farthest point; light may arrive up to 30 degrees
off the Sun line to keep clear. The closest any beam came was 448,909 km.

## Earth and the Moon

**Does Earth freeze at 2.7 AU?**
Without help, yes: our climate model gives 150 K and no liquid water, the same as the company's demo. Mirrors
in space (E3), built in 25-year batches up to 8.5 x 10^8 km^2, keep Earth's sunlight within 1% of today's.
The temperature stays between 287.7 and 288.7 K.

**Does the Moon stay with Earth?**
Yes. The Moon's distance is 0.26 of Earth's Hill radius at the start and 0.095 at 2.7 AU (limit 0.49): the
Hill sphere grows as Earth moves out. The tow's thrust is 0.2% of Earth's pull on the Moon (limit 1%). The Moon
test (`sim/scenarios/moon.py`) follows the Moon itself at the start, middle and end.

**Tides from the asteroid?**
Tide goes as mass over distance cubed: the asteroid's is 0.12% of the Moon's. It lengthens the day by about
2 x 10^-7 s over the whole journey (limit 1 s).

**Seasons?**
Earth's axial tilt swings 21.7 to 26.1 degrees over a million years at 2.7 AU (today 22.2 to 24.4), because
there its spin precession runs close to a slow mode of the planets' orbits. The sunlight mirrors re-aim 1.4% of
Earth's sunlight to keep today's seasons (E3).

## Numerics and honesty

**How do you know the result is not tuned?**
Every number comes from the running model and is written to `results/`; the README table and the momentum
record are generated from those files. The ten benchmarks run as tests on every pull request, and any input
can be changed live: `uv run python -m sim.benchmarks 4 --set e=0.5`.

**Does the answer change with the step size?**
Halving the step (1 day to 0.5 days) moves Earth's arrival year by a few years in 8,758. [Final number from
`out/half_final`, once that run finishes.]

**How is momentum conserved so exactly?**
Each pair's gravity forces are computed once and applied as exact negatives, and every push is added with an
error-free (two-sum) compensated sum. The guide's two checks close to 5.5 x 10^-22 and 5.6 x 10^-16 (limit 10^-9).

**Why not Octo-Earth?**
Its arms push on Earth's field, whose source is Earth's own core: we compute both forces and they cancel to
3.7 x 10^-12. And a 12,000 km arm buckles under its own weight past 471 km in steel, 1,444 km in ideal nanotube.

**What would break your design?**
The power (E1) and building at planet scale (E3). Physically, the closest calls were Mars caught by Jupiter's 2:1
resonance (fixed with the sprint), the asteroid lost during a long outage (15 hours of total blackout is the
margin), and 1 km asteroids in the belt (one every 127 years without E1's nudges).

## The code

**Can we run it?**
`uv sync`, then `uv run python -m sim.benchmarks` (12 s) and `uv run pytest -m "not slow"` (about a minute).
The full journey takes about an hour; the test bench (`viewer/`) replays the saved runs in the browser.
