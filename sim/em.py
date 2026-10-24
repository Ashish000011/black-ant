"""Electromagnetism: the Lorentz force on wires, and Biot-Savart fields.

Our machine moves Earth with gravity and light, not currents, so nothing in the journey uses this. It is here
for the official benchmarks 1 to 3, and to show with numbers why Octo-Earth's arms cannot push Earth: a closed
loop in a uniform field feels no net force.
"""

import numpy as np

MU0 = 1.25663706212e-6  # vacuum permeability, N/A^2 (CODATA 2018)


def wire_force(current: float, length_vec, field) -> np.ndarray:
    """Force on a straight wire carrying `current` along `length_vec` (m) in a uniform field (T): F = I L x B."""
    return current * np.cross(np.asarray(length_vec, float), np.asarray(field, float))


def loop_force(current: float, points, field) -> np.ndarray:
    """Net force on a closed polygonal circuit through `points` (the last joins back to the first): the sum of
    I dl x B over its segments, with B taken at each segment's middle. `field` is a vector or a function of
    position."""
    p = np.asarray(points, float)
    dl = np.roll(p, -1, axis=0) - p
    mid = p + dl / 2
    b = np.array([field(x) for x in mid]) if callable(field) else np.broadcast_to(np.asarray(field, float), dl.shape)
    return current * np.cross(dl, b).sum(axis=0)


def segment_field(current: float, a, b, point) -> np.ndarray:
    """Exact Biot-Savart field (T) at `point` from a straight segment carrying `current` from a to b:
    B = mu0 I / (4 pi) (dl x r1) / |dl x r1|^2 (dl . (r1/|r1| - r2/|r2|)), with r1 = point - a, r2 = point - b."""
    a, b, p = (np.asarray(x, float) for x in (a, b, point))
    dl, r1, r2 = b - a, p - a, p - b
    c = np.cross(dl, r1)
    return MU0 * current / (4 * np.pi) * c / (c @ c) * (dl @ (r1 / np.linalg.norm(r1) - r2 / np.linalg.norm(r2)))


def wire_field(current: float, points, point) -> np.ndarray:
    """Field at `point` from a wire running through `points` (an open polyline)."""
    p = np.asarray(points, float)
    return sum(segment_field(current, p[k], p[k + 1], point) for k in range(len(p) - 1))
