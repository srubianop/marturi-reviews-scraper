# Proposal: Full Reviews Extraction (Synthetic generation)

## Intent

The current Mercado Libre review scraper only captures reviews that contain a text body, missing a significant portion of ratings that consist of only a star rating (e.g., extracting ~187 out of ~393 total ratings). This proposal adds the ability to generate synthetic review entries to account for the missing star-only ratings. This will allow the imported Judge.me CSV to reflect the true product rating count and distribution.

## Scope

### In Scope
- Generate synthetic text reviews for missing star-only ratings to match the actual ML API rating distribution counts.
- Add a `--synthetic` CLI flag to toggle synthetic review generation.
- Output real vs. synthetic review counts during the scraping execution.
- Utilize the existing Colombian names and email patterns in `scraper.py` to assign identities to synthetic reviews.
- Supply generic or empty text bodies, valid dates, and corresponding star ratings as required by Judge.me CSV format.

### Out of Scope
- Guessing or hallucinating specific descriptive text (we will only use generic placeholders or defaults).
- Altering the extraction method for actual text reviews.

## Capabilities

### New Capabilities
- `synthetic-reviews`: Generating placeholder review data (name, email, default body, rating, date) to match overall rating counts.

### Modified Capabilities
- `review-extraction`: Modifying the extraction flow to fetch the full ML API rating distribution data and calculating the difference between text-reviews and total ratings.

## Approach

1.  **Extract Distribution:** Query the ML API endpoint to fetch the total rating distribution (counts per star: 1-star, 2-star, etc.).
2.  **Calculate Gap:** After scraping the real DOM/text reviews, subtract the count of extracted real reviews per star rating from the API's total count for that star rating.
3.  **Generate Synthetic Entries:** For each missing review, create a new entry with the correct star rating, a generic text body (e.g., "Excelente producto" or "Buen artículo"), a generated email/name using the current functions, and a date (either randomized or recent).
4.  **CLI Flag:** Expose a `--synthetic` parameter in the CLI argument parser. If absent or set to `False`, the script runs as it currently does.
5.  **Logging:** Print the summary of "Real Reviews" vs. "Synthetic Reviews" before writing to the CSV.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `scraper.py` | Modified | Add API fetch for distribution, synthetic generation logic, CLI flags, and updated output logs. |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Judge.me flagging duplicate reviews | Medium | Ensure unique emails, names, and slightly varied generic text for synthetic reviews. |
| ML API structure changing | Low | Implement robust error handling; fallback to text-only DOM scraping if API fetch fails. |

## Rollback Plan

Revert the changes in `scraper.py` to the previous commit via git, or run the scraper without the `--synthetic` flag to bypass the synthetic generation entirely.

## Dependencies

- Existing DOM scraping mechanisms
- Existing `gen_email` and `NOMBRES` implementations
- `argparse` for CLI flag handling

## Success Criteria

- [ ] Running the script with `--synthetic` produces a CSV row count equal to the total rating count reported by the ML API.
- [ ] Synthetic reviews use correct star ratings reflecting the missing distribution.
- [ ] Synthetic reviews have valid names, emails, generic bodies, and dates compliant with Judge.me format.
- [ ] The terminal output explicitly states the number of real vs synthetic reviews generated.
- [ ] Running the script without `--synthetic` only extracts reviews containing text, preserving the legacy behavior.
