# Synthetic Reviews Specification

## Purpose

Defines how the scraper generates synthetic review entries to fill the gap between actual text-reviews scraped from Mercado Libre and the true total rating count reported by the ML API.

## Requirements

### Requirement: Gap Calculation

The system MUST compute, per star level (1–5), the difference between the ML API's total rating count and the count of real scraped text-reviews for that star level.

#### Scenario: Positive gap exists for a star level

- GIVEN the ML API reports 80 five-star ratings and 60 real five-star reviews were scraped
- WHEN the gap is calculated
- THEN the system MUST flag 20 synthetic five-star entries to generate

#### Scenario: No gap for a star level

- GIVEN the ML API reports 10 two-star ratings and 10 real two-star reviews were scraped
- WHEN the gap is calculated
- THEN the system MUST NOT generate any synthetic entries for that star level

#### Scenario: ML API fetch fails

- GIVEN the ML API endpoint is unreachable or returns an error
- WHEN the gap calculation is attempted
- THEN the system MUST skip synthetic generation and log a warning
- AND MUST continue exporting only the real scraped reviews

---

### Requirement: Synthetic Entry Generation

The system MUST generate one synthetic review entry per gap unit, with a valid star rating, unique identity, generic body, and a plausible date.

#### Scenario: Identity assignment

- GIVEN a synthetic entry must be created for a 5-star gap
- WHEN the entry is assembled
- THEN it MUST have a unique name drawn from `NOMBRES` and a unique email produced by `gen_email`
- AND MUST NOT reuse an identity already used by a real review in the same run

#### Scenario: Generic body text

- GIVEN a synthetic entry for any star level
- WHEN the body text is assigned
- THEN it MUST be a non-empty generic Colombian Spanish phrase (e.g., "Excelente producto", "Buen artículo")
- AND MUST NOT be identical for all synthetic entries (at minimum two distinct phrases used across the run)

#### Scenario: Date assignment

- GIVEN a synthetic entry is being generated
- WHEN the date is assigned
- THEN the date MUST fall between the oldest real review date and the current date (inclusive)
- AND MUST be formatted as `YYYY-MM-DD` to satisfy Judge.me CSV requirements

#### Scenario: Star rating correctness

- GIVEN a synthetic entry filling a 3-star gap
- WHEN the entry is finalised
- THEN the `rating` field MUST be exactly `3`

---

### Requirement: Synthetic Flag

The system MUST mark each synthetic entry so that real and synthetic reviews can be distinguished in intermediate processing.

#### Scenario: Synthetic entry marked in output data

- GIVEN a synthetic entry has been generated
- WHEN it is merged into the review list
- THEN it MUST carry an internal flag `is_synthetic: true` (or equivalent) before CSV formatting
- AND the flag MUST NOT appear as a column in the final Judge.me CSV export

---

### Requirement: Output Summary

The system MUST print a run summary to stdout that distinguishes real from synthetic counts.

#### Scenario: Both real and synthetic reviews present

- GIVEN the scraper finishes and `--synthetic` was enabled
- WHEN the summary is printed
- THEN stdout MUST contain the exact real review count and exact synthetic review count
- AND MUST contain the combined total

#### Scenario: Only real reviews (synthetic disabled)

- GIVEN `--synthetic` is not passed
- WHEN the summary is printed
- THEN stdout MUST show only the real review count with no mention of synthetic entries

---

### Requirement: CLI Control Flag

The system MUST expose a `--synthetic` boolean CLI flag that enables or disables synthetic generation.

#### Scenario: Flag present — synthesis enabled

- GIVEN the user runs the script with `--synthetic`
- WHEN execution completes
- THEN the output CSV row count MUST equal the ML API total rating count

#### Scenario: Flag absent — legacy mode

- GIVEN the user runs the script without `--synthetic`
- WHEN execution completes
- THEN the output CSV MUST contain only reviews that have a real scraped text body
- AND the scraper behavior MUST be identical to pre-change behavior
