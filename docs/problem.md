# The problem: Black Ant Robotics (TransfiNITTe 2026)

## What is asked

Build a computer simulation of a machine that moves Earth to a new orbit, for example from 1 AU out to
about 2.7 AU near the asteroid belt, without harming the planet or life on it.

The brief offers a reference concept, **Octo-Earth**: a structural ring around Earth along a great
circle, with eight articulated arms (up to about 12,000 km long) rooted on it at 45 degree steps, driven
partly by currents in the arms pushing against magnetic fields (the Lorentz force). Teams may simulate
it, change it, or propose another concept that acts on a planet-sized body. The brief names the options:
a gravity tractor, steered asteroid flybys, a mass driver, a solar sail or mirror array, a magnetic sail.

**We chose a gravity tractor**: an asteroid towing Earth with its own gravity, held in place by light.
Why, and how, is in [approach.md](approach.md).

## How it is judged

All of these are required to win:

| Winning condition | What it means in practice |
| --- | --- |
| Earth reaches its target orbit | Within 10,000 simulated years |
| Earth stays safe | Every threshold in the rulebook appendix holds for the whole run |
| The structure survives | Every structural safety factor stays at or above 1.5 |
| The code is validated | Every applicable benchmark passes |
| The physics is honest | Every force booked with its reaction; energy and momentum conserved |
| No unresolved flags | Only flags caused by your declared hypothetical enablers are allowed |

Teams may declare up to three **hypothetical enablers** (section 7 of the rulebook). Entries that
honestly show their concept failing are still scored and can win other awards.

## What we have, and what we still lack

- **The participant guide** (Planetary Propulsion Hackathon, 24 to 26 October): the ten official benchmarks
  (all pass: `uv run python -m sim.benchmarks`), the enabler rules (declared in writing at the mid-point
  check-in; ours: [enablers.md](enablers.md)), the deliverables and the judging weights.
- **Team size:** the guide says 2 to 4; the organisers later allowed 5.
- **The company's reference demo**, [octo-earth-simulator.vercel.app](https://octo-earth-simulator.vercel.app)
  ("what the company expects"; they call it about 30% successful). Its Safety thresholds panel and Earth safety
  tab give ten Earth-safety thresholds, which we adopt: global mean temperature 263 to 308 K; liquid water on at
  least 30% of the surface; absorbed sunlight under the runaway-greenhouse limit (282 W/m2); surface pressure at
  least 50 kPa; N2 kept (Jeans lambda over 30); magnetopause at least 3 Earth radii; day length changed by at
  most 1 s; the Moon inside 0.49 of Earth's Hill radius; thrust under 0.01 of Earth's pull on the Moon.
- **Still missing:** the rulebook itself. If its appendix differs from the demo's thresholds, the owner changes the
  number in [`config.yaml`](../config.yaml) and the journey is re-run; nothing else has to change.
