"""The ten official benchmarks (participant guide, section 6). Inputs live in sim/benchmarks.py; judges can
change them with: uv run python -m sim.benchmarks 4 --set e=0.5"""

import pytest

from sim.benchmarks import ALL


@pytest.mark.parametrize("number", sorted(ALL))
def test_official_benchmark(number):
    r = ALL[number]()
    print(f"Benchmark {number}, {r['name']}: measured {r['measured']}, expected {r['expected']} ({r['tolerance']})")
    assert r["ok"], r
