# Black Ant: Towing Earth to 2.7 AU

Technical report, TransfiNITTe 2026, team Black Ant · 25 October 2026

*A copy of the shared report document, kept in the repository. The figures are from the 3D test bench (`viewer/`); the detail behind each section is in `docs/approach.md`, `docs/risk-register.md` and `docs/momentum-record.md`.*

## Summary

Earth reaches 2.7006 AU in year 8,758 of the 10,000 allowed, pulled by the gravity of a 3.97 × 10^20 kg asteroid that a beam of light holds 637,100 km away. Nothing touches Earth: the asteroid's pull is a real outside force, and every push in the system is booked with its partner. Mars is moved first, to 3.64 AU, so the two planets never come closer than 0.37 AU.

Every winning condition holds in our simulation (table below), and a million years after arrival the new orbits stay put. Placed for real, our sunlight optics keep Earth at 97% of today's sunlight (286 K) inside E3's bound; this and the other limits we found in our own design are listed at the end.

## The problem and how it is judged

The brief from Black Ant Robotics [3] asks for a simulation of a machine that moves Earth from 1 AU to about 2.7 AU without harming the planet or life on it. We propose a gravity tractor instead of the reference concept (Octo-Earth), and declare the three hypothetical enablers the rules allow; flags caused only by them are allowed.

| Winning condition | Our result |
| --- | --- |
| Earth reaches the target orbit within 10,000 years | Year 8,758, at 2.7006 AU (eccentricity 0.033) |
| Every Earth-safety threshold holds for the whole run | All ten held at every 100-day check |
| Every structural safety factor at least 1.5 | Lowest 1.57, at the full E1 power cap |
| Every applicable benchmark passes | 10 of 10 official benchmarks |
| Every force booked with its reaction; energy and momentum conserved | Ledger closes to 5.6 × 10^-16 and 5.5 × 10^-22 (limit 10^-9); energy gap at most 6.9 × 10^-7 of the total |
| No unresolved flags | 0 unresolved; 6 caused by enablers E1 to E3 |

The ten Earth-safety thresholds are those of the company's reference demo [4]; the benchmarks, the enabler rules and the 1.5 safety factor come from the participant guide [3].

## Why not Octo-Earth

We audited the reference concept with the same physics as our own machine, at the arm the company's demo draws [4]: eight arms rooted 45° apart on a ring round the globe, each 12,000 km long in 24 jointed segments (a 200 km tube with 2 km walls, carrying 1 MA), curling 72° round the globe to a gripper claw.

![Octo-Earth as the company's demo draws it and our audit models it, in the test bench: a ring on the equator and eight jointed arms curling over the planet to gripper claws (arms, joints, claws and ring drawn 3× as thick as true; lengths true)](img/octo-earth.png)

**No net push.** Earth's field comes from currents in its own core (a loop with Earth's dipole moment, 8.0 × 10^22 A m² [23]). The core's field pushes the arms with 1.94 × 10^6 N and the arms' field pushes the core back; computed separately with Biot–Savart and I dl × B, the two cancel to 3.4 × 10^-13 (test X8). Whatever their shape, the arms push only on Earth itself; in the demo's 0.5 nT outside field, closed circuits feel 2 × 10^-12 N.

**The arms cannot hold themselves up.** Curled as drawn, a 12,000 km arm is a beam held only at its root, which carries 5,500 GPa even in ideal nanotube (63 GPa, the strongest single tube measured [20]): a safety factor of 0.012. At a safety factor of 1.5, the longest arm that holds itself up:

| Material | Curled as drawn | Standing straight up | Standing, buckles past [22] |
| --- | --- | --- | --- |
| Structural steel S355 | 5 km | 3 km | 471 km |
| CFRP, unidirectional | 72 km | 86 km | 691 km |
| Carbon nanotube, ideal [20] | 637 km | 6,964 km | 1,444 km |
| Graphene, ideal [21] | 699 km | 10,454 km | 1,200 km |

A short curled arm rises at 36°, so its weight crushes its root as a standing column's does; a long one fails by bending. This is why we move Earth with an asteroid's gravity: the asteroid is outside Earth, and nothing touches the planet.

