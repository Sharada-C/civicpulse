import os

from sqlalchemy import create_engine, text


DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+psycopg2://civicpulse:changeme@localhost:5433/civicpulse"
)


def load_complaints():
    engine = create_engine(DATABASE_URL)

    with engine.begin() as connection:

        connection.execute(
            text("""
                INSERT INTO complaints (
                    complaint_id,
                    category_id,
                    department_id,
                    location_id,
                    description,
                    severity,
                    status,
                    is_synthetic,
                    created_at,
                    resolved_at
                )
                SELECT
                    s.complaint_id,
                    c.category_id,
                    d.department_id,
                    l.location_id,
                    s.description,
                    s.severity,
                    s.status,
                    s.is_synthetic,
                    s.created_at::timestamptz,
                    NULLIF(s.resolved_at, '')::timestamptz
                FROM staging_complaints s

                JOIN categories c
                    ON c.name = s.category

                JOIN departments d
                    ON d.name = s.department

                JOIN LATERAL (
                    SELECT
                        location_id
                    FROM locations loc
                    JOIN wards w
                        ON w.ward_id = loc.ward_id
                    WHERE w.ward_code = s.ward
                    ORDER BY
                        POWER(loc.latitude - s.latitude, 2)
                        +
                        POWER(loc.longitude - s.longitude, 2)
                    LIMIT 1
                ) l
                    ON TRUE

                ON CONFLICT (complaint_id)
                DO NOTHING;
            """)
        )

    print("Complaints loaded successfully")


if __name__ == "__main__":
    load_complaints()