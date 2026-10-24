# The pitch: 7 minutes, then 5 of questions

What we say over the deck, part by part, in the guide's order (section 9), with the slide on what we found and
fixed in part 5. The slides themselves are the shared deck (ask Ashish for the link); the questions are in
[qa.md](qa.md). Every number here comes from `results/` and is checked by `tests/test_report.py`, which also
checks that each part's words fit its time at 150 words a minute, so there is room to point and click.

| Part | Time | Who |
| --- | --- | --- |
| 1. The concept in one picture | 0:30 | Ashish |
| 2. Our estimate and the enablers we chose | 1:00 | Member 3 |
| 3. Live run: deployment, forces, the ledger | 2:00 | Member 4 |
| 4. Does Earth reach the orbit, and is it safe? | 2:00 | Member 2 |
| 5. Benchmarks, what we found and fixed, what we would test next | 1:30 | Member 5 |
| Total | 7:00 | |

Judged on: physical correctness 30, validation 20, scientific honesty 15, depth 15, visualisation 10,
presentation 10. Parts 3 to 5 carry most of it, so do not let parts 1 and 2 run over.

## 1. The concept in one picture (0:30, Ashish)

*Slide: the Earth tow, the asteroid's pull on Earth, Earth's pull back, the light on its mirror.*

> We are Black Ant. We move Earth to 2.7 AU with a gravity tractor held in place by light. A
> 3.97 × 10^20 kg asteroid sits 637,100 km from Earth and pulls it with its gravity; light on the asteroid's
> mirror holds it there. Nothing touches Earth, and every push is booked with its partner.

## 2. Our estimate and the enablers we chose (1:00, Member 3)

*Slide: the estimate in four lines; the three enablers with their limits and the most the run used.*

> The estimate: reaching 2.7 AU takes 1.7 × 10^33 J of orbital energy, or 11.7 km/s on a slow spiral.
> The asteroid gives 6.53 × 10^-8 m/s², 4.6 × 10^-8 of it along the orbit: about 8,000 years. The run takes 8,758.
> Light carries little momentum: holding a pull of 3.95 × 10^17 N takes about 8.4 × 10^25 W. That is
> E1, at most 10^26 W; the run peaked at 9.27 × 10^25 W. E2 is a 100 GPa mirror and cable material; E3
> places the asteroids and builds mirrors. Every flag left names one of the three.

## 3. Live run: deployment, forces, the ledger (2:00, Member 4)

Open the test bench, [ashish000011.github.io/black-ant](https://ashish000011.github.io/black-ant/), before the
pitch starts. If the network fails, play [media/black-ant-demo.mp4](../media/black-ant-demo.mp4) from 0:10.

| Do | Say |
| --- | --- |
| Experiment C, the tow up close, Forces and momentum tab | This is the Earth tow, replayed from the saved run. The asteroid's pull on Earth, 3.95 × 10^17 N; Earth's pull back, equal and opposite; and the light that holds the asteroid, from stations far on the Sun's side. No beam comes within 420,000 km of Earth. |
| Point at the ledger panel | Every push is booked: the beams on the asteroids, the stations' recoil, the light that bounces away, the asteroids sent off at the end. The guide's check closes to 5.6 × 10^-16, against a limit of 10^-9. |
| Experiment B, the journey, play | Mars goes first: its own tow parks it at 3.64 AU in year 5,168, so the planets never meet. Then Earth crosses the belt. |
| Let it run to arrival | Earth arrives at 2.7006 AU in year 8,758, with 0 unresolved flags. |

## 4. Does Earth reach the orbit, and is it safe? (2:00, Member 2)

*Slides: the orbit-size chart; the ten Earth-safety thresholds; a million years later.*

> Yes, in year 8,758 of the 10,000 allowed, at 2.7006 AU. And it stays safe the whole way: all ten thresholds hold
> at every 100-day check. Mirrors in space keep Earth's sunlight between 0.995 and 1.010 of today's, so the
> temperature stays between 287.8 and 288.8 K, with liquid water on at least 82% of the surface. Without the
> mirrors our model gives 150 K, as the company's demo does.
> The Moon stays: it sits at most 0.256 of the way to the edge of Earth's Hill sphere, and the tow's pull is
> at most 0.0020 of Earth's pull on the Moon. The day lengthens by about 2.5 × 10^-7 s.
> Then we switched the tows off and ran the new solar system for a million years. Earth stays between 2.698 and
> 2.702 AU and no planet is thrown out. Two hazards remain, and we say so: a 1 km asteroid about once every
> 127 years crossing the belt, which E1 nudges aside, and a wider swing of the seasons, which the mirrors correct
> by re-aiming 1.4% of Earth's sunlight.

## 5. Benchmarks, what we found and fixed, what next (1:30, Member 5)

*Slides: the ten benchmarks; the found-and-fixed table; next steps.*

> All ten official benchmarks pass, and they run as tests on every pull request; a judge can change any input,
> live. Our own checks add Kepler's third law, energy over 1,000 years, agreement with REBOUND, and the
> Octo-Earth audit: its arms push only on Earth's own core, and the two forces cancel to 3.7 × 10^-12.
> What we found and fixed: Mars parked at 3.1 AU is thrown onto Earth's path, so it parks at 3.64 AU. Crossing
> Jupiter's 2:1 resonance Mars was caught in 6 of 8 trials, so its tow sprints across: caught in 0 of 8. A
> 3-hour beam outage lost the asteroid, so the beam is split across independent stations, and the tow now
> survives a 15-hour blackout.
> Next, we would follow the Moon inside the journey, resolve the climate by latitude, and sweep the tow's mass
> and distance.

## Rehearsals (the issue asks for three, with a timer)

| # | Date | Total | Part over by more than 10 s | Fix |
| --- | --- | --- | --- | --- |
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |
