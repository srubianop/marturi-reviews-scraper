# Tasks: Full Reviews Extraction (Synthetic Generation)

## Phase 1: Infrastructure

- [ ] 1.1 Add `--synthetic` CLI flag to argparse in `scraper.py` (action="store_true", help text)
- [ ] 1.2 Define `BODIES_GENERIC` constant with 6-8 Colombian Spanish phrases
- [ ] 1.3 Add `requests` import for API calls

## Phase 2: Core Implementation

- [ ] 2.1 Implement `fetch_rating_distribution(item_id)` - GET request to ML public API, parse rating_levels dict
- [ ] 2.2 Implement `compute_gap(rating_levels, real_reviews)` - per-star gap calculation
- [ ] 2.3 Implement `generate_synthetic_entry(star, product, oldest_date, used_names, seed)` helper
- [ ] 2.4 Implement `generate_synthetic_entries(gap, product, oldest_date, used_names)` - main generator loop with unique names/emails

## Phase 3: Integration

- [ ] 3.1 Add API fetch call in `scrape_product()` after DOM scraping completes (if synthetic enabled)
- [ ] 3.2 Add gap calculation between API totals and real review counts per star
- [ ] 3.3 Add synthetic generation call with date range from real reviews
- [ ] 3.4 Merge: `real_reviews + synthetic_reviews` into unified list
- [ ] 3.5 Add summary logging: print real count, synthetic count, total
- [ ] 3.6 Strip `is_synthetic` key before CSV export in `main()`

## Phase 4: Manual Testing

- [ ] 4.1 Test `--synthetic` flag absent: verify legacy behavior unchanged
- [ ] 4.2 Test `--synthetic` enabled: verify CSV row count equals ML API total
- [ ] 4.3 Test synthetic entries: check unique emails, valid dates, correct star ratings
- [ ] 4.4 Test failure mode: verify graceful fallback when API returns error
