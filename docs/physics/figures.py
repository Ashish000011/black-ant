"""Figures for the physics paper and deck, drawn from results/ and config.yaml only.

Run from the project root: uv run --with matplotlib python docs/physics/figures.py
Writes docs/physics/fig/*.svg (paper), fig/*.png (deck) and fig/derived.json (the by-hand estimates the text
quotes, computed here from config.yaml so they never drift from it).
"""

import json
import math
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Circle, FancyArrowPatch, Rectangle  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from sim import habitability as hab  # noqa: E402
from sim.config import load_config  # noqa: E402
from sim.constants import AU, C_LIGHT, G, GM_SUN, YEAR  # noqa: E402

OUT = Path(__file__).resolve().parent / "fig"
RES = ROOT / "results"

# Categorical slots in fixed order (dataviz reference palette); limits and guides in neutral ink.
EARTH, MARS, BEAM, REAL, JUP, VIOLET = "#2a78d6", "#eb6834", "#eda100", "#52514e", "#1baf7a", "#6250d6"
INK, MUTED, GRID = "#0b0b0b", "#6f6e69", "#e4e3df"
COL, FULL = 3.4, 7.05   # single and double column widths (inches) for an A4 two-column page

plt.rcParams.update({
    "font.family": "serif", "font.serif": ["cmr10"], "mathtext.fontset": "cm", "axes.formatter.use_mathtext": True,
    "font.size": 7.5, "axes.titlesize": 7.5, "axes.labelsize": 7.5, "legend.fontsize": 6.6,
    "xtick.labelsize": 6.8, "ytick.labelsize": 6.8, "axes.linewidth": 0.5, "axes.edgecolor": MUTED,
    "xtick.color": MUTED, "ytick.color": MUTED, "axes.labelcolor": INK, "text.color": INK,
    "xtick.major.width": 0.5, "ytick.major.width": 0.5, "xtick.minor.width": 0.4, "ytick.minor.width": 0.4,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.4, "axes.axisbelow": True,
    "axes.spines.top": False, "axes.spines.right": False, "legend.frameon": False, "lines.linewidth": 1.1,
    "svg.fonttype": "path", "savefig.bbox": "tight", "savefig.pad_inches": 0.02,
})


def sci(x, digits=2):
    """3.95e+17 -> $3.95\\times10^{17}$"""
    m, e = f"{x:.{digits}e}".split("e")
    return f"${m}\\times10^{{{int(e)}}}$"


def load(name):
    return json.loads((RES / name).read_text())


def save(fig, name, png=True):
    fig.savefig(OUT / f"{name}.svg")
    if png:
        fig.savefig(OUT / f"{name}.png", dpi=220)
    plt.close(fig)


def tag(ax, letter):
    ax.text(0.0, 1.03, f"({letter})", transform=ax.transAxes, fontsize=7.5, va="bottom", ha="left")


def limit_line(ax, y, text, where=0.02, horizontal=True, va="bottom", color=MUTED):
    if horizontal:
        ax.axhline(y, color=color, lw=0.7, ls=(0, (4, 2)))
        ax.text(where, y, " " + text, transform=ax.get_yaxis_transform(), color=color, fontsize=6.2, va=va)
    else:
        ax.axvline(y, color=color, lw=0.7, ls=(0, (4, 2)))
        ax.text(y, where, " " + text, transform=ax.get_xaxis_transform(), color=color, fontsize=6.2, rotation=90,
                va="bottom", ha="right")


# ---------------------------------------------------------------- derived numbers (by hand, from config.yaml)

def derived(cfg, summary):
    earth = next(p for p in cfg["planets"] if p["name"] == "earth")
    tow = next(t for t in cfg["tows"] if t["name"] == "earth-tow")
    m_e, m_a, d = earth["mass_kg"], tow["asteroid_mass_kg"], tow["distance_km"] * 1e3
    pull = G * m_e * m_a / d ** 2
    acc = G * m_a / d ** 2
    f_t = acc * math.cos(math.radians(45))
    mu = GM_SUN + G * m_e
    a0, a1 = 1.0 * AU, tow["stop_au"] * AU
    t_gauss = math.sqrt(mu) / f_t * (a0 ** -0.5 - a1 ** -0.5) / YEAR
    energy = GM_SUN * m_e / 2 * (1 / a0 - 1 / a1)
    v0, v1 = math.sqrt(mu / a0), math.sqrt(mu / a1)
    p_min = pull * C_LIGHT / 2                    # a perfect head-on bounce, 2P/c
    p_45 = pull * C_LIGHT / math.sqrt(2)          # the 45 degree bounce, sqrt(2) P/c
    gradient_days = math.sqrt(d ** 3 / (2 * G * m_e)) / 86400
    st = cfg["structures"]["earth-tow"]
    e2 = cfg["enablers"]
    mirror_k = (e2["e2_absorbed_fraction"] * e2["e1_beam_limit_w"]
                / (2 * e2["e2_emissivity"] * 5.670374419e-8 * math.pi * (st["mirror_radius_km"] * 1e3) ** 2)) ** 0.25
    cable_sf = e2["e2_strength_pa"] * st["cable_cross_section_km2"] * 1e6 / (2 * e2["e1_beam_limit_w"] / C_LIGHT)
    years = summary["tows"]["earth-tow"]["arrival"]["year"]
    beam_energy = 8.4e25 * years * YEAR
    sun_l = 3.828e26                               # nominal solar luminosity, IAU 2015 Resolution B3
    return {
        "pull_n": pull, "accel_m_s2": acc, "along_orbit_n": pull * math.cos(math.radians(45)),
        "gauss_years": t_gauss, "energy_j": energy, "dv_km_s": (v0 - v1) / 1e3, "v0_km_s": v0 / 1e3, "v1_km_s": v1 / 1e3,
        "p_min_w": p_min, "p_45deg_w": p_45, "gradient_days": gradient_days,
        "mirror_k_at_cap": mirror_k, "cable_sf_at_cap": cable_sf,
        "mean_gain_w": summary["ledger"]["bodies_energy_gain_j"] / (years * YEAR),
        "light_energy_j": beam_energy, "work_over_light": summary["ledger"]["beam_work_j"] / beam_energy,
        "e1_over_sun": e2["e1_beam_limit_w"] / sun_l, "sunlight_at_target": 1 / tow["stop_au"] ** 2,
        "v_over_c": v0 / C_LIGHT,
    }


