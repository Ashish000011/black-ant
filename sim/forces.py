"""The tows: where each asteroid should sit, and the beam force that keeps it there (3D).

These functions run twice per tow per step, so they use plain Python numbers written out by
component; that is several times faster than NumPy for 3-element vectors.
"""

import math
from dataclasses import dataclass, field

from .constants import C_LIGHT

Vec = tuple[float, float, float]


@dataclass
class Beam:
    force: Vec = (0.0, 0.0, 0.0)     # push on the asteroid, N
    power: float = 0.0               # W
    incoming: Vec = (0.0, 0.0, 0.0)  # direction the light travels as it arrives
    outgoing: Vec = (0.0, 0.0, 0.0)  # direction the bounced light leaves
    route_deg: float = 0.0           # how far off the Sun line the light arrives


@dataclass
class Tow:
    name: str
    target: int          # index of the planet being towed
    asteroid: int        # index of the asteroid body
    mass: float          # asteroid mass, kg
    distance: float      # asteroid distance from its target, m
    stop_au: float       # the tow stops when the target's orbit reaches this size
    max_beam_w: float    # most this tow may ever use (its mirror and cables are sized for it)
    lift: float = 0.0    # radians above the target's orbit plane (the arrival trim tips the plane with it)
    home: float = 0.0    # resting distance, m: the trim swings around it; a sprint moves it (0 means `distance`)
    shape: object = None # arrival trim: longitude -> spot offsets and their rates (sim/secular.py), or None
    active: bool = True
    beam: Beam = field(default_factory=Beam)
    no_route_steps: int = 0  # steps where no allowed beam could hold the asteroid
    rerouted_steps: int = 0  # steps where the light came in off the Sun line to miss Earth
    capped_steps: int = 0    # steps where the power cap limited the force


def _row(arr, i):
    """Row i as plain floats; arr may be a NumPy array or a list of [x, y, z] rows."""
    r = arr[i]
    return r if isinstance(r, list) else (float(r[0]), float(r[1]), float(r[2]))


def orbit_frame(pos, vel, sun: int, target: int):
    """Unit vectors for a planet's orbit: out (away from the Sun), ahead (direction of travel within
    the orbit's plane), normal (perpendicular to the plane); plus its angular speed around the Sun."""
    p, s, v, sv = _row(pos, target), _row(pos, sun), _row(vel, target), _row(vel, sun)
    rx, ry, rz = p[0] - s[0], p[1] - s[1], p[2] - s[2]
    vx, vy, vz = v[0] - sv[0], v[1] - sv[1], v[2] - sv[2]
    r2 = rx * rx + ry * ry + rz * rz
    rn = math.sqrt(r2)
    ox, oy, oz = rx / rn, ry / rn, rz / rn
    hx, hy, hz = ry * vz - rz * vy, rz * vx - rx * vz, rx * vy - ry * vx
    hn = math.sqrt(hx * hx + hy * hy + hz * hz)
    nx, ny, nz = hx / hn, hy / hn, hz / hn
    ahead = (ny * oz - nz * oy, nz * ox - nx * oz, nx * oy - ny * ox)
    return (ox, oy, oz), ahead, (nx, ny, nz), hn / r2


def _spot(frame, p, v, a, distance, shape=None):
    """The spot is k (out + ahead) + kn (normal) from the target. Without a shape, k = distance / sqrt 2 and
    kn = 0, fixed; with one, k and kn follow the target's longitude L, and their rates (per radian of L,
    times the angular speed w) are fed forward so the controller is not left chasing the spot."""
    (ox, oy, oz), (tx, ty, tz), (nx, ny, nz), w = frame
    if shape is None:
        k, k1, k2, kn, kn1, kn2 = distance * math.sqrt(0.5), 0.0, 0.0, 0.0, 0.0, 0.0
    else:
        k, k1, k2, kn, kn1, kn2 = shape(math.atan2(oy, ox))
    kd, kdd, knd, kndd = k1 * w, k2 * w * w, kn1 * w, kn2 * w * w  # rates in time
    kw, kww = k * w, k * w * w
    return ((p[0] + k * (ox + tx) + kn * nx, p[1] + k * (oy + ty) + kn * ny, p[2] + k * (oz + tz) + kn * nz),
            (v[0] + kd * (ox + tx) + kw * (tx - ox) + knd * nx,
             v[1] + kd * (oy + ty) + kw * (ty - oy) + knd * ny,
             v[2] + kd * (oz + tz) + kw * (tz - oz) + knd * nz),
            (a[0] + (kdd - kww) * (ox + tx) + 2 * kd * w * (tx - ox) + kndd * nx,
             a[1] + (kdd - kww) * (oy + ty) + 2 * kd * w * (ty - oy) + kndd * ny,
             a[2] + (kdd - kww) * (oz + tz) + 2 * kd * w * (tz - oz) + kndd * nz))


