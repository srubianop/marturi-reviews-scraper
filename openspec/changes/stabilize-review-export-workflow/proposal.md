# Proposal: stabilize-review-export-workflow

## Intent

Resolve data loss and inconsistency issues by stabilizing the export workflow. Currently, exports overwrite previous runs, and multiple scripts output different formats (e.g., `;` vs `,` for `picture_urls`). This change standardizes output formats, introduces safe export locations, and supports manual consolidation for multi-product runs without risking data loss.

## Scope

### In Scope
- Modify scraper to save outputs in an ignored, timestamped export directory (`exports/raw/`).
- Standardize `picture_urls` to use comma-separated values (max 5 URLs) across all scripts.
- Provide a clear append/consolidate mechanism for multi-product runs.
- Document a manual-supplement path for screenshot-derived reviews.

### Out of Scope
- Modifying core ML extraction logic or selectors.
- Building a full UI or database backend for reviews.
- Automating the screenshot-to-review process beyond documentation.

## Capabilities

### New Capabilities
- `review-export-management`: Controls how reviews are saved, timestamped, and consolidated into the final Judge.me format.

### Modified Capabilities
- None

## Approach

1. Update `scraper.py` and `.agent/skills/ml-reviews-scraper/assets/scraper.py` to write raw CSVs to an ignored `exports/raw/` directory with timestamped filenames.
2. Unify the `picture_urls` delimiter to `,` in both the main scraper and `scripts/scrape_urls.py`. Limit picture URLs to a maximum of 5.
3. Add an explicit consolidate script (or `--append` flag) that merges raw exports and manual supplements from `exports/manual/` into a final `reviews_judgeme.csv`.
4. Update `README.md` to reflect the new directory structure, output locations, and the consolidation step.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `.agent/skills/ml-reviews-scraper/assets/scraper.py` | Modified | Updates file output logic and standardizes `picture_urls`. |
| `scripts/scrape_urls.py` | Modified | Aligns `picture_urls` delimiter with the main scraper. |
| `scraper.py` | Modified | Updates CLI to support new output paths or append modes. |
| `README.md` | Modified | Documents the new export and manual supplement workflow. |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Breaks downstream manual processes expecting a root `reviews_judgeme.csv` | High | The consolidation step will still output to the root directory, preserving compatibility. |
| Ad-hoc scripts break due to new `picture_urls` delimiter | Medium | Clear documentation and unified standards will minimize confusion. |

## Rollback Plan

Revert the changes to `scraper.py`, `.agent/skills/ml-reviews-scraper/assets/scraper.py`, and `scripts/scrape_urls.py` via `git revert`.

## Dependencies

- None (Standard Python libraries only).

## Success Criteria

- [ ] Each scraper run generates a new, timestamped file in `exports/raw/` without overwriting prior runs.
- [ ] A consolidation step successfully merges multiple raw files into `reviews_judgeme.csv`.
- [ ] `picture_urls` consistently use `,` as a delimiter with a max of 5 URLs across all outputs.