# Tasks: Reorganize Repo Layout

## Phase 1: Layout Prep

- [x] 1.1 Create `data/`, `data/legacy/`, and `scripts/search/`; move tracked assets into their final homes without moving root `reviews_judgeme.csv`.
- [x] 1.2 Update `.gitignore` so `exports/` stays ignored, root `*.csv`/`*.json` remain ignored, and `data/productos.json`, `data/reviews_registry.json`, `data/reviews_judgeme_template.csv`, and `data/legacy/*.csv` stay tracked.

## Phase 2: Path Rewrites and Moves

- [x] 2.1 Move `scripts/investigate.py` and `scripts/check_excel.py` into `scripts/search/`, then change their repo-root math to `parents[2]`; point `investigate.py` at `data/productos.json`.
- [x] 2.2 Update `scripts/scrape_urls.py` to read/write `data/productos.json` and `data/reviews_registry.json` instead of root-relative filenames.
- [x] 2.3 Update `scripts/consolidate_reviews.py` defaults and help text to source template/input CSVs from `data/` while still writing the canonical bundle to root `reviews_judgeme.csv`.

## Phase 3: Docs and References

- [x] 3.1 Update `README.md` path examples and layout notes for `data/`, `scripts/search/`, and the unchanged root output file.
- [x] 3.2 Fix any remaining in-repo references to the moved files/paths so docs and comments match the new layout.

## Phase 4: Verification

- [x] 4.1 Run `python -m py_compile scraper.py scripts/scrape_urls.py scripts/consolidate_reviews.py scripts/search/investigate.py scripts/search/check_excel.py`.
- [x] 4.2 Run `python scripts/search/investigate.py --help` and `python scripts/search/check_excel.py --help`, then confirm the moved assets resolve from repo root.
