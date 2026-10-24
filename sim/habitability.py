"""Keeping Earth habitable: sunlight, temperature, liquid water, air, magnetic shielding, day length and the Moon.

The guide asks us to show, not assume, what happens to each, and the company's reference demo
(octo-earth-simulator.vercel.app) checks ten indicators, which we adopt (config.yaml, safety). Sunlight falls as
1/r^2; the sunlight mirrors (enabler E3) add what they reflect onto Earth. Temperature comes from a
zero-dimensional energy balance with ice-albedo feedback (Budyko 1969, Sellers 1969), its effective emissivity
set so that today's sunlight gives today's 288 K (an assumption we state: the greenhouse effect stays as it is).
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


# Ice-albedo feedback: albedo 0.30 when warm, rising to 0.62 as ice spreads (as in the reference demo).
WARM_ALBEDO, ICE_ALBEDO = 0.30, 0.62
WARM_K, ICE_K = 280.0, 250.0
# Effective emissivity: what makes today's sunlight give today's 288 K (greenhouse effect held as it is).
EMISSIVITY = SOLAR_CONSTANT * (1 - WARM_ALBEDO) / (4 * SIGMA * TODAY_MEAN_K ** 4)
RUNAWAY_W_M2 = 282.0          # absorbed sunlight that would trigger a runaway greenhouse (Goldblatt et al. 2013)


def albedo_at(t_k: float) -> float:
    """Earth's albedo at global mean temperature t: more ice, brighter Earth."""
    if t_k >= WARM_K:
        return WARM_ALBEDO
    if t_k <= ICE_K:
        return ICE_ALBEDO
    return ICE_ALBEDO + (WARM_ALBEDO - ICE_ALBEDO) * (t_k - ICE_K) / (WARM_K - ICE_K)


def mean_temperature(flux: float, start_k: float = TODAY_MEAN_K) -> float:
    """Steady global mean surface temperature (K): sunlight absorbed, (S/4)(1 - A(T)), equals what Earth radiates,
    eps sigma T^4. With ice-albedo feedback there can be a warm and a frozen answer; this follows the one the
    climate reaches from `start_k` (its previous state)."""
    t = start_k
    for _ in range(500):
        new = (flux * (1 - albedo_at(t)) / (4 * EMISSIVITY * SIGMA)) ** 0.25
        if abs(new - t) < 1e-9:
            break
        t = 0.5 * (t + new)
    return t


def absorbed_flux(flux: float, t_k: float) -> float:
    """Sunlight Earth absorbs, averaged over its surface (W/m^2): (S/4)(1 - A)."""
    return flux / 4 * (1 - albedo_at(t_k))


# Surface temperature by latitude follows T(x) = T_mean + T2 P2(x), x = sin(latitude), P2 = (3x^2 - 1)/2
# (North 1975). T2 is set so that today's 288 K leaves 82% of the surface above freezing, as the demo has it.
_P2_TODAY = (3 * 0.82 ** 2 - 1) / 2
LATITUDE_T2_K = (273.15 - TODAY_MEAN_K) / _P2_TODAY


def liquid_water_share(t_mean_k: float) -> float:
    """Share of Earth's surface warm enough for liquid water (above 273.15 K), from the latitude profile."""
    p2 = (273.15 - t_mean_k) / LATITUDE_T2_K
    x2 = (2 * p2 + 1) / 3
    return min(1.0, max(0.0, math.sqrt(max(x2, 0.0))))


def jeans_lambda(sunlight_share: float, molecule_amu: float = 28.0) -> float:
    """Jeans escape parameter for a gas at the exobase (500 km up): lambda = G M m / (k T_exo r). The exosphere
    runs at about 1,000 K today and scales as the square root of sunlight. Above about 30, escape is negligible."""
    t_exo = 1000.0 * math.sqrt(max(sunlight_share, 1e-9))
    m = molecule_amu * 1.66053907e-27
    return 3.986004e14 * m / (1.380649e-23 * t_exo * (6.371e6 + 5.0e5))


def day_length_rate(mass_kg: float, distance_m: float, k2_over_q: float = 0.025) -> float:
    """How fast a body's tide lengthens Earth's day (seconds per second): torque (3/2)(k2/Q) G m^2 R^5 / d^6 on
    Earth's moment of inertia C = 8.04e37 kg m^2; d(LOD)/dt = LOD^2 torque / (2 pi C)."""
    torque = 1.5 * k2_over_q * 6.674e-11 * mass_kg ** 2 * 6.371e6 ** 5 / distance_m ** 6
    return 86164.0 ** 2 * torque / (2 * math.pi * 8.04e37)


def thrust_over_moon_pull(tow_mass_kg: float, tow_distance_m: float, moon_mass_kg: float = 7.342e22,
                          moon_distance_m: float = 3.844e8) -> float:
    """The tow's pull on Earth against Earth's pull on the Moon: if it stays small, Earth does not leave the Moon
    behind. Both share Earth's mass, so it is (m / d^2) over (M_moon / r_moon^2)."""
    return (tow_mass_kg / tow_distance_m ** 2) / (moon_mass_kg / moon_distance_m ** 2)


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
    brings the area to what Earth's orbit will need when the batch ends, predicted from how fast the orbit grew
    since the last batch (over the whole batch: Earth's orbit size wobbles from month to month, so a short-term
    rate is noise). What they deliver is computed from their area and reflectivity: they sit near Earth, so each
    square metre catches the same sunlight per area as Earth does and reflects `reflectivity` of it onto Earth."""

    def __init__(self, cfg: dict, earth_radius_m: float = 6.371e6):
        self.batch = cfg["mirror_batch_years"]
        self.reflect = cfg["mirror_reflectivity"]
        self.disc_km2 = math.pi * earth_radius_m ** 2 / 1e6
        self.area_km2 = 0.0
        self.next_build = 0.0
        self.last_build = None  # (year, a) when the previous batch was built, for the growth rate

    def update(self, year: float, a_au: float, e: float) -> None:
        if year >= self.next_build:
            rate = 0.0
            if self.last_build and year > self.last_build[0]:
                rate = max(0.0, (a_au - self.last_build[1]) / (year - self.last_build[0]))
            self.last_build = (year, a_au)
            a_end = a_au + rate * self.batch
            need = 1.0 / mean_inverse_r2(a_end, e) - 1.0  # extra sunlight, in Earth-discs of 1-AU sunlight
            self.area_km2 = max(self.area_km2, need * self.disc_km2 / self.reflect)
            self.next_build = year + self.batch

    def sunlight_share(self, a_au: float, e: float) -> float:
        """Earth's yearly sunlight with the mirrors, as a share of today's at 1 AU."""
        return mean_inverse_r2(a_au, e) * (1.0 + self.reflect * self.area_km2 / self.disc_km2)
