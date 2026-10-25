"""Prints an HTML page to PDF with Chrome or Edge (Edge comes with Windows), for the report and the verification PDF."""

import os
import pathlib
import shutil
import subprocess
import sys


def browser() -> str:
    """Chrome, Chromium or Edge: on the PATH, or where Windows installs them."""
    for name in ("chrome", "google-chrome", "chromium", "chromium-browser", "msedge", "microsoft-edge"):
        if found := shutil.which(name):
            return found
    for base in (os.environ.get("PROGRAMFILES"), os.environ.get("PROGRAMFILES(X86)"), os.environ.get("LOCALAPPDATA")):
        for rel in (r"Google\Chrome\Application\chrome.exe", r"Microsoft\Edge\Application\msedge.exe"):
            if base and (pathlib.Path(base) / rel).is_file():
                return str(pathlib.Path(base) / rel)
    sys.exit("Chrome or Edge is needed to print the PDF.")


def print_pdf(page: pathlib.Path, pdf: pathlib.Path) -> None:
    subprocess.run([browser(), "--headless=new", "--disable-gpu", "--no-pdf-header-footer", f"--print-to-pdf={pdf}",
                    page.resolve().as_uri()], check=True, capture_output=True, timeout=180)
