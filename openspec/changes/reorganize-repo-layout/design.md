# Design: Reorganize Repo Layout

## Technical Approach

Apply a small structural cleanup without changing the public scraper workflow. Keep `scraper.py` at the root, keep workflow CLIs in `scripts/`, move versioned reference assets under `data/`, move investigative helpers under `scripts/search/`, and keep generated outputs in ignored export/temp folders. Path changes stay procedural and local: each affected script computes `REPO_ROOT` once, then derives stable asset/output paths from it.

## Architecture Decisions

| Decision | Choice | Alternatives considered | Rationale |
|---|---|---|---|
| Root entrypoint | Keep `scraper.py` at repo root | Move scraper into `scripts/` too | Spec requires preserving `python scraper.py ...`; root stays a stable CLI surface. |
| Asset placement | Move tracked JSON/CSV inputs to `data/` and historical CSVs to `data/legacy/` | Keep tracked assets in root | Separates versioned inputs from generated exports and reduces root clutter. |
| Helper relocation | Move only investigative/search helpers to `scripts/search/` | Move every script into subfolders | Small repo, so only the noisy helper scripts move; main workflow CLIs remain easy to find. |
| Path resolution | Use `REPO_ROOT = Path(__file__).resolve().parents[n]` plus named constants per script | Add config loader or package refactor | Procedural repo, no dependency budget for abstraction, and only a few scripts need updates. |
| Output compatibility | Keep `reviews_judgeme.csv` as canonical consolidated output in root | Move final bundle into `data/` | Existing downstream flow already expects the root bundle; changing that would be behavior drift. |

## Data Flow

```text
data/productos.json + data/reviews_registry.json
            │
            └─ scripts/scrape_urls.py
                    └─ exports/raw/*.csv

data/reviews_judgeme_template.csv + exports/raw/*.csv + exports/manual/*.csv
            │
            └─ scripts/consolidate_reviews.py
                    └─ reviews_judgeme.csv

scripts/search/*.py
    └─ resolve REPO_ROOT correctly from deeper location
```

Sequence shape:

```text
CLI -> resolve repo root -> resolve tracked asset paths -> read/write existing workflow locations
```

## File Changes

| File | Action | Description |
|---|---|---|
| `data/productos.json` | Create/move | New tracked home for product mapping data. |
| `data/reviews_registry.json` | Create/move | New tracked home for scrape registry state. |
| `data/reviews_judgeme_template.csv` | Create/move | Tracked template moved out of root. |
| `data/legacy/reviews_judgeme.csv` | Create/move if treated as reference | Preserve historical bundle without redefining active output. |
| `scripts/search/investigate.py` | Move/modify | Update repo-root math and default asset paths. |
| `scripts/search/check_excel.py` | Move/modify | Update repo-root math for deeper nesting. |
| `scripts/scrape_urls.py` | Modify | Replace root-relative JSON reads/writes with `data/` constants. |
| `scripts/consolidate_reviews.py` | Modify | Point template/reference reads to `data/`; keep final output root-default. |
| `.gitignore` | Modify | Keep `exports/`, screenshots, temp files ignored; explicitly unignore tracked files under `data/`. |
| `README.md` | Modify | Document new layout and updated command/path references. |
| `docs/workflow/` | Create | Home for non-OpenSpec workflow notes if any existing supplementary docs are moved. |
| `openspec/changes/reorganize-repo-layout/design.md` | Create | OpenSpec design artifact. |

## Interfaces / Contracts

```python
# scripts/scrape_urls.py
REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"
PRODUCTS_PATH = DATA_DIR / "productos.json"
REGISTRY_PATH = DATA_DIR / "reviews_registry.json"

# scripts/search/*.py
REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"
```

`.gitignore` contract:
- keep broad ignores for generated `*.csv` / `*.json`
- add explicit exceptions for `data/productos.json`, `data/reviews_registry.json`, `data/reviews_judgeme_template.csv`, and any committed `data/legacy/*.csv`

## Testing Strategy

| Layer | What to Test | Approach |
|---|---|---|
| Manual layout | Root and `scripts/` contain only intended files | Inspect tree after move. |
| Manual CLI | `python scripts/scrape_urls.py` reads/writes moved JSON assets | Run once and confirm `data/reviews_registry.json` updates. |
| Manual helper | `python scripts/search/investigate.py` and `check_excel.py` still resolve repo files | Run both from repo root. |
| Manual docs | README commands and referenced paths exist | Follow documented paths/commands after reorg. |

No automated test framework exists.

## Migration / Rollout

1. Create target folders: `data/legacy/`, `docs/workflow/`, `scripts/search/`.
2. Move tracked assets/helpers first.
3. Rewrite path constants in moved/affected scripts.
4. Update `.gitignore` before finalizing moves so tracked assets do not disappear.
5. Update README/docs last, after paths are stable.

No runtime migration or fallback layer is needed; this is a same-change structural rewrite.

## Open Questions

- [ ] Which current non-OpenSpec workflow documents should actually be moved into `docs/workflow/`, since `docs/` is presently empty?
