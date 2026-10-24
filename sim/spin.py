"""Earth's spin axis and axial tilt, followed on top of a recorded orbit.

The Sun and Moon pull on Earth's equatorial bulge and turn the spin axis s around the orbit's pole n:
    ds/dt = alpha (s.n)(s x n)
alpha, the precession constant, is today's lunisolar precession rate over cos(tilt) (IAU 2006). The
Sun's share scales with 1/(a^3 (1-e^2)^1.5); the Moon's share stays (the Moon keeps its distance). The
Moon/Sun split is the ratio of their tidal pulls, m/d^3 of the Moon over that of the Sun.

At 2.7 AU the Sun's share drops about 20 times, so the axis turns more slowly (about 35 instead of 50
arcseconds a year). If that rate nears one of the rates at which the planets tip Earth's orbit plane,
the tilt swings far more than today's 22.1-24.5 degrees (as Mars's does).
"""

import math

import numpy as np

from .constants import AU

# Earth's north pole today, in the J2000 ecliptic frame: ecliptic latitude 90 - 23.439 deg, longitude 90 deg.
TODAY_AXIS = (0.0, math.sin(math.radians(23.439)), math.cos(math.radians(23.439)))


def alphas(a_au, e, spin: dict) -> np.ndarray:
    tilt0 = math.radians(spin["tilt_today_deg"])
    alpha_today = math.radians(spin["lunisolar_precession_arcsec_per_year"] / 3600) / math.cos(tilt0)
    ratio = (spin["moon_mass_kg"] / spin["moon_distance_m"] ** 3) / (spin["sun_mass_kg"] / AU ** 3)
    alpha_sun0 = alpha_today / (1 + ratio) * (1 - spin["earth_e_today"] ** 2) ** 1.5
    alpha_moon = alpha_today * ratio / (1 + ratio)
    return alpha_moon + alpha_sun0 / (np.asarray(a_au) ** 3 * (1 - np.asarray(e) ** 2) ** 1.5)


def follow_spin(years, poles, a_au, e, spin: dict, s0=None) -> tuple[list[float], list[float]]:
    """Tilt (degrees) at each sample and the final spin axis. s0: starting axis (default: today's tilt
    from the first pole, leaning along the pole x (1, 0, 0) direction)."""
    n = np.asarray(poles, float)
    t = np.asarray(years, float)
    if len(t) < 2:
        return [], list(s0) if s0 is not None else []
    alpha = alphas(a_au, e, spin)
    if s0 is None:
        tilt0 = math.radians(spin["tilt_today_deg"])
        side = np.cross(n[0], [1.0, 0.0, 0.0])
        side /= np.linalg.norm(side)
        s = n[0] * math.cos(tilt0) + side * math.sin(tilt0)
    else:
        s = np.asarray(s0, float)
        s = s / np.linalg.norm(s)

    def at(k, frac):
        nn = n[k] + (n[k + 1] - n[k]) * frac
        return nn / np.linalg.norm(nn), alpha[k] + (alpha[k + 1] - alpha[k]) * frac

    def rate(s, nn, al):
        return al * float(s @ nn) * np.cross(s, nn)

    out = [math.degrees(math.acos(float(np.clip(s @ n[0], -1, 1))))]
    for k in range(len(t) - 1):
        h = t[k + 1] - t[k]
        steps = max(1, round(h / spin["step_years"]))
        dh = h / steps
        for j in range(steps):  # fourth-order Runge-Kutta, pole interpolated between samples
            n_a, a_a = at(k, j / steps)
            n_b, a_b = at(k, (j + 0.5) / steps)
            n_c, a_c = at(k, (j + 1) / steps)
            k1 = rate(s, n_a, a_a)
            k2 = rate(s + 0.5 * dh * k1, n_b, a_b)
            k3 = rate(s + 0.5 * dh * k2, n_b, a_b)
            k4 = rate(s + dh * k3, n_c, a_c)
            s = s + dh / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
            s /= np.linalg.norm(s)
        out.append(math.degrees(math.acos(float(np.clip(s @ n[k + 1], -1, 1)))))
    return out, s.tolist()


def orbit_pole(p, v, sp, sv) -> list[float]:
    """Unit vector along a body's heliocentric orbital angular momentum."""
    r = np.asarray(p, float) - np.asarray(sp, float)
    u = np.asarray(v, float) - np.asarray(sv, float)
    h = np.cross(r, u)
    return (h / np.linalg.norm(h)).tolist()


def daily_sunlight(tilt_deg: float, lat_steps: int = 180, day_steps: int = 360) -> tuple[np.ndarray, np.ndarray]:
    """Daily mean sunlight (relative units) at each latitude and day of a circular orbit, and each latitude's
    area weight. Solar declination: sin d = sin(tilt) sin(L); Q = (h0 sin(lat) sin d + cos(lat) cos d sin h0) / pi."""
    lat = np.radians(np.linspace(-89.5, 89.5, lat_steps))[:, None]
    lon = np.linspace(0, 2 * np.pi, day_steps, endpoint=False)[None, :]
    dec = np.arcsin(np.sin(math.radians(tilt_deg)) * np.sin(lon))
    cos_h0 = np.clip(-np.tan(lat) * np.tan(dec), -1.0, 1.0)
    h0 = np.arccos(cos_h0)
    q = (h0 * np.sin(lat) * np.sin(dec) + np.cos(lat) * np.cos(dec) * np.sin(h0)) / np.pi
    return q, np.cos(lat)


def seasons_shift(tilt_deg: float, reference_deg: float) -> float:
    """Share of Earth's yearly sunlight that would have to land at other latitudes or seasons for a tilt of
    tilt_deg to give the same pattern as reference_deg. Tilt never changes the total, only where and when."""
    q, w = daily_sunlight(tilt_deg)
    ref, _ = daily_sunlight(reference_deg)
    return float(0.5 * (np.abs(q - ref) * w).sum() / (ref * w).sum())
