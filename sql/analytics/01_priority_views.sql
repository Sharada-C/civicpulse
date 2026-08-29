CREATE OR REPLACE VIEW category_priority AS

WITH category_stats AS (

    SELECT
        dc.category_name,

        COUNT(*) AS complaint_count,

        AVG(fc.severity_score) AS avg_severity,

        AVG(fc.resolution_time_days) AS avg_resolution_days,

        AVG(
            CASE
                WHEN fc.is_repeat_complaint THEN 1.0
                ELSE 0.0
            END
        ) AS repeat_rate

    FROM fact_complaints fc

    JOIN dim_category dc
        ON fc.category_key = dc.category_key

    GROUP BY dc.category_name
),

normalized AS (

    SELECT
        *,

        complaint_count::NUMERIC
            / MAX(complaint_count) OVER ()
            AS frequency_score,

        avg_resolution_days
            / MAX(avg_resolution_days) OVER ()
            AS resolution_score

    FROM category_stats
)

SELECT

    category_name,

    complaint_count,

    ROUND(avg_severity, 3)
        AS severity_score,

    ROUND(repeat_rate * 100, 2)
        AS repeat_rate_percent,

    ROUND(avg_resolution_days, 2)
        AS avg_resolution_days,

    ROUND(
        0.40 * avg_severity
        + 0.30 * frequency_score
        + 0.20 * repeat_rate
        + 0.10 * resolution_score,
        3
    ) AS priority_score

FROM normalized;
CREATE OR REPLACE VIEW ward_category_priority AS

WITH ward_category_stats AS (

    SELECT
        dl.ward_code,
        dl.ward_name,
        dl.population,

        dc.category_name,

        COUNT(*) AS complaint_count,

        AVG(fc.severity_score) AS avg_severity,

        AVG(fc.resolution_time_days) AS avg_resolution_days,

        AVG(
            CASE
                WHEN fc.is_repeat_complaint THEN 1.0
                ELSE 0.0
            END
        ) AS repeat_rate

    FROM fact_complaints fc

    JOIN dim_location dl
        ON fc.location_key = dl.location_key

    JOIN dim_category dc
        ON fc.category_key = dc.category_key

    GROUP BY
        dl.ward_code,
        dl.ward_name,
        dl.population,
        dc.category_name
),

normalized AS (

    SELECT
        *,

        complaint_count::NUMERIC
            / MAX(complaint_count) OVER ()
            AS frequency_score,

        avg_resolution_days
            / MAX(avg_resolution_days) OVER ()
            AS resolution_score

    FROM ward_category_stats
)

SELECT

    ward_code,
    ward_name,
    category_name,
    population,

    complaint_count,

    ROUND(
        complaint_count * 10000.0 / population,
        2
    ) AS complaints_per_10000,

    ROUND(avg_severity, 3)
        AS severity_score,

    ROUND(repeat_rate * 100, 2)
        AS repeat_rate_percent,

    ROUND(avg_resolution_days, 2)
        AS avg_resolution_days,

    ROUND(
        0.40 * avg_severity
        + 0.30 * frequency_score
        + 0.20 * repeat_rate
        + 0.10 * resolution_score,
        3
    ) AS priority_score

FROM normalized;