# ---------------------------------------------------------------- Fig. 1: the tow's geometry (schematic)

def fig_geometry():
    fig, ax = plt.subplots(figsize=(COL, 2.35))
    ax.set_xlim(-2.4, 2.25)
    ax.set_ylim(-1.05, 1.72)
    ax.set_aspect("equal")
    ax.axis("off")
    # Sun far to the left; Earth at the origin moving +y; asteroid at 45 deg between ahead and away from the Sun
    ax.add_patch(Circle((-2.0, 0), 0.3, color=BEAM, alpha=0.9, lw=0))
    ax.text(-2.0, -0.42, "Sun\n(far away)", ha="center", va="top", fontsize=6.4, color=MUTED)
    ax.add_patch(Circle((0, 0), 0.13, color=EARTH, lw=0))
    ax.text(0.0, -0.2, "Earth", ha="center", va="top", fontsize=6.8)
    ax.annotate("", xy=(0, 0.62), xytext=(0, 0.16), arrowprops=dict(arrowstyle="-|>", color=INK, lw=0.8))
    ax.text(-0.05, 0.42, r"$\mathbf{v}$ (orbit)", ha="right", fontsize=6.6)
    s = 0.72
    ax_, ay_ = s, s
    ax.add_patch(Circle((ax_, ay_), 0.085, color=REAL, lw=0))
    ax.text(ax_ + 0.11, ay_ - 0.08, "asteroid\n$3.97\\times10^{20}$ kg", fontsize=6.2, va="top")
    ax.plot([0.11, ax_ - 0.07], [0.11, ay_ - 0.07], color=MUTED, lw=0.5, ls=(0, (2, 2)))
    ax.text(0.6, 0.42, "637,100 km", rotation=45, fontsize=5.8, color=MUTED, ha="center", va="center")
    # 45 degree arc
    th = [math.radians(x) for x in range(0, 46, 3)]
    ax.plot([0.36 * math.cos(t) for t in th], [0.36 * math.sin(t) for t in th], color=MUTED, lw=0.5)
    ax.text(0.39, 0.02, r"$45^\circ$", fontsize=6.4, color=MUTED)
    ax.plot([0.13, 2.2], [0, 0], color=GRID, lw=0.6)
    ax.text(2.2, 0.02, "away from\nthe Sun", fontsize=6.0, color=MUTED, va="bottom", ha="right")
    # mirror beyond the asteroid, normal along (1,1); cables
    mx, my = ax_ + 0.42, ay_ + 0.42
    L = 0.32
    ax.plot([mx - L * 0.707, mx + L * 0.707], [my + L * 0.707, my - L * 0.707], color=INK, lw=2.0, solid_capstyle="butt")
    ax.plot([ax_ + 0.06, mx - 0.05], [ay_ + 0.06, my - 0.05], color=MUTED, lw=0.5)
    ax.text(mx - 0.26, my + 0.24, "E2 mirror", fontsize=6.2, va="bottom", ha="right")
    ax.text(ax_ + 0.12, ay_ + 0.3, "cables", fontsize=5.8, color=MUTED, rotation=45, ha="center", va="center")
    # beam: in along +x (from the Sun's side), out along -y
    ax.annotate("", xy=(mx - 0.02, my), xytext=(-1.6, my),
                arrowprops=dict(arrowstyle="-|>", color=BEAM, lw=1.6))
    ax.text(-1.55, my + 0.05, r"E1 light in, $\hat{\mathbf{n}}_{in}$", fontsize=6.4, color="#8a5d00", va="bottom")
    ax.annotate("", xy=(mx, -0.95), xytext=(mx, my - 0.02),
                arrowprops=dict(arrowstyle="-|>", color=BEAM, lw=1.6))
    ax.text(mx + 0.05, -0.62, "light out,\n" r"$\hat{\mathbf{n}}_{out}$", fontsize=6.4, color="#8a5d00")
    # forces
    ax.add_patch(FancyArrowPatch((0.09, 0.09), (0.36, 0.36), arrowstyle="-|>", mutation_scale=8, color=EARTH, lw=1.3))
    ax.text(-0.02, 0.22, r"$F_g$", fontsize=7, color=EARTH, ha="right")
    ax.add_patch(FancyArrowPatch((ax_ - 0.08, ay_ - 0.08), (ax_ - 0.3, ay_ - 0.3), arrowstyle="-|>", mutation_scale=8,
                                 color=REAL, lw=1.1))
    ax.add_patch(FancyArrowPatch((mx + 0.03, my + 0.03), (mx + 0.3, my + 0.3), arrowstyle="-|>", mutation_scale=8,
                                 color="#8a5d00", lw=1.3))
    ax.text(mx + 0.33, my + 0.33, r"$\frac{P}{c}(\hat{\mathbf{n}}_{in}-\hat{\mathbf{n}}_{out})$", fontsize=6.8,
            color="#8a5d00", va="center", ha="left")
    ax.text(-2.38, 1.7, "Not to scale", fontsize=6.0, color=MUTED, va="top")
    save(fig, "fig1_geometry")


