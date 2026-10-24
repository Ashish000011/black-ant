# Black Ant: towing Earth to 2.7 AU

Our entry for **Black Ant Robotics** at TransfiNITTe 2026: a simulation of a machine that moves Earth
from 1 AU to about 2.7 AU, near the asteroid belt, without harming the planet or life on it. All six
winning conditions (target within 10,000 years, Earth safe, structures at safety factor 1.5 or more,
benchmarks passing, every force booked, no unresolved flags) are in [docs/problem.md](docs/problem.md).

## Our approach in short

A **gravity tractor held in place by light**. A 4 x 10^20 kg asteroid sits 637,100 km from Earth and
pulls it gently with its own gravity; a focused light beam pushing on a mirror tethered to the asteroid
keeps it from falling onto Earth. Earth's orbit widens a little on every lap and reaches 2.7 AU in about
8,760 years. Mars is towed out of the way first (to 3.64 AU), sunlight mirrors keep Earth at today's
sunlight and temperature, and on the last stretch the tow steers Earth onto the orbit Jupiter lets it
keep. Every push is booked with its reaction, so energy and momentum are checked all the way.

Read [docs/approach.md](docs/approach.md) for the full plan, the physics and why Octo-Earth cannot work,
and [docs/risk-register.md](docs/risk-register.md) for every way it could fail and what we did about it.

## Results

