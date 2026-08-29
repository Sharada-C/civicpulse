# Power BI Dashboard

Connects to the PostgreSQL warehouse (`fact_complaints` + dimensions) — read-only. Put the `.pbix` file in this folder once built; it's gitignored by default (binary, environment-specific) except for exported screenshots, which belong in `docs/screenshots/`.

## Pages

### 1. Executive Overview
Total Complaints · Open · Resolved · Resolution Rate · Average Resolution Time · Critical Complaints — single KPI-card row plus a trend line over time.

### 2. Geographic Intelligence
Map visual using `dim_location` lat/long — hotspots, ward performance choropleth, complaint density.

### 3. Department Performance
Table/matrix: department, backlog, resolution rate, SLA breach count, average resolution time. Sort by backlog descending by default — that's the actionable view for department heads.

### 4. Predictive Analytics
High-risk complaints (from the severity model), predicted resolution time (from the regression model), emerging hotspots (DBSCAN cluster growth week-over-week), priority ranking (from `sql/analytics/priority_score.sql`).

## Connecting

1. Get Data → PostgreSQL database → host `localhost`, port `5432`, database from `.env` `POSTGRES_DB`.
2. Import (not DirectQuery) for MVP — the warehouse refresh cadence matches the Airflow daily schedule, so a scheduled Import refresh is sufficient and simpler than DirectQuery.
3. Build a proper star-schema relationship model in Power BI (Model view) mirroring `sql/warehouse/01_star_schema.sql` — don't just drag in the flat `fact_complaints` table.

## DAX starting points

- `Resolution Rate = DIVIDE([Resolved Complaints], [Total Complaints], 0)`
- `SLA Breach Rate = DIVIDE([Complaints Exceeding Target], [Total Complaints], 0)`

Build these as explicit DAX measures (not calculated columns) so they aggregate correctly across any filter/slicer combination on the report.
