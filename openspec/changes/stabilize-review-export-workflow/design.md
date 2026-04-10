# Design: Stabilize Review Export Workflow

## Technical Approach

Keep scraping logic intact and stabilize only the export workflow. The main scraper will produce append-only raw exports in `exports/raw/`, a dedicated consolidation CLI will build the final root `reviews_judgeme.csv`, and manual supplements will be dropped into `exports/manual/` using the same Judge.me columns. This keeps the repo procedural, avoids overwrites, and preserves the existing final import file for downstream use.

## Architecture Decisions

| Decision | Choice | Alternatives considered | Rationale |
|---|---|---|---|
| Raw export strategy | Timestamped CSVs under `exports/raw/` | Keep overwriting root CSV; append in-place forever | Raw runs become auditable and non-destructive. |
| Final export generation | New `scripts/consolidate_reviews.py` | Add `--append` into scraper | A separate CLI keeps scraping and curation concerns simple in this small repo. |
| Shared contract | Reuse existing Judge.me `FIELDNAMES` everywhere | Separate raw schema | Same schema lets manual CSVs merge without adapters. |
| `picture_urls` normalization | Always comma-separated, max 5 URLs | Preserve mixed `;` / `,` behavior | Prevents format drift between scripts and final exports. |

## Data Flow

```text
python scraper.py URL handle [URL handle...]
    │
    ├─ scrape reviews (unchanged)
    └─ write raw run → exports/raw/{timestamp}__{handles}.csv

manual edits / screenshot-derived reviews
    └─ saved by user → exports/manual/*.csv

python scripts/consolidate_reviews.py
    │
    ├─ read selected raw exports
    ├─ read exports/manual/*.csv
    ├─ normalize picture_urls + headers
    ├─ prefer newest raw rows per product_handle
    └─ write final bundle → reviews_judgeme.csv
```

Sequence shape:

```text
Scraper -> exports/raw/*.csv
Manual reviewer -> exports/manual/*.csv
Consolidator -> normalize -> merge -> reviews_judgeme.csv
```

## File Changes

| File | Action | Description |
|---|---|---|
| `.agent/skills/ml-reviews-scraper/assets/scraper.py` | Modify | Change default output to timestamped raw export, keep `-o/--output` override, normalize `picture_urls`. |
| `scraper.py` | Keep/minor modify | Wrapper stays as CLI entrypoint; only update help text if needed. |
| `scripts/consolidate_reviews.py` | Create | Procedural merger for raw exports + manual supplements into final root CSV. |
| `scripts/scrape_urls.py` | Modify | Normalize `picture_urls` to comma + max 5 and align default output behavior with raw export workflow where practical. |
| `README.md` | Modify | Document `exports/raw`, `exports/manual`, and consolidation step. |
| `.gitignore` | Modify | Explicitly ignore `exports/` and keep template/example files tracked if needed. |

## Interfaces / Contracts

```python
FIELDNAMES = [
    "title", "body", "rating", "review_date", "reviewer_name",
    "reviewer_email", "product_id", "product_handle", "reply", "picture_urls",
]

def normalize_picture_urls(value: str | list[str]) -> str:
    """Return comma-separated URLs, max 5, no blanks."""

def build_raw_output_path(handles: list[str], now: datetime) -> str:
    """exports/raw/20260409T221530Z__handle-a-handle-b.csv"""
```

`scripts/consolidate_reviews.py` CLI:

```text
python scripts/consolidate_reviews.py [--raw-dir exports/raw] [--manual-dir exports/manual] [--output reviews_judgeme.csv] [inputs...]
```

- If explicit input files are passed, merge only those.
- If no inputs are passed, scan `exports/raw/*.csv`, group rows by `product_handle`, and keep the newest raw source per handle.
- Then append all valid `exports/manual/*.csv` rows.

Manual supplement contract:
- Users create CSVs with the same `FIELDNAMES` (template can be copied from `data/reviews_judgeme_template.csv`).
- Manual files are additive only; they are never treated as replacements for raw exports.

## Testing Strategy

| Layer | What to Test | Approach |
|---|---|---|
| Manual CLI | Default scraper run creates unique file in `exports/raw/` | Run scraper twice and verify no overwrite. |
| Manual normalization | `picture_urls` always comma-separated and capped at 5 | Inspect raw and final CSV rows with images. |
| Manual consolidation | Raw + manual files merge into root `reviews_judgeme.csv` | Create two raw inputs plus one manual supplement and verify output row counts. |
| Manual fallback | `-o custom.csv` still works | Run scraper with explicit output override. |

No automated test framework exists; verification remains manual.

## Migration / Rollout

No data migration required. Existing root `reviews_judgeme.csv` remains the final curated artifact, but it is no longer the scraper's default raw output. Rollout order: update scraper defaults, add consolidator, then update docs.

## Open Questions

- [ ] Should `scripts/scrape_urls.py` fully adopt raw-export defaults now, or only normalize formatting and remain a secondary/debug path?
