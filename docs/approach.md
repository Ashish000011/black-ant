# Our approach: towing Earth with a light-held asteroid

## The idea in one paragraph

A 4 x 10^20 kg asteroid (about 670 km across) is parked 637,100 km from Earth, ahead of it and out
from the Sun. Its gravity pulls Earth very gently: 6.5 x 10^-8 m/s^2. Left alone it would fall onto
Earth, so a mirror tethered to it is pushed by a focused beam of light that holds it exactly in place.
Earth keeps being pulled, its orbit widens a little on every lap, and after about 8,760 years it reaches
2.7 AU. Mars sits across that path, so a second, smaller tow moves Mars out of the way first. Sunlight
mirrors keep Earth's sunlight and temperature at today's level the whole way.

## Why not Octo-Earth

Arms rooted on Earth push on Earth, and Earth pushes back on them equally (Newton's third law). Forces
inside the Earth-plus-machine system cancel, so they cannot move its centre of mass: to change Earth's
orbit, a force has to come from outside it (another mass's gravity, light from outside, or mass thrown
away). We audited the reference concept with numbers (`uv run python -m sim.scenarios.octo`, results in
`results/octo_earth.json`), at the arm the company's demo draws: 12,000 km in 24 jointed segments curling
72 degrees round the globe to a claw 4,600 km up, a 200 km tube with 2 km walls, 1 MA.

- **No net push.** Earth's magnetic field comes from currents in Earth's own core. The force of the core's
  field on the arms' circuits (1.9 x 10^6 N) and the force of the arms' field on the core, worked out
  separately, cancel to 3 x 10^-13 of each other (test X8). Whatever their shape, the arms only push on
  Earth itself. In a uniform outside field (the demo's 0.5 nT) closed circuits feel no net force at all.
  Arms with no return path seem to push, but their charge would have nowhere to go; and even in Earth's
  full field they would give at most 3 x 10^9 N, so the trip would take about 10^12 years.
- **The arms cannot hold themselves up.** Curled as drawn, an arm is a beam held only at its root, and its
  weight breaks it there past 5 km in steel and 640 km in nanotube (a safety factor of 0.012 at 12,000 km).
  Standing straight up, a 12,000 km arm's own weight puts 315 GPa on its base in steel (which yields at
  0.355 GPa) and 52 GPa in carbon nanotube (63 GPa is the strongest single tube ever measured: a safety
  factor of 1.2, under the 1.5 required). Long before that, the column buckles
  under its own weight: past 470 km in steel and 1,450 km in nanotube (under 3,000 km even with the
  weakest gravity along the arm). Held out level, the longest arm with a 1.5 safety factor is 17 km in
  steel and 570 km in nanotube.

A gravity tractor gets around both: the asteroid is outside Earth, its pull is a real outside force, and
nothing touches Earth.

## The size of the job

| | |
| --- | --- |
| Earth's orbital speed | 29.8 km/s at 1 AU, 18.1 km/s at 2.7 AU |
| Energy Earth's orbit must gain | about 1.7 x 10^33 J |
| Pull on Earth | about 3.9 x 10^17 N (2.8 x 10^17 N of it along the orbit) |
| Time | about 8,760 of the 10,000 years allowed |

## The physics we use

| Rule | Where it is used | Code |
| --- | --- | --- |
| Newton's gravity between every pair of bodies | The Sun, Venus to Neptune, Ceres, Pallas, Vesta, Hygiea and both tow asteroids, all pulling on each other | `sim/integrator.py` |
| Leapfrog stepping (kick, drift, kick), 1-day steps | Keeps energy from drifting over thousands of years | `sim/integrator.py` |
| Light pressure on a mirror: force = (P/c)(in - out) | The beam that holds each asteroid; power for a force f is P = f^2 c / (2 in.f) | `sim/forces.py` |
| Newton's third law, booked | Every push has its partner: the beam station's recoil, the bounced light, asteroids sent away | `sim/ledger.py` |
| Real starting orbits | Planets from JPL's J2000 orbital elements; the big asteroids from JPL Horizons and the Small-Body Database | `sim/bodies.py`, `config.yaml` |
| Gauss's equations | Steering Earth's orbit shape and plane on arrival | `sim/secular.py` |
| Spin precession of an oblate Earth | Earth's axial tilt (the seasons) after the move | `sim/spin.py` |

Checks run every 100 days during the journey: safety, structures, orbits and the ledger. A check that
fails becomes a **flag** (when, how often, how bad); a flag that relies on one of our enablers names it.
That is the brief's "no unresolved flags" rule, made into code (`sim/flags.py`).

## The machine

**Where the asteroid sits.** 637,100 km from Earth, at 45 degrees between straight ahead and straight
out from the Sun. That angle gives the most pull along Earth's orbit for each watt of light: the beam
comes from the Sun's side, and light can only push, never pull.

**The beam.** Light arriving along "in" and bouncing off along "out" pushes with (P/c)(in - out). The
controller asks for the force that keeps the asteroid on its spot (what the spot's motion needs, minus
the gravity the asteroid already feels, plus a correction for any drift, with a 10-day response). No beam
may pass within 420,000 km of Earth (beyond the Moon's farthest point), so when the straight path would,
light arrives up to 30 degrees off the Sun line instead. About 8.4 x 10^25 W is needed.

**Power.** Mars's tow is served first; the Earth tow may use the rest of E1's 10^26 W. That leaves spare
power to catch the asteroid after a fault (see below). For a few decades while Mars crosses Jupiter's 2:1
resonance, the budget is shared differently (next section), and the total never goes above 10^26 W.

**Structures.** Cables and anchors are sized for the most the beam can ever push (2P/c) with a 1.5
safety factor; the mirror is sized so it stays under 1,500 K. Earth tow: cables 10.5 km^2, anchor
10,500 km^2, mirror radius 2,600 km. Mars tow (sized for its sprint, 4 x 10^25 W): 4.2 km^2, 4,200 km^2,
1,650 km.

## Mars goes first

Earth's path crosses Mars's orbit. Without help, Earth passes Mars at about 33,000 km
(`--no-mars-tow`). A second tow (a 1.6 x 10^20 kg asteroid 400,000 km from Mars, giving Mars the same pull
as Earth gets) moves Mars from 1.52 AU out to **3.64 AU**, past Jupiter's 2:1 resonance at 3.28 AU.

Why so far out: a hovering asteroid sits at an unstable balance, and the planet's pull changes across its spot
at 2GM/d^3. At 100,000 km from Mars (our first design) that gradient acts on a 1.25-day timescale, faster than
both the 10-day controller and the 1-day step, so the asteroid held only because the controller's model was
exact; any disturbance ran away. At 400,000 km the timescale is 10 days and the controller is 39 times stronger
than the gradient. Both are checked every 100 days for both tows.

Where Mars parks matters, because once Earth sits at 2.7 AU, Earth's own resonances join Jupiter's:

| Resonance (orbital periods) | With Jupiter, Mars at | With Earth at 2.7 AU, Mars at |
| --- | --- | --- |
| 2:1 | 3.278 AU | |
| 7:5 | | 3.379 AU |
| 11:6, 9:5, 7:4, 5:3 | 3.473, 3.516, 3.583, 3.701 AU | |
| 3:2, 8:5 | | 3.538, 3.694 AU |

3.64 AU sits between them all, with the widest gap from Earth's orbit (about 0.55 AU).

**Crossing Jupiter's 2:1 resonance.** To get there Mars must cross 3.28 AU while moving toward Jupiter, and a
resonance crossed slowly can catch a planet and pump up its eccentricity. We tested it: Mars started at 2.95 AU
from eight different points on its orbit and was pulled across at the normal strength. **Jupiter caught it in 6
of the 8.** So Mars's tow **sprints**: between 3.0 and 3.5 AU its asteroid moves in to half its distance,
pulling four times as hard (about 3.6 x 10^25 W), and Mars crosses the resonance in decades instead of
centuries. (With the asteroid at 400,000 km, the sprint takes it to 200,000 km; the controller stays five times
stronger than the gradient there.) In the same test, sprints of 3.3 and 4.9 times were caught **0 times out of 8**. To keep E1's total
under 10^26 W, Earth's tow eases off over the same stretch: its asteroid drifts out from 637,100 km to
850,000 km, so it needs about 4.7 x 10^25 W, still with about a third spare. Both moves are ramped over decades
so neither asteroid is left behind. Mars's orbit shape is not trimmed: any weakening of its pull near the
resonance raises the chance of capture.

## The Moon comes along

The Moon is held by Earth's gravity well inside Earth's Hill sphere, and that sphere grows as Earth
moves out. The tow asteroid's tide on the Earth-Moon pair is 0.12% of the Moon's own. Fifty-year runs of
Earth, Moon, asteroid and Sun at the start, middle and end of the journey, against runs without the
asteroid, change the Moon's distance by at most 0.05% (`sim/scenarios/moon.py`). An asteroid about 300
times heavier would be needed to disturb it.

## Keeping Earth livable

At 2.7 AU Earth would get 1/7.3 of today's sunlight. Our climate model (zero-dimensional energy balance with
ice-albedo feedback, as in the company's reference demo) then gives 150.4 K and no liquid water anywhere, the
same as the demo. Sunlight mirrors (E3) make up the difference: built in 25-year batches, each sized for where
Earth's orbit will be when the batch ends, up to about 8.5 x 10^8 km^2 at 2.7 AU (supplying 86% of Earth's
light by then). What they deliver is computed from their area, not assumed. The tow mirror's waste heat
reaching Earth is at most about 0.24% of sunlight.

Every 100 days the journey checks the ten Earth-safety thresholds of the company's reference demo
(`sim/habitability.py`, `sim/checks/safety.py`): global mean temperature (263 to 308 K), the share of the
surface warm enough for liquid water (at least 30%; today 82%), absorbed sunlight under the runaway-greenhouse
limit, surface pressure, N2 kept (Jeans escape), the magnetopause distance, the change in day length, the Moon's
place in Earth's Hill sphere and the tow's pull against Earth's pull on the Moon. Nothing in our machine touches
Earth, so the day changes only through the tow asteroid's tide: about 3 x 10^-7 s over the whole journey
(limit 1 s). Results: `results/summary.json` (climate) and the README table.

## Arriving settled: the arrival trim

Jupiter gives every orbit near it a "forced" eccentricity and a forced orbit plane. An orbit that
arrives off them wobbles around them for ever. Parked at 2.7 AU any old way, Earth's eccentricity drifts
up to 0.09 (sunlight swinging about 18% through each year) and its axial tilt swings between 15 and 28
degrees (today: 22.2 to 24.4).

So from 2.0 AU the Earth tow steers Earth's orbit as it pulls, using Gauss's equations
(`sim/secular.py`):

- **Shape:** the pull is made a little weaker on one side of each lap (the asteroid drifts farther out
  there), which turns Earth's eccentricity toward the forced value, 0.03 at 2.7 AU. Result in a
  million-year test: eccentricity stays under 0.056 (the real Earth's own maximum: 0.051).
- **Plane:** the asteroid rides up to 20 degrees above or below Earth's orbit plane around each lap,
  tipping the plane onto the forced one (computed from Jupiter's and Saturn's planes). Result, following the
  real spin axis from today through the journey and a million years after: tilt 21.7 to 26.1 degrees, against
  15 to 28 untrimmed (today: 22.2 to 24.4).

The pull only ever weakens, so the beam never needs more power, and the asteroid never comes closer.

## After arrival

The tow asteroids are sent away and the ledger keeps what they carried. A million-year run of the moved
solar system (REBOUND's MERCURIUS integrator, `sim/scenarios/longterm.py`) runs beside the real solar
system's own million years, so anything the moved Earth does is compared with what the real one does.
Three hazards remain that today's Earth does not have. Each has a counter with a number:

| Hazard | Size | Counter |
| --- | --- | --- |
| Asteroid impacts: 2.7 AU is inside the main belt | One 1 km impact per about 127 years while crossing and 87 once parked, against Earth's natural one per 500,000 (`results/summary.json`, belt) | E1 nudges any asteroid found heading for Earth: 5 cm/s ten years ahead moves it about 47,000 km, about 10^14 W for a day |
| Big asteroids (Ceres, Pallas, Vesta, Hygiea) passing within 0.01 AU | Never in the real solar system; 23 to 45 times per million years after the move | E1 nudges each pass 50 years ahead: under an hour of a 10^25 W beam |
| Seasons: the remaining tilt swing, 21.7 to 26.1 degrees (today 22.2 to 24.4) | About 1.4% of yearly sunlight lands at a different latitude or season than with today's tilt (the real Earth's own swing: 0.7%) | The sunlight mirrors (E3), which already supply 86% of the light, re-aim that share |

The tilt swing cannot be removed by orbit choice alone: at 2.7 AU Earth's axis turns at about 35
arcseconds a year, close to a rate (26 arcseconds a year) at which Jupiter and Saturn tip every orbit's
plane, and that near-match amplifies it.

## Our three enablers

| Enabler | Provides | Limit |
| --- | --- | --- |
| E1 beamed-power station | Focused light for both tows; nudges dangerous asteroids | Up to 10^26 W; many independent stations, no single fault over a quarter of the power |
| E2 super-mirror material | Tow mirrors and cables | Absorbs 10^-7 of light; 100 GPa strength; density 2,000 kg/m^3; up to 1,500 K |
| E3 planet-scale manufacturing | Places both asteroids; builds the tow and sunlight mirrors | Asteroids up to 4 x 10^20 kg; mirrors up to 10^9 km^2 |

None creates energy or momentum from nothing: every push is booked with its reaction.

## What the stress tests found, and what we did

| Found | Fix | Re-tested |
| --- | --- | --- |
| Mars parked at 3.1 AU is thrown onto an Earth-crossing orbit within a million years (at 3.0 AU, out to 20 AU) | Park Mars past Jupiter's 2:1 resonance | |
| Mars parked at 3.4 AU, next to Earth's 7:5 resonance, drifts until its orbit crosses Earth's | Park Mars at 3.64 AU, between all the resonances, and trim its orbit shape | Parking scan: ten arrangements stable for a million years, orbits at least 0.26 AU apart |
| Crossing Jupiter's 2:1 resonance at the normal pull, Mars was caught in 6 of 8 trials (and every time its shape was being trimmed) | Mars's tow sprints across 3.0-3.5 AU at 4 times the pull while Earth's tow eases off | Caught 0 of 8 at 3.3 and 4.9 times; then the final run |
| A beam outage of 3 hours lost the Earth tow's asteroid, which then fell through the Moon's orbit | Shared E1 budget, structures sized for full power, E1 built from independent stations | Earth tow survives a 15-hour blackout, half the stations down for 1.25 days, a quarter for 2.8 days; Mars tow 13 hours, 1.8 days, and indefinitely |
| Vesta passes Earth at about 0.012 AU during the journey (our limit 0.02) | E1 nudges it fifty years ahead | About 0.3 hours of a 10^25 W beam |
| Mars tow's cables and mirror too weak at its own power cap | Resized | Test at full power for both tows |
| Earth's eccentricity drifts to 0.09 after arrival | Shape trim | Under 0.056 |
| Earth's axial tilt swings 15 to 28 degrees | Plane trim onto the forced plane; mirrors for the rest | 21.7 to 26.1 degrees over a million years; about 1.4% of sunlight re-aimed |
| Our first belt sample was too cold (made-up orbits) | Real orbits from the JPL Small-Body Database | In the final run |

Every risk, how we check it and its status: [risk-register.md](risk-register.md).
