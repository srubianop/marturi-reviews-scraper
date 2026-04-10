# Repository Layout Specification

## Purpose

Define a cleaner repository layout that separates versioned assets, workflow docs, helper scripts, and generated artifacts without changing scraper behavior or the root CLI entrypoint.

## Requirements

### Requirement: Root cleanup

The repository MUST keep the root limited to stable entrypoints and top-level working directories. Loose versioned assets, helper scripts, workflow docs, and debug captures MUST NOT remain in the root after the reorganization.

#### Scenario: Stable root after move
- GIVEN the reorganization is applied
- WHEN a contributor lists the repository root
- THEN `scraper.py`, `README.md`, and intentional top-level folders MAY remain
- AND moved assets, helper scripts, and workflow docs are found only in their designated directories

### Requirement: Script folder subdivision

The system MUST keep workflow CLIs directly under `scripts/` and MUST place investigative/search helpers under `scripts/search/`. Moving helpers deeper SHALL preserve their ability to resolve the repository root correctly.

#### Scenario: Workflow and search scripts are separated
- GIVEN the reorganization is complete
- WHEN a contributor inspects `scripts/`
- THEN workflow commands such as `scrape_urls.py` and `consolidate_reviews.py` remain directly under `scripts/`
- AND helper/search utilities are located under `scripts/search/`

#### Scenario: Moved helper still resolves repo paths
- GIVEN `investigate.py` or `check_excel.py` runs from `scripts/search/`
- WHEN the script reads repository files
- THEN it resolves the same repo root as before
- AND it does not fail because of the deeper path

### Requirement: Versioned assets under data

Versioned non-generated assets MUST live under `data/`. At minimum, `productos.json`, `reviews_registry.json`, and `reviews_judgeme_template.csv` SHALL be referenced from `data/` instead of the root.

#### Scenario: Scripts use moved versioned assets
- GIVEN the assets have been relocated under `data/`
- WHEN `scripts/scrape_urls.py` or `scripts/consolidate_reviews.py` needs those files
- THEN the script reads the `data/` paths successfully
- AND no root-level fallback is required for normal execution

### Requirement: Legacy CSV preservation

Previously kept reference CSV files MUST be preserved under `data/legacy/` instead of being deleted during cleanup. This SHALL NOT redefine the canonical workflow output location for `reviews_judgeme.csv` unless a separate change does so.

#### Scenario: Historical CSVs are retained
- GIVEN a CSV is kept only for reference or backward lookup
- WHEN the repository is reorganized
- THEN that file is moved to `data/legacy/`
- AND existing downstream expectations for the active consolidated output remain unchanged

### Requirement: Generated artifact handling

Generated exports, debug files, screenshots, and temporary bundles MUST remain outside versioned asset locations and MUST stay ignored by default. The repository SHOULD route them to ignored folders such as `exports/`, `exports/debug/`, or `tmp_reviews/` instead of the root.

#### Scenario: Generated files stay out of versioned locations
- GIVEN a scraper or helper produces runtime artifacts
- WHEN the artifact is written
- THEN it lands in an ignored export or temp location
- AND it is not treated as a tracked versioned asset under `data/`

### Requirement: Path compatibility in scripts and docs

All maintained scripts and repository documentation MUST be updated to the new layout in the same change. Path rewrites SHALL preserve current CLI workflows and MUST NOT require changing the public `python scraper.py ...` entrypoint.

#### Scenario: Documentation matches executable paths
- GIVEN the layout change is merged
- WHEN a user follows the README or workflow docs
- THEN every referenced asset, script, and folder path exists
- AND the documented commands still execute with the same scraper behavior

#### Scenario: No scraper workflow regression
- GIVEN the repo layout has changed
- WHEN a user runs the normal scrape and consolidation flow
- THEN the scraper behavior and output format remain the same as before
- AND only internal file locations and documentation references differ
