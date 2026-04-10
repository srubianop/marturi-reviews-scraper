# Proposal: reorganize-repo-layout

## Intent

The current repository root is cluttered with static assets, generated files, and documentation. Scripts have inconsistent locations and hardcoded path resolutions. This change reorganizes the repository structure into dedicated directories (`data/`, `docs/workflow/`, `scripts/search/`) and updates related paths to improve maintainability and hygiene, while keeping the core scraper behavior unchanged.

## Scope

### In Scope
- Move static and configuration assets (`reviews_judgeme_template.csv`, `productos.json`, `reviews_registry.json`) into `data/`.
- Move workflow and supplementary documentation into `docs/workflow/`.
- Move helper scripts (`investigate.py`, `check_excel.py`) into `scripts/search/`.
- Update internal path resolutions in `scripts/investigate.py`, `scripts/check_excel.py`, `scripts/scrape_urls.py`, and `scripts/consolidate_reviews.py` to match the new layout.
- Update `.gitignore` to ensure `data/` assets remain tracked where appropriate.
- Update `README.md` to reflect the new structure and commands.

### Out of Scope
- Modifying the core scraping logic in `scraper.py` or `.agent/skills/ml-reviews-scraper/assets/scraper.py`.
- Changing the structure or format of the output data itself.
- Refactoring `scraper.py` beyond potential path resolution updates if needed.

## Capabilities

### New Capabilities
None

### Modified Capabilities
None

## Approach

Implement the reorganization in two phases as recommended:
1. **Structural Move**: Create `data/`, `docs/workflow/`, and `scripts/search/`. Move non-runtime helpers, docs, and static versioned assets (`productos.json`, `reviews_registry.json`, `reviews_judgeme_template.csv`) to these new directories. Ensure `scraper.py` and canonical outputs like `reviews_judgeme.csv` remain accessible.
2. **Path Rewrites**: Update `scripts/scrape_urls.py` and the search helpers to correctly resolve the new `data/` paths. Update `.gitignore` with specific exceptions for the moved assets to prevent them from being ignored. Revise the `README.md` with the new file paths.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `productos.json`, `reviews_registry.json`, `reviews_judgeme_template.csv` | Moved | Relocated to `data/` |
| `scripts/investigate.py`, `scripts/check_excel.py` | Moved & Modified | Relocated to `scripts/search/`, root path resolution updated |
| `scripts/scrape_urls.py` | Modified | Updated hardcoded paths to point to `data/productos.json` and `data/reviews_registry.json` |
| `scripts/consolidate_reviews.py` | Modified | Output and template path updates as necessary |
| `.gitignore` | Modified | Exceptions added for tracked assets in `data/` |
| `README.md` | Modified | Path examples and layout docs updated |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Untracked moved files | High | Explicitly add `!data/productos.json`, `!data/reviews_registry.json`, and `!data/reviews_judgeme_template.csv` to `.gitignore` |
| Broken script path resolution | Medium | Test script execution (`scrape_urls.py`, `investigate.py`) post-move to verify `Path(__file__).resolve().parents` math is correct |
| Downstream import failures | Low | Maintain `reviews_judgeme.csv` in its expected location or clearly document its new location if moved, ensuring `consolidate_reviews.py` outputs correctly. |

## Rollback Plan

Revert the commit that performs the file moves and path updates. The operation is purely structural and does not affect external systems or databases.

## Dependencies

None

## Success Criteria

- [ ] `data/`, `docs/workflow/`, and `scripts/search/` directories exist with the correct files.
- [ ] Running `python scripts/scrape_urls.py` successfully reads and updates the files in `data/`.
- [ ] Running search scripts from their new locations works without `FileNotFoundError`.
- [ ] `.gitignore` accurately tracks the necessary files in `data/` while ignoring raw outputs.
- [ ] `README.md` reflects the current structure.