# ---------------------------------------------------------------- Fig. 2: the journey

def fig_journey(run, summary, cfg, dv):
    fr = run["frames"]
    t = [f["t"] for f in fr]
    ae = [f["earth_orbit_au"] for f in fr]
    am = [f["mars_orbit_au"] for f in fr]
    ee = [f["earth_eccentricity"] for f in fr]
    pw = [f.get("beam_power_w", 0.0) for f in fr]
    arr = summary["tows"]["earth-tow"]["arrival"]
    mars_arr = summary["tows"]["mars-tow"]["arrival"]
    # by-hand Gauss spiral under the constant along-orbit pull
    tow = next(x for x in cfg["tows"] if x["name"] == "earth-tow")
    earth = next(p for p in cfg["planets"] if p["name"] == "earth")
    f_t = G * tow["asteroid_mass_kg"] / (tow["distance_km"] * 1e3) ** 2 * math.cos(math.radians(45))
    mu = GM_SUN + G * earth["mass_kg"]
    tg, ag = [], []
    for k in range(0, 8100, 20):
        inv = AU ** -0.5 - f_t * k * YEAR / math.sqrt(mu)
        a = inv ** -2 / AU
        if a > 2.7:
            break
        tg.append(k)
        ag.append(a)
    # sunlight optics needed, face on, for today's sunlight (habitability.py's own formula)
    refl = cfg["habitability"]["mirror_reflectivity"]
    disc = math.pi * 6.371e6 ** 2 / 1e6
    need = [max(0.0, 1 / hab.mean_inverse_r2(a, e) - 1) * disc / refl for a, e in zip(ae, ee)]

    fig, axs = plt.subplots(3, 1, figsize=(COL, 3.55), sharex=True, gridspec_kw={"height_ratios": [1.6, 0.85, 0.85]})
    ax = axs[0]
    ax.axhspan(3.0, 3.5, color=MARS, alpha=0.07, lw=0)
    ax.plot(t, am, color=MARS, label="Mars")
    ax.plot(t, ae, color=EARTH, label="Earth")
    ax.plot(tg, ag, color=INK, lw=0.8, ls=(0, (3, 2)), label="Gauss, by hand")
    for y, s in ((3.278, "Jupiter 2:1"),):
        ax.axhline(y, color=MUTED, lw=0.5, ls=(0, (1, 1.5)))
        ax.text(150, y + 0.03, s, fontsize=6.0, color=MUTED, va="bottom")
    ax.text(150, 3.06, "Mars's sprint (4x pull)", fontsize=6.0, color=MARS, va="bottom")
    ax.plot([arr["year"]], [arr["a_au"]], "o", ms=3.5, color=EARTH, mec="white", mew=0.6)
    ax.annotate(f"arrives, year {arr['year']:,.0f}\n{arr['a_au']} AU", (arr["year"], arr["a_au"]), (6300, 1.2),
                fontsize=6.2, arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.5))
    ax.plot([mars_arr["year"]], [mars_arr["a_au"]], "o", ms=3.5, color=MARS, mec="white", mew=0.6)
    ax.annotate(f"parked, year {mars_arr['year']:,.0f}\n{mars_arr['a_au']} AU", (mars_arr["year"], mars_arr["a_au"]),
                (6150, 3.13), fontsize=6.2, arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.5))
    ax.set_ylabel("orbit size $a$ (AU)")
    ax.set_ylim(0.9, 3.9)
    ax.legend(loc="upper left", bbox_to_anchor=(0.0, 0.66))
    tag(ax, "a")

    ax = axs[1]
    ax.plot(t, [p / 1e25 for p in pw], color=BEAM, lw=0.9)
    limit_line(ax, 10, "E1 bound $10^{26}$ W", va="bottom")
    ax.set_ylabel("beams ($10^{25}$ W)")
    ax.set_ylim(0, 12.5)
    ax.text(0.98, 0.06, f"peak {sci(summary['total_beam_max_w'])} W", transform=ax.transAxes, ha="right",
            fontsize=6.2, color=MUTED)
    tag(ax, "b")

    ax = axs[2]
    ax.plot(t, [n / 1e8 for n in need], color=VIOLET, lw=1.0)
    limit_line(ax, 10, "E3 bound $10^{9}$ km$^2$", va="bottom")
    ax.set_ylabel("optics ($10^{8}$ km$^2$)")
    ax.set_ylim(0, 12.5)
    ax.text(0.98, 0.06, "needed for today's sunlight, face on", transform=ax.transAxes, ha="right", fontsize=6.2,
            color=MUTED)
    ax.set_xlabel("year of the journey")
    ax.set_xlim(0, 9000)
    tag(ax, "c")
    fig.subplots_adjust(hspace=0.28)
    fig.align_ylabels(axs)
    save(fig, "fig2_journey")