<!-- results:start -->
| | |
| --- | --- |
| Earth arrives | year 8,758 at 2.7006 AU (limit: year 10,000); eccentricity 0.0331, orbit tilt 1.294 deg |
| Mars parks | year 5,168 at 3.6408 AU |
| Closest Earth-Mars pass | 0.37283 AU (limit 0.05) |
| Closest big asteroid during the journey | ceres 0.0455 AU, pallas 0.0681 AU, vesta 0.0183 AU, hygiea 0.1633 AU (limit 0.02) |
| Most beam power | 9.27e+25 W (E1 limit 1e26) |
| Ledger (the guide's form) | bodies' momentum change matches the applied impulse to 5.5e-22 of it; applied impulse plus its partners: 5.6e-16 (limit 1e-9); beam work matches energy gained to 0.007% |
| Flags during the journey | 0 unresolved; 6 covered by E1, E2, E3 |
| Earth safety: the ten thresholds of the company's reference demo, worst over the journey | temperature 287.8 to 288.8 K (263 to 308); liquid-water area at least 82% (30%); absorbed sunlight at most 241 W/m2 (282); surface pressure 101.3 kPa (50); N2 Jeans lambda at least 194 (30); magnetopause at least 10.0 Earth radii (3); day length changed by under 1e-6 s (1 s); the Moon at most 0.26 of the Hill radius (0.49); thrust at most 0.0020 of Earth's pull on the Moon (0.01) |
| Sunlight mirrors (E3) | sunlight 0.995 to 1.010 of today's; mirrors up to 8.5e+08 km2 (limit 1e9) |
| Asteroid impacts (1 km and up), without E1's nudges | one per 127 years crossing the belt, one per 87 years parked; natural: one per 500,000 |
| A million years after arrival: Earth | orbit 2.698 to 2.702 AU; eccentricity up to 0.060 (real Earth: up to 0.051) |
| A million years after arrival: Mars | orbit 3.614 to 3.655 AU; smallest gap to Earth's orbit 0.362 AU |
| Earth's axial tilt | 21.7 to 26.1 deg (real Earth: 22.2 to 24.4) |
| Sunlight the mirrors re-aim to keep today's seasons | 1.4% of Earth's sunlight (mirrors supply 86%) |
| Big-asteroid passes near Earth | 45 in a million years; each nudged with at most 0.6 hours of a 1e+25 W beam, 50 years ahead |
| Flags after a million years | 0 unresolved; 2 covered by enablers |
| Bodies thrown out in a million years | none |
<!-- results:end -->

Every number above comes from `results/`. The run prints any flag at the end; a flag naming E1, E2 or E3
relies on one of our declared enablers, which the brief allows.

## The 3D test bench

**[ashish000011.github.io/black-ant](https://ashish000011.github.io/black-ant/)**: the journey in 3D (the solar system,
the Earth tow and the Mars tow up close), nine experiments from the baseline to a million years later, and every
check beside it: forces and momentum, orbit, structures, the ten Earth-safety thresholds, benchmarks, plots and
the comparison with the real solar system. It replays the model's saved runs; it computes nothing itself.

```bash
uv run python -m sim.viewer_data   # turn results/ into viewer/public/data/
cd viewer && npm ci && npm run dev # open the address it prints
```

It is published from `main` by `.github/workflows/pages.yml`.

## Setup

Needs [uv](https://docs.astral.sh/uv/). From this folder:

```bash
uv python install 3.12
uv sync
```

## Run

```bash
uv run python -m sim.scenarios.tow --out results    # the full journey with every check, about 35 minutes
uv run python -m sim.scenarios.tow --no-belt --years 500   # a quick look
uv run python -m sim.scenarios.moon                 # the Moon test at the start, middle and end, about 20 seconds
uv run python -m sim.scenarios.longterm --only moved --state results/end_state.json --out results/longterm.json
                                                    # a million years after arrival, about 15 minutes
uv run python -m sim.scenarios.parking              # where Earth and Mars can park, a million years each
uv run python -m sim.scenarios.outage               # how long a beam can fail before its asteroid is lost
uv run python -m sim.scenarios.octo                 # the Octo-Earth audit: net force, arm stress and buckling, 10 seconds
```

Add `--no-mars-tow` to the journey to see why Mars must move first, or `--orbits circular` for flat
circular starting orbits.

## Test

```bash
uv run python -m sim.benchmarks    # the ten official benchmarks, measured against expected, about 12 seconds
uv run python -m sim.benchmarks 4 --set e=0.5 --set periods=20   # change a benchmark's inputs, as judges may
uv run pytest -m "not slow" -v     # quick tests, about a minute (these run on every pull request)
uv run pytest -v -s                # everything, a few minutes
```

The official benchmarks (participant guide, section 6) are `tests/test_official_benchmarks.py`; our own extra
checks are X1 to X9 in `tests/test_extra_checks.py` and `tests/test_checks.py`.

## How we work

- **Nobody pushes to `main`.** Make a branch for your issue (`m2/safety-report`), push it, and open a
  pull request. Ashish reviews and merges; the quick tests must pass first.
- **Your tasks are GitHub issues**, labelled by role: `member-1` physics core, `member-2` safety and
  environment, `member-3` structures and enablers, `member-4` 3D viewer, `member-5` validation and pitch.
- **Rules live in `config.yaml`.** Every limit has its source next to it. If the organisers change a rule,
  change the number there and ask for a re-run; don't hard-code numbers anywhere else.
- **Numbers on slides come from `results/`**, never from memory.

## Where things are

| Path | What it holds |
| --- | --- |
| `docs/problem.md` | The brief and the winning conditions |
| `docs/enablers.md` | Our three hypothetical enablers, as declared at the mid-point check-in |
| `docs/approach.md` | Our plan, the physics, the machine, what we found and fixed |
| `docs/risk-register.md` | Every risk: why it matters, how we check it, the counter, its status, its owner |
| `config.yaml` | Every setting and working rule, with sources; change a number and re-run |
| `results/` | The final run: `summary.json` (every number and flag), `run.json` (one frame per 10 years, what the viewer plays), `end_state.json`, `longterm.json`, `outage.json`, `parking*.json` |
| `sim/bodies.py` | Bodies and their real starting orbits |
| `sim/integrator.py` | Gravity, the leapfrog and Yoshida fourth-order steppers, exactly opposite pair forces, energy |
| `sim/forces.py` | Each tow's spot, and the beam that holds its asteroid there |
| `sim/ledger.py` | The force ledger, kept exactly: applied impulse, station recoil, bounced light, asteroids sent away |
| `sim/flags.py` | Checks and flags |
| `sim/benchmarks.py` | The ten official benchmarks, each with inputs that can be changed |
| `sim/habitability.py` | Sunlight, the sunlight mirrors' build schedule, temperature, shielding, the Moon's Hill sphere |
| `sim/em.py` | Lorentz force and Biot-Savart fields (benchmarks 1 to 3, and the Octo-Earth audit) |
| `sim/checks/` | Safety (Member 2) and structure (Member 3) checks, run every 100 days |
| `sim/belt.py` | 1,000 test asteroids on real orbits: close passes and the impact estimate |
| `sim/secular.py` | The arrival trim: steering Earth's orbit shape and plane |
| `sim/spin.py` | Earth's spin axis, axial tilt and seasons |
| `sim/scenarios/` | The journey, the Moon test, the million-year run, the parking scan, the outage test |
| `sim/viewer_data.py` | Turns `results/` into the 3D test bench's data files |
| `viewer/` | The 3D test bench (Vite and Three.js), published on GitHub Pages |
| `tests/` | The ten official benchmarks, our extra checks X1 to X9 and the safety and structure checks |
| `data/` | Raw JPL data: Horizons vectors and Small-Body Database orbits |
| `sim-proto/` | The first JavaScript prototype, kept for quick experiments |

## Model limits

Planets Venus to Neptune start on their real tilted, oval orbits at J2000.0 (1 January 2000, noon),
from JPL's [orbital elements](https://ssd.jpl.nasa.gov/planets/approx_pos.html); Ceres, Pallas, Vesta
and Hygiea from JPL Horizons. No Mercury (its pull on Earth is tiny and it would need much shorter steps).
Earth carries the Moon's mass in the long runs; the Moon test follows the Moon itself. The benchmarks,
enabler rules and the 1.5 safety factor come from the participant guide; the ten Earth-safety thresholds
from the company's reference demo, until the rulebook appendix says otherwise.
