-- CivicPulse Priority Engine
-- Ranks wards using six explainable factors:
--
-- severity     30%
-- frequency    20%
-- growth       15%
-- repeat       15%
-- population   10%
-- delay        10%

WITH ward_metrics AS (

    SELECT
        dl.ward_code,
        dl.ward_name,
        dl.population,

        AVG(fc.severity_score) AS avg_severity,

        COUNT(*) AS complaint_count,

        AVG(
            CASE
                WHEN fc.is_repeat_complaint THEN 1.0
                ELSE 0.0
            END
        ) AS repeat_rate,

        AVG(fc.resolution_time_days) AS avg_resolution_days

    FROM fact_complaints fc

    JOIN dim_location dl
        ON fc.location_key = dl.location_key

    GROUP BY
        dl.ward_code,
        dl.ward_name,
        dl.population
),

monthly_counts AS (

    SELECT
        dl.ward_code,
        DATE_TRUNC('month', dd.full_date) AS month,
        COUNT(*) AS complaint_count

    FROM fact_complaints fc

    JOIN dim_location dl
        ON fc.location_key = dl.location_key

    JOIN dim_date dd
        ON fc.date_key = dd.date_key

    GROUP BY
        dl.ward_code,
        DATE_TRUNC('month', dd.full_date)
),

monthly_growth AS (

    SELECT
        ward_code,
        month,
        complaint_count,

        LAG(complaint_count)
            OVER (
                PARTITION BY ward_code
                ORDER BY month
            ) AS prev_month_count

    FROM monthly_counts
),

latest_growth AS (

    SELECT DISTINCT ON (ward_code)

        ward_code,

        CASE
            WHEN prev_month_count IS NULL
                 OR prev_month_count = 0
            THEN 0

            ELSE
                100.0
                * (complaint_count - prev_month_count)
                / prev_month_count

        END AS growth_pct

    FROM monthly_growth

    ORDER BY
        ward_code,
        month DESC
),

combined AS (

    SELECT

        wm.*,

        COALESCE(lg.growth_pct, 0)
            AS growth_pct

    FROM ward_metrics wm

    LEFT JOIN latest_growth lg
        ON wm.ward_code = lg.ward_code
),

normalized AS (

    SELECT

        *,

        (
            complaint_count
            - MIN(complaint_count) OVER ()
        )
        /
        NULLIF(
            MAX(complaint_count) OVER ()
            - MIN(complaint_count) OVER (),
            0
        ) AS frequency_norm,

        (
            growth_pct
            - MIN(growth_pct) OVER ()
        )
        /
        NULLIF(
            MAX(growth_pct) OVER ()
            - MIN(growth_pct) OVER (),
            0
        ) AS growth_norm,

        (
            population
            - MIN(population) OVER ()
        )
        /
        NULLIF(
            MAX(population) OVER ()
            - MIN(population) OVER (),
            0
        ) AS population_norm,

        (
            avg_resolution_days
            - MIN(avg_resolution_days) OVER ()
        )
        /
        NULLIF(
            MAX(avg_resolution_days) OVER ()
            - MIN(avg_resolution_days) OVER (),
            0
        ) AS delay_norm

    FROM combined
)

SELECT

    ward_code,
    ward_name,

    ROUND(
        0.30 * COALESCE(avg_severity, 0)
        +
        0.20 * COALESCE(frequency_norm, 0)
        +
        0.15 * COALESCE(growth_norm, 0)
        +
        0.15 * COALESCE(repeat_rate, 0)
        +
        0.10 * COALESCE(population_norm, 0)
        +
        0.10 * COALESCE(delay_norm, 0),
        3
    ) AS priority_score,

    ROUND(COALESCE(avg_severity, 0), 3)
        AS severity_score,

    ROUND(COALESCE(frequency_norm, 0), 3)
        AS frequency_score,

    ROUND(COALESCE(growth_pct, 0), 1)
        AS growth_pct,

    ROUND(COALESCE(repeat_rate, 0) * 100, 2)
        AS repeat_rate_percent,

    ROUND(COALESCE(population_norm, 0), 3)
        AS population_score,

    ROUND(COALESCE(delay_norm, 0), 3)
        AS delay_score

FROM normalized

ORDER BY priority_score DESC

LIMIT :limit;