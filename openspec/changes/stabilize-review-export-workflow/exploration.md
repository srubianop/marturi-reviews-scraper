# Exploration: stabilize-review-export-workflow

### Current State
- The real CLI entrypoint is `scraper.py`, but it only forwards into `.agent/skills/ml-reviews-scraper/assets/scraper.py`.
- That implementation writes a single CSV with `open(..., "w")`, so every run replaces the previous export.
- A second workflow exists in `scripts/scrape_urls.py`: it appends to `reviews_judgeme.csv` and also maintains `data/reviews_registry.json`, but it uses a different `picture_urls` delimiter (`;`), so the two paths are not behaviorally aligned.
- The repo already has generated artifacts in circulation (`reviews_judgeme.csv`, `tmp_reviews/*.csv`, screenshots, registry/output files), so the workflow currently relies on manual consolidation instead of a clear export/run model.

### Affected Areas
- `scraper.py` — public CLI entrypoint; user-facing behavior is defined by the delegated implementation.
- `.agent/skills/ml-reviews-scraper/assets/scraper.py` — primary export pipeline; currently overwrites output and emits comma-joined `picture_urls`.
- `scripts/scrape_urls.py` — alternate append-based workflow; useful evidence of the intended consolidation need, but inconsistent with the main path.
- `.gitignore` — already ignores generated CSV/JSON broadly, but the workflow still creates root-level artifacts that invite confusion.
- `README.md` — documents the default root output file and should reflect safer export conventions.

### Approaches
1. **Minimal stabilization** — keep the scraper logic intact, but make output safer and more explicit.
   - Pros: lowest risk; preserves current scraping behavior.
   - Cons: still leaves consolidation mostly manual.
   - Effort: Low

2. **Run-oriented export workflow** — write each run to an ignored timestamped/partitioned export directory, then provide an explicit consolidate step (or `--append` mode) for merging product runs.
   - Pros: solves overwrite pain; supports manual supplements; keeps raw runs auditable.
   - Cons: adds a small amount of CLI and file-management complexity.
   - Effort: Medium

3. **Workflow split: raw exports + curated bundle** — store per-product raw CSVs plus optional manual-review supplement files/screenshots, then build the final Judge.me CSV from those inputs.
   - Pros: best for messy real-world usage and broken listing edge cases.
   - Cons: larger scope; more coordination between artifacts.
   - Effort: Medium/High

### Recommendation
Keep the change focused on workflow stabilization, not extraction logic. The best scope is: default exports to an ignored run directory (or timestamped filename), add an explicit append/consolidate path for multi-product runs, standardize `picture_urls` to comma-separated values with a max of 5 URLs everywhere, and document a separate manual-supplement path for screenshot-derived reviews. That addresses the real pain without risking the core scraper.

### Risks
- Aligning the two scripts may expose hidden assumptions in downstream manual processes.
- Changing the default output location may break any ad-hoc scripts that expect `reviews_judgeme.csv` in the repo root.
- If manual supplements are not standardized, consolidation can still become messy even after the export workflow improves.

### Ready for Proposal
Yes — this is ready for a narrowly scoped proposal centered on output organization, consolidation, and git hygiene.
