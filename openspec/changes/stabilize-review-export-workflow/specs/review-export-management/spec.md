# Review Export Management Specification

## Purpose

Defines how scraper runs are stored safely, how export inputs are consolidated, and how manual review supplements enter the Judge.me workflow.

## Requirements

### Requirement: Non-Destructive Raw Exports

The system MUST save each default scraper run as a new raw CSV and MUST NOT overwrite a prior raw export from another run.

#### Scenario: Default run creates a timestamped raw export

- GIVEN a user runs the main scraper without an explicit output path
- WHEN the export is written
- THEN the system MUST create a new CSV inside the default raw export location using a timestamped filename
- AND MUST preserve any previously generated raw CSVs

#### Scenario: Explicit output remains opt-in

- GIVEN a user passes an explicit output path
- WHEN the export is written
- THEN the system MAY write to that requested path
- AND the non-destructive default behavior MUST still apply when no path is supplied

### Requirement: Default Export Workspace Is Git-Ignored

The project MUST provide a default export workspace for generated review artifacts, and that workspace MUST be ignored from git.

#### Scenario: Default workspace is available for raw and manual inputs

- GIVEN the repository is used through the documented workflow
- WHEN generated exports or manual supplement files are created
- THEN the workflow MUST place them under an ignored export workspace with separate raw and manual locations

#### Scenario: Curated output remains compatible

- GIVEN a user completes consolidation
- WHEN the final bundle is produced
- THEN the workflow MUST still support emitting `reviews_judgeme.csv` for downstream compatibility

### Requirement: Picture URL Normalization

All Judge.me-facing CSV outputs MUST encode `picture_urls` as a comma-separated string and MUST include no more than 5 image URLs per review row.

#### Scenario: Review has multiple images

- GIVEN a review contains one or more matched image URLs
- WHEN the row is formatted for export
- THEN the system MUST join image URLs with `,`
- AND MUST keep only the first 5 URLs in that field

#### Scenario: Review has no images

- GIVEN a review has no matched image URLs
- WHEN the row is formatted for export
- THEN the system MUST emit an empty `picture_urls` value

### Requirement: Consolidated Final Export

The workflow MUST provide a consolidation step that merges one or more raw exports and any valid manual supplement files into a final Judge.me CSV.

#### Scenario: Consolidate multiple raw exports

- GIVEN two or more raw export CSVs exist in the raw export location
- WHEN the user runs the documented consolidation workflow
- THEN the system MUST merge those inputs into a single `reviews_judgeme.csv`
- AND MUST preserve Judge.me column order in the final file

#### Scenario: Missing manual supplements does not block consolidation

- GIVEN no manual supplement files are present
- WHEN consolidation runs against raw exports only
- THEN the system MUST still produce the final consolidated CSV

### Requirement: Manual Supplement Path For Screenshot-Derived Reviews

The workflow MUST document a manual supplement path for screenshot-derived reviews and SHALL define the expected CSV shape required for consolidation.

#### Scenario: Operator adds reviewed screenshot data manually

- GIVEN some reviews must be transcribed from screenshots instead of scraped automatically
- WHEN the operator follows the documented workflow
- THEN they MUST be able to place a Judge.me-compatible supplement CSV in the manual supplement location
- AND the consolidation step MUST include those rows in the final export

#### Scenario: Manual supplement shape is invalid

- GIVEN a manual supplement file does not match the documented Judge.me columns
- WHEN consolidation reads that file
- THEN the workflow MUST fail with a clear validation message or skip that file with a clear warning
