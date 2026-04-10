# Exploration: reorganize-repo-layout

### Current State
- Root is still doing a lot of work: `scraper.py`, `README.md`, `.gitignore`, plus generated/legacy artifacts like `reviews_judgeme.csv`, `reviews_judgeme_template.csv`, `reviews_registry.json`, `productos.json`, screenshots, and `tmp_reviews/`.
- `scraper.py` is only a thin loader; the real CLI behavior lives in `.agent/skills/ml-reviews-scraper/assets/scraper.py`.
- Workflow CLIs already live under `scripts/` (`consolidate_reviews.py`, `scrape_urls.py`), while the search/debug helpers are still flat in `scripts/`.
- `scripts/investigate.py` and `scripts/check_excel.py` compute repo paths with `Path(__file__).resolve().parents[1]`, so moving them deeper will change their root resolution.
- `scripts/scrape_urls.py` hardcodes root file names for `productos.json` and `reviews_registry.json`.
- `.gitignore` currently ignores all `*.csv` and `*.json`, with only a root-template exception, so relocating tracked assets under `data/` will need explicit unignore rules.

### Affected Areas
- `scraper.py` — must stay as the public CLI entrypoint.
- `scripts/consolidate_reviews.py` — output path and docs may need to stay compatible if `reviews_judgeme.csv` moves.
- `scripts/scrape_urls.py` — root JSON lookups will break if registry/product assets move.
- `scripts/investigate.py`, `scripts/check_excel.py` — repo-root math changes if moved to `scripts/search/`.
- `README.md` — all path examples and layout docs need updates.
- `.gitignore` — needs new exceptions for tracked assets under `data/`.
- Root assets (`reviews_judgeme_template.csv`, `reviews_judgeme.csv`, `productos.json`, `reviews_registry.json`) — candidate move targets.

### Approaches
1. **Safe structural move first** — move docs/helpers/static assets into the new folders, keep `scraper.py` root, and preserve current runtime output behavior.
   - Pros: low behavioral risk; core scraping stays intact.
   - Cons: requires compatibility path updates and `.gitignore` exceptions.
   - Effort: Medium

2. **Full layout switch** — move everything to the target layout, including legacy CSVs and registry inputs, and rewrite every hardcoded path.
   - Pros: matches the target tree in one pass.
   - Cons: highest break risk; downstream scripts and docs will drift unless all references are updated together.
   - Effort: High

### Recommendation
Do the reorganization in two layers: first move non-runtime helpers/docs and static versioned assets into `data/` and `docs/workflow/`, while keeping `scraper.py` and the current consolidation output stable; then update the remaining runtime path references (`scrape_urls.py`, search helpers, `.gitignore`, README) in one follow-up pass. That keeps core scraping behavior unchanged and avoids breaking existing export consumers.

### Risks
- Moving tracked CSV/JSON assets under `data/` without `.gitignore` exceptions will make them disappear from git.
- Moving `scripts/investigate.py` / `scripts/check_excel.py` deeper will break repo-root path assumptions unless their base path logic is updated.
- Moving `reviews_judgeme.csv` out of the root will break the current consolidation CLI and any ad-hoc downstream imports that expect the canonical file there.

### Ready for Proposal
Yes — but the proposal should explicitly separate safe structural moves from runtime path rewrites.