# ---------------------------------------------------------------- Fig. 3: top view

def fig_topview(run, summary):
    fr = run["frames"]
    fig, ax = plt.subplots(figsize=(COL, 3.0))
    th = [2 * math.pi * k / 360 for k in range(361)]
    for r, s, c in ((2.7, "target 2.7 AU", EARTH), (3.278, "Jupiter 2:1", MUTED), (3.64, "Mars park", MARS)):
        ax.plot([r * math.cos(x) for x in th], [r * math.sin(x) for x in th], color=c, lw=0.5, ls=(0, (3, 2)))
    n = len(fr)
    for i, f in enumerate(fr):
        a = 0.15 + 0.85 * i / n
        ax.plot(f["pos"]["earth"][0], f["pos"]["earth"][1], ".", ms=1.6, color=EARTH, alpha=a, mew=0, rasterized=True)
        ax.plot(f["pos"]["mars"][0], f["pos"]["mars"][1], ".", ms=1.6, color=MARS, alpha=a, mew=0, rasterized=True)
    ax.plot(0, 0, "o", ms=5, color=BEAM)
    ax.plot([], [], ".", color=EARTH, label="Earth, every 10 years")
    ax.plot([], [], ".", color=MARS, label="Mars, every 10 years")
    ax.legend(loc="upper right", bbox_to_anchor=(1.12, 1.08), handletextpad=0.1)
    ax.set_aspect("equal")
    ax.set_xlim(-4.0, 4.0)
    ax.set_ylim(-4.0, 4.0)
    ax.set_xlabel("$x$ (AU, ecliptic J2000)")
    ax.set_ylabel("$y$ (AU)")
    ax.text(2.7 * 0.707, -2.7 * 0.707 - 0.1, "2.7 AU", color=EARTH, fontsize=6.2, ha="left", va="top")
    ax.text(-3.64 * 0.6, -3.64 * 0.8 - 0.1, "3.64 AU", color=MARS, fontsize=6.2, ha="right", va="top")
    save(fig, "fig3_topview")


# ---------------------------------------------------------------- Fig. 4: conservation

def fig_conservation(run, summary):
    fr = run["frames"]
    t = [f["t"] for f in fr]
    en = [abs(f["energy_error"]) for f in fr]
    mo = [max(abs(f["momentum_error"]), 1e-26) for f in fr]
    lg = summary["ledger"]
    fig, axs = plt.subplots(2, 1, figsize=(COL, 2.3), sharex=True, gridspec_kw={"height_ratios": [1.4, 1]})
    ax = axs[0]
    ax.semilogy(t, mo, color=EARTH, lw=0.8)
    ax.text(300, 3e-21, "bodies' momentum change vs applied impulse", fontsize=6.0, color=EARTH, va="bottom")
    ax.axhline(lg["nothing_from_nothing_max"], color=VIOLET, lw=0.8)
    ax.text(300, lg["nothing_from_nothing_max"] * 2, "impulse + recoil + light + departed: worst "
            f"{lg['nothing_from_nothing_max']:.1e}", fontsize=6.0, color=VIOLET, va="bottom")
    limit_line(ax, 1e-9, "the guide's limit $10^{-9}$", va="bottom", where=0.02)
    ax.set_ylim(1e-25, 1e-6)
    ax.set_ylabel("momentum ledger")
    tag(ax, "a")
    ax = axs[1]
    ax.plot(t, [x * 1e7 for x in en], color=MARS, lw=0.8)
    ax.set_ylabel(r"energy gap ($10^{-7}$)")
    ax.text(0.98, 0.08, f"beam work {sci(lg['beam_work_j'], 4)} J, bodies gained {sci(lg['bodies_energy_gain_j'], 4)} J",
            transform=ax.transAxes, ha="right", fontsize=6.0, color=MUTED)
    ax.set_ylim(0, 8)
    ax.set_xlim(0, 9000)
    ax.set_xlabel("year of the journey")
    tag(ax, "b")
    fig.subplots_adjust(hspace=0.3)
    fig.align_ylabels(axs)
    save(fig, "fig4_conservation")


# ---------------------------------------------------------------- Fig. 5: climate

