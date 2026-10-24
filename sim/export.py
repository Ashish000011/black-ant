"""Writes a run's results: out/summary.json, out/run.json (the file the 3D viewer reads) and
out/end_state.json (exact final positions and velocities, for the long-term stability run)."""

import json
from pathlib import Path

from .config import ROOT


def write_outputs(summary: dict, frames: list[dict], out_dir: Path | str | None = None,
                  end_state: dict | None = None) -> Path:
    out = Path(out_dir) if out_dir else ROOT / "out"
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    run = {"meta": {"scenario": "tow", "frame_every_years": summary["settings"]["frame_every_years"],
                    "distance_unit": "AU", "mars_tow": summary["settings"]["mars_tow"]},
           "frames": frames}
    (out / "run.json").write_text(json.dumps(run), encoding="utf-8")
    if end_state is not None:
        (out / "end_state.json").write_text(json.dumps(end_state), encoding="utf-8")
    viewer = ROOT / "viewer" / "public"
    if viewer.is_dir():  # once Member 4's viewer exists, keep its copy current
        (viewer / "run.json").write_text(json.dumps(run), encoding="utf-8")
    return out
