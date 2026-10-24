"""The Moon stays with Earth at the start, middle and end of the journey (short runs; the full
50-year runs are `uv run python -m sim.scenarios.moon`)."""

from sim.scenarios.moon import compare


def test_moon_stays_at_every_epoch():
    out = compare(years=5)
    for name, r in out["epochs"].items():
        print(f"Moon {name}: distance change {r['distance_change']:.4%}")
        assert not r["with_asteroid"]["escaped"], name
        assert r["ok"], name


def test_much_heavier_asteroid_would_disturb_the_moon():
    """Sanity check that the test can fail: a 300 times heavier asteroid wrecks the Moon's orbit."""
    r = compare(years=5, asteroid_scale=300, which=("start",))["epochs"]["start"]
    print(f"Moon at x300: escaped {r['with_asteroid']['escaped']}, change {r['distance_change']:.1%}")
    assert r["with_asteroid"]["escaped"] or r["distance_change"] > 0.10