def fig_climate(mirrors):
    shares = [0.10 + 0.005 * k for k in range(0, 241)]
    warm, t = [], 288.0
    for s in reversed(shares):
        t = hab.mean_temperature(s * hab.SOLAR_CONSTANT, t)
        warm.append(t)
    warm.reverse()
    cold, t = [], 150.0
    for s in shares:
        t = hab.mean_temperature(s * hab.SOLAR_CONSTANT, t)
        cold.append(t)
    fig, axs = plt.subplots(2, 1, figsize=(COL, 2.35), sharex=True, gridspec_kw={"height_ratios": [1.7, 1]})
    ax = axs[0]
    ax.axhspan(263, 308, color=JUP, alpha=0.08, lw=0)
    ax.text(0.12, 300, "safe band 263-308 K", fontsize=6.0, color="#0e7a52")
    ax.plot(shares, warm, color=MARS, label="warm start (today's Earth)")
    ax.plot(shares, cold, color=EARTH, ls=(0, (3, 1.5)), label="frozen start")
    cliff = mirrors["refractor_l1"]["climate_cliff_sunlight"]
    limit_line(ax, cliff, f"cliff {cliff:.1%}", horizontal=False, where=0.03)
    pts = [(1.0, 288.0, "today"), (1 / 2.7 ** 2, hab.mean_temperature(hab.SOLAR_CONSTANT / 2.7 ** 2, 288.0),
                                    "2.7 AU, no optics")]
    for k, v in mirrors["refractor_l1"]["by_transmission"].items():
        pts.append((v["sunlight_vs_today_at_e3"], v["temperature_k"], f"L1 ring, $T$={k}"))
    for x, y, s in pts:
        ax.plot(x, y, "o", ms=3.2, color=INK, mec="white", mew=0.5)
    ax.annotate("today", (1.0, 288), (1.08, 268), fontsize=6.0, arrowprops=dict(arrowstyle="-", lw=0.4, color=MUTED))
    ax.annotate(f"2.7 AU, no optics\n{pts[1][1]:.0f} K", (pts[1][0], pts[1][1]), (0.2, 185), fontsize=6.0,
                arrowprops=dict(arrowstyle="-", lw=0.4, color=MUTED))
    bt = mirrors["refractor_l1"]["by_transmission"]
    ax.annotate(f"L1 ring at E3 bound\n$T$=0.95: {bt['0.95']['temperature_k']:.0f} K, "
                f"0.90: {bt['0.90']['temperature_k']:.0f} K\n0.85: frozen", (bt["0.90"]["sunlight_vs_today_at_e3"], 282),
                (0.27, 232), fontsize=6.0, arrowprops=dict(arrowstyle="-", lw=0.4, color=MUTED))
    ax.set_ylabel("global mean $T$ (K)")
    ax.set_ylim(140, 330)
    ax.legend(loc="lower right")
    tag(ax, "a")
    ax = axs[1]
    ax.plot(shares, [hab.liquid_water_share(x) for x in warm], color=MARS)
    ax.plot(shares, [hab.liquid_water_share(x) for x in cold], color=EARTH, ls=(0, (3, 1.5)))
    limit_line(ax, 0.30, "limit 30%", va="bottom", where=0.02)
    ax.set_ylabel("liquid-water area")
    ax.set_xlabel("yearly sunlight, share of today's")
    ax.set_xlim(0.1, 1.3)
    ax.set_ylim(0, 1)
    tag(ax, "b")
    fig.align_ylabels(axs)
    save(fig, "fig5_climate")


# ---------------------------------------------------------------- Fig. 6: Mars's crossing and parking

def fig_mars(crossing, scans):
    v = crossing["variants"]
    rows = [(1.0, v["normal pull"]), (1.56, v["sprint 1.56x (80,000 km)"]), (3.3, v["sprint 3.3x (55,000 km)"]),
            (4.0, v["chosen: sprint 4x with the asteroid at 400,000 km (to 200,000 km)"]),
            (4.9, v["sprint 4.9x (45,000 km)"])]
    fig, axs = plt.subplots(1, 2, figsize=(FULL, 1.95), gridspec_kw={"width_ratios": [1, 2.1]})
    ax = axs[0]
    labels = ["1x\nnormal", "1.56x", "3.3x", "4x\nchosen", "4.9x"]
    caught = [r[1]["caught"] for r in rows]
    bars = ax.bar(range(5), caught, color=[MARS if c else REAL for c in caught], width=0.62)
    for b, c in zip(bars, caught):
        ax.text(b.get_x() + b.get_width() / 2, c + 0.15, f"{c}/8", ha="center", fontsize=6.4)
    bars[3].set_color(JUP)
    ax.set_xticks(range(5), labels)
    ax.set_ylim(0, 8)
    ax.set_ylabel("trials caught by Jupiter's 2:1")
    ax.set_xlabel("Mars tow's pull across 3.0-3.5 AU")
    ax.grid(axis="x", visible=False)
    tag(ax, "a")

    ax = axs[1]
    marks = {"scan 1: Earth $e$ 0.02, as today": ("o", REAL), "scan 2: Earth on forced $e$": ("s", EARTH),
             "scan 3: forced $e$ and plane (as flown)": ("D", JUP)}
    for (label, (m, c)), scan in zip(marks.items(), scans):
        xs = [r["mars_a"] for r in scan["results"]]
        ys = [r["earth_mars_gap_min_au"] for r in scan["results"]]
        ax.plot(xs, ys, m, ms=3.6, color=c, mec="white", mew=0.5, label=label, ls="none")
        for r in scan["results"]:
            if r["stopped"]:
                ax.annotate("escaped", (r["mars_a"], r["earth_mars_gap_min_au"]),
                            (r["mars_a"] + 0.02, r["earth_mars_gap_min_au"] + 0.35), fontsize=5.8, color=MUTED,
                            arrowprops=dict(arrowstyle="-", lw=0.4, color=MUTED))
    ax.axhline(0, color=INK, lw=0.6)
    ax.text(3.36, -0.07, "below 0 the orbits cross", fontsize=6.0, color=MUTED, va="top")
    ax.text(3.642, -1.2, "chosen: 3.64 AU", rotation=90, fontsize=6.0, color="#0e7a52", ha="center", va="bottom")
    for r, s in ((3.278, "J 2:1"), (3.379, "E 7:5"), (3.474, "J 11:6"), (3.516, "J 9:5"), (3.538, "E 3:2"),
                 (3.583, "J 7:4"), (3.694, "E 8:5"), (3.701, "J 5:3")):
        ax.axvline(r, color=GRID, lw=0.8)
        ax.text(r, 0.73, s, rotation=90, fontsize=5.4, color=MUTED, ha="left" if s == "J 5:3" else "right", va="top")
    ax.axvspan(3.62, 3.66, color=JUP, alpha=0.12, lw=0)
    ax.set_xlim(2.98, 3.72)
    ax.set_ylim(-1.9, 0.75)
    ax.set_xlabel("Mars parked at (AU), Earth at 2.7 AU")
    ax.set_ylabel("closest orbit gap in 1 Myr (AU)")
    ax.legend(loc="lower center", ncol=1, bbox_to_anchor=(0.47, 0.0))
    tag(ax, "b")
    fig.subplots_adjust(wspace=0.32)
    save(fig, "fig6_mars")