## The machine: a gravity tractor held by light

A 3.97 × 10^20 kg asteroid (336 km in radius at 2,500 kg/m³) sits 637,100 km from Earth, at 45° between straight ahead along Earth's orbit and straight out from the Sun. Its gravity pulls Earth with 3.95 × 10^17 N (6.53 × 10^-8 m/s²), and Earth's orbit widens a little on every lap. Earth feels only that pull.

![The Earth tow in the test bench: the asteroid's pull on Earth, Earth's pull back, and the light push that holds the asteroid](img/earth-tow.png)

**The beam.** Earth pulls the asteroid back with the same force. A mirror tied to the asteroid by cables is pushed by focused light from stations far on the Sun's side: light arriving along *in* and leaving along *out* pushes with (P/c)(in − out), and its partners are the stations' recoil and the light that leaves. The 45° spot gives the most pull along the orbit per watt, because light can only push. No beam may pass within 420,000 km of Earth (the closest came 448,909 km). Light pressure is flown physics (IKAROS [35], LightSail 2 [36]), and laser sails are planned [37].

**The controller.** Each step it asks for the force that keeps the asteroid on its spot, with a 10-day response that beats the planet's pull gradient at least threefold. The asteroid never strayed more than 2,715 km (0.4%) from its spot.

**Mars moves first.** A second tow (a 1.56 × 10^20 kg asteroid 400,000 km from Mars) parks Mars at 3.64 AU in year 5,168, between the strong resonances with Jupiter and with Earth. Jupiter's 2:1 resonance (3.28 AU) caught Mars in 6 of 8 trials at the normal pull, so across it Mars's asteroid moves in to 200,000 km for 4× the pull (caught 0 of 8) while Earth's eases out.

**Arrival trim.** From 2.0 AU the tow varies its pull by up to 40% around each lap and rides up to 20° off Earth's orbit plane (Gauss's equations), so Earth arrives on the eccentricity (about 0.030) and plane (near the invariable plane [18]) that Jupiter forces at 2.7 AU: the free eccentricity left is 0.0023. After arrival each tow asteroid is sent away, its momentum booked.

**Sunlight optics.** E3 builds them in 25-year batches to replace the sunlight Earth loses; the run counts them face on, up to 8.5 × 10^8 km², holding Earth at 0.995 to 1.010 of today's sunlight. Placed for real, they are a ring of refracting film near the Sun–Earth L1 point, Angel's L1 sunshade [43] used the other way round: it bends sunlight onto Earth from the Sun's own direction, so noons and nights stay natural. Held to E3's 10^9 km², Earth ends at 97% of today's sunlight (286 K), inside every threshold, if the film passes 95% of the light (`sim/scenarios/mirrors.py`).

**Related work.** Our machine is Lu & Love's gravitational tractor [1] turned around: a spacecraft held by its thrusters tows an asteroid with its gravity; here an asteroid held by light tows Earth. The closest earlier plan for moving Earth, Korycansky, Laughlin & Adams [2], swings a 10^19 kg body past Earth about every 6,000 years, a million times over; its passes come within 1.6 Earth radii, raise tides ten times the Moon's and probably lose the Moon, and its authors call it "extremely risky". Ours takes 8,758 years with one held body never closer than 637,100 km, and the Moon stays; the price is E1's power. Stellar engines [40, 41] move the Sun, and Earth only follows it.

## Declared enablers

We declare the three allowed, each with a hard limit in the configuration; each flag it causes names it.

| Enabler | What it provides | Limit | Most the run used | Flags it covers |
| --- | --- | --- | --- | --- |
| E1 Power source | Focused light from many independent stations, their recoil and the bounced light booked; also nudges dangerous asteroids aside | 10^26 W | 9.27 × 10^25 W | Beam power far above humanity's; Vesta's closest pass (0.018 AU); belt impact rates |
| E2 Super-mirror material | Absorbs 10^-7 of the light; 100 GPa strength; up to 1,500 K | as stated | Mirror at 1,466 K and cables at safety factor 1.57, both at the power cap | Tow mirrors and cables |
| E3 Planet-scale space manufacturing | Places the tow asteroids; builds the tow mirrors and the sunlight optics | 10^9 km² of sunlight optics | 5.5 × 10^20 kg of asteroids; 8.5 × 10^8 km² counted face on | Asteroids and optics in place |

