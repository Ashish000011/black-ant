"""The ten official benchmarks (participant guide, section 6). Inputs live in sim/benchmarks.py; judges can
change them with: uv run python -m sim.benchmarks 4 --set e=0.5"""

import pytest

from sim.benchmarks import ALL


@pytest.mark.parametrize("number", sorted(ALL))
def test_official_benchmark(number):
    r = ALL[number]()
    print(f"Benchmark {number}, {r['name']}: measured {r['measured']}, expected {r['expected']} ({r['tolerance']})")
    assert r["ok"], r


@pytest.mark.parametrize("number, inputs", [
    (1, {"current": 3.5, "field": (0.2, -0.4, 0.1)}),
    (2, {"radius": 7.0, "sides": 300}),
    (3, {"current": 250.0, "distance": 4.0}),
    (4, {"e": 0.7, "periods": 3}),
    (4, {"e": 0.9, "periods": 2}),
    (4, {"a_au": 5.2, "e": 0.05}),
    (8, {"push": 3e-8}),
    (9, {"length": 25.0, "density": 2700.0}),
    (10, {"albedo": 0.3}),
])
def test_official_benchmark_with_changed_inputs(number, inputs):
    """Judges may change a benchmark's inputs during judging: each must still pass."""
    r = ALL[number](**inputs)
    print(f"Benchmark {number} with {inputs}: measured {r['measured']}, expected {r['expected']}")
    assert r["ok"], r
