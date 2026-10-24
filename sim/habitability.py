"""Keeping Earth habitable: sunlight, temperature, liquid water, air and magnetic shielding along the journey.

The guide asks us to show, not assume, what happens to each. Sunlight falls as 1/r^2; the sunlight mirrors
(enabler E3) add what they reflect onto Earth. Temperature follows from the energy balance, with Earth's
greenhouse effect held at today's value (an assumption we state, not a result).
"""

import math

SOLAR_CONSTANT = 1361.0       # W/m^2 at 1 AU (Kopp & Lean 2011)
SIGMA = 5.670374419e-8        # Stefan-Boltzmann constant, W/m^2/K^4
ALBEDO = 0.306                # Earth's Bond albedo (NASA Earth fact sheet)
GREENHOUSE_K = 33.0           # today's greenhouse warming: 288 K mean minus 255 K equilibrium


def sunlight(r_au: float, mirror_share: float = 0.0) -> float:
    """Sunlight reaching Earth (W/m^2 across its disc) at r AU, plus what mirrors add as a share of the direct
    sunlight at 1 AU."""
    return SOLAR_CONSTANT / r_au ** 2 + mirror_share * SOLAR_CONSTANT


def equilibrium_temperature(flux: float, albedo: float = ALBEDO) -> float:
    """Temperature (K) at which Earth radiates what it absorbs: T = [S (1 - A) / (4 sigma)]^(1/4)."""
    return (flux * (1 - albedo) / (4 * SIGMA)) ** 0.25


def mean_temperature(flux: float, albedo: float = ALBEDO) -> float:
    """Global mean surface temperature (K): equilibrium plus today's greenhouse warming."""
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