After arrival two more flags arise over a million years, both covered: 45 big-asteroid passes near Earth, each nudged by E1 50 years ahead with at most 0.6 hours of a 10^25 W beam; and a wider swing of Earth's axial tilt, met by re-aiming 1.4% of Earth's sunlight (see Limits).

## Models and equations

Every body pulls every other: the Sun, Venus to Neptune on their real J2000 orbits (JPL [5]), Ceres, Pallas, Vesta and Hygiea (JPL Horizons [6]) and both tow asteroids, with masses from NASA's fact sheets [42]. Each pair's forces are computed once and applied as exact negatives.

```latex
\ddot{\mathbf r}_i = \sum_{j \ne i} \frac{G m_j (\mathbf r_j - \mathbf r_i)}{|\mathbf r_j - \mathbf r_i|^3} + \frac{\mathbf F_i^{\text{beam}}}{m_i}
```

- **Integrators.** Leapfrog with 1-day steps for the journey; Yoshida fourth order [8] for the benchmarks; REBOUND [9] with MERCURIUS [11] and 5-day steps for the million-year runs. Halving the journey's step moves arrival from year 8,758 to 8,730 (0.3%) with the same orbit (eccentricity 0.033, tilt 1.29°), Mars parked in 5,170 against 5,168, 0 unresolved flags and the ledger closed to 2.3 × 10^-16. Only the big asteroids' closest passes move (Vesta 0.037 AU against 0.018): they depend on timing, which is why E1 nudges them.
- **Light pressure.** A mirror turning light from *in* to *out*, and the power for a wanted force:

```latex
\mathbf F = \frac{P}{c}(\hat{\mathbf n}_{in} - \hat{\mathbf n}_{out}), \qquad P = \frac{|\mathbf F|^2 c}{2\, \hat{\mathbf n}_{in} \cdot \mathbf F}
```

- **Orbit growth (Gauss).** A push f along the velocity v (benchmark 8 checks the integrator against it):

```latex
\frac{da}{dt} = \frac{2a^2}{\mu}\, \mathbf v \cdot \mathbf f
```

- **Climate.** A zero-dimensional energy balance (Budyko [13], Sellers [14]) on today's 1,361 W/m² [12], with an albedo rising from 0.30 to 0.62 as the surface freezes between 280 and 250 K and an emissivity that puts today's Earth at 288 K; a latitude profile gives the liquid-water share (82% today). Without the optics it gives 150 K at 2.7 AU, as the company's demo does.

```latex
\frac{S}{4}\,(1 - \alpha(T)) = \varepsilon \sigma T^4
```

- **Air, shield, Moon, day and tilt.** Nitrogen's Jeans parameter; the magnetopause from solar-wind pressure; the Moon against Earth's Hill radius; the tow's tidal torque on Earth's spin; the spin axis precessing at the IAU 2006 rate [16]. Every push is added with an error-free (two-sum) sum.

## Validation

All ten official benchmarks (participant guide, section 6) pass, also with changed inputs (benchmark 4 holds from e = 0 to 0.9); a judge can change any input: `uv run python -m sim.benchmarks 4 --set e=0.5`.

