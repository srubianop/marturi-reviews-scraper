# Tasks: Stabilize Review Export Workflow

## Phase 1: Foundation

- [x] 1.1 Add ignored `exports/` workspace rules in `.gitignore` and create the `exports/raw/` + `exports/manual/` directories as the documented landing zones.
- [x] 1.2 Confirm the shared Judge.me field contract stays identical across `.agent/skills/ml-reviews-scraper/assets/scraper.py` and the new consolidator script.

## Phase 2: Export Stabilization

- [x] 2.1 Update `.agent/skills/ml-reviews-scraper/assets/scraper.py` so the default run writes a timestamped CSV under `exports/raw/`, while explicit `-o/--output` still overrides that default.
- [x] 2.2 Normalize `picture_urls` in `.agent/skills/ml-reviews-scraper/assets/scraper.py` and `scripts/scrape_urls.py` to comma-separated values capped at 5 URLs.
- [x] 2.3 Keep `scraper.py` aligned with the new export wording/behavior so the public CLI entrypoint matches the implementation.

## Phase 3: Consolidation

- [x] 3.1 Create `scripts/consolidate_reviews.py` to merge selected raw files, or the default `exports/raw/*.csv` set, plus `exports/manual/*.csv` into root `reviews_judgeme.csv`.
- [x] 3.2 Add clear validation/warning behavior for malformed manual supplement CSVs and preserve Judge.me column order in the final bundle.

## Phase 4: Documentation and Verification

- [x] 4.1 Update `README.md` with the new raw/manual export workflow, consolidation command, and manual supplement CSV contract.
- [x] 4.2 Manual check: run the scraper twice and verify two distinct files appear in `exports/raw/` without overwriting.
- [x] 4.3 Manual check: consolidate one raw CSV and one manual CSV, then verify `reviews_judgeme.csv` and comma-delimited `picture_urls`.
- [x] 4.4 Syntax check: run `python -m py_compile scraper.py .agent/skills/ml-reviews-scraper/assets/scraper.py scripts/scrape_urls.py scripts/consolidate_reviews.py`.