# ---------------------------------------------------------------- Fig. 7: beam outages

def fig_outage(outage):
    pick = {"shared E1 budget, all beams off": (EARTH, "o", "every station off"),
            "shared E1 budget, half the stations off": (MARS, "s", "half off"),
            "shared E1 budget, a quarter off": (JUP, "D", "a quarter off"),
            "old: own cap 8.5e25 W, all beams off": (REAL, "v", "first design (own cap), all off"),
            "Mars tow, all beams off": (VIOLET, "^", "Mars tow, all off")}
    fig, ax = plt.subplots(figsize=(COL, 2.05))
    for case in outage:
        if case["name"] not in pick:
            continue
        c, m, label = pick[case["name"]]
        tr = sorted(case["trials"], key=lambda x: x["days"])
        xs = [max(x["days"], 0.05) * 24 for x in tr]
        start = tr[0]["closest_km"]
        ys = [x["closest_km"] / start for x in tr]
        ax.semilogx(xs, ys, marker=m, ms=2.8, color=c, lw=0.9, mec="white", mew=0.4,
                    label=f"{label}: safe to {case['longest_safe_outage_days'] * 24:,.0f} h")
    ax.axhline(0.5, color=MUTED, lw=0.6, ls=(0, (4, 2)))
    ax.text(1.25, 0.47, "below: asteroid\nlost, falls\ntoward Earth", fontsize=5.8, color=MUTED, va="top")
    ax.set_xlabel("outage length (hours)")
    ax.set_ylabel("closest distance / design distance")
    ax.set_ylim(0, 1.08)
    h, l = ax.get_legend_handles_labels()
    ax.legend(h, l, loc="upper center", bbox_to_anchor=(0.45, -0.24), ncol=2,
              fontsize=5.9, columnspacing=0.8, handlelength=1.6)
    save(fig, "fig7_outage")


# ---------------------------------------------------------------- Fig. 8: Octo-Earth arms

def fig_octo(octo):
    keep = {"Structural steel S355": (REAL, "o"), "CFRP, unidirectional (axial)": (MARS, "s"),
            "Carbon nanotube, ideal macroscale (hypothetical)": (EARTH, "D"),
            "Graphene, ideal macroscale (hypothetical)": (VIOLET, "^")}
    short = {"Structural steel S355": "steel S355", "CFRP, unidirectional (axial)": "CFRP",
             "Carbon nanotube, ideal macroscale (hypothetical)": "nanotube, ideal",
             "Graphene, ideal macroscale (hypothetical)": "graphene, ideal"}
    fig, ax = plt.subplots(figsize=(COL, 2.05))
    for mat in octo["materials"]:
        if mat["name"] not in keep:
            continue
        c, m = keep[mat["name"]]
        xs = [mat["curled_longest_km"]] + [x["length_km"] for x in mat["lengths"]]
        ys = [1.5] + [x["curled_sf"] for x in mat["lengths"]]
        order = sorted(range(len(xs)), key=lambda i: xs[i])
        ax.loglog([xs[i] for i in order], [ys[i] for i in order], marker=m, ms=2.8, color=c, lw=0.9,
                  label=f"{short[mat['name']]} (holds to {mat['curled_longest_km']:,.0f} km)", mec="white", mew=0.4)
    limit_line(ax, 1.5, "required 1.5", va="bottom", where=0.02)
    ax.axvline(octo["arm"]["length_km"], color=INK, lw=0.6)
    ax.text(octo["arm"]["length_km"] * 0.92, 2e-4, "demo arm\n12,000 km", fontsize=6.0, ha="right", va="bottom")
    ax.set_xlabel("arm length, curled as the demo draws it (km)")
    ax.set_ylabel("safety factor at the root")
    ax.set_xlim(2, 2e4)
    ax.set_ylim(1e-4, 200)
    ax.legend(loc="lower left", fontsize=5.9)
    save(fig, "fig8_octo")


