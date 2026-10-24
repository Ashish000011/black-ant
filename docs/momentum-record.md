# Conservation and momentum record

Generated from `results/` by `uv run python -m sim.report --momentum`. Every number comes from the running model.

## Baseline drift (no push)

| Run | Energy error | Limit |
| --- | --- | --- |
| Official benchmark 5: Sun, Mercury to Neptune, 5 years, Yoshida fourth order, 0.25-day steps | 8.88e-11 | 1e-9 |
| The real solar system for 1,000,000 years (REBOUND MERCURIUS, 5-day steps) | 4.00e-09 | 1e-6 |
| The moved solar system for 1,000,000 years after arrival | 1.34e-08 | 1e-6 |

## The propulsion run's momentum ledger

Earth is pulled only by gravity. The only outside forces in the run are the beams' pushes on the two tow asteroids
(the applied impulse). Their partners are the beam stations, which recoil as they fire, and the light, which carries
momentum away after bouncing. Gravity between bodies is applied in exactly opposite pairs. Asteroids sent away at
the end of their tows take their momentum with them.

| Account | Impulse, kg m/s (x, y, z; J2000 ecliptic) |
| --- | --- |
| Applied impulse (beams on asteroids) | magnitude 8.7841e+26 |
| Beam stations' recoil | (-3.7190e+26, -6.1261e+26, 1.1498e+25) |
| Bounced light | (5.5217e+26, -2.2804e+26, -1.9152e+26) |
| Station recoil plus bounced light | (1.8027e+26, -8.4065e+26, -1.8002e+26) |
| Asteroids sent away | (6.9392e+24, -3.1342e+24, -1.2274e+22) |

| The guide's check | Worst during the run | At the end | Limit |
| --- | --- | --- | --- |
| Integrator is honest: bodies' momentum change against the applied impulse | 5.5e-22 | 1.5e-22 | 1e-9 of the applied impulse |
| Nothing from nothing: applied impulse plus its partners | 5.6e-16 | 3.6e-17 | 1e-9 of the applied impulse |

The stepper keeps every rounding error (sim/ledger.py): each pair's gravity forces are exact negatives bit for bit, and every push is added with an error-free sum, so momentum is conserved to the precision of the arithmetic itself.

## Energy

The beams did 1.7969e+33 J of work on the bodies; the bodies gained 1.7970e+33 J (counting what left with the asteroids sent away). They match to 0.007%. The worst gap between the two during the run was 6.9e-07 of the system's total energy (limit 1e-5).
