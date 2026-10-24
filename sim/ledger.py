"""The force ledger: every beam push is booked together with its partners.

Gravity between bodies needs no booking: each pair's two pulls are exact opposites and are added to the two
bodies' momenta with their rounding kept (Momenta below), so they cancel bit for bit. A beam's push on an
asteroid (the applied impulse) is balanced by two accounts: the station that fired it recoils, and the bounced
light carries momentum away. Asteroids sent away at the end of a tow take their momentum and energy with them,
so those are booked too.

The participant guide's two checks (section 6), both computed exactly with fractions:
    integrator is honest:   |change in all bodies' momentum - applied impulse| < 1e-9 |applied impulse|
    nothing from nothing:   |applied impulse + partners' impulse|              < 1e-9 |applied impulse|
"""

from dataclasses import dataclass, field
from fractions import Fraction

import numpy as np

from .constants import C_LIGHT


def two_sum(a: float, b: float) -> tuple[float, float]:
    """a + b as (rounded sum, exact rounding error): error-free, so no rounding is ever lost (Knuth)."""
    s = a + b
    bb = s - a
    return s, (a - (s - bb)) + (b - bb)


class Exact3:
    """A 3-vector account summed without losing rounding: its value is hi + lo, lo collecting each error."""

    def __init__(self):
        self.hi, self.lo = [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]

    def add(self, x) -> None:
        for i in range(3):
            self.hi[i], e = two_sum(self.hi[i], float(x[i]))
            self.lo[i] += e

    def fractions(self) -> list:
        return [Fraction(self.hi[i]) + Fraction(self.lo[i]) for i in range(3)]

    def floats(self) -> list:
        return [self.hi[i] + self.lo[i] for i in range(3)]


class Momenta:
    """Every body's momentum, the state the stepper kicks: p plus its collected rounding c."""

    def __init__(self, m: np.ndarray, vel: np.ndarray):
        self.p = m[:, np.newaxis] * vel
        self.c = np.zeros_like(self.p)

    def add(self, x: np.ndarray) -> None:
        s = self.p + x
        bb = s - self.p
        self.c += (self.p - (s - bb)) + (x - bb)
        self.p = s

    def add_pairs(self, forces: np.ndarray, h: float) -> None:
        """Gravity for a kick of length h. Each body's pushes are added up in a pairwise tree, keeping every
        rounding error, so the total equals the exact sum and each pair's equal and opposite pushes cancel."""
        n = forces.shape[1]
        width = 1 << (n - 1).bit_length()  # pad to a power of two once, then halve
        x = np.zeros((n, width, 3))
        np.multiply(forces, h, out=x[:, :n])
        err = np.zeros_like(self.p)
        while width > 1:
            width //= 2
            a, b = x[:, :width], x[:, width:2 * width]
            s = a + b
            bb = s - a
            err += ((a - (s - bb)) + (b - bb)).sum(axis=1)
            x = s
        self.add(x[:, 0])
        self.c += err

    def velocity(self, m: np.ndarray, vel: np.ndarray) -> None:
        """Set the velocity of every body with mass from its momentum (bodies without mass keep theirs)."""
        np.divide(self.p + self.c, m[:, np.newaxis], out=vel, where=(m > 0)[:, np.newaxis])

    def total(self) -> list:
        """Exact total momentum of all bodies, as fractions."""
        return [sum((Fraction(float(x)) for x in self.p[:, i]), Fraction(0))
                + sum((Fraction(float(x)) for x in self.c[:, i]), Fraction(0)) for i in range(3)]

    def take(self, i: int) -> tuple[list, list]:
        """Remove body i's momentum (it leaves the run) and return it exactly, as (p, c) floats."""
        p, c = self.p[i].tolist(), self.c[i].tolist()
        self.p[i] = 0.0
        self.c[i] = 0.0
        return p, c


def _norm(v) -> float:
    return float(sum(x * x for x in v)) ** 0.5


@dataclass
class Ledger:
    applied: Exact3 = field(default_factory=Exact3)   # impulse the beams gave the bodies (J_applied), kg m/s
    station: Exact3 = field(default_factory=Exact3)   # recoil of the stations that fired the beams, kg m/s
    light: Exact3 = field(default_factory=Exact3)     # momentum carried away by bounced light, kg m/s
    departed: Exact3 = field(default_factory=Exact3)  # momentum of asteroids sent away, kg m/s
    work: float = 0.0             # energy the beams put into the bodies, J
    departed_energy: float = 0.0  # energy that left with asteroids sent away, J

    def book_beam(self, beam, v_mid, h: float) -> None:
        """Book one half-kick of length h: the impulse the beam gives the asteroid, its work (at the asteroid's
        mid-kick velocity), the station's recoil when it fired, and the momentum of the bounced light."""
        f = beam.force
        self.work += (f[0] * v_mid[0] + f[1] * v_mid[1] + f[2] * v_mid[2]) * h
        k = beam.power / C_LIGHT * h
        self.applied.add([f[i] * h for i in range(3)])
        self.station.add([-k * beam.incoming[i] for i in range(3)])
        self.light.add([k * beam.outgoing[i] for i in range(3)])

    def checks(self, start: list, now: list) -> dict:
        """The guide's two ledger checks, from the bodies' exact total momentum at the start and now."""
        applied = self.applied.fractions()
        departed = self.departed.fractions()
        partners = [s + l for s, l in zip(self.station.fractions(), self.light.fractions())]
        d_bodies = [n + d - s0 for n, d, s0 in zip(now, departed, start)]
        j = _norm(applied)
        return {"applied_impulse": j,
                "integrator_honest": _norm([a - b for a, b in zip(d_bodies, applied)]) / j if j else 0.0,
                "nothing_from_nothing": _norm([a + p for a, p in zip(applied, partners)]) / j if j else 0.0}
