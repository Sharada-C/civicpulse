-- Ranks wards by complaint volume and shows month-over-month growth.
-- Demonstrates: CTE, window functions (RANK, LAG), DATE_TRUNC.

WITH monthly_ward_counts AS (
    SELECT
        dl.ward_code,
        dl.ward_name,
        DATE_TRUNC('month', dd.full_date) AS month,
        COUNT(*) AS complaint_count
    FROM fact_complaints fc
    JOIN dim_location dl ON fc.location_key = dl.location_key
    JOIN dim_date dd ON fc.date_key = dd.date_key
    GROUP BY dl.ward_code, dl.ward_name, DATE_TRUNC('month', dd.full_date)
),
with_growth AS (
    SELECT
        ward_code,
        ward_name,
        month,
        complaint_count,
        LAG(complaint_count) OVER (PARTITION BY ward_code ORDER BY month) AS prev_month_count,
        RANK() OVER (PARTITION BY month ORDER BY complaint_count DESC) AS rank_in_month
    FROM monthly_ward_counts
)
SELECT
    ward_code,
    ward_name,
    month,
    complaint_count,
    prev_month_count,
    ROUND(
        100.0 * (complaint_count - COALESCE(prev_month_count, complaint_count))
        / NULLIF(prev_month_count, 0), 1
    ) AS growth_pct,
    rank_in_month
FROM with_growth
ORDER BY month DESC, rank_in_month
LIMIT 20;
