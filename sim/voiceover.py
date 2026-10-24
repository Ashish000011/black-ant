"""The demo video's voiceover: does each line fit its shot, the captions, and adding the recorded voice.

    uv run python -m sim.voiceover                    # each shot's pace, and writes media/black-ant-demo.srt
    uv run python -m sim.voiceover --voice take1.wav  # adds a recorded voiceover (and the captions) to the video

The shots and their lines are the table in docs/video-script.md. Record the lines in one take, starting at 0:00,
at the times in the table; the video stream is copied unchanged, so only the sound and captions are added.
"""

import argparse
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from .config import ROOT

SCRIPT = ROOT / "docs" / "video-script.md"
VIDEO = ROOT / "media" / "black-ant-demo.mp4"
CAPTIONS = VIDEO.with_suffix(".srt")
MAX_SECONDS = 180          # the guide: at most 3 minutes
WORDS_PER_MINUTE = 160     # brisk but clear narration; above this the line will not fit its shot
CAPTION_CHARS = 42         # per caption line, two lines at most

UNITS = {"km": 1, "au": 2, "k": 1, "w": 1, "kg": 1, "s": 1, "%": 1, "°": 1, "×": 1, "x": 1}


def _number_words(n: int) -> int:
    """How many words it takes to say a whole number: 637100 -> six hundred thirty-seven thousand one hundred (6)."""
    if n == 0:
        return 1
    words, scale = 0, 0
    while n:
        n, group = divmod(n, 1000)
        if group:
            words += (2 if group >= 100 else 0) + (1 if group % 100 else 0) + (1 if scale else 0)
        scale += 1
    return words


def spoken_words(text: str) -> int:
    """Words as they are said aloud, numbers and units read out: '637,100 km' is 7 words, '2.7006 AU' 7."""
    text = re.sub(r"[`*_|]", " ", text)
    count = 0
    for token in re.split(r"[\s/]+|(?<=[a-z])-(?=[a-z0-9])|(?<=[0-9])-(?=[a-z])", text.lower()):
        token = token.strip(".,;:!?()\"'")
        if not token:
            continue
        if m := re.fullmatch(r"10\^(-?)(\d+)", token):  # ten to the (minus) sixteen
            count += 3 + bool(m.group(1)) + _number_words(int(m.group(2)))
        elif m := re.fullmatch(r"(\d[\d,]*)(?:\.(\d+))?(%|°|k|w)?", token):
            whole, decimals = int(m.group(1).replace(",", "")), m.group(2) or ""
            count += _number_words(whole) + (1 + len(decimals) if decimals else 0) + bool(m.group(3))
        elif m := re.fullmatch(r"(\d+):(\d+)", token):  # Jupiter's 2:1 resonance
            count += 3
        else:
            count += UNITS.get(token, 1)
    return count


def _clock(t: str) -> float:
    minutes, seconds = t.split(":")
    return 60 * int(minutes) + float(seconds)


def shots(script: Path = SCRIPT, video_seconds: float | None = None) -> list[dict]:
    """The script's table: each shot's start, end (the next shot's start, or the video's end), what is shown and
    the voiceover."""
    rows = re.findall(r"^\| (\d+:\d\d) \| ([^|]+) \| ([^|]+) \|$", script.read_text(encoding="utf-8"), flags=re.M)
    end = video_seconds or _clock(re.search(r"\((\d+) minutes? (\d+) seconds", script.read_text(encoding="utf-8"))
                                  .expand(r"\1:\2"))
    out = []
    for i, (start, shot, line) in enumerate(rows):
        stop = _clock(rows[i + 1][0]) if i + 1 < len(rows) else end
        words = spoken_words(line)
        out.append({"start": _clock(start), "end": stop, "shot": shot.strip(), "voiceover": line.strip(),
                    "spoken_words": words, "words_per_minute": 60 * words / (stop - _clock(start))})
    return out


def video_seconds(video: Path = VIDEO) -> float | None:
    if not shutil.which("ffprobe"):
        return None
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(video)],
                         check=True, capture_output=True, text=True)
    return float(out.stdout)


def _pieces(sentence: str) -> list[str]:
    """A sentence cut at word boundaries into captions of at most two lines."""
    pieces, words = [], sentence.split()
    while words:
        piece = []
        while words and len(" ".join(piece + words[:1])) <= 2 * CAPTION_CHARS:
            piece.append(words.pop(0))
        pieces.append(" ".join(piece or [words.pop(0)]))
    return pieces


def _wrap(piece: str) -> str:
    if len(piece) <= CAPTION_CHARS:
        return piece
    words = piece.split()
    best = min(range(1, len(words)), key=lambda i: abs(len(" ".join(words[:i])) - len(" ".join(words[i:]))))
    return " ".join(words[:best]) + "\n" + " ".join(words[best:])


def _stamp(t: float) -> str:
    ms = round(t * 1000)
    return f"{ms // 3_600_000:02d}:{ms // 60_000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def captions(all_shots: list[dict]) -> str:
    """SubRip captions of the voiceover: each shot's time shared among its pieces by how long each takes to say."""
    cues = []
    for s in all_shots:
        pieces = [p for sentence in re.split(r"(?<=[.!?])\s+", s["voiceover"]) for p in _pieces(sentence)]
        weights = [spoken_words(p) for p in pieces]
        t = s["start"]
        for piece, w in zip(pieces, weights):
            end = t + (s["end"] - s["start"]) * w / sum(weights)
            cues.append(f"{len(cues) + 1}\n{_stamp(t)} --> {_stamp(end)}\n{_wrap(piece)}\n")
            t = end
    return "\n".join(cues)


def add_voice(voice: Path, video: Path = VIDEO, subtitles: Path = CAPTIONS, out: Path | None = None) -> Path:
    """The video with the recorded voice as its sound and the captions as a subtitle track. The video stream is
    copied as it is; the sound is padded with silence, or cut, to the video's length."""
    out = out or video
    with tempfile.TemporaryDirectory() as tmp:
        made = Path(tmp) / video.name
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(video), "-i", str(voice), "-i", str(subtitles),
                        "-map", "0:v", "-map", "1:a", "-map", "2:s", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k",
                        "-af", "apad", "-shortest", "-c:s", "mov_text", "-metadata:s:s:0", "language=eng",
                        "-movflags", "+faststart", str(made)], check=True)
        shutil.move(made, out)
    return out


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--voice", type=Path, help="a recorded voiceover (wav, m4a, mp3...) to add to the video")
    p.add_argument("--out", type=Path, help="where to write the video with the voice (default: replace it)")
    a = p.parse_args()
    all_shots = shots(video_seconds=video_seconds())
    for s in all_shots:
        verdict = "fits" if s["words_per_minute"] <= WORDS_PER_MINUTE else "TOO LONG"
        print(f"{s['start']:5.0f}-{s['end']:3.0f} s  {s['spoken_words']:3d} words  "
              f"{s['words_per_minute']:3.0f}/min  {verdict:8}  {s['shot']}")
    CAPTIONS.write_text(captions(all_shots), encoding="utf-8")
    print(f"Captions: {CAPTIONS.relative_to(ROOT)}")
    if a.voice:
        print(f"Video with the voiceover: {add_voice(a.voice, out=a.out)}")


if __name__ == "__main__":
    main()
