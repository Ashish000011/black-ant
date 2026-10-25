# Physics paper and physics deck

Two companion documents for the judges, built from `results/` and `config.yaml` only. Rebuild them after any
new run.

| File | What it is |
| --- | --- |
| `black-ant-physics-paper.pdf` | The physics paper: 7 A4 pages, two columns, 10 figures, 6 tables, 9 equations, 50 references. Every model, enabler and what-if run. It is a companion to `docs/report.md`, the submitted technical report, not a replacement |
| `black-ant-physics-deck.pptx` | The physics deck: 11 slides for a 7 to 8 minute talk and 5 hidden backup slides. Slide 2 is a clickable map, every slide has a Map button, and the enabler and what-if cards open the backups (E1, E2, E3, stress tests, a million years). Speaker notes on every slide |
| `figures.py` | Draws `fig/*.svg` and `fig/*.png` and writes `fig/derived.json` (the by-hand estimates) and `fig/deck_data.json` (every number the deck shows) |
| `paper.html`, `paper.css`, `build_paper.mjs` | The paper's text and layout; the build numbers figures, tables, equations and references, typesets the maths with KaTeX and prints with headless Chromium |
| `build_deck.mjs` | The deck, with pptxgenjs: native charts, clickable tiles and hidden backups |

Rebuild (from this folder; needs uv, Node 18+ and Playwright's headless Chromium, `npx playwright-core install chromium-headless-shell` if missing):

```bash
npm ci
npm run figures
npm run paper
npm run deck
```
