# Data

Not committed to git (see `.gitignore`) — this describes the convention, not contents.

## `raw/`
Unmodified downloads from open data sources (e.g. data.gov.in exports, OpenStreetMap extracts) plus any synthetic generation output straight from `pipelines/ingestion/generate_synthetic_complaints.py`. Never edited by hand.

## `processed/`
Output of the cleaning/validation/feature-engineering pipeline (`pipelines/transformation/`) — what actually gets loaded into PostgreSQL and what `ml/training/` scripts read from.

## Synthetic data labeling

Any record not sourced from a real open dataset carries `is_synthetic = true` in the `complaints` table (see `sql/schema/01_oltp_schema.sql`). This is non-negotiable: synthetic and real records must always be distinguishable in the database, in any analysis, and in anything shown in an interview or demo.

## Suggested first real dataset

Start with a single open civic-complaints dataset (e.g. a municipal corporation's public grievance redressal export from data.gov.in) rather than trying to combine several sources on day one — get the pipeline working end-to-end on one source before adding more.
