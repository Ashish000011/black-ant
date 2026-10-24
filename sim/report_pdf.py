"""The technical report as a PDF for submission: docs/report.md -> docs/report.pdf (A4, at most 8 pages).

    uv run python -m sim.report_pdf                  # writes docs/report.pdf with a headless Chromium browser
    uv run python -m sim.report_pdf --html out.html  # also keeps the HTML it printed

The equations (```latex blocks) become MathML, which the browser draws itself, so nothing is fetched from the
web. The PDF carries the SHA-256 of the report it was made from; tests/test_report.py checks it against
docs/report.md, so a PDF older than the report fails the tests.
"""

import argparse
import base64
import hashlib
import html
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import markdown
from latex2mathml.converter import convert as latex_to_mathml
from pypdf import PdfReader, PdfWriter

from .config import ROOT

REPORT = ROOT / "docs" / "report.md"
PDF = ROOT / "docs" / "report.pdf"
MAX_PAGES = 8
MINUS, NBSP = "\u2212", "\u00a0"  # minus sign, no-break space
BROWSERS = ("chromium", "chromium-browser", "google-chrome", "google-chrome-stable", "brave-browser", "microsoft-edge",
            "chrome", "msedge")
# Windows keeps its browsers off PATH, in the usual install folders.
WINDOWS_BROWSERS = ("Google/Chrome/Application/chrome.exe", "Microsoft/Edge/Application/msedge.exe",
                    "BraveSoftware/Brave-Browser/Application/brave.exe")

CSS = """
@page { size: A4; margin: 14mm 15mm 15mm 15mm;
        @bottom-center { content: "Black Ant · technical report · page " counter(page) " of " counter(pages);
                         font: 7.5pt "DejaVu Sans", sans-serif; color: #666; } }
html { font: 9.2pt/1.36 "DejaVu Serif", Georgia, serif; color: #111; }
body { margin: 0; }
h1 { font: bold 17pt/1.2 "DejaVu Sans", sans-serif; margin: 0 0 2pt; }
h1 + p { margin-top: 0; color: #444; }
h2 { font: bold 11.5pt/1.25 "DejaVu Sans", sans-serif; margin: 10pt 0 3pt; border-bottom: 0.6pt solid #999;
     break-after: avoid; }
p, ul { margin: 0 0 4.5pt; }
ul { padding-left: 14pt; }
li { margin-bottom: 2pt; }
table { border-collapse: collapse; width: 100%; margin: 3pt 0 6pt; font: 7.9pt/1.3 "DejaVu Sans", sans-serif;
        break-inside: avoid; }
th, td { border: 0.5pt solid #aaa; padding: 1.6pt 3.5pt; text-align: left; vertical-align: top; }
th { background: #eee; }
img { display: block; max-width: 100%; max-height: 66mm; margin: 4pt auto 2pt; }
p:has(> img) { text-align: center; font: italic 7.9pt "DejaVu Sans", sans-serif; color: #444;
               break-inside: avoid; margin-bottom: 6pt; }
math[display="block"] { display: block math; margin: 4pt 0; font-size: 10.5pt; }
math [mathvariant="bold"] { font-weight: bold; font-style: normal; }  /* vectors: Chromium ignores mathvariant */
pre { font: 7.6pt/1.35 "DejaVu Sans Mono", monospace; background: #f4f4f4; padding: 4pt 6pt; margin: 3pt 0 6pt;
      white-space: pre-wrap; break-inside: avoid; }
code { font-family: "DejaVu Sans Mono", monospace; font-size: 0.9em; }
sup { font-size: 0.7em; line-height: 0; }
a { color: inherit; text-decoration: none; }
"""


def report_hash(path: Path = REPORT) -> str:
    """SHA-256 of the report, with line endings as git stores them, so a Windows checkout matches too."""
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def to_html(text: str) -> str:
    """The report's Markdown as one HTML page: equations as MathML, 10^20 and a^(1/3) as superscripts, and the
    caption of each figure (its alt text) printed under it."""
    maths = []

    def keep_math(m):
        maths.append(latex_to_mathml(m.group(1).strip(), display="block"))
        return f"\n\nMATHBLOCK{len(maths) - 1}\n\n"

    text = re.sub(r"```latex\n(.*?)\n```", keep_math, text, flags=re.S)
    code = []

    def keep_code(m):
        code.append(m.group(0))
        return f"\n\nCODEBLOCK{len(code) - 1}\n\n"

    text = re.sub(r"```.*?```", keep_code, text, flags=re.S)  # no superscripts inside commands
    text = re.sub(r"\^\(([^)]+)\)", r"<sup>\1</sup>", text)
    # A true minus sign and no-break spaces, so a line never breaks inside 5.6 × 10^-16.
    text = re.sub(r"\^(-?[0-9.]*[0-9])", lambda m: "<sup>" + m.group(1).replace("-", MINUS) + "</sup>", text)
    text = text.replace(" × 10<sup>", f"{NBSP}×{NBSP}10<sup>")
    for i, block in enumerate(code):
        text = text.replace(f"CODEBLOCK{i}", block)
    body = markdown.markdown(text, extensions=["tables", "fenced_code"])
    for i, block in enumerate(maths):
        body = body.replace(f"<p>MATHBLOCK{i}</p>", block)
    body = re.sub(r'(<img alt="([^"]*)"[^>]*>)', lambda m: f"{m.group(1)}<br>{m.group(2)}", body)
    title = html.escape(text.splitlines()[0].lstrip("# ").strip())
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>{title}</title>'
            f"<style>{CSS}</style></head><body>{body}</body></html>")


