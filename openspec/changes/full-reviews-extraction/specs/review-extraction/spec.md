# Review Extraction Specification

## Purpose

Defines how the scraper fetches rating distribution data from the ML API and integrates it into the main extraction pipeline alongside the existing DOM text-review scraping.

## Requirements

### Requirement: ML API Rating Distribution Fetch

The system MUST query the ML API endpoint for total rating counts per star level before synthetic generation begins.

#### Scenario: Successful API response

- GIVEN a valid Mercado Libre item ID is provided
- WHEN the scraper queries `api.mercadolibre.com/reviews/item/{ITEM_ID}`
- THEN the system MUST parse the `rating_levels` field from the response
- AND MUST store the count for each star level (1–5)

#### Scenario: API response missing `rating_levels`

- GIVEN the ML API returns a 200 response but lacks the `rating_levels` field
- WHEN the scraper attempts to parse it
- THEN the system MUST log a warning and skip synthetic generation
- AND MUST proceed with exporting only the real scraped reviews

#### Scenario: Non-2xx API response

- GIVEN the ML API returns a 4xx or 5xx status code
- WHEN the scraper receives it
- THEN the system MUST log the HTTP status and skip synthetic generation
- AND MUST NOT abort the entire scraping run

---

### Requirement: Pipeline Integration Order

The system MUST execute the ML API fetch before merging synthetic entries, and after completing real DOM text-review scraping.

#### Scenario: Correct execution order

- GIVEN a scraping run with `--synthetic` enabled
- WHEN the pipeline executes
- THEN the order MUST be: (1) DOM scraping → (2) ML API fetch → (3) gap calculation → (4) synthetic generation → (5) merge → (6) CSV export

#### Scenario: ML API fetch failure does not block DOM results

- GIVEN the ML API is unavailable
- WHEN the pipeline runs
- THEN steps 1 and 6 (DOM scraping and CSV export) MUST still complete successfully with real reviews only

---

### Requirement: Total Count Validation

The system SHOULD validate that the combined real + synthetic count equals the ML API total.

#### Scenario: Count matches API total

- GIVEN synthetic generation completes with `--synthetic` enabled
- WHEN the final review list is assembled
- THEN the total count MUST equal the sum of all `rating_levels` values from the ML API

#### Scenario: Count mismatch detected

- GIVEN a discrepancy exists between the assembled count and the ML API total
- WHEN the validation check runs
- THEN the system SHOULD log a warning with the expected vs. actual counts
- AND MUST NOT block CSV export due to the mismatch
