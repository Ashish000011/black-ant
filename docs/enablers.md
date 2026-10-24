# Our hypothetical enablers (declaration for the mid-point check-in)

Team Black Ant declares three hypothetical enablers. Each is bounded by a stated number, labelled in the
simulation, and fits one of the kinds the participant guide allows (section 7). None creates momentum or
energy: every push is booked in the ledger with the body that takes the equal and opposite push, and all waste
heat is radiated. The numbers live in [`config.yaml`](../config.yaml) (`enablers`); every place the run relies
on an enabler is recorded as a flag that names it (`results/summary.json`, `flags`).

## E1: a power source of up to 10^26 W of focused light

| | |
| --- | --- |
| Allowed kind | "A power source up to a stated wattage, waste heat still radiated" |
| Bound | At most 1.0 x 10^26 W of beam power in total, at every moment (checked every 100 days; most used: 9.27 x 10^25 W) |
| What it does | Lights the tow mirrors on both tow asteroids, from the Sun's side. Mars's tow is served first; Earth's tow uses the rest. For a few decades while Mars crosses Jupiter's 2:1 resonance, Mars's tow takes up to 4 x 10^25 W and Earth's tow eases off to about 4.7 x 10^25 W; the total stays under the bound. The same budget nudges asteroids found heading for Earth (about 10^14 W for a day each) and big asteroids off close passes (under an hour at 10^25 W each) |
| How it is built | Many independent stations: no single fault takes out more than a quarter of the power, and a fault is answered within 12 hours. The outage tests (`sim/scenarios/outage.py`) show both tow asteroids survive that |
| Its reaction partner | The stations recoil as they fire (ledger account `station`), and the light carries momentum away after it bounces (account `light`). Beam push plus both partners add to zero, to 4 parts in 10^15 |
| What it does not do | It makes no force on Earth. It does not cancel its own recoil: the recoil is booked. It is not a real energy source, so we do not claim the energy bonus |

## E2: super-mirror material

| | |
| --- | --- |
| Allowed kind | "Ideal nanotube or graphene arms (50-130 GPa)", applied to mirrors and cables |
| Bound | Tensile strength 100 GPa; density 2,000 kg/m^3; reflects all but 10^-7 of the light that hits it; works up to 1,500 K |
| What it does | The tow mirrors and the cables that tie them to the asteroids |
| How it is checked | Every 100 days: cable and anchor safety factors of at least 1.5 at the beam's actual force, and also at each tow's full power cap (Earth's tow 10^26 W, Mars's tow 4 x 10^25 W for its sprint); mirror temperature from the absorbed share radiated from both faces (`sim/checks/structure.py`) |
| What it does not do | It carries no load beyond 100 GPa / 1.5, and its absorbed heat is radiated, not ignored |

## E3: asteroids and mirrors in place at the start

| | |
| --- | --- |
| Allowed kind | "Access to an asteroid of stated mass", "already built at the start", "free raw material delivered where needed" |
| Bound | Two asteroids: 3.97 x 10^20 kg (Earth's tow, 637,100 km from Earth) and 1.56 x 10^20 kg (Mars's tow, 400,000 km from Mars), both at most 4 x 10^20 kg. Tow mirrors, cables and anchors built. Sunlight mirrors up to 10^9 km^2 (most needed: about 8 x 10^8 km^2 at 2.7 AU) |
| What it does | Puts the tow asteroids on their starting spots and the structures in place; the sunlight mirrors reflect extra sunlight onto Earth as it moves out |
| How it is checked | Asteroid masses and mirror area against the bounds, every 100 days. The sunlight mirrors' light is computed from their area and their distance from the Sun, and Earth's temperature follows from the energy balance (`sim/habitability.py`): the climate is calculated, not assumed |
| What it does not do | It does not move Earth, hold the asteroids or supply energy; it only places matter that the simulation then has to move and hold with E1's light |

## What we do not assume

- No force appears on Earth: Earth is pulled only by the gravity of the tow asteroid, the Sun, the planets and
  the Moon.
- Gravity, inertia and Earth's magnetic field are left alone.
- The climate is not assumed constant: sunlight, temperature, liquid water, air and magnetic shielding are
  computed along the journey (`sim/habitability.py`).
- No load is ignored: every structure carries a safety factor of at least 1.5.

Owner: Ashish Bharti. Changes after the mid-point check-in are not allowed.