def find_browser() -> str:
    for name in BROWSERS:
        if path := shutil.which(name):
            return path
    for root in filter(None, (os.environ.get(v) for v in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA"))):
        for rel in WINDOWS_BROWSERS:
            if (path := Path(root) / rel).exists():
                return str(path)
    raise SystemExit("No Chromium-based browser found; pass one with --browser")


class DevTools:
    """The browser's DevTools protocol over --remote-debugging-pipe (fd 3 in, fd 4 out): some Chromium builds,
    Brave among them, ignore --print-to-pdf in headless mode, but all of them answer Page.printToPDF."""

    def __init__(self, browser: str, profile: str):
        import fcntl  # POSIX only: on Windows print_pdf uses --print-to-pdf instead
        to_browser, self._in = os.pipe()
        self._out, from_browser = os.pipe()
        # Lift the browser's ends above 4, so placing them on fds 3 and 4 never overwrites one with the other.
        lifted = [fcntl.fcntl(fd, fcntl.F_DUPFD_CLOEXEC, 10) for fd in (to_browser, from_browser)]
        os.close(to_browser)
        os.close(from_browser)
        to_browser, from_browser = lifted

        def wire():  # runs in the child: the protocol's two fds
            os.dup2(to_browser, 3)
            os.dup2(from_browser, 4)

        self.proc = subprocess.Popen(
            [browser, "--headless=new", "--remote-debugging-pipe", "--disable-gpu", "--no-first-run",
             "--no-default-browser-check", "--password-store=basic", "--disable-extensions",
             f"--user-data-dir={profile}", "about:blank"],
            preexec_fn=wire, close_fds=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        os.close(to_browser)
        os.close(from_browser)
        self._buffer, self._next = b"", 0

    def _read(self, timeout: float) -> dict:
        import select
        while b"\0" not in self._buffer:
            if not select.select([self._out], [], [], timeout)[0]:
                raise TimeoutError("the browser did not answer")
            chunk = os.read(self._out, 1 << 20)
            if not chunk:
                raise RuntimeError("the browser closed the pipe")
            self._buffer += chunk
        message, self._buffer = self._buffer.split(b"\0", 1)
        return json.loads(message)

    def call(self, method: str, session: str | None = None, timeout: float = 60, **params) -> dict:
        self._next += 1
        message = {"id": self._next, "method": method, "params": params} | ({"sessionId": session} if session else {})
        os.write(self._in, json.dumps(message).encode() + b"\0")
        while True:
            reply = self._read(timeout)
            if reply.get("id") == self._next:
                if "error" in reply:
                    raise RuntimeError(f"{method}: {reply['error']}")
                return reply["result"]

    def wait_for(self, event: str, timeout: float = 60) -> None:
        while self._read(timeout).get("method") != event:
            pass

    def close(self) -> None:
        try:
            self.call("Browser.close", timeout=10)
        except (OSError, RuntimeError, TimeoutError):
            pass
        self.proc.wait(timeout=20)
        os.close(self._in)
        os.close(self._out)


def print_pdf(page: Path, pdf: Path, browser: str) -> None:
    if os.name == "nt":  # Windows has no fds 3 and 4 for the DevTools pipe; Chrome and Edge honour --print-to-pdf
        with tempfile.TemporaryDirectory() as profile:
            subprocess.run([browser, "--headless=new", "--disable-gpu", "--no-first-run", "--no-pdf-header-footer",
                            f"--user-data-dir={profile}", f"--print-to-pdf={pdf}", page.as_uri()],
                           check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=180)
        if not pdf.exists():
            raise SystemExit(f"{browser} wrote no PDF")
        return
    with tempfile.TemporaryDirectory() as profile:
        tools = DevTools(browser, profile)
        try:
            target = tools.call("Target.createTarget", url="about:blank")["targetId"]
            session = tools.call("Target.attachToTarget", targetId=target, flatten=True)["sessionId"]
            tools.call("Page.enable", session)
            tools.call("Page.navigate", session, url=page.as_uri())
            tools.wait_for("Page.loadEventFired")
            out = tools.call("Page.printToPDF", session, timeout=120, printBackground=True, preferCSSPageSize=True)
            pdf.write_bytes(base64.b64decode(out["data"]))
        finally:
            tools.close()


def export(report: Path = REPORT, pdf: Path = PDF, browser: str | None = None, keep_html: Path | None = None) -> int:
    page = report.with_name(".report-print.html")  # beside the report, so img/ resolves
    page.write_text(to_html(report.read_text(encoding="utf-8")), encoding="utf-8")
    try:
        printed = pdf.with_suffix(".tmp.pdf")
        print_pdf(page, printed, browser or find_browser())
        if keep_html:
            shutil.copy(page, keep_html)
    finally:
        page.unlink()
    writer = PdfWriter(clone_from=PdfReader(printed))
    writer.add_metadata({"/Title": "Black Ant: Towing Earth to 2.7 AU (technical report)",
                         "/Author": "Team Black Ant", "/Subject": f"docs/report.md sha256 {report_hash(report)}"})
    with pdf.open("wb") as f:
        writer.write(f)
    printed.unlink()
    pages = len(PdfReader(pdf).pages)
    print(f"{pdf.relative_to(ROOT)}: {pages} pages (limit {MAX_PAGES})")
    return pages


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--browser", help="path to a Chromium-based browser (default: the first one found)")
    p.add_argument("--html", type=Path, help="also keep the HTML page that was printed")
    a = p.parse_args()
    if export(browser=a.browser, keep_html=a.html) > MAX_PAGES:
        raise SystemExit(f"Over the guide's {MAX_PAGES} pages: shorten docs/report.md")


if __name__ == "__main__":
    main()
