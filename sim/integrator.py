"""Gravity between all bodies, and the leapfrog stepper (kick, drift, kick)."""

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
             on_step=None) -> None:
    """Advance a gravity-only system in place. on_step(step, pos, vel) is called after each step."""
    acc = gravity(m, pos)
    for n in range(steps):
        vel += acc * (dt / 2)
        pos += vel * dt
        acc = gravity(m, pos)
        vel += acc * (dt / 2)
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
