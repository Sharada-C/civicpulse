-- CivicPulse OLTP schema
-- Core operational tables. The warehouse (sql/warehouse/) is built FROM these via ETL,
-- it is not a duplicate of them.

CREATE TABLE IF NOT EXISTS departments (
    department_id   SERIAL PRIMARY KEY,
    name            VARCHAR(100) NOT NULL UNIQUE,
    description     TEXT
);

CREATE TABLE IF NOT EXISTS wards (
    ward_id         SERIAL PRIMARY KEY,
    ward_code       VARCHAR(10) NOT NULL UNIQUE,   -- e.g. 'W12'
    name            VARCHAR(100) NOT NULL,
    population      INTEGER
);

CREATE TABLE IF NOT EXISTS locations (
    location_id     SERIAL PRIMARY KEY,
    ward_id         INTEGER REFERENCES wards(ward_id),
    latitude        DOUBLE PRECISION NOT NULL,
    longitude       DOUBLE PRECISION NOT NULL,
    address         TEXT
);

CREATE TABLE IF NOT EXISTS categories (
    category_id     SERIAL PRIMARY KEY,
    name            VARCHAR(50) NOT NULL UNIQUE,     -- normalized, e.g. 'STREETLIGHT'
    default_department_id INTEGER REFERENCES departments(department_id)
);

CREATE TABLE IF NOT EXISTS users (
    user_id         SERIAL PRIMARY KEY,
    email           VARCHAR(255) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    full_name       VARCHAR(150),
    role            VARCHAR(20) NOT NULL CHECK (role IN ('CITIZEN', 'ANALYST', 'ADMIN', 'DEPARTMENT_OFFICER')),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS employees (
    employee_id     SERIAL PRIMARY KEY,
    user_id         INTEGER REFERENCES users(user_id),
    department_id   INTEGER REFERENCES departments(department_id)
);

CREATE TABLE IF NOT EXISTS complaints (
    complaint_id    SERIAL PRIMARY KEY,
    citizen_id      INTEGER REFERENCES users(user_id),
    category_id     INTEGER NOT NULL REFERENCES categories(category_id),
    department_id   INTEGER REFERENCES departments(department_id),
    location_id     INTEGER NOT NULL REFERENCES locations(location_id),
    description     TEXT,
    severity        VARCHAR(10) CHECK (severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    status          VARCHAR(20) NOT NULL DEFAULT 'OPEN' CHECK (status IN ('OPEN', 'IN_PROGRESS', 'RESOLVED', 'CLOSED')),
    is_synthetic    BOOLEAN NOT NULL DEFAULT FALSE,   -- synthetic data must always be labeled
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    resolved_at     TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS complaint_updates (
    update_id       SERIAL PRIMARY KEY,
    complaint_id    INTEGER NOT NULL REFERENCES complaints(complaint_id),
    updated_by      INTEGER REFERENCES users(user_id),
    old_status      VARCHAR(20),
    new_status      VARCHAR(20),
    note            TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Indexes that the query-optimization module (README §8) is built around
CREATE INDEX IF NOT EXISTS idx_complaints_status ON complaints(status);
CREATE INDEX IF NOT EXISTS idx_complaints_category ON complaints(category_id);
CREATE INDEX IF NOT EXISTS idx_complaints_created_at ON complaints(created_at);
CREATE INDEX IF NOT EXISTS idx_complaints_location ON complaints(location_id);
CREATE INDEX IF NOT EXISTS idx_locations_ward ON locations(ward_id);
