-- CivicPulse analytical warehouse — star schema
-- Populated by ETL (pipelines/transformation, spark/jobs) from the OLTP tables in sql/schema/.
-- Do NOT write to these tables directly from the API; only the ETL layer writes here.

CREATE TABLE IF NOT EXISTS dim_date (
    date_key        INTEGER PRIMARY KEY,          -- YYYYMMDD
    full_date       DATE NOT NULL,
    day             INTEGER NOT NULL,
    month           INTEGER NOT NULL,
    year            INTEGER NOT NULL,
    quarter         INTEGER NOT NULL,
    day_of_week     INTEGER NOT NULL,
    is_weekend      BOOLEAN NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_location (
    location_key    SERIAL PRIMARY KEY,
    location_id     INTEGER NOT NULL,             -- natural key back to OLTP locations
    ward_code       VARCHAR(10) NOT NULL,
    ward_name       VARCHAR(100) NOT NULL,
    latitude        DOUBLE PRECISION,
    longitude       DOUBLE PRECISION,
    population      INTEGER
);

CREATE TABLE IF NOT EXISTS dim_category (
    category_key    SERIAL PRIMARY KEY,
    category_id     INTEGER NOT NULL,
    category_name   VARCHAR(50) NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_department (
    department_key  SERIAL PRIMARY KEY,
    department_id   INTEGER NOT NULL,
    department_name VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS fact_complaints (
    complaint_key       SERIAL PRIMARY KEY,
    complaint_id        INTEGER NOT NULL,          -- natural key back to OLTP complaints
    date_key             INTEGER NOT NULL REFERENCES dim_date(date_key),
    location_key          INTEGER NOT NULL REFERENCES dim_location(location_key),
    category_key           INTEGER NOT NULL REFERENCES dim_category(category_key),
    department_key          INTEGER REFERENCES dim_department(department_key),
    severity_score          NUMERIC(3,2),           -- normalized 0-1 for use in priority engine
    resolution_time_days    NUMERIC(6,2),
    status                  VARCHAR(20) NOT NULL,
    is_repeat_complaint     BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_fact_date ON fact_complaints(date_key);
CREATE INDEX IF NOT EXISTS idx_fact_location ON fact_complaints(location_key);
CREATE INDEX IF NOT EXISTS idx_fact_category ON fact_complaints(category_key);
