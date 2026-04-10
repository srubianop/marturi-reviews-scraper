# Apply Progress: Stabilize Review Export Workflow

## Completed

- [x] 1.1 Ignored `exports/` workspace rules added to `.gitignore`; `exports/raw/` and `exports/manual/` directories created locally.
- [x] 1.2 Judge.me field contract kept identical between the scraper asset and the consolidator.
- [x] 2.1 Default scraper runs now write timestamped raw CSVs under `exports/raw/`; `-o/--output` still overrides.
- [x] 2.2 `picture_urls` normalized to comma-separated values capped at 5 URLs in both scraper paths.
- [x] 2.3 `scraper.py` docstring updated to match the new raw-export workflow, and the fallback scraper now writes timestamped raw exports too.
- [x] 3.1 Added `scripts/consolidate_reviews.py` to merge raw exports and manual supplements into `reviews_judgeme.csv`.
- [x] 3.2 Consolidator validates Judge.me headers, warns on malformed manual files, and preserves column order.
- [x] 4.1 README updated with raw/manual workspace guidance, consolidation command, and manual CSV contract.
- [x] 4.2 Manual validation target: two default scraper runs create distinct raw filenames without overwriting.
- [x] 4.3 Manual validation target: consolidation preserves comma-delimited `picture_urls` in the final bundle.
- [x] 4.4 Syntax validation target: `py_compile` for scraper, asset, fallback script, and consolidator.

## Notes

- Raw and manual export folders are ignored by git; only code/docs/config changed.
- Manual supplement CSVs are treated as additive inputs and skipped with warnings if the Judge.me header does not match exactly.
- Lightweight validation used temp fixture CSVs plus CLI help checks to confirm raw-path generation, consolidation, and `picture_urls` normalization without running a full scrape.