| # | Benchmark | Measured | Expected (tolerance) |
| --- | --- | --- | --- |
| 1 | Wire in a field, I L × B summed over 1,000 pieces | (0, 0, 10) N | (0, 0, 10) N (10^-9) |
| 2 | Closed loop in a uniform field | 4.3 × 10^-16 of I L B | 0 (10^-9 of I L B) |
| 3 | Long straight wire, field at 1 m (Biot–Savart) | 2.00000 × 10^-4 T | μ₀I/2πr (10^-6) |
| 4 | Kepler orbit, e = 0.3, 10 periods | back within 1.8 × 10^-8 a; energy 1.1 × 10^-10 | 10^-6 a; 10^-9 |
| 5 | Sun, Mercury to Neptune, 5 years, no push | energy error 8.9 × 10^-11 | 10^-9 |
| 6 | Earth–Moon barycentre's year | 365.260 days | 365.256 (0.1 day) |
| 7 | Hohmann transfer, Earth to Mars | 2.946 and 2.650 km/s; 258.9 days | 2.94, 2.65 km/s; 259 days (0.02 km/s; 2 days) |
| 8 | Push along the velocity: orbit growth | 3,169.7 km | 3,170.1 km from Gauss (1%) |
| 9 | Cantilever under its own weight | root moment and tip deflection both within 10^-9 | qL²/2, qL⁴/8EI (1%) |
| 10 | Earth's equilibrium temperature | 254.0 K | 254 K (2 K) |

Our own checks X1 to X9 add Kepler's third law, energy over 1,000 years, the ledger with a push on, agreement with REBOUND's IAS15 [10], the asteroid's hold, Octo-Earth's zero net force and the axial tilt; the quick tests run on every pull request.

## Results of the journey

Earth arrives in year 8,758 at 2.7006 AU, with an eccentricity of 0.033 and a tilt of 1.29° to today's ecliptic. Mars is parked at 3.641 AU in year 5,168, 3,600 years before Earth gets there.

![The journey at year 5,200 in the test bench: Mars parked at 3.64 AU, Earth at 1.74 AU, every body in the Scene panel and Earth now against year 0 in the Data panel](img/journey.png)

Earth's orbit grows faster as it widens; Mars's climb steepens near 3.3 AU, where its tow sprints. The planets come closest at the very start (0.373 AU, an ordinary Mars opposition), and both beams together peaked at 9.27 × 10^25 W. Two hundred years after arrival Earth sits at 2.699 AU, eccentricity 0.034.

## Earth safety

All ten thresholds hold at every 100-day check of the journey; without the optics the same model gives 150 K and no liquid water at 2.7 AU.

| Threshold | Worst over the journey | Limit |
| --- | --- | --- |
| Global mean temperature | 287.8 to 288.8 K | 263 to 308 K |
| Surface with liquid water | at least 82% | at least 30% |
| Absorbed sunlight (runaway greenhouse) | at most 240.9 W/m² | under 282 W/m² [15] |
| Surface pressure | 101.3 kPa | at least 50 kPa |
| Nitrogen kept (Jeans λ) | at least 194 | over 30 |
| Magnetopause distance | at least 10.0 Earth radii | at least 3 |
| Change in length of day | about 2 × 10^-7 s | at most 1 s |
| Moon's distance over Earth's Hill radius | at most 0.256 | under 0.49 |
| Tow thrust over Earth's pull on the Moon | at most 0.0020 | under 0.01 |

