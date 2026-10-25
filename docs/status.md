# Where we are (24 October, mid-point)

**All six winning conditions hold in our simulation.** Earth reaches 2.7006 AU in year 8,758 (limit 10,000) with
0 unresolved flags; all ten Earth-safety thresholds hold; the lowest structural safety factor is 1.57; all ten
official benchmarks pass; the momentum ledger closes to 5.6 × 10^-16 (limit 10^-9). The full write-up is
[report.md](report.md). The half-step check agrees: halving the time step moves Earth's arrival by 28 years in 8,758
(0.3%), with the same orbit and 0 unresolved flags.

## Deliverables (guide section 9)

| Deliverable | Status | Where |
| --- | --- | --- |
| Source code with README: setup, run, test | Done | this repository; [README](../README.md) |
| Runnable simulation | Done | the Python model; the 3D test bench in `viewer/` ([ashish000011.github.io/black-ant](https://ashish000011.github.io/black-ant/)) |
| Technical report, at most 8 pages | Drafted | [report.md](report.md); export to PDF for submission |
| Conservation and momentum record | Done | [momentum-record.md](momentum-record.md) |
| Demo video, at most 3 minutes | Done | [media/black-ant-demo.mp4](../media/black-ant-demo.mp4) (2 min 20 s, the Blender-style test bench, captions on screen) |
| Pitch deck, 7 minutes | Drafted (13 slides, timed notes) | shared deck (ask Ashish for the link); answers for questions in [qa.md](qa.md) |
| Mid-point review, 5 minutes | Ready | shared deck (ask Ashish); enablers declared in [enablers.md](enablers.md) |

## The issues

| Issue | Status |
| --- | --- |
| #1 Safety report and charts | Done: report "Earth safety"; test bench "Earth safety" tab |
| #2 Explain the three hazards | Done: report "Hazards and stability"; [qa.md](qa.md) |
| #3 Safety values per frame for the viewer | Done: `sim/viewer_data.py` |
| #4 Enabler specs | Done: [enablers.md](enablers.md) |
| #5 Structures report | Done: report "Structures"; test bench "Structure" tab |
| #6 Octo-Earth audit: arm stress and slide | Done: `sim/scenarios/octo.py`; slide in both decks |
| #7 3D viewer playing the run | Done: `viewer/` |
| #8 Safety panel, Octo-Earth tab, deploy, demo clips | Done: tabs, Octo-Earth view, Pages workflow, demo video |
| #9 Rules from the guide | Done: [rules.md](rules.md) |
| #10 Official benchmarks and extra checks | Done: all pass, also with changed inputs |
| #11 Pitch deck, demo video, Q&A, submission | Deck, video and Q&A done; submission left |
| #12 Octo-Earth scenario (now test X8) | Done |
| #13 Re-run with the organisers' rules | Waiting: the guide's rules are in; the rulebook's safety appendix is still not published |
| #14 Mid-point check-in: baseline and enablers | Ready to present |
| #15 Technical report | Drafted: [report.md](report.md) |
| #16 Conservation and momentum record | Done |
| #17 Contribution log | Written by name and by the work each did: [contributions.md](contributions.md); each member checks their section |

## Still to do before the final

1. **Report to PDF** and deck rehearsal.
2. **Contribution log** (#17): careers offers go by individual contribution, so each member checks their section
   of [contributions.md](contributions.md) and adds anything missing.
3. **The demo video's Octo-Earth shot re-rendered** with the new reference view (#27: curled jointed arms, as the
   company's demo draws them).

## How to look at it

```bash
uv sync
uv run python -m sim.benchmarks      # the ten official benchmarks, about 12 seconds
cd viewer && npm ci && npm run dev   # the 3D test bench on your machine
```
