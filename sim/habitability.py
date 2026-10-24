"""Keeping Earth habitable: sunlight, temperature, liquid water, air and magnetic shielding along the journey.

The guide asks us to show, not assume, what happens to each. Sunlight falls as 1/r^2; the sunlight mirrors
(enabler E3) add what they reflect onto Earth. Temperature follows from the energy balance, with Earth's
greenhouse effect held at today's value (an assumption we state, not a result).
"""

import math

SOLAR_CONSTANT = 1361.0       # W/m^2 at 1 AU (Kopp & Lean 2011)
SIGMA = 5.670374419e-8        # Stefan-Boltzmann constant, W/m^2/K^4
ALBEDO = 0.306                # Earth's Bond albedo (NASA Earth fact sheet)
TODAY_MEAN_K = 288.0          # Earth's global mean surface temperature today


def sunlight(r_au: float, mirror_share: float = 0.0) -> float:
    """Sunlight reaching Earth (W/m^2 across its disc) at r AU, plus what mirrors add as a share of the direct
    sunlight at 1 AU."""
    return SOLAR_CONSTANT / r_au ** 2 + mirror_share * SOLAR_CONSTANT


def equilibrium_temperature(flux: float, albedo: float = ALBEDO) -> float:
    """Temperature (K) at which Earth radiates what it absorbs: T = [S (1 - A) / (4 sigma)]^(1/4)."""
    return (flux * (1 - albedo) / (4 * SIGMA)) ** 0.25


# Today's greenhouse warming: the mean surface temperature minus the equilibrium temperature (about 34 K).
GREENHOUSE_K = TODAY_MEAN_K - equilibrium_temperature(SOLAR_CONSTANT)


def mean_temperature(flux: float, albedo: float = ALBEDO) -> float:
    """Global mean surface temperature (K): equilibrium plus today's greenhouse warming, held fixed (stated)."""
    return equilibrium_temperature(flux, albedo) + GREENHOUSE_K


def mirror_share_needed(r_au: float) -> float:
    """Share of 1-AU sunlight the mirrors must add at r AU to give Earth today's sunlight."""
    return max(0.0, 1.0 - 1.0 / r_au ** 2)


def mirror_area_km2(r_au: float, share: float, earth_radius_m: float = 6.371e6) -> float:
    """Mirror area (km^2) at Earth's distance r that reflects `share` of 1-AU sunlight onto Earth's disc: each
    m^2 catches 1361/r^2 W, so the area is share x r^2 x pi R^2."""
    return share * r_au ** 2 * math.pi * earth_radius_m ** 2 / 1e6


def magnetopause_re(r_au: float, today_re: float = 10.0) -> float:
    """Distance of the magnetopause (Earth radii) at r AU. Solar-wind pressure falls as 1/r^2 and the standoff
    distance scales as pressure^(-1/6) (Chapman-Ferraro), so it grows as r^(1/3): farther out, better shielded."""
    return today_re * r_au ** (1 / 3)


def mean_inverse_r2(a_au: float, e: float) -> float:
    """Orbit average of 1/r^2 (1/AU^2): 1 / (a^2 sqrt(1 - e^2)). Sunlight over a year goes as this."""
    return 1.0 / (a_au ** 2 * math.sqrt(1 - e * e))


def hill_share(a_au: float, earth_mass_kg: float, moon_distance_m: float = 3.844e8, sun_mass_kg: float = 1.98892e30) -> float:
    """The Moon's distance as a share of Earth's Hill sphere, radius a (m / 3 M)^(1/3). Prograde moons stay bound
    out to about half of it; the share falls as Earth moves out."""
    return moon_distance_m / (a_au * 1.495978707e11 * (earth_mass_kg / (3 * sun_mass_kg)) ** (1 / 3))


class Mirrors:
    """The sunlight mirrors (enabler E3) as a schedule, not an assumption. They are built in batches; each batch
    brings the area to what Earth's orbit will need when the batch ends, predicted from how fast the orbit is
    growing. What they deliver is computed from their area and reflectivity: they sit near Earth, so each square
    metre catches the same sunlight per area as Earth does and reflects `reflectivity` of it onto Earth's disc."""

    def __init__(self, cfg: dict, earth_radius_m: float = 6.371e6):
        self.batch = cfg["mirror_batch_years"]
        self.reflect = cfg["mirror_reflectivity"]
        self.disc_km2 = math.pi * earth_radius_m ** 2 / 1e6
        self.area_km2 = 0.0
        self.next_build = 0.0
        self.last = None  # (year, a) at the previous update, for the growth rate

    def update(self, year: float, a_au: float, e: float) -> None:
        rate = 0.0
        if self.last and year > self.last[0]:
            rate = max(0.0, (a_au - self.last[1]) / (year - self.last[0]))
        self.last = (year, a_au)
        if year >= self.next_build:
            a_end = a_au + rate * self.batch
            need = 1.0 / mean_inverse_r2(a_end, e) - 1.0  # extra sunlight, in Earth-discs of 1-AU sunlight
            self.area_km2 = max(self.area_km2, need * self.disc_km2 / self.reflect)
            self.next_build = year + self.batch

    def sunlight_share(self, a_au: float, e: float) -> float:
        """Earth's yearly sunlight with the mirrors, as a share of today's at 1 AU."""
        return mean_inverse_r2(a_au, e) * (1.0 + self.reflect * self.area_km2 / self.disc_km2)