# ---------------------------------------------------------------- Fig. 9: a million years after arrival

def fig_longterm(lt):
    mv, rl = lt["moved"]["series"], lt["baseline"]["series"]
    ym = [y / 1e3 for y in mv["year"]]
    yr = [y / 1e3 for y in rl["year"]]

    def frac(a):
        mean = sum(a) / len(a)
        return [(x - mean) / mean * 1e3 for x in a]

    fig, axs = plt.subplots(1, 4, figsize=(FULL, 1.6))
    ax = axs[0]
    ax.plot(ym, frac(mv["orbits"]["earth"]["a"]), color=EARTH, lw=0.5, label="moved solar system (Earth at 2.7 AU)")
    ax.plot(yr, frac(rl["orbits"]["earth"]["a"]), color=REAL, lw=0.7, label="real solar system (Earth at 1 AU)")
    ax.set_ylabel(r"Earth $\Delta a/a$ ($10^{-3}$)")
    fig.legend(*ax.get_legend_handles_labels(), loc="upper center", ncol=2, bbox_to_anchor=(0.5, 1.1))
    ax.set_ylim(-0.8, 1.2)
    tag(ax, "a")
    ax = axs[1]
    ax.plot(yr, rl["orbits"]["earth"]["e"], color=REAL, lw=0.5)
    ax.plot(ym, mv["orbits"]["earth"]["e"], color=EARTH, lw=0.5)
    ax.set_ylabel("Earth eccentricity")
    tag(ax, "b")
    ax = axs[2]
    ax.plot(yr, rl["axial_tilt_deg"], color=REAL, lw=0.6)
    ax.plot(ym, mv["axial_tilt_deg"], color=EARTH, lw=0.6)
    ax.set_ylabel("axial tilt (deg)")
    tag(ax, "c")
    ax = axs[3]
    ax.plot(ym, mv["earth_mars_gap_au"], color=EARTH, lw=0.5)
    ax.plot(yr, rl["earth_mars_gap_au"], color=REAL, lw=0.7)
    ax.set_ylabel("Earth-Mars orbit gap (AU)")
    ax.set_ylim(0, 0.9)
    tag(ax, "d")
    for ax in axs:
        ax.set_xlabel("kyr after arrival")
        ax.set_xlim(0, 1000)
    fig.subplots_adjust(wspace=0.5)
    save(fig, "fig9_longterm")


# ---------------------------------------------------------------- Fig. 10: Earth's eccentricity and the arrival trim

def fig_eccentricity(run, summary, cfg):
    fr = run["frames"]
    t = [f["t"] for f in fr]
    e = [f["earth_eccentricity"] for f in fr]
    trim_au = cfg["arrival_trim"]["from_au"]
    t_trim = next(f["t"] for f in fr if f["earth_orbit_au"] >= trim_au)
    arr = summary["tows"]["earth-tow"]["arrival"]
    fig, ax = plt.subplots(figsize=(COL, 1.4))
    ax.axvspan(t_trim, arr["year"], color=JUP, alpha=0.1, lw=0)
    ax.text(t_trim + 60, 0.052, f"arrival trim\n(from {trim_au} AU)", fontsize=6.0, color="#0e7a52", va="top")
    ax.plot(t, e, color=EARTH, lw=0.8)
    ax.plot([arr["year"]], [arr["eccentricity"]], "o", ms=3.2, color=EARTH, mec="white", mew=0.5)
    ax.annotate(f"arrives: $e$ = {arr['eccentricity']}, free part {arr['free_eccentricity']}",
                (arr["year"], arr["eccentricity"]), (2300, 0.036), fontsize=6.0,
                arrowprops=dict(arrowstyle="-", lw=0.4, color=MUTED))
    ax.set_xlim(0, 9000)
    ax.set_ylim(0, 0.056)
    ax.set_xlabel("year of the journey")
    ax.set_ylabel("Earth eccentricity")
    save(fig, "fig10_eccentricity")


# ---------------------------------------------------------------- Fig. 11: impacts at 2.7 AU by size

def fig_impacts(small, summary):
    sizes = [("20m", "20 m"), ("100m", "100 m"), ("1000m", "1 km")]
    fig, ax = plt.subplots(figsize=(COL, 1.45))
    for k, (place, c, m, dy) in enumerate((("crossing", MARS, "s", 0.14), ("parked", EARTH, "o", -0.14))):
        for j, (key, label) in enumerate(sizes):
            y = j + dy
            yp = small["impacts"][place][key]["years_per_impact"]
            ax.plot([yp["high"], yp["low"]], [y, y], color=c, lw=1.0)
            ax.plot([yp["central"]], [y], m, ms=3.6, color=c, mec="white", mew=0.5,
                    label=("crossing the belt" if place == "crossing" else "parked at 2.7 AU") if j == 0 else None)
    ax.plot([500000], [2], "D", ms=3.6, color=REAL, mec="white", mew=0.5, label="Earth today (1 km)")
    ax.set_xscale("log")
    ax.set_yticks(range(3), [s[1] for s in sizes])
    ax.set_xlim(0.01, 2e6)
    ax.set_ylim(-0.5, 2.5)
    ax.set_xlabel("years between impacts (central, with low-high range)")
    ax.grid(axis="y", visible=False)
    ax.legend(loc="lower right", fontsize=5.9)
    save(fig, "fig11_impacts")