def spot(pos, vel, acc, sun: int, target: int, distance: float, shape=None):
    """Where a tow's asteroid should sit: `distance` from its target, at 45 degrees between straight
    ahead and straight away from the Sun, in the target's orbit plane (or as the arrival trim's shape sets).
    Returns the spot's position, velocity and acceleration (3-tuples), following the target around the Sun."""
    return _spot(orbit_frame(pos, vel, sun, target), _row(pos, target), _row(vel, target), _row(acc, target),
                 distance, shape)


def ray_distance(q, o, u, max_len: float = math.inf) -> float:
    """Closest distance from point q to the ray that starts at o and runs along unit vector u."""
    dx, dy, dz = q[0] - o[0], q[1] - o[1], q[2] - o[2]
    s = max(0.0, min(max_len, dx * u[0] + dy * u[1] + dz * u[2]))
    dx, dy, dz = dx - s * u[0], dy - s * u[1], dz - s * u[2]
    return math.sqrt(dx * dx + dy * dy + dz * dz)


def beam_for(tow: Tow, m, pos, vel, acc, sun: int, earth: int, kp: float, kd: float,
             clearance: float, routes, cap: float | None = None) -> tuple[Beam | None, bool]:
    """The beam that holds a tow's asteroid on its spot, and whether the power cap limited it.

    The controller asks for: feed-forward (what the spot's motion needs, minus the gravity the
    asteroid already feels) plus a correction for any drift. Light arriving along direction "in"
    and bouncing off toward "out" pushes with (P/c)(in - out); the power that gives force f is
    P = |f|^2 c / (2 in.f), so light can only push with a part along its own direction.
    Light normally arrives straight out from the Sun. If that beam, or its bounce, would pass
    closer to Earth than `clearance`, collectors off the line fire instead: the arrival direction
    is turned by each angle in `routes` about the target's orbit normal, smallest turn first.
    cap: the power available right now (E1's budget left after other tows), if lower than max_beam_w.
    Returns (None, False) when no allowed beam can do it.
    """
    limit = tow.max_beam_w if cap is None else min(cap, tow.max_beam_w)
    a = tow.asteroid
    frame = orbit_frame(pos, vel, sun, tow.target)
    sp, sv, sa = _spot(frame, _row(pos, tow.target), _row(vel, tow.target), _row(acc, tow.target), tow.distance, tow.shape)
    ap, av, aa = _row(pos, a), _row(vel, a), _row(acc, a)
    mass = float(m[a])
    fx = mass * (sa[0] - aa[0] + kp * (sp[0] - ap[0]) + kd * (sv[0] - av[0]))
    fy = mass * (sa[1] - aa[1] + kp * (sp[1] - ap[1]) + kd * (sv[1] - av[1]))
    fz = mass * (sa[2] - aa[2] + kp * (sp[2] - ap[2]) + kd * (sv[2] - av[2]))
    f_len = math.sqrt(fx * fx + fy * fy + fz * fz)
    s0 = _row(pos, sun)
    rx, ry, rz = ap[0] - s0[0], ap[1] - s0[1], ap[2] - s0[2]
    r = math.sqrt(rx * rx + ry * ry + rz * rz)
    hx, hy, hz = rx / r, ry / r, rz / r  # straight out from the Sun at the asteroid
    nx, ny, nz = frame[2]
    cx, cy, cz = ny * hz - nz * hy, nz * hx - nx * hz, nx * hy - ny * hx  # normal x radial
    nd = nx * hx + ny * hy + nz * hz
    ep = _row(pos, earth)
    for deg, c, s in routes:
        # Turn the Sun-line direction by deg about the orbit normal (Rodrigues' rotation).
        ix = hx * c + cx * s + nx * nd * (1 - c)
        iy = hy * c + cy * s + ny * nd * (1 - c)
        iz = hz * c + cz * s + nz * nd * (1 - c)
        along = ix * fx + iy * fy + iz * fz
        if along <= 1e-6 * f_len:
            continue  # this light can't pull the asteroid back toward its source
        power = f_len * f_len * C_LIGHT / (2 * along)
        gx, gy, gz, capped = fx, fy, fz, power > limit
        if capped:  # power scales with force, so scale both down to the cap
            k = limit / power
            gx, gy, gz, power = fx * k, fy * k, fz * k, limit
        q = C_LIGHT / power
        ux, uy, uz = ix - gx * q, iy - gy * q, iz - gz * q
        u_len = math.sqrt(ux * ux + uy * uy + uz * uz)
        out = (ux / u_len, uy / u_len, uz / u_len)
        if min(ray_distance(ep, ap, (-ix, -iy, -iz), r), ray_distance(ep, ap, out)) < clearance:
            continue
        return Beam((gx, gy, gz), power, (ix, iy, iz), out, deg), capped
    return None, False
