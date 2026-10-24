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

## What we do not have yet

The rulebook's section 7 (the enablers), its safety appendix (the thresholds) and the official
benchmarks have not been published. Until they are:

- every safety limit, structural rule and enabler limit we use is our own stand-in, written as a number
  with its source in [`config.yaml`](../config.yaml);
- our benchmarks B1 to B9 are in [`tests/`](../tests);
- the questions we will ask the organisers are at the end of [risk-register.md](risk-register.md).

When the real rules arrive, the owner changes the number in `config.yaml` and the journey is re-run.
Nothing else has to change.
