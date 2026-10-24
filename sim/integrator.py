"""Gravity between all bodies, the leapfrog stepper (kick, drift, kick) and Yoshida's fourth-order stepper.

Both are symplectic: energy errors oscillate instead of drifting over long runs. Leapfrog's errors shrink as
the step squared, Yoshida's as the step to the fourth (three leapfrog sub-steps with weights 1/(2 - 2^(1/3))
and -2^(1/3)/(2 - 2^(1/3)); Yoshida 1990).
"""

import numpy as np

from .constants import G


def gravity(m: np.ndarray, pos: np.ndarray) -> np.ndarray:
    """Acceleration of every body from every other body's gravity, shape (N, 2).

    Each pair uses the same separation and distance in both directions, so the pull of i on j
    and of j on i are exactly equal and opposite (Newton's third law, up to rounding).
    """
    d = pos[np.newaxis, :, :] - pos[:, np.newaxis, :]  # d[i, j] points from i to j
    r2 = (d * d).sum(axis=2)
    np.fill_diagonal(r2, np.inf)
    weight = m[np.newaxis, :] * r2 ** -1.5  # G is applied once at the end
    return G * (d * weight[:, :, np.newaxis]).sum(axis=1)


def leapfrog(m: np.ndarray, pos: np.ndarray, vel: np.ndarray, dt: float, steps: int,
             on_step=None, push=None) -> None:
    """Advance a system in place. on_step(step, pos, vel) is called after each step; push(pos, vel), if
    given, returns an extra acceleration (N, 3) added to gravity at each kick."""
    def accel():
        a = gravity(m, pos)
        return a if push is None else a + push(pos, vel)

    acc = accel()
    for n in range(steps):
        vel += acc * (dt / 2)
        pos += vel * dt
        acc = accel()
        vel += acc * (dt / 2)
        if on_step is not None:
            on_step(n + 1, pos, vel)


_W1 = 1 / (2 - 2 ** (1 / 3))
_W0 = -(2 ** (1 / 3)) * _W1
YOSHIDA_DRIFTS = (_W1 / 2, (_W0 + _W1) / 2, (_W0 + _W1) / 2, _W1 / 2)
YOSHIDA_KICKS = (_W1, _W0, _W1)


def yoshida4(m: np.ndarray, pos: np.ndarray, vel: np.ndarray, dt: float, steps: int,
             on_step=None, push=None) -> None:
    """Advance a system in place with Yoshida's fourth-order stepper. push(pos, vel), if given, returns an
    extra acceleration (N, 3) added to gravity at each kick (for benchmarks with a small applied push)."""
    for n in range(steps):
        for k in range(3):
            pos += vel * (YOSHIDA_DRIFTS[k] * dt)
            acc = gravity(m, pos)
            if push is not None:
                acc = acc + push(pos, vel)
            vel += acc * (YOSHIDA_KICKS[k] * dt)
        pos += vel * (YOSHIDA_DRIFTS[3] * dt)
        if on_step is not None:
            on_step(n + 1, pos, vel)


def energy(m: np.ndarray, pos: np.ndarray, vel: np.ndarray) -> float:
    """Total kinetic plus gravitational energy of all bodies with mass, J."""
    keep = m > 0
    m, pos, vel = m[keep], pos[keep], vel[keep]
    kinetic = 0.5 * float(m @ (vel * vel).sum(axis=1))
    d = pos[np.newaxis, :, :] - pos[:, np.newaxis, :]
    r = np.sqrt((d * d).sum(axis=2))
    i, j = np.triu_indices(len(m), k=1)
    potential = -G * float((m[i] * m[j] / r[i, j]).sum())
    return kinetic + potential


def pair_forces(m: np.ndarray, pos: np.ndarray) -> np.ndarray:
    """Gravity between every pair as forces, shape (N, N, 3): F[i, j] is the pull on i from j. Each pair's two
    forces are exact negatives of each other, bit for bit (same product of masses, same distance, negated
    separation), so adding both to the two bodies' momenta cancels exactly."""
    d = pos[np.newaxis, :, :] - pos[:, np.newaxis, :]
    r2 = (d * d).sum(axis=2)
    np.fill_diagonal(r2, np.inf)
    mm = m[:, np.newaxis] * m[np.newaxis, :]
    return (G * mm * r2 ** -1.5)[:, :, np.newaxis] * d