# ---------------------------------------------------------------- data for the deck (build_deck.mjs reads it)

def deck_data(cfg, summary, run, dv):
    fr = run["frames"]
    every = [min(fr, key=lambda f: abs(f["t"] - y)) for y in range(0, int(fr[-1]["t"]) + 1, 100)]
    lt = load("longterm.json")
    mv, rl = lt["moved"]["series"], lt["baseline"]["series"]
    step = max(1, len(mv["year"]) // 100)
    octo = load("octo_earth.json")
    keep = ["Structural steel S355", "CFRP, unidirectional (axial)", "Carbon nanotube, ideal macroscale (hypothetical)",
            "Graphene, ideal macroscale (hypothetical)"]
    mats = {m["name"]: m for m in octo["materials"]}
    bodies = {b["name"]: b["mass_kg"] for b in cfg["small_bodies"]}
    tows = {t["name"]: t for t in cfg["tows"]}
    outage = {o["name"]: o for o in load("outage.json")}
    crossing = load("crossing.json")["variants"]
    mirrors = load("mirrors.json")
    small = load("small_asteroids.json")
    return {
        "derived": dv,
        "summary": {k: summary[k] for k in ("tows", "total_beam_max_w", "mars_closest", "big_asteroids_closest_au",
                                            "big_asteroid_nudges", "climate", "ledger", "flags", "end", "belt")},
        "enablers": cfg["enablers"],
        "journey": {"year": [round(f["t"]) for f in every], "earth_au": [f["earth_orbit_au"] for f in every],
                    "mars_au": [f["mars_orbit_au"] for f in every],
                    "beam_w": [f.get("beam_power_w", 0.0) for f in every]},
        "octo": {"net_force_n": octo["net_force_all_arms"]["on_arms_n"][2],
                 "net_share": octo["net_force_all_arms"]["sum_over_force"], "arm_km": octo["arm"]["length_km"],
                 "materials": [{"name": n, "strength_gpa": mats[n]["strength_pa"] / 1e9,
                                "curled_km": mats[n]["curled_longest_km"], "buckle_km": mats[n]["buckling_length_km"]}
                               for n in keep]},
        "masses_1e20": {"Hygiea": bodies["hygiea"] / 1e20, "Pallas": bodies["pallas"] / 1e20,
                        "Mars tow": tows["mars-tow"]["asteroid_mass_kg"] / 1e20, "Vesta": bodies["vesta"] / 1e20,
                        "Earth tow": tows["earth-tow"]["asteroid_mass_kg"] / 1e20,
                        "E3 bound": cfg["enablers"]["e3_asteroid_limit_kg"] / 1e20, "Ceres": bodies["ceres"] / 1e20},
        "crossing": [{"label": k, "caught": v["caught"], "of": v["of"]} for k, v in crossing.items() if "caught" in v],
        "outage_hours": {k: v["longest_safe_outage_days"] * 24 for k, v in outage.items()},
        "longterm": {"kyr": [y / 1e3 for y in mv["year"][::step]], "tilt_moved": mv["axial_tilt_deg"][::step],
                     "tilt_real": rl["axial_tilt_deg"][::step], "verdict": lt["verdict"],
                     "earth_mars_gap_min_au": lt["moved"]["earth_mars_orbit_gap_min_au"]},
        "optics": {"l1": mirrors["refractor_l1"], "simple_ring": mirrors["simple_ring"],
                   "light_ring_area_km2": mirrors["light_ring"]["area_km2"], "tow_mirror": mirrors["tow_mirror"]},
        "small": {"parked": small["impacts"]["parked"], "crossing": small["impacts"]["crossing"],
                  "e1_20m": small["survey_and_e1"]["20m"]["worst"]},
    }


def main():
    OUT.mkdir(exist_ok=True)
    cfg = load_config()
    summary = load("summary.json")
    run = load("run.json")
    mirrors = load("mirrors.json")
    dv = derived(cfg, summary)
    (OUT / "derived.json").write_text(json.dumps(dv, indent=1))
    (OUT / "deck_data.json").write_text(json.dumps(deck_data(cfg, summary, run, dv)))
    fig_geometry()
    fig_journey(run, summary, cfg, dv)
    fig_conservation(run, summary)
    fig_climate(mirrors)
    fig_mars(load("crossing.json"), [load(f"parking_scan{k}.json") for k in (1, 2, 3)])
    fig_outage(load("outage.json"))
    fig_octo(load("octo_earth.json"))
    fig_longterm(load("longterm.json"))
    fig_eccentricity(run, summary, cfg)
    fig_impacts(load("small_asteroids.json"), summary)
    for k, v in dv.items():
        print(f"{k:22s} {v:.4g}")


if __name__ == "__main__":
    main()
