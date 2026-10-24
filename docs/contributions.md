# Who built what

The guide: "Careers offers are based on individual contribution, so keep a short log of who built what. Every
member should be able to explain the code and the physics."

Each member writes their own lines, as they go: the date, what you built or decided, the pull request. Keep it
honest and short. The git history and the pull requests are the record behind every line.

## Ashish (Member 1: physics core; reviews and merges)

*To be written by Ashish.* The git history before 24 October evening is his: every commit up to `b101f2f`, merged
in [#18](https://github.com/Ashish000011/black-ant/pull/18) and [#19](https://github.com/Ashish000011/black-ant/pull/19).

## Member 2 (safety and environment)

*To be written by Member 2.*

## Member 3 (structures and enablers)

*To be written by Member 3.*

## Member 4 (3D test bench)

*To be written by Member 4.*

## Member 5 (validation and pitch)

| Date | What I built or decided | Pull request |
| --- | --- | --- |
| 24 Oct 2026 | The technical report as a PDF for submission: `sim/report_pdf.py` prints `docs/report.md` to `docs/report.pdf` (7 pages, under the guide's 8), equations as MathML, and stamps the PDF with the report it was made from | branch `m5/report-pitch-submission` |
| 24 Oct 2026 | Checked every number in the report against `results/`: `tests/test_report.py`, 86 checks of the text plus the benchmark table and the chaos copies, and 74 more for the Q&A sheet, the pitch and the voiceover. It found and I fixed: the day-length change (2.5 × 10^-7 s, not 2), Greenhill's buckling length (1,444 km), two benchmark values that are round-off and differ by machine, the journey's run time (an hour and a half), and the report saying the chaos copies agree when one throws Ceres out | branch `m5/report-pitch-submission` |
| 24 Oct 2026 | Q&A sheet rebuilt to 22 questions, each with a one-line answer, more if asked, and who answers; numbers checked against `results/` | branch `m5/report-pitch-submission` |
| 24 Oct 2026 | The pitch's talk track (`docs/pitch.md`): the guide's five parts in 7 minutes, our back-of-envelope estimate (about 8,000 years against the run's 8,758), the found-and-fixed slide, who presents each part, and a test that each part fits its time | branch `m5/report-pitch-submission` |
| 24 Oct 2026 | Demo video voiceover: `sim/voiceover.py` checks each line fits its shot (one did not, so I shortened it), writes timed captions, and adds a recorded voice in one command | branch `m5/report-pitch-submission` |
| 24 Oct 2026 | Submission checklist (`docs/submission.md`): what to upload, the checks first, and the proof | branch `m5/report-pitch-submission` |
