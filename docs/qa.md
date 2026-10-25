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
The rules allow it, and E3 places it. The participant guide (section 7) lists "access to an asteroid of stated mass"
among the allowed enablers, and E3 (planet-scale space manufacturing) declares it in `docs/enablers.md`: two
asteroids put on their starting spots, 3.97 x 10^20 kg for Earth's tow and 1.56 x 10^20 kg for Mars's, both under
a 4 x 10^20 kg bound. It need not be one body: E3 also declares "free raw material delivered where needed", so it
could be gathered from smaller belt asteroids. For scale: Vesta is 2.6 x 10^20 kg, Ceres 9.4 x 10^20 kg.
Bringing it in is not the hard part either. Coming in from the belt at 2.7 AU takes about 11.7 km/s (the gap
between the orbital speeds there and at 1 AU). At the best case, 2P/c, E1's 10^26 W pushes 6.7 x 10^17 N, or
1.7 x 10^-3 m/s^2 on 3.97 x 10^20 kg: about 80 days of push (114 days at our 45 degree bounce). That is only a
check on scale: in the run E3 places the asteroid at the start, and E1 delivers nothing.

**Why move Mars?**
Earth's path from 1 to 2.7 AU crosses Mars's orbit. Mars is towed first to 3.64 AU, between the resonances
with Jupiter and with Earth. The two planets are never closer than 0.37 AU (an ordinary opposition, at the start).

