"""Builds the technical report as a PDF from docs/report.md, as we submit it: A4, 10.5 pt, the references in two
columns at 8 pt. Chrome or Edge (Edge comes with Windows) prints the page; the guide allows 8 pages.

    uv run --with markdown==3.7 --with pypdf==5.1.0 python scripts/report_pdf.py
"""

import pathlib
import sys
import tempfile

import markdown
from pypdf import PdfReader

from browser import print_pdf

ROOT = pathlib.Path(__file__).resolve().parent.parent
SOURCE = ROOT / "docs" / "report.md"
OUT = ROOT / "docs" / "black-ant-report.pdf"
PAGE_LIMIT = 8
CSS = """@page{size:A4;margin:18mm 16mm}body{font:10.5pt/1.38 'Segoe UI',Arial,sans-serif;color:#111}
h1{font-size:17pt;margin:0 0 6pt}h2{font-size:12.5pt;margin:12pt 0 4pt}p,li{margin:3pt 0}
table{border-collapse:collapse;font-size:8.5pt;margin:5pt 0}td,th{border:1px solid #bbb;padding:2px 4px}
img{max-width:100%;max-height:80mm;display:block;margin:5pt auto}code{font-size:9pt}
h2:last-of-type + ol{font-size:8pt;line-height:1.25;columns:2;column-gap:7mm;padding-left:16pt}h2:last-of-type + ol li{margin:0 0 1pt}"""


def main() -> None:
    html = markdown.markdown(SOURCE.read_text(encoding="utf-8"), extensions=["tables"])
    # Written next to report.md, so its img/ links resolve, and removed afterwards.
    with tempfile.NamedTemporaryFile("w", suffix=".html", dir=SOURCE.parent, delete=False, encoding="utf-8") as fh:
        fh.write(f"<!doctype html><meta charset=utf-8><title>Black Ant: Towing Earth to 2.7 AU</title><style>{CSS}</style>{html}")
        page = pathlib.Path(fh.name)
    try:
        print_pdf(page, OUT)
    finally:
        page.unlink(missing_ok=True)
    pages = len(PdfReader(str(OUT)).pages)
    print(f"Wrote {OUT.relative_to(ROOT)}: {pages} pages (limit {PAGE_LIMIT})")
    if pages > PAGE_LIMIT:
        sys.exit(f"The report is over the {PAGE_LIMIT}-page limit: trim docs/report.md.")


if __name__ == "__main__":
    main()