The Moon and the magnetic shield grow safer as Earth moves out (the Moon's share falls to 0.095; the magnetopause widens to 13.9 Earth radii). With the L1 optics held to E3, Earth ends at 97% of today's sunlight, 286 K, still inside every threshold.

## Structures

Every structure keeps a safety factor of at least 1.57, above the 1.5 required, sized for the most a beam can ever push (2P/c at its tow's power cap), so recovery after an outage is covered.

| Check, at the power cap | Earth tow (10^26 W) | Mars tow (4 × 10^25 W) | Limit |
| --- | --- | --- | --- |
| Cable safety factor (E2 material, 100 GPa) | 1.57 | 1.57 | at least 1.5 |
| Anchor safety factor (load spread into rock of 0.1 GPa) | 1.57 | 1.57 | at least 1.5 |
| Tow mirror temperature (absorbs 10^-7, radiates from both faces) | 1,466 K | 1,463 K | at most 1,500 K |
| Asteroid body safety factor (the planet's uneven pull across it) | 120 | 152 | at least 1.5 |

## Conservation and the momentum ledger

The only outside forces in the run are the beams' pushes on the two tow asteroids: the applied impulse, 8.78 × 10^26 kg m/s over the journey. Their partners are the stations' recoil and the light that carries momentum away; gravity acts in exactly opposite pairs, and asteroids sent away take their momentum with them.

| The guide's check | Worst during the run | At the end | Limit |
| --- | --- | --- | --- |
| Integrator is honest: the bodies' momentum change against the applied impulse | 5.5 × 10^-22 | 1.5 × 10^-22 | 10^-9 of the applied impulse |
| Nothing from nothing: the applied impulse plus its partners | 5.6 × 10^-16 | 3.6 × 10^-17 | 10^-9 of the applied impulse |

The beams did 1.7969 × 10^33 J of work and the bodies gained 1.7970 × 10^33 J, counting what left with the asteroids: a 0.007% match.

## Hazards and stability

**The asteroid belt.** Without help, Earth would meet a 1 km asteroid about once every 127 years while crossing the belt and once every 87 years parked at 2.7 AU, against once per 500,000 years today [25]: we tracked 1,000 real belt orbits [7] for 2,958 years and scaled their 1,325 close passes to the belt's 1.2 million asteroids over 1 km [24]. Smaller rocks are far commoner [26]: parked, Earth would meet one of 20 m or more about 8 times a year, and of 100 m once every 9 years. Infrared survey telescopes [27, 28] see a dark 20 m rock 10 to 15 days out [30, 31], and E1 pushes it aside or vaporises it, as DE-STAR proposes [38, 39], with 2% of its spare power; a 1 km asteroid found 10 years ahead needs a 5 cm/s nudge. Dust holes about 570 km² of optics a year for E3 to patch [29]. Mars, its moons and the Moon get craters only: breaking the Moon up would take 20 times the belt's mass [32, 33, 34].

**Beam outages.** The beams come from many independent stations; full runs with the beams cut for longer and longer show the Earth tow keeps its asteroid through 15 hours with every station off, 1.25 days with half off and 2.8 days with a quarter off (Mars's tow: 4.75 days, and 10.5 hours during its sprint).

**A million years after arrival.** With the tows gone, we ran the moved solar system for a million years (REBOUND, MERCURIUS) beside the real one, with 0 unresolved flags; two chaos copies started with tiny changes agree (the solar system is chaotic [19]). No planet is lost; Ceres leaves the solar system in one of the copies, harmlessly.

| | Moved solar system | Real solar system |
| --- | --- | --- |
| Earth's orbit size | 2.698 to 2.702 AU | 0.99998 to 1.00004 AU |
| Earth's eccentricity, highest | 0.060 | 0.051 |
| Earth's axial tilt | 21.7° to 26.1° | 22.2° to 24.4° |
| Mars's orbit size | 3.614 to 3.655 AU | 1.5236 to 1.5239 AU |

Mars's orbit never comes within 0.36 AU of Earth's. Earth's tilt swings twice as wide as today's, because at 2.7 AU its spin precession runs close to a slow mode of the planets' orbits [17].

## Limits of the model

The model answers whether the physics closes; it does not design the hardware. What it leaves out:

- **Hardware.** Beam stations, optics and the placing of the asteroids are what E1, E2 and E3 declare; the simulation books their forces, recoil and limits, not their engineering.
- **Climate in one dimension.** A global energy balance: no weather, oceans, carbon cycle or biology.
- **Seasons.** At 2.7 AU a year lasts 4.44 of today's, so each season lasts about 13 months; the model gives yearly means only. Keeping today's seasonal contrast under the wider tilt swing needs aimable mirrors re-aiming 1.4% of Earth's sunlight, which with the L1 ring must come out of E3's area. Neither is modelled yet.
- **Where the sunlight optics sit.** The run counts them face on. Below 89% of today's sunlight the model's Earth freezes, so the L1 film must pass at least about 88% of the light. We read E3's bound as covering sunlight optics; read as mirrors only, our fallback is a ring held 120° from the Sun by sunlight, bringing the extra light at dawn and dusk.
- **The tow mirror's scattered light.** It faces Earth, so beam light it scatters falls on Earth: staying under a full Moon needs scatter below 3.4 × 10^-11 of the beam. No enabler bounds it (E2 bounds absorption; E1 sets no wavelength).
- **Separate runs and calculations.** The Moon's orbit and Earth's spin axis have their own runs; small asteroids, the Moon reflectors and the optics' placement are calculations on the run's results. The safety thresholds are the company demo's; if the rulebook differs, its numbers go into the configuration and the run is repeated.

Next we would add the Moon as its own body, a latitude- and season-resolved climate, and a sensitivity sweep of tow mass and distance.

## Reproduce it

Everything here comes from the code and results in the repository; every setting lives in `config.yaml` with its source, and the README gives the commands. The 3D test bench replays the runs: [ashish000011.github.io/black-ant](https://ashish000011.github.io/black-ant/).

## References

1. Lu, E. T. & Love, S. G. 2005, Gravitational tractor for towing asteroids, *Nature* 438, 177. doi:10.1038/438177a
2. Korycansky, D. G., Laughlin, G. & Adams, F. C. 2001, Astronomical engineering: a strategy for modifying planetary orbits, *Astrophys. Space Sci.* 275, 349. doi:10.1023/A:1002790227314
3. Black Ant Robotics 2026, Planetary Propulsion Hackathon participant guide, TransfiNITTe 2026.
4. Black Ant Robotics, Octo-Earth reference demo, octo-earth-simulator.vercel.app
5. Standish, E. M., Keplerian elements for approximate positions of the major planets, JPL. ssd.jpl.nasa.gov/planets/approx_pos.html
6. JPL Horizons system. ssd.jpl.nasa.gov/horizons
7. JPL Small-Body Database query. ssd.jpl.nasa.gov/tools/sbdb_query.html
8. Yoshida, H. 1990, Construction of higher order symplectic integrators, *Phys. Lett. A* 150, 262. doi:10.1016/0375-9601(90)90092-3
9. Rein, H. & Liu, S.-F. 2012, REBOUND: an open-source multi-purpose N-body code for collisional dynamics, *A&A* 537, A128. doi:10.1051/0004-6361/201118085
10. Rein, H. & Spiegel, D. S. 2015, IAS15: a fast, adaptive, high-order integrator for gravitational dynamics, *MNRAS* 446, 1424. doi:10.1093/mnras/stu2164
11. Rein, H. et al. 2019, Hybrid symplectic integrators for planetary dynamics (MERCURIUS), *MNRAS* 485, 5490. doi:10.1093/mnras/stz769
12. Kopp, G. & Lean, J. L. 2011, A new, lower value of total solar irradiance, *Geophys. Res. Lett.* 38, L01706. doi:10.1029/2010GL045777
13. Budyko, M. I. 1969, The effect of solar radiation variations on the climate of the Earth, *Tellus* 21, 611. doi:10.3402/tellusa.v21i5.10109
14. Sellers, W. D. 1969, A global climatic model based on the energy balance of the Earth-atmosphere system, *J. Appl. Meteorol.* 8, 392.
15. Goldblatt, C. et al. 2013, Low simulated radiation limit for runaway greenhouse climates, *Nature Geosci.* 6, 661. doi:10.1038/ngeo1892
16. Capitaine, N., Wallace, P. T. & Chapront, J. 2003, Expressions for IAU 2000 precession quantities (adopted as IAU 2006), *A&A* 412, 567. doi:10.1051/0004-6361:20031539
17. Laskar, J. 1990, The chaotic motion of the solar system, *Icarus* 88, 266. doi:10.1016/0019-1035(90)90084-M
18. Souami, D. & Souchay, J. 2012, The solar system's invariable plane, *A&A* 543, A133. doi:10.1051/0004-6361/201219011
19. Laskar, J. 1989, A numerical experiment on the chaotic behaviour of the Solar System, *Nature* 338, 237. doi:10.1038/338237a0
20. Yu, M.-F. et al. 2000, Strength and breaking mechanism of multiwalled carbon nanotubes under tensile load, *Science* 287, 637. doi:10.1126/science.287.5453.637
21. Lee, C., Wei, X., Kysar, J. W. & Hone, J. 2008, Measurement of the elastic properties and intrinsic strength of monolayer graphene, *Science* 321, 385. doi:10.1126/science.1157996
22. Greenhill, A. G. 1881, Determination of the greatest height consistent with stability that a vertical pole or mast can be made, *Proc. Camb. Phil. Soc.* 4, 65.
23. Alken, P. et al. 2021, International Geomagnetic Reference Field: the thirteenth generation, *Earth Planets Space* 73, 49. doi:10.1186/s40623-020-01288-x
24. Tedesco, E. F. & Desert, F.-X. 2002, The Infrared Space Observatory Deep Asteroid Search, *AJ* 123, 2070. doi:10.1086/339482
25. Catalina Sky Survey, FAQ (a 1 km impact every 500,000 years on average). catalina.lpl.arizona.edu/faq
26. Burdanov, A. Y. et al. 2025, JWST sighting of decametre main-belt asteroids and view on meteorite sources, *Nature* 638, 74. doi:10.1038/s41586-024-08480-z
27. Mainzer, A. K. et al. 2023, The Near-Earth Object Surveyor Mission, *Planet. Sci. J.* 4, 224. doi:10.3847/PSJ/ad0468
28. Kim, Y., Mainzer, A. & Masiero, J. 2024, From NEOWISE to NEO Surveyor (survey sensitivity), EU-ESA Workshop on Size Determination of Potentially Hazardous NEOs, ESTEC, 11-13 November. indico.esa.int/event/530
29. Grün, E., Zook, H. A., Fechtig, H. & Giese, R. H. 1985, Collisional balance of the meteoritic complex, *Icarus* 62, 244. doi:10.1016/0019-1035(85)90121-6
30. Harris, A. W. 1998, A thermal model for near-Earth asteroids, *Icarus* 131, 291. doi:10.1006/icar.1997.5865
31. Lebofsky, L. A. et al. 1986, A refined "standard" thermal model for asteroids based on observations of 1 Ceres and 2 Pallas, *Icarus* 68, 239. doi:10.1016/0019-1035(86)90021-7
32. Pitjeva, E. V. & Pitjev, N. P. 2018, Masses of the main asteroid belt and the Kuiper belt from the motions of planets and spacecraft, *Astron. Lett.* 44, 554. doi:10.1134/S1063773718090050
33. Benz, W. & Asphaug, E. 1999, Catastrophic disruptions revisited, *Icarus* 142, 5. doi:10.1006/icar.1999.6204
34. Stewart, S. T. & Leinhardt, Z. M. 2009, Velocity-dependent catastrophic disruption criteria for planetesimals, *ApJ* 691, L133. doi:10.1088/0004-637X/691/2/L133
35. JAXA 2010, IKAROS confirms photon acceleration (press release, 9 July). global.jaxa.jp/press/2010/07/20100709_ikaros_e.html
36. The Planetary Society 2019, LightSail 2 successfully demonstrates flight by light (press release, 31 July). planetary.org/press-releases/lightsail-2-mission-success
37. Breakthrough Initiatives 2016, Breakthrough Starshot announcement (12 April). breakthroughinitiatives.org/news/4
38. Lubin, P. et al. 2013, Directed energy planetary defense, *Proc. SPIE* 8876. deepspace.ucsb.edu
39. Lubin, P. et al. 2014, Toward directed energy planetary defense, *Opt. Eng.* 53(2), 025103. doi:10.1117/1.OE.53.2.025103
40. Shkadov, L. M. 1987, Possibility of controlling solar system motion in the galaxy, 38th IAF Congress, IAA-87-613.
41. Caplan, M. E. 2019, Stellar engines: design considerations for maximizing acceleration, *Acta Astronaut.* 165, 96. doi:10.1016/j.actaastro.2019.08.027
42. Williams, D. R., NASA planetary fact sheets, NSSDCA. nssdc.gsfc.nasa.gov/planetary/factsheet
43. Angel, R. 2006, Feasibility of cooling the Earth with a cloud of small spacecraft near the inner Lagrange point (L1), *PNAS* 103, 17184. doi:10.1073/pnas.0608163103
