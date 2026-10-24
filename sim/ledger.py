"""The force ledger: every beam push is booked together with its partners.

Gravity between bodies needs no booking: the stepper applies each pair equally and oppositely.
A beam's push on an asteroid is balanced by two accounts: the station that fired it recoils, and
the bounced light carries momentum away. Asteroids sent away at the end of a tow take their
momentum and energy with them, so those are booked too.
"""

from dataclasses import dataclass, field

import numpy as np

from .constants import C_LIGHT


def _zero():
    return [0.0, 0.0, 0.0]


@dataclass
class Ledger:
    station: list = field(default_factory=_zero)   # recoil of the stations that fired the beams, kg m/s
    light: list = field(default_factory=_zero)     # momentum carried away by bounced light, kg m/s
    departed: list = field(default_factory=_zero)  # momentum of asteroids sent away, kg m/s
    work: float = 0.0             # energy the beams put into the bodies, J
    departed_energy: float = 0.0  # energy that left with asteroids sent away, J

    def book_beam(self, beam, v_mid, h: float) -> None:
        """Book one half-kick of length h: the beam's work on the asteroid (at its mid-kick
        velocity), the station's recoil when it fired, and the momentum of the bounced light."""
        f = beam.force
        self.work += (f[0] * v_mid[0] + f[1] * v_mid[1] + f[2] * v_mid[2]) * h
        k = beam.power / C_LIGHT * h
        for i in range(3):
            self.station[i] -= k * beam.incoming[i]
            self.light[i] += k * beam.outgoing[i]

    def total_momentum(self, m: np.ndarray, vel: np.ndarray) -> np.ndarray:
        """Momentum of every body plus every account. It should never change."""
        return m @ vel + np.array(self.station) + np.array(self.light) + np.array(self.departed)
