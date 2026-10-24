"""A sample of massless test asteroids spread through the main belt.

Their orbits are real ones: drawn at random from JPL Small-Body Database main-belt asteroids
(orbits_file), each placed at a random point along its orbit. Without that file, orbits are made up
from the spreads in config.yaml (colder than the real belt: more slow, strongly focused passes).

They feel the Sun and planets but pull on nothing. Every pass within close_pass_au of Earth is an
encounter: we keep its closest distance (interpolating between steps so fast passes are not missed)
and relative speed, turn it into a chance of hitting, and scale the sample up to the real belt to
estimate how many real asteroids over 1 km would hit Earth, while crossing the belt and once parked.
"""

import json
import math

import numpy as np

from .bodies import state_from_elements
from .config import ROOT
from .constants import AU, G, GM_SUN

R_EARTH = 6.371e6         # m
V_ESCAPE_EARTH = 11186.0  # m/s
PLANET_MASS_MIN = 1e23    # kg; lighter bodies (the big asteroids, tow asteroids) barely move the sample


class BeltSample:
    def __init__(self, cfg: dict, sun_pos, sun_vel, year: float):
        rng = np.random.default_rng(int(cfg["seed"]))
        n = int(cfg["count"])
        if cfg.get("orbits_file"):
            rows = json.loads((ROOT / cfg["orbits_file"]).read_text(encoding="utf-8"))["data"]
            skip = set(cfg.get("skip_numbers", []))
            rows = [r for r in rows if int(r[0].split()[0]) not in skip]
            pick = rng.choice(len(rows), size=n, replace=False)
            a, e, inc, node, arg_peri = (np.array([float(rows[k][c]) for k in pick]) for c in range(1, 6))
            mean_anom = rng.uniform(0.0, 360.0, n)
        else:
            lo, hi = cfg["a_au"]
            a = rng.uniform(lo, hi, n)
            e = np.clip(np.abs(rng.normal(0.0, cfg["e_spread"], n)), 0.0, 0.3)
            inc = np.clip(np.abs(rng.normal(0.0, cfg["i_spread_deg"], n)), 0.0, 30.0)
            node, arg_peri, mean_anom = rng.uniform(0.0, 360.0, (3, n))
        pos, vel = [], []
        for k in range(n):
            r, v = state_from_elements({"a_au": a[k], "e": e[k], "i_deg": inc[k], "node_longitude_deg": node[k],
                                        "perihelion_longitude_deg": node[k] + arg_peri[k],
                                        "mean_longitude_deg": node[k] + arg_peri[k] + mean_anom[k]}, GM_SUN)
            pos.append(r)
            vel.append(v)
        self.cfg = cfg
        self.start_year = year
        self.pos = np.array(pos) + np.asarray(sun_pos)
        self.vel = np.array(vel) + np.asarray(sun_vel)
        self.x = cfg["close_pass_au"] * AU
        self.min_dist = np.full(n, np.inf)       # each one's closest pass to Earth, m
        self.inside = np.zeros(n, bool)          # within x of Earth right now
        self.enc_min = np.full(n, np.inf)        # the current encounter's closest distance and speed
        self.enc_speed = np.zeros(n)
        self.encounters: list[tuple[float, float, float]] = []  # (year, closest m, relative speed m/s)

    def accel(self, m: np.ndarray, pos: np.ndarray) -> np.ndarray:
        """Acceleration of every test asteroid from the Sun and planets."""
        x, y, z = self.pos[:, 0], self.pos[:, 1], self.pos[:, 2]
        ax, ay, az = np.zeros_like(x), np.zeros_like(x), np.zeros_like(x)
        for j in np.flatnonzero(m > PLANET_MASS_MIN):
            px, py, pz = pos[j]
            dx, dy, dz = px - x, py - y, pz - z
            r2 = dx * dx + dy * dy + dz * dz
            w = G * m[j] / (r2 * np.sqrt(r2))
            ax += dx * w
            ay += dy * w
            az += dz * w
        return np.stack((ax, ay, az), axis=1)

    def track(self, earth_before, earth_after, prev_pos, dt: float, year: float) -> None:
        """Follow each test asteroid's distance to Earth over the last step and log finished encounters."""
        rel0 = prev_pos - earth_before
        step = (self.pos - earth_after) - rel0
        s2 = np.maximum((step * step).sum(axis=1), 1e-30)
        t = np.clip(-(rel0 * step).sum(axis=1) / s2, 0.0, 1.0)
        closest = rel0 + t[:, np.newaxis] * step
        d = np.sqrt((closest * closest).sum(axis=1))
        np.minimum(self.min_dist, d, out=self.min_dist)
        near = d < self.x
        if near.any():
            better = near & (d < self.enc_min)
            self.enc_min[better] = d[better]
            self.enc_speed[better] = np.sqrt(s2[better]) / dt
        for k in np.flatnonzero(self.inside & ~near):
            self._close(k, year)
        self.inside = near

    def _close(self, k: int, year: float) -> None:
        self.encounters.append((year, float(self.enc_min[k]), float(self.enc_speed[k])))
        self.enc_min[k], self.enc_speed[k] = math.inf, 0.0

    def _expected_hits(self, encounters) -> float:
        """Each pass within x hits with Earth's gravitationally focused cross-section over a disc of radius x."""
        scale = self.cfg["real_population_over_1km"] / len(self.min_dist)
        return sum(R_EARTH ** 2 * (1 + (V_ESCAPE_EARTH / max(v, 1.0)) ** 2) / self.x ** 2 for _, _, v in encounters) * scale

    def summary(self, end_year: float, natural_interval_years: float, arrival_year: float | None) -> dict:
        """Close passes in the sample, scaled up to the real belt, against Earth's natural impact rate."""
        for k in np.flatnonzero(self.inside):
            self._close(k, end_year)
        self.inside[:] = False
        split = arrival_year if arrival_year is not None else end_year
        crossing = [e for e in self.encounters if e[0] < split]
        parked = [e for e in self.encounters if e[0] >= split]
        crossing_years, parked_years = split - self.start_year, end_year - split
        hits_crossing, hits_parked = self._expected_hits(crossing), self._expected_hits(parked)
        natural_rate = 1.0 / natural_interval_years
        total_years = end_year - self.start_year
        speeds = [v for _, _, v in self.encounters]
        return {"sample_size": len(self.min_dist), "years_tracked": round(total_years), "close_pass_au": self.cfg["close_pass_au"],
                "sample_encounters": len(self.encounters),
                "sample_closest_au": round(float(self.min_dist.min() / AU), 5),
                "sample_direct_hits": sum(1 for _, d, _ in self.encounters if d < R_EARTH),
                "encounter_speed_median_km_s": round(float(np.median(speeds)) / 1e3, 2) if speeds else None,
                "expected_real_impacts_over_1km": hits_crossing + hits_parked,
                "natural_impacts_same_years": total_years * natural_rate,
                "times_natural_rate": (hits_crossing + hits_parked) / (total_years * natural_rate) if total_years > 0 else 0.0,
                "crossing": {"years": round(crossing_years), "sample_encounters": len(crossing),
                             "expected_impacts": hits_crossing,
                             "years_per_impact": crossing_years / hits_crossing if hits_crossing else math.inf},
                "parked_at_target": {"years": round(parked_years), "sample_encounters": len(parked),
                                     "expected_impacts": hits_parked,
                                     "years_per_impact": parked_years / hits_parked if hits_parked else math.inf,
                                     "times_natural_rate": hits_parked / (parked_years * natural_rate) if parked_years > 0 else 0.0}}