**Why not swap Earth and Mars?**
We studied it ("Plan S", `sim/scenarios/swap.py`) and kept the design: the end state is better, but no crossing we
tested stays outside our 0.05 AU limit. Towing Mars in to Earth's old orbit (1 AU) while Earth goes out would cost
Mars 5.66 km/s instead of 8.52, and Mars would never cross Jupiter's 2:1 resonance. But the two orbits must then
cross: their sizes meet around year 1,940, at about 1.22 AU. We ran the crossing 48 times (Mars's orbit as today or
made round, normal pull or the 4x sprint, 12 starting points each). Every run passes inside the limit (`config.yaml`,
`safety.mars_min_distance_au`), 2 to 99 times, and its closest pass is 0.0018 to 0.045 AU; 10 of 48 came within
1 million km, and 2 inside the Moon's distance. None collided, and Earth's eccentricity stayed at or below 0.026.
The swapped end state (Earth 2.7 AU, Mars 1.0 AU) is stable for a million years in 5 runs: Earth behaves as in the
design, and the gap between the two orbits is 1.39 to 1.46 AU against 0.55 AU for our design set up the same way
(`results/parking_scan3.json`; 0.36 AU after the full journey). A handover by gravity alone (tows off, the planets
nearly level and on opposite sides of the Sun, as Saturn's moons Janus and Epimetheus swap) keeps them at least
0.37 AU apart. Restarting the tows at the normal pull, though, makes them swap back and forth, passing 45,000 to
90,000 km apart; restarting with Mars's tow at 4x gives one clean swap, closest 0.026 AU (3.9 million km), still
under the limit. To run it: `uv run python -m sim.scenarios.swap`, with `--longterm 1e6` or `--handover 3000`
(written to `out/`, not `results/`).

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

## Moving things with light: is it real?

**Why not a Shkadov or Caplan thruster?**
Because they move the Sun, and Earth just comes along at 1 AU. Our job is to change Earth's distance from the Sun.
Both are stellar engines.
- A Shkadov thruster is a giant mirror hovering beside the Sun that sends sunlight back the way it came (Shkadov
  1987, IAA-87-613). Reflecting half the Sun's light back gives a thrust of about 10^18 N, so the Sun accelerates by
  under 10^-12 m/s^2 and moves a few hundredths of a light-year in a million years.
- A Caplan thruster (Caplan 2019, *Acta Astronautica* 165, 96-104, doi:10.1016/j.actaastro.2019.08.027) gathers
  fuel from the Sun and fires fusion jets. It reaches at most 10^-9 m/s^2: about 50 light-years in a million years.
  That is 1.7 x 10^-7 of the Sun's pull on Earth at 1 AU, so Earth's orbit barely notices.

**Where does E1's 10^26 W come from?**
From sunlight: 10^26 W is 26% of the Sun's output (3.828 x 10^26 W, IAU 2015). The natural source is a swarm of
mirrors near the Sun that catch sunlight and focus it onto the tow mirrors: a partial Dyson swarm. Caplan's thruster
assumes the same kind of sunlight collector, to focus sunlight onto the Sun. This is still our declared enabler E1.
The references show it belongs to a known class of ideas, not that anyone can build it.

**Can lasers really deflect asteroids?**
Yes, on paper. DE-STAR (Lubin et al. 2014, *Optical Engineering* 53(2), 025103; UC Santa Barbara) is a phased laser
array powered by sunlight. It heats a spot on an asteroid until the rock boils, and the vapour jet pushes the
asteroid like a rocket. Lubin et al. (SPIE 8876, 2013): "A DE-STAR 4 allows for asteroid engagement starting beyond
1AU with a spot temperature sufficient to completely evaporate up to 500-m diameter asteroids in one year." A
DE-STAR 4 is a 10 km array. This is E1's job against small rocks (`sim/scenarios/small_asteroids.py`). Boiling a
surface pushes far harder per watt than light pressure alone (P/c), which is all our script counts. So the "2% of
E1's spare power" for a 20 m rock is an upper bound.

**Has light pushing anything ever actually worked?**
Yes, in flight. The physics is the same as our beam's: F = 2P/c at best.
- JAXA's IKAROS sailed toward Venus on sunlight. JAXA measured 1.12 mN of light pressure on its 14 m sail on 9 July
  2010 ([JAXA press release](https://global.jaxa.jp/press/2010/07/20100709_ikaros_e.html)), against 1.8 mN for a
  perfect mirror facing the Sun at 1 AU.
- The Planetary Society's LightSail 2 raised its orbit's high point by about 2 km in four days on sunlight alone,
  declared a success on 31 July 2019
  ([The Planetary Society](https://www.planetary.org/press-releases/lightsail-2-mission-success)).
- Breakthrough Starshot (announced 12 April 2016 by Yuri Milner and Stephen Hawking; Mark Zuckerberg on its board)
  plans to push gram-scale sails to 20% of light speed with a laser array of up to 100 GW
  ([Breakthrough Initiatives](https://breakthroughinitiatives.org/news/4)).

On scale: Starshot's 10^11 W pushes grams; E1's 10^26 W is 10^15 times that. The physics is proven; the size is our
enabler.

## Earth and the Moon

**Does Earth freeze at 2.7 AU?**
Without help, yes: our climate model gives 150 K and no liquid water, the same as the company's demo. Mirrors
in space (E3), built in 25-year batches up to 8.5 x 10^8 km^2, keep Earth's sunlight within 1% of today's.
The temperature stays between 287.8 and 288.8 K.

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

**What about night light?**
A full Moon at 2.7 AU gives 0.034 lux, 13.7% of today's 0.25 lux: the Moon moves with Earth and gets less sunlight
too, and the sunlight mirrors (E3) aim at Earth, not the Moon. About 3,335 km^2 of flat mirrors on the Moon's near
side bring the night side back to 0.25 lux. They count against E3's 10^9 km^2 mirror bound, which has
1.5 x 10^8 km^2 to spare, so no new enabler is needed. The area is conservative, up to about 2x: today's figure is a
full Moon overhead, the mirrors' light an average over the whole night hemisphere. They work only from first to last
quarter, around full Moon (cos(phase/2) of their full-Moon light, 45% over a month), so the monthly cycle stays. One
mirror lights a patch about 1,300 km across. They cannot carry the climate: even the whole near side
(9.5 x 10^6 km^2) gives at most 6.6 W/m^2 on the night side, 0.31 K on the global mean. The sunlight mirrors do that
job. The numbers come from `sim/night.py` and `tests/test_night.py`, not the saved run.

## The asteroid belt

The numbers here come from `sim/scenarios/small_asteroids.py` (`results/small_asteroids.json`), which scales the
journey's tracked belt passes down in size with JWST's count of small main-belt asteroids (Burdanov et al. 2024).
Each range takes every low end, or every high end, at once.

**Won't small, dark asteroids hit Earth?**
Without defence, yes, often. Parked at 2.7 AU, Earth would meet a rock of 20 m or more about 8 times a year (1 to
40), one of 100 m or more once every 9 years, and one of 1 km once every 87. At 11.6 km/s a 20 m rock carries
0.13 Mt, a quarter of Chelyabinsk's. A fleet of NEO Surveyor-class infrared telescopes (today's technology) sees a
dark 20 m rock 2.7 to 3.8 million km out, 10 to 15 days before it would arrive, and a 100 m one 14 to 19 million km
out, 7 to 10 weeks. E1 then pushes each one aside with the light it absorbs, while it is still beyond 840,000 km, so
the beam (up to 30 degrees off the Sun line) stays 420,000 km from Earth. A 20 m rock needs 82 m/s: 1.6 x 10^23 W for
a day, even if E1's spot is as wide as the tow mirror. That is 2% of E1's spare power. It is inside E1's declared
role (it nudges dangerous asteroids), so nothing new is declared. In practice E1 pushes the rock aside or vaporises
it. In that day the rock absorbs 2.1 x 10^17 J, while vaporising it takes about 1.3 x 10^14 J. So it boils long
before light pressure alone could move it, and the boiling pushes far harder (see DE-STAR above). Counting light
pressure only is the cautious bound.

**Why not park in a Kirkwood gap?**
The gaps are gaps in orbit size, not in space. Among 20,000 real orbits, sizes near 2.50 AU are only 4% as common as
near 2.70 AU, but asteroids on other orbits cross 2.50 AU all the time. Earth parked there would meet 0.75 times as
many asteroids as at 2.70 AU; at 2.82 AU 1.05 times, and at 2.95 AU 0.77 times. A quarter fewer is not worth
leaving the brief's 2.7 AU. The gaps are Jupiter's resonances, which is why they are empty. The survey and E1 do the
job instead.

**What happens to Mars, its moons and our Moon in the belt?**
Craters only. Scaled by size and gravity focusing at the same encounter speed, the Moon gets 0.9% of Earth's hits (a
20 m rock once every 14 years, 1 km once every 9,300 years). Mars gets 7%, an upper bound because its outer belt is
sparser. Phobos and Deimos get almost none. Breaking Phobos up takes a 2.2 km rock (Benz & Asphaug 1999), which comes
once in 450 million years; Deimos takes a 0.9 km rock, once in 870 million years. Breaking the Moon up takes 20
times the whole belt's mass hitting it (Stewart & Leinhardt 2009; at least 6 times even if every joule went into
it), and Mars 370 times.

**Won't all those mirrors make space debris?**
Some, and it stays small. Dust punches holes in the mirror film: 3.3 x 10^-7 of each face a year. On 8.5 x 10^8 km^2
of sunlight mirrors (about 85,000 satellites of 100 km x 100 km) that is 570 km^2 of film a year, about 5,700
tonnes, mostly vapour and droplets. Sunlight blows droplets under 0.57 um out of the solar system. A loose flake of
5 um film feels sunlight's push at 15% of the Sun's pull, so it drifts off the fleet's orbit rather than staying among
the mirrors. Thin film does not shatter: a hit, even by one of the 2,600 rocks of 1 m or more that cross the mirrors
each year, makes a hole, not a cloud of fragments, so there is no chain reaction of collisions (Kessler syndrome).
What keeps it that way:
- rip-stop film, as on solar sails, so a hole does not spread;
- E3 patching and recycling 570 km^2 of film a year (7 x 10^-7 of the fleet), inside its manufacturing role;
- mirrors placed well away from the orbits today's satellites use;
- E1 pushing rocks aside whole, never breaking them up;
- the same infrared survey tracking anything large that breaks loose.

**Won't rocks hit the tow mirror?**
Yes, and it is built for it. The Earth tow's 2.1 x 10^7 km^2 mirror meets about 65 rocks of 1 m or more a year in
the belt. Over its 2,758 years there, 62 of 20 m or more, 0.85 of 100 m and 0.09 of 1 km (196, 2.7 and 0.29 at the
belt's rate over the whole 8,758-year tow). Its cables meet about 0.35 rocks of 10 m (1.2 kt each). Layers of
protection:
- its own beam: 4.7 x 10^12 W/m^2, 75,000 times the Sun's surface, vaporises a 1 m rock in 3 to 6 ms, so rocks
  reach it only from the sides and back;
- the survey and E1: 20 m rocks are seen about 10 days out and 100 m about 52 days out, then pushed aside or
  vaporised;
- rip-stop panels and E3 patching about 14 km^2 a year (unrepaired, dust would hole 0.18% of it);
- damage margin: E1 has 7.3% spare power, so the mirror can lose about 7% of its area and still hold the asteroid;
- the cables are many strands: their safety factor of 1.57 at the power cap covers losing 4.7%;
- and if all else fails, the Earth tow survives 15 hours with no beam, or 1.25 days at half power.
The Mars tow's mirror meets about 40% of these rates and has 11% spare power.

## The sunlight optics

The numbers here come from `sim/scenarios/mirrors.py` (`results/mirrors.json`), worked out from the run's mirror area.

**Where are the sunlight optics?**
Near the Sun-Earth L1 point, 4.08 million km toward the Sun: a ring of refracting film, 13,400 to 22,300 km from the
Sun-Earth line, that bends sunlight by up to 0.31 degrees onto Earth. The extra light comes from the Sun's own
direction, so noons, dawns, nights and seasons stay natural. It is Angel's (2006) L1 sunshade used the other way
round. Sunlight's push holds the ring a little beyond L1, less the heavier the film: at 100 g/m^2 (10^14 kg in all)
it sits 0.9% out, and Earth catches 82% of the Sun's image each piece throws. Held to E3's 10^9 km^2, Earth gets
97% of today's sunlight (286 K) if the film passes 95% of the light, and 92% (282 K) at 90%. Below 89% of today's
sunlight our climate model freezes, so the film must pass at least about 88%. L1 is unstable (a drift doubles in
about 70 days), so each piece is steered by switching 1% of its reflectivity, nine times what holding within 1,000 km
needs. The tow beams pass 425,000 km from the ring. Why not elsewhere: a mirror right behind Earth sends its light
to the night side, and a ring orbiting Earth that keeps nights dark needs 1.2 x 10^9 km^2, 20% over E3.

E3's bound covers sunlight optics, mirrors or film. If it is read as mirrors only, our fallback is a ring of mirrors
held 120 degrees from the Sun by sunlight (9.8 x 10^8 km^2, 1 um film, 711,000 km out). It can only reach a daylit
strip near dawn and dusk, so a place gets most of its mirror light in the morning and evening, with a dim noon from
the 14% direct Sun. The daily total matches today's, but our one-dimensional climate model cannot show that shape of
the day. Such a ring is not passively stable either: each mirror needs active station-keeping, for example by tilting.

**Will we see the mirrors from Earth?**
The L1 ring, as a bright halo 0.19 to 0.31 degrees from the Sun's centre (the Sun itself is 0.2 degrees across at
2.7 AU): the Sun looks a little wider, and the ring adds nothing at night. With the fallback ring, the mirrors
lighting a place would shine at the Sun's surface brightness, a scatter of sun-bright points along a band, together
0.91 of today's Sun disc. The tow mirror is seen too. It faces Earth, 135
degrees from the Sun in the night sky, as a dull red disc 0.47 degrees wide (the Moon's size) glowing at 1,466 K at
full power: 0.24 lux, as bright as today's full Moon (0.008 to 0.15 lux at the power the run used). Any beam light
it scatters rather than reflects falls on Earth: keeping that under a full Moon needs scatter below 3.4 x 10^-11 of
the beam, and below 3.7 x 10^-8 to keep its heat under our 0.5% limit. E2 bounds only absorption and E1 sets no
wavelength, so this is an open risk our frozen enablers do not cover.

**What happens to our satellites?**
They come along: bound to Earth like the Moon, they move with it. Out of the mirrors' light (which is aimed at the
ground), their solar panels get 13.6% of today's sunlight, so they need about 7 times the panel area or another
power source. The mirror ring stays clear of them: 158,000 km above geostationary orbit, 156,000 km inside the
Moon's closest approach, and inside the 420,000 km that no beam may enter.

## Numerics and honesty

**How do you know the result is not tuned?**
Every number comes from the running model and is written to `results/`; the README table and the momentum
record are generated from those files. The ten benchmarks run as tests on every pull request, and any input
can be changed live: `uv run python -m sim.benchmarks 4 --set e=0.5`.

**Does the answer change with the step size?**
Hardly. Halving the step (1 day to 0.5 days) moves Earth's arrival from year 8,758 to 8,730 (0.3%), with the same
orbit (2.70 AU, eccentricity 0.0333 against 0.0331), Mars parked in 5,170 against 5,168, temperatures 287.8 to
288.9 K and 0 unresolved flags; the ledger closes to 2.3 x 10^-16. The big asteroids' closest passes do change
(Vesta 0.037 AU against 0.018) because they depend on timing, which is why E1 nudges them.

**How is momentum conserved so exactly?**
Each pair's gravity forces are computed once and applied as exact negatives, and every push is added with an
error-free (two-sum) compensated sum. The guide's two checks close to 5.5 x 10^-22 and 5.6 x 10^-16 (limit 10^-9).

**Why not Octo-Earth?**
Its arms push on Earth's field, whose source is Earth's own core: we compute both forces and they cancel to
3.4 x 10^-13, whatever the arms' shape. And curled over the planet as the company's demo draws it, a 12,000 km arm
breaks at its root under its own weight past 5 km in steel, 637 km in ideal nanotube; standing straight up, it would
buckle past 471 km and 1,444 km.

**What would break your design?**
The power (E1) and building at planet scale (E3). Physically, the closest calls were Mars caught by Jupiter's 2:1
resonance (fixed with the sprint), the asteroid lost during a long outage (15 hours of total blackout is the
margin), and 1 km asteroids in the belt (one every 127 years without E1's nudges).

## The code

**Can we run it?**
`uv sync`, then `uv run python -m sim.benchmarks` (12 s) and `uv run pytest -m "not slow"` (about a minute).
The full journey takes about an hour and a half. The test bench, [ashish000011.github.io/black-ant](https://ashish000011.github.io/black-ant/),
replays the saved runs: the experiments on the left, the 3D view in the middle, every check on the right.
