# Where we are (24 October, mid-point)

**All six winning conditions hold in our simulation.** Earth reaches 2.7006 AU in year 8,758 (limit 10,000) with
0 unresolved flags; all ten Earth-safety thresholds hold; the lowest structural safety factor is 1.57; all ten
official benchmarks pass; the momentum ledger closes to 5.6 × 10^-16 (limit 10^-9). The full write-up is
[report.md](report.md).

## Deliverables (guide section 9)

| Deliverable | Status | Where |
| --- | --- | --- |
| Source code with README: setup, run, test | Done | this repository; [README](../README.md) |
| Runnable simulation | Done | the Python model; the 3D test bench in `viewer/` ([ashish000011.github.io/black-ant](https://ashish000011.github.io/black-ant/) once on `main`) |
| Technical report, at most 8 pages | Done | [report.pdf](report.pdf) (6 to 7 pages, depending on the fonts of the machine that builds it), made from [report.md](report.md); every number checked against `results/` by `tests/test_report.py` |
| Conservation and momentum record | Done | [momentum-record.md](momentum-record.md) |
| Demo video, at most 3 minutes | Done, needs the voiceover recorded | [media/black-ant-demo.mp4](../media/black-ant-demo.mp4) (2 min 20 s); script in [video-script.md](video-script.md), every line fits its shot; captions in [media/black-ant-demo.srt](../media/black-ant-demo.srt); how to add the voice: [submission.md](submission.md) |
| Pitch deck, 7 minutes | Drafted (13 slides, timed notes); needs three timed rehearsals | shared deck (ask Ashish for the link); talk track in [pitch.md](pitch.md); 22 questions, with who answers each, in [qa.md](qa.md) |
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
| #9 Rules from the guide, questions for the organisers | Done: [rules.md](rules.md) |
| #10 Official benchmarks and extra checks | Done: all pass, also with changed inputs |
| #11 Pitch deck, demo video, Q&A, submission | Deck, video, Q&A, talk track and submission checklist done; left: record the voiceover, rehearse three times, submit ([submission.md](submission.md)) |
| #12 Octo-Earth scenario (now test X8) | Done |
| #13 Re-run with the organisers' rules | Waiting: the guide's rules are in; the rulebook's safety appendix is still not published |
| #14 Mid-point check-in: baseline and enablers | Ready to present |
| #15 Technical report | Done: [report.pdf](report.pdf), under 8 pages; every number matches `results/` |
| #16 Conservation and momentum record | Done |
| #17 Contribution log | Started: [contributions.md](contributions.md) has Member 5's lines; each member adds their own |

## Still to do before the final

1. **Half-step convergence check** of the final design (the guide: "halve the time step and show the answer does
   not change"). Running; up to year 8,556 the half-step run reaches each orbit size within 3 to 10 years of the
   1-day run (29 years at 2.5 AU, within the logs' sampling).
2. **Deck rehearsal** (three, with a timer: [pitch.md](pitch.md)) and the **voiceover** on the video
   ([submission.md](submission.md)). The report PDF is done.
3. **Contribution log** (#17): careers offers go by individual contribution, so each member adds what they did to
   [contributions.md](contributions.md).
4. **Ask the organisers** the questions in [rules.md](rules.md): the rulebook's safety thresholds, moving Mars,
   asteroid defence within E1.

## How to look at it

```bash
uv sync
uv run python -m sim.benchmarks      # the ten official benchmarks, about 12 seconds
cd viewer && npm ci && npm run dev   # the 3D test bench on your machine
```
