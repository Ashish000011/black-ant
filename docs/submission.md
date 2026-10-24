# Submitting: what goes in, the checks first, and the proof

The deliverables of the guide (section 9), due before the deadline on 26 October 2026. Submit from `main` once
the last pull request is merged, so every link shows the final version.

## What we submit

| Deliverable | What to upload or link | Ready? |
| --- | --- | --- |
| Source code, README with setup, run, test | [github.com/Ashish000011/black-ant](https://github.com/Ashish000011/black-ant) (public) | Yes |
| Runnable simulation | The same repository, and the 3D test bench: [ashish000011.github.io/black-ant](https://ashish000011.github.io/black-ant/) | Yes |
| Technical report, at most 8 pages | [docs/report.pdf](report.pdf): 7 pages, A4, made from [report.md](report.md) | Yes |
| Conservation and momentum record | [docs/momentum-record.md](momentum-record.md) | Yes |
| Demo video, at most 3 minutes | [media/black-ant-demo.mp4](../media/black-ant-demo.mp4), 2 min 20 s; captions in [media/black-ant-demo.srt](../media/black-ant-demo.srt) | After the voiceover |
| Pitch deck, 7 minutes | The shared deck, exported to PDF; the talk track is [pitch.md](pitch.md) | After three timed rehearsals |

The Q&A sheet ([qa.md](qa.md)) is for us, not for upload.

## The voiceover

1. Read each line of [video-script.md](video-script.md) at the time in its table, in one take from 0:00, with the
   video playing muted beside you. Every line fits its shot at about 160 words a minute (a test checks this).
2. Save the take as a WAV or M4A file, then add it to the video. The picture is copied unchanged; the sound and the
   captions are added, and the video keeps its length:

```bash
uv run python -m sim.voiceover --voice take1.wav
```

3. Watch it through once, then commit `media/black-ant-demo.mp4` on a branch and open a pull request.

## The checks before submitting

```bash
uv run pytest -m "not slow"             # quick tests, including every number in the report against results/
uv run python -m sim.benchmarks         # the ten official benchmarks
uv run python -m sim.report_pdf         # rebuild docs/report.pdf if the report changed; prints its page count
uv run python -m sim.voiceover          # each voiceover line fits its shot; rewrites the captions
ffprobe -v error -show_entries format=duration:stream=codec_type -of compact media/black-ant-demo.mp4
```

The last line must show a duration under 180 seconds and an `audio` stream. Then open each link in the table
above in a private window, to be sure it works without our logins.

## The proof

1. Submit, and take a screenshot of the confirmation page, with the date and time showing.
2. Save it as `docs/img/submission-proof.png`, link it in [status.md](status.md), and open a pull request that
   closes issue #11.
